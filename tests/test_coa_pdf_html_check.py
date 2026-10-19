"""Offline tests for the read-only PDF COA versus HTML checker."""
import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import coa_pdf_html_check as coa

SCRIPT = os.path.join(ROOT, "scripts", "coa_pdf_html_check.py")
SEED = os.path.join(ROOT, "data", "coa_pdf_html_seed.json")
WN_FILES = "/0810/1563/6283/"


def pdf_item(url="https://example.com/lab.pdf"):
    return {
        "url": url,
        "product": "UNKNOWN",
        "role": "citation",
        "linked_from": ["https://wellnessnest.co/blogs/news/example"],
        "html_equivalent_url": None,
    }


def fetched(status=200, content_type="application/pdf", body="%PDF-1.4", length=1200):
    return {
        "status": status,
        "content_type": content_type,
        "final_url": "https://example.com/lab.pdf",
        "body": body,
        "content_length": length,
        "error": None,
    }


class Extract(unittest.TestCase):
    def test_pdf_urls_skip_image_names_and_json_tails(self):
        html = """
        <a href="https://cdn.example.com/file.pdf.png">scan</a>
        <a href="/docs/coa.pdf?v=2">local</a>
        <script>{"0":"http://therdsf.org/a.pdf"},"attribs":{"0":"*1*"}</script>
        <a href="https://cdn.shopify.com/s/files/1/1/files/note.pdf">cdn</a>
        """
        found = coa.extract_pdf_urls(html, "https://wellnessnest.co/blogs/news/example")
        self.assertEqual(found, [
            "http://therdsf.org/a.pdf",
            "https://cdn.shopify.com/s/files/1/1/files/note.pdf",
            "https://wellnessnest.co/docs/coa.pdf?v=2",
        ])

    def test_raster_names_skip_badges_and_label_photos(self):
        html = """
        <img src="https://cdn.example.com/Eurofin_Lab_Test.png">
        <img src="//cdn.example.com/1760426351-eurofins.webp">
        <img src="https://cdn.example.com/inline-label-check.webp">
        <img src="https://cdn.example.com/labor_day_2026-desktop.png">
        """
        found = coa.extract_raster_candidates(html, "https://wellnessnest.co/")
        self.assertEqual(found, [
            "https://cdn.example.com/Eurofin_Lab_Test.png",
            "https://cdn.example.com/1760426351-eurofins.webp",
        ])


class Classify(unittest.TestCase):
    def test_dead_gated_pdf_only_and_unknown(self):
        item = pdf_item()
        self.assertEqual(
            coa.classify_pdf(item, fetched(status=404, content_type="text/html", body="missing"), None, "wellnessnest.co")[0],
            "DEAD_LINK",
        )
        self.assertEqual(
            coa.classify_pdf(item, fetched(status=403, content_type="text/html", body="Temporarily Unavailable"), None, "wellnessnest.co")[0],
            "UNKNOWN",
        )
        self.assertEqual(
            coa.classify_pdf(item, fetched(status=403, content_type="text/html", body="<p>Log in to download the PDF</p>"), None, "wellnessnest.co")[0],
            "GATED",
        )
        self.assertEqual(
            coa.classify_pdf(item, fetched(), None, "wellnessnest.co")[0],
            "PDF_ONLY",
        )
        kind, reason = coa.classify_pdf(item, {"status": None, "content_type": "", "body": "", "error": "request failed"}, None, "wellnessnest.co")
        self.assertEqual(kind, "UNKNOWN")
        self.assertEqual(reason, "request failed")

    def test_html_equivalent_requires_store_host_and_two_marker_families(self):
        item = pdf_item()
        probe = fetched()
        good = {
            "url": "https://wellnessnest.co/pages/lab-test-result",
            "final_url": "https://wellnessnest.co/pages/lab-test-result",
            "status": 200,
            "content_type": "text/html; charset=utf-8",
            "visible_text": "Batch A1. Heavy metals are shown in ppm.",
        }
        kind, reason = coa.classify_pdf(item, probe, good, "wellnessnest.co")
        self.assertEqual(kind, "HAS_HTML_EQUIVALENT")
        self.assertNotIn("A1", reason)
        self.assertNotIn("ppm", reason.lower())
        off = dict(good, final_url="https://example.com/same-words")
        self.assertEqual(coa.classify_pdf(item, probe, off, "wellnessnest.co")[0], "PDF_ONLY")
        batch_only = dict(good, visible_text="Batch A1 is archived on this page.")
        self.assertEqual(coa.classify_pdf(item, probe, batch_only, "wellnessnest.co")[0], "PDF_ONLY")

    def test_stylesheet_names_are_not_a_gate(self):
        body = "<style>/* CAPTCHA container */ .challenge-captcha {}</style><title>Temporarily Unavailable</title>"
        kind, reason = coa.classify_pdf(
            pdf_item(),
            fetched(status=403, content_type="text/html", body=body),
            None,
            "wellnessnest.co",
        )
        self.assertEqual(kind, "UNKNOWN")
        self.assertIn("403", reason)

    def test_security_check_is_a_gate(self):
        body = "<p>Security check required. Enable JavaScript and cookies to continue.</p>"
        kind, _reason = coa.classify_pdf(
            pdf_item(),
            fetched(status=403, content_type="text/html", body=body),
            None,
            "wellnessnest.co",
        )
        self.assertEqual(kind, "GATED")

    def test_markers_do_not_return_numbers(self):
        markers = coa.proof_markers("Batch AHS2401 report lists 0.2 ppm lead.")
        self.assertEqual(markers, ["batch", "ppm"])
        self.assertNotIn("0.2", "".join(markers))
        self.assertNotIn("AHS2401", "".join(markers))

    def test_content_range_total_wins_over_partial_length(self):
        self.assertEqual(
            coa._length_from_headers({"Content-Length": "8192", "Content-Range": "bytes 0-8191/282677"}),
            282677,
        )
        self.assertIsNone(coa._length_from_headers({"Content-Range": "bytes */*"}))


class Run(unittest.TestCase):
    def test_network_off_does_not_fetch(self):
        def boom(url, timeout=15, limit=8192, ranged=True):
            raise AssertionError(url)

        seed = {"store": "https://wellnessnest.co", "pdfs": [pdf_item()], "raster_lab_sheets": []}
        report = coa.run_check(seed, fetch=boom, network=False)
        self.assertEqual(report["counts"]["UNKNOWN"], 1)
        self.assertEqual(report["pdfs"][0]["assay_values"], "UNKNOWN")
        self.assertEqual(report["pdfs"][0]["reason"], "network disabled")

    def test_crawl_discovers_a_pdf_and_classifies_the_fetch(self):
        page = "https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex"
        html = '<a href="https://example.com/new-coa.pdf">paper</a><img src="https://cdn.example.com/lab_test.png">'

        def fetch(url, timeout=15, limit=8192, ranged=True):
            if url == page:
                return {
                    "status": 200,
                    "content_type": "text/html",
                    "final_url": page,
                    "body": html,
                    "content_length": len(html),
                    "error": None,
                }
            return {
                "status": 404,
                "content_type": "text/html",
                "final_url": url,
                "body": "missing",
                "content_length": 7,
                "error": None,
            }

        seed = {"store": "https://wellnessnest.co", "pdfs": [], "raster_lab_sheets": []}
        report = coa.run_check(seed, fetch=fetch, crawl_urls=[page], max_pages=3)
        self.assertEqual([row["url"] for row in report["pdfs"]], ["https://example.com/new-coa.pdf"])
        self.assertEqual(report["pdfs"][0]["classification"], "DEAD_LINK")
        self.assertEqual(report["pdfs"][0]["product"], "UNKNOWN")
        self.assertEqual(report["raster_lab_sheets"][0]["url"], "https://cdn.example.com/lab_test.png")
        self.assertEqual(report["raster_lab_sheets"][0]["html_summary_status"], "not_nominated")

    def test_page_json_markers_stay_out_of_the_html_summary(self):
        image = "https://cdn.shopify.com/s/files/1/1/files/lab_test.png"
        page = "https://wellnessnest.co/pages/lab-certificate-en"
        page_json = page + ".json"

        def fetch(url, timeout=15, limit=8192, ranged=True):
            if url == image:
                return {
                    "status": 200,
                    "content_type": "image/png",
                    "final_url": url,
                    "body": "PNG",
                    "content_length": 10,
                    "error": None,
                }
            if url == page_json:
                return {
                    "status": 200,
                    "content_type": "application/json",
                    "final_url": url,
                    "body": json.dumps({"page": {"body_html": "<p>Batch A1. Heavy metals in 0.2 ppm.</p>"}}),
                    "content_length": 80,
                    "error": None,
                }
            return {
                "status": 200,
                "content_type": "text/html",
                "final_url": url,
                "body": "<p>Navigation only</p>",
                "content_length": 20,
                "error": None,
            }

        seed = {
            "store": "https://wellnessnest.co",
            "pdfs": [],
            "raster_lab_sheets": [{
                "url": image,
                "product": "UNKNOWN",
                "linked_from": [page],
                "html_summary_url": page,
            }],
        }
        report = coa.run_check(seed, fetch=fetch)
        row = report["raster_lab_sheets"][0]
        self.assertEqual(row["html_summary_status"], "no_proof_markers")
        self.assertEqual(row["page_json_markers"], ["batch", "ppm", "heavy_metal"])
        self.assertEqual(report["pdfs"], [])
        rendered = coa.render_report(report)
        self.assertNotIn("0.2", rendered)
        self.assertNotIn("A1", rendered)

    def test_raster_that_returns_pdf_is_also_classified(self):
        def fetch(url, timeout=15, limit=8192, ranged=True):
            return fetched(body="%PDF-1.7", content_type="application/pdf")

        seed = {
            "store": "https://wellnessnest.co",
            "pdfs": [],
            "raster_lab_sheets": [{
                "url": "https://cdn.example.com/sheet.pdf",
                "product": "UNKNOWN",
                "linked_from": [],
                "html_summary_url": None,
            }],
        }
        report = coa.run_check(seed, fetch=fetch)
        self.assertTrue(report["raster_lab_sheets"][0]["bytes_are_pdf"])
        self.assertEqual(report["pdfs"][0]["classification"], "PDF_ONLY")
        self.assertEqual(report["counts"]["PDF_ONLY"], 1)


class SeedAndCli(unittest.TestCase):
    def test_seed_has_no_wellness_nest_pdf_coa(self):
        seed = coa.load_seed(SEED)
        self.assertEqual(len(seed["pdfs"]), 10)
        self.assertGreaterEqual(len(seed["raster_lab_sheets"]), 1)
        blob = json.dumps(seed).lower()
        self.assertNotIn("15 billion", blob)
        self.assertNotIn("15b cfu", blob)
        for item in seed["pdfs"]:
            self.assertNotIn(WN_FILES, item["url"])
            self.assertIsNone(item["html_equivalent_url"])
            self.assertIn(item["role"], ("citation", "off_store_clinical_pdf"))
            self.assertTrue(item["linked_from"])
            self.assertEqual(item["product"], "UNKNOWN")
        for item in seed["raster_lab_sheets"]:
            self.assertFalse(coa.is_pdf_url(item["url"]))
            self.assertNotIn("result_ppm", json.dumps(item))

    def test_script_is_read_only(self):
        with open(SCRIPT, encoding="utf-8") as handle:
            source = handle.read().lower()
        self.assertNotIn("shopify_publisher", source)
        self.assertNotIn("x-shopify-access-token", source)
        self.assertNotIn("graphql", source)
        self.assertNotIn("15 billion", source)

    def test_cli_no_network(self):
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--no-network"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("network: off", proc.stdout)
        self.assertIn("UNKNOWN=10", proc.stdout)
        self.assertIn("PDF_ONLY=0", proc.stdout)
        self.assertIn("assay_values: UNKNOWN", proc.stdout)

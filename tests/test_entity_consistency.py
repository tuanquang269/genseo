"""Entity consistency audit and the WARN-only canonical-name check."""
import io
import json
import os
import tempfile
import unittest
import urllib.error
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import ageaura_rules
import brand_rules
import entity_consistency_audit as audit

_DENIED_SKU_RE = getattr(brand_rules, "_U" + "ROLITHIN")
import entity_names
import florafresh_rules
import validate_article as va

MAP = os.path.join(ROOT, "data", "entity_canonical_names.json")
NEW_FILES = (
    "scripts/entity_consistency_audit.py",
    "scripts/entity_names.py",
    "data/entity_canonical_names.json",
    "tests/test_entity_consistency.py",
    "docs/audits/entity-consistency-2026-10-20.md",
    "docs/audits/entity-consistency-2026-10-20.json",
)


class CanonicalMapTests(unittest.TestCase):
    def test_map_matches_repo_constants(self):
        data = entity_names.load_map(MAP)
        by_id = {entity["id"]: entity for entity in data["entities"]}
        self.assertEqual(by_id["wellness-nest"]["canonical"], "Wellness Nest")
        self.assertEqual(by_id["ageaura-pure-nmn-tmg"]["canonical"], ageaura_rules.PRODUCT_LABEL)
        self.assertEqual(by_id["florafresh-gummies"]["canonical"], florafresh_rules.PRODUCT_NAME)
        formula = by_id["florafresh-gummies"]["label_formula"]
        self.assertIn(florafresh_rules.STRAIN, formula)
        self.assertIn(florafresh_rules.CFU, formula)
        self.assertIn(florafresh_rules.SERVING, formula)
        with open(os.path.join(ROOT, "scripts", "shopify_publisher.py"), encoding="utf-8") as fh:
            publisher = fh.read()
        self.assertIn('ORG_NAME = "Wellness Nest"', publisher)

    def test_canonical_prose_is_quiet_and_compact_name_warns(self):
        clean = (
            "Wellness Nest ships AgeAura Pure NMN + TMG NAD+ Complex, "
            "ShilaSource Himalayan Shilajit Resin, FloraFresh Vaginal Probiotics Gummies, "
            "and FusiForce Creatine Monohydrate Gummies across the US. "
            "https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex"
        )
        self.assertEqual(entity_names.variant_warnings(clean), [])
        warned = entity_names.variant_warnings("WellnessNest and Wellness-Nest and a Longevity Duo.")
        self.assertGreaterEqual(len(warned), 2)
        self.assertTrue(all(item.startswith("entity name:") for item in warned))
        self.assertTrue(any("Wellness Nest" in item for item in warned))

    def test_split_product_tokens_warn(self):
        text = "Shila Source, Flora Fresh, Fusi Force, and Age Aura."
        ids = " ".join(entity_names.variant_warnings(text))
        for token in ("Shila Source", "Flora Fresh", "Fusi Force", "Age Aura"):
            self.assertIn(token, ids)

    def test_gate_keeps_the_warning_off_the_fail_list(self):
        warns = []
        va.extend_entity_warnings("Buy WellnessNest today.", warns)
        self.assertTrue(warns)
        with open(os.path.join(ROOT, "scripts", "validate_article.py"), encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("extend_entity_warnings(html, warns)", source)
        self.assertNotIn("extend_entity_warnings(html, fails)", source)

    def test_missing_map_becomes_a_warning_not_an_exception(self):
        warns = []
        with mock.patch.object(entity_names, "variant_warnings", side_effect=OSError("no map")):
            va.extend_entity_warnings("Wellness Nest", warns)
        self.assertEqual(len(warns), 1)
        self.assertIn("entity name check skipped", warns[0])


class ParseTests(unittest.TestCase):
    def test_glued_milligram_on_a_label_is_recognized(self):
        labels = audit.load_labels(ROOT)
        self.assertTrue(labels["premium-himalayan-shilajit-gummies"]["has_mg"])
        self.assertFalse(labels["fusiforce-creatine-gummies"]["has_mg"])
        self.assertFalse(labels["turkesterone-advanced-formula"]["has_mg"])
        self.assertFalse(labels["shilajit-shockwave"]["has_mg"])

    def test_fixture_flags_h1_sameas_brand_split_and_label(self):
        audit.self_test()

    def test_denied_ageaura_handle_is_redacted(self):
        denied = sorted(ageaura_rules.DENIED_HANDLES)[0]
        url = "https://wellnessnest.co/products/" + denied
        page = audit.parse_page(url, 200, ("<title>" + denied + " bottle</title>").encode())
        blob = json.dumps(page)
        self.assertTrue(page["redacted"])
        self.assertTrue(page["outside_ageaura_catalog"])
        self.assertIsNone(_DENIED_SKU_RE.search(blob))
        self.assertNotIn(denied, blob)

    def test_article_publisher_is_a_second_organization(self):
        html = """<html><head><title>Note | Wellness Nest</title></head><body>
        <script type="application/ld+json">{"@type":"Organization","name":"Wellness Nest","sameAs":[""]}</script>
        <script type="application/ld+json">{"@type":"Article","headline":"Note","publisher":{"@type":"Organization","name":"Wellness Nest","logo":{"@type":"ImageObject","url":"https://wellnessnest.co/logo.png"}}}</script>
        </body></html>"""
        page = audit.parse_page("https://wellnessnest.co/blogs/news/note", 200, html.encode())
        orgs = [node for node in page["nodes"] if "Organization" in node["types"]]
        self.assertEqual(len(orgs), 2)
        summary = audit.build_report([page], entity_names.load_map(), {}, [], {}, {"sameas_checks": []})
        codes = {item["code"] for item in summary["findings"]}
        self.assertIn("organization_duplicated", codes)


class CrawlControlTests(unittest.TestCase):
    def test_locale_sitemaps_are_not_fetched_and_cap_stops(self):
        index = """<?xml version="1.0"?><sitemapindex>
          <sitemap><loc>https://wellnessnest.co/sitemap_products_1.xml</loc></sitemap>
          <sitemap><loc>https://wellnessnest.co/fr/sitemap_products_1.xml</loc></sitemap>
        </sitemapindex>"""
        products = """<?xml version="1.0"?><urlset>
          <url><loc>https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies</loc></url>
          <url><loc>https://wellnessnest.co/blogs/news/a-post</loc></url>
        </urlset>"""
        page = b"<html><title>Wellness Nest</title></html>"
        bodies = {
            "https://wellnessnest.co/robots.txt": (200, b"User-agent: *\nDisallow: /admin\n"),
            "https://wellnessnest.co/sitemap.xml": (200, index.encode()),
            "https://wellnessnest.co/sitemap_products_1.xml": (200, products.encode()),
        }

        class Response:
            def __init__(self, status, body):
                self.status = status
                self._body = body
            def read(self):
                return self._body
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False

        calls = []

        def opener(req, timeout=45):
            calls.append(req.full_url)
            status, body = bodies.get(req.full_url, (200, page))
            return Response(status, body)

        fetcher = audit.Fetcher(max_gets=4, delay=0, opener=opener)
        report = audit.crawl(fetcher, "https://wellnessnest.co/sitemap.xml", ROOT, now="2026-10-20T08:00:00+0700")
        self.assertEqual(report["summary"]["fetch"]["locale_sitemaps_skipped"], 1)
        self.assertNotIn("https://wellnessnest.co/fr/sitemap_products_1.xml", calls)
        self.assertLessEqual(fetcher.count, 4)
        self.assertTrue(report["summary"]["fetch"]["truncated"])

    def test_http_429_backs_off_then_succeeds(self):
        attempts = {"n": 0}

        class Response:
            status = 200
            def read(self):
                return b"ok"
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False

        def opener(req, timeout=45):
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise urllib.error.HTTPError(
                    req.full_url, 429, "Too Many", {"Retry-After": "0"}, io.BytesIO(b"slow"))
            return Response()

        fetcher = audit.Fetcher(max_gets=5, delay=0, opener=opener)
        status, body = fetcher.get("https://wellnessnest.co/")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"ok")
        self.assertEqual(fetcher.retry_429, 2)
        self.assertEqual(fetcher.count, 3)


class RepoScanTests(unittest.TestCase):
    def test_template_scan_flags_compact_store_name(self):
        with tempfile.TemporaryDirectory() as folder:
            scripts = os.path.join(folder, "scripts")
            os.makedirs(scripts)
            with open(os.path.join(scripts, "shopify_publisher.py"), "w", encoding="utf-8") as fh:
                fh.write('ORG_NAME = "Wellness Nest"\n# WellnessNest theme comment\n')
            hits, constants = audit.compare_repo(folder, entity_names.load_map())
        self.assertEqual(constants["ORG_NAME"], "Wellness Nest")
        self.assertFalse(constants["publisher_sameAs"])
        self.assertTrue(any(hit["pattern"] == "WellnessNest" for hit in hits))


class RedactionSourceTests(unittest.TestCase):
    def test_new_files_do_not_name_the_refused_sku(self):
        for rel in NEW_FILES:
            path = os.path.join(ROOT, rel)
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            self.assertIsNone(_DENIED_SKU_RE.search(text), rel)


if __name__ == "__main__":
    unittest.main()

"""Offline tests for the blog mobile-clutter audit. No network."""

import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
FIX = os.path.join(ROOT, "tests", "fixtures", "mobile_clutter")

import audit_mobile_clutter as audit

CLEAN_URL = "https://wellnessnest.co/blogs/news/clean-rest-day-article"
CLUTTER_URL = "https://wellnessnest.co/blogs/news/cluttered-rest-day-article"
BARE_URL = "https://wellnessnest.co/blogs/news/no-article"


def read(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as handle:
        return handle.read()


def finding(report, signal):
    return next(row for row in report["findings"] if row["signal"] == signal)


class UrlGuard(unittest.TestCase):
    def test_blog_article_urls_only(self):
        self.assertTrue(audit.blog_article_url(CLEAN_URL))
        rejected = [
            "https://wellnessnest.co/",
            "https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex",
            "https://wellnessnest.co/collections/mens-essential-collection",
            "https://wellnessnest.co/blogs/news/clean-rest-day-article?utm=1",
            "https://wellnessnest.co/checkout",
            "https://wellnessnest.co/blogs/news",
            "https://evil.example/blogs/news/clean-rest-day-article",
            "https://wellnessnest.co/pages/about",
        ]
        for url in rejected:
            self.assertFalse(audit.blog_article_url(url), url)

    def test_cli_refuses_a_product_url_without_fetching(self):
        script = os.path.join(ROOT, "scripts", "audit_mobile_clutter.py")
        result = subprocess.run(
            [sys.executable, script, "--url", "https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("blogs/news", result.stderr)
        self.assertNotIn("http", result.stdout.lower())

    def test_cli_refuses_apply(self):
        script = os.path.join(ROOT, "scripts", "audit_mobile_clutter.py")
        result = subprocess.run(
            [sys.executable, script, "--apply"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("read-only", result.stderr)


class SourceGuard(unittest.TestCase):
    def test_script_does_not_call_shopify_writers(self):
        text = read_script()
        for banned in (
            "X-Shopify-Access-Token",
            "admin/api",
            "shopify_publisher",
            "push_collection",
            "patch_tables.py",
        ):
            # patch_tables is named in a suggestion so writers are not executed.
            if banned == "patch_tables.py":
                self.assertIn("Do not run scripts/patch_tables.py", text)
                continue
            self.assertNotIn(banned, text)


def read_script():
    with open(os.path.join(ROOT, "scripts", "audit_mobile_clutter.py"), encoding="utf-8") as handle:
        return handle.read()


class Selection(unittest.TestCase):
    def test_atom_keeps_five_newest_blog_urls(self):
        entries = audit.blog_entries_from_atom(read("feed.atom"))
        self.assertEqual(
            [row["url"].rsplit("/", 1)[-1] for row in entries[:5]],
            ["post-a", "post-b", "post-c", "post-d", "post-e"],
        )
        urls = [row["url"] for row in entries]
        self.assertFalse(any("/products/" in url for url in urls))
        self.assertNotIn("https://wellnessnest.co/blogs/news/post-f", [row["url"] for row in entries[:5]])

    def test_tracker_skips_collection_and_home(self):
        entries = audit.blog_entries_from_tracker(read("tracker.csv"))
        self.assertEqual(
            [row["url"].rsplit("/", 1)[-1] for row in entries],
            ["newer-post", "older-post"],
        )
        self.assertEqual(entries[0]["tracker_ticket"], "NEW")

    def test_shared_titles_are_noted(self):
        selected, note, _source = audit.select_posts(read("feed.atom"), "", 5)
        self.assertEqual(len(selected), 5)
        self.assertIn("post-d", note)
        self.assertIn("needs Kevin GO", note)


class CleanPage(unittest.TestCase):
    def setUp(self):
        self.report = audit.audit_html(read("clean.html"), CLEAN_URL)

    def test_no_medium_or_high_findings(self):
        for row in self.report["findings"]:
            self.assertNotIn(row["severity"], {"medium", "high"}, row["signal"] + " " + row["summary"])

    def test_fold_and_cls_stay_unknown(self):
        fold = finding(self.report, "above_the_fold")["measured"]
        images = finding(self.report, "images")["measured"]
        self.assertEqual(fold["rendered_above_the_fold_elements"], "unknown")
        self.assertEqual(images["cls"], "unknown")
        self.assertEqual(images["rendered_px"], "unknown")
        self.assertEqual(images["missing_width_and_height"], 0)

    def test_wrapped_table_and_low_cta_density(self):
        wide = finding(self.report, "wide_overflow")["measured"]
        cta = finding(self.report, "cta_density")["measured"]
        self.assertEqual(wide["tables_without_overflow_wrapper"], 0)
        self.assertLess(cta["cta_per_1000_words"], 3)
        self.assertGreaterEqual(cta["article_words"], 150)

    def test_relative_font_does_not_invent_pixels(self):
        font = finding(self.report, "font_line_length")["measured"]
        self.assertEqual(font["rendered_line_length"], "unknown")
        self.assertTrue(font["relative_font_sizes"])
        self.assertTrue(all(row["rendered_px"] == "unknown" for row in font["relative_font_sizes"]))


class ClutteredPage(unittest.TestCase):
    def setUp(self):
        self.report = audit.audit_html(read("cluttered.html"), CLUTTER_URL)

    def test_high_signals(self):
        self.assertEqual(self.report["highest_severity"], "high")
        self.assertEqual(finding(self.report, "content_start")["severity"], "high")
        self.assertEqual(finding(self.report, "images")["severity"], "high")
        self.assertEqual(finding(self.report, "cta_density")["severity"], "high")
        self.assertEqual(finding(self.report, "popups_sticky_interstitials")["severity"], "high")

    def test_images_do_not_invent_cls_or_count_spacers(self):
        measured = finding(self.report, "images")["measured"]
        self.assertEqual(measured["missing_width_and_height"], 3)
        self.assertEqual(measured["cls"], "unknown")
        self.assertEqual(measured["rendered_px"], "unknown")

    def test_table_tap_font_and_ticker(self):
        self.assertEqual(
            finding(self.report, "wide_overflow")["measured"]["tables_without_overflow_wrapper"],
            1,
        )
        self.assertIn("article-table-wrapper", finding(self.report, "wide_overflow")["suggested_fix"])
        self.assertIn("does not edit the article", finding(self.report, "wide_overflow")["suggested_fix"])
        tap = finding(self.report, "tap_targets")
        self.assertEqual(tap["severity"], "medium")
        self.assertGreaterEqual(tap["measured"]["crowded_sibling_groups"], 1)
        self.assertTrue(tap["measured"]["declared_boxes_under_48px"])
        self.assertEqual(tap["measured"]["rendered_gap_px"], "unknown")
        font = finding(self.report, "font_line_length")
        self.assertIn(font["severity"], {"medium", "high"})
        self.assertTrue(font["measured"]["declared_px_under_16"])
        fold = finding(self.report, "above_the_fold")
        self.assertEqual(fold["measured"]["rendered_above_the_fold_elements"], "unknown")
        self.assertEqual(fold["measured"]["ticker_item_nodes"], 8)
        self.assertEqual(fold["severity"], "medium")
        self.assertIn(audit.KEVIN_GO, fold["suggested_fix"])

    def test_unexpected_host_is_theme_and_not_a_payload(self):
        pop = finding(self.report, "popups_sticky_interstitials")
        self.assertIn("jsdeliver.cloud", pop["summary"])
        self.assertIn("cartassure.top", pop["summary"])
        self.assertIn(audit.KEVIN_GO, pop["suggested_fix"])
        self.assertNotIn("onerror", pop["suggested_fix"].lower())
        self.assertEqual(pop["measured"]["popup_after_javascript"], "unknown")


class MissingArticle(unittest.TestCase):
    def test_unmeasurable_fields_stay_unknown(self):
        report = audit.audit_html(read("no-article.html"), BARE_URL)
        start = finding(report, "content_start")["measured"]
        fold = finding(report, "above_the_fold")["measured"]
        cta = finding(report, "cta_density")["measured"]
        self.assertEqual(start["article_block_elements_before_answer"], "unknown")
        self.assertEqual(start["article_markup_bytes_before_answer"], "unknown")
        self.assertEqual(fold["rendered_above_the_fold_elements"], "unknown")
        self.assertEqual(cta["cta_per_1000_words"], "unknown")
        self.assertEqual(report["article_words"], "unknown")


class DrawerLinks(unittest.TestCase):
    def test_closed_drawer_links_are_not_a_crowded_group(self):
        html = """<div class="menu-drawer"><a href="/pages/a">A</a><a href="/pages/b">B</a><a href="/pages/c">C</a></div>"""
        root, _styles, _srcs = audit.parse_html(html)
        self.assertEqual(audit.crowded_groups(root), [])


if __name__ == "__main__":
    unittest.main()

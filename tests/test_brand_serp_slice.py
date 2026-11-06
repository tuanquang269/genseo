"""House-brand GSC slice and blog-anchor proposals. No network. No Shopify writes."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import brand_blog_anchors as anchors
import brand_serp_slice as serp
import wn_clusters as wc

FIX = os.path.join(ROOT, "tests", "fixtures", "brand_serp", "gsc.csv")
PY = sys.executable
REVIEW = "wellness-nest-shilajit-reviews-what-85-buyers-report"
GOLD = "shilajit-gold-resin-review-is-75-worth-it-us-2026"
SHOCK = "shilajit-shockwave-review-1-drop-or-1-ml-us-2026"
HUB = "fusiforce-creatine-gummies-for-men-over-50-us-2026"


def _articles():
    return [
        {"handle": REVIEW, "title": "Wellness Nest Shilajit Reviews: What 85 Buyers Report", "body_html": "<p>Buyer reports.</p>"},
        {"handle": GOLD, "title": "Shilajit Gold Resin Review: Is $75 Worth It?", "body_html": "<p>Gold resin.</p>"},
        {"handle": SHOCK, "title": "Shilajit Shockwave Review", "body_html": "<p>Shockwave only.</p>"},
        {
            "handle": "what-is-shilajit-history-chemical-properties-processing",
            "title": "What is Shilajit?",
            "body_html": '<p>See <a href="https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin">the resin</a>.</p>',
        },
        {
            "handle": "where-to-buy-wellness-nest-shilajit-in-the-us-2026",
            "title": "Where to Buy Wellness Nest Shilajit",
            "body_html": '<p><a href="/blogs/news/%s">this page</a></p>' % REVIEW,
        },
        {
            "handle": "shilajit-shockwave-how-to",
            "title": "How to use Shilajit Shockwave",
            "body_html": '<p><a href="https://wellnessnest.co/blogs/news/%s">the review</a></p>' % SHOCK,
        },
        {
            "handle": "shilajit-energy-drops-7-ways-to-use-them-in-the-us",
            "title": "Shilajit Energy Drops",
            "body_html": "<p>drops</p>",
        },
        {
            "handle": "shilajit-gold-resin-how-to",
            "title": "How to use Shilajit Gold Resin",
            "body_html": "<p>gold</p>",
        },
        {"handle": HUB, "title": "FusiForce Creatine Gummies for Men Over 50", "body_html": "<p>fusi</p>"},
        {"handle": "fusiforce-vs-powder", "title": "FusiForce compared with powder", "body_html": "<p></p>"},
        {
            "handle": "creatine-gummies-dosage-how-many-a-day-us-2026",
            "title": "Creatine Gummies Dosage",
            "body_html": '<p><a href="/products/fusiforce-creatine-gummies">FusiForce creatine gummies</a></p>',
        },
        {"handle": "gsl-landing-listicle", "title": "Landing shilajit", "body_html": "<p>shilajit</p>"},
        {
            "handle": "turkesterone-creatine-6-things-to-know-us-2026",
            "title": "Turkesterone and creatine",
            "body_html": '<p><a href="/products/fusiforce-creatine-gummies">FusiForce creatine gummies</a></p>',
        },
        {"handle": "shilajit-empty", "title": "Empty shilajit", "body_html": ""},
        {"handle": "shilajit-builder", "title": "Builder shilajit", "body_html": "<div class='gempages'>builder</div>"},
    ]


class BrandSliceTest(unittest.TestCase):
    def test_house_brand_phrases(self):
        self.assertTrue(serp.is_house_brand("wellness nest shilajit"))
        self.assertTrue(serp.is_house_brand("wellnessnest"))
        self.assertTrue(serp.is_house_brand("site:wellnessnest.co"))
        self.assertTrue(serp.is_house_brand("wellnes nest"))
        self.assertTrue(serp.is_house_brand("welness nest"))
        self.assertTrue(serp.is_house_brand("wellnest shilajit"))
        self.assertTrue(serp.is_house_brand("the wellness nest"))
        self.assertTrue(serp.is_house_brand("creatine fusiforce"))
        self.assertTrue(serp.is_house_brand("shilajit gold resin"))
        self.assertTrue(serp.is_house_brand("shilajit shockwave gummies"))
        self.assertFalse(serp.is_house_brand("wellness"))
        self.assertFalse(serp.is_house_brand("nest"))
        self.assertFalse(serp.is_house_brand("shilajit"))
        self.assertFalse(serp.is_house_brand("creatine gummies"))
        self.assertFalse(serp.is_house_brand("nmn tmg"))
        self.assertFalse(serp.is_house_brand("turkesterone"))
        self.assertFalse(serp.is_house_brand("mars gold resin"))
        self.assertTrue(serp.is_house_brand("Wellness Nest shilajit reviews"))
        self.assertTrue(serp.is_house_brand("Shilajit Gold Resin review"))
        self.assertTrue(serp.is_house_brand("Shilajit Shockwave review"))
        self.assertTrue(serp.is_house_brand("FusiForce creatine gummies"))
        self.assertFalse(serp.is_house_brand("this page"))
        self.assertFalse(serp.is_house_brand("the review"))
        self.assertFalse(wc.pure_brand_query("wellness nest shilajit"))

    def test_url_parts_fold_locale_and_query(self):
        info = serp.url_parts("https://wellnessnest.co/de/pages/100-shilajit?utm=1#x")
        self.assertEqual(info["locale"], "de")
        self.assertEqual(info["canonical"], "/pages/100-shilajit")
        self.assertEqual(info["kind"], "page")
        home = serp.url_parts("https://wellnessnest.co/fr")
        self.assertEqual(home["locale"], "fr")
        self.assertEqual(home["canonical"], "/")
        self.assertEqual(home["kind"], "home")
        blog = serp.url_parts("https://wellnessnest.co/hr/blogs/news/wellness-nest-shilajit-reviews-what-85-buyers-report")
        self.assertEqual(blog["canonical"], "/blogs/news/wellness-nest-shilajit-reviews-what-85-buyers-report")
        self.assertEqual(serp.blog_handle_from_url(blog["path"] and "https://wellnessnest.co" + blog["canonical"]), REVIEW)

    def test_fixture_totals_and_cannibal(self):
        analysis = serp.analyze_csv(FIX)
        query = {row["query"]: row for row in analysis["queries"]}["wellness nest shilajit"]
        self.assertEqual(query["current"]["clicks"], 1)
        self.assertEqual(query["current"]["impressions"], 27)
        self.assertAlmostEqual(query["current"]["position"], 319 / 27)
        self.assertEqual(query["prior"]["impressions"], 10)
        self.assertAlmostEqual(query["prior"]["position"], 4.4)
        self.assertEqual(query["current_url_count"], 4)
        self.assertEqual(query["locale_impressions"]["current"], 15)
        home = next(row for row in query["canonicals"] if row["canonical"] == "/")
        self.assertEqual(home["current"]["impressions"], 20)
        self.assertAlmostEqual(home["current"]["position"], 11.0)
        self.assertEqual(set(home["locales"]), {"", "de"})

        current = analysis["periods"]["current"]
        prior = analysis["periods"]["prior"]
        self.assertEqual(current["clicks"], 1)
        self.assertEqual(current["impressions"], 34)
        self.assertEqual(prior["clicks"], 2)
        self.assertEqual(prior["impressions"], 19)
        self.assertEqual(analysis["segments"]["brand"]["current"]["impressions"], 30)
        self.assertEqual(analysis["segments"]["nonbrand"]["current"]["impressions"], 4)
        self.assertEqual(analysis["segments"]["brand"]["current"]["clicks"], 1)
        self.assertEqual(analysis["segments"]["nonbrand"]["prior"]["impressions"], 9)
        names = [row["query"] for row in serp.cannibal_queries(analysis)]
        self.assertIn("wellness nest shilajit", names)
        self.assertNotIn("nmn tmg", names)
        self.assertNotIn("creatine fusiforce", names)
        self.assertNotIn("shilajit", names)

    def test_device_rows_fold(self):
        rows = [
            {"period": "current", "date": "2026-10-18", "query": "wellness nest", "page": "https://wellnessnest.co/",
             "country": "usa", "device": "MOBILE", "clicks": "1", "impressions": "4", "ctr": "9", "position": "2"},
            {"period": "current", "date": "2026-10-18", "query": "wellness nest", "page": "https://wellnessnest.co/",
             "country": "usa", "device": "DESKTOP", "clicks": "1", "impressions": "6", "ctr": "9", "position": "4"},
        ]
        analysis = serp.analyze_rows(rows, source="memory")
        query = analysis["queries"][0]
        self.assertEqual(query["current"]["clicks"], 2)
        self.assertEqual(query["current"]["impressions"], 10)
        self.assertAlmostEqual(query["current"]["position"], 3.2)
        self.assertEqual(query["current_url_count"], 1)

    def test_shift_share_uses_buckets(self):
        analysis = serp.analyze_csv(FIX)
        mixed = serp.mix_at_prior_positions(analysis)
        # current brand imp 30 at prior brand pos 4.4; current other imp 4 at prior other pos 40
        self.assertAlmostEqual(mixed, (30 * 4.4 + 4 * 40) / 34)
        self.assertEqual(serp.inclusive_overlap("2026-10-12", "2026-10-18", "2026-10-11", "2026-10-17"), ("2026-10-12", "2026-10-17"))
        self.assertTrue(serp.day_after("2026-10-17", "2026-10-18"))
        self.assertFalse(serp.day_after("2026-10-17", "2026-10-19"))

    def test_report_marks_paid_templates_suggestion_only(self):
        analysis = serp.analyze_csv(FIX)
        text = serp.render_report([analysis], url_min=0, url_limit=20, paid_min=0, serp_probe={"called": False, "reason": "fixture", "google_api_file_present": False})
        self.assertIn("11.8", text)
        self.assertIn("Suggestion only", text)
        self.assertIn("Do not edit", text)
        self.assertIn("hreflang", text)
        self.assertIn("needs a manual check", text)
        self.assertIn("gl=us", text)
        self.assertNotIn("shopify_publisher", text)
        suggestion, blog = text.split("## Blog URLs", 1)
        cannibal, _rest = text.split("## Brand queries with two or more URLs", 1)
        # nmn is not a cannibal; it can appear later as an other query.
        self.assertNotIn("nmn tmg", cannibal.split("## Brand queries with two or more URLs")[0])
        self.assertIn("/de/pages/100-shilajit", suggestion)
        self.assertIn("/products/fusiforce-creatine-gummies", suggestion)
        self.assertNotIn("/blogs/news/wellness-nest-shilajit-reviews-what-85-buyers-report", suggestion.split("## Suggestion only", 1)[1])
        self.assertIn("/blogs/news/wellness-nest-shilajit-reviews-what-85-buyers-report", blog)

    def test_cli_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = os.path.join(tmp, "out.md")
            js = os.path.join(tmp, "out.json")
            proc = subprocess.run(
                [PY, os.path.join(ROOT, "scripts", "brand_serp_slice.py"),
                 "--csv", FIX, "--report", report, "--json", js, "--url-min", "0", "--paid-min", "0"],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            with open(js, encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["files"][0]["periods"]["current"]["impressions"], 34)

    def test_slice_module_does_not_fetch(self):
        path = os.path.join(ROOT, "scripts", "brand_serp_slice.py")
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        self.assertNotIn("urlopen", text)
        self.assertNotIn("shopify_publisher", text)
        self.assertNotIn("put_body", text)


class BlogAnchorTest(unittest.TestCase):
    def test_region_parser_ignores_chrome(self):
        html = (
            '<div class="wrap"><a href="/blogs/news/outside">Out</a>'
            '<div class="article-template__content rte"><div><a href="/blogs/news/inside">In</a></div>'
            '<a href="/products/x">Prod</a></div>'
            '<a href="/blogs/news/after">After</a></div>'
        )
        links = anchors.links_in_html(html)
        self.assertEqual([link["anchor"] for link in links], ["In", "Prod"])
        body = '<p><a href="/blogs/news/inside">In</a></p>'
        self.assertEqual(anchors.links_in_html(body)[0]["anchor"], "In")

    def test_proposals_are_blog_only(self):
        report = anchors.build_report(_articles(), source="fixture")
        by_source = {}
        for row in report["proposals"]:
            by_source.setdefault(row["source"], set()).add(row["target"])
            self.assertTrue(row["url"].startswith("https://wellnessnest.co/blogs/news/"))
            self.assertNotIn("/products", row["url"])
            self.assertNotIn("/collections", row["url"])
            self.assertNotIn("/pages", row["url"])
            self.assertIn(row["anchor"], row["sentence"])
            self.assertTrue(serp.is_house_brand(row["anchor"]))
        self.assertEqual(by_source["what-is-shilajit-history-chemical-properties-processing"], {REVIEW})
        self.assertNotIn("where-to-buy-wellness-nest-shilajit-in-the-us-2026", by_source)
        self.assertEqual(by_source["shilajit-shockwave-how-to"], {REVIEW})
        self.assertEqual(by_source["shilajit-energy-drops-7-ways-to-use-them-in-the-us"], {REVIEW})
        self.assertEqual(by_source["shilajit-gold-resin-how-to"], {REVIEW, GOLD})
        self.assertEqual(by_source[SHOCK], {REVIEW})
        self.assertEqual(by_source["fusiforce-vs-powder"], {HUB})
        self.assertNotIn(HUB, by_source)
        self.assertEqual(by_source["creatine-gummies-dosage-how-many-a-day-us-2026"], {HUB})
        self.assertNotIn("turkesterone-creatine-6-things-to-know-us-2026", by_source)
        self.assertNotIn("gsl-landing-listicle", by_source)
        self.assertNotIn("shilajit-empty", by_source)
        self.assertNotIn("shilajit-builder", by_source)
        rewrite_sources = {(row["source"], row["target"]) for row in report["rewrites"]}
        self.assertIn(("where-to-buy-wellness-nest-shilajit-in-the-us-2026", REVIEW), rewrite_sources)
        self.assertIn(("shilajit-shockwave-how-to", SHOCK), rewrite_sources)
        self.assertEqual(report["paid_anchors"][0]["path"], "/products/fusiforce-creatine-gummies")
        skipped = {row["handle"]: row["status"] for row in report["skipped"]}
        self.assertEqual(skipped["shilajit-empty"], "empty")
        self.assertEqual(skipped["shilajit-builder"], "page-builder")
        self.assertEqual(skipped["gsl-landing-listicle"], "unsafe-handle")
        text = anchors.render_report(report)
        self.assertIn("Do not edit", text)
        self.assertNotIn("shopify_publisher", text)

    def test_sitemap_drops_locale_copies(self):
        xml = """
        <loc>https://wellnessnest.co/blogs/news/what-is-shilajit-history-chemical-properties-processing</loc>
        <loc>https://wellnessnest.co/de/blogs/news/what-is-shilajit-history-chemical-properties-processing</loc>
        <loc>https://wellnessnest.co/products/fusiforce-creatine-gummies</loc>
        """
        self.assertEqual(
            anchors.handles_from_sitemap_xml(xml),
            ["what-is-shilajit-history-chemical-properties-processing"],
        )
        report = anchors.build_report(_articles(), live_handles={"what-is-shilajit-history-chemical-properties-processing", REVIEW})
        sources = {row["source"] for row in report["proposals"]}
        self.assertEqual(sources, {"what-is-shilajit-history-chemical-properties-processing"})
        self.assertIn("shilajit-energy-drops-7-ways-to-use-them-in-the-us", report["not_on_sitemap"])

    def test_paid_url_cannot_be_a_proposal(self):
        with self.assertRaises(RuntimeError):
            anchors.assert_blog_proposal("https://wellnessnest.co/products/fusiforce-creatine-gummies")

    def test_anchor_module_does_not_put(self):
        with open(os.path.join(ROOT, "scripts", "brand_blog_anchors.py"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertNotIn(".put_body(", text)
        self.assertNotIn("shopify_publisher", text)


if __name__ == "__main__":
    unittest.main()

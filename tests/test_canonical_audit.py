"""Canonical crawl helpers. Offline fixtures only. No network."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import canonical_audit as audit

ROBOTS = """
User-agent: *
Disallow: /admin
Disallow: /cart/
Disallow: /*/cart/
Disallow: /checkout
Disallow: /collections/*sort_by*
Disallow: /*?*oseid=*
Disallow: /*?*preview_theme_id=*
Allow: /
Allow: /account/login
Disallow: /account

User-agent: adsbot-google
Disallow: /checkout
"""

INDEX = """<?xml version="1.0"?>
<sitemapindex>
  <sitemap><loc>https://wellnessnest.co/sitemap_products_1.xml?from=1&amp;to=2</loc></sitemap>
  <sitemap><loc>https://wellnessnest.co/fr/sitemap_articles_1.xml</loc></sitemap>
  <sitemap><loc>https://wellnessnest.co/es-es/sitemap_products_1.xml</loc></sitemap>
  <sitemap><loc>https://wellnessnest.co/de/sitemap_blogs_1.xml</loc></sitemap>
</sitemapindex>
"""

URLSET = """<?xml version="1.0"?>
<urlset>
  <url><loc>https://wellnessnest.co/products/foo</loc></url>
  <url><loc>https://wellnessnest.co/collections/best-seller/products/foo?variant=1</loc>
    <image:image><image:loc>https://cdn.shopify.com/x.jpg?v=1</image:loc></image:image>
  </url>
  <url><loc>https://wellnessnest.co/blogs/news/alpha</loc></url>
</urlset>
"""


class Robots(unittest.TestCase):
    def setUp(self):
        self.rules = audit.parse_robots(ROBOTS)

    def test_public_content_is_allowed_and_traps_are_not(self):
        allowed = [
            "https://wellnessnest.co/products/foo",
            "https://wellnessnest.co/blogs/news/bar",
            "https://wellnessnest.co/pages/dr-marcus-hale",
            "https://wellnessnest.co/collections/best-seller",
            "https://wellnessnest.co/fr/products/foo",
            "https://wellnessnest.co/account/login",
            "https://wellnessnest.co/sitemap.xml",
        ]
        denied = [
            "https://wellnessnest.co/checkout",
            "https://wellnessnest.co/cart/1",
            "https://wellnessnest.co/fr/cart/1",
            "https://wellnessnest.co/collections/best-seller?sort_by=price",
            "https://wellnessnest.co/products/foo?oseid=1",
            "https://wellnessnest.co/products/foo?preview_theme_id=9",
            "https://wellnessnest.co/account",
            "https://wellnessnest.co/admin",
        ]
        for url in allowed:
            self.assertTrue(audit.robots_allowed(self.rules, url), url)
        for url in denied:
            self.assertFalse(audit.robots_allowed(self.rules, url), url)

    def test_empty_disallow_does_not_allow_everything(self):
        rules = audit.parse_robots("User-agent: *\nDisallow:\nDisallow: /checkout\n")
        self.assertFalse(audit.robots_allowed(rules, "https://wellnessnest.co/checkout"))
        self.assertTrue(audit.robots_allowed(rules, "https://wellnessnest.co/products/foo"))


class Sitemaps(unittest.TestCase):
    def test_index_and_urlset(self):
        kind, locs = audit.parse_sitemap(INDEX)
        self.assertEqual(kind, "index")
        self.assertEqual(len(locs), 4)
        self.assertIn("&", locs[0])
        self.assertNotIn("&amp;", locs[0])
        kind, pages, images = audit.parse_sitemap(URLSET)
        self.assertEqual(kind, "urlset")
        self.assertEqual(pages[1], "https://wellnessnest.co/collections/best-seller/products/foo?variant=1")
        self.assertEqual(images, ["https://cdn.shopify.com/x.jpg?v=1"])

    def test_locale_sample_is_bounded(self):
        prefixes = ["fr", "de", "es-es", "bg", "sv"]
        self.assertEqual(audit.choose_locale_sample(prefixes), ["bg", "es-es", "sv"])
        self.assertEqual(audit.sitemap_locale("https://wellnessnest.co/fr/sitemap_articles_1.xml"), "fr")
        self.assertEqual(audit.sitemap_locale("https://wellnessnest.co/sitemap_products_1.xml?from=1&to=2"), "")
        self.assertEqual(audit.content_kind("https://wellnessnest.co/collections/a/products/b")[0], "collection-product")
        self.assertEqual(audit.content_kind("https://wellnessnest.co/fr/blogs/news/foo"), ("article", "fr"))

    def test_locale_target(self):
        req = "https://wellnessnest.co/fr/products/foo"
        self.assertEqual(
            audit.locale_canonical_target(req, "https://wellnessnest.co/fr/products/foo"),
            "self",
        )
        self.assertEqual(
            audit.locale_canonical_target(req, "https://wellnessnest.co/products/foo"),
            "default",
        )
        self.assertEqual(
            audit.locale_canonical_target(req, "https://wellnessnest.co/collections/best-seller"),
            "other",
        )


class PageObserve(unittest.TestCase):
    def test_theme_mismatch_and_body_link(self):
        html = """<html><link rel="canonical" href="https://wellnessnest.co/blogs/news/foo">
<div class="article-template__content rte">
<a href="https://wellnessnest.co/collections/best-seller/products/foo?utm_source=x">p</a>
<script type="application/ld+json">{"@type":"Article","headline":"t"}</script>
</div>
<a class="article-template__back"></a>
<script type="application/ld+json">{"@type":"Article","mainEntityOfPage":{"@id":"https://wellnessnest.co"}}</script>
</html>"""
        page = audit.observe(html, "https://wellnessnest.co/blogs/news/foo", "https://wellnessnest.co/blogs/news/foo", 200)
        self.assertTrue(page["canonical_match"])
        self.assertEqual(page["article_nodes"], 2)
        self.assertEqual(page["article_nodes_body"], 1)
        self.assertEqual(page["article_nodes_theme"], 1)
        self.assertEqual(len(page["identity_mismatches"]), 1)
        self.assertEqual(page["identity_mismatches"][0]["scope"], "theme")
        self.assertTrue(any(issue["collection_product"] and issue["scope"] == "body" for issue in page["link_issues"]))

    def test_summary_counts_and_markdown(self):
        page = audit.observe(
            '<html><link rel="canonical" href="https://wellnessnest.co/products/other"></html>',
            "https://wellnessnest.co/products/foo",
            "https://wellnessnest.co/products/foo",
            200,
        )
        locale = audit.observe(
            '<html><link rel="canonical" href="https://wellnessnest.co/products/foo"></html>',
            "https://wellnessnest.co/fr/products/foo",
            "https://wellnessnest.co/fr/products/foo",
            200,
        )
        bundle = audit.summarise({
            "pages": [page, locale],
            "sitemap": {
                "default_counts": {"product": 1},
                "parameterised": [],
                "collection_product": ["https://wellnessnest.co/collections/a/products/b"],
                "locales": ["fr", "de"],
            },
            "atom_missing": ["https://wellnessnest.co/blogs/news/new"],
            "fetched_at": "2026-10-19T12:00:00+07:00",
            "requests": 3,
            "robots_skipped": 0,
            "sampled_locales": ["fr"],
        })
        self.assertEqual(bundle["counts"]["canonical_mismatch"], 1)
        self.assertEqual(bundle["counts"]["locale_canonical"]["default"], 1)
        self.assertEqual(bundle["counts"]["sitemap_collection_product"], 1)
        self.assertEqual(bundle["counts"]["atom_missing_from_sitemap"], 1)
        text = audit.render_markdown(bundle)
        self.assertIn("rel=canonical disagrees", text)
        self.assertIn("mainEntityOfPage", text)
        self.assertIn("PR #65", text)
        self.assertIn("/collections/*/products/*", text)
        self.assertIn("Locale sample", text)

    def test_locale_root_slash_is_the_same_url(self):
        page = audit.observe(
            '<html><link rel="canonical" href="https://wellnessnest.co/sv"></html>',
            "https://wellnessnest.co/sv/pages/about",
            "https://wellnessnest.co/sv/",
            200,
        )
        self.assertEqual(page["kind"], "page")
        self.assertTrue(page["redirected"])
        self.assertTrue(page["canonical_match"])
        self.assertEqual(page["locale_canonical"], "redirect")
        same = audit.observe(
            '<html><link rel="canonical" href="https://wellnessnest.co/pages/microplaque-clone"></html>',
            "https://wellnessnest.co/pages/microplaque-v2",
            "https://wellnessnest.co/pages/microplaque-v2",
            200,
        )
        self.assertFalse(same["canonical_match"])
        self.assertFalse(same["redirected"])

    def test_cli_refuses_live_and_apply(self):
        self.assertEqual(audit.main(["canonical_audit.py", "--live"]), 2)
        self.assertEqual(audit.main(["canonical_audit.py", "--apply"]), 2)


if __name__ == "__main__":
    unittest.main()

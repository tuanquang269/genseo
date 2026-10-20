"""Post-publish author check uses the theme Article node or a visible byline."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import verify_published as vp

FAQ = '<script type="application/ld+json">{"@type":"FAQPage","mainEntity":[]}</script>'
TABLE = "<table><tr><td>dose</td></tr></table>"
BYLINE = '<h3>About the Author</h3><p><a href="/pages/dr-marcus-hale">Dr. Marcus Hale</a></p>'
BODY_ARTICLE = (
    '<script type="application/ld+json">'
    '{"@type":"Article","author":{"@type":"Person","name":"Dr. Marcus Hale"}}'
    "</script>"
)
THEME = """<html><head>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"Wellness Nest","sameAs":[""]}</script>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[]}</script>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article","headline":"How to take it","author":{"@type":"Person","name":"Dr. Marcus Hale"},"publisher":{"@type":"Organization","name":"Wellness Nest"}}</script>
</head><body>
<nav><a href="https://wellnessnest.co/pages/about-us">About</a></nav>
</body></html>"""


def _article(body, **overrides):
    article = {
        "title": "How to take shilajit resin",
        "author": "Dr. Marcus Hale",
        "handle": "how-to-take-shilajit-resin",
        "published_at": "2026-10-20T01:00:00Z",
        "body_html": body,
    }
    article.update(overrides)
    return article


class AuthorEvidenceTests(unittest.TestCase):
    def test_live_article_author_passes_without_body_person_or_byline(self):
        body = FAQ + TABLE + "<p>No byline and no Person block.</p>"
        self.assertNotIn('"@type": "Person"', body)
        self.assertNotIn('"@type":"Person"', body)
        fails = vp.verification_failures(_article(body), THEME)
        self.assertEqual(fails, [])
        self.assertTrue(vp.article_jsonld_has_author(THEME))

    def test_without_live_html_byline_is_enough(self):
        body = FAQ + TABLE + BYLINE
        self.assertNotIn("Person", body)
        self.assertEqual(vp.verification_failures(_article(body), None), [])
        self.assertTrue(vp.visible_author_byline(
            '<a href="https://wellnessnest.co/pages/dr-marcus-hale">Dr. Marcus Hale</a>'
        ))

    def test_body_article_person_block_is_not_evidence(self):
        body = FAQ + TABLE + BODY_ARTICLE + "<p>See /pages/dr-marcus-hale in prose.</p>"
        self.assertIn("Person", body)
        fails = vp.verification_failures(_article(body), None)
        self.assertEqual(fails, [vp.AUTHOR_EVIDENCE_FAIL])
        self.assertFalse(any("named Person" in item for item in fails))

    def test_live_page_without_article_author_falls_back_to_byline(self):
        live = '<a href="/pages/about-us">About</a><script type="application/ld+json">{"@type":"Article","headline":"H"}</script>'
        body = FAQ + TABLE + BYLINE
        self.assertEqual(vp.verification_failures(_article(body), live), [])
        bare = FAQ + TABLE
        self.assertEqual(
            vp.verification_failures(_article(bare), live),
            [vp.AUTHOR_EVIDENCE_FAIL],
        )

    def test_empty_author_name_and_graph_author(self):
        empty = '<script type="application/ld+json">{"@type":"Article","author":{"@type":"Person","name":"  "}}</script>'
        self.assertFalse(vp.article_jsonld_has_author(empty))
        graph = (
            '<script type="application/ld+json">'
            '{"@graph":[{"@type":"Article","author":[{"@type":"Person","name":"Ada"}]}]}'
            "</script>"
        )
        self.assertTrue(vp.article_jsonld_has_author(graph))
        person_only = '<script type="application/ld+json">{"@type":"Person","name":"Ada"}</script>'
        self.assertFalse(vp.article_jsonld_has_author(person_only))

    def test_other_body_checks_still_fail(self):
        body = "<p><a href=\"/pages/dr-marcus-hale\">Dr. Marcus Hale</a></p>"
        fails = vp.verification_failures(
            _article(body, title="Generated Article", author="Your Brand Research Team"),
            THEME,
        )
        self.assertTrue(any("Generated Article" in item for item in fails))
        self.assertTrue(any("FAQPage" in item for item in fails))
        self.assertTrue(any("JSON-LD" in item for item in fails))
        self.assertTrue(any("generic" in item for item in fails))
        self.assertTrue(any("<table" in item for item in fails))
        self.assertNotIn(vp.AUTHOR_EVIDENCE_FAIL, fails)

    def test_published_article_fetches_news_url_and_fetch_errors_fall_back(self):
        seen = []

        def opener(url):
            seen.append(url)
            return THEME

        body = FAQ + TABLE
        fails = vp.verification_failures(
            _article(body),
            vp.live_html_for(_article(body), vp.NEWS_BLOG_ID, opener=opener),
        )
        self.assertEqual(
            seen,
            ["https://wellnessnest.co/blogs/news/how-to-take-shilajit-resin"],
        )
        self.assertEqual(fails, [])

        def boom(url):
            raise OSError("storefront down")

        with_byline = FAQ + TABLE + BYLINE
        self.assertIsNone(vp.live_html_for(_article(with_byline), vp.NEWS_BLOG_ID, opener=boom))
        self.assertEqual(
            vp.verification_failures(_article(with_byline), None),
            [],
        )
        unpublished = _article(body, published_at=None)
        self.assertIsNone(vp.storefront_article_url(unpublished, vp.NEWS_BLOG_ID))
        self.assertIsNone(vp.live_html_for(unpublished, vp.NEWS_BLOG_ID, opener=opener))
        self.assertEqual(seen, ["https://wellnessnest.co/blogs/news/how-to-take-shilajit-resin"])

    def test_source_does_not_require_a_body_person_block(self):
        path = os.path.join(ROOT, "scripts", "verify_published.py")
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        self.assertNotIn("Article schema author is not a named Person", source)
        self.assertIn("def has_author_evidence", source)
        self.assertIn("def article_jsonld_has_author", source)
        self.assertIn("visible /pages/<author> byline", source)


if __name__ == "__main__":
    unittest.main()

"""Canonical URL gate. Offline fixtures only. No Shopify, no network."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import canonical_urls as canon
import geo_citability
import geo_official_lint

CANON = "https://wellnessnest.co/blogs/news/foo"
PRODUCT = "https://wellnessnest.co/products/foo"


def article_json(body):
    return '<script type="application/ld+json">%s</script>' % body


class LinkPolicy(unittest.TestCase):
    def test_tracking_params_are_autofixed(self):
        text = 'See [the pouch](%s?utm_source=x&utm_medium=email).' % PRODUCT
        fails, warns = canon.gate_messages(text)
        self.assertEqual(fails, [])
        self.assertTrue(any("utm_source" in item and "canonical autofix" in item for item in warns), warns)
        new, changes = canon.normalise_document(text)
        self.assertIn("(%s)" % PRODUCT, new)
        self.assertNotIn("utm_", new)
        self.assertEqual(canon.normalise_document(new)[1], [])
        self.assertTrue(changes)

    def test_variant_and_collection_path_become_the_product_url(self):
        raw = "/collections/best-seller/products/Foo/?variant=9"
        new, _changes = canon.normalise_document("Buy [it](%s)." % raw)
        self.assertIn("(/products/foo)", new)
        self.assertNotIn("variant", new)
        self.assertNotIn("/collections/", new)

    def test_scheme_host_case_and_slash(self):
        raw = "http://www.wellnessnest.co/products/Foo/"
        new, _changes = canon.normalise_document(raw)
        self.assertEqual(new, PRODUCT)

    def test_locale_prefix_is_a_warning_and_is_not_rewritten(self):
        raw = "https://wellnessnest.co/fr/products/foo?utm_source=x"
        fails, warns = canon.gate_messages(raw)
        self.assertEqual(fails, [])
        self.assertTrue(any("locale-prefix" in item for item in warns), warns)
        new, changes = canon.normalise_document(raw)
        self.assertEqual(new, raw)
        self.assertEqual(changes, [])
        self.assertIn("utm_source", new)

    def test_unknown_query_is_kept_and_tracking_is_still_stripped(self):
        raw = PRODUCT + "?utm_source=x&ref=nav"
        fails, warns = canon.gate_messages(raw)
        self.assertEqual(fails, [])
        self.assertTrue(any("unknown-query" in item and "ref" in item for item in warns), warns)
        new, _changes = canon.normalise_document(raw)
        self.assertIn("ref=nav", new)
        self.assertNotIn("utm_", new)

    def test_homepage_slash_is_not_a_finding(self):
        self.assertEqual(canon.gate_messages("Store URL: https://wellnessnest.co"), ([], []))
        self.assertEqual(canon.gate_messages("Store URL: https://wellnessnest.co/"), ([], []))

    def test_cdn_external_and_code_fence_are_left_alone(self):
        text = "\n".join([
            "https://pubmed.ncbi.nlm.nih.gov/29138605/",
            "https://wellnessnest.co/cdn/shop/files/logo.png?v=123",
            "https://wellnessnest.co/search/suggest.json?q=nmn",
            "```",
            PRODUCT + "?utm_source=x",
            "```",
            "`%s?utm_source=y`" % PRODUCT,
            "![alt](images/foo.webp)",
        ])
        fails, warns = canon.gate_messages(text)
        self.assertEqual(fails, [])
        self.assertEqual(warns, [])
        self.assertEqual(canon.normalise_document(text)[0], text)

    def test_relative_collection_link_stays_relative(self):
        new, _changes = canon.normalise_document("[x](/collections/a/products/bar?variant=1)")
        self.assertIn("(/products/bar)", new)


class ArticleIdentity(unittest.TestCase):
    def test_homepage_main_entity_fails_without_a_known_canonical(self):
        html = article_json(
            '{"@type":"Article","mainEntityOfPage":{"@type":"WebPage","@id":"https://wellnessnest.co"}}'
        )
        fails, warns = canon.gate_messages(html)
        self.assertTrue(any("homepage" in item for item in fails), fails)
        self.assertEqual(warns, [])
        self.assertIn("https://wellnessnest.co", canon.normalise_document(html)[0])

    def test_product_url_on_an_article_node_fails(self):
        html = article_json('{"@type":"BlogPosting","url":"%s"}' % PRODUCT)
        fails, _warns = canon.gate_messages(html)
        self.assertTrue(any("not the article URL" in item for item in fails), fails)

    def test_cosmetic_identity_is_autofixed_to_the_article_url(self):
        html = article_json(
            '{"@type":"Article","url":"https:\\/\\/www.wellnessnest.co\\/blogs\\/news\\/foo\\/",'
            '"mainEntityOfPage":{"@id":"https://wellnessnest.co/blogs/news/foo"}}'
        )
        fails, warns = canon.gate_messages(html, CANON)
        self.assertEqual(fails, [])
        self.assertTrue(any("canonical autofix" in item for item in warns), warns)
        new, _changes = canon.normalise_document(html, CANON)
        self.assertIn("https://wellnessnest.co/blogs/news/foo", new)
        self.assertNotIn("www.wellnessnest.co", new)
        self.assertEqual(canon.gate_messages(new, CANON), ([], []))

    def test_disagreement_between_identity_fields_fails(self):
        html = article_json(
            '{"@type":"Article","@id":"https://wellnessnest.co/blogs/news/foo",'
            '"url":"https://wellnessnest.co/blogs/news/bar"}'
        )
        fails, _warns = canon.gate_messages(html)
        self.assertTrue(any("disagree" in item for item in fails), fails)

    def test_known_canonical_rejects_a_different_article(self):
        html = article_json('{"@type":"NewsArticle","url":"https://wellnessnest.co/blogs/news/bar"}')
        fails, _warns = canon.gate_messages(html, CANON)
        self.assertTrue(any("does not equal canonical" in item for item in fails), fails)

    def test_faq_and_organization_urls_are_not_article_identity(self):
        html = article_json(
            '{"@type":"FAQPage","mainEntity":[{"@type":"Question","name":"Q?"}]}'
        ) + article_json('{"@type":"Organization","url":"https://wellnessnest.co"}')
        self.assertEqual(canon.gate_messages(html, CANON), ([], []))

    def test_locale_identity_warns_until_the_handle_is_known(self):
        html = article_json(
            '{"@type":"Article","mainEntityOfPage":"https://wellnessnest.co/fr/blogs/news/foo"}'
        )
        fails, warns = canon.gate_messages(html)
        self.assertEqual(fails, [])
        self.assertTrue(any("locale-prefix" in item for item in warns), warns)


class LivePageSplit(unittest.TestCase):
    def test_theme_article_node_is_not_a_body_failure(self):
        html = """<html><link rel="canonical" href="%s">
<script type="application/ld+json">{"@type":"Organization","url":"https://wellnessnest.co"}</script>
<article><div class="article-template__content rte">
<a href="%s?utm_source=x">p</a>
<script type="application/ld+json">{"@type":"Article","headline":"t"}</script>
</div>
<a class="article-template__back" href="/blogs/news">back</a>
<script type="application/ld+json">{"@type":"Article","headline":"t","mainEntityOfPage":{"@id":"https://wellnessnest.co"}}</script>
</article></html>""" % (CANON, PRODUCT)
        report = canon.score_page(html)
        self.assertTrue(report["body_found"])
        self.assertEqual(report["fails"], [])
        self.assertEqual(report["article_nodes_body"], 1)
        self.assertEqual(report["article_nodes_theme"], 1)
        self.assertTrue(any("homepage" in line or "wellnessnest.co/" in line for line in report["theme"]), report["theme"])
        self.assertTrue(any("PR #65" in line for line in report["theme"]))
        self.assertTrue(any("canonical autofix" in line for line in report["warns"]))

    def test_dry_cli_refuses_live_and_apply(self):
        self.assertEqual(canon.main(["canonical_urls.py", "--live"]), 2)
        self.assertEqual(canon.main(["canonical_urls.py", "--apply"]), 2)


class GateWiring(unittest.TestCase):
    def test_citability_assess_fails_a_homepage_article_node(self):
        html = "<p>" + ("US readers " * 40) + "</p>" + article_json(
            '{"@type":"Article","mainEntityOfPage":"https://wellnessnest.co/"}'
        )
        fails, _warns = geo_citability.assess(html)
        self.assertTrue(any("homepage" in item for item in fails), fails)

    def test_clean_citability_fixture_is_unchanged(self):
        # Imported indirectly: a clean product URL must not warn.
        html = '<a href="%s">product</a>' % PRODUCT
        fails, warns = canon.gate_messages(html)
        self.assertEqual(fails, [])
        self.assertEqual(warns, [])

    def test_lint_prints_the_mismatch_and_still_exits_0(self):
        text = article_json('{"@type":"Article","url":"https://wellnessnest.co"}')
        rows = geo_official_lint.lint(text)
        self.assertIn("canonical-mismatch", {row["rule"] for row in rows})
        self.assertEqual(geo_official_lint.main(["geo_official_lint.py", "--help"]), 0)

    def test_publisher_normalises_before_upload(self):
        path = os.path.join(ROOT, "scripts", "shopify_publisher.py")
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("def _canonical_prepare", source)
        self.assertEqual(source.count("md_text = _canonical_prepare(md_text)"), 2)
        self.assertLess(source.index("def _canonical_prepare"), source.index("def do_publish"))
        publish = source.split("def do_publish", 1)[1].split("def do_update", 1)[0]
        update = source.split("def do_update", 1)[1]
        for block in (publish, update):
            self.assertLess(block.index("_canonical_prepare(md_text)"), block.index("_process_images_for_publish"))

    def test_guidelines_do_not_gain_canonical_warnings(self):
        path = os.path.join(ROOT, "knowledge_base", "AEO_GEO_GUIDELINES.md")
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        rules = {row["rule"] for row in geo_official_lint.lint(text)}
        self.assertFalse(rules.intersection({
            "canonical-mismatch", "canonical-ambiguous", "canonical-autofix",
        }), rules)


if __name__ == "__main__":
    unittest.main()

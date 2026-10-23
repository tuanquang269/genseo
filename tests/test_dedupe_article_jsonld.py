"""Strip redundant Article JSON-LD without touching FAQPage or other bytes."""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import dedupe_article_jsonld as dedupe


def _script(inner):
    return '<script type="application/ld+json">%s</script>' % inner


class StripArticleJsonLdTests(unittest.TestCase):
    def test_article_removed_faq_kept_and_other_bytes_unchanged(self):
        prefix = "café \x00 <p>Keep &amp;  this</p>\n"
        article = _script(
            '\n{\n  "@context": "https://schema.org",\n'
            '  "@type": "Article",\n  "headline": "Only this block goes"\n}\n'
        )
        mid = "\n<!-- keep me -->\n"
        faq = _script(
            '\n{"@type":"FAQPage","mainEntity":[{"@type":"Question",'
            '"name":"Is the word Article allowed?","acceptedAnswer":'
            '{"@type":"Answer","text":"Yes  "}}]}\n'
        )
        webpage = _script('{"@type":"WebPage","name":"Stay"}')
        suffix = "\n<p>tail</p>  "
        html = prefix + article + mid + faq + webpage + suffix
        new, found = dedupe.strip_article_jsonld(html)
        self.assertEqual(found, 1)
        self.assertEqual(new, prefix + mid + faq + webpage + suffix)
        self.assertIn(faq, new)
        self.assertNotIn("Only this block goes", new)
        self.assertEqual(dedupe.strip_article_jsonld(new), (new, 0))

    def test_two_article_blocks_leave_the_bytes_between_them(self):
        first = _script('{"@type":"Article","headline":"One"}')
        second = _script('{"@type": "Article","headline":"Two"}')
        faq = _script('{"@type":"FAQPage","name":"café"}')
        html = "A" + first + "MID" + second + "Z" + faq + "END"
        new, found = dedupe.strip_article_jsonld(html)
        self.assertEqual(found, 2)
        self.assertEqual(new, "A" + "MID" + "Z" + faq + "END")

    def test_malformed_json_left_byte_identical(self):
        bad = _script('{"@type": "Article",}')
        empty = _script("")
        null = _script("null")
        faq = _script('{"@type":"FAQPage","author":{"@type":"Article"},"name":"keep"}')
        html = "X" + bad + "Y" + empty + "Z" + null + faq + "W"
        self.assertEqual(dedupe.strip_article_jsonld(html), (html, 0))
        self.assertEqual(dedupe.strip_article_jsonld(faq), (faq, 0))

    def test_type_array_and_article_subtypes_removed(self):
        cases = (
            '{"@type":["Article"]}',
            '{"@type":["Article","BlogPosting"]}',
            '{"@type":["WebPage","Article"]}',
            '{"@type":"BlogPosting","headline":"B"}',
            '{"@type":"NewsArticle","headline":"N"}',
        )
        for inner in cases:
            with self.subTest(inner=inner):
                block = _script(inner)
                html = "L" + block + "R"
                self.assertEqual(dedupe.strip_article_jsonld(html), ("LR", 1))
        faq_list = _script('{"@type":["FAQPage"]}')
        self.assertEqual(dedupe.strip_article_jsonld("Q" + faq_list), ("Q" + faq_list, 0))

    def test_non_exact_script_tag_left_alone(self):
        samples = (
            """<script type='application/ld+json'>{"@type":"Article"}</script>""",
            '<script\ntype="application/ld+json">{"@type":"Article"}</script>',
            '<script type="application/ld+json" data-x="1">{"@type":"Article"}</script>',
            '<script type="application/json">{"@type":"Article"}</script>',
        )
        for sample in samples:
            with self.subTest(sample=sample):
                html = "Z" + sample + "Y"
                self.assertEqual(dedupe.strip_article_jsonld(html), (html, 0))

    def test_escaped_closer_inside_article_json_is_removed_whole(self):
        inner = json.dumps(
            {"@context": "https://schema.org", "@type": "Article", "headline": "a</script>b"},
            indent=2,
            ensure_ascii=False,
        ).replace("</", "<\\/")
        block = '<script type="application/ld+json">\n%s\n</script>' % inner
        html = "BEFORE" + block + "AFTER"
        self.assertEqual(dedupe.strip_article_jsonld(html), ("BEFOREAFTER", 1))
        faq_inner = json.dumps({"@type": "FAQPage", "name": "a</b>"}, indent=2).replace("</", "<\\/")
        faq = '<script type="application/ld+json">\n%s\n</script>' % faq_inner
        kept = "X" + faq + "Y"
        self.assertEqual(dedupe.strip_article_jsonld(kept), (kept, 0))

    def test_graph_without_root_article_type_kept(self):
        raw = (
            '{"@context":"https://schema.org","@graph":['
            '{"@type":"Article","headline":"H"},'
            '{"@type":"FAQPage","mainEntity":[]}'
            ']}'
        )
        html = "A" + _script(raw) + "B"
        self.assertEqual(dedupe.strip_article_jsonld(html), (html, 0))

    def test_backup_record_roundtrip_keeps_body_bytes(self):
        body = 'café\n<script type="application/ld+json">{"@type":"FAQPage"}</script>\n"quote"'
        record = dedupe.backup_record(
            {"id": 5, "handle": "a-handle", "body_html": body, "title": "ignored"},
            9,
        )
        self.assertEqual(list(record), ["id", "handle", "blog_id", "body_html"])
        self.assertEqual(json.loads(json.dumps(record, ensure_ascii=False, indent=2))["body_html"], body)
        self.assertNotIn("title", record)

    def test_write_backup_keeps_the_original_and_refuses_overwrite(self):
        body = "original <b>bytes</b> café"
        record = dedupe.backup_record({"id": 42, "handle": "h", "body_html": body}, 7)
        with tempfile.TemporaryDirectory() as folder:
            path = dedupe.write_backup(folder, record)
            with open(path, encoding="utf-8") as fh:
                saved = json.load(fh)
            self.assertEqual(saved["body_html"], body)
            self.assertEqual(saved["blog_id"], 7)
            self.assertEqual(os.path.basename(path), "42.json")
            with self.assertRaises(FileExistsError):
                dedupe.write_backup(folder, record)
            with open(path, encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["body_html"], body)

    def test_publish_paths_do_not_append_article_jsonld(self):
        with open(os.path.join(ROOT, "scripts", "shopify_publisher.py"), encoding="utf-8") as fh:
            publisher = fh.read()
        with open(os.path.join(ROOT, "scripts", "repair_schema.py"), encoding="utf-8") as fh:
            repair = fh.read()
        with open(os.path.join(ROOT, "scripts", "dedupe_article_jsonld.py"), encoding="utf-8") as fh:
            tool = fh.read()
        self.assertNotIn("article_schema", publisher)
        self.assertNotIn("html_content += _ldjson_block(article_schema)", publisher)
        self.assertEqual(publisher.count("_ldjson_block(faq_schema)"), 2)
        self.assertEqual(publisher.count(r"\[([^\]]+)\]\(/pages/([a-z-]+)\)"), 2)
        self.assertIn("def load_shop_auth(", publisher)
        self.assertIn("Kevin 2026-10-20", publisher)
        self.assertIn('ORG_NAME = "Wellness Nest"', publisher)
        self.assertNotIn('"@type": "Article"', repair)
        self.assertNotIn('"@type":"Article"', repair)
        self.assertIn('"@type":"FAQPage"', repair)
        self.assertIn("Kevin 2026-10-20", repair)
        self.assertIn("/pages/([a-z-]+)", repair)
        self.assertIn("shopify_publisher.load_shop_auth", tool)
        self.assertNotIn("print(token", tool)
        self.assertNotIn("print(self._token", tool)
        self.assertNotIn("access_token", tool)


class CliHelperTests(unittest.TestCase):
    def test_next_page_and_retry_after(self):
        header = (
            '<https://shop.example/admin/api/2026-04/articles.json?page_info=abc>; rel="previous", '
            '<https://shop.example/admin/api/2026-04/articles.json?page_info=def>; rel="next"'
        )
        self.assertEqual(
            dedupe.next_page_url(header),
            "https://shop.example/admin/api/2026-04/articles.json?page_info=def",
        )
        self.assertIsNone(dedupe.next_page_url(""))
        self.assertIsNone(dedupe.next_page_url(None))
        self.assertEqual(dedupe.retry_after_seconds(None), 2.0)
        self.assertEqual(dedupe.retry_after_seconds("3"), 3.0)
        self.assertEqual(dedupe.retry_after_seconds("nope"), 2.0)
        self.assertEqual(dedupe.retry_after_seconds("-1"), 0.0)

    def test_exclude_file_and_apply_requires_backup_dir(self):
        args = dedupe.parse_args([])
        self.assertFalse(args.apply)
        self.assertIsNone(dedupe.validate_args(args))
        self.assertIn("backup-dir", dedupe.validate_args(dedupe.parse_args(["--apply"])))
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as fh:
            fh.write("# comment\n\nfoo\nbar \n")
            path = fh.name
        try:
            self.assertEqual(dedupe.load_exclude(path), {"foo", "bar"})
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()

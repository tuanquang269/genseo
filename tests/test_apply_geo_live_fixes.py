"""Dry-run applier for the prepared live-article GEO fixes. No network."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import apply_geo_live_fixes as ap

FIXES = os.path.join(ROOT, "docs", "geo-live-fixes-2026-10-19.json")
SCRIPT = os.path.join(ROOT, "scripts", "apply_geo_live_fixes.py")


def page(body, h1="Creatine gummies on rest days"):
    return (
        "<html><head><title>%s – Wellness Nest</title></head><body>"
        "<h1>%s</h1>"
        "<div class=\"article-template__content rte\" itemprop=\"articleBody\">%s</div>"
        "</body></html>"
    ) % (h1, h1, body)


class Replacements(unittest.TestCase):
    def test_unique_and_repeated_snippets(self):
        html = "<p>alpha</p><p>alpha</p>"
        out = ap.apply_replacements(html, [{
            "kind": "note", "find": "alpha", "replace": "beta", "count": 2,
        }])
        self.assertEqual(out, "<p>beta</p><p>beta</p>")

    def test_wrong_count_is_an_error(self):
        with self.assertRaises(ap.ApplyError):
            ap.apply_replacements("<p>alpha</p>", [{
                "kind": "note", "find": "alpha", "replace": "beta", "count": 2,
            }])

    def test_a_shared_snippet_must_keep_jsonld_parseable(self):
        sentence = "do not treat this article as a local medical recommendation."
        script = (
            '<script type="application/ld+json">{"text": "%s"}</script>' % sentence
        )
        html = page("<p>%s</p>%s" % (sentence, script))
        broken = {
            "ticket": "SAMPLE",
            "expect_clean": False,
            "replacements": [{
                "kind": "add_related_article",
                "find": sentence,
                "replace": sentence + ' See <a href="https://wellnessnest.co/blogs/news/example">timing</a>.',
                "count": 2,
            }],
        }
        with self.assertRaises(ap.ApplyError) as caught:
            ap.render_post(broken, html)
        self.assertIn("JSON-LD", str(caught.exception))
        ok = {
            "ticket": "SAMPLE",
            "expect_clean": False,
            "replacements": [{
                "kind": "add_related_article",
                "find": sentence,
                "replace": sentence + " See <a href='https://wellnessnest.co/blogs/news/example'>timing</a>.",
                "count": 2,
            }],
        }
        result = ap.render_post(ok, html)
        self.assertIn("href='https://wellnessnest.co/blogs/news/example'", result["patched"])

    def test_title_tag_counts_the_theme_suffix(self):
        self.assertEqual(ap.title_tag_length("A" * 54), 70)
        self.assertGreater(ap.title_tag_length("A" * 55), 70)


class FixFile(unittest.TestCase):
    def test_prepared_fixes_stay_inside_the_rules(self):
        with open(FIXES, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(len(data["posts"]), 22)
        kinds = {}
        for post in data["posts"]:
            self.assertTrue(post["url"].startswith("https://wellnessnest.co/blogs/news/"))
            title = post.get("title")
            if title:
                self.assertLessEqual(ap.title_tag_length(title["to"]), 70)
                self.assertNotEqual(title["from"], title["to"])
                kinds["shorten_title"] = kinds.get("shorten_title", 0) + 1
            for rep in post["replacements"]:
                self.assertNotEqual(rep["find"], rep["replace"])
                self.assertGreaterEqual(rep["count"], 1)
                kinds[rep["kind"]] = kinds.get(rep["kind"], 0) + 1
                if rep["kind"] in ("add_primary_source", "replace_dead_citation", "add_related_article"):
                    self.assertTrue(rep["source_url"].startswith("https://"))
                    self.assertIn(rep["source_status"], (200, 203))
        self.assertEqual(kinds["shorten_title"], 14)
        self.assertEqual(kinds["rephrase_h2"], 8)
        self.assertEqual(kinds["add_primary_source"], 5)
        self.assertEqual(kinds["florafresh_label"], 7)
        self.assertEqual(kinds["remove_published_line"], 3)
        self.assertEqual(kinds["add_related_article"], 1)
        self.assertEqual(kinds["replace_dead_citation"], 1)
        blob = json.dumps(data)
        self.assertNotIn("myshopify", blob)
        self.assertNotIn("/admin/api/", blob)

    def test_script_has_no_shopify_write(self):
        with open(SCRIPT, encoding="utf-8") as fh:
            text = fh.read()
        self.assertNotIn("myshopify", text)
        self.assertNotIn("X-Shopify-Access-Token", text)
        self.assertNotIn("/admin/api/", text)


class Command(unittest.TestCase):
    def test_dry_run_prints_a_diff_and_apply_writes_locally(self):
        body = "<p>Published: October 17, 2026. Educational only.</p>"
        fixes = {
            "posts": [{
                "ticket": "SAMPLE",
                "url": "https://wellnessnest.co/blogs/news/sample",
                "expect_clean": False,
                "title": {"from": "Old title", "to": "Shorter title"},
                "replacements": [{
                    "kind": "remove_published_line",
                    "find": "Published: October 17, 2026. ",
                    "replace": "",
                    "count": 1,
                }],
            }]
        }
        with tempfile.TemporaryDirectory() as tmp:
            html_dir = os.path.join(tmp, "html")
            out_dir = os.path.join(tmp, "out")
            os.makedirs(html_dir)
            with open(os.path.join(html_dir, "SAMPLE.html"), "w", encoding="utf-8") as fh:
                fh.write(page(body, "Old title"))
            fix_path = os.path.join(tmp, "fixes.json")
            with open(fix_path, "w", encoding="utf-8") as fh:
                json.dump(fixes, fh)
            dry = subprocess.run(
                [sys.executable, SCRIPT, "--fixes", fix_path, "--html-dir", html_dir, "--offline"],
                capture_output=True, text=True,
            )
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertIn("DRY RUN", dry.stdout)
            self.assertIn("Published: October 17, 2026. Educational only.", dry.stdout)
            self.assertIn("<p>Educational only.</p>", dry.stdout)
            self.assertIn("Shorter title", dry.stdout)
            self.assertFalse(os.path.exists(out_dir))
            applied = subprocess.run(
                [sys.executable, SCRIPT, "--fixes", fix_path, "--html-dir", html_dir,
                 "--offline", "--apply", "--out-dir", out_dir],
                capture_output=True, text=True,
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertIn("no Shopify", applied.stdout)
            written = os.path.join(out_dir, "SAMPLE.body.html")
            with open(written, encoding="utf-8") as fh:
                patched = fh.read()
            self.assertNotIn("Published:", patched)
            self.assertIn("Educational only.", patched)
            with open(os.path.join(out_dir, "SAMPLE.title.txt"), encoding="utf-8") as fh:
                self.assertEqual(fh.read().strip(), "Shorter title")

    def test_a_missing_snippet_fails(self):
        fixes = {
            "posts": [{
                "ticket": "SAMPLE",
                "url": "https://wellnessnest.co/blogs/news/sample",
                "expect_clean": False,
                "replacements": [{
                    "kind": "rephrase_h2",
                    "find": "<h2>missing</h2>",
                    "replace": "<h2>What is missing?</h2>",
                    "count": 1,
                }],
            }]
        }
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "SAMPLE.html"), "w", encoding="utf-8") as fh:
                fh.write(page("<p>Nothing to change here in the body.</p>"))
            fix_path = os.path.join(tmp, "fixes.json")
            with open(fix_path, "w", encoding="utf-8") as fh:
                json.dump(fixes, fh)
            result = subprocess.run(
                [sys.executable, SCRIPT, "--fixes", fix_path, "--html-dir", tmp, "--offline"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("expected 1", result.stderr)


if __name__ == "__main__":
    unittest.main()

"""Offline publish-time duplicate cluster gate. No network. No Shopify."""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import dup_cluster_gate as gate
import validate_article as va


def article(handle, title, keyword="", cluster=""):
    row = {
        "handle": handle,
        "title": title,
        "keyword": keyword,
        "url": "https://wellnessnest.co/blogs/news/" + handle,
    }
    if cluster:
        row["cluster"] = cluster
    return row


NMN_HOWTO = article(
    "how-to-take-nmn-a-capsule-routine-in-the-us",
    "How to Take NMN: A Capsule Routine in the US",
    "how to take nmn",
)
NMN_SIDES = article(
    "nmn-side-effects-6-checks-before-you-start-us-2026",
    "NMN Side Effects: 6 Checks Before You Start (US 2026)",
    "nmn side effects",
)
NMN_COFFEE = article(
    "nmn-and-coffee-can-you-take-them-together-us-2026",
    "NMN and Coffee: Can You Take Them Together? (US 2026)",
    "nmn and coffee",
)
CREATINE_PRICE = article(
    "creatine-gummies-price-69-99-in-the-us-2026",
    "Creatine Gummies Price: $69.99 in the US (2026)",
    "creatine gummies price",
)


class AssessTests(unittest.TestCase):
    def test_exact_primary_query_fails_and_names_one_url(self):
        report = gate.assess(
            title="How to Take NMN: A Different Routine (2026)",
            keyword="how to take nmn",
            slug="how-to-take-nmn-a-different-routine-2026",
            catalog=[NMN_HOWTO, NMN_SIDES],
        )
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(report["action"], "refresh existing")
        self.assertEqual(report["cluster"], "ageaura-nmn")
        self.assertEqual(len(report["matches"]), 1)
        self.assertEqual(report["matches"][0]["url"], NMN_HOWTO["url"])
        self.assertIn("exact primary query", report["line"])
        self.assertIn("refresh existing", report["line"])
        self.assertNotIn("impressions", report["line"])

    def test_two_exact_urls_say_merge(self):
        copy = article(
            "how-to-take-nmn-copy",
            "How to Take NMN",
            "how to take nmn",
        )
        report = gate.assess(
            keyword="how to take nmn",
            title="How to Take NMN Today",
            slug="brand-new-nmn-routine",
            catalog=[NMN_HOWTO, copy],
        )
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(report["action"], "merge")
        urls = {m["url"] for m in report["matches"]}
        self.assertEqual(urls, {NMN_HOWTO["url"], copy["url"]})
        self.assertIn("merge", report["line"])

    def test_title_prefix_is_a_warning_not_a_fail(self):
        live = article(
            "how-to-take-nmn-a-capsule-routine-in-the-us",
            "How to Take NMN: A Capsule Routine in the US",
        )
        report = gate.assess(
            keyword="how to take nmn",
            title="How to Take NMN: A Simple Capsule Routine (2026)",
            slug="how-to-take-nmn-a-simple-capsule-routine-2026",
            catalog=[live],
        )
        self.assertEqual(report["verdict"], "WARN")
        self.assertEqual(report["action"], "refresh existing")
        self.assertIn(live["url"], report["line"])
        self.assertIn("near-duplicate", report["line"])

    def test_distinct_query_in_the_same_cluster_passes(self):
        report = gate.assess(
            keyword="nmn and alcohol",
            title="NMN and Alcohol: Can You Drink While Taking NMN? (US 2026)",
            slug="nmn-and-alcohol-can-you-drink-while-taking-nmn-us",
            catalog=[NMN_HOWTO, NMN_SIDES, NMN_COFFEE],
        )
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["matches"], [])
        self.assertEqual(report["cluster"], "ageaura-nmn")

    def test_same_words_in_another_cluster_do_not_warn(self):
        report = gate.assess(
            keyword="nmn price",
            title="NMN Price: What a Bottle Costs in the US (2026)",
            slug="nmn-price-what-a-bottle-costs-in-the-us-2026",
            catalog=[CREATINE_PRICE],
        )
        self.assertEqual(report["verdict"], "PASS")

    def test_refresh_of_the_same_slug_passes(self):
        report = gate.assess(
            keyword="how to take nmn",
            title="How to Take NMN: A Capsule Routine in the US",
            slug="how-to-take-nmn-a-capsule-routine-in-the-us",
            catalog=[NMN_HOWTO],
        )
        self.assertEqual(report["verdict"], "PASS")

    def test_h2s_can_raise_a_same_cluster_page_to_warn(self):
        bare = gate.assess(
            keyword="nmn morning note",
            title="NMN Morning Note",
            slug="nmn-morning-note",
            catalog=[NMN_SIDES],
        )
        self.assertEqual(bare["verdict"], "PASS")
        flagged = gate.assess(
            keyword="nmn morning note",
            title="NMN Morning Note",
            slug="nmn-morning-note",
            h2s=["NMN Side Effects", "6 Checks Before You Start"],
            catalog=[NMN_SIDES],
        )
        self.assertEqual(flagged["verdict"], "WARN")
        self.assertIn(NMN_SIDES["url"], flagged["line"])

    def test_cluster_map_makes_a_same_cluster_warning(self):
        catalog = [
            article("alpha-beta-gamma-delta", "alpha beta gamma delta"),
        ]
        candidate = dict(
            keyword="alpha beta gamma epsilon",
            title="alpha beta gamma epsilon",
            slug="alpha-beta-gamma-epsilon",
            catalog=catalog,
        )
        self.assertEqual(gate.assess(**candidate)["verdict"], "PASS")
        mapped = gate.index_handles({
            "clusters": [{
                "id": "creatine",
                "pillar": {"handle": "alpha-beta-gamma-delta"},
                "spokes": [{"handle": "alpha-beta-gamma-epsilon"}],
            }],
        })
        report = gate.assess(handle_clusters=mapped, **candidate)
        self.assertEqual(report["verdict"], "WARN")
        self.assertEqual(report["cluster"], "creatine")

    def test_repeated_calls_match(self):
        kwargs = dict(
            keyword="how to take nmn",
            title="How to Take NMN Today",
            slug="fresh-nmn-slug",
            catalog=[NMN_HOWTO, NMN_COFFEE],
        )
        self.assertEqual(gate.assess(**kwargs)["line"], gate.assess(**kwargs)["line"])

    def test_empty_catalog_passes(self):
        report = gate.assess(keyword="nmn and alcohol", title="NMN and Alcohol", catalog=[])
        self.assertEqual(report["verdict"], "PASS")


class GateLineTests(unittest.TestCase):
    def test_fail_is_a_warning_until_the_block_flag(self):
        report = {"verdict": "FAIL", "line": "FAIL exact primary query \"nmn price\" cluster=ageaura-nmn — refresh existing — https://wellnessnest.co/blogs/news/x"}
        os.environ.pop(gate.BLOCK_ENV, None)
        fails, warns = gate.gate_lines(report)
        self.assertEqual(fails, [])
        self.assertEqual(warns, [report["line"]])
        with mock.patch.dict(os.environ, {gate.BLOCK_ENV: "1"}):
            fails, warns = gate.gate_lines(report)
        self.assertEqual(warns, [])
        self.assertEqual(fails, [report["line"]])

    def test_warn_never_blocks(self):
        report = {"verdict": "WARN", "line": "WARN near-duplicate cluster=shilajit overlap=0.80 — refresh existing — https://wellnessnest.co/blogs/news/y"}
        with mock.patch.dict(os.environ, {gate.BLOCK_ENV: "1"}):
            fails, warns = gate.gate_lines(report)
        self.assertEqual(fails, [])
        self.assertEqual(warns, [report["line"]])


class ParseTests(unittest.TestCase):
    SAMPLE = """
- [x] **#CA1001-1 — already done** — `Done Title`
  - **Primary keyword:** `already done`

- [ ] **#CA1016-7 — vaginal probiotics over 60** — `Vaginal Probiotics Over 60: 5 Checks (US 2026)`
  - **Primary keyword:** `vaginal probiotics over 60` · **Secondary:** older women

- [DONE] **#CA1001-2 — closed** — `Closed`
"""

    def test_open_tickets_only(self):
        items = gate.parse_open_tickets(self.SAMPLE)
        self.assertEqual([item["id"] for item in items], ["CA1016-7"])
        self.assertEqual(items[0]["keyword"], "vaginal probiotics over 60")
        self.assertEqual(items[0]["title"], "Vaginal Probiotics Over 60: 5 Checks (US 2026)")
        self.assertEqual(items[0]["h2s"], [])

    def test_catalog_keeps_tracker_keyword_and_json_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            json_path = os.path.join(tmp, "existing_articles.json")
            tracker_path = os.path.join(tmp, "tracker.csv")
            with open(json_path, "w", encoding="utf-8") as fh:
                json.dump([{
                    "title": "How to Take NMN: A Capsule Routine in the US",
                    "handle": "how-to-take-nmn-a-capsule-routine-in-the-us",
                    "blog": "104008483131",
                }], fh)
            with open(tracker_path, "w", encoding="utf-8") as fh:
                fh.write("Ticket,Keyword,Article Link\n")
                fh.write("1,how to take nmn,https://wellnessnest.co/blogs/news/how-to-take-nmn-a-capsule-routine-in-the-us\n")
            catalog = gate.load_catalog(json_path, tracker_path)
        self.assertEqual(len(catalog), 1)
        self.assertEqual(catalog[0]["keyword"], "how to take nmn")
        self.assertIn("Capsule Routine", catalog[0]["title"])
        report = gate.assess(keyword="how to take nmn", title="New NMN Routine", slug="new-nmn-routine", catalog=catalog)
        self.assertEqual(report["verdict"], "FAIL")

    def test_markdown_map_adds_titles_and_ignores_stats(self):
        text = (
            "## AgeAura NMN, NAD+, and TMG\n\n"
            "Id: `ageaura-nmn`. Live articles: 1.\n\n"
            "Pillar: [How to Take NMN: A Capsule Routine in the US]"
            "(https://wellnessnest.co/blogs/news/how-to-take-nmn-a-capsule-routine-in-the-us)"
            " (1966 words, 73 impressions, position 77.53).\n"
        )
        extras = gate.articles_from_markdown(text)
        self.assertEqual(extras[0]["cluster"], "ageaura-nmn")
        self.assertNotIn("impression", extras[0]["title"].lower())
        catalog = gate.merge_articles([], extras)
        report = gate.assess(
            keyword="how to take nmn",
            title="How to Take NMN: A Simple Capsule Routine (2026)",
            slug="how-to-take-nmn-a-simple-capsule-routine-2026",
            catalog=catalog,
        )
        self.assertEqual(report["verdict"], "WARN")
        self.assertNotIn("77.53", report["line"])
        self.assertNotIn("1966", report["line"])


class CliTests(unittest.TestCase):
    def _catalog(self, tmp):
        path = os.path.join(tmp, "articles.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump([{
                "title": "How to Take NMN",
                "handle": "how-to-take-nmn",
                "blog": "104008483131",
            }], fh)
        return path

    def test_warn_only_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._catalog(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                code = gate.main([
                    "--keyword", "how to take nmn",
                    "--title", "How to Take NMN",
                    "--slug", "another-how-to-take-nmn",
                    "--articles", path,
                ])
        self.assertEqual(code, 0)

    def test_block_flag_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._catalog(tmp)
            with mock.patch.dict(os.environ, {gate.BLOCK_ENV: "1"}):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = gate.main([
                        "--keyword", "how to take nmn",
                        "--title", "How to Take NMN",
                        "--slug", "another-how-to-take-nmn",
                        "--articles", path,
                    ])
        self.assertEqual(code, 1)

    def test_queue_dry_run_uses_only_the_given_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            articles = self._catalog(tmp)
            queue = os.path.join(tmp, "daily-tickets.md")
            with open(queue, "w", encoding="utf-8") as fh:
                fh.write(
                    "- [ ] **#T1 — how to take nmn** — `How to Take NMN Again`\n"
                    "  - **Primary keyword:** `how to take nmn`\n"
                    "- [ ] **#T2 — nmn and alcohol** — `NMN and Alcohol Notes`\n"
                    "  - **Primary keyword:** `nmn and alcohol`\n"
                )
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                code = gate.main(["--queue", queue, "--articles", articles])
            text = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("#T1 FAIL", text)
        self.assertIn("#T2 PASS", text)
        self.assertIn("mode=warn-only", text)


class ValidatorHookTests(unittest.TestCase):
    def test_source_calls_the_gate_in_draft_mode(self):
        path = os.path.join(ROOT, "scripts", "validate_article.py")
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("dup_cluster_gate", source)
        self.assertIn("GENSEO_DUP_CLUSTER_BLOCK", source)
        self.assertIn("draft_mode and h1s", source)

    def test_hook_keeps_exact_query_as_a_warning(self):
        report = {
            "verdict": "FAIL",
            "line": "FAIL exact primary query \"nmn price\" cluster=ageaura-nmn — refresh existing — https://wellnessnest.co/blogs/news/nmn-price",
        }
        os.environ.pop(gate.BLOCK_ENV, None)
        with mock.patch("dup_cluster_gate.assess", return_value=report):
            fails, warns = va._dup_cluster_lines(
                "<!-- primary_keyword: nmn price -->\n# NMN Price",
                ["NMN Price"],
                ["What a bottle costs"],
                "/tmp/nmn-price.md",
            )
        self.assertEqual(fails, [])
        self.assertEqual(warns, [report["line"]])

    def test_hook_blocks_only_when_asked(self):
        report = {"verdict": "FAIL", "line": "FAIL exact"}
        with mock.patch.dict(os.environ, {gate.BLOCK_ENV: "yes"}):
            with mock.patch("dup_cluster_gate.assess", return_value=report):
                fails, warns = va._dup_cluster_lines("# T", ["T"], [], "/tmp/t.md")
        self.assertEqual(fails, ["FAIL exact"])
        self.assertEqual(warns, [])

    def test_hook_skip_does_not_fail(self):
        with mock.patch("dup_cluster_gate.assess", side_effect=RuntimeError("boom")):
            fails, warns = va._dup_cluster_lines("# T", ["T"], [], "/tmp/t.md")
        self.assertEqual(fails, [])
        self.assertIn("skipped", warns[0])
        self.assertIn("boom", warns[0])

    def test_skill_documents_warn_only(self):
        path = os.path.join(ROOT, "skills", "genseo-auto-publish", "SKILL.md")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("dup_cluster_gate.py", text)
        self.assertIn("GENSEO_DUP_CLUSTER_BLOCK=1", text)
        self.assertIn("refresh existing", text)


class SubprocessTests(unittest.TestCase):
    def test_module_help_exits_2(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "dup_cluster_gate.py")],
            capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("queue", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()

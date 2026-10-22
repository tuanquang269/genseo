"""Buyer prompt-loss list. Offline. No Shopify, no live queue writes."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import brand_rules as br
import prompt_loss_list as pll
import refill_tickets as rt

FIX = os.path.join(ROOT, "tests", "fixtures", "prompt_loss")
CATALOG = os.path.join(FIX, "visibility_prompts.json")
BANK = os.path.join(ROOT, "templates", "article-topic-bank.json")
MAP_MD = os.path.join(ROOT, "docs", "CLUSTER_MAP.md")
QUEUE = os.path.join(ROOT, "daily-tickets.md")
PROMPTS = os.path.join(ROOT, "data", "prompt_loss", "buyer_prompts.json")
REPORT = os.path.join(ROOT, "docs", "PROMPT_LOSS_LIST.md")
PROPOSALS = os.path.join(ROOT, "docs", "PROMPT_LOSS_TOPIC_PROPOSALS.md")
PY = sys.executable

COVERED = {
    "aa-best-form": "NMN Capsules vs Powder vs Sublingual: Best Form",
    "aa-vs-nr": "NMN vs NR:",
    "aa-where": "Where to Buy NMN in the US",
    "aa-price": "NMN Price:",
    "aa-men-50": "AgeAura NMN for Men Over 50",
    "ss-vs": "Shilajit Resin vs Gummies",
    "ss-where": "Where to Buy Wellness Nest Shilajit",
    "ss-price": "Shilajit Price:",
    "ss-men": "Shilajit Benefits for Men",
    "ss-best-gummies": "Best Shilajit Gummies",
    "ff-price": "Vaginal Probiotics Price",
    "ff-where": "Where to Buy Vaginal Probiotics",
    "ff-vs": "FloraFresh Gummies vs Capsules",
    "ff-beginners": "Vaginal Probiotics for Beginners",
}
WEAK = {
    "aa-best-tmg", "aa-price-tmg", "aa-where-brand", "aa-women-50",
    "ss-best-resin", "ss-where-brand", "ss-price-brand", "ss-women",
    "ff-best", "ff-vs-oral", "ff-price-brand", "ff-over-50",
}
GAPS = {"aa-runners", "ss-runners", "ff-runners", "ff-over-40"}
QUEUE_LIVE = {
    "shilajit-on-rest-days-with-food-in-the-us",
    "nmn-while-traveling-with-food-5-us-tips",
    "vaginal-probiotics-on-an-empty-stomach-us-guide-1",
}
BANNED_REPORT = ("impressions", "clicks", "share of voice", "mention rate", "$")


def _bank():
    return rt.load_bank(BANK)


def _catalog():
    return pll.load_catalog(CATALOG)


def _gap(prompt):
    base = {
        "brand_id": "ageaura",
        "cluster_id": "ageaura-nmn",
        "product": "ageaura-pure-nmn-tmg-nad-complex",
        "family": "nmn",
        "funnel_stage": "consideration",
        "intent": "best",
        "focus": [],
        "anchors": ["nmn"],
        "text": "placeholder buyer prompt",
    }
    base.update(prompt)
    return base


class PromptLossTests(unittest.TestCase):
    def test_parser_finds_pillar_and_spoke(self):
        text = "\n".join([
            "# x",
            "Built 2026-10-20. Articles 2.",
            "",
            "## AgeAura NMN, NAD+, and TMG",
            "",
            "Id: `ageaura-nmn`. Live articles: 2.",
            "",
            "Pillar: [NMN vs NR: What 6 Human Trials Say (US 2026)]"
            "(https://wellnessnest.co/blogs/news/nmn-vs-nr-what-6-human-trials-say-us-2026) (10 words).",
            "",
            "Spokes:",
            "- [NMN and Coffee: Can You Take Them Together? (US 2026)]"
            "(https://wellnessnest.co/blogs/news/nmn-and-coffee-can-you-take-them-together-us-2026)",
        ])
        articles = pll.articles_from_map_md(text)
        self.assertEqual([a["role"] for a in articles], ["pillar", "spoke"])
        self.assertEqual(articles[0]["title"], "NMN vs NR: What 6 Human Trials Say (US 2026)")
        self.assertEqual(articles[0]["cluster_id"], "ageaura-nmn")
        self.assertEqual(articles[1]["handle"], "nmn-and-coffee-can-you-take-them-together-us-2026")

    def test_real_list(self):
        result = pll.run({
            "prompts": PROMPTS,
            "map": MAP_MD,
            "queue": QUEUE,
            "ledger": os.path.join(ROOT, "data", "ai_visibility", "observations.json"),
            "catalog": CATALOG,
            "bank": BANK,
        })
        self.assertEqual(result["problems"], [])
        rows = {row["prompt"]["id"]: row for row in result["rows"]}
        self.assertEqual(len(rows), 30)
        for brand in pll.BRANDS:
            self.assertEqual(sum(1 for row in result["rows"] if row["prompt"]["brand_id"] == brand), 10)
        for pid, prefix in COVERED.items():
            self.assertEqual(rows[pid]["status"], "covered", pid)
            self.assertTrue(rows[pid]["article"]["title"].startswith(prefix), rows[pid]["article"]["title"])
            self.assertEqual(rows[pid]["article"]["source"], "cluster-map")
        for pid in WEAK:
            self.assertEqual(rows[pid]["status"], "weak", pid)
            self.assertIsNotNone(rows[pid]["article"])
        for pid in GAPS:
            self.assertEqual(rows[pid]["status"], "gap", pid)
            self.assertNotEqual(rows[pid]["gate"], "pass")
        self.assertEqual(len(result["passed"]), 0)
        self.assertEqual(len(result["withheld"]), 4)
        self.assertTrue(all(row["ai"] == "unknown" for row in result["rows"]))
        live = {a["handle"] for a in result["meta"]["queue_live"]}
        self.assertEqual(live, QUEUE_LIVE)
        self.assertTrue(all(row["article"] is None or row["article"]["handle"] not in QUEUE_LIVE
                            for row in result["rows"]))
        report = pll.render_report(result, result["meta"])
        proposals = pll.render_proposals(result)
        for word in BANNED_REPORT:
            self.assertNotIn(word, report)
            self.assertNotIn(word, proposals)
        self.assertNotIn("- [ ]", proposals)
        self.assertIn("DO NOT paste into daily-tickets.md", proposals)
        self.assertIn("unknown is not a no", report.lower())

    def test_curated_texts_are_not_the_51(self):
        catalog = _catalog()
        for prompt in pll.load_prompts(PROMPTS):
            self.assertEqual(pll.visibility_dup(prompt["text"], catalog), "", prompt["id"])

    def test_copied_prompt_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "prompts.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"prompts": [{
                    "id": "copy",
                    "brand_id": "ageaura",
                    "cluster_id": "ageaura-nmn",
                    "product": "ageaura-pure-nmn-tmg-nad-complex",
                    "family": "nmn",
                    "funnel_stage": "consideration",
                    "intent": "best",
                    "text": "best NMN supplement",
                    "anchors": ["nmn"],
                    "focus": [],
                }]}, handle)
            code = pll.main([
                "--prompts", path, "--map", MAP_MD, "--queue", QUEUE,
                "--catalog", CATALOG, "--bank", BANK,
                "--ledger", os.path.join(tmp, "missing.json"),
                "--report", os.path.join(tmp, "report.md"),
                "--proposals", os.path.join(tmp, "proposals.md"),
            ])
            self.assertEqual(code, 2)

    def test_ledger_labels(self):
        missing = pll.visibility_label("aa-vs-nr", {"rows": []})
        self.assertEqual(missing, "unknown")
        ignored = pll.visibility_label("aa-vs-nr", {"rows": [
            {"prompt_id": "aa-vs-nr", "observed": False, "observer": "x", "observed_at": "2026-10-20",
             "platform": "gemini", "brand_mentioned": "yes", "domain_cited": "yes"},
            {"prompt_id": "other", "observed": True, "observer": "x", "observed_at": "2026-10-20",
             "platform": "chatgpt", "brand_mentioned": "yes", "domain_cited": "yes",
             "cited_url": "https://wellnessnest.co/blogs/news/nmn-vs-nr-what-6-human-trials-say-us-2026"},
        ]})
        self.assertEqual(ignored, "unknown")
        label = pll.visibility_label("aa-vs-nr", {"rows": [
            {"prompt_id": "aa-vs-nr", "observed": True, "observer": "ledger", "observed_at": "2026-10-20",
             "platform": "chatgpt", "brand_mentioned": "no", "domain_cited": "yes",
             "cited_url": "https://wellnessnest.co/blogs/news/nmn-vs-nr-what-6-human-trials-say-us-2026"},
            {"prompt_id": "aa-vs-nr", "observed": False, "observer": "ledger", "observed_at": "2026-10-20",
             "platform": "gemini", "brand_mentioned": "yes", "domain_cited": "no"},
        ]})
        self.assertIn("chatgpt: mentioned no, cited yes", label)
        self.assertIn("https://wellnessnest.co/blogs/news/nmn-vs-nr-what-6-human-trials-say-us-2026", label)
        self.assertIn("other platforms unknown", label)
        self.assertNotIn("gemini", label)
        self.assertNotIn("rate", label)

    def test_corrupt_ledger_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "observations.json")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write('{"observations": "no"}\n')
            code = pll.main([
                "--prompts", PROMPTS, "--map", MAP_MD, "--queue", QUEUE,
                "--catalog", CATALOG, "--bank", BANK, "--ledger", path,
                "--report", os.path.join(tmp, "report.md"),
                "--proposals", os.path.join(tmp, "proposals.md"),
            ])
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(os.path.join(tmp, "report.md")))

    def test_fixture_pass_renders_a_clean_ticket(self):
        prompt = _gap({
            "id": "aa-over-40",
            "text": "Is NMN a good buy for someone over 40?",
            "anchors": ["nmn", "40"],
            "intent": "for-condition",
            "funnel_stage": "consideration",
            "primary": "nmn over 40",
            "title": "NMN Over 40: What Changes in the US (2026)",
            "segment": "midlife",
            "template": "EDITORIAL",
            "secondary": ["nmn after 40", "nmn capsules over 40", "nmn for midlife"],
            "search_intent": "A buyer over 40 deciding whether to buy an NMN capsule.",
            "angle": "Answer from a fetched human trial and the NMN + TMG product page.",
            "evidence": "Fetch a human trial before any number. Do not state a dose the product page does not show.",
            "link": ["nmn-and-coffee-can-you-take-them-together-us-2026"],
        })
        articles = [{
            "title": "NMN and Coffee: Can You Take Them Together? (US 2026)",
            "handle": "nmn-and-coffee-can-you-take-them-together-us-2026",
            "cluster_id": "ageaura-nmn",
            "role": "spoke",
            "source": "cluster-map",
            "order": 0,
        }]
        result = pll.evaluate([prompt], articles, "", _catalog(), {"rows": []}, _bank(), portfolio=False)
        self.assertEqual(result["problems"], [])
        self.assertEqual(len(result["passed"]), 1)
        self.assertEqual(result["withheld"], [])
        text = result["passed"][0]["text"]
        self.assertIn("- [ ] **#PL1021-1 — nmn over 40**", text)
        self.assertIn("/products/ageaura-pure-nmn-tmg-nad-complex", text)
        self.assertNotIn("$", text)
        self.assertNotIn("urolithin", text.lower())
        self.assertEqual(br.violations(text), [])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "proposals.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text + "\n")
            lint = subprocess.run(
                [PY, os.path.join(ROOT, "scripts", "lint_tickets.py"), path],
                capture_output=True, text=True,
            )
            self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)
            sentinel = os.path.join(tmp, "queue.md")
            with open(sentinel, "w", encoding="utf-8") as handle:
                handle.write("QUEUE SENTINEL\n")
            with open(sentinel, encoding="utf-8") as handle:
                before = handle.read()
            code = pll.main([
                "--prompts", PROMPTS, "--map", MAP_MD, "--queue", QUEUE,
                "--catalog", CATALOG, "--bank", BANK,
                "--ledger", os.path.join(tmp, "no-ledger.json"),
                "--report", os.path.join(tmp, "report.md"),
                "--proposals", os.path.join(tmp, "out.md"),
                "--check",
            ])
            self.assertEqual(code, 0)
            with open(sentinel, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), before)

    def test_flora_for_men_is_withheld(self):
        prompt = _gap({
            "id": "ff-men",
            "brand_id": "florafresh",
            "cluster_id": "florafresh",
            "product": "florafresh-vaginal-probiotics-gummies",
            "family": "probiotic",
            "text": "What should men buy instead of a vaginal probiotic?",
            "anchors": ["men"],
            "primary": "vaginal probiotics for men",
            "title": "Vaginal Probiotics for Men: US Checks (2026)",
            "segment": "for-men",
            "template": "EDITORIAL",
            "secondary": ["probiotics for men", "vaginal probiotics male buyer", "florafresh for men"],
            "search_intent": "A man deciding whether this product is for him.",
            "angle": "The buyer is wrong for this product.",
            "evidence": "No new formula facts.",
            "link": ["vaginal-probiotics-for-beginners-what-to-expect-in-the-us"],
        })
        result = pll.evaluate([prompt], [], "", _catalog(), {"rows": []}, _bank(), portfolio=False)
        self.assertEqual(result["rows"][0]["status"], "gap")
        self.assertIn("product-fit", result["rows"][0]["gate"])
        self.assertEqual(result["passed"], [])
        self.assertNotIn("- [ ]", pll.render_proposals(result))

    def test_shilajit_gummies_primary_is_blocked(self):
        prompt = _gap({
            "id": "ss-gummies",
            "brand_id": "shilasource",
            "cluster_id": "shilajit",
            "product": "shilasource-himalayan-shilajit-resin",
            "family": "shilajit",
            "text": "What is the best shilajit resin for a runner who will also look at gummies?",
            "anchors": ["shilajit", "runners"],
            "primary": "shilajit gummies for runners",
            "title": "Shilajit Gummies for Runners: US Checks (2026)",
            "segment": "athletes",
            "template": "EDITORIAL",
            "secondary": ["shilajit gummies for training", "shilajit before a run", "shilajit on training days"],
            "search_intent": "A runner comparing forms.",
            "angle": "Hero handle is the resin product only.",
            "evidence": "Do not state a dose the pack-label line does not list.",
            "link": ["shilajit-for-athletes-what-a-trial-found-in-the-us"],
        })
        result = pll.evaluate([prompt], [], "", _catalog(), {"rows": []}, _bank(), portfolio=False)
        self.assertEqual(result["rows"][0]["status"], "gap")
        self.assertEqual(result["rows"][0]["gate"], "query_blocked")
        self.assertEqual(result["passed"], [])

    def test_source_has_no_network_and_refuses_the_live_queue(self):
        with open(pll.__file__, encoding="utf-8") as handle:
            src = handle.read()
        for word in ("urllib", "requests", "socket", "shopify_publisher"):
            self.assertNotIn(word, src)
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "daily-tickets.md")
            with open(target, "w", encoding="utf-8") as handle:
                handle.write("keep\n")
            code = pll.main([
                "--prompts", PROMPTS, "--map", MAP_MD, "--queue", QUEUE,
                "--catalog", CATALOG, "--bank", BANK,
                "--ledger", os.path.join(tmp, "missing.json"),
                "--report", target,
                "--proposals", os.path.join(tmp, "proposals.md"),
            ])
            self.assertEqual(code, 2)
            with open(target, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "keep\n")

    def test_committed_docs_match_render(self):
        result = pll.run({
            "prompts": PROMPTS,
            "map": MAP_MD,
            "queue": QUEUE,
            "ledger": os.path.join(ROOT, "data", "ai_visibility", "observations.json"),
            "catalog": CATALOG,
            "bank": BANK,
        })
        with open(REPORT, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), pll.render_report(result, result["meta"]))
        with open(PROPOSALS, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), pll.render_proposals(result))


if __name__ == "__main__":
    unittest.main()

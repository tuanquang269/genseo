"""Shilajit Shockwave copy follows its OCR-accepted pack-label whitelist.

product_refs/shilajit-shockwave.label.json lists identity lines only.
No milligram, serving count, or volume token is in that whitelist.
Premium Himalayan Shilajit Gummies, Gold Resin, and ShilaSource resin are out of scope.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import brand_rules as br
import refill_tickets as rt
import shockwave_rules as sw
import topic_fitness as tf

LABEL = os.path.join(ROOT, "product_refs", "shilajit-shockwave.label.json")
ACCEPTED = [
    "wellness",
    "nest",
    "SHILAJIT",
    "SHOCKWAVE",
    "EXPERIENCE FOCUSED ENERGY",
    "PEAK PERFORMANCE",
]
_DOSE = re.compile(r"\d|mg\b|ml\b|oz\b|serving|drop|cfu\b|\biu\b", re.I)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


class WhitelistFile(unittest.TestCase):
    def test_pack_file_is_identity_lines_only(self):
        tokens = sw.load_label()
        with open(LABEL, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["required"], ACCEPTED)
        self.assertEqual(data.get("optional") or [], [])
        self.assertEqual(tokens, data["required"] + (data.get("optional") or []))
        for token in tokens:
            self.assertIsNone(_DOSE.search(token), token)
        self.assertNotIn("®", "".join(tokens))
        self.assertNotIn("™", "".join(tokens))
        self.assertIn("30 ml", data["source"])
        self.assertIn("fl oz", data["source"])
        self.assertNotIn("30 ml", " ".join(tokens))
        self.assertNotIn("1 fl oz", " ".join(tokens))
        for phrase in ("500 mg", "250 mg", "1,500 mg", "30 ml", "1 fl oz", "1 oz",
                       "30 servings", "10 drops", "75%"):
            self.assertFalse(sw.listed(phrase, tokens), phrase)
        raw = read("product_refs/shilajit-shockwave.label.json")
        self.assertTrue(sw.violations(raw))

    def test_allowlist_follows_the_file(self):
        self.assertEqual(
            sw.violations("Shilajit Shockwave provides 500 mg.", tokens=["500 mg"]), [])
        self.assertEqual(
            sw.violations("Shilajit Shockwave is 30 ml.", tokens=["30 ml"]), [])
        self.assertEqual(
            sw.violations("Shilajit Shockwave is 1 fl oz.", tokens=["1 fl oz"]), [])
        self.assertTrue(sw.violations("Shilajit Shockwave provides 500 mg."))
        self.assertTrue(sw.violations("Shilajit Shockwave is 30 ml."))
        self.assertEqual(
            sw.violations("Shilajit Shockwave is a dropper bottle.", tokens=[]),
            [sw._PREFIX + "pack label whitelist is missing or empty (" + sw.LABEL_REL + ")"])
        self.assertEqual(sw.violations("Pure Shilajit Gold Resin, 500 mg.", tokens=[]), [])

    def test_ticket_and_landing_lines_invent_no_dose(self):
        for text in (sw.LABEL_LINE, sw.TICKET_LINE, sw.LANDING_NOTE):
            self.assertIsNone(re.search(r"\d", text), text)
            self.assertIsNone(re.search(r"\b(?:mg|ml|fl\s*oz)\b", text, re.I), text)


class LabelCopyPasses(unittest.TestCase):
    def test_identity_lines_pass_every_gate(self):
        for text in (
            sw.LABEL_LINE,
            sw.TICKET_LINE,
            sw.LANDING_NOTE,
            "Shilajit Shockwave. EXPERIENCE FOCUSED ENERGY. PEAK PERFORMANCE.",
            "Shilajit Shockwave drops are $79.99.",
            "/products/shilajit-shockwave is the drops format.",
            "Shilajit Shockwave does not list a milligram amount or a serving count.",
            "Do not add a volume line for Shilajit Shockwave.",
        ):
            self.assertEqual(sw.violations(text), [], text)
            self.assertEqual(br.violations(text), [], text)
            self.assertEqual(br.assess(text).action, "allow", text)
            self.assertEqual(br.prepare_ticket(text), text)

    def test_mark_is_not_required(self):
        text = "Shilajit Shockwave. wellness nest. PEAK PERFORMANCE."
        self.assertNotIn("®", text)
        self.assertEqual(br.violations(text), [])

    def test_context_that_must_stay_allowed(self):
        for text in (
            "Unlike other brands' 500 mg, Shilajit Shockwave lists no milligram on the pack.",
            "Shilajit Shockwave is not 30 servings and not 1 fl oz.",
            "| Shilajit Shockwave | drops |\n| Brand X | 500 mg | 30 servings | 30 ml |",
            "Premium Himalayan Shilajit Gummies list 1500 mg, 60 gummies, and a 60-day supply.",
            "Pure Shilajit Gold Resin, 1.06 oz (30g) - 75 servings, 75% Fulvic.",
            "ShilaSource resin, 70% Fulvic Acid, 1.06oz (30g), 75 servings.",
            "FusiForce has 90 gummies.",
            "FloraFresh: Vitamin C 30 mg per 2 gummies, 15B CFU.",
            "The trial used 250 mg of purified shilajit. Shilajit Shockwave is a dropper bottle.",
            "Premium Himalayan Shilajit Gummies are 60 gummies and a 60-day supply. "
            "Shilajit Shockwave is a dropper bottle.",
            "AgeAura Pure NMN + TMG provides 500 mg NMN. Shilajit Shockwave is a dropper bottle.",
            "Shilajit Shockwave is a dropper bottle. A 60-day trial of ashwagandha lowered stress scores.",
        ):
            self.assertEqual(br.violations(text), [], text)

    def test_other_products_in_the_same_piece_keep_their_own_doses(self):
        text = "\n".join([
            "Shilajit Shockwave is sold as drops.",
            "FloraFresh: per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 15B CFU, "
            "Vitamin C 30 mg and pineapple fruit powder 100 mg.",
            "FusiForce Creatine Monohydrate Gummies, 90 gummies.",
            "Premium Himalayan Shilajit Gummies, 60 gummies, 60-day supply.",
            "Pure Shilajit Gold Resin is a jar.",
        ])
        self.assertEqual(sw.violations(text), [])
        self.assertEqual(br.violations(text), [])


class InventedDosesRejected(unittest.TestCase):
    def assertRejected(self, text, *needles):
        bad = br.violations(text)
        self.assertTrue(bad, text)
        self.assertEqual(br.assess(text).action, "deny", text)
        with self.assertRaises(br.GuardError):
            br.prepare_ticket(text)
        with self.assertRaises(br.GuardError):
            br.assert_publishable("Shilajit Shockwave", text)
        for needle in needles:
            self.assertTrue(any(needle in reason for reason in bad), (needle, bad, text))
        return bad

    def test_milligrams_fail(self):
        self.assertRejected("Shilajit Shockwave provides 500 mg per serving.", "500 mg")
        self.assertRejected("Shilajit Shockwave delivers 250 milligrams.", "250 mg")
        self.assertRejected("/products/shilajit-shockwave lists 1,500 mg.", "1,500 mg")
        self.assertRejected("Shilajit Shockwave contains five hundred milligrams.", "five hundred milligrams")
        self.assertRejected("<p>Shilajit Shockwave</p><p>500 mg of shilajit.</p>", "500 mg")

    def test_servings_and_volume_fail(self):
        self.assertRejected("Shilajit Shockwave has 30 servings.", "30 servings")
        self.assertRejected("Shilajit Shockwave: servings per bottle 30.", "30 servings")
        self.assertRejected("Shilajit Shockwave, thirty servings.", "30 servings")
        self.assertRejected("Shilajit Shockwave is 1 fl oz (30 ml).", "1 fl oz", "30 ml")
        self.assertRejected("Shilajit Shockwave is 1 fluid ounce.", "1 fl oz")
        self.assertRejected("Shilajit Shockwave, 10 drops per serving.", "10 drops")
        self.assertRejected("Shilajit Shockwave, 1 dropper a day.", "1 dropper")

    def test_other_doses_fail(self):
        self.assertRejected("Shilajit Shockwave is 75% fulvic acid.", "75%")
        self.assertRejected("Shilajit Shockwave provides 1 billion CFU.", "1 billion CFU")
        self.assertRejected("Shilajit Shockwave, 5 g per serving.", "5 g")
        self.assertRejected("Shilajit Shockwave, 200 mcg per serving.", "200 mcg")
        self.assertRejected("Shilajit Shockwave is a 60-day supply.", "60-day supply")
        self.assertRejected("Shilajit Shockwave, 60 gummies.", "60 gummies")

    def test_unowned_milligram_in_the_same_piece_fails(self):
        self.assertRejected(
            "Shilajit Shockwave is a dropper bottle. Many labels print 500 mg.",
            "500 mg")


class Gates(unittest.TestCase):
    def test_topic_fitness_code(self):
        verdict, code, _why = tf.assess("Shilajit Shockwave 500 mg review", articles=[])
        self.assertEqual((verdict, code), ("FAIL", "shockwave-label"))
        verdict, code, _why = tf.assess("Shilajit Shockwave review", articles=[])
        self.assertEqual(verdict, "PASS")
        self.assertNotEqual(code, "shockwave-label")
        self.assertEqual(tf.assess("Premium Himalayan Shilajit Gummies 1500 mg review", articles=[])[0], "PASS")

    def test_landing_spec_fields(self):
        clean = {
            "handle": "shilajit-shockwave",
            "title": "Shilajit Shockwave",
            "product": {"bullets": ["EXPERIENCE FOCUSED ENERGY", "PEAK PERFORMANCE"]},
            "items": [{"body": "Drops format.", "source": "A PDP once claimed 500 mg."}],
        }
        self.assertEqual(sw.spec_violations(clean), [])
        self.assertEqual(br.spec_violations(clean), [])
        bad = {
            "handle": "shilajit-shockwave",
            "title": "Shilajit Shockwave",
            "product": {"bullets": ["500 mg shilajit"]},
            "sources": ["A trial used 250 mg of shilajit."],
            "items": [{"chart": {"source": "250 mg per serving"}}],
        }
        reasons = br.spec_violations(bad)
        self.assertTrue(any("500 mg" in r and "product" in r for r in reasons), reasons)
        self.assertTrue(any("250 mg" in r and "chart" in r for r in reasons), reasons)
        self.assertFalse(any("sources" in r for r in reasons), reasons)

    def test_image_prompt_refuses_an_invented_dose(self):
        with self.assertRaises(br.GuardError):
            br.prepare_image_request(
                "Draw Shilajit Shockwave with 500 mg on the label.",
                ["shilajit-shockwave"])
        prompt, handles = br.prepare_image_request(
            "Draw Shilajit Shockwave, PEAK PERFORMANCE, no invented dose.",
            ["shilajit-shockwave"])
        self.assertIn("shilajit-shockwave", handles)
        self.assertIn("PEAK PERFORMANCE", prompt)

    def test_refill_line_and_queue(self):
        bank = rt.load_bank(rt.BANK)
        errs = rt.lint_bank(bank)
        self.assertEqual(errs, [], errs[:4])
        ctx = rt.fixture_ctx(bank, rt.parse_queue(rt.FIX_QUEUE))
        cand = rt.norm_cand(dict(
            rt.FIX_GOOD, id="sw", product="shilajit-shockwave",
            primary="shilajit shockwave for athletes",
            title="Shilajit Shockwave for Athletes (US 2026)",
            secondary=["shockwave drops for training"], segment="athletes",
            intent="athlete comparing a drops format", template="EDITORIAL",
            angle="What the drops format changes about a daily routine.",
            fanout=["how do you take shilajit drops"],
            evidence="Pack label identity lines only.", link=[]), bank, "topic-bank", 1, 0)
        info = {"verdict": ("PASS", "brand"), "suggest": "offline",
                "colls": ["shilajit-wellness-stack", "mens-essential-collection"], "links": []}
        text = rt.render(cand, "CA1009-9", ctx, info)
        self.assertIn(sw.TICKET_LINE, text)
        self.assertEqual(br.violations(text), [])
        price = next(t for t in bank["topics"] if t["id"] == "shilajit-price")
        brief = " ".join([price["primary"], price["title"], price["intent"], price["angle"],
                          price["evidence"]] + price["secondary"] + price["fanout"])
        self.assertIn("Shockwave", brief)
        self.assertEqual(sw.violations(brief), [])

    def test_lint_open_ticket_only(self):
        body = (
            "- [ ] **#T — shockwave** — `Shilajit Shockwave (US 2026)`\n"
            "  - Shilajit Shockwave provides 500 mg.\n"
            "## [DONE] old\n"
            "  - Shilajit Shockwave provides 500 mg.\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
            fh.write(body)
            path = fh.name
        try:
            proc = subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "lint_tickets.py"), path],
                capture_output=True, text=True)
        finally:
            os.remove(path)
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("500 mg", proc.stdout)
        self.assertEqual(proc.stdout.count("BANNED"), 1)

    def test_call_sites_use_the_guard(self):
        for rel in ("scripts/brand_rules.py", "scripts/topic_fitness.py", "scripts/refill_tickets.py",
                    "scripts/build_landing_tickets.py", "scripts/shopify_publisher.py"):
            self.assertIn("shockwave_rules", read(rel), rel)
        self.assertIn("shockwave.spec_violations", read("scripts/brand_rules.py"))
        self.assertIn("shockwave-label", read("scripts/topic_fitness.py"))
        self.assertIn("FAIL [shockwave-label]", read("docs/SHOCKWAVE_LABEL_GUARD.md"))
        for rel in ("scripts/validate_article.py", "scripts/validate_landing.py",
                    "scripts/lint_tickets.py", "scripts/run_ticket_headless.sh",
                    "scripts/run_landing_headless.sh"):
            self.assertIn("shockwave_rules", read(rel), rel)

    def test_cli(self):
        script = os.path.join(ROOT, "scripts", "shockwave_rules.py")
        proc = subprocess.run([sys.executable, script, "--brief"], capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, sw.TICKET_LINE))
        proc = subprocess.run(
            [sys.executable, script, "Shilajit Shockwave provides 500 mg."],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("500 mg", proc.stdout)
        proc = subprocess.run(
            [sys.executable, script, "Shilajit Shockwave. PEAK PERFORMANCE."],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout)


if __name__ == "__main__":
    unittest.main()

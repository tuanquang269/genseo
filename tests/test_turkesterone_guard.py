"""Turkesterone Advanced Formula copy follows its OCR-accepted pack-label whitelist.

product_refs/turkesterone-advanced-formula.label.json lists front-of-pack lines.
The capsule badge is the separate lines 60 and Capsules. No milligram token is
in that whitelist. Bare "turkesterone" (the ingredient) is out of scope.
Premium Himalayan Shilajit Gummies, Shilajit Shockwave, Pure Shilajit Gold
Resin, and ShilaSource resin are out of scope.
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
import gold_resin_rules as gr
import refill_tickets as rt
import shockwave_rules as sw
import shilasource_resin_rules as sr
import topic_fitness as tf
import turkesterone_rules as tk

LABEL = os.path.join(ROOT, "product_refs", "turkesterone-advanced-formula.label.json")
ACCEPTED = [
    "wellness",
    "nest",
    "PREMIUM",
    "TURKESTERONE",
    "ADVANCED",
    "FORMULA",
    "AMPLIFY",
    "MUSCLE",
    "ENDURANCE",
    "60",
    "Dietary Supplement",
    "Capsules",
]


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


class WhitelistFile(unittest.TestCase):
    def test_pack_file_is_the_agreeing_ocr_lines_only(self):
        tokens = tk.load_label()
        with open(LABEL, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["handle"], tk.HANDLE)
        self.assertEqual(data["required"], ACCEPTED)
        self.assertEqual(data.get("optional") or [], [])
        self.assertEqual(data["accepted_ocr"], ACCEPTED)
        self.assertEqual(tokens, data["required"] + (data.get("optional") or []))
        joined = " ".join(tokens)
        self.assertIn("TURKESTERONE", joined)
        self.assertIn("Dietary Supplement", joined)
        self.assertNotIn("TURNESTERONE", joined)
        self.assertNotIn("mg", joined.lower())
        self.assertNotIn("KSM-66", joined)
        self.assertNotIn("Ashwagandha", joined)
        self.assertNotIn("BioPerine", joined)
        self.assertNotIn("Colostrum", joined)
        self.assertIn("TURNESTERONE", data["source"])
        self.assertIn("not copied", data["source"])
        self.assertIn("not corrected", data["source"])
        self.assertIn("KSM-66?Ashwagandha", data["source"])
        self.assertIn("BioPerineBlackPepper", data["source"])
        self.assertIn("Supplement Facts", data["source"])
        self.assertIn("no milligram token", data["source"])
        self.assertIn("rapidocr", data["source"].lower())
        self.assertIn("None scored confidence 1.00", data["source"])
        for leftover in ("TURNESTERONE", "KSM-66", "Ashwagandha", "BioPerine", "Colostrum", "milligram"):
            self.assertNotIn(leftover, joined)
        self.assertIn("Not confirmed", data["mark"])
        self.assertEqual(tk.allowed_phrases(tokens), ["60 capsules"])
        raw = read("product_refs/turkesterone-advanced-formula.label.json")
        self.assertEqual(tk.violations(raw), [])
        module = read("scripts/turkesterone_rules.py")
        for banned in ("TURKESTERONE", "TURNESTERONE", "Ashwagandha", "BioPerine", "KSM-66"):
            self.assertNotIn(banned, module)
        self.assertNotIn("60 capsules", module.lower())

    def test_allowlist_follows_the_file(self):
        self.assertEqual(
            tk.violations("Turkesterone Advanced Formula provides 500 mg.", tokens=["500 mg"]), [])
        self.assertEqual(
            tk.violations("Turkesterone Advanced Formula is 30 capsules.", tokens=["30 capsules"]), [])
        self.assertTrue(tk.violations("Turkesterone Advanced Formula provides 500 mg."))
        self.assertTrue(tk.violations("Turkesterone Advanced Formula is 30 capsules."))
        self.assertEqual(
            tk.violations("Turkesterone Advanced Formula is a jar.", tokens=[]),
            [tk._PREFIX + "pack label whitelist is missing or empty (" + tk.LABEL_REL + ")"])
        self.assertEqual(tk.violations("Shilajit Shockwave provides 500 mg.", tokens=[]), [])
        self.assertEqual(tk.violations("turkesterone, 500 mg per serving."), [])

    def test_ticket_and_landing_lines_match_the_file(self):
        for text in (tk.LABEL_LINE, tk.TICKET_LINE, tk.LANDING_NOTE):
            self.assertIn("TURKESTERONE", text)
            self.assertIn("Capsules", text)
            self.assertEqual(tk.violations(text), [], text)
            self.assertEqual(sw.violations(text), [], text)
            self.assertEqual(gr.violations(text), [], text)
            self.assertEqual(sr.violations(text), [], text)
            self.assertNotIn("TURNESTERONE", text)
            self.assertNotIn("mg", re.sub(r"milligram", "", text, flags=re.I).lower())


class LabelCopyPasses(unittest.TestCase):
    def test_whitelist_lines_pass_every_gate(self):
        for text in (
            tk.LABEL_LINE,
            tk.TICKET_LINE,
            tk.LANDING_NOTE,
            "Turkesterone Advanced Formula. PREMIUM TURKESTERONE. ADVANCED FORMULA. Dietary Supplement.",
            "Turkesterone Advanced Formula, 60 capsules.",
            "Premium Turkesterone is sixty capsules.",
            "Turkesterone Advanced, 60 caps.",
            "/products/turkesterone-advanced-formula is 60 capsules.",
            "Turkesterone Advanced Formula does not list a milligram amount.",
            "Do not add a milligram serving for Turkesterone Advanced Formula.",
            "Turkesterone Advanced Formula is not 500 mg and not 30 capsules.",
            "Turkesterone Advanced Formula for lifters over 60.",
            "Turkesterone Advanced Formula is $75.",
        ):
            self.assertEqual(tk.violations(text), [], text)
            self.assertEqual(br.violations(text), [], text)
            self.assertEqual(br.assess(text).action, "allow", text)
            self.assertEqual(br.prepare_ticket(text), text)

    def test_mark_is_not_required(self):
        text = "Turkesterone Advanced Formula. wellness nest. Dietary Supplement."
        self.assertNotIn("®", text)
        self.assertNotIn("™", text)
        self.assertEqual(br.violations(text), [])

    def test_context_that_must_stay_allowed(self):
        for text in (
            "Unlike other brands' 500 mg, Turkesterone Advanced Formula lists no milligram on the pack.",
            "Turkesterone Advanced Formula is not 30 capsules and not 30 servings.",
            "| Turkesterone Advanced Formula | jar |\n| Brand X | 500 mg | 30 servings | 90 capsules |",
            "Premium Himalayan Shilajit Gummies list 1500 mg, 60 gummies, and a 60-day supply.",
            "ShilaSource resin, 70% Fulvic Acid, 1.06oz (30g), 75 servings.",
            "FusiForce has 90 gummies and 30 servings.",
            "FloraFresh: Vitamin C 30 mg per 2 gummies, 1 billion CFU.",
            "The trial used 250 mg of turkesterone. Turkesterone Advanced Formula is a jar.",
            "A randomized trial of turkesterone used 10 mg. Turkesterone Advanced Formula is a jar.",
            "Premium Himalayan Shilajit Gummies are 60 gummies and a 60-day supply. "
            "Turkesterone Advanced Formula is a jar.",
            "AgeAura Pure NMN + TMG provides 500 mg NMN. Turkesterone Advanced Formula is a jar.",
            "Turkesterone Advanced Formula is a jar. A randomized trial of turkesterone. The dose was 250 mg.",
            "turkesterone 500 mg is a trial dose, not this jar.",
            tk.TICKET_LINE + "\n" + sw.TICKET_LINE,
        ):
            self.assertEqual(tk.violations(text), [], text)
            self.assertEqual(br.violations(text), [], text)

    def test_other_products_in_the_same_piece_keep_their_own_doses(self):
        text = "\n".join([
            "Turkesterone Advanced Formula, 60 capsules. Dietary Supplement.",
            "Shilajit Shockwave, EXPERIENCE FOCUSED ENERGY, PEAK PERFORMANCE.",
            "FloraFresh: per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, "
            "Vitamin C 30 mg and pineapple fruit powder 100 mg.",
            "FusiForce Creatine Monohydrate Gummies, 90 gummies.",
            "Premium Himalayan Shilajit Gummies, 60 gummies, 60-day supply, 1500 mg.",
            "ShilaSource Himalayan Shilajit Resin, 70% Fulvic Acid, 1.06oz (30g), 75 servings.",
            "Pure Shilajit Gold Resin, 75% Fulvic, 1.06 oz (30g) - 75 servings.",
        ])
        self.assertEqual(tk.violations(text), [])
        self.assertEqual(br.violations(text), [])

    def test_other_guards_still_fire(self):
        self.assertTrue(br.violations("Shilajit Shockwave provides 500 mg."))
        self.assertEqual(br.violations("Shilajit Shockwave. PEAK PERFORMANCE."), [])
        self.assertTrue(br.violations("FloraFresh delivers 15 billion CFU."))
        self.assertTrue(br.violations("AgeAura Pure Urolithin A"))
        self.assertEqual(br.violations("AgeAura Pure NMN + TMG NAD Complex"), [])
        self.assertEqual(sw.violations("Turkesterone Advanced Formula has 30 capsules."), [])
        self.assertEqual(tk.violations("Shilajit Shockwave provides 500 mg and 30 servings."), [])
        self.assertTrue(br.violations("Shilajit Shockwave provides 500 mg and 30 servings."))
        self.assertEqual(tk.violations("ShilaSource resin, 300 mg per serving."), [])
        self.assertTrue(br.violations("ShilaSource resin, 300 mg per serving."))

    def test_bank_topics_do_not_invent_a_dose(self):
        bank = json.loads(read("templates/article-topic-bank.json"))
        for topic in bank["topics"]:
            if topic.get("product") != tk.HANDLE:
                continue
            blob = " ".join([
                topic.get("primary") or "",
                topic.get("title") or "",
                topic.get("intent") or "",
                topic.get("angle") or "",
                topic.get("evidence") or "",
                " ".join(topic.get("secondary") or []),
                " ".join(topic.get("fanout") or []),
                tk.TICKET_LINE,
            ])
            self.assertEqual(tk.violations(blob), [], topic["id"])
            self.assertEqual(br.violations(blob), [], topic["id"])


class InventedDosesRejected(unittest.TestCase):
    def assertRejected(self, text, *needles):
        bad = br.violations(text)
        self.assertTrue(bad, text)
        self.assertEqual(br.assess(text).action, "deny", text)
        with self.assertRaises(br.GuardError):
            br.prepare_ticket(text)
        with self.assertRaises(br.GuardError):
            br.assert_publishable("Turkesterone Advanced Formula", text)
        for needle in needles:
            self.assertTrue(any(needle in reason for reason in bad), (needle, bad, text))
        return bad

    def test_milligrams_fail(self):
        self.assertRejected("Turkesterone Advanced Formula provides 500 mg per serving.", "500 mg")
        self.assertRejected("Premium Turkesterone delivers 250 milligrams.", "250 mg")
        self.assertRejected("/products/turkesterone-advanced-formula lists 1,500 mg.", "1500 mg")
        self.assertRejected("Turkesterone Advanced contains five hundred milligrams.", "five hundred milligrams")
        self.assertRejected("<p>Turkesterone Advanced Formula</p><p>500 mg of turkesterone.</p>", "500 mg")
        self.assertRejected("Turkesterone Advanced Formula provides 60 mg.", "60 mg")

    def test_other_counts_and_day_supply_fail(self):
        self.assertRejected("Turkesterone Advanced Formula has 30 capsules.", "30 capsules")
        self.assertRejected("Turkesterone Advanced Formula has 90 capsules.", "90 capsules")
        self.assertRejected("Turkesterone Advanced Formula, thirty capsules.", "30 capsules")
        self.assertRejected("Turkesterone Advanced Formula has 60 servings.", "60 servings")
        self.assertRejected("Turkesterone Advanced Formula: servings per jar 30.", "30 servings")
        self.assertRejected("Turkesterone Advanced Formula is a 30-day supply.", "30-day supply")
        self.assertRejected("Turkesterone Advanced Formula is a 60-day supply.", "60-day supply")
        self.assertRejected("Turkesterone Advanced Formula, 60 caplets.", "60 caplets")
        self.assertRejected("Turkesterone Advanced Formula, 60 tablets.", "60 tablets")
        self.assertRejected("Turkesterone Advanced Formula is standardized to 10%.", "10%")
        self.assertRejected("Turkesterone Advanced Formula is 2 g per serving.", "2 g")

    def test_other_doses_fail(self):
        self.assertRejected("Turkesterone Advanced Formula provides 1 billion CFU.", "1 billion CFU")
        self.assertRejected("Turkesterone Advanced Formula, 200 mcg per serving.", "200 mcg")
        self.assertRejected("Turkesterone Advanced Formula, 60 gummies.", "60 gummies")
        self.assertRejected("Turkesterone Advanced Formula, 1000 IU.", "1000 IU")
        self.assertRejected("Turkesterone Advanced Formula, 10 drops per serving.", "10 drops")

    def test_bare_60_does_not_allow_a_milligram_or_a_serving_count(self):
        self.assertRejected("Turkesterone Advanced Formula provides 60 mg.", "60 mg")
        self.assertRejected("Turkesterone Advanced Formula has 60 servings.", "60 servings")

    def test_unowned_milligram_in_the_same_piece_fails(self):
        self.assertRejected(
            "Turkesterone Advanced Formula is a jar. Many labels print 500 mg.",
            "500 mg")

    def test_naming_the_sku_in_a_study_dose_fails(self):
        self.assertRejected(
            "A trial of Turkesterone Advanced Formula used 250 mg of turkesterone.",
            "250 mg")


class Gates(unittest.TestCase):
    def test_topic_fitness_code(self):
        verdict, code, _why = tf.assess("Turkesterone Advanced Formula 500 mg review", articles=[])
        self.assertEqual((verdict, code), ("FAIL", "turkesterone-label"))
        verdict, code, _why = tf.assess("Turkesterone Advanced Formula review", articles=[])
        self.assertEqual(verdict, "PASS")
        self.assertNotEqual(code, "turkesterone-label")
        ingredient = tf.assess("turkesterone 500 mg review", articles=[])
        self.assertEqual(ingredient[0], "PASS")
        self.assertNotEqual(ingredient[1], "turkesterone-label")
        self.assertEqual(tf.assess("Shilajit Shockwave 500 mg review", articles=[])[1], "shockwave-label")
        self.assertEqual(tf.assess("FloraFresh 15 billion CFU review", articles=[])[1], "florafresh-formula")

    def test_landing_spec_fields(self):
        clean = {
            "handle": "turkesterone-advanced-formula",
            "title": "Turkesterone Advanced Formula",
            "product": {"bullets": ["60 capsules", "Dietary Supplement"]},
            "items": [{"body": "Jar front.", "source": "A PDP once claimed 500 mg."}],
        }
        self.assertEqual(tk.spec_violations(clean), [])
        self.assertEqual(br.spec_violations(clean), [])
        bad = {
            "handle": "turkesterone-advanced-formula",
            "title": "Turkesterone Advanced Formula",
            "product": {"bullets": ["500 mg turkesterone"]},
            "sources": ["A trial used 250 mg of turkesterone."],
            "items": [{"chart": {"source": "30 capsules per jar"}}],
        }
        reasons = br.spec_violations(bad)
        self.assertTrue(any("500 mg" in r and "product" in r for r in reasons), reasons)
        self.assertTrue(any("30 capsules" in r and "chart" in r for r in reasons), reasons)
        self.assertFalse(any("sources" in r for r in reasons), reasons)

    def test_image_prompt_refuses_an_invented_dose(self):
        with self.assertRaises(br.GuardError):
            br.prepare_image_request(
                "Draw Turkesterone Advanced Formula with 500 mg on the label.",
                ["turkesterone-advanced-formula"])
        prompt, handles = br.prepare_image_request(
            "Draw Turkesterone Advanced Formula, 60 capsules, Dietary Supplement.",
            ["turkesterone-advanced-formula"])
        self.assertIn("turkesterone-advanced-formula", handles)
        self.assertIn("60 capsules", prompt)

    def test_refill_line_is_on_the_module(self):
        self.assertEqual(rt.tk.HANDLE, tk.HANDLE)
        self.assertIn("60", tk.TICKET_LINE)
        self.assertIn("Capsules", tk.LANDING_NOTE)
        self.assertEqual(tk.violations(tk.TICKET_LINE), [])
        self.assertEqual(br.violations(tk.LANDING_NOTE + " product=" + tk.HANDLE), [])

    def test_lint_open_ticket_only(self):
        body = (
            "- [ ] **#T — turkesterone** — `Turkesterone Advanced Formula (US 2026)`\n"
            "  - Turkesterone Advanced Formula provides 500 mg.\n"
            "## [DONE] old\n"
            "  - Turkesterone Advanced Formula provides 500 mg.\n"
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
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("500 mg", proc.stdout)
        self.assertEqual(proc.stdout.count("BANNED"), 1)

    def test_call_sites_use_the_guard(self):
        for rel in ("scripts/brand_rules.py", "scripts/topic_fitness.py", "scripts/refill_tickets.py",
                    "scripts/build_landing_tickets.py", "scripts/shopify_publisher.py"):
            self.assertIn("turkesterone_rules", read(rel), rel)
        self.assertIn("turkesterone.spec_violations", read("scripts/brand_rules.py"))
        self.assertIn("turkesterone-label", read("scripts/topic_fitness.py"))
        self.assertIn("FAIL [turkesterone-label]", read("docs/TURKESTERONE_LABEL_GUARD.md"))
        for rel in ("scripts/validate_article.py", "scripts/validate_landing.py",
                    "scripts/lint_tickets.py", "scripts/run_ticket_headless.sh",
                    "scripts/run_landing_headless.sh"):
            self.assertIn("turkesterone_rules", read(rel), rel)

    def test_cli(self):
        script = os.path.join(ROOT, "scripts", "turkesterone_rules.py")
        proc = subprocess.run([sys.executable, script, "--brief"], capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, tk.TICKET_LINE))
        proc = subprocess.run(
            [sys.executable, script, "Turkesterone Advanced Formula provides 500 mg."],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("500 mg", proc.stdout)
        proc = subprocess.run(
            [sys.executable, script, "Turkesterone Advanced Formula, 60 capsules."],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout)


if __name__ == "__main__":
    unittest.main()

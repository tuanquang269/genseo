"""Pure Shilajit Gold Resin copy follows its OCR-accepted pack-label whitelist.

product_refs/pure-shilajit-gold-resin.label.json lists identity lines, 75% Fulvic,
and the serving line 1.06 oz (30g) - 75 servings. No milligram token is in that
whitelist. Premium Himalayan Shilajit Gummies, Shilajit Shockwave, and
ShilaSource resin are out of scope.
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
import topic_fitness as tf

LABEL = os.path.join(ROOT, "product_refs", "pure-shilajit-gold-resin.label.json")
ACCEPTED = [
    "wellness",
    "nest",
    "Himalayan",
    "Shilajit",
    "75% Fulvic",
    "Lab-Tested",
    "Acid",
    "Pure Shilajit Gold Resin",
    "1.06 oz (30g) - 75 servings",
    "Dietary Supplements",
]
SERVING = "1.06 oz (30g) - 75 servings"


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


class WhitelistFile(unittest.TestCase):
    def test_pack_file_is_the_ocr_lines_only(self):
        tokens = gr.load_label()
        with open(LABEL, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["required"], ACCEPTED)
        self.assertEqual(data.get("optional") or [], [])
        self.assertEqual(tokens, data["required"] + (data.get("optional") or []))
        self.assertEqual(data["accepted_ocr"], ACCEPTED)
        joined = " ".join(tokens)
        self.assertIn(SERVING, joined)
        self.assertIn("75% Fulvic", joined)
        self.assertNotIn("mg", joined.lower())
        self.assertNotIn("®", joined)
        self.assertNotIn("™", joined)
        self.assertIn("No milligram serving was read", data["source"])
        self.assertIn("S0g", data["source"])
        self.assertIn("serviogs", data["source"])
        self.assertIn("Sepplements", data["source"])
        self.assertIn("tor Purity", data["source"])
        for leftover in ("S0g", "serviogs", "Sepplements", "tor Purity", "milligram"):
            self.assertNotIn(leftover, joined)
        self.assertIn("Not confirmed", data["mark"])
        self.assertEqual(
            sorted(gr.allowed_phrases(tokens)),
            ["1.06 oz", "30 g", "75 servings", "75%"])
        raw = read("product_refs/pure-shilajit-gold-resin.label.json")
        self.assertEqual(gr.violations(raw), [])
        self.assertNotIn("1.06", read("scripts/gold_resin_rules.py"))

    def test_allowlist_follows_the_file(self):
        self.assertEqual(
            gr.violations("Pure Shilajit Gold Resin provides 500 mg.", tokens=["500 mg"]), [])
        self.assertEqual(
            gr.violations("Pure Shilajit Gold Resin is 30 servings.", tokens=["30 servings"]), [])
        self.assertTrue(gr.violations("Pure Shilajit Gold Resin provides 500 mg."))
        self.assertTrue(gr.violations("Pure Shilajit Gold Resin is 30 servings."))
        self.assertEqual(
            gr.violations("Pure Shilajit Gold Resin is a jar.", tokens=[]),
            [gr._PREFIX + "pack label whitelist is missing or empty (" + gr.LABEL_REL + ")"])
        self.assertEqual(gr.violations("Shilajit Shockwave provides 500 mg.", tokens=[]), [])
        self.assertEqual(gr.violations("gold resin, 500 mg per serving."), [])

    def test_ticket_and_landing_lines_match_the_file(self):
        for text in (gr.LABEL_LINE, gr.TICKET_LINE, gr.LANDING_NOTE):
            self.assertIn("75% Fulvic", text)
            self.assertIn(SERVING, text)
            self.assertEqual(gr.violations(text), [], text)
            self.assertEqual(sw.violations(text), [], text)
            self.assertNotIn("mg", re.sub(r"milligram", "", text, flags=re.I).lower())


class LabelCopyPasses(unittest.TestCase):
    def test_whitelist_lines_pass_every_gate(self):
        for text in (
            gr.LABEL_LINE,
            gr.TICKET_LINE,
            gr.LANDING_NOTE,
            "Pure Shilajit Gold Resin. 75% Fulvic. Lab-Tested. " + SERVING + ". Dietary Supplements.",
            "Pure Shilajit Gold Resin is 75% fulvic acid.",
            "Pure Shilajit Gold Resin is 1.06 oz.",
            "Pure Shilajit Gold Resin is 1.06oz (30g).",
            "Pure Shilajit Gold Resin, 30 grams, 75 servings.",
            "Shilajit Gold Resin has 75 servings.",
            "Pure Shilajit Gold Resin, seventy-five servings.",
            "/products/pure-shilajit-gold-resin is " + SERVING + ".",
            "Pure Shilajit Gold Resin does not list a milligram amount.",
            "Do not add a milligram serving for Pure Shilajit Gold Resin.",
            "Pure Shilajit Gold Resin is not 500 mg and not 30 servings.",
        ):
            self.assertEqual(gr.violations(text), [], text)
            self.assertEqual(br.violations(text), [], text)
            self.assertEqual(br.assess(text).action, "allow", text)
            self.assertEqual(br.prepare_ticket(text), text)

    def test_mark_is_not_required(self):
        text = "Pure Shilajit Gold Resin. wellness nest. 75% Fulvic."
        self.assertNotIn("®", text)
        self.assertNotIn("™", text)
        self.assertEqual(br.violations(text), [])

    def test_context_that_must_stay_allowed(self):
        for text in (
            "Unlike other brands' 500 mg, Pure Shilajit Gold Resin lists no milligram on the pack.",
            "Pure Shilajit Gold Resin is not 30 servings and not 1 fl oz.",
            "| Pure Shilajit Gold Resin | jar |\n| Brand X | 500 mg | 30 servings | 30 ml |",
            "Premium Himalayan Shilajit Gummies list 1500 mg, 60 gummies, and a 60-day supply.",
            "ShilaSource resin, 300 mg per serving, 70% fulvic acid.",
            "FusiForce has 90 gummies and 30 servings.",
            "FloraFresh: Vitamin C 30 mg per 2 gummies, 1 billion CFU.",
            "The trial used 250 mg of purified shilajit. Pure Shilajit Gold Resin is a jar.",
            "Premium Himalayan Shilajit Gummies are 60 gummies and a 60-day supply. "
            "Pure Shilajit Gold Resin is a jar.",
            "AgeAura Pure NMN + TMG provides 500 mg NMN. Pure Shilajit Gold Resin is a jar.",
            "Pure Shilajit Gold Resin is a jar. A randomized trial of ashwagandha. The dose was 250 mg.",
            "Pure Shilajit Gold Resin is $75.",
            gr.TICKET_LINE + "\n" + sw.TICKET_LINE,
        ):
            self.assertEqual(gr.violations(text), [], text)
            self.assertEqual(br.violations(text), [], text)

    def test_other_products_in_the_same_piece_keep_their_own_doses(self):
        text = "\n".join([
            "Pure Shilajit Gold Resin, 75% Fulvic, " + SERVING + ".",
            "Shilajit Shockwave, EXPERIENCE FOCUSED ENERGY, PEAK PERFORMANCE.",
            "FloraFresh: per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, "
            "Vitamin C 30 mg and pineapple fruit powder 100 mg.",
            "FusiForce Creatine Monohydrate Gummies, 90 gummies.",
            "Premium Himalayan Shilajit Gummies, 60 gummies, 60-day supply, 1500 mg.",
            "ShilaSource Himalayan Shilajit Resin, 70% fulvic, 300 mg.",
        ])
        self.assertEqual(gr.violations(text), [])
        self.assertEqual(br.violations(text), [])

    def test_other_guards_still_fire(self):
        self.assertTrue(br.violations("Shilajit Shockwave provides 500 mg."))
        self.assertEqual(br.violations("Shilajit Shockwave. PEAK PERFORMANCE."), [])
        self.assertTrue(br.violations("FloraFresh delivers 15 billion CFU."))
        self.assertTrue(br.violations("AgeAura Pure Urolithin A"))
        self.assertEqual(br.violations("AgeAura Pure NMN + TMG NAD Complex"), [])
        self.assertEqual(sw.violations("Pure Shilajit Gold Resin has 30 servings."), [])
        self.assertEqual(gr.violations("Shilajit Shockwave provides 500 mg and 30 servings."), [])
        self.assertTrue(br.violations("Shilajit Shockwave provides 500 mg and 30 servings."))


class InventedDosesRejected(unittest.TestCase):
    def assertRejected(self, text, *needles):
        bad = br.violations(text)
        self.assertTrue(bad, text)
        self.assertEqual(br.assess(text).action, "deny", text)
        with self.assertRaises(br.GuardError):
            br.prepare_ticket(text)
        with self.assertRaises(br.GuardError):
            br.assert_publishable("Pure Shilajit Gold Resin", text)
        for needle in needles:
            self.assertTrue(any(needle in reason for reason in bad), (needle, bad, text))
        return bad

    def test_milligrams_fail(self):
        self.assertRejected("Pure Shilajit Gold Resin provides 500 mg per serving.", "500 mg")
        self.assertRejected("Pure Shilajit Gold Resin delivers 250 milligrams.", "250 mg")
        self.assertRejected("/products/pure-shilajit-gold-resin lists 1,500 mg.", "1500 mg")
        self.assertRejected("Shilajit Gold Resin contains five hundred milligrams.", "five hundred milligrams")
        self.assertRejected("<p>Pure Shilajit Gold Resin</p><p>500 mg of shilajit.</p>", "500 mg")

    def test_other_servings_volumes_and_day_supply_fail(self):
        self.assertRejected("Pure Shilajit Gold Resin has 30 servings.", "30 servings")
        self.assertRejected("Pure Shilajit Gold Resin: servings per jar 30.", "30 servings")
        self.assertRejected("Pure Shilajit Gold Resin, thirty servings.", "30 servings")
        self.assertRejected("Pure Shilajit Gold Resin, sixty servings.", "60 servings")
        self.assertRejected("Pure Shilajit Gold Resin has 7.5 servings.", "7.5 servings")
        self.assertRejected("Pure Shilajit Gold Resin is 7.5% fulvic acid.", "7.5%")
        self.assertRejected("Pure Shilajit Gold Resin has 175 servings.", "175 servings")
        self.assertRejected("Pure Shilajit Gold Resin is 1 fl oz (30 ml).", "1 fl oz", "30 ml")
        self.assertRejected("Pure Shilajit Gold Resin is 2 oz.", "2 oz")
        self.assertRejected("Pure Shilajit Gold Resin is 106 oz.", "106 oz")
        self.assertRejected("Pure Shilajit Gold Resin is 10.6 oz.", "10.6 oz")
        self.assertRejected("Pure Shilajit Gold Resin is 5 g per serving.", "5 g")
        self.assertRejected("Pure Shilajit Gold Resin is a 30-day supply.", "30-day supply")
        self.assertRejected("Pure Shilajit Gold Resin is a 75-day supply.", "75-day supply")
        self.assertRejected("Pure Shilajit Gold Resin, 10 drops per serving.", "10 drops")

    def test_other_doses_fail(self):
        self.assertRejected("Pure Shilajit Gold Resin is 70% fulvic acid.", "70%")
        self.assertRejected("Pure Shilajit Gold Resin is 80% pure.", "80%")
        self.assertRejected("Pure Shilajit Gold Resin provides 1 billion CFU.", "1 billion CFU")
        self.assertRejected("Pure Shilajit Gold Resin, 200 mcg per serving.", "200 mcg")
        self.assertRejected("Pure Shilajit Gold Resin, 60 gummies.", "60 gummies")
        self.assertRejected("Pure Shilajit Gold Resin, 1000 IU.", "1000 IU")

    def test_omitted_misread_is_not_a_dose_and_not_allowed(self):
        self.assertEqual(
            gr.violations("Pure Shilajit Gold Resin OCR note: S0g and 75 serviogs."), [])
        self.assertTrue(gr.violations("Pure Shilajit Gold Resin is 0 g."))

    def test_unowned_milligram_in_the_same_piece_fails(self):
        self.assertRejected(
            "Pure Shilajit Gold Resin is a jar. Many labels print 500 mg.",
            "500 mg")

    def test_naming_the_resin_in_a_study_dose_fails(self):
        self.assertRejected(
            "A trial of Pure Shilajit Gold Resin used 250 mg of purified shilajit.",
            "250 mg")


class Gates(unittest.TestCase):
    def test_topic_fitness_code(self):
        verdict, code, _why = tf.assess("Pure Shilajit Gold Resin 500 mg review", articles=[])
        self.assertEqual((verdict, code), ("FAIL", "gold-resin-label"))
        verdict, code, _why = tf.assess("Pure Shilajit Gold Resin review", articles=[])
        self.assertEqual(verdict, "PASS")
        self.assertNotEqual(code, "gold-resin-label")
        self.assertEqual(
            tf.assess("Premium Himalayan Shilajit Gummies 1500 mg review", articles=[])[0], "PASS")
        self.assertEqual(tf.assess("Shilajit Shockwave 500 mg review", articles=[])[1], "shockwave-label")
        self.assertEqual(tf.assess("FloraFresh 15 billion CFU review", articles=[])[1], "florafresh-formula")

    def test_landing_spec_fields(self):
        clean = {
            "handle": "pure-shilajit-gold-resin",
            "title": "Pure Shilajit Gold Resin",
            "product": {"bullets": ["75% Fulvic", SERVING]},
            "items": [{"body": "Jar format.", "source": "A PDP once claimed 500 mg."}],
        }
        self.assertEqual(gr.spec_violations(clean), [])
        self.assertEqual(br.spec_violations(clean), [])
        bad = {
            "handle": "pure-shilajit-gold-resin",
            "title": "Pure Shilajit Gold Resin",
            "product": {"bullets": ["500 mg shilajit"]},
            "sources": ["A trial used 250 mg of shilajit."],
            "items": [{"chart": {"source": "30 servings per jar"}}],
        }
        reasons = br.spec_violations(bad)
        self.assertTrue(any("500 mg" in r and "product" in r for r in reasons), reasons)
        self.assertTrue(any("30 servings" in r and "chart" in r for r in reasons), reasons)
        self.assertFalse(any("sources" in r for r in reasons), reasons)

    def test_image_prompt_refuses_an_invented_dose(self):
        with self.assertRaises(br.GuardError):
            br.prepare_image_request(
                "Draw Pure Shilajit Gold Resin with 500 mg on the label.",
                ["pure-shilajit-gold-resin"])
        prompt, handles = br.prepare_image_request(
            "Draw Pure Shilajit Gold Resin, 75% Fulvic, " + SERVING + ".",
            ["pure-shilajit-gold-resin"])
        self.assertIn("pure-shilajit-gold-resin", handles)
        self.assertIn("75% Fulvic", prompt)

    def test_refill_line_and_queue(self):
        bank = rt.load_bank(rt.BANK)
        errs = rt.lint_bank(bank)
        self.assertEqual(errs, [], errs[:4])
        ctx = rt.fixture_ctx(bank, rt.parse_queue(rt.FIX_QUEUE))
        cand = rt.norm_cand(dict(
            rt.FIX_GOOD, id="gr", product="pure-shilajit-gold-resin",
            primary="shilajit gold resin for athletes",
            title="Shilajit Gold Resin for Athletes (US 2026)",
            secondary=["gold resin jar for training"], segment="athletes",
            intent="athlete comparing a resin jar", template="EDITORIAL",
            angle="What the jar format changes about a daily routine.",
            fanout=["how do you take shilajit resin"],
            evidence="Pack label lines only.", link=[]), bank, "topic-bank", 1, 0)
        info = {"verdict": ("PASS", "brand"), "suggest": "offline",
                "colls": ["shilajit-wellness-stack", "mens-essential-collection"], "links": []}
        text = rt.render(cand, "CA1009-8", ctx, info)
        self.assertIn(gr.TICKET_LINE, text)
        self.assertNotIn(sw.TICKET_LINE, text)
        self.assertEqual(br.violations(text), [])
        price = next(t for t in bank["topics"] if t["id"] == "shilajit-price")
        brief = " ".join([price["primary"], price["title"], price["intent"], price["angle"],
                          price["evidence"]] + price["secondary"] + price["fanout"])
        self.assertIn("gold resin", brief)
        self.assertEqual(gr.violations(brief), [])
        self.assertEqual(sw.violations(brief), [])

    def test_lint_open_ticket_only(self):
        body = (
            "- [ ] **#T — gold resin** — `Pure Shilajit Gold Resin (US 2026)`\n"
            "  - Pure Shilajit Gold Resin provides 500 mg.\n"
            "## [DONE] old\n"
            "  - Pure Shilajit Gold Resin provides 500 mg.\n"
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
            self.assertIn("gold_resin_rules", read(rel), rel)
        self.assertIn("gold_resin.spec_violations", read("scripts/brand_rules.py"))
        self.assertIn("gold-resin-label", read("scripts/topic_fitness.py"))
        self.assertIn("FAIL [gold-resin-label]", read("docs/GOLD_RESIN_LABEL_GUARD.md"))
        for rel in ("scripts/validate_article.py", "scripts/validate_landing.py",
                    "scripts/lint_tickets.py", "scripts/run_ticket_headless.sh",
                    "scripts/run_landing_headless.sh"):
            self.assertIn("gold_resin_rules", read(rel), rel)

    def test_cli(self):
        script = os.path.join(ROOT, "scripts", "gold_resin_rules.py")
        proc = subprocess.run([sys.executable, script, "--brief"], capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, gr.TICKET_LINE))
        proc = subprocess.run(
            [sys.executable, script, "Pure Shilajit Gold Resin provides 500 mg."],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("500 mg", proc.stdout)
        proc = subprocess.run(
            [sys.executable, script, "Pure Shilajit Gold Resin. 75% Fulvic. " + SERVING + "."],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout)


if __name__ == "__main__":
    unittest.main()

"""ShilaSource Himalayan Shilajit Resin copy follows its pack-label whitelist.

product_refs/shilasource-himalayan-shilajit-resin.label.json is the 2026-10-08
label_ocr.swift read. Front lines include 70% Fulvic Acid* and 1.06oz (30g).
The servings badge is split across the lines "75" and "SERVINGS" / "Servings".
No milligram token and no Supplement Facts panel are in that file.
Premium Himalayan Shilajit Gummies, Shilajit Shockwave, and Pure Shilajit Gold
Resin are out of scope.
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
import shilasource_resin_rules as sr
import shockwave_rules as sw
import topic_fitness as tf

LABEL = os.path.join(ROOT, "product_refs", "shilasource-himalayan-shilajit-resin.label.json")
REQUIRED = [
    "ShilaSource",
    "Himalayan",
    "Shilajit",
    "Resin",
    "75",
    "Dietary Supplement",
]
OPTIONAL = [
    "Wellness",
    "Nest",
    "70% Fulvic Acid*",
    "Lab-Tested for Purity*",
    "1.06oz (30g)",
    "SERVINGS",
    "Servings",
]
LISTICLE = os.path.join(ROOT, "landing_drafts", "shilasource-resin-listicle-261008.json")


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


class WhitelistFile(unittest.TestCase):
    def test_pack_file_is_the_2026_10_08_lines(self):
        tokens = sr.load_label()
        with open(LABEL, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["required"], REQUIRED)
        self.assertEqual(data["optional"], OPTIONAL)
        self.assertEqual(tokens, REQUIRED + OPTIONAL)
        self.assertNotIn("accepted_ocr", data)
        self.assertIn("label_ocr.swift", data["source"])
        self.assertIn("2026-10-08", data["source"])
        joined = " ".join(tokens)
        self.assertIn("70% Fulvic Acid*", joined)
        self.assertIn("1.06oz (30g)", joined)
        self.assertIn("75", tokens)
        self.assertIn("SERVINGS", tokens)
        self.assertNotIn("mg", joined.lower())
        self.assertNotRegex(joined, r"\d+\s*mg")
        self.assertNotIn("Supplement Facts", joined)
        self.assertNotIn("trace mineral", joined.lower())
        self.assertEqual(
            sorted(sr.allowed_phrases(tokens)),
            ["1.06 oz", "30 g", "70%", "75 servings"])
        raw = read("product_refs/shilasource-himalayan-shilajit-resin.label.json")
        self.assertEqual(sr.violations(raw), [])
        module = read("scripts/shilasource_resin_rules.py")
        self.assertNotIn("1.06", module)
        self.assertNotIn("70%", module)
        self.assertNotIn("400 mg", module)

    def test_allowlist_follows_the_file(self):
        self.assertEqual(
            sr.violations("ShilaSource provides 500 mg.", tokens=["500 mg"]), [])
        self.assertEqual(
            sr.violations("ShilaSource is 30 servings.", tokens=["30 servings"]), [])
        self.assertEqual(
            sr.violations("ShilaSource is 75% fulvic acid.", tokens=["75% Fulvic"]), [])
        self.assertTrue(sr.violations("ShilaSource provides 500 mg."))
        self.assertTrue(sr.violations("ShilaSource is 30 servings."))
        self.assertTrue(sr.violations("ShilaSource is 75% fulvic acid."))
        self.assertEqual(
            sr.violations("ShilaSource is a jar.", tokens=[]),
            [sr._PREFIX + "pack label whitelist is missing or empty (" + sr.LABEL_REL + ")"])
        self.assertEqual(sr.violations("Shilajit Shockwave provides 500 mg.", tokens=[]), [])
        self.assertEqual(sr.violations("Pure Shilajit Gold Resin, 500 mg per serving."), [])
        self.assertEqual(sr.violations("himalayan shilajit resin, 500 mg per serving."), [])

    def test_split_servings_badge_is_not_a_hard_coded_count(self):
        self.assertEqual(
            sr.allowed_phrases(["ShilaSource", "Resin"]), [])
        self.assertEqual(
            sr.allowed_phrases(["75", "Dietary Supplement"]), [])
        self.assertEqual(
            sr.allowed_phrases(["75", "SERVINGS"]), ["75 servings"])
        self.assertEqual(
            sr.violations("ShilaSource has 75 servings.", tokens=["75", "Dietary Supplement"]),
            [sr._PREFIX + "75 servings is not on the pack label whitelist"])

    def test_ticket_and_landing_lines_match_the_file(self):
        for text in (sr.LABEL_LINE, sr.TICKET_LINE, sr.LANDING_NOTE):
            self.assertIn("70% Fulvic Acid*", text)
            self.assertIn("1.06oz (30g)", text)
            self.assertIn("SERVINGS", text)
            self.assertEqual(sr.violations(text), [], text)
            self.assertEqual(sw.violations(text), [], text)
            self.assertNotIn("mg", re.sub(r"milligram", "", text, flags=re.I).lower())


class LabelCopyPasses(unittest.TestCase):
    def test_whitelist_lines_pass_every_gate(self):
        for text in (
            sr.LABEL_LINE,
            sr.TICKET_LINE,
            sr.LANDING_NOTE,
            "ShilaSource Himalayan Shilajit Resin. 70% Fulvic Acid*. Lab-Tested for Purity*. "
            "1.06oz (30g). 75 SERVINGS. Dietary Supplement.",
            "ShilaSource is 70% fulvic acid.",
            "ShilaSource Himalayan Shilajit Resin is 1.06 oz.",
            "ShilaSource is 1.06oz (30g).",
            "ShilaSource, 30 grams, 75 servings.",
            "ShilaSource resin has 75 servings.",
            "ShilaSource, seventy-five servings.",
            "ShilaSource has 75 serving.",
            "/products/shilasource-himalayan-shilajit-resin is 1.06oz (30g), 75 servings.",
            "ShilaSource does not list a milligram amount.",
            "Do not add a milligram serving for ShilaSource.",
            "ShilaSource is not 500 mg and not 30 servings and not 75% fulvic.",
            "ShilaSource Himalayan Shilajit Resin is $59.99.",
        ):
            self.assertEqual(sr.violations(text), [], text)
            self.assertEqual(br.violations(text), [], text)
            self.assertEqual(br.assess(text).action, "allow", text)
            self.assertEqual(br.prepare_ticket(text), text)

    def test_mark_is_not_required(self):
        text = "ShilaSource Himalayan Shilajit Resin. Wellness Nest. 70% Fulvic Acid*."
        self.assertNotIn("®", text)
        self.assertNotIn("™", text)
        self.assertEqual(br.violations(text), [])

    def test_context_that_must_stay_allowed(self):
        for text in (
            "Unlike other brands' 500 mg, ShilaSource lists no milligram on the pack.",
            "ShilaSource is not 30 servings and not 1 fl oz and not 75% fulvic.",
            "| ShilaSource | jar |\n| Brand X | 500 mg | 30 servings | 30 ml |",
            "Premium Himalayan Shilajit Gummies list 1500 mg, 60 gummies, a 60-day supply, "
            "and 85+ trace minerals.",
            "Pure Shilajit Gold Resin, 1.06 oz (30g) - 75 servings, 75% fulvic.",
            "Shilajit Shockwave, EXPERIENCE FOCUSED ENERGY, PEAK PERFORMANCE.",
            "FusiForce has 90 gummies.",
            "FloraFresh: Vitamin C 30 mg per 2 gummies, 15B CFU.",
            "The trial used 250 mg of purified shilajit. ShilaSource is a jar.",
            "Premium Himalayan Shilajit Gummies are 60 gummies and a 60-day supply. "
            "ShilaSource is a jar.",
            "AgeAura Pure NMN + TMG provides 500 mg NMN. ShilaSource is a jar.",
            "ShilaSource is a jar. A randomized trial of ashwagandha. The dose was 250 mg.",
            "ShilaSource is $75.",
            sr.TICKET_LINE + "\n" + sw.TICKET_LINE,
        ):
            self.assertEqual(sr.violations(text), [], text)
            self.assertEqual(br.violations(text), [], text)

    def test_other_products_in_the_same_piece_keep_their_own_doses(self):
        text = "\n".join([
            "ShilaSource Himalayan Shilajit Resin, 70% Fulvic Acid*, 1.06oz (30g), 75 servings.",
            "Shilajit Shockwave, EXPERIENCE FOCUSED ENERGY, PEAK PERFORMANCE.",
            "FloraFresh: per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 15B CFU, "
            "Vitamin C 30 mg and pineapple fruit powder 100 mg.",
            "FusiForce Creatine Monohydrate Gummies, 90 gummies.",
            "Premium Himalayan Shilajit Gummies, 60 gummies, 60-day supply, 1500 mg, 85+ trace minerals.",
            "Pure Shilajit Gold Resin is 75% fulvic acid, 1.06 oz (30g) - 75 servings.",
        ])
        self.assertEqual(sr.violations(text), [])
        self.assertEqual(br.violations(text), [])

    def test_other_guards_still_fire(self):
        self.assertTrue(br.violations("Shilajit Shockwave provides 500 mg."))
        self.assertEqual(br.violations("Shilajit Shockwave. PEAK PERFORMANCE."), [])
        self.assertTrue(br.violations("FloraFresh delivers 1 billion CFU."))
        self.assertTrue(br.violations("AgeAura Pure Urolithin A"))
        self.assertEqual(br.violations("AgeAura Pure NMN + TMG NAD Complex"), [])
        self.assertEqual(sw.violations("ShilaSource resin, 300 mg per serving."), [])
        self.assertTrue(sr.violations("ShilaSource resin, 300 mg per serving."))
        self.assertTrue(br.violations("ShilaSource resin, 300 mg per serving."))
        self.assertEqual(sr.violations("Shilajit Shockwave provides 500 mg and 30 servings."), [])
        self.assertTrue(br.violations("Shilajit Shockwave provides 500 mg and 30 servings."))


class InventedDosesRejected(unittest.TestCase):
    def assertRejected(self, text, *needles):
        bad = br.violations(text)
        self.assertTrue(bad, text)
        self.assertEqual(br.assess(text).action, "deny", text)
        with self.assertRaises(br.GuardError):
            br.prepare_ticket(text)
        with self.assertRaises(br.GuardError):
            br.assert_publishable("ShilaSource Himalayan Shilajit Resin", text)
        for needle in needles:
            self.assertTrue(any(needle in reason for reason in bad), (needle, bad, text))
        return bad

    def test_milligrams_fail(self):
        self.assertRejected("ShilaSource provides 500 mg per serving.", "500 mg")
        self.assertRejected("ShilaSource delivers 250 milligrams.", "250 mg")
        self.assertRejected("ShilaSource resin, 300 mg per serving.", "300 mg")
        self.assertRejected("ShilaSource provides 400 mg of shilajit.", "400 mg")
        self.assertRejected("/products/shilasource-himalayan-shilajit-resin lists 1,500 mg.", "1500 mg")
        self.assertRejected("ShilaSource contains five hundred milligrams.", "five hundred milligrams")
        self.assertRejected("<p>ShilaSource Himalayan Shilajit Resin</p><p>500 mg of shilajit.</p>", "500 mg")

    def test_wrong_servings_fulvic_and_weight_fail(self):
        self.assertRejected("ShilaSource has 30 servings.", "30 servings")
        self.assertRejected("ShilaSource: servings per jar 30.", "30 servings")
        self.assertRejected("ShilaSource, thirty servings.", "30 servings")
        self.assertRejected("ShilaSource, sixty servings.", "60 servings")
        self.assertRejected("ShilaSource has 7.5 servings.", "7.5 servings")
        self.assertRejected("ShilaSource has 175 servings.", "175 servings")
        self.assertRejected("ShilaSource is 75% fulvic acid.", "75%")
        self.assertRejected("ShilaSource is 7.5% fulvic acid.", "7.5%")
        self.assertRejected("ShilaSource is 80% pure.", "80%")
        self.assertRejected("ShilaSource is 1 fl oz (30 ml).", "1 fl oz", "30 ml")
        self.assertRejected("ShilaSource is 2 oz.", "2 oz")
        self.assertRejected("ShilaSource is 10.6 oz.", "10.6 oz")
        self.assertRejected("ShilaSource is 1.06 fl oz.", "1.06 fl oz")
        self.assertRejected("ShilaSource is 5 g per serving.", "5 g")
        self.assertRejected("ShilaSource is 0.4 g per serving.", "0.4 g")
        self.assertRejected("ShilaSource is a 30-day supply.", "30-day supply")
        self.assertRejected("ShilaSource is a 75-day supply.", "75-day supply")

    def test_other_doses_fail(self):
        self.assertRejected("ShilaSource provides 1 billion CFU.", "1 billion CFU")
        self.assertRejected("ShilaSource, 200 mcg per serving.", "200 mcg")
        self.assertRejected("ShilaSource, 60 gummies.", "60 gummies")
        self.assertRejected("ShilaSource, 1000 IU.", "1000 IU")
        self.assertRejected("ShilaSource, 10 drops per serving.", "10 drops")
        self.assertRejected("ShilaSource lists 85+ trace minerals.", "85 minerals")
        self.assertRejected("ShilaSource provides 40 minerals.", "40 minerals")

    def test_bare_75_does_not_allow_a_milligram_or_a_fulvic_percent(self):
        self.assertRejected("ShilaSource provides 75 mg.", "75 mg")
        self.assertRejected("ShilaSource is 75% fulvic.", "75%")

    def test_unowned_milligram_in_the_same_piece_fails(self):
        self.assertRejected(
            "ShilaSource is a jar. Many labels print 500 mg.",
            "500 mg")

    def test_naming_the_resin_in_a_study_dose_fails(self):
        self.assertRejected(
            "A trial of ShilaSource used 250 mg of purified shilajit.",
            "250 mg")


class Gates(unittest.TestCase):
    def test_topic_fitness_code(self):
        verdict, code, _why = tf.assess("ShilaSource Himalayan Shilajit Resin 500 mg review", articles=[])
        self.assertEqual((verdict, code), ("FAIL", "shilasource-resin-label"))
        verdict, code, _why = tf.assess("ShilaSource Himalayan Shilajit Resin review", articles=[])
        self.assertEqual(verdict, "PASS")
        self.assertNotEqual(code, "shilasource-resin-label")
        self.assertEqual(
            tf.assess("Premium Himalayan Shilajit Gummies 1500 mg review", articles=[])[0], "PASS")
        self.assertEqual(tf.assess("Shilajit Shockwave 500 mg review", articles=[])[1], "shockwave-label")
        self.assertEqual(tf.assess("FloraFresh 1 billion CFU review", articles=[])[1], "florafresh-formula")
        bare = tf.assess("himalayan shilajit resin 500 mg review", articles=[])
        self.assertNotEqual(bare[1], "shilasource-resin-label")

    def test_landing_spec_fields(self):
        clean = {
            "handle": "shilasource-himalayan-shilajit-resin",
            "title": "ShilaSource Himalayan Shilajit Resin",
            "chip": "75 servings",
            "product": {"bullets": ["70% Fulvic Acid*", "1.06oz (30g)", "75 SERVINGS"]},
            "items": [{"body": "Jar format.", "source": "A PDP once claimed 500 mg."}],
        }
        self.assertEqual(sr.spec_violations(clean), [])
        self.assertEqual(br.spec_violations(clean), [])
        bad = {
            "handle": "shilasource-himalayan-shilajit-resin",
            "title": "ShilaSource",
            "product": {"bullets": ["500 mg shilajit"]},
            "sources": ["A trial used 250 mg of shilajit."],
            "items": [{"chart": {"source": "30 servings per jar"}}],
        }
        reasons = br.spec_violations(bad)
        self.assertTrue(any("500 mg" in r and "product" in r for r in reasons), reasons)
        self.assertTrue(any("30 servings" in r and "chart" in r for r in reasons), reasons)
        self.assertFalse(any("sources" in r for r in reasons), reasons)

    def test_live_listicle_spec_repeats_only_whitelist_doses(self):
        with open(LISTICLE, encoding="utf-8") as fh:
            spec = json.load(fh)
        self.assertEqual(sr.spec_violations(spec), [])
        self.assertEqual(br.spec_violations(spec), [])

    def test_image_prompt_refuses_an_invented_dose(self):
        with self.assertRaises(br.GuardError):
            br.prepare_image_request(
                "Draw ShilaSource Himalayan Shilajit Resin with 500 mg on the label.",
                ["shilasource-himalayan-shilajit-resin"])
        prompt, handles = br.prepare_image_request(
            "Draw ShilaSource Himalayan Shilajit Resin, 70% Fulvic Acid*, 1.06oz (30g), 75 servings.",
            ["shilasource-himalayan-shilajit-resin"])
        self.assertIn("shilasource-himalayan-shilajit-resin", handles)
        self.assertIn("70% Fulvic Acid*", prompt)

    def test_refill_line_and_queue(self):
        bank = rt.load_bank(rt.BANK)
        errs = rt.lint_bank(bank)
        self.assertEqual(errs, [], errs[:4])
        ctx = rt.fixture_ctx(bank, rt.parse_queue(rt.FIX_QUEUE))
        cand = rt.norm_cand(dict(
            rt.FIX_GOOD, id="sr", product="shilasource-himalayan-shilajit-resin",
            primary="shilajit resin for athletes",
            title="ShilaSource Resin for Athletes (US 2026)",
            secondary=["shilasource resin for training"], segment="athletes",
            intent="athlete comparing a resin jar", template="EDITORIAL",
            angle="What the jar format changes about a daily routine.",
            fanout=["how do you take shilajit resin"],
            evidence="Pack label lines only.",
            inline=["shilajit-shockwave", "premium-himalayan-shilajit-gummies",
                    "pure-shilajit-gold-resin"],
            link=[]), bank, "topic-bank", 1, 0)
        info = {"verdict": ("PASS", "brand"), "suggest": "offline",
                "colls": ["shilajit-wellness-stack", "mens-essential-collection"], "links": []}
        text = rt.render(cand, "CA1010-1", ctx, info)
        self.assertIn(sr.TICKET_LINE, text)
        self.assertIn(sw.TICKET_LINE, text)
        self.assertEqual(br.violations(text), [])
        price = next(t for t in bank["topics"] if t["id"] == "shilajit-price")
        brief = " ".join([price["primary"], price["title"], price["intent"], price["angle"],
                          price["evidence"]] + price["secondary"] + price["fanout"])
        self.assertIn("Shockwave", brief)
        self.assertEqual(sr.violations(brief), [])
        self.assertEqual(sw.violations(brief), [])

    def test_lint_open_ticket_only(self):
        body = (
            "- [ ] **#T — shilasource resin** — `ShilaSource Resin (US 2026)`\n"
            "  - ShilaSource provides 500 mg.\n"
            "## [DONE] old\n"
            "  - ShilaSource provides 500 mg.\n"
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
            self.assertIn("shilasource_resin_rules", read(rel), rel)
        self.assertIn("shilasource_resin.spec_violations", read("scripts/brand_rules.py"))
        self.assertIn("shilasource-resin-label", read("scripts/topic_fitness.py"))
        self.assertIn("FAIL [shilasource-resin-label]", read("docs/SHILASOURCE_RESIN_LABEL_GUARD.md"))
        for rel in ("scripts/validate_article.py", "scripts/validate_landing.py",
                    "scripts/lint_tickets.py", "scripts/run_ticket_headless.sh",
                    "scripts/run_landing_headless.sh"):
            self.assertIn("shilasource_resin_rules", read(rel), rel)

    def test_cli(self):
        script = os.path.join(ROOT, "scripts", "shilasource_resin_rules.py")
        proc = subprocess.run([sys.executable, script, "--brief"], capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, sr.TICKET_LINE))
        proc = subprocess.run(
            [sys.executable, script, "ShilaSource provides 500 mg."],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("500 mg", proc.stdout)
        proc = subprocess.run(
            [sys.executable, script, "ShilaSource. 70% Fulvic Acid*. 1.06oz (30g). 75 servings."],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout)


if __name__ == "__main__":
    unittest.main()

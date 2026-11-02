"""Premium Himalayan Shilajit Gummies copy follows its pack-label whitelist.

60 gummies and a 60-day supply are in product_refs/premium-himalayan-shilajit-gummies.label.json.
A 30-serving panel is not. Milligram amounts pass only when that exact token is in the file
(1500mg Shilajit is; 150 mg is not). Shockwave, Gold Resin, and ShilaSource resin are out of scope.
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import brand_rules as br
import refill_tickets as rt
import shilajit_gummies_rules as sg
import topic_fitness as tf

LABEL = os.path.join(ROOT, "product_refs", "premium-himalayan-shilajit-gummies.label.json")
LISTICLE = os.path.join(ROOT, "landing_drafts", "shilajit-gummies-listicle-261008.json")


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


class WhitelistFile(unittest.TestCase):
    def test_pack_file_is_the_source_of_truth(self):
        tokens = sg.load_label()
        with open(LABEL, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(tokens, data["required"] + data["optional"])
        self.assertEqual(sg.gummy_counts(tokens), [60])
        self.assertEqual(sg.day_supplies(tokens), [60])
        self.assertIn("60 GUMMIES", tokens)
        self.assertIn("60-DAY SUPPLY", tokens)
        self.assertTrue(sg.listed("1500 mg", tokens))
        self.assertTrue(sg.listed("1,500 mg", tokens))
        for phrase in ("30 servings", "30 serving", "30-serving", "150 mg", "250 mg", "500 mg",
                       "2 gummies", "84", "30 gummies", "30-day supply"):
            self.assertFalse(sg.listed(phrase, tokens), phrase)
        self.assertEqual(sg.gummy_counts(["PREMIUM HIMALAYAN", "1500mg Shilajit"]), [])
        self.assertEqual(sg.day_supplies(["60 GUMMIES"]), [])

    def test_allowlist_follows_the_file(self):
        self.assertEqual(
            sg.violations("Premium Himalayan Shilajit Gummies have 30 servings.",
                          tokens=["30 servings", "60 GUMMIES", "60-DAY SUPPLY"]), [])
        self.assertTrue(sg.violations("Premium Himalayan Shilajit Gummies have 30 servings."))
        self.assertEqual(
            sg.violations("Premium Himalayan Shilajit Gummies provide 150 mg.", tokens=["150 mg", "60 GUMMIES"]), [])
        self.assertEqual(
            sg.violations("Premium Himalayan Shilajit Gummies, 90 gummies.", tokens=["90 GUMMIES"]), [])
        self.assertTrue(sg.violations("Premium Himalayan Shilajit Gummies, 60 gummies.", tokens=["90 GUMMIES"]))
        self.assertEqual(
            sg.violations("Premium Himalayan Shilajit Gummies are a pouch.", tokens=[]),
            [sg._PREFIX + "pack label whitelist is missing or empty (" + sg.LABEL_REL + ")"])


class LabelCopyPasses(unittest.TestCase):
    def test_label_lines_pass_every_gate(self):
        for text in (sg.LABEL_LINE, sg.TICKET_LINE, sg.LANDING_NOTE,
                     "Premium Himalayan Shilajit Gummies, 60 gummies, 60-day supply.",
                     "Premium Himalayan Shilajit Gummies list 1500mg Shilajit, 75% Fulvic Acid, "
                     "85+ Trace Minerals, ashwagandha, gokshura and black musli.",
                     "Premium Himalayan Shilajit Gummies list 1,500 mg Shilajit on the pouch."):
            self.assertEqual(sg.violations(text), [], text)
            self.assertEqual(br.violations(text), [], text)
            self.assertEqual(br.assess(text).action, "allow", text)
            self.assertEqual(br.prepare_ticket(text), text)

    def test_context_that_must_stay_allowed(self):
        for text in (
            "Premium Himalayan Shilajit Gummies are not a 30-serving panel. The pouch says 60 gummies "
            "and a 60-day supply.",
            "Do not claim 30 servings or 150 mg for Premium Himalayan Shilajit Gummies.",
            "Unlike other brands' 30 servings, Premium Himalayan Shilajit Gummies are 60 gummies.",
            "| Premium Himalayan Shilajit Gummies | 60 gummies | 60-day supply |\n"
            "| Brand X | 30 servings | 150 mg |",
            "FloraFresh: Vitamin C 30 mg per 2 gummies.",
            "The Pandit trial used 250 mg of purified shilajit. Premium Himalayan Shilajit Gummies are "
            "60 gummies and a 60-day supply.",
            "Premium Himalayan Shilajit Gummies are easy to take. A 60-day trial of ashwagandha lowered "
            "stress scores.",
            "Some pouches are 30 servings.",
        ):
            self.assertEqual(sg.violations(text), [], text)
            self.assertEqual(br.violations(text), [], text)
        # Other SKUs stay out of this guard. Their own label guards still fail closed.
        for text in (
            "Shilajit Shockwave, 30 servings and 500 mg.",
            "Pure Shilajit Gold Resin, 30 servings.",
            "ShilaSource resin, 150 mg per serving.",
            "FusiForce has 84 gummies and 30 servings.",
        ):
            self.assertEqual(sg.violations(text), [], text)
            reasons = br.violations(text)
            self.assertTrue(reasons, text)
            self.assertFalse(any(r.startswith("Shilajit gummies label:") for r in reasons), reasons)
        age = "AgeAura Pure NMN + TMG provides 500 mg NMN across 30 servings."
        self.assertEqual(sg.violations(age), [])
        self.assertEqual(br.violations(age), [])


class WrongCountsRejected(unittest.TestCase):
    def assertRejected(self, text, *needles):
        bad = br.violations(text)
        self.assertTrue(bad, text)
        self.assertEqual(br.assess(text).action, "deny", text)
        for needle in needles:
            self.assertTrue(any(needle in reason for reason in bad), (needle, bad, text))
        return bad

    def test_wrong_pack_counts_fail(self):
        self.assertRejected("Premium Himalayan Shilajit Gummies come in a pouch of 30 gummies.", "30 gummies")
        self.assertRejected("Premium Himalayan Shilajit Gummies ship 84 gummies.", "84 gummies")
        self.assertRejected("Premium Himalayan Shilajit Gummies, 120 count.", "120")
        self.assertRejected("Premium Himalayan Shilajit Gummies: two gummies a day.", "2 gummies a day")
        self.assertRejected("/products/premium-himalayan-shilajit-gummies has thirty servings.", "30 servings")

    def test_30_serving_panel_fails(self):
        self.assertRejected("Premium Himalayan Shilajit Gummies have 30 servings.", "30 servings")
        self.assertRejected("Premium Himalayan Shilajit Gummies: servings per container 30.", "30 servings")
        self.assertRejected("Premium Himalayan Shilajit Gummies are a 30-day supply.", "30-day supply")
        self.assertRejected("Premium Himalayan Shilajit Gummies, 2 gummies per serving.", "2 gummies per serving")
        self.assertRejected("Premium Himalayan Shilajit Gummies, per 2-gummy serving.", "2 gummies per serving")
        self.assertRejected(
            "Premium Himalayan Shilajit Gummies are easy. The count is 30 servings.", "30 servings")

    def test_invented_milligrams_fail_and_label_milligrams_pass(self):
        self.assertRejected("Premium Himalayan Shilajit Gummies provide 150 mg of extract.", "150 mg")
        self.assertRejected("Premium Himalayan Shilajit Gummies provide 250 mg.", "250 mg")
        self.assertRejected("Premium Himalayan Shilajit Gummies provide 500 mg.", "500 mg")
        bad = sg.violations("Premium Himalayan Shilajit Gummies provide 150 mg of a 1,500 mg equivalent.")
        self.assertTrue(any("150 mg" in r for r in bad), bad)
        self.assertFalse(any("1,500 mg" in r or "1500 mg" in r for r in bad), bad)
        self.assertEqual(br.violations("Premium Himalayan Shilajit Gummies list 1,500 mg Shilajit."), [])
        self.assertEqual(br.violations("Premium Himalayan Shilajit Gummies list 1500mg Shilajit."), [])


class SpecsAndCallers(unittest.TestCase):
    def test_product_blocks_and_chip_are_product_claims(self):
        spec = {"title": "Premium Himalayan Shilajit Gummies", "template": "listicle",
                "hero": {"chip": "60 gummies · 30 servings"},
                "product": {"name": "Gummies", "bullets": ["150 mg extract", "2-gummy serving"]},
                "offer": {"bullets": ["30 servings per pouch"]}}
        bad = br.spec_violations(spec)
        self.assertTrue(any("30 servings" in r and "(hero.chip)" in r for r in bad), bad)
        self.assertTrue(any("150 mg" in r and r.endswith("(product)") for r in bad), bad)
        self.assertTrue(any("2 gummies per serving" in r and r.endswith("(product)") for r in bad), bad)
        self.assertTrue(any("30 servings" in r and r.endswith("(offer)") for r in bad), bad)

    def test_provenance_notes_may_quote_the_disputed_panel(self):
        spec = {"title": "Premium Himalayan Shilajit Gummies",
                "image_note": "PDP panel says 30 servings and 150 mg",
                "offer": {"price_source": "PDP says 30 servings and 150 mg; not on the pack label whitelist"},
                "sources": [{"label": "PDP: 30 servings and 150 mg", "url": sg.PRODUCT_URL}]}
        self.assertEqual(br.spec_violations(spec), [])
        self.assertTrue(sg.violations(json.dumps(spec)))

    def test_chart_source_keeps_trial_doses_and_rejects_a_bare_dose(self):
        trial = {"title": "Premium Himalayan Shilajit Gummies",
                 "items": [{"chart": {"source": "Pandit et al. Randomised, placebo-controlled; 250 mg purified "
                                                "shilajit twice daily. Keller et al. placebo; 500 vs 250 mg/day."}}],
                 "product": {"bullets": ["60 gummies", "60-day supply", "1500mg Shilajit"]}}
        self.assertEqual(br.spec_violations(trial), [])
        bare = {"title": "Premium Himalayan Shilajit Gummies",
                "items": [{"chart": {"source": "250 mg per serving"}}]}
        bad = br.spec_violations(bare)
        self.assertTrue(any("250 mg" in r for r in bad), bad)

    def test_existing_listicle_fails_closed(self):
        raw = read("landing_drafts/shilajit-gummies-listicle-261008.json")
        spec = json.loads(raw)
        bad = sg.spec_violations(spec)
        self.assertTrue(any("30 servings" in r for r in bad), bad)
        self.assertTrue(any("150 mg" in r for r in bad), bad)
        self.assertTrue(sg.violations(raw))

    def test_ageaura_stays_nmn_tmg_only(self):
        uro = br.assess("AgeAura Pure Urolithin A")
        self.assertEqual(uro.action, "deny")
        self.assertTrue(any("Urolithin" in r for r in uro.reasons))
        self.assertFalse(any(r.startswith("Shilajit gummies") for r in uro.reasons))
        both = br.assess("AgeAura review. Premium Himalayan Shilajit Gummies have 30 servings.")
        self.assertEqual(both.action, "deny")
        self.assertTrue(any("AgeAura" in r for r in both.reasons))
        self.assertTrue(any("30 servings" in r for r in both.reasons))
        self.assertIn(br.AGEAURA_OK, br.prepare_ticket("AgeAura review for adults over 40"))
        self.assertEqual(br.spec_violations({"title": "AgeAura Pure NMN + TMG NAD Complex"}), [])
        self.assertTrue(any("Urolithin" in r for r in br.spec_violations({"title": "AgeAura Pure Urolithin A"})))
        # Sugar-free stays a FloraFresh denial before and after the 15B CFU rules.
        # "15 billion CFU" is that label count once florafresh_rules.CFU is 15B CFU.
        flora = br.assess("FloraFresh is sugar-free.")
        self.assertEqual(flora.action, "deny")
        self.assertTrue(any(r.startswith("FloraFresh") for r in flora.reasons))
        self.assertFalse(any(r.startswith("Shilajit gummies") for r in flora.reasons))

    def test_topic_fitness_code(self):
        verdict, code, why = tf.assess("Premium Himalayan Shilajit Gummies 30 servings review")
        self.assertEqual((verdict, code), ("FAIL", "shilajit-gummies-label"))
        self.assertIn("60 gummies", why)
        self.assertEqual(tf.assess("Premium Himalayan Shilajit Gummies 150 mg review")[1], "shilajit-gummies-label")
        self.assertNotEqual(tf.assess("Premium Himalayan Shilajit Gummies 60 gummies review")[1],
                            "shilajit-gummies-label")
        self.assertEqual(tf.assess("urolithin a benefits review")[1], "ageaura-sku")
        self.assertEqual(tf.assess("FloraFresh sugar free gummies review")[1], "florafresh-formula")
        self.assertNotEqual(tf.assess("shilajit benefits for men")[1], "shilajit-gummies-label")

    def test_builders_refuse_the_wrong_count(self):
        with self.assertRaises(br.GuardError):
            br.prepare_ticket("- [ ] listicle | wellnessnest | product=" + sg.HANDLE + " · angle: 30 servings")
        with self.assertRaises(br.GuardError):
            br.prepare_image_request("Premium Himalayan Shilajit Gummies pouch labeled 30 servings", [sg.HANDLE])
        prompt, specs = br.prepare_image_request(
            "Premium Himalayan Shilajit Gummies pouch, 60 gummies, 60-day supply, no people's faces", [sg.HANDLE])
        self.assertEqual(specs, [sg.HANDLE])
        self.assertIn("60 gummies", prompt)

    def test_publisher_gate(self):
        with self.assertRaises(br.GuardError):
            br.assert_publishable("Shilajit gummies review",
                                  "Premium Himalayan Shilajit Gummies have 30 servings and 150 mg.")
        br.assert_publishable("Shilajit gummies review", sg.LABEL_LINE + ". " + sg.PRODUCT_URL)

    def test_llms_draft_still_states_only_the_label_line(self):
        text, _rejected = br.llms_txt_draft(br.handles_from_product_refs(os.path.join(ROOT, "product_refs")))
        self.assertEqual(br.violations(text), [])
        self.assertIn("60 gummies", text)
        self.assertIn("60-day supply", text)
        self.assertNotIn("30 servings", text.lower())

    def test_refill_attaches_the_label_line(self):
        bank = json.loads(read("templates/article-topic-bank.json"))
        c = {"product": sg.HANDLE, "primary": "shilajit gummies for men", "title": "Shilajit Gummies for Men",
             "secondary": [], "intent": "buy", "template": "LISTICLE", "angle": "Read the pouch.",
             "fanout": [], "evidence": "Pack label.", "inline": [], "family": "shilajit", "segment": "for-men"}
        ctx = {"bank": bank, "products": {sg.HANDLE: {"price": "59.99"}},
               "collections": {"best-seller": [sg.HANDLE], "shilajit-wellness-stack": [sg.HANDLE]},
               "day": "2026-10-10", "local": False, "live_handles": [], "queue": []}
        info = {"colls": ["best-seller", "shilajit-wellness-stack"], "verdict": ("PASS", "brand"),
                "suggest": "skip", "links": []}
        text = rt.render(c, "CA1010-1", ctx, info)
        self.assertIn(sg.TICKET_LINE, text)
        self.assertEqual(br.violations(text), [])

    def test_landing_note_passes(self):
        line = ("- [ ] listicle | wellnessnest | product=" + sg.HANDLE + " · angle: N things to know "
                "· audience: adults · " + sg.LANDING_NOTE + " (added 2026-10-10)")
        self.assertEqual(br.prepare_ticket(line), line)
        self.assertEqual(br.violations(line), [])

    def test_real_queues_lint_clean(self):
        for rel in ("daily-tickets.md", "daily-landing-tickets.md"):
            r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "lint_tickets.py"),
                                os.path.join(ROOT, rel)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_refill_self_test(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = rt.self_test()
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("Shilajit gummies ticket carries the pack-label line", out.getvalue())

    def test_call_sites_use_the_guard(self):
        for rel in ("scripts/brand_rules.py", "scripts/topic_fitness.py", "scripts/refill_tickets.py",
                    "scripts/build_landing_tickets.py", "scripts/shopify_publisher.py",
                    "scripts/lint_tickets.py", "docs/SHILAJIT_GUMMIES_LABEL_GUARD.md"):
            self.assertIn("shilajit_gummies_rules", read(rel), rel)
        self.assertIn("60 gummies", read("docs/SHILAJIT_GUMMIES_LABEL_GUARD.md"))
        self.assertIn("shilajit_gummies_rules", read("scripts/validate_article.py"))
        self.assertIn("60 gummies", read("scripts/run_ticket_headless.sh"))
        self.assertIn("shilajit_gummies_rules.py", read("scripts/run_landing_headless.sh"))

    def test_cli(self):
        script = os.path.join(ROOT, "scripts", "shilajit_gummies_rules.py")
        r = subprocess.run([sys.executable, script, "--brief"], capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, sg.TICKET_LINE))
        r = subprocess.run([sys.executable, script, "Premium Himalayan Shilajit Gummies have 30 servings."],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("30 servings", r.stdout)
        r = subprocess.run([sys.executable, script, "--spec", LISTICLE], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("30 servings", r.stdout)


if __name__ == "__main__":
    unittest.main()

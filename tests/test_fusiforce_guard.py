"""FusiForce copy follows product_refs/fusiforce-creatine-gummies.label.json.

Pack count is 90 gummies. Kevin 2026-10-23 allows 30 servings and 3 gummies per
serving. Creatine monohydrate is on that file. 84, 25 mg, 50 mg, 5,000 mg, any
other serving count, any milligram amount, and ginseng are not, so those claims
fail closed.
"""
import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import brand_rules as br
import fusiforce_rules as fu
import refill_tickets as rt
import topic_fitness as tf

LABEL = os.path.join(ROOT, "product_refs", "fusiforce-creatine-gummies.label.json")
LISTICLE = os.path.join(ROOT, "landing_drafts", "fusiforce-creatine-listicle-261008.json")
WHITELIST_OK = ["FusiForce", "Creatine", "Monohydrate", "Gummies", "90", "Dietary Supplement"]


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


class WhitelistFile(unittest.TestCase):
    def test_pack_file_is_the_source_of_truth(self):
        tokens = fu.load_label()
        with open(LABEL, encoding="utf-8") as fh:
            data = json.load(fh)
        vault = data["vault_servings"]["lines"]
        self.assertEqual(vault, ["30 servings", "3 gummies per serving"])
        self.assertEqual(tokens, data["required"] + data["optional"] + vault)
        self.assertEqual(fu.pack_count(tokens), 90)
        self.assertTrue(fu.listed("Creatine", tokens))
        self.assertTrue(fu.listed("Monohydrate", tokens))
        self.assertTrue(fu.listed("90", tokens))
        self.assertTrue(fu.listed("30 servings", tokens))
        self.assertTrue(fu.listed("3 gummies per serving", tokens))
        for phrase in ("84", "25 mg", "50 mg", "28 servings", "ginseng", "panax",
                       "ginsenoside", "5000 mg", "5,000 mg", "4 gummies per serving"):
            self.assertFalse(fu.listed(phrase, tokens), phrase)
        self.assertIsNone(fu.pack_count(["Creatine", "Gummies"]))
        self.assertIsNone(fu.pack_count(["90", "84", "Creatine"]))

    def test_allowlist_follows_the_file(self):
        self.assertEqual(fu.violations("FusiForce provides 25 mg.", tokens=["25 mg", "90", "Creatine"]), [])
        self.assertTrue(fu.violations("FusiForce provides 25 mg.", tokens=WHITELIST_OK))
        self.assertEqual(
            fu.violations("FusiForce has 30 servings.", tokens=["30 servings", "90", "Creatine"]), [])
        self.assertEqual(fu.violations("FusiForce contains ginseng.", tokens=["Panax ginseng", "90"]), [])
        self.assertFalse(fu.violations("FusiForce contains ginseng.", tokens=["ginseng", "90"]))
        self.assertTrue(fu.violations("FusiForce contains ginseng.", tokens=WHITELIST_OK))
        self.assertEqual(fu.violations("FusiForce is a pouch.", tokens=[]),
                         [fu._PREFIX + "pack label whitelist is missing or empty (" + fu.LABEL_REL + ")"])


class LabelCopyPasses(unittest.TestCase):
    def test_label_lines_pass_every_gate(self):
        for text in (fu.LABEL_LINE, fu.TICKET_LINE, fu.LANDING_NOTE,
                     "FusiForce Creatine Monohydrate Gummies, 90 gummies, Green Apple flavor.",
                     "FusiForce: 90 gummies / 30 servings (3 gummies per serving).",
                     "FusiForce: Promotes Lean Muscle Growth. Enhances Recovery. 90 gummies. Dietary Supplement."):
            self.assertEqual(fu.violations(text), [], text)
            self.assertEqual(br.violations(text), [], text)
            self.assertEqual(br.assess(text).action, "allow", text)
            self.assertEqual(br.prepare_ticket(text), text)

    def test_open_ticket_wording_passes(self):
        for text in (
            "Apply them to FusiForce honestly — disclose any mismatch between the front label and the panel "
            "(e.g. gummy count) instead of hiding it.",
            "price per 5 g dose. Apply them to FusiForce honestly.",
            "how many gummies equal 5 g of creatine. FusiForce Creatine Monohydrate Gummies.",
            "Creatine Gummies for Beginners: Your First 30 Days. Hero: FusiForce.",
            "FusiForce serving facts from the live PDP.",
            "FusiForce is not 84 gummies. The pouch says 90 gummies.",
            "Do not claim 25 mg or 50 mg or 28 servings for FusiForce.",
            "Unlike other brands' 84-count tubs, FusiForce is 90 gummies.",
            "| FusiForce | 90 gummies |\n| Brand X | 84 gummies | 30 servings |",
            "Shilajit gummies: 30 servings and ginseng.",
            "Some tubs are 84 gummies.",
        ):
            self.assertEqual(br.violations(text), [], text)
        age = "AgeAura Pure NMN + TMG provides 50 mg apigenin across 30 servings."
        self.assertEqual(fu.violations(age), [])
        self.assertEqual(br.violations(age), [])


class WrongCountsRejected(unittest.TestCase):
    def assertRejected(self, text, *needles):
        bad = br.violations(text)
        self.assertTrue(bad, text)
        self.assertEqual(br.assess(text).action, "deny", text)
        for needle in needles:
            self.assertTrue(any(needle in reason for reason in bad), (needle, bad, text))
        return bad

    def test_84_and_other_pack_counts_fail(self):
        self.assertRejected("FusiForce Creatine Gummies come in a pouch of 84 gummies.", "84 gummies")
        self.assertRejected("FusiForce is an 84-count pouch.", "84")
        self.assertRejected("FusiForce panel math is 28×3=84.", "28 x 3 = 84")
        self.assertRejected("FusiForce panel math is 28 x 3 = 84.", "28 x 3 = 84")
        self.assertRejected("The FusiForce pouch holds eighty-four gummies.", "eighty-four")
        self.assertRejected("FusiForce ships 60 gummies per pouch.", "60 gummies")
        self.assertRejected("FusiForce, 120 count.", "120")

    def test_vault_servings_pass(self):
        for text in (
            "FusiForce has 90 gummies.",
            "FusiForce has 30 servings.",
            "FusiForce is a 30-serving pouch.",
            "FusiForce: 3 gummies per serving.",
            "FusiForce is a 3-gummy serving.",
            "FusiForce: 90 gummies / 30 servings (3 gummies per serving).",
        ):
            self.assertEqual(fu.violations(text), [], text)
            self.assertEqual(br.violations(text), [], text)
            self.assertEqual(br.assess(text).action, "allow", text)

    def test_invented_serving_counts_fail(self):
        self.assertRejected("FusiForce has 28 servings per pouch.", "28 servings")
        self.assertRejected("FusiForce pouch: 45 servings.", "45 servings")
        dose = "FusiForce delivers 5,000 mg per serving (3 gummies)."
        bad = self.assertRejected(dose, "5,000 mg")
        self.assertFalse(any("3 gummies per serving" in r for r in bad), bad)
        self.assertRejected("FusiForce, 4 gummies per serving.", "4 gummies per serving")
        self.assertRejected("Take FusiForce per 2-gummy serving.", "2 gummies per serving")

    def test_milligrams_and_ginseng_fail_unless_whitelisted(self):
        self.assertRejected("FusiForce provides 25 mg of ginseng.", "25 mg", "ginseng")
        self.assertRejected("FusiForce panel lists 50 mg.", "50 mg")
        self.assertRejected("FusiForce creatine gummies, 5,000 mg.", "5,000 mg")
        self.assertRejected("FusiForce creatine gummies, 5000 mg.", "5000 mg")
        self.assertRejected("FusiForce adds Panax ginseng (10% ginsenosides).", "Panax", "ginsenosides")
        self.assertRejected("FusiForce contains ginseng.", "ginseng")

    def test_150_mg_is_not_read_as_50_mg(self):
        bad = fu.violations("FusiForce provides 150 mg.")
        self.assertTrue(any("150 mg" in r for r in bad), bad)
        self.assertFalse(any(r.startswith(fu._PREFIX + "50 mg") or " 50 mg" in r for r in bad), bad)
        self.assertTrue(fu.violations("FusiForce provides 50 mg."))


class SpecsAndCallers(unittest.TestCase):
    def test_product_blocks_are_fusiforce_claims(self):
        spec = {"title": "FusiForce: what the pouch says", "template": "listicle",
                "product": {"name": "Creatine Gummies", "bullets": ["84 gummies", "30 servings"]},
                "offer": {"bullets": ["25 mg Panax ginseng"]}}
        bad = br.spec_violations(spec)
        self.assertTrue(any("84 gummies" in r and r.endswith("(product)") for r in bad), bad)
        self.assertFalse(any("30 servings" in r for r in bad), bad)
        self.assertTrue(any("25 mg" in r and r.endswith("(offer)") for r in bad), bad)

    def test_provenance_notes_may_quote_the_disputed_panel(self):
        spec = {"title": "FusiForce",
                "image_note": "PDP panel says 84 gummies and 25 mg",
                "offer": {"price_source": "PDP says 50 mg ginseng and 30 servings; not on the pack label whitelist"},
                "sources": [{"label": "PDP: 5,000 mg and 84 gummies", "url": fu.PRODUCT_URL}]}
        self.assertEqual(br.spec_violations(spec), [])
        self.assertTrue(fu.violations(json.dumps(spec)))

    def test_chart_source_is_checked(self):
        spec = {"title": "FusiForce", "items": [{"chart": {"source": "FusiForce: 84 gummies"}}]}
        self.assertTrue(br.spec_violations(spec))

    def test_label_spec_passes(self):
        spec = {"title": "FusiForce Creatine Monohydrate Gummies",
                "product": {"bullets": ["Creatine monohydrate", "90 gummies", "Green Apple flavor"]}}
        self.assertEqual(br.spec_violations(spec), [])

    def test_existing_listicle_fails_closed(self):
        raw = read("landing_drafts/fusiforce-creatine-listicle-261008.json")
        bad = fu.violations(raw)
        self.assertTrue(any("ginseng" in r.lower() or "Panax" in r for r in bad), bad)
        self.assertTrue(any("5,000 mg" in r or "5000 mg" in r for r in bad), bad)
        self.assertFalse(any("3 gummies per serving" in r for r in bad), bad)
        self.assertTrue(fu.spec_violations(json.loads(raw)))

    def test_ageaura_stays_nmn_tmg_only(self):
        uro = br.assess("AgeAura Pure Urolithin A")
        self.assertEqual(uro.action, "deny")
        self.assertTrue(any("Urolithin" in r for r in uro.reasons))
        self.assertFalse(any(r.startswith("FusiForce") for r in uro.reasons))
        both = br.assess("AgeAura review. FusiForce has 84 gummies.")
        self.assertEqual(both.action, "deny")
        self.assertTrue(any("AgeAura" in r for r in both.reasons))
        self.assertTrue(any("84 gummies" in r for r in both.reasons))
        self.assertIn(br.AGEAURA_OK, br.prepare_ticket("AgeAura review for adults over 40"))
        self.assertEqual(br.spec_violations({"title": "AgeAura Pure NMN + TMG NAD Complex"}), [])
        self.assertTrue(any("Urolithin" in r for r in br.spec_violations({"title": "AgeAura Pure Urolithin A"})))

    def test_topic_fitness_code(self):
        verdict, code, why = tf.assess("FusiForce 84 gummies review")
        self.assertEqual((verdict, code), ("FAIL", "fusiforce-label"))
        self.assertIn("90 gummies", why)
        verdict, code, _why = tf.assess("FusiForce 30 servings review")
        self.assertEqual((verdict, code), ("PASS", "brand_intent"))
        self.assertEqual(tf.assess("FusiForce 28 servings review")[1], "fusiforce-label")
        self.assertEqual(tf.assess("FusiForce 25 mg ginseng review")[1], "fusiforce-label")
        self.assertNotEqual(tf.assess("FusiForce creatine monohydrate gummies review")[1], "fusiforce-label")
        self.assertEqual(tf.assess("urolithin a benefits review")[1], "ageaura-sku")
        # Sugar-free stays a FloraFresh failure before and after the 15B CFU rules.
        # "15 billion CFU" is that label count once florafresh_rules.CFU is 15B CFU.
        self.assertEqual(tf.assess("FloraFresh sugar free gummies review")[1], "florafresh-formula")

    def test_builders_refuse_the_wrong_count(self):
        with self.assertRaises(br.GuardError):
            br.prepare_ticket("- [ ] listicle | wellnessnest | product=" + fu.HANDLE + " · angle: 84 gummies")
        with self.assertRaises(br.GuardError):
            br.prepare_image_request("FusiForce pouch labeled 28 servings", [fu.HANDLE])
        prompt, specs = br.prepare_image_request(
            "FusiForce creatine monohydrate pouch, 90 gummies, 30 servings, 3 gummies per serving, no people's faces",
            [fu.HANDLE])
        self.assertEqual(specs, [fu.HANDLE])
        self.assertIn("90 gummies", prompt)
        self.assertIn("30 servings", prompt)

    def test_publisher_gate(self):
        with self.assertRaises(br.GuardError):
            br.assert_publishable("FusiForce review", "FusiForce has 84 gummies and 25 mg of ginseng.")
        br.assert_publishable("FusiForce review", "FusiForce: " + fu.LABEL_LINE + ". " + fu.PRODUCT_URL)

    def test_refill_attaches_the_label_line(self):
        bank = json.loads(read("templates/article-topic-bank.json"))
        c = {"product": fu.HANDLE, "primary": "where to buy creatine gummies", "title": "Where to Buy",
             "secondary": [], "intent": "buy", "template": "LISTICLE", "angle": "Check the pouch.",
             "fanout": [], "evidence": "Pack label.", "inline": [], "family": "creatine", "segment": "buy"}
        ctx = {"bank": bank, "products": {fu.HANDLE: {"price": "69.99"}},
               "collections": {"best-seller": [fu.HANDLE], "mens-essential-collection": [fu.HANDLE]},
               "day": "2026-10-09", "local": False, "live_handles": [], "queue": []}
        info = {"colls": ["best-seller", "mens-essential-collection"], "verdict": ("PASS", "brand"),
                "suggest": "skip", "links": []}
        text = rt.render(c, "CA1009-3", ctx, info)
        self.assertIn(fu.TICKET_LINE, text)
        self.assertEqual(br.violations(text), [])

    def test_landing_note_passes(self):
        line = ("- [ ] listicle | wellnessnest | product=" + fu.HANDLE + " · angle: Creatine without the scoop "
                "· audience: adults who lift · " + fu.LANDING_NOTE + " (added 2026-10-09)")
        self.assertEqual(br.prepare_ticket(line), line)
        self.assertEqual(br.violations(line), [])

    def test_real_queues_lint_clean(self):
        for rel in ("daily-tickets.md", "daily-landing-tickets.md"):
            r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "lint_tickets.py"),
                                os.path.join(ROOT, rel)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout)

    def test_call_sites_use_the_guard(self):
        for rel in ("scripts/brand_rules.py", "scripts/topic_fitness.py", "scripts/refill_tickets.py",
                    "scripts/build_landing_tickets.py", "scripts/shopify_publisher.py", "docs/FUSIFORCE_LABEL_GUARD.md"):
            self.assertIn("fusiforce_rules", read(rel), rel)
        self.assertIn("90 gummies", read("docs/FUSIFORCE_LABEL_GUARD.md"))

    def test_cli(self):
        script = os.path.join(ROOT, "scripts", "fusiforce_rules.py")
        r = subprocess.run([sys.executable, script, "--brief"], capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, fu.TICKET_LINE))
        r = subprocess.run([sys.executable, script, "FusiForce has 84 gummies."], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("84 gummies", r.stdout)
        r = subprocess.run([sys.executable, script, "--spec", LISTICLE], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)


if __name__ == "__main__":
    unittest.main()

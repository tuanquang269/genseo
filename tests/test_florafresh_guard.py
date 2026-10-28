"""FloraFresh copy follows its Supplement Facts label (Bacillus coagulans SNZ-1969, 15B CFU
per 2 gummies, not sugar-free). 1 billion CFU and 1B CFU are the retired count."""
import contextlib
import csv
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import brand_rules as br
import build_landing_tickets as blt
import florafresh_rules as ff
import refill_tickets as rt
import topic_fitness as tf

LISTICLE = os.path.join(ROOT, "landing_drafts", "florafresh-listicle-261009.json")
OPEN_HEAD = re.compile(r"(- \[ \]|## \[ \])")
FF_RX = re.compile(r"flora[\s_-]?fresh", re.I)

# Verbatim from the live PDP description (read 2026-10-09). Wrong: the label says otherwise.
PDP_FORMULA = (
    "FloraFresh Vaginal Probiotics Gummies are formulated to support vaginal health, microbiome balance, and "
    "daily feminine wellness through a comprehensive blend of probiotics, prebiotics, and supportive nutrients. "
    "Each serving delivers 15 billion CFU from four clinically studied Lactobacillus strains - Lactobacillus "
    "rhamnosus, Lactobacillus reuteri, Lactobacillus salivarius, and Lactobacillus gasseri"
)
PDP_SUGAR_FREE = (
    "Unlike traditional probiotic capsules, FloraFresh comes in a convenient gummy format that makes daily "
    "supplementation simple and enjoyable. The vegan, gluten-free, and sugar-free formula is designed for women "
    "seeking a practical way to support vaginal flora balance without adding complexity to their wellness routine."
)
# Verbatim from a live article (probiotics-for-bv-do-they-actually-work-us-2026) that repeats the PDP.
LIVE_ARTICLE = (
    "What Is Actually in FloraFresh — and What We Cannot Tell You. FloraFresh Vaginal Probiotics Gummies sells for "
    "$40.99. The label states 15 billion CFU per serving from four Lactobacillus species — rhamnosus, reuteri, "
    "salivarius and gasseri — alongside XOS prebiotics, D-mannose and vitamin C."
)
# The #CA1009-2 / #CA1009-8 brief text before the 2026-10-09 fix.
OLD_ANGLE = ("Compare common label ranges in a table and place FloraFresh honestly, using only the CFU and strains "
             "its PDP states. No cure or treatment claims.")
OLD_EVIDENCE = "FloraFresh CFU and strains from the live PDP."
OLD_EVIDENCE_8 = "FloraFresh strains, CFU and storage from the live PDP; any retailer price only from a page fetched at write time."


def lint(text):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "tickets.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "lint_tickets.py"), path],
                           capture_output=True, text=True)
    return r.returncode, r.stdout


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


class LabelFormulaPasses(unittest.TestCase):
    def test_allowlist_constants(self):
        self.assertEqual(ff.HANDLE, "florafresh-vaginal-probiotics-gummies")
        self.assertEqual(ff.PRODUCT_URL, "https://wellnessnest.co/products/" + ff.HANDLE)
        self.assertEqual(ff.STRAIN, "Bacillus coagulans SNZ-1969")
        self.assertEqual(ff.CFU, "15B CFU")
        self.assertLess(abs(float("7.5") * 1e9 - 7.5e9), 1)
        for fact in (ff.STRAIN, ff.CFU, "2 gummies", "Vitamin C 30 mg", "100 mg (with bromelain)", "maltitol",
                     "isomalt", "not sugar-free", "Allergen Free", "Vegan", "Halal", "Gluten Free"):
            self.assertIn(fact, ff.FORMULA_LINE)
        self.assertIn(ff.FORMULA_LINE, ff.TICKET_LINE)
        self.assertIn("Supplement Facts label", ff.TICKET_LINE)

    def test_label_lines_pass_every_gate(self):
        for text in (ff.FORMULA_LINE, ff.TICKET_LINE, ff.LANDING_NOTE):
            text = "FloraFresh " + text
            self.assertEqual(ff.violations(text), [], text)
            self.assertEqual(br.violations(text), [], text)
            self.assertEqual(br.assess(text).action, "allow", text)
            self.assertEqual(br.prepare_ticket(text), text)

    def test_label_copy_passes(self):
        for text in (
            "FloraFresh: per 2 gummies, Bacillus coagulans SNZ-1969, 15B CFU, Vitamin C 30 mg, "
            "pineapple fruit powder 100 mg.",
            "FloraFresh delivers 15 billion CFU per 2-gummy serving from one spore-based strain.",
            "FloraFresh: 7.5 billion CFU per gummy.",
            "FloraFresh is not sugar-free: it is sweetened with maltitol and isomalt.",
            "FloraFresh does not contain XOS, D-mannose or any Lactobacillus strain.",
            "Is FloraFresh sugar-free? No, it is sweetened with maltitol and isomalt.",
            "FloraFresh is Vegan, Halal, Gluten Free and Allergen Free, per its Supplement Facts label.",
            "The live PDP description is wrong; cite the label for FloraFresh strains and CFU.",
            "  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh, 15B CFU per "
            "2 gummies)",
        ):
            self.assertEqual(br.violations(text), [], text)

    def test_historical_listicle_now_fails_the_retired_count(self):
        # 2026-10-09 draft still says 1 billion CFU. Report it; do not rewrite it.
        raw = read("landing_drafts/florafresh-listicle-261009.json")
        spec = json.loads(raw)
        self.assertTrue(ff.violations(raw))
        self.assertTrue(any("1 billion CFU" in r and "1B CFU" in r for r in ff.spec_violations(spec)))
        self.assertTrue(br.spec_violations(spec))
        self.assertTrue(br.violations(json.dumps(spec)))


class WrongFormulaRejected(unittest.TestCase):
    def assertRejected(self, text, *needles):
        bad = br.violations(text)
        self.assertTrue(bad, text)
        self.assertEqual(br.assess(text).action, "deny", text)
        for needle in needles:
            self.assertTrue(any(needle in reason for reason in bad), (needle, bad))
        return bad

    def test_live_pdp_description_rejected(self):
        self.assertRejected(PDP_FORMULA, "four Lactobacillus strains")
        self.assertRejected(PDP_SUGAR_FREE, "not sugar-free")
        self.assertRejected(LIVE_ARTICLE, "rhamnosus, reuteri, salivarius and gasseri")
        self.assertEqual(br.violations("FloraFresh delivers 15 billion CFU of Bacillus coagulans SNZ-1969."), [])

    def test_retired_1_billion_cfu_rejected(self):
        for text in (
            "FloraFresh delivers 1 billion CFU.",
            "FloraFresh delivers 1B CFU.",
            "FloraFresh provides one billion CFU.",
            "FloraFresh lists 1,000,000,000 CFU.",
            "Is FloraFresh 1 billion CFU?",
            "vaginal probiotic dosage florafresh 1 billion cfu probiotic",
            "vaginal probiotic dosage florafresh 1B CFU probiotic",
            "<table><tr><td>FloraFresh</td><td>1 billion CFU</td></tr></table>",
        ):
            self.assertRejected(text, "1 billion CFU", "1B CFU")
        self.assertEqual(br.violations("FloraFresh delivers 15 billion CFU."), [])
        self.assertEqual(br.violations("FloraFresh: 15B CFU per serving."), [])
        self.assertRejected("FloraFresh is a 4-strain, 15B CFU gummy.", "4 strains")

    def test_lactobacillus_formula_rejected(self):
        self.assertRejected("FloraFresh contains Lactobacillus rhamnosus.", "Lactobacillus")
        self.assertRejected("FloraFresh uses L. reuteri and L. gasseri.", "reuteri", "gasseri")
        self.assertRejected("FloraFresh gummies give 15B CFU from four Lactobacillus strains.",
                            "four Lactobacillus strains")
        self.assertRejected("FloraFresh's 4-strain formula", "4 strains")
        self.assertRejected("FloraFresh Vaginal Probiotics Gummies. It also contains Lactobacillus salivarius.",
                            "salivarius")

    def test_sugar_free_xos_mannose_rejected(self):
        self.assertRejected("FloraFresh is sugar-free.", "not sugar-free")
        self.assertRejected("FloraFresh sugar free gummies review", "not sugar-free")
        self.assertRejected("FloraFresh with XOS prebiotic fiber.", "XOS")
        self.assertRejected("FloraFresh adds D-Mannose for urinary support.", "D-mannose")
        self.assertRejected("FloraFresh has no artificial colors and contains D-mannose.", "D-mannose")

    def test_wrong_cfu_amounts_rejected(self):
        self.assertRejected("FloraFresh delivers 10 billion CFU.", "10 billion CFU")
        self.assertRejected("FloraFresh: 1 billion CFU per gummy.", "1 billion CFU", "1B CFU")
        self.assertRejected("FloraFresh: 15 billion CFU per gummy.", "per gummy")
        self.assertRejected("FloraFresh: 7.5 billion CFU per serving.", "per serving")
        self.assertEqual(br.violations("FloraFresh: 7.5 billion CFU per gummy."), [])

    def test_pdp_as_formula_source_rejected(self):
        for text in (OLD_ANGLE, OLD_EVIDENCE, OLD_EVIDENCE_8,
                     "Use the CFU shown at https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies"):
            self.assertRejected(text, "cited from the PDP")


class ContextAllowed(unittest.TestCase):
    def test_research_negation_and_comparison_pass(self):
        for text in (
            "In trials, L. rhamnosus GR-1 plus L. reuteri RC-14 moved flora. FloraFresh uses Bacillus coagulans "
            "SNZ-1969, not those strains.",
            "Studies tested L. rhamnosus, L. reuteri, L. salivarius and L. gasseri in different women. "
            "FloraFresh uses Bacillus coagulans.",
            "Unlike Lactobacillus blends, FloraFresh uses one spore-based strain, Bacillus coagulans SNZ-1969.",
            "Compare FloraFresh's 15B CFU with the 10 billion CFU the trials used.",
            "FloraFresh's retired 1 billion CFU count is not the label.",
            "A trial used 1 billion CFU of L. rhamnosus. FloraFresh uses Bacillus coagulans SNZ-1969.",
            "Other brands list 1 billion CFU. FloraFresh lists 15B CFU.",
            "Take FloraFresh daily. Trials of oral Lactobacillus used 1 to 10 billion CFU a day.",
            "FloraFresh supports a Lactobacillus-dominant flora goal.",
            "Lactobacillus sporogenes is an old name for Bacillus coagulans, the FloraFresh strain.",
            "D-mannose is a sugar studied for urinary health. FloraFresh is a probiotic gummy.",
            "FloraFresh directions from the live PDP only.",
        ):
            self.assertEqual(br.violations(text), [], text)
        for text in (
            "Compare FloraFresh's 1 billion CFU with the 10 billion CFU the trials used.",
            "Compare FloraFresh's 1B CFU with the 10 billion CFU the trials used.",
        ):
            bad = br.violations(text)
            self.assertTrue(any("1 billion CFU" in r and "1B CFU" in r for r in bad), (text, bad))

    def test_tables_compare_brands_row_by_row(self):
        md = "| FloraFresh | 15B CFU | Bacillus coagulans SNZ-1969 |\n| Brand X | 10 billion CFU | 4 strains |"
        self.assertEqual(br.violations(md), [])
        html = ("<table><tr><td>FloraFresh</td><td>15 billion CFU</td></tr>"
                "<tr><td>Brand X</td><td>10 billion CFU, 4 strains</td></tr></table>")
        self.assertEqual(br.violations(html), [])
        self.assertTrue(br.violations("| FloraFresh | 1 billion CFU |"))
        self.assertTrue(br.violations("| FloraFresh | 1B CFU |"))
        self.assertTrue(br.violations("<table><tr><td>FloraFresh</td><td>4 strains</td></tr></table>"))

    def test_text_without_florafresh_is_out_of_scope(self):
        for text in ("Our 15 billion CFU Lactobacillus blend", "sugar free probiotic gummies for women",
                     "XOS and D-mannose in other brands"):
            self.assertFalse(ff.in_scope(text))
            self.assertEqual(br.violations(text), [], text)

    def test_urls_and_slugs_are_not_copy(self):
        link = "Link `/blogs/news/florafresh-vs-generic-probiotics-4-strain-facts-us-2026` for format questions."
        self.assertEqual(br.violations(link), [])
        kept, blocked = br.indexnow_urls(["https://wellnessnest.co/blogs/news/florafresh-15-billion-cfu-guide"])
        self.assertEqual((len(kept), len(blocked)), (1, 0))


class LandingSpecs(unittest.TestCase):
    def test_product_blocks_are_florafresh_claims(self):
        spec = {"title": "FloraFresh: what the label says", "template": "listicle",
                "product": {"name": "Vaginal Probiotic Gummies", "bullets": ["1B CFU", "Sugar-free"]},
                "offer": {"bullets": ["Lactobacillus rhamnosus + L. gasseri"]}}
        bad = br.spec_violations(spec)
        self.assertTrue(any("1B CFU" in r and r.endswith("(product)") for r in bad), bad)
        self.assertTrue(any("not sugar-free" in r for r in bad), bad)
        self.assertTrue(any("rhamnosus" in r and r.endswith("(offer)") for r in bad), bad)

    def test_provenance_notes_may_quote_the_wrong_pdp(self):
        spec = {"title": "FloraFresh", "image_note": "PDP lists 4 Lactobacillus strains",
                "offer": {"price_source": "PDP says 15 billion CFU and sugar-free; dropped, not on the label"},
                "sources": [{"label": "PDP: four Lactobacillus strains, 15 billion CFU", "url": ff.PRODUCT_URL}]}
        self.assertEqual(br.spec_violations(spec), [])
        self.assertTrue(ff.violations(json.dumps(spec)))

    def test_chart_source_is_checked(self):
        spec = {"title": "FloraFresh", "items": [{"chart": {"source": "FloraFresh: 1 billion CFU per serving"}}]}
        self.assertTrue(br.spec_violations(spec))

    def test_ageaura_spec_rules_unchanged(self):
        self.assertTrue(any("Urolithin" in r for r in br.spec_violations({"title": "AgeAura Pure Urolithin A"})))
        self.assertEqual(br.spec_violations({"title": "AgeAura Pure NMN + TMG NAD Complex"}), [])


class BrandRulesIntegration(unittest.TestCase):
    def test_builders_and_image_prompts_refuse_the_pdp_formula(self):
        with self.assertRaises(br.GuardError):
            br.prepare_ticket("- [ ] listicle | wellnessnest | product=" + ff.HANDLE + " · angle: 1 billion CFU")
        with self.assertRaises(br.GuardError):
            br.prepare_image_request("FloraFresh pouch with a sugar-free badge", [ff.HANDLE])
        prompt, specs = br.prepare_image_request("FloraFresh pouch on a linen shelf, no people's faces", [ff.HANDLE])
        self.assertEqual(specs, [ff.HANDLE])
        self.assertNotIn("AgeAura", prompt)

    def test_publisher_gate(self):
        with self.assertRaises(br.GuardError):
            br.assert_publishable("FloraFresh review", "FloraFresh delivers 1B CFU.")
        br.assert_publishable("FloraFresh review", "FloraFresh: " + ff.FORMULA_LINE + ". " + ff.PRODUCT_URL)

    def test_ageaura_stays_nmn_tmg_only(self):
        self.assertEqual(br.assess("AgeAura review").action, "force")
        self.assertEqual(br.assess("AgeAura Pure NMN + TMG NAD Complex").action, "allow")
        uro = br.assess("AgeAura Pure Urolithin A")
        self.assertEqual(uro.action, "deny")
        self.assertFalse(any(r.startswith("FloraFresh") for r in uro.reasons))
        both = br.assess("AgeAura review. FloraFresh is sugar-free.")
        self.assertEqual(both.action, "deny")
        self.assertTrue(any("AgeAura" in r for r in both.reasons))
        self.assertTrue(any("sugar-free" in r for r in both.reasons))
        self.assertIn(br.AGEAURA_OK, br.prepare_ticket("AgeAura review for adults over 40"))


class Gates(unittest.TestCase):
    def test_topic_fitness(self):
        verdict, code, why = tf.assess("FloraFresh 1 billion CFU review")
        self.assertEqual((verdict, code), ("FAIL", "florafresh-formula"))
        self.assertIn(ff.STRAIN, why)
        self.assertEqual(tf.assess("FloraFresh 1B CFU review")[:2], ("FAIL", "florafresh-formula"))
        self.assertEqual(tf.assess("FloraFresh 15B CFU review")[0], "PASS")
        self.assertEqual(tf.assess("FloraFresh sugar free gummies review")[:2], ("FAIL", "florafresh-formula"))
        self.assertEqual(tf.assess("FloraFresh Bacillus coagulans SNZ-1969 review")[0], "PASS")
        self.assertEqual(tf.assess("urolithin a benefits review")[1], "ageaura-sku")

    def test_lint_tickets_open_only(self):
        body = ("**#XX1010-1 — vaginal probiotic dosage** — `Vaginal Probiotic Dosage (US 2026)`\n"
                "  - **Hero product:** `/products/" + ff.HANDLE + "`\n"
                "  - **Angle:** " + OLD_ANGLE + "\n")
        code, out = lint("# queue\n\n- [ ] " + body)
        self.assertEqual(code, 2, out)
        self.assertIn("cited from the PDP", out)
        code, out = lint("# queue\n\n- [DONE 2026-10-09 https://wellnessnest.co/blogs/news/x] " + body)
        self.assertEqual(code, 0, out)
        code, out = lint("# queue\n\n- [ ] " + body.replace(OLD_ANGLE, "Place FloraFresh from its label.")
                         + "  - " + ff.TICKET_LINE + "\n")
        self.assertEqual(code, 0, out)

    def test_real_queues_lint_clean(self):
        for rel in ("daily-tickets.md", "daily-landing-tickets.md"):
            r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "lint_tickets.py"),
                                os.path.join(ROOT, rel)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout)

    def test_refill_self_test(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = rt.self_test()
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("FloraFresh ticket carries the Supplement Facts label formula", out.getvalue())

    def test_landing_queue_line_carries_the_label_note(self):
        line = ("- [ ] listicle | wellnessnest | product=" + ff.HANDLE + " · angle: N things to know · audience: "
                "women · " + ff.LANDING_NOTE + " (added 2026-10-10)")
        self.assertEqual(br.prepare_ticket(line), line)
        self.assertEqual(br.violations(line), [])
        with tempfile.TemporaryDirectory() as d:
            queue = os.path.join(d, "daily-landing-tickets.md")
            with open(queue, "w", encoding="utf-8") as fh:
                fh.write(line + "\n")
            saved, blt.QUEUE = blt.QUEUE, queue
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", ResourceWarning)
                    counts = blt.angle_counts(ff.HANDLE)
            finally:
                blt.QUEUE = saved
        self.assertEqual(counts, {"N things to know": 1})


def open_florafresh_label_errors(block):
    """Label problems on one open FloraFresh ticket. An empty queue has nothing to check."""
    head = block.split("\n")[0][:60]
    errors = [f"{head}: {v}" for v in br.violations(block)]
    if ff.TICKET_LINE not in block:
        errors.append(head + ": missing Supplement Facts label line")
    if re.search(r"(?i)(?<![\d.])\b1[\s-]*(?:billion|bn)\s*cfu\b|(?<![\d.])\b1[\s-]*b\s*cfu\b", block):
        errors.append(head + ": retired 1 billion CFU / 1B CFU")
    return errors


class QueueData(unittest.TestCase):
    def test_open_florafresh_tickets_follow_the_label(self):
        text = read("daily-tickets.md")
        blocks = re.split(r"\n(?=- \[|## \[)", text)
        open_blocks = [b for b in blocks if OPEN_HEAD.match(b)]
        # The splitter has to see every open checkbox, so a broken parse cannot
        # hide a bad ticket behind an empty match. Zero open FloraFresh tickets
        # is a valid queue: the runner publishes them, and DONE tickets are out
        # of scope. Every ticket that is still open must carry the label line.
        self.assertEqual(len(open_blocks), len(re.findall(r"(?m)^(?:- \[ \]|## \[ \])", text)))
        good = (
            "- [ ] **#T — vaginal probiotics**\n"
            "  - **Hero product:** `/products/" + ff.HANDLE + "`\n"
            "  - " + ff.TICKET_LINE + "\n"
        )
        self.assertEqual(open_florafresh_label_errors(good), [])
        self.assertEqual(open_florafresh_label_errors(good + "Each serving delivers 15 billion CFU.\n"), [])
        self.assertTrue(open_florafresh_label_errors(good + "Each serving delivers 1 billion CFU.\n"))
        self.assertTrue(open_florafresh_label_errors(good + "Each serving delivers 1B CFU.\n"))
        self.assertTrue(open_florafresh_label_errors(good.replace("  - " + ff.TICKET_LINE + "\n", "")))
        for block in open_blocks:
            if FF_RX.search(block):
                self.assertEqual(open_florafresh_label_errors(block), [])

    def test_board_and_bank_prefer_the_label(self):
        with open(os.path.join(ROOT, "board", "ideas.csv"), encoding="utf-8", newline="") as fh:
            rows = {r["id"]: r for r in csv.DictReader(fh)}
        bank = {t["id"]: t for t in json.loads(read("templates/article-topic-bank.json"))["topics"]}
        for tid in ("vaginal-probiotic-dosage", "where-to-buy-vaginal-probiotics"):
            row, topic = rows[tid], bank[tid]
            self.assertEqual(row["angle"], topic["angle"], tid)
            self.assertEqual(row["secondary"].split("; "), topic["secondary"], tid)
            brief = " ".join([topic["primary"], topic["title"], topic["intent"], topic["angle"], topic["evidence"]]
                             + topic["secondary"] + topic["fanout"])
            self.assertEqual(br.violations(brief), [], tid)
            self.assertIn("Supplement Facts label", topic["angle"], tid)
            self.assertIn("Supplement Facts label", topic["evidence"], tid)
        dosage = bank["vaginal-probiotic-dosage"]
        self.assertNotIn("1 billion cfu probiotic", dosage["secondary"])
        self.assertIn("15B CFU", dosage["angle"])
        self.assertIn("the label wins", dosage["angle"])
        self.assertIn("fails the gate", dosage["angle"])

    def test_call_sites_use_the_guard(self):
        for rel in ("scripts/validate_landing.py", "scripts/landing_render.py", "scripts/landing_publisher.py",
                    "scripts/tools/landing_task5_specs.py"):
            self.assertIn("spec_violations", read(rel), rel)
        for rel in ("scripts/brand_rules.py", "scripts/topic_fitness.py", "scripts/refill_tickets.py",
                    "scripts/build_landing_tickets.py", "scripts/shopify_publisher.py"):
            self.assertIn("florafresh_rules", read(rel), rel)
        for rel in ("scripts/run_ticket_headless.sh", "scripts/run_landing_headless.sh",
                    "templates/landing/listicle-angles.json", "docs/FLORAFRESH_FORMULA_GUARD.md"):
            self.assertIn("SNZ-1969", read(rel), rel)

    def test_cli(self):
        script = os.path.join(ROOT, "scripts", "florafresh_rules.py")
        r = subprocess.run([sys.executable, script, "--brief"], capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, ff.TICKET_LINE))
        r = subprocess.run([sys.executable, script, "FloraFresh is sugar-free."], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)
        r = subprocess.run([sys.executable, script, "--spec", LISTICLE], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("1 billion CFU", r.stdout)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "florafresh-15b.json")
            spec = {"title": "FloraFresh label facts",
                    "product": {"name": "FloraFresh", "bullets": [
                        "15B CFU per 2 gummies", "Bacillus coagulans SNZ-1969",
                        "Vitamin C 30 mg", "sweetened with maltitol and isomalt, not sugar-free"]}}
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(spec, fh)
            r = subprocess.run([sys.executable, script, "--spec", path], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()

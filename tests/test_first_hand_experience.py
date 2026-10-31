"""Rights-gated first-hand experience block for blog articles.

Seeded lines come from the Kenzie R. (086ac23e) and Hillary H. (e16b6841)
Trybe verdict transcripts. They stay off until rights_confirmed and approved_by
are both set.
"""
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import ageaura_rules
import first_hand_experience as fh

HANDLE = "ageaura-pure-nmn-tmg-nad-complex"
REGISTRY = os.path.join(ROOT, "templates", "first-hand-quotes.json")

# Spoken words from the verdict cards, with the card's clock marks removed.
# Kenzie 086ac23e. Hillary e16b6841. "Thanks for watching!" is the card's
# noted whisper hallucination and is not part of either transcript.
KENZIE = (
    "Turns out I didn't need another bottle. I needed fewer, and a wellness brand that actually works. "
    "In collaboration with Wellness Nest, I found both a clean wellness company and a better supplement "
    "to support my active athletic goals and keeping up with my kids. "
    "Here I have my AgeAura bottle from Wellness Nest and it has helped me with no more afternoon crashes at 3 p.m. "
    "Keep your wellness routine simple and take two capsules at breakfast or in the morning time. "
    "Tap the link below and thank me later."
)
HILLARY = (
    "I'm done. I'm done having to use 12 different bottles just to feel like a functioning adult. "
    "This is all I'm keeping. AgeAura Pure NMN + TMG. I used to take a handful of pills every morning. "
    "Now just two capsules with breakfast. I also used to dread the 3 p.m. because of the energy drop. "
    "Now it's just another hour of my day. It supports cellular energy, which is so important, especially "
    "if you're like me and you're over 40. Just once a day and I can move on with my day. "
    "[If] your supplement shelf looks like a mini pharmacy, you need to tap the link below."
)


def load_seed():
    with open(REGISTRY, encoding="utf-8") as handle:
        return json.load(handle)


def entry(**overrides):
    base = {
        "id": "sample-quote-1",
        "product_handle": HANDLE,
        "creator_display_name": "Kenzie R.",
        "source": "086ac23e",
        "quote": "Now just two capsules with breakfast.",
        "timestamp_range": "0:12-0:15",
        "timestamp_precision": "scored-cut",
        "claim_check": "personal-feel",
        "disclosure": "Paid partnership (#ad)",
        "rights_confirmed": False,
        "approved_by": "",
    }
    base.update(overrides)
    return base


def registry_with(quotes, products=None):
    seed = load_seed()
    return {"version": 1, "products": products or seed["products"], "quotes": quotes}


def cleared(quote_id="hillary-e16b6841-two-capsules"):
    data = load_seed()
    for item in data["quotes"]:
        if item["id"] == quote_id:
            item["rights_confirmed"] = True
            item["approved_by"] = "Kevin"
    return data


class RegistryTests(unittest.TestCase):
    def test_seed_validates_and_stays_gated_off(self):
        data = load_seed()
        self.assertEqual(fh.registry_problems(data), [])
        self.assertEqual(len(data["quotes"]), 8)
        creators = {}
        for item in data["quotes"]:
            creators.setdefault(item["creator_display_name"], []).append(item)
            self.assertFalse(item["rights_confirmed"])
            self.assertEqual(item["approved_by"], "")
            self.assertEqual(item["product_handle"], HANDLE)
            self.assertEqual(item["claim_check"], "personal-feel")
            self.assertTrue(fh.disclosure_ok(item["disclosure"]))
            self.assertNotIn("Huyghue", json.dumps(item))
            self.assertNotIn("a wellness brand that actually works", item["quote"])
            self.assertNotIn("tap the link", item["quote"].lower())
            self.assertNotIn("Thanks for watching", item["quote"])
        self.assertEqual(set(creators), {"Kenzie R.", "Hillary H."})
        self.assertGreaterEqual(len(creators["Kenzie R."]), 2)
        self.assertLessEqual(len(creators["Kenzie R."]), 4)
        self.assertGreaterEqual(len(creators["Hillary H."]), 2)
        self.assertLessEqual(len(creators["Hillary H."]), 4)
        self.assertEqual(
            {item["source"] for item in creators["Kenzie R."]},
            {"086ac23e"},
        )
        self.assertEqual(
            {item["source"] for item in creators["Hillary H."]},
            {"e16b6841"},
        )

    def test_seed_quotes_are_verbatim_transcript_excerpts(self):
        data = load_seed()
        for item in data["quotes"]:
            source = KENZIE if item["source"] == "086ac23e" else HILLARY
            self.assertIn(item["quote"], source, item["id"])

    def test_seed_label_matches_the_pack_file_and_the_allowlist(self):
        data = load_seed()
        product = data["products"][HANDLE]
        self.assertEqual(product["label"], ageaura_rules.PRODUCT_LABEL)
        self.assertEqual(product["label_dose"]["count"], 2)
        self.assertEqual(product["label_dose"]["form"], "capsules")
        with open(
            os.path.join(ROOT, "product_refs", HANDLE + ".label.json"),
            encoding="utf-8",
        ) as handle:
            label = json.load(handle)
        required = label["required"]
        self.assertIn("60", required)
        self.assertIn("Capsules", required)
        self.assertIn("30 Servings", required)
        blob = json.dumps(label)
        self.assertIsNone(re.search(r"\b(?:mg|mcg|milligrams?)\b", blob, re.I))

    def test_real_registry_renders_nothing(self):
        self.assertEqual(fh.render_block(load_seed(), HANDLE), "")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = fh.main(["--product", HANDLE])
        self.assertEqual(code, 0)
        self.assertIn("not rights-confirmed", err.getvalue())
        self.assertNotIn("two capsules", err.getvalue())

    def test_doc_lists_every_seeded_quote(self):
        doc_path = os.path.join(ROOT, "docs", "FIRST_HAND_EXPERIENCE.md")
        with open(doc_path, encoding="utf-8") as handle:
            doc = handle.read()
        for item in load_seed()["quotes"]:
            self.assertIn(item["id"], doc)
            self.assertIn(item["quote"], doc)
            self.assertIn(item["creator_display_name"], doc)


class LintTests(unittest.TestCase):
    def test_label_dose_passes_and_other_doses_fail(self):
        products = load_seed()["products"]
        self.assertEqual(fh.lint_quote(entry(), products), [])
        self.assertEqual(
            fh.lint_quote(entry(quote="Keep your wellness routine simple and take two capsules at breakfast."), products),
            [],
        )
        self.assertEqual(fh.lint_quote(entry(quote="Supports Healthy Aging is printed on the bottle."), products), [])
        self.assertEqual(fh.lint_quote(entry(quote="We spent the weekend on a quiet retreat."), products), [])
        blocked = {
            "disease": "This product cures no disease and I still will not say that.",
            "cure": "I want a cure for how afternoons feel.",
            "treat": "It treats the slump I get after lunch.",
            "reverse aging": "I hoped it would reverse the aging I feel.",
            "anti-aging": "I bought it as an anti-aging capsule routine.",
            "anti aging spaced": "I bought it as an anti aging capsule routine.",
            "three capsules": "I take three capsules with breakfast now.",
            "500 mg": "I take 500 mg with breakfast now.",
            "twice a day": "I take two capsules twice a day.",
            "generic efficacy": "I needed a wellness brand that actually works.",
            "cta": "Tap the link below and thank me later please.",
            "hallucination": "Thanks for watching the rest of my morning.",
            "missing disclosure": "Now just two capsules with breakfast.",
        }
        for name, quote in blocked.items():
            item = entry(quote=quote)
            if name == "missing disclosure":
                item["disclosure"] = "Thanks to the brand"
            problems = fh.lint_quote(item, products)
            self.assertTrue(problems, name)
            if name == "missing disclosure":
                self.assertIn("missing disclosure", problems[0])
            elif name in ("three capsules", "500 mg", "twice a day"):
                self.assertIn("2 capsules daily", problems[0])

    def test_paid_creator_marker_is_required_with_paid_partnership(self):
        products = load_seed()["products"]
        item = entry(disclosure="Paid partnership")
        self.assertIn("missing disclosure", fh.lint_quote(item, products)[0])
        item["disclosure"] = "paid creator"
        self.assertIn("missing disclosure", fh.lint_quote(item, products)[0])

    def test_schema_rejects_a_full_last_name_and_a_denied_handle(self):
        bad_name = registry_with([entry(creator_display_name="Hillary Huyghue")])
        self.assertTrue(any("first name" in item for item in fh.schema_errors(bad_name)))
        denied = registry_with(
            [entry(product_handle="ageaura-pure-urolithin-a")],
            products={
                "ageaura-pure-urolithin-a": {
                    "label": "nope",
                    "label_dose": {"count": 2, "form": "capsules", "schedule": "once daily"},
                }
            },
        )
        blob = " ".join(fh.schema_errors(denied))
        self.assertIn("denied product handle", blob)

    def test_full_vo_requires_a_note(self):
        item = entry(timestamp_precision="full-vo", timestamp_range="0:00-0:28.9")
        self.assertTrue(any("timestamp_note" in line for line in fh.schema_errors(registry_with([item]))))


class GateRenderTests(unittest.TestCase):
    def test_both_flags_are_required(self):
        data = load_seed()
        target = data["quotes"][6]
        self.assertEqual(target["id"], "hillary-e16b6841-two-capsules")
        cases = [
            (False, ""),
            (False, "Kevin"),
            (True, ""),
            (True, "   "),
        ]
        for rights, approved in cases:
            target["rights_confirmed"] = rights
            target["approved_by"] = approved
            self.assertEqual(fh.render_block(data, HANDLE), "", (rights, approved))
        target["rights_confirmed"] = True
        target["approved_by"] = "Kevin"
        html = fh.render_block(data, HANDLE)
        self.assertIn("<blockquote", html)
        self.assertIn("Now just two capsules with breakfast.", html)
        self.assertIn("Hillary H., on AgeAura Pure NMN + TMG NAD+ Complex", html)
        self.assertIn("Paid partnership (#ad)", html)
        self.assertIn("Results vary.", html)
        self.assertIn('data-genseo-first-hand="hillary-e16b6841-two-capsules"', html)
        self.assertIn('data-genseo-first-hand-block="%s"' % HANDLE, html)
        self.assertIn("#54b94a", html)
        self.assertNotIn("Dr.", html)
        self.assertNotIn("Huyghue", html)
        self.assertEqual(html.count("<blockquote"), 1)

    def test_claim_failure_blocks_a_cleared_quote(self):
        data = cleared()
        data["quotes"] = [
            entry(
                id="sample-quote-1",
                quote="It will cure the afternoon slump I had.",
                rights_confirmed=True,
                approved_by="Kevin",
            )
        ]
        self.assertEqual(fh.render_block(data, HANDLE), "")
        message = fh.skip_message(data, HANDLE)
        self.assertIn("cure", message)
        self.assertNotIn("afternoon slump", message)

    def test_html_is_escaped(self):
        data = registry_with([
            entry(
                quote="Fish & chips <are> not my morning routine.",
                rights_confirmed=True,
                approved_by="Kevin",
            )
        ])
        html = fh.render_block(data, HANDLE)
        self.assertIn("Fish &amp; chips &lt;are&gt;", html)
        self.assertNotIn("<are>", html)

    def test_id_filter_and_product_url(self):
        data = cleared("kenzie-086ac23e-3pm")
        data["quotes"][6]["rights_confirmed"] = True
        data["quotes"][6]["approved_by"] = "Kevin"
        one = fh.render_block(data, "https://wellnessnest.co/products/" + HANDLE, quote_id="kenzie-086ac23e-3pm")
        self.assertIn("afternoon crashes at 3 p.m.", one)
        self.assertNotIn("two capsules with breakfast", one)
        self.assertEqual(fh.render_block(data, HANDLE, quote_id="missing-id"), "")
        both = fh.render_block(data, HANDLE)
        self.assertEqual(both.count("<blockquote"), 2)
        self.assertLess(both.index("afternoon crashes"), both.index("two capsules with breakfast"))

    def test_article_gate_is_silent_until_a_quote_is_pasted(self):
        article = (
            '<p><a href="https://wellnessnest.co/products/%s">AgeAura Pure NMN + TMG</a> '
            "in the US is a two-capsule morning routine.</p>" % HANDLE
        )
        fails, warns = fh.article_findings(article)
        self.assertEqual(fails, [])
        self.assertEqual(warns, [])

    def test_article_gate_rejects_an_unapproved_paste(self):
        fails, _warns = fh.article_findings(
            "<p>Now just two capsules with breakfast. That is the whole routine.</p>"
        )
        self.assertTrue(any("unapproved first-hand quote pasted: hillary-e16b6841-two-capsules" in item for item in fails))

    def test_article_gate_accepts_a_cleared_block_and_rejects_a_stripped_one(self):
        data = cleared()
        block = fh.render_block(data, HANDLE, quote_id="hillary-e16b6841-two-capsules")
        fails, warns = fh.article_findings("<p>Intro.</p>\n" + block, registry=data)
        self.assertEqual(fails, [])
        self.assertEqual(warns, [])
        stripped = block.replace("Paid partnership (#ad)", "").replace("Results vary.", "")
        fails, _warns = fh.article_findings(stripped, registry=data)
        self.assertTrue(any("missing disclosure" in item for item in fails))
        self.assertTrue(any("missing results vary note" in item for item in fails))

    def test_article_gate_rejects_a_swapped_line_and_an_unknown_id(self):
        data = cleared()
        swapped = fh.render_block(data, HANDLE, quote_id="hillary-e16b6841-two-capsules")
        swapped = swapped.replace(
            "Now just two capsules with breakfast.",
            "This cure works for everyone who tries it.",
        )
        fails, _warns = fh.article_findings(swapped, registry=data)
        self.assertTrue(any("does not match the registry" in item for item in fails))
        unknown = '<div data-genseo-first-hand="not-a-real-quote"><blockquote><p>Hi.</p></blockquote></div>'
        fails, _warns = fh.article_findings(unknown, registry=data)
        self.assertIn("unknown first-hand quote id: not-a-real-quote", fails)

    def test_article_gate_rejects_a_cleared_disease_line(self):
        data = registry_with([
            entry(
                quote="It treats the afternoon slump I used to dread.",
                rights_confirmed=True,
                approved_by="Kevin",
            )
        ])
        block = (
            '<div data-genseo-first-hand="sample-quote-1"><blockquote><p>%s</p></blockquote>'
            "<p>Paid partnership (#ad)</p><p>Results vary.</p></div>"
            % data["quotes"][0]["quote"]
        )
        fails, _warns = fh.article_findings(block, registry=data)
        self.assertTrue(any("failed claim lint" in item and "treat" in item for item in fails))

    def test_cli_lint_and_gated_render(self):
        lint = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "first_hand_experience.py"), "--lint"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(lint.returncode, 0, lint.stderr)
        self.assertIn("OK (8)", lint.stdout)
        render = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "first_hand_experience.py"), "--product", HANDLE],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(render.returncode, 0, render.stderr)
        self.assertEqual(render.stdout.strip(), "")
        self.assertIn("not rights-confirmed", render.stderr)
        self.assertNotIn("two capsules", render.stdout)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "quotes.json")
            bad = registry_with([entry(quote="This will cure my afternoon.")])
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(bad, handle)
            failed = subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "first_hand_experience.py"), "--lint", "--registry", path],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(failed.returncode, 1)
        self.assertIn("cure", failed.stderr)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fh.main([]), 2)

    def test_pipeline_wires_the_gate_and_landing_pages_do_not(self):
        with open(os.path.join(ROOT, "scripts", "validate_article.py"), encoding="utf-8") as handle:
            gate = handle.read()
        self.assertIn("article_findings", gate)
        skill = os.path.join(ROOT, "skills", "genseo-auto-publish", "SKILL.md")
        templates = os.path.join(ROOT, "skills", "genseo-auto-publish", "references", "article-templates.md")
        with open(skill, encoding="utf-8") as handle:
            skill_text = handle.read()
        with open(templates, encoding="utf-8") as handle:
            template_text = handle.read()
        self.assertIn("first_hand_experience.py", skill_text)
        self.assertIn("first_hand_experience.py", template_text)
        for rel in (
            "scripts/landing_render.py",
            "scripts/landing_publisher.py",
            "scripts/validate_landing.py",
            "scripts/shopify_publisher.py",
        ):
            with open(os.path.join(ROOT, rel), encoding="utf-8") as handle:
                text = handle.read()
            self.assertNotIn("first_hand_experience", text, rel)


if __name__ == "__main__":
    unittest.main()

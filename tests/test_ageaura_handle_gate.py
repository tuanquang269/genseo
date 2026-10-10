"""AgeAura product handles: NMN + TMG is the only target. Urolithin fails closed."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import ageaura_rules as ar
import brand_rules as br
import build_catalog_tickets as catalog
import build_landing_tickets as landing
import refill_tickets as refill
import validate_landing as vl
import landing_label_gate as lg

NMN = "ageaura-pure-nmn-tmg-nad-complex"
URO = "ageaura-pure-urolithin-a"
OTHER_URO = (
    "ageaura-urolithin-a",
    "ageaura-pure-urolithin-a-60",
    "ageaura-pure-urolithin",
    "urolithin-a",
)


class AllowDenyTests(unittest.TestCase):
    def test_allowlist_is_the_nmn_handle_only(self):
        self.assertEqual(ar.ALLOWED_HANDLES, frozenset({NMN}))
        self.assertIn(URO, ar.DENIED_HANDLES)
        self.assertEqual(ar.classify_handle(NMN), "allow")
        self.assertEqual(ar.classify_handle("https://wellnessnest.co/products/" + NMN), "allow")
        self.assertEqual(ar.classify_handle(NMN + ":0"), "allow")
        self.assertEqual(ar.require_target(NMN), NMN)
        self.assertEqual(ar.require_target("https://wellnessnest.co/products/" + NMN + ".js"), NMN)
        self.assertTrue(ar.product_allowed(NMN))
        self.assertTrue(br.product_allowed(NMN))
        self.assertEqual(br.AGEAURA_OK, NMN)

    def test_urolithin_and_other_ageaura_skus_are_denied(self):
        denied = (URO, "https://wellnessnest.co/products/" + URO, URO + ":0") + OTHER_URO
        denied += ("ageaura-pure-nmn-tmg-p2", "ageaura-peptide-complex", "ageaura")
        for handle in denied:
            self.assertEqual(ar.classify_handle(handle), "deny", handle)
            self.assertFalse(ar.product_allowed(handle), handle)
            self.assertIsNone(ar.guard_product_handle(handle), handle)
            with self.assertRaises(ar.AgeAuraProductError):
                ar.require_target(handle)
        self.assertEqual(ar.classify_handle("fusiforce-creatine-gummies"), "other")
        self.assertEqual(ar.require_target("fusiforce-creatine-gummies"), "fusiforce-creatine-gummies")
        self.assertTrue(ar.product_allowed(""))

    def test_campaign_slug_is_not_a_product_target_in_prose(self):
        slug = "ageaura-nmn-listicle-261008"
        self.assertEqual(ar.handles_in_text(slug), [])
        self.assertEqual(ar.text_target_violations(slug), [])
        self.assertTrue(ar.article_link_allowed(slug))
        self.assertFalse(ar.article_link_allowed("urolithin-a-old-page"))
        self.assertFalse(ar.article_link_allowed(URO))
        self.assertTrue(ar.article_link_allowed("nmn-and-alcohol-can-you-drink-while-taking-nmn-us"))

    def test_cli_brief_and_handle(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = ar.main(["--brief"])
        brief = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn(NMN, brief)
        self.assertIn(URO, brief)
        self.assertNotIn("500 mg", brief)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = ar.main(["--handle", NMN])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), NMN)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = ar.main(["--handle", URO])
        self.assertEqual(code, 1)
        self.assertIn(URO, buf.getvalue())


class LandingAndTicketTests(unittest.TestCase):
    def test_validate_landing_refuses_urolithin_handle_and_accepts_nmn(self):
        nmn = {
            "slug": "ageaura-nmn-listicle-261008",
            "handle": "nmn-after-40-research",
            "product": {"handle": NMN, "name": "AgeAura Pure NMN + TMG NAD+ Complex"},
            "hero": {"cta": {"href": "https://wellnessnest.co/products/" + NMN}},
        }
        uro = {
            "slug": "ageaura-nmn-listicle-261008",
            "handle": "gsl-preview-ageaura-nmn",
            "product": {"handle": URO, "name": "AgeAura Pure NMN + TMG NAD+ Complex"},
            "hero": {"cta": {"href": "https://wellnessnest.co/products/" + URO}},
        }
        other = {"product": {"handle": "ageaura-pure-nmn-tmg-p2"}}
        bare = {"product_ref": "ageaura-urolithin-a"}
        underscored = {"product": {"handle": "ageaura_pure_urolithin_a", "name": "AgeAura Pure NMN + TMG"}}
        self.assertEqual(vl.ageaura_target_errors(nmn), [])
        self.assertEqual(br.spec_violations(nmn), [])
        for spec in (uro, other, bare, underscored):
            errs = vl.ageaura_target_errors(spec)
            self.assertTrue(errs, spec)
            self.assertTrue(any("denied product handle" in e for e in errs), errs)
            self.assertTrue(br.spec_violations(spec), spec)
        campaign = {"slug": "ageaura-nmn-listicle-261008", "handle": "gsl-preview-ageaura-nmn"}
        self.assertEqual(vl.ageaura_target_errors(campaign), [])

    def test_live_nmn_landing_spec_passes_the_handle_gate(self):
        path = os.path.join(ROOT, "landing_drafts", "ageaura-nmn-listicle-261008.json")
        with open(path, encoding="utf-8") as fh:
            spec = json.load(fh)
        self.assertEqual(vl.ageaura_target_errors(spec), [])
        self.assertEqual(ar.spec_target_violations(spec), [])

    def test_landing_ticket_line_and_angle_catalog(self):
        with self.assertRaises(br.GuardError):
            landing.ticket_line(URO, "ageaura", "what the trials measured", "adults 40+", "2026-10-10")
        with self.assertRaises(br.GuardError):
            landing.ticket_line("ageaura-urolithin-a", "ageaura", "angle", "adults", "2026-10-10")
        line = landing.ticket_line(NMN, "ageaura", "what the trials measured", "adults 40+", "2026-10-10")
        self.assertIn("product=" + NMN, line)
        self.assertNotIn("urolithin", line.lower())
        self.assertEqual(br.violations(line), [])
        angles_path = os.path.join(ROOT, "templates", "landing", "listicle-angles.json")
        with open(angles_path, encoding="utf-8") as fh:
            angles = json.load(fh)
        self.assertIn(NMN, angles)
        self.assertNotIn(URO, angles)
        self.assertEqual(landing.refused_angle_keys(angles), [])
        tampered = dict(angles)
        tampered[URO] = {"store": "ageaura", "angles": ["do not emit"]}
        self.assertIn(URO, landing.refused_angle_keys(tampered))

    def test_article_ticket_builders_refuse_the_handle(self):
        with self.assertRaises(br.GuardError):
            catalog.guard_anchor(URO)
        self.assertEqual(catalog.guard_anchor(NMN), NMN)
        self.assertEqual(catalog.guard_anchor("fusiforce-creatine-gummies"), "fusiforce-creatine-gummies")
        with self.assertRaises(br.GuardError):
            refill.guard_hero(URO)
        self.assertEqual(refill.guard_hero(NMN), NMN)
        self.assertIsNone(ar.guard_product_handle("https://wellnessnest.co/products/" + URO))
        self.assertEqual(ar.guard_product_handle("https://wellnessnest.co/products/" + NMN), NMN)

    def test_label_gate_refuses_urolithin_even_if_a_whitelist_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = os.path.join(tmp, "product_refs")
            os.makedirs(folder)
            with open(os.path.join(folder, URO + ".label.json"), "w", encoding="utf-8") as fh:
                json.dump({"handle": URO, "required": ["not a real label line"]}, fh)
            with self.assertRaises(lg.LabelGateError) as caught:
                lg.evaluate(URO, ocr_lines=["not a real label line"], root=tmp)
            self.assertIn("denied product handle", str(caught.exception))
            self.assertIn(URO, str(caught.exception))
            self.assertNotIn("LABEL PASS", str(caught.exception))
            spec = {
                "pack_images": ["pack.png"],
                "hero": {"cta": {"href": "https://wellnessnest.co/products/" + URO}},
            }
            errs = lg.whitelist_pack_errors(spec, root=tmp)
            self.assertTrue(any(URO in e for e in errs), errs)

    def test_builders_call_the_shared_helper(self):
        rels = [
            "scripts/brand_rules.py",
            "scripts/validate_landing.py",
            "scripts/build_landing_tickets.py",
            "scripts/build_catalog_tickets.py",
            "scripts/build_ctr_tickets.py",
            "scripts/refill_tickets.py",
            "scripts/landing_label_gate.py",
            "scripts/refresh_targets.py",
            "scripts/build_refresh_tickets.py",
            "scripts/generate_refresh_tickets.py",
            "scripts/packaging_palette.py",
            "scripts/llms_formula.py",
        ]
        for rel in rels:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("ageaura_rules", text, rel)


if __name__ == "__main__":
    unittest.main()

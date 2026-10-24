"""Local llms.txt drafts omit Urolithin A and state a formula only when the label supports it."""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import brand_rules as br
import florafresh_rules as ff
import llms_formula as lf
import llms_txt_draft

NMN = "ageaura-pure-nmn-tmg-nad-complex"
URO = "ageaura-pure-urolithin-a"


def draft_from_refs():
    handles = br.handles_from_product_refs(os.path.join(ROOT, "product_refs"))
    return br.llms_txt_draft(handles)


class FormulaMatchesLabel(unittest.TestCase):
    def test_supported_lines_match_and_bad_lines_do_not(self):
        flora = lf.formula_line(ff.HANDLE)
        fusi = lf.formula_line(lf.FUSI)
        shil = lf.formula_line(lf.SHIL)
        self.assertIn(ff.STRAIN, flora)
        self.assertIn(ff.CFU, flora)
        self.assertIn("90 gummies", fusi)
        self.assertIn("60 gummies", shil)
        self.assertIn("60-day", shil)
        for handle in (
            NMN, URO, "pure-shilajit-gold-resin", "shilajit-shockwave",
            "turkesterone-advanced-formula", "shilasource-himalayan-shilajit-resin",
        ):
            self.assertIsNone(lf.formula_line(handle), handle)
        self.assertFalse(lf.matches_label(lf.FUSI, "FusiForce, 84 gummies."))
        self.assertFalse(lf.matches_label(lf.FUSI, "FusiForce, 90 gummies and 25 mg ginseng."))
        self.assertFalse(lf.matches_label(lf.FUSI, "FusiForce, 90 gummies and 50 mg ginseng."))
        self.assertTrue(lf.matches_label(lf.FUSI, "FusiForce, 90 gummies, 30 servings."))
        self.assertTrue(lf.matches_label(lf.FUSI, "FusiForce, 90 gummies, 3 gummies per serving."))
        self.assertFalse(lf.matches_label(lf.FUSI, "FusiForce, 90 gummies, 5,000 mg."))
        self.assertFalse(lf.matches_label(lf.FUSI, "FusiForce, 90 gummies and Panax ginseng."))
        self.assertFalse(lf.matches_label(lf.FUSI, "FusiForce, 90 gummies, 4 gummies per serving."))
        self.assertFalse(lf.matches_label(lf.SHIL, "Shilajit gummies, 60 gummies, 30 servings."))
        self.assertFalse(lf.matches_label(ff.HANDLE, "FloraFresh delivers 15 billion CFU."))
        self.assertFalse(lf.matches_label(ff.HANDLE, "Urolithin A with " + ff.STRAIN + " " + ff.CFU))

    def test_urolithin_draft_is_refused(self):
        with self.assertRaises(br.GuardError):
            br.assert_llms_text("https://wellnessnest.co/products/" + URO)


class DraftText(unittest.TestCase):
    def test_product_ref_draft_keeps_label_facts_only(self):
        text, rejected = draft_from_refs()
        self.assertIn(URO, rejected)
        self.assertNotIn("urolithin", text.lower())
        self.assertIn(NMN, text)
        self.assertIn("https://wellnessnest.co/products/" + NMN, text)
        self.assertNotIn("https://wellnessnest.co/products/" + URO, text)
        self.assertIn(ff.STRAIN, text)
        self.assertIn("15B CFU", text)
        self.assertNotIn("1 billion CFU", text)
        self.assertNotIn("1B CFU", text)
        self.assertIn("90 gummies", text)
        self.assertNotIn("84", text)
        self.assertNotIn("25 mg", text.lower())
        self.assertNotIn("50 mg", text.lower())
        self.assertNotIn("30 servings", text.lower())
        self.assertIn("60 gummies", text)
        self.assertIn("60-day supply", text)
        self.assertIn(
            "- https://wellnessnest.co/products/pure-shilajit-gold-resin\n"
            "- https://wellnessnest.co/products/shilajit-shockwave\n",
            text,
        )
        self.assertIn(
            "- https://wellnessnest.co/products/turkesterone-advanced-formula\n",
            text,
        )
        self.assertNotIn("TURNESTERONE", text)
        self.assertNotIn("TURKESTERONE", text)
        self.assertNotIn("60 capsules", text.lower())
        self.assertNotIn("500 mg", text.lower())
        self.assertEqual(br.violations(text), [])

    def test_cli_writes_a_local_file_and_does_not_keep_urolithin(self):
        handles = br.handles_from_product_refs(os.path.join(ROOT, "product_refs"))
        text, _rejected = br.llms_txt_draft(handles)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "llms.txt")
            code = llms_txt_draft.main(["--from-product-refs", "--out", path])
            with open(path, encoding="utf-8") as fh:
                written = fh.read()
        self.assertEqual(code, 1)
        self.assertEqual(written, text)
        self.assertNotIn("urolithin", written.lower())

    def test_committed_local_draft_matches_the_generator(self):
        path = os.path.join(ROOT, "deploy", "llms-txt", "llms.txt")
        text, _rejected = draft_from_refs()
        with open(path, encoding="utf-8") as fh:
            committed = fh.read()
        self.assertEqual(committed, text)


if __name__ == "__main__":
    unittest.main()

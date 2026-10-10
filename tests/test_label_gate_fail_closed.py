"""Whitelist pack shots fail closed. These tests do not call macOS Vision."""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import landing_label_gate as lg

FUSI = "fusiforce-creatine-gummies"
SHIL = "premium-himalayan-shilajit-gummies"
SHOCK = "shilajit-shockwave"
TURK = "turkesterone-advanced-formula"
FLORA = "florafresh-vaginal-probiotics-gummies"
GOLD = "pure-shilajit-gold-resin"

FUSI_OK = [
    "Wellness", "Nest", "FusiForce", "Creatine", "Monohydrate", "Gummies",
    "Green Apple flavor", "Promotes Lean Muscle Growth*", "Enhances Recovery*",
    "Boosts Energy Levels*", "Supports Cognitive Function*", "90", "GUMMIES",
    "DIETARY", "SUPPLEMENT",
]
SHIL_OK = [
    "wellness", "nest", "PREMIUM HIMALAYAN", "SHILAJIT GUMMIES",
    "ASHWAGANDHA • GOKSHURA • BLACK MUSLI", "1500mg", "Shilajit", "75%",
    "Fulvic Acid", "85+ Trace", "Minerals", "60 GUMMIES", "60-DAY SUPPLY",
    "DIETARY SUPPLEMENT",
]
SHOCK_OK = [
    "wellness", "nest", "SHILAJIT", "SHOCKWAVE",
    "EXPERIENCE FOCUSED ENERGY", "PEAK PERFORMANCE",
]
TURK_OCR = [
    "wellness", "nest", "PREMIUM", "TURKESTERONE", "ADVANCED", "FORMULA",
    "AMPLIFY", "MUSCLE", "ENDURANCE", "60", "Dietary Supplement", "Capsules",
]
FLORA_OCR = [
    "FloraFresh", "Vaginal", "Probiotic", "Gummies", "60", "DIETARY", "GUMMIES", "SUPPLEMENT",
]
GOLD_OCR = [
    "wellness", "nest", "Himalayan", "Shilajit", "75% Fulvic", "Lab-Tested", "Acid",
    "Pure Shilajit Gold Resin", "1.06 oz (30g) - 75 servings", "Dietary Supplements",
]


class Proc:
    def __init__(self, code, out="", err=""):
        self.returncode = code
        self.stdout = out
        self.stderr = err


def load_label(handle):
    with open(os.path.join(ROOT, "product_refs", handle + ".label.json"), encoding="utf-8") as fh:
        return json.load(fh)


class FailClosedInfrastructure(unittest.TestCase):
    def test_missing_label_json_is_not_a_pass(self):
        for handle in ("not-a-stocked-handle",):
            with self.assertRaises(lg.LabelGateError) as caught:
                lg.evaluate(handle, ocr_lines=["anything"])
            message = str(caught.exception)
            self.assertIn("FAIL CLOSED", message)
            self.assertIn("do not invent", message.lower())
            self.assertNotIn("LABEL PASS", message)
        self.assertTrue(os.path.isfile(lg.label_json_path(TURK)))
        self.assertFalse(os.path.isfile(lg.label_json_path("ageaura-pure-urolithin-a")))
        note = lg.missing_label_note("ageaura-pure-urolithin-a")
        self.assertIn("not an allowed AgeAura", note)
        self.assertNotIn("TURNESTERONE", lg.missing_label_note("not-a-stocked-handle"))

    def test_cli_missing_label_exits_nonzero(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = lg.main(["no-such.png", "--handle", "not-a-stocked-handle"])
        text = buf.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("FAIL CLOSED", text)
        self.assertNotIn("LABEL PASS", text)

    def test_denied_ageaura_sku_exits_nonzero(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = lg.main(["no-such.png", "--handle", "ageaura-pure-urolithin-a"])
        self.assertEqual(code, 1)
        self.assertNotIn("LABEL PASS", buf.getvalue())

    def test_unsupported_platform_is_not_a_pass(self):
        with self.assertRaises(lg.LabelGateError) as caught:
            lg.read_ocr_lines("ignored.png", platform="linux")
        message = str(caught.exception)
        self.assertIn("FAIL CLOSED", message)
        self.assertIn("macOS Vision", message)
        self.assertIn("not a pass", message)
        self.assertIn("not a skip", message)

    def test_missing_swift_and_script_and_image(self):
        with self.assertRaises(lg.LabelGateError) as caught:
            lg.read_ocr_lines("ignored.png", platform="darwin", swift_bin="")
        self.assertIn("swift", str(caught.exception).lower())
        with self.assertRaises(lg.LabelGateError) as caught:
            lg.read_ocr_lines("ignored.png", platform="darwin", swift_bin="/usr/bin/swift", swift_script="/no/such.swift")
        self.assertIn("FAIL CLOSED", str(caught.exception))
        with self.assertRaises(lg.LabelGateError) as caught:
            lg.read_ocr_lines("/no/such-pack.png", platform="darwin", swift_bin="/usr/bin/swift")
        self.assertIn("not found", str(caught.exception))

    def test_failed_and_empty_ocr_are_not_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "pack.png")
            Image.new("RGB", (8, 8), "white").save(path)

            def failed(*_args):
                return Proc(2, "", "vision unavailable")

            def empty(*_args):
                return Proc(0, "not a tab line\n", "")

            def timed_out(*_args):
                raise subprocess.TimeoutExpired(cmd="swift", timeout=180)

            with self.assertRaises(lg.LabelGateError) as caught:
                lg.read_ocr_lines(path, runner=failed, platform="darwin", swift_bin="/usr/bin/swift")
            self.assertIn("exited 2", str(caught.exception))
            with self.assertRaises(lg.LabelGateError) as caught:
                lg.read_ocr_lines(path, runner=empty, platform="darwin", swift_bin="/usr/bin/swift")
            self.assertIn("no text", str(caught.exception))
            with self.assertRaises(lg.LabelGateError) as caught:
                lg.read_ocr_lines(path, runner=timed_out, platform="darwin", swift_bin="/usr/bin/swift")
            self.assertIn("timed out", str(caught.exception))
            with self.assertRaises(lg.LabelGateError):
                lg.evaluate(FUSI, ocr_lines=["  ", ""])

    def test_stubbed_lines_do_not_call_vision(self):
        def boom(*_args):
            raise AssertionError("swift was called")

        result = lg.evaluate(FUSI, ocr_lines=FUSI_OK, runner=boom, platform="linux", swift_bin="")
        self.assertTrue(result["ok"])


class GummyCountAndShockwave(unittest.TestCase):
    def test_fusiforce_84_fails_and_90_passes(self):
        spec = load_label(FUSI)
        self.assertEqual(lg.expected_gummy_counts(spec), [90])
        passed = lg.assess_lines(spec, FUSI_OK)
        self.assertTrue(passed["ok"], passed)
        replaced = lg.assess_lines(spec, [
            "FusiForce", "Creatine", "Monohydrate", "Gummies", "84", "Dietary Supplement",
        ])
        self.assertFalse(replaced["ok"])
        self.assertTrue(replaced["missing"] or replaced["conflicts"])
        self.assertIn("90", replaced["missing"])
        self.assertTrue(any("84" in item for item in replaced["conflicts"]))
        extra = lg.evaluate(FUSI, ocr_lines=FUSI_OK + ["84 gummies"])
        self.assertFalse(extra["ok"])
        self.assertTrue(any(item.startswith("84") for item in extra["conflicts"]))
        self.assertNotIn("LABEL PASS", lg.failure_text(extra))

    def test_shilajit_gummies_count_and_30_serving_panel(self):
        spec = load_label(SHIL)
        self.assertEqual(lg.expected_gummy_counts(spec), [60])
        passed = lg.assess_lines(spec, SHIL_OK)
        self.assertTrue(passed["ok"], passed)
        wrong_count = lg.assess_lines(spec, SHIL_OK + ["84 gummies"])
        self.assertFalse(wrong_count["ok"])
        self.assertTrue(any("84" in item for item in wrong_count["conflicts"]))
        panel = lg.assess_lines(spec, SHIL_OK + ["30 servings"])
        self.assertFalse(panel["ok"])
        self.assertTrue(any("30 servings" in item for item in panel["conflicts"]))

    def test_shockwave_rejects_invented_milligrams(self):
        spec = load_label(SHOCK)
        catalog = " ".join(spec["required"] + spec["optional"] + spec["accepted_ocr"])
        self.assertIsNone(lg._MG_DOSE.search(catalog))
        self.assertNotIn("1 il oz", catalog)
        self.assertNotIn("fl oz", catalog.lower())
        passed = lg.assess_lines(spec, SHOCK_OK)
        self.assertTrue(passed["ok"], passed)
        invented = lg.assess_lines(spec, SHOCK_OK + ["250 mg"])
        self.assertFalse(invented["ok"])
        self.assertTrue(any("250 mg" in item for item in invented["conflicts"]))
        # The gate's 2x read keeps the words and changes the trailing mark. The volume line stays out.
        scaled = [
            "wellness", "nest", "SHILAJIT", "SHOCKWAVE",
            "EXPERIENCE FOCUSED ENERGY", "PEAK PERFORMANCE•", "1 1l oz", "30 ml",
        ]
        self.assertTrue(lg.assess_lines(spec, scaled)["ok"])

    def test_ageaura_label_is_not_a_gummy_count(self):
        spec = load_label("ageaura-pure-nmn-tmg-nad-complex")
        self.assertEqual(lg.expected_gummy_counts(spec), [])


class VerbatimWhitelists(unittest.TestCase):
    def test_new_files_copy_the_ocr_lines_and_nothing_else(self):
        flora = load_label(FLORA)
        gold = load_label(GOLD)
        shock = load_label(SHOCK)
        self.assertEqual(flora["required"], flora["accepted_ocr"])
        self.assertEqual(flora["optional"], [])
        self.assertEqual(flora["required"], FLORA_OCR)
        self.assertEqual(gold["required"], gold["accepted_ocr"])
        self.assertEqual(gold["optional"], [])
        self.assertEqual(gold["required"], GOLD_OCR)
        self.assertEqual(shock["required"], shock["accepted_ocr"])
        self.assertEqual(shock["optional"], [])
        self.assertEqual(shock["required"], SHOCK_OK)
        flora_text = json.dumps(flora)
        for banned in ("SNZ", "15 billion", "Lactobacillus", "1 billion"):
            self.assertNotIn(banned, flora_text)
        for spec in (gold, shock):
            catalog = " ".join(spec["required"] + spec["optional"] + spec["accepted_ocr"])
            self.assertIsNone(lg._MG_DOSE.search(catalog))

    def test_clean_front_lines_pass_the_new_whitelists(self):
        self.assertTrue(lg.assess_lines(load_label(FLORA), FLORA_OCR)["ok"])
        self.assertTrue(lg.assess_lines(load_label(GOLD), GOLD_OCR)["ok"])

    def test_turkesterone_front_lines_and_invented_doses(self):
        spec = load_label(TURK)
        self.assertEqual(spec["required"], spec["accepted_ocr"])
        self.assertEqual(spec["optional"], [])
        self.assertEqual(spec["required"], TURK_OCR)
        catalog = " ".join(spec["required"] + spec["optional"])
        self.assertIsNone(lg._MG_DOSE.search(catalog))
        self.assertNotIn("TURNESTERONE", catalog)
        self.assertIn("TURNESTERONE", spec["source"])
        self.assertIn("not copied", spec["source"])
        self.assertIn("KSM-66?Ashwagandha", spec["source"])
        self.assertNotIn("KSM-66", catalog)
        self.assertNotIn("Ashwagandha", catalog)
        self.assertNotIn("BioPerine", catalog)
        self.assertEqual(lg.expected_capsule_counts(spec), [60])
        self.assertEqual(lg.expected_gummy_counts(spec), [])
        passed = lg.assess_lines(spec, TURK_OCR)
        self.assertTrue(passed["ok"], passed)
        invented = lg.assess_lines(spec, TURK_OCR + ["500 mg"])
        self.assertFalse(invented["ok"])
        self.assertTrue(any("500 mg" in item for item in invented["conflicts"]))
        wrong_count = lg.assess_lines(spec, TURK_OCR + ["90 Capsules"])
        self.assertFalse(wrong_count["ok"])
        self.assertTrue(any("90" in item for item in wrong_count["conflicts"]))
        misread = lg.assess_lines(spec, ["TURNESTERONE", "wellness", "nest"])
        self.assertFalse(misread["ok"])
        self.assertIn("TURKESTERONE", misread["missing"])


class ValidateLandingCaller(unittest.TestCase):
    def test_missing_whitelist_does_not_run_ocr(self):
        spec = {
            "style": "premium",
            "pack_images": ["tmp/pack.webp"],
            "offer": {"href": "https://wellnessnest.co/products/not-a-stocked-handle"},
        }

        def boom(_image, _handle):
            raise AssertionError("gate should not run without a label file")

        errors = lg.whitelist_pack_errors(spec, ROOT, run_gate=boom)
        self.assertEqual(len(errors), 1)
        self.assertIn("FAIL CLOSED", errors[0])
        self.assertIn("not-a-stocked-handle", errors[0])

    def test_claimed_pass_without_images_fails_closed(self):
        spec = {
            "image_note": "label gate PASS (scripts/landing_label_gate.py)",
            "offer": {"href": "https://wellnessnest.co/products/" + FUSI},
        }

        def boom(_image, _handle):
            raise AssertionError("there is no image to OCR")

        errors = lg.whitelist_pack_errors(spec, ROOT, run_gate=boom)
        self.assertTrue(any("pack_images is empty" in err for err in errors))

    def test_gate_failure_is_kept_and_success_is_not(self):
        spec = {
            "pack_images": ["tmp/hero.webp"],
            "offer": {"href": "https://wellnessnest.co/products/" + FUSI},
        }
        failed = lg.whitelist_pack_errors(spec, ROOT, run_gate=lambda _image, _handle: (1, "OCR failed"))
        self.assertEqual(len(failed), 1)
        self.assertIn("label gate FAIL", failed[0])
        self.assertEqual(
            lg.whitelist_pack_errors(spec, ROOT, run_gate=lambda _image, _handle: (0, "ok")),
            [],
        )

    def test_scene_spec_skips_the_gate(self):
        spec = {"style": "premium", "hero": {"summary_html": "A desk, no pack."}}
        self.assertFalse(lg.claims_label_whitelist(spec))
        self.assertEqual(lg.whitelist_pack_errors(spec, ROOT), [])


if __name__ == "__main__":
    unittest.main()

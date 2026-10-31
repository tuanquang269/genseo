"""Pack-image claims follow the cutout, not the label file alone.

A label whitelist without product_refs/<handle>-cutout.png is not a generated
pack shot. Listing pack_images there used to fail the daily lane either way:
the taste rule demanded the list, and the list ran OCR that could not pass.
These tests do not call Shopify, the network, or macOS Vision.
"""
import json
import os
import sys
import tempfile
import unittest

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import landing_label_gate as llg
import landing_pack_claim as claim
import validate_landing as vl

TURK = "turkesterone-advanced-formula"
FUSI = "fusiforce-creatine-gummies"
DAILY = os.path.join(ROOT, "scripts", "run_landing_daily.sh")


def spec(handle, **extra):
    base = {
        "style": "premium",
        "slug": handle + "-listicle-test",
        "offer": {"href": "https://wellnessnest.co/products/" + handle},
    }
    base.update(extra)
    return base


def _png(path, color=(20, 120, 60)):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.new("RGB", (40, 60), color).save(path, "PNG")


def _label(root, handle):
    folder = os.path.join(root, "product_refs")
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, handle + ".label.json"), "w", encoding="utf-8") as fh:
        json.dump({"handle": handle, "required": ["PACK"]}, fh)


class PackListMessageTests(unittest.TestCase):
    def test_turkesterone_without_cutout_does_not_require_pack_images(self):
        self.assertFalse(os.path.isfile(os.path.join(
            ROOT, "product_refs", TURK + "-cutout.png")))
        self.assertTrue(os.path.isfile(os.path.join(
            ROOT, "product_refs", TURK + ".label.json")))
        self.assertIsNone(vl.premium_pack_list_message(spec(TURK)))

    def test_cutout_product_without_pack_images_asks_for_the_gate(self):
        self.assertTrue(os.path.isfile(os.path.join(
            ROOT, "product_refs", FUSI + "-cutout.png")))
        msg = vl.premium_pack_list_message(spec(FUSI))
        self.assertIn("pack_images", msg)

    def test_listed_pack_images_do_not_ask_again(self):
        self.assertIsNone(vl.premium_pack_list_message(spec(
            FUSI, pack_images=["tmp/pack.webp"])))


class NoCutoutOmitTests(unittest.TestCase):
    def test_listing_pack_images_does_not_run_ocr(self):
        called = []

        def boom(image, handle):
            called.append((image, handle))
            raise AssertionError("OCR must not run when the cutout file is missing")

        errors = llg.whitelist_pack_errors(
            spec(TURK, pack_images=["tmp/pack-final-3.webp"], image_note="label gate PASS"),
            ROOT,
            run_gate=boom,
        )
        self.assertEqual(called, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("omit pack_images", errors[0])
        self.assertIn(TURK, errors[0])
        self.assertNotIn("needs macOS Vision", errors[0])


class PrepareSpecTests(unittest.TestCase):
    def test_no_cutout_drops_the_claim_and_uses_the_curated_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            _label(tmp, TURK)
            _png(os.path.join(tmp, "product_refs", TURK + ".png"))
            page = spec(
                TURK,
                pack_images=["tmp/pack-final-3.webp"],
                hero={"image": "tmp/pack-final-3.webp"},
                image_note="label gate PASS via landing_label_gate.py",
            )
            notes = claim.prepare_spec(page, tmp, run_gate=lambda *_a: (_ for _ in ()).throw(AssertionError("gate")))
            self.assertTrue(any("omitted pack_images" in note for note in notes))
            self.assertNotIn("pack_images", page)
            self.assertNotIn("label gate", json.dumps(page).lower())
            self.assertNotIn("landing_label_gate", json.dumps(page))
            self.assertFalse(llg.claims_label_whitelist(page))
            self.assertTrue(page["hero"]["image"].endswith("real-pack.webp"))
            webp = os.path.join(tmp, page["hero"]["image"])
            self.assertTrue(os.path.isfile(webp))
            self.assertLess(os.path.getsize(webp), 80 * 1024)
            self.assertEqual(claim.prepare_spec(page, tmp), [])

    def test_failed_cutout_shot_is_replaced_and_a_pass_is_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            _label(tmp, FUSI)
            cutout = os.path.join(tmp, "product_refs", FUSI + "-cutout.png")
            _png(cutout, color=(10, 40, 90))
            page = spec(
                FUSI,
                pack_images=["tmp/bad.webp", "tmp/good.webp"],
                hero={"image": "tmp/bad.webp"},
            )

            def gate(image, handle):
                self.assertEqual(handle, FUSI)
                if image == "tmp/bad.webp":
                    return 1, "OCR failed"
                return 0, "ok"

            notes = claim.prepare_spec(page, tmp, run_gate=gate)
            self.assertEqual(len(notes), 1)
            self.assertIn("replaced 1 pack shot", notes[0])
            self.assertEqual(page["pack_images"], [
                "tmp_images/landing-%s-listicle-test/cutout-pack.webp" % FUSI,
                "tmp/good.webp",
            ])
            self.assertEqual(page["hero"]["image"], page["pack_images"][0])
            webp = os.path.join(tmp, page["pack_images"][0])
            self.assertLess(os.path.getsize(webp), 80 * 1024)
            self.assertTrue(llg.claims_label_whitelist(page))

    def test_passing_cutout_shots_stay(self):
        with tempfile.TemporaryDirectory() as tmp:
            _label(tmp, FUSI)
            _png(os.path.join(tmp, "product_refs", FUSI + "-cutout.png"))
            page = spec(FUSI, pack_images=["tmp/good.webp"])
            notes = claim.prepare_spec(page, tmp, run_gate=lambda *_a: (0, "ok"))
            self.assertEqual(notes, [])
            self.assertEqual(page["pack_images"], ["tmp/good.webp"])


class WrapperDoesNotPublishTests(unittest.TestCase):
    def test_daily_wrapper_prepares_claims_and_does_not_call_the_publisher(self):
        with open(DAILY, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("scripts/landing_pack_claim.py prepare", text)
        code = "\n".join(
            line for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        self.assertNotIn("landing_publisher.py", code)
        self.assertNotIn("--live", code)
        self.assertNotIn("--install-template", code)


if __name__ == "__main__":
    unittest.main()

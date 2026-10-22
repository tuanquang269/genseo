"""Premium pack_images is required only when a cutout exists.

Turkesterone has a label whitelist and no cutout. The real PDP photo is the
pack shot, and the spec must not claim a label-gate pass. These tests do not
call the network or macOS Vision.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import validate_landing as vl


def spec(handle, **extra):
    base = {
        "style": "premium",
        "offer": {"href": "https://wellnessnest.co/products/" + handle},
    }
    base.update(extra)
    return base


class PackListingTests(unittest.TestCase):
    def test_turkesterone_without_cutout_does_not_require_pack_images(self):
        self.assertFalse(os.path.isfile(os.path.join(
            ROOT, "product_refs", "turkesterone-advanced-formula-cutout.png")))
        self.assertIsNone(vl.premium_pack_list_message(spec("turkesterone-advanced-formula")))

    def test_cutout_product_without_pack_images_asks_for_the_gate(self):
        self.assertTrue(os.path.isfile(os.path.join(
            ROOT, "product_refs", "fusiforce-creatine-gummies-cutout.png")))
        msg = vl.premium_pack_list_message(spec("fusiforce-creatine-gummies"))
        self.assertIn("pack_images", msg)

    def test_listed_pack_images_do_not_ask_again(self):
        self.assertIsNone(vl.premium_pack_list_message(spec(
            "fusiforce-creatine-gummies", pack_images=["tmp/pack.webp"])))


if __name__ == "__main__":
    unittest.main()

"""Wellness Nest blog byline is Mike Moretti (Kevin 2026-10-21).

Reads repo-root roster.json. scripts/genseo_roster.py still loads the Mac path,
which is empty on a cloud VM, so this test does not go through that loader.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import genseo_roster
import validate_article as va

ROSTER_FILE = os.path.join(ROOT, "roster.json")


class MikeMorettiByline(unittest.TestCase):
    def setUp(self):
        with open(ROSTER_FILE, encoding="utf-8") as fh:
            self.roster = json.load(fh)

    def test_mike_is_first_and_the_bio_is_only_the_role(self):
        self.assertEqual(next(iter(self.roster)), "mike-moretti")
        mike = self.roster["mike-moretti"]
        self.assertEqual(mike["name"], genseo_roster.DEFAULT_BLOG_NAME)
        self.assertEqual(mike["bio"], genseo_roster.DEFAULT_BLOG_ROLE)
        self.assertEqual(mike["bio"], "Co-founder, Wellness Nest")
        self.assertIn("TODO", mike["headshot"])
        self.assertIn("TODO", mike["page"])
        self.assertNotIn("Dr.", mike["bio"])
        self.assertIn("dr-marcus-hale", self.roster)
        self.assertTrue(self.roster["dr-marcus-hale"]["bio"].startswith("Dr. Marcus Hale"))

    def test_blog_gate_rejects_hale_and_accepts_mike(self):
        mike = (
            "### About the Author\n"
            "[Mike Moretti](/pages/mike-moretti) — Co-founder, Wellness Nest"
        )
        self.assertEqual(va.blog_byline_fails(mike), [])
        hale = (
            "### About the Author\n"
            "[Dr. Marcus Hale](/pages/dr-marcus-hale) — Dr. Marcus Hale is the resident health researcher."
        )
        bad = va.blog_byline_fails(hale)
        self.assertTrue(any("Dr. Marcus Hale" in item for item in bad), bad)
        self.assertTrue(any("/pages/mike-moretti" in item for item in bad), bad)
        self.assertTrue(va.blog_byline_fails("The byline is Dr. Marcus Hale."))
        self.assertTrue(va.blog_byline_fails("### About the Author\nWellness Nest Editorial Team"))

    def test_publisher_fallback_is_still_the_editorial_team(self):
        # Do not import shopify_publisher here: that import loads the Mac Shopify token.
        path = os.path.join(ROOT, "scripts", "shopify_publisher.py")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn('FALLBACK_AUTHOR = "Wellness Nest Editorial Team"', text)
        self.assertNotIn("Mike Moretti", text)


if __name__ == "__main__":
    unittest.main()

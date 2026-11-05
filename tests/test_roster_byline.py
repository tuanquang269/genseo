"""Mike Moretti is the blog byline. A Dr. Marcus Hale blog byline fails.

No Shopify, no network. The author page is not created here.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import genseo_roster
import validate_article as va
import build_rich_tickets as brt

MIKE_BIO = "Mike Moretti is a co-founder of Wellness Nest and the brand's public face."
HALE_BIO = ("Dr. Marcus Hale is the resident health researcher behind Wellness Nest's editorial team, "
            "translating peer-reviewed sports-nutrition and longevity research into practical daily guidance "
            "for US readers.")


def about(name, handle, bio, extra=""):
    return (f"### About the Author\n[{name}](/pages/{handle}) — {bio}{extra}")


class RosterEntry(unittest.TestCase):
    def test_checkout_roster_is_the_file_next_to_the_scripts(self):
        expected = os.path.join(ROOT, "roster.json")
        self.assertTrue(os.path.samefile(genseo_roster.roster_path(), expected))
        self.assertEqual(genseo_roster.ROSTER_PATH, genseo_roster.roster_path())

    def test_mike_and_hale_are_both_on_the_roster(self):
        self.assertEqual(set(genseo_roster.ROSTER), {"mike-moretti", "dr-marcus-hale"})
        self.assertEqual(genseo_roster.PAGES, {"/pages/mike-moretti", "/pages/dr-marcus-hale"})

    def test_mike_entry_is_facts_only(self):
        mike = genseo_roster.ROSTER["mike-moretti"]
        self.assertEqual(mike["name"], "Mike Moretti")
        self.assertEqual(mike["role"], "Co-founder, Wellness Nest")
        self.assertEqual(mike["bio"], MIKE_BIO)
        self.assertEqual(mike["page"], "/pages/mike-moretti")
        self.assertIsNone(mike["headshot"])
        self.assertIn("PLACEHOLDER", mike["headshot_note"])
        self.assertEqual(mike["default_for"], ["blog"])
        low = mike["bio"].lower()
        for banned in ("dr.", " md", "phd", "cissn", "doctor", "reviewer", "year", "jiu", "stroke", "degree"):
            self.assertNotIn(banned, low)

    def test_hale_bio_is_unchanged_and_he_is_not_the_blog_default(self):
        hale = genseo_roster.ROSTER["dr-marcus-hale"]
        self.assertEqual(hale["name"], "Dr. Marcus Hale")
        self.assertEqual(hale["bio"], HALE_BIO)
        self.assertNotIn("blog", hale.get("default_for") or [])

    def test_defaults(self):
        handle, entry = genseo_roster.blog_default()
        self.assertEqual(handle, "mike-moretti")
        self.assertEqual(entry["name"], "Mike Moretti")
        handle, entry = genseo_roster.landing_default()
        self.assertEqual(handle, "dr-marcus-hale")
        self.assertEqual(entry["name"], "Dr. Marcus Hale")

    def test_page_mismatch_and_two_blog_defaults_fail(self):
        with self.assertRaises(ValueError):
            genseo_roster._validate({
                "mike-moretti": {"name": "Mike Moretti", "bio": "x" * 60, "page": "/pages/someone-else"},
            })
        saved = dict(genseo_roster.ROSTER)
        try:
            genseo_roster.ROSTER["dr-marcus-hale"] = dict(saved["dr-marcus-hale"], default_for=["blog"])
            with self.assertRaises(ValueError):
                genseo_roster.blog_default()
        finally:
            genseo_roster.ROSTER.clear()
            genseo_roster.ROSTER.update(saved)


class AuthorGate(unittest.TestCase):
    def test_mike_verbatim_bio_passes_and_a_medical_claim_fails(self):
        mike = about("Mike Moretti", "mike-moretti", MIKE_BIO)
        self.assertEqual(va._author_fails(mike), [])
        html = mike.replace("### About the Author", "<h3>About the Author</h3>")
        self.assertEqual(va._author_fails(html), [])
        reviewer = about("Mike Moretti", "mike-moretti", MIKE_BIO + " He is a medical reviewer.")
        self.assertTrue(any("medical reviewer" in f for f in va._author_fails(reviewer)))
        doctor = about("Dr. Mike Moretti", "mike-moretti", "Dr. " + MIKE_BIO)
        self.assertTrue(va._author_fails(doctor))
        years = about("Mike Moretti", "mike-moretti", "Mike Moretti is a Strength Coach with over 8 years of experience.")
        self.assertTrue(va._author_fails(years))

    def test_hale_blog_byline_fails(self):
        hale = about("Dr. Marcus Hale", "dr-marcus-hale", HALE_BIO)
        fails = va._author_fails(hale)
        self.assertTrue(any("not the blog byline" in f for f in fails), fails)

    def test_swapped_bio_fails(self):
        swapped = about("Mike Moretti", "mike-moretti", HALE_BIO)
        self.assertTrue(any("approved sentence" in f for f in va._author_fails(swapped)))
        swapped = about("Dr. Marcus Hale", "dr-marcus-hale", MIKE_BIO)
        self.assertTrue(any("approved sentence" in f for f in va._author_fails(swapped)))

    def test_null_headshot_rejects_an_invented_photo(self):
        mike = about("Mike Moretti", "mike-moretti", MIKE_BIO, extra="\n![Mike Moretti](tmp_images/mike.png)")
        self.assertTrue(any("headshot" in f for f in va._author_fails(mike)))

    def test_placeholder_byline_still_fails(self):
        fake = "### About the Author\n[Author Four](/pages/author-four) is a writer."
        self.assertTrue(any("Author Four" in f for f in va._author_fails(fake)))

    def test_self_check_covers_both_authors(self):
        va.test_author_gate()

    def test_rich_tickets_use_the_blog_default(self):
        self.assertEqual(brt.AUTHORS["founder"], "Mike Moretti (/pages/mike-moretti)")
        self.assertTrue(all(v.startswith("Mike Moretti ") for v in brt.AUTHORS.values()))

    def test_role_line_alone_is_not_the_approved_bio(self):
        role_only = about("Mike Moretti", "mike-moretti", "Co-founder, Wellness Nest")
        self.assertTrue(any("approved sentence" in f for f in va._author_fails(role_only)))


class LandingPromptsStayHale(unittest.TestCase):
    def test_landing_prompts_name_hale(self):
        runner = os.path.join(ROOT, "scripts", "run_landing_headless.sh")
        skill = os.path.join(ROOT, "skills", "genseo-landing-pages", "SKILL.md")
        with open(runner, encoding="utf-8") as fh:
            runner_text = fh.read()
        with open(skill, encoding="utf-8") as fh:
            skill_text = fh.read()
        self.assertIn("Byline: Dr. Marcus Hale", runner_text)
        self.assertNotIn("Byline: Mike Moretti", runner_text)
        self.assertNotIn("Do not byline Dr. Marcus Hale", runner_text)
        self.assertIn("This landing lane stays Dr. Marcus Hale", skill_text)
        self.assertIn("Dr. Marcus Hale, fresh", skill_text)
        self.assertNotIn("Mike Moretti, fresh", skill_text)
        handle, entry = genseo_roster.landing_default()
        self.assertEqual(handle, "dr-marcus-hale")
        self.assertEqual(entry["name"], "Dr. Marcus Hale")

    def test_blog_runner_copies_the_roster_bio(self):
        path = os.path.join(ROOT, "scripts", "run_ticket_headless.sh")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("copy his bio from roster.json verbatim", text)
        self.assertIn("Landing pages stay on Hale", text)
        self.assertNotIn("Copy that role from roster.json verbatim", text)


if __name__ == "__main__":
    unittest.main()

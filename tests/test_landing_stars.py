"""Star row for listicle trust and offer ratings.

Five filled stars must keep the markup every existing spec rendered before
the optional `stars` field existed. A lower count fills the rest grey.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import landing_clone as lc  # noqa: E402


class Stars(unittest.TestCase):
    def test_five_stars_match_the_previous_all_green_markup(self):
        previous = (
            '<span class="gslp-stars" aria-label="5 out of 5 stars">'
            + lc.STAR_G * 5
            + "</span>"
        )
        self.assertEqual(lc.gstars(), previous)
        self.assertEqual(lc.gstars(5), previous)

    def test_four_stars_leave_one_grey(self):
        html = lc.gstars(4)
        self.assertIn('aria-label="4 out of 5 stars"', html)
        self.assertEqual(html.count('fill="#2f8a3b"'), 4)
        self.assertEqual(html.count('fill="#c5c9ce"'), 1)


if __name__ == "__main__":
    unittest.main()

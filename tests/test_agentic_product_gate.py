"""The primary article product must join its exact Catalog title to its PDP."""
import os
import sys
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import validate_article as va

TITLE = "AgeAura Pure NMN + TMG NAD Complex"
URL = "https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex"


def page(text=TITLE):
    return f'<p>{text}</p><a href="{URL}">Buy now</a>'


class AgenticProductGateTests(unittest.TestCase):
    def test_exact_catalog_title_and_pdp_link_pass(self):
        with mock.patch.object(va, "_catalog_product_title", return_value=TITLE) as fetch:
            self.assertEqual(va._agentic_catalog_issues(page()), [])
        fetch.assert_called_once_with("ageaura-pure-nmn-tmg-nad-complex")

    def test_short_brand_name_does_not_pass(self):
        with mock.patch.object(va, "_catalog_product_title", return_value=TITLE):
            fails = va._agentic_catalog_issues(page("AgeAura NMN"))
        self.assertTrue(any("exact Catalog title" in fail for fail in fails), fails)
        self.assertIn(TITLE, fails[0])

    def test_title_in_a_link_or_comment_is_not_visible_article_text(self):
        html = page("Read our NMN guide")
        html += f'<!-- {TITLE} --><img alt="{TITLE}" src="product.webp">'
        with mock.patch.object(va, "_catalog_product_title", return_value=TITLE):
            fails = va._agentic_catalog_issues(html)
        self.assertTrue(fails)

    def test_html_markup_and_entities_do_not_break_exact_title_matching(self):
        html = page("AgeAura Pure NMN + <strong>TMG</strong>&nbsp;NAD Complex")
        with mock.patch.object(va, "_catalog_product_title", return_value=TITLE):
            self.assertEqual(va._agentic_catalog_issues(html), [])

    def test_only_the_first_linked_product_is_the_primary_product(self):
        html = page() + '<a href="https://wellnessnest.co/products/fusiforce-creatine-gummies">FusiForce</a>'
        with mock.patch.object(va, "_catalog_product_title", return_value=TITLE) as fetch:
            self.assertEqual(va._agentic_catalog_issues(html), [])
        fetch.assert_called_once_with("ageaura-pure-nmn-tmg-nad-complex")

    def test_catalog_read_failure_blocks_instead_of_guessing(self):
        with mock.patch.object(va, "_catalog_product_title", side_effect=OSError("offline")):
            fails = va._agentic_catalog_issues(page())
        self.assertTrue(any("could not verify" in fail for fail in fails), fails)


if __name__ == "__main__":
    unittest.main()

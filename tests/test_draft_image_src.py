import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import validate_article as va

CDN = ("https://cdn.shopify.com/s/files/1/0810/1563/6283/files/"
       "inline-1-label-check_17c43a1f-db36-4c71-b1aa-74add3168827.webp?v=1792636948")

class DraftImageSrc(unittest.TestCase):
    def test_cdn_image_becomes_img_and_the_real_link_stays_a_link(self):
        html = va.draft_struct_html(
            "See [FDA](https://www.fda.gov/food) and ![closet pouch](%s)." % CDN)
        self.assertIn('<img alt="closet pouch" src="%s">' % CDN, html)
        self.assertIn('<a href="https://www.fda.gov/food">FDA</a>', html)
        self.assertNotIn("!<a", html)

    def test_local_path_becomes_img(self):
        src = "/Users/kevinkreative/genseo/run-assets/shilajit-for-seniors/hero.webp"
        html = va.draft_struct_html("![canister](%s)" % src)
        self.assertIn('<img alt="canister" src="%s">' % src, html)
        self.assertEqual(va.remote_image_fail(src), "")

    def test_remote_src_fails_for_our_cdn_and_for_any_other_host(self):
        own = va.remote_image_fail(CDN)
        other = va.remote_image_fail("https://example.com/pack.png")
        self.assertIn("remote URL", own)
        self.assertIn("/Users", own)
        self.assertIn("remote URL", other)

    def test_empty_alt_cdn_image_is_still_an_img_and_still_remote(self):
        html = va.draft_struct_html("![](%s)" % CDN)
        self.assertIn("<img", html)
        self.assertIn("remote URL", va.remote_image_fail(CDN))

    def test_relative_and_data_are_not_this_helper(self):
        # Relative paths stay a separate publisher hole. data: stays skipped.
        self.assertEqual(va.remote_image_fail("img/pouch.webp"), "")
        self.assertEqual(va.remote_image_fail("data:image/webp;base64,AAAA"), "")

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

    def test_data_uri_does_not_fill_the_image_floor(self):
        # Four data: images used to count toward the floor and skip the file check.
        data = "data:image/webp;base64,AAAA"
        raw = "\n".join("![panel %d](%s)" % (i, data) for i in range(4))
        html = va.draft_struct_html(raw)
        self.assertEqual(len(va.visible_body_images(html, md_draft=True)), 0)
        fails = va.draft_image_file_fails(html, "/private/tmp")
        self.assertEqual(len(fails), 4)
        for item in fails:
            self.assertIn("data URI", item)
            self.assertNotIn("no such file", item)
        padded = va.remote_image_fail(" data:image/webp;base64,AAAA")
        self.assertIn("data URI", padded)
        self.assertNotIn("no such file", padded)

    def test_unquoted_https_src_fails(self):
        raw = ("A US reader checks the pouch label before buying.\n"
               "<img alt=pack src=https://cdn.shopify.com/s/files/a.webp>")
        html = va.draft_struct_html(raw)
        tags = va._IMG_TAG_RE.findall(html)
        self.assertEqual(len(tags), 1)
        self.assertNotIn('src="https://cdn.shopify.com/s/files/a.webp"', tags[0])
        self.assertEqual(
            va.img_tag_src(tags[0]),
            "https://cdn.shopify.com/s/files/a.webp")
        self.assertEqual(len(va.visible_body_images(html, md_draft=True)), 0)
        fails = va.draft_image_file_fails(html, "/private/tmp")
        self.assertEqual(len(fails), 1)
        self.assertIn("remote URL", fails[0])
        self.assertIn("https://cdn.shopify.com/s/files/a.webp", fails[0])
        self.assertNotIn("no such file", fails[0])

    def test_existing_relative_image_fails(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            name = "pouch.webp"
            path = os.path.join(folder, name)
            with open(path, "wb") as fh:
                fh.write(b"RIFF")
            self.assertTrue(os.path.exists(path))
            html = va.draft_struct_html("![pouch](%s)" % name)
            self.assertEqual(len(va.visible_body_images(html, md_draft=True)), 0)
            fails = va.draft_image_file_fails(html, folder)
            self.assertEqual(len(fails), 1)
            self.assertNotIn("no such file", fails[0])
            self.assertIn("/Users", fails[0])
            self.assertIn("/private", fails[0])
        missing = "/Users/kevinkreative/genseo/run-assets/does-not-exist-t24.webp"
        disk = va.draft_image_file_fails(
            '<img alt="canister" src="%s">' % missing, "/private/tmp")
        self.assertEqual(len(disk), 1)
        self.assertIn("no such file", disk[0])
        self.assertNotIn("not a publisher-local", disk[0])

    def test_html_draft_rejects_remote_image(self):
        html = '<img src="https://cdn.shopify.com/s/files/a.webp">'
        for path in ("/tmp/live-article.html", "/tmp/draft.md"):
            fails = va.draft_image_gate(path, html)
            self.assertEqual(len(fails), 1, path)
            self.assertIn("remote URL", fails[0], path)
            self.assertNotIn("no such file", fails[0], path)
        import inspect
        src = inspect.getsource(va.main)
        self.assertIn("draft_image_gate(path, html)", src)
        self.assertNotIn("md_draft and remote_image_fail", src)

    def test_protocol_relative_and_leading_space_are_remote_urls(self):
        cases = [
            "//cdn.shopify.com/s/files/a.webp",
            " https://cdn.shopify.com/s/files/a.webp",
            "\thttps://cdn.example/a.png",
            " //cdn.shopify.com/s/files/a.webp",
            "  HTTP://cdn.shopify.com/a.webp",
        ]
        for src in cases:
            msg = va.remote_image_fail(src)
            self.assertIn("remote URL", msg, src)
            self.assertNotIn("no such file", msg, src)
            html = '<img alt="pouch" src="%s">' % src
            fails = va.draft_image_file_fails(html, "/private/tmp/missing-base")
            self.assertEqual(len(fails), 1, src)
            self.assertIn("remote URL", fails[0], src)
            self.assertNotIn("no such file", fails[0], src)
            md = va.draft_struct_html("![pouch](%s)" % src)
            fails_md = va.draft_image_file_fails(md, "/private/tmp/missing-base")
            self.assertEqual(len(fails_md), 1, src)
            self.assertIn("remote URL", fails_md[0], src)
            self.assertNotIn("no such file", fails_md[0], src)

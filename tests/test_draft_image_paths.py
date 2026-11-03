"""Draft image paths resolve inside the checkout that holds the markdown.

The committed coffee draft uses assets/<slug>/<file> beside the markdown.
validate_article.py --draft joins that to the draft's directory. The publisher
must open the same path, including from a worktree that is not ~/genseo.
"""
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import draft_image_paths as dip

IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
MAIN_CHECKOUT = "/Users/kevinkreative/genseo/run-assets/"


def _validate_join(src, draft_path):
    """The two lines in validate_article.py --draft that turn a src into a file."""
    if re.match(r"(?i)https?://|data:", src):
        return None
    base = os.path.dirname(os.path.abspath(draft_path))
    return src if os.path.isabs(src) else os.path.join(base, src)


class DraftImagePaths(unittest.TestCase):
    def test_relative_join_matches_the_gate_and_stays_by_the_draft(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = os.path.join(tmp, "article.md")
            folder = os.path.join(tmp, "assets", "slug")
            os.makedirs(folder)
            image = os.path.join(folder, "pack.webp")
            with open(image, "wb") as fh:
                fh.write(b"jpeg-bytes")
            with open(draft, "w", encoding="utf-8") as fh:
                fh.write("![pack](assets/slug/pack.webp)\n")
            token = "assets/slug/pack.webp"
            self.assertEqual(dip.disk_path(token, draft), _validate_join(token, draft))
            self.assertTrue(os.path.isfile(dip.disk_path(token, draft)))
            self.assertIsNone(dip.disk_path(token, None))

    def test_absolute_users_and_private_stay_absolute(self):
        self.assertEqual(dip.disk_path("/Users/example/a.webp"), "/Users/example/a.webp")
        self.assertEqual(dip.disk_path("/private/tmp/a.webp"), "/private/tmp/a.webp")
        self.assertIsNone(dip.disk_path("/blogs/news/a.webp"))
        self.assertIsNone(dip.disk_path("/cdn/shop/a.webp"))
        self.assertIsNone(dip.disk_path("https://cdn.shopify.com/s/files/a.webp"))
        self.assertIsNone(dip.disk_path("data:image/png;base64,aaaa"))

    def test_committed_drafts_do_not_point_at_the_main_checkout(self):
        drafts = os.path.join(ROOT, "published_drafts")
        seen = 0
        for name in os.listdir(drafts):
            if not name.endswith(".md"):
                continue
            path = os.path.join(drafts, name)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            self.assertNotIn(MAIN_CHECKOUT, text, name)
            for src in IMG.findall(text):
                if re.match(r"(?i)https?://|data:", src):
                    continue
                disk = _validate_join(src, path)
                self.assertTrue(os.path.isfile(disk), f"{name}: {src} → {disk}")
                self.assertEqual(dip.disk_path(src, path), disk)
                seen += 1
        self.assertGreaterEqual(seen, 4)

    def test_publisher_opens_the_draft_relative_path(self):
        path = os.path.join(ROOT, "scripts", "shopify_publisher.py")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("import draft_image_paths", text)
        self.assertEqual(text.count("persona_credits_html(md_text, file_path)"), 2)
        self.assertIn("draft_path=file_path", text)
        self.assertIn("disk = draft_image_paths.disk_path(local_path, draft_path)", text)


if __name__ == "__main__":
    unittest.main()

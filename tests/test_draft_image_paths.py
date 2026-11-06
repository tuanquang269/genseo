"""Draft image paths resolve inside the checkout that holds the markdown.

The committed coffee draft uses assets/<slug>/<file> beside the markdown.
validate_article.py --draft joins that to the draft's directory. The publisher
must open the same path, including from a worktree that is not ~/genseo.

The publisher join is jailed: realpath must stay inside the draft directory.
`../`, a symlink to the outside, and an absolute path outside that directory
are refused. A normal assets/<slug>/<file> path still opens.
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
        self.assertNotIn("disk_path(path, draft_path) or path", text)
        self.assertIn("except draft_image_paths.DraftImagePathError", text)
        self.assertIn("def _refuse_escaped_image", text)

    def _draft(self, tmp):
        draft_dir = os.path.join(tmp, "published_drafts")
        os.makedirs(draft_dir)
        draft = os.path.join(draft_dir, "article.md")
        with open(draft, "w", encoding="utf-8") as fh:
            fh.write("# title\n")
        return draft

    def _assert_refused(self, token, draft):
        leaky = _validate_join(token, draft)
        with self.assertRaises(dip.DraftImagePathError) as ctx:
            dip.disk_path(token, draft)
        message = str(ctx.exception)
        self.assertIn("refusing", message.lower())
        self.assertIn("outside", message.lower())
        self.assertIn(repr(token), message)
        self.assertIn("draft folder", message)
        return leaky

    def test_dotdot_outside_the_draft_folder_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = self._draft(tmp)
            outside = os.path.join(tmp, "secret.webp")
            with open(outside, "wb") as fh:
                fh.write(b"secret")
            evil_dir = os.path.dirname(draft) + "-evil"
            os.makedirs(evil_dir)
            evil = os.path.join(evil_dir, "secret.webp")
            with open(evil, "wb") as fh:
                fh.write(b"secret")
            evil_name = os.path.basename(evil_dir)
            root = os.path.realpath(os.path.dirname(draft))
            for token in (
                "../secret.webp",
                "assets/../../secret.webp",
                f"../{evil_name}/secret.webp",
            ):
                leaky = self._assert_refused(token, draft)
                resolved = os.path.realpath(leaky)
                # realpath, not the raw join: `assets/../../` is the outside file
                # even when the missing `assets` directory makes the raw path fail isfile.
                self.assertTrue(os.path.isfile(resolved), token)
                self.assertNotEqual(os.path.commonpath([root, resolved]), root)
            # A string-prefix jail would treat "<draft>-evil" as inside "<draft>".
            sibling = os.path.realpath(evil)
            self.assertTrue(sibling.startswith(root))
            self.assertFalse(sibling.startswith(root + os.sep))
            self.assertNotEqual(sibling, root)

    def test_symlink_escape_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = self._draft(tmp)
            inside = os.path.join(os.path.dirname(draft), "assets", "slug")
            os.makedirs(inside)
            outside_dir = os.path.join(tmp, "outside")
            os.makedirs(outside_dir)
            secret = os.path.join(outside_dir, "secret.webp")
            with open(secret, "wb") as fh:
                fh.write(b"secret")
            link = os.path.join(inside, "pack.webp")
            os.symlink(secret, link)
            leaky = self._assert_refused("assets/slug/pack.webp", draft)
            self.assertTrue(os.path.isfile(leaky))
            self.assertTrue(os.path.islink(leaky))
            # Absolute path of the same symlink is the same escape.
            self._assert_refused(os.path.abspath(link), draft)
            os.symlink(outside_dir, os.path.join(os.path.dirname(draft), "escape"))
            leaky_dir = self._assert_refused("escape/secret.webp", draft)
            self.assertTrue(os.path.isfile(leaky_dir))

    def test_absolute_path_outside_the_draft_folder_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = self._draft(tmp)
            folder = os.path.join(os.path.dirname(draft), "assets", "slug")
            os.makedirs(folder)
            image = os.path.join(folder, "pack.webp")
            with open(image, "wb") as fh:
                fh.write(b"jpeg-bytes")
            outside = os.path.realpath(os.path.join(tmp, "secret.webp"))
            with open(outside, "wb") as fh:
                fh.write(b"secret")
            for token in (
                outside,
                "/etc/passwd",
                "/Users/example/outside.webp",
                "/private/tmp/genseo-t33-outside.webp",
            ):
                self._assert_refused(token, draft)
            # An absolute path that realpath keeps inside the draft tree still opens.
            inside_abs = os.path.abspath(image)
            self.assertEqual(dip.disk_path(inside_abs, draft), inside_abs)
            self.assertTrue(os.path.isfile(dip.disk_path(inside_abs, draft)))
            # Without a draft file, the legacy absolute contract is unchanged.
            self.assertEqual(dip.disk_path("/Users/example/a.webp"), "/Users/example/a.webp")
            self.assertEqual(dip.disk_path("/private/tmp/a.webp"), "/private/tmp/a.webp")

    def test_normal_assets_slug_file_still_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = self._draft(tmp)
            folder = os.path.join(os.path.dirname(draft), "assets", "slug")
            os.makedirs(folder)
            image = os.path.join(folder, "pack.webp")
            with open(image, "wb") as fh:
                fh.write(b"jpeg-bytes")
            token = "assets/slug/pack.webp"
            resolved = dip.disk_path(token, draft)
            self.assertEqual(resolved, _validate_join(token, draft))
            self.assertTrue(os.path.isfile(resolved))
            root = os.path.realpath(os.path.dirname(draft))
            self.assertEqual(os.path.commonpath([root, os.path.realpath(resolved)]), root)
            # `..` that normalizes back inside the tree is not an escape.
            nested = "assets/slug/../slug/pack.webp"
            nested_path = dip.disk_path(nested, draft)
            self.assertTrue(os.path.isfile(nested_path))
            self.assertEqual(os.path.commonpath([root, os.path.realpath(nested_path)]), root)
            # A symlink whose target stays inside the draft folder still opens.
            alias = os.path.join(folder, "alias.webp")
            os.symlink(image, alias)
            alias_path = dip.disk_path("assets/slug/alias.webp", draft)
            self.assertTrue(os.path.isfile(alias_path))
            self.assertEqual(os.path.realpath(alias_path), os.path.realpath(image))


if __name__ == "__main__":
    unittest.main()

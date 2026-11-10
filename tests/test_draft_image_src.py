import os
import sys
import tempfile
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

    def test_assets_slug_file_inside_draft_tree_is_accepted(self):
        # main's coffee article and the localized drafts use this form.
        # The publisher joins it to the draft directory and uploads the file.
        with tempfile.TemporaryDirectory() as folder:
            slug = "nmn-and-coffee-us-2026"
            image_dir = os.path.join(folder, "assets", slug)
            os.makedirs(image_dir)
            hero = os.path.join(image_dir, "hero.webp")
            with open(hero, "wb") as fh:
                fh.write(b"RIFF-hero")
            empty = os.path.join(image_dir, "empty.webp")
            with open(empty, "wb") as fh:
                fh.write(b"")
            quarantined = os.path.join(image_dir, "QC-FAILED-hero.webp")
            with open(quarantined, "wb") as fh:
                fh.write(b"RIFF-bad")
            src = "assets/%s/hero.webp" % slug
            draft = os.path.join(folder, "article.md")
            with open(draft, "w", encoding="utf-8") as fh:
                fh.write("![bottle](%s)\n" % src)
            html = va.draft_struct_html("![bottle](%s)" % src)
            self.assertIn('src="%s"' % src, html)
            self.assertEqual(va.remote_image_fail(src, folder), "")
            self.assertEqual(va.draft_image_file_fails(html, folder), [])
            self.assertEqual(va.draft_image_gate(draft, html), [])
            self.assertEqual(len(va.visible_body_images(html, True, folder)), 1)
            missing = "assets/%s/missing.webp" % slug
            missing_html = '<img alt="bottle" src="%s">' % missing
            missing_fails = va.draft_image_file_fails(missing_html, folder)
            self.assertEqual(len(missing_fails), 1)
            self.assertIn("no such file", missing_fails[0])
            self.assertNotIn("not a publisher-local", missing_fails[0])
            self.assertNotIn("outside", missing_fails[0])
            empty_fails = va.draft_image_file_fails(
                '<img alt="bottle" src="assets/%s/empty.webp">' % slug, folder)
            self.assertEqual(len(empty_fails), 1)
            self.assertIn("0 bytes", empty_fails[0])
            quarantine_fails = va.draft_image_file_fails(
                '<img alt="bottle" src="assets/%s/QC-FAILED-hero.webp">' % slug, folder)
            self.assertEqual(len(quarantine_fails), 1)
            self.assertIn("quarantined", quarantine_fails[0])
        coffee = os.path.join(ROOT, "published_drafts", "nmn-and-coffee-us-2026.md")
        if os.path.isfile(coffee):
            base = os.path.dirname(coffee)
            with open(coffee, encoding="utf-8") as fh:
                text = fh.read()
            coffee_html = va.draft_struct_html(text)
            self.assertEqual(va.draft_image_file_fails(coffee_html, base), [])
            self.assertEqual(len(va.visible_body_images(coffee_html, True, base)), 4)

    def test_relative_image_resolving_outside_draft_tree_is_rejected(self):
        with tempfile.TemporaryDirectory() as parent:
            folder = os.path.join(parent, "published_drafts")
            outside = os.path.join(parent, "secret.webp")
            os.makedirs(os.path.join(folder, "assets", "slug"))
            with open(outside, "wb") as fh:
                fh.write(b"secret")
            hero = os.path.join(folder, "assets", "slug", "hero.webp")
            with open(hero, "wb") as fh:
                fh.write(b"RIFF-hero")
            link = os.path.join(folder, "assets", "slug", "escape.webp")
            os.symlink("/etc/passwd", link)
            self.assertTrue(os.path.isfile(link))
            outside_dir = os.path.join(parent, "elsewhere")
            os.makedirs(outside_dir)
            with open(os.path.join(outside_dir, "hero.webp"), "wb") as fh:
                fh.write(b"RIFF-out")
            linked_slug = os.path.join(folder, "assets", "linked")
            os.symlink(outside_dir, linked_slug)
            # Lexical assets/<slug>/<file>, realpath in the draft folder but
            # outside the assets directory.
            sibling = os.path.join(folder, "secret.webp")
            with open(sibling, "wb") as fh:
                fh.write(b"secret")
            os.symlink(sibling, os.path.join(folder, "assets", "slug", "sib.webp"))
            alias = os.path.join(folder, "assets", "slug", "alias.webp")
            os.symlink(hero, alias)
            cases = [
                "assets/slug/escape.webp",
                "assets/linked/hero.webp",
                "assets/slug/sib.webp",
                "../secret.webp",
                # one more .. than assets/slug: normpath leaves published_drafts
                "assets/slug/../../../secret.webp",
            ]
            for src in cases:
                html = '<img alt="pack" src="%s">' % src
                fails = va.draft_image_file_fails(html, folder)
                self.assertEqual(len(fails), 1, src)
                self.assertIn("outside", fails[0], src)
                self.assertNotIn("no such file", fails[0], src)
                self.assertEqual(
                    len(va.visible_body_images(html, True, folder)), 0, src)
                self.assertTrue(va.remote_image_fail(src, folder), src)
            # A symlink whose target stays inside the assets directory still counts.
            self.assertEqual(va.draft_image_file_fails(
                '<img alt="pack" src="assets/slug/alias.webp">', folder), [])
            self.assertEqual(va.remote_image_fail("assets/slug/alias.webp", folder), "")

    def test_reference_style_remote_image_fails(self):
        remote = "https://cdn.shopify.com/s/files/a.webp"
        forms = [
            "![closet pouch][pack]\n\n[pack]: %s\n" % remote,
            "[pack]: %s\n\n![closet pouch][pack]\n" % remote,
            '[pack]: %s "title"\n![closet pouch][pack]\n' % remote,
            "[pack]: <%s>\n![closet pouch][pack]\n" % remote,
            "![closet pouch][]\n\n[closet pouch]: %s\n" % remote,
            "![closet pouch]\n\n[closet pouch]: %s\n" % remote,
            "![closet pouch][pack]\n\n[pack]: //cdn.shopify.com/s/files/a.webp\n",
            "![closet pouch][pack]\n\n[pack]: data:image/webp;base64,AAAA\n",
        ]
        for raw in forms:
            html = va.draft_struct_html(raw)
            self.assertIn("<img", html, raw)
            self.assertNotIn("![", html, raw)
            fails = va.draft_image_file_fails(html, "/private/tmp/missing-base")
            self.assertEqual(len(fails), 1, raw)
            self.assertTrue(
                "remote URL" in fails[0] or "data URI" in fails[0], fails[0])
            self.assertNotIn("no such file", fails[0], raw)
            self.assertEqual(
                len(va.visible_body_images(html, True, "/private/tmp")), 0, raw)
        # An alt that itself contains src= must not become a second attribute.
        injected = (
            '![foo" src="https://cdn.example/evil.webp][id]\n\n'
            "[id]: %s\n" % remote)
        html = va.draft_struct_html(injected)
        self.assertEqual(va.img_tag_src(va._IMG_TAG_RE.findall(html)[0]), remote)
        fails = va.draft_image_file_fails(html, "/private/tmp")
        self.assertEqual(len(fails), 1)
        self.assertIn("remote URL", fails[0])

    def test_publisher_markdown_forms_cannot_hide_a_remote_image(self):
        # markdown.markdown(..., extensions=['extra']) emits an <img> for each
        # of these. The old one-line regex left them as text, so the gate saw
        # zero images and the article could pass.
        remote = "https://cdn.shopify.com/s/files/a.webp"
        forms = [
            "![closet pouch][pack]\n\n[pack]:\t%s\n" % remote,
            "![closet pouch][pack]\n\n[pack]:\n\t%s\n" % remote,
            "![closet pouch][pack]\r\n\r\n[pack]: %s\r\n" % remote,
            "![foo [bar]](%s)" % remote,
            "![closet](<%s>)" % remote,
            '![closet](<%s> "title with ) paren")' % remote,
            "![closet](%s)" % ("\n" + remote),
            "Before the pouch.\n<img\nsrc=\"%s\">" % remote,
        ]
        for raw in forms:
            html = va.draft_struct_html(raw)
            self.assertIn("<img", html, raw)
            fails = va.draft_image_file_fails(html, "/private/tmp/missing-base")
            self.assertGreaterEqual(len(fails), 1, raw)
            self.assertTrue(
                any("remote URL" in item for item in fails), (raw, fails))
            self.assertFalse(
                any("no such file" in item for item in fails), fails)
            self.assertEqual(
                len(va.visible_body_images(html, True, "/private/tmp")), 0, raw)
        source = "Before the pouch.\n<source\nsrcset=\"%s 1x\">" % remote
        source_html = va.draft_struct_html(source)
        self.assertIn("<source", source_html)
        self.assertNotIn("\n", va._SOURCE_TAG_RE.findall(source_html)[0])
        source_fails = va.draft_image_file_fails(source_html, "/private/tmp")
        self.assertEqual(len(source_fails), 1)
        self.assertIn("remote URL", source_fails[0])

    def test_img_slash_src_without_space_fails(self):
        raw_tags = [
            '<img/src="https://cdn.shopify.com/s/files/a.webp">',
            "<img/src=https://cdn.shopify.com/s/files/a.webp>",
            '<IMG/SRC="https://cdn.shopify.com/s/files/a.webp">',
        ]
        for raw in raw_tags:
            html = va.draft_struct_html("Before the pouch.\n" + raw)
            tags = va._IMG_TAG_RE.findall(html)
            self.assertEqual(len(tags), 1, raw)
            self.assertEqual(
                va.img_tag_src(tags[0]),
                "https://cdn.shopify.com/s/files/a.webp", raw)
            self.assertEqual(len(va.visible_body_images(html, True)), 0, raw)
            fails = va.draft_image_file_fails(html, "/private/tmp")
            self.assertEqual(len(fails), 1, raw)
            self.assertIn("remote URL", fails[0], raw)
            self.assertNotIn("no such file", fails[0], raw)

    def test_srcset_and_source_srcset_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            os.makedirs(os.path.join(folder, "assets", "slug"))
            local = "assets/slug/hero.webp"
            with open(os.path.join(folder, local), "wb") as fh:
                fh.write(b"RIFF")
            self.assertEqual(va.remote_image_fail(local, folder), "")
            cases = [
                '<img src="%s" srcset="https://cdn.shopify.com/s/files/evil.webp 1x">' % local,
                '<img src="%s" srcset="https://cdn.example/a.webp 1x, https://cdn.example/b.webp 2x">' % local,
                '<img src="%s" srcset=https://cdn.shopify.com/s/files/evil.webp>' % local,
                '<img src="%s" SRCSET="https://cdn.shopify.com/s/files/evil.webp">' % local,
                '<source srcset="https://cdn.shopify.com/s/files/evil.webp">',
                '<source/srcset="https://cdn.shopify.com/s/files/evil.webp">',
                '<source srcset="https://cdn.example/a.webp 800w, https://cdn.example/b.webp 1600w">',
                '<img srcset="https://cdn.shopify.com/s/files/evil.webp">',
                '<img src="%s" srcset=" //cdn.shopify.com/s/files/evil.webp 1x">' % local,
            ]
            for html in cases:
                fails = va.draft_image_file_fails(html, folder)
                self.assertGreaterEqual(len(fails), 1, html)
                self.assertTrue(
                    any("remote URL" in item for item in fails), fails)
                self.assertFalse(
                    any("no such file" in item for item in fails), fails)
                self.assertEqual(
                    len(va.visible_body_images(html, True, folder)), 0, html)

    def test_alt_src_bait_does_not_hide_remote_src(self):
        with tempfile.TemporaryDirectory() as folder:
            os.makedirs(os.path.join(folder, "assets", "slug"))
            local = "assets/slug/hero.webp"
            with open(os.path.join(folder, local), "wb") as fh:
                fh.write(b"RIFF")
            self.assertEqual(va.remote_image_fail(local, folder), "")
            self.assertTrue(os.path.isfile(os.path.join(folder, local)))
            hidden = (
                '<img alt="bait src=%s" src="https://cdn.shopify.com/s/files/evil.webp">'
                % local)
            self.assertEqual(
                va.img_tag_src(hidden),
                "https://cdn.shopify.com/s/files/evil.webp")
            fails = va.draft_image_file_fails(hidden, folder)
            self.assertEqual(len(fails), 1)
            self.assertIn("remote URL", fails[0])
            self.assertNotIn(local, fails[0])
            self.assertNotIn("no such file", fails[0])
            self.assertEqual(len(va.visible_body_images(hidden, True, folder)), 0)
            # The same bait after a real local src is alt text, not a second image.
            # A later real src attribute is still an image load.
            later = (
                '<img src="%s" alt="caption" src="https://cdn.shopify.com/s/files/evil.webp">'
                % local)
            later_fails = va.draft_image_file_fails(later, folder)
            self.assertTrue(any("remote URL" in item for item in later_fails), later_fails)
            self.assertEqual(len(va.visible_body_images(later, True, folder)), 0)
            alt_only = (
                '<img alt="caption src=https://cdn.shopify.com/s/files/evil.webp" src="%s">'
                % local)
            self.assertEqual(va.draft_image_file_fails(alt_only, folder), [])
            self.assertEqual(len(va.visible_body_images(alt_only, True, folder)), 1)
            # A ">" inside alt used to end the tag regex before the real src.
            quoted_gt = '<img alt="a>b" src="https://cdn.shopify.com/s/files/evil.webp">'
            self.assertEqual(
                va.img_tag_src(va._IMG_TAG_RE.findall(quoted_gt)[0]),
                "https://cdn.shopify.com/s/files/evil.webp")
            gt_fails = va.draft_image_file_fails(quoted_gt, folder)
            self.assertEqual(len(gt_fails), 1)
            self.assertIn("remote URL", gt_fails[0])
            self.assertEqual(len(va.visible_body_images(quoted_gt, True, folder)), 0)

    def test_users_traversal_is_outside_allowed_roots(self):
        cases = [
            "/Users/../../etc/passwd",
            "/Users/kevinkreative/../../etc/passwd",
            "/Users/kevinkreative/genseo/../../../../etc/passwd",
            "/private/tmp/../../etc/passwd",
        ]
        for src in cases:
            # The lexical path may not exist (/Users is absent on Linux). The
            # normalized file does, which is what a naive isfile() would open.
            resolved = os.path.realpath(src)
            self.assertTrue(os.path.isfile(resolved), src)
            self.assertNotEqual(resolved, src)
            msg = va.remote_image_fail(src)
            self.assertIn("outside", msg, src)
            self.assertNotIn("no such file", msg, src)
            self.assertNotIn("remote URL", msg, src)
            html = '<img alt="pack" src="%s">' % src
            fails = va.draft_image_file_fails(html, "/private/tmp")
            self.assertEqual(len(fails), 1, src)
            self.assertIn("outside", fails[0], src)
            self.assertNotIn("no such file", fails[0], src)
            self.assertEqual(len(va.visible_body_images(html, True)), 0, src)
        srcset = (
            '<img src="/Users/../../etc/passwd" '
            'srcset="/Users/kevinkreative/../../etc/passwd 1x">')
        srcset_fails = va.draft_image_file_fails(srcset, "/private/tmp")
        self.assertGreaterEqual(len(srcset_fails), 2)
        self.assertTrue(all("outside" in item for item in srcset_fails))
        # No ".." in the written path. normpath stays under /Users.
        # realpath of the symlink is outside /Users (on macOS, /private/etc/passwd).
        # A Mac checkout lives under /Users. Otherwise use a writable /Users.
        users_dir = ROOT if ROOT.startswith("/Users/") else None
        if users_dir is None and os.path.isdir("/Users") and os.access("/Users", os.W_OK):
            users_dir = "/Users"
        if users_dir is None:
            self._assert_symlink_realpath_leaves_its_root()
            return
        parent = tempfile.mkdtemp(prefix="t32-img-", dir=users_dir)
        link = os.path.join(parent, "escape.webp")
        good = os.path.join(parent, "hero.webp")
        try:
            os.symlink("/etc/passwd", link)
            with open(good, "wb") as fh:
                fh.write(b"RIFF")
            self.assertTrue(link.startswith("/Users/"))
            self.assertTrue(os.path.isfile(link))
            self.assertNotIn("..", link)
            link_fails = va.draft_image_file_fails(
                '<img alt="pack" src="%s">' % link, "/private/tmp")
            self.assertEqual(len(link_fails), 1)
            self.assertIn("outside", link_fails[0])
            self.assertNotIn("no such file", link_fails[0])
            self.assertEqual(va.draft_image_file_fails(
                '<img alt="pack" src="%s">' % good, "/private/tmp"), [])
        finally:
            if os.path.lexists(link):
                os.remove(link)
            if os.path.exists(good):
                os.remove(good)
            os.rmdir(parent)

    def _assert_symlink_realpath_leaves_its_root(self):
        """Same jail as the /Users symlink, without requiring that prefix."""
        parent = tempfile.mkdtemp(prefix="t32-root-")
        root = os.path.join(parent, "root")
        outside = os.path.join(parent, "outside")
        os.makedirs(root)
        os.makedirs(outside)
        secret = os.path.join(outside, "secret.webp")
        good = os.path.join(root, "hero.webp")
        link = os.path.join(root, "escape.webp")
        try:
            with open(secret, "wb") as fh:
                fh.write(b"secret")
            with open(good, "wb") as fh:
                fh.write(b"RIFF")
            os.symlink(secret, link)
            self.assertNotIn("..", link)
            self.assertFalse(va._stays_under(link, root))
            self.assertTrue(va._stays_under(good, root))
        finally:
            if os.path.lexists(link):
                os.remove(link)
            if os.path.exists(good):
                os.remove(good)
            if os.path.exists(secret):
                os.remove(secret)
            os.rmdir(root)
            os.rmdir(outside)
            os.rmdir(parent)


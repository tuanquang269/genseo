"""Packaging palette for landing pages (Kevin 2026-10-09): extraction, re-hue, cascade-safe override, gate.
Run: /usr/bin/python3 -m unittest tests/test_landing_palette.py"""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import landing_palette as lp  # noqa: E402

HOUSE = (".gsl-ref{--gp-ink:#12301f;--gp-forest:#17352a;--gp-text:#23382c;--gp-muted:#3f5347;--gp-accent:#2f8a3b;"
         "--gp-sage:#eef4ee;--gp-sage-2:#e2ece2;--gp-bone:#f6f8f5;--gp-line:#d6e2d6}"
         ".gsl-ref .btn{background:var(--gp-forest);color:#fff;padding:0 34px}"
         ".gsl-ref .pill{background:linear-gradient(137deg,#3a9e40,#2b5a36);border:1.5px solid #3a9e40;font-size:20px}"
         ".gsl-ref .pill{background:#475569}"                     # later non-green rule must still win
         ".gsl-ref .k{color:#2f8a3b}"                              # puts the color family in play
         "@media(max-width:749px){.gsl-ref .x{box-shadow:0 8px 20px rgba(23,53,42,.4);color:#d42929}}")
ROSE = {"hue": 12.0, "chroma": 0.112, "handle": "test-pack"}


def solid_png(path, rgb, size=(120, 160), border=(255, 255, 255)):
    from PIL import Image
    im = Image.new("RGB", (size[0] + 40, size[1] + 40), border)
    im.paste(Image.new("RGB", size, rgb), (20, 20))
    im.save(path)


class ColorMath(unittest.TestCase):
    def test_contrast_reference_values(self):
        self.assertAlmostEqual(lp.contrast((0, 0, 0), (255, 255, 255)), 21.0, places=2)
        self.assertAlmostEqual(lp.contrast((255, 255, 255), (255, 255, 255)), 1.0, places=3)

    def test_rehue_keeps_luminance_so_contrast_is_unchanged(self):
        for hx in ("#17352a", "#2f8a3b", "#3a9e40", "#eef4ee", "#54b94a"):
            o = lp.parse_color(hx)[0]
            n = lp.remap_color(o, ROSE)
            self.assertIsNotNone(n, hx)
            self.assertAlmostEqual(lp.contrast(o, (255, 255, 255)), lp.contrast(n, (255, 255, 255)), delta=0.06)
            self.assertLessEqual(lp.hue_dist(lp.lch(n)[2], ROSE["hue"]), 6, hx)

    def test_hex_with_alpha_is_recolored_and_keeps_alpha(self):
        out = lp.remap_text("color:#1e3a29cc;box-shadow:0 0 1px #1e3a2980;x:#2f8a", ROSE)
        self.assertNotIn("1e3a29", out)
        self.assertRegex(out, r"color:#[0-9a-f]{6}cc;box-shadow:0 0 1px #[0-9a-f]{6}80;")

    def test_non_house_colors_untouched(self):
        for hx in ("#ffffff", "#d42929", "#475569", "#2e2a39", "#000000"):
            self.assertIsNone(lp.remap_color(lp.parse_color(hx)[0], ROSE), hx)

    def test_low_chroma_pale_surface_clears_the_gate_floor(self):
        pale = lp.remap_color(lp.parse_color("#eef4ee")[0], {"hue": 120.1, "chroma": 0.038})
        self.assertIsNotNone(pale)
        self.assertGreaterEqual(lp.lch(pale)[1], lp.TOKEN_CHROMA)
        self.assertLessEqual(lp.hue_dist(lp.lch(pale)[2], 120.1), 6)


class Extraction(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_pink_pack_on_white_background(self):
        p = os.path.join(self.d, "pack.png")
        solid_png(p, (206, 117, 126))
        cols = lp.extract([p])
        self.assertTrue(cols)
        self.assertTrue(all(c["L"] < 0.93 or c["C"] >= 0.03 for c in cols), "white background must be ignored")
        ph = lp.pack_hue(cols)
        self.assertIsNotNone(ph)
        self.assertLessEqual(lp.hue_dist(ph["hue"], lp.lch((206, 117, 126))[2]), 3)

    def test_neutral_pack_keeps_house_palette(self):
        p = os.path.join(self.d, "pack.png")
        solid_png(p, (60, 60, 60))
        self.assertIsNone(lp.pack_hue(lp.extract([p])))

    def test_pack_photo_is_the_png_when_a_cutout_also_exists(self):
        handle, imgs = lp.pack_images({"product_ref": "fusiforce-creatine-gummies"})
        self.assertEqual(handle, "fusiforce-creatine-gummies")
        self.assertEqual(len(imgs), 1)
        self.assertTrue(imgs[0].endswith("fusiforce-creatine-gummies.png"))
        self.assertFalse(imgs[0].endswith("-cutout.png"))

    def test_real_florafresh_ref_is_rose(self):
        ref = os.path.join(ROOT, "product_refs", "florafresh-vaginal-probiotics-gummies.png")
        if not os.path.exists(ref):
            self.skipTest("product ref missing")
        ph = lp.pack_hue(lp.extract([ref]))
        self.assertTrue(ph and (ph["hue"] < 40 or ph["hue"] > 340), ph)


class Override(unittest.TestCase):
    def test_override_is_scoped_more_specific_and_recolored(self):
        out = lp.build_override(HOUSE, ROSE)
        self.assertIn(".gsl-ref.gsl-pal{", out)
        self.assertNotIn("#2f8a3b", out)
        self.assertNotIn("#3a9e40", out)
        self.assertNotIn("rgba(23,53,42", out)
        self.assertIn("#d42929", out)            # red price color in an affected family is copied unchanged
        self.assertIn("@media(max-width:749px){.gsl-ref.gsl-pal .x{", out)
        self.assertNotIn("padding", out)          # unaffected properties are not copied
        self.assertNotIn("font-size", out)

    def test_cascade_preserved_for_later_non_house_rule(self):
        out = lp.build_override(HOUSE, ROSE)
        a, b = out.find(".gsl-ref.gsl-pal .pill{background:linear-gradient"), out.find(".gsl-ref.gsl-pal .pill{background:#475569")
        self.assertTrue(0 <= a < b, "the later grey .pill background must be re-emitted after the recolored one")

    def test_apply_to_body_adds_block_class_and_inline_recolor(self):
        body = '<div class="gsl-ref gsl-ref--listicle"><svg><path fill="#2f8a3b"/></svg></div>\n'
        nb = lp.apply_to_body(body, HOUSE, ROSE)
        self.assertTrue(nb.startswith('<style id="gsl-pal">'))
        self.assertIn('class="gsl-ref gsl-pal gsl-ref--listicle"', nb)
        self.assertNotIn('fill="#2f8a3b"', nb)


class Gate(unittest.TestCase):
    def test_house_green_fails_on_pink_pack(self):
        tok, blk = lp.effective_tokens(HOUSE, '<div class="gsl-ref gsl-ref--listicle"></div>')
        rows = lp.judge(tok, ROSE, blk)
        self.assertFalse(all(ok for _, ok, _ in rows))
        self.assertFalse(dict((n, ok) for n, ok, _ in rows)["hue--gp-forest"])

    def test_rehued_page_passes_hue_and_aa(self):
        nb = lp.apply_to_body('<div class="gsl-ref gsl-ref--listicle"></div>', HOUSE, ROSE)
        tok, blk = lp.effective_tokens(HOUSE, nb)
        bad = [(n, d) for n, ok, d in lp.judge(tok, ROSE, blk) if not ok]
        self.assertEqual(bad, [])

    def test_accent_text_is_darkened_to_aa(self):
        nb = lp.apply_to_body('<div class="gsl-ref gsl-ref--listicle"></div>', HOUSE, ROSE)
        tok, _ = lp.effective_tokens(HOUSE, nb)
        acc = lp.parse_color(tok["--gp-accent"])[0]
        for bg in ("#ffffff", tok["--gp-sage"], tok["--gp-sage-2"]):
            self.assertGreaterEqual(lp.contrast(acc, lp.parse_color(bg)[0]), 4.5, bg)

    def test_check_cli_hard_fail_for_new_spec_without_palette(self):
        d = tempfile.mkdtemp()
        try:
            pack = os.path.join(d, "pack.png")
            solid_png(pack, (206, 117, 126))
            spec = {"slug": "t", "engine": "ref", "created": "2026-10-10", "pack_palette_images": [pack], "offer": {"href": "/products/none"}}
            os.makedirs(os.path.join(d, "t"))
            open(os.path.join(d, "t", "page.css"), "w").write(HOUSE)
            open(os.path.join(d, "t", "body.html"), "w").write('<div class="gsl-ref gsl-ref--listicle"></div>')
            sp = os.path.join(d, "t.json")
            json.dump(spec, open(sp, "w"))
            self.assertEqual(lp.check(sp), 1)                       # green page, pink pack -> FAIL
            open(os.path.join(d, "t", "body.html"), "w").write(lp.apply_to_body('<div class="gsl-ref gsl-ref--listicle"></div>', HOUSE, lp.resolve(spec)))
            self.assertEqual(lp.check(sp), 0)                       # re-hued -> PASS
            spec["created"] = "2026-10-08"; spec["palette"] = None
            json.dump({k: v for k, v in spec.items() if v is not None}, open(sp, "w"))
            open(os.path.join(d, "t", "body.html"), "w").write('<div class="gsl-ref gsl-ref--listicle"></div>')
            self.assertEqual(lp.check(sp), 0)                       # pre-2026-10-09 live pages: WARN only
        finally:
            shutil.rmtree(d)

    def test_old_specs_render_without_palette(self):
        self.assertFalse(lp.wants_palette({"engine": "ref", "created": "2026-10-08"}))
        self.assertTrue(lp.wants_palette({"engine": "ref", "created": "2026-10-09"}))
        self.assertFalse(lp.wants_palette({"engine": "ref", "created": "2026-10-11", "palette": "off"}))


if __name__ == "__main__":
    unittest.main()

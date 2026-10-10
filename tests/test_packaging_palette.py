"""Packaging colors for listicle/landing pages (Kevin 2026-10-09).

The palette file is the source of truth. A hard-window draft that conflicts with it
fails closed. Run: python3 -m unittest tests/test_packaging_palette.py
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import brand_rules as br  # noqa: E402
import florafresh_rules as ff  # noqa: E402
import landing_palette as lp  # noqa: E402
import packaging_palette as pp  # noqa: E402

FF = "florafresh-vaginal-probiotics-gummies"
NMN = "ageaura-pure-nmn-tmg-nad-complex"

HOUSE = (".gsl-ref{--gp-ink:#12301f;--gp-forest:#17352a;--gp-text:#23382c;--gp-muted:#3f5347;--gp-accent:#2f8a3b;"
         "--gp-sage:#eef4ee;--gp-sage-2:#e2ece2;--gp-bone:#f6f8f5;--gp-line:#d6e2d6}")


def _spec(handle, **extra):
    base = {
        "template": "listicle",
        "engine": "ref",
        "created": "2026-10-10",
        "slug": "t",
        "product_ref": handle,
        "offer": {"href": "https://wellnessnest.co/products/" + handle},
    }
    base.update(extra)
    return base


def _write_page(folder, body):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "page.css"), "w", encoding="utf-8") as fh:
        fh.write(HOUSE)
    with open(os.path.join(folder, "body.html"), "w", encoding="utf-8") as fh:
        fh.write(body)


class PaletteFiles(unittest.TestCase):
    def test_florafresh_file_matches_the_pack_photo(self):
        pal = pp.load(FF)
        self.assertEqual(pal["kind"], "chromatic")
        self.assertEqual(pal["packaging_note"], "dusty pink / rose")
        self.assertEqual(pal["hex"], "#d17a85")
        self.assertEqual(pal["hue"], 12.3)
        self.assertEqual(pal["hue_tolerance"], lp.HUE_TOL)
        photo = lp.pack_hue(lp.extract([os.path.join(ROOT, "product_refs", FF + ".png")]))
        self.assertEqual(pal["hex"], photo["hex"])
        self.assertEqual(pal["hue"], photo["hue"])
        self.assertEqual([c["hex"] for c in pal["clusters"]],
                         [c["hex"] for c in lp.extract([os.path.join(ROOT, "product_refs", FF + ".png")])])

    def test_ageaura_file_is_the_measured_neutral_bottle(self):
        pal = pp.load(NMN)
        self.assertEqual(pal["kind"], "neutral")
        self.assertIsNone(pal["hue"])
        self.assertTrue(pal["house_palette_allowed"])
        self.assertIn("white with dark grey text", pal["packaging_note"])
        png = os.path.join(ROOT, "product_refs", NMN + ".png")
        clusters = lp.extract([png])
        self.assertIsNone(lp.pack_hue(clusters))
        self.assertTrue(all(c["C"] < lp.MIN_CHROMA for c in clusters))
        self.assertEqual([c["hex"] for c in pal["clusters"]], [c["hex"] for c in clusters])
        measured = {c["hex"] for c in pal["clusters"]}
        for theme_hex in ("#2e2a39", "#f5f5f7", "#e3e3e8", "#54b94a"):
            self.assertNotIn(theme_hex, measured)

    def test_palette_files_are_not_product_handles(self):
        handles = br.handles_from_product_refs(os.path.join(ROOT, "product_refs"))
        self.assertIn(FF, handles)
        self.assertIn(NMN, handles)
        self.assertNotIn(FF + ".palette", handles)
        self.assertNotIn(NMN + ".palette", handles)
        self.assertNotIn("ageaura-pure-urolithin-a.palette", handles)

    def test_gaps_skip_committed_files_and_the_denied_sku(self):
        missing = pp.gaps()
        self.assertNotIn(FF, missing)
        self.assertNotIn(NMN, missing)
        self.assertNotIn("ageaura-pure-urolithin-a", missing)
        self.assertIn("fusiforce-creatine-gummies", missing)
        self.assertIn("pure-shilajit-gold-resin", missing)


class SpecGate(unittest.TestCase):
    def test_live_pages_are_not_new_violations(self):
        for name in ("florafresh-listicle-261009.json", "ageaura-nmn-listicle-261008.json"):
            with open(os.path.join(ROOT, "landing_drafts", name), encoding="utf-8") as fh:
                spec = json.load(fh)
            self.assertEqual(pp.spec_violations(spec), [], name)
            self.assertEqual(br.spec_violations(spec), [], name)

    def test_florafresh_opt_out_and_green_hue_fail(self):
        off = _spec(FF, palette="off")
        bad = br.spec_violations(off)
        self.assertTrue(any("palette off" in item and "#d17a85" in item for item in bad), bad)
        green = _spec(FF, palette={"hue": 140, "chroma": 0.1})
        bad = pp.spec_violations(green)
        self.assertTrue(bad and "140" in bad[0], bad)
        near = _spec(FF, palette={"hue": 20, "chroma": 0.11})
        self.assertEqual(pp.spec_violations(near), [])

    def test_ageaura_forced_rose_fails_and_house_hue_does_not(self):
        rose = _spec(NMN, palette={"hue": 12, "chroma": 0.11})
        bad = br.spec_violations(rose)
        self.assertTrue(any("neutral" in item for item in bad), bad)
        house = _spec(NMN, palette={"hue": 140, "chroma": 0.1})
        self.assertEqual(pp.spec_violations(house), [])
        self.assertEqual(pp.spec_violations(_spec(NMN)), [])

    def test_old_specs_and_missing_files_are_not_guessed(self):
        old = _spec(FF, created="2026-10-08", palette="off")
        self.assertEqual(pp.spec_violations(old), [])
        self.assertEqual(pp.spec_violations(_spec("fusiforce-creatine-gummies", palette="off")), [])
        self.assertEqual(pp.spec_violations({"title": "FloraFresh", "template": "listicle"}), [])

    def test_unknown_kind_fails_closed(self):
        bad = pp.conflicts(_spec("example-pack"), {"kind": "nope"}, "example-pack")
        self.assertTrue(bad and "no usable kind" in bad[0])

    def test_photo_that_disagrees_with_the_file_fails(self):
        spec = _spec(FF)
        bad = pp.image_violations(spec, {"hue": 210, "hex": "#2244aa"})
        self.assertTrue(bad and "2244aa" not in bad[0] or "210" in bad[0])
        self.assertIn("210", bad[0])
        self.assertEqual(pp.image_violations(_spec(FF, created="2026-10-08"), {"hue": 210, "hex": "#2244aa"}), [])
        self.assertEqual(pp.image_violations(spec, {"hue": 12.3, "hex": "#d17a85"}), [])


class RenderGate(unittest.TestCase):
    def test_resolve_uses_the_file_not_a_conflicting_override(self):
        painted = lp.resolve(_spec(FF, palette={"hue": 140, "chroma": 0.1}))
        self.assertLessEqual(lp.hue_dist(painted["hue"], 12.3), 6)
        self.assertIsNone(lp.resolve(_spec(NMN, palette={"hue": 12, "chroma": 0.11})))

    def test_house_greens_fail_on_florafresh_and_pass_on_neutral_ageaura(self):
        folder = tempfile.mkdtemp()
        try:
            body = '<div class="gsl-ref gsl-ref--listicle"></div>'
            for handle, expect in ((FF, 1), (NMN, 0)):
                spec = _spec(handle, slug="page")
                _write_page(os.path.join(folder, "page"), body)
                path = os.path.join(folder, handle + ".json")
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(spec, fh)
                self.assertEqual(lp.check(path), expect, handle)
        finally:
            shutil.rmtree(folder)

    def test_rehued_florafresh_page_passes_and_opt_out_does_not(self):
        folder = tempfile.mkdtemp()
        try:
            spec = _spec(FF)
            page = os.path.join(folder, "t")
            painted = lp.resolve(spec)
            body = lp.apply_to_body('<div class="gsl-ref gsl-ref--listicle"></div>', HOUSE, painted)
            _write_page(page, body)
            path = os.path.join(folder, "t.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(spec, fh)
            self.assertEqual(lp.check(path), 0)
            spec["palette"] = "off"
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(spec, fh)
            _write_page(page, '<div class="gsl-ref gsl-ref--listicle"></div>')
            self.assertEqual(lp.check(path), 1)
            self.assertTrue(pp.spec_violations(spec))
        finally:
            shutil.rmtree(folder)

    def test_live_florafresh_render_still_passes(self):
        path = os.path.join(ROOT, "landing_drafts", "florafresh-listicle-261009.json")
        self.assertEqual(lp.check(path), 0)
        age = os.path.join(ROOT, "landing_drafts", "ageaura-nmn-listicle-261008.json")
        self.assertEqual(lp.check(age), 0)


class TicketAndCallSites(unittest.TestCase):
    def test_landing_ticket_conflict_fails_lint_and_the_note_does_not(self):
        ok = ("- [ ] listicle | wellnessnest | product=%s · %s · %s"
              % (FF, ff.LANDING_NOTE, pp.landing_note(FF)))
        self.assertEqual(br.violations(ok), [], ok)
        self.assertIn("1 billion CFU", ok)
        self.assertIn("#d17a85", ok)
        bad = "- [ ] listicle | wellnessnest | product=%s · palette: off" % FF
        reasons = br.violations(bad)
        self.assertTrue(any("#d17a85" in item for item in reasons), reasons)
        rose = "- [ ] advertorial | ageaura | product=%s · palette hue: 12" % NMN
        self.assertTrue(any("neutral" in item for item in br.violations(rose)))
        self.assertEqual(br.violations("The house kit uses #54b94a on articles."), [])
        self.assertEqual(br.violations(
            "- [ ] listicle | wellnessnest | product=fusiforce-creatine-gummies · palette: off"), [])

    def test_open_landing_queue_has_no_palette_violation(self):
        with open(os.path.join(ROOT, "daily-landing-tickets.md"), encoding="utf-8") as fh:
            text = fh.read()
        for block in text.splitlines():
            if block.startswith("- [ ]"):
                self.assertEqual(br.violations(block), [], block)

    def test_call_sites_read_the_palette_module(self):
        for rel, needle in (
            ("scripts/brand_rules.py", "packaging_palette.spec_violations"),
            ("scripts/brand_rules.py", "packaging_palette.ticket_violations"),
            ("scripts/build_landing_tickets.py", "pp.landing_note"),
            ("scripts/landing_palette.py", "packaging.load"),
            ("scripts/landing_publisher.py", "landing_palette.py"),
            ("scripts/lint_tickets.py", "packaging_palette.py"),
            ("scripts/validate_landing.py", "packaging_palette.py"),
            ("scripts/shopify_publisher.py", "palette.json"),
        ):
            with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn(needle, text, rel)


if __name__ == "__main__":
    unittest.main()

# Palette / Pillow unittest fix — 2026-10-31

Branch `cursor/fix-palette-pillow-1031`, off `origin/main` `6c46771` (`6c46771de6a11f5719422d94a337215015bec364`, "Publish shilajit loading with food article"). No Shopify, theme, publish, or brand-copy edits. Palette JSON files were not rewritten.

## Root cause

`scripts/landing_palette.py` `extract()` measured pack shots with `Image.thumbnail((160, 160))`. `product_refs/*.palette.json` matches that call on Pillow 10.4 through 12.3 (checked 10.4.0, 11.0.0, 11.3.0, 12.0.0, 12.3.0). Pillow 13.0.0 does not.

Two Pillow 13 resize changes move the k-means clusters:

1. `Image.resize` on an RGBA image now forwards `reducing_gap`. Pillow 12 dropped it when converting RGBA to RGBa, so a thumbnail was a single BICUBIC resize. Pillow 13's default `reducing_gap=2.0` adds an integer pre-shrink.
2. The C resampler now runs the vertical pass first when height shrinks by more than twice the width. Pillow 12 always did horizontal, then vertical. Shilajit Shockwave (`336×680` → `79×160`) hits that path.

On Pillow 13.0.0 + numpy 1.26.4 the exact unittest failures were:

- `tests.test_packaging_palette.PaletteFiles.test_remaining_pack_shots_match_the_png` — FusiForce file `#97c344` vs fresh extract `#9ac547` (the loop stops on the first pack; premium gummies, gold resin, and Shockwave also drift).
- `tests.test_packaging_palette.PaletteFiles.test_shilasource_file_is_the_measured_neutral_pack` — cluster share `0.3505` vs `0.35`, and later hex/hue digits.

Those are the two palette failures. The other two failures on `origin/main` are the landing-queue tests draft PR #98 already retargets. This branch does not change those tests.

## Fix

`extract()` still downscales to the same 160px box, but with two BICUBIC passes (horizontal, then vertical) and `reducing_gap` left off, in RGBa so alpha is not un-premultiplied between passes. That is the Pillow 12 thumbnail result.

Checked against a Pillow 12.3.0 `extract()` dump of all 13 `product_refs/*.png` files (pack shots and cutouts, including the denied Urolithin PNG): Pillow 13 with this path matches every cluster. Pillow 12.3.0 with this path also matches, so a Mac still on Pillow 12 does not move.

Committed palette hexes stay the source of truth. Shockwave remains `#3f452e`. FloraFresh remains `#d17a85`. No ticket or label copy was edited.

## Suite

Interpreter: `/usr/bin/python3` 3.12.3. Command: `bash tests/run_suite.sh`.

This branch, Pillow 13.0.0:

- Shell: `SH_FILES pass=13 fail=0`
- Unittest: `Ran 315 tests`, `FAILED (failures=2)`, `PY_FAIL`
- Failures, both unchanged from `origin/main` and both fixed by draft PR #98 (`ce9ef4c`, `cursor/fix-landing-queue-tests-1028`):
  - `test_landing_rotation.OpenQueueTests.test_rebalanced_open_tickets_include_both_priorities` — `AssertionError: 1 not greater than or equal to 7`
  - `test_queue_closures.FreshCheckoutTests.test_tracked_files_close_todays_tickets_without_a_ledger` — expected `pure-shilajit-gold-resin`, open line is the Shockwave ticket
- Palette module alone: `tests.test_landing_palette` + `tests.test_packaging_palette` — `Ran 40 tests`, `OK`, on both Pillow 13.0.0 and Pillow 12.3.0

This fix plus #98's test files (not part of this PR), Pillow 13.0.0: shell `pass=13 fail=0`, unittest `Ran 315 tests` `OK`, `PY_OK`.

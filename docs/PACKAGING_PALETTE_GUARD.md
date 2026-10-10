# Packaging palette guard (Kevin 2026-10-09)

Every listicle or advertorial landing page wears the hero product's packaging colors. The source of truth is `product_refs/<handle>.palette.json`. `scripts/packaging_palette.py` reads that file. `scripts/brand_rules.py` merges its spec and landing-ticket violations, so the same check runs in:

- `scripts/validate_landing.py` and `scripts/landing_render.py` (`brand_rules.spec_violations`)
- `scripts/landing_publisher.py` (aborts before a Shopify write, then `scripts/landing_palette.py check` aborts again if the painted CSS disagrees)
- `scripts/run_landing_daily.sh` (ticket becomes `DRAFT-QA-FAIL` when the palette check fails)
- `scripts/lint_tickets.py` (open landing tickets only: `listicle |` or `advertorial |`)
- `scripts/build_landing_tickets.py` (appends `packaging_palette.landing_note` when a file exists)

The hard window is a landing spec with `created` on or after 2026-10-09. Older live pages are not failed. Blog articles stay on the house block kit (`#54b94a` / `#1e3a29`). This guard does not recolor them.

A chromatic file fails a spec that sets `palette` to `off` or a manual hue more than `hue_tolerance` degrees (30) from the file. The render check fails when `--gp-forest`, `--gp-accent`, or `--gp-sage` is outside that tolerance, or when k-means on the pack photo disagrees with the file. A neutral file fails a forced hue outside the house-green band (95–170°). Near-grey tokens pass. House greens pass only while `house_palette_allowed` is true.

Hexes in the palette files are measurements. They are not new brand colors.

## Palettes on file

| Handle | Kind | What was measured |
|---|---|---|
| `florafresh-vaginal-probiotics-gummies` | chromatic | Packaging note "dusty pink / rose". K-means of `product_refs/florafresh-vaginal-probiotics-gummies.png`: `#d17a85`, hue 12.3, chroma 0.109. Same clusters as `landing_drafts/florafresh-listicle-261009/palette.json`. |
| `ageaura-pure-nmn-tmg-nad-complex` | neutral | Packaging note "white with dark grey text". K-means of the bottle photo: every cluster is below chroma 0.035 (`#d9d4cf`, `#e3e0dc`, `#beb7b0`, `#94928f`, `#605c58`, `#1c1c1c`), so there is no pack hue. `brand/ageaura.json` ink `#2e2a39` / bg `#f5f5f7` / border `#e3e3e8` are theme tokens, not bottle measurements, and are not the palette. |

`ageaura-pure-urolithin-a` has no palette file on purpose. That SKU stays denied.

## Gaps that need Kevin

These products have a packaging note and a pack photo, and no `*.palette.json`. The gate does not guess a hue for them. The image extractor can still recolor a new page from the photo; that result is not a committed source of truth until a palette file is added from a measurement Kevin accepts.

| Handle | Packaging note already in `product_refs` | Extractor on the pack photo (not committed) |
|---|---|---|
| `fusiforce-creatine-gummies` | bright green | `#97c344`, hue 126.4 |
| `turkesterone-advanced-formula` | green with black lid | `#2c7f28`, hue 142.5 |
| `premium-himalayan-shilajit-gummies` | matte black upper third fading into deep green | `#465e48`, hue 146.9 (one green cluster; the photo is mostly black) |
| `shilajit-shockwave` | black with green accents | `#3f452e`, hue 120.1, chroma 0.038 (barely chromatic) |
| `pure-shilajit-gold-resin` | matte black, bright green label blob, gold line-art and lid | `#607649`, hue 129.7. One hue does not describe black + green + gold. |
| `shilasource-himalayan-shilajit-resin` | matte black tube, amber jar, gold lid | no chromatic cluster (neutral) |

AgeAura's white bottle still renders with house greens, because `house_palette_allowed` is true and the renderer only knows how to rehue chromatic packs. Those greens were not read off the bottle. To make a new AgeAura listicle fail until it is grey, set `house_palette_allowed` to false after a grey token map exists.

```bash
python3 -m unittest tests/test_packaging_palette.py tests/test_landing_palette.py
python3 scripts/packaging_palette.py --spec landing_drafts/florafresh-listicle-261009.json
python3 scripts/packaging_palette.py --brief florafresh-vaginal-probiotics-gummies
python3 scripts/packaging_palette.py --gaps
```

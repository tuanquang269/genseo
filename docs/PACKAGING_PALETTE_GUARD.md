# Packaging palette guard (Kevin 2026-10-09)

Every listicle or advertorial landing page wears the hero product's packaging colors. The source of truth is `product_refs/<handle>.palette.json`. `scripts/packaging_palette.py` reads that file. `scripts/brand_rules.py` merges its spec and landing-ticket violations, so the same check runs in:

- `scripts/validate_landing.py` and `scripts/landing_render.py` (`brand_rules.spec_violations`)
- `scripts/landing_publisher.py` (aborts before a Shopify write, then `scripts/landing_palette.py check` aborts again if the painted CSS disagrees)
- `scripts/run_landing_daily.sh` (ticket becomes `DRAFT-QA-FAIL` when the palette check fails)
- `scripts/lint_tickets.py` (open landing tickets only: `listicle |` or `advertorial |`)
- `scripts/build_landing_tickets.py` (appends `packaging_palette.landing_note` when a file exists)

The hard window is a landing spec with `created` on or after 2026-10-09. Older live pages are not failed. Blog articles stay on the house block kit (`#54b94a` / `#1e3a29`). This guard does not recolor them.

A chromatic file fails a spec that sets `palette` to `off` or a manual hue more than `hue_tolerance` degrees (30) from the file. The render check fails when `--gp-forest`, `--gp-accent`, or `--gp-sage` is outside that tolerance, or when k-means on the pack photo disagrees with the file. A neutral file fails a forced hue outside the house-green band (95–170°). Near-grey tokens pass. House greens pass only while `house_palette_allowed` is true.

Hexes in the palette files are measurements. They are not new brand colors. The measurement image is `product_refs/<handle>.png`. `scripts/landing_palette.py` uses that PNG for the cross-check. A `*-cutout.png` is the fallback only when the PNG is missing, and it is not mixed into the k-means. Where a cutout exists, tests check that its hue stays inside the file's tolerance, or that it is neutral when the file is neutral.

`--gp-sage` is a pale surface (OKLab L > 0.88). Its chroma is raised until it clears 0.012, the same not-grey floor the render check already uses. A low-chroma pack would otherwise paint a sage the gate rejects. The hue stays the file's hue.

## Palettes on file

| Handle | Kind | What was measured |
|---|---|---|
| `florafresh-vaginal-probiotics-gummies` | chromatic | Packaging note "dusty pink / rose". K-means of `product_refs/florafresh-vaginal-probiotics-gummies.png`: `#d17a85`, hue 12.3, chroma 0.109. Same clusters as `landing_drafts/florafresh-listicle-261009/palette.json`. |
| `ageaura-pure-nmn-tmg-nad-complex` | neutral | Packaging note "white with dark grey text". K-means of the bottle photo: every cluster is below chroma 0.035 (`#d9d4cf`, `#e3e0dc`, `#beb7b0`, `#94928f`, `#605c58`, `#1c1c1c`), so there is no pack hue. `brand/ageaura.json` ink `#2e2a39` / bg `#f5f5f7` / border `#e3e3e8` are theme tokens, not bottle measurements, and are not the palette. |
| `fusiforce-creatine-gummies` | chromatic | Packaging note "bright green". K-means of the pack PNG: `#97c344`, hue 126.4, chroma 0.161. Every cluster is green. |
| `turkesterone-advanced-formula` | chromatic | Packaging note "green with black lid". K-means of the pack PNG: `#2c7f28`, hue 142.5, chroma 0.146. Two other clusters sit outside the 30° tolerance (`#cfd099` hue 108.7, `#87846c` hue 101.5). They stay in the file and are not a second UI hue. |
| `premium-himalayan-shilajit-gummies` | chromatic | Packaging note "matte black upper third fading into deep green lower two-thirds". The largest cluster is near-black `#1a1a1b` (chroma 0.002). The UI hue is the heaviest cluster that clears chroma 0.035: `#465e48`, hue 146.9, chroma 0.046. |
| `shilajit-shockwave` | chromatic | Packaging note "black with green accents". The largest cluster is dark `#252820` (chroma 0.015). The UI hue is `#3f452e`, hue 120.1, chroma 0.038. Chromatic share is 0.56, above the 8% neutral cutoff, so the file is chromatic. |
| `pure-shilajit-gold-resin` | chromatic | Packaging note names matte black, a bright green label blob, and gold line-art and lid. The UI hue is the heaviest chromatic cluster, the green blob: `#607649`, hue 129.7, chroma 0.071. `#d5caa7` (hue 92.6, chroma 0.048) is outside the 30° tolerance. It stays in the file and is not a second UI hue. |
| `shilasource-himalayan-shilajit-resin` | neutral | Packaging note "matte black tube with white type; amber/brown glass jar, gold lid, black wraparound label". Every cluster on the pack PNG is below chroma 0.035, so there is no pack hue. Amber and gold in the note did not form a chromatic cluster in this photo. |

`ageaura-pure-urolithin-a` has no palette file on purpose. That SKU stays denied. `packaging_palette.py --gaps` is empty for the current catalog: every other `product_refs/<handle>.json` has a palette file. A new handle with no file is still a gap. The gate does not guess a hue for it.

AgeAura's white bottle and the ShilaSource resin still render with house greens, because `house_palette_allowed` is true and the renderer only knows how to rehue chromatic packs. Those greens were not read off the photo. To make a new listicle for either pack fail until it is grey, set `house_palette_allowed` to false after a grey token map exists.

```bash
python3 -m unittest tests/test_packaging_palette.py tests/test_landing_palette.py
python3 scripts/packaging_palette.py --spec landing_drafts/florafresh-listicle-261009.json
python3 scripts/packaging_palette.py --brief florafresh-vaginal-probiotics-gummies
python3 scripts/packaging_palette.py --gaps
```

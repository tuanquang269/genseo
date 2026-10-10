# FusiForce pack-label guard (2026-10-09)

The pack-label whitelist is the source of truth for FusiForce Creatine Gummies (`https://wellnessnest.co/products/fusiforce-creatine-gummies`):

`product_refs/fusiforce-creatine-gummies.label.json`

Required lines in that file: FusiForce, Creatine, Monohydrate, Gummies, 90, Dietary Supplement. Optional lines include Green Apple flavor and the four front-of-pouch benefit lines (Promotes Lean Muscle Growth, Enhances Recovery, Boosts Energy Levels, Supports Cognitive Function). The file was read off the pack shot with `scripts/tools/label_ocr.swift` on 2026-10-08. The same pouch shots in `product_refs/fusiforce-creatine-gummies.png` and `fusiforce-creatine-gummies-cutout.png` show **90 GUMMIES** and Creatine Monohydrate. They do not show a milligram line or ginseng.

Copy that names FusiForce may say creatine monohydrate and **90 gummies**. It fails closed when it states any of the following and that exact token is not in the whitelist file:

- a pack count other than 90 (including **84** gummies, an 84-count, or 28 × 3 = 84)
- **25 mg**, **50 mg**, or any other milligram amount
- **30 servings**, or any other serving count (`28 servings`, `3 gummies per serving`, `3-gummy serving`)
- ginseng, Panax, or ginsenosides

A partial sachet in the cutout photo is not a whitelist line, so it is not a serving size. Creatine and monohydrate are allowed because those words are whitelist lines. Ginseng is not a whitelist line. `scripts/fusiforce_rules.py` reads the file on each check: if a token is added to the file later, that token is allowed; if the file is missing or no longer has exactly one integer line, pack-count claims fail closed.

`brand_rules.assess()` merges these violations, so every `brand_rules` caller enforces them: `lint_tickets.py` (open tickets only), `validate_article.py`, `validate_landing.py` / `landing_render.py` / `landing_publisher.py` (through `brand_rules.spec_violations()`), `topic_fitness.py` (`FAIL [fusiforce-label]`), the ticket and landing builders, image prompts, and `shopify_publisher.py` (publish and update). `refill_tickets.py` adds the pack-label line to every FusiForce ticket. `build_landing_tickets.py` adds a label note to FusiForce landing briefs. AgeAura rules are unchanged (NMN + TMG only; never Urolithin A).

Negations ("not 84 gummies") and another brand's row ("Brand X | 84 gummies") pass. A FusiForce sentence that states 84, a serving count, a milligram amount, or ginseng does not.

```bash
python3 -m unittest tests/test_fusiforce_guard.py
python3 scripts/fusiforce_rules.py --brief
python3 scripts/fusiforce_rules.py --spec landing_drafts/<slug>.json
```

## Left as they are

- No Shopify write, no PDP edit, no theme or robots change.
- `landing_drafts/fusiforce-creatine-listicle-261008.json` still states 5,000 mg, a 3-gummy serving, and Panax ginseng. Those tokens are not in the whitelist file. `brand_rules` now rejects that copy. The draft was not rewritten here.
- Open FusiForce tickets that do not state those tokens stay as they are. New FusiForce tickets from `refill_tickets.py` carry the 90-gummy line.

## Supplement Facts read, 2026-10-10

`scripts/tools/label_ocr.swift` (macOS Vision, accurate, no language correction) was run on the front pouch and on the live gallery. No photograph of a printed side-panel Supplement Facts was in `product_refs/`, `~/PATI/LLM-Wiki`, the creative stills under `~/PATI/work/projects/Products/creative/FusiForce Creatine Gummies/`, or the live pack shots. The whitelist stays the front pouch. Dose, ginseng, and serving tokens from the graphics below were not copied into `fusiforce-creatine-gummies.label.json`.

Front pouch, confidence 1.00, on `product_refs/fusiforce-creatine-gummies.png`, the cutout, and live gallery image 0 (`creatine_gummies.webp`, 2048 px):

- `FusiForce`, `Creatine`, `Monohydrate`, `Gummies`, `Green Apple flavor`, `90`, `GUMMIES`, `DIETARY`, `SUPPLEMENT`
- A separate `3` line sits with `GUMMIES` on the partial sachet. That is not a serving-size line, and it is not a whitelist token.

Designed Supplement Facts graphic, confidence 1.00, live gallery image 2 (`creatine_gummies_1.webp`) and the same art at `~/PATI/work/ageaura-funnel-7989/u1v2-deploy-2026-08-18/assets/fusiforce-serving-panel-u1v2-v1.webp`:

- `DIRECTIONS: Enjoy 3 gummies daily.`
- `Serving Size: 3 gummies`
- `Servings per container: 28`
- `Creatine Monohydrate` with `5 g` and `(Purified 99.97%)`
- `Panax Ginseng Root Extract 50 mg`
- `(Standardized to 10% Ginsenosides)`
- Other ingredients line includes `Blueberry Flavor` and `Brilliant Blue`
- Sodium amount on that panel is `5 mg` (the 1x read glued it to `<1%` as `5mg <1%`; the 2x read split `5 mg`)

Second designed Supplement Facts graphic, confidence 1.00, live gallery image 15 (`hf_20260312_135110_11829a3d-bf39-4a40-a8ae-c8abcce3085a.webp`):

- `DIRECTIONS: Enjoy 4 gummies daily.`
- `Serving Size: 4 gummies`
- `Serving Per Container: 28`
- `Creatine Monohydrate` with `5 g` and `(Purified 99.97%)`
- `Panax Ginseng Root Extract 50 mg`
- `(Standardized to 10% Ginsenosides)`
- Other ingredients line includes `Blueberry Flavor` (one token read as `Mallitol`)

Blueberry pouch still, confidence 1.00, live gallery image 14 (`1_15.webp`): `Blueberry flavor`, `112`, `GUMMIES`. The full-frame read did not return a `4` line or a `90` line.

Those two facts graphics are not one label. Image 2 states a 3-gummy serving and blueberry ingredients. Image 15 states a 4-gummy serving and blueberry ingredients. The green-apple pouch states `90` and `Green Apple flavor`. `3 × 28 = 84`, which is not the `90` on that pouch. `4 × 28 = 112`, which matches the blueberry still, not the green-apple pouch this label file describes.

Marketing tiles, not a facts panel: image 11 reads `CLINICALLY STUDIED DOSE • 5,000mg`. Image 13 reads `5,000mg`, `Per Serving`, `Only 3`, `Gummies`, `Sour Green`, `Apple Flavor`, and `90`. The live PDP description says 5,000 mg per 3-gummy serving and 25 mg Panax ginseng. Neither `5,000 mg` nor `25 mg` nor `30 servings` nor `84` was a token on either Supplement Facts graphic.

Creative stills in that FusiForce folder returned `90` and, on some frames, `GUMMIES`. They did not return a Supplement Facts panel.

A photo of the printed Supplement Facts on the green-apple 90-count pouch is still required before `5 g`, `50 mg`, `3 gummies`, `28`, or ginseng can be added to the whitelist.

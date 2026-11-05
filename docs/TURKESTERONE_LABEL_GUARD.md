# Turkesterone Advanced Formula pack-label guard

The pack-label whitelist is the source of truth for this one product (`https://wellnessnest.co/products/turkesterone-advanced-formula`):

`product_refs/turkesterone-advanced-formula.label.json`

`scripts/turkesterone_rules.py` reads `required` and `optional` only. The file's `source` note is provenance and is not an allow-list.

This file is not a `scripts/tools/label_ocr.swift` confidence-1.00 read. This host has no macOS Vision, so that script was not re-run. On 2026-10-10, RapidOCR (`rapidocr-onnxruntime`) read `product_refs/turkesterone-advanced-formula.png` at native size and at 2x. `required` and `accepted_ocr` are the strings both reads returned verbatim. None of those lines scored confidence 1.00. The lowest agreeing line is `Capsules` (native 0.9241, 2x 0.9786). The brand line `TURKESTERONE` agreed at 0.9934 / 0.9925.

A 2026-10-09 macOS Vision read of the same PNG returned the brand line as `TURNESTERONE` (confidence 1.00). That string was not copied into `required` or `optional`, and it was not corrected into `TURKESTERONE`. The `TURKESTERONE` line in this file is the RapidOCR agreement, not a rewrite of the Vision miss.

Lines the two RapidOCR reads did not agree on were omitted, not corrected:

- `KSM-66?Ashwagandha` vs `KSM-66? Ashwagandha`
- `POTENTIAL*` vs `POTENTIAL`
- `RECOVERY` vs `RECOVERY*`
- `Colostrum+Tongkat Ali` vs `Colostrum + Tongkat Ali`
- `BioPerineBlackPepper` vs `BioPerine@ Black Pepper`

Whitelist lines today:

- required: `wellness`, `nest`, `PREMIUM`, `TURKESTERONE`, `ADVANCED`, `FORMULA`, `AMPLIFY`, `MUSCLE`, `ENDURANCE`, `60`, `Dietary Supplement`, `Capsules`
- optional: empty

Allowed dose phrases are parsed from those lines. `60` and `Capsules` were separate OCR lines. They were not rewritten into one `60 Capsules` line in the file. A line that is only a number, together with a line that is only the word capsules, is that capsule count. Today that is `60 capsules`. No other number is joined to that word. If a token is added to the file later, that token is allowed. If the file is missing or empty, in-scope copy fails closed.

No milligram token is in `required` or `optional`. Do not add one.

Copy that names Turkesterone Advanced Formula, Premium Turkesterone, Turkesterone Advanced, or `turkesterone-advanced-formula` may repeat the whitelist lines, including `60 capsules`. It fails closed when it states any of the following and that dose phrase is not parsed from the whitelist lines:

- a milligram amount (`500 mg`, `250 milligrams`, `1,500 mg`, `60 mg`)
- a serving count (`30 servings`, `60 servings`, servings per jar 30)
- a different capsule count (`30 capsules`, `90 capsules`, `120 capsules`, `60 caplets`, `60 tablets`)
- a day-supply (`30-day supply`, `60-day supply`)
- another dose the file does not list (micrograms, grams, milliliters, fluid ounces, IU, CFU, counted drops or droppers, a gummy count, a percentage)

Bare "turkesterone" without Advanced, Premium, or this handle is the ingredient. A study sentence that states a trial dose passes when it does not name this SKU. Premium Himalayan Shilajit Gummies, Shilajit Shockwave, Pure Shilajit Gold Resin, ShilaSource resin, AgeAura, and FloraFresh are not this product: copy that names only those SKUs is out of scope.

`brand_rules.assess()` merges these violations, so every `brand_rules` caller enforces them: `lint_tickets.py` (open tickets only), `validate_article.py`, `validate_landing.py` / `landing_render.py` / `landing_publisher.py` (through `brand_rules.spec_violations()`), `topic_fitness.py` (`FAIL [turkesterone-label]`), the ticket and landing builders, image prompts, and `shopify_publisher.py` (publish and update abort). `refill_tickets.py` adds the pack-label line to every Turkesterone ticket. `build_landing_tickets.py` adds a label note to Turkesterone landing briefs. AgeAura rules are unchanged (NMN + TMG only). FloraFresh rules use SNZ-1969 and 15B CFU (a 1-billion count is retired). Shockwave, Gold Resin, and ShilaSource resin rules are unchanged.

Negations ("not a milligram amount") and another brand's row ("Brand X | 500 mg") pass. A study sentence that states a trial dose passes when it does not name this SKU. A sentence that names this SKU and states a milligram, a serving count, or a different capsule count does not.

```bash
python3 -m unittest tests/test_turkesterone_guard.py
python3 scripts/turkesterone_rules.py --brief
python3 scripts/turkesterone_rules.py --spec landing_drafts/<slug>.json
```

## OCR gap that should block a later milligram allow-list

`product_refs/turkesterone-advanced-formula.png` is the jar front only (480×560). The Supplement Facts / side panel was not in that photo and was not read. `required` and `optional` have no serving-size line and no milligram amount. This guard fails those claims closed. Do not add them from the PDP description, from an older article, or from a visual guess. A milligram or Supplement Facts claim can be allow-listed only after a new confidence-1.00 `label_ocr.swift` read of that panel is copied verbatim into `required` or `optional` (misreads omitted, not corrected). Until that read exists, merging a change that allows a milligram dose is blocked.

The ingredient lines that RapidOCR did not agree on (KSM-66, Ashwagandha, Colostrum, Tongkat Ali, BioPerine, the benefit badges) are not whitelist lines. Do not correct the omitted strings into those names.

There is no `product_refs/turkesterone-advanced-formula-cutout.png`. The landing runner uses the real PDP image for this SKU and must not claim `label gate PASS`.

## Left as they are

- No Shopify write, no PDP edit, no publish, no theme or robots change.
- The whitelist was not given a milligram token, a serving count, or a Supplement Facts line.
- The Vision miss `TURNESTERONE` was not corrected into the file.
- The split `60` and `Capsules` lines were not rewritten into one new OCR line.
- Gummies, Shockwave, Gold Resin, and ShilaSource resin were not given a new formula guard in this change.
- Local `llms.txt` still states a URL and no Turkesterone formula sentence.

# Shilajit Shockwave pack-label guard

The pack-label whitelist is the source of truth for this one product (`https://wellnessnest.co/products/shilajit-shockwave`):

`product_refs/shilajit-shockwave.label.json`

OCR-accepted lines in that file: `wellness`, `nest`, `SHILAJIT`, `SHOCKWAVE`, `EXPERIENCE FOCUSED ENERGY`, `PEAK PERFORMANCE`. The file was read with `scripts/tools/label_ocr.swift` on 2026-10-09. A native read and the gate's 2x read agreed on those lines. They did not agree on a mark, so the guard does not require a trademark glyph.

No milligram token was read. The volume line was not stable (`1 il oz` / `1 1l oz` / `30 ml`) and was omitted, not corrected. Those strings are not whitelist lines. `scripts/shockwave_rules.py` reads `required` and `optional` only. The file's `source` note is provenance and is not an allow-list.

Copy that names Shilajit Shockwave or `shilajit-shockwave` may repeat the identity lines. It fails closed when it states any of the following and that exact token is not in the whitelist file:

- a milligram amount (`500 mg`, `250 milligrams`, `1,500 mg`)
- a serving count (`30 servings`, servings per bottle 30)
- a volume (`1 fl oz`, `30 ml`, `1 oz`)
- another dose the file does not list (micrograms, grams, IU, CFU, counted drops or droppers, a day-supply, a gummy count, a fulvic percentage)

If a token is added to the file later, that token is allowed. If the file is missing or empty, in-scope copy fails closed. Premium Himalayan Shilajit Gummies, Pure Shilajit Gold Resin, and ShilaSource resin are not this product: copy that names only those SKUs is out of scope.

`brand_rules.assess()` merges these violations, so every `brand_rules` caller enforces them: `lint_tickets.py` (open tickets only), `validate_article.py`, `validate_landing.py` / `landing_render.py` / `landing_publisher.py` (through `brand_rules.spec_violations()`), `topic_fitness.py` (`FAIL [shockwave-label]`), the ticket and landing builders, image prompts, and `shopify_publisher.py` (publish and update abort). `refill_tickets.py` adds the pack-label line to every Shockwave ticket. `build_landing_tickets.py` adds a label note to Shockwave landing briefs. AgeAura rules are unchanged (NMN + TMG only). FloraFresh rules are unchanged (SNZ-1969, 1 billion CFU).

Negations ("not a milligram amount") and another brand's row ("Brand X | 500 mg") pass. A study sentence that states a trial dose passes when it does not name Shockwave. A sentence that names Shockwave and states a milligram, a serving count, or a volume does not.

```bash
python3 -m unittest tests/test_shockwave_guard.py
python3 scripts/shockwave_rules.py --brief
python3 scripts/shockwave_rules.py --spec landing_drafts/<slug>.json
```

## Left as they are

- No Shopify write, no PDP edit, no theme or robots change.
- The whitelist was not given a milligram, milliliter, or fluid-ounce token.
- Gummies were not given a formula guard in this change. Gold Resin has its own pack-label guard: `docs/GOLD_RESIN_LABEL_GUARD.md`. ShilaSource resin has its own pack-label guard: `docs/SHILASOURCE_RESIN_LABEL_GUARD.md`.

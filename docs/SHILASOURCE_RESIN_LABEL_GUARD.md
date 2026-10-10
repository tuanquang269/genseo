# ShilaSource Himalayan Shilajit Resin pack-label guard

The pack-label whitelist is the source of truth for this one product (`https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin`), the resin SKU on the live listicle `https://wellnessnest.co/pages/shilajit-resin-research`:

`product_refs/shilasource-himalayan-shilajit-resin.label.json`

That file's `source` is a `scripts/tools/label_ocr.swift` read of the live PDP pack shot on 2026-10-08. `scripts/shilasource_resin_rules.py` reads `required` and `optional` only. The `source` note is provenance and is not an allow-list. There is no `accepted_ocr` key (Shockwave and Gold Resin files from 2026-10-09 have one; this file does not).

Whitelist lines today:

- required: `ShilaSource`, `Himalayan`, `Shilajit`, `Resin`, `75`, `Dietary Supplement`
- optional: `Wellness`, `Nest`, `70% Fulvic Acid*`, `Lab-Tested for Purity*`, `1.06oz (30g)`, `SERVINGS`, `Servings`

Allowed dose phrases are parsed from those lines. Today that is `70%`, `1.06 oz`, `30 g`, and `75 servings`. The servings badge was stored as the separate lines `75` and `SERVINGS` / `Servings`. A line that is only a number, together with a line that is only the word servings, is that serving count. No other number is joined to that word. If a token is added to the file later, that token is allowed. If the file is missing or empty, in-scope copy fails closed.

No milligram token is in `required` or `optional`. Do not add one.

Copy that names ShilaSource or `shilasource-himalayan-shilajit-resin` may repeat the whitelist lines, including `70% Fulvic Acid*`, `1.06oz (30g)`, and `75 servings`. It fails closed when it states any of the following and that dose phrase is not parsed from the whitelist lines:

- a milligram amount (`500 mg`, `300 mg`, `400 mg`, `250 milligrams`, `1,500 mg`, `75 mg`)
- a different serving count (`30 servings`, `60 servings`, `175 servings`, servings per jar 30)
- a different fulvic percentage (`75%`, `80%`, `7.5%`)
- a different volume or weight (`1 fl oz`, `1.06 fl oz`, `30 ml`, `2 oz`, `5 g`, `0.4 g`)
- a day-supply (`30-day supply`, `75-day supply`)
- a mineral count (`85 minerals`, `85+ trace minerals`, `40 minerals`)
- another dose the file does not list (micrograms, IU, CFU, counted drops or droppers, a gummy count)

Bare "shilajit resin" or "Himalayan shilajit resin" without ShilaSource or this handle is out of scope. Premium Himalayan Shilajit Gummies, Shilajit Shockwave, Pure Shilajit Gold Resin, AgeAura, and FloraFresh are not this product: copy that names only those SKUs is out of scope.

`brand_rules.assess()` merges these violations, so every `brand_rules` caller enforces them: `lint_tickets.py` (open tickets only), `validate_article.py`, `validate_landing.py` / `landing_render.py` / `landing_publisher.py` (through `brand_rules.spec_violations()`), `topic_fitness.py` (`FAIL [shilasource-resin-label]`), the ticket and landing builders, image prompts, and `shopify_publisher.py` (publish and update abort). `refill_tickets.py` adds the pack-label line to every ShilaSource resin ticket. `build_landing_tickets.py` adds a label note to ShilaSource resin landing briefs. AgeAura rules are unchanged (NMN + TMG only). FloraFresh rules are unchanged (SNZ-1969, 1 billion CFU). Shockwave rules are unchanged (identity lines only; no milligram, serving count, or volume token).

Negations ("not a milligram amount") and another brand's row ("Brand X | 500 mg") pass. A study sentence that states a trial dose passes when it does not name ShilaSource. A sentence that names ShilaSource and states a milligram, a different serving count, or a different fulvic percentage does not.

```bash
python3 -m unittest tests/test_shilasource_resin_guard.py
python3 scripts/shilasource_resin_rules.py --brief
python3 scripts/shilasource_resin_rules.py --spec landing_drafts/<slug>.json
```

## OCR gap that should block a later milligram allow-list

The side panel on `product_refs/shilasource-himalayan-shilajit-resin.png` (Direction for Use / Supplement Facts area) was not transcribed into this label file. `required` and `optional` have no serving-size line, no milligram amount, and no mineral count. This guard fails those claims closed. Do not add them from the PDP description, from an older article, or from a visual guess. A milligram or Supplement Facts claim can be allow-listed only after a new confidence-1.00 `label_ocr.swift` read is copied verbatim into `required` or `optional` (misreads omitted, not corrected). Until that read exists, merging a change that allows a milligram dose is blocked.

The 2026-10-08 file also has no `accepted_ocr` array. That is a provenance gap next to the Shockwave and Gold Resin files. It does not by itself block this fail-closed guard.

## Left as they are

- No Shopify write, no PDP edit, no publish, no theme or robots change.
- The whitelist was not given a milligram token, a serving-size gram amount, or a mineral count.
- The split `75` and `SERVINGS` lines were not rewritten into one new OCR line.
- Gummies, Shockwave, and Gold Resin were not given a new formula guard in this change.

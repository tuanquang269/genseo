# Pure Shilajit Gold Resin pack-label guard

The pack-label whitelist is the source of truth for this one product (`https://wellnessnest.co/products/pure-shilajit-gold-resin`):

`product_refs/pure-shilajit-gold-resin.label.json`

OCR-accepted lines in that file's `required` list: `wellness`, `nest`, `Himalayan`, `Shilajit`, `75% Fulvic`, `Lab-Tested`, `Acid`, `Pure Shilajit Gold Resin`, `1.06 oz (30g) - 75 servings`, `Dietary Supplements`. `optional` is empty. The file was read with `scripts/tools/label_ocr.swift` on 2026-10-09. `required` and `accepted_ocr` are confidence-1.00 lines copied verbatim.

No milligram serving was read. Do not add one. Second-jar misreads were omitted, not corrected (`tor Purity`; `Dietary Sepplements`; `1.06 oz (S0g)-75 serviogs`). Those strings are not whitelist lines. The mark was not confirmed, so the guard does not require a trademark glyph.

`scripts/gold_resin_rules.py` reads `required` and `optional` only. The file's `source` note is provenance and is not an allow-list. Allowed dose phrases are parsed from those lines. Today that is `75%`, `1.06 oz`, `30 g`, and `75 servings`. If a token is added to the file later, that token is allowed. If the file is missing or empty, in-scope copy fails closed.

Copy that names Pure Shilajit Gold Resin, Shilajit Gold Resin, or `pure-shilajit-gold-resin` may repeat the whitelist lines, including the exact OCR serving line and `75% Fulvic`. It fails closed when it states any of the following and that dose phrase is not parsed from the whitelist lines:

- a milligram amount (`500 mg`, `250 milligrams`, `1,500 mg`)
- a different serving count (`30 servings`, `60 servings`, servings per jar 30)
- a different volume or weight (`1 fl oz`, `30 ml`, `2 oz`, `5 g`, `106 oz`)
- a day-supply (`30-day supply`, `75-day supply`)
- another dose the file does not list (micrograms, IU, CFU, counted drops or droppers, a gummy count, a different fulvic percentage)

Bare "gold resin" without the product name or the handle is out of scope. Premium Himalayan Shilajit Gummies, Shilajit Shockwave, ShilaSource resin, AgeAura, and FloraFresh are not this product: copy that names only those SKUs is out of scope.

`brand_rules.assess()` merges these violations, so every `brand_rules` caller enforces them: `lint_tickets.py` (open tickets only), `validate_article.py`, `validate_landing.py` / `landing_render.py` / `landing_publisher.py` (through `brand_rules.spec_violations()`), `topic_fitness.py` (`FAIL [gold-resin-label]`), the ticket and landing builders, image prompts, and `shopify_publisher.py` (publish and update abort). `refill_tickets.py` adds the pack-label line to every Gold Resin ticket. `build_landing_tickets.py` adds a label note to Gold Resin landing briefs. AgeAura rules are unchanged (NMN + TMG only). FloraFresh rules are unchanged (SNZ-1969, 1 billion CFU). Shockwave rules are unchanged (identity lines only; no milligram, serving count, or volume token).

Negations ("not a milligram amount") and another brand's row ("Brand X | 500 mg") pass. A study sentence that states a trial dose passes when it does not name this resin. A sentence that names this resin and states a milligram, a different serving count, or a different volume does not.

```bash
python3 -m unittest tests/test_gold_resin_guard.py
python3 scripts/gold_resin_rules.py --brief
python3 scripts/gold_resin_rules.py --spec landing_drafts/<slug>.json
```

## Left as they are

- No Shopify write, no PDP edit, no theme or robots change.
- The whitelist was not given a milligram token.
- The omitted second-jar misreads were not corrected into the file.
- Gummies, Shockwave, and ShilaSource resin were not given a new formula guard in this change. Turkesterone Advanced Formula has its own pack-label guard: `docs/TURKESTERONE_LABEL_GUARD.md`.

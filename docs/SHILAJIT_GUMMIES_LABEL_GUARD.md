# Premium Himalayan Shilajit Gummies pack-label guard (2026-10-10)

The pack-label whitelist is the source of truth for this one product (`https://wellnessnest.co/products/premium-himalayan-shilajit-gummies`):

`product_refs/premium-himalayan-shilajit-gummies.label.json`

Optional lines in that file include `60 GUMMIES`, `60-DAY SUPPLY`, `1500mg Shilajit`, `75% Fulvic Acid`, `85+ Trace Minerals`, `ASHWAGANDHA`, `GOKSHURA`, and `BLACK MUSLI`. The file was read off the pack shot with `scripts/tools/label_ocr.swift` on 2026-10-08. It does not include a 30-serving panel, a 2-gummy serving, or `150 mg`.

Copy that names Premium Himalayan Shilajit Gummies may say **60 gummies** and a **60-day supply**. It fails closed when it states any of the following and that exact token is not in the whitelist file:

- a pack count other than 60 (including 30 gummies, 84 gummies, or 2 gummies a day)
- **30 servings**, servings per container 30, or any other serving count
- a day-supply other than 60 (a 60-day trial is not a supply claim)
- **150 mg**, **250 mg**, **500 mg**, or any other milligram amount (`1500mg` / `1,500 mg` passes because `1500mg Shilajit` is a whitelist line; `150 mg` does not match that longer number)

`scripts/shilajit_gummies_rules.py` reads the file on each check. If a token is added to the file later, that token is allowed. If the file is missing or no longer names a gummy count, pack-count claims fail closed. Shockwave, Pure Shilajit Gold Resin, and ShilaSource resin are not this product: copy that names only those SKUs is out of scope.

`brand_rules.assess()` merges these violations, so every `brand_rules` caller enforces them: `lint_tickets.py` (open tickets only), `validate_article.py`, `validate_landing.py` / `landing_render.py` / `landing_publisher.py` (through `brand_rules.spec_violations()`), `topic_fitness.py` (`FAIL [shilajit-gummies-label]`), the ticket and landing builders, image prompts, and `shopify_publisher.py` (publish and update). `refill_tickets.py` adds the pack-label line to every Shilajit gummies ticket. `build_landing_tickets.py` adds a label note to Shilajit gummies landing briefs. AgeAura rules are unchanged (NMN + TMG only). FloraFresh count is 15B CFU of SNZ-1969 per 2 gummies (Kevin 2026-10-21). 1 billion CFU and 1B CFU are retired. This PR does not edit florafresh_rules.py.

Negations ("not a 30-serving panel") and another brand's row ("Brand X | 30 servings") pass. A study sentence that states a trial dose ("the trial used 250 mg") passes when it does not claim that dose for this product. A sentence that names this product and states 150 mg or 30 servings does not. Chart sources that cite a trial dose pass; a chart source that is only "250 mg per serving" does not.

```bash
python3 -m unittest tests/test_shilajit_gummies_guard.py
python3 scripts/shilajit_gummies_rules.py --brief
python3 scripts/shilajit_gummies_rules.py --spec landing_drafts/<slug>.json
```

## Left as they are

- No Shopify write, no PDP edit, no theme or robots change.
- `landing_drafts/shilajit-gummies-listicle-261008.json` still states 30 servings, 150 mg, and a 2-gummy serving. Those tokens are not in the whitelist file. `brand_rules` now rejects that copy. The draft was not rewritten here.
- Shockwave, Gold Resin, and ShilaSource resin were not given a formula guard in this change.

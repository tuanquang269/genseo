# Premium Himalayan Shilajit Gummies pack-label guard (2026-10-10)

The pack-label whitelist is the source of truth for this one product (`https://wellnessnest.co/products/premium-himalayan-shilajit-gummies`):

`product_refs/premium-himalayan-shilajit-gummies.label.json`

Optional lines in that file include `60 GUMMIES`, `60-DAY SUPPLY`, `1500mg Shilajit`, `75% Fulvic Acid`, `85+ Trace Minerals`, `ASHWAGANDHA`, `GOKSHURA`, and `BLACK MUSLI`. The file was read off the pack shot with `scripts/tools/label_ocr.swift` on 2026-10-08. It does not include a 30-serving panel, a 2-gummy serving, or `150 mg`.

The product is in scope under the full name, **Himalayan Shilajit Gummies**, **Shilajit Gummies**, or **Shilajit Gummies for Men**, with or without the handle. Shockwave, Pure Shilajit Gold Resin, and ShilaSource resin are still out of scope.

Copy that names this product may say **60 gummies** and a **60-day supply**. It fails closed when it states any of the following and that exact token is not in the whitelist file:

- a pack count other than 60 (including 30 gummies, 84 gummies, or 2 gummies a day)
- **30 servings**, servings per container 30, or any other serving count, including counts written as words (`twenty servings`, `forty servings`, `fifteen servings`, `thirty servings`)
- a day-supply other than 60 (a 60-day trial is not a supply claim)
- **150 mg**, **250 mg**, **500 mg**, or any other milligram amount (`1500mg` / `1,500 mg` passes because `1500mg Shilajit` is a whitelist line; `150 mg` does not match that longer number)
- a gram amount the file does not list, including **0.25 g**, **1.5 grams**, and **five grams**

`scripts/shilajit_gummies_rules.py` reads the file on each check. If a token is added to the file later, that token is allowed. If the file is missing or no longer names a gummy count, pack-count claims fail closed. Shockwave, Pure Shilajit Gold Resin, and ShilaSource resin are not this product: copy that names only those SKUs is out of scope.

`brand_rules.assess()` merges these violations, so every `brand_rules` caller enforces them: `lint_tickets.py` (open tickets only), `validate_article.py`, `validate_landing.py` / `landing_render.py` / `landing_publisher.py` (through `brand_rules.spec_violations()`), `topic_fitness.py` (`FAIL [shilajit-gummies-label]`), the ticket and landing builders, image prompts, and `shopify_publisher.py` (publish and update). `refill_tickets.py` adds the pack-label line to every Shilajit gummies ticket. `build_landing_tickets.py` adds a label note to Shilajit gummies landing briefs. AgeAura rules are unchanged (NMN + TMG only). FloraFresh count is 15B CFU of SNZ-1969 per 2 gummies (Kevin 2026-10-21). This change does not edit florafresh_rules.py.

Negations ("not a 30-serving panel", "Do not claim 150 mg") and another brand's row ("Brand X | 30 servings") pass. A denial ends at `and` or a new delivery verb, and bare `no` or `without` also ends at a comma, so `no fillers and deliver 250 mg`, `is not a stimulant and delivers 250 mg`, `without fillers delivers 150 mg`, and `no fillers, 250 mg` fail. `no 250 mg` and `Do not claim 30 servings or 150 mg` stay denials. A study sentence that states a trial dose ("The Pandit trial used 250 mg of purified shilajit") passes when that dose is not this product's claim. The sentence right after the product name does not pass (`were studied. Participants took 250 mg.`), even when the previous sentence says trial or studied, and even when that next sentence does not start with It or pouch. A different study's dose with a sentence in between stays allowed. A sentence that names this product and states 150 mg, 30 servings, 0.25 g, or 1.5 grams does not. Chart sources that cite a trial dose pass; a chart source that is only "250 mg per serving" does not.

```bash
python3 -m unittest tests/test_shilajit_gummies_guard.py
python3 scripts/shilajit_gummies_rules.py --brief
python3 scripts/shilajit_gummies_rules.py --spec landing_drafts/<slug>.json
```

## Left as they are

- No Shopify write, no PDP edit, no theme or robots change.
- `landing_drafts/shilajit-gummies-listicle-261008.json` still states 30 servings, 150 mg, and a 2-gummy serving. Those tokens are not in the whitelist file. `brand_rules` now rejects that copy. The draft was not rewritten here.
- Shockwave, Gold Resin, and ShilaSource resin were not given a formula guard in this change.

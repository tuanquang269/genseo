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

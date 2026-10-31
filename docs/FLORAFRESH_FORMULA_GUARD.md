# FloraFresh formula guard (2026-10-09, count updated 2026-10-21)

The Supplement Facts label is the source of truth for FloraFresh (`https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies`). Kevin confirmed the label image on 2026-10-09 and set the probiotic count on 2026-10-21:

- per 2 gummies: SNZ-1969 Probiotic Blend (Bacillus coagulans, spore-based) 15B CFU, Vitamin C 30 mg, Pineapple Fruit Powder 100 mg (with bromelain)
- sweetened with maltitol and isomalt, so not sugar-free
- badges: Allergen Free, Vegan, Halal, Gluten Free
- 15 billion CFU is the same count. 1 billion CFU and 1B CFU are the retired count and the linter rejects them.

The live PDP description still tells a wrong strain story: four Lactobacillus strains (rhamnosus, reuteri, salivarius, gasseri), XOS, D-mannose, and sugar-free. Until Kevin gives a GO for a store rewrite, tickets, landing pages, articles, and image prompts cite the label, never the PDP description. A PDP/label mismatch is a gate failure. The 2026-10-09 note recorded the PDP's "15 billion CFU" sentence as the wrong formula because it was bundled with that strain story. The count itself is now 15B CFU.

The label facts live in `scripts/florafresh_rules.py`. `product_refs/florafresh-vaginal-probiotics-gummies.label.json` is a separate front-of-pouch OCR whitelist (2026-10-09). It does not contain the strain or CFU. Do not copy the Supplement Facts formula into that file unless a later OCR read shows the text letter-perfect. `brand_rules.assess()` merges its violations, so every `brand_rules` caller enforces it: `lint_tickets.py` (open tickets only), `validate_article.py`, `validate_landing.py` / `landing_render.py` / `landing_publisher.py` (through `brand_rules.spec_violations()`), `topic_fitness.py` (`FAIL [florafresh-formula]`), the ticket and landing builders, `article_images.py` / `ad_assets.py`, and `shopify_publisher.py` (publish and update). `refill_tickets.py` adds the label formula line to every FloraFresh ticket, `build_landing_tickets.py` adds a label-only note to FloraFresh landing briefs, and both runner prompts carry the rule. AgeAura rules are unchanged (NMN + TMG only).

Copy that names FloraFresh fails when it claims 1 billion CFU or 1B CFU, four Lactobacillus strains, any Lactobacillus or other non-label organism, XOS, D-mannose, a prebiotic, more than one strain, a CFU figure other than 15B CFU per 2 gummies (half of that per gummy is 7.5 billion), or sugar-free, or when it takes strains/CFU from the PDP. A leading "Compare" does not excuse FloraFresh's own retired count. Research copy about other strains, negations ("not sugar-free"), and comparisons with other brands pass. Landing-spec provenance notes (`source`, `*_source`, `image_note`, `sources`) may record what the PDP says.

```bash
python3 -m unittest tests/test_florafresh_guard.py
python3 scripts/florafresh_rules.py --brief                  # the label formula line for briefs
python3 scripts/florafresh_rules.py --spec landing_drafts/<slug>.json
```

## Left for a Kevin GO

- The PDP description, theme, and store settings were not edited.
- 11 of the 12 live articles that name FloraFresh repeat the PDP formula (storefront scan, 2026-10-09). They stay live and unedited (runner rule E). `shopify_publisher.py update` now refuses them until their FloraFresh copy follows the label:
  - `best-time-to-take-vaginal-probiotics-6-rules-us-2026`
  - `florafresh-for-women-over-50-what-changes-us-2026`
  - `florafresh-gummies-vs-capsules-5-format-facts-us-2026`
  - `florafresh-vs-generic-probiotics-4-strain-facts-us-2026`
  - `probiotics-after-antibiotics-for-women-when-to-start-us`
  - `probiotics-and-birth-control-can-you-take-both-us-2026`
  - `probiotics-during-your-period-keep-taking-them-us-2026`
  - `probiotics-for-bv-do-they-actually-work-us-2026`
  - `vaginal-probiotics-how-long-until-they-work-us-2026`
  - `vaginal-probiotics-side-effects-normal-vs-stop-us-2026`
  - `vaginal-probiotics-which-strains-actually-work-us-2026`
- DONE tickets in `daily-tickets.md` stay as they are. On 2026-10-09 the open FloraFresh tickets, `board/ideas.csv`, and the topic bank were moved off the PDP formula. On 2026-10-21 those generators and the still-open tickets were moved to 15B CFU. Historical landing drafts that still say 1 billion CFU (including `landing_drafts/florafresh-listicle-261009.json`) were not rewritten; `florafresh_rules.py --spec` on that file now exits 1.
- The 11 live articles above were not edited. As of the 2026-10-09 scan they repeated the PDP strain story. Whether a live post also says 1 billion CFU is a separate report for Kevin; this change does not update Shopify.

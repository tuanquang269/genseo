# FloraFresh formula guard (2026-10-09)

The Supplement Facts label is the source of truth for FloraFresh (`https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies`). Kevin confirmed the label image on 2026-10-09:

- per 2 gummies: SNZ-1969 Probiotic Blend (Bacillus coagulans, spore-based) 1 billion CFU, Vitamin C 30 mg, Pineapple Fruit Powder 100 mg (with bromelain)
- sweetened with maltitol and isomalt, so not sugar-free
- badges: Allergen Free, Vegan, Halal, Gluten Free

The live PDP description is wrong. It says 15 billion CFU from four Lactobacillus strains (rhamnosus, reuteri, salivarius, gasseri), XOS, D-mannose, and sugar-free. Until Kevin gives a GO for a store rewrite, tickets, landing pages, articles, and image prompts cite the label, never the PDP description. A PDP/label mismatch is a gate failure.

The label facts live in `scripts/florafresh_rules.py`. `brand_rules.assess()` merges its violations, so every `brand_rules` caller enforces it: `lint_tickets.py` (open tickets only), `validate_article.py`, `validate_landing.py` / `landing_render.py` / `landing_publisher.py` (through `brand_rules.spec_violations()`), `topic_fitness.py` (`FAIL [florafresh-formula]`), the ticket and landing builders, `article_images.py` / `ad_assets.py`, and `shopify_publisher.py` (publish and update). `refill_tickets.py` adds the label formula line to every FloraFresh ticket, `build_landing_tickets.py` adds a label-only note to FloraFresh landing briefs, and both runner prompts carry the rule. AgeAura rules are unchanged (NMN + TMG only).

Copy that names FloraFresh fails when it claims 15 billion CFU, four Lactobacillus strains, any Lactobacillus or other non-label organism, XOS, D-mannose, a prebiotic, more than one strain, a CFU figure other than the label's, or sugar-free, or when it takes strains/CFU from the PDP. Research copy about other strains, negations ("not sugar-free"), and comparisons with other brands pass. Landing-spec provenance notes (`source`, `*_source`, `image_note`, `sources`) may record what the PDP says.

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
- DONE tickets in `daily-tickets.md` stay as they are. The open FloraFresh tickets (#CA1009-2, #CA1009-8, #MB1009-7), `board/ideas.csv`, and the topic bank were moved to the label formula.

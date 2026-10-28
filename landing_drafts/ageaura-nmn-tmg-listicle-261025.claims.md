# Claims log: AgeAura NMN + TMG listicle

Fetched: 2026-10-25. Product: `ageaura-pure-nmn-tmg-nad-complex`.

| Claim | Source | How verified |
|---|---|---|
| AgeAura product identity is Pure NMN + TMG NAD+ Complex | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Live PDP and `/products/<handle>.js` fetched this run; `scripts/ageaura_rules.py --brief` checked the handle allowlist. |
| PDP one-time price is $79.99 | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.js | Re-fetched 2026-10-26; variant price was `7999`. compare_at_price is null. |
| Automatic Refill | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.js | Re-fetched 2026-10-26. One-time $79.99 (variant price 7999, compare_at_price null). Automatic Refill every 30 days $59.99 (plan 10022551867), every 60 days $54.99 (plan 10022584635), every 90 days $49.99 (plan 10022617403). Card shows $59.99/bottle for 1 bottle every 30 days. The note prices 2 bottles at $54.99/bottle every 60 days and 3 bottles at $49.99/bottle every 90 days. Sticky says "$59.99/bottle every 30 days". Plan descriptions say pause or cancel anytime. |
| PDP lists 500 mg NMN and 250 mg TMG per daily serving | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | PDP HTML fetched this run; amounts kept in product and offer blocks only. |
| Product label states 60 Capsules and 30 Servings | `product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json` | Existing OCR-accepted label record; no dosage claim added to narrative. |
| Huang trial tested NMN in 66 adults aged 40 to 65 for 60 days; serum NAD+/NADH rose 38% from baseline in the NMN group and 14.3% in placebo | https://doi.org/10.3389/fragi.2022.851698 | Europe PMC core record fetched this run; figures copied from abstract. |
| Morifuji trial tested NMN in 60 older adults for 12 weeks and distinguished a non-significant primary stepping test from secondary outcomes | https://doi.org/10.1007/s11357-024-01204-1 | Europe PMC core record fetched this run; abstract distinguishes primary and secondary outcomes. |
| Olthof trial tested betaine separately in four groups of 19 healthy adults for six weeks | https://doi.org/10.1093/jn/133.12.4135 | Europe PMC core record fetched this run; abstract reports groups, duration and homocysteine outcome. |
| No combined NMN + TMG human trial found in targeted search | https://europepmc.org/search?query=nicotinamide%20mononucleotide%20trimethylglycine | Europe PMC search fetched this run; no combined human-trial record found. Framed as an evidence gap, not proof of impossibility. |
| TrustScore 4.2, 1,144 reviews, and three service reviews | `state/trustpilot/wellnessnest.json`, https://www.trustpilot.com/review/wellnessnest.co | State file available locally and fetched wrapper timestamp is 2026-10-24; quotes copied verbatim, all 5-star URLs retained. Reviews describe service/subscription only, not product efficacy. |
| 90-day guarantee and free shipping over $69 | Live PDP and https://wellnessnest.co/policies/refund-policy | Published store language used; no stronger promise added. |

## Deliberately left out

- No claim that NMN + TMG works better together. No combined human trial was found.
- No claim that NMN increases energy, reverses aging, extends life, treats disease, or improves cognition. PDP marketing language is not presented as clinical evidence.
- No TMG claim about NAD+ production. The betaine study was separate and measured homocysteine.
- No dosage-with-units in numbered narrative rows. Amounts appear only in product and offer blocks sourced to the PDP.
- No expert quote, countdown, scarcity, fake urgency, or fabricated review.
- No COA, laboratory-testing, purity, or third-party-verification claim.
- No competitor, forbidden AgeAura handle, or alternate AgeAura product.

## Image QA

- All images generated foreground-only with `scripts/article_images.py --square --qc`; no-face editorial scenes passed QC.
- `avatar.webp`, `row01-form-r2.webp`, `row02-panel-r2.webp`, `row03-human-r2.webp`, `row04-outcomes.webp`, `row06-gap.webp`, and `row07-routine.webp` passed no-face QC.
- `hero.webp`, `offer-r2.webp`, and `bridge.webp` use the real AgeAura cutout as reference and passed `scripts/landing_label_gate.py` on 2026-10-25.
- `expert` uses the passed `hero.webp`; the failed `expert-r2.webp` is not referenced.
- No generated image is reused by numbered rows. Each numbered row has its own image.

## Price correction 2026-10-26

Re-fetched public product JSON on 2026-10-26 at 2026-10-26T01:40:31Z.

Removed from this draft: No change to the one-time $79.99 or the 30-day $59.99. The sticky line said "From $59.99", and the 60-day and 90-day plans were not on the card.

Now stated: One-time $79.99 (variant price 7999, compare_at_price null). Automatic Refill every 30 days $59.99 (plan 10022551867), every 60 days $54.99 (plan 10022584635), every 90 days $49.99 (plan 10022617403). Card shows $59.99/bottle for 1 bottle every 30 days. The note prices 2 bottles at $54.99/bottle every 60 days and 3 bottles at $49.99/bottle every 90 days. Sticky says "$59.99/bottle every 30 days".

Source: https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.js fetched 2026-10-26 at 2026-10-26T01:40:31Z. One-time price also matched https://wellnessnest.co/collections/all/products.json.

## Mac re-check 2026-10-26

Same Mac re-check as the AgeAura product JSON: per-bottle prices, 1/2/3 bottles on the 30/60/90-day plans. The page now says that.

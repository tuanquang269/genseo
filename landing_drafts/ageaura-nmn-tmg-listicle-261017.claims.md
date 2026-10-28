# Claims log: AgeAura NMN + TMG listicle

Fetched: 2026-10-17. Product: `ageaura-pure-nmn-tmg-nad-complex`.

| Claim | Source | How verified |
|---|---|---|
| AgeAura product identity is Pure NMN + TMG NAD+ Complex | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Live PDP and `/products/<handle>.js` fetched this run; handle allowlist checked with `scripts/ageaura_rules.py`. |
| PDP one-time price is $79.99 | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.js | One-time $79.99 (variant price 7999, compare_at_price null). Automatic Refill every 30 days $59.99 (plan 10022551867), every 60 days $54.99 (plan 10022584635), every 90 days $49.99 (plan 10022617403). Card shows $59.99/bottle for 1 bottle every 30 days. The note prices 2 bottles at $54.99/bottle every 60 days and 3 bottles at $49.99/bottle every 90 days. Sticky says "$59.99/bottle every 30 days". |
| Automatic Refill | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.js | The 2026-10-17 every-four-weeks 15% plan is not in the 2026-10-26 JSON. One-time $79.99 (variant price 7999, compare_at_price null). Automatic Refill every 30 days $59.99 (plan 10022551867), every 60 days $54.99 (plan 10022584635), every 90 days $49.99 (plan 10022617403). Card shows $59.99/bottle for 1 bottle every 30 days. The note prices 2 bottles at $54.99/bottle every 60 days and 3 bottles at $49.99/bottle every 90 days. Sticky says "$59.99/bottle every 30 days". |
| PDP lists 500 mg NMN and 250 mg TMG per daily serving | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | PDP HTML fetched this run; amounts kept in product and offer blocks only. |
| Product label states 60 Capsules and 30 Servings | `product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json` | Existing OCR-accepted label record; no dosage claim added to narrative. |
| Huang trial tested NMN in 66 adults aged 40 to 65 for 60 days; NAD+/NADH rose 38% from baseline in the NMN group and 14.3% in placebo | https://doi.org/10.3389/fragi.2022.851698 | Europe PMC core record fetched this run; figures copied from abstract. |
| Morifuji trial tested NMN in 60 older adults for 12 weeks; four-meter walk result differed, primary stepping test did not | https://doi.org/10.1007/s11357-024-01204-1 | Europe PMC core record fetched this run; abstract distinguishes primary and secondary outcomes. |
| Olthof trial tested betaine separately in healthy adults for six weeks | https://doi.org/10.1093/jn/133.12.4135 | Europe PMC core record fetched this run; abstract reports four groups and fasting homocysteine findings. |
| No combined NMN + TMG human trial found in targeted search | https://europepmc.org/search?query=nicotinamide%20mononucleotide%20trimethylglycine | Europe PMC search fetched this run; zero hits for title/abstract query. Framed as an evidence gap, not proof of impossibility. |
| TrustScore 4.2, 1,144 reviews, and three service reviews | `state/trustpilot/wellnessnest.json`, https://www.trustpilot.com/review/wellnessnest.co | State file fetched at `2026-10-17T02:30:17Z`; quotes copied verbatim, all 5-star URLs retained. Reviews describe service/subscription only, not product efficacy. |
| 90-day guarantee and free shipping over $69 | Live PDP and https://wellnessnest.co/policies/refund-policy | PDP/policy HTML fetched this run; wording limited to published store language. |

## Deliberately left out

- No claim that NMN + TMG works better together. No combined human trial was found.
- No claim that NMN increases energy, reverses aging, extends life, treats disease, or improves cognition. The label's marketing phrases are not presented as clinical findings.
- No TMG claim about NAD+ production. The betaine study was separate and measured homocysteine.
- No expert quote, invented testimonial, countdown, scarcity, fake rating, or fabricated review.
- No COA, laboratory-testing, purity, or third-party-verification claim. PATI rules prohibit presenting those as an AgeAura advantage.
- No dosage-with-units in numbered narrative rows. Amounts appear only in product/offer copy sourced to the PDP.
- No competitor, Urolithin A, peptide, or alternate AgeAura handle.

## Image QA

- All images generated foreground-only with `scripts/article_images.py --square --qc`; no-face editorial scenes passed QC.
- `hero.webp`, `offer.webp`, `expert.webp`, and `bridge.webp` composite the real `product_refs/ageaura-pure-nmn-tmg-nad-complex-cutout.png`.
- `scripts/landing_label_gate.py` returned `LABEL PASS` for all four pack images on 2026-10-17.
- 2x mark crop visually matches the cutout's black stacked S-curved mark and vertical Wellness Nest wordmark.
- No generated image used twice for numbered rows. Every numbered row has a distinct image.

## Price correction 2026-10-26

Re-fetched public product JSON on 2026-10-26 at 2026-10-26T01:40:31Z.

Removed from this draft: One-time $69.95 and Subscribe & Save every four weeks at $59.46 (old plan 9884729659, 15% adjustment).

Now stated: One-time $79.99 (variant price 7999, compare_at_price null). Automatic Refill every 30 days $59.99 (plan 10022551867), every 60 days $54.99 (plan 10022584635), every 90 days $49.99 (plan 10022617403). Card shows $59.99/bottle for 1 bottle every 30 days. The note prices 2 bottles at $54.99/bottle every 60 days and 3 bottles at $49.99/bottle every 90 days. Sticky says "$59.99/bottle every 30 days".

Source: https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.js fetched 2026-10-26 at 2026-10-26T01:40:31Z. One-time price also matched https://wellnessnest.co/collections/all/products.json.

## Mac re-check 2026-10-26

Same Mac re-check as the AgeAura product JSON above: per-bottle prices, 1/2/3 bottles on the 30/60/90-day plans. The page now says that.

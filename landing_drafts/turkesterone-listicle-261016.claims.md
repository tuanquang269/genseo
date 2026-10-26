# Claims log: Turkesterone listicle

| Claim | Source | How verified |
|---|---|---|
| Acute human study enrolled 11 healthy men and measured IGF-1 and resting metabolic rate at baseline, 3 hours, and 24 hours | [Harris et al., Muscles 2024](https://doi.org/10.3390/muscles3040031) | Europe PMC record and abstract fetched 2026-10-16 |
| The acute study reported no significant condition, time, or interaction effects | [Harris et al., Muscles 2024](https://doi.org/10.3390/muscles3040031) | Europe PMC abstract fetched 2026-10-16 |
| Ecdysterone and turkesterone are distinct compounds discussed in the evidence review | [Wozniak et al., Nutrients 2024](https://doi.org/10.3390/nu16091382) | DOI source listed in Europe PMC search and reviewed for compound distinction |
| 2025 preclinical paper studied *Caenorhabditis elegans*, not people | [IJMS 2025](https://doi.org/10.3390/ijms26083739) | Europe PMC search record fetched 2026-10-16 |
| Product price, compare-at price, title, image, and absence of selling plans | [Live PDP JSON](https://wellnessnest.co/products/turkesterone-advanced-formula.js) | Live PDP JSON fetched 2026-10-16 |
| Pack wording: wellness, nest, PREMIUM, TURKESTERONE, ADVANCED, FORMULA, AMPLIFY, MUSCLE, ENDURANCE, 60, Dietary Supplement, Capsules | `product_refs/turkesterone-advanced-formula.label.json` | Existing OCR-approved label file read 2026-10-16 |
| TrustScore, review count, and verbatim service reviews | `state/trustpilot/wellnessnest.json` | Refreshed file fetched 2026-10-16; only 4 to 5 star service reviews used |

## Deliberately omitted

- No milligram amount, serving count, day-supply, or Supplement Facts claim: the label file does not provide them.
- No product-effect claim from the PDP description: PDP marketing copy was not used as evidence.
- No claim that ecdysterone findings are turkesterone findings.
- No claim that animal or laboratory work predicts human muscle growth.
- No claim that the exact product has been tested in a human trial.
- No label-gate PASS claim: generated pack scenes failed OCR checks and the available real PDP asset is used instead.

## Price correction 2026-10-26

Re-fetched public product JSON on 2026-10-26 at 2026-10-26T01:40:31Z.

Removed from this draft: No price change. The 2026-10-16 figures still match.

Now stated: One-time $75.00 (price 7500). Compare-at $119.98 (compare_at_price 11998). selling_plan_groups is empty. quantity_price_breaks empty.

Source: https://wellnessnest.co/products/turkesterone-advanced-formula.js fetched 2026-10-26 at 2026-10-26T01:40:31Z. One-time price also matched https://wellnessnest.co/collections/all/products.json.

## Mac re-check 2026-10-26

Turkesterone re-checked on this Mac against https://wellnessnest.co/products/turkesterone-advanced-formula.js and products.json. Price 7500, compare_at 11998, selling_plan_groups empty. No customer-facing price line was changed.

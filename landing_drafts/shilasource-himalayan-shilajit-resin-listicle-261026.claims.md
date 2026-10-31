# Claims log

| Claim | Source | How verified |
|---|---|---|
| Product name, image, one-time price, and refill pricing | `https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin.js`, fetched 2026-10-26 | Live Shopify product JSON. One-time price `$69.99`; Automatic Refill every 30 days `$49.99`. |
| Pack-label lines | `product_refs/shilasource-himalayan-shilajit-resin.label.json` | Existing OCR whitelist. Only required and optional lines used. No milligram claim or Supplement Facts panel added. |
| Product image | Live PDP image index 0 | Used the clean live PDP CDN image after generated pack shots and composites failed closed label verification. No generated pack image is listed in `pack_images`. |
| Human testosterone study | https://doi.org/10.1111/and.12482 | Europe PMC metadata fetched 2026-10-26, PMID 26395129. Copy limits result to the specified preparation, population, duration, and outcome. |
| Human strength study | https://doi.org/10.1186/s12970-019-0270-2 | Europe PMC metadata fetched 2026-10-26, PMID 30728074. Copy states protocol scope and does not generalize it to this resin. |
| Human skin study | https://doi.org/10.1080/07315724.2018.1564088 | Europe PMC metadata fetched 2026-10-26, PMID 31161927. Copy describes study scope without broadening the result. |
| Laboratory thallium survey | https://doi.org/10.1186/s13065-025-01384-7 | Europe PMC metadata fetched 2026-10-26, PMID 39827344. Copy says some samples, not every jar, and does not claim a product-specific result. |
| TrustScore, review count, and reviews | `state/trustpilot/wellnessnest.json`, fetched 2026-10-26 | TrustScore `4.2`, `1,144` reviews, and verbatim 5-star reviews with source URLs. Service and buying-experience comments are not presented as clinical evidence. |
| Money-back guarantee and shipping threshold | `https://wellnessnest.co/policies/refund-policy`, fetched 2026-10-26; live site text | Policy and site text checked. |

## Deliberately omitted

- No milligram amount, Supplement Facts panel, mineral count, or unsupported serving, weight, volume, fulvic percentage, or day-supply claim.
- No claim that the cited studies tested ShilaSource or this exact resin.
- No specific laboratory result, COA, purity advantage, or third-party testing advantage.
- No invented expert credentials, clinical quote, scarcity, countdown, or product-effect testimonial.
- No `pack_images` key: all generated pack compositions failed the required label gate, and the clean live PDP image is used instead.

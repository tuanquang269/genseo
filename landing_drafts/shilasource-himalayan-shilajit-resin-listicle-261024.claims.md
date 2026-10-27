# Claims log

| Claim | Source | How verified |
|---|---|---|
| ShilaSource product name, format, current one-time price, and refill pricing | `https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin.js`, fetched 2026-10-24 | Live Shopify product JSON. One-time price is $69.99; Automatic Refill every 30 days is $49.99. |
| Pack label lines | `product_refs/shilasource-himalayan-shilajit-resin.label.json` | Existing OCR whitelist. Only required and optional lines used. No milligram claim or Supplement Facts panel added. |
| Pack visuals | Live PDP image index 0 and `product_refs/shilasource-himalayan-shilajit-resin-cutout.png` | Generated images used the real cutout as reference. Every pack shot passed image QC. |
| Human testosterone study | https://doi.org/10.1111/and.12482 | Europe PMC metadata fetched 2026-10-24, PMID 26395129. Copy limits result to the specified preparation, population, and testosterone outcome. |
| Human strength study | https://doi.org/10.1186/s12970-019-0270-2 | Europe PMC metadata fetched 2026-10-24, PMID 30728074. Copy states the protocol scope and does not generalize it to this resin. |
| Human skin study | https://doi.org/10.1080/07315724.2018.1564088 | Europe PMC metadata fetched 2026-10-24, PMID 31161927. Copy describes study scope without broadening the result. |
| Laboratory thallium survey | https://doi.org/10.1186/s13065-025-01384-7 | Europe PMC metadata fetched 2026-10-24, PMID 39827344. Copy says some samples, not every jar, and does not claim a product-specific result. |
| TrustScore and review count | `state/trustpilot/wellnessnest.json`, fetched 2026-10-24 | TrustScore 4.2 and 1,144 reviews exactly as displayed. |
| Expert quote and three review cards | URLs in `expert` block; `state/trustpilot/wellnessnest.json` | Verbatim 5-star Trustpilot text, names and URLs preserved. Service/buying experience, not clinical evidence. |
| Money-back guarantee and shipping threshold | `https://wellnessnest.co/policies/refund-policy`, fetched 2026-10-24; live site ticker | Policy and site text checked. |

## Deliberately omitted

- No milligram amount, Supplement Facts panel, mineral count, or unsupported serving, weight, volume, fulvic percentage, or day-supply claim.
- No claim that the cited studies tested ShilaSource or this exact resin.
- No specific laboratory result, COA, purity advantage, or third-party testing advantage.
- No invented expert credentials, clinical quote, scarcity, countdown, or product-effect testimonial.
- Stale PDP HTML description pricing was omitted because current product JSON is the source used for the offer.

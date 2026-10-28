# Claims log

| Claim | Source | How verified |
|---|---|---|
| ShilaSource product name, format, current one-time price, and refill pricing | `https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin.js`, fetched 2026-10-24 | Re-fetched 2026-10-26. One-time $69.99 (variant price 6999). Automatic Refill every 30 days $49.99 (plan 10022748475), every 60 days $44.99 (plan 10022781243), every 90 days $39.99 (plan 10022814011). Card shows $49.99/jar for 1 jar every 30 days. The note prices 2 jars at $44.99/jar every 60 days and 3 jars at $39.99/jar every 90 days. Sticky says "$49.99/jar every 30 days" (not "From", because the 3-jar price is $39.99/jar). compare_at 9998 is not used as a strike price. quantity_price_breaks empty. Not stated: selling plan 9830990139, name "Delivery every 8 weeks", options include Product Quantity 2 and Order Frequency 8-week, adjustment value_type percentage value 19, allocation price 5669. Charge semantics are unclear, so the draft does not quote that plan. |
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

## Price correction 2026-10-26

Re-fetched public product JSON on 2026-10-26 at 2026-10-26T01:40:31Z.

Removed from this draft: Nothing in the one-time $69.99 or 30-day $49.99 figures. The sticky line said "From $49.99", which is not the lowest Automatic Refill price.

Now stated: One-time $69.99 (variant price 6999). Automatic Refill every 30 days $49.99 (plan 10022748475), every 60 days $44.99 (plan 10022781243), every 90 days $39.99 (plan 10022814011). Card shows $49.99/jar for 1 jar every 30 days. The note prices 2 jars at $44.99/jar every 60 days and 3 jars at $39.99/jar every 90 days. Sticky says "$49.99/jar every 30 days" (not "From", because the 3-jar price is $39.99/jar). compare_at 9998 is not used as a strike price. quantity_price_breaks empty.

Source: https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin.js fetched 2026-10-26 at 2026-10-26T01:40:31Z. One-time price also matched https://wellnessnest.co/collections/all/products.json and https://wellnessnest.co/collections/shilajit/products.json.
Not stated: selling plan 9830990139, name "Delivery every 8 weeks", options include Product Quantity 2 and Order Frequency 8-week, adjustment value_type percentage value 19, allocation price 5669. Charge semantics are unclear, so the draft does not quote that plan.

## Mac re-check 2026-10-26

ShilaSource prices re-checked on this Mac against https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin.js and products.json. Variant 6999. Plans 10022748475 / 10022781243 / 10022814011 allocate 4999 / 4499 / 3999 per jar. The 2026-10-23 pricing table maps 1/2/3 jars to every 30/60/90 days. The page now says that. Plan 9830990139 is still not quoted. compare_at 9998 is still not the strike price.

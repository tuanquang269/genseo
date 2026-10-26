# Claims log — turkesterone-listicle-261023

| Claim | Source | How verified |
|---|---|---|
| Turkesterone is an ecdysteroid plant compound, sourced from Ajuga turkestanica, marketed as a natural alternative to anabolic steroids | Todorova et al., Nutrients 2024, doi:10.3390/nu16091382 | Fetched abstract via Europe PMC REST API 2026-10-23; confirmed journal, year, authors |
| Turkesterone and ecdysterone are related but chemically distinct compounds; most published research covers ecdysterone | Todorova et al., Nutrients 2024, doi:10.3390/nu16091382 | Same abstract; review explicitly treats the two as distinct entries |
| 11 healthy men, single acute turkesterone dose, IGF-1 and resting metabolic rate measured at baseline, 3h, 24h, no statistically significant change vs placebo | Harris et al., Muscles 2024, doi:10.3390/muscles3040031 | Fetched abstract via Europe PMC REST API 2026-10-23; abstract states "failed to reveal any significant main condition, time, or interaction main effects for serum IGF-1, RMR, lipid, and carbohydrate metabolism (p > 0.05)" |
| Study is acute (single dose, 24h follow-up), not a long-term/daily-use trial; no strength or muscle-size outcome measured | Harris et al., Muscles 2024, doi:10.3390/muscles3040031 | Same abstract; explicitly "preliminary investigation" of a single/multiple acute dose, no training outcome reported |
| 2025 study tested maral root extract (contains turkesterone among other phytoecdysteroids) in C. elegans (roundworm), not humans | Todorova et al., IJMS 2025, doi:10.3390/ijms26083739 | Fetched abstract via Europe PMC REST API 2026-10-23; confirmed model organism and compound list (ecdysterone, ponasterone, turkesterone) |
| No published human trial of the combined multi-ingredient formula (turkesterone + ashwagandha + tongkat ali + colostrum + BioPerine) was found | Literature search, this run | Europe PMC search for the three cited DOIs only covers single-ingredient / single-compound studies; no combined-formula trial located |
| Pack front-of-pack text: wellness, nest, PREMIUM, TURKESTERONE, ADVANCED, FORMULA, AMPLIFY, MUSCLE, ENDURANCE, 60, Dietary Supplement, Capsules | product_refs/turkesterone-advanced-formula.label.json | RapidOCR dual-read (native + 2x), all lines in `required`/`accepted_ocr` agreed; no milligram token or Supplement Facts panel was read, and none is stated on the page |
| Price $75.00, compare-at $119.98, no Subscribe & Save selling plan | https://wellnessnest.co/products/turkesterone-advanced-formula.js | Fetched via WebFetch 2026-10-23 (direct curl hit a bot-check page; WebFetch returned raw JSON: price 7500, compare_at_price 11998, selling_plan_groups []) |
| 90-Day Money-Back Guarantee, refund request must be submitted within 90 days of delivery | https://wellnessnest.co/policies/refund-policy | Fetched via WebFetch 2026-10-23: "90-Day Money-Back Guarantee (MBG)"; "Your refund request must be submitted within 90 days from the delivery date." |
| Free shipping on orders over $69 | https://wellnessnest.co/policies/refund-policy | Fetched via WebFetch 2026-10-23: "Free Shipping on Orders Over $69" |
| TrustScore 4.2, 1,144 reviews; Tonya / Jindřich Pavlíček / Martin Mc Cartney JNR 5-star reviews verbatim | state/trustpilot/wellnessnest.json (fetched_at 2026-10-23T02:54:28.202Z) | Read file directly; quotes, names, TrustScore, and count copied exactly as stored (count written with comma per Trustpilot display) |

## Deliberately left out / cut
- No milligram amount, serving count, capsule-count-other-than-60, or day-supply anywhere in the page (pack label file has no Supplement Facts panel; `turkesterone_rules.py --brief` confirms no mg token was ever OCR'd).
- No "lab-tested" / COA claim (house rule, no COA exists for this SKU).
- No pack_images / label-gate claim: `product_refs/turkesterone-advanced-formula-cutout.png` does not exist, so no generated pack-shot whitelist claim was made. Hero/offer/product images use the real live PDP CDN photo (`Turkesterone_Advanced_Formula.webp`) unmodified, downloaded this run.
- No ingredient dosage (KSM-66 Ashwagandha, Tongkat Ali, Colostrum, BioPerine amounts shown on the live PDP description) repeated in body copy — PATI rule #6, no dosage-with-units outside the product/offer card, and the label file does not carry a milligram token to confirm those PDP description numbers against the physical pack anyway.
- No claim about muscle growth, strength, recovery, or endurance from using this product — the cited human trial found no significant effect on its measured markers, and no trial tested the combined formula.
- No mention of the live PDP's own marketing copy (muscle recovery / endurance claims in the product description) since those are unsourced marketing text, not label facts or study findings.

## Price correction 2026-10-26

Re-fetched public product JSON on 2026-10-26 at 2026-10-26T01:40:31Z.

Removed from this draft: No price change. The 2026-10-23 figures still match.

Now stated: One-time $75.00 (price 7500). Compare-at $119.98 (compare_at_price 11998). selling_plan_groups is empty. quantity_price_breaks empty. The draft's "no Subscribe and Save" line remains accurate because no selling plan is listed.

Source: https://wellnessnest.co/products/turkesterone-advanced-formula.js fetched 2026-10-26 at 2026-10-26T01:40:31Z. One-time price also matched https://wellnessnest.co/collections/all/products.json.

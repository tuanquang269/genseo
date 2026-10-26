# Claims log, shilajit-gummies-listicle-261022, 2026-10-22

| Claim | Source | Verification |
|---|---|---|
| The pouch lists a 10:1 shilajit extract per 2-gummy serving and raw-material equivalent | Live PDP HTML and `/products/premium-himalayan-shilajit-gummies.js`, fetched 2026-10-22 | Confirmed in fetched PDP description and product JSON |
| Human trials used purified or standardized extracts, not gummies | Keller 2019, https://doi.org/10.1186/s12970-019-0270-2; Pandit 2016, https://doi.org/10.1111/and.12482; Pingali 2022, https://doi.org/10.1016/j.phymed.2022.154334 | Europe PMC abstracts fetched 2026-10-22 |
| Testosterone findings in men aged 45 to 55 over 90 days | Pandit et al., Andrologia 2016, https://doi.org/10.1111/and.12482 | Europe PMC abstract fetched 2026-10-22 |
| Strength-fatigue finding in 63 men over 8 weeks | Keller et al., JISSN 2019, https://doi.org/10.1186/s12970-019-0270-2 | Europe PMC abstract and PMC full text fetched 2026-10-22 |
| Ashwagandha-only 60-day stress trial | Chandrasekhar et al., Indian J Psychol Med 2012, https://doi.org/10.4103/0253-7176.106022 | Europe PMC abstract fetched 2026-10-22 |
| No published human trial found for a shilajit gummy or this exact blend | Europe PMC searches for shilajit human trials and shilajit extract RCTs, fetched 2026-10-22 | Search results checked; absence stated as an evidence gap, not proof of failure |
| 20.7 percent contamination prevalence in Ayurvedic products purchased online | Saper et al., JAMA 2008, https://doi.org/10.1001/jama.300.8.915 | Europe PMC abstract fetched 2026-10-22 |
| TrustScore, review count and quoted review | `state/trustpilot/wellnessnest.json`, Trustpilot review URL in spec | File fetched 2026-10-22; quote copied verbatim |
| Price and selling plan | Live PDP JS re-fetched 2026-10-26 | One-time $69.99 (variant price 6999). Automatic Refill every 30 days $49.99 (plan 10022748475), every 60 days $44.99 (plan 10022781243), every 90 days $39.99 (plan 10022814011). Card shows $49.99/pouch for 1 pouch every 30 days. The note prices 2 pouches at $44.99/pouch every 60 days and 3 pouches at $39.99/pouch every 90 days. Sticky says "$49.99/pouch every 30 days" (not "From", because the 3-pouch price is $39.99/pouch). compare_at 9998 is not used as a strike price. quantity_price_breaks empty. |

Deliberately omitted: claims that a gummy itself was clinically tested; dosage units in narrative rows; independent lab-testing claims for this SKU; product-effect testimonials beyond the sourced Trustpilot quote; the PDP compare-at price as a strike anchor; fake urgency or scarcity.

## Price correction 2026-10-26

Re-fetched public product JSON on 2026-10-26 at 2026-10-26T01:40:31Z.

Removed from this draft: One-time $59.99 and an Every 4 weeks plan at $44.99 (old plan 9807954235).

Now stated: One-time $69.99 (variant price 6999). Automatic Refill every 30 days $49.99 (plan 10022748475), every 60 days $44.99 (plan 10022781243), every 90 days $39.99 (plan 10022814011). Card shows $49.99/pouch for 1 pouch every 30 days. The note prices 2 pouches at $44.99/pouch every 60 days and 3 pouches at $39.99/pouch every 90 days. Sticky says "$49.99/pouch every 30 days" (not "From", because the 3-pouch price is $39.99/pouch). compare_at 9998 is not used as a strike price. quantity_price_breaks empty.

Source: https://wellnessnest.co/products/premium-himalayan-shilajit-gummies.js fetched 2026-10-26 at 2026-10-26T01:40:31Z. One-time price also matched https://wellnessnest.co/collections/all/products.json and https://wellnessnest.co/collections/shilajit/products.json.
Not stated: two-unit or three-unit one-time prices. They are not in the public JSON.

## Mac re-check 2026-10-26

Same Mac re-check as the shilajit gummies product JSON. The page states the prices per pouch for 1, 2, and 3 pouches.

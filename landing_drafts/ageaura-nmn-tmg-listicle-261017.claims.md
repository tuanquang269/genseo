# Claims log: AgeAura NMN + TMG listicle

Fetched: 2026-10-17, rechecked the same day in review. Product: `ageaura-pure-nmn-tmg-nad-complex`.

| Claim | Source | How verified |
|---|---|---|
| AgeAura product identity is Pure NMN + TMG NAD+ Complex | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Live PDP and `/products/<handle>.js` fetched this review. Handle checked with `scripts/ageaura_rules.py`. |
| Buy 1 one-time price is $69.95 | Live PDP buy box, 2026-10-17, after selecting Buy 1 | The button read "One-Time Purchase Price: $69.95". Variant price in the product JSON is `6995`. |
| Buy 1 Subscribe & Save is $59.46 every four weeks at 15% off | Same buy box, selling plan `9884729659` | With Buy 1 selected, the button read "Subscribe & Save 15% Price: $59.46 Original price: $69.95". JSON allocation `price` and `per_delivery_price` are `5946`. |
| The product page opens on a 3-bottle offer, not on Buy 1 | Live PDP buy box before any click, 2026-10-17 | Preselected Kaching bar is "Buy 2 GET 1 FREE" (quantity 3). That view showed Subscribe & Save 14% at $120.31 (original $209.85) and one-time $139.90 (original $209.85). |
| PDP ingredient list prints 500 mg NMN and 250 mg TMG per 2-capsule serving | Live PDP ingredients block, 2026-10-17 | Visible text: "Each daily serving (2 capsules) contains: 500mg NMN ... 250mg TMG". Kept in the offer card only. Not in the OCR front-label file. |
| Front label states 60 Capsules, 30 Servings, and Vegan Capsule | `product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json` and the pack photos | OCR-accepted label record. The offer, bridge, and expert stills show that bottle. |
| Huang 2022 tested NMN in 66 adults aged 40 to 65 for 60 days; day-60 NAD+/NADH rose 38% from baseline in the NMN group and 14.3% in placebo | https://doi.org/10.3389/fragi.2022.851698 | Europe PMC abstract and PubMed 35821806 fetched this review. Crossref and the Frontiers page list one author, Huang Hao. The page says Huang H, not "et al." |
| Zhang 2025 review of 12 adult trials found higher blood NAD; most glucose and lipid outcomes did not differ | https://doi.org/10.1080/10408398.2024.2387324 | Europe PMC abstract and PubMed 39116016. Authors Zhang J, Poon ET, Wong SH. Journal year 2025 (epub 2024-08-08). |
| Morifuji 2024 tested NMN in 60 older adults for 12 weeks. Blood NAD rose. The 4-meter walk was faster than placebo. The primary stepping test did not differ. Sleep quality scores improved. TMG was not tested. | https://doi.org/10.1007/s11357-024-01204-1 | Europe PMC abstract. Authors Morifuji M, Higashi S, Ebihara S, Nagata M. GeroScience 2024. |
| Olthof 2003 tested betaine, not NMN, in four groups of 19 healthy adults for six weeks and reported lower fasting homocysteine | https://doi.org/10.1093/jn/133.12.4135 | Europe PMC abstract. First author Olthof MR. |
| No combined NMN + TMG or NMN + betaine human trial in a targeted Europe PMC title/abstract search | Europe PMC REST, 2026-10-17 | Queries for nicotinamide mononucleotide plus trimethylglycine, and plus betaine, returned 0 hits. |
| TrustScore 4.2, 1,144 reviews, Trustpilot star graphic is 4 | https://www.trustpilot.com/review/wellnessnest.co | `__NEXT_DATA__` read in a browser this review: `trustScore` 4.2, `numberOfReviews` 1144, `stars` 4. |
| Tonya, Jindřich Pavlíček, and Martin Mc Cartney JNR quotes | The three Trustpilot review URLs in the spec | Each review page opened 2026-10-17. Text, names, countries, months, star counts, and verified flags matched the spec. Service wording only. |
| Free shipping on orders over $69 | Live homepage and PDP ticker, 2026-10-17 | Ticker text: "Free Shipping on Orders Over $69". |
| 90-day money-back guarantee on the first order, with eligibility rules | https://wellnessnest.co/policies/refund-policy | Policy: first order only, at most 3 units, request within 90 days of delivery, product price refunded, shipping and tax not refunded. |

## Deliberately left out

- No claim that NMN + TMG works better together. No combined human trial was found.
- No claim that NMN increases energy, reverses aging, extends life, treats disease, or improves cognition. The label's marketing lines are not presented as clinical findings.
- No study dose in the numbered rows. Huang used 300 mg/day and Morifuji used 250 mg/day. Those amounts stay off the page.
- The PDP also prints 150 mg quercetin, 100 mg trans-resveratrol, 50 mg apigenin, 400 mcg DFE folate, and 1 mg spermidine, and it says the spermidine is from wheat germ. Those lines are not in the OCR front-label file, so they are not on the offer card.
- No COA, laboratory-testing, purity, or third-party-verification claim.
- No countdown, scarcity, or invented review.
- The 6-bottle tier is on the PDP. Its subscribe price was not read off the buy box in this review, so the page does not quote it.
- Listicle CTAs stay on the Shopify PDP. `https://get.wellnessnest.co/product/ageaura-nmn-tmg-v8` returned HTTP 200, and no repo rule sends this listicle there.

## Image QA

- Storefront shots from the daily run show the offer, bridge, and expert bottles as the white AgeAura NMN + TMG bottle: vertical Wellness Nest wordmark, AgeAura badge, NMN + TMG NAD + Complex, Vegan Capsule, the four benefit lines, 60 Capsules, 30 Servings.
- Numbered-row stills are unmarked scenes (paper diagram, beetroot, stones, empty trays, water and a weekly organizer). They do not show another product or a face.
- The hero in the storefront screenshot is covered by the sitewide "Spin for a treat" popup, so this review did not re-grade that one frame. The hero slot is still the generated pack composite from the daily run.
- Original `tmp_images/` files are gitignored and are not on this VM. This review did not re-roll them and did not re-run macOS Vision OCR.

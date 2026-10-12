# Claims log — pure-shilajit-gold-resin-listicle-261012

| Claim (as written on page) | How verified | Source |
|---|---|---|
| "a purified shilajit capsule taken twice daily for 90 days raised free testosterone 19.14 percent versus baseline" | Fetched abstract via Europe PMC/DOI this run; numbers copied verbatim from the abstract | Pandit S et al. Andrologia 2016;48(5):570-575. doi:10.1111/and.12482 |
| "DHEAS... rose 31.35 percent over the same 90 days" | Same abstract, same run | Pandit S et al. Andrologia 2016, doi:10.1111/and.12482 |
| "75 men aged 45 to 55, 90 days... randomised double-blind" | Study design copied from the abstract's methods | Pandit S et al. Andrologia 2016, doi:10.1111/and.12482 |
| "A 28-day pilot study gave 25 healthy men a daily dose of shilajit resin... Leg press strength rose 12.94 percent and grip strength rose 5.73 percent" | Fetched abstract via DOI this run; numbers copied verbatim | Yadav D et al. Cureus 2026;18(1):e102372. doi:10.7759/cureus.102372 |
| "The design was open label with no placebo arm" | Study design stated in the abstract | Yadav D et al. Cureus 2026, doi:10.7759/cureus.102372 |
| "We searched Europe PMC and PubMed for a human trial of a shilajit gummy. We found none." | Absence claim: searched Europe PMC + PubMed this run for "shilajit gummy trial" / "shilajit gummy RCT", no clinical trial of a gummy format found | Search performed 2026-10-12, no citation (negative result) |
| "A 2025 lab survey tested raw shilajit and finished shilajit supplements for thallium... Trace amounts turned up in both" | Fetched abstract via DOI this run | Kamgar E et al. BMC Chem 2025;19:20. doi:10.1186/s13065-025-01384-7 |
| "Some finished products tested higher than the raw material they came from" | Stated in the same abstract's findings | Kamgar E et al. BMC Chem 2025, doi:10.1186/s13065-025-01384-7 |
| Product name, bullets (Himalayan Shilajit, 75% Fulvic Acid, Lab-Tested, 1.06 oz (30g) - 75 servings, Dietary Supplements) | OCR-confirmed front-of-pack lines (no milligram token on this label) + live PDP copy | `product_refs/pure-shilajit-gold-resin.label.json`; `https://wellnessnest.co/products/pure-shilajit-gold-resin` fetched 2026-10-12 |
| Price $75.00, Subscribe & Save $67.50 (10% off, every 4 weeks) | Direct from Shopify product JSON (cents) | `pure-shilajit-gold-resin.js` fetched 2026-10-12: price 7500, selling_plan price 6750 |
| "90-Day Money-Back Guarantee" | Verbatim text match | `/policies/refund-policy` fetched 2026-10-12 |
| "Free shipping on orders $70+" | Verbatim from live site ticker | Site ticker banner, fetched 2026-10-12 |
| Trustpilot TrustScore 4.2, 1,144 reviews (thousands comma as displayed) | Read exactly from the refreshed file, not re-scraped this run | `state/trustpilot/wellnessnest.json` |
| Expert quote: Patricia Kowalski, 5★, "The shilajit from Wellness Nest has helped me..." | Verbatim quote + name exactly as in the refreshed Trustpilot file | `state/trustpilot/wellnessnest.json`, review id `69e1315a036b2887686369df`, published 2026-04-16 |
| Reviews[0-2]: Stephen A McCloskey, A Ginter, ΙΩΑΝΝΗΣ ΜΙΧΑΗΛΙΔΗΣ (5★ each, verbatim) | Verbatim quotes + names exactly as in the refreshed Trustpilot file, casing preserved | `state/trustpilot/wellnessnest.json`, review URLs as listed in the spec |

## Deliberately left out / not claimed

- No milligram, microgram, or mL dose figure is stated for Pure Shilajit Gold Resin itself anywhere on the page. The label has no mg token (resin products are sold by weight/servings, not a per-serving mg claim), so none is invented.
- The exact daily dose used in the Yadav 2026 resin pilot (500 mg/day TruBlk resin) is named only in the chart source line, not in body copy, to avoid it reading as a dose claim for Pure Shilajit Gold Resin, which is a different product.
- The thallium contamination study's exact microgram-per-gram figures are not quoted in body copy (only "trace amounts," with the full numbers left to the chart/source citation) to avoid implying a measured contamination level for this specific product, which was not tested in that survey.
- No face appears in any generated image (hero/offer/expert/product all reuse the OCR-passed label crop `pack-ref.webp`; scene images are no-face UGC lane).
- No countdown timer, stock counter, or fake scarcity messaging anywhere on the page.
- No rating/review below 4 stars used; no review edited or paraphrased.

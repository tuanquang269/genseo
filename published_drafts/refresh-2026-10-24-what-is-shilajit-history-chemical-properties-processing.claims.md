# Claims log — refresh draft 2026-10-24

Article: `blogs/news/what-is-shilajit-history-chemical-properties-processing`
Draft: `published_drafts/refresh-2026-10-24-what-is-shilajit-history-chemical-properties-processing.md`
Diagnosis: GSC page 42 impressions, 0 clicks, position 79.7 (2026-10-15..2026-10-21, vault `90-sources/gsc-daily/2026-10-24-gsc.md`). CLIMB. Title not changed. Not published.

Queries the new blocks answer: "what is shilajit made of" (5 impressions, position 76.0) and "shilajit gummies vs resin" (4 impressions, position 67.0), same GSC file.

## New claims

| Claim in the added blocks | Source |
|---|---|
| Shilajit is described here as about 60-80% humus. The rest is humic and fulvic acids, plant alkaloids, organic acids, resins, and waxes, rather than one chemical. | Live article sentences fetched 2026-10-24: "comprised of about 60-80% humus" and "The other portion of Shilajit that is not made of humic and fulvic acids consists of beneficial plant alkaloids, organic acids, resins, waxes". Not re-checked against a new study. The [FDA dietary supplements overview](https://www.fda.gov/food/dietary-supplements) is linked only as the agency's general supplement role. It is not a composition citation. |
| Premium Himalayan Shilajit Gummies are a Wellness Nest product. The ShilaSource name covers the resin, not the gummies. | Vault `20-brands/21-wellnessnest-products/3-shilasource.md`, name-scope note dated 2026-09-14. Confirmed as separate handles in the public collection `products.json` on 2026-10-24. |
| One unit, one-time: $69.99 for each product. Two units $59.99 per unit. Three units $49.99 per unit. Automatic refill $49.99 / $44.99 / $39.99 per unit for 1 / 2 / 3 units. | Vault `20-brands/21-wellnessnest-products/9-wellnessnest-pricing-table.md` (Kevin, 2026-10-23). Public `product.js` on 2026-10-24 matches the one-unit price (variant `6999`) and the three refill allocations (`4999` / `4499` / `3999`) for both handles. The two-unit and three-unit one-time prices were not re-checked with a cart in this session. |
| Both products are in the shilajit collection and the best-seller collection. | Public `products.json` for `/collections/shilajit-wellness-stack` and `/collections/best-seller`, fetched 2026-10-24. |
| Order processing within 2 business days. After carrier pickup: US economy 3-7 business days, standard 2-5, priority 2. | Public `https://wellnessnest.co/policies/shipping-policy`, fetched 2026-10-24. |
| 90-day money-back guarantee on a first order, with eligibility limits. Shipping fees are not refunded. | Public `https://wellnessnest.co/policies/refund-policy`, fetched 2026-10-24. The draft does not restate every eligibility bullet. |

## One edit inside the old body

The 2023 sentence "Shilajit contains more than 80 trace minerals..." is still present. A lead-in was added so it is attributed to the older paragraph and marked as not a ShilaSource pack-label amount. Naming ShilaSource in the same draft otherwise fails `scripts/shilasource_resin_rules.py`, because "80 minerals" is not on `product_refs/shilasource-himalayan-shilajit-resin.label.json`. The number was not deleted. It is not used as a product fact in the new blocks.

The in-body formula heading `CaSi(KNa)C25H57O26 + C6H6O3` was changed from an `h1` to a paragraph so the draft has one H1, the article title. The formula text was kept. No primary source for that 1979 formula, or for the page's 80°C melting point, was added.

Image `alt` text was filled from the pictures already on the page (cliff, resin bowl, mountain carry, snow ridge, resin chunks, hand-held resin, rocky slope). Those alts do not add a composition or dose claim.

## Not used, because they were not a single vault fact

- Gummies dose. Pack-front OCR in `product_refs/premium-himalayan-shilajit-gummies.label.json` lists optional lines "1500mg Shilajit", "75% Fulvic Acid", "85+ Trace Minerals", "60 GUMMIES", "60-DAY SUPPLY". The live `product.js` description says the Supplement Facts image lists 2 gummies (6 g), 30 servings, and 150 mg of a 10:1 extract. The comparison table does not pick one.
- Fulvic percentage, milligrams, and "85+ trace minerals" as a ShilaSource or gummies selling point. Vault `3-shilasource.md` treats mineral-count and fulvic-% selling as retired, and the resin label file has no mineral count.
- Gold resin and Shockwave. They are separate products and are not in this gummies-vs-resin table.
- The 2026-10-21 sample comparison in the vault (`24-genseo-blog-template`) uses $59.99 and a 150 mg / 30-serving gummies line. Those figures were not copied. The 2026-10-23 pricing table supersedes $59.99.

## Open questions

- Mike Moretti is the public co-founder (vault `20-brands/1-wellnessnest.md`, Kevin 2026-10-11). The live byline on this article is "Mkt Staff". `roster.json` lists only Dr. Marcus Hale, and the article gate requires that approved sentence. The draft uses Dr. Marcus Hale. It does not invent a Mike Moretti roster bio.
- The 60-80% humus figure and the trace-element list in the 2023 body were not tied to a primary study in this refresh. The only outbound source already on the page is `purehimalayanshilajit.com`.
- Vault `3-shilasource.md` also mentions 3/6/12-month ShilaSource reserve packs. They were not in the collection `products.json` checked here, so the draft does not mention them.
- Two-unit and three-unit one-time prices ($59.99 and $49.99 per unit) are from the approved pricing table. This session confirmed the one-unit price and the three refill prices on the public product JSON, not a new cart for the one-time multi-packs.

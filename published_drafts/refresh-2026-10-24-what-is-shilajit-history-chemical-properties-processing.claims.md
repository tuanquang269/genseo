# Claims log — refresh draft 2026-10-24

Article: `blogs/news/what-is-shilajit-history-chemical-properties-processing`
Draft: `published_drafts/refresh-2026-10-24-what-is-shilajit-history-chemical-properties-processing.md`
Diagnosis: GSC page 42 impressions, 0 clicks, position 79.7 (2026-10-15..2026-10-21, vault `90-sources/gsc-daily/2026-10-24-gsc.md`). CLIMB. Title not changed. Not published.

2026-10-25 price pass: the comparison table and FAQ now name Automatic Refill as every 30 / 60 / 90 days. Two-unit and three-unit one-time rows were removed because public product JSON does not list them.

Queries the new blocks answer: "what is shilajit made of" (5 impressions, position 76.0) and "shilajit gummies vs resin" (4 impressions, position 67.0), same GSC file.

## New claims

| Claim in the added blocks | Source |
|---|---|
| Shilajit is described here as about 60-80% humus. The rest is humic and fulvic acids, plant alkaloids, organic acids, resins, and waxes, rather than one chemical. | Live article sentences fetched 2026-10-24: "comprised of about 60-80% humus" and "The other portion of Shilajit that is not made of humic and fulvic acids consists of beneficial plant alkaloids, organic acids, resins, waxes". Not re-checked against a new study. The [FDA dietary supplements overview](https://www.fda.gov/food/dietary-supplements) is linked only as the agency's general supplement role. It is not a composition citation. |
| Premium Himalayan Shilajit Gummies are a Wellness Nest product. The ShilaSource name covers the resin, not the gummies. | Vault `20-brands/21-wellnessnest-products/3-shilasource.md`, name-scope note dated 2026-09-14. Confirmed as separate handles in the public collection `products.json` on 2026-10-24. |
| One unit, one-time: $69.99 for each product. Automatic Refill: $49.99 every 30 days, $44.99 every 60 days, $39.99 every 90 days. No two-unit or three-unit one-time price is stated. | Public product JSON re-read 2026-10-25. `https://wellnessnest.co/products/premium-himalayan-shilajit-gummies.js`: variant 50986079191355, `price` 6999. `https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin.js`: variant 51117944340795, `price` 6999. Both files have one variant. The same day, `https://wellnessnest.co/collections/shilajit-wellness-stack/products.json?limit=250` lists both variants at `69.99` and does not include selling plans. On each product `.js`, selling-plan group `Automatic Refill` (app id 5284869): plan 10022748475 `Automatic Refill · every 30 days` allocation `price` 4999; plan 10022781243 `Automatic Refill · every 60 days` allocation `price` 4499; plan 10022814011 `Automatic Refill · every 90 days` allocation `price` 3999. Adjustments are `value_type` `price` at those same cent amounts. `per_delivery_price` matches `price` on each allocation. These are cadence plans, not quantity breaks. The 2026-10-24 resin listicle claims file records $49.99 as Automatic Refill every 30 days. |
| Premium Himalayan Shilajit Gummies and ShilaSource Himalayan Shilajit Resin are in the shilajit collection and the best-seller collection. | Public `https://wellnessnest.co/collections/shilajit-wellness-stack/products.json?limit=250` and `https://wellnessnest.co/collections/best-seller/products.json?limit=250`, re-read 2026-10-24. Both files list `premium-himalayan-shilajit-gummies` and `shilasource-himalayan-shilajit-resin`. The shilajit collection also lists `pure-shilajit-gold-resin` and `shilajit-shockwave`; best-seller does not. This article's collection sentences name only the gummies and the ShilaSource resin. Product `.js` for those two handles returned HTTP 200 the same day. |
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
- The 2026-10-21 sample comparison in the vault (`24-genseo-blog-template`) uses $59.99 and a 150 mg / 30-serving gummies line. Those figures were not copied. Live `premium-himalayan-shilajit-gummies.js` on 2026-10-25 lists the one-time price at 6999 ($69.99).

## Open questions

- Mike Moretti is the public co-founder (vault `20-brands/1-wellnessnest.md`, Kevin 2026-10-11). The live byline on this article is "Mkt Staff". `roster.json` lists only Dr. Marcus Hale, and the article gate requires that approved sentence. The draft uses Dr. Marcus Hale. It does not invent a Mike Moretti roster bio.
- The 60-80% humus figure and the trace-element list in the 2023 body were not tied to a primary study in this refresh. The only outbound source already on the page is `purehimalayanshilajit.com`.
- Vault `3-shilasource.md` also mentions 3/6/12-month ShilaSource reserve packs. They were not in the collection `products.json` checked here, so the draft does not mention them.
- Two-unit and three-unit one-time prices ($59.99 and $49.99 per unit) were removed on 2026-10-25. Public product `.js` and the shilajit collection `products.json` show one variant at $69.99 for each of these two products. They do not list a two-unit or three-unit one-time price. The earlier figures were only in a vault pricing table that is not in this repo.
- ShilaSource `product.js` on 2026-10-25 also returns plan 9830990139, group name `Delivery every 8 weeks`, allocation `price` 5669 ($56.69), with a Product Quantity option of `2` and a 19% adjustment. The gummies file does not list that plan. The comparison table states only the shared Automatic Refill plans. Whether to add the 8-week plan is Kevin's decision, because the JSON does not say if $56.69 is the checkout total or the per-item price at quantity 2.

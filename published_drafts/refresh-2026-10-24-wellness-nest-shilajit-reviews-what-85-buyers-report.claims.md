# Claims log — refresh draft 2026-10-24

Article: `blogs/news/wellness-nest-shilajit-reviews-what-85-buyers-report`
Draft: `published_drafts/refresh-2026-10-24-wellness-nest-shilajit-reviews-what-85-buyers-report.md`
Diagnosis: GSC page position 2.2, 16 impressions, 1 click, 6.25% CTR (2026-10-15..2026-10-21, vault `90-sources/gsc-daily/2026-10-24-gsc.md`). Ranking page. Title not changed. Price lines in the existing body were corrected. Review counts and quotes were kept. Not published.

2026-10-25 price pass: Automatic Refill amounts are restated as the every 30 / 60 / 90 day selling plans on the public product JSON. Two-unit and three-unit one-time prices were removed because that JSON does not list them.

## New claims

| Claim in the added blocks | Source |
|---|---|
| 85 written reviews; energy named in 30; focus or mood in 24; taste in 15; no effect in 5 | Live article opening and the "What buyers report" table, fetched 2026-10-24 from the public page. Restated, not recounted. |
| The store's review feed includes German, French, Polish, and Italian entries. This count uses the English written reviews only. | Live article section "Where these reviews come from, and what that means in the US". |
| "Erfahrungen" and "avis" are the German and French words for the same review/experience question. No review was translated. | Query list in vault `90-sources/gsc-daily/2026-10-24-gsc.md` ("wellness nest shilajit erfahrungen", "wellness nest shilajit avis", "wellness nest shilajit review"). The gloss is the language of those queries, not a new buyer quote. |
| The shilajit collection includes Premium Himalayan Shilajit Gummies, ShilaSource Himalayan Shilajit Resin, Himalayan Pure Shilajit Gold Resin, and Shilajit Shockwave Energy Drops. The best-seller collection includes Premium Himalayan Shilajit Gummies and ShilaSource Himalayan Shilajit Resin. Gold Resin and Shockwave are linked on their product pages. | Public `https://wellnessnest.co/collections/shilajit-wellness-stack/products.json?limit=250`, fetched 2026-10-24, seven products: `shilasource-himalayan-shilajit-resin`, `premium-himalayan-shilajit-gummies`, `fusiforce-creatine-gummies`, `pure-shilajit-gold-resin`, `shilajit-shockwave`, `turkesterone-advanced-formula`, `florafresh-vaginal-probiotics-gummies`. Public `https://wellnessnest.co/collections/best-seller/products.json?limit=250`, fetched 2026-10-24, four products: `shilasource-himalayan-shilajit-resin`, `premium-himalayan-shilajit-gummies`, `fusiforce-creatine-gummies`, `florafresh-vaginal-probiotics-gummies`. Best-seller does not list `pure-shilajit-gold-resin` or `shilajit-shockwave`. The same day, product `.js` returned HTTP 200: `premium-himalayan-shilajit-gummies.js` (Premium Himalayan Shilajit Gummies), `shilasource-himalayan-shilajit-resin.js` (ShilaSource Himalayan Shilajit Resin), `pure-shilajit-gold-resin.js` (Himalayan Pure Shilajit Gold Resin), `shilajit-shockwave.js` (Shilajit Shockwave Energy Drops). The draft names those four shilajit products in the shilajit collection and only the gummies and the ShilaSource resin in best-seller. It does not name the other handles in either collection. |
| wellnessnest.co ships across the United States. | Already stated in the live FAQ "Where can I buy Wellness Nest shilajit in the US?". Not a new transit-time claim. |

## Price lines

Every dollar amount below was re-read from public product JSON on 2026-10-25. Review counts, quotes, star ratings, and the PubMed citations were not changed. The vault pricing table is not the source for these lines.

| Price line in the draft | Source |
|---|---|
| Meta: one-time, one unit starts at $69.99. Body bullets and FAQ: one unit, one-time, is $69.99 for Premium Himalayan Shilajit Gummies, ShilaSource Himalayan Shilajit Resin, and Shilajit Shockwave Energy Drops. | Public product JSON re-read 2026-10-25. `https://wellnessnest.co/products/premium-himalayan-shilajit-gummies.js`: one variant, 50986079191355, `price` 6999. `https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin.js`: one variant, 51117944340795, `price` 6999. `https://wellnessnest.co/products/shilajit-shockwave.js`: one variant, 48849042112827, `price` 6999. The same day, `https://wellnessnest.co/collections/shilajit-wellness-stack/products.json?limit=250` lists those variants at `69.99`. That collection file does not include selling plans. |
| One unit of Himalayan Pure Shilajit Gold Resin is $75.00 one-time. That product page lists no selling plan. | Public `https://wellnessnest.co/products/pure-shilajit-gold-resin.js` re-read 2026-10-25: one variant, 48768152895803, `price` 7500, `selling_plan_groups` empty, variant `selling_plan_allocations` empty. Collection `products.json` the same day lists that variant at `75.00`. |
| For the gummies, the ShilaSource resin, and the Shockwave drops, Automatic Refill is $49.99 every 30 days, $44.99 every 60 days, or $39.99 every 90 days. | Public product `.js` re-read 2026-10-25 on all three handles. Shared selling-plan group name `Automatic Refill` (app id 5284869). Plan 10022748475, name `Automatic Refill · every 30 days`, allocation `price` 4999 and `per_delivery_price` 4999, adjustment `value_type` `price` value 4999. Plan 10022781243, name `Automatic Refill · every 60 days`, allocation `price` 4499. Plan 10022814011, name `Automatic Refill · every 90 days`, allocation `price` 3999. These are delivery-cadence plans. They are not one-unit, two-unit, and three-unit quantity breaks. The 2026-10-24 resin listicle claims file records the same $49.99 reading for the every-30-days plan. Collection `products.json` does not list the plans. |

## Removed on 2026-10-25

| Earlier price line | Decision |
|---|---|
| Two-unit one-time $59.99 per unit and three-unit one-time $49.99 per unit for the gummies, the ShilaSource resin, and Shockwave. | Removed from the draft. Public product `.js` and the shilajit collection `products.json` each show one variant and one one-time price ($69.99). They do not list a two-unit or three-unit one-time price. The figures were only in vault `20-brands/21-wellnessnest-products/9-wellnessnest-pricing-table.md`, which is not in this repo, and in a 2026-10-24 cart note that this session did not repeat. Not restated. |
| Automatic refill $49.99 / $44.99 / $39.99 per unit for one, two, or three units. | Removed as a quantity reading. The same cent amounts are the Automatic Refill plans every 30 / 60 / 90 days, plan ids 10022748475 / 10022781243 / 10022814011, logged in the table above. |

## Left as the live page states them

Title, star ratings, quoted reviews, and the PubMed links already in the body (Pandit 2016 `26395129`, Keller 2019 `30728074`, Surapaneni 2012 `22771318`). Bylines stays Dr. Marcus Hale, which is the live Person author and the only name in `roster.json`. The meta description's price clause was updated with the one-unit price; the review counts in that sentence were not.

## Open questions

- ShilaSource `product.js` on 2026-10-25 also returns selling-plan group `Delivery every 8 weeks` (app id 294517), plan 9830990139. Options include Order Frequency `8-week` and Product Quantity `2`. The adjustment is `percentage` 19. Allocation `price` and `per_delivery_price` are 5669 ($56.69), `compare_at_price` 6999. Gummies and Shockwave do not list this plan. The draft does not state it, because the JSON does not say whether checkout on that plan charges $56.69 once or $56.69 times the quantity option. Kevin's decision.
- Gold Resin `product.js` on 2026-10-25 still has no selling plan, and the draft says so. A 2026-10-23 Kaching audit (`plans/261021-1741-wn-golive-ads-gempages-audit/kaching-align-261023.md` and `qa-kaching-r1-261023.md`) found the gold resin URL's bundle widget bound to the ShilaSource deal, with a one-time bar at $69.99. This session read public product JSON only, not that widget. If the widget still shows a different price, that needs Kevin.
- Mike Moretti is the public co-founder (vault `20-brands/1-wellnessnest.md`, Kevin 2026-10-11). `roster.json` lists only Dr. Marcus Hale, and the article gate rejects any other About the Author sentence. The live byline was left as Dr. Marcus Hale.
- The live hero image shows pouch lines (1500mg Shilajit, 75% Fulvic Acid, 85+ Trace Minerals, 60 gummies, 60-day supply). Those lines were not copied into the new text. The live gummies `product.js` description instead says the Supplement Facts image lists 2 gummies (6 g), 30 servings, and 150 mg of a 10:1 extract. That conflict was not resolved here.

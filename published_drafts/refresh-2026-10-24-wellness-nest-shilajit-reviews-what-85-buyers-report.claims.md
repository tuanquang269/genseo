# Claims log — refresh draft 2026-10-24

Article: `blogs/news/wellness-nest-shilajit-reviews-what-85-buyers-report`
Draft: `published_drafts/refresh-2026-10-24-wellness-nest-shilajit-reviews-what-85-buyers-report.md`
Diagnosis: GSC page position 2.2, 16 impressions, 1 click, 6.25% CTR (2026-10-15..2026-10-21, vault `90-sources/gsc-daily/2026-10-24-gsc.md`). Ranking page. Title not changed. Existing body kept. Not published.

## New claims

| Claim in the added blocks | Source |
|---|---|
| 85 written reviews; energy named in 30; focus or mood in 24; taste in 15; no effect in 5 | Live article opening and the "What buyers report" table, fetched 2026-10-24 from the public page. Restated, not recounted. |
| The store's review feed includes German, French, Polish, and Italian entries. This count uses the English written reviews only. | Live article section "Where these reviews come from, and what that means in the US". |
| "Erfahrungen" and "avis" are the German and French words for the same review/experience question. No review was translated. | Query list in vault `90-sources/gsc-daily/2026-10-24-gsc.md` ("wellness nest shilajit erfahrungen", "wellness nest shilajit avis", "wellness nest shilajit review"). The gloss is the language of those queries, not a new buyer quote. |
| The shilajit collection lists ShilaSource Himalayan Shilajit Resin and Premium Himalayan Shilajit Gummies. The best-seller collection also lists those two. | Public `products.json` for `/collections/shilajit-wellness-stack` and `/collections/best-seller`, fetched 2026-10-24. |
| wellnessnest.co ships across the United States. | Already stated in the live FAQ "Where can I buy Wellness Nest shilajit in the US?". Not a new transit-time claim. |

## Left as the live page states them

Title, meta description, star ratings, quoted reviews, the $59.99 / $75.00 / $79.99 price lines, and the PubMed links already in the body (Pandit 2016 `26395129`, Keller 2019 `30728074`, Surapaneni 2012 `22771318`). Bylines stays Dr. Marcus Hale, which is the live Person author and the only name in `roster.json`.

## Open questions

- Live `product.js` on 2026-10-24 shows variant price 6999 ($69.99) for both the resin and the gummies. The article body and meta still say $59.99. Those lines were not edited.
- `best-seller` `products.json` returned four products and did not include `pure-shilajit-gold-resin` or `shilajit-shockwave`. The existing sentence says both collections carry "these products" after discussing all four. That sentence was not rewritten.
- Mike Moretti is the public co-founder (vault `20-brands/1-wellnessnest.md`, Kevin 2026-10-11). `roster.json` lists only Dr. Marcus Hale, and the article gate rejects any other About the Author sentence. The live byline was left as Dr. Marcus Hale.
- The live hero image shows pouch lines (1500mg Shilajit, 75% Fulvic Acid, 85+ Trace Minerals, 60 gummies, 60-day supply). Those lines were not copied into the new text. The live gummies `product.js` description instead says the Supplement Facts image lists 2 gummies (6 g), 30 servings, and 150 mg of a 10:1 extract. That conflict was not resolved here.

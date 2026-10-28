# Buyer prompt-loss list

Listed 2026-10-21. Blog articles only. No Shopify write, no theme edit, no paid-traffic page.

## Why this list

Search Engine Land, 20 Oct 2026, read for the 21 Oct digest:

- [How to prioritize SEO content updates and new opportunities](https://searchengineland.com/how-to-prioritize-seo-content-updates-and-new-opportunities-497220) (Gaetano Pizzi). A new URL is for a customer need the site does not already cover. When a page already answers the question, update that page.
- [What is generative engine optimization (GEO)](https://searchengineland.com/what-is-generative-engine-optimization-geo-444418) (Leigh Mckenzie). A buyer prompt asks which product to buy for a person in a specific situation. A mention and a citation are different measurements. This file does not record either one unless the ledger has a real observation.

The 30 prompts extend the 51 hypothesised prompts from PR #81. They do not copy those strings. AI visibility stays unknown unless `data/ai_visibility/observations.json` has a row with `observed: true`, an observer, and a date.

## How a row was scored

Coverage uses titles and handles from `docs/CLUSTER_MAP.md` (built 2026-10-20, 141 articles) plus 23 DONE `/blogs/news/` URLs in `daily-tickets.md` that are not already in the map. Open tickets are not treated as published articles. They do block a new proposal.

Added from the queue and used as the closest article:

- `are-vaginal-probiotics-worth-it-40-99-us-check-2026` — Are Vaginal Probiotics Worth It? How Much You Check (2026) (prompt ff-over-40)

Added from the queue, and not used as the matching article for any of the 30:

- `shilajit-on-rest-days-with-food-in-the-us` — Shilajit on Rest Days, With Food (US 2026)
- `nmn-while-traveling-with-food-5-us-tips` — NMN While Traveling, With Food (US 2026)
- `vaginal-probiotics-on-an-empty-stomach-us-guide-1` — Vaginal Probiotics on an Empty Stomach (US 2026)
- `shilajit-gummies-while-traveling-5-us-tips` — Shilajit Gummies While Traveling, With Food (2026)
- `nmn-on-rest-days-take-it-with-food-us` — NMN Capsules on a Day Off, With Food (US 2026)
- `nmn-storage-with-food-5-us-rules` — Where Should NMN Capsules Sit, With Food Nearby? (2026)
- `shilajit-and-coffee-with-food-us-guide` — Shilajit and Coffee, With Food (US 2026)
- `is-nmn-worth-it-with-food-us-check` — Is NMN Worth It, With Food? (US 2026)
- `nmn-loading-phase-is-it-needed-in-the-us` — NMN Loading Phase, With Food or Not? (2026)
- `shilajit-cycling-with-food-us-rules` — Do You Cycle Shilajit? With Food Rules (2026)
- `vaginal-probiotics-and-alcohol-in-the-us-2026` — Vaginal Probiotics and Alcohol: How Much Matters? (2026)
- `nmn-for-hair-with-food-us-evidence` — NMN and Hair Claims, Taken With Food (US 2026)
- `shilajit-and-alcohol-with-food-us-guide` — Shilajit and Alcohol, With Food (US 2026)
- `vaginal-probiotic-storage-7-heat-checks-us` — Vaginal Probiotic Gummies at Home: How Much Heat? (2026)
- `vaginal-probiotics-together-what-else-in-the-us` — Vaginal Probiotics Together: How Much Else? (2026)
- `vaginal-probiotic-ingredients-what-to-read-us` — Vaginal Probiotic Ingredients: How Much to Read (2026)
- `shilajit-storage-6-home-rules-for-the-us` — Shilajit Storage at Home, With Food Nearby (2026)
- `vaginal-probiotics-for-athletes-us-routine` — Vaginal Probiotics for Athletes (US 2026)
- `real-or-fake-nmn-6-label-checks-for-us-buyers` — Real or Fake NMN, With Food Checks (US 2026)
- `shilajit-gummies-ingredients-6-label-checks-in-the-us` — Shilajit Gummy Ingredients, Taken With Food (2026)
- `shilajit-for-hair-with-food-us-evidence` — Shilajit for Hair, Taken With Food (US 2026)
- `shilajit-loading-with-food-us-trial-evidence` — Shilajit Loading, With Food or Not? (2026)

- **covered**: a title in that brand's cluster contains every anchor and every focus token, and the title matches the buyer intent (best, vs, where to buy, price, or for-condition).
- **weak**: a title contains every anchor, and it misses the intent or a focus token. The named article is the closest one. The action is to update that article.
- **gap**: no title contains every anchor.

A gap is offered as a topic proposal only when `topic_fitness`, `wn_clusters.query_blocked`, and `refill_tickets.clash` all pass against the map and against every ticket in `daily-tickets.md`. A failure is withheld. Nothing is appended to the live queue. Traffic numbers are not copied into this file.

## Counts

| Status | AgeAura | ShilaSource | FloraFresh | Total |
| --- | --- | --- | --- | --- |
| covered | 5 | 5 | 4 | 14 |
| weak | 4 | 4 | 5 | 13 |
| gap | 1 | 1 | 1 | 3 |

AI visibility rows with `observed: true`: 0. Ledger: missing.

Proposals passed: 0. Withheld: 3.

## The 30 prompts

| ID | Brand | Funnel | Intent | Prompt | Status | Article | AI visibility | Nearest prompt-set row |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aa-best-form | AgeAura | consideration | best | What is the best NMN form to buy, capsules or powder? | covered | NMN Capsules vs Powder vs Sublingual: Best Form (US 2026) (`/blogs/news/nmn-capsules-vs-powder-vs-sublingual-best-form-us-2026`) | unknown | — |
| aa-vs-nr | AgeAura | evaluation | vs | Should I buy NMN or NR? | covered | NMN vs NR: What 6 Human Trials Say (US 2026) (`/blogs/news/nmn-vs-nr-what-6-human-trials-say-us-2026`) | unknown | — |
| aa-where | AgeAura | decision | where-to-buy | Where to buy NMN capsules in the US? | covered | Where to Buy NMN in the US: FDA Status Explained (2026) (`/blogs/news/where-to-buy-nmn-in-the-us-fda-status-explained-2026`) | unknown | ageaura-07-best-nmn-capsules |
| aa-price | AgeAura | decision | price | What is the price of an NMN bottle in the US? | covered | NMN Price: Bottle vs Serving Cost in the US (`/blogs/news/nmn-price-bottle-vs-serving-cost-in-the-us`) | unknown | — |
| aa-men-50 | AgeAura | consideration | for-condition | Is NMN a good buy for men over 50? | covered | AgeAura NMN for Men Over 50: What to Expect (US 2026) (`/blogs/news/ageaura-nmn-for-men-over-50-what-to-expect-us-2026`) | unknown | — |
| aa-best-tmg | AgeAura | consideration | best | What is the best NMN supplement that also includes TMG? | weak | NMN + TMG Benefits: What Human Trials Show (US 2026) (`/blogs/news/nmn-tmg-benefits-what-human-trials-show`) | unknown | — |
| aa-price-tmg | AgeAura | decision | price | How much does an NMN and TMG stack cost per bottle? | weak | NMN + TMG Dosage: How Many mg Per Day? (US 2026) (`/blogs/news/nmn-tmg-dosage-how-much-per-day`) | unknown | — |
| aa-where-brand | AgeAura | decision | where-to-buy | Where can I buy AgeAura NMN and TMG capsules in the US? | weak | AgeAura NMN + TMG Ingredients: What Each One Does (US) (`/blogs/news/ageaura-nmn-tmg-ingredients-what-each-one-does-us`) | unknown | — |
| aa-women-50 | AgeAura | consideration | for-condition | What NMN with TMG should a woman over 50 buy? | weak | AgeAura NMN for Men Over 50: What to Expect (US 2026) (`/blogs/news/ageaura-nmn-for-men-over-50-what-to-expect-us-2026`) | unknown | — |
| aa-runners | AgeAura | consideration | best | What is the best NMN for runners to buy? | gap | — | unknown | — |
| ss-vs | ShilaSource | evaluation | vs | Should I buy shilajit resin or shilajit gummies? | covered | Shilajit Resin vs Gummies: Which Works Better? (US 2026) (`/blogs/news/shilajit-resin-vs-gummies-which-works-better-us-2026`) | unknown | shilasource-07-shilajit-resin-vs-gummies |
| ss-where | ShilaSource | decision | where-to-buy | Where to buy Wellness Nest shilajit in the US? | covered | Where to Buy Wellness Nest Shilajit in the US (2026) (`/blogs/news/where-to-buy-wellness-nest-shilajit-in-the-us-2026`) | unknown | — |
| ss-price | ShilaSource | decision | price | What is the shilajit price per serving? | covered | Shilajit Price: Cost Per Serving by Form (US 2026) (`/blogs/news/shilajit-price-cost-per-serving-by-form-us-2026`) | unknown | — |
| ss-men | ShilaSource | consideration | for-condition | What shilajit should men buy? | covered | Shilajit Benefits for Men: 4 Claims Ranked (US 2026) (`/blogs/news/shilajit-benefits-for-men-4-claims-ranked-us-2026`) | unknown | shilasource-09-best-shilajit-for-men |
| ss-best-gummies | ShilaSource | consideration | best | Which shilajit gummies are the best buy for someone who will not use resin? | covered | Best Shilajit Gummies: 6 US Labels Compared (2026) (`/blogs/news/best-shilajit-gummies-6-us-labels-compared-2026`) | unknown | — |
| ss-best-resin | ShilaSource | consideration | best | What is the best shilajit resin to buy if I want a jar, not gummies? | weak | Shilajit Resin vs Gummies: Which Works Better? (US 2026) (`/blogs/news/shilajit-resin-vs-gummies-which-works-better-us-2026`) | unknown | — |
| ss-where-brand | ShilaSource | decision | where-to-buy | Where do I buy ShilaSource Himalayan shilajit resin? | weak | Shilajit Resin vs Gummies: Which Works Better? (US 2026) (`/blogs/news/shilajit-resin-vs-gummies-which-works-better-us-2026`) | unknown | shilasource-11-best-himalayan-shilajit-resin |
| ss-price-brand | ShilaSource | decision | price | What is the price of ShilaSource resin per serving? | weak | Shilajit Price: Cost Per Serving by Form (US 2026) (`/blogs/news/shilajit-price-cost-per-serving-by-form-us-2026`) | unknown | — |
| ss-women | ShilaSource | consideration | for-condition | Is shilajit resin a fit for women over 45? | weak | Shilajit for Women: What Changes After 45 (US 2026) (`/blogs/news/shilajit-for-women-what-changes-after-45-us-2026`) | unknown | shilasource-01-best-shilajit-resin |
| ss-runners | ShilaSource | consideration | best | What is the best shilajit resin for runners? | gap | — | unknown | shilasource-01-best-shilajit-resin |
| ff-price | FloraFresh | decision | price | What do vaginal probiotics cost in the US? | covered | Vaginal Probiotics Price: US Cost (2026) (`/blogs/news/vaginal-probiotics-price-us-cost-2026`) | unknown | florafresh-vaginal-probiotics-for-beginners |
| ff-where | FloraFresh | decision | where-to-buy | Where should a first-time buyer look for vaginal probiotics in the US? | covered | Where to Buy Vaginal Probiotics in the US: 5 Checks (2026) (`/blogs/news/where-to-buy-vaginal-probiotics-in-the-us-5-checks-2026`) | unknown | — |
| ff-vs | FloraFresh | evaluation | vs | Should I buy FloraFresh gummies or capsules? | covered | FloraFresh Gummies vs Capsules: 5 Format Facts (US 2026) (`/blogs/news/florafresh-gummies-vs-capsules-5-format-facts-us-2026`) | unknown | — |
| ff-beginners | FloraFresh | consideration | for-condition | What should a beginner buy for vaginal probiotics? | covered | Vaginal Probiotics for Beginners: What to Expect in the US (`/blogs/news/vaginal-probiotics-for-beginners-what-to-expect-in-the-us`) | unknown | florafresh-where-to-buy-vaginal-probiotics |
| ff-best | FloraFresh | consideration | best | What is the best vaginal probiotic gummy to buy for daily use? | weak | Where to Buy Vaginal Probiotics in the US: 5 Checks (2026) (`/blogs/news/where-to-buy-vaginal-probiotics-in-the-us-5-checks-2026`) | unknown | — |
| ff-vs-oral | FloraFresh | evaluation | vs | Should I buy a vaginal probiotic or an oral probiotic? | weak | Vaginal Probiotics Side Effects: Normal vs Stop (US 2026) (`/blogs/news/vaginal-probiotics-side-effects-normal-vs-stop-us-2026`) | unknown | — |
| ff-price-brand | FloraFresh | decision | price | What is the FloraFresh gummies price per pouch? | weak | FloraFresh Gummies vs Capsules: 5 Format Facts (US 2026) (`/blogs/news/florafresh-gummies-vs-capsules-5-format-facts-us-2026`) | unknown | — |
| ff-over-50 | FloraFresh | consideration | for-condition | What vaginal probiotics should a woman over 50 buy? | weak | Vaginal Probiotics Over 60: 5 Checks in the US (`/blogs/news/vaginal-probiotics-over-60-5-checks-in-the-us`) | unknown | florafresh-vaginal-probiotics-over-60 |
| ff-runners | FloraFresh | consideration | best | What is the best vaginal probiotic for runners to buy? | gap | — | unknown | — |
| ff-over-40 | FloraFresh | consideration | best | What is the best vaginal probiotic for a woman over 40? | weak | Are Vaginal Probiotics Worth It? How Much You Check (2026) (`/blogs/news/are-vaginal-probiotics-worth-it-40-99-us-check-2026`) — published after the cluster map | unknown | — |

## Weak: update these articles

| ID | Article | What the title misses |
| --- | --- | --- |
| aa-best-tmg | NMN + TMG Benefits: What Human Trials Show (US 2026) (`/blogs/news/nmn-tmg-benefits-what-human-trials-show`) | misses the best wording |
| aa-price-tmg | NMN + TMG Dosage: How Many mg Per Day? (US 2026) (`/blogs/news/nmn-tmg-dosage-how-much-per-day`) | misses the price wording |
| aa-where-brand | AgeAura NMN + TMG Ingredients: What Each One Does (US) (`/blogs/news/ageaura-nmn-tmg-ingredients-what-each-one-does-us`) | misses the where-to-buy wording |
| aa-women-50 | AgeAura NMN for Men Over 50: What to Expect (US 2026) (`/blogs/news/ageaura-nmn-for-men-over-50-what-to-expect-us-2026`) | misses tmg |
| ss-best-resin | Shilajit Resin vs Gummies: Which Works Better? (US 2026) (`/blogs/news/shilajit-resin-vs-gummies-which-works-better-us-2026`) | misses the best wording |
| ss-where-brand | Shilajit Resin vs Gummies: Which Works Better? (US 2026) (`/blogs/news/shilajit-resin-vs-gummies-which-works-better-us-2026`) | misses shilasource; misses the where-to-buy wording |
| ss-price-brand | Shilajit Price: Cost Per Serving by Form (US 2026) (`/blogs/news/shilajit-price-cost-per-serving-by-form-us-2026`) | misses shilasource |
| ss-women | Shilajit for Women: What Changes After 45 (US 2026) (`/blogs/news/shilajit-for-women-what-changes-after-45-us-2026`) | misses resin |
| ff-best | Where to Buy Vaginal Probiotics in the US: 5 Checks (2026) (`/blogs/news/where-to-buy-vaginal-probiotics-in-the-us-5-checks-2026`) | misses gummies; misses the best wording |
| ff-vs-oral | Vaginal Probiotics Side Effects: Normal vs Stop (US 2026) (`/blogs/news/vaginal-probiotics-side-effects-normal-vs-stop-us-2026`) | misses oral |
| ff-price-brand | FloraFresh Gummies vs Capsules: 5 Format Facts (US 2026) (`/blogs/news/florafresh-gummies-vs-capsules-5-format-facts-us-2026`) | misses the price wording |
| ff-over-50 | Vaginal Probiotics Over 60: 5 Checks in the US (`/blogs/news/vaginal-probiotics-over-60-5-checks-in-the-us`) | misses 50 |
| ff-over-40 | Are Vaginal Probiotics Worth It? How Much You Check (2026) (`/blogs/news/are-vaginal-probiotics-worth-it-40-99-us-check-2026`) — published after the cluster map | misses the best wording |

## Gaps and the dup/cluster gate

| ID | Primary | Gate |
| --- | --- | --- |
| aa-runners | nmn for runners | already live (nmn + athletes): NMN and Exercise: Before or After a Workout? (US 2026) |
| ss-runners | shilajit resin for runners | already live (shilajit + athletes): Shilajit for Athletes: What a Trial Found in the US |
| ff-runners | vaginal probiotics for runners | already live (probiotic + athletes): Vaginal Probiotics for Athletes (US 2026) |

## AI visibility

PR #81's ledger is not on this branch, so every cell above is unknown unless a local `data/ai_visibility/observations.json` was passed in. Unknown is not a no. This file does not turn the empty ledger into a mention or a citation.

Join key is `prompt_id` only. The 51 hypothesised prompts are a different set, so their rows are not copied onto these 30.

## What needs a GO

- Appending any proposal to `daily-tickets.md`. This run passed 0.
- Publishing or updating a live post. A weak row names the article to update, and this run does not update it.
- Filling the AI visibility ledger, or running an adapter. Do not treat this file as a measured AI result.
- A new URL for a withheld gap. The gate reason is the reason to leave it.

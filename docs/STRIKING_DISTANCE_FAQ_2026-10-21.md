# Striking-distance FAQ — 2026-10-21

DRAFT report. Nothing here was published. No ticket was added to `daily-tickets.md`. No Shopify write.

Window: GSC daily file `~/genseo-wt/inputs/2026-10-21-gsc.md`, raw rows in `~/genseo-wt/inputs/2026-10-21-gsc-raw.csv`, current period 2026-10-12 through 2026-10-18. Page rows below are summed from that CSV (impressions weighted). Locale paths (`/sk/`, `/el/`) are the same handle, not a second article.

Vault read first: GenSeo hub note `~/PATI/LLM-Wiki/20-brands/4-genseo-geo-playbook-gap-2026-10-20.md`, brand notes for FloraFresh, AgeAura, and FusiForce, and `knowledge_base/AEO_GEO_GUIDELINES.md` (answer-first 40–60 words, question headings, primary sources). Cluster map in that hub already treats the birth-control post and the creatine-expire post as pillars, and the NMN-and-coffee post as a spoke. Fan-out stays inside those URLs.

## Query to URL to action

| Query | Imp | Pos | Clicks | Owning URL | Action | Dup gate |
|---|---:|---:|---:|---|---|---|
| can you take probiotics and birth control at the same time | 14 (13 on the EN post, 1 on `/sk/`) | 7.4 | 0 | [/blogs/news/probiotics-and-birth-control-can-you-take-both-us-2026](https://wellnessnest.co/blogs/news/probiotics-and-birth-control-can-you-take-both-us-2026) | **Refresh.** Proposal: `docs/striking-distance-2026-10-21/probiotics-birth-control-answer-block.md` | See gate notes. A new URL is refused. |
| can you take probiotics with birth control | 6 | 9.7 | 0 | same birth-control post | **Refresh** on that same URL. | FAIL dup against the live title (Jaccard 0.86) once the demand floor is not applied. |
| can you take nmn while drinking coffee everyday | 7 (5 EN, 2 `/sk/`) | 9.6 | 0 | [/blogs/news/nmn-and-coffee-can-you-take-them-together-us-2026](https://wellnessnest.co/blogs/news/nmn-and-coffee-can-you-take-them-together-us-2026) | **Refresh.** Proposal: `docs/striking-distance-2026-10-21/nmn-coffee-answer-block.md` | FAIL covered once the live NMN title is in the article list. |
| can you put nmn powder in coffee | 3 (1 EN, 2 `/el/`) | 8.0 | 0 | same NMN-and-coffee post | **Refresh** on that same URL. | FAIL ranking at pos 8 (floor is pos ≤ 8) and FAIL covered. |
| how long do creatine gummies last | 5 | 8.2 | 0 | [/blogs/news/do-creatine-gummies-expire-6-storage-facts-us-2026](https://wellnessnest.co/blogs/news/do-creatine-gummies-expire-6-storage-facts-us-2026) | **Refresh** on the expire post. Not a new article. | REVIEW covered-segment in `topic_fitness.py` ("how long" is not in the title). GSC still assigns the query to this URL, so the page owns it. |
| do creatine gummies expire | 6 | 10.2 | 0 | same expire post | **Refresh.** Proposal: `docs/striking-distance-2026-10-21/creatine-gummies-shelf-life-answer-block.md` | FAIL covered against the live creatine-gummies title. |

Storefront `search/suggest.json` on 2026-10-21 returned the same three articles for "probiotics and birth control," "nmn and coffee," and "do creatine gummies expire." The exact string "how long do creatine gummies last" returned no article. That does not create a gap: the CSV page row for that query is the expire post.

## Dup-gate detail

`scripts/topic_fitness.py` was run from this worktree. Two catalogs:

1. `~/genseo/existing_articles.json` (96 articles). It does **not** contain these three handles. With impressions passed in, every query FAILs `[demand]` because each is under the 20-impression floor for a new page. With impressions omitted, the stale catalog PASSes the NMN and creatine queries as if they were open, and returns REVIEW for the probiotic queries. Do not use that stale file alone.
2. Supplemental list of the three live titles (plus the existing NMN capsules-vs-powder title, which the coffee article already points at). Results with position set:

| Query | pos | Verdict |
|---|---:|---|
| can you take probiotics and birth control at the same time | 7.4 | FAIL `[ranking]` — refresh the page already in the top 8 |
| can you take probiotics with birth control | 9.7 | FAIL `[dup]` overlap 0.86 with the birth-control title |
| can you take nmn while drinking coffee everyday | 9.6 | FAIL `[covered]` NMN |
| can you put nmn powder in coffee | 8.0 | FAIL `[ranking]` |
| how long do creatine gummies last | 8.2 | REVIEW `[covered-segment]` — overruled by the CSV, which has one owning URL |
| do creatine gummies expire | 10.2 | FAIL `[covered]` |

`scripts/brand_article_overlap.py` was not run. It calls the Shopify Admin API and the Search Console API, and it only keeps queries that contain a brand name. These six queries do not. Public suggest.json plus the CSV page column is the check that names the owner.

## Lint

On each proposal's `proposed-block` HTML:

- `florafresh_rules.violations` — clean on all three files (the birth-control block uses the Supplement Facts line).
- `brand_rules.assess` — no deny.
- `geo_citability.assess` — no fails and no warnings. Opening word counts: birth control 57, NMN and coffee 58, creatine gummies 59 (target 40–60; the checker warns outside 40–70).

`validate_article.py` was not run. These files are patches, not 900-word drafts, and they are not in `published_drafts/`. A later update still has to pass `validate_article.py --draft` before `shopify_publisher.py update`.

## Facts the proposals refused to copy

- **FloraFresh count.** The task brief's CFU figure is the one on the live store text. `scripts/florafresh_rules.py` and `docs/FLORAFRESH_FORMULA_GUARD.md` reject that store figure. The birth-control proposal uses the Supplement Facts line in the script: Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, vitamin C 30 mg, pineapple fruit powder 100 mg, maltitol and isomalt, not sugar-free. The live where-to-buy sentence should be replaced with that line when Kevin applies the refresh. This pass does not change the guard.
- **Byline.** Live Article schema and `~/genseo/roster.json` both have Dr. Marcus Hale. Mike Moretti is the byline on the 2026-10-21 blog-template samples in the vault and is not in `roster.json`. The proposals keep Dr. Marcus Hale.
- **AgeAura Pure NMN + TMG NAD+ Complex milligrams** (`/products/ageaura-pure-nmn-tmg-nad-complex`). The public product page prints a per-serving milligram line. The 2026-10-08 pack-shot whitelist does not. The NMN proposal states no milligram amount.
- **Creatine days per pouch.** Not calculated. Front OCR lists 90 and no serving size.

## What needs Kevin's GO

1. Apply the three blocks in place (opening plus FAQ). That means `shopify_publisher.py update` only after `validate_article.py` prints PASS. This pass did not update the live posts.
2. Say whether the FloraFresh guard should stay on the Supplement Facts line. Until that GO, drafts keep the label line.
3. Add Mike Moretti to `roster.json` before any byline switch. Not done here.
4. A title or meta test for these 0-click page-1 queries. Titles were left unchanged because the pages already rank.
5. Any ticket or queue append. None was written.

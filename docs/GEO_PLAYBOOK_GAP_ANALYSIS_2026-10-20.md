# GEO playbook gap analysis, 2026-10-20

Wellness Nest blog on wellnessnest.co. This note compares the three-part playbook (daily source intake, citable articles, pillar and spoke clusters) with the GenSEO pipeline that was already publishing 5 articles a day.

Search Console file: `~/PATI/LLM-Wiki/90-sources/gsc-daily/2026-10-20-gsc-raw.csv`. The `current` window is 11 to 17 October 2026. Summed across queries that window is 4,801 impressions and 45 clicks. Rows whose page is a `/blogs/news/` URL account for 530 impressions and 2 clicks. The rest is mostly the homepage and brand navigation.

A read of the live news blog on 20 October 2026 returned 141 published articles.

## Pillar 1. Daily source intake

**Already in the vault.** `scripts/geo_sources_watch.py` watches Google Search Central, OpenAI, Anthropic, and xAI docs and writes `90-sources/geo-official/`. That is search-product documentation, not shilajit, NMN, NAD+, TMG, or probiotic studies. A Search Console export already lands in `90-sources/gsc-daily/`.

**Added on this branch.** `scripts/wellness_sources_intake.py` reads PubMed (Europe PMC MEDLINE records when NCBI returns a block page), NIH ODS fact sheets, and optional health RSS. It assigns each item to a Wellness Nest cluster and writes `90-sources/wellness-intake/YYYY-MM-DD.md` plus `state/wellness-intake.json`.

**Run on 20 October 2026.** 21 PubMed records (3 shilajit, 12 NMN/NAD/TMG, 6 probiotic). NCBI E-utilities returned a block page, so the records came from Europe PMC. NIH ODS and the NIH news feed returned HTTP 403. The health RSS feed returned no items that named these ingredients. The note is `~/PATI/LLM-Wiki/90-sources/wellness-intake/2026-10-20.md`. A highlight is not a claim. A writer opens the paper and logs it before an article cites a number or a mechanism.

No page titled Claims Bible turned up under `~/PATI/LLM-Wiki/20-brands` or `~/PATI/LLM-Wiki/10-foundations`. The rules that already bind drafts stay in force: structure/function language, a fetched claims log, and the label locks in `scripts/florafresh_rules.py`, `scripts/shilasource_resin_rules.py`, and `scripts/ageaura_rules.py`.

## Pillar 2. Articles an answer engine can cite

**Already shipping.** The daily job writes through `skills/genseo-auto-publish/SKILL.md`, `scripts/validate_article.py`, and `scripts/shopify_publisher.py`. Answer-first openings, FAQ headings, roster bylines, and a primary-source link are gate checks. `docs/GEO_CITABILITY_AUDIT_2026-10-17.md` scored 32 recent posts: openings and FAQ blocks were present. Still open on the live site, and not republished by this branch: five posts with no study or regulator link, three FloraFresh posts that repeat the wrong PDP formula, and two Article JSON-LD nodes on every checked URL.

**Template ref, not in this commit.** `.blog-template-v1.ref.md` lists 28 sections and 20 gaps against the current writer (eyebrow, dek, verdict box, a review format, scorecard, a 30-day timeline, a real expert quote, sticky bar, pack-matched blog colors, and a standard related-posts block). The live skills still use the four formats in the article templates. This branch does not turn that ref into the publisher.

**Added on this branch.** `templates/related-questions-block.md` and `scripts/cluster_related_questions.py` print in-body sentences plus a "What to ask next" H2. The block sits before `## Frequently Asked Questions`. It uses ordinary links, not `###` questions, and it does not add a second FAQPage node. The writer skills run that command only when `state/cluster_map.json` already exists. If the file is missing, the outline is unchanged. The daily job does not set `GENSEO_CLUSTER_PICKER`.

## Pillar 3. Pillar and spoke clusters

**Already in the repo, aimed at a different job.** `docs/internal_linking_strategy.md` sends links from pages that already rank toward pages in striking distance. `scripts/pick_cluster_hub.py` and `scripts/find_intent_clusters.py` find cannibalizing URLs and can 301 the losers. `scripts/add_internal_links.py` is a one-off footer list. `scripts/refill_tickets.py` fills the queue from the ideas board and `templates/article-topic-bank.json`, then `scripts/topic_fitness.py` rejects a covered family and segment. None of those build a pillar and spoke map or insert a marked, reversible link into the article body.

**Added on this branch.**

| Script | Role |
|---|---|
| `scripts/wn_clusters.py` | Shared map, topic rank, sentences, and the blog-only URL check |
| `scripts/build_cluster_map.py` | Pillar, spokes, and gaps. Writes `state/cluster_map.json` and `docs/CLUSTER_MAP.md` |
| `scripts/cluster_topic_picker.py` | Next topics from gaps. Off unless `GENSEO_CLUSTER_PICKER` is `1`, `true`, `yes`, or `on` |
| `scripts/cluster_internal_links.py` | In-body links. Default is a dry run. `--apply` writes `backups/<date>/cluster-links-*.json` first. `--rollback` restores that file. Blog `104008483131` only |
| `scripts/cluster_related_questions.py` | The follow-up block for a new draft |

New tickets from the picker are limited to ShilaSource Himalayan Shilajit Resin, AgeAura Pure NMN + TMG (`/products/ageaura-pure-nmn-tmg-nad-complex`), and FloraFresh (Bacillus coagulans SNZ-1969, 15B CFU per 2 gummies). The 2026-10-20 draft of this note recorded a 1-billion count; Kevin set the count to 15B CFU on 2026-10-21. Gummies, Shockwave, and Gold Resin stay in the map as existing URLs and are not used as new shilajit link targets. Ayurveda pages that do not mention shilajit stay in the unclustered group. Pregnancy, disease, and treatment queries are not turned into tickets.

The map built on 20 October 2026 used the live blog titles, word counts from `ALL_ARTICLES.csv`, the current Search Console window, and the intake state.

| Cluster | Live articles | Pillar |
|---|---|---|
| FloraFresh and vaginal probiotics | 20 | Probiotics and Birth Control: Can You Take Both? (US 2026) |
| AgeAura NMN, NAD+, and TMG | 26 | NMN + TMG Benefits: What Human Trials Show (US 2026) |
| ShilaSource and shilajit | 33 | Wellness Nest Shilajit Reviews: What 85 Buyers Report |
| Creatine and FusiForce | 22 | Do Creatine Gummies Expire? 6 Storage Facts (US 2026) |
| Turkesterone | 16 | Turkesterone for Athletes: Drug-Test Guide (US 2026) |
| Menopause archive | 16 | The MenoMate Journey, month 2 week 6 |
| Healthy aging | 0 | none yet |
| Unclustered | 8 | not linked by the backfill |

Clusters with at least one article: 7. Pillars: 7. Articles: 141.

Search Console queries in positions 8 to 30 are mostly brand navigation ("wellness nest", "wellness nest shilajit"). Those do not become new article primaries. One intake gap remains open: primary `nmn for athletes`, from a paper about nicotinamide riboside and exercise training. That paper is not an NMN result. Leave it unread until someone opens it and writes a claims log. The picker is off, so the daily queue does not receive it.

**Link dry run, all published news articles, no Shopify write.** Report: `docs/CLUSTER_LINK_DRY_RUN_2026-10-20.md`.

| Measure | Count |
|---|---|
| Articles with a proposed new link | 133 |
| In-body sentence links | 615 |
| What to ask next links | 659 |
| New link count | 1,274 |
| Shopify writes | 0 |

The 8 unclustered articles are the ones with no proposed links. Marker on every inserted node: `data-genseo-cluster-link`. `--apply` was not run.

## What is still a decision

The 07:30 ICT publisher keeps the current queue. Turn the picker on only for a refill dry run (`GENSEO_CLUSTER_PICKER=1`) after reading `docs/CLUSTER_MAP.md`. A live link backfill waits for an explicit `--apply` after the dry-run report. Rollback is `python3 scripts/cluster_internal_links.py --rollback <backup.json>` and stays a dry run until `--apply` is passed with it.

Creatine and turkesterone articles are interlinked inside their clusters. The picker does not mint new tickets for them. The menopause archive is mapped the same way. No new MenoMate article is proposed.

# Quarterly content audit

Once a quarter, every published Wellness Nest **news** article gets one proposal: **KEEP**, **REFRESH**, **CONSOLIDATE**, or **PRUNE**. The point is to stop the blog filling up with thin posts and near-duplicates.

This is a review sheet. `scripts/quarterly_content_audit.py` does not publish, redirect, unpublish, delete, or edit the theme. Kevin approves every CONSOLIDATE and every PRUNE before anyone runs a writer.

Search Engine Land described the same four-way pass on 2026-10-20. The thresholds below are the ones this repo already uses for duplicates, thin pages, and refreshes.

## What already existed

| Piece | Role | This audit |
| --- | --- | --- |
| `docs/CLUSTER_MAP.md`, `state/cluster_map.json`, `scripts/wn_clusters.py` | Pillar, spokes, cluster id | Catalog and cluster assignment. Impression figures printed in the map are not copied into traffic cells. |
| `topic_fitness.sig_words` and `DUP_JACCARD` (0.72) | Near-duplicate titles | Same tokenizer and bar for a title consolidate |
| `scripts/build_consolidation_map.py` | KEEP / MERGE / REDIRECT from word count plus Search Console | 700-word thin line, and impressions under 20 with zero clicks stay a **refresh** when an impression exists |
| `scripts/prune_dead.py` | Unpublish pages with zero impressions after 100 days | Age gate. A measured impression keeps the URL off the prune list. That script's `--apply` is a separate Mac step. |
| `scripts/find_dupes.py` | Exact-title clusters; near-dupes are report-only | Numbered `-1` / `-copy` handles are flagged. A 301 still waits for approval. |
| `scripts/consolidation_plan.py`, `scripts/refresh_targets.py` | Live Search Console plans | Climb is position 13 or worse. CTR refresh is position 2–8 with CTR under 2% and at least 20 impressions. |
| `scripts/refill_tickets.py` storefront reads | Public sitemap and Atom | Same public blog URLs, with a hard GET cap |

`scripts/consolidation_plan.py` and `scripts/prune_dead.py` talk to Search Console or the Admin API and can change the store when `--apply` is passed. They are not the quarterly sheet. The unmerged publish-time duplicate warning (open PR for `dup_cluster_gate.py`) checks a draft before it is written. It is not imported here.

There was no quarterly KEEP / REFRESH / CONSOLIDATE / PRUNE inventory before this script.

## Scope

In scope: `https://wellnessnest.co/blogs/news/<handle>` on blog `104008483131`.

Report only, with no suggested edit: Home, collections, product pages, checkout, other locales, and ad or email landing listicles (`gsl-` handles, `landing-listicle`). If one of those URLs shows up in an article sitemap, it is listed under **report only**.

MenoMate is not on sale. Serial journey and meal-plan posts can be consolidate proposals. Distinct menopause explainers are judged on their own. Retiring the whole archive is Kevin's decision, not an automatic prune.

## How to run

Offline, from the committed cluster map plus any local caches (`ALL_ARTICLES.csv`, `existing_articles.json`, `PUBLISHED_ARTICLES_TRACKER.csv`, `state/cluster_map.json`):

```bash
python3 scripts/quarterly_content_audit.py --day 2026-10-20
```

Public read of the English article sitemap, the news Atom feed, and article HTML. Cap 200 GETs. Wait between requests. Back off on HTTP 429. Product, collection, page, and locale sitemaps are not requested.

```bash
python3 scripts/quarterly_content_audit.py --crawl --max-gets 200 --delay 0.4 --day 2026-10-20
```

Search Console, only when a real export is on disk. Until then the traffic cells say `needs GSC data`.

```bash
python3 scripts/quarterly_content_audit.py --gsc ~/PATI/LLM-Wiki/90-sources/gsc-daily/YYYY-MM-DD-gsc-raw.csv --day 2026-10-20
```

Outputs: `reports/quarterly-content-audit-YYYY-MM-DD.md` and `.csv`.

```bash
python3 scripts/quarterly_content_audit.py --self-check
python3 -m unittest tests.test_quarterly_content_audit
```

This is not on the daily launchd runner. A reasonable cadence is the first week of January, April, July, and October, on a Mac that has the vault export.

## Decision rules

First matching rule wins, after overlap groups are built. A consolidate loser is CONSOLIDATE even if it is also thin. The stronger page in that group is KEEP or REFRESH, never PRUNE.

### CONSOLIDATE

Merge unique sections into the stronger URL, unpublish the loser, then 301. The stronger page is chosen from real fields only:

1. When a GSC file was loaded: clicks, then impressions, then a better (lower) average position.
2. Cluster pillar, then word count, then inbound news links, then an older known publish date.

Edges, any one of them:

| Edge | Bar |
| --- | --- |
| Title | `topic_fitness` Jaccard ≥ 0.72 inside the same cluster. Cross-cluster title merges need Jaccard ≥ 0.90 so "how long does NMN take" does not absorb the creatine page. |
| Opening | Jaccard ≥ 0.72 on the significant words in the first 2,500 characters, with at least 25 words on each side. Same cluster, unless the score is ≥ 0.90. |
| Primary query | The tracker keyword or the top GSC query has the same significant-word set. Title-derived queries do not count. |
| Segment | Same cluster and the same set of `wn_clusters` segment ids (`dosage`, `for-women`, `how-to-take`, …). Both pages are bare segment pages, or they share a real qualifier. A shared form word such as `gummies` is not a qualifier. "For women" and "for women over 50" are different sets. "On an empty stomach" and "how to take" share a segment id and stay separate when the remaining words differ. |
| MenoMate serial | Titles that are MenoMate Journey or Meal Plan weeks. Distinct menopause explainers are not in this group. The cluster-map pillar still wins the group. If a sibling has a higher measured word count, the owner-decisions list names it so Kevin can pick a different survivor. |

A loser with GSC clicks, or a loser that is the cluster pillar, is marked higher risk in the reason. Read both pages before approving.

A numbered handle (`-1`, `-2`, `-copy`) whose title is actually different is **REFRESH**, not CONSOLIDATE. Compare the bodies. The gut article sitting on a joint-pain slug is that case.

### PRUNE

Proposal only: noindex, or unpublish and then redirect. Two paths:

**GSC file loaded.** Zero clicks and zero impressions (a missing export row counts as zero, and the note says `no row in export`). Body under 700 words. Publish date older than 100 days. Not the pillar and not the winner of a duplicate group. Frozen ids and `generated-article*` handles stay KEEP.

A page with any impression is not pruned. Under 20 impressions and zero clicks, which `build_consolidation_map.py` would call a redirect, is **REFRESH** here because Google has seen the URL.

A long page (700 words or more) with zero impressions is **REFRESH**, not PRUNE. `prune_dead.py` would unpublish it. This sheet leaves that call to Kevin.

**No GSC file.** Body under 400 words, inbound links from other news articles measured at zero, every in-scope body was fetched, publish date older than 100 days, and the cluster has another page. The reason says the prune is structural and still needs Search Console before a URL change.

Unknown word count is blank, not zero, and cannot trigger a length prune. Unknown publish date cannot trigger an age prune. A young page (100 days or newer) is not pruned. HTTP 404 or 410 on the public article URL is PRUNE with a note to confirm the path before adding a redirect.

### REFRESH

Any of these:

- Pillar under 1,500 words.
- Body under 700 words.
- Last updated more than 180 days ago. Publish time is the fallback.
- GSC position ≥ 13 with at least 20 impressions. Add depth. Keep the title.
- GSC position 2–8, at least 20 impressions, CTR under 2%. Sharpen the meta. Keep the title unless a later CTR pass says otherwise.
- Same-cluster title Jaccard from 0.60 up to 0.72 **and** a shared qualifier that is not just `gummies` / `capsules` / `resin`.
- Numbered-handle pair with different titles.

### KEEP

None of the signals above. The page is the stronger copy in a duplicate set and it is not thin or stale.

## Traffic, dates, and word counts

| Field | When it is filled |
| --- | --- |
| `gsc_clicks`, `gsc_impressions`, `gsc_position` | A `--gsc` CSV was read. Cells are `needs GSC data` otherwise. Position is blank when the export has no impressions. A missing row is `0` clicks, `0` impressions, note `no row in export`. |
| `word_count` | Cluster map `(N words)`, `ALL_ARTICLES.csv`, Atom content, or fetched article body. A page with no `articleBody` uses the theme `MainContent` landmark up to the footer. Blank when unknown. Map text such as `73 impressions` is ignored. |
| `internal_links_in` | Count of other news articles whose body links here. `not measured` when bodies were not fetched. |
| `last_updated` | Article `<time datetime>`, then JSON-LD `datePublished` when the template has no time tag, then a sitemap `lastmod` that is not a bulk touch, then the tracker date. |
| `primary_query` | Tracker keyword, else the top non-brand GSC query, else the title. `primary_query_source` says which. |

A sitemap `lastmod` calendar day that covers 40% or more of the article sitemap, and falls within three days of the audit date, is a bulk touch. It is not treated as an editorial update. Staleness uses the publish time instead.

Nothing in the sheet is estimated. A cell with no source stays blank or says `needs GSC data`.

## Who approves what

| Proposal | Approval | After a yes, on the Mac |
| --- | --- | --- |
| KEEP | None. | No edit. |
| REFRESH | Kevin, then the normal article lane. | `validate_article.py --draft` must print `✓ PASS`. Update through `scripts/shopify_publisher.py`. Climbing pages keep their title and only gain sections. |
| CONSOLIDATE | Kevin names the surviving URL. | Copy unique sections onto the winner. Unpublish the loser. Add the redirect only after that URL is no longer 200. `find_dupes.py --apply` remains limited to exact-title dead duplicates. |
| PRUNE | Kevin, after a GSC check when this sheet had no export. | `prune_dead.py` is dry-run first, then `--apply` in a batch, or a noindex. Log the change. |

Bulk redirects still follow the store rule: backup, dry-run, read the diff, then apply. This quarterly script never runs that sequence.

## Columns

`url`, `title`, `cluster`, `primary_query`, `word_count`, `last_updated`, `internal_links_in`, `duplicate_siblings`, `suggested_action`, `reason`.

The CSV also records `primary_query_source`, `word_count_source`, `last_updated_source`, `merge_into`, and the GSC cells above.

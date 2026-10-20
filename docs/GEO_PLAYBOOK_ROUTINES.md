# GEO playbook routines

Times are ICT (UTC+7). The article publisher stays on `~/genseo` at 07:30, with the 08:05 check and the 14:47 catch-up. These routines do not publish, and they do not set `GENSEO_CLUSTER_PICKER`. Run them from the checkout that has this branch after it is merged and pulled. Until then they live on `feat/geo-llmwiki-clusters`.

Do not pass `--apply` on `scripts/cluster_internal_links.py` unless Kevin has read that day's dry-run report and asked for the write. Do not point these commands at pages, products, collections, the theme, or `gsl-*` landing drafts. The link script refuses those URLs.

## Every day, 06:30 ICT

Intake runs before the 07:30 article job so a writer who opens the vault that morning sees the new papers. The publisher itself does not read this note unless someone has built `state/cluster_map.json` and the skill's optional step finds that file.

```bash
python3 scripts/wellness_sources_intake.py
```

Writes `~/PATI/LLM-Wiki/90-sources/wellness-intake/YYYY-MM-DD.md` and `state/wellness-intake.json`. Exit 0 means the note was written. Exit 2 means every live source failed. NCBI often returns a block page. The script then reads the same queries from Europe PMC. NIH pages that return 403 are listed under Skipped and are not invented.

Prompt for a scheduled agent:

```text
Run the Wellness Nest wellness intake. Checkout: the GenSEO repo that publishes (~/genseo after feat/geo-llmwiki-clusters is on main). Command: python3 scripts/wellness_sources_intake.py. Confirm the vault note 90-sources/wellness-intake/<today>.md exists and print the pubmed, ods, and rss counts. Do not publish. Do not set GENSEO_CLUSTER_PICKER. Do not call shopify_publisher.py.
```

## Monday, 06:45 ICT

Rebuild the cluster map after that morning's intake, still before 07:30.

```bash
python3 scripts/build_cluster_map.py --from-shopify
```

This is a GET of published news articles on blog `104008483131`, plus `ALL_ARTICLES.csv` word counts, the latest `90-sources/gsc-daily/*-gsc-raw.csv` (current period only), and `state/wellness-intake.json`. It writes `state/cluster_map.json`, `docs/CLUSTER_MAP.md`, and `~/PATI/LLM-Wiki/90-sources/cluster-maps/YYYY-MM-DD-cluster-map.md`. It does not PUT.

Prompt:

```text
Rebuild the Wellness Nest cluster map. Command: python3 scripts/build_cluster_map.py --from-shopify. Print clusters, pillars, and article counts. Do not publish. Do not pass --apply to any script.
```

## Monday, 18:00 ICT

The 14:47 catch-up should be finished. Dry-run the link backfill and save the report. Leave Shopify unread for writes.

```bash
python3 scripts/cluster_internal_links.py --from-shopify --dry-run --report docs/CLUSTER_LINK_DRY_RUN-$(date +%F).md
```

Read the first lines of the report (article count, link count, `Shopify writes: no`) before anyone talks about `--apply`.

Prompt:

```text
Dry-run Wellness Nest cluster links for every published news article. Command: python3 scripts/cluster_internal_links.py --from-shopify --dry-run --report docs/CLUSTER_LINK_DRY_RUN-<today>.md. Print articles_with_new_links and link_count. Do not pass --apply. Do not edit products, pages, collections, or the theme.
```

## Optional, not on the daily plist

See what the picker would prepend. This does not edit `daily-tickets.md` when `--dry-run` is set.

```bash
GENSEO_CLUSTER_PICKER=1 python3 scripts/refill_tickets.py --count 8 --dry-run
```

The launchd job must keep `GENSEO_CLUSTER_PICKER` unset. New topics from the picker are only ShilaSource resin, AgeAura Pure NMN + TMG, and FloraFresh on its Supplement Facts label.

## If an apply is later approved

`--apply` writes `backups/<date>/cluster-links-<time>.json` for every article it will change, then PUTs `body_html` on blog `104008483131` only.

```bash
python3 scripts/cluster_internal_links.py --from-shopify --apply --limit 10 --report docs/CLUSTER_LINK_APPLY-<date>.md
```

Restore is a dry run until `--apply` is added:

```bash
python3 scripts/cluster_internal_links.py --rollback backups/<date>/cluster-links-<time>.json
python3 scripts/cluster_internal_links.py --rollback backups/<date>/cluster-links-<time>.json --apply
```

A second apply on the same article inserts nothing when `data-genseo-cluster-link` is already present.

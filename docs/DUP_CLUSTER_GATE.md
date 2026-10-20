# Publish-time duplicate cluster gate

`scripts/dup_cluster_gate.py` compares a new ticket or draft with articles already on the local catalog before publish. It does not call Shopify, Search Console, or any other network.

`topic_fitness` inside `validate_article.py` warns from the title alone. This gate adds the primary keyword, the H2s, the slug, and the cluster id, and it separates an exact primary query (FAIL) from a near-duplicate (WARN).

## Verdicts

- **PASS.** The primary query is not the same token set as an existing keyword or title, and the overlap stays under the near-duplicate line.
- **WARN.** Near-duplicate. The line names the existing URL(s). One URL says `refresh existing`. Two or more say `merge`.
- **FAIL.** Exact primary query: after lowercasing and dropping punctuation, years, the market token `us`, and function words, the keyword's content tokens equal an existing tracker keyword or an existing title.

Same-cluster near-duplicate (cluster id is not `other`): Jaccard at least 0.60, or the keyword's ordered tokens are a prefix of an existing title or keyword (at least 2 tokens), or the shared lead is at least 3 tokens and covers at least three quarters of the keyword. Any cluster: Jaccard at least 0.72. H2 tokens raise the score only when that existing page already uses them. A slug equal to an existing handle is the same URL (a refresh) and is skipped.

Cluster ids come from `state/cluster_map.json` when that file is present. Otherwise they come from the `Id:` sections in `docs/CLUSTER_MAP.md`. A handle that is in neither place uses `wn_clusters.assign_cluster`. Map rows also supply titles and URLs that `existing_articles.json` does not have yet. The gate does not read impression or position figures from the map.

`GENSEO_DUP_CLUSTER_BLOCK=1` (also `true`, `yes`, or `on`) makes an exact-query FAIL exit 1, and `validate_article.py --draft` then treats that line as a hard failure. Unset, FAIL is still printed and the draft stays PASS. A warning never changes the exit code.

## Hook

`validate_article.py` calls the gate only in `--draft` mode, after the H2s are collected. The keyword is an optional `<!-- primary_keyword: ... -->` comment, otherwise the H1. The slug is the draft filename.

## Dry-run (2026-10-20)

```bash
python3 scripts/dup_cluster_gate.py --queue daily-tickets.md
```

Exit 0. Mode `warn-only`.

Catalog actually read (no network):

- `/Users/kevinkreative/genseo/existing_articles.json` (read-only; this checkout does not have its own copy)
- `PUBLISHED_ARTICLES_TRACKER.csv` in this worktree (49 keywords)
- `/Users/kevinkreative/genseo/state/cluster_map.json` (built 2026-10-20, 143 articles). `docs/CLUSTER_MAP.md` in this repo is the fallback when that json file is absent (141 of the same links).

Merged catalog: 159 handles. Open tickets in `daily-tickets.md`: 37. Result: **31 PASS, 5 WARN, 1 FAIL.**

The runner's next open ticket is `#CA1016-7`, which would WARN.

| Ticket | Verdict | Existing URL | Action |
|---|---|---|---|
| `#CA1016-7` vaginal probiotics over 60 | WARN overlap 1.00 | https://wellnessnest.co/blogs/news/vaginal-probiotics-over-60-5-checks-in-the-us | refresh existing |
| `#CA1016-8` creatine gummies on an empty stomach | FAIL exact primary query | https://wellnessnest.co/blogs/news/creatine-gummies-on-an-empty-stomach-us-guide | refresh existing |
| `#CA1016-9` how to take nmn | WARN overlap 0.83 | https://wellnessnest.co/blogs/news/how-to-take-nmn-a-capsule-routine-in-the-us | refresh existing |
| `#CA1016-10` vaginal probiotics for fertility | WARN overlap 1.00 | https://wellnessnest.co/blogs/news/vaginal-probiotics-for-fertility-limits-in-the-us | refresh existing |
| `#CA1016-11` nmn price | WARN overlap 0.43 | https://wellnessnest.co/blogs/news/nmn-price-bottle-vs-serving-cost-in-the-us | refresh existing |
| `#CA1017-8` how much creatine gummies cycling | WARN overlap 0.57 | https://wellnessnest.co/blogs/news/creatine-gummies-while-traveling-how-much-us-2026 | refresh existing |

`#CA1016-7` and `#CA1016-10` stay WARN on the ticket keyword because the live titles still contain `checks` or `limits`. A draft whose H1 repeats that full title would print FAIL at publish time. `#CA1017-8` shares the lead "how much creatine gummies" with the live traveling article and then names a different situation (cycling). The other 31 open tickets passed, including the "with food" variants.

No search volumes or rankings were computed.

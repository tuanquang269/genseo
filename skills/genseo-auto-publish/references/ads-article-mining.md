# Ads → Article Mining — turn paid search terms into blog tickets

Repeatable recipe for refilling `daily-tickets.md` from live Google Ads data.
First run: 2026-08-07 → batch 2 (tickets #8–#12). Run it again whenever the
queue has **< 3 pending `[ ]` tickets**, or weekly.

## Why this works (the economics)

The blog's highest-leverage topics are the search terms the ad account ALREADY
pays for. Two goldmine classes:

1. **Paid-but-not-converting terms** — e.g. `US · Shilajit · Category` spent
   ~$210/90d on "shilajit gummies"/"shilajit" with **0 conversions**. A Shopping
   ad is the wrong answer to a research-intent query; an article is the right
   one. Organic capture = the click we stop paying $3–4.6 for.
2. **Converting query patterns** — e.g. "barbara o neill shilajit" (17 clicks,
   ≈$52, 1 conv). Proven buying intent → an owned article compounds it free.

## Hard rules (inherited, non-negotiable)

- **Exact live `campaign.name`, verbatim, every mention** — never paraphrase,
  translate, or normalize. Names contain pipes/double spaces (e.g.
  `ADC | Shopping | DE | Branded | Shilajit Essential Extract |  LP | TROAS 250%`,
  `[S] Search - SLG - Slovakia  - 2303`) → put them in code spans / bullets,
  NEVER in a Markdown table (pipes break cells).
- Blog output stays **English, US-anchored** (validate_article.py enforces).
  This account's data is DE-heavy — mine the INTENT pattern, write for US.
  A DE-language content lane is a Kevin decision; flag, don't build.
- Cost fields are **micros** (÷1,000,000 = account currency).
- Every ticket keeps the standard gates: STEP 0 dedup, STEP 0.5 topic fitness,
  live-URL verification, `--product-ref` image rule.

## Access

Google Ads MCP (`mcp__google-ads__*`). `list_accounts` → WellnessNest =
`7385813335`. Run queries with `run_gaql` / `execute_gaql_query`.

**GAQL gotchas (hit 2026-08-07):**
- `DURING LAST_90_DAYS` is NOT a valid literal → use
  `segments.date BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'` (compute the dates).
- `WHERE` supports only AND — no OR. For multi-pattern matching use
  `REGEXP_MATCH` (RE2 syntax).

## The 4 slices

```sql
-- 1. What converts (mine the PATTERN, not just the term)
SELECT campaign.name, search_term_view.search_term, metrics.clicks,
       metrics.cost_micros, metrics.conversions
FROM search_term_view
WHERE segments.date BETWEEN '<start>' AND '<end>' AND metrics.conversions > 0
ORDER BY metrics.conversions DESC LIMIT 50

-- 2. Paid-but-not-converting spend (the arbitrage list)
SELECT campaign.name, search_term_view.search_term, metrics.clicks,
       metrics.cost_micros, metrics.conversions
FROM search_term_view
WHERE segments.date BETWEEN '<start>' AND '<end>' AND metrics.clicks > 5
ORDER BY metrics.cost_micros DESC LIMIT 50

-- 3. US lane focus (blog is US-anchored)
SELECT campaign.name, search_term_view.search_term, metrics.clicks,
       metrics.cost_micros, metrics.conversions, metrics.impressions
FROM search_term_view
WHERE segments.date BETWEEN '<start>' AND '<end>'
  AND campaign.name LIKE '%US%' AND metrics.impressions > 10
ORDER BY metrics.cost_micros DESC LIMIT 40

-- 4. Question / comparison phrasing (article-shaped queries)
SELECT campaign.name, search_term_view.search_term, metrics.clicks,
       metrics.cost_micros, metrics.impressions
FROM search_term_view
WHERE segments.date BETWEEN '<start>' AND '<end>'
  AND search_term_view.search_term REGEXP_MATCH
      '.*(how|what|best|does|dosage|vs|review).*'
ORDER BY metrics.impressions DESC LIMIT 30
```

## Pattern → article-type map

| Term pattern | Article type | Batch-2 example |
|---|---|---|
| Category term, US spend, 0 conv | PPC-arbitrage buyer guide | #8 best shilajit gummies |
| `<competitor brand> <product>` | Named comparison (specs off their LIVE pages only; unpublished spec = "not disclosed") | folded into #8 |
| `<influencer name> <ingredient>` | Authority-figure POV review (NEVER imply endorsement) | #9 Barbara O'Neill |
| `<term> for men/for women/over 40` | Audience-segment deep-dive | #10 benefits for men |
| `<brand> erfahrungen/reviews/recenzie/testsieger` | Review-roundup, brand-SERP defense (only REAL store reviews) | #11 |
| `<brand> amazon/dm/kaufen/where to buy` | Retail-availability + anti-fake | #12 (lowest priority) |
| how/what/does question terms | Question long-tail (check dedup first — "what is shilajit" was already covered) | — |

## Ticket writing checklist

1. **Dedup before drafting a ticket:** Admin API list of published article
   titles (`blogs/<BLOG_ID>/articles.json?fields=title,handle,published_at`)
   + tracker CSV + the coverage list in daily-tickets rule 6.
2. **Verify hero handle live:** `https://wellnessnest.co/products.json?limit=250`
   → confirm handle + current price; put both in the ticket.
3. **Evidence line is mandatory:** verbatim campaign.name + clicks/cost/conv
   + window. A ticket without evidence is an opinion.
4. Append as a new `# Batch N` section with source header (account, window,
   method pointer to this file); number tickets sequentially.

## Second-pass lane (not yet run for batch 2)

**GATC competitor scrape** — Google Ads Transparency Center for competitor
domains surfaced by slice results (Aphroly, Erth Wellness, Better Alt…).
Script template: `~/PATI/library/intel-briefs/nuora-google-ads-2026-07-16-assets/scrape_nuora.py`
(swap domain). Winner proxy = run-length × variant-count only. Long-running
competitor ads answer "which angles sustain spend" → presell/advertorial-style
article tickets. Run when a batch needs angle depth, not just keywords.

## Ops findings — hand to ads-ops, do NOT turn into tickets

Log anything that is an account problem, not a content gap. 2026-08-07:
`[S] Shopping DE - 2003` matched junk-broad terms ("die 10 besten
nahrungsergänzungsmittel", "fohow produkte", "beste ayurveda produkte") —
negative-keyword hygiene, belongs to the Google Ads takeover lane, not the blog.

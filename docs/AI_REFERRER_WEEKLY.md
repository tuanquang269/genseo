# Weekly AI referrer report

Counts wellnessnest.co sessions and orders by **referrer domain**. It does not count by UTM. It is a read. It does not publish, and it does not edit a page, product, collection, or theme.

The template with every cell `unknown` is `docs/AI_REFERRER_REPORT_TEMPLATE.md`. `scripts/aeo_tracker.py` is a different tool (prompt mentions). This report is store traffic.

## Flagged window

2026-10-15 through 2026-10-20 is a possible ChatGPT UTM-bug window. Search Engine Land reported on 2026-10-15 that ChatGPT links may have dropped `utm_source=chatgpt.com` and may suppress the HTTP referrer, so some visits show up as direct. OpenAI has not confirmed it.

https://searchengineland.com/chatgpt-appears-to-drop-utm-tracking-making-ai-referral-traffic-harder-to-measure-496552

The vault note is `~/PATI/LLM-Wiki/90-sources/search-engine-land/sel-digest-2026-10-16.md` (item 1). The report always names that window. When the week overlaps it, the ChatGPT row is still the domain count only. Blank and direct rows are not added into ChatGPT. The script does not estimate a correction. A lower domain count in the window is not evidence that traffic stopped.

## Run

```bash
python3 scripts/ai_referrer_report.py
python3 scripts/ai_referrer_report.py --since 2026-10-14 --until 2026-10-20
python3 scripts/ai_referrer_report.py --template
```

No dates means the seven complete days ending yesterday. `SINCE` / `UNTIL` are calendar dates. ShopifyQL applies the shop timezone. A later read of a recent day can move.

## What is counted

| Column | ShopifyQL | Grain |
| --- | --- | --- |
| Sessions | `FROM sessions SHOW sessions GROUP BY referrer_domain` | Online store session |
| Orders | `FROM sales SHOW orders GROUP BY order_referrer_domain` | Order, once |

API version is `SHOPIFY_API_VERSION` or `2026-04`. On that version the sessions schema has no `orders` / `num_orders` column, so orders come from `sales`. The two columns are not a conversion rate.

Hosts that count:

| Engine | Domains |
| --- | --- |
| ChatGPT | `chatgpt.com`, `chat.openai.com` |
| Perplexity | `perplexity.ai` |
| Gemini | `gemini.google.com`, `bard.google.com` |
| Copilot | `copilot.microsoft.com` |
| Claude | `claude.ai` |
| Grok | `grok.com`, `x.ai` |

`www` is stripped. A subdomain counts (`grok.x.ai` is Grok). These do not count: `x.com`, `google.com`, `openai.com`, `microsoft.com`, `my.many.chat`. You.com, Phind, Meta AI, Poe, and DeepSeek are extra rows only when a read actually sees them.

`referrer_source = direct` and a blank referrer domain are separate rows. Do not add them to each other or to an engine.

A finished group-by that omits a domain is 0. If the result hits the row limit (default 1000), that metric is `unknown`, not a partial total. A cell that does not parse is `unknown`, not 0.

UTM is a diagnostic line only (`utm_source=chatgpt.com`, plus any other value containing `chatgpt`). It is never added to the ChatGPT row.

## Credentials

The script calls `shopify_auth.pick({"read_reports"})`.

1. Kevin's CLI app (`SHOPIFY_CLI_APP_SHOP`, `SHOPIFY_CLI_APP_CLIENT_ID`, `SHOPIFY_CLI_APP_CLIENT_SECRET` in the checkout `.env`, via `scripts/shopify_app_token.py`) when that app already has `read_reports`.
2. Otherwise the publisher token in `$GENSEO_CONFIG` or `~/.genseo/shopify_token.json` (`scripts/genseo_config.py`).

Checked 2026-10-21: both existing tokens already include `read_reports`, `read_analytics`, `read_orders`, and `read_all_orders`. The script does not request a new token or a new scope. The GraphQL documents are queries (`shopifyqlQuery`, and an orders referrer read). There is no mutation.

If Shopify refuses the read, the report says `needs scope read_reports`, sessions and orders are `unknown`, and the process exits 2.

When the sales query fails for a reason other than scope, orders fall back to `customerJourneySummary.lastVisit.referrerUrl` (REST `referring_site` in a fixture). `landing_site` / `landingPage` is the on-site landing URL and is not the referrer. If that walk passes 2000 orders, orders stay `unknown`.

## CSV import

Use this when the token cannot read reports. Export the referrer domain from Shopify Analytics, not the UTM columns.

```bash
python3 scripts/ai_referrer_report.py --csv export.csv --csv-complete --since 2026-10-14 --until 2026-10-20
```

Header names it accepts (any case): `referrer_domain`, `session referrer domain`, `order referrer domain`, `sessions`, `orders`, and optional `day` or `date` (`YYYY-MM-DD`).

- `--csv-complete` means the file is the full domain list. An omitted engine is 0.
- Without that flag, an omitted engine stays `unknown`.
- A file that only has UTM columns is rejected. Exit 2. Nothing is counted.
- A blank metric cell is `unknown`, not 0.
- Direct `referrer_source` is `unknown` on a CSV import. The file does not contain that cut.

## Tests

```bash
/usr/bin/python3 tests/test_ai_referrer_report.py
bash tests/run_suite.sh
```

The unit tests do not call Shopify.

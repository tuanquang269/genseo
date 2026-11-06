# AI referrer report template

This file is the markdown from `python3 scripts/ai_referrer_report.py --template`. Every number is unknown. It is not a wellnessnest.co traffic read. Run the script to fill a week. The operator notes are in `docs/AI_REFERRER_WEEKLY.md`.

# Weekly AI referrer report — wellnessnest.co

- Period: 2026-10-14 through 2026-10-20
- Counted by: referrer domain. Not counted by UTM.
- Sessions field: ShopifyQL `sessions.referrer_domain`.
- Orders field: ShopifyQL `sales.order_referrer_domain` (the sessions schema on API 2026-04 has no orders column).
- Queried at: not run
- Source: template — not a store read
- Shop timezone: ShopifyQL applies the shop timezone to SINCE and UNTIL.

## Possible ChatGPT UTM-bug window

Flagged window: 2026-10-15 through 2026-10-20.
Search Engine Land reported on 2026-10-15 that ChatGPT links may have dropped utm_source=chatgpt.com and may suppress the HTTP referrer, so some visits show up as direct. OpenAI has not confirmed it.
Article: https://searchengineland.com/chatgpt-appears-to-drop-utm-tracking-making-ai-referral-traffic-harder-to-measure-496552
This report overlaps that window (2026-10-15 through 2026-10-20).
The ChatGPT row is the referrer-domain count only. It is not a UTM count.
A lower domain count inside the flagged window is not evidence that ChatGPT traffic stopped.
Blank referrer domains and direct sessions are not relabeled as ChatGPT.
This report does not estimate a correction for the UTM-bug window.
Missing data is unknown.

Diagnostic, not a count: sessions with utm_source=chatgpt.com in this period: unknown.
Those sessions are not included in the ChatGPT row.

## Sessions and orders by AI referrer domain

Subdomains of the listed hosts count. www is ignored. x.com is not Grok. google.com is not Gemini. openai.com is not ChatGPT.
Sessions and orders are separate queries. Do not read the pair as a conversion rate.

| Engine | Domains counted | Sessions | Orders |
| --- | --- | --- | --- |
| ChatGPT | chatgpt.com, chat.openai.com | unknown | unknown |
| Perplexity | perplexity.ai | unknown | unknown |
| Gemini | gemini.google.com, bard.google.com | unknown | unknown |
| Copilot | copilot.microsoft.com | unknown | unknown |
| Claude | claude.ai | unknown | unknown |
| Grok | grok.com, x.ai | unknown | unknown |

AI total (engine rows only): sessions unknown, orders unknown.

## Not an AI referrer

Blank referrer domain, referrer_source = direct, and other domains are different ShopifyQL cuts. Do not add them together.

| Bucket | Sessions | Orders |
| --- | --- | --- |
| Blank referrer domain | unknown | unknown |
| referrer_source = direct | unknown | unknown |
| Other referrer domains | unknown | unknown |

## Notes

- Template only. Every number is unknown until a ShopifyQL read or a CSV import fills it.
- Do not replace unknown with a guess.

CSV import, when ShopifyQL is unavailable: `python3 scripts/ai_referrer_report.py --csv export.csv --csv-complete --since 2026-10-14 --until 2026-10-20`.

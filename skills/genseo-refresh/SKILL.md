---
name: genseo-refresh
description: >
  Autonomously REFRESH an EXISTING published US article to recover rankings/clicks —
  WITHOUT creating a new URL. Diagnoses whether the page needs to CLIMB (more depth, stuck on
  page 2) or needs CTR (ranks well but no clicks), then upgrades it and re-publishes IN PLACE
  via the Shopify UPDATE path. Built for a cheap model: follow every step literally and pass
  the mechanical gate before publishing. Trigger: /genseo-refresh with an ARTICLE_ID + keyword.
metadata: {"clawdbot":{"emoji":"♻️","requires":{"commands":["python3","curl"]},"os":["linux","darwin","win32"]}}
---

# GenSeo Refresh — Recover Existing Articles (UPDATE in place, never recreate)

You improve ONE existing US article so it ranks higher and/or earns more clicks. The
market is **US only**. You are a cheap model: **follow this literally**, do not improvise.

## ⛔ THE GOLDEN RULES OF REFRESH (breaking these destroys rankings)
1. **NEVER change the URL/handle.** You publish via the UPDATE path with the existing ARTICLE_ID.
   A new URL throws away all the ranking history this page has built.
2. **NEVER delete content that is working.** Refresh = ADD and IMPROVE, not rewrite-from-scratch.
   Keep the sections that already rank; expand the thin parts; never make the article shorter.
3. **NEVER change the page's core topic / primary keyword.** Sharpen it, don't pivot it.
4. **This is an UPDATE, not a new article.** Do NOT run the duplicate-check or create-article path.

## INPUT (from the refresh ticket)
- ARTICLE_ID (required — the existing Shopify article to update)
- PRIMARY_KEYWORD (the query this page should win)
- BLOG_ID (default 104008483131)

## STEP 0 — PULL THE CURRENT ARTICLE + ITS PERFORMANCE
1. Fetch the live article (title + body) you are about to improve:
   `curl -s "https://wellnessnest.co/admin/api/2026-04/blogs/BLOG_ID/articles/ARTICLE_ID.json" -H "X-Shopify-Access-Token: <token>"`
   (or read it from `published_drafts/` if the draft exists). Save the current body — you will build ON it.
2. Pull what queries it ranks for and its position/CTR (US only):
   `python3 ~/genseo/scripts/gsc_fetcher.py fetch_url_data https://wellnessnest.co/ <full_article_url>`

## STEP 1 — DIAGNOSE (this decides what you do)
Look at the page's current average position for its primary keyword:

- **CLIMB problem — position 13+ (stuck on page 2):** the page isn't deep/relevant enough to reach
  page 1. → Your job is mostly CONTENT: add depth, a comparison table, more specific US detail,
  internal links, and fully cover the sub-questions competitors answer that this page misses.
- **CTR problem — position 4–12 but low/zero clicks:** the page already ranks; it just isn't
  earning the click. → Your job is mostly TITLE + META + ANSWER BLOCK. Do NOT bloat the content.
  Rewrite the title and meta to win the click (see STEP 3 CTR rules), and tighten the answer block.
  ⚠️ If position is 1–8 with 0 clicks, an AI Overview may be taking the click — note this in your
  output; a refresh helps but may not fully recover it.
- **Both:** position 9–13 → do both: light depth + strong title/meta.

State your diagnosis in one line before editing (e.g. "DIAGNOSIS: CLIMB — pos 19, 2,573w, needs page-1 depth").

## ⚠️ WHY EARLIER REFRESHES FAILED (read first)
A June 2026 audit found ALL 5 refreshed pages DROPPED in position. Root cause: the refresh
(a) changed the TITLE of pages that already ranked, and (b) regenerated body content. Both reset
a ranking page's relevance signals. **A page that already ranks is fragile — the smallest change
that adds value wins. Adding a table is safe; rewriting the title or the body is not.**

## STEP 2 — APPEND-ONLY: add what's missing, never rewrite what ranks
The existing body is WHY the page ranks. Preserve it. Your edit = existing body kept VERBATIM,
with new blocks APPENDED. Do NOT regenerate, reword, reorder, or trim existing paragraphs/headings.
Append only the blocks the page is missing:
- **Answer-first block** — first paragraph (40–60 words) directly answers the primary question, contains "the US".
- **≥1 comparison `<table>`** with clear headers (AI Overviews extract these).
- **"Where to Buy in the US"** section with an $price range, fast local delivery, authenticity.
- **≥2 internal links to the matching `/collections/` page**, plus 1–2 links to related existing articles.
- **PRIORITY BRANDS FIRST (feature naturally where relevant):** your priority
  vendor list goes here. Never mention or link a vendor you do not stock.
- **4 FAQs**, ≥1 US-specific.
- **Named author** from the roster with a live `/pages/` link (see auto-publish roster). Schema author = that Person.
- **Self-contained H2 sections**; no "as mentioned above".
- Target depth: most refreshes should end up **1,200–1,800 words** (deeper than the thin original), but
  never pad — every added sentence must add real value (specs, $prices, comparisons, genuine use cases).
- Images: if the article lacks product lifestyle images, generate them (image-to-image off real product photos).

## STEP 3 — TITLE: depends on diagnosis (changing a ranking title is what sank the last batch)
- **CLIMB pages (pos ≥13): KEEP THE EXISTING TITLE.** Do NOT rewrite it. The only allowed change is
  freshening a stale year in place (e.g. "(2024)"/"(2025)" → "(2026)") — keep every other word identical.
  A CLIMB page's title is part of why it ranks; resetting it drops the page. The new `# ` line of the
  draft must equal the current article title (year-bumped at most).
- **BOTH pages (pos 9–13): KEEP THE EXISTING TITLE** — treat the title like a CLIMB page (year-bump
  at most). The depth additions are your fix; improve only the meta description for CTR.
- **CTR pages (diagnosis = CTR, pos ≤12 with low clicks): rewrite the title + meta** — that IS the fix
  for these. Title ≤60 chars, keyword front-loaded, one click trigger; kill boilerplate. Meta 140–155
  chars, answer-first + a differentiator ($price, "100% authentic", "next-day US delivery").
  For a CTR title rewrite you MUST put `<!-- title-change-approved -->` on its own line in the draft —
  the publisher mechanically refuses any title change without it (it keeps the live title instead).
- Meta description (`<!-- meta_description: ... -->`) may be improved on any page — it doesn't affect ranking,
  only CTR, so it's always safe to sharpen.

## STEP 4 — MECHANICAL GATE (must PASS before publishing)
Save the upgraded draft, then run the validator. Do NOT publish until it prints `✓ PASS`:
```
python3 ~/genseo/scripts/validate_article.py ~/genseo/published_drafts/<refresh_draft>.md --draft
```
Fix every `✗` and re-run until PASS.

## STEP 5 — PUBLISH IN PLACE (this EXACT command — no other method)
**You MUST publish by running this exact command. Do NOT use the Shopify MCP, GraphQL,
`update-product`, curl, or any other method to update the article.** Only this python
publisher rebuilds the Article + FAQPage JSON-LD schema and sets the named author. Any other
publish path silently drops the schema and breaks E-E-A-T/AEO.
```
python3 ~/genseo/scripts/shopify_publisher.py update ~/genseo/published_drafts/<refresh_draft>.md BLOG_ID ARTICLE_ID
```

## STEP 5b — POST-PUBLISH REPAIR + VERIFY (mechanical, self-healing — ALWAYS run both)
Immediately after publishing, run these two commands in order:
```
python3 ~/genseo/scripts/repair_schema.py ARTICLE_ID BLOG_ID
python3 ~/genseo/scripts/verify_published.py ARTICLE_ID BLOG_ID
```
- `repair_schema.py` reads the LIVE article and, if the Article or FAQPage JSON-LD schema is
  missing (e.g. because the publish skipped it), rebuilds it FROM the live HTML and injects it.
  It is idempotent — safe to run even when the article is already healthy.
- `verify_published.py` then confirms the live article has schema + named author + table.
- Do NOT mark the ticket DONE until `verify_published.py` prints `✓`. If it still fails,
  the article has no visible FAQ section to build schema from — fix the draft and re-publish.

## STEP 6 — MARK DONE
In `refresh-jun26-60-tickets.md`, mark the ticket `[DONE]` and record: the diagnosis, the old vs new
title, old position, and the publish timestamp. Then continue to the next ticket if asked.

## HARD RULES (failing any = do not publish)
- UPDATE in place with ARTICLE_ID. Never create a new article, never change the handle.
- Never shorten a working article. Never pivot its topic. Never mention out-of-stock brands.
- Must pass `validate_article.py` (✓ PASS) before the UPDATE command runs.

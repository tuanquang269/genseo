# Daily Article Workflow Upgrade — 2026-06-05
*Goal: let the cheap Antigravity model (Gemini Flash 3.5 / Pro 3.1) produce deep,
core-update-safe articles by ENFORCING quality mechanically instead of hoping for it.*

## The diagnosis
The daily pipeline was sound on paper but produced thin output because the only quality
check was an **advisory self-checklist** a fast model could tick without meeting. Result:
the large majority of articles earned almost no impressions. During a core update that
demotes thin/scaled content, that hit-rate is the core problem — not the cadence.

**Conclusion on cadence:** daily is FINE (you have plenty of uncovered query runway and AI does the
writing). The fix is a hard quality gate, not slowing down. Daily *deep* > weekly.

## The pipeline (how it actually runs)
1. Cron → Antigravity: "continue with next 2 tickets in `2ndRound_120_tickets.md`" (09:00 & 16:00)
2. Antigravity reads the next pending ticket → invokes **`genseo-auto-publish`** (the orchestrator)
3. Orchestrator: research → write markdown draft → generate images (nanobanana) → **GATE** → publish

## What changed (the enforcement)
**1. New mechanical gate: `scripts/validate_article.py`** — runs as code, cannot be faked.
Checks: word count ≥900, answer block w/ "the US", a comparison table, $price range,
≥2 `/collections/` links, named roster author with a LIVE `/pages/` link, 4 FAQs, brand
mentions, image alt text, AND every product/collection/author URL returns 200 (no 404s).
- `--draft` mode for the markdown draft (FAQPage schema added post-conversion → warn only).
- Tested: PASSES the deep expanded articles, FAILS every current thin draft.

**2. The REAL orchestrator now enforces it** (`skills/genseo-auto-publish/SKILL.md`
and the identical `skills/` copy — both updated, backup in
`backups/20260605/skills/`):
- **STEP 0 (new): duplicate check** against the LIVE site before writing — prevents the
  cannibalization that cost the atlas/agym/cbum traffic (and would've duplicated ticket #71).
- **STEP 6 (rewritten): mechanical gate** — must print `✓ PASS` before publishing. No PASS, no publish.

**3. Supporting skill copies in `Bot/genseo/skills/`** (content-writer, publisher) rewritten
to the same standard for reference/consistency.

## The quality bar every article must now clear
900–1400 words · answer-first block · 1 comparison table · "Where to buy in US" w/ $price ·
≥2 collection links · 4 FAQs (≥1 US-specific) · named author (real /pages/ link) · Article +
FAQPage schema (author = named Person) · real product links (no 404s) · not a duplicate.

## What this does NOT fix (be honest)
- It enforces *structure & depth*, not *brilliance*. A cheap model can pass the gate with
  competent-but-not-genius content. That's fine — competent + deep + US-specific beats thin.
- Off-site **Brand Authority (32/100)** is untouched — still the biggest remaining GEO gap.
- The 26 remaining tickets in `2ndRound_120_tickets.md` still carry the old trigger prompt;
  they'll route through the upgraded orchestrator, but their `[DONE]` flags are out of sync
  with the live site (hence STEP 0 dup-check is essential).

## How to test it caught on (next cron run)
After the next 09:00/16:00 run, check the new article with:
`python3 scripts/validate_article.py <new_article_url_or_draft>` — it should PASS.
Track US hit-rate weekly with `python3 scripts/sg_report.py 14`. The success metric:
% of new articles reaching ≥10 US impressions should climb substantially.

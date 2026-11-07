---
name: genseo-aeo-tracker
description: Record Wellness Nest AI visibility with mention and citation kept separate. Unknown stays unknown. Use when aeo_tracker.py reports a gap or a legacy Gemini mention count.
---

# GenSeo AEO tracker

You record what an answer engine actually showed. You do not invent a score, a snippet, or a source URL.

> **2026-10-09:** `knowledge_base/AEO_GEO_GUIDELINES.md` §6 wins where this skill conflicts with it. No planted mentions. No separate fan-out pages.

## When to use

- `python3 scripts/aeo_tracker.py report` shows a disagreement gap.
- The legacy `python3 scripts/aeo_tracker.py "<query>"` line says mention and citation are unknown, or it prints a Gemini mention count with citation still unknown.

## Fields

Per brand, per prompt, per platform:

- `brand_mentioned`: yes / no / unknown, with a quoted snippet when yes.
- `domain_cited`: yes / no / unknown. Yes means a `wellnessnest.co` URL is in that platform's source list.
- Competitor mentions and citations, only for names that were actually in the answer or the source list.

Platforms: ChatGPT, Gemini, Google AI Mode, AI Overviews, Perplexity, Grok/X.

Brands: AgeAura Pure NMN + TMG NAD+ Complex; Wellness Nest / ShilaSource (the mention match is ShilaSource; "Wellness Nest" is `store_mentioned`); FloraFresh.

Read `docs/AI_VISIBILITY_MENTION_CITATION.md` before editing the ledger.

## What a gap means

- **Mentioned but not cited.** On-page citability. The checks are `scripts/geo_citability.py`, enforced by `validate_article.py`. See `docs/GEO_CITABILITY_AUDIT_2026-10-17.md`. Do not re-implement them.
- **Cited but not mentioned.** The page that was cited needs the canonical product name. AgeAura is AgeAura Pure NMN + TMG NAD+ Complex only. ShilaSource is ShilaSource Himalayan Shilajit Resin. FloraFresh is FloraFresh Vaginal Probiotics Gummies.

Draft PR #75 (off-page listicle gaps) is a web-search measurement with `ai_citation_observed: false`. Do not paste those rows into this ledger as citations.

## Commands

```bash
python3 scripts/aeo_tracker.py self-check
python3 scripts/aeo_tracker.py validate data/ai_visibility/observations.json
python3 scripts/aeo_tracker.py report
```

`adapt` calls an API only when that platform's key is already in the environment. Google AI Mode and AI Overviews are manual. Do not buy a key, create an account, or call a paid tool that is not already configured.

## Do not

- Fill unknown with a guess.
- Publish, email, or edit the theme from this skill.
- Treat a legacy Gemini mention count as an AI Overview citation.

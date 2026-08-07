# GenSeo & Your Brand - Autonomous SEO Agent Ecosystem

## Vission & Current Board
The goal is to build an autonomous "SEO Agent Team" that operates on a continuous feedback loop: `THINK -> ACT -> OBSERVE` mimicking the top-tier SEO architectural frameworks.

Currently, we have successfully developed the "ACT" layer and the "THINK" layer:
- ✅ **Tool Content A+**: `genseo-content-writer` (Strict API handle pulling, EEAT Markdown formatting, AI Image reference-generation).
- ✅ **Tool Publisher**: `genseo-shopify-publisher` (Direct CDN Upload integrations, Automated Schema attachment, Author setting).
- ✅ **Tool Strategist**: `genseo-seo-strategist` (The Brain. Reads independent Knowledge Bases to formulate AEO/GEO Content Briefs).
- ✅ **Knowledge Base**: Hosted locally at `/knowledge_base/` storing modular AEO and EEAT rules.

---

## 🎯 Strategic Roadmap (To-Do List)

To complete the Autonomous Agent Orchestrator loop, we need to implement the following 4 core upgrades. This file acts as our persistent memory across AI sessions.

### Phase 1: Auto Schema Markup Engine
- [x] Upgrade `genseo-content-writer` to natively output valid JSON-LD.
- [x] Support `FAQPage` schema (pulling from H3 tags).
- [x] Support `Article` and `Product` (Reviews) schema automatically injected via the `shopify_publisher`.

### Phase 2: Agent Orchestrator & Feedback Loop (The Brain)
- [x] Create a new Python daemon / Cron job script: `agent_orchestrator.py`.
- [x] Connect `gsc_fetcher.py` to pull weekly ranking changes for top 100 keywords.
- [x] Define the trigger rule: **If Ranking drops > 5 spots -> Trigger `genseo-content-refresh`**.
- [x] Automate the pipeline: Refresh Content -> Audit -> Publish via Shopify -> Log to Knowledge Base.

### Phase 3: Full Site Crawler (Deep Technical Audit)
- [x] Expand `genseo-seo-optimizer` from single-page analysis to a multi-page crawler.
- [x] Scan full site XML sitemap.
- [x] Detect: 404 Broken Internal Links, Missing H1s, Bad Alt Texts, and Orphaned Pages.
- [x] Feed broken link data automatically back to the Agent Orchestrator to propose bulk-fixes via Shopify Article API.

### Phase 4: AEO (AI Engine Optimization) Tracker
- [x] Create a skill: `genseo-aeo-tracker`.
- [x] Automatically simulate prompts on external LLM APIs (OpenAI/Perplexity/Anthropic): "Where to buy Creatine in {{MARKET}}?"
- [x] Calculate a probabilistic "Brand Mention Score" for Your Brand.
- [x] If the score is low, instruct `genseo-content-writer` to generate PR-style entity content targeting AI models.

---

## 📝 Activity Log
*This section tracks what was accomplished across all coding sessions.*

- **[2026-04-12]**: 🎯 **MASSIVE MILESTONE**: Successfully deployed the 4-Phase Autonomous GenSeo Framework. Implemented the JSON-LD Schema Engine, GSC Orchestrator Watcher, Technical Sitemap Crawler, and AEO Brand Tracker LLM Simulator. Re-architected system into a modular Knowledge Base + Brain + Muscle execution model.
- **[2026-04-11]**: Successfully replaced manual search queries with strict Shopify API `handle` lookups for flawless Internal Linking.
- **[2026-04-11]**: Resolved Shopify CDN Upload 403 Forbidden error by injecting `write_themes` into the OAuth Scopes.
- **[2026-04-11]**: Resolved duplicate Thumbnail image issue by dynamically snipping the first markdown image on publish.
- **[2026-04-10]**: Created `genseo-shopify-publisher` using direct REST API integration instead of generic headless browsers.

# AEO & GEO Guidelines (AI Search + Local Optimization)

This Knowledge Base must be referenced by the `genseo-auto-publish` orchestrator and the `genseo-seo-strategist` to ensure content targets both AI answer engines (ChatGPT, Perplexity, Google AI Overviews) AND local search intent for the US market.

---

## 1. Generative Engine Optimization (GEO) — AI Citability

**CRITICAL DIRECTIVE: The Human-AI Balance**
Never sacrifice human readability for rigid structure. Content must feel fluid, conversational, and natural to a human reader, while seamlessly embedding structured data (like tables or bolded answers) so that AI bots can easily parse the entities.

LLMs summarize text by looking for clear, non-ambiguous entity definitions.

- **Direct Answers (Inverted Pyramid)**: When asking a question (e.g., "What is the best creatine?"), physically type the answer immediately below it in bold within 40 words.
- **Entity Identification**: Name the brand entity "Wellness Nest" clearly and consistently next to verifiable facts (what it sells, ingredients/specs, shipping and return policy). No self-awarded superlatives ("best", "leading", "#1", "most trusted") unless a cited, verifiable source supports them (see §6.1 rule 4).
- **Data Densification**: Use markdown tables to compare products. AI models heavily favor structured tables over long paragraphs when compiling comparisons.
- **Self-Contained Sections**: Each H2 section must be independently comprehensible without reading previous sections. AI systems may extract and quote a single section out of context. Avoid phrases like "As mentioned above..." or "Building on the previous section..."

## 2. Answer Engine Optimization (AEO) — Featured Snippets & AI Overviews

- **Answer-First Introduction (MANDATORY)**: The first 40–60 words of EVERY article MUST contain a clear, complete, direct answer to the primary question. No throat-clearing, no build-up — answer first, then expand. This "answer block" is the #1 signal for featured snippets and AI Overview selection.
- **FAQ Modeling**: Dedicate the bottom 20% of every article to a strict FAQ format (H3 Question -> paragraph answer). These often trigger "People Also Ask" or AI Overviews.
- **Question-Style Headings**: Use headings that mirror how real people ask questions ("What is the best creatine?", "How much protein do I need?", "Is pre workout safe for beginners?"). These directly match voice search and conversational AI queries.
- **Tone & Syntax**: Use authoritative, unbiased, deterministic phrasing instead of passive tones.
  - *Bad*: "You might want to consider trying Wellness Nest for your protein."
  - *Good*: "Wellness Nest's whey isolate lists [X] g protein per [Y] g scoop on its label." (deterministic AND verifiable; fill in from the real product page, never invent; see §6.1 rule 4)

## 3. AI Overview Triggers

- Define technical terms early in the article (e.g., "Creatine Monohydrate is a naturally occurring compound...").
- Bold the names of products and key ingredients to help LLMs parse distinct entities quickly.
- Use comparison tables with clear column headers — AI models extract these preferentially for "vs" and "best of" queries.

---

## 4. Local SEO / GEO Signals — US Market (MANDATORY)

**Every article targeting US MUST weave in local signals naturally.** This is non-negotiable for ranking in local packs, Google Maps, and "near me" queries.

### 4.1 Location Placement Rules
Mention "the US" or local references in ALL of these positions:
- **H1 / Title tag** (e.g., "Best Pre Workout in the US for Busy Professionals")
- **First paragraph** (within the answer block)
- **At least 2 H2 subheadings** where natural
- **Naturally throughout body text** — aim for 3-5 locality references beyond the title

### 4.2 Neighbourhood & Landmark References
Go beyond just "US." Include specific locality signals where they add value:
- **Delivery zones**: state only the coverage in the real shipping policy (nationwide US online store); never list invented regions, cities or neighbourhoods (see §6.5).
- **Pickup references**: DO NOT mention a physical store, pickup or same-day delivery unless Kevin has confirmed it is true. Default: "Order online; ships across the US" with the real shipping times from the store's shipping policy (see §6.5).
- **US lifestyle references**: "Whether you lift at a big-box gym or train in your garage..." (real, generic US context only — never invent named locations)
- **Local context**: only true, specific context (e.g. "In hot, humid summers in the US South, hydration needs rise..."), never blanket claims about the whole country.

### 4.3 Local FAQ Questions (MANDATORY — at least 1 per article)
Every article MUST include at least ONE locally-flavoured FAQ question, such as:
- "Where can I buy [product] in the US?"
- "How long does Wellness Nest take to ship to [US/UK/CA/AU]?" (answer from the real shipping policy only)
- "What's the best [supplement type] for US's climate?"
- "Is [product] third-party tested / what is in it?" (answer from the real label or certificate only)

### 4.4 NAP & Business Consistency
- Always refer to the store as **"Wellness Nest"** (not "Wellness Nest" or "Wellness Nestplements")
- Store URL: `https://wellnessnest.co`
- Reference shipping and authenticity guarantees as trust signals ONLY as stated in the published store policies (no invented promises)

### 4.5 Local Intent Phrases to Weave In
Use these phrases naturally where appropriate:
- "in the US", "for American women over 40"
- "buy online in the US", "order in the US"
- shipping / authenticity phrases ONLY as worded in the published store policies (no "local shipping" or "fast delivery" promises that the policy doesn't make)
- "US gym-goers", "US fitness community"

---

## 5. Dated Learnings (Search Engine Land digest review)
- **2026-10-08 — Answer the fan-out sub-questions** (SEL ~2026-09-30, Ahrefs data): Only ~38% of AI Overview citations rank in the top 10 and ~31% rank 11–100, because Google fans out related searches. Write focused, self-contained answers to follow-up questions (for example NMN + TMG timing, dose per serving, stacking, who it suits), even when the head keyword is out of reach.
  - **Correction 2026-10-08 (official Google docs):** cover fan-out sub-questions as sections INSIDE one pillar article. Do NOT create separate pages per fan-out/variant query; Google calls that scaled content abuse. See §6.1 rule 2.
- **2026-10-08 — Keep revenue pages fresh** (SEL early Oct 2026): AI-cited URLs average ~26% fresher than organic results. Refresh the top revenue posts monthly with a dated update that adds new data or answers.
- **2026-10-08 — Be the clear place to buy** (SEL 2026-09-30): AI shopping answers favor big retailers, most of all on named-product queries, and being cited is not the same as being recommended. Product content needs comparison and "where to buy" sections that name Wellness Nest as the official source. Calling Wellness Nest an independent US brand may help, since adding "independent" to a prompt more than doubled small-store picks.
- **2026-10-08 — Earned mentions drive AI citations** (SEL 2026-09-30, early Oct 2026): ~84% of AI citations come from earned media, and the number and depth of mentions matter more than sentiment. YouTube gave the biggest third-party lift (~2.8x). Pair owned pages with creator/YouTube content and genuine third-party coverage. On Reddit, only answer fresh threads (under ~20 days) helpfully and without promotion.
- **2026-10-08 — Measure AI visibility as a rate** (SEL early Oct 2026): Same-day AI Mode citations overlap only ~9%, and AI Overviews and AI Mode share only ~14% of citations. Track each platform separately, run each prompt several times, report the brand mention rate as a range over 2–4 weeks, and track share of voice, since many citations never name the brand.
- **2026-10-08 — Reviews back up AI answers** (SEL ~2026-10-05, SOCi): 81% of AI users check reviews or social before acting on an AI recommendation. Keep real reviews visible on product pages and reflect them in FAQs.

---

## 6. Official-source GEO rules (2026-10-08)

Source of truth: the official docs tracked daily by `scripts/geo_sources_watch.py`. Notes live in the vault at `90-sources/geo-official/` (google / openai / anthropic / xai baselines + daily digests). **If anything in §1–§5 conflicts with this section, §6 wins.** Each rule cites its source. Lines marked *Inference* are our reading, not the vendor's words.

### 6.1 Google AI Overviews / AI Mode
1. **GEO for Google = SEO.** AI features use the core ranking systems plus RAG and query fan-out. No special AI markup, files or chunking are needed. — https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
2. **Fan-out goes INSIDE pillar articles, not into separate pages.** Making separate content for each variation or fan-out query to manipulate rankings or AI responses is **scaled content abuse**. Answer the sub-questions as H2/H3 sections inside one strong page. Before creating a new article, check whether an existing article already covers the intent; if so, expand that one instead. — https://developers.google.com/search/docs/fundamentals/ai-optimization-guide, https://developers.google.com/search/docs/essentials/spam-policies
3. **Non-commodity content.** Every article needs something a summary of other pages can't give: first-hand testing notes, real product specs and label data, real customer questions, original comparison tables. A rewritten summary of the top results is not enough. — https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
4. **Fact-check ALL generated text, including the title, meta description, structured data and image alt text.** No claims we can't back up. No superlatives about Wellness Nest ("best", "leading", "#1", "most trusted") unless a cited, verifiable source supports them. — https://developers.google.com/search/docs/fundamentals/using-gen-ai-content
5. **No fake freshness.** Don't change dates, or add or remove content, just to look fresh. Only bump `dateModified` and the visible "Last updated" when the main content has substantially changed. — https://developers.google.com/search/docs/fundamentals/creating-helpful-content
6. **Dates must be visible AND consistent.** Show "Published" / "Last updated" on the page and use the same values in `datePublished` / `dateModified`. Emit only ONE Article/BlogPosting node per post. — https://developers.google.com/search/docs/appearance/publication-dates
7. **Real authors only.** The byline links to an author page; schema `author` has `@type` + `url` (or `sameAs`). Fabricated creator profiles (made-up names, AI headshots, false credentials) are deception. Never add credentials (e.g. "Dr.", "RD") that Kevin hasn't confirmed. — https://developers.google.com/search/docs/fundamentals/creating-helpful-content, https://developers.google.com/search/docs/appearance/structured-data/article
8. **Structured data must match visible content.** Never mark up reviews or ratings that aren't real and visible. — https://developers.google.com/search/docs/appearance/structured-data/sd-policies
9. **llms.txt does nothing for Google** ("will neither harm nor help"). Don't spend generation time on it for Google. — https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
10. **Key facts must be in TEXT**, with supporting images/video. AI features can surface images, so give every image a true, descriptive alt text. AI-generated product images sent to Merchant Center must carry IPTC `DigitalSourceType = TrainedAlgorithmicMedia`. — https://developers.google.com/search/docs/appearance/ai-features, https://developers.google.com/search/docs/fundamentals/using-gen-ai-content
11. **Eligibility needs Search Console.** The site must be included in "Search generative AI features" in Search Console. Measure with the Search Console Generative AI performance report (not third-party "AI rank" tools). — https://developers.google.com/search/docs/fundamentals/ai-optimization-guide, https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports
12. **Products:** Merchant Center feeds help products show in AI responses, because crawling may miss products. — https://developers.google.com/search/docs/specialty/ecommerce/share-your-product-data-with-google
13. **Inauthentic mentions don't work.** Don't plant fake forum or review mentions. — https://developers.google.com/search/docs/fundamentals/ai-optimization-guide

### 6.2 ChatGPT (OpenAI)
14. **OAI-SearchBot must stay allowed** for ChatGPT search visibility. GPTBot (training) and ChatGPT-User (user-initiated) are separate switches. Robots changes take about 24h. — https://developers.openai.com/api/docs/bots
15. ChatGPT search shows inline URL citations, and reasoning models `open_page` / `find_in_page`. *Inference:* put the citable facts (dose, price, ingredient amounts, who it's for) as plain text on the page that makes the claim, not only in images or widgets. — https://developers.openai.com/api/docs/guides/tools-web-search
16. Results are tailored by user location, and search can run from a cached copy. *Inference:* publish early (so pages get crawled before the question is asked) and state US/UK/CA/AU shipping facts truthfully in text. — https://developers.openai.com/api/docs/guides/agents-api/tools/web-search
17. *Inference* from OpenAI's example deep-research prompt (which prioritises peer-reviewed research and health organisations): health articles should link primary studies (PubMed/NIH) and regulators (FDA, NIH ODS, CDC, WHO) for each health claim. — https://developers.openai.com/api/docs/guides/deep-research

### 6.3 Claude (Anthropic)
18. ClaudeBot = training, Claude-SearchBot = search result quality, Claude-User = user-initiated fetches. Blocking Claude-SearchBot can reduce visibility and accuracy in Claude's search answers. Keep Claude-SearchBot and Claude-User allowed. — https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler

### 6.4 Grok (xAI)
19. Grok's web search returns citations to the pages it used, and its agent can browse pages; X Search is a separate tool over X posts. *Inference:* real, useful posts from the Wellness Nest X account that link to articles add a second path into Grok answers. xAI documents no crawler user agent, so there's nothing to allow or block in robots.txt specifically for Grok. — https://docs.x.ai/developers/tools/web-search, https://docs.x.ai/developers/tools/x-search, https://docs.x.ai/developers/tools/citations

### 6.5 Never do (any engine)
- Never claim a physical store, pickup, same-day delivery, local warehouses or named delivery zones unless Kevin has confirmed them as true. Wellness Nest is treated as a nationwide online (DTC) store.
- Never invent statistics, studies, awards, reviews, ratings or credentials.
- Never create near-duplicate "variant" pages (city/state/audience swaps of the same article).
- Never change robots.txt, theme or store settings from GenSeo. Propose changes to Kevin instead.

Lint: `python3 scripts/geo_official_lint.py <article.html|md>` prints WARN-only findings for these rules. It never blocks publishing and does not replace `validate_article.py`.

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

## 6. Official-source GEO rules (2026-10-08, gap-fill 2026-10-09)

Source of truth: the official docs tracked daily by `scripts/geo_sources_watch.py`. Notes live in the vault at `~/PATI/LLM-Wiki/90-sources/geo-official/` (google / openai / anthropic / xai baselines + daily digests). **If anything in §1–§5 conflicts with this section, §6 wins.** Each rule cites its source. Lines marked *Inference* are our reading, not the vendor's words.

Rules 1–19 were absorbed on 2026-10-08. **Rules 20–39, and the dated bullets in §6.5 and §6.9, were added on 2026-10-09** by diffing those baselines against this file. The newest digest on this Mac was `digests/geo-official-digest-2026-10-08.md` (first-run baseline, no page-level diffs). There was no `geo-official-digest-2026-10-09.md`.

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
- **2026-10-09** Never claim ChatGPT search uses Bing's index. OpenAI's crawler docs do not say that (§6.6 rule 27).
- **2026-10-09** Never invent a crawler token or UA version the vendor page does not list (no GrokBot, no ClaudeBot version string). See §6.6 rules 27–29.
- **2026-10-09** Never claim `llms.txt` is required, or that it helps rankings on Google, ChatGPT, Claude, or Grok (§6.8 rule 34).
- **2026-10-09** Never claim IndexNow, Google Search Console, or Bing Webmaster Tools is live, verified, or receiving pings for wellnessnest.co (§6.9).
- **2026-10-09** Never put a CAPTCHA, age gate, or forced interstitial on an article or landing. Anthropic's bots will not bypass CAPTCHAs (§6.6 rule 28).
- **2026-10-09** Never add a script that traps the Back button (§6.6 rule 26).
- **2026-10-09** Product identity is not a GEO choice. AgeAura links only to https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex (NMN + TMG). FloraFresh copy follows the Supplement Facts label: Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies. Guards: `scripts/brand_rules.py`, `docs/AGEAURA_PRODUCT_GUARD.md`, `docs/FLORAFRESH_FORMULA_GUARD.md`.
- **2026-10-10** Shilajit Shockwave pack-label copy follows `product_refs/shilajit-shockwave.label.json` only (identity lines; no milligram, serving count, or volume token). Guard: `scripts/shockwave_rules.py`, `docs/SHOCKWAVE_LABEL_GUARD.md`.
- **2026-10-10** Pure Shilajit Gold Resin pack-label copy follows `product_refs/pure-shilajit-gold-resin.label.json` only (`required` + `optional`: identity lines, `75% Fulvic`, and `1.06 oz (30g) - 75 servings`). No milligram token was read. Guard: `scripts/gold_resin_rules.py`, `docs/GOLD_RESIN_LABEL_GUARD.md`.
- **2026-10-10** ShilaSource Himalayan Shilajit Resin pack-label copy follows `product_refs/shilasource-himalayan-shilajit-resin.label.json` only (`required` + `optional` from the 2026-10-08 OCR read: identity lines, `70% Fulvic Acid*`, `1.06oz (30g)`, and the split `75` / `SERVINGS` badge). No milligram token and no Supplement Facts panel were read. Guard: `scripts/shilasource_resin_rules.py`, `docs/SHILASOURCE_RESIN_LABEL_GUARD.md`.

### 6.6 Crawlers, user agents, and robots.txt (2026-10-09)

Numbering continues from rule 19. GenSeo does not edit robots.txt. Propose a full group to Kevin (§6.9).

20. **2026-10-09 — Indexed and snippet-eligible is the technical bar for Google AI features.** Google says there are no extra technical requirements beyond normal Search. `noindex`, `nosnippet`, `data-nosnippet`, and `max-snippet` limit what can be shown. — https://developers.google.com/search/docs/appearance/ai-features, https://developers.google.com/search/blog/2025/05/succeeding-in-ai-search
21. **2026-10-09 — Google-Extended is not a Search switch.** It only controls Gemini training and grounding in Gemini Apps / Vertex AI. It does not change inclusion in Google Search and is not a ranking signal. *Inference:* leave Google-Extended allowed. Do not write that blocking Google-Extended removes AI Overviews or drops the site out of Google Search. — https://developers.google.com/search/docs/appearance/ai-features, https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers
22. **2026-10-09 — One robots.txt group per crawler.** The most specific user-agent group wins, and it is not combined with `User-agent: *`. *Inference:* if a named group is ever added (`OAI-SearchBot`, `GPTBot`, `ClaudeBot`, `Claude-SearchBot`, `Claude-User`), repeat the cart and checkout disallows inside that group. — https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec
23. **2026-10-09 — The CDN and host must allow the crawl, not only robots.txt.** Important content stays in text form. Keep Merchant Center and Business Profile facts aligned with the visible page. *Inference:* do not create a Business Profile that implies a physical store (§6.5). — https://developers.google.com/search/docs/appearance/ai-features
24. **2026-10-09 — Do not chunk pages or chase an ideal length for AI.** Chunking is not required. There is no ideal page length. Do not make a page for every long-tail variant (same abuse class as rule 2). — https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
25. **2026-10-09 — Sitemap `lastmod` only when it is true.** Google uses it only if it stays consistently and verifiably accurate. Update it only when main content, structured data, or links actually change. Same bar as rule 5. — https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
26. **2026-10-09 — Back-button hijacking can demote the site.** Google has treated it as spam since 2026-06-15, including traps that come from a third-party script. Do not add an `onpopstate` handler or any other script that traps the Back button. Auditing live apps is a Kevin GO (§6.9), not a draft edit. — https://developers.google.com/search/blog/2026/04/back-button-hijacking
27. **2026-10-09 — OpenAI: four agents, four jobs.** Allow **OAI-SearchBot**, including the IP ranges at https://openai.com/searchbot.json. If that bot is blocked, the site "will not be shown in ChatGPT search answers", though it can still appear as a navigational link. **GPTBot** is training only; if both are allowed, OpenAI may reuse one crawl. **ChatGPT-User** is a user-initiated fetch; robots.txt may not apply, and it does not decide search inclusion. Manage the search opt-out only through OAI-SearchBot. **OAI-AdsBot** visits submitted ChatGPT ad landing pages only. UA tokens: `OAI-SearchBot/1.x`, `GPTBot/1.x`, `ChatGPT-User/1.0`, `OAI-AdsBot/1.0`. A `robots.txt` marker in the UA means that hit is fetching robots.txt. Robots changes take about 24 hours. These pages do not say ChatGPT search uses Bing's index. Do not state that as fact. — https://developers.openai.com/api/docs/bots
28. **2026-10-09 — Claude: robots.txt is the only reliable control.** ClaudeBot (training), Claude-SearchBot (search index), and Claude-User (user fetch) all follow robots.txt. IP blocking "may not work correctly" because it stops them reading robots.txt. Set rules per subdomain. Crawl-delay is honored; do not set a large crawl-delay on a small blog. Anthropic's bots will not bypass CAPTCHAs. *Inference:* no bot challenge, age gate, or forced popup on article or product pages. Anthropic publishes no UA version strings. Do not invent `ClaudeBot/1.0`, `Claude-SearchBot/1.0`, or `Claude-User/1.0`. — https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
29. **2026-10-09 — xAI publishes no crawler token.** No user agent, IP list, or robots.txt token is documented on the tools pages checked 2026-10-08. Do not add GrokBot, xAI-Bot, or any guessed token. — https://docs.x.ai/developers/tools/web-search

### 6.7 Citation patterns (2026-10-09)

30. **2026-10-09 — The cited URL has to be the page that holds the fact.** ChatGPT search returns inline clickable citations (`url_citation` with URL and title). Reasoning models can open the page and find inside it. Put dose, price, ingredient amounts, and who it suits in plain text on that page, not only in an image or a widget. — https://developers.openai.com/api/docs/guides/tools-web-search
31. **2026-10-09 — Grok: being encountered is not the same as being cited.** `citations` lists every URL the agent saw, including ones it judged not relevant enough. Inline citations are inserted only where it uses a source, they are not guaranteed, and a repeat source keeps the same number. *Inference:* one self-contained sentence per key fact (dose, price, ingredient amount, study result, shipping countries), next to a question-style heading, in server-rendered HTML. Grok's logged steps include `browse_page`, `open_page`, `open_page_with_find`, and `web_search_with_snippets`. When image search is on, use a descriptive file name and alt text, not `image.png` or `IMG_1234.jpg`. — https://docs.x.ai/developers/tools/citations, https://docs.x.ai/developers/tools/web-search, https://docs.x.ai/developers/tools/tool-usage-details
32. **2026-10-09 — Claude publishes no citation-ranking formula.** Visibility depends on allowing Claude-SearchBot and Claude-User (rule 18). Do not invent a ranking recipe. — https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
33. **2026-10-09 — Google's AI surfaces do not share one link set.** AI Overviews and AI Mode may use different models, so the links they show will vary, and AI Overviews often do not trigger. No third-party tool has access to Google's ranking or AI systems. Measure in the Search Console Generative AI performance report (rule 11), once Kevin has confirmed the property. Do not mark that report as already wired up (§6.9). — https://developers.google.com/search/docs/appearance/ai-features, https://developers.google.com/search/docs/fundamentals/ai-optimization-guide

### 6.8 Structured data and llms.txt (2026-10-09)

34. **2026-10-09 — `llms.txt` is not a Google ranking file.** Google Search ignores it ("will neither harm nor help"). This extends rule 9. The OpenAI, Anthropic, and xAI baselines do not say an `llms.txt` file is required for citations. Do not spend generation time writing one, and do not claim it improves rankings or is required for AI Overviews, ChatGPT, Claude, or Grok. Leave Shopify's default file alone. — https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
35. **2026-10-09 — Markup has to match the visible page, including reviews and dates.** Do not mark up content that is not visible, and do not mark up misleading content such as a fake review. If any review is marked up, mark up every visible review. Visible "Published" / "Last updated" and `datePublished` / `dateModified` use the same dates. One Article or BlogPosting node per post (rule 6). The author node needs `@type` plus `url` or `sameAs` for every visible author (rule 7). — https://developers.google.com/search/docs/appearance/structured-data/sd-policies, https://developers.google.com/search/docs/appearance/publication-dates, https://developers.google.com/search/docs/appearance/structured-data/article
36. **2026-10-09 — A sale window is not the everyday price.** `priceValidUntil` and `validThrough` describe an active sale price window. Shipping and return policy can sit on Organization markup or in Search Console "Shipping and returns"; Search Console wins over markup. Do not invent either. Changing Merchant Center or Search Console is a Kevin GO (§6.9). — https://developers.google.com/search/docs/appearance/structured-data/merchant-listing, https://developers.google.com/search/docs/appearance/structured-data/organization, https://developers.google.com/search/blog/2025/11/more-ways-to-share-shipping
37. **2026-10-09 — No special AI schema.** Structured data is not required for AI features. Keep it for rich-result eligibility. Do not add an "AI schema" type. — https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
38. **2026-10-09 — Agentic buyers read the rendered page.** Google says browser agents read screenshots, the DOM, and the accessibility tree, and that protocols such as UCP are emerging. *Inference:* keep the product name, price, ingredients, and shipping in text. The store already exposes `/.well-known/ucp`. Do not invent a second commerce-protocol file. — https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
39. **2026-10-09 — Say how automation was used, and fact-check the chrome.** Google says to consider disclosing how automation was used, and to fact-check titles, meta descriptions, structured data, and image alt text (rule 4). AI-generated product images sent to Merchant Center must use IPTC `DigitalSourceType` `TrainedAlgorithmicMedia` (rule 10). Feeding Merchant Center is a Kevin GO. — https://developers.google.com/search/docs/fundamentals/using-gen-ai-content

### 6.9 What not to change without a Kevin GO (2026-10-09)

These are operating constraints, not vendor ranking factors. Propose them in writing and wait.

- **2026-10-09 — robots.txt.** Named-bot groups, Google-Extended, crawl-delay, IP blocks, and Allow/Disallow edits. A named group is not merged with `User-agent: *` (rule 22). The proposal has to repeat the cart and checkout disallows.
- **2026-10-09 — Theme and storefront.** Do not edit theme `183190880571`, theme Article JSON-LD, app embeds, or popups. Schema cleanup stays a proposal until Kevin says to apply it.
- **2026-10-09 — Merchant Center, Business Profile, and Search Console settings.** Feeds, IPTC image metadata, shipping and returns, and the "Search generative AI features" inclusion flag. Do not mark any of these done inside a draft.
- **2026-10-09 — IndexNow, Google Search Console, and Bing Webmaster Tools are not live** for wellnessnest.co until Kevin hosts the keys. PR #1 (`cursor/indexnow-llms-txt-44d2`, https://github.com/tuanquang269/genseo/pull/1 ) was still an open draft on 2026-10-09. Drafts must not say the store is verified there or that those systems are receiving pings.
- **2026-10-09 — Publishing.** Do not publish, unpublish, or add redirects from a guidelines sync.

Lint: `python3 scripts/geo_official_lint.py <article.html|md>` prints WARN-only findings for the rules it can see in a draft (store and pickup claims, superlatives, fake freshness, credentials, image alt, stale title year, duplicate Article nodes, missing primary-source link, plus the 2026-10-09 checks: `llms-txt-ranking`, `chatgpt-bing-index`, `google-extended-blocks-search`, `invented-crawler-ua`, `indexnow-gsc-bing-live`, `back-button-hijack`, `bot-challenge`, `chunk-for-ai`, `schema-review-not-visible`, `date-mismatch`, `sale-window-unmarked`, `generic-image-filename`). It always exits 0. It does not replace `validate_article.py`, and it does not publish.

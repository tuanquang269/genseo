# SEO & E-E-A-T Guidelines for Wellness Nest

This Knowledge Base must be referenced by the `genseo-seo-strategist` when formulating Content Briefs.

## 1. Experience, Expertise, Authoritativeness, and Trustworthiness (E-E-A-T)
- **Author Identity**: All factual claims about supplements, side effects, and nutrition must be attributed to the "Wellness Nest Research Team" or specific certified trainers.
- **Scientific Backing**: When discussing ingredients like Creatine, Whey, or Pre-workouts, reference their mechanism of action (e.g., ATP cycle for creatine).
- **First-hand Experience**: Do not write "our team tested", "I tried", a customer quote, a star rating, or a byline that says the author uses the product. A first-hand block is allowed only when `scripts/experience_block.py` prints one from `data/experience_quotes.json` (`usage_allowed: true`; `example: true` never renders). If it prints nothing, leave the block out. The optional "How we checked this" line is that script's `--with-method` output, and only when the article gate already checks that product's label. See `docs/first-hand-experience-block.md`.

## 2. On-Page SEO Formatting Rules
- **H1 Tag**: Every article MUST have precisely one `<h1>` containing the primary focus keyword.
- **H2 & H3 Structure**: Use `<h2>` for macro themes (e.g., "What is Creatine"). Use `<h3>` for specific product reviews (e.g., "Mutant CreaKong CX8 Review").
- **Internal Linking**:
  - Exact match anchor texts should be used precisely but sparingly.
  - Links MUST go to validated Shopify Product Handles (not search pages).
  - Use long-tail semantic anchors (e.g., "the most effective creatine in the US").
- **Schema & Structured Data**: Ensure the Content Brief dictates if Product Schema or FAQ Schema is required.

## 3. Commercial Intent & Conversion
- SEO at Wellness Nest is useless without sales. Every review or listicle must clearly prompt the user on *where* and *why* to buy from the store.
- Use strong calls to action (CTAs).
- Highlight "authentic imports", "fast local shipping", and "US's top selection".

## 4. Dated Learnings (Search Engine Land digest review)
- **2026-10-08 — Human fact-check gate** (SEL 2026-10-01/02, 2026-10-07): Google now calls manual review of all AI-generated content "critical", and mass AI text without curation rates as "little to no effort". Every GenSeo article gets a logged human check of claims, dosages and study citations before publish. YMYL supplement claims must match expert consensus. The reviewer checks substance, not just readability.
- **2026-10-08 — No deceptive authorship** (SEL 2026-10-06): Google names AI-generated headshots, made-up author names and false credentials as untrustworthy, low-quality signals. Never invent a person or credential. Any named author or reviewer must be real and verifiable, and the "Wellness Nest Research Team" byline must never be dressed up as a fake individual expert.
- **2026-10-08 — Main content carries the page** (SEL 2026-10-02, 2026-09-30): Raters judge main content on effort, originality, skill and accuracy, and most AI citations go to ordinary thorough pages, not listicles. Put specs, safety notes, ingredient explainers, real reviews and FAQs inside product and category pages, and add first-hand detail an AI draft can't supply.
- **2026-10-08 — Internal links follow business priority** (SEL 2026-10-02): Send contextual links from guides and parent collections to the products and collections that matter now (margin, inventory, demand). Fix the biggest mismatches with a few strong links first, then watch impressions and sales.
- **2026-10-08 — Brand-validation pages** (SEL 2026-10-07): Shoppers who find a product on social mostly search it on Google next. Branded queries like "AgeAura NMN + TMG review", "is AgeAura legit" and "AgeAura ingredients" should land on a strong Wellness Nest page (ingredient breakdown, real reviews, FAQ) that links to the NMN + TMG Complex product page. AgeAura content covers the NMN + TMG Complex only.

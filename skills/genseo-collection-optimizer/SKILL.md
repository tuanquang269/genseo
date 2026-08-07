---
name: genseo-collection-optimizer
description: >
  Use when the user asks to "optimize collection", "cải thiện SEO collection", or gives you a generic 
  Shopify collection URL to improve its ranking. Do NOT use for individual blog articles.
metadata: {"clawdbot":{"emoji":"🛍️","requires":{"commands":["python3"]},"os":["linux","darwin","win32"]}}
---

# GenSeo Collection Optimizer

This agent acts as a specialized AI architect for Shopify Collection Pages. It combines "Dual-Zone Content" best practices with live API data from Google Search Console (GSC) to extract under-utilized high-intent keywords and deploy a fully optimized page — including SEO metadata, structured content, FAQ schema, ItemList schema with Product data, and CollectionPage schema — directly to Shopify via the REST API.

## When to Use
- The user asks you to improve the ranking of a specific Shopify collection page.
- You need to generate an actionable SEO Brief for a collection page that is missing metadata or unique content blocks.

## Design Principles (SEO + AEO + GEO + Mobile-First)

1. **SEO:** Title tag under 60 chars, meta description under 155 chars, primary keyword front-loaded in H1, unique content (50–150 words above grid + 300–500 words below grid), internal hub-spoke links, comparison tables for multi-type categories.
2. **AEO (Answer Engine Optimization):** FAQPage schema with 3–5 Q&As derived from real search queries. Buying guide opens with a "definition-first" paragraph — a concise, cite-ready answer (40–60 words) that AI engines can extract verbatim. Comparison tables for AI-extractable structured data. Problem-solution framing ("If you need X → choose Y because Z").
3. **GEO (Generative Engine Optimization):** Nested `@graph` schema architecture — `CollectionPage` (with `dateModified`) → `ItemList` → `Product` data + `BreadcrumbList` + `FAQPage` (all JSON-LD). E-E-A-T Curator's Note with photo and credentials link. "Last reviewed" freshness signal. {{MARKET}}-specific localisation for hyper-local authority signals.
4. **Mobile-First (MANDATORY):** Your Brand is a mobile-first store. All collection HTML must render cleanly at 375px width. Two components require specific mobile handling:
   - **Curator's Note** must use `class="usup-curator"` on the outer flex div and `class="usup-curator-body"` on the inner text div, so the media query can stack them vertically on small screens.
   - **Related Guides** list items must use `class="usup-guide-item"` on each `<li>`, `class="usup-guide-arrow"` on the `→` span, and `class="usup-guide-link"` on each `<a>`, so links never centre-wrap with a detached arrow on mobile.
   - A **responsive `<style>` block** (see Step 6.6) MUST be prepended to every HTML file.

## The Process

### 1. Ingest Search Console Data
- Use the `run_command` tool to execute the GSC fetcher script:
  `python3 ~/genseo/scripts/gsc_fetcher.py fetch_url_data "https://yourdomain.com" "[COLLECTION_URL]"`
- Analyze the output to identify keywords with high impressions but low clicks, or highly local terms with good CTR (e.g., strong CTR for queries with "{{MARKET}}").

### 2. Web Content & Technical Audit
- Fetch the live HTML of the `[COLLECTION_URL]` to check its current state:
  - Current `<title>` tag (often outdated with wrong year)
  - Current `<h1>` tag text — **CRITICAL:** Check if the Shopify theme already outputs an `<h1>` for the collection title. Record this for Step 6 heading hierarchy decision.
  - Whether it already has "Above the Grid" and "Below the Grid" text blocks
  - Any existing schema markup (FAQPage, CollectionPage, BreadcrumbList, ItemList)
  - Any existing internal links to blog articles
  - **Canonical tag check:** Verify the page has a canonical tag pointing to the clean collection URL (not a filtered/sorted variant like `?sort_by=price-ascending`)
  - **Image alt text audit:** Spot-check whether product images in the collection grid have descriptive, keyword-informed alt text. Flag any missing or generic alt text (e.g., "product image") in the SEO brief.
- Use a python script with `urllib` and `BeautifulSoup` to parse the structure.

### 3. Keyword Cluster Analysis
- Group the GSC keywords into **intent clusters**:
  - **Core Category** (e.g., "fat burner", "protein bar")
  - **Local Intent** (e.g., "best fat burner {{market}}", "protein bar {{market}}")
  - **Comparison / Informational** (e.g., "thermogenic vs non-stimulant", "protein bar vs meal replacement")
  - **Year-Tagged** (e.g., "best fat burner 2026")
  - **Gender / Demographic** (e.g., "best fat burner for women")
  - **Long-Tail / Niche** (e.g., "appetite suppressant {{market}}", "cheap protein bars")
- Present clusters in a table in the SEO brief. Ensure all high-value clusters are addressed in the content.

### 4. Synthesis & Strategy
- Ensure the recommended strategy adheres to the **"Dual-Zone Content"** methodology:
  - **Zone 1 (Above Grid):** 50–150 words. Concise intro hook that establishes what the collection is, who it's for, and includes the primary keyword naturally.
  - **Zone 2 (Below Grid):** 300–500 words buying guide + FAQ + Curator's Note + Related Guides + Comparison Table.
- **Definition-First Opening (AEO mandate):** The first paragraph of the buying guide MUST be a concise (40–60 words), factual, "citation-ready" definition that AI engines can extract verbatim. Example format: "[Category] supplements are [definition]. The most effective [category] in {{MARKET}} in [year] use [key ingredients] to [benefit]. Here's how they work and how to choose the right one."
- **Comparison Table (AEO/GEO mandate):** For categories with multiple sub-types (e.g., thermogenic vs non-stimulant, whey isolate vs concentrate), include an HTML comparison table. Tables are highly extractable by AI engines and rank well in featured snippets. Use `<table>` with clear `<thead>` and `<tbody>`.
- **Internal Links (Hub-Spoke mandate) — REQUIRED:** Include a "📚 Related Guides" section with 3–5 links to published blog articles on the store that relate to this collection. This section is **mandatory**, not optional.
  - First, check the `published_drafts/` directory for relevant articles.
  - If insufficient, query the Shopify API: `python3 -c "import urllib.request,json; req=urllib.request.Request('https://your-store.myshopify.com/admin/api/2026-04/articles.json?limit=50&fields=id,title,handle,blog_id', headers={'X-Shopify-Access-Token': __import__('genseo_config').TOKEN}); print(json.loads(urllib.request.urlopen(req).read()))"` to find related articles.
  - If no related articles exist, flag this in the brief as a content gap to address.
- **Freshness Signal — REQUIRED:** Include a visible "Last reviewed: [Month Year]" line at the bottom of the buying guide section. This signals recency to both users and AI crawlers.
- Inject the most valuable keywords found from GSC. Prevent Keyword Cannibalization by adding Year modifiers or location intent.

### 5. Generate the SEO Brief
- Create an artifact named `[COLLECTION_NAME]_seo_brief.md`.
- The brief MUST contain:
  - **GSC Keyword Cluster Table** with impressions, clicks, positions
  - **Metadata Specs:** Exact `<title>` and `<meta name="description">` to use
  - **H1 Specs:** Exact `<h1>` text (or H2 if theme already provides H1)
  - **Intro Copy (Above Grid):** Exact text for the short intro hook (50–150 words)
  - **Buying Guide Copy (Below Grid):** Detailed text block (definition-first format, 300–500 words)
  - **Comparison Table:** HTML table comparing product sub-types
  - **Related Guides:** 3–5 internal links to published blog articles
  - **Technical Audit Flags:** Any issues found (canonical tags, image alt text, duplicate H1s)

### 6. Generate the HTML File
- Create the full HTML file at `~/genseo/[COLLECTION_HANDLE]-collection.html`.
- The HTML MUST follow the established Dual-Zone template pattern:

#### Heading Hierarchy Decision
- **If the Shopify theme outputs its own `<h1>` for the collection title** (most themes do): Use `<h2>` as the top heading in body_html to avoid duplicate H1s. Sub-sections use `<h3>`.
- **If the theme does NOT output an `<h1>`**: Use `<h1>` as the top heading. Sub-sections use `<h2>`.
- **NEVER use `<h3>` as the primary heading** — this was a legacy pattern that must be corrected.

#### Template Structure
0. **Mobile `<style>` block** — **PREPENDED FIRST** before any other HTML (see Step 6.6 below)
1. **Primary heading** (H2 or H1 per above) — styled, centered, with the optimized heading text
2. **Intro paragraph** (Zone 1, 50–150 words) with internal link to homepage
3. **`<!-- split -->`** comment to separate Zone 1 from Zone 2
4. **Buying guide** with styled info boxes (background #fafafa, border-radius 8px, yellow ⯈ bullets)
5. **Comparison table** for multi-type categories (styled HTML `<table>`)
6. **Curator's Note** block — must include `class="usup-curator"` on outer div and `class="usup-curator-body"` on inner text div (see mobile pattern below)
7. **Related Guides** section — **MANDATORY** — must include `class="usup-guide-item"` on each `<li>`, `class="usup-guide-arrow"` on the `→` span, `class="usup-guide-link"` on each `<a>` (see mobile pattern below)
8. **Freshness line** — `<p style="font-size: 12px; color: #999; text-align: right; margin-top: 20px;">Last reviewed: [Month Year]</p>`
9. **JSON-LD Schema** block using the `@graph` structure (see template below)

### 6.5 Auto-Generate ItemList Schema from Shopify API
- Fetch the products in the collection from the Shopify API to populate the `ItemList` schema with real product data:
  ```
  python3 -c "
  import urllib.request, json
  import sys; sys.path.insert(0, 'scripts')
  from genseo_config import SHOP as shop, TOKEN as token
  # First get collection ID
  req=urllib.request.Request(f'https://{shop}/admin/api/2026-04/smart_collections.json?handle=[HANDLE]', headers={'X-Shopify-Access-Token':token})
  data=json.loads(urllib.request.urlopen(req).read())
  cid=data['smart_collections'][0]['id'] if data.get('smart_collections') else None
  if not cid:
      req=urllib.request.Request(f'https://{shop}/admin/api/2026-04/custom_collections.json?handle=[HANDLE]', headers={'X-Shopify-Access-Token':token})
      data=json.loads(urllib.request.urlopen(req).read())
      cid=data['custom_collections'][0]['id']
  # Then get products via collects
  req=urllib.request.Request(f'https://{shop}/admin/api/2026-04/products.json?collection_id={cid}&limit=20&fields=id,title,handle,vendor,variants,images', headers={'X-Shopify-Access-Token':token})
  products=json.loads(urllib.request.urlopen(req).read())['products']
  for i,p in enumerate(products):
      v=p['variants'][0] if p.get('variants') else {}
      print(json.dumps({'position':i+1,'name':p['title'],'url':f\"https://yourdomain.com/products/{p['handle']}\",'brand':p.get('vendor',''),'price':v.get('price','0'),'available':v.get('available',True)}))
  "
  ```
- Use this data to populate the `itemListElement` array in the schema template below.

### 6.6 Mobile-First Style Block + Component Patterns

Prepend this `<style>` block to **every** collection HTML file, before all other content:

```html
<style>
/* ── Mobile-first responsive fixes ─────────────────────────────── */
@media (max-width: 640px) {

  /* Curator's Note: stack photo above text on small screens */
  .usup-curator {
    flex-direction: column !important;
    align-items: center !important;
    gap: 16px !important;
  }
  .usup-curator-body {
    width: 100% !important;
    text-align: left !important;
  }
  .usup-curator-body p {
    text-align: left !important;
  }

  /* Related Guides: flex row so arrow never separates from text */
  .usup-guide-item {
    display: flex !important;
    align-items: flex-start !important;
    gap: 8px !important;
    padding-left: 0 !important;
    position: static !important;
  }
  .usup-guide-arrow {
    position: static !important;
    flex-shrink: 0 !important;
    line-height: 1.6 !important;
  }
  .usup-guide-link {
    text-align: left !important;
    display: block !important;
  }
}
</style>
```

**Curator's Note HTML pattern** (copy exactly — class names are required):
```html
<div class="usup-curator" style="background-color: #ffffff; border-left: 5px solid #fbdc00; border-radius: 6px; padding: 24px; margin: 30px 0; display: flex; align-items: flex-start; gap: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); border-right: 1px solid #eaeaea; border-top: 1px solid #eaeaea; border-bottom: 1px solid #eaeaea; text-align: left;">
  <img src="https://cdn.shopify.com/s/files/1/0284/6094/1452/files/20200902_200930.jpg?v=1776287716"
      alt="Author One - Sports Nutritionist & Supplement Expert"
      style="width: 80px; height: 80px; min-width: 80px; min-height: 80px; flex-shrink: 0; border-radius: 50%; object-fit: cover; object-position: top; border: 3px solid #ffffff; box-shadow: 0 3px 8px rgba(0,0,0,0.12);">
  <div class="usup-curator-body" style="flex-grow: 1; min-width: 0;">
    <h4 style="margin: 0 0 6px 0; font-size: 16px; font-weight: 700; color: #111; text-transform: uppercase; letter-spacing: 0.5px;">
      Curator's Note <span style="color: #666; font-weight: 400; text-transform: none; letter-spacing: 0px; font-size: 14px;">by Author One</span>
    </h4>
    <p style="margin: 0; font-size: 15px; color: #333; line-height: 1.6; font-style: italic;">
      "[CURATOR QUOTE]"
    </p>
    <a href="/pages/author-one" style="font-size: 11px; font-weight: 800; text-decoration: none; color: #111; display: inline-block; margin-top: 12px; border-bottom: 2px solid #fbdc00; padding-bottom: 2px; text-transform: uppercase;">
      View Credentials &amp; Review Standards
    </a>
  </div>
</div>
```

**Related Guides HTML pattern** (copy exactly — class names are required):
```html
<div style="margin: 30px 0; padding: 24px; background-color: #fafafa; border-radius: 8px; border: 1px solid #eaeaea;">
  <h3 style="margin: 0 0 16px 0; font-size: 17px; color: #111; text-align: left;"><strong>📚 Related Guides</strong></h3>
  <ul style="margin: 0; padding: 0; list-style: none;">
    <li class="usup-guide-item" style="margin-bottom: 10px; display: flex; align-items: flex-start; gap: 8px; text-align: left;">
      <span class="usup-guide-arrow" style="color: #fbdc00; font-weight: 900; flex-shrink: 0; line-height: 1.5;">→</span>
      <a class="usup-guide-link" href="/blogs/articles/[HANDLE]" style="color: #111; text-decoration: underline; font-size: 14px; text-align: left;">[Article Title]</a>
    </li>
    <!-- repeat for each guide link; last li uses margin-bottom: 0 -->
  </ul>
</div>
```

> **Bulk patching tool:** If you need to apply mobile fixes to existing collection HTML files that were generated before this update, run:
> `python3 ~/genseo/scripts/patch_mobile.py`
> This script is idempotent — safe to run multiple times.

#### Schema Template (append to HTML file):
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "CollectionPage",
      "@id": "[COLLECTION_URL]#webpage",
      "name": "[Collection Heading Text]",
      "url": "[COLLECTION_URL]",
      "description": "[Meta description text]",
      "dateModified": "[YYYY-MM-DD]",
      "isPartOf": {
        "@type": "WebSite",
        "@id": "https://yourdomain.com/#website",
        "name": "Your Brand",
        "url": "https://yourdomain.com"
      },
      "breadcrumb": {
        "@type": "BreadcrumbList",
        "itemListElement": [
          { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://yourdomain.com" },
          { "@type": "ListItem", "position": 2, "name": "[Collection Name]", "item": "[COLLECTION_URL]" }
        ]
      },
      "mainEntity": {
        "@type": "ItemList",
        "numberOfItems": "[TOTAL_PRODUCTS]",
        "itemListElement": [
          {
            "@type": "ListItem",
            "position": 1,
            "item": {
              "@type": "Product",
              "name": "[Product Name]",
              "url": "[Product URL]",
              "brand": { "@type": "Brand", "name": "[Brand]" },
              "offers": {
                "@type": "Offer",
                "price": "[Price]",
                "priceCurrency": "{{CURRENCY}}",
                "availability": "https://schema.org/InStock"
              }
            }
          }
        ]
      }
    },
    {
      "@type": "FAQPage",
      "@id": "[COLLECTION_URL]#faq",
      "mainEntity": [
        {
          "@type": "Question",
          "name": "...",
          "acceptedAnswer": { "@type": "Answer", "text": "..." }
        }
      ]
    }
  ]
}
</script>
```

### 7. Deploy Body HTML to Shopify
- Run the push script to deploy the collection body content:
  ```
  python3 ~/genseo/scripts/push_collection.py [HANDLE] [HTML_FILE] --title "[SEO_TITLE]" --meta-description "[META_DESCRIPTION]"
  ```
- This single command updates:
  - `body_html` (the collection description with Dual-Zone content)
  - SEO `title_tag` metafield (the browser tab / SERP title)
  - SEO `description_tag` metafield (the SERP meta description)

### 8. Verify Deployment
- After deployment, fetch the live page again to confirm:
  - The new `<title>` tag is now showing (may take 1-2 minutes for CDN propagation)
  - The body content renders correctly
  - **No duplicate H1 tags** — verify only one `<h1>` exists on the page (theme H1 + body H2, not two H1s)
  - The schema markup validates — link: [Google Rich Results Test](https://search.google.com/test/rich-results)
  - The `ItemList` schema correctly lists products with prices and URLs
  - The "Related Guides" section is present with working links
  - The "Last reviewed" freshness line is visible
- Report the final status to the user.

### Deployment Checklist (MUST pass before reporting success)

**SEO / Content**
- [ ] Title tag < 60 chars, keyword front-loaded
- [ ] Meta description < 155 chars with CTA
- [ ] Exactly one H1 on the page (no duplicates)
- [ ] Zone 1 content: 50–150 words
- [ ] Zone 2 content: 300–500 words (excluding FAQ schema text)
- [ ] Definition-first opening paragraph (40–60 words, citation-ready)
- [ ] Comparison table present (for multi-type categories)
- [ ] Curator's Note with photo + credentials link
- [ ] Related Guides section with 3–5 internal links
- [ ] "Last reviewed: [Month Year]" freshness line visible

**Schema**
- [ ] `@graph` schema: CollectionPage + ItemList + Product data + BreadcrumbList + FAQPage
- [ ] `dateModified` set in CollectionPage schema
- [ ] Schema validates in Google Rich Results Test
- [ ] Canonical tag points to clean collection URL

**Mobile-First (NEW — MANDATORY)**
- [ ] `<style>` media-query block prepended at top of HTML file
- [ ] Curator's Note outer div has `class="usup-curator"`
- [ ] Curator's Note inner text div has `class="usup-curator-body"` and `min-width: 0`
- [ ] Every Related Guide `<li>` has `class="usup-guide-item"` with `display: flex; gap: 8px`
- [ ] Every `→` arrow span has `class="usup-guide-arrow"` (no `position: absolute`)
- [ ] Every guide `<a>` has `class="usup-guide-link"`
- [ ] Visually verified on 375px viewport: Curator's Note stacks vertically, guide links left-align without detached arrows

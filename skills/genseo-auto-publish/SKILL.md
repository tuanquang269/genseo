---
name: genseo-auto-publish
description: >
  Fully autonomous end-to-end SEO content pipeline. This skill replaces the need to manually sequence Strategist, Writer, and Publisher. You give it a keyword or brief, and it will plan, write, source images, fetch internal links, and publish to Shopify directly in one continuous stream.
metadata: {"clawdbot":{"emoji":"🏭","requires":{"commands":["python3","curl"]},"os":["linux","darwin","win32"]}}
---

# GenSeo Auto Publish (End-to-End Orchestrator)

You are the Master Orchestrator. When the user invokes this skill, you must execute the entire SEO content pipeline from Research to Publishing AUTONOMOUSLY. Do not pause to ask the user to switch agents. You possess the powers of the Strategist, the Writer, and the Publisher all in one.

The daily headless prompt carries `SCOPE_WAIVER (Kevin, standing approval for the daily blog article)`. On that run the always-on file-count scope gate is off. More than 2 output files does not mean show a menu and wait. Write the one ticket (draft, images, claims log, tracker row, ticket update) and publish the blog article live after `validate_article.py` prints PASS. A template named LISTICLE is still that blog article. This waiver does not publish a landing-page listicle. On 2026-10-12 three hosted-9router runs showed a file-count menu for `#MB1009-7` and exited 0 with the ticket unchanged.

## Required Input Check
Before diving into Step 1, verify you have:
1. The Target Topic or Keyword(s).
2. The Mode: `[NEW ARTICLE]` or `[REFRESH EXISTING]`. (If Refresh, require the `ARTICLE_ID`).
3. The Target `BLOG_ID`. **Default for wellnessnest.co = `104008483131` (the store's only
   blog, handle `news`) — use it whenever a ticket doesn't say otherwise; never stop to ask
   in an unattended run.**

---

## 🚀 The Autonomous Sequence (10-Step Pipeline)

### STEP 0: DUPLICATE CHECK (MANDATORY — do this FIRST, before anything else)
Publishing a second article for a keyword you already rank for splits your ranking signal
(this is what cost us the atlas/agym/cbum traffic). So before writing:
```
curl -s "https://wellnessnest.co/search/suggest.json?q=PRIMARY_KEYWORD&resources[type]=article&resources[limit]=5"
```
- If an existing article already targets this exact PRIMARY_KEYWORD, **STOP. Do not create a new article.**
  Mark the ticket `[SKIPPED-DUPLICATE: <existing_url>]` and, if the existing one is thin
  (<900 words), switch to `[REFRESH EXISTING]` mode to enrich it instead of duplicating.
- Tickets in the schedule file are NOT a guarantee the topic is unpublished — the `[DONE]`
  markers drift out of sync with the live site. Always verify against the live site here.

### STEP 0.5: TOPIC FITNESS (MANDATORY — is this topic worth an article at all?)
STEP 0 stops exact-keyword duplicates. This stops the bigger leak: **thin / dead topics.** A
audits of thin blog libraries typically find only a small minority of pages earn any click — the dead ones
are generic flavour / recipe / variant pages ("coffee protein shake", "banana protein powder",
"fruity pebbles protein"), exactly the scaled content the May 2026 core update penalises. Before
writing anything, run the gate:
```
python3 ~/genseo/scripts/topic_fitness.py "PRIMARY_KEYWORD_OR_TITLE"
```
- **FAIL** → **STOP. Do NOT write.** Mark the ticket `[SKIPPED-UNFIT: <reason>]`:
  - *flavour/recipe variant, no stocked product* → dead pattern, ~0 US clicks. Skip.
  - *category head-term a collection owns* (e.g. "best probiotics for women") → the COLLECTION
    must win it; a new article cannibalises it. Skip (flag it for a collection-SEO pass instead).
  - *near-duplicate of an existing article* → switch to `[REFRESH EXISTING]` on that URL, don't recreate.
  - *US demand below floor* → no audience. Skip.
- **REVIEW** → proceed ONLY if the ticket brief explicitly greenlit this exact topic (i.e. it came
  from a vetted PASS queue). Otherwise mark `[SKIPPED-UNFIT: needs human vetting]` and move on.
- **PASS** → proceed. For an own-brand DTC store the proven winners are **ingredient/benefit
  long-tail with buyer intent** that funnels to a product we actually sell.

| ✅ WRITE (earns US clicks) | ❌ NEVER (dead / cannibalising) |
|---|---|
| Ingredient buyer question: "Shilajit Resin vs Gummies: Which Works Better?" | Flavour/recipe variant: "shilajit smoothie recipes" |
| Audience-specific benefit: "Creatine for Women Over 40: What Changes" | Bare head-term a collection owns: "best probiotics" (→ collection) |
| Comparison that ends at our SKU: "NMN vs NR: What the Dose Panels Say" | A page we already have (→ refresh it, don't duplicate) |
| Problem→mechanism: "Menopause Joint Pain: Why It Starts at 45" | Third-party brand reviews for brands we don't sell |

(The STEP 6 validator also enforces this mechanically as a backstop — but running it here saves the
wasted image-generation + writing cost of a doomed article.)

### STEP 1: Define Goal & Primary Question
- **⚠️ CHECK CURRENT YEAR FIRST:** Run `date +%Y` to get the current year. Use this year throughout ALL article content, FAQ headings ("best X in the US in [YEAR]"), and image generation prompts ("Best Fat Burners US [YEAR]"). NEVER hardcode a year without checking. The current year baked into images is permanent — regenerating is expensive.
- **⭐ PRIORITY BRANDS (business rule — apply NATURALLY, never forced):**
  Every brand below is a HOUSE brand sold on wellnessnest.co. Priority order:
  1. **ShilaSource** — Himalayan shilajit resin + gummies + gold resin + energy drops.
   **Shilajit Shockwave** (`shilajit-shockwave`) pack-label claims come only from `product_refs/shilajit-shockwave.label.json` (OCR-accepted identity lines; no milligram, serving count, or volume token). `scripts/shockwave_rules.py`, run by `scripts/brand_rules.py`, hard-fails a dose that file does not list.
   **Pure Shilajit Gold Resin** (`pure-shilajit-gold-resin`) pack-label claims come only from `product_refs/pure-shilajit-gold-resin.label.json` (`required` + `optional`, including `75% Fulvic` and `1.06 oz (30g) - 75 servings`; no milligram token). `scripts/gold_resin_rules.py`, run by `scripts/brand_rules.py`, hard-fails a dose that file does not list.
   **ShilaSource Himalayan Shilajit Resin** (`shilasource-himalayan-shilajit-resin`) pack-label claims come only from `product_refs/shilasource-himalayan-shilajit-resin.label.json` (`required` + `optional` from the 2026-10-08 OCR read, including `70% Fulvic Acid*`, `1.06oz (30g)`, and the split `75` / `SERVINGS` badge; no milligram token). `scripts/shilasource_resin_rules.py`, run by `scripts/brand_rules.py`, hard-fails a dose that file does not list.
  2. **FusiForce** — creatine monohydrate gummies 5,000mg
  3. **FloraFresh** — vaginal/feminine probiotic gummies. Formula ONLY from its Supplement Facts label: Bacillus coagulans SNZ-1969 (spore-based), 15B CFU per 2 gummies, Vitamin C 30 mg, pineapple fruit powder 100 mg (with bromelain), sweetened with maltitol + isomalt (not sugar-free). Kevin 2026-10-21: 15B CFU is the count. 1 billion CFU and 1B CFU are retired and `florafresh_rules.py` rejects them. The live PDP description still tells a wrong strain story (four Lactobacillus strains, XOS, D-mannose, sugar-free) until Kevin's GO rewrites it: never copy that story or the older FloraFresh articles that repeat it (`scripts/florafresh_rules.py`, run by `scripts/brand_rules.py`, hard-fails those claims in `validate_article.py` and `lint_tickets.py`).
  4. **MenoMate** — menopause probiotics & herbal blend
  5. **Turkesterone** Advanced Formula (`turkesterone-advanced-formula`). Pack-label claims come only from `product_refs/turkesterone-advanced-formula.label.json` (front-of-pack lines, including the split `60` / `Capsules` badge; no milligram token and no Supplement Facts panel). `scripts/turkesterone_rules.py`, run by `scripts/brand_rules.py`, hard-fails a dose that file does not list. Bare "turkesterone" in a trial sentence is the ingredient, not this SKU.
  6. **AgeAura** — longevity line on the same store. Promote ONLY AgeAura Pure NMN + TMG NAD Complex (`/products/ageaura-pure-nmn-tmg-nad-complex`). Never Urolithin A, peptides, bundles, `ageaura-pure-nmn-tmg-p2`, `/collections/ageaura`, or any other AgeAura SKU (`scripts/ageaura_rules.py` is the handle allowlist; `scripts/brand_rules.py` hard-fails them in `validate_article.py` and `lint_tickets.py`; Kevin 2026-10-07, re-audited 2026-10-09).
  ⛔ **NEVER mention or link MuscleMax** (competitor, not ours). ⛔ Never link any
  product/brand not sold on wellnessnest.co (404 links fail the gate). "Naturally"
  means a creatine article leads with FusiForce because FusiForce IS creatine —
  never shoehorn an irrelevant house brand into a topic. If the ticket brief names
  specific products, use exactly those.

- Decide the **business goal** of the article (educate, capture leads, sell a product, rank for a key phrase).
- Turn the target keyword into **one main user question**, phrased how a real person would ask it (e.g., "What is the best pre workout for beginners in the US?").
- List 3–6 supporting questions (e.g., side effects, dosage, price range) that will become subheadings and FAQ entries — these are what answer engines love to extract.

### STEP 2: Keyword Expansion & Research
- **Active Keyword Expansion:** Use the web-search tool (WebSearch) with the primary keyword to discover:
  - 3–5 **long-tail and question keywords** (e.g., "is pre workout safe for beginners", "how to take pre workout")
  - **AEO-friendly question variants**: "how", "what", "is it safe", "vs"
  - **US-context variants**: "in the US", "delivery", "online" (nationwide DTC — no city/neighbourhood/near-me angles, see STEP 5)
- **Product Handle Sourcing:** Run in the shell (Bash): `curl -s "https://wellnessnest.co/search/suggest.json?q=YOUR_KEYWORD&resources[type]=product"` to find the exact product handlers for internal links. Do not guess handles!
- **Internal Linking Strategy (Power & Target Pages):** Run in the shell (Bash): `python3 ~/genseo/scripts/get_internal_links.py` to retrieve the current Top Power Pages (high traffic) and Target Pages (striking distance). Record these URLs and their target keywords to be naturally embedded into the article body in Step 5.
- **Optional cluster follow-ups:** if `state/cluster_map.json` exists, run `python3 scripts/cluster_related_questions.py --query "<primary keyword>" --package` (use `--handle <slug>` when that slug is already in the map). Paste the in-body sentences in the relevant sections and place "What to ask next" before `## Frequently Asked Questions`. Those lines link the pillar and sibling articles. They are not an FAQ. Do not turn them into `###` questions and do not add FAQPage JSON-LD for them. If the map file is missing, skip this and keep the usual outline. Publish still goes through `validate_article.py` and `shopify_publisher.py`. The daily job does not set `GENSEO_CLUSTER_PICKER`.
- Record the expanded keyword list and internal links mentally — you will weave ALL of them naturally into the article body and FAQ section.

### STEP 3: SERP Analysis & Outline Mapping
- **Competitor SERP Analysis:** Use the web-search tool (WebSearch) to search the primary keyword and examine:
  1. What the **top 3 ranking articles** cover (angle, structure, depth)
  2. **"People Also Ask" questions** — harvest these to seed your FAQ section
  3. **Content gaps** the competitors missed that you can fill better
- **Read Knowledge Base:** Read `~/genseo/knowledge_base/SEO_EEAT_GUIDELINES.md` and `AEO_GEO_GUIDELINES.md`.
> **Official-source GEO rules (2026-10-09):** AEO_GEO_GUIDELINES.md §6 overrides §1–§5 when they conflict. Rules 20–39 add crawler user agents, citation patterns, llms.txt and schema caveats, and the Kevin-GO list in §6.9. After writing each article, run `python3 scripts/geo_official_lint.py <article.html>` (WARN-only, never blocks) and fix the warnings you can. Vault digests: `~/PATI/LLM-Wiki/90-sources/geo-official/digests/` (newest on this Mac: 2026-10-08).
- **Build an Outline** that covers what the SERP shows plus gaps, following this skeleton:
  - H1: Main benefit + keyword + "the US"
  - H2: Direct answer / short definition (the AEO answer block)
  - H2: Benefits / pros & cons
  - H2: Step-by-step "how to" or detailed breakdown
  - H2: Local angle ("Where to buy in the US", delivery, comparison)
  - H2: Product comparisons (with tables where applicable)
  - H2: FAQs (seeded from PAA + local questions)
  - H3: About the Author

### STEP 4: Title & Meta — WIN THE CLICK (CTR is the bottleneck)
Most of our articles already rank on page 1 but get almost NO clicks. Ranking is solved;
**the click is not.** The title tag and meta description are what earn the click in the SERP
and in AI Overviews. Treat this step as writing an ad, not a label.

**TITLE RULES (the H1 / first `# ` line — becomes the Shopify title):**
- **≤ 60 characters** (longer gets truncated in Google → looks broken → fewer clicks). Hard limit.
- **Front-load the primary keyword** (first 1–4 words) so it's bold in the SERP.
- **Add ONE click trigger** — a number, a specific benefit, a year, or a curiosity/contrarian angle.
- **Include "the US"** but do NOT stack 3 generic descriptors. One angle, not five.
- **Kill the boilerplate.** Every competitor writes "The Ultimate Guide to X" / "Complete 2026
  Review & Sourcing Guide." Those are invisible. Be specific and human.

| ❌ Weak (ranks, low CTR) | ✅ Strong (earns the click) |
|---|---|
| The Ultimate Guide to Atlas Whey Protein in the US | Atlas Whey Review: Is It Worth It in the US? (2026) |
| Combat XL Mass Gainer US: Complete 2026 Review & Sourcing Guide | Combat XL Mass Gainer: 1,270 Calories Per Serve — US Review |
| Gym Supplements US: Ultimate 2026 Buying Guide & Store Review | 7 Gym Supplements Worth Buying in the US (2026) |
| The Ultimate Guide to Creatine Monohydrate Supplement | Creatine Monohydrate: Which to Buy in the US (2026)? |

**META DESCRIPTION RULES (`<!-- meta_description: ... -->`, line 2):**
- **140–155 characters.** Front-load the answer/benefit, end with a concrete differentiator + soft CTA.
- Must include the primary keyword + "the US".
- Use a SPECIFIC hook the competitor can't copy: a $ price ("from $49"), a number, a concrete number or benefit (never invent shipping or authenticity claims).
- ❌ "Discover the best X in the US. Expert picks with fast delivery." (generic, every page says this)
- ✅ "Compared 6 mass gainers sold in the US — Combat XL gives the most calories per dollar. See picks, $ prices & where to buy authentic."

**URL handle:** publisher auto-generates from the title; confirm it produces a clean keyword slug.

### STEP 5: Content Writing & Asset Generation (The Muscle Phase)
- **Image Generation — via `article_images.py` (ima2 / ChatGPT Image 2.0 OAuth ONLY):**
  All article images are generated with the repo wrapper, which enforces the PATI hard rules
  (ima2 OAuth generator, ≤1K resolution, webp compressed <80KB before upload):
  ```
  python3 /Users/kevinkreative/genseo/scripts/article_images.py \
      --slug <article-slug> --name <image-name> --prompt "..." \
      [--product-ref <handle>[:index]] [--ugc] [--qc] \
      [--persona-ref /Users/kevinkreative/genseo/personas/<handle>/ref.jpg] \
      [--ref /abs/path/extra_ref.png] [--square]
  ```
  It prints the LOCAL absolute path to use in the draft. One call per image.
  - **🔒 i5.2 UGC FRAMEWORK (Kevin, 2026-08-07; hero lane replaced 2026-08-08) — READ `references/ugc-image-framework.md` BEFORE writing any image prompt.** Posture: **HERO = MODEL + PRODUCT lane** (approved persona holding the real pack label-forward, bright ad-style, DIFFERENT persona per post, `--persona-ref` + `--product-ref` + `--qc`, no `--ugc` — full spec in the framework's § Hero lane); **ALL 3 INLINE images = UGC lane** — write the FULL 10-section labeled prompt from the framework (Spec · Fidelity Lock · Reference · Scene/Moment · Device & Camera · Subject & Body · Lighting · Environment Detail · Style/Imperfection · Negative) and pass `--ugc --qc`. A run-on blob prompt or a thinned section is a violation — that is exactly what produces glossy stock output. Typical inline mix: 1 persona-in-scene (`--persona-ref`, approved bank only) + 2 no-face (hands/POV/flat-lay). QC FAIL (exit 2) → fold the printed reason into the prompt and re-roll, max 2. A face image that is still refused or still failing QC falls back to one human no-face shot for that image only (a hand, a forearm, or a body cropped below the eyes; no --persona-ref), then the article continues. An empty pack-only still life is not that fallback.
  - **Persona bank:** faces come ONLY from `~/genseo/personas/<handle>/` (each approved ONCE by Kevin through the Pinterest real-face gate). Always feed the ORIGINAL ref.jpg, never a previous gen. No approved persona for the demo you need → no-face composition for this article and tell Kevin a new persona needs the one-time gate.
  - **Scene-variety guard:** check the `scene` column of the last ~10 rows in `PUBLISHED_ARTICLES_TRACKER.csv`; never repeat the same scene type twice in a row. Log each image's scene type on publish.
  - **🔒 HARD RULE (Kevin, 2026-08-07) — GENERATED PRODUCT IMAGERY IS ANCHORED ON THE REAL /products/ PACKAGING. NEVER INVENT PACKAGING.** Every image that shows a product is still *generated* (the ima2 lane stays), but it MUST be generated from the real pack shot on the live PDP: pass `--product-ref <handle>[:index]` (the wrapper auto-downloads `https://wellnessnest.co/products/<handle>.js` image [index], attaches it as ref, and appends a packaging-fidelity clause to the prompt). Package FORMAT (pouch vs jar vs bottle vs tub), colors, and label must match the live PDP exactly. Founding violation: FusiForce gens showed a JAR — the real product is a green stand-up POUCH. Two corollaries: (1) the PROMPT must also describe the real package format ("green stand-up pouch", never "jar") — prompt text overrides the ref when they disagree; (2) after generating, OPEN the output next to the ref and verify the package matches BEFORE putting it in the draft. Concept images with no product in frame need no ref. **🔒 CURATED REF LIBRARY (Kevin 2026-08-09, after two wrong images shipped): pass `--product-ref <handle>` with NO `:index`.** `~/genseo/product_refs/<handle>.png` (+ `.json` describing format/colour/wordmark) is the packaging truth and the wrapper injects its description into the prompt automatically. PDP indexes are marketing composites — FloraFresh index 1 contains NO pouch, and generating against it produced an invented white pouch with the graphic's stat badges pasted on. If the wrapper warns that a SKU has no curated ref, OPEN the fallback ref and confirm the package is in it, or stop and report that the SKU needs curating. Also match product details beyond the label (gummy colour = real flavour).
  - **Hero Banner Rule (HARD, Kevin 2026-08-08 — the hero IS the thumbnail/og:image):** The FIRST image MUST be the Hero Banner and it MUST show BOTH an approved-bank persona (visible face) AND the real product pack (label-forward, legible at thumbnail size) — `--product-ref` + `--persona-ref` + `--qc`. **Default composition = pack STANDING beside/in front of the model, hands NOT touching it (NEG "no hands touching the pouch") — ima2 warps hand-pack grips; holding pose only on the first roll, never on re-rolls.** The hero persona MUST be a different character from the previous articles' heroes (rotate the bank, log the handle in the tracker `persona` note); bank can't provide a different demo-appropriate face → use the least-recently-used compliant persona and report "persona bank needs expansion". The wrapper already appends the no-watermark/no-caption/label-legible suffix to every prompt.
  - **⚠️ MANDATORY — hero + ≥3 MORE BODY IMAGES per article (the gate hard-fails below 3 inline; the stripped hero does not count toward the 3):** every distinct product mentioned by name gets its own lifestyle image in its section, and when the article features fewer than 3 products, add concept images to reach 3 — a mechanism/how-it-works visual, a usage-moment scene, or a comparison visual for the table section. So a single-product article = 1 hero + 1 product lifestyle + 2 concept images minimum, ALL FOUR as `![...]()` tags in the body, hero FIRST (see hero-placement rule below).
  - **Faces = APPROVED PERSONA BANK ONLY** (`~/genseo/personas/`) — the hero REQUIRES one (rule above); inline images may use one persona-in-scene; never a fresh/invented face (the 🧑 real-face gate owns new personas). **ALWAYS `ls ~/genseo/personas/` and read each `persona.json` to enumerate the live bank — never assume its size** (4 personas as of 2026-08-09: f1-redshirt, f2-brunette, f3-silver, m1-stubble — but the directory is the truth).
  - **CRITICAL FAILURE SAFEGUARD:** If image generation fails, abort the entire run. DO NOT write a draft with missing images — the gate hard-fails under 3 inline images anyway.
  - **⛔ NEVER USE PRE-BAKED CDN URLS FOR IMAGES IN THE MARKDOWN DRAFT.** Use the exact LOCAL absolute path the wrapper prints in your `![alt](LOCAL_PATH)` tags. The publisher uploads local paths to Shopify Files CDN and rewrites them. If the publisher prints `📸 Uploading 0 image(s)` on an article that should have images, STOP and fix the image paths in the draft.

- **🎨 TEMPLATE ROTATION (Kevin "Full pack" 2026-08-09) — READ `references/article-templates.md` BEFORE drafting.** 4 dạng bài: `EDITORIAL` · `STORY` (bài GemPages joint-pain làm chuẩn) · `LISTICLE` · `COMPARISON`. Chọn theo ticket `type:` nếu có, không thì match intent theo bảng trong reference; hai dạng cùng khớp → tránh lặp dạng của bài liền trước (đọc note `template:` ở tracker row cuối). Dùng đúng block kit trong reference (inline CSS, blank line quanh block, markdown NGOÀI block — publisher dùng python-markdown `extra`, block HTML pass through nguyên vẹn). Log `template:<KEY>` vào tracker row + report.
- **Drafting — Answer-First Structure:** Write the article in Markdown following these critical rules:
  - **CRITICAL FORMATTING RULE:** DO NOT include any YAML frontmatter (e.g., no `---`). The very first line of the markdown file MUST be the H1 Title (e.g., `# Your Title Here`). The second line MUST be the meta description comment (e.g., `<!-- meta_description: ... -->`). The publisher reads the H1 to set the Shopify article `title` field, then **automatically strips it from the rendered body HTML** — so it will NOT appear twice. Do NOT remove it from the draft.
  - **⚠️ HERO PLACEMENT (corrected 2026-08-07 — the code is the authority):** the Hero Banner MUST be the FIRST `![...]()` image tag in the body markdown. `shopify_publisher.py do_publish` takes the FIRST local image found in the body, sets it as `article.image` (the Shopify featured image the theme renders on top), and STRIPS that one tag from the body — so the hero never appears twice. The old instruction ("do not embed the hero in the body") was wrong: with no hero in the body the publisher silently promoted-and-stripped the first lifestyle image instead, and the live article came out one inline image short. Never reference the hero a second time in the body.
  - **ANSWER-FIRST INTRODUCTION (AEO CRITICAL):** The first paragraph (40–60 words) MUST directly and completely answer the primary question with zero fluff. No throat-clearing, no "In this article we will..." — answer first, then expand. This "answer block" is the #1 signal for featured snippets and AI Overview selection. The gate fails an opener under 30 words or one that starts with throat-clearing, and warns outside 40–70.
  - **QUESTION-STYLE H2s:** At least two `##` headings must be questions (`What` / `How` / `Does` / `Is` / `Can` / `Should` / `When` / `Where` / `Why`, or a heading that ends in `?`). Numbered steps ("1. Check the label") do not count. The gate fails a draft with fewer than two.
  - **H1 LENGTH:** Keep the H1 at 50 characters or under. The theme appends ` – Wellness Nest` (~16), and title tags over ~70 truncate. The gate warns above 50.
  - **DO NOT WRITE A DATE LINE:** Do not add `Published: Month D, YYYY` or `Last updated:`. The theme already prints the date. A hand-written date has disagreed with that header by one day (US Pacific vs UTC). The gate fails a `Published:` line.
  - **Self-Contained Sections:** Each H2 section must be independently comprehensible without reading previous sections. AI systems may extract and quote a single section out of context. NEVER use "As mentioned above..." or "Building on the previous point..."
  - **Body Structure for AEO:** Under each heading, start with a direct 1–2 sentence answer, then expand with details (examples, data, pros/cons). Use scannable formatting: short paragraphs, bullet/numbered lists, and comparison tables.
  - **MANDATORY LENGTH:** Determine the Search Intent and write to these exact target lengths:
    - *Quick Guide & FAQs:* 1,000 – 1,500 words. No fluff, direct answers.
    - *Buying Guides / Comparisons:* 1,500 – 2,500 words. Deep analysis, pros/cons. (Most common for Wellness Nest).
    - *Pillar Posts/Ultimate Guides:* 2,500+ words. Comprehensive A-Z coverage.
  - **NO META-LANGUAGE:** NEVER explicitly state the word count or strategy type in the text itself (e.g., NEVER write "In this 2,500 word pillar post").
  - **⛔ BANNED PHRASES (the validator now hard-fails on these).** Google's Sept 2025 Quality Rater Guidelines treat filler and generic AI phrasing as scaled-content-abuse signals (§4.6, §4.6.5, §4.6.6), which is what the May 2026 core update punished us for. On 2026-07-30 all 534 of our own drafts were scored and these are the phrases we actually produce, with real counts. Do not write any of them:
    - `when it comes to` (57 occurrences) → just state the thing
    - `furthermore,` (52) → delete it, or use `also`
    - `navigating the` (26) → say what the reader does, e.g. `choosing between`
    - `elevate your` (25) → name the concrete benefit
    - `game-changer` (22), `state-of-the-art` (13), `cutting-edge` (6), `transform your` (5)
    - `the cornerstone of` (9), `at its core` (6), `in the realm of`
    - `let's dive in` / `let's dive into` (10) → start with the answer instead
    - `ultimately,` (4), `in summary,`, `delve into`, `by leveraging` (2)
    Write the sentence directly instead of reaching for a connector. If a paragraph only exists to introduce the next paragraph, delete the paragraph.
  - **CITE OR DROP NUMBERS:** if you write a statistic, a percentage, a study reference, or a "X times more effective" comparison, put a real source link next to it. If there is no source, do not write the number. The validator flags articles that make 3+ factual claims with zero citations.
  - **PRIMARY SOURCE (HARD):** at least one link to PubMed, NIH, FDA, CDC, WHO, a DOI, regulations.gov, Examine, USADA, or WADA. A Flickr credit or a retailer blog does not count. The gate also resolves outbound links and fails a 404, a 410, or a redirect loop. A publisher 403 (bot wall) is a warning, not a pass to invent a different URL — confirm the link opens.
  - **INTERNAL LINKS (HARD):** at least one `https://wellnessnest.co/products/<handle>` for the product the article is about, and at least one related `https://wellnessnest.co/blogs/news/<handle>` article. Both must be live.
  - **META DESCRIPTION:** the line-2 `<!-- meta_description: ... -->` must be 120–165 characters.
  - **ALT TEXT:** every image alt is a real phrase (not empty, not "image" / "photo"). The gate fails a short or missing alt.
  - **NO DISEASE OR APPROVAL CLAIMS:** do not write that a product cures, treats, or prevents a disease, and do not call it FDA-approved or clinically proven. Saying a supplement does not treat an infection is correct and stays.
  - MUST follow all EEAT and AEO/GEO guidelines from the knowledge base.
  - MUST embed the `curl`-fetched Internal Links absolutely (e.g. `https://wellnessnest.co/products/handle`).
  - MUST format the FAQ precisely using `## Frequently Asked Questions` > `### Question`.
  - **⛔ DO NOT embed `<script type="application/ld+json">` tags in the markdown file.** The markdown renderer outputs them as visible raw text in the article body. FAQ schema and other JSON-LD must be passed as raw HTML appended to `body_html` AFTER the markdown-to-HTML conversion step, never inside the `.md` draft file.

- **US-Market Signals (nationwide DTC store — NOT local SEO):**
  - Include a US anchor ("US", "United States", "American") in the first paragraph
    and at least one H2 — the validator checks both.
  - Ground the article in US buyer context naturally: FDA supplement labeling
    (structure/function, not drug claims), third-party testing expectations,
    US shipping from wellnessnest.co, seasonal/climate context, US price anchors in $.
  - Include at least **1 buying-context FAQ** (e.g., "Where can I buy [product] in the US?",
    "How long does Wellness Nest shipping take in the US?" — answer honestly from store policy;
    NEVER invent shipping speeds or authenticity claims).
  - Do NOT fake a local angle (no invented cities, stores, or pickup points — we ship nationwide).

- **E-E-A-T Named Author Bio (CRITICAL/YMYL):** You MUST conclude every article (after the FAQs) with an `### About the Author` section. The Wellness Nest blog byline is **Mike Moretti** only (Kevin 2026-10-21). DO NOT use generic bylines like "Wellness Nest Team" and do not use Dr. Marcus Hale. `validate_article.py` rejects that name and `/pages/dr-marcus-hale`.

  Format, copied verbatim:

  `[Mike Moretti](/pages/mike-moretti) — Co-founder, Wellness Nest`

  **⛔ THE BIO SENTENCE IS FIXED TEXT — "Co-founder, Wellness Nest". Do not paraphrase, extend, or add credentials, job titles, years of experience, certifications, or specialisms of any kind.** TODO: no approved headshot, and `/pages/mike-moretti` is not confirmed live. Do not invent a photo, a longer bio, or a medical credential, and do not create the author page from this repo. Dr. Marcus Hale remains in `roster.json` so older landing specs still name a roster person. He is not the blog byline.

  **The roster lives in ONE place: `roster.json`.** The validator, the publisher and the
  repair scripts all read it (`scripts/genseo_roster.py`), so there is nothing to keep in
  sync by hand. If `roster.json` is empty, the gate blocks publishing — that means Kevin
  has not approved the roster yet; STOP and tell him, never fill it yourself.

  **The blog byline is Mike Moretti.** Do not pick Dr. Marcus Hale for a blog article.

  **⛔ NEVER invent a byline.** A name that is not in `roster.json` is a
  fabricated identity on YMYL health content — the single most damaging thing
  this pipeline can do. The banned-name list (donor placeholders + anything
  ever removed) is `FAKE_AUTHORS` in `scripts/validate_article.py`.

  **⛔ Never write "Dr.", "MD", "PhD", "RD", "Registered Dietitian", "CISSN", or any certification next to any byline.** Never attach a credential to a byline unless that person actually holds it.

  Format the bio as `[Name](/pages/handle)` followed by the exact sentence. DO NOT write "Connect with them on LinkedIn" and DO NOT put their LinkedIn URL in the visible markdown text. Store the LinkedIn URL only in the JSON-LD schema.

- **Save it:** Write (with the file-write tool)  the final Markdown content to `~/genseo/published_drafts/<article_name>.md`.

### STEP 6: Pre-Publish Quality Gate (MECHANICALLY ENFORCED — NOT OPTIONAL)
A self-checklist can be faked by a fast model. So after saving the draft, you MUST run the
mechanical validator. **You may not proceed to Step 7 until it prints `✓ PASS`.**

```
python3 ~/genseo/scripts/validate_article.py ~/genseo/published_drafts/<article_name>.md --draft
```

The validator checks, as code: word count ≥900, exactly the right heading structure, an
answer block containing "the US", a comparison `<table>`, a $ price range, ≥2
`/collections/` links, a named roster author with a LIVE `/pages/` link, an FAQ heading
plus ≥3 FAQ questions, ≥2 question-style H2s, a product URL, a related article URL, a
primary-source link, a 120–165 character meta description, descriptive image alt text,
no hand-written `Published:` date, no affirmative cure / FDA-approval / clinically-proven
claim, **topic fitness** (hard-fails dead flavour/recipe titles + collection-
owned head-terms — see STEP 0.5) — AND that every product/collection/article/page/author
URL returns HTTP 200 and that outbound citations are not 404, 410, or stuck in a redirect
loop (a 403 bot-wall is a warning). H1 titles over 50 characters warn.

**It also scores the PROSE (added 2026-07-30), and this part hard-fails too.** The structural
checks above only prove an article has a table and a price; they never measured whether the
writing was any good, which is exactly the gap the May 2026 core update exploited. The
validator now prints a `QRG:` line and fails on:

- `overall quality < 80` (our own 534-draft corpus has p10 = 83, so 80 is the bad tail)
- `filler score >= 25` — it prints the exact offending phrases
- `ai-pattern score >= 25` — likewise

Warnings only (fix if easy): repetition >= 20, information density < 0.55, and 3+ factual
claims with no citation.

A missing scorer prints `QRG scoring unavailable: <reason>` and does not fail the draft.
The scorer is the external claude-seo launcher
(`~/.claude/plugins/marketplaces/*claude-seo*/bin/claude-seo`), not a paid API call.
Do not invent a score. `GENSEO_QRG_ADVISORY=1` downgrades a measured failure to a warning;
it does not change a skip.

When it fails on filler or AI-pattern, the validator prints a `content_humanize.py` command
that does deterministic 1:1 phrase swaps. Review its diff; it does not add content. Better:
do not write the banned phrases in STEP 5 in the first place.

- If it exits `✗ DO NOT PUBLISH`, read each `✗` line, FIX that exact problem in the draft,
  and re-run. Repeat until `✓ PASS`. Do NOT rationalize skipping a failure.
- A thin or 404-linked article that somehow reaches Step 7 is a pipeline failure. The whole
  point of this gate is to stop the cheap model from publishing thin content during the
  Google core-update recovery.

(The validator intentionally does not check FAQPage JSON-LD in `--draft` mode because the
publisher appends that schema after the markdown→HTML conversion in Step 7. Ensure the
publisher step adds it.)

### STEP 7: Shopify Publishing (The Integration Phase)
**Publish ONLY with this python script. Do NOT use the Shopify MCP, GraphQL, `create-product`/
`update-product`, or curl — only this publisher adds the Article + FAQPage JSON-LD schema and the
named author. Any other path silently drops the schema.**

**⚠️ REVIEW POSTURE (Kevin, 2026-08-07): `publish` creates an UNPUBLISHED DRAFT by default.**
Kevin reviews drafts in Shopify admin and publishes them there. Do NOT pass `--live`
unless Kevin has explicitly ended the review period in writing.
- If the instruction was `[NEW ARTICLE]`:
  `python3 /Users/kevinkreative/genseo/scripts/shopify_publisher.py publish /Users/kevinkreative/genseo/published_drafts/<article_name>.md <BLOG_ID>`
- If the instruction was `[REFRESH EXISTING]`:
  `python3 /Users/kevinkreative/genseo/scripts/shopify_publisher.py update /Users/kevinkreative/genseo/published_drafts/<article_name>.md <BLOG_ID> <ARTICLE_ID>`
- **Then VERIFY the result:** `python3 /Users/kevinkreative/genseo/scripts/verify_published.py <ARTICLE_ID> <BLOG_ID>` — if it prints `✗` (schema/author missing), you published the wrong way; re-run the command above and re-verify before continuing.

### STEP 8: Post-Publish Verification (MANDATORY TWO-GATE CHECK — DO NOT SKIP)

This step has **two gates that BOTH must pass** before you may proceed to Step 9.

#### Gate 1 — CDN Script Check (Terminal)
Read the publisher script terminal output:
- `✅ IMAGE VERIFICATION PASSED` → Gate 1 passed. Continue to Gate 2.
- `⚠  PARTIAL` or `✗ IMAGE VERIFICATION FAILED` → audit and fix, then re-check:
  `python3 /Users/kevinkreative/genseo/scripts/audit_article_images.py`, fix the draft's
  image paths, re-run `update` for this article.

#### Gate 2 — Rendered-Body Check (MANDATORY — the real source of truth)
Even if Gate 1 shows ✅, verify the rendered article body.
- **DRAFT article (the default posture):** the public URL 404s until Kevin publishes it, so
  verify via the Admin API: fetch the article `body_html`
  (`verify_published.py <ARTICLE_ID> <BLOG_ID>` does this) and confirm every `<img src>` is a
  `cdn.shopify.com` URL that returns HTTP 200 with image bytes (`curl -sI` each one).
- **LIVE article (only after Kevin flips it):** open `https://wellnessnest.co/blogs/news/<HANDLE>`
  in the in-app Browser pane, scroll the full article, confirm ALL images (hero + every product
  lifestyle image) load — not broken, not placeholder. PASS/FAIL with counts.
  (If the pane blocks the domain by policy, fall back to `curl` + HTML checks — that is the
  approved fallback, do not open an outside browser.)
- **LIVE article + widget check:** every `/products/` link in the body becomes a card in the
  theme's **Shop-This-Article widget** (section `sections/shop-this-article.liquid`, wired into
  `templates/article.json`). For live articles confirm: (1) the HTML contains a
  `shopify-section-template--*__shop-this-article` section, and (2) `data-liquid-handles`
  holds ≥1 clean product handle. Full-page cache can lag theme edits — force a fresh render via
  `?section_id=<that section id>` before declaring FAIL. Repo copy of the section (for diffing
  theme drift): `/Users/kevinkreative/genseo/theme/shop-this-article.liquid`.
- If Gate 2 **FAILS** → images are broken despite Gate 1: fix the draft's image paths and
  re-run `update`, then re-run Gate 2 until PASS.

**CRITICAL RULE: You MUST NOT proceed to Step 9 or tell the user the article is complete until BOTH gates pass.** Never report "done" based on the terminal output alone. If you are running multiple articles in sequence, complete ALL gates for article N before starting article N+1.

### STEP 9: Update CSV Tracker
- You MUST append the new article's metadata to `/Users/kevinkreative/genseo/PUBLISHED_ARTICLES_TRACKER.csv`.
- The CSV has exactly **8 columns**: `Ticket,Keyword,Article Link,Posted Date,Has Indexed,Last Check Index Date,Has Tried Request To Index,Last Request Index Date`
- **CRITICAL**: Use the `csv` module (NOT raw `open().write()`) to guarantee correct CRLF line endings and proper column quoting. Run this in the shell (Bash):
```
python3 << 'EOF'
import csv, datetime
row = ['TICKET_NUM', 'primary keyword', 'https://wellnessnest.co/blogs/news/HANDLE', datetime.date.today().isoformat(), 'No', datetime.date.today().isoformat(), 'No', '']
with open('/Users/kevinkreative/genseo/PUBLISHED_ARTICLES_TRACKER.csv', 'a', newline='') as f:
    csv.writer(f).writerow(row)
EOF
```
- Replace `TICKET_NUM`, `primary keyword`, and `HANDLE` with actual values. Always set `Has Indexed=No`, `Has Tried Request To Index=No`, `Last Request Index Date=''` on first publish.

### STEP 9b: Mark the Ticket DONE in the schedule file (MANDATORY — keeps the cron's place)
The daily cron says "continue with the next ticket" and decides which is "next" by reading
the `[ ]` / `[DONE]` markers in the ticket headings of the schedule file. **If you do not mark
the ticket DONE, the cron re-runs it tomorrow and creates a duplicate DRAFT** (STEP 0's live
dedup check cannot catch drafts — `search/suggest.json` only sees published articles).
Ticket headings in `daily-tickets.md` look like `## [ ] Ticket #1 — NEW ARTICLE`; flip the
`[ ]` inside the heading:
```
python3 << 'EOF'
import datetime
f="/Users/kevinkreative/genseo/daily-tickets.md"   # <-- the file this run came from
n=1                                                 # <-- number of THIS ticket
url="https://wellnessnest.co/blogs/news/HANDLE"
today=datetime.date.today().isoformat()
t=open(f).read()
old=f"## [ ] Ticket #{n} "
assert old in t, f"heading not found: {old!r}"
t=t.replace(old, f"## [DONE {today} {url}] Ticket #{n} ", 1)
open(f,"w").write(t)
print("marked DONE: Ticket #", n)
EOF
```
- If STEP 0 found a duplicate and you SKIPPED, use `[SKIPPED-DUPLICATE {today} <existing_url>]`
  instead of `[DONE ...]`; if STEP 0.5 failed fitness, use `[SKIPPED-UNFIT <reason>]`.
- The next cron run picks the first heading still containing `[ ]`.

### STEP 10: Reporting & Refresh Flag
- Report the success of the sequence to the user. Present:
  - The final URL of the Shopify post
  - Image count verified (Gate 1 + Gate 2 results)
  - Brief summary of the semantic strategy (keywords targeted, SERP gaps filled, GEO signals used)
  - Meta description that was set
- **Refresh Flag:** Note the publish date. Flag this article for content refresh review in 90 days via the `genseo-refresh-planner` skill.

### TICKET REFILL: when the queue runs low (< 3 pending `[ ]` tickets)

The daily wrapper stocks the queue itself when open tickets are under `GENSEO_QUEUE_LOW_WATER`
(default two days of `GENSEO_DAILY_TARGET`, 10 when the target is 5). That unattended call is
`refill_tickets.py --if-below` only. Exit 3 writes `state/queue-low-water.marker` and does not
call Ads or an LLM. The mining recipe below is for an interactive session, not the unattended path.

First: `python3 scripts/refill_tickets.py --count 8 --dry-run`, then without `--dry-run` — gated,
product-mapped tickets from `templates/article-topic-bank.json` + `board/ideas.csv`
(`docs/TICKET_REFILL.md`). When it exits 3 (sources ran dry), mine the Google Ads account for the
next batch — the recipe (GAQL slices, term-pattern → article-type map, ticket checklist, hard
rules incl. verbatim `campaign.name`) is codified in
`references/ads-article-mining.md`. Its two goldmine classes: paid-but-not-converting terms
(organic arbitrage) and converting query patterns (compound proven intent). Append the new
batch to `daily-tickets.md` as `# Batch N` with the evidence header; never overwrite old
batches. Second pass when angle depth is needed: the GATC competitor-scrape lane described in
the same file.

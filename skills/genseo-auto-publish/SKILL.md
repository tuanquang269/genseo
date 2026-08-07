---
name: genseo-auto-publish
description: >
  Fully autonomous end-to-end SEO content pipeline. This skill replaces the need to manually sequence Strategist, Writer, and Publisher. You give it a keyword or brief, and it will plan, write, source images, fetch internal links, and publish to Shopify directly in one continuous stream.
metadata: {"clawdbot":{"emoji":"🏭","requires":{"commands":["python3","curl"]},"os":["linux","darwin","win32"]}}
---

# GenSeo Auto Publish (End-to-End Orchestrator)

You are the Master Orchestrator. When the user invokes this skill, you must execute the entire SEO content pipeline from Research to Publishing AUTONOMOUSLY. Do not pause to ask the user to switch agents. You possess the powers of the Strategist, the Writer, and the Publisher all in one.

## Required Input Check
Before diving into Step 1, verify you have:
1. The Target Topic or Keyword(s).
2. The Mode: `[NEW ARTICLE]` or `[REFRESH EXISTING]`. (If Refresh, require the `ARTICLE_ID`).
3. The Target `BLOG_ID`.
*(If the user gives you a Prompt from the Orchestrator Tickets, it generally implies the context. If Blog ID is missing, politely ask them to provide it, then proceed automatically).*

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
  - *flavour/recipe variant, no stocked brand* → dead pattern, ~0 {{MARKET_ABBR}} clicks. Skip.
  - *category head-term a collection owns* (e.g. "best protein powder {{market}}") → the COLLECTION
    must win it; a new article cannibalises it. Skip (flag it for a collection-SEO pass instead).
  - *near-duplicate of an existing article* → switch to `[REFRESH EXISTING]` on that URL, don't recreate.
  - *{{MARKET_ABBR}} demand below floor* → no audience. Skip.
- **REVIEW** → proceed ONLY if the ticket brief explicitly greenlit this exact topic (i.e. it came
  from a vetted PASS queue). Otherwise mark `[SKIPPED-UNFIT: needs human vetting]` and move on.
- **PASS** → proceed. This is the proven winner: a **specific stocked brand/product** + **review /
  comparison / where-to-buy / is-it-worth-it** intent.

| ✅ WRITE (earns {{MARKET_ABBR}} clicks) | ❌ NEVER (dead / cannibalising) |
|---|---|
| Brand review: "Mutant Whey Review (2026)" | Flavour variant: "Coffee / Banana / Fruity Pebbles protein shake" |
| Brand comparison: "Myprotein vs Optimum Nutrition" | Bare head-term: "best protein powder {{market}}" (→ collection) |
| Where-to-buy a brand: "Where to Buy Ghost in {{MARKET}}" | A page we already have (→ refresh it, don't duplicate) |

(The STEP 6 validator also enforces this mechanically as a backstop — but running it here saves the
wasted image-generation + writing cost of a doomed article.)

### STEP 1: Define Goal & Primary Question
- **⚠️ CHECK CURRENT YEAR FIRST:** Run `date +%Y` to get the current year. Use this year throughout ALL article content, FAQ headings ("best X in {{MARKET}} in [YEAR]"), and image generation prompts ("Best Fat Burners {{MARKET}} [YEAR]"). NEVER hardcode a year without checking. The current year baked into images is permanent — regenerating is expensive.
- **⭐ PRIORITY BRANDS (business rule — apply NATURALLY, never forced):** List
  your own priority vendors here in order, plus any vendor you do not carry
  and must never link (a link to a product you do not carry 404s and fails
  the gate). "Naturally" means a creatine article leads with a priority brand
  that actually makes creatine — never shoehorn an irrelevant brand into a topic.
  If the ticket brief names specific brands, use exactly those.

- Decide the **business goal** of the article (educate, capture leads, sell a product, rank for a key phrase).
- Turn the target keyword into **one main user question**, phrased how a real person would ask it (e.g., "What is the best pre workout for beginners in {{MARKET}}?").
- List 3–6 supporting questions (e.g., side effects, dosage, price range) that will become subheadings and FAQ entries — these are what answer engines love to extract.

### STEP 2: Keyword Expansion & Research
- **Active Keyword Expansion:** Use `search_web` with the primary keyword to discover:
  - 3–5 **long-tail and question keywords** (e.g., "is pre workout safe for beginners", "how to take pre workout")
  - **AEO-friendly question variants**: "how", "what", "is it safe", "vs", "near me"
  - **Location variants**: "{{MARKET}}", neighbourhood names, "near me", "delivery", "online"
- **Product Handle Sourcing:** Use `run_command` with `curl -s "https://wellnessnest.co/search/suggest.json?q=YOUR_KEYWORD&resources[type]=product"` to find the exact product handlers for internal links. Do not guess handles!
- **Internal Linking Strategy (Power & Target Pages):** Run `run_command` with `python3 ~/genseo/scripts/get_internal_links.py` to retrieve the current Top Power Pages (high traffic) and Target Pages (striking distance). Record these URLs and their target keywords to be naturally embedded into the article body in Step 5.
- Record the expanded keyword list and internal links mentally — you will weave ALL of them naturally into the article body and FAQ section.

### STEP 3: SERP Analysis & Outline Mapping
- **Competitor SERP Analysis:** Use `search_web` to search the primary keyword and examine:
  1. What the **top 3 ranking articles** cover (angle, structure, depth)
  2. **"People Also Ask" questions** — harvest these to seed your FAQ section
  3. **Content gaps** the competitors missed that you can fill better
- **Read Knowledge Base:** Read `~/genseo/knowledge_base/SEO_EEAT_GUIDELINES.md` and `AEO_GEO_GUIDELINES.md`.
- **Build an Outline** that covers what the SERP shows plus gaps, following this skeleton:
  - H1: Main benefit + keyword + "{{MARKET}}"
  - H2: Direct answer / short definition (the AEO answer block)
  - H2: Benefits / pros & cons
  - H2: Step-by-step "how to" or detailed breakdown
  - H2: Local angle ("Where to buy in {{MARKET}}", delivery, comparison)
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
- **Include "{{MARKET}}"** but do NOT stack 3 generic descriptors. One angle, not five.
- **Kill the boilerplate.** Every competitor writes "The Ultimate Guide to X" / "Complete 2026
  Review & Sourcing Guide." Those are invisible. Be specific and human.

| ❌ Weak (ranks, low CTR) | ✅ Strong (earns the click) |
|---|---|
| The Ultimate Guide to Atlas Whey Protein in {{MARKET}} | Atlas Whey Review: Is It Worth It in {{MARKET}}? (2026) |
| Combat XL Mass Gainer {{MARKET}}: Complete 2026 Review & Sourcing Guide | Combat XL Mass Gainer: 1,270 Calories Per Serve — {{MARKET_ABBR}} Review |
| Gym Supplements {{MARKET}}: Ultimate 2026 Buying Guide & Store Review | 7 Gym Supplements Worth Buying in {{MARKET}} (2026) |
| The Ultimate Guide to Creatine Monohydrate Supplement | Creatine Monohydrate: Which to Buy in {{MARKET}} (2026)? |

**META DESCRIPTION RULES (`<!-- meta_description: ... -->`, line 2):**
- **140–155 characters.** Front-load the answer/benefit, end with a concrete differentiator + soft CTA.
- Must include the primary keyword + "{{MARKET}}".
- Use a SPECIFIC hook the competitor can't copy: an {{CURRENCY}} price ("from {{CURRENCY}} $49"), a number, "100% authentic", "next-day {{MARKET_ABBR}} delivery".
- ❌ "Discover the best X in {{MARKET}}. Expert picks with fast delivery." (generic, every page says this)
- ✅ "Compared 6 mass gainers sold in {{MARKET}} — Combat XL gives the most calories per dollar. See picks, {{CURRENCY}} prices & where to buy authentic."

**URL handle:** publisher auto-generates from the title; confirm it produces a clean keyword slug.

### STEP 5: Content Writing & Asset Generation (The Muscle Phase)
- **Image Generation (MANDATORY Image-to-Image!):**
  - **Hero Banner Rule:** The FIRST generated image MUST be the Hero Banner and it MUST depict the real products discussed. Pass up to 3 real product image paths into `ImagePaths` so the banner shows real products, never purely AI-hallucinated tubs. Always append to every hero image prompt: **"NO watermark. NO blog name text. NO caption. NO attribution text in any corner. Clean image only."**
  - **⚠️ MANDATORY — 1 Lifestyle Image Per Product (NON-NEGOTIABLE):** Every distinct product mentioned by name in the article MUST have its own dedicated generated lifestyle image embedded in the section where it is featured. Do NOT write a product section without a corresponding image. A single hero image is NEVER sufficient. Count the products → generate that many images + 1 hero. This rule exists because: (1) it dramatically improves user engagement and conversion, (2) it signals comprehensive E-E-A-T coverage to AI search systems, and (3) it prevents the article from looking thin or unfinished.
  - **⚠️ COMPETITOR PRODUCT IMAGES (MANDATORY for review/comparison articles):** If the article reviews or compares a brand we do NOT carry (e.g. EHP Labs, Myprotein, etc.), you MUST also generate a lifestyle image for that competitor product. Fetch their product image as reference using: `curl -sL "https://<brand>.sg/products/<handle>.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['product']['images'][0]['src'])"`. Download it to `tmp_images/`, then pass it into `generate_image` ImagePaths. Place the image in the section that describes the competitor product. Do NOT leave the competitor product section image-free.
  - To prevent "AI Spam" looks, download real product images first: `curl -o ~/genseo/tmp_images/ref_product.png https://cdn.shopify.com/s/files/...`. Save to `tmp_images/` not `/tmp/`.
  - Pass the downloaded absolute path into the `ImagePaths` argument of `generate_image` so the AI uses the real product brand and shape as a reference.
  - **CRITICAL FAILURE SAFEGUARD:** If `generate_image` fails (e.g. 503 Capacity Exhausted), abort the entire operation immediately. DO NOT write a draft with missing images. Report to the user and ask them to retry.
  - **⛔ NEVER USE PRE-BAKED CDN URLS FOR IMAGES IN THE MARKDOWN DRAFT.** After `generate_image` runs, it returns a local absolute path (e.g. `~/.gemini/antigravity/brain/<conv-id>/filename_<hash>.png`). You MUST use that exact local path in your `![alt](LOCAL_PATH)` image tags. The publisher script reads local paths, uploads them to Shopify Files CDN, and rewrites them to real CDN URLs. If you write a CDN URL that doesn't exist yet (e.g. `https://cdn.shopify.com/s/files/.../t64_mutant_whey_lifestyle.png`), the publisher will see 0 images to upload and the article will have no images. The symptom is the publisher outputting `📸 Uploading 0 image(s)` — if you ever see that on an article that should have images, STOP and fix the image paths in the draft before proceeding.

- **Drafting — Answer-First Structure:** Write the article in Markdown following these critical rules:
  - **CRITICAL FORMATTING RULE:** DO NOT include any YAML frontmatter (e.g., no `---`). The very first line of the markdown file MUST be the H1 Title (e.g., `# Your Title Here`). The second line MUST be the meta description comment (e.g., `<!-- meta_description: ... -->`). The publisher reads the H1 to set the Shopify article `title` field, then **automatically strips it from the rendered body HTML** — so it will NOT appear twice. Do NOT remove it from the draft.
  - **⛔ DO NOT embed the Hero Banner image in the article body markdown.** The publisher sets the first generated image as `article.image` (the Shopify featured image), and the theme renders it at the top of the article automatically. Embedding it again as a `![...]()` tag in the body will cause a second hero image to appear. Only product lifestyle images belong as `![...]()` tags in the body.
  - **ANSWER-FIRST INTRODUCTION (AEO CRITICAL):** The first paragraph (40–60 words) MUST directly and completely answer the primary question with zero fluff. No throat-clearing, no "In this article we will..." — answer first, then expand. This "answer block" is the #1 signal for featured snippets and AI Overview selection.
  - **Self-Contained Sections:** Each H2 section must be independently comprehensible without reading previous sections. AI systems may extract and quote a single section out of context. NEVER use "As mentioned above..." or "Building on the previous point..."
  - **Body Structure for AEO:** Under each heading, start with a direct 1–2 sentence answer, then expand with details (examples, data, pros/cons). Use scannable formatting: short paragraphs, bullet/numbered lists, and comparison tables.
  - **MANDATORY LENGTH:** Determine the Search Intent and write to these exact target lengths:
    - *Quick Guide & FAQs:* 1,000 – 1,500 words. No fluff, direct answers.
    - *Buying Guides / Comparisons:* 1,500 – 2,500 words. Deep analysis, pros/cons. (Most common for Your Brand).
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
  - MUST follow all EEAT and AEO/GEO guidelines from the knowledge base.
  - MUST embed the `curl`-fetched Internal Links absolutely (e.g. `https://wellnessnest.co/products/handle`).
  - MUST format the FAQ precisely using `## Frequently Asked Questions` > `### Question`.
  - **⛔ DO NOT embed `<script type="application/ld+json">` tags in the markdown file.** The markdown renderer outputs them as visible raw text in the article body. FAQ schema and other JSON-LD must be passed as raw HTML appended to `body_html` AFTER the markdown-to-HTML conversion step, never inside the `.md` draft file.

- **GEO / Local Signals (MANDATORY for {{MARKET}} articles):**
  - Include "{{MARKET}}" in the H1 and first paragraph.
  - Add at least **2 neighbourhood or locality references** beyond just "{{MARKET}}" (e.g., {{LOCALITY}}, {{LOCALITY}}, {{LOCALITY}}, {{LOCALITY}}).
  - Include at least **1 local FAQ question** (e.g., "Where can I buy [product] in {{MARKET}}?", "Does Your Brand offer same-day delivery?").
  - Weave local context naturally: delivery coverage, store pickup, gym culture, climate references.

- **E-E-A-T Named Author Bio (CRITICAL/YMYL):** You MUST conclude every article (after the FAQs) with an `### About the Author` section attributing the article to ONE of the **real, named employees on your roster** below. DO NOT use generic bylines like "Your Brand Team".

  **⛔ THE BIO SENTENCE IS FIXED TEXT. Copy it VERBATIM. Do not paraphrase, extend, or add credentials, job titles, years of experience, certifications, or specialisms of any kind.** These are real people; anything you add about them is a fabricated claim about a real person's professional qualifications on health content, and it is the single most damaging thing this pipeline can do. If a topic seems to call for a credential nobody on this list has, that is not a licence to invent one — write the article without the claim.

  | Byline | Link | Bio sentence — copy exactly |
  |---|---|---|
  | **Author One** | `/pages/author-one` | REPLACE ME: one factual sentence about a real person on your team. |
  | **Author Two** | `/pages/author-two` | REPLACE ME: one factual sentence about a real person on your team. |
  | **Author Three** | `/pages/author-three` | REPLACE ME: one factual sentence about a real person on your team. |
  | **Author Four** | `/pages/author-four` | REPLACE ME. |
  | **Author Five** | `/pages/author-five` | REPLACE ME. |
  | **Author Six** | `/pages/author-six` | REPLACE ME. |
  | **Author Seven** | `/pages/author-seven` | REPLACE ME. |

  **Fill this table with YOUR OWN real staff before running the pipeline**, and
  create a live `/pages/<handle>` for each. Delete the rows you do not need, but
  keep the handles in sync with `ROSTER_PAGES` in `scripts/validate_article.py`
  and `ROSTER` in `scripts/shopify_publisher.py` — the gate rejects any byline
  that is not on all three lists, so a stale roster blocks publishing.

  **Pick the byline whose scope genuinely fits the topic.** Set one default
  for product reviews / comparisons / buying guides.

  **⛔ NEVER invent a byline.** A name that is not a real person on the roster
  above is a fabricated identity on YMYL health content — the single most
  damaging thing this pipeline can do. Keep a banned-name list here of any
  fabricated authors you have had to remove, so they are never recreated.

  **⛔ Never write "Dr.", "MD", "PhD", "RD", "Registered Dietitian", "CISSN", or any certification next to any byline.** Never attach a credential to a byline unless that person actually holds it.

  Format the bio as `[Name](/pages/handle)` followed by the exact sentence. DO NOT write "Connect with them on LinkedIn" and DO NOT put their LinkedIn URL in the visible markdown text. Store the LinkedIn URL only in the JSON-LD schema.

- **Save it:** Use `write_to_file` to save the final Markdown content to `~/genseo/published_drafts/<article_name>.md`.

### STEP 6: Pre-Publish Quality Gate (MECHANICALLY ENFORCED — NOT OPTIONAL)
A self-checklist can be faked by a fast model. So after saving the draft, you MUST run the
mechanical validator. **You may not proceed to Step 7 until it prints `✓ PASS`.**

```
python3 ~/genseo/scripts/validate_article.py ~/genseo/published_drafts/<article_name>.md --draft
```

The validator checks, as code: word count ≥900, exactly the right heading structure, an
answer block containing "{{MARKET}}", a comparison `<table>`, an {{CURRENCY}} price range, ≥2
`/collections/` links, a named roster author with a LIVE `/pages/` link, 4 FAQs, brand
mentions, image alt text, **topic fitness** (hard-fails dead flavour/recipe titles + collection-
owned head-terms — see STEP 0.5) — AND that every product/collection/author URL returns HTTP 200
(no guessed 404 links).

**It also scores the PROSE (added 2026-07-30), and this part hard-fails too.** The structural
checks above only prove an article has a table and a price; they never measured whether the
writing was any good, which is exactly the gap the May 2026 core update exploited. The
validator now prints a `QRG:` line and fails on:

- `overall quality < 80` (our own 534-draft corpus has p10 = 83, so 80 is the bad tail)
- `filler score >= 25` — it prints the exact offending phrases
- `ai-pattern score >= 25` — likewise

Warnings only (fix if easy): repetition >= 20, information density < 0.55, and 3+ factual
claims with no citation.

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
- If the instruction was `[NEW ARTICLE]`:
  Run `run_command`: `python3 ~/genseo/scripts/shopify_publisher.py publish ~/genseo/published_drafts/<article_name>.md <BLOG_ID>`
- If the instruction was `[REFRESH EXISTING]`:
  Run `run_command`: `python3 ~/genseo/scripts/shopify_publisher.py update ~/genseo/published_drafts/<article_name>.md <BLOG_ID> <ARTICLE_ID>`
- **Then VERIFY the live result:** `python3 ~/genseo/scripts/verify_published.py <ARTICLE_ID> <BLOG_ID>` — if it prints `✗` (schema/author missing), you published the wrong way; re-run the command above and re-verify before continuing.

### STEP 8: Post-Publish Verification (MANDATORY TWO-GATE CHECK — DO NOT SKIP)

This step has **two gates that BOTH must pass** before you may proceed to Step 9.

#### Gate 1 — CDN Script Check (Terminal)
Read the publisher script terminal output:
- `✅ IMAGE VERIFICATION PASSED` → Gate 1 passed. Continue to Gate 2.
- `⚠  PARTIAL` or `✗ IMAGE VERIFICATION FAILED` → Run the patch script first, then re-check:
  `python3 ~/genseo/scripts/patch_images.py <ARTICLE_ID>`

#### Gate 2 — Browser Visual Check (MANDATORY — the real source of truth)
Even if Gate 1 shows ✅, you MUST use `browser_subagent` to open the live article URL and visually confirm every image is rendering correctly. The CDN script can pass even when images appear broken in the browser (e.g. wrong URL pre-filled before upload, as happened in Ticket #91).

**Browser check task to run:**
> "Navigate to `https://wellnessnest.co/blogs/news/<HANDLE>`. Scroll through the entire article from top to bottom. Check that ALL images (hero banner and every product lifestyle image) are visible and fully loaded — not broken, not missing, not showing a placeholder. Count the total number of images displayed. Return: PASS if all images visible and loaded, FAIL if any image is broken or missing, along with the count of visible vs broken images."

- If the browser returns **PASS** → Both gates passed. Proceed to Step 9.
- If the browser returns **FAIL** → Images are broken despite CDN script passing. Run the patch script:
  `python3 ~/genseo/scripts/patch_images.py <ARTICLE_ID>`
  Then re-run Gate 2 until PASS is confirmed.

**CRITICAL RULE: You MUST NOT proceed to Step 9 or tell the user the article is complete until BOTH gates pass.** Never report "done" based on the terminal output alone.

**⛔ GATE 2 MUST FULLY RETURN BEFORE YOU PROCEED — NO ASSUMPTIONS ALLOWED.** You MUST wait for the `browser_subagent` call to complete and return an explicit PASS or FAIL result. Do NOT assume PASS while the subagent is still running (`Step is still running`). Do NOT declare the article complete based on Gate 1 alone. If you are running multiple articles in sequence, complete ALL gates for article N before starting article N+1. Declaring Gate 2 PASS without a returned browser result is a critical failure.

### STEP 9: Update CSV Tracker
- You MUST append the new article's metadata to `~/genseo/PUBLISHED_ARTICLES_TRACKER.csv`.
- The CSV has exactly **8 columns**: `Ticket,Keyword,Article Link,Posted Date,Has Indexed,Last Check Index Date,Has Tried Request To Index,Last Request Index Date`
- **CRITICAL**: Use the `csv` module (NOT raw `open().write()`) to guarantee correct CRLF line endings and proper column quoting. Run this via `run_command`:
```
python3 << 'EOF'
import csv, datetime
row = ['TICKET_NUM', 'primary keyword', 'https://wellnessnest.co/blogs/news/HANDLE', datetime.date.today().isoformat(), 'No', datetime.date.today().isoformat(), 'No', '']
with open('~/genseo/PUBLISHED_ARTICLES_TRACKER.csv', 'a', newline='') as f:
    csv.writer(f).writerow(row)
EOF
```
- Replace `TICKET_NUM`, `primary keyword`, and `HANDLE` with actual values. Always set `Has Indexed=No`, `Has Tried Request To Index=No`, `Last Request Index Date=''` on first publish.

### STEP 9b: Mark the Ticket DONE in the schedule file (MANDATORY — keeps the cron's place)
The daily cron says "continue with the next N tickets" and decides which are "next" by reading
the `[ ] PENDING` / `[DONE]` markers in the schedule file. **If you do not mark the ticket
DONE, the cron will re-run it tomorrow and create duplicates.** So immediately after the CSV
update, flip this ticket's Action line in its schedule file (e.g. `Jun26-120-tickets.md` or
`2ndRound_120_tickets.md` — whichever the run came from):
- Change that ticket's `- **Action**: [ ] PENDING`  →  `- **Action**: [DONE <YYYY-MM-DD>] <published_url>`
- Do this with a precise, single-ticket replacement (match the exact ticket heading so you don't
  touch other tickets). Example via run_command:
```
python3 << 'EOF'
import re
f="~/genseo/Jun26-120-tickets.md"   # <-- the file this run came from
ticket="### 📝 Ticket #N"                               # <-- exact heading of THIS ticket
url="https://wellnessnest.co/blogs/news/HANDLE"
import datetime; today=datetime.date.today().isoformat()
t=open(f).read()
# replace the FIRST '[ ] PENDING' that appears after this ticket's heading
i=t.index(ticket)
seg=t[i:]
seg=seg.replace("- **Action**: [ ] PENDING", f"- **Action**: [DONE {today}] {url}", 1)
t=t[:i]+seg
open(f,"w").write(t)
print("marked DONE:", ticket)
EOF
```
- If STEP 0 found a duplicate and you SKIPPED, instead mark it `[SKIPPED-DUPLICATE <date>] <existing_url>` so the cron also moves past it.
- After this, the next cron run will correctly pick the following still-`PENDING` ticket.

### STEP 10: Reporting & Refresh Flag
- Report the success of the sequence to the user. Present:
  - The final URL of the Shopify post
  - Image count verified (Gate 1 + Gate 2 results)
  - Brief summary of the semantic strategy (keywords targeted, SERP gaps filled, GEO signals used)
  - Meta description that was set
- **Refresh Flag:** Note the publish date. Flag this article for content refresh review in 90 days via the `genseo-refresh-planner` skill.

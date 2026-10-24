# Daily ticket queue — wellnessnest.co (batch 1, hand-written 2026-08-07)

Agent được lệnh *"continue with the next ticket in daily-tickets.md"* → lấy ticket
`[ ]` PENDING kế tiếp → chạy skill `genseo-auto-publish` đủ 10 STEP → tick `[DONE <date>] <url>`.

**Queue status (2026-10-16):** this file is not empty. Any "the queue is EMPTY" or "Refill needed" section dated 2026-08 is history from that day. Do not stop on it. Do not append a new refill note while a later heading still starts with an open checkbox (`- [ ]` or `## [ ]`). The run prompt's QUEUE POINTER names that first open heading.

## Quy tắc chung (đọc trước mỗi ticket)

0. **BLOG_ID cho MỌI ticket = `104008483131`** (blog duy nhất của store, handle `news`).

1. Mọi internal link phải trỏ tới URL đang LIVE. Link 404 sẽ bị gate chặn.
2. Không tạo bài mới cho keyword đã có bài — STEP 0 check trước, trùng thì refresh.
3. Byline lấy từ `/Users/kevinkreative/genseo/roster.json`. Roster rỗng = STOP, báo Kevin.
4. Publish bằng `scripts/shopify_publisher.py` (mặc định DRAFT — Kevin duyệt trong admin).
5. Ảnh: `scripts/article_images.py` (ima2 OAuth). **HARD RULE (Kevin 2026-08-07):** ảnh CÓ
   sản phẩm trong khung → bắt buộc `--product-ref <handle>` (tự tải pack shot thật từ
   `/products/<handle>.js` làm ref + khoá prompt theo bao bì). KHÔNG bịa bao bì — format
   (pouch/jar/bottle), màu, label phải đúng PDP; prompt phải TẢ đúng format thật; gen xong
   mở output so với ref rồi mới đưa vào draft. Hero = ảnh ĐẦU TIÊN trong body (publisher
   strip thành article.image).
6. Tồn kho coverage hiện có: MenoMate journey/meal-plan series · shilajit foundational
   (what-is / benefits / types / sourcing / lab-testing / Ayurveda / fulvic-skin) ·
   menopause (joint pain / gut / fasting / weight / hormones / rage) · dad-bod series.
   KHÔNG viết lại các góc đó.

---

## [DONE 2026-08-07 https://wellnessnest.co/blogs/news/creatine-gummies-vs-powder-which-should-you-actually-take] Ticket #1 — NEW ARTICLE

- **Status:** DRAFT trên Shopify (article id `621836861755`, chưa public — Kevin bấm publish trong
  admin: https://admin.shopify.com/store/wellnessnest1/content/articles/621836861755). Gate PASS,
  Gate 2 Admin-API PASS (3 inline <80KB + hero + 3 JSON-LD). Byline Dr. Marcus Hale.
- **Primary keyword:** `creatine gummies vs powder`
- **Secondary:** do creatine gummies work, creatine gummies absorption, 5000mg creatine gummies, creatine for beginners
- **Search intent:** comparison, buyer deciding a format
- **Collection links (≥2, verify live):** `/collections/womens-essentials-collection`, `/collections/best-seller`
- **Hero product:** `/products/fusiforce-creatine-gummies` ($69.99)
- **Comparison table:** gummies vs powder vs capsules — dose per serving, absorption, taste/GI, daily habit adherence, price per month
- **Angle:** the real question is adherence, not chemistry — creatine only works taken daily, and the format you actually stick with wins. Answer that in the answer block.
- **Author:** (from roster.json — Kevin approves)
- **Dedup note:** no existing creatine article on the blog (checked 2026-08-07)

## [DONE 2026-08-08 https://wellnessnest.co/blogs/news/creatine-for-women-over-40-what-changes-in-the-us] Ticket #2 — NEW ARTICLE

- **Primary keyword:** `creatine for women over 40`
- **Secondary:** creatine benefits for women, does creatine cause bloating in women, creatine menopause muscle loss
- **Search intent:** informational→buyer, women skeptical of a "gym bro" supplement
- **Collection links:** `/collections/womens-essentials-collection`, `/collections/best-seller`
- **Hero product:** `/products/fusiforce-creatine-gummies`
- **Comparison table:** what changes after 40 (muscle loss %, recovery, bone, brain fog) × how creatine addresses each, with citations
- **Angle:** muscle loss after 40 is measurable and creatine is one of the few supplements with real strength evidence in women — de-bro the narrative.
- **Author:** (from roster.json)
- **Dedup note:** menopause series exists but zero creatine coverage on the BLOG (checked 2026-08-07).
  ⚠ Store has an UNPUBLISHED page draft `/pages/9-surprising-things-creatine-may-do-for-women-beyond-building-muscle`
  (id 157057941819) — a page, not an article; read it before writing to avoid overlap, do not publish it.
- **Collection-claim note:** FusiForce is NOT in womens-essentials-collection (only FloraFresh + AgeAura are)
  — link the collection as a browse suggestion, never claim membership. Same trap caught in Ticket #1.

## [DONE 2026-08-09 https://wellnessnest.co/blogs/news/vaginal-probiotics-which-strains-actually-work-us-2026] Ticket #3 — NEW ARTICLE

- **Primary keyword:** `vaginal probiotics what strains work`
- **Template:** STORY (per references/article-templates.md)
- **Secondary:** probiotics for pH balance, lactobacillus for feminine health, probiotics for odor
- **Search intent:** problem-aware buyer comparing products
- **Collection links:** `/collections/womens-essentials-collection`, `/collections/best-seller`
- **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` ($40.99)
- **Comparison table:** strains (L. rhamnosus, L. reuteri, L. crispatus...) × what evidence supports each × oral vs suppository delivery
- **Angle:** most "women's probiotics" are gut blends with a pink label — strain specificity is the whole game. Educate, then show FloraFresh's strains.
- **Author:** (from roster.json)
- **Dedup note:** zero feminine-health articles on blog (checked 2026-08-07)

## [DONE 2026-08-09 https://wellnessnest.co/blogs/news/turkesterone-benefits-dosing-whats-real-us-2026] Ticket #4 — NEW ARTICLE

- **Primary keyword:** `turkesterone benefits and dosing`
- **Template:** EDITORIAL (per references/article-templates.md)
- **Secondary:** is turkesterone natty, turkesterone vs ecdysterone, turkesterone results timeline
- **Search intent:** buyer researching before purchase
- **Collection links:** `/collections/mens-essential-collection`, `/collections/best-seller`
- **Hero product:** `/products/turkesterone-advanced-formula` ($75.00)
- **Comparison table:** turkesterone vs ecdysterone vs tribulus — mechanism, evidence level, who it suits
- **Angle:** separate the TikTok hype from what's actually known; honest evidence framing builds more trust (and conversions) than overclaiming.
- **Author:** (from roster.json)
- **Dedup note:** no turkesterone article exists (checked 2026-08-07)

## [DONE 2026-08-09 https://wellnessnest.co/blogs/news/nmn-and-tmg-together-why-the-pairing-matters-us-2026] Ticket #5 — NEW ARTICLE

- **Primary keyword:** `nmn and tmg together`
- **Template:** COMPARISON (per references/article-templates.md)
- **Secondary:** why take tmg with nmn, nmn methylation depletion, nmn tmg dosage ratio
- **Search intent:** informed longevity buyer (knows NMN, asking why TMG)
- **Collection links:** `/collections/ageaura`, `/collections/best-seller`
- **Hero product:** `/products/ageaura-pure-nmn-tmg-nad-complex` ($69.95)
- **Comparison table:** NMN alone vs NMN+TMG — NAD+ pathway step, methyl-group cost, what TMG restores
- **Angle:** LEAD WITH NMN (largest-dose ingredient — hard rule), TMG is the supporting actor that keeps methylation from being drained. Never lead with a minor ingredient.
- **Author:** (from roster.json)
- **Dedup note:** zero NMN/longevity articles on the blog (checked 2026-08-07)

## [DONE 2026-08-09 https://wellnessnest.co/blogs/news/urolithin-a-benefits-the-40-problem-us-buyers-miss] Ticket #6 — NEW ARTICLE

- **Primary keyword:** `urolithin a benefits`
- **Template:** STORY (per references/article-templates.md)
- **Secondary:** urolithin a vs nmn, mitophagy supplement, urolithin a muscle aging, pomegranate urolithin
- **Search intent:** informed longevity buyer comparing next-gen compounds
- **Collection links:** `/collections/ageaura`, `/collections/best-seller`
- **Hero product:** `/products/ageaura-pure-urolithin-a` ($199.99 — live URL, unlisted in nav)
- **Comparison table:** Urolithin A vs NMN+TMG — pathway (mitophagy vs NAD+), evidence, who should start where
- **Angle:** "cellular cleanup" (mitophagy) is the clearest mechanism story in longevity — explain it plainly, position vs the NAD+ pipeline, funnel to both AgeAura SKUs.
- **Author:** (from roster.json)
- **Dedup note:** zero urolithin/longevity articles on blog; topic_fitness PASS [brand] (checked 2026-08-07)

## [DONE 2026-08-09 https://wellnessnest.co/blogs/news/shilajit-energy-drops-7-ways-to-use-them-in-the-us] Ticket #7 — NEW ARTICLE

- **Primary keyword:** `shilajit energy drops how to use`
- **Template:** LISTICLE (per references/article-templates.md)
- **Secondary:** liquid shilajit vs resin, shilajit drops in coffee, fastest way to take shilajit
- **Search intent:** format-curious buyer (already sold on shilajit)
- **Collection links:** `/collections/shilajit-wellness-stack`, `/collections/mens-essential-collection`
- **Hero product:** `/products/shilajit-shockwave` ($79.99)
- **Comparison table:** drops vs resin vs gummies — onset, portability, dosing, who each suits
- **Angle:** the "Types of Shilajit Products" foundational exists — do NOT rewrite it. This is a practical how-to-use piece for the drops format, linking back to that guide.
- **Author:** (from roster.json)
- **Dedup note:** types-comparison exists (link it); no how-to-use-drops article (checked 2026-08-07)

---

# Batch 2 — mined from Google Ads search terms (2026-08-07)

Source: account `7385813335` (WellnessNest), `search_term_view`, window `2026-05-09 → 2026-08-07`
via Google Ads MCP. Method + refill recipe: `skills/genseo-auto-publish/references/ads-article-mining.md`.
Campaign names below are **verbatim live `campaign.name`** (hard rule — never paraphrase them).
Context that framed this batch: paid conversions concentrate in DE branded shilajit Shopping;
the US non-brand campaign spends with **zero** conversions — those exact terms are the organic
lane's job. Blog stays English/US-anchored (gate enforces); a DE-language content lane is a
separate Kevin decision, NOT covered by these tickets.

## [DONE 2026-08-09 https://wellnessnest.co/blogs/news/best-shilajit-gummies-6-us-labels-compared-2026] Ticket #8 — NEW ARTICLE (type: PPC-arbitrage + competitor comparison)

- **Primary keyword:** `best shilajit gummies`
- **Template:** LISTICLE (per references/article-templates.md)
- **Secondary:** shilajit gummies for men, himalayan shilajit gummies, shilajit gummies vs resin, aphroly shilajit gummies, gold shilajit gummies
- **Ads evidence (90d):** campaign `US · Shilajit · Category` — "shilajit gummies" 19 clicks · $88.05 · 0 conv; "himalayan shilajit gummies" 4 clicks · $7.59; "shilajit gummies for men" 1 click · $2.63. Competitor-brand searches in the same lane: "aphroly shilajit gummies" (campaign `[S] Search - SLG - Slovakia  - 2303`), "erth wellness gummies", "better alt shilajit", "gold shilajit gummies", "optimum shilajit" (all `US · Shilajit · Category`). English "best shilajit" also paid-clicked in `[S] Shopping DE - 2003` ($1.89).
- **Search intent:** buyer comparing gummy brands — the exact click we currently pay $3–4.6 for with zero paid conversions
- **Collection links:** `/collections/shilajit-wellness-stack`, `/collections/best-seller`
- **Hero product:** `/products/premium-himalayan-shilajit-gummies` ($59.99)
- **Comparison table:** Wellness Nest Premium Himalayan Gummies vs named competitor gummies (Aphroly, Erth Wellness, Better Alt) — shilajit amount per serving, fulvic acid disclosure, servings per pouch, price per serving. ⚠ Competitor specs MUST be read off their live product pages at write time — never invent a competitor number; if a spec isn't published, write "not disclosed" (that itself sells).
- **Angle:** most gummy brands hide the actual shilajit dose behind proprietary blends — teach the reader to read the panel, then let the comparison table do the selling.
- **Author:** (from roster.json)
- **Dedup note:** types-of-shilajit-products article compares FORMATS — link it, don't rewrite; no brand-comparison / best-gummies article exists (blog list checked 2026-08-07)

## [DONE 2026-08-09] Ticket #9 — NEW ARTICLE (type: authority-figure search capture)

- **Primary keyword:** `barbara o neill shilajit`
- **Template:** EDITORIAL (per references/article-templates.md)
- **Secondary:** barbara o'neill shilajit benefits, what does barbara o'neill say about shilajit, barbara o'neill minerals
- **Ads evidence (90d):** campaign `ADC | Shopping | DE | Branded | Shilajit Essential Extract |  LP | TROAS 250%` — "barbara o neill shilajit" 17 clicks · ≈$52 · **1 conv**; plus "shilajit barbara o neill" (≈$30) and "barbara o neill shilajit kaufen" (≈$20). People search her name + shilajit and it converts — an article owns that SERP for free.
- **Search intent:** followers of a health educator checking her take before buying
- **Collection links:** `/collections/shilajit-wellness-stack`, `/collections/best-seller`
- **Hero product:** `/products/shilasource-himalayan-shilajit-resin` ($59.99 — resin is the form she discusses); link gummies inline as the modern format
- **Comparison table:** what Barbara O'Neill teaches about shilajit × what published research says × what to check on a label
- **Angle:** researcher's review of her public teachings — where the science agrees, where it's thinner than she implies, and how to pick a product that holds up either way. **Accuracy guard: she has NO affiliation with Wellness Nest — never imply endorsement; that is a fabricated fact, same class as invented clinical numbers.**
- **Author:** (from roster.json)
- **Dedup note:** no authority/influencer article exists (blog list checked 2026-08-07)

## [DONE 2026-08-09 https://wellnessnest.co/blogs/news/shilajit-benefits-for-men-4-claims-ranked-us-2026] Ticket #10 — NEW ARTICLE (type: audience-segment deep-dive)

- **Primary keyword:** `shilajit benefits for men`
- **Template:** STORY (per references/article-templates.md)
- **Secondary:** shilajit testosterone, shilajit gummies for men, shilajit energy and recovery, how to increase testosterone naturally
- **Ads evidence (90d):** campaign `US · Shilajit · Category` — "shilajit benefits for men" 1 click · $1.44; "shilajit gummies for men" 1 click · $2.63; "shilajit benefits" 2 clicks · $2.69. Campaign `[S] Shopping DE - 2003` — "how to increase testosterone" 1 click · $2.07 (a Shopping ad is the wrong answer to that query; an article is the right one).
- **Search intent:** men researching testosterone/energy angle before buying
- **Collection links:** `/collections/mens-essential-collection`, `/collections/shilajit-wellness-stack`
- **Hero product:** `/products/shilasource-himalayan-shilajit-resin` ($59.99); gummies inline
- **Comparison table:** the men-specific evidence map — testosterone, energy/mitochondria, recovery, fertility — study type & strength per claim, with citations
- **Angle:** the general benefits article exists and stays general — this one answers the male buyer directly. Honest evidence grading (which claims have RCTs vs tradition) converts better than hype for this reader.
- **Author:** (from roster.json)
- **Dedup note:** general benefits + what-is articles exist — LINK both, do not restate general benefits; no men-specific article (blog list checked 2026-08-07)

## [DONE 2026-08-10 https://wellnessnest.co/blogs/news/wellness-nest-shilajit-reviews-what-85-buyers-report] Ticket #11 — NEW ARTICLE (type: review-intent / brand-SERP defense)

- **Primary keyword:** `wellness nest shilajit reviews`
- **Template:** EDITORIAL (per references/article-templates.md)
- **Secondary:** wellness nest shilajit results, shilajit before and after, is wellness nest legit
- **Ads evidence (90d):** campaign `ADC | Shopping | DE | Branded | Shilajit Essential Extract |  LP | TROAS 250%` — "wellness nest shilajit erfahrungen" (brand-review intent, converting lane); campaign `[S] Search - SLG - Slovakia  - 2303` — "shilajit gummies recenzie"; campaign `[S] Shopping DE - 2003` — "bestes shilajit testsieger" family (test-winner intent, 41+8 impr). Review-intent queries exist in every geo; today no owned page answers them.
- **Search intent:** near-buyer looking for social proof / verification
- **Collection links:** `/collections/shilajit-wellness-stack`, `/collections/best-seller`
- **Hero product:** `/products/premium-himalayan-shilajit-gummies` ($59.99); resin inline
- **Comparison table:** what customers report by theme (energy, recovery, taste/ritual, time-to-notice) × representative quotes
- **Angle:** aggregate REAL customer reviews from the store's review widget into a themed results roundup. **Accuracy guard: only quote reviews that actually exist on the store — never invent or embellish a review. Do NOT lead on lab-tested/COA as the advantage (house rule) — customer outcomes are the story.**
- **Author:** (from roster.json)
- **Dedup note:** no reviews/results article exists (blog list checked 2026-08-07)

## [x] Ticket #12 — NEW ARTICLE (type: retail-availability / where-to-buy) — LOWEST priority, run last
<!-- DONE 2026-08-13 — LIVE id 621858095419
     https://wellnessnest.co/blogs/news/where-to-buy-wellness-nest-shilajit-in-the-us-2026 -->
<!-- This was the last open ticket. The queue is now EMPTY: brand-coverage as a topic source is
     exhausted (2 vendors, both covered), so the next batch needs a real query-gap input — either
     GSC (no OAuth client on this machine; scripts/credentials.json and gsc_token.json are absent)
     or a Google Ads search-terms export. -->


- **Primary keyword:** `where to buy wellness nest shilajit`
- **Template:** EDITORIAL (per references/article-templates.md)
- **Secondary:** wellness nest shilajit amazon, is shilajit sold in stores, how to spot fake shilajit
- **Ads evidence (90d):** campaign `ADC | Shopping | DE | Branded | Shilajit Essential Extract |  LP | TROAS 250%` — "wellness nest shilajit dm" (drugstore-chain query), "shilajit von wellness nest amazon", "wellness nest shilajit kaufen" family; campaign `[S] Shopping DE - 2003` — "shilajit bestellen". Buyers ask where to purchase; the answer should be an owned page, not a reseller.
- **Search intent:** brand-navigational, checking channels & authenticity
- **Collection links:** `/collections/shilajit-wellness-stack`, `/collections/best-seller`
- **Hero product:** `/products/shilasource-himalayan-shilajit-resin` ($59.99); gummies + gold resin (`/products/pure-shilajit-gold-resin`, $75.00) inline
- **Comparison table:** buying direct vs marketplaces vs retail — authenticity guarantee, freshness/lot control, pricing, support & returns
- **Angle:** direct-from-Wellness-Nest is the only channel with guaranteed authentic product — plus a practical fake-shilajit spotting checklist (ties to the sourcing article).
- **Author:** (from roster.json)
- **Dedup note:** sourcing + lab-testing articles exist — link them; no where-to-buy article (blog list checked 2026-08-07)

## [DONE 2026-08-10 https://wellnessnest.co/blogs/news/how-to-choose-shilajit-gummies-7-checks-us-2026] Ticket #13 — NEW ARTICLE (type: LISTICLE — organic presell format)

- **Format:** LISTICLE — numbered points, each = ONE pain/benefit tied to the mechanism, skimmable,
  soft CTA. Craft: `~/PATI/LLM-Wiki/30-creative/32-copy/7-advertorial-listicle-presell-framework.md`
  (vault doctrine: listicle fits COLD readers with generic angle = blog search traffic). Still passes
  every gate — ≥900 words, US anchor, 3 inline images, ≥2 collection links.
- **Primary keyword:** `how to choose shilajit gummies` (working title: "7 Things to Check Before You Buy Shilajit Gummies")
- **Secondary:** shilajit gummies ingredients, fulvic acid content, third party tested shilajit, shilajit gummies dosage per serving
- **Ads evidence (90d):** quality/criteria-hunting visible across campaigns — `US · Shilajit · Category`: "gold shilajit gummies", "better alt shilajit", "erth wellness gummies", "optimum shilajit" (buyers comparing quality across brands); `[S] Shopping DE - 2003` + `ADC | Shopping | DE | Branded | Shilajit Essential Extract |  LP | TROAS 250%`: "shilajit beste qualität", "bestes shilajit testsieger" family. Criteria-education captures ALL of these without naming a single brand in the keyword.
- **Search intent:** cold buyer who doesn't yet know how to judge a gummy — teach the checklist, let the criteria sell
- **Collection links:** `/collections/shilajit-wellness-stack`, `/collections/best-seller`
- **Hero product:** `/products/premium-himalayan-shilajit-gummies` ($59.99)
- **Angle:** each numbered point = one criterion (actual shilajit mg per serving · fulvic acid disclosure · source transparency · servings math · sugar load · gummy-vs-resin equivalence · return policy). Product appears as the worked example of each criterion, never as a hard pitch.
- **Author:** (from roster.json)
- **Dedup note:** distinct from #8 (brand-comparison table) — this is criteria education; cross-link #8's article once live. No how-to-choose article exists (blog list checked 2026-08-07)

## [DONE 2026-08-11 https://wellnessnest.co/blogs/news/fake-shilajit-6-signs-yours-isnt-real-us-2026] Ticket #14 — NEW ARTICLE (type: LISTICLE — organic presell format)

- **Format:** LISTICLE — same craft source + gates as #13.
- **Primary keyword:** `fake shilajit` (working title: "6 Signs Your Shilajit Is Fake — and How to Verify the Real Thing")
- **Secondary:** real shilajit vs fake, how to test shilajit at home, authentic himalayan shilajit, shilajit purity test
- **Ads evidence (90d):** authenticity anxiety runs through the paid terms — "natural himalayan shilajit" (`US · Shilajit · Category`), "optimum shilajit", the DE testsieger/qualität family, and the #12 where-to-buy cluster ("wellness nest shilajit dm/amazon" = people checking channels because they fear fakes). Nobody owns this SERP with an owned page yet.
- **Search intent:** worried buyer pre-purchase OR post-purchase verification — both funnel to a trusted source
- **Collection links:** `/collections/shilajit-wellness-stack`, `/collections/mens-essential-collection`
- **Hero product:** `/products/shilasource-himalayan-shilajit-resin` ($59.99); gummies inline
- **Angle:** 6 verifiable signs (solubility & residue · burn test myth debunk · price-too-good math · label red flags · origin claims without lot traceability · texture/smell). Link the existing sourcing + lab-testing articles as depth. ⚠ House rule: do NOT lead on lab-tested/COA as THE advantage — sourcing transparency + reader empowerment is the story.
- **Author:** (from roster.json)
- **Dedup note:** sourcing + lab-testing articles exist — LINK, don't restate; no fake-spotting article (blog list checked 2026-08-07)

---

# BATCH 2026-08-13 — tickets #15–#22 (built WITHOUT GSC)

Kevin: *"I approve all of them, I need published articles without any delay."* The queue was empty
and GSC is still unauthorised, so this batch was sourced from what is available at $0: the live
product catalog (11 SKUs), the full 62-article blog inventory, and the `topic_fitness.py` gate.

**Why these eight and not others.** `topic_fitness.py` was returning `FAIL [covered]` on almost
every shilajit/creatine/turkesterone angle, which is what made the topic well look dry. Root cause
found and fixed today: `seg_taken` was **brand-blind** — it asked "does ANY live title contain this
segment modifier?", so *"Creatine for Women Over 40"* vetoed *"Shilajit for Women"*, and
*"Creatine Gummies vs Powder"* vetoed every `vs` comparison on the blog. Scoping the check to
articles that actually mention the brand restores the audience and comparison long-tail without
weakening the anti-cannibalisation guarantee (the page that would compete is by definition a page
about the same brand). All eight below now return `REVIEW [covered-segment]`, and Kevin's message
is the ticket-brief greenlight that verdict asks for.

**One article per brand+segment pair — do not add a second.** The moment a `vs` shilajit article
is live, `seg_taken` flips and every other shilajit `vs` topic correctly goes back to FAIL. That is
the guard working, not a regression.

All eight verified 0 matches on `suggest.json` at 2026-08-13.

| # | Title | Brand · segment | Products |
|---|---|---|---|
| ~~15~~ ✅ | [Shilajit Side Effects: 7 Signs to Watch For (US 2026)](https://wellnessnest.co/blogs/news/shilajit-side-effects-7-signs-to-watch-for-us-2026) — LIVE 2026-08-13, id 621858226491, LISTICLE, seq=19 all-no-face | shilajit · side effects | resin + gummies |
| ~~16~~ ✅ | [Shilajit Resin vs Gummies: Which Works Better? (US 2026)](https://wellnessnest.co/blogs/news/shilajit-resin-vs-gummies-which-works-better-us-2026) — LIVE 2026-08-13, id 621858259259, COMPARISON, seq=20 hero m3039-as-01 | shilajit · vs | resin + gummies |
| ~~17~~ ✅ | [Creatine Gummies Dosage: How Many a Day? (US 2026)](https://wellnessnest.co/blogs/news/creatine-gummies-dosage-how-many-a-day-us-2026) — LIVE 2026-08-13, id 621858292027, EDITORIAL, seq=21 hero m3039-as-02 | creatine gummies · dosage | FusiForce |
| ~~18~~ ✅ | [Shilajit for Women: What Changes After 45 (US 2026)](https://wellnessnest.co/blogs/news/shilajit-for-women-what-changes-after-45-us-2026) — LIVE 2026-08-13, id 621858488635, STORY, seq=22 hero NO-FACE | shilajit · for women | resin + gummies |
| ~~19~~ ✅ | [Turkesterone vs Ecdysterone: Which Is Worth It? (US 2026)](https://wellnessnest.co/blogs/news/turkesterone-vs-ecdysterone-which-is-worth-it-us-2026) — LIVE 2026-08-13, id 621858586939, COMPARISON, seq=23 hero m2029-as-01 | turkesterone · vs | Turkesterone Advanced |
| ~~20~~ ✅ | [When to Take NMN: Morning or Night? (US 2026)](https://wellnessnest.co/blogs/news/when-to-take-nmn-morning-or-night-us-2026) — LIVE 2026-08-13, id 621858619707, EDITORIAL, seq=24 hero f5059-wh-02 | nmn · morning or night | AgeAura NMN+TMG |
| ~~21~~ ✅ | [Vaginal Probiotics: How Long Until They Work? (US 2026)](https://wellnessnest.co/blogs/news/vaginal-probiotics-how-long-until-they-work-us-2026) — LIVE 2026-08-13, id 621858685243, STORY, seq=25 hero NO-FACE | vaginal probiotic · how long | FloraFresh |
| ~~22~~ ✅ | [How Much Shilajit Per Day: Dosage by Form (US 2026)](https://wellnessnest.co/blogs/news/how-much-shilajit-per-day-dosage-by-form-us-2026) — LIVE 2026-08-13, id 621859406139, EDITORIAL, seq=27 hero m3039-bl-04 | shilajit · how much | resin + gummies + gold |

Template rotation: previous three were LISTICLE, LISTICLE, EDITORIAL. Alternate across the batch.

**Uncovered SKU still with no page of its own:** `pure-shilajit-gold-resin` ($75) and
`shilajit-shockwave` ($79.99) — the gold resin FAILs the gate as `covered` because "shilajit" is
its only brand token; it needs a distinct segment angle, not a bare product page.

## Refill needed

**Not the current queue.** The empty-queue note under this heading is history from 2026-08-13. Later open checkboxes in this file are real tickets. Do not stop here, and do not append another refill note, while one of those headings is still open.

**2026-08-13 — the queue is EMPTY.** Ticket #22 was the last open item in batch 2026-08-13
(#15–#22 all shipped). The google-ads MCP is not connected in this environment, so the
mining recipe in `skills/genseo-auto-publish/references/ads-article-mining.md` cannot be run
from a headless session. **Kevin: run the mining recipe in the app** (paid-but-not-converting
terms + converting query patterns) and append the next batch here as `# BATCH <date>`.

Still-uncovered SKUs needing a distinct segment angle, not a bare product page:
`pure-shilajit-gold-resin` ($75) · `shilajit-shockwave` ($79.99). Note that #22 now publicly
flags that the gold-resin PDP publishes no serving size — fixing that page is worth more than
an article about it.

---

## Shipped without a ticket

- **[DONE 2026-08-13] #23 — turkesterone timing** — mined on the day because the queue was
  empty. Coverage map across the 11 live SKUs put turkesterone as the thinnest cluster with a
  stocked $75 product: two existing articles (vs-ecdysterone, benefits-dosing), neither about
  when to take it. `topic_fitness.py` → `PASS [brand]`; live suggest.json clean on
  "turkesterone timing", "when to take turkesterone", "turkesterone with food".
  → https://wellnessnest.co/blogs/news/turkesterone-timing-food-protein-or-fasted-us-2026

Remaining uncovered after #23: `pure-shilajit-gold-resin` · `shilajit-shockwave` (both still
need a segment angle, not a bare product page).

# BATCH 2026-08-14

- [DONE 2026-08-14 https://wellnessnest.co/blogs/news/shilajit-gold-resin-review-is-75-worth-it-us-2026] **#24 — shilajit gold resin review** — `Shilajit Gold Resin Review: Worth $75? (US 2026)`
  - Product: `pure-shilajit-gold-resin` · $75 live price · EDITORIAL.
  - Intent: near-buyer audit of the documented $15 premium. Disclose the missing serving size and Supplement Facts panel. Do not repeat unsupported potency, gold, testing, or outcome claims.
  - Gates: live `suggest.json` returned no article match; `topic_fitness.py` → `PASS [brand_intent]`.

## Refill needed

**Not the current queue.** The empty-queue note under this heading is history from 2026-08-14. Later open checkboxes in this file are real tickets. Do not stop here, and do not append another refill note, while one of those headings is still open.

**2026-08-14 — the queue is EMPTY again.** #24 was the only item in this batch and it shipped;
every heading above is `[DONE]` (#12 included, DONE 2026-08-13 in its HTML comment). No `[ ]`
ticket remains, so this run published nothing by design.

The google-ads MCP is **not connected in this headless session** (no google-ads tool is exposed —
only web search / fetch), so the mining recipe in
`skills/genseo-auto-publish/references/ads-article-mining.md` cannot be run from here.
**Kevin: run that recipe in the app** (paid-but-not-converting terms + converting query patterns)
and append the next batch below as `# BATCH <date>`.

$0 fallback if you want tickets without touching Ads: `scripts/build_catalog_tickets.py` /
`build_ctr_tickets.py` / `refresh_targets.py` / `build_rich_tickets.py` (batch 2026-08-13 was
sourced this way). Not run here — refilling the queue is your call, not this run's.

Uncovered SKU carried forward from 2026-08-13: `shilajit-shockwave` ($79.99) — still needs a
distinct segment angle, not a bare product page. `pure-shilajit-gold-resin` is now covered by #24.

# BATCH 2026-08-15

- [DONE 2026-08-15 https://wellnessnest.co/blogs/news/how-much-nmn-per-day-what-trials-used-us-2026] **#25 — how much nmn per day** — `How Much NMN Per Day: What Trials Used (US 2026)`
  - **Primary keyword:** `how much nmn per day` · **Secondary:** nmn dosage, nmn dose per day, how many mg of nmn, nmn 500mg
  - **Template:** COMPARISON (dose ladder judged tier against tier; previous #24 was EDITORIAL so the variety guard is satisfied).
  - **Products:** `ageaura-pure-nmn-tmg-nad-complex` ($69.95) · `ageaura-pure-nmn-tmg-the-essential-longevity-duo` ($59.95). Collections: `/collections/ageaura`, `/collections/best-seller`.
  - **Intent:** informed buyer who already knows what NMN is and wants the number. The two live NMN
    articles cover the TMG pairing (#5) and timing (#20); neither states a dose.
  - **Angle:** answer from the trials, not from marketing. Every human trial that measured an outcome
    sat between 250 and 900 mg/day; the largest dose-ranging trial found blood NAD+ rose with dose
    while efficacy flattened near the middle of that range. Then do the label math on our own listing.
  - **Disclose (house honesty pattern, same as #22/#24):** only ONE of the four AgeAura NMN listings
    publishes a milligram amount at all (200 mg NMN + 100 mg TMG per capsule); the other three say
    only "one capsule daily". None publishes a Supplement Facts panel or a servings-per-container
    count on the PDP. Do NOT repeat the PDP's "third-party tested" line — no COA is published
    (house rule `no-coa-competitive-advantage`).
  - **Evidence spine (all DOIs verified live against api.crossref.org this run; NCBI is IP-blocked
    from this Mac so nothing was taken from PubMed directly):**
    Okabe 2022 Front Nutr 10.3389/fnut.2022.868640 (250 mg/d, 12 wk, n=30) ·
    Katayoshi 2023 Sci Rep 10.1038/s41598-023-29787-3 (125 mg x2 = 250 mg/d, 12 wk, n=36 middle-aged) ·
    Yoshino 2021 Science 10.1126/science.abe9985 (250 mg/d, 10 wk, postmenopausal prediabetic women) ·
    Yi 2022 GeroScience 10.1007/s11357-022-00705-1 (300/600/900 mg/d, 60 d, n=80) ·
    Fukamizu 2022 Sci Rep 10.1038/s41598-022-18272-y (1250 mg/d, 4 wk, n=31).
  - **Gates:** STEP 0 live `suggest.json` = 0 article matches across 7 query variants
    (how much nmn per day / nmn dosage / nmn dose / how much nmn / nmn how many mg / nmn 500mg /
    nmn per day); positive control on "nmn" correctly returned #20 and #5.
    `topic_fitness.py` -> `REVIEW [covered-segment]` (brand nmn covered, "dosage" segment open) —
    proceeding under Kevin's standing greenlight for this mined queue (2026-08-13).
  - **Mined because the queue was empty** (DAILY-RUN section 2). GSC unauthorised and the google-ads
    MCP is absent headless, so this came from the live catalog + the live blog inventory at $0.

## Refill needed

**Not the current queue.** The empty-queue note under this heading is history from 2026-08-15. Later open checkboxes in this file are real tickets. Do not stop here, and do not append another refill note, while one of those headings is still open.

**2026-08-15 — the queue is EMPTY again.** #25 was mined on the day (the queue was empty at 07:30)
and shipped, so nothing is left open. GSC is still unauthorised on this Mac and no google-ads tool
is exposed to a headless run, so the mining recipe in
`skills/genseo-auto-publish/references/ads-article-mining.md` still cannot run from here.
**Kevin: run that recipe in the app** and append the next batch below as `# BATCH <date>`.

$0 fallback that produced both this batch and 2026-08-13's: read the live catalog + the live blog
inventory, list the brand+segment pairs no title covers, gate each through `topic_fitness.py`, then
STEP 0 each survivor against `suggest.json`.

Segments still open after #25 (all gate to `REVIEW [covered-segment]`, none checked against
suggest.json yet — do that before writing):
`creatine gummies` + side effects · `vaginal probiotic` + side effects · `nmn` + side effects ·
`shilajit` + drops-vs-resin (note the older "Types of Shilajit Products" article already compares
drops and resin, so this one needs a genuinely narrower angle or it cannibalises).

Uncovered SKU carried forward from 2026-08-13 and 2026-08-14: `shilajit-shockwave` ($79.99) — still
needs a distinct segment angle, not a bare product page. Ticket #7 (energy drops, 7 ways to use
them) is the closest existing coverage, so a second generic drops article would cannibalise it.

**2026-08-15 (second run of the day) — queue still EMPTY, nothing published by design.** This run
was told to take the first `[ ]` heading; there is none (the only two `[ ]` strings left in this
file are the instruction line 4 and the prose on line 319). The run stopped without writing an
article rather than mining a second topic on the same day, because a same-day second article on the
remaining open segments would land next to #25 while it is still being indexed.
The google-ads MCP is **still not exposed to this headless session** (available MCP tools this run:
web search / web fetch only; the Shopify MCP is present but unauthenticated, and it is barred by
hard rule #2 anyway). **Kevin: run the mining recipe in the app**
(`skills/genseo-auto-publish/references/ads-article-mining.md` — paid-but-not-converting terms +
converting query patterns) and append the next batch below as `# BATCH <date>`.
The open segments and the uncovered `shilajit-shockwave` SKU listed directly above are unchanged and
are the shortest path to a $0 refill if you would rather not touch Ads.

**2026-08-15 (third run of the day) — queue still EMPTY, nothing published by design.** No `[ ]`
heading exists; the queue has now been empty for three consecutive runs. The google-ads MCP is
**still not exposed to this headless session** (MCP tools present this run: web search / web fetch;
the Shopify and claude.ai servers are listed but unauthenticated, and Shopify MCP is barred by hard
rule #2 regardless). **Kevin: run the mining recipe in the app**
(`skills/genseo-auto-publish/references/ads-article-mining.md`) and append the next batch as
`# BATCH <date>`. Nothing above this line changed — the open segments and `shilajit-shockwave`
remain the $0 refill path.


# BATCH 2026-10-06 (MacBook failover lane — ticket ids prefixed MB so they can never collide with the Mini's #NN queue)

Mined by Grok Bot on the MacBook at $0 while the Mac Mini was unreachable (its queue + persona state
since 2026-08-15 live only on the Mini, unpushed). Source: live catalog (products.json) + live blog
inventory (sitemap_blogs_1.xml, 88 handles incl. the 5 Oct-5 posts) + `topic_fitness.py` + STEP 0
`suggest.json` (0 article matches for every primary/secondary query, checked 2026-10-06 ~10:00 ICT).
Kevin's standing greenlight for mined queues (2026-08-13) + 5/day GO cover the REVIEW verdicts.

**MacBook-lane rules for this batch (read before every ticket):**
- **ALL images NO-FACE** (hero = real pack in a real scene, `--product-ref` + `--qc`, no `--persona-ref`; inline =
  hands/POV/flat-lay/scene). Reason: `personas/index.json` on this Mac is stale vs the Mini (angles spent
  Aug 16–Oct 5 are unknown here), so any persona pick risks re-spending an angle — Kevin's hard rule. Do NOT run
  `persona_picker.py pick` in this batch. QC must FAIL any image with a recognizable human face.
- **AgeAura = NMN + TMG only.** Never mention, link or picture Urolithin A. Link ONLY `/products/ageaura-pure-nmn-tmg-nad-complex` — never `ageaura-pure-nmn-tmg-p2`, the Essential Longevity Duo or `/collections/ageaura` (use `/collections/best-seller`). Enforced by `lint_tickets.py` + `validate_article.py`.
- **Fact-check log (Google: manual fact-checking of AI content is "critical", SEL 2026-10-06):** before publish,
  write `~/genseo/logs/claims/<slug>.md` — one row per factual claim (number, study, mechanism, dose): claim ·
  source URL · fetched & confirmed (Y/N). Any claim not confirmed from a fetched source is deleted from the draft.
- Byline: roster.json only. Blog id 104008483131. Publish `--live`.

- [DONE 2026-10-06 https://wellnessnest.co/blogs/news/probiotics-after-antibiotics-for-women-when-to-start-us] **#MB1006-1 — vaginal probiotics after antibiotics** — `Vaginal Probiotics After Antibiotics: When to Start (US 2026)`
  - **Primary keyword:** `probiotics after antibiotics for women` · **Secondary:** vaginal probiotics after antibiotics, when to take probiotics after antibiotics, yeast infection after antibiotics, how long after antibiotics to take probiotics
  - **Template:** EDITORIAL · **Gate:** topic_fitness PASS [brand]
  - **Products:** `/products/florafresh-vaginal-probiotics-gummies` ($40.99). Collections: `/collections/womens-essentials-collection`, `/collections/best-seller`.
  - **Angle:** timing (spacing the dose from the antibiotic, continuing after the course), what the evidence does and does not show for preventing post-antibiotic yeast/BV, when to call a clinician. Link existing: yeast-infection-vs-bv, vaginal-probiotics-how-long-until-they-work, probiotics-for-bv. No drug/cure claims (FDA structure/function only).

- [DONE 2026-10-06 https://wellnessnest.co/blogs/news/how-to-take-shilajit-resin-dissolve-it-right-us-2026] **#MB1006-2 — how to take shilajit resin** — `How to Take Shilajit Resin: Dissolve It Right (US 2026)`
  - **Primary keyword:** `how to take shilajit resin` · **Secondary:** how to dissolve shilajit resin, shilajit resin in warm water, pea size shilajit, shilajit resin under tongue
  - **Template:** LISTICLE (step-by-step) · **Gate:** topic_fitness REVIEW [covered-segment] → greenlit (no "how to take" title exists)
  - **Products:** `/products/shilasource-himalayan-shilajit-resin` ($59.99) hero; `/products/pure-shilajit-gold-resin` ($75) inline. Collections: `/collections/shilajit-wellness-stack`, `/collections/mens-essential-collection`.
  - **Angle:** the practical method (tool/scoop, pea-size portion, water temperature, stirring, taste fixes, storage). LINK — do not restate — how-much-shilajit-per-day (dose) and when-to-take-shilajit (timing). Don't lead on lab-tested/COA as the advantage.

- [DONE 2026-10-06 https://wellnessnest.co/blogs/news/creatine-gummies-loading-phase-is-it-needed-us-2026] **#MB1006-3 — creatine gummies loading phase** — `Creatine Gummies Loading Phase: Is It Needed? (US 2026)`
  - **Primary keyword:** `creatine loading phase gummies` · **Secondary:** do you need to load creatine, creatine loading phase, how many creatine gummies to load, creatine saturation
  - **Template:** STORY · **Gate:** topic_fitness PASS [brand]
  - **Products:** `/products/fusiforce-creatine-gummies` ($69.99). Collections: `/collections/mens-essential-collection`, `/collections/best-seller`.
  - **Angle:** loading (≈20 g/day × 5–7 days) vs steady 3–5 g/day reach the same muscle saturation, just later — cite the classic Hultman 1996 J Appl Physiol data only if fetched/confirmed. What loading means in gummy count (and why most buyers should not). LINK creatine-gummies-dosage + how-long-does-creatine-take-to-work, don't restate.

- [DONE 2026-10-06 https://wellnessnest.co/blogs/news/nmn-capsules-vs-powder-vs-sublingual-best-form-us-2026] **#MB1006-4 — nmn capsules vs powder vs sublingual** — `NMN Capsules vs Powder vs Sublingual: Which Format? (US 2026)`
  - **Primary keyword:** `nmn capsules vs powder` · **Secondary:** sublingual nmn, nmn powder vs capsules, best form of nmn, nmn absorption
  - **Template:** COMPARISON · **Gate:** topic_fitness PASS [brand_intent]
  - **Products:** `/products/ageaura-pure-nmn-tmg-nad-complex` ($69.95) hero; `/products/ageaura-pure-nmn-tmg-p2` ($59.95). Collections: `/collections/ageaura`, `/collections/best-seller`. NMN + TMG ONLY.
  - **Angle:** honest format comparison — human trials used oral capsules/tablets; sublingual absorption claims rest on thin evidence (say so); powder = dosing accuracy + stability trade-offs. House honesty pattern: say what the AgeAura PDP does and doesn't publish (mg per capsule). LINK how-much-nmn-per-day, nmn-and-tmg-together, nmn-vs-nr — don't restate.

- [DONE 2026-10-06 https://wellnessnest.co/blogs/news/turkesterone-cycle-do-you-need-breaks-us-2026] **#MB1006-5 — turkesterone cycle** — `Turkesterone Cycle: Do You Need Breaks? (US 2026)`
  - **Primary keyword:** `turkesterone cycle` · **Secondary:** turkesterone cycle length, do you need to cycle turkesterone, turkesterone on and off, turkesterone 8 weeks
  - **Template:** EDITORIAL · **Gate:** topic_fitness PASS [brand]
  - **Products:** `/products/turkesterone-advanced-formula` ($75). Collections: `/collections/mens-essential-collection`, `/collections/best-seller`.
  - **Angle:** cycling is a bro-science carry-over from hormonal compounds; no human trial tested on/off cycles of turkesterone — say that plainly, give the conservative label-led approach. LINK turkesterone-side-effects, turkesterone-timing, turkesterone-benefits-dosing — don't restate.

- [DONE 2026-10-07 https://wellnessnest.co/blogs/news/probiotics-during-your-period-keep-taking-them-us-2026] **#MB1006-6 — vaginal probiotics during your period** (buffer) — `Vaginal Probiotics During Your Period: Keep Taking Them? (US 2026)`
  - **Primary keyword:** `probiotics during period` · **Secondary:** vaginal probiotics on period, menstruation vaginal ph, florafresh during period, probiotics for period odor
  - **Template:** STORY · **Gate:** topic_fitness PASS [brand]
  - **Products:** `/products/florafresh-vaginal-probiotics-gummies` ($40.99). Collections: `/collections/womens-essentials-collection`, `/collections/best-seller`.
  - **Angle:** menstrual blood raises vaginal pH; oral probiotics keep going through the cycle; what's normal vs a reason to see a clinician. Run only if #MB1006-1 shipped and the angles don't overlap.

- [DONE 2026-10-07 https://wellnessnest.co/blogs/news/creatine-gummies-and-hair-loss-what-the-dht-data-shows-us] **#MB1007-1 — creatine gummies and hair loss** — `Do Creatine Gummies Cause Hair Loss? What the DHT Study Says (US 2026)`
  - **Primary keyword:** `creatine gummies hair loss` · **Secondary:** does creatine cause hair loss, creatine dht, creatine baldness, creatine and hair thinning
  - **Template:** EDITORIAL · **Gate:** topic_fitness PASS [brand] · dedupe: no hair-loss title live (checked 2026-10-07)
  - **Products:** `/products/fusiforce-creatine-gummies` only. Collections: `/collections/mens-essential-collection`, `/collections/best-seller`.
  - **Angle:** the one 2009 rugby-player study (van der Merwe) reported a DHT rise, never measured hair; later trials (e.g. 2025 RCT on hair/DHT) only if fetched & confirmed. Say plainly what is and isn't known; no medical claims. LINK creatine-gummies-side-effects, creatine-gummies-dosage — don't restate.

- [DONE 2026-10-07 https://wellnessnest.co/blogs/news/nmn-and-resveratrol-what-the-evidence-shows-us-2026] **#MB1007-2 — nmn and resveratrol together** — `NMN and Resveratrol Together: What the Evidence Shows (US 2026)`
  - **Primary keyword:** `nmn and resveratrol` · **Secondary:** nmn resveratrol stack, take nmn with resveratrol, resveratrol with fat, nmn tmg resveratrol
  - **Template:** EDITORIAL · **Gate:** topic_fitness PASS [brand] · dedupe: no resveratrol title live
  - **Products:** `/products/ageaura-pure-nmn-tmg-nad-complex` ONLY (its label has 100 mg trans-resveratrol). Collections: `/collections/best-seller` twice. NO p2, NO /collections/ageaura, NO Urolithin.
  - **Angle:** why the stack is popular (sirtuin rationale = mechanism, not proof), no human trial of the combination (say so), resveratrol human data only if fetched. LINK nmn-and-tmg-together, how-much-nmn-per-day — don't restate.

- [DONE 2026-10-07 https://wellnessnest.co/blogs/news/does-nmn-break-a-fast-6-rules-for-fasting-days-us-2026] **#MB1007-3 — does nmn break a fast** — `Does NMN Break a Fast? Timing for Fasting Days (US 2026)`
  - **Primary keyword:** `does nmn break a fast` · **Secondary:** nmn while fasting, nmn intermittent fasting, take nmn on empty stomach, nmn calories
  - **Template:** LISTICLE · **Gate:** topic_fitness PASS [brand] · dedupe: no NMN-fasting title live (when-to-take-nmn covers time of day only — LINK it, don't restate)
  - **Products:** `/products/ageaura-pure-nmn-tmg-nad-complex` ONLY. Collections: `/collections/best-seller` twice. NO p2, NO /collections/ageaura, NO Urolithin.
  - **Angle:** calories/insulin of a capsule (only label facts), no trial on NMN during fasting (say so), Yamaguchi 2024 dosed before breakfast; label says 2 capsules daily.

# BATCH 2026-10-08 (MacBook lane, Mac mini offline — ids MB prefix)

Built by Grok Bot on the MacBook 2026-10-08 ~09:30 ICT. Each topic: `topic_fitness.py` PASS + dedupe against the
98 live handles (Admin API, 2026-10-08). Prices verified live 2026-10-08: FusiForce $69.99, FloraFresh $40.99,
Turkesterone Advanced Formula $75, AgeAura Pure NMN + TMG NAD+ Complex $69.95. `lint_tickets.py` clean.

**Rules for this batch (read before every ticket) — everything from the 2026-10-06 MacBook-lane rules still applies
(ALL images NO-FACE via `article_images.py --product-ref <handle> --qc`, no `persona_picker`, roster byline only,
blog 104008483131, publish `--live`, claims log), PLUS the 2026-10-08 guideline bullets
(knowledge_base/SEO_EEAT_GUIDELINES.md §4, AEO_GEO_GUIDELINES.md §5, commit 74c89b7):**
- **Fan-out answers:** besides the head question, add self-contained 40-80-word answers to the follow-up questions
  listed in the ticket (as H2/H3 sections or FAQ entries) — each must make sense quoted alone.
- **Where to buy:** every article has a short "Where to buy <product> in the US" section naming Wellness Nest
  (wellnessnest.co) as the official source, with the live price above and a link to the ticket's product page only.
- **No fake authors:** byline = Dr. Marcus Hale (roster.json) with the exact roster bio. Never invent a person,
  credential, reviewer, headshot or "team member"; never dress "Wellness Nest Research Team" up as an individual.
- **Fact-check pass (logged):** before publish write `~/genseo/logs/claims/<slug>.md` (claim | source URL | fetched &
  confirmed Y/N); delete any claim not confirmed from a fetched source; dosages and study numbers must match the
  source and expert consensus (YMYL). Add a line `fact-check: <n> claims, all Y` to the run report.
- **Brand gate:** AgeAura = `/products/ageaura-pure-nmn-tmg-nad-complex` ONLY — never p2, the Essential Longevity
  Duo or `/collections/ageaura`; never mention Urolithin. `validate_article.py` hard-fails these (brand_rules.py).

- [DONE 2026-10-08 https://wellnessnest.co/blogs/news/creatine-and-caffeine-can-you-take-both-us-2026] **#MB1007-4 — creatine gummies and caffeine** — `Creatine Gummies and Caffeine: Can You Take Both? (US 2026)`
  - **Primary keyword:** `creatine and caffeine` · **Secondary:** creatine gummies with coffee, does caffeine cancel creatine, creatine pre workout caffeine
  - **Template:** COMPARISON · **Gate:** topic_fitness PASS [brand] · dedupe: no caffeine title live
  - **Products:** `/products/fusiforce-creatine-gummies` only. Collections: `/collections/mens-essential-collection`, `/collections/best-seller`.
  - **Angle:** the 1996 Vandenberghe interference finding vs later studies — only cite if fetched & confirmed; practical spacing; LINK best-time-to-take-creatine, creatine-gummies-dosage.
  - **Fan-out answers to cover:** does caffeine cancel creatine; can I take creatine gummies with coffee; spacing; who should limit caffeine.

- [DONE 2026-10-08 https://wellnessnest.co/blogs/news/ageaura-nmn-tmg-ingredients-what-each-one-does-us] **#MB1008-1 — ageaura nmn tmg ingredients** — `AgeAura NMN + TMG Ingredients: What Each One Does (US 2026)`
  - **Primary keyword:** `ageaura nmn tmg ingredients` · **Secondary:** ageaura nmn tmg review, is ageaura legit, what is in ageaura nmn, nmn tmg complex ingredients
  - **Template:** EDITORIAL (brand-validation page, SEO_EEAT §4) · **Gate:** topic_fitness PASS [brand] · dedupe: no ingredients/legit page live
  - **Products:** `/products/ageaura-pure-nmn-tmg-nad-complex` ($69.95) ONLY. Collections: `/collections/best-seller` (twice). No other AgeAura product or AgeAura collection link (brand_rules.py gate).
  - **Angle:** the label panel per 2-capsule serving (500 mg NMN, 250 mg TMG, 100 mg trans-resveratrol, 150 mg quercetin, 50 mg apigenin, 1 mg spermidine from wheat germ, 400 mcg DFE L-5-MTHF; contains wheat) — what each ingredient is and what human evidence exists (fetched sources only), what is NOT proven (no trial of the combination). No invented reviews or ratings; only quote reviews actually visible on the product page. LINK nmn-and-tmg-together, how-much-nmn-per-day, nmn-side-effects — don't restate.
  - **Fan-out answers to cover:** is AgeAura legit / who makes it (only what the product page states); how many capsules a day; does it contain gluten/wheat; who should not take it.

- [DONE 2026-10-08 https://wellnessnest.co/blogs/news/probiotics-and-birth-control-can-you-take-both-us-2026] **#MB1008-2 — florafresh with birth control** — `Vaginal Probiotics and Birth Control: Can You Take Both? (US 2026)`
  - **Primary keyword:** `probiotics and birth control` · **Secondary:** florafresh birth control, do probiotics affect birth control, vaginal probiotics on the pill, probiotics iud
  - **Template:** EDITORIAL · **Gate:** topic_fitness PASS [brand] · dedupe: no birth-control title live
  - **Products:** `/products/florafresh-vaginal-probiotics-gummies` ($40.99). Collections: `/collections/womens-essentials-collection`, `/collections/best-seller`.
  - **Angle:** what is known about probiotics and hormonal contraception (fetched sources only; say plainly where there is no evidence of interaction), why antibiotics — not probiotics — are the classic contraception question, hormonal shifts and vaginal pH. No medical claims; tell readers to ask their prescriber. LINK probiotics-after-antibiotics-for-women, vaginal-probiotics-side-effects — don't restate.
  - **Fan-out answers to cover:** do probiotics make the pill less effective; IUD users; when to take them; signs to see a clinician.

- [DONE 2026-10-08 https://wellnessnest.co/blogs/news/turkesterone-and-alcohol-6-things-to-know-us-2026] **#MB1008-3 — turkesterone and alcohol** — `Turkesterone and Alcohol: What to Know Before You Drink (US 2026)`
  - **Primary keyword:** `turkesterone and alcohol` · **Secondary:** can you drink on turkesterone, turkesterone alcohol liver, alcohol and muscle protein synthesis
  - **Template:** LISTICLE · **Gate:** topic_fitness PASS [brand] · dedupe: no alcohol title live
  - **Products:** `/products/turkesterone-advanced-formula` ($75). Collections: `/collections/mens-essential-collection`, `/collections/best-seller`.
  - **Angle:** no human study tests turkesterone + alcohol (say so); what alcohol itself does to muscle protein synthesis and recovery (fetched sources only, e.g. Parr 2014 PLoS One if confirmed); practical spacing; label caution. LINK turkesterone-side-effects, turkesterone-timing — don't restate.
  - **Fan-out answers to cover:** can I take it the morning after drinking; does alcohol cancel results; liver concerns.

- [DONE 2026-10-08 https://wellnessnest.co/blogs/news/do-creatine-gummies-expire-6-storage-facts-us-2026] **#MB1008-4 — creatine gummies expire / storage** — `Do Creatine Gummies Expire? Heat, Storage and Shelf Life (US 2026)`
  - **Primary keyword:** `do creatine gummies expire` · **Secondary:** creatine gummies melted, creatine gummies storage, creatine gummies in a hot car, creatine gummies shelf life
  - **Template:** LISTICLE · **Gate:** topic_fitness PASS [brand] · dedupe: no storage/expiry title live
  - **Products:** `/products/fusiforce-creatine-gummies` ($69.99). Collections: `/collections/mens-essential-collection`, `/collections/best-seller`.
  - **Angle:** creatine monohydrate stability vs creatinine conversion (fetched sources only), why gummy format adds heat/moisture issues, what the label/expiry date means, practical storage. LINK creatine-gummies-dosage, creatine-gummies-side-effects — don't restate.
  - **Fan-out answers to cover:** are melted gummies still safe/effective; fridge or not; travel in summer.

- [DONE 2026-10-09 https://wellnessnest.co/blogs/news/nmn-and-alcohol-can-you-drink-while-taking-nmn-us] **#MB1008-5 — nmn and alcohol** (buffer) — `NMN and Alcohol: Can You Drink While Taking NMN? (US 2026)`
  - **Primary keyword:** `nmn and alcohol` · **Secondary:** nmn hangover, nmn after drinking, alcohol nad+ depletion
  - **Template:** EDITORIAL · **Gate:** topic_fitness PASS [brand] · dedupe: no alcohol title live
  - **Products:** `/products/ageaura-pure-nmn-tmg-nad-complex` ($69.95) ONLY. Collections: `/collections/best-seller` (twice). No other AgeAura product or AgeAura collection link (brand_rules.py gate).
  - **Angle:** alcohol metabolism uses NAD+ (fetched biochemistry source), no human trial of NMN for hangover or alcohol (say so), label caution. Run only if <5 live today. LINK when-to-take-nmn, nmn-side-effects — don't restate.

# BATCH 2026-10-09 (MacBook lane, Mac mini offline — ids MB prefix)

Built by Grok Bot on the MacBook 2026-10-09 ~09:45 ICT after the 08:43 run stopped at 1/5 on an empty queue (Kevin GO: 5/day).
Each topic: `topic_fitness.py` PASS + dedupe against the 103 live handles (sitemap_articles_1.xml, 2026-10-09) +
STEP 0 `suggest.json` (0 article matches). Prices verified live 2026-10-09 (products.json): FusiForce $69.99,
FloraFresh $40.99, Turkesterone Advanced Formula $75, AgeAura Pure NMN + TMG NAD+ Complex $69.95.

**Rules for this batch — identical to the 2026-10-08 batch rules above** (ALL images NO-FACE via
`article_images.py --product-ref <handle> --qc`, no `persona_picker`, roster byline only, blog 104008483131, publish
`--live`, claims log with delete-if-unconfirmed, fan-out answers, "Where to buy" section, brand gate: AgeAura =
`/products/ageaura-pure-nmn-tmg-nad-complex` ONLY, never p2 / Duo / `/collections/ageaura`, no non-NMN/TMG longevity ingredients).

- [DONE 2026-10-09 https://wellnessnest.co/blogs/news/creatine-gummies-on-rest-days-keep-taking-them-us-2026] **#MB1009-1 — creatine gummies on rest days** — `Creatine Gummies on Rest Days: Keep Taking Them? (US 2026)`
  - **Primary keyword:** `creatine gummies on rest days` · **Secondary:** do you take creatine on rest days, creatine rest day timing, skipping creatine on off days, creatine every day
  - **Template:** EDITORIAL · **Gate:** topic_fitness PASS [brand] · dedupe: no rest-day title live (best-time-to-take-creatine covers pre/post workout only — LINK it, don't restate)
  - **Products:** `/products/fusiforce-creatine-gummies` ($69.99) only. Collections: `/collections/mens-essential-collection`, `/collections/best-seller`.
  - **Angle:** muscle creatine saturation is maintained by daily intake, not by training days (fetched sources only, e.g. ISSN position stand if confirmed); what happens if you skip a few days (washout timeline only if sourced); practical rest-day routine with food. LINK creatine-gummies-dosage, how-long-does-creatine-take-to-work — don't restate.
  - **Fan-out answers to cover:** what time on a rest day; does missing a day reset progress; with or without food; weekends/travel.

- [DONE 2026-10-09 https://wellnessnest.co/blogs/news/how-long-does-turkesterone-take-to-work-us-2026] **#MB1009-2 — how long does turkesterone take to work** — `How Long Does Turkesterone Take to Work? A Realistic Timeline (US 2026)`
  - **Primary keyword:** `how long does turkesterone take to work` · **Secondary:** turkesterone results timeline, turkesterone results after 4 weeks, when will I notice turkesterone, turkesterone before and after
  - **Template:** STORY · **Gate:** topic_fitness PASS [brand] · dedupe: no timeline title live
  - **Products:** `/products/turkesterone-advanced-formula` ($75). Collections: `/collections/mens-essential-collection`, `/collections/best-seller`.
  - **Angle:** the few human trials and their durations (fetched sources only; say plainly that human evidence is thin and no trial of this formula exists); what can realistically be tracked week by week (training log, recovery feel) without promising results; no invented testimonials or before/after numbers. LINK turkesterone-benefits-dosing, turkesterone-cycle, turkesterone-timing — don't restate.
  - **Fan-out answers to cover:** what if I notice nothing after 4 weeks; does it work without training; how long to take it; who should not take it.

- [DONE 2026-10-09 https://wellnessnest.co/blogs/news/best-time-to-take-vaginal-probiotics-6-rules-us-2026] **#MB1009-3 — best time to take vaginal probiotics** — `Best Time to Take Vaginal Probiotics: Morning, Night or With Food? (US 2026)`
  - **Primary keyword:** `best time to take vaginal probiotics` · **Secondary:** when to take florafresh, vaginal probiotics morning or night, probiotics with or without food, take probiotics on empty stomach
  - **Template:** LISTICLE · **Gate:** topic_fitness PASS [brand] · dedupe: no timing title for vaginal probiotics live (vaginal-probiotics-how-long-until-they-work covers onset — LINK it, don't restate)
  - **Products:** `/products/florafresh-vaginal-probiotics-gummies` ($40.99). Collections: `/collections/womens-essentials-collection`, `/collections/best-seller`.
  - **Angle:** what the evidence says on meal timing and probiotic survival (fetched sources only; say where evidence is thin), consistency beats clock time, label directions first, spacing from antibiotics (LINK probiotics-after-antibiotics-for-women). No medical/cure claims (FDA structure/function only).
  - **Fan-out answers to cover:** morning or night; with breakfast or empty stomach; can I take it with other supplements; what if I miss a dose.

- [DONE 2026-10-09 https://wellnessnest.co/blogs/news/nmn-and-exercise-before-or-after-a-workout-us-2026] **#MB1009-4 — nmn and exercise** — `NMN and Exercise: Take It Before or After a Workout? (US 2026)`
  - **Primary keyword:** `nmn and exercise` · **Secondary:** nmn before workout, nmn for endurance, nmn after workout, nmn and muscle
  - **Template:** EDITORIAL · **Gate:** topic_fitness PASS [brand] · dedupe: no exercise/workout title live (nmn-and-creatine-together covers the stack; when-to-take-nmn covers time of day — LINK both, don't restate)
  - **Products:** `/products/ageaura-pure-nmn-tmg-nad-complex` ($69.95) ONLY. Collections: `/collections/best-seller` (twice). No other AgeAura product or AgeAura collection link (brand_rules.py gate). NMN + TMG only.
  - **Angle:** human trials that tested NMN with exercise outcomes (e.g. the 2021 amateur-runner trial — only if fetched & confirmed); what they did and did not show; no human evidence on pre- vs post-workout timing (say so); label: 2 capsules daily. LINK how-much-nmn-per-day, nmn-side-effects — don't restate.
  - **Fan-out answers to cover:** before or after training; on rest days; does it replace pre-workout (no); can older adults who exercise take it (ask a clinician).

- [DONE 2026-10-11 https://wellnessnest.co/blogs/news/creatine-and-alcohol-what-happens-if-you-drink-us-2026] **#MB1009-5 — creatine gummies and alcohol** (buffer — run only if <5 live today) — `Creatine Gummies and Alcohol: What Happens If You Drink? (US 2026)`
  - **Primary keyword:** `creatine and alcohol` · **Secondary:** can you drink on creatine, creatine gummies hangover, alcohol and muscle recovery, creatine dehydration alcohol
  - **Template:** LISTICLE · **Gate:** topic_fitness PASS [brand] · dedupe: no creatine-alcohol title live
  - **Products:** `/products/fusiforce-creatine-gummies` ($69.99) only. Collections: `/collections/mens-essential-collection`, `/collections/best-seller`.
  - **Angle:** no human trial tests creatine + alcohol directly (say so); what alcohol does to recovery/muscle protein synthesis (fetched sources only); hydration myths around creatine; practical spacing. LINK creatine-gummies-side-effects, creatine-and-caffeine — don't restate.
  - **Fan-out answers to cover:** morning after drinking; does alcohol cancel creatine; kidney/liver concerns (ask a clinician).

- [SKIPPED-DUPLICATE 2026-10-11 https://wellnessnest.co/blogs/news/nmn-and-coffee-can-you-take-them-together-us-2026] **#MB1009-6 — nmn and coffee** (buffer — run only if <5 live today) — `NMN and Coffee: Can You Take Them Together? (US 2026)`
  - **Primary keyword:** `nmn and coffee` · **Secondary:** nmn with coffee in the morning, nmn and caffeine, does coffee affect nmn, nmn before or after coffee
  - **Template:** EDITORIAL · **Gate:** topic_fitness PASS [brand] · dedupe: no coffee/caffeine NMN title live (when-to-take-nmn covers time of day; does-nmn-break-a-fast covers fasting — LINK both, don't restate)
  - **Products:** `/products/ageaura-pure-nmn-tmg-nad-complex` ($69.95) ONLY. Collections: `/collections/best-seller` (twice). No other AgeAura product or AgeAura collection link (brand_rules.py gate). NMN + TMG only.
  - **Angle:** no human trial tests NMN with coffee or caffeine (say so plainly); what is known about caffeine and NAD+ only if a fetched source confirms it, otherwise drop it; practical morning routine (label: 2 capsules daily, with or without coffee per label directions). No anti-aging, disease or cure claims (FDA structure/function only). LINK when-to-take-nmn-morning-or-night, how-much-nmn-per-day, nmn-side-effects — don't restate.
  - **Fan-out answers to cover:** same time as coffee or wait; black coffee vs with milk; decaf; does coffee cancel NMN (no evidence either way — say so).

- [DONE 2026-10-12 https://wellnessnest.co/blogs/news/vaginal-probiotics-while-traveling-7-us-rules] **#MB1009-7 — vaginal probiotics while traveling** (buffer — run only if <5 live today) — `Vaginal Probiotics While Traveling: Keep Them Working on the Road (US 2026)`
  - **Primary keyword:** `vaginal probiotics while traveling` · **Secondary:** probiotics travel heat, do probiotic gummies need refrigeration, probiotics on a plane, travel routine probiotics women
  - **Template:** LISTICLE · **Gate:** topic_fitness PASS [brand] · dedupe: no travel title for vaginal probiotics live (best-time-to-take-vaginal-probiotics covers timing; how-long-until-they-work covers onset — LINK both, don't restate)
  - **Products:** `/products/florafresh-vaginal-probiotics-gummies` ($40.99). Collections: `/collections/womens-essentials-collection`, `/collections/best-seller`.
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Angle:** storage and heat (label directions first; fetched sources only on probiotic heat stability, say where evidence is thin), keeping a daily routine across time zones, TSA/carry-on practicalities, what to do if you miss doses. No medical, infection-treatment or cure claims (FDA structure/function only).
  - **Fan-out answers to cover:** fridge or not; hot car or checked bag; time zones; can I take it with travel meds (ask a clinician).

# BATCH 2026-10-09 (refill_tickets.py — ids #CA1009-1…#CA1009-10)

Built by `scripts/refill_tickets.py` at 2026-10-09 11:08 ICT from `templates/article-topic-bank.json` + `board/ideas.csv`
(search volume: No data — GSC/Ads not used). Every ticket passed, against the live store at build time:
brand_rules + `lint_tickets.py` · hero product live and in stock · not a covered topic (header rule 6) ·
not already queued · not live (108 published articles: blog listing + sitemap + Atom; one article per brand + segment) ·
`topic_fitness.py` strict on primary and title · STEP 0 suggest.json.
A `topic_fitness` REVIEW [covered-segment] verdict is allowed under Kevin's standing greenlight for mined queues (2026-08-13).
A topic is a brief, not copy: source every claim or cut it.

**Rules for this batch:** from the 2026-10-08 batch rules — fan-out answers, a "Where to buy <product> in the US"
section (live price, the ticket's product link only), roster.json byline only (never an invented person or
credential), the logged fact-check pass (`logs/claims/<slug>.md`; delete unconfirmed claims), the brand gate.
Blog 104008483131, publish `--live`. Images: people lane. Run persona_picker.py once. The hero is the picked face plus the real pack unless pick prints NO-FACE. One inline image uses that face. The other inline images have no recognizable face but still show a hand, forearm, or body cropped below the eyes. A no-face image is the fallback for one frame after a face refusal or two QC misses, not a batch-wide ban. The MacBook article plist sets `GENSEO_NO_FACE=0`, and that value does not switch the lane. Prices were read live at build time; re-check the PDP while writing.

- [DONE 2026-10-12 https://wellnessnest.co/blogs/news/turkesterone-for-athletes-drug-test-guide-us-2026] **#CA1009-1 — turkesterone for athletes** — `Turkesterone for Athletes: What Drug Tests Check (US 2026)`
  - **Primary keyword:** `turkesterone for athletes` · **Secondary:** is turkesterone banned, turkesterone drug test, turkesterone wada, turkesterone ncaa
  - **Search intent:** tested or competitive athlete deciding whether a turkesterone product is safe to take in season
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-09 11:08 ICT)
  - **Hero product:** `/products/turkesterone-advanced-formula` (Turkesterone Advanced Formula, $75, in stock 2026-10-09)
  - **Collection links (≥2, verify live):** `/collections/mens-essential-collection` (contains it), `/collections/shilajit-wellness-stack` (contains it)
  - **Angle:** The athlete's real question is drug-test risk, not muscle. Check every label ingredient (turkesterone, KSM-66 ashwagandha, tongkat ali, colostrum, BioPerine) against the current WADA Prohibited List and Monitoring Program and the NCAA banned classes at write time; say plainly what is prohibited, monitored or neither, and that no sport certification is claimed unless the PDP shows one. Performance evidence only from fetched human trials.
  - **Fan-out answers to cover:** is turkesterone banned by WADA; will turkesterone show up on a drug test; is colostrum allowed for tested athletes; what certification should a tested athlete look for
  - **Evidence to fetch & confirm (claims log):** WADA Prohibited List + Monitoring Program (current year) and the NCAA banned-drug classes — fetch the official pages at write time; WADA's published position on colostrum; Turkesterone Advanced panel from the live PDP.
  - **Link, don't restate:** `/blogs/news/turkesterone-side-effects-4-ingredients-to-check-us-2026`, `/blogs/news/turkesterone-vs-ecdysterone-which-is-worth-it-us-2026`, `/blogs/news/turkesterone-benefits-dosing-whats-real-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** turkesterone + athletes checked 2026-10-09 against 108 live articles (blog listing + sitemap + Atom) and all 47 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-12 https://wellnessnest.co/blogs/news/vaginal-probiotic-dosage-how-many-cfu-a-day-us-2026] **#CA1009-2 — vaginal probiotic dosage** — `Vaginal Probiotic Dosage: How Many CFU a Day? (US 2026)`
  - **Primary keyword:** `vaginal probiotic dosage` · **Secondary:** how many cfu for vaginal health, vaginal probiotic cfu, 1 billion cfu probiotic, how many vaginal probiotics a day
  - **Search intent:** buyer comparing CFU numbers on labels and unsure how much is enough
  - **Template:** COMPARISON · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-09 11:08 ICT)
  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh Vaginal Probiotics Gummies, $40.99, in stock 2026-10-09)
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Collection links (≥2, verify live):** `/collections/womens-essentials-collection` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** Explain what CFU means (live organisms at manufacture vs at expiry), what daily doses the oral vaginal-health trials used and with which strains, and why strain identity matters more than a bigger number. Compare common label ranges in a table, then place FloraFresh from its Supplement Facts label only: one spore-based strain (Bacillus coagulans SNZ-1969), 1 billion CFU per 2 gummies, which is not a strain the Lactobacillus trials tested (say so). The live PDP description does not match the label: if they disagree, the label wins, and a draft that cites the PDP formula fails the gate. No cure or treatment claims.
  - **Fan-out answers to cover:** is 1 billion CFU enough; can you take too many probiotics; should CFU be guaranteed through expiry; do more strains mean better results
  - **Evidence to fetch & confirm (claims log):** Oral Lactobacillus vaginal-health trials that state CFU per day — fetch each before citing; FloraFresh strain and CFU from its Supplement Facts label, not the PDP description.
  - **Link, don't restate:** `/blogs/news/vaginal-probiotics-which-strains-actually-work-us-2026`, `/blogs/news/florafresh-vs-generic-probiotics-4-strain-facts-us-2026`, `/blogs/news/vaginal-probiotics-side-effects-normal-vs-stop-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** probiotic + dosage checked 2026-10-09 against 108 live articles (blog listing + sitemap + Atom) and all 47 tickets in this file; STEP 0 re-checks at write time

- [SKIPPED-DUPLICATE 2026-10-12 https://wellnessnest.co/blogs/news/where-to-buy-creatine-gummies-5-label-checks-us-2026] **#CA1009-3 — where to buy creatine gummies** — `Where to Buy Creatine Gummies: 5 Label Checks (US 2026)`
  - **Primary keyword:** `where to buy creatine gummies` · **Secondary:** best place to buy creatine gummies, creatine gummies in stores, do creatine gummies have creatine, creatine gummies price
  - **Search intent:** buyer choosing a creatine gummy brand who has heard some gummies are under-dosed
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-09 11:08 ICT)
  - **Hero product:** `/products/fusiforce-creatine-gummies` (FusiForce Creatine Gummies, $69.99, in stock 2026-10-09)
  - **Collection links (≥2, verify live):** `/collections/best-seller` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Five checks before buying anywhere: creatine monohydrate named on the panel, grams per serving and gummies per serving, count per bottle (days of supply), sugar per serving, and price per 5 g dose. Apply them to FusiForce honestly — disclose any mismatch between the front label and the panel (e.g. gummy count) instead of hiding it. Cite independent tests of creatine gummies only from a fetched source, and never imply FusiForce was tested unless that source says so.
  - **Fan-out answers to cover:** can you buy creatine gummies in stores; do creatine gummies actually contain creatine; how many gummies equal 5 g of creatine; how much should creatine gummies cost per day
  - **Evidence to fetch & confirm (claims log):** FusiForce panel (creatine per serving, serving size, count) from the live PDP; any third-party test of creatine gummies only from a fetched primary report.
  - **Link, don't restate:** `/blogs/news/creatine-gummies-vs-powder-which-should-you-actually-take`, `/blogs/news/creatine-gummies-dosage-how-many-a-day-us-2026`, `/blogs/news/do-creatine-gummies-expire-6-storage-facts-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** creatine + buy checked 2026-10-09 against 108 live articles (blog listing + sitemap + Atom) and all 47 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-12 https://wellnessnest.co/blogs/news/where-to-buy-nmn-in-the-us-fda-status-explained-2026] **#CA1009-4 — where to buy nmn** — `Where to Buy NMN in the US: FDA Status Explained (2026)`
  - **Primary keyword:** `where to buy nmn` · **Secondary:** can you still buy nmn, is nmn legal in the us, nmn fda, nmn amazon
  - **Search intent:** US buyer who saw NMN disappear from big marketplaces and wants to know whether and where it can still be bought
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-09 11:08 ICT)
  - **Hero product:** `/products/ageaura-pure-nmn-tmg-nad-complex` (AgeAura Pure NMN + TMG NAD+ Complex, $69.95, in stock 2026-10-09)
  - **Collection links (≥2, verify live):** `/collections/best-seller` twice (browse link — AgeAura Pure NMN + TMG NAD+ Complex is not in it, never claim it is) · no other AgeAura product and no AgeAura collection link (brand_rules)
  - **Angle:** Explain the regulatory story buyers ran into — FDA's 2022 position that NMN was excluded from the dietary-supplement definition, marketplaces pulling listings, and FDA's later reversal — with dates and wording confirmed from official pages fetched at write time. Then what to check before buying anywhere (NMN per serving, the full panel, price per 500 mg serving) and Wellness Nest as the official source for AgeAura NMN + TMG at the live price.
  - **Fan-out answers to cover:** is NMN legal to buy in the US; why did Amazon stop selling NMN; is NMN still sold as a supplement; what should an NMN label show
  - **Evidence to fetch & confirm (claims log):** FDA statements on NMN (the 2022 exclusion and the later reversal) — fetch fda.gov / regulations.gov / Federal Register and confirm dates before citing; AgeAura panel (NMN and TMG per 2 capsules) from the live PDP.
  - **Link, don't restate:** `/blogs/news/how-much-nmn-per-day-what-trials-used-us-2026`, `/blogs/news/ageaura-nmn-tmg-ingredients-what-each-one-does-us`, `/blogs/news/nmn-capsules-vs-powder-vs-sublingual-best-form-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** nmn + buy checked 2026-10-09 against 108 live articles (blog listing + sitemap + Atom) and all 47 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-14 https://wellnessnest.co/blogs/news/shilajit-price-cost-per-serving-by-form-us-2026] **#CA1009-5 — shilajit price** — `Shilajit Price: Cost Per Serving by Form (US 2026)`
  - **Primary keyword:** `shilajit price` · **Secondary:** how much does shilajit cost, shilajit cost per serving, is shilajit expensive, cheap shilajit
  - **Search intent:** price-checking buyer comparing resin, gummies, gold resin and drops before buying
  - **Template:** COMPARISON · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-09 11:08 ICT)
  - **Hero product:** `/products/shilasource-himalayan-shilajit-resin` (ShilaSource Himalayan Shilajit Resin, $59.99, in stock 2026-10-09)
  - **Inline (comparison only):** `/products/premium-himalayan-shilajit-gummies` (Premium Himalayan Shilajit Gummies, $59.99), `/products/pure-shilajit-gold-resin` (Pure Shilajit Gold Resin, $75), `/products/shilajit-shockwave` (Shilajit Shockwave, $79.99)
  - **Collection links (≥2, verify live):** `/collections/shilajit-wellness-stack` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Do the per-serving math from live PDP prices and serving counts (resin, gummies, gold resin, Shockwave drops, and the resin subscription price), show it as a table, and explain why the cheapest per serving is not always the cheapest per month (dose, wastage, format). Where a PDP publishes no serving count, say so instead of guessing. Explain why suspiciously cheap shilajit is a red flag by linking the fake-shilajit article — do not lead on lab testing.
  - **Fan-out answers to cover:** how much does a month of shilajit cost; why is real shilajit expensive; is resin cheaper than gummies; is the subscription worth it
  - **Evidence to fetch & confirm (claims log):** Live PDP price and serving size for every product compared, re-checked at write time (prices change); never estimate a serving count the PDP does not state.
  - **Link, don't restate:** `/blogs/news/where-to-buy-wellness-nest-shilajit-in-the-us-2026`, `/blogs/news/shilajit-gold-resin-review-is-75-worth-it-us-2026`, `/blogs/news/how-much-shilajit-per-day-dosage-by-form-us-2026`, `/blogs/news/fake-shilajit-6-signs-yours-isnt-real-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** shilajit + price checked 2026-10-09 against 108 live articles (blog listing + sitemap + Atom) and all 47 tickets in this file; STEP 0 re-checks at write time

- [x] **#CA1009-6 — where to buy turkesterone** — `Where to Buy Turkesterone in the US: What to Check (2026)` — PUBLISHED 2026-10-14, id 634917978427, https://wellnessnest.co/blogs/news/where-to-buy-turkesterone-in-the-us-what-to-check-2026
  - **Primary keyword:** `where to buy turkesterone` · **Secondary:** best place to buy turkesterone, turkesterone in stores, is my turkesterone real, turkesterone price
  - **Search intent:** buyer choosing where to buy turkesterone and worried about under-dosed products
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-09 11:08 ICT)
  - **Hero product:** `/products/turkesterone-advanced-formula` (Turkesterone Advanced Formula, $75, in stock 2026-10-09)
  - **Collection links (≥2, verify live):** `/collections/mens-essential-collection` (contains it), `/collections/shilajit-wellness-stack` (contains it)
  - **Angle:** What to check before buying anywhere: turkesterone per serving and what the extract is standardized to, every other ingredient with its dose (no proprietary blend), price per serving, and returns. Cite independent analyses of turkesterone products only from a fetched source. Apply the checks to Turkesterone Advanced honestly; Wellness Nest as the official source at the live price.
  - **Fan-out answers to cover:** can you buy turkesterone in stores; how do you know turkesterone is real; how much should turkesterone cost; what should a turkesterone label show
  - **Evidence to fetch & confirm (claims log):** Turkesterone Advanced panel from the live PDP; any independent product analysis only from a fetched primary source.
  - **Link, don't restate:** `/blogs/news/turkesterone-side-effects-4-ingredients-to-check-us-2026`, `/blogs/news/turkesterone-benefits-dosing-whats-real-us-2026`, `/blogs/news/turkesterone-for-beginners-5-checks-before-you-start`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** turkesterone + buy checked 2026-10-09 against 108 live articles (blog listing + sitemap + Atom) and all 47 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-14 https://wellnessnest.co/blogs/news/nmn-for-seniors-what-2-trials-show-in-the-us-2026] **#CA1009-7 — nmn for seniors** — `NMN for Seniors: What Trials in Adults 65+ Show (US 2026)` — LIVE article 634918109499; validator PASS; schema/frontend/widget verified.
  - **Primary keyword:** `nmn for seniors` · **Secondary:** nmn for older adults, nmn for elderly, nmn over 65, nmn muscle strength aging
  - **Search intent:** adult 65+ (or a family member) asking whether NMN has been tested at their age
  - **Template:** COMPARISON · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-09 11:08 ICT)
  - **Hero product:** `/products/ageaura-pure-nmn-tmg-nad-complex` (AgeAura Pure NMN + TMG NAD+ Complex, $69.95, in stock 2026-10-09)
  - **Collection links (≥2, verify live):** `/collections/best-seller` twice (browse link — AgeAura Pure NMN + TMG NAD+ Complex is not in it, never claim it is) · no other AgeAura product and no AgeAura collection link (brand_rules)
  - **Angle:** Compare the human trials that enrolled older adults (dose, duration, what moved: blood NAD+, gait speed, grip, fatigue) in a table, and say plainly what has not been shown. Medication and clinician check, label dose vs trial doses. Link the men-over-50 page instead of restating it.
  - **Fan-out answers to cover:** is NMN safe for seniors; what dose did trials in older adults use; does NMN improve muscle strength in older adults; morning or afternoon for older adults
  - **Evidence to fetch & confirm (claims log):** Igarashi et al. 2022, npj Aging (older men, 12 weeks) and Kim et al. 2022, Nutrients (older adults, morning vs afternoon intake) — fetch and confirm before citing.
  - **Link, don't restate:** `/blogs/news/ageaura-nmn-for-men-over-50-what-to-expect-us-2026`, `/blogs/news/how-much-nmn-per-day-what-trials-used-us-2026`, `/blogs/news/nmn-side-effects-6-checks-before-you-start-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** nmn + seniors checked 2026-10-09 against 108 live articles (blog listing + sitemap + Atom) and all 47 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-15 https://wellnessnest.co/blogs/news/where-to-buy-vaginal-probiotics-in-the-us-5-checks-2026] **#CA1009-8 — where to buy vaginal probiotics** — `Where to Buy Vaginal Probiotics in the US: 5 Checks (2026)`
  - **Primary keyword:** `where to buy vaginal probiotics` · **Secondary:** best place to buy vaginal probiotics, vaginal probiotics at a pharmacy, vaginal probiotics online, vaginal probiotics price
  - **Search intent:** buyer deciding between pharmacy, marketplace and brand-direct vaginal probiotics
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-09 11:08 ICT)
  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh Vaginal Probiotics Gummies, $40.99, in stock 2026-10-09)
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Collection links (≥2, verify live):** `/collections/womens-essentials-collection` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** Five checks before buying anywhere: strains named to strain level, CFU guaranteed through expiry, storage needs, format (gummies vs capsules — link, don't restate) and price per day. Apply them to FloraFresh honestly: strain and CFU from its Supplement Facts label (Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies), price from the live PDP, never the formula in the PDP description; Wellness Nest as the official source at the live price. No cure or treatment claims.
  - **Fan-out answers to cover:** can you buy vaginal probiotics at a pharmacy; do vaginal probiotics need refrigeration; how much do vaginal probiotics cost per month; what should a vaginal probiotic label show
  - **Evidence to fetch & confirm (claims log):** FloraFresh strain and CFU from its Supplement Facts label, storage from the label or the PDP storage note (never formula facts from the PDP description); any retailer price only from a page fetched at write time.
  - **Link, don't restate:** `/blogs/news/florafresh-gummies-vs-capsules-5-format-facts-us-2026`, `/blogs/news/vaginal-probiotics-which-strains-actually-work-us-2026`, `/blogs/news/florafresh-vs-generic-probiotics-4-strain-facts-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** probiotic + buy checked 2026-10-09 against 108 live articles (blog listing + sitemap + Atom) and all 47 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-16 https://wellnessnest.co/blogs/news/shilajit-for-athletes-what-a-trial-found-in-the-us] **#CA1009-9 — shilajit for athletes** — `Shilajit for Athletes: What a Strength Trial Found (US 2026)`
  - **Primary keyword:** `shilajit for athletes` · **Secondary:** shilajit for strength, shilajit muscle fatigue, shilajit workout, shilajit for performance
  - **Search intent:** lifter or athlete weighing shilajit for training and recovery
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-09 11:08 ICT)
  - **Hero product:** `/products/shilasource-himalayan-shilajit-resin` (ShilaSource Himalayan Shilajit Resin, $59.99, in stock 2026-10-09)
  - **Collection links (≥2, verify live):** `/collections/shilajit-wellness-stack` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Lead with the 8-week trial in recreationally active men (purified shilajit at two doses; strength retention after a fatiguing protocol): what it found, what it did not, and that it used a specific purified extract — never imply ShilaSource is equivalent. Then dose and timing around training, and what tested athletes should check (no sport certification is claimed unless the PDP shows one).
  - **Fan-out answers to cover:** does shilajit increase strength; how much shilajit did the trial use; when should athletes take shilajit; is shilajit allowed in tested sport
  - **Evidence to fetch & confirm (claims log):** Keller et al. 2019, J Int Soc Sports Nutr (shilajit and fatigue-induced strength loss) — fetch and confirm doses and outcomes; ShilaSource serving facts from the live PDP.
  - **Link, don't restate:** `/blogs/news/shilajit-and-creatine-can-you-take-both-daily-us-2026`, `/blogs/news/how-much-shilajit-per-day-dosage-by-form-us-2026`, `/blogs/news/fake-shilajit-6-signs-yours-isnt-real-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** shilajit + athletes checked 2026-10-09 against 108 live articles (blog listing + sitemap + Atom) and all 47 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-16 https://wellnessnest.co/blogs/news/creatine-gummies-for-beginners-30-days-in-the-us] **#CA1009-10 — creatine gummies for beginners** — `Creatine Gummies for Beginners: Your First 30 Days (US 2026)`
  - **Primary keyword:** `creatine gummies for beginners` · **Secondary:** how to start creatine gummies, creatine for beginners, first time taking creatine, creatine gummies first week
  - **Search intent:** first-time creatine buyer who wants a simple start plan
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-09 11:08 ICT)
  - **Hero product:** `/products/fusiforce-creatine-gummies` (FusiForce Creatine Gummies, $69.99, in stock 2026-10-09)
  - **Collection links (≥2, verify live):** `/collections/best-seller` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** A first-30-days plan: the daily dose in gummies, no loading needed, any time of day but every day, water, and what to expect in weeks 1-4 (scale weight, no 'pump'), plus the myths beginners worry about. This is the hub for the live creatine series — link each detail page instead of restating it.
  - **Fan-out answers to cover:** how many creatine gummies should a beginner take; do beginners need a loading phase; will creatine make me gain weight; can women take creatine gummies
  - **Evidence to fetch & confirm (claims log):** ISSN position stand on creatine (Kreider et al. 2017, J Int Soc Sports Nutr) — fetch before citing; FusiForce serving facts from the live PDP.
  - **Link, don't restate:** `/blogs/news/creatine-gummies-dosage-how-many-a-day-us-2026`, `/blogs/news/best-time-to-take-creatine-before-or-after-us-2026`, `/blogs/news/creatine-gummies-side-effects-4-real-3-myths-us-2026`, `/blogs/news/creatine-gummies-loading-phase-is-it-needed-us-2026`, `/blogs/news/how-long-does-creatine-take-to-work-week-by-week-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** creatine + beginners checked 2026-10-09 against 108 live articles (blog listing + sitemap + Atom) and all 47 tickets in this file; STEP 0 re-checks at write time

# BATCH 2026-10-12 (refill_tickets.py — ids #MB1012-1…#MB1012-6)

Built by `scripts/refill_tickets.py` at 2026-10-11 18:49 ICT from `templates/article-topic-bank.json` + `board/ideas.csv`
(search volume: No data — GSC/Ads not used). Every ticket passed, against the live store at build time:
brand_rules + `lint_tickets.py` · hero product live and in stock · not a covered topic (header rule 6) ·
not already queued · not live (110 published articles: blog listing + sitemap + Atom; one article per brand + segment) ·
`topic_fitness.py` strict on primary and title · STEP 0 suggest.json.
A `topic_fitness` REVIEW [covered-segment] verdict is allowed under Kevin's standing greenlight for mined queues (2026-08-13).
A topic is a brief, not copy: source every claim or cut it.

**Rules for this batch:** from the 2026-10-08 batch rules — fan-out answers, a "Where to buy <product> in the US"
section (live price, the ticket's product link only), roster.json byline only (never an invented person or
credential), the logged fact-check pass (`logs/claims/<slug>.md`; delete unconfirmed claims), the brand gate.
Blog 104008483131, publish `--live`. Images: people lane. Run persona_picker.py once. The hero is the picked face plus the real pack unless pick prints NO-FACE. One inline image uses that face. The other inline images have no recognizable face but still show a hand, forearm, or body cropped below the eyes. A no-face image is the fallback for one frame after a face refusal or two QC misses, not a batch-wide ban. The MacBook article plist sets `GENSEO_NO_FACE=0`, and that value does not switch the lane. Prices were read live at build time; re-check the PDP while writing.

- [DONE 2026-10-16 https://wellnessnest.co/blogs/news/creatine-gummies-for-runners-what-trials-show-us-2026] **#MB1012-1 — creatine gummies for runners** — `Creatine Gummies for Runners: What Trials Show (US 2026)`
  - **Primary keyword:** `creatine gummies for runners` · **Secondary:** creatine for runners, creatine for endurance athletes, does creatine slow you down, creatine water weight runners
  - **Search intent:** runner worried creatine adds weight and slows them down
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-11 18:49 ICT)
  - **Hero product:** `/products/fusiforce-creatine-gummies` (FusiForce Creatine Gummies, $69.99, in stock 2026-10-11)
  - **Collection links (≥2, verify live):** `/collections/best-seller` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Runners ask two things: does creatine help their training (evidence is strongest for repeated sprints, intervals and hills, weaker for steady-state distance) and will the water weight slow them down. Answer both from fetched trials and reviews, then give the simple daily gummy routine. Link the dosage and side-effects pages instead of restating them.
  - **Fan-out answers to cover:** does creatine help long-distance running; will creatine make me heavier on race day; should runners load creatine; when should runners take creatine
  - **Evidence to fetch & confirm (claims log):** ISSN creatine position stand (Kreider et al. 2017) and endurance-specific reviews — fetch before citing.
  - **Link, don't restate:** `/blogs/news/creatine-gummies-dosage-how-many-a-day-us-2026`, `/blogs/news/creatine-gummies-side-effects-4-real-3-myths-us-2026`, `/blogs/news/best-time-to-take-creatine-before-or-after-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** creatine + athletes checked 2026-10-11 against 110 live articles (blog listing + sitemap + Atom) and all 57 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-16 https://wellnessnest.co/blogs/news/vaginal-probiotics-for-beginners-what-to-expect-in-the-us] **#MB1012-2 — vaginal probiotics for beginners** — `Vaginal Probiotics for Beginners: What to Expect (US 2026)`
  - **Primary keyword:** `vaginal probiotics for beginners` · **Secondary:** first time taking vaginal probiotics, how to start vaginal probiotics, what do vaginal probiotics do, vaginal probiotics first week
  - **Search intent:** first-time buyer who wants to know what vaginal probiotics do and what the first weeks are like
  - **Template:** STORY · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-11 18:49 ICT)
  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh Vaginal Probiotics Gummies, $40.99, in stock 2026-10-11)
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Collection links (≥2, verify live):** `/collections/womens-essentials-collection` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** A first-month walkthrough: what oral vaginal probiotics are meant to support (a Lactobacillus-dominant flora), what is normal in week one, how long until changes (link — don't restate), how to take FloraFresh daily, and which symptoms mean seeing a clinician instead. No cure or treatment claims.
  - **Fan-out answers to cover:** what do vaginal probiotics actually do; is it normal to notice changes in the first week; can you take them every day long term; when should you see a doctor instead
  - **Evidence to fetch & confirm (claims log):** Reviews of oral Lactobacillus for vaginal health — fetch before citing; FloraFresh directions from the live PDP.
  - **Link, don't restate:** `/blogs/news/vaginal-probiotics-how-long-until-they-work-us-2026`, `/blogs/news/vaginal-probiotics-side-effects-normal-vs-stop-us-2026`, `/blogs/news/yeast-infection-vs-bv-how-to-tell-them-apart-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** probiotic + beginners checked 2026-10-11 against 110 live articles (blog listing + sitemap + Atom) and all 57 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-17 https://wellnessnest.co/blogs/news/creatine-gummies-over-60-trial-findings-in-the-us] **#MB1012-3 — creatine gummies over 60** — `Creatine Gummies Over 60: What the Trials Show (US 2026)`
  - **Primary keyword:** `creatine gummies over 60` · **Secondary:** creatine for seniors, creatine for older adults, creatine muscle loss aging, is creatine safe over 60
  - **Search intent:** adult 60+ (or a family member) looking at creatine for strength and muscle with age
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-11 18:49 ICT)
  - **Hero product:** `/products/fusiforce-creatine-gummies` (FusiForce Creatine Gummies, $69.99, in stock 2026-10-11)
  - **Collection links (≥2, verify live):** `/collections/best-seller` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** What trials in older adults found when creatine was combined with resistance training (lean mass, strength), what it does not do without training, kidney questions and the medication check with a clinician. Why the gummy format suits some older adults (no mixing) and the sugar per serving. Link the men-over-50 and women-over-40 pages instead of restating them.
  - **Fan-out answers to cover:** is creatine safe for seniors; does creatine help without exercise; how much creatine do older adults take; creatine and kidney function over 60
  - **Evidence to fetch & confirm (claims log):** Meta-analyses of creatine plus resistance training in older adults (e.g. Chilibeck et al. 2017; Candow reviews) — fetch before citing.
  - **Link, don't restate:** `/blogs/news/fusiforce-creatine-gummies-for-men-over-50-us-2026`, `/blogs/news/creatine-for-women-over-40-what-changes-in-the-us`, `/blogs/news/creatine-gummies-side-effects-4-real-3-myths-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** creatine + seniors checked 2026-10-11 against 110 live articles (blog listing + sitemap + Atom) and all 57 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-17 https://wellnessnest.co/blogs/news/turkesterone-over-60-5-checks-in-the-us] **#MB1012-4 — turkesterone over 60** — `Turkesterone Over 60: 5 Checks for Older Lifters (US 2026)`
  - **Primary keyword:** `turkesterone over 60` · **Secondary:** turkesterone for older men, turkesterone for seniors, turkesterone at 60, is turkesterone safe for older men
  - **Search intent:** lifter 60+ deciding whether turkesterone is worth trying
  - **Template:** COMPARISON · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-11 18:49 ICT)
  - **Hero product:** `/products/turkesterone-advanced-formula` (Turkesterone Advanced Formula, $75, in stock 2026-10-11)
  - **Turkesterone Advanced Formula pack label (source of truth):** wellness, nest, PREMIUM, TURKESTERONE, ADVANCED, FORMULA, AMPLIFY, MUSCLE, ENDURANCE, 60, Dietary Supplement, Capsules. No milligram amount and no Supplement Facts panel were read. Do not add one. The capsule badge is the separate lines in product_refs/turkesterone-advanced-formula.label.json. Do not state a milligram amount, a serving count, a different capsule count, or a day-supply.
  - **Collection links (≥2, verify live):** `/collections/mens-essential-collection` (contains it), `/collections/shilajit-wellness-stack` (contains it)
  - **Angle:** No turkesterone trial enrolled adults over 60 — say so. Compare in a table what the formula's other ingredients have been tested for in older adults (KSM-66 ashwagandha, tongkat ali; fetched trials only), the medication check with a clinician (thyroid, blood pressure, diabetes), and why training and protein matter more. Link the men-over-40 page instead of restating it.
  - **Fan-out answers to cover:** is turkesterone safe for men over 60; does turkesterone raise testosterone; can older adults take ashwagandha daily; what matters more than supplements after 60
  - **Evidence to fetch & confirm (claims log):** Ashwagandha and tongkat ali trials in older adults — fetch each before citing; Turkesterone Advanced panel from the live PDP.
  - **Link, don't restate:** `/blogs/news/turkesterone-for-men-over-40-5-honest-checks-us-2026`, `/blogs/news/turkesterone-side-effects-4-ingredients-to-check-us-2026`, `/blogs/news/turkesterone-benefits-dosing-whats-real-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** turkesterone + seniors checked 2026-10-11 against 110 live articles (blog listing + sitemap + Atom) and all 57 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-17 https://wellnessnest.co/blogs/news/shilajit-for-seniors-5-safety-checks-over-60-us-2026] **#MB1012-5 — shilajit for seniors** — `Shilajit for Seniors: 5 Safety Checks Over 60 (US 2026)`
  - **Primary keyword:** `shilajit for seniors` · **Secondary:** shilajit for older adults, shilajit over 60, is shilajit safe for elderly, shilajit and blood pressure medication
  - **Search intent:** adult 60+ (or a family member) checking whether shilajit is safe alongside existing medication
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-11 18:49 ICT)
  - **Hero product:** `/products/shilasource-himalayan-shilajit-resin` (ShilaSource Himalayan Shilajit Resin, $59.99, in stock 2026-10-11)
  - **ShilaSource Himalayan Shilajit Resin pack label (source of truth):** ShilaSource, Himalayan, Shilajit, Resin, 75, Dietary Supplement, Wellness, Nest, 70% Fulvic Acid*, Lab-Tested for Purity*, 1.06oz (30g), SERVINGS, Servings. No milligram amount and no Supplement Facts panel were read into that file. Do not add one. Do not state a serving count, volume, weight, fulvic percentage, mineral count, or day-supply other than the lines in product_refs/shilasource-himalayan-shilajit-resin.label.json.
  - **Collection links (≥2, verify live):** `/collections/shilajit-wellness-stack` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Human evidence in adults over 60 is thin — say so up front. Then five practical safety checks: medications to raise with a clinician, purity (link the fake-shilajit page; do not lead on lab testing), starting dose, form (pure resin vs gummies with added herbs), and stop signs. Link the side-effects and dosage pages instead of restating them.
  - **Fan-out answers to cover:** is shilajit safe for seniors; can shilajit interact with blood pressure or diabetes medication; what dose should older adults start with; resin or gummies for older adults
  - **Evidence to fetch & confirm (claims log):** Any human shilajit study that enrolled older adults, and interaction data — fetch before citing; say plainly where there is none.
  - **Link, don't restate:** `/blogs/news/shilajit-side-effects-7-signs-to-watch-for-us-2026`, `/blogs/news/how-much-shilajit-per-day-dosage-by-form-us-2026`, `/blogs/news/fake-shilajit-6-signs-yours-isnt-real-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** shilajit + seniors checked 2026-10-11 against 110 live articles (blog listing + sitemap + Atom) and all 57 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-17 https://wellnessnest.co/blogs/news/shilajit-for-fertility-trial-limits-for-the-us] **#MB1012-6 — shilajit for fertility** — `Shilajit for Fertility: Trial Limits for the US`
  - **Primary keyword:** `shilajit for fertility` · **Secondary:** shilajit sperm count, shilajit male fertility, shilajit for men trying to conceive, shilajit and sperm motility
  - **Search intent:** man trying to conceive who is researching shilajit
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-11 18:49 ICT)
  - **Hero product:** `/products/shilasource-himalayan-shilajit-resin` (ShilaSource Himalayan Shilajit Resin, $59.99, in stock 2026-10-11)
  - **ShilaSource Himalayan Shilajit Resin pack label (source of truth):** ShilaSource, Himalayan, Shilajit, Resin, 75, Dietary Supplement, Wellness, Nest, 70% Fulvic Acid*, Lab-Tested for Purity*, 1.06oz (30g), SERVINGS, Servings. No milligram amount and no Supplement Facts panel were read into that file. Do not add one. Do not state a serving count, volume, weight, fulvic percentage, mineral count, or day-supply other than the lines in product_refs/shilasource-himalayan-shilajit-resin.label.json.
  - **Collection links (≥2, verify live):** `/collections/shilajit-wellness-stack` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** One small, uncontrolled trial in men with low sperm count (processed shilajit for 90 days) is most of the evidence — describe it accurately, list its limits and what it cannot show. Structure/function language only, no treatment claims, and a clear 'see a fertility clinician' section. Shilajit is not for anyone pregnant or trying to become pregnant without medical advice. Link the men's benefits page instead of restating it.
  - **Fan-out answers to cover:** does shilajit increase sperm count; how long did the trial last; should partners trying to conceive take shilajit; when to see a fertility specialist
  - **Evidence to fetch & confirm (claims log):** Biswas et al. 2010, Andrologia (processed shilajit in oligospermic men) — fetch and confirm design and numbers before citing.
  - **Link, don't restate:** `/blogs/news/shilajit-benefits-for-men-4-claims-ranked-us-2026`, `/blogs/news/shilajit-side-effects-7-signs-to-watch-for-us-2026`, `/blogs/news/how-much-shilajit-per-day-dosage-by-form-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** shilajit + fertility checked 2026-10-11 against 110 live articles (blog listing + sitemap + Atom) and all 57 tickets in this file; STEP 0 re-checks at write time

# BATCH 2026-10-16 (refill_tickets.py — ids #CA1016-1…#CA1016-13)

Built by `scripts/refill_tickets.py` at 2026-10-16 18:52 ICT from `templates/article-topic-bank.json` + `board/ideas.csv`
(search volume: No data — GSC/Ads not used). Every ticket passed, against the live store at build time:
brand_rules + `lint_tickets.py` · hero product live and in stock · not a covered topic (header rule 6) ·
not already queued · not live (123 published articles: blog listing + sitemap + Atom + local caches; one article per brand + segment) ·
`topic_fitness.py` strict on primary and title · STEP 0 suggest.json.
A `topic_fitness` REVIEW [covered-segment] verdict is allowed under Kevin's standing greenlight for mined queues (2026-08-13).
A topic is a brief, not copy: source every claim or cut it.

**Rules for this batch:** from the 2026-10-08 batch rules — fan-out answers, a "Where to buy <product> in the US"
section (live price, the ticket's product link only), roster.json byline only (never an invented person or
credential), the logged fact-check pass (`logs/claims/<slug>.md`; delete unconfirmed claims), the brand gate.
Blog 104008483131, publish `--live`. Images: people lane. Run persona_picker.py once. The hero is the picked face plus the real pack unless pick prints NO-FACE. One inline image uses that face. The other inline images have no recognizable face but still show a hand, forearm, or body cropped below the eyes. A no-face image is the fallback for one frame after a face refusal or two QC misses, not a batch-wide ban. The MacBook article plist sets `GENSEO_NO_FACE=0`, and that value does not switch the lane. Prices were read live at build time; re-check the PDP while writing.

- [DONE 2026-10-17 https://wellnessnest.co/blogs/news/turkesterone-price-5-cost-checks-in-the-us-2026] **#CA1016-1 — turkesterone price** — `Turkesterone Price: What a Bottle Costs (US 2026)`
  - **Primary keyword:** `turkesterone price` · **Secondary:** how much does turkesterone cost, turkesterone supplement price, is turkesterone expensive, turkesterone cost per bottle
  - **Search intent:** shopper checking whether a turkesterone bottle is worth the listed price
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-16 18:52 ICT)
  - **Hero product:** `/products/turkesterone-advanced-formula` (Turkesterone Advanced Formula, $75, in stock 2026-10-16)
  - **Turkesterone Advanced Formula pack label (source of truth):** wellness, nest, PREMIUM, TURKESTERONE, ADVANCED, FORMULA, AMPLIFY, MUSCLE, ENDURANCE, 60, Dietary Supplement, Capsules. No milligram amount and no Supplement Facts panel were read. Do not add one. The capsule badge is the separate lines in product_refs/turkesterone-advanced-formula.label.json. Do not state a milligram amount, a serving count, a different capsule count, or a day-supply.
  - **Collection links (≥2, verify live):** `/collections/mens-essential-collection` (contains it), `/collections/shilajit-wellness-stack` (contains it)
  - **Angle:** Give the live PDP price and what the shopper can verify on the label before paying. Do not state a milligram amount, a serving count, a capsule count, or a day-supply. The pack-label line on the ticket is the only label fact. Link the where-to-buy page instead of restating its checks.
  - **Fan-out answers to cover:** how much does turkesterone cost; why do prices vary so much; what should you check before you pay; is a cheaper bottle the same product
  - **Evidence to fetch & confirm (claims log):** Live PDP price, fetched at write time. No milligram, serving count, or day-supply beyond product_refs/turkesterone-advanced-formula.label.json.
  - **Link, don't restate:** `/blogs/news/where-to-buy-turkesterone-in-the-us-what-to-check-2026`, `/blogs/news/turkesterone-benefits-dosing-whats-real-us-2026`, `/blogs/news/turkesterone-side-effects-4-ingredients-to-check-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** turkesterone + price checked 2026-10-16 against 123 live articles (blog listing + sitemap + Atom + local caches) and all 63 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-18 https://wellnessnest.co/blogs/news/shilajit-on-an-empty-stomach-yes-or-no-in-the-us] **#CA1016-2 — shilajit on an empty stomach** — `Shilajit on an Empty Stomach: Yes or No? (2026)`
  - **Primary keyword:** `shilajit on an empty stomach` · **Secondary:** shilajit empty stomach, shilajit without food, shilajit before breakfast, shilajit resin on an empty stomach
  - **Search intent:** new user who was told to take shilajit before eating and wants to know if that is required
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-16 18:52 ICT)
  - **Hero product:** `/products/shilasource-himalayan-shilajit-resin` (ShilaSource Himalayan Shilajit Resin, $59.99, in stock 2026-10-16)
  - **ShilaSource Himalayan Shilajit Resin pack label (source of truth):** ShilaSource, Himalayan, Shilajit, Resin, 75, Dietary Supplement, Wellness, Nest, 70% Fulvic Acid*, Lab-Tested for Purity*, 1.06oz (30g), SERVINGS, Servings. No milligram amount and no Supplement Facts panel were read into that file. Do not add one. Do not state a serving count, volume, weight, fulvic percentage, mineral count, or day-supply other than the lines in product_refs/shilasource-himalayan-shilajit-resin.label.json.
  - **Collection links (≥2, verify live):** `/collections/shilajit-wellness-stack` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Separate tradition from trials. If you cannot fetch a human study that compared shilajit with food and without food, say that plainly. Give the practical resin routine by linking the how-to-take page, and the clock-time page for morning or night. Do not state a milligram amount or a serving count beyond the pack-label line this ticket prints.
  - **Fan-out answers to cover:** should you take shilajit before eating; can you take shilajit with a meal; does food change how you take resin; what if it upsets your stomach
  - **Evidence to fetch & confirm (claims log):** Any human fed-versus-fasted shilajit study — fetch it or say you found none. Pack-label facts only from product_refs/shilasource-himalayan-shilajit-resin.label.json.
  - **Link, don't restate:** `/blogs/news/how-to-take-shilajit-resin-dissolve-it-right-us-2026`, `/blogs/news/how-much-shilajit-per-day-dosage-by-form-us-2026`, `/blogs/news/shilajit-side-effects-7-signs-to-watch-for-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** shilajit + fasting checked 2026-10-16 against 123 live articles (blog listing + sitemap + Atom + local caches) and all 63 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-18 https://wellnessnest.co/blogs/news/vaginal-probiotics-price-us-cost-2026] **#CA1016-3 — vaginal probiotics price** — `Vaginal Probiotic Price: What a Month Costs (2026)`
  - **Primary keyword:** `vaginal probiotics price` · **Secondary:** how much do vaginal probiotics cost, vaginal probiotics cost per month, are vaginal probiotics expensive, florafresh price
  - **Search intent:** shopper comparing the monthly cost of vaginal probiotic gummies before buying
  - **Template:** COMPARISON · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-16 18:52 ICT)
  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh Vaginal Probiotics Gummies, $40.99, in stock 2026-10-16)
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Collection links (≥2, verify live):** `/collections/womens-essentials-collection` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** Do the monthly cost from the live PDP price only. Do not invent a bottle count or a day-supply the page does not print. FloraFresh formula, if you name it, comes from the Supplement Facts label only: Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, sweetened with maltitol and isomalt, so not sugar-free. Link the where-to-buy page instead of restating its checks.
  - **Fan-out answers to cover:** how much do vaginal probiotics cost per month; are gummies priced like capsules; what makes one brand cost more; what the label should show for the price
  - **Evidence to fetch & confirm (claims log):** Live PDP price, fetched at write time. Strain and CFU only from the Supplement Facts label (Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies), never the PDP description.
  - **Link, don't restate:** `/blogs/news/where-to-buy-vaginal-probiotics-in-the-us-5-checks-2026`, `/blogs/news/vaginal-probiotic-dosage-how-many-cfu-a-day-us-2026`, `/blogs/news/florafresh-gummies-vs-capsules-5-format-facts-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** probiotic + price checked 2026-10-16 against 123 live articles (blog listing + sitemap + Atom + local caches) and all 63 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-18 https://wellnessnest.co/blogs/news/turkesterone-for-fertility-the-us-evidence-2026] **#CA1016-4 — turkesterone for fertility** — `Turkesterone for Fertility: What Is Known (2026)`
  - **Primary keyword:** `turkesterone for fertility` · **Secondary:** turkesterone and sperm, turkesterone male fertility, turkesterone while trying to conceive, does turkesterone affect fertility
  - **Search intent:** man trying to conceive who has seen turkesterone marketed for hormones and wants fertility evidence
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-16 18:52 ICT)
  - **Hero product:** `/products/turkesterone-advanced-formula` (Turkesterone Advanced Formula, $75, in stock 2026-10-16)
  - **Turkesterone Advanced Formula pack label (source of truth):** wellness, nest, PREMIUM, TURKESTERONE, ADVANCED, FORMULA, AMPLIFY, MUSCLE, ENDURANCE, 60, Dietary Supplement, Capsules. No milligram amount and no Supplement Facts panel were read. Do not add one. The capsule badge is the separate lines in product_refs/turkesterone-advanced-formula.label.json. Do not state a milligram amount, a serving count, a different capsule count, or a day-supply.
  - **Collection links (≥2, verify live):** `/collections/mens-essential-collection` (contains it), `/collections/shilajit-wellness-stack` (contains it)
  - **Angle:** Search for human trials of turkesterone and sperm, conception, or fertility. If you cannot fetch one, say that is the state of the evidence. Do not turn a hormone claim from another page into a fertility result. Do not state a milligram amount, a serving count, a capsule count, or a day-supply. Not a fertility treatment. Link the dosing page instead of restating it.
  - **Fan-out answers to cover:** does turkesterone affect sperm; is there a fertility trial; can you take it while trying to conceive; when should you ask a clinician
  - **Evidence to fetch & confirm (claims log):** PubMed or DOI search for turkesterone and fertility or sperm — fetch a paper or state that you found no human trial. No milligram amount.
  - **Link, don't restate:** `/blogs/news/turkesterone-benefits-dosing-whats-real-us-2026`, `/blogs/news/turkesterone-side-effects-4-ingredients-to-check-us-2026`, `/blogs/news/turkesterone-for-women-3-trials-85-men-0-women-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** turkesterone + fertility checked 2026-10-16 against 123 live articles (blog listing + sitemap + Atom + local caches) and all 63 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-18 https://wellnessnest.co/blogs/news/creatine-gummies-price-69-99-in-the-us-2026] **#CA1016-5 — creatine gummies price** — `Creatine Gummies Price: Cost Per Bottle (US 2026)`
  - **Primary keyword:** `creatine gummies price` · **Secondary:** how much do creatine gummies cost, creatine gummies cost per day, are creatine gummies expensive, creatine gummy price
  - **Search intent:** shopper comparing what a bottle of creatine gummies costs before choosing a format
  - **Template:** COMPARISON · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-16 18:52 ICT)
  - **Hero product:** `/products/fusiforce-creatine-gummies` (FusiForce Creatine Gummies, $69.99, in stock 2026-10-16)
  - **Collection links (≥2, verify live):** `/collections/best-seller` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Build a cost table from the live FusiForce PDP only: price, servings the PDP actually prints, and creatine per serving if the panel prints it. Do not invent a count or a gram amount the page does not show. A powder price goes in the table only from a page fetched the same day. Link the where-to-buy and dosage pages instead of restating them.
  - **Fan-out answers to cover:** how much does a bottle of creatine gummies cost; are gummies more expensive than powder; what changes the price per day; is a bigger bottle cheaper
  - **Evidence to fetch & confirm (claims log):** Live FusiForce PDP price and serving facts, re-checked at write time. Any powder price only from a page fetched the same day. No estimated serving count.
  - **Link, don't restate:** `/blogs/news/where-to-buy-creatine-gummies-5-label-checks-us-2026`, `/blogs/news/creatine-gummies-dosage-how-many-a-day-us-2026`, `/blogs/news/creatine-gummies-vs-powder-which-should-you-actually-take`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** creatine + price checked 2026-10-16 against 123 live articles (blog listing + sitemap + Atom + local caches) and all 63 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-18 https://wellnessnest.co/blogs/news/nmn-for-fertility-human-evidence-in-the-us-2026] **#CA1016-6 — nmn for fertility** — `NMN for Fertility: What Human Studies Show (2026)`
  - **Primary keyword:** `nmn for fertility` · **Secondary:** nmn and fertility, nmn ovarian reserve, nmn and sperm, nmn while trying to conceive
  - **Search intent:** person trying to conceive who has seen NMN claimed for fertility and wants human evidence, not animal headlines
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-16 18:52 ICT)
  - **Hero product:** `/products/ageaura-pure-nmn-tmg-nad-complex` (AgeAura Pure NMN + TMG NAD+ Complex, $69.95, in stock 2026-10-16)
  - **Collection links (≥2, verify live):** `/collections/best-seller` twice (browse link — AgeAura Pure NMN + TMG NAD+ Complex is not in it, never claim it is) · no other AgeAura product and no AgeAura collection link (brand_rules)
  - **Angle:** Sort fetched papers into human and animal before you cite any number. If you cannot fetch a human fertility trial, say so and do not borrow an animal result as a human one. AgeAura Pure NMN + TMG NAD+ Complex is not a fertility drug. Do not invent a milligram amount. Link the dosage page instead of restating trial doses.
  - **Fan-out answers to cover:** is there human NMN fertility research; what did animal studies measure; can you take NMN while trying to conceive; what dose did any human study use
  - **Evidence to fetch & confirm (claims log):** PubMed or DOI papers on NMN and fertility, ovarian reserve, or sperm — fetch each one. State human versus animal. No invented milligram.
  - **Link, don't restate:** `/blogs/news/how-much-nmn-per-day-what-trials-used-us-2026`, `/blogs/news/nmn-side-effects-6-checks-before-you-start-us-2026`, `/blogs/news/nmn-for-women-what-the-all-female-trial-missed-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** nmn + fertility checked 2026-10-16 against 123 live articles (blog listing + sitemap + Atom + local caches) and all 63 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1016-7 — vaginal probiotics over 60** — `Vaginal Probiotics Over 60: 5 Checks (US 2026)`
  - **Primary keyword:** `vaginal probiotics over 60` · **Secondary:** vaginal probiotics for older women, probiotics after menopause, vaginal probiotics at 60, probiotics for postmenopausal women
  - **Search intent:** woman over 60, or someone buying for her, checking whether a vaginal probiotic gummy fits that age
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-16 18:52 ICT)
  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh Vaginal Probiotics Gummies, $40.99, in stock 2026-10-16)
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Collection links (≥2, verify live):** `/collections/womens-essentials-collection` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** Five checks for this age: what the vaginal microbiome does after menopause (fetched sources only), whether any oral-probiotic trial enrolled women over 60, medication questions for a clinician, the gummy routine, and when symptoms mean a clinician instead of a supplement. FloraFresh formula from the Supplement Facts label only: Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, which is not a strain those Lactobacillus trials tested (say so). No cure or treatment claims. Link the over-50 page instead of restating it.
  - **Fan-out answers to cover:** do vaginal probiotics change after menopause; were women over 60 in the trials; can you take them with other medication; when should you see a clinician instead
  - **Evidence to fetch & confirm (claims log):** Reviews of the vaginal microbiome after menopause, and any oral probiotic trial that enrolled women over 60 — fetch before citing. FloraFresh strain and CFU from the Supplement Facts label, not the PDP description.
  - **Link, don't restate:** `/blogs/news/vaginal-probiotics-which-strains-actually-work-us-2026`, `/blogs/news/vaginal-probiotics-side-effects-normal-vs-stop-us-2026`, `/blogs/news/florafresh-vs-generic-probiotics-4-strain-facts-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** probiotic + seniors checked 2026-10-16 against 123 live articles (blog listing + sitemap + Atom + local caches) and all 63 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1016-8 — creatine gummies on an empty stomach** — `Creatine Gummies on an Empty Stomach (US 2026)`
  - **Primary keyword:** `creatine gummies on an empty stomach` · **Secondary:** creatine empty stomach, creatine without food, can you take creatine fasted, creatine gummies before breakfast
  - **Search intent:** person who trains fasted or skips breakfast and wants to know if creatine still makes sense without a meal
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-16 18:52 ICT)
  - **Hero product:** `/products/fusiforce-creatine-gummies` (FusiForce Creatine Gummies, $69.99, in stock 2026-10-16)
  - **Collection links (≥2, verify live):** `/collections/best-seller` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Answer the fed-or-fasted question from fetched trials and reviews: what a meal changes, what it does not, and whether a gummy changes that. Do not restate the before-or-after-workout page or the gram dose. Stomach upset stays a link to the side-effects page. No medical claims.
  - **Fan-out answers to cover:** can you take creatine without food; does a meal change absorption; will gummies bother an empty stomach; what if you train before breakfast
  - **Evidence to fetch & confirm (claims log):** Trials or reviews of creatine taken with and without carbohydrate or a meal — fetch each before citing. FusiForce directions from the live PDP only.
  - **Link, don't restate:** `/blogs/news/best-time-to-take-creatine-before-or-after-us-2026`, `/blogs/news/creatine-gummies-dosage-how-many-a-day-us-2026`, `/blogs/news/creatine-gummies-side-effects-4-real-3-myths-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** creatine + fasting checked 2026-10-16 against 123 live articles (blog listing + sitemap + Atom + local caches) and all 63 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1016-9 — how to take nmn** — `How to Take NMN: A Simple Capsule Routine (2026)`
  - **Primary keyword:** `how to take nmn` · **Secondary:** how to use nmn capsules, nmn capsule directions, swallow or dissolve nmn, nmn with water
  - **Search intent:** buyer who already has capsules and wants the daily routine, not another clock-time or dose article
  - **Template:** STORY · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 1 match(es), none targets this primary: How Long Does NMN Take to Work? Week 1 to 12 (US 2026) (2026-10-16 18:52 ICT)
  - **Hero product:** `/products/ageaura-pure-nmn-tmg-nad-complex` (AgeAura Pure NMN + TMG NAD+ Complex, $69.95, in stock 2026-10-16)
  - **Collection links (≥2, verify live):** `/collections/best-seller` twice (browse link — AgeAura Pure NMN + TMG NAD+ Complex is not in it, never claim it is) · no other AgeAura product and no AgeAura collection link (brand_rules)
  - **Angle:** Walk through the capsule routine on the AgeAura Pure NMN + TMG NAD+ Complex label: swallow with water, follow the servings line on the pack label, and what to do if you miss one day. Do not invent a milligram amount. Link the morning-or-night page and the dosage page instead of restating them.
  - **Fan-out answers to cover:** do you swallow NMN capsules; do you take them with water; what if you miss a day; can you open the capsule
  - **Evidence to fetch & confirm (claims log):** Pack-label directions in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json and the live PDP. No invented milligram.
  - **Link, don't restate:** `/blogs/news/when-to-take-nmn-morning-or-night-us-2026`, `/blogs/news/how-much-nmn-per-day-what-trials-used-us-2026`, `/blogs/news/nmn-side-effects-6-checks-before-you-start-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** nmn + how-to-take checked 2026-10-16 against 123 live articles (blog listing + sitemap + Atom + local caches) and all 63 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1016-10 — vaginal probiotics for fertility** — `Vaginal Probiotics for Fertility: The Limits (2026)`
  - **Primary keyword:** `vaginal probiotics for fertility` · **Secondary:** probiotics while trying to conceive, vaginal probiotics and conception, probiotics and fertility, probiotics before pregnancy
  - **Search intent:** woman trying to conceive who has been told a vaginal probiotic might help and wants the limit of that claim
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-16 18:52 ICT)
  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh Vaginal Probiotics Gummies, $40.99, in stock 2026-10-16)
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Collection links (≥2, verify live):** `/collections/womens-essentials-collection` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** This is not the BV page and not the yeast page. Answer whether oral probiotics have been studied around conception, from papers you fetch, and say what they did not measure. FloraFresh formula from the Supplement Facts label only: Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, which is not a strain those Lactobacillus trials tested (say so). Not a fertility treatment. No cure or treatment claims. Link the BV page and the strains page instead of restating them.
  - **Fan-out answers to cover:** can vaginal probiotics help conception; what did the studies measure; can you take them while trying to conceive; when should you see a clinician
  - **Evidence to fetch & confirm (claims log):** Trials or reviews of probiotics and conception or vaginal flora in women trying to conceive — fetch before citing. FloraFresh strain and CFU from the Supplement Facts label, not the PDP description.
  - **Link, don't restate:** `/blogs/news/vaginal-probiotics-which-strains-actually-work-us-2026`, `/blogs/news/probiotics-for-bv-do-they-actually-work-us-2026`, `/blogs/news/yeast-infection-vs-bv-how-to-tell-them-apart-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** probiotic + fertility checked 2026-10-16 against 123 live articles (blog listing + sitemap + Atom + local caches) and all 63 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1016-11 — nmn price** — `NMN Price: What a Bottle Costs in the US (2026)`
  - **Primary keyword:** `nmn price` · **Secondary:** how much does nmn cost, nmn supplement price, is nmn expensive, nmn cost per bottle
  - **Search intent:** US shopper who wants the real bottle price of an NMN supplement after marketplace listings changed
  - **Template:** COMPARISON · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-16 18:52 ICT)
  - **Hero product:** `/products/ageaura-pure-nmn-tmg-nad-complex` (AgeAura Pure NMN + TMG NAD+ Complex, $69.95, in stock 2026-10-16)
  - **Collection links (≥2, verify live):** `/collections/best-seller` twice (browse link — AgeAura Pure NMN + TMG NAD+ Complex is not in it, never claim it is) · no other AgeAura product and no AgeAura collection link (brand_rules)
  - **Angle:** Price the AgeAura Pure NMN + TMG NAD+ Complex from the live PDP and the servings line on its pack label. Do not invent a milligram amount the label file does not list. If the PDP prints a milligram, repeat it only after you fetch that page. Link the where-to-buy page for the FDA story instead of restating it.
  - **Fan-out answers to cover:** how much does a bottle of NMN cost; what does one serving cost; why do NMN prices differ; what should the label show before you pay
  - **Evidence to fetch & confirm (claims log):** Live PDP price, fetched at write time. Serving facts only from the pack label in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json. No invented milligram.
  - **Link, don't restate:** `/blogs/news/where-to-buy-nmn-in-the-us-fda-status-explained-2026`, `/blogs/news/how-much-nmn-per-day-what-trials-used-us-2026`, `/blogs/news/ageaura-nmn-tmg-ingredients-what-each-one-does-us`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** nmn + price checked 2026-10-16 against 123 live articles (blog listing + sitemap + Atom + local caches) and all 63 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-19 https://wellnessnest.co/blogs/news/how-to-take-creatine-gummies-in-the-us-2026] **#CA1016-12 — how to take creatine gummies** — `How to Take Creatine Gummies Each Day (US 2026)`
  - **Primary keyword:** `how to take creatine gummies` · **Secondary:** how to use creatine gummies, creatine gummies directions, chew or swallow creatine gummies, creatine gummies with water
  - **Search intent:** first buyer who has the bottle and wants the physical daily routine, not another dose debate
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-16 18:52 ICT)
  - **Hero product:** `/products/fusiforce-creatine-gummies` (FusiForce Creatine Gummies, $69.99, in stock 2026-10-16)
  - **Collection links (≥2, verify live):** `/collections/best-seller` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** The gummy routine the dosage page and the before-or-after page do not cover: chew them, water, the same time you will remember, rest days included, travel, and what the live label says to do. Link those two pages for the gram amount and the workout clock. Do not restate either one.
  - **Fan-out answers to cover:** do you chew creatine gummies; do you need water with them; what if you miss a day; can you take them on rest days
  - **Evidence to fetch & confirm (claims log):** FusiForce directions from the live PDP. ISSN creatine position stand (Kreider et al. 2017) only for the daily-consistency point — fetch before citing.
  - **Link, don't restate:** `/blogs/news/creatine-gummies-dosage-how-many-a-day-us-2026`, `/blogs/news/best-time-to-take-creatine-before-or-after-us-2026`, `/blogs/news/creatine-gummies-on-rest-days-keep-taking-them-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** creatine + how-to-take checked 2026-10-16 against 123 live articles (blog listing + sitemap + Atom + local caches) and all 63 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-20 https://wellnessnest.co/blogs/news/creatine-gummies-for-fertility-us-evidence] **#CA1016-13 — creatine gummies for fertility** — `Creatine Gummies for Fertility: What We Know (2026)`
  - **Primary keyword:** `creatine gummies for fertility` · **Secondary:** creatine and sperm, creatine male fertility, creatine and pregnancy, does creatine affect fertility
  - **Search intent:** person trying to conceive who has seen creatine mentioned for sperm or pregnancy and wants the actual evidence
  - **Template:** STORY · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-16 18:52 ICT)
  - **Hero product:** `/products/fusiforce-creatine-gummies` (FusiForce Creatine Gummies, $69.99, in stock 2026-10-16)
  - **Collection links (≥2, verify live):** `/collections/best-seller` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Report only studies you fetch. Separate sperm-quality findings from pregnancy findings, and say when a study is small, short, or not in humans. Creatine is not a fertility treatment. Anyone pregnant or trying to conceive should talk to a clinician before starting. Link the side-effects page instead of restating it.
  - **Fan-out answers to cover:** does creatine affect sperm; can you take creatine while trying to conceive; is there pregnancy research; when should you ask a clinician
  - **Evidence to fetch & confirm (claims log):** PubMed or DOI papers on creatine and sperm quality or pregnancy — fetch each paper and cite only what it measured. No unfetched numbers.
  - **Link, don't restate:** `/blogs/news/creatine-gummies-side-effects-4-real-3-myths-us-2026`, `/blogs/news/creatine-gummies-dosage-how-many-a-day-us-2026`, `/blogs/news/creatine-for-women-over-40-what-changes-in-the-us`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** creatine + fertility checked 2026-10-16 against 123 live articles (blog listing + sitemap + Atom + local caches) and all 63 tickets in this file; STEP 0 re-checks at write time

# BATCH 2026-10-17 (refill_tickets.py — ids #CA1017-1…#CA1017-35)

Built by `scripts/refill_tickets.py` at 2026-10-17 14:56 ICT from `templates/article-topic-bank.json` + `board/ideas.csv`
(search volume: No data — GSC/Ads not used). Every ticket passed, against the live store at build time:
brand_rules + `lint_tickets.py` · hero product live and in stock · not a covered topic (header rule 6) ·
not already queued · not live (128 published articles: blog listing + sitemap + Atom + local caches; one article per brand + segment) ·
`topic_fitness.py` strict on primary and title · STEP 0 suggest.json.
A `topic_fitness` REVIEW [covered-segment] verdict is allowed under Kevin's standing greenlight for mined queues (2026-08-13).
A topic is a brief, not copy: source every claim or cut it.

**Rules for this batch:** from the 2026-10-08 batch rules — fan-out answers, a "Where to buy <product> in the US"
section (live price, the ticket's product link only), roster.json byline only (never an invented person or
credential), the logged fact-check pass (`logs/claims/<slug>.md`; delete unconfirmed claims), the brand gate.
Blog 104008483131, publish `--live`. Images: people lane. Run persona_picker.py once. The hero is the picked face plus the real pack unless pick prints NO-FACE. One inline image uses that face. The other inline images have no recognizable face but still show a hand, forearm, or body cropped below the eyes. A no-face image is the fallback for one frame after a face refusal or two QC misses, not a batch-wide ban. The MacBook article plist sets `GENSEO_NO_FACE=0`, and that value does not switch the lane. Prices were read live at build time; re-check the PDP while writing.

- [DONE 2026-10-20 https://wellnessnest.co/blogs/news/how-to-take-vaginal-probiotics-in-the-us] **#CA1017-1 — how to take vaginal probiotics** — `How to Take Vaginal Probiotics (US 2026)`
  - **Primary keyword:** `how to take vaginal probiotics` · **Secondary:** vaginal probiotic gummy routine, chew vaginal probiotics, vaginal probiotics with water, vaginal probiotic directions
  - **Search intent:** buyer who has the pouch and wants the daily chew, not another clock or CFU page
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh Vaginal Probiotics Gummies, $40.99, in stock 2026-10-17)
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Collection links (≥2, verify live):** `/collections/womens-essentials-collection` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** Chew the gummies, water, and the same time you will remember. The best-time page owns the clock; link it. The dosage page owns the count; link it. FloraFresh formula, if you name it, comes from the Supplement Facts label only: Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, sweetened with maltitol and isomalt. Never the PDP description. No cure or treatment claims.
  - **Fan-out answers to cover:** do you chew them; do you take them with water; what if you miss a day; where is the clock-time page
  - **Evidence to fetch & confirm (claims log):** Live PDP directions for the routine. Strain and CFU only from the Supplement Facts label.
  - **Link, don't restate:** `/blogs/news/best-time-to-take-vaginal-probiotics-6-rules-us-2026`, `/blogs/news/vaginal-probiotic-dosage-how-many-cfu-a-day-us-2026`, `/blogs/news/florafresh-gummies-vs-capsules-5-format-facts-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** probiotic + how-to-take checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-20 https://wellnessnest.co/blogs/news/shilajit-on-rest-days-with-food-in-the-us] **#CA1017-2 — shilajit on rest days with food** — `Shilajit on Rest Days, With Food (US 2026)`
  - **Primary keyword:** `shilajit on rest days with food` · **Secondary:** shilajit on off days, shilajit on a day off, shilajit rest day routine, take shilajit every day
  - **Search intent:** person who takes shilajit on gym days and wants the day off answered separately
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/shilasource-himalayan-shilajit-resin` (ShilaSource Himalayan Shilajit Resin, $59.99, in stock 2026-10-17)
  - **ShilaSource Himalayan Shilajit Resin pack label (source of truth):** ShilaSource, Himalayan, Shilajit, Resin, 75, Dietary Supplement, Wellness, Nest, 70% Fulvic Acid*, Lab-Tested for Purity*, 1.06oz (30g), SERVINGS, Servings. No milligram amount and no Supplement Facts panel were read into that file. Do not add one. Do not state a serving count, volume, weight, fulvic percentage, mineral count, or day-supply other than the lines in product_refs/shilasource-himalayan-shilajit-resin.label.json.
  - **Collection links (≥2, verify live):** `/collections/shilajit-wellness-stack` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** The athletes page is the strength trial. This page is the off day: do you still take resin when you are not in the gym, and does a meal change that. If no trial compared rest days, say so. Link the athletes page and the how-to-take page. No milligram and no serving count beyond the pack-label line.
  - **Fan-out answers to cover:** do you take shilajit on days off; does a meal change the off-day routine; what if you only take it on gym days; where is the dissolve method
  - **Evidence to fetch & confirm (claims log):** Any human trial that reported rest-day use — fetch it or say you found none. Pack-label facts only from product_refs/shilasource-himalayan-shilajit-resin.label.json.
  - **Link, don't restate:** `/blogs/news/shilajit-for-athletes-what-a-trial-found-in-the-us`, `/blogs/news/how-to-take-shilajit-resin-dissolve-it-right-us-2026`, `/blogs/news/when-to-take-shilajit-morning-or-night-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** shilajit + rest-days checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-20 https://wellnessnest.co/blogs/news/creatine-gummies-while-traveling-how-much-us-2026] **#CA1017-3 — how much creatine gummies while traveling** — `Creatine Gummies While Traveling: How Much? (US 2026)`
  - **Primary keyword:** `how much creatine gummies while traveling` · **Secondary:** creatine gummies on vacation, creatine gummies on a flight, packing creatine gummies, creatine travel routine
  - **Search intent:** person packing for a US trip who wants the gummy habit to survive the suitcase
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/fusiforce-creatine-gummies` (FusiForce Creatine Gummies, $69.99, in stock 2026-10-17)
  - **Collection links (≥2, verify live):** `/collections/best-seller` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** The home storage page covers shelf life. This page is the trip: carry-on, a hot US car, time zones, and the same chew you already use. Do not restate grams or the expire rules. Link those pages. No medical claims.
  - **Fan-out answers to cover:** do creatine gummies go in a carry-on; does a hot car change them; do you skip days you travel; does the amount change on the road
  - **Evidence to fetch & confirm (claims log):** FusiForce directions from the live PDP. Any travel or stability note only from a page fetched at write time. No invented gram amount.
  - **Link, don't restate:** `/blogs/news/do-creatine-gummies-expire-6-storage-facts-us-2026`, `/blogs/news/creatine-gummies-dosage-how-many-a-day-us-2026`, `/blogs/news/best-time-to-take-creatine-before-or-after-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** creatine + travel checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-21 https://wellnessnest.co/blogs/news/how-much-turkesterone-on-rest-days-in-the-us] **#CA1017-4 — how much turkesterone on rest days** — `Turkesterone on Rest Days: How Much Changes? (2026)`
  - **Primary keyword:** `how much turkesterone on rest days` · **Secondary:** turkesterone on off days, turkesterone on a day off, turkesterone rest day capsules, turkesterone every day
  - **Search intent:** lifter who takes it on gym days and wants the off-day answer
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/turkesterone-advanced-formula` (Turkesterone Advanced Formula, $75, in stock 2026-10-17)
  - **Turkesterone Advanced Formula pack label (source of truth):** wellness, nest, PREMIUM, TURKESTERONE, ADVANCED, FORMULA, AMPLIFY, MUSCLE, ENDURANCE, 60, Dietary Supplement, Capsules. No milligram amount and no Supplement Facts panel were read. Do not add one. The capsule badge is the separate lines in product_refs/turkesterone-advanced-formula.label.json. Do not state a milligram amount, a serving count, a different capsule count, or a day-supply.
  - **Collection links (≥2, verify live):** `/collections/mens-essential-collection` (contains it), `/collections/shilajit-wellness-stack` (contains it)
  - **Angle:** The athletes page is the drug-test guide. This page is the off day. If no study compared gym days and off days, say so. Do not state a milligram, a serving count, a capsule count, or a day-supply. Link the athletes page and the timing page.
  - **Fan-out answers to cover:** do you take it on days off; does the amount change; what if you only take it on gym days; where is the drug-test page
  - **Evidence to fetch & confirm (claims log):** Any human trial that reported rest days — fetch it or say you found none. No milligram.
  - **Link, don't restate:** `/blogs/news/turkesterone-for-athletes-drug-test-guide-us-2026`, `/blogs/news/turkesterone-timing-food-protein-or-fasted-us-2026`, `/blogs/news/how-long-does-turkesterone-take-to-work-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** turkesterone + rest-days checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-21 https://wellnessnest.co/blogs/news/nmn-while-traveling-with-food-5-us-tips] **#CA1017-5 — nmn while traveling with food** — `NMN While Traveling, With Food (US 2026)`
  - **Primary keyword:** `nmn while traveling with food` · **Secondary:** nmn capsules on a flight, nmn on vacation, packing nmn capsules, nmn time zone
  - **Search intent:** traveler with a capsule bottle who wants a simple trip routine
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/ageaura-pure-nmn-tmg-nad-complex` (AgeAura Pure NMN + TMG NAD+ Complex, $69.95, in stock 2026-10-17)
  - **Collection links (≥2, verify live):** `/collections/best-seller` twice (browse link — AgeAura Pure NMN + TMG NAD+ Complex is not in it, never claim it is) · no other AgeAura product and no AgeAura collection link (brand_rules)
  - **Angle:** Capsules in a bag, a missed day, and a time-zone shift. Follow the pack label for how you swallow them. Link the morning-or-night page. Do not invent a milligram. AgeAura Pure NMN + TMG NAD+ Complex only.
  - **Fan-out answers to cover:** do capsules go in a carry-on; what if you miss a day; does the clock change in a new time zone; do you take them with a meal
  - **Evidence to fetch & confirm (claims log):** Pack-label directions and the live PDP. No invented milligram. No invented airport rule. AgeAura Pure NMN + TMG NAD+ Complex only.
  - **Link, don't restate:** `/blogs/news/when-to-take-nmn-morning-or-night-us-2026`, `/blogs/news/nmn-side-effects-6-checks-before-you-start-us-2026`, `/blogs/news/how-much-nmn-per-day-what-trials-used-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** nmn + travel checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-21 https://wellnessnest.co/blogs/news/vaginal-probiotics-on-an-empty-stomach-us-guide-1] **#CA1017-6 — vaginal probiotics on an empty stomach** — `Vaginal Probiotics on an Empty Stomach (US 2026)`
  - **Primary keyword:** `vaginal probiotics on an empty stomach` · **Secondary:** vaginal probiotics without food, vaginal probiotics before breakfast, probiotic gummies before eating, vaginal probiotics with a meal
  - **Search intent:** reader who wants the meal question separated from the morning-or-night question
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh Vaginal Probiotics Gummies, $40.99, in stock 2026-10-17)
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Collection links (≥2, verify live):** `/collections/womens-essentials-collection` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** The best-time page answers morning or night. This page answers with a meal or without one, from probiotic-survival research you fetch. Do not restate the clock. FloraFresh formula, if you name it, comes from the Supplement Facts label only: Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, sweetened with maltitol and isomalt. Never the PDP description. No cure or treatment claims.
  - **Fan-out answers to cover:** does a meal change survival; is an empty stomach required; what if the label is silent; where is the clock-time page
  - **Evidence to fetch & confirm (claims log):** Tompkins et al. 2011, Beneficial Microbes, or a newer fetched paper on probiotic survival with a meal. Confirm before citing.
  - **Link, don't restate:** `/blogs/news/best-time-to-take-vaginal-probiotics-6-rules-us-2026`, `/blogs/news/vaginal-probiotics-side-effects-normal-vs-stop-us-2026`, `/blogs/news/vaginal-probiotic-dosage-how-many-cfu-a-day-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** probiotic + fasting checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-21 https://wellnessnest.co/blogs/news/shilajit-gummies-while-traveling-5-us-tips] **#CA1017-7 — shilajit gummies while traveling with food** — `Shilajit Gummies While Traveling, With Food (2026)`
  - **Primary keyword:** `shilajit gummies while traveling with food` · **Secondary:** shilajit gummies on a flight, shilajit gummies on vacation, travel with shilajit gummies, shilajit gummies in a hotel
  - **Search intent:** traveler who wants shilajit without packing a resin jar
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/premium-himalayan-shilajit-gummies` (Premium Himalayan Shilajit Gummies, $59.99, in stock 2026-10-17)
  - **Collection links (≥2, verify live):** `/collections/shilajit-wellness-stack` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** Gummies on a trip: what you carry, heat in a US car, and keeping one daily habit. Do not restate the resin-versus-gummies page. Link it. Gummies, resin, gold resin, and drops are different products. No milligram the live gummy PDP does not print.
  - **Fan-out answers to cover:** are gummies easier to pack than resin; what does heat do on a trip; do you take them with a meal; what if you miss a travel day
  - **Evidence to fetch & confirm (claims log):** Live gummy PDP for what the label prints. No invented milligram. Resin routine stays a link.
  - **Link, don't restate:** `/blogs/news/shilajit-resin-vs-gummies-which-works-better-us-2026`, `/blogs/news/how-to-take-shilajit-resin-dissolve-it-right-us-2026`, `/blogs/news/how-much-shilajit-per-day-dosage-by-form-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** shilajit + travel checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-22 https://wellnessnest.co/blogs/news/creatine-gummies-cycling-breaks-us-2026] **#CA1017-8 — how much creatine gummies cycling** — `Creatine Gummies Cycling: How Much Changes? (US 2026)`
  - **Primary keyword:** `how much creatine gummies cycling` · **Secondary:** do you cycle creatine, creatine on and off, creatine gummies weeks off, should you stop creatine
  - **Search intent:** lifter who has read that some supplements need weeks off and wants the creatine answer
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/fusiforce-creatine-gummies` (FusiForce Creatine Gummies, $69.99, in stock 2026-10-17)
  - **Collection links (≥2, verify live):** `/collections/best-seller` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Loading is a different page. This asks whether you stop for weeks. Answer from the ISSN creatine position stand if you fetch it: creatine is usually taken every day, not in on-and-off blocks. If you cannot fetch that line, say what you did fetch. Link the loading page and the how-long page. Do not restate the gram amount.
  - **Fan-out answers to cover:** do you take weeks off creatine; is cycling different from loading; what happens if you stop; does a gummy change that
  - **Evidence to fetch & confirm (claims log):** ISSN creatine position stand (Kreider et al. 2017) — fetch before citing. FusiForce directions from the live PDP only.
  - **Link, don't restate:** `/blogs/news/creatine-gummies-loading-phase-is-it-needed-us-2026`, `/blogs/news/how-long-does-creatine-take-to-work-week-by-week-us-2026`, `/blogs/news/creatine-gummies-on-rest-days-keep-taking-them-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** creatine + cycle checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-22 https://wellnessnest.co/blogs/news/turkesterone-while-traveling-us-packing-guide] **#CA1017-9 — how much turkesterone while traveling** — `Turkesterone While Traveling: How Much to Pack? (2026)`
  - **Primary keyword:** `how much turkesterone while traveling` · **Secondary:** turkesterone on a flight, turkesterone on vacation, packing turkesterone, turkesterone hotel routine
  - **Search intent:** lifter packing a jar who should not invent a capsule count for the trip
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/turkesterone-advanced-formula` (Turkesterone Advanced Formula, $75, in stock 2026-10-17)
  - **Turkesterone Advanced Formula pack label (source of truth):** wellness, nest, PREMIUM, TURKESTERONE, ADVANCED, FORMULA, AMPLIFY, MUSCLE, ENDURANCE, 60, Dietary Supplement, Capsules. No milligram amount and no Supplement Facts panel were read. Do not add one. The capsule badge is the separate lines in product_refs/turkesterone-advanced-formula.label.json. Do not state a milligram amount, a serving count, a different capsule count, or a day-supply.
  - **Collection links (≥2, verify live):** `/collections/mens-essential-collection` (contains it), `/collections/shilajit-wellness-stack` (contains it)
  - **Angle:** The jar goes in the bag. You do not split capsules into a count this ticket does not have. Missed days and hotel heat. Do not state a milligram, a serving count, a capsule count, or a day-supply. Link the timing page and the side-effects page.
  - **Fan-out answers to cover:** does the whole jar travel; what if you miss a day; what does hotel heat change; where is the daily routine
  - **Evidence to fetch & confirm (claims log):** Live PDP and the pack-label file. No invented capsule count or temperature.
  - **Link, don't restate:** `/blogs/news/turkesterone-timing-food-protein-or-fasted-us-2026`, `/blogs/news/turkesterone-side-effects-4-ingredients-to-check-us-2026`, `/blogs/news/where-to-buy-turkesterone-in-the-us-what-to-check-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** turkesterone + travel checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-22 https://wellnessnest.co/blogs/news/are-vaginal-probiotics-worth-it-40-99-us-check-2026] **#CA1017-10 — are vaginal probiotics worth it how much** — `Are Vaginal Probiotics Worth It? How Much You Check (2026)`
  - **Primary keyword:** `are vaginal probiotics worth it how much` · **Secondary:** vaginal probiotics review, are vaginal probiotics legit, florafresh honest check, vaginal probiotic gummies review
  - **Search intent:** shopper who wants a straight worth-it check without a fake star rating
  - **Template:** COMPARISON · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh Vaginal Probiotics Gummies, $40.99, in stock 2026-10-17)
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Collection links (≥2, verify live):** `/collections/womens-essentials-collection` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** Not the where-to-buy checklist and not a star-rating roundup. No invented reviews. What the Supplement Facts label lets you verify, and what the live PDP still has to show for the current offer. Link the where-to-buy page. FloraFresh formula, if you name it, comes from the Supplement Facts label only: Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, sweetened with maltitol and isomalt. Never the PDP description. No cure or treatment claims.
  - **Fan-out answers to cover:** what can you verify without a review; what a star rating cannot prove; what do you still read on the product page; where is the buy checklist
  - **Evidence to fetch & confirm (claims log):** Supplement Facts label plus the live PDP offer, fetched at write time. No invented review or rating.
  - **Link, don't restate:** `/blogs/news/where-to-buy-vaginal-probiotics-in-the-us-5-checks-2026`, `/blogs/news/florafresh-gummies-vs-capsules-5-format-facts-us-2026`, `/blogs/news/vaginal-probiotics-which-strains-actually-work-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** probiotic + reviews checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-22 https://wellnessnest.co/blogs/news/turkesterone-and-coffee-with-food-us-2026] **#CA1017-11 — turkesterone and coffee with food** — `Turkesterone and Coffee, With Food (US 2026)`
  - **Primary keyword:** `turkesterone and coffee with food` · **Secondary:** turkesterone with coffee, turkesterone and caffeine, turkesterone morning coffee, turkesterone beside coffee
  - **Search intent:** lifter who takes capsules with morning coffee and wants the evidence
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/turkesterone-advanced-formula` (Turkesterone Advanced Formula, $75, in stock 2026-10-17)
  - **Turkesterone Advanced Formula pack label (source of truth):** wellness, nest, PREMIUM, TURKESTERONE, ADVANCED, FORMULA, AMPLIFY, MUSCLE, ENDURANCE, 60, Dietary Supplement, Capsules. No milligram amount and no Supplement Facts panel were read. Do not add one. The capsule badge is the separate lines in product_refs/turkesterone-advanced-formula.label.json. Do not state a milligram amount, a serving count, a different capsule count, or a day-supply.
  - **Collection links (≥2, verify live):** `/collections/mens-essential-collection` (contains it), `/collections/shilajit-wellness-stack` (contains it)
  - **Angle:** Lifters often take capsules with morning coffee. Fetch any human evidence before you claim an interaction. If you find none, say so. Do not state a milligram, a serving count, a capsule count, or a day-supply. Link the timing page. No stimulant claim.
  - **Fan-out answers to cover:** can capsules go with coffee; is there an interaction study; does a meal change it; where is the timing page
  - **Evidence to fetch & confirm (claims log):** PubMed or DOI search for turkesterone and caffeine — fetch a paper or state that you found none. No milligram.
  - **Link, don't restate:** `/blogs/news/turkesterone-timing-food-protein-or-fasted-us-2026`, `/blogs/news/turkesterone-side-effects-4-ingredients-to-check-us-2026`, `/blogs/news/turkesterone-benefits-dosing-whats-real-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** turkesterone + caffeine checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-22 https://wellnessnest.co/blogs/news/nmn-on-rest-days-take-it-with-food-us] **#CA1017-12 — nmn on rest days with food** — `NMN Capsules on a Day Off, With Food (US 2026)`
  - **Primary keyword:** `nmn on rest days with food` · **Secondary:** nmn on off days, nmn when you skip the gym, nmn rest day capsules, take nmn every day
  - **Search intent:** person who times NMN around workouts and wants the day off
  - **Template:** STORY · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/ageaura-pure-nmn-tmg-nad-complex` (AgeAura Pure NMN + TMG NAD+ Complex, $69.95, in stock 2026-10-17)
  - **Collection links (≥2, verify live):** `/collections/best-seller` twice (browse link — AgeAura Pure NMN + TMG NAD+ Complex is not in it, never claim it is) · no other AgeAura product and no AgeAura collection link (brand_rules)
  - **Angle:** The exercise page covers workout timing. This page is the day you do not train. Link that page and the morning-or-night page. AgeAura Pure NMN + TMG NAD+ Complex only. Do not invent a milligram. Do not restate the dose page.
  - **Fan-out answers to cover:** do you take NMN on days off; does a meal matter more on a rest day; what if you only take it on gym days; where is the clock-time page
  - **Evidence to fetch & confirm (claims log):** Any trial that reported non-training days — fetch it or say you found none. No invented milligram. AgeAura Pure NMN + TMG NAD+ Complex only.
  - **Link, don't restate:** `/blogs/news/nmn-and-exercise-before-or-after-a-workout-us-2026`, `/blogs/news/when-to-take-nmn-morning-or-night-us-2026`, `/blogs/news/how-much-nmn-per-day-what-trials-used-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** nmn + rest-days checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-23 https://wellnessnest.co/blogs/news/creatine-gummies-worth-it-us-2026-check] **#CA1017-13 — are creatine gummies worth it how much** — `Are Creatine Gummies Worth It? How Much You Get (2026)`
  - **Primary keyword:** `are creatine gummies worth it how much` · **Secondary:** creatine gummies review, are creatine gummies legit, creatine gummies honest check, fusiforce creatine gummies review
  - **Search intent:** shopper who wants a straight answer before paying for gummies instead of powder
  - **Template:** COMPARISON · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/fusiforce-creatine-gummies` (FusiForce Creatine Gummies, $69.99, in stock 2026-10-17)
  - **Collection links (≥2, verify live):** `/collections/best-seller` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Not a price page and not the powder comparison. Compare what a shopper can verify on the live FusiForce PDP (creatine monohydrate named, and only the amounts the panel prints) with what a review page often skips. No invented star rating or buyer quotes. Link the powder page and the where-to-buy page.
  - **Fan-out answers to cover:** what can you verify on the label; what a review cannot prove; how do gummies differ from powder; what should you ignore in ads
  - **Evidence to fetch & confirm (claims log):** Live FusiForce PDP, fetched at write time. Any third-party gummy test only from a fetched report, and only if that report names the product.
  - **Link, don't restate:** `/blogs/news/creatine-gummies-vs-powder-which-should-you-actually-take`, `/blogs/news/where-to-buy-creatine-gummies-5-label-checks-us-2026`, `/blogs/news/creatine-gummies-dosage-how-many-a-day-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** creatine + reviews checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-23 https://wellnessnest.co/blogs/news/nmn-storage-with-food-5-us-rules] **#CA1017-14 — nmn storage with food** — `Where Should NMN Capsules Sit, With Food Nearby? (2026)`
  - **Primary keyword:** `nmn storage with food` · **Secondary:** how to store nmn, nmn bottle heat, nmn shelf life, nmn in the kitchen
  - **Search intent:** bottle owner deciding where capsules should sit at home
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/ageaura-pure-nmn-tmg-nad-complex` (AgeAura Pure NMN + TMG NAD+ Complex, $69.95, in stock 2026-10-17)
  - **Collection links (≥2, verify live):** `/collections/best-seller` twice (browse link — AgeAura Pure NMN + TMG NAD+ Complex is not in it, never claim it is) · no other AgeAura product and no AgeAura collection link (brand_rules)
  - **Angle:** Bottle closed, heat, and the date printed on the pack if there is one. Do not invent an expiry. Link the morning-or-night page for the routine. Do not invent a milligram. AgeAura Pure NMN + TMG NAD+ Complex only.
  - **Fan-out answers to cover:** does the bottle need a fridge; what does heat do; can it sit near food; what if the pack prints a date
  - **Evidence to fetch & confirm (claims log):** Live PDP and the pack-label file only. No invented expiry or temperature. AgeAura Pure NMN + TMG NAD+ Complex only.
  - **Link, don't restate:** `/blogs/news/when-to-take-nmn-morning-or-night-us-2026`, `/blogs/news/nmn-side-effects-6-checks-before-you-start-us-2026`, `/blogs/news/how-much-nmn-per-day-what-trials-used-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** nmn + storage checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-23 https://wellnessnest.co/blogs/news/shilajit-and-coffee-with-food-us-guide] **#CA1017-15 — shilajit and coffee with food** — `Shilajit and Coffee, With Food (US 2026)`
  - **Primary keyword:** `shilajit and coffee with food` · **Secondary:** shilajit with coffee, shilajit and caffeine, shilajit in the morning with coffee, shilajit beside coffee
  - **Search intent:** morning coffee drinker deciding whether resin belongs in the same cup routine
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/shilasource-himalayan-shilajit-resin` (ShilaSource Himalayan Shilajit Resin, $59.99, in stock 2026-10-17)
  - **ShilaSource Himalayan Shilajit Resin pack label (source of truth):** ShilaSource, Himalayan, Shilajit, Resin, 75, Dietary Supplement, Wellness, Nest, 70% Fulvic Acid*, Lab-Tested for Purity*, 1.06oz (30g), SERVINGS, Servings. No milligram amount and no Supplement Facts panel were read into that file. Do not add one. Do not state a serving count, volume, weight, fulvic percentage, mineral count, or day-supply other than the lines in product_refs/shilasource-himalayan-shilajit-resin.label.json.
  - **Collection links (≥2, verify live):** `/collections/shilajit-wellness-stack` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Morning coffee plus resin is a common habit, not a studied pairing. Say what you could and could not fetch. Link the morning-or-night page for the clock, and do not restate it. Drops are a different product; do not borrow that label. No milligram beyond the resin pack-label line. Do not claim a caffeine amount.
  - **Fan-out answers to cover:** can resin go with morning coffee; does coffee change the routine; is there any caffeine in the resin; what if your stomach objects
  - **Evidence to fetch & confirm (claims log):** Any fetched paper on shilajit and caffeine. If none, say so. Pack-label line only. No invented caffeine amount.
  - **Link, don't restate:** `/blogs/news/when-to-take-shilajit-morning-or-night-us-2026`, `/blogs/news/how-to-take-shilajit-resin-dissolve-it-right-us-2026`, `/blogs/news/shilajit-side-effects-7-signs-to-watch-for-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** shilajit + caffeine checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-23 https://wellnessnest.co/blogs/news/how-to-take-turkesterone-in-the-us-2026] **#CA1017-16 — how to take turkesterone** — `How to Take Turkesterone Capsules (US 2026)`
  - **Primary keyword:** `how to take turkesterone` · **Secondary:** turkesterone capsule routine, swallow turkesterone, turkesterone with water, turkesterone directions
  - **Search intent:** buyer who has the jar and wants the physical routine, not another clock or cost page
  - **Template:** STORY · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 1 match(es), none targets this primary: How Long Does Turkesterone Take to Work? (US 2026) (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/turkesterone-advanced-formula` (Turkesterone Advanced Formula, $75, in stock 2026-10-17)
  - **Turkesterone Advanced Formula pack label (source of truth):** wellness, nest, PREMIUM, TURKESTERONE, ADVANCED, FORMULA, AMPLIFY, MUSCLE, ENDURANCE, 60, Dietary Supplement, Capsules. No milligram amount and no Supplement Facts panel were read. Do not add one. The capsule badge is the separate lines in product_refs/turkesterone-advanced-formula.label.json. Do not state a milligram amount, a serving count, a different capsule count, or a day-supply.
  - **Collection links (≥2, verify live):** `/collections/mens-essential-collection` (contains it), `/collections/shilajit-wellness-stack` (contains it)
  - **Angle:** Swallow with water, the same time you will remember, and what the jar front actually is. Do not state a milligram, a serving count, a capsule count, or a day-supply. The pack-label line is the only label fact. Link the timing page and the dosing page instead of restating them.
  - **Fan-out answers to cover:** do you swallow the capsules; do you take them with water; what if you miss one; where is the clock-time page
  - **Evidence to fetch & confirm (claims log):** Live PDP directions and product_refs/turkesterone-advanced-formula.label.json. No milligram and no extra capsule count beyond the split badge the ticket line prints.
  - **Link, don't restate:** `/blogs/news/turkesterone-timing-food-protein-or-fasted-us-2026`, `/blogs/news/turkesterone-benefits-dosing-whats-real-us-2026`, `/blogs/news/turkesterone-side-effects-4-ingredients-to-check-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** turkesterone + how-to-take checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-24 https://wellnessnest.co/blogs/news/is-nmn-worth-it-with-food-us-check] **#CA1017-17 — is nmn worth it with food** — `Is NMN Worth It, With Food? (US 2026)`
  - **Primary keyword:** `is nmn worth it with food` · **Secondary:** nmn review, is nmn legit, nmn honest check, is the nmn tmg complex worth it
  - **Search intent:** US shopper who wants a straight worth-it check after marketplace listings changed
  - **Template:** COMPARISON · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/ageaura-pure-nmn-tmg-nad-complex` (AgeAura Pure NMN + TMG NAD+ Complex, $69.95, in stock 2026-10-17)
  - **Collection links (≥2, verify live):** `/collections/best-seller` twice (browse link — AgeAura Pure NMN + TMG NAD+ Complex is not in it, never claim it is) · no other AgeAura product and no AgeAura collection link (brand_rules)
  - **Angle:** Not the ingredients page and not the where-to-buy regulatory story. What a US shopper can check on the live AgeAura Pure NMN + TMG NAD+ Complex only PDP, and what human trials have not shown. No invented reviews or star ratings. Link those two pages. Do not invent a milligram.
  - **Fan-out answers to cover:** what can you verify on the bottle; what trials have not shown; is a meal part of the decision; where is the regulatory story
  - **Evidence to fetch & confirm (claims log):** Live PDP for AgeAura Pure NMN + TMG NAD+ Complex only. Human trials only from papers you fetch. No invented review.
  - **Link, don't restate:** `/blogs/news/where-to-buy-nmn-in-the-us-fda-status-explained-2026`, `/blogs/news/ageaura-nmn-tmg-ingredients-what-each-one-does-us`, `/blogs/news/nmn-side-effects-6-checks-before-you-start-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** nmn + reviews checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [DONE 2026-10-24 https://wellnessnest.co/blogs/news/creatine-gummies-ingredients-us-label-guide] **#CA1017-18 — creatine gummies ingredients how much** — `Creatine Gummies Ingredients: How Much Is Named (2026)`
  - **Primary keyword:** `creatine gummies ingredients how much` · **Secondary:** what is in creatine gummies, creatine monohydrate gummies ingredients, fusiforce ingredients, creatine gummies label
  - **Search intent:** label reader who wants the ingredient list, not another shopping checklist
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/fusiforce-creatine-gummies` (FusiForce Creatine Gummies, $69.99, in stock 2026-10-17)
  - **Collection links (≥2, verify live):** `/collections/best-seller` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Read the live panel: creatine monohydrate and whatever else the PDP actually prints. Do not invent a gram amount. Link the dosage page for the daily amount and the where-to-buy page for the five label checks. This page is the ingredient list, not the shopping checklist.
  - **Fan-out answers to cover:** is the creatine monohydrate; what else is on the panel; what if the front and the panel disagree; where is the daily amount explained
  - **Evidence to fetch & confirm (claims log):** FusiForce ingredient list from the live PDP only. No invented gram, count, or sweetener the page does not print.
  - **Link, don't restate:** `/blogs/news/creatine-gummies-dosage-how-many-a-day-us-2026`, `/blogs/news/where-to-buy-creatine-gummies-5-label-checks-us-2026`, `/blogs/news/creatine-gummies-side-effects-4-real-3-myths-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** creatine + ingredients checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-19 — nmn loading with food** — `NMN Loading Phase, With Food or Not? (2026)`
  - **Primary keyword:** `nmn loading with food` · **Secondary:** nmn loading week, nmn bigger start, do you load nmn, nmn front load
  - **Search intent:** reader who saw a loading week claimed and wants the trial schedule
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/ageaura-pure-nmn-tmg-nad-complex` (AgeAura Pure NMN + TMG NAD+ Complex, $69.95, in stock 2026-10-17)
  - **Collection links (≥2, verify live):** `/collections/best-seller` twice (browse link — AgeAura Pure NMN + TMG NAD+ Complex is not in it, never claim it is) · no other AgeAura product and no AgeAura collection link (brand_rules)
  - **Angle:** If the human trials you fetch used a steady amount rather than a front-load, say that and link the dosage page. Do not invent a loading protocol or a milligram. AgeAura Pure NMN + TMG NAD+ Complex only. It is not a drug.
  - **Fan-out answers to cover:** did human trials use a bigger start; is a loading week required; where is the steady amount; does a meal change the start
  - **Evidence to fetch & confirm (claims log):** Human NMN trials you fetch — describe the schedule. If none used a load, say so. No invented milligram. AgeAura Pure NMN + TMG NAD+ Complex only.
  - **Link, don't restate:** `/blogs/news/how-much-nmn-per-day-what-trials-used-us-2026`, `/blogs/news/how-long-does-nmn-take-to-work-week-1-to-12-us-2026`, `/blogs/news/nmn-side-effects-6-checks-before-you-start-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** nmn + loading checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-20 — shilajit cycling with food** — `Do You Cycle Shilajit? With Food Rules (2026)`
  - **Primary keyword:** `shilajit cycling with food` · **Secondary:** shilajit on and off, shilajit weeks off, should you cycle shilajit, shilajit breaks
  - **Search intent:** user who has been taking resin for months and wonders whether to pause
  - **Template:** COMPARISON · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/shilasource-himalayan-shilajit-resin` (ShilaSource Himalayan Shilajit Resin, $59.99, in stock 2026-10-17)
  - **ShilaSource Himalayan Shilajit Resin pack label (source of truth):** ShilaSource, Himalayan, Shilajit, Resin, 75, Dietary Supplement, Wellness, Nest, 70% Fulvic Acid*, Lab-Tested for Purity*, 1.06oz (30g), SERVINGS, Servings. No milligram amount and no Supplement Facts panel were read into that file. Do not add one. Do not state a serving count, volume, weight, fulvic percentage, mineral count, or day-supply other than the lines in product_refs/shilasource-himalayan-shilajit-resin.label.json.
  - **Collection links (≥2, verify live):** `/collections/shilajit-wellness-stack` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** The how-long page asks how many weeks people take it. This page asks whether you plan weeks off. If you cannot fetch a trial that used an on-and-off schedule, say that is the evidence. Link the how-long page. No milligram beyond the pack-label line.
  - **Fan-out answers to cover:** do you need weeks off; is a pause different from stopping; what did trials actually do; does a meal change a pause
  - **Evidence to fetch & confirm (claims log):** Any human shilajit trial schedule you fetch. If none used a planned pause, say so. Pack-label line only for the resin.
  - **Link, don't restate:** `/blogs/news/for-how-long-can-we-take-shilajit`, `/blogs/news/how-much-shilajit-per-day-dosage-by-form-us-2026`, `/blogs/news/shilajit-side-effects-7-signs-to-watch-for-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** shilajit + cycle checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-21 — how much vaginal probiotics and alcohol** — `Vaginal Probiotics and Alcohol: How Much Matters? (2026)`
  - **Primary keyword:** `how much vaginal probiotics and alcohol` · **Secondary:** probiotics and drinking, vaginal probiotics after alcohol, probiotics and wine, alcohol and vaginal flora
  - **Search intent:** woman who drinks and wants the limit of any probiotic claim around alcohol
  - **Template:** STORY · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh Vaginal Probiotics Gummies, $40.99, in stock 2026-10-17)
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Collection links (≥2, verify live):** `/collections/womens-essentials-collection` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** Not a treatment for anything alcohol does. Fetch papers on alcohol and the vaginal microbiome before citing a number. The gummy organism may not be the one those papers used; say so if it is not. Link the side-effects page. FloraFresh formula, if you name it, comes from the Supplement Facts label only: Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, sweetened with maltitol and isomalt. Never the PDP description. No cure or treatment claims.
  - **Fan-out answers to cover:** is there a human study; does the gummy match the papers; is it a next-morning fix; when should you see a clinician
  - **Evidence to fetch & confirm (claims log):** Fetched papers on alcohol and the vaginal microbiome only. No treatment claim.
  - **Link, don't restate:** `/blogs/news/vaginal-probiotics-side-effects-normal-vs-stop-us-2026`, `/blogs/news/vaginal-probiotics-which-strains-actually-work-us-2026`, `/blogs/news/probiotics-for-bv-do-they-actually-work-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** probiotic + alcohol checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-22 — how much heat turkesterone storage** — `Turkesterone Storage: How Much Heat Matters? (2026)`
  - **Primary keyword:** `how much heat turkesterone storage` · **Secondary:** how to store turkesterone, turkesterone jar heat, turkesterone shelf life, turkesterone in a hot car
  - **Search intent:** jar owner deciding where capsules should sit in a hot US kitchen or car
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/turkesterone-advanced-formula` (Turkesterone Advanced Formula, $75, in stock 2026-10-17)
  - **Turkesterone Advanced Formula pack label (source of truth):** wellness, nest, PREMIUM, TURKESTERONE, ADVANCED, FORMULA, AMPLIFY, MUSCLE, ENDURANCE, 60, Dietary Supplement, Capsules. No milligram amount and no Supplement Facts panel were read. Do not add one. The capsule badge is the separate lines in product_refs/turkesterone-advanced-formula.label.json. Do not state a milligram amount, a serving count, a different capsule count, or a day-supply.
  - **Collection links (≥2, verify live):** `/collections/mens-essential-collection` (contains it), `/collections/shilajit-wellness-stack` (contains it)
  - **Angle:** Closed jar, a hot US car, and a bathroom cabinet. Do not invent a temperature or a shelf-life the label file does not list. Do not state a milligram, a serving count, a capsule count, or a day-supply. Link the side-effects page for stop signs only.
  - **Fan-out answers to cover:** does the jar need a fridge; what does a hot car change; what does the label say about storage; what if the capsules soften
  - **Evidence to fetch & confirm (claims log):** Live PDP and product_refs/turkesterone-advanced-formula.label.json. No invented temperature.
  - **Link, don't restate:** `/blogs/news/turkesterone-side-effects-4-ingredients-to-check-us-2026`, `/blogs/news/where-to-buy-turkesterone-in-the-us-what-to-check-2026`, `/blogs/news/turkesterone-benefits-dosing-whats-real-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** turkesterone + storage checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-23 — nmn for hair with food** — `NMN and Hair Claims, Taken With Food (US 2026)`
  - **Primary keyword:** `nmn for hair with food` · **Secondary:** nmn hair growth, nmn and hair, does nmn help hair, nmn hair claims
  - **Search intent:** reader who has seen hair claims and wants human papers kept apart from animal headlines
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/ageaura-pure-nmn-tmg-nad-complex` (AgeAura Pure NMN + TMG NAD+ Complex, $69.95, in stock 2026-10-17)
  - **Collection links (≥2, verify live):** `/collections/best-seller` twice (browse link — AgeAura Pure NMN + TMG NAD+ Complex is not in it, never claim it is) · no other AgeAura product and no AgeAura collection link (brand_rules)
  - **Angle:** Separate human papers from animal papers before any number. If you cannot fetch a human hair trial, say so. Not a hair treatment. Link the side-effects page. Do not invent a milligram. AgeAura Pure NMN + TMG NAD+ Complex only.
  - **Fan-out answers to cover:** is there a human hair trial; what did animal papers measure; does a meal change the claim; when should you ignore the ad
  - **Evidence to fetch & confirm (claims log):** PubMed or DOI papers on NMN and hair — fetch each one and label human or animal. No borrowed result. AgeAura Pure NMN + TMG NAD+ Complex only.
  - **Link, don't restate:** `/blogs/news/nmn-side-effects-6-checks-before-you-start-us-2026`, `/blogs/news/nmn-for-women-what-the-all-female-trial-missed-us-2026`, `/blogs/news/how-much-nmn-per-day-what-trials-used-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** nmn + hair checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-24 — shilajit and alcohol with food** — `Shilajit and Alcohol, With Food (US 2026)`
  - **Primary keyword:** `shilajit and alcohol with food` · **Secondary:** shilajit and drinking, shilajit hangover, shilajit after alcohol, can you take shilajit with alcohol
  - **Search intent:** adult who drinks and wants to know if resin the same day is a studied idea
  - **Template:** STORY · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/shilasource-himalayan-shilajit-resin` (ShilaSource Himalayan Shilajit Resin, $59.99, in stock 2026-10-17)
  - **ShilaSource Himalayan Shilajit Resin pack label (source of truth):** ShilaSource, Himalayan, Shilajit, Resin, 75, Dietary Supplement, Wellness, Nest, 70% Fulvic Acid*, Lab-Tested for Purity*, 1.06oz (30g), SERVINGS, Servings. No milligram amount and no Supplement Facts panel were read into that file. Do not add one. Do not state a serving count, volume, weight, fulvic percentage, mineral count, or day-supply other than the lines in product_refs/shilasource-himalayan-shilajit-resin.label.json.
  - **Collection links (≥2, verify live):** `/collections/shilajit-wellness-stack` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** What fetched research says about shilajit and alcohol, and what it does not say. A meal is not a hangover fix. Not a treatment. Link the side-effects page. No milligram beyond the pack-label line.
  - **Fan-out answers to cover:** is there a human study; does a meal change anything; is it a hangover aid; when should you skip it
  - **Evidence to fetch & confirm (claims log):** PubMed or DOI search on shilajit and alcohol — fetch a paper or state that you found none. No treatment claim.
  - **Link, don't restate:** `/blogs/news/shilajit-side-effects-7-signs-to-watch-for-us-2026`, `/blogs/news/how-to-take-shilajit-resin-dissolve-it-right-us-2026`, `/blogs/news/when-to-take-shilajit-morning-or-night-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** shilajit + alcohol checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-25 — how much vaginal probiotic storage** — `Vaginal Probiotic Gummies at Home: How Much Heat? (2026)`
  - **Primary keyword:** `how much vaginal probiotic storage` · **Secondary:** do probiotic gummies need a fridge, vaginal probiotic shelf life, probiotic gummies in a cupboard, probiotic gummies heat
  - **Search intent:** pouch owner deciding between a cupboard and a fridge at home
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh Vaginal Probiotics Gummies, $40.99, in stock 2026-10-17)
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Collection links (≥2, verify live):** `/collections/womens-essentials-collection` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** Home shelf, not the suitcase. The travel page owns planes and hotels; link it. Do not invent a fridge rule the PDP does not print. FloraFresh formula, if you name it, comes from the Supplement Facts label only: Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, sweetened with maltitol and isomalt. Never the PDP description. No cure or treatment claims.
  - **Fan-out answers to cover:** does the pouch need a fridge; what does heat do at home; how is that different from a trip; what if the gummies soften
  - **Evidence to fetch & confirm (claims log):** Live PDP storage line, if it prints one. If it does not, say so. No invented temperature.
  - **Link, don't restate:** `/blogs/news/vaginal-probiotics-while-traveling-7-us-rules`, `/blogs/news/florafresh-gummies-vs-capsules-5-format-facts-us-2026`, `/blogs/news/vaginal-probiotics-side-effects-normal-vs-stop-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** probiotic + storage checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-26 — how much turkesterone loading** — `Turkesterone Loading: How Much the Start Changes? (2026)`
  - **Primary keyword:** `how much turkesterone loading` · **Secondary:** turkesterone loading phase, turkesterone bigger start, do you load turkesterone, turkesterone front load
  - **Search intent:** lifter who saw a loading week claimed and wants the trial schedule
  - **Template:** COMPARISON · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/turkesterone-advanced-formula` (Turkesterone Advanced Formula, $75, in stock 2026-10-17)
  - **Turkesterone Advanced Formula pack label (source of truth):** wellness, nest, PREMIUM, TURKESTERONE, ADVANCED, FORMULA, AMPLIFY, MUSCLE, ENDURANCE, 60, Dietary Supplement, Capsules. No milligram amount and no Supplement Facts panel were read. Do not add one. The capsule badge is the separate lines in product_refs/turkesterone-advanced-formula.label.json. Do not state a milligram amount, a serving count, a different capsule count, or a day-supply.
  - **Collection links (≥2, verify live):** `/collections/mens-essential-collection` (contains it), `/collections/shilajit-wellness-stack` (contains it)
  - **Angle:** The cycle page covers planned pauses. This page asks whether a bigger start exists. If you cannot fetch a trial that used a load, say so. Do not invent one. Do not state a milligram, a serving count, a capsule count, or a day-supply. Link the cycle page.
  - **Fan-out answers to cover:** did any trial use a bigger start; is a loading week required; how is that different from a pause; what should you not invent
  - **Evidence to fetch & confirm (claims log):** Human turkesterone trials you fetch — describe the schedule or say you found no loading protocol. No milligram.
  - **Link, don't restate:** `/blogs/news/turkesterone-cycle-do-you-need-breaks-us-2026`, `/blogs/news/how-long-does-turkesterone-take-to-work-us-2026`, `/blogs/news/turkesterone-benefits-dosing-whats-real-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** turkesterone + loading checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-27 — how much else with vaginal probiotics together** — `Vaginal Probiotics Together: How Much Else? (2026)`
  - **Primary keyword:** `how much else with vaginal probiotics together` · **Secondary:** vaginal probiotics with other supplements, probiotics same day as vitamins, can you combine vaginal probiotics, probiotic gummies with a multivitamin
  - **Search intent:** woman who already takes other supplements and wants the same-day limit
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh Vaginal Probiotics Gummies, $40.99, in stock 2026-10-17)
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Collection links (≥2, verify live):** `/collections/womens-essentials-collection` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** Other supplements the same day: what to ask a clinician about, and what was not studied as a combination. Link the antibiotics page for that case. Do not name an amount for a product this ticket does not sell. FloraFresh formula, if you name it, comes from the Supplement Facts label only: Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, sweetened with maltitol and isomalt. Never the PDP description. No cure or treatment claims.
  - **Fan-out answers to cover:** can you take them with a multivitamin; what was not studied together; where is the antibiotics page; when should you ask a clinician
  - **Evidence to fetch & confirm (claims log):** Fetched papers on combining oral probiotics with other supplements, or say you found none. No invented combination result.
  - **Link, don't restate:** `/blogs/news/probiotics-after-antibiotics-for-women-when-to-start-us`, `/blogs/news/vaginal-probiotics-side-effects-normal-vs-stop-us-2026`, `/blogs/news/best-time-to-take-vaginal-probiotics-6-rules-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** probiotic + stack checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-28 — fake creatine gummies how much** — `Fake Creatine Gummies: How Much Is Missing? (2026)`
  - **Primary keyword:** `fake creatine gummies how much` · **Secondary:** are creatine gummies real, under filled creatine gummies, creatine gummies counterfeit, real or fake creatine gummies
  - **Search intent:** shopper who heard some gummies contain less creatine than the front implies
  - **Template:** STORY · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/fusiforce-creatine-gummies` (FusiForce Creatine Gummies, $69.99, in stock 2026-10-17)
  - **Collection links (≥2, verify live):** `/collections/best-seller` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Some gummies have been reported under-filled. Cite that only from a report you fetch, and never say FusiForce was in that report unless the report says so. Give the checks a US shopper can do on a label. Link the where-to-buy page instead of restating it. Do not lead on a certificate.
  - **Fan-out answers to cover:** how can a gummy be under-filled; what does the panel have to name; was FusiForce in any public test; what should you do if the label is vague
  - **Evidence to fetch & confirm (claims log):** A fetched primary report of creatine gummy content, only if you can open it. Live FusiForce PDP for what this product prints. No invented test result.
  - **Link, don't restate:** `/blogs/news/where-to-buy-creatine-gummies-5-label-checks-us-2026`, `/blogs/news/creatine-gummies-vs-powder-which-should-you-actually-take`, `/blogs/news/creatine-gummies-dosage-how-many-a-day-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** creatine + authenticity checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-29 — vaginal probiotic ingredients how much** — `Vaginal Probiotic Ingredients: How Much to Read (2026)`
  - **Primary keyword:** `vaginal probiotic ingredients how much` · **Secondary:** what is in vaginal probiotic gummies, florafresh label panel, vaginal probiotic gummy ingredients, probiotic gummies sweetener
  - **Search intent:** label reader who wants the rest of the panel, not another organism roundup
  - **Template:** COMPARISON · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh Vaginal Probiotics Gummies, $40.99, in stock 2026-10-17)
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Collection links (≥2, verify live):** `/collections/womens-essentials-collection` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** The organism page owns which organisms were studied. Link it. This page is the rest of the Supplement Facts label: the named organism, the CFU line, vitamin C, pineapple fruit powder, and the sweeteners. Never the PDP description. FloraFresh formula, if you name it, comes from the Supplement Facts label only: Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, sweetened with maltitol and isomalt. Never the PDP description. No cure or treatment claims.
  - **Fan-out answers to cover:** what else is on the panel; where is the organism page; what sweetener is named; what should you not copy from the product description
  - **Evidence to fetch & confirm (claims log):** Supplement Facts label only for formula facts. Live PDP for the offer, not the formula.
  - **Link, don't restate:** `/blogs/news/vaginal-probiotics-which-strains-actually-work-us-2026`, `/blogs/news/florafresh-gummies-vs-capsules-5-format-facts-us-2026`, `/blogs/news/vaginal-probiotic-dosage-how-many-cfu-a-day-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** probiotic + ingredients checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-30 — shilajit storage with food** — `Shilajit Storage at Home, With Food Nearby (2026)`
  - **Primary keyword:** `shilajit storage with food` · **Secondary:** how to store shilajit resin, shilajit jar heat, shilajit shelf life, shilajit in the kitchen
  - **Search intent:** jar owner who wants to know where gold resin should sit at home
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/pure-shilajit-gold-resin` (Pure Shilajit Gold Resin, $75, in stock 2026-10-17)
  - **Pure Shilajit Gold Resin pack label (source of truth):** wellness, nest, Himalayan, Shilajit, 75% Fulvic, Lab-Tested, Acid, Pure Shilajit Gold Resin, 1.06 oz (30g) - 75 servings, Dietary Supplements. No milligram amount was read. Do not add one. Do not state a serving count, volume, weight, or day-supply other than the serving line in product_refs/pure-shilajit-gold-resin.label.json.
  - **Collection links (≥2, verify live):** `/collections/shilajit-wellness-stack` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Gold resin in a jar: lid on, heat, and keeping it out of strong kitchen smells. Do not invent a shelf-life, a temperature, or a milligram. The pack-label line is the only serving fact. Link the how-to-take page for dissolving. Gummies and drops are different products.
  - **Fan-out answers to cover:** does the jar need a fridge; what does heat do to resin; can it sit near food; what does the label actually say about servings
  - **Evidence to fetch & confirm (claims log):** Live gold-resin PDP and product_refs/pure-shilajit-gold-resin.label.json only. No invented temperature or shelf-life.
  - **Link, don't restate:** `/blogs/news/how-to-take-shilajit-resin-dissolve-it-right-us-2026`, `/blogs/news/shilajit-gold-resin-review-is-75-worth-it-us-2026`, `/blogs/news/how-much-shilajit-per-day-dosage-by-form-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** shilajit + storage checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-31 — vaginal probiotics for athletes** — `Vaginal Probiotics for Athletes (US 2026)`
  - **Primary keyword:** `vaginal probiotics for athletes` · **Secondary:** probiotics for active women, vaginal probiotics and exercise, athlete probiotic gummies, probiotic gummies on gym days
  - **Search intent:** woman who trains and wants to know whether the gummy routine changes
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/florafresh-vaginal-probiotics-gummies` (FloraFresh Vaginal Probiotics Gummies, $40.99, in stock 2026-10-17)
  - **FloraFresh formula (Supplement Facts label, the source of truth):** per 2 gummies, Bacillus coagulans SNZ-1969 (spore-based) 1 billion CFU, Vitamin C 30 mg and pineapple fruit powder 100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges Allergen Free, Vegan, Halal, Gluten Free. Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article (both repeat a wrong formula); a PDP/label mismatch is a gate failure.
  - **Collection links (≥2, verify live):** `/collections/womens-essentials-collection` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** A gym habit does not change the gummy routine. Say what research did not test in athletes. No performance claim and no cure claim. Link the beginners page and the side-effects page. FloraFresh formula, if you name it, comes from the Supplement Facts label only: Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, sweetened with maltitol and isomalt. Never the PDP description. No cure or treatment claims.
  - **Fan-out answers to cover:** does a gym habit change the routine; were athletes in the trials; is there a performance claim; where is the beginners page
  - **Evidence to fetch & confirm (claims log):** Any oral-probiotic trial that enrolled women athletes — fetch it or say you found none. No performance claim.
  - **Link, don't restate:** `/blogs/news/vaginal-probiotics-for-beginners-what-to-expect-in-the-us`, `/blogs/news/vaginal-probiotics-side-effects-normal-vs-stop-us-2026`, `/blogs/news/vaginal-probiotics-which-strains-actually-work-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** probiotic + athletes checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-32 — real or fake nmn with food** — `Real or Fake NMN, With Food Checks (US 2026)`
  - **Primary keyword:** `real or fake nmn with food` · **Secondary:** fake nmn capsules, counterfeit nmn, is my nmn real, nmn bottle check
  - **Search intent:** US shopper trying to tell a real labeled bottle from a listing that does not match its panel
  - **Template:** STORY · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/ageaura-pure-nmn-tmg-nad-complex` (AgeAura Pure NMN + TMG NAD+ Complex, $69.95, in stock 2026-10-17)
  - **Collection links (≥2, verify live):** `/collections/best-seller` twice (browse link — AgeAura Pure NMN + TMG NAD+ Complex is not in it, never claim it is) · no other AgeAura product and no AgeAura collection link (brand_rules)
  - **Angle:** This is not the regulatory history; link the where-to-buy page for that. This page is how a US shopper spots a bottle that does not match its own label. Use only the live AgeAura Pure NMN + TMG NAD+ Complex only panel as the example. Do not invent a milligram the page does not print. Do not lead on a certificate.
  - **Fan-out answers to cover:** what should the panel name; how do listings go wrong; what is the regulatory page for; what can you check without a lab
  - **Evidence to fetch & confirm (claims log):** Live PDP for AgeAura Pure NMN + TMG NAD+ Complex only. No invented test. The where-to-buy article holds the regulatory dates.
  - **Link, don't restate:** `/blogs/news/where-to-buy-nmn-in-the-us-fda-status-explained-2026`, `/blogs/news/ageaura-nmn-tmg-ingredients-what-each-one-does-us`, `/blogs/news/nmn-capsules-vs-powder-vs-sublingual-best-form-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** nmn + authenticity checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-33 — shilajit gummies ingredients with food** — `Shilajit Gummy Ingredients, Taken With Food (2026)`
  - **Primary keyword:** `shilajit gummies ingredients with food` · **Secondary:** what is in shilajit gummies, shilajit gummy label, shilajit gummies ingredient list, shilajit gummies panel
  - **Search intent:** buyer who wants the gummy ingredient list before comparing it with resin
  - **Template:** LISTICLE · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/premium-himalayan-shilajit-gummies` (Premium Himalayan Shilajit Gummies, $59.99, in stock 2026-10-17)
  - **Collection links (≥2, verify live):** `/collections/shilajit-wellness-stack` (contains it), `/collections/best-seller` (contains it)
  - **Angle:** What the gummy PDP actually lists, fetched the day you write. Resin, gold resin, and drops are different products with different labels; link the resin-versus-gummies page instead of rebuilding it. No milligram you did not read on that page. Do not lead with lab testing.
  - **Fan-out answers to cover:** what does the gummy label name; how is that different from resin; what if a word is missing; do you take them with a meal
  - **Evidence to fetch & confirm (claims log):** Live gummy PDP ingredient list, fetched at write time. No borrowed resin percentage.
  - **Link, don't restate:** `/blogs/news/shilajit-resin-vs-gummies-which-works-better-us-2026`, `/blogs/news/how-to-choose-shilajit-gummies-7-checks-us-2026`, `/blogs/news/best-shilajit-gummies-6-us-labels-compared-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** shilajit + ingredients checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-34 — shilajit for hair with food** — `Shilajit for Hair, Taken With Food (US 2026)`
  - **Primary keyword:** `shilajit for hair with food` · **Secondary:** shilajit hair growth, shilajit and hair, does shilajit help hair, shilajit hair claims
  - **Search intent:** reader who has seen hair claims and wants the human evidence separated from the ads
  - **Template:** EDITORIAL · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/shilasource-himalayan-shilajit-resin` (ShilaSource Himalayan Shilajit Resin, $59.99, in stock 2026-10-17)
  - **ShilaSource Himalayan Shilajit Resin pack label (source of truth):** ShilaSource, Himalayan, Shilajit, Resin, 75, Dietary Supplement, Wellness, Nest, 70% Fulvic Acid*, Lab-Tested for Purity*, 1.06oz (30g), SERVINGS, Servings. No milligram amount and no Supplement Facts panel were read into that file. Do not add one. Do not state a serving count, volume, weight, fulvic percentage, mineral count, or day-supply other than the lines in product_refs/shilasource-himalayan-shilajit-resin.label.json.
  - **Collection links (≥2, verify live):** `/collections/shilajit-wellness-stack` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Search for human trials of shilajit and hair. If you cannot fetch one, say so, and do not promote a hair result from a different outcome. Not a hair treatment. Link the side-effects page. No milligram beyond the pack-label line.
  - **Fan-out answers to cover:** is there a human hair trial; what did the studies actually measure; does a meal change anything; when should you skip the claim
  - **Evidence to fetch & confirm (claims log):** PubMed or DOI search for shilajit and hair — fetch each paper and label it human or not. No unfetched result.
  - **Link, don't restate:** `/blogs/news/shilajit-side-effects-7-signs-to-watch-for-us-2026`, `/blogs/news/shilajit-benefits-for-men-4-claims-ranked-us-2026`, `/blogs/news/how-much-shilajit-per-day-dosage-by-form-us-2026`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** shilajit + hair checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

- [ ] **#CA1017-35 — shilajit loading with food** — `Shilajit Loading, With Food or Not? (2026)`
  - **Primary keyword:** `shilajit loading with food` · **Secondary:** shilajit loading phase, shilajit bigger start, do you load shilajit, shilajit opening week
  - **Search intent:** new user who saw a loading week mentioned and wants to know if trials did that
  - **Template:** COMPARISON · **Gate:** topic_fitness REVIEW [covered-segment] → allowed under Kevin's standing greenlight for mined queues (2026-08-13) · STEP 0: suggest.json 0 article matches (2026-10-17 14:56 ICT)
  - **Hero product:** `/products/shilasource-himalayan-shilajit-resin` (ShilaSource Himalayan Shilajit Resin, $59.99, in stock 2026-10-17)
  - **ShilaSource Himalayan Shilajit Resin pack label (source of truth):** ShilaSource, Himalayan, Shilajit, Resin, 75, Dietary Supplement, Wellness, Nest, 70% Fulvic Acid*, Lab-Tested for Purity*, 1.06oz (30g), SERVINGS, Servings. No milligram amount and no Supplement Facts panel were read into that file. Do not add one. Do not state a serving count, volume, weight, fulvic percentage, mineral count, or day-supply other than the lines in product_refs/shilasource-himalayan-shilajit-resin.label.json.
  - **Collection links (≥2, verify live):** `/collections/shilajit-wellness-stack` (contains it), `/collections/mens-essential-collection` (contains it)
  - **Angle:** Some pages imply a bigger start. If you cannot fetch a human trial that used a loading week, say so and point at the dosage page for the steady amount. Do not invent a load. No milligram beyond the pack-label line.
  - **Fan-out answers to cover:** did any trial use a bigger start; is a loading week required; what does the steady page cover; does a meal change the start
  - **Evidence to fetch & confirm (claims log):** Human shilajit trials you fetch — describe the schedule they used. If none loaded, say so.
  - **Link, don't restate:** `/blogs/news/how-much-shilajit-per-day-dosage-by-form-us-2026`, `/blogs/news/how-to-take-shilajit-resin-dissolve-it-right-us-2026`, `/blogs/news/shilajit-for-beginners-5-checks-before-your-first-pouch`
  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, reviewer or credential
  - **Dedup note:** shilajit + loading checked 2026-10-17 against 128 live articles (blog listing + sitemap + Atom + local caches) and all 76 tickets in this file; STEP 0 re-checks at write time

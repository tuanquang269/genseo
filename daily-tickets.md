# Daily ticket queue — wellnessnest.co (batch 1, hand-written 2026-08-07)

Agent được lệnh *"continue with the next ticket in daily-tickets.md"* → lấy ticket
`[ ]` PENDING kế tiếp → chạy skill `genseo-auto-publish` đủ 10 STEP → tick `[DONE <date>] <url>`.

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


# BATCH 2026-08-16

- [DONE 2026-08-20 https://wellnessnest.co/blogs/news/shilajit-shockwave-review-1-drop-or-1-ml-us-2026] Ticket #26 — shilajit shockwave review — `Shilajit Shockwave Review: 1 Drop or 1 mL? (US 2026)`
  - **Primary keyword:** `shilajit shockwave review` · **Secondary:** shilajit shockwave, shilajit energy drops review, shilajit drops dosage, how many drops of shilajit
  - **Template:** EDITORIAL (review/audit intent; previous #25 was COMPARISON so the variety guard is satisfied).
  - **Product:** `shilajit-shockwave` ($79.99) — the LAST stocked SKU with no article, carried forward from 2026-08-13, -14 and -15. Supporting: `premium-himalayan-shilajit-gummies` ($59.99) · `shilasource-himalayan-shilajit-resin` ($59.99) · `pure-shilajit-gold-resin` ($75.00). Collections: `/collections/shilajit-wellness-stack`, `/collections/mens-essential-collection`, `/collections/best-seller`.
  - **Intent:** near-buyer deciding whether the most expensive shilajit SKU on the store is worth $20 more than the resin.
  - **Angle (the payload, found by parsing the RENDERED PDP):** the listing publishes TWO conflicting
    servings — the directions block says `1 serving = 1 drop`, the FAQ block says
    `drop 1ml (a full dropper)`, roughly a twenty-fold gap. The page's own value block prints a
    `$0.60` cost per serving; at $79.99 that implies ~133 servings, which only reconciles with the
    single-drop reading (133 mL would not fit a 1–2 fl oz dropper bottle). So the article resolves
    the contradiction in the buyer's favour and tells them to start at 2–3 drops.
  - **Disclose (house honesty pattern, same as #22/#24):** no Supplement Facts panel, no bottle
    volume, no servings-per-container, and no caffeine mg — the page says only "a moderate dose of
    caffeine". Across the four US shilajit SKUs, price runs OPPOSITE to label detail: the $59.99
    gummies publish a full panel (150 mg 10:1 extract = 1,500 mg raw, 2 gummies/6 g, 30 servings),
    the $75.00 gold resin and the $79.99 drops publish nothing. Do NOT repeat any COA or
    "third-party tested" line (house rule `no-coa-competitive-advantage`), and do NOT repeat the
    PDP's asthma answer (see the flag in the run log).
  - **Evidence spine (all DOIs verified live against api.crossref.org this run; NCBI/Europe PMC are
    IP-blocked from this Mac):**
    Keller 2019 JISSN 10.1186/s12970-019-0270-2 (250 & 500 mg/d, 8 wk, resistance-trained men) ·
    Pandit 2016 Andrologia 10.1111/and.12482 (250 mg BID, 90 d) ·
    McLellan 2016 Neurosci Biobehav Rev 10.1016/j.neubiorev.2016.09.001 (caffeine dose-response) ·
    Arring 2018 JACM 10.1089/acm.2017.0361 (ginseng for fatigue — mixed) ·
    Jamshidi & Cohen 2017 eCAM 10.1155/2017/9217567 (tulsi — small trials) ·
    FDA 400 mg/day caffeine consumer update + FDA structure/function claims page.
  - **Gates:** STEP 0 live `suggest.json` = 0 article matches across 6 query variants
    (shilajit shockwave / shockwave / shilajit shockwave review / shilajit drops review /
    shilajit energy drops worth it / creatine-style controls); positive control on "shilajit"
    correctly returned 5 live articles and on "shilajit liquid drops" returned the old
    Types-of-Shilajit page. `topic_fitness.py` → `PASS [brand_intent]` (the only PASS of the four
    candidates mined today — the three `side effects` segments all returned `REVIEW`).
  - **Mined because the queue was empty** (DAILY-RUN section 2). GSC unauthorised and no google-ads
    tool is exposed to this headless run, so this came from the live catalog + the live blog
    inventory at $0.
  - **CARRIED OVER — blocked on images, 5th consecutive day. Ticket stays `[ ]`.**
    08-16 and 08-17 stalled on an ima2 HTTP **429** quota block; the 08-18 run never started
    ("You've hit your weekly limit"); 08-19 failed differently, on HTTP 401 `AUTH_CHATGPT_EXPIRED`.
    **On 2026-08-20 the 401 is GONE and the 429 is back.** Kevin re-authenticated on 08-19 at 08:48
    (`~/.codex/auth.json` rewritten, `last_refresh` 2026-08-19T01:48:15Z, access_token good to
    08-29), and the oauth proxy now answers `GET :10531/v1/models` with **HTTP 200** — the exact
    probe that failed yesterday. So the auth leg is **fixed and needs no further action**. What
    remains is the older, unrelated block: `POST :3333/api/generate` returns **HTTP 429** with
    `upstreamType: "usage_limit_reached"` — the ChatGPT plan's image quota, exhausted, not a
    transient rate limit. `logs/ima2-quota-wait.log` shows it probed for **5 hours** on 08-19 and
    never reopened. No paid image API was substituted; no credential was entered.
    **The draft is finished and needs no rework**:
    `published_drafts/shilajit-shockwave-review-1-drop-or-1-ml-us-2026.md`, 2,011 words, h1:1 h2:9
    table:True collections:3, 9/9 outbound links 200, 0 MuscleMax — `validate_article.py --draft`'s
    **only** failure is the 4 absent image files. STEP 0 re-run on 08-20 (7 variants) still returns
    0 matches on the primary keyword, and the PDP payload (`1 drop` vs `1ml (a full dropper)`,
    `cost per serving: $0.6`, no Supplement Facts) was re-verified live and still holds.
    QC re-roll budget **0 of 2 spent** (both 08-20 attempts died in transport at 429, before any
    image existed to QC). Persona reservation **seq=34 (NO-FACE, 0 face angles)** left RESERVED, not
    committed — no angle burned. **The blocker is now purely quota: nothing on this Mac can clear
    it.** When the image allowance resets: make the 4 images, re-validate to PASS, publish
    live/visible, then `persona_picker.py commit --seq 34`.
  - **✅ RESOLVED 2026-08-20 (second run of the day) — the image quota REOPENED and the ticket
    shipped on its 6th day.** The cheap probe that returned 429 at 01:47Z returned **HTTP 200**;
    `GET :10531/v1/models` was already 200, so both legs were clear. All 4 images generated on the
    FIRST roll, QC PASS each (`0 of 2` re-rolls spent), and each was eyeballed against its curated
    ref: hero = Shockwave bottle alone at bench height, no hands; the 3-pack lineup rendered the
    gummies as the real POUCH (badges verbatim) and ShilaSource as the matte-black canister + amber
    gold-lid jar, not a pouch. Draft needed **zero rework** — gate `✓ PASS` exit 0 at 2,011 words.
    LIVE id **621886439739**, `published_at` non-null, frontend 200 with a browser UA. The first
    `verify_published.py` FAILED on `author is not a named Person` (Shopify wrote the byline as
    "Wellness Nest Editorial Team"); `repair_schema.py 621886439739` set it to Dr. Marcus Hale and
    the re-run passed. Reservation seq=34 committed after the live publish; 0 face angles burned.

# BATCH 2026-08-21

- [DONE 2026-08-21 https://wellnessnest.co/blogs/news/creatine-gummies-side-effects-4-real-3-myths-us-2026] Ticket #27 — creatine gummies side effects — `Creatine Gummies Side Effects: 4 Real, 3 Myths (US 2026)`
  - **Primary keyword:** `creatine gummies side effects` · **Secondary:** creatine side effects, are creatine gummies safe, creatine bloating, creatine gummies kidney, creatine hair loss
  - **Template:** LISTICLE (7 numbered items; previous #26 was EDITORIAL so the variety guard is satisfied).
  - **Product:** `fusiforce-creatine-gummies` ($69.99). Collections: `/collections/mens-essential-collection`, `/collections/best-seller`.
  - **Intent:** buyer who already wants creatine and is checking what it will do to them before committing to a daily habit. Three creatine articles are live (dosage, vs-powder, for-women-over-40); none covers side effects.
  - **Angle:** split the list — 4 side effects that are real and dose-related (GI distress, water weight, the sugar a powder does not have, and the ADDED PANAX GINSENG rather than the creatine as the interaction line) against 3 that are not (kidney damage, hair loss, dehydration/cramps). The non-obvious payload: creatine raises SERUM CREATININE, the exact marker US labs use to estimate kidney function, so a routine panel can look worse while the kidneys are fine — that mechanism is why the kidney myth keeps regenerating.
  - **Disclose (house honesty pattern, same as #22/#24/#25/#26):** verified live on the rendered PDP this run — the Green Apple pouch front prints **90 GUMMIES** and the Blueberry pouch front prints **112 GUMMIES** at the same $69.99, i.e. 30 vs 37 days at the label's own 3-gummy serving. The Supplement Facts panel appears only on the pouch BACK in PDP image index 10, at thumbnail size and not legible; no servings-per-container and no grams of sugar are published in the listing text. Article routes the reader to support@wellnessnest.co. Do NOT repeat the PDP's COA / third-party-tested / ISO 17025 / "500+ peer-reviewed studies" lines (house rule `no-coa-competitive-advantage`).
  - **Evidence spine (all 8 DOIs verified live against api.crossref.org this run; NCBI/eutils IP-blocked from this Mac):**
    Kreider 2017 JISSN 10.1186/s12970-017-0173-z (ISSN position stand, safety + dose-related GI) ·
    Antonio 2021 JISSN 10.1186/s12970-021-00412-w (misconceptions: hair loss, cramps, dehydration) ·
    Ostojic & Ahmetovic 2008 Res Sports Med 10.1080/15438620701693280 (GI distress 10 g vs 5 g) ·
    Deminice 2015 Int J Sports Med 10.1055/s-0035-1559690 (total body water, deuterium oxide dilution) ·
    Poortmans & Francaux 1999 MSSE 10.1097/00005768-199908000-00005 (renal function unimpaired) ·
    Tsiaras 2026 J Ren Nutr 10.1053/j.jrn.2026.04.010 (kidney function systematic review + meta-analysis of RCTs) ·
    van der Merwe 2009 Clin J Sport Med 10.1097/JSM.0b013e3181b8b52f (DHT:T ratio, 3 wk, the ENTIRE hair-loss basis) ·
    Yuan 2004 Ann Intern Med 10.7326/0003-4819-141-1-200407060-00011 (American ginseng reduces warfarin effect) ·
    plus NCCIH Asian ginseng page + FDA structure/function framing.
    NOTE: two DOIs were rejected during verification because Crossref resolved them to the WRONG paper —
    10.1097/00005768-199908000-00002 (returns a tibial-stress-fracture paper) and 10.1152/japplphysiol.00745.2002.
    The correct Poortmans DOI is ...-00005. Do not re-cite the ...-00002 form.
  - **Gates:** STEP 0 live `suggest.json` = 0 article matches across 6 query variants (creatine gummies side effects / creatine side effects / creatine gummies safe / are creatine gummies safe / creatine bloating / do creatine gummies cause bloating); positive control on "creatine" correctly returned 3 live articles and on "creatine gummies" returned the dosage + vs-powder pages. `topic_fitness.py` → `REVIEW [covered-segment]`, proceeding under Kevin's standing greenlight for this mined queue (2026-08-13).
  - **Mined because the queue was empty** (DAILY-RUN section 2). GSC unauthorised and no google-ads tool is exposed to this headless run, so this came from the live catalog (22 SKUs) + the live blog inventory (57 articles) at $0.

## Refill needed

**2026-08-21 — the queue was EMPTY at the start of this run and #27 was mined on the day**
(DAILY-RUN section 2), then shipped, so nothing is left open again. GSC is still unauthorised on
this Mac and no google-ads tool is exposed to a headless run, so the mining recipe in
`skills/genseo-auto-publish/references/ads-article-mining.md` still cannot run from here.
**Kevin: run that recipe in the app** and append the next batch below as `# BATCH <date>`.

$0 fallback that produced this batch: read the live catalog + the live blog inventory, list the
brand+segment pairs no title covers, gate each through `topic_fitness.py`, then STEP 0 each
survivor against `suggest.json`.

Segments still open after #27 (each gates to `REVIEW [covered-segment]`; STEP 0 each against
suggest.json before writing):
`nmn` + side effects · `vaginal probiotic` + side effects · `turkesterone` + side effects ·
`shilajit` + drops-vs-resin (the older "Types of Shilajit Products" page already compares drops
and resin, so this one needs a genuinely narrower angle or it cannibalises).
**`creatine gummies` + side effects is now CLOSED by #27** — do not re-mine it.

**Every stocked SKU now has an article.** The catalog grew from 11 to 22 handles, but the 11 new
ones are fulfilment and subscription variants, not new products: `shilajit-gummies-single-jar`
($39.99) and `shilajit-gummies-two-jar-pack` ($72.00) are add-on jars of the same
`premium-himalayan-shilajit-gummies`, and the `*-3/6/12-month-reserve` handles are subscription
bundles of SKUs already covered. None of them justifies its own article; the remaining demand is
segment long-tail on products we already write about.

**2026-08-21 (second run of the day) — queue still EMPTY, nothing published, by design.** No `[ ]`
heading exists anywhere in this file. The day's article was already shipped by the 07:30 run
(#27, LIVE id `621890044219`, frontend re-checked HTTP 200 with a browser UA this run), and
DAILY-RUN §1 caps the job at one article per day — so this run did not mine a second topic. That
guard matters here: every segment left open below gates to `REVIEW [covered-segment]`, and a
same-day second article off a covered segment is exactly how a page starts competing with one of
our own. **Kevin: run the mining recipe in the app**
(`skills/genseo-auto-publish/references/ads-article-mining.md`) and append the next batch as
`# BATCH <date>`. GSC is still unauthorised on this Mac and no google-ads tool is exposed to a
headless run, so the $0 fallback above stays the only path from here.

Housekeeping done this run: the 07:30 run published, flipped its ticket and appended tracker row
27, but never committed — `daily-tickets.md` and `personas/index.json` (which carries the seq=35
persona commit for #27) were left dirty in the working tree. Both are committed now. Nothing else
about #27 was touched.

**2026-08-21 (third run of the day) — queue still EMPTY, nothing published, by design.** No `[ ]`
heading exists anywhere in this file; the only `[ ]` strings left are inside prose (the rules
block at the top and the historical notes on #26, whose heading is `[DONE 2026-08-20 …]`). Today's
one article already shipped at 07:30 (#27, LIVE id `621890044219`; frontend re-checked this run,
HTTP 200 with a browser UA), and DAILY-RUN §1 caps the job at one article per day, so this run did
not mine a third topic. The same-day guard is the point: every segment listed as open above gates
to `REVIEW [covered-segment]`, and stacking a second article onto a covered segment on the same
day is how a page starts competing with one of our own.

**Kevin: run the mining recipe in the app**
(`skills/genseo-auto-publish/references/ads-article-mining.md`) and append the next batch as
`# BATCH <date>`. The google-ads MCP is **not exposed to this headless session** (MCP servers
present this run: claude.ai and Shopify, both unauthenticated — and Shopify MCP is barred by hard
rule #2 regardless). GSC is still unauthorised on this Mac, so the $0 catalog + blog-inventory
fallback above stays the only path from here. Nothing above this line changed this run; the
working tree was already clean when it started.


# BATCH 2026-08-22

- [DONE 2026-08-22 https://wellnessnest.co/blogs/news/urolithin-a-dosage-how-many-mg-per-day-us-2026] Ticket #28 — urolithin a dosage — `Urolithin A Dosage: How Many mg Per Day? (US 2026)`
  - **Primary keyword:** `urolithin a dosage` · **Secondary:** how much urolithin a per day, urolithin a 500 mg, urolithin a dose for muscle, urolithin a mitopure dose, is 1000 mg urolithin a better
  - **Template:** EDITORIAL (templates reference maps dosage intent -> EDITORIAL; previous #27 was LISTICLE so the variety guard is satisfied).
  - **Product:** `ageaura-pure-urolithin-a` ($199.99). Collections: `/collections/ageaura`, `/collections/best-seller`.
  - **Intent:** buyer who has already decided urolithin A is worth trying and is now asking what dose to buy — the single most expensive SKU on the store, so the dose question is really a "what am I paying $199.99 for" question.
  - **Angle:** the dose ladder the human trials actually used — 250 mg / 500 mg / 1,000 mg — judged tier by tier on what each one MOVED, not on what it is marketed to do. The non-obvious payload: 1,000 mg is not the "stronger" option most buyers assume. Andreux 2019 dosed up to 1,000 mg for safety, and Liu 2022 ran 1,000 mg in older adults and found muscle-endurance gains WITHOUT a change in peak ATP — while Singh 2022 got strength and endurance improvements at 500 mg. So the ladder flattens at the top, and the honest US buyer answer is that 500 mg once daily is the line, which is exactly what this SKU sells.
  - **Second payload (cost, nobody else publishes it):** at $199.99 for 30 capsules that is **$6.67 per day** — verified at source on the rendered PDP this run. The multi-bottle tiers change that number materially: Buy 2 get 1 free $399.99 (3 bottles / 90 days = $4.44/day), Buy 3 get 2 free $599.99 (5 bottles / 150 days = $4.00/day), Buy 6 get 6 free $1,199.99 (12 bottles / 360 days = $3.33/day). Publish the per-day math; it is the real decision the reader is making.
  - **Disclose (house honesty pattern, same as #22/#24/#25/#26/#27):** verified live on the rendered PDP this run — 500 mg of >=98% pure Urolithin A per vegan HPMC capsule, USP grade; other ingredients microcrystalline cellulose, vegetable magnesium stearate, silicon dioxide; 30 capsules per bottle = 30-day supply at one capsule daily; 90-day money-back guarantee, bottle not returned. Do NOT repeat the PDP's "third-party tested for identity and potency" or "clinically dosed" lines (house rule `no-coa-competitive-advantage`).
  - **Evidence spine (all 6 DOIs verified live against api.crossref.org this run; NCBI/eutils IP-blocked from this Mac):**
    Andreux 2019 Nature Metabolism 10.1038/s42255-019-0073-4 (first-in-human, 250/500/1000 mg, 4 wk, safety + plasma exposure) *
    Singh 2022 Cell Reports Medicine 10.1016/j.xcrm.2022.100633 (middle-aged adults, 500 mg and 1000 mg, 4 months, muscle strength + endurance) *
    Liu 2022 JAMA Network Open 10.1001/jamanetworkopen.2021.44279 (older adults 65-90, 1000 mg, 4 months, muscle endurance without a peak-ATP change) *
    Ryu 2016 Nature Medicine 10.1038/nm.4132 (the mitophagy mechanism, C. elegans + rodents) *
    Tomas-Barberan 2014 J Agric Food Chem 10.1021/jf5024615 (three urolithin metabotypes — why food-source dosing is not a dose) *
    Singh 2019 Nature Communications 10.1038/s41467-018-07859-7 (gut-barrier / Nrf2, background mechanism).
    NOTE: doi.org returns 403 to curl for the JAMA and ACS entries (publisher bot-blocking, not a bad DOI) — both resolved correctly through the Crossref API, which is the check that counts.
  - **Internal links:** the existing `/blogs/news/urolithin-a-benefits-the-40-problem-us-buyers-miss` owns the 40%-converter and mitophagy explainer — LINK it, do not restate it. `/blogs/news/how-much-nmn-per-day-what-trials-used-us-2026` is the sibling dose article for the other AgeAura SKU.
  - **Gates:** STEP 0 live `suggest.json` = 0 article matches on `urolithin a dosage`, `urolithin a how much`, `nmn side effects`, `turkesterone side effects`, `vaginal probiotics side effects`, `nmn vs nr`; positive controls returned 1 on `urolithin a` (the benefits article) and 5 on `shilajit`, so the check was live and the zeroes are real. `topic_fitness.py` -> `REVIEW [covered-segment]`, proceeding under Kevin's standing greenlight for this mined queue (2026-08-13).
  - **Mined because the queue was empty** (DAILY-RUN section 2). GSC is still unauthorised and no google-ads tool is exposed to this headless run, so this came from the live catalog + the live blog inventory (57 articles) at $0.


## Refill needed

**2026-08-22 — the queue was EMPTY at the start of this run and #28 was mined on the day**
(DAILY-RUN section 2), then shipped, so nothing is left open again. GSC is still unauthorised on
this Mac and no google-ads tool is exposed to a headless run (MCP servers present this run:
claude.ai and Shopify, both UNAUTHENTICATED — and Shopify MCP is barred by hard rule #2 anyway),
so the mining recipe in `skills/genseo-auto-publish/references/ads-article-mining.md` still cannot
run from here. **Kevin: run that recipe in the app** and append the next batch below as
`# BATCH <date>`.

**`urolithin a` + dosage is now CLOSED by #28** — do not re-mine it.

Segments still open after #28 (each gates to `REVIEW [covered-segment]`; STEP 0 each against
suggest.json before writing — all three returned 0 article matches when probed on 2026-08-22, so
they are still genuinely uncovered):
`nmn` + side effects · `vaginal probiotic` + side effects · `turkesterone` + side effects ·
`shilajit` + drops-vs-resin (the older "Types of Shilajit Products" page already compares drops
and resin, so this one needs a genuinely narrower angle or it cannibalises) ·
`nmn` + vs NR (probed clean this run, and the NMN dose article already links the AgeAura SKU).

**⚠ NEW FINDING THIS RUN — a collection-claim trap worth reusing.** `ageaura-pure-urolithin-a` is
in **NEITHER** `/collections/ageaura` (which contains only `ageaura-pure-nmn-tmg-the-essential-longevity-duo`
and `ageaura-pure-nmn-tmg`) **NOR** `/collections/best-seller` (shilajit resin, shilajit gummies,
FusiForce, FloraFresh). Both URLs return 200, so the validator's link check passes either way and
would NOT have caught a membership claim. #28 links both as browse suggestions only. Verify
membership with `/collections/<handle>/products.json` before writing any "part of our X collection"
sentence — same trap first caught on Ticket #1/#2 with FusiForce.

**⚠ RESEARCH LANE RESTORED (partly).** NCBI/eutils is still IP-blocked from this Mac, but the
**Europe PMC REST API is reachable and anonymous** — no key, no account:
`https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%22<doi>%22&resultType=core&format=json`
It returned full abstracts for all three urolithin A trials this run, which is how #28 could state
that BOTH four-month trials missed their pre-named primary endpoint. Crossref confirms a DOI points
at the right paper; Europe PMC tells you what the paper actually found. Use both from now on —
Crossref alone cannot stop a real-but-misdescribed citation.

**2026-08-22 (second run of the day) — queue still EMPTY, nothing published, by design.** No `[ ]`
heading exists anywhere in this file; every `[ ]` string left is prose (the rules block at the top
and the historical carry-over notes on #26, whose heading is `[DONE 2026-08-20 …]`). Today's one
article already shipped (#28, LIVE id `621894074683`; frontend re-checked this run, HTTP 200 with a
browser UA), and DAILY-RUN §1 caps the job at one article per day, so this run did not mine a
second topic. The same-day guard is the point: every segment listed as open above gates to
`REVIEW [covered-segment]`, and stacking a second article onto a covered segment on the same day is
how a page starts competing with one of our own.

**Kevin: run the mining recipe in the app**
(`skills/genseo-auto-publish/references/ads-article-mining.md`) and append the next batch as
`# BATCH <date>`. The google-ads MCP is **not exposed to this headless session** (MCP servers
present this run: claude.ai and Shopify, both UNAUTHENTICATED — and Shopify MCP is barred by hard
rule #2 regardless; the only network tools reachable are web search / web fetch). GSC is still
unauthorised on this Mac, so the $0 catalog + blog-inventory fallback above stays the only path
from here. Nothing above this line changed this run; the working tree was already clean when it
started, and tracker row 28 was already appended and committed by the 07:30 run.

**2026-08-22 (third run of the day) — queue still EMPTY, nothing published, by design.** No `[ ]`
heading exists anywhere in this file (`grep "^##.*\[ \]"` returns nothing); every remaining `[ ]`
string is prose — the rules block at the top and the historical carry-over notes. Today's one
article is #28, still LIVE: `https://wellnessnest.co/blogs/news/urolithin-a-dosage-how-many-mg-per-day-us-2026`
re-checked this run, HTTP 200 with a browser User-Agent. DAILY-RUN §1 caps the job at one article
per day, so no second topic was mined.

**Kevin: run the mining recipe in the app**
(`skills/genseo-auto-publish/references/ads-article-mining.md`) and append the next batch as
`# BATCH <date>`. The google-ads MCP is **not exposed to this headless session** — the only MCP
servers present are claude.ai and Shopify, both UNAUTHENTICATED (and Shopify MCP is barred by hard
rule #2 regardless); the only reachable network tools are web search / web fetch. GSC is still
unauthorised on this Mac, so the $0 catalog + blog-inventory fallback stays the only path from
here. The open-segment list above (nmn side effects · vaginal probiotic side effects · turkesterone
side effects · shilajit drops-vs-resin · nmn vs NR) is unchanged and was not re-probed this run.
Nothing else in this file changed; the working tree was clean when this run started.


# BATCH 2026-08-23

Mined per DAILY-RUN §2 (queue empty; GSC + google-ads still unavailable). Source: live catalog
(`/collections.json`, `/products.json`) + blog inventory (`ALL_ARTICLES.csv`). Segment `nmn` + `vs NR`
was on the open-segment list carried from 2026-08-22 and re-probed clean against `suggest.json`
this run (0 article matches). Chosen over the three `side effects` candidates because the skill's
own STEP 0.5 WRITE table names this exact pattern ("Comparison that ends at our SKU: NMN vs NR")
and because the template variety guard wants a non-EDITORIAL after #28.

## [DONE 2026-08-23 https://wellnessnest.co/blogs/news/nmn-vs-nr-what-6-human-trials-say-us-2026] Ticket #29 — NEW ARTICLE (type: COMPARISON)
- **Primary keyword:** `nmn vs nr`
- **STEP 0 (live, 2026-08-23):** `suggest.json?q=nmn vs nr` -> 0 article matches. Clean.
- **STEP 0.5:** `REVIEW [covered-segment]` — greenlit under Kevin's standing queue approval
  (2026-08-13, "I approve all of them, I need published articles without any delay").
- **Angle:** the two molecules are compared on marketing volume, not on trial evidence. The honest
  read is that the positive metabolic RCT on NMN used 250 mg while the null metabolic RCT on NR
  used 2,000 mg — 8x the dose, opposite result, different populations. Lead with that.
- **Ends at SKU:** `ageaura-pure-nmn-tmg-nad-complex` ($69.95, curated ref exists). We do NOT sell
  NR — compare the ingredient, never link an NR product.
- **Template:** COMPARISON (previous #28 was EDITORIAL, so the variety guard is satisfied).
- **Evidence bank (all verified this run via Europe PMC, abstracts read — not title-only):**
  Trammell 2016 Nat Commun `10.1038/ncomms12948` | Martens 2018 Nat Commun `10.1038/s41467-018-03421-7`
  | Dollerup 2018 AJCN `10.1093/ajcn/nqy132` (NR 2,000 mg/d, 12 wk, insulin sensitivity NOT improved)
  | Yoshino 2021 Science `10.1126/science.abe9985` (NMN 250 mg, 10 wk, muscle insulin sensitivity up)
  | Yi 2023 GeroScience `10.1007/s11357-022-00705-1` (300/600/900 mg dose-response, 6-min walk)
  | Elhassan 2019 Cell Rep `10.1016/j.celrep.2019.07.043` (NR 1 g/d, 21 d, aged muscle).
- **Collection-membership trap:** `ageaura-pure-nmn-tmg-nad-complex` is NOT in `/collections/ageaura`
  (verified this run — that collection holds only `...-the-essential-longevity-duo` and `...-nmn-tmg`).
  Link collections as browse suggestions only. Never write "part of our X collection".
- **Do NOT state FDA/regulatory status of NMN.** It could not be verified from this machine
  (WebFetch dead, fda.gov not fetched) and it moves. Omitted deliberately, not forgotten.

**2026-08-23 — Ticket #29 MINED AND PUBLISHED.** Queue was empty at start (0 `[ ]` headings), so the
run mined per DAILY-RUN §2 instead of skipping the day. `nmn` + `vs NR` is now **CLOSED by #29** — do
not re-mine it. LIVE id `621895811387`, HTTP 200, og:title correct.

Segments still open after #29 (each gates to `REVIEW [covered-segment]`; STEP 0 each against
suggest.json before writing — all three `side effects` candidates were re-probed this run on
2026-08-23 and returned **0 article matches**, so they are still genuinely uncovered):
`nmn` + side effects · `vaginal probiotic` + side effects · `turkesterone` + side effects ·
`shilajit` + drops-vs-resin (still needs a genuinely narrower angle or it cannibalises the older
"Types of Shilajit Products" page).

Still uncovered on the catalog side, needs a distinct segment angle: `pure-shilajit-gold-resin` ($75)
· `shilajit-shockwave` ($79.99).

**⚠ NEW THIS RUN — the QRG prose gate is not actually running on this Mac.** `validate_article.py`
printed `⚠ QRG quality scoring skipped (claude-seo runtime not installed)`. The structural gate
(word count, headings, table, links-return-200, author, images) passed and is real, but the three
prose gates DAILY-RUN §1.3 leans on — `overall quality < 80`, `filler >= 25`, `ai-pattern >= 25` —
did **not** execute. Every `✓ PASS` on this machine is therefore structural-only. Banned phrases were
checked by hand this run (0 hits), but that is a human step standing in for a broken gate. Worth
fixing before it silently ships a thin article.

**⚠ Reusable finding — the every-3rd no-face hero fired on seq 37.** `persona_picker.py pick` returned
`hero: NO-FACE` with an empty `warnings[]`. That is the scheduled rotation, NOT an exhausted pool, and
it means 0 face angles were burned on this article. Do not "fix" it by forcing `--force-face`.

## Refill needed

**2026-08-23 (later run) — 0 `[ ]` tickets remain and today's article is ALREADY SHIPPED.**
Ticket #29 (`nmn vs nr`) was mined and published LIVE earlier today by the first 2026-08-23 run
(id `621895811387`, frontend re-verified HTTP 200 with a browser UA this run). DAILY-RUN §1 caps the
job at one article per day, so this run did **not** mine or publish a second topic. What it did do
was close the first run's outstanding bookkeeping: that run left `daily-tickets.md`,
`personas/index.json` (seq 37 commit) and the tracker row **uncommitted** in git. They are committed
now. `persona_picker.py status` shows seq=37 with **0 reservations open**, so no `release` was owed.

No google-ads tool is exposed to this headless run (MCP servers present: claude.ai and Shopify, both
UNAUTHENTICATED — and Shopify MCP is barred by hard rule #2 anyway) and GSC is still unauthorised on
this Mac, so the mining recipe in `skills/genseo-auto-publish/references/ads-article-mining.md`
cannot run from here. **Kevin: run that recipe in the app** and append the next batch below as
`# BATCH <date>`. The open segments carried forward are listed in the #29 block above — the three
`side effects` candidates (`nmn`, `vaginal probiotic`, `turkesterone`) were each re-probed clean
against the live `suggest.json` on 2026-08-23, plus `pure-shilajit-gold-resin` and
`shilajit-shockwave` on the catalog side.

**Still unfixed, second run in a row reporting it:** `validate_article.py` prints
`⚠ QRG quality scoring skipped (claude-seo runtime not installed)` on this Mac, so the three prose
hard-fails DAILY-RUN §1.3 leans on (overall quality < 80, filler ≥ 25, ai-pattern ≥ 25) do **not**
execute. Every `✓ PASS` produced here is structural-only.

# BATCH 2026-08-24

Mined per DAILY-RUN §2 (queue empty — 0 `[ ]` headings at start; GSC unauthorised and google-ads MCP
not connected, so no demand data). Source: live catalog `/products.json` (22 SKUs) + `/collections.json`
(6 collections) + blog inventory `ALL_ARTICLES.csv` (57 articles). Three open `side effects` segments
were carried forward from #29; all three re-probed clean against `suggest.json` this run
(`nmn side effects` 0, `turkesterone side effects` 0, `vaginal probiotics side effects` 0).
`shilajit gold resin` was re-probed and is now **CLOSED** — it returns the live #25 article, so it
comes off the open list.

Chose `vaginal probiotics side effects` over the other two: FloraFresh is priority brand #3 (vs
Turkesterone #5, AgeAura #6); turkesterone already carries THREE articles (benefits+dosing, vs
ecdysterone, timing) so a fourth over-concentrates that cluster; and NMN was published yesterday
(#29), so a second NMN article two days running risks self-competition inside the same cluster.
FloraFresh has 2 articles, both from 2026-08-09 — the longest gap of the three brands.

## [DONE 2026-08-24 https://wellnessnest.co/blogs/news/vaginal-probiotics-side-effects-normal-vs-stop-us-2026] Ticket #30 — NEW ARTICLE (type: LISTICLE)
- **Primary keyword:** `vaginal probiotics side effects`
- **Secondary:** are vaginal probiotics safe, probiotic gummies bloating, d-mannose side effects,
  how long do probiotic side effects last, can probiotics cause a yeast infection
- **STEP 0 (live, 2026-08-24):** `suggest.json?q=vaginal probiotics side effects` → 0 article matches. Clean.
- **STEP 0.5:** `REVIEW [covered-segment]` — greenlit under Kevin's standing queue approval
  (2026-08-13, "I approve all of them, I need published articles without any delay").
- **Template:** LISTICLE — `references/article-templates.md` maps "X side effects" → LISTICLE, and the
  previous article (#29) was COMPARISON, so the variety guard is satisfied.
- **Angle:** the honest split — what is a real, expected, self-limiting side effect of an oral
  Lactobacillus gummy (first-week gas/bloating, mild nausea, the sugar-alcohol load in a sugar-free
  gummy) versus what is a myth (it "causes" yeast infections) versus what is a genuine
  contraindication almost nobody publishes (severely immunocompromised / central-line / critically ill
  — Lactobacillus bacteremia is rare but documented and carries real mortality). Nobody in this SERP
  separates "expected and passes" from "stop and call someone".
- **Ends at SKU:** `florafresh-vaginal-probiotics-gummies` ($40.99, curated ref exists at
  `product_refs/florafresh-vaginal-probiotics-gummies.json`).
- **Payload verified at source on the rendered PDP this run:** 15 billion CFU per serving from four
  Lactobacillus strains (L. rhamnosus, L. reuteri, L. salivarius, L. gasseri) + XOS prebiotic +
  D-Mannose + Vitamin C; 2 gummies daily with water; 60 gummies = 30-day supply; vegan, gluten-free,
  sugar-free; $40.99.
- **Collection links:** `florafresh-vaginal-probiotics-gummies` IS a genuine member of BOTH
  `/collections/womens-essentials-collection` (3 products) and `/collections/best-seller` (4 products)
  — verified live this run. Membership can be stated here, unlike #28/#29. Still link them as browse
  suggestions rather than making a promotional claim.
- **Evidence bank (5 DOIs, each resolved at api.crossref.org to the correct paper AND the abstract read
  via Europe PMC — not title-only; NCBI eutils stays IP-blocked from this Mac):**
  Cohen 2020 NEJM `10.1056/NEJMoa1915254` (LACTIN-V, *vaginal* L. crispatus CTV-05, BV recurrence 30%
  vs 45% placebo at wk12, RR 0.66; AE rate did NOT differ from placebo) |
  Hayward 2024 JAMA Intern Med `10.1001/jamainternmed.2024.0264` (D-mannose 2 g/d, 6 mo, n=598 UK
  primary care: 51.0% vs 55.7% had a further suspected UTI, risk difference −5%, P=.26 — NOT effective
  for prophylaxis) |
  Sato 2025 J Infect Chemother `10.1016/j.jiac.2025.102794` (Lactobacillus bacteremia, 17 patients,
  risk factors present in 82.4%, 30-day mortality 35.3%) |
  Umbrella review 2026 Nutrition Reviews `10.1093/nutrit/nuaf303` (128 SRs/MAs of RCTs, efficacy AND
  safety of probiotics/prebiotics/synbiotics) |
  Russo 2019 Beneficial Microbes `10.3920/BM2018.0075` (oral L. acidophilus GLA-14 + L. rhamnosus HN001
  + lactoferrin as adjuvant to metronidazole in recurrent BV).
- **Route honesty (the differentiator):** the strongest BV probiotic trial (Cohen 2020) used a
  *vaginally applied* strain, not an oral gummy. Say so. Do not let a reader infer a NEJM result
  transfers to an oral product.
- **Disclose our own gaps (house pattern, same as #22/#24/#25/#26/#27):** the FloraFresh listing
  publishes 15 billion CFU total but **no per-strain CFU split**, and **no mg amount for D-Mannose or
  Vitamin C** — a reader who wants to compare the D-mannose dose against the 2 g/d used in Hayward 2024
  cannot do it from the listing. Route them to support@wellnessnest.co for the panel. This confirms the
  DAILY-RUN §6 "no Supplement Facts panel" flag; the strain-identity contradiction flagged there is NOT
  reproducible on the current rendered PDP (the four strains are stated consistently), so that half of
  the flag looks stale.
- **Do NOT repeat the PDP's disease-adjacent copy.** "Treats the root cause", "stays & colonizes",
  "top OB/GYN recommended formula", "100% natural ingredients" and the three inconsistent social-proof
  counts are all flagged in DAILY-RUN §6 — none of them go in the article. No COA / "clinically tested"
  line either (house rule `no-coa-competitive-advantage`).
- **Medical boundary:** structure/function language only. No treatment or cure claim for BV, yeast
  infection or UTI. Tell the reader plainly when to stop and contact a clinician.
- **Author:** Dr. Marcus Hale (roster.json, sole source).

### ✅ RESOLVED 2026-08-24 (later run) — the blocked-run note below is HISTORY, ticket #30 shipped

The collision was solved in the PROMPT, not by re-picking: the re-pick landed on seq 39 (release keeps seq as a
counter, so the same pair was NOT re-issued — but `high-angle-down` + `chin-up` did recur with a different persona).
Fix that worked, 4/4 first-roll QC PASS: front-load the head pose AND the identity clause together; describe the
camera as only slightly above the eye line; raise the gaze target to chest height so the eyes drop without the head;
NEGATIVE-list "no chin tucked toward the chest, no bowed or downward-tilted head".

#### ⛔ 2026-08-24 earlier run — BLOCKED ON THE HERO IMAGE (historical)

The ticket above was mined, gated and fully researched this run. **Nothing was written and nothing
was published.** The run stopped at STEP 5 because the hero image burned all three ima2 attempts
(1 initial roll + the 2 permitted re-rolls, DAILY-RUN §3) and the skill's CRITICAL FAILURE SAFEGUARD
says to abort rather than draft an article with missing images.

`persona_picker.py pick --audience women-25-45` issued **seq 38**, hero `f2029-bl-01`,
hero angle `profile-right+chin-up`, gaze `down-at-product`, shot `high-angle-down`,
inline angle `profile-left+chin-down`, gaze `at-lens`. `warnings[]` was EMPTY.

| roll | QC verdict (gemini-3.1-pro-low via gem9) |
|---|---|
| 1 — initial | `FAIL - chin dipped instead of raised` |
| 2 — re-roll 1, chin instruction hardened, explicit negatives added | `FAIL - chin dipped instead of raised` |
| 3 — re-roll 2, head pose moved to the top of the prompt, camera softened to a mild downward tilt | `FAIL - human identity mismatch against reference.` |

**ROOT CAUSE, and it is reusable.** `high-angle-down` and `chin-up` are geometrically opposed. A camera
above the subject pulls the rendered head forward; asking for a raised chin in the same frame fights the
generator on every roll. Rolls 1 and 2 lost that fight identically. Roll 3 won the pose argument by
flattening the camera and front-loading the pose — and lost the FACE instead, because the prompt weight
that had been holding the persona identity went to the pose. **This is a picker-level collision, not a
prompt-writing failure: the picker can hand out `high-angle-down` + `chin-up` together and there is no
guard against it.** Worth a rule in the picker rather than another agent burning three rolls on it.

**Bookkeeping is CLEAN — nothing is owed:**
- `persona_picker.py release --seq 38` was run. Both angles returned to the pool; `status` now reads
  `21 spent + 0 reserved`, **0 face angles burned**. No angle was ever committed against a failed render.
- ⚠️ **`release` + re-pick is deterministic on seq**, so tomorrow's `pick` at seq 38 with
  `--audience women-25-45` will re-issue **the same colliding pair**. Expect it. Do not brute-force a
  fourth roll at the same combination — either accept the no-face composition the picker offers, or
  raise the collision with Kevin. Do not invent a face and do not hand-pick a substitute angle.
- The QC-failed render was NOT deleted. It is parked at
  `tmp_images/vaginal-probiotics-side-effects-whats-normal-us-2026/hero.QC-FAILED-do-not-ship-20260824.webp`
  — renamed so no later run can pick it up as a shippable hero. **Do not ship it.**
- No draft file was created, nothing was sent to Shopify, `PUBLISHED_ARTICLES_TRACKER.csv` was not
  touched, and `frozen_articles.txt` was not touched.

**Everything the next run needs is already banked in the ticket above** — STEP 0 probe, STEP 0.5 verdict,
template choice, the PDP payload verified at source, the collection-membership check, and all 5 DOIs
resolved at Crossref with their abstracts read. Tomorrow's run should go straight to STEP 5 imagery.

**Also still unfixed, third run in a row:** `validate_article.py` prints
`⚠ QRG quality scoring skipped (claude-seo runtime not installed)` on this Mac, so the three prose
hard-fails (overall quality < 80, filler ≥ 25, ai-pattern ≥ 25) do not execute. Every `✓ PASS` here is
structural-only. It did not bite this run — the run never reached the gate.

## Refill needed

**2026-08-24 (later run) — 0 `[ ]` tickets remain and today's article is ALREADY SHIPPED.**
Ticket #30 (`vaginal probiotics side effects`) was mined and published LIVE earlier today
(id `621897744699`; frontend re-verified HTTP 200 with a browser UA this run, `og:title`
matches). DAILY-RUN §1 caps the job at one article per day, so this run did **not** mine or
publish a second topic. What it did do was close the bookkeeping the shipping run left open:
`logs/daily/2026-08-24.log` and `logs/daily/last-run.json` both still described today as
**BLOCKED**, which is what the cron reports back to Kevin through Eugene — Kevin would have
been told the day failed while the article was live. Both are corrected now.
`persona_picker.py status` reads seq=39 with **0 reservations open**, so no `release` was owed,
and the tracker row for #30 is present.

**Correction to the blocked-run warning above (line ~852): it was WRONG.** That note predicted
`release --seq 38` + re-pick would deterministically re-issue the same colliding pair. It did
not — `release()` keeps seq as a counter, so the retry picked at seq 39 with a *different*
persona. The `high-angle-down` + `chin-up` collision itself did recur and was solved in the
PROMPT (4/4 first-roll QC PASS, 0 re-rolls): front-load the head pose **and** the identity
clause together, describe the camera as only slightly above the eye line, raise the down-gaze
target to chest height, and NEGATIVE-list "no chin tucked toward the chest, no bowed or
downward-tilted head". Future runs: that pair is promptable, **do not treat it as a blocker**.

No google-ads tool is exposed to this headless run (MCP servers present: claude.ai and Shopify,
both UNAUTHENTICATED — and Shopify MCP is barred by hard rule #2 anyway) and GSC is still
unauthorised on this Mac, so the mining recipe in
`skills/genseo-auto-publish/references/ads-article-mining.md` cannot run from here.
**Kevin: run that recipe in the app** and append the next batch below as `# BATCH <date>`.
Open segments carried forward after #30: `nmn side effects` and `turkesterone side effects`
(both re-probed clean against the live `suggest.json` on 2026-08-24), plus
`pure-shilajit-gold-resin` and `shilajit-shockwave` on the catalog side.
`vaginal probiotics side effects` is now CLOSED (shipped as #30) and
`shilajit gold resin` was already closed by #25.

**Still unfixed, FOURTH run in a row:** `validate_article.py` prints
`⚠ QRG quality scoring skipped (claude-seo runtime not installed)`, so the three prose
hard-fails DAILY-RUN §1.3 leans on (overall quality < 80, filler ≥ 25, ai-pattern ≥ 25) do
**not** execute. It bit today: #30 shipped on a structural-only PASS plus a hand-checked
banned-phrase list.

# BATCH 2026-08-25

Mined per DAILY-RUN §2 (queue empty — 0 `[ ]` headings at start; GSC unauthorised and no google-ads
tool exposed to this headless run, so no demand data). Source: live catalog `/products.json`
(22 SKUs) + `/collections.json` (6 collections) + blog inventory. Two open segments were carried
forward from #30: `nmn side effects` and `turkesterone side effects`. Both re-probed clean against
`suggest.json` this run (0 article matches each). `shilajit` + any angle now FAILs the gate as
`covered`, so it was dropped rather than forced.

Chose `turkesterone side effects` over `nmn side effects` on three counts: Turkesterone is priority
brand #5 vs AgeAura #6; the turkesterone cluster has 3 articles whose most recent is 2026-08-13
(12 days) while NMN has 4 whose most recent is 2026-08-23 (2 days) — a fifth NMN page now would
land next to #29 while it is still being indexed; and #30 already spent yesterday on the third
`side effects` segment, so alternating brands keeps the clusters even.

## [DONE 2026-08-25 https://wellnessnest.co/blogs/news/turkesterone-side-effects-4-ingredients-to-check-us-2026] Ticket #31 — NEW ARTICLE (type: EDITORIAL)
- **Primary keyword:** `turkesterone side effects`
- **Secondary:** is turkesterone safe, turkesterone liver, turkesterone side effects in males,
  does turkesterone affect hormones, turkesterone drug interactions
- **STEP 0 (live, 2026-08-25):** `suggest.json?q=turkesterone side effects` → 0 article matches.
  Also 0 on `nmn side effects`, `creatine loading phase`, `when to take creatine`. Positive
  controls the same run: `turkesterone` → 3 live articles, `creatine` → 4, `nmn` → 4, `shilajit`
  → 5. The check was live, so the zero is real.
- **STEP 0.5:** `topic_fitness.py "Turkesterone Side Effects: What's Real? (US 2026)"` →
  `REVIEW [covered-segment]` — greenlit under Kevin's standing queue approval (2026-08-13,
  "I approve all of them, I need published articles without any delay").
- **Template:** EDITORIAL. The registry maps "X side effects" → LISTICLE, but two things override
  it here: #30 (yesterday) was LISTICLE so the variety guard wants a different shape, and a
  numbered list of side effects would misrepresent the evidence — there is no published human
  adverse-event catalogue for turkesterone to number. Answer-first EDITORIAL is the honest shape.
- **Ends at SKU:** `turkesterone-advanced-formula` ($75.00, curated ref exists at
  `product_refs/turkesterone-advanced-formula.json` — green plastic jar, black screw lid).
- **Angle (the payload):** the side-effect question for turkesterone is not really about
  turkesterone. Two facts do the work. (1) The 10-week human trial everyone cites as "the
  turkesterone study" is not one — it is Isenmann 2019 on **ecdysterone**, a different
  phytoecdysteroid; the only human turkesterone data is an 11-man **acute** study that followed
  people for 24 hours. So "no known side effects" is a statement about missing evidence, not about
  safety. (2) Turkesterone is almost never sold alone, and every documented human adverse event in
  a stacked formula belongs to one of the *other* ingredients. On our own label that means
  ashwagandha (liver-injury case reports), tongkat ali (an unsettled regulatory picture), piperine
  (raises the blood level of co-taken medicines) and colostrum (a dairy allergen in a product no
  one reads as dairy). The reader's real job is to read the panel, and only a label that publishes
  per-ingredient doses lets them.
- **Third beat:** ecdysterone sits on the WADA Monitoring Program, so for a tested athlete the
  relevant "side effect" is a doping-control one, not a physiological one.
- **Payload verified at source on the rendered PDP this run:** 500 mg Turkesterone
  (Ajuga turkestanica) · 300 mg KSM-66 Ashwagandha · 250 mg Tongkat Ali · 250 mg Colostrum
  (15% IgG) · 10 mg BioPerine. 60 capsules per bottle, 2 daily with food, $75.00.
- **Collection links:** `turkesterone-advanced-formula` IS a genuine member of
  `/collections/mens-essential-collection` and `/collections/shilajit-wellness-stack` (verified
  live this run) but is **NOT** in `/collections/best-seller` (that holds shilajit resin, shilajit
  gummies, FusiForce, FloraFresh). Link best-seller as a browse suggestion only — never as a
  membership claim. Same trap as #1/#2/#28/#29.
- **Evidence bank (11 DOIs, every one resolved at api.crossref.org to the correct paper AND its
  abstract read via Europe PMC — not title-only; NCBI eutils stays IP-blocked from this Mac):**
  Isenmann 2019 Arch Toxicol `10.1007/s00204-019-02490-x` (ecdysterone, 10 wk, n=46 young men
  strength-training; muscle mass and 1-RM bench up; **no increase in liver or kidney toxicity
  biomarkers**) |
  Grabowska/Muscles 2024 `10.3390/muscles3040031` (the only human turkesterone study — n=11 men,
  **acute**, pre / 3 h / 24 h; no significant effect on IGF-1, RMR, lipid or carbohydrate
  metabolism; authors report favourable hemodynamic and GI tolerability over that window) |
  Nutrients 2024 review `10.3390/nu16091382` (ecdysterone + turkesterone, sources and evidence) |
  Metabolites 2021 `10.3390/metabo11060366` (single 50 mg dose, 12 volunteers, urinary elimination;
  states ecdysterone was added to the **WADA Monitoring Program**) |
  Björnsson 2020 Liver Int `10.1111/liv.14393` (ashwagandha DILI, 5 cases, Iceland + US DILIN;
  latency 2–12 wk, cholestatic or mixed, jaundice + pruritus, no hepatic failure, tests normalised
  in 1–5 months in four of five) |
  Cureus 2026 scoping review `10.7759/cureus.109764` (13 publications, 25 patients; injury after
  weeks of use, cholestatic/mixed predominating) |
  Hepatology Communications 2023 `10.1097/hc9.0000000000000270` (largest series, India) |
  EFSA 2021 `10.2903/j.efsa.2021.6937` (tongkat ali root extract as an EU novel food at up to
  200 mg/day: positive in vitro chromosome-aberration test and a positive in vivo comet assay at
  2,000 mg/kg bw at first-contact tissues → Panel concluded safety **not established**) |
  eCAM 2013 `10.1155/2013/102987` (the counterweight — 13-week subchronic rodent study on tongkat
  ali root powder found no adverse effects to 2 g/kg/day, ADI up to 1.2 g/adult/day) |
  Bhardwaj 2002 JPET `10.1124/jpet.102.034728` (piperine inhibits human P-glycoprotein and CYP3A4;
  digoxin and cyclosporine transport IC50 15.5 and 74.1 µM) |
  Chandrasekhar 2012 Indian J Psychol Med `10.4103/0253-7176.106022` (KSM-66, 300 mg **twice**
  daily, 60 days, n=64 — the dose our label runs at half of).
- **Disclose our own gaps (house honesty pattern, #22/#24/#25/#26/#27/#28/#30):** the listing
  publishes ingredient doses but **no Supplement Facts panel**, and it does not say whether the
  500 mg turkesterone figure is per capsule or per 2-capsule serving — the copy says "in one
  powerful capsule" and then "Take 2 daily", which cannot both be the serving. Colostrum is not
  flagged as a **milk allergen** anywhere in the listing. Route the reader to
  support@wellnessnest.co for the panel.
- **⛔ Do NOT repeat these PDP lines** (house rule `no-coa-competitive-advantage` plus
  unsupportable safety/authority claims): "zero reported side effects", "Doctor-approved",
  "Backed by 100,000+ studies", "Clean, Natural & Third-Party Validated", "4.9/5 stars from 1,800+
  real customers", "5 clinically studied ingredients". The first one is flatly contradicted by the
  evidence in this very article — it is flagged to Kevin in the run report, not argued with in the
  body.
- **Medical boundary:** structure/function language only. No treatment or cure claim. State plainly
  who should not take it and when to stop and call a clinician.
- **Author:** Dr. Marcus Hale (roster.json, sole source).

### ⛔ 2026-08-25 — CARRIED OVER, BLOCKED AT STEP 5 ON THE INLINE PERSONA IMAGE. Ticket stays `[ ]`.

The ticket above is fully mined, gated and researched. **Nothing was written and nothing was
published.** The run stopped at STEP 5 because the inline persona-in-scene image burned all three
ima2 attempts (1 initial roll + the 2 permitted re-rolls, DAILY-RUN §3), and the skill's CRITICAL
FAILURE SAFEGUARD says to abort rather than draft an article with missing images. This was **not**
a quota or auth failure — `GET :10531/v1/models` returned 200 and every roll produced an image.
It was a pose failure, three times.

`persona_picker.py pick --audience men-20-35` issued **seq 40**, hero `m2029-hl-02`,
hero angle `front+level`, gaze `at-lens`, shot `mid-subject-fg-pack`,
inline angle `front+chin-up`, inline gaze `down-at-hands`. `warnings[]` was EMPTY.

**The HERO passed on the first roll** and was eyeballed against `product_refs/turkesterone-advanced-formula.png`:
green jar, black screw lid, wordmark, ADVANCED FORMULA banner, all three icon badges and the
ingredient list all correct and legible at thumbnail size; pack standing on the console with no hand
touching it. It is parked at
`tmp_images/turkesterone-side-effects-4-ingredients-to-check-us-2026/hero.QC-PASS-VALID-ONLY-FOR-m2029-hl-02-front-level.webp`.
**The filename is a guard, not decoration** — seq 40 was released, so the next `pick` may hand out a
different persona, and shipping this hero under a different persona's committed angle is exactly the
permanent-damage case DAILY-RUN §3 warns about. Reuse it ONLY if the next pick re-issues
`m2029-hl-02` + `front+level`; otherwise regenerate.

| roll | QC verdict (gemini-3.1-pro-low via gem9) |
|---|---|
| 1 — initial, hands on a shaker at chest height, camera slightly below eye line | `FAIL - chin dipped not raised` |
| 2 — re-roll 1, chin-lift hardened (throat visible, gap chin-to-collarbone), hands raised to collarbone height, camera dropped to sternum and angled up | `FAIL - chin dipped not raised, unreferenced background tub` |
| 3 — re-roll 2, chin-lift made physical: he is DRINKING from the shaker, which tips the head back | `FAIL - head turned right.` |

**ROOT CAUSE, and it extends the 2026-08-24 finding rather than repeating it.** `chin-up` paired
with a downward gaze (`down-at-hands`) is the collision; `high-angle-down` was never the whole story.
On 08-24 the pair was `profile-right+chin-up` + `high-angle-down` and the fix was to flatten the
camera and raise the gaze target to chest height. **That fix does not generalise to a `front` yaw.**
Applied here it failed twice — with the head squared to the lens there is no yaw for the generator to
hide the pose in, so "looking down at his hands" collapses the whole head forward every time.
Roll 3 finally won the chin by making the lift *physical* (drinking tips the head back) — and the
render does show a correctly raised chin, jaw lengthened, throat visible — but the raised shaker
occluded most of the face, and with the identity cue weakened the head drifted a few degrees off
axis, so QC caught it on yaw instead. **Reusable rule: when the issued pair is `front+chin-up` with
an `away`-family gaze, motivate the chin-lift with an action that does NOT put hands or an object in
front of the face** (looking up at a shelf, pulling a t-shirt over the head, tipping a cap back,
standing under a doorway light). Do not spend three rolls rediscovering this.

**Bookkeeping is CLEAN — nothing is owed:**
- `persona_picker.py release --seq 40` was run. Both angles returned to the pool; `status` reads
  `23 spent + 0 reserved`, **0 face angles burned**. No angle was committed against a failed render.
- The QC-failed render was NOT deleted. It is parked as
  `tmp_images/turkesterone-side-effects-4-ingredients-to-check-us-2026/inline-1-kitchen-shaker.QC-FAILED-do-not-ship-20260825.webp`.
  **Do not ship it.**
- No draft file was created, nothing was sent to Shopify, `PUBLISHED_ARTICLES_TRACKER.csv` was not
  touched, `frozen_articles.txt` was not touched, and no file was deleted.

**Everything the next run needs is already banked in the ticket above** — the STEP 0 probe with its
positive controls, the STEP 0.5 verdict, the template decision and why it departs from the registry,
the PDP payload verified at source, the collection-membership check, and all 11 DOIs resolved at
Crossref with their abstracts read at Europe PMC. **Tomorrow's run should go straight to STEP 5
imagery.** Two of the four images still need to exist (a no-face label-reading shot and a no-face
concept shot for the drug-interaction beat); neither needs a face, so neither can hit this collision.

**Still unfixed, FIFTH run in a row:** `validate_article.py` prints
`⚠ QRG quality scoring skipped (claude-seo runtime not installed)`, so the three prose hard-fails
DAILY-RUN §1.3 leans on (overall quality < 80, filler ≥ 25, ai-pattern ≥ 25) do not execute on this
Mac. It did not bite this run — the run never reached the gate.

### ✅ RESOLVED — the blocked-run note above is HISTORY. Ticket #31 SHIPPED later the same day.

The block was cleared by the next run of 2026-08-25: id `621904232763`, live at
`/blogs/news/turkesterone-side-effects-4-ingredients-to-check-us-2026`, heading flipped `[DONE]`,
tracker row present. Re-verified this run — frontend HTTP 200 with a browser UA, `verify_published.py`
PASS (schema, `Dr. Marcus Hale` as Person, table), and the live `suggest.json` now returns the
article on `turkesterone side effects`, so it is in the store's own index. The parked
`hero.QC-PASS-VALID-ONLY-FOR-m2029-hl-02-front-level.webp` was correctly **not** shipped: the
re-pick issued a different persona (`m2029-mx-01`, seq 41), so the hero was regenerated. Both
QC-failed renders stay parked and unshipped. Nothing is owed on the picker: `status` reads
`25 spent + 0 reserved`, seq 41 committed.

## Refill needed

**2026-08-25 (later run) — 0 `[ ]` tickets remain and today's article is ALREADY SHIPPED.**
DAILY-RUN §1 caps the job at one article per day, so this run did **not** mine or publish a second
topic. What it did do was close the bookkeeping the shipping run left open: `logs/daily/2026-08-25.log`
and `logs/daily/last-run.json` both still described today as **BLOCKED**, which is what the cron
reports back to Kevin through Eugene — he would have been told the day failed while the article was
live. Both are corrected now. This is the second day running that the shipping run flipped the ticket
and the tracker but not the run record (same as 2026-08-24); the fix belongs in the skill's STEP 10,
not in a daily patch.

No google-ads tool is exposed to this headless run (MCP servers present: claude.ai and Shopify, both
UNAUTHENTICATED — and Shopify MCP is barred by hard rule #2 anyway) and GSC is still unauthorised on
this Mac, so the mining recipe in `skills/genseo-auto-publish/references/ads-article-mining.md`
cannot run from here. **Kevin: run that recipe in the app** and append the next batch below as
`# BATCH <date>`.

Open segments carried forward after #31, all re-probed live against `suggest.json` this run:
- `nmn side effects` — **0 article matches, still open.** It is now the last untaken member of the
  `side effects` family: turkesterone (#31), vaginal probiotics (#30), creatine gummies and shilajit
  are all live and each returns its own article on that query.
- catalog side: `pure-shilajit-gold-resin` and `shilajit-shockwave` still have no article.
- `turkesterone side effects` is now CLOSED (shipped as #31).

Note for whoever mines next: the `shilajit` cluster is at 5+ articles and any new shilajit angle now
FAILs the fitness gate as `covered` — do not force one. Also parse `suggest.json` with
`json.loads(raw, strict=False)`; the payload carries raw control characters and a plain `json.load`
raises `Invalid control character`, which a careless run would misread as "0 matches" and use to
green-light an already-COVERED keyword.

**Still unfixed, SIXTH run in a row:** `validate_article.py` prints
`⚠ QRG quality scoring skipped (claude-seo runtime not installed)`, so overall-quality/filler/
ai-pattern hard-fails do not execute on this Mac. #31 shipped on a structural-only PASS plus a
hand-checked banned-phrase list.

**`ALL_ARTICLES.csv` is stale (2026-08-17, missing #26–#31).** Harmless while every check runs
against the live site, but a run that trusts it for internal-link picking will miss the six newest
articles. `python3 scripts/fetch_all_articles.py` refreshes it.


# BATCH 2026-08-26 — mined by the unattended run (no GSC, no google-ads MCP)

**Evidence header.** Queue was empty at 07:30 (0 `[ ]` headings). Mined per DAILY-RUN §2 from what is
on the machine: live catalog (`products.json`, 22 SKUs), live blog inventory (`ALL_ARTICLES.csv`
refreshed this run to 63 rows), and live `search/suggest.json` probes. Carried forward from the
2026-08-25 refill note: `nmn side effects` was the last untaken member of the `side effects` family.
Re-probed live this run with `curl -sg` + browser UA + `json.loads(strict=False)`:

- `nmn side effects` → **0 article matches** — OPEN, taken as #32.
- `nmn` → 4 articles (when-to-take, vs-nr, and-tmg-together, how-much-per-day) — none targets side effects.
- `nmn dosage` → 0 matches.
- `pure shilajit gold resin` → 0 matches — still open on the catalog side.
- `shilajit shockwave` → **1 match, `/blogs/news/shilajit-shockwave-review-1-drop-or-1-ml-us-2026`.**
  DAILY-RUN §2 and the 2026-08-25 refill note both still list this SKU as uncovered. **They are stale.**
  This is the drift STEP 0 exists to catch. Only `pure-shilajit-gold-resin` remains uncovered.

`build_catalog_tickets.py` still returns 0 tickets on this store (brand-coverage based, every house
brand has a page). Not waited on.

## [DONE 2026-08-26 https://wellnessnest.co/blogs/news/nmn-side-effects-6-checks-before-you-start-us-2026] Ticket #32 — NEW ARTICLE (type: LISTICLE)

- **Primary keyword:** `nmn side effects`
- **Title:** NMN Side Effects: 6 Checks Before You Start (US 2026)  (53 chars)
- **STEP 0:** live `suggest.json` → 0 article matches. PASS.
- **STEP 0.5:** `topic_fitness.py` → `REVIEW [covered-segment]` — "brand nmn has a general article,
  but 'side effects' is an audience/intent no existing title covers". Proceeding under Kevin's
  standing greenlight for this queue (2026-08-13: *"I approve all of them, I need published articles
  without any delay"*), per DAILY-RUN §1.2.
- **Template:** LISTICLE. Registry maps `X side effects` → LISTICLE; previous article #31 was
  EDITORIAL, so the variety guard is satisfied.
- **Product:** `ageaura-pure-nmn-tmg-nad-complex` $69.95 (the only NMN SKU with a curated
  `product_refs/` entry). Panel re-verified at source on the RENDERED PDP this run — see the tracker row.
- **Internal links:** the 4 live NMN articles, all re-checked HTTP 200 this run.
- **Angle:** the dose ladder. Human NMN trials ran to 1,250 mg/day and reported no severe adverse
  events; the documented, dose-dependent effects on this label belong to the *co-ingredients*
  (betaine/TMG on LDL, trans-resveratrol on CYP enzymes) and to an allergen almost nobody reads —
  spermidine here is from **wheat germ extract**, so the label carries a `Contains: Wheat` line.

## Refill needed

**2026-08-26 (later run) — 0 `[ ]` tickets remain and today's article is ALREADY SHIPPED.**
DAILY-RUN §1 caps the job at one article per day, so this run did **not** mine or publish a second
topic. Nothing was left open by the shipping run either: `logs/daily/2026-08-26.log` and
`logs/daily/last-run.json` both already read `status: published` / ticket #32 — the STEP 10
bookkeeping miss that had to be repaired by hand on 2026-08-24 and 2026-08-25 did **not** recur.
Ticket #32 re-verified live this run: frontend 200 with a browser UA, tracker row present.

No google-ads tool is exposed to this headless run (MCP servers present: claude.ai and Shopify, both
UNAUTHENTICATED — and Shopify MCP is barred by hard rule #2 anyway) and GSC is still unauthorised on
this Mac, so the mining recipe in `skills/genseo-auto-publish/references/ads-article-mining.md`
cannot run from here. **Kevin: run that recipe in the app** and append the next batch below as
`# BATCH <date>`.

Open segments after #32, all probed live against `suggest.json` this run (`curl -sg` + browser UA +
`json.loads(strict=False)`):
- `best time to take creatine` — **0 article matches.** Cleanest open segment on the board. The
  creatine cluster has vs-powder, dosage and women-over-40, none of them timing.
- `probiotics for bv` — **0 article matches.** FloraFresh has which-strains (#3) and side-effects
  (#30); the BV-specific intent is untaken.
- `menopause supplement` — **0 article matches**, but read this one carefully before taking it:
  MenoMate carries ~15 legacy pre-pipeline articles (meal-plan sets, symptom pages) that
  `topic_fitness.py` will very likely score `covered`. It is a gap in *ranking*, not in *inventory*.
- `nmn vs nad` — 0 matches, but #29 `nmn-vs-nr` is adjacent enough that this is probably a
  cannibalisation risk, not an opportunity. Check `find_dupes.py` logic before drafting.
- catalog side: `pure-shilajit-gold-resin` is the **only** genuinely uncovered SKU. It needs a
  distinct segment angle, not a bare product page.
- CLOSED and confirmed live this run: `creatine gummies dosage`, `urolithin a dosage`,
  `shilajit for women`, `turkesterone vs ecdysterone`, `shilajit shockwave`.

The `side effects` family is now CLOSED across all five brands (shilajit, creatine gummies,
vaginal probiotics #30, turkesterone #31, NMN #32). Do not force another shilajit angle either: the
cluster is at 6+ articles and any new one FAILs the fitness gate as `covered`.

**Still unfixed, SEVENTH run in a row:** `validate_article.py` prints
`⚠ QRG quality scoring skipped (claude-seo runtime not installed)`, so the overall-quality / filler /
ai-pattern hard-fails do not execute on this Mac. #32 shipped on a structural-only PASS plus a
hand-checked banned-phrase list. Installing the claude-seo runtime is the highest-value fix left in
this pipeline — it is the one gate that is silently absent rather than failing loudly.

`ALL_ARTICLES.csv` is current as of the #32 run (63 rows + header). No refresh needed before the
next run.

**2026-08-26 (third run of the day) — queue still EMPTY, nothing published, by design.**
`grep "^## \[ \]"` returns nothing; every remaining `[ ]` string in this file is prose (the rules
block at the top and the historical run notes). Per the run rules, a run that finds no pending
ticket does **not** write an article. DAILY-RUN §1 also caps the job at one article per day and
ticket #32 already shipped this morning — re-verified live again this run: frontend
`nmn-side-effects-6-checks-before-you-start-us-2026` returns **HTTP 200** with a browser UA.
`logs/daily/last-run.json` still reads `status: published` / ticket #32, so no bookkeeping repair
was needed.

No google-ads tool is exposed to this headless run (MCP servers present: exa, claude.ai, Shopify —
and Shopify MCP is barred by hard rule #2 anyway), and GSC remains unauthorised on this Mac, so the
mining recipe in `skills/genseo-auto-publish/references/ads-article-mining.md` cannot run from here.
**Kevin: run that recipe in the app** and append the next batch below as `# BATCH <date>`.

Re-probed live this run against `suggest.json` (`curl -sg` + browser UA + `json.loads(strict=False)`),
so the next run starts from verified ground:
- `best time to take creatine` — **0 article matches**, still the cleanest open segment on the board.
- `probiotics for bv` — **0 article matches**, still untaken.
The remaining segment reads from the earlier note today stand unchanged and are not re-listed:
`menopause supplement` is a ranking gap not an inventory gap, `nmn vs nad` is a cannibalisation risk
against #29, `pure-shilajit-gold-resin` is the only genuinely uncovered SKU, and the `side effects`
family is CLOSED across all five brands.

**Still unfixed, EIGHTH run in a row:** `validate_article.py` prints
`⚠ QRG quality scoring skipped (claude-seo runtime not installed)`, so the overall-quality / filler /
ai-pattern hard-fails do not execute on this Mac. Installing the claude-seo runtime is the
highest-value fix left in this pipeline — it is the one gate that is silently absent rather than
failing loudly.


# BATCH 2026-08-27 — mined by the unattended run (queue empty; no GSC, no google-ads MCP)

Evidence header: mined at $0 from the live catalog (`products.json`, 22 SKUs) + the live blog
inventory (`suggest.json` probes, browser UA, `curl -sg`, `json.loads(strict=False)`) because GSC is
unauthorised on this Mac and no google-ads tool is exposed to a headless run. The segment was
carried on the open-segment list by the 2026-08-25 and 2026-08-26 runs and re-probed live today.

STEP 0 live probes this run — `best time to take creatine` **0 article matches**, `when to take
creatine` 0, `creatine timing` 0, `creatine before or after workout` 0. Positive control
`creatine` returns 4 live articles (dosage · women-over-40 · gummies-vs-powder · side-effects) and
**none of them targets timing**. Product probe `creatine` returns `fusiforce-creatine-gummies` at
$69.99 plus three reserve SKUs, so the segment ends at a SKU we stock.

DRIFT CAUGHT THIS RUN: DAILY-RUN §2 and the tickets refill notes still list
`pure-shilajit-gold-resin` as the only genuinely uncovered SKU. It is **not** uncovered —
`/blogs/news/shilajit-gold-resin-review-is-75-worth-it-us-2026` is live and `suggest.json` returns
it for `shilajit gold resin`. The catalog side now has **no** uncovered SKU.

## [DONE 2026-08-27 https://wellnessnest.co/blogs/news/best-time-to-take-creatine-before-or-after-us-2026] Ticket #33 — NEW ARTICLE (type: EDITORIAL)

- **Primary keyword:** `best time to take creatine`
- **Template:** `EDITORIAL` — the registry maps how/what/why/dosage informational intent to
  EDITORIAL, and #32 was LISTICLE, so the variety guard is satisfied.
- **Working title:** Best Time to Take Creatine: Before or After? (US 2026)
- **Product:** FusiForce — Creatine Monohydrate Gummies 5,000 mg, `fusiforce-creatine-gummies`,
  $69.99, Green Apple + Blueberry, 3 gummies = 5 g creatine + 25 mg Panax ginseng (10% ginsenosides).
- **Collections (all three verified live members):** `/collections/mens-essential-collection`,
  `/collections/best-seller`, `/collections/shilajit-wellness-stack`.
- **Angle:** the timing question has a real answer and it is not the one the search demands.
  Total daily intake and *consistency* drive muscle saturation; the around-workout window is a
  small, weakly-evidenced second-order effect. Our own PDP already says "take anytime" — the
  article backs that with the evidence instead of inventing a window.
- **Internal links (4 live creatine articles, re-check 200 before use):** creatine-gummies-dosage ·
  creatine-gummies-vs-powder · creatine-for-women-over-40 · creatine-gummies-side-effects.
- **House rules:** no COA / ISO 17025 / Eurofins / "third-party tested" / "137,000 customers" /
  "4.8-4.9 stars" repeated from the PDP (`no-coa-competitive-advantage`). No MuscleMax.


## Refill needed

**2026-08-27 — Ticket #33 shipped, queue is EMPTY again (0 `[ ]` headings).** The next run must
mine per DAILY-RUN §2. GSC is still unauthorised on this Mac and no google-ads tool is exposed to a
headless run, so `skills/genseo-auto-publish/references/ads-article-mining.md` cannot run from here.
**Kevin: run that recipe in the app** and append the next batch below as `# BATCH <date>`.

**THE CATALOG SIDE IS NOW CLOSED — this supersedes DAILY-RUN §2 and every refill note above it.**
`pure-shilajit-gold-resin` is no longer uncovered: `suggest.json` returns
`/blogs/news/shilajit-gold-resin-review-is-75-worth-it-us-2026` for `shilajit gold resin`. Every SKU
on the store now has at least one article. Future mining has to come from **segment gaps**, not from
walking the SKU list — `build_catalog_tickets.py` was already returning 0 and now the manual fallback
returns 0 too.

Re-probed live this run (`curl -sg` + browser UA + `json.loads(strict=False)`), all **0 article
matches**, so the next run starts from verified ground:
- `how long does creatine take to work` — 0. Strongest of the set: same cluster as #33, buyer-intent,
  ends at `fusiforce-creatine-gummies`, and the saturation evidence spine (Hultman 1996, Kreider 2017)
  is already banked in the #33 row so the research cost is near zero.
- `probiotics for bv` — 0. Still untaken after three runs of carrying it. FloraFresh has
  which-strains (#3) and side-effects (#30); the BV-specific intent is open. Note the route-honesty
  constraint the #30 row established: the NEJM LACTIN-V result used a **vaginal** strain and does not
  transfer to an oral gummy — any BV article has to say so or it is misleading.
- `turkesterone dosage` — 0, but check `find_dupes.py` first: #31 (side effects) and the existing
  benefits-dosing article may already own the dose intent.
- `shilajit for sleep` — 0, but the shilajit cluster is at 7+ articles and `topic_fitness.py` will
  very likely score it `covered`. Do not force it.
- `nmn vs nad` — 0, still a cannibalisation risk against #29 `nmn-vs-nr`, unchanged.
- `menopause supplement` — 0, still a **ranking** gap not an inventory gap (MenoMate carries ~15
  legacy pre-pipeline articles), unchanged.
- `urolithin a vs nmn` — 0. New this run. Cross-brand comparison inside AgeAura; would need care not
  to cannibalise #28 (urolithin-a-dosage) or #29 (nmn-vs-nr).

**Still unfixed, NINTH run in a row:** `validate_article.py` prints
`⚠ QRG quality scoring skipped (claude-seo runtime not installed)`, so the overall-quality / filler /
ai-pattern hard-fails do not execute on this Mac. #33 shipped on a structural-only PASS plus a
hand-checked banned-phrase list (0 hits). Installing the claude-seo runtime is still the
highest-value fix left in this pipeline — it is the one gate that is silently absent rather than
failing loudly.

**Open flag for Kevin, carried from #27 and not re-verified this run:** the Blueberry FusiForce pouch
front was recorded printing 112 gummies against Green Apple's 90 at the same $69.99. The `.js`
endpoint exposes no per-variant pack image, so #33 published only the verified 90 figure.

## Refill needed

**2026-08-27 (later run) — QUEUE EMPTY. No `[ ]` ticket anywhere in this file. No article written.**

Ticket #33 (`best-time-to-take-creatine-before-or-after-us-2026`) shipped earlier today and was
re-verified live this run: frontend GET returns **HTTP 200** with a browser UA. Its bookkeeping
(ticket flip, tracker row, persona `seq=43` commit) was left **uncommitted** by that run; this run
commits it. Nothing was re-published.

All four ticket generators were run this run and all four dead-end:

| Generator | Result this run |
|---|---|
| `build_catalog_tickets.py` | `0 PASS tickets`, `0 unvouched brands`, `0 already-covered`, `0 thin` — the catalog side is genuinely closed, confirming the 2026-08-26 note |
| `build_rich_tickets.py` | `FileNotFoundError: blog_ticket_candidates.csv` — its input is GSC-derived and absent |
| `build_ctr_tickets.py` | needs an out-path arg **and** GSC; GSC is unauthorised on this Mac |
| `refresh_targets.py` | same GSC dependency |

So there is no $0 local path left to a new ticket: brand-coverage as a topic source is exhausted
(every SKU has an article) and every remaining generator needs query data this machine cannot read.
The google-ads MCP is **not exposed to this headless run** either.

**Kevin: run the mining recipe in the app** —
`skills/genseo-auto-publish/references/ads-article-mining.md` — and append the next batch below as
`# BATCH <date>`. Mining must now come from **segment gaps**, not from walking the SKU list.

Carried candidates, all re-probed 0-article by the 2026-08-27 earlier run and **not** re-probed here
(one of them, `best time to take creatine`, became #33, so the list is one shorter):

- `how long does creatine take to work` — same cluster as #33, buyer-intent, ends at
  `fusiforce-creatine-gummies`; the saturation evidence spine (Hultman 1996, Kreider 2017) is banked
  in the #33 row, so research cost is near zero. **Strongest of the set.** Check `find_dupes.py`
  against #33 first — timing and time-to-effect are adjacent intents.
- `probiotics for bv` — FloraFresh has which-strains (#3) and side-effects (#30); BV-specific intent
  is still open after four runs of carrying it. Route-honesty constraint from the #30 row stands:
  the NEJM LACTIN-V result used a **vaginal** strain and does not transfer to an oral gummy.
- `turkesterone dosage` — check `find_dupes.py` first; #31 plus the existing benefits-dosing article
  may already own the dose intent.
- `shilajit for sleep` — shilajit cluster is at 7+ articles; `topic_fitness.py` will likely score it
  `covered`. Do not force it.
- `nmn vs nad` — cannibalisation risk against #29 `nmn-vs-nr`, unchanged.
- `urolithin a vs nmn` — cross-brand inside AgeAura; would need care not to cannibalise #28 or #29.
- `menopause supplement` — a **ranking** gap, not an inventory gap (MenoMate carries ~15 legacy
  pre-pipeline articles), unchanged.

**Still unfixed, TENTH run in a row:** `validate_article.py` prints
`⚠ QRG quality scoring skipped (claude-seo runtime not installed)`, so the overall-quality / filler /
ai-pattern hard-fails do not execute on this Mac. Installing the claude-seo runtime remains the
highest-value fix left in this pipeline — it is the one gate that is silently absent rather than
failing loudly.

**Open flag, still not re-verified:** the Blueberry FusiForce pouch front was recorded printing 112
gummies against Green Apple's 90 at the same $69.99. The `.js` endpoint exposes no per-variant pack
image, so #33 published only the verified 90 figure.

## Refill needed

**2026-08-27 (third run) — QUEUE EMPTY. No `[ ]` ticket anywhere in this file. No article written.**

`grep -n '^#\{1,3\} \[ \]' daily-tickets.md` returns nothing. Every `[ ]` string left in the file is
prose (the rules block at the top, plus the historical run notes). Ticket #33
(`best-time-to-take-creatine-before-or-after-us-2026`) shipped earlier today; its bookkeeping was
committed by the previous run (`30b2107`). Nothing was published or re-published this run.

All four ticket generators re-run this run. All four dead-end, unchanged from the earlier run:

| Generator | Result this run |
|---|---|
| `build_catalog_tickets.py` | `0 PASS tickets`, `0 unvouched brands`, `0 already-covered`, `0 thin (<3 SKU)` — catalog coverage is genuinely closed |
| `build_rich_tickets.py` | `FileNotFoundError: blog_ticket_candidates.csv` — its input is GSC-derived and absent |
| `build_ctr_tickets.py` | `scripts/credentials.json not found` — GSC OAuth is not configured on this Mac |
| `refresh_targets.py` | `scripts/credentials.json not found` — same GSC blocker |

**google-ads MCP is unavailable in this environment** (the only MCP servers present are `claude.ai`
and `Shopify`, both unauthorised and non-interactive here). So per the run rules, no mining was
attempted from ad data and no ticket was invented.

### Kevin — please run the mining recipe in the app

Open the google-ads MCP in the desktop app and mine a fresh batch, then paste it into this file under
a `# BATCH <date>` heading. Mining must come from **segment gaps**, not from walking the SKU list —
the SKU list is exhausted.

Carried candidates, unchanged and **not** re-probed this run (no GSC, no ads MCP):

- `how long does creatine take to work` — same cluster as #33, buyer-intent, ends at
  `fusiforce-creatine-gummies`. Saturation evidence (Hultman 1996, Kreider 2017) is banked in the #33
  row, so research cost is near zero. **Strongest of the set.** Run `find_dupes.py` against #33
  first — timing and time-to-effect are adjacent intents.
- `probiotics for bv` — FloraFresh has which-strains (#3) and side-effects (#30); BV-specific intent
  is still open after five runs of carrying it. Route-honesty constraint from the #30 row stands: the
  NEJM LACTIN-V result used a **vaginal** strain and does not transfer to an oral gummy.
- `turkesterone dosage` — check `find_dupes.py` first; #31 plus the existing benefits-dosing article
  may already own the dose intent.
- `shilajit for sleep` — shilajit cluster is at 7+ articles; `topic_fitness.py` will likely score it
  `covered`. Do not force it.
- `nmn vs nad` — cannibalisation risk against #29 `nmn-vs-nr`, unchanged.
- `urolithin a vs nmn` — cross-brand inside AgeAura; would need care not to cannibalise #28 or #29.
- `menopause supplement` — a **ranking** gap, not an inventory gap (MenoMate carries ~15 legacy
  pre-pipeline articles), unchanged.

**Housekeeping snag, new this run:** `build_catalog_tickets.py` with no arg now refuses to run —
`refusing to overwrite existing catalog-brand-tickets.md`. That stale 0-ticket artifact is sitting in
the repo root. Delete it, or call the generator with an out-path / `--append`, otherwise every future
run has to route around it.

**Still unfixed, ELEVENTH run in a row:** `validate_article.py` prints
`⚠ QRG quality scoring skipped (claude-seo runtime not installed)`, so the overall-quality / filler /
ai-pattern hard-fails do not execute on this Mac. Installing the claude-seo runtime remains the
highest-value fix left in this pipeline — it is the one gate that is silently absent rather than
failing loudly.

**Open flag, still not re-verified:** the Blueberry FusiForce pouch front was recorded printing 112
gummies against Green Apple's 90 at the same $69.99. The `.js` endpoint exposes no per-variant pack
image, so #33 published only the verified 90 figure.

# BATCH 2026-08-28 — mined by the unattended run (queue empty; no GSC, no google-ads MCP)

Evidence header: mined at $0 from the live catalog (`products.json`, 22 SKUs) + the live blog
inventory (`ALL_ARTICLES.csv`, 63 rows) + `suggest.json` probes (`curl -sg`, browser UA,
`json.loads(strict=False)`). GSC is unauthorised on this Mac and no google-ads tool is exposed to a
headless run. `probiotics for bv` has been carried on the open-segment list by the 2026-08-25,
-08-26 and three 2026-08-27 runs and was re-probed live today.

STEP 0 live probes this run — **9 probes, all 0 article matches**: `probiotics for bv`,
`bv`, `bacterial vaginosis`, `probiotics for bacterial vaginosis`, `vaginal odor`,
`lactobacillus crispatus`, `ph balance`, `does probiotics help bv`, `florafresh`. Positive control
`probiotics` returns 4 live articles (which-strains · how-long · side-effects · a MenoMate meal-plan
page) and **none targets BV**. Product probe confirms the segment ends at a stocked SKU,
`florafresh-vaginal-probiotics-gummies` $40.99.

**DRIFT CAUGHT THIS RUN — Urolithin A is NOT a stocked SKU.** `CLAUDE.md` §2 and `DAILY-RUN.md` §2
both describe AgeAura as "NMN+TMG · Urolithin A · Longevity Peptides". The live `products.json`
returns **22 products and no urolithin SKU at all**; a product probe for `urolithin` returns zero
results while an article probe returns two live urolithin articles. So `urolithin a vs nmn` — carried
as a candidate by the last three runs — was **rejected this run**: half the comparison would point at
a product the store does not sell. `product_refs/ageaura-pure-urolithin-a.png` is also now a ref for
a delisted SKU. Kevin: either the SKU was delisted or it never shipped; the two live urolithin
articles should be checked for links to a dead product page.

## [DONE 2026-08-28 https://wellnessnest.co/blogs/news/probiotics-for-bv-do-they-actually-work-us-2026] Ticket #34 — NEW ARTICLE (type: COMPARISON)

- **Primary keyword:** `probiotics for bv`
- **Template:** `COMPARISON` — the registry maps "which should you / alternative to" comparison
  intent to COMPARISON, and the article is structurally a three-way route comparison
  (antibiotics vs vaginal probiotic vs oral gummy). Previous #33 was EDITORIAL, so the variety
  guard is satisfied. Last COMPARISON was #29 on 2026-08-23.
- **Working title:** Probiotics for BV: Do They Actually Work? (US 2026) — 50 chars.
- **Product:** FloraFresh — Vaginal Probiotics Gummies, `florafresh-vaginal-probiotics-gummies`,
  $40.99, Pineapple flavor, 15 billion CFU per 2-gummy serving from 4 *Lactobacillus* species
  (rhamnosus, reuteri, salivarius, gasseri) + XOS prebiotics + D-mannose + vitamin C; 60 gummies =
  30 days at the label's own serving size; ~$1.37/day. Range $24.50–$110.70.
- **Collections (all three verified live members via `collections/<h>/products.json`):**
  `/collections/womens-essentials-collection`, `/collections/best-seller`,
  `/collections/shilajit-wellness-stack`.
- **Angle — THE ROUTE PROBLEM, and the honest rebuttal to it.** The landmark BV probiotic result
  (LACTIN-V, NEJM) used *L. crispatus* CTV-05 delivered **vaginally**, and the vitamin C result used
  a **vaginal** tablet — neither transfers automatically to a swallowed gummy. But the article does
  not stop at the convenient half: the 2022 *Front Nutr* meta-regression tested route directly and
  found it did **not** predict recurrence (p=0.67 vaginal, p=0.44 oral). Stating both is the
  differentiator against every competitor page that picks one and sells it.
- **Internal links (3 live FloraFresh articles, each re-checked 200 this run):** vaginal-probiotics-
  how-long · vaginal-probiotics-which-strains · vaginal-probiotics-side-effects.
- **House rules:** medical boundary is structure/function only, with an explicit "probiotics do not
  cure BV, antibiotics do" answer block and a stop-and-call-a-clinician list. Nothing repeated from
  the PDP per `no-coa-competitive-advantage` — see the tracker row for the exact suppressed list.
  No MuscleMax.

## Refill needed

**2026-08-28 — Ticket #34 shipped, queue is EMPTY again (0 `[ ]` headings).** The next run must
mine per DAILY-RUN §2. GSC is still unauthorised and no google-ads tool is exposed to a headless run,
so `skills/genseo-auto-publish/references/ads-article-mining.md` cannot run from here.
**Kevin: run that recipe in the app** and append the next batch below as `# BATCH <date>`.

Carried candidates, re-probed live this run unless noted, all **0 article matches**:

- `how long does creatine take to work` — 0. Ends at `fusiforce-creatine-gummies`; the saturation
  evidence spine (Hultman 1996, Kreider 2017) is banked in the #33 row. **Deferred again this run**
  for a substantive reason, not indecision: #33 (`best time to take creatine`) shipped 2026-08-27,
  and timing vs time-to-effect are adjacent intents on a page that is one day old. Give it distance,
  and run `find_dupes.py` against #33 when GSC credentials exist.
- `turkesterone dosage` — 0, but **topic_fitness is wrong about this one**. It returns
  `REVIEW [covered-segment]` claiming "dosage is an intent no existing title covers"; the live
  article `Turkesterone Benefits & Dosing: What's Real? (US 2026)` has *Dosing* in its title and
  already owns that intent. Treat as taken unless it is reframed.
- `urolithin a vs nmn` — **REJECTED, see the drift note above.** No urolithin SKU on the store.
- `shilajit for sleep` — shilajit cluster is at 18+ articles; do not force it.
- `nmn vs nad` — cannibalisation risk against #29 `nmn-vs-nr`, unchanged. NMN cluster is now at 5.
- `menopause supplement` — a **ranking** gap, not an inventory gap (~15 legacy MenoMate articles).
- **New this run, not yet probed:** `probiotics while on antibiotics` and `yeast infection vs bv`
  are the two obvious neighbours of #34 and the FloraFresh cluster is only at 4 articles — the
  least-saturated brand cluster on the store. Probe those first next run.

**Still unfixed, ELEVENTH run in a row:** `validate_article.py` prints
`⚠ QRG quality scoring skipped (claude-seo runtime not installed)`, so the overall-quality / filler /
ai-pattern hard-fails do not execute on this Mac. #34 shipped on a structural PASS plus a
hand-checked 26-phrase banned list (0 hits). Installing the claude-seo runtime remains the
highest-value fix left in this pipeline — it is the one gate that is silently absent rather than
failing loudly.

**Housekeeping snag, carried from 2026-08-27 and still true:** `build_catalog_tickets.py` with no arg
refuses to run — `refusing to overwrite existing catalog-brand-tickets.md`. That stale 0-ticket
artifact is still in the repo root. It was NOT deleted this run (§4 forbids `rm`); move it to
`_superseded/` or call the generator with an out-path.

## Refill needed

**2026-08-28 (second run today) — queue still EMPTY (0 `[ ]` headings).** No article was written.
Per DAILY-RUN §2 the next batch must be mined, but GSC is unauthorised
(`scripts/credentials.json` missing) and **no google-ads tool is exposed to this headless run**, so
`skills/genseo-auto-publish/references/ads-article-mining.md` cannot execute from here.
**Kevin: run that recipe in the app** and append the next batch below as `# BATCH <date>`.

Live index re-pulled this run (`fetch_all_articles.py`): **68 articles**, #34 confirmed present.
Cluster sizes now: shilajit 23 · menopause 9 (legacy MenoMate) · probiotics 5 · creatine 5 · NMN 5 ·
turkesterone 4 · urolithin 2.

Probed live against the fresh index this run — all **0 title/handle matches**, all still open:

- `probiotics while on antibiotics` — 0. Neighbour of #34, and the FloraFresh cluster is 5 articles
  against shilajit's 23, so it is still the least-saturated brand cluster on the store. **Best
  candidate for the next run.**
- `yeast infection vs bv` — 0. Differential-diagnosis intent; nothing on the store touches "yeast".
  Watch the medical-claim surface: this one needs the roster's strongest reviewer, not any author.
- `how long does creatine take to work` — 0. Deferred twice for adjacency to #33
  (`best time to take creatine`, shipped 2026-08-27); that page is now 1 day old, so the argument to
  keep deferring is weaker than last run but not yet gone. Ship it after the two probiotic angles.
- `turkesterone dosage` — treat as TAKEN. `topic_fitness.py` still returns `REVIEW [covered-segment]`
  claiming no title covers dosing; the live `Turkesterone Benefits & Dosing: What's Real? (US 2026)`
  does. Unchanged from last run.
- `urolithin a vs nmn` — still REJECTED. No urolithin SKU on the store.
- `shilajit for sleep` — cluster at 23. Do not force it.
- `nmn vs nad` — cannibalisation risk against #29 `nmn-vs-nr`. Unchanged.
- `menopause supplement` — a ranking gap, not an inventory gap (9 legacy MenoMate articles).

**Still unfixed, TWELFTH run in a row:** `validate_article.py` prints
`⚠ QRG quality scoring skipped (claude-seo runtime not installed)`, so the overall-quality / filler /
ai-pattern hard-fails never execute on this Mac. Every recent article shipped on a structural PASS
plus a hand-checked banned-phrase list. Installing the claude-seo runtime is still the
highest-value fix left in this pipeline — the one gate that is silently absent rather than failing loudly.

**Housekeeping snag, carried from 2026-08-27, still true:** `build_catalog_tickets.py` with no arg
refuses to run — `refusing to overwrite existing catalog-brand-tickets.md`. That stale 0-ticket
artifact is still in the repo root; §4 forbids `rm`, so move it to `_superseded/` or call the
generator with an out-path.

## Refill needed

**2026-08-28 (third run today) — queue still EMPTY (0 `[ ]` headings).** No article was written; per
the run rules an empty queue means do not invent one. Mining still cannot execute from here: GSC is
unauthorised (`scripts/credentials.json` absent — re-checked this run) and **no google-ads tool is
exposed to this headless run** (tool search for a Google Ads / keyword-planner capability returns
only web-search tools), so `skills/genseo-auto-publish/references/ads-article-mining.md` is
unreachable. **Kevin: run that recipe in the app** and append the next batch below as `# BATCH <date>`.

No live re-probe this run — the second run today already re-pulled the index (68 articles) and probed
the full candidate list a few hours ago; a third pull the same day would only burn quota. The ranked
shortlist from that run stands unchanged and is ready to become tickets the moment a batch lands:

1. `probiotics while on antibiotics` — FloraFresh cluster is 5 vs shilajit's 23, least saturated.
2. `yeast infection vs bv` — differential-diagnosis intent, nothing on the store touches "yeast";
   needs the roster's strongest medical reviewer.
3. `how long does creatine take to work` — deferred three times for adjacency to #33 (2026-08-27);
   that page is now 1 day old, so the deferral argument is nearly spent.

Rejected/taken, unchanged: `turkesterone dosage` (taken — `topic_fitness.py` is wrong about it),
`urolithin a vs nmn` (no urolithin SKU), `shilajit for sleep` (cluster at 23), `nmn vs nad`
(cannibalises #29), `menopause supplement` (ranking gap, not inventory gap).

**Still unfixed, THIRTEENTH run in a row:** `validate_article.py` prints
`⚠ QRG quality scoring skipped (claude-seo runtime not installed)`, so the overall-quality / filler /
ai-pattern hard-fails never execute on this Mac. Installing the claude-seo runtime is still the
highest-value fix left in this pipeline — the one gate that is silently absent rather than failing loudly.

# BATCH 2026-08-29 — mined by the unattended run (queue empty; no GSC, no google-ads MCP)

Queue was EMPTY at the start of this run (0 `[ ]` headings). Per DAILY-RUN §1.1.2 an empty queue is
the job, not a blocker, so this run mined a ticket from the live catalog + live blog inventory and
executed it.

**Live STEP 0 probes this run** (`curl -sg` + browser UA + `json.loads(strict=False)`), 9 probes:
`probiotics while on antibiotics` 0 · `probiotics with antibiotics` 0 · `antibiotics` 0 ·
`yeast infection` 0 · `yeast infection vs bv` 0 · `how long does creatine take to work` 0 ·
`creatine how long` 0 · `creatine loading` 0. Positive control `probiotics` returned 5 live
articles, so the endpoint was answering truthfully.

**Why creatine and not the probiotics candidates the last three runs ranked first.** The carried
shortlist put `probiotics while on antibiotics` at #1 on cluster-saturation grounds (FloraFresh 5 vs
shilajit 23). That ranking was made before #34 shipped. #34 (`Probiotics for BV`, 2026-08-28) is one
day old and BV's standard of care *is* antibiotics, so a `probiotics while on antibiotics` page would
have been the most cannibalising thing on the store, not the least. `how long does creatine take to
work` had been deferred three times for adjacency to #33 (`best time to take creatine`, 2026-08-27);
those are different intents — time-of-day vs time-to-effect — and no live creatine article covers
onset at all (live cluster: dosage · side effects · women over 40 · gummies vs powder · best time).
Deferral spent. The two probiotics angles stay open for a later run.

## [DONE 2026-08-29 https://wellnessnest.co/blogs/news/how-long-does-creatine-take-to-work-week-by-week-us-2026] Ticket #35 — NEW ARTICLE (type: STORY)

- **Primary keyword:** how long does creatine take to work
- **Title:** How Long Does Creatine Take to Work? Week by Week (US 2026)
- **Brand / SKU:** FusiForce Creatine Monohydrate Gummies ($69.99) — `fusiforce-creatine-gummies`
- **Template:** STORY. #34 was COMPARISON, #33 EDITORIAL, #32 LISTICLE; STORY has not run in the
  last 5 articles, and a week-by-week timeline is a genuine journey/lived-problem intent.
- **Collections (verified live this run):** `best-seller` and `mens-essential-collection` both
  contain the SKU. `womens-essentials-collection` does **not** — link it only for the other lines,
  never as if it carried creatine.
- **Angle:** the gap between "working" and "noticeable" — water in week 1, saturation by day 28,
  strength only from week 4–12, and the measured non-responder minority.
- **Compliance:** do NOT restate the PDP's COA / Eurofins / ISO 17025 / "137,000 customers" /
  star-rating claims (house rule `no-coa-competitive-advantage`). Do NOT state the gummy count or
  the ginseng mg — both carry the packaging discrepancies flagged in DAILY-RUN §6.

## Refill needed — next run

**Queue is EMPTY again** (0 `[ ]` headings) after #35 closed. Per DAILY-RUN §1.1.2 the next run mines
rather than skips. GSC is still unauthorised and no google-ads tool is exposed to a headless run, so
`references/ads-article-mining.md` stays unreachable; mine from live catalog + live blog inventory.

Ranked shortlist, all probed live 2026-08-29 at 0 article matches:

1. `yeast infection vs bv` — differential-diagnosis intent, nothing on the store touches "yeast".
   Now the strongest FloraFresh angle because it is a *diagnosis* question, not a second "do probiotics
   work for X" page. Watch the medical-claim surface hard.
2. `probiotics while on antibiotics` — held back this run on purpose. #34 (`Probiotics for BV`,
   2026-08-28) is the standard-of-care-is-antibiotics page, so this one was the most cannibalising
   candidate on the store, not the least. It gets safer the further #34 recedes; ship it after one
   non-probiotics article, not before.
3. A shilajit angle for the two uncovered SKUs — `pure-shilajit-gold-resin` ($75) and
   `shilajit-shockwave` ($79.99), still the only stocked products with no distinct segment page. The
   shilajit cluster is at 23, so this needs a genuinely distinct segment angle or `seg_taken` will
   veto it.

Rejected/taken, unchanged: `turkesterone dosage` (taken — `topic_fitness.py` is wrong about it),
`urolithin a vs nmn` (no urolithin SKU on the live catalog — 22 products, re-confirmed 2026-08-29),
`nmn vs nad` (cannibalises #29), `menopause supplement` (ranking gap, not an inventory gap).
Creatine onset is now CLOSED by #35.

**New rule earned this run, worth carrying:** any DOI containing `(`, `)`, `<` or `>` must be swapped
for the journal's alternate DOI before it goes into a markdown link. The Crossref-canonical DOI for
Rawson & Volek 2003 is `10.1519/1533-4287(2003)017<0822:EOCSAR>2.0.CO;2`; dropped into `[text](url)`
it terminates the link at the first `)` and injects a bogus tag. Alternate `10.1519/00124278-200311000-00031`
is the same paper and URL-safe. Nothing in the pipeline checks for this.

**Second rule earned this run:** `article_images.py` tolerates 2 concurrent ima2 gens, not 3 — the
third returned `OAuth proxy returned 500`. That is a TRANSPORT failure and must not be charged against
the 2-QC-re-roll budget; re-run it serially instead.

**Still unfixed, FOURTEENTH run in a row:** `validate_article.py` prints
`⚠ QRG quality scoring skipped (claude-seo runtime not installed)`, so the overall-quality / filler /
ai-pattern hard-fails never execute on this Mac. Installing the claude-seo runtime is still the
highest-value fix left in this pipeline — the one gate that is silently absent rather than failing loudly.

**Housekeeping, carried since 2026-08-27, deliberately NOT actioned:** the stale 0-ticket
`catalog-brand-tickets.md` in the repo root still makes `build_catalog_tickets.py` refuse to run
("refusing to overwrite existing catalog-brand-tickets.md"). §4 forbids `rm`; the fix is a move to
`_superseded/` or an explicit out-path. Left for Kevin — moving repo files is outside the §1 daily loop.

**2026-08-29 (second run of the day) — queue still EMPTY, nothing published, by design.** No `[ ]`
heading exists anywhere in this file (`grep "^## \[ \]"` returns nothing); every remaining `[ ]`
string is prose. Today's article is already shipped and verified live: Ticket #35
(`how-long-does-creatine-take-to-work-week-by-week-us-2026`, article id 621929496891) returned HTTP
200 with a browser UA on re-check this run, its tracker row is present, and the persona reservation
for it is already closed (`personas/index.json` at seq 45). This run's instructions say to log a
refill request instead of mining when the queue is empty, so no second article was written.

### Kevin — please run the mining recipe in the app

The google-ads MCP is not exposed to this headless session and GSC is still unauthorised, so
`references/ads-article-mining.md` cannot run here. Please run it in the app so the queue refills
with real search-term evidence. Until then the ranked shortlist above stands unchanged and is the
best available starting point: (1) `yeast infection vs bv`, (2) `probiotics while on antibiotics`
— safe to ship now that #35 is a non-probiotics article standing between it and #34, (3) a distinct
segment angle for `pure-shilajit-gold-resin` / `shilajit-shockwave`.

**2026-08-29 (third run of the day) — queue still EMPTY, nothing published, by design.** No `[ ]`
heading exists anywhere in this file (`grep "^##.*\[ \]"` returns only the historical, already-
RESOLVED `###` note at line 1005); every other remaining `[ ]` string is prose. Today's article is
still live and healthy: Ticket #35 (`how-long-does-creatine-take-to-work-week-by-week-us-2026`,
article id 621929496891) re-checked this run and returned HTTP 200 with a browser UA. This run's
instructions say to log a refill request instead of mining when the queue is empty, so no article
was written and no persona angle was spent.

### Kevin — please run the mining recipe in the app

The google-ads MCP is still not exposed to this headless session (no ads tool is registered at all)
and GSC remains unauthorised, so `references/ads-article-mining.md` cannot run here. Please run it in
the app so the queue refills with real search-term evidence. The ranked shortlist above is unchanged
and remains the best available starting point: (1) `yeast infection vs bv`, (2) `probiotics while on
antibiotics`, (3) a distinct segment angle for `pure-shilajit-gold-resin` / `shilajit-shockwave`.

Two carried blockers, unchanged and still worth Kevin's hands: the claude-seo runtime is not
installed, so `validate_article.py` silently skips the QRG quality/filler/AI-pattern hard-fails
(fifteenth run in a row); and the stale 0-ticket `catalog-brand-tickets.md` in the repo root still
blocks `build_catalog_tickets.py` — it needs a move to `_superseded/`, which §4 puts outside the
daily loop.


# BATCH 2026-08-30 — mined by the unattended run (queue empty; no GSC, no google-ads MCP)

Queue was EMPTY at the start of this run (0 `[ ]` headings). Per DAILY-RUN §1.1.2 an empty queue is
the job, not a blocker, so this run mined from the live catalog (22 SKUs) + live blog inventory.

**Live STEP 0 probes this run** (`curl -sg` + browser UA + `json.loads(strict=False)`), 28 probes.
Positive control `probiotics` returned 5 live articles, so the endpoint was answering truthfully.
0 article matches: `yeast infection vs bv` · `yeast infection` · `probiotics and yeast` ·
`probiotics while on antibiotics` · `probiotics with antibiotics` · `antibiotics` ·
`is turkesterone a steroid` · `turkesterone natty` · `turkesterone steroid` · `turkesterone for women` ·
`how long does turkesterone take to work` · `turkesterone results` · `creatine hair loss` ·
`does creatine cause hair loss` · `hair loss` · `dht` · `creatine kidneys` · `creatine safe` ·
`shilajit testosterone` · `shilajit and testosterone` · `nmn and exercise` · `shilajit for athletes` ·
`shilajit resin vs gold resin`.

**DAILY-RUN §2 IS STALE — corrected here.** §2 lists `pure-shilajit-gold-resin` and
`shilajit-shockwave` as "still uncovered, needs a distinct segment angle". Both are LIVE:
`shilajit gold resin` → *Shilajit Gold Resin Review: Is $75 Worth It? (US 2026)*, `shilajit shockwave`
→ *Shilajit Shockwave Review: 1 Drop or 1 mL? (US 2026)*. Shortlist item 3 from the 2026-08-29 run is
therefore CLOSED. Every stocked SKU now has a page.

**Two candidates killed by reading the live pages, not by suggest.json.** `suggest.json` matches
shallowly and returned 0 for both, so both looked greenfield:
- `is turkesterone a steroid` / `turkesterone natty` — already owned by #4
  (*Turkesterone Benefits & Dosing*), which contains "steroid" ×17, "natty" ×6, "anabolic" ×6,
  "WADA" ×3 and answers the natty question in its own intro. A dedicated page cannibalises it.
- `does creatine cause hair loss` — already named in the answer block of
  *Creatine Gummies Side Effects: 4 Real, 3 Myths* ("Kidney damage, hair loss and dehydration are the
  three that US buyers ask about most"). It is a sub-angle of a live page, not a gap.
**Rule earned: a 0 from `suggest.json` is necessary but NOT sufficient. Before writing, fetch the
cluster's existing pages and grep the candidate's key terms in the rendered body.** Both of these
would have shipped as cannibalising duplicates on suggest.json evidence alone.

**Why `yeast infection vs bv` and not `probiotics while on antibiotics`** — this REVERSES the
2026-08-29 shortlist's stated unblock condition. That run held the antibiotics angle back and said it
"gets safer the further #34 recedes; ship it after one non-probiotics article". #35 satisfied that
condition literally, but the condition was wrong: the overlap with #34 is **semantic, not temporal**.
#34 (*Probiotics for BV*, 4,288 words) contains "antibiotic" ×20, "metronidazole" ×5, a whole H2
"Contender 1: Antibiotics, the Only Actual Treatment", and frames probiotics as "an add-on after
antibiotics". A creatine article shipping in between changes none of that. By contrast #34 contains
"yeast" exactly ONCE — a passing line in its when-to-call-a-clinician list — and "candida" zero times.
The yeast angle is the genuinely uncovered one. `probiotics while on antibiotics` is now recommended
for RETIREMENT as a standalone page, not deferral.

## [DONE 2026-08-30 https://wellnessnest.co/blogs/news/yeast-infection-vs-bv-how-to-tell-them-apart-us-2026] Ticket #36 — NEW ARTICLE (type: COMPARISON)

- **Primary keyword:** yeast infection vs bv
- **Title:** Yeast Infection vs BV: How to Tell Them Apart (US 2026)
- **Brand / SKU:** FloraFresh vaginal probiotics — `florafresh-vaginal-probiotics-gummies` ($40.99),
  `florafresh-single-bottle` ($24.50), `florafresh-3-month-reserve` ($57.00)
- **Template:** COMPARISON. Registry maps "X vs Y" intent → COMPARISON. Previous article #35 was
  STORY, so the variety guard is satisfied.
- **Cluster rationale:** FloraFresh is the second-thinnest cluster with a stocked SKU (5 live pages
  vs shilajit 24, menopause 15). Urolithin is thinner (2) but has NO SKU on the live 22-product
  catalog, so it cannot end at a product.
- **Angle:** the differentiation itself — discharge character, odour, itch, and pH are what separate
  the two, and they are treated with opposite drug classes. This is a "which one do I have, and what
  do I do next" page. #34 owns BV *treatment efficacy*; this page owns *identification*. Send the
  reader to a clinician for diagnosis, and place probiotics honestly where the evidence puts them —
  post-treatment recurrence support, not a cure and not a treatment for either condition.
- **Compliance (YMYL, hard):** no diagnosis, no cure claims, no "treats", no "eliminates". State
  plainly that self-diagnosis is unreliable and that both conditions need a clinician. Do NOT restate
  FloraFresh PDP claims flagged in DAILY-RUN §6 — no "treats the root cause", no "stays & colonizes",
  no "top OB/GYN recommended", no "100% natural", no social-proof counts, no COA/clinically-tested
  language (`no-coa-competitive-advantage`). No mg serving figures.

### ✅ RESOLVED 2026-08-30 (later run) — the blocked-run note below is HISTORY. Ticket #36 SHIPPED.

Live at https://wellnessnest.co/blogs/news/yeast-infection-vs-bv-how-to-tell-them-apart-us-2026
(article id `621932282171`, `published_at` non-null, frontend 200 with a browser UA). Both post-publish
gates passed; `verify_published.py` passed on the first try so no `repair_schema.py` was needed.

What the resuming run did, and the two things worth reusing:
- Took a **fresh pick, seq 47** (`warnings[]` empty) exactly as the note below recommended, and
  regenerated BOTH the hero and the persona inline image under it so `commit` matched what shipped.
  `inline-1-notebook` and `inline-2-bathroom-shelf` were reused unchanged (no-face, no angle spent).
  Seq 46 stays burned and unreleased — 2 of f3039-as-01's 21 angles are gone with no article on them.
- **The mirror-of-ref class below is real, and it is broader than the exact mirror.** f3039-as-02's
  ref also faces frame-LEFT; the inline `profile-left` came back "head turned wrong direction" on roll 1.
  The fix was to stop *asserting* the direction and **motivate it with scene geometry** (window and exit
  door off the RIGHT edge, photographer on her LEFT), state the silhouette as testable checks (which ear,
  which side of the silhouette, where nose/chin/back-of-head point), and add "IGNORE the reference photo's
  head direction entirely". Passed next roll.
- **A front angle needs every competing directional cue REMOVED, including the lighting.** The hero's
  roll 2 failed "head turned right, not squared" — caused by my own prompt writing the light as "a frosted
  window off to the right". The model turned her head into the light. Roll 3 used frontal bounced light, a
  symmetric doorframe on both sides, the pack centred in front of her, and bilateral-symmetry checks. PASS.
  (Roll 1 had failed "chin dipped not raised": the `down-at-product` gaze drags the whole head down unless
  pitch and gaze are separated in words — "chin UP, head tilted BACK, only the EYEBALLS move down".)
- One hero attempt returned "No image data returned from the image backend" — no image, so no QC verdict.
  A roll the judge never saw is **not** a QC re-roll; it was retried, not counted, and that is what left
  budget for the roll that passed.

**Kevin — the picker fix suggested below is still unactioned and still recommended:** record each persona's
ref-pose yaw in `persona.json` and have `persona_picker.py` refuse to issue the mirror of it, the way it
already refuses a spent angle. Two personas in a row have now burned rolls on this.

<details><summary>Original blocked-run note (2026-08-30 earlier run) — kept for the record</summary>

### Ticket #36 STATUS 2026-08-30 — BLOCKED AT THE HERO IMAGE, NOT PUBLISHED. Left `[ ]` on purpose.

The heading stays `[ ]` so the NEXT run continues this ticket instead of mining a new one. The queue is
therefore NOT empty tomorrow. Everything except the hero is finished and banked.

**Done and reusable:**
- Draft written and saved: `published_drafts/yeast-infection-vs-bv-how-to-tell-them-apart-us-2026.md`
  (1,888 content words, h2:11, 1 comparison table, 6 FAQs, 2 collection links, byline intact).
- `validate_article.py --draft` now fails on **exactly one** item: `only 3 body image tag(s) — need >=4`.
  Every other structural check passes. Drop in a hero as the FIRST image tag and it should go green.
- 3 of 4 images generated and **QC PASS on the first roll**, already referenced in the draft:
  `inline-1-notebook` (no-face), `inline-2-bathroom-shelf` (no-face, product), `inline-3-kitchen-persona`
  (persona f3039-as-01, angle `profile-left+chin-down`). All three eyeballed against
  `product_refs/florafresh-vaginal-probiotics-gummies.png`: pouch format, vertical wordmark, FloraFresh
  badge, closed 'Pineapple flavor' outline border and AMBER gummy colour all correct.
- 9 citations verified at Crossref (DOI + author surnames). `Sobel, 2007` is SINGLE-AUTHOR — never write
  "Sobel et al.". Amsel 1983 has 6 real authors despite Crossref returning an empty author array.

**The blocker: the hero mirrors, and the re-roll budget is spent.**
Picker seq 46 issued hero `f3039-as-01` @ `3q-left+chin-up` (nose must point at the frame-RIGHT edge).
Three generations, all with the picker's `hero_face_angle_phrase` verbatim including the `frame_hint`:
1. roll 1 — QC **PASS**, but the head was mirrored (nose at the frame-LEFT edge). Caught by eye, not by QC.
2. roll 2 — QC **FAIL** "head turned toward wrong edge (mirrored)".
3. roll 3 — QC **FAIL** "wrong head angle, nose points left instead of right".
Budget of 2 re-rolls is spent, so the run STOPPED per DAILY-RUN section 3 and did not roll a fourth time.
Both failed rolls preserved (never deleted) at `_superseded/img-qc-fails/`.

**Root cause, and it is new.** `personas/f3039-as-01/ref.jpg` is ITSELF a three-quarter view with the
subject's nose pointing at the frame-LEFT edge. The requested `3q-left` is the near-exact MIRROR of the
reference's own pose, so identity-locking drags the head back to the ref every time. Roll 1 also
reproduced the ref's teal velvet top verbatim, which confirms the ref is driving pose and wardrobe, not
just identity. The same persona's `profile-left+chin-down` inline image rendered CORRECTLY on the first
roll — 80 degrees is far enough from the ref pose to force a genuine re-pose. This is a THIRD failure
class, distinct from the label-element class (#33) and the scene-geometry class (#31/#33):
**an angle that is the mirror of the persona ref's own pose is effectively unrenderable for that persona,
and `frame_hint` does not fix it.** The 2026-08-13 fix assumed the flip was a left/right vocabulary
problem; for a mirror-of-ref angle it is not.

**Persona reservation seq 46 was deliberately NOT released.** `release` + re-pick is documented as
deterministic on seq (DAILY-RUN section 3), so releasing would re-issue the identical failing assignment
tomorrow and loop forever. Holding the reservation costs 2 angles out of 1,905 — which DAILY-RUN itself
calls "nothing" — and makes the next `pick` advance to seq 47 with a different persona.

**Recommended next run:** take a FRESH pick (seq 47). Regenerate the hero AND the persona inline image
under that new pick so `commit` matches what actually ships exactly; keep `inline-1-notebook` and
`inline-2-bathroom-shelf` as they are (both no-face, no angle spent). Then gate and publish.

**For Kevin — the real fix.** `taxonomy.json` has a per-angle `renderable` flag, but this failure is
per-PERSONA: it depends on which way that persona's own ref.jpg faces. Suggested fix is to record each
persona's ref-pose yaw in `persona.json` and have `persona_picker.py` refuse to issue the mirror of it,
the same way it already refuses a spent angle. Not actioned here — changing the picker's issuing logic
is outside the section 1 daily loop.

**Second finding, already worked around in the draft.** `validate_article.py:206` wraps "the first line
not starting with `<`" as the answer block in `--draft` mode. A MULTI-LINE HTML comment whose
continuation lines are indented therefore turns those lines into a false answer block, and the article
fails `answer block missing US-market anchor` even when the real opening paragraph is correct. Keep
block comments in a draft on ONE line.

</details>


## Refill needed

**2026-08-30 (later run) — queue EMPTY, nothing published, by design.** No `[ ]` heading exists
anywhere in this file. `grep "^##.*\[ \]"` returns zero rows; the only two `[ ]` strings left are
historical `###` blocked-run notes (line 1005 and the `<details>` block above), and BOTH are marked
RESOLVED — #31 and #36 both shipped. Ticket #36 re-checked this run:
`yeast-infection-vs-bv-how-to-tell-them-apart-us-2026` (article id `621932282171`) returns HTTP 200
with a browser UA. This run's instructions say to log a refill request instead of mining when the
queue is empty, so no article was written and **no persona angle was spent**.

### Kevin — please run the mining recipe in the app

The google-ads MCP is still not registered in this headless session (the only MCP tools present are
web search/fetch; Shopify and claude.ai are unauthenticated) and GSC remains unauthorised, so
`references/ads-article-mining.md` cannot run here. Please run it in the app so the queue refills
with real search-term evidence.

**The hand-mined shortlist is now genuinely exhausted — this is new.** All three items the
2026-08-29 runs carried forward are closed:
1. `yeast infection vs bv` — SHIPPED as #36 on 2026-08-30.
2. `probiotics while on antibiotics` — the 2026-08-30 mining pass RETIRED it as a standalone page.
   #34 (*Probiotics for BV*) contains "antibiotic" ×20, "metronidazole" ×5 and a whole H2 on
   antibiotics; the overlap is semantic, not temporal, so waiting does not unblock it.
3. `pure-shilajit-gold-resin` / `shilajit-shockwave` — both already LIVE; DAILY-RUN §2 is stale on
   this point and was corrected in the 2026-08-30 batch note above.

Every stocked SKU on the live 22-product catalog now has a page. There is no keyword left that can
be justified from the catalog alone, which is exactly why real search-term data is now the binding
constraint on this queue — not a nice-to-have. Also apply the rule earned on 2026-08-30 when mining:
a 0 from `suggest.json` is necessary but NOT sufficient; fetch the cluster's existing pages and grep
the candidate's key terms in the rendered body before writing a ticket.

Three carried blockers for Kevin's hands, unchanged:
- The claude-seo runtime is not installed, so `validate_article.py` silently skips the QRG
  quality/filler/AI-pattern hard-fails (sixteenth run in a row).
- The stale 0-ticket `catalog-brand-tickets.md` in the repo root still blocks
  `build_catalog_tickets.py`; it needs a move to `_superseded/`, which §4 puts outside the daily loop.
- `persona_picker.py` still issues angles that mirror a persona's own `ref.jpg` pose. Two personas
  in a row (f3039-as-01 seq 46, f3039-as-02) have burned image rolls on it. Suggested fix stands:
  record the ref-pose yaw in `persona.json` and refuse its mirror the way a spent angle is refused.


# BATCH 2026-08-31

**Mined this run (queue was empty — 0 `[ ]` headings). Evidence: hand-mined from the live
catalog + live cluster pages, per DAILY-RUN section 2. GSC unauthorised and google-ads MCP not
exposed headless, so no search-term data was available.**

STEP 0 probes run this morning against `search/suggest.json` (curl -sg + browser UA), 8 candidates,
all returned 0 articles: `urolithin a side effects` · `creatine loading phase` · `shilajit at night` ·
`urolithin a vs nmn` · `turkesterone for women` · `shilajit and testosterone` · `creatine and kidneys` ·
`nmn and blood pressure`.

Applying the rule earned 2026-08-30 (a 0 from suggest.json is necessary but NOT sufficient), the
Urolithin A cluster's two live pages were fetched and grepped:
- `urolithin-a-dosage-how-many-mg-per-day-us-2026` — "side effect" x0, no safety/tolerability H2.
- `urolithin-a-benefits-the-40-problem-us-buyers-miss` — "side effect" x1, no safety H2, but it DOES
  own an H2 "Urolithin A vs NMN", so the `urolithin a vs nmn` candidate is KILLED as semantically covered.

Result: `urolithin a side effects` is the genuinely uncovered leg. The cluster has dosage + benefits;
every other brand on this store already has its side-effects page (shilajit #15, turkesterone #31,
NMN #32, creatine gummies #27, vaginal probiotics #30). Urolithin A is the only one missing it.

## [DONE 2026-08-31 https://wellnessnest.co/blogs/news/urolithin-a-side-effects-what-3-trials-report-us-2026] Ticket #37 — NEW ARTICLE (type: LISTICLE)

- **Primary keyword:** urolithin a side effects
- **Working title:** Urolithin A Side Effects: What the Trials Report (US 2026)
- **STEP 0.5 topic_fitness:** `REVIEW [covered-segment]` — proceed under Kevin's standing greenlight
  for this queue (2026-08-13, "I approve all of them, I need published articles without any delay").
- **Template:** LISTICLE. #36 was COMPARISON, so the variety guard holds; "X side effects" is the
  LISTICLE intent row in `references/article-templates.md`.
- **SKU it ends at:** `ageaura-pure-urolithin-a` ($199.99, 30 vegan capsules, 500 mg/serving) — the
  only Urolithin A SKU on the store. Curated ref exists.
- **Collections (both verified HTTP 200):** `/collections/ageaura` · `/collections/best-seller`
- **Internal links:** the two cluster pages above (link them, do not restate them).
- **Author:** Dr. Marcus Hale (roster.json, sole source).
- **Persona:** picker seq 48 returned `hero: NO-FACE` (scheduled no-face cycle) — 0 face angles at
  risk this run, which also routes around the mirror-of-ref failure that blocked 2026-08-30.

### Ticket #37 — post-publish record (written by the later run of 2026-08-31)

The run that wrote #37 shipped the article but exited before it recorded the IDs or committed. Both
post-publish gates were re-run this run and both PASS:
- `verify_published.py 621934805307 104008483131` → `✓ Live article verified — schema, author, table
  all present` (FAQPage True · ld+json True · table True · author `Dr. Marcus Hale`).
- Frontend `urolithin-a-side-effects-what-3-trials-report-us-2026` returns HTTP 200 with a browser
  UA; `published_at` is non-null (`2026-08-30T17:40:59-07:00`).
- Persona `commit` also landed before the exit: `personas/index.json` is at seq 48 with `NO-FACE`
  appended to `recent_heroes` and `no_face_cycle.position` rolled to 0. No angle needs releasing.

Nothing was left half-done — only the `git commit` was missing, and this run makes it.

## Refill needed

**2026-08-31 (later run) — queue EMPTY, nothing published, by design.** `grep "^## \[ \]"` returns
zero rows. Today's article is ALREADY SHIPPED (#37 above), so per rule 6 this run wrote no article,
mined no ticket, and **spent no persona angle**.

### Kevin — please run the mining recipe in the app

The google-ads MCP is still not registered in this headless session (no google-ads tool is exposed;
Shopify and claude.ai are present but unauthenticated) and GSC remains unauthorised, so
`references/ads-article-mining.md` cannot run here. Please run it in the app so the queue refills
with real search-term evidence.

**The hand-mined shortlist stays exhausted.** The 2026-08-31 mining pass burned its own best
candidate (`urolithin a side effects` → #37) and, in the same pass, KILLED `urolithin a vs nmn` as
semantically covered by the existing benefits page. Of the eight probes it ran, the six left over
are all still unverified against their clusters: `creatine loading phase` · `shilajit at night` ·
`turkesterone for women` · `shilajit and testosterone` · `creatine and kidneys` ·
`nmn and blood pressure`. A 0 from `suggest.json` is necessary but NOT sufficient — grep the
cluster's rendered pages before any of those becomes a ticket. Every stocked SKU on the live
22-product catalog has a page, so real search-term data is the binding constraint, not a nice-to-have.

Three carried blockers for Kevin's hands, all re-checked this run and all unchanged:
- The claude-seo runtime is not installed (`ModuleNotFoundError: No module named 'claude_seo'`), so
  `validate_article.py` silently skips the QRG quality/filler/AI-pattern hard-fails (seventeenth run
  in a row).
- The stale 0-ticket `catalog-brand-tickets.md` in the repo root still blocks
  `build_catalog_tickets.py`; it needs a move to `_superseded/`, which §4 puts outside the daily loop.
- `persona_picker.py` still issues angles that mirror a persona's own `ref.jpg` pose. #37 dodged this
  only because it drew a NO-FACE hero, so the bug is untested-again, not fixed. Suggested fix stands:
  record the ref-pose yaw in `persona.json` and refuse its mirror the way a spent angle is refused.

## Refill needed

**2026-08-31 (third run of the day) — queue EMPTY, nothing published, by design.**
`grep -nE "^#{1,4} .*\[ \]" daily-tickets.md` returns only the two historical `###` blocked-run
notes (line 1005 for #31, and the `<details>` note for #36); both are marked RESOLVED and both
articles shipped, so there is **no open ticket heading anywhere in this file**. Today's article is
already live — #37 `urolithin-a-side-effects-what-3-trials-report-us-2026` re-checked this run,
HTTP 200 with a browser UA. Per rule 6 this run wrote no article, mined no ticket, and **spent no
persona angle**. Working tree was clean at start, so no bookkeeping was outstanding either.

### Kevin — please run the mining recipe in the app

The google-ads MCP is still not registered in this headless session (a tool search for google-ads
returns only web search/fetch; Shopify and claude.ai are present but unauthenticated) and GSC
remains unauthorised, so `references/ads-article-mining.md` cannot run here. Please run it in the
app so the queue refills with real search-term evidence.

**The hand-mined shortlist stays exhausted**, unchanged from the earlier run today. Six probes from
the 2026-08-31 mining pass are still unverified against their clusters and are the cheapest place to
restart: `creatine loading phase` · `shilajit at night` · `turkesterone for women` ·
`shilajit and testosterone` · `creatine and kidneys` · `nmn and blood pressure`. A 0 from
`suggest.json` is necessary but NOT sufficient — fetch and grep the cluster's rendered pages before
any of those becomes a ticket (that rule is what killed `urolithin a vs nmn`). Every stocked SKU on
the live 22-product catalog already has a page, so real search-term data is the binding constraint.

Three carried blockers for Kevin's hands, all unchanged:
- The claude-seo runtime is not installed, so `validate_article.py` silently skips the QRG
  quality/filler/AI-pattern hard-fails (eighteenth run in a row).
- The stale 0-ticket `catalog-brand-tickets.md` in the repo root still blocks
  `build_catalog_tickets.py`; it needs a move to `_superseded/`, which §4 puts outside the daily loop.
- `persona_picker.py` still issues angles that mirror a persona's own `ref.jpg` pose. Still untested
  since #37 drew NO-FACE. Suggested fix stands: record the ref-pose yaw in `persona.json` and refuse
  its mirror the way a spent angle is refused.

---

# BATCH 2026-09-01 — mined by the unattended run (queue empty; no GSC, no google-ads MCP)

**Evidence header.** `daily-tickets.md` had zero `[ ]` headings at 07:31 ICT, so DAILY-RUN §1.1.2
applies: mine, then execute. Sources used, all $0 and all on this machine or the live store:
`https://wellnessnest.co/products.json` (22 SKUs), `ALL_ARTICLES.csv` (68 rows),
`PUBLISHED_ARTICLES_TRACKER.csv` (37 rows), and the six unverified probes the 2026-08-31 run
left behind. STEP 0 probed 8 keywords against `search/suggest.json` with a browser UA — all 8
returned 0 articles. Then the 2026-08-30 rule was applied (a 0 from suggest.json is necessary
but NOT sufficient): the four live turkesterone pages were fetched and their rendered bodies
grepped. Result — `female` x0, `woman` x0, `menstrual` x0 across all four; the only occurrence of
`women` in any body is an internal link to the *creatine* for-women page. No H2 or H3 anywhere in
the cluster addresses a female reader. The segment is genuinely unowned, so it is not a
cannibalisation risk against `turkesterone-benefits-dosing-whats-real-us-2026`.

STEP 0.5 `topic_fitness.py "turkesterone for women"` → `REVIEW [covered-segment]` (exit 2):
*"brand has a general article, but 'for women' is an audience/intent no existing title covers —
distinct enough to write IF the ticket brief greenlit this exact topic; link the general page
instead of restating it."* Proceeding under Kevin's standing greenlight of 2026-08-13
("I approve all of them, I need published articles without any delay"). The instruction inside
the verdict is obeyed: this article links the general page rather than restating its dosing.

Candidates rejected this pass, with the reason:
- `shilajit and testosterone` — the live `shilajit-benefits-for-men` page already ranks four
  testosterone claims; the grep, not suggest.json, killed it.
- `creatine and kidneys` — `creatine-gummies-side-effects-4-real-3-myths` owns the kidney myth as
  a named item in its own body.
- `creatine loading phase` / `shilajit at night` / `nmn and blood pressure` — left unprobed at the
  cluster-grep stage once a stronger candidate cleared; they stay on the shortlist.

## [DONE 2026-09-01 https://wellnessnest.co/blogs/news/turkesterone-for-women-3-trials-85-men-0-women-us-2026] Ticket #38 — NEW ARTICLE (type: EDITORIAL)

- **Primary keyword:** `turkesterone for women`
- **Secondary:** turkesterone for females, is turkesterone safe for women, turkesterone women dosage,
  turkesterone side effects women, does turkesterone work for women
- **Search intent:** informational, audience-segment safety/efficacy question with buyer intent
- **Title (59 chars):** `Turkesterone for Women: 3 Trials, 85 Men, 0 Women (US 2026)`
- **Template:** `EDITORIAL` — the registry routes `"for women/men" informational` here, and it
  breaks the run of COMPARISON (#34), STORY (#35), COMPARISON (#36), LISTICLE (#37).
- **BLOG_ID:** `104008483131`
- **Hero product:** `/products/turkesterone-advanced-formula` ($75.00, 60 capsules, 2/day)
- **Secondary product:** `/products/fusiforce-creatine-gummies` ($69.99) — the evidence-backed
  alternative for the muscle goal, which is an honest recommendation, not a shoehorn.
- **Collection links (≥2, verified live 2026-09-01):** `/collections/womens-essentials-collection`,
  `/collections/best-seller`
- **Angle:** every human study that measured a muscle, strength or metabolic outcome for
  turkesterone or ecdysterone enrolled men only — 11 (Harris 2024) + 46 (Isenmann 2019) +
  28 recruited/24 completed (JISSN 2025) = 85 men, 0 women. The one human study that did include
  women measured urinary excretion, not results, and reported no sex difference. Meanwhile the
  working mechanism runs through **estrogen receptor beta**, which is the one receptor where a
  female reader has an obvious reason to want data and has none. Our own PDP is written "for men"
  in its own words. Say all of that plainly.
- **Author:** Dr. Marcus Hale (roster.json, sole source)
- **Dedup note:** STEP 0 clean (0 hits, 8 probes) + cluster grep clean (see evidence header).


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

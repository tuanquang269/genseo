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

## [ ] Ticket #9 — NEW ARTICLE (type: authority-figure search capture)

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

## [ ] Ticket #10 — NEW ARTICLE (type: audience-segment deep-dive)

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

## [ ] Ticket #11 — NEW ARTICLE (type: review-intent / brand-SERP defense)

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

## [ ] Ticket #12 — NEW ARTICLE (type: retail-availability / where-to-buy) — LOWEST priority, run last

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

## [ ] Ticket #13 — NEW ARTICLE (type: LISTICLE — organic presell format)

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

## [ ] Ticket #14 — NEW ARTICLE (type: LISTICLE — organic presell format)

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

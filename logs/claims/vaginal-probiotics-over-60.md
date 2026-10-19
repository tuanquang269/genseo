# CA1016-7 — vaginal probiotics over 60

Checked 2026-10-19. Source review by automated pipeline; no claim of independent human medical review. 15 factual claim entries below. All retained claims fetched and confirmed. Advice/checklist language is editorial, not a claimed treatment protocol.

Claim | Source URL | fetched+confirmed Y/N
--- | --- | ---
Menopause-associated estrogen decline is linked to reduced vaginal Lactobacillus abundance and higher pH | https://pmc.ncbi.nlm.nih.gov/articles/PMC10047399/ | Y — fetched review, section on vaginal microbiome
Menopause, certain medicines and other conditions can cause vaginal dryness | https://www.nhs.uk/conditions/vaginal-dryness/ | Y — fetched guidance
Persistent dryness despite self-care, dryness affecting daily life, unusual discharge, or bleeding after sex/menopause warrant medical advice | https://www.nhs.uk/conditions/vaginal-dryness/ | Y — fetched referral criteria
Petricevic study randomized 72 postmenopausal participants | https://pubmed.ncbi.nlm.nih.gov/18701205/ ; https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:18701205%20AND%20SRC:MED&format=json&resultType=core | Y — primary abstract fetched through Europe PMC API; PubMed web fetch cookie wall
Trial used oral L. rhamnosus GR-1 and L. reuteri RC-14 versus placebo for 14 days | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:18701205%20AND%20SRC:MED&format=json&resultType=core | Y — primary abstract
Primary trial outcome was Nugent-score change of at least two grades; improvement was more frequent in intervention group | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:18701205%20AND%20SRC:MED&format=json&resultType=core | Y — primary abstract; not represented as symptom or FloraFresh efficacy
Retrieved abstract omits participant ages and separate over-60 results | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:18701205%20AND%20SRC:MED&format=json&resultType=core | Y — abstract inspected; snippet-only age range 55–65 excluded
FloraFresh Supplement Facts serving size is 2 gummies | https://cdn.shopify.com/s/files/1/0810/1563/6283/files/FloraFresh_Supplement_Fact.webp | Y — downloaded actual embedded PDP panel and visually read
FloraFresh lists spore-based Bacillus coagulans SNZ-1969 at 1 billion CFU per serving | https://cdn.shopify.com/s/files/1/0810/1563/6283/files/FloraFresh_Supplement_Fact.webp | Y — visually confirmed; not the Lactobacillus trial formula
Panel lists vitamin C and pineapple fruit powder with bromelain | https://cdn.shopify.com/s/files/1/0810/1563/6283/files/FloraFresh_Supplement_Fact.webp | Y — visually confirmed; amounts not repeated in draft
Panel other ingredients include maltitol and isomalt | https://cdn.shopify.com/s/files/1/0810/1563/6283/files/FloraFresh_Supplement_Fact.webp | Y — visually confirmed; no sugar-free claim made
CFU means colony-forming units | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:18701205%20AND%20SRC:MED&format=json&resultType=core | Y — spelled out in primary abstract
Probiotic harmful-effect risk is greater with severe illness or compromised immunity | https://www.nccih.nih.gov/health/probiotics-usefulness-and-safety | Y — fetched by research agent; no invented medication-specific interaction
FloraFresh listed at $40.99 and available at check | https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies.js | Y — fetched JSON price 4099, available true; price described as observed, not permanent
FloraFresh is an oral gummy rather than an intravaginal preparation | https://cdn.shopify.com/s/files/1/0810/1563/6283/files/FloraFresh_Supplement_Fact.webp ; https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies | Y — gummy dietary supplement identity and serving panel; no invented dosing frequency

## Research and execution notes
- Search gap: general older-women product roundups do not establish over-60-specific FloraFresh efficacy. Covered trial population, strain mismatch, medication-review questions, practical routine, symptom referral.
- Question variants: probiotics after menopause; vaginal probiotics for older women; trial enrollment over 60; medication review; when symptoms need assessment. No claim that actual PAA boxes/rank positions were observed.
- Product handle sourced through live suggest.json; product, collections, related articles and author returned HTTP 200 with browser User-Agent.
- Older linked articles and PDP formula descriptions conflict with current label. Draft explicitly tells readers to use current Supplement Facts; no old formula copied.
- Palette: shared template blocks recolored to dusty-rose packaging per AEO/GEO §6.5.
- template:LISTICLE; persona: none (failover no-face). No persona picker or persona-state edits.
- Images: hero + three inline, all QC PASS first attempt; product images visually compared with curated pouch. Scenes: bedroom-chest/kitchen-breakfast-table/home-writing-desk/reading-chair.
- ima2 $0 subscription (standing approval).
- 90-day refresh review: 2027-01-17. Review new age-specific research and label accuracy; do not change live article automatically.

## Publish verification
- Article ID 634944553275; frontend https://wellnessnest.co/blogs/news/vaginal-probiotics-over-60-5-checks-in-the-us
- Pre-publish daily count 0; exact-keyword suggest.json empty immediately before publish.
- validate_article.py: exit 0, ✓ PASS; 1554 content words. GEO lint: zero warnings. QRG unavailable (runtime not installed), not reported as scored.
- Publisher --live uploaded four images; CDN gate PASS 4/4.
- Initial verify failed named-Person author schema; repair_schema.py applied only to this newly created article, then verify_published.py PASS.
- published_at 2026-10-18T19:09:33-07:00 (2026-10-19 UTC); frontend browser User-Agent HTTP 200.
- All four image URLs returned HTTP 200, image content types and nonempty image bytes; all appeared in frontend HTML. Rendered inline body 3/3 plus hero verified via approved HTML fallback (browser pane unavailable).
- Shop-this-article section present; data-liquid-handles includes florafresh-vaginal-probiotics-gummies.
- IndexNow skipped by publisher: no key configured.
- Unrelated concurrent scripts/article_images.py change excluded from this article commit.

# CA1016-6 — NMN for fertility claim check

Checked 2026-10-18. Source pages fetched by the research agent; human abstract additionally fetched in the main run. Y means the cited source supports the narrowly worded claim, not independent clinical validation. No human reviewer is claimed. No ingredient dose is stated. Search tools returned no SERP result blocks, so no top-three ranking or People Also Ask claims are made.

Claim | Source URL | fetched+confirmed Y/N
--- | --- | ---
The human conference abstract describes 50 women with diminished ovarian reserve, with 25 per comparison group. | https://academic.oup.com/humrep/article/40/Supplement_1/deaf097.217/8171099 | Y
The abstract describes a retrospective design but also uses randomization language without a clear allocation method; it cannot confidently be called an RCT. | https://academic.oup.com/humrep/article/40/Supplement_1/deaf097.217/8171099 | Y
The abstract reports 12 pregnancies among 25 NMN participants versus 6 among 25 controls, without reported live-birth counts. | https://academic.oup.com/humrep/article/40/Supplement_1/deaf097.217/8171099 | Y
The abstract reports follicular and endometrial measurements, not proof that NMN caused a pregnancy difference. | https://academic.oup.com/humrep/article/40/Supplement_1/deaf097.217/8171099 | Y
The human conference abstract does not specify a sufficiently clear NMN regimen for a fertility dosing recommendation. | https://academic.oup.com/humrep/article/40/Supplement_1/deaf097.217/8171099 | Y
Bertoldo 2020 studied reproductive aging in mice, not human supplementation. | https://pmc.ncbi.nlm.nih.gov/articles/PMC7063679/ | Y
Bertoldo 2020 reports improvements in some oocyte and reproductive outcomes in aged female mice. | https://pmc.ncbi.nlm.nih.gov/articles/PMC7063679/ | Y
Separate Bertoldo experiments added NMN directly to embryo culture medium. | https://pmc.ncbi.nlm.nih.gov/articles/PMC7063679/ | Y
Bertoldo results do not support a simple higher-amount-is-better reproductive rule. | https://pmc.ncbi.nlm.nih.gov/articles/PMC7063679/ | Y
The 2025 systematic review identified seven preclinical intervention studies and called for standardized protocols and clinical trials. | https://pmc.ncbi.nlm.nih.gov/articles/PMC12831783/ | Y
The review's human-oocyte component was gene-expression analysis, not demonstration of oral NMN fertility benefit. | https://pmc.ncbi.nlm.nih.gov/articles/PMC12831783/ | Y
The reviewed sources do not establish a completed human randomized trial showing NMN fertility benefit; this is scoped to reviewed sources, not universal nonexistence. | https://pmc.ncbi.nlm.nih.gov/articles/PMC12831783/ ; https://academic.oup.com/humrep/article/40/Supplement_1/deaf097.217/8171099 | Y
An obese male-mouse experiment reported improved spermatogenesis-related outcomes; no extrapolation to men is made. | https://pmc.ncbi.nlm.nih.gov/articles/PMC12700873/ | Y
A maternal-obesity/male-offspring mouse study reported adverse sperm-related findings under its NMN treatment conditions. | https://pmc.ncbi.nlm.nih.gov/articles/PMC6589912/ | Y
FDA's women's supplement page advises discussing supplements and prenatal vitamins with a healthcare provider; it is not an NMN-specific endorsement or warning. | https://www.fda.gov/consumers/womens-health-topics/dietary-supplements-tips-women | Y
AgeAura Pure NMN + TMG NAD+ Complex live product JSON lists price 6995 cents ($69.95); curated pack identifies NMN + TMG NAD + Complex and vegan capsules. No fertility claim or ingredient amount inferred. | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.js ; product_refs/ageaura-pure-nmn-tmg-nad-complex.png | Y

## Non-clinical verification

- Live product URL, best-seller collection, three ticket-named related articles: HTTP 200 with browser User-Agent.
- Best-seller is linked only for general browsing; no AgeAura membership claim.
- Byline and fixed bio copied from roster.json; no extra credentials or reviewer added.
- Four no-face images: QC PASS; packaging visually compared with curated bottle. One appointment image re-roll after QC demanded a packaging reference.
- Template EDITORIAL. persona: none (failover no-face). ima2 $0 subscription (standing approval).
- validate_article.py: exit 0, ✓ PASS, 1532 content words. QRG unavailable (claude-seo runtime not installed). geo_official_lint: 0 warnings.
- Published LIVE article 634940719419. Final guard: daily count 4; suggest.json empty. Publisher uploaded 4 images, CDN gate PASS.
- Initial verify failed generic Organization author. repair_schema.py repaired this run's article; re-verification PASS, named Person author and FAQ schema.
- published_at: 2026-10-17T21:49:39-07:00 (Shopify Pacific timestamp; local run date 2026-10-18). Frontend HTTP 200 with Mozilla/5.0; 4/4 CDN image URLs returned image bytes; rendered inline images 3/3; Shop-This-Article widget contains the clean AgeAura handle. Browser pane unavailable; approved HTTP/HTML fallback used.
- Publisher transforms the local markdown in place (strips H1, metadata and promoted hero; rewrites inline paths to CDN). The committed file is its post-publish artifact, not a republish-ready source. No existing article was modified.
- Search/SERP tools returned no results; top-three competitor review and People Also Ask extraction unavailable. Evidence research used directly fetched source papers instead.
- Refresh review due 2027-01-16; no scheduled task created. IndexNow skipped: no configured key.

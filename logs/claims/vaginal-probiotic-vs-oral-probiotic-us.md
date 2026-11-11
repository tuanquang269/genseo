# MB1110-2 claim audit — 2026-11-11

Automated source review; not represented as human clinical review. Repeated claims grouped. 12 retained factual claims confirmed. Advice is framed as advice, not trial evidence.

Claim | Source URL | fetched+confirmed Y/N
--- | --- | ---
FloraFresh is sold as a gummy supplement marketed for vaginal wellness | https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies.js | Y — product JSON and curated pack read
FloraFresh price is $40.99 at this check | https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies.js | Y — price 4099
FloraFresh is available at this check | https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies.js | Y — available true
FloraFresh ingredient image identifies SNZ-1969 Bacillus coagulans | https://cdn.shopify.com/s/files/1/0810/1563/6283/files/7_babef3ee-e845-4aba-83d7-a8b25b714ec0.png?v=1793094703 | Y — downloaded and visually read; consistent with approved formula record
FloraFresh ingredient image identifies Vitamin C | https://cdn.shopify.com/s/files/1/0810/1563/6283/files/7_babef3ee-e845-4aba-83d7-a8b25b714ec0.png?v=1793094703 | Y
FloraFresh ingredient image identifies pineapple fruit powder with bromelain | https://cdn.shopify.com/s/files/1/0810/1563/6283/files/7_babef3ee-e845-4aba-83d7-a8b25b714ec0.png?v=1793094703 | Y
Live descriptive copy conflicts with approved Supplement Facts record | https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies.js | Y — compared with docs/FLORAFRESH_FORMULA_GUARD.md and scripts/florafresh_rules.py --brief; incorrect marketing claims not adopted
Effects of different probiotics cannot be assumed equivalent | https://www.nccih.nih.gov/health/probiotics-what-you-need-to-know | Y — fetched source summary
Probiotic harmful-effect concern is greater for serious illness or compromised immunity | https://www.nccih.nih.gov/health/probiotics-what-you-need-to-know | Y
CDC does not support probiotic products as adjunctive or replacement BV therapy | https://www.cdc.gov/std/treatment-guidelines/bv.htm | Y
CDC discusses vaginal L. crispatus CTV-05 Lactin-V after vaginal metronidazole with a recurrence finding | https://www.cdc.gov/std/treatment-guidelines/bv.htm | Y — no extrapolation to FloraFresh
CDC describes clinical/laboratory BV diagnosis and recommends treatment for symptomatic patients | https://www.cdc.gov/std/treatment-guidelines/bv.htm | Y

Removed: serving size, CFU amount, vitamin and pineapple quantities, sweetener statements. Approved local record has them, but this run did not retrieve a readable live Supplement Facts panel. The image named Fact.png is a testimonial collage, not the facts panel. No testimonial or disease-outcome claims retained.

Images: all four ima2 outputs QC PASS, visually checked against curated packaging. Illustrations, not evidence of product efficacy. No new face generated. Picker reservation 150 NO-FACE, warnings empty; committed after live publish.

## Publication outcome — verification blocked

LIVE article 635069989179: https://wellnessnest.co/blogs/news/vaginal-probiotic-vs-oral-probiotic-the-us-choice
Admin: https://admin.shopify.com/store/wellnessnest1/content/articles/635069989179
published_at: 2026-11-10T17:39:59-08:00. Browser-UA frontend HTTP 200. Hero plus three body images returned HTTP 200 with image bytes. Shopping widget present, handle florafresh-vaginal-probiotics-gummies. Frontend contains Person schema.

Draft validator PASS (2151 words), GEO lint zero warnings, CDN gate PASS. QRG scoring unavailable. verify_published.py FAIL: Article schema author is not a named Person. Repair_schema changed author field to approved roster author but did not resolve failure. Corrected byline to relative URL and updated ONLY this newly created article via publisher after another PASS; restored proper hero placement with --replace-cover. Verifier still fails because publisher lines 969–972 intentionally omit body Article schema in favor of theme Article schema (2026-10-20 design), while verifier requires a Person node inside body_html. No scripts, gate, or theme altered to bypass this conflict.

Ticket not marked DONE; tracker append withheld because skill forbids Step 9 until all gates pass. Do not create another copy: this article is already public. Next queued ticket after resolving this run: MB1110-3, nmn vs niacin. template:COMPARISON. persona: none (failover no-face). scene: breakfast-nook; hallway-console; living-room-ottoman; home-office-side-table. ima2 $0 subscription (standing approval). Refresh review due 2027-02-09, not scheduled.


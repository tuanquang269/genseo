# CA1016-9 — how to take nmn

Checked 2026-10-19. Template: STORY. Persona: none (failover no-face). Scope: capsule-use routine, not timing, dose selection, or benefits. No ingredient milligram amounts asserted.

## Confirmed claims — 15

Claim | Source URL | fetched+confirmed Y/N
--- | --- | ---
AgeAura's current product FAQ instructs two capsules daily. | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Y — WebFetch and live HTML extraction: “Follow the label: 2 capsules daily.”
The verified front label states 60 Capsules. | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Y — product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json plus visually opened original curated pack image.
The verified front label states 30 Servings. | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Y — same label record and original image; not interpreted as a personal daily prescription.
The live FAQ mentions water when breaking a fast. | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Y — exact extracted phrase: “if you fast, take with water when you break the fast.”
No opening, dissolving, fixed water-volume, or missed-day instructions were found in the checked front-label record and product FAQ. | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Y — bounded absence claim about checked sources, not every possible manufacturer document.
The product FAQ says not to exceed the label. | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Y — live HTML: “Don’t exceed the label.”
The product page advises professional consultation if pregnant, nursing, under 18, on medication, or managing a medical condition. | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Y — exact precaution paragraph fetched; not treated as proof of safety outside those groups.
Current product price was US$69.95. | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.js | Y — price=6995; available=true; website HTML Offer also 69.95 USD. WebFetch availability summary was inconsistent, so no availability claim appears in article.
Supplement labels identify serving size and servings per container. | https://www.fda.gov/food/information-consumers-using-dietary-supplements/questions-and-answers-dietary-supplements | Y — FDA label-disclosure section retrieved via WebFetch.
Manufacturers determine supplement serving sizes; FDA does not approve serving sizes. | https://www.fda.gov/food/information-consumers-using-dietary-supplements/questions-and-answers-dietary-supplements | Y — retrieved FDA dosing explanation; not an FDA-approved individual dose.
FDA recommends consulting a healthcare professional before taking supplements. | https://www.fda.gov/food/information-consumers-using-dietary-supplements/questions-and-answers-dietary-supplements | Y — fetched consumer-safety guidance.
Supplements can interact with medicines or other supplements. | https://www.fda.gov/food/information-consumers-using-dietary-supplements/questions-and-answers-dietary-supplements | Y — fetched guidance; no NMN-specific interaction invented.
General NHS pill-swallowing advice recommends taking pills with water. | https://www.nhs.uk/conditions/problems-swallowing-pills/ | Y — “take pills with water”; clearly attributed as general advice, not an NMN absorption finding.
NHS advises against opening capsules or altering pills without medical advice. | https://www.nhs.uk/conditions/problems-swallowing-pills/ | Y — fetched guidance; article recommends product-specific confirmation rather than claiming a capsule coating or release mechanism.
NHS warns against its pill-swallowing techniques when someone also struggles to swallow food or drink because of choking risk. | https://www.nhs.uk/conditions/problems-swallowing-pills/ | Y — fetched guidance; medical advice recommended instead.

## Recommendations, not empirical claims

Single reminder, taken/not-taken note, retaining original label during travel, and contacting seller when bottle and website disagree are practical editorial suggestions. No claim of demonstrated adherence improvement, faster absorption, health benefit, missed-dose harm, or lost efficacy. Do-not-double advice is limited to not exceeding the verified label and seeking professional instructions; no fabricated NMN missed-dose protocol.

## Research and verification notes

- STEP 0: live suggest.json primary-keyword query returned only the existing time-to-effect article, not this capsule-use intent. Recheck immediately before publish.
- STEP 0.5: topic_fitness PASS [brand].
- Keywords/questions: how to take nmn; how to use nmn capsules; nmn capsule directions; swallow or dissolve nmn; nmn with water; missed day; opening a capsule. Ticket-provided question set, not presented as observed PAA.
- WebSearch attempted three relevant queries but returned no result blocks. Google search fetch returned access notice; Bing fetch did not expose relevant organic results or PAA. Top-three ranking competitor review could not be verified; no invented SERP rankings. A guessed ProHealth guide URL returned 404 and is not cited.
- NIH ODS URLs returned 403/no readable body; excluded. FDA and NHS supplied fetched, relevant primary institutional guidance.
- get_internal_links.py ran successfully, returned no recommendations. Ticket's three related articles, product, best-seller collection and roster author page all verified HTTP 200 with Mozilla/5.0.
- Product page ingredient marketing differs from narrow front-label source; no added blend ingredients, doses, treatment claims, research efficacy claims, or slogans copied as evidence.
- Four images generated with ima2 OAuth; no-face throughout. Hero and product inline images use curated --product-ref without index. All outputs opened and visually checked against original bottle. No persona tool or persona file used.
- Travel concept initial QC FAIL: “no packaging reference to compare against”; replaced with product-in-scene and curated ref, then QC PASS. Other three images QC PASS first attempt.
- ima2 $0 subscription (standing approval).

## Publication result

- validate_article.py: exit 0, ✓ PASS; 1,250 content words. QRG scorer unavailable (runtime not installed); not claimed as measured PASS.
- geo_official_lint.py: 0 warnings.
- Immediately before publish: published_today=2; suggest.json still only the unrelated time-to-effect article.
- Published with shopify_publisher.py --live: article 634944684347, https://wellnessnest.co/blogs/news/how-to-take-nmn-a-capsule-routine-in-the-us .
- Publisher CDN gate: PASS 4/4; verify_published.py PASS author, schema, table. Public HTTP 200 with Mozilla/5.0. published_at=2026-10-18T19:38:21-07:00 (2026-10-19 UTC/local run date).
- Read-only runnable check: python3 run-assets/how-to-take-nmn/verify_live.py . Four CDN images and rendered URL aliases return HTTP 200 with image bytes, three inline images present, hero present, widget clean handle confirmed.
- Additional schema audit: publisher body has one Article schema; theme adds another Article schema and a different date formatting. repair_schema.py reports healthy/no changes. Theme/schema edits require separate approval; left untouched and reported as warning, not falsely declared fixed.
- Publisher rewrote the local draft by stripping H1/meta/hero and replacing local images with CDN URLs; restored source draft metadata and local image references after publication so it remains a reusable validated source. No live content update required.
- Refresh review due 2027-01-17. No planner skill available; review date recorded in tracker.

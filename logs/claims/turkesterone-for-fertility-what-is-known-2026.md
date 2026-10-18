# CA1016-4 claims check — 2026-10-18

Verification performed by automated source retrieval and review; not a claimed human medical review. No fertility benefit, fertility dose, ingredient amount or reproductive-safety claim is inferred.

Claim | Source URL | fetched+confirmed Y/N
--- | --- | ---
Targeted title/abstract search for turkesterone AND fertility/sperm/conception returned zero; broader retrieved records did not identify a human fertility trial. This describes search results, not proof no study exists anywhere. | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=TITLE_ABS%3Aturkesterone%20AND%20%28fertility%20OR%20sperm%20OR%20conception%29&format=json&pageSize=6&resultType=core | Y
The acute preliminary human study included 11 apparently healthy men. | https://pmc.ncbi.nlm.nih.gov/articles/PMC12121319/ | Y
The study used single-ingestion conditions with follow-up through 24 hours and metabolic monitoring through three hours. | https://pmc.ncbi.nlm.nih.gov/articles/PMC12121319/ | Y
The study measured IGF-1, resting metabolic rate and fuel metabolism, finding no significant treatment-related changes in the main IGF-1/metabolic outcomes. | https://pmc.ncbi.nlm.nih.gov/articles/PMC12121319/ | Y
The study did not measure sperm, semen, conception or pregnancy outcomes; its findings cannot establish reproductive safety or efficacy. | https://pmc.ncbi.nlm.nih.gov/articles/PMC12121319/ | Y
FDA recommends discussing supplements with qualified health professionals; interactions with medicines or other supplements can occur. | https://www.fda.gov/food/information-consumers-using-dietary-supplements/questions-and-answers-dietary-supplements | Y
FDA does not approve dietary supplements for safety/effectiveness before sale. | https://www.fda.gov/food/information-consumers-using-dietary-supplements/questions-and-answers-dietary-supplements | Y
CDC describes male assessment using history, examination and semen analysis measuring concentration, movement and shape; specialist interpretation matters. | https://www.cdc.gov/reproductive-health/infertility-faq/index.html | Y
CDC advises evaluation after 12 months for couples without obvious concerns when the female partner is under 35; six months when 35 or older; sooner over 40 or with known concerns. | https://www.cdc.gov/reproductive-health/infertility-faq/index.html | Y
CDC lists testicular injury, chemotherapy, previous fertility difficulties and sexual-function problems as reasons for men not to delay evaluation. | https://www.cdc.gov/reproductive-health/infertility-faq/index.html | Y
CDC supports preconception consultation and assessment involving both partners; mildly abnormal semen results do not necessarily establish infertility. | https://www.cdc.gov/reproductive-health/infertility-faq/index.html | Y
Wellness Nest listed Turkesterone Advanced Formula at 7500 cents ($75), available, when retrieved. Product and both ticket collection URLs returned HTTP 200. | https://wellnessnest.co/products/turkesterone-advanced-formula.js | Y
The curated front reference identifies Turkesterone Advanced Formula and Dietary Supplement, not a Supplement Facts panel; no ingredient quantity or serving regimen is inferred. | https://wellnessnest.co/products/turkesterone-advanced-formula | Y — identity visually confirmed against product_refs/turkesterone-advanced-formula.png and .label.json, not PDP formula prose

## Research and asset record

- STEP 0: suggest.json returned no article matches. STEP 0.5: PASS [brand].
- WebSearch for primary fertility/trial query returned no results in this environment; no top-three ranking/PAA claims fabricated. Expanded questions came from the ticket and retrieved evidence: sperm effects, human trial, trying to conceive, clinician evaluation, US buying context.
- PubMed UI returned cookie barrier; Europe PMC API retrieved PubMed-indexed study records and exact targeted search count. PMC full study retrieved independently.
- AUA guideline required login; attempted ReproductiveFacts/ASRM URLs returned error pages; NIH page returned 503. No claims attributed to those inaccessible pages.
- get_internal_links.py returned no Power/Target recommendations. Ticket article links and collections verified HTTP 200.
- Template:EDITORIAL. Persona: none (failover no-face). No persona_picker.py or persona refs.
- Hero:bedside-table; inline:home-office-desk/kitchen-table/entryway-console. Final four QC PASS; inline-clinician first attempt failed missing packaging reference, corrected on next roll. Final packaging visually compared with curated reference.
- ima2 $0 subscription (standing approval).
- Post-publish: article 634940653883, published_at 2026-10-17T21:25:42-07:00 (2026-10-18 UTC). Initial named-Person schema check failed; repair_schema.py corrected this newly created article, subsequent verify_published.py PASS. CDN 4/4 HTTP 200 image bytes; rendered-body 3/3; frontend HTTP 200 with Mozilla/5.0; shop widget contains clean handle turkesterone-advanced-formula within pipe delimiters. One custom widget assert assumed no delimiters and failed; inspection confirmed valid pipe-delimited markup, not a storefront defect.
- Validator: PASS, 1460 words. QRG scoring unavailable: claude-seo runtime not installed. CDC and Europe PMC search links inconclusive HTTP 403 in validator; content was separately retrieved from CDC via WebFetch and Europe PMC API.

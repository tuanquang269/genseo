# Claims log — is turkesterone banned by WADA?

Refresh of the live article `turkesterone-for-athletes-drug-test-guide-us-2026` (article id 634907001147). Same URL. Not published.

SEO title rewritten for the query "is turkesterone banned by WADA" (44 characters): "Is Turkesterone Banned by WADA? No (US 2026)". The "No" is the same answer as the opening block below, not a new claim.

Meta description rewritten (160 characters): "No. The 2026 WADA Prohibited List does not name turkesterone. Ecdysterone is monitored, not on that list. US athletes should still check the product with USADA." "Not on that list" repeats the Monitoring Program point already in the opening: the program names ecdysterone as a substance that is not on the Prohibited List.

Opening answer block, unchanged: 57 words. WADA status is taken from the 2026 Prohibited List and the 2026 Monitoring Program, with USADA's ecdysteroids page as the US anti-doping reading of the class. List year stated: 2026, in force 1 January 2026. No body sentence changed in this pass. The draft byline is Mike Moretti, co-founder. The sentence is the roster bio from the same entry as draft PR #94. No headshot was added.

## Fetched for the WADA answer

- 2026 Prohibited List (English PDF, effective 1 January 2026): https://www.wada-ama.org/sites/default/files/2025-09/2026list_en_final_clean_september_2025.pdf
  - The retrieved text does not contain "turkesterone" or "ecdysterone".
  - S2 names "Insulin-like growth factor 1 (IGF-1, mecasermin) and its analogues." It does not say that every colostrum product contains IGF-1.
  - A direct curl of this PDF from this machine returned HTTP 202 with an empty body (CloudFront WAF challenge). The text used here is the fetch of that same official URL on 24 October 2026.
- 2026 Monitoring Program PDF: https://www.wada-ama.org/sites/default/files/2025-09/2026_list_monitoring_program_en_final_clean_september_2025.pdf
  - Quotes Code Article 4.5: substances which are not on the Prohibited List, monitored for patterns of misuse.
  - Anabolic agents, in and out of competition: Ecdysterone.
  - Turkesterone is not named.
- List index page, in force 1 January 2026: https://www.wada-ama.org/en/resources/world-anti-doping-code-and-international-standards/prohibited-list
- USADA, "What Athletes Need to Know about Ecdysteroids," retrieved 24 October 2026, no publication date on the page: https://www.usada.org/dietary-supplements/athletes-need-know-ecdysteroids/
  - Names turkesterone with ecdysterone and ecdysone as ecdysteroids.
  - "While not currently prohibited under the World Anti-Doping Agency (WADA) rules, ecdysteroids are on the WADA Monitoring List."
  - "No, at present, WADA has not added ecdysteroids to the Prohibited List." Monitoring list since 2020.
  - "There are no FDA-approved medications that contain ecdysteroids."
  - Tells athletes to use third-party certified supplements and gives the Drug Reference Line, (719) 785-2000 option 2.
- NCAA 2026-27 banned substances PDF, fetched 24 October 2026: https://ncaaorg.s3.amazonaws.com/ssi/substance/2026-27/2026-27NCAA_BannedSubstances.pdf
  - The text includes the line "IGF-1 (colostrum; deer antler velvet)".
  - Turkesterone is not named in the lines retrieved.

## Removed

- https://www.usada.org/spirit-of-sport/nutrition/natural-products-derived-from-plants-and-animals/ returned HTTP 404 to the article gate. The USADA colostrum/IGF-1 sentence that depended on it was deleted. The IGF-1 and colostrum sentences now cite the 2026 WADA list and the NCAA PDF above.

## Product facts

- Public product catalog, 24 October 2026: `turkesterone-advanced-formula`, price 7500 cents ($75.00), available. https://wellnessnest.co/products/turkesterone-advanced-formula.js
- The same description names 500 mg turkesterone, 300 mg KSM-66 ashwagandha, 250 mg tongkat ali, 250 mg colostrum, 10 mg BioPerine, 60 capsules, and "take 2 daily." Those milligram amounts and the "2 daily" direction are not in `product_refs/turkesterone-advanced-formula.label.json`. The draft does not repeat them.
- Agreed pack-label lines: wellness, nest, PREMIUM, TURKESTERONE, ADVANCED, FORMULA, AMPLIFY, MUSCLE, ENDURANCE, 60, Dietary Supplement, Capsules. No milligram amount. Colostrum was not an agreed OCR line (`docs/TURKESTERONE_LABEL_GUARD.md`).
- Vault entity `~/PATI/LLM-Wiki/20-brands/21-wellnessnest-products/7-turkesterone.md` lists a $75 draft price and a different formula story. The $75 figure used here is the public catalog price above.

## Preserved from the live article, not re-fetched this pass

Certification, strict-liability, and supplement-risk paragraphs were already on the public article:

https://wellnessnest.co/blogs/news/turkesterone-for-athletes-drug-test-guide-us-2026

Remaining USADA link from that article:

- https://www.usada.org/athlete-advisory/supplement-risk-nsf-certified-for-sport/

## Internal links (existing organic posts and collections; pages not edited)

- https://wellnessnest.co/blogs/news/turkesterone-side-effects-4-ingredients-to-check-us-2026
- https://wellnessnest.co/blogs/news/turkesterone-vs-ecdysterone-which-is-worth-it-us-2026
- https://wellnessnest.co/blogs/news/turkesterone-benefits-dosing-whats-real-us-2026
- https://wellnessnest.co/blogs/news/how-long-does-turkesterone-take-to-work-us-2026
- https://wellnessnest.co/blogs/news/turkesterone-over-60-5-checks-in-the-us
- https://wellnessnest.co/blogs/news/turkesterone-cycle-do-you-need-breaks-us-2026
- https://wellnessnest.co/collections/mens-essential-collection
- https://wellnessnest.co/collections/shilajit-wellness-stack
- https://wellnessnest.co/products/turkesterone-advanced-formula

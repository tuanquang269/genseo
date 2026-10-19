# CA1016-11 — nmn price

Checked 2026-10-19. Automated source verification; no claim of human review. 12 confirmed factual claims/calculations. No market-wide price range, ingredient dose, clinical effect, stock promise or testing certification used.

Claim | Source URL | fetched+confirmed Y/N
--- | --- | ---
AgeAura Pure NMN + TMG NAD+ Complex listed price is $69.95 USD on 2026-10-19 | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex ; https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.js | Y — live PDP and product JSON fetched by research agent
Pack reads 60 Capsules | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Y — product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json read by research agent; curated original PNG visually opened by main agent
Pack reads 30 Servings | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Y — label JSON plus original reference PNG, not generated image
Price per labeled serving is $69.95 / 30 = $2.331666..., rounded $2.33 | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Y — arithmetic from confirmed price and label count
Price per capsule is $69.95 / 60 = $1.165833..., rounded $1.17 | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Y — arithmetic from confirmed price and label count
Capsule count and serving count are different units on this pack | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Y — 60 versus 30 visibly confirmed
Supplement labels include serving size and servings per container | https://www.fda.gov/food/information-consumers-using-dietary-supplements/questions-and-answers-dietary-supplements | Y — main agent WebFetch retrieved FDA labeling explanation
Supplement Facts lists dietary ingredient quantities, with exception for individual proprietary-blend quantities | https://www.fda.gov/food/information-consumers-using-dietary-supplements/questions-and-answers-dietary-supplements | Y — fetched FDA text confirms exception
FDA does not approve dietary supplements before marketing | https://www.fda.gov/food/information-consumers-using-dietary-supplements/questions-and-answers-dietary-supplements | Y — fetched exact FDA statement
FDA advises consultation with healthcare professional before purchasing/using supplements | https://www.fda.gov/food/information-consumers-using-dietary-supplements/questions-and-answers-dietary-supplements | Y — fetched FDA advice
Supplements may interact with medicines | https://www.fda.gov/food/information-consumers-using-dietary-supplements/questions-and-answers-dietary-supplements | Y — fetched FDA safety guidance; draft recommends consultation for medication users
Named author and verbatim bio match approved roster | https://wellnessnest.co/pages/dr-marcus-hale | Y — local roster.json read; linked page HTTP 200

## Research limits
- PDP rendered availability and product JSON availability conflict. No stock assertion published.
- Search-result price bands were not fetched and confirmed. Excluded entirely.
- No dollars-per-milligram or ingredient-dose calculation: the pack-count source is not a verified Supplement Facts dose panel.
- NIH ODS request returned 403; not cited.
- FDA regulatory-history details unnecessary for price scope; link related where-to-buy article instead.
- Search research supplied broad comparison, price-explainer and cost-normalization angles, not verified rank positions or a literal PAA box. No ranking/PAA claim made.
- Product-ref packaging visually checked against all three generated product scenes. All four image QC calls PASS; no-face throughout.

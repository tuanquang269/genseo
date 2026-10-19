# CA1016-8 claim check — 2026-10-19

Automated source verification; not represented as a human clinical review. PubMed returned cookie challenges; abstracts fetched and confirmed through Europe PMC's core records. No unconfirmed dose, mechanism, absorption, safety, or efficacy claim retained. Medical-care instructions and routine examples are cautious advice, not measured outcomes.

Claim | Source URL | fetched+confirmed Y/N
--- | --- | ---
Green et al. compared creatine alone against creatine plus carbohydrate in humans | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:8944667&format=json&resultType=core | Y
The Green study enrolled 24 men and lasted five days | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:8944667&format=json&resultType=core | Y
Both Green study groups increased muscle creatine; the carbohydrate group increased it more | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:8944667&format=json&resultType=core | Y
Green used dissolved creatine and a substantial simple-carbohydrate protocol, not FusiForce gummies or a comparison of ordinary breakfasts | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:8944667&format=json&resultType=core | Y
The Green abstract does not establish an overnight-fast gummy advantage or a requirement for added carbohydrate | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:8944667&format=json&resultType=core | Y
Steenge et al. studied 12 men with creatine and protein/carbohydrate treatments | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:10956365&format=json&resultType=core | Y
Certain carbohydrate-containing treatments enhanced whole-body creatine retention in Steenge | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:10956365&format=json&resultType=core | Y
Steenge measured whole-body retention, not direct intestinal gummy absorption or long-term training superiority | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:10956365&format=json&resultType=core | Y
Neither cited abstract establishes FusiForce-specific empty-stomach tolerance, superior fasted use, or breakfast-enhanced gummy absorption | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:8944667%20OR%20EXT_ID:10956365&format=json&resultType=core | Y (individual records fetched separately)
FusiForce live product description says Take anytime and suggests the same time each day; it specifies no meal requirement | https://wellnessnest.co/products/fusiforce-creatine-gummies.js | Y
FusiForce live product JSON price was 6999 cents ($69.99), available true; draft avoids a stock promise due to inconsistent rendered extraction | https://wellnessnest.co/products/fusiforce-creatine-gummies.js | Y
FusiForce package is a green stand-up pouch with Green Apple flavor branding matching the generated hero and product inline | https://wellnessnest.co/products/fusiforce-creatine-gummies | Y (curated product_refs/fusiforce-creatine-gummies.png opened and compared)

## Research and scope
- STEP 0: live suggest.json returned no articles for the exact primary keyword.
- STEP 0.5: PASS [brand].
- Template: EDITORIAL. Primary: creatine gummies on an empty stomach. Supporting questions: creatine without food; meal/absorption versus retention; fasted workout routine; gummy stomach comfort.
- WebSearch attempted three queries; no usable results returned. Top-three SERP positions/PAA could not be verified; none claimed. Outline follows approved ticket plus fetched trials and product-specific directions.
- All product/collection/article/author links fetched with browser User-Agent; HTTP 200.
- Four images QC:PASS; visually reviewed. persona: none (failover no-face). Scenes: entryway-bench/dining-table/home-exercise-floor/home-office-meal-shelf.
- ima2 $0 subscription (standing approval).
- Review after 90 days: 2027-01-17. No scheduled refresh or changes to existing live posts.

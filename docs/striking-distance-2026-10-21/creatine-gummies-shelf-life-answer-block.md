# DRAFT proposal — creatine gummy shelf life (do not publish)

Status: **DRAFT. Not published. Not a ticket. No Shopify write.**

This is a refresh block for the blog post that already ranks for both queries. Do not open a second URL for "how long do they last." Do not change the title or the handle. The byline to apply is Mike Moretti, Co-founder, Wellness Nest. Applying the refresh still waits on a live `/pages/mike-moretti` (HTTP 404 on 2026-10-21, recorded in PR #88).

| Field | Value |
|---|---|
| Queries | "how long do creatine gummies last" (5 imp, pos 8.2, 0 clicks); "do creatine gummies expire" (6 imp, pos 10.2, 0 clicks) |
| Owning URL | https://wellnessnest.co/blogs/news/do-creatine-gummies-expire-6-storage-facts-us-2026 |
| Action | Refresh the opening so the first sentences answer both "expire" and "how long," and add those FAQ lines. Keep the existing storage sections. |
| Byline | **Mike Moretti**, role `Co-founder, Wellness Nest` (Kevin 2026-10-21). The earlier draft recorded the live Article author as Dr. Marcus Hale. This pass does not update the post. `/pages/mike-moretti` returned HTTP 404 on 2026-10-21 (PR #88; HEAD during this edit was 404 again), so the apply waits on Kevin creating that page. |
| Title | Keep `Do Creatine Gummies Expire? 6 Storage Facts (US 2026)`. |

`topic_fitness.py` can return REVIEW for "how long" because that phrase is not in the title. Search Console still gives every impression for that query to this URL. The refresh stays on this URL.

Apply only the block between the markers.

<!-- proposed-block -->
<p>Creatine gummies do expire. How long they last is the date on that pouch, when it has one. In the US, FDA rules do not require an expiration date, and a printed date needs the maker's own data. Dry creatine powder showed no degradation after more than 3 years at 40°C. A moist gummy does not inherit that result.</p>

<h2>How long do creatine gummies last?</h2>
<p>Until the date on that pouch, if the brand printed one. There is no single month count that fits every gummy. <a href="https://www.fda.gov/regulatory-information/search-fda-guidance-documents/small-entity-compliance-guide-current-good-manufacturing-practice-manufacturing-packaging-labeling">FDA's small-entity guide for dietary-supplement manufacturing</a> says the rule does not require an expiration date, a shelf date, or a "best if used by" date. If a company prints one, it should have data to support that date. Dry creatine monohydrate powder is a different product: <a href="https://doi.org/10.1007/s00726-011-0874-6">Jäger and colleagues</a> report no creatinine above the 67 ppm quantification limit after more than 3 years at room temperature or at 40°C (104°F). In solution, lower pH and higher temperature speed the change to creatinine. A gummy holds water, so the powder result does not transfer. Days of use in one FusiForce pouch are not calculated here.</p>

<h2>Do creatine gummies expire?</h2>
<p>Yes. Treat a printed date as the outer limit for a pouch stored as the label says, and discard a pouch that smells off, shows mold, or was cooked in heat even if the date has not arrived. The solution data below describe liquids, not finished gummies. They show the direction of the risk.</p>

<h2>Frequently Asked Questions</h2>
<h3>How long do creatine gummies last?</h3>
<p><strong>As long as the date on that pouch, when the pouch has a date.</strong> US supplement rules do not require the date. Powder stability of more than 3 years at 40°C is not a gummy shelf life. How many days one pouch lasts in use was not calculated: the front-of-pack read lists 90 and does not list a serving size.</p>
<h3>Do creatine gummies expire?</h3>
<p><strong>Yes.</strong> Use the printed date when there is one. Heat, moisture, and acid give creatine a path to creatinine that dry powder does not have. A melted shape alone is not described in these sources as mold. Smell, mold, or a passed date are reasons to discard the pouch.</p>
<h3>Does the powder study apply to a gummy?</h3>
<p><strong>No.</strong> The multi-year result is creatine monohydrate powder. The same review says creatine in water degrades, faster when the liquid is more acidic and warmer. After 3 days at 25°C the cited solution losses were 4% at pH 5.5, 12% at pH 4.5, and 21% at pH 3.5. Those percentages are not gummy losses.</p>
<h3>Where can I buy FusiForce creatine gummies in the US?</h3>
<p><strong>On the Wellness Nest product page, checked 2026-10-21.</strong> <a href="https://wellnessnest.co/products/fusiforce-creatine-gummies">FusiForce Creatine Monohydrate Gummies</a> — the live product title includes 5,000 mg — listed at $69.99. The handle is in the <a href="https://wellnessnest.co/collections/best-seller">Best Seller collection</a> and the <a href="https://wellnessnest.co/collections/mens-essential-collection">Men's Essential collection</a>. For the daily count, read <a href="https://wellnessnest.co/blogs/news/creatine-gummies-dosage-how-many-a-day-us-2026">creatine gummies dosage: how many a day</a>.</p>
<!-- /proposed-block -->

## Sources checked 2026-10-21

- Jäger R, Purpura M, Shao A, Inoue T, Kreider RB. Analysis of the efficacy, safety, and regulatory status of novel forms of creatine. 2011. PMID 21424716. Full text via Europe PMC, PMC3080578. DOI https://doi.org/10.1007/s00726-011-0874-6. Powder: no creatinine above 67 ppm after more than 3 years at room temperature or 40°C (104°F). At 60°C (140°F), 106 ppm creatinine was detected after 44 months. Solution: after 3 days at 25°C, about 4% loss at pH 5.5, 12% at pH 4.5, 21% at pH 3.5. Journal title was null in the Europe PMC search record; the full text was read.
- FDA, Small Entity Compliance Guide for dietary-supplement CGMP. Fetched 2026-10-21: the DS CGMP rule does not require an expiration date (or a shelf date or "best if used by" date). If you place one, you should have data to support it. 72 FR 34752 at 34855. https://www.fda.gov/regulatory-information/search-fda-guidance-documents/small-entity-compliance-guide-current-good-manufacturing-practice-manufacturing-packaging-labeling
- FusiForce identity: `product_refs/fusiforce-creatine-gummies.label.json` (front OCR, 2026-10-08) required lines include FusiForce, Creatine, Monohydrate, Gummies, 90, Dietary Supplement. No serving size and no shelf-life length are in that file. Live product title from `products/fusiforce-creatine-gummies.js`: "FusiForce - Creatine Monohydrate Gummies 5,000 mg". Variant price 6999 cents ($69.99) on 2026-10-21.
- Collection membership the same day: the handle is in `best-seller` and `mens-essential-collection`.
- Sibling article HTTP 200: `creatine-gummies-dosage-how-many-a-day-us-2026`.

## UNVERIFIED in this pass

- How many days one FusiForce pouch lasts. The front OCR has "90" and does not list gummies per serving. The store description mentions a 3-gummy serving. Those two sources were not multiplied. The older vault note of 28 servings was not re-read off a facts panel in this pass.
- The live article's "about 60% lost in 28 days" citric-acid figure was not in the Jäger full text read here. This block does not repeat it.
- No gummy-specific shelf-life month count was found in the sources above. Do not invent one.
- "Lab-tested," COA, and NSF are not used in this block.

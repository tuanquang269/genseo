# Off-page listicle gap list — 2026-10-20

Draft research for Wellness Nest. No email was sent. No Shopify write was made.

Spark: Search Engine Land, [How to audit off-page AI search visibility and build a 90-day plan](https://searchengineland.com/audit-off-page-ai-search-visibility-90-day-plan-494866) (published October 12, 2026). The article says third-party listicles and comparison pages matter, and it sorts them by how often an AI-visibility tool retrieved them. This run did not use that tool. Every row has `ai_citation_observed: false`. The evidence field is `web search rank`, plus a page GET when the fetch succeeded.

No ChatGPT, Perplexity, or Google AI Overview session was run. ai_citation_observed is false on every source. A web search rank is not an AI citation.

## Products in scope

- AgeAura outreach is only AgeAura Pure NMN + TMG NAD+ Complex: https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex
- ShilaSource outreach is only ShilaSource Himalayan Shilajit Resin: https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin
- Pack lines that may be quoted live in the matching `product_refs/*.label.json` file. Do not add a milligram amount.

## Hypothesised prompts

These are hypothesised prompts, not questions observed in an answer engine.

### ageaura

- best NMN supplement — hypothesised
- best NMN supplement 2026 — hypothesised
- best NMN with TMG — hypothesised
- NMN vs NR — hypothesised
- best NAD+ supplement 2026 — hypothesised
- best NAD booster supplement — hypothesised
- best NMN capsules — hypothesised
- NMN and TMG together — hypothesised
- best NMN supplement reddit — hypothesised
- top NMN brands compared — hypothesised
- best liposomal NMN — hypothesised
- pure NMN supplement brand — hypothesised
- best NMN for longevity — hypothesised
- NMN TMG stack review — hypothesised
- best NMN supplement third party tested — hypothesised
- NAD+ precursor comparison NMN NR — hypothesised
- best NMN powder — hypothesised
- Wonderfeel vs Tru Niagen — hypothesised

### shilasource

- best shilajit resin — hypothesised
- best shilajit gummies — hypothesised
- best shilajit supplement — hypothesised
- pure Himalayan shilajit brand — hypothesised
- best shilajit 2026 — hypothesised
- best shilajit resin reddit — hypothesised
- shilajit resin vs gummies — hypothesised
- best authentic shilajit — hypothesised
- best shilajit for men — hypothesised
- legitimate shilajit brands — hypothesised
- best Himalayan shilajit resin — hypothesised
- best shilajit supplement 2026 — hypothesised
- shilajit brands compared — hypothesised
- best third party tested shilajit — hypothesised
- pure shilajit resin brands — hypothesised
- best shilajit drops — hypothesised
- shilajit resin brands reddit — hypothesised
- best shilajit gummies 2026 — hypothesised

## Fetch

| Counter | Value |
|---|---|
| GET budget | 200 |
| GETs used | 79 |
| HTTP 200 | 65 |
| HTTP 429 | 0 |
| HTTP 404 | 4 |
| robots disallow | 9 |
| other non-200 | 10 |

The GET count includes robots.txt and contact-page checks, not only article URLs. A robots.txt Disallow skips that article URL. A 429 waits and retries once. A 403 on robots.txt is not treated as a disallow, because the rules were not readable; the article GET still counts toward the budget.

The counters above are the completed fetch only. An earlier pass the same day requested this URL set and stopped when a contact page timed out, so those reads are not in the table. Nine later reads checked brand context and date meta on pages that run had already opened. Each pass stayed inside the 200 GET budget.

## Counts

| Cluster | Sources | Already name us | Gaps |
|---|---|---|---|
| ageaura | 20 | 0 | 19 |
| shilasource | 24 | 5 | 16 |

## How a gap is scored

A gap is a page that names at least one other brand and does not name Wellness Nest or the cluster brand. An explainer needs two other brands. Studies are not gaps. The score adds a page-type weight, up to six brands, and a small bonus when a 2025 or 2026 date is shown on the page. A search snippet is weighted lower than a fetched page. Competitor-owned roundups stay in the list and are marked do-not-pitch. A gummy URL can still score as a gap; the resin sample is not the pitch for that URL. Nothing here is a retrieval count.

## Top gaps — AgeAura Pure NMN + TMG

### 1. The 8 Best NMN Supplements of 2026: Expert Approved | Fortune

- Score: 67. Type: listicle. Domain: `fortune.com`.
- URL: https://fortune.com/article/best-nmn-supplements/
- Date shown: October 16, 2026 (from the page date meta; the byline was outside the first screen of prose)
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: PartiQlar, Wonderfeel, Omre, Transparent Labs, For Youth, Welzo, GenuinePurity, Hello100 (+2 more)
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://fortune.com/2021/04/15/how-to-pitch-fortune-get-a-story-picked-up-business-magazine-freelance-work-pitching-advice/
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of AgeAura Pure NMN + TMG NAD+ Complex (https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex). Quote only lines in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json. Do not add a milligram amount. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA. Link a report only if Kevin already published it as HTML.

### 2. Best NMN Supplement (2026): Testing, Dose and Cost Compared

- Score: 67. Type: listicle. Domain: `verifiedsupplementdata.com`.
- URL: https://verifiedsupplementdata.com/nmn/best-overall/
- Date shown: October 12, 2026
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Transparent Labs, Neurogan, Renue By Science, Toniiq, Codeage, ProHealth, Genex Formulas, Double Wood (+2 more)
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://verifiedsupplementdata.com/about/
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of AgeAura Pure NMN + TMG NAD+ Complex (https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex). Quote only lines in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json. Do not add a milligram amount. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA. Link a report only if Kevin already published it as HTML.

### 3. Best NMN Supplements 2026: Cost per Effective Dose

- Score: 63. Type: roundup. Domain: `verifiedsupplementdata.com`.
- URL: https://verifiedsupplementdata.com/supplements/nmn/
- Date shown: October 12, 2026
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Transparent Labs, Renue By Science, Neurogan, Toniiq, Nutricost, ProHealth, Codeage, Elysium
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://verifiedsupplementdata.com/about/
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of AgeAura Pure NMN + TMG NAD+ Complex (https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex). Quote only lines in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json. Do not add a milligram amount. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA. Link a report only if Kevin already published it as HTML.

### 4. Best NMN Supplements: 2026 Buyer's Guide

- Score: 61. Type: listicle. Domain: `healthline.com`.
- URL: https://www.healthline.com/health/best-nmn-supplements
- Date shown: April 29, 2026 (from the page date meta; the byline was outside the first screen of prose)
- Note: Thorne is named in an author aside about other brands, not as an NMN pick, so it is not in the brand list.
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: California Gold Nutrition, Double Wood, Nutricost
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://www.healthline.com/about/contact-us
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of AgeAura Pure NMN + TMG NAD+ Complex (https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex). Quote only lines in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json. Do not add a milligram amount. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA. Link a report only if Kevin already published it as HTML.

### 5. Third-Party Tested NMN 2026: Which Brands Are Certified

- Score: 59. Type: directory. Domain: `verifiedsupplementdata.com`.
- URL: https://verifiedsupplementdata.com/nmn/third-party-tested/
- Date shown: October 12, 2026
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Transparent Labs, Codeage, Cata-Kor, Elysium, Renue By Science, Neurogan, Toniiq
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://verifiedsupplementdata.com/about/
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of AgeAura Pure NMN + TMG NAD+ Complex (https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex). Quote only lines in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json. Do not add a milligram amount. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA. Link a report only if Kevin already published it as HTML.

### 6. Wonderfeel Youngr NMN vs Tru Niagen (2026): Which NAD+ Booster Wins?

- Score: 59. Type: comparison. Domain: `bettervitals.com`.
- URL: https://www.bettervitals.com/learn/tru-niagen-vs-wonderfeel-youngr
- Date shown: Jul 10, 2026
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Wonderfeel, Tru Niagen, NOVOS
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://www.bettervitals.com/contact
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of AgeAura Pure NMN + TMG NAD+ Complex (https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex). Quote only lines in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json. Do not add a milligram amount. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA. Link a report only if Kevin already published it as HTML.

### 7. Best TMG (Trimethylglycine) Supplements: The NMN and Creatine Partner

- Score: 59. Type: listicle. Domain: `usefulvitamins.com`.
- URL: https://usefulvitamins.com/best-tmg-supplements/
- Date shown: May 29, 2026
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Double Wood, Nutricost
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://usefulvitamins.com/contacts/
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of AgeAura Pure NMN + TMG NAD+ Complex (https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex). Quote only lines in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json. Do not add a milligram amount. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA. Link a report only if Kevin already published it as HTML.

### 8. NMN vs NR (2026): Which NAD+ Precursor Has Better Evidence?

- Score: 52. Type: comparison. Domain: `longevitybenchmark.com`.
- URL: https://www.longevitybenchmark.com/supplements/nmn-vs-nr/
- Date shown: not shown in the text we read
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Tru Niagen, Elysium
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://www.longevitybenchmark.com/about
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of AgeAura Pure NMN + TMG NAD+ Complex (https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex). Quote only lines in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json. Do not add a milligram amount. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA. Link a report only if Kevin already published it as HTML.

### 9. 7 Best NMN Supplements Of 2026 – Forbes Health

- Score: 34. Type: listicle. Domain: `forbes.com`.
- URL: https://www.forbes.com/health/wellness/best-nmn-supplements/
- Date shown: not shown in the text we read
- How found: web search rank. Evidence: web search rank. Basis: search_snippet. `ai_citation_observed: false`.
- Other brands named: BulkSupplements, Natural Factors, Genex Formulas, Upnourish, Nutricost, ProHealth, Innerbody Labs
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of AgeAura Pure NMN + TMG NAD+ Complex (https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex). Quote only lines in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json. Do not add a milligram amount. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA. Link a report only if Kevin already published it as HTML.

### 10. Which NMN Supplements Publish Third-Party Batch Test Results

- Score: 32. Type: roundup. Domain: `factually.co`.
- URL: https://factually.co/fact-checks/health-fitness/nmn-supplements-third-party-batch-test-results-1f16c6
- Date shown: not shown in the text we read
- How found: web search rank. Evidence: web search rank. Basis: search_snippet. `ai_citation_observed: false`.
- Other brands named: GenuinePurity, NOVOS, DoNotAge, PartiQlar, Jinfiniti, Welzo
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of AgeAura Pure NMN + TMG NAD+ Complex (https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex). Quote only lines in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json. Do not add a milligram amount. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA. Link a report only if Kevin already published it as HTML.

### 11. The 5 Best NAD+ Supplements for Optimal Aging, According to Dietitians

- Score: 31. Type: listicle. Domain: `verywellhealth.com`.
- URL: https://www.verywellhealth.com/best-nad-supplements-8713201
- Date shown: not shown in the text we read
- How found: web search rank. Evidence: web search rank. Basis: search_snippet. `ai_citation_observed: false`.
- Other brands named: Tru Niagen, Life Extension, Thorne
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of AgeAura Pure NMN + TMG NAD+ Complex (https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex). Quote only lines in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json. Do not add a milligram amount. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA. Link a report only if Kevin already published it as HTML.

### 12. 10 Best NAD Supplements Of 2026 – Forbes Health

- Score: 29. Type: listicle. Domain: `forbes.com`.
- URL: https://www.forbes.com/health/wellness/best-nad-supplements/
- Date shown: not shown in the text we read
- How found: web search rank. Evidence: web search rank. Basis: search_snippet. `ai_citation_observed: false`.
- Other brands named: Tru Niagen
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of AgeAura Pure NMN + TMG NAD+ Complex (https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex). Quote only lines in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json. Do not add a milligram amount. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA. Link a report only if Kevin already published it as HTML.

### 13. Best NAD Supplements of 2026: Top 6 NMN & NR Picks, Reviewed & Ranked

- Score: 22. Type: brand_roundup. Domain: `omre.co`.
- URL: https://omre.co/blogs/news/best-nad-supplements
- Date shown: not shown in the text we read
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Omre, Tru Niagen, PartiQlar, Innerbody Labs, Wonderfeel, Elysium
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: do_not_pitch. Competitor-owned roundup. The Search Engine Land SOP marks vendor pages do-not-pitch, because the page will not add a rival as the pick.

### 14. I want to start using NMN and NAD+ where do I start?

- Score: 19. Type: reddit. Domain: `reddit.com`.
- URL: https://www.reddit.com/r/NMN/comments/1q7m38v/i_want_to_start_using_nmn_and_nad_where_do_i_start/
- Date shown: not shown in the text we read
- How found: web search rank. Evidence: web search rank. Basis: search_snippet. `ai_citation_observed: false`.
- Other brands named: Renue By Science, ProHealth, PartiQlar, Manapura, Codeage
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: do_not_pitch. Community thread. Do not pitch. A roster writer may answer the question only if Kevin asks for that reply.

### 15. How do you pick a good NMN supplement you can trust?

- Score: 19. Type: reddit. Domain: `reddit.com`.
- URL: https://www.reddit.com/r/NMN/comments/1r0ywaj/how_do_you_pick_a_good_nmn_supplement_you_can/
- Date shown: not shown in the text we read
- How found: web search rank. Evidence: web search rank. Basis: search_snippet. `ai_citation_observed: false`.
- Other brands named: Solensis, Manapura, ProHealth, Renue By Science, PartiQlar
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: do_not_pitch. Community thread. Do not pitch. A roster writer may answer the question only if Kevin asks for that reply.

## Top gaps — ShilaSource / shilajit

### 1. Best Shilajit Supplements Review & Top Picks - ConsumerLab.com

- Score: 63. Type: roundup. Domain: `consumerlab.com`.
- URL: https://www.consumerlab.com/reviews/shilajit/shilajit-supplements/
- Date shown: May 7, 2026 (from the page date meta; the byline was outside the first screen of prose)
- Note: The product names are in the static image labels. The fetched copy says the full review needs JavaScript. This row is not a reading of a paid write-up.
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Pürblack, Lotus Blooming, Nootropics Depot, PrimaVie, Organifi, Pure Himalayan Shilajit
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://www.consumerlab.com/support/contact/
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of ShilaSource Himalayan Shilajit Resin (https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin). Quote only lines in product_refs/shilasource-himalayan-shilajit-resin.label.json. Do not add a milligram amount, a mineral count, or a joined serving count. Other shilajit jars and the gummy format are separate products and are not this outreach SKU. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA.

### 2. Best Shilajit Resin and Brands: 4 Picks, Lab Reports (2026)

- Score: 63. Type: listicle. Domain: `the-best-supplement.com`.
- URL: https://www.the-best-supplement.com/ranking/best-shilajit-resin
- Date shown: September 4, 2026 (from the page date meta; the byline was outside the first screen of prose)
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Natural Shilajit, Mountaindrop, Chuga, Pure Himalayan Shilajit
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of ShilaSource Himalayan Shilajit Resin (https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin). Quote only lines in product_refs/shilasource-himalayan-shilajit-resin.label.json. Do not add a milligram amount, a mineral count, or a joined serving count. Other shilajit jars and the gummy format are separate products and are not this outreach SKU. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA.

### 3. Best Shilajit Supplement | Our top 5 picks from testing [2026]

- Score: 62. Type: listicle. Domain: `innerbody.com`.
- URL: https://www.innerbody.com/best-shilajit-supplement
- Date shown: November 18, 2025 (from the page date meta; the byline was outside the first screen of prose)
- Note: A lowercase natural shilajit phrase in the article is the substance, not the Natural Shilajit brand, so it is not in the brand list.
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Nootropics Depot, Pure Himalayan Shilajit, Pürblack, Nugenix, PrimaVie
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of ShilaSource Himalayan Shilajit Resin (https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin). Quote only lines in product_refs/shilasource-himalayan-shilajit-resin.label.json. Do not add a milligram amount, a mineral count, or a joined serving count. Other shilajit jars and the gummy format are separate products and are not this outreach SKU. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA.

### 4. Best Shilajit Gummies (2026) — Top Picks Ranked & Compared

- Score: 60. Type: listicle. Domain: `shilajitdb.com`.
- URL: https://shilajitdb.com/best/best-gummies
- Date shown: not shown in the text we read
- Note: Ranked names were read from the static HTML. The shell also includes a loading line.
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Xara, Sunmed, Life Cykel, Root Labs, Novomins
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://shilajitdb.com/about
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of ShilaSource Himalayan Shilajit Resin (https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin). Quote only lines in product_refs/shilasource-himalayan-shilajit-resin.label.json. Do not add a milligram amount, a mineral count, or a joined serving count. Other shilajit jars and the gummy format are separate products and are not this outreach SKU. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA. This URL is a gummy roundup. Do not offer the resin as a gummy, and do not pitch another jar under the resin name.

### 5. Recent updates — Shilajit Transparency Database | ShilajitDB

- Score: 59. Type: directory. Domain: `shilajitdb.com`.
- URL: https://shilajitdb.com/updates
- Date shown: Oct 9, 2026
- Note: Ranked names were read from the static HTML. The shell also includes a loading line. Himalayan Natural Shilajit Gummies is a different product line, so it is not counted as the Natural Shilajit brand.
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Lotus Blooming, Pürblack, Root Labs, Novomins, VitaUp, Essencraft, Pure Himalayan Shilajit, Life Cykel (+4 more)
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://shilajitdb.com/about
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of ShilaSource Himalayan Shilajit Resin (https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin). Quote only lines in product_refs/shilasource-himalayan-shilajit-resin.label.json. Do not add a milligram amount, a mineral count, or a joined serving count. Other shilajit jars and the gummy format are separate products and are not this outreach SKU. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA.

### 6. Best Shilajit Resin (2026) — Top Picks Ranked & Compared

- Score: 58. Type: listicle. Domain: `shilajitdb.com`.
- URL: https://shilajitdb.com/best/best-resin
- Date shown: not shown in the text we read
- Note: Ranked names were read from the static HTML. The shell also includes a loading line.
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Pürblack, Lotus Blooming, Pure Himalayan Shilajit, Essencraft
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://shilajitdb.com/about
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of ShilaSource Himalayan Shilajit Resin (https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin). Quote only lines in product_refs/shilasource-himalayan-shilajit-resin.label.json. Do not add a milligram amount, a mineral count, or a joined serving count. Other shilajit jars and the gummy format are separate products and are not this outreach SKU. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA.

### 7. Shilajit: Benefits, Dosage & Top Picks | Supplement Scored

- Score: 57. Type: roundup. Domain: `supplementscored.com`.
- URL: https://www.supplementscored.com/supplements/shilajit/
- Date shown: Apr 2026
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: PrimaVie, Pure Himalayan Shilajit, Nootropics Depot
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://www.supplementscored.com/about
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of ShilaSource Himalayan Shilajit Resin (https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin). Quote only lines in product_refs/shilasource-himalayan-shilajit-resin.label.json. Do not add a milligram amount, a mineral count, or a joined serving count. Other shilajit jars and the gummy format are separate products and are not this outreach SKU. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA.

### 8. Best Third-Party Tested Shilajit (2026) — Named Lab & COA

- Score: 54. Type: directory. Domain: `shilajitdb.com`.
- URL: https://shilajitdb.com/best/best-third-party-tested
- Date shown: not shown in the text we read
- Note: Ranked names were read from the static HTML. The shell also includes a loading line.
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Pürblack, Lotus Blooming, Pure Himalayan Shilajit, Essencraft, Xara, Sunmed, Novomins
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://shilajitdb.com/about
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of ShilaSource Himalayan Shilajit Resin (https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin). Quote only lines in product_refs/shilasource-himalayan-shilajit-resin.label.json. Do not add a milligram amount, a mineral count, or a joined serving count. Other shilajit jars and the gummy format are separate products and are not this outreach SKU. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA.

### 9. Shilajit Comparison: 240+ Products Ranked Side-by-Side (2026) | ShilajitDB

- Score: 54. Type: directory. Domain: `shilajitdb.com`.
- URL: https://shilajitdb.com/shilajit-comparison
- Date shown: not shown in the text we read
- Note: Ranked names were read from the static HTML. The shell also includes a loading line.
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Lotus Blooming, Pürblack, Life Cykel, Essencraft, Puralis, Pure Himalayan Shilajit
- Wellness Nest / cluster brand: absent
- Editor contact page (public, checked this run): https://shilajitdb.com/about
- Outreach: draft_only. Draft only, do not email or submit a form. Offer one sample of ShilaSource Himalayan Shilajit Resin (https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin). Quote only lines in product_refs/shilasource-himalayan-shilajit-resin.label.json. Do not add a milligram amount, a mineral count, or a joined serving count. Other shilajit jars and the gummy format are separate products and are not this outreach SKU. A roster byline may be quoted only after Kevin names the person. Do not lead with a lab test or a COA.

### 10. Best Shilajit Gummies 2026: Ranked by Fulvic Acid & COA

- Score: 25. Type: brand_roundup. Domain: `yourhealthier.com`.
- URL: https://yourhealthier.com/blogs/blog/best-shilajit-gummies-2026
- Date shown: September 20, 2026
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: YourHealthier, Black Lotus, Root Labs, PrimaVie, Lotus Blooming
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: do_not_pitch. Competitor-owned roundup. The Search Engine Land SOP marks vendor pages do-not-pitch, because the page will not add a rival as the pick.

### 11. 5 Best Shilajit Supplements of 2026 | WOWMD

- Score: 22. Type: brand_roundup. Domain: `wowmd.com`.
- URL: https://www.wowmd.com/blogs/wellness/best-shilajit-supplements
- Date shown: not shown in the text we read
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: WOWMD, PrimaVie, VitaUp, Nootropics Depot, Black Lotus, Double Wood
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: do_not_pitch. Competitor-owned roundup. The Search Engine Land SOP marks vendor pages do-not-pitch, because the page will not add a rival as the pick.

### 12. Best shilajit brands?

- Score: 19. Type: reddit. Domain: `reddit.com`.
- URL: https://www.reddit.com/r/SHILAJIT/comments/1dt4hgq/best_shilajit_brands/
- Date shown: not shown in the text we read
- How found: web search rank. Evidence: web search rank. Basis: search_snippet. `ai_citation_observed: false`.
- Other brands named: Pürblack, Chuga, Natural Shilajit, Organifi, Pure Himalayan Shilajit
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: do_not_pitch. Community thread. Do not pitch. A roster writer may answer the question only if Kevin asks for that reply.

### 13. Best quality Shilajit Supplement Brand?

- Score: 19. Type: reddit. Domain: `reddit.com`.
- URL: https://www.reddit.com/r/Supplements/comments/1bfxn5g/best_qaulity_shilajit_supplement_brand/
- Date shown: not shown in the text we read
- How found: web search rank. Evidence: web search rank. Basis: search_snippet. `ai_citation_observed: false`.
- Other brands named: Pürblack, Lotus Blooming, PrimaVie, Nootropics Depot, Pure Himalayan Shilajit
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: do_not_pitch. Community thread. Do not pitch. A roster writer may answer the question only if Kevin asks for that reply.

### 14. Shilajit Reviews 2026: Real Results + What to Expect

- Score: 17. Type: brand_roundup. Domain: `vitadote.com`.
- URL: https://www.vitadote.com/blog/shilajit-experiences-reviews-expect/
- Date shown: 15 March 2026
- How found: web search rank. Evidence: web search rank. Basis: fetched_body. `ai_citation_observed: false`.
- Other brands named: Vitadote
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: do_not_pitch. Competitor-owned roundup. The Search Engine Land SOP marks vendor pages do-not-pitch, because the page will not add a rival as the pick.

### 15. Finding real shilajit

- Score: 15. Type: reddit. Domain: `reddit.com`.
- URL: https://www.reddit.com/r/Ayurveda/comments/1kv9ocl/finding_real_shilajit/
- Date shown: not shown in the text we read
- How found: web search rank. Evidence: web search rank. Basis: search_snippet. `ai_citation_observed: false`.
- Other brands named: Pürblack, Lotus Blooming
- Wellness Nest / cluster brand: absent
- Editor contact page: none confirmed
- Outreach: do_not_pitch. Community thread. Do not pitch. A roster writer may answer the question only if Kevin asks for that reply.

## Pages that already name us

These are not gaps. Do not paste their numbers into a pitch. Several shilajit reviews add figures that are not on the resin pack file.

- shilasource — https://www.the-best-supplement.com/review/wellness-nest-shilajit — marks: ShilaSource, Wellness Nest — basis: fetched_body
- shilasource — https://shilajitjournal.com/wellness-nest-shilajit-review/ — marks: ShilaSource, Wellness Nest — basis: fetched_body
- shilasource — https://nutrotonic.com/blogs/news/is-wellness-nest-shilajit-legit-effectiveness-actual-customer-reviews — marks: Wellness Nest — basis: fetched_body
- shilasource — https://truescorehub.com/blog/wellness-nest-shilasource-review-2026-is-this-the-purest-himalayan-shilajit-you-can-buy — marks: ShilaSource, Wellness Nest — basis: fetched_body
- shilasource — https://www.trustpilot.com/review/wellnessnest.co — marks: Wellness Nest — basis: search_snippet

## 90-day sequence

This follows the article's three streams (directories, outreach, objections) without pretending we measured retrievals.

### Days 1-30 — lock the facts, still no send

1. Treat this file as the source map. Do not assign a retrieval tier.
2. Write one public HTML fact sheet per product. Use the label file only. Do not put the only copy of a proof in a PDF.
3. Re-check each contact URL in the gap list. Drop any that no longer resolve.
4. Kevin decides whether a sample may ship, and which roster person may be quoted.

### Days 31-60 — draft pitches, highest independent score first

1. Pitch only rows whose outreach action is `draft_only`.
2. Skip `do_not_pitch` (Reddit, competitor-owned roundups, affiliate reviews, review directories).
3. One publication at a time. Use the contact page. Do not harvest personal addresses from an old pitch article.
4. Offer the sample, the label lines, and a roster quote if Kevin named the person. Do not lead with a lab test or a COA.
5. AgeAura pitches name only the NMN + TMG product above.
6. A gummy URL is not a resin pitch. Offer the resin sample on a resin or general shilajit ranking.

### Days 61-90 — remeasure what this script can remeasure

1. Run the fetch again. Compare `us_mentioned` with this file.
2. A new mention on a page we fetched is the result this method can claim.
3. An answer-engine citation still requires someone to observe that engine. This sequence does not do that.
4. Trustpilot already lists Wellness Nest. This run did not census other directories.
5. Pages that already name ShilaSource and add off-label figures are a correction decision, not a gap pitch.

## Needs a Kevin GO

- Sending any email, form, or sample.
- Naming a roster person as the quote.
- Publishing an HTML lab page, or leading a pitch with a COA. The house rule is that a lab test is not the lead advantage. The ShilaSource lab-as-the-pitch angle stays retired.
- A reply on Reddit.
- Asking a site that already names us to change a figure.
- Paying for an AI-visibility tool if a real retrieval ranking is wanted later.

## Rerun

```bash
python3 scripts/offpage_listicle_gap.py --check
python3 scripts/offpage_listicle_gap.py --fetch --report docs/OFFPAGE_LISTICLE_GAP_2026-10-20.md
python3 -m unittest tests/test_offpage_listicle_gap.py
```

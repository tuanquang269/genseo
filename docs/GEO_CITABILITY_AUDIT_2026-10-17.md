# GEO citability audit — live blog posts, 7–17 October 2026

Read-only check of whether recent Wellness Nest articles are easy for ChatGPT search, Claude, Perplexity, Google AI Overviews, and Grok to cite. No Shopify login, no Admin API, no theme edit, no republish.

- **Fetched:** 2026-10-17 11:41 UTC, public HTTPS GET with a browser user agent.
- **Source of URLs:** `PUBLISHED_ARTICLES_TRACKER.csv` rows dated 2026-10-07 through 2026-10-17, cross-checked against `[DONE]` lines in `daily-tickets.md`. `#CA1009-3` is `SKIPPED-DUPLICATE` and is not in this set. `#CA1009-6` is published (tracker + ticket `[x]`) and is included.
- **Count:** 32 articles (the window asked for 30+).
- **Link check:** HEAD, then GET when HEAD was missing, blocked, or an error. Redirects followed up to 6 hops.

## Scoreboard

| Check | Result |
|---|---|
| HTTP 200, self-canonical, no `noindex` | 32/32 |
| Meta description present, 130–165 characters | 32/32 |
| Direct answer in the opening paragraph (48–73 words, on the headline topic) | 32/32 |
| FAQ heading and at least 4 question H3s | 32/32 |
| Body byline: Dr. Marcus Hale → `/pages/dr-marcus-hale` | 32/32 |
| Product URL for the article's product family, and it returns 200 | 32/32 |
| Descriptive image alt on every hero and inline image | 32/32 |
| FAQPage + Person JSON-LD present in the HTML | 32/32 |
| Title tag over 70 characters | **14/32** |
| Only one question-style H2 | **8/32** |
| No primary-source link (study or regulator) | **5/32** |
| Related `/blogs/news/` article link | 31/32 (missing on 1) |
| Two different calendar dates on the page | **22/32** |
| Two Article JSON-LD nodes | **32/32** |
| Hand-written `Published:` line in the body | 3/32 |
| Author name in the theme header (next to the date) | 0/32 |
| Separate reviewer byline | 0/32 |
| Confirmed dead citation (404) | 1 URL |
| Citation 403 from this VM (publisher bot-wall) | 20 URLs on 12 articles |
| Redirect loops, HTTP 429, usage-limit, or on-demand warnings | none |

Opening answers are real. The gaps that keep a page from being quoted are missing sources, a wrong FloraFresh formula on three posts, split dates from two Article nodes, thin question headings, and title tags the theme pushes past ~70 characters.

## Top 5 gaps by impact

### 1. No study or regulator link — 5/32

Four articles have no outbound link at all. A fifth links only to a Flickr photo and a Creative Commons licence. Answer engines that prefer a primary source have nothing on the page to follow.

| Ticket | URL |
|---|---|
| CA1009-10 | https://wellnessnest.co/blogs/news/creatine-gummies-for-beginners-30-days-in-the-us |
| CA1009-5 | https://wellnessnest.co/blogs/news/shilajit-price-cost-per-serving-by-form-us-2026 |
| CA1009-8 | https://wellnessnest.co/blogs/news/where-to-buy-vaginal-probiotics-in-the-us-5-checks-2026 |
| MB1012-2 | https://wellnessnest.co/blogs/news/vaginal-probiotics-for-beginners-what-to-expect-in-the-us |
| CA1009-2 | https://wellnessnest.co/blogs/news/vaginal-probiotic-dosage-how-many-cfu-a-day-us-2026 |

`#CA1009-4` (where to buy NMN) links FDA dockets on regulations.gov. That counts as a regulator source. `#CA1009-1` links USADA and an NCAA banned-substance PDF; one USADA URL is a 404 (gap note below).

**Recommendation for Kevin:** add one real PubMed, NIH, FDA, or DOI link on each of the five URLs above. This run does not edit live articles.

### 2. FloraFresh copy repeats the wrong PDP formula — 3/32

The Supplement Facts label is Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, sweetened with maltitol and isomalt. These three live posts describe the product as 15 billion CFU from four Lactobacillus strains, plus XOS, D-mannose, and sugar-free. That is the live PDP description, which is wrong until a store rewrite. An answer engine will quote it.

| Ticket | URL |
|---|---|
| MB1006-6 | https://wellnessnest.co/blogs/news/probiotics-during-your-period-keep-taking-them-us-2026 |
| MB1008-2 | https://wellnessnest.co/blogs/news/probiotics-and-birth-control-can-you-take-both-us-2026 |
| MB1009-3 | https://wellnessnest.co/blogs/news/best-time-to-take-vaginal-probiotics-6-rules-us-2026 |

`#CA1009-2` names Lactobacillus only as study strains and states FloraFresh's 1 billion CFU label figure beside them. That contrast is not the PDP formula.

`scripts/florafresh_rules.py` already fails a new draft that attaches 15 billion CFU, four Lactobacillus strains, XOS, D-mannose, or sugar-free to FloraFresh. No guard change was required.

**Recommendation for Kevin:** correct those three articles to the label. This run does not republish them.

AgeAura / NMN posts in this set do not mention Urolithin A.

### 3. Two Article nodes, and two calendar dates on 22/32

Every page emits two `Article` nodes:

- The theme emits `Article` + `WebPage` + `Person`. The visible header is a US Pacific calendar date. The `<time datetime>` value is UTC, which is the next calendar day for posts published in the evening Pacific time.
- The publisher appends a second `Article` + `Person` + `ImageObject`, plus `FAQPage`, inside the article body. Its date is often the UTC day.

The two dates in the table below are always exactly one day apart. Three posts also print `Published: October 17, 2026` in the body (`CA1016-1`, `MB1012-3`, `MB1012-4`), which matches the UTC day and disagrees with the theme header.

Google's publication-date guidance is one Article node and the same date in the visible page and in `datePublished` / `dateModified`. Theme JSON-LD is held for Kevin (PR #1). This run does not change the theme or `shopify_publisher.py` schema output.

**Recommendation for Kevin:** choose one Article node and one calendar date (Pacific display and UTC `datetime` need to be the same day, or the visible line needs to say which zone it is). Until that lands, new drafts should not add their own `Published:` line. The gate now fails that line.

The theme header prints the date and does not print the author name. The author is in the body on all 32 pages. There is no separate reviewer. Do not invent one.

### 4. Only one question-style H2 — 8/32

FAQ blocks are in good shape (heading plus at least four questions on every page). Eight articles use numbered steps (`1. Check the label`) and a single question heading, usually a where-to-buy line. A section an answer engine can lift is a question heading with the answer in the next sentences.

Tickets: `CA1009-10`, `CA1009-6`, `CA1009-8`, `MB1007-3`, `MB1008-3`, `MB1009-3`, `MB1009-7`, `MB1012-5`.

Eight opening paragraphs run 63–73 words against a 40–60 word target. All 32 still answer the headline in the first paragraph. That is a length warning, not a missing answer.

### 5. Title tags of 71–76 characters — 14/32

The H1 itself is 40–60 characters. The theme appends ` – Wellness Nest` (~16), so an H1 of 55–60 becomes a title tag of 71–76. The old gate warned only above 65 characters on the H1, so these titles never warned. Snippets truncate in that band.

**Recommendation for Kevin:** shortening a live title is a retitle. These posts are days old. Leave them unless you explicitly want the tags rewritten. New H1s now warn above 50 characters.

### Also fix when you next touch the page

- **Dead citation (1).** `#CA1009-1` links `https://www.usada.org/spirit-of-sport/nutrition/natural-products-derived-from-plants-and-animals/`, which returns 404. The article's other USADA and NCAA links returned 200.
- **Missing related article (1).** `#MB1012-4` https://wellnessnest.co/blogs/news/turkesterone-over-60-5-checks-in-the-us links the Turkesterone product and two collections, and no other `/blogs/news/` article.
- **403s are bot-walls from this VM (20 URLs, 12 articles).** DOI links that resolve to JAMA, Oxford, Wiley, Science, AHA, Diabetes Journals, Taylor & Francis, Physiology, and MDPI, plus Europe PMC and three CDC pages, returned 403 to both HEAD and GET. Four PubMed PMIDs returned 203 and are counted as resolving. Zero redirect loops. These 403s are not treated as dead links in the new gate.

Disease-cure, "FDA-approved", and "guaranteed result" hits in the body are the articles telling readers that a supplement does not treat an infection, that a retailer's "FDA approved" badge is not a drug approval, or that trials do not supply a guaranteed result. They are not product cure claims.

## Per-article table

Title and meta lengths are the live `<title>` and meta description. Primary is the count of distinct study/regulator links (PubMed, NIH, FDA, CDC, WHO, DOI, regulations.gov, Examine, USADA, WADA, Cochrane, BMJ, Lancet, NEJM, JAMA, NHS, EFSA) after a second pass. Dates are the distinct calendar days found in the theme header, `<time datetime>`, body `Published:` line, and Article JSON-LD.

| Ticket | Slug | HTTP | Title | Meta | Answer | Q-H2 | FAQ | Primary | Related | Dates | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| CA1009-1 | `turkesterone-for-athletes-drug-test-guide-us-2026` | 200 | 68 | 130 | 57 | 5 | 7 | 3 | 3 | 2026-10-12 | citation 404 |
| CA1009-10 | `creatine-gummies-for-beginners-30-days-in-the-us` | 200 | 65 | 140 | 60 | 1 | 5 | 0 | 3 | 2026-10-15 / 2026-10-16 | 1 question H2; no primary source; date split |
| CA1009-2 | `vaginal-probiotic-dosage-how-many-cfu-a-day-us-2026` | 200 | 71 | 135 | 64 | 6 | 6 | 0 | 3 | 2026-10-12 | title 71; no primary source |
| CA1009-4 | `where-to-buy-nmn-in-the-us-fda-status-explained-2026` | 200 | 71 | 136 | 54 | 5 | 5 | 2 | 3 | 2026-10-12 | title 71 |
| CA1009-5 | `shilajit-price-cost-per-serving-by-form-us-2026` | 200 | 66 | 150 | 59 | 2 | 4 | 0 | 4 | 2026-10-14 | no primary source |
| CA1009-6 | `where-to-buy-turkesterone-in-the-us-what-to-check-2026` | 200 | 73 | 165 | 59 | 1 | 6 | 1 | 3 | 2026-10-14 | title 73; 1 question H2 |
| CA1009-7 | `nmn-for-seniors-what-2-trials-show-in-the-us-2026` | 200 | 68 | 157 | 56 | 7 | 6 | 2 | 3 | 2026-10-14 | citation 403 bot-wall |
| CA1009-8 | `where-to-buy-vaginal-probiotics-in-the-us-5-checks-2026` | 200 | 74 | 164 | 56 | 1 | 5 | 0 | 3 | 2026-10-15 / 2026-10-16 | title 74; 1 question H2; no primary source; date split |
| CA1009-9 | `shilajit-for-athletes-what-a-trial-found-in-the-us` | 200 | 67 | 132 | 54 | 6 | 5 | 1 | 3 | 2026-10-15 / 2026-10-16 | date split |
| CA1016-1 | `turkesterone-price-5-cost-checks-in-the-us-2026` | 200 | 66 | 151 | 53 | 6 | 6 | 1 | 3 | 2026-10-16 / 2026-10-17 | date split; body Published line |
| MB1006-6 | `probiotics-during-your-period-keep-taking-them-us-2026` | 200 | 74 | 152 | 58 | 4 | 4 | 6 | 4 | 2026-10-06 / 2026-10-07 | title 74; date split; citation 403 bot-wall; FloraFresh PDP formula |
| MB1007-1 | `creatine-gummies-and-hair-loss-what-the-dht-data-shows-us` | 200 | 76 | 141 | 48 | 3 | 5 | 2 | 3 | 2026-10-07 | title 76 |
| MB1007-2 | `nmn-and-resveratrol-what-the-evidence-shows-us-2026` | 200 | 70 | 147 | 60 | 5 | 5 | 7 | 4 | 2026-10-07 | citation 403 bot-wall |
| MB1007-3 | `does-nmn-break-a-fast-6-rules-for-fasting-days-us-2026` | 200 | 73 | 147 | 51 | 1 | 5 | 4 | 3 | 2026-10-07 | title 73; 1 question H2; citation 403 bot-wall |
| MB1007-4 | `creatine-and-caffeine-can-you-take-both-us-2026` | 200 | 67 | 150 | 57 | 7 | 5 | 3 | 4 | 2026-10-07 / 2026-10-08 | date split; citation 403 bot-wall |
| MB1008-1 | `ageaura-nmn-tmg-ingredients-what-each-one-does-us` | 200 | 70 | 144 | 56 | 5 | 5 | 6 | 4 | 2026-10-07 / 2026-10-08 | date split; citation 403 bot-wall |
| MB1008-2 | `probiotics-and-birth-control-can-you-take-both-us-2026` | 200 | 74 | 159 | 72 | 4 | 5 | 4 | 4 | 2026-10-07 / 2026-10-08 | title 74; date split; citation 403 bot-wall; FloraFresh PDP formula |
| MB1008-3 | `turkesterone-and-alcohol-6-things-to-know-us-2026` | 200 | 68 | 142 | 54 | 1 | 5 | 8 | 2 | 2026-10-07 / 2026-10-08 | 1 question H2; date split; citation 403 bot-wall |
| MB1008-4 | `do-creatine-gummies-expire-6-storage-facts-us-2026` | 200 | 69 | 147 | 56 | 2 | 5 | 5 | 2 | 2026-10-07 / 2026-10-08 | date split |
| MB1008-5 | `nmn-and-alcohol-can-you-drink-while-taking-nmn-us` | 200 | 69 | 140 | 56 | 7 | 5 | 5 | 2 | 2026-10-08 / 2026-10-09 | date split |
| MB1009-1 | `creatine-gummies-on-rest-days-keep-taking-them-us-2026` | 200 | 74 | 154 | 63 | 6 | 5 | 4 | 4 | 2026-10-08 / 2026-10-09 | title 74; date split; citation 403 bot-wall |
| MB1009-2 | `how-long-does-turkesterone-take-to-work-us-2026` | 200 | 66 | 146 | 59 | 5 | 5 | 4 | 3 | 2026-10-08 / 2026-10-09 | date split |
| MB1009-3 | `best-time-to-take-vaginal-probiotics-6-rules-us-2026` | 200 | 71 | 152 | 66 | 1 | 5 | 3 | 2 | 2026-10-08 / 2026-10-09 | title 71; 1 question H2; date split; FloraFresh PDP formula |
| MB1009-4 | `nmn-and-exercise-before-or-after-a-workout-us-2026` | 200 | 70 | 145 | 66 | 3 | 5 | 6 | 4 | 2026-10-08 / 2026-10-09 | date split; citation 403 bot-wall |
| MB1009-5 | `creatine-and-alcohol-what-happens-if-you-drink-us-2026` | 200 | 74 | 136 | 60 | 6 | 6 | 1 | 2 | 2026-10-10 / 2026-10-11 | title 74; date split |
| MB1009-7 | `vaginal-probiotics-while-traveling-7-us-rules` | 200 | 62 | 156 | 58 | 1 | 8 | 1 | 2 | 2026-10-12 | 1 question H2 |
| MB1012-1 | `creatine-gummies-for-runners-what-trials-show-us-2026` | 200 | 72 | 151 | 71 | 6 | 5 | 1 | 3 | 2026-10-15 / 2026-10-16 | title 72; date split |
| MB1012-2 | `vaginal-probiotics-for-beginners-what-to-expect-in-the-us` | 200 | 74 | 146 | 73 | 6 | 5 | 0 | 3 | 2026-10-15 / 2026-10-16 | title 74; no primary source; date split |
| MB1012-3 | `creatine-gummies-over-60-trial-findings-in-the-us` | 200 | 66 | 152 | 54 | 4 | 7 | 4 | 3 | 2026-10-16 / 2026-10-17 | date split; body Published line |
| MB1012-4 | `turkesterone-over-60-5-checks-in-the-us` | 200 | 56 | 143 | 71 | 5 | 5 | 4 | 0 | 2026-10-16 / 2026-10-17 | no related article; date split; body Published line |
| MB1012-5 | `shilajit-for-seniors-5-safety-checks-over-60-us-2026` | 200 | 71 | 148 | 54 | 1 | 5 | 3 | 3 | 2026-10-16 / 2026-10-17 | title 71; 1 question H2; date split |
| MB1012-6 | `shilajit-for-fertility-trial-limits-for-the-us` | 200 | 63 | 140 | 59 | 7 | 5 | 3 | 3 | 2026-10-16 / 2026-10-17 | date split; citation 403 bot-wall |

JSON-LD already on the page (report only; theme markup was not changed): `Organization`, theme `Article` + `WebPage` + `Person`, and publisher `Article` + `Person` + `ImageObject` + `FAQPage`.

## What the gate now fails before publish

`scripts/validate_article.py` calls `scripts/geo_citability.py` on the draft:

- At least two question-style H2s, an FAQ heading, and at least three FAQ questions.
- A product URL, a related article URL, and a primary-source link. regulations.gov, Examine, USADA, and WADA count, along with the existing PubMed/NIH/FDA/CDC/WHO/DOI list. `geo_official_lint.py` uses the same host list for its warn-only check.
- Meta description 120–165 characters in `--draft` mode.
- Image alt of at least a short phrase (empty, missing, or `photo` / `image` fails).
- A hand-written `Published: Month D, YYYY` line.
- An affirmative cure, treat, or prevent claim, an `is FDA-approved` claim, `clinically proven`, or `guaranteed results`. A sentence that negates the claim or calls it a medical promise passes.
- Opening paragraph under 30 words, or one that starts with throat-clearing (`In this article…`). Length outside 40–70 words warns.
- Outbound citation 404, 410, hard 5xx, or a redirect loop. HTTP 403, 429, 503, and timeouts warn and do not fail the draft.
- Internal link check now includes the full `/blogs/news/<handle>` URL plus `/pages/` and `/policies/`, not only `/blogs/news`.
- H1 over 50 characters warns, because the theme suffix pushes the title tag past ~70.

Writer instructions in `skills/genseo-auto-publish/SKILL.md` and `skills/genseo-content-writer/SKILL.md` match that gate.

Live articles above are recommendations. They were not edited.

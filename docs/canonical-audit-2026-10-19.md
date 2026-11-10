# Canonical audit — wellnessnest.co, 2026-10-19

Read-only public crawl. HTTP GET only, robots.txt respected, about one request per second. No Shopify Admin API, no theme edit, no republish.

- **Fetched:** 2026-10-19T17:18:28+07:00
- **User-Agent:** `GenSeoCanonicalAudit/1.0 (+https://wellnessnest.co; read-only)`
- **Requests:** 430 (robots skipped: 0)
- **Locale sample:** bg, es-es, sv (of 20 locales in the sitemap index)
- **Source:** Search Engine Land canonicalization guide, 2026-10-16, via the 2026-10-17 SEL digest. The chosen canonical is the URL Google can cite in AI Overviews and AI Mode.

Theme Article JSON-LD is reported and not treated as a GenSeo publish failure. Draft PR #65 (`cursor/geo-delta-audit-6434`) already holds the duplicate-Article note and is awaiting owner GO. This crawl does not change that proposal.

## Counts

| Check | Count |
|---|---:|
| HTML URLs fetched | 372 |
| HTTP 200 | 361 |
| Other HTTP status | 11 |
| rel=canonical matches the fetched URL | 360 |
| rel=canonical disagrees with the fetched URL | 1 |
| HTTP 200 with no rel=canonical | 0 |
| Redirected to a different cleaned URL | 35 |
| Pages with more than one Article node | 106 |
| Article nodes seen | 250 |
| Pages whose Article mainEntityOfPage / url / @id disagrees | 144 |
| …disagreement is in the theme (outside the article body) | 144 |
| …disagreement is in the article body (GenSeo) | 0 |
| Identity value is the homepage | 144 |
| Sitemap page URLs with a query string | 0 |
| Sitemap page URLs under /collections/*/products/* | 0 |
| Distinct parameterised internal links | 31 |
| Distinct /collections/*/products/* internal links | 0 |
| Locale sample URLs fetched | 27 |
| Locale sample canonicalises to itself | 21 |
| Locale sample canonicalises to the default URL | 0 |
| Locale sample canonicalises somewhere else | 0 |
| Locale sample redirected before the canonical was read | 6 |
| Sitemap URLs that returned 404 | 11 |
| Blog atom entries missing from sitemap_articles | 5 |

Fetched by kind: article 144, blog 4, collection 12, home 1, page 186, product 25.

Default sitemap page URLs: article 133, blog 1, collection 6, home 1, page 180, product 19.

## Top issues

1. **Theme Article `mainEntityOfPage` points at the homepage** on 144 pages. The article body GenSeo emits does this on 0 pages. Duplicate Article nodes are on 106 pages (106 articles also have a body Article node; 38 have only the theme node). That theme node is the 2026-10-08 finding and stays with draft PR #65.
2. **rel=canonical disagrees with the URL that answered** on 1 page (trailing-slash-only differences are the same URL). 0 HTTP 200 responses had no canonical. 35 sitemap URLs redirected to a different cleaned URL. 11 sitemap URLs returned 404.
3. **Parameterised internal links:** 31 distinct URLs. **/collections/*/products/*** internal links: 0 distinct URLs. Sitemap page URLs with a query: 0. Sitemap collection-product URLs: 0.
4. **Locale sample** (27 pages): 21 canonicalise to themselves, 0 to the unprefixed default URL, 0 somewhere else, 6 redirected before the canonical tag was read.
5. **5 article URLs are in the blog atom feed and not in `sitemap_articles_1.xml`.** The sitemap file's newest entries can lag a publish. Those URLs were fetched anyway and are in this report.

## rel=canonical disagreements

Locale URLs whose canonical is the unprefixed default page are in Locale sample. They are not in this count. A trailing slash on a non-root path is treated as the same URL.

| Fetched | Canonical | Kind |
|---|---|---|
| https://wellnessnest.co/pages/microplaque-v2 | https://wellnessnest.co/pages/microplaque-clone | page |

## Article identity disagreements

| Page | Scope | Field | Value |
|---|---|---|---|
| https://wellnessnest.co/blogs/news/what-is-shilajit-history-chemical-properties-processing | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/for-how-long-can-we-take-shilajit | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/2-what-is-ayuveda | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/what-is-ayurveda-principles-of-ayurvedic-medicine-and-its-holistic-approach | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/1-introduction-to-shilajit-history-origins-and-cultural-significance-in-ayurveda | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/traditional-uses-of-shilajit-ancient-practices-and-modern-applications-in-ayurveda | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/types-of-shilajit-products-comparison-of-resin-capsules-liquid-drops-and-gummies | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/how-shilajit-is-sourced-sustainable-sourcing-and-quality-control-in-shilajit-production | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/discovering-the-power-of-shilajit-benefits-for-health-wellness-and-vitality | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/mastering-menopause-natural-ways-to-balance-your-hormones-and-boost-vitality | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/shed-the-menopause-pounds-secrets-to-keeping-weight-off-for-good | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/how-fasting-can-support-you-through-menopause-what-you-need-to-know | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/from-stiff-to-strong-overcoming-joint-pain-during-menopause | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/taming-the-storm-managing-emotional-rage-during-menopause | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/shilajit-why-lab-testing-matters | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/shilajit-fulvic-acid-for-better-and-glowing-skin | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/fasted-training-for-weight-loss-might-do-more-harm-than-good | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/dad-bod-to-rad-bod | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/the-dad-bod-explained | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/dad-bod-chronicles | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/intro-menomate-meal-plan | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/menomate-meal-plan-set-1-week-1 | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/menomate-meal-plan-set-1-week-2 | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/menomate-meal-plan-set-1-week-3 | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/menomate-meal-plan-set-1-week-4 | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/the-5-worst-menopause-symptoms | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/seen-us-in-the-news-here-s-the-truth-1 | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/the-menomate-journey-month-2-week-6-how-black-cohosh-can-naturally-balance-your-hormones-and-end-hot-flash-chaos | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/the-menomate-journey-month-2-week-7-how-dim-can-reset-your-hormones-and-stop-the-rollercoaster-for-good | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |
| https://wellnessnest.co/blogs/news/the-menomate-journey-month-2-week-8-how-curry-leaf-can-slow-down-aging-and-give-you-energy-that-lasts-all-day | theme | mainEntityOfPage.@id | https://wellnessnest.co/ |

144 pages have at least one disagreement. The JSON file lists each one. Body-scope rows are GenSeo-controlled. Theme-scope rows need owner GO before a theme edit.

## Parameterised and collection-product links

Sitemap parameterised page URLs:

- none in the default sitemaps or the sampled locale sitemaps

Sitemap `/collections/*/products/*` page URLs:

- none in the default sitemaps or the sampled locale sitemaps

Pure locale-prefix URLs (hreflang and language chrome, with no other defect) are not listed here. The locale sample is where those copies are judged.
Link storage stopped at 40 interesting URLs on 3 pages. A later parameterised link on those pages can be missing from this list.

Article-body links (inside `article-template__content`, before `article-template__back`): 0 parameterised, 0 collection-product. The publish gate only rewrites that slice. `chrome` and `page` rows are the theme or a non-article template.

Internal links seen on fetched pages (parameterised), most widespread first:

- 307 pages (chrome, page): https://wellnessnest.co/pages/100-shilajit?_ab=0&key=1721446208696
- 307 pages (chrome, page): https://wellnessnest.co/pages/about-us?_ab=0&key=1719739323477
- 307 pages (chrome, page): https://wellnessnest.co/pages/lab-test-result?_ab=0&key=1721553369159
- 307 pages (chrome, page): https://wellnessnest.co/pages/review-and-testimonial?_ab=0&key=1721446203502
- 268 pages (chrome, page): https://wellnessnest.co/pages/contact-us?_ab=0&key=1719739279494
- 268 pages (chrome, page): https://wellnessnest.co/pages/manage-my-subscription?_ab=0&key=1721982867650
- 36 pages (page): https://wellnessnest.co/products/premium-himalayan-shilajit-gummies?utm_source=hompage-slider&utm_medium=en&utm_campaign=fusiforce
- 36 pages (page): https://wellnessnest.co/products/premium-himalayan-shilajit-gummies?utm_source=hompage-slider&utm_medium=en&utm_campaign=resin
- 36 pages (page): https://wellnessnest.co/products/premium-himalayan-shilajit-gummies?utm_source=hompage-slider&utm_medium=en&utm_campaign=shilajit-gummies
- 6 pages (page): https://wellnessnest.co/blogs/news/1-introduction-to-shilajit-history-origins-and-cultural-significance-in-ayurveda?_ab=0&key=1717959919454
- 3 pages (page): https://wellnessnest.co/blogs/news/what-is-ayurveda-principles-of-ayurvedic-medicine-and-its-holistic-approach?_ab=0&key=1717959067154
- 3 pages (page): https://wellnessnest.co/products/psgs-h?selling_plan=8989245755
- 2 pages (page): https://wellnessnest.co/blogs/news/1-introduction-to-shilajit-history-origins-and-cultural-significance-in-ayurveda?_ab=0&key=1717959064799
- 2 pages (page): https://wellnessnest.co/products/menomate?selling_plan=9640935739#gsQk86ZiSq
- 1 pages (page): /bg/blogs/news?page=2
- 1 pages (page): /bg/blogs/news?page=23
- 1 pages (page): /bg/blogs/news?page=3
- 1 pages (page): /blogs/news?page=2
- 1 pages (page): /blogs/news?page=23
- 1 pages (page): /blogs/news?page=3
- 1 pages (page): /es-es/blogs/news?page=2
- 1 pages (page): /es-es/blogs/news?page=23
- 1 pages (page): /es-es/blogs/news?page=3
- 1 pages (page): /sv/blogs/news?page=2
- 1 pages (page): /sv/blogs/news?page=23

Internal links seen on fetched pages (`/collections/*/products/*`):

- none

## Locale sample

The index lists 20 locale prefixes. HTML was fetched for at most two products, two collections, two pages, one blog, and two articles from each sampled locale. The other locale sitemap files were not downloaded.

| Locale URL | Canonical | Target |
|---|---|---|
| https://wellnessnest.co/bg/products/pure-shilajit-gold-resin | https://wellnessnest.co/bg/products/pure-shilajit-gold-resin | self |
| https://wellnessnest.co/bg/products/shilajit-shockwave | https://wellnessnest.co/bg/products/shilajit-shockwave | self |
| https://wellnessnest.co/bg/pages/about | https://wellnessnest.co/bg | redirect |
| https://wellnessnest.co/bg/pages/home-page | https://wellnessnest.co/ | redirect |
| https://wellnessnest.co/bg/collections/frontpage | https://wellnessnest.co/bg/collections/frontpage | self |
| https://wellnessnest.co/bg/collections/mens-essential-collection | https://wellnessnest.co/bg/collections/mens-essential-collection | self |
| https://wellnessnest.co/bg/blogs/news | https://wellnessnest.co/bg/blogs/news | self |
| https://wellnessnest.co/bg/blogs/news/what-is-shilajit-history-chemical-properties-processing | https://wellnessnest.co/bg/blogs/news/what-is-shilajit-history-chemical-properties-processing | self |
| https://wellnessnest.co/bg/blogs/news/for-how-long-can-we-take-shilajit | https://wellnessnest.co/bg/blogs/news/for-how-long-can-we-take-shilajit | self |
| https://wellnessnest.co/es-es/products/pure-shilajit-gold-resin | https://wellnessnest.co/es-es/products/pure-shilajit-gold-resin | self |
| https://wellnessnest.co/es-es/products/shilajit-shockwave | https://wellnessnest.co/es-es/products/shilajit-shockwave | self |
| https://wellnessnest.co/es-es/pages/about | https://wellnessnest.co/ | redirect |
| https://wellnessnest.co/es-es/pages/home-page | https://wellnessnest.co/ | redirect |
| https://wellnessnest.co/es-es/collections/frontpage | https://wellnessnest.co/es-es/collections/frontpage | self |
| https://wellnessnest.co/es-es/collections/mens-essential-collection | https://wellnessnest.co/es-es/collections/mens-essential-collection | self |
| https://wellnessnest.co/es-es/blogs/news | https://wellnessnest.co/es-es/blogs/news | self |
| https://wellnessnest.co/es-es/blogs/news/what-is-shilajit-history-chemical-properties-processing | https://wellnessnest.co/es-es/blogs/news/what-is-shilajit-history-chemical-properties-processing | self |
| https://wellnessnest.co/es-es/blogs/news/for-how-long-can-we-take-shilajit | https://wellnessnest.co/es-es/blogs/news/for-how-long-can-we-take-shilajit | self |
| https://wellnessnest.co/sv/products/pure-shilajit-gold-resin | https://wellnessnest.co/sv/products/pure-shilajit-gold-resin | self |
| https://wellnessnest.co/sv/products/shilajit-shockwave | https://wellnessnest.co/sv/products/shilajit-shockwave | self |
| https://wellnessnest.co/sv/pages/about | https://wellnessnest.co/sv | redirect |
| https://wellnessnest.co/sv/pages/home-page | https://wellnessnest.co/sv | redirect |
| https://wellnessnest.co/sv/collections/frontpage | https://wellnessnest.co/sv/collections/frontpage | self |
| https://wellnessnest.co/sv/collections/mens-essential-collection | https://wellnessnest.co/sv/collections/mens-essential-collection | self |
| https://wellnessnest.co/sv/blogs/news | https://wellnessnest.co/sv/blogs/news | self |
| https://wellnessnest.co/sv/blogs/news/what-is-shilajit-history-chemical-properties-processing | https://wellnessnest.co/sv/blogs/news/what-is-shilajit-history-chemical-properties-processing | self |
| https://wellnessnest.co/sv/blogs/news/for-how-long-can-we-take-shilajit | https://wellnessnest.co/sv/blogs/news/for-how-long-can-we-take-shilajit | self |

## Redirects and sitemap 404s

35 sitemap URLs answered at a different cleaned URL. Landing URLs: https://wellnessnest.co/ (32), https://wellnessnest.co/sv/ (2), https://wellnessnest.co/bg/ (1).

- https://wellnessnest.co/pages/about → https://wellnessnest.co/
- https://wellnessnest.co/pages/home-page → https://wellnessnest.co/
- https://wellnessnest.co/pages/products-shilajit → https://wellnessnest.co/
- https://wellnessnest.co/pages/shilajit-vitality-max → https://wellnessnest.co/
- https://wellnessnest.co/pages/tracking → https://wellnessnest.co/
- https://wellnessnest.co/pages/sms-sign-up-page → https://wellnessnest.co/
- https://wellnessnest.co/pages/test → https://wellnessnest.co/
- https://wellnessnest.co/pages/help-center → https://wellnessnest.co/
- https://wellnessnest.co/pages/subscriptiom-management → https://wellnessnest.co/
- https://wellnessnest.co/pages/subscription-management → https://wellnessnest.co/
- https://wellnessnest.co/pages/rewards-program-page-2 → https://wellnessnest.co/
- https://wellnessnest.co/pages/rewards-program-page-3 → https://wellnessnest.co/
- https://wellnessnest.co/pages/lab-certificate → https://wellnessnest.co/
- https://wellnessnest.co/pages/lab-test-spanish → https://wellnessnest.co/
- https://wellnessnest.co/pages/joy-loyalty-page → https://wellnessnest.co/
- https://wellnessnest.co/pages/lab-certificate-fr → https://wellnessnest.co/
- https://wellnessnest.co/pages/lab-certificate-florafresh → https://wellnessnest.co/
- https://wellnessnest.co/pages/lab-certificate-en → https://wellnessnest.co/
- https://wellnessnest.co/pages/lab-certificate-de → https://wellnessnest.co/
- https://wellnessnest.co/pages/lab-certificate-el → https://wellnessnest.co/
- https://wellnessnest.co/pages/lab-certificate-se → https://wellnessnest.co/
- https://wellnessnest.co/pages/lab-certificate-no → https://wellnessnest.co/
- https://wellnessnest.co/pages/lab-certificate-pt → https://wellnessnest.co/
- https://wellnessnest.co/pages/lab-certificate-dk → https://wellnessnest.co/
- https://wellnessnest.co/pages/onyx-test → https://wellnessnest.co/
- https://wellnessnest.co/pages/ingredients_shilajit-gummy → https://wellnessnest.co/
- https://wellnessnest.co/pages/lab-certificate-hu → https://wellnessnest.co/
- https://wellnessnest.co/pages/lab-certificate-hr → https://wellnessnest.co/
- https://wellnessnest.co/pages/lab-certificate-sl → https://wellnessnest.co/
- https://wellnessnest.co/bg/pages/about → https://wellnessnest.co/bg/
- https://wellnessnest.co/bg/pages/home-page → https://wellnessnest.co/
- https://wellnessnest.co/es-es/pages/about → https://wellnessnest.co/
- https://wellnessnest.co/es-es/pages/home-page → https://wellnessnest.co/
- https://wellnessnest.co/sv/pages/about → https://wellnessnest.co/sv/
- https://wellnessnest.co/sv/pages/home-page → https://wellnessnest.co/sv/

Sitemap URLs that returned 404:

- https://wellnessnest.co/pages/rewards-program-page
- https://wellnessnest.co/pages/rewards-program-page-1
- https://wellnessnest.co/pages/lab-certificate-menomate
- https://wellnessnest.co/pages/lab-certificate-it
- https://wellnessnest.co/pages/lab-certificate-pl
- https://wellnessnest.co/pages/lab-certificate-nl
- https://wellnessnest.co/pages/lab-certificate-es
- https://wellnessnest.co/pages/lab-certificate-ro
- https://wellnessnest.co/pages/lab-certificate-bg
- https://wellnessnest.co/pages/lab-certificate-fi
- https://wellnessnest.co/pages/ageaura-listicle

## Atom entries missing from the article sitemap

- https://wellnessnest.co/blogs/news/nmn-price-bottle-vs-serving-cost-in-the-us
- https://wellnessnest.co/blogs/news/vaginal-probiotics-for-fertility-limits-in-the-us
- https://wellnessnest.co/blogs/news/how-to-take-nmn-a-capsule-routine-in-the-us
- https://wellnessnest.co/blogs/news/creatine-gummies-on-an-empty-stomach-us-guide
- https://wellnessnest.co/blogs/news/vaginal-probiotics-over-60-5-checks-in-the-us

## Owner decisions

- Theme Article JSON-LD (`mainEntityOfPage` / a second Article node) is a theme change. Draft PR #65 already covers the duplicate node. Do not ship a second theme patch from this audit.
- Locale copies that canonicalise to themselves are duplicate URLs Google can cite instead of the default page. Pointing them at the default URL is a Shopify markets setting, not a blog-draft fix.
- A parameterised or `/collections/*/products/*` link in the theme chrome (scope `chrome` or `page`) is a theme edit. The publish gate autofixes those only inside article drafts GenSeo writes.
- GenSeo's publisher still does not emit Article `mainEntityOfPage`. The gate fails a value that is not the article URL. It does not invent one before Shopify assigns the handle.
- `/pages/microplaque-v2` returns 200 and its rel=canonical is `/pages/microplaque-clone`. That is a page-level canonical, not a blog draft.
- 35 sitemap URLs redirect to the homepage or a locale root, and 11 sitemap URLs return 404. Taking them out of the sitemap is a pages cleanup, not a publish-gate change.
- The parameterised links in this report (`?_ab=&key=`, homepage slider `utm_`, `?page=`) are theme or page chrome. None were inside an article body.


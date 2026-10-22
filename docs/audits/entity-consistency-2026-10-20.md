# Entity consistency audit — Wellness Nest — 2026-10-20

Search Engine Land, 15 October 2026, [How entity confusion can hurt your brand's AI visibility](https://searchengineland.com/entity-confusion-hurt-ai-visibility-496139): inconsistent brand and product names split a brand into fuzzy entities that AI assistants skip. This audit reads the public wellnessnest.co sitemap (products, pages, blogs, articles) and compares those names with `product_refs/*.label.json` and the publisher's organization name. Nothing on the live store was changed.

## Crawl

- Generated: 2026-10-20T09:18:21+0700
- Sitemap: https://wellnessnest.co/sitemap.xml
- HTTP GETs: 345 (cap 400). Truncated: False.
- HTTP 429 retries: 0. Transport errors: 0.
- Sitemap children in the index: 106. Locale copies skipped (not fetched): 102. Default-locale sitemap files fetched: 4.
- Content URLs selected: 339. Fetched: 339.
- Fetched pages by type: home 1, product 19, page 180, blog 1, article 138.
- Page HTTP status: 200=328, 404=11.
- JSON-LD blocks that failed to parse, pages: 0.
- Scope is the unprefixed English sitemap. Locale copies would repeat the catalog in other languages and would pass the 400 GET cap.
- Marketplace listings were not fetched.
- robots.txt `User-agent: *` Disallow rules honored: 40 (first: /admin, /cart/, /*/cart/, /checkout).

## Recommended canonical names

Use these in newly published GenSeo articles. The map file is `data/entity_canonical_names.json`. It is not applied to the theme or to Shopify titles.

| Entity | Canonical name | Source |
|---|---|---|
| `wellness-nest` | Wellness Nest | scripts/shopify_publisher.py ORG_NAME; scripts/repair_schema.py publisher name |
| `ageaura-pure-nmn-tmg` | AgeAura Pure NMN + TMG NAD+ Complex | scripts/ageaura_rules.py PRODUCT_LABEL; product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json required lines AgeAura, NMN + TMG, NAD + Complex |
| `shilasource-resin` | ShilaSource Himalayan Shilajit Resin | product_refs/shilasource-himalayan-shilajit-resin.label.json required lines ShilaSource, Himalayan, Shilajit, Resin |
| `florafresh-gummies` | FloraFresh Vaginal Probiotics Gummies | Kevin 2026-10-21: 15B CFU of Bacillus coagulans SNZ-1969 per 2 gummies. 15 billion CFU is the same count. 1 billion CFU is retired.; product_refs/florafresh-vaginal-probiotics-gummies.label.json front lines FloraFresh, Vaginal, Probiotic, Gummies |
| `pure-shilajit-gold-resin` | Pure Shilajit Gold Resin | product_refs/pure-shilajit-gold-resin.label.json required line Pure Shilajit Gold Resin |
| `shilajit-shockwave` | Shilajit Shockwave | product_refs/shilajit-shockwave.label.json required lines SHILAJIT, SHOCKWAVE |
| `premium-himalayan-shilajit-gummies` | Premium Himalayan Shilajit Gummies | product_refs/premium-himalayan-shilajit-gummies.label.json required lines PREMIUM HIMALAYAN, SHILAJIT GUMMIES |
| `fusiforce-creatine-gummies` | FusiForce Creatine Monohydrate Gummies | product_refs/fusiforce-creatine-gummies.label.json required lines FusiForce, Creatine, Monohydrate, Gummies |
| `turkesterone-advanced-formula` | Turkesterone Advanced Formula | product_refs/turkesterone-advanced-formula.label.json required lines TURKESTERONE, ADVANCED, FORMULA |
| `shilajit-gummies-single-jar` | Shilajit Gummies Single Jar | Product JSON-LD name on https://wellnessnest.co/products/shilajit-gummies-single-jar, crawl 2026-10-20. No product_refs label file. |
| `shilajit-gummies-two-jar-pack` | Shilajit Gummies Two-Jar Pack | Product JSON-LD name on https://wellnessnest.co/products/shilajit-gummies-two-jar-pack, crawl 2026-10-20. No product_refs label file. |

AgeAura articles name only **AgeAura Pure NMN + TMG NAD+ Complex**. FloraFresh formula, from its Supplement Facts label: **Bacillus coagulans SNZ-1969, 15B CFU per 2 gummies**.

## Live observations

Crawl records below are what the live store returned on 2026-10-20. They were not rewritten. The blog Article author for new posts is Mike Moretti, Co-founder, Wellness Nest (https://wellnessnest.co/pages/mike-moretti — do not create that page). The FloraFresh label count is 15B CFU per 2 gummies. 1 billion CFU is the retired count.

- https://wellnessnest.co/pages/ageaura-av01-dr-hale-f6 — Live observation: Dr. Marcus Hale appears on this live URL. Not the blog Article author.
- https://wellnessnest.co/pages/ageaura-av01-dr-hale-f7 — Live observation: Dr. Marcus Hale appears on this live URL. Not the blog Article author.
- https://wellnessnest.co/pages/dr-marcus-hale — Live observation: Dr. Marcus Hale appears on this live URL. Not the blog Article author.
- https://wellnessnest.co/blogs/news/vaginal-probiotic-dosage-how-many-cfu-a-day-us-2026 — Live observation: this page states the retired count "1 billion CFU". The quote was not rewritten.

## Measured name fields

- `og:site_name`: 1 distinct value(s) across 323 nodes/pages. Wellness Nest (323).
- `Organization.name`: 1 distinct value(s) across 518 nodes/pages. Wellness Nest (518).
- `Organization.logo`: 2 distinct value(s) across 380 nodes/pages. https://wellnessnest.co/cdn/shop/files/WNN_Main_Logo_eb77747f-0bd5-4316-a9ba-92349ddbe5cc.png?v=1769923702&width=500 (274), https://wellnessnest.co/cdn/shop/files/WNN_Main_Logo_eb77747f-0bd5-4316-a9ba-92349ddbe5cc.png (106). Distinct file paths after dropping the query string: 1.
- Store name token in titles, H1s, Open Graph, and schema: wellness nest (1256).

## Findings

### product_name_variants:ageaura-pure-nmn-tmg — 2

ageaura-pure-nmn-tmg product titles, H1s, or Product schema names do not share one loose form. Canonical is 'AgeAura Pure NMN + TMG NAD+ Complex'.

- https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex; field=title; surface=AgeAura Pure NMN + TMG — NAD⁺ Longevity Duo

### product_name_variants:florafresh-gummies — 3

florafresh-gummies product titles, H1s, or Product schema names do not share one loose form. Canonical is 'FloraFresh Vaginal Probiotics Gummies'.

- https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies; field=title; surface=FloraFresh Vaginal Probiotics Gummies | Vaginal Health & pH Support
- https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies; field=h1; surface=Shilajit Gummies Single Jar

### product_name_variants:pure-shilajit-gold-resin — 2

pure-shilajit-gold-resin product titles, H1s, or Product schema names do not share one loose form. Canonical is 'Pure Shilajit Gold Resin'.

- https://wellnessnest.co/products/pure-shilajit-gold-resin; field=Product.name; surface=Himalayan Pure Shilajit Gold Resin
- https://wellnessnest.co/products/pure-shilajit-gold-resin; field=title; surface=Pure Shilajit Gold Resin for Energy & Vitality - High Potency

### product_name_variants:shilajit-shockwave — 2

shilajit-shockwave product titles, H1s, or Product schema names do not share one loose form. Canonical is 'Shilajit Shockwave'.

- https://wellnessnest.co/products/shilajit-shockwave; field=Product.name; surface=Shilajit Shockwave Energy Drops
- https://wellnessnest.co/products/shilajit-shockwave; field=title; surface=Shilajit Energy Drops - Shockwave Formula for Focus & Performance

### product_name_variants:premium-himalayan-shilajit-gummies — 3

premium-himalayan-shilajit-gummies product titles, H1s, or Product schema names do not share one loose form. Canonical is 'Premium Himalayan Shilajit Gummies'.

- https://wellnessnest.co/products/premium-himalayan-shilajit-gummies; field=title; surface=Premium Himalayan Shilajit Gummies | 60 Gummies
- https://wellnessnest.co/products/premium-himalayan-shilajit-gummies; field=h1; surface=Shilajit Gummies Single Jar

### product_name_variants:fusiforce-creatine-gummies — 2

fusiforce-creatine-gummies product titles, H1s, or Product schema names do not share one loose form. Canonical is 'FusiForce Creatine Monohydrate Gummies'.

- https://wellnessnest.co/products/fusiforce-creatine-gummies; field=Product.name; surface=FusiForce - Creatine Monohydrate Gummies 5,000 mg
- https://wellnessnest.co/products/fusiforce-creatine-gummies; field=title; surface=Creatine Gummies for Muscle Growth - 5g Monohydrate | FusiForce

### product_name_variants:turkesterone-advanced-formula — 2

turkesterone-advanced-formula product titles, H1s, or Product schema names do not share one loose form. Canonical is 'Turkesterone Advanced Formula'.

- https://wellnessnest.co/products/turkesterone-advanced-formula; field=title; surface=Turkesterone for Muscle Growth & Strength - Advanced Formula

### product_name_variants:shilajit-gummies-two-jar-pack — 2

shilajit-gummies-two-jar-pack product titles, H1s, or Product schema names do not share one loose form. Canonical is 'Shilajit Gummies Two-Jar Pack'.

- https://wellnessnest.co/products/shilajit-gummies-two-jar-pack; field=h1; surface=Shilajit Gummies Single Jar

### product_brand_not_organization — 2

Product.brand is not the Organization name 'Wellness Nest'.

- https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex; product_name=AgeAura Pure NMN + TMG NAD+ Complex; brand=AgeAura; organization=Wellness Nest
- https://wellnessnest.co/products/ageaura-pure-nmn-tmg-p2; product_name=AgeAura Pure NMN + TMG - Rejuvenation Duo; brand=AgeAura; organization=Wellness Nest

### organization_missing — 54

Page has no Organization JSON-LD (page 53, product 1).

- https://wellnessnest.co/products/ageaura-pure-nmn-tmg-p2; type=product
- https://wellnessnest.co/pages/aa-ltc-01; type=page
- https://wellnessnest.co/pages/adv-ltc01; type=page
- https://wellnessnest.co/pages/advertorial-template; type=page
- https://wellnessnest.co/pages/ageaura-advertorial; type=page

### organization_duplicated — 138

Page has more than one Organization node and the names agree.

- https://wellnessnest.co/blogs/news/1-introduction-to-shilajit-history-origins-and-cultural-significance-in-ayurveda; organization_nodes=2; name=Wellness Nest
- https://wellnessnest.co/blogs/news/2-what-is-ayuveda; organization_nodes=2; name=Wellness Nest
- https://wellnessnest.co/blogs/news/ageaura-nmn-for-men-over-50-what-to-expect-us-2026; organization_nodes=3; name=Wellness Nest
- https://wellnessnest.co/blogs/news/ageaura-nmn-tmg-ingredients-what-each-one-does-us; organization_nodes=3; name=Wellness Nest
- https://wellnessnest.co/blogs/news/barbara-oneill-shilajit-the-videos-are-ai-fakes; organization_nodes=3; name=Wellness Nest

### sameas_missing — 518

Organization.sameAs is missing or every value is blank on 518 Organization nodes across 274 pages.

- https://wellnessnest.co/; sameAs=['', '', '', '', '', '', '', '', '']; name=Wellness Nest
- https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex; sameAs=['', '', '', '', '', '', '', '', '']; name=Wellness Nest
- https://wellnessnest.co/products/florafresh-3-month-reserve; sameAs=['', '', '', '', '', '', '', '', '']; name=Wellness Nest

### h1_disagrees_with_product_name — 12

On 12 product pages the H1 does not match Product.name. 12 of them use the H1 'Shilajit Gummies Single Jar'.

- https://wellnessnest.co/products/florafresh-3-month-reserve; h1=Shilajit Gummies Single Jar; product_name=FloraFresh 3-Month Reserve
- https://wellnessnest.co/products/florafresh-6-month-reserve; h1=Shilajit Gummies Single Jar; product_name=FloraFresh 6-Month Reserve
- https://wellnessnest.co/products/florafresh-single-bottle; h1=Shilajit Gummies Single Jar; product_name=FloraFresh Single Bottle
- https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies; h1=Shilajit Gummies Single Jar; product_name=FloraFresh - Vaginal Probiotics Gummies
- https://wellnessnest.co/products/fusiforce-12-month-reserve; h1=Shilajit Gummies Single Jar; product_name=FusiForce 12-Month Reserve

### h1_empty — 2

Product page has no H1 text.

- https://wellnessnest.co/products/pure-shilajit-gold-resin; product_name=Himalayan Pure Shilajit Gold Resin
- https://wellnessnest.co/products/shilajit-shockwave; product_name=Shilajit Shockwave Energy Drops

### article_jsonld_duplicated — 106

106 of 138 fetched article pages (HTTP 200) have more than one Article JSON-LD node.

- https://wellnessnest.co/blogs/news/ageaura-nmn-for-men-over-50-what-to-expect-us-2026; article_nodes=2
- https://wellnessnest.co/blogs/news/ageaura-nmn-tmg-ingredients-what-each-one-does-us; article_nodes=2
- https://wellnessnest.co/blogs/news/barbara-oneill-shilajit-the-videos-are-ai-fakes; article_nodes=2
- https://wellnessnest.co/blogs/news/best-shilajit-gummies-6-us-labels-compared-2026; article_nodes=2
- https://wellnessnest.co/blogs/news/best-time-to-take-creatine-before-or-after-us-2026; article_nodes=2

### ageaura_outside_catalog — 1

AgeAura product handle is outside the NMN + TMG catalog. New articles stay on AgeAura Pure NMN + TMG NAD+ Complex.

- https://wellnessnest.co/products/ageaura-pure-nmn-tmg-p2; handle=ageaura-pure-nmn-tmg-p2

### sitemap_missing_product — 1

Canonical product handle is not among the product URLs in the default-locale product sitemap.

- https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin; handle=shilasource-himalayan-shilajit-resin; canonical=ShilaSource Himalayan Shilajit Resin

### live_observation — 1

Live observation: the page states 15 billion CFU, the same count as the label. Supplement Facts label: Bacillus coagulans SNZ-1969, 15B CFU per 2 gummies.

- https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies; field=og:description; sentence=Support vaginal health, pH balance, microbiome with Vaginal Probiotics. 15 Billion CFU probiotics, D-Mannose, prebiotics, and Vitamin C for daily feminine care.
- https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies; field=meta description; sentence=Support vaginal health, pH balance, microbiome with Vaginal Probiotics. 15 Billion CFU probiotics, D-Mannose, prebiotics, and Vitamin C for daily feminine care.
- https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies; field=Product.description; sentence=ehensive blend of probiotics, prebiotics, and supportive nutrients. Each serving delivers 15 billion CFU from four clinically studied Lactobacillus strains - Lactobacillus rhamnosus, Lactobacill

### label_contradiction — 1

D-mannose is the rejected PDP formula. Supplement Facts label: Bacillus coagulans SNZ-1969, 15B CFU per 2 gummies.

- https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies; field=og:description; sentence=aginal health, pH balance, microbiome with Vaginal Probiotics. 15 Billion CFU probiotics, D-Mannose, prebiotics, and Vitamin C for daily feminine care.
- https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies; field=meta description; sentence=aginal health, pH balance, microbiome with Vaginal Probiotics. 15 Billion CFU probiotics, D-Mannose, prebiotics, and Vitamin C for daily feminine care.
- https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies; field=Product.description; sentence=and helping maintain the natural balance of vaginal flora. Combined with XOS prebiotics, D-Mannose, and Vitamin C, FloraFresh provides targeted support for women looking to maintain intima

### label_contradiction — 1

Lactobacillus strains are the rejected PDP formula. Supplement Facts label: Bacillus coagulans SNZ-1969, 15B CFU per 2 gummies.

- https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies; field=Product.description; sentence=d supportive nutrients. Each serving delivers 15 billion CFU from four clinically studied Lactobacillus strains - Lactobacillus rhamnosus, Lactobacillus reuteri, Lactobacillus salivarius, and L

### label_contradiction — 1

XOS is the rejected PDP formula. Supplement Facts label: Bacillus coagulans SNZ-1969, 15B CFU per 2 gummies.

- https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies; field=Product.description; sentence=ginal microbiome and helping maintain the natural balance of vaginal flora. Combined with XOS prebiotics, D-Mannose, and Vitamin C, FloraFresh provides targeted support for women look

### label_contradiction — 1

Description states a milligram amount. product_refs/fusiforce-creatine-gummies.label.json has no milligram line.

- https://wellnessnest.co/products/fusiforce-creatine-gummies; field=Product.description; sentence=DescriptionDescriptionDescriptionFusiForce – Creatine Monohydrate Gummies 5,000 mg + Panax Ginseng FusiForce is a next‑generation creatine monohydrate gummy, delivering a f

### label_contradiction — 1

Description states a milligram amount. product_refs/turkesterone-advanced-formula.label.json has no milligram line.

- https://wellnessnest.co/products/turkesterone-advanced-formula; field=Product.description; sentence=rkesterone Advanced Formula stacks 5 synergistic ingredients in doses that actually work: 500 mg Turkesterone (Ajuga Turkestanica) — the anabolic powerhouse that supercharges protein syn

## Product URLs with no canonical-map entry

These handles have no `product_refs/*.label.json` match in the map. Names below are the ones the crawl read.

- `ageaura-pure-nmn-tmg-p2` https://wellnessnest.co/products/ageaura-pure-nmn-tmg-p2 — Product.name ['AgeAura Pure NMN + TMG - Rejuvenation Duo'] — H1 ['AgeAura Pure NMN + TMG - Rejuvenation Duo', 'AgeAura Pure NMN + TMG - Rejuvenation Duo'] — title AgeAura Pure NMN + TMG — NAD⁺ Longevity Duo | Wellness Nest
- `florafresh-3-month-reserve` https://wellnessnest.co/products/florafresh-3-month-reserve — Product.name ['FloraFresh 3-Month Reserve'] — H1 ['Shilajit Gummies Single Jar'] — title FloraFresh 3-Month Reserve – Wellness Nest
- `florafresh-6-month-reserve` https://wellnessnest.co/products/florafresh-6-month-reserve — Product.name ['FloraFresh 6-Month Reserve'] — H1 ['Shilajit Gummies Single Jar'] — title FloraFresh 6-Month Reserve – Wellness Nest
- `florafresh-single-bottle` https://wellnessnest.co/products/florafresh-single-bottle — Product.name ['FloraFresh Single Bottle'] — H1 ['Shilajit Gummies Single Jar'] — title FloraFresh Single Bottle – Wellness Nest
- `fusiforce-12-month-reserve` https://wellnessnest.co/products/fusiforce-12-month-reserve — Product.name ['FusiForce 12-Month Reserve'] — H1 ['Shilajit Gummies Single Jar'] — title FusiForce 12-Month Reserve – Wellness Nest
- `fusiforce-3-month-half-reserve` https://wellnessnest.co/products/fusiforce-3-month-half-reserve — Product.name ['FusiForce 3-Month Half Reserve'] — H1 ['Shilajit Gummies Single Jar'] — title FusiForce 3-Month Half Reserve – Wellness Nest
- `fusiforce-6-month-reserve` https://wellnessnest.co/products/fusiforce-6-month-reserve — Product.name ['FusiForce 6-Month Reserve'] — H1 ['Shilajit Gummies Single Jar'] — title FusiForce 6-Month Reserve – Wellness Nest
- `shilasource-12-month-reserve` https://wellnessnest.co/products/shilasource-12-month-reserve — Product.name ['ShilaSource 12-Month Reserve'] — H1 ['Shilajit Gummies Single Jar'] — title ShilaSource 12-Month Reserve – Wellness Nest
- `shilasource-3-month-reserve` https://wellnessnest.co/products/shilasource-3-month-reserve — Product.name ['ShilaSource 3-Month Reserve'] — H1 ['Shilajit Gummies Single Jar'] — title ShilaSource 3-Month Reserve – Wellness Nest
- `shilasource-6-month-reserve` https://wellnessnest.co/products/shilasource-6-month-reserve — Product.name ['ShilaSource 6-Month Reserve'] — H1 ['Shilajit Gummies Single Jar'] — title ShilaSource 6-Month Reserve – Wellness Nest

## Repo sources of truth

- `scripts/shopify_publisher.py` `ORG_NAME` is `Wellness Nest`.
- Article publisher JSON-LD in `scripts/shopify_publisher.py` sets the organization name and logo and does not set `sameAs`. `scripts/repair_schema.py` matches that shape.
- Non-canonical spellings in publisher, repair, and article/landing templates: 7.
- `scripts/article_images.py:451` WellnessNest — for this SKU, if one exists. Every WellnessNest PDP image is a marketing composite — so
- `scripts/landing_render.py:15` WellnessNest — rtorial` (+ PATI-ADAPTATION.md) and the WellnessNest theme gotchas (`wellnessnest-advertoria
- `templates/landing/page.gsl-ref-advertorial-takeover-v1.liquid:52` WellnessNest — "utility-bar"], [id*="utility-bar"], /* WellnessNest theme: horizontal-ticker = the green "F
- `templates/landing/README.md:20` WellnessNest — orial` (+ `PATI-ADAPTATION.md`) and the WellnessNest theme gotchas (`wellnessnest-advertoria
- `templates/landing/page.genseo-landing-takeover-v1.liquid:52` WellnessNest — "utility-bar"], [id*="utility-bar"], /* WellnessNest theme: horizontal-ticker = the green "F
- `skills/genseo-auto-publish/references/ads-article-mining.md:35` WellnessNest — mcp__google-ads__*`). `list_accounts` → WellnessNest = `7385813335`. Run queries with `run_g
- `skills/genseo-auto-publish/references/ugc-image-framework.md:139` WellnessNest — ree). - **Never pass `:index`.** Every WellnessNest PDP "image" is a marketing composite; s

## Fixes that need Kevin's GO

This pass does not edit the theme, product titles, schema on the live site, social profiles, or marketplaces.

- Theme / Organization schema: fill `sameAs` with profiles Kevin confirms, and remove empty strings. A duplicated Organization node (theme header plus article publisher) needs a theme or app decision before anyone deletes a block.
- GemPages / product templates: an H1 that names a different product is a template binding. Changing it is a theme edit.
- Shopify product SEO titles and Product.brand: retitling a live product, or switching Product.brand between the line name and Wellness Nest, needs a store edit. AgeAura's brand field is the line name today; whether that should match the store Organization is Kevin's call.
- FloraFresh PDP strain story (Lactobacillus, XOS, D-mannose, sugar-free) stays until Kevin approves a PDP rewrite. The label count is 15B CFU per 2 gummies (Kevin 2026-10-21). 15 billion CFU on the PDP is that same count and is a live observation. 1 billion CFU is retired.
- Blog Article author for new posts is Mike Moretti, Co-founder, Wellness Nest. https://wellnessnest.co/pages/mike-moretti is not created from this repo. Live pages that still name Dr. Marcus Hale stay crawl observations.
- Social profiles: this crawl found no non-empty `sameAs` URLs to check. Do not invent profile URLs.
- Marketplaces: not in this crawl. Do not change Amazon or other marketplace titles from this report.
- AgeAura handles outside `ageaura-pure-nmn-tmg-nad-complex` stay off new articles. Unpublishing a live product is a separate GO.
- Live handle `ageaura-pure-nmn-tmg-p2` (https://wellnessnest.co/products/ageaura-pure-nmn-tmg-p2) uses Product.name ['AgeAura Pure NMN + TMG - Rejuvenation Duo']. Do not copy that name into articles. Retitling or unpublishing it needs Kevin's GO.
- Product sitemap does not list `shilasource-himalayan-shilajit-resin`. Changing sitemap inclusion needs Kevin's GO.

## What this repo change does

`validate_article.py` warns, and still passes, when a draft uses a non-canonical spelling from the map (`WellnessNest`, `Wellness-Nest`, `Longevity Duo`, split `Age Aura` / `Shila Source` / `Flora Fresh` / `Fusi Force`). The warning is not a publish failure.

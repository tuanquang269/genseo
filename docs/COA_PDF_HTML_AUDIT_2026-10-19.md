# COA PDF vs HTML audit (2026-10-19)

Read-only check of wellnessnest.co for PDF certificates of analysis and lab sheets, and whether the same proof is already in crawlable HTML. No store writes, no theme edits, no publish. Assay numbers were not read out of any image or PDF. Where a value was not read, this file says UNKNOWN.

Checked at `2026-10-19T16:20:13Z` with `python3 scripts/coa_pdf_html_check.py`.

## Result

Wellness Nest’s own Files library has **zero PDFs**. The public crawl found **zero Wellness Nest PDF COAs**.

Ten PDFs are linked from the store. Nine are third-party citations. One is a clinical PDF on a different Shopify shop, linked from `/pages/charlesanderson`. None of the ten has a nominated HTML equivalent on wellnessnest.co.

| Classification | Count | What it means here |
|---|---:|---|
| HAS_HTML_EQUIVALENT | 0 | No PDF has a live wellnessnest.co HTML page that carries batch/lot text plus ppm, heavy metal, or “certificate of analysis” |
| PDF_ONLY | 7 | The URL returns a PDF, and no such HTML page was nominated |
| GATED | 1 | ResearchGate returned a security-check page |
| DEAD_LINK | 1 | HTTP 404 |
| UNKNOWN | 1 | The host did not answer |

Proof that does exist on the store is **raster images** (PNG, JPEG, WEBP). Eleven of those are in the seed. One image URL returns HTTP 404. The images were not OCR’d, so every analyte value is UNKNOWN.

## What was fetched

- English sitemaps: 180 pages, 20 product URLs, 138 articles, plus the homepage, four policy URLs, `/llms.txt`, and `/agents.md`. 346 requests. 302 returned HTTP 200, 33 returned HTTP 429, 11 returned HTTP 404.
- The 33 rate-limited URLs are listed in `data/coa_pdf_html_rate_limited_2026-10-19.txt`. Their HTML was not read.
- `products.json` and `pages.json` bodies were searched for `.pdf`. None.
- A separate GET of `/products/shilasource-himalayan-shilajit-resin` (HTTP 200; that handle was not in the 20-URL product sitemap) found no PDF.
- Read-only Admin GraphQL `files` query: `filename:*.pdf` returned 0 nodes. A scan of 152 `GENERIC_FILE` objects found no `application/pdf`.
- Repo search of tracked source found no Wellness Nest COA PDF URL. An untracked FloraFresh claims note cites an unrelated psychology-paper PDF. That file is not a store COA.

HTTP 404 among lab URLs (the page is not public): `lab-certificate-bg`, `lab-certificate-es`, `lab-certificate-fi`, `lab-certificate-it`, `lab-certificate-nl`, `lab-certificate-pl`, `lab-certificate-ro`, `lab-certificate-menomate`.

## PDF inventory

`HAS_HTML_EQUIVALENT` is strict. A page that only links the PDF does not count. The seed nominates no HTML equivalent for these ten URLs. The checker does not copy numbers out of the PDF.

| Role | Class | HTTP | Type | Bytes | Linked from | Product |
|---|---|---:|---|---:|---|---|
| citation | DEAD_LINK | 404 | text/html | UNKNOWN | `/blogs/news/what-is-shilajit-history-chemical-properties-processing` | UNKNOWN |
| citation | UNKNOWN | none | UNKNOWN | UNKNOWN | same article | UNKNOWN |
| citation | GATED | 403 | text/html | 23761 | same article | UNKNOWN |
| citation | PDF_ONLY | 206 | application/pdf | 386173 | same article | UNKNOWN |
| citation | PDF_ONLY | 206 | application/pdf | 290650 | `/blogs/news/2-what-is-ayuveda` | UNKNOWN |
| citation | PDF_ONLY | 206 | application/pdf | 287190 | `/pages/shilasource-post-hysterectomy-libido-women` | UNKNOWN |
| citation | PDF_ONLY | 206 | application/pdf | 764689 | `/blogs/news/probiotics-after-antibiotics-for-women-when-to-start-us` | UNKNOWN |
| citation | PDF_ONLY | 200 | application/pdf | 140898 | `/blogs/news/from-stiff-to-strong-overcoming-joint-pain-during-menopause-1` | UNKNOWN |
| citation | PDF_ONLY | 206 | application/pdf | 102414 | `/blogs/news/taming-the-storm-managing-emotional-rage-during-menopause` | UNKNOWN |
| off-store clinical PDF | PDF_ONLY | 206 | application/pdf | 282677 | `/pages/charlesanderson` | UNKNOWN |

URLs, in the same order:

1. `http://therdsf.org/wp-content/uploads/2014/06/shilijitNEW-1.pdf` — DEAD_LINK
2. `http://www.ccras.nic.in/sites/default/files/viewpdf/jimh/JIMH_2010/13%20to%2024.pdf` — UNKNOWN after two attempts (timeout)
3. ResearchGate PDF for the Gupta shilajit paper — HTTP 403, visible text “Security check required”
4. `https://www.shd.org.rs/JSCS/Vol75/No3/14_4376_3974.pdf`
5. `https://globalresearchonline.net/journalcontents/v59-1/23.pdf`
6. `https://interscience.org.uk/images/article/v15-i4/3ijahm.pdf`
7. `https://isappscience.org/wp-content/uploads/2024/12/ISAPP-Clinician-resource-probiotic-use-alongside-antibiotics.pdf`
8. `https://www.aaos.org/contentassets/1cd7f41417ec4dd4b5c4c48532183b96/1184-the-impact-of-obesity-on-bone-and-joint-health1.pdf`
9. `https://www.womens-health-concern.org/wp-content/uploads/2023/07/28-WHC-FACTSHEET-Nutrition-in-Menopause-JULY2023-A.pdf` redirects to `.../2026/09/28-NEW-WHC-FACTSHEET-Nutrition-in-Menopause-SEPT2026-A.pdf`, which is still a PDF
10. `https://cdn.shopify.com/s/files/1/0742/9102/0008/files/MAGNALI_FUEL_-_CLINICAL_EVIDENCE.pdf?v=1762315274` — shop id `0742/9102/0008`, not Wellness Nest files (`0810/1563/6283`)

These ten do not need a Wellness Nest COA page. They are citations, plus one advertorial PDF that is not a house-brand certificate.

## Raster lab sheets

Filename, image-header width and height (read 2026-10-19, not an assay), and the checker’s HTTP result. `page_json` is the Storefront Ajax document (`/pages/<handle>.json`). Marker names are English words only: batch/lot, ppm, heavy metal, certificate of analysis. The checker does not print the numbers it saw.

| File | Header | HTTP | Bytes | HTML page markers | Page JSON markers | Product |
|---|---|---:|---:|---|---|---|
| `2503-Batch1000pcs-Commercial_Lab_Test_Shilajit_Gold.png` | 2916×3654 | 200 | 701474 | none | ppm, heavy_metal | UNKNOWN |
| `2503-Batch1000pcs-Eurofins_Test_Shilajit_Gold_1.png` | 595×841 | 200 | 145671 | none | ppm | UNKNOWN |
| `Eurofin_Lab_Test.png` | 800×1847 | 206 | 582237 | not nominated | — | fusiforce-creatine-gummies |
| `Creatine_Gummies_Lab_Test.jpg` | 740×400 | 200 | 98461 | not nominated | — | UNKNOWN |
| `Shilajit_labtest.webp` | 537×1024 | 200 | 87972 | not nominated | — | UNKNOWN |
| `20250625-144427.jpg` | 1260×1222 | 200 | 125508 | none | none | florafresh-vaginal-probiotics-gummies |
| `gempages_…8567b1e6….png` | 2404×914 | 200 | 55755 | batch | none | UNKNOWN |
| `gempages_…e79a0ef9….png` | 1080×1892 | 200 | 38424 | batch | none | UNKNOWN |
| `gempages_…12126c61….png` | UNKNOWN | 404 | UNKNOWN | batch (page still live) | none | UNKNOWN |
| `CERTIFICATE_4537ce94-….png` | 1500×1500 | 206 | 554277 | not nominated | — | pure-shilajit-gold-resin |
| `mnm_en_lab.webp` | 1520×1521 | 200 | 733525 | not nominated | — | UNKNOWN |

Linked-from counts are in `data/coa_pdf_html_seed.json`.

### HTML versus the Ajax body

`/pages/lab-certificate-en`, `/pages/lab-certificate-florafresh`, and `/pages/lab-test-spanish` each returned an HTML document of 448111 bytes. That HTML does not contain the lab PNG filename or the proof prose. The same prose is in `page.body_html` on the `.json` URL:

- English JSON says the report below shows heavy metal levels in ppm, and that the shilajit “contains less than 1 ppm or ND (not detected)”. That sentence is the page’s copy. This audit did not read the PNG, so the per-metal table is UNKNOWN. The sentence does not name a current SKU handle.
- Spanish JSON discusses heavy metals (“metales pesados”) and ppm. The checker’s English marker list only recorded `ppm`.
- FloraFresh JSON is marketing copy. It repeats formula figures that `docs/FLORAFRESH_FORMULA_GUARD.md` rejects. Those figures were not copied into the seed or this table. The JPEG was not read.

`/pages/lab-test-result` is different. Its HTML includes crawlable lines: Pure Himalayan Shilajit Resin, batch AHS2401, report AIR-24-IR-052483-01, dated June 5, 2024. The page says this document does not verify gummies or every current resin lot, and it points readers to support@wellnessnest.co for a lot match. The assay table is the images. One of the three GemPages image URLs is HTTP 404. The page’s own `.json` body is the GemPages placeholder, so the JSON markers are empty while the HTML has `batch`.

`1760426351-eurofins.webp` is a 656×140 banner linked from many product and listicle pages, including the ShilaSource resin PDP. It is a badge, not a lab sheet, and it is not in the seed.

Admin files whose names contain `Lab_Test`, `Eurofins_Test`, or `COA` and that this crawl did **not** find in public HTML include `1308-Batch24000pcs-Commercial_Lab_Test_Shilajit_Gold.png`, `0506-Batch4000pcs-Commercial_Lab_Test_Shilajit_Gold.png`, `1308-Batch24000pcs-Eurofins_Test_Shilajit_Gold.png`, `0506-Batch4000pcs-Eurofins_Test_Shilajit_Gold.png`, `image_COA.png`, `image_COA.webp`, `lab.webp`, and `lab_test.avif`. Link status for those filenames: not found on the crawled HTML. Contents UNKNOWN.

## House products

| Product | PDF COA | What the public pages do |
|---|---|---|
| AgeAura Pure NMN + TMG (`ageaura-pure-nmn-tmg-nad-complex`) | none found | PDP links the shared nav item `/pages/lab-test-result`. That page’s own text is about one resin batch. No AgeAura lab image was found. |
| ShilaSource resin | none found | PDP links the eurofins badge and `/pages/lab-test-result`. The HTML there names batch AHS2401 and the report id above. The table is an image. |
| FloraFresh | none found | `/pages/lab-certificate-florafresh` HTML does not include the JPEG or the JSON marketing copy. The JSON copy conflicts with the Supplement Facts label guard. |
| FusiForce creatine gummies | none found | PDP links `Eurofin_Lab_Test.png` (800×1847). No HTML assay table was nominated. |
| Premium Himalayan shilajit gummies | none found | PDP links the eurofins badge. `Shilajit_labtest.webp` is on the gummies PDP and on 27 listicle pages. Pixels UNKNOWN. `/pages/lab-test-result` says it does not verify gummies. |
| Pure Shilajit Gold Resin | none found | PDP links `CERTIFICATE_4537ce94-….png` (1500×1500). Pixels UNKNOWN. No HTML assay table was nominated. |
| Shilajit Shockwave | none found | Nav link to `/pages/lab-test-result` only. |
| Turkesterone Advanced | none found | Nav link to `/pages/lab-test-result` only. |
| MenoMate | none found | `mnm_en_lab.webp` is on four MenoMate pages. MenoMate is not a current for-sale SKU. Pixels UNKNOWN. |

## Re-run

```bash
python3 scripts/coa_pdf_html_check.py
python3 scripts/coa_pdf_html_check.py --json /tmp/coa-pdf-html.json
python3 scripts/coa_pdf_html_check.py --crawl --max-pages 40
python3 scripts/coa_pdf_html_check.py --urls data/coa_pdf_html_rate_limited_2026-10-19.txt --max-pages 40
python3 scripts/coa_pdf_html_check.py --no-network
```

The script only GETs public URLs. It does not upload or publish. `--no-network` classifies every PDF as UNKNOWN and is what the test suite runs. A PDF becomes `HAS_HTML_EQUIVALENT` only when the seed’s `html_equivalent_url` is a live wellnessnest.co HTML page whose visible text has a batch or lot word and one of ppm, heavy metal, or “certificate of analysis”. Page JSON markers are reported on raster rows and do not promote a PDF into that class.

## Recommendations for Kevin

No live change was made. These are decisions, not a queue the agent will run.

1. There is no Wellness Nest PDF COA to noindex. Adding a PDF as the only copy of a lab sheet would leave the same gap this audit was opened to find.
2. Crawlable proof, if you want it, is an HTML page per current SKU whose words you have checked against a report you accept. This audit cannot supply the analyte table. AgeAura still has no COA file in this inventory; do not invent one.
3. `/pages/lab-certificate-en` and the Spanish lab page: the heavy-metal sentence lives in the page JSON, and the HTML response that a crawler fetches does not include it or the PNG. Putting an approved sentence into the HTML is the change that makes it crawlable. The PNG table stays UNKNOWN until someone reads it.
4. `/pages/lab-test-result` already has batch, report id, and date in HTML, and it already limits itself to one resin batch. One embedded image URL returns 404 (`gempages_…12126c61….png`). A text table on that page still needs a source you accept. The page is not evidence for gummies, Gold Resin, Shockwave, Turkesterone, AgeAura, or FloraFresh.
5. FloraFresh `/pages/lab-certificate-florafresh` is a public page. Treat it as marketing, not as a certificate. The JSON repeats the PDP formula the label guard rejects. Any rewrite needs your GO. The JPEG was not read.
6. Gold Resin `CERTIFICATE_….png` and FusiForce `Eurofin_Lab_Test.png` have no HTML assay text. An HTML page for either one needs you to read the image first.
7. The citation PDFs and the Magnali Fuel PDF do not need a house COA page. The therdsf.org link is a 404. ResearchGate is behind a security check. The CCRAS host did not answer. The Women’s Health Concern link now redirects to a newer PDF. Cleanup of those citations is separate from COA HTML.
8. After the store stops returning 429, re-check the 33 URLs in `data/coa_pdf_html_rate_limited_2026-10-19.txt` with the command above.

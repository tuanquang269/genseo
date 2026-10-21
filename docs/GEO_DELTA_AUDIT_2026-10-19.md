# GEO citability delta — articles published after the 17 October gate

Read-only check of whether the citability gate that landed on 17 October (`scripts/validate_article.py` → `scripts/geo_citability.py`, commit `ebda307`, 2026-10-17 11:54 UTC) actually lifted the weak metrics from `docs/GEO_CITABILITY_AUDIT_2026-10-17.md`. Public HTTPS GET only. No Shopify login, no Admin API, no theme edit, no republish, and no edit to a live post.

## Which posts

The gate is in the publisher path for everything published after 2026-10-17 11:54 UTC. The 17 October audit already scored `#CA1016-1`. The next live articles are the ten below.

`PUBLISHED_ARTICLES_TRACKER.csv` on `main` has `#CA1016-2` through `#CA1016-6` dated 2026-10-18, matching `[DONE 2026-10-18]` lines. `#CA1016-7` through `#CA1016-11` are live and recorded on their publish commits (`1a93376`, `ab96d55`, `685dab3`, `2ed33f1`, `ab8d5e8`): each commit adds a tracker row and a `[DONE 2026-10-19]` line. Those commits are not on `main` yet, so the working copy of `daily-tickets.md` still shows them open. This run did not edit that file. The public Atom feed lists the same ten URLs as the newest posts (published_at the evening of 17 October and 18 October, US Pacific, which is 18 October and 19 October UTC).

| Ticket | URL | Tracker date |
|---|---|---|
| CA1016-2 | https://wellnessnest.co/blogs/news/shilajit-on-an-empty-stomach-yes-or-no-in-the-us | 2026-10-18 |
| CA1016-3 | https://wellnessnest.co/blogs/news/vaginal-probiotics-price-us-cost-2026 | 2026-10-18 |
| CA1016-4 | https://wellnessnest.co/blogs/news/turkesterone-for-fertility-the-us-evidence-2026 | 2026-10-18 |
| CA1016-5 | https://wellnessnest.co/blogs/news/creatine-gummies-price-69-99-in-the-us-2026 | 2026-10-18 |
| CA1016-6 | https://wellnessnest.co/blogs/news/nmn-for-fertility-human-evidence-in-the-us-2026 | 2026-10-18 |
| CA1016-7 | https://wellnessnest.co/blogs/news/vaginal-probiotics-over-60-5-checks-in-the-us | 2026-10-19 |
| CA1016-8 | https://wellnessnest.co/blogs/news/creatine-gummies-on-an-empty-stomach-us-guide | 2026-10-19 |
| CA1016-9 | https://wellnessnest.co/blogs/news/how-to-take-nmn-a-capsule-routine-in-the-us | 2026-10-19 |
| CA1016-10 | https://wellnessnest.co/blogs/news/vaginal-probiotics-for-fertility-limits-in-the-us | 2026-10-19 |
| CA1016-11 | https://wellnessnest.co/blogs/news/nmn-price-bottle-vs-serving-cost-in-the-us | 2026-10-19 |

Each of the ten drafts logged `PASS` in `validate_runs.log` before publish (2026-10-18 10:55 through 2026-10-19 10:09, local time). QRG scoring was skipped on all ten because the claude-seo runtime is not installed. That skip is already in the tracker notes. It is not a citability-rule miss.

Fetched 2026-10-19, public HTTPS GET, browser user agent. Article body is the `itemprop="articleBody"` region. Title and meta lengths are the visible `<title>` and meta description after HTML unescape. Question H2s use the gate's own rule (a heading that starts with What/How/Does… or ends in `?`, excluding the FAQ heading). Primary sources use the same host list as `geo_citability.py`.

## Did the gate lift the weak metrics?

Yes for every metric the gate can enforce on the draft. No for the theme date and the second Article node.

| Check | 7–17 Oct (32) | 18–19 Oct (10) |
|---|---:|---:|
| HTTP 200, self-canonical, no `noindex` | 32/32 | 10/10 |
| Meta description 130–165 characters | 32/32 | 10/10 |
| Opening answer 40–70 words | 32/32 in the audit's "answers the headline" band | 10/10 |
| FAQ heading and at least 4 questions | 32/32 | 10/10 |
| Body byline Mike Moretti, Co-founder, Wellness Nest → `/pages/mike-moretti` | 0/32 (fetched bodies still name Dr. Marcus Hale) | 0/10 (fetched bodies still name Dr. Marcus Hale) |
| Product URL present | 32/32 | 10/10 |
| Descriptive image alt | 32/32 | 10/10 |
| FAQPage + Person JSON-LD | 32/32 | 10/10 |
| Title tag over 70 characters | **14/32** | **0/10** |
| Only one question-style H2 | **8/32** | **0/10** |
| No primary-source link | **5/32** | **0/10** |
| No related `/blogs/news/` article | **1/32** | **0/10** |
| Hand-written `Published:` line | **3/32** | **0/10** |
| H1 over 50 characters (gate warning, not a fail) | 24/32 | **0/10** |
| Two calendar dates | **22/32** | **10/10** |
| Two Article JSON-LD nodes | **32/32** | **10/10** |
| Author name in the theme header | 0/32 | 0/10 |
| Separate reviewer byline | 0/32 | 0/10 |
| Confirmed dead citation (404) | 1 URL | none |
| Citation 403 from this machine (bot-wall) | 20 URLs on 12 articles | 5 URLs on 4 articles |
| `geo_citability.assess` hard fail on the live body | 14/32 (they predate the gate) | **0/10** |

The byline row uses Kevin's 2026-10-21 rule: Mike Moretti, Co-founder, Wellness Nest, linking `/pages/mike-moretti`. On the 2026-10-19 fetch every sampled body still named Dr. Marcus Hale and linked `/pages/dr-marcus-hale`. That page was live. `/pages/mike-moretti` is not, so this audit does not rewrite the live bylines. The other rows are unchanged observations from that fetch.

Question H2s on the new posts are real questions (`What does the evidence say…?`, `Can you take creatine without food?`), not statement headings that merely start with "What". Primary links resolve: PubMed returned 203, PMC and FDA and NCCIH and NHS returned 200. The 403s are Europe PMC search URLs, two CDC pages, and one Oxford University Press article. The gate warns on 403 and does not fail the draft. None of those URLs is a 404. FloraFresh copy on `#CA1016-3`, `#CA1016-7`, and `#CA1016-10` does not trip `florafresh_rules.py`.

No post in this set passed the gate and then missed a hard gate rule. There is no slipped-publish bug to fix.

## Gate bug that was fixed

Rescoring the 17 October pages with the current gate flagged two educational sentences the audit said were not product claims:

- `#CA1009-2`: "Neither registry entry proves that a product with the same number will prevent, treat, or cure an infection."
- `#CA1009-8`: "Be cautious with claims that promise to cure an infection, replace clinical care, or guarantee a change in odor, discharge, pain, or pH."

`neither` / `nor` were not treated as negation, and a caution about "claims that promise to cure" was scored as the cure claim itself. Both posts were published before the gate, so this did not let a bad article out. It would block a new draft that uses the wording the audit kept. `scripts/geo_citability.py` now treats `neither` / `nor` as negation and skips a sentence that says "be cautious with claims" or "claims that promise to cure". "We promise to cure an infection" still fails. Covered in `tests/test_geo_citability.py`. The live sentences were not rewritten.

## Theme change, not applied

Every one of the ten pages still emits two `Article` nodes and two calendar dates, one day apart:

- The theme prints a US Pacific date in the header (`October 17, 2026`) and a UTC `datetime` on `<time>` (`2026-10-18T03:56:56Z`) for an article published the evening of 17 October Pacific. The same one-day split is on the 19 October UTC batch (header 18 October, UTC datetime 19 October).
- `scripts/shopify_publisher.py` appends a second `Article` in the body with `datePublished` set from `datetime.utcnow()`.

Proposed change, held for Kevin, same posture as the 17 October audit:

1. Keep one `Article` node. Stop appending the publisher's body `Article`, and keep the theme node, or the reverse. Not both.
2. Render the visible date and the `datetime` value in `America/Los_Angeles` so they are the same calendar day. Do not use a naive UTC clock for the date readers see.
3. Do not add a hand-written `Published:` line. The gate already fails that, and none of the ten new posts have one.
4. The theme header still does not print the author. The body byline is on all ten pages. Putting the name next to the date is a theme edit. Do not invent a reviewer.

This run does not change the theme or `shopify_publisher.py`.

## Per-article table

Dates are the distinct calendar days in the theme header, `<time datetime>`, and Article JSON-LD. Notes call out 403 bot-walls only. Nothing else in the gate's hard rules missed.

| Ticket | HTTP | Title | Meta | Answer | Q-H2 | FAQ | Primary | Related | Dates | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| CA1016-2 | 200 | 66 | 147 | 52 | 7 | 5 | 1 | 2 | 2026-10-17 / 2026-10-18 | Europe PMC 403; date split; two Article nodes |
| CA1016-3 | 200 | 56 | 141 | 64 | 5 | 8 | 2 | 3 | 2026-10-17 / 2026-10-18 | CDC 403; date split; two Article nodes |
| CA1016-4 | 200 | 66 | 153 | 53 | 5 | 5 | 3 | 2 | 2026-10-17 / 2026-10-18 | Europe PMC and CDC 403; date split; two Article nodes |
| CA1016-5 | 200 | 63 | 146 | 55 | 7 | 5 | 1 | 3 | 2026-10-17 / 2026-10-18 | date split; two Article nodes |
| CA1016-6 | 200 | 66 | 154 | 52 | 6 | 5 | 5 | 2 | 2026-10-17 / 2026-10-18 | Oxford 403; date split; two Article nodes |
| CA1016-7 | 200 | 62 | 149 | 57 | 3 | 5 | 4 | 2 | 2026-10-18 / 2026-10-19 | date split; two Article nodes |
| CA1016-8 | 200 | 62 | 147 | 55 | 5 | 4 | 2 | 3 | 2026-10-18 / 2026-10-19 | date split; two Article nodes |
| CA1016-9 | 200 | 60 | 149 | 53 | 4 | 4 | 2 | 3 | 2026-10-18 / 2026-10-19 | date split; two Article nodes |
| CA1016-10 | 200 | 66 | 146 | 53 | 6 | 4 | 4 | 2 | 2026-10-18 / 2026-10-19 | date split; two Article nodes |
| CA1016-11 | 200 | 59 | 151 | 50 | 6 | 5 | 1 | 3 | 2026-10-18 / 2026-10-19 | date split; two Article nodes |

## Ready-to-apply fixes for the 17 October set

No new miss in the ten posts above needs a content fix. The file `docs/geo-live-fixes-2026-10-19.json` prepares edits for **22 of the 32** audited posts. The other **10** only have the theme date / second Article node, so they have no body or title edit.

`scripts/apply_geo_live_fixes.py` fetches the live page, checks each snippet still occurs the expected number of times, and prints a unified diff of the article body plus a title diff when the title changes. It does not call Shopify. Two snippets (`#CA1009-10` loading sentence, `#MB1012-4` recommendation sentence) also appear inside an FAQ JSON-LD string. Those links use single-quoted `href` attributes so the same replacement stays valid HTML and valid JSON. The dry run rejects a patch that leaves a JSON-LD block unparseable.

```bash
python3 scripts/apply_geo_live_fixes.py
python3 scripts/apply_geo_live_fixes.py --ticket CA1009-1
python3 scripts/apply_geo_live_fixes.py --apply
```

The default is a dry run. `--apply` writes `docs/geo-live-fixes-out/<ticket>.body.html` and, when the title changes, `<ticket>.title.txt`. That directory is gitignored. Live pages stay as they are. Do not run `--apply` until you want the local files. Do not point those files at the store until you explicitly decide to update live posts.

| Kind | Count |
|---|---:|
| Shorten the title so the tag (`H1` + ` – Wellness Nest`) is ≤70 characters | 14 posts |
| Rephrase one H2 into a question | 8 posts |
| Add one primary-source link (URL checked 200, or PubMed 203) | 5 posts |
| Replace the FloraFresh formula with the Supplement Facts label | 3 posts, 7 snippets |
| Remove the hand-written `Published: October 17, 2026.` line | 3 posts |
| Add a related article link on `#MB1012-4` | 1 post |
| Replace the dead USADA URL on `#CA1009-1` | 1 post |

Posts can carry more than one kind. The 22 tickets are `CA1009-1`, `CA1009-2`, `CA1009-4`, `CA1009-5`, `CA1009-6`, `CA1009-8`, `CA1009-10`, `CA1016-1`, `MB1006-6`, `MB1007-1`, `MB1007-3`, `MB1008-2`, `MB1008-3`, `MB1009-1`, `MB1009-3`, `MB1009-5`, `MB1009-7`, `MB1012-1`, `MB1012-2`, `MB1012-3`, `MB1012-4`, `MB1012-5`.

Theme-only, no prepared body or title edit: `CA1009-7`, `CA1009-9`, `MB1007-2`, `MB1007-4`, `MB1008-1`, `MB1008-4`, `MB1008-5`, `MB1009-2`, `MB1009-4`, `MB1012-6`.

### Sources checked before they were written into the fix file

Checked 2026-10-19 with the same HEAD-then-GET curl the gate uses.

| Use | URL | Status | Why it is the right link |
|---|---|---:|---|
| `#CA1009-1` replaces the 404 | https://www.usada.org/spirit-of-sport/natural-products-derived-plants-animals/ | 200 | The old `/nutrition/natural-products-derived-from-plants-and-animals/` URL is still 404. This page is the moved article. It says colostrum and deer antler velvet can contain detectable quantities of IGF-1, which is the sentence the article already attributes to USADA. |
| `#CA1009-10` creatine loading | https://pmc.ncbi.nlm.nih.gov/articles/PMC5469049/ | 200 | ISSN position stand. It describes 3 g/day for 28 days as a gradual alternative to rapid loading. |
| `#CA1009-5` price per serving | https://www.fda.gov/food/information-consumers-using-dietary-supplements/questions-and-answers-dietary-supplements | 200 | FDA: the Supplement Facts panel must list the serving size and the number of servings per container. |
| `#CA1009-8` cure-claim caution | same FDA Q&A | 200 | FDA: a supplement marketed to treat, prevent, or cure a disease is regulated as a drug. |
| `#CA1009-2` and `#MB1012-2` | https://www.nccih.nih.gov/health/probiotics-usefulness-and-safety | 200 | NCCIH: different types of probiotics may have different effects. |
| `#MB1012-4` related article | https://wellnessnest.co/blogs/news/how-long-does-turkesterone-take-to-work-us-2026 | 200 | Existing turkesterone article. |

FloraFresh replacements name Bacillus coagulans SNZ-1969, 15B CFU per 2 gummies, vitamin C 30 mg, pineapple fruit powder 100 mg, sweetened with maltitol and isomalt (not sugar-free). 15 billion CFU is the same count. They do not use the retired 1 billion CFU figure, and they do not repeat four Lactobacillus strains, XOS, or D-mannose. Paragraphs about Lactobacillus in the vaginal microbiome, cited to papers, are left as research copy. The `find` strings still quote the live Lactobacillus wording so the patch can match those posts. `florafresh_rules.py` on this branch still flags 15B CFU as the old PDP figure. `scripts/apply_geo_live_fixes.py` ignores only that stale fingerprint when the patched body names SNZ-1969 and 15B CFU. Other FloraFresh violations still fail the dry run. This file does not publish. When the file was first prepared, `geo_citability.assess` reported no hard fail on any of the 22 patched bodies (checked against the fetched HTML, not against Shopify).

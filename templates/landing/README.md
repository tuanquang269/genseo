# Landing templates

**Current engine (2026-10-06): reference replicas** — `engine: "ref"` specs → `scripts/landing_clone.py`.
- `ref/css/*.css` — the reference's own section CSS (copied from `~/PATI/work/omnicreatine-local-clone/assets/omnicreatine.com/cdn/shop/t/56/assets/`, sourcemap comments stripped).
- `ref/extra.css` — what Dawn base.css gave the reference + the static featured-product grid/gallery, header/footer replicas, HTML chart cards, Montserrat metric tweak.
- `ref/svg.json` — the reference's inline SVG icons (stars, badge, arrows, shield, ticks).
- `page.gsl-ref-listicle-v1.liquid` / `page.gsl-ref-advertorial-takeover-v1.liquid` — generated (CSS scoped to `.gsl-ref`, brand palette, JS for gallery / bundle form / reviews dots / real-deadline countdown) — installed in the live theme 2026-10-06 as NEW files. Change → bump `-v2`.
- Spec samples: `landing_drafts/fusiforce-creatine-gummies-listicle.json` (listicle), `landing_drafts/shilasource-resin-advertorial.json` (advertorial). Keys: `topbar`, `hero`, `byline`, `items[]` (`image` square or `chart`), `bridge` (row 07), `expert` (+`source`), `offer`, `product` (`gallery[]`, `options[]` with `variant_id`/`qty`/`selling_plan`, `icon_row`, `buy_once`, `rating_line` + `rating_source`), `testimonials[]` (+`source`), `faq[]`, `faq_image`, `faq_cta`, `header`, `footer`.

---
Legacy v1 engine (`landing_render.py`, `page.genseo-landing-*-v1.liquid`) below — kept for reference, not installed.

# GenSeo landing templates: `listicle` and `advertorial`

Renderer: `scripts/landing_render.py` · gate: `scripts/validate_landing.py` · publish/preview: `scripts/landing_publisher.py`
· agent workflow: `skills/genseo-landing-pages/SKILL.md` · runner: `scripts/run_landing_headless.sh` · queue: `landing-tickets.md`
· brand tokens: `brand/wellnessnest.json`, `brand/ageaura.json` (extends wellnessnest).

Delivery follows Kevin's vault skill `claude-design-dtc-listicle-advertorial` (+ `PATI-ADAPTATION.md`) and the
WellnessNest theme gotchas (`wellnessnest-advertorial-builder`, `crawl-funnel-to-shopify`):
- `body_html` = inline CSS only, no `<script>`; classes namespaced `gsl-`, rows marked `data-gsl-row` / `data-gsl-split`.
- `page.genseo-landing-v1.liquid` (theme header/footer kept) and `page.genseo-landing-takeover-v1.liquid` (hides theme
  chrome with CSS, because `{% layout none %}` is ignored on this store) hold the ONE style block: reset + the single
  grid media query (text 2/3 · media rail 1/3 from 760px; 1 column below) and output `{{ page.content }}`.
  The live theme has no default page template, so a page without one of these suffixes 404s.
- Shell 1160px, prose measure ≤ 760px, one alignment model (text left, media rail right) everywhere.
- Sticky bar = CSS `position:sticky` as the last child of the "sticky zone" (bridge → end for hybrid, after the hero
  for advertorial), so it only appears once that zone is on screen. No JS.
- `<details>` FAQ accordion; CTAs open the exact PDP URL in a new tab, min 44px tall.

## Where the structure came from
Reference pages (competitor omnicreatine.com, cloned locally by another agent; read-only):
`python3 -m http.server 8790 -d ~/PATI/work/omnicreatine-local-clone` on the MacBook.

| Reference: `/pages/10-reasons-why-creatine-is-for-skinny-people/` | Our `listicle` |
|---|---|
| timer bar (countdown) | `announcement` strip — **no countdown** |
| hero-article: H1 with coloured number, byline + "last updated", summary | `title` + `title_highlight`, `byline`, `updated`, `summary` |
| 7–10 image/text rows, number pill 01…, some with bar charts | `items[]` (pill numbers, `image` or `chart`, both allowed) |
| expert section (dark navy, 5-star quote card, portrait) | `expert` (dark section, **no portrait/face**, quote must be sourced or placeholder) |
| offer box (dashed border, pack left, "Lock in X% off", CTA, countdown, sell-out risk, money-back) | `offer` + `product.image` (**no countdown / scarcity**) |
| — | `sources[]` list, `sticky_cta` bar |
| footer FDA disclaimer | footer from `brand.disclaimer` + `legal_footer` |

| Reference: `/pages/advv-1/` | Our `advertorial` |
|---|---|
| mini header: "Shop now" + logo | auto from `brand.logo` / `brand.domain` |
| hero split: image, H1 "6 Reasons…", subhead, CTA, guarantee line | `hero{image, eyebrow, subhead, cta, trust_line}` + `title` |
| 4–6 numbered circle rows, alternating sides, one with a chart | `items[]` (circle numbers, alternating) |
| expert / trust dark section | `expert` |
| featured product: gallery, rating, bullets, pack options with prices, CTA | `product{image, rating_line, name, blurb, bullets[], options[], cta, fine_print[]}` |
| 3 review cards on dark | `testimonials[]` (placeholders unless `source`) |
| FAQ accordion | `faq[]` |
| footer | footer + `sources[]` + `sticky_cta` |

## Spec schema (`landing_drafts/<slug>.json`)
```
template: "listicle" | "advertorial"   posture: "hybrid" | "advertorial" | "editorial"   template_suffix
store: "wellnessnest" | "ageaura"     slug: handle (also the page handle)
title, title_highlight (listicle), meta_description, byline{name (roster.json), role}, updated, summary, announcement
hero{image, alt, eyebrow, subhead, cta{text, href}, trust_line}                                (advertorial)
items[]{title, body (p/strong/em/a/ul/ol/li/br only), image, alt, chart{title, bars[]{label, value, display, highlight}, source}}
expert{number, heading, body, quote, attribution, image(no faces), source}
offer{badge, headline, subhead, cta, fine_print[]}                                              (listicle)
product{name, image, blurb, bullets[], options[]{label, note, price, highlight}, rating_line, rating_source, cta, fine_print[], source}
intro (listicle, limited HTML) · items[].evidence (label, e.g. "Human trial, J Appl Physiol 1996")
bridge{eyebrow, heading, body, image, alt} · checklist{heading, intro, items[]} · final_cta{heading, body, cta}
testimonials_heading, testimonials[]{title, quote, name, detail, source}, faq[]{q, a}, sources[]{label, url}, sticky_cta{label, text, href}
```
Images: repo-relative `tmp_images/landing-<slug>/<name>.webp` (from `article_images.py --qc`) or an https Shopify CDN URL.
`[[PLACEHOLDER: …]]` anywhere renders as a yellow chip and blocks `--live`.

## Brand tokens used (Wellness Nest, from the live theme "WN Shopify Theme - 02072026", Shrine PRO 1.8.1)
primary `#54b94a` · primary_dark `#3a9e40` · ink `#1e3a29` · text `#222126` · dark_section `#2e2a39` · bg_soft `#f6fbf5`
· border `#dbeedb` · price_accent `#dd1d1d` · body font Montserrat · headings Helvetica 700 · logo `WNN_Main_Logo` (theme CDN).
AgeAura overrides: ink `#2e2a39`, bg_soft `#f5f5f7`, border `#e3e3e8`; forbidden: urolithin, peptide, musclemax.
The only AgeAura product handle a ticket or spec may target is `ageaura-pure-nmn-tmg-nad-complex` (`scripts/ageaura_rules.py`). `ageaura-pure-urolithin-a` fails closed in `build_landing_tickets.py` and `validate_landing.py`.

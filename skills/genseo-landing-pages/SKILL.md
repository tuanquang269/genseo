---
name: genseo-landing-pages
description: Build an on-brand GenSeo landing page (template "listicle" or "advertorial") for Wellness Nest or AgeAura as a local preview or an UNPUBLISHED Shopify page. Use when asked for a listicle/advertorial/sales page, not for the daily SEO articles.
---

# GenSeo landing pages — listicle & advertorial

These are Shopify **pages** (`/pages/<handle>`), not blog articles. They live outside the daily
5/day article flow: no ticket in `daily-tickets.md`, no `genseo_published_today.py` guard, no tracker CSV row,
and they can never show up in `/blogs/news.atom`, so they never count toward (or block) the 5/day target.
Queue: `landing-tickets.md` (manual) / `daily-landing-tickets.md` (daily lane, own 1/day guard — see the end of this file). Runner: `scripts/run_landing_headless.sh`. Section map + schema: `templates/landing/README.md`.

## Templates = EXACT replicas of the reference pages (Kevin 2026-10-06, priority)
`"engine": "ref"` specs render with `scripts/landing_clone.py` (landing_render.py / landing_publisher.py dispatch to it):
- **listicle** = omnicreatine `/pages/10-reasons-why-creatine-is-for-skinny-people`; **advertorial** = `/pages/advv-1`
  (local clone `~/PATI/work/omnicreatine-local-clone`, `python3 -m http.server 8790`). Same section order, markup,
  class names, spacing and type scale. Change only copy, product data, images and brand tokens. Don't simplify.
  - listicle: top bar (`rbltb`) → hero article card + byline (`rblha`) → rows 01–07 alternating (`rblit--v2`; rows 02 + 04
    are the chart slots) → 08 expert/proof (`rble--v2`) → offer card (`rblof`) → footer (`rblft`).
  - advertorial: header → hero (`rblh`) → rows 1–4 (`rblit`) → 5 expert/proof (`rble`) → featured product (gallery +
    `rbp-head` + `nw-bundle` Subscribe & Save → real `/cart/add` form with variant/qty/selling_plan + icon row + buy-once)
    → 3 review cards (`rblr`) → FAQ accordion + tall image (`rbq`) → footer.
- CSS = the reference's own section files (`templates/landing/ref/css/`) + `ref/extra.css`, scoped under `.gsl-ref`,
  palette/font swapped to the brand. Icons from `ref/svg.json`. It ships inline in the theme template
  `templates/page.gsl-ref-<kind>[-takeover]-v1.liquid` (+ small JS); the page body is markup only.
- Every image slot is cropped from a GenSeo-generated square (`article_images.py --square --qc`, no faces) to the
  reference slot (rows 616×590 desktop / 1:1 mobile, expert 616×560, hero 616×700, FAQ 720×1036), webp < 80 KB.
  Real PDP pack shots only where the reference shows the product (offer card, product gallery) and only clean ones
  (no faces, no claim overlays). Chart slots = data-accurate HTML charts (`chart` / `chart.kind: "stats"`), not images.
- Reviews/rating: Trustpilot (`trustpilot.com/review/wellnessnest.co`, parse `__NEXT_DATA__` — needs a real browser,
  curl/WebFetch get a bot wall): 4–5★ only, verbatim, first name + initial as shown, TrustScore + count exactly as
  displayed. No reviewer → the expert slot carries a real Trustpilot review. Countdown/sell-out only with a real
  `topbar.deadline`. Listicle keeps theme chrome; advertorial = takeover (`"takeover": true`) with header/footer replicas.
- Before reporting: side-by-side reference vs ours at 1440 + 375 (`scripts/landing_compare_shot.mjs <url> <out.png> <width>` + `scripts/landing_sbs.py <ref.png> <ours.png> <out.jpg> <colw>`).
- Throwaway handles via `"handle"` (e.g. `gsl-preview-<x>-t1`); `--draft --install-template` adds the template to the
  live theme only if that key does not exist yet (never overwrites). Unpublished pages 404 on the storefront.

## Vault doctrine this skill follows (read when in doubt; vault wins over this file)
- `~/.claude/skills/claude-design-dtc-listicle-advertorial/SKILL.md` + **`PATI-ADAPTATION.md`** (Kevin's Claude Design
  listicle/advertorial skill; the PATI overlay wins): source discipline, funnel order, layout system, sticky reveal,
  single-file Shopify Custom Liquid delivery, real-vs-fake trust modules, acceptance checklist.
- `~/.claude/skills/wellnessnest-advertorial-builder/references/gotchas.md` and
  `~/.claude/skills/crawl-funnel-to-shopify/` (SKILL.md, references/gotchas.md, assets/hide_chrome.html): the live
  theme has no default page template, `{% layout none %}` is ignored (GemPages), compiled-template cache → bump the
  suffix, GemPages per-URL render cache → throwaway handle, theme-protected asset names.
- Vault: `30-creative/32-copy/7-advertorial-listicle-presell-framework.md` (32.7 content structure),
  `10-foundations/65-shopify-dev-docs-map.md`, `20-brands/1-wellnessnest.md` + `21-wellnessnest-products/*`.
  Where 32.7 suggests Urolithin A for AgeAura or "purity testing" as the ShilaSource origin story, or a product note
  repeats FloraFresh's PDP formula, Kevin's newer rules win (AgeAura = NMN + TMG only; FE-22 / no-COA; FloraFresh =
  its Supplement Facts label).

## Posture (Kevin's call — PATI-ADAPTATION #1)
`posture` in the spec: **hybrid** (listicle default — editorial findings, product only from the bridge on, sticky bar
only after the bridge, zero fabricated trust) · **advertorial** (advertorial default — the reference's scaffolding:
hero CTA, sticky for the whole page, review cards; still no fabricated facts) · **editorial** (no announcement, no
testimonials, no sticky). Surface the choice to Kevin; never silently downgrade his pick.

## Hard rules
1. **No invented facts.** Every number, study, dose, price, rating, review count, testimonial and expert quote
   comes from a page you actually fetched this run (PubMed / Europe PMC / DOI, the live PDP `/products/<handle>.js`,
   `/policies/refund-policy`). Anything else is `[[PLACEHOLDER: what is needed]]` or is cut. Placeholders render
   as yellow chips, and `--live` refuses any page that still has one.
2. **Testimonials, star ratings, "X customers", expert quotes**: placeholders unless the spec block carries a
   `source` (review app export, signed expert review). Do not copy PDP social-proof numbers onto a page.
3. **AgeAura = the NMN + TMG Complex only** (`/products/ageaura-pure-nmn-tmg-nad-complex`, Kevin 2026-10-06). No other
   AgeAura handle, bundle (`-p2`) or collection link; never Urolithin A or peptides. `brand/ageaura.json`
   (`allowed_products`, `forbidden_terms`) + `validate_landing.py` block them in any store's page.
   **FloraFresh = its Supplement Facts label** (Kevin 2026-10-09): Bacillus coagulans SNZ-1969, 1 billion CFU per
   2 gummies, Vitamin C 30 mg, pineapple fruit powder 100 mg (with bromelain), maltitol + isomalt (not sugar-free).
   The live PDP description (15 billion CFU, four Lactobacillus strains, XOS, D-mannose, sugar-free) is wrong until
   Kevin's GO rewrites it, so for FloraFresh the PDP gives price, offer and directions, never the formula.
   `validate_landing.py` fails any FloraFresh claim the label does not support (`scripts/florafresh_rules.py`).
   **Shilajit Shockwave** pack-label doses come only from `product_refs/shilajit-shockwave.label.json` (identity lines; no milligram, serving count, or volume token). `validate_landing.py` fails a dose that file does not list (`scripts/shockwave_rules.py`).
   **Pure Shilajit Gold Resin** pack-label doses come only from `product_refs/pure-shilajit-gold-resin.label.json` (identity lines, `75% Fulvic`, and `1.06 oz (30g) - 75 servings`; no milligram token). `validate_landing.py` fails a dose that file does not list (`scripts/gold_resin_rules.py`).
   **ShilaSource Himalayan Shilajit Resin** pack-label doses come only from `product_refs/shilasource-himalayan-shilajit-resin.label.json` (front-of-pack lines: `70% Fulvic Acid*`, `1.06oz (30g)`, and the split `75` / `SERVINGS` badge; no milligram token). `validate_landing.py` fails a dose that file does not list (`scripts/shilasource_resin_rules.py`).
4. **No faces** in any image. Use `scripts/article_images.py` with `--qc` (same pipeline + QC as articles),
   `--product-ref <handle>` (no `:index`) for any image showing a pack, `--ugc` for lifestyle shots, and put
   "no people's faces" in the NEGATIVE. Never `--persona-ref`, never `persona_picker.py`. Run in the foreground.
5. **No fake urgency.** The reference pages use countdown timers and "sell-out risk" lines; we render them only with a
   real promo deadline (`topbar.deadline`), otherwise the top bar shows labels only and the offer has no timer.
6. **FE-22 (ShilaSource):** never bring back lab / fulvic % / heavy-metal claims or the removed testimonials.
7. **Funnel order** (hybrid/editorial): the numbered findings never name or link the product; the `bridge` runs
   daily use → format friction → "convenience is part of consistency" → product as ONE option; CTAs invite
   inspection ("See serving & ingredients"), open the exact PDP URL in a new tab. The validator enforces it.
8. **No dosage-with-units in body copy** (PATI-ADAPTATION #6): mg/g/IU amounts only in the product/offer card, and
   only what the live PDP prints. Describe study doses in words ("a high-dose loading week", "a small daily amount").
9. **Lead ingredient = largest dose** on the panel (PATI-ADAPTATION #5) for any formula bullets.
10. **Images < 80 KB as served with `Accept: image/webp`** (PATI-ADAPTATION #8); pack shots = real PDP CDN image,
   uncropped, `object-fit:contain`. Lifestyle shots that show no package must also show no OTHER package (the QC
   fails any tub/jar without a reference; describe a shaker/scoop/scene instead).
11. House voice from `brand/<store>.json` → `voice` (plain, evidence-led, honest about what a study did NOT test,
   e.g. "purified extract, not our resin"). Byline must be on `roster.json` (default Dr. Marcus Hale).
12. Never publish live. Never edit an existing live page/article.

## Workflow
1. **Brief → product facts.** `curl -s -A "Mozilla/5.0" https://wellnessnest.co/products/<handle>.js` → title,
   price, variants, images[0] (real packaging for the product/offer block). Read the vault product note
   `~/PATI/LLM-Wiki/20-brands/21-wellnessnest-products/<product>.md` if present. FloraFresh formula facts come
   from its Supplement Facts label only (`python3 scripts/florafresh_rules.py --brief`), never the PDP description.
2. **Evidence.** 3–6 sources max. Confirm every figure in the abstract (Europe PMC REST:
   `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:<doi>&resultType=core&format=json`).
3. **Spec.** Write `landing_drafts/<slug>.json` (schema in `templates/landing/README.md`; copy a sample:
   `landing_drafts/fusiforce-creatine-gummies-listicle.json` / `shilasource-resin-advertorial.json`).
   Each numbered item that states a number needs an inline `<a href>` to its source.
4. **Images** (listicle: 2–4 item images; advertorial: hero + 2–3 item images), slug `landing-<slug>`:
   `/usr/bin/python3 scripts/article_images.py --slug landing-<slug> --name <name> --product-ref <handle> [--ugc] --qc --prompt "<SPEC/SCENE/LIGHT/STYLE/NEGATIVE: no people's faces, no text overlays, no other brands>"`
   Reference them in the spec as `tmp_images/landing-<slug>/<name>.webp`. A QC FAIL means re-roll (max 3).
5. **Claims log** `landing_drafts/<slug>.claims.md`: claim | source | how verified, plus what you deliberately left out.
6. **Gate + preview:** `/usr/bin/python3 scripts/landing_publisher.py landing_drafts/<slug>.json`
   (runs `validate_landing.py`, renders `landing_drafts/<slug>/{body.html,preview.html}`). Fix every ✗.
6b. **Copy hard-rules gate (advisory for pages):** `/opt/homebrew/bin/python3 ~/.claude/skills/evolve-copywriting-consultant/scripts/copy_hardrules_gate.py <text export> --ref-brand NONE --panel NONE`.
   Known page-context findings: the FDA disclaimer trips "disease verb", the roster byline trips "surnamed doctor",
   product-card amounts trip "dosage". Anything else = fix. The Evolve 6-part toolkit pass + benchmark judge
   ([[advertorial-swipe-benchmark]], tie = fail) are the craft half — run them before Kevin reviews.
7. **Screenshot:** `playwright screenshot --full-page --viewport-size=1280,900 --wait-for-timeout=2500 file://…/preview.html landing_drafts/<slug>/desktop.png`
   (and `--device="iPhone 13" … mobile.png`).
8. **Optional unpublished draft:** `landing_publisher.py <spec> --draft` → Shopify page `published:false`,
   local images uploaded to Shopify Files, ids stored in `landing_drafts/<slug>/shopify.json` (re-runs update it).
9. **Live** only on Kevin's explicit GO: `GENSEO_LANDING_LIVE_OK=1 landing_publisher.py <spec> --live`
   (refused while any placeholder remains). The page carries `template_suffix` (default `genseo-landing-v1`,
   takeover = `genseo-landing-takeover-v1`); `--live` refuses if `templates/page.<suffix>.liquid` is missing from
   the live theme, and `--install-template` uploads it from `templates/landing/` (needs write_themes). Bump the
   suffix on any template change. Iterate on a throwaway handle first (GemPages caches per URL).
10. Commit `landing_drafts/<slug>.json`, `.claims.md`, `<slug>/body.html`, screenshots. `tmp_images/` is not versioned.

## Daily listicle lane (Kevin 2026-10-08) — 1 UNPUBLISHED draft per day, Kevin approves
- launchd `com.pati.genseo-landing` 08:15 + 16:15 catch-up → `scripts/run_landing_daily.sh` (MacBook = standby,
  waits 75 min; Mini = primary; plists in `deploy/com.pati.genseo-landing.{macbook,mini}.plist`). Kill switch:
  `touch state/landing-daily.disabled`.
- Article batch on the same Mac (`state/daily.lock`): the lane yields to it at most `GENSEO_LANDING_ARTICLE_YIELD_MIN`
  (default 30) wall-clock minutes, re-checking every `GENSEO_LANDING_POLL_SEC` (60) s, then re-runs the guard and builds
  ALONGSIDE it. A page is never a blog article, so article publishing stays serialized by the article lane's own lock +
  guards. (Until 2026-10-09 it waited up to 180 min via `GENSEO_LANDING_WAIT_ARTICLES_MIN`, which is no longer read; a
  long article batch then held the day's draft hostage.) Offline self-check: `bash tests/test_landing_daily_lock.sh`.
- Guard: `scripts/landing_guard.py` counts Shopify pages with a `gsl-` handle CREATED today (ICT). ≥1 → stand down;
  Shopify unreadable → fail closed. `landing_publisher.py` (env `GENSEO_LANDING_DAILY=1`) re-checks it right before
  POSTing a new page, refuses `--live`, and requires a `gsl-preview-` handle.
- Queue `daily-landing-tickets.md` ← `scripts/build_landing_tickets.py` (live products.json → real single SKUs that pass
  `brand_rules` + have `product_refs/<handle>.png` + an entry in `templates/landing/listicle-angles.json`; LRU product
  rotation, no repeat inside 6 days; least-used angle) → `lint_tickets.py`.
- Reviews: `scripts/trustpilot_reviews.mjs` → `state/trustpilot/wellnessnest.json` (4–5★ only, verbatim, TrustScore +
  count as displayed). The agent quotes only from that file; missing → placeholder, never invented.
- Agent: `run_landing_headless.sh --queue daily-landing-tickets.md --next` with the DAILY rules (ref listicle,
  `gsl-ref-listicle-v1`, slug `<short>-listicle-<yymmdd>`, handle `gsl-preview-<slug>`, Dr. Marcus Hale, fresh
  no-face `--square --qc` images uploaded by the publisher with the CLI app token).
- Wrapper post-checks on its own: validate_landing.py, landing_qa.mjs (desktop.png 1440 + mobile.png 375, overflow),
  page must be unpublished (force-hidden + logged if not), ticket re-tagged `[DRAFT <day> page <id>]` /
  `[DRAFT-QA-FAIL …]` / `[FAILED …]`, outputs committed. Logs: `logs/landing-daily/<day>.log`.
- Review a draft: unpublished pages 404 on the storefront. Short look on the live theme:
  `landing_preview_toggle.py on <page_id>` (gsl-preview- handles only) → check → `landing_preview_toggle.py off <page_id>`.

### Benchmark vs the reference listicle (2026-10-08)
- `node scripts/landing_bench_extract.mjs <url|preview.html> state/bench/<name>` → 1440/375 full-page shots + text + DOM
  measurements (H1 lines, paragraph words, screens tall, small text, dashes, CTA wrap, image alts…).
- `/usr/bin/python3 scripts/landing_bench_jev.py state/bench/ref.json state/bench/<name>.json --label rN --calls 4 --cap 0.30`
  → blind A/B (random order) JEV jev-latest scores on 12 criteria (design-taste-frontend + DTC), averaged;
  ledger in `state/bench/jev-ledger.json`. JEV is text-only: screenshots go in as measurements, not pixels.
- Reference: `python3 -m http.server 8790 -d ~/PATI/work/omnicreatine-local-clone` →
  /pages/10-reasons-why-creatine-is-for-skinny-people/ (already extracted to state/bench/ref.json).
- Lessons now enforced by validate_landing.py for `"daily": true` (warnings otherwise): no em/en dashes, H1 ≤ 48
  chars, summary ≤ 32 words, item titles ≤ 34 chars, paragraphs ≤ 40 words, ≤ 520 chars per row, short chart
  labels, CTA ≤ 3 words. Renderer: chart text ≥ 13px, portrait offer pack capped at 440px, crops always < 80 KB.
  Publisher: CDN cache keyed by content hash, so re-rendered images re-upload.

### Premium visual layer (2026-10-08, Kevin: "UI/UX and product images still too ugly")
- Spec `"style": "premium"` + `"template_suffix": "gsl-ref-listicle-v2"` appends `templates/landing/ref/premium.css` (forest/bone/sage palette, radius lock 24/16/pill, tinted shadows, 19px body, number badges, gradient charts, review cards, polished offer, mobile sticky CTA after the bridge). v1 pages are untouched. The theme file is installed once; a CSS change means a NEW suffix (v3), never overwriting.
- Keys: hero.kicker/image/chip/cta/source/focal_y, trust[] + trust_source, items[].evidence_label, items[].layout "callout", expert.reviews[] (real 4-5★ Trustpilot + URL), offer.rating_html/price{now,was,tag,note}/bullets/price_source, sticky_cta, pack_images[]. Model: landing_drafts/ageaura-nmn-listicle-261008.json.
- Images: one art direction for the whole page. Pack shots are generated with the real cutout as `--ref`, gated by `landing_label_gate.py` and a mark zoom check, with `landing_pack_shots.py` composites as the fallback (scripts/tools/README.md). A whitelist pack shot fails closed when `product_refs/<handle>.label.json` is missing, OCR fails, or the host has no macOS Vision (`swift` + `scripts/tools/label_ocr.swift`). That is not a pass. Skip the gate only for images that are not whitelist pack shots. See `docs/LABEL_OCR_GATE.md`.
- Visual benchmark: `scripts/landing_bench_vision.py state/bench/live state/bench/<new> --label <x> --calls 6` runs a blind A/B in random order with two vision judges (gem9: gemini-3.1-pro-low + gpt-5.6-luna, $0) on 7 criteria. Reference = the LIVE omnicreatine listicle (state/bench/live-*.png). v3 result: new 7.21 vs live 5.50, ahead on all 7 criteria.

### Approval = the REAL Shopify render (2026-10-08)
Kevin saw an old offer box in his preview while the local v3 screenshots looked right, so screenshots for approval now always come from the storefront. `scripts/landing_real_qa.py <spec>` does two things:
- **Read-only parity checks:** the MAIN theme holds `templates/page.<suffix>.liquid` byte-identical to the local copy; `template_suffix` matches; the page's visible text equals local `body.html`; all images are on the Shopify CDN.
- **Storefront screenshots:** `landing_live_shot.mjs` takes them in a ~40 s gsl-preview window (fresh context, `?v=` cache-buster), then hides the page again in a finally block.

`run_landing_daily.sh` runs it after every daily draft and tags the ticket DRAFT-QA-FAIL if it fails. Set `GENSEO_LANDING_REAL_QA_WINDOW=0` to keep parity but skip the window.

### Packaging palette (Kevin 2026-10-09: "UI/UX colors must be congruent with the product's packaging")
Every listicle/advertorial wears the hero product's PACK colors. A chromatic pack replaces the house greens. A neutral pack with no measured chromatic hue keeps the house greens until a grey token map is recorded. Kevin judges pages heavily on visual design.
- **Extract:** `scripts/landing_palette.py extract <img…>` k-means (OKLab, k=6) over `product_refs/<handle>.png`
  (+ spec `pack_palette_images`), ignoring near-white/near-black/transparent pixels. Pack hue = heaviest chromatic
  cluster (OKLCh C >= 0.035). A pack with < 8 % chromatic pixels is "neutral" and keeps the house palette.
- **Apply (automatic at render):** `landing_clone.py` calls `landing_palette.resolve(spec)` for every `engine: ref` spec
  created >= 2026-10-09 (a chromatic palette file refuses `"palette": "off"`; `{"hue": 12, "chroma": 0.11}` is applied only when it sits within the file's hue tolerance). Every
  house-green literal in the compiled template CSS and in the body (inline SVG fills, #rrggbbaa included) is re-hued to the
  pack hue at the SAME WCAG luminance, so all contrast ratios stay what the template already passes; text tokens
  (`--gp-accent/ink/text/muted`) are additionally darkened to >= 4.6:1 on white and the soft surfaces.
  Delivered as `<style id="gsl-pal">` + class `gsl-pal` in the **page body**: selectors re-emitted one class more specific
  (`.gsl-ref.gsl-pal …`) for every declaration of an affected property family, so the template's own cascade is kept.
  **The shared theme template is never touched**: other live pages on the same suffix render exactly as before.
  Output: `landing_drafts/<slug>/palette.json` (pack clusters, hue, chroma).
- **Source of truth:** `product_refs/<handle>.palette.json`, read by `scripts/packaging_palette.py`. Hexes in that
  file are measurements (k-means of the pack photo, or the packaging note already in `product_refs/<handle>.json`).
  Do not invent a hue for a product with no file. FloraFresh is chromatic dusty pink / rose `#d17a85` (hue 12.3).
  AgeAura Pure NMN + TMG is neutral (white with dark grey text; no cluster reached chroma 0.035). A hard-window spec
  (`created` >= 2026-10-09) fails closed when it sets `palette` off on a chromatic file, forces a hue outside the
  file's tolerance, or forces a chromatic hue on a neutral file. The pack photo failing to match the file is also a
  failure. Products with no palette file are a gap, not a guessed color. See `docs/PACKAGING_PALETTE_GUARD.md`.
- **Gate:** `scripts/landing_palette.py check <spec>` on the rendered body: CTA `--gp-forest`, `--gp-accent` and
  `--gp-sage` hue within 30° of the pack hue (the palette file's hue when the file exists), accent chroma >= 0.035,
  WCAG AA (4.5:1) for ink/text/muted/accent on white and sage and white on the CTA. A neutral file allows near-grey
  tokens and, while `house_palette_allowed` is true, the house greens. FAIL is hard for specs created >= 2026-10-09
  (WARN for older live pages). `palette: off` does not skip that fail when a chromatic palette file exists. Runs in
  `brand_rules.spec_violations` (so `validate_landing.py`, `landing_render.py`, and `landing_publisher.py` refuse the
  spec), `landing_palette.py check` (refuses the push), `run_landing_daily.sh` (ticket → DRAFT-QA-FAIL palette=fail),
  `lint_tickets.py` (open landing tickets only), and `landing_real_qa.py` repeats the hue test on the storefront's
  computed colors (`<vp>_palette_matches_pack`).
- **Clipped text:** `landing_qa.mjs` and `landing_live_shot.mjs` report `clipped` (an element's own text wider than its
  box or off-screen; swipe carousels, hidden sticky bar and deliberate ellipsis excluded). The daily wrapper treats it
  like overflow; real QA has `<vp>_no_clipped_text`. Page-level fix for the offer pill (`PAGE_FIX_CSS`, body
  `<style id="gsl-fix">`, specs >= 2026-10-09): it wraps/shrinks on phones instead of being cut off.
- Tests: `/usr/bin/python3 -m unittest tests/test_packaging_palette.py tests/test_landing_palette.py`.
- First page: FloraFresh `/pages/vaginal-probiotic-research` (pack #d17a85 rose → CTA #561b26, accent #a44958,
  sage #feeff0, ink #501521).

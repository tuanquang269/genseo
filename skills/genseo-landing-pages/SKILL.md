---
name: genseo-landing-pages
description: Build an on-brand GenSeo landing page (template "listicle" or "advertorial") for Wellness Nest or AgeAura as a local preview or an UNPUBLISHED Shopify page. Use when asked for a listicle/advertorial/sales page, not for the daily SEO articles.
---

# GenSeo landing pages — listicle & advertorial

These are Shopify **pages** (`/pages/<handle>`), not blog articles. They live outside the daily
5/day article flow: no ticket in `daily-tickets.md`, no `genseo_published_today.py` guard, no tracker CSV row,
and they can never show up in `/blogs/news.atom`, so they never count toward (or block) the 5/day target.
Queue: `landing-tickets.md`. Runner: `scripts/run_landing_headless.sh`. Section map + schema: `templates/landing/README.md`.

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
  Where 32.7 suggests Urolithin A for AgeAura or "purity testing" as the ShilaSource origin story, Kevin's newer
  rules win (AgeAura = NMN + TMG only; FE-22 / no-COA).

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
3. **AgeAura = NMN + TMG only.** Never Urolithin A or peptides; `brand/ageaura.json` `forbidden_terms` fails the gate.
4. **No faces** in any image. Use `scripts/article_images.py` with `--qc` (same pipeline + QC as articles),
   `--product-ref <handle>` (no `:index`) for any image showing a pack, `--ugc` for lifestyle shots, and put
   "no people's faces" in the NEGATIVE. Never `--persona-ref`, never `persona_picker.py`. Run in the foreground.
5. **No fake urgency.** The reference pages use countdown timers and "sell-out risk" lines; we don't.
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
   `~/PATI/LLM-Wiki/20-brands/21-wellnessnest-products/<product>.md` if present.
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

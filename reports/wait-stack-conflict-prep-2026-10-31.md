# Wait-stack conflict prep — 2026-10-31

Report only. Nothing in this pass was merged to `main`. No pull request was closed, retargeted, or marked ready. No branch was force-pushed or rebased. Nothing was published. No theme file, paid-traffic page, Meta record, spend change, email send, or store setting was edited.

This pass does the leftover that draft [#103](https://github.com/tuanquang269/genseo/pull/103) left on purpose: refresh [#83](https://github.com/tuanquang269/genseo/pull/83), [#46](https://github.com/tuanquang269/genseo/pull/46), and [#50](https://github.com/tuanquang269/genseo/pull/50) onto `origin/main`, then map the conflicts those three still have with the wait drafts. The wait stack itself was not pushed.

`origin/main` is `6c46771de6a11f5719422d94a337215015bec364` ("Publish shilajit loading with food article", 2026-10-27 10:17:43 +0700). That is the same SHA [#100](https://github.com/tuanquang269/genseo/pull/100), [#101](https://github.com/tuanquang269/genseo/pull/101), [#103](https://github.com/tuanquang269/genseo/pull/103), and [#104](https://github.com/tuanquang269/genseo/pull/104) were written against.

## What was updated

Each branch received one `git merge --no-ff origin/main`. The merge was clean. The push was a fast-forward of that branch (`429ac9a..6301fa5`, `22773f7..5baccfd`, `4a3684d..f844148`). All three stay drafts. GitHub reported `MERGEABLE` / `CLEAN` against `main` after the push. Each tip is 2 commits ahead of `main` and 0 behind.

| PR | Branch | Previous tip | New tip | Parents |
| --- | --- | --- | --- | --- |
| #83 | `cursor/ai-referrer-weekly-1021` | `429ac9a2d77ce32319a1cd193378e6f13d5eefe5` | `6301fa5e67b8ceeabf23edf65ab1f2674f094f40` | `429ac9a` + `6c46771` |
| #46 | `cursor/turkesterone-listicle-qa-91b6` | `22773f70213e41977cb0ad969daced6b20896964` | `5baccfd631af6de6e24fd4120250d528da3bfde5` | `22773f7` + `6c46771` |
| #50 | `cursor/ageaura-listicle-qa-55fe` | `4a3684dec18f69de98ac456dd013de9419f4ebe4` | `f844148bd3009cf3432f41a5d358af0f35b93b13` | `4a3684d` + `6c46771` |

The merge did not rewrite the files those drafts actually own:

- #83: `knowledge_base/AEO_GEO_GUIDELINES.md` and `scripts/ai_referrer_report.py` match the old tip.
- #46: `landing_drafts/turkesterone-listicle-261016.claims.md`, the spec JSON, `body.html`, `preview.html`, and the QA note match the old tip. `scripts/validate_landing.py` on the new tip matches `main`. Relative to the old tip, that file only picked up `main`'s cutout docstring. The branch's `premium_pack_list_message` helper is already on `main`.
- #50: the AgeAura `261017` claims log, spec JSON, `body.html`, `preview.html`, `scripts/landing_clone.py`, and `tests/test_landing_stars.py` match the old tip.

These three tips still carry `main`'s FloraFresh constant (`CFU = "1 billion CFU"`, `_LABEL_CFU = 1e9`). The 15B guard is [#104](https://github.com/tuanquang269/genseo/pull/104) (`CFU = "15B CFU"`, `_LABEL_CFU = 15e9`). This pass did not copy that guard onto #83, #46, or #50.

## Conflict map

Pairwise checks used the new tips. For #83 vs #85, #46 vs #96, and #50 vs #96, a detached worktree ran `git merge --no-commit --no-ff`, the conflict regions were read, then `git merge --abort` and the worktree was removed. Nothing from those simulations was committed or pushed. The other pairs are `git merge-tree --write-tree` only.

### Still conflicting

| Pair | Result | Files | Who owns the source of truth |
| --- | --- | --- | --- |
| #83 `6301fa5` vs #85 `88457b2` | 1 content conflict | `knowledge_base/AEO_GEO_GUIDELINES.md` lines 83–87 | #83 owns the 2026-10-21 referrer-domain bullet. #85 owns the 2026-10-21 buyer prompt-loss bullet. Same list position, two different sentences. |
| #46 `5baccfd` vs #96 `29c6c25` | 1 content conflict | `landing_drafts/turkesterone-listicle-261016.claims.md` lines 22–50 | #46 owns the QA tail (worm-study wording, no cutout, Trustpilot left unread, jar photo). #96 owns the 2026-10-26 price note. |
| #50 `f844148` vs #96 `29c6c25` | 4 content conflicts | `landing_drafts/ageaura-nmn-tmg-listicle-261017.claims.md`, `.json`, `body.html`, `preview.html` | #50 owns the 2026-10-17 citation, star, and buy-box QA. #96 owns the 2026-10-26 offer rewrite. |

#83 vs #85 is one insertion point. A later resolution is to keep both bullets, referrer-domain note then prompt-loss note. That edit was not applied. #85 still needs a GO before a queue append or a live visibility run, and this pass does not take #85's text onto #83.

#46 vs #96 is not a one-time price disagreement. Both claims logs say one-time $75.00 (`price` 7500) and compare-at $119.98 (`compare_at_price` 11998), with `selling_plan_groups` empty on the 2026-10-16 read. #96's 2026-10-26 note says those figures still matched and that no customer-facing price line changed. The conflict is the ending of the file: #46's QA caveats versus #96's shorter no-claim lines plus that price note. The "no claim" sentences were rewritten on both sides, so this was left unresolved.

#50 vs #96 is a real offer conflict. Both pages are AgeAura Pure NMN + TMG NAD+ Complex, byline Dr. Marcus Hale. The offer text differs:

| | #50 (fetched 2026-10-17) | #96 (product JSON 2026-10-26) |
| --- | --- | --- |
| One-time | $69.95 (`6995`) | $79.99 (`7999`, `compare_at_price` null) |
| Plan | Subscribe & Save 15% every four weeks, plan `9884729659`, Buy 1 $59.46 | Automatic Refill plan `10022551867` every 30 days at 5999, `10022584635` every 60 days at 5499, `10022617403` every 90 days at 4999 |
| Buy box the draft describes | Opens on Kaching "Buy 2 GET 1 FREE" (qty 3): $139.90 one-time or $120.31 subscribe | Card states $59.99/bottle for 1 bottle every 30 days. The 2026-10-17 plan is called removed. |
| Stars on `preview.html` | `4 out of 5` (TrustScore 4.2, 1,144 reviews) | `5 out of 5` (same 4.2 and 1,144) |
| Ingredient bullets | 500 mg NMN and 250 mg TMG per 2-capsule serving, and the extra PDP lines are marked as absent from the OCR front-label file | Same NMN and TMG lines; the OCR-absence sentence is not in the product bullets |

#96 is the source of truth for the AgeAura cents and plan ids it recorded on 2026-10-26. #50 is the source of truth for the Huang / Zhang / Morifuji / Olthof citations, the 4-star graphic, and the 2026-10-17 preselect observation. Those files were not merged.

### Clean pairs (not pushed)

| Pair | `merge-tree` |
| --- | --- |
| #83 vs #96 | Clean. The guidelines file auto-merges. |
| #46 vs #50 | Clean. |
| #98 `ce9ef4c` vs #83, vs #46, and vs #50 | Clean. |
| #104 `a07b1c2` vs #83, vs #46, vs #50, vs #98, vs #85, vs #58, vs #91 | Clean. |
| #83 vs #90 | Clean. The guidelines file auto-merges. |

### #104 vs the drafts it replaces, and vs #96

[#104](https://github.com/tuanquang269/genseo/pull/104) `a07b1c2478582589ee6f6b3fd0dcc37e5987a497` is the reconcile draft (15B, Mike on the blog, Hale on landing and listicle). It was not merged and not modified.

| Pair | Result | Conflict files |
| --- | --- | --- |
| #104 vs #82 `e90976d`, #88 `b622718`, #94 `0762f27` | Conflict | Roster, byline skills, and the blog gate. #104 already combines these three. Do not merge them on top of #104. |
| #104 vs #90 `c3de3b8` | Conflict, 24 files | Rules, roster, runners, `scripts/validate_article.py`, and the Gold Resin / ShilaSource / Shockwave / Turkesterone guard tests. `scripts/florafresh_rules.py` is not in the conflict list. |
| #104 vs #96 `29c6c25` | Conflict, 3 files | `docs/FLORAFRESH_FORMULA_GUARD.md`, `scripts/run_ticket_headless.sh`, `tests/test_florafresh_guard.py` |
| #104 vs #92 `15002fe` | Conflict | `roster.json`, `scripts/genseo_roster.py` |
| #104 vs #93 `c0aebd5` | Conflict | `roster.json`, `scripts/genseo_roster.py`, `scripts/run_ticket_headless.sh` |

The #104 vs #96 hunks, left unresolved:

- Formula guard, one sentence. #104: historical landing drafts that still say 1 billion CFU were not rewritten, and `--spec` on `florafresh-listicle-261009.json` exits 1. #96: this branch rewrote the FloraFresh landing drafts and claims logs to 15B, so `--spec` exits 0.
- `scripts/run_ticket_headless.sh`. #104 has the Mike Moretti blog byline paragraph (roster bio verbatim). #96's side of that hunk is empty.
- `tests/test_florafresh_guard.py`. #104's `test_historical_listicle_now_fails_the_retired_count` expects the 2026-10-09 draft to fail. #96's `test_live_listicle_passes` expects that draft, rewritten to 15B, to pass.

`scripts/florafresh_rules.py` is `CFU = "15B CFU"` on both #104 and #96. The fight is whether old unpublished specs stay at 1 billion CFU and fail the linter (#104) or get rewritten and pass (#96).

## Public JSON read this morning

Read-only GETs. No Admin API. No write.

`https://wellnessnest.co/pages/mike-moretti` returned HTTP 404 at Sat, 31 Oct 2026 09:39:25 GMT. `https://wellnessnest.co/pages/dr-marcus-hale` returned HTTP 200 at the same second. The page was not created. No headshot was added.

`https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.js` at 09:39:25 GMT:

- Title: AgeAura Pure NMN + TMG NAD+ Complex. Variant price `7999`. `compare_at_price` null.
- Automatic Refill plan `10022551867` every 30 days, adjustment `price` 5999.
- Plan `10022584635` every 60 days, adjustment `price` 5499.
- Plan `10022617403` every 90 days, adjustment `price` 4999.

Those cents and plan ids match #96's 2026-10-26 AgeAura note. They do not match #50's $69.95 / plan `9884729659` / $59.46. The product.js payload does not include the Kaching bar, so this read does not say whether the PDP still opens on 3 bottles.

`https://wellnessnest.co/products/turkesterone-advanced-formula.js` at 09:39:25 GMT:

- Variant price `7500`. `compare_at_price` null.
- Automatic Refill plan `10022650171` every 30 days, adjustment `price` 5999.
- Plan `10022682939` every 60 days, adjustment `price` 5499.
- Plan `10022715707` every 90 days, adjustment `price` 4999.

The one-time `7500` still matches #46 and #96. The null compare-at and the three refill plans do not. Both drafts still say compare-at `11998` and empty `selling_plan_groups`. Those lines were not edited.

`https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin.js` at 09:40:45 GMT:

- Variant price `6999`. `compare_at_price` null.
- Plan `10022748475` every 30 days, adjustment `price` 4999.
- Plan `10022781243` every 60 days, adjustment `price` 4499.
- Plan `10022814011` every 90 days, adjustment `price` 3999.
- Plan `9830990139` is not in this payload.

That is the trio #96 already states. The 8-week $56.69 line stays out of customer-facing copy until Kevin confirms the charge. This pass did not search Kaching.

## Recommended land order

Still drafts. This pass does not merge them.

### After #98

#98 stays first. It is the landing-queue suite fix, already on `6c46771` plus one commit, and it merge-trees clean with the three refreshed tips.

Then the #100 steps that do not touch these conflicts, with #83 in its old slot now that it contains `main`:

1. #98.
2. #84, #86, #83. Land #83 without #85.
3. #78, #75, #72, #70, #69, #81, #65, #64, #87.
4. Hold #46 and #50. They are git-clean against `main`, against each other, against #98, and against #104. They still conflict with #96, and the Turkesterone compare-at / refill lines are behind this morning's product.js. Leave both unpublished.
5. #67, #97, #71. After #71 is on `main`, retarget #73 from `cursor/entity-consistency-audit-1020` to `main`, then merge #73. The Organization `sameAs` edit stays a proposal.

When #85 later gets a GO, refresh it onto whatever `main` contains and keep both guidelines bullets. Do not append the queue or run a live visibility pass inside that refresh.

### After #104

#104 replaces #100 steps 20–22's "#88 then the #82/#94 refreshes" as the byline and 15B landing.

1. Land #104. Blog byline is Mike Moretti, with the roster bio copied verbatim. Landing pages and listicles stay Dr. Marcus Hale. FloraFresh is 15B CFU of Bacillus coagulans SNZ-1969 per 2 gummies. AgeAura stays NMN + TMG only. The eight seeded first-hand lines stay off.
2. After that lands, #82, #88, and #94 are close-candidates. They still conflict with #104, so they are superseded rather than merged. This pass does not close them.
3. Leave #90 open. It conflicts with #104 on 24 paths. The piece #104 did not take is the FusiForce and Shilajit gummies guards. Refresh those onto #104 in a later draft. Do not land #90 as it stands.
4. #91 merge-trees clean with #104. Leave it draft. It tracks unpublished 15B FloraFresh drafts. Tracking them is not a publish. A later publish of a Mike draft still needs `/pages/mike-moretti` to return 200.
5. Refresh #96 only after the price decision below. Onto #104, keep #104's formula-guard sentence, keep the test that the historical 1 billion CFU listicle fails `--spec`, and keep the Mike byline paragraph in `scripts/run_ticket_headless.sh`. Leave #96's rewritten FloraFresh specs on #96 until that test choice is explicit. Price lines, when they are copied, come from a fresh product.js read. For Turkesterone, do not copy `11998` or "no selling plan" from either current draft.
6. #58 is clean against #104 and still waits. Merging it registers `.github/workflows/genseo-cloud-failover.yml`.
7. #92 and #93 still conflict with #104 on the roster files. Refresh them onto #104's Mike blog / Hale landing split. They stay in the Kevin-wait set. Plan `9830990139` stays unstated.

## Still needs Kevin

- Create `/pages/mike-moretti` and point it at the roster bio. `headshot` stays null. Do not invent a photo. Hale's page is already HTTP 200, which is why landing and listicle bylines stay Hale.
- Set `rights_confirmed` and `approved_by` on only the first-hand lines that may run. On #104, `templates/first-hand-quotes.json` has eight quotes (`kenzie-086ac23e-*`, `hillary-e16b6841-*`). Every one has `rights_confirmed: false` and `approved_by: ""`. Quotes are AgeAura NMN + TMG only. A Trybe approve is not that permission.
- Name the price source for the unpublished listicles. This morning's product.js matches #96 on AgeAura (`7999` and plans `10022551867` / `10022584635` / `10022617403`) and matches #96's ShilaSource resin trio. Turkesterone one-time `7500` matches both drafts, and the compare-at plus the refill plans have moved since the 2026-10-26 sweep. The 4-star graphic is #50's correction; #96's preview drew five stars for the same 4.2 TrustScore.
- GO on #85 before any prompt-loss queue append or live visibility run.
- #58 failover workflow, #92 refresh questions (byline, the stale reviews-page price, the gummies dose), and #93 FAQ drafts. None of those were edited here.
- After #104 is on `main`, close #82, #88, and #94 as superseded. Not before, and not from this draft.

## Left untouched

#90, #88, #91, #82, #94, #58, #85, #92, #93, #96, #98, #100, #101, #103, and #104 were not pushed. #98 was left draft, as #103 left it. No Shopify publish. No theme file. No paid-traffic page.

# Land-now readiness — 2026-10-31

Report only. Nothing in this pass was merged to `main`. No pull request was closed, retargeted, or marked ready. No branch was force-pushed or rebased. Nothing was published. No theme file, paid-traffic page, or store setting was edited.

`origin/main` is `6c46771de6a11f5719422d94a337215015bec364` ("Publish shilajit loading with food article"). That matches the base of `reports/draft-pr-merge-plan-2026-10-30.md` on draft #100.

The land-now list is steps 1–19 of that plan. This pass did not touch the mike-moretti-gated drafts (#90, #88, #91, #82, #94) or the five wait drafts (#58, #85, #92, #93, #96).

`https://wellnessnest.co/pages/mike-moretti` returned HTTP 404 on 2026-10-31. `https://wellnessnest.co/pages/dr-marcus-hale` returned HTTP 200. `scripts/florafresh_rules.py` on `main` is still `CFU = "1 billion CFU"` and `_LABEL_CFU = 1e9`. The 15B CFU guard stays on #88. Landing bylines were not flipped to Mike Moretti.

## What was updated

Seven land-now branches were behind `main`. `git merge-tree` of `origin/main` into each one was clean, and none of those seven conflict with #58, #85, #92, #93, or #96. Each received one merge commit (`git merge --no-ff origin/main`), was pushed with a normal push, and is still a draft.

| PR | Branch | Previous tip | New tip |
| --- | --- | --- | --- |
| #84 | `cursor/mobile-clutter-audit-1021` | `c6bf852f9635ac28d025432b6b86991196c97782` | `9f9d4de5d8357a797933b801c7f3704a2d7ede5e` |
| #86 | `cursor/brand-serp-slide-1021` | `884977b2e9ed02214579526cbacb32cbe5c69bd5` | `22b66f930df30409bd9a61741a4c5e41eefb139e` |
| #75 | `cursor/offpage-listicle-gap-1020` | `e6b020f0745193f1539c1c7e81237143197d7680` | `396cd02faa2b72c7174b9ca506833541e6cba368` |
| #72 | `cursor/ageaura-ai-mode-gap-map-1020` | `eee58d15beeab3ced46f2a26e7df19980bd50b76` | `c2c03bd8a9dd05cbfd3508e80077c9bd48b5431b` |
| #70 | `cursor/coa-pdf-html-audit-df6a` | `77331d0a86a94e1a3a314d0a82395860c1a1fc06` | `544b0abfffa290c10c31cd442a2bc1db71d4a5ba` |
| #69 | `cursor/geo-direct-deep-content-7b88` | `5f8dbca5be407c395271d633a54d142bf3d188be` | `b8baa228b76afc2c024e083f6b28eae4ab12ca75` |
| #67 | `cursor/canonical-url-gate-3d26` | `56826d4e8636ecbb8c615930647ae7cedeb1d2dd` | `4dc63845131590ce8ca7da7edd1429ef84de051a` |

The other twelve land-now branches were not pushed. Nine already contain `6c46771`. Three were left behind on purpose (see blockers).

## Suite

`bash tests/run_suite.sh` once on `origin/main` at `6c46771`, then once on #98 at `ce9ef4c468c18b64be1209db6be0188329c91b86`. Interpreter `/usr/bin/python3` with Pillow 13.0.0. The two runs were serial. No other draft was suite-tested this pass.

| Tree | Shell | Unittest | Exit |
| --- | --- | --- | --- |
| `main` `6c46771` | 13 pass, 0 fail | 315 tests, 4 failures | 1 |
| #98 `ce9ef4c` | 13 pass, 0 fail | 315 tests, 2 failures | 1 |

Failures on `main`:

1. `test_landing_rotation.OpenQueueTests.test_rebalanced_open_tickets_include_both_priorities` — open queue length 1, test expects at least 7.
2. `test_queue_closures.FreshCheckoutTests.test_tracked_files_close_todays_tickets_without_a_ledger` — expects `pure-shilajit-gold-resin`; the open line is `product=shilajit-shockwave`.
3. `test_packaging_palette.PaletteFiles.test_remaining_pack_shots_match_the_png` — stored FusiForce hex `#97c344`, Pillow 13 remeasure `#9ac547`.
4. `test_packaging_palette.PaletteFiles.test_shilasource_file_is_the_measured_neutral_pack` — stored cluster floats differ from a Pillow 13 remeasure (`0.3505` vs `0.35`, and a later hue `3.3` vs `3.6`).

#98 clears failures 1 and 2. Failures 3 and 4 remain on #98 and are already on `origin/main`. They are this VM's Pillow 13 remeasure of pack shots, not a new regression. The stored palette files were not edited. No `cursor/suite-hermetic-1031` branch was opened.

Palette `FAIL` lines printed while landing tests run are the gate's own log. The unittest summary above is the failure count.

## Land-now table

Order is the #100 plan, steps 1–19. `Behind` is commits on `origin/main` that are not in the branch. `Mergeable` is GitHub's state on 2026-10-31 after the pushes above. Suite notes other than #98 mean the suite was not run on that tip; expect `main`'s four failures unless the row says otherwise.

| PR | Branch | Tip | Mergeable | Behind | Suite | Blockers |
| --- | --- | --- | --- | --- | --- | --- |
| #98 | `cursor/fix-landing-queue-tests-1028` | `ce9ef4c468c18b64be1209db6be0188329c91b86` | MERGEABLE / CLEAN vs `main` | no | ran: shell 13/13; unittest 2 palette failures; both queue tests pass | None for landing onto `main`. Still a draft. Land this first. |
| #84 | `cursor/mobile-clutter-audit-1021` | `9f9d4de5d8357a797933b801c7f3704a2d7ede5e` | MERGEABLE / CLEAN vs `main` | no (main merged this pass) | not run | None vs the wait stack. Read-only mobile clutter audit. |
| #86 | `cursor/brand-serp-slide-1021` | `22b66f930df30409bd9a61741a4c5e41eefb139e` | MERGEABLE / CLEAN vs `main` | no (main merged this pass) | not run | None vs the wait stack. Brand-SERP notes only. |
| #83 | `cursor/ai-referrer-weekly-1021` | `429ac9a2d77ce32319a1cd193378e6f13d5eefe5` | MERGEABLE / CLEAN vs `main` | yes, 35 | not run | Not updated. Conflicts with wait #85 on `knowledge_base/AEO_GEO_GUIDELINES.md`. A merge of `main` into this branch would be clean and would not rewrite that file. Left at the old tip. |
| #78 | `cursor/quarterly-content-audit-78b5` | `bfd51a045618d1605e7139dc9e1587dd1041595d` | MERGEABLE / CLEAN vs `main` | no | not run | None. Already contained `main`. |
| #75 | `cursor/offpage-listicle-gap-1020` | `396cd02faa2b72c7174b9ca506833541e6cba368` | MERGEABLE / CLEAN vs `main` | no (main merged this pass) | not run | None vs the wait stack. Off-page gap list. |
| #72 | `cursor/ageaura-ai-mode-gap-map-1020` | `c2c03bd8a9dd05cbfd3508e80077c9bd48b5431b` | MERGEABLE / CLEAN vs `main` | no (main merged this pass) | not run | None vs the wait stack. AgeAura in the map is NMN + TMG. Urolithin strings are flagged crawl quotes, not a new SKU. |
| #70 | `cursor/coa-pdf-html-audit-df6a` | `544b0abfffa290c10c31cd442a2bc1db71d4a5ba` | MERGEABLE / CLEAN vs `main` | no (main merged this pass) | not run | None vs the wait stack. Read-only COA audit. |
| #69 | `cursor/geo-direct-deep-content-7b88` | `b8baa228b76afc2c024e083f6b28eae4ab12ca75` | MERGEABLE / CLEAN vs `main` | no (main merged this pass) | not run | None vs the wait stack. GEO traffic report. |
| #81 | `cursor/ai-visibility-mention-citation-1020` | `a2c8b056c207464ce4df1a6dd0123e1b8044c3d4` | MERGEABLE / CLEAN vs `main` | no | not run | None. Already contained `main`. Shares `knowledge_base/AEO_GEO_GUIDELINES.md` with #85 and merge-tree against #85 is clean. A Urolithin-only mention does not count as AgeAura. |
| #65 | `cursor/geo-delta-audit-6434` | `e2984fb96471d24d07109af557a9c349e61a5890` | MERGEABLE / CLEAN vs `main` | no | not run | None. Already contained `main`. `scripts/apply_geo_live_fixes.py` stays a dry run unless `--apply` is passed, and that path does not call the Shopify Admin API. |
| #64 | `cursor/boot-catchup-8034` | `63482afa293bf08f48a06c286b7678935f0f6ec8` | MERGEABLE / CLEAN vs `main` | no | not run | None. Already contained `main`. Opt-in catch-up plist under `deploy/`. The script does not call `launchctl`. |
| #87 | `cursor/striking-faq-1021` | `6679085cc21825aa9d5f90808aed82ab745ffe12` | MERGEABLE / CLEAN vs `main` | no | not run | Already contained `main`. Four proposal docs. They do not update live posts. Applying a block still waits on `/pages/mike-moretti` (404 today). The birth-control proposal names SNZ-1969 at 15B CFU per 2 gummies and uses the Mike Moretti byline. Not in the gated set (#90 / #88 / #91 / #82 / #94). |
| #46 | `cursor/turkesterone-listicle-qa-91b6` | `22773f70213e41977cb0ad969daced6b20896964` | MERGEABLE / CLEAN vs `main` | yes, 100 | not run | Not updated. Conflicts with wait #96 on `landing_drafts/turkesterone-listicle-261016.claims.md`. The claims file states a 2026-10-16 PDP price ($75.00 / compare-at $119.98). A merge of `main` would be clean and would not rewrite that claims file (only a docstring in `scripts/validate_landing.py` auto-merges). Left at the old tip. Leave the listicle unpublished. |
| #50 | `cursor/ageaura-listicle-qa-55fe` | `4a3684dec18f69de98ac456dd013de9419f4ebe4` | MERGEABLE / CLEAN vs `main` | yes, 81 | not run | Not updated. Conflicts with wait #96 on `landing_drafts/ageaura-nmn-tmg-listicle-261017.claims.md`, the spec JSON, `body.html`, and `preview.html`. Those files quote 2026-10-17 buy-box prices, including the preselected 3-bottle offer. A merge of `main` would be clean and would not rewrite those four files. Left at the old tip. NMN + TMG only. Leave the page unpublished. |
| #67 | `cursor/canonical-url-gate-3d26` | `4dc63845131590ce8ca7da7edd1429ef84de051a` | MERGEABLE / CLEAN vs `main` | no (main merged this pass) | not run | None vs the wait stack. Canonical check before publish, plus the 2026-10-19 crawl record. |
| #97 | `cursor/validator-429-unverified-1027` | `d088ccb3ed275fc0d61a0847a208bc2d6b32f286` | MERGEABLE / CLEAN vs `main` | no | not run | None. Already contained `main`. A Shopify HTTP 429 on the draft dead-link check stays `UNVERIFIED` (exit 3). Exit 0 is still the only pass. |
| #71 | `cursor/entity-consistency-audit-1020` | `bebea7a1b1408eca21b7f28d61fa3063a730d0db` | MERGEABLE / CLEAN vs `main` | no | not run | None vs the wait stack. Already contained `main`. Does not edit `scripts/florafresh_rules.py`. Land this on `main` before retargeting #73. |
| #73 | `cursor/seo-entity-fixes-1020` | `8be49f663461df365b86a9b584481db8d3bc9d54` | MERGEABLE / CLEAN vs base `cursor/entity-consistency-audit-1020` | no (`main` is an ancestor; GitHub base is #71, not `main`) | not run | Do not retarget to `main` until #71 is on `main`. `git merge-tree` of this head onto `main` is clean. The diff has no theme file. Organization `sameAs` stays a proposal in the PR body. |

## Left untouched

| PR | Why it was not updated |
| --- | --- |
| #90, #88, #91 | Steps 20–22. Wait on `/pages/mike-moretti` (still 404). #88 is the current 15B CFU guard and the Mike Moretti blog default. Hale stays the landing byline. |
| #82, #94 | Mike-gated refreshes. Draft #102 already recorded a refresh. Both contain #88, so merging either to `main` would land the 15B guard and the Mike blog default before the author page exists. Not pushed again. |
| #58, #85, #92, #93, #96 | Wait for Kevin. Failover workflow, prompt-loss GO, byline/dose/ShilaSource plan `9830990139`, FAQ drafts, and product-JSON vs vault price source. Plan `9830990139` stays unstated. |
| #95, #77 | Refresh steps 23–24, not in steps 1–19. Draft #102 already merged `main` into them. Not pushed again. #95 still carries `main`'s `1 billion CFU` line. The 15B guard is #88. |
| #89, #68, #99, #1, #9, #10, #38 | Not in the land-now prefix. #1 stays on the theme / IndexNow hold. |

## Still the land order

When these drafts are actually merged, keep #100's order. This pass did not merge any of them.

1. #98 first (queue tests).
2. Then #84, #86, #78, #75, #72, #70, #69, #81, #65, #64, #87, #67, #97, #71.
3. Hold #83 until the `knowledge_base/AEO_GEO_GUIDELINES.md` conflict with #85 is resolved without taking the #85 GO.
4. Hold #46 and #50 until the price source for those two unpublished listicles is chosen. They conflict with #96. Landing them before a #96 refresh is what #100 recommends, and that is a price decision, so they were not brought onto `main` here.
5. After #71 is on `main`, retarget #73 from `cursor/entity-consistency-audit-1020` to `main`, then merge #73. Not done here.
6. Steps 20–22 (#90, then #88, then #91) stay behind the author-page decision.

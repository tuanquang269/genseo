# DRAFT — open-draft merge order — 2026-10-30

Report only. This pull request adds this file and nothing else. It does not merge, close, or retarget any other pull request. It does not publish, and it does not edit a theme file or a paid-traffic page.

GitHub `main` for this plan is `6c46771de6a11f5719422d94a337215015bec364` ("Publish shilajit loading with food article"). Every open draft still targets that commit, except #73, whose base is #71's branch. Each draft is individually `MERGEABLE` / `CLEAN` against its base (queried 2026-10-30). The work below is the combined order.

The local `main` checkout on this Mac is 33 commits ahead of `origin/main` and has uncommitted files. Those commits are the Cherish lane and were not pushed. The suite and the merge simulation used `origin/main`. This branch is cut from `origin/main`.

## Recommended order

`git merge-tree` applied this exact sequence onto `origin/main` with zero conflicts. Steps 1–19 leave the FloraFresh guard and the blog byline gate as they are on `main`. Steps 20–22 are also git-clean, and they are the steps that install the 15B CFU guard and the Mike Moretti blog default. Wait on the author-page decision before step 20.

`main` still has `CFU = "1 billion CFU"` and `_LABEL_CFU = 1e9` in `scripts/florafresh_rules.py`. The current correction is #88. #90 carries an older copy of that correction plus the FusiForce and shilajit-gummies label guards. Landing #90 and then #88 keeps both.

### Steps 1–19 — clean, no product decision

1. **#98** `ce9ef4c468c1` — Point the two landing-queue tests at the open Shockwave ticket. This is the suite fix. Land it before any refresh of #95.
2. **#84** `c6bf852f9635` — Read-only mobile clutter audit for blog articles.
3. **#86** `884977b2e9ed` — Brand-SERP defence notes for the 2026-10-21 position slide.
4. **#83** `429ac9a2d77c` — Weekly AI referrer report by domain.
5. **#78** `bfd51a045618` — Read-only quarterly news-blog content audit.
6. **#75** `e6b020f07451` — Off-page listicle gap list for AgeAura and ShilaSource.
7. **#72** `eee58d15beea` — AgeAura follow-up gap map. The map's product rule is AgeAura Pure NMN + TMG NAD+ Complex. Crawl excerpts that mention Urolithin are flagged as claims to verify, and the doc says not to copy them into a new heading.
8. **#70** `77331d0a86a9` — Read-only audit of PDF COAs versus crawlable HTML.
9. **#69** `5f8dbca5be40` — Direct-to-deep-content sessions on the GEO traffic report.
10. **#81** `a2c8b056c207` — Record AI mentions and citations separately. A Urolithin-only mention does not count as AgeAura.
11. **#65** `e2984fb96471` — Post-gate GEO scores and a prepared fix file. `scripts/apply_geo_live_fixes.py` defaults to a dry run, writes under `docs/geo-live-fixes-out/` only with `--apply`, and does not call the Shopify Admin API.
12. **#64** `63482afa293b` — Opt-in login catch-up for a missed morning slot. The plist lives in `deploy/`. Self-apply does not install it, and the script does not call `launchctl` or pass `--live`.
13. **#87** `6679085cc218` — Striking-distance FAQ proposals. The birth-control block uses Bacillus coagulans SNZ-1969, 15B CFU per 2 gummies, and the byline on the proposals is Mike Moretti. Merging the four docs does not update the live posts. Applying a block still waits on a live `/pages/mike-moretti`.
14. **#46** `22773f70213e` — QA for the unpublished Turkesterone listicle (`gsl-preview-turkesterone-listicle-261016`). Leave it unpublished.
15. **#50** `4a3684dec18f` — QA for the unpublished AgeAura NMN + TMG listicle (`gsl-preview-ageaura-nmn-tmg-listicle-261017`). The claims log records that the PDP buy box opens on the Kaching bar "Buy 2 GET 1 FREE". This PR does not change Kaching bindings. Leave the page unpublished. Land it before any later refresh of #96 so the Huang / star / offer corrections survive that refresh.
16. **#67** `56826d4e8636` — Canonical URL check before publish, plus the 2026-10-19 crawl record.
17. **#97** `d088ccb3ed27` — A Shopify HTTP 429 on the draft dead-link check is `UNVERIFIED` and exits 3. Exit 0 stays the only pass. A 404 or 410 still exits 1.
18. **#71** `bebea7a1b140` — Entity consistency audit and canonical name map. FloraFresh in that map is 15B CFU of SNZ-1969. Merge #71 to `main` before retargeting #73.
19. **#73** `8be49f663461` — One Article JSON-LD block per article. GitHub's base is `cursor/entity-consistency-audit-1020`, not `main`. The head contains #71, is 0 commits behind `main`, and merge-tree onto `main` is clean. After #71 is on `main`, retarget #73 to `main` and merge it. The Organization `sameAs` theme edit is a proposal in the PR body. The diff does not change a theme file.

Steps 2–15 share little with each other. This exact order is the one that was simulated. #67, #71, and #97 all edit `scripts/validate_article.py` and still merged clean in this order.

### Steps 20–22 — git-clean, wait on `/pages/mike-moretti`

`https://wellnessnest.co/pages/mike-moretti` was HTTP 404 on 2026-10-21 (#88) and again while #87 was edited. `https://wellnessnest.co/pages/dr-marcus-hale` was HTTP 200. #88 makes Mike Moretti the blog default and rejects a Dr. Marcus Hale blog byline. Hale stays on `roster.json` for landing pages. The publisher's live-URL check is unchanged, so a new Mike draft fails that check until the page returns 200.

Kevin's decision before step 20: create `/pages/mike-moretti`, or accept that new blog drafts fail closed until that page exists. The 15B CFU guard ships in the same two pulls. There is no separate current draft that changes only the guard.

20. **#90** `4386e4863be9` — Port of the FusiForce and shilajit-gummies label guards onto current rule files, on top of an older #88. Merge this before #88. The reverse order conflicts on `daily-landing-tickets.md` only.
21. **#88** `b6227188efc2` — Current FloraFresh guard (`CFU = "15B CFU"`, `_LABEL_CFU = 15e9`) and the Mike Moretti blog byline. #88 was refreshed onto today's `main` after #90 was cut, so #88 is not an ancestor of #90. Both pulls are required. #90 then #88 is clean.
22. **#91** `ade6dd72ad7e` — Tracked copies of four FloraFresh drafts that had been only on the Mac checkout, plus the sixteen files from #89. Count is 15 billion CFU of SNZ-1969 per 2 gummies. Blog byline is Mike Moretti. Publishing those drafts waits on the author page.

### Refresh after the clean sequence

These conflict with the 22-pull tree. The conflict is textual. The resolution rule is below. Leave the pulls open until the refresh exists.

23. **#95** `e2dea61028c0` — After #98. Conflicts on `tests/test_landing_rotation.py` and `tests/test_queue_closures.py` in either order. Keep #98's Shockwave assertions on those two files. Take #95's process-list fixtures in `scripts/genseo_self_apply.sh`, `scripts/genseo_sync_main.sh`, `tests/test_self_apply.sh`, and `tests/test_sync_main.sh`. Those four auto-merge with #64, which is already in the tree. #95 can be refreshed as soon as #98 is in, without waiting for steps 20–22.
24. **#77** `fa9e5659022b` — After #71 and #97. One conflict: `scripts/validate_article.py`. Keep the entity checks and the 429 `UNVERIFIED` exit 3. Add the warn-only near-duplicate cluster gate.
25. **#82** `61c7574680c0` — After #88. Conflicts on `scripts/validate_article.py`, `skills/genseo-auto-publish/SKILL.md`, and `skills/genseo-content-writer/SKILL.md`. This is the rights-gated first-hand block. Seeded quotes stay off unless `rights_confirmed` and `approved_by` are set. Keep #88's Hale-blog rejection, #97's 429 behavior, and #71 / #67's validator edits.
26. **#94** `bd8b4734212e` — After #88 and #97, and after the same author-page decision as step 20. Eight conflicts: `DAILY-RUN.md`, `daily-tickets.md`, `roster.json`, `scripts/genseo_roster.py`, `scripts/refill_tickets.py`, `scripts/validate_article.py`, `skills/genseo-auto-publish/SKILL.md`, `skills/genseo-content-writer/SKILL.md`. #94 adds Mike's verbatim bio and a null headshot, and its gate still accepts a Dr. Marcus Hale blog byline. Keep #88's rule that a Hale blog byline fails. Take #94's bio sentence and null headshot where they match that rule. Landing pages stay on Hale.

### Wait for Kevin — do not merge these yet

| PR | Head | Why it waits | Conflict against the 22-pull tree |
| --- | --- | --- | --- |
| #58 | `6813af4b97cf` | Author asked to wait. Merging registers `.github/workflows/genseo-cloud-failover.yml` (18:30 and 22:00 ICT plus `workflow_dispatch`). The job skips unless the repo variable `GENSEO_CLOUD_FAILOVER` is `1`. The script fail-closes and does not publish. | Clean. The wait is the workflow registration, not a conflict. |
| #85 | `88457b2351e8` | PR says a queue append or a live visibility run still needs a GO. The script refuses to write `daily-tickets.md`. | `knowledge_base/AEO_GEO_GUIDELINES.md` (shared with #83). |
| #92 | `15002fea894a` | Open questions in the two claims logs: Mike Moretti versus the roster byline, a stale $59.99 on the reviews page, and a gummies dose conflict. The claims log also records ShilaSource selling plan `9830990139`, group "Delivery every 8 weeks", allocation price 5669 ($56.69). Charge semantics are not decided. | `roster.json`, `scripts/genseo_roster.py`. |
| #93 | `c0aebd5aeb7d` | FAQ refresh drafts for three live URLs. The branch also carries a second copy of the 15B rule edits. Keep the seventeen files under `drafts/gsc-2026-10-24/` when this is refreshed. The birth-control and period drafts name SNZ-1969 and do not state a CFU count. Nothing in this plan publishes them. | Sixteen files, listed in the matrix below. |
| #96 | `29c6c2556cbe` | Unpublished landing prices were aligned to public product JSON fetched 2026-10-26. The vault pack table is still the other candidate source of truth. The sweep states ShilaSource Automatic Refill at $49.99 / $44.99 / $39.99 (plans `10022748475` / `10022781243` / `10022814011`) and explicitly leaves plan `9830990139` ($56.69, 8-week) unstated. Kaching charge semantics for that plan are still open. #96 also ports the 15B guard; `scripts/florafresh_rules.py` auto-merges, the guard doc and tests do not. | Twenty files once #46 and #50 are in the tree, including the AgeAura `261017` listicle and `landing_drafts/turkesterone-listicle-261016.claims.md`. |

When #96 is eventually refreshed: keep #88 / #90's FloraFresh guard bytes, keep #46 and #50's non-price QA, and write a price only from the source Kevin names. Leave plan `9830990139` out of customer-facing copy until the 8-week $56.69 charge is confirmed.

## What changed from the earlier rough order

An earlier pass suggested roughly **#95 → #84 → #86 → #83 → #90 → #94 → #82 → #91 → #87**, then holds on **#85, #92, #93, #96**.

Re-simulated against today's heads:

- #95 first collides with #98. Both orders conflict on the two landing-queue tests. #98 matches the open Shockwave line (2026-10-28). #95 freezes an older rebalance snapshot and also fixes the self-apply / sync-main process list. Keep both jobs by landing #98 and refreshing #95, as in step 23.
- #84, #86, #83, and #87 still belong in the clean prefix. They moved only because #98, #97, and the audits around them were included.
- #90 still belongs before the byline work, and it must be **before #88**, not after a separate #94. #88 was merged forward to `6c46771` on 2026-10-28 (`b622718`). #90 does not contain that merge. #90 then #88 is clean. #88 then #90 conflicts on `daily-landing-tickets.md`.
- #94 and #82 cannot sit in the same clean batch as #88. Both orders conflict. They are refreshes (steps 25 and 26), not clean merges.
- #91 still follows the guard, and it still covers #89.
- Holds #85, #92, #93, and #96 are unchanged as decisions. Their conflict lists are longer once #88, #90, #46, and #50 are in the tree.
- #97 joins the clean prefix. It conflicts with #94 only, so it lands before the #94 refresh.
- #99 is the 2026-10-28 readiness snapshot (`reports/draft-pr-readiness-2026-10-28.md`). It merges clean and is not part of this code order. This file replaces that snapshot as the active plan.

## Supersession and close-candidates

Leave every pull open. Nothing was closed.

| Pull | Relation | When it becomes a close-candidate |
| --- | --- | --- |
| #89 `ae39ad2e80f1` | The single commit is an ancestor of #91. Sixteen `published_drafts/` files. #91 adds four more: `are-vaginal-probiotics-worth-it-how-much-2026.md`, `vaginal-probiotics-empty-stomach-us-2026.md`, `vaginal-probiotics-on-an-empty-stomach-us-2026.md`, `where-to-buy-vaginal-probiotics-in-the-us-5-checks-2026.md`. Merging #89 after #91 is an empty merge. | After #91 is on `main`. |
| #68 `b3b416a83d13` | Earlier evidence-only experience block (`scripts/experience_block.py`). #82 is the later rights-gated block (`scripts/first_hand_experience.py`). They conflict on `scripts/validate_article.py`. Against the 22-pull tree, #68's remaining conflict is `scripts/shopify_publisher.py` (from #67 and #73). | If #82 is the block that should ship. A refresh of #68 is a second design, not a leftover commit. |
| #9 `ad0cebfaa96d`, #10 `d7fb719589ce` | Open, not drafts, both `CONFLICTING` with `main`. #90 is the port onto current rule files. `scripts/shilajit_gummies_rules.py` is the same blob on #10 and #90 (`1755cca4aa`). `scripts/fusiforce_rules.py` differs (26 lines between #9 and #90). Both test files differ. Merging #9 or #10 on top of #90 still conflicts across the shared rule files those branches last edited when they were ~156 commits behind. | After #90 is accepted as the port. Leave them open until then. |
| #99 `1af4fc8a8ae5` | Readiness report from 2026-10-28. One new file. Clean against the 22-pull tree. | After this 2026-10-30 plan is the copy you keep. The file itself does not collide with this report. |

#88 is not a close-candidate. #90 does not contain #88's 2026-10-28 merge of `main`.

#95 is not a close-candidate. The process-list test fixes are only on #95.

#98 is not a close-candidate. It is the landing-queue fix.

## File-overlap matrix

34 open drafts. 96 pairs share at least one path. Pairwise `git merge-tree` of those pairs, each order, onto a merge of `main` plus the first pull:

- 73 pairs auto-merge in both orders.
- 22 pairs conflict in both orders.
- 1 pair conflicts in one order only: **#88 then #90** conflicts on `daily-landing-tickets.md`. **#90 then #88** is clean.

Sharing a path is not a conflict. The rows below are the conflicts that remain if the 22-pull sequence lands and the later pull is merged as-is.

| Later pull | Files that conflict with the 22-pull tree |
| --- | --- |
| #95 | `tests/test_landing_rotation.py`, `tests/test_queue_closures.py` |
| #77 | `scripts/validate_article.py` |
| #82 | `scripts/validate_article.py`, `skills/genseo-auto-publish/SKILL.md`, `skills/genseo-content-writer/SKILL.md` |
| #94 | `DAILY-RUN.md`, `daily-tickets.md`, `roster.json`, `scripts/genseo_roster.py`, `scripts/refill_tickets.py`, `scripts/validate_article.py`, `skills/genseo-auto-publish/SKILL.md`, `skills/genseo-content-writer/SKILL.md` |
| #92 | `roster.json`, `scripts/genseo_roster.py` |
| #68 | `scripts/shopify_publisher.py` |
| #85 | `knowledge_base/AEO_GEO_GUIDELINES.md` |
| #93 | `.cursor/rules/genseo-landing-lane.mdc`, `docs/LABEL_OCR_GATE.md`, `knowledge_base/AEO_GEO_GUIDELINES.md`, `roster.json`, `scripts/brand_rules.py`, `scripts/genseo_roster.py`, `scripts/llms_formula.py`, `scripts/run_landing_headless.sh`, `scripts/run_ticket_headless.sh`, `skills/genseo-auto-publish/SKILL.md`, `templates/landing/listicle-angles.json`, `tests/test_gold_resin_guard.py`, `tests/test_packaging_palette.py`, `tests/test_shilasource_resin_guard.py`, `tests/test_shockwave_guard.py`, `tests/test_turkesterone_guard.py` |
| #96 | `.cursor/rules/genseo-landing-lane.mdc`, `docs/FLORAFRESH_FORMULA_GUARD.md`, `docs/LABEL_OCR_GATE.md`, `knowledge_base/AEO_GEO_GUIDELINES.md`, `landing_drafts/ageaura-nmn-tmg-listicle-261017.claims.md`, `landing_drafts/ageaura-nmn-tmg-listicle-261017.json`, `landing_drafts/ageaura-nmn-tmg-listicle-261017/body.html`, `landing_drafts/ageaura-nmn-tmg-listicle-261017/preview.html`, `landing_drafts/turkesterone-listicle-261016.claims.md`, `scripts/brand_rules.py`, `scripts/llms_formula.py`, `scripts/run_landing_headless.sh`, `scripts/run_ticket_headless.sh`, `skills/genseo-auto-publish/SKILL.md`, `templates/landing/listicle-angles.json`, `tests/test_florafresh_guard.py`, `tests/test_gold_resin_guard.py`, `tests/test_shilasource_resin_guard.py`, `tests/test_shockwave_guard.py`, `tests/test_turkesterone_guard.py` |

Hottest path in that matrix: `scripts/validate_article.py` (#77, #82, #94, and already edited inside the prefix by #67, #71, #97, #88, #90).

Path counts that look large and mostly auto-merge: #88 and #90 share 47 paths and conflict in only one order, on one file. #89 and #91 share 16 paths because #89 is contained in #91.

## Suite baseline

Ran once on 2026-10-30, in a detached worktree of `origin/main` at `6c46771`, so the dirty local checkout was not the tree under test.

```
bash tests/run_suite.sh
```

- Interpreter: `/usr/bin/python3` (numpy and PIL).
- Shell files: `SH_FILES pass=13 fail=0`.
- Unittest: `Ran 315 tests` in 7.732s, `FAILED (failures=2)`, then `PY_FAIL`.
- Suite exit: 1.

The two failures:

1. `test_landing_rotation.OpenQueueTests.test_rebalanced_open_tickets_include_both_priorities` — `assertGreaterEqual(len(open_lines), 7)` got 1.
2. `test_queue_closures.FreshCheckoutTests.test_tracked_files_close_todays_tickets_without_a_ledger` — expected `pure-shilajit-gold-resin` in the first open landing line. The open line is `product=shilajit-shockwave` (added 2026-10-26).

#98 is the fix for those two assertions. #95 rewrites the same two tests to a frozen rebalance record instead. Palette-gate `FAIL` lines in the suite log are printed by landing tests while they run. The unittest summary records only the two failures above.

The suite was not re-run on each draft. #99's 2026-10-28 note still describes per-draft runs against this same `main` SHA: every combined tree they measured kept this two-failure baseline, and #95's own suite was green because it changes the two tests.

## Hard rules checked on the diffs

- FloraFresh count to keep when resolving a conflict: **15B CFU** of Bacillus coagulans SNZ-1969 per 2 gummies. "15 billion CFU" is the same count. "1 billion CFU" / "1B CFU" is the retired count. Trial doses that are actually 1 billion CFU of a different organism (the pregnancy-study capsule in #89 / #91) stay described as that study.
- Blog byline to keep: **Mike Moretti**, role `Co-founder, Wellness Nest`. A Dr. Marcus Hale blog byline fails once #88 is in. Landing and listicle bylines stay Dr. Marcus Hale.
- AgeAura copy that should ship names **NMN + TMG** only. Diffs that contain the string "urolithin" are guards, audits, or crawl quotes (#1, #72, #75, #81, #68, #82), not a new Urolithin SKU.
- No open draft's file list includes `theme/`, a section, a layout, or a product/collection template. #73's theme `sameAs` change is unapplied. #96 and #46 / #50 edit unpublished landing drafts.
- This pass did not publish, did not merge to `main`, did not force-push, and did not close a pull request.

## How this was simulated

- `gh pr list` for every open pull request on `tuanquang269/genseo`, 2026-10-30.
- `git fetch` of each head. Local `origin/<branch>` matches the GitHub head SHA for all 38 open pulls (34 drafts plus #1, #9, #10, #38).
- `git merge-tree --write-tree` from `origin/main`. A clean result was stored with `git commit-tree` as a dangling commit and the next pull was merged onto that. No branch was moved. Conflict paths are the paths `merge-tree` printed before `CONFLICT`.

## Open pulls that are not drafts

Out of the draft train. Listed because #90 names #9 and #10, and #1 is the IndexNow hold.

| PR | Head | GitHub | Merge-tree vs `origin/main` |
| --- | --- | --- | --- |
| #1 IndexNow and `llms.txt` | `e4982bd433d5` | `CONFLICTING` | `deploy/llms-txt/README.md`, `deploy/llms-txt/llms.txt`, `scripts/shopify_publisher.py` |
| #9 FusiForce label guard | `ad0cebfaa96d` | `CONFLICTING` | Fifteen shared rule/skill files. See close-candidate note. |
| #10 Shilajit gummies label guard | `d7fb719589ce` | `CONFLICTING` | Sixteen shared rule/skill files. See close-candidate note. |
| #38 Mac Mini failover bootstrap | `4a475e62bbc4` | `CONFLICTING` | `.cursor/rules/genseo-operating-rules.mdc`, `deploy/com.pati.genseo-landing.mini.plist`, `scripts/mac_return_reconcile.sh` |

#1 stays on the theme / IndexNow GO. The publisher ping is env-gated, and the PR does not upload a theme. It still conflicts with current `main`, so it is not in this order.

## Inventory

Drafts only. `Files` is `git diff --name-only <base>...<head>` against the pull's GitHub base. Full paths are in the appendix. Every row was `MERGEABLE` / `CLEAN` on 2026-10-30.

| PR | Head | Base | Files | Place in this plan |
| --- | --- | --- | --- | --- |
| #46 | `22773f70213e41977cb0ad969daced6b20896964` | main | 10 | Step 14 |
| #50 | `4a3684dec18f69de98ac456dd013de9419f4ebe4` | main | 6 | Step 15 |
| #58 | `6813af4b97cf5d51e5dff122585c313a780e88c6` | main | 4 | Wait. Workflow registration. Git-clean. |
| #64 | `63482afa293bf08f48a06c286b7678935f0f6ec8` | main | 7 | Step 12 |
| #65 | `e2984fb96471d24d07109af557a9c349e61a5890` | main | 7 | Step 11 |
| #67 | `56826d4e8636ecbb8c615930647ae7cedeb1d2dd` | main | 12 | Step 16 |
| #68 | `b3b416a83d13c562f51fde70a4d894d142ab21c7` | main | 16 | Close-candidate if #82 ships |
| #69 | `5f8dbca5be407c395271d633a54d142bf3d188be` | main | 3 | Step 9 |
| #70 | `77331d0a86a94e1a3a314d0a82395860c1a1fc06` | main | 5 | Step 8 |
| #71 | `bebea7a1b1408eca21b7f28d61fa3063a730d0db` | main | 7 | Step 18 |
| #72 | `eee58d15beeab3ced46f2a26e7df19980bd50b76` | main | 5 | Step 7 |
| #73 | `8be49f663461df365b86a9b584481db8d3bc9d54` | #71's branch | 11 | Step 19, after retarget |
| #75 | `e6b020f0745193f1539c1c7e81237143197d7680` | main | 6 | Step 6 |
| #77 | `fa9e5659022bba30395a0aa6013260835843774c` | main | 5 | Refresh, step 24 |
| #78 | `bfd51a045618d1605e7139dc9e1587dd1041595d` | main | 5 | Step 5 |
| #81 | `a2c8b056c207464ce4df1a6dd0123e1b8044c3d4` | main | 11 | Step 10 |
| #82 | `61c7574680c00b1b87f900b1a23b1657bd67f7a9` | main | 10 | Refresh, step 25 |
| #83 | `429ac9a2d77ce32319a1cd193378e6f13d5eefe5` | main | 8 | Step 4 |
| #84 | `c6bf852f9635ac28d025432b6b86991196c97782` | main | 9 | Step 2 |
| #85 | `88457b2351e8847f1245d7fd050879657b1fd5f1` | main | 7 | Wait for GO |
| #86 | `884977b2e9ed02214579526cbacb32cbe5c69bd5` | main | 6 | Step 3 |
| #87 | `6679085cc21825aa9d5f90808aed82ab745ffe12` | main | 4 | Step 13 |
| #88 | `b6227188efc2e74ea9b02ff23e429c752ade9fe2` | main | 47 | Step 21, after the author-page decision |
| #89 | `ae39ad2e80f151ee8f1ee53c8a53e05bceaa2bd3` | main | 16 | Close-candidate after #91 |
| #90 | `4386e4863be9bdb48feeca69bd1acb52c87989a3` | main | 58 | Step 20, before #88 |
| #91 | `ade6dd72ad7e0620d0787c3bed2ee940cc42be87` | main | 20 | Step 22 |
| #92 | `15002fea894a7f5357c2da8496d513fa5cbfa0f4` | main | 6 | Wait. Price, dose, byline, 8-week plan |
| #93 | `c0aebd5aeb7d129e3a8c4d3d4828291c49b5fa69` | main | 57 | Wait. Refresh the FAQ drafts onto #88 / #90 |
| #94 | `bd8b4734212ece71e9582dab3c509c72c79a7a9f` | main | 11 | Refresh, step 26, same author-page decision |
| #95 | `e2dea61028c045e0dfc285acd0dd8a7877d39805` | main | 6 | Refresh, step 23, after #98 |
| #96 | `29c6c2556cbe9c82154fafa87a749edb6e1a1469` | main | 105 | Wait. Price source of truth and the 8-week plan |
| #97 | `d088ccb3ed275fc0d61a0847a208bc2d6b32f286` | main | 2 | Step 17 |
| #98 | `ce9ef4c468c18b64be1209db6be0188329c91b86` | main | 2 | Step 1 |
| #99 | `1af4fc8a8ae59232934af61872b13d6279c18219` | main | 1 | Prior readiness snapshot. Not in the code order |

## Appendix — files touched

Paths are relative to each pull's base. #73's base is #71, so those 11 paths are the SEO-fix diff, not the entity-audit diff. The last four headings are the open non-drafts (#1, #9, #10, #38).

### #46 `22773f70213e41977cb0ad969daced6b20896964` — Fix the unpublished Turkesterone listicle draft (2026-10-16)
Base `main` · branch `cursor/turkesterone-listicle-qa-91b6` · 10 files
- `landing_drafts/turkesterone-listicle-261016.QA.md`
- `landing_drafts/turkesterone-listicle-261016.claims.md`
- `landing_drafts/turkesterone-listicle-261016.json`
- `landing_drafts/turkesterone-listicle-261016/body.html`
- `landing_drafts/turkesterone-listicle-261016/desktop.jpg`
- `landing_drafts/turkesterone-listicle-261016/mobile.jpg`
- `landing_drafts/turkesterone-listicle-261016/preview.html`
- `landing_drafts/turkesterone-listicle-261016/qa.json`
- `scripts/validate_landing.py`
- `tests/test_landing_pack_listing.py`

### #50 `4a3684dec18f69de98ac456dd013de9419f4ebe4` — Fix AgeAura NMN listicle claims, stars, and the offer the PDP opens on
Base `main` · branch `cursor/ageaura-listicle-qa-55fe` · 6 files
- `landing_drafts/ageaura-nmn-tmg-listicle-261017.claims.md`
- `landing_drafts/ageaura-nmn-tmg-listicle-261017.json`
- `landing_drafts/ageaura-nmn-tmg-listicle-261017/body.html`
- `landing_drafts/ageaura-nmn-tmg-listicle-261017/preview.html`
- `scripts/landing_clone.py`
- `tests/test_landing_stars.py`

### #58 `6813af4b97cf5d51e5dff122585c313a780e88c6` — Add a disabled off-Mac heartbeat for the article lane
Base `main` · branch `cursor/cloud-failover-scaffold-2d90` · 4 files
- `.github/workflows/genseo-cloud-failover.yml`
- `docs/CLOUD_FAILOVER_FEASIBILITY.md`
- `scripts/genseo_cloud_failover.py`
- `tests/test_cloud_failover.py`

### #64 `63482afa293bf08f48a06c286b7678935f0f6ec8` — Opt-in login catch-up for morning slots missed while powered off
Base `main` · branch `cursor/boot-catchup-8034` · 7 files
- `.cursor/rules/genseo-operating-rules.mdc`
- `DAILY-RUN.md`
- `deploy/com.pati.genseo-catchup.plist`
- `scripts/genseo_boot_catchup.py`
- `scripts/genseo_self_apply.sh`
- `tests/test_boot_catchup.sh`
- `tests/test_catchup_decision.py`

### #65 `e2984fb96471d24d07109af557a9c349e61a5890` — Score post-gate articles and prepare live GEO fixes
Base `main` · branch `cursor/geo-delta-audit-6434` · 7 files
- `.gitignore`
- `docs/GEO_DELTA_AUDIT_2026-10-19.md`
- `docs/geo-live-fixes-2026-10-19.json`
- `scripts/apply_geo_live_fixes.py`
- `scripts/geo_citability.py`
- `tests/test_apply_geo_live_fixes.py`
- `tests/test_geo_citability.py`

### #67 `56826d4e8636ecbb8c615930647ae7cedeb1d2dd` — Check canonical URLs before publish and record the 2026-10-19 crawl
Base `main` · branch `cursor/canonical-url-gate-3d26` · 12 files
- `docs/canonical-audit-2026-10-19.json`
- `docs/canonical-audit-2026-10-19.md`
- `knowledge_base/AEO_GEO_GUIDELINES.md`
- `scripts/canonical_audit.py`
- `scripts/canonical_urls.py`
- `scripts/geo_citability.py`
- `scripts/geo_official_lint.py`
- `scripts/shopify_publisher.py`
- `scripts/validate_article.py`
- `skills/genseo-auto-publish/SKILL.md`
- `tests/test_canonical_audit.py`
- `tests/test_canonical_urls.py`

### #68 `b3b416a83d13c562f51fde70a4d894d142ab21c7` — Add an evidence-only first-hand experience block for articles
Base `main` · branch `cursor/first-hand-experience-block-0de5` · 16 files
- `.cursor/rules/genseo-operating-rules.mdc`
- `DAILY-RUN.md`
- `data/experience_quotes.json`
- `docs/first-hand-experience-block.md`
- `knowledge_base/AEO_GEO_GUIDELINES.md`
- `knowledge_base/SEO_EEAT_GUIDELINES.md`
- `scripts/experience_block.py`
- `scripts/run_ticket_headless.sh`
- `scripts/shopify_publisher.py`
- `scripts/validate_article.py`
- `skills/genseo-auto-publish/SKILL.md`
- `skills/genseo-auto-publish/references/article-templates.md`
- `skills/genseo-content-refresh/SKILL.md`
- `skills/genseo-content-writer/SKILL.md`
- `skills/genseo-refresh/SKILL.md`
- `tests/test_experience_block.py`

### #69 `5f8dbca5be407c395271d633a54d142bf3d188be` — Add direct-to-deep-content sessions to the GEO traffic report
Base `main` · branch `cursor/geo-direct-deep-content-7b88` · 3 files
- `scripts/deep_content_pages.py`
- `scripts/geo_traffic_report.py`
- `tests/test_geo_traffic_report.py`

### #70 `77331d0a86a94e1a3a314d0a82395860c1a1fc06` — Read-only audit: PDF COAs versus crawlable HTML
Base `main` · branch `cursor/coa-pdf-html-audit-df6a` · 5 files
- `data/coa_pdf_html_rate_limited_2026-10-19.txt`
- `data/coa_pdf_html_seed.json`
- `docs/COA_PDF_HTML_AUDIT_2026-10-19.md`
- `scripts/coa_pdf_html_check.py`
- `tests/test_coa_pdf_html_check.py`

### #71 `bebea7a1b1408eca21b7f28d61fa3063a730d0db` — GEO: entity consistency audit + canonical name map (SEL 10-15)
Base `main` · branch `cursor/entity-consistency-audit-1020` · 7 files
- `data/entity_canonical_names.json`
- `docs/audits/entity-consistency-2026-10-20.json`
- `docs/audits/entity-consistency-2026-10-20.md`
- `scripts/entity_consistency_audit.py`
- `scripts/entity_names.py`
- `scripts/validate_article.py`
- `tests/test_entity_consistency.py`

### #72 `eee58d15beeab3ced46f2a26e7df19980bd50b76` — AgeAura AI Mode follow-up gap map (draft)
Base `main` · branch `cursor/ageaura-ai-mode-gap-map-1020` · 5 files
- `data/ai_mode_seeds/ageaura_nmn_tmg.crawl.json`
- `data/ai_mode_seeds/ageaura_nmn_tmg.json`
- `docs/AI_MODE_GAP_MAP_AGEAURA_2026-10-20.md`
- `scripts/ai_mode_gap_map.py`
- `tests/test_ai_mode_gap_map.py`

### #73 `8be49f663461df365b86a9b584481db8d3bc9d54` — SEO fixes 2026-10-20: one Article JSON-LD per article; proposals for sameAs, product H1s, resin sitemap
Base `cursor/entity-consistency-audit-1020` · branch `cursor/seo-entity-fixes-1020` · 11 files
- `data/entity_canonical_names.json`
- `docs/audits/entity-consistency-2026-10-20.json`
- `docs/audits/entity-consistency-2026-10-20.md`
- `docs/audits/seo-fix-2026-10-20.md`
- `scripts/dedupe_article_jsonld.py`
- `scripts/entity_consistency_audit.py`
- `scripts/repair_schema.py`
- `scripts/shopify_publisher.py`
- `scripts/verify_published.py`
- `tests/test_dedupe_article_jsonld.py`
- `tests/test_verify_published.py`

### #75 `e6b020f0745193f1539c1c7e81237143197d7680` — Draft: off-page listicle gap list for AgeAura and ShilaSource
Base `main` · branch `cursor/offpage-listicle-gap-1020` · 6 files
- `data/offpage_seeds/ageaura.json`
- `data/offpage_seeds/shilasource.json`
- `data/offpage_sources_2026-10-20.json`
- `docs/OFFPAGE_LISTICLE_GAP_2026-10-20.md`
- `scripts/offpage_listicle_gap.py`
- `tests/test_offpage_listicle_gap.py`

### #77 `fa9e5659022bba30395a0aa6013260835843774c` — Warn-only publish gate for near-duplicate query clusters
Base `main` · branch `cursor/publish-dup-cluster-gate-1020` · 5 files
- `docs/DUP_CLUSTER_GATE.md`
- `scripts/dup_cluster_gate.py`
- `scripts/validate_article.py`
- `skills/genseo-auto-publish/SKILL.md`
- `tests/test_dup_cluster_gate.py`

### #78 `bfd51a045618d1605e7139dc9e1587dd1041595d` — Add a read-only quarterly news-blog content audit
Base `main` · branch `cursor/quarterly-content-audit-78b5` · 5 files
- `docs/quarterly-content-audit.md`
- `reports/quarterly-content-audit-2026-10-20.csv`
- `reports/quarterly-content-audit-2026-10-20.md`
- `scripts/quarterly_content_audit.py`
- `tests/test_quarterly_content_audit.py`

### #81 `a2c8b056c207464ce4df1a6dd0123e1b8044c3d4` — Record AI mentions and citations as separate fields
Base `main` · branch `cursor/ai-visibility-mention-citation-1020` · 11 files
- `.cursor/skills/genseo-aeo-tracker/SKILL.md`
- `.gitignore`
- `data/ai_visibility/competitor_patterns.json`
- `data/ai_visibility/observations.json`
- `data/ai_visibility/prompt_set.json`
- `docs/AI_VISIBILITY_MENTION_CITATION.md`
- `knowledge_base/AEO_GEO_GUIDELINES.md`
- `scripts/aeo_tracker.py`
- `scripts/ai_visibility.py`
- `skills/genseo-aeo-tracker/SKILL.md`
- `tests/test_ai_visibility.py`

### #82 `61c7574680c00b1b87f900b1a23b1657bd67f7a9` — Add a rights-gated first-hand experience block for blog articles
Base `main` · branch `cursor/first-hand-experience-block-2d23` · 10 files
- `docs/FIRST_HAND_EXPERIENCE.md`
- `knowledge_base/SEO_EEAT_GUIDELINES.md`
- `scripts/first_hand_experience.py`
- `scripts/validate_article.py`
- `skills/genseo-auto-publish/SKILL.md`
- `skills/genseo-auto-publish/references/article-templates.md`
- `skills/genseo-content-writer/SKILL.md`
- `templates/first-hand-experience-block.md`
- `templates/first-hand-quotes.json`
- `tests/test_first_hand_experience.py`

### #83 `429ac9a2d77ce32319a1cd193378e6f13d5eefe5` — Weekly AI referrer report by domain, not UTM
Base `main` · branch `cursor/ai-referrer-weekly-1021` · 8 files
- `docs/AI_REFERRER_REPORT_TEMPLATE.md`
- `docs/AI_REFERRER_WEEKLY.md`
- `docs/GEO_PLAYBOOK_ROUTINES.md`
- `knowledge_base/AEO_GEO_GUIDELINES.md`
- `scripts/ai_referrer_report.py`
- `tests/fixtures/ai_referrer_utm_only.csv`
- `tests/fixtures/ai_referrer_week.csv`
- `tests/test_ai_referrer_report.py`

### #84 `c6bf852f9635ac28d025432b6b86991196c97782` — Add a read-only mobile clutter audit for blog articles
Base `main` · branch `cursor/mobile-clutter-audit-1021` · 9 files
- `docs/MOBILE_CLUTTER_AUDIT_2026-10-21.json`
- `docs/MOBILE_CLUTTER_AUDIT_2026-10-21.md`
- `scripts/audit_mobile_clutter.py`
- `tests/fixtures/mobile_clutter/clean.html`
- `tests/fixtures/mobile_clutter/cluttered.html`
- `tests/fixtures/mobile_clutter/feed.atom`
- `tests/fixtures/mobile_clutter/no-article.html`
- `tests/fixtures/mobile_clutter/tracker.csv`
- `tests/test_mobile_clutter_audit.py`

### #85 `88457b2351e8847f1245d7fd050879657b1fd5f1` — Buyer prompt-loss list for AgeAura, ShilaSource, and FloraFresh
Base `main` · branch `cursor/prompt-loss-list-1021` · 7 files
- `data/prompt_loss/buyer_prompts.json`
- `docs/PROMPT_LOSS_LIST.md`
- `docs/PROMPT_LOSS_TOPIC_PROPOSALS.md`
- `knowledge_base/AEO_GEO_GUIDELINES.md`
- `scripts/prompt_loss_list.py`
- `tests/fixtures/prompt_loss/visibility_prompts.json`
- `tests/test_prompt_loss_list.py`

### #86 `884977b2e9ed02214579526cbacb32cbe5c69bd5` — Brand-SERP defence for the 2026-10-21 position slide
Base `main` · branch `cursor/brand-serp-slide-1021` · 6 files
- `docs/BRAND_BLOG_ANCHOR_PROPOSALS_2026-10-21.md`
- `docs/BRAND_SERP_DEFENCE_2026-10-21.md`
- `scripts/brand_blog_anchors.py`
- `scripts/brand_serp_slice.py`
- `tests/fixtures/brand_serp/gsc.csv`
- `tests/test_brand_serp_slice.py`

### #87 `6679085cc21825aa9d5f90808aed82ab745ffe12` — Draft: striking-distance answer-first FAQ refreshes (2026-10-21)
Base `main` · branch `cursor/striking-faq-1021` · 4 files
- `docs/STRIKING_DISTANCE_FAQ_2026-10-21.md`
- `docs/striking-distance-2026-10-21/creatine-gummies-shelf-life-answer-block.md`
- `docs/striking-distance-2026-10-21/nmn-coffee-answer-block.md`
- `docs/striking-distance-2026-10-21/probiotics-birth-control-answer-block.md`

### #88 `b6227188efc2e74ea9b02ff23e429c752ade9fe2` — FloraFresh 15B CFU and Mike Moretti blog byline
Base `main` · branch `cursor/florafresh-15b-mike-moretti-0e04` · 47 files
- `.cursor/rules/genseo-landing-lane.mdc`
- `.cursor/rules/genseo-operating-rules.mdc`
- `.cursor/rules/genseo-ticket-queue.mdc`
- `AGENTS.md`
- `DAILY-RUN.md`
- `board/ideas.csv`
- `daily-landing-tickets.md`
- `daily-tickets.md`
- `deploy/llms-txt/llms.txt`
- `docs/FLORAFRESH_FORMULA_GUARD.md`
- `docs/GEO_PLAYBOOK_GAP_ANALYSIS_2026-10-20.md`
- `docs/GOLD_RESIN_LABEL_GUARD.md`
- `docs/LABEL_OCR_GATE.md`
- `docs/SHILASOURCE_RESIN_LABEL_GUARD.md`
- `docs/SHOCKWAVE_LABEL_GUARD.md`
- `docs/TURKESTERONE_LABEL_GUARD.md`
- `knowledge_base/AEO_GEO_GUIDELINES.md`
- `roster.json`
- `scripts/brand_rules.py`
- `scripts/cluster_topic_picker.py`
- `scripts/florafresh_rules.py`
- `scripts/genseo_roster.py`
- `scripts/lint_tickets.py`
- `scripts/llms_formula.py`
- `scripts/refill_tickets.py`
- `scripts/run_landing_headless.sh`
- `scripts/run_ticket_headless.sh`
- `scripts/topic_fitness.py`
- `scripts/validate_article.py`
- `skills/genseo-auto-publish/SKILL.md`
- `skills/genseo-content-writer/SKILL.md`
- `skills/genseo-landing-pages/SKILL.md`
- `templates/article-topic-bank.json`
- `templates/landing/listicle-angles.json`
- `templates/related-questions-block.md`
- `tests/test_blog_byline.py`
- `tests/test_florafresh_guard.py`
- `tests/test_geo_citability.py`
- `tests/test_geo_clusters.py`
- `tests/test_geo_official_lint.py`
- `tests/test_gold_resin_guard.py`
- `tests/test_llms_formula.py`
- `tests/test_packaging_palette.py`
- `tests/test_shilasource_resin_guard.py`
- `tests/test_shockwave_guard.py`
- `tests/test_turkesterone_guard.py`
- `tickets.example.md`

### #89 `ae39ad2e80f151ee8f1ee53c8a53e05bceaa2bd3` — FloraFresh drafts: 1B → 15B CFU (SNZ-1969)
Base `main` · branch `cursor/drafts-15b-cfu-1022` · 16 files
- `published_drafts/creatine-gummies-for-runners-what-trials-show-us-2026.md`
- `published_drafts/creatine-gummies-over-60-trials-us-2026.md`
- `published_drafts/how-to-take-vaginal-probiotics-us-2026.md`
- `published_drafts/nmn-and-coffee-us-2026.md`
- `published_drafts/shilajit-for-athletes-what-a-strength-trial-found-us-2026.md`
- `published_drafts/shilajit-for-fertility-what-one-small-trial-found-us-2026.md`
- `published_drafts/shilajit-for-seniors-5-safety-checks-over-60-us-2026.md`
- `published_drafts/shilajit-gummies-while-traveling-with-food-us-2026.md`
- `published_drafts/shilajit-on-rest-days-with-food-us-2026.md`
- `published_drafts/turkesterone-over-60-5-checks-us-2026.md`
- `published_drafts/turkesterone-price-us-2026.md`
- `published_drafts/turkesterone-rest-days-us-2026.md`
- `published_drafts/vaginal-probiotic-dosage-how-many-cfu-a-day-us-2026.md`
- `published_drafts/vaginal-probiotics-for-beginners-what-to-expect-us-2026.md`
- `published_drafts/vaginal-probiotics-while-traveling-keep-them-working-us-2026.md`
- `published_drafts/where-to-buy-nmn-fda-status-explained-us-2026.md`

### #90 `4386e4863be9bdb48feeca69bd1acb52c87989a3` — Combine #9 + #10 onto main + #88 (draft)
Base `main` · branch `cursor/combine-9-10-on-88-1023` · 58 files
- `.cursor/rules/genseo-landing-lane.mdc`
- `.cursor/rules/genseo-operating-rules.mdc`
- `.cursor/rules/genseo-ticket-queue.mdc`
- `AGENTS.md`
- `DAILY-RUN.md`
- `board/ideas.csv`
- `daily-landing-tickets.md`
- `daily-tickets.md`
- `deploy/llms-txt/llms.txt`
- `docs/FLORAFRESH_FORMULA_GUARD.md`
- `docs/FUSIFORCE_LABEL_GUARD.md`
- `docs/GEO_PLAYBOOK_GAP_ANALYSIS_2026-10-20.md`
- `docs/GOLD_RESIN_LABEL_GUARD.md`
- `docs/LABEL_OCR_GATE.md`
- `docs/SHILAJIT_GUMMIES_LABEL_GUARD.md`
- `docs/SHILASOURCE_RESIN_LABEL_GUARD.md`
- `docs/SHOCKWAVE_LABEL_GUARD.md`
- `docs/TURKESTERONE_LABEL_GUARD.md`
- `knowledge_base/AEO_GEO_GUIDELINES.md`
- `product_refs/fusiforce-creatine-gummies.label.json`
- `roster.json`
- `scripts/brand_rules.py`
- `scripts/build_landing_tickets.py`
- `scripts/cluster_topic_picker.py`
- `scripts/florafresh_rules.py`
- `scripts/fusiforce_rules.py`
- `scripts/genseo_roster.py`
- `scripts/lint_tickets.py`
- `scripts/llms_formula.py`
- `scripts/refill_tickets.py`
- `scripts/run_landing_headless.sh`
- `scripts/run_ticket_headless.sh`
- `scripts/shilajit_gummies_rules.py`
- `scripts/shopify_publisher.py`
- `scripts/topic_fitness.py`
- `scripts/validate_article.py`
- `scripts/validate_landing.py`
- `skills/genseo-auto-publish/SKILL.md`
- `skills/genseo-content-writer/SKILL.md`
- `skills/genseo-landing-pages/SKILL.md`
- `templates/article-topic-bank.json`
- `templates/landing/listicle-angles.json`
- `templates/related-questions-block.md`
- `tests/test_ageaura_guard.py`
- `tests/test_blog_byline.py`
- `tests/test_florafresh_guard.py`
- `tests/test_fusiforce_guard.py`
- `tests/test_geo_citability.py`
- `tests/test_geo_clusters.py`
- `tests/test_geo_official_lint.py`
- `tests/test_gold_resin_guard.py`
- `tests/test_llms_formula.py`
- `tests/test_packaging_palette.py`
- `tests/test_shilajit_gummies_guard.py`
- `tests/test_shilasource_resin_guard.py`
- `tests/test_shockwave_guard.py`
- `tests/test_turkesterone_guard.py`
- `tickets.example.md`

### #91 `ade6dd72ad7e0620d0787c3bed2ee940cc42be87` — Track untracked FloraFresh drafts at 15B CFU
Base `main` · branch `cursor/untracked-drafts-15b-1024` · 20 files
- `published_drafts/are-vaginal-probiotics-worth-it-how-much-2026.md`
- `published_drafts/creatine-gummies-for-runners-what-trials-show-us-2026.md`
- `published_drafts/creatine-gummies-over-60-trials-us-2026.md`
- `published_drafts/how-to-take-vaginal-probiotics-us-2026.md`
- `published_drafts/nmn-and-coffee-us-2026.md`
- `published_drafts/shilajit-for-athletes-what-a-strength-trial-found-us-2026.md`
- `published_drafts/shilajit-for-fertility-what-one-small-trial-found-us-2026.md`
- `published_drafts/shilajit-for-seniors-5-safety-checks-over-60-us-2026.md`
- `published_drafts/shilajit-gummies-while-traveling-with-food-us-2026.md`
- `published_drafts/shilajit-on-rest-days-with-food-us-2026.md`
- `published_drafts/turkesterone-over-60-5-checks-us-2026.md`
- `published_drafts/turkesterone-price-us-2026.md`
- `published_drafts/turkesterone-rest-days-us-2026.md`
- `published_drafts/vaginal-probiotic-dosage-how-many-cfu-a-day-us-2026.md`
- `published_drafts/vaginal-probiotics-empty-stomach-us-2026.md`
- `published_drafts/vaginal-probiotics-for-beginners-what-to-expect-us-2026.md`
- `published_drafts/vaginal-probiotics-on-an-empty-stomach-us-2026.md`
- `published_drafts/vaginal-probiotics-while-traveling-keep-them-working-us-2026.md`
- `published_drafts/where-to-buy-nmn-fda-status-explained-us-2026.md`
- `published_drafts/where-to-buy-vaginal-probiotics-in-the-us-5-checks-2026.md`

### #92 `15002fea894a7f5357c2da8496d513fa5cbfa0f4` — GSC 10-24: refresh drafts for shilajit reviews + what-is-shilajit (no publish)
Base `main` · branch `cursor/gsc-1024-blog-refresh` · 6 files
- `published_drafts/refresh-2026-10-24-wellness-nest-shilajit-reviews-what-85-buyers-report.claims.md`
- `published_drafts/refresh-2026-10-24-wellness-nest-shilajit-reviews-what-85-buyers-report.md`
- `published_drafts/refresh-2026-10-24-what-is-shilajit-history-chemical-properties-processing.claims.md`
- `published_drafts/refresh-2026-10-24-what-is-shilajit-history-chemical-properties-processing.md`
- `roster.json`
- `scripts/genseo_roster.py`

### #93 `c0aebd5aeb7d129e3a8c4d3d4828291c49b5fa69` — GSC 10-24: FAQ drafts — probiotics + birth control/period, turkesterone WADA (no publish)
Base `main` · branch `cursor/gsc-1024-faq-cluster` · 57 files
- `.cursor/rules/genseo-landing-lane.mdc`
- `.cursor/rules/genseo-operating-rules.mdc`
- `.cursor/rules/genseo-ticket-queue.mdc`
- `DAILY-RUN.md`
- `board/ideas.csv`
- `daily-tickets.md`
- `deploy/llms-txt/llms.txt`
- `docs/FLORAFRESH_FORMULA_GUARD.md`
- `docs/GEO_PLAYBOOK_GAP_ANALYSIS_2026-10-20.md`
- `docs/GOLD_RESIN_LABEL_GUARD.md`
- `docs/LABEL_OCR_GATE.md`
- `docs/SHILASOURCE_RESIN_LABEL_GUARD.md`
- `docs/SHOCKWAVE_LABEL_GUARD.md`
- `docs/TURKESTERONE_LABEL_GUARD.md`
- `drafts/gsc-2026-10-24/img/bc-clinic-waiting-room.webp`
- `drafts/gsc-2026-10-24/img/bc-nightstand-evening.webp`
- `drafts/gsc-2026-10-24/img/bc-tote-bag-cafe.webp`
- `drafts/gsc-2026-10-24/img/florafresh-pouch.png`
- `drafts/gsc-2026-10-24/img/period-desk-drawer.webp`
- `drafts/gsc-2026-10-24/img/period-sofa-routine.webp`
- `drafts/gsc-2026-10-24/img/period-weekend-bag.webp`
- `drafts/gsc-2026-10-24/img/turk-ingredient-panel.webp`
- `drafts/gsc-2026-10-24/img/turk-training-bag.webp`
- `drafts/gsc-2026-10-24/img/turk-verification-notes.webp`
- `drafts/gsc-2026-10-24/img/turkesterone-jar.png`
- `drafts/gsc-2026-10-24/probiotics-and-birth-control-can-you-take-both-us-2026.claims.md`
- `drafts/gsc-2026-10-24/probiotics-and-birth-control-can-you-take-both-us-2026.md`
- `drafts/gsc-2026-10-24/probiotics-during-your-period-keep-taking-them-us-2026.claims.md`
- `drafts/gsc-2026-10-24/probiotics-during-your-period-keep-taking-them-us-2026.md`
- `drafts/gsc-2026-10-24/turkesterone-for-athletes-drug-test-guide-us-2026.claims.md`
- `drafts/gsc-2026-10-24/turkesterone-for-athletes-drug-test-guide-us-2026.md`
- `knowledge_base/AEO_GEO_GUIDELINES.md`
- `roster.json`
- `scripts/brand_rules.py`
- `scripts/cluster_topic_picker.py`
- `scripts/florafresh_rules.py`
- `scripts/genseo_roster.py`
- `scripts/lint_tickets.py`
- `scripts/llms_formula.py`
- `scripts/refill_tickets.py`
- `scripts/run_landing_headless.sh`
- `scripts/run_ticket_headless.sh`
- `scripts/topic_fitness.py`
- `skills/genseo-auto-publish/SKILL.md`
- `skills/genseo-landing-pages/SKILL.md`
- `templates/article-topic-bank.json`
- `templates/landing/listicle-angles.json`
- `templates/related-questions-block.md`
- `tests/test_florafresh_guard.py`
- `tests/test_geo_clusters.py`
- `tests/test_geo_official_lint.py`
- `tests/test_gold_resin_guard.py`
- `tests/test_llms_formula.py`
- `tests/test_packaging_palette.py`
- `tests/test_shilasource_resin_guard.py`
- `tests/test_shockwave_guard.py`
- `tests/test_turkesterone_guard.py`

### #94 `bd8b4734212ece71e9582dab3c509c72c79a7a9f` — Accept Mike Moretti as the Wellness Nest blog byline
Base `main` · branch `cursor/kevin-facts-guards-1024` · 11 files
- `DAILY-RUN.md`
- `daily-tickets.md`
- `roster.json`
- `scripts/build_rich_tickets.py`
- `scripts/genseo_roster.py`
- `scripts/refill_tickets.py`
- `scripts/validate_article.py`
- `skills/genseo-auto-publish/SKILL.md`
- `skills/genseo-content-writer/SKILL.md`
- `skills/genseo-landing-pages/SKILL.md`
- `tests/test_roster_byline.py`

### #95 `e2dea61028c045e0dfc285acd0dd8a7877d39805` — Fix the long-standing known test failures
Base `main` · branch `cursor/fix-known-test-failures-1025` · 6 files
- `scripts/genseo_self_apply.sh`
- `scripts/genseo_sync_main.sh`
- `tests/test_landing_rotation.py`
- `tests/test_queue_closures.py`
- `tests/test_self_apply.sh`
- `tests/test_sync_main.sh`

### #96 `29c6c2556cbe9c82154fafa87a749edb6e1a1469` — Align unpublished landing offers with live product JSON
Base `main` · branch `cursor/landing-drafts-price-sweep-1026` · 105 files
- `.cursor/rules/genseo-landing-lane.mdc`
- `.cursor/rules/genseo-operating-rules.mdc`
- `.cursor/rules/genseo-ticket-queue.mdc`
- `DAILY-RUN.md`
- `board/ideas.csv`
- `daily-tickets.md`
- `deploy/llms-txt/llms.txt`
- `docs/FLORAFRESH_FORMULA_GUARD.md`
- `docs/GOLD_RESIN_LABEL_GUARD.md`
- `docs/LABEL_OCR_GATE.md`
- `docs/SHILASOURCE_RESIN_LABEL_GUARD.md`
- `docs/SHOCKWAVE_LABEL_GUARD.md`
- `docs/TURKESTERONE_LABEL_GUARD.md`
- `knowledge_base/AEO_GEO_GUIDELINES.md`
- `landing_drafts/ageaura-nmn-listicle-261008.claims.md`
- `landing_drafts/ageaura-nmn-listicle-261008.json`
- `landing_drafts/ageaura-nmn-listicle-261008/body.html`
- `landing_drafts/ageaura-nmn-listicle-261008/preview.html`
- `landing_drafts/ageaura-nmn-tmg-listicle-261017.claims.md`
- `landing_drafts/ageaura-nmn-tmg-listicle-261017.json`
- `landing_drafts/ageaura-nmn-tmg-listicle-261017/body.html`
- `landing_drafts/ageaura-nmn-tmg-listicle-261017/preview.html`
- `landing_drafts/ageaura-nmn-tmg-listicle-261025.claims.md`
- `landing_drafts/ageaura-nmn-tmg-listicle-261025.json`
- `landing_drafts/ageaura-nmn-tmg-listicle-261025/body.html`
- `landing_drafts/ageaura-nmn-tmg-listicle-261025/preview.html`
- `landing_drafts/florafresh-listicle-261009.KEVIN-REVIEW.md`
- `landing_drafts/florafresh-listicle-261009.claims.md`
- `landing_drafts/florafresh-listicle-261009.json`
- `landing_drafts/florafresh-listicle-261009/body.html`
- `landing_drafts/florafresh-listicle-261009/preview.html`
- `landing_drafts/florafresh-listicle-261019.claims.md`
- `landing_drafts/florafresh-listicle-261019.json`
- `landing_drafts/florafresh-listicle-261019/body.html`
- `landing_drafts/florafresh-listicle-261019/preview.html`
- `landing_drafts/fusiforce-creatine-gummies-listicle-261015.claims.md`
- `landing_drafts/fusiforce-creatine-gummies-listicle-261015.json`
- `landing_drafts/fusiforce-creatine-gummies-listicle-261015/body.html`
- `landing_drafts/fusiforce-creatine-gummies-listicle-261015/preview.html`
- `landing_drafts/fusiforce-creatine-gummies-listicle.claims.md`
- `landing_drafts/fusiforce-creatine-gummies-listicle.json`
- `landing_drafts/fusiforce-creatine-gummies-listicle/body.html`
- `landing_drafts/fusiforce-creatine-gummies-listicle/preview.html`
- `landing_drafts/fusiforce-creatine-listicle-261008.claims.md`
- `landing_drafts/fusiforce-creatine-listicle-261008.json`
- `landing_drafts/fusiforce-creatine-listicle-261008/body.html`
- `landing_drafts/fusiforce-creatine-listicle-261008/preview.html`
- `landing_drafts/pure-shilajit-gold-resin-listicle-261012.claims.md`
- `landing_drafts/pure-shilajit-gold-resin-listicle-261012.json`
- `landing_drafts/pure-shilajit-gold-resin-listicle-261012/body.html`
- `landing_drafts/pure-shilajit-gold-resin-listicle-261012/preview.html`
- `landing_drafts/pure-shilajit-gold-resin-listicle-261020.claims.md`
- `landing_drafts/pure-shilajit-gold-resin-listicle-261020.json`
- `landing_drafts/pure-shilajit-gold-resin-listicle-261020/body.html`
- `landing_drafts/pure-shilajit-gold-resin-listicle-261020/preview.html`
- `landing_drafts/shilajit-gummies-listicle-261008.claims.md`
- `landing_drafts/shilajit-gummies-listicle-261008.json`
- `landing_drafts/shilajit-gummies-listicle-261008/body.html`
- `landing_drafts/shilajit-gummies-listicle-261008/preview.html`
- `landing_drafts/shilajit-gummies-listicle-261022.claims.md`
- `landing_drafts/shilajit-gummies-listicle-261022.json`
- `landing_drafts/shilasource-himalayan-shilajit-resin-listicle-261024.claims.md`
- `landing_drafts/shilasource-himalayan-shilajit-resin-listicle-261024.json`
- `landing_drafts/shilasource-himalayan-shilajit-resin-listicle-261024/body.html`
- `landing_drafts/shilasource-himalayan-shilajit-resin-listicle-261024/preview.html`
- `landing_drafts/shilasource-resin-advertorial.claims.md`
- `landing_drafts/shilasource-resin-advertorial.json`
- `landing_drafts/shilasource-resin-advertorial/body.html`
- `landing_drafts/shilasource-resin-advertorial/preview.html`
- `landing_drafts/shilasource-resin-listicle-261008.claims.md`
- `landing_drafts/shilasource-resin-listicle-261008.json`
- `landing_drafts/shilasource-resin-listicle-261008/body.html`
- `landing_drafts/shilasource-resin-listicle-261008/preview.html`
- `landing_drafts/turkesterone-listicle-261016.claims.md`
- `landing_drafts/turkesterone-listicle-261023.claims.md`
- `logs/claims/how-to-take-vaginal-probiotics-us-2026.md`
- `logs/claims/vaginal-probiotic-dosage-how-many-cfu-a-day-us-2026.md`
- `logs/claims/vaginal-probiotic-gummies-at-home-how-much-heat-2026.md`
- `logs/claims/vaginal-probiotic-ingredients-how-much-2026.md`
- `logs/claims/vaginal-probiotics-and-alcohol-how-much-matters-us-2026.md`
- `logs/claims/vaginal-probiotics-for-beginners-what-to-expect-us-2026.md`
- `logs/claims/vaginal-probiotics-while-traveling-keep-them-working-us-2026.md`
- `scripts/brand_rules.py`
- `scripts/cluster_topic_picker.py`
- `scripts/florafresh_rules.py`
- `scripts/lint_tickets.py`
- `scripts/llms_formula.py`
- `scripts/refill_tickets.py`
- `scripts/run_landing_headless.sh`
- `scripts/run_ticket_headless.sh`
- `scripts/topic_fitness.py`
- `skills/genseo-auto-publish/SKILL.md`
- `skills/genseo-landing-pages/SKILL.md`
- `templates/article-topic-bank.json`
- `templates/landing/listicle-angles.json`
- `templates/related-questions-block.md`
- `tests/test_florafresh_guard.py`
- `tests/test_geo_clusters.py`
- `tests/test_geo_official_lint.py`
- `tests/test_gold_resin_guard.py`
- `tests/test_llms_formula.py`
- `tests/test_packaging_palette.py`
- `tests/test_shilasource_resin_guard.py`
- `tests/test_shockwave_guard.py`
- `tests/test_turkesterone_guard.py`

### #97 `d088ccb3ed275fc0d61a0847a208bc2d6b32f286` — Treat a Shopify 429 on the draft dead-link check as unverified
Base `main` · branch `cursor/validator-429-unverified-1027` · 2 files
- `scripts/validate_article.py`
- `tests/test_draft_link_429.py`

### #98 `ce9ef4c468c18b64be1209db6be0188329c91b86` — Point landing queue tests at the open Shockwave ticket
Base `main` · branch `cursor/fix-landing-queue-tests-1028` · 2 files
- `tests/test_landing_rotation.py`
- `tests/test_queue_closures.py`

### #99 `1af4fc8a8ae59232934af61872b13d6279c18219` — Draft PR readiness against main (2026-10-28)
Base `main` · branch `cursor/draft-pr-readiness-1028` · 1 files
- `reports/draft-pr-readiness-2026-10-28.md`

### #1 `e4982bd433d5190beea8fb6003c5c30414e607ca` — IndexNow env-gated pings and llms.txt drafts
Base `main` · branch `cursor/indexnow-llms-txt-44d2` · 14 files
- `.gitignore`
- `DAILY-RUN.md`
- `LOCALIZE.md`
- `README.md`
- `deploy/llms-txt/README.md`
- `deploy/llms-txt/llms-full.txt`
- `deploy/llms-txt/llms.txt`
- `docs/indexnow-and-llms-txt.md`
- `scripts/build_llms_txt.py`
- `scripts/indexnow_ping.py`
- `scripts/setup_indexnow.py`
- `scripts/shopify_publisher.py`
- `tests/test_build_llms_txt.py`
- `tests/test_indexnow_ping.py`

### #9 `ad0cebfaa96d84fe41792fd7edf90df4d1677620` — FusiForce pack label fails closed on 84, doses, and ginseng
Base `main` · branch `cursor/fusiforce-label-guard-befe` · 20 files
- `.cursor/rules/genseo-landing-lane.mdc`
- `.cursor/rules/genseo-operating-rules.mdc`
- `.cursor/rules/genseo-ticket-queue.mdc`
- `docs/FUSIFORCE_LABEL_GUARD.md`
- `docs/LABEL_OCR_GATE.md`
- `knowledge_base/AEO_GEO_GUIDELINES.md`
- `scripts/brand_rules.py`
- `scripts/build_landing_tickets.py`
- `scripts/fusiforce_rules.py`
- `scripts/lint_tickets.py`
- `scripts/refill_tickets.py`
- `scripts/run_landing_headless.sh`
- `scripts/run_ticket_headless.sh`
- `scripts/shopify_publisher.py`
- `scripts/topic_fitness.py`
- `scripts/validate_article.py`
- `skills/genseo-auto-publish/SKILL.md`
- `templates/landing/listicle-angles.json`
- `tests/test_ageaura_guard.py`
- `tests/test_fusiforce_guard.py`

### #10 `d7fb719589ce3216b9b4127b364ec1136f20c1df` — Shilajit gummies pack label fails closed on 30 servings and invented milligrams
Base `main` · branch `cursor/shilajit-gummies-label-guard-306e` · 20 files
- `.cursor/rules/genseo-landing-lane.mdc`
- `.cursor/rules/genseo-operating-rules.mdc`
- `.cursor/rules/genseo-ticket-queue.mdc`
- `docs/LABEL_OCR_GATE.md`
- `docs/SHILAJIT_GUMMIES_LABEL_GUARD.md`
- `knowledge_base/AEO_GEO_GUIDELINES.md`
- `scripts/brand_rules.py`
- `scripts/build_landing_tickets.py`
- `scripts/lint_tickets.py`
- `scripts/refill_tickets.py`
- `scripts/run_landing_headless.sh`
- `scripts/run_ticket_headless.sh`
- `scripts/shilajit_gummies_rules.py`
- `scripts/shopify_publisher.py`
- `scripts/topic_fitness.py`
- `scripts/validate_article.py`
- `skills/genseo-auto-publish/SKILL.md`
- `skills/genseo-landing-pages/SKILL.md`
- `tests/test_ageaura_guard.py`
- `tests/test_shilajit_gummies_guard.py`

### #38 `4a475e62bbc4f8c602e62085121005fb4694c888` — Add Mac Mini failover bootstrap and Cursor worker LaunchAgent
Base `main` · branch `cursor/mac-mini-failover-bootstrap-b4e0` · 10 files
- `.cursor/rules/genseo-operating-rules.mdc`
- `DAILY-RUN.md`
- `deploy/com.pati.cursor-agent-worker.plist`
- `deploy/com.pati.genseo-daily.mini.plist`
- `deploy/com.pati.genseo-landing.mini.plist`
- `docs/FAILOVER.md`
- `scripts/mac_mini_failover_bootstrap.sh`
- `scripts/mac_return_reconcile.sh`
- `tests/test_mac_mini_failover_bootstrap.sh`
- `tests/test_mac_return_reconcile.sh`


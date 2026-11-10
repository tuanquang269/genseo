# LAND order — 2026-11-07 16:49 ICT

> Working recommendation moved on 2026-11-10 16:48 ICT to `board/burn-land-order-2026-11-10.md`. The tables below are this snapshot and were not edited.

Draft for Kevin's GO. This pass updated the board only. Nothing was merged, closed, retargeted, marked ready, or published. No Shopify write. #121 was not edited, pushed, rebased, or commented. FloraFresh live 15 billion CFU wording stays with T3. AgeAura in this order is NMN + TMG only.

A local scratch branch `scratch/land-order-sim-20261107` was test-merged in a worktree and then deleted. It was not pushed. Tree SHAs below are from those merges. A re-run on these tips has to reproduce the trees. The scratch commit SHAs are not on the remote.

Prior snapshot: `board/burn-land-order-2026-11-06-2035.md`. Its tables were not edited. A pointer at the top of that file names this one.

`origin/main` is still `bf3ad1b7cd9723c310f3f6dae3f16ee2e9e18ba8` (2026-11-06 13:21:54 +0700, "cherish_auto: add band guarantee line + rail TOC the shell prints"). 45 pull requests are open. The 20:35 board counted 43 and did not include this PR or #130. Every open PR is in the inventory and in one section below.

Evidence is `git merge --no-ff` in the order below, on a worktree of that main (git 2.43.0), then `git merge --no-commit` of every other open PR onto that tip, aborted after the result was recorded. Pairwise rows are `git merge-tree --write-tree` of the second tip onto a local commit of `origin/main` merged with the first tip, both orders. This pass did not run `bash tests/run_suite.sh`. Tips of #81, #85, #127, and #128 are the same SHAs as the 20:35 board, and main has not moved, so that board's `PromptSet` and `PromptLossTests` results still describe those merged trees.

## CI

The repo has no GitHub Actions workflows. For every open tip, the check-runs API returns `total_count: 0` and the combined commit status is `pending` with zero statuses. GraphQL shows two check suites, Supabase and Cursor, stuck `queued` with a null conclusion (created and never updated; confirmed on #118 `b6256f2`, same shape on all 45). That is not a pass and not a fail.

GitHub `mergeable` / `mergeStateStatus` in the inventory is against the PR's base. That base is not main for #73, #115, #122, #123, and #124.

## What changed since 20:35

Rebased onto `bf3ad1b` (merge-base is main, 0 behind):

| PR | New tip | Solo tree vs main | Versus the 20:35 solo tree |
| --- | --- | --- | --- |
| #126 | `d2f07e8405b718201404894547d233bcb1efb5a0` | `1ba991ce88d6ebc4cda4aa06799f83afd66d36da` | Same tree. Was `2dbe163`. |
| #125 | `8875f68002b704ec4d2a24a9f9f1232d0bdd7417` | `002a2c8fc643de18cdf8a2a8dcea10a80fa23581` | Same tree. Was `0548ecd`. |
| #118 | `b6256f249f30ce40ff2fadcffe6e1db7d96dcb4f` | `2293bf53e20fa7a9d856272ed3d9d25485465ea4` | Same tree. Was `f910ecc`. |
| #120 | `2302f4b62f103c74fb4c02c9711eb21533073d59` | `7112e0e278275a46141cbd7da91cb7d15801f9bf` | Same tree. Was `47f45a0`. |
| #119 | `e557298e96d8115dbd408aff21e12efa379b704a` | `883c4381c3e28e1a1c79f68c89f506988010b577` | Same tree. Was `4c8a749`. |
| #116 | `60aee102b54f365b1b83eac83f0489786c89b314` | `3f40c96c3c5f8bd414140670077e3a58396a9666` | Not the same. Delta vs old solo tree `66b37054` is only `tests/test_first_publish_url.py` (+10/−1). The test now imports under the Wellness Nest shop check. Was `1f401b9`. |
| #124 | `a068ae32350ff52c236a65f0e1a0bc0d0eac20c1` | `d4d3640f4a3d24166b36e21e4f5dbc5708722d92` | Restacked onto #120 `2302f4b`, which is an ancestor. Delta vs old solo tree `4f6eb829` is only `board/burn-124-rebase-2026-11-07-t60.md`. The port files match old tip `5e2888d`. |

#122 moved during this pass. The first read was tip `e8e8154dbbd86f67ef80ea00c8063d4e1a088ea8`, GitHub CONFLICTING against `cursor/draft-local-image-gate-1102`. Merge-tree of that tip onto `e557298` conflicted: content in `scripts/validate_article.py`, add/add in `tests/test_draft_image_src.py`. At 2026-11-07 09:54 UTC the tip became `1fa33f6a90fd269d9d0f12a1513c5e79d4311072`, a merge of `e8e8154` with #119 `e557298`. GitHub is MERGEABLE / CLEAN against that base. #119 is an ancestor. The image-src conflict is gone. Solo tree vs main is `6245b57a89da92d58f2bd305d810220cdf0fb4c9` (0 behind / 9 ahead). The diff against #119 is six files: the warn-only dup-cluster gate plus `tests/test_ima2_retry.py`. The merge message keeps the parent's draft-image jail and its full test file, and the warn-only dup-cluster hook. FloraFresh in that message stays SNZ-1969 at 1 billion CFU.

That ima2 file still conflicts with #118 in both orders, on `tests/test_ima2_retry.py`. On the step-18 chain the only conflict is that same file (`scripts/validate_article.py` auto-merges). #122 is clean on the wave-1 tip, before #118. It still cannot share a tree with #118, and it still conflicts with #77 on `scripts/validate_article.py`. Do not land #77 and #122 both.

#123 was not restacked. Tip `58e59895b19a26837c541d25de87796660bc150f` still contains pre-rebase #120 `47f45a0`, not `2302f4b`. GitHub says MERGEABLE against base `cursor/hermetic-writer-ps-1102`, and merge-tree onto `2302f4b` is clean (tree `6c4afc97cd896ef1a36cea7f9d9a2036a52e2632`, the same tree as #123 vs main). Merge-tree of #123 with #124 now conflicts on the four port files. The 20:35 note that #123 and #124 merge cleanly in either direction is no longer true.

#127 `83e0497afa92fcc935f74d37147ad1232f7d1e0e` and #128 `c9c90e4491bf04d43730276fdbee8395811837e3` were not rebased. Both are still 4 behind / 2 ahead, and both are still clean against this main.

#67 `4dc63845131590ce8ca7da7edd1429ef84de051a` is still open, still not a git ancestor of #116 (the rebase rewrote the commits), and still conflicts with main in `skills/genseo-auto-publish/SKILL.md` only.

Scratch chain trees for steps 1–15 match the 20:35 board exactly. The chain diverges at #124 by the restack note. #116 then adds the test import fix. On the final chain tree the 2026-10-09 guidelines bullet is still FloraFresh Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, and AgeAura still links only to the NMN + TMG product. `roster.json` on the chain is still Dr. Marcus Hale. #116's `tests/test_first_publish_url.py` still fixtures `[Mike Moretti](/pages/mike-moretti)` and asserts the publisher sends that author string. This PR does not change the roster.

## Recommended order

Same 18 drafts, same sequence. The scratch merge was clean at every step. No pairwise conflict inside this list forces a swap: every file-overlapping pair among these 18 is clean in both orders.

#120 before #124 matches #124's base. #124's tip already contains #120 `2302f4b`, so merging #124 alone also brings that commit. The separate #120 step is how that commit lands if #124 is held. #125 before #127/#128, #127 before #128, and #119 before #116 are clean in reverse too. This order keeps the 1 billion CFU doc lock ahead of the guidelines bullets, and the image-src gate ahead of the canonical edit to `scripts/validate_article.py`.

Git-clean is not permission to press merge. #125, #58, #64, and #86 say so in the PR text. #116 changes live publish. Those calls are under Owner decisions. The order below is the git order once those calls are a GO.

### Wave 1

Steps 5–13 do not share files with each other, so their relative order is free. #126 shares no files with any other open PR. It stays first so a later suite run in a worktree can construct `Profile("wellnessnest")`.

| Step | PR | Branch | Tip | Behind / ahead | Solo tree vs main | Chain tree |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | #126 | `cursor/hermetic-store-profile-b59c` | `d2f07e8405b718201404894547d233bcb1efb5a0` | 0 / 1 | `1ba991ce88d6ebc4cda4aa06799f83afd66d36da` | `1ba991ce88d6ebc4cda4aa06799f83afd66d36da` |
| 2 | #125 | `cursor/florafresh-1b-snz1969-lock-366e` | `8875f68002b704ec4d2a24a9f9f1232d0bdd7417` | 0 / 1 | `002a2c8fc643de18cdf8a2a8dcea10a80fa23581` | `6abf863cfcb47f2b8dce6c517ffda61bb6eba96b` |
| 3 | #127 | `cloud/81-refresh-1105b` | `83e0497afa92fcc935f74d37147ad1232f7d1e0e` | 4 / 2 | `c859bb259c5649646c5512fcf1da949c3880d115` | `2311e951271cebf32c3301989766aab616653d8a` |
| 4 | #128 | `cloud/85-refresh-1105b` | `c9c90e4491bf04d43730276fdbee8395811837e3` | 4 / 2 | `4c528216bcc79034ed9aee7e5e145c9398223f75` | `6145f1b8e7584c073a65c61837ccfc8d5462799e` |
| 5 | #58 | `cursor/cloud-failover-scaffold-2d90` | `6813af4b97cf5d51e5dff122585c313a780e88c6` | 161 / 1 | `d57e765da98b698c4d8b54597cb4c31fce22d122` | `fba84a5c68fba6918a4ec4a986d59b3b13136f0f` |
| 6 | #64 | `cursor/boot-catchup-8034` | `63482afa293bf08f48a06c286b7678935f0f6ec8` | 94 / 2 | `80a900334e6b133926af45522f519420b303bcbf` | `5cdd4fbacb8052fae06a30f754e94d72644ae295` |
| 7 | #69 | `cursor/geo-direct-deep-content-7b88` | `b8baa228b76afc2c024e083f6b28eae4ab12ca75` | 94 / 3 | `9abc5a89a53d6c23fe1d558c0c08f896710f23bb` | `2d4c665892f913b36ec322c6f96db053cc438ecb` |
| 8 | #70 | `cursor/coa-pdf-html-audit-df6a` | `544b0abfffa290c10c31cd442a2bc1db71d4a5ba` | 94 / 2 | `132ddc3efa8503793a1751f988e45e5423214835` | `a634388c0775762c91ab52e2ffe93721fb50fc62` |
| 9 | #72 | `cursor/ageaura-ai-mode-gap-map-1020` | `c2c03bd8a9dd05cbfd3508e80077c9bd48b5431b` | 94 / 2 | `e3c4de073fe16c9bad8a3f98c7363282c27087ec` | `76820e2ce79e676c5a8fa2dbb0b4dc4f1f77f5c3` |
| 10 | #75 | `cursor/offpage-listicle-gap-1020` | `396cd02faa2b72c7174b9ca506833541e6cba368` | 94 / 2 | `40e8e3e1a90967f42799cde3dca37b9b0038f81f` | `ed64eae0cdf86983ff579d09133d97b672eaa5e5` |
| 11 | #78 | `cursor/quarterly-content-audit-78b5` | `bfd51a045618d1605e7139dc9e1587dd1041595d` | 94 / 2 | `b722f6e4ecc43be25e0c62e4d3e110f2afb78bf3` | `85934a07278e4be09ff6008e64e33144fc88515c` |
| 12 | #84 | `cursor/mobile-clutter-audit-1021` | `9f9d4de5d8357a797933b801c7f3704a2d7ede5e` | 94 / 2 | `0e568c5a32f94438c5a0a489996dc0a1f22eb738` | `5f597094519088c5be37c4fe77e3be99ab21e15e` |
| 13 | #86 | `cursor/brand-serp-slide-1021` | `22b66f930df30409bd9a61741a4c5e41eefb139e` | 94 / 2 | `ec83d6daa4956dab10809f7e097a97e5fdb7ee9a` | `a87100218f81e1e4b70f8df1dfadddfee2f2a1f8` |

Chain tip after step 13: tree `a87100218f81e1e4b70f8df1dfadddfee2f2a1f8`. Same tree as the 20:35 board.

### Wave 2 — after wave 1

| Step | PR | Branch | Tip | Behind / ahead | Solo tree vs main | Chain tree |
| --- | --- | --- | --- | --- | --- | --- |
| 14 | #118 | `cursor/hermetic-unittest-flakes-1102` | `b6256f249f30ce40ff2fadcffe6e1db7d96dcb4f` | 0 / 1 | `2293bf53e20fa7a9d856272ed3d9d25485465ea4` | `3f21b3c377881cb9cb42f7949cb521fce3e7105f` |
| 15 | #120 | `cursor/hermetic-writer-ps-1102` | `2302f4b62f103c74fb4c02c9711eb21533073d59` | 0 / 1 | `7112e0e278275a46141cbd7da91cb7d15801f9bf` | `ff0dd79b27362061c80ef08a9c76cc11db52a997` |
| 16 | #124 | `cursor/port-115-sync-main-onto-120-64e7` | `a068ae32350ff52c236a65f0e1a0bc0d0eac20c1` | 0 / 4 | `d4d3640f4a3d24166b36e21e4f5dbc5708722d92` | `1dc7c3ae14d638ea472b531f8a2b8d82a2084984` |
| 17 | #119 | `cursor/draft-local-image-gate-1102` | `e557298e96d8115dbd408aff21e12efa379b704a` | 0 / 4 | `883c4381c3e28e1a1c79f68c89f506988010b577` | `ac39e6de002f25468364d42d2529ae77f89c1df6` |
| 18 | #116 | `cursor/canonical-url-gate-supersede-67-1102` | `60aee102b54f365b1b83eac83f0489786c89b314` | 0 / 4 | `3f40c96c3c5f8bd414140670077e3a58396a9666` | `96fe2f97ba60e11035a246d9a0f72528eb1b24bb` |

Chain tip after step 18: local commit `9935443944b9e43354ecbce4c6eaa1ba9c77c981` (not pushed), tree `96fe2f97ba60e11035a246d9a0f72528eb1b24bb`.

What each step is:

1. **#126** checkout-relative Wellness Nest paths in `scripts/store_profiles.py`, `stores/wellnessnest/profile.json`, and `tests/test_store_isolation.py`. No overlap with #118.
2. **#125** locks FloraFresh instruction docs to SNZ-1969, 1 billion CFU. No live post edit. The PR text says "Draft only. Do not merge."
3. **#127** landing head for the AI mention/citation work. Supersedes #81.
4. **#128** landing head for the buyer prompt-loss list. Supersedes #85. Clean with #127 in either order.
5. **#58** disabled off-Mac heartbeat. The workflow stays off unless `vars.GENSEO_CLOUD_FAILOVER == '1'`. The PR says do not merge until Kevin says so.
6. **#64** opt-in login catch-up. This is the step that conflicts with #123 on `.cursor/rules/genseo-operating-rules.mdc`. It does not conflict with #120 or #124. The PR says the install is still for Kevin.
7. **#69** read-only GEO direct-to-deep-content sessions.
8. **#70** read-only PDF COA vs HTML audit.
9. **#72** AgeAura AI Mode gap map. The product in the map is NMN + TMG.
10. **#75** off-page listicle gap list for AgeAura and ShilaSource.
11. **#78** read-only quarterly news-blog audit.
12. **#84** read-only mobile clutter audit.
13. **#86** brand-SERP notes for the 2026-10-21 position slide. The test plan says do not merge until a GO covers any blog body edit, article rebuild, or hreflang/title change. This PR does not publish.
14. **#118** hermetic queue and ima2 tests. Landing vehicle for #111. Test-only diff. Blocks #122 and #123 on `tests/test_ima2_retry.py`.
15. **#120** hermetic writer tests. Ancestor of #124. Not an ancestor of #123; #123 still merges onto `2302f4b`.
16. **#124** port of #115 onto #120, plus the restack note. This is the landing head, not #115. The port changes production job matching in `scripts/genseo_self_apply.sh`, `scripts/genseo_sync_main.sh`, and `scripts/mac_return_reconcile.sh`.
17. **#119** remote-image draft gate. `scripts/validate_article.py` and `tests/test_draft_image_src.py`. Tip `e557298` is an ancestor of #122 `1fa33f6`.
18. **#116** canonical URL gate, the replay of #67. `shopify_publisher.py` calls `_canonical_prepare` before image upload and exits 2 when the Article URL is not that article's clean blog URL. The guidelines hunk merged after #125, so the 1 billion CFU bullet stays. Theme JSON-LD stays out (that is #65).

## Pairwise conflicts

Scope: the 31 open PRs that merge clean onto main, file lists taken before #122 moved. Every overlapping pair (45), both orders (90 merge-trees). 30 pairs were clean in both orders. 15 conflicted in both orders. No pair was clean in one order and conflicted in the other. After #122's tip moved to `1fa33f6`, three of those pairs were re-tested: #119 ↔ #122 is now clean both ways (#119 is a parent of that merge), #118 ↔ #122 still conflicts both ways on `tests/test_ima2_retry.py`, and #77 ↔ #122 still conflicts both ways on `scripts/validate_article.py`. The table omits the cleared #119 ↔ #122 row. The other 14 rows did not use the moved tip.

Clean inside the recommended 18, both orders: #125/#127, #125/#128, #127/#128, #64/#120, #64/#124, #116/#119, #116/#125, #116/#127, #116/#128, #120/#124. #126 shares files with nobody.

Also clean, and it changes the 20:35 read: #77/#116 and #97/#116. On these tips #77 and #97 do not conflict with #116. They conflict with #119, both orders, on `scripts/validate_article.py`. There is no order in which #77 or #97 lands in the same tree as #119. #116/#121, #116/#122, #120/#123, #83/#127, #81/#128, #85/#127, and #122/#123 are also clean both ways. #97/#122 was clean against the old #122 tip and is not clean against `1fa33f6`: that tip contains #119, so #97 conflicts with it on `scripts/validate_article.py`, both orders.

| Pair | Both orders | Files |
| --- | --- | --- |
| #64 ↔ #123 | conflict | `.cursor/rules/genseo-operating-rules.mdc` |
| #77 ↔ #119 | conflict | `scripts/validate_article.py` |
| #77 ↔ #122 | conflict | `scripts/validate_article.py` |
| #81 ↔ #127 | conflict | `data/ai_visibility/prompt_set.json`, `docs/AI_VISIBILITY_MENTION_CITATION.md`, `tests/test_ai_visibility.py` |
| #83 ↔ #85 | conflict | `knowledge_base/AEO_GEO_GUIDELINES.md` |
| #83 ↔ #128 | conflict | `knowledge_base/AEO_GEO_GUIDELINES.md` |
| #85 ↔ #128 | conflict | `docs/PROMPT_LOSS_LIST.md`, `tests/test_prompt_loss_list.py` |
| #97 ↔ #119 | conflict | `scripts/validate_article.py` |
| #115 ↔ #120 | conflict | `scripts/genseo_self_apply.sh`, `scripts/mac_return_reconcile.sh`, `tests/test_mac_return_reconcile.sh`, `tests/test_self_apply.sh` |
| #115 ↔ #123 | conflict | `scripts/genseo_self_apply.sh`, `scripts/mac_return_reconcile.sh`, `tests/test_mac_return_reconcile.sh`, `tests/test_self_apply.sh` |
| #115 ↔ #124 | conflict | `scripts/genseo_self_apply.sh`, `scripts/mac_return_reconcile.sh`, `tests/test_mac_return_reconcile.sh`, `tests/test_self_apply.sh` |
| #118 ↔ #122 | conflict | `tests/test_ima2_retry.py` |
| #118 ↔ #123 | conflict | `tests/test_ima2_retry.py` |
| #123 ↔ #124 | conflict | `scripts/genseo_self_apply.sh`, `scripts/mac_return_reconcile.sh`, `tests/test_mac_return_reconcile.sh`, `tests/test_self_apply.sh` |

## Chain probes

After step 18 (tree `96fe2f97ba60e11035a246d9a0f72528eb1b24bb`), each remaining open PR was merged with `--no-commit` and then aborted. The scratch tip was left on the step-18 commit. The worktree was clean afterward.

Clean on that tip:

| PR | Chain tree | Why it is still not in the 18 |
| --- | --- | --- |
| #46 | `f595cfb7a16bd86a931a3038a1fa8729620c56a8` | Unpublished Turkesterone listicle. Price and claims stay Kevin's. |
| #50 | `f03a56d1fcb09842e90e622fd71632e14d9f33b2` | Unpublished AgeAura NMN + TMG listicle. The page stays unpublished. |
| #121 | `a58415b8008bfd501ff40b4c7ee3eb90bbb2a133` | Git-clean, including solo tree `5c2bfdc12923433d9ab9cea2f21ddadcfd47a9a2`. Held. The diff adds alt text that says 15 billion CFU. Not touched. |
| #129 | `3814e4f3c34d1e8851b01d24dadeb4d17bf36920` | This board, at the pre-update tip. Not a code land. |
| #130 | `5f12b521252e012ac9167bb55265c1a0b0e6c02a` | Owner-triage note `board/owner-stale-triage-2026-11-06.md`. Different file. No overlap with this board. |

Conflict on that tip. "Same as solo" means the chain conflict paths are the solo-vs-main paths.

| PR | On the chain | Solo vs main |
| --- | --- | --- |
| #1 | same as solo | 3 files, see inventory |
| #9 | same as solo | 15 files |
| #10 | same as solo | 16 files |
| #38 | same as solo | `.cursor/rules/genseo-operating-rules.mdc`, `deploy/com.pati.genseo-landing.mini.plist`, `scripts/mac_return_reconcile.sh` |
| #65 | same as solo | `.gitignore` |
| #67 | `scripts/canonical_urls.py`, `scripts/shopify_publisher.py`, `skills/genseo-auto-publish/SKILL.md`, `tests/test_canonical_urls.py` | `skills/genseo-auto-publish/SKILL.md` only. The extra three are because #116 is already in the tree. |
| #68 | `.cursor/rules/genseo-operating-rules.mdc`, `scripts/shopify_publisher.py` | operating-rules file only. The publisher path is the #116 overlap. |
| #71 | same as solo | `scripts/validate_article.py` |
| #73 | same as solo | `scripts/shopify_publisher.py`, `scripts/validate_article.py` |
| #77 | `scripts/validate_article.py` | clean. The conflict arrives with #119. |
| #81 | `data/ai_visibility/prompt_set.json`, `docs/AI_VISIBILITY_MENTION_CITATION.md`, `tests/test_ai_visibility.py` | clean. Conflicts with #127. |
| #83 | `knowledge_base/AEO_GEO_GUIDELINES.md` | clean. Conflicts with #128. |
| #85 | `docs/PROMPT_LOSS_LIST.md`, `tests/test_prompt_loss_list.py` | clean. Conflicts with #128. |
| #90 | solo paths plus `tests/test_geo_official_lint.py` | `board/ideas.csv`, `docs/LABEL_OCR_GATE.md`, `knowledge_base/AEO_GEO_GUIDELINES.md`, `templates/article-topic-bank.json`. The test file is the #125 overlap. |
| #95 | `scripts/genseo_self_apply.sh`, `scripts/genseo_sync_main.sh`, `tests/test_landing_rotation.py`, `tests/test_self_apply.sh` | `scripts/genseo_sync_main.sh` only. The rest is #118 and #124. |
| #96 | solo paths plus `docs/LABEL_OCR_GATE.md`, `knowledge_base/AEO_GEO_GUIDELINES.md`, `tests/test_geo_official_lint.py` | `board/ideas.csv`, `templates/article-topic-bank.json`. The added paths are the #125 overlap. |
| #97 | `scripts/validate_article.py` | clean. The conflict arrives with #119. |
| #111 | `tests/test_landing_rotation.py`, `tests/test_queue_closures.py` | `tests/test_landing_rotation.py` only. The second file is #118. |
| #115 | `scripts/genseo_self_apply.sh`, `scripts/mac_return_reconcile.sh`, `tests/test_mac_return_reconcile.sh`, `tests/test_self_apply.sh` | clean vs main. Conflicts with #120 and #124. |
| #117 | same as solo | `scripts/run_landing_headless.sh`, `scripts/run_ticket_headless.sh` |
| #122 | `tests/test_ima2_retry.py` only, re-tested on tip `1fa33f6` | clean vs main and clean vs #119. The chain conflict is #118. The three-file conflict was the pre-restack tip `e8e8154`. |
| #123 | `.cursor/rules/genseo-operating-rules.mdc`, `scripts/genseo_self_apply.sh`, `scripts/mac_return_reconcile.sh`, `tests/test_ima2_retry.py`, `tests/test_mac_return_reconcile.sh`, `tests/test_self_apply.sh` | clean vs main and clean onto #120. Chain conflicts are #64, #118, and #124. |

## Held out of this GO

| PR | Why it is held |
| --- | --- |
| #83 | Clean vs main (solo tree `2eda9bead1dadb3f38077ca9f8c833d0ae8a03af`) and clean after #127. Conflicts with #128, and with #85, on `knowledge_base/AEO_GEO_GUIDELINES.md`. The PR says do not merge until Kevin says so. Next burn replays the one referrer-domain bullet onto the post-#128 guidelines. |
| #97 | Shopify 429 on the draft dead-link check stays unverified (exit 3). Clean vs main (solo tree `40d0a155f8311147101d66f0678e5f49489c7ca2`) and clean with #116. Conflicts with #119 on `scripts/validate_article.py`, and with #122 `1fa33f6` for the same reason, so it cannot join this chain. Replay onto the post-#119 validator, or land it only in a chain that does not include #119. |
| #77 | Warn-only near-duplicate gate. Clean vs main (solo tree `535d36d8522754b1fad3295fccbd221c1d751d07`) and clean with #116. Conflicts with #119, and also with its own replay #122, on `scripts/validate_article.py`. Do not land #77 and #122 both. |
| #121 | Not touched. Chain-clean and main-clean. The image-path rewrite adds alt lines that state 15 billion CFU, including `published_drafts/are-vaginal-probiotics-worth-it-how-much-2026.md`, `published_drafts/vaginal-probiotic-dosage-how-many-cfu-a-day-us-2026.md`, `published_drafts/vaginal-probiotics-on-an-empty-stomach-us-2026.md`, and `published_drafts/where-to-buy-vaginal-probiotics-in-the-us-5-checks-2026.md`. The PR itself says do not merge until the 13 heroes exist and `/pages/mike-moretti` is live. T3 owns the live 15B wording. |
| #122 | Stacked replay of #77. The 09:54 UTC merge `1fa33f6` put it onto #119 `e557298`, and GitHub is CLEAN against that base. The image-src conflict is gone. It still conflicts with #118 on `tests/test_ima2_retry.py`, both orders, including on the step-18 chain. Reconcile that test with #118 before it can follow wave 2. Until then #122 is not landable and #77 stays open. |
| #123 | Stacked replay of #38. Clean onto #120 `2302f4b` and clean onto main. On this chain it conflicts with #64 (`.cursor/rules/genseo-operating-rules.mdc`), #118 (`tests/test_ima2_retry.py`), and #124 (the four port files). Restack past #64, #118, and #124. The Mac Mini dry-run hold from #38 still applies. |

## Supersede

#81 is not an ancestor of #127. On the chain, #81 conflicts with #127 in `data/ai_visibility/prompt_set.json`, `docs/AI_VISIBILITY_MENTION_CITATION.md`, and `tests/test_ai_visibility.py`. #81 alone is still merge-clean, and the 20:35 merged-tree test still applies: `PromptSet` failed on the #81 tree (FloraFresh prompt order, including morning-or-night) and passed on the #127 tree (18 bank prompts). Leave #81 open until #127 is on main.

#85 is not an ancestor of #128. On the chain, #85 conflicts in `docs/PROMPT_LOSS_LIST.md` and `tests/test_prompt_loss_list.py`. #85 alone is still merge-clean. The 20:35 `PromptLossTests` failure (DONE set missing `fake-vaginal-probiotics-5-checks-in-the-us`, 23 vs 24) still describes that unchanged tip. Leave #85 open until #128 is on main.

#67 is the conflicting draft #116 replaces. Close is a recommendation only. This pass did not close it.

#115 is merge-clean against main (solo tree `e0340da62586f002dfd48d158f411ca41e0c7939`, tip `bdffeabb27c671503503062e8e6336cb4d365153`, base `cursor/sync-main-test-isolation-1101`, GitHub CLEAN) and conflicts with both #120 and #124 on `scripts/genseo_self_apply.sh`, `scripts/mac_return_reconcile.sh`, `tests/test_mac_return_reconcile.sh`, and `tests/test_self_apply.sh`. Land #124.

#111 conflicts with main in `tests/test_landing_rotation.py` and, once #118 is in the chain, also in `tests/test_queue_closures.py`. #118 is the clean replay.

#68 conflicts with main in `.cursor/rules/genseo-operating-rules.mdc`. Main already has `scripts/first_hand_experience.py`, wired into `scripts/validate_article.py` and `skills/genseo-auto-publish/SKILL.md`. #68 would add a second module, `scripts/experience_block.py`.

#117 still conflicts with main in `scripts/run_landing_headless.sh` and `scripts/run_ticket_headless.sh`. Its tree still says FloraFresh is 15B CFU and the blog byline is Mike Moretti (`AGENTS.md`, `DAILY-RUN.md`, `daily-tickets.md`, the three `.cursor/rules` files). It is not a landable successor for #9, #10, or #90. AgeAura on that branch stays NMN + TMG. Do not land #117 as it stands.

## CLOSE — recommendations only

Nothing was closed.

| PR | Recommendation | Why |
| --- | --- | --- |
| #68 | Close now. | The first-hand block is already on main. This branch conflicts and would add `scripts/experience_block.py`. |
| #67 | Close. | Open conflicting draft, superseded by #116 `60aee10`, which is in wave 2 and has the gate. #67 is not a git ancestor of that tip. Do not merge #67. Closing the draft does not delete #116. |
| #81 | Close after #127 is on main. | Merge-clean today, and wrong once the current topic bank is in the tree. |
| #85 | Close after #128 is on main. | Merge-clean today, and wrong once the current DONE set is in the tree. |
| #111 | Close after #118 is on main. | Conflicts. #118 is the clean fixture replay. |
| #115 | Close after #124 is on main. | Clean vs main, and conflicts with #120 and with #124. |
| #77 | Keep open. | Clean today. Conflicts once #119 is in. #122 is the replay. The #119 half of that restack landed at `1fa33f6`. It still conflicts with #118 on `tests/test_ima2_retry.py`. |
| #38 | Keep open. | Not a draft. Conflicts with main. #123 is the replay and now also conflicts with #124. Same Mini dry-run hold. |
| #9, #10, #90 | Keep open. | All conflict with main. #9 and #10 are not drafts. #117 is the intended guard replay and is not clean, and it still teaches 15B CFU and a Mike Moretti blog byline. |
| #95 | Keep open. | Solo conflict is `scripts/genseo_sync_main.sh`. On the chain it also conflicts with #118 and #124. Those hunks are not the same patch. Closing it now drops the delta the later PRs did not take. |
| #122, #123 | Keep open. | They are the replays of #77 and #38. #122 is on #119 and still conflicts with #118. #123 still needs a restack past #64, #118, and #124. Do not close them as if the work had landed. |
| #121 | Do not close. | Held, not superseded. Not touched. |
| #83 | Keep open. | Clean vs main, conflicts with #128. Close only after the referrer bullet is replayed, or after Kevin says the report itself will not land. |
| #117 | Do not close yet. | It is the only open guard bundle, and it is the wrong FloraFresh text. A later replay that keeps 1 billion CFU and Dr. Marcus Hale is what lets #9, #10, and #90 close. |

## OWNER — decisions needed

This pass did not choose these. Git-clean steps stay in the order above so the sequence is ready when the answer is GO.

1. **GO or hold the steps whose own text refuses the button.** #125 says "Draft only. Do not merge." #58 says "Do not merge until Kevin says so." #64 says "Still for Kevin" (install, the 14:47 quiet period, the 15-minute gap). #86's test plan says do not merge until a GO covers any blog body edit, article rebuild, or hreflang/title change. #86 does not publish. Pulling any of these out does not break the others: #125 is pairwise-clean with #127, #128, and #116, and steps 5–13 do not share files.
2. **#116 publish behavior.** Landing it makes `shopify_publisher.py` exit 2 before image upload when the Article URL is not the clean blog URL. #116's body asks Kevin whether to close #67. It does not itself say to hold the gate. #130's triage lists #116 under Kevin decision because this is a live-publish change. Decide whether wave 2 step 18 is a GO.
3. **#46 and #50.** Both are merge-clean against main and against the full chain. They stay out because the unpublished Turkesterone listicle and the unpublished AgeAura NMN + TMG listicle are product decisions. An older conflict with #96 on the listicle claim files is not a conflict against main.
4. **#121 stays held.** Chain-clean. New alt text in the diff says 15 billion CFU. T3 owns live FloraFresh wording. This pass did not touch the branch.
5. **#83.** Not in the order. Clean vs main, conflicts with #128, and the PR says do not merge until Kevin says so. Either replay the one referrer-domain bullet after #128, or leave #83 open.
6. **#38 / #123.** The Mini dry-run is still the product hold ("Do not merge until the Mini can run the dry-run"). Separately, #123 is not git-clean on this chain until it is restacked past #64, #118, and #124. #38 is not a draft and conflicts with main. Do not resolve-and-merge it from the button.
7. **Still conflicting, still waiting, not in the order.** #65 (`.gitignore` only vs main; live GEO fixes). #71 (`scripts/validate_article.py`; base of #73). #73 is GitHub-CLEAN against `cursor/entity-consistency-audit-1020` and conflicts with main in `scripts/shopify_publisher.py` and `scripts/validate_article.py`. #96 conflicts in `board/ideas.csv` and `templates/article-topic-bank.json` (unpublished price sweep; prices need a fresh check). #1 conflicts in `deploy/llms-txt/README.md`, `deploy/llms-txt/llms.txt`, and `scripts/shopify_publisher.py`. #1 is not a draft.
8. **#130.** Draft triage note from 2026-11-06. It puts #58, #64, #86, #125, and #116 in a Kevin-decision bucket. This board still lists them as merge-clean steps, with the holds named above. The two files do not overlap. Reconcile the buckets. Do not merge either board as if it were a code change.
9. **Non-drafts that also conflict with main:** #1, #9, #10, #38. Do not resolve-and-merge them from the button.

## Blockers

None inside the 18-step scratch merge. Each step applied clean.

Blocked until someone restacks, not by this order:

- **#122** now merges into rebased #119 (`1fa33f6`). It still cannot share a tree with #118 (`tests/test_ima2_retry.py`, both orders).
- **#123** cannot follow the chain once #64, #118, and #124 are in. It can still merge onto #120 alone. Do not merge it into the #120 branch ahead of #124; the two conflict.
- **#77 and #97** cannot share a tree with #119. They can share a tree with #116. #97 also conflicts with #122 `1fa33f6`, because that tip contains #119.
- **#83** cannot share a tree with #128.
- **#115** cannot share a tree with #120 or #124.
- **#121** is not a git blocker. It is a wording hold. Left untouched.

## Inventory — all 45 open PRs

Read at 2026-11-07 16:49 +07 from `gh pr list`, local `git merge-tree --write-tree origin/main <tip>`, and `git diff --name-only <base>...<tip>`. CI for every row is the empty queued state in the CI section. Behind / ahead is versus `origin/main`. Solo "clean" shows the first 12 hex digits of the merge tree. The wave table has the full tree for the 18.

| PR | Draft | Base | Tip | Behind / ahead | GitHub vs base | Solo vs main | Files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| #1 | no | main | `e4982bd433d5` | 277 / 5 | CONFLICTING / DIRTY | conflict (3) | 14 |
| #9 | no | main | `ad0cebfaa96d` | 273 / 4 | CONFLICTING / DIRTY | conflict (15) | 20 |
| #10 | no | main | `d7fb719589ce` | 273 / 4 | CONFLICTING / DIRTY | conflict (16) | 20 |
| #38 | no | main | `4a475e62bbc4` | 195 / 1 | CONFLICTING / DIRTY | conflict (3) | 10 |
| #46 | yes | main | `5baccfd631af` | 94 / 2 | MERGEABLE / CLEAN | clean `8fcb9b9107b5` | 9 |
| #50 | yes | main | `f844148bd300` | 94 / 2 | MERGEABLE / CLEAN | clean `d45e6517ebba` | 6 |
| #58 | yes | main | `6813af4b97cf` | 161 / 1 | MERGEABLE / CLEAN | clean `d57e765da98b` | 4 |
| #64 | yes | main | `63482afa293b` | 94 / 2 | MERGEABLE / CLEAN | clean `80a900334e6b` | 7 |
| #65 | yes | main | `e2984fb96471` | 94 / 5 | CONFLICTING / DIRTY | conflict (1) | 7 |
| #67 | yes | main | `4dc638451315` | 94 / 2 | CONFLICTING / DIRTY | conflict (1) | 12 |
| #68 | yes | main | `b3b416a83d13` | 144 / 1 | CONFLICTING / DIRTY | conflict (1) | 16 |
| #69 | yes | main | `b8baa228b76a` | 94 / 3 | MERGEABLE / CLEAN | clean `9abc5a89a53d` | 3 |
| #70 | yes | main | `544b0abfffa2` | 94 / 2 | MERGEABLE / CLEAN | clean `132ddc3efa85` | 5 |
| #71 | yes | main | `bebea7a1b140` | 94 / 3 | CONFLICTING / DIRTY | conflict (1) | 7 |
| #72 | yes | main | `c2c03bd8a9dd` | 94 / 2 | MERGEABLE / CLEAN | clean `e3c4de073fe1` | 5 |
| #73 | yes | `cursor/entity-consistency-audit-1020` | `8be49f663461` | 94 / 8 | MERGEABLE / CLEAN | conflict (2) | 11 |
| #75 | yes | main | `396cd02faa2b` | 94 / 2 | MERGEABLE / CLEAN | clean `40e8e3e1a909` | 6 |
| #77 | yes | main | `01a115e27094` | 94 / 2 | MERGEABLE / CLEAN | clean `535d36d85227` | 5 |
| #78 | yes | main | `bfd51a045618` | 94 / 2 | MERGEABLE / CLEAN | clean `b722f6e4ecc4` | 5 |
| #81 | yes | main | `a2c8b056c207` | 94 / 2 | MERGEABLE / CLEAN | clean `0d10cba1e44e` | 11 |
| #83 | yes | main | `6301fa5e67b8` | 94 / 2 | MERGEABLE / CLEAN | clean `2eda9bead1da` | 8 |
| #84 | yes | main | `9f9d4de5d835` | 94 / 2 | MERGEABLE / CLEAN | clean `0e568c5a32f9` | 9 |
| #85 | yes | main | `88457b2351e8` | 94 / 5 | MERGEABLE / CLEAN | clean `d0207446fc3a` | 7 |
| #86 | yes | main | `22b66f930df3` | 94 / 2 | MERGEABLE / CLEAN | clean `ec83d6daa495` | 6 |
| #90 | yes | main | `c3de3b81ac31` | 94 / 5 | CONFLICTING / DIRTY | conflict (4) | 58 |
| #95 | yes | main | `31180f390b56` | 94 / 4 | CONFLICTING / DIRTY | conflict (1) | 6 |
| #96 | yes | main | `29c6c2556cbe` | 94 / 5 | CONFLICTING / DIRTY | conflict (2) | 105 |
| #97 | yes | main | `d088ccb3ed27` | 94 / 1 | MERGEABLE / CLEAN | clean `40d0a155f831` | 2 |
| #111 | yes | main | `7cc561173119` | 94 / 1 | CONFLICTING / DIRTY | conflict (1) | 5 |
| #115 | yes | `cursor/sync-main-test-isolation-1101` | `bdffeabb27c6` | 93 / 1 | MERGEABLE / CLEAN | clean `e0340da62586` | 5 |
| #116 | yes | main | `60aee102b54f` | 0 / 4 | MERGEABLE / CLEAN | clean `3f40c96c3c5f` | 13 |
| #117 | yes | main | `4d96c57cf9f5` | 83 / 3 | CONFLICTING / DIRTY | conflict (2) | 19 |
| #118 | yes | main | `b6256f249f30` | 0 / 1 | MERGEABLE / CLEAN | clean `2293bf53e20f` | 7 |
| #119 | yes | main | `e557298e96d8` | 0 / 4 | MERGEABLE / CLEAN | clean `883c4381c3e2` | 2 |
| #120 | yes | main | `2302f4b62f10` | 0 / 1 | MERGEABLE / CLEAN | clean `7112e0e27827` | 4 |
| #121 | yes | main | `a694616c8092` | 83 / 3 | MERGEABLE / CLEAN | clean `5c2bfdc12923` | 87 |
| #122 | yes | `cursor/draft-local-image-gate-1102` | `1fa33f6a90fd` | 0 / 9 | MERGEABLE / CLEAN | clean `6245b57a89da` | 6 |
| #123 | yes | `cursor/hermetic-writer-ps-1102` | `58e59895b19a` | 83 / 4 | MERGEABLE / CLEAN | clean `6c4afc97cd89` | 13 |
| #124 | yes | `cursor/hermetic-writer-ps-1102` | `a068ae32350f` | 0 / 4 | MERGEABLE / CLEAN | clean `d4d3640f4a3d` | 7 |
| #125 | yes | main | `8875f68002b7` | 0 / 1 | MERGEABLE / CLEAN | clean `002a2c8fc643` | 11 |
| #126 | yes | main | `d2f07e8405b7` | 0 / 1 | MERGEABLE / CLEAN | clean `1ba991ce88d6` | 3 |
| #127 | yes | main | `83e0497afa92` | 4 / 2 | MERGEABLE / CLEAN | clean `c859bb259c56` | 11 |
| #128 | yes | main | `c9c90e4491bf` | 4 / 2 | MERGEABLE / CLEAN | clean `4c528216bcc7` | 7 |
| #129 | yes | main | `cdee61a26629` | 0 / 1 | MERGEABLE / CLEAN | clean `13c979637d81` | 1 |
| #130 | yes | main | `3e85c5877436` | 0 / 1 | MERGEABLE / CLEAN | clean `d6ae4873aac5` | 1 |

Conflict paths vs main (the 14 PRs whose solo merge-tree exits 1). #122 is not in this table. On tip `1fa33f6` it is GitHub-CLEAN against #119 and clean against main.

| PR | Conflict paths vs main |
| --- | --- |
| #1 | `deploy/llms-txt/README.md`, `deploy/llms-txt/llms.txt`, `scripts/shopify_publisher.py` |
| #9 | `.cursor/rules/genseo-landing-lane.mdc`, `.cursor/rules/genseo-operating-rules.mdc`, `.cursor/rules/genseo-ticket-queue.mdc`, `knowledge_base/AEO_GEO_GUIDELINES.md`, `scripts/brand_rules.py`, `scripts/build_landing_tickets.py`, `scripts/lint_tickets.py`, `scripts/refill_tickets.py`, `scripts/run_landing_headless.sh`, `scripts/run_ticket_headless.sh`, `scripts/shopify_publisher.py`, `scripts/topic_fitness.py`, `scripts/validate_article.py`, `skills/genseo-auto-publish/SKILL.md`, `templates/landing/listicle-angles.json` |
| #10 | `.cursor/rules/genseo-landing-lane.mdc`, `.cursor/rules/genseo-operating-rules.mdc`, `.cursor/rules/genseo-ticket-queue.mdc`, `docs/LABEL_OCR_GATE.md`, `knowledge_base/AEO_GEO_GUIDELINES.md`, `scripts/brand_rules.py`, `scripts/build_landing_tickets.py`, `scripts/lint_tickets.py`, `scripts/refill_tickets.py`, `scripts/run_landing_headless.sh`, `scripts/run_ticket_headless.sh`, `scripts/shopify_publisher.py`, `scripts/topic_fitness.py`, `scripts/validate_article.py`, `skills/genseo-auto-publish/SKILL.md`, `skills/genseo-landing-pages/SKILL.md` |
| #38 | `.cursor/rules/genseo-operating-rules.mdc`, `deploy/com.pati.genseo-landing.mini.plist`, `scripts/mac_return_reconcile.sh` |
| #65 | `.gitignore` |
| #67 | `skills/genseo-auto-publish/SKILL.md` |
| #68 | `.cursor/rules/genseo-operating-rules.mdc` |
| #71 | `scripts/validate_article.py` |
| #73 | `scripts/shopify_publisher.py`, `scripts/validate_article.py` |
| #90 | `board/ideas.csv`, `docs/LABEL_OCR_GATE.md`, `knowledge_base/AEO_GEO_GUIDELINES.md`, `templates/article-topic-bank.json` |
| #95 | `scripts/genseo_sync_main.sh` |
| #96 | `board/ideas.csv`, `templates/article-topic-bank.json` |
| #111 | `tests/test_landing_rotation.py` |
| #117 | `scripts/run_landing_headless.sh`, `scripts/run_ticket_headless.sh` |

## Reproduce

```bash
git fetch origin main
git rev-parse origin/main   # bf3ad1b7cd9723c310f3f6dae3f16ee2e9e18ba8
git merge-tree --write-tree --name-only --messages origin/main d2f07e8405b718201404894547d233bcb1efb5a0
git merge-tree --write-tree --name-only --messages origin/cursor/draft-local-image-gate-1102 1fa33f6a90fd269d9d0f12a1513c5e79d4311072
# exit 0 and one tree line: clean. CONFLICT lines are the hold.
# The pre-restack #122 tip e8e8154 conflicted on this base. 1fa33f6 does not.
# Sequential proof, local worktree only. Do not push it.
git worktree add --detach /tmp/land-sim origin/main
git -C /tmp/land-sim merge --no-ff --no-edit d2f07e8405b718201404894547d233bcb1efb5a0
```

The 18 tips in order: `d2f07e8` #126, `8875f68` #125, `83e0497` #127, `c9c90e4` #128, `6813af4` #58, `63482af` #64, `b8baa22` #69, `544b0ab` #70, `c2c03bd` #72, `396cd02` #75, `bfd51a0` #78, `9f9d4de` #84, `22b66f9` #86, `b6256f2` #118, `2302f4b` #120, `a068ae3` #124, `e557298` #119, `60aee10` #116. Step 18 tree on this pass: `96fe2f97ba60e11035a246d9a0f72528eb1b24bb`.

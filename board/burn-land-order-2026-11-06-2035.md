# LAND order — Burn1106-t55 (2026-11-06 20:35 ICT)

> Working recommendation moved on 2026-11-07 16:49 ICT to `board/burn-land-order-2026-11-07-1649.md`. The tables below are this snapshot and were not edited.

Draft for Kevin's GO. Nothing in this pass was merged, closed, retargeted, or marked ready. No branch was force-pushed or rebased. Nothing was published. No Shopify write, no Meta spend, no email. FloraFresh live 15B corrections stay with T3. AgeAura in this order is NMN + TMG only.

`origin/main` is `bf3ad1b7cd9723c310f3f6dae3f16ee2e9e18ba8` (2026-11-06 13:21:54 +0700, "cherish_auto: add band guarantee line + rail TOC the shell prints"). 43 pull requests are open. Every one of them is in a section below.

Evidence is `git merge-tree --write-tree --name-only --messages origin/main <tip>` (git 2.43.0), then the same command along the chain below. A listed tree is the merge result. Re-running the command on these SHAs produces the same tree. "Chain tree" is the result after every earlier step in that wave has been applied. This burn did not run `bash tests/run_suite.sh`. The two unittest classes in the supersede section ran one after another on `/usr/bin/python3`.

## Wave 1 — GO, in this order

These 13 drafts merge cleanly onto current main, and they still merge cleanly when applied in this order. Steps 1–4 stay in this order: the profile fix, the 1 billion CFU doc lock, then #127, then #128. Steps 5–13 do not share files with each other, so their relative order is free.

| Step | PR | Branch | Tip | Behind / ahead | Solo tree vs main | Chain tree |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | #126 | `cursor/hermetic-store-profile-b59c` | `2dbe163d707069c93efcac788209544f6a8648f1` | 4 / 1 | `1ba991ce88d6ebc4cda4aa06799f83afd66d36da` | `1ba991ce88d6ebc4cda4aa06799f83afd66d36da` |
| 2 | #125 | `cursor/florafresh-1b-snz1969-lock-366e` | `0548ecdbd9a1f368b9e97741c985dad9813a6a39` | 4 / 1 | `002a2c8fc643de18cdf8a2a8dcea10a80fa23581` | `6abf863cfcb47f2b8dce6c517ffda61bb6eba96b` |
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

Chain tip after step 13: tree `a87100218f81e1e4b70f8df1dfadddfee2f2a1f8`.

What each step is:

1. **#126 suite enabler.** Checkout-relative Wellness Nest paths in `scripts/store_profiles.py`, `stores/wellnessnest/profile.json`, and `tests/test_store_isolation.py`. A worktree of main rejects `Profile("wellnessnest")` because the profile names absolute `/Users/kevinkreative/genseo/...` paths. This is the first land so later suite runs in a worktree can construct the profile. It does not touch `test_queue_closures` (that fixture is #118). Pairwise merge-tree with #118 is clean. No overlap with the rest of wave 1.
2. **#125 FloraFresh docs lock, before the refresh tips.** Docs, the failed 2026-10-21 landing ticket line, striking-distance proposals, and tests. `scripts/florafresh_rules.py` on main is already `CFU = "1 billion CFU"`. This PR makes the instruction files match that lock and marks the 2026-10-21 striking-distance proposals do-not-apply. It does not edit a live post. The guidelines hunk is the 2026-10-09 product-identity bullet (15B sentence replaced with 1 billion CFU). AgeAura stays NMN + TMG. Blog byline in that doc stays Dr. Marcus Hale until `/pages/mike-moretti` is HTTP 200.
3. **#127, the landing head for the AI mention/citation work.** See the supersede section. Inserts the mention-vs-citation bullet above the 2026-10-08 reviews line in `knowledge_base/AEO_GEO_GUIDELINES.md`.
4. **#128, the landing head for the buyer prompt-loss list.** Inserts its bullet directly under that same reviews line. Clean after #127. See the supersede section.
5. **#58 disabled off-Mac heartbeat.** Adds `.github/workflows/genseo-cloud-failover.yml`. The job's `if` is `vars.GENSEO_CLOUD_FAILOVER == '1'`. Unset stays off, so a merge does not arm the cron. The script does not publish.
6. **#64 opt-in login catch-up.** Plist under `deploy/`, plus `scripts/genseo_boot_catchup.py`. This is the step that later blocks #123: both edit `.cursor/rules/genseo-operating-rules.mdc`.
7. **#69** read-only GEO direct-to-deep-content sessions.
8. **#70** read-only PDF COA vs HTML audit for 2026-10-19.
9. **#72** AgeAura AI Mode gap map. Crawl quotes in the doc mention Urolithin A on old protocol pages. The doc says Urolithin is not the AgeAura SKU this cluster may promote. The product in the map is NMN + TMG.
10. **#75** off-page listicle gap list for AgeAura and ShilaSource.
11. **#78** read-only quarterly news-blog audit.
12. **#84** read-only mobile clutter audit.
13. **#86** brand-SERP notes for the 2026-10-21 position slide.

#83 was on the previous LAND-clean list. It is clean against main alone (solo tree `2eda9bead1dadb3f38077ca9f8c833d0ae8a03af`, tip `6301fa5e67b8ceeabf23edf65ab1f2674f094f40`, 94 behind / 2 ahead) and it is clean after #127. It conflicts with #128. Both insert a bullet immediately after the 2026-10-08 reviews line in `knowledge_base/AEO_GEO_GUIDELINES.md`. Landing #83 before #128 conflicts the same way. Hold #83 out of this GO. The next burn replays that one referrer-domain bullet onto the post-#128 guidelines.

## Supersede #81 → #127 and #85 → #128

Both old heads are merge-clean against this main. GitHub's CLEAN state matches merge-tree. The reason to land the refresh tips is the tests on the merged tree, not a conflict.

| Head | Tip | Solo tree vs main | Merged-tree tests |
| --- | --- | --- | --- |
| #81 `cursor/ai-visibility-mention-citation-1020` | `a2c8b056c207464ce4df1a6dd0123e1b8044c3d4` | `0d10cba1e44ed1c33a8beae38746f2273fd6a236` | `PromptSet`: 7 tests, 1 failed |
| #127 `cloud/81-refresh-1105b` | `83e0497afa92fcc935f74d37147ad1232f7d1e0e` | `c859bb259c5649646c5512fcf1da949c3880d115` | `PromptSet`: 7 tests, OK |
| #85 `cursor/prompt-loss-list-1021` | `88457b2351e8847f1245d7fd050879657b1fd5f1` | `d0207446fc3acef63ac926f645467fc408989216` | `PromptLossTests`: 11 tests, 2 failed |
| #128 `cloud/85-refresh-1105b` | `c9c90e4491bf04d43730276fdbee8395811837e3` | `4c528216bcc79034ed9aee7e5e145c9398223f75` | `PromptLossTests`: 11 tests, OK |

#81 is not an ancestor of #127. They share merge-base `6c46771` with the old main. The merged-tree diff of #127 against #81 is three files: `data/ai_visibility/prompt_set.json`, `docs/AI_VISIBILITY_MENTION_CITATION.md`, and `tests/test_ai_visibility.py` (41 insertions, 17 deletions). On the #81 merge, `florafresh_bank_problems` returns `FloraFresh prompt order drifted from the topic bank`. That catalog has 15 FloraFresh prompts, including `florafresh-florafresh-morning-or-night`. Current `templates/article-topic-bank.json` on main has 18 FloraFresh primaries. The #127 merge has those 18, in bank order, and drops the morning-or-night id. Added ids: odor, after-sex, fake, with-coffee. A Urolithin-only mention still does not count as AgeAura. AgeAura stays NMN + TMG. FloraFresh in the guard stays SNZ-1969 at 1 billion CFU.

#85 is not an ancestor of #128. Same old merge-base. The merged-tree diff is `docs/PROMPT_LOSS_LIST.md` and `tests/test_prompt_loss_list.py`. On the #85 merge, `test_real_list` fails because the live DONE set contains `fake-vaginal-probiotics-5-checks-in-the-us` and the old expected set does not. `test_committed_docs_match_render` fails on 23 DONE URLs in the committed doc versus 24 in the render. The #128 merge counts that URL. The URL is listed and is not a prompt. Urolithin is not a prompt.

Leave #81 and #85 open until #127 and #128 are on main. Then close them as superseded. This pass did not close them.

## Wave 2 — GO after wave 1, in this order

Still a draft GO. These five are sequentially clean on top of wave 1's chain tree `a87100218f81e1e4b70f8df1dfadddfee2f2a1f8`. They are also each clean against main alone.

| Step | PR | Branch | Tip | Behind / ahead | Solo tree vs main | Chain tree |
| --- | --- | --- | --- | --- | --- | --- |
| 14 | #118 | `cursor/hermetic-unittest-flakes-1102` | `f910ecc9d80c12808059a20b5388d57d6b3b5a2c` | 83 / 1 | `2293bf53e20fa7a9d856272ed3d9d25485465ea4` | `3f21b3c377881cb9cb42f7949cb521fce3e7105f` |
| 15 | #120 | `cursor/hermetic-writer-ps-1102` | `47f45a01bb431dd4578fca922c0240e76a1143af` | 83 / 1 | `7112e0e278275a46141cbd7da91cb7d15801f9bf` | `ff0dd79b27362061c80ef08a9c76cc11db52a997` |
| 16 | #124 | `cursor/port-115-sync-main-onto-120-64e7` | `5e2888d8129a752f2a66ca996de473e4f42b6834` | 83 / 3 | `4f6eb8298307dcb088e82723fd2723adeea3408a` | `a512fe9bffc34b149faa1a5f634789122f61a7ae` |
| 17 | #119 | `cursor/draft-local-image-gate-1102` | `4c8a749537188e1c146b2ef44c94077f49bb03c0` | 83 / 4 | `883c4381c3e28e1a1c79f68c89f506988010b577` | `5755fa807377a697ab8351d70884db85ca2759c9` |
| 18 | #116 | `cursor/canonical-url-gate-supersede-67-1102` | `1f401b95c2625e53a4b1d0cf91e802a6bbcad9fa` | 83 / 5 | `66b37054756275578e62f8bdb3f37de78dfb8d4f` | `957c78dc524018b5e59b66ad9b4481b1db8ca7bb` |

14. **#118 hermetic queue and ima2 tests.** Freezes landing-queue and closure fixtures under `tests/fixtures/queues/` and changes `tests/test_ima2_retry.py` so the timeout test execs `/usr/bin/perl` directly. This is the landing vehicle for the #111 goal. Test-only diff.
15. **#120 hermetic writer tests.** `scripts/genseo_self_apply.sh`, `scripts/mac_return_reconcile.sh`, and their tests. The branch description says production still scans `ps` and fail-closes, and the test flags are ignored unless set. #120's tip is an ancestor of both #123 and #124.
16. **#124 port of #115 onto #120.** Includes #120. Adds checkout-scoped job matching in `scripts/genseo_self_apply.sh`, `scripts/genseo_sync_main.sh`, and `scripts/mac_return_reconcile.sh`. This one does change those scripts' production matching. Land this instead of #115. Merging #115 onto #124 conflicts in `scripts/genseo_self_apply.sh`, `scripts/mac_return_reconcile.sh`, `tests/test_mac_return_reconcile.sh`, and `tests/test_self_apply.sh`. #115's own base `ffe14da` (#114) is already in main, and #115 alone is clean against main (solo tree `e0340da62586f002dfd48d158f411ca41e0c7939`, tip `bdffeabb27c671503503062e8e6336cb4d365153`, 93 behind / 1 ahead). That solo result is why it looks landable. The chain says the landing head is #124.
17. **#119 remote-image draft gate.** `scripts/validate_article.py` and `tests/test_draft_image_src.py`. A draft markdown image `src` that is not a local path fails closed. Tip `4c8a749` is two commits past the SHA #122 was stacked on (`f5f60b7`).
18. **#116 canonical URL gate, the replay of #67.** #67's tip `4dc63845131590ce8ca7da7edd1429ef84de051a` is an ancestor of #116. #67 itself conflicts with main in `skills/genseo-auto-publish/SKILL.md` only. #116 calls `_canonical_prepare` before image upload on publish and update, and exits 2 when the Article URL is not that article's clean blog URL. The guidelines edit is the lint sentence for the canonical checks, and it merged cleanly after #125, so the 1 billion CFU bullet stays. `tests/test_first_publish_url.py` uses a fixture byline `Mike Moretti` and asserts the publisher sends that author through. `roster.json` on main is still Dr. Marcus Hale. This PR does not change the roster.

## Merge-clean, held out of this GO

| PR | Why it is held | Evidence |
| --- | --- | --- |
| #83 | Clean vs main. Conflicts with #128 on the reviews-line bullet in `knowledge_base/AEO_GEO_GUIDELINES.md`. | Solo tree above. Chain: clean after #127, conflict on #128 in both orders tried. |
| #97 | Shopify 429 on the draft dead-link check stays `UNVERIFIED` (exit 3). Clean vs main and clean on top of wave 1. Conflicts with #119 and with #116 on `scripts/validate_article.py`. | Solo tree `40d0a155f8311147101d66f0678e5f49489c7ca2`. Tip `d088ccb3ed275fc0d61a0847a208bc2d6b32f286`, 94 behind / 1 ahead. |
| #77 | Warn-only near-duplicate gate. Clean vs main and clean on top of wave 1. Conflicts with the wave 2 chain once #119 is in, on `scripts/validate_article.py`. The stacked replay is #122. | Solo tree `535d36d8522754b1fad3295fccbd221c1d751d07`. Tip `01a115e27094a9b1b55a19cd73a76921a560f5cc`. |
| #121 | Image paths in 19 published drafts move to checkout-relative `assets/`. Merge-tree is clean through wave 2 (chain tree `ac931d448342dcd062e7bc874d3a1342f0b51b0f`; solo tree `5c2bfdc12923433d9ab9cea2f21ddadcfd47a9a2`). The markdown rewrite states **15 billion CFU** in FloraFresh alts, including `published_drafts/are-vaginal-probiotics-worth-it-how-much-2026.md`, `published_drafts/vaginal-probiotic-dosage-how-many-cfu-a-day-us-2026.md`, `published_drafts/vaginal-probiotics-on-an-empty-stomach-us-2026.md`, and `published_drafts/where-to-buy-vaginal-probiotics-in-the-us-5-checks-2026.md`. Live FloraFresh corrections are with T3. | 84 `published_drafts` paths plus `scripts/draft_image_paths.py`, `scripts/shopify_publisher.py`, and `tests/test_draft_image_paths.py`. |
| #122 | Stacked replay of #77 onto #119. Merge-tree of #122 onto the current #119 tip is clean, and #122 onto wave 1 is clean. #122's tip `e8e8154` does not contain #119's later commits `2ed1c43` and `4c8a749`, so merging #122 by itself leaves those two image-src fixes out. After #118 is in the chain, #122 conflicts on `tests/test_ima2_retry.py`. | Tip `e8e8154dbbd86f67ef80ea00c8063d4e1a088ea8`. Base on GitHub is `cursor/draft-local-image-gate-1102`. Stack point is `f5f60b7`, not the current #119 tip. |
| #123 | Stacked replay of #38 onto #120. #120's tip is an ancestor. Pairwise, #123 and #124 merge cleanly in either direction. On top of wave 1, #123 conflicts with #64 in `.cursor/rules/genseo-operating-rules.mdc`. On top of wave 2 it also conflicts with #118 on `tests/test_ima2_retry.py`. | Tip `58e59895b19a26837c541d25de87796660bc150f`. |

## OWNER — still waiting on Kevin

Open. This pass did not close them and did not refresh their branches.

| PR | Merge-tree vs main | Wait |
| --- | --- | --- |
| #46 | Clean. Solo tree `8fcb9b9107b5fc2b282b1e595ebabc91827056f6`. Tip `5baccfd631af6de6e24fd4120250d528da3bfde5`, 94 behind / 2 ahead. | Unpublished Turkesterone listicle. Price and claims are still Kevin's. |
| #50 | Clean. Solo tree `d45e6517ebbaa57f6f12242968cabd9acf838614`. Tip `f844148bd3009cf3432f41a5d358af0f35b93b13`, 94 behind / 2 ahead. | Unpublished AgeAura NMN + TMG listicle. The page stays unpublished. |
| #65 | Conflict in `.gitignore` only. Other paths auto-merge. Tip `e2984fb96471d24d07109af557a9c349e61a5890`. | GEO delta audit and the live-fix script. Theme JSON-LD stays out of #116 on purpose. |
| #71 | Conflict in `scripts/validate_article.py`. Tip `bebea7a1b1408eca21b7f28d61fa3063a730d0db`. | Base of #73. Entity-consistency audit. |
| #73 | Conflict in `scripts/shopify_publisher.py` and `scripts/validate_article.py`. GitHub base is `cursor/entity-consistency-audit-1020` (#71), not main. Tip `8be49f663461df365b86a9b584481db8d3bc9d54`. | SEO entity fixes. Retarget only after #71 has a clean replay onto main. |
| #96 | Conflict in `board/ideas.csv` and `templates/article-topic-bank.json`. Tip `29c6c2556cbe9c82154fafa87a749edb6e1a1469`. | Unpublished landing price sweep from the 2026-10-26 product JSON. |
| #1 | Conflict in `deploy/llms-txt/README.md`, `deploy/llms-txt/llms.txt`, and `scripts/shopify_publisher.py`. Tip `e4982bd433d5190beea8fb6003c5c30414e607ca`, 277 behind / 5 ahead. | IndexNow and `llms.txt`. Not a draft. Theme and live ping stay held. |

#46 and #50 are merge-clean against this main. An older board had them conflicting with #96 on the listicle claims files. That is no longer a conflict against main. They stay on the owner list because the unpublished offers are a product decision, not because git is blocked.

## CLOSE — recommendations only

Nothing was closed.

| PR | Recommendation | Successor status |
| --- | --- | --- |
| #67 | Close after #116 is on main. | #116 contains #67. #67 conflicts with main in `skills/genseo-auto-publish/SKILL.md`. |
| #111 | Close after #118 is on main. | #111 conflicts in `tests/test_landing_rotation.py`. #118 is the clean fixture replay and is wave 2 step 14. |
| #115 | Close after #124 is on main. | #115 is clean against main and conflicts with #124 on the four checkout-scope files. Land #124. |
| #77 | Keep open until #122 is restacked past #118 and landed. | #77 is merge-clean today. #122 is the replay and currently conflicts with #118 on `tests/test_ima2_retry.py`. |
| #38 | Keep open until #123 is restacked past #64 and #118 and landed. | #38 conflicts in `.cursor/rules/genseo-operating-rules.mdc`, `deploy/com.pati.genseo-landing.mini.plist`, and `scripts/mac_return_reconcile.sh`. #123 is not an ancestor of that old tip. |
| #9, #10, #90 | Keep open. | The intended guard replay is #117. #117 conflicts with main in `scripts/run_landing_headless.sh` and `scripts/run_ticket_headless.sh`. Its docs still say FloraFresh is 15B CFU of SNZ-1969 (a comment; it does not edit `scripts/florafresh_rules.py`). #90 also conflicts, in `board/ideas.csv`, `docs/LABEL_OCR_GATE.md`, `knowledge_base/AEO_GEO_GUIDELINES.md`, and `templates/article-topic-bank.json`, and it was built on the closed 15B era. |
| #68 | Close. The first-hand block is already on main as `scripts/first_hand_experience.py`, wired into `scripts/validate_article.py` and `skills/genseo-auto-publish/SKILL.md`. | #68 conflicts in `.cursor/rules/genseo-operating-rules.mdc` and would add a second module, `scripts/experience_block.py`. |
| #95 | Keep open. | Conflict is `scripts/genseo_sync_main.sh` only. Queue-fixture intent overlaps #118, and #114 already landed a hermetic `test_sync_main`. The self-apply delta on this branch is not the same patch as #124. Closing it now drops that delta. |
| #81, #85 | Close after #127 and #128 are on main. | Merge-clean, and wrong once main's topic bank and DONE set are in the tree. See the supersede section. |

## Next burn

1. Replay #83's single referrer-domain bullet onto the guidelines after #128. Then #83 can land, or close as superseded by that replay.
2. Restack #122 onto the post-#118 tree. Keep #119's tip `4c8a749` (land #119 first). Reconcile the ima2 timeout hunk with #118's perl-exec test. Then #77 can close.
3. Restack #123 onto the post-#64 + #118 + #120 tree. The operating-rules hunk and the ima2 hunk are the two conflicts. Then #38 can close.
4. Split #121. The path jail in `scripts/draft_image_paths.py` is separable from the FloraFresh alt lines that still say 15 billion CFU. T3 owns the live 15B wording. The merge is already clean; the hold is the wording.
5. Replay #117's FusiForce and shilajit-gummies guards onto current main without the 15B CFU sentences, and resolve `scripts/run_landing_headless.sh` and `scripts/run_ticket_headless.sh`. Then #9, #10, and #90 can close.
6. Land #97's 429-unverified exit either before wave 2 or as a replay onto the post-#116 `scripts/validate_article.py`. It is clean today and becomes a conflict once #119 or #116 lands.
7. After #124 is on main, close #115. There is no second copy to merge.

## Reproduce

```bash
git fetch origin main
git rev-parse origin/main   # expect bf3ad1b7cd9723c310f3f6dae3f16ee2e9e18ba8
git merge-tree --write-tree --name-only --messages origin/main origin/cloud/81-refresh-1105b
git merge-tree --write-tree --name-only --messages origin/main origin/cloud/85-refresh-1105b
```

Exit 0 and a single tree line means clean. Conflict lines are the hold. A full-suite run, if anyone uses one as extra proof, has to be serial. This board's proof is merge-tree plus the two unittest classes on the merged trees.

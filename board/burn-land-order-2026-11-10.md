# LAND order — 2026-11-10 16:48 ICT

Draft for Kevin. This pass added this file and a one-line pointer on `board/burn-land-order-2026-11-07-1649.md`. Nothing was merged, closed, retargeted, marked ready, or published. No Shopify write. #121 was not checked out, edited, pushed, rebased, or commented.

Prior snapshot: `board/burn-land-order-2026-11-07-1649.md`. Its tables were not edited.

`origin/main` is still `bf3ad1b7cd9723c310f3f6dae3f16ee2e9e18ba8` (2026-11-06 13:21:54 +0700, "cherish_auto: add band guarantee line + rail TOC the shell prints"). 47 pull requests are open. The 16:49 board counted 45. The two new drafts are #131 and #132, pinned copies of the tips that board used for #127 and #128. Every open PR is in the inventory.

Evidence is `git merge-tree --write-tree` on git 2.43.0, then `git commit-tree` for the next parent. Those scratch commits stayed in this clone. They were not branched and not pushed. Re-running merge-tree on the SHAs below has to reproduce the trees. This pass did not run `bash tests/run_suite.sh`. There are no files under `.github/workflows` on this main. Check-runs were not re-queried.

GitHub `mergeable` / `mergeStateStatus` in the inventory is against the PR base. That base is not main for #73, #115, #122, #123, and #124.

## Recommended order

One sequence. Steps 1–18 are the same pull requests, in the same order, as the 16:49 board. Each step merged clean. The chain tree after every step matches that board, including step 18 `96fe2f97ba60e11035a246d9a0f72528eb1b24bb`.

#127 and #128 have new tips. Each new tip is 0 behind main. Merging the old tip (now #131 / #132) onto main produces the same tree as merging the new tip. Swapping #127 and #128 after #125 still ends at step-4 tree `6145f1b8e7584c073a65c61837ccfc8d5462799e`.

#122 `6def68d` is clean after #119, including on the finished 18-step chain. Landing it immediately after step 17 and then landing #116 ends at the same tree as landing it after step 18: `fb7af14d61644e3f23c66dcf96bfa679cd3884bc`. This order keeps the 18-step chain intact and appends #122.

The Shopify 429 check to land is branch `t69-97-on-122` at `af350ba`, after #122. There is no open PR for that branch. #97's own tip still conflicts with the chain on `scripts/validate_article.py`.

| Step | PR | Branch | Tip | Behind / ahead | Solo tree vs main | Chain tree |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | #126 | `cursor/hermetic-store-profile-b59c` | `d2f07e8405b718201404894547d233bcb1efb5a0` | 0 / 1 | `1ba991ce88d6ebc4cda4aa06799f83afd66d36da` | `1ba991ce88d6ebc4cda4aa06799f83afd66d36da` |
| 2 | #125 | `cursor/florafresh-1b-snz1969-lock-366e` | `8875f68002b704ec4d2a24a9f9f1232d0bdd7417` | 0 / 1 | `002a2c8fc643de18cdf8a2a8dcea10a80fa23581` | `6abf863cfcb47f2b8dce6c517ffda61bb6eba96b` |
| 3 | #127 | `cloud/81-refresh-1105b` | `cc6e639aabede85bde64dfbb4a3785354e5b2122` | 0 / 2 | `c859bb259c5649646c5512fcf1da949c3880d115` | `2311e951271cebf32c3301989766aab616653d8a` |
| 4 | #128 | `cloud/85-refresh-1105b` | `bc901715c94fd6d084f99a5f2fb9d7490b70f4f0` | 0 / 2 | `4c528216bcc79034ed9aee7e5e145c9398223f75` | `6145f1b8e7584c073a65c61837ccfc8d5462799e` |
| 5 | #58 | `cursor/cloud-failover-scaffold-2d90` | `6813af4b97cf5d51e5dff122585c313a780e88c6` | 161 / 1 | `d57e765da98b698c4d8b54597cb4c31fce22d122` | `fba84a5c68fba6918a4ec4a986d59b3b13136f0f` |
| 6 | #64 | `cursor/boot-catchup-8034` | `63482afa293bf08f48a06c286b7678935f0f6ec8` | 94 / 2 | `80a900334e6b133926af45522f519420b303bcbf` | `5cdd4fbacb8052fae06a30f754e94d72644ae295` |
| 7 | #69 | `cursor/geo-direct-deep-content-7b88` | `b8baa228b76afc2c024e083f6b28eae4ab12ca75` | 94 / 3 | `9abc5a89a53d6c23fe1d558c0c08f896710f23bb` | `2d4c665892f913b36ec322c6f96db053cc438ecb` |
| 8 | #70 | `cursor/coa-pdf-html-audit-df6a` | `544b0abfffa290c10c31cd442a2bc1db71d4a5ba` | 94 / 2 | `132ddc3efa8503793a1751f988e45e5423214835` | `a634388c0775762c91ab52e2ffe93721fb50fc62` |
| 9 | #72 | `cursor/ageaura-ai-mode-gap-map-1020` | `c2c03bd8a9dd05cbfd3508e80077c9bd48b5431b` | 94 / 2 | `e3c4de073fe16c9bad8a3f98c7363282c27087ec` | `76820e2ce79e676c5a8fa2dbb0b4dc4f1f77f5c3` |
| 10 | #75 | `cursor/offpage-listicle-gap-1020` | `396cd02faa2b72c7174b9ca506833541e6cba368` | 94 / 2 | `40e8e3e1a90967f42799cde3dca37b9b0038f81f` | `ed64eae0cdf86983ff579d09133d97b672eaa5e5` |
| 11 | #78 | `cursor/quarterly-content-audit-78b5` | `bfd51a045618d1605e7139dc9e1587dd1041595d` | 94 / 2 | `b722f6e4ecc43be25e0c62e4d3e110f2afb78bf3` | `85934a07278e4be09ff6008e64e33144fc88515c` |
| 12 | #84 | `cursor/mobile-clutter-audit-1021` | `9f9d4de5d8357a797933b801c7f3704a2d7ede5e` | 94 / 2 | `0e568c5a32f94438c5a0a489996dc0a1f22eb738` | `5f597094519088c5be37c4fe77e3be99ab21e15e` |
| 13 | #86 | `cursor/brand-serp-slide-1021` | `22b66f930df30409bd9a61741a4c5e41eefb139e` | 94 / 2 | `ec83d6daa4956dab10809f7e097a97e5fdb7ee9a` | `a87100218f81e1e4b70f8df1dfadddfee2f2a1f8` |
| 14 | #118 | `cursor/hermetic-unittest-flakes-1102` | `b6256f249f30ce40ff2fadcffe6e1db7d96dcb4f` | 0 / 1 | `2293bf53e20fa7a9d856272ed3d9d25485465ea4` | `3f21b3c377881cb9cb42f7949cb521fce3e7105f` |
| 15 | #120 | `cursor/hermetic-writer-ps-1102` | `2302f4b62f103c74fb4c02c9711eb21533073d59` | 0 / 1 | `7112e0e278275a46141cbd7da91cb7d15801f9bf` | `ff0dd79b27362061c80ef08a9c76cc11db52a997` |
| 16 | #124 | `cursor/port-115-sync-main-onto-120-64e7` | `a068ae32350ff52c236a65f0e1a0bc0d0eac20c1` | 0 / 4 | `d4d3640f4a3d24166b36e21e4f5dbc5708722d92` | `1dc7c3ae14d638ea472b531f8a2b8d82a2084984` |
| 17 | #119 | `cursor/draft-local-image-gate-1102` | `e557298e96d8115dbd408aff21e12efa379b704a` | 0 / 4 | `883c4381c3e28e1a1c79f68c89f506988010b577` | `ac39e6de002f25468364d42d2529ae77f89c1df6` |
| 18 | #116 | `cursor/canonical-url-gate-supersede-67-1102` | `60aee102b54f365b1b83eac83f0489786c89b314` | 0 / 4 | `3f40c96c3c5f8bd414140670077e3a58396a9666` | `96fe2f97ba60e11035a246d9a0f72528eb1b24bb` |
| 19 | #122 | `t30-77-on-119` | `6def68d7206af24342452617509e61814b958a2c` | 0 / 10 | `058cdd445e5d8a21c254a3f917f7023c9d77efa0` | `fb7af14d61644e3f23c66dcf96bfa679cd3884bc` |
| 20 | `t69-97-on-122` | `t69-97-on-122` | `af350ba372ef840696eb82ac02d15cab2786512b` | 0 / 12 | `6645a037b8d81c0da990cfb3b2352261b95b88e8` | `0a2bbcd42e2810648d4ab79d98d3d2f9934538db` |

Step 20 has no pull request. Its parents are #122 `6def68d` and #97 `d088ccb3`. The diff against #122 is `scripts/validate_article.py` and `tests/test_draft_link_429.py`. HTTP 429 that is still there after retries is `WARN/UNVERIFIED` and exits 3. Exit 0 remains the only publishable result.

## Step 21 — `t70-123-on-chain` is on origin

Noted 2026-11-10 21:07 ICT. This note does not merge, close, retarget, or publish. #121 was not touched. No pull request was opened for `t72-123-runatload`.

`origin/t70-123-on-chain` is `7c15da6ed38139945662305470a41c20ba38b67f`. Parents are `b649e64` (the 19-step chain through #122) and #123 `0105335`. `tests/test_ima2_retry.py` on that commit is blob `e01843a2c4750449aec411f29bdfededfde48c82`, the same blob as #118. The 1-second readiness wait stayed. #123's 8-second spawn-time blob `df73f883` did not.

`test_only_the_catchup_agent_runs_at_load` fails on `7c15da6`. The assertion is `True is not False : com.pati.cursor-agent-worker.plist`. #64 requires every `deploy/*.plist` except `com.pati.genseo-catchup.plist` to set `RunAtLoad` false, so a calendar content job cannot start at login. #123's `deploy/com.pati.cursor-agent-worker.plist` sets `RunAtLoad` and `KeepAlive` true. That installer writes the plist and does not call launchctl. The documented start is `launchctl bootstrap`, which starts the worker because `RunAtLoad` is true, and `tests/test_mac_mini_failover_bootstrap.sh` rejects a rendered worker whose `RunAtLoad` is not true. The other six deploy plists stay `RunAtLoad` false. The failure is the catch-up test's blanket else, written before the worker existed. The worker already starts at load under #123.

`origin/t72-123-runatload` is `01819f4f129ef17efbf0fa512d52eccdc56939ec`, one commit on `7c15da6`. The worker plist bytes are unchanged (`92c72f67`). The test allowlists that plist, requires `KeepAlive` true, no calendar, and `worker start --name`, and still requires `RunAtLoad` false on every other non-catch-up plist.

Same VM, `/usr/bin/python3`, Pillow 13.0.0: 723 tests. `7c15da6` is 6 failures / 28 errors. `01819f4` is 5 failures / 28 errors. The only name that moved is `test_only_the_catchup_agent_runs_at_load`. Shell files on `01819f4`: 15 pass / 0 fail. On `7c15da6` those shell files pass once Pillow imports; `test_boot_catchup.sh` had exited at `python_bin.sh` before that install, then 42 checks / 0 failed. No rate-limit or usage warning in those logs.

## Decisions waiting on Kevin

This pass did not choose these. Items 1 and 2 are still waiting. Item 3 is settled on `7c15da6`.

1. **GO to land wave 1: #126 → #125 → #127 / #128.** All four are merge-clean onto main and onto this chain. #127 and #128 may swap; the step-4 tree stays `6145f1b8e7584c073a65c61837ccfc8d5462799e`. Steps 5–18 stay in the order above and were not given a new GO by this pass.
2. **Close #77. Do not merge it.** The dup-cluster gate in #122 is the same bytes. Merging #77 onto the 18-step chain conflicts in `scripts/validate_article.py`. Branch `t69-77-on-122` (`d46da63`) merges #77 onto #122 and the result tree equals #122's tree `058cdd445e5d8a21c254a3f917f7023c9d77efa0`, so #77 adds nothing once #122 is present.
3. **#123 ima2 timeout is resolved: keep #118's 1-second readiness wait.** `t70-123-on-chain` `7c15da6` is on origin and carries blob `e01843a2`. At 16:48 ICT that branch was not on origin (`git ls-remote --heads origin t70-123-on-chain` was empty). The conflict that choice settled: #123 `01053354` is clean onto #120 and clean with #124 in both orders. On the full chain it conflicts in two files:
   - `.cursor/rules/genseo-operating-rules.mdc`, against #64. The only conflict hunk is the last line of the read-only bash block: #64 adds `bash tests/test_boot_catchup.sh`, #123 adds `bash tests/test_mac_mini_failover_bootstrap.sh`. Both lines can be kept.
   - `tests/test_ima2_retry.py`, against #118, both orders. This was the behavior choice, and it is settled. #118 (blob `e01843a2c4750449aec411f29bdfededfde48c82`, and the blob the chain still has after #122) execs `/usr/bin/perl` directly and starts the 1-second timeout only after the grandchild pidfile is ready. #123 (blob `df73f883d81a2280a012b3c92b2e8a8ed697634f`) keeps a spawn-time timeout and raises it from 1 second to 8. The sleeper still sleeps 30 seconds, so 8 seconds must still expire and the process tree must be killed. Neither diff changes a production timeout. The chain keeps #118, because #122's copy of this file is main's blob `4a2fe042b99c2d9c15faf186941a673b6427243c`. `7c15da6` kept that #118 blob. The RunAtLoad follow-up is step 21.

## Claims checked

**18-step chain.** Current tips of #126, #125, #127, #128, #58, #64, #69, #70, #72, #75, #78, #84, #86, #118, #120, #124, #119, #116 apply clean, in that order, onto `bf3ad1b`. Step-18 tree `96fe2f97ba60e11035a246d9a0f72528eb1b24bb` matches the 16:49 board. #127's tip moved from `83e0497` (now #131, 4 behind / 2 ahead) to `cc6e639` (0 behind / 2 ahead). #128's tip moved from `c9c90e4` (now #132) to `bc90171`. The diff between each pair of tips is `daily-tickets.md`, `scripts/cherish_auto.py`, and `scripts/run_store.py`. The catalog and prompt-loss files match, and the solo trees match, so the chain trees did not move. Merging #131 or #132 onto the chain after step 4 leaves tree `6145f1b8e7584c073a65c61837ccfc8d5462799e` unchanged. They are not extra land steps.

**#122 after #119.** Tip `6def68d7206af24342452617509e61814b958a2c` on `t30-77-on-119`. #119 `e557298` is an ancestor. The PR base `cursor/draft-local-image-gate-1102` is that same commit. GitHub reports MERGEABLE / CLEAN. `git merge-tree` onto #119 is clean and the tree equals #122's own tree `058cdd445e5d8a21c254a3f917f7023c9d77efa0`. `git merge-tree` against #118 is clean in both orders (tree `b0d545e7bbac23b9310b259464548d75bab4fbf5`). On the step-18 chain the merge is clean, tree `fb7af14d61644e3f23c66dcf96bfa679cd3884bc`, and `tests/test_ima2_retry.py` stays #118's blob `e01843a`. The previous tip `1fa33f6` still carries the 8-second ima2 blob `df73f88`. `6def68d` put that file back to main's blob.

**#77 is superseded by #122.** These three files are byte-identical between #77 `01a115e27094a9b1b55a19cd73a76921a560f5cc` and #122 `6def68d`, and they stay identical on the chain-plus-#122 tree:

| File | Blob |
| --- | --- |
| `docs/DUP_CLUSTER_GATE.md` | `e676b9ac7eabbe4d6775cd12415da50febdbfc1f` |
| `scripts/dup_cluster_gate.py` | `99fd10189c9a9b24dc027ec8a6fc7c099465a49e` |
| `tests/test_dup_cluster_gate.py` | `7710110d38f381a4cd3979a426c4db7c6f4b0247` |

`_dup_cluster_lines` in `scripts/validate_article.py` is the same 936 bytes on both tips. #77 is still clean alone against main (solo tree `535d36d8522754b1fad3295fccbd221c1d751d07`, and that merge keeps `import first_hand_experience`). On the chain, and against #122 directly, it conflicts in `scripts/validate_article.py`. Close #77 after Kevin accepts that recommendation. This pass did not close it.

**#97 replay.** `af350ba372ef840696eb82ac02d15cab2786512b` on `t69-97-on-122` is a merge of #97 `d088ccb3ed275fc0d61a0847a208bc2d6b32f286` onto #122 `6def68d`. Clean against #122 (tree `6645a037b8d81c0da990cfb3b2352261b95b88e8`) and clean on the chain after #122 (tree `0a2bbcd42e2810648d4ab79d98d3d2f9934538db`). #97's own tip is clean against main (solo tree `40d0a155f831`) and conflicts with the chain, and with the chain plus #122, on `scripts/validate_article.py`.

**#123.** Tip `0105335432d816237cbe8bf808e7dabccaba3dc7` on `t30-38-on-120`. #120 `2302f4b` is an ancestor. GitHub is MERGEABLE / CLEAN against that base. Solo tree vs main and vs #120 is `6c4afc97cd896ef1a36cea7f9d9a2036a52e2632`, the same tree the 16:49 board recorded. The #124 port-file conflict from that board is gone. The full-chain conflict is the two files in decision 3. `cloud/123-on-118` at `1f4a256` (2026-11-04) is an older merge and current #118 is not its ancestor. It is not `t70-123-on-chain`. That restack is on origin now; step 21.

**#121.** Left out of the order. Tip still `a694616c809266de494ee7ea34cc17543065d66a`. Solo vs main is clean (`5c2bfdc12923`). Not touched.

## Held out of this order

- **#77.** Close recommendation above. Clean vs main today, and the wrong patch once #119 is in the tree.
- **#97's original tip.** The 429 check that lands is `t69-97-on-122`.
- **#123.** Restack `t70-123-on-chain` `7c15da6` is on origin. The ima2 timeout is settled (keep #118's 1s wait). RunAtLoad follow-up is `t72-123-runatload` `01819f4`. Not merged by this pass. See step 21.
- **#131 and #132.** Same landed trees as #127 and #128. Merging them after step 4 changes nothing.
- **#121.** Wording hold. Not touched.
- **#129 and #130.** Board files. Not code lands. #130 is still `3e85c58774366f0876b386d531140aff17ec84e1`.

The 16:49 close list for #67, #68, #81, #85, #111, and #115 was not re-decided here. Those tips did not move, and their solo conflict paths against main are unchanged in the inventory.

## Inventory — all 47 open PRs

Read at 2026-11-10 16:48 ICT from `gh pr list --state open` and local `git merge-tree --write-tree origin/main <tip>`. Behind / ahead is versus `origin/main`. "Files vs base" is `git diff --name-only origin/<base>...<tip>`. Solo "clean" is the first 12 hex digits of the merge tree.

| PR | Draft | Base | Tip | Behind / ahead | GitHub vs base | Solo vs main | Files vs base |
| --- | --- | --- | --- | --- | --- | --- | --- |
| #1 | no | `main` | `e4982bd433d5` | 277 / 5 | CONFLICTING / DIRTY | conflict (3) | 14 |
| #9 | no | `main` | `ad0cebfaa96d` | 273 / 4 | CONFLICTING / DIRTY | conflict (15) | 20 |
| #10 | no | `main` | `d7fb719589ce` | 273 / 4 | CONFLICTING / DIRTY | conflict (16) | 20 |
| #38 | no | `main` | `4a475e62bbc4` | 195 / 1 | CONFLICTING / DIRTY | conflict (3) | 10 |
| #46 | yes | `main` | `5baccfd631af` | 94 / 2 | MERGEABLE / CLEAN | clean `8fcb9b9107b5` | 9 |
| #50 | yes | `main` | `f844148bd300` | 94 / 2 | MERGEABLE / CLEAN | clean `d45e6517ebba` | 6 |
| #58 | yes | `main` | `6813af4b97cf` | 161 / 1 | MERGEABLE / CLEAN | clean `d57e765da98b` | 4 |
| #64 | yes | `main` | `63482afa293b` | 94 / 2 | MERGEABLE / CLEAN | clean `80a900334e6b` | 7 |
| #65 | yes | `main` | `e2984fb96471` | 94 / 5 | CONFLICTING / DIRTY | conflict (1) | 7 |
| #67 | yes | `main` | `4dc638451315` | 94 / 2 | CONFLICTING / DIRTY | conflict (1) | 12 |
| #68 | yes | `main` | `b3b416a83d13` | 144 / 1 | CONFLICTING / DIRTY | conflict (1) | 16 |
| #69 | yes | `main` | `b8baa228b76a` | 94 / 3 | MERGEABLE / CLEAN | clean `9abc5a89a53d` | 3 |
| #70 | yes | `main` | `544b0abfffa2` | 94 / 2 | MERGEABLE / CLEAN | clean `132ddc3efa85` | 5 |
| #71 | yes | `main` | `bebea7a1b140` | 94 / 3 | CONFLICTING / DIRTY | conflict (1) | 7 |
| #72 | yes | `main` | `c2c03bd8a9dd` | 94 / 2 | MERGEABLE / CLEAN | clean `e3c4de073fe1` | 5 |
| #73 | yes | `cursor/entity-consistency-audit-1020` | `8be49f663461` | 94 / 8 | MERGEABLE / CLEAN | conflict (2) | 11 |
| #75 | yes | `main` | `396cd02faa2b` | 94 / 2 | MERGEABLE / CLEAN | clean `40e8e3e1a909` | 6 |
| #77 | yes | `main` | `01a115e27094` | 94 / 2 | MERGEABLE / CLEAN | clean `535d36d85227` | 5 |
| #78 | yes | `main` | `bfd51a045618` | 94 / 2 | MERGEABLE / CLEAN | clean `b722f6e4ecc4` | 5 |
| #81 | yes | `main` | `a2c8b056c207` | 94 / 2 | MERGEABLE / CLEAN | clean `0d10cba1e44e` | 11 |
| #83 | yes | `main` | `6301fa5e67b8` | 94 / 2 | MERGEABLE / CLEAN | clean `2eda9bead1da` | 8 |
| #84 | yes | `main` | `9f9d4de5d835` | 94 / 2 | MERGEABLE / CLEAN | clean `0e568c5a32f9` | 9 |
| #85 | yes | `main` | `88457b2351e8` | 94 / 5 | MERGEABLE / CLEAN | clean `d0207446fc3a` | 7 |
| #86 | yes | `main` | `22b66f930df3` | 94 / 2 | MERGEABLE / CLEAN | clean `ec83d6daa495` | 6 |
| #90 | yes | `main` | `c3de3b81ac31` | 94 / 5 | CONFLICTING / DIRTY | conflict (4) | 58 |
| #95 | yes | `main` | `31180f390b56` | 94 / 4 | CONFLICTING / DIRTY | conflict (1) | 6 |
| #96 | yes | `main` | `29c6c2556cbe` | 94 / 5 | CONFLICTING / DIRTY | conflict (2) | 105 |
| #97 | yes | `main` | `d088ccb3ed27` | 94 / 1 | MERGEABLE / CLEAN | clean `40d0a155f831` | 2 |
| #111 | yes | `main` | `7cc561173119` | 94 / 1 | CONFLICTING / DIRTY | conflict (1) | 5 |
| #115 | yes | `cursor/sync-main-test-isolation-1101` | `bdffeabb27c6` | 93 / 1 | MERGEABLE / CLEAN | clean `e0340da62586` | 5 |
| #116 | yes | `main` | `60aee102b54f` | 0 / 4 | MERGEABLE / CLEAN | clean `3f40c96c3c5f` | 13 |
| #117 | yes | `main` | `4d96c57cf9f5` | 83 / 3 | CONFLICTING / DIRTY | conflict (2) | 19 |
| #118 | yes | `main` | `b6256f249f30` | 0 / 1 | MERGEABLE / CLEAN | clean `2293bf53e20f` | 7 |
| #119 | yes | `main` | `e557298e96d8` | 0 / 4 | MERGEABLE / CLEAN | clean `883c4381c3e2` | 2 |
| #120 | yes | `main` | `2302f4b62f10` | 0 / 1 | MERGEABLE / CLEAN | clean `7112e0e27827` | 4 |
| #121 | yes | `main` | `a694616c8092` | 83 / 3 | MERGEABLE / CLEAN | clean `5c2bfdc12923` | 87 |
| #122 | yes | `cursor/draft-local-image-gate-1102` | `6def68d7206a` | 0 / 10 | MERGEABLE / CLEAN | clean `058cdd445e5d` | 5 |
| #123 | yes | `cursor/hermetic-writer-ps-1102` | `0105335432d8` | 0 / 4 | MERGEABLE / CLEAN | clean `6c4afc97cd89` | 11 |
| #124 | yes | `cursor/hermetic-writer-ps-1102` | `a068ae32350f` | 0 / 4 | MERGEABLE / CLEAN | clean `d4d3640f4a3d` | 7 |
| #125 | yes | `main` | `8875f68002b7` | 0 / 1 | MERGEABLE / CLEAN | clean `002a2c8fc643` | 11 |
| #126 | yes | `main` | `d2f07e8405b7` | 0 / 1 | MERGEABLE / CLEAN | clean `1ba991ce88d6` | 3 |
| #127 | yes | `main` | `cc6e639aabed` | 0 / 2 | MERGEABLE / CLEAN | clean `c859bb259c56` | 11 |
| #128 | yes | `main` | `bc901715c94f` | 0 / 2 | MERGEABLE / CLEAN | clean `4c528216bcc7` | 7 |
| #129 | yes | `main` | `af620b76f2c2` | 0 / 3 | MERGEABLE / CLEAN | clean `9409a0a6108c` | 2 |
| #130 | yes | `main` | `3e85c5877436` | 0 / 1 | MERGEABLE / CLEAN | clean `d6ae4873aac5` | 1 |
| #131 | yes | `main` | `83e0497afa92` | 4 / 2 | MERGEABLE / CLEAN | clean `c859bb259c56` | 11 |
| #132 | yes | `main` | `c9c90e4491bf` | 4 / 2 | MERGEABLE / CLEAN | clean `4c528216bcc7` | 7 |

#129's row is the parent of this commit. This commit adds `board/burn-land-order-2026-11-10.md` and the pointer on the 16:49 file. It is not a code land.

Conflict paths vs main, for the PRs whose solo merge-tree exits 1. #122 and #123 are clean in that column. Their chain results are above.

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
git merge-tree --write-tree --name-only origin/main cc6e639aabede85bde64dfbb4a3785354e5b2122
git merge-tree --write-tree --name-only e557298e96d8115dbd408aff21e12efa379b704a 6def68d7206af24342452617509e61814b958a2c
git merge-tree --write-tree --name-only 6def68d7206af24342452617509e61814b958a2c af350ba372ef840696eb82ac02d15cab2786512b
git ls-remote --heads origin t70-123-on-chain   # 7c15da6ed38139945662305470a41c20ba38b67f
git ls-remote --heads origin t72-123-runatload   # 01819f4f129ef17efbf0fa512d52eccdc56939ec
```

Exit 0 and one tree line means clean. The 18 tips in order: `d2f07e8` #126, `8875f68` #125, `cc6e639` #127, `bc90171` #128, `6813af4` #58, `63482af` #64, `b8baa22` #69, `544b0ab` #70, `c2c03bd` #72, `396cd02` #75, `bfd51a0` #78, `9f9d4de` #84, `22b66f9` #86, `b6256f2` #118, `2302f4b` #120, `a068ae3` #124, `e557298` #119, `60aee10` #116. Step 18 tree: `96fe2f97ba60e11035a246d9a0f72528eb1b24bb`. Then `6def68d` #122, tree `fb7af14d61644e3f23c66dcf96bfa679cd3884bc`. Then `af350ba`, tree `0a2bbcd42e2810648d4ab79d98d3d2f9934538db`.

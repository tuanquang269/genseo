# Draft PR readiness against main — 2026-10-28

Compared with `main` at `6c46771de6a11f5719422d94a337215015bec364` (Publish shilajit loading with food article). Nothing was merged, no draft was marked ready for review, no branch was deleted, and no history was force-pushed or rebased.

`cursor/fix-landing-queue-tests-1028` (#98) was not checked out, edited, or pushed.

## How tests were run

`bash tests/run_suite.sh` on current main: all 13 shell files pass. Unittest runs 315 tests and fails 2. Both failures are the landing-queue tests #98 is fixing:

- `test_landing_rotation.OpenQueueTests.test_rebalanced_open_tickets_include_both_priorities` (open queue is one Shockwave line; the test still expects at least 7)
- `test_queue_closures.FreshCheckoutTests.test_tracked_files_close_todays_tickets_without_a_ledger` (expects `pure-shilajit-gold-resin`; the open line is Shockwave)

**Baseline** below means those two failures and no others. `tests/test_landing_rotation.py` and `tests/test_queue_closures.py` were not edited on any branch this pass pushed. Where a conflicting PR had also changed them, the merge kept main's copies so #98 still owns the fix.

The full suite was run for main and for every combined tree that changes shell scripts, shell tests, deploy files, plists, `DAILY-RUN.md`, or `.cursor/` rules. Other combined trees got `unittest discover` only. Three parallel suite runs falsely failed `test_daily_lock.sh` and `test_sync_main.sh` (they share one git directory). Rerun one at a time, those files passed. Later suites were serial.

No open draft is superseded by main. Every one still has a non-empty diff. #89 is not on main; its only commit is already inside #91.

## Result

| PR | Title | Status | Test result |
| --- | --- | --- | --- |
| 98 | Point landing queue tests at the open Shockwave ticket | clean (not touched; other job) | not run |
| 97 | Treat a Shopify 429 on the draft dead-link check as unverified | clean | unittest: baseline |
| 96 | Align unpublished landing offers with live product JSON | refreshed+pushed `29c6c2556cbe9c82154fafa87a749edb6e1a1469` | full suite: baseline |
| 95 | Fix the long-standing known test failures | clean | full suite: pass (this PR rewrites the two landing-queue tests) |
| 94 | Accept Mike Moretti as the Wellness Nest blog byline | clean | full suite: baseline |
| 93 | GSC 10-24: FAQ drafts — probiotics + birth control/period, turkesterone WADA (no publish) | clean | full suite: baseline |
| 92 | GSC 10-24: refresh drafts for shilajit reviews + what-is-shilajit (no publish) | clean | unittest: baseline |
| 91 | Track untracked FloraFresh drafts at 15B CFU | clean | unittest: baseline |
| 90 | Combine #9 + #10 onto main + #88 (draft) | clean | full suite: baseline |
| 89 | FloraFresh drafts: 1B → 15B CFU (SNZ-1969) | clean | unittest: baseline. Not on main. The branch is an ancestor of #91, so merging #91 covers it. Left open. |
| 88 | FloraFresh 15B CFU and Mike Moretti blog byline | refreshed+pushed `b6227188efc2e74ea9b02ff23e429c752ade9fe2` | full suite: baseline |
| 87 | Draft: striking-distance answer-first FAQ refreshes (2026-10-21) | clean | unittest: baseline |
| 86 | Brand-SERP defence for the 2026-10-21 position slide | clean | unittest: baseline |
| 85 | Buyer prompt-loss list for AgeAura, ShilaSource, and FloraFresh | refreshed+pushed `88457b2351e8847f1245d7fd050879657b1fd5f1` | unittest: baseline after the rescore. Before that commit the merged tree also failed `test_real_list` and `test_committed_docs_match_render`. |
| 84 | Add a read-only mobile clutter audit for blog articles | clean | unittest: baseline |
| 83 | Weekly AI referrer report by domain, not UTM | clean | unittest: baseline |
| 82 | Add a rights-gated first-hand experience block for blog articles | clean | unittest: baseline |
| 81 | Record AI mentions and citations as separate fields | clean | full suite: baseline |
| 78 | Add a read-only quarterly news-blog content audit | clean | unittest: baseline |
| 77 | Warn-only publish gate for near-duplicate query clusters | clean | unittest: baseline |
| 75 | Draft: off-page listicle gap list for AgeAura and ShilaSource | clean | unittest: baseline |
| 73 | SEO fixes 2026-10-20: one Article JSON-LD per article; proposals for sameAs, product H1s, resin sitemap | refreshed+pushed `8be49f663461df365b86a9b584481db8d3bc9d54` | unittest: baseline. Base is #71, not main. GitHub reports it mergeable into that base. |
| 72 | AgeAura AI Mode follow-up gap map (draft) | clean | unittest: baseline |
| 71 | GEO: entity consistency audit + canonical name map (SEL 10-15) | refreshed+pushed `bebea7a1b1408eca21b7f28d61fa3063a730d0db` | unittest: baseline. Clean merge of main, pushed so #73 stays a small diff on top of this branch. |
| 70 | Read-only audit: PDF COAs versus crawlable HTML | clean | unittest: baseline |
| 69 | Add direct-to-deep-content sessions to the GEO traffic report | clean | unittest: baseline |
| 68 | Add an evidence-only first-hand experience block for articles | clean | full suite: baseline |
| 67 | Check canonical URLs before publish and record the 2026-10-19 crawl | clean | full suite: baseline |
| 65 | Score post-gate articles and prepare live GEO fixes | refreshed+pushed `e2984fb96471d24d07109af557a9c349e61a5890` | full suite: baseline |
| 64 | Opt-in login catch-up for morning slots missed while powered off | refreshed+pushed `63482afa293bf08f48a06c286b7678935f0f6ec8` | full suite: baseline |
| 58 | Add a disabled off-Mac heartbeat for the article lane | clean | unittest: baseline |
| 50 | Fix AgeAura NMN listicle claims, stars, and the offer the PDP opens on | clean | unittest: baseline |
| 46 | Fix the unpublished Turkesterone listicle draft (2026-10-16) | clean | unittest: baseline |

GitHub now reports every draft above as `MERGEABLE` / `CLEAN` against its current base. Open non-drafts #1, #9, #10, and #38 were out of scope.

## What the conflict merges kept

- **#96** `daily-tickets.md`: the published `#CA1017-32` line stays DONE with its live URL. FloraFresh landing copy on this branch stays 15B CFU. Landing-queue tests stay at main's bytes.
- **#88** `daily-landing-tickets.md`: the four 2026-10-17 lines keep main's FAILED / FAILED / FAILED / DRAFT outcomes. The FloraFresh questions line keeps this PR's 15B CFU wording. `scripts/florafresh_rules.py` is `CFU = "15B CFU"`. `roster.json` names Mike Moretti.
- **#65 and #64**: the only conflicts were in `tests/test_queue_closures.py`. Both files that #98 edits were restored to main. The GEO audit and the opt-in catch-up are otherwise intact.
- **#73** (stacked on #71): publisher and `repair_schema.py` still do not append a second Article JSON-LD block. Main's unreachable `if False` Article injection was not put back. The entity map still says FloraFresh is 15B CFU of SNZ-1969, and the expected blog author is still Mike Moretti. This branch does not change `florafresh_rules.py`; that guard is #88.
- **#71**: merge of main was itself clean. It was pushed because #73's base is this branch. Without it, merging main only into #73 would have dumped main into the #73 review diff.
- **#85**: merged main, then recorded the two newer DONE shilajit URLs (`shilajit-for-hair-with-food-us-evidence`, `shilajit-loading-with-food-us-trial-evidence`) in the prompt-loss report and in `QUEUE_LIVE`. Neither URL became the matching article for one of the 30 prompts.

## Merge order

Each row is mergeable into current main (or, for #73, into current #71). Several of them edit the same byline and FloraFresh files, so landing one will make the next ones conflict until they are refreshed again. Order below is the sequence that keeps that refresh small. Do not merge any of them until that is what you want; this pass did not merge them.

1. **#98** first. It is the designated fix for the two red landing-queue tests. Every other draft except #95 still fails those two, on purpose.
2. **#88** next. It is the FloraFresh 15B CFU guard and the Mike Moretti roster entry. #94, #93, #92, and #96 all conflict with this updated branch (roster, `validate_article.py`, `run_ticket_headless.sh`, or the FloraFresh guard tests).
3. **#94**, then **#93** and **#92**. They accept Mike Moretti and carry unpublished drafts. Refresh each onto #88 and keep 15B CFU plus the Mike Moretti byline.
4. **#91**. Draft tracking at 15B CFU. It merges cleanly onto updated #88. **#89** becomes redundant once #91 is merged; leave #89 open until then. It is not already on main.
5. **#96**. Landing offer prices. After #88, expect conflicts in `docs/FLORAFRESH_FORMULA_GUARD.md`, `scripts/run_ticket_headless.sh`, and `tests/test_florafresh_guard.py`. Keep 15B CFU.
6. **#90**. This branch already contains #88's original commit plus the FusiForce and shilajit-gummies label guards (the substance of non-drafts #9 and #10). Against updated #88 the only conflict found was `daily-landing-tickets.md`. Land it after #88, then decide whether #9 and #10 are still needed. They were not closed here.
7. **#65**. GEO audit. It already treats 15B CFU as the label count and Mike Moretti as the byline, and it merges cleanly onto updated #88.
8. **#87**. Striking-distance FAQ drafts. No code overlap with the guard. Merge any time after the byline guard so new articles keep Mike Moretti.
9. **#71, then #73**. #73's base is `cursor/entity-consistency-audit-1020`. Merging #73 to main before #71 would skip the stack. #71 is mergeable to main now; #73 is mergeable into #71 and its diff against that base is the JSON-LD dedupe, not the rest of main.
10. **#82 before #68**. Both add a first-hand experience block and conflict in `scripts/validate_article.py`. #82 is the later rights-gated blog block and is already based on current main. #68 is the earlier evidence-only block and also conflicts with #67 in `scripts/shopify_publisher.py`. Prefer #82. Refresh #68 only if you still want that older block.
11. **#67**, then the independent audits and gates, in any order: **#97, #77, #81, #78, #84, #83, #86, #85, #75, #72, #70, #69, #58, #64, #50, #46**. #67 conflicts with #82 only in `skills/genseo-auto-publish/SKILL.md`. #97 is clean against both #82 and #77. #77 is clean against #67.
12. **#95 last, and only after #98**. Its suite is green because it rewrites the same two landing-queue tests #98 rewrites, with a different expectation (a frozen rebalance record, not the current Shockwave open line). This pass left that rewrite in place. After #98 merges, refresh #95 and keep #98's landing-queue assertions plus #95's self-apply and sync-main test fixes.

## Product facts used while resolving conflicts

FloraFresh count kept or written in this pass is 15B CFU of Bacillus coagulans SNZ-1969 per 2 gummies. The blog byline kept for Wellness Nest articles is Mike Moretti. No live page, paid-traffic page, theme file, or store setting was edited. Nothing was published and no email was sent.

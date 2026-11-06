# OWNER stale-PR triage — 2026-11-06

43 open pull requests. Nothing in this note was closed or merged. GitHub mergeability is against each PR's base as of this read (main at `bf3ad1b`). Suites on those other branches were not re-run here.

Four PRs are **not drafts** and also conflict with main. Do not resolve-and-merge them from the button: [#1](https://github.com/tuanquang269/genseo/pull/1), [#9](https://github.com/tuanquang269/genseo/pull/9), [#10](https://github.com/tuanquang269/genseo/pull/10), [#38](https://github.com/tuanquang269/genseo/pull/38).

FloraFresh label source of truth stays Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies. AgeAura stays NMN + TMG only. A branch that puts 15B CFU or a Mike Moretti blog byline back into docs or the publisher is not land-ready.

## Kevin decision

These still need a call before anyone merges them.

| PR | Why it is still yours |
|---|---|
| [#1](https://github.com/tuanquang269/genseo/pull/1) | IndexNow pings and `llms.txt` drafts. Conflicts. The PR itself lists open calls (live `/llms.txt`, MenoMate rows, Urolithin PDP). Not a draft. |
| [#38](https://github.com/tuanquang269/genseo/pull/38) | Mac Mini failover. Conflicts. Text says do not merge until a dry-run on `Kevins-Mac-mini-2`. Not a draft. The conflict-free replay is [#123](https://github.com/tuanquang269/genseo/pull/123), stacked on [#120](https://github.com/tuanquang269/genseo/pull/120). Same dry-run question. |
| [#46](https://github.com/tuanquang269/genseo/pull/46) | Unpublished Turkesterone listicle. Trustpilot lines and missing scene files are left for you. |
| [#50](https://github.com/tuanquang269/genseo/pull/50) | Unpublished AgeAura NMN listicle (claims, stars, offer). Label gate still wants macOS Vision; images are gitignored. |
| [#58](https://github.com/tuanquang269/genseo/pull/58) | Off-Mac heartbeat. Explicit do-not-merge: a later arm could publish. |
| [#64](https://github.com/tuanquang269/genseo/pull/64) | Login catch-up LaunchAgent. Code is written. Install, the 14:47 quiet period, and the 15-minute gap are still open. |
| [#65](https://github.com/tuanquang269/genseo/pull/65) | Live GEO fixes. Explicit do-not-merge until you decide to update posts that are already live. Conflicts. |
| [#68](https://github.com/tuanquang269/genseo/pull/68) | First-hand experience block. Conflicts. Example quotes never render; shipping the hook is a product call. |
| [#71](https://github.com/tuanquang269/genseo/pull/71) | Entity name map. Conflicts. Warns inside `validate_article.py`. GO list is theme sameAs, GemPages H1s, PDP copy. [#73](https://github.com/tuanquang269/genseo/pull/73) is stacked on this branch and is not mergeable to main on its own. |
| [#83](https://github.com/tuanquang269/genseo/pull/83) | Weekly AI referrer report. Explicit do-not-merge. |
| [#86](https://github.com/tuanquang269/genseo/pull/86) | Brand-SERP note. Explicit do-not-merge until a GO covers any blog body edit or hreflang/title change. |
| [#96](https://github.com/tuanquang269/genseo/pull/96) | Landing offer sweep from product JSON fetched 2026-10-26. Conflicts. Prices need a fresh check before land. |
| [#116](https://github.com/tuanquang269/genseo/pull/116) | Canonical URL gate re-applied onto main (successor of [#67](https://github.com/tuanquang269/genseo/pull/67)). Clean, but `shopify_publisher.py` exits 2 before image upload. That is a live-publish behavior change. |
| [#117](https://github.com/tuanquang269/genseo/pull/117) | FusiForce and shilajit-gummies guards, meant to replace [#90](https://github.com/tuanquang269/genseo/pull/90). Conflicts, and the branch still teaches FloraFresh 15B CFU and a Mike Moretti blog byline. Do not land as-is. |
| [#121](https://github.com/tuanquang269/genseo/pull/121) | Local image paths for 19 drafts. Hold in the PR: 13 heroes, and `/pages/mike-moretti` live. Alt text in the diff still says 15 billion CFU. |
| [#125](https://github.com/tuanquang269/genseo/pull/125) | Doc lock to SNZ-1969 at 1 billion CFU. Matches the label source of truth. The PR says do not merge in that batch, so it stays with you. |
| [#122](https://github.com/tuanquang269/genseo/pull/122) | Stacked replay of the [#77](https://github.com/tuanquang269/genseo/pull/77) dup-cluster gate onto [#119](https://github.com/tuanquang269/genseo/pull/119). Pick one path. Do not land both [#77](https://github.com/tuanquang269/genseo/pull/77) and [#122](https://github.com/tuanquang269/genseo/pull/122). |
| [#123](https://github.com/tuanquang269/genseo/pull/123) | Stacked replay of [#38](https://github.com/tuanquang269/genseo/pull/38) onto [#120](https://github.com/tuanquang269/genseo/pull/120). Same Mini dry-run hold as [#38](https://github.com/tuanquang269/genseo/pull/38). |

## Auto-close when the successor lands

Do not merge the old head. Close it only after the successor is the one you keep. This note does not close any of them.

| Close | After | Why the old head should not land |
|---|---|---|
| [#67](https://github.com/tuanquang269/genseo/pull/67) | [#116](https://github.com/tuanquang269/genseo/pull/116) | [#116](https://github.com/tuanquang269/genseo/pull/116) is the same canonical gate, rebased. [#67](https://github.com/tuanquang269/genseo/pull/67) conflicts. Whether to land the gate at all is in the table above. |
| [#81](https://github.com/tuanquang269/genseo/pull/81) | [#127](https://github.com/tuanquang269/genseo/pull/127) | [#127](https://github.com/tuanquang269/genseo/pull/127) says to merge `cloud/81-refresh-1105b` and not the [#81](https://github.com/tuanquang269/genseo/pull/81) head. The old head fails current FloraFresh topic-bank checks. |
| [#85](https://github.com/tuanquang269/genseo/pull/85) | [#128](https://github.com/tuanquang269/genseo/pull/128) | [#128](https://github.com/tuanquang269/genseo/pull/128) says to merge `cloud/85-refresh-1105b` and not the [#85](https://github.com/tuanquang269/genseo/pull/85) head. The old head does not count the current DONE set. |
| [#9](https://github.com/tuanquang269/genseo/pull/9), [#10](https://github.com/tuanquang269/genseo/pull/10), [#90](https://github.com/tuanquang269/genseo/pull/90) | a guard PR that keeps 1 billion CFU and Dr. Marcus Hale | [#90](https://github.com/tuanquang269/genseo/pull/90) bundles the closed 15B / Mike Moretti direction with the guards. [#117](https://github.com/tuanquang269/genseo/pull/117) is the intended guard successor and is **not** clean yet (see above). All three conflict. [#9](https://github.com/tuanquang269/genseo/pull/9) and [#10](https://github.com/tuanquang269/genseo/pull/10) are not drafts. |
| [#111](https://github.com/tuanquang269/genseo/pull/111) | [#118](https://github.com/tuanquang269/genseo/pull/118) | Older landing-queue fixture (gold-resin open head). [#118](https://github.com/tuanquang269/genseo/pull/118) freezes the later Shockwave snapshot. [#111](https://github.com/tuanquang269/genseo/pull/111) conflicts. |
| [#95](https://github.com/tuanquang269/genseo/pull/95) | [#118](https://github.com/tuanquang269/genseo/pull/118) and [#120](https://github.com/tuanquang269/genseo/pull/120) | Older flake fix (queue assertions plus an empty `ps` in test mode). Conflicts. Later hermetic PRs cover the same failures on current main. |
| [#115](https://github.com/tuanquang269/genseo/pull/115) | [#124](https://github.com/tuanquang269/genseo/pull/124) | Stacked on [#114](https://github.com/tuanquang269/genseo/pull/114), which already merged. [#124](https://github.com/tuanquang269/genseo/pull/124) is the port onto [#120](https://github.com/tuanquang269/genseo/pull/120). |

## Land-ready

Clean against main, base is main, and the PR text does not hold the merge for a product or brand call. Follow-up store edits, emails, and theme changes are still a separate GO. This burn did not re-run their suites. Drafts stay drafts until you merge them.

| PR | What landing it does |
|---|---|
| [#69](https://github.com/tuanquang269/genseo/pull/69) | Read-only GEO direct-to-deep-content report. |
| [#70](https://github.com/tuanquang269/genseo/pull/70) | Read-only COA PDF vs HTML audit. No store change in the PR. |
| [#72](https://github.com/tuanquang269/genseo/pull/72) | AgeAura AI Mode gap map. No publish. Live H2 edits stay a later GO. |
| [#75](https://github.com/tuanquang269/genseo/pull/75) | Off-page listicle gap list. No email sent. Outreach stays a later GO. |
| [#77](https://github.com/tuanquang269/genseo/pull/77) | Warn-only near-duplicate cluster gate. Stays a warning unless `GENSEO_DUP_CLUSTER_BLOCK=1`. See [#122](https://github.com/tuanquang269/genseo/pull/122) before landing both. |
| [#78](https://github.com/tuanquang269/genseo/pull/78) | Read-only quarterly content audit. Redirects are not in the PR. |
| [#84](https://github.com/tuanquang269/genseo/pull/84) | Read-only mobile clutter audit. Theme findings stay a later GO. |
| [#97](https://github.com/tuanquang269/genseo/pull/97) | Draft dead-link check treats Shopify 429 as unverified (exit 3), not as a live URL. |
| [#118](https://github.com/tuanquang269/genseo/pull/118) | Queue and ima2 tests use frozen fixtures, not the live queue. Rebased onto `bf3ad1b` in this burn (`b6256f2`). `FreshCheckoutTests` passed. Keep it draft until you want it. Does not touch [#126](https://github.com/tuanquang269/genseo/pull/126)'s profile paths. |
| [#119](https://github.com/tuanquang269/genseo/pull/119) | Draft markdown fails when an image `src` is a remote URL. |
| [#120](https://github.com/tuanquang269/genseo/pull/120) | Reconcile and self-apply tests stop reading other live writers. Production scan stays fail-closed. |
| [#124](https://github.com/tuanquang269/genseo/pull/124) | Port of [#115](https://github.com/tuanquang269/genseo/pull/115) onto [#120](https://github.com/tuanquang269/genseo/pull/120). Land only after [#120](https://github.com/tuanquang269/genseo/pull/120). Not a second copy of [#115](https://github.com/tuanquang269/genseo/pull/115) onto main. |
| [#126](https://github.com/tuanquang269/genseo/pull/126) | Wellness Nest profile paths resolve inside the checkout. Left `FreshCheckoutTests` for [#118](https://github.com/tuanquang269/genseo/pull/118). No file overlap with [#118](https://github.com/tuanquang269/genseo/pull/118). |
| [#127](https://github.com/tuanquang269/genseo/pull/127) | Successor head for [#81](https://github.com/tuanquang269/genseo/pull/81). FloraFresh stays SNZ-1969 at 1 billion CFU. AgeAura stays NMN + TMG. |
| [#128](https://github.com/tuanquang269/genseo/pull/128) | Successor head for [#85](https://github.com/tuanquang269/genseo/pull/85). Same label and AgeAura locks. |

## Not in the tables above

Every open number is in one table: 1, 9, 10, 38, 46, 50, 58, 64, 65, 67, 68, 69, 70, 71, 72, 73 (under [#71](https://github.com/tuanquang269/genseo/pull/71)), 75, 77, 78, 81, 83, 84, 85, 86, 90, 95, 96, 97, 111, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128.

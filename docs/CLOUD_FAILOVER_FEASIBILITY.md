# Off-Mac article failover — feasibility

**Verdict: partial.** A Linux runner can decide whether the MacBook already published today's articles. It cannot write and publish those articles with the pipeline as it stands.

The MacBook stays primary (`GENSEO_HOST_ROLE=primary`, ticket prefix `MB`, slots 07:30 / 08:05 / 14:47 ICT). This change does not load the Mac Mini, does not edit the launchd plists, and does not call the article publisher. PRs #52–#57 (caffeinate, feed retry, self-apply, queue low-water) stay the Mac's own recovery. They do not help when the Mac is asleep or offline for the whole day, which is the gap this note is about.

What landed here:

- `scripts/genseo_cloud_failover.py` — the decision. Off unless `GENSEO_CLOUD_FAILOVER` is exactly `1`. It never publishes.
- `.github/workflows/genseo-cloud-failover.yml` — `workflow_dispatch` plus two UTC crons. The job is skipped unless the repository **variable** `GENSEO_CLOUD_FAILOVER` is `1`. Unset means off. The workflow file names no secret.
- `tests/test_cloud_failover.py` — the decision table. No live feed, no Shopify, no model call.

A merge registers the cron on `main`. GitHub still skips the job until Kevin creates that variable and sets it to `1`. Creating the variable is a settings change, not a code change, and it still does not publish: a run that finds a gap exits fail-closed (`publish-blocked`) because the publish arm is not in this scaffold.

## What a run decides

The public atom feed is the cross-host lock, the same one the two Macs already use (`scripts/genseo_published_today.py`, `https://wellnessnest.co/blogs/news.atom`, ICT date). The committed record is `[DONE YYYY-MM-DD` in `daily-tickets.md`. `PUBLISHED_ARTICLES_TRACKER.csv` and `state/published-by-<host>.log` are gitignored, so a fresh runner does not have them.

Order, once the flag is on:

1. Unreadable feed → fail closed. A missing feed is not treated as zero.
2. Before 18:30 ICT → stand down. The Mac slots still own the day. A delayed cron that lands the next morning also stands down, because the check is the clock, not the cron minute.
3. Live count ≥ `GENSEO_DAILY_TARGET` (default 5) → stand down, even if the repo has no DONE line for today (the Mac may not have pushed).
4. A post in the last 50 minutes that is not in this runner's local log → stand down. The runner's log starts empty, so any recent post counts as the other host.
5. `state/daily.lock` held on **this** machine → stand down. A GitHub runner cannot see the Mac's lock. The feed and the peer window are the shared lock.
6. Repo DONE lines for today ≥ target → stand down, even if the feed is behind.
7. No open ticket (`^(- \[ \]|## \[ \])`, same pattern as `deploy/grokbot-genseo-daily.sh`) → stand down. This script does not refill and does not call an ads or LLM miner.
8. Open-ticket lint failure (`scripts/lint_tickets.py`, the label guards) → fail closed.
9. Otherwise the day is short. Exit fail-closed with `publish-arm-disabled` plus every missing dependency name. `publish` is false.

The 22:00 ICT cron is a second look. The Mac wrapper waits out a peer (up to six windows) and then takes over. One cloud observation at 18:30 would drop a day where a single post went live at 18:10 and the Mac then died. The later run looks again. It still does not publish.

A red Actions run means the gate refused. It does not mean an article was published or that a publish failed.

## Inventory

"Replace" means a Linux runner can do the same job without a new vendor and without weakening a gate. Cost is what that replacement would spend. This scaffold spends none of it: the armed job does one or two public GETs of the atom feed, a local lint, and local imports. It does not call Shopify Admin, `ai.patigroup.com`, ima2, or gem9.

| Dependency | Where it lives | On the article path | Linux replacement | Cost if a later arm used it |
|---|---|---|---|---|
| Public atom feed | `scripts/genseo_published_today.py` | Yes. Shared lock. | Already portable. `urllib`, no credential. | None. Public GET. |
| Peer window, 50 min | same script, `--peer-active`, `state/published-by-<host>.log` | Yes. | Portable. Empty log = every recent post is foreign, so the runner stands down. | None. |
| Ticket queue | `daily-tickets.md` in git | Yes. | Portable for what has been pushed. Unpushed Mac edits are invisible. The feed still blocks a second copy of a URL that is already live. | None. |
| Open-ticket lint / label guards | `scripts/lint_tickets.py`, `brand_rules.py`, `florafresh_rules.py`, `shockwave_rules.py`, `gold_resin_rules.py`, `shilasource_resin_rules.py`, `turkesterone_rules.py`, `ageaura_rules.py` | Yes, before a ticket runs. | Portable. They read committed `product_refs/*.label.json`. They do not OCR. | None. |
| `geo_citability` | `scripts/geo_citability.py`, called by `validate_article.py` | Yes, on a draft. | Portable Python. Live URL checks use `curl` against public pages. This scaffold loads the module and does not score a draft, because it writes none. | None until a draft exists. Then public HTTP only. |
| QRG / `claude-seo` | `~/.claude/plugins/marketplaces/*claude-seo*/bin/claude-seo`, data under `~/Library/Application Support/claude-seo`, Python from `~/.local/share/uv/python/` | Yes. Missing launcher is a **warning**, not a hard fail (`validate_article.qrg_scores`). Measured scores still hard-fail. | Same behavior on Linux: report the skip, do not invent a score, do not call a paid API to replace it. Installing the plugin on a runner would be a later choice. | None today. Not an Anthropic API call. |
| Roster loader | `scripts/genseo_roster.py` reads only `/Users/kevinkreative/genseo/roster.json` | Yes. Empty roster fails `validate_article.py`. | **Not replaced.** The file is in the repo, but the loader ignores the checkout. Operating rule: that Mac path is expected, not a bug to patch. A symlink on the runner would satisfy it without a code change. This scaffold reports `roster-empty` and does not create the symlink. | None. No secret. |
| `topic_fitness.py` catalog | `ROOT = "/Users/kevinkreative/genseo"`, cache `existing_articles.json` (gitignored) | STEP 0.5. A missing file becomes `[]`, so near-duplicate checks do not see the live catalog. | **Not replaced.** Refreshing the cache is `refresh_article_cache.py`, which reads the Admin token. STEP 0 `suggest.json` is a public storefront read and is portable, and this scaffold does not run it. | Admin API only if someone refreshes the cache. Do not. |
| Shopify Admin token | `~/.genseo/shopify_token.json`, or the path in `GENSEO_CONFIG`. JSON keys `shop` and `access_token`. `scripts/genseo_config.py` exits at import if the file is missing or still a placeholder. | Yes, to publish. | **Not wired.** A runner can hold the same file. This workflow does not. The scaffold never imports `genseo_config` (that import would sys.exit, or would load the token into the process). | The store's own Admin API. Not a new vendor. This PR does not call it. |
| Shopify CLI app env | `SHOPIFY_CLI_APP_SHOP`, `SHOPIFY_CLI_APP_CLIENT_ID`, `SHOPIFY_CLI_APP_CLIENT_SECRET` in `~/genseo/.env`, read by `scripts/shopify_app_token.py` | Not the daily file-token path. Used by the client-credentials helper. | Same three names, if that helper is used later. The daily publisher path uses the token file above. | Admin API, only if that helper runs. It does not run here. |
| `SHOPIFY_API_VERSION` | env, default `2026-04` | Publisher only. | Optional. Has a default. | None. |
| Writer, native Claude | `~/.local/bin/claude`, login in `~/.claude-genseo`. macOS Keychain, per config dir. `ANTHROPIC_API_KEY` is unset on purpose so the CLI stays off on-demand billing. | Yes, only when the writer and the fallback are not `PATI-*`. The current writer is `PATI-*`, so this lane is not the one the daily job uses. | **Not portable.** Keychain does not exist on Linux. Do not add `ANTHROPIC_API_KEY`. If that variable is set, the probe records `ANTHROPIC_API_KEY-must-stay-unset` and a would-fill run fail-closes. The value is not printed. | On-demand Anthropic billing if it were set. This PR does not call Anthropic. |
| Writer, local 9router | `127.0.0.1:20128`, used only when `/v1/models` lists the writer alias | Yes, on the Mac that is running the router. | **Not on a GitHub runner.** Nothing in this repo starts that process. | Subscription router, local. Not called here. |
| Writer, hosted 9router | `NINE_ROUTER_KEY` from the environment or `~/PATI/LLM-Wiki/.env` (Syncthing vault, MacBook → Mini, not in git). Base `GENSEO_ROUTER_BASE`, default `https://ai.patigroup.com`. The lane copies the key into `ANTHROPIC_AUTH_TOKEN` and unsets `ANTHROPIC_API_KEY`. | Yes. This is the lane the Mac uses when local 9router has no PATI alias. | A Linux runner can run the `claude` CLI and send the same key. **This scaffold does not.** The probe only checks that the variable is non-empty. | **Paid / subscription.** Tokens go to the existing PATI router. Not a new vendor, and not Anthropic on-demand, but it is a paid call. Do not arm a writer until that spend is accepted. |
| Model map | `scripts/genseo_model_map.json` | Yes. | Portable file. Useless without a lane above. | None by itself. |
| `ima2` images | `scripts/article_images.py` exits at import if `ima2` or `cwebp` is missing. Default `GENSEO_IMA2_PROVIDER=oauth`, `GENSEO_IMA2_MODEL=gpt-6-sol`. Binary under `~/.npm-global`, nvm, or `~/.local/bin`. ChatGPT OAuth session is on the Mac. There is no env var in this repo for that session. | Yes. Hero + 3 inline images are required. `validate_article.py` requires ≥3 inline images. | **Blocking. No in-repo replacement.** `cwebp` itself is `apt install webp`. The OAuth session is not. `GENSEO_IMAGE_BACKEND=gpt` is described for the Mini in `DAILY-RUN.md` and is not what `article_images.py` runs. A paid image API (KIE, Veo, Kling, and the rest named in the runner prompt) is forbidden. | $0 ChatGPT subscription on the Mac. Not available to this runner. This PR does not generate images. |
| `gem9` image QC | Hardcoded `/Users/kevinkreative/.local/bin/gem9`. `--qc` calls it. A missing binary fails the image step. Comments describe it as a 9router subscription judge. | Yes, whenever `--qc` is passed. The article prompt requires `--qc`. | **Blocking.** No binary in the repo. Pointing it at a paid vision API would be a new call this pipeline does not allow. | Router subscription if the binary ran. Not called here. |
| Pillow, markdown | pip, for the publisher and draft rendering | Yes, at publish time. | `pip install`. Not sufficient. | None. |
| Node | nvm, because `ima2` is a Node script | Yes, as part of ima2. | Node installs. The OAuth session does not come with it. | None. |
| macOS Vision OCR | `swift` + `scripts/tools/label_ocr.swift` (`VNRecognizeTextRequest`), `scripts/landing_label_gate.py` | **No.** Article checks use the committed label JSON. Vision is the landing pack-shot gate. A non-darwin host fail-closes that gate, which is correct. | Cannot replace Vision. Do not teach the article lane to call it. | None for articles. |
| `sips` | `scripts/run_landing_daily.sh` JPEG conversion | **No.** Landing screenshots. | Not needed for articles. | None. |
| `caffeinate`, `pmset`, launchd | `scripts/genseo_power_assert.sh`, `deploy/com.pati.genseo-daily.macbook.plist`, `~/bin/grokbot-genseo-daily.sh`, `~/Library/LaunchAgents/com.pati.genseo-daily.plist` | Scheduling and sleep only. | Not needed. A hosted runner does not sleep. The cron above is the replacement for the clock. | GitHub Actions minutes, and only when the variable is `1`. A skipped job does not run the steps. |
| Lane lock | `state/daily.lock` (gitignored directory + pid) | Yes, on one machine. | The decision table is ported (live wrapper held, dead pid stale, missing pid held for 6h). The directory is not shared with the Mac. | None. |
| Cursor agent worker | `com.pati.cursor-agent-worker`, `agent worker start` | Not the article writer. The writer is Claude Code. | A Cursor cloud VM can run this same script. It does not remove the ima2, gem9, Keychain, or token blockers. This repo's cloud-agent boundary still forbids the publisher, image generation, and `persona_picker.py`. | Cursor plan time. No Shopify call. |
| Persona bank | `scripts/persona_picker.py`, `personas/index.json` | Skipped on the MacBook. The plist sets `GENSEO_NO_FACE=1`. | Stay no-face. The workflow sets `GENSEO_NO_FACE=1`. This script does not import or run the picker. | None. |
| Claims log | `logs/claims/<slug>.md`, sources fetched in the writer session (Europe PMC / DOI / PubMed) | Yes, before publish. | Those are public pages, fetched by the writer. This script writes no claims. | None here. A later writer would do public HTTP, plus the router spend above. |
| Git push of the ticket flip | Mac `git push` after publish | Yes, best-effort. | This workflow is `contents: read`. It does not push. | None. |
| Lark notify | `~/.genseo/lark_app.json` (`base`, `app_id`, `app_secret`, `receive_id`, `receive_id_type`) | Not in the daily article wrapper. | Not required. | None. |

## Secrets

This scaffold needs **no new secret**. The workflow does not reference `secrets.*`. The script prints booleans and gap names. It does not print env values, and it does not open the Shopify token file (it only asks whether the path exists).

Kevin would add the following only in a later change that actually grows a publish arm. Names only:

| Name | Required for a later publish arm? | Notes |
|---|---|---|
| `NINE_ROUTER_KEY` | Yes, for the hosted writer | Existing PATI router. A paid/subscription call to `https://ai.patigroup.com`. Not read by an armed heartbeat beyond a presence check, and the shipped workflow does not pass it in. |
| `GENSEO_CONFIG` | Path only | Points at the JSON file. It is not the token. |
| JSON keys `shop`, `access_token` | Yes, inside that file | This is what `scripts/genseo_config.py` loads. There is no `SHOPIFY_ACCESS_TOKEN` env var on the daily path. A later workflow would have to materialize the file from a GitHub secret Kevin chooses. This PR does not name or create that secret. |
| `SHOPIFY_CLI_APP_SHOP`, `SHOPIFY_CLI_APP_CLIENT_ID`, `SHOPIFY_CLI_APP_CLIENT_SECRET` | No for the daily file-token path | Only `scripts/shopify_app_token.py`. |
| `SHOPIFY_API_VERSION` | No | Defaults to `2026-04`. |
| `GENSEO_ROUTER_BASE` | No | Defaults to `https://ai.patigroup.com`. |
| `ANTHROPIC_API_KEY` | **Do not add** | The article lane unsets it so Claude Code cannot bill on demand. A present value is a fail-closed gap on a would-fill run. |
| ima2 / ChatGPT OAuth | No name exists | The session is local to the Mac. Inventing a secret for it is not a replacement. |
| `GENSEO_CLOUD_FAILOVER` | Arms the heartbeat only | Repository **variable**, not a secret. Exact value `1`. |

`GENSEO_IMA2_PROVIDER` and `GENSEO_IMA2_MODEL` are selectors, not secrets.

## What is still blocking a real failover

1. **Images.** `ima2` OAuth plus the `gem9` binary. Articles cannot pass the image rules without them, and the house rule forbids a paid image API instead.
2. **Writer auth.** Native login is Keychain. Local 9router is a Mac process. Hosted 9router needs `NINE_ROUTER_KEY` and would spend the PATI subscription. Not wired.
3. **Shopify token file.** Not on the runner. The publisher is not invoked. Importing `genseo_config` on a runner without the file exits.
4. **Roster path and topic-fitness catalog path.** Absolute Mac paths. Empty roster fails the article gate. Empty catalog blinds STEP 0.5. Not patched.
5. **No shared lock directory.** A future arm that published in the same minute the Mac woke, before either post was in the feed, could double-publish. The Mac re-checks the feed immediately before publish. A cloud arm would have to do that too, and would still lose a same-minute race. This scaffold does not publish, so it does not open that race.
6. **QRG plugin** is optional on the Mac (skip = warning). A Linux publish would have the same hole unless the plugin is installed. This scaffold does not publish unscored drafts; it publishes nothing.

Until those are solved in a review Kevin accepts, the flag should stay unset.

## Actions minutes and rate limits

A read-only run of the gate at 09:01 ICT on 2026-10-18 (`GENSEO_CLOUD_FAILOVER=1`, no token, no router key) got `live_count: 0` from the public feed and stood down: `before-cutoff`, `publish: false`. That matches the storefront still showing no article for this ICT day. The same run reported the Linux gaps by name (`NINE_ROUTER_KEY`, `shopify-token-file`, `claude-cli`, `ima2`, `cwebp`, `gem9`, `roster-empty`) and the existing QRG skip warning. It did not publish.

Checked while writing this, read-only, against `tuanquang269/genseo`:

- The repo is **private**.
- GitHub REST rate limit at that moment: core 5848 of 5850 remaining, search 30 of 30, GraphQL 5850 of 5850. No throttle, no secondary-rate warning.
- A skipped job (variable unset) does not run steps, so it does not spend Actions minutes. After merge, GitHub will still record a workflow run at each cron. That is a log line, not a runner.
- An armed run is one short `ubuntu-latest` job (10 minute cap) doing public feed reads and local Python. It is not a 90-minute writer loop. Five tickets at 90 minutes each would not fit a single hosted job and would burn private-repo minutes. That loop is not in this workflow.
- No on-demand model API is called. No Shopify Admin call. No image generation.

The storefront atom feed is unauthenticated. Arming the variable adds at most four GETs a day (count + peer, twice). That is the same feed the Mac already polls.

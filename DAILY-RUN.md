# DAILY-RUN.md — the GenSeo daily job

**Owner: Hermes agent `eugene-schwartz`, cron job "GenSeo Daily" `454070ba1442`, 07:30 ICT (+07).**
This file is the runbook the unattended run reads. `AGENTS.md` (6 hard rules) and the
`genseo-auto-publish` skill (10-step pipeline) stay the authority on *how* to make an article.
This file only says **what to do each day, in what order, and when to stop**.

Written 2026-08-13. Rebuild when the state block at the bottom stops matching reality.

---

## 0 · Two-Mac failover (Kevin 2026-10-06 — no automation may depend on one Mac)

GenSeo runs from **whichever Mac is online**. Both Macs carry the same pipeline and the same
schedule; the live site decides who publishes.

| | Mac Mini (primary) | MacBook Pro (standby) |
|---|---|---|
| launchd | Mini's existing 07:30 batch + 14:47 catch-up | `com.pati.genseo-daily` 07:30 + 14:47 (`~/Library/LaunchAgents/com.pati.genseo-daily.plist`) |
| wrapper | `~/bin/grokbot-genseo-daily.sh` | `~/bin/grokbot-genseo-daily.sh` (role `standby`, waits 20 min first) |
| writer | `PATI-Alpha-Plan-Review` → `PATI-Fable-5` via local 9router :20128 **only when `/v1/models` lists that alias**. A `PATI-*` writer never uses the native Claude login lane | same picker. Hosted `ai.patigroup.com` when local is down **or the local list has no PATI writer alias** (key from vault `.env`, never printed) |
| images | `GENSEO_IMAGE_BACKEND=gpt` (cx/gpt-image-2.5 via 9router), Grok Imagine fallback | ima2 ChatGPT OAuth lane (`GENSEO_IMA2_PROVIDER=oauth`, `GENSEO_IMA2_MODEL=gpt-6-sol`, $0 subscription) |
| image QC | gem9 judges | gem9 judges (gem9 defaults to the hosted router, so it works without the Mini) |
| tickets | Mini `daily-tickets.md` (#NN) | MacBook `daily-tickets.md` (#MBmmdd-N — ids can never collide) |

**Wrapper copy.** launchd runs `~/bin/grokbot-genseo-daily.sh`, a copy of `deploy/grokbot-genseo-daily.sh`.
A pull does not update that copy. On each Mac, after pull:

```bash
cd ~/genseo && git pull
bash scripts/install_mac_daily_wrapper.sh
```

The script creates `~/bin` if needed, copies the wrapper, checks it is executable, and prints whether
`scripts/genseo_daily_lock.sh` and `scripts/genseo_group_timeout.sh` are in the checkout. It does not
start launchd. Offline: `bash tests/test_install_mac_daily_wrapper.sh`.

**Headless model lane (2026-10-10).** `run_ticket_headless.sh` and `run_landing_headless.sh` share `scripts/genseo_model_lane.sh`. A `PATI-*` writer or fallback (defaults `PATI-Alpha-Plan-Review` and `PATI-Fable-5`) never uses the native Claude login lane: Claude Code does not know those ids (`unrecognized_model`, landing 2026-10-10 09:30). Native login (`~/.claude-genseo`, `loggedIn: true`) is only for a writer and fallback that are not `PATI-*`. For a PATI writer, and whenever native does not apply, local 9router `:20128` is used only when `GET /v1/models` includes `GENSEO_WRITER_MODEL`. MacBook local 9router can be up and still list only `ag/gemini-*` ids. That is not a writer lane: headless falls through to hosted `GENSEO_ROUTER_BASE` (default `https://ai.patigroup.com`) with `NINE_ROUTER_KEY`. The run log records `native`, `local-9router`, or `hosted-9router` and does not print the key.

**Bash on a PATI writer (2026-10-11).** Claude Code 2.1.295+ defaults `claude -p` to permission mode `auto`. Auto mode names the session model as the Bash safety service. `PATI-Alpha-Plan-Review` is a 9router alias, not a classifier `ai.patigroup.com` can run, so Bash returns "Bash safety service `PATI-Alpha-Plan-Review` is unavailable" and the agent exits 0 with the ticket unchanged (articles 2026-10-11 08:19). Read tools still work. Router lanes (`local-9router` and `hosted-9router`) pass `--permission-mode dontAsk`. The tool allowlist stays the gate, and `dontAsk` does not call that classifier. The `[claude-code:unrecognized_model]` line can still print; it is a warning. The id sent to the gateway stays `PATI-Alpha-Plan-Review` (fallback `PATI-Fable-5`). Native login is not pinned. The daily wrapper execs `run_ticket_headless.sh` once per ticket, so the next ticket reads this from disk. No launchd restart.

**Double-publish prevention.** The Macs share no writable state (vault Syncthing is MacBook→Mini
one-way; the Mini's repo commits are unpushed), so the PUBLIC SITE is the lock:
1. `scripts/genseo_published_today.py` counts today's (ICT) posts in `/blogs/news.atom`. Every
   wrapper loop AND `run_ticket_headless.sh` exit when it is ≥ `GENSEO_DAILY_TARGET` (5). Unreadable
   feed = fail closed.
2. `--peer-active 50 --local-log state/published-by-<host>.log`: a post that went live in the last
   50 min and was not published by this Mac means the other Mac is mid-batch → stand down.
3. The runner prompt re-checks the count + STEP 0 `suggest.json` immediately before
   `shopify_publisher.py` (catches a topic the other Mac shipped while this run was writing).
4. Standby waits 20 min at each slot so a healthy Mini goes first.
5. A local mkdir lock (`state/daily.lock`, wrapper PID in `daily.lock/pid`) stops the 14:47
   catch-up overlapping a running batch. A live `grokbot-genseo-daily` is never evicted for
   age, even with no PID file (a batch started before PID stamping). A dead PID is stale and
   may be taken immediately. A missing PID is stale only after 6 hours, so a lock that has not
   finished writing its PID is left alone. Each ticket runs in its own session for 90 minutes
   (`scripts/genseo_group_timeout.sh`); on timeout the process group is killed (ticket bash and
   Claude). `perl alarm; exec` is not used there — that signal hits only bash and leaves Claude
   publishing into the next ticket. launchd runs `~/bin/grokbot-genseo-daily.sh`, a copy of
   `deploy/grokbot-genseo-daily.sh`. After pull, `bash scripts/install_mac_daily_wrapper.sh`
   (`docs/TICKET_REFILL.md`) so the next slot picks this up. It does not start launchd.
   Helpers load from `~/genseo/scripts/`. Offline: `bash tests/test_daily_lock.sh`.

**MacBook lane = all images NO-FACE** until `personas/index.json` is re-synced from the Mini
(angles spent there since 2026-08-15 are unknown here — re-spending one breaks Kevin's
one-angle-per-model rule). QC fails any image with a recognizable face on the no-face lane.

**Fact-check log:** every run writes `logs/claims/<slug>.md` (claim | source | confirmed) and drops
unconfirmed claims before publish (SEL 2026-10-06: Google calls manual fact-checking critical).

**When the Mini comes back:** copy `scripts/genseo_published_today.py`, the guard block of
`run_ticket_headless.sh`, the `--peer-active` check in `grokbot-genseo-daily.sh`, and this section to
the Mini; push the Mini's unpushed commits (or rsync `personas/index.json`, `PUBLISHED_ARTICLES_TRACKER.csv`,
`daily-tickets.md`) so both Macs share persona + tracker state again.

## 0.5 · Landing pages (listicle / advertorial) — NOT part of the 5/day (2026-10-06)

Sales-style pages built from the omnicreatine reference layouts, re-skinned with `brand/<store>.json`.
They are Shopify **pages**, never blog articles: no daily-tickets.md entry, no live-count guard, no tracker row,
and they cannot appear in `/blogs/news.atom`, so they never count toward or block the 5 articles/day.
Run: `scripts/run_landing_headless.sh <listicle|advertorial> <store> "<brief>"` or `--next` (queue `landing-tickets.md`).
Default output is a local preview; `GENSEO_LANDING_DRAFT=1` adds an UNPUBLISHED page; live needs Kevin's GO
(`GENSEO_LANDING_LIVE_OK=1 … --live`, refused while placeholders remain). Details: `skills/genseo-landing-pages/SKILL.md`.
Daily lane (`scripts/run_landing_daily.sh`, launchd 08:15 + 16:15, 1 UNPUBLISHED listicle draft/day): it gives this
Mac's article batch (`state/daily.lock`) at most a 30-min courtesy yield, then builds alongside it — it never waits out
the whole batch, and it never touches the article publisher.
Unpublished listicle prompts carry a standing `SCOPE_WAIVER` (`scripts/run_landing_headless.sh`, 2026-10-11). The writer must not ask a human to proceed. That day's `pure-shilajit-gold-resin` run asked, exited with an empty SPEC, and the wrapper logged FAILED (no spec). The product file was not missing. The DAILY LISTICLE LANE block says it overrides looser rules above; its first bullet keeps the draft standing approval in force.
**Pack palette (Kevin 2026-10-09):** every landing page wears its hero product's packaging colors. The source of truth is
`product_refs/<handle>.palette.json` (`scripts/packaging_palette.py`, `docs/PACKAGING_PALETTE_GUARD.md`); `scripts/landing_palette.py`
applies it in the page body at render, never in the shared theme template. The palette gate + clipped-text check fail a draft that doesn't match.

## 1 · The daily loop

Do these in order. Stop at the first hard stop and report it. One article per day is the
target — do not batch several, and never publish two articles on the same primary keyword.

### 1.1 Pick the work
1. Read `daily-tickets.md`. Take the first ticket that is **not** `[DONE …]`, `[x]`,
   `[SKIPPED-…]`.
2. **If there is no pending ticket, mine one** (§2). Append it under a `# BATCH <YYYY-MM-DD>`
   heading in `daily-tickets.md`, then execute it. Do not skip the day because the queue is
   empty — an empty queue is the job, not a blocker.

### 1.2 Run the pipeline
Follow the `genseo-auto-publish` skill end to end. The two steps that actually kill runs:

- **STEP 0, duplicate check, is not optional.** The live site is the authority — not the
  tracker, not `daily-tickets.md`. Both drift. On 2026-08-13 a full article was written for
  ticket #22 that was **already live**; the tracker row existed and was missed.
  ```bash
  curl -s "https://wellnessnest.co/search/suggest.json?q=PRIMARY_KEYWORD&resources\[type\]=article&resources\[limit\]=5" -A "Mozilla/5.0"
  ```
  Escape the brackets and send a UA, or the JSON comes back malformed. A match → mark the
  ticket `[SKIPPED-DUPLICATE: <url>]` and move to the next ticket.
- **STEP 0.5, `python3 scripts/topic_fitness.py "<title>"`.** `FAIL` → skip, do not write.
  `REVIEW [covered-segment]` → allowed only because Kevin greenlit this queue
  (*"I approve all of them, I need published articles without any delay"*, 2026-08-13).

### 1.3 Gate, publish, record
1. `python3 scripts/validate_article.py <draft>.md --draft` → must print `✓ PASS`.
   Publishing without a PASS is hard rule 1.
2. `python3 scripts/shopify_publisher.py …` — the **only** publish path. Shopify MCP /
   GraphQL / REST drop the JSON-LD. Publish **live/visible**, never draft (Kevin, standing:
   *"just auto publish visible. I will do QA step even after you publish"*).
3. Verify the live URL returns HTTP 200 and the `og:title` is the intended title.
4. Append a row to `PUBLISHED_ARTICLES_TRACKER.csv` and mark the ticket `[DONE …]` in
   `daily-tickets.md`. The tracker row must carry: template, word count, seq, hero persona
   handle + both face angles, QC result, and the scene list — the next run reads them.

### 1.4 Report
Write the run outcome to `logs/daily/<YYYY-MM-DD>.log` and a one-line summary to
`logs/daily/last-run.json`. The cron script reads that file the next morning and reports it
back to Kevin through Eugene.

---

## 2 · Mining a ticket when the queue is empty

**First run the gated refill:** `python3 scripts/refill_tickets.py --count 8 --dry-run`, read it, then drop
`--dry-run`. It appends product-mapped tickets from `templates/article-topic-bank.json` + `board/ideas.csv`
after the same dedup and fitness gates as below; the daily wrapper can call it on its own
(`GENSEO_AUTO_REFILL=1`). See `docs/TICKET_REFILL.md`. Mine by hand only when it exits 3 (sources ran dry).

**GSC is unauthorised on this Mac and the google-ads MCP is not connected**, so the two
normal demand sources are unavailable. Mine at $0 from what is on the machine:

1. Live catalog: `curl -s https://wellnessnest.co/products.json` → 11 SKUs, 6 house brands.
2. Live blog inventory: `ALL_ARTICLES.csv` + `PUBLISHED_ARTICLES_TRACKER.csv`.
3. Gate each candidate through `topic_fitness.py`, then STEP 0 against `suggest.json`.

The pattern that works: **brand + segment long-tail with buyer intent that ends at a SKU we
stock** — dosage, side effects, "vs", "for <audience>", "how long until". One article per
brand+segment pair; once a `vs` shilajit article is live, `seg_taken` correctly vetoes every
other shilajit `vs` topic. That is the guard working.

**Still uncovered, needs a distinct segment angle (not a bare product page):**
`pure-shilajit-gold-resin` ($75) · `shilajit-shockwave` ($79.99).

`scripts/build_catalog_tickets.py` returns 0 tickets on this store — it is brand-coverage
based and every house brand already has a page. Do not wait on it.

---

## 3 · Images — the part that fails most

- **Generator: `scripts/article_images.py` only** (ima2 / ChatGPT Image 2.0 over OAuth, $0).
  Any per-token image API — KIE, Higgsfield, Nano Banana, Veo, Kling — is **forbidden**.
- 1 hero + **≥3 inline**. The gate hard-fails below 3 inline. Hero must be the first
  `![]()` tag in the body; the publisher promotes it to `article.image` and strips it.
- Hero = approved persona **+ real pack**, label-forward. Pack **standing beside** the model,
  hands not touching it — ima2 warps hand-pack grips.
- Every product image needs `--product-ref <handle>` **and** the real pack format described
  in the prompt text ("black-to-green stand-up foil pouch", never "jar"). Prompt text
  overrides the ref when they disagree.
- **QC re-roll budget is 2.** After two FAILs, stop and report. Do not roll a third time.
- **Face-angle hard rule (Kevin, 2026-08-09): never reuse a face angle on the same model,
  ever.** The picker enforces it:
  ```bash
  python3 scripts/persona_picker.py pick   …   # reserves hero + inline angles
  python3 scripts/persona_picker.py commit …   # burns them, append-only
  ```
  `commit` requires `sorted(given) == sorted(issued)` — a pick **always** issues two angles
  (hero + inline) and there is no `--no-inline` flag, so an inline persona image cannot be
  swapped for a no-face one after picking. Angles burn on `commit` only; `release` +
  re-pick is deterministic on seq and re-issues the same angles.
  **Never commit an angle that does not match the image actually shipped** — that permanently
  burns a real angle against a wrong render.

---

## 4 · Standing constraints (do not renegotiate these unattended)

| | |
|---|---|
| 💵 | Images: ima2 OAuth only, $0, standing approval — no cost gate needed. **Any paid media API is forbidden.** |
| 🔑 | **Never create an account, enter a password, or register an API client / developer key.** A source that needs a key is disqualified unless a genuinely anonymous path exists. |
| 🚫 | Permission classifier blocks a call → **report it. Never re-issue it through `curl` to evade the block.** |
| 🌐 | Browser work happens in the in-app Browser pane. Never `open -a Comet` / Chrome. |
| ⛔ | **Never mention or link MuscleMax** (competitor). Never link a product or collection that does not exist — 404 links fail the gate. |
| 🧾 | **No COA / "clinically tested" claims where none exists** (house rule `no-coa-competitive-advantage`). Proxy proof only. |
| 🗑 | Never `rm`. Move to `_superseded/` instead. Never touch `frozen_articles.txt` articles. |
| ✍️ | One author: **Dr. Marcus Hale**, `roster.json` is the sole source. The approved bio sentence must appear **intact, after** the link: `[Dr. Marcus Hale](/pages/dr-marcus-hale) — Dr. Marcus Hale is the resident health researcher behind …` The validator matches the first 60 chars of the bio as a substring; putting the link *inside* the sentence breaks it. |
| 🔒 | `status="pending"` default, the `{active, flagged}` allow-list, and `approve` as the sole pending→active transition in the persona system must stay untouched. |
| 🖼 | Faces come **only** from `~/genseo/personas/`. Never invent a face. New personas need Kevin's one-time real-face gate. |

---

## 5 · Known-broken, work around them (do not try to fix mid-run)

| Thing | State | Workaround |
|---|---|---|
| `WebSearch` / `WebFetch` | **Dead** — 9router routes them to `PATI-Haiku-4.5` | Use `curl` against the live store + local CSVs. No SERP research. |
| Google Search Console | No credentials on this Mac | Blocked on Kevin creating the OAuth desktop client, or a manual Queries CSV export |
| google-ads MCP | Not connected headless | Kevin runs the mining recipe in the app |
| NCBI eutils | IP-blocked | Cite from evidence already banked in tracker rows |
| `scripts/get_internal_links.py` | Returns empty | Pick internal links by hand from `ALL_ARTICLES.csv` |
| IndexNow | Key unconfigured | Skip the ping; note it in the log |
| `hermes cron status` | Reports on the **active profile**, not the one you meant | Check the profile you care about: `launchctl list \| grep gateway-eugene-schwartz` plus the age of `~/.hermes/profiles/eugene-schwartz/cron/ticker_heartbeat` |

---

## 6 · State as of 2026-08-13

**Published.** 22 tracker rows. Batch #15–#22 shipped and all eight verified HTTP 200:
shilajit-side-effects-7-signs · shilajit-resin-vs-gummies · creatine-gummies-dosage ·
shilajit-for-women · turkesterone-vs-ecdysterone · when-to-take-nmn ·
vaginal-probiotics-how-long · how-much-shilajit-per-day.
Last publish seq = **27**.

**Queue.** `daily-tickets.md` is **empty** — 13 `[DONE]` + 1 `[x]` through #14, and #15–#22
are all closed. The first run under this job must mine (§2).

**Persona bank.** 137 personas on disk, **127 active**, 10 retired.
Active by cell: `m3039` 33 · `m4049` 17 · `m5059` 16 · `f3039` 15 · `f4049` 14 · `m2029` 13 ·
`f2029` 9 · `m6070` 5 · `f5059` 5 · **`f6070` 0 (empty)**.
An article needing a woman 60–70 has no face — use a no-face composition and report that the
bank needs expansion.

**Superseded.** `published_drafts/_superseded/how-much-shilajit-per-day.DUPLICATE-do-not-publish-20260813.md`
— written after #22 was already live. Do not publish it. Note that this file overwrote the
local draft that produced the live article, so the local draft for that slug no longer matches
what is on Shopify. The live article itself is fine.

**Open, waiting on Kevin — do not act unattended:**
- 17 published duplicates of *"From Stiff to Strong: Overcoming Joint Pain During Menopause"*
  (ids 612728570171, 614470484283, 615161856315, 615322616123, 615322648891, 615339360571,
  615355056443, 615379501371, 615424557371, 616346288443, 616449343803, 621532021051,
  621532905787, 621533299003, 621533397307, 621533495611, 621567902011). Deletion is
  destructive — needs an explicit go-ahead.
- GemPages page *"Types of Shilajit Products"* (id 611224748347).
- `backfill_seo_metafields.py --all` — classifier-blocked, must not be worked around.
- GSC: path A (Kevin creates the OAuth desktop client) vs path B (manual Queries CSV export).

**Open product/compliance flags (report, don't fix in an article):**
FloraFresh — the PDP description contradicts its Supplement Facts label (15 billion CFU, four
Lactobacillus strains, XOS, D-mannose, "sugar-free" vs Bacillus coagulans SNZ-1969, 1 billion
CFU, maltitol + isomalt). Kevin confirmed the label on 2026-10-09: our copy follows the label
and the PDP rewrite waits for his GO (`docs/FLORAFRESH_FORMULA_GUARD.md`). Also "Treats the
root cause" / "Stays & colonizes" disease claims, "Top OB/GYN recommended formula", "100%
natural ingredients", three inconsistent social-proof counts (71,180+ / 79,239+ / 7,159+).
Gold Resin ($75) and Shockwave ($79.99) publish **no milligram serving size at all** while
both $59.99 SKUs do, and both still carry un-rewritten hype copy. Packaging discrepancies:
shilajit gummies front "60-DAY SUPPLY" vs panel 30 servings; FusiForce front "90 GUMMIES" vs
panel 28×3=84; FusiForce PDP "25 mg ginseng" vs panel "50 mg".

AgeAura promotion is handle-locked (`scripts/ageaura_rules.py`, `docs/AGEAURA_PRODUCT_GUARD.md`):
new tickets and landing specs may target only `ageaura-pure-nmn-tmg-nad-complex`.
`ageaura-pure-urolithin-a` and any other Urolithin A AgeAura handle fail closed in the ticket
builders and `validate_landing.py`. The live Urolithin PDP is not unpublished by this guard.

**Hero-face gate (applied 2026-10-09):** `fetch_personas.py` records
`exaggerated_expression` and `usable_as_identity_reference`. Missing keys on older rows
default to a resting, usable face. `persona_picker.py` will not issue `m3039-as-02`
(QC notes: "Man making a silly face") or any row with `exaggerated_expression: true` or
`usable_as_identity_reference: false` as a hero, and `article_images.py` refuses the same
ref if it is passed by hand. `f6070` is still empty.

---

## 7 · How the job is wired

```
Hermes cron "GenSeo Daily"  (profile eugene-schwartz, 30 7 * * *)
  └─ --script genseo-daily.sh      runs FIRST, every tick, ~3s, NO llm, NO paid call
       ├─ reports yesterday's outcome from logs/daily/last-run.json + the run log
       ├─ live truth: tracker depth, last ticket, last seq
       ├─ preflight: shopify token, queue depth, persona pool health, ima2 daemon
       └─ prints the day's candidate topic + the exact command to run it
  └─ script stdout is injected into Eugene's prompt
  └─ Eugene writes the morning brief → delivered to origin + Feishu
```

**Fully automatic since 2026-08-13.** The script mines or picks the ticket, then launches a
detached `claude -p` run that writes, gates and publishes the article without a human. Eugene's
brief the next morning reports what it did. Kevin approved this explicitly.

⚠️ **The run uses `--permission-mode bypassPermissions`.** That is the one security-relevant
choice in this design, and Kevin approved it on 2026-08-13 after being shown the trade-off. It
is scoped to `~/genseo` via `--add-dir` and cwd, and §4 forbids deleting files, creating
accounts and entering credentials. A stale-PID guard stops a second run stacking on a run that
never finished.

**To revert to brief-only:** delete section 5 of `genseo-daily.sh`. The job then reports and
stops, and nothing publishes without Kevin at the keyboard.

**Why Eugene shells out instead of doing it natively.** Eugene cannot run this pipeline in its
own tool loop: `code_execution.max_tool_calls` is 50 and `terminal.timeout` is 180 s, while
images alone need 600 s+ and one article needs far more than 50 tool calls. Eugene schedules
and reports; the heavy work runs outside its loop.

**Why the job is pinned** (`--model cc/claude-opus-5 --provider custom`). Eugene's global model
drifted to `PATI-Haiku-4.5`, and Hermes fails an unpinned job closed on drift — that is exactly
what killed the 04:00 "TrendTrack Daily Swipe" run on 2026-08-13. The drift guard is skipped
for pinned axes (`cron/scheduler.py:3978`). **Never un-pin this job.**

**The script always runs, even if the agent leg fails.** Hermes executes `--script` at
`scheduler.py:3432`, before the drift guard at `:4015`. A broken gateway or a bad model id
costs the report, not the preflight.

**Operate the job.** Use the `--profile` flag. **`HERMES_PROFILE=…` is silently ignored by
`hermes cron`** — it writes to `active_profile` (`kevin-chief-of-staff`) instead, which is where
the first attempt at this job landed by mistake.
```bash
hermes --profile eugene-schwartz cron list
hermes --profile eugene-schwartz cron run 454070ba1442     # fire once now
hermes --profile eugene-schwartz cron pause 454070ba1442
hermes --profile eugene-schwartz cron runs 454070ba1442
```

**Where the script must live.** Hermes resolves `--script` against the **profile's own**
scripts directory, not the shared one:
`~/.hermes/profiles/eugene-schwartz/scripts/genseo-daily.sh`.
**It must be a real file — a symlink into `~/.hermes/scripts/` is rejected** ("resolves outside
the allowed scripts directory"), which is how the first two test fires failed.

**Delivery is `origin`.** Eugene has no Telegram or Lark chat bound (`telegram.allowed_chats` is
empty, no `feishu` key in its config), so the brief lands in the cron output directory and the
dashboard: `~/.hermes/profiles/eugene-schwartz/cron/output/454070ba1442/`. To push it to a chat,
bind the channel and then `hermes --profile eugene-schwartz cron edit 454070ba1442 --deliver origin,telegram`.

**Fallback chain, fixed 2026-08-13.** Eugene's two fallback model ids were dead
(`PATI-Opus 4.8` — no such model — and `PATI-Sonnet 5` with a space). Corrected to `PATI-Opus-5`
and `PATI-Sonnet-5`, both real on 9router. Backup: `config.yaml.bak-20260813-fallbackfix`.
`model.default` is still `PATI-Haiku-4.5`; that is the drift this job is pinned against.

⚠️ **The `PATI-*` aliases on 9router do not serve the model their name claims.** Probed
2026-08-13 against `http://127.0.0.1:20128/v1/chat/completions`:

| alias | actually served |
|---|---|
| `PATI-Opus-5` | `gpt-5.6-sol-review` |
| `PATI-Sonnet-5` | `grok-4.5-medium` |
| `PATI-Haiku-4.5` | `gpt-5.6-luna-review` |

The `cc/claude-*` ids do serve the right Claude models, but they answer with an SSE stream even
on a non-streamed request, and Hermes drops to the fallback every run — so this job's brief is
in practice written by whatever `PATI-Opus-5` maps to, not by Opus. The brief is a small
summarisation task so the output is fine, but **this affects every Hermes agent on this Mac,
not just GenSeo.** Fixing the 9router alias table is a separate job.

# Mac Mini failover

The MacBook Pro is the machine whose daily launchd is loaded. The Mac Mini
(`Kevins-Mac-mini-2.local`) is the failover. It does not run the daily article
job or the daily landing job until this bootstrap installs those plists, and it
installs them only when the guard says the MacBook is not the active runner.
The MacBook article plist in this repo is already `GENSEO_HOST_ROLE=primary`
with ticket prefix `MB`. This bootstrap does not edit that plist or
`deploy/grokbot-genseo-daily.sh`. An already-loaded MacBook agent can still
be `standby` until that plist is copied and bootstrapped again (`DAILY-RUN.md`).

Only one Mac may have `com.pati.genseo-daily` and `com.pati.genseo-landing`
loaded. Listicle pages from that landing job stay unpublished drafts.

`scripts/mac_return_reconcile.sh` is the MacBook dry-run checklist. It does not
install Mini plists, and it does not start launchd. Do not load the MacBook
daily or landing agents while the Mini still has those labels bootstrapped.
The public-site peer window in `deploy/grokbot-genseo-daily.sh` still applies
after a machine is loaded. This bootstrap is the gate that keeps the second
launchd from being installed. It cannot see the other Mac and it does not
call `launchctl`.

## Names

| What | Value |
|---|---|
| Mini DNS hostname | `Kevins-Mac-mini-2.local` |
| Cursor worker on the MacBook | `--name MacBook-Pro` |
| Cursor worker on the Mini | `--name Mac-Mini` |
| Guard token for the MacBook | `macbook-pro` |
| Article launchd label | `com.pati.genseo-daily` |
| Landing launchd label | `com.pati.genseo-landing` |
| Worker launchd label | `com.pati.cursor-agent-worker` |

The Cursor worker name, the guard token, and the DNS hostname are three
different strings.

## CLI

Cursor's installer symlinks the same binary to `~/.local/bin/agent` and
`~/.local/bin/cursor-agent`. Use `cursor-agent`. The name `agent` is also what
the Grok CLI installs, and whichever install ran last owns that symlink.
`agent worker start --name` is the My Machines command; the plist runs it as
`cursor-agent worker start --name Mac-Mini --worker-dir ~/genseo`.

Docs: [CLI installation](https://cursor.com/docs/cli/installation),
[My Machines](https://cursor.com/docs/cloud-agent/self-hosted/my-machines),
[parameters](https://cursor.com/docs/cli/reference/parameters).

## Checklist

Dry-run is the default. It writes nothing and does not call `launchctl`.

```bash
cd ~/genseo && git fetch origin main && git checkout main && git pull --ff-only origin main
bash scripts/mac_mini_failover_bootstrap.sh
```

It checks:

- `~/.local/bin/cursor-agent` and `~/.grok/bin/grok` exist and are executable
- `~/genseo` is a git checkout, clean, on `main`
- `.env` key names only. Shopify keys are the `e["SHOPIFY_CLI_APP_..."]` reads
  in `scripts/shopify_app_token.py` (`~/genseo/.env`, last assignment, no
  `export`). `NINE_ROUTER_KEY` is the vault read in `scripts/genseo_model_lane.sh`
  (`~/PATI/LLM-Wiki/.env`, first `^(export )?NINE_ROUTER_KEY=` line). Values are
  never printed.
- `~/.genseo/shopify_token.json` exists and has a real `shop` and `access_token`
  (the file is not printed)

## Worker plist

```bash
bash scripts/mac_mini_failover_bootstrap.sh --install-worker
```

That writes `~/Library/LaunchAgents/com.pati.cursor-agent-worker.plist`
(`RunAtLoad` and `KeepAlive`, logs under `~/Library/Logs`). It does not load
the agent and it does not install the daily plists. Sign in once on the Mini
with `cursor-agent login`, then load:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.pati.cursor-agent-worker.plist
```

## Primary / failover guard

The script reads subjects on `origin/main`. It does not fetch, pull, or push.
It walks every matching subject on that ref, not a short window that can hide
an older heartbeat behind unrelated `failover-` commits.

- `failover-heartbeat: macbook-pro <epoch>` — the MacBook is the active runner
  at that unix time
- `failover-release: macbook-pro <epoch>` — the MacBook agents were unloaded

`<epoch>` is digits only, from `date +%s`. The host token is lowercase
`macbook-pro`. The marker is the commit subject, not the body.

`--enable-daily` is allowed only when the newest release epoch is greater than
the newest heartbeat epoch. A missing marker leaves the MacBook active.
A heartbeat that is hours or days old does **not** authorize the Mini. The
daily job does not write these markers, so silence is not proof the MacBook
is offline or unhealthy. `GENSEO_FAILOVER_HEARTBEAT_MAX_AGE` is ignored if it
is set. An epoch more than one hour in the future fail-closes when it is a
heartbeat; an epoch more than seven days ahead is ignored and cannot
authorize a release.

A local file on one Mac is not the guard. The two machines do not share a home
directory.

## Handing the daily jobs to the Mini

On the MacBook, unload the agents first. The marker commit has to be made on
`main` with an empty index, then pushed without `--force`. `git push origin
HEAD:main` from another branch can publish that branch. A normal `git commit`
would record whatever is staged, including a secret.

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-daily.plist
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-landing.plist
cd ~/genseo
git checkout main
git pull --ff-only origin main
git diff --cached --quiet
git commit --allow-empty -m "failover-release: macbook-pro $(date +%s)"
git show --stat HEAD
git push origin main
```

`git diff --cached --quiet` must succeed before the commit. `git show --stat`
must list no files. Do not use `--force`.

On the Mini, fetch so `origin/main` has that subject, then:

```bash
cd ~/genseo && git fetch origin main && git checkout main && git pull --ff-only origin main
bash scripts/mac_mini_failover_bootstrap.sh --enable-daily
```

When the guard allows, that copies:

- `deploy/com.pati.genseo-daily.mini.plist` → `~/Library/LaunchAgents/com.pati.genseo-daily.plist`
  (`GENSEO_HOST_ROLE=primary`, ticket prefix `MM`, `GENSEO_NO_FACE=1`)
- `deploy/com.pati.genseo-landing.mini.plist` → `~/Library/LaunchAgents/com.pati.genseo-landing.plist`

`/Users/kevinkreative` in those templates is rewritten to the current home.
`--enable-daily` also runs `scripts/install_mac_daily_wrapper.sh`, which copies
the article wrapper to `~/bin` and does not start launchd. Load only after the
MacBook bootout:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-daily.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-landing.plist
```

`GENSEO_NO_FACE=1` matches the landing Mini plist. The Mini has not had
`personas/index.json` confirmed, and spending a face angle twice breaks the
one-angle rule. The landing lane still builds one unpublished `gsl-preview-*`
draft. It does not publish.

While the Mini is primary, leave the MacBook agents unloaded. Loading both
schedules the same 07:30 / 14:47 article slots and the same 08:15 / 16:15
landing slots.

To record that the MacBook is running again, unload the Mini first. On the
Mini, `--disable-daily` removes only plists that carry
`installed-by: mac_mini_failover_bootstrap`. It does not call `launchctl`.

```bash
bash scripts/mac_mini_failover_bootstrap.sh --disable-daily
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-daily.plist
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-landing.plist
```

Then on the MacBook, load its agents and push a heartbeat from `main` the same
way as the release (empty index, no `--force`):

```bash
cd ~/genseo
git checkout main
git pull --ff-only origin main
git diff --cached --quiet
git commit --allow-empty -m "failover-heartbeat: macbook-pro $(date +%s)"
git show --stat HEAD
git push origin main
```

A heartbeat with no newer release blocks the next `--enable-daily`, including
when that heartbeat is older than 36 hours. Already-installed Mini plists stay
on disk until `--disable-daily`. Leaving them loaded beside the MacBook
schedules both machines. The Mini article plist is `primary` for the handover
window so it does not sit in `standby` waiting for a MacBook that was unloaded.
That is safe only while the MacBook agents are actually unloaded. This script
cannot check that.

## Test

```bash
bash tests/test_mac_mini_failover_bootstrap.sh
```

The test uses temp directories. It does not call `launchctl` or the network.
`GENSEO_FAILOVER_TEST=1` is how that test writes LaunchAgents off Darwin. On a
Mac the installer already may write; the test flag is not part of the handover.

#!/bin/bash
# GenSeo daily batch — runs on WHICHEVER Mac is online (Kevin 2026-10-06: no automation may depend on one Mac).
# launchd com.pati.genseo-daily: 07:30 batch, 08:05 check, 14:47 catch-up.
# Loops run_ticket_headless.sh (one ticket per call) until today's ICT live count reaches GENSEO_DAILY_TARGET.
# GENSEO_AUTO_REFILL=1: when fewer tickets are open than are still to publish today, scripts/refill_tickets.py
# tops daily-tickets.md up once per run (gated, lint-checked; docs/TICKET_REFILL.md). Default off.
#
# Double-publish prevention (the two Macs share NO writable state: vault Syncthing is MacBook->Mini one-way,
# ticket files are per-Mac, the Mini's repo commits are unpushed) — so the PUBLIC SITE is the shared state:
#   1. before every ticket: live count today (genseo_published_today.py) >= target -> stop   [both Macs]
#   2. before every ticket: a post went live in the last GENSEO_PEER_WINDOW_MIN minutes that THIS Mac did not
#      publish -> the other Mac is mid-batch -> stop; the next slot tops up whatever is missing
#   3. inside the run, right before shopify_publisher.py: count + STEP 0 suggest.json re-check (runner prompt)
#   4. ticket ids per Mac never collide (MacBook batch uses #MBmmdd-N) and STEP 0 kills same-topic repeats
#   5. GENSEO_HOST_ROLE=standby waits GENSEO_STANDBY_DELAY_MIN first, so a healthy peer
#      has a head start and rule 2 makes this Mac stand down. The MacBook plist is
#      primary with GENSEO_TICKET_PREFIX=MB until a Mini failover release is explicit
#      (MacBook agents unloaded, Mini plist loaded as primary). The wrapper default
#      is primary. Standby is only when the LaunchAgent sets it. Do not load both
#      Macs as primary. Prefix fallback: standby -> MB, otherwise MM, unless
#      GENSEO_TICKET_PREFIX is set (the MacBook plist sets MB so a primary MacBook
#      does not mint Mini MM ids).
#   6. local mkdir lock (state/daily.lock + pid): catch-up exits while that PID is a live
#      grokbot-genseo-daily, however old the lock is. A dead PID is stale. A missing PID is
#      stale only after 6h (GENSEO_LOCK_STALE_SEC), so a lock still being stamped is not stolen.
#      A live wrapper with no PID file (the pre-PID lock) is not stolen for age either.
#   7. each ticket is its own session, 90 min (GENSEO_TICKET_TIMEOUT_SEC). The deadline is
#      monotonic elapsed time. Timeout TERMs then KILLs the descendant tree (ticket bash,
#      Claude, and workers that called setsid) and the process group. perl `alarm; exec`
#      only signaled bash and left Claude publishing into the next ticket. A timeout is a
#      no-publish; the EXIT trap releases state/daily.lock when this wrapper returns.
# launchd runs ~/bin/grokbot-genseo-daily.sh, a copy of this file. After git pull:
#   bash ~/genseo/scripts/install_mac_daily_wrapper.sh
# Pulling alone is not enough. That copy is what 07:30, 08:05, and 14:47 execute. The
# installer does not start launchd and does not change the loaded plist. The role
# is LaunchAgent environment: copy deploy/com.pati.genseo-daily.macbook.plist over
# ~/Library/LaunchAgents/com.pati.genseo-daily.plist and bootstrap the agent again,
# or the loaded job keeps GENSEO_HOST_ROLE=standby. Helpers load from ~/genseo/scripts/.
# Offline: bash tests/test_daily_lock.sh
# Wake: launchd can start this file before DNS is up (2026-10-16 08:51 ICT).
# scripts/genseo_wait_for_network.sh runs after the lock and before the first
# feed read. It waits until wellnessnest.co and the Shopify admin host resolve,
# up to GENSEO_NET_WAIT_MAX_SEC (default 600) with backoff. Each wait is logged.
# If DNS never comes up, the log says "network not ready — timeout" and this
# file exits 1 before any feed read. GENSEO_NET_WAIT_MAX_SEC=0 skips that wait.
# An unreadable live count (-1) is still retried GENSEO_LIVE_FEED_RETRIES times
# (default 3, cap 5) with GENSEO_LIVE_FEED_BACKOFF_SEC between tries (default 5,
# cap 30), then fail closed. A readable count does not sleep there and still
# runs the peer-active check. That retry is not the wake wait.
# Checkout: after that wait succeeds, scripts/genseo_sync_main.sh runs
# `git fetch origin main` and `git merge --ff-only origin/main` when local
# main can fast-forward. Untracked files that would not be overwritten stay.
# A tracked edit that would be overwritten is stashed or backed up and logged.
# A publish/* branch returns to main (the branch ref is kept). The fetch runs
# from a copy of this file so git does not rewrite the script bash is reading.
# It does not fast-forward while another GenSeo job holds a lane lock or has
# a checkout script open. A fast-forward re-execs
# ~/genseo/deploy/grokbot-genseo-daily.sh (same PID, so state/daily.lock stays
# held). After each ticket, HEAD is switched back to main when it is still on
# publish/*. launchd runs ~/bin. After a successful sync this file sources
# scripts/genseo_self_apply.sh, which reinstalls ~/bin when the bytes differ
# (bash scripts/install_mac_daily_wrapper.sh) and reloads a changed LaunchAgent
# only after this process exits. It does not start a run. Later edits of this
# file are read from the repo on the re-exec. Pulling alone does not update
# ~/bin until that self-apply runs. A ~/bin older than the re-exec still needs
# one manual bash scripts/install_mac_daily_wrapper.sh.
# Sleep (2026-10-17): the Mac was in maintenance sleep at 07:27 and dark-woke
# at 07:38 with DNS down until 07:39. pmset "sleep 1" is an idle timer, so a
# running batch can be suspended without a power assertion. Before the stable
# copy, this file arms caffeinate -i -s -w of its own PID
# (scripts/genseo_power_assert.sh). That covers the DNS wait and every ticket.
# -i blocks idle sleep. -s blocks system sleep on AC, including a dark wake
# returning to sleep. On battery -s is not enforced. No sudo and no pmset
# change. A missing caffeinate is logged and the run continues. The loaded
# plist should also put /usr/bin/caffeinate -i -s in front of this file so the
# assertion starts at launchd's exec. Self-apply copies that plist and
# bootstraps it after this process exits. An agent that was never loaded still
# needs one manual copy and bootstrap. RunAtLoad stays false.
# The 08:05 slot is this same job. launchd does not start a second instance
# while one is still running, and the daily lock exits 0 if a second copy
# does start. A count that has already reached the daily target does not
# start a ticket. A 07:30 that never fired, or that exited early, is retried
# at 08:05 instead of waiting until 14:47. Intervals the Mac slept through
# coalesce into one fire on wake. The DNS wait below still bounds a resolver
# that is down for about a minute (the 07:38 dark wake) inside its 600s budget.
set -uo pipefail
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$HOME/.codex/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
G="$HOME/genseo"; PY=/usr/bin/python3
if [ -f "$G/scripts/genseo_power_assert.sh" ]; then
  # shellcheck source=../scripts/genseo_power_assert.sh
  . "$G/scripts/genseo_power_assert.sh" || {
    printf '%s\n' "FATAL: could not load scripts/genseo_power_assert.sh" >&2
    exit 1
  }
  genseo_power_assert_arm || true
fi
if [ -f "$G/scripts/genseo_sync_main.sh" ]; then
  # shellcheck source=../scripts/genseo_sync_main.sh
  . "$G/scripts/genseo_sync_main.sh" || {
    printf '%s\n' "FATAL: could not load scripts/genseo_sync_main.sh" >&2
    exit 1
  }
  genseo_exec_stable_copy grokbot-genseo-daily "$@"
fi
TARGET="${GENSEO_DAILY_TARGET:-5}"
ROLE="${GENSEO_HOST_ROLE:-primary}"
DELAY="${GENSEO_STANDBY_DELAY_MIN:-20}"
PEER_WIN="${GENSEO_PEER_WINDOW_MIN:-50}"
MAX_RUNS="${GENSEO_MAX_RUNS:-9}"
TICKET_TIMEOUT="${GENSEO_TICKET_TIMEOUT_SEC:-5400}"
case "$TICKET_TIMEOUT" in
  ''|*[!0-9]*|0) TICKET_TIMEOUT=5400 ;;
esac
REFILL="${GENSEO_AUTO_REFILL:-0}"
REFILL_BUFFER="${GENSEO_REFILL_BUFFER:-3}"
REFILL_PREFIX="${GENSEO_TICKET_PREFIX:-$([ "$ROLE" = standby ] && echo MB || echo MM)}"
# Extra reads after the first -1. 0 keeps the old single-check fail-closed.
# Caps stop a bad LaunchAgent value from spinning or sleeping for hours.
LIVE_FEED_RETRIES="${GENSEO_LIVE_FEED_RETRIES:-3}"
LIVE_FEED_BACKOFF="${GENSEO_LIVE_FEED_BACKOFF_SEC:-5}"
case "$LIVE_FEED_RETRIES" in
  ''|*[!0-9]*) LIVE_FEED_RETRIES=3 ;;
esac
if [ "$LIVE_FEED_RETRIES" -gt 5 ]; then LIVE_FEED_RETRIES=5; fi
case "$LIVE_FEED_BACKOFF" in
  ''|*[!0-9]*) LIVE_FEED_BACKOFF=5 ;;
esac
if [ "$LIVE_FEED_BACKOFF" -gt 30 ]; then LIVE_FEED_BACKOFF=30; fi
HOST="$(hostname -s)"; DAY="$(date +%F)"
LOGDIR="$G/logs/daily"; mkdir -p "$LOGDIR" "$G/state"
LOG="$LOGDIR/$DAY.log"
export GENSEO_TIMEOUT_LOG="$LOG"
MINE="$G/state/published-by-$HOST.log"     # URLs this Mac published (one per line: <iso-ts> <url>)
LOCK="$G/state/daily.lock"
ts(){ date '+%F %T'; }
say(){ echo "[$(ts)] [$HOST/$ROLE] $*" | tee -a "$LOG"; }
export GENSEO_DAILY_TARGET="$TARGET"
if declare -F genseo_power_assert_note >/dev/null 2>&1; then
  genseo_power_assert_note || true
fi

if [ ! -f "$G/scripts/genseo_daily_lock.sh" ] || [ ! -f "$G/scripts/genseo_group_timeout.sh" ]; then
  say "FATAL: missing scripts/genseo_daily_lock.sh or scripts/genseo_group_timeout.sh — git pull ~/genseo, then bash scripts/install_mac_daily_wrapper.sh"
  exit 1
fi
if [ ! -f "$G/scripts/genseo_wait_for_network.sh" ]; then
  say "FATAL: missing scripts/genseo_wait_for_network.sh — git pull ~/genseo, then bash scripts/install_mac_daily_wrapper.sh"
  exit 1
fi
# shellcheck source=../scripts/genseo_daily_lock.sh
. "$G/scripts/genseo_daily_lock.sh" || { say "FATAL: could not load daily lock helper"; exit 1; }
# shellcheck source=../scripts/genseo_wait_for_network.sh
. "$G/scripts/genseo_wait_for_network.sh" || { say "FATAL: could not load network wait helper"; exit 1; }
# A re-exec after the fast-forward keeps this PID and the lock it already holds.
lock_owned=0
if declare -F genseo_daily_lock_is_ours >/dev/null 2>&1 && genseo_daily_lock_is_ours; then
  lock_owned=1
fi
if [ "$lock_owned" != 1 ]; then
  genseo_daily_lock_acquire
  lock_rc=$?
  case "$lock_rc" in
    0) ;;
    10) exit 0 ;;
    *) exit "$lock_rc" ;;
  esac
fi
if declare -F genseo_return_publish_branch_to_main >/dev/null 2>&1 && declare -F genseo_stable_copy_release >/dev/null 2>&1; then
  trap 'genseo_return_publish_branch_to_main || true; genseo_daily_lock_release; genseo_stable_copy_release now || true' EXIT
elif declare -F genseo_stable_copy_release >/dev/null 2>&1; then
  trap 'genseo_daily_lock_release; genseo_stable_copy_release now || true' EXIT
else
  trap 'genseo_daily_lock_release' EXIT
fi

live_urls(){ $PY "$G/scripts/genseo_published_today.py" --json 2>/dev/null | $PY -c 'import json,sys
d=json.load(sys.stdin); [print(e["url"]) for e in d.get("entries",[])]' 2>/dev/null; }
live_count(){ local n; n="$($PY "$G/scripts/genseo_published_today.py" 2>/dev/null | tail -1)"; case "$n" in ''|*[!0-9-]*) n=-1;; esac; echo "$n"; }

# The start line below is the first feed read. Wait for DNS before it so a
# wake does not burn the short live-feed retry on ENOTFOUND / -1.
# The fast-forward is after that wait and before the feed read. A re-exec
# already waited, and it already holds the lock.
if [ "${GENSEO_NET_WAIT_DONE:-}" != 1 ]; then
  if ! genseo_wait_for_network; then
    exit 1
  fi
  export GENSEO_NET_WAIT_DONE=1
fi
if [ "${GENSEO_MAIN_SYNCED:-}" != 1 ]; then
  if declare -F genseo_sync_origin_main >/dev/null 2>&1; then
    genseo_sync_origin_main "$G/deploy/grokbot-genseo-daily.sh" "$@"
  else
    say "WARN: origin/main not updated — missing scripts/genseo_sync_main.sh — continuing on the current checkout"
  fi
fi
# Only after a successful sync. A fetch failure, a refused fast-forward, or a
# dry-run leaves GENSEO_MAIN_SYNCED unset and does not touch ~/bin or launchd.
if [ "${GENSEO_MAIN_SYNCED:-}" = 1 ] && [ -f "$G/scripts/genseo_self_apply.sh" ]; then
  # shellcheck source=../scripts/genseo_self_apply.sh
  . "$G/scripts/genseo_self_apply.sh" || say "WARN: self-apply could not be loaded — continuing on the current setup"
  if declare -F genseo_self_apply >/dev/null 2>&1; then
    genseo_self_apply com.pati.genseo-daily || say "WARN: self-apply failed — continuing on the current setup"
  fi
fi
say "start (target $TARGET/day, live now $(live_count))"
if [ "$ROLE" = "standby" ] && [ "${GENSEO_NO_DELAY:-0}" != "1" ]; then
  say "standby: waiting ${DELAY} min so a healthy peer Mac goes first"; sleep $(( DELAY * 60 ))
fi

fails=0; pw=0; refilled=0; PEER_MAX_WAITS="${GENSEO_PEER_MAX_WAITS:-6}"
for i in $(seq 1 $(( MAX_RUNS + ${GENSEO_PEER_MAX_WAITS:-6} ))); do
  n="$(live_count)"
  feed_try=0
  while [ "$n" -lt 0 ] && [ "$feed_try" -lt "$LIVE_FEED_RETRIES" ]; do
    feed_try=$((feed_try + 1))
    say "live feed unreadable — retry $feed_try/$LIVE_FEED_RETRIES in ${LIVE_FEED_BACKOFF}s"
    if [ "$LIVE_FEED_BACKOFF" -gt 0 ]; then
      sleep "$LIVE_FEED_BACKOFF"
    fi
    n="$(live_count)"
  done
  if [ "$n" -lt 0 ]; then say "live feed unreadable — fail closed, exit"; exit 1; fi
  if [ "$n" -ge "$TARGET" ]; then say "DONE: $n/$TARGET live for $DAY (ICT)"; exit 0; fi
  peer="$($PY "$G/scripts/genseo_published_today.py" --peer-active "$PEER_WIN" --local-log "$MINE" 2>/dev/null)"; rc=$?
  if [ "$rc" = 3 ]; then
    # 2026-10-07 fix: standing down for good let a peer that died after 1 post leave the day at 1/5.
    # Wait out the peer window and re-check; if the peer publishes nothing more, this Mac takes over.
    pw=$((pw+1))
    if [ "$pw" -gt "$PEER_MAX_WAITS" ]; then say "$peer — peer still active after $PEER_MAX_WAITS waits, standing down at $n/$TARGET"; exit 0; fi
    say "$peer — other Mac is publishing; wait ${PEER_WIN} min ($pw/$PEER_MAX_WAITS) then re-check (take over if it went quiet)"
    sleep $(( PEER_WIN * 60 )); continue
  fi
  open=$(grep -cE '^(- \[ \]|## \[ \])' "$G/daily-tickets.md" 2>/dev/null || true)
  need=$(( TARGET - n ))
  if [ "$REFILL" = "1" ] && [ "$refilled" = 0 ] && [ "${open:-0}" -lt "$need" ]; then
    refilled=1
    say "${open:-0} open ticket(s) for $need still to publish today → refill_tickets.py (prefix $REFILL_PREFIX)"
    perl -e 'alarm 600; exec @ARGV' "$PY" "$G/scripts/refill_tickets.py" --if-below "$need" \
      --count $(( need - ${open:-0} + REFILL_BUFFER )) --prefix "$REFILL_PREFIX" >> "$LOG" 2>&1; frc=$?
    case "$frc" in
      0) ;;
      3) say "refill: fewer topics passed than asked — add topics to templates/article-topic-bank.json or board/ideas.csv" ;;
      *) say "refill failed (exit $frc) — see $LOG" ;;
    esac
    git -C "$G" add -- daily-tickets.md board/ideas.csv 2>/dev/null \
      && git -C "$G" commit -q -m "queue: refill_tickets.py on $HOST" -- daily-tickets.md board/ideas.csv >/dev/null 2>&1
    open=$(grep -cE '^(- \[ \]|## \[ \])' "$G/daily-tickets.md" 2>/dev/null || true)
  fi
  if [ "${open:-0}" -eq 0 ]; then say "ticket queue EMPTY at $n/$TARGET — hard stop (no empty-queue model burn); refill daily-tickets.md"; exit 0; fi
  if ! lint="$($PY "$G/scripts/lint_tickets.py" "$G/daily-tickets.md" 2>&1)"; then
    say "ticket lint FAILED (banned AgeAura/Urolithin link in an open ticket) — fix daily-tickets.md; stopping"; echo "$lint" >> "$LOG"; exit 1
  fi
  before="$(live_urls | sort)"
  say "run $i: live $n/$TARGET, $open open ticket(s) → run_ticket_headless.sh"
  /bin/bash "$G/scripts/genseo_group_timeout.sh" "$TICKET_TIMEOUT" /bin/bash "$G/scripts/run_ticket_headless.sh"; rrc=$?
  if declare -F genseo_return_publish_branch_to_main >/dev/null 2>&1; then
    genseo_return_publish_branch_to_main || true
  fi
  after="$(live_urls | sort)"
  new="$(comm -13 <(echo "$before") <(echo "$after") | sed '/^$/d')"
  if [ -n "$new" ]; then
    while read -r u; do echo "$(date '+%FT%T%z') $u" >> "$MINE"; say "published: $u"; done <<< "$new"
    fails=0
  else
    fails=$((fails+1))
    if [ "$rrc" -eq 124 ]; then
      say "run $i TIMEOUT exit 124 after ${TICKET_TIMEOUT}s — nothing new went live (fail #$fails)"
    else
      say "run $i exit $rrc — nothing new went live (skip/dup/fail #$fails)"
    fi
    [ "$fails" -ge 3 ] && { say "3 runs in a row without a publish — stopping; check logs/articles-*.log"; exit 1; }
  fi
done
say "max runs reached at $(live_count)/$TARGET"

#!/bin/bash
# GenSeo daily batch — runs on WHICHEVER Mac is online (Kevin 2026-10-06: no automation may depend on one Mac).
# launchd com.pati.genseo-daily: 07:30 batch + 14:47 catch-up (same slots as the Mini).
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
#   5. GENSEO_HOST_ROLE=standby (MacBook) waits GENSEO_STANDBY_DELAY_MIN first, so if the Mini is healthy its
#      07:30 batch has a head start and rule 2 makes this Mac stand down.
#   6. local mkdir lock (state/daily.lock + pid): catch-up exits while that PID is a live
#      grokbot-genseo-daily, however old the lock is. A dead PID is stale. A missing PID is
#      stale only after 6h (GENSEO_LOCK_STALE_SEC), so a lock still being stamped is not stolen.
#      A live wrapper with no PID file (the pre-PID lock) is not stolen for age either.
#   7. each ticket is its own session, 90 min (GENSEO_TICKET_TIMEOUT_SEC). Timeout kills the
#      process group (ticket bash + Claude). perl `alarm; exec` only signaled bash and left Claude
#      publishing into the next ticket.
# launchd runs ~/bin/grokbot-genseo-daily.sh, a copy of this file. After git pull, copy it to ~/bin/
# (docs/TICKET_REFILL.md) so the next slot uses this; helpers load from ~/genseo/scripts/.
# Offline: bash tests/test_daily_lock.sh
set -uo pipefail
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$HOME/.codex/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
G="$HOME/genseo"; PY=/usr/bin/python3
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
HOST="$(hostname -s)"; DAY="$(date +%F)"
LOGDIR="$G/logs/daily"; mkdir -p "$LOGDIR" "$G/state"
LOG="$LOGDIR/$DAY.log"
MINE="$G/state/published-by-$HOST.log"     # URLs this Mac published (one per line: <iso-ts> <url>)
LOCK="$G/state/daily.lock"
ts(){ date '+%F %T'; }
say(){ echo "[$(ts)] [$HOST/$ROLE] $*" | tee -a "$LOG"; }
export GENSEO_DAILY_TARGET="$TARGET"

if [ ! -f "$G/scripts/genseo_daily_lock.sh" ] || [ ! -f "$G/scripts/genseo_group_timeout.sh" ]; then
  say "FATAL: missing scripts/genseo_daily_lock.sh or scripts/genseo_group_timeout.sh — git pull ~/genseo, then cp this wrapper to ~/bin/"
  exit 1
fi
# shellcheck source=../scripts/genseo_daily_lock.sh
. "$G/scripts/genseo_daily_lock.sh" || { say "FATAL: could not load daily lock helper"; exit 1; }
genseo_daily_lock_acquire
lock_rc=$?
case "$lock_rc" in
  0) ;;
  10) exit 0 ;;
  *) exit "$lock_rc" ;;
esac
trap 'genseo_daily_lock_release' EXIT

live_urls(){ $PY "$G/scripts/genseo_published_today.py" --json 2>/dev/null | $PY -c 'import json,sys
d=json.load(sys.stdin); [print(e["url"]) for e in d.get("entries",[])]' 2>/dev/null; }
live_count(){ local n; n="$($PY "$G/scripts/genseo_published_today.py" 2>/dev/null | tail -1)"; case "$n" in ''|*[!0-9-]*) n=-1;; esac; echo "$n"; }

say "start (target $TARGET/day, live now $(live_count))"
if [ "$ROLE" = "standby" ] && [ "${GENSEO_NO_DELAY:-0}" != "1" ]; then
  say "standby: waiting ${DELAY} min so a healthy peer Mac goes first"; sleep $(( DELAY * 60 ))
fi

fails=0; pw=0; refilled=0; PEER_MAX_WAITS="${GENSEO_PEER_MAX_WAITS:-6}"
for i in $(seq 1 $(( MAX_RUNS + ${GENSEO_PEER_MAX_WAITS:-6} ))); do
  n="$(live_count)"
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
  after="$(live_urls | sort)"
  new="$(comm -13 <(echo "$before") <(echo "$after") | sed '/^$/d')"
  if [ -n "$new" ]; then
    while read -r u; do echo "$(date '+%FT%T%z') $u" >> "$MINE"; say "published: $u"; done <<< "$new"
    fails=0
  else
    fails=$((fails+1)); say "run $i exit $rrc — nothing new went live (skip/dup/fail #$fails)"
    [ "$fails" -ge 3 ] && { say "3 runs in a row without a publish — stopping; check logs/articles-*.log"; exit 1; }
  fi
done
say "max runs reached at $(live_count)/$TARGET"

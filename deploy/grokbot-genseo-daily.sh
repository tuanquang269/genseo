#!/bin/bash
# GenSeo daily batch — runs on WHICHEVER Mac is online (Kevin 2026-10-06: no automation may depend on one Mac).
# launchd com.pati.genseo-daily: 07:30 batch + 14:47 catch-up (same slots as the Mini).
# Loops run_ticket_headless.sh (one ticket per call) until today's ICT live count reaches GENSEO_DAILY_TARGET.
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
#   6. local mkdir lock: the 14:47 catch-up never overlaps a still-running 07:30 batch on the same Mac.
set -uo pipefail
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$HOME/.codex/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
G="$HOME/genseo"; PY=/usr/bin/python3
TARGET="${GENSEO_DAILY_TARGET:-5}"
ROLE="${GENSEO_HOST_ROLE:-primary}"
DELAY="${GENSEO_STANDBY_DELAY_MIN:-20}"
PEER_WIN="${GENSEO_PEER_WINDOW_MIN:-50}"
MAX_RUNS="${GENSEO_MAX_RUNS:-9}"
HOST="$(hostname -s)"; DAY="$(date +%F)"
LOGDIR="$G/logs/daily"; mkdir -p "$LOGDIR" "$G/state"
LOG="$LOGDIR/$DAY.log"
MINE="$G/state/published-by-$HOST.log"     # URLs this Mac published (one per line: <iso-ts> <url>)
LOCK="$G/state/daily.lock"
ts(){ date '+%F %T'; }
say(){ echo "[$(ts)] [$HOST/$ROLE] $*" | tee -a "$LOG"; }
export GENSEO_DAILY_TARGET="$TARGET"

if ! mkdir "$LOCK" 2>/dev/null; then
  if [ $(( $(date +%s) - $(stat -f %m "$LOCK") )) -gt 21600 ]; then rmdir "$LOCK"; mkdir "$LOCK" || exit 1
  else say "another batch is running on this Mac (lock $LOCK) — exit"; exit 0; fi
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

live_urls(){ $PY "$G/scripts/genseo_published_today.py" --json 2>/dev/null | $PY -c 'import json,sys
d=json.load(sys.stdin); [print(e["url"]) for e in d.get("entries",[])]' 2>/dev/null; }
live_count(){ local n; n="$($PY "$G/scripts/genseo_published_today.py" 2>/dev/null | tail -1)"; case "$n" in ''|*[!0-9-]*) n=-1;; esac; echo "$n"; }

say "start (target $TARGET/day, live now $(live_count))"
if [ "$ROLE" = "standby" ] && [ "${GENSEO_NO_DELAY:-0}" != "1" ]; then
  say "standby: waiting ${DELAY} min so a healthy peer Mac goes first"; sleep $(( DELAY * 60 ))
fi

fails=0; pw=0; PEER_MAX_WAITS="${GENSEO_PEER_MAX_WAITS:-6}"
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
  if [ "${open:-0}" -eq 0 ]; then say "ticket queue EMPTY at $n/$TARGET — hard stop (no empty-queue model burn); refill daily-tickets.md"; exit 0; fi
  if ! lint="$($PY "$G/scripts/lint_tickets.py" "$G/daily-tickets.md" 2>&1)"; then
    say "ticket lint FAILED (banned AgeAura/Urolithin link in an open ticket) — fix daily-tickets.md; stopping"; echo "$lint" >> "$LOG"; exit 1
  fi
  before="$(live_urls | sort)"
  say "run $i: live $n/$TARGET, $open open ticket(s) → run_ticket_headless.sh"
  perl -e 'alarm 5400; exec @ARGV' /bin/bash "$G/scripts/run_ticket_headless.sh"; rrc=$?
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

#!/bin/bash
# Offline self-check of scripts/run_landing_daily.sh scheduling + locks: no Shopify, no model, no images, no git.
#   bash tests/test_landing_daily_lock.sh                                # ~80 s (case 7 waits out a real 1-min yield)
#   LANDING_WRAPPER=<another copy> bash tests/test_landing_daily_lock.sh  # same cases against another wrapper
# Every case runs the REAL wrapper under `env -i HOME=<sandbox>`, so its G=$HOME/genseo is a throwaway dir whose
# scripts/ are stubs: landing_guard.py replays scripted exit codes (state/guard-codes; none left = 0, slot free) and
# run_landing_headless.sh only records that the agent would start now, with which env, and whether state/daily.lock
# was held at that moment. No spec is produced, so a run that reaches the agent ends "FAILED: no spec produced".
# scripts/genseo_group_timeout.sh is copied in for real. Case 11 caps a TERM-ignoring child at 1s. Case 12 deletes
# that helper and expects a fail-closed exit before the agent.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WRAPPER="${LANDING_WRAPPER:-$ROOT/scripts/run_landing_daily.sh}"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/landing-lock-test.XXXXXX")" || exit 1
cleanup() {
  local p f
  kill $(jobs -p) 2>/dev/null || true
  if [ -n "${TMP:-}" ] && [ -d "$TMP" ]; then
    while IFS= read -r f; do
      p=$(tr -cd '0-9' < "$f" 2>/dev/null || true)
      [ -n "$p" ] && kill -KILL "$p" 2>/dev/null || true
    done < <(find "$TMP" -type f \( -name 'child.pid' -o -name 'runner.pid' \) 2>/dev/null)
  fi
  rm -rf "$TMP"
}
trap cleanup EXIT
PASS=0; FAIL=0; H=""; S=""; RC=""; T0=0

sandbox(){  # sandbox <name> [guard exit codes...]: fresh fake HOME in $H, its genseo/state in $S
  H="$TMP/$1"; shift; S="$H/genseo/state"; local sc="$H/genseo/scripts"
  mkdir -p "$sc" "$S" "$H/genseo/logs"
  cp "$ROOT/scripts/genseo_group_timeout.sh" "$sc/genseo_group_timeout.sh"
  echo "$*" > "$S/guard-codes"
  cat > "$sc/landing_guard.py" <<'PY'
import sys
codes = open("state/guard-codes").read().split()
open("state/guard-codes", "w").write(" ".join(codes[1:]))
print("stub landing_guard: exit", codes[0] if codes else 0)
sys.exit(int(codes[0]) if codes else 0)
PY
  cat > "$sc/build_landing_tickets.py" <<'PY'
q = "daily-landing-tickets.md"
try:
    s = open(q).read()
except FileNotFoundError:
    s = "# stub queue\n\n"
if "- [ ] " not in s:
    open(q, "w").write(s + "- [ ] listicle | wellnessnest | product=stub-product - angle: stub (added 2026-01-01)\n")
PY
  echo 'import sys; sys.exit(0)' > "$sc/lint_tickets.py"
  echo 'console.log("stub trustpilot")' > "$sc/trustpilot_reviews.mjs"
  cat > "$sc/run_landing_headless.sh" <<'SH'
{ echo "ts=$(date +%s)"; [ -d state/daily.lock ] && echo "art_lock=held" || echo "art_lock=free"
  echo "env=daily:${GENSEO_LANDING_DAILY:-} draft:${GENSEO_LANDING_DRAFT:-} live_ok:${GENSEO_LANDING_LIVE_OK:-}"
  echo "args=$*"; } > state/agent-called
SH
}
run(){  # run <timeout s> [VAR=value ...]: the real wrapper on the current sandbox, with a clean environment
  local t=$1; shift
  T0=$(date +%s)
  env -i HOME="$H" PATH=/usr/bin:/bin:/usr/sbin:/sbin "$@" \
    /usr/bin/perl -e 'alarm shift; exec @ARGV' "$t" /bin/bash "$WRAPPER" > "$H/out.log" 2>&1
  RC=$?
}
check(){  # check <description> <command...>
  local d=$1; shift
  if "$@"; then PASS=$((PASS+1)); echo "  ok    $d"
  else FAIL=$((FAIL+1)); echo "  FAIL  $d (wrapper rc=$RC)"; tail -4 "$H/out.log" | sed 's/^/        | /'; fi
}
not(){ ! "$@"; }
rc_is(){ [ "$RC" = "$1" ]; }
logged(){ grep -qF -- "$1" "$H/out.log"; }
agent_started(){ [ -f "$S/agent-called" ]; }
agent_saw(){ grep -qxF -- "$1" "$S/agent-called" 2>/dev/null; }
started_after(){  # started_after <min s> <max s>: the agent started that long after the wrapper did
  local t; t="$(sed -n 's/^ts=//p' "$S/agent-called" 2>/dev/null)"
  [ -n "$t" ] && [ $(( t - T0 )) -ge "$1" ] && [ $(( t - T0 )) -le "$2" ]
}
wait_dead() {
  local p=$1 i
  for i in $(seq 1 40); do
    kill -0 "$p" 2>/dev/null || return 0
    sleep 0.05
  done
  return 1
}
# Stamp for touch -t, N hours ago. BSD date -v (macOS bash 3.2) first.
# GNU date -d only if -v did not print [[CC]YY]MMDDhhmm[.SS]. Never try -d
# first: on macOS, date -d sets the kernel DST flag.
touch_mtime_hours_ago() {
  local hours=$1 path=$2 stamp=""
  stamp=$(date -v-"${hours}"H +%Y%m%d%H%M.%S 2>/dev/null) || true
  case "$stamp" in
    [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].[0-9][0-9]) ;;
    *) stamp="" ;;
  esac
  if [ -z "$stamp" ]; then
    stamp=$(date -d "${hours} hours ago" +%Y%m%d%H%M.%S 2>/dev/null) || true
    case "$stamp" in
      [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].[0-9][0-9]) ;;
      *) return 1 ;;
    esac
  fi
  touch -t "$stamp" "$path"
}
# Epoch mtime for the fixture check. GNU stat -c first; BSD stat -f second.
# Same order as path_mtime in scripts/run_landing_daily.sh.
epoch_mtime() {
  local p=$1 m=""
  m=$(stat -c %Y "$p" 2>/dev/null) || true
  case "$m" in
    ''|*[!0-9]*) m="" ;;
  esac
  if [ -z "$m" ]; then
    m=$(stat -f %m "$p" 2>/dev/null) || true
    case "$m" in
      ''|*[!0-9]*) m="" ;;
    esac
  fi
  if [ -z "$m" ]; then
    m=$(/usr/bin/python3 -c 'import os,sys; print(int(os.stat(sys.argv[1]).st_mtime))' "$p" 2>/dev/null) || true
    case "$m" in
      ''|*[!0-9]*) return 1 ;;
    esac
  fi
  printf '%s\n' "$m"
}

echo "wrapper: $WRAPPER"
echo "1. today's draft already exists (guard exit 3) -> stand down, even with the article batch running"
sandbox exists 3; mkdir "$S/daily.lock"; run 20
check "exit 0" rc_is 0
check "logged DONE" logged "today's gsl- landing draft already exists"
check "agent never started" not agent_started

echo "2. Shopify unreadable (guard exit 1) -> fail closed"
sandbox unreadable 1; run 20
check "exit 1" rc_is 1
check "logged fail closed" logged "fail closed"
check "agent never started" not agent_started

echo "3. kill switch (state/landing-daily.disabled)"
sandbox disabled; touch "$S/landing-daily.disabled"; run 20
check "exit 0" rc_is 0
check "logged disabled" logged "disabled (kill switch)"
check "agent never started" not agent_started

echo "4. another landing run holds state/landing-daily.lock -> exit and leave its lock alone"
sandbox busy; mkdir "$S/landing-daily.lock"; run 20
check "exit 0" rc_is 0
check "logged another landing run" logged "another landing run is active"
check "agent never started" not agent_started
check "the other run's lock is still there" test -d "$S/landing-daily.lock"

echo "5. article batch running, yield 0 -> builds alongside it at once, in the draft-only lane"
sandbox alongside; mkdir "$S/daily.lock"; run 30 GENSEO_LANDING_ARTICLE_YIELD_MIN=0
check "agent started within 10 s" started_after 0 10
check "while state/daily.lock was held" agent_saw "art_lock=held"
check "logged building alongside" logged "still running — building alongside it"
check "GENSEO_LANDING_DAILY=1 + GENSEO_LANDING_DRAFT=1, no GENSEO_LANDING_LIVE_OK" agent_saw "env=daily:1 draft:1 live_ok:"
check "daily queue, next ticket" agent_saw "args=--queue daily-landing-tickets.md --next"
check "wrapper carried on after the agent (stub made no spec)" logged "FAILED: no spec produced"
check "article lock untouched" test -d "$S/daily.lock"
check "landing lock released" test ! -e "$S/landing-daily.lock"

echo "6. article batch finishes 3 s into a 1-min yield -> builds as soon as the lock clears"
sandbox clears; mkdir "$S/daily.lock"; ( sleep 3; rmdir "$S/daily.lock" ) &
run 45 GENSEO_LANDING_ARTICLE_YIELD_MIN=1 GENSEO_LANDING_POLL_SEC=1
check "agent started 2-15 s in, not after the full minute" started_after 2 15
check "after the lock cleared" agent_saw "art_lock=free"
check "logged article batch finished" logged "article batch finished — building now"

echo "7. article batch outlasts a 1-min yield -> builds alongside it after ~60 s"
sandbox outlasts; mkdir "$S/daily.lock"; run 120 GENSEO_LANDING_ARTICLE_YIELD_MIN=1 GENSEO_LANDING_POLL_SEC=5
check "agent started 58-90 s in" started_after 58 90
check "while state/daily.lock was held" agent_saw "art_lock=held"
check "logged the yield" logged "yielding up to 1 min"
check "logged building alongside" logged "still running — building alongside it"

echo "8. stale article lock (7 h old, batch long gone) -> no yield at all"
sandbox stale; mkdir "$S/daily.lock"
if ! touch_mtime_hours_ago 7 "$S/daily.lock"; then
  FAIL=$((FAIL+1)); echo "  FAIL  could not stamp a 7h-old mtime (BSD date -v / GNU date -d)"
  fixture_age=0
else
  fixture_m="$(epoch_mtime "$S/daily.lock" || true)"
  if [ -n "${fixture_m:-}" ]; then fixture_age=$(( $(date +%s) - fixture_m )); else fixture_age=0; fi
  if [ "$fixture_age" -ge 21600 ]; then
    PASS=$((PASS+1)); echo "  ok    fixture mtime is older than 6h"
  else
    FAIL=$((FAIL+1)); echo "  FAIL  fixture mtime is older than 6h (age=${fixture_age}s)"
  fi
fi
run 30
check "agent started within 10 s" started_after 0 10
check "no yield logged" not logged "yielding"

echo "9. peer Mac made today's draft while this Mac yielded (guard 0, then 3) -> stand down"
sandbox peer_yield 0 3; mkdir "$S/daily.lock"; run 30 GENSEO_LANDING_ARTICLE_YIELD_MIN=0
check "exit 0" rc_is 0
check "logged stand down" logged "draft appeared meanwhile — stand down"
check "agent never started" not agent_started

echo "10. standby: peer made today's draft during the standby delay (guard 0, then 3) -> stand down"
sandbox standby 0 3; run 30 GENSEO_HOST_ROLE=standby GENSEO_LANDING_STANDBY_DELAY_MIN=0
check "exit 0" rc_is 0
check "logged peer stand down" logged "peer Mac already made today's draft — stand down"
check "agent never started" not agent_started

echo "11. listicle writer uses the process-group timeout"
check "syntax landing wrapper" bash -n "$ROOT/scripts/run_landing_daily.sh"
check "syntax group timeout" bash -n "$ROOT/scripts/genseo_group_timeout.sh"
check "GNU stat -c is tried before BSD stat -f" awk '
  /stat -c %Y/ { if (!gnu) gnu=NR }
  /stat -f %m/ { if (!bsd) bsd=NR }
  END { exit !(gnu && bsd && gnu < bsd) }
' "$ROOT/scripts/run_landing_daily.sh"
check "BSD date -v is tried before GNU date -d" awk '
  /date -v-/ { if (!bsd) bsd=NR }
  /date -d "/ { if (!gnu) gnu=NR }
  END { exit !(bsd && gnu && bsd < gnu) }
' "$ROOT/tests/test_landing_daily_lock.sh"
check "calls group timeout" grep -q 'genseo_group_timeout.sh' "$ROOT/scripts/run_landing_daily.sh"
check "default cap is 5400s" grep -q 'GENSEO_LANDING_TIMEOUT_SEC:-5400' "$ROOT/scripts/run_landing_daily.sh"
check "ticket line is not perl alarm" not grep -q 'alarm .*run_landing_headless' "$ROOT/scripts/run_landing_daily.sh"
sandbox group_timeout
cat > "$H/genseo/scripts/run_landing_headless.sh" << 'EOF'
#!/bin/bash
state="$HOME/genseo/state"
printf '%s\n' "$$" > "$state/runner.pid"
perl -e '
  $SIG{TERM} = "IGNORE";
  $SIG{HUP} = "IGNORE";
  $SIG{INT} = "IGNORE";
  open my $f, ">", $ARGV[0] or die $!;
  print $f "$$\n";
  close $f;
  sleep 60;
' "$state/child.pid" &
wait
EOF
run 40 GENSEO_LANDING_TIMEOUT_SEC=1 GENSEO_TIMEOUT_GRACE_SEC=0
check "logged agent exit 124" logged "agent exit 124"
check "timeout warned in the day log" grep -q "signaling process group" "$H/genseo/logs/landing-daily/"*.log
check "returned before the child sleep" test $(( $(date +%s) - T0 )) -lt 25
childp=$(tr -cd '0-9' < "$S/child.pid" 2>/dev/null || true)
check "child pid was recorded" test -n "$childp"
check "TERM-ignoring child is dead" wait_dead "$childp"
runnerp=$(tr -cd '0-9' < "$S/runner.pid" 2>/dev/null || true)
check "runner pid was recorded" test -n "$runnerp"
check "runner is dead" wait_dead "$runnerp"
check "wrapper carried on after the timeout" logged "FAILED: no spec produced"
check "landing lock released" test ! -e "$S/landing-daily.lock"
check "exit 1" rc_is 1

echo "12. missing group-timeout helper fails closed before the agent"
sandbox missing_helper
rm -f "$H/genseo/scripts/genseo_group_timeout.sh"
run 20
check "exit 1" rc_is 1
check "logged FATAL" logged "FATAL: missing scripts/genseo_group_timeout.sh"
check "agent never started" not agent_started
check "landing lock was not taken" test ! -e "$S/landing-daily.lock"

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" = 0 ]

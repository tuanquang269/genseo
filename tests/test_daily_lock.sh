#!/bin/bash
# Offline checks for the article-daily lock and the 90-minute process-group timeout.
# No Shopify, no Claude, no network.
#   bash tests/test_daily_lock.sh
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../scripts/genseo_daily_lock.sh
. "$ROOT/scripts/genseo_daily_lock.sh"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/daily-lock-test.XXXXXX")" || exit 1
PIDS=""
SLEEPER=""
H=""
LOCK=""
SAYLOG=""
RC=0
PASS=0
FAIL=0

track() { PIDS="$PIDS $*"; }
cleanup() {
  local p f
  for p in $PIDS; do kill -KILL "$p" 2>/dev/null || true; done
  if [ -n "${TMP:-}" ] && [ -d "$TMP" ]; then
    while IFS= read -r f; do
      p=$(tr -cd '0-9' < "$f" 2>/dev/null || true)
      [ -n "$p" ] && kill -KILL "$p" 2>/dev/null || true
    done < <(find "$TMP" -type f \( -name 'child.pid' -o -name 'sleeper.pid' -o -name 'runner.pid' \) 2>/dev/null)
  fi
  jobs -p | while read -r p; do kill -KILL "$p" 2>/dev/null || true; done
  rm -rf "$TMP"
}
trap cleanup EXIT

say() { printf '%s\n' "$*" >> "$SAYLOG"; }
not() { ! "$@"; }
check() {
  local d=$1
  shift
  if "$@"; then
    PASS=$((PASS + 1))
    printf '  ok    %s\n' "$d"
  else
    FAIL=$((FAIL + 1))
    printf '  FAIL  %s\n' "$d"
    if [ -n "${SAYLOG:-}" ] && [ -f "$SAYLOG" ]; then sed 's/^/        | /' "$SAYLOG"; fi
    if [ -n "${H:-}" ] && [ -f "$H/out.log" ]; then tail -20 "$H/out.log" | sed 's/^/        | /'; fi
    if [ -n "${H:-}" ] && [ -f "$H/err.log" ]; then tail -10 "$H/err.log" | sed 's/^/        ! /'; fi
  fi
}
pid_of() {
  local p=""
  [ -f "$LOCK/pid" ] || return 1
  IFS= read -r p < "$LOCK/pid" || return 1
  printf '%s\n' "$p"
}
new_lock() {
  local d="$TMP/lock-$1"
  mkdir -p "$d"
  LOCK="$d/daily.lock"
  SAYLOG="$d/say.log"
  : > "$SAYLOG"
}
set_age() {
  /usr/bin/python3 - "$1" "$2" <<'PY'
import os, sys, time
p, sec = sys.argv[1], int(sys.argv[2])
t = time.time() - sec
os.utime(p, (t, t))
PY
}
start_wrapper_sleeper() {
  # Double-fork so the sleeper is not a child of this shell. The lock scan ignores
  # this shell's own forks (they still wear the wrapper cmdline); a real catch-up is
  # a sibling, and the sleeper has to look like one.
  local pf="$TMP/wrapper-sleeper.pid"
  rm -f "$pf"
  perl -MPOSIX -e '
    use POSIX qw(setsid);
    my $pid = fork();
    exit 0 if $pid;
    setsid();
    fork() and exit 0;
    open my $f, ">", shift @ARGV or exit 1;
    print $f "$$\n";
    close $f;
    exec @ARGV or exit 1;
  ' "$pf" bash -c 'exec -a grokbot-genseo-daily sleep 120' >/dev/null &
  local starter=$!
  wait "$starter" 2>/dev/null || true
  wait_file "$pf" || return 1
  SLEEPER=$(tr -cd '0-9' < "$pf")
  track "$SLEEPER"
  kill -0 "$SLEEPER"
}
start_other_sleeper() {
  sleep 120 >/dev/null &
  SLEEPER=$!
  track "$SLEEPER"
  sleep 0.1
  kill -0 "$SLEEPER"
}
stop_sleeper() {
  [ -n "${SLEEPER:-}" ] || return 0
  kill -KILL "$SLEEPER" 2>/dev/null || true
  wait "$SLEEPER" 2>/dev/null || true
  SLEEPER=""
}
acquire() {
  genseo_daily_lock_acquire
  RC=$?
  return 0
}
wait_file() {
  local f=$1 i
  for i in $(seq 1 50); do
    [ -s "$f" ] && return 0
    sleep 0.05
  done
  return 1
}
wait_dead() {
  local p=$1 i
  for i in $(seq 1 40); do
    kill -0 "$p" 2>/dev/null || return 0
    sleep 0.05
  done
  return 1
}

echo "1. command match: the wrapper, not an editor or cp"
check "bash script is the wrapper" genseo_cmd_is_daily_wrapper "/bin/bash /Users/kevinkreative/bin/grokbot-genseo-daily.sh"
check "argv0 sleeper is the wrapper" genseo_cmd_is_daily_wrapper "grokbot-genseo-daily 120"
check "vim is not" not genseo_cmd_is_daily_wrapper "vim /Users/kevinkreative/bin/grokbot-genseo-daily.sh"
check "cp is not" not genseo_cmd_is_daily_wrapper "cp deploy/grokbot-genseo-daily.sh /Users/kevinkreative/bin/grokbot-genseo-daily.sh"
check "grep is not" not genseo_cmd_is_daily_wrapper "grep grokbot-genseo-daily logs/daily/x.log"

echo "2. fresh acquire records this PID and release drops only our lock"
new_lock fresh
acquire
check "acquire rc 0" test "$RC" = 0
check "lock is a directory" test -d "$LOCK"
check "pid is this shell" test "$(pid_of)" = "$$"
check "started stamp exists" test -f "$LOCK/started"
genseo_daily_lock_release
check "release removes our lock" test ! -e "$LOCK"

echo "3. release does not remove a lock owned by another PID"
new_lock foreign
if ! start_other_sleeper; then echo "sleeper failed"; exit 1; fi
mkdir "$LOCK"
printf '%s\n' "$SLEEPER" > "$LOCK/pid"
genseo_daily_lock_release
check "foreign lock remains" test -d "$LOCK"
check "foreign pid unchanged" test "$(pid_of)" = "$SLEEPER"
stop_sleeper

echo "4. live wrapper PID, lock 8h old — do not steal"
new_lock liveold
if ! start_wrapper_sleeper; then echo "wrapper sleeper failed"; exit 1; fi
mkdir "$LOCK"
printf '%s\n' "$SLEEPER" > "$LOCK/pid"
set_age "$LOCK" 28800
acquire
check "busy rc 10" test "$RC" = 10
check "logged another batch" grep -q "another batch is running" "$SAYLOG"
check "did not take over" not grep -q "taking over" "$SAYLOG"
check "pid unchanged" test "$(pid_of)" = "$SLEEPER"
check "sleeper still alive" kill -0 "$SLEEPER"
stop_sleeper

echo "5. live non-wrapper PID, lock young — do not steal"
new_lock youngother
if ! start_other_sleeper; then echo "sleeper failed"; exit 1; fi
mkdir "$LOCK"
printf '%s\n' "$SLEEPER" > "$LOCK/pid"
acquire
check "busy rc 10" test "$RC" = 10
check "pid unchanged" test "$(pid_of)" = "$SLEEPER"
stop_sleeper

echo "6. live non-wrapper PID, lock 8h old, no real wrapper — take it"
new_lock oldother
if ! start_other_sleeper; then echo "sleeper failed"; exit 1; fi
mkdir "$LOCK"
printf '%s\n' "$SLEEPER" > "$LOCK/pid"
set_age "$LOCK" 28800
acquire
check "takeover rc 0" test "$RC" = 0
check "logged taking over" grep -q "taking over" "$SAYLOG"
check "pid is us" test "$(pid_of)" = "$$"
check "unrelated sleeper still alive" kill -0 "$SLEEPER"
genseo_daily_lock_release
stop_sleeper

echo "7. dead PID, lock young — take it"
new_lock dead
mkdir "$LOCK"
printf '%s\n' 99999999 > "$LOCK/pid"
acquire
check "takeover rc 0" test "$RC" = 0
check "logged taking over" grep -q "taking over" "$SAYLOG"
check "pid is us" test "$(pid_of)" = "$$"
genseo_daily_lock_release

echo "8. dead PID while a wrapper is actually running — do not steal"
new_lock deadlive
if ! start_wrapper_sleeper; then echo "wrapper sleeper failed"; exit 1; fi
mkdir "$LOCK"
printf '%s\n' 99999999 > "$LOCK/pid"
acquire
check "busy rc 10" test "$RC" = 10
check "dead pid left in place" test "$(pid_of)" = 99999999
check "sleeper still alive" kill -0 "$SLEEPER"
stop_sleeper

echo "9. missing PID, lock young or 2h — do not steal; 8h with nobody running — take it"
new_lock missyoung
mkdir "$LOCK"
acquire
check "young missing is busy" test "$RC" = 10
check "still no pid file" test ! -f "$LOCK/pid"

new_lock miss2h
mkdir "$LOCK"
set_age "$LOCK" 7200
acquire
check "2h missing is busy (default 6h)" test "$RC" = 10

new_lock miss8h
mkdir "$LOCK"
set_age "$LOCK" 28800
acquire
check "8h missing is takeover" test "$RC" = 0
check "logged taking over" grep -q "taking over" "$SAYLOG"
genseo_daily_lock_release

echo "10. missing PID, lock 8h old, wrapper still running — do not steal for age"
new_lock misslive
if ! start_wrapper_sleeper; then echo "wrapper sleeper failed"; exit 1; fi
mkdir "$LOCK"
set_age "$LOCK" 28800
acquire
check "busy rc 10" test "$RC" = 10
check "did not stamp a pid" test ! -f "$LOCK/pid"
check "sleeper still alive" kill -0 "$SLEEPER"
stop_sleeper

echo "11. GENSEO_LOCK_STALE_SEC overrides the 6h default"
new_lock custom
mkdir "$LOCK"
set_age "$LOCK" 60
GENSEO_LOCK_STALE_SEC=30
acquire
unset GENSEO_LOCK_STALE_SEC
check "custom threshold takeover" test "$RC" = 0
genseo_daily_lock_release

SAYLOG=""
echo "12. PID file names this process (PID reuse) — adopt, do not treat us as another batch"
selfdir="$TMP/self"
mkdir -p "$selfdir"
cat > "$selfdir/self.sh" << 'EOF'
#!/bin/bash
set -u
. "$HELPER"
say() { :; }
mkdir -p "$(dirname "$LOCK")"
mkdir "$LOCK"
printf '%s\n' "$$" > "$LOCK/pid"
genseo_daily_lock_acquire
rc=$?
printf '%s\n' "$rc" > "$OUT/rc"
printf '%s\n' "$$" > "$OUT/self"
if [ -f "$LOCK/pid" ]; then cat "$LOCK/pid" > "$OUT/pid"; fi
if [ "$rc" -eq 0 ]; then genseo_daily_lock_release; fi
EOF
env HELPER="$ROOT/scripts/genseo_daily_lock.sh" LOCK="$selfdir/daily.lock" OUT="$selfdir" \
  bash -c 'exec -a grokbot-genseo-daily /bin/bash "$1"' _ "$selfdir/self.sh"
check "adopt rc 0" test "$(cat "$selfdir/rc")" = 0
check "adopted pid is that process" test "$(tr -cd '0-9' < "$selfdir/pid")" = "$(tr -cd '0-9' < "$selfdir/self")"
check "adopt released the lock" test ! -e "$selfdir/daily.lock"

echo "13. wrapper script wires the helper and does not alarm-exec the ticket"
check "syntax daily wrapper" bash -n "$ROOT/deploy/grokbot-genseo-daily.sh"
check "syntax lock helper" bash -n "$ROOT/scripts/genseo_daily_lock.sh"
check "syntax group timeout" bash -n "$ROOT/scripts/genseo_group_timeout.sh"
check "calls group timeout" grep -q 'genseo_group_timeout.sh' "$ROOT/deploy/grokbot-genseo-daily.sh"
check "acquires pid lock" grep -q 'genseo_daily_lock_acquire' "$ROOT/deploy/grokbot-genseo-daily.sh"
check "ticket line is not perl alarm" not grep -q 'alarm .*run_ticket_headless' "$ROOT/deploy/grokbot-genseo-daily.sh"

echo "14. group timeout returns the command status and kills the process group"
ign="$TMP/ignore.sh"
cat > "$ign" << 'EOF'
#!/bin/bash
printf '%s\n' "$$" > "$2"
perl -e '
  $SIG{TERM} = "IGNORE";
  $SIG{HUP} = "IGNORE";
  $SIG{INT} = "IGNORE";
  open my $f, ">", $ARGV[0] or die $!;
  print $f "$$\n";
  close $f;
  sleep 8;
' "$1" &
wait
EOF
t0=$(date +%s)
GENSEO_TIMEOUT_GRACE_SEC=0 /bin/bash "$ROOT/scripts/genseo_group_timeout.sh" 5 /bin/bash -c 'exit 3' >"$TMP/exit3.out" 2>"$TMP/exit3.err"
RC=$?
t1=$(date +%s)
check "exit 3 propagates" test "$RC" = 3
check "did not wait out 5s" test $((t1 - t0)) -le 3

GENSEO_TIMEOUT_GRACE_SEC=0 /bin/bash "$ROOT/scripts/genseo_group_timeout.sh" 5 /bin/does-not-exist-genseo >"$TMP/miss.out" 2>"$TMP/miss.err"
RC=$?
check "missing command is 127" test "$RC" = 127

/bin/bash "$ROOT/scripts/genseo_group_timeout.sh" >"$TMP/usage.out" 2>"$TMP/usage.err"
RC=$?
check "usage is 2" test "$RC" = 2

sleep 60 >/dev/null &
sib=$!
track "$sib"
kid="$TMP/child.pid"
runf="$TMP/runner.pid"
GENSEO_TIMEOUT_GRACE_SEC=0 /bin/bash "$ROOT/scripts/genseo_group_timeout.sh" 5 /bin/bash "$ign" "$kid" "$runf" >"$TMP/to.out" 2>"$TMP/to.err" &
tp=$!
track "$tp"
check "child pid appeared" wait_file "$kid"
child=$(tr -cd '0-9' < "$kid")
runner=$(tr -cd '0-9' < "$runf")
pgid=$(ps -o pgid= -p "$child" | tr -d '[:space:]')
check "child stays in the ticket session" test "$pgid" = "$runner"
wait "$tp"
RC=$?
check "timeout exit 124" test "$RC" = 124
check "stderr names the group" grep -q "signaling process group" "$TMP/to.err"
check "TERM-ignoring child is dead" wait_dead "$child"
check "sibling outside the group survived" kill -0 "$sib"
kill -KILL "$sib" 2>/dev/null || true
wait "$sib" 2>/dev/null || true

echo "15. SIGTERM to the waiter is forwarded to the ticket group"
kid2="$TMP/child2.pid"
runf2="$TMP/runner2.pid"
GENSEO_TIMEOUT_GRACE_SEC=0 /bin/bash "$ROOT/scripts/genseo_group_timeout.sh" 6 /bin/bash "$ign" "$kid2" "$runf2" >"$TMP/fwd.out" 2>"$TMP/fwd.err" &
tp=$!
track "$tp"
check "forward child appeared" wait_file "$kid2"
child2=$(tr -cd '0-9' < "$kid2")
sleep 0.2
kill -TERM "$tp"
wait "$tp"
RC=$?
check "forward exit 143" test "$RC" = 143
check "stderr says forwarding" grep -q "forwarding signal" "$TMP/fwd.err"
check "forwarded KILL reached the child" wait_dead "$child2"

sandbox() {
  H="$TMP/wrap-$1"
  local sc="$H/genseo/scripts"
  mkdir -p "$sc" "$H/genseo/state" "$H/genseo/logs/daily"
  cp "$ROOT/scripts/genseo_daily_lock.sh" "$sc/genseo_daily_lock.sh"
  cp "$ROOT/scripts/genseo_group_timeout.sh" "$sc/genseo_group_timeout.sh"
  cat > "$sc/genseo_published_today.py" << 'PY'
import os, sys
root = os.path.join(os.environ["HOME"], "genseo")
if "--json" in sys.argv:
    print('{"entries":[]}')
    raise SystemExit(0)
if "--peer-active" in sys.argv:
    raise SystemExit(0)
print(open(os.path.join(root, "state", "live-count")).read().strip())
PY
  printf '%s\n' 'import sys; sys.exit(0)' > "$sc/lint_tickets.py"
  printf '%s\n' '0' > "$H/genseo/state/live-count"
}
run_wrapper() {
  local t=$1
  perl -e 'alarm shift; exec @ARGV' "$t" \
    env -i HOME="$H" PATH="/usr/bin:/bin:/usr/sbin:/sbin" \
      GENSEO_DAILY_TARGET="${WRAP_TARGET:-5}" \
      GENSEO_MAX_RUNS="${WRAP_MAX_RUNS:-1}" \
      GENSEO_PEER_MAX_WAITS="${WRAP_PEER_WAITS:-0}" \
      GENSEO_TICKET_TIMEOUT_SEC="${WRAP_TICKET_TIMEOUT:-5400}" \
      GENSEO_TIMEOUT_GRACE_SEC="${WRAP_GRACE:-0}" \
      GENSEO_NO_DELAY=1 \
      GENSEO_AUTO_REFILL=0 \
      /bin/bash "$ROOT/deploy/grokbot-genseo-daily.sh" >"$H/out.log" 2>"$H/err.log"
  RC=$?
}
echo "16. real wrapper: missing helper fails closed"
sandbox missing
rm -f "$H/genseo/scripts/genseo_daily_lock.sh"
run_wrapper 15
check "exit 1" test "$RC" = 1
check "logged FATAL" grep -q "FATAL: missing" "$H/out.log"

echo "17. real wrapper: 8h lock held by a live wrapper — catch-up exits, lock untouched"
sandbox busy
if ! start_wrapper_sleeper; then echo "wrapper sleeper failed"; exit 1; fi
mkdir "$H/genseo/state/daily.lock"
printf '%s\n' "$SLEEPER" > "$H/genseo/state/daily.lock/pid"
set_age "$H/genseo/state/daily.lock" 28800
run_wrapper 15
check "exit 0" test "$RC" = 0
check "logged another batch" grep -q "another batch is running" "$H/out.log"
check "did not start a batch" not grep -q "start (target" "$H/out.log"
check "did not take over" not grep -q "taking over" "$H/out.log"
check "pid unchanged" test "$(tr -cd '0-9' < "$H/genseo/state/daily.lock/pid")" = "$SLEEPER"
check "sleeper still alive" kill -0 "$SLEEPER"
check "lock still held" test -d "$H/genseo/state/daily.lock"
stop_sleeper

echo "18. real wrapper: dead PID is taken, then released on the way out"
sandbox dead
mkdir "$H/genseo/state/daily.lock"
printf '%s\n' 99999999 > "$H/genseo/state/daily.lock/pid"
printf '%s\n' 5 > "$H/genseo/state/live-count"
run_wrapper 15
check "exit 0" test "$RC" = 0
check "logged taking over" grep -q "taking over" "$H/out.log"
check "reached DONE" grep -q "DONE:" "$H/out.log"
check "lock released" test ! -e "$H/genseo/state/daily.lock"

echo "19. real wrapper: ticket timeout kills a child that ignores TERM"
sandbox timeout
printf '%s\n' 0 > "$H/genseo/state/live-count"
printf '%s\n' '- [ ] **#900** timeout test' > "$H/genseo/daily-tickets.md"
cat > "$H/genseo/scripts/run_ticket_headless.sh" << 'EOF'
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
  sleep 40;
' "$state/child.pid" &
wait
EOF
WRAP_TARGET=5
WRAP_MAX_RUNS=1
WRAP_PEER_WAITS=0
WRAP_TICKET_TIMEOUT=1
WRAP_GRACE=0
run_wrapper 20
check "wrapper exit 0" test "$RC" = 0
check "logged timeout 124" grep -q "exit 124" "$H/out.log"
check "timeout warned" grep -q "signaling process group" "$H/err.log"
childp=$(tr -cd '0-9' < "$H/genseo/state/child.pid" 2>/dev/null || true)
check "child pid was recorded" test -n "$childp"
check "orphan child is dead" wait_dead "$childp"
check "lock released after the batch" test ! -e "$H/genseo/state/daily.lock"

echo
printf '%s passed, %s failed\n' "$PASS" "$FAIL"
[ "$FAIL" = 0 ]

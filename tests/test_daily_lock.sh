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
    done < <(find "$TMP" -type f \( -name 'child.pid' -o -name 'sleeper.pid' -o -name 'runner.pid' -o -name 'grand.pid' -o -name 'mid.pid' -o -name 'bash.pid' \) 2>/dev/null)
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
# bash 3.2 has no BASHPID, and the lock scan runs two $(...) deep. A one-level
# parent check treats that grandchild fork as another daily batch.
grandf="$TMP/grand.pid"
rm -f "$grandf"
sh -c 'sleep 40 & echo $! > "$1"; wait' _ "$grandf" &
holder=$!
track "$holder"
check "grandchild pid appeared" wait_file "$grandf"
grand=$(tr -cd '0-9' < "$grandf")
track "$grand"
check "grandchild fork is this shell" genseo_pid_in_this_shell "$grand"
check "init is not this shell" not genseo_pid_in_this_shell 1
kill -KILL "$grand" "$holder" 2>/dev/null || true
wait "$holder" 2>/dev/null || true

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
check "syntax network wait" bash -n "$ROOT/scripts/genseo_wait_for_network.sh"
check "calls group timeout" grep -q 'genseo_group_timeout.sh' "$ROOT/deploy/grokbot-genseo-daily.sh"
check "acquires pid lock" grep -q 'genseo_daily_lock_acquire' "$ROOT/deploy/grokbot-genseo-daily.sh"
check "ticket line is not perl alarm" not grep -q 'alarm .*run_ticket_headless' "$ROOT/deploy/grokbot-genseo-daily.sh"
check "cap does not arm alarm" not grep -q 'alarm $secs' "$ROOT/scripts/genseo_group_timeout.sh"
check "low-water is after the lane lock and before a ticket" awk '
  /^[[:space:]]*#/ { next }
  /genseo_daily_lock_acquire/ && !lock { lock=NR }
  /genseo_queue_low_water \|\|/ && !low { low=NR }
  /run_ticket_headless\.sh/ && !ticket { ticket=NR }
  END { exit !(lock && low && ticket && lock < low && low < ticket) }
' "$ROOT/deploy/grokbot-genseo-daily.sh"

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
check "success path has no perl comma warning" not grep -q "Possible attempt to separate words with commas" "$TMP/exit3.err"
check "success path has no unreachable-statement warning" not grep -q "unlikely to be reached" "$TMP/exit3.err"

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
check "timeout stderr has no perl comma warning" not grep -q "Possible attempt to separate words with commas" "$TMP/to.err"
check "timeout stderr has no unreachable-statement warning" not grep -q "unlikely to be reached" "$TMP/to.err"
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

echo "21. cap kills a TERM-ignoring grandchild that left the group and blocked in connect"
# The session leader's process group is not the whole tree. Claude (and a worker
# it spawned) calls setsid; kill -$leader misses that pid. It is reparented to
# init and stays in connect (SYN_SENT). The waiter must still return, and that
# pid must be dead, within cap + grace.
treedir="$TMP/tree21"
mkdir -p "$treedir"
tree="$TMP/tree-connect.sh"
cat > "$tree" << 'EOF'
#!/bin/bash
d=$1
printf '%s\n' "$$" > "$d/bash.pid"
perl -e '
use POSIX qw(setsid);
use Socket;
my ($grandf, $midf) = @ARGV;
my $pid = fork();
die "fork\n" unless defined $pid;
if ($pid == 0) {
  setsid() or die "setsid\n";
  $SIG{TERM} = "IGNORE";
  $SIG{HUP} = "IGNORE";
  $SIG{INT} = "IGNORE";
  open my $f, ">", $grandf or die $!;
  print $f "$$\n";
  close $f;
  socket(my $s, PF_INET, SOCK_STREAM, 0) or die $!;
  my $addr = sockaddr_in(81, inet_aton("192.0.2.1"));
  connect($s, $addr);
  sleep 120;
  exit 0;
}
$SIG{TERM} = "IGNORE";
$SIG{HUP} = "IGNORE";
$SIG{INT} = "IGNORE";
open my $f, ">", $midf or die $!;
print $f "$$\n";
close $f;
waitpid($pid, 0);
' "$d/grand.pid" "$d/mid.pid" &
wait
EOF
chmod +x "$tree"
sleep 30 >/dev/null &
sib=$!
track "$sib"
t0=$(date +%s)
GENSEO_TIMEOUT_GRACE_SEC=1 /bin/bash "$ROOT/scripts/genseo_group_timeout.sh" 2 /bin/bash "$tree" "$treedir" >"$TMP/tree.out" 2>"$TMP/tree.err" &
tp=$!
track "$tp"
check "grandchild pid appeared" wait_file "$treedir/grand.pid"
check "session leader pid appeared" wait_file "$treedir/bash.pid"
check "middle pid appeared" wait_file "$treedir/mid.pid"
grand=$(tr -cd '0-9' < "$treedir/grand.pid")
leader=$(tr -cd '0-9' < "$treedir/bash.pid")
midp=$(tr -cd '0-9' < "$treedir/mid.pid")
gpgid=$(ps -o pgid= -p "$grand" 2>/dev/null | tr -d '[:space:]')
lpgid=$(ps -o pgid= -p "$leader" 2>/dev/null | tr -d '[:space:]')
check "grandchild left the ticket process group" test -n "$gpgid" -a -n "$lpgid" -a "$gpgid" != "$lpgid"
# Bound the waiter. A hang in blocking waitpid must fail this case, not the suite.
(
  sleep 12
  kill -KILL "$tp" 2>/dev/null || true
) &
guard=$!
track "$guard"
wait "$tp"
RC=$?
kill -KILL "$guard" 2>/dev/null || true
wait "$guard" 2>/dev/null || true
t1=$(date +%s)
check "timeout exit 124" test "$RC" = 124
check "returned within cap + grace" test $((t1 - t0)) -le 8
check "did not return before the cap" test $((t1 - t0)) -ge 2
check "stderr names the group" grep -q "signaling process group" "$TMP/tree.err"
check "TERM-ignoring grandchild is dead" wait_dead "$grand"
check "TERM-ignoring middle process is dead" wait_dead "$midp"
check "session leader is dead" wait_dead "$leader"
check "sibling outside the tree survived" kill -0 "$sib"
kill -KILL "$sib" 2>/dev/null || true
wait "$sib" 2>/dev/null || true

sandbox() {
  H="$TMP/wrap-$1"
  local sc="$H/genseo/scripts"
  mkdir -p "$sc" "$H/genseo/state" "$H/genseo/logs/daily"
  cp "$ROOT/scripts/genseo_daily_lock.sh" "$sc/genseo_daily_lock.sh"
  cp "$ROOT/scripts/genseo_group_timeout.sh" "$sc/genseo_group_timeout.sh"
  cp "$ROOT/scripts/genseo_wait_for_network.sh" "$sc/genseo_wait_for_network.sh"
  cat > "$sc/genseo_published_today.py" << 'PY'
import os, sys
root = os.path.join(os.environ["HOME"], "genseo")
state = os.path.join(root, "state")
if "--json" in sys.argv:
    print('{"entries":[]}')
    raise SystemExit(0)
if "--peer-active" in sys.argv:
    peer = os.path.join(state, "peer-rc")
    if os.path.isfile(peer):
        raw = open(peer).read().strip() or "0"
        try:
            code = int(raw)
        except ValueError:
            code = 0
        if code == 3:
            print("peer-active: fixture")
        else:
            print("peer-idle")
        raise SystemExit(code)
    raise SystemExit(0)
seq = os.path.join(state, "live-seq")
if os.path.isfile(seq):
    lines = [ln.strip() for ln in open(seq) if ln.strip() != ""]
    if not lines:
        lines = ["-1"]
    idx_path = os.path.join(state, "live-seq.idx")
    idx = 0
    if os.path.isfile(idx_path):
        try:
            idx = int(open(idx_path).read().strip() or "0")
        except ValueError:
            idx = 0
    val = lines[idx] if idx < len(lines) else lines[-1]
    open(idx_path, "w").write(str(idx + 1))
    print(val)
    raise SystemExit(0)
print(open(os.path.join(state, "live-count")).read().strip())
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
      GENSEO_NO_DELAY="${WRAP_NO_DELAY:-1}" \
      GENSEO_STANDBY_DELAY_MIN="${WRAP_DELAY_MIN:-20}" \
      GENSEO_HOST_ROLE="${WRAP_ROLE:-primary}" \
      GENSEO_TICKET_PREFIX="${WRAP_PREFIX-}" \
      GENSEO_AUTO_REFILL="${WRAP_REFILL:-0}" \
      GENSEO_QUEUE_LOW_WATER="${WRAP_LOW_WATER-}" \
      GENSEO_LIVE_FEED_RETRIES="${WRAP_FEED_RETRIES:-3}" \
      GENSEO_LIVE_FEED_BACKOFF_SEC="${WRAP_FEED_BACKOFF:-0}" \
      GENSEO_NET_WAIT_MAX_SEC="${WRAP_NET_WAIT:-0}" \
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
check "did not log queue low" not grep -q "QUEUE LOW" "$H/out.log"
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

echo "20. real wrapper: dead PID while a sibling wrapper is alive — do not steal"
sandbox sibling
if ! start_wrapper_sleeper; then echo "wrapper sleeper failed"; exit 1; fi
mkdir "$H/genseo/state/daily.lock"
printf '%s\n' 99999999 > "$H/genseo/state/daily.lock/pid"
printf '%s\n' 0 > "$H/genseo/state/live-count"
run_wrapper 15
check "exit 0" test "$RC" = 0
check "logged another batch" grep -q "another batch is running" "$H/out.log"
check "did not take over" not grep -q "taking over" "$H/out.log"
check "did not start a batch" not grep -q "start (target" "$H/out.log"
check "dead pid left" test "$(tr -cd '0-9' < "$H/genseo/state/daily.lock/pid")" = 99999999
check "sleeper still alive" kill -0 "$SLEEPER"
check "lock still held" test -d "$H/genseo/state/daily.lock"
stop_sleeper

echo "22. real wrapper: setsid connect-hang is a no-publish, the tree dies, the lock is released"
sandbox treewrap
printf '%s\n' 0 > "$H/genseo/state/live-count"
printf '%s\n' '- [ ] **#901** tree timeout' > "$H/genseo/daily-tickets.md"
cat > "$H/genseo/scripts/run_ticket_headless.sh" << 'EOF'
#!/bin/bash
state="$HOME/genseo/state"
printf '%s\n' "$$" > "$state/bash.pid"
perl -e '
use POSIX qw(setsid);
use Socket;
my ($grandf, $midf) = @ARGV;
my $pid = fork();
die "fork\n" unless defined $pid;
if ($pid == 0) {
  setsid() or die "setsid\n";
  $SIG{TERM} = "IGNORE";
  $SIG{HUP} = "IGNORE";
  $SIG{INT} = "IGNORE";
  open my $f, ">", $grandf or die $!;
  print $f "$$\n";
  close $f;
  socket(my $s, PF_INET, SOCK_STREAM, 0) or die $!;
  my $addr = sockaddr_in(81, inet_aton("192.0.2.1"));
  connect($s, $addr);
  sleep 120;
  exit 0;
}
$SIG{TERM} = "IGNORE";
$SIG{HUP} = "IGNORE";
$SIG{INT} = "IGNORE";
open my $f, ">", $midf or die $!;
print $f "$$\n";
close $f;
waitpid($pid, 0);
' "$state/grand.pid" "$state/mid.pid" &
wait
EOF
WRAP_TARGET=5
WRAP_MAX_RUNS=1
WRAP_PEER_WAITS=0
WRAP_TICKET_TIMEOUT=1
WRAP_GRACE=1
run_wrapper 20
check "wrapper exit 0" test "$RC" = 0
check "logged timeout 124" grep -q "exit 124" "$H/out.log"
check "stdout counts a timeout" grep -q "TIMEOUT" "$H/out.log"
check "stderr names the group" grep -q "signaling process group" "$H/err.log"
daylog=$(ls "$H/genseo/logs/daily/"*.log 2>/dev/null | head -1)
check "daily log has the timeout line" grep -q "signaling process group" "$daylog"
check "daily log counts it as no publish" grep -q "nothing new went live" "$daylog"
grand=$(tr -cd '0-9' < "$H/genseo/state/grand.pid" 2>/dev/null || true)
midp=$(tr -cd '0-9' < "$H/genseo/state/mid.pid" 2>/dev/null || true)
check "grandchild pid was recorded" test -n "$grand"
check "setsid grandchild is dead" wait_dead "$grand"
check "middle process is dead" wait_dead "$midp"
check "lock released after the timeout" test ! -e "$H/genseo/state/daily.lock"

echo "23. real wrapper: sleep-forever child that ignores SIGTERM is killed and the lock is released"
# Image retries sleep inside the ticket tree (5s, then 15s). A hang that ignores
# TERM — the backoff process, or a setsid grandchild blocked in sleep — has to
# die on KILL, and the wrapper's EXIT trap has to drop state/daily.lock.
sandbox sleepforever
printf '%s\n' 0 > "$H/genseo/state/live-count"
printf '%s\n' '- [ ] **#902** sleep forever' > "$H/genseo/daily-tickets.md"
cat > "$H/genseo/scripts/run_ticket_headless.sh" << 'EOF'
#!/bin/bash
state="$HOME/genseo/state"
printf '%s\n' "$$" > "$state/bash.pid"
perl -e '
use POSIX qw(setsid);
my ($grandf, $midf) = @ARGV;
my $pid = fork();
die "fork\n" unless defined $pid;
if ($pid == 0) {
  setsid() or die "setsid\n";
  $SIG{TERM} = "IGNORE";
  $SIG{HUP} = "IGNORE";
  $SIG{INT} = "IGNORE";
  open my $f, ">", $grandf or die $!;
  print $f "$$\n";
  close $f;
  while (1) { sleep 30; }
  exit 0;
}
$SIG{TERM} = "IGNORE";
$SIG{HUP} = "IGNORE";
$SIG{INT} = "IGNORE";
open my $f, ">", $midf or die $!;
print $f "$$\n";
close $f;
while (1) { sleep 30; }
' "$state/grand.pid" "$state/mid.pid" &
wait
EOF
WRAP_TARGET=5
WRAP_MAX_RUNS=1
WRAP_PEER_WAITS=0
WRAP_TICKET_TIMEOUT=1
WRAP_GRACE=1
run_wrapper 20
check "wrapper exit 0" test "$RC" = 0
check "logged timeout 124" grep -q "exit 124" "$H/out.log"
check "stdout counts a timeout" grep -q "TIMEOUT" "$H/out.log"
check "stderr names the group" grep -q "signaling process group" "$H/err.log"
daylog=$(ls "$H/genseo/logs/daily/"*.log 2>/dev/null | head -1)
check "daily log has the timeout line" grep -q "signaling process group" "$daylog"
check "daily log counts it as no publish" grep -q "nothing new went live" "$daylog"
leader=$(tr -cd '0-9' < "$H/genseo/state/bash.pid" 2>/dev/null || true)
grand=$(tr -cd '0-9' < "$H/genseo/state/grand.pid" 2>/dev/null || true)
midp=$(tr -cd '0-9' < "$H/genseo/state/mid.pid" 2>/dev/null || true)
check "session leader pid was recorded" test -n "$leader"
check "grandchild pid was recorded" test -n "$grand"
check "middle pid was recorded" test -n "$midp"
check "session leader is dead" wait_dead "$leader"
check "sleep-forever grandchild is dead" wait_dead "$grand"
check "sleep-forever middle process is dead" wait_dead "$midp"
check "lock released after the sleeper timeout" test ! -e "$H/genseo/state/daily.lock"

# The start line calls live_count once before the loop, so a live-seq fixture
# must include that banner read. Backoff is 0 here so the suite stays offline
# and does not sleep.
reset_wrap() {
  WRAP_TARGET=5
  WRAP_MAX_RUNS=1
  WRAP_PEER_WAITS=0
  WRAP_TICKET_TIMEOUT=5400
  WRAP_GRACE=0
  WRAP_NO_DELAY=1
  WRAP_DELAY_MIN=20
  WRAP_ROLE=primary
  unset WRAP_PREFIX
  WRAP_REFILL=0
  unset WRAP_LOW_WATER
  WRAP_FEED_RETRIES=3
  WRAP_FEED_BACKOFF=0
  WRAP_NET_WAIT=0
}
retry_lines() { grep -c 'live feed unreadable — retry ' "$H/out.log" || true; }

echo "24. macbook plist is primary with MB prefix; standby remains opt-in"
plist="$ROOT/deploy/com.pati.genseo-daily.macbook.plist"
check "macbook role is primary" grep -q '<key>GENSEO_HOST_ROLE</key><string>primary</string>' "$plist"
check "macbook prefix is MB" grep -q '<key>GENSEO_TICKET_PREFIX</key><string>MB</string>' "$plist"
check "macbook stays no-face" grep -q '<key>GENSEO_NO_FACE</key><string>1</string>' "$plist"
check "role key is not standby" not grep -q '<key>GENSEO_HOST_ROLE</key><string>standby</string>' "$plist"
check "standby delay remains in the wrapper" grep -q 'ROLE" = "standby"' "$ROOT/deploy/grokbot-genseo-daily.sh"
check "default feed retries is 3" grep -q 'GENSEO_LIVE_FEED_RETRIES:-3' "$ROOT/deploy/grokbot-genseo-daily.sh"
check "default feed backoff is 5" grep -q 'GENSEO_LIVE_FEED_BACKOFF_SEC:-5' "$ROOT/deploy/grokbot-genseo-daily.sh"
check "retry cap is 5" grep -q 'LIVE_FEED_RETRIES" -gt 5' "$ROOT/deploy/grokbot-genseo-daily.sh"
check "runbook says pulling alone is not enough" grep -q 'Pulling alone is not enough' "$ROOT/DAILY-RUN.md"
check "runbook names the wrapper installer" grep -q 'bash scripts/install_mac_daily_wrapper.sh' "$ROOT/DAILY-RUN.md"

echo "25. unreadable feed with retries 0 fail-closes and does not call the peer guard"
reset_wrap
sandbox feed0
printf '%s\n' '-1' '-1' >"$H/genseo/state/live-seq"
printf '%s\n' 3 >"$H/genseo/state/peer-rc"
WRAP_FEED_RETRIES=0
run_wrapper 15
check "exit 1" test "$RC" = 1
check "logged fail closed" grep -q "live feed unreadable — fail closed, exit" "$H/out.log"
check "no retry line" test "$(retry_lines)" = 0
check "did not reach a ticket" not grep -q "run 1:" "$H/out.log"
# banner + one loop read = 2. peer-rc is never consumed because we exit first.
check "banner plus one loop read" test "$(tr -cd '0-9' < "$H/genseo/state/live-seq.idx")" = 2
check "still no peer-active log" not grep -q "peer-active" "$H/out.log"

echo "26. unreadable feed retries the cap, then fail-closes"
reset_wrap
sandbox feedcap
i=0
: >"$H/genseo/state/live-seq"
while [ "$i" -lt 12 ]; do
  printf '%s\n' '-1' >>"$H/genseo/state/live-seq"
  i=$((i + 1))
done
printf '%s\n' 3 >"$H/genseo/state/peer-rc"
WRAP_FEED_RETRIES=9
run_wrapper 15
check "exit 1" test "$RC" = 1
check "logged fail closed" grep -q "live feed unreadable — fail closed, exit" "$H/out.log"
check "capped at 5 retries" test "$(retry_lines)" = 5
check "banner plus six loop reads" test "$(tr -cd '0-9' < "$H/genseo/state/live-seq.idx")" = 7
check "did not stand down for a peer" not grep -q "peer-active" "$H/out.log"
check "did not start a ticket" not grep -q "run 1:" "$H/out.log"

echo "27. unreadable feed that recovers continues; a readable count does not retry"
reset_wrap
sandbox feedok
printf '%s\n' '-1' '-1' '5' >"$H/genseo/state/live-seq"
WRAP_FEED_RETRIES=3
run_wrapper 15
check "exit 0" test "$RC" = 0
check "logged one retry" test "$(retry_lines)" = 1
check "reached DONE" grep -q "DONE:" "$H/out.log"
check "did not fail closed" not grep -q "fail closed" "$H/out.log"

reset_wrap
sandbox readable
printf '%s\n' 0 >"$H/genseo/state/live-count"
printf '%s\n' 3 >"$H/genseo/state/peer-rc"
run_wrapper 15
check "peer stand-down exit 0" test "$RC" = 0
check "readable path logged the peer" grep -q "peer-active: fixture" "$H/out.log"
check "stood down" grep -q "standing down" "$H/out.log"
check "readable path did not retry" test "$(retry_lines)" = 0
check "readable path did not fail closed" not grep -q "fail closed" "$H/out.log"
check "did not start a ticket while the peer was active" not grep -q "run 1:" "$H/out.log"

echo "28. primary does not wait; standby still waits; prefix follows role unless set"
reset_wrap
sandbox primary
printf '%s\n' 5 >"$H/genseo/state/live-count"
WRAP_ROLE=primary
WRAP_NO_DELAY=0
WRAP_DELAY_MIN=20
run_wrapper 15
check "primary exit 0" test "$RC" = 0
check "primary reached DONE" grep -q "DONE:" "$H/out.log"
check "primary did not log standby" not grep -q "standby: waiting" "$H/out.log"

reset_wrap
sandbox standby
printf '%s\n' 5 >"$H/genseo/state/live-count"
WRAP_ROLE=standby
WRAP_NO_DELAY=0
WRAP_DELAY_MIN=0
run_wrapper 15
check "standby exit 0" test "$RC" = 0
check "standby logged the wait" grep -q "standby: waiting 0 min" "$H/out.log"
check "standby reached DONE" grep -q "DONE:" "$H/out.log"

reset_wrap
sandbox prefixmm
printf '%s\n' 0 >"$H/genseo/state/live-count"
WRAP_ROLE=primary
unset WRAP_PREFIX
WRAP_REFILL=1
run_wrapper 15
check "primary fallback exit 0" test "$RC" = 0
check "unset prefix on primary is MM" grep -q "prefix MM" "$H/out.log"
check "primary fallback is not MB" not grep -q "prefix MB" "$H/out.log"

reset_wrap
sandbox prefixmb
printf '%s\n' 0 >"$H/genseo/state/live-count"
WRAP_ROLE=standby
unset WRAP_PREFIX
WRAP_REFILL=1
WRAP_NO_DELAY=1
run_wrapper 15
check "standby prefix exit 0" test "$RC" = 0
check "unset prefix on standby is MB" grep -q "prefix MB" "$H/out.log"
check "standby fallback is not MM" not grep -q "prefix MM" "$H/out.log"

reset_wrap
sandbox prefixset
printf '%s\n' 0 >"$H/genseo/state/live-count"
WRAP_ROLE=primary
WRAP_PREFIX=MB
WRAP_REFILL=1
run_wrapper 15
check "explicit MB exit 0" test "$RC" = 0
check "explicit prefix MB wins on primary" grep -q "prefix MB" "$H/out.log"
check "explicit MB is not MM" not grep -q "prefix MM" "$H/out.log"

echo "29. low-water refills a finished day up to two days of target, then is a no-op"
reset_wrap
sandbox lowfill
printf '%s\n' 5 >"$H/genseo/state/live-count"
cat >"$H/genseo/scripts/refill_tickets.py" <<'PY'
import os, sys
root = os.path.join(os.environ["HOME"], "genseo")
open(os.path.join(root, "state", "refill-args"), "w").write(" ".join(sys.argv[1:]))
args = sys.argv[1:]
count = 0
if "--count" in args:
    count = int(args[args.index("--count") + 1])
rc_path = os.path.join(root, "state", "refill-rc")
if os.path.isfile(rc_path):
    raise SystemExit(int(open(rc_path).read().strip() or "0"))
queue = os.path.join(root, "daily-tickets.md")
with open(queue, "a", encoding="utf-8") as fh:
    for i in range(1, count + 1):
        fh.write("- [ ] **#T%d** low water\n" % i)
raise SystemExit(0)
PY
run_wrapper 20
check "refill exit 0" test "$RC" = 0
check "logged QUEUE LOW" grep -q "QUEUE LOW:" "$H/out.log"
check "reached DONE after the refill" grep -q "DONE:" "$H/out.log"
check "args ask for the threshold" grep -q -- "--if-below 10" "$H/genseo/state/refill-args"
check "args ask for the shortfall" grep -q -- "--count 10" "$H/genseo/state/refill-args"
check "args carry a prefix" grep -q -- "--prefix" "$H/genseo/state/refill-args"
check "args are not offline" not grep -q -- "--offline" "$H/genseo/state/refill-args"
check "ten open lines were appended" test "$(grep -cE '^(- \[ \]|## \[ \])' "$H/genseo/daily-tickets.md")" = 10
rm -f "$H/genseo/state/refill-args"
run_wrapper 20
check "second run exit 0" test "$RC" = 0
check "second run sees the runway" grep -q "queue low-water: 10 open ticket(s) >= 10" "$H/out.log"
check "second run did not call refill" test ! -e "$H/genseo/state/refill-args"

echo "30. a short bank writes the marker and does not start a ticket"
reset_wrap
sandbox lowdry
printf '%s\n' 0 >"$H/genseo/state/live-count"
printf '%s\n' 3 >"$H/genseo/state/refill-rc"
cp "$TMP/wrap-lowfill/genseo/scripts/refill_tickets.py" "$H/genseo/scripts/refill_tickets.py"
run_wrapper 20
check "short bank exit 0" test "$RC" = 0
check "logged refill exit 3" grep -q "refill exit 3" "$H/out.log"
check "marker names exit 3" grep -q "exit=3" "$H/genseo/state/queue-low-water.marker"
check "marker says no paid api" grep -q "paid_api=not called" "$H/genseo/state/queue-low-water.marker"
check "short bank did not start a ticket" not grep -q "run 1:" "$H/out.log"
check "short bank left the queue empty" test ! -s "$H/genseo/daily-tickets.md"

echo "31. low-water 0 keeps the empty-queue hard stop and writes no marker"
reset_wrap
sandbox lowoff
printf '%s\n' 0 >"$H/genseo/state/live-count"
WRAP_LOW_WATER=0
run_wrapper 15
check "disabled guard exit 0" test "$RC" = 0
check "disabled guard did not log QUEUE LOW" not grep -q "QUEUE LOW" "$H/out.log"
check "disabled guard wrote no marker" test ! -e "$H/genseo/state/queue-low-water.marker"
check "disabled guard hard-stopped" grep -q "ticket queue EMPTY" "$H/out.log"

echo "32. a stocked queue does not call refill"
reset_wrap
sandbox lowstock
printf '%s\n' 5 >"$H/genseo/state/live-count"
i=0
while [ "$i" -lt 10 ]; do
  i=$((i + 1))
  printf '%s\n' "- [ ] **#P$i** seeded" >>"$H/genseo/daily-tickets.md"
done
run_wrapper 15
check "stocked exit 0" test "$RC" = 0
check "stocked queue is at the threshold" grep -q ">= 10" "$H/out.log"
check "stocked queue wrote no args" test ! -e "$H/genseo/state/refill-args"
check "stocked queue cleared no marker by calling refill" test ! -e "$H/genseo/state/queue-low-water.marker"

echo
printf '%s passed, %s failed\n' "$PASS" "$FAIL"
[ "$FAIL" = 0 ]

#!/bin/bash
# Idle-sleep and dark-wake guards for the scheduled article and landing runs.
# No Shopify, no launchd, no pmset, no sudo. Bash 3.2 safe.
#   bash tests/test_power_assert.sh
#
# Proves: caffeinate -i -s -w <this-pid> is armed once and survives exec;
# a missing or instant caffeinate does not stop the run; a retry that finds
# the lane lock or a finished day does not start a ticket or a landing build;
# the plists add the check slot and keep RunAtLoad false.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HELPER="$ROOT/scripts/genseo_power_assert.sh"
ARTICLE="$ROOT/deploy/grokbot-genseo-daily.sh"
LANDING="$ROOT/scripts/run_landing_daily.sh"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/power-assert.XXXXXX")" || exit 1
PIDS=""
PASS=0
FAIL=0
RC=0

cleanup() {
  local p
  for p in $PIDS; do
    kill -KILL "$p" 2>/dev/null || true
    wait "$p" 2>/dev/null || true
  done
  if [ -n "${WORK:-}" ] && [ -d "$WORK" ]; then
    if [ -f "$WORK/caff-pids" ]; then
      while IFS= read -r p; do
        case "$p" in
          ''|*[!0-9]*) continue ;;
        esac
        kill -KILL "$p" 2>/dev/null || true
        wait "$p" 2>/dev/null || true
      done <"$WORK/caff-pids"
    fi
  fi
  rm -rf "$WORK"
}
trap cleanup EXIT

ok() { PASS=$((PASS + 1)); printf '  ok   %s\n' "$*"; }
bad() { FAIL=$((FAIL + 1)); printf '  FAIL %s\n' "$*"; }

show() {
  printf '    stdout: %s\n' "$(tr '\n' '|' <"$WORK/out" 2>/dev/null || true)"
  printf '    stderr: %s\n' "$(tr '\n' '|' <"$WORK/err" 2>/dev/null || true)"
  if [ -f "$WORK/caff.log" ]; then
    printf '    caff: %s\n' "$(tr '\n' '|' <"$WORK/caff.log")"
  fi
}

assert_rc() {
  if [ "$RC" = "$1" ]; then ok "$2"
  else bad "$2 (rc $RC, want $1)"; show; fi
}

has() {
  if grep -F -q -- "$2" "$1"; then ok "$3"
  else bad "$3"; show; fi
}

lacks() {
  if grep -F -q -- "$2" "$1"; then bad "$3"; show
  else ok "$3"; fi
}

track() { PIDS="$PIDS $1"; }

wait_dead() {
  local p=$1 i
  for i in $(seq 1 40); do
    kill -0 "$p" 2>/dev/null || return 0
    sleep 0.05
  done
  return 1
}

bounded() {
  local t=$1 pid watch
  shift
  "$@" &
  pid=$!
  (
    sleep "$t"
    kill -TERM "$pid" 2>/dev/null || true
  ) &
  watch=$!
  wait "$pid"
  RC=$?
  kill -TERM "$watch" 2>/dev/null || true
  wait "$watch" 2>/dev/null || true
}

order_code() {
  local file=$1 early=$2 late=$3 label=$4
  if awk -v early="$early" -v late="$late" '
    /^[[:space:]]*#/ { next }
    index($0, early) && !e { e=NR }
    index($0, late) && !l { l=NR }
    END { exit !(e && l && e < l) }
  ' "$file"; then
    ok "$label"
  else
    bad "$label"
  fi
}

code_lacks() {
  local file=$1 word=$2 label=$3
  if awk -v word="$word" '
    /^[[:space:]]*#/ { next }
    index($0, word) { found=1 }
    END { exit found+0 }
  ' "$file"; then
    ok "$label"
  else
    bad "$label"
  fi
}

cat >"$WORK/bin-caffeinate" <<'EOF'
#!/bin/bash
log=${GENSEO_CAFFEINATE_LOG:?}
printf '%s\n' "$*" >>"$log"
mode=${GENSEO_CAFFEINATE_MODE:-wait}
if [ "$mode" = exit ]; then
  exit 0
fi
target=""
prev=""
for arg in "$@"; do
  if [ "$prev" = "-w" ]; then
    target=$arg
  fi
  prev=$arg
done
printf '%s\n' "$$" >>"${GENSEO_CAFFEINATE_PIDS:?}"
if [ -z "$target" ]; then
  exit 0
fi
i=0
while kill -0 "$target" 2>/dev/null; do
  i=$((i + 1))
  if [ "$i" -gt 400 ]; then
    exit 0
  fi
  sleep 0.05
done
exit 0
EOF
chmod 755 "$WORK/bin-caffeinate"
: >"$WORK/caff.log"
: >"$WORK/caff-pids"

reset_caff() {
  : >"$WORK/caff.log"
  : >"$WORK/caff-pids"
  : >"$WORK/out"
  : >"$WORK/err"
}

echo "1. syntax, direct exec, and the assertion is armed before the DNS wait"
bash -n "$HELPER" && ok "bash -n helper" || bad "bash -n helper"
bash -n "$ARTICLE" && ok "bash -n article wrapper" || bad "bash -n article wrapper"
bash -n "$LANDING" && ok "bash -n landing wrapper" || bad "bash -n landing wrapper"
bash -n "$ROOT/scripts/install_mac_daily_wrapper.sh" && ok "bash -n installer" || bad "bash -n installer"
reset_caff
bounded 5 /bin/bash "$HELPER" >"$WORK/out" 2>"$WORK/err"
assert_rc 2 "direct exec refuses"
lacks "$WORK/out" "power assertion:" "direct exec does not arm"
code_lacks "$HELPER" "sudo" "helper code has no sudo"
code_lacks "$HELPER" "pmset" "helper code has no pmset"
code_lacks "$HELPER" "shopify_publisher" "helper code does not publish"
code_lacks "$ARTICLE" "sudo" "article wrapper code has no sudo"
code_lacks "$ARTICLE" "pmset" "article wrapper code has no pmset"
code_lacks "$LANDING" "--live" "landing wrapper code has no --live"
order_code "$ARTICLE" "genseo_power_assert_arm" "genseo_exec_stable_copy grokbot-genseo-daily" "article arms before the stable copy"
order_code "$ARTICLE" "genseo_power_assert_arm" "genseo_wait_for_network" "article arms before the DNS wait"
order_code "$ARTICLE" "genseo_power_assert_note" "genseo_daily_lock_acquire" "article logs the assertion before the lock"
order_code "$ARTICLE" "genseo_wait_for_network;" '$(live_count)' "article DNS wait stays before the first live count"
order_code "$LANDING" "genseo_power_assert_arm" "genseo_exec_stable_copy run_landing_daily" "landing arms before the stable copy"
order_code "$LANDING" "genseo_power_assert_arm" "genseo_wait_for_network" "landing arms before the DNS wait"
order_code "$LANDING" "genseo_power_assert_note" 'mkdir "$LOCK"' "landing logs the assertion before its lock"
grep -F -q 'GENSEO_DAILY_TARGET:-5' "$ARTICLE" && ok "article target default stays 5" || bad "article target default changed"
grep -F -q 'GENSEO_LANDING_DRAFT=1' "$LANDING" && ok "landing stays draft-only" || bad "landing draft env missing"
grep -F -q '/bin/bash "$G/scripts/run_ticket_headless.sh"' "$ARTICLE" && ok "article still runs one ticket at a time" || bad "article ticket runner missing"

echo "2. one caffeinate -i -s -w of this pid, including across exec"
reset_caff
cat >"$WORK/reexec.sh" <<'EOF'
#!/bin/bash
set -uo pipefail
. "$GENSEO_POWER_HELPER"
genseo_power_assert_arm || true
genseo_power_assert_arm || true
if [ "${STAGE:-}" != 2 ]; then
  export STAGE=2
  exec /bin/bash "$0"
fi
say() { printf '%s\n' "$*"; }
genseo_power_assert_note || true
printf 'wrapper_pid:%s\n' "$$"
sleep 0.3
EOF
chmod 755 "$WORK/reexec.sh"
bounded 15 env -i \
  PATH="/usr/bin:/bin" \
  GENSEO_POWER_ASSERT_TEST=1 \
  GENSEO_CAFFEINATE="$WORK/bin-caffeinate" \
  GENSEO_CAFFEINATE_LOG="$WORK/caff.log" \
  GENSEO_CAFFEINATE_PIDS="$WORK/caff-pids" \
  GENSEO_CAFFEINATE_MODE=wait \
  GENSEO_POWER_HELPER="$HELPER" \
  /bin/bash "$WORK/reexec.sh" >"$WORK/out" 2>"$WORK/err"
assert_rc 0 "re-exec fixture exits 0"
has "$WORK/out" "power assertion: caffeinate -i -s -w" "logs the assertion"
lines=$(grep -c . "$WORK/caff.log" || true)
[ "$lines" = 1 ] && ok "caffeinate spawned once across a second arm and an exec" || bad "caffeinate lines were $lines, want 1"
wpid=$(sed -n 's/^wrapper_pid://p' "$WORK/out")
cargs=$(head -1 "$WORK/caff.log")
[ "$cargs" = "-i -s -w $wpid" ] && ok "args are -i -s -w of the wrapper pid" || bad "args were [$cargs], wrapper $wpid"
holder=$(head -1 "$WORK/caff-pids")
case "$holder" in
  ''|*[!0-9]*) bad "holder pid missing" ;;
  *)
    if wait_dead "$holder"; then ok "holder exited after the wrapper"
    else bad "holder $holder still running"; track "$holder"; fi
    ;;
esac

echo "3. missing, disabled, and non-test overrides do not spawn and do not stop the caller"
reset_caff
bounded 10 env -i \
  PATH="$WORK:/usr/bin:/bin" \
  GENSEO_POWER_ASSERT_TEST=1 \
  GENSEO_CAFFEINATE="$WORK/no-such-caffeinate" \
  GENSEO_CAFFEINATE_LOG="$WORK/caff.log" \
  GENSEO_CAFFEINATE_PIDS="$WORK/caff-pids" \
  GENSEO_POWER_HELPER="$HELPER" \
  /bin/bash -c '
    set -uo pipefail
    . "$GENSEO_POWER_HELPER"
    genseo_power_assert_arm || true
    say() { printf "%s\n" "$*"; }
    genseo_power_assert_note || true
    printf "continued\n"
  ' >"$WORK/out" 2>"$WORK/err"
assert_rc 0 "missing caffeinate still exits 0"
has "$WORK/out" "continued" "missing caffeinate continues"
has "$WORK/out" "power assertion: not held (caffeinate missing)" "missing caffeinate is logged"
[ ! -s "$WORK/caff.log" ] && ok "missing path was not executed" || bad "missing path was executed"

reset_caff
bounded 10 env -i \
  PATH="/usr/bin:/bin" \
  GENSEO_POWER_ASSERT_TEST=1 \
  GENSEO_POWER_ASSERT_DISABLE=1 \
  GENSEO_CAFFEINATE="$WORK/bin-caffeinate" \
  GENSEO_CAFFEINATE_LOG="$WORK/caff.log" \
  GENSEO_CAFFEINATE_PIDS="$WORK/caff-pids" \
  GENSEO_POWER_HELPER="$HELPER" \
  /bin/bash -c '
    set -uo pipefail
    . "$GENSEO_POWER_HELPER"
    genseo_power_assert_arm || true
    say() { printf "%s\n" "$*"; }
    genseo_power_assert_note || true
    printf "continued\n"
  ' >"$WORK/out" 2>"$WORK/err"
assert_rc 0 "disable still exits 0"
has "$WORK/out" "power assertion: disabled" "disable is logged"
has "$WORK/out" "continued" "disable continues"
[ ! -s "$WORK/caff.log" ] && ok "disable did not spawn" || bad "disable spawned"

reset_caff
bounded 10 env -i \
  PATH="$WORK:/usr/bin:/bin" \
  GENSEO_CAFFEINATE="$WORK/bin-caffeinate" \
  GENSEO_CAFFEINATE_LOG="$WORK/caff.log" \
  GENSEO_CAFFEINATE_PIDS="$WORK/caff-pids" \
  GENSEO_POWER_HELPER="$HELPER" \
  /bin/bash -c '
    set -uo pipefail
    . "$GENSEO_POWER_HELPER"
    genseo_power_assert_arm || true
    say() { printf "%s\n" "$*"; }
    genseo_power_assert_note || true
  ' >"$WORK/out" 2>"$WORK/err"
assert_rc 0 "ignored override exits 0"
has "$WORK/out" "power assertion: not held (caffeinate missing)" "non-test override is ignored"
[ ! -s "$WORK/caff.log" ] && ok "non-test override did not run the fake" || bad "non-test override ran the fake"

echo "4. plists: check slots, caffeinate prefix, RunAtLoad stays false"
plist_ok() {
  local file=$1 args=$2 slots=$3 label=$4
  if /usr/bin/python3 - "$file" "$args" "$slots" <<'PY'
import plistlib, sys
path, want_args, want_slots = sys.argv[1:]
with open(path, "rb") as fh:
    data = plistlib.load(fh)
args = data.get("ProgramArguments")
slots = sorted((int(item["Hour"]), int(item["Minute"])) for item in data["StartCalendarInterval"])
expect_args = want_args.split("|")
expect_slots = []
for part in want_slots.split(","):
    hour, minute = part.split(":")
    expect_slots.append((int(hour), int(minute)))
expect_slots.sort()
if args != expect_args or slots != expect_slots or data.get("RunAtLoad") is not False:
    sys.stderr.write("args=%s slots=%s RunAtLoad=%s\n" % (args, slots, data.get("RunAtLoad")))
    raise SystemExit(1)
PY
  then
    ok "$label"
  else
    bad "$label"
  fi
}
ART_ARGS="/usr/bin/caffeinate|-i|-s|/bin/bash|/Users/kevinkreative/bin/grokbot-genseo-daily.sh"
LAND_ARGS="/usr/bin/caffeinate|-i|-s|/bin/bash|/Users/kevinkreative/genseo/scripts/run_landing_daily.sh"
plist_ok "$ROOT/deploy/com.pati.genseo-daily.macbook.plist" "$ART_ARGS" "7:30,8:05,14:47" "article plist intervals and caffeinate"
plist_ok "$ROOT/deploy/com.pati.genseo-landing.macbook.plist" "$LAND_ARGS" "8:15,9:20,16:15" "macbook landing plist intervals and caffeinate"
plist_ok "$ROOT/deploy/com.pati.genseo-landing.mini.plist" "$LAND_ARGS" "8:15,9:20,16:15" "mini landing plist intervals and caffeinate"
grep -F -q '<key>GENSEO_HOST_ROLE</key><string>primary</string>' "$ROOT/deploy/com.pati.genseo-daily.macbook.plist" \
  && ok "article plist stays primary" || bad "article plist role changed"
grep -F -q '<key>GENSEO_TICKET_PREFIX</key><string>MB</string>' "$ROOT/deploy/com.pati.genseo-daily.macbook.plist" \
  && ok "article plist stays MB" || bad "article plist prefix changed"
grep -F -q '<key>GENSEO_DAILY_TARGET</key><string>5</string>' "$ROOT/deploy/com.pati.genseo-daily.macbook.plist" \
  && ok "article plist target stays 5" || bad "article plist target changed"
grep -F -q '<key>GENSEO_HOST_ROLE</key><string>standby</string>' "$ROOT/deploy/com.pati.genseo-landing.macbook.plist" \
  && ok "macbook landing stays standby" || bad "macbook landing role changed"
grep -F -q '<key>GENSEO_HOST_ROLE</key><string>primary</string>' "$ROOT/deploy/com.pati.genseo-landing.mini.plist" \
  && ok "mini landing stays primary" || bad "mini landing role changed"
grep -F -q '<string>com.pati.genseo-daily</string>' "$ROOT/deploy/com.pati.genseo-daily.macbook.plist" \
  && ok "article label unchanged" || bad "article label changed"
grep -F -q '<string>com.pati.genseo-landing</string>' "$ROOT/deploy/com.pati.genseo-landing.macbook.plist" \
  && ok "landing label unchanged" || bad "landing label changed"

echo "5. article retry exits on a live lock and does not start a ticket"
reset_caff
H="$WORK/home-lock"
sc="$H/genseo/scripts"
mkdir -p "$sc" "$H/genseo/state" "$H/genseo/logs/daily"
cp "$ROOT/scripts/genseo_daily_lock.sh" "$sc/genseo_daily_lock.sh"
cp "$ROOT/scripts/genseo_group_timeout.sh" "$sc/genseo_group_timeout.sh"
cp "$ROOT/scripts/genseo_wait_for_network.sh" "$sc/genseo_wait_for_network.sh"
cp "$HELPER" "$sc/genseo_power_assert.sh"
cat >"$sc/genseo_published_today.py" <<'PY'
import os, sys
root = os.path.join(os.environ["HOME"], "genseo", "state")
open(os.path.join(root, "feed-called"), "a").write("1\n")
if "--json" in sys.argv:
    print('{"entries":[]}')
    raise SystemExit(0)
if "--peer-active" in sys.argv:
    print("peer-idle")
    raise SystemExit(0)
print("5")
PY
cat >"$sc/run_ticket_headless.sh" <<'EOF'
#!/bin/bash
touch "$HOME/genseo/state/ticket-called"
exit 0
EOF
chmod 755 "$sc/run_ticket_headless.sh"
printf '%s\n' '5' >"$H/genseo/state/live-count"
printf '%s\n' '- [ ] **#1** should not run' >"$H/genseo/daily-tickets.md"
sleeper_pidfile="$WORK/sleeper.pid"
rm -f "$sleeper_pidfile"
perl -MPOSIX -e '
  use POSIX qw(setsid);
  my $pid = fork();
  exit 0 if $pid;
  setsid();
  fork() and exit 0;
  open my $fh, ">", shift @ARGV or exit 1;
  print $fh "$$\n";
  close $fh;
  exec @ARGV or exit 1;
' "$sleeper_pidfile" bash -c 'exec -a grokbot-genseo-daily sleep 120' >/dev/null &
starter=$!
wait "$starter" 2>/dev/null || true
i=0
while [ ! -s "$sleeper_pidfile" ] && [ "$i" -lt 50 ]; do
  i=$((i + 1))
  sleep 0.05
done
sleeper=$(tr -cd '0-9' <"$sleeper_pidfile")
track "$sleeper"
mkdir "$H/genseo/state/daily.lock"
printf '%s\n' "$sleeper" >"$H/genseo/state/daily.lock/pid"
bounded 20 env -i \
  HOME="$H" \
  PATH="/usr/bin:/bin" \
  GENSEO_DAILY_TARGET=5 \
  GENSEO_MAX_RUNS=1 \
  GENSEO_NO_DELAY=1 \
  GENSEO_NET_WAIT_MAX_SEC=0 \
  GENSEO_LIVE_FEED_RETRIES=0 \
  GENSEO_POWER_ASSERT_TEST=1 \
  GENSEO_CAFFEINATE="$WORK/bin-caffeinate" \
  GENSEO_CAFFEINATE_LOG="$WORK/caff.log" \
  GENSEO_CAFFEINATE_PIDS="$WORK/caff-pids" \
  GENSEO_CAFFEINATE_MODE=wait \
  /bin/bash "$ARTICLE" >"$WORK/out" 2>"$WORK/err"
assert_rc 0 "locked retry exits 0"
has "$WORK/out" "another batch is running" "locked retry logs the other batch"
has "$WORK/out" "power assertion: caffeinate -i -s -w" "locked retry still armed caffeinate"
lacks "$WORK/out" "start (target" "locked retry does not read the live count"
lacks "$WORK/out" "run 1:" "locked retry does not start a ticket run"
[ ! -e "$H/genseo/state/ticket-called" ] && ok "locked retry did not exec the ticket runner" || bad "locked retry exec'd the ticket runner"
[ ! -e "$H/genseo/state/feed-called" ] && ok "locked retry did not read the feed" || bad "locked retry read the feed"
[ -d "$H/genseo/state/daily.lock" ] && ok "locked retry left the lock" || bad "locked retry removed the lock"
[ "$(tr -cd '0-9' <"$H/genseo/state/daily.lock/pid")" = "$sleeper" ] && ok "locked retry left the owner pid" || bad "locked retry replaced the owner pid"
kill -0 "$sleeper" 2>/dev/null && ok "original batch still alive" || bad "original batch died"
clock=$(grep -c . "$WORK/caff.log" || true)
[ "$clock" = 1 ] && ok "locked retry spawned one caffeinate" || bad "locked retry caffeinate lines were $clock"
lacks "$WORK/out" "shopify_publisher.py" "locked retry does not name the publisher"

echo "6. a finished day is a no-op even if caffeinate exits immediately"
reset_caff
H="$WORK/home-done"
sc="$H/genseo/scripts"
mkdir -p "$sc" "$H/genseo/state" "$H/genseo/logs/daily"
cp "$ROOT/scripts/genseo_daily_lock.sh" "$sc/genseo_daily_lock.sh"
cp "$ROOT/scripts/genseo_group_timeout.sh" "$sc/genseo_group_timeout.sh"
cp "$ROOT/scripts/genseo_wait_for_network.sh" "$sc/genseo_wait_for_network.sh"
cp "$HELPER" "$sc/genseo_power_assert.sh"
cat >"$sc/genseo_published_today.py" <<'PY'
import os, sys
root = os.path.join(os.environ["HOME"], "genseo", "state")
open(os.path.join(root, "feed-called"), "a").write("1\n")
if "--json" in sys.argv:
    print('{"entries":[]}')
    raise SystemExit(0)
if "--peer-active" in sys.argv:
    print("peer-idle")
    raise SystemExit(0)
print("5")
PY
cat >"$sc/run_ticket_headless.sh" <<'EOF'
#!/bin/bash
touch "$HOME/genseo/state/ticket-called"
exit 0
EOF
chmod 755 "$sc/run_ticket_headless.sh"
printf '%s\n' '5' >"$H/genseo/state/live-count"
bounded 20 env -i \
  HOME="$H" \
  PATH="/usr/bin:/bin" \
  GENSEO_DAILY_TARGET=5 \
  GENSEO_MAX_RUNS=1 \
  GENSEO_NO_DELAY=1 \
  GENSEO_NET_WAIT_MAX_SEC=0 \
  GENSEO_LIVE_FEED_RETRIES=0 \
  GENSEO_POWER_ASSERT_TEST=1 \
  GENSEO_CAFFEINATE="$WORK/bin-caffeinate" \
  GENSEO_CAFFEINATE_LOG="$WORK/caff.log" \
  GENSEO_CAFFEINATE_PIDS="$WORK/caff-pids" \
  GENSEO_CAFFEINATE_MODE=exit \
  /bin/bash "$ARTICLE" >"$WORK/out" 2>"$WORK/err"
assert_rc 0 "finished day exits 0"
has "$WORK/out" "DONE:" "finished day reaches DONE"
has "$WORK/out" "network wait skipped" "finished day still passes the DNS wait"
lacks "$WORK/out" "run 1:" "finished day does not start a ticket run"
[ ! -e "$H/genseo/state/ticket-called" ] && ok "finished day did not exec the ticket runner" || bad "finished day exec'd the ticket runner"
[ ! -e "$H/genseo/state/daily.lock" ] && ok "finished day released the lock" || bad "finished day left the lock"
if awk '
  /power assertion:/ { if (!a) a=NR }
  /network wait skipped/ { if (!n) n=NR }
  /DONE:/ { if (!d) d=NR }
  END { exit !(a && n && d && a < n && n < d) }
' "$WORK/out"; then
  ok "assertion, then DNS wait, then DONE"
else
  bad "assertion was not logged before the DNS wait"
  show
fi
grep -q . "$WORK/caff.log" && ok "instant caffeinate was still invoked" || bad "instant caffeinate was not invoked"
grep -q 'did not stay up\|not held' "$WORK/out" && ok "instant caffeinate is not described as held" || bad "instant caffeinate looked held"

echo "7. landing retry stands down when today's draft exists and does not build"
reset_caff
H="$WORK/home-land"
sc="$H/genseo/scripts"
mkdir -p "$sc" "$H/genseo/state" "$H/genseo/logs"
cp "$ROOT/scripts/genseo_group_timeout.sh" "$sc/genseo_group_timeout.sh"
cp "$ROOT/scripts/genseo_wait_for_network.sh" "$sc/genseo_wait_for_network.sh"
cp "$HELPER" "$sc/genseo_power_assert.sh"
printf '%s\n' '3' >"$H/genseo/state/guard-codes"
cat >"$sc/landing_guard.py" <<'PY'
import sys
codes = open("state/guard-codes").read().split()
open("state/guard-codes", "w").write(" ".join(codes[1:]))
print("stub landing_guard: exit", codes[0] if codes else 0)
sys.exit(int(codes[0]) if codes else 0)
PY
cat >"$sc/landing_publisher.py" <<'PY'
import os, sys
open(os.path.join("state", "publisher-called"), "w").write(" ".join(sys.argv))
raise SystemExit(0)
PY
cat >"$sc/run_landing_headless.sh" <<'EOF'
#!/bin/bash
touch "$HOME/genseo/state/agent-called"
exit 0
EOF
chmod 755 "$sc/run_landing_headless.sh"
bounded 20 env -i \
  HOME="$H" \
  PATH="/usr/bin:/bin" \
  GENSEO_HOST_ROLE=primary \
  GENSEO_NO_DELAY=1 \
  GENSEO_NET_WAIT_MAX_SEC=0 \
  GENSEO_POWER_ASSERT_TEST=1 \
  GENSEO_CAFFEINATE="$WORK/bin-caffeinate" \
  GENSEO_CAFFEINATE_LOG="$WORK/caff.log" \
  GENSEO_CAFFEINATE_PIDS="$WORK/caff-pids" \
  GENSEO_CAFFEINATE_MODE=wait \
  /bin/bash "$LANDING" >"$WORK/out" 2>"$WORK/err"
assert_rc 0 "landing stand-down exits 0"
has "$WORK/out" "today's gsl- landing draft already exists" "landing retry stands down"
has "$WORK/out" "power assertion: caffeinate -i -s -w" "landing retry armed caffeinate"
lacks "$WORK/out" "landing_publisher.py" "landing retry does not build a page"
[ ! -e "$H/genseo/state/publisher-called" ] && ok "landing publisher was not executed" || bad "landing publisher ran"
[ ! -e "$H/genseo/state/agent-called" ] && ok "landing agent was not executed" || bad "landing agent ran"
[ ! -e "$H/genseo/state/landing-daily.lock" ] && ok "landing lock released" || bad "landing lock still held"
[ ! -s "$H/genseo/state/guard-codes" ] && ok "guard ran once" || bad "guard was not consumed"
land_lines=$(grep -c . "$WORK/caff.log" || true)
[ "$land_lines" = 1 ] && ok "landing retry spawned one caffeinate" || bad "landing caffeinate lines were $land_lines"
if awk '
  /power assertion:/ { if (!a) a=NR }
  /network wait skipped/ { if (!n) n=NR }
  /gsl- landing draft already exists/ { if (!g) g=NR }
  END { exit !(a && n && g && a < n && n < g) }
' "$WORK/out"; then
  ok "landing assertion, then DNS wait, then stand-down"
else
  bad "landing assertion was not before the DNS wait"
  show
fi

echo "8. a second landing start exits while the first lock is held"
reset_caff
H="$WORK/home-land-lock"
sc="$H/genseo/scripts"
mkdir -p "$sc" "$H/genseo/state" "$H/genseo/logs"
cp "$ROOT/scripts/genseo_group_timeout.sh" "$sc/genseo_group_timeout.sh"
cp "$ROOT/scripts/genseo_wait_for_network.sh" "$sc/genseo_wait_for_network.sh"
cp "$HELPER" "$sc/genseo_power_assert.sh"
printf '%s\n' '0' >"$H/genseo/state/guard-codes"
cat >"$sc/landing_guard.py" <<'PY'
import sys
print("stub landing_guard should not run")
sys.exit(0)
PY
cat >"$sc/landing_publisher.py" <<'PY'
raise SystemExit(0)
PY
mkdir "$H/genseo/state/landing-daily.lock"
# Young lock, no owner the wrapper can steal. path_mtime is now.
bounded 20 env -i \
  HOME="$H" \
  PATH="/usr/bin:/bin" \
  GENSEO_HOST_ROLE=primary \
  GENSEO_NO_DELAY=1 \
  GENSEO_NET_WAIT_MAX_SEC=0 \
  GENSEO_POWER_ASSERT_TEST=1 \
  GENSEO_CAFFEINATE="$WORK/bin-caffeinate" \
  GENSEO_CAFFEINATE_LOG="$WORK/caff.log" \
  GENSEO_CAFFEINATE_PIDS="$WORK/caff-pids" \
  GENSEO_CAFFEINATE_MODE=exit \
  /bin/bash "$LANDING" >"$WORK/out" 2>"$WORK/err"
assert_rc 0 "overlapping landing exits 0"
has "$WORK/out" "another landing run is active" "overlapping landing logs the lock"
lacks "$WORK/out" "stub landing_guard" "overlapping landing does not call the guard"
lacks "$WORK/out" "landing_publisher.py" "overlapping landing does not publish"
[ -d "$H/genseo/state/landing-daily.lock" ] && ok "overlapping landing left the lock" || bad "overlapping landing cleared the lock"

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" = 0 ]

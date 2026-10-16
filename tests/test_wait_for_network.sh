#!/bin/bash
# DNS wait in front of the daily article feed read and the landing Shopify read.
# Linux-runnable. Stubs the resolver. No Shopify, no publish, no launchd.
#   bash tests/test_wait_for_network.sh
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HELPER="$ROOT/scripts/genseo_wait_for_network.sh"
ARTICLE="$ROOT/deploy/grokbot-genseo-daily.sh"
LANDING="$ROOT/scripts/run_landing_daily.sh"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/wait-for-network.XXXXXX")" || exit 1
PASS=0
FAIL=0
RC=0
H=""

cleanup() {
  local p
  for p in $(jobs -p); do
    kill -KILL "$p" 2>/dev/null || true
    wait "$p" 2>/dev/null || true
  done
  rm -rf "$WORK"
}
trap cleanup EXIT

ok() { PASS=$((PASS + 1)); printf '  ok   %s\n' "$*"; }
bad() { FAIL=$((FAIL + 1)); printf '  FAIL %s\n' "$*"; }

show() {
  printf '    rc=%s\n' "$RC"
  if [ -f "$WORK/unit.out" ]; then
    printf '    stdout: %s\n' "$(tr '\n' '|' <"$WORK/unit.out")"
  fi
  if [ -f "$WORK/unit.err" ]; then
    printf '    stderr: %s\n' "$(tr '\n' '|' <"$WORK/unit.err")"
  fi
}

has_out() {
  if grep -F -q -- "$1" "$WORK/unit.out"; then ok "$2"
  else bad "$2"; show; fi
}
lacks_out() {
  if grep -F -q -- "$1" "$WORK/unit.out"; then bad "$2"; show
  else ok "$2"; fi
}

CLOCK="$WORK/clock"
SLEEPS="$WORK/sleeps"
DNS_STATE="$WORK/dns-state"
DNS_LOG="$WORK/dns-log"
mkdir -p "$WORK/bin"

cat >"$WORK/bin/dns-stub" <<'EOF'
#!/bin/bash
printf '%s\n' "$1" >>"${GENSEO_DNS_LOG:?}"
fail_host="${GENSEO_DNS_FAIL_HOST:-}"
if [ -n "$fail_host" ] && [ "$1" != "$fail_host" ]; then
  exit 0
fi
n=$(tr -cd '0-9' <"${GENSEO_DNS_STATE:?}")
if [ "${n:-0}" -gt 0 ]; then
  printf '%s\n' "$((n - 1))" >"$GENSEO_DNS_STATE"
  exit 1
fi
exit 0
EOF
cat >"$WORK/bin/now-clock" <<'EOF'
#!/bin/bash
tr -cd '0-9' <"${GENSEO_CLOCK_FILE:?}"
printf '\n' 
EOF
cat >"$WORK/bin/sleep-clock" <<'EOF'
#!/bin/bash
printf '%s\n' "$1" >>"${GENSEO_SLEEP_LOG:?}"
python3 -c 'import sys
p, d = sys.argv[1], int(sys.argv[2])
cur = int(open(p).read().strip() or "0")
open(p, "w").write(str(cur + d) + "\n")
' "${GENSEO_CLOCK_FILE:?}" "$1"
EOF
cat >"$WORK/bin/now-bad" <<'EOF'
#!/bin/bash
printf '%s\n' nope
EOF
cat >"$WORK/bin/sleep-fail" <<'EOF'
#!/bin/bash
exit 1
EOF
chmod +x "$WORK/bin/"*

reset_clock() {
  printf '%s\n' "${1:-1000}" >"$CLOCK"
  : >"$SLEEPS"
}
reset_dns() {
  printf '%s\n' "${1:-0}" >"$DNS_STATE"
  : >"$DNS_LOG"
}

# bounded <seconds> command...
# Kills the command if it is still running after <seconds>.
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

run_unit() {
  local t=$1
  shift
  : >"$WORK/unit.out"
  : >"$WORK/unit.err"
  bounded "$t" env "$@" bash -c '
    set -uo pipefail
    . "$1"
    genseo_wait_for_network
  ' _ "$HELPER" >"$WORK/unit.out" 2>"$WORK/unit.err"
}

hook_env() {
  printf '%s\n' \
    GENSEO_NET_WAIT_TEST=1 \
    GENSEO_DNS_RESOLVE="$WORK/bin/dns-stub" \
    GENSEO_DNS_STATE="$DNS_STATE" \
    GENSEO_DNS_LOG="$DNS_LOG" \
    GENSEO_NET_NOW_CMD="$WORK/bin/now-clock" \
    GENSEO_NET_SLEEP_CMD="$WORK/bin/sleep-clock" \
    GENSEO_CLOCK_FILE="$CLOCK" \
    GENSEO_SLEEP_LOG="$SLEEPS" \
    PATH="/usr/bin:/bin"
}

assert_rc() {
  if [ "$RC" = "$1" ]; then ok "$2"
  else bad "$2 (rc $RC, want $1)"; show; fi
}

echo "1. syntax, direct exec, and the wrappers call the wait before the first read"
bash -n "$HELPER" && ok "bash -n helper" || bad "bash -n helper"
bash -n "$ARTICLE" && ok "bash -n article wrapper" || bad "bash -n article wrapper"
bash -n "$LANDING" && ok "bash -n landing wrapper" || bad "bash -n landing wrapper"
bounded 5 /bin/bash "$HELPER" >"$WORK/unit.out" 2>"$WORK/unit.err"
assert_rc 2 "direct exec refuses"
lacks_out "network ready" "direct exec does not report ready"
if awk '
  /genseo_wait_for_network;/ { if (!call) call=NR }
  /\$\(live_count\)/ { if (!feed) feed=NR }
  END { exit !(call && feed && call < feed) }
' "$ARTICLE"; then
  ok "article wait is before the first live_count"
else
  bad "article wait is not before the first live_count"
fi
if awk '
  /genseo_wait_for_network;/ { if (!call) call=NR }
  /^guard; g=/ { if (!g) g=NR }
  END { exit !(call && g && call < g) }
' "$LANDING"; then
  ok "landing wait is before the first guard call"
else
  bad "landing wait is not before the first guard call"
fi
grep -F -q 'GENSEO_DAILY_TARGET:-5' "$ARTICLE" && ok "daily target default is still 5" || bad "daily target default changed"
grep -F -q 'GENSEO_HOST_ROLE:-primary' "$ARTICLE" && ok "article role default is still primary" || bad "article role default changed"
grep -F -q 'GENSEO_LIVE_FEED_RETRIES:-3' "$ARTICLE" && ok "feed retries default is still 3" || bad "feed retries default changed"
grep -F -q 'GENSEO_LIVE_FEED_BACKOFF_SEC:-5' "$ARTICLE" && ok "feed backoff default is still 5" || bad "feed backoff default changed"
grep -F -q 'LIVE_FEED_RETRIES" -gt 5' "$ARTICLE" && ok "feed retry cap is still 5" || bad "feed retry cap changed"
grep -F -q 'live feed unreadable — fail closed, exit' "$ARTICLE" && ok "feed fail-closed line remains" || bad "feed fail-closed line missing"
grep -F -q 'ROLE" = "standby"' "$ARTICLE" && ok "standby delay remains" || bad "standby delay missing"
grep -F -q 'GENSEO_LANDING_DAILY=1 GENSEO_LANDING_DRAFT=1' "$LANDING" && ok "landing stays draft-only" || bad "landing draft env changed"
grep -F -q 'guard: Shopify unreadable — fail closed' "$LANDING" && ok "Shopify unreadable line remains" || bad "Shopify unreadable line missing"
grep -F -q 'GENSEO_HOST_ROLE:-primary' "$LANDING" && ok "landing role default is still primary" || bad "landing role default changed"
if grep -F -q 'shopify_publisher.py' "$HELPER"; then
  bad "network helper names the article publisher"
else
  ok "network helper does not publish"
fi

echo "2. skip is immediate and does not resolve"
reset_dns 99
run_unit 10 \
  GENSEO_NET_WAIT_TEST=1 \
  GENSEO_NET_WAIT_MAX_SEC=0 \
  GENSEO_DNS_RESOLVE="$WORK/bin/dns-stub" \
  GENSEO_DNS_STATE="$DNS_STATE" \
  GENSEO_DNS_LOG="$DNS_LOG" \
  GENSEO_NET_NOW_CMD="$WORK/bin/now-bad" \
  PATH="/usr/bin:/bin"
assert_rc 0 "skip exits 0"
has_out "network wait skipped (GENSEO_NET_WAIT_MAX_SEC=0)" "skip is logged"
lacks_out "fail closed" "skip is not a fail-closed"
[ ! -s "$DNS_LOG" ] && ok "skip does not resolve" || bad "skip called the resolver"

echo "3. default names, then failure then success, with each wait logged"
reset_clock 1000
reset_dns 2
# shellcheck disable=SC2046
run_unit 10 $(hook_env) \
  GENSEO_NET_WAIT_MAX_SEC=30 \
  GENSEO_NET_WAIT_BACKOFF_SEC=5 \
  GENSEO_NET_WAIT_BACKOFF_CAP_SEC=60
assert_rc 0 "recovers after two failures"
has_out "network not ready (wellnessnest.co wellnessnest1.myshopify.com unresolved) — waiting 5s (elapsed 0s/30s)" "first wait names both hosts"
has_out "network ready (wellnessnest.co wellnessnest1.myshopify.com)" "ready names both hosts"
lacks_out "fail closed" "recovery is not fail-closed"
lacks_out "live feed unreadable" "recovery does not say the feed is unreadable"
lacks_out "Shopify unreadable" "recovery does not say Shopify is unreadable"
printf '%s\n' wellnessnest.co wellnessnest1.myshopify.com wellnessnest.co wellnessnest1.myshopify.com >"$WORK/expect-dns"
cmp -s "$WORK/expect-dns" "$DNS_LOG" && ok "resolver saw storefront then admin host, twice" || bad "resolver order drifted"
printf '%s\n' 5 >"$WORK/expect-sleep"
cmp -s "$WORK/expect-sleep" "$SLEEPS" && ok "one 5s wait" || bad "sleep was not 5s"

echo "4. a hyphenated name is legal; a bad name fails closed before DNS"
reset_clock 1000
reset_dns 0
# shellcheck disable=SC2046
run_unit 10 $(hook_env) \
  GENSEO_NET_WAIT_MAX_SEC=30 \
  GENSEO_NET_WAIT_BACKOFF_SEC=5 \
  GENSEO_NET_HOSTS='wellnessnest.co shop-admin.example'
assert_rc 0 "hyphenated host is accepted"
has_out "network ready (wellnessnest.co shop-admin.example)" "ready uses the override list"
reset_dns 0
# shellcheck disable=SC2046
run_unit 10 $(hook_env) \
  GENSEO_NET_WAIT_MAX_SEC=30 \
  GENSEO_SHOPIFY_ADMIN_HOST='bad_host'
assert_rc 1 "underscore host fails closed"
has_out "network not ready — bad DNS name, fail closed" "bad name is logged"
lacks_out "live feed unreadable" "bad name is not a feed failure"
[ ! -s "$DNS_LOG" ] && ok "bad name does not resolve" || bad "bad name called the resolver"
reset_dns 0
# shellcheck disable=SC2046
run_unit 10 $(hook_env) \
  GENSEO_NET_WAIT_MAX_SEC=30 \
  GENSEO_NET_HOSTS='evil;rm'
assert_rc 1 "metacharacter host fails closed"
has_out "network not ready — bad DNS name, fail closed" "metacharacter is logged"
[ ! -s "$DNS_LOG" ] && ok "metacharacter does not resolve" || bad "metacharacter called the resolver"

echo "5. only the unresolved host is waited on"
reset_clock 1000
reset_dns 1
# shellcheck disable=SC2046
run_unit 10 $(hook_env) \
  GENSEO_NET_WAIT_MAX_SEC=30 \
  GENSEO_NET_WAIT_BACKOFF_SEC=5 \
  GENSEO_DNS_FAIL_HOST='wellnessnest1.myshopify.com'
assert_rc 0 "shop-only failure then recovers"
has_out "network not ready (wellnessnest1.myshopify.com unresolved) — waiting 5s (elapsed 0s/30s)" "wait names only the admin host"
lacks_out "wellnessnest.co unresolved" "storefront was already resolved"
has_out "network ready (wellnessnest.co wellnessnest1.myshopify.com)" "both ready after the shop host resolves"

echo "6. exponential backoff, the 600s cap, a stuck clock, and a broken sleep"
reset_clock 1000
reset_dns 1000
# shellcheck disable=SC2046
run_unit 10 $(hook_env) \
  GENSEO_NET_WAIT_MAX_SEC=100 \
  GENSEO_NET_WAIT_BACKOFF_SEC=5 \
  GENSEO_NET_WAIT_BACKOFF_CAP_SEC=20
assert_rc 1 "budget expiry exits 1"
has_out "network not ready — timeout after 100s (DNS unresolved: wellnessnest.co wellnessnest1.myshopify.com), fail closed" "timeout names the budget and both hosts"
lacks_out "network ready" "timeout is not ready"
lacks_out "live feed unreadable" "timeout is not feed unreadable"
printf '%s\n' 5 10 20 20 20 20 5 >"$WORK/expect-sleep"
cmp -s "$WORK/expect-sleep" "$SLEEPS" && ok "backoff is 5,10,20,20,20,20,5" || bad "backoff sequence drifted"
reset_clock 1000
reset_dns 1000
# shellcheck disable=SC2046
run_unit 10 $(hook_env) \
  GENSEO_NET_WAIT_MAX_SEC=99999 \
  GENSEO_NET_WAIT_BACKOFF_SEC=60 \
  GENSEO_NET_WAIT_BACKOFF_CAP_SEC=60
assert_rc 1 "oversized budget still exits 1"
sum=$(awk '{s+=$1} END {print s+0}' "$SLEEPS")
[ "$sum" = 600 ] && ok "budget is clamped to 600s" || bad "budget sum was $sum, want 600"
reset_clock 1000
reset_dns 0
# shellcheck disable=SC2046
run_unit 10 $(hook_env) \
  GENSEO_NET_WAIT_MAX_SEC=30 \
  GENSEO_NET_NOW_CMD="$WORK/bin/now-bad"
assert_rc 1 "bad clock exits 1"
has_out "network not ready — clock unreadable, fail closed" "bad clock is logged"
[ ! -s "$DNS_LOG" ] && ok "bad clock does not resolve" || bad "bad clock called the resolver"
reset_clock 1000
reset_dns 5
# shellcheck disable=SC2046
run_unit 10 $(hook_env) \
  GENSEO_NET_WAIT_MAX_SEC=30 \
  GENSEO_NET_WAIT_BACKOFF_SEC=5 \
  GENSEO_NET_SLEEP_CMD="$WORK/bin/sleep-fail"
assert_rc 1 "broken sleep exits 1"
has_out "network not ready — wait interrupted, fail closed" "interrupted wait is logged"
lacks_out "network not ready — timeout" "interrupted wait is not a timeout"

echo "7. test hooks are ignored unless GENSEO_NET_WAIT_TEST=1; real resolver"
reset_dns 99
run_unit 15 \
  GENSEO_NET_WAIT_TEST=0 \
  GENSEO_NET_WAIT_MAX_SEC=5 \
  GENSEO_NET_WAIT_BACKOFF_SEC=0 \
  GENSEO_NET_HOSTS=localhost \
  GENSEO_DNS_RESOLVE="$WORK/bin/dns-stub" \
  GENSEO_DNS_STATE="$DNS_STATE" \
  GENSEO_DNS_LOG="$DNS_LOG" \
  PATH="/usr/bin:/bin"
assert_rc 0 "localhost resolves without the stub"
has_out "network ready (localhost)" "ready via the system resolver"
[ ! -s "$DNS_LOG" ] && ok "stub was not used" || bad "stub ran without GENSEO_NET_WAIT_TEST=1"
run_unit 20 \
  GENSEO_NET_WAIT_TEST=0 \
  GENSEO_NET_WAIT_MAX_SEC=2 \
  GENSEO_NET_WAIT_BACKOFF_SEC=0 \
  GENSEO_DNS_TIMEOUT_SEC=1 \
  GENSEO_NET_HOSTS='no-such-host.invalid' \
  PATH="/usr/bin:/bin"
assert_rc 1 "NXDOMAIN exits 1"
has_out "network not ready — timeout" "NXDOMAIN logs a network timeout"
has_out "fail closed" "NXDOMAIN fail-closes"
lacks_out "network ready" "NXDOMAIN is not ready"
lacks_out "live feed unreadable" "NXDOMAIN is not feed unreadable"

article_home() {
  H="$WORK/home-$1"
  local sc="$H/genseo/scripts"
  rm -rf "$H"
  mkdir -p "$sc" "$H/genseo/state" "$H/genseo/logs/daily"
  cp "$ROOT/scripts/genseo_daily_lock.sh" "$sc/genseo_daily_lock.sh"
  cp "$ROOT/scripts/genseo_group_timeout.sh" "$sc/genseo_group_timeout.sh"
  cp "$HELPER" "$sc/genseo_wait_for_network.sh"
  cat >"$sc/genseo_published_today.py" <<'PY'
import os, sys
root = os.path.join(os.environ["HOME"], "genseo")
state = os.path.join(root, "state")
idx = os.path.join(state, "calls")
n = 0
if os.path.isfile(idx):
    try:
        n = int(open(idx).read().strip() or "0")
    except ValueError:
        n = 0
open(idx, "w").write(str(n + 1))
if "--json" in sys.argv:
    print('{"entries":[]}')
    raise SystemExit(0)
if "--peer-active" in sys.argv:
    print("peer-idle")
    raise SystemExit(0)
print(open(os.path.join(state, "live-count")).read().strip())
PY
  printf '%s\n' 5 >"$H/genseo/state/live-count"
}

run_article() {
  local t=$1
  shift
  : >"$H/out.log"
  : >"$H/err.log"
  bounded "$t" env -i HOME="$H" PATH="/usr/bin:/bin:/usr/sbin:/sbin" \
    GENSEO_DAILY_TARGET=5 \
    GENSEO_MAX_RUNS=1 \
    GENSEO_PEER_MAX_WAITS=0 \
    GENSEO_NO_DELAY=1 \
    GENSEO_HOST_ROLE=primary \
    GENSEO_LIVE_FEED_RETRIES=0 \
    GENSEO_LIVE_FEED_BACKOFF_SEC=0 \
    GENSEO_NET_WAIT_TEST=1 \
    GENSEO_DNS_RESOLVE="$WORK/bin/dns-stub" \
    GENSEO_DNS_STATE="$DNS_STATE" \
    GENSEO_DNS_LOG="$DNS_LOG" \
    "$@" \
    /bin/bash "$ARTICLE" >"$H/out.log" 2>"$H/err.log"
  cp "$H/out.log" "$WORK/unit.out"
  cp "$H/err.log" "$WORK/unit.err"
}

landing_home() {
  H="$WORK/home-land-$1"
  local sc="$H/genseo/scripts"
  rm -rf "$H"
  mkdir -p "$sc" "$H/genseo/state" "$H/genseo/logs"
  cp "$ROOT/scripts/genseo_group_timeout.sh" "$sc/genseo_group_timeout.sh"
  cp "$HELPER" "$sc/genseo_wait_for_network.sh"
  printf '%s\n' "$2" >"$H/genseo/state/guard-codes"
  cat >"$sc/landing_guard.py" <<'PY'
import sys
codes = open("state/guard-codes").read().split()
open("state/guard-codes", "w").write(" ".join(codes[1:]))
print("stub landing_guard: exit", codes[0] if codes else 0)
sys.exit(int(codes[0]) if codes else 0)
PY
}

run_landing() {
  local t=$1
  shift
  : >"$H/out.log"
  : >"$H/err.log"
  bounded "$t" env -i HOME="$H" PATH="/usr/bin:/bin:/usr/sbin:/sbin" \
    GENSEO_HOST_ROLE=primary \
    GENSEO_NO_DELAY=1 \
    GENSEO_NET_WAIT_TEST=1 \
    GENSEO_DNS_RESOLVE="$WORK/bin/dns-stub" \
    GENSEO_DNS_STATE="$DNS_STATE" \
    GENSEO_DNS_LOG="$DNS_LOG" \
    "$@" \
    /bin/bash "$LANDING" >"$H/out.log" 2>"$H/err.log"
  cp "$H/out.log" "$WORK/unit.out"
  cp "$H/err.log" "$WORK/unit.err"
}

echo "8. article wrapper: DNS fails then succeeds before any feed read, then the count is used"
reset_dns 2
article_home recover
run_article 15 \
  GENSEO_NET_WAIT_MAX_SEC=30 \
  GENSEO_NET_WAIT_BACKOFF_SEC=0
assert_rc 0 "article wrapper exits 0"
has_out "network not ready (wellnessnest.co wellnessnest1.myshopify.com unresolved) — waiting 0s" "article logs the wait"
has_out "network ready (wellnessnest.co wellnessnest1.myshopify.com)" "article logs ready"
has_out "DONE:" "article reaches the existing done path"
lacks_out "live feed unreadable" "article recovery does not use the feed-unreadable line"
calls=$(tr -cd '0-9' <"$H/genseo/state/calls" 2>/dev/null || true)
[ "$calls" = 2 ] && ok "feed was read twice, after DNS (banner + loop)" || bad "feed reads were $calls, want 2"
if awk '
  /waiting 0s/ { if (!w) w=NR }
  /network ready/ { if (!r) r=NR }
  /start \(target/ { if (!s) s=NR }
  END { exit !(w && r && s && w < r && r < s) }
' "$H/out.log"; then
  ok "wait, then ready, then the first feed read"
else
  bad "feed read was not after DNS"
fi

echo "9. article wrapper: DNS never comes up, fail closed, feed is not read"
reset_dns 9999
article_home timeout
run_article 20 \
  GENSEO_NET_WAIT_MAX_SEC=2 \
  GENSEO_NET_WAIT_BACKOFF_SEC=1
assert_rc 1 "article DNS timeout exits 1"
has_out "network not ready — timeout" "article logs a network timeout"
has_out "fail closed" "article timeout fail-closes"
lacks_out "live feed unreadable" "article timeout does not say the feed is unreadable"
lacks_out "start (target" "article timeout does not read the feed in the banner"
[ ! -e "$H/genseo/state/calls" ] && ok "published_today.py was not called" || bad "published_today.py ran during the DNS wait"
[ ! -e "$H/genseo/state/daily.lock" ] && ok "article lock released" || bad "article lock still held"
lacks_out "shopify_publisher.py" "article timeout does not publish"

echo "10. article wrapper: GENSEO_NET_WAIT_MAX_SEC=0 skips even if DNS would fail"
reset_dns 99
article_home skip
run_article 15 GENSEO_NET_WAIT_MAX_SEC=0
assert_rc 0 "skipped wait still exits 0"
has_out "network wait skipped (GENSEO_NET_WAIT_MAX_SEC=0)" "article logs the skip"
has_out "DONE:" "skip still reaches the done path"
[ ! -s "$DNS_LOG" ] && ok "skipped article wait does not resolve" || bad "skipped article wait resolved"
calls=$(tr -cd '0-9' <"$H/genseo/state/calls")
[ "$calls" = 2 ] && ok "skip still reads the feed" || bad "skip feed reads were $calls"

echo "11. landing wrapper: DNS fails then succeeds, then the guard runs"
reset_dns 2
landing_home recover 3
run_landing 15 \
  GENSEO_NET_WAIT_MAX_SEC=30 \
  GENSEO_NET_WAIT_BACKOFF_SEC=0
assert_rc 0 "landing recovery exits 0"
has_out "network not ready (wellnessnest.co wellnessnest1.myshopify.com unresolved) — waiting 0s" "landing logs the wait"
has_out "network ready" "landing logs ready"
has_out "today's gsl- landing draft already exists" "landing still stands down on guard 3"
lacks_out "Shopify unreadable" "landing recovery is not Shopify unreadable"
[ ! -s "$H/genseo/state/guard-codes" ] && ok "guard ran after DNS" || bad "guard was not consumed"
[ ! -e "$H/genseo/state/landing-daily.lock" ] && ok "landing lock released after stand-down" || bad "landing lock still held"

echo "12. landing wrapper: DNS never comes up, fail closed, guard is not called"
reset_dns 9999
landing_home timeout 7
run_landing 20 \
  GENSEO_NET_WAIT_MAX_SEC=2 \
  GENSEO_NET_WAIT_BACKOFF_SEC=1
assert_rc 1 "landing DNS timeout exits 1"
has_out "network not ready — timeout" "landing logs a network timeout"
has_out "fail closed" "landing timeout fail-closes"
lacks_out "Shopify unreadable" "landing timeout does not say Shopify is unreadable"
lacks_out "stub landing_guard" "guard was not started"
[ "$(tr -cd '0-9' <"$H/genseo/state/guard-codes")" = 7 ] && ok "guard code was not consumed" || bad "guard code changed"
[ ! -e "$H/genseo/state/agent-called" ] && ok "landing agent did not start" || bad "landing agent started"
[ ! -e "$H/genseo/state/landing-daily.lock" ] && ok "landing lock released" || bad "landing lock still held"
lacks_out "landing_publisher.py" "landing timeout does not build a page"

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" = 0 ]

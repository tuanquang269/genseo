#!/bin/bash
# Offline Mac Mini failover bootstrap. No launchctl, no network, no Shopify.
#   bash tests/test_mac_mini_failover_bootstrap.sh
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT/scripts/mac_mini_failover_bootstrap.sh"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/failover-boot.XXXXXX")" || exit 1
trap 'rm -rf "$WORK"' EXIT
PASS=0
FAIL=0
CANARY="CANARY_SECRET_do_not_print_9f3a"

ok() { PASS=$((PASS + 1)); printf '  ok   %s\n' "$*"; }
bad() { FAIL=$((FAIL + 1)); printf '  FAIL %s\n' "$*"; }

HOME_DIR=""
GENSEO_HOME=""
TEST_MODE=0
HB_REF=origin/main
MAX_AGE=""
WORKER_NAME=Mac-Mini
FAILOVER_HOSTNAME="Kevins-Mac-mini-2.local"
GIT_DIR_ENV=""

reset_flags() {
  TEST_MODE=0
  HB_REF=origin/main
  MAX_AGE=""
  WORKER_NAME=Mac-Mini
  FAILOVER_HOSTNAME="Kevins-Mac-mini-2.local"
  GIT_DIR_ENV=""
}

run() {
  : >"$WORK/out"
  : >"$WORK/err"
  cmd=(env -i
    "HOME=$HOME_DIR"
    "PATH=/usr/bin:/bin"
    "GENSEO_HOME=$GENSEO_HOME"
    "GENSEO_FAILOVER_TEST=$TEST_MODE"
    "GENSEO_FAILOVER_HEARTBEAT_REF=$HB_REF"
    "GENSEO_FAILOVER_HOSTNAME=$FAILOVER_HOSTNAME"
    "GENSEO_WORKER_NAME=$WORKER_NAME")
  if [ -n "$MAX_AGE" ]; then
    cmd+=("GENSEO_FAILOVER_HEARTBEAT_MAX_AGE=$MAX_AGE")
  fi
  if [ -n "$GIT_DIR_ENV" ]; then
    cmd+=("GIT_DIR=$GIT_DIR_ENV")
  fi
  "${cmd[@]}" /bin/bash "$SCRIPT" "$@" >"$WORK/out" 2>"$WORK/err"
  RC=$?
}

assert_rc() {
  if [ "$RC" = "$1" ]; then ok "$2"
  else bad "$2 (rc $RC, want $1)"; printf '    stdout: %s\n' "$(tr '\n' '|' <"$WORK/out")"; printf '    stderr: %s\n' "$(tr '\n' '|' <"$WORK/err")"; fi
}

has() {
  if grep -F -q -- "$2" "$1"; then ok "$3"
  else bad "$3"; fi
}

lacks() {
  if grep -F -q -- "$2" "$1"; then bad "$3"
  else ok "$3"; fi
}

no_secret() {
  if grep -F -q -- "$CANARY" "$WORK/out" || grep -F -q -- "$CANARY" "$WORK/err"; then
    bad "secret value leaked ($1)"
  else
    ok "secret value hidden ($1)"
  fi
}

git_in() {
  git -C "$GENSEO_HOME" "$@"
}

write_token() {
  local shop="$1" token="$2"
  mkdir -p "$HOME_DIR/.genseo"
  python3 - "$HOME_DIR/.genseo/shopify_token.json" "$shop" "$token" <<'PY'
import json, sys
json.dump({"shop": sys.argv[2], "access_token": sys.argv[3]}, open(sys.argv[1], "w"))
PY
}

# name, secrets: good|parser
new_ready() {
  reset_flags
  HOME_DIR="$WORK/home-$1"
  GENSEO_HOME="$HOME_DIR/genseo"
  rm -rf "$HOME_DIR"
  mkdir -p "$HOME_DIR/.local/bin" "$HOME_DIR/.grok/bin" "$HOME_DIR/PATI/LLM-Wiki" \
    "$GENSEO_HOME/scripts" "$GENSEO_HOME/deploy"
  printf '%s\n' '#!/bin/sh' 'echo agent' >"$HOME_DIR/.local/bin/cursor-agent"
  printf '%s\n' '#!/bin/sh' 'echo grok' >"$HOME_DIR/.grok/bin/grok"
  chmod 755 "$HOME_DIR/.local/bin/cursor-agent" "$HOME_DIR/.grok/bin/grok"
  printf '%s\n' '#!/bin/bash' 'echo daily' >"$GENSEO_HOME/deploy/grokbot-genseo-daily.sh"
  printf '%s\n' '#!/bin/bash' 'echo landing' >"$GENSEO_HOME/scripts/run_landing_daily.sh"
  printf '%s\n' 'lock' >"$GENSEO_HOME/scripts/genseo_daily_lock.sh"
  printf '%s\n' 'timeout' >"$GENSEO_HOME/scripts/genseo_group_timeout.sh"
  if [ "$2" = parser ]; then
    cat >"$GENSEO_HOME/.env" <<EOF
# SHOPIFY_CLI_APP_SHOP=${CANARY}-comment
export SHOPIFY_CLI_APP_CLIENT_ID=${CANARY}-export
SHOPIFY_CLI_APP_SHOP="${CANARY}-shop"
SHOPIFY_CLI_APP_CLIENT_SECRET=${CANARY}-secret
EOF
    printf '%s\n' 'NINE_ROUTER_KEY=' "export NINE_ROUTER_KEY=\"${CANARY}-vault\"" \
      >"$HOME_DIR/PATI/LLM-Wiki/.env"
  else
    cat >"$GENSEO_HOME/.env" <<EOF
SHOPIFY_CLI_APP_SHOP=${CANARY}-shop
SHOPIFY_CLI_APP_CLIENT_ID=${CANARY}-id
SHOPIFY_CLI_APP_CLIENT_SECRET=${CANARY}-secret
EOF
    printf '%s\n' "export NINE_ROUTER_KEY=\"${CANARY}-vault\"" >"$HOME_DIR/PATI/LLM-Wiki/.env"
  fi
  write_token "${CANARY}-shop" "${CANARY}-token"
  git_in init -q
  git_in symbolic-ref HEAD refs/heads/main
  git_in config user.email test@example.com
  git_in config user.name Test
  git_in add -f -- .env deploy scripts
  git_in commit -q -m fixture
}

marker() {
  git_in commit -q --allow-empty -m "$1"
}

check_plist() {
  python3 - "$@" <<'PY'
import plistlib, sys
path, kind = sys.argv[1], sys.argv[2]
with open(path, "rb") as fh:
    data = plistlib.load(fh)
if kind == "worker":
    args = data["ProgramArguments"]
    if args[1:4] != ["worker", "start", "--name"]:
        raise SystemExit("argv %s" % args)
    if args[4] != sys.argv[3]:
        raise SystemExit("name %s" % args[4])
    if not args[0].endswith("/.local/bin/cursor-agent"):
        raise SystemExit("bin %s" % args[0])
    if args[5] != "--worker-dir" or args[6] != data["WorkingDirectory"]:
        raise SystemExit("workdir")
    if data["RunAtLoad"] is not True or data["KeepAlive"] is not True:
        raise SystemExit("keepalive")
    if data["ThrottleInterval"] != 30:
        raise SystemExit("throttle")
    if data["Label"] != "com.pati.cursor-agent-worker":
        raise SystemExit("label")
    if not data["StandardOutPath"].endswith("/Library/Logs/com.pati.cursor-agent-worker.out.log"):
        raise SystemExit("stdout log")
    if not data["StandardErrorPath"].endswith("/Library/Logs/com.pati.cursor-agent-worker.err.log"):
        raise SystemExit("stderr log")
    if "/.grok/bin" not in data["EnvironmentVariables"]["PATH"]:
        raise SystemExit("path")
elif kind == "daily":
    env = data["EnvironmentVariables"]
    if data["Label"] != "com.pati.genseo-daily" or data["RunAtLoad"] is not False:
        raise SystemExit("daily label")
    if env.get("GENSEO_HOST_ROLE") != "primary" or env.get("GENSEO_TICKET_PREFIX") != "MM":
        raise SystemExit("daily role")
    if env.get("GENSEO_NO_FACE") != "1":
        raise SystemExit("noface")
    if not data["ProgramArguments"][1].endswith("/bin/grokbot-genseo-daily.sh"):
        raise SystemExit("daily program")
elif kind == "landing":
    if data["Label"] != "com.pati.genseo-landing" or data["RunAtLoad"] is not False:
        raise SystemExit("landing label")
    if data["EnvironmentVariables"].get("GENSEO_HOST_ROLE") != "primary":
        raise SystemExit("landing role")
    if "GENSEO_LANDING_LIVE_OK" in data["EnvironmentVariables"]:
        raise SystemExit("live ok")
    if not data["ProgramArguments"][1].endswith("/scripts/run_landing_daily.sh"):
        raise SystemExit("landing program")
    raw = open(path, "r", encoding="utf-8").read()
    for banned in ("GENSEO_LANDING_LIVE_OK", "--live", "shopify_publisher", "landing_publisher"):
        if banned in raw:
            raise SystemExit("publish switch %s" % banned)
    if "never published" not in raw or "installed-by: mac_mini_failover_bootstrap" not in raw:
        raise SystemExit("landing mark")
else:
    raise SystemExit("kind")
PY
}

echo "1. help and unknown argument write nothing"
new_ready help good
run --help
assert_rc 0 "help exit 0"
has "$WORK/out" "does not call launchctl" "help says launchctl is not called"
[ ! -e "$HOME_DIR/Library" ] && ok "help wrote no Library" || bad "help wrote Library"
[ ! -e "$HOME_DIR/bin" ] && ok "help wrote no bin" || bad "help wrote bin"
run --not-a-flag
assert_rc 2 "unknown arg exit 2"
[ ! -e "$HOME_DIR/Library" ] && ok "unknown arg wrote nothing" || bad "unknown arg wrote Library"

echo "2. default dry-run on an empty home writes nothing"
HOME_DIR="$WORK/empty-home"
GENSEO_HOME="$HOME_DIR/genseo"
reset_flags
rm -rf "$HOME_DIR"
mkdir -p "$HOME_DIR"
run
assert_rc 0 "empty dry-run exit 0"
has "$WORK/out" "mode: dry-run" "mode dry-run"
has "$WORK/out" "requested: none" "nothing requested"
has "$WORK/out" "cursor-agent: MISSING" "cursor-agent missing"
has "$WORK/out" "grok: MISSING" "grok missing"
has "$WORK/out" "guard: block" "guard blocks"
has "$WORK/out" "daily_ready: no" "daily not ready"
has "$WORK/out" "launchd: not started" "launchd not started"
has "$WORK/out" "hostname expected: Kevins-Mac-mini-2.local" "names the Mini hostname"
has "$WORK/out" "worker_name: Mac-Mini" "default worker name"
has "$WORK/out" 'load_worker: launchctl bootstrap gui/$(id -u)' "prints the worker load line"
[ ! -e "$HOME_DIR/Library" ] && ok "dry-run wrote no Library" || bad "dry-run wrote Library"
[ ! -e "$HOME_DIR/bin" ] && ok "dry-run wrote no bin" || bad "dry-run wrote bin"

echo "3. env key names come from the readers; values stay hidden"
new_ready parser parser
write_token "your-store.myshopify.com" "shpat_YOUR_ADMIN_API_TOKEN"
tpl_sum=$(cksum "$ROOT/deploy/com.pati.cursor-agent-worker.plist")
run
assert_rc 0 "parser dry-run exit 0"
has "$WORK/out" "env key SHOPIFY_CLI_APP_SHOP: present (genseo/.env)" "shop key present"
has "$WORK/out" "env key SHOPIFY_CLI_APP_CLIENT_ID: MISSING (genseo/.env)" "export shopify key ignored"
has "$WORK/out" "env key SHOPIFY_CLI_APP_CLIENT_SECRET: present (genseo/.env)" "secret key present"
has "$WORK/out" "env key NINE_ROUTER_KEY: MISSING (vault .env)" "blank vault line wins"
has "$WORK/out" "shopify token file: incomplete" "placeholder token incomplete"
lacks "$WORK/out" "GEMINI_API_KEY" "gemini key is not an .env requirement"
lacks "$WORK/out" "FLICKR_API_KEY" "flickr key is not an .env requirement"
no_secret "parser dry-run"
derived=$(grep -oE 'e\["SHOPIFY_CLI_APP_[A-Z0-9_]+"\]' "$ROOT/scripts/shopify_app_token.py" \
  | sed -E 's/^e\["//; s/"\]$//' | sort -u)
derived_ok=1
while IFS= read -r key; do
  [ -n "$key" ] || continue
  if ! grep -F -q "env key ${key}:" "$WORK/out"; then
    derived_ok=0
  fi
done <<EOF
$derived
EOF
[ "$derived_ok" = 1 ] && ok "every shopify_app_token.py key is listed" || bad "derived keys missing"
[ "$(cksum "$ROOT/deploy/com.pati.cursor-agent-worker.plist")" = "$tpl_sum" ] && ok "worker template unchanged" || bad "worker template changed"

echo "4. a fresh MacBook heartbeat blocks daily install and subjects are not evaluated"
new_ready fresh good
NOW=$(date +%s)
marker "failover-heartbeat: macbook-pro $((NOW - 30))"
marker 'failover-release: macbook-pro $(touch '"$WORK/pwned"')'
HB_REF=HEAD
TEST_MODE=1
MAX_AGE=3600
run --enable-daily
assert_rc 1 "fresh heartbeat enable exit 1"
has "$WORK/out" "guard: block" "fresh heartbeat blocks"
has "$WORK/out" "daily_block: guard" "daily block is the guard"
has "$WORK/out" "daily_install: refused" "daily install refused"
has "$WORK/out" "worker_install: not-requested" "worker not requested"
has "$WORK/out" "wrapper: not run" "wrapper not run"
has "$WORK/err" "refusing daily plists" "stderr refuses daily"
[ ! -e "$WORK/pwned" ] && ok "commit subject was not evaluated" || bad "commit subject ran"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" ] && ok "no daily plist" || bad "daily plist written"
[ ! -e "$HOME_DIR/bin/grokbot-genseo-daily.sh" ] && ok "no wrapper copy" || bad "wrapper copied"

echo "5. a newer release allows the daily plists and leaves the worker uninstalled"
new_ready release good
NOW=$(date +%s)
marker "failover-heartbeat: macbook-pro $((NOW - 30))"
marker "failover-release: macbook-pro $NOW"
HB_REF=HEAD
TEST_MODE=1
MAX_AGE=3600
daily_tpl=$(cksum "$ROOT/deploy/com.pati.genseo-daily.mini.plist")
macbook_tpl=$(cksum "$ROOT/deploy/com.pati.genseo-daily.macbook.plist")
run --enable-daily
assert_rc 0 "release enable exit 0"
has "$WORK/out" "guard: allow" "release allows"
has "$WORK/out" "daily_install: written" "daily written"
has "$WORK/out" "worker_install: not-requested" "worker still not requested"
has "$WORK/out" "wrapper: ran" "wrapper ran"
has "$WORK/out" "launchd: not started" "launchd still not started"
no_secret "release enable"
[ -x "$HOME_DIR/bin/grokbot-genseo-daily.sh" ] && ok "wrapper copy executable" || bad "wrapper copy missing"
cmp -s "$GENSEO_HOME/deploy/grokbot-genseo-daily.sh" "$HOME_DIR/bin/grokbot-genseo-daily.sh" \
  && ok "wrapper copy matches the checkout" || bad "wrapper copy differs"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.cursor-agent-worker.plist" ] && ok "worker plist absent" || bad "worker plist written"
if check_plist "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" daily; then
  ok "daily plist is primary MM"
else
  bad "daily plist shape"
fi
if check_plist "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-landing.plist" landing; then
  ok "landing plist is primary and unpublished"
else
  bad "landing plist shape"
fi
[ -d "$GENSEO_HOME/logs" ] && ok "article log dir created" || bad "article log dir missing"
grep -F -q 'installed-by: mac_mini_failover_bootstrap' "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" \
  && ok "daily plist has the installer mark" || bad "daily plist missing the installer mark"
lacks "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" "/Users/kevinkreative" "daily plist home rewritten"
lacks "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-landing.plist" "/Users/kevinkreative" "landing plist home rewritten"
[ "$(cksum "$ROOT/deploy/com.pati.genseo-daily.macbook.plist")" = "$macbook_tpl" ] && ok "macbook daily plist untouched" || bad "macbook daily plist changed"
grep -F -q '<key>GENSEO_HOST_ROLE</key><string>primary</string>' "$ROOT/deploy/com.pati.genseo-daily.macbook.plist" \
  && ok "macbook daily plist stays primary" || bad "macbook role is not primary"
grep -F -q '<key>GENSEO_TICKET_PREFIX</key><string>MB</string>' "$ROOT/deploy/com.pati.genseo-daily.macbook.plist" \
  && ok "macbook ticket prefix stays MB" || bad "macbook prefix changed"
[ "$(cksum "$ROOT/deploy/com.pati.genseo-daily.mini.plist")" = "$daily_tpl" ] && ok "mini daily template unchanged" || bad "mini daily template changed"

echo "6. a stale heartbeat does not allow enable; origin/main is not implied by HEAD"
new_ready stale good
NOW=$(date +%s)
marker "failover-heartbeat: macbook-pro $((NOW - 7200))"
HB_REF=HEAD
TEST_MODE=1
MAX_AGE=10
run --enable-daily
assert_rc 1 "stale heartbeat enable exit 1"
has "$WORK/out" "guard: block" "stale heartbeat blocks"
has "$WORK/out" "stale heartbeat is not an offline MacBook" "reason refuses silence"
has "$WORK/out" "heartbeat_max_age: ignored" "max-age knob is ignored"
has "$WORK/out" "stale_heartbeat_allow: no" "stale allow is off"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" ] && ok "stale heartbeat wrote no daily plist" || bad "stale heartbeat wrote daily"
MAX_AGE=""
HB_REF=origin/main
run --enable-daily
assert_rc 1 "default ref ignores a local HEAD marker"
has "$WORK/out" "guard: block" "missing origin/main blocks"
has "$WORK/out" "heartbeat ref origin/main is missing" "reason names origin/main"

new_ready hidden good
NOW=$(date +%s)
marker "failover-heartbeat: macbook-pro $NOW"
i=0
while [ "$i" -lt 120 ]; do
  marker "failover-noise: pad $i"
  i=$((i + 1))
done
marker "failover-release: macbook-pro $((NOW - 10))"
HB_REF=HEAD
TEST_MODE=1
run --enable-daily
assert_rc 1 "noise cannot hide a newer heartbeat"
has "$WORK/out" "guard: block" "hidden heartbeat still blocks"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" ] && ok "hidden heartbeat wrote no plist" || bad "hidden heartbeat wrote a plist"

new_ready future good
NOW=$(date +%s)
marker "failover-release: macbook-pro $NOW"
marker "failover-heartbeat: macbook-pro $((NOW + 7200))"
HB_REF=HEAD
TEST_MODE=1
run --enable-daily
assert_rc 1 "slightly future heartbeat blocks"
has "$WORK/out" "in the future" "reason says future"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" ] && ok "future heartbeat wrote no plist" || bad "future heartbeat wrote a plist"

new_ready nonsense good
NOW=$(date +%s)
marker "failover-heartbeat: macbook-pro 9999999999"
marker "failover-release: macbook-pro $NOW"
HB_REF=HEAD
TEST_MODE=1
run --enable-daily
assert_rc 0 "far-future heartbeat is ignored when a release is current"
has "$WORK/out" "guard: allow" "current release still allows"

new_ready tied good
NOW=$(date +%s)
marker "failover-heartbeat: macbook-pro $NOW"
marker "failover-release: macbook-pro $NOW"
HB_REF=HEAD
TEST_MODE=1
run --enable-daily
assert_rc 1 "equal epochs do not release"
has "$WORK/out" "guard: block" "tie stays blocked"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" ] && ok "tie wrote no plist" || bad "tie wrote a plist"

echo "7. worker install renders Mac-Mini and does not install daily jobs"
new_ready worker good
TEST_MODE=1
run --install-worker
assert_rc 0 "worker install exit 0"
has "$WORK/out" "worker_install: written" "worker written"
has "$WORK/out" "daily_install: not-requested" "daily not requested"
has "$WORK/out" "launchd: not started" "worker install did not start launchd"
no_secret "worker install"
[ -d "$HOME_DIR/Library/Logs" ] && ok "log dir created" || bad "log dir missing"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" ] && ok "daily plist not installed" || bad "daily plist installed"
[ ! -e "$HOME_DIR/bin/grokbot-genseo-daily.sh" ] && ok "wrapper not run for worker" || bad "wrapper ran for worker"
if check_plist "$HOME_DIR/Library/LaunchAgents/com.pati.cursor-agent-worker.plist" worker Mac-Mini; then
  ok "worker plist shape"
else
  bad "worker plist shape"
fi
WORKER_NAME=MiniAlt
run --install-worker
assert_rc 0 "second worker install exit 0"
if check_plist "$HOME_DIR/Library/LaunchAgents/com.pati.cursor-agent-worker.plist" worker MiniAlt; then
  ok "worker plist replaced"
else
  bad "worker plist not replaced"
fi

echo "8. refusals: missing binary, bad name, symlink, non-Mac, dirty, other branch"
new_ready miss good
rm -f "$HOME_DIR/.local/bin/cursor-agent"
TEST_MODE=1
run --install-worker
assert_rc 1 "missing cursor-agent exit 1"
has "$WORK/out" "worker_block: cursor-agent" "block names cursor-agent"
has "$WORK/out" "worker_install: refused" "worker refused"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.cursor-agent-worker.plist" ] && ok "no plist without the binary" || bad "plist written without binary"

new_ready badname good
WORKER_NAME="bad name"
TEST_MODE=1
run --install-worker
assert_rc 1 "bad worker name exit 1"
has "$WORK/out" "worker_block: name" "block names the worker name"
[ ! -e "$HOME_DIR/Library" ] && ok "bad name wrote nothing" || bad "bad name wrote Library"

new_ready link good
TEST_MODE=1
mkdir -p "$HOME_DIR/Library/LaunchAgents"
printf '%s\n' original >"$WORK/outside-target"
ln -s "$WORK/outside-target" "$HOME_DIR/Library/LaunchAgents/com.pati.cursor-agent-worker.plist"
run --install-worker
assert_rc 1 "symlink dest exit 1"
has "$WORK/err" "refusing to follow symlink" "stderr names the symlink"
[ -L "$HOME_DIR/Library/LaunchAgents/com.pati.cursor-agent-worker.plist" ] && ok "symlink kept" || bad "symlink replaced"
[ "$(cat "$WORK/outside-target")" = original ] && ok "symlink target untouched" || bad "symlink target changed"

new_ready linux good
TEST_MODE=0
run --install-worker
assert_rc 2 "non-Mac apply exit 2"
has "$WORK/err" "refusing:" "stderr says refusing"
has "$WORK/out" "worker_install: refused" "non-Mac worker refused"
[ ! -e "$HOME_DIR/Library" ] && ok "non-Mac wrote no Library" || bad "non-Mac wrote Library"

new_ready dirty good
NOW=$(date +%s)
marker "failover-release: macbook-pro $NOW"
HB_REF=HEAD
TEST_MODE=1
printf '\n' >>"$GENSEO_HOME/.env"
run --enable-daily
assert_rc 1 "dirty tree exit 1"
has "$WORK/out" "daily_block: clean" "dirty tree blocks daily"
has "$WORK/out" "clean: no" "reports dirty"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" ] && ok "dirty tree wrote no daily plist" || bad "dirty tree wrote daily"

new_ready branch good
NOW=$(date +%s)
marker "failover-release: macbook-pro $NOW"
git_in checkout -q -b side
HB_REF=HEAD
TEST_MODE=1
run --enable-daily
assert_rc 1 "non-main exit 1"
has "$WORK/out" "daily_block: branch" "branch blocks daily"
has "$WORK/out" "branch: side" "reports the branch"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" ] && ok "side branch wrote no daily plist" || bad "side branch wrote daily"

echo "9. both flags, and dry-run wins over apply"
new_ready bothblock good
TEST_MODE=1
run --install-worker --enable-daily
assert_rc 1 "both flags with guard block exit 1"
has "$WORK/out" "worker_install: written" "worker still installs"
has "$WORK/out" "daily_install: refused" "daily refused beside the worker"
has "$WORK/out" "daily_block: guard" "guard is why"
[ -f "$HOME_DIR/Library/LaunchAgents/com.pati.cursor-agent-worker.plist" ] && ok "worker file exists" || bad "worker file missing"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" ] && ok "daily file absent" || bad "daily file present"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-landing.plist" ] && ok "landing file absent" || bad "landing file present"

new_ready bothok good
NOW=$(date +%s)
marker "failover-release: macbook-pro $NOW"
HB_REF=HEAD
TEST_MODE=1
run --dry-run --enable-daily --install-worker
assert_rc 0 "dry-run with apply flags exit 0"
has "$WORK/out" "mode: dry-run" "dry-run wins"
has "$WORK/out" "requested: install-worker,enable-daily" "both requested"
has "$WORK/out" "worker_install: would-write" "worker would write"
has "$WORK/out" "daily_install: would-write" "daily would write"
has "$WORK/out" "wrapper: not run" "dry-run does not run the wrapper"
[ ! -e "$HOME_DIR/Library" ] && ok "dry-run apply wrote nothing" || bad "dry-run apply wrote Library"
[ ! -e "$HOME_DIR/bin" ] && ok "dry-run apply wrote no bin" || bad "dry-run apply wrote bin"
run --install-worker --enable-daily
assert_rc 0 "both flags with release exit 0"
has "$WORK/out" "worker_install: written" "both: worker written"
has "$WORK/out" "daily_install: written" "both: daily written"
has "$WORK/out" "launchd: not started" "both: launchd not started"
no_secret "both flags"

echo "10. a revision that looks like a git option is refused, and install commands are not executed"
new_ready age good
HB_REF='--all'
run
assert_rc 2 "option-shaped ref exit 2"
has "$WORK/err" "not an option" "stderr rejects the ref"
[ ! -e "$HOME_DIR/Library" ] && ok "bad ref wrote nothing" || bad "bad ref wrote Library"
HB_REF=origin/main
run --enable-daily --disable-daily
assert_rc 2 "enable and disable together exit 2"
has "$WORK/err" "together are refused" "stderr refuses both daily flags"
[ ! -e "$HOME_DIR/Library" ] && ok "both daily flags wrote nothing" || bad "both daily flags wrote Library"

python3 - "$SCRIPT" <<'PY'
import pathlib, re, sys
text = pathlib.Path(sys.argv[1]).read_text()
text = re.sub(r"<<'EOF'\n.*?^EOF\n", "", text, count=1, flags=re.S | re.M)
text = re.sub(r"<<'PY'\n.*?^PY\n", "", text, flags=re.S | re.M)
text = re.sub(r"'[^']*'", "''", text)
code = "\n".join(line.split("#", 1)[0] for line in text.splitlines())
bad = []
for word in ("launchctl", "osascript", "git fetch", "git pull", "git push", "git commit", "curl", "ssh", "shopify_publisher", "$(id"):
    if word in code:
        bad.append(word)
if bad:
    sys.exit("executable code contains: " + ", ".join(bad))
PY
if [ $? = 0 ]; then ok "no launchctl, fetch, push, or Shopify call in code"
else bad "static command scan failed"; fi

python3 - "$SCRIPT" <<'PY'
import pathlib, sys
text = pathlib.Path(sys.argv[1]).read_text()
banned = ("declare -A", "mapfile", "readarray", "local -n")
found = [w for w in banned if w in text]
if found:
    sys.exit("bash 4 syntax: " + ", ".join(found))
PY
if [ $? = 0 ]; then ok "no bash-4-only syntax"
else bad "bash 4 syntax present"; fi

src_args=$(python3 - "$ROOT/deploy/com.pati.cursor-agent-worker.plist" <<'PY'
import plistlib, sys
data = plistlib.load(open(sys.argv[1], "rb"))
print("\n".join(data["ProgramArguments"]))
PY
)
printf '%s\n' "$src_args" | grep -qx '__CURSOR_AGENT_BIN__' && ok "template binary is the cursor-agent token" || bad "template binary token"
printf '%s\n' "$src_args" | grep -qx '__WORKER_NAME__' && ok "template name is a token" || bad "template name token"
printf '%s\n' "$src_args" | grep -qx 'worker' && ok "template subcommand is worker" || bad "template missing worker"
printf '%s\n' "$src_args" | grep -qx 'start' && ok "template subcommand is start" || bad "template missing start"
printf '%s\n' "$src_args" | grep -qx -- '--name' && ok "template passes --name" || bad "template missing --name"
grep -q 'cursor-agent' "$ROOT/deploy/com.pati.cursor-agent-worker.plist" && ok "template comment names cursor-agent" || bad "template missing cursor-agent"
grep -q '>primary<' "$ROOT/deploy/com.pati.genseo-daily.mini.plist" && ok "mini daily template is primary" || bad "mini daily role"
grep -q 'never published' "$ROOT/deploy/com.pati.genseo-landing.mini.plist" && ok "landing template stays unpublished" || bad "landing template wording"
grep -q 'cp deploy/com.pati.genseo-landing.mini.plist' "$ROOT/deploy/com.pati.genseo-landing.mini.plist" \
  && bad "landing template still documents a raw copy" || ok "landing template does not document a raw copy"
allow_n=$(grep -c 'GUARD_STATUS=allow' "$SCRIPT")
[ "$allow_n" = 1 ] && ok "guard has one allow path" || bad "guard allow paths: $allow_n"

echo "11. disable, foreign plists, wrong host, and GIT_DIR"
new_ready foreign good
NOW=$(date +%s)
marker "failover-release: macbook-pro $NOW"
HB_REF=HEAD
TEST_MODE=1
mkdir -p "$HOME_DIR/Library/LaunchAgents"
printf '%s\n' 'foreign daily' >"$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist"
run --enable-daily
assert_rc 1 "foreign daily plist exit 1"
has "$WORK/out" "daily_block: foreign-plist" "foreign plist blocks"
[ "$(cat "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist")" = "foreign daily" ] && ok "foreign daily plist kept" || bad "foreign daily plist replaced"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-landing.plist" ] && ok "foreign block wrote no landing plist" || bad "foreign block wrote landing"

new_ready offhost good
NOW=$(date +%s)
marker "failover-release: macbook-pro $NOW"
HB_REF=HEAD
TEST_MODE=1
FAILOVER_HOSTNAME="MacBook-Pro.local"
run --enable-daily
assert_rc 1 "wrong hostname enable exit 1"
has "$WORK/out" "hostname match: no" "wrong host does not match"
has "$WORK/out" "daily_block: hostname" "hostname blocks daily"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" ] && ok "wrong host wrote no daily plist" || bad "wrong host wrote daily"
FAILOVER_HOSTNAME="Kevins-Mac-mini-2.local"
run --install-worker
assert_rc 0 "worker install on the Mini hostname exit 0"
FAILOVER_HOSTNAME="macbook-pro.local"
run --disable-daily
assert_rc 1 "wrong hostname disable exit 1"
has "$WORK/err" "hostname is not the Mini" "disable names the hostname"
[ -f "$HOME_DIR/Library/LaunchAgents/com.pati.cursor-agent-worker.plist" ] && ok "wrong host left the worker plist" || bad "wrong host removed the worker"

new_ready gitdir good
NOW=$(date +%s)
marker "failover-heartbeat: macbook-pro $NOW"
decoy="$WORK/decoy-repo"
mkdir -p "$decoy"
git -C "$decoy" init -q
git -C "$decoy" config user.email test@example.com
git -C "$decoy" config user.name Test
git -C "$decoy" commit -q --allow-empty -m "failover-release: macbook-pro $NOW"
HB_REF=HEAD
TEST_MODE=1
GIT_DIR_ENV="$decoy/.git"
run --enable-daily
assert_rc 1 "GIT_DIR does not retarget the guard"
has "$WORK/out" "guard: block" "home heartbeat still blocks"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" ] && ok "GIT_DIR wrote no daily plist" || bad "GIT_DIR wrote a daily plist"
GIT_DIR_ENV=""

new_ready cycle good
NOW=$(date +%s)
marker "failover-release: macbook-pro $NOW"
HB_REF=HEAD
TEST_MODE=1
run --install-worker --enable-daily
assert_rc 0 "enable before disable exit 0"
worker_body=$(cat "$HOME_DIR/Library/LaunchAgents/com.pati.cursor-agent-worker.plist")
run --dry-run --disable-daily
assert_rc 0 "dry-run disable exit 0"
has "$WORK/out" "disable_daily: would-remove" "dry-run disable would remove"
[ -f "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" ] && ok "dry-run disable left daily" || bad "dry-run disable removed daily"
run --disable-daily
assert_rc 0 "disable exit 0"
has "$WORK/out" "disable_daily: removed" "disable removed marked plists"
has "$WORK/out" "launchd: not started" "disable did not start launchd"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist" ] && ok "daily plist removed" || bad "daily plist remains"
[ ! -e "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-landing.plist" ] && ok "landing plist removed" || bad "landing plist remains"
[ -f "$HOME_DIR/Library/LaunchAgents/com.pati.cursor-agent-worker.plist" ] && ok "disable left the worker" || bad "disable removed the worker"
[ "$(cat "$HOME_DIR/Library/LaunchAgents/com.pati.cursor-agent-worker.plist")" = "$worker_body" ] && ok "worker plist bytes unchanged" || bad "worker plist changed"
run --disable-daily
assert_rc 0 "second disable exit 0"
has "$WORK/out" "disable_daily: absent" "second disable is absent"
no_secret "disable cycle"

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" = 0 ]

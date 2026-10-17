#!/bin/bash
# Offline drift check for ~/bin and the installed LaunchAgents.
# No real launchd, no network, no Shopify, no publish.
#   bash tests/test_self_apply.sh
# Syntax target is bash 3.2 (macOS /bin/bash).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SELF="$ROOT/scripts/genseo_self_apply.sh"
ARTICLE="$ROOT/deploy/grokbot-genseo-daily.sh"
LANDING="$ROOT/scripts/run_landing_daily.sh"
INSTALL="$ROOT/scripts/install_mac_daily_wrapper.sh"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/self-apply.XXXXXX")" || exit 1
PASS=0
FAIL=0
RC=0
HOLD_PIDS=""
LOGF="$WORK/none.log"
LAUNCH_LOG="$WORK/none-launch.log"
FIX=""
HOME_DIR=""
LABEL="com.pati.genseo-daily"
APPLY_ENV=""
START_STATUS="$(git -C "$ROOT" status --porcelain)"

cleanup() {
  local p
  for p in $HOLD_PIDS; do
    kill "$p" 2>/dev/null || true
    wait "$p" 2>/dev/null || true
  done
  if command -v pgrep >/dev/null 2>&1; then
    for p in $(pgrep -f 'bash /tmp/genseo-self-apply.' 2>/dev/null || true); do
      kill "$p" 2>/dev/null || true
    done
  fi
  rm -rf "$WORK"
}
trap cleanup EXIT

ok() { PASS=$((PASS + 1)); printf '  ok   %s\n' "$*"; }
bad() {
  FAIL=$((FAIL + 1))
  printf '  FAIL %s\n' "$*"
  if [ -f "${LOGF:-}" ]; then
    printf '    log: %s\n' "$(tr '\n' '|' <"$LOGF" | tail -c 900)"
  fi
  if [ -f "${LAUNCH_LOG:-}" ]; then
    printf '    launchctl: %s\n' "$(tr '\n' '|' <"$LAUNCH_LOG" | tail -c 500)"
  fi
  if [ -f "$WORK/out" ]; then
    printf '    stdout: %s\n' "$(tr '\n' '|' <"$WORK/out" | tail -c 400)"
  fi
  if [ -f "$WORK/err" ]; then
    printf '    stderr: %s\n' "$(tr '\n' '|' <"$WORK/err" | tail -c 400)"
  fi
  if [ -f "$WORK/child.err" ]; then
    printf '    child-err: %s\n' "$(tr '\n' '|' <"$WORK/child.err" | tail -c 400)"
  fi
}

has() {
  if [ -f "$1" ] && grep -F -q -- "$2" "$1"; then ok "$3"
  else bad "$3"; fi
}

lacks() {
  if [ -f "$1" ] && grep -F -q -- "$2" "$1"; then bad "$3"
  else ok "$3"; fi
}

count_of() {
  if [ -f "$1" ]; then
    grep -c -F -- "$2" "$1" 2>/dev/null || true
  else
    printf '0\n'
  fi
}

wait_file() {
  local path=$1 tries=$2 i=0
  while [ "$i" -lt "$tries" ]; do
    [ -f "$path" ] && return 0
    sleep 0.1
    i=$((i + 1))
  done
  return 1
}

wait_log() {
  local needle=$1 tries=$2 i=0
  while [ "$i" -lt "$tries" ]; do
    if [ -f "$LOGF" ] && grep -F -q -- "$needle" "$LOGF"; then
      return 0
    fi
    sleep 0.1
    i=$((i + 1))
  done
  return 1
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

py_mtime() {
  /usr/bin/python3 -c 'import os,sys; print(int(os.stat(sys.argv[1]).st_mtime))' "$1"
}

py_set_mtime() {
  /usr/bin/python3 -c 'import os,sys; os.utime(sys.argv[1], (1000000000, 1000000000))' "$1"
}

new_fix() {
  FIX="$WORK/fix-$1"
  HOME_DIR="$WORK/home-$1"
  LOGF="$WORK/log-$1"
  LAUNCH_LOG="$WORK/launch-$1.log"
  rm -rf "$FIX" "$HOME_DIR"
  mkdir -p "$FIX/deploy" "$FIX/scripts" "$FIX/state" "$HOME_DIR"
  cp "$ROOT/deploy/com.pati.genseo-daily.macbook.plist" "$FIX/deploy/"
  cp "$ROOT/deploy/com.pati.genseo-landing.macbook.plist" "$FIX/deploy/"
  cp "$ROOT/deploy/com.pati.genseo-landing.mini.plist" "$FIX/deploy/"
  printf '%s\n' '#!/bin/bash' 'echo daily-wrapper' >"$FIX/deploy/grokbot-genseo-daily.sh"
  chmod 755 "$FIX/deploy/grokbot-genseo-daily.sh"
  cp "$INSTALL" "$FIX/scripts/install_mac_daily_wrapper.sh"
  : >"$LOGF"
  : >"$LAUNCH_LOG"
  LABEL="com.pati.genseo-daily"
  APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook"
}

seed_wrapper_match() {
  mkdir -p "$HOME_DIR/bin"
  cp "$FIX/deploy/grokbot-genseo-daily.sh" "$HOME_DIR/bin/grokbot-genseo-daily.sh"
  chmod 755 "$HOME_DIR/bin/grokbot-genseo-daily.sh"
}

seed_plist() {
  local name=$1 body=$2
  mkdir -p "$HOME_DIR/Library/LaunchAgents"
  printf '%s\n' "$body" >"$HOME_DIR/Library/LaunchAgents/$name"
}

stamp_loaded() {
  local name=$1
  mkdir -p "$HOME_DIR/Library/LaunchAgents/.genseo-self-apply"
  cp "$HOME_DIR/Library/LaunchAgents/$name" \
    "$HOME_DIR/Library/LaunchAgents/.genseo-self-apply/${name%.plist}.loaded"
}

write_launchctl() {
  local mode=$1 dest=$2
  cat >"$dest" <<EOF
#!/bin/bash
printf '%s\n' "\$*" >> "$LAUNCH_LOG"
case "\$1" in
  print)
    if [ -f "$WORK/print-state" ]; then
      cat "$WORK/print-state"
    else
      printf 'state = waiting\n'
    fi
    exit 0
    ;;
  bootout)
    if [ "$mode" = "bootout-fail" ]; then exit 1; fi
    exit 0
    ;;
  bootstrap)
    if [ "$mode" = "fail-once" ]; then
      n=0
      if [ -f "$WORK/bs-count" ]; then n=\$(cat "$WORK/bs-count"); fi
      n=\$((n + 1))
      printf '%s\n' "\$n" > "$WORK/bs-count"
      if [ "\$n" -eq 1 ]; then exit 1; fi
      exit 0
    fi
    if [ "$mode" = "bootout-fail" ]; then exit 1; fi
    exit 0
    ;;
  *) exit 99 ;;
esac
EOF
  chmod 755 "$dest"
}

run_apply() {
  : >"$WORK/out"
  : >"$WORK/err"
  # APPLY_ENV is a list of KEY=value assignments with no spaces in the values.
  env -i \
    HOME="$HOME_DIR" \
    PATH="/usr/bin:/bin" \
    G="$FIX" \
    GENSEO_SELF_APPLY_LOG="$LOGF" \
    GENSEO_SELF_APPLY_SH="$SELF" \
    $APPLY_ENV \
    /bin/bash -c '
      set -uo pipefail
      . "$GENSEO_SELF_APPLY_SH"
      genseo_self_apply "$1"
      printf "APPLY_RC:%s\n" "$?"
      printf "CONTINUED\n"
    ' _ "$LABEL" >"$WORK/out" 2>"$WORK/err"
  RC=$?
}

assert_continued() {
  if [ "$RC" = 0 ]; then ok "$1 exits 0"
  else bad "$1 exits 0 (rc $RC)"; fi
  has "$WORK/out" "APPLY_RC:0" "$1 returns 0"
  has "$WORK/out" "CONTINUED" "$1 continues"
}

daily_plist() { printf '%s\n' "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-daily.plist"; }
landing_plist() { printf '%s\n' "$HOME_DIR/Library/LaunchAgents/com.pati.genseo-landing.plist"; }

echo "1. syntax, direct exec, call order, and no forbidden commands"
bash -n "$SELF" && ok "bash -n self-apply" || bad "bash -n self-apply"
bash -n "$ARTICLE" && ok "bash -n article wrapper" || bad "bash -n article wrapper"
bash -n "$LANDING" && ok "bash -n landing wrapper" || bad "bash -n landing wrapper"
bash -n "$INSTALL" && ok "bash -n installer" || bad "bash -n installer"
: >"$WORK/out"
: >"$WORK/err"
env -i HOME="$WORK/nohome" PATH="/usr/bin:/bin" /bin/bash "$SELF" >"$WORK/out" 2>"$WORK/err"
RC=$?
if [ "$RC" = 2 ]; then ok "direct exec exits 2"
else bad "direct exec exits 2 (rc $RC)"; fi
lacks "$WORK/out" "fast-forwarded" "direct exec does not fast-forward"
lacks "$WORK/out" "wrapper installed" "direct exec does not install"
[ ! -e "$WORK/nohome/bin" ] && ok "direct exec creates no wrapper" || bad "direct exec created a wrapper"
if awk '
  /^[[:space:]]*#/ { next }
  /for bad in/ { next }
  /sudo/ { print NR": "$0; bad=1 }
  /pmset/ { print NR": "$0; bad=1 }
  /kickstart/ { print NR": "$0; bad=1 }
  /shopify_publisher/ { print NR": "$0; bad=1 }
  /landing_publisher/ { print NR": "$0; bad=1 }
  /--live/ { print NR": "$0; bad=1 }
  /launchctl start/ { print NR": "$0; bad=1 }
  END { exit bad+0 }
' "$SELF"; then
  ok "self-apply does not kickstart, publish, or change power settings"
else
  bad "self-apply contains a forbidden command"
fi
if awk '
  /^[[:space:]]*#/ { next }
  /(bash|sh)[[:space:]].*(grokbot-genseo-daily|run_landing_daily|run_ticket_headless|run_landing_headless)/ { print NR": "$0; bad=1 }
  /genseo_published_today\.py/ { print NR": "$0; bad=1 }
  END { exit bad+0 }
' "$SELF"; then
  ok "self-apply does not execute a wrapper or read the live count"
else
  bad "self-apply executes a wrapper or reads the live count"
fi
order_code "$ARTICLE" 'genseo_sync_origin_main ' 'genseo_self_apply com.pati.genseo-daily' "article self-apply is after the sync"
order_code "$ARTICLE" 'genseo_self_apply com.pati.genseo-daily' '$(live_count)' "article self-apply is before the first live count"
order_code "$ARTICLE" 'GENSEO_MAIN_SYNCED:-}" = 1' 'genseo_self_apply com.pati.genseo-daily' "article self-apply stays inside the synced gate"
order_code "$LANDING" 'genseo_sync_origin_main ' 'genseo_self_apply com.pati.genseo-landing' "landing self-apply is after the sync"
order_code "$LANDING" 'genseo_self_apply com.pati.genseo-landing' 'guard; g=' "landing self-apply is before the first guard"
order_code "$LANDING" 'GENSEO_MAIN_SYNCED:-}" = 1' 'genseo_self_apply com.pati.genseo-landing' "landing self-apply stays inside the synced gate"
grep -F -q 'GENSEO_DAILY_TARGET:-5' "$ARTICLE" && ok "article target default stays 5" || bad "article target default changed"
grep -F -q 'GENSEO_LANDING_DRAFT=1' "$LANDING" && ok "landing stays draft-only" || bad "landing draft env missing"

echo "2. off a Mac, disabled, and sync dry-run copy nothing"
new_fix offmac
seed_plist "com.pati.genseo-daily.plist" "OLD-DAILY"
APPLY_ENV=""
run_apply
assert_continued "not a Mac"
has "$LOGF" "self-apply: skipped — not a Mac" "logs not a Mac"
lacks "$LOGF" "wrapper installed" "not a Mac does not install"
lacks "$LOGF" "plist copied" "not a Mac does not copy a plist"
[ "$(cat "$(daily_plist)")" = "OLD-DAILY" ] && ok "not a Mac leaves the plist" || bad "not a Mac changed the plist"
[ ! -e "$HOME_DIR/bin/grokbot-genseo-daily.sh" ] && ok "not a Mac leaves ~/bin absent" || bad "not a Mac wrote ~/bin"

new_fix disabled
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_SELF_APPLY_DISABLE=1 GENSEO_HOST_KIND=macbook"
run_apply
assert_continued "disabled"
has "$LOGF" "self-apply: disabled — continuing on the current setup" "logs disabled"
[ ! -e "$HOME_DIR/bin/grokbot-genseo-daily.sh" ] && ok "disabled writes no wrapper" || bad "disabled wrote a wrapper"
[ ! -e "$HOME_DIR/Library" ] && ok "disabled writes no LaunchAgent" || bad "disabled wrote LaunchAgents"

new_fix dry
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_SYNC_DRY_RUN=1 GENSEO_HOST_KIND=macbook"
run_apply
assert_continued "dry-run"
has "$LOGF" "self-apply: skipped — sync dry-run" "logs sync dry-run"
[ ! -e "$HOME_DIR/bin/grokbot-genseo-daily.sh" ] && ok "dry-run writes no wrapper" || bad "dry-run wrote a wrapper"

echo "3. host kind: explicit, name, model, and no system_profiler in test mode"
mkdir -p "$WORK/fakebin"
cat >"$WORK/fakebin/system_profiler" <<EOF
#!/bin/bash
printf '%s\n' called > "$WORK/profiler-called"
printf '%s\n' 'Model Name: Mac mini'
EOF
chmod 755 "$WORK/fakebin/system_profiler"
host_out() {
  env -i PATH="$WORK/fakebin:/usr/bin:/bin" GENSEO_SELF_APPLY_TEST=1 $1 \
    /bin/bash -c '
      set -uo pipefail
      . "$1"
      k=$(genseo_self_apply_host_kind)
      rc=$?
      printf "KIND:%s:%s\n" "$k" "$rc"
    ' _ "$SELF" >"$WORK/out" 2>"$WORK/err"
}
host_out ""
has "$WORK/out" "KIND::1" "test mode does not use the real machine"
[ ! -e "$WORK/profiler-called" ] && ok "test mode does not call system_profiler" || bad "system_profiler ran"
host_out "GENSEO_HOST_KIND=macbook"
has "$WORK/out" "KIND:macbook:0" "explicit macbook"
host_out "GENSEO_HOST_KIND=mini"
has "$WORK/out" "KIND:mini:0" "explicit mini"
host_out "GENSEO_HOST_KIND=laptop"
has "$WORK/out" "KIND::1" "garbage kind fails closed"
host_out "GENSEO_HOST_KIND=macbook GENSEO_SELF_APPLY_HOSTNAME=Kevins-Mac-mini-2"
has "$WORK/out" "KIND:macbook:0" "explicit kind wins over the hostname"
host_out "GENSEO_SELF_APPLY_HOSTNAME=Kevins-Mac-mini-2"
has "$WORK/out" "KIND:mini:0" "Kevins-Mac-mini-2 is a mini"
host_out "GENSEO_SELF_APPLY_HOSTNAME=Kevins-MacBook-Pro"
has "$WORK/out" "KIND:macbook:0" "Kevins-MacBook-Pro is a macbook"
host_out "GENSEO_SELF_APPLY_HOSTNAME=cloud-vm GENSEO_HOST_MODEL=Macmini9,1"
has "$WORK/out" "KIND:mini:0" "Macmini model is a mini"
host_out "GENSEO_SELF_APPLY_HOSTNAME=cloud-vm GENSEO_HOST_MODEL=MacBookPro18,3"
has "$WORK/out" "KIND:macbook:0" "MacBook model is a macbook"
host_out "GENSEO_SELF_APPLY_HOSTNAME=cloud-vm GENSEO_HOST_MODEL=Mac14,3"
has "$WORK/out" "KIND::1" "Mac14,3 is not treated as a Mini or a MacBook"
host_out "GENSEO_SELF_APPLY_HOSTNAME=Kevins-Mac-mini-2 GENSEO_HOST_MODEL=MacBookPro18,3"
has "$WORK/out" "KIND::1" "disagreeing name and model fail closed"

new_fix garbage
seed_plist "com.pati.genseo-daily.plist" "OLD-DAILY"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=laptop"
run_apply
assert_continued "unrecognized host"
has "$LOGF" "self-apply: wrapper installed" "unrecognized host still installs the wrapper"
has "$LOGF" "self-apply: host unrecognized — plist not changed" "unrecognized host logs plist not changed"
[ "$(cat "$(daily_plist)")" = "OLD-DAILY" ] && ok "unrecognized host leaves the plist" || bad "unrecognized host changed the plist"
cmp -s "$FIX/deploy/grokbot-genseo-daily.sh" "$HOME_DIR/bin/grokbot-genseo-daily.sh" \
  && ok "unrecognized host wrapper bytes match" || bad "unrecognized host wrapper bytes differ"

echo "4. plist safety: real files, RunAtLoad, and HOME"
safe_rc() {
  env -i HOME="$1" PATH="/usr/bin:/bin" GENSEO_SELF_APPLY_TEST="$2" \
    /bin/bash -c '
      set -uo pipefail
      . "$1"
      genseo_self_apply_plist_safe "$2" "$3"
      printf "SAFE_RC:%s\n" "$?"
    ' _ "$SELF" "$3" "$4" >"$WORK/out" 2>"$WORK/err"
}
safe_rc /tmp/not-in-plist 1 "$ROOT/deploy/com.pati.genseo-daily.macbook.plist" "com.pati.genseo-daily"
has "$WORK/out" "SAFE_RC:0" "macbook daily plist passes its label"
safe_rc /tmp/not-in-plist 1 "$ROOT/deploy/com.pati.genseo-daily.macbook.plist" "com.pati.genseo-landing"
has "$WORK/out" "SAFE_RC:3" "macbook daily plist fails the landing label"
safe_rc /tmp/not-in-plist 0 "$ROOT/deploy/com.pati.genseo-daily.macbook.plist" "com.pati.genseo-daily"
has "$WORK/out" "SAFE_RC:8" "production mode refuses a plist that does not name HOME"
mkdir -p "$WORK/home-safe"
sed "s#/Users/kevinkreative#$WORK/home-safe#g" \
  "$ROOT/deploy/com.pati.genseo-daily.macbook.plist" >"$WORK/home-safe.plist"
safe_rc "$WORK/home-safe" 0 "$WORK/home-safe.plist" "com.pati.genseo-daily"
has "$WORK/out" "SAFE_RC:0" "production mode accepts a plist that names HOME"

new_fix runat
seed_wrapper_match
seed_plist "com.pati.genseo-daily.plist" "OLD-DAILY"
cp "$FIX/deploy/com.pati.genseo-landing.macbook.plist" "$(landing_plist)"
stamp_loaded "com.pati.genseo-landing.plist"
sed 's/<false\/>/<true\/>/' "$FIX/deploy/com.pati.genseo-daily.macbook.plist" \
  >"$FIX/deploy/com.pati.genseo-daily.macbook.plist.tmp"
mv "$FIX/deploy/com.pati.genseo-daily.macbook.plist.tmp" \
  "$FIX/deploy/com.pati.genseo-daily.macbook.plist"
write_launchctl ok "$WORK/lc-runat"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook GENSEO_LAUNCHCTL=$WORK/lc-runat"
run_apply
assert_continued "RunAtLoad true"
has "$LOGF" "repo plist refused" "RunAtLoad true is refused"
[ "$(cat "$(daily_plist)")" = "OLD-DAILY" ] && ok "RunAtLoad true is not copied" || bad "RunAtLoad true was copied"
[ ! -s "$LAUNCH_LOG" ] && ok "RunAtLoad true does not call launchctl" || bad "RunAtLoad true called launchctl"

echo "5. wrapper unchanged, installed, and install failure"
new_fix wrap-same
seed_wrapper_match
py_set_mtime "$HOME_DIR/bin/grokbot-genseo-daily.sh"
cat >"$FIX/scripts/install_mac_daily_wrapper.sh" <<EOF
#!/bin/bash
printf '%s\n' called > "$WORK/installer-called"
exit 0
EOF
chmod 755 "$FIX/scripts/install_mac_daily_wrapper.sh"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook"
run_apply
assert_continued "wrapper unchanged"
has "$LOGF" "self-apply: wrapper unchanged" "logs wrapper unchanged"
[ ! -e "$WORK/installer-called" ] && ok "unchanged wrapper does not run the installer" || bad "installer ran for an unchanged wrapper"
[ "$(py_mtime "$HOME_DIR/bin/grokbot-genseo-daily.sh")" = "1000000000" ] \
  && ok "unchanged wrapper keeps its mtime" || bad "unchanged wrapper mtime moved"

new_fix wrap-new
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook"
run_apply
assert_continued "wrapper install"
has "$LOGF" "self-apply: wrapper installed" "logs wrapper installed"
[ -x "$HOME_DIR/bin/grokbot-genseo-daily.sh" ] && ok "installed wrapper is executable" || bad "installed wrapper is not executable"
cmp -s "$FIX/deploy/grokbot-genseo-daily.sh" "$HOME_DIR/bin/grokbot-genseo-daily.sh" \
  && ok "installed wrapper matches the checkout" || bad "installed wrapper bytes differ"
py_set_mtime "$HOME_DIR/bin/grokbot-genseo-daily.sh"
: >"$LOGF"
run_apply
has "$LOGF" "self-apply: wrapper unchanged" "second run logs wrapper unchanged"
[ "$(py_mtime "$HOME_DIR/bin/grokbot-genseo-daily.sh")" = "1000000000" ] \
  && ok "second run does not rewrite the wrapper" || bad "second run rewrote the wrapper"

new_fix wrap-fail
printf '%s\n' '#!/bin/bash' 'exit 1' >"$FIX/scripts/install_mac_daily_wrapper.sh"
chmod 755 "$FIX/scripts/install_mac_daily_wrapper.sh"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook"
run_apply
assert_continued "wrapper install failure"
has "$LOGF" "self-apply: wrapper install failed (rc 1) — continuing on the current setup" "logs the installer rc"
[ ! -e "$HOME_DIR/bin/grokbot-genseo-daily.sh" ] && ok "failed install leaves ~/bin absent" || bad "failed install wrote ~/bin"
[ ! -e "$HOME_DIR/Library" ] && ok "failed install creates no agent" || bad "failed install created an agent"

echo "6. unchanged, missing, and symlink plists"
new_fix same-plist
seed_wrapper_match
mkdir -p "$HOME_DIR/Library/LaunchAgents"
cp "$FIX/deploy/com.pati.genseo-daily.macbook.plist" "$(daily_plist)"
cp "$FIX/deploy/com.pati.genseo-landing.macbook.plist" "$(landing_plist)"
stamp_loaded "com.pati.genseo-daily.plist"
stamp_loaded "com.pati.genseo-landing.plist"
write_launchctl ok "$WORK/lc-same"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook GENSEO_LAUNCHCTL=$WORK/lc-same"
run_apply
assert_continued "plist unchanged"
has "$LOGF" "self-apply: com.pati.genseo-daily plist unchanged" "daily plist unchanged"
has "$LOGF" "self-apply: com.pati.genseo-landing plist unchanged" "landing plist unchanged"
[ ! -s "$LAUNCH_LOG" ] && ok "unchanged plists do not call launchctl" || bad "unchanged plists called launchctl"

new_fix missing-plist
seed_wrapper_match
write_launchctl ok "$WORK/lc-miss"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook GENSEO_LAUNCHCTL=$WORK/lc-miss"
run_apply
assert_continued "plist not installed"
has "$LOGF" "self-apply: com.pati.genseo-daily skipped — not installed" "daily not installed"
has "$LOGF" "self-apply: com.pati.genseo-landing skipped — not installed" "landing not installed"
[ ! -e "$HOME_DIR/Library" ] && ok "missing agents are not created" || bad "missing agents created a Library dir"

new_fix symlink
seed_wrapper_match
mkdir -p "$HOME_DIR/Library/LaunchAgents"
printf '%s\n' 'secret' >"$WORK/secret-target"
ln -s "$WORK/secret-target" "$(daily_plist)"
cp "$FIX/deploy/com.pati.genseo-landing.macbook.plist" "$(landing_plist)"
stamp_loaded "com.pati.genseo-landing.plist"
write_launchctl ok "$WORK/lc-link"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook GENSEO_LAUNCHCTL=$WORK/lc-link"
run_apply
assert_continued "symlink plist"
has "$LOGF" "self-apply: com.pati.genseo-daily installed plist is a symlink — not replaced" "symlink is refused"
[ -L "$(daily_plist)" ] && ok "symlink stays a symlink" || bad "symlink was replaced"
[ "$(cat "$WORK/secret-target")" = "secret" ] && ok "symlink target untouched" || bad "symlink target changed"

echo "7. MacBook copies both plists and defers only the running label"
new_fix macbook
seed_wrapper_match
seed_plist "com.pati.genseo-daily.plist" "OLD-DAILY"
seed_plist "com.pati.genseo-landing.plist" "OLD-LANDING"
write_launchctl ok "$WORK/lc-mac"
rm -f "$WORK/print-state" "$WORK/apply-done" "$WORK/release-child"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook GENSEO_LAUNCHCTL=$WORK/lc-mac GENSEO_SELF_APPLY_POLL_SEC=0.05 GENSEO_SELF_APPLY_SETTLE_SEC=0"
cat >"$WORK/grokbot-genseo-daily" <<EOF
#!/bin/bash
set -uo pipefail
mkdir -p "\$G/state/daily.lock"
printf '%s\n' "\$\$" > "\$G/state/daily.lock/pid"
. "\$GENSEO_SELF_APPLY_SH"
genseo_self_apply com.pati.genseo-daily
genseo_self_apply com.pati.genseo-daily
printf '%s\n' done > "$WORK/apply-done"
while [ ! -f "$WORK/release-child" ]; do
  sleep 0.05
done
exit 0
EOF
chmod 755 "$WORK/grokbot-genseo-daily"
: >"$WORK/child.out"
: >"$WORK/child.err"
env -i \
  HOME="$HOME_DIR" \
  PATH="/usr/bin:/bin" \
  G="$FIX" \
  GENSEO_SELF_APPLY_LOG="$LOGF" \
  GENSEO_SELF_APPLY_SH="$SELF" \
  $APPLY_ENV \
  /bin/bash "$WORK/grokbot-genseo-daily" >"$WORK/child.out" 2>"$WORK/child.err" &
CHILD=$!
HOLD_PIDS="$HOLD_PIDS $CHILD"
if wait_file "$WORK/apply-done" 80; then ok "macbook apply finished while the job was alive"
else bad "macbook apply did not finish"; fi
sleep 0.5
if grep -F -q "com.pati.genseo-landing.plist" "$LAUNCH_LOG" \
  && grep -F -q "bootstrap" "$LAUNCH_LOG"; then
  ok "idle landing label was reloaded during the article job"
else
  bad "idle landing label was not reloaded during the article job"
fi
if grep -F -q "com.pati.genseo-daily.plist" "$LAUNCH_LOG"; then
  bad "running article label was reloaded in-process"
else
  ok "running article label was not reloaded in-process"
fi
has "$LOGF" "self-apply: com.pati.genseo-daily reload deferred until pid" "daily reload is deferred"
has "$LOGF" "self-apply: com.pati.genseo-daily reload already queued" "second call does not queue another helper"
[ "$(count_of "$LOGF" "self-apply: com.pati.genseo-daily reload deferred until pid")" = "1" ] \
  && ok "one deferred helper" || bad "deferred helper count was not 1"
cmp -s "$FIX/deploy/com.pati.genseo-daily.macbook.plist" "$(daily_plist)" \
  && ok "macbook daily bytes were copied" || bad "macbook daily bytes were not copied"
cmp -s "$FIX/deploy/com.pati.genseo-landing.macbook.plist" "$(landing_plist)" \
  && ok "macbook landing bytes were copied" || bad "macbook landing bytes were not copied"
printf '%s\n' go >"$WORK/release-child"
wait "$CHILD" 2>/dev/null || true
HOLD_PIDS=""
if wait_log "self-apply: com.pati.genseo-daily reloaded" 80; then
  ok "daily reload runs after the job exits"
else
  bad "daily reload did not run after the job exits"
fi
daily_boots=$(grep -c 'bootout .*com\.pati\.genseo-daily\.plist' "$LAUNCH_LOG" || true)
daily_straps=$(grep -c 'bootstrap .*com\.pati\.genseo-daily\.plist' "$LAUNCH_LOG" || true)
land_straps=$(grep -c 'bootstrap .*com\.pati\.genseo-landing\.plist' "$LAUNCH_LOG" || true)
[ "$daily_boots" = "1" ] && ok "daily bootout once" || bad "daily bootout count was $daily_boots"
[ "$daily_straps" = "1" ] && ok "daily bootstrap once" || bad "daily bootstrap count was $daily_straps"
[ "$land_straps" = "1" ] && ok "landing bootstrap once" || bad "landing bootstrap count was $land_straps"
lacks "$LAUNCH_LOG" "kickstart" "helper does not kickstart"
/usr/bin/python3 -c 'import plistlib,sys; d=plistlib.load(open(sys.argv[1],"rb")); sys.exit(0 if d.get("RunAtLoad") is False and not d.get("KeepAlive") else 1)' \
  "$(daily_plist)" && ok "reloaded daily plist keeps RunAtLoad false" || bad "reloaded daily plist changed RunAtLoad"
cmp -s "$(daily_plist)" "$HOME_DIR/Library/LaunchAgents/.genseo-self-apply/com.pati.genseo-daily.loaded" \
  && ok "daily load record matches the installed plist" || bad "daily load record mismatch"
cmp -s "$(landing_plist)" "$HOME_DIR/Library/LaunchAgents/.genseo-self-apply/com.pati.genseo-landing.loaded" \
  && ok "landing load record matches the installed plist" || bad "landing load record mismatch"
[ "$(cat "$HOME_DIR/Library/LaunchAgents/.genseo-self-apply/com.pati.genseo-daily.plist.bak")" = "OLD-DAILY" ] \
  && ok "daily backup is the previous plist" || bad "daily backup is not the previous plist"
[ -d "$FIX/state/daily.lock" ] && ok "self-apply does not remove the article lock" || bad "article lock was removed"
before_lines=$(wc -l <"$LAUNCH_LOG" | tr -d ' ')
: >"$LOGF"
env -i \
  HOME="$HOME_DIR" PATH="/usr/bin:/bin" G="$FIX" \
  GENSEO_SELF_APPLY_LOG="$LOGF" GENSEO_SELF_APPLY_SH="$SELF" \
  GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook \
  GENSEO_LAUNCHCTL="$WORK/lc-mac" \
  /bin/bash -c '
    set -uo pipefail
    . "$GENSEO_SELF_APPLY_SH"
    genseo_self_apply com.pati.genseo-daily
    printf "CONTINUED\n"
  ' >"$WORK/out" 2>"$WORK/err"
RC=$?
if [ "$RC" = 0 ]; then ok "second macbook apply exits 0"
else bad "second macbook apply exits 0 (rc $RC)"; fi
has "$LOGF" "self-apply: com.pati.genseo-daily plist unchanged" "second run leaves daily"
has "$LOGF" "self-apply: com.pati.genseo-landing plist unchanged" "second run leaves landing"
after_lines=$(wc -l <"$LAUNCH_LOG" | tr -d ' ')
[ "$before_lines" = "$after_lines" ] && ok "second run does not call launchctl" || bad "second run called launchctl"

echo "8. Mini copies the landing plist and does not install an article agent"
new_fix mini
seed_wrapper_match
seed_plist "com.pati.genseo-daily.plist" "OLD-DAILY"
seed_plist "com.pati.genseo-landing.plist" "OLD-LANDING"
write_launchctl ok "$WORK/lc-mini"
rm -f "$WORK/apply-done" "$WORK/release-child"
LABEL="com.pati.genseo-landing"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=mini GENSEO_LAUNCHCTL=$WORK/lc-mini GENSEO_SELF_APPLY_POLL_SEC=0.05 GENSEO_SELF_APPLY_SETTLE_SEC=0"
cat >"$WORK/run_landing_daily.sh" <<EOF
#!/bin/bash
set -uo pipefail
mkdir -p "\$G/state/landing-daily.lock"
printf '%s\n' "\$\$" > "\$G/state/landing-daily.lock.owner"
. "\$GENSEO_SELF_APPLY_SH"
genseo_self_apply com.pati.genseo-landing
printf '%s\n' done > "$WORK/apply-done"
while [ ! -f "$WORK/release-child" ]; do
  sleep 0.05
done
exit 0
EOF
chmod 755 "$WORK/run_landing_daily.sh"
env -i \
  HOME="$HOME_DIR" PATH="/usr/bin:/bin" G="$FIX" \
  GENSEO_SELF_APPLY_LOG="$LOGF" GENSEO_SELF_APPLY_SH="$SELF" $APPLY_ENV \
  /bin/bash "$WORK/run_landing_daily.sh" >"$WORK/child.out" 2>"$WORK/child.err" &
CHILD=$!
HOLD_PIDS="$HOLD_PIDS $CHILD"
if wait_file "$WORK/apply-done" 80; then ok "mini apply finished"
else bad "mini apply did not finish"; fi
has "$LOGF" "self-apply: com.pati.genseo-daily skipped — no mini plist until failover-release" "mini has no article plist"
[ "$(cat "$(daily_plist)")" = "OLD-DAILY" ] && ok "mini leaves the article agent bytes" || bad "mini changed the article agent"
cmp -s "$FIX/deploy/com.pati.genseo-landing.mini.plist" "$(landing_plist)" \
  && ok "mini landing bytes were copied" || bad "mini landing bytes were not copied"
if cmp -s "$FIX/deploy/com.pati.genseo-landing.macbook.plist" "$(landing_plist)"; then
  bad "mini received the MacBook landing plist"
else
  ok "mini did not receive the MacBook landing plist"
fi
if grep -F -q "com.pati.genseo-landing.plist" "$LAUNCH_LOG"; then
  bad "running mini landing label was reloaded in-process"
else
  ok "running mini landing label was not reloaded in-process"
fi
printf '%s\n' go >"$WORK/release-child"
wait "$CHILD" 2>/dev/null || true
HOLD_PIDS=""
if wait_log "self-apply: com.pati.genseo-landing reloaded" 80; then
  ok "mini landing reload runs after the job exits"
else
  bad "mini landing reload did not run after the job exits"
fi
[ -d "$FIX/state/landing-daily.lock" ] && ok "self-apply does not remove the landing lock" || bad "landing lock was removed"

echo "9. the other lane is left alone while it is busy"
new_fix busy-lock
seed_wrapper_match
mkdir -p "$HOME_DIR/Library/LaunchAgents"
cp "$FIX/deploy/com.pati.genseo-daily.macbook.plist" "$(daily_plist)"
stamp_loaded "com.pati.genseo-daily.plist"
seed_plist "com.pati.genseo-landing.plist" "OLD-LANDING"
mkdir -p "$FIX/state/landing-daily.lock"
sleep 60 &
SLEEPER=$!
HOLD_PIDS="$HOLD_PIDS $SLEEPER"
printf '%s\n' "$SLEEPER" >"$FIX/state/landing-daily.lock.owner"
write_launchctl ok "$WORK/lc-busy"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook GENSEO_LAUNCHCTL=$WORK/lc-busy"
run_apply
assert_continued "busy lock"
has "$LOGF" "self-apply: com.pati.genseo-landing left in place — lock held" "landing lock is left in place"
[ "$(cat "$(landing_plist)")" = "OLD-LANDING" ] && ok "busy landing plist is not copied" || bad "busy landing plist was copied"
lacks "$LAUNCH_LOG" "com.pati.genseo-landing.plist" "busy landing label is not reloaded"
kill "$SLEEPER" 2>/dev/null || true
wait "$SLEEPER" 2>/dev/null || true
HOLD_PIDS=""
[ -d "$FIX/state/landing-daily.lock" ] && ok "busy lock directory stays" || bad "busy lock directory was removed"

new_fix busy-nopid
seed_wrapper_match
mkdir -p "$HOME_DIR/Library/LaunchAgents"
cp "$FIX/deploy/com.pati.genseo-daily.macbook.plist" "$(daily_plist)"
stamp_loaded "com.pati.genseo-daily.plist"
seed_plist "com.pati.genseo-landing.plist" "OLD-LANDING"
mkdir -p "$FIX/state/landing-daily.lock"
write_launchctl ok "$WORK/lc-nopid"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook GENSEO_LAUNCHCTL=$WORK/lc-nopid"
run_apply
assert_continued "lock without pid"
has "$LOGF" "self-apply: com.pati.genseo-landing left in place — lock held" "missing owner is fail-closed"
[ "$(cat "$(landing_plist)")" = "OLD-LANDING" ] && ok "missing owner does not copy" || bad "missing owner copied"

new_fix busy-job
seed_wrapper_match
mkdir -p "$HOME_DIR/Library/LaunchAgents"
cp "$FIX/deploy/com.pati.genseo-daily.macbook.plist" "$(daily_plist)"
stamp_loaded "com.pati.genseo-daily.plist"
seed_plist "com.pati.genseo-landing.plist" "OLD-LANDING"
sleep 60 &
SLEEPER=$!
HOLD_PIDS="$HOLD_PIDS $SLEEPER"
cat >"$WORK/ps-landing" <<EOF
#!/bin/bash
printf '%s %s\n' "$SLEEPER" "bash /tmp/run_landing_daily.sh"
exit 0
EOF
chmod 755 "$WORK/ps-landing"
write_launchctl ok "$WORK/lc-job"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook GENSEO_LAUNCHCTL=$WORK/lc-job GENSEO_SELF_APPLY_PS=$WORK/ps-landing"
run_apply
assert_continued "landing job visible"
has "$LOGF" "self-apply: com.pati.genseo-landing left in place — a job is running" "visible landing job is left in place"
[ "$(cat "$(landing_plist)")" = "OLD-LANDING" ] && ok "visible job does not copy" || bad "visible job copied"
kill "$SLEEPER" 2>/dev/null || true
wait "$SLEEPER" 2>/dev/null || true
HOLD_PIDS=""

new_fix busy-ps
seed_wrapper_match
mkdir -p "$HOME_DIR/Library/LaunchAgents"
cp "$FIX/deploy/com.pati.genseo-daily.macbook.plist" "$(daily_plist)"
stamp_loaded "com.pati.genseo-daily.plist"
seed_plist "com.pati.genseo-landing.plist" "OLD-LANDING"
printf '%s\n' '#!/bin/bash' 'exit 1' >"$WORK/ps-fail"
chmod 755 "$WORK/ps-fail"
write_launchctl ok "$WORK/lc-ps"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook GENSEO_LAUNCHCTL=$WORK/lc-ps GENSEO_SELF_APPLY_PS=$WORK/ps-fail"
run_apply
assert_continued "ps unreadable"
has "$LOGF" "self-apply: com.pati.genseo-landing left in place — process list unreadable" "unreadable ps is fail-closed"
[ "$(cat "$(landing_plist)")" = "OLD-LANDING" ] && ok "unreadable ps does not copy" || bad "unreadable ps copied"

echo "10. reload failure restores the previous plist"
new_fix fail-once
seed_wrapper_match
mkdir -p "$HOME_DIR/Library/LaunchAgents"
cp "$FIX/deploy/com.pati.genseo-daily.macbook.plist" "$(daily_plist)"
stamp_loaded "com.pati.genseo-daily.plist"
seed_plist "com.pati.genseo-landing.plist" "OLD-LANDING"
rm -f "$WORK/bs-count" "$WORK/print-state"
write_launchctl fail-once "$WORK/lc-once"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook GENSEO_LAUNCHCTL=$WORK/lc-once"
run_apply
assert_continued "bootstrap fails once"
has "$LOGF" "self-apply: com.pati.genseo-landing reload failed — restored the previous plist — continuing on the previous launchd setup" "logs the restored plist"
[ "$(cat "$(landing_plist)")" = "OLD-LANDING" ] && ok "failed bootstrap restores the old bytes" || bad "failed bootstrap left the new bytes"
straps=$(grep -c 'bootstrap .*com\.pati\.genseo-landing\.plist' "$LAUNCH_LOG" || true)
[ "$straps" = "2" ] && ok "restore bootstraps the previous plist" || bad "bootstrap count was $straps"
if [ -f "$HOME_DIR/Library/LaunchAgents/.genseo-self-apply/com.pati.genseo-landing.loaded" ] \
  && cmp -s "$FIX/deploy/com.pati.genseo-landing.macbook.plist" \
    "$HOME_DIR/Library/LaunchAgents/.genseo-self-apply/com.pati.genseo-landing.loaded"; then
  bad "failed reload recorded the new plist as loaded"
else
  ok "failed reload does not record the new plist as loaded"
fi

new_fix not-loaded
seed_wrapper_match
mkdir -p "$HOME_DIR/Library/LaunchAgents"
cp "$FIX/deploy/com.pati.genseo-daily.macbook.plist" "$(daily_plist)"
stamp_loaded "com.pati.genseo-daily.plist"
seed_plist "com.pati.genseo-landing.plist" "OLD-LANDING"
write_launchctl bootout-fail "$WORK/lc-none"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook GENSEO_LAUNCHCTL=$WORK/lc-none"
run_apply
assert_continued "bootout fails"
has "$LOGF" "self-apply: com.pati.genseo-landing reload failed — launchd was not switched — continuing on the previous launchd setup" "logs that launchd was not switched"
[ "$(cat "$(landing_plist)")" = "OLD-LANDING" ] && ok "unloaded failure restores the file" || bad "unloaded failure left the new file"
straps=$(grep -c 'bootstrap .*com\.pati\.genseo-landing\.plist' "$LAUNCH_LOG" || true)
boots=$(grep -c 'bootout .*com\.pati\.genseo-landing\.plist' "$LAUNCH_LOG" || true)
[ "$straps" = "1" ] && ok "a label that was not loaded is not bootstrapped" || bad "bootstrap count was $straps"
[ "$boots" = "1" ] && ok "bootout was tried once" || bad "bootout count was $boots"

echo "11. launchd running, this process's lock, and a dead lock pid"
new_fix running
seed_wrapper_match
mkdir -p "$HOME_DIR/Library/LaunchAgents"
cp "$FIX/deploy/com.pati.genseo-daily.macbook.plist" "$(daily_plist)"
stamp_loaded "com.pati.genseo-daily.plist"
seed_plist "com.pati.genseo-landing.plist" "OLD-LANDING"
printf '%s\n' 'state = running' >"$WORK/print-state"
write_launchctl ok "$WORK/lc-run"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook GENSEO_LAUNCHCTL=$WORK/lc-run"
run_apply
assert_continued "launchd running"
has "$LOGF" "self-apply: com.pati.genseo-landing reload skipped — launchd reports it running" "running label is not reloaded"
lacks "$LAUNCH_LOG" "bootout" "running label is not bootout"
cmp -s "$FIX/deploy/com.pati.genseo-landing.macbook.plist" "$(landing_plist)" \
  && ok "running label still received the new bytes" || bad "running label did not receive the new bytes"
[ ! -f "$HOME_DIR/Library/LaunchAgents/.genseo-self-apply/com.pati.genseo-landing.loaded" ] \
  && ok "running label does not write a load record" || bad "running label wrote a load record"
rm -f "$WORK/print-state"

new_fix self-lock
seed_wrapper_match
mkdir -p "$HOME_DIR/Library/LaunchAgents"
cp "$FIX/deploy/com.pati.genseo-daily.macbook.plist" "$(daily_plist)"
write_launchctl ok "$WORK/lc-self"
env -i \
  HOME="$HOME_DIR" PATH="/usr/bin:/bin" G="$FIX" \
  GENSEO_SELF_APPLY_LOG="$LOGF" GENSEO_SELF_APPLY_TEST=1 \
  GENSEO_LAUNCHCTL="$WORK/lc-self" \
  /bin/bash -c '
    set -uo pipefail
    . "$1"
    mkdir -p "$G/state/daily.lock"
    printf "%s\n" "$$" > "$G/state/daily.lock/pid"
    genseo_self_apply_perform_reload \
      com.pati.genseo-daily \
      "$HOME/Library/LaunchAgents/com.pati.genseo-daily.plist" \
      "$HOME/Library/LaunchAgents/.genseo-self-apply/com.pati.genseo-daily.plist.bak" \
      "$HOME/Library/LaunchAgents/.genseo-self-apply/com.pati.genseo-daily.loaded" \
      daily "$G"
    printf "APPLY_RC:%s\n" "$?"
    printf "CONTINUED\n"
  ' _ "$SELF" >"$WORK/out" 2>"$WORK/err"
RC=$?
if [ "$RC" = 0 ]; then ok "in-process reload exits 0"
else bad "in-process reload exits 0 (rc $RC)"; fi
has "$WORK/out" "CONTINUED" "in-process reload continues"
has "$LOGF" "self-apply: com.pati.genseo-daily reload skipped — this process holds the lane lock" "this process cannot bootout its own label"
lacks "$LAUNCH_LOG" "bootout" "this process does not bootout"
[ -d "$FIX/state/daily.lock" ] && ok "in-process check leaves the lock" || bad "in-process check removed the lock"

new_fix dead-pid
seed_wrapper_match
mkdir -p "$HOME_DIR/Library/LaunchAgents"
cp "$FIX/deploy/com.pati.genseo-daily.macbook.plist" "$(daily_plist)"
stamp_loaded "com.pati.genseo-daily.plist"
seed_plist "com.pati.genseo-landing.plist" "OLD-LANDING"
dead=300000
while kill -0 "$dead" 2>/dev/null; do
  dead=$((dead + 1))
done
mkdir -p "$FIX/state/landing-daily.lock"
printf '%s\n' "$dead" >"$FIX/state/landing-daily.lock.owner"
write_launchctl ok "$WORK/lc-dead"
APPLY_ENV="GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook GENSEO_LAUNCHCTL=$WORK/lc-dead"
run_apply
assert_continued "dead lock pid"
has "$LOGF" "self-apply: com.pati.genseo-landing reloaded" "a dead lock pid does not block the other lane"
cmp -s "$FIX/deploy/com.pati.genseo-landing.macbook.plist" "$(landing_plist)" \
  && ok "dead lock pid still copies" || bad "dead lock pid did not copy"

echo "12. a job that does not exit is not reloaded when the wait expires"
new_fix timeout
seed_wrapper_match
seed_plist "com.pati.genseo-daily.plist" "OLD-DAILY"
cp "$FIX/deploy/com.pati.genseo-landing.macbook.plist" "$(landing_plist)"
stamp_loaded "com.pati.genseo-landing.plist"
write_launchctl ok "$WORK/lc-time"
rm -f "$WORK/print-state"
cat >"$WORK/grokbot-genseo-daily" <<EOF
#!/bin/bash
set -uo pipefail
mkdir -p "\$G/state/daily.lock"
printf '%s\n' "\$\$" > "\$G/state/daily.lock/pid"
. "\$GENSEO_SELF_APPLY_SH"
genseo_self_apply com.pati.genseo-daily
sleep 30
EOF
chmod 755 "$WORK/grokbot-genseo-daily"
env -i \
  HOME="$HOME_DIR" PATH="/usr/bin:/bin" G="$FIX" \
  GENSEO_SELF_APPLY_LOG="$LOGF" GENSEO_SELF_APPLY_SH="$SELF" \
  GENSEO_SELF_APPLY_TEST=1 GENSEO_INSTALL_WRAPPER_TEST=1 GENSEO_HOST_KIND=macbook \
  GENSEO_LAUNCHCTL="$WORK/lc-time" \
  GENSEO_SELF_APPLY_POLL_SEC=0.1 GENSEO_SELF_APPLY_SETTLE_SEC=0 \
  GENSEO_SELF_APPLY_DEADLINE_SEC=2 \
  /bin/bash "$WORK/grokbot-genseo-daily" >"$WORK/child.out" 2>"$WORK/child.err" &
CHILD=$!
HOLD_PIDS="$HOLD_PIDS $CHILD"
if wait_log "reload wait timed out — not reloading while the job may still be running" 80; then
  ok "wait timeout is logged"
else
  bad "wait timeout was not logged"
fi
lacks "$LAUNCH_LOG" "bootout" "timeout does not bootout"
kill "$CHILD" 2>/dev/null || true
wait "$CHILD" 2>/dev/null || true
HOLD_PIDS=""

echo "13. repo status is unchanged"
end_status="$(git -C "$ROOT" status --porcelain)"
if [ "$end_status" = "$START_STATUS" ]; then ok "self-apply tests do not write into the repo"
else bad "self-apply tests changed the repo status"; printf '    %s\n' "$end_status"; fi

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" = 0 ]

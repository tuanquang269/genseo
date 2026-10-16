#!/bin/bash
# Offline install of the launchd daily wrapper into a temp HOME.
# No launchd, no network, no Shopify.
#   bash tests/test_install_mac_daily_wrapper.sh
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL="$ROOT/scripts/install_mac_daily_wrapper.sh"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/install-mac-wrapper.XXXXXX")" || exit 1
trap 'rm -rf "$WORK"' EXIT
PASS=0
FAIL=0

ok() { PASS=$((PASS + 1)); printf '  ok   %s\n' "$*"; }
bad() { FAIL=$((FAIL + 1)); printf '  FAIL %s\n' "$*"; }

# run_install <home> <genseo_home> <test_mode:0|1> -- [args...]
# test_mode 1 sets GENSEO_INSTALL_WRAPPER_TEST so the copy can run off Darwin.
run_install() {
  local home="$1" ghome="$2" testflag="$3"
  shift 3
  [ "${1:-}" = "--" ] && shift
  : >"$WORK/out"
  : >"$WORK/err"
  if [ "$testflag" = 1 ]; then
    env -i HOME="$home" PATH="/usr/bin:/bin" GENSEO_HOME="$ghome" GENSEO_INSTALL_WRAPPER_TEST=1 \
      /bin/bash "$INSTALL" "$@" >"$WORK/out" 2>"$WORK/err"
  else
    env -i HOME="$home" PATH="/usr/bin:/bin" GENSEO_HOME="$ghome" \
      /bin/bash "$INSTALL" "$@" >"$WORK/out" 2>"$WORK/err"
  fi
  RC=$?
}

assert_rc() { # assert_rc <want> <label>
  if [ "$RC" = "$1" ]; then ok "$2"
  else bad "$2 (rc $RC, want $1)"; printf '    stdout: %s\n' "$(tr '\n' '|' <"$WORK/out")"; printf '    stderr: %s\n' "$(tr '\n' '|' <"$WORK/err")"; fi
}

has() { # has <file> <needle> <label>
  if grep -F -q -- "$2" "$1"; then ok "$3"
  else bad "$3"; fi
}

lacks() { # lacks <file> <needle> <label>
  if grep -F -q -- "$2" "$1"; then bad "$3"
  else ok "$3"; fi
}

new_home() {
  HOME_DIR="$WORK/home-$1"
  rm -rf "$HOME_DIR"
  mkdir -p "$HOME_DIR"
}

# Checkout whose wrapper names the lock helpers.
fixture() { # fixture <name> <with_helpers:0|1> <mode>
  FIX="$WORK/fix-$1"
  rm -rf "$FIX"
  mkdir -p "$FIX/deploy" "$FIX/scripts"
  cat >"$FIX/deploy/grokbot-genseo-daily.sh" <<'EOF'
#!/bin/bash
# sources scripts/genseo_daily_lock.sh and scripts/genseo_group_timeout.sh
echo daily
EOF
  chmod "$3" "$FIX/deploy/grokbot-genseo-daily.sh"
  if [ "$2" = 1 ]; then
    printf '%s\n' 'lock' >"$FIX/scripts/genseo_daily_lock.sh"
    printf '%s\n' 'timeout' >"$FIX/scripts/genseo_group_timeout.sh"
  fi
}

echo "1. non-Mac write is refused and creates nothing"
fixture refuse 1 644
new_home refuse
env -i HOME="$HOME_DIR" PATH="/usr/bin:/bin" GENSEO_HOME="$FIX" \
  GENSEO_INSTALL_WRAPPER_PRETEND_OS=Linux \
  /bin/bash "$INSTALL" >"$WORK/out" 2>"$WORK/err"
RC=$?
assert_rc 2 "exit 2 when the host is not treated as a Mac"
[ ! -e "$HOME_DIR/bin/grokbot-genseo-daily.sh" ] && ok "no dest file" || bad "dest was written"
[ ! -d "$HOME_DIR/Library" ] && ok "no LaunchAgents dir" || bad "Library was created"
has "$WORK/err" "refusing:" "stderr says refusing"

echo "2. --dry-run under a temp HOME writes nothing and reports helpers"
fixture dry 1 755
new_home dry
run_install "$HOME_DIR" "$FIX" 0 -- --dry-run
assert_rc 0 "dry-run exit 0"
has "$WORK/out" "dry-run: yes" "dry-run flag"
has "$WORK/out" "executable: not written" "not written"
has "$WORK/out" "helper scripts/genseo_daily_lock.sh: present" "lock helper present"
has "$WORK/out" "helper scripts/genseo_group_timeout.sh: present" "timeout helper present"
has "$WORK/out" "launchd: not started" "launchd not started"
has "$WORK/out" "plist: not copied" "dry-run says the plist is not copied"
[ ! -e "$HOME_DIR/bin" ] && ok "bin dir not created" || bad "bin dir created"

echo "3. dry-run refuses a lock-PID wrapper whose helpers are absent"
fixture drymiss 0 755
new_home drymiss
run_install "$HOME_DIR" "$FIX" 0 -- --dry-run
assert_rc 1 "dry-run exit 1 when helpers required and missing"
has "$WORK/out" "helper scripts/genseo_daily_lock.sh: MISSING" "reports MISSING lock helper"
has "$WORK/err" "Nothing was copied" "nothing copied"
[ ! -e "$HOME_DIR/bin/grokbot-genseo-daily.sh" ] && ok "dry-run left no dest" || bad "dry-run wrote dest"

echo "4. test-mode copy into a temp HOME: executable, byte match, helpers present"
fixture apply 1 644
new_home apply
src_sum=$(cksum "$FIX/deploy/grokbot-genseo-daily.sh")
run_install "$HOME_DIR" "$FIX" 1 --
assert_rc 0 "copy exit 0"
dest="$HOME_DIR/bin/grokbot-genseo-daily.sh"
[ -f "$dest" ] && ok "dest exists" || bad "dest missing"
[ -x "$dest" ] && ok "dest executable (source was 644)" || bad "dest not executable"
cmp -s "$FIX/deploy/grokbot-genseo-daily.sh" "$dest" && ok "bytes match source" || bad "bytes differ"
[ "$src_sum" = "$(cksum "$FIX/deploy/grokbot-genseo-daily.sh")" ] && ok "source unchanged" || bad "source changed"
has "$WORK/out" "executable: yes" "says executable"
has "$WORK/out" "launchd: not started" "says launchd not started"
has "$WORK/out" "plist: not copied" "copy says the plist is not copied"
has "$WORK/out" "helper scripts/genseo_daily_lock.sh: present" "present lock helper"
has "$WORK/out" "helper scripts/genseo_group_timeout.sh: present" "present timeout helper"
lacks "$WORK/out" "note: this wrapper does not require" "no transition note when helpers exist"

echo "5. second copy replaces the dest and does not follow a symlink"
printf '%s\n' '#!/bin/bash' '# sources scripts/genseo_daily_lock.sh' 'echo two' >>"$FIX/deploy/grokbot-genseo-daily.sh"
run_install "$HOME_DIR" "$FIX" 1 --
assert_rc 0 "second copy exit 0"
cmp -s "$FIX/deploy/grokbot-genseo-daily.sh" "$dest" && ok "dest replaced" || bad "dest not replaced"
rm -f "$dest"
ln -s "$WORK/outside-target" "$dest"
printf '%s\n' 'original' >"$WORK/outside-target"
run_install "$HOME_DIR" "$FIX" 1 --
assert_rc 1 "symlink dest refused"
[ "$(cat "$WORK/outside-target")" = "original" ] && ok "symlink target untouched" || bad "symlink target changed"
[ -L "$dest" ] && ok "symlink left in place" || bad "symlink removed"

echo "6. GENSEO_HOME defaults to ~/genseo inside the temp HOME"
new_home default
mkdir -p "$HOME_DIR/genseo/deploy"
printf '%s\n' '#!/bin/bash' 'echo default-home' >"$HOME_DIR/genseo/deploy/grokbot-genseo-daily.sh"
out="$WORK/out"
err="$WORK/err"
env -i HOME="$HOME_DIR" PATH="/usr/bin:/bin" GENSEO_INSTALL_WRAPPER_TEST=1 \
  /bin/bash "$INSTALL" >"$out" 2>"$err"
RC=$?
assert_rc 0 "default GENSEO_HOME exit 0"
cmp -s "$HOME_DIR/genseo/deploy/grokbot-genseo-daily.sh" "$HOME_DIR/bin/grokbot-genseo-daily.sh" \
  && ok "copied from ~/genseo" || bad "did not copy from ~/genseo"
has "$WORK/out" "helper scripts/genseo_daily_lock.sh: MISSING" "default checkout reports MISSING"
has "$WORK/out" "note: this wrapper does not require" "transition note when wrapper does not need helpers"

echo "7. missing checkout fails before creating ~/bin"
new_home missing
run_install "$HOME_DIR" "$WORK/no-such-checkout" 1 --
assert_rc 1 "missing source exit 1"
[ ! -e "$HOME_DIR/bin" ] && ok "no bin on missing source" || bad "bin created for missing source"
has "$WORK/err" "missing source:" "names missing source"

echo "8. real deploy/grokbot-genseo-daily.sh copies under a temp HOME"
new_home real
if grep -q 'genseo_daily_lock.sh' "$ROOT/deploy/grokbot-genseo-daily.sh" \
  || grep -q 'genseo_group_timeout.sh' "$ROOT/deploy/grokbot-genseo-daily.sh"; then
  real_needs=1
else
  real_needs=0
fi
real_missing=0
for rel in scripts/genseo_daily_lock.sh scripts/genseo_group_timeout.sh; do
  if [ ! -f "$ROOT/$rel" ]; then real_missing=1; fi
done
run_install "$HOME_DIR" "$ROOT" 1 --
if [ "$real_needs" = 1 ] && [ "$real_missing" = 1 ]; then
  assert_rc 1 "real wrapper needs helpers that are absent"
  [ ! -e "$HOME_DIR/bin/grokbot-genseo-daily.sh" ] && ok "real copy withheld" || bad "real copy written without helpers"
else
  assert_rc 0 "real wrapper copy exit 0"
  [ -x "$HOME_DIR/bin/grokbot-genseo-daily.sh" ] && ok "real dest executable" || bad "real dest not executable"
  cmp -s "$ROOT/deploy/grokbot-genseo-daily.sh" "$HOME_DIR/bin/grokbot-genseo-daily.sh" \
    && ok "real dest matches deploy/" || bad "real dest differs"
  has "$WORK/out" "helper scripts/genseo_wait_for_network.sh: present" "real tree network helper present"
  has "$WORK/out" "helper scripts/genseo_sync_main.sh: present" "real tree sync helper present"
  grep -F -q 'genseo_wait_for_network.sh' "$HOME_DIR/bin/grokbot-genseo-daily.sh" \
    && ok "copied wrapper waits for DNS" || bad "copied wrapper has no DNS wait"
  grep -F -q 'genseo_sync_main.sh' "$HOME_DIR/bin/grokbot-genseo-daily.sh" \
    && ok "copied wrapper syncs origin/main" || bad "copied wrapper has no origin/main sync"
fi
for rel in scripts/genseo_daily_lock.sh scripts/genseo_group_timeout.sh; do
  if [ -f "$ROOT/$rel" ]; then
    has "$WORK/out" "helper $rel: present" "real tree $rel present"
  else
    has "$WORK/out" "helper $rel: MISSING" "real tree $rel missing"
  fi
done

echo "9. installer code does not call launchctl, ssh, or Shopify"
code=$(python3 -c '
import pathlib, sys
text = pathlib.Path(sys.argv[1]).read_text()
print("\n".join(line.split("#", 1)[0] for line in text.splitlines()))
' "$INSTALL")
clean=1
for word in launchctl ssh shopify osascript; do
  if printf '%s\n' "$code" | grep -i -q "$word"; then
    bad "code contains $word"
    clean=0
  fi
done
[ "$clean" = 1 ] && ok "no launchctl, ssh, Shopify, or osascript in code"

echo "10. unknown argument and --help"
new_home help
run_install "$HOME_DIR" "$ROOT" 0 -- --not-a-flag
assert_rc 2 "unknown arg exit 2"
[ ! -e "$HOME_DIR/bin" ] && ok "unknown arg wrote nothing" || bad "unknown arg wrote bin"
run_install "$HOME_DIR" "$ROOT" 0 -- --help
assert_rc 0 "help exit 0"
has "$WORK/out" "Does not start launchd." "help mentions launchd is not started"
[ ! -e "$HOME_DIR/bin" ] && ok "help wrote nothing" || bad "help wrote bin"

echo "11. a wrapper that waits for DNS is not copied when that helper is absent"
fixture netmiss 1 755
printf '\n%s\n' '. "$HOME/genseo/scripts/genseo_wait_for_network.sh"' >>"$FIX/deploy/grokbot-genseo-daily.sh"
new_home netmiss
run_install "$HOME_DIR" "$FIX" 1 --
assert_rc 1 "copy refused without the network helper"
has "$WORK/err" "Nothing was copied" "refused copy says nothing was copied"
has "$WORK/out" "helper scripts/genseo_wait_for_network.sh: MISSING" "reports the network helper missing"
[ ! -e "$HOME_DIR/bin/grokbot-genseo-daily.sh" ] && ok "no dest without the network helper" || bad "dest written without the network helper"
printf '%s\n' 'wait' >"$FIX/scripts/genseo_wait_for_network.sh"
run_install "$HOME_DIR" "$FIX" 1 --
assert_rc 0 "copy succeeds once the network helper exists"
has "$WORK/out" "helper scripts/genseo_wait_for_network.sh: present" "network helper present"
cmp -s "$FIX/deploy/grokbot-genseo-daily.sh" "$HOME_DIR/bin/grokbot-genseo-daily.sh" \
  && ok "DNS wrapper bytes match" || bad "DNS wrapper bytes differ"

echo "12. a wrapper that syncs origin/main is not copied when that helper is absent"
fixture syncmiss 1 755
printf '\n%s\n' '. "$HOME/genseo/scripts/genseo_sync_main.sh"' >>"$FIX/deploy/grokbot-genseo-daily.sh"
new_home syncmiss
run_install "$HOME_DIR" "$FIX" 1 --
assert_rc 1 "copy refused without the sync helper"
has "$WORK/err" "Nothing was copied" "refused sync copy says nothing was copied"
has "$WORK/out" "helper scripts/genseo_sync_main.sh: MISSING" "reports the sync helper missing"
[ ! -e "$HOME_DIR/bin/grokbot-genseo-daily.sh" ] && ok "no dest without the sync helper" || bad "dest written without the sync helper"
printf '%s\n' 'sync' >"$FIX/scripts/genseo_sync_main.sh"
run_install "$HOME_DIR" "$FIX" 1 --
assert_rc 0 "copy succeeds once the sync helper exists"
has "$WORK/out" "helper scripts/genseo_sync_main.sh: present" "sync helper present"
cmp -s "$FIX/deploy/grokbot-genseo-daily.sh" "$HOME_DIR/bin/grokbot-genseo-daily.sh" \
  && ok "sync wrapper bytes match" || bad "sync wrapper bytes differ"

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" = 0 ]

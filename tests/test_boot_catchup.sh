#!/bin/bash
# Opt-in boot catch-up. No Shopify, no launchctl, no caffeinate, no network.
# Bash 3.2. The decision clock is injected. HOME points at a trap plist that
# would publish if the program read the real LaunchAgents directory.
#   bash tests/test_boot_catchup.sh
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$("$ROOT/tests/python_bin.sh")" || exit 1
SCRIPT="$ROOT/scripts/genseo_boot_catchup.py"
SELF="$ROOT/scripts/genseo_self_apply.sh"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/boot-catchup.XXXXXX")" || exit 1
PASS=0
FAIL=0

cleanup() {
  rm -rf "$WORK"
}
trap cleanup EXIT

ok() { PASS=$((PASS + 1)); printf '  ok   %s\n' "$*"; }
bad() { FAIL=$((FAIL + 1)); printf '  FAIL %s\n' "$*"; }

show() {
  printf '    stdout: %s\n' "$(tr '\n' '|' <"$1" 2>/dev/null || true)"
  printf '    stderr: %s\n' "$(tr '\n' '|' <"$2" 2>/dev/null || true)"
}

mkdir -p "$WORK/bin" "$WORK/home/Library/LaunchAgents"
FORBIDDEN="$WORK/forbidden.log"
: >"$FORBIDDEN"
cat >"$WORK/bin/launchctl" <<'EOF'
#!/bin/sh
printf '%s\n' "launchctl $*" >> "$GENSEO_CATCHUP_FORBIDDEN_LOG"
exit 99
EOF
cat >"$WORK/bin/caffeinate" <<'EOF'
#!/bin/sh
printf '%s\n' "caffeinate $*" >> "$GENSEO_CATCHUP_FORBIDDEN_LOG"
exit 99
EOF
chmod 755 "$WORK/bin/launchctl" "$WORK/bin/caffeinate"
"$PY" - "$WORK/home/Library/LaunchAgents/com.pati.genseo-daily.plist" <<'PY'
import plistlib, sys
plistlib.dump({
    "Label": "com.pati.genseo-daily",
    "ProgramArguments": ["/bin/echo", "--live", "shopify_publisher"],
    "RunAtLoad": False,
    "EnvironmentVariables": {"GENSEO_TICKET_PREFIX": "MM", "GENSEO_HOST_ROLE": "standby"},
}, open(sys.argv[1], "wb"))
PY
"$PY" - "$WORK/home/Library/LaunchAgents/com.pati.genseo-landing.plist" <<'PY'
import plistlib, sys
plistlib.dump({
    "Label": "com.pati.genseo-landing",
    "ProgramArguments": ["/bin/echo", "--live"],
    "RunAtLoad": False,
    "EnvironmentVariables": {"GENSEO_HOST_ROLE": "primary"},
}, open(sys.argv[1], "wb"))
PY

run_catchup() {
  local state="$1" now="$2" adone="$3" alock="$4" ldone="$5" llock="$6"
  mkdir -p "$state"
  env -i \
    HOME="$WORK/home" \
    PATH="$WORK/bin:/usr/bin:/bin" \
    TMPDIR="${TMPDIR:-/tmp}" \
    GENSEO_CATCHUP_FORBIDDEN_LOG="$FORBIDDEN" \
    GENSEO_CATCHUP_TEST=1 \
    GENSEO_CATCHUP_DAY=2026-10-19 \
    GENSEO_CATCHUP_NOW="$now" \
    GENSEO_CATCHUP_STATE_DIR="$state" \
    GENSEO_CATCHUP_ARTICLE_DONE="$adone" \
    GENSEO_CATCHUP_ARTICLE_LOCKED="$alock" \
    GENSEO_CATCHUP_LANDING_DONE="$ldone" \
    GENSEO_CATCHUP_LANDING_LOCKED="$llock" \
    GENSEO_CATCHUP_ARTICLE_PLIST="$ROOT/deploy/com.pati.genseo-daily.macbook.plist" \
    GENSEO_CATCHUP_LANDING_PLIST="$ROOT/deploy/com.pati.genseo-landing.macbook.plist" \
    "$PY" "$SCRIPT" >"$state/out" 2>"$state/err"
  printf '%s\n' "$?"
}

expect_rc() {
  local got="$1" want="$2" name="$3" state="$4"
  if [ "$got" = "$want" ]; then ok "$name exits $want"
  else bad "$name exits $want (rc $got)"; show "$state/out" "$state/err"; fi
}

has() {
  if grep -F -q -- "$2" "$1"; then ok "$3"
  else bad "$3"; show "$1" /dev/null; fi
}

lacks() {
  if grep -F -q -- "$2" "$1"; then bad "$3"; show "$1" /dev/null
  else ok "$3"; fi
}

echo "1. missed morning, already done, in progress, before first, after last"
STATE="$WORK/missed"
RC="$(run_catchup "$STATE" 08:09 0 0 0 0)"
expect_rc "$RC" 0 "08:09" "$STATE"
has "$STATE/out" "article start missed-morning-slot" "08:09 starts the article lane"
has "$STATE/out" "/usr/bin/caffeinate -i -s" "08:09 command is caffeinate -i -s"
has "$STATE/out" "grokbot-genseo-daily.sh" "08:09 uses the article wrapper"
lacks "$STATE/out" "run_landing_daily.sh" "08:09 does not start landing before 08:15"
lacks "$STATE/out" "--live" "08:09 does not pass --live"
lacks "$STATE/out" "shopify_publisher" "08:09 does not name the article publisher"
[ -f "$STATE/2026-10-19-article.started" ] && ok "08:09 stamps the article lane" || bad "08:09 did not stamp articles"
[ ! -e "$STATE/2026-10-19-landing.started" ] && ok "08:09 does not stamp landing" || bad "08:09 stamped landing"

STATE="$WORK/again"
mkdir -p "$STATE"
cp "$WORK/missed/2026-10-19-article.started" "$STATE/2026-10-19-article.started"
RC="$(run_catchup "$STATE" 10:00 0 0 0 0)"
expect_rc "$RC" 0 "second login" "$STATE"
has "$STATE/out" "article skip already-fired" "second login does not start articles again"
# Landing was not stamped at 08:09. A later login can still start that lane.
has "$STATE/out" "landing start missed-morning-slot" "later login can start a lane that never fired"
lacks "$STATE/out" "--live" "second login does not pass --live"

STATE="$WORK/done"
RC="$(run_catchup "$STATE" 10:00 1 0 1 0)"
expect_rc "$RC" 0 "already done" "$STATE"
has "$STATE/out" "article skip already-done" "done articles do not start"
has "$STATE/out" "landing skip already-done" "done landing does not start"
lacks "$STATE/out" " start " "already done launches nothing"
[ ! -e "$STATE/2026-10-19-article.started" ] && ok "already done writes no article stamp" || bad "already done stamped articles"

STATE="$WORK/lock"
RC="$(run_catchup "$STATE" 10:00 0 1 0 1)"
expect_rc "$RC" 0 "in progress" "$STATE"
has "$STATE/out" "article skip in-progress" "article lock does not start"
has "$STATE/out" "landing skip in-progress" "landing lock does not start"
lacks "$STATE/out" " start " "in progress launches nothing"

STATE="$WORK/early"
RC="$(run_catchup "$STATE" 06:30 0 0 0 0)"
expect_rc "$RC" 0 "before first" "$STATE"
has "$STATE/out" "article skip before-first-slot" "before 07:30 does not start articles"
has "$STATE/out" "landing skip before-first-slot" "before 08:15 does not start landing"
lacks "$STATE/out" " start " "before first slot launches nothing"

STATE="$WORK/late"
RC="$(run_catchup "$STATE" 17:00 0 0 0 0)"
expect_rc "$RC" 0 "after last" "$STATE"
has "$STATE/out" "article skip after-last-slot" "after 14:47 does not start articles"
has "$STATE/out" "landing skip after-last-slot" "after 16:15 does not start landing"
lacks "$STATE/out" " start " "after last slot launches nothing"

STATE="$WORK/soon"
RC="$(run_catchup "$STATE" 08:00 0 0 0 0)"
expect_rc "$RC" 0 "next slot soon" "$STATE"
has "$STATE/out" "article skip next-slot-soon" "08:00 leaves 08:05 to launchd"
has "$STATE/out" "landing skip before-first-slot" "08:00 leaves 08:15 to launchd"
lacks "$STATE/out" " start " "a near slot launches nothing"

echo "2. no launchctl, no caffeinate, trap plist unused"
if [ ! -s "$FORBIDDEN" ]; then ok "launchctl and caffeinate were not executed"
else bad "a forbidden command ran"; printf '    %s\n' "$(tr '\n' '|' <"$FORBIDDEN")"; fi

echo "3. install text, self-apply refusal, calendar agents stay RunAtLoad false"
PRINT="$WORK/print-install.out"
env -i PATH="$WORK/bin:/usr/bin:/bin" HOME="$WORK/home" \
  GENSEO_CATCHUP_FORBIDDEN_LOG="$FORBIDDEN" \
  "$PY" "$SCRIPT" --print-install >"$PRINT" 2>"$WORK/print-install.err"
INSTALL_WANT='cp ~/genseo/deploy/com.pati.genseo-catchup.plist ~/Library/LaunchAgents/com.pati.genseo-catchup.plist && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-catchup.plist'
if [ "$(cat "$PRINT")" = "$INSTALL_WANT" ]; then
  ok "install one-liner"
else
  bad "install one-liner"
  show "$PRINT" "$WORK/print-install.err"
fi
UNPRINT="$WORK/print-uninstall.out"
env -i PATH="$WORK/bin:/usr/bin:/bin" HOME="$WORK/home" \
  "$PY" "$SCRIPT" --print-uninstall >"$UNPRINT" 2>"$WORK/print-uninstall.err"
UNINSTALL_WANT='launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-catchup.plist; rm -f ~/Library/LaunchAgents/com.pati.genseo-catchup.plist'
if [ "$(cat "$UNPRINT")" = "$UNINSTALL_WANT" ]; then
  ok "uninstall one-liner"
else
  bad "uninstall one-liner"
  show "$UNPRINT" "$WORK/print-uninstall.err"
fi
if grep -F -q -f "$PRINT" "$ROOT/DAILY-RUN.md" && grep -F -q -f "$UNPRINT" "$ROOT/DAILY-RUN.md"; then
  ok "runbook has both one-liners"
else
  bad "runbook is missing an one-liner"
fi
if [ ! -s "$FORBIDDEN" ]; then ok "printing install did not execute launchctl"
else bad "printing install executed a forbidden command"; fi

SAFE_RC=0
(
  # shellcheck disable=SC1090
  . "$SELF"
  genseo_self_apply_plist_safe "$ROOT/deploy/com.pati.genseo-catchup.plist" "com.pati.genseo-catchup"
) || SAFE_RC=$?
if [ "$SAFE_RC" = 4 ]; then ok "self-apply refuses the catch-up plist"
else bad "self-apply refuse rc was $SAFE_RC, want 4"; fi

REL_RC=0
REL="$(
  # shellcheck disable=SC1090
  . "$SELF"
  genseo_self_apply_rel macbook catchup
)" || REL_RC=$?
if [ "$REL_RC" != 0 ] && [ -z "$REL" ]; then ok "self-apply has no catch-up plist"
else bad "self-apply returned a catch-up plist ($REL rc $REL_RC)"; fi

"$PY" - "$ROOT/deploy/com.pati.genseo-daily.macbook.plist" "$ROOT/deploy/com.pati.genseo-landing.macbook.plist" <<'PY'
import plistlib, sys
ok = True
for path in sys.argv[1:]:
    data = plistlib.load(open(path, "rb"))
    if data.get("RunAtLoad") is not False or "StartCalendarInterval" not in data:
        sys.stderr.write("calendar plist changed: %s\n" % path)
        ok = False
if not ok:
    sys.exit(1)
PY
if [ "$?" = 0 ]; then ok "article and landing agents still have calendars and RunAtLoad false"
else bad "article or landing plist changed RunAtLoad"; fi

printf 'pass=%s fail=%s\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]

#!/bin/bash
# Offline checks for scripts/mac_return_reconcile.sh.
# Temp git repos only. No Shopify, no network, no launchd, no push.
#   bash tests/test_mac_return_reconcile.sh
# Syntax target is bash 3.2 (macOS /bin/bash). This host parses with bash -n
# and runs the fixture with whatever bash is installed.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT/scripts/mac_return_reconcile.sh"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/mac-return-reconcile.XXXXXX")" || exit 1
PIDS=""
PASS=0
FAIL=0
START_STATUS="$(git -C "$ROOT" status --porcelain)"
START_HEAD="$(git -C "$ROOT" rev-parse HEAD)"

cleanup() {
  local p
  for p in $PIDS; do
    kill "$p" 2>/dev/null || true
    wait "$p" 2>/dev/null || true
  done
  rm -rf "$WORK"
}
trap cleanup EXIT

ok() { PASS=$((PASS + 1)); printf '  ok   %s\n' "$*"; }
bad() { FAIL=$((FAIL + 1)); printf '  FAIL %s\n' "$*"; }

show_fail() {
  printf '    stdout: %s\n' "$(tr '\n' '|' <"$WORK/out")"
  printf '    stderr: %s\n' "$(tr '\n' '|' <"$WORK/err")"
}

assert_rc() {
  if [ "$RC" = "$1" ]; then ok "$2"
  else bad "$2 (rc $RC, want $1)"; show_fail; fi
}

has() {
  if grep -F -q -- "$2" "$1"; then ok "$3"
  else bad "$3"; show_fail; fi
}

lacks() {
  if grep -F -q -- "$2" "$1"; then bad "$3"; show_fail
  else ok "$3"; fi
}

git_cfg() {
  git -C "$1" config user.email "reconcile-test@example.com"
  git -C "$1" config user.name "reconcile-test"
  git -C "$1" config commit.gpgsign false
  git -C "$1" config core.hooksPath "$WORK/no-hooks"
}

init_repo() {
  local name="$1"
  BARE="$WORK/bare-$name"
  REPO="$WORK/repo-$name"
  rm -rf "$BARE" "$REPO"
  git init --bare -b main "$BARE" >/dev/null 2>&1
  git init -b main "$REPO" >/dev/null 2>&1
  git_cfg "$REPO"
  printf 'state/\n' >"$REPO/.gitignore"
  printf '%s\n' 'v1' >"$REPO/README"
  git -C "$REPO" add .gitignore README
  git -C "$REPO" commit -m "v1" >/dev/null 2>&1 || exit 1
  git -C "$REPO" remote add origin "$BARE"
  git -C "$REPO" push origin main >/dev/null 2>&1 || exit 1
}

advance_origin() {
  local name="$1"
  local other="$WORK/other-$name"
  rm -rf "$other"
  git clone "$BARE" "$other" >/dev/null 2>&1 || exit 1
  git_cfg "$other"
  printf '%s\n' 'v2' >"$other/README"
  git -C "$other" add README
  git -C "$other" commit -m "v2" >/dev/null 2>&1 || exit 1
  git -C "$other" push origin main >/dev/null 2>&1 || exit 1
}

set_age() {
  python3 -c 'import os,sys,time
p=sys.argv[1]
age=int(sys.argv[2])
t=time.time()-age
os.utime(p,(t,t))' "$1" "$2"
}

run_rec() {
  [ -n "${REPO:-}" ] || { printf '%s\n' "REPO unset" >&2; exit 1; }
  : >"$WORK/out"
  : >"$WORK/err"
  env GENSEO_HOME="$REPO" GIT_TERMINAL_PROMPT=0 \
    bash "$SCRIPT" "$@" >"$WORK/out" 2>"$WORK/err"
  RC=$?
}

head_of() { git -C "$1" rev-parse HEAD; }
bare_main() { git -C "$BARE" rev-parse main; }

mkdir -p "$WORK/no-hooks" "$WORK/home"

echo "0. bash -n and the script does not execute push, reset, or launchctl"
bash -n "$SCRIPT" && ok "bash -n" || bad "bash -n"
if awk '
  /^[[:space:]]*#/ {next}
  /^[[:space:]]*printf / {next}
  /git[[:space:]]+push/ {print NR": "$0; bad=1}
  /git[[:space:]]+reset/ {print NR": "$0; bad=1}
  /git[[:space:]]+checkout/ {print NR": "$0; bad=1}
  /git[[:space:]]+clean/ {print NR": "$0; bad=1}
  /git[[:space:]]+stash/ {print NR": "$0; bad=1}
  /rm[[:space:]]+-r/ {print NR": "$0; bad=1}
  /launchctl/ {print NR": "$0; bad=1}
  END {exit bad+0}
' "$SCRIPT"; then
  ok "no push, reset, checkout, clean, stash, rm -r, or launchctl command"
else
  bad "script contains a forbidden command"
fi
grep -F -q 'git merge --ff-only origin/main' "$SCRIPT" && ok "apply is ff-only" || bad "missing ff-only"
if awk '
  /^[[:space:]]*#/ {next}
  /^[[:space:]]*printf / {next}
  /(bash|python3?)[[:space:]].*(shopify_publisher\.py|landing_publisher\.py|run_landing_daily\.sh|grokbot-genseo-daily\.sh)/ {print NR": "$0; bad=1}
  END {exit bad+0}
' "$SCRIPT"; then
  ok "no publisher, daily-job, or --live invocation"
else
  bad "script invokes a publisher, daily job, or --live"
fi
grep -F -q 'e1b8519' "$SCRIPT" && ok "historical sha e1b8519 is named" || bad "missing e1b8519"
grep -F -q '289803e' "$SCRIPT" && ok "historical sha 289803e is named" || bad "missing 289803e"
n=$(grep -c 'gc.auto=0' "$SCRIPT" || true)
if [ "$n" -ge 2 ]; then ok "fetch and merge disable auto-gc"
else bad "gc.auto=0 count is $n"; fi
if grep -F -q 'BSD stat -f only' "$SCRIPT"; then
  bad "stale claim that landing mtime is BSD stat only"
else
  ok "mtime comment matches the landing helper"
fi
grep -F -q 'GENSEO_LOCK_STALE_SEC:-21600' "$ROOT/scripts/genseo_daily_lock.sh" && ok "daily lock default is 21600" || bad "daily lock default drifted"
grep -F -q -- '-gt 14400' "$ROOT/scripts/run_landing_daily.sh" && ok "landing lock steals after 14400" || bad "landing lock threshold drifted"

echo "1. help and conflicting flags"
bash "$SCRIPT" --help >"$WORK/out" 2>"$WORK/err"
RC=$?
assert_rc 0 "help exit 0"
has "$WORK/out" "usage:" "help prints usage"
has "$WORK/out" "install_mac_daily_wrapper.sh" "help names the wrapper reinstall"
has "$WORK/out" "Does not publish" "help says apply does not publish"
has "$WORK/out" "never --live" "help names the draft-only verify"
bash "$SCRIPT" --nope >"$WORK/out" 2>"$WORK/err"
RC=$?
assert_rc 2 "unknown argument exit 2"
bash "$SCRIPT" --dry-run --apply >"$WORK/out" 2>"$WORK/err"
RC=$?
assert_rc 2 "--dry-run with --apply exit 2"
bash "$SCRIPT" --dry-run --apply-stale-lock >"$WORK/out" 2>"$WORK/err"
RC=$?
assert_rc 2 "--dry-run with --apply-stale-lock exit 2"
mkdir -p "$WORK/not-a-repo"
env GENSEO_HOME="$WORK/not-a-repo" bash "$SCRIPT" >"$WORK/out" 2>"$WORK/err"
RC=$?
assert_rc 1 "not a git repo exit 1"
has "$WORK/err" "not a git work tree" "stderr names the missing repo"

echo "2. dry-run on a clean repo that is behind origin"
init_repo behind
advance_origin behind
BEFORE="$(head_of "$REPO")"
BARE_BEFORE="$(bare_main)"
mkdir -p "$REPO/state/daily.lock" "$REPO/state/landing-daily.lock"
printf '%s\n' 99999999 >"$REPO/state/daily.lock/pid"
set_age "$REPO/state/daily.lock" 18000
set_age "$REPO/state/landing-daily.lock" 18000
run_rec
assert_rc 0 "dry-run exit 0"
has "$WORK/out" "mode: dry-run" "mode is dry-run"
has "$WORK/out" "ict:" "ict line"
has "$WORK/out" "+0700" "ict offset +0700"
has "$WORK/out" "branch: main" "branch main"
has "$WORK/out" "fetch: ok" "fetch ok"
has "$WORK/out" "main_vs_head_relation: behind" "behind origin/main"
has "$WORK/out" "local_commits_not_on_origin: 0" "no local-only commits"
has "$WORK/out" "historical e1b8519: not in this clone" "e1b8519 absent here"
has "$WORK/out" "historical 289803e: not in this clone" "289803e absent here"
has "$WORK/out" "personas_index: clean" "personas clean"
has "$WORK/out" "state_ignored: yes" "state/ ignored"
has "$WORK/out" "threshold_daily_sec: 21600" "daily threshold 6h"
has "$WORK/out" "threshold_landing_sec: 14400" "landing threshold 4h"
has "$WORK/out" "lock daily.lock suggested_unlock: no" "5h daily lock is not stale"
has "$WORK/out" "lock daily.lock reason: younger-than-threshold" "daily reason is age"
has "$WORK/out" "lock landing-daily.lock suggested_unlock: yes" "5h landing lock is stale"
has "$WORK/out" "lock landing-daily.lock suggest: rmdir " "landing suggest is rmdir"
has "$WORK/out" "wrapper: bash scripts/install_mac_daily_wrapper.sh" "daily wrapper reminder"
has "$WORK/out" "wrapper_doc: DAILY-RUN.md docs/TICKET_REFILL.md" "wrapper docs"
has "$WORK/out" "wrapper_plist_repo: deploy/com.pati.genseo-daily.macbook.plist" "daily plist in repo"
has "$WORK/out" "wrapper_role: MacBook GENSEO_HOST_ROLE=primary GENSEO_TICKET_PREFIX=MB until Mini failover-release. Copy the plist and bootstrap; the wrapper installer does not." "daily role reminder"
has "$WORK/out" "checklist:    That plist is GENSEO_HOST_ROLE=primary and GENSEO_TICKET_PREFIX=MB until a Mini failover-release." "checklist names primary MB"
has "$WORK/out" "landing_plist_repo: deploy/com.pati.genseo-landing.macbook.plist" "landing plist in repo"
has "$WORK/out" "worker: agent worker start --name MacBook-Pro" "worker reminder"
has "$WORK/out" "launchagent: com.pati.cursor-agent-worker" "worker launchagent"
has "$WORK/out" "checklist: 1. cd ~/genseo && bash scripts/mac_return_reconcile.sh" "checklist printed"
has "$WORK/out" "apply: not requested" "dry-run does not apply"
has "$WORK/out" "catchup_cmd: git merge --ff-only origin/main" "dry-run names the ff-only catch-up"
has "$WORK/out" "catchup: would fast-forward on --apply" "behind checkout would fast-forward"
has "$WORK/out" "wrapper_install: skipped missing-source" "fixture has no wrapper to copy"
has "$WORK/out" "verify: skipped-not-checkout" "fixture skips writer-map verify"
has "$WORK/out" "result: ok" "result ok"
lacks "$WORK/out" "rm -rf" "report has no rm -rf"
if grep -F 'git push --force' "$WORK/out" | grep -v -e 'Do not' -e 'do not' | grep -q .; then
  bad "report tells the operator to force-push"
else
  ok "force-push is only named as a prohibition"
fi
[ "$(head_of "$REPO")" = "$BEFORE" ] && ok "dry-run left HEAD" || bad "dry-run moved HEAD"
[ "$(bare_main)" = "$BARE_BEFORE" ] && ok "dry-run did not push" || bad "dry-run pushed"
[ -d "$REPO/state/daily.lock" ] && ok "dry-run left daily.lock" || bad "dry-run removed daily.lock"
[ -d "$REPO/state/landing-daily.lock" ] && ok "dry-run left landing lock" || bad "dry-run removed landing lock"
AGE="$(sed -n 's/^lock daily.lock age: //p' "$WORK/out")"
if [ "$AGE" -gt 17000 ] && [ "$AGE" -lt 20000 ]; then ok "daily age is about 5h"
else bad "daily age $AGE"; fi

echo "3. --apply fast-forwards, and --apply-stale-lock removes only the stale landing lock"
run_rec --apply --apply-stale-lock
assert_rc 0 "apply plus stale-lock exit 0"
has "$WORK/out" "apply: fast-forward" "fast-forward"
has "$WORK/out" "lock_apply landing-daily.lock: removed" "landing lock removed"
has "$WORK/out" "lock_apply daily.lock: kept younger-than-threshold" "young daily lock kept"
[ "$(head_of "$REPO")" = "$(git -C "$REPO" rev-parse origin/main)" ] && ok "HEAD matches origin/main" || bad "HEAD is not origin/main"
[ "$(bare_main)" = "$BARE_BEFORE" ] && ok "fast-forward did not push" || bad "fast-forward pushed"
[ -d "$REPO/state/daily.lock" ] && ok "daily.lock still present" || bad "daily.lock removed"
[ ! -e "$REPO/state/landing-daily.lock" ] && ok "landing lock gone" || bad "landing lock still present"
run_rec --apply
assert_rc 0 "second apply exit 0"
has "$WORK/out" "apply: already up to date" "already up to date"
[ "$(bare_main)" = "$BARE_BEFORE" ] && ok "second apply did not push" || bad "second apply pushed"

echo "4. --apply refuses a dirty personas/index.json"
init_repo dirty
mkdir -p "$REPO/personas"
printf '%s\n' '{}' >"$REPO/personas/index.json"
git -C "$REPO" add personas/index.json
git -C "$REPO" commit -m "personas" >/dev/null 2>&1 || exit 1
git -C "$REPO" push origin main >/dev/null 2>&1 || exit 1
advance_origin dirty
printf '%s\n' '{"dirty":true}' >"$REPO/personas/index.json"
BEFORE="$(head_of "$REPO")"
run_rec --apply
assert_rc 3 "dirty apply exit 3"
has "$WORK/out" "apply: refused" "apply refused"
has "$WORK/out" "apply_block: dirty" "dirty block"
has "$WORK/out" "personas_index: dirty" "personas called out"
has "$WORK/out" "no-face" "no-face reminder"
has "$WORK/out" "result: apply-refused" "result refused"
[ "$(head_of "$REPO")" = "$BEFORE" ] && ok "dirty tree was not merged" || bad "dirty tree merged"
grep -F -q '{"dirty":true}' "$REPO/personas/index.json" && ok "personas file left in place" || bad "personas file changed"

echo "5. --apply refuses unpushed commits and does not push them"
init_repo unpushed
advance_origin unpushed
printf '%s\n' 'local publish' >"$REPO/LOCAL"
git -C "$REPO" add LOCAL
git -C "$REPO" commit -m "publish: local article" >/dev/null 2>&1 || exit 1
LOCAL_SHA="$(head_of "$REPO")"
BARE_BEFORE="$(bare_main)"
run_rec --apply
assert_rc 3 "unpushed apply exit 3"
has "$WORK/out" "apply_block: local-commits-not-on-origin" "unpushed block"
has "$WORK/out" "apply_next: do not run git push --force" "instructions refuse force-push"
has "$WORK/out" "apply_next: do not run git reset --hard" "instructions refuse reset"
has "$WORK/out" "local_commit:" "local commit is listed"
[ "$(head_of "$REPO")" = "$LOCAL_SHA" ] && ok "local commit kept" || bad "local commit moved"
[ "$(bare_main)" = "$BARE_BEFORE" ] && ok "unpushed commit was not pushed" || bad "unpushed commit was pushed"
git -C "$BARE" log --format='%s' main | grep -F -q "publish: local article" && bad "bare repo received the publish commit" || ok "bare repo has no publish commit"

echo "6. --apply does not switch off another branch"
init_repo side
advance_origin side
git -C "$REPO" checkout -b side >/dev/null 2>&1 || exit 1
BEFORE="$(head_of "$REPO")"
run_rec --apply
assert_rc 3 "side branch apply exit 3"
has "$WORK/out" "apply_block: not-on-main" "not-on-main block"
[ "$(git -C "$REPO" rev-parse --abbrev-ref HEAD)" = side ] && ok "stayed on side" || bad "left side"
[ "$(head_of "$REPO")" = "$BEFORE" ] && ok "side HEAD unchanged" || bad "side HEAD moved"

echo "6b. --apply returns an article branch to main and does not push its commits"
init_repo artapply
printf '%s\n' '- [ ] **#CA1016-2 — shilajit on an empty stomach** — `Title`' >"$REPO/daily-tickets.md"
printf '%s\n' '- [ ] **#CA1016-7 — vaginal probiotics over 60** — `Next`' >>"$REPO/daily-tickets.md"
git -C "$REPO" add daily-tickets.md
git -C "$REPO" commit -m "queue" >/dev/null 2>&1 || exit 1
git -C "$REPO" push origin main >/dev/null 2>&1 || exit 1
git -C "$REPO" checkout -b article/ca1016-2 >/dev/null 2>&1 || exit 1
printf '%s\n' '- [DONE 2026-10-18 https://wellnessnest.co/blogs/news/shilajit-on-an-empty-stomach-yes-or-no-in-the-us] **#CA1016-2 — shilajit on an empty stomach** — `Title`' >"$REPO/daily-tickets.md"
printf '%s\n' '- [ ] **#CA1016-7 — vaginal probiotics over 60** — `Next`' >>"$REPO/daily-tickets.md"
git -C "$REPO" add daily-tickets.md
git -C "$REPO" commit -m "publish CA1016-2" >/dev/null 2>&1 || exit 1
printf '%s\n' 'scratch' >"$REPO/scratch.txt"
ART_SHA="$(head_of "$REPO")"
BARE_BEFORE="$(bare_main)"
run_rec
assert_rc 0 "article dry-run exit 0"
has "$WORK/out" "day_branch_return: would record queue closures and switch article/ca1016-2 to main on --apply (ref kept)" "dry-run names the article return"
[ "$(git -C "$REPO" rev-parse --abbrev-ref HEAD)" = "article/ca1016-2" ] && ok "article dry-run stayed" || bad "article dry-run switched"
[ ! -e "$REPO/state/queue-closures.json" ] && ok "article dry-run wrote no ledger" || bad "article dry-run wrote a ledger"
run_rec --apply
assert_rc 0 "article apply exit 0"
has "$WORK/out" "day_branch_return: switched article/ca1016-2 to main" "apply switched the article branch"
has "$WORK/out" "day_branch_ref: kept" "apply kept the article ref"
has "$WORK/out" "recorded: 1 queue closure(s)" "apply recorded the closure"
has "$WORK/out" "apply: already up to date" "main needed no fast-forward"
has "$WORK/out" "result: ok" "article apply result ok"
lacks "$WORK/out" "apply_block: not-on-main" "article apply is not blocked for the branch"
[ "$(git -C "$REPO" rev-parse --abbrev-ref HEAD)" = main ] && ok "apply left HEAD on main" || bad "apply did not leave HEAD on main"
[ "$(head_of "$REPO")" = "$(git -C "$REPO" rev-parse origin/main)" ] && ok "apply HEAD matches origin/main" || bad "apply HEAD is not origin/main"
[ "$(git -C "$REPO" rev-parse article/ca1016-2)" = "$ART_SHA" ] && ok "article ref still points at the publish commit" || bad "article ref moved"
[ "$(bare_main)" = "$BARE_BEFORE" ] && ok "publish commit was not pushed" || bad "publish commit was pushed"
git -C "$BARE" log --format='%s' main | grep -F -q "publish CA1016-2" && bad "bare repo received the publish commit" || ok "bare repo has no publish commit"
grep -F -q -- '- [ ] **#CA1016-2' "$REPO/daily-tickets.md" && ok "work tree ticket line is the open main line" || bad "work tree kept the DONE line"
grep -F -q 'CA1016-2' "$REPO/state/queue-closures.json" && ok "ledger names CA1016-2" || bad "ledger missing CA1016-2"
[ "$(cat "$REPO/scratch.txt")" = "scratch" ] && ok "untracked file kept" || bad "untracked file lost"
first=$(/usr/bin/python3 "$ROOT/scripts/genseo_queue_closures.py" first --queue "$REPO/daily-tickets.md")
case "$first" in
  *'#CA1016-7'*) ok "effective queue starts at CA1016-7" ;;
  *) bad "effective queue is $first" ;;
esac

echo "7. GENSEO_LOCK_STALE_SEC is honored; GENSEO_LANDING_LOCK_STALE_SEC is not"
init_repo envthr
mkdir -p "$REPO/state/daily.lock" "$REPO/state/landing-daily.lock"
printf '%s\n' 99999999 >"$REPO/state/daily.lock/pid"
set_age "$REPO/state/daily.lock" 18000
set_age "$REPO/state/landing-daily.lock" 30
GENSEO_LOCK_STALE_SEC=1000 GENSEO_LANDING_LOCK_STALE_SEC=1 run_rec
unset GENSEO_LOCK_STALE_SEC GENSEO_LANDING_LOCK_STALE_SEC
assert_rc 0 "threshold env dry-run exit 0"
has "$WORK/out" "threshold_daily_sec: 1000" "daily threshold from env"
has "$WORK/out" "threshold_daily_source: GENSEO_LOCK_STALE_SEC" "daily source is env"
has "$WORK/out" "threshold_landing_sec: 14400" "landing threshold stays 14400"
has "$WORK/out" "lock daily.lock suggested_unlock: yes" "lowered daily threshold marks 5h stale"
has "$WORK/out" "lock landing-daily.lock suggested_unlock: no" "30s landing lock stays young"
has "$WORK/out" "lock landing-daily.lock reason: younger-than-threshold" "landing ignores the env override"
[ -d "$REPO/state/daily.lock" ] && ok "env dry-run left daily.lock" || bad "env dry-run removed daily.lock"

echo "8. extra files and a symlink are not removed"
init_repo extra
mkdir -p "$REPO/state/daily.lock"
printf '%s\n' 99999999 >"$REPO/state/daily.lock/pid"
printf '%s\n' note >"$REPO/state/daily.lock/note"
set_age "$REPO/state/daily.lock" 30000
run_rec --apply-stale-lock
assert_rc 4 "extra file blocks unlock"
has "$WORK/out" "lock_apply daily.lock: kept unexpected-files" "unexpected-files"
has "$WORK/out" "mode: apply-stale-lock" "lock-only apply is not labeled dry-run"
[ -f "$REPO/state/daily.lock/note" ] && ok "note file kept" || bad "note file removed"
[ -f "$REPO/state/daily.lock/pid" ] && ok "pid file kept" || bad "pid file removed"
init_repo link
mkdir -p "$REPO/state/real-daily-lock"
ln -s real-daily-lock "$REPO/state/daily.lock"
run_rec --apply-stale-lock
assert_rc 4 "symlink lock blocks unlock"
has "$WORK/out" "lock_apply daily.lock: kept symlink" "symlink kept"
[ -L "$REPO/state/daily.lock" ] && ok "symlink remains" || bad "symlink removed"
[ -d "$REPO/state/real-daily-lock" ] && ok "symlink target remains" || bad "symlink target removed"

echo "9. a live daily writer blocks unlock; an unrelated live PID does not"
init_repo live
mkdir -p "$WORK/writers" "$REPO/state/daily.lock"
cat >"$WORK/writers/grokbot-genseo-daily" <<'EOF'
#!/bin/bash
sleep 180
EOF
chmod +x "$WORK/writers/grokbot-genseo-daily"
"$WORK/writers/grokbot-genseo-daily" &
WRITER_PID=$!
PIDS="$PIDS $WRITER_PID"
sleep 1
printf '%s\n' "$WRITER_PID" >"$REPO/state/daily.lock/pid"
set_age "$REPO/state/daily.lock" 30000
run_rec --apply-stale-lock
assert_rc 4 "live writer blocks unlock"
has "$WORK/out" "lock_apply daily.lock: kept live-writer" "live-writer reason"
[ -d "$REPO/state/daily.lock" ] && ok "lock kept while writer lives" || bad "lock removed under a live writer"
kill -0 "$WRITER_PID" 2>/dev/null && ok "writer was not killed" || bad "writer was killed"
kill "$WRITER_PID" 2>/dev/null || true
wait "$WRITER_PID" 2>/dev/null || true
PIDS=""

init_repo otherpid
mkdir -p "$REPO/state/daily.lock"
sleep 180 &
SLEEP_PID=$!
PIDS="$PIDS $SLEEP_PID"
sleep 1
printf '%s\n' "$SLEEP_PID" >"$REPO/state/daily.lock/pid"
set_age "$REPO/state/daily.lock" 30000
run_rec
assert_rc 0 "unrelated pid dry-run exit 0"
has "$WORK/out" "recorded_pid: $SLEEP_PID alive-other" "reused pid is not a writer"
has "$WORK/out" "lock daily.lock suggested_unlock: yes" "old lock with a reused pid is stale"
[ -d "$REPO/state/daily.lock" ] && ok "dry-run kept the reused-pid lock" || bad "dry-run removed it"
run_rec --apply-stale-lock
assert_rc 0 "unrelated pid unlock exit 0"
has "$WORK/out" "lock_apply daily.lock: removed" "reused-pid lock removed"
[ ! -e "$REPO/state/daily.lock" ] && ok "reused-pid lock is gone" || bad "reused-pid lock remains"
ls -d "$REPO/state"/daily.lock.reconcile-hold.* >/dev/null 2>&1 && bad "hold dir left after removal" || ok "no hold dir left after removal"
kill -0 "$SLEEP_PID" 2>/dev/null && ok "unrelated sleep was not killed" || bad "unrelated sleep was killed"
kill "$SLEEP_PID" 2>/dev/null || true
wait "$SLEEP_PID" 2>/dev/null || true
PIDS=""

echo "9b. a live landing writer blocks the landing lock"
init_repo landlive
mkdir -p "$WORK/writers" "$REPO/state/landing-daily.lock"
cat >"$WORK/writers/run_landing_daily.sh" <<'EOF'
#!/bin/bash
sleep 180
EOF
chmod +x "$WORK/writers/run_landing_daily.sh"
"$WORK/writers/run_landing_daily.sh" &
LAND_PID=$!
PIDS="$PIDS $LAND_PID"
sleep 1
set_age "$REPO/state/landing-daily.lock" 30000
run_rec --apply-stale-lock
assert_rc 4 "live landing writer blocks unlock"
has "$WORK/out" "lock_apply landing-daily.lock: kept live-writer" "landing live-writer reason"
[ -d "$REPO/state/landing-daily.lock" ] && ok "landing lock kept" || bad "landing lock removed under a live writer"
kill -0 "$LAND_PID" 2>/dev/null && ok "landing writer was not killed" || bad "landing writer was killed"
kill "$LAND_PID" 2>/dev/null || true
wait "$LAND_PID" 2>/dev/null || true
PIDS=""

echo "10. a failed fetch refuses --apply and still exits 0 on dry-run"
init_repo nofetch
git -C "$REPO" remote set-url origin "$WORK/no-such-remote"
BEFORE="$(head_of "$REPO")"
run_rec
assert_rc 0 "fetch failure dry-run exit 0"
has "$WORK/out" "fetch: failed" "fetch failed"
[ "$(head_of "$REPO")" = "$BEFORE" ] && ok "failed fetch left HEAD" || bad "failed fetch moved HEAD"
run_rec --apply
assert_rc 3 "fetch failure apply exit 3"
has "$WORK/out" "apply_block: fetch-failed" "fetch-failed block"
[ "$(head_of "$REPO")" = "$BEFORE" ] && ok "refused apply left HEAD" || bad "refused apply moved HEAD"

echo "12. a lock swapped in the removal window is restored, not deleted"
init_repo swapped
mkdir -p "$REPO/state/daily.lock"
printf '%s\n' 99999999 >"$REPO/state/daily.lock/pid"
set_age "$REPO/state/daily.lock" 30000
cat >"$WORK/swap-lock.sh" <<'EOF'
#!/bin/bash
path=$1
mv "$path" "${path}.old-stale"
mkdir "$path"
printf '%s\n' KEEPME >"$path/pid"
printf '%s\n' now >"$path/started"
EOF
chmod +x "$WORK/swap-lock.sh"
export GENSEO_RECONCILE_BEFORE_RM="$WORK/swap-lock.sh"
run_rec --apply-stale-lock
unset GENSEO_RECONCILE_BEFORE_RM
assert_rc 4 "replaced lock is not cleared"
has "$WORK/out" "lock_apply daily.lock: kept changed" "swap is kept changed"
lacks "$WORK/out" "lock_apply daily.lock: removed" "swap was not reported removed"
grep -F -q KEEPME "$REPO/state/daily.lock/pid" && ok "replacement pid kept" || bad "replacement pid missing"
[ -d "$REPO/state/daily.lock.old-stale" ] && ok "previous lock dir was not deleted" || bad "previous lock dir deleted"
[ -f "$REPO/state/daily.lock.old-stale/pid" ] && ok "previous pid file kept" || bad "previous pid file deleted"
ls -d "$REPO/state"/daily.lock.reconcile-hold.* >/dev/null 2>&1 && bad "hold dir left after restore" || ok "hold dir not left after restore"

echo "13. an empty process list does not clear a stale lock or fast-forward"
init_repo nops
advance_origin nops
mkdir -p "$REPO/state/daily.lock"
printf '%s\n' 99999999 >"$REPO/state/daily.lock/pid"
set_age "$REPO/state/daily.lock" 30000
mkdir -p "$WORK/nops-bin"
cat >"$WORK/nops-bin/ps" <<'EOF'
#!/bin/bash
exit 0
EOF
chmod +x "$WORK/nops-bin/ps"
BEFORE="$(head_of "$REPO")"
OLD_PATH=$PATH
PATH="$WORK/nops-bin:$PATH"
export PATH
run_rec --apply-stale-lock
PATH="$OLD_PATH"
export PATH
assert_rc 4 "empty ps blocks unlock"
has "$WORK/out" "lock_apply daily.lock: kept process-list-unknown" "process list unknown"
has "$WORK/out" "lock daily.lock suggested_unlock: no" "empty ps does not suggest unlock"
[ -d "$REPO/state/daily.lock" ] && ok "lock kept when ps is empty" || bad "lock removed when ps is empty"
PATH="$WORK/nops-bin:$PATH"
export PATH
run_rec --apply
PATH="$OLD_PATH"
export PATH
assert_rc 3 "empty ps blocks apply"
has "$WORK/out" "apply_block: process-list-unknown" "apply blocked without a process list"
[ "$(head_of "$REPO")" = "$BEFORE" ] && ok "apply without ps left HEAD" || bad "apply without ps moved HEAD"

echo "14. GIT_DIR does not make --apply operate on another repository"
init_repo gitdir
advance_origin gitdir
DECOY="$WORK/decoy-gitdir"
rm -rf "$DECOY"
git init -b main "$DECOY" >/dev/null 2>&1 || exit 1
git_cfg "$DECOY"
printf '%s\n' decoy >"$DECOY/README"
git -C "$DECOY" add README
git -C "$DECOY" commit -m decoy >/dev/null 2>&1 || exit 1
DECOY_HEAD="$(head_of "$DECOY")"
export GIT_DIR="$DECOY/.git"
export GIT_WORK_TREE="$DECOY"
run_rec --apply
rc_save=$RC
unset GIT_DIR GIT_WORK_TREE
RC=$rc_save
assert_rc 0 "apply with GIT_DIR set still exits 0"
has "$WORK/out" "apply: fast-forward" "ff happened in GENSEO_HOME"
[ "$(head_of "$REPO")" = "$(git -C "$REPO" rev-parse origin/main)" ] && ok "GENSEO_HOME fast-forwarded" || bad "GENSEO_HOME was not fast-forwarded"
[ "$(head_of "$DECOY")" = "$DECOY_HEAD" ] && ok "decoy repo was not modified" || bad "decoy repo changed"

echo "15. --apply fast-forwards origin/main, reinstalls the wrapper, and verifies the model map"
ORIG_HOME="${HOME:-}"
init_repo catchup
mkdir -p "$REPO/deploy" "$REPO/scripts"
cp "$ROOT/deploy/grokbot-genseo-daily.sh" "$REPO/deploy/grokbot-genseo-daily.sh"
cp "$ROOT/deploy/com.pati.genseo-daily.macbook.plist" "$REPO/deploy/com.pati.genseo-daily.macbook.plist"
cp "$ROOT/scripts/genseo_daily_lock.sh" "$REPO/scripts/genseo_daily_lock.sh"
cp "$ROOT/scripts/genseo_group_timeout.sh" "$REPO/scripts/genseo_group_timeout.sh"
cp "$ROOT/scripts/genseo_wait_for_network.sh" "$REPO/scripts/genseo_wait_for_network.sh"
cp "$ROOT/scripts/genseo_sync_main.sh" "$REPO/scripts/genseo_sync_main.sh"
cp "$ROOT/scripts/genseo_power_assert.sh" "$REPO/scripts/genseo_power_assert.sh"
cp "$ROOT/scripts/genseo_errlog.sh" "$REPO/scripts/genseo_errlog.sh"
cp "$ROOT/scripts/genseo_model_map.json" "$REPO/scripts/genseo_model_map.json"
cp "$ROOT/scripts/run_landing_daily.sh" "$REPO/scripts/run_landing_daily.sh"
cp "$ROOT/scripts/landing_publisher.py" "$REPO/scripts/landing_publisher.py"
cp "$ROOT/scripts/run_landing_headless.sh" "$REPO/scripts/run_landing_headless.sh"
git -C "$REPO" add deploy scripts
git -C "$REPO" commit -m "pipeline files" >/dev/null 2>&1 || exit 1
git -C "$REPO" push origin main >/dev/null 2>&1 || exit 1
advance_origin catchup
CATCH_HOME="$WORK/home-catchup"
rm -rf "$CATCH_HOME"
mkdir -p "$CATCH_HOME"
export HOME="$CATCH_HOME"
export GENSEO_INSTALL_WRAPPER_TEST=1
BEFORE="$(head_of "$REPO")"
BARE_BEFORE="$(bare_main)"
run_rec
assert_rc 0 "pipeline dry-run exit 0"
has "$WORK/out" "catchup: would fast-forward on --apply" "pipeline dry-run would fast-forward"
has "$WORK/out" "wrapper_install: planned" "dry-run plans the wrapper copy"
has "$WORK/out" "wrapper_install_detail: dry-run: yes" "installer dry-run writes nothing"
has "$WORK/out" "wrapper_install_detail: launchd: not started" "dry-run does not start launchd"
has "$WORK/out" "verify_scope: origin/main" "dry-run verifies origin/main"
has "$WORK/out" "verify_model_map: ok" "origin model map is ok"
has "$WORK/out" "verify_landing_draft_only: ok" "origin landing lane is draft-only"
has "$WORK/out" "verify_wrapper_feed_retry: ok" "origin wrapper has the live-feed retry"
has "$WORK/out" "verify_wrapper_role_default: primary" "origin wrapper defaults to primary"
has "$WORK/out" "verify_wrapper_net_wait: ok" "origin wrapper waits for DNS"
has "$WORK/out" "verify_landing_net_wait: ok" "origin landing wrapper waits for DNS"
has "$WORK/out" "verify_repo_plist_role: ok" "repo plist is primary MB"
has "$WORK/out" "verify: ok" "dry-run verify ok"
has "$WORK/out" "result: ok" "pipeline dry-run result ok"
lacks "$WORK/out" "wrapper_install: copied" "dry-run does not report a copy"
[ "$(head_of "$REPO")" = "$BEFORE" ] && ok "pipeline dry-run left HEAD" || bad "pipeline dry-run moved HEAD"
[ "$(bare_main)" = "$BARE_BEFORE" ] && ok "pipeline dry-run did not push" || bad "pipeline dry-run pushed"
[ ! -e "$CATCH_HOME/bin/grokbot-genseo-daily.sh" ] && ok "dry-run did not write ~/bin" || bad "dry-run wrote ~/bin"
run_rec --apply
assert_rc 0 "pipeline apply exit 0"
has "$WORK/out" "catchup_cmd: git merge --ff-only origin/main" "apply names ff-only"
has "$WORK/out" "apply: fast-forward" "pipeline apply fast-forwarded"
has "$WORK/out" "wrapper_install: copied" "apply copied the wrapper"
has "$WORK/out" "wrapper_dest_match: yes" "copied wrapper matches the checkout"
has "$WORK/out" "wrapper_install_detail: launchd: not started" "apply does not start launchd"
has "$WORK/out" "verify_scope: worktree" "apply verifies the work tree"
has "$WORK/out" "verify_model_map: ok" "work tree model map is ok"
has "$WORK/out" "verify_landing_draft_only: ok" "work tree landing lane is draft-only"
has "$WORK/out" "verify_wrapper_net_wait: ok" "work tree wrapper waits for DNS"
has "$WORK/out" "verify_landing_net_wait: ok" "work tree landing wrapper waits for DNS"
has "$WORK/out" "verify: ok" "apply verify ok"
has "$WORK/out" "result: ok" "pipeline apply result ok"
lacks "$WORK/out" "shopify_publisher.py" "apply output does not name the article publisher"
[ "$(head_of "$REPO")" = "$(git -C "$REPO" rev-parse origin/main)" ] && ok "pipeline HEAD matches origin/main" || bad "pipeline HEAD is not origin/main"
[ "$(bare_main)" = "$BARE_BEFORE" ] && ok "pipeline apply did not push" || bad "pipeline apply pushed"
cmp -s "$REPO/deploy/grokbot-genseo-daily.sh" "$CATCH_HOME/bin/grokbot-genseo-daily.sh" && ok "installed wrapper bytes match deploy/" || bad "installed wrapper differs"
grep -F -q 'GENSEO_LIVE_FEED_RETRIES' "$CATCH_HOME/bin/grokbot-genseo-daily.sh" && ok "installed wrapper has the feed retry" || bad "installed wrapper lacks the feed retry"
grep -F -q 'GENSEO_HOST_ROLE:-primary' "$CATCH_HOME/bin/grokbot-genseo-daily.sh" && ok "installed wrapper defaults to primary" || bad "installed wrapper role default drifted"
grep -F -q 'genseo_wait_for_network.sh' "$CATCH_HOME/bin/grokbot-genseo-daily.sh" && ok "installed wrapper waits for DNS" || bad "installed wrapper has no DNS wait"
grep -F -q 'network not ready — timeout' "$CATCH_HOME/bin/grokbot-genseo-daily.sh" && ok "installed wrapper names the DNS timeout" || bad "installed wrapper missing the DNS timeout line"
[ -f "$REPO/scripts/genseo_wait_for_network.sh" ] && ok "fast-forward left the DNS helper in the checkout" || bad "DNS helper missing after fast-forward"
[ -x "$CATCH_HOME/bin/grokbot-genseo-daily.sh" ] && ok "installed wrapper is executable" || bad "installed wrapper is not executable"

echo "15b. a landing --live flag on origin fails verify and does not publish"
init_repo badland
mkdir -p "$REPO/deploy" "$REPO/scripts"
cp "$ROOT/deploy/grokbot-genseo-daily.sh" "$REPO/deploy/grokbot-genseo-daily.sh"
cp "$ROOT/scripts/genseo_daily_lock.sh" "$REPO/scripts/genseo_daily_lock.sh"
cp "$ROOT/scripts/genseo_group_timeout.sh" "$REPO/scripts/genseo_group_timeout.sh"
cp "$ROOT/scripts/genseo_wait_for_network.sh" "$REPO/scripts/genseo_wait_for_network.sh"
cp "$ROOT/scripts/genseo_sync_main.sh" "$REPO/scripts/genseo_sync_main.sh"
cp "$ROOT/scripts/genseo_power_assert.sh" "$REPO/scripts/genseo_power_assert.sh"
cp "$ROOT/scripts/genseo_errlog.sh" "$REPO/scripts/genseo_errlog.sh"
cp "$ROOT/scripts/genseo_model_map.json" "$REPO/scripts/genseo_model_map.json"
cp "$ROOT/scripts/run_landing_daily.sh" "$REPO/scripts/run_landing_daily.sh"
cp "$ROOT/scripts/landing_publisher.py" "$REPO/scripts/landing_publisher.py"
cp "$ROOT/scripts/run_landing_headless.sh" "$REPO/scripts/run_landing_headless.sh"
git -C "$REPO" add deploy scripts
git -C "$REPO" commit -m "pipeline files" >/dev/null 2>&1 || exit 1
git -C "$REPO" push origin main >/dev/null 2>&1 || exit 1
POISON="$WORK/other-badland"
rm -rf "$POISON"
git clone "$BARE" "$POISON" >/dev/null 2>&1 || exit 1
git_cfg "$POISON"
printf '\n%s\n' 'python3 scripts/landing_publisher.py spec.json --live' >> "$POISON/scripts/run_landing_daily.sh"
git -C "$POISON" add scripts/run_landing_daily.sh
git -C "$POISON" commit -m "bad live flag" >/dev/null 2>&1 || exit 1
git -C "$POISON" push origin main >/dev/null 2>&1 || exit 1
BAD_HOME="$WORK/home-badland"
rm -rf "$BAD_HOME"
mkdir -p "$BAD_HOME"
export HOME="$BAD_HOME"
BEFORE="$(head_of "$REPO")"
run_rec
assert_rc 0 "bad landing dry-run still exits 0"
has "$WORK/out" "verify_landing_draft_only: live-flag" "dry-run sees the origin --live flag"
has "$WORK/out" "verify: fail" "dry-run verify fails"
has "$WORK/out" "result: verify-failed" "dry-run result names the verify failure"
[ "$(head_of "$REPO")" = "$BEFORE" ] && ok "bad landing dry-run left HEAD" || bad "bad landing dry-run moved HEAD"
[ ! -e "$BAD_HOME/bin/grokbot-genseo-daily.sh" ] && ok "bad landing dry-run wrote no wrapper" || bad "bad landing dry-run wrote a wrapper"
run_rec --apply
assert_rc 5 "bad landing apply exit 5"
has "$WORK/out" "apply: fast-forward" "bad landing still fast-forwards"
has "$WORK/out" "verify_landing_draft_only: live-flag" "apply sees the --live flag"
has "$WORK/out" "verify: fail" "apply verify fails"
has "$WORK/out" "result: catch-up-incomplete" "apply result is catch-up-incomplete"
has "$WORK/out" "wrapper_install_detail: launchd: not started" "failed verify still does not start launchd"
lacks "$WORK/out" "shopify_publisher.py" "failed verify does not name the article publisher"
grep -F -q 'python3 scripts/landing_publisher.py spec.json --live' "$REPO/scripts/run_landing_daily.sh" && ok "fast-forward brought the bad line in for the operator to see" || bad "fast-forward did not update the landing script"

echo "15c. an empty writer model map fails verify after the fast-forward"
init_repo badmap
mkdir -p "$REPO/deploy" "$REPO/scripts"
cp "$ROOT/deploy/grokbot-genseo-daily.sh" "$REPO/deploy/grokbot-genseo-daily.sh"
cp "$ROOT/scripts/genseo_daily_lock.sh" "$REPO/scripts/genseo_daily_lock.sh"
cp "$ROOT/scripts/genseo_group_timeout.sh" "$REPO/scripts/genseo_group_timeout.sh"
cp "$ROOT/scripts/genseo_wait_for_network.sh" "$REPO/scripts/genseo_wait_for_network.sh"
cp "$ROOT/scripts/genseo_sync_main.sh" "$REPO/scripts/genseo_sync_main.sh"
cp "$ROOT/scripts/genseo_power_assert.sh" "$REPO/scripts/genseo_power_assert.sh"
cp "$ROOT/scripts/genseo_errlog.sh" "$REPO/scripts/genseo_errlog.sh"
cp "$ROOT/scripts/genseo_model_map.json" "$REPO/scripts/genseo_model_map.json"
cp "$ROOT/scripts/run_landing_daily.sh" "$REPO/scripts/run_landing_daily.sh"
cp "$ROOT/scripts/landing_publisher.py" "$REPO/scripts/landing_publisher.py"
cp "$ROOT/scripts/run_landing_headless.sh" "$REPO/scripts/run_landing_headless.sh"
git -C "$REPO" add deploy scripts
git -C "$REPO" commit -m "pipeline files" >/dev/null 2>&1 || exit 1
git -C "$REPO" push origin main >/dev/null 2>&1 || exit 1
POISON="$WORK/other-badmap"
rm -rf "$POISON"
git clone "$BARE" "$POISON" >/dev/null 2>&1 || exit 1
git_cfg "$POISON"
printf '%s\n' '{"modelOverrides":{}}' > "$POISON/scripts/genseo_model_map.json"
git -C "$POISON" add scripts/genseo_model_map.json
git -C "$POISON" commit -m "empty model map" >/dev/null 2>&1 || exit 1
git -C "$POISON" push origin main >/dev/null 2>&1 || exit 1
export HOME="$WORK/home-badmap"
mkdir -p "$HOME"
run_rec --apply
assert_rc 5 "empty model map apply exit 5"
has "$WORK/out" "apply: fast-forward" "empty map still fast-forwards"
has "$WORK/out" "verify_model_map: invalid" "empty model map is invalid"
has "$WORK/out" "result: catch-up-incomplete" "empty map result is catch-up-incomplete"

echo "15d. local-only commits still block the fast-forward and the wrapper copy"
init_repo localblock
mkdir -p "$REPO/deploy" "$REPO/scripts"
cp "$ROOT/deploy/grokbot-genseo-daily.sh" "$REPO/deploy/grokbot-genseo-daily.sh"
cp "$ROOT/scripts/genseo_daily_lock.sh" "$REPO/scripts/genseo_daily_lock.sh"
cp "$ROOT/scripts/genseo_group_timeout.sh" "$REPO/scripts/genseo_group_timeout.sh"
cp "$ROOT/scripts/genseo_wait_for_network.sh" "$REPO/scripts/genseo_wait_for_network.sh"
cp "$ROOT/scripts/genseo_sync_main.sh" "$REPO/scripts/genseo_sync_main.sh"
cp "$ROOT/scripts/genseo_power_assert.sh" "$REPO/scripts/genseo_power_assert.sh"
cp "$ROOT/scripts/genseo_errlog.sh" "$REPO/scripts/genseo_errlog.sh"
cp "$ROOT/scripts/genseo_model_map.json" "$REPO/scripts/genseo_model_map.json"
cp "$ROOT/scripts/run_landing_daily.sh" "$REPO/scripts/run_landing_daily.sh"
cp "$ROOT/scripts/landing_publisher.py" "$REPO/scripts/landing_publisher.py"
cp "$ROOT/scripts/run_landing_headless.sh" "$REPO/scripts/run_landing_headless.sh"
git -C "$REPO" add deploy scripts
git -C "$REPO" commit -m "pipeline files" >/dev/null 2>&1 || exit 1
git -C "$REPO" push origin main >/dev/null 2>&1 || exit 1
advance_origin localblock
printf '%s\n' 'local only' >"$REPO/LOCAL"
git -C "$REPO" add LOCAL
git -C "$REPO" commit -m "local only" >/dev/null 2>&1 || exit 1
LOCAL_SHA="$(head_of "$REPO")"
BARE_BEFORE="$(bare_main)"
export HOME="$WORK/home-localblock"
mkdir -p "$HOME"
run_rec --apply
assert_rc 3 "local-only apply still refused"
has "$WORK/out" "apply_block: local-commits-not-on-origin" "local-only block"
has "$WORK/out" "apply_next: do not run git push --force" "local-only still refuses force-push"
has "$WORK/out" "wrapper_install: skipped not-fast-forwarded" "wrapper is not copied when fast-forward is refused"
[ "$(head_of "$REPO")" = "$LOCAL_SHA" ] && ok "local-only commit kept" || bad "local-only commit moved"
[ "$(bare_main)" = "$BARE_BEFORE" ] && ok "local-only commit was not pushed" || bad "local-only commit was pushed"
[ ! -e "$HOME/bin/grokbot-genseo-daily.sh" ] && ok "refused apply wrote no wrapper" || bad "refused apply wrote a wrapper"
if [ -n "$ORIG_HOME" ]; then
  export HOME="$ORIG_HOME"
else
  unset HOME
fi
unset GENSEO_INSTALL_WRAPPER_TEST

echo "11. the workspace checkout was not fetched or edited by this test"
END_STATUS="$(git -C "$ROOT" status --porcelain)"
END_HEAD="$(git -C "$ROOT" rev-parse HEAD)"
[ "$END_HEAD" = "$START_HEAD" ] && ok "workspace HEAD unchanged" || bad "workspace HEAD changed"
[ "$END_STATUS" = "$START_STATUS" ] && ok "workspace status unchanged" || bad "workspace status changed"

echo
printf '%s passed, %s failed\n' "$PASS" "$FAIL"
[ "$FAIL" = 0 ]

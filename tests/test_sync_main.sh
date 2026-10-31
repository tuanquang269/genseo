#!/bin/bash
# Pre-run fast-forward of origin/main for the article and landing launchd wrappers.
# Temp git repos only. No Shopify, no network, no launchd, no push.
#   bash tests/test_sync_main.sh
# Syntax target is bash 3.2 (macOS /bin/bash).
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HELPER="$ROOT/scripts/genseo_sync_main.sh"
ARTICLE="$ROOT/deploy/grokbot-genseo-daily.sh"
LANDING="$ROOT/scripts/run_landing_daily.sh"
INSTALL="$ROOT/scripts/install_mac_daily_wrapper.sh"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/sync-main.XXXXXX")" || exit 1
PASS=0
FAIL=0
RC=0
START_STATUS="$(git -C "$ROOT" status --porcelain)"
START_HEAD="$(git -C "$ROOT" rev-parse HEAD)"

HOLD_PIDS=""
cleanup() {
  local p
  for p in $HOLD_PIDS; do
    kill "$p" 2>/dev/null || true
    wait "$p" 2>/dev/null || true
  done
  rm -rf "$WORK"
}
trap cleanup EXIT

ok() { PASS=$((PASS + 1)); printf '  ok   %s\n' "$*"; }
bad() { FAIL=$((FAIL + 1)); printf '  FAIL %s\n' "$*"; }

show_fail() {
  if [ -f "$WORK/out" ]; then printf '    stdout: %s\n' "$(tr '\n' '|' <"$WORK/out")"; fi
  if [ -f "$WORK/err" ]; then printf '    stderr: %s\n' "$(tr '\n' '|' <"$WORK/err")"; fi
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
  git -C "$1" config user.email "sync-test@example.com"
  git -C "$1" config user.name "sync-test"
  git -C "$1" config commit.gpgsign false
}

init_repo() {
  local name="$1"
  BARE="$WORK/bare-$name"
  REPO="$WORK/repo-$name"
  rm -rf "$BARE" "$REPO"
  git init --bare -b main "$BARE" >/dev/null 2>&1 || return 1
  git init -b main "$REPO" >/dev/null 2>&1 || return 1
  git_cfg "$REPO"
  printf '%s\n' 'logs/' 'state/' >"$REPO/.gitignore"
  printf '%s\n' 'v1' >"$REPO/README"
  git -C "$REPO" add .gitignore README
  git -C "$REPO" commit -m "v1" >/dev/null 2>&1 || return 1
  git -C "$REPO" remote add origin "$BARE"
  git -C "$REPO" push origin main >/dev/null 2>&1 || return 1
}

advance_origin() {
  local name="$1"
  local other="$WORK/other-$name"
  rm -rf "$other"
  git clone "$BARE" "$other" >/dev/null 2>&1 || return 1
  git_cfg "$other"
  printf '%s\n' 'from-origin' >"$other/FROM_ORIGIN"
  git -C "$other" add FROM_ORIGIN
  git -C "$other" commit -m "v2" >/dev/null 2>&1 || return 1
  git -C "$other" push origin main >/dev/null 2>&1 || return 1
}

head_of() { git -C "$1" rev-parse HEAD; }
bare_main() { git -C "$BARE" rev-parse main; }

# Call the helper with $0 outside the checkout so a fast-forward is allowed.
run_sync() {
  : >"$WORK/out"
  : >"$WORK/err"
  env -i PATH="/usr/bin:/bin" GIT_TERMINAL_PROMPT=0 \
    ${SYNC_ENV:-} \
    bash -c '
      set -uo pipefail
      G=$1
      . "$2"
      genseo_sync_origin_main ""
      printf "sync_rc:%s\n" "$?"
    ' _ "$REPO" "$HELPER" >"$WORK/out" 2>"$WORK/err"
  RC=$?
}

order_between() {
  # order_between <file> <earlier-literal> <later-literal> <label>
  # index(), not a regex: macOS awk -v turns \$ into $ and $ is end-of-line.
  local file=$1 early=$2 late=$3 label=$4
  if awk -v early="$early" -v late="$late" '
    index($0, early) && !e { e=NR }
    index($0, late) && !l { l=NR }
    END { exit !(e && l && e < l) }
  ' "$file"; then
    ok "$label"
  else
    bad "$label"
  fi
}

echo "1. syntax, direct exec, fetch is ff-only, and the wrappers call it after DNS"
bash -n "$HELPER" && ok "bash -n helper" || bad "bash -n helper"
bash -n "$ARTICLE" && ok "bash -n article wrapper" || bad "bash -n article wrapper"
bash -n "$LANDING" && ok "bash -n landing wrapper" || bad "bash -n landing wrapper"
bash -n "$INSTALL" && ok "bash -n installer" || bad "bash -n installer"
: >"$WORK/out"
: >"$WORK/err"
env -i PATH="/usr/bin:/bin" bash "$HELPER" >"$WORK/out" 2>"$WORK/err"
RC=$?
assert_rc 2 "direct exec refuses"
lacks "$WORK/out" "fast-forwarded" "direct exec does not fast-forward"
if awk '
  /^[[:space:]]*#/ { next }
  /git[[:space:]]+push/ { print NR": "$0; bad=1 }
  /git[[:space:]]+reset/ { print NR": "$0; bad=1 }
  /git[[:space:]]+rebase/ { print NR": "$0; bad=1 }
  /git[[:space:]]+clean/ { print NR": "$0; bad=1 }
  /git[[:space:]]+checkout/ { print NR": "$0; bad=1 }
  /--hard/ { print NR": "$0; bad=1 }
  /--force/ { print NR": "$0; bad=1 }
  END { exit bad+0 }
' "$HELPER"; then
  ok "helper has no push, reset, rebase, clean, checkout, or force"
else
  bad "helper contains a forbidden git command"
fi
grep -F -q 'fetch origin main' "$HELPER" && ok "helper fetches origin main" || bad "helper missing fetch origin main"
grep -F -q 'merge --ff-only origin/main' "$HELPER" && ok "helper merges ff-only" || bad "helper missing ff-only"
order_between "$ARTICLE" 'genseo_exec_stable_copy grokbot-genseo-daily' 'genseo_wait_for_network;' "article copies itself aside before the network wait"
order_between "$ARTICLE" 'genseo_daily_lock_acquire' 'genseo_wait_for_network;' "article still takes the lock before the network wait"
order_between "$ARTICLE" 'genseo_wait_for_network;' 'genseo_sync_origin_main ' "article syncs after the network wait"
order_between "$ARTICLE" 'genseo_sync_origin_main ' '$(live_count)' "article syncs before the first live count"
order_between "$LANDING" 'genseo_exec_stable_copy run_landing_daily' 'genseo_wait_for_network;' "landing copies itself aside before the network wait"
order_between "$LANDING" 'mkdir "$LOCK"' 'genseo_wait_for_network;' "landing still takes the lock before the network wait"
order_between "$LANDING" 'genseo_wait_for_network;' 'genseo_sync_origin_main ' "landing syncs after the network wait"
order_between "$LANDING" 'genseo_sync_origin_main ' 'guard; g=' "landing syncs before the first guard"
grep -F -q 'GENSEO_LANDING_DAILY=1 GENSEO_LANDING_DRAFT=1' "$LANDING" && ok "landing stays draft-only" || bad "landing draft env changed"
grep -F -q 'genseo_return_publish_branch_to_main' "$ARTICLE" && ok "article wrapper returns publish branches to main" || bad "article wrapper does not return to main"
grep -F -q 'genseo_return_publish_branch_to_main' "$LANDING" && ok "landing wrapper returns publish branches to main" || bad "landing wrapper does not return to main"
if awk '
  /^[[:space:]]*#/ { next }
  /--live/ { print NR": "$0; bad=1 }
  END { exit bad+0 }
' "$LANDING"; then
  ok "landing wrapper gained no --live flag"
else
  bad "landing wrapper has a --live flag outside a comment"
fi

echo "2. fast-forward updates main, ignores logs/, and does not push or run hooks"
if ! init_repo ff || ! advance_origin ff; then
  bad "ff fixture"
else
  ok "ff fixture"
  mkdir -p "$REPO/logs"
  printf '%s\n' 'keep-log' >"$REPO/logs/noise"
  cat >"$REPO/.git/hooks/post-merge" <<'EOF'
#!/bin/bash
printf '%s\n' ran >"$(git rev-parse --show-toplevel)/HOOK_RAN"
EOF
  chmod 755 "$REPO/.git/hooks/post-merge"
  before=$(head_of "$REPO")
  bare_before=$(bare_main)
  git -C "$REPO" config --unset user.email || true
  git -C "$REPO" config --unset user.name || true
  run_sync
  assert_rc 0 "fast-forward exits 0"
  has "$WORK/out" "sync_rc:0" "fast-forward function returns 0"
  has "$WORK/out" "origin/main: git fetch origin main" "fast-forward logs the fetch"
  has "$WORK/out" "origin/main: git merge --ff-only origin/main" "fast-forward logs the merge"
  has "$WORK/out" "origin/main: fast-forwarded" "fast-forward logs the result"
  [ "$(head_of "$REPO")" = "$(git -C "$REPO" rev-parse origin/main)" ] && ok "HEAD matches origin/main" || bad "HEAD is not origin/main"
  [ "$(head_of "$REPO")" != "$before" ] && ok "HEAD moved" || bad "HEAD did not move"
  [ -f "$REPO/FROM_ORIGIN" ] && ok "origin file is in the work tree" || bad "origin file missing"
  [ "$(cat "$REPO/logs/noise")" = "keep-log" ] && ok "ignored log survived" || bad "ignored log changed"
  [ ! -e "$REPO/HOOK_RAN" ] && ok "post-merge hook did not run" || bad "post-merge hook ran"
  [ "$(bare_main)" = "$bare_before" ] && ok "fast-forward did not push" || bad "fast-forward pushed"
fi

echo "3. untracked files that do not overlap fast-forward; overlapping edits are preserved"
if ! init_repo dirty || ! advance_origin dirty; then
  bad "dirty fixture"
else
  ok "dirty fixture"
  printf '%s\n' 'local-edit' >"$REPO/README"
  before=$(head_of "$REPO")
  run_sync
  assert_rc 0 "dirty exits 0"
  has "$WORK/out" "tracked local edits kept" "dirty edit is kept when origin does not touch it"
  has "$WORK/out" "fast-forwarded" "dirty non-overlap still fast-forwards"
  [ "$(head_of "$REPO")" = "$(git -C "$REPO" rev-parse origin/main)" ] && ok "dirty non-overlap HEAD matches origin/main" || bad "dirty non-overlap HEAD is not origin/main"
  [ "$(head_of "$REPO")" != "$before" ] && ok "dirty non-overlap HEAD moved" || bad "dirty non-overlap HEAD stayed"
  [ "$(cat "$REPO/README")" = "local-edit" ] && ok "dirty edit kept in the work tree" || bad "dirty edit lost"
  [ -f "$REPO/FROM_ORIGIN" ] && ok "dirty non-overlap took the origin file" || bad "dirty non-overlap missed the origin file"
fi

if ! init_repo overlap || ! advance_origin overlap; then
  bad "overlap fixture"
else
  ok "overlap fixture"
  printf '%s\n' 'from-origin-readme' >"$WORK/other-overlap/README"
  git_cfg "$WORK/other-overlap"
  git -C "$WORK/other-overlap" add README
  git -C "$WORK/other-overlap" commit -m "readme from origin" >/dev/null 2>&1 || { bad "overlap origin commit"; }
  git -C "$WORK/other-overlap" push origin main >/dev/null 2>&1 || { bad "overlap origin push"; }
  printf '%s\n' 'local-edit' >"$REPO/README"
  before=$(head_of "$REPO")
  run_sync
  assert_rc 0 "overlap exits 0"
  has "$WORK/out" "preserved tracked edits in stash:" "overlap stashes the tracked edit"
  has "$WORK/out" "fast-forwarded" "overlap still fast-forwards"
  [ "$(head_of "$REPO")" = "$(git -C "$REPO" rev-parse origin/main)" ] && ok "overlap HEAD matches origin/main" || bad "overlap HEAD is not origin/main"
  [ "$(head_of "$REPO")" != "$before" ] && ok "overlap HEAD moved" || bad "overlap HEAD stayed"
  [ "$(cat "$REPO/README")" = "from-origin-readme" ] && ok "overlap work tree has origin README" || bad "overlap work tree kept the local README"
  git -C "$REPO" --no-pager stash show -p >"$WORK/stash.patch" 2>"$WORK/stash.err" || true
  grep -F -q 'local-edit' "$WORK/stash.patch" && ok "overlap edit is in the stash" || bad "overlap edit missing from the stash"
  [ -f "$REPO/FROM_ORIGIN" ] && ok "overlap took the origin file" || bad "overlap missed the origin file"
fi

if ! init_repo untracked || ! advance_origin untracked; then
  bad "untracked fixture"
else
  ok "untracked fixture"
  printf '%s\n' 'scratch' >"$REPO/scratch.txt"
  before=$(head_of "$REPO")
  run_sync
  assert_rc 0 "untracked exits 0"
  has "$WORK/out" "untracked files kept" "untracked non-overlap is kept"
  has "$WORK/out" "fast-forwarded" "untracked non-overlap still fast-forwards"
  [ "$(head_of "$REPO")" = "$(git -C "$REPO" rev-parse origin/main)" ] && ok "untracked HEAD matches origin/main" || bad "untracked HEAD is not origin/main"
  [ "$(head_of "$REPO")" != "$before" ] && ok "untracked HEAD moved" || bad "untracked HEAD stayed"
  [ "$(cat "$REPO/scratch.txt")" = "scratch" ] && ok "untracked file kept" || bad "untracked file lost"
  [ -f "$REPO/FROM_ORIGIN" ] && ok "untracked checkout took the origin file" || bad "untracked checkout missed the origin file"
fi

if ! init_repo clash || ! advance_origin clash; then
  bad "clash fixture"
else
  ok "clash fixture"
  printf '%s\n' 'local scratch' >"$REPO/FROM_ORIGIN"
  before=$(head_of "$REPO")
  run_sync
  assert_rc 0 "clash exits 0"
  has "$WORK/out" "untracked file would be overwritten (FROM_ORIGIN)" "clash names the untracked file"
  has "$WORK/out" "continuing on the current checkout" "clash continues"
  [ "$(head_of "$REPO")" = "$before" ] && ok "clash HEAD unchanged" || bad "clash HEAD moved"
  [ "$(cat "$REPO/FROM_ORIGIN")" = "local scratch" ] && ok "clash file kept" || bad "clash file overwritten"
  lacks "$WORK/out" "fast-forwarded" "clash did not fast-forward"
fi

if ! init_repo ahead; then
  bad "ahead fixture"
else
  ok "ahead fixture"
  printf '%s\n' 'only-local' >"$REPO/LOCAL_ONLY"
  git_cfg "$REPO"
  git -C "$REPO" add LOCAL_ONLY
  git -C "$REPO" commit -m "local only" >/dev/null 2>&1 || { bad "ahead commit"; }
  local_sha=$(head_of "$REPO")
  bare_before=$(bare_main)
  run_sync
  assert_rc 0 "ahead exits 0"
  has "$WORK/out" "local commits are not on origin/main" "ahead warns"
  [ "$(head_of "$REPO")" = "$local_sha" ] && ok "ahead commit kept" || bad "ahead commit moved"
  [ -f "$REPO/LOCAL_ONLY" ] && ok "ahead file kept" || bad "ahead file lost"
  [ "$(bare_main)" = "$bare_before" ] && ok "ahead commit was not pushed" || bad "ahead commit was pushed"
  lacks "$WORK/out" "fast-forwarded" "ahead did not fast-forward"
fi

if ! init_repo diverge || ! advance_origin diverge; then
  bad "diverge fixture"
else
  ok "diverge fixture"
  printf '%s\n' 'only-local' >"$REPO/LOCAL_ONLY"
  git_cfg "$REPO"
  git -C "$REPO" add LOCAL_ONLY
  git -C "$REPO" commit -m "local only" >/dev/null 2>&1 || { bad "diverge commit"; }
  local_sha=$(head_of "$REPO")
  run_sync
  assert_rc 0 "diverged exits 0"
  has "$WORK/out" "local commits are not on origin/main" "diverged warns"
  [ "$(head_of "$REPO")" = "$local_sha" ] && ok "diverged local commit kept" || bad "diverged local commit moved"
  [ -f "$REPO/LOCAL_ONLY" ] && ok "diverged local file kept" || bad "diverged local file lost"
  [ ! -e "$REPO/FROM_ORIGIN" ] && ok "diverged checkout did not take the origin file" || bad "diverged checkout took the origin file"
fi

if ! init_repo side || ! advance_origin side; then
  bad "side fixture"
else
  ok "side fixture"
  git -C "$REPO" checkout -b side >/dev/null 2>&1 || { bad "side branch"; }
  before=$(head_of "$REPO")
  run_sync
  assert_rc 0 "side branch exits 0"
  has "$WORK/out" "HEAD is side, not main" "side branch warns"
  [ "$(git -C "$REPO" symbolic-ref --short HEAD)" = "side" ] && ok "stayed on side" || bad "left side"
  [ "$(head_of "$REPO")" = "$before" ] && ok "side HEAD unchanged" || bad "side HEAD moved"
  [ ! -e "$REPO/FROM_ORIGIN" ] && ok "side branch did not take the origin file" || bad "side branch took the origin file"
fi

if ! init_repo detach || ! advance_origin detach; then
  bad "detach fixture"
else
  ok "detach fixture"
  git -C "$REPO" checkout --detach >/dev/null 2>&1 || { bad "detach"; }
  before=$(head_of "$REPO")
  run_sync
  assert_rc 0 "detached exits 0"
  has "$WORK/out" "not main" "detached warns"
  [ "$(head_of "$REPO")" = "$before" ] && ok "detached HEAD unchanged" || bad "detached HEAD moved"
fi

echo "3b. a publish branch returns to main; another job blocks the fast-forward"
if ! init_repo pubin || ! advance_origin pubin; then
  bad "pubin fixture"
else
  ok "pubin fixture"
  old=$(head_of "$REPO")
  git -C "$REPO" checkout -b publish/mb1012-3 >/dev/null 2>&1 || { bad "pubin branch"; }
  run_sync
  assert_rc 0 "contained publish branch exits 0"
  has "$WORK/out" "publish branch publish/mb1012-3 is contained in origin/main" "contained publish branch is recognized"
  has "$WORK/out" "switched publish/mb1012-3 to main" "contained publish branch switches to main"
  has "$WORK/out" "fast-forwarded" "contained publish branch fast-forwards main"
  [ "$(git -C "$REPO" symbolic-ref --short HEAD)" = "main" ] && ok "contained publish branch left HEAD on main" || bad "contained publish branch did not leave HEAD on main"
  [ "$(head_of "$REPO")" = "$(git -C "$REPO" rev-parse origin/main)" ] && ok "contained publish branch HEAD matches origin/main" || bad "contained publish branch HEAD is not origin/main"
  [ "$(git -C "$REPO" rev-parse publish/mb1012-3)" = "$old" ] && ok "contained publish ref still points at its tip" || bad "contained publish ref moved"
  [ -f "$REPO/FROM_ORIGIN" ] && ok "contained publish branch took the origin file" || bad "contained publish branch missed the origin file"
fi

if ! init_repo pubkeep || ! advance_origin pubkeep; then
  bad "pubkeep fixture"
else
  ok "pubkeep fixture"
  git -C "$REPO" checkout -b publish/keep >/dev/null 2>&1 || { bad "pubkeep branch"; }
  printf '%s\n' 'only-local' >"$REPO/LOCAL_ONLY"
  git_cfg "$REPO"
  git -C "$REPO" add LOCAL_ONLY
  git -C "$REPO" commit -m "keep me" >/dev/null 2>&1 || { bad "pubkeep commit"; }
  kept=$(head_of "$REPO")
  run_sync
  assert_rc 0 "unique publish branch exits 0"
  has "$WORK/out" "preserving branch publish/keep" "unique publish commits are preserved"
  [ "$(git -C "$REPO" symbolic-ref --short HEAD)" = "main" ] && ok "unique publish branch left HEAD on main" || bad "unique publish branch did not leave HEAD on main"
  [ "$(head_of "$REPO")" = "$(git -C "$REPO" rev-parse origin/main)" ] && ok "unique publish branch fast-forwarded main" || bad "unique publish branch did not fast-forward main"
  [ "$(git -C "$REPO" rev-parse publish/keep)" = "$kept" ] && ok "unique publish ref still points at its commit" || bad "unique publish ref moved"
  git -C "$REPO" cat-file -e publish/keep:LOCAL_ONLY && ok "unique file still exists on the publish ref" || bad "unique file missing from the publish ref"
  [ ! -e "$REPO/LOCAL_ONLY" ] && ok "unique file is not in the main work tree" || bad "unique file leaked into the main work tree"
  [ -f "$REPO/FROM_ORIGIN" ] && ok "unique publish branch took the origin file on main" || bad "unique publish branch missed the origin file"
fi

if ! init_repo retmain; then
  bad "retmain fixture"
else
  ok "retmain fixture"
  git -C "$REPO" checkout -b publish/after >/dev/null 2>&1 || { bad "retmain branch"; }
  before=$(head_of "$REPO")
  : >"$WORK/out"
  : >"$WORK/err"
  env -i PATH="/usr/bin:/bin" GIT_TERMINAL_PROMPT=0 \
    bash -c '
      set -uo pipefail
      G=$1
      . "$2"
      genseo_return_publish_branch_to_main
      printf "sync_rc:%s\n" "$?"
    ' _ "$REPO" "$HELPER" >"$WORK/out" 2>"$WORK/err"
  RC=$?
  assert_rc 0 "return-to-main exits 0"
  has "$WORK/out" "sync_rc:0" "return-to-main returns 0"
  [ "$(git -C "$REPO" symbolic-ref --short HEAD)" = "main" ] && ok "return-to-main left HEAD on main" || bad "return-to-main did not leave HEAD on main"
  [ "$(head_of "$REPO")" = "$before" ] && ok "return-to-main did not fast-forward" || bad "return-to-main moved HEAD"
  [ "$(git -C "$REPO" rev-parse publish/after)" = "$before" ] && ok "return-to-main kept the publish ref" || bad "return-to-main moved the publish ref"
  lacks "$WORK/out" "fast-forwarded" "return-to-main did not log a fast-forward"
fi

if ! init_repo sidekeep || ! advance_origin sidekeep; then
  bad "sidekeep fixture"
else
  ok "sidekeep fixture"
  git -C "$REPO" checkout -b side >/dev/null 2>&1 || { bad "sidekeep branch"; }
  : >"$WORK/out"
  : >"$WORK/err"
  env -i PATH="/usr/bin:/bin" GIT_TERMINAL_PROMPT=0 \
    bash -c '
      set -uo pipefail
      G=$1
      . "$2"
      genseo_return_publish_branch_to_main
    ' _ "$REPO" "$HELPER" >"$WORK/out" 2>"$WORK/err"
  RC=$?
  assert_rc 0 "return-to-main ignores a non-publish branch"
  [ "$(git -C "$REPO" symbolic-ref --short HEAD)" = "side" ] && ok "non-publish branch stayed" || bad "non-publish branch was switched"
fi

echo "3c. an article branch returns to main and the open queue skips published tickets"
if ! init_repo artret; then
  bad "artret fixture"
else
  ok "artret fixture"
  cat >"$REPO/daily-tickets.md" <<'EOF'
- [ ] **#CA1016-2 — shilajit on an empty stomach** — `Shilajit on an Empty Stomach`
- [ ] **#CA1016-7 — vaginal probiotics over 60** — `Vaginal Probiotics Over 60`
EOF
  cat >"$REPO/daily-landing-tickets.md" <<'EOF'
- [ ] listicle | wellnessnest | product=premium-himalayan-shilajit-gummies · angle: gummies (added 2026-10-16)
- [ ] listicle | wellnessnest | product=florafresh-vaginal-probiotics-gummies · angle: flora (added 2026-10-16)
EOF
  git_cfg "$REPO"
  git -C "$REPO" add daily-tickets.md daily-landing-tickets.md
  git -C "$REPO" commit -m "queue" >/dev/null 2>&1 || { bad "artret queue commit"; }
  git -C "$REPO" push origin main >/dev/null 2>&1 || { bad "artret push"; }
  if ! advance_origin artret; then
    bad "artret origin"
  fi
  git -C "$REPO" checkout -b article/ca1016-2 >/dev/null 2>&1 || { bad "artret branch"; }
  python3 - "$REPO/daily-tickets.md" "$REPO/daily-landing-tickets.md" <<'PY'
import pathlib, sys
tickets, landing = sys.argv[1:]
path = pathlib.Path(tickets)
path.write_text(path.read_text().replace(
    "- [ ] **#CA1016-2",
    "- [DONE 2026-10-18 https://wellnessnest.co/blogs/news/shilajit-on-an-empty-stomach-yes-or-no-in-the-us] **#CA1016-2",
    1,
))
path = pathlib.Path(landing)
path.write_text(path.read_text().replace(
    "- [ ] listicle | wellnessnest | product=premium-himalayan-shilajit-gummies",
    "- [DRAFT 2026-10-18 page 166299173179] listicle | wellnessnest | product=premium-himalayan-shilajit-gummies",
    1,
))
PY
  git -C "$REPO" add daily-tickets.md daily-landing-tickets.md
  git -C "$REPO" commit -m "publish" >/dev/null 2>&1 || { bad "artret publish commit"; }
  kept=$(head_of "$REPO")
  printf '%s\n' 'scratch' >"$REPO/scratch.txt"
  SYNC_ENV="GENSEO_SYNC_DRY_RUN=1"
  run_sync
  unset SYNC_ENV
  assert_rc 0 "article dry-run exits 0"
  has "$WORK/out" "would record: 2 queue closure(s)" "article dry-run names both closures"
  has "$WORK/out" "would switch article/ca1016-2 to main" "article dry-run would switch"
  [ "$(git -C "$REPO" symbolic-ref --short HEAD)" = "article/ca1016-2" ] && ok "article dry-run stayed on the branch" || bad "article dry-run left the branch"
  [ ! -e "$REPO/state/queue-closures.json" ] && ok "article dry-run wrote no ledger" || bad "article dry-run wrote a ledger"
  run_sync
  assert_rc 0 "article branch exits 0"
  has "$WORK/out" "preserving branch article/ca1016-2" "article commits are preserved"
  has "$WORK/out" "recorded: 2 queue closure(s)" "article branch records both closures"
  has "$WORK/out" "switched article/ca1016-2 to main" "article branch switches to main"
  [ "$(git -C "$REPO" symbolic-ref --short HEAD)" = "main" ] && ok "article branch left HEAD on main" || bad "article branch did not leave HEAD on main"
  [ "$(head_of "$REPO")" = "$(git -C "$REPO" rev-parse origin/main)" ] && ok "article branch HEAD matches origin/main" || bad "article branch HEAD is not origin/main"
  [ "$(git -C "$REPO" rev-parse article/ca1016-2)" = "$kept" ] && ok "article ref still points at its commit" || bad "article ref moved"
  git -C "$REPO" cat-file -e "article/ca1016-2:daily-tickets.md" && ok "closed queue still exists on the article ref" || bad "closed queue missing from the article ref"
  grep -F -q -- '- [ ] **#CA1016-2' "$REPO/daily-tickets.md" && ok "main work tree has the open article line" || bad "main work tree lost the open article line"
  grep -F -q 'CA1016-2' "$REPO/state/queue-closures.json" && ok "ledger names CA1016-2" || bad "ledger missing CA1016-2"
  grep -F -q 'premium-himalayan-shilajit-gummies' "$REPO/state/queue-closures.json" && ok "ledger names the landing line" || bad "ledger missing the landing line"
  first=$(/usr/bin/python3 "$ROOT/scripts/genseo_queue_closures.py" first --queue "$REPO/daily-tickets.md")
  case "$first" in
    *'#CA1016-7'*) ok "effective article queue starts at CA1016-7" ;;
    *) bad "effective article queue is $first" ;;
  esac
  land=$(/usr/bin/python3 "$ROOT/scripts/genseo_queue_closures.py" first --queue "$REPO/daily-landing-tickets.md")
  case "$land" in
    *florafresh*) ok "effective landing queue skips the drafted gummies line" ;;
    *) bad "effective landing queue is $land" ;;
  esac
  [ "$(cat "$REPO/scratch.txt")" = "scratch" ] && ok "article return kept the untracked file" || bad "article return lost the untracked file"
  [ -f "$REPO/FROM_ORIGIN" ] && ok "article return took the origin file" || bad "article return missed the origin file"
fi

echo "3d. end of run returns an article branch without a fast-forward"
if ! init_repo artend; then
  bad "artend fixture"
else
  ok "artend fixture"
  printf '%s\n' '- [ ] **#CA1016-2 — shilajit on an empty stomach** — `Title`' >"$REPO/daily-tickets.md"
  git_cfg "$REPO"
  git -C "$REPO" add daily-tickets.md
  git -C "$REPO" commit -m "queue" >/dev/null 2>&1 || { bad "artend queue commit"; }
  git -C "$REPO" push origin main >/dev/null 2>&1 || { bad "artend push"; }
  git -C "$REPO" checkout -b article/ca1016-2 >/dev/null 2>&1 || { bad "artend branch"; }
  printf '%s\n' '- [DONE 2026-10-18 https://wellnessnest.co/blogs/news/shilajit-on-an-empty-stomach-yes-or-no-in-the-us] **#CA1016-2 — shilajit on an empty stomach** — `Title`' >"$REPO/daily-tickets.md"
  git -C "$REPO" add daily-tickets.md
  git -C "$REPO" commit -m "publish" >/dev/null 2>&1 || { bad "artend publish commit"; }
  before=$(head_of "$REPO")
  : >"$WORK/out"
  : >"$WORK/err"
  env -i PATH="/usr/bin:/bin" GIT_TERMINAL_PROMPT=0 \
    bash -c '
      set -uo pipefail
      G=$1
      . "$2"
      genseo_return_publish_branch_to_main
      printf "sync_rc:%s\n" "$?"
    ' _ "$REPO" "$HELPER" >"$WORK/out" 2>"$WORK/err"
  RC=$?
  assert_rc 0 "article return-to-main exits 0"
  has "$WORK/out" "sync_rc:0" "article return-to-main returns 0"
  has "$WORK/out" "recorded: 1 queue closure(s)" "article return records the closure"
  [ "$(git -C "$REPO" symbolic-ref --short HEAD)" = "main" ] && ok "article return left HEAD on main" || bad "article return did not leave HEAD on main"
  [ "$(git -C "$REPO" rev-parse article/ca1016-2)" = "$before" ] && ok "article return kept the ref" || bad "article return moved the ref"
  grep -F -q -- '- [ ] **#CA1016-2' "$REPO/daily-tickets.md" && ok "article return restored the open line on main" || bad "article return left the DONE line on main"
  grep -F -q 'CA1016-2' "$REPO/state/queue-closures.json" && ok "article return ledger names CA1016-2" || bad "article return ledger missing CA1016-2"
  lacks "$WORK/out" "fast-forwarded" "article return did not fast-forward"
fi

if ! init_repo dryff || ! advance_origin dryff; then
  bad "dryff fixture"
else
  ok "dryff fixture"
  printf '%s\n' 'scratch' >"$REPO/scratch.txt"
  before=$(head_of "$REPO")
  SYNC_ENV="GENSEO_SYNC_DRY_RUN=1"
  run_sync
  unset SYNC_ENV
  assert_rc 0 "dry-run exits 0"
  has "$WORK/out" "untracked files kept" "dry-run keeps untracked files"
  has "$WORK/out" "origin/main: would ff " "dry-run reports would ff"
  lacks "$WORK/out" "fast-forwarded" "dry-run does not fast-forward"
  [ "$(head_of "$REPO")" = "$before" ] && ok "dry-run left HEAD" || bad "dry-run moved HEAD"
  [ ! -e "$REPO/FROM_ORIGIN" ] && ok "dry-run did not take the origin file" || bad "dry-run took the origin file"
  [ "$(cat "$REPO/scratch.txt")" = "scratch" ] && ok "dry-run kept the untracked file" || bad "dry-run lost the untracked file"
fi

if ! init_repo dryutd; then
  bad "dryutd fixture"
else
  ok "dryutd fixture"
  printf '%s\n' 'scratch' >"$REPO/scratch.txt"
  before=$(head_of "$REPO")
  SYNC_ENV="GENSEO_SYNC_DRY_RUN=1"
  run_sync
  unset SYNC_ENV
  assert_rc 0 "dry-run up to date exits 0"
  has "$WORK/out" "untracked files kept" "dry-run up to date keeps untracked files"
  has "$WORK/out" "origin/main: already up to date" "dry-run reports up to date"
  lacks "$WORK/out" "would ff" "dry-run up to date does not say would ff"
  [ "$(head_of "$REPO")" = "$before" ] && ok "dry-run up to date left HEAD" || bad "dry-run up to date moved HEAD"
fi

if ! init_repo locked || ! advance_origin locked; then
  bad "locked fixture"
else
  ok "locked fixture"
  mkdir -p "$REPO/state/daily.lock"
  sleep 120 &
  HOLD_PIDS="$HOLD_PIDS $!"
  printf '%s\n' "$!" >"$REPO/state/daily.lock/pid"
  before=$(head_of "$REPO")
  run_sync
  assert_rc 0 "lock block exits 0"
  has "$WORK/out" "another GenSeo job holds the lock" "lock block warns"
  [ "$(head_of "$REPO")" = "$before" ] && ok "lock block left HEAD" || bad "lock block moved HEAD"
  [ ! -e "$REPO/FROM_ORIGIN" ] && ok "lock block did not take the origin file" || bad "lock block took the origin file"
  kill "$!" 2>/dev/null || true
fi

if ! init_repo openjob || ! advance_origin openjob; then
  bad "openjob fixture"
else
  ok "openjob fixture"
  mkdir -p "$REPO/scripts"
  cat >"$REPO/scripts/run_ticket_headless.sh" <<'EOF'
#!/bin/bash
sleep 120
EOF
  chmod 755 "$REPO/scripts/run_ticket_headless.sh"
  "$REPO/scripts/run_ticket_headless.sh" >/dev/null 2>&1 &
  HOLD_PIDS="$HOLD_PIDS $!"
  open_pid=$!
  before=$(head_of "$REPO")
  run_sync
  assert_rc 0 "open script exits 0"
  has "$WORK/out" "another GenSeo job has a script open" "open script warns"
  [ "$(head_of "$REPO")" = "$before" ] && ok "open script left HEAD" || bad "open script moved HEAD"
  [ ! -e "$REPO/FROM_ORIGIN" ] && ok "open script did not take the origin file" || bad "open script took the origin file"
  kill "$open_pid" 2>/dev/null || true
fi

echo "4. a failed fetch and a non-checkout continue; GIT_DIR cannot retarget the repo"
if ! init_repo fetchfail; then
  bad "fetch fixture"
else
  ok "fetch fixture"
  before=$(head_of "$REPO")
  git -C "$REPO" remote set-url origin "$WORK/no-such-remote"
  run_sync
  assert_rc 0 "fetch failure exits 0"
  has "$WORK/out" "fetch failed" "fetch failure warns"
  has "$WORK/out" "continuing on the current checkout" "fetch failure continues"
  [ "$(head_of "$REPO")" = "$before" ] && ok "fetch failure left HEAD" || bad "fetch failure moved HEAD"
  lacks "$WORK/out" "fast-forwarded" "fetch failure did not fast-forward"
fi

if ! init_repo notgit; then
  bad "notgit fixture"
else
  ok "notgit fixture"
  plain="$WORK/plain-notgit"
  rm -rf "$plain"
  mkdir -p "$plain"
  printf '%s\n' 'plain' >"$plain/README"
  REPO="$plain"
  run_sync
  assert_rc 0 "non-checkout exits 0"
  has "$WORK/out" "not a git work tree" "non-checkout warns"
  [ "$(cat "$plain/README")" = "plain" ] && ok "non-checkout file kept" || bad "non-checkout file changed"
fi

if ! init_repo gitdir || ! advance_origin gitdir; then
  bad "gitdir fixture"
else
  ok "gitdir fixture"
  DECOY="$WORK/decoy-gitdir"
  rm -rf "$DECOY"
  git init -b main "$DECOY" >/dev/null 2>&1 || { bad "decoy init"; }
  git_cfg "$DECOY"
  printf '%s\n' 'decoy' >"$DECOY/README"
  git -C "$DECOY" add README
  git -C "$DECOY" commit -m decoy >/dev/null 2>&1 || { bad "decoy commit"; }
  decoy_head=$(head_of "$DECOY")
  before=$(head_of "$REPO")
  : >"$WORK/out"
  : >"$WORK/err"
  env -i PATH="/usr/bin:/bin" GIT_TERMINAL_PROMPT=0 \
    GIT_DIR="$DECOY/.git" GIT_WORK_TREE="$DECOY" \
    bash -c '
      set -uo pipefail
      G=$1
      . "$2"
      genseo_sync_origin_main ""
      printf "sync_rc:%s\n" "$?"
    ' _ "$REPO" "$HELPER" >"$WORK/out" 2>"$WORK/err"
  RC=$?
  assert_rc 0 "GIT_DIR fast-forward exits 0"
  [ "$(head_of "$REPO")" = "$(git -C "$REPO" rev-parse origin/main)" ] && ok "GIT_DIR updated the checkout" || bad "GIT_DIR did not update the checkout"
  [ "$(head_of "$REPO")" != "$before" ] && ok "GIT_DIR checkout HEAD moved" || bad "GIT_DIR checkout HEAD stayed"
  [ "$(head_of "$DECOY")" = "$decoy_head" ] && ok "GIT_DIR decoy was not modified" || bad "GIT_DIR decoy changed"
fi

echo "5. rewriting the launch file while the copy runs does not abort the script"
home5="$WORK/home-stable"
rm -rf "$home5"
mkdir -p "$home5/genseo/scripts"
cp "$HELPER" "$home5/genseo/scripts/genseo_sync_main.sh"
cat >"$WORK/entry.sh" <<'EOF'
#!/bin/bash
set -uo pipefail
G="$HOME/genseo"
. "$G/scripts/genseo_sync_main.sh"
genseo_exec_stable_copy grokbot-genseo-daily "$@"
trap 'genseo_stable_copy_release now' EXIT
printf '%s\n' 'echo ontAsk' >"$GENSEO_LAUNCH_SOURCE"
echo STABLE_OK
echo "STABLE_SCRIPT:$GENSEO_STABLE_SCRIPT"
EOF
: >"$WORK/out"
: >"$WORK/err"
env -i HOME="$home5" PATH="/usr/bin:/bin" bash "$WORK/entry.sh" >"$WORK/out" 2>"$WORK/err"
RC=$?
assert_rc 0 "stable copy exits 0"
has "$WORK/out" "STABLE_OK" "stable copy finished after the launch file changed"
lacks "$WORK/out" "ontAsk" "stdout is not the rewritten launch file"
lacks "$WORK/err" "ontAsk" "stderr is not the rewritten launch file"
grep -F -q 'echo ontAsk' "$WORK/entry.sh" && ok "launch file was rewritten" || bad "launch file was not rewritten"
stable_path=$(sed -n 's/^STABLE_SCRIPT://p' "$WORK/out")
if [ -n "$stable_path" ] && [ ! -e "$stable_path" ]; then
  ok "stable copy removed on exit"
else
  bad "stable copy left behind ($stable_path)"
fi

echo "6. a fast-forward re-execs the repo script and adopts the lock"
if ! init_repo reexec; then
  bad "reexec fixture"
else
  ok "reexec fixture"
  mkdir -p "$REPO/scripts" "$REPO/deploy"
  cp "$HELPER" "$REPO/scripts/genseo_sync_main.sh"
  cat >"$REPO/deploy/grokbot-genseo-daily.sh" <<'EOF'
#!/bin/bash
set -uo pipefail
G="$HOME/genseo"
. "$G/scripts/genseo_sync_main.sh"
genseo_exec_stable_copy grokbot-genseo-daily "$@"
LOCK="$G/state/daily.lock"
mkdir -p "$LOCK"
printf '%s\n' "$$" >"$LOCK/pid"
export GENSEO_NET_WAIT_DONE=1
genseo_sync_origin_main "$G/deploy/grokbot-genseo-daily.sh" "$@"
echo OLD
EOF
  git_cfg "$REPO"
  git -C "$REPO" add scripts deploy
  git -C "$REPO" commit -m "v1 wrapper" >/dev/null 2>&1 || { bad "reexec v1 commit"; }
  git -C "$REPO" push origin main >/dev/null 2>&1 || { bad "reexec v1 push"; }
  other="$WORK/other-reexec"
  rm -rf "$other"
  git clone "$BARE" "$other" >/dev/null 2>&1 || { bad "reexec clone"; }
  git_cfg "$other"
  cat >"$other/deploy/grokbot-genseo-daily.sh" <<'EOF'
#!/bin/bash
set -uo pipefail
G="$HOME/genseo"
. "$G/scripts/genseo_sync_main.sh"
genseo_exec_stable_copy grokbot-genseo-daily "$@"
LOCK="$G/state/daily.lock"
if [ "${GENSEO_MAIN_SYNCED:-}" = 1 ] && genseo_daily_lock_is_ours; then
  echo NEW
  exit 0
fi
echo V2_DID_NOT_ADOPT
exit 1
EOF
  printf '%s\n' 'from-origin' >"$other/FROM_ORIGIN"
  git -C "$other" add deploy/grokbot-genseo-daily.sh FROM_ORIGIN
  git -C "$other" commit -m "v2 wrapper" >/dev/null 2>&1 || { bad "reexec v2 commit"; }
  git -C "$other" push origin main >/dev/null 2>&1 || { bad "reexec v2 push"; }
  bare_before=$(bare_main)
  home6="$(dirname "$REPO")"
  # The clone has to be named genseo under HOME. init_repo used repo-reexec.
  link_home="$WORK/home-reexec"
  rm -rf "$link_home"
  mkdir -p "$link_home"
  ln -s "$REPO" "$link_home/genseo"
  : >"$WORK/out"
  : >"$WORK/err"
  env -i HOME="$link_home" PATH="/usr/bin:/bin" GIT_TERMINAL_PROMPT=0 \
    bash "$REPO/deploy/grokbot-genseo-daily.sh" >"$WORK/out" 2>"$WORK/err"
  RC=$?
  assert_rc 0 "re-exec exits 0"
  has "$WORK/out" "NEW" "re-exec ran the updated script"
  lacks "$WORK/out" "OLD" "re-exec did not continue the old script"
  lacks "$WORK/out" "V2_DID_NOT_ADOPT" "re-exec adopted the lock"
  has "$WORK/out" "re-exec " "re-exec was logged"
  [ -f "$REPO/FROM_ORIGIN" ] && ok "re-exec fast-forward brought the origin file" || bad "re-exec missed the origin file"
  [ "$(bare_main)" = "$bare_before" ] && ok "re-exec did not push" || bad "re-exec pushed"
  [ "$(head_of "$REPO")" = "$(git -C "$REPO" rev-parse origin/main)" ] && ok "re-exec HEAD matches origin/main" || bad "re-exec HEAD drifted"
fi

echo "7. a stale launcher re-execs the repo script when main is already current"
if ! init_repo stale; then
  bad "stale fixture"
else
  ok "stale fixture"
  mkdir -p "$REPO/scripts" "$REPO/deploy" "$WORK/bin"
  cp "$HELPER" "$REPO/scripts/genseo_sync_main.sh"
  cat >"$REPO/deploy/grokbot-genseo-daily.sh" <<'EOF'
#!/bin/bash
set -uo pipefail
G="$HOME/genseo"
. "$G/scripts/genseo_sync_main.sh"
genseo_exec_stable_copy grokbot-genseo-daily "$@"
LOCK="$G/state/daily.lock"
if [ "${GENSEO_MAIN_SYNCED:-}" = 1 ] && genseo_daily_lock_is_ours; then
  echo CANONICAL
  exit 0
fi
echo CANONICAL_MISSED
exit 1
EOF
  git_cfg "$REPO"
  git -C "$REPO" add scripts deploy
  git -C "$REPO" commit -m "canonical" >/dev/null 2>&1 || { bad "stale commit"; }
  git -C "$REPO" push origin main >/dev/null 2>&1 || { bad "stale push"; }
  cat >"$WORK/bin/grokbot-genseo-daily.sh" <<'EOF'
#!/bin/bash
set -uo pipefail
G="$HOME/genseo"
. "$G/scripts/genseo_sync_main.sh"
genseo_exec_stable_copy grokbot-genseo-daily "$@"
LOCK="$G/state/daily.lock"
mkdir -p "$LOCK"
printf '%s\n' "$$" >"$LOCK/pid"
export GENSEO_NET_WAIT_DONE=1
genseo_sync_origin_main "$G/deploy/grokbot-genseo-daily.sh" "$@"
echo LAUNCHER
EOF
  link_home="$WORK/home-stale"
  rm -rf "$link_home"
  mkdir -p "$link_home"
  ln -s "$REPO" "$link_home/genseo"
  before=$(head_of "$REPO")
  : >"$WORK/out"
  : >"$WORK/err"
  env -i HOME="$link_home" PATH="/usr/bin:/bin" GIT_TERMINAL_PROMPT=0 \
    bash "$WORK/bin/grokbot-genseo-daily.sh" >"$WORK/out" 2>"$WORK/err"
  RC=$?
  assert_rc 0 "stale launcher exits 0"
  has "$WORK/out" "CANONICAL" "stale launcher re-execs the repo script"
  lacks "$WORK/out" "LAUNCHER" "stale launcher does not keep running its own body"
  has "$WORK/out" "already up to date" "stale launcher was already on origin/main"
  [ "$(head_of "$REPO")" = "$before" ] && ok "stale launcher did not move HEAD" || bad "stale launcher moved HEAD"
fi

echo "8. reading a script inside the checkout does not fast-forward that file"
if ! init_repo inside || ! advance_origin inside; then
  bad "inside fixture"
else
  ok "inside fixture"
  mkdir -p "$REPO/scripts"
  cp "$HELPER" "$REPO/scripts/genseo_sync_main.sh"
  cat >"$REPO/inside.sh" <<'EOF'
#!/bin/bash
set -uo pipefail
G=$(cd "$(dirname "$0")" && pwd)
. "$G/scripts/genseo_sync_main.sh"
genseo_sync_origin_main ""
echo INSIDE_DONE
EOF
  git_cfg "$REPO"
  git -C "$REPO" add scripts/genseo_sync_main.sh inside.sh
  git -C "$REPO" commit -m "inside script" >/dev/null 2>&1 || { bad "inside commit"; }
  before=$(head_of "$REPO")
  : >"$WORK/out"
  : >"$WORK/err"
  env -i PATH="/usr/bin:/bin" GIT_TERMINAL_PROMPT=0 \
    bash "$REPO/inside.sh" >"$WORK/out" 2>"$WORK/err"
  RC=$?
  assert_rc 0 "inside-checkout exits 0"
  has "$WORK/out" "reading a script inside the checkout" "inside-checkout refuses"
  has "$WORK/out" "INSIDE_DONE" "inside-checkout still finishes"
  [ "$(head_of "$REPO")" = "$before" ] && ok "inside-checkout HEAD unchanged" || bad "inside-checkout HEAD moved"
  [ ! -e "$REPO/FROM_ORIGIN" ] && ok "inside-checkout did not take the origin file" || bad "inside-checkout took the origin file"
fi

echo "9. the article wrapper warns and still finishes when the helper is absent"
sandbox="$WORK/home-wrap/genseo"
mkdir -p "$sandbox/scripts" "$sandbox/state" "$sandbox/logs/daily" "$WORK/fakebin"
cp "$ROOT/scripts/genseo_daily_lock.sh" "$sandbox/scripts/genseo_daily_lock.sh"
cp "$ROOT/scripts/genseo_group_timeout.sh" "$sandbox/scripts/genseo_group_timeout.sh"
cp "$ROOT/scripts/genseo_wait_for_network.sh" "$sandbox/scripts/genseo_wait_for_network.sh"
cat >"$sandbox/scripts/genseo_published_today.py" <<'PY'
import sys
if "--json" in sys.argv:
    print('{"entries":[]}')
    raise SystemExit(0)
print("5")
PY
cat >"$WORK/fakebin/git" <<'EOF'
#!/bin/bash
printf '%s\n' "$*" >>"${GIT_CALLS:?}"
exit 99
EOF
chmod 755 "$WORK/fakebin/git"
: >"$WORK/git-calls"
: >"$WORK/out"
: >"$WORK/err"
env -i HOME="$WORK/home-wrap" PATH="$WORK/fakebin:/usr/bin:/bin" \
  GIT_CALLS="$WORK/git-calls" \
  GENSEO_DAILY_TARGET=5 \
  GENSEO_MAX_RUNS=1 \
  GENSEO_NO_DELAY=1 \
  GENSEO_NET_WAIT_MAX_SEC=0 \
  GENSEO_LIVE_FEED_RETRIES=0 \
  bash "$ARTICLE" >"$WORK/out" 2>"$WORK/err"
RC=$?
assert_rc 0 "article wrapper without the helper exits 0"
has "$WORK/out" "missing scripts/genseo_sync_main.sh" "article wrapper warns that the helper is missing"
has "$WORK/out" "DONE:" "article wrapper still reaches the done path"
[ ! -s "$WORK/git-calls" ] && ok "article wrapper did not run git" || bad "article wrapper ran git"
[ ! -e "$sandbox/state/daily.lock" ] && ok "article lock released" || bad "article lock still held"

echo "10. the workspace checkout was not fetched or edited by this test"
END_STATUS="$(git -C "$ROOT" status --porcelain)"
END_HEAD="$(git -C "$ROOT" rev-parse HEAD)"
[ "$END_HEAD" = "$START_HEAD" ] && ok "workspace HEAD unchanged" || bad "workspace HEAD changed"
[ "$END_STATUS" = "$START_STATUS" ] && ok "workspace status unchanged" || bad "workspace status changed"

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" = 0 ]

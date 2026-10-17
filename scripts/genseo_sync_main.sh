#!/bin/bash
# Fast-forward ~/genseo to origin/main before a scheduled article or landing run.
#
# Sourced by deploy/grokbot-genseo-daily.sh and scripts/run_landing_daily.sh
# after the network wait and after the lane lock is held. Bash 3.2 safe.
# Do not enable set -e here. Does not publish, push, rebase, or reset.
#
# git fetch origin main, then git merge --ff-only origin/main, when HEAD
# is main (or a publish/* branch that can be switched back to main) and
# every commit on local main is already on origin/main. Ignored logs and
# state do not count. Untracked files that the incoming tree does not
# overwrite are left in place. A tracked edit that would be overwritten is
# stashed, or copied under /tmp/genseo-preserve-<stamp>-<pid>/, and that
# path is logged. A publish/* ref is never deleted: if its commits are not
# on origin/main the ref keeps them and HEAD still returns to main when
# that switch is safe. Any other branch, a detached HEAD, or local commits
# on main that are not on origin are logged and left as they are.
#
# The fast-forward does not run while another GenSeo job holds
# state/daily.lock or state/landing-daily.lock, while another job is
# executing a checkout script, or while this process is still reading a
# script inside the checkout. GENSEO_SYNC_DRY_RUN=1 fetches and logs
# "already up to date" or "would ff" and does not switch, stash, or merge.
#
# Bash reads a script as it runs. A fast-forward that rewrites that file
# mid-run has produced a garbled token (the 2026-10 ontAsk failure). The
# wrapper calls genseo_exec_stable_copy first: that copies the running file
# outside the repo and execs the copy. The fetch then runs while bash is
# reading the copy. A fast-forward, or a ~/bin launcher that differs from
# the repo script, re-execs the repo script so the rest of the run reads
# the updated file from the start. The lock directory stays held: exec
# keeps the same PID, and the repo script adopts the lock instead of
# exiting as a second run.
#
# GENSEO_STABLE_COPY=1     this process is already the copy, or the re-exec
# GENSEO_STABLE_SCRIPT     absolute path of the copy
# GENSEO_LAUNCH_SOURCE     path launchd started
# GENSEO_SYNC_UNSAFE=1     the copy failed; do not fetch
# GENSEO_MAIN_SYNCED=1     fetch already decided for this run
# GENSEO_LOCK_HELD=1       re-exec still owns the lane lock (same PID)
# GENSEO_NET_WAIT_DONE=1   the network wait already succeeded

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  printf '%s\n' "source scripts/genseo_sync_main.sh from a daily wrapper; it does not fetch or publish." >&2
  exit 2
fi

genseo_sync_note() {
  if declare -F say >/dev/null 2>&1; then
    say "$*"
  else
    printf '%s\n' "$*"
  fi
}

# Drop the copy once bash is no longer reading it. The path has to be the
# temp file this helper created, outside the checkout. Pass "now" from an
# EXIT trap: that is the one time $0 itself may be removed. Unlinking the
# running file earlier makes bash reopen the path (the ontAsk failure).
genseo_stable_copy_release() {
  local p=${GENSEO_STABLE_SCRIPT:-} root="" repo=""
  [ -n "$p" ] || return 0
  if [ "$p" = "$0" ] && [ "${1:-}" != "now" ]; then
    return 0
  fi
  [ -f "$p" ] || return 0
  root=${TMPDIR:-/tmp}
  root=${root%/}
  repo=${G:-}
  repo=${repo%/}
  case "$p" in
    /tmp/grokbot-genseo-daily.*|/tmp/run_landing_daily.*|"$root"/grokbot-genseo-daily.*|"$root"/run_landing_daily.*)
      ;;
    *) return 0 ;;
  esac
  if [ -n "$repo" ]; then
    case "$p" in
      "$repo"|"$repo"/*) return 0 ;;
    esac
  fi
  rm -f "$p"
  return 0
}

# Copy $0 aside and replace this process with that copy. Returns only when
# this process is already the copy, or the copy could not be made.
# prefix is grokbot-genseo-daily or run_landing_daily so the daily lock
# scanner still sees the article wrapper in the process list.
genseo_exec_stable_copy() {
  local prefix=$1 src="" dest="" root="" repo=""
  shift
  if [ "${GENSEO_STABLE_COPY:-}" = 1 ]; then
    if [ -n "${GENSEO_STABLE_SCRIPT:-}" ] && [ "$GENSEO_STABLE_SCRIPT" != "$0" ]; then
      genseo_stable_copy_release
    fi
    return 0
  fi
  case "$prefix" in
    grokbot-genseo-daily|run_landing_daily) ;;
    *)
      export GENSEO_SYNC_UNSAFE=1
      return 0
      ;;
  esac
  src=$0
  if [ ! -f "$src" ]; then
    export GENSEO_SYNC_UNSAFE=1
    return 0
  fi
  # Keep the copy outside the checkout. An untracked file inside it would
  # make git status dirty and the fast-forward would refuse itself.
  root=${TMPDIR:-/tmp}
  repo=${G:-}
  repo=${repo%/}
  if [ -n "$repo" ]; then
    case "$root" in
      "$repo"|"$repo"/*) root=/tmp ;;
    esac
  fi
  dest=$(mktemp "${root%/}/${prefix}.XXXXXX") || {
    export GENSEO_SYNC_UNSAFE=1
    return 0
  }
  # BSD cp on macOS does not treat -- as end of options.
  if ! cp "$src" "$dest"; then
    rm -f "$dest"
    export GENSEO_SYNC_UNSAFE=1
    return 0
  fi
  chmod 700 "$dest" || true
  export GENSEO_STABLE_COPY=1
  export GENSEO_STABLE_SCRIPT=$dest
  export GENSEO_LAUNCH_SOURCE=$src
  exec /bin/bash "$dest" "$@"
  export GENSEO_SYNC_UNSAFE=1
  return 0
}

# git for the checkout in $GENSEO_SYNC_REPO. Env vars that point git at a
# different repository are cleared for this command only.
genseo_sync_git() {
  env \
    -u GIT_DIR \
    -u GIT_WORK_TREE \
    -u GIT_INDEX_FILE \
    -u GIT_OBJECT_DIRECTORY \
    -u GIT_COMMON_DIR \
    -u GIT_NAMESPACE \
    GIT_TERMINAL_PROMPT=0 \
    GIT_ASKPASS=/usr/bin/true \
    SSH_ASKPASS=/usr/bin/true \
    GIT_SSH_COMMAND="ssh -o BatchMode=yes" \
    git -C "$GENSEO_SYNC_REPO" -c gc.auto=0 -c core.hooksPath=/dev/null "$@"
}

# 0 when this process still owns state/daily.lock. The PID file is written
# before the fast-forward. exec keeps $$, so the re-exec'd wrapper adopts it.
genseo_daily_lock_is_ours() {
  local pid=""
  [ "${GENSEO_LOCK_HELD:-}" = 1 ] || return 1
  [ -n "${LOCK:-}" ] || return 1
  [ -d "$LOCK" ] || return 1
  [ -f "$LOCK/pid" ] || return 1
  IFS= read -r pid < "$LOCK/pid" || return 1
  [ "$pid" = "$$" ]
}

# 0 when this process still owns state/landing-daily.lock. The owner file
# sits beside the lock directory so rmdir of the empty directory still works.
genseo_landing_lock_is_ours() {
  local pid=""
  [ "${GENSEO_LOCK_HELD:-}" = 1 ] || return 1
  [ -n "${LOCK:-}" ] || return 1
  [ -d "$LOCK" ] || return 1
  [ -f "${LOCK}.owner" ] || return 1
  IFS= read -r pid < "${LOCK}.owner" || return 1
  [ "$pid" = "$$" ]
}

# Drop a trailing CR from a lock file written on a different machine.
genseo_sync_trim() {
  local s=$1
  s=${s//$'\r'/}
  printf '%s' "$s"
}

genseo_sync_pid_alive() {
  local pid=$1 state=""
  case "$pid" in
    ''|*[!0-9]*|0) return 1 ;;
  esac
  kill -0 "$pid" 2>/dev/null || return 1
  if [ -r "/proc/$pid/stat" ]; then
    state=$(cat "/proc/$pid/stat" 2>/dev/null || true)
    state=${state##*) }
    state=${state%% *}
  else
    state=$(ps -p "$pid" -o state= 2>/dev/null | awk '{print substr($1,1,1)}' || true)
  fi
  case "$state" in
    Z|z) return 1 ;;
  esac
  return 0
}

# 0 when pid is this shell or a process it forked.
genseo_sync_pid_is_us() {
  local pid=$1 ppid="" guard=0
  case "$pid" in
    ''|*[!0-9]*|0) return 1 ;;
  esac
  while [ "$guard" -lt 40 ]; do
    [ "$pid" = "$$" ] && return 0
    if [ -r "/proc/$pid/status" ]; then
      ppid=$(awk '/^PPid:/ {print $2}' "/proc/$pid/status" 2>/dev/null || true)
    else
      ppid=$(ps -p "$pid" -o ppid= 2>/dev/null | tr -d '[:space:]' || true)
    fi
    case "$ppid" in
      ''|*[!0-9]*|0|1) return 1 ;;
    esac
    [ "$ppid" = "$pid" ] && return 1
    pid=$ppid
    guard=$((guard + 1))
  done
  return 1
}

# 0 when a lane lock is held by a live PID that is not this run.
genseo_sync_lock_held_by_other() {
  local repo=$1 file="" pid=""
  for file in "$repo/state/daily.lock/pid" "$repo/state/landing-daily.lock.owner"; do
    [ -f "$file" ] || continue
    if ! IFS= read -r pid <"$file"; then
      return 0
    fi
    pid=$(genseo_sync_trim "$pid")
    genseo_sync_pid_alive "$pid" || continue
    genseo_sync_pid_is_us "$pid" && continue
    return 0
  done
  return 1
}

# A GenSeo job, not vim/cp/grep that merely names the file.
genseo_sync_cmd_is_job() {
  local cmd=$1 first="" rest="" token=""
  cmd="${cmd#"${cmd%%[![:space:]]*}"}"
  [ -n "$cmd" ] || return 1
  case "$cmd" in
    *grokbot-genseo-daily*|*run_landing_daily*|*run_ticket_headless*|*run_landing_headless*) ;;
    *) return 1 ;;
  esac
  first=${cmd%% *}
  rest=${cmd#"$first"}
  rest=${rest#" "}
  token=${first##*/}
  case "$token" in
    grokbot-genseo-daily|grokbot-genseo-daily.sh|run_landing_daily|run_landing_daily.sh|run_ticket_headless.sh|run_landing_headless.sh) return 0 ;;
    bash|sh)
      case "$rest" in
        *grokbot-genseo-daily*|*run_landing_daily*|*run_ticket_headless*|*run_landing_headless*) return 0 ;;
      esac
      ;;
  esac
  return 1
}

# 0 when another live GenSeo job is executing. ps failure fails closed.
genseo_sync_other_job_script() {
  local tmp="" pid="" cmd="" saw=1
  tmp=$(mktemp "${TMPDIR:-/tmp}/genseo-sync-ps.XXXXXX") || return 0
  if ps -axww -o pid=,args= >"$tmp" 2>/dev/null; then
    saw=0
  elif ps -eo pid=,args= >"$tmp" 2>/dev/null; then
    saw=0
  fi
  if [ "$saw" != 0 ]; then
    rm -f "$tmp"
    return 0
  fi
  while read -r pid cmd; do
    case "$pid" in
      ''|*[!0-9]*) continue ;;
    esac
    genseo_sync_cmd_is_job "$cmd" || continue
    genseo_sync_pid_is_us "$pid" && continue
    genseo_sync_pid_alive "$pid" || continue
    rm -f "$tmp"
    return 0
  done <"$tmp"
  rm -f "$tmp"
  return 1
}

# Physical path of a file or directory. Collapses repeated slashes and
# symlinks (/var -> /private/var). macOS TMPDIR ends in a slash, so $0 can
# be /var/folders/.../T//repo/script.sh while pwd prints one slash.
genseo_sync_physical_path() {
  local p=$1 dir="" base=""
  [ -n "$p" ] || return 1
  while :; do
    case "$p" in
      *//*) p=${p//\/\//\/} ;;
      *) break ;;
    esac
  done
  if [ -d "$p" ]; then
    dir=$(cd "$p" && pwd -P) || return 1
    printf '%s\n' "$dir"
    return 0
  fi
  dir=$(cd "$(dirname "$p")" 2>/dev/null && pwd -P) || return 1
  base=$(basename "$p")
  printf '%s/%s\n' "$dir" "$base"
}

# 0 when this process is parsing a script that lives in the checkout.
genseo_sync_reading_checkout_script() {
  local repo=$1 running=$0 repo_phys="" run_phys=""
  case "$running" in
    /*) ;;
    */*) running=$(pwd)/$running ;;
    *) return 1 ;;
  esac
  repo_phys=$(genseo_sync_physical_path "$repo") || return 1
  run_phys=$(genseo_sync_physical_path "$running") || return 1
  case "$run_phys" in
    "$repo_phys"/*)
      [ "${GENSEO_STABLE_COPY:-}" = 1 ] && return 1
      return 0
      ;;
  esac
  return 1
}

genseo_sync_tracked_dirty() {
  local line=""
  line=$(genseo_sync_git status --porcelain --untracked-files=no 2>/dev/null) || return 2
  [ -n "$line" ]
}

genseo_sync_has_untracked() {
  local line=""
  line=$(genseo_sync_git status --porcelain --untracked-files=normal 2>/dev/null) || return 2
  case "$line" in
    *'?? '*) return 0 ;;
  esac
  return 1
}

# Print the first untracked path that tree-ish already tracks. Empty if none.
# Directories that status collapses to one line are checked as a prefix.
genseo_sync_untracked_hit() {
  local tree=$1 line="" path="" hit="" tmp=""
  tmp=$(mktemp "${TMPDIR:-/tmp}/genseo-sync-tree.XXXXXX") || return 1
  while IFS= read -r line; do
    case "$line" in
      '?? '*) path=${line#?? } ;;
      *) continue ;;
    esac
    case "$path" in
      */)
        if genseo_sync_git ls-tree -r --name-only "$tree" -- "${path%/}" >"$tmp" 2>/dev/null; then
          if [ -s "$tmp" ]; then
            rm -f "$tmp"
            printf '%s\n' "$path"
            return 0
          fi
        fi
        ;;
      *)
        if genseo_sync_git cat-file -e "$tree:$path" 2>/dev/null; then
          rm -f "$tmp"
          printf '%s\n' "$path"
          return 0
        fi
        ;;
    esac
  done <<EOF
$(genseo_sync_git status --porcelain --untracked-files=normal 2>/dev/null || true)
EOF
  rm -f "$tmp"
  return 1
}

# 0 when a tracked local edit touches a path that differs between the two trees.
genseo_sync_tracked_overlaps() {
  local a=$1 b=$2 tmp="" hit=""
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/genseo-sync-ov.XXXXXX") || return 1
  genseo_sync_git -c core.quotePath=false diff --name-only "$a" >"$tmp/dirty" 2>/dev/null || true
  genseo_sync_git -c core.quotePath=false diff --name-only --cached "$a" >>"$tmp/dirty" 2>/dev/null || true
  if [ ! -s "$tmp/dirty" ]; then
    rm -rf "$tmp"
    return 1
  fi
  sort -u -o "$tmp/dirty" "$tmp/dirty"
  if ! genseo_sync_git -c core.quotePath=false diff --name-only "$a" "$b" >"$tmp/diff" 2>/dev/null; then
    rm -rf "$tmp"
    return 1
  fi
  sort -u -o "$tmp/diff" "$tmp/diff"
  hit=$(comm -12 "$tmp/dirty" "$tmp/diff" | head -n 1 || true)
  rm -rf "$tmp"
  [ -n "$hit" ]
}

# Park tracked edits. Leaves untracked files alone. Logs the stash or backup.
genseo_sync_preserve_tracked() {
  local branch="" stamp="" msg="" dest="" repo="" path="" listed=""
  if [ -n "${GENSEO_SYNC_PRESERVE:-}" ]; then
    return 0
  fi
  branch=$(genseo_sync_git symbolic-ref --quiet --short HEAD 2>/dev/null || printf '%s' detached)
  stamp=$(date +%Y%m%d-%H%M%S)
  msg="genseo-sync $stamp $branch"
  listed=$(genseo_sync_git -c commit.gpgsign=false stash push -m "$msg" 2>&1 || true)
  listed=$(genseo_sync_git stash list 2>/dev/null || true)
  listed=${listed%%$'\n'*}
  case "$listed" in
    *"$msg"*)
      genseo_sync_note "preserved tracked edits in stash: $msg"
      GENSEO_SYNC_PRESERVE=stash
      return 0
      ;;
  esac
  dest=${TMPDIR:-/tmp}
  dest=${dest%/}/genseo-preserve-$stamp-$$
  mkdir -p "$dest/files" || return 1
  repo=$GENSEO_SYNC_REPO
  if ! genseo_sync_git diff HEAD >"$dest/tracked.diff"; then
    return 1
  fi
  genseo_sync_git status --porcelain --untracked-files=no >"$dest/status.txt" 2>/dev/null || true
  genseo_sync_git -c core.quotePath=false diff --name-only HEAD >"$dest/names.txt" 2>/dev/null || true
  genseo_sync_git -c core.quotePath=false diff --name-only --cached >>"$dest/names.txt" 2>/dev/null || true
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    if [ -f "$repo/$path" ]; then
      mkdir -p "$dest/files/$(dirname "$path")"
      cp "$repo/$path" "$dest/files/$path" || true
    fi
  done <"$dest/names.txt"
  if ! genseo_sync_git restore --source=HEAD --worktree --staged . >/dev/null 2>&1; then
    genseo_sync_note "WARN: tracked edits left in the work tree — backup at $dest"
    return 1
  fi
  genseo_sync_note "preserved tracked edits in $dest/tracked.diff"
  GENSEO_SYNC_PRESERVE=$dest
  return 0
}

genseo_sync_undo_preserve() {
  local how=${GENSEO_SYNC_PRESERVE:-}
  GENSEO_SYNC_PRESERVE=""
  case "$how" in
    "") return 0 ;;
    stash)
      if ! genseo_sync_git stash pop >/dev/null 2>&1; then
        genseo_sync_note "WARN: could not restore stashed edits — they remain in the stash"
      fi
      ;;
    *)
      if [ -f "$how/tracked.diff" ] && [ -s "$how/tracked.diff" ]; then
        if ! genseo_sync_git apply "$how/tracked.diff" >/dev/null 2>&1; then
          genseo_sync_note "WARN: could not reapply $how/tracked.diff — the backup is still there"
        fi
      fi
      ;;
  esac
  return 0
}

genseo_sync_clear_preserve_flag() {
  GENSEO_SYNC_PRESERVE=""
}

# Switch publish/* to local main. Does not fast-forward and does not delete
# the publish ref. Returns 1 when the caller should stop without merging.
genseo_sync_publish_to_main() {
  local branch="" hit="" counts="" dry=0
  branch=$(genseo_sync_git symbolic-ref --quiet --short HEAD 2>/dev/null || true)
  case "$branch" in
    publish/*) ;;
    *) return 0 ;;
  esac
  [ "${GENSEO_SYNC_DRY_RUN:-}" = 1 ] && dry=1
  if genseo_sync_git merge-base --is-ancestor HEAD origin/main; then
    genseo_sync_note "publish branch $branch is contained in origin/main"
  else
    counts=$(genseo_sync_git rev-list --left-right --count origin/main...HEAD 2>/dev/null || true)
    genseo_sync_note "preserving branch $branch (commits not on origin/main: $counts)"
  fi
  if genseo_sync_git rev-parse --verify --quiet refs/heads/main >/dev/null; then
    hit=$(genseo_sync_untracked_hit refs/heads/main || true)
    if [ -n "$hit" ]; then
      genseo_sync_note "WARN: origin/main not updated — untracked file would be overwritten ($hit) — continuing on the current checkout"
      return 1
    fi
    if [ "$dry" = 1 ]; then
      genseo_sync_note "origin/main: would switch $branch to main"
      if genseo_sync_tracked_overlaps HEAD refs/heads/main; then
        genseo_sync_note "would preserve tracked edits"
      fi
      return 0
    fi
    if genseo_sync_tracked_overlaps HEAD refs/heads/main; then
      if ! genseo_sync_preserve_tracked; then
        genseo_sync_note "WARN: origin/main not updated — could not preserve tracked edits — continuing on the current checkout"
        return 1
      fi
    fi
    if ! genseo_sync_git switch main >/dev/null 2>&1; then
      if genseo_sync_tracked_dirty; then
        if ! genseo_sync_preserve_tracked; then
          genseo_sync_undo_preserve
          genseo_sync_note "WARN: origin/main not updated — could not switch $branch to main — continuing on the current checkout"
          return 1
        fi
        if ! genseo_sync_git switch main >/dev/null 2>&1; then
          genseo_sync_undo_preserve
          genseo_sync_note "WARN: origin/main not updated — could not switch $branch to main — continuing on the current checkout"
          return 1
        fi
      else
        genseo_sync_undo_preserve
        genseo_sync_note "WARN: origin/main not updated — could not switch $branch to main — continuing on the current checkout"
        return 1
      fi
    fi
    genseo_sync_note "origin/main: switched $branch to main"
    return 0
  fi
  hit=$(genseo_sync_untracked_hit origin/main || true)
  if [ -n "$hit" ]; then
    genseo_sync_note "WARN: origin/main not updated — untracked file would be overwritten ($hit) — continuing on the current checkout"
    return 1
  fi
  if [ "$dry" = 1 ]; then
    genseo_sync_note "origin/main: would switch $branch to main"
    return 0
  fi
  if genseo_sync_tracked_dirty; then
    if ! genseo_sync_preserve_tracked; then
      genseo_sync_note "WARN: origin/main not updated — could not preserve tracked edits — continuing on the current checkout"
      return 1
    fi
  fi
  if ! genseo_sync_git switch -c main --track origin/main >/dev/null 2>&1; then
    genseo_sync_undo_preserve
    genseo_sync_note "WARN: origin/main not updated — could not switch $branch to main — continuing on the current checkout"
    return 1
  fi
  genseo_sync_note "origin/main: switched $branch to main"
  return 0
}

# End of an article or landing run. publish/* returns to main. No fetch, no
# fast-forward, no delete of the publish ref.
genseo_return_publish_branch_to_main() {
  local repo="" branch="" gitdir=""
  GENSEO_SYNC_PRESERVE=""
  repo=${G:-}
  if [ -z "$repo" ]; then
    repo=${GENSEO_HOME:-}
  fi
  repo=${repo%/}
  if [ -z "$repo" ] || [ "$repo" = "/" ] || [ ! -d "$repo" ]; then
    return 0
  fi
  GENSEO_SYNC_REPO=$repo
  if ! genseo_sync_git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    unset GENSEO_SYNC_REPO
    return 0
  fi
  branch=$(genseo_sync_git symbolic-ref --quiet --short HEAD 2>/dev/null || true)
  case "$branch" in
    publish/*) ;;
    *)
      unset GENSEO_SYNC_REPO
      return 0
      ;;
  esac
  gitdir=$(genseo_sync_git rev-parse --git-dir 2>/dev/null || true)
  case "$gitdir" in
    "") ;;
    /*) ;;
    *) gitdir="$repo/$gitdir" ;;
  esac
  if [ -n "$gitdir" ] && { [ -e "$gitdir/MERGE_HEAD" ] || [ -d "$gitdir/rebase-merge" ] || [ -d "$gitdir/rebase-apply" ]; }; then
    genseo_sync_note "WARN: stayed on $branch — a merge or rebase is in progress"
    unset GENSEO_SYNC_REPO
    return 0
  fi
  if genseo_sync_reading_checkout_script "$repo"; then
    genseo_sync_note "WARN: stayed on $branch — this process is reading a script inside the checkout"
    unset GENSEO_SYNC_REPO
    return 0
  fi
  if genseo_sync_lock_held_by_other "$repo"; then
    genseo_sync_note "WARN: stayed on $branch — another GenSeo job holds the lock"
    unset GENSEO_SYNC_REPO
    return 0
  fi
  if genseo_sync_other_job_script "$repo"; then
    genseo_sync_note "WARN: stayed on $branch — another GenSeo job has a script open"
    unset GENSEO_SYNC_REPO
    return 0
  fi
  if ! genseo_sync_git rev-parse --verify --quiet origin/main >/dev/null 2>&1; then
    genseo_sync_note "WARN: stayed on $branch — origin/main is missing"
    unset GENSEO_SYNC_REPO
    return 0
  fi
  genseo_sync_publish_to_main || true
  genseo_sync_clear_preserve_flag
  unset GENSEO_SYNC_REPO
  return 0
}

# canonical is the repo script to exec when the checkout moves or that file
# differs from the one this process is reading. Extra args are passed through
# on that exec. Returns 0 when the caller should keep going. Does not return
# when it re-execs.
genseo_sync_origin_main() {
  local canonical=$1
  shift
  local repo="" branch="" head="" origin="" before="" after="" hit=""
  local counts="" running="" gitdir="" moved=0 need_reexec=0 dry=0
  GENSEO_SYNC_PRESERVE=""

  if [ "${GENSEO_SYNC_UNSAFE:-}" = 1 ]; then
    genseo_sync_note "WARN: origin/main not updated — this script could not be copied aside — continuing on the current checkout"
    return 0
  fi

  repo=${G:-}
  if [ -z "$repo" ]; then
    repo=${GENSEO_HOME:-}
  fi
  repo=${repo%/}
  if [ -z "$repo" ] || [ "$repo" = "/" ] || [ ! -d "$repo" ]; then
    genseo_sync_note "WARN: origin/main not updated — checkout path missing — continuing on the current checkout"
    return 0
  fi
  GENSEO_SYNC_REPO=$repo

  if ! genseo_sync_git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    unset GENSEO_SYNC_REPO
    genseo_sync_note "WARN: origin/main not updated — $repo is not a git work tree — continuing on the current checkout"
    return 0
  fi

  gitdir=$(genseo_sync_git rev-parse --git-dir 2>/dev/null || true)
  case "$gitdir" in
    "") ;;
    /*) ;;
    *) gitdir="$repo/$gitdir" ;;
  esac
  if [ -n "$gitdir" ] && { [ -e "$gitdir/MERGE_HEAD" ] || [ -d "$gitdir/rebase-merge" ] || [ -d "$gitdir/rebase-apply" ]; }; then
    unset GENSEO_SYNC_REPO
    genseo_sync_note "WARN: origin/main not updated — a merge or rebase is in progress — continuing on the current checkout"
    return 0
  fi

  genseo_sync_note "origin/main: git fetch origin main"
  if ! genseo_sync_git fetch origin main >/dev/null 2>&1; then
    unset GENSEO_SYNC_REPO
    genseo_sync_note "WARN: origin/main not updated — fetch failed — continuing on the current checkout"
    return 0
  fi
  if ! genseo_sync_git rev-parse --verify --quiet origin/main >/dev/null 2>&1; then
    unset GENSEO_SYNC_REPO
    genseo_sync_note "WARN: origin/main not updated — origin/main is missing after fetch — continuing on the current checkout"
    return 0
  fi

  # A fast-forward rewrites files under the checkout. Refuse that while bash
  # is still reading one of those files, while another job holds a lane lock,
  # or while another job is executing a checkout script.
  if genseo_sync_reading_checkout_script "$repo"; then
    unset GENSEO_SYNC_REPO
    genseo_sync_note "WARN: origin/main not updated — this process is reading a script inside the checkout — continuing on the current checkout"
    return 0
  fi
  if genseo_sync_lock_held_by_other "$repo"; then
    unset GENSEO_SYNC_REPO
    genseo_sync_note "WARN: origin/main not updated — another GenSeo job holds the lock — continuing on the current checkout"
    return 0
  fi
  if genseo_sync_other_job_script "$repo"; then
    unset GENSEO_SYNC_REPO
    genseo_sync_note "WARN: origin/main not updated — another GenSeo job has a script open — continuing on the current checkout"
    return 0
  fi

  before=$(genseo_sync_git rev-parse HEAD)
  branch=$(genseo_sync_git symbolic-ref --quiet --short HEAD 2>/dev/null || true)
  if [ -z "$branch" ]; then
    unset GENSEO_SYNC_REPO
    genseo_sync_note "WARN: origin/main not updated — HEAD is detached, not main — continuing on the current checkout"
    return 0
  fi
  if [ "$branch" != "main" ]; then
    case "$branch" in
      publish/*)
        if ! genseo_sync_publish_to_main; then
          genseo_sync_undo_preserve
          unset GENSEO_SYNC_REPO
          return 0
        fi
        ;;
      *)
        unset GENSEO_SYNC_REPO
        genseo_sync_note "WARN: origin/main not updated — HEAD is $branch, not main — continuing on the current checkout"
        return 0
        ;;
    esac
  fi

  [ "${GENSEO_SYNC_DRY_RUN:-}" = 1 ] && dry=1
  origin=$(genseo_sync_git rev-parse origin/main)
  head=$(genseo_sync_git rev-parse HEAD)
  # A dry-run on publish/* logs the switch and leaves HEAD there. Judge the
  # fast-forward against local main, which is where HEAD would land.
  if [ "$dry" = 1 ]; then
    branch=$(genseo_sync_git symbolic-ref --quiet --short HEAD 2>/dev/null || true)
    case "$branch" in
      publish/*)
        if genseo_sync_git rev-parse --verify --quiet refs/heads/main >/dev/null; then
          head=$(genseo_sync_git rev-parse refs/heads/main)
        fi
        ;;
    esac
  fi

  if genseo_sync_has_untracked; then
    if [ "$head" != "$origin" ] && genseo_sync_git merge-base --is-ancestor "$head" "$origin"; then
      hit=$(genseo_sync_untracked_hit "$origin" || true)
      if [ -n "$hit" ]; then
        genseo_sync_undo_preserve
        unset GENSEO_SYNC_REPO
        genseo_sync_note "WARN: origin/main not updated — untracked file would be overwritten ($hit) — continuing on the current checkout"
        return 0
      fi
    fi
    genseo_sync_note "untracked files kept"
  fi

  if [ "$head" = "$origin" ]; then
    genseo_sync_note "origin/main: already up to date"
    if genseo_sync_tracked_dirty; then
      genseo_sync_note "tracked local edits kept"
    fi
  elif genseo_sync_git merge-base --is-ancestor "$head" "$origin"; then
    if [ "$dry" != 1 ] && genseo_sync_tracked_overlaps HEAD origin/main; then
      if ! genseo_sync_preserve_tracked; then
        genseo_sync_undo_preserve
        unset GENSEO_SYNC_REPO
        genseo_sync_note "WARN: origin/main not updated — could not preserve tracked edits — continuing on the current checkout"
        return 0
      fi
    elif [ "$dry" = 1 ] && genseo_sync_tracked_overlaps HEAD origin/main; then
      genseo_sync_note "would preserve tracked edits"
    elif genseo_sync_tracked_dirty; then
      genseo_sync_note "tracked local edits kept"
    fi
    if [ "$dry" = 1 ]; then
      genseo_sync_clear_preserve_flag
      unset GENSEO_SYNC_REPO
      genseo_sync_note "origin/main: would ff $(genseo_sync_git rev-parse --short "$head") -> $(genseo_sync_git rev-parse --short "$origin")"
      return 0
    fi
    genseo_sync_note "origin/main: git merge --ff-only origin/main"
    if ! genseo_sync_git merge --ff-only origin/main >/dev/null 2>&1; then
      genseo_sync_undo_preserve
      unset GENSEO_SYNC_REPO
      genseo_sync_note "WARN: origin/main not updated — fast-forward failed — continuing on the current checkout"
      return 0
    fi
    genseo_sync_clear_preserve_flag
    after=$(genseo_sync_git rev-parse HEAD)
    if [ "$before" != "$after" ]; then
      moved=1
    fi
    genseo_sync_note "origin/main: fast-forwarded $(genseo_sync_git rev-parse --short "$before") -> $(genseo_sync_git rev-parse --short HEAD)"
  else
    counts=$(genseo_sync_git rev-list --left-right --count origin/main...HEAD 2>/dev/null || true)
    if genseo_sync_tracked_dirty; then
      genseo_sync_note "tracked local edits kept"
    fi
    genseo_sync_clear_preserve_flag
    unset GENSEO_SYNC_REPO
    genseo_sync_note "WARN: origin/main not updated — local commits are not on origin/main ($counts) — continuing on the current checkout"
    return 0
  fi
  genseo_sync_clear_preserve_flag

  after=$(genseo_sync_git rev-parse HEAD)
  if [ "$before" != "$after" ]; then
    moved=1
  fi

  # Re-exec once onto the repo script. If this process is already that
  # file, do not exec again: a second pass would see the stable copy differ
  # and loop. A fast-forward re-execs even when the script bytes matched, so
  # the new process sources the updated helpers. A stale ~/bin launcher
  # re-execs when the repo script differs and HEAD did not move.
  need_reexec=0
  if [ -n "$canonical" ] && [ -f "$canonical" ] && [ ! -L "$canonical" ] && [ "$0" != "$canonical" ]; then
    case "$canonical" in
      "$repo"/*)
        if [ "$moved" = 1 ]; then
          need_reexec=1
        else
          running=$0
          if [ -n "${GENSEO_STABLE_SCRIPT:-}" ] && [ -f "$GENSEO_STABLE_SCRIPT" ]; then
            running=$GENSEO_STABLE_SCRIPT
          fi
          if [ -f "$running" ] && ! cmp -s "$running" "$canonical"; then
            need_reexec=1
          fi
        fi
        ;;
    esac
  fi

  unset GENSEO_SYNC_REPO
  export GENSEO_MAIN_SYNCED=1
  if [ "$need_reexec" = 1 ]; then
    export GENSEO_LOCK_HELD=1
    export GENSEO_NET_WAIT_DONE=1
    export GENSEO_STABLE_COPY=1
    genseo_sync_note "re-exec $canonical"
    exec /bin/bash "$canonical" "$@"
    genseo_sync_note "WARN: re-exec failed — continuing on the current checkout"
  fi
  return 0
}

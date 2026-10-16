#!/bin/bash
# Fast-forward ~/genseo to origin/main before a scheduled article or landing run.
#
# Sourced by deploy/grokbot-genseo-daily.sh and scripts/run_landing_daily.sh
# after the network wait and after the lane lock is held. Bash 3.2 safe.
# Do not enable set -e here. Does not publish, push, rebase, or reset.
#
# git fetch origin main, then git merge --ff-only origin/main, only when
# HEAD is main, the work tree is clean (ignored logs and state do not count),
# and every local commit is already on origin/main. A dirty tree, another
# branch, or local commits that are not on origin are logged. The run
# continues on the current checkout.
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

# canonical is the repo script to exec when the checkout moves or that file
# differs from the one this process is reading. Extra args are passed through
# on that exec. Returns 0 when the caller should keep going. Does not return
# when it re-execs.
genseo_sync_origin_main() {
  local canonical=$1
  shift
  local repo="" branch="" porcelain="" first="" head="" origin="" before="" after=""
  local counts="" running="" gitdir="" moved=0 need_reexec=0 rc=0

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

  branch=$(genseo_sync_git symbolic-ref --quiet --short HEAD 2>/dev/null || true)
  if [ "$branch" != "main" ]; then
    unset GENSEO_SYNC_REPO
    genseo_sync_note "WARN: origin/main not updated — HEAD is ${branch:-detached}, not main — continuing on the current checkout"
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

  porcelain=$(genseo_sync_git status --porcelain --untracked-files=normal 2>/dev/null)
  rc=$?
  if [ "$rc" -ne 0 ]; then
    unset GENSEO_SYNC_REPO
    genseo_sync_note "WARN: origin/main not updated — could not read git status — continuing on the current checkout"
    return 0
  fi
  if [ -n "$porcelain" ]; then
    first=${porcelain%%$'\n'*}
    unset GENSEO_SYNC_REPO
    genseo_sync_note "WARN: origin/main not updated — checkout has uncommitted changes ($first) — continuing on the current checkout"
    return 0
  fi

  # A fast-forward rewrites files under the checkout. Refuse that while bash
  # is still reading one of those files. The stable copy lives outside it.
  # A $0 with no slash (bash -c) is not a checkout path.
  running=$0
  case "$running" in
    /*) ;;
    */*) running=$(pwd)/$running ;;
    *) running="" ;;
  esac
  if [ -n "$running" ]; then
    case "$running" in
      "$repo"/*)
        if [ "${GENSEO_STABLE_COPY:-}" != 1 ]; then
          unset GENSEO_SYNC_REPO
          genseo_sync_note "WARN: origin/main not updated — this process is reading a script inside the checkout — continuing on the current checkout"
          return 0
        fi
        ;;
    esac
  fi

  before=$(genseo_sync_git rev-parse HEAD)
  origin=$(genseo_sync_git rev-parse origin/main)
  if [ "$before" = "$origin" ]; then
    genseo_sync_note "origin/main: already up to date"
  elif genseo_sync_git merge-base --is-ancestor "$before" "$origin"; then
    genseo_sync_note "origin/main: git merge --ff-only origin/main"
    if ! genseo_sync_git merge --ff-only origin/main >/dev/null 2>&1; then
      unset GENSEO_SYNC_REPO
      genseo_sync_note "WARN: origin/main not updated — fast-forward failed — continuing on the current checkout"
      return 0
    fi
    after=$(genseo_sync_git rev-parse HEAD)
    if [ "$before" != "$after" ]; then
      moved=1
    fi
    genseo_sync_note "origin/main: fast-forwarded $(genseo_sync_git rev-parse --short "$before") -> $(genseo_sync_git rev-parse --short HEAD)"
  else
    counts=$(genseo_sync_git rev-list --left-right --count origin/main...HEAD 2>/dev/null || true)
    unset GENSEO_SYNC_REPO
    genseo_sync_note "WARN: origin/main not updated — local commits are not on origin/main ($counts) — continuing on the current checkout"
    return 0
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

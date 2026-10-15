#!/bin/bash
# MacBook return reconcile. Run this on the Mac after days offline.
# Bash 3.2 safe: no namerefs, no mapfile, no ${var,,}, no globstar.
# Dry-run is the default. It does not publish, call Shopify, push, reset, or start launchd.
#
# Offline: bash tests/test_mac_return_reconcile.sh
#
# checklist: 1. cd ~/genseo && bash scripts/mac_return_reconcile.sh
# checklist:    Default is dry-run. It prints ICT time, git status, main vs HEAD, local commits that are not on origin, and lock ages. It fetches origin. It does not merge, delete a lock, push, reset, or publish.
# checklist: 2. If local commits are not on origin, read them with git show and keep them. Do not run git push --force. Do not run git reset --hard. e1b8519 and 289803e were unpushed publish commits on this Mac. If either is still local, leave it.
# checklist: 3. If personas/index.json is dirty, leave it. DAILY-RUN.md keeps the MacBook image lane no-face until that file is re-synced from the Mini.
# checklist: 4. A lock is cleared only when you pass --apply-stale-lock, the lock is older than its documented threshold, and no live writer PID is running. The report prints the rmdir command on a dry-run and does not run it.
# checklist:    daily.lock threshold is 21600 seconds (6h), GENSEO_LOCK_STALE_SEC in scripts/genseo_daily_lock.sh. A live grokbot-genseo-daily or run_ticket_headless.sh blocks removal at any age.
# checklist:    landing-daily.lock threshold is 14400 seconds (4h), hardcoded in scripts/run_landing_daily.sh. A live run_landing_daily.sh or run_landing_headless.sh blocks removal at any age.
# checklist: 5. --apply fast-forwards main only: git merge --ff-only origin/main. It runs only when HEAD is main, the work tree is clean, fetch succeeded, and every local branch commit is already on origin. Otherwise it prints instructions and changes nothing.
# checklist: 6. After main moves, refresh the daily LaunchAgent wrapper. A pull does not update ~/bin. Run: bash scripts/install_mac_daily_wrapper.sh
# checklist:    Docs: DAILY-RUN.md and docs/TICKET_REFILL.md. The installer does not start launchd. launchd label com.pati.genseo-daily runs ~/bin/grokbot-genseo-daily.sh.
# checklist:    Repo plist: deploy/com.pati.genseo-daily.macbook.plist. Installed path named in DAILY-RUN.md: ~/Library/LaunchAgents/com.pati.genseo-daily.plist.
# checklist: 7. Landing code updates by the pull: launchd runs scripts/run_landing_daily.sh from this checkout (DAILY-RUN.md). MacBook plist, from the install comment in deploy/com.pati.genseo-landing.macbook.plist:
# checklist:    cp deploy/com.pati.genseo-landing.macbook.plist ~/Library/LaunchAgents/com.pati.genseo-landing.plist
# checklist:    launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-landing.plist
# checklist:    Copy or bootstrap that plist only when the agent is not already loaded. This script does not.
# checklist: 8. Start the Cursor private worker yourself: agent worker start --name MacBook-Pro
# checklist:    LaunchAgent label: com.pati.cursor-agent-worker. This repo does not contain that plist. This script does not start the worker.
# checklist: 9. Do not start grokbot-genseo-daily.sh or run_landing_daily.sh from this reconcile. The next 07:30 / 14:47 and 08:15 / 16:15 slots run them. Starting them here would publish or open a Shopify draft.
#
# Does not: genseo_daily_lock_acquire, shopify_publisher, landing_publisher, launchctl,
# agent worker start, git push, git reset, git checkout, git stash, git clean, rm -r.
# --apply is git merge --ff-only origin/main and nothing else.
# --apply-stale-lock removes pid and started inside a stale daily.lock, then rmdir.
# A landing lock is rmdir only, and only when the directory is empty.

set -uo pipefail

usage() {
  printf '%s\n' \
    "usage: bash scripts/mac_return_reconcile.sh [--dry-run] [--apply] [--apply-stale-lock]" \
    "GENSEO_HOME defaults to the checkout that contains this script (~/genseo on the Mac)." \
    "Default is dry-run: fetch and report. No merge, no lock delete, no push, no publish." \
    "--apply           git merge --ff-only origin/main when main is clean and fully pushed." \
    "--apply-stale-lock  rmdir a lock only past its documented age with no live writer." \
    "Exit 0 report or apply finished. Exit 2 usage. Exit 3 apply refused. Exit 4 lock not cleared."
}

APPLY=0
APPLY_LOCK=0
DRY_SET=0
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --apply-stale-lock) APPLY_LOCK=1 ;;
    --dry-run) DRY_SET=1 ;;
    -h|--help) usage; exit 0 ;;
    *)
      printf 'unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done
if [ "$APPLY" = 1 ] && [ "$DRY_SET" = 1 ]; then
  printf '%s\n' "--dry-run and --apply together are refused" >&2
  exit 2
fi
if [ "$APPLY_LOCK" = 1 ] && [ "$DRY_SET" = 1 ]; then
  printf '%s\n' "--dry-run and --apply-stale-lock together are refused" >&2
  exit 2
fi

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
DEFAULT_HOME=$(cd "$SCRIPT_DIR/.." && pwd)
GENSEO_HOME=${GENSEO_HOME:-$DEFAULT_HOME}

# Epoch mtime. Same order as genseo_path_mtime in scripts/genseo_daily_lock.sh:
# GNU stat -c, then BSD stat -f. GNU stat -f is filesystem info and must not be first.
# run_landing_daily.sh still calls BSD stat -f only; this helper does not.
reconcile_path_mtime() {
  local p=$1 m="" py=""
  m=$(stat -c %Y "$p" 2>/dev/null) || true
  case "$m" in
    ''|*[!0-9]*) m="" ;;
  esac
  if [ -z "$m" ]; then
    m=$(stat -f %m "$p" 2>/dev/null) || true
    case "$m" in
      ''|*[!0-9]*) m="" ;;
    esac
  fi
  if [ -z "$m" ]; then
    if [ -x /usr/bin/python3 ]; then
      py=/usr/bin/python3
    elif command -v python3 >/dev/null 2>&1; then
      py=$(command -v python3)
    else
      return 1
    fi
    m=$("$py" -c 'import os,sys; print(int(os.stat(sys.argv[1]).st_mtime))' "$p" 2>/dev/null) || true
    case "$m" in
      ''|*[!0-9]*) return 1 ;;
    esac
  fi
  printf '%s\n' "$m"
}

reconcile_lock_age() {
  local p=$1 m="" now=""
  m=$(reconcile_path_mtime "$p") || return 1
  now=$(date +%s)
  printf '%s\n' $((now - m))
}

reconcile_threshold() {
  local s=$1 d=$2
  case "$s" in
    ''|*[!0-9]*) printf '%s\n' "$d" ;;
    *) printf '%s\n' "$s" ;;
  esac
}

reconcile_pid_state() {
  local pid=$1 stat="" state=""
  if [ -r "/proc/$pid/stat" ]; then
    stat=$(cat "/proc/$pid/stat" 2>/dev/null || true)
    state=${stat##*) }
    state=${state%% *}
    printf '%s\n' "$state"
    return 0
  fi
  state=$(ps -p "$pid" -o state= 2>/dev/null | awk '{print substr($1,1,1)}' || true)
  [ -n "$state" ] || return 1
  printf '%s\n' "$state"
}

# kill -0 is true for a zombie. A zombie is not a running writer.
reconcile_pid_alive() {
  local pid=$1 state=""
  case "$pid" in
    ''|*[!0-9]*|0) return 1 ;;
  esac
  kill -0 "$pid" 2>/dev/null || return 1
  state=$(reconcile_pid_state "$pid" || true)
  case "$state" in
    Z|z) return 1 ;;
  esac
  return 0
}

reconcile_pid_command() {
  local pid=$1 cmd=""
  if [ -r "/proc/$pid/cmdline" ]; then
    cmd=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)
    printf '%s' "$cmd"
    return 0
  fi
  cmd=$(ps -ww -p "$pid" -o args= 2>/dev/null || ps -ww -p "$pid" -o command= 2>/dev/null || true)
  printf '%s' "$cmd"
}

reconcile_cmd_has_token() {
  local cmd=$1 needle=$2 first="" rest="" token=""
  cmd="${cmd#"${cmd%%[![:space:]]*}"}"
  [ -n "$cmd" ] || return 1
  case "$cmd" in
    *"$needle"*) ;;
    *) return 1 ;;
  esac
  first=${cmd%% *}
  rest=${cmd#"$first"}
  rest=${rest#" "}
  token=${first##*/}
  case "$token" in
    "$needle") return 0 ;;
    bash|sh|python|python3)
      case "$rest" in
        *"$needle"*) return 0 ;;
      esac
      ;;
  esac
  return 1
}

reconcile_cmd_is_daily_writer() {
  local cmd=$1
  reconcile_cmd_has_token "$cmd" "grokbot-genseo-daily" && return 0
  reconcile_cmd_has_token "$cmd" "grokbot-genseo-daily.sh" && return 0
  reconcile_cmd_has_token "$cmd" "run_ticket_headless.sh" && return 0
  return 1
}

reconcile_cmd_is_landing_writer() {
  local cmd=$1
  reconcile_cmd_has_token "$cmd" "run_landing_daily.sh" && return 0
  reconcile_cmd_has_token "$cmd" "run_landing_headless.sh" && return 0
  return 1
}

reconcile_cmd_is_publisher() {
  local cmd=$1
  reconcile_cmd_has_token "$cmd" "shopify_publisher.py" && return 0
  reconcile_cmd_has_token "$cmd" "landing_publisher.py" && return 0
  return 1
}

reconcile_cmd_matches_lane() {
  local lane=$1 cmd=$2
  case "$lane" in
    daily)
      reconcile_cmd_is_daily_writer "$cmd" && return 0
      reconcile_cmd_is_publisher "$cmd" && return 0
      ;;
    landing)
      reconcile_cmd_is_landing_writer "$cmd" && return 0
      reconcile_cmd_is_publisher "$cmd" && return 0
      ;;
    any)
      reconcile_cmd_is_daily_writer "$cmd" && return 0
      reconcile_cmd_is_landing_writer "$cmd" && return 0
      reconcile_cmd_is_publisher "$cmd" && return 0
      ;;
  esac
  return 1
}

# Space-separated PIDs in RECONCILE_LIVE_WRITERS. Does not print the process list.
reconcile_collect_writers() {
  local lane=$1 psout="" pid="" cmd=""
  RECONCILE_LIVE_WRITERS=""
  psout=$(ps -axww -o pid=,args= 2>/dev/null || ps -eo pid=,args= 2>/dev/null || true)
  while read -r pid cmd; do
    case "$pid" in
      ''|*[!0-9]*|0) continue ;;
    esac
    reconcile_pid_alive "$pid" || continue
    reconcile_cmd_matches_lane "$lane" "$cmd" || continue
    case " $RECONCILE_LIVE_WRITERS " in
      *" $pid "*) ;;
      *) RECONCILE_LIVE_WRITERS="${RECONCILE_LIVE_WRITERS}${pid} " ;;
    esac
  done <<< "$psout"
}

reconcile_read_pid() {
  local pid=""
  [ -f "$1/pid" ] || return 1
  IFS= read -r pid < "$1/pid" || return 1
  case "$pid" in
    ''|*[!0-9]*|0) return 1 ;;
  esac
  printf '%s\n' "$pid"
}

reconcile_note_writer() {
  local pid=$1
  case " $RECONCILE_LIVE_WRITERS " in
    *" $pid "*) ;;
    *) RECONCILE_LIVE_WRITERS="${RECONCILE_LIVE_WRITERS}${pid} " ;;
  esac
}

# Appends a live recorded PID when its command is a writer, a publisher, or unreadable.
# An unrelated live PID (the number was reused) does not count.
reconcile_recorded_writer() {
  local path=$1 lane=$2 pid="" cmd=""
  pid=$(reconcile_read_pid "$path" || true)
  [ -n "$pid" ] || return 1
  reconcile_pid_alive "$pid" || return 1
  cmd=$(reconcile_pid_command "$pid")
  if [ -z "$cmd" ]; then
    reconcile_note_writer "$pid"
    return 0
  fi
  if reconcile_cmd_matches_lane "$lane" "$cmd"; then
    reconcile_note_writer "$pid"
    return 0
  fi
  return 1
}

# Sets LOCK_* for one path. Suggests an unlock only when age > threshold,
# no live writer, and the directory has no unexpected names.
reconcile_inspect_lock() {
  local label=$1 path=$2 lane=$3 threshold=$4
  local names="" base="" pid="" cmd=""
  LOCK_LABEL=$label
  LOCK_PATH=$path
  LOCK_LANE=$lane
  LOCK_THRESHOLD=$threshold
  LOCK_AGE=""
  LOCK_LIVE=""
  LOCK_KIND=absent
  LOCK_EXTRA=0
  LOCK_SUGGEST=no
  LOCK_REASON=absent
  LOCK_RECORDED=missing
  LOCK_RECORDED_STATE=missing
  if [ ! -e "$path" ] && [ ! -L "$path" ]; then
    return 0
  fi
  if [ -L "$path" ]; then
    LOCK_KIND=symlink
    LOCK_REASON=symlink
    return 0
  fi
  if [ ! -d "$path" ]; then
    LOCK_KIND=file
    LOCK_REASON=not-a-directory
    return 0
  fi
  LOCK_KIND=dir
  pid=$(reconcile_read_pid "$path" || true)
  if [ -z "$pid" ]; then
    if [ -f "$path/pid" ]; then
      LOCK_RECORDED=invalid
      LOCK_RECORDED_STATE=invalid
    fi
  else
    LOCK_RECORDED=$pid
    if reconcile_pid_alive "$pid"; then
      cmd=$(reconcile_pid_command "$pid")
      if [ -z "$cmd" ] || reconcile_cmd_matches_lane "$lane" "$cmd"; then
        LOCK_RECORDED_STATE=alive-writer
      else
        LOCK_RECORDED_STATE=alive-other
      fi
    else
      LOCK_RECORDED_STATE=dead
    fi
  fi
  if ! LOCK_AGE=$(reconcile_lock_age "$path"); then
    LOCK_AGE=""
    LOCK_REASON=mtime-unknown
    return 0
  fi
  reconcile_collect_writers "$lane"
  reconcile_recorded_writer "$path" "$lane" || true
  LOCK_LIVE=$RECONCILE_LIVE_WRITERS
  if [ -n "$LOCK_LIVE" ]; then
    LOCK_REASON=live-writer
    return 0
  fi
  if ! names=$(ls -A "$path" 2>/dev/null); then
    LOCK_REASON=unlistable
    return 0
  fi
  if [ -n "$names" ]; then
    while IFS= read -r base; do
      [ -n "$base" ] || continue
      case "$lane" in
        daily)
          case "$base" in
            pid|started) ;;
            *) LOCK_EXTRA=1 ;;
          esac
          ;;
        *)
          LOCK_EXTRA=1
          ;;
      esac
    done <<< "$names"
  fi
  if [ "$LOCK_EXTRA" = 1 ]; then
    LOCK_REASON=unexpected-files
    return 0
  fi
  case "$LOCK_AGE" in
    ''|*[!0-9-]*) LOCK_REASON=mtime-unknown; return 0 ;;
  esac
  if [ "$LOCK_AGE" -gt "$threshold" ]; then
    LOCK_SUGGEST=yes
    LOCK_REASON=stale
  else
    LOCK_REASON=younger-than-threshold
  fi
}

reconcile_print_lock() {
  printf 'lock %s: %s\n' "$LOCK_LABEL" "$LOCK_KIND"
  printf 'lock %s path: %s\n' "$LOCK_LABEL" "$LOCK_PATH"
  if [ -n "$LOCK_AGE" ]; then
    printf 'lock %s age: %s\n' "$LOCK_LABEL" "$LOCK_AGE"
  else
    printf 'lock %s age: unknown\n' "$LOCK_LABEL"
  fi
  printf 'lock %s threshold: %s\n' "$LOCK_LABEL" "$LOCK_THRESHOLD"
  printf 'lock %s recorded_pid: %s %s\n' "$LOCK_LABEL" "$LOCK_RECORDED" "$LOCK_RECORDED_STATE"
  if [ -n "$LOCK_LIVE" ]; then
    printf 'lock %s live_writer: %s\n' "$LOCK_LABEL" "$LOCK_LIVE"
  else
    printf 'lock %s live_writer: none\n' "$LOCK_LABEL"
  fi
  printf 'lock %s suggested_unlock: %s\n' "$LOCK_LABEL" "$LOCK_SUGGEST"
  printf 'lock %s reason: %s\n' "$LOCK_LABEL" "$LOCK_REASON"
  if [ "$LOCK_SUGGEST" = yes ]; then
    if [ "$LOCK_LANE" = daily ]; then
      printf 'lock %s suggest: rm -f %q %q\n' "$LOCK_LABEL" "$LOCK_PATH/pid" "$LOCK_PATH/started"
    fi
    printf 'lock %s suggest: rmdir %q\n' "$LOCK_LABEL" "$LOCK_PATH"
  fi
}

# 0 removed, absent, or younger than the threshold. 4 left in place on purpose.
reconcile_apply_lock() {
  reconcile_inspect_lock "$1" "$2" "$3" "$4"
  case "$LOCK_REASON" in
    absent)
      printf 'lock_apply %s: absent\n' "$LOCK_LABEL"
      return 0
      ;;
    younger-than-threshold)
      printf 'lock_apply %s: kept younger-than-threshold\n' "$LOCK_LABEL"
      return 0
      ;;
    stale)
      ;;
    *)
      printf 'lock_apply %s: kept %s\n' "$LOCK_LABEL" "$LOCK_REASON"
      return 4
      ;;
  esac
  # Re-check immediately before removal. Inspect already required a dead writer.
  reconcile_collect_writers "$LOCK_LANE"
  reconcile_recorded_writer "$LOCK_PATH" "$LOCK_LANE" || true
  if [ -n "$RECONCILE_LIVE_WRITERS" ]; then
    printf 'lock_apply %s: kept live-writer\n' "$LOCK_LABEL"
    return 4
  fi
  if [ "$LOCK_LANE" = daily ]; then
    rm -f "$LOCK_PATH/pid" "$LOCK_PATH/started" || {
      printf 'lock_apply %s: kept rm-failed\n' "$LOCK_LABEL"
      return 4
    }
  fi
  if rmdir "$LOCK_PATH" 2>/dev/null; then
    printf 'lock_apply %s: removed\n' "$LOCK_LABEL"
    return 0
  fi
  printf 'lock_apply %s: kept rmdir-failed\n' "$LOCK_LABEL"
  return 4
}

reconcile_print_checklist() {
  local self="" line=""
  if [ -f "$0" ]; then
    self=$0
  else
    printf '%s\n' "checklist: unavailable. Run: bash scripts/mac_return_reconcile.sh"
    return 0
  fi
  while IFS= read -r line; do
    case "$line" in
      '# checklist: '*) printf '%s\n' "${line#"# "}" ;;
    esac
  done < "$self"
}

reconcile_ict() {
  local s="" z=""
  for z in Asia/Saigon Asia/Ho_Chi_Minh; do
    s=$(TZ="$z" date '+%F %T %z' 2>/dev/null) || s=""
    case "$s" in
      *+0700)
        printf '%s %s\n' "$s" "$z"
        return 0
        ;;
    esac
  done
  s=$(date '+%F %T %z')
  printf '%s zone-unknown\n' "$s"
}

reconcile_historical() {
  local short=$1 full=""
  full=$(git -C "$REPO" rev-parse --verify --quiet "${short}^{commit}" 2>/dev/null) || full=""
  if [ -z "$full" ]; then
    printf 'historical %s: not in this clone\n' "$short"
    return 0
  fi
  printf 'historical %s: present %s\n' "$short" "$(git -C "$REPO" log -1 --format='%h %d %s' "$full" 2>/dev/null || printf '%s' "$full")"
  if git -C "$REPO" rev-parse --verify --quiet origin/main >/dev/null 2>&1; then
    if git -C "$REPO" merge-base --is-ancestor "$full" origin/main 2>/dev/null; then
      printf 'historical %s: ancestor of origin/main\n' "$short"
    else
      printf 'historical %s: not an ancestor of origin/main. Keep it. Do not force-push.\n' "$short"
    fi
  else
    printf 'historical %s: origin/main missing, ancestry not checked\n' "$short"
  fi
}

DAILY_RAW=${GENSEO_LOCK_STALE_SEC:-}
DAILY_THRESHOLD=$(reconcile_threshold "$DAILY_RAW" 21600)
LANDING_THRESHOLD=14400
case "$DAILY_RAW" in
  ''|*[!0-9]*) DAILY_THRESHOLD_SOURCE=default ;;
  *) DAILY_THRESHOLD_SOURCE=GENSEO_LOCK_STALE_SEC ;;
esac

if ! REPO=$(git -C "$GENSEO_HOME" rev-parse --show-toplevel 2>/dev/null); then
  printf 'repo: not a git work tree: %s\n' "$GENSEO_HOME" >&2
  exit 1
fi

HOST=$(hostname -s 2>/dev/null || hostname 2>/dev/null || printf 'unknown')
ICT=$(reconcile_ict)
BRANCH=$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || printf 'unknown')
HEAD_SHA=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || printf 'unknown')

if [ "$APPLY" = 1 ]; then
  MODE_NAME=apply
else
  MODE_NAME=dry-run
fi
if [ "$APPLY" = 1 ]; then
  GIT_APPLY_WORD=yes
else
  GIT_APPLY_WORD=no
fi
if [ "$APPLY_LOCK" = 1 ]; then
  LOCK_APPLY_WORD=yes
else
  LOCK_APPLY_WORD=no
fi
printf '%s\n' "== Mac return reconcile =="
printf 'mode: %s\n' "$MODE_NAME"
printf 'git_apply: %s\n' "$GIT_APPLY_WORD"
printf 'lock_apply: %s\n' "$LOCK_APPLY_WORD"
printf 'ict: %s\n' "$ICT"
printf 'host: %s\n' "$HOST"
printf 'repo: %s\n' "$REPO"
printf 'branch: %s\n' "$BRANCH"
printf 'head: %s\n' "$HEAD_SHA"
printf '%s\n' "status:"
git -C "$REPO" status -sb 2>/dev/null | while IFS= read -r line; do
  printf 'status: %s\n' "$line"
done || true

printf '%s\n' "== fetch =="
FETCH_RC=0
FETCH_OUT=$(GIT_TERMINAL_PROMPT=0 git -C "$REPO" fetch origin 2>&1) || FETCH_RC=$?
if [ "$FETCH_RC" = 0 ]; then
  printf '%s\n' "fetch: ok"
else
  printf '%s\n' "fetch: failed"
  n=0
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    n=$((n + 1))
    [ "$n" -le 20 ] || continue
    printf 'fetch_detail: %s\n' "$line"
  done <<< "$FETCH_OUT"
fi

printf '%s\n' "== main vs HEAD =="
if git -C "$REPO" rev-parse --verify --quiet origin/main >/dev/null 2>&1; then
  ORIGIN_MAIN=$(git -C "$REPO" rev-parse origin/main)
  printf 'origin_main: %s\n' "$ORIGIN_MAIN"
  COUNTS=$(git -C "$REPO" rev-list --left-right --count origin/main...HEAD 2>/dev/null || true)
  BEHIND=""
  AHEAD=""
  read -r BEHIND AHEAD <<< "$COUNTS" || true
  case "$BEHIND" in
    ''|*[!0-9]*) BEHIND="" ;;
  esac
  case "$AHEAD" in
    ''|*[!0-9]*) AHEAD="" ;;
  esac
  if [ -n "$BEHIND" ] && [ -n "$AHEAD" ]; then
    printf 'main_vs_head: behind %s ahead %s\n' "$BEHIND" "$AHEAD"
    if [ "$BEHIND" = 0 ] && [ "$AHEAD" = 0 ]; then
      printf '%s\n' "main_vs_head_relation: same"
    elif [ "$BEHIND" -gt 0 ] && [ "$AHEAD" -gt 0 ]; then
      printf '%s\n' "main_vs_head_relation: diverged"
    elif [ "$AHEAD" -gt 0 ]; then
      printf '%s\n' "main_vs_head_relation: ahead"
    else
      printf '%s\n' "main_vs_head_relation: behind"
    fi
  else
    printf '%s\n' "main_vs_head: unknown"
    printf '%s\n' "main_vs_head_relation: unknown"
  fi
else
  ORIGIN_MAIN=""
  printf '%s\n' "origin_main: missing"
  printf '%s\n' "main_vs_head: unknown"
  printf '%s\n' "main_vs_head_relation: unknown"
fi

LOCAL_N=$(git -C "$REPO" rev-list --count HEAD --branches --not --remotes=origin 2>/dev/null) || LOCAL_N=""
case "$LOCAL_N" in
  ''|*[!0-9]*) printf '%s\n' "local_commits_not_on_origin: unknown" ;;
  *) printf 'local_commits_not_on_origin: %s\n' "$LOCAL_N" ;;
esac
if [ -n "$LOCAL_N" ] && [ "$LOCAL_N" != 0 ]; then
  n=0
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    n=$((n + 1))
    [ "$n" -le 30 ] || continue
    printf 'local_commit: %s\n' "$line"
  done <<< "$(git -C "$REPO" log --format='%h %d %s' -n 30 HEAD --branches --not --remotes=origin 2>/dev/null || true)"
  if [ "$LOCAL_N" -gt 30 ]; then
    printf '%s\n' "local_commits_truncated: yes"
  fi
fi
reconcile_historical e1b8519
reconcile_historical 289803e

PORCELAIN=$(git -C "$REPO" status --porcelain 2>/dev/null || true)
PERSONAS_DIRTY=0
if [ -n "$PORCELAIN" ]; then
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    printf 'dirty: %s\n' "$line"
    case "$line" in
      *personas/index.json*) PERSONAS_DIRTY=1 ;;
    esac
  done <<< "$PORCELAIN"
else
  printf '%s\n' "dirty: none"
fi
if [ "$PERSONAS_DIRTY" = 1 ]; then
  printf '%s\n' "personas_index: dirty. Leave it. DAILY-RUN.md keeps the MacBook image lane no-face until personas/index.json is re-synced from the Mini."
else
  printf '%s\n' "personas_index: clean"
fi

if git -C "$REPO" check-ignore -q state 2>/dev/null || git -C "$REPO" check-ignore -q state/ 2>/dev/null; then
  printf '%s\n' "state_ignored: yes"
else
  printf '%s\n' "state_ignored: no"
fi

GD=$(git -C "$REPO" rev-parse --git-dir 2>/dev/null || true)
case "$GD" in
  /*|"") ;;
  *) GD="$REPO/$GD" ;;
esac
GIT_BUSY=0
if [ -n "$GD" ]; then
  if [ -e "$GD/MERGE_HEAD" ] || [ -d "$GD/rebase-merge" ] || [ -d "$GD/rebase-apply" ] || [ -e "$GD/CHERRY_PICK_HEAD" ] || [ -e "$GD/REVERT_HEAD" ]; then
    GIT_BUSY=1
  fi
fi
if [ "$GIT_BUSY" = 1 ]; then
  printf '%s\n' "git_in_progress: yes"
else
  printf '%s\n' "git_in_progress: no"
fi

printf '%s\n' "== locks =="
printf 'threshold_daily_sec: %s\n' "$DAILY_THRESHOLD"
printf 'threshold_daily_source: %s\n' "$DAILY_THRESHOLD_SOURCE"
printf '%s\n' "threshold_daily_doc: scripts/genseo_daily_lock.sh GENSEO_LOCK_STALE_SEC default 21600. Age alone is not enough while a writer PID is live."
printf 'threshold_landing_sec: %s\n' "$LANDING_THRESHOLD"
printf '%s\n' "threshold_landing_doc: scripts/run_landing_daily.sh uses age -gt 14400 then rmdir. This helper uses 14400 and does not read GENSEO_LANDING_LOCK_STALE_SEC."
printf '%s\n' "lock_note: a bare claude process is not a writer PID here. Before clearing a lock, look for one left from 2026-10-12."

DAILY_LOCK="$REPO/state/daily.lock"
LANDING_LOCK="$REPO/state/landing-daily.lock"
reconcile_inspect_lock "daily.lock" "$DAILY_LOCK" daily "$DAILY_THRESHOLD"
reconcile_print_lock
reconcile_inspect_lock "landing-daily.lock" "$LANDING_LOCK" landing "$LANDING_THRESHOLD"
reconcile_print_lock

for leftover in "$REPO/state"/daily.lock.stale.[0-9]* "$REPO/state"/daily.lock.releasing.[0-9]*; do
  [ -e "$leftover" ] || continue
  printf 'leftover: %s not touched\n' "$leftover"
done

printf '%s\n' "== reminders =="
printf '%s\n' "wrapper: bash scripts/install_mac_daily_wrapper.sh"
printf '%s\n' "wrapper_doc: DAILY-RUN.md docs/TICKET_REFILL.md"
printf '%s\n' "wrapper_dest: ~/bin/grokbot-genseo-daily.sh"
printf '%s\n' "wrapper_plist_repo: deploy/com.pati.genseo-daily.macbook.plist"
printf '%s\n' "wrapper_plist_installed: ~/Library/LaunchAgents/com.pati.genseo-daily.plist"
printf '%s\n' "landing_plist_repo: deploy/com.pati.genseo-landing.macbook.plist"
printf '%s\n' "landing_script: scripts/run_landing_daily.sh"
printf '%s\n' "worker: agent worker start --name MacBook-Pro"
printf '%s\n' "launchagent: com.pati.cursor-agent-worker"
printf '%s\n' "does_not: publish, Shopify, git push, git reset --hard, force-push, launchctl, worker start"
reconcile_print_checklist

printf '%s\n' "== actions =="
LOCK_PROBLEM=0
if [ "$APPLY_LOCK" = 1 ]; then
  reconcile_apply_lock "daily.lock" "$DAILY_LOCK" daily "$DAILY_THRESHOLD" || LOCK_PROBLEM=4
  reconcile_apply_lock "landing-daily.lock" "$LANDING_LOCK" landing "$LANDING_THRESHOLD" || LOCK_PROBLEM=4
else
  printf '%s\n' "lock_apply: not requested"
fi

apply_allowed() {
  local n=""
  APPLY_ALLOWED=1
  if [ "$FETCH_RC" != 0 ]; then
    printf '%s\n' "apply_block: fetch-failed"
    APPLY_ALLOWED=0
  fi
  if [ "$BRANCH" != main ]; then
    printf '%s\n' "apply_block: not-on-main"
    printf '%s\n' "apply_next: this script does not switch branches. Review this branch, then fast-forward main yourself when it is clean."
    APPLY_ALLOWED=0
  fi
  if [ "$GIT_BUSY" = 1 ]; then
    printf '%s\n' "apply_block: git-operation-in-progress"
    APPLY_ALLOWED=0
  fi
  if [ -n "$PORCELAIN" ]; then
    printf '%s\n' "apply_block: dirty"
    printf '%s\n' "apply_next: git status --short"
    printf '%s\n' "apply_next: this script does not stash, commit, or reset."
    if [ "$PERSONAS_DIRTY" = 1 ]; then
      printf '%s\n' "apply_next: leave personas/index.json. DAILY-RUN.md keeps the MacBook image lane no-face until it is re-synced from the Mini."
    fi
    APPLY_ALLOWED=0
  fi
  n=$LOCAL_N
  case "$n" in
    ''|*[!0-9]*|0) ;;
    *)
      printf '%s\n' "apply_block: local-commits-not-on-origin"
      printf '%s\n' "apply_next: git log --oneline --decorate -n 30 HEAD --branches --not --remotes=origin"
      printf '%s\n' "apply_next: git show <sha>"
      printf '%s\n' "apply_next: do not run git push --force"
      printf '%s\n' "apply_next: do not run git reset --hard"
      printf '%s\n' "apply_next: a normal git push, after you have read the commits, is outside this script."
      APPLY_ALLOWED=0
      ;;
  esac
  case "$n" in
    ''|*[!0-9]*)
      printf '%s\n' "apply_block: local-commits-unknown"
      APPLY_ALLOWED=0
      ;;
  esac
  if [ -z "$ORIGIN_MAIN" ]; then
    printf '%s\n' "apply_block: origin-main-missing"
    APPLY_ALLOWED=0
  elif ! git -C "$REPO" merge-base --is-ancestor HEAD origin/main 2>/dev/null; then
    printf '%s\n' "apply_block: head-not-ancestor-of-origin-main"
    APPLY_ALLOWED=0
  fi
  reconcile_collect_writers any
  if [ -n "$RECONCILE_LIVE_WRITERS" ]; then
    printf 'apply_block: live-writer %s\n' "$RECONCILE_LIVE_WRITERS"
    APPLY_ALLOWED=0
  fi
  [ "$APPLY_ALLOWED" = 1 ]
}

APPLY_RESULT=not-requested
if [ "$APPLY" != 1 ]; then
  printf '%s\n' "apply: not requested"
elif [ "$LOCK_PROBLEM" != 0 ]; then
  printf '%s\n' "apply: skipped because a lock was not cleared"
  APPLY_RESULT=skipped-lock
else
  if apply_allowed; then
    BEFORE=$(git -C "$REPO" rev-parse HEAD)
    MERGE_RC=0
    MERGE_OUT=$(git -C "$REPO" merge --ff-only origin/main 2>&1) || MERGE_RC=$?
    while IFS= read -r line; do
      [ -n "$line" ] || continue
      printf 'merge: %s\n' "$line"
    done <<< "$MERGE_OUT"
    AFTER=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || printf 'unknown')
    ORIGIN_NOW=$(git -C "$REPO" rev-parse origin/main 2>/dev/null || printf 'missing')
    if [ "$MERGE_RC" != 0 ] || [ "$AFTER" != "$ORIGIN_NOW" ]; then
      printf '%s\n' "apply: fast-forward-failed"
      APPLY_RESULT=failed
    elif [ "$BEFORE" = "$AFTER" ]; then
      printf '%s\n' "apply: already up to date"
      APPLY_RESULT=uptodate
    else
      printf '%s\n' "apply: fast-forward"
      APPLY_RESULT=fast-forward
    fi
  else
    printf '%s\n' "apply: refused"
    APPLY_RESULT=refused
  fi
fi

if [ "$APPLY" != 1 ] && [ "$APPLY_LOCK" != 1 ]; then
  printf '%s\n' "result: ok"
  exit 0
fi
if [ "$APPLY_RESULT" = failed ] || [ "$APPLY_RESULT" = refused ]; then
  printf '%s\n' "result: apply-refused"
  exit 3
fi
if [ "$LOCK_PROBLEM" != 0 ] || [ "$APPLY_RESULT" = skipped-lock ]; then
  printf '%s\n' "result: lock-not-cleared"
  exit 4
fi
printf '%s\n' "result: ok"
exit 0

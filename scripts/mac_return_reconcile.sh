#!/bin/bash
# MacBook return reconcile. Run this on the Mac after days offline.
# Bash 3.2 safe: no namerefs, no mapfile, no ${var,,}, no globstar.
# Dry-run is the default. It does not publish, call Shopify, push, reset, copy the wrapper, or start launchd.
#
# Offline: bash tests/test_mac_return_reconcile.sh
#
# checklist: 1. cd ~/genseo && bash scripts/mac_return_reconcile.sh
# checklist:    Default is dry-run. It prints ICT time, git status, main vs HEAD, local commits that are not on origin, and lock ages. It fetches origin. It does not merge, delete a lock, push, reset, copy the wrapper, or publish.
# checklist: 2. If local commits are not on origin, read them with git show and keep them. Do not run git push --force. Do not run git reset --hard. e1b8519 and 289803e were unpushed publish commits on this Mac. If either is still local, leave it.
# checklist: 3. If personas/index.json is dirty, leave it. DAILY-RUN.md keeps the MacBook image lane no-face until that file is re-synced from the Mini.
# checklist: 4. A lock is cleared only when you pass --apply-stale-lock, the lock is older than its documented threshold, and no live writer PID is running. The report prints the rmdir command on a dry-run and does not run it. If that directory changes before removal, it is left in place.
# checklist:    daily.lock threshold is 21600 seconds (6h), GENSEO_LOCK_STALE_SEC in scripts/genseo_daily_lock.sh. A live grokbot-genseo-daily or run_ticket_headless.sh blocks removal at any age.
# checklist:    landing-daily.lock threshold is 14400 seconds (4h), hardcoded in scripts/run_landing_daily.sh. A live run_landing_daily.sh or run_landing_headless.sh blocks removal at any age.
# checklist: 5. --apply fast-forwards main only: git merge --ff-only origin/main. It runs only when HEAD is main, the work tree is clean, fetch succeeded, and every local branch commit is already on origin. Otherwise it prints instructions and changes nothing. Local commits that are not on origin stay local. This script does not rebase them and does not push. Do not run git push --force.
# checklist: 6. When that fast-forward is allowed, or main is already up to date, --apply reinstalls the daily wrapper: bash scripts/install_mac_daily_wrapper.sh. Dry-run prints the plan and does not copy. The installer does not start launchd.
# checklist:    Docs: DAILY-RUN.md and docs/TICKET_REFILL.md. launchd label com.pati.genseo-daily runs ~/bin/grokbot-genseo-daily.sh. Pulling alone does not update ~/bin.
# checklist:    That wrapper waits for DNS before the first live-feed read (scripts/genseo_wait_for_network.sh). --apply copies the wrapper into ~/bin. The helper stays in this checkout.
# checklist:    Repo plist: deploy/com.pati.genseo-daily.macbook.plist. Installed path named in DAILY-RUN.md: ~/Library/LaunchAgents/com.pati.genseo-daily.plist.
# checklist:    That plist is GENSEO_HOST_ROLE=primary and GENSEO_TICKET_PREFIX=MB until a Mini failover-release. Copy it onto the installed LaunchAgent and bootstrap again. install_mac_daily_wrapper.sh does not change that env. Pulling alone does not update ~/bin.
# checklist: 7. Landing code updates by the pull: launchd runs scripts/run_landing_daily.sh from this checkout (DAILY-RUN.md). That script waits for the same DNS names before its first Shopify read. It is not copied to ~/bin. MacBook plist, from the install comment in deploy/com.pati.genseo-landing.macbook.plist:
# checklist:    cp deploy/com.pati.genseo-landing.macbook.plist ~/Library/LaunchAgents/com.pati.genseo-landing.plist
# checklist:    launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-landing.plist
# checklist:    Copy or bootstrap that plist only when the agent is not already loaded. This script does not.
# checklist:    Do not load the MacBook daily or landing agents while the Mini still has those labels bootstrapped. Unload the Mini first (docs/FAILOVER.md). Both loaded means two schedules.
# checklist: 8. Start the Cursor private worker yourself: cursor-agent worker start --name MacBook-Pro
# checklist:    Binary: ~/.local/bin/cursor-agent. The name agent collides with the Grok CLI. Mini template: deploy/com.pati.cursor-agent-worker.plist (installed only by scripts/mac_mini_failover_bootstrap.sh on the Mini). This script does not start the worker.
# checklist: 9. Read-only verify on dry-run (against origin/main) and after --apply (against the work tree): scripts/genseo_model_map.json maps claude-opus-5-5 to PATI-Alpha-Plan-Review and claude-fable-5 to PATI-Fable-5. The landing daily lane stays draft-only and never passes --live. Do not start grokbot-genseo-daily.sh or run_landing_daily.sh from this reconcile. The next 07:30 / 14:47 and 08:15 / 16:15 slots run them. Starting them here would publish or open a Shopify draft.
#
# Does not: genseo_daily_lock_acquire, shopify_publisher, landing_publisher, launchctl,
# cursor-agent worker start, git push, git reset, git checkout, git stash, git clean, rm -r.
# --apply is git merge --ff-only origin/main when that fast-forward is allowed,
# then scripts/install_mac_daily_wrapper.sh. It does not publish or start launchd.
# Fetch and that merge set gc.auto=0 so auto-gc cannot prune a local dangling commit.
# --apply-stale-lock moves one stale lock directory aside, checks it is still the
# same directory, then removes pid and started (daily only) and rmdir.
# A landing lock is rmdir only, and only when the directory is empty.
# A directory that was replaced is moved back and left in place.

set -uo pipefail

usage() {
  printf '%s\n' \
    "usage: bash scripts/mac_return_reconcile.sh [--dry-run] [--apply] [--apply-stale-lock]" \
    "GENSEO_HOME defaults to the checkout that contains this script (~/genseo on the Mac)." \
    "Default is dry-run: fetch and report. No merge, no lock delete, no push, no wrapper copy, no publish." \
    "--apply           git merge --ff-only origin/main when main is clean and every local commit is already on origin," \
    "                  then bash scripts/install_mac_daily_wrapper.sh. Does not publish or start launchd." \
    "--apply-stale-lock  remove one stale lock dir when its identity is unchanged and no writer is live." \
    "Read-only verify: scripts/genseo_model_map.json and a draft-only landing lane (never --live)." \
    "Exit 0 report finished. A dry-run verify failure still exits 0 and prints result: verify-failed." \
    "Exit 2 usage. Exit 3 apply refused. Exit 4 lock not cleared. Exit 5 --apply catch-up incomplete."
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
# git -C does not override these. A parent that exported them would
# fast-forward or fetch a different repository than GENSEO_HOME.
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE

# Epoch mtime. Same order as genseo_path_mtime in scripts/genseo_daily_lock.sh
# and path_mtime in scripts/run_landing_daily.sh:
# GNU stat -c, then BSD stat -f, then /usr/bin/python3.
# GNU stat -f is filesystem info and must not be tried first.
reconcile_path_mtime() {
  local p=$1 m=""
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
    m=$(/usr/bin/python3 -c 'import os,sys; print(int(os.stat(sys.argv[1]).st_mtime))' "$p" 2>/dev/null) || true
    case "$m" in
      ''|*[!0-9]*) return 1 ;;
    esac
  fi
  printf '%s\n' "$m"
}

# device:inode. GNU stat -c, then BSD stat -f. Same order as mtime.
reconcile_dir_id() {
  local p=$1 id=""
  id=$(stat -c '%d:%i' "$p" 2>/dev/null) || true
  case "$id" in
    ''|*[!0-9:]*) id="" ;;
  esac
  if [ -z "$id" ]; then
    id=$(stat -f '%d:%i' "$p" 2>/dev/null) || true
    case "$id" in
      ''|*[!0-9:]*) return 1 ;;
    esac
  fi
  printf '%s\n' "$id"
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
# RECONCILE_PS_OK=0 when the listing has no numeric pid: absence of a writer is then unknown.
reconcile_collect_writers() {
  local lane=$1 psout="" pid="" cmd="" seen=0
  RECONCILE_LIVE_WRITERS=""
  RECONCILE_PS_OK=0
  psout=$(ps -axww -o pid=,args= 2>/dev/null || ps -eo pid=,args= 2>/dev/null || true)
  while read -r pid cmd; do
    case "$pid" in
      ''|*[!0-9]*|0) continue ;;
    esac
    seen=1
    reconcile_pid_alive "$pid" || continue
    reconcile_cmd_matches_lane "$lane" "$cmd" || continue
    case " $RECONCILE_LIVE_WRITERS " in
      *" $pid "*) ;;
      *) RECONCILE_LIVE_WRITERS="${RECONCILE_LIVE_WRITERS}${pid} " ;;
    esac
  done <<< "$psout"
  if [ "$seen" = 0 ]; then
    return 1
  fi
  RECONCILE_PS_OK=1
  return 0
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
  reconcile_collect_writers "$lane" || true
  if [ "$RECONCILE_PS_OK" != 1 ]; then
    LOCK_REASON=process-list-unknown
    return 0
  fi
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

reconcile_names_ok() {
  local path=$1 lane=$2 names="" base=""
  names=$(ls -A "$path" 2>/dev/null) || return 1
  [ -n "$names" ] || return 0
  while IFS= read -r base; do
    [ -n "$base" ] || continue
    case "$lane" in
      daily)
        case "$base" in
          pid|started) ;;
          *) return 1 ;;
        esac
        ;;
      *)
        return 1
        ;;
    esac
  done <<< "$names"
  return 0
}

# missing, symlink, or file:<text>. Compared before a directory is deleted.
reconcile_pid_snapshot() {
  local pid=""
  if [ -L "$1/pid" ]; then
    printf '%s\n' symlink
    return 0
  fi
  if [ ! -f "$1/pid" ]; then
    printf '%s\n' missing
    return 0
  fi
  IFS= read -r pid < "$1/pid" || pid=""
  printf 'file:%s\n' "$pid"
}

# Move a held-aside lock back when the path is free. Never deletes on this path.
reconcile_restore_hold() {
  local hold=$1
  if [ ! -e "$LOCK_PATH" ] && [ ! -L "$LOCK_PATH" ]; then
    mv "$hold" "$LOCK_PATH" 2>/dev/null || printf 'lock_apply %s: aside %s\n' "$LOCK_LABEL" "$hold"
  else
    printf 'lock_apply %s: aside %s\n' "$LOCK_LABEL" "$hold"
  fi
}

# 0 removed, absent, or younger than the threshold. 4 left in place on purpose.
# Deletes only the directory object that was classified as stale. A replacement
# at the same path is moved back and kept. The hold name is not a
# daily.lock.stale.* / daily.lock.releasing.* path, so the next acquire's sweep
# does not remove it if a restore fails.
reconcile_apply_lock() {
  local id="" pid_snap="" mtime="" hold="" now_id="" now_pid="" now_m=""
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
  id=$(reconcile_dir_id "$LOCK_PATH" || true)
  pid_snap=$(reconcile_pid_snapshot "$LOCK_PATH")
  mtime=$(reconcile_path_mtime "$LOCK_PATH" || true)
  case "$id" in
    ''|*[!0-9:]*)
      printf 'lock_apply %s: kept id-unknown\n' "$LOCK_LABEL"
      return 4
      ;;
  esac
  if [ -L "$LOCK_PATH" ] || [ ! -d "$LOCK_PATH" ]; then
    printf 'lock_apply %s: kept changed\n' "$LOCK_LABEL"
    return 4
  fi
  now_id=$(reconcile_dir_id "$LOCK_PATH" || true)
  now_pid=$(reconcile_pid_snapshot "$LOCK_PATH")
  now_m=$(reconcile_path_mtime "$LOCK_PATH" || true)
  if [ "$now_id" != "$id" ] || [ "$now_pid" != "$pid_snap" ] || [ "$now_m" != "$mtime" ]; then
    printf 'lock_apply %s: kept changed\n' "$LOCK_LABEL"
    return 4
  fi
  if ! reconcile_names_ok "$LOCK_PATH" "$LOCK_LANE"; then
    printf 'lock_apply %s: kept changed\n' "$LOCK_LABEL"
    return 4
  fi
  reconcile_collect_writers "$LOCK_LANE" || true
  if [ "$RECONCILE_PS_OK" != 1 ]; then
    printf 'lock_apply %s: kept process-list-unknown\n' "$LOCK_LABEL"
    return 4
  fi
  reconcile_recorded_writer "$LOCK_PATH" "$LOCK_LANE" || true
  if [ -n "$RECONCILE_LIVE_WRITERS" ]; then
    printf 'lock_apply %s: kept live-writer\n' "$LOCK_LABEL"
    return 4
  fi
  # Test seam, unset on a Mac run. Placed after the checks so a swap here is
  # the removal window. A failing hook does not delete.
  if [ -n "${GENSEO_RECONCILE_BEFORE_RM:-}" ]; then
    if ! "$GENSEO_RECONCILE_BEFORE_RM" "$LOCK_PATH"; then
      printf 'lock_apply %s: kept pre-remove-hook-failed\n' "$LOCK_LABEL"
      return 4
    fi
  fi
  hold="${LOCK_PATH}.reconcile-hold.$$"
  if [ -e "$hold" ] || [ -L "$hold" ]; then
    printf 'lock_apply %s: kept hold-exists\n' "$LOCK_LABEL"
    return 4
  fi
  if ! mv "$LOCK_PATH" "$hold" 2>/dev/null; then
    printf 'lock_apply %s: kept mv-failed\n' "$LOCK_LABEL"
    return 4
  fi
  now_id=$(reconcile_dir_id "$hold" || true)
  now_pid=$(reconcile_pid_snapshot "$hold")
  if [ "$now_id" != "$id" ] || [ "$now_pid" != "$pid_snap" ]; then
    reconcile_restore_hold "$hold"
    printf 'lock_apply %s: kept changed\n' "$LOCK_LABEL"
    return 4
  fi
  if ! reconcile_names_ok "$hold" "$LOCK_LANE"; then
    reconcile_restore_hold "$hold"
    printf 'lock_apply %s: kept changed\n' "$LOCK_LABEL"
    return 4
  fi
  if [ "$LOCK_LANE" = daily ]; then
    rm -f "$hold/pid" "$hold/started" || {
      reconcile_restore_hold "$hold"
      printf 'lock_apply %s: kept rm-failed\n' "$LOCK_LABEL"
      return 4
    }
  fi
  if rmdir "$hold" 2>/dev/null; then
    printf 'lock_apply %s: removed\n' "$LOCK_LABEL"
    return 0
  fi
  reconcile_restore_hold "$hold"
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

reconcile_line_is_comment() {
  local s=$1
  s="${s#"${s%%[![:space:]]*}"}"
  case "$s" in
    '#'*) return 0 ;;
  esac
  return 1
}

# 0 when a non-comment line contains the --live flag.
reconcile_file_invokes_live() {
  local f=$1 line=""
  [ -f "$f" ] || return 1
  while IFS= read -r line || [ -n "$line" ]; do
    reconcile_line_is_comment "$line" && continue
    case "$line" in
      *'--live'*) return 0 ;;
    esac
  done < "$f"
  return 1
}

reconcile_python() {
  if command -v python3 >/dev/null 2>&1; then
    command python3 "$@"
    return $?
  fi
  if [ -x /usr/bin/python3 ]; then
    /usr/bin/python3 "$@"
    return $?
  fi
  return 127
}

# 0 ok, 2 missing, 1 invalid or unreadable.
reconcile_model_map_ok() {
  local f=$1
  [ -f "$f" ] || return 2
  reconcile_python - "$f" <<'PY'
import json, sys
path = sys.argv[1]
try:
    data = json.load(open(path))
except Exception:
    sys.exit(1)
ov = data.get("modelOverrides")
if not isinstance(ov, dict):
    sys.exit(1)
need = (
    ("claude-opus-5-5", "PATI-Alpha-Plan-Review"),
    ("claude-fable-5", "PATI-Fable-5"),
)
for key, val in need:
    if ov.get(key) != val:
        sys.exit(1)
sys.exit(0)
PY
}

# 0 ok, 2 missing file, 3 a non-comment --live flag, 4 a draft-only guard is gone.
reconcile_landing_draft_only() {
  local daily=$1 pub=$2 head=$3
  [ -f "$daily" ] && [ -f "$pub" ] && [ -f "$head" ] || return 2
  if reconcile_file_invokes_live "$daily"; then
    return 3
  fi
  grep -F -q -e 'GENSEO_LANDING_DAILY=1 GENSEO_LANDING_DRAFT=1' "$daily" || return 4
  grep -F -q -e 'if daily and mode == "live"' "$pub" || return 4
  grep -F -q -e '--live refused in the daily landing lane' "$pub" || return 4
  grep -F -q -e 'Never --live.' "$head" || return 4
  return 0
}

reconcile_origin_has() {
  local rel=$1
  [ -n "${ORIGIN_MAIN:-}" ] || return 1
  git --no-pager -C "$REPO" cat-file -e "origin/main:$rel" 2>/dev/null
}

reconcile_pipeline_present() {
  PIPELINE=0
  if [ -f "$REPO/deploy/grokbot-genseo-daily.sh" ] || [ -f "$REPO/scripts/genseo_model_map.json" ] || [ -f "$REPO/scripts/run_landing_daily.sh" ]; then
    PIPELINE=1
    return 0
  fi
  if reconcile_origin_has "deploy/grokbot-genseo-daily.sh" \
    || reconcile_origin_has "scripts/genseo_model_map.json" \
    || reconcile_origin_has "scripts/run_landing_daily.sh"; then
    PIPELINE=1
  fi
}

# Prints the path to use. Origin blobs are written to dest.
reconcile_take_file() {
  local rel=$1 dest=$2
  if [ "$VERIFY_SCOPE" = worktree ]; then
    if [ -f "$REPO/$rel" ]; then
      printf '%s\n' "$REPO/$rel"
      return 0
    fi
    return 1
  fi
  rm -f "$dest"
  if git --no-pager -C "$REPO" show "origin/main:$rel" >"$dest" 2>/dev/null; then
    printf '%s\n' "$dest"
    return 0
  fi
  rm -f "$dest"
  return 1
}

reconcile_verify() {
  local map_f="" land_f="" pub_f="" head_f="" wrap_f="" plist_f=""
  local fail=0 path="" rc=0
  reconcile_pipeline_present
  if [ "$PIPELINE" != 1 ]; then
    printf '%s\n' "verify: skipped-not-checkout"
    return 0
  fi
  if [ "$APPLY_RESULT" = fast-forward ] || [ "$APPLY_RESULT" = uptodate ]; then
    VERIFY_SCOPE=worktree
    printf '%s\n' "verify_scope: worktree"
  else
    VERIFY_SCOPE=origin
    printf '%s\n' "verify_scope: origin/main"
  fi
  map_f=$(mktemp "${TMPDIR:-/tmp}/mac-return-map.XXXXXX") || return 1
  land_f=$(mktemp "${TMPDIR:-/tmp}/mac-return-land.XXXXXX") || { rm -f "$map_f"; return 1; }
  pub_f=$(mktemp "${TMPDIR:-/tmp}/mac-return-pub.XXXXXX") || { rm -f "$map_f" "$land_f"; return 1; }
  head_f=$(mktemp "${TMPDIR:-/tmp}/mac-return-head.XXXXXX") || { rm -f "$map_f" "$land_f" "$pub_f"; return 1; }
  wrap_f=$(mktemp "${TMPDIR:-/tmp}/mac-return-wrapf.XXXXXX") || { rm -f "$map_f" "$land_f" "$pub_f" "$head_f"; return 1; }
  plist_f=$(mktemp "${TMPDIR:-/tmp}/mac-return-plist.XXXXXX") || { rm -f "$map_f" "$land_f" "$pub_f" "$head_f" "$wrap_f"; return 1; }

  path=$(reconcile_take_file "scripts/genseo_model_map.json" "$map_f" || true)
  rc=0
  if [ -z "$path" ]; then
    printf '%s\n' "verify_model_map: missing"
    fail=1
  else
    reconcile_model_map_ok "$path" || rc=$?
    case "$rc" in
      0) printf '%s\n' "verify_model_map: ok" ;;
      2) printf '%s\n' "verify_model_map: missing"; fail=1 ;;
      *) printf '%s\n' "verify_model_map: invalid"; fail=1 ;;
    esac
  fi

  path=$(reconcile_take_file "scripts/run_landing_daily.sh" "$land_f" || true)
  local pub_path="" head_path=""
  pub_path=$(reconcile_take_file "scripts/landing_publisher.py" "$pub_f" || true)
  head_path=$(reconcile_take_file "scripts/run_landing_headless.sh" "$head_f" || true)
  rc=0
  if [ -z "$path" ] || [ -z "$pub_path" ] || [ -z "$head_path" ]; then
    printf '%s\n' "verify_landing_draft_only: missing"
    fail=1
  else
    reconcile_landing_draft_only "$path" "$pub_path" "$head_path" || rc=$?
    case "$rc" in
      0) printf '%s\n' "verify_landing_draft_only: ok" ;;
      3) printf '%s\n' "verify_landing_draft_only: live-flag"; fail=1 ;;
      2) printf '%s\n' "verify_landing_draft_only: missing"; fail=1 ;;
      *) printf '%s\n' "verify_landing_draft_only: guard-missing"; fail=1 ;;
    esac
  fi
  if [ -n "$path" ] && grep -F -q 'genseo_wait_for_network.sh' "$path" \
    && grep -F -q 'genseo_wait_for_network;' "$path"; then
    printf '%s\n' "verify_landing_net_wait: ok"
  else
    printf '%s\n' "verify_landing_net_wait: missing"
    fail=1
  fi

  path=$(reconcile_take_file "deploy/grokbot-genseo-daily.sh" "$wrap_f" || true)
  if [ -z "$path" ]; then
    printf '%s\n' "verify_wrapper_feed_retry: missing"
    printf '%s\n' "verify_wrapper_role_default: missing"
    printf '%s\n' "verify_wrapper_net_wait: missing"
    fail=1
  else
    if grep -F -q 'GENSEO_LIVE_FEED_RETRIES' "$path"; then
      printf '%s\n' "verify_wrapper_feed_retry: ok"
    else
      printf '%s\n' "verify_wrapper_feed_retry: missing"
      fail=1
    fi
    if grep -F -q 'GENSEO_HOST_ROLE:-primary' "$path"; then
      printf '%s\n' "verify_wrapper_role_default: primary"
    else
      printf '%s\n' "verify_wrapper_role_default: missing"
      fail=1
    fi
    if grep -F -q 'genseo_wait_for_network.sh' "$path" \
      && grep -F -q 'genseo_wait_for_network;' "$path"; then
      printf '%s\n' "verify_wrapper_net_wait: ok"
    else
      printf '%s\n' "verify_wrapper_net_wait: missing"
      fail=1
    fi
  fi

  path=$(reconcile_take_file "deploy/com.pati.genseo-daily.macbook.plist" "$plist_f" || true)
  if [ -z "$path" ]; then
    printf '%s\n' "verify_repo_plist_role: absent"
  elif grep -F -q '<key>GENSEO_HOST_ROLE</key><string>primary</string>' "$path" \
    && grep -F -q '<key>GENSEO_TICKET_PREFIX</key><string>MB</string>' "$path"; then
    printf '%s\n' "verify_repo_plist_role: ok"
  else
    printf '%s\n' "verify_repo_plist_role: not-primary"
    fail=1
  fi

  rm -f "$map_f" "$land_f" "$pub_f" "$head_f" "$wrap_f" "$plist_f"
  if [ "$fail" = 1 ]; then
    printf '%s\n' "verify: fail"
    return 1
  fi
  printf '%s\n' "verify: ok"
  return 0
}

reconcile_prefix_file() {
  local prefix=$1 file=$2 n=0 line=""
  [ -f "$file" ] || return 0
  while IFS= read -r line || [ -n "$line" ]; do
    [ -n "$line" ] || continue
    n=$((n + 1))
    [ "$n" -le 40 ] || continue
    printf '%s: %s\n' "$prefix" "$line"
  done < "$file"
}

# dry-run prints the plan. apply copies when the checkout has the wrapper source.
reconcile_install_wrapper() {
  local mode=$1
  local src="$REPO/deploy/grokbot-genseo-daily.sh"
  local install_script="$SCRIPT_DIR/install_mac_daily_wrapper.sh"
  local out="" err="" rc=0 dest=""
  if [ ! -f "$install_script" ]; then
    install_script="$REPO/scripts/install_mac_daily_wrapper.sh"
  fi
  if [ ! -f "$src" ]; then
    if reconcile_origin_has "deploy/grokbot-genseo-daily.sh"; then
      if [ "$mode" = dry-run ]; then
        printf '%s\n' "wrapper_install: planned after fast-forward"
        return 0
      fi
      printf '%s\n' "wrapper_install: failed missing-source"
      return 1
    fi
    printf '%s\n' "wrapper_install: skipped missing-source"
    return 0
  fi
  if [ ! -f "$install_script" ]; then
    printf '%s\n' "wrapper_install: failed missing-installer"
    [ "$mode" = dry-run ] && return 0
    return 1
  fi
  out=$(mktemp "${TMPDIR:-/tmp}/mac-return-wrap-out.XXXXXX") || return 1
  err=$(mktemp "${TMPDIR:-/tmp}/mac-return-wrap-err.XXXXXX") || { rm -f "$out"; return 1; }
  rc=0
  if [ "$mode" = dry-run ]; then
    printf '%s\n' "wrapper_install: planned"
    env GENSEO_HOME="$REPO" bash "$install_script" --dry-run >"$out" 2>"$err" || rc=$?
  else
    env GENSEO_HOME="$REPO" bash "$install_script" >"$out" 2>"$err" || rc=$?
  fi
  reconcile_prefix_file wrapper_install_detail "$out"
  reconcile_prefix_file wrapper_install_err "$err"
  rm -f "$out" "$err"
  if [ "$mode" = dry-run ]; then
    printf 'wrapper_install_rc: %s\n' "$rc"
    return 0
  fi
  if [ "$rc" != 0 ]; then
    printf 'wrapper_install: failed rc %s\n' "$rc"
    return 1
  fi
  dest="${HOME:-}/bin/grokbot-genseo-daily.sh"
  if [ -z "${HOME:-}" ] || [ ! -f "$dest" ] || [ ! -x "$dest" ] || ! cmp -s "$src" "$dest"; then
    printf '%s\n' "wrapper_install: mismatch"
    return 1
  fi
  printf '%s\n' "wrapper_install: copied"
  printf '%s\n' "wrapper_dest_match: yes"
  return 0
}

# 0 when --apply must not fast-forward. Local-only commits stay local: no rebase, no push.
reconcile_catchup_blocked() {
  if [ "${FETCH_RC:-1}" != 0 ] || [ "${BRANCH:-}" != main ] || [ "${GIT_BUSY:-1}" = 1 ]; then
    return 0
  fi
  if [ "${STATUS_RC:-1}" != 0 ] || [ -n "${PORCELAIN:-}" ]; then
    return 0
  fi
  case "${LOCAL_N:-}" in
    0) ;;
    *) return 0 ;;
  esac
  if [ -z "${ORIGIN_MAIN:-}" ]; then
    return 0
  fi
  return 1
}

reconcile_catchup_plan() {
  printf '%s\n' "catchup_cmd: git merge --ff-only origin/main"
  CATCHUP_STATE=blocked
  if reconcile_catchup_blocked; then
    printf '%s\n' "catchup: blocked"
    return 0
  fi
  if [ "$HEAD_SHA" = "$ORIGIN_MAIN" ]; then
    CATCHUP_STATE=uptodate
    printf '%s\n' "catchup: already up to date"
    return 0
  fi
  if git -C "$REPO" merge-base --is-ancestor HEAD origin/main 2>/dev/null; then
    CATCHUP_STATE=behind
    printf '%s\n' "catchup: would fast-forward on --apply"
    return 0
  fi
  printf '%s\n' "catchup: blocked"
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
elif [ "$APPLY_LOCK" = 1 ]; then
  MODE_NAME=apply-stale-lock
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
FETCH_OUT=$(GIT_TERMINAL_PROMPT=0 git -C "$REPO" -c gc.auto=0 fetch origin 2>&1) || FETCH_RC=$?
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

STATUS_RC=0
PORCELAIN=$(git -C "$REPO" status --porcelain 2>/dev/null) || STATUS_RC=$?
PERSONAS_DIRTY=0
if [ "$STATUS_RC" != 0 ]; then
  printf '%s\n' "dirty: unknown"
elif [ -n "$PORCELAIN" ]; then
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
if [ "$STATUS_RC" != 0 ]; then
  printf '%s\n' "personas_index: unknown"
elif [ "$PERSONAS_DIRTY" = 1 ]; then
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

for leftover in \
  "$REPO/state"/daily.lock.stale.[0-9]* \
  "$REPO/state"/daily.lock.releasing.[0-9]* \
  "$REPO/state"/daily.lock.reconcile-hold.[0-9]* \
  "$REPO/state"/landing-daily.lock.reconcile-hold.[0-9]*
do
  [ -e "$leftover" ] || continue
  printf 'leftover: %s not touched\n' "$leftover"
done

printf '%s\n' "== reminders =="
printf '%s\n' "wrapper: bash scripts/install_mac_daily_wrapper.sh"
printf '%s\n' "wrapper_doc: DAILY-RUN.md docs/TICKET_REFILL.md"
printf '%s\n' "wrapper_dest: ~/bin/grokbot-genseo-daily.sh"
printf '%s\n' "wrapper_plist_repo: deploy/com.pati.genseo-daily.macbook.plist"
printf '%s\n' "wrapper_plist_installed: ~/Library/LaunchAgents/com.pati.genseo-daily.plist"
printf '%s\n' "wrapper_role: MacBook GENSEO_HOST_ROLE=primary GENSEO_TICKET_PREFIX=MB until Mini failover-release. Copy the plist and bootstrap; the wrapper installer does not."
printf '%s\n' "landing_plist_repo: deploy/com.pati.genseo-landing.macbook.plist"
printf '%s\n' "landing_script: scripts/run_landing_daily.sh"
printf '%s\n' "worker: cursor-agent worker start --name MacBook-Pro"
printf '%s\n' "worker_bin: ~/.local/bin/cursor-agent"
printf '%s\n' "worker_note: do not start argv0 agent; that name collides with the Grok CLI"
printf '%s\n' "launchagent: com.pati.cursor-agent-worker"
printf '%s\n' "does_not: publish, Shopify, git push, git reset --hard, force-push, launchctl, worker start, landing --live"
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
  if [ "${STATUS_RC:-1}" != 0 ]; then
    printf '%s\n' "apply_block: status-failed"
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
  reconcile_collect_writers any || true
  if [ "$RECONCILE_PS_OK" != 1 ]; then
    printf '%s\n' "apply_block: process-list-unknown"
    APPLY_ALLOWED=0
  fi
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
    printf '%s\n' "catchup_cmd: git merge --ff-only origin/main"
    MERGE_OUT=$(git -C "$REPO" -c gc.auto=0 merge --ff-only origin/main 2>&1) || MERGE_RC=$?
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

printf '%s\n' "== catch-up =="
WRAPPER_PROBLEM=0
VERIFY_PROBLEM=0
if [ "$APPLY" = 1 ]; then
  case "$APPLY_RESULT" in
    fast-forward|uptodate)
      reconcile_install_wrapper apply || WRAPPER_PROBLEM=1
      ;;
    *)
      printf '%s\n' "wrapper_install: skipped not-fast-forwarded"
      ;;
  esac
elif [ "$APPLY_LOCK" = 1 ]; then
  printf '%s\n' "wrapper_install: not requested"
else
  reconcile_catchup_plan
  if [ "$CATCHUP_STATE" = blocked ]; then
    printf '%s\n' "wrapper_install: skipped catch-up-blocked"
  else
    reconcile_install_wrapper dry-run || true
  fi
fi
reconcile_verify || VERIFY_PROBLEM=1

if [ "$APPLY_RESULT" = failed ] || [ "$APPLY_RESULT" = refused ]; then
  printf '%s\n' "result: apply-refused"
  exit 3
fi
if [ "$LOCK_PROBLEM" != 0 ] || [ "$APPLY_RESULT" = skipped-lock ]; then
  printf '%s\n' "result: lock-not-cleared"
  exit 4
fi
if [ "$APPLY" = 1 ] && { [ "$WRAPPER_PROBLEM" = 1 ] || [ "$VERIFY_PROBLEM" = 1 ]; }; then
  printf '%s\n' "result: catch-up-incomplete"
  exit 5
fi
if [ "$VERIFY_PROBLEM" = 1 ]; then
  printf '%s\n' "result: verify-failed"
  exit 0
fi
printf '%s\n' "result: ok"
exit 0

#!/bin/bash
# Daily-batch lock for deploy/grokbot-genseo-daily.sh.
#
# state/daily.lock is a directory (atomic mkdir). The wrapper PID is state/daily.lock/pid.
# Launchd's 14:47 catch-up used to rmdir any lock older than 6 hours. A 07:30 batch still
# on a ticket is older than that and was losing its lock to the catch-up.
#
# Rules (genseo_daily_lock_acquire):
#   * mkdir wins — record $$ and keep the lock. Age is not consulted.
#   * Recorded PID is a live grokbot-genseo-daily (kill -0, command matches) — exit without
#     taking it, however old the directory is.
#   * Some other live grokbot-genseo-daily exists (old lock with no PID file, or a dead PID
#     left behind while the batch is still running) — same, do not take it.
#   * Recorded PID is dead, or this process's own PID (the holder died and the PID was reused
#     by us) — the lock is stale. Take it even if the directory is young.
#   * PID missing or not the wrapper — take it only when the directory is older than
#     GENSEO_LOCK_STALE_SEC (default 21600). A just-created lock has not written its PID yet.
#
# Release removes the directory only when the PID file is still $$. The previous trap was a
# bare rmdir, which deleted a lock a newer owner had just created.
#
# Sourced by the wrapper. Do not enable set -e here. Offline: bash tests/test_daily_lock.sh

genseo_lock_note() {
  if declare -F say >/dev/null 2>&1; then
    say "$*"
  fi
}

genseo_lock_stale_sec() {
  local s=${GENSEO_LOCK_STALE_SEC:-21600}
  case "$s" in
    ''|*[!0-9]*) s=21600 ;;
  esac
  printf '%s\n' "$s"
}

# Epoch mtime. GNU stat understands -c; BSD stat (macOS) understands -f. GNU `stat -f`
# is filesystem info and must not be tried first.
genseo_path_mtime() {
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

genseo_pid_state() {
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

# kill -0 succeeds for a zombie. A zombie holder is not a running batch.
genseo_pid_alive() {
  local pid=$1 state=""
  case "$pid" in
    ''|*[!0-9]*|0) return 1 ;;
  esac
  kill -0 "$pid" 2>/dev/null || return 1
  state=$(genseo_pid_state "$pid" || true)
  case "$state" in
    Z|z) return 1 ;;
  esac
  return 0
}

genseo_pid_command() {
  local pid=$1 cmd=""
  if [ -r "/proc/$pid/cmdline" ]; then
    cmd=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)
    printf '%s' "$cmd"
    return 0
  fi
  cmd=$(ps -ww -p "$pid" -o args= 2>/dev/null || ps -ww -p "$pid" -o command= 2>/dev/null || true)
  printf '%s' "$cmd"
}

# The daily wrapper, not vim/cp/grep that merely mention the filename.
#   /bin/bash .../grokbot-genseo-daily.sh
#   grokbot-genseo-daily          (argv0, including the test sleeper)
genseo_cmd_is_daily_wrapper() {
  local cmd=$1 first="" rest="" token=""
  cmd="${cmd#"${cmd%%[![:space:]]*}"}"
  [ -n "$cmd" ] || return 1
  case "$cmd" in
    *grokbot-genseo-daily*) ;;
    *) return 1 ;;
  esac
  first=${cmd%% *}
  rest=${cmd#"$first"}
  rest=${rest#" "}
  token=${first##*/}
  case "$token" in
    grokbot-genseo-daily|grokbot-genseo-daily.sh) return 0 ;;
    bash|sh)
      case "$rest" in
        *grokbot-genseo-daily*) return 0 ;;
      esac
      ;;
  esac
  return 1
}

# True for this shell, the scanner's subshell, or a direct child of either.
# classify/find run inside $(...), and that fork still has the wrapper's cmdline
# until it execs. Those are not a second batch. A launchd catch-up is a sibling, not a child.
genseo_pid_in_this_shell() {
  local pid=$1 ppid=""
  case "$pid" in
    ''|*[!0-9]*|0) return 1 ;;
  esac
  [ "$pid" = "$$" ] && return 0
  if [ -n "${BASHPID:-}" ] && [ "$pid" = "$BASHPID" ]; then
    return 0
  fi
  if [ -r "/proc/$pid/status" ]; then
    ppid=$(awk '/^PPid:/ {print $2}' "/proc/$pid/status" 2>/dev/null || true)
  else
    ppid=$(ps -p "$pid" -o ppid= 2>/dev/null | tr -d '[:space:]' || true)
  fi
  [ "$ppid" = "$$" ] && return 0
  if [ -n "${BASHPID:-}" ] && [ "$ppid" = "$BASHPID" ]; then
    return 0
  fi
  return 1
}

# Print the PID of a live daily wrapper that is not this shell, or return 1.
genseo_find_other_daily_wrapper() {
  local pid="" cmd=""
  if [ -d /proc ]; then
    for pid in /proc/[0-9]*; do
      pid=${pid#/proc/}
      genseo_pid_in_this_shell "$pid" && continue
      [ -r "/proc/$pid/cmdline" ] || continue
      cmd=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)
      if genseo_cmd_is_daily_wrapper "$cmd" && genseo_pid_alive "$pid"; then
        printf '%s\n' "$pid"
        return 0
      fi
    done
    return 1
  fi
  while read -r pid cmd; do
    case "$pid" in
      ''|*[!0-9]*|0) continue ;;
    esac
    genseo_pid_in_this_shell "$pid" && continue
    if genseo_cmd_is_daily_wrapper "$cmd" && genseo_pid_alive "$pid"; then
      printf '%s\n' "$pid"
      return 0
    fi
  done < <(ps -axww -o pid=,args= 2>/dev/null || ps -eo pid=,args= 2>/dev/null)
  return 1
}

genseo_daily_lock_read_pid() {
  local pid=""
  [ -f "$LOCK/pid" ] || return 1
  IFS= read -r pid < "$LOCK/pid" || return 1
  case "$pid" in
    ''|*[!0-9]*|0) return 1 ;;
  esac
  printf '%s\n' "$pid"
}

# One line: status|pid|age   status is live, held, stale, or absent.
genseo_daily_lock_classify() {
  local pid="" age=-1 m="" now="" other="" cmd="" stale_sec=""
  if [ ! -e "$LOCK" ]; then
    printf 'absent||\n'
    return 0
  fi
  if [ ! -d "$LOCK" ]; then
    printf 'held||\n'
    return 0
  fi
  pid=$(genseo_daily_lock_read_pid || true)
  now=$(date +%s)
  if m=$(genseo_path_mtime "$LOCK"); then
    age=$(( now - m ))
  fi
  if [ -n "$pid" ] && [ "$pid" != "$$" ] && genseo_pid_alive "$pid"; then
    cmd=$(genseo_pid_command "$pid")
    if [ -z "$cmd" ] || genseo_cmd_is_daily_wrapper "$cmd"; then
      printf 'live|%s|%s\n' "$pid" "$age"
      return 0
    fi
  fi
  stale_sec=$(genseo_lock_stale_sec)
  local stale=0
  if [ -n "$pid" ] && [ "$pid" = "$$" ]; then
    stale=1
  elif [ -n "$pid" ] && ! genseo_pid_alive "$pid"; then
    stale=1
  elif [ "$age" -ge 0 ] && [ "$age" -gt "$stale_sec" ]; then
    stale=1
  fi
  if [ "$stale" -eq 1 ]; then
    # Age, or a dead PID file, is not enough while a morning batch is still in the process table.
    other=$(genseo_find_other_daily_wrapper || true)
    if [ -n "$other" ]; then
      printf 'live|%s|%s\n' "$other" "$age"
      return 0
    fi
    printf 'stale|%s|%s\n' "$pid" "$age"
    return 0
  fi
  printf 'held|%s|%s\n' "$pid" "$age"
}

genseo_daily_lock_write_owner() {
  printf '%s\n' "$$" > "$LOCK/pid" || return 1
  date +%s > "$LOCK/started" 2>/dev/null || true
  return 0
}

genseo_daily_lock_sweep() {
  local d=""
  for d in "$LOCK".stale.[0-9]* "$LOCK".releasing.[0-9]*; do
    [ -d "$d" ] || continue
    rm -f "$d/pid" "$d/started"
    rmdir "$d" 2>/dev/null || true
  done
}

# Move a directory we just created and failed to stamp, so it cannot sit as a young PID-less lock.
genseo_daily_lock_drop_new_dir() {
  local dest="${LOCK}.releasing.$$"
  if mv "$LOCK" "$dest" 2>/dev/null; then
    rm -f "$dest/pid" "$dest/started"
    rmdir "$dest" 2>/dev/null || true
  fi
}

# 0 acquired, 10 held by a live batch (caller should exit 0), 1 could not record the owner.
genseo_daily_lock_acquire() {
  local attempt="" info="" status="" pid="" age="" dest=""
  [ -n "${LOCK:-}" ] || return 1
  for attempt in 1 2; do
    if mkdir "$LOCK" 2>/dev/null; then
      if genseo_daily_lock_write_owner; then
        genseo_daily_lock_sweep
        return 0
      fi
      genseo_daily_lock_drop_new_dir
      return 1
    fi
    info=$(genseo_daily_lock_classify)
    IFS='|' read -r status pid age <<< "$info"
    case "$status" in
      live)
        genseo_lock_note "another batch is running on this Mac (lock $LOCK pid $pid) — exit"
        return 10
        ;;
      held)
        genseo_lock_note "another batch is running on this Mac (lock $LOCK) — exit"
        return 10
        ;;
      absent)
        continue
        ;;
      stale)
        dest="${LOCK}.stale.$$"
        if mv "$LOCK" "$dest" 2>/dev/null && mkdir "$LOCK" 2>/dev/null; then
          if genseo_daily_lock_write_owner; then
            rm -f "$dest/pid" "$dest/started"
            rmdir "$dest" 2>/dev/null || true
            genseo_daily_lock_sweep
            genseo_lock_note "stale daily lock (pid ${pid:-missing}, age ${age}s) — taking over"
            return 0
          fi
          genseo_daily_lock_drop_new_dir
        fi
        if [ -d "$dest" ]; then
          if [ ! -d "$LOCK" ] && mv "$dest" "$LOCK" 2>/dev/null; then
            :
          else
            rm -f "$dest/pid" "$dest/started"
            rmdir "$dest" 2>/dev/null || true
          fi
        fi
        ;;
      *)
        genseo_lock_note "daily lock unreadable ($LOCK) — exit"
        return 1
        ;;
    esac
  done
  genseo_lock_note "another batch is running on this Mac (lock $LOCK) — exit"
  return 10
}

genseo_daily_lock_release() {
  local pid="" dest=""
  [ -n "${LOCK:-}" ] || return 0
  [ -d "$LOCK" ] || return 0
  if [ -f "$LOCK/pid" ]; then
    IFS= read -r pid < "$LOCK/pid" || pid=""
  fi
  [ "$pid" = "$$" ] || return 0
  dest="${LOCK}.releasing.$$"
  if mv "$LOCK" "$dest" 2>/dev/null; then
    rm -f "$dest/pid" "$dest/started"
    rmdir "$dest" 2>/dev/null || true
  fi
  return 0
}

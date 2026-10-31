#!/bin/bash
# User-level power assertion for one scheduled GenSeo run.
#
# pmset "sleep 1" is an idle timer. A busy job does not keep the Mac awake.
# On 2026-10-17 the MacBook was in maintenance sleep at 07:27, dark-woke at
# 07:38, and a morning batch could be suspended mid-run. caffeinate is
# user-level: no sudo, and this file does not change pmset.
#
#   -i  PreventUserIdleSystemSleep (the idle timer)
#   -s  PreventSystemSleep while on AC (a dark wake going back to sleep)
#   -w  this process. exec of a stable copy keeps the same PID, so the
#       assertion stays across that re-exec. Do not exec caffeinate in
#       place of this shell: the daily lock records $$, and the lock scanner
#       does not treat a caffeinate parent as the wrapper.
#
# The holder is a detached grandchild (its own session). This shell does not
# wait for it, and a later exec does not drop it. -w releases it when $$
# exits. On battery, -s is not enforced; -i still blocks idle sleep.
# If caffeinate or perl is missing, the run continues.
#
# Test hooks are ignored unless GENSEO_POWER_ASSERT_TEST=1:
#   GENSEO_CAFFEINATE            executable used instead of caffeinate
#   GENSEO_POWER_ASSERT_DISABLE=1  do not spawn
#
# Sourced by deploy/grokbot-genseo-daily.sh and scripts/run_landing_daily.sh.
# Bash 3.2 safe. Do not enable set -e here. Does not publish.

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  printf '%s\n' "source scripts/genseo_power_assert.sh from a daily wrapper; it does not publish." >&2
  exit 2
fi

# Print the pid of a detached caffeinate, or nothing on failure.
# The grandchild is reparented and put in its own session.
genseo_power_assert_spawn() {
  perl -MPOSIX -e '
    use POSIX qw(setsid);
    my $mid = fork();
    exit 1 unless defined $mid;
    if ($mid) {
      waitpid($mid, 0);
      my $rc = $? >> 8;
      exit($rc == 0 ? 0 : 1);
    }
    setsid();
    my $grand = fork();
    exit 1 unless defined $grand;
    if ($grand) {
      print "$grand\n";
      exit 0;
    }
    open STDIN, "<", "/dev/null";
    open STDOUT, ">", "/dev/null";
    open STDERR, ">", "/dev/null";
    exec @ARGV or exit 1;
  ' "$@"
}

# Arm once per process. A re-exec inherits GENSEO_POWER_ASSERTED=1 and the
# same PID, so it must not start a second holder. Returns 0 either way.
genseo_power_assert_arm() {
  local caf="" cpid=""
  if [ "${GENSEO_POWER_ASSERTED:-}" = 1 ]; then
    return 0
  fi
  if [ "${GENSEO_POWER_ASSERT_TEST:-0}" = 1 ] && [ "${GENSEO_POWER_ASSERT_DISABLE:-}" = 1 ]; then
    export GENSEO_POWER_ASSERT_DISABLED=1
    return 0
  fi
  caf=""
  if [ "${GENSEO_POWER_ASSERT_TEST:-0}" = 1 ] && [ -n "${GENSEO_CAFFEINATE:-}" ]; then
    caf=$GENSEO_CAFFEINATE
  else
    caf=$(command -v caffeinate 2>/dev/null || true)
  fi
  if [ -z "$caf" ] || [ ! -x "$caf" ]; then
    return 0
  fi
  if ! command -v perl >/dev/null 2>&1; then
    return 0
  fi
  cpid=$(genseo_power_assert_spawn "$caf" -i -s -w "$$" 2>/dev/null || true)
  case "$cpid" in
    ''|*[!0-9]*) return 0 ;;
  esac
  if kill -0 "$cpid" 2>/dev/null; then
    export GENSEO_POWER_ASSERTED=1
    export GENSEO_POWER_ASSERT_PID=$cpid
    return 0
  fi
  export GENSEO_POWER_ASSERT_DIED=1
  return 0
}

# One log line, after say() exists. Safe to call again after a re-exec.
genseo_power_assert_note() {
  local pid=""
  if [ "${GENSEO_POWER_ASSERT_LOGGED:-}" = 1 ]; then
    return 0
  fi
  export GENSEO_POWER_ASSERT_LOGGED=1
  if ! declare -F say >/dev/null 2>&1; then
    export GENSEO_POWER_ASSERT_LOGGED=0
    return 0
  fi
  if [ "${GENSEO_POWER_ASSERT_DISABLED:-}" = 1 ]; then
    say "power assertion: disabled — continuing"
    return 0
  fi
  pid=${GENSEO_POWER_ASSERT_PID:-}
  if [ "${GENSEO_POWER_ASSERTED:-}" = 1 ] && [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    say "power assertion: caffeinate -i -s -w $$ (holder $pid; idle sleep, and system sleep on AC)"
    return 0
  fi
  if [ "${GENSEO_POWER_ASSERTED:-}" = 1 ] || [ "${GENSEO_POWER_ASSERT_DIED:-}" = 1 ]; then
    say "power assertion: caffeinate -i -s -w $$ did not stay up — continuing"
    return 0
  fi
  say "power assertion: not held (caffeinate missing) — continuing"
  return 0
}

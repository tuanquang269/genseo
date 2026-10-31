#!/bin/bash
# After a successful origin/main sync, make the Mac match this checkout.
#
# Sourced by deploy/grokbot-genseo-daily.sh and scripts/run_landing_daily.sh
# once GENSEO_MAIN_SYNCED=1 (fast-forward, or already up to date). Bash 3.2
# safe. Do not enable set -e here. Does not publish, push, or start a run.
#
# Wrapper: cmp ~/bin/grokbot-genseo-daily.sh to deploy/grokbot-genseo-daily.sh.
# Same bytes and executable: leave it. Different: scripts/install_mac_daily_wrapper.sh.
# That installer does not start launchd. A failure is logged and the run continues.
#
# Plists: pick the repo file for this host. MacBook uses
# deploy/com.pati.genseo-daily.macbook.plist and
# deploy/com.pati.genseo-landing.macbook.plist. Mini uses
# deploy/com.pati.genseo-landing.mini.plist. There is no Mini article plist
# until an explicit failover-release, so a Mini never receives the MacBook
# article agent from here. Host: GENSEO_HOST_KIND=macbook|mini if set,
# otherwise the machine name (Kevins-Mac-mini-2, anything with "mini" or
# "macbook"), then hw.model Macmini* / MacBook*, then system_profiler
# "Model Name". A tie or an unknown machine changes no plist.
#
# An installed LaunchAgent that is not on disk is not created. A plist whose
# bytes already match the repo, and that this script has loaded before, is
# left alone. The load record is a copy under
# ~/Library/LaunchAgents/.genseo-self-apply/, not a git path.
#
# The label of the job that is running is never bootout'd in this process.
# launchd would kill that job. The new bytes are copied now. A detached
# helper (its own session, same idea as scripts/genseo_power_assert.sh) waits
# until this PID has exited, then bootout + bootstrap. RunAtLoad must be
# false. The helper does not kickstart and does not execute either wrapper.
# The other label is reloaded immediately only when that lane's lock is free
# and no job for it is in the process list. If reload fails, the previous
# plist is put back and, when this script had unloaded the label, bootstrapped
# again. The article or landing run keeps going either way.
#
# Test hooks are ignored unless GENSEO_SELF_APPLY_TEST=1:
#   GENSEO_LAUNCHCTL              executable used instead of launchctl
#   GENSEO_SELF_APPLY_HOSTNAME    machine name, instead of hostname/scutil
#   GENSEO_HOST_MODEL             hw.model, instead of sysctl
#   GENSEO_SELF_APPLY_POLL_SEC    helper wait interval (default 2)
#   GENSEO_SELF_APPLY_SETTLE_SEC  pause after the job exits (default 1)
# GENSEO_SELF_APPLY_DISABLE=1 logs and returns without copying.
# GENSEO_SYNC_DRY_RUN=1 logs and returns without copying.
#
# Offline: bash tests/test_self_apply.sh

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  case "${1:-}" in
    --reload-after) ;;
    *)
      printf '%s\n' "source scripts/genseo_self_apply.sh from a daily wrapper; it does not publish or start launchd." >&2
      exit 2
      ;;
  esac
fi

genseo_self_apply_queued=""

genseo_self_apply_note() {
  local line=""
  line="[$(date '+%F %T')] $*"
  if declare -F say >/dev/null 2>&1; then
    say "$*"
  else
    printf '%s\n' "$line"
  fi
  if [ "${GENSEO_SELF_APPLY_NOTE_NOFILE:-}" = 1 ]; then
    return 0
  fi
  if [ -n "${GENSEO_SELF_APPLY_LOG:-}" ]; then
    printf '%s\n' "$line" >> "$GENSEO_SELF_APPLY_LOG" 2>/dev/null || true
  fi
  return 0
}

genseo_self_apply_detail() {
  local line=""
  line="[$(date '+%F %T')] $*"
  if [ -n "${GENSEO_SELF_APPLY_LOG:-}" ]; then
    printf '%s\n' "$line" >> "$GENSEO_SELF_APPLY_LOG" 2>/dev/null || true
  fi
  return 0
}

genseo_self_apply_append_file() {
  local prefix=$1 file=$2 n=0 line=""
  [ -f "$file" ] || return 0
  while IFS= read -r line || [ -n "$line" ]; do
    [ -n "$line" ] || continue
    n=$((n + 1))
    [ "$n" -le 40 ] || break
    genseo_self_apply_detail "$prefix: $line"
  done < "$file"
  return 0
}

# 0 when this process may copy into ~/bin and ~/Library. Linux CI sets the test flag.
genseo_self_apply_on_mac() {
  if [ "${GENSEO_SELF_APPLY_TEST:-0}" = 1 ]; then
    return 0
  fi
  if [ "$(uname -s 2>/dev/null || true)" = "Darwin" ]; then
    return 0
  fi
  return 1
}

genseo_self_apply_lower() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

# Prints macbook or mini. Returns 1 when the machine is unknown or the signals disagree.
genseo_self_apply_host_kind() {
  local explicit="" name="" low="" from_name="" from_model="" model="" prof="" model_name=""
  explicit=${GENSEO_HOST_KIND:-}
  case "$explicit" in
    macbook|mini)
      printf '%s\n' "$explicit"
      return 0
      ;;
    "") ;;
    *) return 1 ;;
  esac
  if [ "${GENSEO_SELF_APPLY_TEST:-0}" = 1 ]; then
    if [ -n "${GENSEO_SELF_APPLY_HOSTNAME:-}" ]; then
      low=$(genseo_self_apply_lower "$GENSEO_SELF_APPLY_HOSTNAME")
      case "$low" in
        *mini*) from_name=mini ;;
        *macbook*) from_name=macbook ;;
      esac
    fi
    model=${GENSEO_HOST_MODEL:-}
  else
    while IFS= read -r name; do
      [ -n "$name" ] || continue
      low=$(genseo_self_apply_lower "$name")
      case "$low" in
        *mini*)
          if [ "$from_name" = "macbook" ]; then
            return 1
          fi
          from_name=mini
          ;;
        *macbook*)
          if [ "$from_name" = "mini" ]; then
            return 1
          fi
          from_name=macbook
          ;;
      esac
    done <<EOF
$(hostname -s 2>/dev/null || true)
$(hostname 2>/dev/null || true)
$( [ -x /usr/sbin/scutil ] && /usr/sbin/scutil --get ComputerName 2>/dev/null || true )
$( [ -x /usr/sbin/scutil ] && /usr/sbin/scutil --get LocalHostName 2>/dev/null || true )
EOF
    if command -v sysctl >/dev/null 2>&1; then
      model=$(sysctl -n hw.model 2>/dev/null || true)
    fi
  fi
  case "$model" in
    Macmini*|MacMini*) from_model=mini ;;
    MacBook*|Macbook*) from_model=macbook ;;
  esac
  if [ -n "$from_name" ] && [ -n "$from_model" ] && [ "$from_name" != "$from_model" ]; then
    return 1
  fi
  if [ -n "$from_name" ]; then
    printf '%s\n' "$from_name"
    return 0
  fi
  if [ -n "$from_model" ]; then
    printf '%s\n' "$from_model"
    return 0
  fi
  if [ "${GENSEO_SELF_APPLY_TEST:-0}" = 1 ]; then
    return 1
  fi
  if ! command -v system_profiler >/dev/null 2>&1; then
    return 1
  fi
  prof=$(perl -e 'alarm 8; exec @ARGV' system_profiler SPHardwareDataType 2>/dev/null || true)
  model_name=$(printf '%s\n' "$prof" | awk -F: '/Model Name/ { gsub(/^[[:space:]]+/, "", $2); print $2; exit }')
  case "$model_name" in
    *"Mac mini"*) printf '%s\n' mini; return 0 ;;
    *MacBook*) printf '%s\n' macbook; return 0 ;;
  esac
  return 1
}

genseo_self_apply_label() {
  case "$1" in
    daily) printf '%s\n' "com.pati.genseo-daily" ;;
    landing) printf '%s\n' "com.pati.genseo-landing" ;;
    *) return 1 ;;
  esac
}

# Repo-relative plist for this host and lane. Empty for the Mini article lane.
genseo_self_apply_rel() {
  case "$1:$2" in
    macbook:daily) printf '%s\n' "deploy/com.pati.genseo-daily.macbook.plist" ;;
    macbook:landing) printf '%s\n' "deploy/com.pati.genseo-landing.macbook.plist" ;;
    mini:landing) printf '%s\n' "deploy/com.pati.genseo-landing.mini.plist" ;;
    mini:daily) return 0 ;;
    *) return 1 ;;
  esac
}

# 0 when the plist is safe to hand to launchctl. RunAtLoad must be false so
# bootstrap does not start a job. KeepAlive must not be set.
genseo_self_apply_plist_safe() {
  local file=$1 label=$2 py="" rc=0
  if [ -x /usr/bin/python3 ]; then
    py=/usr/bin/python3
  elif command -v python3 >/dev/null 2>&1; then
    py=$(command -v python3)
  else
    return 2
  fi
  "$py" - "$file" "$label" <<'PY'
import plistlib
import sys

path, label = sys.argv[1], sys.argv[2]
try:
    with open(path, "rb") as fh:
        data = plistlib.load(fh)
except Exception:
    sys.exit(2)
if data.get("Label") != label:
    sys.exit(3)
if data.get("RunAtLoad") is not False:
    sys.exit(4)
if data.get("KeepAlive") not in (None, False):
    sys.exit(5)
args = data.get("ProgramArguments")
if not isinstance(args, list) or not args:
    sys.exit(6)
blob = " ".join(str(item) for item in args)
for bad in ("kickstart", "--live", "shopify_publisher", "landing_publisher"):
    if bad in blob:
        sys.exit(7)
for item in args:
    if str(item) == "launchctl":
        sys.exit(7)
sys.exit(0)
PY
  rc=$?
  if [ "$rc" != 0 ]; then
    return "$rc"
  fi
  if [ "${GENSEO_SELF_APPLY_TEST:-0}" != 1 ]; then
    if [ -z "${HOME:-}" ] || ! grep -F -q -- "$HOME" "$file"; then
      return 8
    fi
  fi
  return 0
}

genseo_self_apply_pid_alive() {
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

genseo_self_apply_trim() {
  local s=$1
  s=${s//$'\r'/}
  printf '%s' "$s"
}

# 0 when the command is a GenSeo job for this lane, not vim/cp/grep.
genseo_self_apply_cmd_is_lane() {
  local lane=$1 cmd=$2 first="" rest="" token=""
  cmd="${cmd#"${cmd%%[![:space:]]*}"}"
  [ -n "$cmd" ] || return 1
  case "$lane" in
    daily)
      case "$cmd" in
        *grokbot-genseo-daily*|*run_ticket_headless*) ;;
        *) return 1 ;;
      esac
      ;;
    landing)
      case "$cmd" in
        *run_landing_daily*|*run_landing_headless*) ;;
        *) return 1 ;;
      esac
      ;;
    *) return 1 ;;
  esac
  first=${cmd%% *}
  rest=${cmd#"$first"}
  rest=${rest#" "}
  token=${first##*/}
  case "$token" in
    bash|sh|caffeinate) ;;
    grokbot-genseo-daily|grokbot-genseo-daily.sh|run_ticket_headless.sh)
      [ "$lane" = daily ] && return 0
      return 1
      ;;
    run_landing_daily|run_landing_daily.sh|run_landing_headless.sh)
      [ "$lane" = landing ] && return 0
      return 1
      ;;
    *) return 1 ;;
  esac
  case "$lane" in
    daily)
      case "$rest" in
        *grokbot-genseo-daily*|*run_ticket_headless*) return 0 ;;
      esac
      ;;
    landing)
      case "$rest" in
        *run_landing_daily*|*run_landing_headless*) return 0 ;;
      esac
      ;;
  esac
  return 1
}

# 0 when a live process for this lane is visible. 2 when ps cannot be read.
genseo_self_apply_job_running() {
  local lane=$1 tmp="" pid="" cmd="" saw=1
  tmp=$(mktemp "${TMPDIR:-/tmp}/genseo-self-apply-ps.XXXXXX") || return 2
  if [ "${GENSEO_SELF_APPLY_TEST:-0}" = 1 ] && [ -n "${GENSEO_SELF_APPLY_PS:-}" ]; then
    if [ -x "$GENSEO_SELF_APPLY_PS" ] && "$GENSEO_SELF_APPLY_PS" >"$tmp" 2>/dev/null; then
      saw=0
    fi
  elif ps -axww -o pid=,args= >"$tmp" 2>/dev/null; then
    saw=0
  elif ps -eo pid=,args= >"$tmp" 2>/dev/null; then
    saw=0
  fi
  if [ "$saw" != 0 ]; then
    rm -f "$tmp"
    return 2
  fi
  while read -r pid cmd; do
    case "$pid" in
      ''|*[!0-9]*) continue ;;
    esac
    [ "$pid" = "$$" ] && continue
    genseo_self_apply_cmd_is_lane "$lane" "$cmd" || continue
    genseo_self_apply_pid_alive "$pid" || continue
    rm -f "$tmp"
    return 0
  done <"$tmp"
  rm -f "$tmp"
  return 1
}

# 0 when this lane must not be bootout'd. Sets genseo_self_apply_busy_reason.
genseo_self_apply_lane_busy() {
  local lane=$1 repo=$2 lock="" pidfile="" pid="" job_rc=1
  genseo_self_apply_busy_reason=""
  case "$lane" in
    daily)
      lock="$repo/state/daily.lock"
      pidfile="$lock/pid"
      ;;
    landing)
      lock="$repo/state/landing-daily.lock"
      pidfile="${lock}.owner"
      ;;
    *)
      genseo_self_apply_busy_reason="unknown lane"
      return 0
      ;;
  esac
  if [ -d "$lock" ]; then
    pid=""
    if [ -f "$pidfile" ]; then
      IFS= read -r pid <"$pidfile" || pid=""
      pid=$(genseo_self_apply_trim "$pid")
    fi
    if genseo_self_apply_pid_alive "$pid"; then
      if [ "$pid" = "$$" ]; then
        genseo_self_apply_busy_reason="this process holds the lane lock"
      else
        genseo_self_apply_busy_reason="lock held"
      fi
      return 0
    elif [ ! -f "$pidfile" ]; then
      genseo_self_apply_busy_reason="lock held"
      return 0
    fi
  fi
  genseo_self_apply_job_running "$lane"
  job_rc=$?
  if [ "$job_rc" = 0 ]; then
    genseo_self_apply_busy_reason="a job is running"
    return 0
  fi
  if [ "$job_rc" = 2 ]; then
    genseo_self_apply_busy_reason="process list unreadable"
    return 0
  fi
  return 1
}

genseo_self_apply_launchctl_bin() {
  if [ "${GENSEO_SELF_APPLY_TEST:-0}" = 1 ] && [ -n "${GENSEO_LAUNCHCTL:-}" ]; then
    if [ -x "$GENSEO_LAUNCHCTL" ]; then
      printf '%s\n' "$GENSEO_LAUNCHCTL"
      return 0
    fi
    return 1
  fi
  if [ -x /bin/launchctl ]; then
    printf '%s\n' /bin/launchctl
    return 0
  fi
  command -v launchctl 2>/dev/null || return 1
}

# 0 when launchctl print says this label is executing.
genseo_self_apply_launchd_running() {
  local bin=$1 domain=$2 label=$3 out=""
  out=$("$bin" print "$domain/$label" 2>/dev/null || true)
  printf '%s\n' "$out" | awk '$1 == "state" && $2 == "=" && $3 == "running" { found=1 } END { exit (found ? 0 : 1) }'
}

# bootout + bootstrap of one installed plist. Does not start the job.
# On bootstrap failure, puts the backup bytes back. Bootstraps that backup
# only if bootout had unloaded a label that was already loaded.
genseo_self_apply_perform_reload() {
  local label=$1 plist=$2 backup=$3 loaded=$4 lane=$5 repo=$6
  local bin="" uid="" domain="" boot_rc=0 bs_rc=0 safe_rc=0
  if [ ! -f "$plist" ] || [ -L "$plist" ]; then
    genseo_self_apply_note "self-apply: $label reload skipped — installed plist missing"
    return 0
  fi
  safe_rc=0
  genseo_self_apply_plist_safe "$plist" "$label" || safe_rc=$?
  if [ "$safe_rc" != 0 ]; then
    genseo_self_apply_note "self-apply: $label reload skipped — installed plist refused (rc $safe_rc) — continuing on the current setup"
    return 0
  fi
  uid=$(id -u 2>/dev/null || true)
  case "$uid" in
    ''|*[!0-9]*)
      genseo_self_apply_note "self-apply: $label reload failed — uid unreadable — continuing on the current setup"
      return 0
      ;;
  esac
  if genseo_self_apply_lane_busy "$lane" "$repo"; then
    genseo_self_apply_note "self-apply: $label reload skipped — ${genseo_self_apply_busy_reason:-lane busy}"
    return 0
  fi
  bin=$(genseo_self_apply_launchctl_bin || true)
  if [ -z "$bin" ]; then
    genseo_self_apply_note "self-apply: launchctl missing — $label not reloaded — continuing on the current setup"
    return 0
  fi
  domain="gui/$uid"
  if genseo_self_apply_launchd_running "$bin" "$domain" "$label"; then
    genseo_self_apply_note "self-apply: $label reload skipped — launchd reports it running"
    return 0
  fi
  boot_rc=0
  "$bin" bootout "$domain" "$plist" >/dev/null 2>&1 || boot_rc=$?
  bs_rc=0
  "$bin" bootstrap "$domain" "$plist" >/dev/null 2>&1 || bs_rc=$?
  if [ "$bs_rc" = 0 ]; then
    mkdir -p "$(dirname "$loaded")" 2>/dev/null || true
    if cp "$plist" "$loaded" 2>/dev/null; then
      genseo_self_apply_note "self-apply: $label reloaded"
    else
      genseo_self_apply_note "self-apply: $label reloaded — load record was not written"
    fi
    return 0
  fi
  if [ -f "$backup" ] && [ ! -L "$backup" ]; then
    cp "$backup" "$plist" 2>/dev/null || true
  fi
  if [ "$boot_rc" = 0 ]; then
    "$bin" bootout "$domain" "$plist" >/dev/null 2>&1 || true
    if "$bin" bootstrap "$domain" "$plist" >/dev/null 2>&1; then
      genseo_self_apply_note "self-apply: $label reload failed — restored the previous plist — continuing on the previous launchd setup"
    else
      genseo_self_apply_note "self-apply: $label reload failed — restore bootstrap also failed — label may be unloaded"
    fi
  else
    genseo_self_apply_note "self-apply: $label reload failed — launchd was not switched — continuing on the previous launchd setup"
  fi
  return 0
}

# 0 while pid still looks like the lane job we are waiting on.
# ps without -ww truncates the command. The script name is at the end, so a
# truncated line would look like some other process and this helper would
# stop waiting while the job is still alive. Wide ps keeps the name.
genseo_self_apply_pid_is_job() {
  local pid=$1 lane=$2 cmd=""
  genseo_self_apply_pid_alive "$pid" || return 1
  cmd=$(ps -ww -p "$pid" -o args= 2>/dev/null || true)
  if [ -z "$cmd" ]; then
    cmd=$(ps -p "$pid" -o args= 2>/dev/null || true)
  fi
  if [ -z "$cmd" ]; then
    return 0
  fi
  genseo_self_apply_cmd_is_lane "$lane" "$cmd"
}

genseo_self_apply_spawn() {
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
    my $log = $ENV{GENSEO_SELF_APPLY_LOG} || "";
    open STDIN, "<", "/dev/null";
    if ($log ne "" && open my $fh, ">>", $log) {
      open STDOUT, ">>&", $fh;
      open STDERR, ">>&", $fh;
    } else {
      open STDOUT, ">", "/dev/null";
      open STDERR, ">", "/dev/null";
    }
    exec @ARGV or exit 1;
  ' "$@"
}

genseo_self_apply_schedule() {
  local label=$1 plist=$2 backup=$3 loaded=$4 lane=$5 repo=$6
  local copy="" root="" helper_pid="" poll=2 settle=1 deadline=64800
  case " ${genseo_self_apply_queued:-} " in
    *" $label "*)
      genseo_self_apply_note "self-apply: $label reload already queued"
      return 0
      ;;
  esac
  if [ ! -f "${BASH_SOURCE[0]}" ]; then
    genseo_self_apply_note "self-apply: $label reload helper did not start — launchd still has the previous job"
    return 0
  fi
  root=${TMPDIR:-/tmp}
  root=${root%/}
  copy=$(mktemp "$root/genseo-self-apply.XXXXXX") || {
    genseo_self_apply_note "self-apply: $label reload helper did not start — launchd still has the previous job"
    return 0
  }
  if ! cp "${BASH_SOURCE[0]}" "$copy"; then
    rm -f "$copy"
    genseo_self_apply_note "self-apply: $label reload helper did not start — launchd still has the previous job"
    return 0
  fi
  chmod 700 "$copy" || true
  if [ "${GENSEO_SELF_APPLY_TEST:-0}" = 1 ]; then
    case "${GENSEO_SELF_APPLY_POLL_SEC:-}" in
      ''|*[!0-9.]*) ;;
      0|0.0|0.00) ;;
      *) poll=$GENSEO_SELF_APPLY_POLL_SEC ;;
    esac
    case "${GENSEO_SELF_APPLY_SETTLE_SEC:-}" in
      ''|*[!0-9.]*) ;;
      *) settle=$GENSEO_SELF_APPLY_SETTLE_SEC ;;
    esac
    case "${GENSEO_SELF_APPLY_DEADLINE_SEC:-}" in
      ''|*[!0-9]*) ;;
      *) deadline=$GENSEO_SELF_APPLY_DEADLINE_SEC ;;
    esac
  fi
  helper_pid=$(
    GENSEO_SELF_APPLY_LOG="${GENSEO_SELF_APPLY_LOG:-}" \
    genseo_self_apply_spawn \
      /usr/bin/env -i \
      HOME="${HOME:-}" \
      PATH="/usr/bin:/bin:/usr/sbin:/sbin" \
      TMPDIR="${TMPDIR:-/tmp}" \
      GENSEO_SELF_APPLY_LOG="${GENSEO_SELF_APPLY_LOG:-}" \
      GENSEO_SELF_APPLY_NOTE_NOFILE=1 \
      GENSEO_SELF_APPLY_TEST="${GENSEO_SELF_APPLY_TEST:-0}" \
      GENSEO_LAUNCHCTL="${GENSEO_LAUNCHCTL:-}" \
      GENSEO_SELF_APPLY_PS="${GENSEO_SELF_APPLY_PS:-}" \
      GENSEO_SELF_APPLY_PARENT_PID="$$" \
      GENSEO_SELF_APPLY_PLIST="$plist" \
      GENSEO_SELF_APPLY_LABEL="$label" \
      GENSEO_SELF_APPLY_LANE="$lane" \
      GENSEO_SELF_APPLY_BACKUP="$backup" \
      GENSEO_SELF_APPLY_LOADED="$loaded" \
      GENSEO_SELF_APPLY_REPO="$repo" \
      GENSEO_SELF_APPLY_POLL="$poll" \
      GENSEO_SELF_APPLY_SETTLE="$settle" \
      GENSEO_SELF_APPLY_DEADLINE="$deadline" \
      GENSEO_SELF_APPLY_COPY="$copy" \
      /bin/bash "$copy" --reload-after
  ) || helper_pid=""
  case "$helper_pid" in
    ''|*[!0-9]*)
      rm -f "$copy"
      genseo_self_apply_note "self-apply: $label reload helper did not start — launchd still has the previous job"
      return 0
      ;;
  esac
  genseo_self_apply_queued="${genseo_self_apply_queued:-} $label "
  genseo_self_apply_note "self-apply: $label reload deferred until pid $$ exits (helper $helper_pid)"
  return 0
}

genseo_self_apply_install_wrapper() {
  local repo=$1 src="" dest="" installer="" out="" err="" rc=0
  src="$repo/deploy/grokbot-genseo-daily.sh"
  dest="${HOME}/bin/grokbot-genseo-daily.sh"
  installer="$repo/scripts/install_mac_daily_wrapper.sh"
  if [ ! -f "$src" ]; then
    genseo_self_apply_note "self-apply: wrapper source missing — continuing on the current setup"
    return 0
  fi
  if [ -f "$dest" ] && [ ! -L "$dest" ] && [ -x "$dest" ] && cmp -s "$src" "$dest"; then
    genseo_self_apply_note "self-apply: wrapper unchanged"
    return 0
  fi
  if [ ! -f "$installer" ]; then
    genseo_self_apply_note "self-apply: wrapper install failed (installer missing) — continuing on the current setup"
    return 0
  fi
  out=$(mktemp "${TMPDIR:-/tmp}/genseo-self-apply-inst.XXXXXX") || {
    genseo_self_apply_note "self-apply: wrapper install failed (rc 1) — continuing on the current setup"
    return 0
  }
  err=$(mktemp "${TMPDIR:-/tmp}/genseo-self-apply-inst.XXXXXX") || {
    rm -f "$out"
    genseo_self_apply_note "self-apply: wrapper install failed (rc 1) — continuing on the current setup"
    return 0
  }
  rc=0
  env GENSEO_HOME="$repo" /bin/bash "$installer" >"$out" 2>"$err" || rc=$?
  genseo_self_apply_append_file "wrapper-install" "$out"
  genseo_self_apply_append_file "wrapper-install-err" "$err"
  rm -f "$out" "$err"
  if [ "$rc" != 0 ]; then
    genseo_self_apply_note "self-apply: wrapper install failed (rc $rc) — continuing on the current setup"
    return 0
  fi
  if [ ! -f "$dest" ] || [ -L "$dest" ] || [ ! -x "$dest" ] || ! cmp -s "$src" "$dest"; then
    genseo_self_apply_note "self-apply: wrapper install failed (mismatch) — continuing on the current setup"
    return 0
  fi
  genseo_self_apply_note "self-apply: wrapper installed"
  return 0
}

genseo_self_apply_one_plist() {
  local kind=$1 lane=$2 current=$3 repo=$4
  local label="" rel="" src="" dest="" agents="" stampdir="" loaded="" backup=""
  local src_diff=0 safe_rc=0 tmp=""
  label=$(genseo_self_apply_label "$lane" || true)
  [ -n "$label" ] || return 0
  rel=$(genseo_self_apply_rel "$kind" "$lane" || true)
  if [ -z "$rel" ]; then
    genseo_self_apply_note "self-apply: $label skipped — no mini plist until failover-release"
    return 0
  fi
  src="$repo/$rel"
  agents="${HOME}/Library/LaunchAgents"
  dest="$agents/$label.plist"
  if [ ! -f "$src" ]; then
    genseo_self_apply_note "self-apply: $label repo plist missing — not copied"
    return 0
  fi
  safe_rc=0
  genseo_self_apply_plist_safe "$src" "$label" || safe_rc=$?
  if [ "$safe_rc" != 0 ]; then
    genseo_self_apply_note "self-apply: $label repo plist refused (rc $safe_rc) — not copied"
    return 0
  fi
  if [ -L "$dest" ]; then
    genseo_self_apply_note "self-apply: $label installed plist is a symlink — not replaced"
    return 0
  fi
  if [ ! -f "$dest" ]; then
    genseo_self_apply_note "self-apply: $label skipped — not installed"
    return 0
  fi
  stampdir="$agents/.genseo-self-apply"
  loaded="$stampdir/$label.loaded"
  backup="$stampdir/$label.plist.bak"
  src_diff=0
  if ! cmp -s "$src" "$dest"; then
    src_diff=1
  fi
  if [ "$src_diff" = 0 ] && [ -f "$loaded" ] && cmp -s "$dest" "$loaded"; then
    genseo_self_apply_note "self-apply: $label plist unchanged"
    return 0
  fi
  if [ "$label" != "$current" ] && genseo_self_apply_lane_busy "$lane" "$repo"; then
    genseo_self_apply_note "self-apply: $label left in place — ${genseo_self_apply_busy_reason:-that lane is running}"
    return 0
  fi
  if ! mkdir -p "$stampdir"; then
    genseo_self_apply_note "self-apply: $label plist copy failed — continuing on the current setup"
    return 0
  fi
  if [ "$src_diff" = 1 ]; then
    if ! cp "$dest" "$backup"; then
      genseo_self_apply_note "self-apply: $label plist copy failed — continuing on the current setup"
      return 0
    fi
    tmp=$(mktemp "$stampdir/.${label}.XXXXXX") || {
      genseo_self_apply_note "self-apply: $label plist copy failed — continuing on the current setup"
      return 0
    }
    if ! cp "$src" "$tmp"; then
      rm -f "$tmp"
      genseo_self_apply_note "self-apply: $label plist copy failed — continuing on the current setup"
      return 0
    fi
    chmod 644 "$tmp" || true
    if ! cmp -s "$src" "$tmp"; then
      rm -f "$tmp"
      genseo_self_apply_note "self-apply: $label plist copy failed — continuing on the current setup"
      return 0
    fi
    if ! mv -f "$tmp" "$dest"; then
      rm -f "$tmp"
      genseo_self_apply_note "self-apply: $label plist copy failed — continuing on the current setup"
      return 0
    fi
    genseo_self_apply_note "self-apply: $label plist copied from $rel"
  else
    genseo_self_apply_note "self-apply: $label plist bytes match — launchd load unrecorded"
    # A second pass in this same run already saved the pre-change bytes.
    # Copying dest over that backup would make a failed reload restore the
    # new file instead of the one launchd still has.
    if [ ! -f "$backup" ] || cmp -s "$backup" "$dest"; then
      cp "$dest" "$backup" 2>/dev/null || true
    fi
  fi
  if [ "$label" = "$current" ]; then
    genseo_self_apply_schedule "$label" "$dest" "$backup" "$loaded" "$lane" "$repo"
    return 0
  fi
  genseo_self_apply_perform_reload "$label" "$dest" "$backup" "$loaded" "$lane" "$repo"
  return 0
}

# Apply wrapper and plist drift. Always returns 0: a failure must not stop the run.
genseo_self_apply() {
  local current=${1:-} repo="" kind=""
  if [ "${GENSEO_SYNC_DRY_RUN:-}" = 1 ]; then
    genseo_self_apply_note "self-apply: skipped — sync dry-run"
    return 0
  fi
  if [ "${GENSEO_SELF_APPLY_DISABLE:-}" = 1 ]; then
    genseo_self_apply_note "self-apply: disabled — continuing on the current setup"
    return 0
  fi
  if [ -z "${HOME:-}" ] || [ "$HOME" = "/" ]; then
    genseo_self_apply_note "self-apply: HOME is unset — continuing on the current setup"
    return 0
  fi
  if ! genseo_self_apply_on_mac; then
    genseo_self_apply_note "self-apply: skipped — not a Mac"
    return 0
  fi
  repo=${G:-}
  if [ -z "$repo" ]; then
    repo=${HOME}/genseo
  fi
  repo=${repo%/}
  if [ -z "${GENSEO_SELF_APPLY_LOG:-}" ]; then
    GENSEO_SELF_APPLY_LOG="$repo/logs/self-apply.log"
  fi
  export GENSEO_SELF_APPLY_LOG
  if [ -n "$repo" ] && [ "$repo" != "/" ]; then
    mkdir -p "$(dirname "$GENSEO_SELF_APPLY_LOG")" 2>/dev/null || true
  fi
  if [ ! -d "$repo" ]; then
    genseo_self_apply_note "self-apply: checkout missing — continuing on the current setup"
    return 0
  fi
  case "$current" in
    com.pati.genseo-daily|com.pati.genseo-landing) ;;
    *)
      genseo_self_apply_note "self-apply: skipped — unknown current label"
      return 0
      ;;
  esac
  genseo_self_apply_install_wrapper "$repo"
  kind=$(genseo_self_apply_host_kind || true)
  case "$kind" in
    macbook|mini)
      genseo_self_apply_note "self-apply: host $kind"
      ;;
    *)
      genseo_self_apply_note "self-apply: host unrecognized — plist not changed"
      return 0
      ;;
  esac
  genseo_self_apply_one_plist "$kind" daily "$current" "$repo"
  genseo_self_apply_one_plist "$kind" landing "$current" "$repo"
  return 0
}

genseo_self_apply_copy_release() {
  local p=${GENSEO_SELF_APPLY_COPY:-} root=""
  [ -n "$p" ] || return 0
  [ -f "$p" ] || return 0
  root=${TMPDIR:-/tmp}
  root=${root%/}
  case "$p" in
    /tmp/genseo-self-apply.*|"$root"/genseo-self-apply.*) rm -f "$p" ;;
  esac
  return 0
}

genseo_self_apply_wait_and_reload() {
  local pid="" lane="" plist="" backup="" loaded="" repo="" label=""
  local poll=2 settle=1 deadline=64800 start=0 now=0
  pid=${GENSEO_SELF_APPLY_PARENT_PID:-}
  lane=${GENSEO_SELF_APPLY_LANE:-}
  plist=${GENSEO_SELF_APPLY_PLIST:-}
  backup=${GENSEO_SELF_APPLY_BACKUP:-}
  loaded=${GENSEO_SELF_APPLY_LOADED:-}
  repo=${GENSEO_SELF_APPLY_REPO:-}
  label=${GENSEO_SELF_APPLY_LABEL:-}
  poll=${GENSEO_SELF_APPLY_POLL:-2}
  settle=${GENSEO_SELF_APPLY_SETTLE:-1}
  deadline=${GENSEO_SELF_APPLY_DEADLINE:-64800}
  case "$poll" in
    ''|*[!0-9.]*) poll=2 ;;
  esac
  case "$settle" in
    ''|*[!0-9.]*) settle=1 ;;
  esac
  case "$deadline" in
    ''|*[!0-9]*) deadline=64800 ;;
  esac
  G=$repo
  start=$(date +%s)
  while genseo_self_apply_pid_is_job "$pid" "$lane"; do
    now=$(date +%s)
    if [ $((now - start)) -ge "$deadline" ]; then
      genseo_self_apply_note "self-apply: $label reload wait timed out — not reloading while the job may still be running"
      return 0
    fi
    sleep "$poll"
  done
  if [ "$settle" != 0 ] && [ "$settle" != 0.0 ]; then
    sleep "$settle"
  fi
  genseo_self_apply_perform_reload "$label" "$plist" "$backup" "$loaded" "$lane" "$repo"
  return 0
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  case "${1:-}" in
    --reload-after)
      trap 'genseo_self_apply_copy_release' EXIT
      genseo_self_apply_wait_and_reload
      exit 0
      ;;
  esac
fi

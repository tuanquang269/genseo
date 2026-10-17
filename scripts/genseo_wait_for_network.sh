#!/bin/bash
# Wait until DNS resolves the storefront and the Shopify admin host.
#
# 2026-10-16 08:51 ICT: launchd ran the missed article and landing slots when
# the Mac woke. The article feed retry is 3 x 5s and genseo_published_today.py
# returns -1 as soon as DNS fails. The landing guard calls Shopify once and
# fail-closes. Neither plist waits for a network. This wait sits in front of
# those reads.
# 2026-10-17 07:38 ICT: a dark wake started before DNS was up (down until
# 07:39, about a minute). That gap is inside the default 600s budget. The
# sleep in this loop is idle time. The daily wrappers arm caffeinate before
# calling this function so pmset "sleep 1" cannot suspend the Mac during the
# backoff. This function does not take that assertion itself.
#
# Sourced by deploy/grokbot-genseo-daily.sh and scripts/run_landing_daily.sh.
# Bash 3.2 safe. Do not enable set -e here. Does not publish and does not
# read the atom feed or the Admin API.
#
# GENSEO_NET_WAIT_MAX_SEC          default 600, cap 600. 0 skips the wait.
# GENSEO_NET_WAIT_BACKOFF_SEC      default 5, cap 60. 0 is a legal test value.
# GENSEO_NET_WAIT_BACKOFF_CAP_SEC  default 60, cap 60.
# GENSEO_DNS_TIMEOUT_SEC           default 5, cap 30. One lookup.
# GENSEO_SHOPIFY_ADMIN_HOST        default wellnessnest1.myshopify.com
# GENSEO_NET_HOSTS                 space-separated override of the full list.
# Test hooks are ignored unless GENSEO_NET_WAIT_TEST=1:
#   GENSEO_DNS_RESOLVE    executable; arg is the host; exit 0 means resolved
#   GENSEO_NET_NOW_CMD    executable; prints integer monotonic seconds
#   GENSEO_NET_SLEEP_CMD  executable; arg is the seconds to wait
#
# Resolver: /usr/bin/python3 socket.getaddrinfo (the system resolver). dig is
# not on the stock macOS launchd PATH. dscacheutil and scutil -r are the other
# on-box tools; python is already required by both wrappers and is what the
# Linux tests run. Each lookup is capped so a blackholed resolver cannot spend
# the whole budget inside one call.
#
# Budget clock: time.clock_gettime(CLOCK_MONOTONIC) from each python3 process.
# That clock is system-wide (seconds since boot on Linux and macOS), so the
# samples are comparable. Apple Python 3.9 time.monotonic() is
# mach_absolute_time() minus the interpreter start, so every new process
# prints ~0, elapsed time never reaches this budget, and a DNS-down wait
# exits only on the stall>500 guard (hours) while state/daily.lock is held.
# If no monotonic API is available, the fallback is /proc/uptime (the same
# Linux clock, still cross-process) and only then time.time(). Wall time is
# not the primary clock: NTP can step it backward. The loop already treats a
# backward step as no progress.

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  printf '%s\n' "source scripts/genseo_wait_for_network.sh from a daily wrapper; it does not publish." >&2
  exit 2
fi

genseo_net_note() {
  if declare -F say >/dev/null 2>&1; then
    say "$*"
  else
    printf '%s\n' "$*"
  fi
}

# Print VALUE clamped to CAP. Non-numeric values become DEFAULT. 0 is kept.
genseo_net_clamp() {
  local raw=$1 def=$2 cap=$3 n
  case "$raw" in
    ''|*[!0-9]*) n=$def ;;
    *) n=$((10#$raw)) ;;
  esac
  if [ "$n" -gt "$cap" ]; then
    n=$cap
  fi
  printf '%s\n' "$n"
}

genseo_net_py() {
  if [ -n "${PY:-}" ] && [ -x "$PY" ]; then
    printf '%s\n' "$PY"
    return 0
  fi
  if [ -x /usr/bin/python3 ]; then
    printf '%s\n' /usr/bin/python3
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  return 1
}

genseo_net_hosts() {
  local shop
  if [ -n "${GENSEO_NET_HOSTS:-}" ]; then
    printf '%s\n' "$GENSEO_NET_HOSTS"
    return 0
  fi
  shop="${GENSEO_SHOPIFY_ADMIN_HOST:-wellnessnest1.myshopify.com}"
  printf '%s\n' "wellnessnest.co $shop"
}

# 0 when every character of RAW is a hostname character or a separating space.
genseo_hosts_charset_ok() {
  local raw=$1 i=0 c
  while [ "$i" -lt "${#raw}" ]; do
    c=${raw:$i:1}
    case "$c" in
      [A-Za-z0-9.]|' '|'-') ;;
      *) return 1 ;;
    esac
    i=$((i + 1))
  done
  return 0
}

# 0 when HOST is a single DNS name we are willing to look up.
genseo_host_ok() {
  local host=$1
  case "$host" in
    ''|.*|*.|*..*) return 1 ;;
  esac
  if [ "${#host}" -gt 253 ]; then
    return 1
  fi
  if ! genseo_hosts_charset_ok "$host"; then
    return 1
  fi
  case "$host" in
    *' '*) return 1 ;;
  esac
  return 0
}

genseo_net_now() {
  local out="" py=""
  if [ "${GENSEO_NET_WAIT_TEST:-0}" = 1 ] && [ -n "${GENSEO_NET_NOW_CMD:-}" ]; then
    [ -x "$GENSEO_NET_NOW_CMD" ] || return 1
    out=$("$GENSEO_NET_NOW_CMD") || return 1
  else
    py=$(genseo_net_py) || return 1
    # One process per sample. Do not use time.monotonic(): on Apple Python
    # 3.9 it is process-relative and each sample is ~0. Prefer a raw
    # monotonic clock id (CLOCK_MONOTONIC, then the macOS raw clocks). Those
    # stay on one timeline across processes. Fallback when that API is
    # missing or raises: /proc/uptime (Linux CLOCK_MONOTONIC seconds), then
    # time.time() so a sample still advances across processes.
    out=$("$py" -c 'import time
def n():
    cg = getattr(time, "clock_gettime", None)
    if cg is not None:
        for name in ("CLOCK_MONOTONIC", "CLOCK_MONOTONIC_RAW", "CLOCK_UPTIME_RAW"):
            clk = getattr(time, name, None)
            if clk is None:
                continue
            try:
                return int(cg(clk))
            except OSError:
                continue
    try:
        raw = open("/proc/uptime", "r").read().split()
        return int(float(raw[0]))
    except (OSError, ValueError, IndexError):
        return int(time.time())
print(n())
') || return 1
  fi
  case "$out" in
    ''|*[!0-9]*) return 1 ;;
  esac
  printf '%s\n' "$((10#$out))"
}

genseo_net_sleep() {
  local sec=$1
  case "$sec" in
    ''|*[!0-9]*) return 1 ;;
  esac
  if [ "${GENSEO_NET_WAIT_TEST:-0}" = 1 ] && [ -n "${GENSEO_NET_SLEEP_CMD:-}" ]; then
    [ -x "$GENSEO_NET_SLEEP_CMD" ] || return 1
    "$GENSEO_NET_SLEEP_CMD" "$sec"
    return $?
  fi
  if [ "$sec" -gt 0 ]; then
    sleep "$sec"
  fi
  return 0
}

# 0 when HOST resolves. A test resolver runs only when GENSEO_NET_WAIT_TEST=1.
genseo_dns_resolves() {
  local host=$1 py="" timeout=""
  if [ "${GENSEO_NET_WAIT_TEST:-0}" = 1 ] && [ -n "${GENSEO_DNS_RESOLVE:-}" ]; then
    [ -x "$GENSEO_DNS_RESOLVE" ] || return 1
    "$GENSEO_DNS_RESOLVE" "$host"
    return $?
  fi
  py=$(genseo_net_py) || return 1
  timeout=$(genseo_net_clamp "${GENSEO_DNS_TIMEOUT_SEC:-5}" 5 30)
  if [ "$timeout" -lt 1 ]; then
    timeout=1
  fi
  "$py" -c '
import os, socket, sys, threading
host = sys.argv[1]
try:
    limit = float(sys.argv[2])
except ValueError:
    os._exit(1)
if limit <= 0:
    os._exit(1)
box = []
def work():
    try:
        socket.getaddrinfo(host, 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except Exception:
        box.append(False)
        return
    box.append(True)
t = threading.Thread(target=work, daemon=True)
t.start()
t.join(limit)
if box and box[0]:
    os._exit(0)
os._exit(1)
' "$host" "$timeout"
}

# 0 when every configured name resolves, or when the wait is skipped.
# 1 on timeout, a bad name, or a missing clock. The caller fail-closes.
genseo_wait_for_network() {
  local max="" back="" cap="" hosts="" host="" count=0
  local missing="" now="" start="" deadline="" elapsed="" remain="" step=""
  local py="" stall=0 prev="" backoff=""
  local IFS=' '

  max=$(genseo_net_clamp "${GENSEO_NET_WAIT_MAX_SEC:-600}" 600 600)
  if [ "$max" -eq 0 ]; then
    genseo_net_note "network wait skipped (GENSEO_NET_WAIT_MAX_SEC=0)"
    return 0
  fi

  hosts=$(genseo_net_hosts)
  if ! genseo_hosts_charset_ok "$hosts"; then
    genseo_net_note "network not ready — bad DNS name, fail closed"
    return 1
  fi
  count=0
  for host in $hosts; do
    count=$((count + 1))
    if ! genseo_host_ok "$host"; then
      genseo_net_note "network not ready — bad DNS name, fail closed"
      return 1
    fi
  done
  if [ "$count" -eq 0 ]; then
    genseo_net_note "network not ready — no DNS names configured, fail closed"
    return 1
  fi

  if [ "${GENSEO_NET_WAIT_TEST:-0}" != 1 ] || [ -z "${GENSEO_NET_NOW_CMD:-}" ]; then
    if ! py=$(genseo_net_py); then
      genseo_net_note "network not ready — python3 missing, fail closed"
      return 1
    fi
  fi

  back=$(genseo_net_clamp "${GENSEO_NET_WAIT_BACKOFF_SEC:-5}" 5 60)
  cap=$(genseo_net_clamp "${GENSEO_NET_WAIT_BACKOFF_CAP_SEC:-60}" 60 60)
  if [ "$cap" -lt "$back" ]; then
    back=$cap
  fi
  backoff=$back

  start=$(genseo_net_now) || {
    genseo_net_note "network not ready — clock unreadable, fail closed"
    return 1
  }
  deadline=$((start + max))
  prev=$start
  stall=0

  while :; do
    missing=""
    for host in $hosts; do
      if genseo_dns_resolves "$host"; then
        continue
      fi
      if [ -n "$missing" ]; then
        missing="$missing $host"
      else
        missing=$host
      fi
    done
    if [ -z "$missing" ]; then
      genseo_net_note "network ready ($hosts)"
      return 0
    fi
    now=$(genseo_net_now) || {
      genseo_net_note "network not ready — clock unreadable, fail closed"
      return 1
    }
    # A backoff of 0 must not busy-loop if the clock is stuck. A moving clock
    # resets the stall count, so the 600s budget still applies. The clock has
    # to move across processes. A per-process sample stays at 0 and this
    # guard is the only exit, which holds the daily lock for hours.
    if [ "$now" -le "$prev" ]; then
      stall=$((stall + 1))
    else
      stall=0
    fi
    prev=$now
    if [ "$stall" -gt 500 ]; then
      genseo_net_note "network not ready — timeout after ${max}s (DNS unresolved: $missing), fail closed"
      return 1
    fi
    elapsed=$((now - start))
    if [ "$elapsed" -lt 0 ]; then
      elapsed=0
    fi
    if [ "$now" -ge "$deadline" ]; then
      genseo_net_note "network not ready — timeout after ${elapsed}s (DNS unresolved: $missing), fail closed"
      return 1
    fi
    remain=$((deadline - now))
    step=$backoff
    if [ "$step" -gt "$remain" ]; then
      step=$remain
    fi
    genseo_net_note "network not ready ($missing unresolved) — waiting ${step}s (elapsed ${elapsed}s/${max}s)"
    if ! genseo_net_sleep "$step"; then
      genseo_net_note "network not ready — wait interrupted, fail closed"
      return 1
    fi
    if [ "$backoff" -gt 0 ]; then
      backoff=$((backoff * 2))
      if [ "$backoff" -gt "$cap" ]; then
        backoff=$cap
      fi
    fi
  done
}

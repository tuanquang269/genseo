#!/bin/bash
# Mac Mini failover checklist and installer. Dry-run unless an apply flag is set.
#
#   bash scripts/mac_mini_failover_bootstrap.sh
#   bash scripts/mac_mini_failover_bootstrap.sh --install-worker
#   bash scripts/mac_mini_failover_bootstrap.sh --enable-daily
#
# --install-worker writes ~/Library/LaunchAgents/com.pati.cursor-agent-worker.plist
# (worker name Mac-Mini, binary ~/.local/bin/cursor-agent) and does not load it.
# --enable-daily copies the Mini article and landing plists and runs
# scripts/install_mac_daily_wrapper.sh. It does that only when the primary/failover
# guard says the MacBook is not the active runner.
#
# Guard (docs/FAILOVER.md): read origin/main subjects, do not fetch or push.
# Allow daily plists only when a `failover-release: macbook-pro <epoch>` subject
# is newer than every `failover-heartbeat: macbook-pro <epoch>`. A missing marker
# or a stale heartbeat means the MacBook is still the active runner. Silence is
# not an offline MacBook. Heartbeats are not written by the daily job.
#
# Does not call launchctl, ssh, curl, git fetch, git pull, or git push, and does
# not publish. Listicle launchd stays the unpublished-draft lane.
# --disable-daily removes only LaunchAgent plists that carry the installer
# mark. It does not bootout a loaded job.
# Bash 3.2. Offline: bash tests/test_mac_mini_failover_bootstrap.sh
# GENSEO_FAILOVER_TEST=1 lets the copy run off Darwin (the test only).
set -uo pipefail

DRY=1
SEEN_DRY=0
REQ_WORKER=0
REQ_DAILY=0
REQ_DISABLE=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) SEEN_DRY=1 ;;
    --install-worker) REQ_WORKER=1 ;;
    --enable-daily) REQ_DAILY=1 ;;
    --disable-daily) REQ_DISABLE=1 ;;
    -h|--help)
      cat <<'EOF'
usage: bash scripts/mac_mini_failover_bootstrap.sh [--dry-run] [--install-worker] [--enable-daily] [--disable-daily]

Dry-run is the default. --dry-run wins when it is combined with an apply flag.
--install-worker renders the Cursor worker LaunchAgent (name Mac-Mini) and writes it
under ~/Library/LaunchAgents. It does not load launchd and does not install the
daily article or landing plists.
--enable-daily installs those two plists only when a failover-release subject on
the heartbeat ref is newer than every failover-heartbeat for the MacBook. A stale
or missing heartbeat does not authorize it. The script then runs
install_mac_daily_wrapper.sh. It does not call launchctl and it does not publish.
Listicle jobs stay unpublished drafts.
--disable-daily removes those two plists only when they contain this installer's
mark. It does not remove the worker plist, call launchctl, or publish.
--enable-daily and --disable-daily together are refused.

Env (names only in the checklist; values are never printed):
  GENSEO_HOME                         default ~/genseo
  CURSOR_AGENT_BIN                    default ~/.local/bin/cursor-agent
  GROK_BIN                            default ~/.grok/bin/grok
  GENSEO_WORKER_NAME                  default Mac-Mini
  GENSEO_FAILOVER_PRIMARY_HOST        default macbook-pro
  GENSEO_FAILOVER_HEARTBEAT_REF       default origin/main
  GENSEO_CONFIG                       Shopify token json (presence only)
EOF
      exit 0
      ;;
    *)
      printf '%s\n' "unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

if [ "$REQ_DAILY" = 1 ] && [ "$REQ_DISABLE" = 1 ]; then
  printf '%s\n' "--enable-daily and --disable-daily together are refused" >&2
  exit 2
fi

if [ "$REQ_WORKER" = 0 ] && [ "$REQ_DAILY" = 0 ] && [ "$REQ_DISABLE" = 0 ]; then
  DRY=1
elif [ "$SEEN_DRY" = 1 ]; then
  DRY=1
else
  DRY=0
fi

die() { printf '%s\n' "$*" >&2; exit 1; }
usage_err() { printf '%s\n' "$*" >&2; exit 2; }

if [ -z "${HOME:-}" ]; then
  die "HOME is unset"
fi
case "$HOME" in
  *[!A-Za-z0-9/._-]*) die "HOME has characters this installer will not write into a plist" ;;
esac

ROOT=$(cd "$(dirname "$0")/.." && pwd -P)
ROOT=${ROOT%/}
GENSEO_HOME=${GENSEO_HOME:-$HOME/genseo}
GENSEO_HOME=${GENSEO_HOME%/}
CURSOR_AGENT_BIN=${CURSOR_AGENT_BIN:-$HOME/.local/bin/cursor-agent}
GROK_BIN=${GROK_BIN:-$HOME/.grok/bin/grok}
GENSEO_WORKER_NAME=${GENSEO_WORKER_NAME:-Mac-Mini}
GENSEO_FAILOVER_PRIMARY_HOST=${GENSEO_FAILOVER_PRIMARY_HOST:-macbook-pro}
GENSEO_FAILOVER_HEARTBEAT_REF=${GENSEO_FAILOVER_HEARTBEAT_REF:-origin/main}
TOKEN_FILE=${GENSEO_CONFIG:-$HOME/.genseo/shopify_token.json}
case "$TOKEN_FILE" in
  "~/"*) TOKEN_FILE="$HOME/${TOKEN_FILE#~/}" ;;
esac

case "$GENSEO_FAILOVER_PRIMARY_HOST" in
  *[!a-z0-9-]*|"") usage_err "GENSEO_FAILOVER_PRIMARY_HOST must be a lowercase host token" ;;
esac
case "$GENSEO_FAILOVER_HEARTBEAT_REF" in
  ""|-*|*[!A-Za-z0-9/_.-]*) usage_err "GENSEO_FAILOVER_HEARTBEAT_REF must be a git revision, not an option" ;;
esac
# git -C does not override these. A parent that exported them would let the
# guard read a different repository than GENSEO_HOME.
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE

export PATH="$HOME/.local/bin:$HOME/.grok/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin${PATH:+:$PATH}"
PY=/usr/bin/python3
if [ ! -x "$PY" ]; then
  PY=python3
fi

WORKER_TEMPLATE="$ROOT/deploy/com.pati.cursor-agent-worker.plist"
DAILY_TEMPLATE="$ROOT/deploy/com.pati.genseo-daily.mini.plist"
LANDING_TEMPLATE="$ROOT/deploy/com.pati.genseo-landing.mini.plist"
AGENT_DIR="$HOME/Library/LaunchAgents"
WORKER_DEST="$AGENT_DIR/com.pati.cursor-agent-worker.plist"
DAILY_DEST="$AGENT_DIR/com.pati.genseo-daily.plist"
LANDING_DEST="$AGENT_DIR/com.pati.genseo-landing.plist"
LOG_DIR="$HOME/Library/Logs"
ENV_FILE="$GENSEO_HOME/.env"
INSTALL_MARK="installed-by: mac_mini_failover_bootstrap"
# Epochs further ahead than this are ignored. A heartbeat between this skew
# and NONSENSE_AHEAD still fail-closes. A stale heartbeat never authorizes.
GUARD_SKEW=3600
GUARD_NONSENSE_AHEAD=604800
VAULT_ENV="$HOME/PATI/LLM-Wiki/.env"

TMP_PLIST=""
cleanup() {
  if [ -n "$TMP_PLIST" ] && [ -f "$TMP_PLIST" ]; then
    rm -f "$TMP_PLIST"
  fi
}
trap cleanup EXIT

on_mac=0
if [ "$(uname -s)" = "Darwin" ]; then
  on_mac=1
fi
TEST_MODE=0
if [ "${GENSEO_FAILOVER_TEST:-0}" = "1" ]; then
  TEST_MODE=1
fi

plist_safe() {
  case "$1" in
    ''|*[!A-Za-z0-9/._-]*) return 1 ;;
  esac
  case "$1" in
    *__CURSOR_AGENT_BIN__*|*__WORKER_NAME__*|*__GENSEO_HOME__*|*__HOME__*) return 1 ;;
  esac
  return 0
}

name_safe() {
  case "$1" in
    [A-Za-z0-9]*) ;;
    *) return 1 ;;
  esac
  case "$1" in
    *[!A-Za-z0-9._-]*) return 1 ;;
  esac
  if [ "${#1}" -gt 64 ]; then
    return 1
  fi
  return 0
}

# Prints present, MISSING, or unreadable. Never prints the value.
# shopify: last assignment in the file, the way shopify_app_token.py loads .env.
# vault: first ^(export )?KEY= line, the way genseo_model_lane.sh loads the vault.
env_key_status() {
  local mode="$1" file="$2" key="$3" rc
  if [ ! -e "$file" ]; then
    printf '%s\n' MISSING
    return 0
  fi
  if [ ! -f "$file" ] || [ ! -r "$file" ]; then
    printf '%s\n' unreadable
    return 0
  fi
  "$PY" - "$mode" "$file" "$key" <<'PY'
import re, sys
mode, path, key = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    lines = open(path).read().splitlines()
except Exception:
    sys.exit(2)
if mode == "shopify":
    found = False
    val = ""
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() != key:
            continue
        found = True
        val = v.strip().strip('"').strip("'")
    sys.exit(0 if found and val else 1)
if mode == "vault":
    pat = re.compile(r"^(export )?" + re.escape(key) + r"=(.*)$")
    for raw in lines:
        match = pat.match(raw.rstrip("\r"))
        if not match:
            continue
        val = match.group(2)
        if val[:1] in ("'", '"'):
            val = val[1:]
        if val[-1:] in ("'", '"'):
            val = val[:-1]
        sys.exit(0 if val else 1)
    sys.exit(1)
sys.exit(2)
PY
  rc=$?
  case "$rc" in
    0) printf '%s\n' present ;;
    1) printf '%s\n' MISSING ;;
    *) printf '%s\n' unreadable ;;
  esac
}

derive_shopify_keys() {
  local src="$ROOT/scripts/shopify_app_token.py"
  if [ ! -f "$src" ]; then
    return 0
  fi
  grep -oE 'e\["SHOPIFY_CLI_APP_[A-Z0-9_]+"\]' "$src" 2>/dev/null \
    | sed -E 's/^e\["//; s/"\]$//' \
    | sort -u || true
}

derive_vault_keys() {
  local src="$ROOT/scripts/genseo_model_lane.sh"
  if [ ! -f "$src" ]; then
    return 0
  fi
  if grep -q 'PATI/LLM-Wiki/.env' "$src" && grep -q 'NINE_ROUTER_KEY=' "$src"; then
    printf '%s\n' 'NINE_ROUTER_KEY'
  fi
}

token_status() {
  local rc
  if [ ! -e "$TOKEN_FILE" ]; then
    printf '%s\n' MISSING
    return 0
  fi
  if [ ! -f "$TOKEN_FILE" ] || [ ! -r "$TOKEN_FILE" ]; then
    printf '%s\n' unreadable
    return 0
  fi
  "$PY" - "$TOKEN_FILE" <<'PY'
import json, sys
path = sys.argv[1]
try:
    data = json.load(open(path))
except Exception:
    sys.exit(2)
if not isinstance(data, dict):
    sys.exit(2)

def real(value):
    if value is None or value == "":
        return False
    text = str(value)
    if text.startswith("your-") or text.startswith("shpat_YOUR_"):
        return False
    return True

shop = data.get("shop")
token = data.get("access_token")
if real(shop) and real(token):
    sys.exit(0)
sys.exit(1)
PY
  rc=$?
  case "$rc" in
    0) printf '%s\n' present ;;
    1) printf '%s\n' incomplete ;;
    *) printf '%s\n' unreadable ;;
  esac
}

GUARD_STATUS=block
GUARD_REASON=""
GUARD_HB_EPOCH=0
GUARD_REL_EPOCH=0
guard_eval() {
  local ref="$GENSEO_FAILOVER_HEARTBEAT_REF"
  local primary="$GENSEO_FAILOVER_PRIMARY_HOST"
  local now line kind rest host epoch ceiling nonsense future_hb
  GUARD_STATUS=block
  GUARD_HB_EPOCH=0
  GUARD_REL_EPOCH=0
  now=$(date +%s)
  case "$now" in
    ''|*[!0-9]*)
      GUARD_REASON="date +%s failed; fail closed"
      return 1
      ;;
  esac
  ceiling=$((now + GUARD_SKEW))
  nonsense=$((now + GUARD_NONSENSE_AHEAD))
  if [ ! -d "$GENSEO_HOME" ] || ! git --no-pager -C "$GENSEO_HOME" rev-parse --verify --quiet "${ref}^{commit}" >/dev/null 2>&1; then
    GUARD_REASON="heartbeat ref ${ref} is missing; MacBook is assumed active"
    return 1
  fi
  # The revision goes before --. After --, git treats it as a path and the
  # marker history comes back empty.
  future_hb=0
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    kind=""
    case "$line" in
      "failover-heartbeat: ${primary} "*) kind=failover-heartbeat ;;
      "failover-release: ${primary} "*) kind=failover-release ;;
      *) continue ;;
    esac
    rest=${line#*: }
    host=${rest%% *}
    epoch=${rest#* }
    case "$host" in
      *[!a-z0-9-]*|"") continue ;;
    esac
    case "$epoch" in
      *[!0-9]*|"") continue ;;
    esac
    if [ "${#epoch}" -gt 10 ]; then
      continue
    fi
    if [ "$host" != "$primary" ]; then
      continue
    fi
    epoch=$((10#$epoch))
    if [ "$epoch" -gt "$nonsense" ]; then
      continue
    fi
    if [ "$epoch" -gt "$ceiling" ]; then
      if [ "$kind" = "failover-heartbeat" ]; then
        future_hb=1
      fi
      continue
    fi
    if [ "$kind" = "failover-heartbeat" ] && [ "$epoch" -gt "$GUARD_HB_EPOCH" ]; then
      GUARD_HB_EPOCH=$epoch
    elif [ "$kind" = "failover-release" ] && [ "$epoch" -gt "$GUARD_REL_EPOCH" ]; then
      GUARD_REL_EPOCH=$epoch
    fi
  done < <(git --no-pager -C "$GENSEO_HOME" log --format='%s' \
    --grep="^failover-heartbeat: ${primary} " \
    --grep="^failover-release: ${primary} " \
    "$ref" -- 2>/dev/null || true)
  if [ "$future_hb" = 1 ]; then
    GUARD_STATUS=block
    GUARD_REASON="primary ${primary} heartbeat is more than ${GUARD_SKEW}s in the future; fail closed"
    return 1
  fi
  if [ "$GUARD_REL_EPOCH" -gt "$GUARD_HB_EPOCH" ]; then
    GUARD_STATUS=allow
    GUARD_REASON="primary ${primary} released at ${GUARD_REL_EPOCH} after heartbeat ${GUARD_HB_EPOCH}"
    return 0
  fi
  if [ "$GUARD_HB_EPOCH" -gt 0 ]; then
    GUARD_STATUS=block
    GUARD_REASON="primary ${primary} heartbeat ${GUARD_HB_EPOCH} has no newer release; a stale heartbeat is not an offline MacBook"
    return 1
  fi
  GUARD_STATUS=block
  GUARD_REASON="no failover-release newer than a failover-heartbeat for ${primary} on ${ref}; MacBook is assumed active"
  return 1
}

file_mark() {
  if [ -f "$1" ] && [ -x "$1" ]; then
    printf '%s\n' present
  elif [ -e "$1" ]; then
    printf '%s\n' not-executable
  else
    printf '%s\n' MISSING
  fi
}

classify_dest() {
  local dest="$1"
  if [ -L "$dest" ]; then
    printf '%s\n' symlink
    return 0
  fi
  if [ ! -e "$dest" ]; then
    printf '%s\n' absent
    return 0
  fi
  if [ ! -f "$dest" ]; then
    printf '%s\n' not-file
    return 0
  fi
  if grep -F -q "$INSTALL_MARK" "$dest"; then
    printf '%s\n' ours
    return 0
  fi
  printf '%s\n' foreign
}

install_from_render() {
  local dest="$1"
  local stage dest_dir
  shift
  if [ -L "$dest" ]; then
    die "refusing to follow symlink: $dest"
  fi
  if [ -e "$dest" ] && [ ! -f "$dest" ]; then
    die "dest exists and is not a file: $dest"
  fi
  dest_dir=$(dirname "$dest")
  mkdir -p "$dest_dir" || die "could not create $dest_dir"
  stage=$(mktemp "$dest_dir/.failover.XXXXXX") || die "could not stage in $dest_dir"
  TMP_PLIST=$stage
  "$@" > "$stage" || die "render failed: $dest"
  if [ ! -s "$stage" ]; then
    die "render produced an empty plist: $dest"
  fi
  mv -f "$stage" "$dest" || die "could not replace $dest"
  TMP_PLIST=""
  chmod 644 "$dest" || die "could not chmod $dest"
}

render_worker() {
  awk -v bin="$CURSOR_AGENT_BIN" -v name="$GENSEO_WORKER_NAME" -v home="$HOME" -v ghome="$GENSEO_HOME" '
    {
      gsub(/__GENSEO_HOME__/, ghome)
      gsub(/__CURSOR_AGENT_BIN__/, bin)
      gsub(/__WORKER_NAME__/, name)
      gsub(/__HOME__/, home)
      print
    }
  ' "$WORKER_TEMPLATE"
}

rewrite_home_plist() {
  awk -v home="$HOME" -v ghome="$GENSEO_HOME" '
    {
      gsub(/\/Users\/kevinkreative\/genseo/, ghome)
      gsub(/\/Users\/kevinkreative/, home)
      print
    }
  ' "$1"
}

host_now=$(hostname 2>/dev/null || true)
host_source=hostname
if [ "$TEST_MODE" = 1 ] && [ -n "${GENSEO_FAILOVER_HOSTNAME:-}" ]; then
  host_now=$GENSEO_FAILOVER_HOSTNAME
  host_source=test
fi
[ -n "$host_now" ] || host_now=unknown
host_lc=$(printf '%s' "$host_now" | tr '[:upper:]' '[:lower:]')
host_match=no
case "$host_lc" in
  kevins-mac-mini-2|kevins-mac-mini-2.local) host_match=yes ;;
esac
if [ "$host_match" != yes ] && [ "$host_source" != test ] && command -v scutil >/dev/null 2>&1; then
  for scutil_key in LocalHostName ComputerName; do
    host_extra=$(scutil --get "$scutil_key" 2>/dev/null || true)
    host_extra_lc=$(printf '%s' "$host_extra" | tr '[:upper:]' '[:lower:]')
    case "$host_extra_lc" in
      kevins-mac-mini-2|kevins-mac-mini-2.local) host_match=yes ;;
    esac
  done
fi

cursor_state=$(file_mark "$CURSOR_AGENT_BIN")
grok_state=$(file_mark "$GROK_BIN")

clone=MISSING
branch=missing
clean=no
if [ -d "$GENSEO_HOME" ]; then
  if git -C "$GENSEO_HOME" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    clone=present
    branch=$(git -C "$GENSEO_HOME" rev-parse --abbrev-ref HEAD 2>/dev/null || printf '%s' missing)
    dirt=$(git -C "$GENSEO_HOME" status --porcelain 2>/dev/null || printf '%s' status-failed)
    if [ -z "$dirt" ]; then
      clean=yes
    else
      clean=no
    fi
  else
    clone=not-a-git-repo
  fi
fi

guard_eval || true

shopify_keys=$(derive_shopify_keys)
vault_keys=$(derive_vault_keys)
env_file_state=MISSING
if [ -f "$ENV_FILE" ] && [ -r "$ENV_FILE" ]; then
  env_file_state=present
elif [ -e "$ENV_FILE" ]; then
  env_file_state=unreadable
fi
vault_file_state=MISSING
if [ -f "$VAULT_ENV" ] && [ -r "$VAULT_ENV" ]; then
  vault_file_state=present
elif [ -e "$VAULT_ENV" ]; then
  vault_file_state=unreadable
fi
token_state=$(token_status)

env_block=0
shopify_count=0
if [ -z "$shopify_keys" ]; then
  env_block=1
fi
vault_count=0

requested=none
if [ "$REQ_WORKER" = 1 ]; then
  requested=install-worker
fi
if [ "$REQ_DAILY" = 1 ]; then
  if [ "$requested" = none ]; then
    requested=enable-daily
  else
    requested="$requested,enable-daily"
  fi
fi
if [ "$REQ_DISABLE" = 1 ]; then
  if [ "$requested" = none ]; then
    requested=disable-daily
  else
    requested="$requested,disable-daily"
  fi
fi
if [ "$DRY" = 1 ]; then
  mode=dry-run
else
  mode=apply
fi

printf '%s\n' "mac mini failover bootstrap"
printf '%s\n' "mode: $mode"
printf '%s\n' "requested: $requested"
printf '%s\n' "hostname: $host_now"
printf '%s\n' "hostname expected: Kevins-Mac-mini-2.local"
printf '%s\n' "hostname match: $host_match"
printf '%s\n' "genseo_home: $GENSEO_HOME"
printf '%s\n' "repo_root: $ROOT"
printf '%s\n' "worker_name: $GENSEO_WORKER_NAME"
printf '%s\n' "cursor_agent_bin: $CURSOR_AGENT_BIN"
printf '%s\n' "cursor-agent: $cursor_state"
printf '%s\n' "grok_bin: $GROK_BIN"
printf '%s\n' "grok: $grok_state"
printf '%s\n' "clone: $clone"
printf '%s\n' "branch: $branch"
printf '%s\n' "clean: $clean"
printf '%s\n' "env file genseo: $env_file_state"
while IFS= read -r key; do
  [ -n "$key" ] || continue
  shopify_count=$((shopify_count + 1))
  st=$(env_key_status shopify "$ENV_FILE" "$key")
  printf '%s\n' "env key ${key}: ${st} (genseo/.env)"
  if [ "$st" != present ]; then
    env_block=1
  fi
done <<EOF
$shopify_keys
EOF
printf '%s\n' "env file vault: $vault_file_state"
while IFS= read -r key; do
  [ -n "$key" ] || continue
  vault_count=$((vault_count + 1))
  st=$(env_key_status vault "$VAULT_ENV" "$key")
  printf '%s\n' "env key ${key}: ${st} (vault .env)"
  if [ "$st" != present ]; then
    env_block=1
  fi
done <<EOF
$vault_keys
EOF
if [ "$shopify_count" = 0 ]; then
  printf '%s\n' "env key list genseo: empty"
fi
if [ "$vault_count" = 0 ]; then
  printf '%s\n' "env key list vault: empty"
  env_block=1
fi
printf '%s\n' "shopify token file: $token_state"
printf '%s\n' "guard: $GUARD_STATUS"
printf '%s\n' "guard_reason: $GUARD_REASON"
printf '%s\n' "guard_heartbeat_epoch: $GUARD_HB_EPOCH"
printf '%s\n' "guard_release_epoch: $GUARD_REL_EPOCH"
printf '%s\n' "guard_ref: $GENSEO_FAILOVER_HEARTBEAT_REF"
printf '%s\n' "guard_primary: $GENSEO_FAILOVER_PRIMARY_HOST"
printf '%s\n' "stale_heartbeat_allow: no"
if [ -n "${GENSEO_FAILOVER_HEARTBEAT_MAX_AGE+x}" ]; then
  printf '%s\n' "heartbeat_max_age: ignored"
fi

worker_ready=yes
daily_ready=yes
if [ "$host_match" != yes ]; then
  worker_ready=no
  daily_ready=no
  printf '%s\n' "worker_block: hostname"
  printf '%s\n' "daily_block: hostname"
fi
if ! name_safe "$GENSEO_WORKER_NAME"; then
  worker_ready=no
  printf '%s\n' "worker_block: name"
fi
if ! plist_safe "$CURSOR_AGENT_BIN" || ! plist_safe "$HOME" || ! plist_safe "$GENSEO_HOME"; then
  worker_ready=no
  daily_ready=no
  printf '%s\n' "worker_block: path"
  printf '%s\n' "daily_block: path"
fi
if [ ! -f "$WORKER_TEMPLATE" ]; then
  worker_ready=no
  printf '%s\n' "worker_block: template"
fi
if [ "$cursor_state" != present ]; then
  worker_ready=no
  printf '%s\n' "worker_block: cursor-agent"
fi
if [ ! -d "$GENSEO_HOME" ]; then
  worker_ready=no
  printf '%s\n' "worker_block: genseo-home"
fi
worker_class=$(classify_dest "$WORKER_DEST")
if [ "$worker_class" = foreign ] || [ "$worker_class" = not-file ]; then
  worker_ready=no
  printf '%s\n' "worker_block: foreign-plist"
fi
if [ -L "$AGENT_DIR" ] || [ -L "$LOG_DIR" ]; then
  worker_ready=no
  daily_ready=no
  printf '%s\n' "worker_block: symlink"
  printf '%s\n' "daily_block: symlink"
fi
if [ "$worker_ready" = yes ]; then
  printf '%s\n' "worker_block: none"
fi
printf '%s\n' "worker_ready: $worker_ready"

if [ "$GUARD_STATUS" != allow ]; then
  daily_ready=no
  printf '%s\n' "daily_block: guard"
fi
if [ "$clone" != present ]; then
  daily_ready=no
  printf '%s\n' "daily_block: clone"
fi
if [ "$branch" != main ]; then
  daily_ready=no
  printf '%s\n' "daily_block: branch"
fi
if [ "$clean" != yes ]; then
  daily_ready=no
  printf '%s\n' "daily_block: clean"
fi
if [ "$env_block" != 0 ]; then
  daily_ready=no
  printf '%s\n' "daily_block: env"
fi
if [ "$token_state" != present ]; then
  daily_ready=no
  printf '%s\n' "daily_block: token"
fi
if [ "$grok_state" != present ]; then
  daily_ready=no
  printf '%s\n' "daily_block: grok"
fi
for rel in scripts/run_landing_daily.sh scripts/genseo_daily_lock.sh scripts/genseo_group_timeout.sh deploy/grokbot-genseo-daily.sh; do
  if [ ! -f "$GENSEO_HOME/$rel" ]; then
    daily_ready=no
    printf '%s\n' "daily_block: helpers"
    break
  fi
done
if [ ! -f "$DAILY_TEMPLATE" ] || [ ! -f "$LANDING_TEMPLATE" ]; then
  daily_ready=no
  printf '%s\n' "daily_block: plist"
else
  if ! grep -F -q "$INSTALL_MARK" "$DAILY_TEMPLATE" || ! grep -F -q "$INSTALL_MARK" "$LANDING_TEMPLATE"; then
    daily_ready=no
    printf '%s\n' "daily_block: mark"
  fi
  if ! grep -F -q 'never published' "$LANDING_TEMPLATE" || grep -E -q 'GENSEO_LANDING_LIVE_OK|--live|shopify_publisher|landing_publisher' "$LANDING_TEMPLATE"; then
    daily_ready=no
    printf '%s\n' "daily_block: landing-publish"
  fi
fi
daily_class=$(classify_dest "$DAILY_DEST")
landing_class=$(classify_dest "$LANDING_DEST")
if [ "$daily_class" = foreign ] || [ "$daily_class" = not-file ] || [ "$landing_class" = foreign ] || [ "$landing_class" = not-file ]; then
  daily_ready=no
  printf '%s\n' "daily_block: foreign-plist"
fi
if [ -L "$GENSEO_HOME/logs" ]; then
  daily_ready=no
  printf '%s\n' "daily_block: symlink"
fi
if [ "$daily_ready" = yes ]; then
  printf '%s\n' "daily_block: none"
fi
printf '%s\n' "daily_ready: $daily_ready"
printf '%s\n' "worker_plist: $WORKER_DEST"
printf '%s\n' "daily_plist: $DAILY_DEST"
printf '%s\n' "landing_plist: $LANDING_DEST"
printf '%s\n' "worker argv: $CURSOR_AGENT_BIN worker start --name $GENSEO_WORKER_NAME --worker-dir $GENSEO_HOME"
printf '%s\n' 'load_worker: launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.pati.cursor-agent-worker.plist'
printf '%s\n' 'load_daily: launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-daily.plist'
printf '%s\n' 'load_landing: launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-landing.plist'
printf '%s\n' 'macbook_bootout: launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-daily.plist'
printf '%s\n' 'macbook_bootout: launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-landing.plist'
printf '%s\n' "release marker subject: failover-release: ${GENSEO_FAILOVER_PRIMARY_HOST} <epoch>"
printf '%s\n' 'wrapper_hint: bash scripts/install_mac_daily_wrapper.sh'
printf '%s\n' "launchd: not started"
printf '%s\n' 'handover_check: this script cannot see the MacBook and does not call launchctl. Boot the MacBook agents out before loading the Mini plists.'
printf '%s\n' "daily_plist_class: $daily_class"
printf '%s\n' "landing_plist_class: $landing_class"
if [ "$GUARD_STATUS" != allow ] && { [ "$daily_class" = ours ] || [ "$landing_class" = ours ]; }; then
  printf '%s\n' "warning: installer plists are on disk while the guard is block. This script does not bootout launchd. --disable-daily removes the marked files only."
fi

worker_install=not-requested
daily_install=not-requested
disable_install=not-requested
disable_bad=0
disable_ours=0
if [ "$REQ_DISABLE" = 1 ]; then
  case "$daily_class" in
    absent) ;;
    ours) disable_ours=1 ;;
    *) disable_bad=1 ;;
  esac
  case "$landing_class" in
    absent) ;;
    ours) disable_ours=1 ;;
    *) disable_bad=1 ;;
  esac
  if [ -L "$AGENT_DIR" ]; then
    disable_bad=1
  fi
  if [ "$disable_bad" = 1 ]; then
    if [ "$DRY" = 1 ]; then
      disable_install=would-refuse
    fi
  elif [ "$disable_ours" = 1 ]; then
    if [ "$DRY" = 1 ]; then
      disable_install=would-remove
    fi
  else
    disable_install=absent
  fi
fi
if [ "$REQ_WORKER" = 1 ]; then
  if [ "$DRY" = 1 ]; then
    if [ "$worker_ready" = yes ]; then
      worker_install=would-write
    else
      worker_install=would-refuse
    fi
  fi
fi
if [ "$REQ_DAILY" = 1 ]; then
  if [ "$DRY" = 1 ]; then
    if [ "$daily_ready" = yes ]; then
      daily_install=would-write
    else
      daily_install=would-refuse
    fi
  fi
fi

wrapper_state="not run"
if [ "$DRY" = 1 ]; then
  printf '%s\n' "wrapper: $wrapper_state"
  printf '%s\n' "worker_install: $worker_install"
  printf '%s\n' "daily_install: $daily_install"
  printf '%s\n' "disable_daily: $disable_install"
  exit 0
fi

if [ "$on_mac" != 1 ] && [ "$TEST_MODE" != 1 ]; then
  if [ "$REQ_WORKER" = 1 ]; then
    worker_install=refused
  fi
  if [ "$REQ_DAILY" = 1 ]; then
    daily_install=refused
  fi
  if [ "$REQ_DISABLE" = 1 ]; then
    disable_install=refused
  fi
  printf '%s\n' "wrapper: $wrapper_state"
  printf '%s\n' "worker_install: $worker_install"
  printf '%s\n' "daily_install: $daily_install"
  printf '%s\n' "disable_daily: $disable_install"
  printf '%s\n' "refusing: this installer writes LaunchAgents on a Mac (uname $(uname -s))." >&2
  printf '%s\n' "On the Mini: bash ~/genseo/scripts/mac_mini_failover_bootstrap.sh" >&2
  exit 2
fi

apply_fail=0
if [ "$REQ_WORKER" = 1 ]; then
  if [ "$worker_ready" != yes ]; then
    worker_install=refused
    apply_fail=1
    printf '%s\n' "refusing worker plist: worker_ready no" >&2
  else
    mkdir -p "$LOG_DIR" || die "could not create $LOG_DIR"
    install_from_render "$WORKER_DEST" render_worker
    if grep -E -q '__CURSOR_AGENT_BIN__|__WORKER_NAME__|__GENSEO_HOME__|__HOME__' "$WORKER_DEST"; then
      rm -f "$WORKER_DEST"
      die "rendered worker plist still has unsubstituted tokens"
    fi
    worker_install=written
  fi
fi

if [ "$REQ_DAILY" = 1 ]; then
  if [ "$daily_ready" != yes ]; then
    daily_install=refused
    apply_fail=1
    printf '%s\n' "refusing daily plists: daily_ready no" >&2
  else
    if [ -L "$LOG_DIR" ] || [ -L "$GENSEO_HOME/logs" ]; then
      die "refusing to follow symlink: logs"
    fi
    mkdir -p "$LOG_DIR" "$GENSEO_HOME/logs" || die "could not create log dirs"
    if [ "$TEST_MODE" = 1 ]; then
      env HOME="$HOME" GENSEO_HOME="$GENSEO_HOME" PATH="$PATH" GENSEO_INSTALL_WRAPPER_TEST=1 \
        /bin/bash "$ROOT/scripts/install_mac_daily_wrapper.sh" || die "daily wrapper install failed"
    else
      env HOME="$HOME" GENSEO_HOME="$GENSEO_HOME" PATH="$PATH" \
        /bin/bash "$ROOT/scripts/install_mac_daily_wrapper.sh" || die "daily wrapper install failed"
    fi
    wrapper_state=ran
    install_from_render "$DAILY_DEST" rewrite_home_plist "$DAILY_TEMPLATE"
    install_from_render "$LANDING_DEST" rewrite_home_plist "$LANDING_TEMPLATE"
    if [ "$HOME" != "/Users/kevinkreative" ]; then
      if grep -q '/Users/kevinkreative' "$DAILY_DEST" || grep -q '/Users/kevinkreative' "$LANDING_DEST"; then
        rm -f "$DAILY_DEST" "$LANDING_DEST"
        die "daily plist still points at /Users/kevinkreative"
      fi
    fi
    if ! grep -F -q "$INSTALL_MARK" "$DAILY_DEST" || ! grep -F -q "$INSTALL_MARK" "$LANDING_DEST" || ! grep -F -q 'never published' "$LANDING_DEST" || grep -E -q 'GENSEO_LANDING_LIVE_OK|--live|shopify_publisher|landing_publisher' "$LANDING_DEST"; then
      rm -f "$DAILY_DEST" "$LANDING_DEST"
      die "landing plist is not an unpublished-draft job"
    fi
    daily_install=written
  fi
fi

if [ "$REQ_DISABLE" = 1 ]; then
  if [ "$host_match" != yes ]; then
    disable_install=refused
    apply_fail=1
    printf '%s\n' "refusing disable: hostname is not the Mini" >&2
  elif [ "$disable_bad" = 1 ]; then
    disable_install=refused
    apply_fail=1
    printf '%s\n' "refusing disable: plist is not ours or LaunchAgents is a symlink" >&2
  elif [ "$disable_ours" = 1 ]; then
    if [ "$daily_class" = ours ]; then
      rm -f "$DAILY_DEST" || die "could not remove $DAILY_DEST"
    fi
    if [ "$landing_class" = ours ]; then
      rm -f "$LANDING_DEST" || die "could not remove $LANDING_DEST"
    fi
    disable_install=removed
  else
    disable_install=absent
  fi
fi

printf '%s\n' "wrapper: $wrapper_state"
printf '%s\n' "worker_install: $worker_install"
printf '%s\n' "daily_install: $daily_install"
printf '%s\n' "disable_daily: $disable_install"
if [ "$apply_fail" != 0 ]; then
  exit 1
fi
exit 0

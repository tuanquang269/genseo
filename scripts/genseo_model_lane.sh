#!/bin/bash
# Writer-model lane for the GenSeo headless runners. Sourced by
# run_ticket_headless.sh and run_landing_headless.sh. Never prints NINE_ROUTER_KEY.
#
# Order:
#   1. native           caller set USE_NATIVE=1 (~/.claude-genseo loggedIn: true)
#                       AND neither the writer nor the fallback is a router alias
#   2. local-9router    GENSEO_LOCAL_ROUTER (default http://127.0.0.1:20128) is up
#                       AND /v1/models lists GENSEO_WRITER_MODEL
#   3. hosted-9router   GENSEO_ROUTER_BASE (default https://ai.patigroup.com)
#                       with NINE_ROUTER_KEY from the env or ~/PATI/LLM-Wiki/.env
#
# Router aliases use the prefix PATI- (default writer PATI-Alpha-Plan-Review,
# fallback PATI-Fable-5). Native Claude Code does not know those ids and returns
# unrecognized_model (landing 2026-10-10 09:30). When the writer or the fallback
# matches, USE_NATIVE is ignored and cleared so the router lanes run, including
# callers that branch on the login flag (run_ticket_headless.sh).
#
# Bare aliases are not passed to claude. scripts/genseo_model_map.json maps an
# Anthropic id Claude Code accepts onto each alias (claude-opus-5-5 for the
# planner, claude-fable-5 for the Fable fallback). --model / --fallback-model
# receive the Anthropic id. modelOverrides in --settings is what the gateway
# receives, so the router still sees the PATI alias. No Anthropic API key is
# set. An alias with no map entry is a fatal error before claude starts:
# landing 2026-10-15 sat ~2h20 after unrecognized_model on the SDK query and
# on agent:builtin:Explore (the fallback alias). A /v1/models hit is not a
# Claude Code registration. GENSEO_MODEL_MAP_JSON overrides the map path and
# must stay unset in production.
#
# Local lane does not export ANTHROPIC_BASE_URL. The Mini's global Claude settings
# already route at its 9router, and a process env cannot reliably override that.
# Hosted lane exports the base URL and token into the lean CLAUDE_CONFIG_DIR
# (no settings.json), which is what a MacBook needs when :20128 is up but its
# model list has no PATI writer alias (2026-10-10).
#
# Router lanes set GENSEO_PERMISSION_MODE=dontAsk. Claude Code 2.1.295+ defaults
# `claude -p` to permission mode auto, and auto mode uses the session model id as
# the Bash safety service. PATI-Alpha-Plan-Review is not a classifier the gateway
# can run, so Bash is blocked and the agent exits 0 before any write (articles
# 2026-10-11 08:19). dontAsk keeps the runner allowlist and does not call that
# classifier. The gateway still receives the PATI alias through modelOverrides.
# Native login leaves GENSEO_PERMISSION_MODE empty (CLI default). A stale value
# in the environment is cleared or overwritten here.
#
# Wrong-shape response (landing 2026-10-12 09:19): a PATI alias can return HTTP 200
# JSON that is an OpenAI chat.completion, not an Anthropic Messages API message.
# Claude Code logs "body is JSON but not a Message" and exits. Its own
# --fallback-model does not run. genseo_run_writer_with_shape_fallback re-executes
# the same argv once on GENSEO_WRITER_FALLBACK. GENSEO_WRITER_SHAPE_RETRY stops a
# second re-exec. Draft-only flags are unchanged; this helper never publishes.
#
# Test hooks — leave unset in production:
#   GENSEO_LANE_LOCAL_UP=0|1
#   GENSEO_LANE_MODELS_JSON='{"data":[{"id":"..."}]}'

genseo_writer_model() {
  printf '%s' "${GENSEO_WRITER_MODEL:-PATI-Alpha-Plan-Review}"
}

genseo_writer_fallback() {
  printf '%s' "${GENSEO_WRITER_FALLBACK:-PATI-Fable-5}"
}

# A test may assign GENSEO_MODEL_MAP_JSON without exporting it. Python only
# sees the exported environment, and this must run in the current shell.
genseo_export_model_map() {
  if [ -n "${GENSEO_MODEL_MAP_JSON:-}" ]; then
    export GENSEO_MODEL_MAP_JSON
  fi
}

genseo_model_map_py() {
  local dir
  dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  printf '%s' "${GENSEO_MODEL_MAP_PY:-$dir/genseo_model_map.py}"
}

# Print the Claude Code model id for $1. A claude-* id is unchanged. A mapped
# gateway alias becomes the Anthropic id from scripts/genseo_model_map.json.
# On refusal, set GENSEO_MODEL_LANE_ERROR and return 1. Never prints the router key.
genseo_claude_model_id() {
  local py line
  genseo_export_model_map
  py="$(genseo_model_map_py)"
  line="$(python3 "$py" claude-id -- "$1" 2>/dev/null)" || true
  case "$line" in
    "OK "*)
      printf '%s' "${line#OK }"
      return 0
      ;;
    "ERR "*)
      GENSEO_MODEL_LANE_ERROR="${line#ERR }"
      printf '%s\n' "$GENSEO_MODEL_LANE_ERROR" >&2
      return 1
      ;;
    *)
      GENSEO_MODEL_LANE_ERROR="model map could not be read"
      printf '%s\n' "$GENSEO_MODEL_LANE_ERROR" >&2
      return 1
      ;;
  esac
}

# Resolve $1 in the current shell. Command substitution cannot keep
# GENSEO_MODEL_LANE_ERROR, so the error is read back from stderr.
# On success GENSEO_RESOLVED_MODEL is the Claude Code id.
genseo_resolve_model() {
  local errfile id
  errfile="$(mktemp "${TMPDIR:-/tmp}/genseo-model-id.XXXXXX")" || {
    GENSEO_MODEL_LANE_ERROR="model map could not be read"
    return 1
  }
  if ! id="$(genseo_claude_model_id "$1" 2>"$errfile")"; then
    GENSEO_MODEL_LANE_ERROR="$(tr '\n' ' ' <"$errfile" | sed 's/ *$//')"
    rm -f "$errfile"
    if [ -z "${GENSEO_MODEL_LANE_ERROR:-}" ]; then
      GENSEO_MODEL_LANE_ERROR="unrecognized model: $1"
    fi
    GENSEO_RESOLVED_MODEL=""
    return 1
  fi
  rm -f "$errfile"
  GENSEO_RESOLVED_MODEL="$id"
}

# Pin family aliases only for gateway aliases this run mapped. A claude-* writer
# keeps the CLI default. Unset first so a previous alias cannot leak into a
# native run in the same shell.
genseo_pin_one_family() {
  local configured="$1" resolved="$2"
  case "$configured" in
    claude-*|"") return 0 ;;
  esac
  case "$resolved" in
    *opus*) export ANTHROPIC_DEFAULT_OPUS_MODEL="$resolved" ;;
    *fable*) export ANTHROPIC_DEFAULT_FABLE_MODEL="$resolved" ;;
  esac
}

genseo_pin_mapped_families() {
  local writer_id="" fallback_id=""
  unset ANTHROPIC_DEFAULT_OPUS_MODEL ANTHROPIC_DEFAULT_FABLE_MODEL
  genseo_resolve_model "$GENSEO_WRITER_MODEL" || return 1
  writer_id="$GENSEO_RESOLVED_MODEL"
  genseo_resolve_model "$GENSEO_WRITER_FALLBACK" || return 1
  fallback_id="$GENSEO_RESOLVED_MODEL"
  genseo_pin_one_family "$GENSEO_WRITER_MODEL" "$writer_id"
  genseo_pin_one_family "$GENSEO_WRITER_FALLBACK" "$fallback_id"
}

# Stdin-less: $3 is the existing --settings JSON, or empty. Prints the merged
# object, or nothing when there is nothing to pass. modelOverrides values are
# the gateway aliases.
genseo_merge_model_settings() {
  local py merged errfile rc
  genseo_export_model_map
  py="$(genseo_model_map_py)"
  errfile="$(mktemp "${TMPDIR:-/tmp}/genseo-model-settings.XXXXXX")" || return 1
  merged="$(python3 "$py" merge-settings --writer "$1" --fallback "$2" 2>"$errfile" <<<"${3:-}")"
  rc=$?
  if [ "$rc" != 0 ]; then
    GENSEO_MODEL_LANE_ERROR="$(tr '\n' ' ' <"$errfile" | sed 's/ *$//')"
    rm -f "$errfile"
    return 1
  fi
  rm -f "$errfile"
  printf '%s' "$merged"
}

genseo_claude_model_log_line() {
  local writer_id="" fallback_id="" saved=""
  saved="${GENSEO_MODEL_LANE_ERROR:-}"
  writer_id="$(genseo_claude_model_id "${GENSEO_WRITER_MODEL:-}" 2>/dev/null)" || writer_id="unmapped"
  fallback_id="$(genseo_claude_model_id "${GENSEO_WRITER_FALLBACK:-}" 2>/dev/null)" || fallback_id="unmapped"
  GENSEO_MODEL_LANE_ERROR="$saved"
  printf '(claude-model: writer=%s fallback=%s gateway=%s/%s)\n' \
    "$writer_id" "$fallback_id" \
    "${GENSEO_WRITER_MODEL:-}" "${GENSEO_WRITER_FALLBACK:-}"
}

# Exit 0 when $1 is a 9router alias Claude Code native login cannot resolve.
# The alias family is the PATI- prefix. A later "PATI" substring is not an alias.
genseo_model_is_router_alias() {
  case "${1:-}" in
    PATI-*) return 0 ;;
  esac
  return 1
}

# stdin = /v1/models JSON. Exit 0 when $1 is an exact data[].id or data[].name.
# Exit 1 when the list parsed and the id is absent. Exit 2 when the body is not a list.
genseo_models_json_has_id() {
  python3 -c '
import json, sys
want = sys.argv[1]
raw = sys.stdin.read()
try:
    data = json.loads(raw) if raw.strip() else None
except Exception:
    sys.exit(2)
rows = data.get("data") if isinstance(data, dict) else data
if not isinstance(rows, list):
    sys.exit(2)
for row in rows:
    if isinstance(row, dict):
        mid = row.get("id")
        if mid in (None, ""):
            mid = row.get("name")
    elif isinstance(row, str):
        mid = row
    else:
        continue
    if str(mid) == want:
        sys.exit(0)
sys.exit(1)
' "$1"
}

_genseo_load_nine_key() {
  local k line
  k="${NINE_ROUTER_KEY:-}"
  if [ -z "$k" ] && [ -f "$HOME/PATI/LLM-Wiki/.env" ]; then
    line="$(grep -E '^(export )?NINE_ROUTER_KEY=' "$HOME/PATI/LLM-Wiki/.env" 2>/dev/null | head -1 || true)"
    k="$(printf '%s\n' "$line" | sed -E 's/^(export )?NINE_ROUTER_KEY=//; s/^["'"'"']//; s/["'"'"']$//')"
  fi
  printf '%s' "$k"
}

genseo_select_model_lane() {
  local model base up body key cfg
  GENSEO_WRITER_MODEL="$(genseo_writer_model)"
  GENSEO_WRITER_FALLBACK="$(genseo_writer_fallback)"
  export GENSEO_WRITER_MODEL GENSEO_WRITER_FALLBACK
  model="$GENSEO_WRITER_MODEL"
  GENSEO_MODEL_LANE=""
  GENSEO_MODEL_LANE_ERROR=""
  GENSEO_PERMISSION_MODE=""
  export GENSEO_PERMISSION_MODE
  base="${GENSEO_LOCAL_ROUTER:-http://127.0.0.1:20128}"
  base="${base%/}"
  cfg="${GENSEO_CFG:-$HOME/.claude-genseo}"

  # Refuse a bare alias before any router call. Claude Code does not accept it,
  # and confirming it on a subagent switch is what hung landing 2026-10-15.
  unset ANTHROPIC_DEFAULT_OPUS_MODEL ANTHROPIC_DEFAULT_FABLE_MODEL
  if ! genseo_resolve_model "$model"; then
    return 1
  fi
  if ! genseo_resolve_model "$GENSEO_WRITER_FALLBACK"; then
    return 1
  fi

  # PATI-* is not a native Claude model. Ignore the login flag and clear it so
  # run_ticket_headless.sh uses the router invocation (context cap, strict MCP).
  if genseo_model_is_router_alias "$model" || genseo_model_is_router_alias "$GENSEO_WRITER_FALLBACK"; then
    USE_NATIVE=0
  fi

  if [ "${USE_NATIVE:-0}" = "1" ]; then
    genseo_pin_mapped_families || return 1
    export CLAUDE_CONFIG_DIR="$cfg"
    GENSEO_MODEL_LANE="native"
    return 0
  fi

  up=0
  if [ -n "${GENSEO_LANE_LOCAL_UP+x}" ]; then
    [ "$GENSEO_LANE_LOCAL_UP" = "1" ] && up=1
  elif curl -s -m 3 -o /dev/null "$base/" 2>/dev/null; then
    up=1
  fi

  if [ "$up" = "1" ]; then
    if [ -n "${GENSEO_LANE_MODELS_JSON+x}" ]; then
      body="$GENSEO_LANE_MODELS_JSON"
    else
      body="$(curl -s -m 5 "$base/v1/models" 2>/dev/null || true)"
    fi
    if printf '%s' "$body" | genseo_models_json_has_id "$model"; then
      genseo_pin_mapped_families || return 1
      GENSEO_MODEL_LANE="local-9router"
      GENSEO_PERMISSION_MODE="dontAsk"
      export GENSEO_PERMISSION_MODE
      return 0
    fi
  fi

  key="$(_genseo_load_nine_key)"
  if [ -z "$key" ]; then
    GENSEO_MODEL_LANE_ERROR="no model lane (no native login, local 9router down or missing ${model}, no NINE_ROUTER_KEY)"
    return 1
  fi
  genseo_pin_mapped_families || return 1
  export ANTHROPIC_BASE_URL="${GENSEO_ROUTER_BASE:-https://ai.patigroup.com}"
  export ANTHROPIC_AUTH_TOKEN="$key"
  export CLAUDE_CONFIG_DIR="$cfg"
  mkdir -p "$cfg"
  GENSEO_MODEL_LANE="hosted-9router"
  GENSEO_PERMISSION_MODE="dontAsk"
  export GENSEO_PERMISSION_MODE
  return 0
}

genseo_lane_log_line() {
  printf '(lane: %s on %s writer=%s fallback=%s permission=%s)\n' \
    "${GENSEO_MODEL_LANE:-unset}" \
    "$(hostname -s 2>/dev/null || hostname)" \
    "${GENSEO_WRITER_MODEL:-PATI-Alpha-Plan-Review}" \
    "${GENSEO_WRITER_FALLBACK:-PATI-Fable-5}" \
    "${GENSEO_PERMISSION_MODE:-cli-default}"
}

# Exit 0 when the writer log's latest attempt is a non-Anthropic model payload.
# Exit 1 when it is an Anthropic message, an Anthropic error, or any other failure.
genseo_log_needs_writer_fallback() {
  local dir py
  dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  py="${GENSEO_WRITER_RESPONSE_PY:-$dir/genseo_writer_response.py}"
  [ -f "$py" ] || return 1
  python3 "$py" --log "$1" >/dev/null
}

# Bound a stuck writer connect or read without changing the model or the provider.
# 2026-10-12 run 5: the Claude process sat at 0% CPU with two connects in SYN_SENT
# to Cloudflare, past the 90-minute ticket cap. CLAUDE_CODE_CONNECT_TIMEOUT_MS is a
# no-op since Claude Code 2.1.186. API_TIMEOUT_MS is the whole-request cap (Claude's
# own 10-minute default, set here so a build with no default cannot wait forever).
# CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS bounds the handshake and the first response
# byte. CLAUDE_STREAM_IDLE_TIMEOUT_MS bounds a read that goes quiet; the CLI clamps
# an explicit value to at least 5 minutes. Export any of them before the runner to
# override. Settings-file env still wins inside Claude Code when it replaces the
# process environment; the ticket cap is the backstop.
genseo_exec_writer() {
  local bin=$1
  shift
  env \
    "API_TIMEOUT_MS=${API_TIMEOUT_MS:-600000}" \
    "CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS=${CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS:-120000}" \
    "CLAUDE_STREAM_IDLE_TIMEOUT_MS=${CLAUDE_STREAM_IDLE_TIMEOUT_MS:-300000}" \
    "$bin" "$@"
}

# Rewrite --model / --fallback-model to Claude Code ids and merge modelOverrides
# into the existing --settings object. $1 is the gateway name for this attempt
# (writer or fallback). Remaining args are the caller's claude argv.
# Sets GENSEO_PREPARED_ARGS and GENSEO_PREPARED_MODEL. Does not exec claude.
genseo_prepare_writer_args() {
  local model_name="$1"
  shift
  local -a incoming=()
  local -a built=()
  local i=0 count=0 arg="" nxt=""
  local attempt_id="" writer_id="" fallback_id=""
  local settings_at=-1 existing="" merged=""
  GENSEO_PREPARED_ARGS=()
  GENSEO_PREPARED_MODEL=""
  if [ "$#" -gt 0 ]; then
    incoming=("$@")
  fi
  count=${#incoming[@]}
  if ! genseo_resolve_model "${GENSEO_WRITER_MODEL:-}"; then
    return 1
  fi
  writer_id="$GENSEO_RESOLVED_MODEL"
  if ! genseo_resolve_model "${GENSEO_WRITER_FALLBACK:-}"; then
    return 1
  fi
  fallback_id="$GENSEO_RESOLVED_MODEL"
  if ! genseo_resolve_model "$model_name"; then
    return 1
  fi
  attempt_id="$GENSEO_RESOLVED_MODEL"
  GENSEO_PREPARED_MODEL="$attempt_id"
  unset ANTHROPIC_DEFAULT_OPUS_MODEL ANTHROPIC_DEFAULT_FABLE_MODEL
  genseo_pin_one_family "${GENSEO_WRITER_MODEL:-}" "$writer_id"
  genseo_pin_one_family "${GENSEO_WRITER_FALLBACK:-}" "$fallback_id"
  while [ "$i" -lt "$count" ]; do
    arg="${incoming[$i]}"
    if [ "$arg" = "--model" ] || [ "$arg" = "--fallback-model" ]; then
      i=$((i + 1))
      if [ "$i" -ge "$count" ]; then
        GENSEO_MODEL_LANE_ERROR="missing value after $arg"
        return 1
      fi
      nxt="${incoming[$i]}"
      if ! genseo_resolve_model "$nxt"; then
        return 1
      fi
      nxt="$GENSEO_RESOLVED_MODEL"
      # A caller --model is rewritten so a bare alias cannot reach claude.
      # The attempt id is appended last and is the one claude uses.
      if [ "$arg" = "--fallback-model" ]; then
        built+=("--fallback-model" "$nxt")
      fi
      i=$((i + 1))
      continue
    fi
    if [ "$arg" = "--settings" ]; then
      i=$((i + 1))
      settings_at=${#built[@]}
      if [ "$i" -ge "$count" ]; then
        built+=("--settings" "")
        break
      fi
      built+=("--settings" "${incoming[$i]}")
      i=$((i + 1))
      continue
    fi
    built+=("$arg")
    i=$((i + 1))
  done
  built+=("--model" "$GENSEO_PREPARED_MODEL")
  existing=""
  if [ "$settings_at" -ge 0 ]; then
    existing="${built[$((settings_at + 1))]}"
  fi
  if ! merged="$(genseo_merge_model_settings "${GENSEO_WRITER_MODEL:-}" "${GENSEO_WRITER_FALLBACK:-}" "$existing")"; then
    return 1
  fi
  if [ -n "$merged" ]; then
    if [ "$settings_at" -ge 0 ]; then
      built[$((settings_at + 1))]="$merged"
    else
      built+=("--settings" "$merged")
    fi
  fi
  GENSEO_PREPARED_ARGS=("${built[@]}")
}

_genseo_model_fail() {
  local log="$1"
  local msg="${GENSEO_MODEL_LANE_ERROR:-unrecognized model}"
  printf 'FATAL: %s\n' "$msg" >>"$log"
  printf 'FATAL: %s\n' "$msg" >&2
}

_genseo_log_writer_attempt() {
  local log="$1" gateway="$2"
  printf '=== writer attempt model=%s gateway=%s ===\n' \
    "$GENSEO_PREPARED_MODEL" "$gateway" >>"$log"
}

# Run claude once. On a non-Anthropic HTTP 200 JSON failure, run it one more time
# with --model set to the fallback's Claude Code id. Same remaining argv, including
# draft/permission flags. Gateway aliases are rewritten before exec. An unmapped
# alias returns 1 without starting claude.
genseo_run_writer_with_shape_fallback() {
  local log="$1" bin="$2"
  shift 2
  local rc=0
  if [ -z "$log" ] || [ -z "$bin" ]; then
    echo "writer-shape: missing log or claude bin" >&2
    return 1
  fi
  : "${GENSEO_WRITER_MODEL:=PATI-Alpha-Plan-Review}"
  : "${GENSEO_WRITER_FALLBACK:=PATI-Fable-5}"
  export GENSEO_WRITER_MODEL GENSEO_WRITER_FALLBACK

  if [ "${GENSEO_WRITER_SHAPE_RETRY:-0}" = "1" ]; then
    if ! genseo_prepare_writer_args "$GENSEO_WRITER_FALLBACK" "$@"; then
      _genseo_model_fail "$log"
      return 1
    fi
    _genseo_log_writer_attempt "$log" "$GENSEO_WRITER_FALLBACK"
    genseo_exec_writer "$bin" "${GENSEO_PREPARED_ARGS[@]}" >>"$log" 2>&1 || rc=$?
    return "$rc"
  fi

  if ! genseo_prepare_writer_args "$GENSEO_WRITER_MODEL" "$@"; then
    _genseo_model_fail "$log"
    return 1
  fi
  _genseo_log_writer_attempt "$log" "$GENSEO_WRITER_MODEL"
  genseo_exec_writer "$bin" "${GENSEO_PREPARED_ARGS[@]}" >>"$log" 2>&1 || rc=$?
  if [ "$rc" -eq 0 ]; then
    return 0
  fi
  if [ -z "$GENSEO_WRITER_FALLBACK" ] || [ "$GENSEO_WRITER_FALLBACK" = "$GENSEO_WRITER_MODEL" ]; then
    return "$rc"
  fi
  if ! genseo_log_needs_writer_fallback "$log"; then
    return "$rc"
  fi
  printf 'writer-shape: %s returned HTTP 200 JSON that is not an Anthropic message; one re-exec on %s\n' \
    "$GENSEO_WRITER_MODEL" "$GENSEO_WRITER_FALLBACK" >>"$log"
  GENSEO_WRITER_SHAPE_RETRY=1
  export GENSEO_WRITER_SHAPE_RETRY
  if ! genseo_prepare_writer_args "$GENSEO_WRITER_FALLBACK" "$@"; then
    _genseo_model_fail "$log"
    return 1
  fi
  _genseo_log_writer_attempt "$log" "$GENSEO_WRITER_FALLBACK"
  rc=0
  genseo_exec_writer "$bin" "${GENSEO_PREPARED_ARGS[@]}" >>"$log" 2>&1 || rc=$?
  if genseo_log_needs_writer_fallback "$log"; then
    printf 'writer-shape: %s also returned a non-Anthropic payload; not retrying again\n' \
      "$GENSEO_WRITER_FALLBACK" >>"$log"
  fi
  return "$rc"
}

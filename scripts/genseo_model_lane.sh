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
# classifier. The writer id sent to the gateway stays the PATI alias.
# unrecognized_model may still print; that line is a warning, not the Bash block.
# Native login leaves GENSEO_PERMISSION_MODE empty (CLI default). A stale value
# in the environment is cleared or overwritten here.
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

  # PATI-* is not a native Claude model. Ignore the login flag and clear it so
  # run_ticket_headless.sh uses the router invocation (context cap, strict MCP).
  if genseo_model_is_router_alias "$model" || genseo_model_is_router_alias "$GENSEO_WRITER_FALLBACK"; then
    USE_NATIVE=0
  fi

  if [ "${USE_NATIVE:-0}" = "1" ]; then
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

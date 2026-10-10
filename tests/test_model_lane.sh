#!/bin/bash
# Offline checks for scripts/genseo_model_lane.sh. No Shopify, no Claude, no network.
#   bash tests/test_model_lane.sh
#   bash tests/test_model_lane.sh --live
# --live probes this machine's :20128 and vault key and prints only the lane name
# (native / local-9router / hosted-9router), never the key.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../scripts/genseo_model_lane.sh
. "$ROOT/scripts/genseo_model_lane.sh"

if [ "${1:-}" = "--live" ]; then
  unset GENSEO_LANE_LOCAL_UP GENSEO_LANE_MODELS_JSON
  GENSEO_CFG="${GENSEO_CFG:-$HOME/.claude-genseo}"
  USE_NATIVE=0
  if [ -d "$GENSEO_CFG" ] && [ -x "$HOME/.local/bin/claude" ]; then
    AUTH_JSON="$(CLAUDE_CONFIG_DIR="$GENSEO_CFG" "$HOME/.local/bin/claude" auth status 2>/dev/null || true)"
    case "$AUTH_JSON" in *'"loggedIn": true'*|*'"loggedIn":true'*) USE_NATIVE=1;; esac
  fi
  if ! genseo_select_model_lane; then
    echo "lane=none"
    echo "error=no-model-lane"
    exit 1
  fi
  echo "lane=$GENSEO_MODEL_LANE"
  echo "writer=$GENSEO_WRITER_MODEL"
  echo "fallback=$GENSEO_WRITER_FALLBACK"
  if [ -n "${ANTHROPIC_BASE_URL:-}" ]; then
    echo "base_host=$(printf '%s' "$ANTHROPIC_BASE_URL" | sed -E 's#^[a-z]+://([^/]+).*#\1#')"
  else
    echo "base_host="
  fi
  if [ -n "${ANTHROPIC_AUTH_TOKEN:-}" ]; then echo "token_set=yes"; else echo "token_set=no"; fi
  unset ANTHROPIC_AUTH_TOKEN
  exit 0
fi

SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/model-lane-test.XXXXXX")" || exit 1
trap 'rm -rf "$SANDBOX"' EXIT
PASS=0
FAIL=0
FAKE_KEY='lane-test-secret-do-not-print'
QUOTED_KEY='quoted-lane-secret-do-not-print'

ok() { PASS=$((PASS + 1)); echo "  ok   $*"; }
bad() { FAIL=$((FAIL + 1)); echo "  FAIL $*"; }

reset_env() {
  unset NINE_ROUTER_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL CLAUDE_CONFIG_DIR USE_NATIVE
  unset GENSEO_LANE_LOCAL_UP GENSEO_LANE_MODELS_JSON GENSEO_WRITER_MODEL GENSEO_WRITER_FALLBACK
  unset GENSEO_ROUTER_BASE GENSEO_MODEL_LANE GENSEO_MODEL_LANE_ERROR GENSEO_LOCAL_ROUTER GENSEO_CFG
  export HOME="$SANDBOX"
  export GENSEO_CFG="$SANDBOX/claude-cfg"
  rm -rf "$SANDBOX/PATI" "$SANDBOX/claude-cfg" "$SANDBOX/out" "$SANDBOX/err"
  mkdir -p "$SANDBOX"
}

no_secret() { # no_secret <file> <secret> <label>
  if grep -F -q -- "$2" "$1" 2>/dev/null; then bad "$3 leaked"
  else ok "$3"; fi
}

select_lane() {
  genseo_select_model_lane >"$SANDBOX/out" 2>"$SANDBOX/err"
  return $?
}

echo "1. native wins even when local has no writer model and a key is set"
reset_env
USE_NATIVE=1
GENSEO_LANE_LOCAL_UP=1
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"ag/gemini-3.8-flash-high"}]}'
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ "${GENSEO_MODEL_LANE:-}" = "native" ] && ok "lane native" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ -z "${ANTHROPIC_AUTH_TOKEN:-}" ] && ok "native does not export router token" || bad "native exported a token"
[ ! -s "$SANDBOX/out" ] && ok "stdout empty" || bad "stdout not empty"
no_secret "$SANDBOX/out" "$FAKE_KEY" "native stdout has no key"
no_secret "$SANDBOX/err" "$FAKE_KEY" "native stderr has no key"

echo "2. local up + exact writer id → local-9router, no hosted token"
reset_env
USE_NATIVE=0
GENSEO_LANE_LOCAL_UP=1
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"ag/gemini-3.8-flash-high"},{"id":"PATI-Alpha-Plan-Review"}]}'
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ "${GENSEO_MODEL_LANE:-}" = "local-9router" ] && ok "lane local-9router" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ -z "${ANTHROPIC_AUTH_TOKEN:-}" ] && ok "local does not export token" || bad "local exported a token"
[ -z "${ANTHROPIC_BASE_URL:-}" ] && ok "local does not export base url" || bad "local exported base url"
log="$(genseo_lane_log_line)"
case "$log" in
  *'(lane: local-9router on '*' writer=PATI-Alpha-Plan-Review fallback=PATI-Fable-5)'*) ok "log line" ;;
  *) bad "log line [$log]" ;;
esac
no_secret "$SANDBOX/out" "$FAKE_KEY" "local stdout has no key"

echo "3. local up without the writer id → hosted-9router"
reset_env
USE_NATIVE=0
GENSEO_LANE_LOCAL_UP=1
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"ag/gemini-3.8-flash-high"},{"id":"PATI-Alpha-Plan-Review-extra"}]}'
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ "${GENSEO_MODEL_LANE:-}" = "hosted-9router" ] && ok "lane hosted-9router" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ "${ANTHROPIC_BASE_URL:-}" = "https://ai.patigroup.com" ] && ok "default hosted base" || bad "base ${ANTHROPIC_BASE_URL:-empty}"
[ "${ANTHROPIC_AUTH_TOKEN:-}" = "$FAKE_KEY" ] && ok "token loaded" || bad "token mismatch"
[ "${CLAUDE_CONFIG_DIR:-}" = "$SANDBOX/claude-cfg" ] && ok "lean config dir" || bad "config dir"
[ -d "$SANDBOX/claude-cfg" ] && ok "config dir created" || bad "config dir missing"
[ "${GENSEO_WRITER_FALLBACK:-}" = "PATI-Fable-5" ] && ok "default fallback" || bad "fallback ${GENSEO_WRITER_FALLBACK:-empty}"
log="$(genseo_lane_log_line)"
case "$log" in
  *'lane: hosted-9router '*) ok "log names hosted-9router" ;;
  *) bad "log line [$log]" ;;
esac
no_secret "$SANDBOX/out" "$FAKE_KEY" "hosted stdout has no key"
no_secret "$SANDBOX/err" "$FAKE_KEY" "hosted stderr has no key"
printf '%s' "$log" >"$SANDBOX/logline"
no_secret "$SANDBOX/logline" "$FAKE_KEY" "log line has no key"

echo "4. local down → hosted, including a custom base and fallback"
reset_env
USE_NATIVE=0
GENSEO_LANE_LOCAL_UP=0
GENSEO_ROUTER_BASE="https://router.example.test"
GENSEO_WRITER_FALLBACK="PATI-Other"
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ "${GENSEO_MODEL_LANE:-}" = "hosted-9router" ] && ok "lane hosted-9router" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ "${ANTHROPIC_BASE_URL:-}" = "https://router.example.test" ] && ok "custom base" || bad "base ${ANTHROPIC_BASE_URL:-empty}"
[ "${GENSEO_WRITER_FALLBACK:-}" = "PATI-Other" ] && ok "custom fallback" || bad "fallback"
log="$(genseo_lane_log_line)"
case "$log" in
  *'fallback=PATI-Other'*) ok "log shows fallback" ;;
  *) bad "log line [$log]" ;;
esac

echo "5. unparseable model list falls through to hosted"
reset_env
USE_NATIVE=0
GENSEO_LANE_LOCAL_UP=1
GENSEO_LANE_MODELS_JSON='not-json'
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ "${GENSEO_MODEL_LANE:-}" = "hosted-9router" ] && ok "lane hosted-9router" || bad "lane ${GENSEO_MODEL_LANE:-empty}"

echo "6. name field counts, a longer id does not"
reset_env
USE_NATIVE=0
GENSEO_LANE_LOCAL_UP=1
GENSEO_LANE_MODELS_JSON='{"data":[{"name":"PATI-Alpha-Plan-Review"}]}'
select_lane
[ "${GENSEO_MODEL_LANE:-}" = "local-9router" ] && ok "match on name" || bad "lane ${GENSEO_MODEL_LANE:-empty}"

echo "7. GENSEO_WRITER_MODEL override"
reset_env
USE_NATIVE=0
GENSEO_LANE_LOCAL_UP=1
GENSEO_WRITER_MODEL="PATI-Custom"
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"PATI-Alpha-Plan-Review"}]}'
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
[ "${GENSEO_MODEL_LANE:-}" = "hosted-9router" ] && ok "custom writer missing → hosted" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
reset_env
USE_NATIVE=0
GENSEO_LANE_LOCAL_UP=1
GENSEO_WRITER_MODEL="PATI-Custom"
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"PATI-Custom"}]}'
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
[ "${GENSEO_MODEL_LANE:-}" = "local-9router" ] && ok "custom writer present → local" || bad "lane ${GENSEO_MODEL_LANE:-empty}"

echo "8. no key and local missing the model → fail, no secret on stdout"
reset_env
USE_NATIVE=0
GENSEO_LANE_LOCAL_UP=1
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"ag/gemini-3.8-flash-high"}]}'
select_lane
rc=$?
[ "$rc" = 1 ] && ok "exit 1" || bad "exit $rc"
[ -z "${GENSEO_MODEL_LANE:-}" ] && ok "lane empty" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
case "${GENSEO_MODEL_LANE_ERROR:-}" in
  *'missing PATI-Alpha-Plan-Review'*'NINE_ROUTER_KEY'*) ok "error names the missing model" ;;
  *) bad "error [${GENSEO_MODEL_LANE_ERROR:-empty}]" ;;
esac
[ ! -s "$SANDBOX/out" ] && ok "stdout empty" || bad "stdout not empty"

echo "9. quoted key in ~/PATI/LLM-Wiki/.env"
reset_env
USE_NATIVE=0
GENSEO_LANE_LOCAL_UP=0
mkdir -p "$SANDBOX/PATI/LLM-Wiki"
printf '%s\n' 'export NINE_ROUTER_KEY="'"$QUOTED_KEY"'"' >"$SANDBOX/PATI/LLM-Wiki/.env"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ "${GENSEO_MODEL_LANE:-}" = "hosted-9router" ] && ok "lane hosted-9router" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ "${ANTHROPIC_AUTH_TOKEN:-}" = "$QUOTED_KEY" ] && ok "quoted key loaded" || bad "quoted key mismatch"
no_secret "$SANDBOX/out" "$QUOTED_KEY" "env-file stdout has no key"
no_secret "$SANDBOX/err" "$QUOTED_KEY" "env-file stderr has no key"

echo "10. runners source the helper and pass the writer env to claude"
for rel in scripts/run_landing_headless.sh scripts/run_ticket_headless.sh; do
  file="$ROOT/$rel"
  grep -q 'scripts/genseo_model_lane.sh' "$file" && ok "$rel sources helper" || bad "$rel missing source"
  grep -q 'genseo_select_model_lane' "$file" && ok "$rel selects lane" || bad "$rel missing select"
  grep -q 'genseo_lane_log_line' "$file" && ok "$rel logs lane" || bad "$rel missing log"
  grep -q -- '--model "$GENSEO_WRITER_MODEL"' "$file" && ok "$rel writer model" || bad "$rel writer flag"
  grep -q -- '--fallback-model "$GENSEO_WRITER_FALLBACK"' "$file" && ok "$rel fallback model" || bad "$rel fallback flag"
  if grep -q 'PATI-Alpha-Plan-Review' "$file"; then bad "$rel still hardcodes the writer model"; else ok "$rel no hardcoded writer"; fi
  if grep -q 'curl -s -m 3 -o /dev/null http://127.0.0.1:20128/' "$file"; then bad "$rel still uses the up/down-only gate"; else ok "$rel gate moved"; fi
done
grep -q 'hosted-9router' "$ROOT/DAILY-RUN.md" && ok "DAILY-RUN names hosted-9router" || bad "DAILY-RUN lane note"
grep -q 'no PATI writer alias' "$ROOT/DAILY-RUN.md" && ok "DAILY-RUN notes missing PATI alias" || bad "DAILY-RUN alias note"
ticket='- [ ] listicle | wellnessnest | product=pure-shilajit-gold-resin · angle: Resin vs capsules vs gummies: N things to compare before you pick a shilajit format · audience: adults comparing shilajit formats (added 2026-10-09)'
grep -qxF -- "$ticket" "$ROOT/daily-landing-tickets.md" && ok "gold-resin ticket reopened" || bad "gold-resin ticket line"
if grep -q 'FAILED 2026-10-10' "$ROOT/daily-landing-tickets.md"; then bad "FAILED tag still on the queue"; else ok "FAILED tag cleared"; fi

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" = 0 ]

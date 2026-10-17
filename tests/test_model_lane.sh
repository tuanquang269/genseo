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
  unset GENSEO_PERMISSION_MODE GENSEO_MODEL_MAP_JSON GENSEO_MODEL_MAP_PY
  unset ANTHROPIC_DEFAULT_OPUS_MODEL ANTHROPIC_DEFAULT_FABLE_MODEL ANTHROPIC_API_KEY
  unset GENSEO_PREPARED_MODEL GENSEO_PREPARED_ARGS
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

echo "1. native wins for a non-PATI writer and fallback, even when local has no writer model and a key is set"
reset_env
USE_NATIVE=1
GENSEO_WRITER_MODEL="claude-sonnet-4-6"
GENSEO_WRITER_FALLBACK="claude-haiku-4-5"
GENSEO_LANE_LOCAL_UP=1
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"ag/gemini-3.8-flash-high"}]}'
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ "${GENSEO_MODEL_LANE:-}" = "native" ] && ok "lane native" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ "${USE_NATIVE:-}" = "1" ] && ok "login flag kept" || bad "USE_NATIVE was ${USE_NATIVE:-empty}"
[ -z "${GENSEO_PERMISSION_MODE:-}" ] && ok "native leaves permission mode to the CLI" || bad "permission ${GENSEO_PERMISSION_MODE:-empty}"
[ -z "${ANTHROPIC_DEFAULT_OPUS_MODEL:-}" ] && ok "native sonnet does not pin opus" || bad "opus pin leaked into native"
[ -z "${ANTHROPIC_DEFAULT_FABLE_MODEL:-}" ] && ok "native sonnet does not pin fable" || bad "fable pin leaked into native"
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
[ "${GENSEO_PERMISSION_MODE:-}" = "dontAsk" ] && ok "local permission dontAsk" || bad "permission ${GENSEO_PERMISSION_MODE:-empty}"
[ -z "${ANTHROPIC_AUTH_TOKEN:-}" ] && ok "local does not export token" || bad "local exported a token"
[ -z "${ANTHROPIC_BASE_URL:-}" ] && ok "local does not export base url" || bad "local exported base url"
[ -z "${ANTHROPIC_API_KEY:-}" ] && ok "local does not set an Anthropic API key" || bad "local set ANTHROPIC_API_KEY"
[ "${ANTHROPIC_DEFAULT_OPUS_MODEL:-}" = "claude-opus-5-5" ] && ok "planner pin is opus 5.5" || bad "opus pin ${ANTHROPIC_DEFAULT_OPUS_MODEL:-empty}"
[ "${ANTHROPIC_DEFAULT_FABLE_MODEL:-}" = "claude-fable-5" ] && ok "fallback pin is fable 5" || bad "fable pin ${ANTHROPIC_DEFAULT_FABLE_MODEL:-empty}"
log="$(genseo_lane_log_line)"
case "$log" in
  *'(lane: local-9router on '*' writer=PATI-Alpha-Plan-Review fallback=PATI-Fable-5 permission=dontAsk)'*) ok "log line" ;;
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
[ "${GENSEO_PERMISSION_MODE:-}" = "dontAsk" ] && ok "hosted permission dontAsk" || bad "permission ${GENSEO_PERMISSION_MODE:-empty}"
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

echo "4. local down → hosted, including a custom base and a mapped fallback"
reset_env
USE_NATIVE=0
GENSEO_LANE_LOCAL_UP=0
GENSEO_ROUTER_BASE="https://router.example.test"
cat >"$SANDBOX/map-other.json" <<'EOF'
{"modelOverrides":{"claude-opus-5-5":"PATI-Alpha-Plan-Review","claude-haiku-4-5":"PATI-Other"}}
EOF
GENSEO_MODEL_MAP_JSON="$SANDBOX/map-other.json"
GENSEO_WRITER_FALLBACK="PATI-Other"
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ "${GENSEO_MODEL_LANE:-}" = "hosted-9router" ] && ok "lane hosted-9router" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ "${ANTHROPIC_BASE_URL:-}" = "https://router.example.test" ] && ok "custom base" || bad "base ${ANTHROPIC_BASE_URL:-empty}"
[ "${GENSEO_WRITER_FALLBACK:-}" = "PATI-Other" ] && ok "custom fallback" || bad "fallback"
[ "${ANTHROPIC_DEFAULT_OPUS_MODEL:-}" = "claude-opus-5-5" ] && ok "mapped writer pins opus" || bad "opus pin ${ANTHROPIC_DEFAULT_OPUS_MODEL:-empty}"
[ -z "${ANTHROPIC_DEFAULT_FABLE_MODEL:-}" ] && ok "haiku fallback does not pin fable" || bad "fable pin ${ANTHROPIC_DEFAULT_FABLE_MODEL:-empty}"
[ -z "${ANTHROPIC_API_KEY:-}" ] && ok "hosted does not set an Anthropic API key" || bad "hosted set ANTHROPIC_API_KEY"
log="$(genseo_lane_log_line)"
case "$log" in
  *'fallback=PATI-Other'*) ok "log shows fallback" ;;
  *) bad "log line [$log]" ;;
esac
claude_log="$(genseo_claude_model_log_line)"
case "$claude_log" in
  *'writer=claude-opus-5-5 fallback=claude-haiku-4-5 gateway=PATI-Alpha-Plan-Review/PATI-Other'*) ok "claude log names both ids" ;;
  *) bad "claude log [$claude_log]" ;;
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
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"PATI-Custom"}]}'
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 1 ] && ok "unmapped alias exits 1" || bad "exit $rc"
[ -z "${GENSEO_MODEL_LANE:-}" ] && ok "unmapped alias does not pick a lane" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ -z "${ANTHROPIC_AUTH_TOKEN:-}" ] && ok "unmapped alias does not export a token" || bad "unmapped exported a token"
[ -z "${ANTHROPIC_BASE_URL:-}" ] && ok "unmapped alias does not export a base url" || bad "unmapped exported a base url"
[ -z "${ANTHROPIC_API_KEY:-}" ] && ok "unmapped alias does not set an Anthropic API key" || bad "unmapped set ANTHROPIC_API_KEY"
case "${GENSEO_MODEL_LANE_ERROR:-}" in
  *'unrecognized model: PATI-Custom'*'modelOverrides'*'genseo_model_map.json'*'unrecognized_model'*) ok "error names the unmapped alias" ;;
  *) bad "error [${GENSEO_MODEL_LANE_ERROR:-empty}]" ;;
esac
reset_env
USE_NATIVE=0
GENSEO_LANE_LOCAL_UP=1
cat >"$SANDBOX/map-custom.json" <<'EOF'
{"modelOverrides":{"claude-haiku-4-5":"PATI-Custom","claude-fable-5":"PATI-Fable-5"}}
EOF
GENSEO_MODEL_MAP_JSON="$SANDBOX/map-custom.json"
GENSEO_WRITER_MODEL="PATI-Custom"
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"PATI-Custom"}]}'
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
[ "${GENSEO_MODEL_LANE:-}" = "local-9router" ] && ok "mapped custom writer present → local" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ "${ANTHROPIC_DEFAULT_OPUS_MODEL:-}" = "" ] && ok "custom haiku writer does not pin opus" || bad "opus pin ${ANTHROPIC_DEFAULT_OPUS_MODEL:-empty}"
resolved="$(genseo_claude_model_id "$GENSEO_WRITER_MODEL")"
[ "$resolved" = "claude-haiku-4-5" ] && ok "custom map resolves the writer" || bad "resolved $resolved"

echo "8. no key and local missing the model → fail, no secret on stdout"
reset_env
USE_NATIVE=0
GENSEO_LANE_LOCAL_UP=1
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"ag/gemini-3.8-flash-high"}]}'
select_lane
rc=$?
[ "$rc" = 1 ] && ok "exit 1" || bad "exit $rc"
[ -z "${GENSEO_MODEL_LANE:-}" ] && ok "lane empty" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ -z "${GENSEO_PERMISSION_MODE:-}" ] && ok "failure does not pin dontAsk" || bad "permission ${GENSEO_PERMISSION_MODE:-empty}"
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
  bash -n "$file" && ok "$rel parses" || bad "$rel does not parse"
  grep -q 'scripts/genseo_model_lane.sh' "$file" && ok "$rel sources helper" || bad "$rel missing source"
  grep -q 'genseo_select_model_lane' "$file" && ok "$rel selects lane" || bad "$rel missing select"
  grep -q 'genseo_lane_log_line' "$file" && ok "$rel logs lane" || bad "$rel missing log"
  grep -q 'genseo_run_writer_with_shape_fallback' "$file" && ok "$rel shape fallback" || bad "$rel missing shape fallback"
  grep -q -- '--fallback-model "$GENSEO_WRITER_FALLBACK"' "$file" && ok "$rel fallback model" || bad "$rel fallback flag"
  if grep -q 'PATI-Alpha-Plan-Review' "$file"; then bad "$rel still hardcodes the writer model"; else ok "$rel no hardcoded writer"; fi
  if grep -q 'curl -s -m 3 -o /dev/null http://127.0.0.1:20128/' "$file"; then bad "$rel still uses the up/down-only gate"; else ok "$rel gate moved"; fi
  grep -F -q 'PATI-*' "$file" && ok "$rel documents PATI-* skip" || bad "$rel missing PATI-* skip note"
  grep -F -q 'unrecognized_model' "$file" && ok "$rel names unrecognized_model" || bad "$rel missing unrecognized_model"
done
grep -q 'genseo_prepare_writer_args' "$ROOT/scripts/genseo_model_lane.sh" \
  && ok "helper rewrites model ids before exec" || bad "helper missing prepare"
if grep -q -- '--model "$GENSEO_WRITER_MODEL"' "$ROOT/scripts/genseo_model_lane.sh" \
  || grep -q -- '--model "$GENSEO_WRITER_FALLBACK"' "$ROOT/scripts/genseo_model_lane.sh"; then
  bad "helper still passes a raw gateway alias to --model"
else
  ok "helper does not pass a raw gateway alias to --model"
fi
grep -q 'modelOverrides' "$ROOT/scripts/genseo_model_map.json" \
  && ok "map file has modelOverrides" || bad "map file missing modelOverrides"
grep -q 'genseo_claude_model_log_line' "$ROOT/scripts/run_landing_headless.sh" \
  && ok "landing logs the claude model ids" || bad "landing missing claude model log"
grep -q 'genseo_claude_model_log_line' "$ROOT/scripts/run_ticket_headless.sh" \
  && ok "article logs the claude model ids" || bad "article missing claude model log"
grep -q 'GENSEO_WRITER_SHAPE_RETRY' "$ROOT/scripts/genseo_model_lane.sh" \
  && ok "helper stops after one re-exec" || bad "helper missing retry guard"
grep -F -q 'PATI-*' "$ROOT/scripts/genseo_model_lane.sh" && ok "helper documents PATI-* skip" || bad "helper missing PATI-* skip"
grep -F -q 'unrecognized_model' "$ROOT/scripts/genseo_model_lane.sh" && ok "helper names unrecognized_model" || bad "helper missing unrecognized_model"
grep -F -q '[ "${GENSEO_MODEL_LANE:-}" = "native" ]' "$ROOT/scripts/run_ticket_headless.sh" \
  && ok "ticket runner invokes on chosen lane" || bad "ticket runner still keys the invocation off USE_NATIVE"
if grep -q 'if \[ "\$USE_NATIVE" = "1" \]' "$ROOT/scripts/run_ticket_headless.sh"; then
  bad "ticket runner still branches on raw USE_NATIVE"
else
  ok "ticket runner does not branch on raw USE_NATIVE"
fi
grep -q 'hosted-9router' "$ROOT/DAILY-RUN.md" && ok "DAILY-RUN names hosted-9router" || bad "DAILY-RUN lane note"
grep -q 'no PATI writer alias' "$ROOT/DAILY-RUN.md" && ok "DAILY-RUN notes missing PATI alias" || bad "DAILY-RUN alias note"
grep -F -q 'never uses the native Claude login lane' "$ROOT/DAILY-RUN.md" && ok "DAILY-RUN skips native for PATI" || bad "DAILY-RUN native-skip note"
grep -F -q 'unrecognized_model' "$ROOT/DAILY-RUN.md" && ok "DAILY-RUN names unrecognized_model" || bad "DAILY-RUN unrecognized_model note"
grep -F -q -- '--permission-mode "$GENSEO_PERMISSION_MODE"' "$ROOT/scripts/run_ticket_headless.sh" \
  && ok "ticket runner passes permission mode" || bad "ticket runner missing permission mode"
grep -F -q 'GENSEO_PERMISSION_MODE:=dontAsk' "$ROOT/scripts/run_ticket_headless.sh" \
  && ok "ticket runner defaults dontAsk" || bad "ticket runner missing dontAsk default"
if awk '/GENSEO_MODEL_LANE:-}" = "native"/,/^else$/' "$ROOT/scripts/run_ticket_headless.sh" | grep -q 'permission-mode'; then
  bad "ticket native branch passes permission-mode"
else
  ok "ticket native branch leaves the CLI permission mode"
fi
grep -F -q -- '--permission-mode "$GENSEO_PERMISSION_MODE"' "$ROOT/scripts/run_landing_headless.sh" \
  && ok "landing runner passes permission mode" || bad "landing runner missing permission mode"
grep -F -q 'GENSEO_PERMISSION_MODE:=dontAsk' "$ROOT/scripts/run_landing_headless.sh" \
  && ok "landing runner defaults dontAsk" || bad "landing runner missing dontAsk default"
grep -F -q 'permission-mode dontAsk' "$ROOT/DAILY-RUN.md" && ok "DAILY-RUN names dontAsk" || bad "DAILY-RUN dontAsk note"
grep -F -q 'Bash safety service' "$ROOT/DAILY-RUN.md" && ok "DAILY-RUN names the Bash safety block" || bad "DAILY-RUN Bash safety note"
grep -F -q 'GENSEO_PERMISSION_MODE="dontAsk"' "$ROOT/scripts/genseo_model_lane.sh" \
  && ok "helper sets dontAsk" || bad "helper missing dontAsk"
ticket='- [DRAFT 2026-10-12 page 166173573435] listicle | wellnessnest | product=pure-shilajit-gold-resin · angle: Resin vs capsules vs gummies: N things to compare before you pick a shilajit format · audience: adults comparing shilajit formats (added 2026-10-09)'
grep -qxF -- "$ticket" "$ROOT/daily-landing-tickets.md" && ok "gold-resin stays the unpublished draft" || bad "gold-resin draft line"
if grep -qE '^- \[ \] .*pure-shilajit-gold-resin.*Resin vs capsules vs gummies' "$ROOT/daily-landing-tickets.md"; then
  bad "gold-resin draft angle is open again"
else
  ok "gold-resin draft angle is not an open ticket"
fi
if grep -q 'FAILED 2026-10-10' "$ROOT/daily-landing-tickets.md"; then bad "FAILED tag still on the queue"; else ok "FAILED tag cleared"; fi
if grep -q 'FAILED 2026-10-11' "$ROOT/daily-landing-tickets.md"; then bad "FAILED 2026-10-11 tag still on the queue"; else ok "2026-10-11 FAILED tag cleared"; fi

echo "11. USE_NATIVE=1 + default PATI writer + local lists the id → local, not native"
reset_env
USE_NATIVE=1
GENSEO_LANE_LOCAL_UP=1
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"ag/gemini-3.8-flash-high"},{"id":"PATI-Alpha-Plan-Review"}]}'
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ "${GENSEO_MODEL_LANE:-}" = "local-9router" ] && ok "lane local-9router" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ "${GENSEO_PERMISSION_MODE:-}" = "dontAsk" ] && ok "PATI local permission dontAsk" || bad "permission ${GENSEO_PERMISSION_MODE:-empty}"
[ "${USE_NATIVE:-}" = "0" ] && ok "native flag cleared" || bad "USE_NATIVE=${USE_NATIVE:-empty}"
[ "${GENSEO_WRITER_MODEL:-}" = "PATI-Alpha-Plan-Review" ] && ok "default writer" || bad "writer ${GENSEO_WRITER_MODEL:-empty}"
[ "${GENSEO_WRITER_FALLBACK:-}" = "PATI-Fable-5" ] && ok "default fallback" || bad "fallback ${GENSEO_WRITER_FALLBACK:-empty}"
[ -z "${ANTHROPIC_AUTH_TOKEN:-}" ] && ok "local does not export token" || bad "local exported a token"
[ -z "${ANTHROPIC_BASE_URL:-}" ] && ok "local does not export base url" || bad "local exported base url"
[ "${ANTHROPIC_DEFAULT_OPUS_MODEL:-}" = "claude-opus-5-5" ] && ok "PATI local pins opus" || bad "opus pin ${ANTHROPIC_DEFAULT_OPUS_MODEL:-empty}"
[ "${ANTHROPIC_DEFAULT_FABLE_MODEL:-}" = "claude-fable-5" ] && ok "PATI local pins fable" || bad "fable pin ${ANTHROPIC_DEFAULT_FABLE_MODEL:-empty}"
no_secret "$SANDBOX/out" "$FAKE_KEY" "PATI-local stdout has no key"
no_secret "$SANDBOX/err" "$FAKE_KEY" "PATI-local stderr has no key"

echo "12. USE_NATIVE=1 + PATI writer + local missing the id + key → hosted"
reset_env
USE_NATIVE=1
GENSEO_WRITER_MODEL="PATI-Fable-5"
GENSEO_LANE_LOCAL_UP=1
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"ag/gemini-3.8-flash-high"}]}'
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ "${GENSEO_MODEL_LANE:-}" = "hosted-9router" ] && ok "lane hosted-9router" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ "${GENSEO_PERMISSION_MODE:-}" = "dontAsk" ] && ok "PATI hosted permission dontAsk" || bad "permission ${GENSEO_PERMISSION_MODE:-empty}"
[ "${USE_NATIVE:-}" = "0" ] && ok "native flag cleared" || bad "USE_NATIVE=${USE_NATIVE:-empty}"
[ "${ANTHROPIC_BASE_URL:-}" = "https://ai.patigroup.com" ] && ok "default hosted base" || bad "base ${ANTHROPIC_BASE_URL:-empty}"
[ "${ANTHROPIC_AUTH_TOKEN:-}" = "$FAKE_KEY" ] && ok "token loaded" || bad "token mismatch"
[ "${GENSEO_WRITER_MODEL:-}" = "PATI-Fable-5" ] && ok "writer kept" || bad "writer ${GENSEO_WRITER_MODEL:-empty}"
no_secret "$SANDBOX/out" "$FAKE_KEY" "PATI-hosted stdout has no key"
no_secret "$SANDBOX/err" "$FAKE_KEY" "PATI-hosted stderr has no key"

echo "13. USE_NATIVE=1 + PATI writer + local down + key → hosted"
reset_env
USE_NATIVE=1
GENSEO_LANE_LOCAL_UP=0
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ "${GENSEO_MODEL_LANE:-}" = "hosted-9router" ] && ok "lane hosted-9router" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ "${USE_NATIVE:-}" = "0" ] && ok "native flag cleared" || bad "USE_NATIVE=${USE_NATIVE:-empty}"
[ "${ANTHROPIC_AUTH_TOKEN:-}" = "$FAKE_KEY" ] && ok "token loaded" || bad "token mismatch"
no_secret "$SANDBOX/out" "$FAKE_KEY" "PATI-down stdout has no key"
no_secret "$SANDBOX/err" "$FAKE_KEY" "PATI-down stderr has no key"

echo "14. USE_NATIVE=1 + PATI writer + local missing + no key → fail, no secret"
reset_env
USE_NATIVE=1
GENSEO_LANE_LOCAL_UP=1
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"ag/gemini-3.8-flash-high"}]}'
select_lane
rc=$?
[ "$rc" = 1 ] && ok "exit 1" || bad "exit $rc"
[ -z "${GENSEO_MODEL_LANE:-}" ] && ok "lane empty" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ "${USE_NATIVE:-}" = "0" ] && ok "native flag cleared" || bad "USE_NATIVE=${USE_NATIVE:-empty}"
case "${GENSEO_MODEL_LANE_ERROR:-}" in
  *'missing PATI-Alpha-Plan-Review'*'NINE_ROUTER_KEY'*) ok "error names the missing model" ;;
  *) bad "error [${GENSEO_MODEL_LANE_ERROR:-empty}]" ;;
esac
[ -z "${ANTHROPIC_AUTH_TOKEN:-}" ] && ok "no token exported" || bad "token exported on failure"
[ ! -s "$SANDBOX/out" ] && ok "stdout empty" || bad "stdout not empty"

echo "15. USE_NATIVE=1 + non-PATI writer + PATI fallback skips native"
reset_env
USE_NATIVE=1
GENSEO_WRITER_MODEL="claude-sonnet-4-6"
GENSEO_WRITER_FALLBACK="PATI-Fable-5"
GENSEO_LANE_LOCAL_UP=1
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"claude-sonnet-4-6"}]}'
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ "${GENSEO_MODEL_LANE:-}" = "local-9router" ] && ok "fallback PATI + local id → local" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ "${USE_NATIVE:-}" = "0" ] && ok "native flag cleared" || bad "USE_NATIVE=${USE_NATIVE:-empty}"
reset_env
USE_NATIVE=1
GENSEO_WRITER_MODEL="claude-sonnet-4-6"
GENSEO_WRITER_FALLBACK="PATI-Fable-5"
GENSEO_LANE_LOCAL_UP=1
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"ag/gemini-3.8-flash-high"}]}'
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
[ "${GENSEO_MODEL_LANE:-}" = "hosted-9router" ] && ok "fallback PATI + missing id → hosted" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ "${USE_NATIVE:-}" = "0" ] && ok "native flag cleared" || bad "USE_NATIVE=${USE_NATIVE:-empty}"
no_secret "$SANDBOX/out" "$FAKE_KEY" "fallback-PATI stdout has no key"
no_secret "$SANDBOX/err" "$FAKE_KEY" "fallback-PATI stderr has no key"

echo "16. a later PATI substring is not a router alias, so native still wins"
reset_env
USE_NATIVE=1
GENSEO_WRITER_MODEL="claude-PATI-not-a-prefix"
GENSEO_WRITER_FALLBACK="claude-haiku-4-5"
GENSEO_LANE_LOCAL_UP=1
GENSEO_LANE_MODELS_JSON='{"data":[{"id":"PATI-Alpha-Plan-Review"}]}'
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ "${GENSEO_MODEL_LANE:-}" = "native" ] && ok "lane native" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ "${USE_NATIVE:-}" = "1" ] && ok "login flag kept" || bad "USE_NATIVE=${USE_NATIVE:-empty}"
[ -z "${GENSEO_PERMISSION_MODE:-}" ] && ok "substring native leaves permission mode" || bad "permission ${GENSEO_PERMISSION_MODE:-empty}"
[ -z "${ANTHROPIC_AUTH_TOKEN:-}" ] && ok "native does not export router token" || bad "native exported a token"
[ -z "${ANTHROPIC_DEFAULT_OPUS_MODEL:-}" ] && ok "native claude id does not pin opus" || bad "opus pin leaked"
[ -z "${ANTHROPIC_DEFAULT_FABLE_MODEL:-}" ] && ok "native claude id does not pin fable" || bad "fable pin leaked"
no_secret "$SANDBOX/out" "$FAKE_KEY" "substring stdout has no key"
no_secret "$SANDBOX/err" "$FAKE_KEY" "substring stderr has no key"

echo "17. a stale auto permission mode cannot survive lane selection"
reset_env
USE_NATIVE=0
GENSEO_LANE_LOCAL_UP=0
GENSEO_PERMISSION_MODE="auto"
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ "${GENSEO_MODEL_LANE:-}" = "hosted-9router" ] && ok "lane hosted-9router" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ "${GENSEO_PERMISSION_MODE:-}" = "dontAsk" ] && ok "stale auto overwritten" || bad "permission ${GENSEO_PERMISSION_MODE:-empty}"
log="$(genseo_lane_log_line)"
case "$log" in
  *'permission=dontAsk'*) ok "log shows dontAsk" ;;
  *) bad "log line [$log]" ;;
esac
no_secret "$SANDBOX/out" "$FAKE_KEY" "stale-auto stdout has no key"
no_secret "$SANDBOX/err" "$FAKE_KEY" "stale-auto stderr has no key"
reset_env
USE_NATIVE=1
GENSEO_WRITER_MODEL="claude-sonnet-4-6"
GENSEO_WRITER_FALLBACK="claude-haiku-4-5"
GENSEO_PERMISSION_MODE="dontAsk"
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
[ "${GENSEO_MODEL_LANE:-}" = "native" ] && ok "lane native" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
[ -z "${GENSEO_PERMISSION_MODE:-}" ] && ok "native clears a stale dontAsk" || bad "permission ${GENSEO_PERMISSION_MODE:-empty}"
log="$(genseo_lane_log_line)"
case "$log" in
  *'permission=cli-default'*) ok "native log says cli-default" ;;
  *) bad "log line [$log]" ;;
esac
no_secret "$SANDBOX/out" "$FAKE_KEY" "stale-dontAsk stdout has no key"
no_secret "$SANDBOX/err" "$FAKE_KEY" "stale-dontAsk stderr has no key"

echo "18. default aliases resolve to Claude ids and settings keep the gateway alias"
reset_env
writer_id="$(genseo_claude_model_id "PATI-Alpha-Plan-Review")"
[ "$writer_id" = "claude-opus-5-5" ] && ok "planner alias maps to opus 5.5" || bad "planner id $writer_id"
fallback_id="$(genseo_claude_model_id "PATI-Fable-5")"
[ "$fallback_id" = "claude-fable-5" ] && ok "fable alias maps to fable 5" || bad "fable id $fallback_id"
plain_id="$(genseo_claude_model_id "claude-sonnet-4-6")"
[ "$plain_id" = "claude-sonnet-4-6" ] && ok "claude id passes through" || bad "passthrough $plain_id"
merged="$(genseo_merge_model_settings "PATI-Alpha-Plan-Review" "PATI-Fable-5" '{"claudeMdExcludes":["/tmp/CLAUDE.md"]}')"
python3 - "$merged" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
if data.get("claudeMdExcludes") != ["/tmp/CLAUDE.md"]:
    sys.exit("excludes dropped: %r" % data)
overrides = data.get("modelOverrides") or {}
if overrides.get("claude-opus-5-5") != "PATI-Alpha-Plan-Review":
    sys.exit("planner override missing: %r" % overrides)
if overrides.get("claude-fable-5") != "PATI-Fable-5":
    sys.exit("fable override missing: %r" % overrides)
if "ANTHROPIC_API_KEY" in data or "apiKey" in data:
    sys.exit("settings carry a billing key")
PY
[ "$?" = 0 ] && ok "settings merge keeps excludes and gateway aliases" || bad "settings merge"
if genseo_claude_model_id "PATI-No-Such" >/dev/null 2>/dev/null; then
  bad "unmapped alias resolved"
else
  case "${GENSEO_MODEL_LANE_ERROR:-}" in
    *'unrecognized model: PATI-No-Such'*'/v1/models listing is not enough'*) ok "unmapped alias fails closed" ;;
    *) bad "unmapped error [${GENSEO_MODEL_LANE_ERROR:-empty}]" ;;
  esac
fi

echo "19. a leaked API key is cleared before the lane can use it"
reset_env
export ANTHROPIC_API_KEY="on-demand-key-do-not-use"
USE_NATIVE=0
GENSEO_LANE_LOCAL_UP=0
NINE_ROUTER_KEY="$FAKE_KEY"
select_lane
rc=$?
[ "$rc" = 0 ] && ok "exit 0" || bad "exit $rc"
[ -z "${ANTHROPIC_API_KEY:-}" ] && ok "select unsets ANTHROPIC_API_KEY" || bad "API key survived select"
[ "${GENSEO_MODEL_LANE:-}" = "hosted-9router" ] && ok "lane still hosted" || bad "lane ${GENSEO_MODEL_LANE:-empty}"
grep -F -q 'unset ANTHROPIC_API_KEY' "$ROOT/scripts/genseo_model_lane.sh" \
  && ok "helper unsets the API key" || bad "helper does not unset the API key"
grep -F -q 'env -u ANTHROPIC_API_KEY' "$ROOT/scripts/genseo_model_lane.sh" \
  && ok "writer exec strips the API key" || bad "writer exec can inherit the API key"
if grep -F -q 's/ *$//' "$ROOT/scripts/genseo_model_lane.sh"; then
  bad "error path still strips with BSD sed"
else
  ok "error path does not use BSD sed"
fi

echo "20. an error file with no trailing newline still yields the message"
printf '%s' 'unrecognized model: PATI-Custom modelOverrides' >"$SANDBOX/nonewline"
got="$(_genseo_collapse_file "$SANDBOX/nonewline")"
[ "$got" = "unrecognized model: PATI-Custom modelOverrides" ] && ok "no-newline error kept" || bad "collapsed [$got]"
printf '%s\n%s\n' 'line one' 'line two' >"$SANDBOX/twoline"
got="$(_genseo_collapse_file "$SANDBOX/twoline")"
[ "$got" = "line one line two" ] && ok "two error lines joined" || bad "collapsed [$got]"

echo "21. settings that are not JSON fail in the parent shell"
reset_env
GENSEO_WRITER_MODEL="PATI-Alpha-Plan-Review"
GENSEO_WRITER_FALLBACK="PATI-Fable-5"
if genseo_prepare_writer_args "$GENSEO_WRITER_MODEL" -p "prompt" --settings 'not-json' --fallback-model "$GENSEO_WRITER_FALLBACK"; then
  bad "bad settings returned 0"
else
  ok "bad settings returns 1"
fi
case "${GENSEO_MODEL_LANE_ERROR:-}" in
  *'model settings are not a JSON object'*) ok "parent keeps the settings error" ;;
  *) bad "settings error [${GENSEO_MODEL_LANE_ERROR:-empty}]" ;;
esac

echo "22. native claude ids are not rewritten and do not inherit a stale pin"
reset_env
GENSEO_WRITER_MODEL="claude-sonnet-4-6"
GENSEO_WRITER_FALLBACK="claude-haiku-4-5"
export ANTHROPIC_DEFAULT_OPUS_MODEL="stale-opus"
export ANTHROPIC_DEFAULT_FABLE_MODEL="stale-fable"
if genseo_prepare_writer_args "$GENSEO_WRITER_MODEL" \
  -p "prompt" \
  --fallback-model "$GENSEO_WRITER_FALLBACK" \
  --settings '{"claudeMdExcludes":["/tmp/CLAUDE.md"]}'; then
  ok "native prepare exit 0"
else
  bad "native prepare failed [${GENSEO_MODEL_LANE_ERROR:-empty}]"
fi
[ "${GENSEO_PREPARED_MODEL:-}" = "claude-sonnet-4-6" ] && ok "native model unchanged" || bad "model ${GENSEO_PREPARED_MODEL:-empty}"
[ -z "${ANTHROPIC_DEFAULT_OPUS_MODEL:-}" ] && ok "prepare clears a stale opus pin" || bad "opus pin ${ANTHROPIC_DEFAULT_OPUS_MODEL:-empty}"
[ -z "${ANTHROPIC_DEFAULT_FABLE_MODEL:-}" ] && ok "prepare clears a stale fable pin" || bad "fable pin ${ANTHROPIC_DEFAULT_FABLE_MODEL:-empty}"
if python3 - "${GENSEO_PREPARED_ARGS[@]}" <<'PY'
import json, sys
args = sys.argv[1:]
if "--model" not in args or args[args.index("--model") + 1] != "claude-sonnet-4-6":
    sys.exit("model %r" % args)
if "--fallback-model" not in args or args[args.index("--fallback-model") + 1] != "claude-haiku-4-5":
    sys.exit("fallback %r" % args)
blob = args[args.index("--settings") + 1]
data = json.loads(blob)
if "modelOverrides" in data:
    sys.exit("native settings gained overrides: %r" % data)
if data.get("claudeMdExcludes") != ["/tmp/CLAUDE.md"]:
    sys.exit("excludes %r" % data)
if "ANTHROPIC_API_KEY" in data or "apiKey" in data:
    sys.exit("billing key in settings")
PY
then ok "native settings stay free of gateway overrides"
else bad "native settings"; fi

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" = 0 ]

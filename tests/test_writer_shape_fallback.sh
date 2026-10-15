#!/bin/bash
# Wrong-shape writer responses re-exec once on GENSEO_WRITER_FALLBACK.
# Landing 2026-10-12 09:19: HTTP 200 OpenAI chat.completion, Claude exited with
# "JSON but not a Message" and did not use --fallback-model. No Shopify, no
# network, no real claude. Gold-resin stays a DRAFT; this test does not reopen it.
#   bash tests/test_writer_shape_fallback.sh
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/scripts/genseo_writer_response.py"
# shellcheck source=../scripts/genseo_model_lane.sh
. "$ROOT/scripts/genseo_model_lane.sh"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/writer-shape.XXXXXX")" || exit 1
trap 'rm -rf "$TMP"' EXIT
PASS=0
FAIL=0
STUB="$TMP/claude"
CALLS="$TMP/calls"
MODE="$TMP/mode"
LOG="$TMP/run.log"
export CALLS MODE

ok() { PASS=$((PASS + 1)); echo "  ok    $*"; }
bad() { FAIL=$((FAIL + 1)); echo "  FAIL  $*"; }

py_rc() { # py_rc <want> <label> [script args...]
  local want="$1" label="$2" rc
  shift 2
  python3 "$PY" "$@" >/dev/null 2>"$TMP/py.err"
  rc=$?
  if [ "$rc" = "$want" ]; then ok "$label"
  else bad "$label (rc=$rc)"; sed 's/^/        | /' "$TMP/py.err"; fi
}

cat > "$STUB" <<'EOF'
#!/bin/bash
{
  printf 'CALL\n'
  printf '%s\n' "$@"
  printf 'ENV draft=%s live=%s\n' "${GENSEO_LANDING_DRAFT:-}" "${GENSEO_LANDING_LIVE_OK:-}"
  printf 'END\n'
} >> "$CALLS"
n="$(grep -c '^CALL$' "$CALLS" || true)"
mode="$(cat "$MODE")"
case "$mode" in
  anthropic-ok)
    printf '%s\n' '{"id":"msg_1","type":"message","role":"assistant","model":"claude","content":[{"type":"text","text":"ok"}]}'
    exit 0
    ;;
  phrase-exit-0)
    printf '%s\n' 'body is JSON but not a Message'
    exit 0
    ;;
  phrase-then-ok|phrase-twice|openai-then-ok|openai-twice)
    if [ "$n" = "1" ]; then
      if [ "$mode" = "openai-then-ok" ] || [ "$mode" = "openai-twice" ]; then
        printf '%s\n' '{"id":"chatcmpl-1","object":"chat.completion","choices":[{"index":0,"message":{"role":"assistant","content":"x"},"finish_reason":"stop"}]}'
      else
        printf '%s\n' 'API Error: body is JSON but not a Message'
      fi
      if [ "$mode" = "phrase-twice" ] || [ "$mode" = "openai-twice" ]; then exit 7; fi
      exit 1
    fi
    if [ "$mode" = "phrase-twice" ] || [ "$mode" = "openai-twice" ]; then
      printf '%s\n' 'API Error: body is JSON but not a Message'
      exit 7
    fi
    printf '%s\n' 'SPEC: landing_drafts/stub.json'
    exit 0
    ;;
  anthropic-error)
    printf '%s\n' '{"type":"error","error":{"type":"overloaded_error","message":"Overloaded"}}'
    exit 1
    ;;
  other-fail)
    printf '%s\n' 'input exceeds the context window'
    printf '%s\n' '{"model":"PATI-Alpha-Plan-Review","query_source":"sdk"}'
    exit 1
    ;;
  always-fail)
    printf '%s\n' 'API Error: body is JSON but not a Message'
    exit 4
    ;;
  *)
    printf 'unknown mode %s\n' "$mode" >&2
    exit 99
    ;;
esac
EOF
chmod +x "$STUB"

call_count() { grep -c '^CALL$' "$CALLS" 2>/dev/null || true; }
model_n() {
  awk -v n="$1" '
    $0=="CALL" { c++; grab=0; next }
    $0=="END" { grab=0; next }
    grab && c==n { print; exit }
    $0=="--model" && c==n { grab=1; next }
  ' "$CALLS"
}

reset_run() {
  unset GENSEO_WRITER_SHAPE_RETRY GENSEO_WRITER_RESPONSE_PY
  export GENSEO_WRITER_MODEL="PATI-Alpha-Plan-Review"
  export GENSEO_WRITER_FALLBACK="PATI-Fable-5"
  export GENSEO_LANDING_DRAFT=1
  unset GENSEO_LANDING_LIVE_OK
  : > "$CALLS"
  : > "$LOG"
}

run_writer() {
  genseo_run_writer_with_shape_fallback "$LOG" "$STUB" \
    -p "prompt" --fallback-model "$GENSEO_WRITER_FALLBACK" --permission-mode dontAsk
  RC=$?
}

echo "1. classifier: Anthropic success is not a fallback, OpenAI JSON is"
ANTHROPIC='{"id":"msg_1","type":"message","role":"assistant","model":"claude","content":[{"type":"text","text":"ok"}]}'
TOOL='{"id":"msg_2","type":"message","role":"assistant","model":"claude","content":[{"type":"tool_use","id":"t1","name":"Bash","input":{}}]}'
OPENAI='{"id":"chatcmpl-1","object":"chat.completion","created":1,"model":"PATI-Alpha-Plan-Review","choices":[{"index":0,"message":{"role":"assistant","content":"hi"},"finish_reason":"stop"}],"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2}}'
CHUNK='{"id":"chatcmpl-1","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"a"}}]}'
RESP='{"id":"resp_1","object":"response","output":[{"type":"message","role":"assistant","content":[{"type":"output_text","text":"hi"}]}]}'
ERR='{"type":"error","error":{"type":"overloaded_error","message":"Overloaded"}}'
STREAM='{"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"a"}}'
STRINGY='{"type":"message","role":"assistant","content":"not a content block list"}'
py_rc 1 "anthropic message stays on the primary" --body "$ANTHROPIC"
py_rc 1 "anthropic tool_use message stays on the primary" --body "$TOOL"
py_rc 1 "anthropic error envelope is not a provider mismatch" --body "$ERR"
py_rc 1 "anthropic stream event is not a provider mismatch" --body "$STREAM"
py_rc 0 "openai chat.completion needs one fallback" --body "$OPENAI"
py_rc 0 "openai chat.completion.chunk needs one fallback" --body "$CHUNK"
py_rc 0 "openai responses payload needs one fallback" --body "$RESP"
py_rc 0 "message with string content is not an Anthropic message" --body "$STRINGY"
py_rc 0 "other JSON object is not an Anthropic message" --body '{"foo":1}'
py_rc 1 "plain text is not a wrong-shape JSON body" --body 'input exceeds the context window'

cat > "$TMP/morning.log" <<'EOF'
=== landing run 20261012-0919 listicle wellnessnest ===
(lane: hosted-9router writer=PATI-Alpha-Plan-Review fallback=PATI-Fable-5 permission=dontAsk)
[claude-code:unrecognized_model] {"model":"PATI-Alpha-Plan-Review","query_source":"sdk"}
API Error: API returned an empty or malformed response (HTTP 200) — check for a proxy or gateway intercepting the request. Response: content-type json, body is JSON but not a Message, size unknown, request-id absent, server cloudflare, intermediary headers cf-cache-status cf-ray content-encoding transfer-encoding. This was the non-streaming retry of streaming request (no Anthropic request-id), which failed with: other; 0 stream events received.
=== exit 1 ===
EOF
py_rc 0 "morning landing log needs one fallback" --log "$TMP/morning.log"
cat > "$TMP/unrecognized-only.log" <<'EOF'
[claude-code:unrecognized_model] {"model":"PATI-Alpha-Plan-Review","query_source":"sdk"}
input exceeds the context window
EOF
py_rc 1 "unrecognized_model JSON alone does not re-exec" --log "$TMP/unrecognized-only.log"
cat > "$TMP/recovered.log" <<'EOF'
=== writer attempt model=PATI-Alpha-Plan-Review ===
API Error: body is JSON but not a Message
=== writer attempt model=PATI-Fable-5 ===
{"id":"msg_1","type":"message","role":"assistant","model":"claude","content":[{"type":"text","text":"ok"}]}
EOF
py_rc 1 "latest Anthropic attempt does not ask for another re-exec" --log "$TMP/recovered.log"
cat > "$TMP/both-wrong.log" <<'EOF'
=== writer attempt model=PATI-Alpha-Plan-Review ===
API Error: body is JSON but not a Message
=== writer attempt model=PATI-Fable-5 ===
{"id":"chatcmpl-2","object":"chat.completion","choices":[{"index":0,"message":{"role":"assistant","content":"no"}}]}
EOF
py_rc 0 "latest OpenAI attempt still counts as wrong-shape" --log "$TMP/both-wrong.log"

echo "2. runner: Anthropic success is one call on the primary"
reset_run
printf '%s\n' anthropic-ok > "$MODE"
run_writer
[ "$RC" = 0 ] && ok "exit 0" || bad "exit $RC"
[ "$(call_count)" = 1 ] && ok "one call" || bad "calls $(call_count)"
[ "$(model_n 1)" = "claude-opus-5-5" ] && ok "primary model is the Claude id" || bad "model $(model_n 1)"
grep -q 'modelOverrides' "$CALLS" && ok "primary call carries modelOverrides" || bad "missing modelOverrides"
grep -q 'PATI-Alpha-Plan-Review' "$CALLS" && ok "override value is the planner alias" || bad "planner alias missing"
if grep -q -- '--model PATI-' "$CALLS" || grep -q -- '--fallback-model PATI-' "$CALLS"; then
  bad "primary call passed a bare alias"
else
  ok "primary call has no bare alias"
fi
if grep -q 'one re-exec' "$LOG"; then bad "success re-execed"; else ok "no re-exec"; fi
[ -z "${GENSEO_WRITER_SHAPE_RETRY:-}" ] && ok "retry flag stays unset" || bad "retry flag leaked"

echo "3. runner: exit 0 that mentions the diagnostic still does not re-exec"
reset_run
printf '%s\n' phrase-exit-0 > "$MODE"
run_writer
[ "$RC" = 0 ] && ok "exit 0" || bad "exit $RC"
[ "$(call_count)" = 1 ] && ok "one call" || bad "calls $(call_count)"
if grep -q 'one re-exec' "$LOG"; then bad "phrase on success re-execed"; else ok "success phrase ignored"; fi

echo "4. runner: the morning phrase re-execs once, and the fallback can succeed"
reset_run
printf '%s\n' phrase-then-ok > "$MODE"
run_writer
[ "$RC" = 0 ] && ok "exit 0" || bad "exit $RC"
[ "$(call_count)" = 2 ] && ok "exactly two calls" || bad "calls $(call_count)"
[ "$(model_n 1)" = "claude-opus-5-5" ] && ok "first model is the Claude planner id" || bad "first $(model_n 1)"
[ "$(model_n 2)" = "claude-fable-5" ] && ok "second model is the Claude fable id" || bad "second $(model_n 2)"
grep -q 'one re-exec on PATI-Fable-5' "$LOG" && ok "log names the one re-exec" || bad "missing re-exec line"
if grep -q 'not retrying again' "$LOG"; then bad "success logged a second failure"; else ok "no second-failure line"; fi
grep -q 'SPEC: landing_drafts/stub.json' "$LOG" && ok "fallback output kept" || bad "missing fallback output"
[ "$(grep -c '^ENV draft=1 live=$' "$CALLS" || true)" = 2 ] && ok "both calls stay draft-only" || bad "draft env drifted"
if grep -q -- '--live' "$CALLS"; then bad "re-exec passed --live"; else ok "re-exec has no --live"; fi
[ "$(grep -c -- '--permission-mode' "$CALLS" || true)" = 2 ] && ok "permission mode on both calls" || bad "permission mode drifted"

echo "5. runner: OpenAI JSON with no diagnostic phrase also re-execs once"
reset_run
printf '%s\n' openai-then-ok > "$MODE"
run_writer
[ "$RC" = 0 ] && ok "exit 0" || bad "exit $RC"
[ "$(call_count)" = 2 ] && ok "exactly two calls" || bad "calls $(call_count)"
[ "$(model_n 2)" = "claude-fable-5" ] && ok "fallback model is the Claude fable id" || bad "second $(model_n 2)"

echo "6. runner: fallback failure stops, keeps the fallback status, and does not call a third time"
reset_run
printf '%s\n' phrase-twice > "$MODE"
run_writer
[ "$RC" = 7 ] && ok "fallback exit 7" || bad "exit $RC"
[ "$(call_count)" = 2 ] && ok "exactly two calls" || bad "calls $(call_count)"
grep -q 'not retrying again' "$LOG" && ok "stop line" || bad "missing stop line"
[ "${GENSEO_WRITER_SHAPE_RETRY:-}" = 1 ] && ok "retry flag blocks another pass" || bad "flag ${GENSEO_WRITER_SHAPE_RETRY:-empty}"
printf '%s\n' always-fail > "$MODE"
run_writer
[ "$(call_count)" = 3 ] && ok "re-entry is a single fallback call" || bad "calls $(call_count)"
[ "$(model_n 3)" = "claude-fable-5" ] && ok "re-entry uses the Claude fable id" || bad "third $(model_n 3)"
[ "$RC" = 4 ] && ok "re-entry returns that call" || bad "re-entry exit $RC"

echo "7. runner: OpenAI on both attempts stops after the fallback"
reset_run
printf '%s\n' openai-twice > "$MODE"
run_writer
[ "$RC" = 7 ] && ok "fallback exit 7" || bad "exit $RC"
[ "$(call_count)" = 2 ] && ok "exactly two calls" || bad "calls $(call_count)"
grep -q 'not retrying again' "$LOG" && ok "stop line" || bad "missing stop line"

echo "8. runner: an Anthropic error and any other failure do not re-exec"
reset_run
printf '%s\n' anthropic-error > "$MODE"
run_writer
[ "$RC" = 1 ] && ok "anthropic error exit 1" || bad "exit $RC"
[ "$(call_count)" = 1 ] && ok "anthropic error is one call" || bad "calls $(call_count)"
reset_run
printf '%s\n' other-fail > "$MODE"
run_writer
[ "$RC" = 1 ] && ok "other failure exit 1" || bad "exit $RC"
[ "$(call_count)" = 1 ] && ok "other failure is one call" || bad "calls $(call_count)"
if grep -q 'one re-exec' "$LOG"; then bad "other failure re-execed"; else ok "other failure did not re-exec"; fi

echo "9. runner: same model, or a missing classifier, does not loop"
reset_run
export GENSEO_WRITER_MODEL="PATI-Fable-5"
export GENSEO_WRITER_FALLBACK="PATI-Fable-5"
printf '%s\n' always-fail > "$MODE"
run_writer
[ "$RC" = 4 ] && ok "same-model exit 4" || bad "exit $RC"
[ "$(call_count)" = 1 ] && ok "same-model is one call" || bad "calls $(call_count)"
reset_run
export GENSEO_WRITER_RESPONSE_PY="$TMP/missing-classifier.py"
printf '%s\n' always-fail > "$MODE"
run_writer
[ "$RC" = 4 ] && ok "missing classifier keeps the primary exit" || bad "exit $RC"
[ "$(call_count)" = 1 ] && ok "missing classifier does not re-exec" || bad "calls $(call_count)"

echo "10. both headless runners share the helper and keep their publish rules"
for rel in scripts/run_landing_headless.sh scripts/run_ticket_headless.sh scripts/genseo_model_lane.sh; do
  bash -n "$ROOT/$rel" && ok "$rel parses" || bad "$rel does not parse"
done
python3 -m py_compile "$PY" && ok "classifier compiles" || bad "classifier does not compile"
[ "$(grep -c 'genseo_run_writer_with_shape_fallback' "$ROOT/scripts/run_landing_headless.sh" || true)" = 1 ] \
  && ok "landing has one writer call" || bad "landing writer call count"
[ "$(grep -c 'genseo_run_writer_with_shape_fallback' "$ROOT/scripts/run_ticket_headless.sh" || true)" = 2 ] \
  && ok "article has a writer call per lane" || bad "article writer call count"
if grep -q 'CLAUDE_BIN" -p' "$ROOT/scripts/run_landing_headless.sh" "$ROOT/scripts/run_ticket_headless.sh"; then
  bad "a runner still invokes claude directly"
else
  ok "runners go through the shape helper"
fi
grep -q 'Never --live' "$ROOT/scripts/run_landing_headless.sh" && ok "landing prompt still refuses --live" || bad "landing lost Never --live"
grep -q 'shopify_publisher.py --live' "$ROOT/scripts/run_ticket_headless.sh" && ok "article prompt still publishes through the gate" || bad "article lost --live"
if grep -q -- '--live' "$ROOT/scripts/genseo_model_lane.sh" "$ROOT/scripts/genseo_writer_response.py"; then
  bad "helper mentions --live"
else
  ok "helper does not publish"
fi
grep -q 'one re-exec' "$ROOT/DAILY-RUN.md" && ok "DAILY-RUN documents the one re-exec" || bad "DAILY-RUN missing the re-exec"
draft='- [DRAFT 2026-10-12 page 166173573435] listicle | wellnessnest | product=pure-shilajit-gold-resin'
grep -qF -- "$draft" "$ROOT/daily-landing-tickets.md" && ok "gold-resin draft untouched" || bad "gold-resin draft line"
if grep -qE '^- \[ \] .*pure-shilajit-gold-resin' "$ROOT/daily-landing-tickets.md"; then
  bad "gold-resin was reopened"
else
  ok "gold-resin was not reopened"
fi

echo "11. writer network deadlines do not change the model"
NET="$TMP/net-claude"
NETOUT="$TMP/net-out"
export NETOUT
cat > "$NET" << 'EOF'
#!/bin/bash
{
  printf 'api=%s\n' "${API_TIMEOUT_MS:-}"
  printf 'first=%s\n' "${CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS:-}"
  printf 'idle=%s\n' "${CLAUDE_STREAM_IDLE_TIMEOUT_MS:-}"
  if [ -n "${ANTHROPIC_API_KEY+x}" ]; then
    printf 'apikey=set\n'
  else
    printf 'apikey=unset\n'
  fi
  printf 'args=%s\n' "$*"
} > "$NETOUT"
printf '%s\n' '{"id":"msg_1","type":"message","role":"assistant","model":"claude","content":[{"type":"text","text":"ok"}]}'
exit 0
EOF
chmod +x "$NET"
reset_run
unset API_TIMEOUT_MS CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS CLAUDE_STREAM_IDLE_TIMEOUT_MS
export ANTHROPIC_API_KEY="on-demand-key-do-not-use"
genseo_run_writer_with_shape_fallback "$TMP/net.log" "$NET" -p "prompt" --fallback-model PATI-Fable-5
unset ANTHROPIC_API_KEY
RC=$?
[ "$RC" = 0 ] && ok "default deadlines exit 0" || bad "default deadlines exit $RC"
grep -q '^api=600000$' "$NETOUT" && ok "default API_TIMEOUT_MS is 600000" || bad "api $(grep '^api=' "$NETOUT")"
grep -q '^first=120000$' "$NETOUT" && ok "default first-byte timeout is 120000" || bad "first $(grep '^first=' "$NETOUT")"
grep -q '^idle=300000$' "$NETOUT" && ok "default idle timeout is 300000" || bad "idle $(grep '^idle=' "$NETOUT")"
grep -q '^apikey=unset$' "$NETOUT" && ok "writer child does not see ANTHROPIC_API_KEY" || bad "apikey $(grep '^apikey=' "$NETOUT")"
grep -q -- '--model claude-opus-5-5' "$NETOUT" && ok "primary model is the Claude id" || bad "model args drifted"
grep -q -- '--fallback-model claude-fable-5' "$NETOUT" && ok "fallback flag is the Claude fable id" || bad "fallback flag was not rewritten"
if grep -q -- '--model PATI-' "$NETOUT" || grep -q -- '--fallback-model PATI-' "$NETOUT"; then
  bad "bare PATI alias was passed to claude"
else
  ok "bare PATI alias was not passed to claude"
fi
grep -q 'PATI-Alpha-Plan-Review' "$NETOUT" && ok "settings still name the planner alias" || bad "gateway planner alias missing"
grep -q 'PATI-Fable-5' "$NETOUT" && ok "settings still name the fable alias" || bad "gateway fable alias missing"
API_TIMEOUT_MS=111111 CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS=22222 CLAUDE_STREAM_IDLE_TIMEOUT_MS=333333 \
  genseo_run_writer_with_shape_fallback "$TMP/net.log" "$NET" -p "prompt" --fallback-model PATI-Fable-5
grep -q '^api=111111$' "$NETOUT" && ok "explicit API_TIMEOUT_MS kept" || bad "override api $(grep '^api=' "$NETOUT")"
grep -q '^first=22222$' "$NETOUT" && ok "explicit first-byte timeout kept" || bad "override first $(grep '^first=' "$NETOUT")"
grep -q '^idle=333333$' "$NETOUT" && ok "explicit idle timeout kept" || bad "override idle $(grep '^idle=' "$NETOUT")"
grep -q -- '--model claude-opus-5-5' "$NETOUT" && ok "override kept the Claude planner id" || bad "override changed model"
[ -z "${API_TIMEOUT_MS:-}" ] && ok "timeout export did not leak into the shell" || bad "API_TIMEOUT_MS leaked"

echo "12. an unmapped alias does not start claude"
reset_run
export GENSEO_WRITER_MODEL="PATI-No-Such"
printf '%s\n' anthropic-ok > "$MODE"
run_writer
[ "$RC" = 1 ] && ok "unmapped exit 1" || bad "exit $RC"
[ "$(call_count)" = 0 ] && ok "unmapped does not exec" || bad "calls $(call_count)"
grep -q 'FATAL: unrecognized model: PATI-No-Such' "$LOG" && ok "log names the refusal" || bad "missing fatal line"
if grep -q 'ANTHROPIC_API_KEY' "$LOG"; then bad "refusal log mentions an API key"; else ok "refusal log has no API key"; fi

echo "13. existing --settings JSON keeps claudeMdExcludes"
reset_run
printf '%s\n' anthropic-ok > "$MODE"
genseo_run_writer_with_shape_fallback "$LOG" "$STUB" \
  -p "prompt" --settings '{"claudeMdExcludes":["/tmp/CLAUDE.md"]}' \
  --fallback-model "$GENSEO_WRITER_FALLBACK"
RC=$?
[ "$RC" = 0 ] && ok "settings merge exit 0" || bad "exit $RC"
if python3 - "$CALLS" <<'PY'
import json, sys
text = open(sys.argv[1], encoding="utf-8").read().splitlines()
blob = ""
for i, line in enumerate(text):
    if line == "--settings" and i + 1 < len(text):
        blob = text[i + 1]
        break
if not blob:
    sys.exit("no settings arg")
data = json.loads(blob)
if data.get("claudeMdExcludes") != ["/tmp/CLAUDE.md"]:
    sys.exit("excludes %r" % data)
overrides = data.get("modelOverrides") or {}
if overrides.get("claude-opus-5-5") != "PATI-Alpha-Plan-Review":
    sys.exit("override %r" % overrides)
if overrides.get("claude-fable-5") != "PATI-Fable-5":
    sys.exit("fable override %r" % overrides)
PY
then ok "merged settings keep excludes and the gateway aliases"
else bad "settings merge in argv"; fi

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" = 0 ]

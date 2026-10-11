#!/bin/bash
# Assembled landing prompt: unpublished listicles carry a standing draft waiver.
# 2026-10-11 pure-shilajit-gold-resin exited with an empty SPEC because the writer
# asked a human to proceed on a scope gate. The product file was present.
# No Shopify, no model, no images. --print-prompt exits before the model lane.
#   bash tests/test_landing_prompt_waiver.sh
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER="$ROOT/scripts/run_landing_headless.sh"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/landing-prompt-waiver.XXXXXX")" || exit 1
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/home"
ln -s "$ROOT" "$TMP/home/genseo"
PASS=0; FAIL=0

ok(){ PASS=$((PASS+1)); echo "  ok    $1"; }
bad(){ FAIL=$((FAIL+1)); echo "  FAIL  $1"; }

assemble(){  # assemble <outfile> <runner args...>  — lane flags come from the caller
  local out=$1; shift
  env -i HOME="$TMP/home" PATH="/usr/bin:/bin" \
    GENSEO_LANDING_DAILY="${GENSEO_LANDING_DAILY-}" \
    GENSEO_LANDING_DRAFT="${GENSEO_LANDING_DRAFT-}" \
    GENSEO_LANDING_LIVE_OK="${GENSEO_LANDING_LIVE_OK-}" \
    /bin/bash "$RUNNER" "$@" > "$out"
}

# Every "ask a human to proceed" must be the prohibition "Do not ask a human to proceed."
proceed_is_only_prohibited(){
  python3 - "$1" <<'PY'
import sys
text = open(sys.argv[1], encoding="utf-8").read()
needle = "ask a human to proceed"
start = 0
count = 0
while True:
    i = text.find(needle, start)
    if i < 0:
        break
    count += 1
    if text[max(0, i - 7):i] != "Do not ":
        sys.exit("unprohibited proceed ask: %r" % text[max(0, i - 24):i + len(needle)])
    start = i + len(needle)
if count < 1:
    sys.exit("missing proceed prohibition")
print(count)
PY
}

echo "1. daily + draft (the 2026-10-11 lane) — waiver survives the DAILY_RULES override"
OUT="$TMP/daily.txt"
if GENSEO_LANDING_DAILY=1 GENSEO_LANDING_DRAFT=1 \
  assemble "$OUT" --print-prompt --queue daily-landing-tickets.md --next; then
  ok "print-prompt exit 0"
else
  bad "print-prompt failed"; echo "-----"; cat "$OUT"; echo "-----"
fi
if python3 - "$OUT" <<'PY'
import sys
text = open(sys.argv[1], encoding="utf-8").read()
override = "these override anything looser above"
preserve = "DRAFT STANDING APPROVAL is not a looser rule and is NOT overridden by the sentence above."
waiver = "SCOPE_WAIVER (Kevin, standing approval for unpublished draft listicles):"
need = [
    override, preserve, waiver,
    "Do not ask a human to proceed.",
    "product=pure-shilajit-gold-resin",
    "empty SPEC, the 2026-10-11 gold-resin no-spec failure",
    "Never --live",
    "DRAFT ALREADY APPROVED.",
    "Do not show a file-count menu.",
    "more than 2 output files",
    'Do not ask "Proceed with the full unpublished draft package?"',
    "FILE-COUNT MENU is not a looser rule",
    "ima2 OAuth lane at $0",
    "Do not stop for a cost table.",
]
missing = [s for s in need if s not in text]
if missing:
    sys.exit("missing: " + " | ".join(missing))
if text.index("DRAFT ALREADY APPROVED.") > text.index("Build ONE GenSeo landing page."):
    sys.exit("draft lead is below the build sentence")
if text.index(preserve) < text.index(override):
    sys.exit("preservation bullet is above the override sentence")
if text.index(waiver) < text.index(override):
    sys.exit("SCOPE_WAIVER block is above the override sentence")
menu = "FILE-COUNT MENU is not a looser rule"
if text.index(menu) < text.index(override):
    sys.exit("file-count bullet is above the override sentence")
ask = 'Do not ask "Proceed with the full unpublished draft package?"'
bare = "Proceed with the full unpublished draft package?"
start = 0
while True:
    i = text.find(bare, start)
    if i < 0:
        break
    if not text[max(0, i - len('Do not ask "')):i].endswith('Do not ask "'):
        sys.exit("unprohibited package question")
    start = i + len(bare)
banned = [
    "ask the human to proceed before",
    "wait for a human",
    "Should I proceed",
    "please confirm before",
]
hit = [s for s in banned if s in text]
if hit:
    sys.exit("prompt requires a human: " + " | ".join(hit))
print("daily-ok")
PY
then ok "daily prompt has standing waiver after the override"; else bad "daily prompt assertions"; fi
if n="$(proceed_is_only_prohibited "$OUT")"; then
  [ "$n" -ge 2 ] && ok "proceed ask appears only as Do not ($n)" || bad "expected waiver and daily bullet, got $n"
else
  bad "proceed-ask check"
fi

echo "2. local preview (no daily flag) is still unpublished — waiver on, daily override absent"
OUT="$TMP/preview.txt"
if assemble "$OUT" --print-prompt listicle wellnessnest "product=pure-shilajit-gold-resin preview"; then
  ok "preview print-prompt exit 0"
else
  bad "preview print-prompt failed"
fi
if grep -q 'SCOPE_WAIVER (Kevin, standing approval for unpublished draft listicles):' "$OUT" \
  && grep -q 'Do not ask a human to proceed.' "$OUT" \
  && grep -q 'DRAFT ALREADY APPROVED.' "$OUT" \
  && grep -q 'Do not show a file-count menu.' "$OUT" \
  && grep -q 'Proceed with the full unpublished draft package?' "$OUT" \
  && ! grep -q 'DAILY LISTICLE LANE' "$OUT" \
  && ! grep -q 'FILE-COUNT MENU' "$OUT"; then
  ok "preview waiver without daily override"
else
  bad "preview waiver shape"
fi

echo "3. daily lane keeps the waiver even if a live flag leaked into the environment"
OUT="$TMP/leaked-live.txt"
if GENSEO_LANDING_DAILY=1 GENSEO_LANDING_DRAFT=1 GENSEO_LANDING_LIVE_OK=1 \
  assemble "$OUT" --print-prompt listicle wellnessnest "product=pure-shilajit-gold-resin leaked"; then
  ok "leaked-live print-prompt exit 0"
else
  bad "leaked-live print-prompt failed"
fi
if grep -q 'SCOPE_WAIVER (Kevin, standing approval for unpublished draft listicles):' "$OUT" \
  && grep -q 'NOT overridden by the sentence above' "$OUT" \
  && grep -q 'FILE-COUNT MENU is not a looser rule' "$OUT" \
  && grep -q 'Never --live' "$OUT"; then
  ok "daily waiver held with leaked LIVE_OK"
else
  bad "daily waiver dropped when LIVE_OK leaked"
fi

echo "4. a non-daily live attempt does not get the draft standing approval"
OUT="$TMP/live.txt"
if GENSEO_LANDING_LIVE_OK=1 \
  assemble "$OUT" --print-prompt listicle wellnessnest "product=pure-shilajit-gold-resin live-attempt"; then
  ok "live-attempt print-prompt exit 0"
else
  bad "live-attempt print-prompt failed"
fi
if grep -q 'SCOPE_WAIVER (Kevin, standing approval for unpublished draft listicles):' "$OUT" \
  || grep -q 'Do not ask a human to proceed.' "$OUT" \
  || grep -q 'DRAFT STANDING APPROVAL' "$OUT" \
  || grep -q 'DRAFT ALREADY APPROVED.' "$OUT" \
  || grep -q 'more than 2 output files' "$OUT" \
  || grep -q 'Proceed with the full unpublished draft package?' "$OUT"; then
  bad "live attempt still carries the draft waiver"
else
  ok "live attempt has no draft waiver"
fi

echo "5. gold-resin ticket is the open one the next daily/catch-up will take"
first="$(grep -m1 -E '^- \[ \] ' "$ROOT/daily-landing-tickets.md" || true)"
case "$first" in
  *'product=pure-shilajit-gold-resin'*) ok "first open ticket is gold resin" ;;
  *) bad "first open ticket [$first]" ;;
esac
if grep -q 'FAILED 2026-10-11' "$ROOT/daily-landing-tickets.md"; then
  bad "queue still has FAILED 2026-10-11"
else
  ok "no FAILED 2026-10-11 tag"
fi
if grep -q 're-armed 2026-10-11' "$ROOT/daily-landing-tickets.md"; then
  ok "re-arm note is on the queue"
else
  bad "missing 2026-10-11 re-arm note"
fi

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" = 0 ]

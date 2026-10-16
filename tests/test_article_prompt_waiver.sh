#!/bin/bash
# Assembled article prompt: the daily blog writer carries a standing scope waiver.
# 2026-10-12 #MB1009-7 exited 0 three times after a file-count menu. The ticket
# stayed open. Nothing was published.
# No Shopify, no model, no images. --print-prompt exits before the model lane.
#   bash tests/test_article_prompt_waiver.sh
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER="$ROOT/scripts/run_ticket_headless.sh"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/article-prompt-waiver.XXXXXX")" || exit 1
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/home"
ln -s "$ROOT" "$TMP/home/genseo"
PASS=0; FAIL=0

ok(){ PASS=$((PASS+1)); echo "  ok    $1"; }
bad(){ FAIL=$((FAIL+1)); echo "  FAIL  $1"; }
pointer_first() {
  awk '$0 == "First open line:" { getline; print; exit }' "$1"
}
assert_publish_lines() {
  local f=$1 label=$2
  if grep -F -q 'genseo_published_today.py' "$f" \
    && grep -F -q 'do NOT publish' "$f" \
    && grep -F -q 'scripts/shopify_publisher.py --live' "$f" \
    && grep -F -q 'validate_article.py prints PASS' "$f" \
    && grep -F -q 'no shopify_publisher.py update' "$f" \
    && grep -F -q "that file's required and optional lines" "$f"; then
    ok "$label keeps publish text and the double-publish guard"
  else
    bad "$label changed publish or double-publish text"
  fi
}
reject_broken_noface() {
  local f=$1 label=$2
  if grep -F -q 'GENSEO_NO_FACE=1 = 1' "$f" || grep -F -q 'GENSEO_NO_FACE=0 = 1' "$f" \
    || grep -F -q '${GENSEO_NO_FACE:-0}' "$f" || grep -F -q '${GENSEO_DAILY_TARGET:-5}' "$f"; then
    bad "$label still has a broken env splice"
  else
    ok "$label has no broken env splice"
  fi
}

echo "1. daily article prompt names the file-count gate and keeps live publish"
OUT="$TMP/article.txt"
if env -i HOME="$TMP/home" PATH="/usr/bin:/bin" /bin/bash "$RUNNER" --print-prompt > "$OUT"; then
  ok "print-prompt exit 0"
else
  bad "print-prompt failed"; echo "-----"; cat "$OUT"; echo "-----"
fi
if python3 - "$OUT" "$ROOT/CLAUDE.md" <<'PY'
import sys
text = open(sys.argv[1], encoding="utf-8").read()
claude = open(sys.argv[2], encoding="utf-8").read()
need = [
    "ARTICLE ALREADY APPROVED.",
    "SCOPE_WAIVER (Kevin, standing approval for the daily blog article):",
    "Do not ask a human to proceed.",
    "Do not show a file-count menu.",
    "more than 2 output files",
    'Do not ask "Proceed with the full live publish package?"',
    "2026-10-12 failure",
    "#MB1009-7",
    "scripts/shopify_publisher.py --live",
    "landing-page listicle",
    "The file-count scope gate is not one of those rules.",
    "Silence does not mean 0 files.",
    "A ticket template named LISTICLE is still this blog article.",
]
missing = [s for s in need if s not in text]
if missing:
    sys.exit("prompt missing: " + " | ".join(missing))
if not text.startswith("ARTICLE ALREADY APPROVED."):
    sys.exit("approval lead is not first")
waiver = "SCOPE_WAIVER (Kevin, standing approval for the daily blog article):"
exit_bullet = "The file-count scope gate is not one of those rules."
if text.index(waiver) < text.index(exit_bullet):
    sys.exit("SCOPE_WAIVER is above the exit-bullet exclusion")
bare = "Proceed with the full live publish package?"
start = 0
while True:
    i = text.find(bare, start)
    if i < 0:
        break
    if not text[max(0, i - len('Do not ask "')):i].endswith('Do not ask "'):
        sys.exit("unprohibited live-package question")
    start = i + len(bare)
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
if count < 2:
    sys.exit("expected lead and waiver proceed bans, got %d" % count)
banned = [
    "SCOPE_WAIVER (Kevin, standing approval for unpublished draft listicles):",
    "Proceed with the full unpublished draft package?",
    "Should I proceed",
    "wait for a human",
    "please confirm before",
    "Do not publish live.",
]
hit = [s for s in banned if s in text]
if hit:
    sys.exit("article prompt carries a landing or ask line: " + " | ".join(hit))
# Project CLAUDE.md must key each waiver on its own heading. A bare
# "contains SCOPE_WAIVER" rule would attach "Do not publish live" to articles.
article = "SCOPE_WAIVER (Kevin, standing approval for the daily blog article)"
landing = "SCOPE_WAIVER (Kevin, standing approval for unpublished draft listicles)"
for label, heading in (("article", article), ("landing", landing)):
    if heading not in claude:
        sys.exit("CLAUDE.md missing %s waiver heading" % label)
if "When the prompt contains `SCOPE_WAIVER`," in claude:
    sys.exit("CLAUDE.md still uses a bare SCOPE_WAIVER match")
art_at = claude.index(article)
land_at = claude.index(landing)
art_para = claude[art_at:art_at + 700]
land_para = claude[land_at:land_at + 500]
if "Do not publish live." not in land_para:
    sys.exit("landing waiver lost the do-not-publish-live line")
if "Do not publish live." in art_para:
    sys.exit("article waiver says do not publish live")
if "shopify_publisher.py" not in art_para:
    sys.exit("article waiver does not name the publisher")
if "landing-page listicle" not in art_para:
    sys.exit("article waiver does not keep landing pages unpublished")
print("article-ok")
PY
then ok "prompt and CLAUDE.md keep the two waivers apart"; else bad "prompt assertions"; fi

# #MB1009-7 was published in 925e143. The prompt still names that 2026-10-12
# failure. The Mac publisher keeps flipping later tickets on main, so the
# queue head id is not stable. The invariant is that the failure ticket is
# not what the next run would pick.
echo "2. the 2026-10-12 failure ticket is not the open queue head"
first="$(grep -m1 -E '^(- \[ \]|## \[ \])' "$ROOT/daily-tickets.md" | tr -d '\r' || true)"
open_n="$(grep -cE '^(- \[ \]|## \[ \])' "$ROOT/daily-tickets.md" || true)"
if [ -n "$first" ]; then
  ok "an open ticket remains"
  got="$(pointer_first "$TMP/article.txt")"
  if [ "$got" = "$first" ]; then
    ok "prompt names that open queue head"
  else
    bad "prompt queue head $(printf '%q' "$got") != $(printf '%q' "$first")"
  fi
else
  bad "ticket queue has no open line"
fi
if grep -F -x -q "Open tickets: $open_n" "$TMP/article.txt"; then
  ok "prompt open count matches the wrapper grep ($open_n)"
else
  bad "prompt open count is not $open_n"
fi
assert_publish_lines "$TMP/article.txt" "default prompt"
reject_broken_noface "$TMP/article.txt" "default prompt"
if grep -F -q 'the env value GENSEO_NO_FACE is exactly 1; this run: 0' "$TMP/article.txt" \
  && grep -F -q '>= 5 (or -1), do NOT publish' "$TMP/article.txt"; then
  ok "unset no-face value is 0 and the daily target stays 5"
else
  bad "default prompt lost the no-face value or the daily target"
fi
if grep -F -q "QUEUE POINTER (shell grep of daily-tickets.md, same pattern as the daily wrapper):" "$TMP/article.txt" \
  && grep -F -q "Older sections that say the queue is EMPTY" "$TMP/article.txt"; then
  ok "prompt warns that old empty-queue notes are history"
else
  bad "prompt missing the empty-queue history warning"
fi
case "$first" in
  *'#MB1009-7'*) bad "failure ticket is still the queue head" ;;
  *) ok "queue head is not #MB1009-7" ;;
esac
if grep -E '^- \[ \] .*#MB1009-7' "$ROOT/daily-tickets.md" >/dev/null; then
  bad "#MB1009-7 is still open"
else
  ok "#MB1009-7 is not an open ticket"
fi

echo "2b. GENSEO_NO_FACE=1 leads the prompt and the default prompt does not"
if grep -F -q "NO-FACE LANE (GENSEO_NO_FACE=1)" "$TMP/article.txt"; then
  bad "default prompt carries the no-face banner"
else
  ok "default prompt has no no-face banner"
fi
NOFACE="$TMP/noface.txt"
if env -i HOME="$TMP/home" PATH="/usr/bin:/bin" GENSEO_NO_FACE=1 /bin/bash "$RUNNER" --print-prompt > "$NOFACE"; then
  ok "no-face print-prompt exit 0"
else
  bad "no-face print-prompt failed"
fi
if grep -F -q "NO-FACE LANE (GENSEO_NO_FACE=1)" "$NOFACE" \
  && grep -F -q "Do not run persona_picker.py" "$NOFACE" \
  && grep -F -q "Do not edit or commit personas/index.json" "$NOFACE"; then
  head_line="$(head -n 1 "$NOFACE")"
  case "$head_line" in
    "NO-FACE LANE (GENSEO_NO_FACE=1)."*) ok "no-face banner is the first line" ;;
    *) bad "no-face banner is not the first line: $head_line" ;;
  esac
else
  bad "no-face prompt missing the banner"
fi
assert_publish_lines "$NOFACE" "no-face prompt"
reject_broken_noface "$NOFACE" "no-face prompt"
if grep -F -q 'the env value GENSEO_NO_FACE is exactly 1; this run: 1' "$NOFACE" \
  && grep -F -q '>= 5 (or -1), do NOT publish' "$NOFACE"; then
  ok "no-face prompt says this run is 1 and keeps the daily target"
else
  bad "no-face prompt lost the run value or the daily target"
fi
ZERO="$TMP/noface0.txt"
if env -i HOME="$TMP/home" PATH="/usr/bin:/bin" GENSEO_NO_FACE=0 /bin/bash "$RUNNER" --print-prompt > "$ZERO"; then
  ok "GENSEO_NO_FACE=0 print-prompt exit 0"
else
  bad "GENSEO_NO_FACE=0 print-prompt failed"
fi
if grep -F -q "NO-FACE LANE (GENSEO_NO_FACE=1)" "$ZERO"; then
  bad "GENSEO_NO_FACE=0 still carries the banner"
else
  ok "GENSEO_NO_FACE=0 has no banner"
fi
if grep -F -q 'this run: 0' "$ZERO"; then
  ok "GENSEO_NO_FACE=0 renders this run: 0"
else
  bad "GENSEO_NO_FACE=0 did not render this run: 0"
fi
TRUEV="$TMP/nofacetrue.txt"
if env -i HOME="$TMP/home" PATH="/usr/bin:/bin" GENSEO_NO_FACE=true /bin/bash "$RUNNER" --print-prompt > "$TRUEV"; then
  ok "GENSEO_NO_FACE=true print-prompt exit 0"
else
  bad "GENSEO_NO_FACE=true print-prompt failed"
fi
if grep -F -q "NO-FACE LANE (GENSEO_NO_FACE=1)" "$TRUEV"; then
  bad "GENSEO_NO_FACE=true was treated as the no-face lane"
else
  ok "only exact 1 turns the no-face banner on"
fi
if grep -F -q 'this run: true' "$TRUEV"; then
  ok "non-1 no-face value is shown verbatim"
else
  bad "GENSEO_NO_FACE=true was not shown verbatim"
fi
BOTH="$TMP/noface-target.txt"
if env -i HOME="$TMP/home" PATH="/usr/bin:/bin" GENSEO_NO_FACE=1 GENSEO_DAILY_TARGET=7 \
  /bin/bash "$RUNNER" --print-prompt > "$BOTH"; then
  ok "no-face plus daily target print-prompt exit 0"
else
  bad "no-face plus daily target print-prompt failed"
fi
if grep -F -q '>= 7 (or -1), do NOT publish' "$BOTH" \
  && ! grep -F -q '>= 5 (or -1), do NOT publish' "$BOTH" \
  && head -n 1 "$BOTH" | grep -F -q "NO-FACE LANE (GENSEO_NO_FACE=1)."; then
  ok "banner prepend keeps the expanded daily target"
else
  bad "banner prepend broke the daily-target splice"
fi

echo "2c. heading tickets, decoys, CRLF, and ticket text is not executed"
HEAD="$TMP/head-home"
mkdir -p "$HEAD/genseo"
SENTINEL="$TMP/pwned-sentinel"
# Unquoted heredoc: \$ and \` stay literal so writing the fixture does not run
# the ticket text. $SENTINEL is the path the runner must not touch.
cat > "$HEAD/genseo/daily-tickets.md" <<EOF
**2026-08-13 — the queue is EMPTY.**
## Refill needed
  - [ ] indented decoy
- [x] closed dash
## [DONE 2026-08-01] closed heading
## [ ] Ticket #HS-9 heading style wins \$(touch $SENTINEL) \`echo PWNED2\`
- [ ] **#DASH-2** later dash
EOF
HEADOUT="$TMP/head.txt"
if env -i HOME="$HEAD" PATH="/usr/bin:/bin" /bin/bash "$RUNNER" --print-prompt > "$HEADOUT"; then
  ok "heading fixture print-prompt exit 0"
else
  bad "heading fixture print-prompt failed"
fi
want='## [ ] Ticket #HS-9 heading style wins $(touch '"$SENTINEL"') `echo PWNED2`'
got="$(pointer_first "$HEADOUT")"
if [ "$got" = "$want" ]; then
  ok "first open line is the ## [ ] heading, not a later dash"
else
  bad "heading pointer $(printf '%q' "$got") != $(printf '%q' "$want")"
fi
if grep -F -x -q 'Open tickets: 2' "$HEADOUT" \
  && grep -F -q 'Older sections that say the queue is EMPTY' "$HEADOUT" \
  && ! grep -F -q '#DASH-2' "$HEADOUT" \
  && ! grep -F -q 'indented decoy' "$HEADOUT"; then
  ok "heading fixture counts 2 and does not dump later or decoy lines"
else
  bad "heading fixture count or decoy leak"
fi
if [ -e "$SENTINEL" ]; then
  bad "ticket text was executed"
else
  ok "ticket command substitution was not executed"
fi
assert_publish_lines "$HEADOUT" "heading fixture"
CRLF="$TMP/crlf-home"
mkdir -p "$CRLF/genseo"
python3 - "$CRLF/genseo/daily-tickets.md" <<'PY'
import sys
text = "\n".join([
    "**2026-08-13 — the queue is EMPTY.**",
    "## Refill needed",
    "- [x] closed crlf",
    "## [ ] Ticket #CRLF-9 heading survives crlf",
    "",
])
open(sys.argv[1], "wb").write(text.replace("\n", "\r\n").encode())
PY
CRLF_OUT="$TMP/crlf.txt"
if env -i HOME="$CRLF" PATH="/usr/bin:/bin" /bin/bash "$RUNNER" --print-prompt > "$CRLF_OUT"; then
  ok "crlf print-prompt exit 0"
else
  bad "crlf print-prompt failed"
fi
crlf_want='## [ ] Ticket #CRLF-9 heading survives crlf'
crlf_got="$(pointer_first "$CRLF_OUT")"
if [ "$crlf_got" = "$crlf_want" ]; then
  ok "crlf ## [ ] line is named without a carriage return"
else
  bad "crlf pointer $(printf '%q' "$crlf_got")"
fi
case "$crlf_got" in
  *$'\r'*) bad "crlf pointer still contains CR" ;;
  *) ok "crlf pointer has no CR" ;;
esac
if grep -F -x -q 'Open tickets: 1' "$CRLF_OUT"; then
  ok "crlf file counts the heading ticket"
else
  bad "crlf open count is not 1"
fi

echo "2d. zero open tickets, empty file, and a missing file"
assert_zero() {
  local f=$1 label=$2
  if python3 - "$f" <<'PY'
import sys
text = open(sys.argv[1], encoding="utf-8").read()
block = """QUEUE POINTER (shell grep of daily-tickets.md, same pattern as the daily wrapper):
Open tickets: 0
First open line:
(none)
Do not write an article."""
if block not in text:
    sys.exit("missing 0-open block")
if "Process that ticket and no other." in text:
    sys.exit("still says to process a ticket")
PY
  then
    ok "$label says 0 open and does not name a ticket"
  else
    bad "$label 0-open pointer"
  fi
}
ZEROQ="$TMP/zero-home"
mkdir -p "$ZEROQ/genseo"
python3 - "$ZEROQ/genseo/daily-tickets.md" <<'PY'
import sys
text = "\n".join([
    "**2026-08-13 — the queue is EMPTY.**",
    "## Refill needed",
    "- [x] closed dash",
    "## [DONE 2026-08-01] closed heading",
    "- [DONE 2026-08-02] old done",
    "  - [ ] indented not open",
    "## [x] checked heading",
    "",
])
open(sys.argv[1], "wb").write(text.replace("\n", "\r\n").encode())
PY
ZERO_OUT="$TMP/zero.txt"
if env -i HOME="$ZEROQ" PATH="/usr/bin:/bin" /bin/bash "$RUNNER" --print-prompt > "$ZERO_OUT"; then
  ok "zero-open print-prompt exit 0"
else
  bad "zero-open print-prompt failed"
fi
assert_zero "$ZERO_OUT" "closed-only queue"
assert_publish_lines "$ZERO_OUT" "zero-open prompt"
if grep -F -q "NO-FACE LANE (GENSEO_NO_FACE=1)" "$ZERO_OUT"; then
  bad "zero-open default prompt has the no-face banner"
else
  ok "zero-open default prompt has no banner"
fi
EMPTYF="$TMP/empty-file-home"
mkdir -p "$EMPTYF/genseo"
: > "$EMPTYF/genseo/daily-tickets.md"
EMPTY_OUT="$TMP/empty-file.txt"
if env -i HOME="$EMPTYF" PATH="/usr/bin:/bin" /bin/bash "$RUNNER" --print-prompt > "$EMPTY_OUT"; then
  ok "empty file print-prompt exit 0"
else
  bad "empty file print-prompt failed"
fi
assert_zero "$EMPTY_OUT" "empty ticket file"
MISSH="$TMP/missing-home"
mkdir -p "$MISSH/genseo"
MISS_OUT="$TMP/missing.txt"
if env -i HOME="$MISSH" PATH="/usr/bin:/bin" /bin/bash "$RUNNER" --print-prompt > "$MISS_OUT"; then
  ok "missing file print-prompt exit 0"
else
  bad "missing file print-prompt failed"
fi
assert_zero "$MISS_OUT" "missing ticket file"
NFZERO="$TMP/nfzero.txt"
if env -i HOME="$ZEROQ" PATH="/usr/bin:/bin" GENSEO_NO_FACE=1 /bin/bash "$RUNNER" --print-prompt > "$NFZERO"; then
  ok "no-face zero-open print-prompt exit 0"
else
  bad "no-face zero-open print-prompt failed"
fi
nf_head="$(head -n 1 "$NFZERO")"
case "$nf_head" in
  "NO-FACE LANE (GENSEO_NO_FACE=1)."*) ok "no-face banner still leads a 0-open prompt" ;;
  *) bad "0-open no-face banner is not first: $nf_head" ;;
esac
assert_zero "$NFZERO" "no-face zero-open"
reject_broken_noface "$NFZERO" "no-face zero-open"
if grep -F -q 'this run: 1' "$NFZERO"; then
  ok "0-open no-face prompt still says this run: 1"
else
  bad "0-open no-face prompt lost this run: 1"
fi

echo "2e. shell empty-queue exit and live-count guard stay ahead of claude"
if python3 - "$RUNNER" <<'PY'
import sys
text = open(sys.argv[1], encoding="utf-8").read()
empty = text.index("retry skipped: ticket queue empty")
live = text.index('/usr/bin/python3 "$HOME/genseo/scripts/genseo_published_today.py"')
hand = text.index('-p "$PROMPT"')
if not (empty < live < hand):
    sys.exit("empty-queue exit, live-count guard, and claude handoff are out of order")
if text.count('-p "$PROMPT"') != 2:
    sys.exit("expected 2 prompt hands, got %d" % text.count('-p "$PROMPT"'))
if "shopify_publisher.py publish" in text:
    sys.exit("runner gained a direct publish invocation")
print("guard-order-ok")
PY
then
  ok "empty queue and the live-count guard still exit before claude"
else
  bad "shell guard order changed"
fi

echo "3. article run excludes the user scope-gate CLAUDE.md; project memory stays"
OUT="$TMP/settings.txt"
if env -i HOME="$TMP/home" PATH="/usr/bin:/bin" \
  GENSEO_ARTICLE_PRINT_SETTINGS=1 /bin/bash "$RUNNER" > "$OUT"; then
  ok "settings print exit 0"
else
  bad "settings print failed"; echo "-----"; cat "$OUT"; echo "-----"
fi
if python3 - "$OUT" "$TMP/article.txt" \
  "$TMP/home/.claude/CLAUDE.md" "$TMP/home/PATI/LLM-Wiki/CLAUDE.md" \
  "$ROOT/CLAUDE.md" "$ROOT/AGENTS.md" <<'PY'
import json, sys
text = open(sys.argv[1], encoding="utf-8").read().splitlines()
prompt = open(sys.argv[2], encoding="utf-8").read()
user_md, wiki_md, project_claude, project_agents = sys.argv[3:]
if len(text) != 2 or text[0] != "--settings":
    sys.exit("expected --settings then one JSON line, got %r" % text[:4])
data = json.loads(text[1])
if list(data) != ["claudeMdExcludes"]:
    sys.exit("settings keys %r" % list(data))
ex = data["claudeMdExcludes"]
need = [user_md, wiki_md, "**/.claude/CLAUDE.md", "**/LLM-Wiki/CLAUDE.md"]
if ex != need:
    sys.exit("excludes %r" % ex)
for banned in (project_claude, project_agents, "AGENTS.md", "genseo/CLAUDE.md"):
    if banned in ex:
        sys.exit("project memory excluded: %s" % banned)
gate = "validate_article.py prints PASS"
pub = "scripts/shopify_publisher.py --live"
if gate not in prompt or pub not in prompt:
    sys.exit("publish path missing from the prompt")
if prompt.index(gate) > prompt.index(pub):
    sys.exit("validate gate is after the publisher")
if "validate_article.py gate (exit 0 required)" not in prompt:
    sys.exit("step gate missing")
print("settings-ok")
PY
then ok "settings exclude the user and wiki CLAUDE.md"; else bad "settings excludes"; fi

if grep -F -q '/bin/bash "$G/scripts/run_ticket_headless.sh"' "$ROOT/deploy/grokbot-genseo-daily.sh"; then
  ok "daily wrapper calls the checkout runner"
else
  bad "daily wrapper does not call the checkout runner"
fi
# print-settings, the native invocation, and the router invocation
settings_hits="$(grep -F -c '"${SETTINGS_ARGS[@]}"' "$RUNNER" || true)"
if [ "$settings_hits" = 3 ]; then
  ok "print-settings, native, and router pass the exclude"
else
  bad "expected 3 settings expansions, got $settings_hits"
fi
if awk '/GENSEO_MODEL_LANE:-}" = "native"/,/^else$/' "$RUNNER" | grep -F -q '"${SETTINGS_ARGS[@]}"'; then
  ok "native lane passes claudeMdExcludes"
else
  bad "native lane missing settings"
fi
if awk '/^else$/,/^fi$/' "$RUNNER" | grep -F -q '"${SETTINGS_ARGS[@]}"'; then
  ok "router lane passes claudeMdExcludes"
else
  bad "router lane missing settings"
fi
if awk '/GENSEO_MODEL_LANE:-}" = "native"/,/^else$/' "$RUNNER" | grep -q 'permission-mode'; then
  bad "native lane passes permission-mode"
else
  ok "native lane leaves the CLI permission mode"
fi

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]

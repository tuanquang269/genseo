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
first="$(grep -m1 -E '^- \[ \]' "$ROOT/daily-tickets.md" || true)"
if [ -n "$first" ]; then
  ok "an open ticket remains"
  if grep -F -q -- "$first" "$TMP/article.txt"; then
    ok "prompt names that open queue head"
  else
    bad "prompt missing the open queue head"
  fi
else
  bad "ticket queue has no open line"
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

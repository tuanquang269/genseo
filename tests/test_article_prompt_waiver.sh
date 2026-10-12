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

echo "2. first open article ticket is still #MB1009-7"
first="$(grep -m1 -E '^- \[ \]' "$ROOT/daily-tickets.md" || true)"
case "$first" in
  *'#MB1009-7'*) ok "first open ticket is #MB1009-7" ;;
  *) bad "first open ticket [$first]" ;;
esac

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]

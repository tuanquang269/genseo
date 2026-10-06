#!/bin/bash
# GenSeo landing-page runner (listicle / advertorial) — manual or queued, NEVER part of the daily 5/day flow.
#   scripts/run_landing_headless.sh listicle wellnessnest "creatine gummies for adults over 40 — FusiForce"
#   scripts/run_landing_headless.sh advertorial wellnessnest "ShilaSource shilajit resin — honest explainer"
#   scripts/run_landing_headless.sh --next          # first "- [ ]" line in landing-tickets.md
# Output: landing_drafts/<slug>.json + .claims.md + <slug>/preview.html (+ an UNPUBLISHED Shopify page only if
# GENSEO_LANDING_DRAFT=1). It never publishes live, never touches daily-tickets.md, never runs the 5/day guard
# (Shopify pages are not in /blogs/news.atom, so they cannot affect the daily count either way).
# Same model lane as run_ticket_headless.sh: native login dir if logged in, else local 9router (Mini),
# else hosted 9router ai.patigroup.com with the lean ~/.claude-genseo config (MacBook). Works on either Mac.
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
for d in "$HOME"/.nvm/versions/node/*/bin; do [ -d "$d" ] && PATH="$d:$PATH"; done
export PATH
unset ANTHROPIC_API_KEY
cd "$HOME/genseo" || exit 1
if [ "$1" = "--next" ]; then
  LINE="$(grep -m1 -E '^- \[ \] ' landing-tickets.md 2>/dev/null)"
  [ -z "$LINE" ] && { echo "landing queue empty"; exit 0; }
  # format: - [ ] <listicle|advertorial> | <store> | <brief>
  TEMPLATE="$(echo "$LINE" | sed -E 's/^- \[ \] *//' | cut -d'|' -f1 | xargs)"
  STORE="$(echo "$LINE" | cut -d'|' -f2 | xargs)"
  BRIEF="$(echo "$LINE" | cut -d'|' -f3- | xargs)"
else
  TEMPLATE="$1"; STORE="$2"; BRIEF="$3"
fi
case "$TEMPLATE" in listicle|advertorial) ;; *) echo "usage: $0 <listicle|advertorial> <store> \"<brief>\" | --next"; exit 2;; esac
[ -f "brand/$STORE.json" ] || { echo "no brand tokens: brand/$STORE.json"; exit 2; }
[ -n "$BRIEF" ] || { echo "empty brief"; exit 2; }
if ! python3 -c 'import PIL, markdown' >/dev/null 2>&1 && /usr/bin/python3 -c 'import PIL, markdown' >/dev/null 2>&1; then
  mkdir -p "$HOME/genseo/state/pybin" && ln -sf /usr/bin/python3 "$HOME/genseo/state/pybin/python3"
  export PATH="$HOME/genseo/state/pybin:$PATH"
fi
GENSEO_CFG="$HOME/.claude-genseo"; USE_NATIVE=0
if [ -d "$GENSEO_CFG" ]; then
  AUTH_JSON="$(CLAUDE_CONFIG_DIR="$GENSEO_CFG" "$HOME/.local/bin/claude" auth status 2>/dev/null || true)"
  case "$AUTH_JSON" in *'"loggedIn": true'*|*'"loggedIn":true'*) USE_NATIVE=1;; esac
fi
if [ "$USE_NATIVE" = "1" ]; then
  export CLAUDE_CONFIG_DIR="$GENSEO_CFG"
elif ! curl -s -m 3 -o /dev/null http://127.0.0.1:20128/ 2>/dev/null; then
  _K="${NINE_ROUTER_KEY:-}"
  if [ -z "$_K" ] && [ -f "$HOME/PATI/LLM-Wiki/.env" ]; then
    _K="$(grep -E '^(export )?NINE_ROUTER_KEY=' "$HOME/PATI/LLM-Wiki/.env" | head -1 | sed -E 's/^(export )?NINE_ROUTER_KEY=//; s/^["'"'"']//; s/["'"'"']$//')"
  fi
  [ -z "$_K" ] && { echo "FATAL: no model lane (no native login, no local 9router, no NINE_ROUTER_KEY)"; exit 1; }
  export ANTHROPIC_BASE_URL="${GENSEO_ROUTER_BASE:-https://ai.patigroup.com}" ANTHROPIC_AUTH_TOKEN="$_K"
  export CLAUDE_CONFIG_DIR="$GENSEO_CFG"; mkdir -p "$GENSEO_CFG"; unset _K
fi
export CLAUDE_CODE_MAX_CONTEXT_TOKENS=150000
CLAUDE_BIN="$HOME/.local/bin/claude"; [ -x "$CLAUDE_BIN" ] || CLAUDE_BIN="$(command -v claude)"
mkdir -p logs; STAMP="$(date +%Y%m%d-%H%M)"; LOG="logs/landing-$STAMP.log"
DRAFT_RULE="Stop after the local preview (do NOT run landing_publisher.py --draft)."
[ "${GENSEO_LANDING_DRAFT:-0}" = "1" ] && DRAFT_RULE="After the preview passes, run landing_publisher.py <spec> --draft (UNPUBLISHED Shopify page). Never --live."
PROMPT="Build ONE GenSeo landing page. template=$TEMPLATE store=$STORE brief: $BRIEF
Read /Users/kevinkreative/genseo/skills/genseo-landing-pages/SKILL.md plus the vault skill it points to (~/.claude/skills/claude-design-dtc-listicle-advertorial/SKILL.md and PATI-ADAPTATION.md, which wins) and follow them exactly (spec JSON -> no-face images via scripts/article_images.py --qc -> claims log -> validate_landing.py -> landing_publisher.py preview). $DRAFT_RULE
Hard rules: no invented claims, numbers, ratings, reviews, testimonials or expert quotes — anything you cannot source from a page you actually fetched is a [[PLACEHOLDER: ...]] or is cut. AgeAura = NMN + TMG only, never Urolithin A. No faces in any image. No countdown timers or fake scarcity. Never publish live, never touch daily-tickets.md or any live article. Run image generations in the foreground (no background jobs).
Finish with: SPEC: <path>  PREVIEW: <file:// path>  placeholders: <n>  claims: <n>."
echo "=== landing run $STAMP $TEMPLATE $STORE ===" >> "$LOG"
"$CLAUDE_BIN" -p "$PROMPT" --model PATI-Alpha-Plan-Review --fallback-model PATI-Fable-5 --strict-mcp-config \
  --output-format text --allowed-tools "Read,Write,Edit,Bash,Glob,Grep,WebFetch,WebSearch" >> "$LOG" 2>&1
RC=$?
echo "=== exit $RC ===" >> "$LOG"; tail -5 "$LOG"
if [ "$1" = "--next" ] && [ $RC = 0 ]; then
  /usr/bin/python3 - "$LINE" <<'PY'
import sys, datetime
line = sys.argv[1]; p = "landing-tickets.md"; s = open(p).read()
s = s.replace(line, line.replace("- [ ]", f"- [PREVIEW {datetime.date.today()}]", 1), 1); open(p, "w").write(s)
PY
fi
exit $RC

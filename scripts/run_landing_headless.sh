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
QUEUE="landing-tickets.md"
if [ "$1" = "--queue" ]; then QUEUE="$2"; shift 2; fi   # daily lane: --queue daily-landing-tickets.md --next
if [ "$1" = "--next" ]; then
  LINE="$(grep -m1 -E '^- \[ \] ' "$QUEUE" 2>/dev/null)"
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
mkdir -p logs; STAMP="$(date +%Y%m%d-%H%M)"; LOG="${GENSEO_LANDING_LOG:-logs/landing-$STAMP.log}"
DRAFT_RULE="Stop after the local preview (do NOT run landing_publisher.py --draft)."
[ "${GENSEO_LANDING_DRAFT:-0}" = "1" ] && DRAFT_RULE="After the preview passes, run landing_publisher.py <spec> --draft (UNPUBLISHED Shopify page). Never --live."
DAILY_RULES=""
if [ "${GENSEO_LANDING_DAILY:-0}" = "1" ]; then
  # Daily listicle lane (Kevin 2026-10-08): one UNPUBLISHED draft per day for Kevin to approve. run_landing_daily.sh
  # re-runs validate_landing.py + landing_qa.mjs itself and re-checks the page is unpublished afterwards.
  DAY="$(TZ=Asia/Saigon date +%y%m%d)"
  DAILY_RULES="
DAILY LISTICLE LANE (Kevin 2026-10-08) — these override anything looser above:
- Template = the reference-replica LISTICLE: \"engine\": \"ref\", \"template\": \"listicle\", \"posture\": \"hybrid\", \"template_suffix\": \"gsl-ref-listicle-v1\", \"takeover\": false. Copy the structure (keys, item count, chart slots on rows 02 + 04, bridge, expert, offer, product, footer, sources) of landing_drafts/fusiforce-creatine-gummies-listicle.json; write ALL new copy for the product/angle in the ticket. Do not reuse that page's images or claims unless you re-verify them for this product.
- slug = <short product name>-listicle-$DAY (lowercase, e.g. ageaura-nmn-listicle-$DAY); \"handle\": \"gsl-preview-<slug>\" (MUST start with gsl-preview-). Add \"created\": \"$(TZ=Asia/Saigon date +%F)\" and \"daily\": true to the spec. Byline: Dr. Marcus Hale (roster.json), role \"Wellness Nest editorial team\".
- Content per the vault learnings + GenSeo guidelines (knowledge_base/SEO_EEAT_GUIDELINES.md + knowledge_base/AEO_GEO_GUIDELINES.md, brand/<store>.json voice): answer-first, plain US English, every number/study linked inline to a source you fetched this run (Europe PMC / DOI / PubMed), say what the evidence did NOT test. No invented stats, claims, prices, ratings or quotes; product card = only what the live PDP (/products/<handle>.js + PDP HTML) prints.
- Reviews: ONLY real 4-5 star Trustpilot reviews from state/trustpilot/wellnessnest.json (refreshed by the wrapper from trustpilot.com/review/wellnessnest.co). Quote verbatim, reviewer name exactly as shown, TrustScore + review count exactly as in that file (count written with a thousands comma as Trustpilot displays it), source = the review URL + date. Prefer a review that mentions the product or the buying experience; never edit the wording; never use a 1-3 star review. If the file is missing or empty, leave the expert slot as a [[PLACEHOLDER: real Trustpilot review]] — never write one.
- Images: fresh ones for this page only, slug landing-<slug>, via scripts/article_images.py --square --qc (no-face lane: --ugc for scenes, --product-ref <handle> (no :index) for any image that shows the pack, \"no people's faces\" in the NEGATIVE, never --persona-ref). Byline avatar = a no-face square (e.g. a desk/notebook still life). Foreground only. QC FAIL -> re-roll (max 3) or drop that image slot.
- Gate: validate_landing.py must PASS, then NODE_PATH=\$(npm root -g) node scripts/landing_qa.mjs landing_drafts/<slug>/preview.html (desktop.png + mobile.png; fix overflow at 375). Then landing_publisher.py <spec> --draft (env GENSEO_LANDING_DAILY=1 is already set: it refuses a 2nd gsl- page today and uploads images with the CLI app token). NEVER --live, NEVER --install-template, NEVER landing_preview_toggle.py, never publish or unhide any page.
- Do not git commit (the wrapper commits)."
fi
PROMPT="Build ONE GenSeo landing page. template=$TEMPLATE store=$STORE brief: $BRIEF
Read /Users/kevinkreative/genseo/skills/genseo-landing-pages/SKILL.md plus the vault skill it points to (~/.claude/skills/claude-design-dtc-listicle-advertorial/SKILL.md and PATI-ADAPTATION.md, which wins) and follow them exactly (spec JSON -> no-face images via scripts/article_images.py --qc -> claims log -> validate_landing.py -> landing_publisher.py preview). $DRAFT_RULE
Hard rules: no invented claims, numbers, ratings, reviews, testimonials or expert quotes — anything you cannot source from a page you actually fetched is a [[PLACEHOLDER: ...]] or is cut. AgeAura = NMN + TMG only, never Urolithin A. No faces in any image. No countdown timers or fake scarcity. Never publish live, never touch daily-tickets.md or any live article. Run image generations in the foreground (no background jobs).$DAILY_RULES
Finish with: SPEC: <path>  PREVIEW: <file:// path>  placeholders: <n>  claims: <n>."
echo "=== landing run $STAMP $TEMPLATE $STORE ===" >> "$LOG"
"$CLAUDE_BIN" -p "$PROMPT" --model PATI-Alpha-Plan-Review --fallback-model PATI-Fable-5 --strict-mcp-config \
  --output-format text --allowed-tools "Read,Write,Edit,Bash,Glob,Grep,WebFetch,WebSearch" >> "$LOG" 2>&1
RC=$?
echo "=== exit $RC ===" >> "$LOG"; tail -5 "$LOG"
if [ "$1" = "--next" ] && [ $RC = 0 ] && [ "${GENSEO_LANDING_DAILY:-0}" != "1" ]; then   # daily lane: wrapper re-tags
  /usr/bin/python3 - "$LINE" "$QUEUE" <<'PY'
import sys, datetime
line = sys.argv[1]; p = sys.argv[2]; s = open(p).read()
s = s.replace(line, line.replace("- [ ]", f"- [PREVIEW {datetime.date.today()}]", 1), 1); open(p, "w").write(s)
PY
fi
exit $RC

#!/bin/bash
# GenSeo landing-page runner (listicle / advertorial) — manual or queued, NEVER part of the daily 5/day flow.
#   scripts/run_landing_headless.sh listicle wellnessnest "creatine gummies for adults over 40 — FusiForce"
#   scripts/run_landing_headless.sh advertorial wellnessnest "ShilaSource shilajit resin — honest explainer"
#   scripts/run_landing_headless.sh --next          # first "- [ ]" line in landing-tickets.md
#   scripts/run_landing_headless.sh --print-prompt listicle wellnessnest "brief"   # assembled prompt only; no model
# Output: landing_drafts/<slug>.json + .claims.md + <slug>/preview.html (+ an UNPUBLISHED Shopify page only if
# GENSEO_LANDING_DRAFT=1). It never publishes live, never touches daily-tickets.md, never runs the 5/day guard
# (Shopify pages are not in /blogs/news.atom, so they cannot affect the daily count either way).
# Same model lane as run_ticket_headless.sh (scripts/genseo_model_lane.sh). A PATI-* writer
# or fallback is a 9router alias: native Claude login is ignored (unrecognized_model,
# landing 2026-10-10 09:30). Otherwise native login if logged in. Else local 9router only
# when /v1/models lists the writer alias, else hosted ai.patigroup.com. A MacBook router
# that is up with no PATI-* ids is not a writer lane. Router lanes pass
# --permission-mode dontAsk so auto mode does not use the PATI id as the Bash safety
# service (articles 2026-10-11 08:19). A PATI-* id with no modelOverrides entry in
# scripts/genseo_model_map.json is refused before claude starts (landing 2026-10-15).
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
for d in "$HOME"/.nvm/versions/node/*/bin; do [ -d "$d" ] && PATH="$d:$PATH"; done
export PATH
unset ANTHROPIC_API_KEY
cd "$HOME/genseo" || exit 1
# --print-prompt writes the assembled writer prompt and exits before the model lane.
# tests/test_landing_prompt_waiver.sh uses it. No Shopify, no claude.
PRINT_PROMPT=0
if [ "${1:-}" = "--print-prompt" ]; then PRINT_PROMPT=1; shift; fi
if [ "${GENSEO_LANDING_PRINT_PROMPT:-0}" = "1" ]; then PRINT_PROMPT=1; fi
QUEUE="landing-tickets.md"
if [ "$1" = "--queue" ]; then QUEUE="$2"; shift 2; fi   # daily lane: --queue daily-landing-tickets.md --next
if [ "$1" = "--next" ]; then
  if [ -f "$HOME/genseo/scripts/genseo_queue_closures.py" ]; then
    LINE="$(/usr/bin/python3 "$HOME/genseo/scripts/genseo_queue_closures.py" first --queue "$QUEUE")" || exit 1
  else
    LINE="$(grep -m1 -E '^- \[ \] ' "$QUEUE" 2>/dev/null)"
  fi
  [ -z "$LINE" ] && { echo "landing queue empty"; exit 0; }
  # format: - [ ] <listicle|advertorial> | <store> | <brief>
  TEMPLATE="$(echo "$LINE" | sed -E 's/^- \[ \] *//' | cut -d'|' -f1 | xargs)"
  STORE="$(echo "$LINE" | cut -d'|' -f2 | xargs)"
  BRIEF="$(echo "$LINE" | cut -d'|' -f3- | xargs)"
else
  TEMPLATE="$1"; STORE="$2"; BRIEF="$3"
fi
case "$TEMPLATE" in listicle|advertorial) ;; *) echo "usage: $0 [--print-prompt] <listicle|advertorial> <store> \"<brief>\" | [--print-prompt] --queue <file> --next"; exit 2;; esac
[ -f "brand/$STORE.json" ] || { echo "no brand tokens: brand/$STORE.json"; exit 2; }
[ -n "$BRIEF" ] || { echo "empty brief"; exit 2; }
if ! python3 -c 'import PIL, markdown' >/dev/null 2>&1 && /usr/bin/python3 -c 'import PIL, markdown' >/dev/null 2>&1; then
  mkdir -p "$HOME/genseo/state/pybin" && ln -sf /usr/bin/python3 "$HOME/genseo/state/pybin/python3"
  export PATH="$HOME/genseo/state/pybin:$PATH"
fi
# GENSEO_LANDING_PRINT_SETTINGS=1 prints the unpublished-run --settings payload and exits
# before the model lane. tests/test_landing_prompt_waiver.sh uses it. No Shopify, no claude.
if [ "$PRINT_PROMPT" != 1 ] && [ "${GENSEO_LANDING_PRINT_SETTINGS:-0}" != "1" ]; then
  GENSEO_CFG="$HOME/.claude-genseo"; USE_NATIVE=0
  if [ -d "$GENSEO_CFG" ]; then
    AUTH_JSON="$(CLAUDE_CONFIG_DIR="$GENSEO_CFG" "$HOME/.local/bin/claude" auth status 2>/dev/null || true)"
    case "$AUTH_JSON" in *'"loggedIn": true'*|*'"loggedIn":true'*) USE_NATIVE=1;; esac
  fi
  # shellcheck source=genseo_model_lane.sh
  . "$HOME/genseo/scripts/genseo_model_lane.sh"
  if ! genseo_select_model_lane; then
    echo "FATAL: ${GENSEO_MODEL_LANE_ERROR:-no model lane}"
    exit 1
  fi
fi
export CLAUDE_CODE_MAX_CONTEXT_TOKENS=150000
CLAUDE_BIN="$HOME/.local/bin/claude"; [ -x "$CLAUDE_BIN" ] || CLAUDE_BIN="$(command -v claude)"
mkdir -p logs; STAMP="$(date +%Y%m%d-%H%M)"; LOG="${GENSEO_LANDING_LOG:-logs/landing-$STAMP.log}"
DRAFT_RULE="Stop after the local preview (do NOT run landing_publisher.py --draft)."
[ "${GENSEO_LANDING_DRAFT:-0}" = "1" ] && DRAFT_RULE="After the preview passes, run landing_publisher.py <spec> --draft (UNPUBLISHED Shopify page). Never --live."
# Draft-only / unpublished listicles (Kevin: he approves later; this runner never auto-publishes).
# 2026-10-11 pure-shilajit-gold-resin: the writer hit the always-on file-count scope gate
# (~/.claude/CLAUDE.md: more than 2 output files → show a menu and wait), asked
# "Proceed with the full unpublished draft package?", and exited with an empty SPEC.
# The product file was present. The daily block below says it overrides looser rules
# above, so the waiver is repeated there and is not a looser rule.
# Off only for a non-daily, non-draft live attempt (GENSEO_LANDING_LIVE_OK=1).
SCOPE_WAIVER=""
DRAFT_LEAD=""
if [ "${GENSEO_LANDING_DAILY:-0}" = "1" ] || [ "${GENSEO_LANDING_DRAFT:-0}" = "1" ] || [ "${GENSEO_LANDING_LIVE_OK:-0}" != "1" ]; then
  DRAFT_LEAD='DRAFT ALREADY APPROVED. Write the unpublished package in this run. The always-on scope gate is off: more than 2 output files does not mean show a menu and wait. Do not show a file-count menu. Do not wait. Do not ask a human to proceed.'
  SCOPE_WAIVER='
SCOPE_WAIVER (Kevin, standing approval for unpublished draft listicles):
- This run is draft-only. Do not publish live. Kevin already approved writing the unpublished draft or the local preview. Do not ask a human to proceed. Do not stop on a scope gate, a posture check, or a question about whether to continue.
- The always-on scope gate is off. That rule says more than 2 output files, show a menu with real file counts, then wait, and silence means the smallest set. Do not show that menu. Do not wait. The full unpublished package is the approved deliverable. Do not ask "Proceed with the full unpublished draft package?" That question and an exit is the 2026-10-11 gold-resin empty SPEC.
- Posture is hybrid on the daily lane, and a local preview stays unpublished. Do not list postures for a pick.
- Image generation is the ima2 OAuth lane at $0. Do not stop for a cost table.
- Lines that say to surface a choice to Kevin do not apply to this unpublished run. Keep going and write the spec.
- Write landing_drafts/<slug>.json and the page. Finish with SPEC: and a real json path. An exit with no spec is a failed run.
- This waiver does not approve --live, theme writes, or edits to a page that is already public.'
fi
DAILY_RULES=""
if [ "${GENSEO_LANDING_DAILY:-0}" = "1" ]; then
  # Daily listicle lane (Kevin 2026-10-08): one UNPUBLISHED draft per day for Kevin to approve. run_landing_daily.sh
  # re-runs validate_landing.py + landing_qa.mjs itself and re-checks the page is unpublished afterwards.
  DAY="$(TZ=Asia/Saigon date +%y%m%d)"
  DAILY_RULES="
DAILY LISTICLE LANE (Kevin 2026-10-08) — these override anything looser above:
- DRAFT STANDING APPROVAL is not a looser rule and is NOT overridden by the sentence above. The SCOPE_WAIVER stays in force for this unpublished draft. Do not ask a human to proceed. Do not stop on a scope gate. Write the spec and the unpublished page before you exit. Asking to proceed and exiting is a failed run (empty SPEC, the 2026-10-11 gold-resin no-spec failure).
- FILE-COUNT MENU is not a looser rule and is NOT overridden by the sentence above. Do not show a file-count menu. Do not wait. The always-on line \"more than 2 output files\" does not apply. Do not ask whether to proceed with the full unpublished draft package.
- Template = the reference-replica LISTICLE: \"engine\": \"ref\", \"template\": \"listicle\", \"posture\": \"hybrid\", \"template_suffix\": \"gsl-ref-listicle-v2\", \"style\": \"premium\", \"takeover\": false. Copy the structure (keys, item count, chart slots on rows 02 + 04, bridge, expert, offer, product, footer, sources, plus the premium keys: hero kicker/image/chip/cta/source, trust[4] + trust_source, evidence_label per row, layout callout on the evidence-gap row, expert.reviews[3] + reviews_source, offer rating_html/price/bullets/price_source, sticky_cta) of landing_drafts/ageaura-nmn-listicle-261008.json (2026-10-08 visual benchmark winner vs the live omnicreatine listicle); write ALL new copy for the product/angle in the ticket. Do not reuse that page's images or claims unless you re-verify them for this product.
- slug = <short product name>-listicle-$DAY (lowercase, e.g. ageaura-nmn-listicle-$DAY); \"handle\": \"gsl-preview-<slug>\" (MUST start with gsl-preview-). Add \"created\": \"$(TZ=Asia/Saigon date +%F)\" and \"daily\": true to the spec. Byline: Mike Moretti (roster.json), role \"Co-founder, Wellness Nest\". TODO: no approved headshot — keep the no-face avatar still life, do not invent a portrait. Do not byline Dr. Marcus Hale.
- Content per the vault learnings + GenSeo guidelines (knowledge_base/SEO_EEAT_GUIDELINES.md + knowledge_base/AEO_GEO_GUIDELINES.md, brand/<store>.json voice): answer-first, plain US English, every number/study linked inline to a source you fetched this run (Europe PMC / DOI / PubMed), say what the evidence did NOT test. No invented stats, claims, prices, ratings or quotes; product card = only what the live PDP (/products/<handle>.js + PDP HTML) prints, except the FloraFresh formula: strain, CFU, ingredients and sugar claims come ONLY from its Supplement Facts label (python3 scripts/florafresh_rules.py --brief), never from the PDP description. Shilajit Shockwave pack-label doses come ONLY from product_refs/shilajit-shockwave.label.json (identity lines only; no milligram, serving count, or volume token; python3 scripts/shockwave_rules.py --brief). Pure Shilajit Gold Resin pack-label doses come ONLY from product_refs/pure-shilajit-gold-resin.label.json (the OCR serving line and 75% Fulvic; no milligram amount and no other serving count, volume, weight, or day-supply; python3 scripts/gold_resin_rules.py --brief). ShilaSource Himalayan Shilajit Resin pack-label doses come ONLY from product_refs/shilasource-himalayan-shilajit-resin.label.json (required and optional lines only; no milligram amount was read; do not state a different serving count, volume, weight, fulvic percentage, mineral count, or day-supply; python3 scripts/shilasource_resin_rules.py --brief). Turkesterone Advanced Formula pack-label doses come ONLY from product_refs/turkesterone-advanced-formula.label.json (front-of-pack lines only; the capsule badge is the separate lines 60 and Capsules; no milligram amount and no Supplement Facts panel were read; do not state a serving count, a different capsule count, or a day-supply; python3 scripts/turkesterone_rules.py --brief).
- Reviews: ONLY real 4-5 star Trustpilot reviews from state/trustpilot/wellnessnest.json (refreshed by the wrapper from trustpilot.com/review/wellnessnest.co). Quote verbatim, reviewer name exactly as shown, TrustScore + review count exactly as in that file (count written with a thousands comma as Trustpilot displays it), source = the review URL + date. Prefer a review that mentions the product or the buying experience; never edit the wording; never use a 1-3 star review. If the file is missing or empty, leave the expert slot as a [[PLACEHOLDER: real Trustpilot review]] — never write one.
- Images: fresh ones for this page only, slug landing-<slug>, via scripts/article_images.py --square --qc (no-face lane: --ugc for scenes, --product-ref <handle> (no :index) for any image that shows the pack, \"no people's faces\" in the NEGATIVE, never --persona-ref). Byline avatar = a no-face square (e.g. a desk/notebook still life). Every numbered row gets its OWN image (no image used twice). ONE art direction for every image on the page (Kevin 2026-10-08 'too ugly' fix; put this ART block in every prompt): \"premium editorial wellness photography; warm ivory and sand tones with soft sage-green accents; soft diffused morning window light from the upper left; gentle botanical leaf shadows; travertine stone and natural linen; shallow depth of field; calm, airy, luxury skincare-brand look; muted natural colours\". Pack shots (hero, offer, expert, bridge, one late row; never before the bridge except the hero): ONLY when product_refs/<handle>-cutout.png AND product_refs/<handle>.label.json exist, generate with scripts/article_images.py --square --qc --ref product_refs/<handle>-cutout.png and a PACK FACE WHITELIST that lists the label text letter-perfect (see scripts/tools/README or the 2026-10-08 entry in state/landing-build-progress.md); then EVERY pack image must pass /usr/bin/python3 scripts/landing_label_gate.py <image> --handle <handle> (exit 0) AND you must Read a 2x zoom crop of the logo mark and compare it with the cutout (mark description is in the label json). Any fail -> re-roll (max 3) -> fallback = composite the real cutout with scripts/landing_pack_shots.py --bg <generated empty scene> --out ... (tone match + cylinder shading + cast shadow). FAIL CLOSED: a whitelist pack shot with a missing product_refs/<handle>.label.json, a non-zero landing_label_gate.py, an empty OCR read, or a host without macOS Vision (swift + scripts/tools/label_ocr.swift) is a failure. Do not treat that as a pass and do not skip the gate. Skip the gate only when you did not generate a whitelist pack shot. No cutout/label json for the product -> a clean real PDP pack image (no hands, faces or overlays) or product_refs/<handle>.png as webp, and do not write label gate PASS. Price anchor in the offer = the PDP's real Subscribe & Save selling plan vs the one-time price (/products/<handle>.js selling_plan_groups); no compare_at = no strike price. Foreground only. QC FAIL -> re-roll (max 3) or drop that image slot.
- PACK IMAGES VS CUTOUT: pack_images is a whitelist claim and runs the label gate. Set pack_images only when product_refs/<handle>-cutout.png exists and every listed file already passed landing_label_gate.py with exit 0. If that cutout file does not exist, omit the pack_images key. Do not set an empty list. Do not write a label-gate pass phrase or PACK FACE WHITELIST into the spec. A label json without a cutout is expected. Use the live PDP pack image or product_refs/<handle>.png. validate_landing.py does not require pack_images in that case. Missing a cutout is not a reason to exit without landing_drafts/<slug>.json. If the cutout exists and a generated shot fails the gate, re-roll at most 3 times, then composite the real cutout with landing_pack_shots.py. Do not list a shot that failed the gate.
- Gate: validate_landing.py must PASS, then NODE_PATH=\$(npm root -g) node scripts/landing_qa.mjs landing_drafts/<slug>/preview.html (desktop.png + mobile.png; fix overflow at 375). Then landing_publisher.py <spec> --draft (env GENSEO_LANDING_DAILY=1 is already set: it refuses a 2nd gsl- page today and uploads images with the CLI app token). NEVER --live, NEVER --install-template, NEVER landing_preview_toggle.py, never publish or unhide any page (the wrapper runs landing_real_qa.py afterwards: it checks that the MAIN theme holds your template_suffix file unchanged and screenshots the REAL storefront render in a short guarded window; Kevin approves on that render, so never rely on preview.html alone).
- Copy shape (2026-10-08 benchmark vs the reference listicle, scored blind with JEV: these rules turned a 3-criteria loss into a win; validate_landing.py now FAILS daily specs that break them): H1 (accent + title) <= 48 chars; hero summary <= 32 words; item titles <= 34 chars; 2 short <p> per row, 15-30 words each (hard max 40), <= 520 chars per row; chart stat value <= 8 chars, label <= 24 chars, chart source = one short line (authors, journal year, n, duration); ZERO em or en dashes anywhere visible (use a comma, colon, period or 'to'; page ranges with '-'); offer CTA <= 3 words. Every row image must literally illustrate that row's point (e.g. walking finding -> people walking; meta-analysis -> research papers), alt = an honest description of the scene. Match the rhythm and length of landing_drafts/ageaura-nmn-listicle-261008.json (benchmark winner).
- Do not git commit (the wrapper commits)."
fi
PROMPT="${DRAFT_LEAD}
Build ONE GenSeo landing page. template=$TEMPLATE store=$STORE brief: $BRIEF
Read /Users/kevinkreative/genseo/skills/genseo-landing-pages/SKILL.md plus the vault skill it points to (~/.claude/skills/claude-design-dtc-listicle-advertorial/SKILL.md and PATI-ADAPTATION.md, which wins) and follow them exactly (spec JSON -> no-face images via scripts/article_images.py --qc -> claims log -> validate_landing.py -> landing_publisher.py preview). $DRAFT_RULE
Hard rules: no invented claims, numbers, ratings, reviews, testimonials or expert quotes — anything you cannot source from a page you actually fetched is a [[PLACEHOLDER: ...]] or is cut. AgeAura = NMN + TMG only, never Urolithin A. FloraFresh = its Supplement Facts label formula only (Bacillus coagulans SNZ-1969, 15B CFU per 2 gummies, not sugar-free); 1 billion CFU and 1B CFU are the retired count. The live PDP description is still wrong on the strain story (Lactobacillus strains, XOS, D-mannose, sugar-free), never copy it. Shilajit Shockwave = the OCR-accepted lines in product_refs/shilajit-shockwave.label.json only; do not state a milligram amount, a serving count, or a volume line that file does not list (python3 scripts/shockwave_rules.py --brief). Pure Shilajit Gold Resin = the required and optional lines in product_refs/pure-shilajit-gold-resin.label.json only, including the OCR serving line and 75% Fulvic; do not state a milligram amount or a different serving count, volume, weight, or day-supply (python3 scripts/gold_resin_rules.py --brief). ShilaSource Himalayan Shilajit Resin = the required and optional lines in product_refs/shilasource-himalayan-shilajit-resin.label.json only; no milligram amount was read; do not state a different serving count, volume, weight, fulvic percentage, mineral count, or day-supply (python3 scripts/shilasource_resin_rules.py --brief). Turkesterone Advanced Formula = the required and optional lines in product_refs/turkesterone-advanced-formula.label.json only; no milligram amount and no Supplement Facts panel were read; the capsule badge is the separate lines 60 and Capsules; do not state a serving count, a different capsule count, or a day-supply (python3 scripts/turkesterone_rules.py --brief). A whitelist pack shot (PACK FACE WHITELIST or pack_images) fails closed when product_refs/<handle>.label.json is missing, OCR fails, or the host has no macOS Vision (swift + scripts/tools/label_ocr.swift): do not treat that as a pass. Skip the label gate only when the image is not a whitelist pack shot. No faces in any image. No countdown timers or fake scarcity. Never publish live, never touch daily-tickets.md or any live article. Run image generations in the foreground (no background jobs).$DAILY_RULES
$SCOPE_WAIVER
Finish with: SPEC: <path>  PREVIEW: <file:// path>  placeholders: <n>  claims: <n>."
if [ "$PRINT_PROMPT" = 1 ]; then
  printf '%s\n' "$PROMPT"
  exit 0
fi
# 2026-10-11 pure-shilajit-gold-resin: hosted lane set CLAUDE_CONFIG_DIR to
# ~/.claude-genseo (no CLAUDE.md there) and the writer still loaded
# ~/.claude/CLAUDE.md as User memory. That file's always-on scope gate said
# more than 2 output files, show a menu, then wait. The model asked
# "Proceed with the full unpublished draft package?" and exited 0 with no spec.
# claudeMdExcludes drops that User file (and the wiki path it symlinks to) for
# unpublished runs. Project CLAUDE.md and this prompt stay. A non-daily live
# attempt does not get the waiver, so it does not get this exclude.
# --settings merges; it does not replace the lane's auth or permission flags.
SETTINGS_ARGS=()
if [ -n "$SCOPE_WAIVER" ]; then
  SETTINGS_JSON="$(/usr/bin/python3 - "$HOME/.claude/CLAUDE.md" "$HOME/PATI/LLM-Wiki/CLAUDE.md" <<'PY'
import json, sys
user_md, wiki_md = sys.argv[1:]
print(json.dumps({
    "claudeMdExcludes": [
        user_md,
        wiki_md,
        "**/.claude/CLAUDE.md",
        "**/LLM-Wiki/CLAUDE.md",
    ]
}))
PY
)" || SETTINGS_JSON=""
  if [ -n "$SETTINGS_JSON" ]; then
    SETTINGS_ARGS=(--settings "$SETTINGS_JSON")
  else
    echo "WARN: claudeMdExcludes settings were not built; prompt waiver only" >> "$LOG"
  fi
fi
if [ "${GENSEO_LANDING_PRINT_SETTINGS:-0}" = "1" ]; then
  if [ "${#SETTINGS_ARGS[@]}" -gt 0 ]; then
    printf '%s\n' "${SETTINGS_ARGS[@]}"
  fi
  exit 0
fi
echo "=== landing run $STAMP $TEMPLATE $STORE ===" >> "$LOG"
genseo_lane_log_line >> "$LOG"
genseo_claude_model_log_line >> "$LOG"
# Router lanes only. Native keeps the CLI default. dontAsk is the fallback if the
# lane left the mode empty on a non-native run.
PERM_ARGS=()
if [ "${GENSEO_MODEL_LANE:-}" != "native" ]; then
  : "${GENSEO_PERMISSION_MODE:=dontAsk}"
  PERM_ARGS=(--permission-mode "$GENSEO_PERMISSION_MODE")
fi
# 2026-10-12 09:19: the primary writer returned HTTP 200 OpenAI chat.completion.
# Claude logged "JSON but not a Message" and exited with no spec. --fallback-model
# did not run. One re-exec uses GENSEO_WRITER_FALLBACK. The prompt and draft flags
# stay as they are; this path still never passes --live.
genseo_run_writer_with_shape_fallback "$LOG" "$CLAUDE_BIN" \
  -p "$PROMPT" --fallback-model "$GENSEO_WRITER_FALLBACK" \
  "${PERM_ARGS[@]}" "${SETTINGS_ARGS[@]}" --strict-mcp-config \
  --output-format text --allowed-tools "Read,Write,Edit,Bash,Glob,Grep,WebFetch,WebSearch"
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

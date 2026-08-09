#!/bin/bash
# GenSeo headless ticket runner — called by launchd (com.pati.genseo-articles).
# Mirrors the proven pati-os dreams pattern: enrich launchd's minimal PATH,
# strip ANTHROPIC_API_KEY so claude CLI uses subscription OAuth, run one ticket.

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
# nvm-installed node (Mac mini lane) — ima2 is a node script and needs node on PATH
for d in "$HOME"/.nvm/versions/node/*/bin; do [ -d "$d" ] && PATH="$d:$PATH"; done
export PATH
unset ANTHROPIC_API_KEY
# Mac mini's global settings.json routes claude through the local 9router proxy
# (PATI-Opus-5 etc.) for Hermes. FINDINGS 2026-08-09 (00.6-mistakes has the full map):
# empty-string process env is IGNORED (settings env wins); --settings deep-merges and
# cannot DELETE a key (null becomes the literal string "null"); any present
# ANTHROPIC_AUTH_TOKEN key — even empty — switches the CLI out of OAuth. So the ONLY
# clean native lane is a dedicated CLAUDE_CONFIG_DIR with no settings.json, which
# needs a one-time `CLAUDE_CONFIG_DIR=$HOME/.claude-genseo claude /login` by Kevin
# (Keychain cred state is per config dir). Until that login exists we fall back to
# the legacy 9router lane (works, but unrecognized model name → ~50% autocompact risk).
GENSEO_CFG="$HOME/.claude-genseo"
USE_NATIVE=0
if [ -d "$GENSEO_CFG" ]; then
  AUTH_JSON="$(CLAUDE_CONFIG_DIR="$GENSEO_CFG" "$HOME/.local/bin/claude" auth status 2>/dev/null || true)"
  case "$AUTH_JSON" in *'"loggedIn": true'*|*'"loggedIn":true'*) USE_NATIVE=1;; esac
fi

CLAUDE_BIN="$HOME/.local/bin/claude"
[ -x "$CLAUDE_BIN" ] || CLAUDE_BIN="$(command -v claude)"
if [ -z "$CLAUDE_BIN" ]; then echo "FATAL: claude CLI not found"; exit 1; fi

# Run from the repo so the native-lane config dir trusts exactly this workspace
# (trust for ~/genseo is seeded in ~/.claude-genseo/.claude.json).
cd "$HOME/genseo" || exit 1

LOGDIR="$HOME/genseo/logs"
mkdir -p "$LOGDIR"
STAMP="$(date +%Y%m%d-%H%M)"

PROMPT='Continue with the next ticket in /Users/kevinkreative/genseo/daily-tickets.md.

Rules for this run:
1. Take the FIRST ticket whose heading still contains `[ ]` (top-to-bottom). Process exactly ONE ticket, then STOP.
2. Follow the genseo-auto-publish skill end-to-end — if the Skill tool is unavailable, Read /Users/kevinkreative/genseo/skills/genseo-auto-publish/SKILL.md and follow it exactly: all 10 STEPs, STEP 0 dedup, STEP 0.5 topic fitness, images via scripts/article_images.py per the i5.2 UGC framework with --product-ref for any image containing a product, validate_article.py gate (exit 0 required), and BOTH post-publish gates.
   PACKAGING HARD RULE (Kevin 2026-08-09, after two wrong images shipped): pass --product-ref <handle> with NO :index. ~/genseo/product_refs/<handle>.png is the curated packaging truth and the wrapper injects its written description into the prompt. PDP indexes are marketing composites and some contain no package at all — generating against one produced an invented white pouch with the graphic stat badges pasted onto the label. If the wrapper warns a SKU has no curated ref, open the fallback ref, confirm the package is in it, and say so in the report; if it is not, stop and report that the SKU needs curating. Match product details beyond the label too (gummy colour = real flavour).
   HERO HARD RULE (Kevin 2026-08-08): the FIRST/hero image (it becomes the Shopify thumbnail/og:image) MUST show BOTH an approved-bank persona (visible face, ~/genseo/personas/ only) AND the real product pack label-forward — --persona-ref + --product-ref + --qc, NO --ugc. Default composition: the pack STANDS on a surface beside the model, hands NOT touching it, with "no hands touching the pouch" in the NEGATIVE (ima2 warps hand-pack grips; a holding pose is first-roll-only). The hero persona must DIFFER from previous articles hero personas — ALWAYS ls ~/genseo/personas/ and read each persona.json to enumerate the live bank (never assume its size from docs or prior reports), then rotate (least-recently-used, demo-appropriate). If no demo-appropriate different face exists, use the least-recently-used compliant persona and add "persona bank needs expansion" to the report. NEVER invent a fresh face.
3. Publish as DRAFT only (publisher default). NEVER pass --live.
4. Flip the ticket heading to [DONE <date> <url>] (or SKIPPED per skill rules), append the tracker CSV row, then git commit the genseo repo and try to push; if push fails for auth, keep the commit local and note "push pending" in the report — do not treat it as a run failure.
5. TEMPLATE ROTATION: pick the article template (EDITORIAL / STORY / LISTICLE / COMPARISON) per skills/genseo-auto-publish/references/article-templates.md — ticket type: field wins, else intent match, avoid repeating the previous articles template; use only the block kit in that reference (blank lines around HTML blocks, markdown outside blocks); log template:<KEY> in the tracker row and the report. Tickets marked type LISTICLE also follow the craft pointer in the ticket. Gates unchanged for every template.
6. If NO `[ ]` ticket remains: do NOT write an article. If the google-ads MCP is unavailable in this environment, append a line to daily-tickets.md under a "## Refill needed" heading asking Kevin to run the mining recipe in the app, and stop.
7. Finish with a report containing BOTH links on their own lines exactly as:
   ADMIN: https://admin.shopify.com/store/wellnessnest1/content/articles/<id>
   FRONTEND: https://wellnessnest.co/blogs/news/<handle>
   plus: article title, primary keyword, gate results, next ticket number.

STANDING APPROVALS (Kevin, 2026-08-08 — this run is unattended, never pause to ask):
- The mandatory media-cost gate is PRE-APPROVED for ima2 OAuth image generation only (ChatGPT subscription, $0 per image — hero + 3 inline per article). Do not stop to present a cost table for ima2; note "ima2 $0 subscription (standing approval)" in the report instead.
- This pre-approval covers NOTHING else: any paid media API (KIE, Veo, Kling, HeyGen, ElevenLabs, per-token image/video/audio) remains FORBIDDEN in this pipeline — if a step seems to need one, skip it, mark the ticket [BLOCKED <reason>], and report.
- If any OTHER rule requires human input, do not improvise: leave the ticket un-flipped, explain in the report, exit.

CONTEXT HYGIENE (a run died on "input exceeds the context window", 2026-08-09): never Read a whole large file — use offset/limit chunks for anything over ~500 lines; never cat/tail entire logs or HTML dumps; read only the sections of skill references you need. If a tool result looks huge, summarize and move on instead of re-reading it.'

echo "=== GenSeo ticket run $STAMP ===" >> "$LOGDIR/articles-$STAMP.log"
if [ "$USE_NATIVE" = "1" ]; then
  echo "(lane: native subscription via CLAUDE_CONFIG_DIR=$GENSEO_CFG)" >> "$LOGDIR/articles-$STAMP.log"
  CLAUDE_CONFIG_DIR="$GENSEO_CFG" "$CLAUDE_BIN" -p "$PROMPT" \
    --model opus \
    --output-format text \
    --allowed-tools "Read,Write,Edit,Bash,Glob,Grep,WebFetch" \
    >> "$LOGDIR/articles-$STAMP.log" 2>&1
  RC=$?
else
  echo "(lane: LEGACY 9router — run 'CLAUDE_CONFIG_DIR=~/.claude-genseo claude /login' on the mini to unlock the native lane)" >> "$LOGDIR/articles-$STAMP.log"
  # 9router's real per-request limit is smaller than the 200k the CLI assumes for the
  # unrecognized model name — three runs died on "input exceeds the context window"
  # (2026-08-09). Cap the window well below it so autocompact fires early enough.
  export CLAUDE_CODE_MAX_CONTEXT_TOKENS=150000
  "$CLAUDE_BIN" -p "$PROMPT" \
    --model opus \
    --output-format text \
    --allowed-tools "Read,Write,Edit,Bash,Glob,Grep,WebFetch" \
    >> "$LOGDIR/articles-$STAMP.log" 2>&1
  RC=$?
fi
echo "=== exit $RC ===" >> "$LOGDIR/articles-$STAMP.log"
bash "$HOME/genseo/scripts/notify_lark.sh" "$LOGDIR/articles-$STAMP.log" "$RC" >> "$LOGDIR/articles-$STAMP.log" 2>&1
exit $RC

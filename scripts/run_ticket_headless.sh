#!/bin/bash
# GenSeo headless ticket runner — called by launchd (com.pati.genseo-articles).
# Mirrors the proven pati-os dreams pattern: enrich launchd's minimal PATH,
# strip ANTHROPIC_API_KEY so claude CLI uses subscription OAuth, run one ticket.

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
# nvm-installed node (Mac mini lane) — ima2 is a node script and needs node on PATH
for d in "$HOME"/.nvm/versions/node/*/bin; do [ -d "$d" ] && PATH="$d:$PATH"; done
export PATH
unset ANTHROPIC_API_KEY

CLAUDE_BIN="$HOME/.local/bin/claude"
[ -x "$CLAUDE_BIN" ] || CLAUDE_BIN="$(command -v claude)"
if [ -z "$CLAUDE_BIN" ]; then echo "FATAL: claude CLI not found"; exit 1; fi

LOGDIR="$HOME/genseo/logs"
mkdir -p "$LOGDIR"
STAMP="$(date +%Y%m%d-%H%M)"

PROMPT='Continue with the next ticket in /Users/kevinkreative/genseo/daily-tickets.md.

Rules for this run:
1. Take the FIRST ticket whose heading still contains `[ ]` (top-to-bottom). Process exactly ONE ticket, then STOP.
2. Follow the genseo-auto-publish skill end-to-end — if the Skill tool is unavailable, Read /Users/kevinkreative/genseo/skills/genseo-auto-publish/SKILL.md and follow it exactly: all 10 STEPs, STEP 0 dedup, STEP 0.5 topic fitness, images via scripts/article_images.py per the i5.2 UGC framework with --product-ref for any image containing a product, validate_article.py gate (exit 0 required), and BOTH post-publish gates.
3. Publish as DRAFT only (publisher default). NEVER pass --live.
4. Flip the ticket heading to [DONE <date> <url>] (or SKIPPED per skill rules), append the tracker CSV row, then git commit the genseo repo and try to push; if push fails for auth, keep the commit local and note "push pending" in the report — do not treat it as a run failure.
5. If the ticket is marked type LISTICLE, follow the listicle format instructions in the ticket (craft: ~/PATI/LLM-Wiki/30-creative/32-copy/7-advertorial-listicle-presell-framework.md). Gates unchanged.
6. If NO `[ ]` ticket remains: do NOT write an article. If the google-ads MCP is unavailable in this environment, append a line to daily-tickets.md under a "## Refill needed" heading asking Kevin to run the mining recipe in the app, and stop.
7. Finish with a report containing BOTH links on their own lines exactly as:
   ADMIN: https://admin.shopify.com/store/wellnessnest1/content/articles/<id>
   FRONTEND: https://wellnessnest.co/blogs/news/<handle>
   plus: article title, primary keyword, gate results, next ticket number.

STANDING APPROVALS (Kevin, 2026-08-08 — this run is unattended, never pause to ask):
- The mandatory media-cost gate is PRE-APPROVED for ima2 OAuth image generation only (ChatGPT subscription, $0 per image — hero + 3 inline per article). Do not stop to present a cost table for ima2; note "ima2 $0 subscription (standing approval)" in the report instead.
- This pre-approval covers NOTHING else: any paid media API (KIE, Veo, Kling, HeyGen, ElevenLabs, per-token image/video/audio) remains FORBIDDEN in this pipeline — if a step seems to need one, skip it, mark the ticket [BLOCKED <reason>], and report.
- If any OTHER rule requires human input, do not improvise: leave the ticket un-flipped, explain in the report, exit.'

echo "=== GenSeo ticket run $STAMP ===" >> "$LOGDIR/articles-$STAMP.log"
"$CLAUDE_BIN" -p "$PROMPT" \
  --output-format text \
  --allowed-tools "Read,Write,Edit,Bash,Glob,Grep,WebFetch" \
  >> "$LOGDIR/articles-$STAMP.log" 2>&1
RC=$?
echo "=== exit $RC ===" >> "$LOGDIR/articles-$STAMP.log"
bash "$HOME/genseo/scripts/notify_lark.sh" "$LOGDIR/articles-$STAMP.log" "$RC" >> "$LOGDIR/articles-$STAMP.log" 2>&1
exit $RC

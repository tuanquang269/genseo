#!/bin/bash
# GenSeo headless ticket runner — called by launchd (com.pati.genseo-articles).
# Mirrors the proven pati-os dreams pattern: enrich launchd's minimal PATH,
# strip ANTHROPIC_API_KEY so claude CLI uses subscription OAuth, run one ticket.
#   scripts/run_ticket_headless.sh --print-prompt   # assembled prompt only; no model
#   GENSEO_ARTICLE_PRINT_SETTINGS=1 scripts/run_ticket_headless.sh  # --settings only; no model

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
# nvm-installed node (Mac mini lane) — ima2 is a node script and needs node on PATH
for d in "$HOME"/.nvm/versions/node/*/bin; do [ -d "$d" ] && PATH="$d:$PATH"; done
export PATH
unset ANTHROPIC_API_KEY
# --print-prompt writes the assembled writer prompt and exits before the model
# lane, the live-count guard, and claude. tests/test_article_prompt_waiver.sh
# uses it. No Shopify, no claude.
PRINT_PROMPT=0
if [ "${1:-}" = "--print-prompt" ]; then PRINT_PROMPT=1; shift; fi

# Same open-queue view as deploy/grokbot-genseo-daily.sh. state/queue-closures.json
# hides tickets already closed on article/* or publish/* after a return to main.
# A missing helper keeps the raw grep. An unreadable ledger fails closed.
queue_open_count() {
  local n="" script="$HOME/genseo/scripts/genseo_queue_closures.py"
  if [ ! -f "$script" ]; then
    n=$(grep -cE '^(- \[ \]|## \[ \])' "$1" 2>/dev/null || true)
    case "$n" in
      ''|*[!0-9]*) n=0 ;;
    esac
    printf '%s\n' "$n"
    return 0
  fi
  n=$(/usr/bin/python3 "$script" count --queue "$1" 2>/dev/null) || return 1
  case "$n" in
    ''|*[!0-9]*) return 1 ;;
  esac
  printf '%s\n' "$n"
}
queue_first_open() {
  local script="$HOME/genseo/scripts/genseo_queue_closures.py"
  if [ ! -f "$script" ]; then
    grep -m1 -E '^(- \[ \]|## \[ \])' "$1" 2>/dev/null || true
    return 0
  fi
  /usr/bin/python3 "$script" first --queue "$1" 2>/dev/null || return 1
}

# GENSEO_ARTICLE_PRINT_SETTINGS=1 prints the article-run --settings payload and exits
# before the model lane, the live-count guard, and claude.
# tests/test_article_prompt_waiver.sh uses it. No Shopify, no claude.
if [ "$PRINT_PROMPT" != 1 ] && [ "${GENSEO_ARTICLE_PRINT_SETTINGS:-0}" != "1" ]; then
# Pipeline scripts need Pillow/markdown. If the first python3 on PATH lacks them (MacBook: Homebrew 3.12),
# shim python3 -> /usr/bin/python3 for this run so the agent never trips on "No module named PIL".
if ! python3 -c 'import PIL, markdown' >/dev/null 2>&1 && /usr/bin/python3 -c 'import PIL, markdown' >/dev/null 2>&1; then
  mkdir -p "$HOME/genseo/state/pybin" && ln -sf /usr/bin/python3 "$HOME/genseo/state/pybin/python3"
  export PATH="$HOME/genseo/state/pybin:$PATH"
fi
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

# Writing lane (scripts/genseo_model_lane.sh). A PATI-* writer or fallback never uses native
# Claude login, even when ~/.claude-genseo is logged in: those ids are unrecognized_model
# there (landing 2026-10-10 09:30). An alias with no modelOverrides entry is refused
# before claude starts (landing 2026-10-15). Otherwise native login wins. Local 9router is used only
# when :20128 is up AND /v1/models lists the writer model — the Mini's global settings.json
# routes that lane, and a process env cannot override it there. A router that is up without
# the PATI writer alias (MacBook 2026-10-10: only ag/gemini-* ids) falls through to hosted
# ai.patigroup.com. Key from the env or the vault .env. Never printed. The hosted lane uses
# lean ~/.claude-genseo (no settings.json): the MacBook's global ~/.claude filled 450k
# tokens before the first ticket read (2026-10-06 09:57). The invocation below follows
# GENSEO_MODEL_LANE, not the raw login flag. Router lanes pass --permission-mode dontAsk:
# Claude Code 2.1.295+ defaults -p to auto, and auto mode uses the PATI model id as the
# Bash safety service (articles 2026-10-11 08:19). dontAsk keeps ALLOWED_TOOLS as the gate.
# shellcheck source=genseo_model_lane.sh
. "$HOME/genseo/scripts/genseo_model_lane.sh"
if ! genseo_select_model_lane; then
  mkdir -p "$HOME/genseo/logs"
  echo "[$(date '+%F %T')] FATAL: ${GENSEO_MODEL_LANE_ERROR:-no model lane}" >> "$HOME/genseo/logs/articles-retry.log"
  exit 1
fi

CLAUDE_BIN="$HOME/.local/bin/claude"
[ -x "$CLAUDE_BIN" ] || CLAUDE_BIN="$(command -v claude)"
if [ -z "$CLAUDE_BIN" ]; then echo "FATAL: claude CLI not found"; exit 1; fi

# Run from the repo so the native-lane config dir trusts exactly this workspace
# (trust for ~/genseo is seeded in ~/.claude-genseo/.claude.json).
cd "$HOME/genseo" || exit 1
# Empty queue — do not burn the model lane (Kevin/Grok Bot 2026-10-05; synced from Mini).
# Counts both ticket styles: "- [ ] **#NN" (2026-08-15+) and "## [ ] Ticket #NN" (batch 1-2).
_OPEN=$(queue_open_count "$HOME/genseo/daily-tickets.md") || exit 1
_OPEN=${_OPEN:-0}
if [ "$_OPEN" -eq 0 ]; then
  echo "[$(date '+%F %T')] retry skipped: ticket queue empty" >> "$HOME/genseo/logs/articles-retry.log"
  exit 0
fi
# Two-Mac failover guard (Kevin 2026-10-06: no automation may depend on one Mac). The live site is
# the shared state: if today's (ICT) target is already live — from EITHER Mac — do not start a ticket.
# Fails closed: an unreadable feed (-1) also stops the run rather than publishing blind.
_TARGET="${GENSEO_DAILY_TARGET:-5}"
_LIVE="$(/usr/bin/python3 "$HOME/genseo/scripts/genseo_published_today.py" 2>/dev/null | tail -1)"
case "$_LIVE" in ''|*[!0-9-]*) _LIVE=-1;; esac
if [ "$_LIVE" -lt 0 ] || [ "$_LIVE" -ge "$_TARGET" ]; then
  echo "[$(date '+%F %T')] $(hostname -s) skipped: live today=$_LIVE target=$_TARGET" >> "$HOME/genseo/logs/articles-retry.log"
  exit 0
fi
fi

PROMPT='ARTICLE ALREADY APPROVED. Write and publish this one blog article in this run. The always-on file-count scope gate is off: more than 2 output files does not mean show a menu and wait. Do not show a file-count menu. Do not wait. Do not ask a human to proceed.

Continue with the next ticket in /Users/kevinkreative/genseo/daily-tickets.md.

Rules for this run:
1. Take the ticket named in the QUEUE POINTER at the end of this prompt. That line is the first heading that still starts with "- [ ]" or "## [ ]". Process exactly ONE ticket, then STOP. Do not decide the queue is empty from an older "Refill needed" or "queue is EMPTY" section. daily-tickets.md is longer than 500 lines; those notes are history above later open tickets.
2. Follow the genseo-auto-publish skill end-to-end — if the Skill tool is unavailable, Read /Users/kevinkreative/genseo/skills/genseo-auto-publish/SKILL.md and follow it exactly: all 10 STEPs, STEP 0 dedup, STEP 0.5 topic fitness, images via scripts/article_images.py per the i5.2 UGC framework with --product-ref for any image containing a product, validate_article.py gate (exit 0 required), and BOTH post-publish gates.
   PACKAGING HARD RULE (Kevin 2026-08-09, after two wrong images shipped): pass --product-ref <handle> with NO :index. ~/genseo/product_refs/<handle>.png is the curated packaging truth and the wrapper injects its written description into the prompt. PDP indexes are marketing composites and some contain no package at all — generating against one produced an invented white pouch with the graphic stat badges pasted onto the label. If the wrapper warns a SKU has no curated ref, open the fallback ref, confirm the package is in it, and say so in the report; if it is not, stop and report that the SKU needs curating. Match product details beyond the label too (gummy colour = real flavour).
   HERO HARD RULE (Kevin 2026-08-08): the FIRST/hero image (it becomes the Shopify thumbnail/og:image) MUST show BOTH an approved-bank persona (visible face, ~/genseo/personas/ only) AND the real product pack label-forward — --persona-ref + --product-ref + --qc, NO --ugc. Default composition: the pack STANDS on a surface beside the model, hands NOT touching it, with "no hands touching the pouch" in the NEGATIVE (ima2 warps hand-pack grips; a holding pose is first-roll-only). Feed the exact hero_ref path the picker prints (see the PERSONA ROTATION rule below), never a previous gen. NEVER invent a fresh face.
   PERSONA ROTATION HARD RULE (Kevin 2026-08-09 — "prepare 200 referenced different models as hard rule"): NEVER choose the hero persona, the gaze or the shot type yourself, and NEVER grep the tracker CSV for them. Run `/usr/bin/python3 scripts/persona_picker.py pick --audience <token>` (or `--brand <Brand>` when the ticket names no audience; valid tokens are in personas/taxonomy.json) and obey its JSON exactly: hero, hero_ref, hero_gaze, hero_shot, inline_gaze, hero_face_angle, inline_face_angle (+ the *_phrase fields, which go into the prompt verbatim). The picker enforces pool-scoped least-recently-used rotation, the one-angle-per-model law, the no-repeat gaze law (the `to-camera` family never twice running for one face, and never on hero and inline within one article), the last-3 shot window and the every-3rd-hero no-face cycle MECHANICALLY. Free-text notes in the CSV are no longer the source of truth: parsing them on 2026-08-09 returned "no-contact" and "bank" as persona handles, which is precisely how a 200-face bank would silently rot back into reusing one face. Echo every picker warning into the report verbatim. If pick prints hero NO-FACE, compose a product-in-a-real-scene or scene-only hero — still --product-ref + --qc, still no --ugc, no face at all; a face plus a pack on every single row is the structural tell that gaze rotation cannot reach. An empty or angle-exhausted pool now DEGRADES to a NO-FACE pick with the shortfall in warnings[] rather than exiting: report it, do NOT invent a face and do NOT borrow a wrong-demographic one. A non-zero exit means a bad audience token or unreadable state — fix it, never route around it. FACE ANGLE HARD RULE (Kevin 2026-08-10 — "khong bao gio generate cung 1 goc mat cho 1 model"): each persona has 21 head angles and each is spent PERMANENTLY on first use (hero and inline count separately). Pass --face-angle <hero_face_angle> to article_images.py for the hero and --face-angle <inline_face_angle> for the inline persona-in-scene image, and put the matching *_phrase into the prompt verbatim; the wrapper refuses an angle that persona already spent and QC FAILs a head that does not match the brief. Never substitute an angle of your own. PICK ALREADY SPENT THE ANGLES. As of 2026-08-11 `pick` reserves what it issues the moment it prints it, so the assignment is binding whether or not this article ever ships — you can never be handed those two angles again. That closes the hole where a run died between pick and commit and the very next pick returned a byte-identical hero, angle for angle, onto a second live og:image. So: run pick EXACTLY ONCE per article, and if you find yourself picking twice, the second assignment is the real one and the first must be released. AFTER a successful LIVE publish and never before, run `/usr/bin/python3 scripts/persona_picker.py commit --hero <h> --gaze <g> --inline-gaze <ig> --shot <s> --face-angle <a> --inline-face-angle <ia> --expect-seq <seq from pick>`; --expect-seq is now MANDATORY (it names which reservation is being closed), --face-angle is mandatory for a face hero, and commit refuses a repeat rather than deduping it. A non-zero exit there means the commit disagrees with what pick issued — wrong hero, an angle the picker never handed out, or a reservation already closed — so read the message and fix the article; do NOT force it and do NOT hand-edit personas/index.json. If the article does NOT publish (gate failure, abort, QC out of re-rolls), run `/usr/bin/python3 scripts/persona_picker.py release --seq <seq from pick>` so the angles go back; skipping it costs two of the twenty-one angles that persona has and nothing else, so when in doubt leave them burned rather than releasing an article that might in fact be live.
   PROMPT WORDING (still yours to write): say the picker gaze in plain words — gaze is where the EYES point WITHIN the head, a separate axis from face_angle (where the head points) and shot (where the camera is); never write a phrase that fights the assigned head angle. Write the shot type into the prompt, and vary at least one of framing / expression register / wardrobe colour between articles. The pack label must stay legible at thumbnail size — that limits how far it recedes, not which shot the picker chose. The inline persona-in-scene image reuses the SAME face (one persons story) but MUST use inline_gaze, not hero_gaze.
3. Publish LIVE — ALWAYS pass --live to shopify_publisher.py. Kevin ended the draft-review period in writing on 2026-08-09 ("just auto publish visible. I will do QA step even after you publish"), so the article must be visible to the public the moment this run finishes; he QAs on the live site. After publishing, confirm the article JSON has a non-null published_at AND that the frontend URL returns HTTP 200 with a browser User-Agent (a bare curl gets throttled). A draft that reports success but 404s for visitors is a FAILED run, not a completed one.
4. Flip the ticket heading to [DONE <date> <url>] (or SKIPPED per skill rules), append the tracker CSV row, then git commit the genseo repo and try to push; if push fails for auth, keep the commit local and note "push pending" in the report — do not treat it as a run failure.
5. TEMPLATE ROTATION: pick the article template (EDITORIAL / STORY / LISTICLE / COMPARISON) per skills/genseo-auto-publish/references/article-templates.md — ticket type: field wins, else intent match, avoid repeating the previous articles template; use only the block kit in that reference (blank lines around HTML blocks, markdown outside blocks); log template:<KEY> in the tracker row and the report. Tickets marked type LISTICLE also follow the craft pointer in the ticket. Gates unchanged for every template.
6. If the QUEUE POINTER says 0 open tickets: do NOT write an article. If the google-ads MCP is unavailable in this environment, append a line to daily-tickets.md under a "## Refill needed" heading asking Kevin to run the mining recipe in the app, and stop. If the pointer names an open line, that ticket is open — do not append a refill note.
7. Finish with a report containing BOTH links on their own lines exactly as:
   ADMIN: https://admin.shopify.com/store/wellnessnest1/content/articles/<id>
   FRONTEND: https://wellnessnest.co/blogs/news/<handle>
   plus: article title, primary keyword, gate results, next ticket number.

STANDING APPROVALS (Kevin, 2026-08-08 — this run is unattended, never pause to ask):
- The mandatory media-cost gate is PRE-APPROVED for ima2 OAuth image generation only (ChatGPT subscription, $0 per image — hero + 3 inline per article). Do not stop to present a cost table for ima2; note "ima2 $0 subscription (standing approval)" in the report instead.
- This pre-approval covers NOTHING else: any paid media API (KIE, Veo, Kling, HeyGen, ElevenLabs, per-token image/video/audio) remains FORBIDDEN in this pipeline — if a step seems to need one, skip it, mark the ticket [BLOCKED <reason>], and report.
- If any OTHER rule requires human input, do not improvise: leave the ticket un-flipped, explain in the report, exit. The file-count scope gate is not one of those rules. The SCOPE_WAIVER at the end of this prompt turns that gate off for this blog article.

CONTEXT HYGIENE (a run died on "input exceeds the context window", 2026-08-09): never Read a whole large file — use offset/limit chunks for anything over ~500 lines; never cat/tail entire logs or HTML dumps; read only the sections of skill references you need. If a tool result looks huge, summarize and move on instead of re-reading it. For daily-tickets.md, start at the QUEUE POINTER line instead of byte 0.

TWO-MAC FAILOVER RULES (Kevin 2026-10-06 — GenSeo runs on whichever Mac is online; the Mini and the MacBook keep separate ticket files):
A. DOUBLE-PUBLISH GUARD: immediately BEFORE running shopify_publisher.py, run `/usr/bin/python3 scripts/genseo_published_today.py` — if it prints a number >= '"${GENSEO_DAILY_TARGET:-5}"' (or -1), do NOT publish: release any persona reservation, leave the ticket un-flipped, report "daily target already live" and stop. Then re-run STEP 0 (suggest.json for the primary keyword) at that same moment: if an article for this keyword went live since you started (the other Mac may have shipped it), mark the ticket [SKIPPED-DUPLICATE <date> <url>] and stop.
B. FACT-CHECK LOG (Google calls manual fact-checking of AI content critical, SEL 2026-10-06): before publishing, write logs/claims/<slug>.md with one line per factual claim (number, study, dose, mechanism): claim | source URL | fetched+confirmed Y/N. Delete from the draft any claim you could not confirm from a source you actually fetched. Mention the claim count in the report.
C. AgeAura = NMN + TMG only. Never mention, link or picture Urolithin A in any article. If the next open ticket is about Urolithin A (or AgeAura Urolithin A), mark it [SKIPPED-UNFIT <date> AgeAura is NMN+TMG only] and take the following ticket instead.
G. FloraFresh formula = its Supplement Facts label: Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies, Vitamin C 30 mg, pineapple fruit powder 100 mg (with bromelain), sweetened with maltitol + isomalt (NOT sugar-free). The live PDP description and older FloraFresh articles carry a wrong formula (15 billion CFU, four Lactobacillus strains, XOS, D-mannose, sugar-free): never copy formula facts from them, cite the label. validate_article.py fails any FloraFresh claim the label does not support (python3 scripts/florafresh_rules.py --brief prints the label line).
S. Shilajit Shockwave pack label is product_refs/shilajit-shockwave.label.json: wellness, nest, SHILAJIT, SHOCKWAVE, EXPERIENCE FOCUSED ENERGY, PEAK PERFORMANCE. That file has no milligram amount, no serving count, and no volume line. Do not state one. python3 scripts/shockwave_rules.py --brief prints the line. Premium Himalayan Shilajit Gummies, Pure Shilajit Gold Resin, and ShilaSource resin are separate products and are not covered by this rule.
R. Pure Shilajit Gold Resin pack label is product_refs/pure-shilajit-gold-resin.label.json. Repeat only that file'\''s required and optional lines, including the OCR serving line and 75% Fulvic. No milligram amount was read. Do not add one. Do not state a different serving count, volume, weight, or day-supply. python3 scripts/gold_resin_rules.py --brief prints the line. Premium Himalayan Shilajit Gummies, Shilajit Shockwave, and ShilaSource resin are separate products and are not covered by this rule.
L. ShilaSource Himalayan Shilajit Resin pack label is product_refs/shilasource-himalayan-shilajit-resin.label.json. Repeat only that file'\''s required and optional lines. No milligram amount and no Supplement Facts panel were read into that file. Do not add one. Do not state a serving count, volume, weight, fulvic percentage, mineral count, or day-supply other than those lines. python3 scripts/shilasource_resin_rules.py --brief prints the line. Premium Himalayan Shilajit Gummies, Shilajit Shockwave, and Pure Shilajit Gold Resin are separate products and are not covered by this rule.
T. Turkesterone Advanced Formula pack label is product_refs/turkesterone-advanced-formula.label.json. Repeat only that file'\''s required and optional lines. No milligram amount and no Supplement Facts panel were read into that file. Do not add one. The capsule badge is the separate lines 60 and Capsules. Do not state a milligram amount, a serving count, a different capsule count, or a day-supply. python3 scripts/turkesterone_rules.py --brief prints the line. Bare turkesterone (the ingredient) is not this SKU. Premium Himalayan Shilajit Gummies, Shilajit Shockwave, Pure Shilajit Gold Resin, and ShilaSource resin are separate products and are not covered by this rule.
F. Never run Bash commands in the background (no run_in_background, no trailing &): this is a one-shot -p run and it ENDS when you stop talking, killing background image jobs (2026-10-06 10:47 a run exited mid-images). Run image generations in the foreground, one or several per command.
E. NEVER modify an existing live post: no [REFRESH EXISTING], no shopify_publisher.py update on an article you did not create in this run. If STEP 0/0.5 says refresh or duplicate, mark the ticket SKIPPED and move to the next one.
D. People are the default article image lane (the env value GENSEO_NO_FACE is exactly 1; this run: '"${GENSEO_NO_FACE:-0}"'). That printed value does not switch this run onto a no-face lane, including when a stale LaunchAgent still exports 1. A ticket batch header that says "ALL images NO-FACE", including the 2026-10-06 MacBook failover batches, does not switch this run either. Run persona_picker.py once and follow the HERO / PERSONA ROTATION / FACE ANGLE rules. The hero shows the picked face and the real pack unless pick prints hero NO-FACE (every 3rd hero, or an empty bank). One inline image uses that same face. The other inline images have no recognizable face but still show a person (a hand, a forearm, or a body cropped below the eyes), not an empty pack-only still life. If ima2 refuses a face prompt or that one image fails QC after the two allowed re-rolls, replace only that image with this human no-face fallback and release the angle if the published article will not use it. Do not turn the rest of the article into empty product shots. Log "persona: none (failover no-face)" only when pick itself printed hero NO-FACE.

SCOPE_WAIVER (Kevin, standing approval for the daily blog article):
- This run writes and publishes one blog article from daily-tickets.md. Kevin already approved that package on 2026-08-09 (auto publish visible). Do not ask a human to proceed. Do not stop on a scope gate.
- The always-on scope gate is off. That rule says more than 2 output files, show a menu with real file counts, then wait, and silence means the smallest set. Do not show that menu. Do not wait. Silence does not mean 0 files. The full package is the approved deliverable.
- The full package for this one ticket is the draft, the hero image, at least 3 inline images, logs/claims/<slug>.md, the tracker CSV row, and the ticket heading update. Write those files. Do not offer a smaller set.
- Do not ask "Proceed with the full live publish package?" That question and an exit with the ticket still open is the 2026-10-12 failure (logs/articles-20261012-0750.log, 0752, 0755, ticket #MB1009-7 unchanged).
- The bullet that says to exit when some other rule requires human input does not apply to this scope gate. Leaving the ticket `[ ]` and writing no draft is a failed run.
- A ticket template named LISTICLE is still this blog article. Publish it live after validate_article.py prints PASS, using scripts/shopify_publisher.py --live. This waiver does not publish a landing-page listicle, a gsl- page, or any file under landing_drafts/.
- ima2 image generation stays the $0 standing approval. Do not stop for a cost table.'

# 2026-10-16: the writer read the August "queue is EMPTY" note (the file is
# longer than the 500-line read cap) and exited 0 while the wrapper still
# counted open "- [ ]" tickets. Name the grep hit in the prompt.
# Rule D above splices GENSEO_NO_FACE as "this run: N". Do not write
# GENSEO_NO_FACE=$N = 1 — that quote break rendered as "GENSEO_NO_FACE=1 = 1".
TICKET_FILE="$HOME/genseo/daily-tickets.md"
# Same view as deploy/grokbot-genseo-daily.sh, including the closure ledger.
# A CRLF ticket file still matches; drop the trailing CR so the pointer is one line.
FIRST_OPEN="$(queue_first_open "$TICKET_FILE")" || exit 1
FIRST_OPEN="${FIRST_OPEN%$'\r'}"
OPEN_N="$(queue_open_count "$TICKET_FILE")" || exit 1
case "$OPEN_N" in
  ''|*[!0-9]*) OPEN_N=0 ;;
esac
# 2026-10-16 7a33142 put a NO-FACE LANE banner on the first line whenever
# GENSEO_NO_FACE=1. The MacBook article plist has exported 1 since 2026-10-06
# (26a706e). After that banner, every article through 2026-10-19 logged
# "persona: none" and the pictures lost people. The value is still printed in
# rule D so a stale plist is visible. It does not switch the lane. No-face is
# the per-image fallback in rule D, after a face refusal or two QC misses.
if [ -n "$FIRST_OPEN" ]; then
  PROMPT="$PROMPT

QUEUE POINTER (shell grep of daily-tickets.md, same pattern as the daily wrapper):
Open tickets: $OPEN_N
First open line:
$FIRST_OPEN
Process that ticket and no other. Older sections that say the queue is EMPTY or \"## Refill needed\" are history. Do not append a refill note while this line is still open. Lines listed in state/queue-closures.json are already closed on this Mac. This pointer already skipped them. Do not process a skipped line."
else
  PROMPT="$PROMPT

QUEUE POINTER (shell grep of daily-tickets.md, same pattern as the daily wrapper):
Open tickets: 0
First open line:
(none)
Do not write an article."
fi

if [ "$PRINT_PROMPT" = 1 ]; then
  printf '%s\n' "$PROMPT"
  exit 0
fi

# 2026-10-12 #MB1009-7: the hosted lane still loaded ~/.claude/CLAUDE.md as User
# memory. CLAUDE_CONFIG_DIR does not stop that load. That file's always-on scope
# gate said more than 2 output files, show a menu, then wait. Three runs printed
# the menu and exited 0 with the ticket still open (logs/articles-20261012-0750.log,
# 0752, 0755). claudeMdExcludes drops that User file (and the wiki path it
# symlinks to) on every article run, native and router. Project CLAUDE.md,
# AGENTS.md, and this prompt stay. Live publish stays scripts/shopify_publisher.py
# after validate_article.py prints PASS. --settings merges; it does not replace
# the lane's auth or permission flags.
SETTINGS_ARGS=()
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
fi
if [ "${GENSEO_ARTICLE_PRINT_SETTINGS:-0}" = "1" ]; then
  if [ "${#SETTINGS_ARGS[@]}" -gt 0 ]; then
    printf '%s\n' "${SETTINGS_ARGS[@]}"
  fi
  exit 0
fi

LOGDIR="$HOME/genseo/logs"
mkdir -p "$LOGDIR"
STAMP="$(date +%Y%m%d-%H%M)"

# Both lanes get the same grant, declared once so they cannot drift apart.
# WebSearch added 2026-08-12. It was missing, and its absence was silent: the skill's STEP 2
# (long-tail / question-keyword expansion) and STEP 3 (competitor SERP + People-Also-Ask harvest)
# both run on WebSearch, so in the cron lane they were structurally impossible. Runs did not fail
# on it — they wrote the article from the ticket brief alone and mentioned it at the bottom of the
# report ("WebSearch permission wasn't granted"), which is the worst failure mode available: every
# unattended article shipped without the SERP research the skill says it is built on.
ALLOWED_TOOLS="Read,Write,Edit,Bash,Glob,Grep,WebFetch,WebSearch"

echo "=== GenSeo ticket run $STAMP ===" >> "$LOGDIR/articles-$STAMP.log"
genseo_lane_log_line >> "$LOGDIR/articles-$STAMP.log"
genseo_claude_model_log_line >> "$LOGDIR/articles-$STAMP.log"
if [ -z "$SETTINGS_JSON" ]; then
  echo "WARN: claudeMdExcludes settings were not built; prompt waiver only" >> "$LOGDIR/articles-$STAMP.log"
fi
# Native invocation only when the picker kept the login lane. A PATI-* writer
# clears USE_NATIVE and sets local-9router or hosted-9router instead.
# Both lanes pass claudeMdExcludes. The user scope-gate file loads as User
# memory even when CLAUDE_CONFIG_DIR is the lean lane.
# A non-Anthropic HTTP 200 (OpenAI chat.completion from a PATI alias) re-execs
# once on GENSEO_WRITER_FALLBACK. The prompt, including live publish after the
# article gate, is the same on that re-exec.
if [ "${GENSEO_MODEL_LANE:-}" = "native" ]; then
  CLAUDE_CONFIG_DIR="$GENSEO_CFG" genseo_run_writer_with_shape_fallback \
    "$LOGDIR/articles-$STAMP.log" "$CLAUDE_BIN" \
    -p "$PROMPT" \
    --fallback-model "$GENSEO_WRITER_FALLBACK" \
    "${SETTINGS_ARGS[@]}" \
    --output-format text \
    --allowed-tools "$ALLOWED_TOOLS"
  RC=$?
else
  # 9router's real per-request limit is smaller than the 200k the CLI assumes for the
  # unrecognized model name — three runs died on "input exceeds the context window"
  # (2026-08-09). Cap the window well below it so autocompact fires early enough.
  # dontAsk: auto mode would name the PATI writer as the Bash safety service and
  # block every script before a write. The lane sets this; the default covers a miss.
  export CLAUDE_CODE_MAX_CONTEXT_TOKENS=150000
  : "${GENSEO_PERMISSION_MODE:=dontAsk}"
  genseo_run_writer_with_shape_fallback \
    "$LOGDIR/articles-$STAMP.log" "$CLAUDE_BIN" \
    -p "$PROMPT" \
    --fallback-model "$GENSEO_WRITER_FALLBACK" \
    --permission-mode "$GENSEO_PERMISSION_MODE" \
    "${SETTINGS_ARGS[@]}" \
    --strict-mcp-config \
    --output-format text \
    --allowed-tools "$ALLOWED_TOOLS"
  RC=$?
fi
echo "=== exit $RC ===" >> "$LOGDIR/articles-$STAMP.log"
bash "$HOME/genseo/scripts/notify_lark.sh" "$LOGDIR/articles-$STAMP.log" "$RC" >> "$LOGDIR/articles-$STAMP.log" 2>&1
exit $RC

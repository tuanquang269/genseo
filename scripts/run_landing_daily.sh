#!/bin/bash
# GenSeo DAILY listicle landing page — ONE unpublished Shopify draft per day for Kevin to approve (Kevin 2026-10-08).
# NEVER publishes: landing_publisher.py --draft only (published:false), --live is refused in this lane, and the
# wrapper re-checks the page afterwards and force-hides it if anything ever made it visible.
# REAL render QA (Kevin 2026-10-08): landing_real_qa.py checks theme/template/body parity read-only, then screenshots the
# REAL storefront in a ~40 s gsl-preview window (on -> screenshot -> off in a finally) so approval never rests on a local
# render. GENSEO_LANDING_REAL_QA_WINDOW=0 keeps the parity checks but skips the window.
# launchd com.pati.genseo-landing: 08:15 + 16:15 catch-up, on WHICHEVER Mac is online (deploy/com.pati.genseo-landing.*.plist).
#
# One-page-per-day guarantee across the two Macs (they share no writable state -> Shopify is the shared state):
#   1. landing_guard.py: a page with a 'gsl-' handle created today (ICT) already exists -> stand down   [both Macs]
#      (Shopify unreadable -> fail closed, build nothing)
#   2. GENSEO_HOST_ROLE=standby (MacBook) waits GENSEO_LANDING_STANDBY_DELAY_MIN (default 75) first, so a healthy
#      Mini (primary) finishes its draft and rule 1 makes this Mac stand down; then re-checks the guard
#   3. landing_publisher.py (GENSEO_LANDING_DAILY=1) re-runs landing_guard.py right before it POSTs a NEW page
#   4. local mkdir lock: the 16:15 catch-up never overlaps a still-running 08:15 run on the same Mac
#   5. this Mac's article batch (state/daily.lock) only gets a short courtesy yield, never the whole day: wait while it
#      runs, at most GENSEO_LANDING_ARTICLE_YIELD_MIN (default 30) wall-clock minutes, re-checking every
#      GENSEO_LANDING_POLL_SEC (default 60) s, then re-check rule 1 and build ALONGSIDE it. Overlap is safe: this lane
#      only ever writes a Shopify PAGE, never a blog article (article publishing stays serialized by daily.lock and the
#      article lane's own guards); pages never reach /blogs/news.atom (the article live-count + peer guards); and
#      ima2 serve admits parallel jobs (it renders 3 at a time on its one OAuth session by itself).
#   6. the listicle writer is its own session for 90 min (GENSEO_LANDING_TIMEOUT_SEC, default 5400).
#      scripts/genseo_group_timeout.sh TERM then KILLs that process group (landing bash and Claude).
# Kill switch: touch state/landing-daily.disabled (or GENSEO_LANDING_DAILY_ENABLED=0).
set -uo pipefail
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
for d in "$HOME"/.nvm/versions/node/*/bin; do [ -d "$d" ] && PATH="$d:$PATH"; done; export PATH
G="$HOME/genseo"; PY=/usr/bin/python3; cd "$G" || exit 1
ROLE="${GENSEO_HOST_ROLE:-primary}"; DELAY="${GENSEO_LANDING_STANDBY_DELAY_MIN:-75}"
YIELD="${GENSEO_LANDING_ARTICLE_YIELD_MIN:-30}"; POLL="${GENSEO_LANDING_POLL_SEC:-60}"
LANDING_TIMEOUT="${GENSEO_LANDING_TIMEOUT_SEC:-5400}"
case "$LANDING_TIMEOUT" in
  ''|*[!0-9]*|0) LANDING_TIMEOUT=5400 ;;
esac
HOST="$(hostname -s)"; DAY="$(TZ=Asia/Saigon date +%F)"
LOGDIR="$G/logs/landing-daily"; mkdir -p "$LOGDIR" "$G/state"; LOG="$LOGDIR/$DAY.log"
LOCK="$G/state/landing-daily.lock"; MINE="$G/state/landing-by-$HOST.log"; ART_LOCK="$G/state/daily.lock"
QUEUE="daily-landing-tickets.md"
ts(){ date '+%F %T'; }
say(){ echo "[$(ts)] [$HOST/$ROLE] $*" | tee -a "$LOG"; }
# sleep until the wall clock reaches epoch $1 in <= POLL s steps, ending early once the optional condition command
# (args 2..) fails; a deadline instead of a count of sleeps, so a Mac that dozes off mid-wait cannot stretch the wait
wait_until(){ local end=$1 now; shift; while now=$(date +%s); [ "$now" -lt "$end" ] && { [ $# = 0 ] || "$@"; }; do sleep $(( end - now < POLL ? end - now : POLL )); done; }
# Courtesy yield only. A daily.lock directory younger than 6h counts as "the article batch may be
# running"; one that vanishes mid-check counts as released (an empty stat inside $(( )) would abort
# this script). The article wrapper does not steal its lock for age while a live grokbot-genseo-daily
# matches — this yield does not read that PID. Past 6h it builds alongside, which is safe (a page,
# never a blog article).
articles_running(){ local m; m="$(stat -f %m "$ART_LOCK" 2>/dev/null)" && [ $(( $(date +%s) - m )) -lt 21600 ]; }

[ "${GENSEO_LANDING_DAILY_ENABLED:-1}" = "1" ] && [ ! -e "$G/state/landing-daily.disabled" ] || { say "disabled (kill switch) — exit"; exit 0; }
if [ ! -f "$G/scripts/genseo_group_timeout.sh" ]; then
  say "FATAL: missing scripts/genseo_group_timeout.sh — git pull ~/genseo"
  exit 1
fi
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ $(( $(date +%s) - $(stat -f %m "$LOCK") )) -gt 14400 ]; then rmdir "$LOCK"; mkdir "$LOCK" || exit 1
  else say "another landing run is active on this Mac — exit"; exit 0; fi
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

guard(){ $PY scripts/landing_guard.py >> "$LOG" 2>&1; }
guard; g=$?
[ $g = 3 ] && { say "DONE: today's gsl- landing draft already exists — nothing to do"; exit 0; }
[ $g != 0 ] && { say "guard: Shopify unreadable — fail closed"; exit 1; }
say "start: no gsl- landing draft yet today ($DAY ICT)"
if [ "$ROLE" = "standby" ] && [ "${GENSEO_NO_DELAY:-0}" != "1" ]; then
  say "standby: waiting ${DELAY} min so a healthy peer Mac goes first"; wait_until $(( $(date +%s) + DELAY * 60 ))
  guard; g=$?
  [ $g = 3 ] && { say "peer Mac already made today's draft — stand down"; exit 0; }
  [ $g != 0 ] && { say "guard: Shopify unreadable — fail closed"; exit 1; }
fi
if articles_running; then
  say "article batch running on this Mac (state/daily.lock) — yielding up to ${YIELD} min, then building alongside it"
  wait_until $(( $(date +%s) + YIELD * 60 )) articles_running
  if articles_running; then say "article batch still running — building alongside it (this lane writes a Shopify page, never a blog article)"
  else say "article batch finished — building now"; fi
  guard; g=$?
  [ $g = 3 ] && { say "draft appeared meanwhile — stand down"; exit 0; }
  [ $g != 0 ] && { say "guard: Shopify unreadable — fail closed"; exit 1; }
fi

# reviews (real 4-5★ only); a failure is not fatal — the agent then leaves the review slot as a placeholder
NODE_PATH="$(npm root -g)" node scripts/trustpilot_reviews.mjs >> "$LOG" 2>&1 || say "WARN: Trustpilot refresh failed — page will carry a review placeholder"
$PY scripts/build_landing_tickets.py >> "$LOG" 2>&1 || { say "ticket builder failed — see log"; exit 1; }
if ! $PY scripts/lint_tickets.py "$QUEUE" >> "$LOG" 2>&1; then say "lint_tickets FAILED on $QUEUE — stopping"; exit 1; fi
LINE="$(grep -m1 -E '^- \[ \] ' "$QUEUE")"
[ -z "$LINE" ] && { say "no open landing ticket — stopping"; exit 1; }
say "ticket: $LINE"
STAMP="$(date +%Y%m%d-%H%M)"; RUNLOG="logs/landing-daily-$STAMP.log"; START=$(date +%s)
GENSEO_LANDING_DAILY=1 GENSEO_LANDING_DRAFT=1 GENSEO_NO_FACE=1 GENSEO_LANDING_LOG="$RUNLOG" \
  /bin/bash "$G/scripts/genseo_group_timeout.sh" "$LANDING_TIMEOUT" \
  /bin/bash scripts/run_landing_headless.sh --queue "$QUEUE" --next >> "$LOG" 2>&1; RC=$?
say "agent exit $RC (log $RUNLOG)"

# post-checks done HERE, independent of what the agent reported
SPEC="$(grep -oE 'SPEC: *[^ ]+\.json' "$RUNLOG" 2>/dev/null | tail -1 | sed -E 's/SPEC: *//')"
if [ -z "$SPEC" ] || [ ! -f "$SPEC" ]; then
  SPEC="$($PY - "$DAY" "$START" <<'PY'
import glob, json, os, sys
day, start = sys.argv[1], int(sys.argv[2])
c = [p for p in glob.glob("landing_drafts/*.json") if os.path.getmtime(p) >= start]
c = [p for p in c if (lambda s: s.get("daily") or s.get("created") == day)(json.load(open(p)))]
print(max(c, key=os.path.getmtime) if c else "")
PY
)"
fi
[ -n "$SPEC" ] && SPEC="${SPEC#$G/}"
tag(){ $PY - "$LINE" "$1" "$QUEUE" <<'PY'
import sys
line, tag, p = sys.argv[1:4]; s = open(p).read()
open(p, "w").write(s.replace(line, line.replace("- [ ]", f"- [{tag}]", 1), 1))
PY
}
if [ -z "$SPEC" ] || [ ! -f "$SPEC" ]; then
  say "FAILED: no spec produced"; tag "FAILED $DAY no spec (see $RUNLOG)"; exit 1
fi
SLUG="$($PY -c 'import json,sys;print(json.load(open(sys.argv[1]))["slug"])' "$SPEC")"; OUT="landing_drafts/$SLUG"
$PY scripts/validate_landing.py "$SPEC" >> "$LOG" 2>&1; V=$?
$PY scripts/landing_render.py "$SPEC" >> "$LOG" 2>&1
$PY scripts/landing_palette.py check "$SPEC" >> "$LOG" 2>&1; PAL=$?   # packaging palette gate (Kevin 2026-10-09)
QA="$(NODE_PATH="$(npm root -g)" node scripts/landing_qa.mjs "$OUT/preview.html" 2>>"$LOG")"; Q=$?
echo "$QA" > "$OUT/qa.json"
QOK="$($PY -c 'import json,sys
d=json.load(open(sys.argv[1])); bad=[w for w,r in d["widths"].items() if r["overflow"]]; cl=[w for w,r in d["widths"].items() if r.get("clipped")]
print("ok" if not bad and not cl else ("overflow@"+",".join(bad) if bad else "clipped@"+",".join(cl)))' "$OUT/qa.json" 2>/dev/null || echo "qa-error")"
[ $Q != 0 ] && QOK="qa-error"
for f in desktop mobile; do [ -f "$OUT/$f.png" ] && sips -s format jpeg -s formatOptions 70 "$OUT/$f.png" --out "$OUT/$f.jpg" >/dev/null 2>&1; done
# what Kevin will actually see: the real Shopify storefront render (not preview.html)
RQ="skip"
if [ -f "$OUT/shopify.json" ]; then
  if $PY scripts/landing_real_qa.py "$SPEC" >> "$LOG" 2>&1; then RQ=ok; else RQ=fail; fi
  for f in desktop mobile offer; do [ -f "$OUT/real-$f.png" ] && sips -s format jpeg -s formatOptions 70 "$OUT/real-$f.png" --out "$OUT/real-$f.jpg" >/dev/null 2>&1; done
fi
# the page must exist and be UNPUBLISHED; anything visible gets hidden on the spot
PSTATE="$($PY - "$OUT/shopify.json" <<'PY'
import json, os, sys, urllib.request
sys.path.insert(0, "scripts"); os.environ["GENSEO_PUBLISHER_REEXEC"] = "1"
import genseo_config as cfg
from shopify_auth import pick
if not os.path.exists(sys.argv[1]): print("nopage"); sys.exit()
rec = json.load(open(sys.argv[1])); pid = rec["page_id"]
if rec.get("mode") == "live":   # Kevin-GO live page (the daily lane can never set mode=live): never re-hide it
    print(f"{pid} LIVE-KEVIN-GO-NOT-TOUCHED {rec.get('handle')}"); sys.exit()
shop, tok, _ = pick({"write_online_store_pages"})
H = {"X-Shopify-Access-Token": tok, "Content-Type": "application/json"}
u = f"https://{shop}/admin/api/{cfg.API}/pages/{pid}.json"
p = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30))["page"]
if p.get("published_at"):
    urllib.request.urlopen(urllib.request.Request(u, method="PUT", headers=H, data=json.dumps({"page": {"id": pid, "published": False}}).encode()), timeout=30)
    print(f"{pid} WAS-VISIBLE-NOW-HIDDEN {p['handle']}")
else:
    print(f"{pid} unpublished {p['handle']}")
PY
)"
PQ=ok; [ "$PAL" != 0 ] && PQ=fail
say "spec $SPEC · validate rc=$V · qa=$QOK · palette=$PQ · real-render=$RQ · page: ${PSTATE:-unknown}"
case "$PSTATE" in
  nopage|"") tag "FAILED $DAY no Shopify draft (validate rc=$V, qa=$QOK; see $RUNLOG)"; R=1;;
  *) PID="${PSTATE%% *}"
     if [ $V = 0 ] && [ "$QOK" = ok ] && [ "$PQ" = ok ] && [ "$RQ" = ok ]; then tag "DRAFT $DAY page $PID"; R=0; else tag "DRAFT-QA-FAIL $DAY page $PID validate=$V qa=$QOK palette=$PQ real=$RQ"; R=2; fi
     echo "$(date '+%FT%T%z') $PID $SPEC" >> "$MINE"
     say "ADMIN: https://admin.shopify.com/store/wellnessnest1/content/pages/$PID (unpublished draft — Kevin approves)";;
esac
FILES=("$QUEUE" "$SPEC")
for f in "${SPEC%.json}.claims.md" "$OUT/body.html" "$OUT/palette.json" "$OUT/page.css" "$OUT/preview.html" "$OUT/shopify.json" "$OUT/qa.json" "$OUT/desktop.jpg" "$OUT/mobile.jpg" "$OUT/real_qa.json" "$OUT/real-desktop.jpg" "$OUT/real-mobile.jpg" "$OUT/real-offer.jpg"; do [ -f "$f" ] && FILES+=("$f"); done
for i in 1 2 3 4 5 6; do [ -e .git/index.lock ] && sleep 10 || break; done
git add -- "${FILES[@]}" >> "$LOG" 2>&1 && git commit -q -m "landing daily $DAY: $SLUG (UNPUBLISHED draft ${PID:-none}, validate=$V qa=$QOK palette=$PQ real=$RQ)" -- "${FILES[@]}" >> "$LOG" 2>&1 \
  && say "committed $(git rev-parse --short HEAD)" || say "WARN: commit failed (see log)"
exit $R

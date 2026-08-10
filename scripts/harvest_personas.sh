#!/bin/bash
# Fill the 200-slot persona bank from Open Images, in two passes.
#
# Pass 1 takes ONE face per cell, all fifty, before any cell gets a second. A bank with fifty
# cells one deep is usable by the picker across all ten rotation pools; a bank with five cells
# full is not usable at all, because nine pools still have nothing to draw. Pass 2 then fills
# to target.
#
# The passes cost the same as running straight to target would, because the verdict cache is
# keyed on the image: everything pass 1 judged, pass 2 replays for free. Cells within a gender
# also share one canonical walk order for the same reason.
#
# Order inside each pass is easy-first — white before the rest, mid-life before the tails —
# so a run that is interrupted has spent its time where the corpus is dense, and the thin
# cells grind last against the warmest cache.
set -u
cd "$(dirname "$0")/.." || exit 1

LOG_DIR="personas/_openimages/harvest-logs"
mkdir -p "$LOG_DIR"

# Ethnicity outer, band inner: the corpus is far more lopsided by ethnicity (74% white in the
# first 38 vision readings) than by age, so ethnicity is the axis that decides whether a cell
# is reachable at all.
CELLS=""
for eth in wh hl bl as mx; do
  for band in 3039 4049 2029 5059 6070; do
    for g in f m; do
      CELLS="$CELLS ${g}${band}-${eth}"
    done
  done
done

run_pass () {
  local pass="$1"; shift
  local n=0
  for cell in $CELLS; do
    n=$((n + 1))
    printf '[%s] pass %s (%d/50) %-12s ' "$(date +%H:%M:%S)" "$pass" "$n" "$cell"
    /usr/bin/python3 -u scripts/fetch_personas.py fetch \
        --cell "$cell" --source openimages \
        --workers "$WORKERS" --download-concurrency "$DLC" \
        --vision-concurrency "$VC" \
        --per-page 500 --pages 20 --max-candidates 12000 --sleep 0.1 \
        "$@" > "$LOG_DIR/${pass}-${cell}.log" 2>&1
    # Report from the log rather than the exit status: fetch exits 0 on "found nothing", and
    # "nothing" is the answer this whole exercise is trying to measure.
    #
    # Assign, then test — do NOT pipe into `|| echo`. A pipeline's status is the LAST command's,
    # so `grep ... | head -1 || echo` reports head's success and the fallback can never run: the
    # line this is meant to catch is precisely the one where grep matched nothing. That is how
    # m3039-hl printed two raw candidate-rejection lines and passed for a summary.
    #
    # `is at depth` joined the pattern with --depth: a cell that is already deep enough prints
    # neither "accepted" nor "is full", so every skipped cell in pass 1 was silently falling
    # through to a fallback that also wasn't firing.
    local summary
    summary="$(tail -3 "$LOG_DIR/${pass}-${cell}.log" \
               | grep -E 'accepted|is full|is at depth' | head -1)"
    printf '%s\n' "${summary:-(no summary line — see $LOG_DIR/${pass}-${cell}.log)}"
  done
}

WORKERS="${WORKERS:-12}"
# Was 8, which is the setting that put us in staticflickr's penalty box on 2026-08-10 — though
# the real culprit there was the `_o` rendition, which flickr meters specifically, and the size
# ladder no longer requests it. Kept low anyway because there is nothing to buy by raising it:
# a `_k` download measures ~1.2s and the run needs about 0.4 of them per second to keep the
# vision gate saturated. Downloading faster than the thing downstream can judge just queues.
DLC="${DLC:-4}"
# The router's ceiling, not ours. --workers describes how many candidates are IN FLIGHT
# (downloading, hashing, waiting); this describes how many may be talking to 9router at once,
# and above roughly six it starts shedding load with 502s whose retry backoff costs more than
# the call. Raising WORKERS without raising this is the intended shape.
VC="${VC:-6}"

echo "=== pass 1: one face per cell, breadth before depth ==="
# --depth 1, not --limit 1: --limit caps what THIS RUN adds, so re-running an interrupted pass 1
# would give a second face to every cell it had already reached before any untouched cell got its
# first. Depth is idempotent, which is what makes the pass restartable at all.
run_pass one --depth 1
echo ""
echo "=== pass 2: fill to target ==="
run_pass full
echo ""
echo "=== done $(date) ==="
/usr/bin/python3 scripts/fetch_personas.py plan

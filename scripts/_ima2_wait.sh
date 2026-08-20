#!/bin/bash
# Transport-level 429 waiter for the daily run. NOT a QC re-roll — this never
# touches the 2-re-roll budget (DAILY-RUN section 3). Probes with the cheapest
# possible request (tiny prompt, no refs, square) every INTERVAL seconds until
# the ima2/OAuth image quota reopens, then exits 0 so the caller generates for real.
# Exits 1 if the window closes without the quota reopening.

OUT=/Users/kevinkreative/genseo/logs/ima2-quota-wait.log
INTERVAL=${INTERVAL:-420}
DEADLINE=${DEADLINE:-18000}   # 5 hours
START=$(date +%s)
i=0

echo "=== ima2 quota waiter started $(date -u +%Y-%m-%dT%H:%M:%SZ) interval=${INTERVAL}s deadline=${DEADLINE}s ===" >> "$OUT"

while true; do
  i=$((i+1))
  NOW=$(date +%s); ELAPSED=$((NOW-START))
  if [ "$ELAPSED" -ge "$DEADLINE" ]; then
    echo "[$(date -u +%H:%M:%SZ)] probe #$i DEADLINE REACHED after ${ELAPSED}s — quota never reopened" >> "$OUT"
    echo "QUOTA_STILL_CLOSED" >> "$OUT"
    exit 1
  fi

  RESP=$(curl -s -m 120 -X POST http://127.0.0.1:3333/api/generate \
    -H 'Content-Type: application/json' \
    -d '{"prompt":"a plain flat light grey square on a white background","size":"1024x1024","quality":"low","n":1}' \
    -w '\nHTTPSTATUS:%{http_code}')
  CODE=$(echo "$RESP" | grep -o 'HTTPSTATUS:[0-9]*' | cut -d: -f2)

  if [ "$CODE" = "200" ]; then
    echo "[$(date -u +%H:%M:%SZ)] probe #$i HTTP 200 after ${ELAPSED}s — QUOTA OPEN" >> "$OUT"
    echo "QUOTA_OPEN" >> "$OUT"
    exit 0
  fi

  echo "[$(date -u +%H:%M:%SZ)] probe #$i HTTP ${CODE} (elapsed ${ELAPSED}s) still limited" >> "$OUT"
  sleep "$INTERVAL"
done

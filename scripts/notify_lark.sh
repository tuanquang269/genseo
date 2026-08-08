#!/bin/bash
# Post a GenSeo run summary to Lark via a group custom-bot webhook.
# Usage: notify_lark.sh <run-log-file> <exit-code>
# Webhook URL lives in ~/.genseo/lark_webhook (single line, NOT in the repo).

LOG="$1"; RC="${2:-?}"
HOOK_FILE="$HOME/.genseo/lark_webhook"
[ -f "$HOOK_FILE" ] || { echo "notify_lark: no webhook configured ($HOOK_FILE missing) — skipping"; exit 0; }
HOOK="$(head -1 "$HOOK_FILE" | tr -d '[:space:]')"
[ -n "$HOOK" ] || exit 0

HOSTLABEL="$(hostname -s)"
STAMP="$(date '+%Y-%m-%d %H:%M')"

ADMIN_URL=""
TITLE_LINE=""
if [ -f "$LOG" ]; then
  ADMIN_URL="$(grep -o 'https://admin\.shopify\.com/store/[^ )"]*' "$LOG" | tail -1)"
  TITLE_LINE="$(grep -iE 'title:|article title' "$LOG" | tail -1 | cut -c1-160)"
  TAIL="$(tail -12 "$LOG" | cut -c1-200 | tr '"' "'" )"
else
  TAIL="(log file missing: $LOG)"
fi

if [ "$RC" = "0" ]; then
  HEAD="✅ GenSeo: bài mới đã lên Shopify (DRAFT) — chờ anh review"
else
  HEAD="❌ GenSeo: run lỗi (exit $RC) — cần xem log"
fi

BODY="$HEAD
$STAMP · $HOSTLABEL
$TITLE_LINE"
[ -n "$ADMIN_URL" ] && BODY="$BODY
Review: $ADMIN_URL"
BODY="$BODY

--- report tail ---
$TAIL"

# JSON-encode via python (always present on macOS)
PAYLOAD="$(python3 - "$BODY" <<'EOF'
import json, sys
print(json.dumps({"msg_type": "text", "content": {"text": sys.argv[1]}}))
EOF
)"

curl -sf -X POST -H 'Content-Type: application/json' -d "$PAYLOAD" "$HOOK" >/dev/null \
  && echo "notify_lark: sent" || echo "notify_lark: POST failed"

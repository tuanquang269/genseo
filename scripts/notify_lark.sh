#!/bin/bash
# Post a GenSeo run summary to Kevin on Lark via the PATI app bot (Eugen Schwartz).
# Usage: notify_lark.sh <run-log-file> <exit-code>
# Config: ~/.genseo/lark_app.json — {"base","app_id","app_secret","receive_id","receive_id_type"}
# (secrets live outside the repo; missing/incomplete config = silent skip)

# Incident: notify_lark.sh --incident <store> <kind> <shortfall> <cause> <next action> <next checkpoint>
# One message per store + kind + ICT day (state/incidents/<day>-<store>-<kind>.sent); a repeat is a no-op.
# Every incident also lands in state/incidents.jsonl, so a missing Lark config is still on record.
CFG="$HOME/.genseo/lark_app.json"
if [ "${1:-}" = "--incident" ]; then
  G="$HOME/genseo"; DAY="$(TZ=Asia/Ho_Chi_Minh date +%F)"
  STORE="$2" KIND="$3"
  mkdir -p "$G/state/incidents"
  SENT="$G/state/incidents/$DAY-$STORE-$KIND.sent"
  [ -e "$SENT" ] && { echo "notify_lark: incident $STORE/$KIND already reported $DAY — skipping"; exit 0; }
  export LK_STORE="$STORE" LK_KIND="$KIND" LK_SHORT="$4" LK_CAUSE="$5" LK_NEXT="$6" LK_CHECK="$7" \
         LK_DAY="$DAY" LK_HOST="$(hostname -s)" LK_JSONL="$G/state/incidents.jsonl" LK_CFG="$CFG" LK_SENT="$SENT"
  /usr/bin/python3 - <<'EOF'
import datetime as dt, json, os, urllib.request
e = os.environ
rec = {"at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "store": e["LK_STORE"], "kind": e["LK_KIND"],
       "shortfall": e["LK_SHORT"], "cause": e["LK_CAUSE"], "owner": "GenSEO coordinator",
       "next_action": e["LK_NEXT"], "next_checkpoint": e["LK_CHECK"], "host": e["LK_HOST"]}
text = "\n".join([f"🚨 GenSEO incident · {rec['store']} · {rec['kind']} · {e['LK_DAY']} · {rec['host']}",
                   f"Shortfall: {rec['shortfall']}", f"Cause: {rec['cause']}", f"Owner: {rec['owner']}",
                   f"Next action: {rec['next_action']}", f"Next checkpoint: {rec['next_checkpoint']}"])
sent = "no-config"
try:
    cfg = json.load(open(e["LK_CFG"]))
    if cfg.get("receive_id"):
        def post(url, payload, token=None):
            h = {"Content-Type": "application/json"}
            if token: h["Authorization"] = f"Bearer {token}"
            return json.load(urllib.request.urlopen(urllib.request.Request(url, json.dumps(payload).encode(), h), timeout=20))
        tok = post(f"{cfg['base']}/open-apis/auth/v3/tenant_access_token/internal",
                   {"app_id": cfg["app_id"], "app_secret": cfg["app_secret"]})["tenant_access_token"]
        r = post(f"{cfg['base']}/open-apis/im/v1/messages?receive_id_type={cfg.get('receive_id_type', 'chat_id')}",
                 {"receive_id": cfg["receive_id"], "msg_type": "text", "content": json.dumps({"text": text})}, tok)
        sent = "sent" if r.get("code") == 0 else f"failed {r.get('code')} {str(r.get('msg', ''))[:80]}"
except FileNotFoundError:
    pass
except Exception as x:  # network / auth: keep the record, retry next run
    sent = f"failed {type(x).__name__}"
rec["lark"] = sent
with open(e["LK_JSONL"], "a") as fh:
    fh.write(json.dumps(rec) + "\n")
if sent in ("sent", "no-config"):
    open(e["LK_SENT"], "w").write(rec["at"] + " " + sent + "\n")
print("notify_lark: incident", rec["store"], rec["kind"], sent)
EOF
  exit 0
fi

LOG="$1"; RC="${2:-?}"
[ -f "$CFG" ] || { echo "notify_lark: no config — skipping"; exit 0; }

HOSTLABEL="$(hostname -s)"
STAMP="$(date '+%Y-%m-%d %H:%M')"

ADMIN_URL=""
TITLE_LINE=""
TAIL="(log file missing: $LOG)"
FRONT_URL=""
if [ -f "$LOG" ]; then
  ADMIN_URL="$(grep -o 'https://admin\.shopify\.com/store/[^ )"]*' "$LOG" | tail -1)"
  FRONT_URL="$(grep -o 'https://wellnessnest\.co/blogs/news/[^ )"]*' "$LOG" | tail -1)"
  TITLE_LINE="$(grep -iE 'title:|article title' "$LOG" | tail -1 | cut -c1-160)"
  TAIL="$(tail -12 "$LOG" | cut -c1-200)"
fi

if [ "$RC" = "0" ] && [ -n "$ADMIN_URL" ]; then
  HEAD="✅ GenSeo: bài mới đã lên Shopify (DRAFT) — chờ anh review"
elif [ "$RC" = "0" ]; then
  HEAD="⚠️ GenSeo: run kết thúc nhưng KHÔNG có draft URL — bài chưa lên, xem report tail"
else
  HEAD="❌ GenSeo: run lỗi (exit $RC) — cần xem log"
fi

export LK_HEAD="$HEAD" LK_STAMP="$STAMP · $HOSTLABEL" LK_TITLE="$TITLE_LINE" \
       LK_URL="$ADMIN_URL" LK_FRONT="$FRONT_URL" LK_TAIL="$TAIL"

python3 - <<'EOF'
import json, os, sys, urllib.request

cfg = json.load(open(os.path.expanduser('~/.genseo/lark_app.json')))
if not cfg.get('receive_id'):
    print('notify_lark: receive_id not set — skipping'); sys.exit(0)

def post(url, payload, token=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=h)
    return json.load(urllib.request.urlopen(req, timeout=20))

tok = post(f"{cfg['base']}/open-apis/auth/v3/tenant_access_token/internal",
           {'app_id': cfg['app_id'], 'app_secret': cfg['app_secret']})['tenant_access_token']

parts = [os.environ['LK_HEAD'], os.environ['LK_STAMP']]
if os.environ.get('LK_TITLE'): parts.append(os.environ['LK_TITLE'])
if os.environ.get('LK_URL'):   parts.append('🔧 Back-end (review/publish): ' + os.environ['LK_URL'])
if os.environ.get('LK_FRONT'): parts.append('🌐 Front-end (live sau khi publish): ' + os.environ['LK_FRONT'])
parts.append('\n--- report tail ---\n' + os.environ.get('LK_TAIL', ''))
text = '\n'.join(parts)

rt = cfg.get('receive_id_type', 'chat_id')
r = post(f"{cfg['base']}/open-apis/im/v1/messages?receive_id_type={rt}",
         {'receive_id': cfg['receive_id'], 'msg_type': 'text',
          'content': json.dumps({'text': text})}, tok)
print('notify_lark:', 'sent' if r.get('code') == 0 else f"failed {r.get('code')} {r.get('msg','')[:80]}")
EOF

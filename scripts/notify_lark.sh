#!/bin/bash
# Post a GenSeo run summary to Kevin on Lark via the PATI app bot (Eugen Schwartz).
# Usage: notify_lark.sh <run-log-file> <exit-code>
# Config: ~/.genseo/lark_app.json — {"base","app_id","app_secret","receive_id","receive_id_type"}
# (secrets live outside the repo; missing/incomplete config = silent skip)

LOG="$1"; RC="${2:-?}"
CFG="$HOME/.genseo/lark_app.json"
[ -f "$CFG" ] || { echo "notify_lark: no config — skipping"; exit 0; }

HOSTLABEL="$(hostname -s)"
STAMP="$(date '+%Y-%m-%d %H:%M')"

ADMIN_URL=""
TITLE_LINE=""
TAIL="(log file missing: $LOG)"
if [ -f "$LOG" ]; then
  ADMIN_URL="$(grep -o 'https://admin\.shopify\.com/store/[^ )"]*' "$LOG" | tail -1)"
  TITLE_LINE="$(grep -iE 'title:|article title' "$LOG" | tail -1 | cut -c1-160)"
  TAIL="$(tail -12 "$LOG" | cut -c1-200)"
fi

if [ "$RC" = "0" ]; then
  HEAD="✅ GenSeo: bài mới đã lên Shopify (DRAFT) — chờ anh review"
else
  HEAD="❌ GenSeo: run lỗi (exit $RC) — cần xem log"
fi

export LK_HEAD="$HEAD" LK_STAMP="$STAMP · $HOSTLABEL" LK_TITLE="$TITLE_LINE" \
       LK_URL="$ADMIN_URL" LK_TAIL="$TAIL"

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
if os.environ.get('LK_URL'):   parts.append('Review: ' + os.environ['LK_URL'])
parts.append('\n--- report tail ---\n' + os.environ.get('LK_TAIL', ''))
text = '\n'.join(parts)

rt = cfg.get('receive_id_type', 'chat_id')
r = post(f"{cfg['base']}/open-apis/im/v1/messages?receive_id_type={rt}",
         {'receive_id': cfg['receive_id'], 'msg_type': 'text',
          'content': json.dumps({'text': text})}, tok)
print('notify_lark:', 'sent' if r.get('code') == 0 else f"failed {r.get('code')} {r.get('msg','')[:80]}")
EOF

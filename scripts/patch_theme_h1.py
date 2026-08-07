#!/usr/bin/env python3
"""
patch_theme_h1.py — Remove the visually-hidden "Collection: " prefix from the
collection H1 in the main theme's banner section, leaving a clean keyword H1.

Surgical: removes ONLY the <span class="visually-hidden">...title...: </span> line.
Backup of the original is written by backup_before_changes.py first.

Usage:
  python3 patch_theme_h1.py          # dry-run (shows diff)
  python3 patch_theme_h1.py --apply  # push to live theme
  python3 patch_theme_h1.py --revert # restore from backup
"""
import json, urllib.request, urllib.parse, sys, os, datetime

from genseo_config import SHOP, TOKEN, API
THEME="100000000010"; KEY="sections/main-collection-banner.liquid"
ROOT="~/genseo"
BK=f"{ROOT}/backups/{datetime.date.today().strftime('%Y%m%d')}/theme__sections__main-collection-banner.liquid"

def get_asset():
    url=f"https://{SHOP}/admin/api/{API}/themes/{THEME}/assets.json?asset[key]={urllib.parse.quote(KEY)}"
    req=urllib.request.Request(url, headers={"X-Shopify-Access-Token":TOKEN})
    return json.loads(urllib.request.urlopen(req).read())['asset']['value']

def put_asset(value):
    payload={"asset":{"key":KEY,"value":value}}
    req=urllib.request.Request(f"https://{SHOP}/admin/api/{API}/themes/{THEME}/assets.json",
        data=json.dumps(payload).encode(), method="PUT",
        headers={"X-Shopify-Access-Token":TOKEN,"Content-Type":"application/json"})
    urllib.request.urlopen(req);

def main():
    apply="--apply" in sys.argv; revert="--revert" in sys.argv
    if revert:
        if not os.path.exists(BK): print(f"No backup at {BK}"); return
        put_asset(open(BK).read()); print("✅ Reverted theme banner from backup."); return

    cur=get_asset()
    # target line (the visually-hidden prefix span)
    import re
    pat=re.compile(r'\n\s*<span class="visually-hidden">\{\{ \'sections\.collection_template\.title\' \| t \}\}: </span>')
    m=pat.search(cur)
    if not m:
        print("⚠️  Target span not found — theme may have changed. No edit made.")
        # show the h1 block for manual inspection
        h1=re.search(r'<h1[^>]*>.*?</h1>', cur, re.S)
        print(h1.group(0) if h1 else "(no h1 found)")
        return
    new=pat.sub('', cur)
    print("--- BEFORE ---")
    print(re.search(r'<h1[^>]*>.*?</h1>', cur, re.S).group(0))
    print("\n--- AFTER ---")
    print(re.search(r'<h1[^>]*>.*?</h1>', new, re.S).group(0))
    if apply:
        put_asset(new); print("\n✅ APPLIED to live theme.")
    else:
        print("\n(dry-run) Re-run with --apply to push. --revert to undo later.")

if __name__=="__main__":
    main()

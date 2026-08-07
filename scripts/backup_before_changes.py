#!/usr/bin/env python3
"""Backup current live state of everything we're about to edit, to backups/<date>/.
Lets us revert any change. Read-only against Shopify."""
import json, urllib.request, urllib.parse, os, datetime

from genseo_config import SHOP, TOKEN, API
MAIN_THEME="183190880571"
ROOT="/Users/kevinkreative/genseo"
STAMP=datetime.date.today().strftime("%Y%m%d")
BK=f"{ROOT}/backups/{STAMP}"
os.makedirs(BK, exist_ok=True)

COLLECTION_IDS={
  "protein-powder":186319929484,"optimum-nutrition-us":236628312246,
  "creatine":344726306998,"mass-gainer":268057280694,"pre-workout":345002574006,
  "dymatize-nutrition":236626935990,"ghost":344548573366,"myprotein-us":236627493046}

def api(url):
    req=urllib.request.Request(url, headers={"X-Shopify-Access-Token":TOKEN})
    return json.loads(urllib.request.urlopen(req).read())

# 1) collections (title, body_html, metafields)
coll_backup={}
for h,cid in COLLECTION_IDS.items():
    c=api(f"https://{SHOP}/admin/api/{API}/collections/{cid}.json")['collection']
    mf=api(f"https://{SHOP}/admin/api/{API}/collections/{cid}/metafields.json")['metafields']
    coll_backup[h]={"id":cid,"title":c.get('title'),"body_html":c.get('body_html'),
        "metafields":[{"namespace":m['namespace'],"key":m['key'],"value":m['value']} for m in mf if m['namespace']=='global']}
with open(f"{BK}/collections_backup.json","w") as f: json.dump(coll_backup,f,indent=2)
print(f"Backed up {len(coll_backup)} collections -> {BK}/collections_backup.json")

# 2) theme locale file (the H1 'Collection:' label source) — en.default.json
for key in ["locales/en.default.json","sections/main-collection-banner.liquid"]:
    url=f"https://{SHOP}/admin/api/{API}/themes/{MAIN_THEME}/assets.json?asset[key]={urllib.parse.quote(key)}"
    try:
        v=api(url)['asset']['value']
        safe=key.replace('/','__')
        with open(f"{BK}/theme__{safe}","w") as f: f.write(v)
        print(f"Backed up theme asset {key} ({len(v)} chars)")
    except Exception as e:
        print(f"Could not back up {key}: {e}")

print(f"\nAll backups in: {BK}")

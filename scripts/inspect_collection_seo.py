"""Read-only: inspect current SEO state of top collections before patching.
Shows current title_tag / description_tag metafields and body_html size."""
import json, urllib.request

shop= __import__("genseo_config").SHOP
token= __import__("genseo_config").TOKEN
API="2026-04"
HANDLES=["protein-powder","optimum-nutrition-{{market}}","creatine","mass-gainer",
         "pre-workout","dymatize-nutrition","ghost","myprotein-{{market}}"]

def get(url):
    req=urllib.request.Request(url, headers={"X-Shopify-Access-Token":token})
    return json.loads(urllib.request.urlopen(req).read())

def find_collection(handle):
    for ctype in ("smart_collections","custom_collections"):
        d=get(f"https://{shop}/admin/api/{API}/{ctype}.json?handle={handle}")
        arr=d.get(ctype,[])
        if arr: return ctype, arr[0]
    return None, None

for h in HANDLES:
    ctype, col = find_collection(h)
    if not col:
        print(f"[{h}] NOT FOUND"); continue
    cid=col['id']
    title=col.get('title','')
    body=col.get('body_html') or ''
    mf=get(f"https://{shop}/admin/api/{API}/collections/{cid}/metafields.json").get('metafields',[])
    seo={m['key']:m['value'] for m in mf if m['namespace']=='global' and m['key'] in ('title_tag','description_tag')}
    print(f"\n=== {h}  (id={cid}, {ctype}) ===")
    print(f"  collection.title (= theme H1 source): {title!r}")
    print(f"  SEO title_tag    : {seo.get('title_tag','(none)')}")
    print(f"  SEO description  : {seo.get('description_tag','(none)')[:120]}")
    print(f"  body_html length : {len(body)} chars")

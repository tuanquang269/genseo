#!/usr/bin/env python3
"""
redirect_thin_batch.py — Redirect thin filler articles from SG_THIN_REDIRECT.csv.
Conservative default: --blog training (generic filler, 0 commercial value).
Unpublish + 301 each. Dry-run by default; --apply to execute; --revert to undo.
Logged to backups/<date>/thin_redirect_log.json.
"""
import json, urllib.request, csv, sys, os, datetime

from genseo_config import SHOP, TOKEN, API
BLOG_IDS={"news4008483131}
ROOT="/Users/kevinkreative/genseo"
LOG=f"{ROOT}/backups/{datetime.date.today().strftime('%Y%m%d')}/thin_redirect_log.json"

import time
def api(url, data=None, method="GET", _retries=4):
    for attempt in range(_retries):
        try:
            req=urllib.request.Request(url, data=(json.dumps(data).encode() if data else None), method=method,
                headers={"X-Shopify-Access-Token":TOKEN,"Content-Type":"application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=30).read()) if method!="DELETE" else {}
        except Exception as ex:
            if attempt==_retries-1: raise
            time.sleep(2*(attempt+1))

def existing_redirect_id(path):
    d=api(f"https://{SHOP}/admin/api/{API}/redirects.json?path={path}")
    rs=d.get('redirects',[])
    return rs[0]['id'] if rs else None

def resolve_id(blog_id, path):
    handle=path.rstrip('/').split('/')[-1]
    d=api(f"https://{SHOP}/admin/api/{API}/blogs/{blog_id}/articles.json?handle={handle}&fields=id,handle")
    a=d.get('articles',[])
    return a[0]['id'] if a else None

def main():
    apply="--apply" in sys.argv; revert="--revert" in sys.argv
    blog_filter=None
    if "--blog" in sys.argv: blog_filter=sys.argv[sys.argv.index("--blog")+1]

    if revert:
        log=json.load(open(LOG)) if os.path.exists(LOG) else []
        for e in log:
            if e.get("article_id"):
                try: api(f"https://{SHOP}/admin/api/{API}/blogs/{e['blog_id']}/articles/{e['article_id']}.json",{"article":{"id":e['article_id'],"published":True}},"PUT"); print(f"  republished {e['source']}")
                except Exception as ex: print(f"  republish fail {e['source']}: {ex}")
            if e.get("redirect_id"):
                try: api(f"https://{SHOP}/admin/api/{API}/redirects/{e['redirect_id']}.json",None,"DELETE"); print(f"  deleted redirect {e['source']}")
                except Exception as ex: print(f"  redirect del note: {ex}")
        print("✅ revert done"); return

    rows=list(csv.DictReader(open(f"{ROOT}/SG_THIN_REDIRECT.csv")))
    if blog_filter: rows=[r for r in rows if r['blog']==blog_filter]
    print(f"=== redirect_thin_batch.py — {'APPLY' if apply else 'DRY-RUN'} — {len(rows)} articles (blog={blog_filter or 'all'}) ===\n")
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    log=json.load(open(LOG)) if os.path.exists(LOG) else []
    done_sources={e['source'] for e in log}
    for r in rows:
        src=r['url']; tgt=r['redirect_target']; blog=BLOG_IDS[r['blog']]
        # idempotent: skip if a redirect already exists for this path
        rid=existing_redirect_id(src)
        if rid:
            if src not in done_sources:
                aid=resolve_id(blog, src)
                log.append({"source":src,"target":tgt,"blog_id":blog,"article_id":aid,"redirect_id":rid})
                json.dump(log, open(LOG,"w"), indent=2)
            print(f"  SKIP (already redirected): {src.split('/blogs/')[-1][:50]}")
            continue
        aid=resolve_id(blog, src)
        line=f"  {src.split('/blogs/')[-1][:52]:52} -> {tgt}  (id={aid})"
        if not apply:
            print(line); continue
        e={"source":src,"target":tgt,"blog_id":blog,"article_id":aid,"redirect_id":None}
        if aid:
            api(f"https://{SHOP}/admin/api/{API}/blogs/{blog}/articles/{aid}.json",{"article":{"id":aid,"published":False}},"PUT")
        rr=api(f"https://{SHOP}/admin/api/{API}/redirects.json",{"redirect":{"path":src,"target":tgt}},"POST")
        e["redirect_id"]=rr['redirect']['id']
        log.append(e); json.dump(log, open(LOG,"w"), indent=2)   # write after EACH success
        print(line+"  ✓")
    if apply:
        print(f"\nLog now has {len(log)} actions -> {LOG}")
    else:
        print("\nRe-run with --apply (and --blog training) to execute.")

if __name__=="__main__":
    main()

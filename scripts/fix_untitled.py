#!/usr/bin/env python3
"""
fix_untitled.py — Recover any LIVE 'Generated Article' (untitled) post.

A post gets the default title 'Generated Article' when it was published without a real
H1/title (usually via a wrong publish path that bypassed the fail-loud guard). This tool:
  1. Scans both blogs for PUBLISHED articles titled 'Generated Article' (skips unpublished/redirected).
  2. Recovers the real title from (in order): <!-- Title: ... -->, leaked `title: "..."`, or the slug.
  3. DUPLICATE CHECK: searches live articles for the recovered topic. If a strong match exists,
     it FLAGS the post as a likely duplicate (recommend redirect/merge) instead of titling it.
  4. Sets the title + named author, strips leaked metadata, and rebuilds schema (via repair_schema).

Dry-run by default (proposes). Add --apply to run FULLY AUTONOMOUSLY:
  - unique untitled post  -> set real title + named author + rebuild schema
  - clear duplicate (strict, high title-overlap with a live non-self article)
                          -> unpublish + 301 redirect to that article (the correct action)
  - uncertain            -> default to TITLING (safe: never loses content)
All actions are logged to backups/<date>/untitled_autofix_log.json (reversible).
Usage: python3 fix_untitled.py [--apply]
"""
import sys, json, re, urllib.request, urllib.parse, subprocess, os, datetime

from genseo_config import SHOP, TOKEN, API
BLOGS={104008483131:"news"}
ROSTER={"author-two":"Author Two","author-one":"Author One","author-three":"Author Three",
 "author-four":"Author Four","author-five":"Author Five","author-six":"Author Six","author-seven":"Author Seven"}

def api(url,data=None,method="GET"):
    req=urllib.request.Request(url,data=(json.dumps(data).encode() if data else None),method=method,
        headers={"X-Shopify-Access-Token":TOKEN,"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read()) if method!="DELETE" else {}

def recover_title(body, handle):
    m=re.search(r'<!--\s*title:\s*(.+?)\s*-->', body, re.I) or re.search(r'^\s*title:\s*["\']?(.+?)["\']?\s*$', body, re.M|re.I)
    if m: return m.group(1).strip().strip('"\'').replace(' -->','').strip(), "metadata"
    # slug fallback: turn handle into a title
    return handle.replace('-',' ').title(), "slug"

STOP=set("the a an to in of for is are and or vs best guide ultimate complete review {{market}} sg 2024 2025 2026 2027 your you what how do does top".split())
def toks(s): return set(w for w in re.sub(r'[^a-z0-9 ]',' ',s.lower()).split() if w not in STOP and len(w)>2)

def best_duplicate(title, self_handle):
    """Return (url, overlap) of the strongest LIVE non-self article matching `title`, else (None,0)."""
    q=urllib.parse.quote(" ".join(title.split()[:6]))
    try:
        d=json.loads(urllib.request.urlopen(f"https://wellnessnest.co/search/suggest.json?q={q}&resources[type]=article&resources[limit]=5").read())
        arts=d.get('resources',{}).get('results',{}).get('articles',[])
    except Exception: return (None,0.0)
    tt=toks(title); best=(None,0.0)
    for a in arts:
        u=a.get('url','');
        if self_handle in u: continue          # skip self
        at=toks(a.get('title',''))
        if not tt or not at: continue
        overlap=len(tt&at)/len(tt|at)          # Jaccard on significant tokens
        if overlap>best[1]: best=(u.split('?')[0], round(overlap,2))
    return best

DUP_THRESHOLD=0.75  # Jaccard token overlap above which we treat it as the SAME topic → redirect

def main():
    apply="--apply" in sys.argv
    print(f"=== fix_untitled.py — {'APPLY (autonomous)' if apply else 'DRY-RUN'} ===\n")
    found=0; titled=0; redirected=0; log=[]
    for bid,bname in BLOGS.items():
        url=f"https://{SHOP}/admin/api/{API}/blogs/{bid}/articles.json?limit=250&fields=id,title,handle,body_html,published_at"
        while url:
            req=urllib.request.Request(url,headers={"X-Shopify-Access-Token":TOKEN}); res=urllib.request.urlopen(req); d=json.loads(res.read())
            for a in d['articles']:
                if a['title'].strip()!='Generated Article': continue
                if not a.get('published_at'): continue   # skip unpublished/redirected (already handled)
                found+=1
                body=a.get('body_html') or ''
                title,src=recover_title(body, a['handle'])
                dup_url,overlap=best_duplicate(title, a['handle'])
                is_dup = dup_url and overlap>=DUP_THRESHOLD
                print(f"[{bid}/{a['id']}] {a['handle']}")
                print(f"   recovered title ({src}): {title!r}")
                if dup_url: print(f"   closest live article: {dup_url}  (overlap {overlap})")

                if is_dup:
                    # AUTONOMOUS: clear duplicate → unpublish + 301 to the established article
                    action=f"REDIRECT → {dup_url} (overlap {overlap})"
                    if apply:
                        path=f"/blogs/{bname}/{a['handle']}"
                        api(f"https://{SHOP}/admin/api/{API}/blogs/{bid}/articles/{a['id']}.json",{"article":{"id":a['id'],"published":False}},"PUT")
                        api(f"https://{SHOP}/admin/api/{API}/redirects.json",{"redirect":{"path":path,"target":dup_url.replace('https://wellnessnest.co','')}},"POST")
                        redirected+=1
                        log.append({"action":"redirect","id":a['id'],"path":path,"target":dup_url,"overlap":overlap})
                        print(f"   ✓ {action}")
                    else:
                        print(f"   (dry-run) would {action}")
                else:
                    # AUTONOMOUS default (safe): TITLE it + named author + rebuild schema
                    am=re.search(r'<!--\s*author url:\s*/pages/([a-z-]+)\s*-->', body, re.I) or re.search(r'/pages/([a-z-]+)', body)
                    author=ROSTER.get(am.group(1) if am else None)
                    if not author:
                        author=(a.get('author') or '').strip()
                        author=author if author in ROSTER.values() else "Author Four"
                    if apply:
                        clean_body=re.sub(r'<!--\s*(title|author|author url|meta description|seo_title|seo_description|tags|status):.*?-->\s*','',body,flags=re.I)
                        api(f"https://{SHOP}/admin/api/{API}/blogs/{bid}/articles/{a['id']}.json",
                            {"article":{"id":a['id'],"title":title,"body_html":clean_body,"author":author}},"PUT")
                        subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__),"repair_schema.py"), str(a['id']), str(bid)])
                        titled+=1
                        log.append({"action":"title","id":a['id'],"title":title,"author":author})
                        print(f"   ✓ TITLED {title!r} + author={author} + schema rebuilt")
                    else:
                        print(f"   (dry-run) would TITLE {title!r} + author={author}")
                print()
            url=None
            for p in res.headers.get('Link','').split(','):
                if 'rel="next"' in p: url=p[p.find('<')+1:p.find('>')]
    # log + summary
    if apply and log:
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
        os.makedirs(f"/Users/kevinkreative/genseo/backups/{stamp}",exist_ok=True)
        p=f"/Users/kevinkreative/genseo/backups/{stamp}/untitled_autofix_log.json"
        prev=json.load(open(p)) if os.path.exists(p) else []
        json.dump(prev+log, open(p,"w"), indent=2)
        print(f"Logged {len(log)} actions -> {p}")
    print(f"Untitled posts found: {found} | titled: {titled} | redirected(dup): {redirected}" + ("" if found else " — nothing to fix ✓"))

if __name__=="__main__": main()

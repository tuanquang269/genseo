#!/usr/bin/env python3
"""
find_dupes.py — Detect & heal titled-duplicate articles (cannibalization).

Clusters all LIVE published articles by NORMALIZED title (stopwords + year stripped). A cluster
of 2+ = the same article published under variant slugs (-1 / -v2 / -2027 / identical title).
Winner = the member with the most SG traffic (clicks, then impressions, then oldest). The rest
are unpublished + 301-redirected to the winner.

SAFETY: only EXACT-normalized-title clusters are auto-merged in --apply (extremely conservative —
genuinely different topics have different token sets, so no false positives). Near-duplicates
(high overlap but not identical) are only REPORTED for human review, never auto-merged.

Usage:
  python3 find_dupes.py            # dry-run: report clusters
  python3 find_dupes.py --apply    # auto-merge EXACT-title clusters (logged, reversible)
"""
import sys, json, re, datetime, os, urllib.request
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from genseo_config import SHOP, TOKEN, API
BLOGS={104008483131:"news"}
STOP=set("the a an to in of for is are and or vs best guide ultimate complete review {{market}} sg "
         "your you what how do does top picks 2024 2025 2026 2027 2028".split())

def api(url,data=None,method="GET"):
    req=urllib.request.Request(url,data=(json.dumps(data).encode() if data else None),method=method,
        headers={"X-Shopify-Access-Token":TOKEN,"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read()) if method!="DELETE" else {}

def norm_key(title):
    t=re.sub(r'[^a-z0-9 ]',' ',title.lower())
    return tuple(sorted(w for w in t.split() if w not in STOP and len(w)>2))

def jaccard(a,b):
    sa,sb=set(a),set(b)
    return len(sa&sb)/len(sa|sb) if (sa|sb) else 0

def sg_pagemap():
    try:
        from gsc_fetcher import get_service
        svc=get_service(); SITE='https://wellnessnest.co/'
        SG=[{'filters':[{'dimension':'country','operator':'equals','expression':'{{COUNTRY_CODE}}'}]}]
        end=datetime.date.today()-datetime.timedelta(days=2); start=end-datetime.timedelta(days=89)
        fmt=lambda d:d.strftime('%Y-%m-%d')
        rows=svc.searchanalytics().query(siteUrl=SITE,body={'startDate':fmt(start),'endDate':fmt(end),
            'dimensions':['page'],'rowLimit':25000,'dimensionFilterGroups':SG}).execute().get('rows',[])
        return {r['keys'][0]:(r['clicks'],r['impressions']) for r in rows}
    except Exception as e:
        print(f"  (GSC unavailable: {e} — winner falls back to oldest article)"); return {}

def main():
    apply="--apply" in sys.argv
    print(f"=== find_dupes.py — {'APPLY (auto-merge exact dupes)' if apply else 'DRY-RUN'} ===\n")
    arts=[]
    for bid,bname in BLOGS.items():
        url=f"https://{SHOP}/admin/api/{API}/blogs/{bid}/articles.json?limit=250&fields=id,title,handle,created_at,published_at"
        while url:
            req=urllib.request.Request(url,headers={"X-Shopify-Access-Token":TOKEN}); res=urllib.request.urlopen(req); d=json.loads(res.read())
            for a in d['articles']:
                if a.get('published_at') and a['title'].strip() and a['title'].strip()!='Generated Article':
                    arts.append({**a,"blog":bname,"bid":bid,"key":norm_key(a['title']),
                                 "url":f"https://wellnessnest.co/blogs/{bname}/{a['handle']}"})
            url=None
            for p in res.headers.get('Link','').split(','):
                if 'rel="next"' in p: url=p[p.find('<')+1:p.find('>')]
    print(f"Live published articles scanned: {len(arts)}")
    pm=sg_pagemap()
    def traffic(a): c,i=pm.get(a['url'],(0,0)); return (c,i)

    # group by exact normalized-title key
    clusters={}
    for a in arts:
        if a['key']: clusters.setdefault(a['key'],[]).append(a)
    exact=[m for m in clusters.values() if len(m)>1]

    log=[]; merged=0
    print(f"\n=== EXACT-title duplicate clusters: {len(exact)} ===")
    for members in sorted(exact, key=lambda m:-len(m)):
        members.sort(key=lambda a:(-traffic(a)[0],-traffic(a)[1], a['created_at']))  # winner first
        winner=members[0]
        print(f"\n  '{winner['title'][:55]}' ×{len(members)}")
        for a in members:
            c,i=traffic(a); tag="KEEP (winner)" if a is winner else "→ redirect"
            print(f"     {tag}: clk={c} imp={i} | {a['handle'][:55]}")
        wpath=f"/blogs/{winner['blog']}/{winner['handle']}"
        for a in members[1:]:
            c,i=traffic(a)
            # SAFETY GUARD: only auto-merge a loser that is effectively DEAD. A loser with real
            # traffic may be a distinct article with a colliding templated title (e.g. my own
            # refresh titles) — merging it would destroy a live page. Report those instead.
            dead = (c==0 and i<10)
            if not dead:
                print(f"     ⚠ '{a['handle'][:45]}' has traffic (clk={c} imp={i}) — NOT auto-merged; review manually")
                continue
            if apply:
                lpath=f"/blogs/{a['blog']}/{a['handle']}"
                api(f"https://{SHOP}/admin/api/{API}/blogs/{a['bid']}/articles/{a['id']}.json",{"article":{"id":a['id'],"published":False}},"PUT")
                r=api(f"https://{SHOP}/admin/api/{API}/redirects.json",{"redirect":{"path":lpath,"target":wpath}},"POST")
                log.append({"loser_id":a['id'],"loser":lpath,"winner":wpath,"redirect_id":r['redirect']['id']})
                merged+=1
                print(f"     ✓ merged dead dupe '{a['handle'][:45]}' → winner")
            else:
                print(f"     (would auto-merge dead dupe '{a['handle'][:45]}' → winner)")

    # near-duplicates (report only) — high overlap but not identical key
    print(f"\n=== NEAR-duplicates (review manually — NOT auto-merged) ===")
    near=0; keys=[a for a in arts]
    seen=set()
    for i in range(len(arts)):
        for j in range(i+1,len(arts)):
            a,b=arts[i],arts[j]
            if a['key']==b['key']: continue  # already an exact cluster
            ov=jaccard(a['key'],b['key'])
            if ov>=0.7:
                pair=tuple(sorted([a['id'],b['id']]))
                if pair in seen: continue
                seen.add(pair); near+=1
                print(f"  overlap {ov:.2f}: '{a['title'][:40]}' <> '{b['title'][:40]}'")
    if not near: print("  none")

    if apply and log:
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
        os.makedirs(f"/Users/kevinkreative/genseo/backups/{stamp}",exist_ok=True)
        p=f"/Users/kevinkreative/genseo/backups/{stamp}/dupe_merge_log.json"
        prev=json.load(open(p)) if os.path.exists(p) else []
        json.dump(prev+log, open(p,"w"), indent=2)
        print(f"\nLogged {len(log)} merges -> {p} (reversible)")
    print(f"\nSummary: exact-dup clusters={len(exact)} merged={merged} near-dup-pairs(review)={near}")

if __name__=="__main__": main()

#!/usr/bin/env python3
"""
build_consolidation_map_full.py — Full-corpus consolidation map over ALL 632 articles
(reads ALL_ARTICLES.csv produced by fetch_all_articles.py).

Detects:
  - duplicate/near-duplicate clusters by normalized title (cannibalization)
  - thin zero-traffic redirect candidates
Verdicts (conservative — never kills a page with SG clicks):
  KEEP/EXPAND  : sg_clicks>=1 OR sg_imp>=50
  MERGE→winner : in a title-duplicate cluster, not the winner
  REDIRECT     : words<700 AND sg_imp<20 AND sg_clicks==0 AND not a cluster winner
  REVIEW       : everything else
Outputs SG_CONSOLIDATION_FULL.csv. Read-only.
"""
import csv, re, os
ROOT="~/genseo"
STOP=set("the a an to in of for is are and or vs best guide ultimate complete review {{market}} sg 2025 2026 2027 your you what how do does in-{{market}} everything-you-need know about all things need".split())

def norm(title):
    t=re.sub(r'[^a-z0-9 ]',' ',title.lower())
    toks=[w for w in t.split() if w not in STOP and len(w)>2]
    # drop trailing numeric suffix tokens
    return " ".join(sorted(set(toks)))

def main():
    rows=list(csv.DictReader(open(f"{ROOT}/ALL_ARTICLES.csv")))
    for r in rows:
        r['words']=int(r['words']); r['sg_imp']=int(r['sg_imp']); r['sg_clicks']=int(r['sg_clicks']); r['sg_pos']=float(r['sg_pos'])

    # cluster only NUTRITION (commercial) by normalized title key
    clusters={}
    for r in rows:
        clusters.setdefault(norm(r['title']),[]).append(r)

    out=[]
    dup_clusters=[]
    for nk,members in clusters.items():
        members.sort(key=lambda r:(-r['sg_clicks'],-r['sg_imp']))
        winner=members[0]['url']
        is_dup=len(members)>1 and nk!=""
        if is_dup: dup_clusters.append((nk,members))
        for r in members:
            has_traffic=r['sg_clicks']>=1 or r['sg_imp']>=50
            thin=r['words']<700
            if has_traffic:
                v="KEEP/EXPAND"
            elif is_dup and r['url']!=winner:
                v="MERGE→winner"
            elif thin and r['sg_imp']<20 and r['sg_clicks']==0:
                v="REDIRECT"
            else:
                v="REVIEW"
            out.append({'verdict':v,'title':r['title'],'sg_clicks':r['sg_clicks'],'sg_imp':r['sg_imp'],
                'sg_pos':r['sg_pos'],'words':r['words'],'blog':r['blog'],'created':r['created'],
                'cluster_size':len(members),
                'winner':'yes' if (is_dup and r['url']==winner) else '',
                'merge_into':winner.replace('https://yourdomain.com','') if (is_dup and r['url']!=winner) else '',
                'url':r['url'].replace('https://yourdomain.com',''),'id':r['id']})

    order={'REDIRECT':0,'MERGE→winner':1,'REVIEW':2,'KEEP/EXPAND':3}
    out.sort(key=lambda r:(order[r['verdict']], r['sg_imp']))
    outp=f"{ROOT}/SG_CONSOLIDATION_FULL.csv"
    with open(outp,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['verdict','title','sg_clicks','sg_imp','sg_pos','words','blog','created','cluster_size','winner','merge_into','url','id'])
        w.writeheader(); w.writerows(out)

    from collections import Counter
    cnt=Counter(r['verdict'] for r in out)
    print(f"Wrote {len(out)} rows -> {outp}\n=== VERDICTS (632 articles) ===")
    for v in ['REDIRECT','MERGE→winner','REVIEW','KEEP/EXPAND']:
        risk=sum(r['sg_clicks'] for r in out if r['verdict']==v)
        print(f"  {v:14}: {cnt.get(v,0):>3}  (SG clicks in bucket: {risk})")
    real_dups=[(nk,m) for nk,m in dup_clusters if len(m)>1]
    print(f"\n=== DUPLICATE/CANNIBALIZATION CLUSTERS: {len(real_dups)} ===")
    for nk,m in sorted(real_dups,key=lambda x:-sum(r['sg_clicks'] for r in x[1]))[:25]:
        tot=sum(r['sg_clicks'] for r in m)
        print(f"  [{tot} SG clk total] x{len(m)}: {m[0]['title'][:55]}")
        for r in m:
            print(f"      clk={r['sg_clicks']:>2} imp={r['sg_imp']:>4} w={r['words']:>4} | {r['url'].replace('/blogs/nutrition/','')[:62]}")

if __name__=="__main__":
    main()

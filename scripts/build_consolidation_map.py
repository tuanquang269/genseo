#!/usr/bin/env python3
"""
build_consolidation_map.py — Decide what to do with each published article.

Joins 3 signals per article:
  1. Word count (from published_drafts/*.md)
  2. Keyword-duplicate clusters (same/near keyword across multiple URLs = cannibalization)
  3. Real SG performance (GSC, country=sgp, last 28d): impressions, clicks, position

Verdict logic (conservative — never kill a ranking page):
  KEEP/EXPAND : has SG traffic (imp>=50 or clicks>=1) — improve, don't remove
  MERGE       : part of a keyword-duplicate cluster — consolidate into the best performer
  REDIRECT    : thin (<700w) AND ~no SG traffic (imp<20, clicks=0) AND not the cluster winner
  REVIEW      : everything else (low signal, manual look)

Outputs SG_CONSOLIDATION_MAP.csv. Read-only — proposes, never edits.
"""
import os, csv, re, datetime, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from gsc_fetcher import get_service

ROOT="/Users/kevinkreative/genseo"
DRAFTS=f"{ROOT}/published_drafts"
TRACKER=f"{ROOT}/PUBLISHED_ARTICLES_TRACKER.csv"
SITE='https://wellnessnest.co/'
SG=[{'filters':[{'dimension':'country','operator':'equals','expression':'usa'}]}]
fmt=lambda d:d.strftime('%Y-%m-%d')

STOP=set("the a an to in of for is are and or vs best guide ultimate review us 2026 2027 your you what how complete".split())
def norm_kw(k):
    toks=[t for t in re.sub(r'[^a-z0-9 ]','',k.lower()).split() if t not in STOP]
    return " ".join(sorted(toks))

def wordcount_for(url):
    """Best-effort: match a draft file to the article by slug tokens."""
    slug=url.rstrip('/').split('/')[-1]
    return slug

def main():
    # --- load tracker (keyword + url + posted) ---
    arts=[]
    with open(TRACKER) as f:
        for row in csv.DictReader(f):
            url=row['Article Link'].strip()
            if not url: continue
            arts.append({'kw':row['Keyword'].strip(),'url':url,'posted':row.get('Posted Date','')})

    # --- map draft files -> wordcount, and try to attach to articles by slug tokens ---
    draft_wc={}
    for fn in os.listdir(DRAFTS):
        if not fn.endswith('.md'): continue
        p=os.path.join(DRAFTS,fn)
        try: wc=len(open(p,encoding='utf-8',errors='ignore').read().split())
        except: wc=0
        draft_wc[fn]=wc
    # heuristic slug match: tokens of keyword appear in draft filename
    def wc_for_article(a):
        kwtok=set(re.sub(r'[^a-z0-9 ]','',a['kw'].lower()).split())
        best=None;bestscore=0
        for fn,wc in draft_wc.items():
            ftok=set(re.sub(r'[^a-z0-9_]',' ',fn.lower()).replace('_',' ').split())
            score=len(kwtok & ftok)
            if score>bestscore: bestscore=score;best=(fn,wc)
        return best if bestscore>=2 else None

    # --- GSC SG performance per page (28d) ---
    svc=get_service()
    end=datetime.date.today()-datetime.timedelta(days=3); start=end-datetime.timedelta(days=27)
    rows=svc.searchanalytics().query(siteUrl=SITE,body={'startDate':fmt(start),'endDate':fmt(end),
        'dimensions':['page'],'rowLimit':25000,'dimensionFilterGroups':SG}).execute().get('rows',[])
    perf={r['keys'][0]:(r['clicks'],r['impressions'],r['position']) for r in rows}

    # --- cluster by normalized keyword ---
    clusters={}
    for a in arts:
        clusters.setdefault(norm_kw(a['kw']),[]).append(a)

    out=[]
    for nk,members in clusters.items():
        # rank members by SG impressions to find the cluster winner
        def imp(a): return perf.get(a['url'],(0,0,0))[1]
        members_sorted=sorted(members,key=lambda a:-imp(a))
        winner=members_sorted[0]['url']
        is_dup=len(members)>1
        for a in members_sorted:
            c,i,pos=perf.get(a['url'],(0,0,0))
            wc=wc_for_article(a); wcval=wc[1] if wc else None
            thin = wcval is not None and wcval<700
            has_traffic = i>=50 or c>=1
            if has_traffic:
                verdict="KEEP/EXPAND"
            elif is_dup and a['url']!=winner:
                verdict="MERGE→winner"
            elif thin and i<20 and c==0:
                verdict="REDIRECT"
            else:
                verdict="REVIEW"
            out.append({
                'verdict':verdict,'keyword':a['kw'],'norm_kw':nk,
                'sg_imp':i,'sg_clicks':c,'sg_pos':round(pos,1) if pos else 0,
                'words':wcval if wcval is not None else '?',
                'cluster_size':len(members),
                'is_cluster_winner':'yes' if (is_dup and a['url']==winner) else '',
                'url':a['url'].replace('https://wellnessnest.co',''),
                'merge_into':winner.replace('https://wellnessnest.co','') if (is_dup and a['url']!=winner) else ''
            })

    # sort: actionable first (REDIRECT, MERGE), then by low traffic
    order={'REDIRECT':0,'MERGE→winner':1,'REVIEW':2,'KEEP/EXPAND':3}
    out.sort(key=lambda r:(order[r['verdict']], r['sg_imp']))

    outp=f"{ROOT}/SG_CONSOLIDATION_MAP.csv"
    with open(outp,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['verdict','keyword','sg_imp','sg_clicks','sg_pos','words','cluster_size','is_cluster_winner','merge_into','url','norm_kw'])
        w.writeheader(); w.writerows(out)

    # summary
    from collections import Counter
    cnt=Counter(r['verdict'] for r in out)
    print(f"Wrote {len(out)} rows -> {outp}\n")
    print("=== VERDICT SUMMARY ===")
    for v in ['REDIRECT','MERGE→winner','REVIEW','KEEP/EXPAND']:
        print(f"  {v:14}: {cnt.get(v,0)}")
    dup_clusters=sum(1 for m in clusters.values() if len(m)>1)
    print(f"\n  keyword-duplicate clusters (cannibalization): {dup_clusters}")
    print("\n=== DUPLICATE CLUSTERS (same target keyword, multiple URLs) ===")
    for nk,m in sorted(clusters.items(), key=lambda kv:-len(kv[1])):
        if len(m)<=1: continue
        print(f"  '{m[0]['kw']}' x{len(m)}:")
        for a in sorted(m,key=lambda a:-perf.get(a['url'],(0,0,0))[1]):
            c,i,p=perf.get(a['url'],(0,0,0))
            print(f"      SGimp={i:>4} clk={c} | {a['url'].replace('https://wellnessnest.co','')[:70]}")
    print("\n=== TOP REDIRECT CANDIDATES (thin + no SG traffic) ===")
    for r in [r for r in out if r['verdict']=='REDIRECT'][:20]:
        print(f"  w={r['words']!s:>4} imp={r['sg_imp']:>3} | {r['url'][:72]}")

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""
fetch_all_articles.py — Pull EVERY blog article from Shopify (all blogs, paginated)
and join with SG GSC performance (28d). Outputs ALL_ARTICLES.csv = full corpus,
not just the 92 in the tracker. Read-only.
"""
import json, urllib.request, urllib.parse, csv, re, os, sys, datetime
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from gsc_fetcher import get_service

SHOP= __import__("genseo_config").SHOP
TOKEN= __import__("genseo_config").TOKEN
API="2026-04"
SITE='https://yourdomain.com/'
SG=[{'filters':[{'dimension':'country','operator':'equals','expression':'{{COUNTRY_CODE}}'}]}]
fmt=lambda d:d.strftime('%Y-%m-%d')
ROOT="~/genseo"

def api(url):
    req=urllib.request.Request(url, headers={"X-Shopify-Access-Token":TOKEN})
    res=urllib.request.urlopen(req)
    return res, json.loads(res.read())

def paginate(path):
    """Follow Shopify Link-header cursor pagination."""
    url=f"https://{SHOP}/admin/api/{API}/{path}"
    out=[]
    while url:
        res,data=api(url)
        key=list(data.keys())[0]
        out.extend(data[key])
        link=res.headers.get('Link','')
        nxt=None
        for part in link.split(','):
            if 'rel="next"' in part:
                nxt=part[part.find('<')+1:part.find('>')]
        url=nxt
    return out

def main():
    blogs=paginate("blogs.json?limit=250")
    print(f"Blogs found: {[(b['handle'],b['id']) for b in blogs]}")
    articles=[]
    for b in blogs:
        arts=paginate(f"blogs/{b['id']}/articles.json?limit=250&fields=id,title,handle,created_at,published_at,body_html")
        for a in arts:
            handle=a.get('handle','')
            url=f"https://yourdomain.com/blogs/{b['handle']}/{handle}"
            wc=len(re.sub(r'<[^>]*>',' ', a.get('body_html') or '').split())
            articles.append({'blog':b['handle'],'id':a['id'],'title':a.get('title',''),
                'url':url,'created':(a.get('published_at') or a.get('created_at') or '')[:10],'words':wc})
    print(f"Total articles pulled from Shopify: {len(articles)}")

    # SG perf per page
    svc=get_service()
    end=datetime.date.today()-datetime.timedelta(days=3); start=end-datetime.timedelta(days=27)
    rows=svc.searchanalytics().query(siteUrl=SITE,body={'startDate':fmt(start),'endDate':fmt(end),
        'dimensions':['page'],'rowLimit':25000,'dimensionFilterGroups':SG}).execute().get('rows',[])
    perf={r['keys'][0]:(r['clicks'],r['impressions'],r['position']) for r in rows}

    for a in articles:
        c,i,p=perf.get(a['url'],(0,0,0))
        a['sg_clicks']=c; a['sg_imp']=i; a['sg_pos']=round(p,1) if p else 0

    articles.sort(key=lambda a:(a['sg_imp'], a['sg_clicks']))
    outp=f"{ROOT}/ALL_ARTICLES.csv"
    with open(outp,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['blog','id','title','url','created','words','sg_imp','sg_clicks','sg_pos'])
        w.writeheader(); w.writerows(articles)
    print(f"Wrote {len(articles)} -> {outp}")

    # quick stats
    thin=sum(1 for a in articles if a['words']<700)
    zero=sum(1 for a in articles if a['sg_imp']==0 and a['sg_clicks']==0)
    thinzero=sum(1 for a in articles if a['words']<700 and a['sg_imp']<20 and a['sg_clicks']==0)
    print(f"\n  <700 words: {thin}")
    print(f"  zero SG traffic: {zero}")
    print(f"  thin AND ~zero SG (redirect candidates): {thinzero}")

if __name__=="__main__":
    main()

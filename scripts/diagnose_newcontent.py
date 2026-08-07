"""Does the NEW daily content actually contribute? And what happened to the big loser page?"""
import sys, os, datetime, csv
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from gsc_fetcher import get_service

SITE = 'https://yourdomain.com/'

def q(service, body):
    return service.searchanalytics().query(siteUrl=SITE, body=body).execute().get('rows', [])

def main():
    service = get_service()
    end = datetime.date.today() - datetime.timedelta(days=3)
    start = end - datetime.timedelta(days=27)
    s = start.strftime('%Y-%m-%d'); e = end.strftime('%Y-%m-%d')

    # 1) New articles (tickets posted 2026-05-05 onward) - do they have impressions?
    tracker = '~/genseo/PUBLISHED_ARTICLES_TRACKER.csv'
    new_urls = []
    with open(tracker) as f:
        r = csv.DictReader(f)
        for row in r:
            posted = row.get('Posted Date','')
            if posted >= '2026-05-05':
                new_urls.append(row['Article Link'].strip())
    new_urls = list(dict.fromkeys(new_urls))
    print(f"=== NEW ARTICLES posted >= 2026-05-05: {len(new_urls)} URLs ===")

    # batch query all pages, then intersect
    pages = q(service, {'startDate': s, 'endDate': e, 'dimensions':['page'], 'rowLimit': 5000})
    pmap = {row['keys'][0]: row for row in pages}
    total_pages_with_imp = len(pmap)

    hit = 0; total_imp = 0; total_clicks = 0
    for u in new_urls:
        if u in pmap:
            hit += 1
            total_imp += pmap[u]['impressions']
            total_clicks += pmap[u]['clicks']
    print(f"  of those, appearing in GSC last 28d with ANY impressions: {hit}/{len(new_urls)}")
    print(f"  TOTAL impressions from new articles: {total_imp}")
    print(f"  TOTAL clicks from new articles: {total_clicks}")
    print(f"  (whole site has {total_pages_with_imp} pages with impressions)")

    # 2) The big loser - query level, last 28d vs prior 28d
    loser = 'https://yourdomain.com/blogs/nutrition/1-scoop-of-whey-how-many-calories-protein-nutritional-value-of-whey'
    def qbypage(s,e):
        rows = q(service, {'startDate':s,'endDate':e,'dimensions':['query'],
            'dimensionFilterGroups':[{'filters':[{'dimension':'page','expression':loser,'operator':'equals'}]}],
            'rowLimit':25})
        return {r['keys'][0]:(r['clicks'],r['impressions'],r['position']) for r in rows}
    p1s=(start-datetime.timedelta(days=28)).strftime('%Y-%m-%d'); p1e=(start-datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    m_prior=qbypage(p1s,p1e); m_recent=qbypage(s,e)
    print(f"\n=== BIG LOSER PAGE: 1-scoop-of-whey (query-level) ===")
    print("query | prior(imp,pos) -> recent(imp,pos)")
    allq = sorted(set(m_prior)|set(m_recent), key=lambda k:-(m_prior.get(k,(0,0,0))[1]))
    for k in allq[:12]:
        pr=m_prior.get(k,(0,0,0)); rc=m_recent.get(k,(0,0,0))
        print(f"  {k[:45]:45} | {pr[1]:>6} imp pos {pr[2]:4.1f} -> {rc[1]:>6} imp pos {rc[2]:4.1f}")

if __name__=='__main__':
    main()

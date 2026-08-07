"""SG daily trajectory + collection vs blog split + which page-type drives SG."""
import sys, os, datetime
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from gsc_fetcher import get_service
SITE='https://yourdomain.com/'
SG=[{'filters':[{'dimension':'country','operator':'equals','expression':'{{COUNTRY_CODE}}'}]}]
fmt=lambda d:d.strftime('%Y-%m-%d')
def query(svc,s,e,dims,limit=5000):
    return svc.searchanalytics().query(siteUrl=SITE,body={'startDate':fmt(s),'endDate':fmt(e),'dimensions':dims,'rowLimit':limit,'dimensionFilterGroups':SG}).execute().get('rows',[])
def main():
    svc=get_service()
    end=datetime.date.today()-datetime.timedelta(days=3)
    # SG daily last 35 days
    s=end-datetime.timedelta(days=34)
    rows=sorted((r['keys'][0],r['clicks'],r['impressions'],r['position']) for r in query(svc,s,end,['date'],500))
    print("=== SG DAILY (last 35d) — is it genuinely dropping recently? ===")
    for d,c,i,p in rows:
        bar='#'*int(i/200)
        print(f"  {d}  clk {c:>3}  imp {i:>5} pos {p:4.1f}  {bar}")

    # collection vs blog split, period over period
    p2e=end; p2s=end-datetime.timedelta(days=27); p1e=p2s-datetime.timedelta(days=1); p1s=p1e-datetime.timedelta(days=27)
    def split(s,e):
        d={'collections':[0,0],'blogs':[0,0],'products':[0,0],'pages':[0,0],'home/other':[0,0]}
        for r in query(svc,s,e,['page'],5000):
            u=r['keys'][0];
            k='home/other'
            if '/collections/' in u: k='collections'
            elif '/blogs/' in u: k='blogs'
            elif '/products/' in u: k='products'
            elif '/pages/' in u: k='pages'
            d[k][0]+=r['clicks']; d[k][1]+=r['impressions']
        return d
    a=split(p1s,p1e); b=split(p2s,p2e)
    print("\n=== SG TRAFFIC BY PAGE TYPE (prior -> recent, 28d) ===")
    print(f"{'type':14} {'clicks':>16} {'impressions':>20}")
    for k in ['collections','blogs','products','pages','home/other']:
        print(f"  {k:12} {a[k][0]:>6} -> {b[k][0]:<6}      {a[k][1]:>7} -> {b[k][1]:<7}")

if __name__=='__main__': main()

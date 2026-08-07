"""SG-ONLY weekly reporting standard for wellnessnest.co.
Run this instead of trusting the global GSC dashboard.
Usage: python3 sg_report.py            # default 28d vs prior 28d
       python3 sg_report.py 14          # 14d vs prior 14d
"""
import sys, os, datetime
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from gsc_fetcher import get_service

SITE='https://wellnessnest.co/'
SG=[{'filters':[{'dimension':'country','operator':'equals','expression':'usa'}]}]
fmt=lambda d:d.strftime('%Y-%m-%d')

def query(svc,s,e,dims,limit=25000):
    return svc.searchanalytics().query(siteUrl=SITE,body={
        'startDate':fmt(s),'endDate':fmt(e),'dimensions':dims,'rowLimit':limit,
        'dimensionFilterGroups':SG}).execute().get('rows',[])

def total(svc,s,e):
    rs=query(svc,s,e,[],1)
    if not rs: return (0,0,0,0)
    r=rs[0]; return (r['clicks'],r['impressions'],r['ctr'],r['position'])

def main():
    win=int(sys.argv[1]) if len(sys.argv)>1 else 28
    svc=get_service()
    end=datetime.date.today()-datetime.timedelta(days=3)
    p2e=end; p2s=end-datetime.timedelta(days=win-1)
    p1e=p2s-datetime.timedelta(days=1); p1s=p1e-datetime.timedelta(days=win-1)
    pct=lambda a,b: f"{((b-a)/a*100):+.1f}%" if a else "n/a"

    print(f"=== SINGAPORE SEO REPORT ({win}d vs prior {win}d) — country=sgp ONLY ===")
    print(f"Recent: {p2s}..{p2e}   Prior: {p1s}..{p1e}\n")
    c1=total(svc,p1s,p1e); c2=total(svc,p2s,p2e)
    print(f"  Clicks      {c1[0]:>7} -> {c2[0]:<7} {pct(c1[0],c2[0])}")
    print(f"  Impressions {c1[1]:>7} -> {c2[1]:<7} {pct(c1[1],c2[1])}")
    print(f"  Avg pos     {c1[3]:>7.1f} -> {c2[3]:<7.1f} {c2[3]-c1[3]:+.1f}")
    print(f"  CTR         {c1[2]*100:>6.2f}% -> {c2[2]*100:<6.2f}%")

    def qmap(s,e):
        return {r['keys'][0]:(r['clicks'],r['impressions'],r['position']) for r in query(svc,s,e,['query'])}
    q1=qmap(p1s,p1e); q2=qmap(p2s,p2e)
    dl=sorted(((q2.get(k,(0,0,0))[1]-q1.get(k,(0,0,0))[1],k,q1.get(k,(0,0,0)),q2.get(k,(0,0,0))) for k in set(q1)|set(q2)))
    print("\n  TOP SG QUERY LOSERS (imp delta | pos prior->recent):")
    for d,k,a,b in dl[:10]:
        print(f"    {d:+5} | {k[:40]:40} pos {a[2]:4.1f}->{b[2]:<4.1f}")
    print("\n  TOP SG QUERY GAINERS:")
    for d,k,a,b in dl[-8:][::-1]:
        print(f"    {d:+5} | {k[:40]:40} pos {a[2]:4.1f}->{b[2]:<4.1f}")

if __name__=='__main__': main()

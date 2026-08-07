"""Clean {{MARKET}}-ONLY diagnosis. ALL queries go through the SG-filtered wrapper."""
import sys, os, datetime, csv
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from gsc_fetcher import get_service

SITE='https://wellnessnest.co/'
SG=[{'filters':[{'dimension':'country','operator':'equals','expression':'{{COUNTRY_CODE}}'}]}]
fmt=lambda d:d.strftime('%Y-%m-%d')

def query(svc, s, e, dims, country=True, limit=5000):
    body={'startDate':fmt(s),'endDate':fmt(e),'dimensions':dims,'rowLimit':limit}
    if country: body['dimensionFilterGroups']=SG
    return svc.searchanalytics().query(siteUrl=SITE,body=body).execute().get('rows',[])

def total(svc,s,e,country=True):
    rs=query(svc,s,e,[],country,1)
    if not rs: return (0,0,0,0)
    r=rs[0]; return (r['clicks'],r['impressions'],r['ctr'],r['position'])

def main():
    svc=get_service()
    end=datetime.date.today()-datetime.timedelta(days=3)
    p2e=end; p2s=end-datetime.timedelta(days=27)
    p1e=p2s-datetime.timedelta(days=1); p1s=p1e-datetime.timedelta(days=27)
    pct=lambda a,b: f"{((b-a)/a*100):+.1f}%" if a else "n/a"

    # SG share — now BOTH correctly computed
    sg=total(svc,p2s,p2e,country=True); allc=total(svc,p2s,p2e,country=False)
    print("=== SG SHARE OF TRAFFIC (recent 28d) ===")
    print(f"ALL countries: clicks={allc[0]:>5} imp={allc[1]:>7}")
    print(f"{{MARKET}}    : clicks={sg[0]:>5} imp={sg[1]:>7}  ({sg[1]/allc[1]*100:.0f}% imp, {sg[0]/allc[0]*100:.0f}% clicks)")

    print("\n=== SINGAPORE PERIOD OVER PERIOD (28d, country=sgp) ===")
    c1=total(svc,p1s,p1e); c2=total(svc,p2s,p2e)
    print(f"PRIOR  {p1s}..{p1e}: clicks={c1[0]} imp={c1[1]} ctr={c1[2]:.3f} pos={c1[3]:.1f}")
    print(f"RECENT {p2s}..{p2e}: clicks={c2[0]} imp={c2[1]} ctr={c2[2]:.3f} pos={c2[3]:.1f}")
    print(f"DELTA: clicks {pct(c1[0],c2[0])}  impressions {pct(c1[1],c2[1])}  pos {c2[3]-c1[3]:+.1f}")

    # SG queries — what SG users actually search; which queries lost rank
    print("\n=== TOP SINGAPORE QUERIES: prior vs recent ===")
    def qmap(s,e):
        return {r['keys'][0]:(r['clicks'],r['impressions'],r['position']) for r in query(svc,s,e,['query'],True,5000)}
    q1=qmap(p1s,p1e); q2=qmap(p2s,p2e)
    # rank by recent impressions
    top=sorted(q2.items(), key=lambda kv:-kv[1][1])[:20]
    print(f"{'query':42} {'clk':>4} {'imp':>5} {'pos':>5}  | prior pos")
    for k,(c,i,p) in top:
        pp=q1.get(k,(0,0,0))[2]
        print(f"  {k[:40]:40} {c:>4} {i:>5} {p:5.1f}  | {pp:5.1f}")

    # SG query losers (biggest impression drops among SG queries)
    print("\n=== SG QUERY IMPRESSION LOSERS (rank drops that cost SG impressions) ===")
    deltas=sorted(((q2.get(k,(0,0,0))[1]-q1.get(k,(0,0,0))[1],k,q1.get(k,(0,0,0)),q2.get(k,(0,0,0))) for k in set(q1)|set(q2)))
    for d,k,a,b in deltas[:15]:
        print(f"  {d:+5} | imp {a[1]:>4}->{b[1]:<4} pos {a[2]:4.1f}->{b[2]:<4.1f} clk {a[0]}->{b[0]} | {k[:42]}")
    print("\n=== SG QUERY GAINERS ===")
    for d,k,a,b in deltas[-10:][::-1]:
        print(f"  {d:+5} | imp {a[1]:>4}->{b[1]:<4} pos {a[2]:4.1f}->{b[2]:<4.1f} clk {a[0]}->{b[0]} | {k[:42]}")

if __name__=='__main__': main()

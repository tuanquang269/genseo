"""US-ONLY decline diagnosis. Filters GSC by country=sgp."""
import sys, os, datetime, csv
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from gsc_fetcher import get_service

SITE='https://wellnessnest.co/'
SG=[{'filters':[{'dimension':'country','operator':'equals','expression':'usa'}]}]

def q(svc,b):
    b.setdefault('dimensionFilterGroups', SG)
    return svc.searchanalytics().query(siteUrl=SITE,body=b).execute().get('rows',[])

def main():
    svc=get_service()
    end=datetime.date.today()-datetime.timedelta(days=3)
    p2e=end; p2s=end-datetime.timedelta(days=27)
    p1e=p2s-datetime.timedelta(days=1); p1s=p1e-datetime.timedelta(days=27)
    fmt=lambda d:d.strftime('%Y-%m-%d')

    # ---- SG vs ALL split (sanity: how much of traffic is even SG?) ----
    def totals(s,e,sg=True):
        body={'startDate':fmt(s),'endDate':fmt(e),'dimensions':[],'rowLimit':1}
        if not sg: body['dimensionFilterGroups']=[]
        rs=svc.searchanalytics().query(siteUrl=SITE,body=body).execute().get('rows',[])
        if not rs: return (0,0,0,0)
        r=rs[0]; return (r['clicks'],r['impressions'],r['ctr'],r['position'])
    allr=totals(p2s,p2e,sg=False); sgr=totals(p2s,p2e,sg=True)
    print("=== SG SHARE OF TRAFFIC (recent 28d) ===")
    print(f"ALL countries: clicks={allr[0]} imp={allr[1]}")
    print(f"US    : clicks={sgr[0]} imp={sgr[1]}  ({sgr[1]/allr[1]*100:.0f}% of impressions, {sgr[0]/allr[0]*100:.0f}% of clicks)")

    # ---- SG period over period ----
    c1=totals(p1s,p1e); c2=totals(p2s,p2e)
    pct=lambda a,b: f"{((b-a)/a*100):+.1f}%" if a else "n/a"
    print(f"\n=== SINGAPORE PERIOD OVER PERIOD (28d) ===")
    print(f"PRIOR  {p1s}..{p1e}: clicks={c1[0]} imp={c1[1]} ctr={c1[2]:.3f} pos={c1[3]:.1f}")
    print(f"RECENT {p2s}..{p2e}: clicks={c2[0]} imp={c2[1]} ctr={c2[2]:.3f} pos={c2[3]:.1f}")
    print(f"DELTA: clicks {pct(c1[0],c2[0])}  impressions {pct(c1[1],c2[1])}  pos {c2[3]-c1[3]:+.1f}")

    # ---- SG weekly trend ----
    s56=end-datetime.timedelta(days=55)
    rows=q(svc,{'startDate':fmt(s56),'endDate':fmt(end),'dimensions':['date'],'rowLimit':500})
    daily=sorted((r['keys'][0],r['clicks'],r['impressions'],r['position']) for r in rows)
    print("\n=== SINGAPORE WEEKLY TREND ===")
    for i in range(0,len(daily),7):
        ch=daily[i:i+7]
        if not ch: continue
        print(f"  {ch[0][0]}..{ch[-1][0]}: clicks={sum(x[1] for x in ch):>4} imp={sum(x[2] for x in ch):>6} pos={sum(x[3] for x in ch)/len(ch):4.1f}")

    # ---- SG page-level deltas ----
    def pm(s,e):
        return {r['keys'][0]:(r['clicks'],r['impressions'],r['position']) for r in q(svc,{'startDate':fmt(s),'endDate':fmt(e),'dimensions':['page'],'rowLimit':5000})}
    m1=pm(p1s,p1e); m2=pm(p2s,p2e)
    print(f"\n=== SINGAPORE PAGE COUNTS === prior={len(m1)} recent={len(m2)}")
    deltas=sorted(((m2.get(u,(0,0,0))[1]-m1.get(u,(0,0,0))[1],u,m1.get(u,(0,0,0)),m2.get(u,(0,0,0))) for u in set(m1)|set(m2)))
    gross_loss=sum(d[0] for d in deltas if d[0]<0)
    print(f"gross SG loss={gross_loss}  top1={sum(x[0] for x in deltas[:1])} top5={sum(x[0] for x in deltas[:5])} top10={sum(x[0] for x in deltas[:10])}")
    print("\n--- TOP 15 SG IMPRESSION LOSERS ---")
    for d,u,a,b in deltas[:15]:
        print(f"  {d:+6} | imp {a[1]:>5}->{b[1]:<5} clk {a[0]:>3}->{b[0]:<3} pos {a[2]:4.0f}->{b[2]:<4.0f} | {u.replace('https://wellnessnest.co','')[:60]}")
    print("\n--- TOP 10 SG GAINERS ---")
    for d,u,a,b in deltas[-10:][::-1]:
        print(f"  {d:+6} | imp {a[1]:>5}->{b[1]:<5} clk {a[0]:>3}->{b[0]:<3} pos {a[2]:4.0f}->{b[2]:<4.0f} | {u.replace('https://wellnessnest.co','')[:60]}")

    # ---- Do new articles get SG traffic? ----
    tracker='/Users/kevinkreative/genseo/PUBLISHED_ARTICLES_TRACKER.csv'
    new=[]
    with open(tracker) as f:
        for row in csv.DictReader(f):
            if row.get('Posted Date','')>='2026-05-05': new.append(row['Article Link'].strip())
    new=list(dict.fromkeys(new))
    hit=sum(1 for u in new if u in m2); imp=sum(m2.get(u,(0,0,0))[1] for u in new); clk=sum(m2.get(u,(0,0,0))[0] for u in new)
    print(f"\n=== NEW ARTICLES (>=2026-05-05, n={len(new)}) — SINGAPORE ONLY ===")
    print(f"  appearing in SG GSC: {hit}/{len(new)}  |  SG impressions={imp}  SG clicks={clk}")

if __name__=='__main__': main()

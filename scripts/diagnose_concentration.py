"""Is the impression loss concentrated in a few pages, or broad/sitewide?"""
import sys, os, datetime
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from gsc_fetcher import get_service
SITE='https://yourdomain.com/'
def q(svc,b): return svc.searchanalytics().query(siteUrl=SITE,body=b).execute().get('rows',[])
def main():
    svc=get_service()
    end=datetime.date.today()-datetime.timedelta(days=3)
    p2e=end; p2s=end-datetime.timedelta(days=27); p1e=p2s-datetime.timedelta(days=1); p1s=p1e-datetime.timedelta(days=27)
    def pm(s,e):
        return {r['keys'][0]:r['impressions'] for r in q(svc,{'startDate':s.strftime('%Y-%m-%d'),'endDate':e.strftime('%Y-%m-%d'),'dimensions':['page'],'rowLimit':5000})}
    m1=pm(p1s,p1e); m2=pm(p2s,p2e)
    deltas=sorted(((m2.get(u,0)-m1.get(u,0)) for u in set(m1)|set(m2)))
    total_loss=sum(d for d in deltas if d<0)
    total_gain=sum(d for d in deltas if d>0)
    net=total_loss+total_gain
    top1=sum(sorted(deltas)[:1]); top5=sum(sorted(deltas)[:5]); top10=sum(sorted(deltas)[:10])
    losers=sum(1 for d in deltas if d<0); gainers=sum(1 for d in deltas if d>0)
    print(f"PRIOR total imp (top5k pages): {sum(m1.values())}")
    print(f"RECENT total imp (top5k pages): {sum(m2.values())}")
    print(f"NET change: {net:+}")
    print(f"  gross loss: {total_loss}   gross gain: {total_gain:+}")
    print(f"  pages down: {losers}   pages up: {gainers}")
    print(f"\nConcentration of the GROSS LOSS:")
    print(f"  worst 1 page  = {top1} ({top1/total_loss*100:.0f}% of all losses)")
    print(f"  worst 5 pages = {top5} ({top5/total_loss*100:.0f}% of all losses)")
    print(f"  worst 10 pages= {top10} ({top10/total_loss*100:.0f}% of all losses)")
if __name__=='__main__': main()

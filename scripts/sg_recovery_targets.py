"""Build the SG recovery target list:
For each commercial SG query that lost rank/visibility, find which PAGE ranked for it,
its click potential, and current status. Also surface SG-volume opportunity queries.
Outputs SG_RECOVERY_TARGETS.csv"""
import sys, os, datetime, csv
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from gsc_fetcher import get_service

SITE='https://yourdomain.com/'
SG=[{'filters':[{'dimension':'country','operator':'equals','expression':'{{COUNTRY_CODE}}'}]}]
fmt=lambda d:d.strftime('%Y-%m-%d')

def query(svc,s,e,dims,limit=25000):
    return svc.searchanalytics().query(siteUrl=SITE,body={
        'startDate':fmt(s),'endDate':fmt(e),'dimensions':dims,'rowLimit':limit,
        'dimensionFilterGroups':SG}).execute().get('rows',[])

def main():
    svc=get_service()
    end=datetime.date.today()-datetime.timedelta(days=3)
    p2e=end; p2s=end-datetime.timedelta(days=27)
    p1e=p2s-datetime.timedelta(days=1); p1s=p1e-datetime.timedelta(days=27)

    # query-level deltas
    def qmap(s,e):
        return {r['keys'][0]:(r['clicks'],r['impressions'],r['ctr'],r['position']) for r in query(svc,s,e,['query'])}
    q1=qmap(p1s,p1e); q2=qmap(p2s,p2e)

    # query+page map (recent + prior) to attribute each query to a URL
    def qpmap(s,e):
        m={}
        for r in query(svc,s,e,['query','page']):
            qk,pg=r['keys']; m.setdefault(qk,[]).append((pg,r['impressions'],r['position']))
        # pick the page with most impressions per query
        return {k:max(v,key=lambda x:x[1]) for k,v in m.items()}
    qp1=qpmap(p1s,p1e); qp2=qpmap(p2s,p2e)

    # Commercial intent signal: contains a brand, category, or '{{market}}'/'buy'/'shop'/'price'/'near me'
    COMM=['{{market}}','sg','buy','shop','price','near me','cheap','best','where','store',
          'optimum','myprotein','my protein','dymatize','mutant','ghost','quest','musclepharm',
          'muscletech','nutricost','natrol','california gold','sports research','isopure',
          'mass gainer','pre workout','preworkout','creatine','fat burner','protein powder',
          'whey protein','protein bar','blender bottle','owala','collagen','barebells','meiji']
    def is_comm(k): return any(t in k for t in COMM)

    rows=[]
    for k in set(q1)|set(q2):
        a=q1.get(k,(0,0,0,0)); b=q2.get(k,(0,0,0,0))
        imp_delta=b[1]-a[1]
        # candidates: lost visibility OR dropped >=3 positions, commercial, had real prior impressions
        prior_imp=a[1]; recent_imp=b[1]; prior_pos=a[3]; recent_pos=b[3]
        lost_vis = prior_imp>=30 and recent_imp==0
        rank_drop = prior_imp>=30 and recent_imp>0 and (recent_pos-prior_pos)>=3
        if (lost_vis or rank_drop) and is_comm(k):
            pg = qp1.get(k,('?',0,0))[0]  # page that ranked PRIOR
            status='LOST_VISIBILITY' if lost_vis else 'RANK_DROP'
            rows.append({
                'query':k,'status':status,
                'prior_imp':prior_imp,'recent_imp':recent_imp,
                'prior_pos':round(prior_pos,1),'recent_pos':round(recent_pos,1),
                'prior_clicks':a[0],'recent_clicks':b[0],
                'imp_delta':imp_delta,'ranking_page':pg.replace('https://yourdomain.com','')
            })
    rows.sort(key=lambda r:(r['status']!='LOST_VISIBILITY', -r['prior_imp']))

    out='~/genseo/SG_RECOVERY_TARGETS.csv'
    with open(out,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['query','status','prior_pos','recent_pos','prior_imp','recent_imp','prior_clicks','recent_clicks','imp_delta','ranking_page'])
        w.writeheader(); w.writerows(rows)
    print(f"Wrote {len(rows)} SG recovery targets -> {out}\n")
    print(f"{'query':38} {'status':16} {'pos':>10} {'imp p->r':>12} {'page'}")
    for r in rows[:30]:
        print(f"  {r['query'][:36]:36} {r['status']:16} {r['prior_pos']:4.0f}->{r['recent_pos']:<4.0f} {r['prior_imp']:>5}->{r['recent_imp']:<5} {r['ranking_page'][:40]}")

    # ---- SG OPPORTUNITY: queries where we rank pos 5-20 with real impressions = striking distance ----
    print("\n=== SG STRIKING-DISTANCE OPPORTUNITIES (pos 5-15, imp>=50, commercial) ===")
    opp=[]
    for k,(c,i,ct,p) in q2.items():
        if 5<=p<=15 and i>=50 and is_comm(k):
            pg=qp2.get(k,('?',0,0))[0].replace('https://yourdomain.com','')
            opp.append((i,p,c,k,pg))
    opp.sort(reverse=True)
    out2='~/genseo/SG_OPPORTUNITIES.csv'
    with open(out2,'w',newline='') as f:
        w=csv.writer(f); w.writerow(['query','position','impressions','clicks','ranking_page'])
        for i,p,c,k,pg in opp: w.writerow([k,round(p,1),i,c,pg])
    for i,p,c,k,pg in opp[:20]:
        print(f"  {k[:38]:38} pos {p:4.1f}  imp {i:>5}  clk {c:>3}  | {pg[:38]}")
    print(f"\nWrote {len(opp)} opportunities -> {out2}")

if __name__=='__main__': main()

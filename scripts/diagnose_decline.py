"""Diagnostic: verify and quantify the impressions/clicks decline from GSC.
Pulls daily trend, period-over-period comparison, and per-page deltas."""
import sys, os, datetime, json
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from gsc_fetcher import get_service

SITE = 'https://yourdomain.com/'

def q(service, body):
    return service.searchanalytics().query(siteUrl=SITE, body=body).execute().get('rows', [])

def main():
    service = get_service()
    today = datetime.date.today()
    # GSC data lags ~2-3 days; anchor window end 3 days back to avoid partial data
    end = today - datetime.timedelta(days=3)

    # 1) Daily trend, last 56 days
    start = end - datetime.timedelta(days=55)
    rows = q(service, {
        'startDate': start.strftime('%Y-%m-%d'),
        'endDate': end.strftime('%Y-%m-%d'),
        'dimensions': ['date'],
        'rowLimit': 500,
    })
    print("=== DAILY TREND (clicks / impressions / avg position) ===")
    print(f"window: {start} to {end}")
    daily = []
    for r in rows:
        d = r['keys'][0]
        daily.append((d, r['clicks'], r['impressions'], r['position']))
    daily.sort()
    # weekly buckets for readability
    print("\nWeekly rollup (Mon-anchored buckets of 7):")
    for i in range(0, len(daily), 7):
        chunk = daily[i:i+7]
        if not chunk: continue
        c = sum(x[1] for x in chunk)
        imp = sum(x[2] for x in chunk)
        avgpos = sum(x[3] for x in chunk)/len(chunk)
        print(f"  {chunk[0][0]} .. {chunk[-1][0]}: clicks={c:>5}  impressions={imp:>7}  avg_pos={avgpos:5.1f}")

    # 2) Period over period: last 28d vs prior 28d
    p2_end = end
    p2_start = end - datetime.timedelta(days=27)
    p1_end = p2_start - datetime.timedelta(days=1)
    p1_start = p1_end - datetime.timedelta(days=27)

    def totals(s, e):
        rs = q(service, {'startDate': s.strftime('%Y-%m-%d'), 'endDate': e.strftime('%Y-%m-%d'),
                         'dimensions': [], 'rowLimit': 1})
        if not rs: return (0,0,0,0)
        r = rs[0]
        return (r['clicks'], r['impressions'], r['ctr'], r['position'])

    print("\n=== PERIOD OVER PERIOD (28d) ===")
    c1 = totals(p1_start, p1_end)
    c2 = totals(p2_start, p2_end)
    print(f"PRIOR  {p1_start}..{p1_end}: clicks={c1[0]} imp={c1[1]} ctr={c1[2]:.3f} pos={c1[3]:.1f}")
    print(f"RECENT {p2_start}..{p2_end}: clicks={c2[0]} imp={c2[1]} ctr={c2[2]:.3f} pos={c2[3]:.1f}")
    def pct(a,b): return f"{((b-a)/a*100):+.1f}%" if a else "n/a"
    print(f"DELTA: clicks {pct(c1[0],c2[0])}  impressions {pct(c1[1],c2[1])}  pos {c2[3]-c1[3]:+.1f}")

    # 3) Page-level deltas
    def page_map(s, e):
        rs = q(service, {'startDate': s.strftime('%Y-%m-%d'), 'endDate': e.strftime('%Y-%m-%d'),
                         'dimensions': ['page'], 'rowLimit': 1000})
        return {r['keys'][0]: (r['clicks'], r['impressions'], r['position']) for r in rs}
    m1 = page_map(p1_start, p1_end)
    m2 = page_map(p2_start, p2_end)
    print(f"\n=== PAGE COUNTS ===")
    print(f"pages with impressions PRIOR: {len(m1)}  RECENT: {len(m2)}")

    deltas = []
    for url in set(m1) | set(m2):
        i1 = m1.get(url, (0,0,0))[1]
        i2 = m2.get(url, (0,0,0))[1]
        deltas.append((i2-i1, url, i1, i2, m1.get(url,(0,0,0))[2], m2.get(url,(0,0,0))[2]))
    deltas.sort()
    print("\n--- TOP 15 IMPRESSION LOSERS (page) ---")
    for d, url, i1, i2, p1, p2 in deltas[:15]:
        print(f"  {d:+6} | {i1:>5}->{i2:<5} pos {p1:4.0f}->{p2:<4.0f} | {url.replace('https://yourdomain.com','')}")
    print("\n--- TOP 10 IMPRESSION GAINERS (page) ---")
    for d, url, i1, i2, p1, p2 in deltas[-10:][::-1]:
        print(f"  {d:+6} | {i1:>5}->{i2:<5} pos {p1:4.0f}->{p2:<4.0f} | {url.replace('https://yourdomain.com','')}")

if __name__ == '__main__':
    main()

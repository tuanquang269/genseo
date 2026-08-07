#!/usr/bin/env python3
"""refresh_targets.py — build a PAGE-LEVEL-ACCURATE refresh queue.

Why: the old jul27-refresh-tickets.md ranked targets by query-level aggregates, which misattribute
impressions. Verified failures: "owala {{market}}" (9.5k imp) credited to the Bottle Boot article is
actually won by /collections/owala; "myprotein vs optimum nutrition" flagged pos 13.8 CLIMB is
actually pos 1.9 on the real article. Refreshing a page that already ranks (or the wrong URL) wastes
effort and risks the title-reset damage. This finder attributes every SG query to the ACTUAL page
Google ranks and only surfaces pages with genuine fixable upside.

For each of OUR blog article URLs (anchor #fragments merged), it reports:
  - real totals (imp / clicks / weighted avg pos)
  - CLIMB queries: this page ranks pos 8–20 (just off / near page 1) with real imp -> add depth
  - CTR queries:   this page ranks pos 2–7 but CTR < CTR_FLOOR -> sharpen meta/title
A page is a target only if it has climbable or weak-CTR demand ITSELF (not a sibling/collection).

Usage: refresh_targets.py [out.md] [--min-imp 150]
"""
import datetime, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gsc_fetcher import get_service

SITE = "https://yourdomain.com/"
CLIMB_LO, CLIMB_HI = 8.0, 20.0     # just-off-page-1 .. top-of-page-2 = realistic to climb with depth
CTR_LO, CTR_HI = 2.0, 7.99         # page-1 positions where a weak CTR is a meta/title problem
CTR_FLOOR = 0.02                   # < 2% CTR at a page-1 position = fixable underclick


def pull(dimensions, filters, limit=25000):
    svc = get_service()
    end = datetime.date.today().strftime('%Y-%m-%d')
    start = (datetime.date.today() - datetime.timedelta(days=90)).strftime('%Y-%m-%d')
    body = {'startDate': start, 'endDate': end, 'dimensions': dimensions, 'rowLimit': limit,
            'dimensionFilterGroups': [{'filters': filters}]}
    return svc.searchanalytics().query(siteUrl=SITE, body=body).execute().get('rows', [])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out = args[0] if args else f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/refresh-targets-verified.md"
    min_imp = int(sys.argv[sys.argv.index('--min-imp') + 1]) if '--min-imp' in sys.argv else 150

    rows = pull(['page', 'query'],
                [{'dimension': 'country', 'operator': 'equals', 'expression': '{{COUNTRY_CODE}}'},
                 {'dimension': 'page', 'operator': 'contains', 'expression': '/blogs/'}])
    # aggregate per canonical page (strip #fragment)
    pages = {}
    for r in rows:
        page, q = r['keys']
        page = page.split('#')[0]
        imp, clk, pos = int(r['impressions']), int(r['clicks']), r['position']
        p = pages.setdefault(page, {'imp': 0, 'clk': 0, 'wpos': 0.0, 'q': []})
        p['imp'] += imp; p['clk'] += clk; p['wpos'] += pos * imp
        p['q'].append((q, imp, clk, round(pos, 1)))

    targets = []
    for page, p in pages.items():
        if p['imp'] < min_imp:
            continue
        avgpos = p['wpos'] / p['imp']
        climb = [(q, i, c, ps) for q, i, c, ps in p['q'] if CLIMB_LO <= ps <= CLIMB_HI and i >= 10]
        ctr = [(q, i, c, ps) for q, i, c, ps in p['q']
               if CTR_LO <= ps < CTR_HI and i >= 20 and (c / i if i else 0) < CTR_FLOOR]
        climb_imp = sum(i for _, i, _, _ in climb)
        ctr_imp = sum(i for _, i, _, _ in ctr)
        if not climb and not ctr:
            continue                              # already ranking well / no fixable demand on THIS page
        targets.append({'page': page, 'imp': p['imp'], 'clk': p['clk'], 'avgpos': avgpos,
                        'climb': sorted(climb, key=lambda x: -x[1])[:6], 'climb_imp': climb_imp,
                        'ctr': sorted(ctr, key=lambda x: -x[1])[:6], 'ctr_imp': ctr_imp,
                        'score': climb_imp + ctr_imp})
    targets.sort(key=lambda t: -t['score'])

    L = ["# 🔁 Refresh targets — PAGE-LEVEL VERIFIED (each query attributed to the page Google actually ranks)", "",
         f"*SG only, 90d, min {min_imp} imp/page. CLIMB = this page ranks pos {CLIMB_LO:.0f}–{CLIMB_HI:.0f} "
         f"(append-only depth, KEEP title). CTR = pos {CTR_LO:.0f}–{CTR_HI:.0f} but <{CTR_FLOOR*100:.0f}% CTR "
         "(sharpen meta; title only if needed). Pages already ranking pos<4 or with no fixable demand are EXCLUDED. "
         "Verify a page owns the query itself before editing — this file already did that.*", ""]
    for i, t in enumerate(targets, 1):
        slug = t['page'].split('/nutrition/')[-1].split('/')[-1]
        L.append(f"## Refresh #{i} — {slug[:70]}")
        L.append(f"- **URL**: {t['page']}")
        L.append(f"- **Real page totals**: {t['imp']} imp / {t['clk']} clk / avg pos {t['avgpos']:.1f} "
                 f"| fixable-imp score {t['score']}")
        if t['climb']:
            L.append(f"- **CLIMB (pos 8–20, add depth append-only)** — {t['climb_imp']} imp:")
            for q, im, c, ps in t['climb']:
                L.append(f"    - `{q}`  ({im} imp, {c} clk, pos {ps})")
        if t['ctr']:
            L.append(f"- **CTR (pos 2–7, weak click-through, sharpen meta)** — {t['ctr_imp']} imp:")
            for q, im, c, ps in t['ctr']:
                L.append(f"    - `{q}`  ({im} imp, {c} clk, pos {ps}, CTR {c/im*100:.1f}%)")
        L.append("")
    open(out, "w").write("\n".join(L))
    print(f"refresh targets: {len(targets)} pages with genuine fixable upside -> {os.path.basename(out)}")
    for t in targets[:12]:
        slug = t['page'].split('/nutrition/')[-1][:52]
        print(f"  score {t['score']:>5} | {t['imp']:>5} imp pos {t['avgpos']:>4.1f} | {slug}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
keyword_target_map.py — for each of OUR article pages, find the keyword it WANTS to rank for
(its highest-demand SG query), its current position, and bucket it by what action actually moves it:

  🚀 PUSH   pos 8–20 on a keyword with real demand (imp>=MIN_PUSH_IMP) -> near page 1, worth the effort:
            internal-link authority in + append-only depth. THIS is "rank the page for its keyword".
  ✅ WIN    target pos < 8 -> already page 1. Leave it (CTR meta only if weak).
  🪨 FAR    target pos > 20 -> far from page 1; low ROI, deprioritize (authority-bound / weak intent).
  🧟 ZOMBIE page total SG imp < ZOMBIE_IMP -> ranks ~nothing; dead weight (dclean/merge candidate).
  🔀 CANNIBAL flag: the page's target keyword is ALSO ranked >=CANNIB_IMP by another of our pages
            -> genuine same-keyword competition; consolidate that specific pair (NOT the whole brand).

Reframe this encodes: the goal is keywords ON PAGE 1, not the raw count of ranked keywords. A page at
pos 12 "ranks" its keyword but earns ~nothing; PUSH turns rankings into traffic. READ-ONLY (no changes).

Usage: keyword_target_map.py [--filter <handle-substr>] [out.md]
"""
import datetime, os, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gsc_fetcher import get_service

SITE = "https://wellnessnest.co/"
MIN_PUSH_IMP = 30    # a target kw needs this much 90d SG demand to be worth pushing
ZOMBIE_IMP   = 10    # page total imp below this = ranks ~nothing
CANNIB_IMP   = 15    # two pages each >= this on the same query = real competition on it
PUSH_LO, PUSH_HI = 8.0, 20.0


def pull():
    svc = get_service()
    end = datetime.date.today().strftime('%Y-%m-%d')
    start = (datetime.date.today() - datetime.timedelta(days=90)).strftime('%Y-%m-%d')
    return svc.searchanalytics().query(siteUrl=SITE, body={
        'startDate': start, 'endDate': end, 'dimensions': ['page', 'query'], 'rowLimit': 25000,
        'dimensionFilterGroups': [{'filters': [
            {'dimension': 'country', 'operator': 'equals', 'expression': 'usa'},
            {'dimension': 'page', 'operator': 'contains', 'expression': '/blogs/'}]}]}).execute().get('rows', [])


def main():
    filt = sys.argv[sys.argv.index('--filter') + 1] if '--filter' in sys.argv else None
    pos_args = [a for a in sys.argv[1:] if not a.startswith('--') and a != filt]
    out = pos_args[0] if pos_args else f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/keyword-target-map{('-'+filt) if filt else ''}.md"

    rows = pull()
    pages = {}
    qmap = defaultdict(lambda: defaultdict(int))   # query -> handle -> imp (cannibalization)
    for r in rows:
        page, q = r['keys']
        h = page.split('#')[0].rstrip('/').split('/')[-1]
        imp, clk, pos = int(r['impressions']), int(r['clicks']), r['position']
        p = pages.setdefault(h, {'imp': 0, 'clk': 0, 'wpos': 0.0, 'q': []})
        p['imp'] += imp; p['clk'] += clk; p['wpos'] += pos * imp
        p['q'].append((q, imp, clk, pos))
        qmap[q][h] += imp

    if filt:
        pages = {h: p for h, p in pages.items() if filt in h}

    rank = {'PUSH': [], 'WIN': [], 'FAR': [], 'ZOMBIE': []}
    for h, p in pages.items():
        # aggregate identical queries (GSC can split rows), then target = highest-imp query
        agg = defaultdict(lambda: [0, 0, 0.0])
        for q, i, c, ps in p['q']:
            a = agg[q]; a[0] += i; a[1] += c; a[2] += ps * i
        tq = max(agg, key=lambda q: agg[q][0])
        ti, tc, twp = agg[tq]; tpos = twp / ti if ti else 999
        avgpos = p['wpos'] / p['imp'] if p['imp'] else 999
        # cannibalization: another page also ranks the target kw >= CANNIB_IMP
        rivals = {rh: im for rh, im in qmap[tq].items() if rh != h and im >= CANNIB_IMP and (not filt or filt in rh)}
        rec = {'h': h, 'imp': p['imp'], 'clk': p['clk'], 'avgpos': avgpos,
               'tq': tq, 'ti': ti, 'tc': tc, 'tpos': tpos, 'rivals': rivals}
        if p['imp'] < ZOMBIE_IMP:
            rank['ZOMBIE'].append(rec)
        elif tpos < PUSH_LO:
            rank['WIN'].append(rec)
        elif PUSH_LO <= tpos <= PUSH_HI and ti >= MIN_PUSH_IMP:
            rank['PUSH'].append(rec)
        else:
            rank['FAR'].append(rec)
    for k in rank:
        rank[k].sort(key=lambda r: -r['ti'])

    L = [f"# 🎯 Keyword Target Map{(' — '+filt) if filt else ''} (SG, 90d, page-level attribution)", "",
         "*Each page → the keyword it WANTS to rank for (highest-demand SG query) + current position. "
         f"🚀 PUSH = pos {PUSH_LO:.0f}–{PUSH_HI:.0f} w/ ≥{MIN_PUSH_IMP} imp (near page 1 → internal-link + depth). "
         "✅ WIN = pos <8 (page 1, leave). 🪨 FAR = pos >20 (low ROI). 🧟 ZOMBIE = <10 imp (dead). "
         "🔀 = another of our pages also ranks this keyword (consolidate that pair only).*", ""]
    for k, emoji, note in [('PUSH','🚀','the opportunity — turn rankings into page-1 traffic'),
                           ('WIN','✅','already page 1'), ('FAR','🪨','far from page 1, deprioritize'),
                           ('ZOMBIE','🧟','ranks ~nothing')]:
        g = rank[k]
        tot = sum(r['ti'] for r in g)
        L.append(f"## {emoji} {k} — {len(g)} pages ({note}) | {tot} target-kw imp")
        for r in g:
            flag = f"  🔀 vs {', '.join(f'{rh}={im}' for rh,im in r['rivals'].items())}" if r['rivals'] else ""
            L.append(f"- **{r['tq']}** — pos {r['tpos']:.1f}, {r['ti']}imp/{r['tc']}clk  →  `{r['h'][:56]}` "
                     f"(page {r['clk']}clk/{r['imp']}imp){flag}")
        L.append("")
    open(out, "w").write("\n".join(L))
    print(f"keyword target map{(' ['+filt+']') if filt else ''}: "
          f"PUSH {len(rank['PUSH'])} | WIN {len(rank['WIN'])} | FAR {len(rank['FAR'])} | ZOMBIE {len(rank['ZOMBIE'])} "
          f"-> {os.path.basename(out)}")
    print("\nTop PUSH (near page 1, real demand — the priority):")
    for r in rank['PUSH'][:12]:
        fl = " 🔀" if r['rivals'] else ""
        print(f"  pos {r['tpos']:>4.1f} {r['ti']:>4}imp {r['tc']:>2}clk | {r['tq'][:38]:38} | {r['h'][:40]}{fl}")


if __name__ == '__main__':
    main()

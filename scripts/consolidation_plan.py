#!/usr/bin/env python3
"""consolidation_plan.py — build a REVIEW-FIRST cannibalization consolidation plan (READ-ONLY).

The cheap-model daily publishing has, over time, created many near-duplicate articles on the same
brand/topic (MuscleTech Nitro-Tech ~4 versions, ON whey, Myprotein Impact, Meiji ×3, "best protein
powder" ×4-5...). Google splits authority across them, likely pinning high-imp pages at pos 8-13.
Consolidating each cluster (301 the weaker versions into the strongest) concentrates authority.

This produces the PLAN only — no site changes. For each cluster it picks the WINNER by real SG data
(clicks → imp → best avg position → oldest/most-authoritative) and lists the LOSERS to 301, with a
per-cluster risk flag (a loser with real clicks needs its unique content merged append-only into the
winner FIRST, and is higher-risk). Owner reviews the whole plan before any redirect is executed.

Output: consolidation-plan.md, clusters ranked by total SG impressions (biggest opportunity first).
"""
import datetime, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gsc_fetcher import get_service

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://wellnessnest.co/"
MIN_Q_IMP = 25   # an article must get >= this imp on a query to count as "competing" for it


def pull(dimensions):
    svc = get_service()
    end = datetime.date.today().strftime('%Y-%m-%d')
    start = (datetime.date.today() - datetime.timedelta(days=90)).strftime('%Y-%m-%d')
    body = {'startDate': start, 'endDate': end, 'dimensions': dimensions, 'rowLimit': 25000,
            'dimensionFilterGroups': [{'filters': [
                {'dimension': 'country', 'operator': 'equals', 'expression': '{{COUNTRY_CODE}}'},
                {'dimension': 'page', 'operator': 'contains', 'expression': '/blogs/'}]}]}
    return svc.searchanalytics().query(siteUrl=SITE, body=body).execute().get('rows', [])


def main():
    arts = json.load(open(f"{ROOT}/existing_articles.json"))
    by_handle = {a['handle']: a for a in arts}

    # page-level totals
    stats = {}
    for r in pull(['page']):
        url = r['keys'][0].split('#')[0]
        s = stats.setdefault(url, [0, 0, 0.0])
        s[0] += int(r['clicks']); s[1] += int(r['impressions']); s[2] += r['position'] * int(r['impressions'])
    for a in arts:
        u = a['handle']
        # match the GSC page whose last path segment == handle
        rec = next(([c, i, wp] for url, (c, i, wp) in stats.items() if url.rstrip('/').split('/')[-1] == u), [0, 0, 0.0])
        a['clicks'], a['imp'], a['pos'] = rec[0], rec[1], (rec[2] / rec[1] if rec[1] else 999)

    # CANNIBALIZATION by query CO-COMPETITION (catches meiji etc. that title-similarity misses):
    # for each query, the set of our articles each earning >= MIN_Q_IMP is a competing set.
    from collections import defaultdict
    qgroups = defaultdict(lambda: defaultdict(int))   # query -> handle -> imp
    for r in pull(['query', 'page']):
        q, url = r['keys']
        h = url.split('#')[0].rstrip('/').split('/')[-1]
        if h in by_handle:
            qgroups[q][h] += int(r['impressions'])
    # group identical competing-sets, aggregate contested imp + queries
    setmap = defaultdict(lambda: [0, []])   # frozenset(handles) -> [contested imp, queries]
    for q, hits in qgroups.items():
        competing = frozenset(h for h, im in hits.items() if im >= MIN_Q_IMP)
        if len(competing) >= 2:
            setmap[competing][0] += sum(hits[h] for h in competing)
            setmap[competing][1].append(q)

    # Build (winner, loser) edges from each competing set, then assign each loser to the SINGLE
    # winner it competes with most (by shared imp) so every article is redirected at most once and
    # Sếp reviews ONE decision per winner page (not the same winner scattered across many clusters).
    def rank_key(h):
        a = by_handle[h]
        return (-a['clicks'], -a['imp'], a['pos'], a['id'])
    from collections import defaultdict
    loser_best = {}   # loser handle -> (winner handle, contested imp, set(queries))
    for handles, (cimp, qs) in setmap.items():
        win = min(handles, key=rank_key)
        for lo in handles:
            if lo == win:
                continue
            cur = loser_best.get(lo)
            if cur is None or cimp > cur[1]:
                loser_best[lo] = (win, cimp, set(qs))
    winners = defaultdict(lambda: {'losers': [], 'qs': set(), 'imp': 0})
    for lo, (win, cimp, qs) in loser_best.items():
        # don't let a page be both a winner elsewhere and a loser here: keep it a loser only if it
        # truly ranks worse than its assigned winner (rank_key already guaranteed win is best in-set)
        w = winners[win]
        w['losers'].append(lo); w['qs'] |= qs; w['imp'] += by_handle[lo]['imp']
    clusters = []
    for win, d in winners.items():
        g = [by_handle[win]] + sorted((by_handle[h] for h in d['losers']), key=lambda a: -a['imp'])
        clusters.append((g, d['imp'], sorted(d['qs'], key=len)))
    clusters.sort(key=lambda x: -(sum(a['imp'] for a in x[0])))

    L = ["# 🔀 Cannibalization Consolidation Plan — REVIEW FIRST (no changes made)", "",
         f"*{len(clusters)} clusters where ≥2 of our live articles COMPETE for the same SG queries "
         f"(each ≥{MIN_Q_IMP} imp on a shared query — query co-competition, which catches dupes that "
         "differently-worded titles hide). WINNER (keep) = most SG clicks → imp → best avg pos. LOSERS → "
         "301 to winner AFTER merging any unique content append-only. A loser with real clicks is "
         "HIGHER-RISK (🔴) — merge content first. Nothing is redirected until Owner approves. Ranked by "
         "contested impressions.*", ""]
    total_contested = 0
    for n, (g, cimp, qs) in enumerate(clusters, 1):
        win = g[0]; losers = g[1:]
        loser_clicks = sum(a['clicks'] for a in losers)
        total_contested += sum(a['imp'] for a in losers)
        risk = "🔴 HIGH (loser has clicks — merge content first)" if loser_clicks > 0 else "🟢 low (losers ~dead)"
        L.append(f"## Cluster #{n} — {cimp} contested imp | risk {risk}")
        L.append(f"- **Contested queries** ({len(qs)}): {', '.join(qs[:5])}")
        L.append(f"- ✅ **KEEP (winner)**: [{win['clicks']}clk/{win['imp']}imp/pos{win['pos']:.0f}] {win['title'][:66]}")
        L.append(f"    - `{win['handle']}` (id {win['id']})")
        for lo in losers:
            L.append(f"- ↪️ **301 → winner**: [{lo['clicks']}clk/{lo['imp']}imp/pos{lo['pos']:.0f}] {lo['title'][:66]}")
            L.append(f"    - `{lo['handle']}` (id {lo['id']})")
        L.append("")
    L.insert(2, f"**Total SG impressions on to-be-redirected losers: {total_contested}.** "
                "Recovering even part of this onto the winners is the upside.\n")
    open(f"{ROOT}/consolidation-plan.md", "w").write("\n".join(L))
    print(f"consolidation plan: {len(clusters)} clusters, {total_contested} imp on losers -> consolidation-plan.md")
    for n, (g, cimp, qs) in enumerate(clusters[:15], 1):
        lc = sum(a['clicks'] for a in g[1:])
        print(f"  #{n} {cimp:>5}imp {len(g)}pp loser-clk {lc:>3} | win: {g[0]['title'][:44]}")


if __name__ == '__main__':
    main()

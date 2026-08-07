#!/usr/bin/env python3
"""Find blog pages CANNIBALIZING each other by GSC query-overlap (US, 90d).

Title matching misses intent-level dupes (e.g. the 7-article vitamin-store cluster).
This detects them from behavior: two pages both earning impressions on the same
queries ARE competing, whatever their titles say.

Detection: for each query with >=20 SG imp, pages earning >=20% of that query's
impressions are "contenders". Page-pairs contending on >=2 queries get clustered
(connected components).

Merge policy (--apply):
  - winner = most SG clicks, then impressions
  - AUTO-MERGE a loser only when loser_imp < 10% of winner_imp  → unpublish + 301
    (no content transplant — at <10% there is nothing worth moving; the two proven
    merges to date, meiji + vitamin, transplanted nothing and won)
  - anything bigger is REPORTED for the operator to decide. Frozen IDs never touched.

Usage: find_intent_clusters.py [--apply] [--min-query-imp 20]
Log: backups/<date>/intent_merge_log.json (reversible: republish + delete redirect)
"""
import argparse, collections, datetime, json, os, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gsc_fetcher import get_service

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.expanduser('~/.genseo/shopify_token.json')
BLOGS = {104008483131: 'news'}


def shopify_articles():
    auth = json.load(open(CONFIG_PATH))
    idx = {}
    for blog in BLOGS:
        url = f"https://{auth['shop']}/admin/api/2026-04/blogs/{blog}/articles.json?limit=250&fields=id,handle,title&published_status=published"
        while url:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"X-Shopify-Access-Token": auth['access_token']}))
            for a in json.loads(r.read())['articles']:
                idx[a['handle']] = (blog, a['id'], a['title'])
            url = None
            for p in r.headers.get('Link', '').split(','):
                if 'rel="next"' in p:
                    url = p[p.find('<')+1:p.find('>')]
    return idx, auth


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--min-query-imp', type=int, default=20)
    ap.add_argument('--force-merge', action='append', default=[], metavar='HANDLE',
                    help='full loser handle to merge past the 10%% guardrail (repeatable). '
                         'The winner is still the one the cluster computes — never named here. '
                         'Any handle that does not match a real cluster loser aborts the run.')
    a = ap.parse_args()
    forced, forced_hit = set(a.force_merge), set()

    svc = get_service()
    end = datetime.date.today() - datetime.timedelta(days=2)
    start = end - datetime.timedelta(days=90)
    rows = svc.searchanalytics().query(siteUrl='https://wellnessnest.co/', body={
        'startDate': str(start), 'endDate': str(end), 'dimensions': ['query', 'page'],
        'dimensionFilterGroups': [{'filters': [{'dimension': 'country', 'operator': 'equals', 'expression': 'usa'}]}],
        'rowLimit': 25000}).execute().get('rows', [])

    # per-query page shares (blog pages only) + per-page totals
    qpages = collections.defaultdict(dict)   # query -> {handle: imp}
    ptotals = collections.defaultdict(lambda: [0, 0])  # handle -> [imp, clicks]
    for r in rows:
        url = r['keys'][1].split('#')[0]
        if '/blogs/' not in url:
            continue
        h = url.rstrip('/').split('/')[-1]
        qpages[r['keys'][0]][h] = qpages[r['keys'][0]].get(h, 0) + r['impressions']
        ptotals[h][0] += r['impressions']; ptotals[h][1] += r['clicks']

    # competing pairs: both pages earn >=20% of a >=min-imp query
    pair_queries = collections.defaultdict(set)
    for q, pages in qpages.items():
        tot = sum(pages.values())
        if tot < a.min_query_imp:
            continue
        contenders = [h for h, i in pages.items() if i >= 0.2 * tot]
        for i in range(len(contenders)):
            for j in range(i + 1, len(contenders)):
                pair_queries[tuple(sorted((contenders[i], contenders[j])))].add(q)
    edges = {p: qs for p, qs in pair_queries.items() if len(qs) >= 2}

    # connected components
    adj = collections.defaultdict(set)
    for (x, y) in edges:
        adj[x].add(y); adj[y].add(x)
    seen, clusters = set(), []
    for n in adj:
        if n in seen:
            continue
        comp, stack = [], [n]
        while stack:
            c = stack.pop()
            if c in seen:
                continue
            seen.add(c); comp.append(c)
            stack.extend(adj[c] - seen)
        clusters.append(comp)

    idx, auth = shopify_articles()
    frozen = set()
    ff = os.path.join(BASE, 'frozen_articles.txt')
    if os.path.exists(ff):
        frozen = {l.split('#')[0].strip() for l in open(ff) if l.split('#')[0].strip()}

    # Validate --force-merge handles BEFORE the first write. A truncated or mistyped
    # handle must abort the run — silently merging nothing is the failure mode that
    # already cost us two missed merges on the first sweep.
    all_losers = set()
    for comp in clusters:
        ms = [(h, *ptotals[h]) for h in comp if h in idx]
        if len(ms) < 2:
            continue
        ms.sort(key=lambda m: (-m[2], -m[1]))
        all_losers.update(h for h, _, _ in ms[1:])
    unknown = forced - all_losers
    if unknown:
        print(f"FAIL: --force-merge handles are not cluster losers: {sorted(unknown)}", file=sys.stderr)
        return 1

    log, auto, forced_n, manual = [], 0, 0, 0
    for comp in clusters:
        members = [(h, *ptotals[h]) for h in comp if h in idx]
        if len(members) < 2:
            continue
        members.sort(key=lambda m: (-m[2], -m[1]))  # clicks desc, imp desc
        winner = members[0]
        shared = sorted({q for p, qs in edges.items() if p[0] in comp and p[1] in comp for q in qs})
        print(f"\n■ CLUSTER ({len(members)} pages) — shared queries: {', '.join(shared[:4])}")
        for h, imp, clk in members:
            tag = 'WINNER' if h == winner[0] else ''
            print(f"   {clk:4d} clk {imp:6d} imp  {h[:70]} {tag}")
        for h, imp, clk in members[1:]:
            blog, aid, _ = idx[h]
            if str(aid) in frozen:
                print(f"   → {h[:50]}: FROZEN, skipped"); continue
            is_forced = h in forced
            if is_forced:
                forced_hit.add(h)
            if imp < 0.1 * max(winner[1], 1) or is_forced:
                kind = 'FORCE-MERGE' if is_forced else 'AUTO-MERGE'
                action = kind if a.apply else f'would {kind}'
                print(f"   → {action}: {h[:55]} → {winner[0][:45]}")
                if a.apply:
                    hdr = {"X-Shopify-Access-Token": auth['access_token'], "Content-Type": "application/json"}
                    req = urllib.request.Request(
                        f"https://{auth['shop']}/admin/api/2026-04/blogs/{blog}/articles/{aid}.json",
                        data=json.dumps({"article": {"id": aid, "published": False}}).encode(), method='PUT', headers=hdr)
                    urllib.request.urlopen(req)
                    wblog = idx[winner[0]][0]
                    red = urllib.request.Request(f"https://{auth['shop']}/admin/api/2026-04/redirects.json",
                        data=json.dumps({"redirect": {"path": f"/blogs/{BLOGS[blog]}/{h}",
                                                      "target": f"/blogs/{BLOGS[wblog]}/{winner[0]}"}}).encode(),
                        method='POST', headers=hdr)
                    rid = json.loads(urllib.request.urlopen(red).read())['redirect']['id']
                    log.append({"loser": h, "loser_id": aid, "winner": winner[0], "redirect_id": rid,
                                "loser_stats": [imp, clk], "winner_stats": [winner[1], winner[2]],
                                "forced": is_forced})
                if is_forced:
                    forced_n += 1
                else:
                    auto += 1
            else:
                print(f"   → ⚠ MANUAL DECISION: {h[:55]} has {imp} imp ({100*imp/max(winner[1],1):.0f}% of winner)")
                manual += 1
    if a.apply and log:
        d = os.path.join(BASE, 'backups', datetime.date.today().isoformat())
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'intent_merge_log.json'), 'a') as f:
            json.dump(log, f, indent=2)
    print(f"\n{'applied' if a.apply else 'dry-run'}: {auto} auto-merge, "
          f"{forced_n} FORCED past the guardrail, {manual} need manual decision")
    missed = forced - forced_hit
    if missed:
        print(f"FAIL: --force-merge handles never fired (frozen?): {sorted(missed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

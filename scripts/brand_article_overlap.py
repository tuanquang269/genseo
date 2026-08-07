#!/usr/bin/env python3
"""Per-brand view of which articles compete, so a human can decide what merges into what.

`find_intent_clusters.py` needs a page to hold >=20% of a >=20-impression query on >=2 shared
queries. That is deliberately strict and it now reports zero auto-merges — the free wins are gone.
But the brand-query measurement found 244 SG brand queries with 2+ articles ranking, so the
cannibalisation is real below that threshold. This lists it per brand instead of deciding for you.

For each brand: every blog article ranking on a query naming that brand, with the commercial pages
(collection/product) it is competing against, so the merge target is visible rather than inferred.

Usage:
    python3 scripts/brand_article_overlap.py MYPROTEIN "Optimum Nutrition" PVL Mutant
"""
import collections
import datetime
import json
import os
import pathlib
import re
import sys
import urllib.request

sys.path.append(os.path.expanduser("/Users/kevinkreative/genseo/scripts/"))
from gsc_fetcher import get_service  # noqa: E402

SITE = "https://wellnessnest.co/"
CONFIG = os.path.expanduser("~/.genseo/shopify_token.json")
BLOGS = {104008483131: "news"}
BASE = pathlib.Path(__file__).resolve().parent.parent


def published_handles():
    """GSC keeps reporting URLs for weeks after we unpublish or 301 them.

    14.1% of blog impressions in the last 28 days point at articles that are already gone —
    including the three year-suffixed PVL duplicates, which an earlier sweep had merged before I
    'discovered' them. Anything not in this set is not a merge candidate, it is already done.
    """
    auth = json.load(open(CONFIG))
    out = set()
    for blog in BLOGS:
        url = (f"https://{auth['shop']}/admin/api/2026-04/blogs/{blog}/articles.json"
               f"?limit=250&fields=id,handle&published_status=published")
        while url:
            r = urllib.request.urlopen(urllib.request.Request(
                url, headers={"X-Shopify-Access-Token": auth["access_token"]}), timeout=60)
            for a in json.loads(r.read())["articles"]:
                out.add(a["handle"])
            url = None
            for part in r.headers.get("Link", "").split(","):
                if 'rel="next"' in part:
                    url = part[part.find("<") + 1:part.find(">")]
    return out


def word_pat(name):
    ts = [re.escape(t) for t in re.split(r"[^a-z0-9]+", name.lower()) if t]
    return re.compile(r"\b" + r"\W+".join(ts) + r"\b")


def selftest():
    assert not word_pat("LAC").search("meal replacement")
    assert word_pat("Optimum Nutrition").search("optimum nutrition gold standard")
    assert not word_pat("Mutant").search("mutants")          # \b stops the plural
    assert word_pat("PVL").search("is pvl iso gold good")


def short(url):
    return url.replace("https://wellnessnest.co", "")


def main(brands):
    selftest()
    live = published_handles()
    print(f"published articles: {len(live)}")
    svc = get_service()
    end = datetime.date.today() - datetime.timedelta(days=2)
    start = end - datetime.timedelta(days=90)
    rows, sr = [], 0
    while True:
        body = {"startDate": str(start), "endDate": str(end), "dimensions": ["query", "page"],
                "rowLimit": 25000, "startRow": sr,
                "dimensionFilterGroups": [{"filters": [
                    {"dimension": "country", "operator": "equals", "expression": "{{COUNTRY_CODE}}"}]}]}
        got = svc.searchanalytics().query(siteUrl=SITE, body=body).execute().get("rows", [])
        rows += got
        if len(got) < 25000:
            break
        sr += len(got)

    # fold anchor-fragment rows or one article looks like several
    folded = collections.defaultdict(lambda: [0, 0, []])
    for r in rows:
        q, url = r["keys"]
        k = (q, url.split("#")[0].split("?")[0])
        folded[k][0] += r["impressions"]
        folded[k][1] += r["clicks"]
        folded[k][2].append(r["position"])
    print(f"SG query x page, {start}..{end}: {len(rows)} raw -> {len(folded)} folded\n")

    report = {}
    for brand in brands:
        p = word_pat(brand)
        arts = collections.defaultdict(lambda: [0, 0, set(), []])
        comm = collections.defaultdict(lambda: [0, 0, []])
        for (q, url), (imp, clk, poss) in folded.items():
            if not p.search(q.lower()):
                continue
            if "/blogs/" in url:
                if url.rstrip("/").split("/")[-1] not in live:
                    continue          # already unpublished or 301'd; not a merge candidate
                a = arts[url]
                a[0] += imp
                a[1] += clk
                a[2].add(q)
                a[3] += poss
            elif "/collections/" in url or "/products/" in url:
                c = comm[url]
                c[0] += imp
                c[1] += clk
                c[2] += poss
        if not arts:
            continue
        ranked = sorted(arts.items(), key=lambda kv: -kv[1][0])
        tot_i = sum(v[0] for v in arts.values())
        tot_c = sum(v[1] for v in arts.values())
        print("=" * 100)
        print(f"{brand}  —  {len(arts)} articles rank on its SG queries: "
              f"{tot_i} imp / {tot_c} clicks")
        print(f"{'imp':>6} {'clk':>4} {'CTR':>6} {'pos':>5} {'qs':>4}  article")
        for url, (imp, clk, qs, poss) in ranked:
            print(f"{imp:6.0f} {clk:4.0f} {clk/max(imp,1):6.2%} "
                  f"{sum(poss)/len(poss):5.1f} {len(qs):4d}  {short(url)[:74]}")
        keep = ranked[0]
        # Deliberately NOT proposing "merge the other 18". Most of the tail covers a DIFFERENT
        # product from the same brand (pvl-watertight-review, pvl-eaa-bcaa-complete-review) and
        # folding those into the whey guide would destroy real coverage. Merge candidates are the
        # ones sharing queries with the leader — the `qs` column and the shared-query list below.
        overlap = [(u, v) for u, v in ranked[1:] if v[2] & keep[1][2]]
        print(f"\n   biggest       : {short(keep[0])[:76]}")
        print(f"   shares queries with it: {len(overlap)} of {len(ranked)-1} other articles"
              f"  ({sum(v[0] for _, v in overlap)} imp / {sum(v[1] for _, v in overlap)} clk)")
        for u, v in overlap[:8]:
            common = sorted(v[2] & keep[1][2])
            print(f"      {v[0]:5.0f} imp {v[1]:3.0f} clk  {short(u).split('/')[-1][:52]:54} "
                  f"shared: {', '.join(common[:3])[:40]}")
        if comm:
            print("\n   commercial pages competing for the same brand queries "
                  "(these should win them):")
            for url, (imp, clk, poss) in sorted(comm.items(), key=lambda kv: -kv[1][0])[:6]:
                print(f"   {imp:6.0f} imp {clk:4.0f} clk pos {sum(poss)/len(poss):5.1f}  "
                      f"{short(url)[:66]}")
        else:
            print("\n   ⚠ NO collection or product page ranks on this brand's queries at all.")
        print()
        report[brand] = {
            "articles": [{"url": u, "imp": v[0], "clicks": v[1],
                          "avg_pos": round(sum(v[3])/len(v[3]), 1),
                          "queries": sorted(v[2])} for u, v in ranked],
            "biggest": keep[0],
            "shares_queries_with_biggest": [
                {"url": u, "imp": v[0], "clicks": v[1],
                 "shared_queries": sorted(v[2] & keep[1][2])} for u, v in overlap],
            "commercial": [{"url": u, "imp": v[0], "clicks": v[1],
                            "avg_pos": round(sum(v[2])/len(v[2]), 1)}
                           for u, v in sorted(comm.items(), key=lambda kv: -kv[1][0])],
        }

    dst = BASE / "backups" / datetime.date.today().isoformat()
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "brand_article_overlap.json").write_text(json.dumps(report, indent=1))
    print(f"saved: {dst / 'brand_article_overlap.json'}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))

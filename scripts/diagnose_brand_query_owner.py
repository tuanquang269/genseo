#!/usr/bin/env python3
"""For SG brand-name queries, which page type does Google actually rank?

Two jobs, one GSC pull.

1. Redo the brand-collection gap honestly. The first pass matched a vendor string against a
   collection title by exact normalised equality, which reported "PVL has no collection page" when
   `pvl-nutrition` exists with 240 products, and the same for `Dymatize` vs `dymatize-nutrition`.
   A brand is covered if its tokens appear in a collection handle/title, or in a TITLE/VENDOR
   ruleset condition — that last one matters because `pvl-nutrition` is built on
   `TITLE CONTAINS 'PVL'`, not on the vendor field at all.

2. Measure whether blog articles are taking commercial brand queries off the collection and product
   pages that could convert them. Observed on PVL: `pvl iso gold` ranks a guide article, and five
   different article URLs compete for `pvl iso gold review`.

Usage:
    python3 scripts/diagnose_brand_query_owner.py
    python3 scripts/diagnose_brand_query_owner.py --brand PVL      # drill into one brand
"""
import argparse
import collections
import datetime
import json
import os
import pathlib
import re
import sys
import time
import urllib.request

sys.path.append(os.path.expanduser("~/genseo/scripts/"))
from gsc_fetcher import get_service  # noqa: E402

CONFIG = os.path.expanduser("~/.genseo/shopify_token.json")
SITE = "https://yourdomain.com/"
API = "2026-04"
BASE = pathlib.Path(__file__).resolve().parent.parent

with open(CONFIG) as fh:
    CFG = json.load(fh)
SHOP, TOKEN = CFG["shop"], CFG["access_token"]
HDR = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}

PRODUCTS = """query($c:String){products(first:200,after:$c,query:"status:active"){
 pageInfo{hasNextPage endCursor} nodes{vendor onlineStoreUrl}}}"""
COLLECTIONS = """query($c:String){collections(first:200,after:$c){
 pageInfo{hasNextPage endCursor}
 nodes{handle title ruleSet{rules{column relation condition}}}}}"""


def gql(query, variables):
    req = urllib.request.Request(f"https://{SHOP}/admin/api/{API}/graphql.json",
                                 data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers=HDR)
    out = json.loads(urllib.request.urlopen(req, timeout=90).read())
    if "errors" in out:
        raise RuntimeError(out["errors"])
    return out["data"]


def page(query, root):
    cur = None
    while True:
        d = gql(query, {"c": cur})[root]
        yield from d["nodes"]
        if not d["pageInfo"]["hasNextPage"]:
            break
        cur = d["pageInfo"]["endCursor"]
        time.sleep(0.3)


def tokens(s):
    return [t for t in re.split(r"[^a-z0-9]+", (s or "").lower()) if t]


def word_pat(name):
    """Whole-word, in-order match. Plain substring credits 'LAC' with 'meal replacement'."""
    ts = [re.escape(t) for t in tokens(name)]
    return re.compile(r"\b" + r"\W+".join(ts) + r"\b") if ts else None


def selftest():
    assert not word_pat("LAC").search("meal replacement {{market}}")
    assert word_pat("LAC").search("lac taut collagen")
    assert not word_pat("ABE").search("rosabella beetroot")
    # the bug this script exists to fix: brand is a PREFIX of the collection name
    assert covered("PVL", [{"handle": "pvl-nutrition", "title": "PVL NUTRITION", "ruleSet": None}])
    assert covered("Dymatize", [{"handle": "dymatize-nutrition", "title": "Dymatize Nutrition",
                                 "ruleSet": None}])
    # and coverage via a title rule, since pvl-nutrition is built on TITLE CONTAINS 'PVL'
    assert covered("PVL", [{"handle": "x", "title": "Y", "ruleSet": {"rules": [
        {"column": "TITLE", "relation": "CONTAINS", "condition": "PVL"}]}}])
    assert not covered("Nocco", [{"handle": "pvl-nutrition", "title": "PVL NUTRITION",
                                  "ruleSet": None}])
    print("selftest OK")


def covered(brand, cols):
    p = word_pat(brand)
    if not p:
        return False
    for c in cols:
        for hay in (c["handle"].replace("-", " "), c["title"]):
            if p.search(hay.lower()):
                return True
        rs = c.get("ruleSet")
        for r in (rs or {}).get("rules", []):
            if r["column"] in ("TITLE", "VENDOR") and p.search((r["condition"] or "").lower()):
                return True
    return False


def kind(url):
    for k in ("/products/", "/collections/", "/blogs/", "/pages/"):
        if k in url:
            return k.strip("/")
    return "home"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    selftest()

    vendors = collections.Counter(p["vendor"] for p in page(PRODUCTS, "products")
                                 if p["onlineStoreUrl"])
    cols = list(page(COLLECTIONS, "collections"))

    svc = get_service()
    end = datetime.date.today() - datetime.timedelta(days=2)
    start = end - datetime.timedelta(days=28)
    rows, sr = [], 0
    while True:
        body = {"startDate": start.isoformat(), "endDate": end.isoformat(),
                "dimensions": ["query", "page"], "rowLimit": 25000, "startRow": sr,
                "dimensionFilterGroups": [{"filters": [
                    {"dimension": "country", "operator": "equals", "expression": "{{COUNTRY_CODE}}"}]}]}
        got = svc.searchanalytics().query(siteUrl=SITE, body=body).execute().get("rows", [])
        rows += got
        if len(got) < 25000:
            break
        sr += len(got)
    raw_n = len(rows)

    # Fold "jump to section" anchor rows into their page. They are always blog URLs and always
    # carry 0 clicks, so leaving them in both inflates the blog share of impressions AND makes
    # one article look like a dozen competing ones. This bit me on the first run.
    folded = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        q, url = r["keys"]
        k = (q, url.split("#")[0].split("?")[0])
        folded[k][0] += r["impressions"]
        folded[k][1] += r["clicks"]
    rows = [{"keys": list(k), "impressions": v[0], "clicks": v[1]} for k, v in folded.items()]
    frag = raw_n - len(rows)
    print(f"SG query x page rows {start}..{end}: {raw_n} raw -> {len(rows)} after folding "
          f"{frag} anchor-fragment/param rows\n")

    gap = [(v, n) for v, n in vendors.most_common() if not covered(v, cols)]
    print(f"brands carried: {len(vendors)} | collections: {len(cols)} | "
          f"NO collection page: {len(gap)} (was 67 before the prefix fix)\n")

    brands = [a.brand] if a.brand else [v for v, _ in gap]
    out = []
    for brand in brands:
        p = word_pat(brand)
        hits = [r for r in rows if p and p.search(r["keys"][0].lower())]
        if not hits:
            continue
        imp = sum(h["impressions"] for h in hits)
        by = collections.defaultdict(lambda: [0, 0, set()])
        for h in hits:
            b = by[kind(h["keys"][1])]
            b[0] += h["impressions"]
            b[1] += h["clicks"]
            b[2].add(h["keys"][1])
        out.append((imp, brand, vendors.get(brand, 0), dict(by)))
    out.sort(reverse=True)

    hdr = f"{'imp':>5} {'clk':>4} {'prods':>5}  brand"
    print("UNCOVERED brands with measured SG demand:" if not a.brand else f"brand: {a.brand}")
    print(hdr + "   " + "  ".join(f"{k}:imp/clk/urls" for k in
                                  ("blogs", "collections", "products")))
    for imp, brand, nprod, by in out:
        clk = sum(v[1] for v in by.values())
        cells = "  ".join(
            f"{by.get(k, [0, 0, set()])[0]:5.0f}/{by.get(k, [0, 0, set()])[1]:.0f}/"
            f"{len(by.get(k, [0, 0, set()])[2]):d}" for k in ("blogs", "collections", "products"))
        print(f"{imp:5.0f} {clk:4.0f} {nprod:5d}  {brand:22} {cells}")

    # Who owns brand queries overall — the cannibalisation question
    covered_brands = [v for v in vendors if covered(v, cols)]
    agg = collections.defaultdict(lambda: [0, 0])
    per_query_urls = collections.Counter()
    for brand in covered_brands:
        p = word_pat(brand)
        for r in rows:
            q, url = r["keys"]
            if p and p.search(q.lower()):
                agg[kind(url)][0] += r["impressions"]
                agg[kind(url)][1] += r["clicks"]
                if kind(url) == "blogs":
                    per_query_urls[(brand, q)] += 1
    ti = sum(v[0] for v in agg.values()) or 1
    tc = sum(v[1] for v in agg.values()) or 1
    print(f"\nSG queries naming a brand we DO have a collection for "
          f"({len(covered_brands)} brands) — who Google ranks:")
    print(f"{'page type':13} {'imp':>7} {'%imp':>6} {'clk':>5} {'%clk':>6} {'CTR':>7}")
    for k, (i, c) in sorted(agg.items(), key=lambda kv: -kv[1][0]):
        print(f"{k:13} {i:7.0f} {i/ti:6.1%} {c:5.0f} {c/tc:6.1%} {c/max(i,1):7.2%}")

    multi = [(n, b, q) for (b, q), n in per_query_urls.items() if n >= 2]
    multi.sort(reverse=True)
    print(f"\nbrand queries where 2+ distinct ARTICLES compete (fragments folded): {len(multi)}"
          f"  |  3+: {sum(1 for n, _, _ in multi if n >= 3)}")
    for n, b, q in multi[:20]:
        print(f"   {n:2d} articles   {b:20} {q[:44]}")

    dst = BASE / "backups" / datetime.date.today().isoformat()
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "brand_query_owner.json").write_text(json.dumps({
        "uncovered": [{"brand": b, "products": n, "imp": i,
                       "by_type": {k: v[:2] + [sorted(v[2])] for k, v in by.items()}}
                      for i, b, n, by in out],
        "owner_by_type": {k: v for k, v in agg.items()},
        "multi_article_queries": [{"urls": n, "brand": b, "query": q} for n, b, q in multi],
    }, indent=1))
    print(f"\nsaved: {dst / 'brand_query_owner.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

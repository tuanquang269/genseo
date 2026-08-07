#!/usr/bin/env python3
"""Why do ~569 of 952 online products take zero SG impressions?

ACTION-PLAN 2.3 proposes writing unique copy for the top 100 of them. That costs
real human days, so prove the diagnosis first: if the pages are not indexed, copy
changes nothing, and if the earning and zero cohorts are structurally identical,
copy is not the differentiator either.

Compares the two cohorts on everything cheap to measure, then spends URL-Inspection
quota only on a sample of the zero cohort.

Usage:
    python3 scripts/diagnose_zero_impression_products.py            # cohort compare, no quota
    python3 scripts/diagnose_zero_impression_products.py --inspect 60
"""
import argparse
import collections
import datetime
import json
import os
import pathlib
import re
import statistics
import sys
import time
import urllib.request

sys.path.append(os.path.expanduser("/Users/kevinkreative/genseo/scripts/"))
from gsc_fetcher import get_service  # noqa: E402

CONFIG = os.path.expanduser("~/.genseo/shopify_token.json")
SITE = "https://wellnessnest.co/"
API = "2026-04"
BASE = pathlib.Path(__file__).resolve().parent.parent

with open(CONFIG) as fh:
    CFG = json.load(fh)
SHOP, TOKEN = CFG["shop"], CFG["access_token"]
HDR = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}

FETCH = """query($cursor:String){products(first:100,after:$cursor,query:"status:active"){
 pageInfo{hasNextPage endCursor}
 nodes{id handle title vendor onlineStoreUrl publishedAt descriptionHtml
   collections(first:20){nodes{handle}}
   media(first:1){nodes{id}}
   variants(first:50){nodes{sku barcode price}}}}}"""


def gql(query, variables):
    req = urllib.request.Request(f"https://{SHOP}/admin/api/{API}/graphql.json",
                                 data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers=HDR)
    out = json.loads(urllib.request.urlopen(req, timeout=90).read())
    if "errors" in out:
        raise RuntimeError(out["errors"])
    return out["data"]


def load_products():
    cur, out = None, []
    while True:
        d = gql(FETCH, {"cursor": cur})["products"]
        out += [p for p in d["nodes"] if p["onlineStoreUrl"]]
        if not d["pageInfo"]["hasNextPage"]:
            break
        cur = d["pageInfo"]["endCursor"]
        time.sleep(0.3)
    return out


def gsc_product_rows(svc, days=28):
    """SG-only page rows for /products/. Paginate — the default 1k cap truncates."""
    end = datetime.date.today() - datetime.timedelta(days=2)
    start = end - datetime.timedelta(days=days)
    rows, start_row = {}, 0
    while True:
        body = {
            "startDate": start.isoformat(), "endDate": end.isoformat(),
            "dimensions": ["page"], "rowLimit": 25000, "startRow": start_row,
            "dimensionFilterGroups": [{"filters": [
                {"dimension": "country", "operator": "equals", "expression": "{{COUNTRY_CODE}}"},
                {"dimension": "page", "operator": "contains", "expression": "/products/"}]}],
        }
        r = svc.searchanalytics().query(siteUrl=SITE, body=body).execute()
        got = r.get("rows", [])
        for row in got:
            # anchor-fragment rows can never be click-attributed — fold them into the page
            url = row["keys"][0].split("#")[0].split("?")[0]
            agg = rows.setdefault(url, [0, 0])
            agg[0] += row["impressions"]
            agg[1] += row["clicks"]
        if len(got) < 25000:
            break
        start_row += len(got)
    return rows, start, end


def prose_len(html_body):
    """Visible word count, excluding the internal-link boxes and any markup."""
    body = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", html_body or "", flags=re.S | re.I)
    body = re.sub(r"<a\b[^>]*>.*?</a>", " ", body, flags=re.S | re.I)
    return len(re.sub(r"<[^>]+>", " ", body).split())


def band(xs):
    if not xs:
        return "n/a"
    xs = sorted(xs)
    return (f"median {statistics.median(xs):6.0f} | mean {statistics.mean(xs):6.0f} | "
            f"p10 {xs[len(xs)//10]:5.0f} | p90 {xs[min(len(xs)-1, 9*len(xs)//10)]:6.0f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inspect", type=int, default=0,
                    help="sample size for URL Inspection (quota: 2000/day). 0 = skip.")
    a = ap.parse_args()

    svc = get_service()
    prods = load_products()
    gsc, start, end = gsc_product_rows(svc)
    print(f"online products: {len(prods)} | GSC SG product rows {start}..{end}: {len(gsc)}\n")

    zero, earning = [], []
    for p in prods:
        url = p["onlineStoreUrl"].split("?")[0]
        imp, clk = gsc.get(url, (0, 0))
        vs = p["variants"]["nodes"]
        rec = {
            "handle": p["handle"], "url": url, "title": p["title"], "vendor": p["vendor"],
            "imp": imp, "clk": clk,
            "words": prose_len(p["descriptionHtml"]),
            "collections": len(p["collections"]["nodes"]),
            "variants": len(vs),
            "has_image": bool(p["media"]["nodes"]),
            "has_barcode": any((v.get("barcode") or "").strip() for v in vs),
            "published": (p["publishedAt"] or "")[:10],
            "title_len": len(p["title"]),
        }
        (earning if imp > 0 else zero).append(rec)

    print(f"ZERO SG impressions : {len(zero)}")
    print(f"earning impressions : {len(earning)}\n")

    for name, key in (("description words", "words"), ("collections", "collections"),
                      ("variants", "variants"), ("title length", "title_len")):
        print(f"{name:20} zero    {band([r[key] for r in zero])}")
        print(f"{'':20} earning {band([r[key] for r in earning])}")

    for name, key in (("has image", "has_image"), ("has barcode", "has_barcode")):
        z = sum(r[key] for r in zero) / max(len(zero), 1)
        e = sum(r[key] for r in earning) / max(len(earning), 1)
        print(f"{name:20} zero {z:5.1%}   earning {e:5.1%}")

    print("\nno description at all (<20 words):"
          f" zero {sum(r['words'] < 20 for r in zero)}/{len(zero)}"
          f" | earning {sum(r['words'] < 20 for r in earning)}/{len(earning)}")
    print("in 0 collections:"
          f" zero {sum(r['collections'] == 0 for r in zero)}"
          f" | earning {sum(r['collections'] == 0 for r in earning)}")

    vz = collections.Counter(r["vendor"] for r in zero)
    ve = collections.Counter(r["vendor"] for r in earning)
    print("\ntop vendors in the ZERO cohort (zero / earning):")
    for v, n in vz.most_common(12):
        print(f"   {v[:30]:32} {n:4d} / {ve.get(v, 0):4d}")

    out = BASE / "backups" / datetime.date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)

    if a.inspect:
        # widest-spread sample: not just the first N, which would be alphabetical by cursor
        step = max(1, len(zero) // a.inspect)
        sample = zero[::step][:a.inspect]
        print(f"\nURL Inspection on {len(sample)} of the zero cohort "
              f"(every {step}th, spread across the list):")
        states = collections.Counter()
        detail = []
        for i, r in enumerate(sample, 1):
            try:
                res = svc.urlInspection().index().inspect(body={
                    "inspectionUrl": r["url"], "siteUrl": SITE}).execute()["inspectionResult"]
            except Exception as exc:
                states[f"API ERROR {type(exc).__name__}"] += 1
                continue
            idx = res.get("indexStatusResult", {})
            cov = idx.get("coverageState", "?")
            states[cov] += 1
            detail.append({"handle": r["handle"], "coverage": cov,
                           "verdict": idx.get("verdict"),
                           "canonical_matches": idx.get("googleCanonical") == idx.get("userCanonical"),
                           "googleCanonical": idx.get("googleCanonical"),
                           "crawledAs": idx.get("crawledAs"),
                           "lastCrawl": (idx.get("lastCrawlTime") or "")[:10],
                           "robots": idx.get("robotsTxtState"),
                           "richResults": bool(res.get("richResultsResult"))})
            if i % 20 == 0:
                print(f"   {i}/{len(sample)}")
            time.sleep(0.2)
        print()
        for s, n in states.most_common():
            print(f"   {n:4d}  {s}")
        wrong_canon = [d for d in detail if d["canonical_matches"] is False]
        print(f"\n   canonical mismatch: {len(wrong_canon)}/{len(detail)}")
        for d in wrong_canon[:5]:
            print(f"      {d['handle'][:45]:47} -> {d['googleCanonical']}")
        nostruct = sum(not d["richResults"] for d in detail)
        print(f"   no rich-result type detected: {nostruct}/{len(detail)}")
        (out / "zero_impression_inspection.json").write_text(json.dumps(detail, indent=1))
        print(f"   detail: {out / 'zero_impression_inspection.json'}")

    (out / "zero_impression_products.json").write_text(json.dumps(
        {"zero": zero, "earning": earning}, indent=1))
    print(f"\ncohorts: {out / 'zero_impression_products.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

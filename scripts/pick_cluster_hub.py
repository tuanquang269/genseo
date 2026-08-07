#!/usr/bin/env python3
"""Pick the hub for a cannibalising article cluster, on 6-month AND 3-month SG data.

A 28-day window cannot tell a page that is dying from one that never worked, and picking the hub off
the wrong one is expensive: the losers get 301'd into it. So every candidate is measured over both
windows and the trend between them is shown explicitly.

The cluster is discovered from behaviour, not from handles: any still-published article that earns SG
impressions on a query matching --query-pattern. Handle-guessing misses articles whose title never
says the product name, and includes ones that only mention it in passing.

Filters that are not optional here, each of which produced a wrong table earlier in this project:
  * fold `#anchor` rows into their page, or one article looks like several
  * drop articles already unpublished or 301'd — 14% of blog impressions are for dead URLs
  * whole-word query matching, so "LAC" does not match "meal replacement"

Usage:
    python3 scripts/pick_cluster_hub.py --query-pattern "impact whey" --brand MYPROTEIN
"""
import argparse
import collections
import datetime
import json
import os
import pathlib
import re
import sys
import urllib.request

sys.path.append(os.path.expanduser("~/genseo/scripts/"))
from gsc_fetcher import get_service  # noqa: E402

SITE = "https://yourdomain.com/"
CONFIG = os.path.expanduser("~/.genseo/shopify_token.json")
BLOGS = {100000000001: "nutrition", 100000000002: "training"}
BASE = pathlib.Path(__file__).resolve().parent.parent
AUTH = json.load(open(CONFIG))


def shopify_articles():
    """handle -> (blog, id, title, prose word count). Published only."""
    out = {}
    for blog in BLOGS:
        url = (f"https://{AUTH['shop']}/admin/api/2026-04/blogs/{blog}/articles.json"
               f"?limit=250&fields=id,handle,title,body_html,published_at&published_status=published")
        while url:
            r = urllib.request.urlopen(urllib.request.Request(
                url, headers={"X-Shopify-Access-Token": AUTH["access_token"]}), timeout=90)
            for a in json.loads(r.read())["articles"]:
                body = a.get("body_html") or ""
                body = re.sub(r"<a\b[^>]*>.*?</a>", " ", body, flags=re.S | re.I)
                out[a["handle"]] = (blog, a["id"], a["title"],
                                    len(re.sub(r"<[^>]+>", " ", body).split()))
            url = None
            for part in r.headers.get("Link", "").split(","):
                if 'rel="next"' in part:
                    url = part[part.find("<") + 1:part.find(">")]
    return out


def fetch(svc, days):
    end = datetime.date.today() - datetime.timedelta(days=2)
    start = end - datetime.timedelta(days=days)
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
    return rows, start, end


def word_pat(s):
    ts = [re.escape(t) for t in re.split(r"[^a-z0-9]+", s.lower()) if t]
    return re.compile(r"\b" + r"\W+".join(ts) + r"\b")


def selftest():
    assert not word_pat("LAC").search("meal replacement")
    assert word_pat("impact whey").search("myprotein impact whey isolate review")
    assert not word_pat("impact whey").search("impactful wheyless blend")
    print("selftest OK")


def collect(rows, live, qpat, bpat):
    """handle -> [imp, clicks, weighted position numerator, query set]"""
    agg = collections.defaultdict(lambda: [0, 0, 0.0, set()])
    for r in rows:
        q, url = r["keys"]
        if "/blogs/" not in url:
            continue
        if not qpat.search(q.lower()):
            continue
        if bpat and not bpat.search(q.lower()):
            continue
        h = url.split("#")[0].split("?")[0].rstrip("/").split("/")[-1]
        if h not in live:
            continue
        a = agg[h]
        a[0] += r["impressions"]
        a[1] += r["clicks"]
        a[2] += r["position"] * r["impressions"]
        a[3].add(q)
    return agg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query-pattern", required=True,
                    help='e.g. "impact whey" — matched whole-word against the GSC query')
    ap.add_argument("--brand", help="additional whole-word term the query must contain")
    a = ap.parse_args()
    selftest()

    live = shopify_articles()
    svc = get_service()
    qpat, bpat = word_pat(a.query_pattern), word_pat(a.brand) if a.brand else None

    windows = {}
    for label, days in (("6mo", 183), ("3mo", 91)):
        rows, start, end = fetch(svc, days)
        windows[label] = collect(rows, live, qpat, bpat)
        print(f"{label}: {start}..{end}, {len(rows)} SG query x page rows")

    six, three = windows["6mo"], windows["3mo"]
    handles = sorted(set(six) | set(three), key=lambda h: -six.get(h, [0])[0])
    if not handles:
        print("no live articles match — check the pattern")
        return 1

    print(f"\n{len(handles)} still-published articles rank on SG queries containing "
          f"{a.query_pattern!r}" + (f" AND {a.brand!r}" if a.brand else "") + "\n")
    hdr = (f"{'6mo imp':>8} {'clk':>4} {'pos':>5} | {'3mo imp':>8} {'clk':>4} {'pos':>5} | "
           f"{'3mo share':>9} {'words':>6} {'qs':>4}  article")
    print(hdr)
    print("-" * len(hdr))
    rowdata = []
    for h in handles:
        s = six.get(h, [0, 0, 0.0, set()])
        t = three.get(h, [0, 0, 0.0, set()])
        spos = s[2] / s[0] if s[0] else 0
        tpos = t[2] / t[0] if t[0] else 0
        # what fraction of this page's 6-month impressions landed in the recent 3 months.
        # >0.5 means it is holding or growing; <0.35 means it is fading.
        share = t[0] / s[0] if s[0] else 0
        rowdata.append((h, s, t, spos, tpos, share))
        print(f"{s[0]:8.0f} {s[1]:4.0f} {spos:5.1f} | {t[0]:8.0f} {t[1]:4.0f} {tpos:5.1f} | "
              f"{share:8.0%} {live[h][3]:6d} {len(s[3] | t[3]):4d}  {h[:52]}")

    tot6 = sum(r[1][0] for r in rowdata)
    tot3 = sum(r[2][0] for r in rowdata)
    c6 = sum(r[1][1] for r in rowdata)
    c3 = sum(r[2][1] for r in rowdata)
    print(f"\ncluster totals: 6mo {tot6:.0f} imp / {c6:.0f} clk"
          f"  |  3mo {tot3:.0f} imp / {c3:.0f} clk"
          f"  |  recent share {tot3/max(tot6,1):.0%}")

    print("\nranked by clicks over BOTH windows (the only metric that survives a rank change):")
    for h, s, t, sp, tp, sh in sorted(rowdata, key=lambda r: -(r[1][1] + r[2][1]))[:6]:
        print(f"   {s[1]+t[1]:4.0f} clk total ({s[1]:.0f} in 6mo, {t[1]:.0f} in 3mo)  "
              f"{live[h][3]:5d} words  {h[:56]}")
        print(f"        {live[h][2][:88]}")

    out = BASE / "backups" / datetime.date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    dst = out / f"cluster_{re.sub(r'[^a-z0-9]+', '_', a.query_pattern.lower())}.json"
    dst.write_text(json.dumps([{
        "handle": h, "title": live[h][2], "words": live[h][3],
        "imp_6mo": s[0], "clicks_6mo": s[1], "pos_6mo": round(sp, 1),
        "imp_3mo": t[0], "clicks_3mo": t[1], "pos_3mo": round(tp, 1),
        "recent_share": round(sh, 3), "queries": sorted(s[3] | t[3]),
    } for h, s, t, sp, tp, sh in rowdata], indent=1))
    print(f"\nsaved: {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Build a pillar and spoke map for the Wellness Nest blog.

Reads existing_articles.json, ALL_ARTICLES.csv, PUBLISHED_ARTICLES_TRACKER.csv,
and the latest vault GSC export. Optional wellness-intake state adds fresh gaps.

  python3 scripts/build_cluster_map.py
  python3 scripts/build_cluster_map.py --csv tests/fixtures/geo_clusters/articles.csv --gsc tests/fixtures/geo_clusters/gsc.csv --out-json /tmp/map.json --out-md /tmp/map.md --no-vault

Writes state/cluster_map.json (gitignored) and docs/CLUSTER_MAP.md.
A vault copy goes to 90-sources/cluster-maps/ when the vault is present.
No Shopify writes.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wn_clusters as wc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT = os.path.expanduser(os.environ.get("GENSEO_VAULT", "~/PATI/LLM-Wiki"))
GENSEO_MAIN = os.path.expanduser("~/genseo")


def _first(*paths):
    for path in paths:
        if path and os.path.isfile(path):
            return path
    return ""


def latest_gsc(vault):
    folder = os.path.join(vault, "90-sources", "gsc-daily")
    files = sorted(glob.glob(os.path.join(folder, "*-gsc-raw.csv")))
    return files[-1] if files else ""


def load_intake(path):
    if not path or not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    items = []
    for row in (data.get("items") or {}).values():
        items.append({
            "title": row.get("title") or "",
            "cluster": row.get("cluster") or wc.assign_cluster(row.get("title") or ""),
            "url": row.get("url") or "",
            "source": row.get("kind") or "intake",
        })
    return items


def maybe_shopify_titles():
    """Read published blog article titles. Never requests products, pages, or themes."""
    path = os.path.expanduser(os.environ.get("GENSEO_CONFIG", "~/.genseo/shopify_token.json"))
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    shop = cfg["shop"]
    token = cfg["access_token"]
    api = os.environ.get("SHOPIFY_API_VERSION", "2026-04")
    import urllib.request
    headers = {"X-Shopify-Access-Token": token}
    url = (
        "https://%s/admin/api/%s/blogs/%s/articles.json?limit=250&published_status=published"
        "&fields=id,handle,title,published_at,blog_id"
        % (shop, api, wc.BLOG_ID)
    )
    out = []
    while url:
        wc.assert_blog_article_endpoint(url.split("?", 1)[0])
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=90) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            link = resp.headers.get("Link", "")
        for article in payload.get("articles") or []:
            if str(article.get("blog_id") or wc.BLOG_ID) != str(wc.BLOG_ID):
                continue
            handle = (article.get("handle") or "").lower()
            if not handle:
                continue
            out.append({
                "id": str(article.get("id") or ""),
                "handle": handle,
                "title": article.get("title") or "",
                "url": wc.article_url(handle),
                "blog": wc.BLOG_ID,
                "created": article.get("published_at") or "",
                "words": 0,
                "source": "shopify",
            })
        url = ""
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part[part.find("<") + 1:part.find(">")]
    return out


def build_from_args(args):
    # An explicit catalog path is the whole catalog. Do not also read ~/genseo.
    explicit = any([args.json, args.csv, args.tracker])
    if explicit:
        json_path = args.json or ""
        csv_path = args.csv or ""
        tracker_path = args.tracker or ""
    else:
        json_path = _first(os.path.join(ROOT, "existing_articles.json"), os.path.join(GENSEO_MAIN, "existing_articles.json"))
        csv_path = _first(os.path.join(ROOT, "ALL_ARTICLES.csv"), os.path.join(GENSEO_MAIN, "ALL_ARTICLES.csv"))
        tracker_path = _first(os.path.join(ROOT, "PUBLISHED_ARTICLES_TRACKER.csv"))
    if args.from_shopify and not csv_path:
        csv_path = _first(os.path.join(ROOT, "ALL_ARTICLES.csv"), os.path.join(GENSEO_MAIN, "ALL_ARTICLES.csv"))
    gsc_path = args.gsc or latest_gsc(args.vault)
    json_rows = wc.load_json_articles(json_path) if json_path else []
    csv_rows = wc.load_csv_articles(csv_path) if csv_path else []
    tracker_rows = wc.load_tracker(tracker_path) if tracker_path else []
    if args.from_shopify:
        live = maybe_shopify_titles()
        # Live titles win. CSV still supplies word counts for matching handles.
        by_csv = {row["handle"]: row for row in csv_rows}
        merged_live = []
        for row in live:
            extra = by_csv.get(row["handle"]) or {}
            row["words"] = extra.get("words") or 0
            merged_live.append(row)
        csv_rows = merged_live
        json_rows = []
        # The live blog GET is the catalog. Tracker-only handles are not link targets.
        tracker_rows = []
    articles = wc.merge_articles(json_rows, csv_rows, tracker_rows)
    if not articles:
        raise SystemExit("no articles found; pass --json or --csv")
    gsc_rows = wc.read_gsc_csv(gsc_path) if gsc_path and os.path.isfile(gsc_path) else []
    intake = load_intake(args.intake)
    meta = {
        "built": args.day or wc.now_ict().date().isoformat(),
        "sources": {
            "json": json_path or "none",
            "csv": csv_path or "none",
            "tracker": tracker_path or "none",
            "gsc": gsc_path or "none",
            "intake": args.intake or "none",
            "shopify_titles": "yes" if args.from_shopify else "no",
        },
    }
    return wc.build_map(articles, gsc_rows, intake, meta), meta


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the Wellness Nest pillar and spoke map.")
    ap.add_argument("--json", help="existing_articles.json")
    ap.add_argument("--csv", help="ALL_ARTICLES.csv")
    ap.add_argument("--tracker", help="PUBLISHED_ARTICLES_TRACKER.csv")
    ap.add_argument("--gsc", help="GSC raw csv (default: latest vault 90-sources/gsc-daily)")
    ap.add_argument("--intake", default=os.path.join(ROOT, "state", "wellness-intake.json"))
    ap.add_argument("--vault", default=VAULT)
    ap.add_argument("--out-json", default=os.path.join(ROOT, "state", "cluster_map.json"))
    ap.add_argument("--out-md", default=os.path.join(ROOT, "docs", "CLUSTER_MAP.md"))
    ap.add_argument("--vault-md", help="vault copy path (default: 90-sources/cluster-maps/YYYY-MM-DD-cluster-map.md)")
    ap.add_argument("--no-vault", action="store_true")
    ap.add_argument("--from-shopify", action="store_true", help="read published blog titles (GET articles only)")
    ap.add_argument("--day")
    ap.add_argument("--stdout", action="store_true", help="print markdown and skip file writes")
    args = ap.parse_args(argv)
    cluster_map, _meta = build_from_args(args)
    text = wc.render_markdown(cluster_map)
    print(
        "clusters=%s pillars=%s articles=%s"
        % (cluster_map["cluster_count"], cluster_map["pillar_count"], cluster_map["article_count"])
    )
    if args.stdout:
        print(text)
        return 0
    os.makedirs(os.path.dirname(os.path.abspath(args.out_json)), exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(cluster_map, f, indent=2)
        f.write("\n")
    os.makedirs(os.path.dirname(os.path.abspath(args.out_md)), exist_ok=True)
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote %s" % args.out_json)
    print("wrote %s" % args.out_md)
    if not args.no_vault:
        day = cluster_map["built"]
        dest = args.vault_md or os.path.join(args.vault, "90-sources", "cluster-maps", "%s-cluster-map.md" % day)
        folder = os.path.dirname(dest)
        if os.path.isdir(os.path.dirname(folder)) or os.path.isdir(args.vault):
            os.makedirs(folder, exist_ok=True)
            front = (
                "---\nsource_url: https://wellnessnest.co/blogs/news\ningested: %s\n"
                "sha256: %s\ntags: [brand, analytics]\n---\n\n" % (day, __import__("hashlib").sha256(text.encode("utf-8")).hexdigest())
            )
            with open(dest, "w", encoding="utf-8") as f:
                f.write(front + text)
            print("wrote %s" % dest)
        else:
            print("vault missing, skipped copy: %s" % args.vault)
    return 0


if __name__ == "__main__":
    sys.exit(main())

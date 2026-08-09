#!/usr/bin/env python3
"""Backfill the `global.title_tag` / `global.description_tag` metafields on live articles.

Why this exists: until 2026-08-09 `shopify_publisher.py` wrote the hand-tuned STEP 4 meta
description into `summary_html` only. That field is the blog-index excerpt — the theme renders
`<meta name="description">` from `page_description`, which reads `global.description_tag` and
otherwise silently falls back to scraping the top of the body. So every article published before
that date shipped to Google with a truncated intro as its SERP snippet. The publisher now sets
the metafields on publish/update; this script repairs the ones already live.

Usage:
  backfill_seo_metafields.py --dry-run                 # report only, touch nothing
  backfill_seo_metafields.py --ids 621842301243,...    # repair specific articles
  backfill_seo_metafields.py --all                     # repair every article missing one

Articles listed in frozen_articles.txt are skipped unconditionally — they are stabilizing
their rankings and must not be touched.
"""
import argparse
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genseo_config as _gcfg  # noqa: E402
from shopify_publisher import set_seo_metafields  # noqa: E402

API = _gcfg.API
BLOG_ID = "104008483131"
DRAFTS_DIR = "/Users/kevinkreative/genseo/published_drafts"
FREEZE_FILE = "/Users/kevinkreative/genseo/frozen_articles.txt"


def _auth():
    with open(_gcfg.CONFIG_PATH) as f:
        d = json.load(f)
    return d["shop"], d["access_token"] if "access_token" in d else d["token"]


def _get(shop, token, path):
    req = urllib.request.Request(
        f"https://{shop}/admin/api/{API}/{path}",
        headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req).read())


def _frozen():
    if not os.path.exists(FREEZE_FILE):
        return set()
    with open(FREEZE_FILE) as f:
        return {l.split("#")[0].strip() for l in f if l.split("#")[0].strip()}


def _draft_meta():
    """{normalised title: (title, meta_description, source)} from every draft on disk.

    Usually empty: `do_publish` rewrites the draft with CDN URLs *after* stripping the H1 and the
    meta_description comment, so a published draft no longer carries either. Kept because a
    freshly written, not-yet-published draft does, and it beats the summary_html round-trip.
    """
    out = {}
    if not os.path.isdir(DRAFTS_DIR):
        return out
    for name in os.listdir(DRAFTS_DIR):
        if not name.endswith(".md"):
            continue
        text = open(os.path.join(DRAFTS_DIR, name), encoding="utf-8").read()
        h1 = re.search(r"^#\s+(.+)$", text, re.M)
        md = re.search(r"<!--\s*meta_description:(.*?)-->", text, re.S)
        if not (h1 and md):
            continue
        title = h1.group(1).strip()
        out[re.sub(r"\W+", "", title).lower()] = (title, md.group(1).strip(), name)
    return out


def _summary_meta(article):
    """Recover the meta description from `summary_html`.

    The publisher has always written the STEP 4 description there, so every GenSeo article carries
    an exact copy of what should have been in `description_tag`. Legacy (pre-GenSeo) articles have
    an empty summary and are left alone — inventing descriptions for them is a separate job.
    """
    txt = re.sub(r"<[^>]+>", "", article.get("summary_html") or "").strip()
    return txt or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ids", help="comma-separated article ids to repair")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    shop, token = _auth()
    frozen = _frozen()
    drafts = _draft_meta()
    only = {i.strip() for i in args.ids.split(",")} if args.ids else None

    articles = _get(shop, token, f"blogs/{BLOG_ID}/articles.json?limit=250")["articles"]
    print(f"{len(articles)} articles on blog {BLOG_ID}; {len(drafts)} drafts with a meta_description\n")

    missing, repaired, skipped = [], [], []
    for a in articles:
        aid = str(a["id"])
        mf = _get(shop, token, f"articles/{aid}/metafields.json")["metafields"]
        has = {m["key"] for m in mf if m.get("namespace") == "global"}
        if "description_tag" in has:
            continue
        key = re.sub(r"\W+", "", a["title"]).lower()
        hit = drafts.get(key)
        if hit:
            desc, src = hit[1], hit[2]
        else:
            desc, src = _summary_meta(a), "summary_html"
        if not desc:
            skipped.append((aid, a["title"], "no description available (legacy article)"))
            continue
        if aid in frozen:
            skipped.append((aid, a["title"], "FROZEN"))
            continue
        missing.append((aid, a["title"], desc, src))

    for aid, title, desc, src in missing:
        target = args.all or (only and aid in only)
        mark = "→ REPAIR" if (target and not args.dry_run) else "  (would repair)"
        print(f"{mark} {aid}  {title[:55]}")
        print(f"           {len(desc)} chars  from {src}")
        if target and not args.dry_run:
            set_seo_metafields(shop, token, aid, title=title, meta_description=desc)
            repaired.append(aid)

    if skipped:
        print("\nSKIPPED:")
        for aid, title, why in skipped:
            print(f"  {aid}  {title[:55]}  — {why}")

    print(f"\nmissing description_tag: {len(missing)}   repaired now: {len(repaired)}")


if __name__ == "__main__":
    main()

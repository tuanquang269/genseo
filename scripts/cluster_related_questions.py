#!/usr/bin/env python3
"""Print a What to ask next block, and optional in-body cluster sentences.

The block links each question to the cluster page that answers it.
It is not an FAQ and it does not emit FAQPage JSON-LD.
A new article that is not in the map yet can pass --query instead of --handle.
If state/cluster_map.json is missing, print nothing and exit 0.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wn_clusters as wc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve(cluster_map, handle="", query=""):
    """Return (handle, cluster). An unknown handle falls through to the query cluster."""
    handle = (handle or "").strip().lower()
    if handle:
        cluster = wc.article_cluster(cluster_map, handle)
        if cluster:
            return handle, cluster
    if query:
        cid = wc.assign_cluster(query)
        cluster = wc.cluster_index(cluster_map).get(cid)
        if cluster and cluster.get("id") != "other":
            return "", cluster
    return handle, None


def questions_for_handle(handle, cluster_map, limit=5):
    _handle, cluster = resolve(cluster_map, handle=handle)
    if not cluster:
        return []
    return wc.related_questions(handle, cluster, limit=limit)


def package_markdown(handle, cluster, limit=5):
    parts = []
    sentences = wc.contextual_markdown(handle, cluster)
    if sentences:
        parts.append(sentences.rstrip())
        parts.append("")
    questions = wc.related_questions(handle, cluster, limit=limit)
    block = wc.related_questions_markdown(questions)
    if block:
        parts.append(block.rstrip())
        parts.append("")
    return "\n".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Related questions and in-body cluster links for one article.")
    ap.add_argument("--handle", default="", help="live article handle already in the cluster map")
    ap.add_argument("--query", default="", help="primary keyword when the new article is not in the map yet")
    ap.add_argument("--map", default=os.environ.get("GENSEO_CLUSTER_MAP") or os.path.join(ROOT, "state", "cluster_map.json"))
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--html", action="store_true")
    ap.add_argument("--links", action="store_true", help="print in-body sentences only")
    ap.add_argument("--package", action="store_true", help="print in-body sentences, then What to ask next")
    ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args(argv)
    if not args.handle and not args.query:
        print("pass --handle or --query")
        return 1
    if not os.path.isfile(args.map):
        print("cluster map missing: %s" % args.map)
        return 0
    with open(args.map, encoding="utf-8") as f:
        cluster_map = json.load(f)
    handle, cluster = resolve(cluster_map, handle=args.handle, query=args.query)
    limit = min(5, max(1, args.limit))
    if args.package:
        print(package_markdown(handle, cluster, limit=limit))
        return 0
    if args.links:
        print(wc.contextual_markdown(handle, cluster))
        return 0
    questions = wc.related_questions(handle, cluster, limit=limit) if cluster else []
    if args.html:
        print(wc.related_questions_html(questions))
    else:
        print(wc.related_questions_markdown(questions))
    return 0


if __name__ == "__main__":
    sys.exit(main())

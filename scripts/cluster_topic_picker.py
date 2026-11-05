#!/usr/bin/env python3
"""Rank the next Wellness Nest article topics from cluster gaps.

Used by scripts/refill_tickets.py only when GENSEO_CLUSTER_PICKER=1.
The daily 5 article job does not set that variable, so this picker stays off.

Products: ShilaSource Himalayan Shilajit Resin, AgeAura Pure NMN + TMG
(https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex only),
and FloraFresh (Bacillus coagulans SNZ-1969, 15B CFU per 2 gummies).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wn_clusters as wc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def map_path(root=None, explicit=None):
    if explicit:
        return explicit
    env = os.environ.get("GENSEO_CLUSTER_MAP", "").strip()
    if env:
        return env
    return os.path.join(root or ROOT, "state", "cluster_map.json")


def load_map(path):
    if not path or not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def candidates_for_refill(bank, root=None, map_path=None, limit=8):
    """Topic dicts for refill_tickets.norm_cand. Empty when the map is missing."""
    data = load_map(map_path or map_path_default(root))
    if not data:
        return []
    return wc.topics_from_map(data, bank, limit=limit)


def map_path_default(root):
    return map_path(root)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Print ranked cluster topics. Does not edit the ticket queue.")
    ap.add_argument("--map", help="cluster_map.json (default state/cluster_map.json or $GENSEO_CLUSTER_MAP)")
    ap.add_argument("--bank", default=os.path.join(ROOT, "templates", "article-topic-bank.json"))
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    path = map_path(explicit=args.map)
    data = load_map(path)
    if not data:
        print("cluster picker: no map at %s" % path)
        return 0
    with open(args.bank, encoding="utf-8") as f:
        bank = json.load(f)
    topics = wc.topics_from_map(data, bank, limit=args.limit)
    if args.json:
        print(json.dumps(topics, indent=2))
    else:
        print("cluster picker: %s topic(s) from %s" % (len(topics), path))
        for topic in topics:
            print("%6.1f  %-22s  %s" % (topic["rank"], topic["segment"], topic["title"]))
            print("         primary: %s" % topic["primary"])
            print("         product: /products/%s" % topic["product"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Publish-time near-duplicate and query-cluster gate.

Compares a ticket or draft (title, primary keyword, H2s, slug) with the local
article catalog. No network. Stdlib plus wn_clusters.assign_cluster, which is
the same assignment the cluster map is built from.

Catalog order: existing_articles.json, PUBLISHED_ARTICLES_TRACKER.csv, then
titles already listed in state/cluster_map.json or docs/CLUSTER_MAP.md when
the json cache is behind the map. Map rows contribute a title, URL, and
cluster id. Impression and position figures in the map are not read.

Verdicts:
  PASS  distinct primary query
  WARN  near-duplicate — names the existing URL(s); action is
        "refresh existing" (one URL) or "merge" (two or more)
  FAIL  exact same primary query (normalized token set)

Exit 0 unless GENSEO_DUP_CLUSTER_BLOCK is 1/true/yes/on, in which case FAIL
exits 1. WARN never changes the exit code, so the daily lane stays unblocked
by default.

  python3 scripts/dup_cluster_gate.py --queue daily-tickets.md
  python3 scripts/dup_cluster_gate.py --draft published_drafts/article.md
  python3 scripts/dup_cluster_gate.py --keyword "how to take nmn" --title "..."
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wn_clusters as wc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENSEO_MAIN = os.path.expanduser("~/genseo")
BLOCK_ENV = "GENSEO_DUP_CLUSTER_BLOCK"

# Same-cluster near-duplicate, and a tighter bar that applies in any cluster.
# 0.72 matches topic_fitness.DUP_JACCARD for a title that is almost the same page.
NEAR_JACCARD = 0.60
STRONG_JACCARD = 0.72
PREFIX_MIN = 2
LCP_MIN = 3
LCP_RATIO = 0.75
MAX_URLS = 5
MIN_EXACT = 2

STOP = {
    "a", "an", "the", "of", "for", "to", "in", "on", "and", "or", "with", "from", "by",
    "your", "you", "is", "are", "it", "its", "this", "that", "us", "usa", "sg",
    "best", "review", "guide", "ultimate",
    "2024", "2025", "2026", "2027", "2028",
    "what", "can", "do", "does", "about", "into", "than", "just", "not", "at", "as",
    "be", "if", "per", "while",
}

OPEN_SPLIT = re.compile(r"\n(?=- \[|## \[)")
OPEN_HEAD = re.compile(
    r"^(?:- |## )\[ \] \*\*#([A-Za-z0-9-]+)\s+[—–-]\s+(.+?)\*\*(?:\s+[—–-]\s+`([^`]*)`)?"
)
PRIMARY_KW = re.compile(r"\*\*Primary keyword:\*\*\s*`([^`]+)`")
DRAFT_KW = re.compile(r"<!--\s*primary_keyword:\s*(.*?)\s*-->", re.I)
H1_RX = re.compile(r"^#\s+(.+)$", re.M)
H2_RX = re.compile(r"^##\s+(.+)$", re.M)
MAP_SECTION = re.compile(r"(?m)^(?=## )")
MAP_ID = re.compile(r"^Id: `([a-z0-9-]+)`", re.M)
MAP_LINK = re.compile(
    r"\[([^\]]+)\]\((https://wellnessnest\.co/blogs/news/([a-z0-9-]+))\)"
)


def blocking():
    return os.environ.get(BLOCK_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def _first(*paths):
    for path in paths:
        if path and os.path.isfile(path):
            return path
    return ""


def default_paths():
    """Repo files first, then the main checkout. Read-only. No network."""
    json_path = os.environ.get("GENSEO_ARTICLES_JSON") or _first(
        os.path.join(ROOT, "existing_articles.json"),
        os.path.join(GENSEO_MAIN, "existing_articles.json"),
    )
    tracker_path = os.environ.get("GENSEO_TRACKER") or _first(
        os.path.join(ROOT, "PUBLISHED_ARTICLES_TRACKER.csv"),
        os.path.join(GENSEO_MAIN, "PUBLISHED_ARTICLES_TRACKER.csv"),
    )
    map_path = os.environ.get("GENSEO_CLUSTER_MAP") or _first(
        os.path.join(ROOT, "state", "cluster_map.json"),
        os.path.join(GENSEO_MAIN, "state", "cluster_map.json"),
    )
    map_md = os.environ.get("GENSEO_CLUSTER_MAP_MD") or _first(
        os.path.join(ROOT, "docs", "CLUSTER_MAP.md"),
        os.path.join(GENSEO_MAIN, "docs", "CLUSTER_MAP.md"),
    )
    return json_path, tracker_path, map_path, map_md


def token_list(text):
    """Ordered content tokens. Years, market filler, and function words drop out."""
    raw = (text or "").lower().replace("\u2019", "'").replace("\u2018", "'")
    raw = raw.replace("\u2013", " ").replace("\u2014", " ")
    raw = re.sub(r"\([^)]*\)", " ", raw)
    raw = re.sub(r"[^a-z0-9+]+", " ", raw)
    out = []
    for word in raw.split():
        if word in STOP or len(word) < 2:
            continue
        out.append(word)
    return out


def token_key(text):
    return tuple(sorted(set(token_list(text))))


def slugify(text):
    raw = (text or "").lower().replace("\u2013", " ").replace("\u2014", " ")
    raw = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return raw[:120]


def jaccard(left, right):
    if not left or not right:
        return 0.0
    inter = len(left & right)
    union = len(left | right)
    if union == 0:
        return 0.0
    return inter / union


def overlap_score(focus, h2_tokens, exist):
    """H2 tokens raise the score only when that existing page already uses them."""
    base = jaccard(focus, exist)
    boosted = jaccard(focus | (h2_tokens & exist), exist)
    return boosted if boosted > base else base


def lcp_len(left, right):
    n = 0
    for a, b in zip(left, right):
        if a != b:
            break
        n += 1
    return n


def is_prefix(short, long):
    return len(short) >= PREFIX_MIN and len(long) >= len(short) and long[:len(short)] == short


def load_catalog(json_path="", tracker_path=""):
    """Union of existing_articles.json and the tracker, keyed by handle.

    The tracker Keyword column is the published primary query. A JSON title
    stays the title when it is longer than that keyword.
    """
    by = {}
    if json_path and os.path.isfile(json_path):
        for row in wc.load_json_articles(json_path):
            handle = row["handle"]
            by[handle] = {
                "handle": handle,
                "title": row.get("title") or "",
                "keyword": "",
                "url": row.get("url") or wc.article_url(handle),
            }
    if tracker_path and os.path.isfile(tracker_path):
        with open(tracker_path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                url = (row.get("Article Link") or row.get("url") or "").strip()
                handle = wc.handle_from_url(url)
                if not handle:
                    continue
                keyword = (row.get("Keyword") or row.get("keyword") or "").strip()
                cur = by.get(handle)
                if cur:
                    if keyword:
                        cur["keyword"] = keyword
                    if url:
                        cur["url"] = url
                    if not cur.get("title"):
                        cur["title"] = keyword
                    continue
                by[handle] = {
                    "handle": handle,
                    "title": keyword,
                    "keyword": keyword,
                    "url": url or wc.article_url(handle),
                }
    return [by[handle] for handle in sorted(by)]


def load_cluster_map(path):
    if not path or not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        return None
    return data


def articles_from_json_map(cluster_map):
    """Titles and URLs already stored on the cluster map. Ignores impressions."""
    out = []
    if not cluster_map:
        return out
    for cluster in cluster_map.get("clusters") or []:
        cid = cluster.get("id") or "other"
        members = []
        if cluster.get("pillar"):
            members.append(cluster["pillar"])
        members.extend(cluster.get("spokes") or [])
        for member in members:
            handle = (member.get("handle") or "").lower()
            if not handle:
                continue
            out.append({
                "handle": handle,
                "title": (member.get("title") or "").strip(),
                "keyword": "",
                "url": member.get("url") or wc.article_url(handle),
                "cluster": cid,
            })
    return out


def articles_from_markdown(text):
    """Blog links under each Id: cluster section of CLUSTER_MAP.md.

    Only the title and URL are read. Impression and position notes in the
    same paragraph are left unused.
    """
    out = []
    seen = set()
    for part in MAP_SECTION.split(text or ""):
        id_match = MAP_ID.search(part)
        if not id_match:
            continue
        cid = id_match.group(1)
        for title, url, handle in MAP_LINK.findall(part):
            if handle in seen:
                continue
            seen.add(handle)
            out.append({
                "handle": handle,
                "title": re.sub(r"\s+", " ", title).strip(),
                "keyword": "",
                "url": url,
                "cluster": cid,
            })
    return out


def merge_articles(catalog, extras):
    """Add map rows the json/tracker caches do not have yet.

    A tracker Keyword stays the primary query. A longer map title replaces a
    title that is only that keyword.
    """
    by = {row["handle"]: dict(row) for row in catalog or []}
    for extra in extras or []:
        handle = extra.get("handle") or ""
        if not handle:
            continue
        cur = by.get(handle)
        if not cur:
            by[handle] = dict(extra)
            continue
        if extra.get("cluster"):
            cur["cluster"] = extra["cluster"]
        extra_title = extra.get("title") or ""
        cur_title = cur.get("title") or ""
        if extra_title and (not cur_title or cur_title == (cur.get("keyword") or "") or len(extra_title) > len(cur_title)):
            cur["title"] = extra_title
        if extra.get("url") and not cur.get("url"):
            cur["url"] = extra["url"]
    return [by[handle] for handle in sorted(by)]


def index_handles(cluster_map):
    """handle -> cluster id from a built cluster map. Empty when the file is absent."""
    out = {}
    if not cluster_map:
        return out
    for cluster in cluster_map.get("clusters") or []:
        cid = cluster.get("id") or "other"
        pillar = cluster.get("pillar") or {}
        handle = (pillar.get("handle") or "").lower()
        if handle:
            out[handle] = cid
        for spoke in cluster.get("spokes") or []:
            handle = (spoke.get("handle") or "").lower()
            if handle:
                out[handle] = cid
    return out


def cluster_for_text(text, handle, handle_clusters):
    handle = (handle or "").lower()
    if handle and handle in handle_clusters:
        return handle_clusters[handle]
    return wc.assign_cluster(text or "")


def _focus_tokens(primary, title, slug):
    tokens = set(token_list(primary))
    tokens |= set(token_list(title))
    tokens |= set(token_list((slug or "").replace("-", " ")))
    return tokens


def _exist_tokens(article):
    tokens = set(token_list(article.get("keyword") or ""))
    tokens |= set(token_list(article.get("title") or ""))
    tokens |= set(token_list((article.get("handle") or "").replace("-", " ")))
    return tokens


def _exact(primary, article):
    key = token_key(primary)
    if len(key) < MIN_EXACT:
        return False
    for field in (article.get("keyword") or "", article.get("title") or ""):
        if token_key(field) == key:
            return True
    return False


def _near(score, same, primary_tokens, article):
    if score >= STRONG_JACCARD:
        return True
    if not same:
        return False
    if score >= NEAR_JACCARD:
        return True
    for field in (article.get("title") or "", article.get("keyword") or ""):
        ordered = token_list(field)
        if is_prefix(primary_tokens, ordered):
            return True
        if not primary_tokens:
            continue
        shared = lcp_len(primary_tokens, ordered)
        if shared >= LCP_MIN and shared / len(primary_tokens) >= LCP_RATIO:
            return True
    return False


def _blank(primary, title, slug, cluster):
    return {
        "verdict": "PASS",
        "cluster": cluster,
        "keyword": primary,
        "title": title,
        "slug": slug,
        "action": "",
        "overlap": 0.0,
        "matches": [],
        "line": "PASS cluster=%s" % (cluster or "other"),
    }


def load_default_context():
    """JSON + tracker, then cluster-map titles when those caches are behind."""
    json_path, tracker_path, map_path, map_md = default_paths()
    catalog = load_catalog(json_path, tracker_path)
    cluster_map = load_cluster_map(map_path)
    handle_clusters = index_handles(cluster_map)
    if cluster_map:
        extras = articles_from_json_map(cluster_map)
    elif map_md:
        with open(map_md, encoding="utf-8") as fh:
            extras = articles_from_markdown(fh.read())
    else:
        extras = []
    for row in extras:
        handle_clusters.setdefault(row["handle"], row.get("cluster") or "other")
    catalog = merge_articles(catalog, extras)
    return catalog, handle_clusters


def assess(title="", keyword="", h2s=None, slug="", catalog=None, handle_clusters=None, cluster=""):
    """Return one report dict. catalog=[] compares against nothing and PASSes."""
    h2s = list(h2s or [])
    title = (title or "").strip()
    primary = (keyword or title).strip()
    slug = (slug or "").strip().lower()
    handle_clusters = handle_clusters or {}
    if catalog is None:
        catalog, discovered = load_default_context()
        if not handle_clusters:
            handle_clusters = discovered
    text = " ".join([primary, title, slug.replace("-", " ")])
    cid = cluster or cluster_for_text(text, slug, handle_clusters)
    if not primary and not title:
        return _blank("", "", slug, cid)

    focus = _focus_tokens(primary, title, slug)
    h2_tokens = set()
    for head in h2s:
        h2_tokens |= set(token_list(head))
    primary_tokens = token_list(primary)
    matches = []
    for article in catalog:
        handle = (article.get("handle") or "").lower()
        if not handle or (slug and slug == handle):
            continue
        exist = _exist_tokens(article)
        score = overlap_score(focus, h2_tokens, exist)
        ecluster = article.get("cluster") or cluster_for_text(
            " ".join([
                article.get("keyword") or "",
                article.get("title") or "",
                handle.replace("-", " "),
            ]),
            handle,
            handle_clusters,
        )
        same = bool(cid and ecluster and cid == ecluster and cid != "other")
        exact = _exact(primary, article)
        if not exact and not _near(score, same, primary_tokens, article):
            continue
        matches.append({
            "url": article.get("url") or wc.article_url(handle),
            "handle": handle,
            "title": article.get("title") or "",
            "cluster": ecluster,
            "overlap": round(score, 4),
            "reason": "exact-query" if exact else "near-duplicate",
        })
    matches.sort(key=lambda m: (
        0 if m["reason"] == "exact-query" else 1,
        1 if wc.is_dupe_handle(m["handle"]) else 0,
        -m["overlap"],
        m["url"],
    ))
    shown = matches[:MAX_URLS]
    if not shown:
        return _blank(primary, title, slug, cid)
    verdict = "FAIL" if any(m["reason"] == "exact-query" for m in shown) else "WARN"
    if verdict == "FAIL":
        shown = [m for m in shown if m["reason"] == "exact-query"][:MAX_URLS]
    action = "refresh existing" if len(shown) == 1 else "merge"
    urls = " | ".join(m["url"] for m in shown)
    top = shown[0]["overlap"]
    if verdict == "FAIL":
        line = 'FAIL exact primary query "%s" cluster=%s — %s — %s' % (primary, cid, action, urls)
    else:
        line = "WARN near-duplicate cluster=%s overlap=%.2f — %s — %s" % (cid, top, action, urls)
    return {
        "verdict": verdict,
        "cluster": cid,
        "keyword": primary,
        "title": title,
        "slug": slug,
        "action": action,
        "overlap": top,
        "matches": shown,
        "line": line,
    }


def gate_lines(report):
    """(fail_lines, warn_lines) for validate_article. Default keeps FAIL as a warning."""
    verdict = (report or {}).get("verdict") or "PASS"
    if verdict == "PASS":
        return [], []
    line = report.get("line") or verdict
    if verdict == "FAIL" and blocking():
        return [line], []
    return [], [line]


def parse_open_tickets(text):
    """Open `- [ ]` / `## [ ]` tickets only. Closed lines are history."""
    out = []
    for block in OPEN_SPLIT.split(text or ""):
        head = block.split("\n", 1)[0]
        match = OPEN_HEAD.match(head)
        if not match:
            continue
        kw_match = PRIMARY_KW.search(block)
        heading_kw = (match.group(2) or "").strip()
        title = (match.group(3) or "").strip() or heading_kw
        keyword = kw_match.group(1).strip() if kw_match else heading_kw
        out.append({
            "id": match.group(1),
            "keyword": keyword,
            "title": title,
            "h2s": [h.strip() for h in H2_RX.findall(block)],
            "slug": slugify(title),
        })
    return out


def parse_draft(text, path=""):
    title_match = H1_RX.search(text or "")
    title = title_match.group(1).strip() if title_match else ""
    kw_match = DRAFT_KW.search(text or "")
    keyword = kw_match.group(1).strip() if kw_match else title
    slug = ""
    if path:
        slug = os.path.splitext(os.path.basename(path))[0].lower()
    if not slug:
        slug = slugify(title)
    return {
        "id": "",
        "keyword": keyword,
        "title": title,
        "h2s": [h.strip() for h in H2_RX.findall(text or "")],
        "slug": slug,
    }


def _prepare(args):
    # An explicit catalog path is the whole catalog. Do not also read the
    # repo map, or unit tests would depend on docs/CLUSTER_MAP.md.
    if any([args.articles, args.tracker, args.map]):
        catalog = load_catalog(args.articles, args.tracker)
        cluster_map = load_cluster_map(args.map)
        return catalog, index_handles(cluster_map)
    return load_default_context()


def _items_from_args(args):
    if args.queue:
        with open(args.queue, encoding="utf-8") as fh:
            return parse_open_tickets(fh.read())
    if args.ticket:
        with open(args.ticket, encoding="utf-8") as fh:
            items = parse_open_tickets(fh.read())
        if args.id:
            want = args.id.lstrip("#")
            items = [item for item in items if item["id"] == want]
        return items
    if args.draft:
        with open(args.draft, encoding="utf-8") as fh:
            return [parse_draft(fh.read(), args.draft)]
    if args.title or args.keyword or args.h2:
        title = args.title or args.keyword
        keyword = args.keyword or args.title
        return [{
            "id": "",
            "keyword": keyword,
            "title": title,
            "h2s": list(args.h2 or []),
            "slug": args.slug or slugify(title),
        }]
    return None


def format_queue_line(item, report):
    prefix = ("#%s " % item["id"]) if item.get("id") else ""
    return prefix + report["line"]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Offline publish-time duplicate cluster gate.")
    ap.add_argument("--title", default="")
    ap.add_argument("--keyword", default="")
    ap.add_argument("--slug", default="")
    ap.add_argument("--h2", action="append", default=None)
    ap.add_argument("--draft", help="markdown draft path")
    ap.add_argument("--ticket", help="ticket file; optional --id selects one open ticket")
    ap.add_argument("--id", default="")
    ap.add_argument("--queue", help="dry-run every open ticket in a daily-tickets.md file")
    ap.add_argument("--articles", default="", help="existing_articles.json (skips the default catalog)")
    ap.add_argument("--tracker", default="", help="PUBLISHED_ARTICLES_TRACKER.csv")
    ap.add_argument("--map", default="", help="state/cluster_map.json")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    items = _items_from_args(args)
    if items is None:
        ap.print_help()
        return 2
    catalog, handle_clusters = _prepare(args)
    reports = []
    lines = []
    for item in items:
        report = assess(
            title=item.get("title") or "",
            keyword=item.get("keyword") or "",
            h2s=item.get("h2s") or [],
            slug=item.get("slug") or "",
            catalog=catalog,
            handle_clusters=handle_clusters,
        )
        report["id"] = item.get("id") or ""
        reports.append(report)
        lines.append(format_queue_line(item, report))
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for report in reports:
        counts[report["verdict"]] = counts.get(report["verdict"], 0) + 1
    mode = "block" if blocking() else "warn-only"
    summary = "dup_cluster_gate: queued=%d pass=%d warn=%d fail=%d mode=%s" % (
        len(reports), counts["PASS"], counts["WARN"], counts["FAIL"], mode,
    )
    if args.json:
        print(json.dumps({"mode": mode, "summary": summary, "results": reports}, ensure_ascii=False, indent=1))
    else:
        for line in lines:
            print(line)
        if len(reports) != 1 or items[0].get("id"):
            print(summary)
    if blocking() and counts["FAIL"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

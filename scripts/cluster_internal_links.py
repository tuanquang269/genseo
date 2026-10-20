#!/usr/bin/env python3
"""Insert contextual cluster links into blog article HTML.

Default is a dry run: read articles, write a diff report, do not PUT.
--apply writes backups/<date>/cluster-links-*.json for every article it will
change, then PUT body_html on blog 104008483131 only.

--rollback <file> restores those bodies. It also requires --apply.
Landing handles (gsl-*, landing-*) are skipped. Pages, products, collections,
and theme URLs are refused.

Idempotent marker: data-genseo-cluster-link.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wn_clusters as wc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    path = os.path.expanduser(os.environ.get("GENSEO_CONFIG", "~/.genseo/shopify_token.json"))
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    api = os.environ.get("SHOPIFY_API_VERSION", "2026-04")
    return cfg["shop"], cfg["access_token"], api


class ShopifyArticles:
    """GET and PUT blog articles only. backup_before_changes.py backs up collections
    and the theme and runs on import, so this client does not import it. Backups for
    this job are full article JSON files in backups/, same folder convention.
    """

    def __init__(self, shop, token, api):
        self.shop = shop
        self.token = token
        self.api = api

    def _url(self, article_id=None):
        base = "https://%s/admin/api/%s/blogs/%s/articles" % (self.shop, self.api, wc.BLOG_ID)
        if article_id:
            url = base + "/%s.json" % article_id
        else:
            url = base + ".json"
        wc.assert_blog_article_endpoint(url)
        return url

    def list_articles(self):
        url = self._url() + "?limit=250&published_status=published&fields=id,handle,title,body_html,blog_id,published_at"
        wc.assert_blog_article_endpoint(url.split("?", 1)[0])
        out = []
        headers = {"X-Shopify-Access-Token": self.token}
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
                out.append({
                    "id": article.get("id"),
                    "handle": handle,
                    "title": article.get("title") or "",
                    "body_html": article.get("body_html") or "",
                    "blog_id": str(wc.BLOG_ID),
                })
            url = ""
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part[part.find("<") + 1:part.find(">")]
        return out

    def put_body(self, article_id, body_html):
        url = self._url(article_id)
        payload = {"article": {"id": int(article_id), "body_html": body_html}}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="PUT",
            headers={
                "X-Shopify-Access-Token": self.token,
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.status


def plan_updates(articles, cluster_map, limit=None):
    updates = []
    skipped = []
    for article in articles:
        handle = (article.get("handle") or "").lower()
        if str(article.get("blog_id") or article.get("blog") or wc.BLOG_ID) not in (wc.BLOG_ID, "news"):
            skipped.append((handle, "not the news blog"))
            continue
        if not wc.safe_handle(handle):
            skipped.append((handle or "?", "skipped landing or unsafe handle"))
            continue
        cluster = wc.article_cluster(cluster_map, handle)
        if not cluster or cluster.get("id") == "other":
            skipped.append((handle, "no cluster"))
            continue
        new_body, added = wc.plan_article_html(article.get("body_html") or "", handle, cluster)
        if not added:
            continue
        updates.append({
            "id": article.get("id"),
            "handle": handle,
            "title": article.get("title") or "",
            "blog_id": wc.BLOG_ID,
            "old_body": article.get("body_html") or "",
            "new_body": new_body,
            "added": added,
        })
    updates.sort(key=lambda row: row["handle"])
    if limit is not None:
        updates = updates[:limit]
    return updates, skipped


def write_backup(updates, folder):
    os.makedirs(folder, exist_ok=True)
    stamp = dt.datetime.now(wc.ICT).strftime("%H%M%S")
    path = os.path.join(folder, "cluster-links-%s.json" % stamp)
    payload = {
        "kind": "genseo-cluster-links",
        "blog_id": wc.BLOG_ID,
        "created": dt.datetime.now(wc.ICT).isoformat(),
        "articles": [
            {
                "id": row["id"],
                "handle": row["handle"],
                "title": row["title"],
                "body_html": row["old_body"],
            }
            for row in updates
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
        f.write("\n")
    return path


def render_report(updates, skipped, cluster_map, applied):
    body_links = sum(1 for row in updates for link in row["added"] if link["kind"] != "question")
    question_links = sum(1 for row in updates for link in row["added"] if link["kind"] == "question")
    link_count = body_links + question_links
    lines = [
        "# Cluster link dry run" if not applied else "# Cluster link apply",
        "",
        "Clusters: %s. Pillars: %s. Articles in the map: %s." % (
            cluster_map.get("cluster_count"), cluster_map.get("pillar_count"), cluster_map.get("article_count"),
        ),
        "Articles with proposed new links: %s." % len(updates),
        "In-body sentence links: %s." % body_links,
        "What to ask next links: %s." % question_links,
        "New link count: %s." % link_count,
        "Shopify writes: %s." % ("yes" if applied else "no"),
        "",
        "Links are sentences in the body plus a What to ask next list. The list is not an FAQ and does not add FAQPage JSON-LD. Marker: data-genseo-cluster-link.",
        "",
        "## Proposed",
        "",
    ]
    if not updates:
        lines.append("No new links.")
        lines.append("")
    for row in updates:
        lines.append("### %s" % row["handle"])
        lines.append("")
        for link in row["added"]:
            lines.append("- %s: [%s](%s)" % (link["kind"], link["handle"], link["url"]))
        lines.append("")
    lines.append("## Skipped sample")
    lines.append("")
    for handle, reason in skipped[:30]:
        lines.append("- %s: %s" % (handle or "?", reason))
    lines.append("")
    return "\n".join(lines), link_count


def apply_rollback(path, store, apply):
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    if payload.get("kind") != "genseo-cluster-links":
        raise SystemExit("refusing rollback file that is not a cluster-links backup")
    if str(payload.get("blog_id")) != str(wc.BLOG_ID):
        raise SystemExit("refusing rollback for a different blog")
    articles = payload.get("articles") or []
    print("rollback %s articles from %s" % (len(articles), path))
    if not apply:
        for article in articles:
            print("would restore %s" % article.get("handle"))
        print("dry-run: no PUT")
        return 0
    for article in articles:
        store.put_body(article["id"], article.get("body_html") or "")
        print("restored %s" % article.get("handle"))
    return 0


def run(args, store=None, articles=None, cluster_map=None):
    apply = bool(args.apply)
    if args.dry_run and args.apply:
        print("pass only one of --dry-run and --apply")
        return 1
    if args.rollback:
        if store is None and apply:
            shop, token, api = load_config()
            store = ShopifyArticles(shop, token, api)
        if store is None and not apply:
            return apply_rollback(args.rollback, store=None, apply=False)
        return apply_rollback(args.rollback, store, apply)
    if cluster_map is None:
        with open(args.map, encoding="utf-8") as f:
            cluster_map = json.load(f)
    if articles is None:
        if args.articles:
            with open(args.articles, encoding="utf-8") as f:
                raw = json.load(f)
            articles = raw.get("articles") if isinstance(raw, dict) else raw
        elif args.from_shopify:
            if store is None:
                shop, token, api = load_config()
                store = ShopifyArticles(shop, token, api)
            articles = store.list_articles()
        else:
            print("pass --articles or --from-shopify")
            return 1
    updates, skipped = plan_updates(articles, cluster_map, limit=args.limit)
    report, link_count = render_report(updates, skipped, cluster_map, applied=apply)
    if args.report:
        folder = os.path.dirname(os.path.abspath(args.report))
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report)
        print("wrote %s" % args.report)
    print(
        "articles_with_new_links=%s link_count=%s apply=%s"
        % (len(updates), link_count, "yes" if apply else "no")
    )
    if not apply:
        if not args.report:
            print(report)
        return 0
    if not updates:
        print("nothing to apply")
        return 0
    day = dt.datetime.now(wc.ICT).date().isoformat()
    backup_dir = getattr(args, "backup_dir", None) or os.path.join(ROOT, "backups", day)
    backup = write_backup(updates, backup_dir)
    print("backup %s" % backup)
    if store is None:
        shop, token, api = load_config()
        store = ShopifyArticles(shop, token, api)
    for row in updates:
        if not row.get("id"):
            print("skip %s: no article id" % row["handle"])
            continue
        store.put_body(row["id"], row["new_body"])
        print("updated %s" % row["handle"])
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Contextual cluster links for blog articles. Default dry run.")
    ap.add_argument("--map", default=os.path.join(ROOT, "state", "cluster_map.json"))
    ap.add_argument("--articles", help="JSON list of articles with body_html")
    ap.add_argument("--from-shopify", action="store_true", help="GET published blog articles")
    ap.add_argument("--dry-run", action="store_true", help="default when --apply is absent")
    ap.add_argument("--apply", action="store_true", help="PUT body_html after a full backup")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--report", help="markdown report path")
    ap.add_argument("--rollback", help="backup JSON from a previous --apply")
    args = ap.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Audit live news-blog anchors and propose blog-to-blog brand links.

Reads stored article HTML. Does not PUT, publish, or edit paid templates.
The Admin reader, when requested, is cluster_internal_links.ShopifyArticles
list_articles (GET blog 104008483131 only). GemPages bodies use
cluster_internal_links.body_is_gempages and are not proposed, because that
script already skips them: the live page does not render body_html.

A proposal is one sentence inside a news article, pointing at another news
article, with a house-brand anchor. Product, collection, page, home, and
cart URLs are never targets.

Usage:
    python3 scripts/brand_blog_anchors.py --articles tests/fixtures/brand_serp/articles.json \
        --out /tmp/proposals.md
    python3 scripts/brand_blog_anchors.py --fetch-admin --out docs/BRAND_BLOG_ANCHOR_PROPOSALS_2026-10-21.md
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brand_serp_slice as serp
import wn_clusters as wc

BRAND_REVIEW = "wellness-nest-shilajit-reviews-what-85-buyers-report"
GOLD_REVIEW = "shilajit-gold-resin-review-is-75-worth-it-us-2026"
SHOCKWAVE_REVIEW = "shilajit-shockwave-review-1-drop-or-1-ml-us-2026"

ANCHORS = {
    BRAND_REVIEW: "Wellness Nest shilajit reviews",
    GOLD_REVIEW: "Shilajit Gold Resin review",
    SHOCKWAVE_REVIEW: "Shilajit Shockwave review",
}
SENTENCES = {
    BRAND_REVIEW: "Shoppers looking up the store brand can read [{anchor}]({url}).",
    GOLD_REVIEW: "The Gold Resin note on this store is [{anchor}]({url}).",
    SHOCKWAVE_REVIEW: "The Shockwave note on this store is [{anchor}]({url}).",
}
FUSI_ANCHOR = "FusiForce creatine gummies"
FUSI_SENTENCE = "The FusiForce gummy article on this store is [{anchor}]({url})."

_SHILAJIT = re.compile(r"shilajit|shilasource|fulvic", re.I)
_SHOCKWAVE = re.compile(r"shockwave", re.I)
_GOLD = re.compile(r"gold\s*resin", re.I)
_FUSI = re.compile(r"fusiforce", re.I)


class _LinkParser(HTMLParser):
    def __init__(self, region_only):
        super().__init__(convert_charrefs=True)
        self.region_only = region_only
        self.region_depth = 0
        self.in_region = not region_only
        self.skip = 0
        self.in_a = False
        self.href = ""
        self.anchor_parts = []
        self.links = []
        self.done = False

    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        tag = tag.lower()
        ad = {key.lower(): (value or "") for key, value in attrs}
        if tag in ("script", "style"):
            self.skip += 1
            return
        classes = ad.get("class", "").split()
        if self.region_only and tag == "div" and "article-template__content" in classes and not self.in_region:
            self.in_region = True
            self.region_depth = 1
        elif self.region_only and self.in_region and tag == "div":
            self.region_depth += 1
        if self.in_region and self.skip == 0 and tag == "a":
            self.in_a = True
            self.href = ad.get("href", "").strip()
            self.anchor_parts = []

    def handle_endtag(self, tag):
        if self.done:
            return
        tag = tag.lower()
        if tag == "a" and self.in_a:
            text = re.sub(r"\s+", " ", "".join(self.anchor_parts)).strip()
            if self.href:
                self.links.append({"href": self.href, "anchor": text})
            self.in_a = False
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        if self.region_only and self.in_region and tag == "div":
            self.region_depth -= 1
            if self.region_depth <= 0:
                self.in_region = False
                self.done = True

    def handle_data(self, data):
        if self.in_a and self.skip == 0:
            self.anchor_parts.append(data)


def links_in_html(html):
    text = html or ""
    region = "article-template__content" in text
    parser = _LinkParser(region_only=region)
    parser.feed(text)
    parser.close()
    return parser.links


def article_status(article):
    import cluster_internal_links as cil
    body = article.get("body_html") or ""
    if cil.body_is_gempages(body):
        return "page-builder"
    if not body.strip():
        return "empty"
    return "ok"


def _text(article):
    return "%s %s" % (article.get("title") or "", article.get("handle") or "")


def fusiforce_rank(article):
    handle = (article.get("handle") or "").lower()
    title = (article.get("title") or "").lower()
    score = 0
    if handle.startswith("fusiforce-creatine"):
        score += 100
    if "gummies" in handle or "gummies" in title:
        score += 10
    if "review" in handle:
        score += 5
    return (-score, len(handle), handle)


def pick_fusiforce_hub(articles):
    candidates = [
        article for article in articles
        if wc.safe_handle(article.get("handle") or "") and _FUSI.search(_text(article))
        and article_status(article) == "ok"
    ]
    if not candidates:
        return ""
    candidates.sort(key=fusiforce_rank)
    return candidates[0]["handle"].lower()


def _known_target(handle, hub):
    if handle == hub and hub:
        return "fusiforce"
    return {
        BRAND_REVIEW: "brand-review",
        GOLD_REVIEW: "gold",
        SHOCKWAVE_REVIEW: "shockwave",
    }.get(handle, "")


def mentions_fusiforce(article):
    blob = _text(article) + "\n" + (article.get("body_html") or "")
    return bool(_FUSI.search(blob))


def fusi_source(article):
    """Creatine articles, or a page whose title or handle names FusiForce.

    A turkesterone or NMN article that only mentions the gummy in passing is
    not a source. Those product lines stay separate.
    """
    if not mentions_fusiforce(article):
        return False
    text = _text(article)
    if _FUSI.search(text):
        return True
    return wc.assign_cluster(text) == "creatine"


def proposal_targets(article, articles):
    handle = (article.get("handle") or "").lower()
    if article_status(article) != "ok" or not wc.safe_handle(handle):
        return []
    text = _text(article)
    hub = pick_fusiforce_hub(articles)
    present = {(item.get("handle") or "").lower() for item in articles}
    targets = []
    if _SHILAJIT.search(text):
        targets.append(BRAND_REVIEW)
        if _SHOCKWAVE.search(text):
            targets.append(SHOCKWAVE_REVIEW)
        if _GOLD.search(text):
            targets.append(GOLD_REVIEW)
    if fusi_source(article) and hub:
        targets.append(hub)
    out = []
    for target in targets:
        if target == handle or target not in present:
            continue
        if target not in out:
            out.append(target)
    return out


def _linked_handles(links):
    found = {}
    for link in links:
        handle = serp.blog_handle_from_url(link["href"])
        if not handle:
            continue
        found.setdefault(handle, []).append(link)
    return found


def assert_blog_proposal(url):
    path = serp.url_parts(url)["path"]
    if not path.startswith("/blogs/news/"):
        raise RuntimeError("proposal is not a news article: %s" % url)
    for bit in ("/products", "/collections", "/pages", "/cart", "/checkouts"):
        if bit in path:
            raise RuntimeError("proposal touches a paid path: %s" % url)
    return url


def sentence_for(target, hub):
    url = assert_blog_proposal(wc.article_url(target))
    if target == hub:
        anchor = FUSI_ANCHOR
        text = FUSI_SENTENCE.format(anchor=anchor, url=url)
    else:
        anchor = ANCHORS[target]
        text = SENTENCES[target].format(anchor=anchor, url=url)
    if not serp.is_house_brand(anchor):
        raise RuntimeError("anchor is not a house brand: %s" % anchor)
    return anchor, url, text


def build_report(articles, live_handles=None, source=""):
    articles = [dict(article, handle=(article.get("handle") or "").lower()) for article in articles]
    by_handle = {}
    for article in articles:
        if article["handle"]:
            by_handle[article["handle"]] = article
    hub = pick_fusiforce_hub(articles)
    live = None if live_handles is None else {handle.lower() for handle in live_handles}

    existing = []
    paid_anchors = []
    other_links = 0
    proposals = []
    rewrites = []
    skipped = []
    not_on_sitemap = []

    for article in articles:
        handle = article["handle"]
        if not handle:
            continue
        status = article_status(article)
        on_sitemap = live is None or handle in live
        if live is not None and not on_sitemap:
            not_on_sitemap.append(handle)
        if status != "ok" or not wc.safe_handle(handle):
            skipped.append({
                "handle": handle,
                "title": article.get("title") or "",
                "status": status if status != "ok" else "unsafe-handle",
            })
            continue
        links = links_in_html(article.get("body_html") or "")
        linked = _linked_handles(links)
        for link in links:
            blog_handle = serp.blog_handle_from_url(link["href"])
            info = serp.url_parts(link["href"])
            brand_anchor = serp.is_house_brand(link["anchor"])
            if blog_handle and blog_handle != handle:
                existing.append({
                    "source": handle,
                    "source_title": article.get("title") or "",
                    "target": blog_handle,
                    "anchor": link["anchor"],
                    "brand_anchor": brand_anchor,
                })
            elif info["ours"] and info["kind"] in serp.PAID_KINDS and brand_anchor:
                paid_anchors.append({
                    "source": handle,
                    "anchor": link["anchor"],
                    "path": info["path"],
                })
            elif info["ours"] and not blog_handle:
                other_links += 1
        if not on_sitemap:
            continue
        for target in proposal_targets(article, articles):
            if live is not None and target not in live:
                continue
            anchors = linked.get(target, [])
            if anchors and any(serp.is_house_brand(link["anchor"]) for link in anchors):
                continue
            if anchors:
                rewrites.append({
                    "source": handle,
                    "source_title": article.get("title") or "",
                    "target": target,
                    "anchors": [link["anchor"] for link in anchors],
                })
                continue
            anchor, url, text = sentence_for(target, hub)
            proposals.append({
                "source": handle,
                "source_title": article.get("title") or "",
                "target": target,
                "target_title": (by_handle.get(target) or {}).get("title") or "",
                "anchor": anchor,
                "url": url,
                "sentence": text,
                "kind": _known_target(target, hub),
            })

    proposals.sort(key=lambda row: (row["target"], row["source"]))
    rewrites.sort(key=lambda row: (row["target"], row["source"]))
    existing.sort(key=lambda row: (row["target"], row["source"], row["anchor"]))
    return {
        "source": source,
        "articles": len(articles),
        "hub": hub,
        "existing": existing,
        "paid_anchors": paid_anchors,
        "other_links": other_links,
        "proposals": proposals,
        "rewrites": rewrites,
        "skipped": skipped,
        "not_on_sitemap": sorted(not_on_sitemap),
        "targets_present": {
            BRAND_REVIEW: BRAND_REVIEW in by_handle,
            GOLD_REVIEW: GOLD_REVIEW in by_handle,
            SHOCKWAVE_REVIEW: SHOCKWAVE_REVIEW in by_handle,
        },
        "gaps": _body_gaps(skipped),
    }


def _body_gaps(skipped):
    """Shilajit or FusiForce articles whose stored body cannot take a sentence."""
    rows = []
    for row in skipped:
        blob = "%s %s" % (row.get("title") or "", row.get("handle") or "")
        if _SHILAJIT.search(blob) or _FUSI.search(blob):
            rows.append(row)
    rows.sort(key=lambda row: row["handle"])
    return rows


def _review_existing(report):
    wanted = {BRAND_REVIEW, GOLD_REVIEW, SHOCKWAVE_REVIEW}
    return [row for row in report["existing"] if row["target"] in wanted]


def _collapse_links(rows):
    grouped = {}
    for row in rows:
        key = (row["source"], row["target"])
        slot = grouped.get(key)
        if slot is None:
            slot = {
                "source": row["source"],
                "target": row["target"],
                "anchors": [],
                "brand_anchor": False,
            }
            grouped[key] = slot
        if row["anchor"] and row["anchor"] not in slot["anchors"]:
            slot["anchors"].append(row["anchor"])
        slot["brand_anchor"] = slot["brand_anchor"] or row["brand_anchor"]
    out = list(grouped.values())
    out.sort(key=lambda row: (row["target"], row["source"]))
    return out


def render_report(report, audit_date="2026-10-21"):
    lines = [
        "# Brand blog anchor proposals — %s" % audit_date,
        "",
        "Proposal only. No Shopify write, no theme edit, and no change to home, "
        "product, collection, page, cart, or checkout URLs. "
        "Each new link is a news article pointing at another news article.",
        "",
        "`docs/CLUSTER_LINK_DRY_RUN_2026-10-20.md` records Shopify writes: no. "
        "This audit reads stored article bodies and does not treat that dry run as live.",
        "",
        "Source: %s" % (report.get("source") or "article records passed in."),
        "",
        "Articles in the set: %d. New sentences: %d. "
        "Stored blog-to-blog links of any kind: %d. "
        "Links to a target whose anchors are all non-brand: %d. "
        "Skipped (empty body, page builder, or unsafe handle): %d. "
        "Not on the unprefixed article sitemap: %d. "
        "Same-site links that are not news articles: %d."
        % (
            report["articles"], len(report["proposals"]), len(report["existing"]),
            len(report["rewrites"]), len(report["skipped"]), len(report["not_on_sitemap"]),
            report["other_links"],
        ),
        "",
        "FusiForce hub handle: `%s`." % (report["hub"] or "(none)"),
        "",
        "Review targets present in the set: %s."
        % ", ".join("%s=%s" % (key, "yes" if value else "no") for key, value in sorted(report["targets_present"].items())),
        "",
        "## Existing links to the brand review posts",
        "",
        "A brand anchor matches the same house-brand rule as the CSV slice "
        "(store name, or a house line such as FusiForce, Shockwave, or Shilajit Gold Resin).",
        "",
    ]
    reviews = _collapse_links(_review_existing(report))
    brand_review_sources = {
        row["source"] for row in reviews if row["target"] == BRAND_REVIEW and row["brand_anchor"]
    }
    lines.append(
        "Distinct sources with a house-brand anchor to the Wellness Nest shilajit review: %d."
        % len(brand_review_sources)
    )
    lines.append("")
    if not reviews:
        lines.append("No stored body in this set links to those three review handles.")
    else:
        lines.extend(_table(
            ["source", "target", "anchors", "brand anchor"],
            [
                [row["source"], row["target"], "; ".join(row["anchors"]), "yes" if row["brand_anchor"] else "no"]
                for row in reviews
            ],
        ))
    lines.extend(["", "## Shilajit or FusiForce bodies that cannot take a sentence", ""])
    lines.append(
        "These handles match shilajit or FusiForce, and the stored body is empty or a page builder. "
        "`cluster_internal_links.py` skips that kind of body because the live page does not render `body_html`. "
        "No sentence is proposed. Rebuilding the article onto the news template would need a separate GO."
    )
    lines.append("")
    if not report.get("gaps"):
        lines.append("None.")
    else:
        lines.extend(_table(
            ["handle", "reason"],
            [[row["handle"], row["status"]] for row in report["gaps"]],
        ))
        shilajit_gap = any(
            _SHILAJIT.search("%s %s" % (row.get("title") or "", row.get("handle") or ""))
            for row in report["gaps"]
        )
        if shilajit_gap and report.get("targets_present", {}).get(BRAND_REVIEW, False):
            _anchor, _url, text = sentence_for(BRAND_REVIEW, report.get("hub") or "")
            lines.extend([
                "",
                "If one of those shilajit articles is rebuilt on the news template, the sentence to add is:",
                "",
                text,
                "",
                "Do not paste it into the current stored body.",
            ])
    lines.extend([
        "",
        "## Already linked, anchor is not a house-brand phrase",
        "",
        "These bodies already contain the href. A second link is not proposed. "
        "Changing the anchor is a blog edit and needs a GO. This file does not change it.",
        "",
    ])
    if not report["rewrites"]:
        lines.append("None.")
    else:
        lines.extend(_table(
            ["source", "target", "current anchor"],
            [
                [row["source"], row["target"], "; ".join(row["anchors"])]
                for row in report["rewrites"]
            ],
        ))
    lines.extend([
        "",
        "## Proposed sentences",
        "",
        "Paste only with a GO, into the source article body, on the news blog. "
        "One sentence. The anchor is the house brand. The href is the news article.",
        "",
    ])
    if not report["proposals"]:
        if report.get("gaps"):
            lines.append(
                "No missing sentence in a body the news template already renders. "
                "The sentence for a rebuilt shilajit article is in the section above."
            )
        else:
            lines.append("No missing blog-to-blog brand link under these rules.")
    else:
        lines.extend(_table(
            ["source", "target", "anchor", "sentence"],
            [
                [row["source"], row["target"], row["anchor"], row["sentence"]]
                for row in report["proposals"]
            ],
        ))
    lines.extend([
        "",
        "## Brand anchors that already point at paid templates",
        "",
        "Listed so they are visible. Do not edit these URLs from this proposal.",
        "",
    ])
    if not report["paid_anchors"]:
        lines.append("None in this set.")
    else:
        shown = report["paid_anchors"][:40]
        lines.extend(_table(
            ["source", "anchor", "path"],
            [[row["source"], row["anchor"], row["path"]] for row in shown],
        ))
        if len(report["paid_anchors"]) > len(shown):
            lines.append("")
            lines.append("%d more paid-template anchors are omitted from this table." % (len(report["paid_anchors"]) - len(shown)))
    lines.extend(["", "## Skipped articles", ""])
    if not report["skipped"]:
        lines.append("None.")
    else:
        lines.extend(_table(
            ["handle", "reason"],
            [[row["handle"], row["status"]] for row in report["skipped"]],
        ))
    if report["not_on_sitemap"]:
        lines.extend([
            "",
            "## Published in Admin, absent from the unprefixed article sitemap",
            "",
            "No proposal from these handles.",
            "",
        ])
        for handle in report["not_on_sitemap"]:
            lines.append("- `%s`" % handle)
    lines.extend([
        "",
        "## What needs a GO",
        "",
        "- Applying any sentence above is a news-article body edit. This file does not apply it.",
        "- Rewriting an existing non-brand anchor is a separate blog edit.",
        "- Paid-template anchors stay as they are.",
        "- A new article is not created here. If the FusiForce hub is a segment article, "
        "that is the live page the anchor can point at until a different target exists.",
        "",
    ])
    return "\n".join(lines).rstrip() + "\n"


def _table(headers, rows):
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        cells = []
        for value in row:
            text = "" if value is None else str(value)
            cells.append(text.replace("|", "\\|").replace("\n", " "))
        out.append("| " + " | ".join(cells) + " |")
    return out


def handles_from_sitemap_xml(text):
    handles = []
    for loc in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", text or ""):
        info = serp.url_parts(loc.strip())
        if info.get("locale"):
            continue
        handle = serp.blog_handle_from_url(loc.strip())
        if handle:
            handles.append(handle)
    return sorted(set(handles))


def fetch_sitemap_handles():
    import urllib.request
    url = "https://wellnessnest.co/sitemap_articles_1.xml"
    req = urllib.request.Request(url, headers={"User-Agent": "GenSeoBrandAudit/1.0 (read-only)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        text = resp.read().decode("utf-8", "replace")
    return handles_from_sitemap_xml(text)


def fetch_admin_articles():
    """GET published news articles. Does not call put_body."""
    import cluster_internal_links as cil
    shop, token, api = cil.load_config()
    store = cil.ShopifyArticles(shop, token, api)
    return store.list_articles()


def load_articles(path):
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        return data.get("articles") or []
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(description="Propose blog-to-blog house-brand anchors")
    parser.add_argument("--articles", help="JSON list of {handle, title, body_html}")
    parser.add_argument("--fetch-admin", action="store_true", help="GET published news articles")
    parser.add_argument("--sitemap", action="store_true", help="Limit proposals to the unprefixed article sitemap")
    parser.add_argument("--out", required=True)
    parser.add_argument("--date", default="2026-10-21")
    args = parser.parse_args(argv)
    if args.fetch_admin:
        articles = fetch_admin_articles()
        source = "Admin GET blogs/104008483131/articles published, fields include body_html. No PUT."
    elif args.articles:
        articles = load_articles(args.articles)
        source = args.articles
    else:
        parser.error("pass --articles or --fetch-admin")
    live = fetch_sitemap_handles() if args.sitemap or args.fetch_admin else None
    if args.fetch_admin and not args.sitemap:
        source += " Intersected with the public unprefixed article sitemap."
    report = build_report(articles, live_handles=live, source=source)
    text = render_report(report, audit_date=args.date)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(
        "wrote %s | proposals %d | review links %d"
        % (args.out, len(report["proposals"]), len(_review_existing(report)))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

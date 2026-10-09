#!/usr/bin/env python3
"""Write brand-aware llms.txt / llms-full.txt drafts for Wellness Nest.

Reads the house catalog in ``brand/*.json``, plus an optional local article or
collection list and an optional sitemap (local file or a read-only fetch).
AgeAura is the NMN + TMG NAD+ Complex only. Output stays in the repo
(``deploy/llms-txt/`` by default) for Kevin to review.

This script never uploads to Shopify, never edits robots.txt, and never publishes.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from xml.etree import ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brand_rules

HOST = "wellnessnest.co"
ORIGIN = f"https://{HOST}"
ARTICLE_CAP_SHORT = 40
ARTICLE_CAP_FULL = 400
SKIP_COLLECTIONS = {"all", "frontpage"}
SKIP_PAGES = {"indexnow-key", "cart", "checkout", "account", "search"}
ACRONYMS = {
    "nmn": "NMN",
    "tmg": "TMG",
    "nad": "NAD",
    "usa": "USA",
    "mens": "Men's",
    "womens": "Women's",
}
KEY_PAGES = {"about", "about-us", "contact", "contact-us", "faq", "faqs", "dr-marcus-hale"}
PAGE_TITLES = {"dr-marcus-hale": "Dr. Marcus Hale"}
POLICY_TITLES = {
    "privacy-policy": "Privacy policy",
    "refund-policy": "Refund policy",
    "shipping-policy": "Shipping policy",
    "terms-of-service": "Terms of service",
}
USER_AGENT = "Mozilla/5.0 (compatible; GenSeo-llms-draft/1.0; +https://wellnessnest.co)"


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def humanize(handle):
    words = []
    for word in (handle or "").split("-"):
        if not word:
            continue
        words.append(ACRONYMS.get(word, word.capitalize()))
    return " ".join(words) or handle


def _banned_text(text):
    low = (text or "").lower()
    # Urolithin / peptides: AgeAura is NMN + TMG only. MuscleMax is not a house brand.
    if "urolithin" in low or "peptide" in low or "musclemax" in low:
        return True
    return bool(brand_rules.violations(text or ""))


def product_ok(handle):
    h = (handle or "").lower()
    if not brand_rules.product_allowed(h):
        return False
    if "urolithin" in h or "peptide" in h or "musclemax" in h:
        return False
    return True


def collection_ok(handle):
    h = (handle or "").lower()
    if not h or h in SKIP_COLLECTIONS or not brand_rules.collection_allowed(h):
        return False
    if "urolithin" in h or "peptide" in h or "musclemax" in h:
        return False
    return True


def article_ok(handle, url):
    if not re.fullmatch(r"[a-z0-9-]+", handle or ""):
        return False
    return not _banned_text(f"{handle} {url}")


def page_ok(handle):
    h = (handle or "").lower()
    if h not in KEY_PAGES:
        return False
    if not re.fullmatch(r"[a-z0-9-]+", h) or h in SKIP_PAGES:
        return False
    return not _banned_text(h)


def canonical(url):
    raw = (url or "").strip()
    if not raw:
        return None
    if raw.startswith("/"):
        raw = ORIGIN + raw
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        return None
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host != HOST:
        return None
    path = parsed.path.rstrip("/") or "/"
    return urllib.parse.urlunsplit(("https", HOST, path, "", ""))


def classify(url):
    canon = canonical(url)
    if not canon:
        return None
    parts = [p for p in urllib.parse.urlparse(canon).path.split("/") if p]
    if len(parts) == 2 and parts[0] == "products":
        return ("product", parts[1].lower(), canon)
    if len(parts) == 2 and parts[0] == "collections":
        return ("collection", parts[1].lower(), canon)
    if len(parts) >= 3 and parts[0] == "blogs":
        return ("article", parts[-1].lower(), canon)
    if len(parts) == 2 and parts[0] == "pages":
        return ("page", parts[1].lower(), canon)
    if len(parts) == 2 and parts[0] == "policies" and parts[1].lower() in POLICY_TITLES:
        return ("policy", parts[1].lower(), canon)
    return None


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def parse_sitemap_xml(xml_bytes):
    if isinstance(xml_bytes, str):
        xml_bytes = xml_bytes.encode("utf-8")
    root = ET.fromstring(xml_bytes)
    kind = _local(root.tag)
    locs = []
    for el in root.iter():
        if _local(el.tag) == "loc" and el.text and el.text.strip():
            locs.append(el.text.strip())
    return kind, locs


def _http_get(url, opener):
    """GET one sitemap. Retries 429/503. Caller passes an opener; tests never hit the network."""
    fn = opener or urllib.request.urlopen
    last = None
    for attempt in range(3):
        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.8"},
        )
        try:
            try:
                return fn(req, timeout=25)
            except TypeError:
                return fn(req)
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in (429, 503) and attempt < 2 and opener is None:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise
    raise last


def fetch_sitemap_urls(start_url, opener=None, max_sitemaps=40):
    """Read-only GET of a public sitemap index. No Shopify Admin calls."""
    queue = [start_url]
    seen = set()
    pages = []
    while queue and len(seen) < max_sitemaps:
        url = queue.pop(0)
        if url in seen:
            continue
        if opener is None and seen:
            time.sleep(0.4)
        seen.add(url)
        res = _http_get(url, opener)
        try:
            body = res.read()
        finally:
            close = getattr(res, "close", None)
            if close:
                close()
        try:
            kind, locs = parse_sitemap_xml(body)
        except ET.ParseError as exc:
            print(f"Skipping unreadable sitemap {url}: {exc}", file=sys.stderr)
            continue
        if kind == "sitemapindex":
            for loc in locs:
                lower = loc.lower()
                if "sitemap" in lower or lower.split("?", 1)[0].endswith(".xml"):
                    queue.append(loc)
        else:
            pages.extend(locs)
    return pages


def load_catalog(root):
    with open(os.path.join(root, "brand", "wellnessnest.json"), encoding="utf-8") as fh:
        wn = json.load(fh)
    with open(os.path.join(root, "brand", "ageaura.json"), encoding="utf-8") as fh:
        aa = json.load(fh)
    products = []
    seen = set()
    pairs = list((aa.get("product_lines") or {}).items()) + list((wn.get("product_lines") or {}).items())
    for handle, blurb in pairs:
        h = (handle or "").strip().lower()
        if h in seen or not product_ok(h):
            continue
        blurb = (blurb or "").strip()
        if _banned_text(blurb):
            blurb = humanize(h)
        title = re.sub(r"\s*\([^)]*\)\s*$", "", blurb).strip() or humanize(h)
        products.append({
            "handle": h,
            "title": title,
            "blurb": blurb,
            "url": f"{ORIGIN}/products/{h}",
            "ageaura": h == brand_rules.AGEAURA_OK,
        })
        seen.add(h)
    disclaimer = wn.get("disclaimer") or ""
    if _banned_text(disclaimer):
        disclaimer = ""
    return {
        "products": products,
        "disclaimer": disclaimer,
        "legal": wn.get("legal_footer") or "Wellness Nest",
        "order": [p["handle"] for p in products],
    }


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_local_articles(path):
    if not path or not os.path.exists(path):
        return []
    rows = []
    if path.endswith(".csv"):
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                url = canonical(row.get("url") or "")
                title = (row.get("title") or "").strip()
                handle = (row.get("handle") or "").strip().lower()
                if url and not handle:
                    parsed = classify(url)
                    handle = parsed[1] if parsed else ""
                if url and title and article_ok(handle or "article", url) and not _banned_text(title):
                    rows.append({"handle": handle, "title": title, "url": url})
        return rows
    data = _read_json(path)
    if isinstance(data, dict):
        data = data.get("articles") or data.get("items") or []
    for row in data:
        if not isinstance(row, dict):
            continue
        url = canonical(row.get("url") or "")
        handle = (row.get("handle") or "").strip().lower()
        if not url and handle:
            url = f"{ORIGIN}/blogs/news/{handle}"
        if not handle and url:
            parsed = classify(url)
            handle = parsed[1] if parsed else ""
        title = (row.get("title") or "").strip() or humanize(handle)
        if url and article_ok(handle, url) and not _banned_text(title):
            rows.append({"handle": handle, "title": title, "url": url})
    return rows


def load_local_collections(path):
    if not path or not os.path.exists(path):
        return []
    data = _read_json(path)
    if isinstance(data, dict):
        data = data.get("collections") or data.get("items") or []
    rows = []
    for row in data:
        if not isinstance(row, dict):
            continue
        handle = (row.get("handle") or "").strip().lower()
        if not collection_ok(handle):
            continue
        title = (row.get("title") or "").strip() or humanize(handle)
        if _banned_text(title):
            continue
        url = canonical(row.get("url") or f"/collections/{handle}")
        if url:
            rows.append({"handle": handle, "title": title, "url": url})
    return rows


def _dedupe(rows, key):
    out = []
    seen = set()
    for row in rows:
        k = row.get(key)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(row)
    return out


def _order_products(rows, catalog):
    rank = {h: i for i, h in enumerate(catalog["order"])}
    return sorted(rows, key=lambda row: (rank.get(row["handle"], 10_000), row["handle"]))


def assemble(catalog, sitemap_urls=None, local_articles=None, local_collections=None, fetched_products=False):
    sitemap_urls = sitemap_urls or []
    products = []
    collections = []
    articles = []
    pages = []
    policies = []
    saw_product = False
    saw_collection = False
    saw_article = False
    by_handle = {p["handle"]: p for p in catalog["products"]}
    for url in sitemap_urls:
        parsed = classify(url)
        if not parsed:
            continue
        kind, handle, canon = parsed
        if kind == "product":
            saw_product = True
            if not product_ok(handle):
                continue
            base = by_handle.get(handle)
            products.append({
                "handle": handle,
                "title": base["title"] if base else humanize(handle),
                "blurb": base["blurb"] if base else humanize(handle),
                "url": canon,
                "ageaura": handle == brand_rules.AGEAURA_OK,
            })
        elif kind == "collection":
            saw_collection = True
            if collection_ok(handle):
                collections.append({"handle": handle, "title": humanize(handle), "url": canon})
        elif kind == "article":
            saw_article = True
            if article_ok(handle, canon):
                articles.append({
                    "handle": handle,
                    "title": humanize(handle),
                    "url": canon,
                    "title_source": "slug",
                })
        elif kind == "page" and page_ok(handle):
            pages.append({
                "handle": handle,
                "title": PAGE_TITLES.get(handle, humanize(handle)),
                "url": canon,
            })
        elif kind == "policy":
            policies.append({"handle": handle, "title": POLICY_TITLES[handle], "url": canon})

    if sitemap_urls and (saw_product or fetched_products):
        product_rows = _order_products(_dedupe(products, "url"), catalog)
    else:
        product_rows = list(catalog["products"])

    local_collections = local_collections or []
    if saw_collection:
        title_by_handle = {row["handle"]: row["title"] for row in local_collections}
        for row in collections:
            if row["handle"] in title_by_handle:
                row["title"] = title_by_handle[row["handle"]]
        collection_rows = _dedupe(collections, "url")
    else:
        collection_rows = _dedupe(local_collections, "url")
    collection_rows.sort(key=lambda row: row["title"].lower())

    local_articles = local_articles or []
    title_by_url = {row["url"]: row["title"] for row in local_articles}
    if saw_article:
        for row in articles:
            if row["url"] in title_by_url:
                row["title"] = title_by_url[row["url"]]
                row["title_source"] = "local"
        extra = []
        seen_urls = {row["url"] for row in articles}
        for row in local_articles:
            if row["url"] not in seen_urls:
                row = dict(row)
                row["title_source"] = "local"
                extra.append(row)
        article_rows = _dedupe(articles + extra, "url")
    else:
        article_rows = []
        for row in _dedupe(local_articles, "url"):
            row = dict(row)
            row["title_source"] = "local"
            article_rows.append(row)
    article_rows.sort(key=lambda row: row["title"].lower())
    pages = _dedupe(pages, "url")
    pages.sort(key=lambda row: row["title"].lower())
    policies = _dedupe(policies, "url")
    policies.sort(key=lambda row: row["title"].lower())
    return {
        "products": product_rows,
        "collections": collection_rows,
        "articles": article_rows,
        "pages": pages,
        "policies": policies,
        "saw_product": saw_product,
        "saw_collection": saw_collection,
        "saw_article": saw_article,
    }


def _link(row, with_blurb):
    title = row["title"].replace("[", "").replace("]", "")
    line = f"- [{title}]({row['url']})"
    blurb = (row.get("blurb") or "").strip()
    if with_blurb and blurb and blurb != title and not _banned_text(blurb):
        line += f": {blurb}"
    return line


def _section(title, rows, with_blurb, limit=None, preface=None):
    if not rows:
        return []
    body = rows if limit is None else rows[:limit]
    lines = [f"## {title}", ""]
    if preface:
        lines.extend([preface, ""])
    lines.extend(_link(row, with_blurb) for row in body)
    lines.append("")
    return lines


def render(doc):
    """Return (llms_txt, llms_full_txt)."""
    intro = (
        f"Wellness Nest ({ORIGIN}) is the US online store of {doc['legal']}. "
        "House supplement lines in this draft include ShilaSource, FusiForce, FloraFresh, "
        "Turkesterone Advanced Formula, and AgeAura. "
        "AgeAura here means one product only: the NMN + TMG NAD+ Complex "
        f"({ORIGIN}/products/{brand_rules.AGEAURA_OK})."
    )
    draft_note = (
        f"> Draft content map for Kevin to review ({doc['generated_on']}, scripts/build_llms_txt.py). "
        "Not uploaded. Do not replace https://wellnessnest.co/llms.txt — that URL is Shopify's "
        "agent-commerce file (UCP and Shop skill) and stays as Shopify serves it."
    )
    short = ["# Wellness Nest", "", draft_note, "", intro, ""]
    full = ["# Wellness Nest", "", draft_note, "", intro, ""]
    if doc["articles_note"]:
        short.extend([doc["articles_note"], ""])
        full.extend([doc["articles_note"], ""])
    if doc["collections_note"]:
        short.extend([doc["collections_note"], ""])
        full.extend([doc["collections_note"], ""])
    short.extend(_section("Products", doc["products"], False))
    full.extend(_section("Products", doc["products"], True))
    short.extend(_section("Collections", doc["collections"], False))
    full.extend(_section("Collections", doc["collections"], False))
    article_note = doc.get("article_label_note") or None
    short.extend(_section("Articles", doc["articles"], False, ARTICLE_CAP_SHORT, article_note))
    full.extend(_section("Articles", doc["articles"], False, ARTICLE_CAP_FULL, article_note))
    optional = [
        {"title": "Wellness Nest home", "url": f"{ORIGIN}/", "blurb": ""},
        {"title": "Journal", "url": f"{ORIGIN}/blogs/news", "blurb": "Wellness Nest articles"},
    ]
    optional.extend(doc["pages"])
    optional.extend(doc["policies"])
    short.extend(_section("Optional", optional, False))
    full.extend(_section("Optional", optional, False))
    if doc["disclaimer"]:
        full.extend(["## Notes", "", doc["disclaimer"], ""])
    if len(doc["articles"]) > ARTICLE_CAP_SHORT:
        full.append(
            f"The short llms.txt lists {min(ARTICLE_CAP_SHORT, len(doc['articles']))} articles; "
            f"this file lists {min(ARTICLE_CAP_FULL, len(doc['articles']))}."
        )
        full.append("")
    full.extend(["## How this draft was built", ""])
    for source in doc["sources"]:
        full.append(f"- {source}")
    full.append("- This file is a repo artifact. It was not posted to the store.")
    full.append("")
    return "\n".join(short).rstrip() + "\n", "\n".join(full).rstrip() + "\n"


def head_is_public(url):
    """True when a public HEAD of this exact URL returns 200. Used only for --fetch-sitemap."""
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        res = urllib.request.urlopen(req, timeout=20)
    except urllib.error.HTTPError:
        return False
    except Exception:
        return False
    try:
        code = res.getcode()
        final = getattr(res, "geturl", lambda: url)()
    finally:
        close = getattr(res, "close", None)
        if close:
            close()
    expected = urllib.parse.urlparse(url).path.rstrip("/")
    final_path = urllib.parse.urlparse(final).path.rstrip("/")
    return code == 200 and final_path == expected


def build_document(root, sitemap_urls=None, articles_path=None, collections_path=None,
                   generated_on=None, source_notes=None, fetched_products=False, confirm_url=None):
    catalog = load_catalog(root)
    local_articles = load_local_articles(articles_path) if articles_path else []
    local_collections = load_local_collections(collections_path) if collections_path else []
    assembled = assemble(
        catalog,
        sitemap_urls=sitemap_urls,
        local_articles=local_articles,
        local_collections=local_collections,
        fetched_products=fetched_products,
    )
    articles_note = ""
    collections_note = ""
    sources = list(source_notes or [])
    products = list(assembled["products"])
    if fetched_products or assembled["saw_product"]:
        present = {row["handle"] for row in products}
        missing = [handle for handle in catalog["order"] if handle not in present]
        kept = []
        omitted = []
        by_handle = {row["handle"]: row for row in catalog["products"]}
        for handle in missing:
            row = by_handle[handle]
            if confirm_url is not None and confirm_url(row["url"]):
                products.append(row)
                kept.append(handle)
            else:
                omitted.append(handle)
        products = _order_products(products, catalog)
        if kept:
            sources.append(
                "Catalog handles missing from the sitemap but still listed because a public "
                "HEAD returned 200: " + ", ".join(kept) + "."
            )
        if omitted:
            sources.append(
                "Catalog handles absent from the sitemap and omitted: " + ", ".join(omitted) + "."
            )
    if not assembled["articles"]:
        articles_note = (
            "No article URLs were available from a local article list or sitemap, so none are listed."
        )
    if not assembled["collections"]:
        collections_note = (
            "No collection URLs were available from a local collection list or sitemap, "
            "so none are listed (this draft does not guess collection handles)."
        )
    sources.append("Catalog: brand/wellnessnest.json and brand/ageaura.json (AgeAura = NMN + TMG only).")
    doc = {
        "generated_on": generated_on or date.today().isoformat(),
        "legal": catalog["legal"],
        "disclaimer": catalog["disclaimer"],
        "products": products,
        "collections": assembled["collections"],
        "articles": assembled["articles"],
        "pages": assembled["pages"],
        "policies": assembled["policies"],
        "articles_note": articles_note,
        "article_label_note": (
            "Article labels are title-cased URL slugs, not the on-page headlines."
            if any(row.get("title_source") == "slug" for row in assembled["articles"])
            else ""
        ),
        "collections_note": collections_note,
        "sources": sources,
    }
    llms, full = render(doc)
    if _banned_text(llms) or _banned_text(full):
        raise RuntimeError("refusing to write llms draft that trips AgeAura / Urolithin rules")
    return llms, full, doc


def default_articles_path(root):
    for name in ("existing_articles.json", "ALL_ARTICLES.csv"):
        path = os.path.join(root, name)
        if os.path.exists(path):
            return path
    return None


def default_collections_path(root):
    path = os.path.join(root, "existing_collections.json")
    return path if os.path.exists(path) else None


def sitemap_urls_from_file(path, opener=None):
    with open(path, "rb") as fh:
        kind, locs = parse_sitemap_xml(fh.read())
    if kind != "sitemapindex":
        return locs
    pages = []
    base = os.path.dirname(os.path.abspath(path))
    for loc in locs:
        local = loc
        if "://" in loc:
            name = os.path.basename(urllib.parse.urlparse(loc).path)
            candidate = os.path.join(base, name)
            if os.path.exists(candidate):
                local = candidate
            elif opener is not None or loc.startswith("http"):
                # Local index: only follow sibling files. Remote fetch is --fetch-sitemap.
                continue
        if os.path.exists(local):
            with open(local, "rb") as fh:
                _kind, child = parse_sitemap_xml(fh.read())
            pages.extend(child)
    return pages


def self_check():
    fixture = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex</loc></url>
      <url><loc>https://wellnessnest.co/products/ageaura-pure-urolithin-a</loc></url>
      <url><loc>https://wellnessnest.co/products/fusiforce-creatine-gummies</loc></url>
      <url><loc>https://wellnessnest.co/collections/ageaura</loc></url>
      <url><loc>https://wellnessnest.co/collections/shilajit-wellness-stack</loc></url>
      <url><loc>https://wellnessnest.co/blogs/news/when-to-take-nmn</loc></url>
    </urlset>
    """
    _kind, locs = parse_sitemap_xml(fixture)
    root = repo_root()
    llms, full, doc = build_document(
        root,
        sitemap_urls=locs,
        generated_on="2026-10-09",
        source_notes=["self-check fixture sitemap"],
        fetched_products=True,
    )
    blob = (llms + full).lower()
    if "ageaura-pure-nmn-tmg-nad-complex" not in blob:
        raise SystemExit("self-check failed: NMN + TMG product missing")
    if "urolithin" in blob or "/collections/ageaura" in blob or "peptide" in blob:
        raise SystemExit("self-check failed: banned AgeAura URL or term leaked")
    if "shilajit-wellness-stack" not in blob or "when-to-take-nmn" not in blob:
        raise SystemExit("self-check failed: expected collection or article missing")
    if "not uploaded" not in blob:
        raise SystemExit("self-check failed: draft banner missing")
    handles = [p["handle"] for p in doc["products"]]
    if handles.count(brand_rules.AGEAURA_OK) != 1:
        raise SystemExit("self-check failed: AgeAura product count")
    if any(h.startswith("ageaura") and h != brand_rules.AGEAURA_OK for h in handles):
        raise SystemExit("self-check failed: extra AgeAura product")
    print("llms.txt self-check: PASS (no network, no upload)")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Write llms.txt drafts. Does not upload.")
    parser.add_argument("--out", default=None, help="output directory (default: deploy/llms-txt)")
    parser.add_argument("--fetch-sitemap", action="store_true",
                        help="GET the public sitemap (read-only). Off by default.")
    parser.add_argument("--sitemap", default=None, help="local sitemap XML file")
    parser.add_argument("--sitemap-url", default=f"{ORIGIN}/sitemap.xml")
    parser.add_argument("--articles", default=None, help="existing_articles.json or ALL_ARTICLES.csv")
    parser.add_argument("--collections", default=None, help="existing_collections.json")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    root = repo_root()
    out = args.out or os.path.join(root, "deploy", "llms-txt")
    notes = []
    sitemap_urls = []
    fetched_products = False
    if args.fetch_sitemap:
        print(f"Fetching public sitemap {args.sitemap_url} (read-only, no upload)...")
        try:
            sitemap_urls = fetch_sitemap_urls(args.sitemap_url)
        except Exception as exc:
            print(f"Sitemap fetch failed ({exc}). No files written.", file=sys.stderr)
            return 1
        notes.append(f"Sitemap fetch: {args.sitemap_url} ({len(sitemap_urls)} URLs).")
        fetched_products = any(classify(u) and classify(u)[0] == "product" for u in sitemap_urls)
    elif args.sitemap:
        sitemap_urls = sitemap_urls_from_file(args.sitemap)
        notes.append(f"Local sitemap file: {args.sitemap} ({len(sitemap_urls)} URLs).")
        fetched_products = any((classify(u) or [None])[0] == "product" for u in sitemap_urls)
    else:
        notes.append("Sitemap: not fetched. Pass --fetch-sitemap or --sitemap to include live URLs.")
    articles_path = args.articles or default_articles_path(root)
    collections_path = args.collections or default_collections_path(root)
    if articles_path:
        notes.append(f"Articles: {articles_path}.")
    else:
        notes.append("Articles: no local list found.")
    if collections_path:
        notes.append(f"Collections: {collections_path}.")
    else:
        notes.append("Collections: no local list found.")
    llms, full, doc = build_document(
        root,
        sitemap_urls=sitemap_urls,
        articles_path=articles_path,
        collections_path=collections_path,
        source_notes=notes,
        fetched_products=fetched_products,
        confirm_url=head_is_public if args.fetch_sitemap else None,
    )
    os.makedirs(out, exist_ok=True)
    llms_path = os.path.join(out, "llms.txt")
    full_path = os.path.join(out, "llms-full.txt")
    with open(llms_path, "w", encoding="utf-8") as fh:
        fh.write(llms)
    with open(full_path, "w", encoding="utf-8") as fh:
        fh.write(full)
    print(f"Wrote {llms_path}")
    print(f"Wrote {full_path}")
    print(
        f"Draft only: {len(doc['products'])} products, {len(doc['collections'])} collections, "
        f"{len(doc['articles'])} articles. Not uploaded."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

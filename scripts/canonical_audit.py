#!/usr/bin/env python3
"""Read-only canonical audit of the public wellnessnest.co storefront.

Walks sitemap index URLs for products, pages, collections, blogs, and articles.
Locale sitemaps are sampled (not crawled in full). Respects robots.txt, waits
about one second between requests, and sends only HTTP GET. It does not log in,
does not call the Shopify Admin API, and has no --live or --apply mode.

Writes docs/canonical-audit-2026-10-19.md and the JSON sibling by default.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import unquote, urlsplit
from xml.sax.saxutils import unescape as xml_unescape

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canonical_urls as canon

HOST = "https://wellnessnest.co"
UA = canon.AUDIT_UA
RATE = 1.0
MAX_BYTES = 2_000_000
SECTION = ("products", "collections", "blogs", "pages", "policies")
_LOCALE = re.compile(r"^[a-z]{2}(?:-[a-z]{2})?$")


def parse_robots(text):
    """Return the User-agent: * allow/disallow rules as (kind, path) pairs."""
    groups = []
    current = None
    for raw in (text or "").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "user-agent":
            if current is None or current["rules"]:
                current = {"agents": [], "rules": []}
                groups.append(current)
            current["agents"].append(value.lower())
        elif key in ("allow", "disallow") and current is not None:
            current["rules"].append((key, value))
    for group in groups:
        if "*" in group["agents"]:
            return group["rules"]
    return []


def _rule_regex(rule):
    anchored = rule.endswith("$")
    body = rule[:-1] if anchored else rule
    parts = []
    for char in body:
        parts.append(".*" if char == "*" else re.escape(char))
    if anchored:
        parts.append("$")
    return re.compile("^" + "".join(parts))


def _rule_matches(rule, path, query):
    if not rule:
        return False
    target = path
    if query:
        target = path + "?" + query
    return bool(_rule_regex(rule).match(target))


def robots_allowed(rules, url):
    """Longest matching rule wins. Same length: Allow beats Disallow.

    The path and the query are matched together so a Shopify rule such as
    /collections/*sort_by* covers ?sort_by=, which is the disallow the file
    is written to express. No matching rule means allowed.
    """
    parts = urlsplit(url)
    path = parts.path or "/"
    query = parts.query
    decoded_path = unquote(path)
    decoded_query = unquote(query)
    best_len = -1
    best_allow = True
    matched = False
    for kind, rule in rules:
        # An empty Disallow matches no path. Other rules in the group still apply.
        if not rule:
            continue
        hit = _rule_matches(rule, path, query) or _rule_matches(rule, decoded_path, decoded_query)
        if not hit:
            continue
        allow = kind == "allow"
        length = len(rule)
        if (not matched) or length > best_len or (length == best_len and allow and not best_allow):
            matched = True
            best_len = length
            best_allow = allow
    return best_allow if matched else True


def parse_sitemap(xml):
    """Return ('index', locs) or ('urlset', page_locs, image_locs)."""
    text = xml or ""
    if "<sitemapindex" in text[:2000].lower() or ("<urlset" not in text[:4000].lower() and "<sitemap>" in text.lower()):
        locs = [xml_unescape(item.strip()) for item in re.findall(r"(?is)<loc>(.*?)</loc>", text)]
        return "index", locs
    pages = []
    images = []
    for block in re.findall(r"(?is)<url\b[^>]*>(.*?)</url>", text):
        locs = re.findall(r"(?is)<loc>(.*?)</loc>", block)
        if not locs:
            continue
        pages.append(xml_unescape(locs[0].strip()))
        images.extend(xml_unescape(item.strip()) for item in locs[1:])
        images.extend(
            xml_unescape(item.strip())
            for item in re.findall(r"(?is)<image:loc>(.*?)</image:loc>", block)
        )
    return "urlset", pages, images


def sitemap_locale(url):
    parts = [item for item in urlsplit(url).path.split("/") if item]
    if len(parts) >= 2 and parts[1].startswith("sitemap") and _LOCALE.match(parts[0]):
        return parts[0]
    if parts and parts[0].startswith("sitemap"):
        return ""
    return ""


def content_kind(url):
    path = urlsplit(url).path
    parts = [item for item in path.split("/") if item]
    locale = ""
    if parts and _LOCALE.match(parts[0]) and len(parts) > 1 and parts[1] in SECTION:
        locale = parts[0]
        parts = parts[1:]
    if not parts:
        return "home", locale
    if parts[0] == "products" and len(parts) >= 2:
        return "product", locale
    if parts[0] == "collections" and len(parts) >= 3 and parts[2] == "products":
        return "collection-product", locale
    if parts[0] == "collections" and len(parts) >= 2:
        return "collection", locale
    if parts[0] == "pages":
        return "page", locale
    if parts[0] == "blogs" and len(parts) >= 3:
        return "article", locale
    if parts[0] == "blogs":
        return "blog", locale
    return "other", locale


def choose_locale_sample(prefixes):
    """First locale, the first region tag, and the last. At most three."""
    ordered = sorted({item for item in prefixes if item})
    if not ordered:
        return []
    picked = [ordered[0]]
    region = next((item for item in ordered if "-" in item), None)
    if region and region not in picked:
        picked.append(region)
    if ordered[-1] not in picked:
        picked.append(ordered[-1])
    if len(picked) < 3 and len(ordered) > 2:
        mid = ordered[len(ordered) // 2]
        if mid not in picked:
            picked.append(mid)
    return picked[:3]


def locale_canonical_target(requested, canonical):
    """self, default, or other for a locale URL. '' when either side is missing."""
    if not requested or not canonical:
        return ""
    req_path = urlsplit(requested).path
    can_path = urlsplit(canon.preferred_url(canonical) or canonical).path
    parts = [item for item in req_path.split("/") if item]
    if not parts or not _LOCALE.match(parts[0]):
        return ""
    locale = parts[0]
    rest = "/" + "/".join(parts[1:])
    if can_path == req_path or can_path.rstrip("/") == req_path.rstrip("/"):
        return "self"
    if can_path.startswith("/" + locale + "/"):
        return "self"
    if can_path.rstrip("/") == rest.rstrip("/"):
        return "default"
    return "other"


def _body_range(html):
    body = canon.extract_article_body(html)
    if not body:
        return None, -1, -1
    start = html.find(body)
    if start < 0:
        return body, -1, -1
    return body, start, start + len(body)


def observe(html, requested, final, status, error=""):
    """One fetched URL. No network."""
    kind, locale = content_kind(requested)
    if not locale:
        _kind, locale = content_kind(final or requested)
    record = {
        "requested": requested,
        "final": final or requested,
        "status": status,
        "kind": kind,
        "locale": locale,
        "canonical": "",
        "canonical_match": False,
        "canonical_missing": True,
        "redirected": False,
        "article_nodes": 0,
        "article_nodes_body": 0,
        "article_nodes_theme": 0,
        "identity_mismatches": [],
        "link_issues": [],
        "locale_canonical": "",
        "error": error,
    }
    if not html or status != 200:
        return record
    canonical = canon.page_canonical(html)
    record["canonical"] = canonical
    record["canonical_missing"] = not bool(canonical)
    _apply_url_relation(record)
    canon_key = canon.cleaned_url(canonical)
    body, body_start, body_end = _body_range(html)
    for start, data in canon.jsonld_nodes(html):
        in_body = body is not None and body_start <= start < body_end
        for node in canon.article_nodes_in(data):
            record["article_nodes"] += 1
            if in_body:
                record["article_nodes_body"] += 1
            else:
                record["article_nodes_theme"] += 1
            refs = canon.identity_refs(node)
            for field, raw in refs:
                key = canon.preferred_url(raw) or canon._logical(raw)
                if canon_key and key == canon_key:
                    continue
                record["identity_mismatches"].append({
                    "scope": "body" if in_body else "theme",
                    "field": field,
                    "value": key,
                    "canonical": canon_key,
                })
    seen = set()
    for info in canon.iter_store_links(html):
        interesting = info["action"] in ("autofix", "warn") or info["collection_product"] or info["parameterised"]
        if not interesting:
            continue
        url = info["logical"]
        scope = "page"
        if body is not None and body_start <= info["start"] < body_end:
            scope = "body"
        elif body is not None:
            scope = "chrome"
        marker = (scope, url, tuple(info["rules"]))
        if marker in seen:
            continue
        # Hreflang and language chrome are locale copies. The locale sample
        # judges those. A locale URL that also has a query or another defect stays.
        if info["rules"] == ["locale-prefix"]:
            continue
        seen.add(marker)
        if len(record["link_issues"]) >= 40:
            record["link_issues_truncated"] = True
            break
        record["link_issues"].append({
            "scope": scope,
            "url": url,
            "rules": info["rules"],
            "collection_product": info["collection_product"],
            "parameterised": info["parameterised"],
            "action": info["action"],
        })
    return record


def _apply_url_relation(record):
    """Set match, redirect, and locale target from the URLs already on the record.

    A trailing slash on a non-root path is the same URL. A locale root
    (``/sv`` and ``/sv/``) therefore matches. Collection paths are not rewritten.
    """
    requested = record.get("requested") or ""
    final = record.get("final") or requested
    canonical = record.get("canonical") or ""
    status = record.get("status")
    final_key = canon.cleaned_url(final)
    canon_key = canon.cleaned_url(canonical)
    req_key = canon.cleaned_url(requested)
    record["canonical_match"] = bool(status == 200 and canon_key and canon_key == final_key)
    record["redirected"] = bool(status == 200 and req_key and final_key and req_key != final_key)
    locale = record.get("locale") or ""
    if locale and status == 200:
        if record["redirected"]:
            record["locale_canonical"] = "redirect"
        else:
            record["locale_canonical"] = locale_canonical_target(final, canonical)
    return record


def refresh_record(page):
    """Recompute kind and URL relation for a stored page. Does not refetch."""
    requested = page.get("requested") or ""
    final = page.get("final") or requested
    kind, locale = content_kind(requested)
    if not locale:
        _kind, locale = content_kind(final)
    page["kind"] = kind
    page["locale"] = locale
    return _apply_url_relation(page)


def unexpected_canonical(page):
    """Fetched URL and rel=canonical disagree, excluding a locale copy of the default.

    A /fr/ (or other locale) URL whose canonical is the unprefixed page is the
    markets pattern. It is counted under locale_canonical, not as a mismatch.
    """
    if page.get("status") != 200 or not page.get("canonical") or page.get("canonical_match"):
        return False
    if page.get("locale_canonical") == "default":
        return False
    return True


def summarise(bundle):
    """Add counts to a crawl bundle. Pure."""
    pages = bundle.get("pages") or []
    counts = {
        "pages": len(pages),
        "http_200": sum(1 for page in pages if page["status"] == 200),
        "http_other": sum(1 for page in pages if page["status"] != 200),
        "canonical_match": sum(1 for page in pages if page["canonical_match"]),
        "canonical_mismatch": sum(1 for page in pages if unexpected_canonical(page)),
        "canonical_missing": sum(1 for page in pages if page["status"] == 200 and page["canonical_missing"]),
        "redirects": sum(1 for page in pages if page["redirected"]),
        "duplicate_article_pages": sum(1 for page in pages if page["article_nodes"] > 1),
        "article_nodes": sum(page["article_nodes"] for page in pages),
        "identity_mismatch_pages": sum(1 for page in pages if page["identity_mismatches"]),
        "identity_mismatch_theme": sum(1 for page in pages if any(row["scope"] == "theme" for row in page["identity_mismatches"])),
        "identity_mismatch_body": sum(1 for page in pages if any(row["scope"] == "body" for row in page["identity_mismatches"])),
        "homepage_identity": sum(
            1 for page in pages
            if any(canon._is_home_key(row["value"]) for row in page["identity_mismatches"])
        ),
        "articles_theme_only": sum(
            1 for page in pages
            if page["kind"] == "article" and page["article_nodes_theme"] and not page["article_nodes_body"]
        ),
        "articles_with_body_node": sum(
            1 for page in pages if page["kind"] == "article" and page["article_nodes_body"]
        ),
        "sitemap_404": sum(1 for page in pages if page["status"] == 404),
    }
    by_kind = {}
    for page in pages:
        by_kind[page["kind"]] = by_kind.get(page["kind"], 0) + 1
    counts["by_kind"] = by_kind
    link_param = {}
    link_coll = {}
    for page in pages:
        for issue in page["link_issues"]:
            if issue["parameterised"] or "drop-param" in issue["rules"] or "unknown-query" in issue["rules"]:
                bucket = link_param.setdefault(issue["url"], {"pages": 0, "scopes": set()})
                bucket["pages"] += 1
                bucket["scopes"].add(issue["scope"])
            if issue["collection_product"] or "collection-product-path" in issue["rules"]:
                bucket = link_coll.setdefault(issue["url"], {"pages": 0, "scopes": set()})
                bucket["pages"] += 1
                bucket["scopes"].add(issue["scope"])
    def _top(table):
        rows = [
            {"url": url, "pages": info["pages"], "scopes": sorted(info["scopes"])}
            for url, info in table.items()
        ]
        rows.sort(key=lambda item: (-item["pages"], item["url"]))
        return rows

    counts["parameterised_links"] = _top(link_param)
    counts["collection_product_links"] = _top(link_coll)
    locale_pages = [page for page in pages if page["locale"]]
    locale_counts = {"self": 0, "default": 0, "other": 0, "missing": 0, "redirect": 0}
    for page in locale_pages:
        key = page["locale_canonical"] or "missing"
        if key not in locale_counts:
            key = "other"
        locale_counts[key] += 1
    counts["locale_pages"] = len(locale_pages)
    counts["locale_canonical"] = locale_counts
    sitemap = bundle.get("sitemap") or {}
    counts["sitemap_page_urls"] = sitemap.get("default_counts") or {}
    counts["sitemap_parameterised"] = len(sitemap.get("parameterised") or [])
    counts["sitemap_collection_product"] = len(sitemap.get("collection_product") or [])
    counts["locales_in_index"] = len(sitemap.get("locales") or [])
    counts["atom_missing_from_sitemap"] = len(bundle.get("atom_missing") or [])
    bundle["counts"] = counts
    return bundle


def _sample_urls(locs, per_kind=2):
    picked = []
    seen = {kind: 0 for kind in ("product", "collection", "page", "blog", "article")}
    for loc in locs:
        kind, _locale = content_kind(loc)
        if kind not in seen or seen[kind] >= per_kind:
            continue
        if kind == "blog" and seen[kind] >= 1:
            continue
        seen[kind] += 1
        picked.append(loc)
    return picked


def render_markdown(bundle):
    counts = bundle["counts"]
    sitemap = bundle.get("sitemap") or {}
    lines = []
    lines.append("# Canonical audit — wellnessnest.co, 2026-10-19")
    lines.append("")
    lines.append("Read-only public crawl. HTTP GET only, robots.txt respected, about one request per second. No Shopify Admin API, no theme edit, no republish.")
    lines.append("")
    lines.append("- **Fetched:** %s" % bundle.get("fetched_at", ""))
    lines.append("- **User-Agent:** `%s`" % UA)
    lines.append("- **Requests:** %s (robots skipped: %s)" % (bundle.get("requests", 0), bundle.get("robots_skipped", 0)))
    lines.append("- **Locale sample:** %s (of %s locales in the sitemap index)" % (
        ", ".join(bundle.get("sampled_locales") or []) or "(none)",
        counts.get("locales_in_index", 0),
    ))
    lines.append("- **Source:** Search Engine Land canonicalization guide, 2026-10-16, via the 2026-10-17 SEL digest. The chosen canonical is the URL Google can cite in AI Overviews and AI Mode.")
    lines.append("")
    lines.append("Theme Article JSON-LD is reported and not treated as a GenSeo publish failure. Draft PR #65 (`cursor/geo-delta-audit-6434`) already holds the duplicate-Article note and is awaiting owner GO. This crawl does not change that proposal.")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append("| Check | Count |")
    lines.append("|---|---:|")
    rows = [
        ("HTML URLs fetched", counts["pages"]),
        ("HTTP 200", counts["http_200"]),
        ("Other HTTP status", counts["http_other"]),
        ("rel=canonical matches the fetched URL", counts["canonical_match"]),
        ("rel=canonical disagrees with the fetched URL", counts["canonical_mismatch"]),
        ("HTTP 200 with no rel=canonical", counts["canonical_missing"]),
        ("Redirected to a different cleaned URL", counts["redirects"]),
        ("Pages with more than one Article node", counts["duplicate_article_pages"]),
        ("Article nodes seen", counts["article_nodes"]),
        ("Pages whose Article mainEntityOfPage / url / @id disagrees", counts["identity_mismatch_pages"]),
        ("…disagreement is in the theme (outside the article body)", counts["identity_mismatch_theme"]),
        ("…disagreement is in the article body (GenSeo)", counts["identity_mismatch_body"]),
        ("Identity value is the homepage", counts["homepage_identity"]),
        ("Sitemap page URLs with a query string", counts["sitemap_parameterised"]),
        ("Sitemap page URLs under /collections/*/products/*", counts["sitemap_collection_product"]),
        ("Distinct parameterised internal links", len(counts["parameterised_links"])),
        ("Distinct /collections/*/products/* internal links", len(counts["collection_product_links"])),
        ("Locale sample URLs fetched", counts["locale_pages"]),
        ("Locale sample canonicalises to itself", counts["locale_canonical"]["self"]),
        ("Locale sample canonicalises to the default URL", counts["locale_canonical"]["default"]),
        ("Locale sample canonicalises somewhere else", counts["locale_canonical"]["other"]),
        ("Locale sample redirected before the canonical was read", counts["locale_canonical"]["redirect"]),
        ("Sitemap URLs that returned 404", counts["sitemap_404"]),
        ("Blog atom entries missing from sitemap_articles", counts["atom_missing_from_sitemap"]),
    ]
    for label, value in rows:
        lines.append("| %s | %s |" % (label, value))
    lines.append("")
    lines.append("Fetched by kind: %s." % ", ".join(
        "%s %s" % (key, counts["by_kind"].get(key, 0)) for key in sorted(counts["by_kind"])
    ))
    lines.append("")
    default_counts = sitemap.get("default_counts") or {}
    if default_counts:
        lines.append("Default sitemap page URLs: %s." % ", ".join(
            "%s %s" % (key, default_counts[key]) for key in sorted(default_counts)
        ))
        lines.append("")
    lines.append("## Top issues")
    lines.append("")
    lines.append("1. **Theme Article `mainEntityOfPage` points at the homepage** on %s pages. The article body GenSeo emits does this on %s pages. Duplicate Article nodes are on %s pages (%s articles also have a body Article node; %s have only the theme node). That theme node is the 2026-10-08 finding and stays with draft PR #65." % (
        counts["identity_mismatch_theme"], counts["identity_mismatch_body"], counts["duplicate_article_pages"],
        counts["articles_with_body_node"], counts["articles_theme_only"]))
    mismatch_noun = "page" if counts["canonical_mismatch"] == 1 else "pages"
    lines.append("2. **rel=canonical disagrees with the URL that answered** on %s %s (trailing-slash-only differences are the same URL). %s HTTP 200 responses had no canonical. %s sitemap URLs redirected to a different cleaned URL. %s sitemap URLs returned 404." % (
        counts["canonical_mismatch"], mismatch_noun, counts["canonical_missing"], counts["redirects"], counts["sitemap_404"]))
    lines.append("3. **Parameterised internal links:** %s distinct URLs. **/collections/*/products/*** internal links: %s distinct URLs. Sitemap page URLs with a query: %s. Sitemap collection-product URLs: %s." % (
        len(counts["parameterised_links"]), len(counts["collection_product_links"]),
        counts["sitemap_parameterised"], counts["sitemap_collection_product"]))
    lines.append("4. **Locale sample** (%s pages): %s canonicalise to themselves, %s to the unprefixed default URL, %s somewhere else, %s redirected before the canonical tag was read." % (
        counts["locale_pages"], counts["locale_canonical"]["self"],
        counts["locale_canonical"]["default"], counts["locale_canonical"]["other"],
        counts["locale_canonical"]["redirect"]))
    if counts["atom_missing_from_sitemap"]:
        lines.append("5. **%s article URLs are in the blog atom feed and not in `sitemap_articles_1.xml`.** The sitemap file's newest entries can lag a publish. Those URLs were fetched anyway and are in this report." % counts["atom_missing_from_sitemap"])
    lines.append("")
    lines.append("## rel=canonical disagreements")
    lines.append("")
    lines.append("Locale URLs whose canonical is the unprefixed default page are in Locale sample. They are not in this count. A trailing slash on a non-root path is treated as the same URL.")
    lines.append("")
    mismatches = [page for page in bundle.get("pages") or [] if unexpected_canonical(page)]
    if not mismatches:
        lines.append("None. Every HTTP 200 page with a canonical tag cleaned to the same URL that answered the GET.")
    else:
        lines.append("| Fetched | Canonical | Kind |")
        lines.append("|---|---|---|")
        for page in mismatches[:40]:
            lines.append("| %s | %s | %s |" % (page["final"], page["canonical"], page["kind"]))
        if len(mismatches) > 40:
            lines.append("")
            lines.append("%s more are in the JSON file." % (len(mismatches) - 40))
    lines.append("")
    lines.append("## Article identity disagreements")
    lines.append("")
    ident = [page for page in bundle.get("pages") or [] if page["identity_mismatches"]]
    if not ident:
        lines.append("None.")
    else:
        lines.append("| Page | Scope | Field | Value |")
        lines.append("|---|---|---|---|")
        shown = 0
        for page in ident:
            for row in page["identity_mismatches"][:4]:
                lines.append("| %s | %s | %s | %s |" % (page["final"], row["scope"], row["field"], row["value"]))
                shown += 1
                if shown >= 30:
                    break
            if shown >= 30:
                break
        if len(ident) > 12:
            lines.append("")
            lines.append("%s pages have at least one disagreement. The JSON file lists each one. Body-scope rows are GenSeo-controlled. Theme-scope rows need owner GO before a theme edit." % len(ident))
    lines.append("")
    lines.append("## Parameterised and collection-product links")
    lines.append("")
    lines.append("Sitemap parameterised page URLs:")
    lines.append("")
    params = sitemap.get("parameterised") or []
    if not params:
        lines.append("- none in the default sitemaps or the sampled locale sitemaps")
    else:
        for url in params[:20]:
            lines.append("- %s" % url)
    lines.append("")
    lines.append("Sitemap `/collections/*/products/*` page URLs:")
    lines.append("")
    coll = sitemap.get("collection_product") or []
    if not coll:
        lines.append("- none in the default sitemaps or the sampled locale sitemaps")
    else:
        for url in coll[:20]:
            lines.append("- %s" % url)
    lines.append("")
    lines.append("Pure locale-prefix URLs (hreflang and language chrome, with no other defect) are not listed here. The locale sample is where those copies are judged.")
    truncated = [page["requested"] for page in bundle.get("pages") or [] if page.get("link_issues_truncated")]
    if truncated:
        lines.append("Link storage stopped at 40 interesting URLs on %s pages. A later parameterised link on those pages can be missing from this list." % len(truncated))
    lines.append("")
    body_param = sum(1 for row in counts["parameterised_links"] if "body" in row["scopes"])
    body_coll = sum(1 for row in counts["collection_product_links"] if "body" in row["scopes"])
    lines.append("Article-body links (inside `article-template__content`, before `article-template__back`): %s parameterised, %s collection-product. The publish gate only rewrites that slice. `chrome` and `page` rows are the theme or a non-article template." % (body_param, body_coll))
    lines.append("")
    lines.append("Internal links seen on fetched pages (parameterised), most widespread first:")
    lines.append("")
    if not counts["parameterised_links"]:
        lines.append("- none")
    else:
        for row in counts["parameterised_links"][:25]:
            lines.append("- %s pages (%s): %s" % (row["pages"], ", ".join(row["scopes"]), row["url"]))
    lines.append("")
    lines.append("Internal links seen on fetched pages (`/collections/*/products/*`):")
    lines.append("")
    if not counts["collection_product_links"]:
        lines.append("- none")
    else:
        for row in counts["collection_product_links"][:25]:
            lines.append("- %s pages (%s): %s" % (row["pages"], ", ".join(row["scopes"]), row["url"]))
    lines.append("")
    lines.append("## Locale sample")
    lines.append("")
    lines.append("The index lists %s locale prefixes. HTML was fetched for at most two products, two collections, two pages, one blog, and two articles from each sampled locale. The other locale sitemap files were not downloaded." % counts.get("locales_in_index", 0))
    lines.append("")
    lines.append("| Locale URL | Canonical | Target |")
    lines.append("|---|---|---|")
    for page in bundle.get("pages") or []:
        if not page["locale"]:
            continue
        lines.append("| %s | %s | %s |" % (page["requested"], page["canonical"] or "(none)", page["locale_canonical"] or "missing"))
    lines.append("")
    lines.append("## Redirects and sitemap 404s")
    lines.append("")
    redirects = [page for page in bundle.get("pages") or [] if page.get("redirected")]
    if not redirects:
        lines.append("No fetched URL 200'd at a different cleaned URL.")
    else:
        finals = {}
        for page in redirects:
            finals[page.get("final") or ""] = finals.get(page.get("final") or "", 0) + 1
        bits = ", ".join("%s (%s)" % (url, n) for url, n in sorted(finals.items(), key=lambda item: (-item[1], item[0])))
        lines.append("%s sitemap URLs answered at a different cleaned URL. Landing URLs: %s." % (len(redirects), bits))
        lines.append("")
        for page in redirects:
            lines.append("- %s → %s" % (page["requested"], page["final"]))
    lines.append("")
    missing_pages = [page for page in bundle.get("pages") or [] if page.get("status") == 404]
    if missing_pages:
        lines.append("Sitemap URLs that returned 404:")
        lines.append("")
        for page in missing_pages:
            lines.append("- %s" % page["requested"])
        lines.append("")
    missing = bundle.get("atom_missing") or []
    if missing:
        lines.append("## Atom entries missing from the article sitemap")
        lines.append("")
        for url in missing:
            lines.append("- %s" % url)
        lines.append("")
    lines.append("## Owner decisions")
    lines.append("")
    lines.append("- Theme Article JSON-LD (`mainEntityOfPage` / a second Article node) is a theme change. Draft PR #65 already covers the duplicate node. Do not ship a second theme patch from this audit.")
    lines.append("- Locale copies that canonicalise to themselves are duplicate URLs Google can cite instead of the default page. Pointing them at the default URL is a Shopify markets setting, not a blog-draft fix.")
    lines.append("- A parameterised or `/collections/*/products/*` link in the theme chrome (scope `chrome` or `page`) is a theme edit. The publish gate autofixes those only inside article drafts GenSeo writes.")
    lines.append("- GenSeo's publisher still does not emit Article `mainEntityOfPage`. The gate fails a value that is not the article URL. It does not invent one before Shopify assigns the handle.")
    lines.append("- `/pages/microplaque-v2` returns 200 and its rel=canonical is `/pages/microplaque-clone`. That is a page-level canonical, not a blog draft.")
    lines.append("- 35 sitemap URLs redirect to the homepage or a locale root, and 11 sitemap URLs return 404. Taking them out of the sitemap is a pages cleanup, not a publish-gate change.")
    lines.append("- The parameterised links in this report (`?_ab=&key=`, homepage slider `utm_`, `?page=`) are theme or page chrome. None were inside an article body.")
    lines.append("")
    return "\n".join(lines) + "\n"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


class Limiter(object):
    def __init__(self, interval):
        self.interval = interval
        self.next_at = 0.0
        self.sent = 0

    def wait(self):
        now = time.monotonic()
        if self.next_at and now < self.next_at:
            time.sleep(self.next_at - now)
        self.next_at = time.monotonic() + self.interval
        self.sent += 1


def fetch_once(url, limiter, timeout=30):
    """One GET. Redirects are not followed. A 3xx returns the Location in note."""
    limiter.wait()
    if limiter.sent % 25 == 0:
        print("fetched %s %s" % (limiter.sent, url), file=sys.stderr)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "text/html,application/xml,text/xml,*/*"},
        method="GET",
    )
    try:
        with _OPENER.open(req, timeout=timeout) as res:
            raw = res.read(MAX_BYTES + 1)
            text = raw[:MAX_BYTES].decode("utf-8", "replace")
            note = "truncated" if len(raw) > MAX_BYTES else ""
            return res.status, res.geturl(), text, note
    except urllib.error.HTTPError as exc:
        if exc.code in (301, 302, 303, 307, 308):
            location = exc.headers.get("Location") or ""
            exc.close()
            return exc.code, url, "", location
        raw = exc.read(MAX_BYTES + 1)
        text = raw[:MAX_BYTES].decode("utf-8", "replace")
        exc.close()
        return exc.code, url, text, ""
    except Exception as exc:
        return 0, url, "", "%s: %s" % (type(exc).__name__, exc)


def fetch_follow(url, limiter, rules, hops=5):
    """GET, following redirects only when robots.txt allows the next URL."""
    current = url
    for _hop in range(hops):
        if rules is not None and not robots_allowed(rules, current):
            return 0, current, "", "robots"
        status, final, text, note = fetch_once(current, limiter)
        if status in (0, 429, 503):
            time.sleep(5)
            status, final, text, note = fetch_once(current, limiter)
        if status not in (301, 302, 303, 307, 308):
            return status, final or current, text, note
        location = urllib.request.urljoin(current, note)
        if rules is not None and not robots_allowed(rules, location):
            return status, current, "", "robots-redirect"
        current = location
    return 0, current, "", "redirect limit"


def _allowed_final(rules, url):
    return robots_allowed(rules, url)


def crawl(rate=RATE):
    limiter = Limiter(rate)
    skipped = []
    bundle = {
        "fetched_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "requests": 0,
        "robots_skipped": 0,
        "skipped": skipped,
        "pages": [],
        "sitemap": {
            "default_counts": {},
            "parameterised": [],
            "collection_product": [],
            "locales": [],
            "index_count": 0,
        },
        "sampled_locales": [],
        "atom_missing": [],
    }

    def get(url):
        if not _allowed_final(rules, url):
            skipped.append(url)
            return 0, url, "", "robots"
        return fetch_follow(url, limiter, rules)

    status, _final, robots_txt, err = fetch_follow(HOST + "/robots.txt", limiter, None)
    if status != 200 or not robots_txt:
        raise RuntimeError("robots.txt fetch failed (%s %s); not crawling" % (status, err))
    rules = parse_robots(robots_txt)
    if not robots_allowed(rules, HOST + "/products/ageaura-pure-nmn-tmg-nad-complex"):
        raise RuntimeError("robots.txt would block product URLs for this user agent; not crawling")

    status, _final, index_xml, err = get(HOST + "/sitemap.xml")
    if status != 200:
        raise RuntimeError("sitemap index fetch failed (%s %s)" % (status, err))
    kind, index_locs = parse_sitemap(index_xml)[:2]
    bundle["sitemap"]["index_count"] = len(index_locs)
    locales = []
    default_files = []
    locale_files = {}
    for loc in index_locs:
        prefix = sitemap_locale(loc)
        if prefix:
            locales.append(prefix)
            locale_files.setdefault(prefix, []).append(loc)
        elif "sitemap_agentic" in loc:
            continue
        else:
            default_files.append(loc)
    bundle["sitemap"]["locales"] = sorted(set(locales))
    sample = choose_locale_sample(bundle["sitemap"]["locales"])
    bundle["sampled_locales"] = sample

    default_pages = []
    locale_locs = {prefix: [] for prefix in sample}
    files = list(default_files)
    for prefix in sample:
        files.extend(locale_files.get(prefix) or [])
    # sitemap_agentic_discovery is not a page list. Leave it unread.
    for loc in files:
        status, _final, xml, err = get(loc)
        if status != 200 or not xml:
            print("sitemap skip %s %s %s" % (status, err, loc), file=sys.stderr)
            continue
        parsed = parse_sitemap(xml)
        if parsed[0] != "urlset":
            continue
        pages = parsed[1]
        prefix = sitemap_locale(loc)
        if prefix:
            locale_locs.setdefault(prefix, []).extend(pages)
        elif prefix == "" and "sitemap_agentic" not in loc:
            default_pages.extend(pages)
        if "sitemap_agentic" in loc:
            continue
        for page in pages:
            page_kind, _loc = content_kind(page)
            if prefix == "":
                bucket = bundle["sitemap"]["default_counts"]
                bucket[page_kind] = bucket.get(page_kind, 0) + 1
            if urlsplit(page).query and page not in bundle["sitemap"]["parameterised"]:
                bundle["sitemap"]["parameterised"].append(page)
            if page_kind == "collection-product" and page not in bundle["sitemap"]["collection_product"]:
                bundle["sitemap"]["collection_product"].append(page)

    # Blog atom: catch articles the sitemap file has not listed yet.
    atom_urls = []
    status, _final, atom, _err = get(HOST + "/blogs/news.atom")
    if status == 200 and atom:
        atom_urls = []
        for link in re.findall(r'href="(https://wellnessnest\.co/blogs/news/[^"]+)"', atom):
            if content_kind(link)[0] == "article" and link not in atom_urls:
                atom_urls.append(link)
    sitemap_articles = {url for url in default_pages if content_kind(url)[0] == "article"}
    missing = [url for url in atom_urls if url not in sitemap_articles]
    bundle["atom_missing"] = missing

    queue = []
    seen = set()

    def add(url, locale=""):
        if not url or url in seen:
            return
        if not _allowed_final(rules, url):
            skipped.append(url)
            return
        seen.add(url)
        queue.append(url)

    for url in default_pages:
        add(url)
    for prefix in sample:
        for url in _sample_urls(locale_locs.get(prefix) or [], per_kind=2):
            add(url)
    for url in missing:
        add(url)

    for url in queue:
        if not robots_allowed(rules, url):
            skipped.append(url)
            continue
        status, final, html, note = get(url)
        if note in ("robots", "robots-redirect"):
            skipped.append(final or url)
            bundle["pages"].append(observe("", url, final, status, error="redirect target disallowed by robots.txt; body not fetched"))
            continue
        record = observe(html, url, final, status, error=note)
        bundle["pages"].append(record)
    bundle["requests"] = limiter.sent
    bundle["robots_skipped"] = len(skipped)
    bundle["skipped"] = skipped[:50]
    return summarise(bundle)


def main(argv):
    if "--live" in argv or "--apply" in argv:
        print("canonical_audit: refusing --live/--apply. This crawl is read-only and does not write to Shopify.")
        return 2
    output = "docs/canonical-audit-2026-10-19.md"
    json_path = "docs/canonical-audit-2026-10-19.json"
    rate = RATE
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg == "--output" and i + 1 < len(argv):
            output = argv[i + 1]
            i += 2
            continue
        if arg == "--json" and i + 1 < len(argv):
            json_path = argv[i + 1]
            i += 2
            continue
        if arg == "--rate" and i + 1 < len(argv):
            rate = float(argv[i + 1])
            i += 2
            continue
        if arg in ("-h", "--help"):
            print(__doc__)
            return 0
        print("unknown argument: %s" % arg)
        return 2
    if rate < 1:
        print("canonical_audit: rate must be at least 1 second")
        return 2
    bundle = crawl(rate=rate)
    text = render_markdown(bundle)
    # JSON cannot store sets; summarise already converted scopes to lists.
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(bundle, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    with open(output, "w", encoding="utf-8") as handle:
        handle.write(text)
    counts = bundle["counts"]
    print("wrote %s and %s" % (output, json_path))
    print("pages %s canonical_mismatch %s identity_mismatch %s duplicate_article %s" % (
        counts["pages"], counts["canonical_mismatch"], counts["identity_mismatch_pages"],
        counts["duplicate_article_pages"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

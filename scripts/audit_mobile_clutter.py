#!/usr/bin/env python3
"""Read-only mobile clutter audit for wellnessnest.co /blogs/news articles.

Fetches each article with a plain GET and a mobile Safari user agent, then
reports reading-clutter signals from the initial HTML. It does not call the
Shopify Admin API, does not publish, and does not edit the theme.

Reuses ideas already in the repo, without calling the writers:

- scripts/audit_article_images.py skips spacer and display:none images. This
  audit applies that filter to public HTML only.
- scripts/patch_tables.py names the overflow wrapper article-table-wrapper.
  This audit only suggests that class.
- scripts/patch_mobile.py rewrites collection HTML and pushes it. It is not
  a blog audit and this script does not call it.
- PUBLISHED_ARTICLES_TRACKER.csv is a cross-check for which handles the repo
  already recorded. The public Atom feed decides "most recently published".

Search Engine Land, 20 October 2026, described a leaked clutterScore field
and said the formula is not public
(https://searchengineland.com/google-clutterscore-seo-497178). This report
does not compute that score. A viewport count this GET cannot see is the
string "unknown".

Theme and app fixes are suggestions. Each one says "report only, needs Kevin GO".
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 "
    "Mobile/15E148 Safari/604.1"
)
ATOM_URL = "https://wellnessnest.co/blogs/news.atom"
BLOG_HOST = "wellnessnest.co"
KEVIN_GO = "Report only, needs Kevin GO."
ARTICLE_ONLY = "Suggestion only. This audit does not edit the article."
RANK = {"info": 0, "low": 1, "medium": 2, "high": 3}
BLOCKS = {
    "div", "p", "section", "article", "header", "footer", "nav", "aside",
    "ul", "ol", "li", "table", "h1", "h2", "h3", "h4", "h5", "h6",
    "figure", "form", "main", "blockquote",
}
VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
    # Theme icons ship <path> without a close tag. Treating the shape tags
    # as void keeps the rest of the document from nesting inside the icon.
    "path", "circle", "line", "rect", "use", "stop", "polygon", "polyline",
}
DRAWER_TOKENS = {"menu-drawer", "cart-drawer", "header-drawer"}
DESKTOP_NAV_TOKENS = {"header__inline-menu", "mega-menu", "mega-menu__content"}
OVERLAY_HOST_SUFFIXES = (
    "klaviyo.com", "privy.com", "justuno.com", "optinmonster.com",
    "attentivemobile.com", "postscript.io", "omnisend.com",
)
SAFE_HOST_SUFFIXES = OVERLAY_HOST_SUFFIXES + (
    "shopify.com", "shopifycdn.com", "shopifycloud.com", "myshopify.com",
    "shopifysvc.com", "googleapis.com", "gstatic.com", "google.com",
    "google-analytics.com", "googletagmanager.com", "facebook.net",
    "facebook.com", "clarity.ms", "bing.com", "rechargecdn.com",
    "trustpilot.com", "goaffpro.com", "goaffpro.app", "trueprofit.io",
    "shrinetheme.com", "schema.org", "shop.app",
)
ANSWER_WORDS = 20
SHORT_PAGE_WORDS = 150
CTA_MEDIUM = 3.0
CTA_HIGH = 6.0
TAP_MIN_PX = 48


class Node:
    def __init__(self, tag, attrs):
        self.tag = tag
        self.attrs = attrs
        self.parent = None
        self.children = []  # Node or ("text", str) in source order

    def classes(self):
        return set((self.attrs.get("class") or "").split())


class TreeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {})
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        node.parent = self.stack[-1]
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        node.parent = self.stack[-1]
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if len(self.stack) > 1 and self.stack[-1].tag == tag:
            self.stack.pop()

    def handle_data(self, data):
        if data:
            self.stack[-1].children.append(("text", data))


def blog_article_url(url):
    """True only for a single wellnessnest.co blog article, with no query."""
    try:
        parts = urllib.parse.urlsplit((url or "").strip())
    except ValueError:
        return False
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if parts.scheme not in ("http", "https") or host != BLOG_HOST:
        return False
    if parts.query or parts.fragment:
        return False
    path = parts.path.rstrip("/")
    return re.fullmatch(r"/blogs/news/[a-z0-9][a-z0-9-]{0,180}", path) is not None


def handle_of(url):
    path = urllib.parse.urlsplit(url).path.rstrip("/")
    return path.rsplit("/", 1)[-1]


def word_count(text):
    return len(re.findall(r"[A-Za-z0-9']+", text or ""))


def visible_text(node):
    parts = []
    for child in node.children:
        if isinstance(child, tuple):
            parts.append(child[1])
        elif child.tag not in ("script", "style"):
            parts.append(visible_text(child))
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def iter_elements(node):
    for child in node.children:
        if isinstance(child, Node):
            yield child
            yield from iter_elements(child)


def class_tokens(node):
    return node.classes()


def attr(node, name):
    return node.attrs.get(name)


def ancestor_tokens(node):
    tokens = set()
    tags = set()
    cur = node
    while cur is not None:
        tokens |= cur.classes()
        tags.add(cur.tag)
        cur = cur.parent
    return tokens, tags


def in_drawer(node):
    tokens, tags = ancestor_tokens(node)
    if tokens & DRAWER_TOKENS or tags & DRAWER_TOKENS:
        return True
    cur = node
    while cur is not None:
        if cur.tag == "details" and "open" not in cur.attrs:
            return True
        cur = cur.parent
    return False


def in_desktop_nav(node):
    tokens, _tags = ancestor_tokens(node)
    return bool(tokens & DESKTOP_NAV_TOKENS)


def is_hidden(node):
    if node.attrs.get("hidden") is not None:
        return True
    tokens = node.classes()
    if tokens & {"hidden", "visually-hidden", "mobile-hidden"}:
        return True
    style = (node.attrs.get("style") or "").lower().replace(" ", "")
    return "display:none" in style


def in_svg(node):
    cur = node
    while cur is not None:
        if cur.tag == "svg":
            return True
        cur = cur.parent
    return False


def parse_html(html):
    """Strip script and style bodies so JSON-LD cannot break the tree."""
    styles = re.findall(r"<style\b[^>]*>([\s\S]*?)</style>", html, flags=re.I)
    script_srcs = []
    for match in re.finditer(r"<script\b([^>]*)>", html, flags=re.I):
        src = re.search(r"\bsrc\s*=\s*['\"]([^'\"]+)['\"]", match.group(1), re.I)
        if src:
            script_srcs.append(src.group(1))
    cleaned = re.sub(
        r"<script\b([^>]*)>[\s\S]*?</script>",
        lambda m: "<script%s></script>" % m.group(1),
        html,
        flags=re.I,
    )
    cleaned = re.sub(
        r"<style\b[^>]*>[\s\S]*?</style>",
        "<style></style>",
        cleaned,
        flags=re.I,
    )
    parser = TreeParser()
    parser.feed(cleaned)
    parser.close()
    return parser.root, styles, script_srcs


def find_first(root, pred):
    for node in iter_elements(root):
        if pred(node):
            return node
    return None


def article_body(root):
    node = find_first(root, lambda n: n.attrs.get("itemprop") == "articleBody")
    if node:
        return node
    return find_first(
        root, lambda n: "article-template__content" in n.classes()
    )


def h1_node(root):
    return find_first(root, lambda n: n.tag == "h1")


def answer_paragraph(article):
    if article is None:
        return None
    for node in iter_elements(article):
        if node.tag != "p":
            continue
        tokens, _tags = ancestor_tokens(node)
        if "image-credits" in tokens:
            continue
        if word_count(visible_text(node)) >= ANSWER_WORDS:
            return node
    return None


def blocks_before(article, answer):
    if article is None or answer is None:
        return "unknown"
    count = 0
    for node in iter_elements(article):
        if node is answer:
            break
        if node is article:
            continue
        if node.tag in BLOCKS:
            count += 1
    return count


def article_slice_bounds(html):
    match = re.search(
        r"<div\b[^>]*itemprop\s*=\s*['\"]articleBody['\"][^>]*>",
        html,
        flags=re.I,
    )
    if not match:
        match = re.search(
            r"<div\b[^>]*class\s*=\s*['\"][^'\"]*article-template__content[^'\"]*['\"][^>]*>",
            html,
            flags=re.I,
        )
    if not match:
        return None
    start = match.start()
    depth = 0
    for token in re.finditer(r"</?div\b[^>]*>", html[start:], flags=re.I):
        if token.group(0).lower().startswith("</"):
            depth -= 1
            if depth == 0:
                return start, start + token.end()
        else:
            depth += 1
    return None


def raw_answer_offset(html):
    """Byte offsets in the original document, not the script-stripped copy."""
    bounds = article_slice_bounds(html)
    if not bounds:
        return None
    start, end = bounds
    slice_html = html[start:end]
    for match in re.finditer(r"<p\b[^>]*>[\s\S]*?</p>", slice_html, flags=re.I):
        text = re.sub(r"<[^>]+>", " ", match.group(0))
        text = re.sub(r"\s+", " ", text).strip()
        if "image-credits" in match.group(0):
            continue
        if word_count(text) >= ANSWER_WORDS:
            absolute = start + match.start()
            body_at = html.lower().find("<body")
            return {
                "article_markup_bytes_before_answer": match.start(),
                "document_markup_bytes_before_answer": (
                    absolute - body_at if body_at >= 0 else "unknown"
                ),
                "answer_text_starts": text[:140],
            }
    return {
        "article_markup_bytes_before_answer": "unknown",
        "document_markup_bytes_before_answer": "unknown",
        "answer_text_starts": "unknown",
    }


def host_of(src):
    value = (src or "").strip()
    if not value or value.startswith("${"):
        return ""
    if value.startswith("//"):
        value = "https:" + value
    if value.startswith("/"):
        return BLOG_HOST
    try:
        host = urllib.parse.urlsplit(value).netloc.lower()
    except ValueError:
        return ""
    return host.split(":")[0]


def host_is(host, suffix):
    return host == suffix or host.endswith("." + suffix)


def unexpected_script_host(host):
    if not host or host == BLOG_HOST:
        return False
    if any(host_is(host, suffix) for suffix in SAFE_HOST_SUFFIXES):
        return False
    markers = ("jsdeliver", "jsdelivr", "cartassure", "shopify")
    return any(marker in host for marker in markers)


def css_rules(styles):
    text = "\n".join(styles)
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    grouped = {}
    for match in re.finditer(r"([^{}@]+)\{([^{}]*)\}", text):
        selector = re.sub(r"\s+", " ", match.group(1)).strip()
        if not selector or selector.startswith("@"):
            continue
        grouped.setdefault(selector, []).append(match.group(2))
    return {key: " ".join(parts) for key, parts in grouped.items()}


def px_value(declaration, prop):
    match = re.search(
        r"(?:^|[;{\s])%s\s*:\s*([0-9.]+)px\b" % re.escape(prop),
        declaration,
        flags=re.I,
    )
    if not match:
        return None
    return float(match.group(1))


def selector_classes(selector):
    return re.findall(r"\.([A-Za-z0-9_-]+)", selector)


def document_has_class(root, name):
    return find_first(root, lambda n, name=name: name in n.classes()) is not None


def selector_present(root, selector):
    classes = selector_classes(selector)
    if not classes:
        return True
    return any(document_has_class(root, name) for name in classes)


def is_content_image(node):
    if node.tag != "img" or in_svg(node):
        return False
    src = (node.attrs.get("src") or "").strip()
    cls = " ".join(node.classes()).lower()
    style = (node.attrs.get("style") or "").lower()
    alt = node.attrs.get("alt") or ""
    if not src or src.startswith("${") or alt.startswith("${"):
        return False
    if "spacer" in cls or "spacer" in src.lower():
        return False
    if "display:none" in style.replace(" ", "") or "display: none" in style:
        return False
    return True


def image_record(node, region):
    style = node.attrs.get("style") or ""
    width = node.attrs.get("width")
    height = node.attrs.get("height")
    sized = bool(width) and bool(height)
    style_sized = bool(re.search(r"\bwidth\s*:", style, re.I)) and bool(
        re.search(r"\bheight\s*:", style, re.I)
    )
    aspect = bool(re.search(r"aspect-ratio\s*:", style, re.I))
    return {
        "region": region,
        "alt": re.sub(r"\s+", " ", node.attrs.get("alt") or "")[:80],
        "width_attr": width or "unknown",
        "height_attr": height or "unknown",
        "missing_width_and_height": not sized and not style_sized,
        "aspect_ratio_in_style": aspect,
        "class_mobile_hidden": "mobile-hidden" in ancestor_tokens(node)[0] or "mobile-hidden" in node.classes(),
        "rendered_px": "unknown",
        "cls": "unknown",
    }


def overflow_wrapped(node):
    cur = node.parent
    while cur is not None:
        if cur.classes() & {"article-table-wrapper", "table-wrapper", "table-wrap"}:
            return True
        style = (cur.attrs.get("style") or "").lower().replace(" ", "")
        if "overflow-x:auto" in style or "overflow-x:scroll" in style or "overflow:auto" in style:
            return True
        cur = cur.parent
    return False


def product_href(href):
    if not href:
        return False
    path = urllib.parse.urlsplit(href).path
    return path.startswith("/products/") or "/products/" in href


def cta_count(root, article):
    inline = []
    if article is not None:
        for node in iter_elements(article):
            if node.tag != "a" or is_hidden(node):
                continue
            href = node.attrs.get("href") or ""
            if product_href(href):
                inline.append(href.split("?")[0])
    cards = 0
    for node in iter_elements(root):
        if "card-wrapper" in node.classes() and _under_class(node, "shop-this-article"):
            cards += 1
    newsletter = 0
    section = find_first(
        root,
        lambda n: "newsletter" in n.classes() or "newsletter" in (n.attrs.get("id") or ""),
    )
    if section is not None:
        for node in iter_elements(section):
            if node.tag == "form" or (node.tag == "input" and (node.attrs.get("type") or "").lower() == "email"):
                newsletter = 1
                break
    return {
        "inline_product_links": len(inline),
        "shop_this_article_cards": cards,
        "newsletter_forms": newsletter,
        "cta_blocks": len(inline) + cards + newsletter,
        "inline_product_hrefs": inline,
    }


def _under_class(node, token):
    tokens, _tags = ancestor_tokens(node)
    return token in tokens or token in node.classes()


def elements_between(root, start, end, tags):
    if start is None or end is None:
        return "unknown"
    seen_start = False
    count = 0
    for node in iter_elements(root):
        if node is start:
            seen_start = True
            continue
        if not seen_start:
            continue
        if node is end:
            break
        if node.tag in tags and not is_hidden(node) and not in_drawer(node) and not in_desktop_nav(node) and not in_svg(node):
            count += 1
    return count


def source_blocks_before_h1(root, h1):
    if h1 is None:
        return "unknown", "unknown"
    total = 0
    mobile_candidates = 0
    for node in iter_elements(root):
        if node is h1:
            break
        if node.tag not in BLOCKS or in_svg(node):
            continue
        total += 1
        if in_drawer(node) or in_desktop_nav(node) or is_hidden(node):
            continue
        mobile_candidates += 1
    return total, mobile_candidates


def ticker_stats(root):
    items = [
        node for node in iter_elements(root)
        if "horizontal-ticker__item" in node.classes()
    ]
    texts = []
    for node in items:
        text = visible_text(node)
        if text:
            texts.append(text)
    unique = []
    for text in texts:
        if text not in unique:
            unique.append(text)
    return {"item_nodes": len(items), "unique_messages": unique}


def sections_before_h1(html):
    h1_at = html.lower().find("<h1")
    if h1_at < 0:
        return "unknown"
    ids = re.findall(r'id="(shopify-section[^"]+)"', html[:h1_at])
    named = []
    for section_id in ids:
        window = html[max(0, html.find(section_id) - 80):html.find(section_id) + 500]
        if "horizontal-ticker" in window:
            named.append("horizontal-ticker")
        elif "section-header" in window or "header-wrapper" in window:
            named.append("header")
        elif "cart-drawer" in window:
            named.append("cart-drawer")
        elif "article-template" in window or "__main" in section_id:
            named.append("article")
        else:
            named.append("other")
    return named


def crowded_groups(root):
    groups = []
    for node in iter_elements(root):
        if in_drawer(node) or in_desktop_nav(node) or in_svg(node):
            continue
        run = []
        words_between = 0

        def flush():
            nonlocal run, words_between
            if len(run) >= 3:
                groups.append(len(run))
            run = []
            words_between = 0

        for child in node.children:
            if isinstance(child, tuple):
                words = word_count(child[1])
                if words:
                    words_between += words
                    if words_between >= 3 and run:
                        flush()
                continue
            interactive = child.tag in {"a", "button"} and not is_hidden(child)
            if not interactive:
                if child.tag in BLOCKS and run:
                    flush()
                continue
            if words_between >= 3:
                flush()
            run.append(child)
            words_between = 0
        flush()
    return groups


def selector_on_control(root, selector):
    """True when one of the selector's classes sits on a link or button."""
    classes = selector_classes(selector)
    if not classes:
        return False
    for node in iter_elements(root):
        if node.tag not in {"a", "button"}:
            continue
        if any(name in node.classes() for name in classes):
            return True
    return False


def declared_small_targets(rules, root):
    found = []
    for selector, body in rules.items():
        if "svg" in selector.lower():
            continue
        if not selector_on_control(root, selector):
            continue
        width = px_value(body, "width")
        if width is None:
            width = px_value(body, "min-width")
        height = px_value(body, "height")
        if height is None:
            height = px_value(body, "min-height")
        if width is None or height is None:
            continue
        if width < TAP_MIN_PX and height < TAP_MIN_PX:
            found.append({
                "selector": selector[:160],
                "declared_width_px": width,
                "declared_height_px": height,
                "rendered_px": "unknown",
            })
    return found


def font_hints(root, article, rules):
    declared = []
    relative = []
    regions = []
    for node in iter_elements(root):
        interesting = node is article or _under_class(node, "article-template__content") or _under_class(node, "article-header") or _under_class(node, "shop-this-article") or _under_class(node, "newsletter") or _under_class(node, "horizontal-ticker") or "image-credits" in node.classes()
        if not interesting or is_hidden(node):
            continue
        style = node.attrs.get("style") or ""
        for size in re.findall(r"font-size\s*:\s*([^;]+)", style, flags=re.I):
            size = size.strip()
            where = node.tag + ("." + next(iter(node.classes()), "") if node.classes() else "")
            px = re.fullmatch(r"([0-9.]+)px", size, flags=re.I)
            if px:
                value = float(px.group(1))
                if value < 16:
                    declared.append({
                        "where": short_selector(where),
                        "font_size_px": value,
                        "rendered_px": "unknown",
                    })
            else:
                relative.append({"where": where, "font_size": size, "rendered_px": "unknown"})
    for selector, body in rules.items():
        selector_l = selector.lower()
        if not any(token in selector_l for token in ("article", "rte", "sta__", "ticker", "share", "newsletter", "image-credit")):
            continue
        if not selector_present(root, selector):
            continue
        for size in re.findall(r"font-size\s*:\s*([^;]+)", body, flags=re.I):
            size = size.strip()
            px = re.fullmatch(r"([0-9.]+)px", size, flags=re.I)
            if not px:
                relative.append({
                    "where": short_selector(selector),
                    "font_size": size,
                    "rendered_px": "unknown",
                })
                continue
            value = float(px.group(1))
            if value < 16:
                declared.append({
                    "where": short_selector(selector),
                    "font_size_px": value,
                    "rendered_px": "unknown",
                })
    line_length = "unknown"
    for selector, body in rules.items():
        if not any(token in selector.lower() for token in ("article-template__content", "rte", "page-width")):
            continue
        match = re.search(r"max-width\s*:\s*([^;]+)", body, flags=re.I)
        if match:
            # A max-width above the phone width does not set the mobile line length.
            line_length = "unknown"
            break
    return declared, relative, line_length


def short_selector(selector):
    classes = selector_classes(selector)
    if classes:
        return "." + classes[-1]
    text = re.sub(r"\s+", " ", selector).strip()
    return text[:40]


def placeholder_sections(root):
    found = []
    for needle in ("promo-popup", "global-music-player", "scroll-to-top"):
        node = find_first(
            root,
            lambda n, needle=needle: needle in (n.attrs.get("id") or "") or needle in " ".join(n.classes()),
        )
        if node is None:
            continue
        text = visible_text(node)
        found.append({
            "id": needle,
            "text_in_initial_html": text[:80] if text else "",
            "rendered_behavior": "unknown",
        })
    return found


def fixed_and_sticky(rules, root):
    fixed = []
    sticky = []
    for selector, body in rules.items():
        if not selector_present(root, selector):
            continue
        if re.search(r"position\s*:\s*fixed", body, flags=re.I):
            fixed.append({
                "selector": selector[:180],
                "full_width_bottom": bool(
                    re.search(r"\bleft\s*:", body, re.I)
                    and re.search(r"\bright\s*:", body, re.I)
                    and re.search(r"\bbottom\s*:", body, re.I)
                ),
            })
        elif re.search(r"position\s*:\s*sticky", body, flags=re.I):
            sticky.append(selector[:180])
    return fixed, sticky


def issue(severity, summary, fix, scope):
    needs = scope in {"theme", "mixed"}
    if needs and KEVIN_GO not in fix:
        fix = fix.rstrip() + " " + KEVIN_GO
    if scope in {"article", "mixed"} and "does not edit the article" not in fix:
        fix = fix.rstrip() + " " + ARTICLE_ONLY
    return {
        "severity": severity,
        "summary": summary,
        "suggested_fix": fix,
        "scope": scope,
        "needs_kevin_go": needs,
    }


def max_severity(issues):
    if not issues:
        return "info"
    return max(issues, key=lambda item: RANK[item["severity"]])["severity"]


def rollup(signal, issues, measured):
    if not issues:
        issues = [issue(
            "info",
            "Checked in the initial HTML. Nothing in this signal crossed a clutter threshold.",
            "No change suggested.",
            "article",
        )]
        # The info row is not an article edit. Drop the boilerplate.
        issues[0]["suggested_fix"] = "No change suggested."
        issues[0]["needs_kevin_go"] = False
    severity = max_severity(issues)
    scopes = {item["scope"] for item in issues}
    scope = next(iter(scopes)) if len(scopes) == 1 else "mixed"
    summaries = [item["summary"] for item in issues]
    fixes = []
    for item in issues:
        if item["suggested_fix"] not in fixes and item["suggested_fix"] != "No change suggested.":
            fixes.append(item["suggested_fix"])
    if not fixes:
        fixes = ["No change suggested."]
    return {
        "signal": signal,
        "severity": severity,
        "summary": " ".join(summaries),
        "measured": measured,
        "suggested_fix": " ".join(fixes),
        "scope": scope,
        "needs_kevin_go": any(item["needs_kevin_go"] for item in issues),
        "issues": issues,
    }


def signal_content_start(article, answer, raw):
    measured = {
        "article_block_elements_before_answer": blocks_before(article, answer),
        "answer_is_first_paragraph": "unknown",
        "article_markup_bytes_before_answer": "unknown",
        "document_markup_bytes_before_answer": "unknown",
    }
    if raw:
        measured["article_markup_bytes_before_answer"] = raw["article_markup_bytes_before_answer"]
        measured["document_markup_bytes_before_answer"] = raw["document_markup_bytes_before_answer"]
    issues = []
    blocks = measured["article_block_elements_before_answer"]
    if article is None or answer is None or blocks == "unknown":
        measured["answer_is_first_paragraph"] = "unknown"
        issues.append(issue(
            "info",
            "Article body or the first answer paragraph was not found. Content-start position is unknown.",
            "No change suggested from this signal.",
            "article",
        ))
        issues[0]["suggested_fix"] = "No change suggested from this signal."
    else:
        first_p = find_first(article, lambda n: n.tag == "p")
        measured["answer_is_first_paragraph"] = first_p is answer
        if blocks >= 6:
            severity = "high"
        elif blocks >= 3:
            severity = "medium"
        elif blocks >= 1:
            severity = "low"
        else:
            severity = "info"
        if severity == "info":
            issues.append(issue(
                "info",
                "The first long paragraph is the start of the article body (%s markup bytes inside the article before that paragraph)."
                % measured["article_markup_bytes_before_answer"],
                "No change suggested.",
                "article",
            ))
            issues[0]["suggested_fix"] = "No change suggested."
        else:
            issues.append(issue(
                severity,
                "The article body has %s block element(s) before the first answer paragraph." % blocks,
                "Move the answer paragraph above the introductory blocks.",
                "article",
            ))
    bytes_before = measured["document_markup_bytes_before_answer"]
    if isinstance(bytes_before, int):
        measured["document_bytes_note"] = (
            "Byte count includes theme chrome and scripts. It is not a viewport position."
        )
    return rollup("content_start", issues, measured)


def signal_popups(html, root, rules, script_srcs):
    fixed, sticky = fixed_and_sticky(rules, root)
    hosts = []
    overlay_hosts = []
    other_hosts = []
    for src in script_srcs:
        host = host_of(src)
        if not host or host in hosts:
            continue
        hosts.append(host)
        if any(host_is(host, suffix) for suffix in OVERLAY_HOST_SUFFIXES):
            overlay_hosts.append(host)
        elif unexpected_script_host(host):
            pass
        else:
            other_hosts.append(host)
    unexpected = []
    for host in hosts:
        if unexpected_script_host(host) and host not in unexpected:
            unexpected.append(host)
    lower = html.lower()
    if "cartassure.top" in lower and "cartassure.top" not in unexpected:
        unexpected.append("cartassure.top")
    elif "cartassure" in lower and not any("cartassure" in item for item in unexpected):
        unexpected.append("cartassure")
    if "240.1.2.3" in lower and "240.1.2.3" not in unexpected:
        unexpected.append("240.1.2.3")
    cro = [src for src in script_srcs if "gemx" in src.lower() or "gx-global" in src.lower()]
    placeholders = placeholder_sections(root)
    trigger = find_first(root, lambda n: "sta__trigger" in n.classes())
    trigger_open = "unknown"
    if trigger is not None:
        expanded = trigger.attrs.get("aria-expanded")
        trigger_open = expanded if expanded is not None else "unknown"
    measured = {
        "fixed_selectors": fixed,
        "sticky_selectors": sticky,
        "overlay_script_hosts": overlay_hosts,
        "unexpected_hosts": unexpected,
        "cro_scripts_present": len(cro),
        "placeholder_sections": placeholders,
        "shop_trigger_aria_expanded": trigger_open,
        "popup_after_javascript": "unknown",
        "other_script_hosts": other_hosts,
    }
    issues = []
    if unexpected:
        issues.append(issue(
            "high",
            "Initial HTML references unexpected host(s): %s." % ", ".join(unexpected),
            "Remove the unexpected script and any header item that references it, after a theme backup.",
            "theme",
        ))
    bars = [
        row for row in fixed
        if "sta__trigger" in row["selector"]
        or (row["full_width_bottom"] and "overlay" not in row["selector"] and "modal" not in row["selector"])
    ]
    if bars:
        bottom_bar = any(row["full_width_bottom"] for row in bars)
        issues.append(issue(
            "high" if bottom_bar else "medium",
            "Shop-this-article CSS sets position:fixed%s. Trigger aria-expanded is %s. Whether JavaScript hides the control is unknown."
            % (
                " and stretches it to both side edges along the bottom" if bottom_bar else "",
                trigger_open,
            ),
            "Do not pin a shop bar over the article on mobile. Keep the product mention inline.",
            "theme",
        ))
    elif fixed:
        issues.append(issue(
            "medium",
            "position:fixed is declared for %s." % fixed[0]["selector"][:80],
            "Check that this fixed layer does not cover the article on a phone.",
            "theme",
        ))
    if overlay_hosts:
        issues.append(issue(
            "medium",
            "Overlay-vendor script host(s) loaded: %s. No vendor form was required to record the script. Whether a popup opens after JavaScript is unknown."
            % ", ".join(overlay_hosts),
            "Replace a full-screen email popup with an inline form that does not cover the article.",
            "theme",
        ))
    if sticky:
        issues.append(issue(
            "low",
            "position:sticky is declared for %s." % sticky[0][:80],
            "A sticky header is theme chrome. Leave it unless it stacks with the ticker and the shop bar.",
            "theme",
        ))
    if cro:
        issues.append(issue(
            "info",
            "A CRO app script is on the page. What it injects on this mobile GET is unknown.",
            "No change suggested until the injected layer is identified.",
            "theme",
        ))
    empty_shells = [row["id"] for row in placeholders if not row["text_in_initial_html"]]
    if empty_shells:
        issues.append(issue(
            "info",
            "Section shell(s) with no control text in the initial HTML: %s. Rendered behavior is unknown."
            % ", ".join(empty_shells),
            "No change suggested from the empty shell alone.",
            "theme",
        ))
    return rollup("popups_sticky_interstitials", issues, measured)


def _inside(node, ancestor):
    cur = node
    while cur is not None:
        if cur is ancestor:
            return True
        cur = cur.parent
    return False


def signal_images(root, article):
    records = []
    if article is not None:
        for node in iter_elements(article):
            if is_content_image(node):
                records.append(image_record(node, "article_body"))
    for node in iter_elements(root):
        if not is_content_image(node):
            continue
        if article is not None and _inside(node, article):
            continue
        blob = " ".join(ancestor_tokens(node)[0] | node.classes())
        if "article-header" in blob or "article-template__hero" in blob:
            records.append(image_record(node, "article_header"))
    shop = find_first(root, lambda n: "shop-this-article" in n.classes())
    shop_records = []
    if shop is not None:
        for node in iter_elements(shop):
            if is_content_image(node):
                shop_records.append(image_record(node, "shop_this_article"))
    missing = [row for row in records if row["missing_width_and_height"] and not row["aspect_ratio_in_style"]]
    missing_shop = [row for row in shop_records if row["missing_width_and_height"] and not row["aspect_ratio_in_style"]]
    measured = {
        "content_images": len(records),
        "missing_width_and_height": len(missing),
        "shop_this_article_images": len(shop_records),
        "shop_this_article_missing_width_and_height": len(missing_shop),
        "cls": "unknown",
        "rendered_px": "unknown",
        "images": records[:12],
    }
    issues = []
    if missing:
        severity = "high" if len(missing) >= 3 else "medium"
        issues.append(issue(
            severity,
            "%s content image(s) have no width and height and no aspect-ratio style. CLS is unknown."
            % len(missing),
            "Add width and height attributes that match each file's pixel size.",
            "article",
        ))
    if missing_shop:
        issues.append(issue(
            "low",
            "%s Shop this article image(s) have no width and height. Rendered size is unknown."
            % len(missing_shop),
            "Give the shop-card images width and height in the section.",
            "theme",
        ))
    hidden_hero = [row for row in records if row["region"] == "article_header" and row["class_mobile_hidden"]]
    if hidden_hero:
        issues.append(issue(
            "info",
            "The article header image carries class mobile-hidden. Whether the phone hides it is unknown without the theme stylesheet.",
            "No change suggested from the class name alone.",
            "theme",
        ))
    return rollup("images", issues, measured)


def signal_cta(root, article):
    counts = cta_count(root, article)
    words = word_count(visible_text(article)) if article is not None else 0
    if article is None or words == 0:
        density = "unknown"
    else:
        density = round(counts["cta_blocks"] * 1000 / words, 2)
    measured = dict(counts)
    measured["article_words"] = words if article is not None else "unknown"
    measured["cta_per_1000_words"] = density
    measured["threshold_note"] = (
        "Heuristic count of product links, shop cards, and email forms per 1,000 article words. "
        "Not clutterScore. Not the Better Ads 30 percent height test, which needs a layout viewport."
    )
    issues = []
    if density == "unknown":
        issues.append(issue(
            "info",
            "CTA density is unknown because the article word count is unknown.",
            "No change suggested.",
            "article",
        ))
        issues[0]["suggested_fix"] = "No change suggested."
    elif words < SHORT_PAGE_WORDS:
        issues.append(issue(
            "info",
            "CTA blocks: %s. Words: %s. Per 1,000 words: %s. The page is under %s words, so the density threshold is not applied."
            % (counts["cta_blocks"], words, density, SHORT_PAGE_WORDS),
            "No change suggested from density on a short fixture.",
            "article",
        ))
        issues[0]["suggested_fix"] = "No change suggested from density on a short fixture."
    else:
        if density >= CTA_HIGH:
            severity = "high"
        elif density >= CTA_MEDIUM:
            severity = "medium"
        else:
            severity = "info"
        summary = (
            "%s CTA block(s) across %s article words, %s per 1,000 words "
            "(inline product links %s, shop cards %s, newsletter forms %s)."
            % (
                counts["cta_blocks"], words, density,
                counts["inline_product_links"], counts["shop_this_article_cards"],
                counts["newsletter_forms"],
            )
        )
        if severity == "info":
            issues.append(issue("info", summary, "No change suggested.", "article"))
            issues[0]["suggested_fix"] = "No change suggested."
        else:
            scope = "theme" if counts["inline_product_links"] == 0 else "mixed"
            fix = (
                "Keep one product mention in the article. The shop card and the email form are theme sections."
            )
            issues.append(issue(severity, summary, fix, scope))
    repeated = {}
    for href in counts["inline_product_hrefs"]:
        repeated[href] = repeated.get(href, 0) + 1
    repeated = {href: count for href, count in repeated.items() if count >= 3}
    if repeated:
        issues.append(issue(
            "low",
            "The same product URL is linked %s times in the article body." % max(repeated.values()),
            "Keep a single product link near the label mention.",
            "article",
        ))
    return rollup("cta_density", issues, measured)


def signal_wide(article):
    tables = []
    naked = []
    if article is not None:
        for node in iter_elements(article):
            if node.tag == "table":
                tables.append(node)
                if not overflow_wrapped(node):
                    naked.append(node)
    wide_style = []
    if article is not None:
        for node in iter_elements(article):
            style = node.attrs.get("style") or ""
            for prop in ("min-width", "width"):
                value = px_value(style, prop)
                if value is not None and value > 390 and node.tag not in {"img"}:
                    wide_style.append({"tag": node.tag, "property": prop, "declared_px": value})
    measured = {
        "tables": len(tables),
        "tables_without_overflow_wrapper": len(naked),
        "wide_inline_px": wide_style,
        "rendered_overflow": "unknown",
    }
    issues = []
    if naked:
        issues.append(issue(
            "medium",
            "%s table(s) in the article have no overflow wrapper. Whether they overflow a phone viewport is unknown."
            % len(naked),
            "Wrap each table in a div with class article-table-wrapper and overflow-x:auto. Do not run scripts/patch_tables.py from this audit; that script writes article HTML.",
            "article",
        ))
    if wide_style:
        issues.append(issue(
            "medium",
            "An inline style declares a width above 390px (%s)." % wide_style[0],
            "Let the element use the column width instead of a fixed pixel width.",
            "article",
        ))
    return rollup("wide_overflow", issues, measured)


def signal_tap(root, rules):
    groups = crowded_groups(root)
    small = declared_small_targets(rules, root)
    measured = {
        "crowded_sibling_groups": len(groups),
        "crowded_group_sizes": groups[:8],
        "declared_boxes_under_48px": small,
        "rendered_gap_px": "unknown",
        "rendered_target_px": "unknown",
    }
    issues = []
    if small:
        box = small[0]
        issues.append(issue(
            "medium",
            "Declared box %sx%s px on %s is under %s px. Rendered size is unknown."
            % (
                box["declared_width_px"],
                box["declared_height_px"],
                short_selector(box["selector"]),
                TAP_MIN_PX,
            ),
            "Raise the declared width and height of that control to at least 48px.",
            "theme" if "sta__" in box["selector"] or "header" in box["selector"] else "article",
        ))
    if groups:
        issues.append(issue(
            "low",
            "%s group(s) of 3 or more sibling links or buttons have no inline gap. Pixel gap is unknown."
            % len(groups),
            "Separate those controls by at least 8px of padding or gap in the section CSS.",
            "theme",
        ))
    return rollup("tap_targets", issues, measured)


def signal_font(root, article, rules):
    declared, relative, line_length = font_hints(root, article, rules)
    # Dedup identical where/size pairs.
    seen = set()
    declared_u = []
    for row in declared:
        key = (row["where"], row.get("font_size_px"))
        if key in seen:
            continue
        seen.add(key)
        declared_u.append(row)
    seen = set()
    relative_u = []
    for row in relative:
        key = (row["where"], row.get("font_size"))
        if key in seen:
            continue
        seen.add(key)
        relative_u.append(row)
    measured = {
        "declared_px_under_16": declared_u[:12],
        "relative_font_sizes": relative_u[:8],
        "rendered_line_length": line_length,
    }
    issues = []
    if declared_u:
        smallest = min(row["font_size_px"] for row in declared_u)
        severity = "high" if smallest < 12 else "medium"
        scope = "theme"
        if any(row["where"].startswith("p") or "article" in row["where"] for row in declared_u):
            # An inline style on article copy is an article edit. Theme selectors stay theme.
            if all("sta__" in row["where"] or "ticker" in row["where"] or "newsletter" in row["where"] or "share" in row["where"] for row in declared_u):
                scope = "theme"
            elif any(row["where"].startswith("p") or row["where"].startswith("aside") for row in declared_u):
                scope = "mixed" if any("sta__" in row["where"] or "ticker" in row["where"] for row in declared_u) else "article"
        shop_only = all("sta__" in row["where"] for row in declared_u)
        issues.append(issue(
            severity,
            "Declared font-size under 16px: %s." % ", ".join(
                "%s at %s" % (row["where"][:40], row["font_size_px"]) for row in declared_u[:4]
            ),
            "Use at least 16px for the shop-bar label." if shop_only else "Use at least 16px for article text and for labels on mobile controls.",
            "theme" if shop_only else scope,
        ))
    if relative_u:
        issues.append(issue(
            "info",
            "Relative font-size present (%s). Rendered px is unknown." % relative_u[0]["font_size"],
            "No change suggested until the computed pixel size is known.",
            "article" if any(row["where"].startswith("aside") or row["where"].startswith("p") for row in relative_u) else "theme",
        ))
    if not declared_u and line_length == "unknown":
        pass
    measured["rendered_line_length"] = "unknown"
    return rollup("font_line_length", issues, measured)


def signal_fold(html, root, h1, answer):
    total, candidates = source_blocks_before_h1(root, h1)
    ticker = ticker_stats(root)
    between = elements_between(root, h1, answer, {"a", "button", "h2"})
    sections = sections_before_h1(html)
    measured = {
        "rendered_above_the_fold_elements": "unknown",
        "source_block_elements_before_h1": total,
        "source_block_elements_before_h1_excluding_drawers_desktop_nav_and_hidden": candidates,
        "sections_before_h1": sections,
        "interactive_elements_between_h1_and_answer": between,
        "ticker_item_nodes": ticker["item_nodes"],
        "ticker_unique_messages": ticker["unique_messages"],
    }
    issues = []
    copies = ticker["item_nodes"]
    unique = ticker["unique_messages"]
    if copies >= 8 and len(unique) <= 4:
        issues.append(issue(
            "medium",
            "One ticker sits before the H1, repeated as %s item nodes (%s unique message(s)). Rendered bar height is unknown. Above-the-fold element count is unknown."
            % (copies, len(unique)),
            "Keep a single line in the ticker instead of repeating the same messages in the HTML.",
            "theme",
        ))
    elif isinstance(between, int) and between >= 6:
        issues.append(issue(
            "low",
            "%s interactive elements sit between the H1 and the answer paragraph. Above-the-fold count is unknown."
            % between,
            "Move share controls below the first paragraph.",
            "theme",
        ))
    else:
        issues.append(issue(
            "info",
            "Rendered above-the-fold count is unknown. This GET does not lay out a viewport. Sections before the H1 in source order: %s."
            % (sections if isinstance(sections, list) else "unknown"),
            "No change suggested from source order alone.",
            "theme",
        ))
    return rollup("above_the_fold", issues, measured)


def page_title(root, html):
    h1 = h1_node(root)
    if h1 is not None:
        text = visible_text(h1)
        if text:
            return text
    match = re.search(r"<title>([\s\S]*?)</title>", html, flags=re.I)
    if not match:
        return "unknown"
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", match.group(1))).strip()[:180]


def audit_html(html, url, meta=None):
    """Audit one article document. `html` is the public response body."""
    meta = meta or {}
    if not blog_article_url(url):
        raise ValueError("refusing non-blog URL: %s" % url)
    root, styles, script_srcs = parse_html(html)
    rules = css_rules(styles)
    article = article_body(root)
    answer = answer_paragraph(article)
    h1 = h1_node(root)
    raw = raw_answer_offset(html)
    findings = [
        signal_content_start(article, answer, raw),
        signal_popups(html, root, rules, script_srcs),
        signal_images(root, article),
        signal_cta(root, article),
        signal_wide(article),
        signal_tap(root, rules),
        signal_font(root, article, rules),
        signal_fold(html, root, h1, answer),
    ]
    words = word_count(visible_text(article)) if article is not None else "unknown"
    return {
        "url": url,
        "handle": handle_of(url),
        "title": page_title(root, html),
        "published_at": meta.get("published_at") or "unknown",
        "tracker_ticket": meta.get("tracker_ticket") or "",
        "in_tracker": meta.get("in_tracker", "not_checked"),
        "article_words": words,
        "highest_severity": max_severity(findings),
        "findings": findings,
        "error": None,
    }


def blog_entries_from_atom(xml_text):
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    entries = []
    seen = set()
    for entry in root.findall("a:entry", ns):
        link = ""
        for node in entry.findall("a:link", ns):
            if node.attrib.get("rel", "alternate") == "alternate":
                link = node.attrib.get("href") or ""
                break
        link = link.split("#")[0].strip()
        if not blog_article_url(link):
            continue
        link = link.rstrip("/")
        if link in seen:
            continue
        seen.add(link)
        published = (
            entry.findtext("a:published", default="", namespaces=ns)
            or entry.findtext("a:updated", default="", namespaces=ns)
        )
        title = entry.findtext("a:title", default="", namespaces=ns) or ""
        entries.append({
            "url": link,
            "published_at": published,
            "title": re.sub(r"\s+", " ", title).strip(),
            "source": "atom",
        })
    entries.sort(key=lambda row: row["published_at"], reverse=True)
    return entries


def blog_entries_from_tracker(csv_text):
    reader = csv.DictReader(io.StringIO(csv_text))
    entries = []
    seen = set()
    for row in reader:
        url = (row.get("Article Link") or "").strip().rstrip("/")
        if not blog_article_url(url):
            continue
        if url in seen:
            continue
        seen.add(url)
        date_match = re.search(r"(20\d{2}-\d{2}-\d{2})", row.get("Posted Date") or "")
        if not date_match:
            continue
        entries.append({
            "url": url,
            "published_at": date_match.group(1),
            "title": (row.get("Keyword") or "").strip(),
            "source": "tracker",
            "tracker_ticket": (row.get("Ticket") or "").strip(),
        })
    entries.sort(key=lambda row: row["published_at"], reverse=True)
    return entries


def annotate_tracker(selected, tracker_entries):
    by_url = {row["url"].rstrip("/"): row for row in tracker_entries}
    for row in selected:
        match = by_url.get(row["url"].rstrip("/"))
        row["in_tracker"] = bool(match)
        row["tracker_ticket"] = (match or {}).get("tracker_ticket") or row.get("tracker_ticket") or ""
    return selected


def duplicate_titles(entries):
    buckets = {}
    for row in entries:
        title = (row.get("title") or "").strip().lower()
        if not title:
            continue
        buckets.setdefault(title, []).append(row["url"])
    return {title: urls for title, urls in buckets.items() if len(urls) > 1}


def fetch(url, timeout=40):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": MOBILE_UA, "Accept": "text/html,application/atom+xml;q=0.9,*/*;q=0.8"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return response.status, response.geturl(), body.decode(charset, "replace")


def error_post(url, message, meta=None):
    meta = meta or {}
    return {
        "url": url,
        "handle": handle_of(url) if blog_article_url(url) else "",
        "title": meta.get("title") or "unknown",
        "published_at": meta.get("published_at") or "unknown",
        "tracker_ticket": meta.get("tracker_ticket") or "",
        "in_tracker": meta.get("in_tracker", "not_checked"),
        "article_words": "unknown",
        "highest_severity": "unknown",
        "findings": [],
        "error": message,
    }


def render_markdown(report):
    lines = [
        "# Mobile clutter audit — wellnessnest.co blog — %s" % report["date"],
        "",
        "Read-only public GET with a mobile Safari user agent. No Shopify Admin API, no theme edit, no publish. Fixes below are suggestions.",
        "",
        "## Why these signals",
        "",
        report["context"],
        "",
        "## How a number is labeled",
        "",
        "A viewport fact this GET cannot see is the string `unknown`. Declared CSS pixels are the sizes written in the page, not a layout measurement. `cls` is unknown on every post.",
        "",
        "## Selection",
        "",
        report["selection_note"],
        "",
        "| Published | Handle | Tracker | Highest |",
        "|---|---|---|---|",
    ]
    for post in report["posts"]:
        lines.append("| %s | `%s` | %s | %s |" % (
            str(post.get("published_at") or "unknown")[:25],
            post.get("handle") or "",
            post.get("tracker_ticket") or ("yes" if post.get("in_tracker") is True else "no" if post.get("in_tracker") is False else "not checked"),
            post.get("highest_severity"),
        ))
    lines.extend(["", "## Repeated theme findings", ""])
    if report["repeated_theme"]:
        lines.append("These high or medium theme issues used the same wording on every fetched post.")
        lines.append("")
        for row in report["repeated_theme"]:
            lines.append("- **%s** (%s). %s" % (row["signal"], row["severity"], row["summary"]))
            lines.append("  - %s" % row["suggested_fix"])
    else:
        lines.append("No high or medium theme finding used the same wording on every fetched post.")
    lines.extend(["", "## Per post", ""])
    for post in report["posts"]:
        lines.append("### %s" % (post.get("title") or post.get("handle")))
        lines.append("")
        lines.append("- URL: %s" % post.get("url"))
        lines.append("- Published: %s" % post.get("published_at"))
        lines.append("- Article words: %s" % post.get("article_words"))
        lines.append("- Highest severity: %s" % post.get("highest_severity"))
        if post.get("error"):
            lines.append("- Fetch error: %s" % post["error"])
            lines.append("")
            continue
        for finding in post["findings"]:
            lines.append("")
            lines.append("#### %s — %s" % (finding["signal"], finding["severity"]))
            lines.append("")
            for item in finding["issues"]:
                lines.append("- **%s** (%s). %s" % (item["severity"], item["scope"], item["summary"]))
                lines.append("  - %s" % item["suggested_fix"])
        lines.append("")
    lines.append("This audit did not edit the theme, the articles, or any Home, Collection, Product, Sales, Checkout, or landing page.")
    lines.append("")
    return "\n".join(lines)


def repeated_theme_findings(posts):
    fetched = [post for post in posts if not post.get("error")]
    if not fetched:
        return []
    buckets = {}
    for post in fetched:
        seen = set()
        for finding in post["findings"]:
            for item in finding["issues"]:
                if item["severity"] not in {"high", "medium"}:
                    continue
                if item["scope"] == "article":
                    continue
                key = (finding["signal"], item["severity"], item["summary"])
                if key in seen:
                    continue
                seen.add(key)
                buckets.setdefault(key, []).append(item)
    rows = []
    for (signal, severity, summary), items in buckets.items():
        if len(items) < len(fetched):
            continue
        rows.append({
            "signal": signal,
            "severity": severity,
            "posts": len(fetched),
            "summary": summary,
            "suggested_fix": items[0]["suggested_fix"],
        })
    rows.sort(key=lambda row: RANK[row["severity"]], reverse=True)
    return rows


def build_report(posts, selection_note, source):
    today = datetime.now().astimezone().date().isoformat()
    context = (
        "The vault at ~/PATI/LLM-Wiki has no `90-sources/search-engine-land/sel-digest-2026-10-21.md`. "
        "The freshest digest on disk is `sel-digest-2026-10-20.md` (content pruning, social search, local AI). "
        "The clutter spark is Search Engine Land, 20 October 2026, "
        "[Google's clutterScore](https://searchengineland.com/google-clutterscore-seo-497178): "
        "intrusive pop-ups, sticky and floating layers, third-party scripts, and repeated templates. "
        "That article says the leaked field has no public formula, so this audit does not invent a clutterScore. "
        "`knowledge_base/AEO_GEO_GUIDELINES.md` already forbids a forced interstitial on an article. "
        "Existing writers were not extended: `scripts/patch_mobile.py` pushes collection HTML, "
        "`scripts/audit_article_images.py` reads the Admin API, and `scripts/patch_tables.py` writes article bodies. "
        "The spacer-image skip and the `article-table-wrapper` name are reused as checks only."
    )
    return {
        "date": today,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": source,
        "user_agent": MOBILE_UA,
        "shopify_writes": 0,
        "theme_edits": 0,
        "context": context,
        "selection_note": selection_note,
        "post_count": len(posts),
        "posts": posts,
        "repeated_theme": repeated_theme_findings(posts),
    }


def default_paths(today):
    return (
        "docs/MOBILE_CLUTTER_AUDIT_%s.md" % today,
        "docs/MOBILE_CLUTTER_AUDIT_%s.json" % today,
    )


def load_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def select_posts(atom_xml, tracker_csv, limit):
    atom_entries = blog_entries_from_atom(atom_xml) if atom_xml else []
    tracker_entries = blog_entries_from_tracker(tracker_csv) if tracker_csv else []
    if atom_entries:
        selected = atom_entries[:limit]
        source = "public atom feed %s" % ATOM_URL
        note = (
            "Selected the %s newest `/blogs/news/` entries from the public Atom feed. "
            "Product, collection, home, checkout, and landing URLs are ignored. "
            "The tracker is a cross-check, not the sort."
        ) % len(selected)
    elif tracker_entries:
        selected = tracker_entries[:limit]
        source = "PUBLISHED_ARTICLES_TRACKER.csv"
        note = (
            "The Atom feed was empty or unavailable. Selected the %s newest blog URLs "
            "with a YYYY-MM-DD date in PUBLISHED_ARTICLES_TRACKER.csv."
        ) % len(selected)
    else:
        selected = []
        source = "none"
        note = "No blog URLs were available from the Atom feed or the tracker."
    annotate_tracker(selected, tracker_entries)
    dupes = duplicate_titles(selected)
    if dupes:
        rendered = "; ".join(
            "%s (%s)" % (title, ", ".join(handle_of(url) for url in urls))
            for title, urls in dupes.items()
        )
        note += " Shared titles in this set: %s. Consolidation is a separate decision and needs Kevin GO." % rendered
    return selected, note, source


def audit_urls(pairs, pause_s=0.4):
    posts = []
    for index, meta in enumerate(pairs):
        url = meta["url"]
        if not blog_article_url(url):
            posts.append(error_post(url, "refused: not a /blogs/news/ article URL", meta))
            continue
        try:
            status, final, html = fetch(url)
        except urllib.error.HTTPError as exc:
            posts.append(error_post(url, "HTTP %s" % exc.code, meta))
            continue
        except urllib.error.URLError as exc:
            posts.append(error_post(url, "fetch failed: %s" % exc.reason, meta))
            continue
        final_base = final.split("#")[0].split("?")[0].rstrip("/")
        if not blog_article_url(final_base):
            posts.append(error_post(
                url,
                "refused after redirect to %s" % final,
                meta,
            ))
            continue
        meta = dict(meta)
        meta["url"] = final_base
        try:
            posts.append(audit_html(html, final_base, meta))
            posts[-1]["http_status"] = status
        except Exception as exc:  # noqa: BLE001 — one bad page should not drop the report
            posts.append(error_post(final_base, "parse failed: %s" % exc, meta))
        if pause_s and index < len(pairs) - 1:
            time.sleep(pause_s)
    return posts


def write_report(report, md_path, json_path):
    markdown = render_markdown(report)
    if md_path:
        with open(md_path, "w", encoding="utf-8") as handle:
            handle.write(markdown)
    if json_path:
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=True)
            handle.write("\n")
    return markdown


def main(argv):
    if any(flag in argv for flag in ("--apply", "--publish", "--push")):
        print("This audit is read-only. It does not apply, publish, or push.", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description="Read-only mobile clutter audit for wellnessnest.co blog articles.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--url", action="append", default=[])
    parser.add_argument("--html", help="Audit this local HTML file. Requires one --url blog article.")
    parser.add_argument("--atom", help="Read this Atom file instead of the live feed.")
    parser.add_argument("--tracker", default="PUBLISHED_ARTICLES_TRACKER.csv")
    parser.add_argument("--md", default="")
    parser.add_argument("--json", dest="json_path", default="")
    parser.add_argument("--pause", type=float, default=0.4)
    args = parser.parse_args(argv)
    if args.limit < 1:
        print("--limit must be >= 1", file=sys.stderr)
        return 2
    for url in args.url:
        if not blog_article_url(url):
            print(
                "Refusing %s. This audit only reads https://wellnessnest.co/blogs/news/<handle>."
                % url,
                file=sys.stderr,
            )
            return 2

    tracker_csv = ""
    if args.tracker:
        try:
            tracker_csv = load_text(args.tracker)
        except OSError:
            tracker_csv = ""

    if args.html:
        if len(args.url) != 1:
            print("--html requires exactly one --url blog article.", file=sys.stderr)
            return 2
        html = load_text(args.html)
        meta = {"published_at": "unknown", "in_tracker": "not_checked"}
        if tracker_csv:
            tracker_entries = blog_entries_from_tracker(tracker_csv)
            annotate_tracker([{"url": args.url[0], **meta}], tracker_entries)
            matched = next((row for row in tracker_entries if row["url"].rstrip("/") == args.url[0].rstrip("/")), None)
            if matched:
                meta["in_tracker"] = True
                meta["tracker_ticket"] = matched.get("tracker_ticket") or ""
                meta["published_at"] = matched.get("published_at") or "unknown"
            else:
                meta["in_tracker"] = False
        posts = [audit_html(html, args.url[0].rstrip("/"), meta)]
        note = "Audited one local HTML file. No network fetch."
        source = "local html"
    elif args.url:
        pairs = [{"url": url.rstrip("/"), "published_at": "unknown", "title": "", "in_tracker": "not_checked"} for url in args.url]
        if tracker_csv:
            annotate_tracker(pairs, blog_entries_from_tracker(tracker_csv))
        posts = audit_urls(pairs, pause_s=args.pause)
        note = "Audited the blog URLs passed on the command line."
        source = "cli urls"
    else:
        if args.atom:
            atom_xml = load_text(args.atom)
            source_feed = args.atom
        else:
            try:
                _status, _final, atom_xml = fetch(ATOM_URL)
            except (urllib.error.URLError, urllib.error.HTTPError) as exc:
                atom_xml = ""
                source_feed = "atom fetch failed: %s" % exc
            else:
                source_feed = ATOM_URL
        selected, note, source = select_posts(atom_xml, tracker_csv, args.limit)
        if not selected:
            print(note, file=sys.stderr)
            return 1
        note = note + " Feed: %s." % source_feed
        posts = audit_urls(selected, pause_s=args.pause)

    report = build_report(posts, note, source if not args.html and not args.url else source)
    today = report["date"]
    md_path, json_path = args.md, args.json_path
    if not md_path and not json_path and not args.html:
        md_path, json_path = default_paths(today)
    markdown = write_report(report, md_path, json_path)
    if not md_path:
        print(markdown)
    else:
        print("Wrote %s" % md_path)
        if json_path:
            print("Wrote %s" % json_path)
        for post in posts:
            top = [
                "%s:%s" % (finding["signal"], finding["severity"])
                for finding in post.get("findings") or []
                if finding["severity"] in {"high", "medium"}
            ]
            print("%s %s %s" % (post.get("highest_severity"), post.get("handle"), ", ".join(top) or post.get("error")))
    if posts and all(post.get("error") for post in posts):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

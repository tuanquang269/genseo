#!/usr/bin/env python3
"""
verify_published.py — POST-PUBLISH gate. Fetches the LIVE article from Shopify and
confirms the publish actually added everything (schema, author, table). This catches the
failure where a model publishes via the wrong path (MCP/GraphQL/curl) that skips schema.

Author evidence (Kevin 2026-10-20): the theme main-article section emits Article
JSON-LD with an author. That block is not appended to body_html. When this script
fetches the public article HTML and that HTML has an Article node with an author,
the author check passes. The theme author can be a different person than the
expected blog author; that tolerance stays. Otherwise the only author requirement
is a visible byline link to /pages/<author> in body_html. A body Article or Person
JSON-LD block is never required.

Expected blog author (Kevin 2026-10-21): Mike Moretti, Co-founder, Wellness Nest,
https://wellnessnest.co/pages/mike-moretti. That page 404s. This script does not
create it. Without a theme Article author, the Shopify author field must be
Mike Moretti.

Usage: python3 verify_published.py <ARTICLE_ID> [BLOG_ID]
Exit 0 = live article is good. Exit 1 = something missing → re-publish via the python publisher.
"""
import html as html_lib
import json
import re
import sys
import urllib.error
import urllib.request

NEWS_BLOG_ID = "104008483131"
NEWS_BLOG_HANDLE = "news"
PUBLIC_ORIGIN = "https://wellnessnest.co"

# Blog Article author (Kevin 2026-10-21). Role is exactly this string.
EXPECTED_BLOG_AUTHOR = "Mike Moretti"
EXPECTED_BLOG_ROLE = "Co-founder, Wellness Nest"
EXPECTED_BLOG_AUTHOR_HANDLE = "mike-moretti"
EXPECTED_BLOG_AUTHOR_URL = PUBLIC_ORIGIN + "/pages/" + EXPECTED_BLOG_AUTHOR_HANDLE
_UA = "GenSeoVerify/1.0 (post-publish check; +https://wellnessnest.co)"

_JSONLD_RE = re.compile(
    r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)
_HREF_RE = re.compile(r"""href\s*=\s*(["'])(.*?)\1""", re.I | re.S)
_AUTHOR_PAGE_RE = re.compile(
    r"^(?:(?:https?:)?//[^/?#]+)?/pages/([a-z0-9-]+)/?(?:[?#].*)?$",
    re.I,
)
_HANDLE_RE = re.compile(r"^[a-z0-9-]+$", re.I)

AUTHOR_EVIDENCE_FAIL = (
    "no Article author on the live page (or the live page was not fetched) "
    "and no visible /pages/<author> byline in body_html"
)


def _as_text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    if isinstance(value, str):
        return value
    return None


def _types(node):
    raw = node.get("@type")
    if isinstance(raw, str):
        return [raw.strip()]
    if isinstance(raw, list):
        return [item.strip() for item in raw if isinstance(item, str)]
    return []


def _iter_nodes(node):
    if isinstance(node, list):
        for item in node:
            yield from _iter_nodes(item)
        return
    if not isinstance(node, dict):
        return
    yield node
    graph = node.get("@graph")
    if graph is not None:
        yield from _iter_nodes(graph)


def _author_present(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_author_present(item) for item in value)
    if isinstance(value, dict):
        name = value.get("name")
        if isinstance(name, str) and name.strip():
            return True
        for key in ("url", "@id"):
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                return True
    return False


def article_jsonld_has_author(page_html):
    """True when page HTML contains Article JSON-LD whose author is non-empty."""
    text = _as_text(page_html)
    if not text:
        return False
    for block in _JSONLD_RE.findall(text):
        raw = html_lib.unescape(block).strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for node in _iter_nodes(data):
            if "Article" in _types(node) and _author_present(node.get("author")):
                return True
    return False


def visible_author_byline(body_html):
    """True when body_html has an anchor to /pages/<author>."""
    text = _as_text(body_html)
    if not text:
        return False
    for match in _HREF_RE.finditer(text):
        href = html_lib.unescape(match.group(2)).strip()
        if _AUTHOR_PAGE_RE.match(href):
            return True
    return False


def has_author_evidence(body_html, live_html=None):
    """Author check.

    live_html is the public article HTML when that fetch happened, otherwise None.
    An Article author on that page is enough. Otherwise only the visible
    /pages/<author> byline in body_html is required. Body JSON-LD is not evidence.
    """
    if live_html is not None and article_jsonld_has_author(live_html):
        return True
    return visible_author_byline(body_html)


def storefront_article_url(article, blog_id, blog_handle=None):
    """Public article URL, or None when there is no live page to fetch."""
    handle = (article.get("handle") or "").strip()
    if not article.get("published_at") or not _HANDLE_RE.match(handle):
        return None
    if blog_handle is None:
        if str(blog_id) != NEWS_BLOG_ID:
            return None
        blog_handle = NEWS_BLOG_HANDLE
    blog_handle = str(blog_handle).strip().strip("/")
    if not _HANDLE_RE.match(blog_handle):
        return None
    return f"{PUBLIC_ORIGIN}/blogs/{blog_handle}/{handle}"


def fetch_live_html(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        status = getattr(res, "status", None) or res.getcode()
        if status != 200:
            return None
        return res.read().decode("utf-8", "replace")


def live_html_for(article, blog_id, opener=None, blog_handle=None):
    """Fetch public article HTML. None when there is no URL or the fetch fails."""
    url = storefront_article_url(article, blog_id, blog_handle=blog_handle)
    if not url:
        return None
    try:
        return _as_text((opener or fetch_live_html)(url))
    except (OSError, urllib.error.URLError, ValueError):
        return None


def author_field_failures(raw_author, theme_author_present):
    """Shopify author field.

    Mike Moretti is the expected blog author. A non-empty theme Article author
    still passes when the field names someone else (live pages can still say
    Dr. Marcus Hale). An empty or placeholder field fails either way.
    """
    name = (raw_author or "").strip()
    if name == EXPECTED_BLOG_AUTHOR:
        return []
    if not name or name == "Your Brand Research Team":
        return ["author field is generic ('%s')" % (raw_author,)]
    if theme_author_present:
        return []
    return [
        "author field is '%s'; expected blog author is %s, %s"
        % (name, EXPECTED_BLOG_AUTHOR, EXPECTED_BLOG_ROLE)
    ]


def verification_failures(article, live_html=None):
    """Failure strings for one article. Empty means the post-publish check passed."""
    body = article.get("body_html") or ""
    fails = []
    if (article.get("title") or "").strip() in ("", "Generated Article"):
        fails.append("title is empty/'Generated Article'")
    if "FAQPage" not in body:
        fails.append(
            "no FAQPage schema in live body (publish path skipped schema → use shopify_publisher.py)"
        )
    if "application/ld+json" not in body:
        fails.append("no JSON-LD schema at all (wrong publish path)")
    theme_author = live_html is not None and article_jsonld_has_author(live_html)
    if not has_author_evidence(body, live_html):
        fails.append(AUTHOR_EVIDENCE_FAIL)
    fails.extend(author_field_failures(article.get("author"), theme_author))
    if "<table" not in body:
        fails.append("no comparison <table> in live body")
    return fails


def fetch_admin_article(shop, token, api, blog_id, article_id):
    url = f"https://{shop}/admin/api/{api}/blogs/{blog_id}/articles/{article_id}.json"
    req = urllib.request.Request(url, headers={"X-Shopify-Access-Token": token})
    with urllib.request.urlopen(req) as res:
        payload = json.loads(res.read().decode("utf-8"))
    return payload["article"]


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: python3 verify_published.py <ARTICLE_ID> [BLOG_ID]")
        return 2
    aid = args[0]
    blog = args[1] if len(args) > 1 else NEWS_BLOG_ID
    from genseo_config import API, SHOP, TOKEN

    article = fetch_admin_article(SHOP, TOKEN, API, blog, aid)
    live_html = live_html_for(article, blog)
    body = article.get("body_html") or ""
    fails = verification_failures(article, live_html)
    if live_html is None:
        live_bit = "not-fetched"
    elif article_jsonld_has_author(live_html):
        live_bit = "article-author"
    else:
        live_bit = "no-article-author"

    print(f"=== VERIFY LIVE article {aid} ===")
    print(f"  title: {article.get('title')}")
    print(f"  handle: {article.get('handle')}")
    print(f"  author: {article.get('author')}")
    print(
        f"  FAQPage:{('FAQPage' in body)}  ld+json:{('application/ld+json' in body)}"
        f"  table:{('<table' in body)}  byline:{visible_author_byline(body)}  live:{live_bit}"
    )
    if fails:
        print("FAILED:")
        for item in fails:
            print("  ✗ " + item)
        print(
            "\nRESULT: ✗ Re-publish with: python3 /Users/kevinkreative/genseo/scripts/"
            f"shopify_publisher.py update <draft.md> {blog} {aid}"
        )
        return 1
    print("\nRESULT: ✓ Live article verified — schema, author, table all present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

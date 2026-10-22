"""Deep content pages for the GEO traffic report.

One definition. Blog articles, guides, and listicle/landing pages count.
Home, the collections index, cart, checkout, account, search, and policy
pages do not. A leading Shopify market prefix (/de, /es-es) is removed
before those rules run.
"""
import re
from urllib.parse import unquote, urlsplit

DEEP_CONTENT_PAGE = {
    "description": (
        "A deep content page is a blog article (/blogs/<blog>/<article>), "
        "a guide (/guides/<slug>), or a listicle/landing page (/pages/<handle>). "
        "The blog index (/blogs and /blogs/<blog>) is not an article. "
        "Home, the collections index, cart, checkout, account, search, and policy "
        "pages do not count. A leading Shopify market prefix such as /de or /es-es "
        "is ignored."
    ),
    "locale_prefix": r"^[a-z]{2}(?:-[a-z]{2})?$",
    "counts": (
        ("blog_article", r"^/blogs/[^/]+/[^/]+$"),
        ("guide", r"^/guides/[^/]+(?:/[^/]+)*$"),
        ("listicle_or_landing", r"^/pages/[^/]+$"),
    ),
    "never": {
        "home": ("/",),
        "collections_index": ("/collections", "/collections/all"),
        "prefixes": (
            "/cart",
            "/checkout",
            "/checkouts",
            "/account",
            "/search",
            "/policies",
        ),
        "policy_page_handles": (
            "privacy-policy",
            "refund-policy",
            "shipping-policy",
            "terms-of-service",
            "contact-information",
            "legal-notice",
            "subscription-policy",
        ),
        "not_article_slugs": ("tagged",),
    },
}

_LOCALE = re.compile(DEEP_CONTENT_PAGE["locale_prefix"])
_COUNTS = tuple(
    (name, re.compile(pattern)) for name, pattern in DEEP_CONTENT_PAGE["counts"]
)


def normalize_path(value):
    """Path only, lowercased, no query, no trailing slash except the root."""
    if value is None:
        return "/"
    raw = str(value).strip()
    if not raw:
        return "/"
    if "://" in raw:
        raw = urlsplit(raw).path or "/"
    else:
        raw = raw.split("?", 1)[0].split("#", 1)[0]
    raw = unquote(raw).lower()
    if not raw.startswith("/"):
        raw = "/" + raw
    while "//" in raw:
        raw = raw.replace("//", "/")
    if len(raw) > 1 and raw.endswith("/"):
        raw = raw[:-1]
    return raw or "/"


def strip_market_locale(path):
    """Drop one leading Shopify market prefix. The path is already normalized."""
    parts = path.split("/")
    if len(parts) >= 2 and parts[1] and _LOCALE.fullmatch(parts[1]):
        rest = "/" + "/".join(parts[2:])
        if len(rest) > 1 and rest.endswith("/"):
            rest = rest[:-1]
        return rest or "/"
    return path


def _prefix_excluded(path, prefix):
    return path == prefix or path.startswith(prefix + "/")


def _never_counts(path):
    never = DEEP_CONTENT_PAGE["never"]
    if path in never["home"] or path in never["collections_index"]:
        return True
    for prefix in never["prefixes"]:
        if _prefix_excluded(path, prefix):
            return True
    if path.startswith("/pages/"):
        handle = path[len("/pages/"):]
        if handle in never["policy_page_handles"]:
            return True
    if path.startswith("/blogs/"):
        slug = path.rsplit("/", 1)[-1]
        if slug in never["not_article_slugs"]:
            return True
    return False


def is_deep_content_page(value):
    """True when value is a blog article, guide, or listicle/landing page."""
    path = strip_market_locale(normalize_path(value))
    if _never_counts(path):
        return False
    return any(pattern.fullmatch(path) for _name, pattern in _COUNTS)

#!/usr/bin/env python3
"""Two audit fixes in one PUT to sections/main-product.liquid.

1. aggregateRating in the Product JSON-LD (ACTION-PLAN 1.1)
   Judge.me syncs into the standard `reviews.rating` / `reviews.rating_count`
   metafields — the same source the theme's own star widget
   (blocks/product-rating.liquid) already reads — but the JSON-LD block never
   emitted them, so no product SERP could show stars.

   Reality check before you expect 953 pages of stars: only 42 published
   products currently carry a rating metafield (3,864 reviews total). The rest
   have no reviews yet. This edit is written so every product Judge.me syncs
   later picks it up automatically.

2. The extra <h1> (ACTION-PLAN 1.4)
   The "page" popup block renders the linked policy page title as an <h1>, so
   every product page shipped two H1s ("Return & Refund Policy" being the
   second). Demoted to <h2>; the class stays `h2` so nothing moves visually.

   The same markup exists in two files. What actually renders on a product page
   is `blocks/product_popup.liquid` (the block id in the DOM ends in
   `__product_popup_*`); the copy inside sections/main-product.liquid is the
   older section-block path. Both are patched — fixing only the section leaves
   the live page unchanged, which is exactly how this was missed the first time.

   NOT fixed here: the rendered DOM also carries two more H1s ("UNLOCK",
   "10% OFF"). Those come from a Klaviyo popup rich-text block
   (`klaviyo-form-richtext`), not the theme — fix them in the Klaviyo form
   editor.

Usage:
    python3 scripts/add_rating_and_fix_h1_theme.py --dry-run
    python3 scripts/add_rating_and_fix_h1_theme.py --apply
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

CONFIG = os.path.expanduser("~/.genseo/shopify_token.json")
API_VERSION = "2026-04"
THEME = "100000000010"
ASSET = "sections/main-product.liquid"
POPUP_ASSET = "blocks/product_popup.liquid"
BACKUP_DIR = Path("backups/20260802")
BACKUP = BACKUP_DIR / "sections__main-product.liquid"
POPUP_BACKUP = BACKUP_DIR / "blocks__product_popup.liquid"

# a product that has reviews, and one that does not — both must stay valid
VERIFY_RATED = "https://yourdomain.com/products/dymatize-nutrition-iso-100-hydrolyzed-1-3-5-lb"
VERIFY_UNRATED = "https://yourdomain.com/products/mutant-whey-whey-protein"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

# the shippingDetails array closes on the `],` line — the insert goes between that
# and "offers", NOT before it, or the object lands inside the shipping array
RATING_ANCHOR = '      ],\n      "offers": [\n'
RATING_ANCHOR_HEAD = '      ],\n'
RATING_ANCHOR_TAIL = '      "offers": [\n'

RATING_ADDITION = """      {%- assign review_count = product.metafields.reviews.rating_count.value | default: 0 -%}
      {%- if product.metafields.reviews.rating.value != blank and review_count > 0 -%}
        {%- comment -%}
          Judge.me syncs into reviews.rating / reviews.rating_count. Same source
          as the on-page star widget, so the markup always matches what a user
          sees — which is what Google requires of review snippets.
        {%- endcomment -%}
        "aggregateRating": {
          "@type": "AggregateRating",
          "ratingValue": {{ product.metafields.reviews.rating.value.rating | json }},
          "bestRating": {{ product.metafields.reviews.rating.value.scale_max | json }},
          "worstRating": {{ product.metafields.reviews.rating.value.scale_min | json }},
          "reviewCount": {{ review_count | json }}
        },
      {%- endif -%}
"""

H1_BEFORE = '<h1 class="h2">{{ block.settings.page.title }}</h1>'
H1_AFTER = '<h2 class="h2">{{ block.settings.page.title }}</h2>'


with open(CONFIG) as handle:
    CFG = json.load(handle)
SHOP = CFG["shop"]
TOKEN = CFG["access_token"]


def api(path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"https://{SHOP}/admin/api/{API_VERSION}/{path}",
        data=data,
        method=method,
        headers={"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(request, timeout=45).read())


def get_asset(key=ASSET):
    query = urllib.parse.urlencode({"asset[key]": key})
    return api(f"themes/{THEME}/assets.json?{query}")["asset"]["value"]


def put_asset(value, key=ASSET):
    return api(
        f"themes/{THEME}/assets.json",
        method="PUT",
        payload={"asset": {"key": key, "value": value}},
    )


def fetch(url):
    # cache-bust: an asset PUT takes a moment to propagate and a stale render
    # would look exactly like a failed patch
    url = f"{url}?nocache={int(time.time())}"
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=45) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        return response.read().decode("utf-8", errors="replace")


def product_schema(html):
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        parsed = json.loads(raw)  # raises if the Liquid edit produced invalid JSON
        if isinstance(parsed, dict) and parsed.get("@type") == "Product":
            return parsed
    raise RuntimeError("Product JSON-LD block not found")


def verify_live():
    """Rated page gains the rating, unrated page stays valid, both drop to one H1."""
    try:
        rated_html = fetch(VERIFY_RATED)
        unrated_html = fetch(VERIFY_UNRATED)
        rated = product_schema(rated_html)
        product_schema(unrated_html)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"

    rating = rated.get("aggregateRating")
    if not rating:
        return False, "aggregateRating missing on the rated product"
    for key in ("ratingValue", "reviewCount"):
        if not rating.get(key):
            return False, f"aggregateRating.{key} empty"
    for label, html in (("rated", rated_html), ("unrated", unrated_html)):
        count = len(re.findall(r"<h1[\s>]", html))
        if count != 1:
            return False, f"{label} page has {count} h1 elements in raw HTML, expected 1"
    return True, rating


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.apply or args.dry_run):
        parser.error("pass --dry-run or --apply")

    current = get_asset()
    popup = get_asset(POPUP_ASSET)
    if "aggregateRating" in current and H1_BEFORE not in popup:
        print("Already patched. Nothing to do.")
        return 0
    if current.count(RATING_ANCHOR) != 1:
        print(f"FAIL: rating anchor found {current.count(RATING_ANCHOR)}×, expected 1", file=sys.stderr)
        return 1
    if popup.count(H1_BEFORE) != 1:
        print(f"FAIL: popup h1 found {popup.count(H1_BEFORE)}×, expected 1", file=sys.stderr)
        return 1

    patched = current.replace(
        RATING_ANCHOR, RATING_ANCHOR_HEAD + RATING_ADDITION + RATING_ANCHOR_TAIL
    )
    patched = patched.replace(H1_BEFORE, H1_AFTER)  # legacy copy in the section
    patched_popup = popup.replace(H1_BEFORE, H1_AFTER)

    if args.dry_run:
        print("--- insert before the offers array ---")
        print(RATING_ADDITION)
        print(f"--- {H1_BEFORE}\n+++ {H1_AFTER}")
        print(f"{ASSET} {len(current)} -> {len(patched)} chars")
        print(f"{POPUP_ASSET} {len(popup)} -> {len(patched_popup)} chars")
        return 0

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for path, value in ((BACKUP, current), (POPUP_BACKUP, popup)):
        if not path.is_file():
            path.write_bytes(value.encode("utf-8"))
            print(f"backup written: {path}")
        if path.read_bytes().decode("utf-8") != value:
            print(f"FAIL: {path} does not match the live asset. Re-take it.", file=sys.stderr)
            return 1

    print("Applying patch to LIVE theme...")
    put_asset(patched)
    put_asset(patched_popup, POPUP_ASSET)
    time.sleep(3)
    print("Verifying live pages...")
    ok, detail = verify_live()
    if not ok:
        print(f"VERIFY FAILED: {detail}", file=sys.stderr)
        print("Reverting from backup...", file=sys.stderr)
        put_asset(BACKUP.read_bytes().decode("utf-8"))
        put_asset(POPUP_BACKUP.read_bytes().decode("utf-8"), POPUP_ASSET)
        print("reverted.", file=sys.stderr)
        return 1

    print("OK. Rendered Product schema now carries:")
    print(json.dumps(detail, indent=2))
    print("Both verified pages render exactly one <h1>.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

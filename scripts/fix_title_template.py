#!/usr/bin/env python3
"""Fix the <title> template in layout/theme.liquid (ACTION-PLAN 1.2).

Two defects, one edit:

1. The tag spans multiple lines with no whitespace control, so every page on the
   site emitted a literal newline and six spaces inside <title> — 498 of the 536
   crawled pages. Google collapses it, but every non-rendering consumer (AI
   crawlers, social scrapers, SEO tools) sees the raw string.

2. " – Your Brand" (15 chars) was appended unconditionally. Median product
   title is already 76 characters against a ~60-character SERP display, so the
   suffix pushed the keyword out of view for no gain. It is now appended only
   when the base title is short enough that the result still fits (45 + 15 = 60).

Not covered here: the 159 over-length blog titles and the long product-title
pattern itself. Those are content edits, not template edits.

ponytail: 45 is a character count, not a pixel measurement — Google truncates on
width, so a title of wide characters can still clip. Character count is the
approximation every SEO tool uses and it is worth exactly as much scrutiny.

Usage:
    python3 scripts/fix_title_template.py --dry-run
    python3 scripts/fix_title_template.py --apply
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
THEME = "183190880571"
ASSET = "layout/theme.liquid"
BACKUP = Path("backups/20260802/layout__theme.liquid")
SUFFIX = " – Your Brand"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

VERIFY_URLS = (
    "https://wellnessnest.co/",
    "https://wellnessnest.co/products/dymatize-nutrition-iso-100-hydrolyzed-1-3-5-lb",
    "https://wellnessnest.co/collections/protein-powder",
    "https://wellnessnest.co/blogs/news/the-ultimate-guide-to-protein-powders-in-{{market}}",
)

BEFORE = """    <title>
      {{ page_title }}
      {%- if current_tags %} &ndash; tagged "{{ current_tags | join: ', ' }}"{% endif -%}
      {%- if current_page != 1 %} &ndash; Page {{ current_page }}{% endif -%}
      {%- unless page_title contains shop.name %} &ndash; {{ shop.name }}{% endunless -%}
    </title>"""

AFTER = """    <title>
      {%- liquid
        # Built as one string so the tag emits no stray whitespace, and so the
        # shop-name suffix can be dropped when it would push the title past the
        # ~60-character SERP display. Do not re-expand this across lines.
        assign seo_title = page_title | strip
        if current_tags
          assign tag_list = current_tags | join: ', '
          assign seo_title = seo_title | append: ' – tagged "' | append: tag_list | append: '"'
        endif
        if current_page != 1
          assign seo_title = seo_title | append: ' – Page ' | append: current_page
        endif
        unless seo_title contains shop.name
          assign title_length = seo_title | size
          if title_length <= 45
            assign seo_title = seo_title | append: ' – ' | append: shop.name
          endif
        endunless
        echo seo_title
      -%}
    </title>"""


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


def get_asset():
    query = urllib.parse.urlencode({"asset[key]": ASSET})
    return api(f"themes/{THEME}/assets.json?{query}")["asset"]["value"]


def put_asset(value):
    return api(
        f"themes/{THEME}/assets.json",
        method="PUT",
        payload={"asset": {"key": ASSET, "value": value}},
    )


def page_title(url):
    request = urllib.request.Request(f"{url}?nocache={int(time.time())}", headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=45) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        html = response.read().decode("utf-8", errors="replace")
    match = re.search(r"<title>(.*?)</title>", html, re.S)
    if not match:
        raise RuntimeError(f"no <title> on {url}")
    return match.group(1)


def verify_live():
    titles = {}
    for url in VERIFY_URLS:
        try:
            title = page_title(url)
        except Exception as exc:
            return False, f"{url}: {type(exc).__name__}: {exc}"
        if not title.strip():
            return False, f"{url}: empty title"
        if title != title.strip() or "\n" in title:
            return False, f"{url}: title still carries whitespace: {title!r}"
        if len(title) > 60 and title.endswith(SUFFIX):
            return False, f"{url}: over-length title still carries the suffix: {title!r}"
        titles[url] = title
        time.sleep(1.2)  # the origin rate-limits browser UAs above ~2 req/s
    return True, titles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.apply or args.dry_run):
        parser.error("pass --dry-run or --apply")

    current = get_asset()
    if "assign seo_title" in current:
        print("Already patched. Nothing to do.")
        return 0
    if current.count(BEFORE) != 1:
        print(f"FAIL: title block found {current.count(BEFORE)}×, expected 1", file=sys.stderr)
        return 1

    patched = current.replace(BEFORE, AFTER)

    if args.dry_run:
        print("--- BEFORE ---")
        print(BEFORE)
        print("\n+++ AFTER +++")
        print(AFTER)
        return 0

    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.is_file():
        BACKUP.write_bytes(current.encode("utf-8"))
        print(f"backup written: {BACKUP}")
    if BACKUP.read_bytes().decode("utf-8") != current:
        print("FAIL: backup does not match the live asset. Re-take it.", file=sys.stderr)
        return 1

    print("Applying patch to LIVE theme...")
    put_asset(patched)
    time.sleep(3)
    print("Verifying live pages...")
    ok, detail = verify_live()
    if not ok:
        print(f"VERIFY FAILED: {detail}", file=sys.stderr)
        print("Reverting from backup...", file=sys.stderr)
        put_asset(BACKUP.read_bytes().decode("utf-8"))
        print("reverted.", file=sys.stderr)
        return 1

    for url, title in detail.items():
        print(f"{len(title):>3}  {title}\n     {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

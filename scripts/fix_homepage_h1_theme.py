#!/usr/bin/env python3
"""Give the homepage a real text H1 (ACTION-PLAN 2.6).

The homepage's only h1 was `<h1 class="header__heading">` wrapping the logo link.
Two problems, one of them worse than the audit recorded:

1. The heading carried no text at all — its accessible name came from the logo's
   `alt`, so the page had no heading describing what it is about.
2. The logo block contains an inline `<style>` for the mobile logo swap, and that
   style lives INSIDE the h1. Anything reading `h1.textContent` rather than
   rendering the page — most SEO crawlers, scrapers and AI bots — reads a CSS
   media query as the homepage heading.

Fix: the logo wrapper becomes a plain div, and a real text h1 is emitted using the
theme's own `visually-hidden` a11y class (the same pattern the collection banner
already uses for its "Collection: " prefix). No visual change.

ponytail: the h1 is visually hidden rather than designed into the hero, because a
visible heading is a layout decision, not a bug fix. If Owner wants it on screen,
that is a hero-section change and this snippet edit should be reverted first.

Usage:
    python3 scripts/fix_homepage_h1_theme.py --dry-run
    python3 scripts/fix_homepage_h1_theme.py --apply
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
ASSET = "snippets/header-logo.liquid"
BACKUP = Path("backups/20260802/snippets__header-logo.liquid")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

HOME = "https://yourdomain.com/"
# header-logo renders site-wide; these must keep working and must NOT gain an h1.
OTHER_PAGES = (
    "https://yourdomain.com/products/dymatize-nutrition-iso-100-hydrolyzed-1-3-5-lb",
    "https://yourdomain.com/collections/protein-powder",
)

H1_TEXT = "Supplement Store in {{MARKET}}"

OPEN_BEFORE = """{%- if request.page_type == 'index' -%}
    <h1 class="header__heading">
{%- endif -%}
"""

OPEN_AFTER = """{%- if request.page_type == 'index' -%}
    {%- comment -%}
      The logo used to BE the homepage h1, so the only heading on the page was an
      image — and because the mobile-logo <style> block below sits inside it, any
      consumer reading h1 text content got a CSS media query. The logo is now a
      div; the real heading is the visually-hidden h1 above it, using the theme's
      own a11y class (same pattern as the collection banner's "Collection: ").
    {%- endcomment -%}
    <h1 class="visually-hidden">""" + H1_TEXT + """ &ndash; {{ shop.name }}</h1>
    <div class="header__heading">
{%- endif -%}
"""

CLOSE_BEFORE = """{%- if request.page_type == 'index' -%}
    </h1>
{%- endif -%}"""

CLOSE_AFTER = """{%- if request.page_type == 'index' -%}
    </div>
{%- endif -%}"""

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


def fetch(url):
    request = urllib.request.Request(f"{url}?nocache={int(time.time())}", headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=45) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        return response.read().decode("utf-8", errors="replace")


def h1_blocks(html):
    return re.findall(r"<h1\b[^>]*>(.*?)</h1>", html, re.S)


def verify_live():
    try:
        home = fetch(HOME)
    except Exception as exc:
        return False, f"{HOME}: {type(exc).__name__}: {exc}"

    blocks = h1_blocks(home)
    if len(blocks) != 1:
        return False, f"homepage has {len(blocks)} h1 elements, expected 1"
    inner = blocks[0]
    if H1_TEXT not in inner:
        return False, f"homepage h1 does not carry the heading text: {inner[:120]!r}"
    if "<style" in inner.lower() or "@media" in inner:
        return False, "homepage h1 still contains a <style> block"
    # the logo itself must survive the unwrap
    if 'class="header__heading"' not in home or "header__heading-logo" not in home:
        return False, "logo markup missing after the unwrap"

    for url in OTHER_PAGES:
        time.sleep(1.3)  # the origin rate-limits browser UAs above ~2 req/s
        try:
            html = fetch(url)
        except Exception as exc:
            return False, f"{url}: {type(exc).__name__}: {exc}"
        if H1_TEXT in html:
            return False, f"{url}: homepage-only h1 leaked onto a non-index template"
        if "header__heading-logo" not in html:
            return False, f"{url}: header logo missing"
    return True, re.sub(r"\s+", " ", inner).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.apply or args.dry_run):
        parser.error("pass --dry-run or --apply")

    current = get_asset()
    if 'class="visually-hidden"' in current and "header__heading" in current:
        print("Already patched. Nothing to do.")
        return 0
    for name, anchor in (("open", OPEN_BEFORE), ("close", CLOSE_BEFORE)):
        if current.count(anchor) != 1:
            print(f"FAIL: {name} anchor found {current.count(anchor)}x, expected 1", file=sys.stderr)
            return 1

    patched = current.replace(OPEN_BEFORE, OPEN_AFTER).replace(CLOSE_BEFORE, CLOSE_AFTER)
    if patched.count("<h1") != 1 or patched.count("</h1>") != 1:
        print("FAIL: patched snippet does not have exactly one balanced h1", file=sys.stderr)
        return 1

    if args.dry_run:
        print(OPEN_AFTER)
        print(CLOSE_AFTER)
        print(f"asset {len(current)} -> {len(patched)} chars")
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
    ok, detail = verify_live()
    if not ok:
        print(f"VERIFY FAILED: {detail}", file=sys.stderr)
        put_asset(BACKUP.read_bytes().decode("utf-8"))
        print("reverted.", file=sys.stderr)
        return 1

    print(f"OK. Homepage h1 is now: {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

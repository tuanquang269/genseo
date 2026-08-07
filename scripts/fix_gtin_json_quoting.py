#!/usr/bin/env python3
"""Quote the GTIN in Product JSON-LD: `{{ variant.barcode }}` -> `{{ variant.barcode | json }}`.

A latent theme bug that only became visible once barcodes existed. Both
`sections/main-product.liquid` and `sections/featured-product.liquid` emit

    "gtin12": {{ variant.barcode }},

with no `| json`, so the value lands unquoted. Before 2026-08-02 every barcode was
blank and the branch never fired. Backfilling 2,449 GTINs the same day turned it on
for 747 products, with two failure modes:

  * barcode starts with "0" (45 products) -> `"gtin12": 033674156858` is **invalid
    JSON**; the whole Product block fails to parse, so Google sees no product schema
    at all. Strictly worse than having no GTIN.
  * every other barcode -> parses, but emits a JSON *number* where schema.org and
    Google's merchant-listing docs require Text.

A sample of 20 live product pages measured 1 unparseable / 19 numeric / 0 clean.

`| json` fixes both at once: it quotes the value and escapes it.

ponytail: regex over the three length branches rather than rewriting the schema
block. The branches are already correct — only the filter is missing.

Usage:
    python3 scripts/fix_gtin_json_quoting.py --dry-run
    python3 scripts/fix_gtin_json_quoting.py --apply
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
ASSETS = ("sections/main-product.liquid", "sections/featured-product.liquid")
BACKUP_DIR = Path("backups/20260802")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

# leading-zero barcode: the block is unparseable BEFORE the fix, must be a string after
LEADING_ZERO = ("https://wellnessnest.co/products/natures-way-alive-once-daily-mens-multi-vitamin-60-tablets",
                "033674156858")
# ordinary barcode: parses before the fix but as a number, must be a string after
ORDINARY = ("https://wellnessnest.co/products/allmax-nutrition-caffeine-200-mg-100-tablets",
            "665553126227")
# Both probes are SINGLE-variant on purpose. Tapita only takes over multi-variant
# products, so a multi-variant page would verify Tapita's schema, not the theme's.

PATTERN = re.compile(r'("gtin\d*"\s*:\s*\{\{\s*variant\.barcode\s*)\}\}')

with open(CONFIG) as fh:
    CFG = json.load(fh)
SHOP, TOKEN = CFG["shop"], CFG["access_token"]


def api(path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"https://{SHOP}/admin/api/{API_VERSION}/{path}",
                                 data=data, method=method,
                                 headers={"X-Shopify-Access-Token": TOKEN,
                                          "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=45).read())


def get_asset(key):
    q = urllib.parse.urlencode({"asset[key]": key})
    return api(f"themes/{THEME}/assets.json?{q}")["asset"]["value"]


def put_asset(key, value):
    return api(f"themes/{THEME}/assets.json", method="PUT",
               payload={"asset": {"key": key, "value": value}})


def gtin_of(url):
    """Parse every ld+json block; return ('ok', gtin_value) or ('unparseable', err)."""
    req = urllib.request.Request(f"{url}?nocache={int(time.time())}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        if resp.status != 200:
            return "http", f"HTTP {resp.status}"
        html = resp.read().decode("utf-8", errors="replace")
    found = None
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            parsed = json.loads(raw)
        except Exception as exc:
            return "unparseable", str(exc)
        for m in re.finditer(r'"gtin\d*":\s*("?)([^",}]+)\1', json.dumps(parsed)):
            found = m.group(2)
    return "ok", found


def verify_live():
    for url, expected in (LEADING_ZERO, ORDINARY):
        try:
            state, value = gtin_of(url)
        except Exception as exc:
            return False, f"{url}: {type(exc).__name__}: {exc}"
        if state != "ok":
            return False, f"{url}: {state}: {value}"
        if value != expected:
            return False, f"{url}: gtin is {value!r}, expected the string {expected!r}"
        time.sleep(1.3)  # origin rate-limits browser UAs above ~2 req/s
    return True, "both leading-zero and ordinary GTINs emit as quoted strings"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not (a.apply or a.dry_run):
        ap.error("pass --dry-run or --apply")

    originals, patched, total = {}, {}, 0
    for key in ASSETS:
        cur = get_asset(key)
        n = len(PATTERN.findall(cur))
        if n == 0 and "variant.barcode | json" in cur:
            print(f"{key}: already patched")
            continue
        if n == 0:
            print(f"FAIL: {key} has no unquoted gtin emission to fix", file=sys.stderr)
            return 1
        originals[key] = cur
        patched[key] = PATTERN.sub(r"\1| json }}", cur)
        total += n
        print(f"{key}: {n} emission(s) to quote")

    if not patched:
        print("Nothing to do.")
        return 0
    if a.dry_run:
        for key, val in patched.items():
            for m in re.finditer(r'"gtin\d*":[^\n]*', val):
                print("   ", m.group(0).strip())
        print(f"\n{total} emission(s) would be quoted")
        return 0

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for key, cur in originals.items():
        bp = BACKUP_DIR / (key.replace("/", "__") + ".pre-gtinquote")
        if not bp.is_file():
            bp.write_bytes(cur.encode("utf-8"))
            print(f"backup: {bp}")
        if bp.read_bytes().decode("utf-8") != cur:
            print(f"FAIL: backup for {key} does not match live. Re-take it.", file=sys.stderr)
            return 1

    print("Applying to LIVE theme...")
    for key, val in patched.items():
        put_asset(key, val)
    time.sleep(3)
    ok, detail = verify_live()
    if not ok:
        print(f"VERIFY FAILED: {detail}", file=sys.stderr)
        for key, cur in originals.items():
            put_asset(key, cur)
        print("reverted both files.", file=sys.stderr)
        return 1

    print(f"OK. {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

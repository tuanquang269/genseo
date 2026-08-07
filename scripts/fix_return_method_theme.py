#!/usr/bin/env python3
"""Correct returnMethod in the theme's Product JSON-LD: ReturnByMail -> ReturnInStore.

The 2026-07-30 edit transcribed `ReturnByMail` from /policies/refund-policy
("we'll send you instructions on how and where to send your package"). The
product-page popup says the opposite ("All returns must be delivered to our
warehouse", with opening hours), and the Tapita app — which is the schema Google
actually renders — has always declared `Return in store`.

Owner resolved it on 2026-08-02: **Return in store is the real process.** So the
theme was the wrong one, and this aligns it with both reality and Tapita.

Not changed: `returnFees` stays ReturnFeesCustomerResponsibility, matching
Tapita's "Customer responsibility".

ponytail: "Free shipping above $99" is deliberately NOT in this JSON-LD.
Google's merchant-listing docs type `shippingDetails.shippingRate` as a plain
MonetaryAmount with no documented threshold field, and a bare 0-rate entry would
tell Google shipping is unconditionally free — the exact false signal we are
fixing in Tapita. It belongs in the meta description, not the markup.

Usage:
    python3 scripts/fix_return_method_theme.py --dry-run
    python3 scripts/fix_return_method_theme.py --apply
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
ASSET = "sections/main-product.liquid"
BACKUP = Path("backups/20260802/sections__main-product.liquid.pre-returnmethod")
VERIFY_URL = "https://wellnessnest.co/products/dymatize-nutrition-iso-100-hydrolyzed-1-3-5-lb"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

BEFORE = '"returnMethod": "https://schema.org/ReturnByMail",'
AFTER = '"returnMethod": "https://schema.org/ReturnInStore",'

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


def verify_live():
    try:
        request = urllib.request.Request(
            f"{VERIFY_URL}?nocache={int(time.time())}", headers={"User-Agent": UA}
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            html = response.read().decode("utf-8", errors="replace")
        product = None
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and parsed.get("@type") == "Product":
                product = parsed
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    if not product:
        return False, "Product JSON-LD block not found"
    method = product.get("hasMerchantReturnPolicy", {}).get("returnMethod")
    if method != "https://schema.org/ReturnInStore":
        return False, f"returnMethod is {method!r}"
    return True, product["hasMerchantReturnPolicy"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.apply or args.dry_run):
        parser.error("pass --dry-run or --apply")

    current = get_asset()
    if AFTER in current and BEFORE not in current:
        print("Already patched. Nothing to do.")
        return 0
    if current.count(BEFORE) != 1:
        print(f"FAIL: anchor found {current.count(BEFORE)}×, expected 1", file=sys.stderr)
        return 1

    patched = current.replace(BEFORE, AFTER)

    if args.dry_run:
        print(f"--- {BEFORE}\n+++ {AFTER}")
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

    print("OK. Live return policy now:")
    print(json.dumps(detail, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Fill Shopify variant barcodes (GTIN) from the MAIN TOBUY sheet, by SKU.

Only 4 of 3,739 online-store variants carried a barcode, which is why our offers
cannot be matched to Google's product catalogue and never appear in the free
"Popular products" blocks. Column A of `4. SUP_MAIN_DATA` holds the barcode and
column B the SKU, so the data already existed — nobody had to scan anything.

**Column A is not purely GTINs.** For own-brand items it holds internal codes
(`ULSUP-088`, `SUP-00008`, `847280`). Writing those into the barcode field would
push junk into the Merchant Center feed and earn disapprovals — strictly worse
than leaving it blank. So every value must pass BOTH:
  1. shape: exactly 8, 12, 13 or 14 digits
  2. the GS1 mod-10 check digit
Anything else is reported, never written. Those items are the ones that should be
declared `identifierExists: false` in Merchant Center instead.

Usage:
    python3 scripts/fill_gtins.py --selftest
    python3 scripts/fill_gtins.py --dry-run
    python3 scripts/fill_gtins.py --apply
"""
import argparse
import collections
import csv
import datetime
import json
import os
import pathlib
import re
import sys
import time
import urllib.request

CONFIG = os.path.expanduser("~/.genseo/shopify_token.json")
SHEET = pathlib.Path.home() / "Downloads" / "MAIN TOBUY - 4. SUP_MAIN_DATA.csv"
BASE = pathlib.Path(__file__).resolve().parent.parent
API = "2026-04"

with open(CONFIG) as fh:
    CFG = json.load(fh)
SHOP, TOKEN = CFG["shop"], CFG["access_token"]
HDR = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}


def norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def valid_gtin(code):
    """GS1 mod-10: pad to 14, weight the first 13 alternately 3,1 from the left."""
    code = (code or "").strip()
    if not re.fullmatch(r"\d{8}|\d{12}|\d{13}|\d{14}", code):
        return False
    p = code.zfill(14)
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(p[:13]))
    return (10 - total % 10) % 10 == int(p[13])


def gql(query, variables):
    req = urllib.request.Request(
        f"https://{SHOP}/admin/api/{API}/graphql.json",
        data=json.dumps({"query": query, "variables": variables}).encode(), headers=HDR)
    out = json.loads(urllib.request.urlopen(req, timeout=90).read())
    if "errors" in out:
        raise RuntimeError(out["errors"])
    return out["data"]


FETCH = """query($cursor:String){products(first:200,after:$cursor,query:"status:active"){
 pageInfo{hasNextPage endCursor}
 nodes{id title onlineStoreUrl variants(first:50){nodes{id sku barcode}}}}}"""

UPDATE = """mutation($productId:ID!,$variants:[ProductVariantsBulkInput!]!){
 productVariantsBulkUpdate(productId:$productId, variants:$variants){
   productVariants{id barcode}
   userErrors{field message}}}"""


def load_sheet():
    rows = list(csv.reader(SHEET.open(encoding="utf-8-sig", errors="replace")))[1:]
    out = {}
    for r in rows:
        if len(r) < 2:
            continue
        sku, code = norm(r[1]), (r[0] or "").strip()
        if sku and code:
            out[sku] = code
    return out


def load_variants():
    cur, prods = None, []
    while True:
        d = gql(FETCH, {"cursor": cur})["products"]
        for p in d["nodes"]:
            if not p["onlineStoreUrl"]:
                continue
            prods.append(p)
        if not d["pageInfo"]["hasNextPage"]:
            break
        cur = d["pageInfo"]["endCursor"]
        time.sleep(0.35)
    return prods


def selftest():
    assert valid_gtin("740985229286")       # UPC-A off the sheet
    assert valid_gtin("0740985229286")
    assert not valid_gtin("740985229287")   # broken check digit
    assert not valid_gtin("ULSUP-088")      # internal code
    assert not valid_gtin("SUP-00008")
    assert not valid_gtin("847280")         # 6 digits: not a GTIN length
    assert not valid_gtin("")
    assert not valid_gtin(None)
    assert valid_gtin("4901777289536")      # EAN-13
    assert not valid_gtin("4901777289535")
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not (a.apply or a.dry_run):
        ap.error("pass --dry-run, --apply or --selftest")
    if not SHEET.is_file():
        print(f"FAIL: sheet not found at {SHEET}", file=sys.stderr)
        return 1

    sheet = load_sheet()
    prods = load_variants()

    plan = collections.defaultdict(list)   # product gid -> [{id, barcode}]
    stats = collections.Counter()
    rejected, missing = [], []
    for p in prods:
        for v in p["variants"]["nodes"]:
            if (v.get("barcode") or "").strip():
                stats["already had one"] += 1
                continue
            sku = norm(v.get("sku"))
            if not sku:
                stats["variant has no SKU"] += 1
                continue
            code = sheet.get(sku)
            if not code:
                stats["SKU not in sheet"] += 1
                missing.append((v["sku"], p["title"]))
                continue
            if not valid_gtin(code):
                stats["value is not a valid GTIN"] += 1
                rejected.append((code, v["sku"], p["title"]))
                continue
            stats["WILL WRITE"] += 1
            plan[p["id"]].append({"id": v["id"], "barcode": code})

    total = sum(stats.values())
    print(f"online-store variants: {total}")
    for k, n in stats.most_common():
        print(f"  {k:28} {n:5d}")
    print(f"\nproducts touched: {len(plan)}")
    print(f"\nrejected values (internal codes / bad check digit), first 10 of {len(rejected)}:")
    for c, s, t in rejected[:10]:
        print(f"   {c[:16]:18} sku={s[:18]:20} {t[:40]}")

    out = BASE / "backups" / datetime.date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    (out / "gtin_rejected.json").write_text(json.dumps(
        {"not_a_valid_gtin": rejected, "sku_not_in_sheet": missing}, indent=1))
    print(f"\nfull reject list: {out / 'gtin_rejected.json'}")

    if a.dry_run:
        return 0

    written, errors = 0, []
    for i, (pid, variants) in enumerate(plan.items(), 1):
        try:
            r = gql(UPDATE, {"productId": pid, "variants": variants})["productVariantsBulkUpdate"]
            if r["userErrors"]:
                errors.append((pid, r["userErrors"]))
            else:
                written += len(r["productVariants"])
        except Exception as exc:
            errors.append((pid, f"{type(exc).__name__}: {exc}"))
        if i % 100 == 0:
            print(f"   {i}/{len(plan)} products, {written} variants written")
        time.sleep(0.3)

    (out / "gtin_written.json").write_text(json.dumps(
        {"written": written, "errors": errors}, indent=1))
    print(f"\napplied: {written} variants written, {len(errors)} product error(s)")
    for pid, e in errors[:5]:
        print("   ", pid, str(e)[:120])
    return 0


if __name__ == "__main__":
    sys.exit(main())

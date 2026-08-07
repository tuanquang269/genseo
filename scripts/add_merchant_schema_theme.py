#!/usr/bin/env python3
"""Add hasMerchantReturnPolicy + shippingDetails to the product JSON-LD.

Google's merchant rules want both on Product (or its Offer). Neither was present,
so every product page was missing return and shipping eligibility signals for
free merchant listings and Shopping surfaces.

Values are transcribed from the store's OWN published policies, not invented:

  Shipping  https://wellnessnest.co/policies/shipping-policy
            "J&T - {{CURRENCY}} 3.99 (2-3 working days)"
            "Free Shipping on orders over {{CURRENCY}} 99 with JNT"
            Operating hours Mon-Fri 9:00-17:30, Sat 9:00-13:00 -> handling 0-1 day

  Refund    https://wellnessnest.co/policies/refund-policy
            "We have a 7-day return policy"
            Customer ships the item back after requesting a return.

Two readings of the refund policy were ambiguous and Owner decided them
(2026-07-30): the customer bears return shipping, and supplements ARE returnable
within the 7-day window when the seal is intact (they are not treated as the
"perishable goods (such as food)" exception).

hasMemberProgram is deliberately NOT added: the store has no loyalty program, and
declaring one that does not exist would be a false merchant signal.

ponytail: policy values are inlined in the theme rather than driven from
metafields. If a policy changes, this JSON-LD must be updated with it. The source
policy URLs are in the Liquid comment so the next editor knows where truth lives.

Usage:
    python3 scripts/add_merchant_schema_theme.py --dry-run
    python3 scripts/add_merchant_schema_theme.py --apply
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SHOP = __import__("genseo_config").SHOP
TOKEN = __import__("genseo_config").TOKEN
THEME = "183190880571"
ASSET = "sections/main-product.liquid"
BACKUP = Path("backups/2026-07-30-theme/sections__main-product.liquid")
VERIFY_URL = "https://wellnessnest.co/products/nutrabio-intra-blast"

ANCHOR = (
    '      "brand": {\n'
    '        "@type": "Brand",\n'
    '        "name": {{ product.vendor | json }}\n'
    "      },\n"
)

ADDITION = """      {%- comment -%}
        Merchant eligibility signals. Values transcribed from the store policies:
          /policies/shipping-policy  (J&T {{CURRENCY}} 3.99, 2-3 working days, free over {{CURRENCY}} 99)
          /policies/refund-policy    (7-day window, customer ships item back)
        Update these together with the policy pages, not independently.
      {%- endcomment -%}
      "hasMerchantReturnPolicy": {
        "@type": "MerchantReturnPolicy",
        "applicableCountry": "SG",
        "returnPolicyCountry": "SG",
        "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
        "merchantReturnDays": 7,
        "returnMethod": "https://schema.org/ReturnByMail",
        "returnFees": "https://schema.org/ReturnFeesCustomerResponsibility",
        "merchantReturnLink": {{ request.origin | append: "/policies/refund-policy" | json }}
      },
      "shippingDetails": [
        {
          "@type": "OfferShippingDetails",
          "shippingRate": {
            "@type": "MonetaryAmount",
            "value": 3.99,
            "currency": "{{CURRENCY}}"
          },
          "shippingDestination": {
            "@type": "DefinedRegion",
            "addressCountry": "SG"
          },
          "deliveryTime": {
            "@type": "ShippingDeliveryTime",
            "handlingTime": {
              "@type": "QuantitativeValue",
              "minValue": 0,
              "maxValue": 1,
              "unitCode": "DAY"
            },
            "transitTime": {
              "@type": "QuantitativeValue",
              "minValue": 2,
              "maxValue": 3,
              "unitCode": "DAY"
            }
          }
        }
      ],
"""


def api(path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"https://{SHOP}/admin/api/2026-04/{path}",
        data=data,
        method=method,
        headers={"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req).read())


def get_asset():
    q = urllib.parse.urlencode({"asset[key]": ASSET})
    return api(f"themes/{THEME}/assets.json?{q}")["asset"]["value"]


def put_asset(value):
    return api(
        f"themes/{THEME}/assets.json",
        method="PUT",
        payload={"asset": {"key": ASSET, "value": value}},
    )


def fetch_product_jsonld():
    req = urllib.request.Request(VERIFY_URL, headers={"User-Agent": "genseo-schema-verify"})
    with urllib.request.urlopen(req, timeout=45) as res:
        if res.status != 200:
            raise RuntimeError(f"HTTP {res.status}")
        html = res.read().decode("utf-8", errors="replace")
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        parsed = json.loads(raw)  # raises if the Liquid edit produced invalid JSON
        if isinstance(parsed, dict) and parsed.get("@type") == "Product":
            return parsed
    raise RuntimeError("Product JSON-LD block not found on page")


def verify_live():
    try:
        product = fetch_product_jsonld()
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    for key in ("hasMerchantReturnPolicy", "shippingDetails"):
        if key not in product:
            return False, f"{key} missing from rendered Product schema"
    return True, product


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not (args.apply or args.dry_run):
        ap.error("pass --dry-run or --apply")

    current = get_asset()
    if "hasMerchantReturnPolicy" in current:
        print("Already patched. Nothing to do.")
        return 0
    if current.count(ANCHOR) != 1:
        print(
            f"FAIL: anchor found {current.count(ANCHOR)} times, expected 1", file=sys.stderr
        )
        return 1

    patched = current.replace(ANCHOR, ANCHOR + ADDITION)

    if args.dry_run:
        print("--- inserting after the brand block ---")
        print(ADDITION)
        print(f"asset {len(current)} -> {len(patched)} chars")
        return 0

    if not BACKUP.is_file():
        print(f"FAIL: backup missing at {BACKUP}", file=sys.stderr)
        return 1
    backup_value = BACKUP.read_text(encoding="utf-8")
    if backup_value != current:
        print("FAIL: backup does not match live asset. Re-take the backup.", file=sys.stderr)
        return 1

    print("Applying patch to LIVE theme...")
    put_asset(patched)
    print("Verifying live page...")
    ok, detail = verify_live()
    if not ok:
        print(f"VERIFY FAILED: {detail}", file=sys.stderr)
        print("Reverting from backup...", file=sys.stderr)
        put_asset(backup_value)
        ok2, detail2 = verify_live()
        print(f"revert verify: {'restored' if ok2 else detail2}", file=sys.stderr)
        return 1

    print("OK. Rendered Product schema now carries:")
    print(json.dumps(
        {k: detail[k] for k in ("hasMerchantReturnPolicy", "shippingDetails")}, indent=2
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())

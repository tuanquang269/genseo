#!/usr/bin/env python3
"""Declare the real loyalty program on the Organization JSON-LD (`hasMemberProgram`).

The 2026-07-30 note said not to add this because "there is no loyalty program".
That was wrong: **Joy: Loyalty Program (Avada) is installed and live**, and
/pages/loyalty-page renders a customer-facing program called "Your Brand
Rewards" with five tiers. Owner confirmed on 2026-08-02 to declare it.

Every value below is transcribed from the live program, not invented — tier
names and lifetime-point thresholds come from the Joy config embedded in the
storefront, the perks from the rendered loyalty page:

    Bronze    0 pts       starter level, no tier reward yet
    Silver    1,500 pts   $10 OFF
    Gold      3,000 pts   $30 OFF + anniversary gifts
    Platinum  9,000 pts   $50 OFF + anniversary gifts + exclusive training plan
    Diamond   30,000 pts  $100 OFF + the above + special discounts & free shipping

Members earn 3 points per {{CURRENCY}} 1 spent, so `TierBenefitLoyaltyPoints` is true of
every tier. `TierBenefitLoyaltyShipping` is added to Diamond only, which is the
one tier whose published perks include free shipping.

`TierBenefitLoyaltyPrice` is deliberately NOT declared on any tier: that means
member-specific prices on product pages, and our Offers carry a single price for
everyone. The tier rewards are discount coupons, which is a different thing.
Declaring it would be the same class of false merchant signal we just removed
from the shipping config.

ponytail: tier thresholds are inlined. If the program is re-tiered in Joy, this
JSON-LD must be updated with it — the loyalty page is the source of truth.

Usage:
    python3 scripts/add_member_program_theme.py --dry-run
    python3 scripts/add_member_program_theme.py --apply
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
ASSET = "sections/header.liquid"
BACKUP = Path("backups/20260802/sections__header.liquid")
VERIFY_URLS = (
    "https://wellnessnest.co/",
    "https://wellnessnest.co/products/dymatize-nutrition-iso-100-hydrolyzed-1-3-5-lb",
)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

ANCHOR = '    "@type": "Organization",\n    "name": {{ shop.name | json }},\n'

TIERS = [
    ("Bronze", 0, ["https://schema.org/TierBenefitLoyaltyPoints"]),
    ("Silver", 1500, ["https://schema.org/TierBenefitLoyaltyPoints"]),
    ("Gold", 3000, ["https://schema.org/TierBenefitLoyaltyPoints"]),
    ("Platinum", 9000, ["https://schema.org/TierBenefitLoyaltyPoints"]),
    (
        "Diamond",
        30000,
        [
            "https://schema.org/TierBenefitLoyaltyPoints",
            "https://schema.org/TierBenefitLoyaltyShipping",
        ],
    ),
]


def tier_block(name, points, benefits):
    benefit = json.dumps(benefits[0]) if len(benefits) == 1 else json.dumps(benefits)
    requirement = f"{points:,} lifetime points earned"
    return (
        "        {\n"
        '          "@type": "MemberProgramTier",\n'
        f'          "@id": "{{{{ request.origin }}}}/pages/loyalty-page#tier-{name.lower()}",\n'
        f'          "name": "{name}",\n'
        f'          "hasTierRequirement": "{requirement}",\n'
        f'          "hasTierBenefit": {benefit}\n'
        "        }"
    )


ADDITION = (
    '    {%- comment -%}\n'
    "      Joy: Loyalty Program (Avada), live at /pages/loyalty-page. Tier names and\n"
    "      lifetime-point thresholds are transcribed from that page — update them together.\n"
    '    {%- endcomment -%}\n'
    '    "hasMemberProgram": {\n'
    '      "@type": "MemberProgram",\n'
    '      "name": "Your Brand Rewards",\n'
    '      "url": {{ request.origin | append: "/pages/loyalty-page" | json }},\n'
    '      "hasTiers": [\n'
    + ",\n".join(tier_block(*t) for t in TIERS)
    + "\n      ]\n"
    "    },\n"
)

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
    """header.liquid renders on every page — a syntax error here breaks the whole site."""
    for url in VERIFY_URLS:
        try:
            request = urllib.request.Request(
                f"{url}?nocache={int(time.time())}", headers={"User-Agent": UA}
            )
            with urllib.request.urlopen(request, timeout=45) as response:
                if response.status != 200:
                    return False, f"{url}: HTTP {response.status}"
                html = response.read().decode("utf-8", errors="replace")
            org = None
            for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
                parsed = json.loads(raw)  # every block must still parse
                if isinstance(parsed, dict) and parsed.get("@type") == "Organization":
                    org = parsed
        except Exception as exc:
            return False, f"{url}: {type(exc).__name__}: {exc}"
        if not org:
            return False, f"{url}: Organization block missing"
        program = org.get("hasMemberProgram")
        if not program:
            return False, f"{url}: hasMemberProgram missing"
        if len(program.get("hasTiers", [])) != len(TIERS):
            return False, f"{url}: expected {len(TIERS)} tiers, got {len(program.get('hasTiers', []))}"
        time.sleep(1.2)
    return True, program


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.apply or args.dry_run):
        parser.error("pass --dry-run or --apply")

    current = get_asset()
    if "hasMemberProgram" in current:
        print("Already patched. Nothing to do.")
        return 0
    if current.count(ANCHOR) != 1:
        print(f"FAIL: anchor found {current.count(ANCHOR)}×, expected 1", file=sys.stderr)
        return 1

    patched = current.replace(ANCHOR, ANCHOR + ADDITION)

    if args.dry_run:
        print(ADDITION)
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

    print("OK. Live Organization now carries:")
    print(json.dumps(detail, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

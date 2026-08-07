#!/usr/bin/env python3
"""Fix the Organization JSON-LD in sections/header.liquid.

Two defects on every page of the store:
  1. `sameAs` hardcodes 9 social settings, so the 6 unconfigured ones render as
     empty strings ("") inside the JSON-LD array. Invalid values in a live
     entity block.
  2. `"url"` is `request.origin | append: page.url`. On /pages/* templates that
     emits the CURRENT page URL as the Organization's url instead of the
     homepage (we have author pages like /pages/marcus-thorne).

Applies the patch to the LIVE theme, then verifies a real page still returns 200
with parseable JSON-LD. Auto-reverts from the backup if verification fails, so a
Liquid syntax error cannot leave the header broken.

Usage:
    python3 scripts/fix_org_schema_theme.py --dry-run
    python3 scripts/fix_org_schema_theme.py --apply
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
ASSET = "sections/header.liquid"
BACKUP = Path("backups/2026-07-30-theme/sections__header.liquid")
VERIFY_URL = "https://wellnessnest.co/products/nutrabio-intra-blast"

OLD = (
    '    "sameAs": [\n'
    "      {{ settings.social_twitter_link | json }},\n"
    "      {{ settings.social_facebook_link | json }},\n"
    "      {{ settings.social_pinterest_link | json }},\n"
    "      {{ settings.social_instagram_link | json }},\n"
    "      {{ settings.social_tiktok_link | json }},\n"
    "      {{ settings.social_tumblr_link | json }},\n"
    "      {{ settings.social_snapchat_link | json }},\n"
    "      {{ settings.social_youtube_link | json }},\n"
    "      {{ settings.social_vimeo_link | json }}\n"
    "    ],\n"
    '    "url": {{ request.origin | append: page.url | json }}\n'
)

NEW = """    {%- comment -%}
      sameAs must contain only configured profiles. Blank social settings
      previously emitted "" entries into the live JSON-LD.
    {%- endcomment -%}
    {%- liquid
      assign social_raw = settings.social_twitter_link | append: '|' | append: settings.social_facebook_link | append: '|' | append: settings.social_pinterest_link | append: '|' | append: settings.social_instagram_link | append: '|' | append: settings.social_tiktok_link | append: '|' | append: settings.social_tumblr_link | append: '|' | append: settings.social_snapchat_link | append: '|' | append: settings.social_youtube_link | append: '|' | append: settings.social_vimeo_link
      assign social_parts = social_raw | split: '|'
      assign social_clean = ''
      for social_url in social_parts
        assign social_trimmed = social_url | strip
        if social_trimmed != blank
          if social_clean == blank
            assign social_clean = social_trimmed
          else
            assign social_clean = social_clean | append: '|' | append: social_trimmed
          endif
        endif
      endfor
    -%}
    {%- if social_clean != blank -%}
      {%- assign social_same_as = social_clean | split: '|' -%}
      "sameAs": {{ social_same_as | json }},
    {%- endif %}
    "url": {{ request.origin | json }}
"""


def api(path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"https://{SHOP}/admin/api/2026-04/{path}",
        data=data,
        method=method,
        headers={
            "X-Shopify-Access-Token": TOKEN,
            "Content-Type": "application/json",
        },
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


def verify_live():
    """Page still renders and every JSON-LD block parses with a clean sameAs."""
    req = urllib.request.Request(VERIFY_URL, headers={"User-Agent": "genseo-schema-verify"})
    with urllib.request.urlopen(req, timeout=45) as res:
        if res.status != 200:
            return False, f"HTTP {res.status}"
        html = res.read().decode("utf-8", errors="replace")

    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.S
    )
    if not blocks:
        return False, "no JSON-LD blocks found on page"

    org = None
    for raw in blocks:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            return False, f"JSON-LD no longer parses: {exc}"
        if isinstance(parsed, dict) and parsed.get("@type") == "Organization":
            org = parsed
    if org is None:
        return False, "Organization block disappeared"
    same_as = org.get("sameAs", [])
    if any(not str(u).strip() for u in same_as):
        return False, f"sameAs still has blank entries: {same_as}"
    if org.get("url", "").rstrip("/") != "https://wellnessnest.co":
        return False, f"Organization url wrong: {org.get('url')!r}"
    return True, org


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not (args.apply or args.dry_run):
        ap.error("pass --dry-run or --apply")

    current = get_asset()
    if OLD not in current:
        if "social_clean" in current:
            print("Already patched (social_clean present). Nothing to do.")
            return 0
        print("FAIL: expected block not found in live asset. Theme changed?", file=sys.stderr)
        return 1
    if current.count(OLD) != 1:
        print(f"FAIL: block appears {current.count(OLD)} times, expected 1", file=sys.stderr)
        return 1

    patched = current.replace(OLD, NEW)

    if args.dry_run:
        print("--- would replace ---")
        print(OLD)
        print("--- with ---")
        print(NEW)
        print(f"asset {len(current)} -> {len(patched)} chars")
        return 0

    if not BACKUP.is_file():
        print(f"FAIL: backup missing at {BACKUP}", file=sys.stderr)
        return 1
    backup_value = BACKUP.read_text(encoding="utf-8")
    if backup_value != current:
        print("FAIL: backup does not match live asset. Re-take the backup first.", file=sys.stderr)
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
        print(f"revert verify: {ok2} {detail2 if not ok2 else 'restored'}", file=sys.stderr)
        return 1

    print("OK. Organization JSON-LD now:")
    print(json.dumps(detail, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

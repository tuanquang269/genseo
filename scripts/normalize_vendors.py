#!/usr/bin/env python3
"""Collapse near-duplicate vendor strings so one brand is one string.

9 brands are spelled two or three ways across 420 online products — 'Your Brand'
vs 'Your Brand', 'Now Foods' vs 'now foods', 'BlenderBottle' vs 'Blender Bottle'.
Two concrete harms, both measured:

  * Shopify's Google channel maps `vendor` -> the Merchant Center `brand` attribute.
    Google joins an offer to its catalogue entity on brand + GTIN together, so a split
    brand string undercuts the GTIN backfill done 2026-08-02.
  * Automated collections match vendor by exact string. The `now-foods` collection
    rule is `EQUALS 'Now Foods'`, so the one product tagged 'now foods' is silently
    excluded. The `muscletech` collection carries two rules purely to paper over the
    same problem.

Some splits do not normalise to the same key at all — `'Dymatize'` vs `'Dymatize Nutrition'` — so they
need naming a human decision, not a rule. Pass those with `--alias "Dymatize=Dymatize Nutrition"`.
They go through exactly the same collection-rule safety check as the automatic ones.

Winner = the variant with the most products, which also minimises writes (34, not 420).
Case is not the point; consistency is. The one rule that must hold is that no
automated collection loses a product, so every VENDOR ruleset is checked against the
chosen winner BEFORE anything is written.

Usage:
    python3 scripts/normalize_vendors.py --dry-run
    python3 scripts/normalize_vendors.py --apply
"""
import argparse
import collections
import datetime
import json
import os
import pathlib
import re
import sys
import time
import urllib.request

CONFIG = os.path.expanduser("~/.genseo/shopify_token.json")
API = "2026-04"
BASE = pathlib.Path(__file__).resolve().parent.parent

with open(CONFIG) as fh:
    CFG = json.load(fh)
SHOP, TOKEN = CFG["shop"], CFG["access_token"]
HDR = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}

FETCH = """query($c:String){products(first:200,after:$c,query:"status:active"){
 pageInfo{hasNextPage endCursor}
 nodes{id handle vendor onlineStoreUrl}}}"""

RULES = """query($c:String){collections(first:200,after:$c){pageInfo{hasNextPage endCursor}
 nodes{handle ruleSet{rules{column relation condition}}}}}"""

UPDATE = """mutation($input:ProductInput!){productUpdate(input:$input){
 product{id vendor} userErrors{field message}}}"""


def gql(query, variables):
    req = urllib.request.Request(f"https://{SHOP}/admin/api/{API}/graphql.json",
                                 data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers=HDR)
    out = json.loads(urllib.request.urlopen(req, timeout=90).read())
    if "errors" in out:
        raise RuntimeError(out["errors"])
    return out["data"]


def page(query, root):
    cur = None
    while True:
        d = gql(query, {"c": cur})[root]
        yield from d["nodes"]
        if not d["pageInfo"]["hasNextPage"]:
            break
        cur = d["pageInfo"]["endCursor"]
        time.sleep(0.3)


def brand_key(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def selftest():
    assert brand_key("Blender Bottle") == brand_key("BlenderBottle")
    assert brand_key("Now Foods") == brand_key("now foods")
    assert brand_key("Your Brand") == brand_key("Your Brand")
    assert brand_key("Now Foods") != brand_key("Now Sports")   # genuinely different brands
    assert brand_key("Dymatize") != brand_key("Dymatize Nutrition")
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--alias", action="append", default=[], metavar="LOSER=WINNER",
                    help="merge two vendor strings that do NOT normalise to the same brand "
                         "(repeatable). Both sides must exist on a live product or the run aborts.")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not (a.apply or a.dry_run):
        ap.error("pass --dry-run, --apply or --selftest")

    prods = [p for p in page(FETCH, "products") if p["onlineStoreUrl"]]
    counts = collections.Counter(p["vendor"] for p in prods)

    groups = collections.defaultdict(list)
    for name, n in counts.items():
        groups[brand_key(name)].append((name, n))

    winners = {}   # loser string -> winner string
    for variants in groups.values():
        if len(variants) < 2:
            continue
        # most products wins, but never an all-lowercase string over a properly-cased one:
        # `vendor` becomes the Merchant Center `brand`, and "owala" is not a brand name even
        # though it outnumbers "Owala" 5:3. All-caps is left alone — that is a styling choice
        # some brands really make, lowercase-only is just a typo.
        variants.sort(key=lambda v: (v[0].islower(), -v[1]))
        win = variants[0][0]
        for loser, _ in variants[1:]:
            winners[loser] = win

    for spec in a.alias:
        if "=" not in spec:
            print(f"FAIL: --alias needs LOSER=WINNER, got {spec!r}", file=sys.stderr)
            return 1
        loser, win = (s.strip() for s in spec.split("=", 1))
        # Typos here would silently rename nothing, or invent a brand string no product uses.
        for side in (loser, win):
            if side not in counts:
                print(f"FAIL: no live product has vendor {side!r}. "
                      f"Closest: {[n for n in counts if brand_key(side)[:5] in brand_key(n)][:5]}",
                      file=sys.stderr)
                return 1
        winners[loser] = win

    if not winners:
        print("No duplicate vendor strings. Nothing to do.")
        return 0

    # A rename must never drop a product out of an automated collection.
    vendor_rules = collections.defaultdict(list)
    for c in page(RULES, "collections"):
        rs = c["ruleSet"]
        if not rs:
            continue
        for r in rs["rules"]:
            if r["column"] == "VENDOR":
                vendor_rules[r["condition"]].append((c["handle"], r["relation"]))

    print("planned renames:")
    unsafe = []
    for loser, win in sorted(winners.items(), key=lambda kv: -counts[kv[0]]):
        guarded = vendor_rules.get(win, [])
        note = ""
        if loser in vendor_rules and not guarded:
            # the loser string is the one a rule keys on, and the winner is not -> renaming
            # would empty that collection
            unsafe.append((loser, win, vendor_rules[loser]))
            note = "  <-- UNSAFE: a collection rule keys on the loser"
        elif loser in vendor_rules:
            note = f"  (rule on both; {[h for h, _ in guarded]} still matches)"
        elif guarded:
            note = f"  (rule on winner: {[h for h, _ in guarded]} gains these)"
        print(f"   {counts[loser]:4d}x  {loser!r:24} -> {win!r}{note}")

    if unsafe:
        print("\nFAIL: renaming would break these collection rules. Fix the rules first:",
              file=sys.stderr)
        for loser, win, where in unsafe:
            print(f"   {loser!r} -> {win!r} but rule lives on {where}", file=sys.stderr)
        return 1

    todo = [p for p in prods if p["vendor"] in winners]
    print(f"\n{len(todo)} products across {len(winners)} renames")
    if a.dry_run:
        return 0

    out = BASE / "backups" / datetime.date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    (out / "vendor_normalize_before.json").write_text(json.dumps(
        [{"id": p["id"], "handle": p["handle"], "vendor": p["vendor"]} for p in todo], indent=1))

    done, errs = 0, []
    for i, p in enumerate(todo, 1):
        want = winners[p["vendor"]]
        try:
            r = gql(UPDATE, {"input": {"id": p["id"], "vendor": want}})["productUpdate"]
            if r["userErrors"]:
                errs.append((p["handle"], r["userErrors"]))
            elif r["product"]["vendor"] != want:
                errs.append((p["handle"], f"wrote {want!r}, read back {r['product']['vendor']!r}"))
            else:
                done += 1
        except Exception as exc:
            errs.append((p["handle"], f"{type(exc).__name__}: {exc}"))
        if i % 10 == 0:
            print(f"   {i}/{len(todo)}")
        time.sleep(0.3)

    print(f"\nwrote {done}, {len(errs)} error(s)")
    for h, e in errs[:5]:
        print("   ", h, str(e)[:120])

    regroup = collections.defaultdict(list)
    for name in {p["vendor"] for p in page(FETCH, "products") if p["onlineStoreUrl"]}:
        regroup[brand_key(name)].append(name)
    remaining = {k: v for k, v in regroup.items() if len(v) > 1}
    print(f"verify: duplicate vendor groups remaining = {len(remaining)} {remaining or ''}")
    (out / "vendor_normalize_result.json").write_text(json.dumps(
        {"written": done, "errors": errs, "remaining_groups": remaining}, indent=1))
    return 0 if not remaining and not errs else 1


if __name__ == "__main__":
    sys.exit(main())

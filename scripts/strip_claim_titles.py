#!/usr/bin/env python3
"""Remove unsupportable health claims from product titles flagged by Merchant Center.

Context. Merchant Center disapproves 74 landing pages under "Healthcare and medicine:
misleading claims". Only 17 of those carry claim wording in the TITLE, and of those 17 the
wording splits three ways — which is why this is a hand-checked list of 10 and not a regex
sweep over 94 products:

  KEEP — registered product names. Doctor's Best genuinely sells "High Absorption Magnesium"
    and "High Absorption CoQ10"; stripping that renames the product.
  KEEP — product-type words customers search with: "Fat Burner", "Testosterone Booster".
    Hydroxycut IS a fat burner. Deleting the category word does not make a weight-loss product
    compliant with Google's healthcare policy, it just makes the product harder to find.
  REMOVE — efficacy claims a supplement cannot support: "Enhance Vitality & Virility",
    "helps Weight Management", "For Weight Loss", "Immune Support", "Enhanced Health
    Effectiveness", "Lose Weight Supplement", "Fat loss", plus keyword stuffing like
    "Men Health, Muscle Builder" and "Slim Body".

Only the third group is edited here. Worth doing on compliance grounds whether or not Google
lifts the disapproval — and the SEO exposure is measured, not assumed: these 17 pages earned
1 SG click and 223 impressions in 90 days combined.

Usage:
    python3 scripts/strip_claim_titles.py --dry-run
    python3 scripts/strip_claim_titles.py --apply
    python3 scripts/strip_claim_titles.py --revert
"""
import argparse
import datetime
import json
import os
import pathlib
import sys
import time
import urllib.request

AUTH = json.load(open(os.path.expanduser("~/.genseo/shopify_token.json")))
API = "2026-04"
BASE = pathlib.Path(__file__).resolve().parent.parent
LOG = BASE / "backups" / datetime.date.today().isoformat() / "claim_title_log.json"

# (product id, exact current title, new title). The current title is asserted before writing,
# so a stale entry aborts instead of overwriting something a human changed since.
EDITS = [
    (7693190824118,
     "Now Sports, Tribulus, 1000mg, Enhance Vitality & Virility, 90 - 180 Tablets",
     "Now Sports, Tribulus, 1000mg, 90 - 180 Tablets"),
    (6211049029814,
     "Now Foods, EGCg, Green Author Five Extract helps Weight Management, Fat Burner, 200 mg, 90-180 count",
     "Now Foods, EGCg, Green Author Five Extract, Fat Burner, 200 mg, 90-180 count"),
    (8392020852918,
     "Applied Nutrition, Glutamine Powder, Pure Micronized, Muscle Recovery & Immune Support, 250g",
     "Applied Nutrition, Glutamine Powder, Pure Micronized, Muscle Recovery, 250g"),
    (7699991986358,
     "Sports Research MCT Oil Softgels For Weight Loss,100% Non-GMO Coconuts, Keto Friendly, Digestive Supplement",
     "Sports Research MCT Oil Softgels, 100% Non-GMO Coconuts, Keto Friendly, Digestive Supplement"),
    (7570617532598,
     "Nutrex Research, Tribulus Black 1300, Testosterone Booster for Men, Men Health, Muscle Builder, 120 Capsules",
     "Nutrex Research, Tribulus Black 1300, Testosterone Booster for Men, 120 Capsules"),
    (7740860825782,
     "Nutrex Research, Tribulus 1400, Testosterone Booster For Men, Enhanced Health Effectiveness, 90 Capsules",
     "Nutrex Research, Tribulus 1400, Testosterone Booster For Men, 90 Capsules"),
    (7693183418550,
     "Appliednutrition, Green Author Five, Fat Burner, EGCG, Antioxidant, Lose Weight Supplement, 30-90 Liquid Softgels",
     "Appliednutrition, Green Author Five, Fat Burner, EGCG, Antioxidant, 30-90 Liquid Softgels"),
    (7689943515318,
     "Muscletech Hydroxycut Hardcore Next Gen  Weight Loss  Weight Management  Fat Burner  Slim Body  100 Caps",
     "Muscletech Hydroxycut Hardcore Next Gen, Fat Burner, 100 Caps"),
    (7690512859318,
     "Muscletech Hydroxycut Hardcore Next Gen | Weight Loss | Weight Management | Fat Burner | Slim Body | 100 Caps",
     "Muscletech Hydroxycut Hardcore Next Gen, Fat Burner, 100 Caps"),
    (7671562797238,
     "Combo SIGNATURE SHRED STACK, Mutant Whey 5lb + JNX omen + Hydroxycut Elite 110s, Fat loss, Fat Burner",
     "Combo SIGNATURE SHRED STACK, Mutant Whey 5lb + JNX omen + Hydroxycut Elite 110s, Fat Burner"),
]


def rest(path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"https://{AUTH['shop']}/admin/api/{API}/{path}", data=data, method=method,
        headers={"X-Shopify-Access-Token": AUTH["access_token"], "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def selftest():
    """Every edit must only DELETE words — never invent, reorder, or lose the size/count."""
    import re
    for pid, old, new in EDITS:
        assert old != new, pid
        assert len(new) < len(old), pid
        # the pack size must survive, since that is what the shopper matches on
        size = re.findall(r"\d+\s*(?:-\s*\d+\s*)?(?:g|mg|kg|lbs?|caps?(?:ules)?|tabs?(?:lets)?|"
                          r"softgels|count|Sers|Caps)\b", old, re.I)
        for token in size:
            assert token.lower().replace(" ", "") in new.lower().replace(" ", ""), (pid, token)
        # No new words: every token in the new title must already exist in the old one.
        # Tokenise on non-word characters rather than whitespace — several supplier titles glue
        # words to punctuation ("For Weight Loss,100% Non-GMO"), so splitting on spaces makes
        # "100%" look invented when it is not.
        def tokens(s):
            return set(re.findall(r"[a-z0-9%]+", s.lower()))
        assert tokens(new) <= tokens(old), (pid, sorted(tokens(new) - tokens(old)))
    assert len({p for p, _, _ in EDITS}) == len(EDITS), "duplicate product id"
    print(f"selftest OK — {len(EDITS)} edits, all deletions only, pack sizes preserved")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--limit", type=int, help="canary: only the first N")
    a = ap.parse_args()
    if not (a.apply or a.dry_run or a.revert):
        ap.error("pass --dry-run, --apply or --revert")
    selftest()

    if a.revert:
        if not LOG.is_file():
            sys.exit(f"no log at {LOG}")
        done = json.loads(LOG.read_text())["applied"]
        for e in done:
            rest(f"products/{e['id']}.json", "PUT", {"product": {"id": e["id"], "title": e["old"]}})
            print(f"  restored {e['id']}  {e['old'][:70]}")
            time.sleep(0.4)
        print(f"reverted {len(done)}")
        return 0

    edits = EDITS[:a.limit] if a.limit else EDITS
    plan, skipped = [], []
    for pid, old, new in edits:
        live = rest(f"products/{pid}.json?fields=id,title,handle")["product"]
        if live["title"].strip() != old.strip():
            skipped.append((pid, f"live title differs: {live['title'][:60]!r}"))
            continue
        plan.append((pid, old, new, live["handle"]))

    for pid, old, new, handle in plan:
        print(f"\n  {pid}")
        print(f"    - {old}")
        print(f"    + {new}")
    for pid, why in skipped:
        print(f"\n  SKIP {pid}: {why}")
    if a.dry_run:
        print(f"\ndry-run: {len(plan)} would change, {len(skipped)} skipped")
        return 0

    applied = []
    for pid, old, new, handle in plan:
        rest(f"products/{pid}.json", "PUT", {"product": {"id": pid, "title": new}})
        applied.append({"id": pid, "old": old, "new": new, "handle": handle})
        time.sleep(0.4)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    prior = json.loads(LOG.read_text())["applied"] if LOG.is_file() else []
    seen = {e["id"] for e in prior}
    LOG.write_text(json.dumps({"applied": prior + [e for e in applied if e["id"] not in seen],
                               "skipped": skipped}, indent=1, ensure_ascii=False))
    print(f"\nwrote {len(applied)}; log {LOG}")

    print("\nverifying via the Admin API...")
    bad = []
    for e in applied:
        got = rest(f"products/{e['id']}.json?fields=id,title")["product"]["title"]
        if got.strip() != e["new"].strip():
            bad.append((e["id"], got))
    print(f"confirmed {len(applied) - len(bad)}/{len(applied)}")
    for pid, got in bad:
        print(f"   FAIL {pid}: {got[:70]}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

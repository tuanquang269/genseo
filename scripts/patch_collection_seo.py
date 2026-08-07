#!/usr/bin/env python3
"""
patch_collection_seo.py — Safe SEO patcher for top SG commercial collections.

Fixes (via Shopify Product/Collection API — does NOT touch theme files):
  1. collection.title casing  -> normalizes ALL-CAPS brand titles to Title Case
                                 (improves the theme-rendered H1 + breadcrumbs).
  2. SEO title_tag            -> corrects stale/weak title tags (e.g. Optimum's "2025").
  3. SEO description_tag       -> corrects weak meta descriptions.

SAFETY: dry-run by default. Prints the before/after diff and changes NOTHING.
        Add --apply to actually PUT the changes. Add --only <handle> to limit.

NOTE: The H1 still renders with a theme-level "Collection: " prefix. Removing that
      prefix is a THEME TEMPLATE edit (main-collection.liquid), handled separately —
      this script intentionally does not edit theme files.
"""
import json, urllib.request, argparse

SHOP= __import__("genseo_config").SHOP
TOKEN= __import__("genseo_config").TOKEN
API="2026-04"

# handle -> desired state. None = leave unchanged.
# title       : collection.title (H1 + nav/breadcrumb) — keep SHORT & clean.
# title_tag   : <title> SEO tag (<=70 chars ideal).
# description : meta description (<=160 chars).
TARGETS = {
  "protein-powder": {
    "title": "Protein Powder",  # already fine
    "title_tag": "Best Whey Protein Powder {{MARKET}} (2026) — Isolate, Blend & Plant",
    "description": "Shop the best whey protein powder in {{MARKET}} — Mutant Whey, PVL Iso Gold, Basic Whey Blend & more. 100% authentic, fast local delivery. From {{CURRENCY}} $53.",
  },
  "optimum-nutrition-{{market}}": {
    "title": "Optimum Nutrition",  # was ALL CAPS
    "title_tag": "Optimum Nutrition {{MARKET}} (2026) — Gold Standard Whey & More",
    "description": "Buy authentic Optimum Nutrition in {{MARKET}} — Gold Standard 100% Whey, Isolate, Serious Mass & Creatine. Authorised retailer, fast local delivery.",
  },
  "creatine": {
    "title": "Creatine",
    "title_tag": "Best Creatine Monohydrate {{MARKET}} (2026)",
    "description": "Shop the best creatine monohydrate supplements in {{MARKET}} (2026). Powder, capsules & gummies from top brands. 100% authentic, fast delivery.",
  },
  "mass-gainer": {
    "title": "Mass Gainer",  # was 'Mass gainer'
    "title_tag": "Best Mass Gainer Supplements {{MARKET}} (2026)",
    "description": "Shop {{MARKET}}'s best mass gainers in 2026 — high-calorie protein powders for hardgainers & bulking. 100% authentic, fast local delivery.",
  },
  "pre-workout": {
    "title": "Pre-Workout",
    "title_tag": "Best Pre-Workout Supplements {{MARKET}} (2026)",
    "description": "Shop {{MARKET}}'s best pre-workout supplements in 2026. Stimulant & stim-free options. 100% authentic, fast local delivery.",
  },
  "dymatize-nutrition": {
    "title": "Dymatize Nutrition",  # was ALL CAPS
    "title_tag": "Dymatize Nutrition {{MARKET}} — ISO 100 & Whey Protein (2026)",
    "description": "Shop Dymatize Nutrition in {{MARKET}} — ISO 100 Hydrolyzed, Elite Whey, Casein & more. Authorised retailer. 100% authentic, fast local delivery.",
  },
  "ghost": {
    "title": "Ghost",  # was ALL CAPS
    "title_tag": "Ghost Protein {{MARKET}} — Whey, Pre-Workout & Supplements (2026)",
    "description": "Buy Ghost protein powder & supplements in {{MARKET}} — Ghost Whey, Legend Pre-Workout, BCAA & more. Authorised retailer. Fast local delivery.",
  },
  "myprotein-{{market}}": {
    "title": "Myprotein",  # was ALL CAPS 'MYPROTEIN'
    "title_tag": "Buy Myprotein {{MARKET}} (2026) — Authorised Retailer",
    "description": "Shop authentic Myprotein supplements in {{MARKET}} — Impact Whey, creatine, multivitamins & more. Fast local delivery from our SG warehouse.",
  },
}

def api_get(url):
    req=urllib.request.Request(url, headers={"X-Shopify-Access-Token":TOKEN})
    return json.loads(urllib.request.urlopen(req).read())

def find_collection(handle):
    for ctype in ("smart_collections","custom_collections"):
        d=api_get(f"https://{SHOP}/admin/api/{API}/{ctype}.json?handle={handle}")
        arr=d.get(ctype,[])
        if arr: return ctype, arr[0]
    return None, None

def current_seo(cid):
    mf=api_get(f"https://{SHOP}/admin/api/{API}/collections/{cid}/metafields.json").get('metafields',[])
    return {m['key']:m['value'] for m in mf if m['namespace']=='global' and m['key'] in ('title_tag','description_tag')}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Actually push changes (default: dry-run)")
    ap.add_argument("--only", help="Limit to one handle")
    args=ap.parse_args()

    handles=[args.only] if args.only else list(TARGETS)
    mode="APPLY (LIVE)" if args.apply else "DRY-RUN (no changes)"
    print(f"=== patch_collection_seo.py — {mode} ===\n")

    for h in handles:
        want=TARGETS.get(h)
        if not want: print(f"[{h}] no target defined, skip"); continue
        ctype, col = find_collection(h)
        if not col: print(f"[{h}] NOT FOUND\n"); continue
        cid=col['id']; cur_title=col.get('title',''); seo=current_seo(cid)
        changes={}
        if want.get("title") and want["title"]!=cur_title:
            changes["collection.title"]=(cur_title, want["title"])
        if want.get("title_tag") and want["title_tag"]!=seo.get("title_tag"):
            changes["title_tag"]=(seo.get("title_tag","(none)"), want["title_tag"])
        if want.get("description") and want["description"]!=seo.get("description_tag"):
            changes["description_tag"]=(seo.get("description_tag","(none)")[:60]+"…", want["description"][:60]+"…")

        print(f"--- {h} (id={cid}) ---")
        if not changes:
            print("  no changes needed\n"); continue
        for k,(old,new) in changes.items():
            print(f"  {k}:")
            print(f"     OLD: {old}")
            print(f"     NEW: {new}")

        if args.apply:
            key="smart_collection" if ctype=="smart_collections" else "custom_collection"
            upd={"id":cid}
            if "collection.title" in changes: upd["title"]=want["title"]
            mfs=[]
            if "title_tag" in changes:
                mfs.append({"namespace":"global","key":"title_tag","value":want["title_tag"],"type":"single_line_text_field"})
            if "description_tag" in changes:
                mfs.append({"namespace":"global","key":"description_tag","value":want["description"],"type":"single_line_text_field"})
            if mfs: upd["metafields"]=mfs
            req=urllib.request.Request(
                f"https://{SHOP}/admin/api/{API}/{ctype}/{cid}.json",
                data=json.dumps({key:upd}).encode(), method="PUT",
                headers={"X-Shopify-Access-Token":TOKEN,"Content-Type":"application/json"})
            try:
                urllib.request.urlopen(req); print("  ✅ APPLIED\n")
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
                if hasattr(e,'read'): print("   ",e.read().decode()[:200])
                print()
        else:
            print("  (dry-run — not applied)\n")

    if not args.apply:
        print("Run again with --apply to push these changes live.")

if __name__=="__main__":
    main()

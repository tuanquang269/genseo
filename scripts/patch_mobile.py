#!/usr/bin/env python3
"""
patch_mobile.py — Fix Curator's Note + Related Guides for mobile-first layout.
Applies CSS class names + injects a <style> media-query block.
Re-deploys all patched collections to Shopify.
Usage: python3 patch_mobile.py
"""
import os, re, subprocess

GENSEO_DIR = "/Users/kevinkreative/genseo"
PUSH_SCRIPT = f"{GENSEO_DIR}/scripts/push_collection.py"

COLLECTIONS = [
    ("preworkout-collection.html",               "pre-workout",                  "Best Pre-Workout Supplements {{MARKET}} (2026)",                       "Shop {{MARKET}}'s best pre-workout supplements in 2026. Stimulant & stim-free options. 100% authentic, fast local delivery."),
    ("protein-powder-collection.html",           "protein-powder",               "Best Whey Protein Powder {{MARKET}} (2026)",                           "Shop the best whey protein powder in {{MARKET}} (2026). Isolate, concentrate & hydrolysate from top brands. 100% authentic, fast local delivery."),
    ("myprotein-{{market}}-collection.html",      "myprotein-{{market}}",          "Buy Myprotein {{MARKET}} (2026) — Authorised Retailer",                "Shop authentic Myprotein supplements in {{MARKET}} — Impact Whey, creatine, multivitamins & more. Fast local delivery from our SG warehouse."),
    ("creatine-collection.html",                 "creatine",                     "Best Creatine Monohydrate {{MARKET}} (2026)",                          "Shop the best creatine monohydrate supplements in {{MARKET}} (2026). Powder, capsules & gummies from top brands. 100% authentic, fast delivery."),
    ("mass-gainer-collection.html",              "mass-gainer",                  "Best Mass Gainer Supplements {{MARKET}} (2026)",                       "Shop {{MARKET}}'s best mass gainers in 2026 — high-calorie protein powders for hardgainers & bulking. 100% authentic, fast local delivery."),
    ("protein-bar-meal-replacement-collection.html", "protein-bar-meal-replacement", "Best Protein Bars {{MARKET}} (2026) | Low Sugar",                 "Shop {{MARKET}}'s best protein bars & meal replacement bars in 2026 — Quest, Barebells, Grenade & more. Low sugar, high protein. Fast delivery."),
    ("blenderbottle-collection.html",            "blenderbottle",                "BlenderBottle {{MARKET}} — Official Shaker Bottles (2026)",            "Shop BlenderBottle {{MARKET}} — official retailer for Classic, Strada & Radian shakers. Best protein shaker bottles with fast local delivery."),
    ("owala-collection.html",                    "owala",                        "Owala Water Bottles {{MARKET}} (2026) — Authorised Retailer",          "Shop authentic Owala water bottles & shakers in {{MARKET}} — FreeSip Tritan & Insulated Stainless. Authorised retailer. Fast local delivery."),
    ("dymatize-nutrition-collection.html",       "dymatize-nutrition",           "Dymatize Nutrition {{MARKET}} — ISO 100 & Whey Protein (2026)",        "Shop Dymatize Nutrition in {{MARKET}} — ISO 100 Hydrolyzed, Elite Whey, Casein & more. Authorised retailer. 100% authentic, fast local delivery."),
    ("fat-burner-collection.html",               "fat-burner",                   "Best Fat Burner Supplements {{MARKET}} (2026)",                        "Shop the best fat burner supplements in {{MARKET}} (2026). Stimulant & non-stim thermogenics from Cellucor, EVLution, JNX & more. Fast local delivery."),
    ("shakers-bottle-collection.html",           "shakers-bottle",               "Best Protein Shaker Bottles {{MARKET}} (2026)",                        "Shop the best protein shaker bottles & gym water bottles in {{MARKET}} (2026) — BlenderBottle, Owala & more. Fast local delivery."),
]

MOBILE_STYLE = """\
<style>
/* ── Mobile-first responsive fixes ─────────────────────────────── */
@media (max-width: 640px) {

  /* Curator's Note: stack photo above text on small screens */
  .usup-curator {
    flex-direction: column !important;
    align-items: center !important;
    gap: 16px !important;
  }
  .usup-curator-body {
    width: 100% !important;
    text-align: left !important;
  }
  .usup-curator-body p {
    text-align: left !important;
  }

  /* Related Guides: flex row so arrow never separates from text */
  .usup-guide-item {
    display: flex !important;
    align-items: flex-start !important;
    gap: 8px !important;
    padding-left: 0 !important;
    position: static !important;
  }
  .usup-guide-arrow {
    position: static !important;
    flex-shrink: 0 !important;
    line-height: 1.6 !important;
  }
  .usup-guide-link {
    text-align: left !important;
    display: block !important;
  }
}
</style>
"""


def strip_existing_patch(html: str) -> str:
    """Remove any previously injected style block so we don't stack duplicates."""
    return re.sub(
        r'<style>\s*/\*\s*──\s*Mobile-first.*?</style>\s*',
        '',
        html,
        flags=re.DOTALL
    )


def add_curator_class(html: str) -> str:
    """Add class="usup-curator" to the curator outer wrapper div and class to inner body div."""
    # Outer div: has both border-left:5px solid #fbdc00 AND display:flex
    html = re.sub(
        r'(<div)\s+(style="[^"]*border-left:\s*5px solid #fbdc00[^"]*display:\s*flex[^"]*")',
        r'<div class="usup-curator" \2',
        html
    )
    # Inner text div: has flex-grow: 1 immediately inside the curator div
    # We add class only to divs that don't already have a class
    html = re.sub(
        r'(<div)\s+(style="flex-grow:\s*1;?")',
        r'<div class="usup-curator-body" \2',
        html
    )
    return html


def fix_guide_items(html: str) -> str:
    """
    Convert Related Guides list items from position:absolute arrow to flex approach.
    Works even if class already present (idempotent).
    """

    # ── Fix <li> elements ─────────────────────────────────────────────────────
    # Pattern: any <li style="...padding-left: 20px; position: relative;...">
    def fix_li(m):
        style = m.group(1)
        # Replace padding-left + position:relative with flex vars we override via CSS
        style = re.sub(r'padding-left:\s*\d+px;\s*', '', style)
        style = re.sub(r'position:\s*relative;\s*', '', style)
        # Ensure text-align left
        if 'text-align' not in style:
            style = style.rstrip(';') + '; text-align: left;'
        return f'<li class="usup-guide-item" style="{style.strip()}">'

    html = re.sub(
        r'<li\s+(?:class="[^"]*"\s+)?style="([^"]*padding-left:[^"]*position:\s*relative[^"]*)"',
        fix_li,
        html
    )
    html = re.sub(
        r'<li\s+(?:class="[^"]*"\s+)?style="([^"]*position:\s*relative[^"]*padding-left:[^"]*)"',
        fix_li,
        html
    )

    # ── Fix the → arrow <span> ────────────────────────────────────────────────
    html = re.sub(
        r'<span\s+(?:class="[^"]*"\s+)?style="position:\s*absolute;\s*left:\s*0;\s*top:\s*\d+px;([^"]*?)">→</span>',
        r'<span class="usup-guide-arrow" style="color: #fbdc00; font-weight: 900;\1">→</span>',
        html
    )

    # ── Fix the <a> link ──────────────────────────────────────────────────────
    html = re.sub(
        r'(<a\s+href="[^"]*")\s+style="color:\s*#111;\s*text-decoration:\s*underline;\s*font-size:\s*14px;"',
        r'\1 class="usup-guide-link" style="color: #111; text-decoration: underline; font-size: 14px; text-align: left;"',
        html
    )

    return html


def patch(html: str) -> str:
    html = strip_existing_patch(html)
    html = add_curator_class(html)
    html = fix_guide_items(html)
    html = MOBILE_STYLE + html
    return html


def deploy(handle, filepath, title, meta):
    result = subprocess.run(
        ["python3", PUSH_SCRIPT, handle, filepath,
         "--title", title, "--meta-description", meta],
        capture_output=True, text=True
    )
    out = result.stdout + result.stderr
    ok = "SUCCESS" in out
    status = "✅" if ok else "❌"
    print(f"  {status} {handle}")
    if not ok:
        print(f"     {out[:400]}")
    return ok


if __name__ == "__main__":
    patched, deployed, skipped = 0, 0, 0

    for filename, handle, title, meta in COLLECTIONS:
        filepath = os.path.join(GENSEO_DIR, filename)
        if not os.path.exists(filepath):
            print(f"⚠️  {filename} not found — skipping")
            skipped += 1
            continue

        print(f"\n[{handle}]")

        with open(filepath, "r", encoding="utf-8") as f:
            original = f.read()

        fixed = patch(original)

        # Quick sanity checks
        assert "usup-curator" in fixed,   f"curator class missing in {filename}"
        assert "usup-guide-item" in fixed, f"guide-item class missing in {filename}"
        assert "usup-guide-arrow" in fixed, f"guide-arrow class missing in {filename}"
        print(f"  🔧 Patched (curator={'usup-curator' in fixed}, guides={'usup-guide-item' in fixed})")
        patched += 1

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(fixed)

        ok = deploy(handle, filepath, title, meta)
        if ok:
            deployed += 1

    print(f"\n{'─'*50}")
    print(f"Patched: {patched} | Deployed: {deployed} | Skipped: {skipped}")

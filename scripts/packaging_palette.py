#!/usr/bin/env python3
"""Packaging-color source of truth for listicle and advertorial landing pages.

Kevin 2026-10-09: the page's UI colors must match the hero product's packaging.
The committed file is product_refs/<handle>.palette.json. Hex values in those
files are measurements (k-means of the pack photo already in product_refs, or
the packaging note in product_refs/<handle>.json). This module does not invent
a brand color for a product that has no file.

  python3 scripts/packaging_palette.py --spec landing_drafts/<slug>.json
  python3 scripts/packaging_palette.py --brief <handle>
  python3 scripts/packaging_palette.py --gaps

Hard window: landing specs created on or after 2026-10-09 (template listicle or
advertorial, or engine ref). Older live pages are left alone.

Chromatic file (FloraFresh, dusty pink / rose #d17a85): palette off, or a manual
hue more than hue_tolerance degrees from the file, is a violation. The render
gate (scripts/landing_palette.py check) fails when the painted CTA, accent, or
sage hue is outside that tolerance, and when the pack photo's own hue disagrees
with the file.

Neutral file (AgeAura Pure NMN + TMG, white with dark grey text, no chromatic
cluster): a forced hue outside the house-green band is a violation. House greens
stay allowed only while house_palette_allowed is true. That fallback is the
existing renderer behavior, not a color read off the bottle.

A product with no palette file is a gap (see --gaps). The gate does not guess a
hue for it. Blog articles are out of scope; they keep the house block kit.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTO_FROM = "2026-10-09"
HUE_TOL = 30.0
HOUSE_HUE = (95.0, 170.0)
PREFIX = "packaging palette: "

_PRODUCT = re.compile(r"/products/([a-z0-9-]+)", re.I)
_LANDING_LINE = re.compile(r"(?i)(?:listicle|advertorial)\s*\|")
_PRODUCT_EQ = re.compile(r"product=([a-z0-9-]+)", re.I)
_OPT_OUT = re.compile(r'(?i)palette\s*[:=]\s*["\']?off\b|"palette"\s*:\s*"off"')
_HUE = re.compile(
    r'(?i)(?:"palette"\s*:\s*\{[^}]*"hue"\s*:\s*([0-9.]+)'
    r"|palette\s*[:=]\s*\{[^}]*hue[\"']?\s*[:=]\s*([0-9.]+)"
    r"|palette\s+hue\s*[:=]?\s*([0-9.]+))"
)


def hue_dist(h1, h2):
    d = abs(float(h1) - float(h2)) % 360
    return min(d, 360 - d)


def palette_path(handle, refs_dir=None):
    folder = refs_dir or os.path.join(ROOT, "product_refs")
    return os.path.join(folder, handle + ".palette.json")


def load(handle, refs_dir=None):
    """Parsed palette file, or None when this product has no committed palette."""
    if not handle:
        return None
    path = palette_path(handle, refs_dir)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    data["_path"] = os.path.relpath(path, ROOT)
    return data


def hero_handle(spec):
    if not isinstance(spec, dict):
        return None
    if spec.get("product_ref"):
        return str(spec["product_ref"]).strip().lower()
    for blk in (spec.get("offer") or {}, spec.get("sticky_cta") or {}, (spec.get("hero") or {}).get("cta") or {}):
        if not isinstance(blk, dict):
            continue
        found = _PRODUCT.search(blk.get("href") or "")
        if found:
            return found.group(1).lower()
    return None


def in_window(spec):
    """True for a listicle/advertorial landing spec dated on or after the rule."""
    if not isinstance(spec, dict):
        return False
    if str(spec.get("created") or "") < AUTO_FROM:
        return False
    return spec.get("template") in ("listicle", "advertorial") or spec.get("engine") == "ref"


def landing_note(handle):
    """One clause for a landing ticket. Empty when this product has no palette file."""
    pal = load(handle)
    if not pal:
        return ""
    if pal.get("kind") == "chromatic":
        return (
            "UI colors follow product_refs/%s.palette.json (%s, %s). "
            "Do not opt out or recolor away from that pack."
            % (handle, pal.get("hex") or "", pal.get("packaging_note") or "")
        )
    if pal.get("kind") == "neutral":
        return (
            "UI colors: pack is neutral (%s; product_refs/%s.palette.json). "
            "Do not force a chromatic hue."
            % (pal.get("packaging_note") or "no chromatic cluster", handle)
        )
    return ""


def iter_product_handles(refs_dir=None):
    folder = refs_dir or os.path.join(ROOT, "product_refs")
    handles = []
    if not os.path.isdir(folder):
        return handles
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".json"):
            continue
        if name.endswith(".label.json") or name.endswith(".palette.json"):
            continue
        handles.append(name[: -len(".json")])
    return handles


def gaps(refs_dir=None):
    """Product handles that have a packaging note and no palette file.

    The denied Urolithin SKU is omitted. Do not add a palette for it.
    """
    missing = []
    for handle in iter_product_handles(refs_dir):
        if "urolithin" in handle:
            continue
        if load(handle, refs_dir) is None:
            missing.append(handle)
    return missing


def spec_violations(spec):
    """Violations for a landing spec. Empty outside the hard window or with no palette file."""
    if not in_window(spec):
        return []
    handle = hero_handle(spec)
    if not handle:
        return []
    pal = load(handle)
    if not pal:
        return []
    return conflicts(spec, pal, handle)


def image_violations(spec, extracted):
    """The pack photo disagrees with the committed file. Empty when there is no file."""
    if not in_window(spec) or not extracted:
        return []
    handle = hero_handle(spec)
    pal = load(handle) if handle else None
    if not pal:
        return []
    if pal.get("kind") == "chromatic" and pal.get("hue") is not None:
        dist = hue_dist(extracted.get("hue"), pal["hue"])
        tol = float(pal.get("hue_tolerance", HUE_TOL))
        if dist > tol:
            return [
                PREFIX + "%s pack photo hue %s is %.0f° from the palette file %s"
                % (handle, extracted.get("hue"), dist, pal.get("hex") or pal["hue"])
            ]
        return []
    if pal.get("kind") == "neutral":
        return [
            PREFIX + "%s palette file says neutral (%s) but the pack photo has chromatic hue %s (%s)"
            % (handle, pal.get("packaging_note") or "", extracted.get("hue"), extracted.get("hex") or "")
        ]
    return []


def conflicts(spec, pal, handle):
    """Spec-level conflicts with one palette dict. `kind` other than chromatic/neutral fails closed."""
    mode = spec.get("palette", "auto")
    kind = pal.get("kind")
    if kind == "chromatic":
        if pal.get("hue") is None:
            return [PREFIX + handle + " chromatic palette file has no hue"]
        out = []
        if mode == "off":
            out.append(
                PREFIX + "%s is %s (%s); palette off would keep the house greens"
                % (handle, pal.get("hex") or pal["hue"], pal.get("packaging_note") or "chromatic pack")
            )
        if isinstance(mode, dict) and "hue" in mode:
            dist = hue_dist(mode["hue"], pal["hue"])
            tol = float(pal.get("hue_tolerance", HUE_TOL))
            if dist > tol:
                out.append(
                    PREFIX + "%s hue %s is %.0f° from pack hue %s (%s; tolerance %.0f°)"
                    % (handle, mode["hue"], dist, pal["hue"], pal.get("hex") or "", tol)
                )
        return out
    if kind == "neutral":
        if isinstance(mode, dict) and "hue" in mode:
            hue = float(mode["hue"])
            if pal.get("house_palette_allowed") and HOUSE_HUE[0] <= hue <= HOUSE_HUE[1]:
                return []
            return [
                PREFIX + "%s pack is neutral (%s); hue %s is not a measured pack color"
                % (handle, pal.get("packaging_note") or "no chromatic cluster", mode["hue"])
            ]
        return []
    return [PREFIX + handle + " palette file has no usable kind"]


def ticket_violations(text):
    """Open landing-ticket lines that opt out or name a conflicting hue.

    Article tickets do not use `listicle |` / `advertorial |`, so house-green
    article copy is not a hit. A product with no palette file is not a hit.
    """
    text = text or ""
    if not _LANDING_LINE.search(text):
        return []
    found = _PRODUCT_EQ.search(text)
    if not found:
        return []
    handle = found.group(1).lower()
    if load(handle) is None:
        return []
    base = {"template": "listicle", "engine": "ref", "created": AUTO_FROM, "product_ref": handle}
    out = []
    if _OPT_OUT.search(text):
        spec = dict(base, palette="off")
        out.extend(spec_violations(spec))
    hue_match = _HUE.search(text)
    if hue_match:
        raw = next(group for group in hue_match.groups() if group)
        spec = dict(base, palette={"hue": float(raw)})
        out.extend(spec_violations(spec))
    deduped = []
    for item in out:
        if item not in deduped:
            deduped.append(item)
    return deduped


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if argv[0] == "--brief":
        if len(argv) != 2:
            sys.exit(__doc__)
        note = landing_note(argv[1])
        if not note:
            print("packaging palette: no file for " + argv[1])
            return 1
        print(note)
        return 0
    if argv[0] == "--gaps":
        missing = gaps()
        for handle in missing:
            print(handle)
        print("gaps: %d product(s) without product_refs/<handle>.palette.json" % len(missing))
        return 0
    if argv[0] == "--spec":
        if len(argv) != 2:
            sys.exit(__doc__)
        with open(argv[1], encoding="utf-8") as fh:
            spec = json.load(fh)
        bad = spec_violations(spec)
        print("packaging_palette: %d violation(s)" % len(bad))
        for item in bad:
            print("  " + item)
        return 1 if bad else 0
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main())

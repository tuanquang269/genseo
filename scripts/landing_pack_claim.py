#!/usr/bin/env python3
"""Normalize a landing spec's pack_images claim before validate_landing.py.

  /usr/bin/python3 scripts/landing_pack_claim.py prepare landing_drafts/<slug>.json

No Shopify, no --live, no theme edit. The daily wrapper runs this after the writer
and before validate_landing.py.

Two shapes, matching docs/LABEL_OCR_GATE.md:

- No product_refs/<handle>-cutout.png: pack_images is not a whitelist shot. Drop
  the key, scrub a label-gate pass claim, and point any image that used those
  paths at a webp of product_refs/<handle>.png (the curated pack photo).
- Cutout present: keep pack_images. A listed file that fails the label gate is
  replaced with a webp of that cutout so the gate reads the real label, not a
  redraw. Shots that already pass are left alone. The gate still runs.
"""
import json
import os
import re
import sys

from PIL import Image

import brand_rules
import landing_label_gate as llg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_IMAGE_KEYS = {"image", "avatar"}


def product_handle(spec):
    found = re.search(r"/products/([a-z0-9-]+)", json.dumps(spec))
    return found.group(1) if found else None


def _cutout(handle, root):
    return os.path.join(root, "product_refs", handle + "-cutout.png")


def _label(handle, root):
    return os.path.join(root, "product_refs", handle + ".label.json")


def _png(handle, root):
    return os.path.join(root, "product_refs", handle + ".png")


def _flatten(path):
    image = Image.open(path)
    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.getchannel("A"))
        return background
    return image.convert("RGB")


def save_under_80kb(image, dest):
    """Write a webp under 80 KB. Raises OSError if it cannot."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    width0 = image.width
    widths = [width0]
    for width in (1000, 800, 640, 480, 360):
        if width < width0:
            widths.append(width)
    for width in widths:
        frame = image
        if width != width0:
            frame = image.resize(
                (width, max(1, round(image.height * width / width0))), Image.LANCZOS
            )
        for quality in (80, 70, 60, 50, 40):
            frame.save(dest, "WEBP", quality=quality, method=6)
            if os.path.getsize(dest) < 80 * 1024:
                return
    raise OSError("could not write %s under 80 KB" % dest)


def _pack_webp(spec, handle, root, source, name):
    slug = spec.get("slug") or handle
    rel = "tmp_images/landing-%s/%s" % (slug, name)
    dest = os.path.join(root, rel)
    save_under_80kb(_flatten(source), dest)
    return rel


def _walk(obj, on_dict):
    if isinstance(obj, dict):
        on_dict(obj)
        for value in obj.values():
            _walk(value, on_dict)
    elif isinstance(obj, list):
        for value in obj:
            _walk(value, on_dict)


def _map_images(spec, mapping):
    def visit(node):
        packs = node.get("pack_images")
        if isinstance(packs, list):
            node["pack_images"] = [mapping.get(item, item) for item in packs]
        for key in _IMAGE_KEYS:
            value = node.get(key)
            if isinstance(value, str) and value in mapping:
                node[key] = mapping[value]

    _walk(spec, visit)


def _scrub(spec):
    changed = False

    def scrub_value(value):
        nonlocal changed
        if isinstance(value, str):
            cleaned = llg._WHITELIST_CLAIM.sub("real pack photo", value)
            if cleaned != value:
                changed = True
            return cleaned
        if isinstance(value, dict):
            for key in list(value.keys()):
                value[key] = scrub_value(value[key])
            return value
        if isinstance(value, list):
            return [scrub_value(item) for item in value]
        return value

    scrub_value(spec)
    return changed


def prepare_spec(spec, root=None, run_gate=None):
    """Mutate spec in place. Return note strings. Writes pack webps under root.

    run_gate(image, handle) -> (returncode, summary). Default is the real
    landing_label_gate.py subprocess. Tests pass a stub. This function never
    contacts Shopify.
    """
    root = ROOT if root is None else root
    notes = []
    handle = product_handle(spec)
    if not handle:
        return notes
    cutout = _cutout(handle, root)
    label = _label(handle, root)
    if not os.path.isfile(cutout):
        if not os.path.isfile(label):
            return notes
        packs = list(spec.get("pack_images") or [])
        if not packs and not llg.claims_label_whitelist(spec):
            return notes
        png = _png(handle, root)
        rel = None
        if packs and os.path.isfile(png) and brand_rules.asset_path_allowed(png):
            rel = _pack_webp(spec, handle, root, png, "real-pack.webp")
            _map_images(spec, {path: rel for path in packs})
        elif packs:
            notes.append(
                "no curated png for %s; removed pack_images without swapping pixels" % handle
            )
        spec.pop("pack_images", None)
        _scrub(spec)
        notes.insert(
            0,
            "no cutout for %s: omitted pack_images (curated pack photo, not a whitelist shot)"
            % handle,
        )
        return notes
    packs = list(spec.get("pack_images") or [])
    if not packs or not brand_rules.asset_path_allowed(cutout):
        return notes
    gate = run_gate or (lambda image, gated: llg._default_run_gate(root, image, gated))
    failed = []
    for image in packs:
        code, line = gate(image, handle)
        if code != 0:
            failed.append((image, line))
    if not failed:
        return notes
    rel = _pack_webp(spec, handle, root, cutout, "cutout-pack.webp")
    _map_images(spec, {image: rel for image, _line in failed})
    unique = []
    for image in spec.get("pack_images") or []:
        if image not in unique:
            unique.append(image)
    spec["pack_images"] = unique
    summary = failed[0][1][:120]
    notes.append(
        "replaced %d pack shot(s) for %s that failed the label gate (%s) with the cutout"
        % (len(failed), handle, summary)
    )
    return notes


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2 or argv[0] != "prepare":
        sys.exit("usage: landing_pack_claim.py prepare <spec.json>")
    path = argv[1]
    with open(path, encoding="utf-8") as fh:
        spec = json.load(fh)
    notes = prepare_spec(spec, ROOT)
    if notes:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(spec, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        for note in notes:
            print(note)
    else:
        print("pack claim unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())

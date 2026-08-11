#!/usr/bin/env python3
"""verify_ad_assets.py — measure every delivered ad asset. Independent of the
script that produced them, on purpose: a build step that reports its own output
is reporting its intent, not the bytes on disk.

Checks each file against the Demand Gen specs read from Google Ads Help
(13704860 / 17140672) on 2026-08-11, and against the v24 MimeType enum, which
has IMAGE_JPEG / IMAGE_PNG / IMAGE_GIF and no webp member.

Run with /usr/bin/python3.
"""
import glob
import os
import sys

from PIL import Image

ROOT = "/Users/kevinkreative/genseo/tmp_images/fusiforce-ad-assets"
UPLOADABLE = {"PNG", "JPEG", "GIF"}          # mirrors MimeTypeEnum.MimeType
# name pattern -> (w, h, max_bytes, label)
EXPECT = {
    "1200x628": (1200, 628, 5 * 1024 * 1024, "landscape 1.91:1"),
    "1200x1200": (1200, 1200, 5 * 1024 * 1024, "square 1:1"),
    "1200x300": (1200, 300, 150 * 1024, "logo 4:1"),
}
LOGO_CAP = 150 * 1024


def main():
    rows, bad = [], []
    for path in sorted(glob.glob(os.path.join(ROOT, "*.png"))
                       + glob.glob(os.path.join(ROOT, "*.jpg"))):
        name = os.path.basename(path)
        with Image.open(path) as im:
            fmt, (w, h) = im.format, im.size
        nbytes = os.path.getsize(path)
        key = next((k for k in EXPECT if k in name), None)
        notes = []
        if fmt not in UPLOADABLE:
            notes.append(f"FORMAT {fmt} is not an uploadable MimeType")
        if key is None:
            notes.append("unrecognised geometry in filename")
        else:
            ew, eh, cap, label = EXPECT[key]
            if name.startswith("logo_") and key == "1200x1200":
                cap = LOGO_CAP
            if (w, h) != (ew, eh):
                notes.append(f"DIMENSIONS {w}x{h} != {ew}x{eh}")
            if nbytes > cap:
                notes.append(f"SIZE {nbytes//1024}KB > {cap//1024}KB cap")
        rows.append((name, fmt, f"{w}x{h}", f"{nbytes//1024}KB",
                     "; ".join(notes) or "ok"))
        if notes:
            bad.append(name)

    w0 = max(len(r[0]) for r in rows)
    print(f"{'file'.ljust(w0)}  {'fmt'.ljust(5)} {'measured'.ljust(10)} {'bytes'.ljust(8)} notes")
    for r in rows:
        print(f"{r[0].ljust(w0)}  {r[1].ljust(5)} {r[2].ljust(10)} {r[3].ljust(8)} {r[4]}")
    print(f"\n{len(rows)} files, {len(rows)-len(bad)} conforming, {len(bad)} problem(s)")
    if any(f.endswith(".webp") for f in os.listdir(ROOT)):
        print("✗ a .webp is present in the delivery directory")
        return 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

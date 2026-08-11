#!/usr/bin/env python3
"""wn_logo_assets.py — Google Ads logo assets from the REAL Wellness Nest logo.

Nothing here is generated. Google requires the logo to represent the advertised
business; a generated or generic mark is a policy violation and would also be
the wrong logo. Both sources were downloaded (GET only) from the live storefront
on 2026-08-11:

  square source  ~/genseo/tmp_images/fusiforce-ad-assets/_logo_src/WNN_Main_Symbol.png
      from https://wellnessnest.co/cdn/shop/files/WNN_Main_Symbol.png?v=1769680118
      referenced by:  <link rel="icon" ...> on https://wellnessnest.co/
      measured 1523x1001 RGBA — the green "W" nest mark, the brand's own icon

  wordmark source ~/genseo/tmp_images/fusiforce-ad-assets/_logo_src/WNN_Main_Logo.png
      from https://wellnessnest.co/cdn/shop/files/WNN_Main_Logo_eb77747f-0bd5-4316-a9ba-92349ddbe5cc.png
      referenced by:  header <img alt="Wellness Nest"> on https://wellnessnest.co/
      measured 2601x601 RGBA — full "W + Wellness Nest" horizontal lockup

Outputs (Google Ads Help 13704860, read 2026-08-11): logo 1:1 recommended
1200x1200, max 150KB. The 4:1 1200x300 landscape logo is NOT listed on the
Demand Gen asset page — it is a Display/Performance Max slot — so it is built
here as an optional extra, not as a Demand Gen requirement.

Neither source is square or exactly 4:1, so both are FITTED (aspect preserved)
and padded onto a white canvas. Never stretched: a stretched logo is a modified
logo. White rather than transparent because a transparent logo disappears
against whichever background the placement happens to use.

Run with /usr/bin/python3 (Homebrew python3 has no PIL).
"""
import os

from PIL import Image

SRC = "/Users/kevinkreative/genseo/tmp_images/fusiforce-ad-assets/_logo_src"
OUT = "/Users/kevinkreative/genseo/tmp_images/fusiforce-ad-assets"
MAX_LOGO_BYTES = 150 * 1024


def fit_on_white(src_path, tw, th, margin=0.08):
    """Scale to fit inside the target with a margin, centre on white. No stretch."""
    im = Image.open(src_path).convert("RGBA")
    box_w, box_h = int(tw * (1 - 2 * margin)), int(th * (1 - 2 * margin))
    scale = min(box_w / im.width, box_h / im.height)
    im = im.resize((max(1, int(round(im.width * scale))),
                    max(1, int(round(im.height * scale)))), Image.LANCZOS)
    canvas = Image.new("RGBA", (tw, th), (255, 255, 255, 255))
    canvas.paste(im, ((tw - im.width) // 2, (th - im.height) // 2), im)
    return canvas.convert("RGB")


def save_under_cap(im, path):
    """PNG first. A flat two-colour logo compresses far under 150KB, but the cap
    is real, so verify it rather than assume it — and fall back to JPEG (also an
    accepted format) if a future logo ever blows past it."""
    im.save(path, "PNG", optimize=True)
    if os.path.getsize(path) <= MAX_LOGO_BYTES:
        return path
    jpg = path.rsplit(".", 1)[0] + ".jpg"
    for q in (95, 90, 85, 80):
        im.save(jpg, "JPEG", quality=q, optimize=True)
        if os.path.getsize(jpg) <= MAX_LOGO_BYTES:
            os.unlink(path)
            return jpg
    raise SystemExit(f"✗ {path}: cannot get the logo under 150KB")


def main():
    made = []
    # 1:1 — the nest symbol. It is the mark the brand itself uses in a square
    # slot (it is the site favicon), and it stays legible when a placement
    # renders the logo small. The full lockup fitted into a square would put the
    # wordmark at ~277px tall inside 1200px of mostly empty canvas.
    made.append(save_under_cap(
        fit_on_white(os.path.join(SRC, "WNN_Main_Symbol.png"), 1200, 1200, margin=0.12),
        os.path.join(OUT, "logo_1200x1200.png")))
    # 4:1 — the horizontal lockup, which is natively 4.33:1 and so fits width-wise
    # with a little padding top and bottom.
    made.append(save_under_cap(
        fit_on_white(os.path.join(SRC, "WNN_Main_Logo.png"), 1200, 300, margin=0.04),
        os.path.join(OUT, "logo_1200x300.png")))

    for p in made:
        with Image.open(p) as im:
            print(f"{os.path.basename(p)}  {im.format} {im.size[0]}x{im.size[1]}  "
                  f"{os.path.getsize(p)//1024}KB")


if __name__ == "__main__":
    main()

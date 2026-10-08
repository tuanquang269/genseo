#!/usr/bin/env python3
"""Brand-locked product shots for landing pages: the REAL pack, composited into a generated scene.

  /usr/bin/python3 scripts/landing_pack_shots.py --bg <scene.webp> --out <out.webp> --x 0.6 --base 0.68 --h 0.58 \
      [--cut product_refs/<handle>-cutout.png] [--light left|right] [--dark]

Why compositing (product-image-brandlock §CORE LESSON + PATI-ADAPTATION #7): image models redraw labels and marks
from their own prior; pasting the real pack makes the logo, title and benefit rows correct by construction.
The scene comes from article_images.py (no product, empty podium/ledge, one art direction for the whole page);
this script adds the real cutout (made with scripts/tools/subject_lift.swift from a PDP image) plus lighting:
side shading from the key light, a warm tone match to the scene, a contact shadow and a soft cast shadow.
--x = horizontal centre of the pack (0..1), --base = y of the pack's base (0..1), --h = pack height (0..1).
Output is webp < 80 KB (website-images-under-80kb).
"""
import argparse, os, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--cut", default=os.path.join(ROOT, "product_refs", "ageaura-pure-nmn-tmg-nad-complex-cutout.png"))
    ap.add_argument("--x", type=float, default=0.5); ap.add_argument("--base", type=float, default=0.72)
    ap.add_argument("--h", type=float, default=0.55); ap.add_argument("--light", default="left")
    ap.add_argument("--dark", action="store_true", help="scene is dark: lower the pack exposure a touch")
    ap.add_argument("--size", type=int, default=1200)
    a = ap.parse_args()
    bg = Image.open(a.bg).convert("RGB")
    if bg.width != a.size:
        bg = bg.resize((a.size, round(bg.height * a.size / bg.width)), Image.LANCZOS)
    W, H = bg.size
    cut = Image.open(a.cut).convert("RGBA")
    ph = int(a.h * H); pw = int(cut.width * ph / cut.height)
    cut = cut.resize((pw, ph), Image.LANCZOS)
    x0 = int(a.x * W - pw / 2); y0 = int(a.base * H - ph)
    rgb, alpha = cut.convert("RGB"), cut.getchannel("A")
    # 1) tone match: multiply 10% toward the scene's mean colour around the base
    region = bg.crop((max(0, x0 - pw // 2), max(0, y0 + ph // 2), min(W, x0 + pw + pw // 2), min(H, y0 + ph + ph // 6)))
    mean = tuple(int(v) for v in ImageStat.Stat(region).mean[:3])
    rgb = Image.blend(rgb, ImageChops.multiply(rgb, Image.new("RGB", rgb.size, mean)), 0.10)
    if a.dark:
        rgb = Image.blend(rgb, Image.new("RGB", rgb.size, (0, 0, 0)), 0.10)
    # 2) cylindrical shading from the key light: far side darker, soft edge falloff, a highlight band near the lit side
    import math
    bx = alpha.getbbox() or (0, 0, pw, ph)
    prof_d, prof_h = [], []
    for x in range(pw):
        u = min(1.0, max(0.0, (x - bx[0]) / max(1, bx[2] - bx[0])))
        if a.light != "left":
            u = 1 - u
        edge = max(0.0, 1 - min(u, 1 - u) / 0.12)            # 1 at the silhouette edges
        prof_d.append(int(255 * min(0.6, 0.03 + 0.34 * u ** 2.2 + 0.16 * edge ** 2)))
        prof_h.append(int(255 * 0.22 * math.exp(-((u - 0.2) / 0.07) ** 2)))
    dark = Image.new("L", (pw, 1)); dark.putdata(prof_d); dark = dark.resize((pw, ph))
    hil = Image.new("L", (pw, 1)); hil.putdata(prof_h); hil = hil.resize((pw, ph))
    rgb = Image.composite(Image.new("RGB", rgb.size, (28, 32, 26)), rgb, dark)
    rgb = Image.composite(Image.new("RGB", rgb.size, (255, 254, 250)), rgb, hil)
    cut = rgb.copy(); cut.putalpha(alpha)
    out = bg.convert("RGBA")
    # 3) cast shadow: the silhouette sheared away from the light, very soft
    sh = Image.new("L", (W, H), 0)
    sil = alpha.resize((pw, max(1, int(ph * 0.35))))
    shear = 0.9 if a.light == "left" else -0.9
    sil = sil.transform((pw + int(abs(shear) * sil.height), sil.height), Image.AFFINE,
                        (1, shear if shear < 0 else -shear, (-shear * sil.height if shear > 0 else 0), 0, 1, 0), Image.BICUBIC)
    sil = sil.transpose(Image.FLIP_TOP_BOTTOM)
    sh.paste(sil, (x0 + (0 if shear > 0 else -int(abs(shear) * sil.height)), y0 + ph - int(sil.height * 0.15)), sil)
    sh = sh.filter(ImageFilter.GaussianBlur(max(6, pw // 18))).point(lambda v: int(v * (0.28 if not a.dark else 0.4)))
    out = Image.composite(Image.new("RGBA", (W, H), (30, 28, 22, 255)), out, sh)
    # 4) contact shadow under the base
    cs = Image.new("L", (W, H), 0); d = ImageDraw.Draw(cs)
    cw, ch = int(pw * 0.86), max(6, int(ph * 0.045))
    cx, cy = int(a.x * W), y0 + ph - int(ch * 0.35)
    d.ellipse((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2), fill=200)
    cs = cs.filter(ImageFilter.GaussianBlur(max(4, ch // 2)))
    out = Image.composite(Image.new("RGBA", (W, H), (20, 18, 14, 255)), out, cs.point(lambda v: int(v * 0.6)))
    out.alpha_composite(cut, (x0, y0))
    out = out.convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    for w, qs in ((1200, (84, 78, 72)), (1000, (82, 76)), (880, (80, 74)), (760, (78, 70, 62))):
        im = out if w >= W else out.resize((w, round(H * w / W)), Image.LANCZOS)
        for q in qs:
            im.save(a.out, "WEBP", quality=q, method=6)
            if os.path.getsize(a.out) < 80 * 1024:
                print(f"✓ {a.out} {im.size} q{q} {os.path.getsize(a.out)//1024} KB"); return
    sys.exit("✗ could not get under 80 KB")


if __name__ == "__main__":
    main()

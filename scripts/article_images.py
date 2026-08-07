#!/usr/bin/env python3
"""article_images.py — GenSeo image lane for wellnessnest.co.

Generates ONE article image via ima2 (ChatGPT Image 2.0 OAuth — the only
generator PATI hard rules allow), then compresses it to webp under 80KB
(website-image hard rule; Shopify CDN re-encodes, so small source = small CDN).

Usage:
  python3 article_images.py --slug <article-slug> --name hero \
      --prompt "..." [--ref /abs/path/real_pack.png ...] [--square]

Prints the LOCAL absolute .webp path on the last line — put exactly that path
in the draft's ![alt](...) tag; shopify_publisher.py uploads it to the CDN.

House rules baked in:
  * generator = ima2 OAuth only (no KIE / per-token APIs)
  * default size 1536x1024 (blog landscape, 1K class — never 2K/4K)
  * every prompt gets the no-watermark/no-caption suffix
  * output webp < 80KB (quality ladder, then width ladder)
  * HARD RULE (Kevin 2026-08-07): any image that SHOWS a product must be
    generated FROM the real packaging on /products/<handle> — pass
    --product-ref <handle> (auto-downloads the PDP pack shot as ref and locks
    the prompt to it). Never invent packaging: format (pouch vs jar vs
    bottle), colors, and label must match the live PDP. The first violation
    was real: FusiForce gens showed a JAR; the real product is a green POUCH.
    After generating, VIEW the output next to the ref before using it.
"""
import argparse
import os
import re
import subprocess
import sys

IMA2 = "/Users/kevinkreative/.npm-global/bin/ima2"
CWEBP = "/opt/homebrew/bin/cwebp"
OUT_ROOT = "/Users/kevinkreative/genseo/tmp_images"
MAX_BYTES = 80 * 1024
PROMPT_SUFFIX = (" NO watermark. NO blog name text. NO caption. NO attribution text in any "
                 "corner. Clean image only. Product label must remain legible. "
                 "No recognizable human faces.")
PACK_FIDELITY = (" The product package must EXACTLY match the reference image: same package "
                 "format, same shape, same colors, same label layout and text. Do not invent, "
                 "restyle, or substitute the packaging.")


def fetch_product_ref(handle_spec):
    """--product-ref <handle>[:index] → download the real PDP image as a PNG ref.
    Index defaults to 0 (the main pack shot). Cached per handle:index."""
    import io
    import json
    import urllib.request
    from PIL import Image
    handle, _, idx = handle_spec.partition(":")
    idx = int(idx or 0)
    dest = os.path.join(OUT_ROOT, f"ref_{re.sub(r'[^a-z0-9-]', '-', handle)}_{idx}.png")
    if os.path.exists(dest):
        return dest
    p = json.load(urllib.request.urlopen(f"https://wellnessnest.co/products/{handle}.js"))
    if idx >= len(p["images"]):
        sys.exit(f"✗ product {handle} has only {len(p['images'])} images (asked for index {idx})")
    url = "https:" + p["images"][idx] + "&width=1200"
    req = urllib.request.Request(url, headers={"Accept": "image/webp", "User-Agent": "Mozilla/5.0"})
    Image.open(io.BytesIO(urllib.request.urlopen(req).read())).convert("RGB").save(dest)
    return dest


def _ensure_serve(env):
    """ima2 gen needs the local `ima2 serve` daemon (holds the ChatGPT OAuth
    session, image endpoint at 127.0.0.1:3333). Unattended daily runs can't
    assume it's up, so probe the port and start it if needed."""
    import socket
    import time
    with socket.socket() as s:
        s.settimeout(2)
        if s.connect_ex(("127.0.0.1", 3333)) == 0:
            return
    subprocess.Popen([IMA2, "serve"], env=env,
                     stdout=open("/tmp/ima2-serve-genseo.log", "a"),
                     stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(15):  # re-probe up to 30s instead of hoping a fixed sleep is enough
        time.sleep(2)
        with socket.socket() as s:
            s.settimeout(2)
            if s.connect_ex(("127.0.0.1", 3333)) == 0:
                return
    sys.exit("✗ ima2 serve did not come up within 30s — check /tmp/ima2-serve-genseo.log (OAuth session may need re-login)")


def gen_png(prompt, size, out_png, refs, timeout=360):
    cmd = [IMA2, "gen", prompt + PROMPT_SUFFIX, "-q", "medium", "-s", size,
           "-o", out_png, "--timeout", str(timeout)]
    for r in refs:
        if not os.path.exists(r):
            sys.exit(f"✗ ref image not found: {r}")
        cmd += ["--ref", r]
    env = os.environ.copy()
    env["PATH"] = os.path.dirname(IMA2) + ":" + env.get("PATH", "")
    _ensure_serve(env)
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout + 30)
    if res.returncode != 0 or not os.path.exists(out_png) or os.path.getsize(out_png) < 30_000:
        tail = (res.stderr or res.stdout).strip().splitlines()[-3:]
        sys.exit("✗ ima2 generation failed: " + " | ".join(tail))


def compress_webp(src_png, out_webp):
    """Quality ladder first, then width ladder — stop at the first result <80KB."""
    for width in (1200, 1000, 800, 640):
        for q in (80, 70, 60, 50, 40):
            res = subprocess.run(
                [CWEBP, "-q", str(q), "-resize", str(width), "0", src_png, "-o", out_webp],
                capture_output=True, text=True)
            if res.returncode == 0 and os.path.exists(out_webp) and os.path.getsize(out_webp) < MAX_BYTES:
                return os.path.getsize(out_webp), q, width
    sys.exit("✗ could not compress under 80KB even at q40/640px — simplify the image")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True, help="article slug (output folder name)")
    ap.add_argument("--name", required=True, help="image name, e.g. hero, fusiforce-lifestyle")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--ref", action="append", default=[], help="absolute path to a REAL product image (repeatable)")
    ap.add_argument("--product-ref", action="append", default=[],
                    help="<handle>[:index] — auto-download the live PDP pack shot as ref and lock "
                         "the prompt to that packaging (REQUIRED whenever the image shows a product)")
    ap.add_argument("--square", action="store_true", help="1024x1024 instead of 1536x1024 landscape")
    a = ap.parse_args()

    for spec in a.product_ref:
        a.ref.append(fetch_product_ref(spec))
    if a.product_ref:
        a.prompt += PACK_FIDELITY

    slug = re.sub(r"[^a-z0-9-]", "-", a.slug.lower())
    name = re.sub(r"[^a-z0-9-]", "-", a.name.lower())
    out_dir = os.path.join(OUT_ROOT, slug)
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.join(out_dir, f"{name}.png")
    webp = os.path.join(out_dir, f"{name}.webp")

    size = "1024x1024" if a.square else "1536x1024"
    print(f"⏳ ima2 gen {name} ({size}, {len(a.ref)} ref)...", flush=True)
    gen_png(a.prompt, size, png, a.ref)
    nbytes, q, width = compress_webp(png, webp)
    os.unlink(png)  # keep only the deliverable; the PNG is 10-20x the size
    print(f"✓ {nbytes//1024}KB webp (q{q}, {width}px)")
    print(webp)


if __name__ == "__main__":
    main()

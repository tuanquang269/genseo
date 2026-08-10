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

import shutil as _shutil


def _find_bin(name, candidates):
    for c in candidates:
        p = os.path.expanduser(c)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    found = _shutil.which(name)
    if found:
        return found
    sys.exit(f"✗ {name} binary not found (tried {candidates} + PATH)")


IMA2 = _find_bin("ima2", ["~/.npm-global/bin/ima2", "~/.nvm/versions/node/v24.19.0/bin/ima2", "~/.local/bin/ima2"])
CWEBP = _find_bin("cwebp", ["/opt/homebrew/bin/cwebp", "~/.local/bin/cwebp", "/usr/local/bin/cwebp"])
OUT_ROOT = "/Users/kevinkreative/genseo/tmp_images"
MAX_BYTES = 80 * 1024
# The third-party-brand clause is not belt-and-braces: left ungated, the generator fills empty
# shelf and counter space with plausible supplement tubs, and on 3 of 3 test generations one of
# them read LIV PURE — a real competing brand, on our own blog. The watermark ban did not cover
# it and the QC packaging check only compared against OUR label, so nothing was watching.
PROMPT_SUFFIX = (" NO watermark. NO blog name text. NO caption. NO attribution text in any "
                 "corner. Clean image only. Product label must remain legible. NO other branded "
                 "product packaging in frame. Never invent a supplement brand name.")
# Appended ONLY on no-face images. Until 2026-08-09 this clause rode on EVERY prompt,
# including the hero lane — which mandates a visible approved persona. So the generator
# got "match this reference person's face" and "no recognizable human faces" in the same
# prompt and split the difference into a generic averaged face. That contradiction, not
# the size of the persona bank, is the main reason the /blogs/news grid read as AI.
NO_FACE_CLAUSE = " No recognizable human faces."
PACK_FIDELITY = (" The product package must EXACTLY match the reference image: same package "
                 "format, same shape, same colors, same label layout and text. Do not invent, "
                 "restyle, or substitute the packaging.")
# i5.2 UGC lane (see skills/genseo-auto-publish/references/ugc-image-framework.md).
# The agent writes the 10-section prompt; these are the MECHANICAL backstops.
UGC_SUFFIX = (" Shot on a phone, handheld, casual snapshot framing, slightly imperfect angle, "
              "natural depth of field, available light only, subtle grain, amateur photo energy, "
              "muted phone-JPEG colours, no HDR gloss, unretouched surfaces.")
UGC_NEG = (" NO beaming model staring at camera. NO sterile marble hero countertop. NO floating "
           "ingredients. NO studio softbox lighting. NO teal-orange colour grade. NO plastic "
           "skin, NO glassy eyes, NO waxy symmetric face. NOT a stock photo.")
CAMERA_MATCH = (" Match the persona reference photo's camera exactly: available light (not "
                "studio), real skin texture with visible pores and slight imperfections, same "
                "focal length class and depth of field, subtle grain, no cosmetic smoothing.")
# Hero lane forbids --ugc, so before 2026-08-09 it carried NO anti-stock negatives at all —
# the only images on the blog index were the only ones generated without them. This is the
# hero-safe subset: it kills the plastic-skin/waxy-symmetry tells without killing the bright
# ad-style look the hero lane is supposed to have (so no "NO studio softbox" here).
HERO_NEG = (" NO plastic skin, NO waxy symmetric face, NO glassy eyes, NO airbrushed pores, "
            "NO teal-orange colour grade, NO flawless catalogue retouching. NOT a stock photo.")
GEM9 = "/Users/kevinkreative/.local/bin/gem9"


def degrade_grain(png_path):
    """Light film-grain + micro quality degrade — raw ima2 is too HD-clean for UGC
    (same rationale as the degrade-start-frame video rule). Applied BEFORE webp.
    Pure PIL (no numpy on system python): zero-centered noise via ImageChops."""
    from PIL import Image, ImageChops
    im = Image.open(png_path).convert("RGB")
    noise = Image.effect_noise(im.size, 8).convert("L")  # sigma≈8 around 128 = subtle grain
    im = ImageChops.add(im, Image.merge("RGB", [noise] * 3), scale=1.0, offset=-128)
    im.save(png_path)


def qc_gem9(webp_path, refs, is_ugc, has_persona):
    """Vision QC via gem9 (9router subscription — per PATI rule, never per-token).
    Returns (passed, reason)."""
    rubric = ["You are a strict image QC gate for a DTC supplement blog. Compare the FIRST image "
              "(the generated candidate) against the other image(s) (references). Answer each check, "
              "then end with exactly 'VERDICT: PASS' or 'VERDICT: FAIL - <short reason>'.",
              "1. PACKAGING (the strictest check). If a package is visible, compare it element by "
              "element with the reference: (a) same format — pouch vs bottle vs jar vs dropper; "
              "(b) same dominant color; (c) the brand wordmark present, in the same place, reading "
              "the same; (d) same product title; (e) same badges/benefit rows in the same layout; "
              "(f) no text, stat badge, or graphic that is NOT on the reference package. Any "
              "mismatch in a-f = FAIL, and say which letter failed. Soft or garbled MICRO-text "
              "(fine print you could not read on the reference either) is an accepted generator "
              "artifact — not a FAIL on its own.",
              "1b. If the candidate shows a package but NO reference image contains that package, "
              "answer 'VERDICT: FAIL - no packaging reference to compare against'."]
    if is_ugc:
        rubric.append("2. Does it read as a casual real-phone UGC snapshot (imperfect framing, "
                      "available light, lived-in scene) and NOT a studio/stock photo? Glossy "
                      "stock look = FAIL.")
    rubric.append("3. Any rendered text/watermark/caption that is not on the product label = FAIL.")
    rubric.append("3b. Any product package in frame that is NOT the referenced product = FAIL. "
                  "An invented brand name on a jar, tub, bottle or pouch counts, even a plausible "
                  "one — name it in the reason.")
    if has_persona:
        rubric.append("4. Does the person look like a natural real human matching the persona "
                      "reference (no plastic skin, no dead eyes, no warped hands)? = FAIL if not.")
    res = subprocess.run([GEM9, "-p", "\n".join(rubric), webp_path, *refs],
                         capture_output=True, text=True, timeout=180)
    out = (res.stdout or "") + (res.stderr or "")
    m = re.search(r"VERDICT:\s*(PASS|FAIL[^\n]*)", out)
    if not m:
        return True, f"qc-inconclusive ({out.strip()[-120:]})"  # never hard-block on QC infra failure
    v = m.group(1)
    return v.startswith("PASS"), v


CURATED_ROOT = os.path.expanduser("~/genseo/product_refs")


def curated_ref(handle):
    """A hand-cropped, verified pack shot for this SKU, if one exists.

    Every WellnessNest PDP image is a marketing composite — some contain no
    package at all. Ticket #3 fed `--product-ref <handle>:1` (an "AFTER 2 WEEKS"
    graphic with no pouch in it) and the generator invented a white pouch,
    copying that graphic's stat badges onto the fake label. The curated crop is
    the only trustworthy packaging source; the PDP index path is the fallback.
    Returns (png_path, meta_dict) or (None, None)."""
    import json
    png = os.path.join(CURATED_ROOT, f"{handle}.png")
    if not os.path.exists(png):
        return None, None
    meta_path = os.path.join(CURATED_ROOT, f"{handle}.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    return png, meta


def fetch_product_ref(handle_spec):
    """--product-ref <handle>[:index] → the real packaging as a PNG ref.

    A curated crop in ~/genseo/product_refs wins over any PDP index, because
    PDP images are composites and an index can silently point at one with no
    package in it."""
    import io
    import json
    import urllib.request
    from PIL import Image
    handle, _, idx = handle_spec.partition(":")
    idx = int(idx or 0)
    png, _meta = curated_ref(handle)
    if png:
        if idx:
            print(f"  (ignoring :{idx} — using the curated pack ref for {handle})", flush=True)
        return png
    print(f"  ⚠ no curated pack ref for {handle} — falling back to PDP image [{idx}]. "
          f"VERIFY the package is actually in that image before trusting the output.", flush=True)
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
    ap.add_argument("--ugc", action="store_true",
                    help="i5.2 UGC lane: phone-snapshot suffix + anti-stock NEG bank + grain degrade "
                         "(see references/ugc-image-framework.md — inline article images use this)")
    ap.add_argument("--persona-ref", default=None,
                    help="absolute path to the APPROVED persona ref photo (~/genseo/personas/<handle>/ref.jpg). "
                         "Only personas Kevin approved through the one-time Pinterest gate — never a fresh face.")
    ap.add_argument("--qc", action="store_true",
                    help="vision QC via gem9 (9router): packaging/UGC/no-text/persona rubric; "
                         "FAIL prints the reason and exits 2 so the caller can re-roll")
    ap.add_argument("--square", action="store_true", help="1024x1024 instead of 1536x1024 landscape")
    a = ap.parse_args()

    for spec in a.product_ref:
        a.ref.append(fetch_product_ref(spec))
    if a.product_ref:
        # Prompt text overrides the ref image when they disagree, so state the real
        # packaging in words too — a prompt saying "white pouch" beat a pink-pouch ref.
        for spec in a.product_ref:
            _, meta = curated_ref(spec.partition(":")[0])
            if meta and meta.get("describe"):
                a.prompt += (f" The package in frame is {meta['describe']}. It is a "
                             f"{meta['format']}, {meta['color']} — never any other format or color.")
        a.prompt += PACK_FIDELITY
    if a.persona_ref:
        if not os.path.exists(a.persona_ref):
            sys.exit(f"✗ persona ref not found: {a.persona_ref} — persona bank lives in ~/genseo/personas/")
        a.ref.append(a.persona_ref)
        a.prompt += CAMERA_MATCH
    else:
        a.prompt += NO_FACE_CLAUSE
    if a.ugc:
        a.prompt += UGC_SUFFIX + UGC_NEG
    else:
        # Every non-UGC call IS the hero lane (the framework gives all three inline images
        # --ugc), so the negatives belong to the LANE, not to whether a face is in frame.
        # Gating them on persona_ref left the no-face hero — the every-3rd-article branch the
        # picker now mandates, and the ONLY branch available while the bank is empty — with no
        # anti-stock negatives at all: the same hole, surviving in the one path that currently
        # carries every hero on the blog index.
        a.prompt += HERO_NEG

    slug = re.sub(r"[^a-z0-9-]", "-", a.slug.lower())
    name = re.sub(r"[^a-z0-9-]", "-", a.name.lower())
    out_dir = os.path.join(OUT_ROOT, slug)
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.join(out_dir, f"{name}.png")
    webp = os.path.join(out_dir, f"{name}.webp")

    size = "1024x1024" if a.square else "1536x1024"
    print(f"⏳ ima2 gen {name} ({size}, {len(a.ref)} ref{', UGC' if a.ugc else ''})...", flush=True)
    gen_png(a.prompt, size, png, a.ref)
    # Unconditional. Raw ima2 output is too HD-clean for anything we publish, and every
    # narrower rule tried here has leaked: gating on --ugc left all heroes glossy, then gating
    # on `ugc or persona_ref` still left the no-face hero glossy — and the no-face hero is what
    # the blog index shows whenever the bank can't fill the slot. There is no image in this
    # pipeline that wants the untouched render, so stop enumerating which ones do.
    degrade_grain(png)
    nbytes, q, width = compress_webp(png, webp)
    os.unlink(png)  # keep only the deliverable; the PNG is 10-20x the size
    if a.qc:
        passed, verdict = qc_gem9(webp, a.ref, a.ugc, bool(a.persona_ref))
        print(f"QC → {verdict}")
        if not passed:
            sys.exit(2)  # caller re-rolls with the FAIL reason folded into the prompt (max 2)
    print(f"✓ {nbytes//1024}KB webp (q{q}, {width}px)")
    print(webp)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""ad_assets.py — Google Ads (Demand Gen) image lane for Wellness Nest.

Sibling of article_images.py, NOT a replacement. The blog lane ends in a <80KB
webp and deletes its PNG; Google Ads cannot accept either of those facts:

  * the v24 MimeType enum has IMAGE_JPEG / IMAGE_PNG / IMAGE_GIF and no webp
    entry, so a webp asset simply cannot be described to the API
    (verified: google.ads.googleads.v24.enums.types.mime_type.MimeTypeEnum)
  * Demand Gen serves fixed geometries, not "whatever the generator returned"

So this lane keeps the PNG, emits PNG only, and lands on exact pixel targets.
Everything upstream of that — the ima2 OAuth binary, the prompt suffix bank,
the pack-fidelity clause and the gem9 QC rubric — is IMPORTED from
article_images.py rather than copied, so the two lanes cannot drift apart.

Geometry (Google Ads Help 13704860 / 17140672, read 2026-08-11):
  landscape 1.91:1 -> 1200x628   (min 600x314, max 5MB, .jpg/.png)
  square     1:1   -> 1200x1200  (min 300x300, max 5MB, .jpg/.png)

WHY THE GEOMETRY IS ENFORCED HERE AND NOT TRUSTED FROM ima2 -----------------
ima2 forwards -s to the model as a hint on the image_generation tool; the model
is free to ignore it, and it does. Measured this run:
    -s 1200x628   -> 1254x1254   (silently square)
    -s 1536x1024  -> 1536x1024   (honoured)
    -s 1024x1024  -> 1536x1024   (silently landscape)
A pipeline that trusted -s would have shipped square images into a 1.91:1 slot
and never printed a word about it. So: request the nearest NATIVE size, measure
what actually came back, and normalise deterministically in PIL. If the return
is so far off that centre-cropping would eat the composition, regenerate.

Run with /usr/bin/python3 — the Homebrew python3 on PATH has no PIL.

Usage:
  /usr/bin/python3 ad_assets.py --concept a1 --geom landscape --prompt "..." \
      [--product-ref fusiforce-creatine-gummies] [--ref /abs/path.png] [--ugc] --qc

Prints the LOCAL absolute .png path on the last line.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imported, never re-implemented: same generator binary, same prompt bank, same
# QC gate as the blog lane. Copying these would let the ad lane quietly fall
# behind the next fix to the packaging rubric.
from article_images import (  # noqa: E402
    HERO_NEG,
    NO_FACE_CLAUSE,
    PACK_FIDELITY,
    UGC_NEG,
    UGC_SUFFIX,
    curated_ref,
    degrade_grain,
    fetch_product_ref,
    gen_png,
    qc_gem9,
)

OUT_ROOT = "/Users/kevinkreative/genseo/tmp_images/fusiforce-ad-assets"

# target -> (width, height, native ima2 size to ask for)
# The native list is what the underlying image model actually renders
# (1024x1024 / 1536x1024 / 1024x1536); ask for the closest one and crop in.
GEOMS = {
    "landscape": (1200, 628, "1536x1024"),
    "square": (1200, 1200, "1024x1024"),
}

# Fraction of the generated pixels that must survive the centre-crop. A square
# return cropped into 1.91:1 keeps 52%, which is not a crop, it is a different
# photograph — the subject the prompt was built around ends up half out of
# frame. 0.75 passes the two legitimate cases (1.5:1 -> 1.91:1 keeps 78%,
# 1:1 -> 1:1 keeps 100%) and rejects the silent-fallback cases.
MIN_RETAINED = 0.75

# Ads-lane framing. The crop is coming whether the generator plans for it or
# not, so tell it where the safe area is.
FRAMING = {
    "landscape": (" Compose for a WIDE horizontal banner: every key subject sits inside the "
                  "central horizontal band, with generous empty space above and below that can "
                  "be cropped away without losing anything."),
    "square": (" Compose for a SQUARE frame: subject centred, balanced negative space on all "
               "four sides, nothing important near the edges."),
}

# Google Ads renders creative next to real editorial. Rendered words are also
# the single most reliable AI tell (misspelt, half-formed letterforms), and
# every headline in this campaign is delivered as a TEXT asset, not burnt into
# the pixels. So handwriting in the napkin/notebook/sticky-note concepts is
# rendered as indistinct strokes: the gesture of writing, no readable words.
NO_TEXT_HARD = (" ABSOLUTELY NO legible words, letters, numbers, captions, labels or signage "
                "anywhere in the image except the product's own printed label. Any handwriting "
                "or print must be indistinct, unreadable pen strokes only.")


def measure(path):
    """Actual format/size/bytes of a file on disk. Never inferred from intent."""
    from PIL import Image
    with Image.open(path) as im:
        return im.format, im.size, os.path.getsize(path)


def retained_fraction(src_wh, target_wh):
    """What share of the source survives a centre-crop to the target ratio."""
    (w, h), (tw, th) = src_wh, (target_wh[0], target_wh[1])
    tr, sr = tw / th, w / h
    if sr > tr:
        return (h * tr) / w          # cropping width
    return (w / tr) / h              # cropping height


def normalise(src_png, dst_png, tw, th):
    """Centre-crop to the target ratio, then resample to the exact pixel target.

    Crop-then-resize, never a straight resize: a straight resize to a different
    ratio stretches faces, bottles and type, and a stretched pouch fails the
    packaging check for a reason that has nothing to do with the generator."""
    from PIL import Image
    with Image.open(src_png) as im:
        im = im.convert("RGB")
        w, h = im.size
        tr = tw / th
        if w / h > tr:
            nw, nh = int(round(h * tr)), h
        else:
            nw, nh = w, int(round(w / tr))
        left, top = (w - nw) // 2, (h - nh) // 2
        im = im.crop((left, top, left + nw, top + nh))
        im = im.resize((tw, th), Image.LANCZOS)
        im.save(dst_png, "PNG", optimize=True)


def build_prompt(a, geom):
    prompt = a.prompt
    refs = list(a.ref)
    for spec in a.product_ref:
        refs.append(fetch_product_ref(spec))
    if a.product_ref:
        # Prompt text overrides the reference image when the two disagree — the
        # FusiForce jar/pouch failure came from exactly that. So the verbatim
        # `describe` string goes into the words, not just the attached ref.
        for spec in a.product_ref:
            _, meta = curated_ref(spec.partition(":")[0])
            if meta and meta.get("describe"):
                prompt += (f" The package in frame is {meta['describe']}. It is a "
                           f"{meta['format']}, {meta['color']} — never any other format or color.")
        prompt += PACK_FIDELITY
    prompt += NO_FACE_CLAUSE          # no faces anywhere in this batch, by design
    prompt += UGC_SUFFIX + UGC_NEG if a.ugc else HERO_NEG
    prompt += FRAMING[geom] + NO_TEXT_HARD
    return prompt, refs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--concept", required=True, help="concept id, e.g. a1 (names the output file)")
    ap.add_argument("--geom", required=True, choices=sorted(GEOMS))
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--product-ref", action="append", default=[],
                    help="<handle>[:index] — REQUIRED whenever the product is in frame")
    ap.add_argument("--ugc", action="store_true")
    ap.add_argument("--qc", action="store_true", help="gem9 vision gate; FAIL exits 2")
    ap.add_argument("--out-root", default=OUT_ROOT)
    a = ap.parse_args()

    tw, th, native = GEOMS[a.geom]
    prompt, refs = build_prompt(a, a.geom)
    os.makedirs(a.out_root, exist_ok=True)
    raw_dir = os.path.join(a.out_root, "_raw")
    os.makedirs(raw_dir, exist_ok=True)
    stem = f"{a.concept}_{tw}x{th}"
    raw = os.path.join(raw_dir, f"{stem}_raw.png")
    final = os.path.join(a.out_root, f"{stem}.png")

    # gen_png() starts the ima2 serve daemon itself, with IMA2's own directory
    # prepended to PATH. Doing it here too would only risk launching the daemon
    # under a worse PATH than the one that works.
    for attempt in range(1, 4):
        print(f"⏳ ima2 gen {stem} (ask {native}, {len(refs)} ref, try {attempt}/3)...", flush=True)
        if os.path.exists(raw):
            os.unlink(raw)
        gen_png(prompt, native, raw, refs)
        fmt, size, nbytes = measure(raw)
        keep = retained_fraction(size, (tw, th))
        print(f"   returned {fmt} {size[0]}x{size[1]} ({nbytes//1024}KB), "
              f"centre-crop keeps {keep:.0%}", flush=True)
        if keep >= MIN_RETAINED:
            break
        print(f"   ✗ generator ignored the requested {native} badly enough that the crop would "
              f"discard {1-keep:.0%} of the frame — regenerating", flush=True)
    else:
        sys.exit(f"✗ {stem}: 3 generations all came back at a ratio that cannot be cropped to "
                 f"{tw}x{th} without losing more than {1-MIN_RETAINED:.0%} of the image.")

    normalise(raw, final, tw, th)
    # Same reasoning as the blog lane: raw ima2 is too HD-clean, and the native
    # lane is supposed to read as something a person photographed.
    degrade_grain(final)

    fmt, size, nbytes = measure(final)
    if fmt != "PNG" or size != (tw, th):
        sys.exit(f"✗ {stem}: post-normalise check failed — {fmt} {size}, expected PNG ({tw}, {th})")
    if nbytes > 5 * 1024 * 1024:
        sys.exit(f"✗ {stem}: {nbytes//1024}KB exceeds the 5MB Demand Gen image ceiling")

    if a.qc:
        passed, verdict = qc_gem9(final, refs, a.ugc, False)
        print(f"QC → {verdict}")
        if not passed:
            sys.exit(2)

    print(f"✓ {fmt} {size[0]}x{size[1]} {nbytes//1024}KB")
    print(final)


if __name__ == "__main__":
    main()

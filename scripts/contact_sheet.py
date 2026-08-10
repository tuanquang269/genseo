#!/usr/bin/env python3
"""Build a contact sheet of the persona bank so the faces can be QC'd by eye.

The machine gates in fetch_personas.py are good at what they measure — licence, resolution,
burned-in text, dHash duplicates, and a vision rubric that reads age, gender, ethnicity and
occlusion. What they cannot measure is the thing a bank of advertising faces is actually for:
whether the photograph reads as a person you would believe in a supplement ad. That judgement
needs a human (or at minimum a pair of eyes) looking at the pictures, which means the pictures
have to be lookable-at — two hundred separate file opens is not a review, it is a chore that
gets skipped.

Two framings, because they catch different faults:

  --frame head   crops to the head region, derived from the MIAP person box that Open Images
                 already ships. This is the framing for identity questions: is this the age
                 band we asked for, does the face read the way the rubric said, are two of
                 these obviously the same person.

  --frame full   the whole photograph, letterboxed. This is the framing for context questions:
                 a second person half out of frame, a logo on a shirt, a setting that would be
                 absurd behind a supplement claim. The gates screen some of this; they do not
                 screen taste.

Sheets are written per rotation pool by default, because the pool is the unit the picker
actually rotates over — reviewing a pool tells you what a reader of one brand's articles will
see over the next ten posts, which is the question that matters.
"""
import argparse
import gzip
import json
import os
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont

BASE = "/Users/kevinkreative/genseo/personas"
INDEX = os.path.join(BASE, "index.json")
TAXONOMY = os.path.join(BASE, "taxonomy.json")
CANDIDATES = os.path.join(BASE, "_openimages", "candidates.json.gz")
OUT_DIR = os.path.join(BASE, "_contact-sheets")

TILE = 420                 # big enough that a face inside a head crop is genuinely legible
CAPTION_H = 74             # three lines of 11px text plus padding
COLS = 5                   # 5 x 420 = 2100px wide; fits a screen without horizontal scrolling
PAD = 8
BG = (24, 24, 27)
FG = (235, 235, 238)
DIM = (150, 150, 158)
STATUS_COLOR = {"active": (74, 222, 128), "pending": (250, 204, 21),
                "flagged": (248, 113, 113), "retired": (113, 113, 122)}


def _font(size, bold=False):
    """A real font if the system has one, else PIL's bitmap default.

    Falling back rather than raising matters: a contact sheet with ugly captions is still a
    contact sheet, and this script exists to get eyes onto faces.
    """
    for path in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
                 else "/System/Library/Fonts/Supplemental/Arial.ttf",
                 "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def load_boxes():
    """image_id -> MIAP person box, for head cropping.

    Open Images boxes every person in the photograph with a normalised [XMin, XMax, YMin, YMax].
    That is a PERSON box, not a face box, but the top of a standing human is reliably their
    head, so the top slice of the box is a usable face crop without adding a face detector (and
    without another vision call per persona, which at ~16s each would cost an hour for the bank).

    An image with several boxes keeps the largest: the bank only accepts person_count == 1, so
    the largest box is the subject and any others are the crowd behind them.
    """
    if not os.path.exists(CANDIDATES):
        return {}
    with gzip.open(CANDIDATES, "rt") as fh:
        recs = json.load(fh)
    boxes = {}
    for r in recs:
        box = r.get("box")
        iid = r.get("image_id")
        if not box or not iid:
            continue
        # build_index.py writes [XMin, YMin, XMax, YMax] — NOT the MIAP CSV's own column order,
        # which is XMin, XMax, YMin, YMax. Reading it in CSV order produces boxes like
        # x 0.000-0.013 (a person 1% of the frame wide) and inverted y ranges, and the crops
        # come out as asphalt and blurred walls. Checked against the builder, not assumed.
        area = (box[2] - box[0]) * (box[3] - box[1])
        if iid not in boxes or area > boxes[iid][0]:
            boxes[iid] = (area, box)
    return {k: v[1] for k, v in boxes.items()}


def head_crop(img, box):
    """A square head-and-shoulders crop from a normalised MIAP person box [x0, y0, x1, y1].

    A fixed fraction of the box height cannot work, because the boxes are not a consistent
    framing: some are a standing figure across the whole frame, some are a chest-up portrait
    that already fills it. Scale from the box WIDTH instead, which is much more stable — an
    adult's shoulders-and-arms span is roughly 2.2 head-widths whatever the shot, and a head is
    about 1.3 times as tall as it is wide, so head height lands near 0.6 of the box width.

    Clamped at both ends: never less than 12% of the box height (a wide box of someone lying
    down or arms outstretched would otherwise crop to a postage stamp) and never more than 85%
    (a box that IS a face should not crop tighter than the face).
    """
    w, h = img.size
    x0, y0, x1, y1 = box[0] * w, box[1] * h, box[2] * w, box[3] * h
    bw, bh = max(1.0, x1 - x0), max(1.0, y1 - y0)
    head = min(max(bw * 0.62, bh * 0.12), bh * 0.85)
    side = min(head * 1.9, float(min(w, h)))    # head plus shoulders, and never bigger than the frame
    cx = (x0 + x1) / 2.0
    cy = y0 + head * 0.55                       # centre just below the crown, not on the box top
    # Slide (do not shrink) a crop that runs off an edge: shrinking would change this tile's
    # scale relative to every other tile, and a grid at inconsistent scale is hard to read.
    left = min(max(0.0, cx - side / 2), max(0.0, w - side))
    top = min(max(0.0, cy - side / 2), max(0.0, h - side))
    return img.crop((int(left), int(top), int(left + side), int(top + side)))


def fit_square(img, size):
    """Letterbox into a square without distorting. Faces are the subject; stretching them lies."""
    img = img.copy()
    img.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("RGB", (size, size), (16, 16, 18))
    canvas.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
    return canvas


def tile_for(handle, doc, row, box, frame):
    """One captioned tile: the picture, then who it is and what the machine said about it."""
    ref = os.path.join(BASE, handle, "ref.jpg")
    canvas = Image.new("RGB", (TILE, TILE + CAPTION_H), BG)
    try:
        img = Image.open(ref).convert("RGB")
        if frame == "head" and box:
            img = head_crop(img, box)
        canvas.paste(fit_square(img, TILE), (0, 0))
    except Exception as exc:                                        # noqa: BLE001
        d = ImageDraw.Draw(canvas)
        d.rectangle([0, 0, TILE, TILE], fill=(60, 20, 20))
        d.text((12, TILE // 2), "unreadable:\n%s" % textwrap.shorten(str(exc), 60),
               font=_font(13), fill=FG)

    d = ImageDraw.Draw(canvas)
    status = (row or {}).get("status", "NO INDEX ROW")
    v = (doc.get("qc") or {}).get("vision") or {}
    src = doc.get("source") or {}
    age = ("~%s-%s" % (v.get("apparent_age_min"), v.get("apparent_age_max"))
           if v.get("apparent_age_min") is not None else "age ?")
    y = TILE + 5
    d.text((PAD, y), handle, font=_font(16, bold=True), fill=FG)
    sw = d.textlength(handle, font=_font(16, bold=True))
    d.text((PAD + sw + 10, y + 3), status.upper(), font=_font(12, bold=True),
           fill=STATUS_COLOR.get(status, (248, 113, 113)))
    d.text((PAD, y + 22), "%s  %s  reads %s" % (doc.get("cell_id", "?"), age,
                                                v.get("ethnicity_group", "?")),
           font=_font(12), fill=DIM)
    # studio_or_press_context is recorded by the rubric and deliberately NOT enforced there —
    # it is taste, and the thin cells have no headroom for a fourth gate. This caption is where
    # it becomes actionable, which is the whole reason it is worth recording at all. The head
    # angle rides along because a ref that is already a profile is the one thing that makes the
    # 21-angle rule unsatisfiable, and it is easy to miss in a 420px tile.
    flags = []
    if v.get("studio_or_press_context") is True:
        flags.append("STUDIO/PRESS")
    if v.get("face_angle_reads"):
        flags.append(str(v["face_angle_reads"]))
    if flags:
        d.text((PAD + 250, y + 22), " · ".join(flags), font=_font(12, bold=True),
               fill=(251, 146, 60))
    d.text((PAD, y + 40), textwrap.shorten("© %s · %s" % (src.get("author", "?"),
                                                          src.get("license", "?")), 52),
           font=_font(11), fill=DIM)
    return canvas


def build_sheet(handles, index, boxes, title, frame, out_path):
    rows = index.get("personas") or {}
    tiles = []
    for h in handles:
        try:
            doc = json.load(open(os.path.join(BASE, h, "persona.json")))
        except (OSError, ValueError):
            doc = {}
        iid = ((doc.get("source") or {}).get("photo_id"))
        tiles.append(tile_for(h, doc, rows.get(h), boxes.get(iid), frame))
    if not tiles:
        return None
    n_rows = (len(tiles) + COLS - 1) // COLS
    header = 46
    sheet = Image.new("RGB", (COLS * (TILE + PAD) + PAD,
                              header + n_rows * (TILE + CAPTION_H + PAD) + PAD), BG)
    d = ImageDraw.Draw(sheet)
    d.text((PAD + 4, 12), title, font=_font(22, bold=True), fill=FG)
    for i, t in enumerate(tiles):
        x = PAD + (i % COLS) * (TILE + PAD)
        y = header + (i // COLS) * (TILE + CAPTION_H + PAD)
        sheet.paste(t, (x, y))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sheet.save(out_path, quality=88, optimize=True)
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pool", help="one rotation pool, e.g. f4049")
    ap.add_argument("--cell", help="one taxonomy cell, e.g. f4049-hl")
    ap.add_argument("--all", action="store_true", help="one sheet per rotation pool")
    ap.add_argument("--frame", choices=("head", "full"), default="head")
    ap.add_argument("--status", default="", help="comma-separated filter, e.g. pending")
    ap.add_argument("--out-dir", default=OUT_DIR)
    args = ap.parse_args()

    index = json.load(open(INDEX))
    boxes = load_boxes()
    want = {s.strip() for s in args.status.split(",") if s.strip()}

    # The DIRECTORY is the bank — the same reason fetch_personas.load_bank() walks directories.
    # A persona stranded on disk without an index row is exactly the thing a review should be
    # able to see, so filtering by the index here would hide the faults worth finding.
    handles = sorted(h for h in os.listdir(BASE)
                     if not h.startswith("_")
                     and os.path.exists(os.path.join(BASE, h, "ref.jpg")))
    docs = {}
    for h in handles:
        try:
            docs[h] = json.load(open(os.path.join(BASE, h, "persona.json")))
        except (OSError, ValueError):
            docs[h] = {}
    if want:
        rows = index.get("personas") or {}
        handles = [h for h in handles if (rows.get(h) or {}).get("status") in want]

    groups = {}
    if args.cell:
        groups[args.cell] = [h for h in handles if docs[h].get("cell_id") == args.cell]
    elif args.pool:
        groups[args.pool] = [h for h in handles if docs[h].get("pool_id") == args.pool]
    elif args.all:
        for h in handles:
            groups.setdefault(docs[h].get("pool_id") or "no-pool", []).append(h)
    else:
        groups["bank"] = handles

    written = []
    for key in sorted(groups):
        hs = groups[key]
        if not hs:
            print("· %s — nothing to show" % key)
            continue
        title = "%s — %d face(s)%s · frame=%s" % (key, len(hs),
                                                  (" · status " + ",".join(sorted(want))) if want
                                                  else "", args.frame)
        path = os.path.join(args.out_dir, "%s-%s.jpg" % (key, args.frame))
        out = build_sheet(hs, index, boxes, title, args.frame, path)
        if out:
            written.append(out)
            print("✓ %-10s %2d face(s) → %s" % (key, len(hs), out))
    if not written:
        sys.exit("nothing written")


if __name__ == "__main__":
    main()

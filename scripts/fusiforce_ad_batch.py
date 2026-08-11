#!/usr/bin/env python3
"""fusiforce_ad_batch.py — drive ad_assets.py over the 10 FusiForce DG concepts.

Concepts are from native-image-concept-brief.md (A1-A5 comparison, B1-B5 women 40+).
Strictly sequential: there is ONE `ima2 serve` daemon holding one OAuth session,
so two generations at once would fight over it.

Every concept is generated at BOTH Demand Gen geometries:
  landscape 1200x628 (1.91:1) and square 1200x1200 (1:1).

Run:  /usr/bin/python3 fusiforce_ad_batch.py [--only a1,b5] [--geom landscape]
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
AD_ASSETS = os.path.join(HERE, "ad_assets.py")
PY = "/usr/bin/python3"
LOG = "/Users/kevinkreative/genseo/tmp_images/fusiforce-ad-assets/_batch_log.json"
PACK = "fusiforce-creatine-gummies"

# ugc=True is the phone-snapshot lane (imperfect framing, available light, grain).
# The two pack-forward concepts (a5/b5) are the hero lane, matching how the two
# already-approved heroes were made.
CONCEPTS = {
    "a1": dict(ugc=True, pack=False, prompt=(
        "Overhead phone snapshot looking straight down at a real kitchen counter. A half-drunk "
        "glass of water sits on the counter with a distinct ring of chalky white sediment settled "
        "at the bottom of the glass, undissolved and gritty. Beside the glass lie three "
        "green-apple coloured gummies. Everyday worn counter surface, a few crumbs, natural "
        "window light from one side. No packaging of any kind in frame, no containers, no tubs, "
        "no bottles.")),
    "a2": dict(ugc=True, pack=False, prompt=(
        "A slightly creased paper napkin lying on a wooden cafe table, photographed from above at "
        "a casual angle. On the napkin someone has drawn a quick two-column comparison in blue "
        "ballpoint: a rough sketch of a scoop on the left, a rough sketch of a small chewable "
        "square on the right, with tick and cross marks down each column in the same hand, and one "
        "item loosely circled. A faint brown coffee ring stains one corner. The ink bleeds very "
        "slightly into the napkin fibres. Shot on a table in available light, not scanned. The "
        "marks read as handwriting from a distance but no letter or word is actually formed.")),
    "a3": dict(ugc=True, pack=False, prompt=(
        "A plain unbranded plastic shaker bottle lying on its side in a stainless steel kitchen "
        "sink, lid off beside it, dried chalky white powder residue crusted on the inside wall and "
        "around the rim. Hard morning light through a window above the sink. A few water droplets "
        "in the basin. Completely blank bottle with no label, no logo, no printing, no brand name "
        "anywhere on it. Nothing staged, nothing branded, real domestic kitchen.")),
    "a4": dict(ugc=True, pack=True, prompt=(
        "An open carry-on suitcase on a made bed, packed with real creased clothes and a toiletry "
        "bag. A large completely blank white plastic supplement tub sits awkwardly on top of the "
        "clothes, plainly too bulky to fit — the lid pushes above the rim of the case. Tucked flat "
        "beside the toiletry bag, fitting easily, is the product pouch. The white tub is entirely "
        "unlabelled: no printing, no logo, no brand name, no text of any kind on it. Warm bedroom "
        "light, handheld phone snapshot.")),
    "a5": dict(ugc=False, pack=True, prompt=(
        "A dark stone kitchen counter in real window light. On the left stands the product pouch, "
        "upright and facing the camera. On the right sits a stainless steel scoop heaped with "
        "chalky white powder, and beside it a glass of water with visible undissolved white "
        "sediment settled at the bottom. Clean editorial product photography, natural side light, "
        "soft shadows on the stone.")),
    "b1": dict(ugc=True, pack=False, prompt=(
        "A quiet corner of a home living room used for training. Two light hex dumbbells rest on a "
        "slightly worn exercise mat on a wood floor, the mat edge curling up a little from use. "
        "Soft morning light across the floor from a nearby window. Nobody in frame, no person, no "
        "hands. Lived-in domestic room, a skirting board and a bit of wall visible. Not a gym, not "
        "a fitness advertisement.")),
    "b2": dict(ugc=True, pack=False, prompt=(
        "A spiral-bound notebook lying open on a kitchen table, photographed from above at a "
        "slight angle. The open page holds a handwritten training log in blue ink: rows of short "
        "entries, several struck through with a single line, and a large question mark in the "
        "margin. A pair of reading glasses rests at the edge of the frame, and a mug sits just out "
        "of focus behind. Warm afternoon kitchen light. The writing reads as real handwriting from "
        "a distance but no letter, word or number is actually formed — only indistinct pen "
        "strokes.")),
    "b3": dict(ugc=True, pack=False, prompt=(
        "Looking up a domestic wooden staircase from the bottom step. A woman's hand rests on the "
        "banister rail in the lower part of the frame — the hand and a little of the forearm only, "
        "no person visible, no face, no body. Warm afternoon light falling down the stairwell onto "
        "the carpet runner. Ordinary family home, a little wear on the treads.")),
    "b4": dict(ugc=True, pack=False, prompt=(
        "A yellow square sticky note stuck on a bathroom mirror, photographed slightly off-centre "
        "with a phone. Three short handwritten lines on the note in blue ink, the bottom line "
        "underlined twice. The mirror reflects an ordinary bathroom behind — tiles, a towel on a "
        "rail — with no person and no reflection of a camera or phone anywhere. Soft daylight. The "
        "note reads as handwriting from a distance but no letter or word is actually formed.")),
    "b5": dict(ugc=False, pack=True, prompt=(
        "A wooden gym bench in a bright home training space. The product pouch stands upright on "
        "the bench, facing the camera. Beside it lie a tightly rolled exercise mat, two small hex "
        "dumbbells, a plain unbranded stainless water bottle, and a neatly folded towel. Natural "
        "daylight from a large window, soft shadows on the wood. No people, no hands.")),
}


def run(cid, geom, spec, extra_clause=""):
    cmd = [PY, AD_ASSETS, "--concept", cid, "--geom", geom,
           "--prompt", spec["prompt"] + extra_clause, "--qc"]
    if spec["ugc"]:
        cmd.append("--ugc")
    if spec["pack"]:
        cmd += ["--product-ref", PACK]
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    out = (p.stdout or "") + (p.stderr or "")
    verdict = next((ln for ln in out.splitlines() if ln.startswith("QC →")), "")
    print(f"[{cid} {geom}] rc={p.returncode} {time.time()-t0:.0f}s {verdict}", flush=True)
    if p.returncode != 0:
        print("   " + " | ".join(out.strip().splitlines()[-4:]), flush=True)
    return dict(concept=cid, geom=geom, rc=p.returncode, verdict=verdict,
                tail=out.strip().splitlines()[-6:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma-separated concept ids")
    ap.add_argument("--geom", default="landscape,square")
    a = ap.parse_args()
    ids = [c.strip() for c in a.only.split(",") if c.strip()] or list(CONCEPTS)
    geoms = [g.strip() for g in a.geom.split(",") if g.strip()]

    results = []
    if os.path.exists(LOG):
        results = json.load(open(LOG))
    for cid in ids:
        if cid not in CONCEPTS:
            sys.exit(f"unknown concept {cid}")
        for geom in geoms:
            results = [r for r in results
                       if not (r["concept"] == cid and r["geom"] == geom)]
            results.append(run(cid, geom, CONCEPTS[cid]))
            os.makedirs(os.path.dirname(LOG), exist_ok=True)
            json.dump(results, open(LOG, "w"), indent=1)
    ok = sum(1 for r in results if r["rc"] == 0)
    print(f"\n== {ok}/{len(results)} passed ==")


if __name__ == "__main__":
    main()

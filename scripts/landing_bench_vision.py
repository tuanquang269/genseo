#!/usr/bin/env python3
"""Blind VISUAL A/B judge for landing pages: vision models SEE the screenshots (not text).

  /usr/bin/python3 scripts/landing_bench_vision.py state/bench/live state/bench/v3-r2 --label r2 [--calls 4]

Inputs are prefixes written by landing_bench_extract.mjs (<prefix>-desktop.png 1440 wide, <prefix>-mobile.png 375).
Per call the two pages are randomly assigned to A/B and sent as 3 images (under the ~300 KB 9router tunnel cap):
  1. above-the-fold, desktop + mobile, A | B (higher resolution)   2. full desktop page, A | B
  3. full mobile page in 3 columns, A | B
Judges = the gem9 ladder used by article_images.py QC (9router subscription, $0 per call), alternated per call
so two different vision models vote. Scores 1-10 on 7 criteria; results are de-randomised, averaged and written to
state/bench/vision-scores.json. Criteria: visual_polish, product_imagery, ui_hierarchy, mobile_ux,
premium_brand_feel, image_consistency, cta_offer_design.
"""
import json, os, random, re, subprocess, sys, tempfile, time
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEM9 = os.path.expanduser("~/.local/bin/gem9")
JUDGES = ["ag/gemini-3.1-pro-low", "cx/gpt-5.6-luna"]
CRIT = ["visual_polish", "product_imagery", "ui_hierarchy", "mobile_ux", "premium_brand_feel", "image_consistency", "cta_offer_design"]
PROMPT = """You are a senior DTC e-commerce art director judging two landing pages, A and B, for a supplement brand.
You get 3 images: (1) the first screen of each page (desktop left, mobile right) with A on the left half and B on the
right half; (2) the full desktop page of A (left) and B (right); (3) the full mobile page of A (left block, read the 3
columns top-to-bottom left-to-right) and B (right block, same).
Judge ONLY what you SEE (layout, imagery, typography, spacing, colour, components). Ignore which product it is and
ignore copy quality. Be strict and specific; a 10 is reserved for world-class work.
Score each page 1-10 on:
- visual_polish: craft, spacing rhythm, alignment, finish
- product_imagery: quality, lighting, styling and believability of product photos (bottle/pack shots)
- ui_hierarchy: clarity of headline, sections, number badges, charts/stat cards, scannability
- mobile_ux: mobile readability, spacing, tap targets, CTA visibility
- premium_brand_feel: does it feel like a premium DTC brand rather than a template
- image_consistency: one coherent art direction across all images (palette, light, mood)
- cta_offer_design: offer box, price presentation, CTA buttons, guarantee/trust elements
Reply with ONLY this JSON, no prose before it:
{"A":{"visual_polish":n,"product_imagery":n,"ui_hierarchy":n,"mobile_ux":n,"premium_brand_feel":n,"image_consistency":n,"cta_offer_design":n},
 "B":{...same keys...},"notes_A":"<=25 words, weakest visual issue","notes_B":"<=25 words, weakest visual issue"}"""


def label(im, text):
    d = ImageDraw.Draw(im); d.rectangle((0, 0, 44, 30), fill=(0, 0, 0)); d.text((14, 8), text, fill=(255, 255, 255))
    return im


def side(a, b, gap=16):
    h = max(a.height, b.height); m = Image.new("RGB", (a.width + b.width + gap, h), (255, 255, 255))
    m.paste(a, (0, 0)); m.paste(b, (a.width + gap, 0)); return m


def fold(prefix):
    d = Image.open(prefix + "-desktop.png").convert("RGB"); d = d.crop((0, 0, d.width, round(d.width * 900 / 1440))).resize((560, 350), Image.LANCZOS)
    m = Image.open(prefix + "-mobile.png").convert("RGB"); m = m.crop((0, 0, m.width, round(m.width * 812 / 375))).resize((162, 350), Image.LANCZOS)   # dpr-aware (storefront shots are 2x)
    return side(d, m, 8)


def full_d(prefix, w=380):
    im = Image.open(prefix + "-desktop.png").convert("RGB"); return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)


def full_m(prefix, cols=3, w=150):
    im = Image.open(prefix + "-mobile.png").convert("RGB"); h = im.height
    parts = [im.crop((0, i * h // cols, im.width, (i + 1) * h // cols)).resize((w, round((h // cols) * w / im.width)), Image.LANCZOS) for i in range(cols)]
    m = Image.new("RGB", (w * cols + 6 * (cols - 1), parts[0].height), (255, 255, 255))
    for i, p in enumerate(parts): m.paste(p, (i * (w + 6), 0))
    return m


def save(im, path, budget):
    for q in (70, 62, 55, 48, 42):
        im.save(path, "JPEG", quality=q, optimize=True)
        if os.path.getsize(path) <= budget:
            return path
    im.thumbnail((im.width * 3 // 4, im.height * 3 // 4)); im.save(path, "JPEG", quality=45); return path


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    ref, new = args[0], args[1]
    lab = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else "run"
    calls = int(sys.argv[sys.argv.index("--calls") + 1]) if "--calls" in sys.argv else 4
    if lab in args: args.remove(lab)
    tmp = tempfile.mkdtemp()
    res = {"ref": [], "new": []}; notes = []; used = []
    for i in range(calls):
        flip = random.random() < 0.5
        A, B = (new, ref) if flip else (ref, new)
        imgs = [save(label(side(fold(A), fold(B), 24), "A|B"), f"{tmp}/1.jpg", 80_000),
                save(side(full_d(A), full_d(B)), f"{tmp}/2.jpg", 95_000),
                save(side(full_m(A), full_m(B), 28), f"{tmp}/3.jpg", 95_000)]
        judge = JUDGES[i % len(JUDGES)]
        out = ""
        for attempt in range(2):
            try:
                out = subprocess.run([GEM9, "-m", judge, "-p", PROMPT, *imgs], capture_output=True, text=True, timeout=240).stdout
            except subprocess.TimeoutExpired:
                out = ""
            m = re.search(r"\{.*\}", out, re.S)
            if m:
                break
            judge = JUDGES[(i + 1) % len(JUDGES)]
        try:
            js = json.loads(m.group(0))
        except Exception:
            print(f"call {i+1}: no JSON from {judge}: {out[-200:]!r}"); continue
        a, b = js["A"], js["B"]
        rn, rr = (a, b) if flip else (b, a)
        res["new"].append({k: float(rn[k]) for k in CRIT}); res["ref"].append({k: float(rr[k]) for k in CRIT})
        notes.append({"judge": judge, "new_is": "A" if flip else "B", "notes_new": js.get("notes_A" if flip else "notes_B"), "notes_ref": js.get("notes_B" if flip else "notes_A")})
        used.append(judge)
        print(f"call {i+1} [{judge}] new={'A' if flip else 'B'}  new {sum(rn[k] for k in CRIT)/7:.2f}  ref {sum(rr[k] for k in CRIT)/7:.2f}")
    if not res["new"]:
        sys.exit("✗ no judge answered")
    avg = {s: {k: round(sum(x[k] for x in res[s]) / len(res[s]), 2) for k in CRIT} for s in res}
    for s in avg: avg[s]["OVERALL"] = round(sum(avg[s][k] for k in CRIT) / len(CRIT), 2)
    print(f"{'criterion':22} {'ref':>6} {'new':>6}")
    for k in CRIT + ["OVERALL"]:
        print(f"{k:22} {avg['ref'][k]:6.2f} {avg['new'][k]:6.2f}" + ("  <" if avg['new'][k] < avg['ref'][k] else ""))
    for n in notes: print(f"- [{n['judge']}] new: {n['notes_new']} | ref: {n['notes_ref']}")
    p = os.path.join(ROOT, "state", "bench", "vision-scores.json")
    allr = json.load(open(p)) if os.path.exists(p) else {}
    allr[lab] = {"ref": ref, "new": new, "avg": avg, "calls": len(res["new"]), "judges": used, "notes": notes, "at": time.strftime("%Y-%m-%d %H:%M")}
    json.dump(allr, open(p, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()

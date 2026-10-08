#!/usr/bin/env python3
"""Label gate for generated product shots (product-image-brandlock 3-pass gate, pass 2 = narrow text sweep).

  /usr/bin/python3 scripts/landing_label_gate.py <image> [--handle ageaura-pure-nmn-tmg-nad-complex]

OCRs the image at 2x with macOS Vision (scripts/tools/label_ocr.swift) and checks it against the pack's
label whitelist in product_refs/<handle>.label.json: every REQUIRED string must be read letter-perfect
(case/space-insensitive), and any other text line that looks like a misspelling of a label word fails.
Exit 0 = PASS, 1 = FAIL (prints what was missing/garbled). The mark (logo) cannot be OCR'd: a human/vision
zoom check is still required (crop_zoom at >= 2x next to the real pack) before shipping.
"""
import difflib, json, os, re, subprocess, sys, tempfile
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(s):
    return re.sub(r"[^a-z0-9+*]", "", s.lower())


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    handle = sys.argv[sys.argv.index("--handle") + 1] if "--handle" in sys.argv else "ageaura-pure-nmn-tmg-nad-complex"
    if handle in args:
        args.remove(handle)
    spec = json.load(open(os.path.join(ROOT, "product_refs", f"{handle}.label.json")))
    im = Image.open(args[0]).convert("RGB")
    im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    im.save(tmp)
    out = subprocess.run(["swift", os.path.join(ROOT, "scripts", "tools", "label_ocr.swift"), tmp], capture_output=True, text=True, timeout=180).stdout
    os.unlink(tmp)
    lines = [l.split("\t", 1)[1] for l in out.splitlines() if "\t" in l]
    blob = norm(" ".join(lines))
    missing = [s for s in spec["required"] if norm(s) not in blob]
    wn = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
    vocab = {wn(w) for s in spec["required"] + spec.get("optional", []) for w in s.split() if len(wn(w)) >= 4}
    garbled = []
    for l in lines:
        for w in l.split():
            n = wn(w)
            if len(n) >= 4 and n not in vocab:
                close = difflib.get_close_matches(n, vocab, n=1, cutoff=0.75)
                if close:
                    garbled.append(f"{w} (~{close[0]})")
    print("read:", " | ".join(lines))
    if missing or garbled:
        print("✗ LABEL FAIL", ("missing: " + "; ".join(missing)) if missing else "", ("garbled: " + "; ".join(garbled)) if garbled else "")
        sys.exit(1)
    print(f"✓ LABEL PASS ({len(spec['required'])} required strings read letter-perfect)")


if __name__ == "__main__":
    main()

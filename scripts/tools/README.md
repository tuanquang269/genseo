# scripts/tools — small helpers for the landing lane (macOS)

- `subject_lift.swift <in> <out.png>`: Vision foreground mask, giving a transparent cutout. Use it to make `product_refs/<handle>-cutout.png` from a clean PDP pack image.
- `label_ocr.swift <img>`: Vision accurate OCR, printing `conf\ttext` lines. Used by `scripts/landing_label_gate.py`. macOS only (`swift` + Vision). A whitelist pack shot cannot pass without it. See `docs/LABEL_OCR_GATE.md`.
- `slice_view.py <prefix> <outprefix>`: slices the bench screenshots into viewable JPEGs.

## Generated pack shots (premium listicle, Kevin 2026-10-08)

```
GENSEO_NO_FACE=1 /usr/bin/python3 scripts/article_images.py --slug landing-<slug> --square --qc --name <name> \
  --ref product_refs/<handle>-cutout.png --prompt "SPEC: Photorealistic premium product photo 1024x1024. SCENE: <scene, bottle placement + % of frame height> <PACK FACE WHITELIST> <ART> <NEGATIVE>"
```

- PACK FACE WHITELIST: list every label string letter-perfect (from `product_refs/<handle>.label.json`), plus "no seals, no extra badges, no other text; the EXACT bottle in the reference image, upright, label facing the camera, undistorted".
- ART: "premium editorial wellness photography; warm ivory and sand tones with soft sage-green accents; soft diffused morning window light from the upper left; gentle botanical leaf shadows; travertine stone and natural linen; shallow depth of field; calm, airy, luxury skincare-brand look; muted natural colours."
- NEGATIVE: "no people, no faces, no hands, no other products or packaging, no readable text anywhere except the bottle label, no watermark."
- Gate: `landing_label_gate.py <img> --handle <handle>` must exit 0, and a 2x zoom crop of the mark must match the cutout. List the files in the spec's `pack_images` (validate_landing.py re-runs the gate). Missing `product_refs/<handle>.label.json`, a failed or empty OCR read, or a host that is not macOS exits non-zero. Do not treat that as a pass and do not skip the gate for a whitelist pack shot. Scene images with no `pack_images` and no label-gate claim are the only skip.
- Fallback: `scripts/landing_pack_shots.py --bg <empty generated scene> --out <webp> --x .6 --base .68 --h .5 [--dark]` composites the real cutout (tone match, cylinder shading, cast and contact shadow).

# Label OCR gate (fail closed)

`scripts/landing_label_gate.py` is the whitelist check for a generated pack shot. Exit 0 is the only pass. Exit 1 means the shot did not pass. Callers must not treat a crash, an empty read, or a missing file as a pass.

## When macOS Vision is required

Passing a whitelist pack shot requires all of:

- macOS
- `swift` on `PATH` (`/usr/bin/swift` on this Mac)
- `scripts/tools/label_ocr.swift` (Vision `VNRecognizeTextRequest`, accurate, no language correction)

The CLI upscales the image 2x and checks `product_refs/<handle>.label.json`. These all exit 1:

- the label JSON is missing, unreadable, or has no `required` strings
- the image path is missing
- `swift` is missing, the Swift script is missing, the process exits non-zero, times out, or returns no text lines
- the host is not macOS

There is no flag that skips OCR and still exits 0. Unit tests pass `ocr_lines` into `evaluate()` so CI can prove those branches without Vision. That stub is not available on the CLI.

`validate_landing.py` treats a premium spec as a whitelist claim when `pack_images` is non-empty or the spec says `label gate PASS`, `landing_label_gate`, or `PACK FACE WHITELIST`. A missing label file is a hard error. The gate is not invoked, and the spec does not pass.

The mark still needs a human or vision zoom at 2x. OCR does not check the logo.

## When the gate is skipped

Skip only when the image is not a whitelist pack shot: no `pack_images`, and the spec does not claim a label-gate pass. Scene images and a real PDP pack used because the product has no cutout are that case. Do not write `label gate PASS` for them.

`scripts/run_landing_headless.sh` generates a whitelist pack shot only when both `product_refs/<handle>-cutout.png` and `product_refs/<handle>.label.json` exist. If either is missing, use the real PDP image and do not claim the gate passed.

## Label files and reads that were not promoted

Required strings in a new label file are confidence-1.00 lines copied from `label_ocr.swift` on 2026-10-09. Misreads were omitted. They were not corrected, and doses the read did not show were not added.

| Handle | Whitelist | Note |
|---|---|---|
| `florafresh-vaginal-probiotics-gummies` | Front pouch: FloraFresh, Vaginal, Probiotic, Gummies, 60, DIETARY, GUMMIES, SUPPLEMENT | Not the Supplement Facts panel. Strain and CFU stay in `scripts/florafresh_rules.py`. |
| `pure-shilajit-gold-resin` | Front identity lines, including `75% Fulvic`, `Lab-Tested`, `Pure Shilajit Gold Resin`, `1.06 oz (30g) - 75 servings` | No milligram serving was read. Do not add one. Tomorrow's listicle dry-run must not publish. |
| `shilajit-shockwave` | wellness, nest, SHILAJIT, SHOCKWAVE, EXPERIENCE FOCUSED ENERGY, PEAK PERFORMANCE | No milligram token was read. The volume line was not stable (`1 il oz` / `1 1l oz`) and is not in the whitelist. An OCR line with a milligram dose fails the gate. |
| `turkesterone-advanced-formula` | No file | The brand line was read as `TURNESTERONE`. That was not rewritten into the label, and no dose was added. The gate fails closed until a letter-perfect file exists. |
| `ageaura-pure-urolithin-a` | No file | Not an allowed AgeAura SKU. Do not add a promotion whitelist. |

FusiForce's existing whitelist required token is `90` next to `Gummies`. A 2026-10-10 Vision read of the live gallery found two designed Supplement Facts graphics that disagree with that pouch (3 gummies / 28 servings / blueberry ingredients, and 4 gummies / 28 servings). Those tokens were not added. See `docs/FUSIFORCE_LABEL_GUARD.md`. A read that says `84` or `84 gummies` fails. The shilajit gummies whitelist includes optional `60 GUMMIES` and `60-DAY SUPPLY`. A `30 servings` line on that read fails. Those checks use the label file plus a stubbed OCR blob. They do not call Swift.

The Gold Resin PDP composite also contains a supplement-facts wrap. Vision misreads that wrap into near-misses of Shilajit, servings, and supplements, so `landing_label_gate.py` on `product_refs/pure-shilajit-gold-resin.png` exits 1. That is fail closed. A clean front-only read of the required lines passes the checker. Do not drop whitelist words to force the composite through. Gold Resin has no cutout, so the landing runner uses the real PDP image and must not claim `label gate PASS`.

## llms.txt drafts

`scripts/llms_txt_draft.py` writes a local file only. It does not upload.

- The Urolithin A PDP is omitted. The draft text itself must not contain `urolithin`.
- FloraFresh states Bacillus coagulans SNZ-1969 and 1 billion CFU, from `florafresh_rules.py`.
- FusiForce states 90 gummies, from the pack label file. The file does not contain a serving count or a ginseng milligram, so the draft does not state `30 servings`, `84`, `25 mg`, or `50 mg`.
- Shilajit gummies state 60 gummies and a 60-day supply, from the pack label. They do not state a 30-serving panel.
- Gold Resin, Shockwave, Turkesterone, and ShilaSource get a URL and no formula sentence.

Regenerate with:

```bash
python3 scripts/llms_txt_draft.py --from-product-refs --out /tmp/llms-wn.txt
```

`deploy/llms-txt/llms.txt` is the same local draft. Do not upload it.

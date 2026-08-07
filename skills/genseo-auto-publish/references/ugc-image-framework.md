# i5.2 — UGC Image Framework for GenSeo articles (borrowed from v5.2 Flow)

> Added 2026-08-07 (Kevin's order: "ảnh phải có UGC — mượn v5.2 framework cho video để update
> framework generate ảnh"). This is the STILL-IMAGE adaptation of the v5.2 12-section Omni video
> framework (`~/PATI/LLM-Wiki/30-creative/34-video/1-v5.2-flow.md`) + the ugc-cam-xuc emotion layer
> + the anti-stock direction. Generator stays **ima2 OAuth only**; packaging stays locked to the
> live PDP (`--product-ref` hard rule). Posture chốt bởi Kevin 2026-08-07:
> **HERO = clean pack-shot (PDP style, og:image legibility) · INLINE = UGC per this framework ·
> faces = PERSONA BANK (Pinterest gate run ONCE, approved creators reused forever).**

## HARD RULE — emit ALL 10 sections, labeled, in order. Never a run-on blob.

Same discipline as v5.2's 12-section rule: generating a UGC article image without filling this
template is a violation. Thinning a section (e.g. one-word Lighting) is what produces glossy
stock-looking output. Write the 10 sections as labeled lines, then pass the assembled prompt to
`article_images.py` (the wrapper appends the mechanical guardrails on top).

| # | Section | What goes in it |
|---|---------|-----------------|
| 1 | **SPEC** | `Photorealistic casual smartphone photo, 1536x1024 landscape` (or square). Never "professional product photography" for inline UGC. |
| 2 | **FIDELITY LOCK** | Product packaging exactly as reference — auto-appended by `--product-ref`; restate the real format in words ("green stand-up pouch", never invent). |
| 3 | **REFERENCE** | Which refs ride along: product pack shot (always, if product in frame) + persona photo (`--persona-ref`, only for face images). |
| 4 | **SCENE / MOMENT** | One specific lived moment, mid-action — "7am kitchen counter, cereal bowl half-eaten, pouch just unzipped". A moment, not a set. |
| 5 | **DEVICE & CAMERA** | The UGC signature: "shot on a phone, handheld, casual snapshot framing, slightly imperfect angle, natural depth of field, mild motion softness". |
| 6 | **SUBJECT & BODY** | Body tells the story, not adjectives (ugc-cam-xuc ②): "hand mid-reach into the pouch, gym bag zipper half-open". No-face default: wrist-up hands / POV / over-shoulder / back-of-head. Persona images: natural ¾ angle, MODERATE expression, real-smile mechanics (eyes crinkle — FACS), never stiff frontal grin. |
| 7 | **LIGHTING** | Available light only: window daylight, warm kitchen bulb, gym fluorescent. Slightly imperfect white balance. Never "studio lighting / softbox". |
| 8 | **ENVIRONMENT DETAIL** | Lived-in clutter that sells realness (keys, charging cable, half towel) + ONE brand-colour accent in the room (anti-stock memory). 2-3 props max, named specifically. |
| 9 | **STYLE / IMPERFECTION** | "Amateur photo energy": subtle grain, unretouched surfaces, no HDR gloss, colours slightly muted like a real phone JPEG. |
| 10 | **NEGATIVE** | Anti-stock tropes BY NAME (no beaming model staring at camera, no sterile marble countertop with citrus slices, no floating ingredients, no teal-orange grade) + anti-AI (no plastic skin, no glassy eyes, no waxy symmetric face) + no watermark/caption/text + packaging guard (auto). |

## Persona bank (the face lane — Kevin's chosen posture)

- The 🧑 real-face Pinterest gate runs **ONCE**: curate 3 real (non-AI) candidate photos per persona,
  Kevin picks 1 → that photo becomes the persona's PERMANENT reference, stored at
  `~/genseo/personas/<handle>/ref.jpg` + `persona.json` (name-slug, demo, camera notes, articles used).
- Every face image feeds THE ORIGINAL Pinterest ref (never a previous gen — ima2 i2i drifts identity;
  chaining gens compounds drift). Slight cross-article drift is accepted; frame faces ¾ or mid-shot,
  not tight closeups, to keep it unnoticeable.
- Camera-match directive is mandatory (from image-asset-rules): "match the reference's camera —
  available light, real skin texture with pores, same DOF class, subtle grain, no cosmetic smoothing."
- **≥1 no-face UGC image per article is still fine** — mix reads more authentic than face-in-every-shot.
- New persona (new demo/brand angle) ⇒ the gate runs once more for that persona. Never invent a face
  without the gate; never reuse a gen output as a new persona ref.
- Persona images still pass the 🖼️ duyệt-ảnh gate the FIRST time each persona is generated (present
  stills next to the Pinterest ref for Kevin); after that first approval the daily pipeline runs QC-only.

## Per-article image mix (posture chốt 2026-08-07)

1. **Hero** — CLEAN pack-shot lane (PDP-style, legible label, og:image duty). NOT UGC. `--product-ref`, no `--ugc`.
2. **Inline ×3** — UGC lane, this framework, typical mix: 1 persona-in-scene (face) + 2 no-face
   (hands/POV/flat-lay/detail). All with `--ugc`; product-in-frame ones also `--product-ref`.
3. Scene-variety guard: before writing prompts, check the `scene` column for the last ~10 rows in
   `PUBLISHED_ARTICLES_TRACKER.csv` — do not repeat a scene type twice in a row (kitchen-counter,
   gym-bench, bathroom-shelf, car, office-desk, park…). Log each image's scene type when publishing.

## Wrapper mechanics (`article_images.py`)

- `--ugc` → appends the UGC device/style suffix + the anti-stock/anti-AI NEG bank, and applies a
  light film-grain degrade after generation (borrowed from the degrade-start-frame realism rule —
  raw ima2 is too HD-clean) before webp compression.
- `--persona-ref /abs/path/ref.jpg` → attaches the persona photo + appends the camera-match directive.
- `--qc` → vision QC via `gem9` (9router subscription — NEVER per-token): sends output + refs with a
  strict rubric (packaging matches PDP ref? UGC-not-stock? no rendered text? face natural, matches
  persona?) → verdict `QC:PASS` / `QC:FAIL <reason>`; FAIL = re-roll with the reason folded into the
  prompt, max 2 re-rolls then STOP and report. Daily runs use `--qc` on every UGC image.

## Filled example (inline, no-face, product in frame)

```
SPEC: Photorealistic casual smartphone photo, 1536x1024 landscape.
FIDELITY LOCK: green stand-up pouch of Wellness Nest FusiForce Creatine Monohydrate Gummies, exactly as reference.
REFERENCE: real PDP pack shot (auto via --product-ref).
SCENE/MOMENT: 7:05am kitchen counter mid-breakfast — cereal bowl half-finished, phone propped against the fruit bowl, pouch just unzipped.
DEVICE & CAMERA: shot on a phone, handheld, slightly tilted casual framing, natural shallow depth, mild motion softness.
SUBJECT & BODY: a hand (wrist up) pinching one pale green gummy above the open pouch, other edge of frame catches a coffee mug being pushed aside.
LIGHTING: morning window light from the left, slightly warm white balance, soft shadows.
ENVIRONMENT DETAIL: car keys and an AirPods case by the toaster, a green dish towel (brand colour accent) crumpled near the sink.
STYLE/IMPERFECTION: amateur snapshot energy, subtle grain, unretouched counter smudges, muted phone-JPEG colours, no HDR gloss.
NEGATIVE: no beaming model facing camera, no sterile marble hero counter, no floating ingredients, no studio softbox light, no teal-orange grade, no plastic skin, no watermark, no caption, no on-image text.
```

## Cross-refs (do not restate — read at source)

Packaging hard rule → CLAUDE.md 📦 + SKILL.md STEP 5 · generator/resolution → [[image-asset-rules]] ·
v5.2 origin + 12-section discipline → [[v5.2-flow]] · emotion/FACS depth → `ugc-cam-xuc` skill ·
anti-stock NEG direction → memory `imagery-anti-stock-direction` · degrade rationale → memory
`ai-video-degrade-startframe-realism` · <80KB webp → CLAUDE.md 🖼️.

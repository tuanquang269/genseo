# i5.2 — UGC Image Framework for GenSeo articles (borrowed from v5.2 Flow)

> Added 2026-08-07 (Kevin's order: "ảnh phải có UGC — mượn v5.2 framework cho video để update
> framework generate ảnh"). This is the STILL-IMAGE adaptation of the v5.2 12-section Omni video
> framework (`~/PATI/LLM-Wiki/30-creative/34-video/1-v5.2-flow.md`) + the ugc-cam-xuc emotion layer
> + the anti-stock direction. Generator stays **ima2 OAuth only**; packaging stays locked to the
> live PDP (`--product-ref` hard rule). Posture chốt bởi Kevin 2026-08-07, hero lane REPLACED
> 2026-08-08 (Kevin: "luôn luôn có hình ảnh nhân vật khác nhau mỗi blogs và có ảnh sản phẩm —
> có model và ảnh sản phẩm trên hình ảnh thumbnail"):
> **HERO = MODEL + PRODUCT (ad-style, § Hero lane below) · INLINE = UGC per this framework ·
> faces = PERSONA BANK (Pinterest gate run ONCE, approved creators reused forever).**

## HERO LANE — MODEL + PRODUCT ON THE THUMBNAIL (HARD RULE, Kevin 2026-08-08)

The hero is the FIRST `![...]()` image in the body — `shopify_publisher.py` promotes it to
`article.image`, so it IS the blog thumbnail and og:image. Reference bar: the GemPages FusiForce
hero on `/blogs/news/news-copy-of-from-stiff-to-strong…` (model holding the green pouch label-forward,
bright ad-style). Requirements, all mandatory:

1. **A persona (visible face) AND the real product pack, together in frame.** Label faces the
   camera and stays legible at thumbnail size. `--product-ref` + `--persona-ref` + `--qc`, always.
   **DEFAULT COMPOSITION (2026-08-09, after 4 QC burns in 2 days): the pack STANDS on a
   surface beside / in front of the model — hands do NOT touch it. Put "no hands touching or
   holding the pouch" in the NEGATIVE.** ima2 reliably warps hand-pack grips ("warped hand" was
   the QC fail on 3 of 4 burned rolls). A holding pose is a stretch goal: attempt it only on the
   FIRST roll; any QC fail → switch to the no-contact composition for the remaining re-rolls.
2. **Different character per blog post.** The hero persona MUST differ from the previous articles'
   hero personas — rotate through the approved bank, never repeat until the bank is exhausted, then
   restart with the least-recently-used. **ENUMERATE the bank — `ls ~/genseo/personas/` and read
   each `persona.json` — before claiming it is too small; NEVER assume its size from docs or
   prior-run reports** (the 2026-08-09 morning run blocked itself believing the bank had 1 face
   while 4 were installed). Log the persona handle in the tracker CSV row. Bank too
   small to rotate (or no demo-appropriate persona) → generate with the least-recently-used
   compliant persona and put one line in the report: "persona bank needs expansion (real-face gate)".
   NEVER invent a fresh face to satisfy variety — the 🧑 gate still owns new faces.
3. **REUSED PERSONA ⇒ NEW LOOK DIRECTION (HARD RULE, Kevin 2026-08-09).** Rotating the bank is
   NOT enough. When a face comes back around it must be posed differently, or the blog index reads
   as a wall of AI — Kevin flagged exactly this on the live `/blogs/news` grid: **m1-stubble**
   (#4 turkesterone + #7 energy drops) and **f2-brunette** (#1 + #6) each shipped the same
   straight-to-camera ¾ pose twice, *"easily to be spot as AI generated"*. Before writing the hero
   prompt: grep the tracker for this persona handle, read every prior `gaze:` note, and pick an
   axis value NOT yet used for that face. State it in the prompt in plain words and log
   `gaze:<value>` in the tracker row.

   | axis value | what it means in the prompt |
   |---|---|
   | `to-camera-3q-left` | body ¾ turned, face to lens, weight on left — the default FIRST use only |
   | `to-camera-3q-right` | mirror of the above |
   | `off-left` / `off-right` | head turned away, eyes off-frame, lens catches the side of the face |
   | `down-at-product` | looking down at the pack / phone / notebook on the surface, not at the lens |
   | `over-shoulder` | body angled away from camera, head turned back over the shoulder |
   | `profile` | full side view, eye-line parallel to the frame edge |

   **`to-camera-*` may never run twice in a row for the same persona, across any two articles.**
   Change at least ONE more variable too: framing (chest-up / waist-up / wider room-with-subject),
   expression register (neutral-focused / closed-mouth half-smile / mid-laugh / skeptical brow), or
   wardrobe colour. Identity = the face in `ref.jpg` and nothing else — outfit, hair styling and
   setting are free to change and SHOULD change. The same discipline applies to the inline
   persona-in-scene image.
4. **Style = bright ad-style hero, NOT gritty UGC.** No `--ugc` flag. Clean daylight, appealing,
   confident model, natural real-smile mechanics. The anti-stock NEG bank ("no beaming model facing
   camera") applies to the INLINE lane only — the hero is EXEMPT from that one line by design
   (Kevin's reference IS a model facing camera with the pack). Anti-AI NEG stays (no plastic skin,
   no glassy eyes, no waxy face), packaging guard stays, and **no on-image text** stays — the text
   overlay on Kevin's reference is a design-tool composite, not something ima2 may attempt.
5. Persona must fit the article's audience demo (women-40+ article → female 40s–50s persona;
   men's shilajit article → male persona once the bank has one).

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

## Packaging refs — CURATED LIBRARY ONLY (HARD RULE, Kevin 2026-08-09)

`~/genseo/product_refs/<handle>.png` is a hand-cropped, eyeball-verified shot of the REAL package,
with `<handle>.json` describing it in words (format, colour, wordmark, title, footer).
`article_images.py` uses it automatically for `--product-ref <handle>` and appends the written
description to the prompt (prompt text overrides the ref image when they disagree).

- **Never pass `:index`.** Every WellnessNest PDP "image" is a marketing composite; some contain no
  package at all. Ticket #3 passed `--product-ref florafresh…:1` — an "AFTER ONLY 2 WEEKS" graphic
  with no pouch in it — and the generator invented a WHITE pouch and pasted that graphic's stat
  badges onto the fake label. Two published images shipped wrong. The wrapper now ignores `:index`
  whenever a curated ref exists, but do not write one anyway.
- **SKU has no curated ref?** The wrapper prints a warning and falls back to PDP image [0]. In that
  case you MUST open the downloaded ref and confirm the package is actually in it BEFORE using the
  output — or stop and report that the SKU needs a curated ref (crop it from the PDP composite,
  save both `.png` and `.json`, commit).
- **Describe the real package in the prompt too** — format and colour by name ("dusty-pink stand-up
  pouch", never "white pouch"), and NEGATIVE-list the failure: "no invented label layout, no
  stat-percentage badges on the package".
- Product details beyond the label count too: gummy colour must match the real flavour (FloraFresh
  pineapple = amber, not red/pink).
- Covered today: florafresh · fusiforce · ageaura-nmn-tmg · ageaura-urolithin-a · shilajit-shockwave
  · turkesterone. Any new SKU = curate first, generate second.

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

1. **Hero** — MODEL + PRODUCT lane (§ Hero lane above): approved persona holding the real pack
   label-forward, bright ad-style, different persona per post. `--product-ref` + `--persona-ref`
   + `--qc`, no `--ugc`. (Old clean pack-shot lane RETIRED 2026-08-08.)
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

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
2. **THE PICKER CHOOSES THE PERSONA, THE GAZE AND THE SHOT — YOU DO NOT** (HARD RULE, Kevin
   2026-08-09: *"prepare 200 referenced different models as hard rule"*). The bank is scaling
   4 → **200 faces** across **10 rotation pools** (gender × age band; `~/genseo/personas/taxonomy.json`),
   which is past the size where an agent can eyeball rotation or grep it out of a CSV. Run:
   ```
   /usr/bin/python3 ~/genseo/scripts/persona_picker.py pick --audience <token>   # or --brand <Brand>
   ```
   and obey the JSON exactly: `hero`, `hero_ref`, `hero_gaze`, `hero_shot`, `inline_gaze`,
   **`hero_face_angle`**, **`inline_face_angle`** (+ their `*_phrase` fields, which go into the
   prompt verbatim). It enforces pool-scoped LRU, the one-angle-per-model law, the no-repeat gaze
   law, the last-3 shot window and the every-3rd no-face hero **mechanically**. Echo every
   `warnings[]` entry into the report verbatim. **Never `ls` the bank and pick by eye, and never
   grep the tracker for rotation state** — parsing the free-text `Posted Date` column on 2026-08-09
   returned `no-contact` and `bank` as if they were persona handles, which is precisely how a
   200-face bank silently rots back into reusing one face. `hero: "NO-FACE"` → compose
   product-in-a-real-scene or scene-only (still `--product-ref` + `--qc`, still no `--ugc`); an
   empty or angle-exhausted pool now DEGRADES to exactly that, with the shortfall in `warnings[]`
   — report it and **NEVER invent a fresh face or borrow a wrong-demographic one** (the 🧑 gate
   still owns new faces). A non-zero exit means a bad audience token or an unreadable state file:
   fix it, do not route around it.
   **AFTER a successful LIVE publish only:** `persona_picker.py commit --hero … --gaze … --inline-gaze …
   --shot … --face-angle … --inline-face-angle … --expect-seq <seq from pick>`. `--face-angle` is
   mandatory for a face hero and commit REFUSES an angle that persona has already spent. A non-zero
   exit there means another run committed first — re-run `pick`, never force it.
3. **REUSED PERSONA ⇒ NEW LOOK DIRECTION (HARD RULE, Kevin 2026-08-09).** Rotating the bank is
   NOT enough. When a face comes back around it must be posed differently, or the blog index reads
   as a wall of AI — Kevin flagged exactly this on the live `/blogs/news` grid: **m1-stubble**
   (#4 turkesterone + #7 energy drops) and **f2-brunette** (#1 + #6) each shipped the same
   straight-to-camera ¾ pose twice, *"easily to be spot as AI generated"*. The picker now decides
   the value; **your** job is to say `hero_gaze` in the prompt in plain words (and `inline_gaze`,
   not `hero_gaze`, on the inline persona-in-scene image) and log `gaze:<value>` in the tracker row.

   **⚠️ THREE INDEPENDENT AXES — do not collapse them.** `face_angle` = where the **HEAD** points
   (yaw × pitch). `gaze` = where the **EYES** point *within* that head. `shot` = where the
   **CAMERA** is. The pre-2026-08-10 gaze vocabulary mixed head orientation (`profile`,
   `over-shoulder`) into the eye axis, so the two contradicted each other in a single prompt and
   the generator quietly dropped one. Current `gaze_values` are eye-only, and each carries a
   `family`: **`to-camera`** (`at-lens`, `just-past-lens`) or **`away`** (`down-at-product`,
   `down-at-hands`, `off-into-room`, `up-and-away`, `at-another-person`). The picker will not give
   the same persona `to-camera` two articles running, and will not put hero and inline in the
   `to-camera` family within one article.

   **🔁 ONE FACE ANGLE PER MODEL, ONCE, EVER (HARD RULE, Kevin 2026-08-10: *"khong bao gio
   generate cung 1 goc mat cho 1 model"*).** 21 angles per persona — 7 yaws (`front`, `3q-left/right`,
   `profile-left/right`, `half-back-left/right`) × 3 pitches (`level`, `chin-down`, `chin-up`). Each
   is spent permanently on first use; hero and inline count separately, so one article consumes two.
   **You do not choose the angle and you do not substitute one** — pass `--face-angle
   <hero_face_angle>` to `article_images.py` and put `hero_face_angle_phrase` into the prompt
   verbatim. The wrapper rejects an angle the persona has already spent, and QC FAILs an image whose
   rendered head does not match the brief. A wrong angle is not a cosmetic miss: the angle is burned
   whether or not it rendered, so it costs one of 21 AND leaves a repeat the bookkeeping calls unique.

   Change at least ONE more variable too: framing (chest-up / waist-up / wider room-with-subject),
   expression register (neutral-focused / closed-mouth half-smile / mid-laugh / skeptical brow), or
   wardrobe colour. Identity = the face in `ref.jpg` and nothing else — outfit, hair styling and
   setting are free to change and SHOULD change. The same discipline applies to the inline
   persona-in-scene image.
4. **ROTATE THE SHOT TYPE TOO (HARD RULE, 2026-08-09).** Contact-sheeting the six live heroes
   (#4–#9) after Kevin's rejection showed the repeat is not only gaze — five of six were the same
   shot: ONE adult, mid-shot, indoors, daylight, smiling, with the pack planted large in a
   foreground corner. A wall of that reads as machine output even when the faces and the gaze
   differ, because the *brief* is visibly identical. The picker returns `hero_shot` (it keeps the
   last-3 window in `personas/index.json`, so do not read the tracker for it). Write that shot type
   into the prompt and log `shot:<value>`:

   | shot value | what changes |
   |---|---|
   | `mid-subject-fg-pack` | the current default — subject mid-shot, pack large in the near corner |
   | `wide-room` | subject small in a real room, pack on a surface at natural size |
   | `over-shoulder` | camera behind the subject, reading past them to the pack |
   | `low-table-level` | lens down at surface height, pack in the near plane, subject behind it |
   | `high-angle-down` | looking down onto the surface and the subject's hands/upper body |
   | `through-doorway` | subject framed by a doorway/window edge, pack on the near sill or table |

   The label still has to be legible at thumbnail size — that constrains how far the pack can
   recede, not which shot type you may pick.
5. **Style = bright ad-style hero, NOT gritty UGC.** No `--ugc` flag. Clean daylight, appealing,
   confident model, natural real-smile mechanics. The anti-stock NEG bank ("no beaming model facing
   camera") applies to the INLINE lane only — the hero is EXEMPT from that one line by design
   (Kevin's reference IS a model facing camera with the pack). Anti-AI NEG stays (no plastic skin,
   no glassy eyes, no waxy face), packaging guard stays, and **no on-image text** stays — the text
   overlay on Kevin's reference is a design-tool composite, not something ima2 may attempt.
6. Persona must fit the article's audience demo (women-40+ article → female 40s–50s persona;
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
- Covered today: florafresh · fusiforce · ageaura-pure-nmn-tmg-nad-complex · shilajit-shockwave
  · pure-shilajit-gold-resin · shilasource-himalayan-shilajit-resin · turkesterone. AgeAura image prompts use that one handle only — never `ageaura-pure-urolithin-a` or any other AgeAura SKU (`scripts/brand_rules.py` refuses the prompt). FloraFresh prompts never put a formula claim its Supplement Facts label does not carry on a badge, overlay or caption ("15B CFU", Lactobacillus strain names, "sugar-free"; `scripts/brand_rules.py` refuses the prompt). Shockwave prompts never put a milligram, serving count, or volume the pack-label file does not list (`scripts/shockwave_rules.py`). Gold Resin prompts may repeat the whitelist serving line and `75% Fulvic`, and never put a milligram or a different serving count, volume, weight, or day-supply (`scripts/gold_resin_rules.py`). ShilaSource resin prompts may repeat the whitelist fulvic line, net-weight line, and 75 servings badge, and never put a milligram, a different serving count, a different fulvic percentage, a mineral count, or a day-supply (`scripts/shilasource_resin_rules.py`). Turkesterone prompts may repeat the front-of-pack whitelist, including the split 60 and Capsules badge, and never put a milligram, a serving count, a different capsule count, or a day-supply (`scripts/turkesterone_rules.py`). Any new SKU = curate first, generate second.

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
- **Structure (2026-08-09, the 200-face rule).** `taxonomy.json` = the 50-cell / 10-pool target;
  `<handle>/persona.json` = IMMUTABLE provenance (source URL, photographer, licence + attribution text,
  sha256, QC verdict, Kevin's approval date); `personas/index.json` = MUTABLE rotation state, written
  ONLY by `persona_picker.py`. Never hand-edit `index.json` mid-run and never let a persona exist
  without a licence record — `status: "flagged"` marks a face the picker uses only as a last resort
  (f1-redshirt: low-res crop; f3-silver: burned-in photographer watermark). Licence spine for new
  faces: Flickr `license=9,11,4` only (CC0 / CC BY 4.0 / CC BY 2.0). **Pexels and Unsplash are OUT** —
  both ToS forbid using their photos for machine-learning/datasets.
- **The 3-option approval gate is UNCHANGED and still blocking for new faces.** Nothing enters the bank
  without Kevin. Scaling to 200 needs him to pick the intake format first (3-options-per-face, or
  wave contact sheets) — until he answers, the fetcher may only STAGE candidates, never approve them.

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

- `--ugc` → appends the UGC device/style suffix + the anti-stock/anti-AI NEG bank. Without it you
  are in the hero lane, which gets the hero-safe NEG subset instead (kills plastic skin / waxy
  symmetry / catalogue retouching, keeps the bright ad look) — **with or without a face**.
- **Film-grain degrade runs on EVERY image**, always, before webp compression (borrowed from the
  degrade-start-frame realism rule — raw ima2 is too HD-clean). It used to be a `--ugc` effect, then
  a `--ugc or --persona-ref` effect; both times the hero lane leaked through and the heroes — the
  only image the blog index grid shows — were the glossiest thing on the site. Measured on the
  flattest tiles: live pre-fix heroes 0.00–0.58, grained images 1.2–2.3. A hero at 0.00 is a render.
- `--persona-ref /abs/path/ref.jpg` → attaches the persona photo + appends the camera-match directive.
- `--qc` → vision QC via `gem9` (9router subscription — NEVER per-token): sends output + refs with a
  strict rubric (packaging matches PDP ref? UGC-not-stock? no rendered text? face natural, matches
  persona?) → verdict `QC:PASS` / `QC:FAIL <reason>`; FAIL = re-roll with the reason folded into the
  prompt, max 2 re-rolls. A face image that is still refused or still failing QC falls back to one human no-face shot for that image only (a hand, a forearm, or a body cropped below the eyes; no --persona-ref). An empty pack-only still life is not that fallback. Daily runs use `--qc` on every UGC image.

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

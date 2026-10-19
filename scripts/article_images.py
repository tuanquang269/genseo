#!/usr/bin/env python3
"""article_images.py — GenSeo image lane for wellnessnest.co.

Generates ONE article image via ima2 (ChatGPT Image 2.0 OAuth — the only
generator PATI hard rules allow), then compresses it to webp under 80KB
(website-image hard rule; Shopify CDN re-encodes, so small source = small CDN).

Usage:
  python3 article_images.py --slug <article-slug> --name hero \
      --prompt "..." [--ref /abs/path/real_pack.png ...] [--square]

Prints the LOCAL absolute .webp path on the last line — put exactly that path
in the draft's ![alt](...) tag; shopify_publisher.py uploads it to the CDN.

House rules baked in:
  * generator = ima2 OAuth only (no KIE / per-token APIs)
  * a dropped Responses stream, HTTP 429/5xx, timeout, or connection reset
    is retried inside gen_png (3 attempts, 5s then 15s). One call stops at
    10 minutes so a hero plus three inline images stay under half of the
    90-minute ticket cap. A timed-out ima2 tree is killed before the
    backoff sleep. Auth, content policy, and invalid-request failures are
    not retried.
  * default size 1536x1024 (blog landscape, 1K class — never 2K/4K)
  * every prompt gets the no-watermark/no-caption suffix
  * output webp < 80KB (quality ladder, then width ladder)
  * HARD RULE (Kevin 2026-08-07): any image that SHOWS a product must be
    generated FROM the real packaging on /products/<handle> — pass
    --product-ref <handle> (auto-downloads the PDP pack shot as ref and locks
    the prompt to it). Never invent packaging: format (pouch vs jar vs
    bottle), colors, and label must match the live PDP. The first violation
    was real: FusiForce gens showed a JAR; the real product is a green POUCH.
    After generating, VIEW the output next to the ref before using it.
"""
import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
import brand_rules
import persona_picker

import shutil as _shutil


def _find_bin(name, candidates):
    for c in candidates:
        p = os.path.expanduser(c)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    found = _shutil.which(name)
    if found:
        return found
    sys.exit(f"✗ {name} binary not found (tried {candidates} + PATH)")


IMA2 = _find_bin("ima2", ["~/.npm-global/bin/ima2", "~/.nvm/versions/node/v24.19.0/bin/ima2", "~/.local/bin/ima2"])
CWEBP = _find_bin("cwebp", ["/opt/homebrew/bin/cwebp", "~/.local/bin/cwebp", "/usr/local/bin/cwebp"])
OUT_ROOT = "/Users/kevinkreative/genseo/tmp_images"
MAX_BYTES = 80 * 1024
# The third-party-brand clause is not belt-and-braces: left ungated, the generator fills empty
# shelf and counter space with plausible supplement tubs, and on 3 of 3 test generations one of
# them read LIV PURE — a real competing brand, on our own blog. The watermark ban did not cover
# it and the QC packaging check only compared against OUR label, so nothing was watching.
PROMPT_SUFFIX = (" NO watermark. NO blog name text. NO caption. NO attribution text in any "
                 "corner. Clean image only. Product label must remain legible. NO other branded "
                 "product packaging in frame. Never invent a supplement brand name.")
# Appended ONLY on no-face images. Until 2026-08-09 this clause rode on EVERY prompt,
# including the hero lane — which mandates a visible approved persona. So the generator
# got "match this reference person's face" and "no recognizable human faces" in the same
# prompt and split the difference into a generic averaged face. That contradiction, not
# the size of the persona bank, is the main reason the /blogs/news grid read as AI.
NO_FACE_CLAUSE = " No recognizable human faces."
PACK_FIDELITY = (" The product package must EXACTLY match the reference image: same package "
                 "format, same shape, same colors, same label layout and text. Do not invent, "
                 "restyle, or substitute the packaging.")
# i5.2 UGC lane (see skills/genseo-auto-publish/references/ugc-image-framework.md).
# The agent writes the 10-section prompt; these are the MECHANICAL backstops.
UGC_SUFFIX = (" Shot on a phone, handheld, casual snapshot framing, slightly imperfect angle, "
              "natural depth of field, available light only, subtle grain, amateur photo energy, "
              "muted phone-JPEG colours, no HDR gloss, unretouched surfaces.")
UGC_NEG = (" NO beaming model staring at camera. NO sterile marble hero countertop. NO floating "
           "ingredients. NO studio softbox lighting. NO teal-orange colour grade. NO plastic "
           "skin, NO glassy eyes, NO waxy symmetric face. NOT a stock photo.")
CAMERA_MATCH = (" Match the persona reference photo's camera exactly: available light (not "
                "studio), real skin texture with visible pores and slight imperfections, same "
                "focal length class and depth of field, subtle grain, no cosmetic smoothing.")
# Hero lane forbids --ugc, so before 2026-08-09 it carried NO anti-stock negatives at all —
# the only images on the blog index were the only ones generated without them. This is the
# hero-safe subset: it kills the plastic-skin/waxy-symmetry tells without killing the bright
# ad-style look the hero lane is supposed to have (so no "NO studio softbox" here).
HERO_NEG = (" NO plastic skin, NO waxy symmetric face, NO glassy eyes, NO airbrushed pores, "
            "NO teal-orange colour grade, NO flawless catalogue retouching. NOT a stock photo.")
GEM9 = "/Users/kevinkreative/.local/bin/gem9"

PERSONAS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "personas")


FACE_ANGLE_CLAUSE = (" HEAD ANGLE, follow exactly and do not average it toward a front-on "
                     "portrait: {phrase}.")


def face_angle_phrase(angle_id, persona_ref):
    """Kevin's hard rule (2026-08-10): never the same face angle twice for one model.

    persona_picker.py already refuses to hand out a spent angle. This is the second lock, and
    it is the one that matters: the picker's output passes through an agent that writes a prompt
    by hand, and every previous single-point rule in this pipeline has eventually been lost at
    exactly that step — paraphrased, abbreviated, or simply not carried over. So the wrapper
    re-reads the persona's own history and refuses, rather than trusting that what arrived here
    is what the picker said.

    Returns the angle's prompt phrase, which is also handed to the QC rubric so the vision gate
    checks the head against the same words the generator was given.
    """
    tax_p, idx_p = os.path.join(PERSONAS, "taxonomy.json"), os.path.join(PERSONAS, "index.json")
    try:
        with open(tax_p) as fh:
            tax = json.load(fh)
    except (OSError, ValueError) as exc:
        sys.exit(f"✗ cannot read the face-angle vocabulary ({exc}). Refusing to generate a face "
                 f"image without it — an unvalidated angle is an unenforced rule.")
    values = tax.get("face_angle_values") or []
    # The phrase is subject-relative ("turned about 35 degrees to THEIR left"), and on
    # 2026-08-13 both ima2 and the judge read it viewer-relative: hero 3q-left rendered as
    # 3q-right and inline profile-right as profile-left, and QC passed both because the judge
    # makes the same flip the generator did. A gate that shares the generator's confusion cannot
    # catch it. `frame_hint` restates the same angle in terms neither side has to invert — which
    # image edge the nose points at, and which ear is nearest the camera — and rides along on the
    # ONE string that goes to both, so they can never be given different definitions.
    angles = {a["id"]: " — ".join(x for x in (a["phrase"], a.get("frame_hint")) if x)
              for a in values}
    renderable = {a["id"] for a in values if a.get("renderable", True)}
    if angle_id not in angles:
        sys.exit(f"✗ unknown --face-angle {angle_id!r}. Valid: {', '.join(sorted(renderable))}")
    # Second reader of the same flag persona_picker.py filters on. The picker will not issue a
    # non-renderable angle, so reaching here means a hand-picked one — and the cost of letting it
    # through is not a re-roll, it is one of the persona's irreplaceable angles marked spent for
    # an image the generator cannot render and the judge cannot verify.
    if angle_id not in renderable:
        why = next((a.get("not_renderable_reason") for a in values if a["id"] == angle_id), "")
        sys.exit(f"✗ --face-angle {angle_id!r} is marked non-renderable in taxonomy.json"
                 f"{': ' + why if why else ''}.\n"
                 f"  Use an angle from `persona_picker.py pick`; it only issues renderable ones.")

    # The handle is derived from the ref's parent directory, so a ref from outside the bank
    # yields a handle nothing in index.json matches — which reads as "this persona has spent no
    # angles" and waves every angle through, forever. Refuse instead of guessing: a face that is
    # not in the bank has no angle history to check it against, and that is the whole gate.
    ref_abs = os.path.abspath(persona_ref)
    if os.path.dirname(os.path.dirname(ref_abs)) != os.path.abspath(PERSONAS):
        sys.exit(f"✗ persona ref must live in the bank ({PERSONAS}/<handle>/ref.jpg), got "
                 f"{ref_abs}. An off-bank ref has no angle history, so the one-angle-per-model "
                 f"rule cannot be enforced against it.")
    handle = os.path.basename(os.path.dirname(ref_abs))
    try:
        with open(idx_p) as fh:
            entry = ((json.load(fh).get("personas") or {}).get(handle)) or {}
    except (OSError, ValueError):
        entry = {}

    # Second gate, same reasoning as the first: persona_picker.py already selects on the
    # {active, flagged} allow-list, but its output passes through an agent that writes the
    # article_images.py call by hand, and a hand-written --persona-ref never went through the
    # picker at all. Every persona in the bank is `retired` today and the ones sourcing is about
    # to add arrive `pending`, so the hand-written path currently points at nothing approved.
    # Fail CLOSED on a missing or unreadable entry: absent state is absent approval, and this is
    # the one difference from the angle check above, where absent state genuinely means nothing
    # has been spent yet. Nothing legitimate is lost — the picker only ever emits refs for
    # personas that are in index.json and selectable.
    status = entry.get("status")
    if status not in ("active", "flagged"):
        sys.exit(f"✗ persona {handle} is not approved for use (status={status!r}; only 'active' "
                 f"and 'flagged' may generate). Nothing but `fetch_personas.py approve {handle} "
                 f"--by <who>` may change that — do not edit index.json by hand, and do not "
                 f"route around this by passing the ref from somewhere else.")

    # Same identity gate as persona_picker.pick. A hand-written --persona-ref never went
    # through the picker, which is how a gurn that is still status=active would become the
    # og:image. m3039-as-02 is refused here even if its booleans are cleared.
    why = persona_picker.identity_refusal(entry, handle)
    if why:
        sys.exit(f"✗ persona {handle} cannot anchor a hero / identity reference ({why}).\n"
                 f"  persona_picker.py will not issue this face. Do not pass its ref by hand.")

    if angle_id in (entry.get("angles_used") or []):
        sys.exit(f"✗ persona {handle} has ALREADY used face angle {angle_id!r}. Kevin's hard rule "
                 f"is one angle per model, once, ever. Run `persona_picker.py pick` and use the "
                 f"angle it gives you — do not pick one by hand.\n"
                 f"  spent so far: {', '.join(entry.get('angles_used') or [])}")

    # Third gate: was this angle actually ISSUED for this persona? The check above catches a
    # REPEAT, which is the rule as written; it cannot catch a fresh angle the agent chose for
    # itself, and that one is worse — it ships live and lands in no ledger, so the picker will
    # hand it out again later in perfect good faith. Since 2026-08-11 `pick` reserves what it
    # issues, so an outstanding reservation is exactly the evidence needed.
    #
    # Conditioned on the persona HAVING a reservation, deliberately. An empty list means either
    # a pre-reservation state file or a persona nobody has picked, and neither is a violation;
    # refusing on absence would break every legitimate call made before this existed.
    reserved = entry.get("angles_reserved") or []
    if reserved and angle_id not in reserved:
        sys.exit(f"✗ persona {handle} was issued {', '.join(reserved)} — not {angle_id!r}. Use the "
                 f"angles `persona_picker.py pick` printed for THIS article; substituting one "
                 f"burns the issued angles and puts an unrecorded angle on a live page.")

    return angles[angle_id]


def record_credit(out_dir, persona_ref):
    """Note, beside the images, whose photograph this article's face was anchored on.

    CC BY 2.0 is not satisfied by a credit sitting in a JSON file on my laptop — it has to
    travel with the published work, and all three usable faces in the bank are CC BY. The
    publisher is the thing that reaches the page, but it sees only image paths: it has no way
    to know which persona fed which render. So the step that DOES know writes it down, in the
    one directory the publisher is guaranteed to be reading from.

    Keyed by handle, so a re-roll of the same image overwrites rather than duplicating, and an
    article using two personas credits both."""
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(persona_ref)),
                               "persona.json")) as fh:
            src = (json.load(fh).get("source") or {})
    except (OSError, ValueError):
        return                       # no provenance on disk = nothing to assert; upstream gates
    if not src.get("attribution_required"):
        return                       # CC0 asks for nothing
    handle = os.path.basename(os.path.dirname(os.path.abspath(persona_ref)))
    path = os.path.join(out_dir, "CREDITS.json")
    try:
        with open(path) as fh:
            creds = json.load(fh)
    except (OSError, ValueError):
        creds = {}
    creds[handle] = {"text": src.get("attribution_text"), "license": src.get("license"),
                     "license_url": src.get("license_url"), "page_url": src.get("page_url"),
                     "author": src.get("author")}
    with open(path, "w") as fh:
        json.dump(creds, fh, indent=1)


def degrade_grain(png_path):
    """Light film-grain + micro quality degrade — raw ima2 is too HD-clean for UGC
    (same rationale as the degrade-start-frame video rule). Applied BEFORE webp.
    Pure PIL (no numpy on system python): zero-centered noise via ImageChops."""
    from PIL import Image, ImageChops
    im = Image.open(png_path).convert("RGB")
    noise = Image.effect_noise(im.size, 8).convert("L")  # sigma≈8 around 128 = subtle grain
    im = ImageChops.add(im, Image.merge("RGB", [noise] * 3), scale=1.0, offset=-128)
    im.save(png_path)


# Cloudflare (cloudflared, in front of staff.patiagency.com) gives up on a slow upstream at ~90s
# and answers 502. The judge payload is base64 inside a JSON body, so upstream wall-clock scales
# with ref bytes. Measured 2026-08-12 against cx/gpt-5.6-luna, same rubric shape:
#   180KB of refs → 19s, verdict.   260KB → 45s, verdict.   460KB → 502 after 90s.
# The refs this pipeline actually hands the judge are far past that: curated pack shots reach
# 918KB (premium-himalayan-shilajit-gummies.png) and persona ref.jpg reaches 1.1MB, so a hero QC
# — candidate + pack + face — was a ~2MB body and could not be judged AT ALL. From the call site
# that is indistinguishable from a quota outage: no VERDICT line. And on a face the gate fails
# CLOSED, so it burns all three rolls without a single real verdict, which is exactly the shape
# of the two runs that failed to deliver.
#
# So the judge gets its own downscaled copies. This does NOT touch what the GENERATOR sees —
# gen_png still receives the full-resolution refs, where packaging and skin detail decide the
# output. The rubric only asks whether a wordmark reads the same and where a head points; 768px
# answers both. Copies are cached on (name, mtime, size, budget) so a re-roll re-encodes nothing.
JUDGE_PAYLOAD_BYTES = 280 * 1024      # under the measured ~300KB tunnel ceiling
JUDGE_CACHE = os.path.join(OUT_ROOT, "judge_refs")


def judge_ref(path, budget):
    """A copy of `path` small enough to survive the tunnel. Returns `path` itself if it already
    is, or if Pillow is unavailable — a full-size ref that might time out still beats no gate."""
    try:
        if os.path.getsize(path) <= budget:
            return path
        st = os.stat(path)
    except OSError:
        return path
    key = re.sub(r"[^A-Za-z0-9]+", "-", os.path.basename(path))[:60]
    dest = os.path.join(JUDGE_CACHE, f"{key}-{int(st.st_mtime)}-{st.st_size}-{budget}.jpg")
    if os.path.exists(dest):
        return dest
    try:
        from PIL import Image
        os.makedirs(JUDGE_CACHE, exist_ok=True)
        im = Image.open(path).convert("RGB")
        for edge, q in ((768, 80), (640, 72), (512, 65), (448, 60)):
            small = im.copy()
            small.thumbnail((edge, edge), Image.LANCZOS)
            small.save(dest, "JPEG", quality=q, optimize=True)
            if os.path.getsize(dest) <= budget:
                break
        return dest
    except Exception as exc:                                   # noqa: BLE001 — never block the gate
        print(f"  ⚠ judge-ref downscale failed for {path} ({exc}) — sending it full size", flush=True)
        return path


def judge_images(webp_path, refs):
    """Candidate first (the rubric says "the FIRST image"), then refs inside the byte budget."""
    if not refs:
        return [webp_path]
    try:
        spent = os.path.getsize(webp_path)
    except OSError:
        spent = MAX_BYTES
    per_ref = max((JUDGE_PAYLOAD_BYTES - spent) // len(refs), 50 * 1024)
    return [webp_path] + [judge_ref(r, per_ref) for r in refs]


# The judge ladder, most-preferred first. Fixed and declared HERE, not chosen per call.
#
# On 2026-08-12 both scheduled runs died on the same thing: gem9's default `ag/gemini-3.1-pro-low`
# returned 429 RESOURCE_EXHAUSTED for the whole run (every `ag/*` model did), qc fails CLOSED on a
# face, so the hero could not be verified at all and the run burned all three rolls on a judge that
# never answered. `cx/gpt-5.6-luna` answered the identical rubric on the same subscription at $0.
#
# The 08:47 run flagged the real hazard in its own report: "swapping the judge model changes gate
# strictness, so I did not keep swapping until something passed." That is why this is a LADDER and
# not a retry loop. A verdict — PASS or FAIL — ends it immediately; we step down only when the judge
# did not answer at all (429 / 5xx / timeout / no VERDICT line), which is a transport failure, not a
# lenient judge. Worst case is two calls per image, in a fixed order, and the reason string names
# which judge actually spoke so a verdict is never anonymous.
QC_JUDGES = ["ag/gemini-3.1-pro-low", "cx/gpt-5.6-luna"]


def qc_judges():
    """Ladder for this process. GEM9_MODEL moves a judge to the front; it does not disable the
    fallback — GEM9_MODEL is a global gem9 variable shared with every other caller, so honouring
    it as a hard pin would let an unrelated `export` silently take the gate back to one judge."""
    pinned = os.environ.get("GEM9_MODEL")
    if not pinned:
        return list(QC_JUDGES)
    return [pinned] + [m for m in QC_JUDGES if m != pinned]


def run_judge(model, prompt, images):
    """One rubric call. Returns (verdict_or_None, raw_output). None means the judge did not
    answer — caller steps down the ladder; it must NOT be read as a FAIL."""
    try:
        res = subprocess.run([GEM9, "-m", model, "-p", prompt, *images],
                             capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return None, "timed out after 180s"
    out = (res.stdout or "") + (res.stderr or "")
    m = re.search(r"VERDICT:\s*(PASS|FAIL[^\n]*)", out)
    return (m.group(1) if m else None), out


def qc_gem9(webp_path, refs, is_ugc, has_persona, angle_phrase=None):
    """Vision QC via gem9 (9router subscription — per PATI rule, never per-token).
    Returns (passed, reason)."""
    rubric = ["You are a strict image QC gate for a DTC supplement blog. Compare the FIRST image "
              "(the generated candidate) against the other image(s) (references). Answer each check, "
              "then end with exactly 'VERDICT: PASS' or 'VERDICT: FAIL - <short reason>'.",
              "1. PACKAGING (the strictest check). If a package is visible, compare it element by "
              "element with the reference: (a) same format — pouch vs bottle vs jar vs dropper; "
              "(b) same dominant color; (c) the brand wordmark present, in the same place, reading "
              "the same; (d) same product title; (e) same badges/benefit rows in the same layout; "
              "(f) no text, stat badge, or graphic that is NOT on the reference package. Any "
              "mismatch in a-f = FAIL, and say which letter failed. Soft or garbled MICRO-text "
              "(fine print you could not read on the reference either) is an accepted generator "
              "artifact — not a FAIL on its own.",
              "1b. If the candidate shows a package but NO reference image contains that package, "
              "answer 'VERDICT: FAIL - no packaging reference to compare against'."]
    if is_ugc:
        rubric.append("2. Does it read as a casual real-phone UGC snapshot (imperfect framing, "
                      "available light, lived-in scene) and NOT a studio/stock photo? Glossy "
                      "stock look = FAIL.")
    rubric.append("3. Any rendered text/watermark/caption that is not on the product label = FAIL.")
    rubric.append("3b. Any product package in frame that is NOT the referenced product = FAIL. "
                  "An invented brand name on a jar, tub, bottle or pouch counts, even a plausible "
                  "one — name it in the reason.")
    if not has_persona:
        # 2026-10-06: no-face lane (and the MacBook failover lane, where personas/index.json is not
        # synced with the Mini) — a face that slipped in is an unapproved/unaccounted persona.
        rubric.append("4. FACES. This image must contain NO recognizable human face (hands, arms, "
                      "a back or a cropped body below the eyes are fine). Any recognizable face, "
                      "even partly turned or in the background = FAIL - face in frame.")
    if has_persona:
        # Check 5 briefly FAILed an image whose person was recognisably the reference individual.
        # That was the right gate for a bank of one-shot faces; it is the wrong gate for the bank
        # Kevin reaffirmed on 2026-08-10, which is built on identity PERSISTENCE — the same model
        # returning at a new angle. Under that design check 5 would fail every single generation,
        # so it is removed rather than left to be silently overridden at the call site.
        # What it was protecting against has NOT gone away: the exposure is a publicity-rights
        # question, it is recorded in CLAUDE.md, and Kevin has accepted it. A vision rubric was
        # never the right place to litigate it — it belongs at intake, in which photographs enter
        # the bank at all.
        rubric.append("4. Does the person look like a natural real human (no plastic skin, no dead "
                      "eyes, no warped hands), and do they read as the SAME PERSON as the "
                      "reference photograph — same apparent age, build, hair and face? = FAIL if not.")
        if angle_phrase:
            rubric.append("5. HEAD ANGLE. The brief for this image was: %s. Look at where the "
                          "HEAD points, not where the eyes point. Answer these three in order "
                          "before you decide: (a) which edge of the image does the NOSE point "
                          "toward — left, right, or straight at the lens? (b) which ear is nearest "
                          "the camera, and on which side of the head silhouette does it sit? "
                          "(c) is the chin level, dipped, or raised? Then compare all three with "
                          "the brief. Do NOT translate 'their left' in your head — the brief "
                          "already tells you what it looks like in the frame; a mirrored render "
                          "is the exact failure this check exists to catch. If the head is squared "
                          "to the lens when the brief asked for a turn, or turned when the brief "
                          "asked for square, or turned toward the WRONG edge of the frame, or the "
                          "chin is level when the brief asked it dipped or raised = FAIL, and say "
                          "what you actually see for (a), (b) and (c). This one matters: the angle "
                          "is spent for this model whether or not it was rendered, so a wrong "
                          "angle costs a real angle and gets a repeat that the bookkeeping will "
                          "show as unique." % angle_phrase)
    prompt, images, tried = "\n".join(rubric), judge_images(webp_path, refs), []
    for model in qc_judges():
        verdict, out = run_judge(model, prompt, images)
        if verdict:
            # Name the judge. Two models can sit behind one verdict now, and a FAIL reason that
            # does not say who wrote it cannot be argued with afterwards.
            return verdict.startswith("PASS"), f"{verdict} [{model}]"
        tried.append(f"{model}: {out.strip()[-100:]}")
    # Every judge on the ladder stayed silent — the gate did not run.
    # Fail OPEN for the cosmetic checks — a 9router hiccup should not abort a whole run over
    # framing. Fail CLOSED when a face is in frame. The reason changed on 2026-08-10 but the
    # answer did not: the face branch now carries the head-angle check, and a face angle is
    # spent for that model the moment it is committed, whether or not the generator actually
    # rendered it. So an unverified face image does not cost a re-roll, it costs one of 21
    # irreplaceable angles — and leaves a repeat that the bookkeeping will report as unique.
    # A gate that returns PASS when it did not run is not a gate.
    detail = " | ".join(tried)
    if has_persona:
        return False, f"qc-inconclusive with a face in frame ({detail})"
    return True, f"qc-inconclusive ({detail})"


CURATED_ROOT = os.path.expanduser("~/genseo/product_refs")


def curated_ref(handle):
    """A hand-cropped, verified pack shot for this SKU, if one exists.

    Every WellnessNest PDP image is a marketing composite — some contain no
    package at all. Ticket #3 fed `--product-ref <handle>:1` (an "AFTER 2 WEEKS"
    graphic with no pouch in it) and the generator invented a white pouch,
    copying that graphic's stat badges onto the fake label. The curated crop is
    the only trustworthy packaging source; the PDP index path is the fallback.
    Returns (png_path, meta_dict) or (None, None)."""
    import json
    if handle and not brand_rules.product_allowed(handle):
        return None, None
    png = os.path.join(CURATED_ROOT, f"{handle}.png")
    if not os.path.exists(png):
        return None, None
    meta_path = os.path.join(CURATED_ROOT, f"{handle}.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    return png, meta


def fetch_product_ref(handle_spec):
    """--product-ref <handle>[:index] → the real packaging as a PNG ref.

    A curated crop in ~/genseo/product_refs wins over any PDP index, because
    PDP images are composites and an index can silently point at one with no
    package in it."""
    import io
    import json
    import urllib.request
    from PIL import Image
    raw, _, idx = handle_spec.partition(":")
    try:
        handle, how = brand_rules.resolve_handle(raw)
    except brand_rules.GuardError as e:
        sys.exit(f"✗ AgeAura guard: {e}")
    if how == "force":
        print(f"  AgeAura guard: '{raw}' locked to {handle}", flush=True)
    idx = int(idx or 0)
    png, _meta = curated_ref(handle)
    if png:
        if idx:
            print(f"  (ignoring :{idx} — using the curated pack ref for {handle})", flush=True)
        return png
    if not brand_rules.product_allowed(handle):
        sys.exit(f"✗ AgeAura guard: refusing PDP download for {handle}")
    print(f"  ⚠ no curated pack ref for {handle} — falling back to PDP image [{idx}]. "
          f"VERIFY the package is actually in that image before trusting the output.", flush=True)
    dest = os.path.join(OUT_ROOT, f"ref_{re.sub(r'[^a-z0-9-]', '-', handle)}_{idx}.png")
    if os.path.exists(dest):
        return dest
    p = json.load(urllib.request.urlopen(f"https://wellnessnest.co/products/{handle}.js"))
    if idx >= len(p["images"]):
        sys.exit(f"✗ product {handle} has only {len(p['images'])} images (asked for index {idx})")
    url = "https:" + p["images"][idx] + "&width=1200"
    req = urllib.request.Request(url, headers={"Accept": "image/webp", "User-Agent": "Mozilla/5.0"})
    Image.open(io.BytesIO(urllib.request.urlopen(req).read())).convert("RGB").save(dest)
    return dest


def _ensure_serve(env):
    """ima2 gen needs the local `ima2 serve` daemon (holds the ChatGPT OAuth
    session, image endpoint at 127.0.0.1:3333). Unattended daily runs can't
    assume it's up, so probe the port and start it if needed."""
    import socket
    import time
    with socket.socket() as s:
        s.settimeout(2)
        if s.connect_ex(("127.0.0.1", 3333)) == 0:
            return
    subprocess.Popen([IMA2, "serve"], env=env,
                     stdout=open("/tmp/ima2-serve-genseo.log", "a"),
                     stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(15):  # re-probe up to 30s instead of hoping a fixed sleep is enough
        time.sleep(2)
        with socket.socket() as s:
            s.settimeout(2)
            if s.connect_ex(("127.0.0.1", 3333)) == 0:
                return
    sys.exit("✗ ima2 serve did not come up within 30s — check /tmp/ima2-serve-genseo.log (OAuth session may need re-login)")


# 2026-10-12 #CA1009-3 (daily run 4, 18:21–18:41 ICT): ima2 printed
# "Responses stream returned an error" and gen_png exited on that first try.
# deploy/grokbot-genseo-daily.sh then counts a ticket that puts nothing new
# live, and stops the day after three of those. A dropped stream, a 429/5xx,
# a timeout, or a reset is the upstream blipping — retry a few times, briefly.
# 2026-10-19 #CA1016-7: ima2 3.23.1 printed a different line for the same
# blip, "Responses request failed before receiving a response" with
# "Hint: Network/proxy failed" (code NETWORK_FAILED, HTTP 502). That
# wording did not match the 2026-10-12 pattern, so gen_png exited on the
# first try and the wrapper stopped after three no-publish runs.
# Auth, content policy, and a bad request are the same call again: do not
# retry them, and do not retry an error we cannot classify. ad_assets.py's
# 3-try loop is a different gate (wrong aspect ratio after a file landed).
# It calls gen_png, so it inherits this retry; it does not replace it.
# QC re-rolls (exit 2, max 2) stay in the caller. No second image vendor.
#
# The ticket cap is GENSEO_TICKET_TIMEOUT_SEC (5400) in
# deploy/grokbot-genseo-daily.sh. Three full subprocess timeouts on a hero
# and three inline images are about 78 minutes, which leaves the writer
# nothing. One gen_png call may spend IMA2_CALL_BUDGET_SEC. Four of those
# stay under half the cap. Fast failures still use the 5s/15s backoff; the
# backoff total is 20s. A TimeoutExpired kills the ima2 process tree before
# that sleep: subprocess timeout kills only the direct child, and a setsid
# worker would otherwise be reparented to init while this process is in
# time.sleep, where the ticket tree-kill cannot see it.
IMA2_ATTEMPTS = 3
IMA2_BACKOFF_SEC = (5, 15)  # after attempt 1, then after attempt 2
IMA2_MIN_PNG_BYTES = 30_000
TICKET_CAP_SEC = 5400
IMA2_CALL_BUDGET_SEC = 600
IMA2_TIMEOUT_PAD_SEC = 30
_IMA2_KILL_GRACE_SEC = 0.2

# Status codes count only when they are written as an HTTP failure. A dose
# ("500 mg") or our own "--timeout 360" flag must not look transient.
_IMA2_TRANSIENT_RE = (
    re.compile(r"responses stream returned an error", re.I),
    re.compile(r"responses request failed before receiving a response", re.I),
    re.compile(r"oauth image request failed before receiving a response", re.I),
    re.compile(r"\bNETWORK_FAILED\b"),
    re.compile(r"network/proxy failed", re.I),
    re.compile(r"\b(?:response|responses|event) stream\b[^.\n]{0,80}\b(?:error|interrupted|closed|failed)\b", re.I),
    re.compile(r"\bstream (?:error|interrupted|closed|failed|disconnected)\b", re.I),
    re.compile(r"\b(?:econnreset|econnrefused|etimedout|econnaborted|epipe|enotconn|enetunreach|ehostunreach)\b", re.I),
    re.compile(r"connection (?:reset|refused|aborted)|broken pipe|socket hang up|peer closed connection|server disconnected", re.I),
    re.compile(r"timed out|timeout exceeded|deadline exceeded|gateway timeout|read timeout|i/o timeout|request timeout", re.I),
    re.compile(r"\b(?:http|status|error|code)[:\s/]+(429|500|502|503|504|529)\b", re.I),
    re.compile(r"\b(?:internal server error|bad gateway|service unavailable|gateway timeout|too many requests)\b", re.I),
    re.compile(r"\b(?:temporarily unavailable|upstream (?:error|reset)|network error|fetch failed|rate limit)\b", re.I),
    re.compile(r"APIConnectionError|APITimeoutError|APIConnectionTimeoutError|ConnectError|ReadTimeout|RemoteProtocolError"),
    re.compile(r"\boverloaded\b", re.I),
)
_IMA2_PERMANENT_RE = (
    re.compile(r"\b(?:unauthorized|unauthorised|authentication failed|invalid api key|invalid_api_key|not logged in|login required|re-login|oauth session expired)\b", re.I),
    re.compile(r"\b(?:http|status|error|code)[:\s/]+(400|401|402|403)\b", re.I),
    re.compile(r"\b(?:bad request|invalid request|invalid_request_error|invalid_request)\b", re.I),
    re.compile(r"\b(?:forbidden|payment required)\b", re.I),
    re.compile(r"\b(?:content policy|content_policy(?:_violation)?|safety system|moderation blocked)\b", re.I),
    re.compile(r"\b(?:insufficient_quota|quota exceeded|billing hard limit)\b", re.I),
)


def ima2_error_class(text):
    """Classify an ima2 failure as 'transient', 'permanent', or 'unknown'.

    Permanent wins when both match, so a stream line that also carries a 401
    or a content-policy refusal is not retried. Callers that see 'unknown'
    must not retry: an unrecognized refusal repeated three times still fails,
    and it spends three generations to do it.
    """
    blob = text or ""
    if any(pat.search(blob) for pat in _IMA2_PERMANENT_RE):
        return "permanent"
    if any(pat.search(blob) for pat in _IMA2_TRANSIENT_RE):
        return "transient"
    return "unknown"


def _ima2_chosen_output(res):
    """stderr when ima2 wrote one, otherwise stdout. Matches the old tail source,
    except blank stderr no longer hides a real error on stdout."""
    err = (getattr(res, "stderr", None) or "").strip()
    out = (getattr(res, "stdout", None) or "").strip()
    return err or out


def _ima2_tail(text, returncode):
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    if lines:
        return " | ".join(lines[-3:])
    if returncode is None:
        return "no output"
    return "exit %s, no output" % returncode


def _ima2_give_up(attempt, last_tail, why):
    print(f"   ✗ ima2 attempt {attempt}/{IMA2_ATTEMPTS}: {last_tail} — {why}", flush=True)
    sys.exit("✗ ima2 generation failed: " + last_tail)


def _ppid_map():
    """pid -> parent pid. Linux /proc, otherwise ps (macOS has no /proc)."""
    mapping = {}
    if os.path.isdir("/proc"):
        for ent in os.listdir("/proc"):
            if not ent.isdigit():
                continue
            path = "/proc/%s/status" % ent
            try:
                fh = open(path, encoding="utf-8", errors="replace")
            except OSError:
                continue
            try:
                for line in fh:
                    if line.startswith("PPid:"):
                        mapping[int(ent)] = int(line.split()[1])
                        break
            finally:
                fh.close()
        if mapping:
            return mapping
    for argv in (
        ["ps", "-ax", "-o", "pid=,ppid="],
        ["/bin/ps", "-ax", "-o", "pid=,ppid="],
        ["/usr/bin/ps", "-ax", "-o", "pid=,ppid="],
    ):
        try:
            out = subprocess.check_output(argv, stderr=subprocess.DEVNULL, text=True)
        except (OSError, subprocess.CalledProcessError):
            continue
        mapping = {}
        for line in out.splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                mapping[int(parts[0])] = int(parts[1])
        if mapping:
            return mapping
    return mapping


def _descendant_pids(seed):
    """Seed plus every process whose parent chain still reaches it."""
    try:
        seed = int(seed or 0)
    except (TypeError, ValueError):
        return []
    me = os.getpid()
    if seed <= 1 or seed == me:
        return []
    ppid = _ppid_map()
    out = [seed]
    seen = {seed}
    for _guard in range(40):
        grew = False
        for pid, parent in list(ppid.items()):
            if pid in seen or pid <= 1 or pid == me:
                continue
            if parent in seen:
                seen.add(pid)
                out.append(pid)
                grew = True
        if not grew:
            break
    return out


def _pid_alive(pid):
    if not pid or pid <= 1 or pid == os.getpid():
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _signal_pids(sig, pids):
    me = os.getpid()
    seen = set()
    for pid in pids:
        if not pid or pid <= 1 or pid == me or pid in seen:
            continue
        seen.add(pid)
        try:
            os.kill(pid, sig)
        except OSError:
            pass


def _kill_pid_tree(seed):
    """TERM, then KILL, seed and any process still parented under it.

    Snapshot before the first signal. A setsid grandchild stays in the set
    until its parent dies; killing the parent first would reparent it to
    init and the later ticket tree-kill would miss it during backoff sleep.
    """
    wave = _descendant_pids(seed)
    if not wave:
        try:
            seed = int(seed or 0)
        except (TypeError, ValueError):
            return
        if seed <= 1 or seed == os.getpid():
            return
        wave = [seed]
    _signal_pids(signal.SIGTERM, wave)
    time.sleep(_IMA2_KILL_GRACE_SEC)
    kill_set = list(wave)
    for pid in wave:
        if _pid_alive(pid):
            kill_set.extend(_descendant_pids(pid))
    _signal_pids(signal.SIGKILL, kill_set)


def _close_pipes(proc):
    for stream in (proc.stdout, proc.stderr, proc.stdin):
        if stream is None:
            continue
        try:
            stream.close()
        except OSError:
            pass


def _run_ima2(cmd, env, timeout_s):
    """Run one ima2 generation. On timeout, kill its process tree first.

    subprocess.run kills only the direct child, and only after the
    TimeoutExpired is raised from inside run(). Doing it here means the
    setsid worker is still parented under ima2 when we snapshot it.
    """
    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        try:
            out, err = proc.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired as exc:
            _kill_pid_tree(proc.pid)
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            raise subprocess.TimeoutExpired(
                cmd, timeout_s, output=exc.output, stderr=exc.stderr)
        return subprocess.CompletedProcess(cmd, proc.returncode, out, err)
    finally:
        _close_pipes(proc)


def _attempt_limit(timeout, remaining):
    """Seconds this attempt may block. Never past the call budget."""
    if remaining < 1:
        return 0
    return min(timeout + IMA2_TIMEOUT_PAD_SEC, int(remaining))


def gen_png(prompt, size, out_png, refs, timeout=360, sleeper=None, clock=None):
    """Render one PNG via the local ima2 binary.

    sleeper defaults to time.sleep. clock defaults to time.monotonic.
    Tests pass their own so the backoff does not actually wait and so a
    call-budget check can run without burning the subprocess timeout.
    """
    cmd = [IMA2, "gen", prompt + PROMPT_SUFFIX, "-q", "medium", "-s", size,
           "-o", out_png, "--timeout", str(timeout)]
    for r in refs:
        if not os.path.exists(r):
            sys.exit(f"✗ ref image not found: {r}")
        cmd += ["--ref", r]
    # 2026-10-06 (MacBook failover): ima2 3.x has no default model until one is set, so name the
    # lane explicitly. GENSEO_IMA2_PROVIDER/MODEL override; default = ChatGPT OAuth (subscription, $0).
    prov = os.environ.get("GENSEO_IMA2_PROVIDER", "oauth")
    model = os.environ.get("GENSEO_IMA2_MODEL", "gpt-6-sol")
    if prov:
        cmd += ["--provider", prov]
    if model:
        cmd += ["--model", model]
    env = os.environ.copy()
    env["PATH"] = os.path.dirname(IMA2) + ":" + env.get("PATH", "")
    pause = time.sleep if sleeper is None else sleeper
    now = time.monotonic if clock is None else clock
    t0 = now()
    last_tail = "no output"
    for attempt in range(1, IMA2_ATTEMPTS + 1):
        remaining = IMA2_CALL_BUDGET_SEC - (now() - t0)
        if remaining < 1:
            _ima2_give_up(
                attempt,
                "%s (stopped at %ss call budget)" % (last_tail, IMA2_CALL_BUDGET_SEC),
                "call budget, not retrying",
            )
        if os.path.isfile(out_png):
            os.unlink(out_png)
        _ensure_serve(env)
        remaining = IMA2_CALL_BUDGET_SEC - (now() - t0)
        limit = _attempt_limit(timeout, remaining)
        if limit < 1:
            _ima2_give_up(
                attempt,
                "%s (stopped at %ss call budget)" % (last_tail, IMA2_CALL_BUDGET_SEC),
                "call budget, not retrying",
            )
        try:
            res = _run_ima2(cmd, env, limit)
        except subprocess.TimeoutExpired:
            last_tail = "timed out after %ss" % limit
            kind = "transient"
        else:
            chosen = _ima2_chosen_output(res)
            size_b = os.path.getsize(out_png) if os.path.isfile(out_png) else 0
            if res.returncode == 0 and size_b >= IMA2_MIN_PNG_BYTES:
                return
            last_tail = _ima2_tail(chosen, res.returncode)
            kind = ima2_error_class(chosen)
            # Exit 0 with no usable file and no refusal text is a truncated
            # write. A policy line on that same output stays permanent.
            if res.returncode == 0 and size_b < IMA2_MIN_PNG_BYTES:
                note = "output missing" if size_b == 0 else (
                    "output %dB < %dB" % (size_b, IMA2_MIN_PNG_BYTES))
                last_tail = ("%s: %s" % (note, last_tail)) if chosen else note
                if kind == "unknown":
                    kind = "transient"
        if kind == "transient" and attempt < IMA2_ATTEMPTS:
            wait = IMA2_BACKOFF_SEC[min(attempt - 1, len(IMA2_BACKOFF_SEC) - 1)]
            elapsed = now() - t0
            # Do not sleep, and do not start another attempt, when this call
            # has already used the budget. The ticket cap still kills this
            # process if it is inside pause(); the budget is what keeps four
            # images from arriving there.
            if elapsed + wait >= IMA2_CALL_BUDGET_SEC:
                _ima2_give_up(
                    attempt,
                    "%s (stopped at %ss call budget)" % (last_tail, IMA2_CALL_BUDGET_SEC),
                    "call budget, not retrying",
                )
            print(f"   ✗ ima2 attempt {attempt}/{IMA2_ATTEMPTS}: {last_tail} "
                  f"— transient, retrying in {wait}s", flush=True)
            pause(wait)
            continue
        if kind == "permanent":
            why = "permanent, not retrying"
        elif kind != "transient":
            why = "not retrying"
        else:
            why = "transient, giving up"
        _ima2_give_up(attempt, last_tail, why)


def compress_webp(src_png, out_webp):
    """Quality ladder first, then width ladder — stop at the first result <80KB."""
    for width in (1200, 1000, 800, 640):
        for q in (80, 70, 60, 50, 40):
            res = subprocess.run(
                [CWEBP, "-q", str(q), "-resize", str(width), "0", src_png, "-o", out_webp],
                capture_output=True, text=True)
            if res.returncode == 0 and os.path.exists(out_webp) and os.path.getsize(out_webp) < MAX_BYTES:
                return os.path.getsize(out_webp), q, width
    sys.exit("✗ could not compress under 80KB even at q40/640px — simplify the image")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True, help="article slug (output folder name)")
    ap.add_argument("--name", required=True, help="image name, e.g. hero, fusiforce-lifestyle")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--ref", action="append", default=[], help="absolute path to a REAL product image (repeatable)")
    ap.add_argument("--product-ref", action="append", default=[],
                    help="<handle>[:index] — auto-download the live PDP pack shot as ref and lock "
                         "the prompt to that packaging (REQUIRED whenever the image shows a product)")
    ap.add_argument("--ugc", action="store_true",
                    help="i5.2 UGC lane: phone-snapshot suffix + anti-stock NEG bank + grain degrade "
                         "(see references/ugc-image-framework.md — inline article images use this)")
    ap.add_argument("--persona-ref", default=None,
                    help="absolute path to the APPROVED persona ref photo (~/genseo/personas/<handle>/ref.jpg). "
                         "Only personas Kevin approved through the one-time Pinterest gate — never a fresh face.")
    ap.add_argument("--face-angle", default=None,
                    help="face angle id from personas/taxonomy.json face_angle_values, e.g. "
                         "'3q-left+chin-down'. MANDATORY with --persona-ref. Kevin's hard rule: "
                         "one angle per model, once, ever — take it from persona_picker.py pick.")
    ap.add_argument("--qc", action="store_true",
                    help="vision QC via gem9 (9router): packaging/UGC/no-text/persona rubric; "
                         "FAIL prints the reason and exits 2 so the caller can re-roll")
    ap.add_argument("--square", action="store_true", help="1024x1024 instead of 1536x1024 landscape")
    a = ap.parse_args()
    try:
        a.prompt, a.product_ref = brand_rules.prepare_image_request(a.prompt, a.product_ref)
    except brand_rules.GuardError as e:
        sys.exit(f"✗ brand guard: {e}")

    for spec in a.product_ref:
        a.ref.append(fetch_product_ref(spec))
    if a.product_ref:
        # Prompt text overrides the ref image when they disagree, so state the real
        # packaging in words too — a prompt saying "white pouch" beat a pink-pouch ref.
        for spec in a.product_ref:
            _, meta = curated_ref(spec.partition(":")[0])
            if meta and meta.get("describe"):
                a.prompt += (f" The package in frame is {meta['describe']}. It is a "
                             f"{meta['format']}, {meta['color']} — never any other format or color.")
        a.prompt += PACK_FIDELITY
    if a.persona_ref:
        if not os.path.exists(a.persona_ref):
            sys.exit(f"✗ persona ref not found: {a.persona_ref} — persona bank lives in ~/genseo/personas/")
        if not a.face_angle:
            sys.exit("✗ --persona-ref requires --face-angle. Kevin's hard rule (2026-08-10) is one "
                     "face angle per model, once, ever — an image generated without a declared "
                     "angle cannot be checked against that history, and an unchecked angle is a "
                     "repeated angle waiting to happen. Get it from `persona_picker.py pick` "
                     "(fields hero_face_angle / inline_face_angle).")
        a.ref.append(a.persona_ref)
        angle_phrase = face_angle_phrase(a.face_angle, a.persona_ref)
        a.prompt += CAMERA_MATCH + FACE_ANGLE_CLAUSE.format(phrase=angle_phrase)
    else:
        if a.face_angle:
            sys.exit("✗ --face-angle without --persona-ref: there is no face to angle, and "
                     "recording the angle as spent would burn it for nothing.")
        angle_phrase = None
        a.prompt += NO_FACE_CLAUSE
    if a.ugc:
        a.prompt += UGC_SUFFIX + UGC_NEG
    else:
        # Every non-UGC call IS the hero lane (the framework gives all three inline images
        # --ugc), so the negatives belong to the LANE, not to whether a face is in frame.
        # Gating them on persona_ref left the no-face hero — the every-3rd-article branch the
        # picker now mandates, and the ONLY branch available while the bank is empty — with no
        # anti-stock negatives at all: the same hole, surviving in the one path that currently
        # carries every hero on the blog index.
        a.prompt += HERO_NEG

    slug = re.sub(r"[^a-z0-9-]", "-", a.slug.lower())
    name = re.sub(r"[^a-z0-9-]", "-", a.name.lower())
    out_dir = os.path.join(OUT_ROOT, slug)
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.join(out_dir, f"{name}.png")
    webp = os.path.join(out_dir, f"{name}.webp")

    size = "1024x1024" if a.square else "1536x1024"
    print(f"⏳ ima2 gen {name} ({size}, {len(a.ref)} ref{', UGC' if a.ugc else ''})...", flush=True)
    gen_png(a.prompt, size, png, a.ref)
    # Unconditional. Raw ima2 output is too HD-clean for anything we publish, and every
    # narrower rule tried here has leaked: gating on --ugc left all heroes glossy, then gating
    # on `ugc or persona_ref` still left the no-face hero glossy — and the no-face hero is what
    # the blog index shows whenever the bank can't fill the slot. There is no image in this
    # pipeline that wants the untouched render, so stop enumerating which ones do.
    degrade_grain(png)
    nbytes, q, width = compress_webp(png, webp)
    os.unlink(png)  # keep only the deliverable; the PNG is 10-20x the size
    if a.qc:
        passed, verdict = qc_gem9(webp, a.ref, a.ugc, bool(a.persona_ref), angle_phrase)
        print(f"QC → {verdict}")
        if not passed:
            sys.exit(2)  # caller re-rolls with the FAIL reason folded into the prompt (max 2)
    if a.persona_ref:
        # After QC, not before: a render that failed and was thrown away owes nobody a credit,
        # and a CREDITS.json naming a persona no surviving image used would quietly turn the
        # credits block into a list of everyone we happened to try.
        record_credit(out_dir, a.persona_ref)
    print(f"✓ {nbytes//1024}KB webp (q{q}, {width}px)")
    print(webp)


if __name__ == "__main__":
    main()

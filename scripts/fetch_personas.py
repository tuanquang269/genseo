#!/usr/bin/env python3
"""Source real-photograph faces for the GenSeo persona bank, from Flickr, under licence.

WHY THIS EXISTS. persona_picker.py rotates over a bank of four faces. On 2026-08-09 two of
them were flagged: f1-redshirt is 333x500 (0.17MP — an upscaled blur the moment ima2 uses it
as an anchor) and f3-silver carries "Chapin (c) 2016 Chapin Photography" burned into the
shirt. A third, f2-brunette, still sits in the bank marked "active" and carries
"(c) stefano borghetto" along its bottom edge; nothing caught it. All four record
`"license": "UNVERIFIED - sourced before the licence spine existed"`, which means the store
has been generating commercial marketing images anchored on photographs whose terms nobody
ever read back from an API.

Every one of those refs passed a human eyeball pass. That is the point: eyeballs are the
control that already failed, at n=4, and the taxonomy asks for 200. So the gates here are
mechanical and ordered cheapest-first, each candidate gets a printed one-line verdict, and
nothing reaches the bank that has not survived all five.

Yield is deliberately low. "CC0/CC-BY only" intersected with "one clearly visible,
unretouched, non-famous person in this age band, photographed by a camera" leaves single
digit percent of raw search results. That ratio is correct: the bank is the realism anchor
under every hero image on /blogs/news, and one AI-looking or watermarked face contaminates
every article it fronts.

    plan      what each taxonomy cell still needs (no network)
    fetch     fill ONE cell from Flickr
    verify    re-run the gates over the bank already on disk
    selftest  exercise the pure functions (no network, no API key)

Runs under /usr/bin/python3 (3.9): stdlib + PIL + numpy + requests, which is the only
interpreter on this Mac carrying all three (homebrew python3 has no PIL).
"""
import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time

import numpy as np
import requests
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONAS = os.path.join(ROOT, "personas")
INDEX = os.path.join(PERSONAS, "index.json")
TAXONOMY = os.path.join(PERSONAS, "taxonomy.json")
GEM9 = "/Users/kevinkreative/.local/bin/gem9"
FLICKR_REST = "https://api.flickr.com/services/rest/"

# The repo's split-interpreter trap has a sibling: genseo_config lives next to this file, so
# the scripts dir must be on sys.path BEFORE the import, or a run launched from any other cwd
# dies on ImportError. persona_picker.py sidesteps it by importing nothing; we cannot.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------------------------------------------
# LICENCE SPINE
# --------------------------------------------------------------------------------------
# Everything downstream of this bank is a derivative work used to sell supplements, so an
# acceptable licence has to permit commercial use AND derivatives, with no share-alike clause
# reaching back into the marketing output. Three ids clear that bar. The rejection reasons are
# kept as strings because the fetch log has to say WHICH licence it saw and why it refused it.
ALLOWED_LICENSES = {
    "9": {"name": "CC0 1.0",
          "url": "https://creativecommons.org/publicdomain/zero/1.0/",
          "attribution": False},
    "11": {"name": "CC BY 4.0",
           "url": "https://creativecommons.org/licenses/by/4.0/",
           "attribution": True},
    "4": {"name": "CC BY 2.0",
          "url": "https://creativecommons.org/licenses/by/2.0/",
          "attribution": True},
}
FORBIDDEN_LICENSES = {
    "0": "All Rights Reserved",
    "1": "CC BY-NC-SA 2.0 - NonCommercial (wellnessnest.co is a commercial store) + ShareAlike",
    "2": "CC BY-NC 2.0 - NonCommercial; the output is sold",
    "3": "CC BY-NC-ND 2.0 - NonCommercial + NoDerivatives; every hero image is a derivative",
    "5": "CC BY-SA 2.0 - ShareAlike would reach into commercial marketing output",
    "6": "CC BY-ND 2.0 - NoDerivatives; the whole pipeline makes derivative works",
    "7": "'No known copyright restrictions' - not a CC grant. It is an archive-institution flag, "
         "provisioned to museums and libraries, and it skews to notable people and historical material",
    "8": "'United States Government Work' - not a CC instrument, provisioned to federal bodies; "
         "skews to officials, military and press events",
    "10": "Public Domain Mark - a label asserting a belief about status, carrying no warranty and no grant",
    "12": "CC BY-SA 4.0 - ShareAlike",
}
LICENSE_SEARCH_PARAM = "9,11,4"  # order matters only cosmetically; the gate re-checks per photo
ALLOWED_LICENSE_NAMES = set(v["name"] for v in ALLOWED_LICENSES.values())

# --------------------------------------------------------------------------------------
# ACCEPTANCE THRESHOLDS
# --------------------------------------------------------------------------------------
MIN_MEGAPIXELS = 1.0
MIN_SHORT_EDGE = 800          # f1-redshirt is 333x500; this floor is why it would be refused
DHASH_MAX_DISTANCE = 8
WM_WORK_EDGE = 720            # watermark screen works on a 720px-long-edge copy
WM_EDGE_THRESHOLD = 40        # local max-min contrast that counts as a "stroke"
WM_FLAT_STD = 14.0            # background smoothness under the strokes
WM_MIN_DENSITY = 0.020        # stroke density inside a corner/edge band
WM_MIN_RATIO = 4.0            # ...relative to the picture's interior
WM_MIN_ROW_COVERAGE = 0.30    # ...and arranged as a horizontal line, the way text is
VISION_TIMEOUT = 180
VISION_INFRA_ABORT = 5        # consecutive gem9/9router failures that end the run
MIN_APPARENT_AGE = 18         # absolute floor — never source a face that could read as a minor
MAX_AGE_INTERVAL = 15         # a wider estimate than this is a hedge, not an answer


class _AbortRun(Exception):
    """Internal: unwind cmd_fetch's nested loops while still hitting the index-commit finally."""

# --------------------------------------------------------------------------------------
# QUERY BANK  --  tune these tables, not the composer below.
# --------------------------------------------------------------------------------------
# Flickr's index answers to what a photographer TITLED and TAGGED a picture, which is scene
# language, not census language. "Hispanic male 30-39" returns keyword-spammed stock and
# conference badges; "man cooking kitchen candid" returns photographs of people. Every phrase
# here is therefore natural-language, and demographic terms appear only as the light hint a
# photographer might plausibly have typed.
SUBJECT_WORDS = {
    ("male", "20-29"): ["young man", "guy in his twenties", "man in his 20s"],
    ("male", "30-39"): ["man in his thirties", "man in his 30s", "dad in his thirties"],
    ("male", "40-49"): ["man in his forties", "man in his 40s", "middle aged man"],
    ("male", "50-59"): ["man in his fifties", "man in his 50s", "greying man"],
    ("male", "60-70"): ["man in his sixties", "older man", "retired man"],
    ("female", "20-29"): ["young woman", "woman in her twenties", "woman in her 20s"],
    ("female", "30-39"): ["woman in her thirties", "woman in her 30s", "mother in her thirties"],
    ("female", "40-49"): ["woman in her forties", "woman in her 40s", "middle aged woman"],
    ("female", "50-59"): ["woman in her fifties", "woman in her 50s", "silver haired woman"],
    ("female", "60-70"): ["woman in her sixties", "older woman", "grandmother portrait"],
}
SCENE_PHRASES = {
    "20-29": ["kitchen candid", "gym natural light", "walking outdoors portrait",
              "coffee shop candid", "backyard afternoon", "home portrait available light"],
    "30-39": ["kitchen candid", "workshop working", "running trail portrait",
              "market shopping candid", "home office natural light", "park weekend candid"],
    "40-49": ["kitchen candid", "garage workshop", "hiking trail portrait",
              "garden weekend", "home portrait available light", "cycling outdoors candid"],
    "50-59": ["kitchen candid", "gardening portrait", "allotment working",
              "walking outdoors natural light", "workshop woodworking", "home portrait window light"],
    "60-70": ["gardening portrait", "kitchen candid", "allotment working",
              "walking outdoors natural light", "sitting at home window light", "market candid"],
}
# Gate 5 records apparent ethnicity but does NOT reject on it (that is not in the rubric), so
# these hints are the only steering the cell quota gets. An empty string means "unhinted" —
# Flickr's default result skew already lands on the wh cells, and forcing the term there just
# pulls in costume and heritage-festival pictures.
ETHNICITY_HINTS = {
    "wh": {"male": [""], "female": [""]},
    "hl": {"male": ["latino", "hispanic", "mexican american"],
           "female": ["latina", "hispanic", "mexican american"]},
    "bl": {"male": ["black man", "african american"], "female": ["black woman", "african american"]},
    "as": {"male": ["asian american", "south asian", "chinese american"],
           "female": ["asian american", "south asian", "chinese american"]},
    "mx": {"male": ["mixed race", "middle eastern", "native american"],
           "female": ["mixed race", "middle eastern", "native american"]},
}
# Hand-tuned per-cell lists win over the composer. Fill one in whenever a cell's composed
# queries prove barren — that is cheaper than widening the composer for everybody.
QUERY_OVERRIDES = {}

CAMERA_NOTES = ("indoor/ambient available light, real skin texture — always camera-match; "
                "ALWAYS feed THIS ref.jpg, never a previous gen (ima2 i2i drifts identity)")


# --------------------------------------------------------------------------------------
# house-style IO (mirrors persona_picker.py: never guess past a corrupt state file)
# --------------------------------------------------------------------------------------
def _load(path, what):
    try:
        with open(path) as fh:
            return json.load(fh)
    except FileNotFoundError:
        sys.exit("✗ %s missing: %s — the bank is not initialised" % (what, path))
    except json.JSONDecodeError as exc:
        sys.exit("✗ %s is corrupt (%s): %s — restore from git, do NOT hand-edit mid-run"
                 % (what, exc, path))


def _atomic_write(path, doc):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(doc, fh, indent=1)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def api_key():
    """FLICKR_API_KEY, else the flickr_api_key field of the shared GenSeo config.

    genseo_config is imported lazily: it calls sys.exit() at module scope when the Shopify
    config is absent, and `plan`/`verify`/`selftest` need neither Shopify nor Flickr."""
    k = os.environ.get("FLICKR_API_KEY", "").strip()
    if k:
        return k
    cfg_path = os.path.expanduser(os.environ.get("GENSEO_CONFIG", "~/.genseo/shopify_token.json"))
    try:
        import genseo_config
        cfg_path = genseo_config.CONFIG_PATH
    except SystemExit:
        pass  # no Shopify config; the file path below is still the right place to be told about
    try:
        with open(cfg_path) as fh:
            k = (json.load(fh).get("flickr_api_key") or "").strip()
    except (OSError, json.JSONDecodeError):
        k = ""
    if not k:
        sys.exit("✗ no Flickr API key. Either:\n"
                 "    export FLICKR_API_KEY=...\n"
                 "  or add a \"flickr_api_key\" field to %s\n"
                 "  Get one at https://www.flickr.com/services/apps/create/apply/ "
                 "(non-commercial key is fine; the LICENCE of each photo is what governs use, "
                 "not the key tier). Never commit it." % cfg_path)
    return k


# --------------------------------------------------------------------------------------
# GATE 1 — licence
# --------------------------------------------------------------------------------------
def gate_license(photo):
    """Read the licence back from the response; never assume the search filter held.
    Returns (license_id, info_or_None, reason)."""
    lic = str(photo.get("license", "")).strip()
    if lic in ALLOWED_LICENSES:
        return lic, ALLOWED_LICENSES[lic], ""
    known = FORBIDDEN_LICENSES.get(lic)
    if known:
        return lic, None, "licence %s forbidden: %s" % (lic, known)
    return lic, None, ("licence %r is not a licence id this script knows — refusing rather than "
                       "guessing what it permits" % lic)


# --------------------------------------------------------------------------------------
# GATE 2 — resolution
# --------------------------------------------------------------------------------------
def meets_resolution(w, h):
    return (w * h) / 1e6 >= MIN_MEGAPIXELS and min(w, h) >= MIN_SHORT_EDGE


def sizes_from_extras(photo):
    """(area, w, h, url, label) candidates the search response already gave us."""
    out = []
    for suf, label in (("o", "original"), ("l", "large-1024")):
        u, w, h = photo.get("url_" + suf), photo.get("width_" + suf), photo.get("height_" + suf)
        try:
            if u and int(w) and int(h):
                out.append((int(w) * int(h), int(w), int(h), u, label))
        except (TypeError, ValueError):
            continue
    return out


def largest_size(photo, key, session, allow_getsizes=True, sleep=0.0):
    """Largest DOWNLOADABLE size. The extras list only carries url_l (1024 long edge, which is
    0.7MP on a 3:2 frame and fails the floor) and url_o (present only when the owner allows
    original download), so anything in between needs flickr.photos.getSizes."""
    cands = sizes_from_extras(photo)
    best = max(cands) if cands else None
    if best and meets_resolution(best[1], best[2]):
        return best
    if not allow_getsizes:
        return best
    # url_l is 1024 on the long edge = 0.70MP on a 3:2 frame, so it never clears the floor and
    # url_o is absent whenever the owner blocks original download — meaning this fires for MOST
    # candidates. That is one extra API call each, and --sleep only throttled search pages.
    # Unthrottled it is the fastest way to hit Flickr's hourly key limit.
    if sleep:
        time.sleep(sleep)
    # Do NOT swallow this. Returning `best` on a throttle made every candidate report as
    # "1024x683 = 0.70MP, below floor" — 400 plausible resolution rejections and no hint
    # anywhere that the API was refusing us, so the natural response is to re-run and
    # deepen the throttle. Let it surface as an api failure.
    data = flickr_call(session, "flickr.photos.getSizes", key, photo_id=photo["id"])
    for s in (data.get("sizes", {}) or {}).get("size", []) or []:
        try:
            w, h = int(s["width"]), int(s["height"])
        except (KeyError, TypeError, ValueError):
            continue
        if s.get("media") == "photo" or "source" in s:
            cands.append((w * h, w, h, s["source"], s.get("label", "?")))
    return max(cands) if cands else None


# --------------------------------------------------------------------------------------
# GATE 3 — burned-in text screen
# --------------------------------------------------------------------------------------
# THIS IS A SCREEN, NOT A PROOF. It looks for what a credit line physically is: thin
# high-contrast strokes sitting on a locally smooth background, bunched into a corner or edge
# band, arranged as a horizontal run. That shape is why it does not fire on m1-stubble's
# striped shirt (high contrast, but the background under it is not smooth) and does fire on
# f2-brunette's "(c) stefano borghetto". Measured against the legacy bank on 2026-08-09 it
# also MISSED f3-silver's "Chapin" script watermark: a script face over hair-on-bokeh sits
# below the density threshold, and raising the threshold to catch it flags clean portraits.
# The vision gate is the real check; this one exists to avoid paying for a model call on an
# image that is obviously stamped.
def _box_mean(a, r):
    """Mean over a (2r+1)^2 window, integral-image style — no scipy on this interpreter."""
    a = a.astype(np.float32)
    k = 2 * r + 1
    integral = np.pad(a, r + 1, mode="edge").cumsum(0).cumsum(1)
    h, w = a.shape
    y, x = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
    return (integral[y + k, x + k] - integral[y, x + k] - integral[y + k, x] + integral[y, x]) / float(k * k)


def text_mask(img):
    """Boolean mask of pixels that look like rendered text: high local contrast on flat ground."""
    scale = float(WM_WORK_EDGE) / max(img.size)
    g = img.convert("L")
    if scale < 1.0:
        g = g.resize((max(1, int(g.size[0] * scale)), max(1, int(g.size[1] * scale))), Image.LANCZOS)
    strokes = (np.asarray(g.filter(ImageFilter.MaxFilter(3)), np.int16)
               - np.asarray(g.filter(ImageFilter.MinFilter(3)), np.int16)) > WM_EDGE_THRESHOLD
    # A median filter wide enough to swallow the strokes leaves the background they sit on;
    # its local std says whether that background is a flat shirt or a head of hair.
    bg = np.asarray(g.filter(ImageFilter.MedianFilter(9)), np.float32)
    mean = _box_mean(bg, 12)
    std = np.sqrt(np.clip(_box_mean(bg * bg, 12) - mean * mean, 0, None))
    return strokes & (std < WM_FLAT_STD)


def watermark_screen(img):
    """Returns (flagged, detail_string)."""
    tm = text_mask(img)
    h, w = tm.shape
    cw, ch = int(w * 0.34), int(h * 0.24)
    bands = {
        "top-left": (0, 0, cw, ch), "top-right": (w - cw, 0, w, ch),
        "bottom-left": (0, h - ch, cw, h), "bottom-right": (w - cw, h - ch, w, h),
        "bottom-strip": (int(w * 0.15), int(h * 0.86), int(w * 0.85), h),
        "top-strip": (int(w * 0.15), 0, int(w * 0.85), int(h * 0.14)),
    }
    interior = float(tm[int(h * 0.28):int(h * 0.72), int(w * 0.28):int(w * 0.72)].mean())
    worst = (0.0, 0.0, 0.0, "none")
    for name, (x0, y0, x1, y1) in bands.items():
        sub = tm[y0:y1, x0:x1]
        if sub.size == 0:
            continue
        density = float(sub.mean())
        ratio = density / max(interior, 0.002)
        row_cov = float(sub.mean(axis=1).max())
        if density * min(ratio, 8.0) > worst[0] * min(worst[1], 8.0):
            worst = (density, ratio, row_cov, name)
    density, ratio, row_cov, name = worst
    flagged = (density >= WM_MIN_DENSITY and ratio >= WM_MIN_RATIO and row_cov >= WM_MIN_ROW_COVERAGE)
    return flagged, "%s d=%.4f ratio=%.1f row=%.2f" % (name, density, ratio, row_cov)


# --------------------------------------------------------------------------------------
# GATE 4 — perceptual dedup
# --------------------------------------------------------------------------------------
# dHash catches the same FILE arriving twice: re-uploads, crops, re-encodes, resizes, the
# 500px and 2048px copies of one shot. It does NOT catch two different photographs of
# similar-looking people — nothing in a 64-bit gradient signature knows what a face is. Cell
# diversity is gate 5's job, and ultimately Kevin's eye.
def dhash(img):
    g = np.asarray(img.convert("L").resize((9, 8), Image.LANCZOS), dtype=np.int16)
    bits = (g[:, 1:] > g[:, :-1]).flatten()
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def hamming(a, b):
    return bin(a ^ b).count("1")


def dhash_hex(value):
    return "%016x" % value


# --------------------------------------------------------------------------------------
# GATE 5 — vision (gem9 / 9router subscription; per PATI rule never a per-token API)
# --------------------------------------------------------------------------------------
VISION_RUBRIC = (
    "You are a strict sourcing gate for a photographic persona bank. Judge ONLY the attached "
    "image. Return a single JSON object and nothing else - no prose, no markdown fence. Keys, "
    "all required:\n"
    '{"is_camera_photograph": true|false, "person_count": <integer>, '
    '"apparent_age_min": <integer>, "apparent_age_max": <integer>, '
    '"apparent_gender": "male"|"female"|"ambiguous", "face_clearly_visible": true|false, '
    '"face_obscured": true|false, "beauty_filtered": true|false, '
    '"visible_text_or_watermark": true|false, "recognizable_public_figure": true|false, '
    '"apparent_ethnicity": "<short phrase>", "notes": "<one short sentence>"}\n'
    "Definitions. is_camera_photograph: false for AI-generated, CGI, 3D render, painting, "
    "drawing or illustration. person_count: humans whose face is at least partly in frame. "
    "face_obscured: sunglasses, a hand, a mask, hair or heavy shadow covering the face. "
    "beauty_filtered: skin smoothing, blemish removal, catalogue-style retouching, beauty-app "
    "filtering. visible_text_or_watermark: ANY burned-in text, credit line, logo, date stamp or "
    "signature anywhere in the frame. recognizable_public_figure: a celebrity, politician, "
    "athlete or other identifiable public person."
)


def _extract_json(text):
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


class VisionInfraError(RuntimeError):
    """gem9 itself failed. Distinct from a verdict, because they demand opposite responses:
    a verdict rejects one photo, an infra failure means every verdict this run is worthless."""


def vision_check(image_path):
    """Returns (parsed_dict_or_None, raw_output). Raw is stored verbatim in persona.json.

    gem9 reports its own failures with sys.exit("gem9: HTTP 429: {...}") — a JSON error body
    on STDERR with a non-zero exit. Concatenating stderr into the parse made that body look
    like a verdict: it parses, it has no is_camera_photograph key, and every candidate came
    back rejected as "not a camera photograph". Read the exit status, and parse stdout only.
    """
    res = subprocess.run([GEM9, "-p", VISION_RUBRIC, image_path],
                         capture_output=True, text=True, timeout=VISION_TIMEOUT)
    if res.returncode != 0:
        raise VisionInfraError("gem9 exit %d: %s"
                               % (res.returncode, (res.stderr or res.stdout or "").strip()[:200]))
    raw = (res.stdout or "").strip()
    parsed = _extract_json(raw)
    if parsed is None:
        # Exit 0 with nothing parseable is still an infra symptom, not a judgement on the face.
        raise VisionInfraError("gem9 exited 0 but returned no JSON: %r" % raw[:200])
    return parsed, raw


def evaluate_vision(v, cell):
    """Pure verdict function over the parsed JSON. Returns a list of reject reasons.

    article_images.py deliberately fails OPEN when its QC is inconclusive — it is grading an
    image it already paid to generate. Sourcing is the opposite trade: candidates are free and
    admitting one AI face poisons every article it fronts, so an unusable answer is a reject.
    """
    if not isinstance(v, dict):
        return ["vision output was not usable JSON"]
    reasons = []
    if v.get("is_camera_photograph") is not True:
        reasons.append("not a camera photograph (AI/CGI/illustration)")
    try:
        n = int(v.get("person_count", -1))
    except (TypeError, ValueError):
        n = -1
    if n != 1:
        reasons.append("person_count=%s (need exactly 1 unambiguous subject)" % v.get("person_count"))
    # Age. A bare interval-OVERLAP test is far too weak here, and the two ways it fails are
    # not symmetric. 12-21 overlaps the 20-29 band, so a photograph of a teenager would be
    # written into the bank and end up anchoring supplement advertising — that one is a
    # safety floor, not a taxonomy preference, so it is absolute. And 18-75 overlaps EVERY
    # band in the taxonomy, so one cautious hedge satisfies all ten pools at once and the age
    # structure of the bank quietly stops existing. Require: nobody under 18, an estimate
    # narrow enough to mean something, and its CENTRE inside the band we asked for.
    lo, hi = [int(x) for x in cell["age_band"].split("-")]
    try:
        amin, amax = int(v["apparent_age_min"]), int(v["apparent_age_max"])
        if amax < amin:
            amin, amax = amax, amin
        mid = (amin + amax) / 2.0
        if amin < MIN_APPARENT_AGE:
            reasons.append("apparent age starts at %d — below the hard floor of %d"
                           % (amin, MIN_APPARENT_AGE))
        elif amax - amin > MAX_AGE_INTERVAL:
            reasons.append("apparent age %d-%d spans %d years — too hedged to place in a band"
                           % (amin, amax, amax - amin))
        elif not (lo - 2 <= mid <= hi + 2):
            reasons.append("apparent age %d-%d centres on %.0f, outside cell band %s"
                           % (amin, amax, mid, cell["age_band"]))
    except (KeyError, TypeError, ValueError):
        reasons.append("no usable apparent age")
    if str(v.get("apparent_gender", "")).lower() != cell["gender"]:
        reasons.append("gender %r != cell %r" % (v.get("apparent_gender"), cell["gender"]))
    if v.get("face_clearly_visible") is not True:
        reasons.append("face not clearly visible")
    if v.get("face_obscured") is True:
        reasons.append("face obscured (sunglasses/hands/shadow)")
    if v.get("beauty_filtered") is True:
        reasons.append("beauty-filtered / retouched")
    if v.get("visible_text_or_watermark") is True:
        reasons.append("visible watermark, logo or burned-in text")
    if v.get("recognizable_public_figure") is True:
        reasons.append("recognizable public figure")
    return reasons


# --------------------------------------------------------------------------------------
# Flickr
# --------------------------------------------------------------------------------------
class FlickrError(RuntimeError):
    pass


def _scrub(text, key):
    """The api_key travels in the QUERY STRING, so anything that quotes the request URL back
    at us — urllib3's MaxRetryError text above all — carries the live key. Every FlickrError
    is printed verbatim by cmd_fetch, so scrubbing has to happen at the raise, not the print."""
    t = str(text)
    return t.replace(key, "<api_key>") if key else t


def flickr_call(session, method, key, **params):
    params.update(method=method, api_key=key, format="json", nojsoncallback=1)
    try:
        r = session.get(FLICKR_REST, params=params, timeout=30)
    except requests.RequestException as exc:
        # Name the class first (DNS vs TLS vs reset is the diagnostic an operator needs) and
        # only then the scrubbed detail — so the useful part survives even if a future
        # requests/urllib3 renders the URL in a form the literal replace misses.
        raise FlickrError("network: %s: %s" % (type(exc).__name__, _scrub(exc, key)))
    if r.status_code != 200:
        raise FlickrError("HTTP %s" % r.status_code)  # body may echo the key back; never print it
    try:
        data = r.json()
    except ValueError:
        raise FlickrError("non-JSON response")
    if data.get("stat") != "ok":
        raise FlickrError("api: %s (code %s)" % (data.get("message"), data.get("code")))
    return data


def search_page(session, key, text, page, per_page):
    data = flickr_call(
        session, "flickr.photos.search", key,
        text=text, license=LICENSE_SEARCH_PARAM, safe_search=1, content_types=0,
        media="photos", sort="relevance", per_page=per_page, page=page,
        extras="license,owner_name,url_l,url_o,o_dims,path_alias,realname")
    photos = data.get("photos", {}) or {}
    return photos.get("photo", []) or [], int(photos.get("pages", 0) or 0)


def photo_page_url(photo):
    owner = photo.get("path_alias") or photo.get("owner") or ""
    return "https://www.flickr.com/photos/%s/%s/" % (owner, photo["id"])


def author_name(photo):
    for k in ("realname", "ownername", "path_alias", "owner"):
        v = (photo.get(k) or "").strip()
        if v:
            return v
    return "unknown"


# --------------------------------------------------------------------------------------
# bank on disk
# --------------------------------------------------------------------------------------
def persona_dirs():
    if not os.path.isdir(PERSONAS):
        return []
    out = []
    for name in sorted(os.listdir(PERSONAS)):
        d = os.path.join(PERSONAS, name)
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "persona.json")):
            out.append((name, d))
    return out


def load_bank():
    """handle -> {"dir","doc","ref"} for everything already on disk."""
    bank = {}
    for handle, d in persona_dirs():
        doc = _load(os.path.join(d, "persona.json"), "persona.json for %s" % handle)
        bank[handle] = {"dir": d, "doc": doc, "ref": os.path.join(d, "ref.jpg")}
    return bank


def bank_hashes(bank):
    """handle -> dhash int. Uses the stored value when present (verify stays cheap); legacy
    personas predate the field, so those get hashed from ref.jpg."""
    out = {}
    for handle, rec in bank.items():
        stored = (rec["doc"].get("image") or {}).get("dhash")
        if stored:
            try:
                out[handle] = int(stored, 16)
                continue
            except ValueError:
                pass
        if os.path.exists(rec["ref"]):
            out[handle] = dhash(Image.open(rec["ref"]))
    return out


def taken_handles(bank, index):
    return set(bank) | set(index.get("personas") or {})


def next_handle(cell_id, taken):
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", cell_id):
        sys.exit("✗ cell_id %r is not filesystem-safe — taxonomy.json is wrong" % cell_id)
    for n in range(1, 100):
        h = "%s-%02d" % (cell_id, n)
        if h not in taken:
            return h
    sys.exit("✗ cell %s already has 99 personas — refusing to allocate a 100th" % cell_id)


def cells_by_id(tax):
    return dict((c["cell_id"], c) for c in tax["cells"])


def cell_counts(bank):
    """cell_id -> count, plus pool_id -> count of legacy personas carrying no cell."""
    per_cell, legacy = {}, {}
    for rec in bank.values():
        cid = rec["doc"].get("cell_id")
        if cid:
            per_cell[cid] = per_cell.get(cid, 0) + 1
        else:
            pid = rec["doc"].get("pool_id") or "?"
            legacy[pid] = legacy.get(pid, 0) + 1
    return per_cell, legacy


# --------------------------------------------------------------------------------------
# queries
# --------------------------------------------------------------------------------------
def build_queries(cell, max_queries):
    """Returns (queries, truncated_count)."""
    if cell["cell_id"] in QUERY_OVERRIDES:
        base = list(QUERY_OVERRIDES[cell["cell_id"]])
    else:
        subjects = SUBJECT_WORDS[(cell["gender"], cell["age_band"])]
        scenes = SCENE_PHRASES[cell["age_band"]]
        hints = ETHNICITY_HINTS[cell["ethnicity_key"]][cell["gender"]]
        base = []
        for i, scene in enumerate(scenes):
            for j, subject in enumerate(subjects):
                hint = hints[(i + j) % len(hints)]
                base.append(" ".join(p for p in (hint, subject, scene) if p))
    seen, ordered = set(), []
    for q in base:
        if q not in seen:
            seen.add(q)
            ordered.append(q)
    if max_queries and len(ordered) > max_queries:
        return ordered[:max_queries], len(ordered) - max_queries
    return ordered, 0


# --------------------------------------------------------------------------------------
# writing a persona
# --------------------------------------------------------------------------------------
def attribution_text(photo, info):
    if not info["attribution"]:
        return None
    return '"%s" by %s (%s), licensed under %s (%s)' % (
        (photo.get("title") or "untitled").strip(), author_name(photo),
        photo_page_url(photo), info["name"], info["url"])


def build_persona_doc(handle, cell, photo, lic_id, info, img_meta, vision, raw_verdict, wm_detail):
    age_est = ""
    if isinstance(vision, dict) and vision.get("apparent_age_min") is not None:
        age_est = " ~%s-%s" % (vision.get("apparent_age_min"), vision.get("apparent_age_max"))
    return {
        "schema_version": 2,
        "handle": handle,
        "pool_id": cell["pool_id"],
        "cell_id": cell["cell_id"],
        "gender": cell["gender"],
        "age_band": cell["age_band"],
        "ethnicity_key": cell["ethnicity_key"],
        "ethnicity_note": ("sourced for cell %s (%s); the vision gate REPORTS apparent ethnicity "
                           "but does not enforce it — confirm by eye before first use"
                           % (cell["cell_id"], cell["ethnicity"])),
        "demo": "US %s%s, %s — candid available-light photograph" % (
            "man" if cell["gender"] == "male" else "woman", age_est,
            (isinstance(vision, dict) and vision.get("apparent_ethnicity")) or cell["ethnicity"]),
        "build_vibe": None,
        "source": {
            "platform": "flickr",
            "page_url": photo_page_url(photo),
            "photo_id": str(photo["id"]),
            "author": author_name(photo),
            "license": info["name"],
            "license_url": info["url"],
            "attribution_required": bool(info["attribution"]),
            "attribution_text": attribution_text(photo, info),
        },
        "image": dict(img_meta),
        "qc": {
            "ai_verdict": raw_verdict,
            "watermark": False,
            "face_visible": True,
            "accepted_date": time.strftime("%Y-%m-%d"),
            "notes": ("machine gates passed: licence id %s read back from the API, %.2fMP, "
                      "burned-in-text screen (%s), dHash-deduped vs the whole bank, vision gate. "
                      "Vision JSON: %s" % (lic_id, img_meta["megapixels"], wm_detail,
                                           json.dumps(vision, sort_keys=True))),
            "vision": vision,
        },
        "approved_by": None,
        "approved_date": None,
        "camera_notes": CAMERA_NOTES,
        "usage": ("%s-audience articles (%s); persona is VISUAL ONLY, never named in copy "
                  "(byline stays the roster author)"
                  % (cell["gender"], ", ".join(cell.get("brands_served") or []))),
        # PENDING, never "active". Machine gates establish that a photo is legally usable and
        # technically sound; they cannot establish that Kevin wants this face representing the
        # brand. Only `approve` flips this, and only the picker reads the index copy.
        "status": "pending",
        "flag_reason": None,
    }


def write_persona(handle, doc, jpeg_bytes):
    d = os.path.join(PERSONAS, handle)
    os.makedirs(d, exist_ok=True)
    ref = os.path.join(d, "ref.jpg")
    with open(ref, "wb") as fh:
        fh.write(jpeg_bytes)
    _atomic_write(os.path.join(d, "persona.json"), doc)
    return ref


def as_jpeg(raw):
    """(bytes, PIL.Image). Keeps the original bytes when they are already JPEG so the stored
    sha256 is the sha256 of what the photographer published."""
    img = Image.open(io.BytesIO(raw))
    img.load()
    if raw[:2] == b"\xff\xd8":
        return raw, img
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=92)
    data = buf.getvalue()
    return data, Image.open(io.BytesIO(data))


# --------------------------------------------------------------------------------------
# subcommands
# --------------------------------------------------------------------------------------
def cmd_plan(_args):
    tax, bank = _load(TAXONOMY, "taxonomy"), load_bank()
    per_cell, legacy = cell_counts(bank)
    print("%-12s %-8s %6s %6s %7s" % ("CELL", "POOL", "TARGET", "HAVE", "NEEDED"))
    total_t = total_h = total_n = 0
    for cell in tax["cells"]:
        have = per_cell.get(cell["cell_id"], 0)
        need = max(0, cell["target_count"] - have)
        total_t += cell["target_count"]
        total_h += have
        total_n += need
        print("%-12s %-8s %6d %6d %7d%s" % (cell["cell_id"], cell["pool_id"],
                                            cell["target_count"], have, need,
                                            "" if need else "   ✓ full"))
    print("%-12s %-8s %6d %6d %7d" % ("TOTAL", "", total_t, total_h, total_n))
    if legacy:
        print("\nlegacy personas with no cell_id (counted against NO cell above):")
        for pid in sorted(legacy):
            print("  pool %-6s %d" % (pid, legacy[pid]))
    print("\nfetch one cell:  fetch_personas.py fetch --cell <cell_id> [--limit N] [--dry-run]")


def cmd_verify(args):
    bank = load_bank()
    if not bank:
        sys.exit("✗ no personas on disk under %s" % PERSONAS)
    hashes = bank_hashes(bank)
    cells = cells_by_id(_load(TAXONOMY, "taxonomy")) if args.vision else {}
    failures = 0
    for handle in sorted(bank):
        rec = bank[handle]
        doc, problems, notes = rec["doc"], [], []

        lic = ((doc.get("source") or {}).get("license") or "").strip()
        if lic not in ALLOWED_LICENSE_NAMES:
            problems.append("licence %r not in the allow-list (%s)"
                            % (lic, ", ".join(sorted(ALLOWED_LICENSE_NAMES))))

        if not os.path.exists(rec["ref"]):
            problems.append("ref.jpg missing on disk")
            print("%-14s FAIL  %s" % (handle, "; ".join(problems)))
            failures += 1
            continue
        img = Image.open(rec["ref"])
        w, h = img.size
        if not meets_resolution(w, h):
            problems.append("resolution %dx%d = %.2fMP (floor %.1fMP and %dpx short edge)"
                            % (w, h, w * h / 1e6, MIN_MEGAPIXELS, MIN_SHORT_EDGE))

        flagged, detail = watermark_screen(img)
        notes.append("wm[%s]" % detail)
        if flagged:
            problems.append("burned-in-text screen fired: %s" % detail)

        mine = hashes.get(handle)
        if mine is not None:
            for other in sorted(hashes):
                if other != handle and hamming(mine, hashes[other]) <= DHASH_MAX_DISTANCE:
                    problems.append("dHash duplicate of %s (distance %d)"
                                    % (other, hamming(mine, hashes[other])))

        if args.vision:
            cell = cells.get(doc.get("cell_id"))
            if cell is None:
                # Legacy personas carry cell_id: null, so there is no age band or gender to
                # judge against. Saying so is better than inventing a cell for them.
                notes.append("vision skipped (no cell_id)")
            else:
                try:
                    vision, _raw = vision_check(rec["ref"])
                except (OSError, subprocess.SubprocessError, VisionInfraError) as exc:
                    # An audit must not brand a face as failing when it was the model that
                    # failed. Say the check did not run; do not count it as a problem.
                    notes.append("vision UNAVAILABLE (%s)" % exc)
                else:
                    problems.extend("vision: " + r for r in evaluate_vision(vision, cell))

        print("%-14s %-4s %s%s" % (handle, "FAIL" if problems else "PASS",
                                   "; ".join(problems) if problems else "clean",
                                   "   [%s]" % " ".join(notes) if notes else ""))
        failures += 1 if problems else 0
    print("\n%d/%d personas would fail the gates today." % (failures, len(bank)))
    if not args.vision:
        print("(gate 5 not run — pass --vision to re-check the bank through gem9)")
    sys.exit(1 if failures else 0)


def cmd_approve(args):
    """Kevin's decision, recorded. This is the ONLY thing that makes a fetched face usable.

    Deliberately not a bulk --all: the whole point of the pending state is that a human looked
    at each face. It writes both places — persona.json for provenance (who, when) and
    index.json because that is the only file persona_picker.py reads."""
    bank, index = load_bank(), _load(INDEX, "index")
    new_status = "retired" if args.reject else "active"
    people = index.setdefault("personas", {})
    changed = []
    for handle in args.handles:
        if handle not in bank:
            sys.exit("✗ unknown persona %r — nothing written" % handle)
        if handle not in people:
            sys.exit("✗ %s has a directory on disk but no index.json row; run `verify` first "
                     "— nothing written" % handle)
    for handle in args.handles:
        doc = bank[handle]["doc"]
        doc["status"] = new_status
        doc["approved_by"] = None if args.reject else (args.by or "kevin")
        doc["approved_date"] = None if args.reject else time.strftime("%Y-%m-%d")
        if args.reject:
            doc["flag_reason"] = args.reason or "rejected on sight by Kevin"
        _atomic_write(os.path.join(PERSONAS, handle, "persona.json"), doc)
        people[handle]["status"] = new_status
        changed.append(handle)
    _atomic_write(INDEX, index)
    print("✓ %s: %s" % ("REJECTED (retired)" if args.reject else "approved", ", ".join(changed)))
    if not args.reject:
        print("These are now selectable by persona_picker.py.")


def cmd_fetch(args):
    cells = cells_by_id(_load(TAXONOMY, "taxonomy"))
    if args.cell not in cells:
        sys.exit("✗ unknown --cell %r. Valid: %s" % (args.cell, ", ".join(sorted(cells))))
    cell = cells[args.cell]

    bank, index = load_bank(), _load(INDEX, "index")
    per_cell, _ = cell_counts(bank)
    have = per_cell.get(cell["cell_id"], 0)
    needed = max(0, cell["target_count"] - have)
    if args.limit is not None:
        # --limit is a CAP, always. It used to fall through to `args.limit` when the cell was
        # already full, which turned a safety brake into a request for N more faces than the
        # taxonomy asks for — and skewed the picker's pool rotation toward that one cell.
        needed = min(needed, args.limit)
    if needed <= 0:
        print("✓ cell %s is full (%d/%d) — nothing to fetch"
              % (cell["cell_id"], have, cell["target_count"]))
        return

    key = api_key()
    session = requests.Session()
    session.headers["User-Agent"] = "genseo-fetch-personas/1.0 (+wellnessnest.co)"

    queries, dropped = build_queries(cell, args.queries)
    hashes = bank_hashes(bank)
    known_photo_ids = set()
    for rec in bank.values():
        pid = (rec["doc"].get("source") or {}).get("photo_id")
        if pid:
            known_photo_ids.add(str(pid))
    taken = taken_handles(bank, index)

    print("cell %s — %s %s %s | have %d, target %d, fetching up to %d"
          % (cell["cell_id"], cell["gender"], cell["age_band"], cell["ethnicity"],
             have, cell["target_count"], needed))
    print("licence filter: %s (%s)" % (LICENSE_SEARCH_PARAM,
                                       ", ".join(ALLOWED_LICENSES[i]["name"]
                                                 for i in LICENSE_SEARCH_PARAM.split(","))))
    print("queries (%d%s), up to %d page(s) x %d results each:"
          % (len(queries), ", %d MORE AVAILABLE but capped by --queries" % dropped if dropped else "",
             args.pages, args.per_page))
    for q in queries:
        print("   %s" % q)
    if args.dry_run:
        print("DRY RUN: gates run for real, nothing is written to disk.")
    print("")

    accepted, examined, seen_ids = [], 0, set()
    stop_reason = "queries exhausted"
    vision_infra_fails = 0
    try:
        for query in queries:
            if len(accepted) >= needed:
                stop_reason = "reached the fetch target"
                break
            for page in range(1, args.pages + 1):
                if len(accepted) >= needed:
                    stop_reason = "reached the fetch target"
                    break
                if examined >= args.max_candidates:
                    stop_reason = "hit --max-candidates=%d" % args.max_candidates
                    break
                try:
                    photos, total_pages = search_page(session, key, query, page, args.per_page)
                except FlickrError as exc:
                    print("  ✗ search failed (%s | page %d): %s" % (query, page, exc))
                    break
                if not photos:
                    break
                for photo in photos:
                    if len(accepted) >= needed:
                        break
                    if examined >= args.max_candidates:
                        break
                    pid = str(photo.get("id"))
                    if pid in seen_ids:
                        continue
                    seen_ids.add(pid)
                    if pid in known_photo_ids:
                        print("  · %-12s already in the bank" % pid)
                        continue
                    examined += 1
                    verdict = process_candidate(photo, cell, key, session, hashes, args)
                    # An infra failure is NOT evidence the photo is bad. Left uncounted, a
                    # 9router outage renders as 400 content rejections and reads as "Flickr
                    # has nothing for this cell" — the operator rewrites good queries and
                    # burns the whole --max-candidates budget on doomed calls.
                    if verdict[0] == "vision-infra":
                        vision_infra_fails += 1
                        print("  ! %-12s [vision-infra] %s  (%d in a row)"
                              % (pid, verdict[1], vision_infra_fails))
                        if vision_infra_fails >= VISION_INFRA_ABORT:
                            stop_reason = ("ABORTED — %d consecutive vision-infra failures; "
                                           "this is a gem9/9router problem, not a photo problem"
                                           % vision_infra_fails)
                            raise _AbortRun()
                        continue
                    vision_infra_fails = 0
                    if verdict[0] != "accept":
                        print("  ✗ %-12s [%s] %s" % (pid, verdict[0], verdict[1]))
                        continue
                    doc_parts, jpeg, img = verdict[2], verdict[3], verdict[4]
                    handle = next_handle(cell["cell_id"], taken)
                    taken.add(handle)
                    doc = build_persona_doc(handle, cell, photo, doc_parts["lic_id"],
                                            doc_parts["info"], doc_parts["img_meta"],
                                            doc_parts["vision"], doc_parts["raw"], doc_parts["wm"])
                    ref = None if args.dry_run else write_persona(handle, doc, jpeg)
                    print("  ✓ %-12s [%s] → %s  %dx%d %.2fMP %s by %s"
                          % (pid, "would accept" if args.dry_run else "accept", handle,
                             img.size[0], img.size[1], img.size[0] * img.size[1] / 1e6,
                             doc_parts["info"]["name"], author_name(photo)))
                    accepted.append((handle, cell["pool_id"], ref))
                    hashes[handle] = int(doc_parts["img_meta"]["dhash"], 16)
                if total_pages and page >= total_pages:
                    break
                time.sleep(args.sleep)
    except _AbortRun:
        pass
    finally:
        # write_persona() already committed each accept to disk. If we die here without
        # writing the index, those dirs are invisible to the picker forever while
        # cell_counts() still counts them as filled — capacity vanishes silently.
        if not args.dry_run:
            commit_accepted(accepted)

    print("\nexamined %d candidate(s), accepted %d of %d wanted — stopped: %s"
          % (examined, len(accepted), needed, stop_reason))
    if dropped:
        print("NOTE: %d further query phrasings were CAPPED by --queries=%d, not exhausted."
              % (dropped, args.queries))
    if accepted and not args.dry_run:
        print("These passed the MACHINE gates only. They are status=\"pending\" and the picker "
              "will not hero them. Kevin's approval is what flips them to active.")


def commit_accepted(accepted):
    """Write the accepted personas into index.json as PENDING.

    Two things this must not do. (1) Never status="active": persona_picker.py selects on the
    index alone and never opens persona.json, so a null approved_by there is decorative —
    an "active" row here IS the approval, and would put a face Kevin has never seen on a live
    Shopify og:image at the next 08:47 run. (2) Never leave persona dirs on disk without a
    matching index row: write_persona() commits per candidate, so a crash mid-loop used to
    strand faces that cell_counts() then counted as filled and the picker could never see.
    Hence: caller invokes this from a finally."""
    if not accepted:
        return
    # Re-read immediately before writing: persona_picker.py commit may have landed while
    # this run was downloading, and clobbering it silently repeats a persona.
    fresh = _load(INDEX, "index")
    people = fresh.setdefault("personas", {})
    for handle, pool_id, ref in accepted:
        # angles_used seeded explicitly rather than left to `.get(..) or []` at read time:
        # Kevin's one-angle-per-model rule is enforced entirely off this list, and a key that
        # only appears after the first commit is a key that looks the same when it is missing
        # as when the persona is genuinely fresh.
        people[handle] = {"handle": handle, "pool_id": pool_id, "status": "pending",
                          "ref": ref, "used_count": 0, "last_used_seq": 0,
                          "gaze_used": [], "last_gaze": None, "angles_used": []}
    _atomic_write(INDEX, fresh)
    print("\n✓ index.json updated (+%d personas as PENDING, atomic, re-read before write)"
          % len(accepted))


def process_candidate(photo, cell, key, session, hashes, args):
    """Runs gates 1-5, cheapest first. Returns a tuple whose first element is the gate that
    rejected it, or ("accept", "", parts, jpeg_bytes, image)."""
    lic_id, info, reason = gate_license(photo)
    if not info:
        return ("licence", reason)

    try:
        size = largest_size(photo, key, session, allow_getsizes=not args.no_getsizes,
                            sleep=args.sleep)
    except FlickrError as exc:
        return ("api", "getSizes failed: %s" % exc)
    if not size:
        return ("resolution", "no downloadable size reported")
    _, w, h, url, label = size
    if not meets_resolution(w, h):
        return ("resolution", "%dx%d = %.2fMP short=%d (floor %.1fMP / %dpx) [%s]"
                % (w, h, w * h / 1e6, min(w, h), MIN_MEGAPIXELS, MIN_SHORT_EDGE, label))

    try:
        resp = session.get(url, timeout=90)
        resp.raise_for_status()
        jpeg, img = as_jpeg(resp.content)
    except (requests.RequestException, OSError, ValueError) as exc:
        return ("download", "%s" % exc)
    if img.size[0] * img.size[1] / 1e6 < MIN_MEGAPIXELS:
        return ("resolution", "delivered file is %dx%d, smaller than advertised" % img.size)

    flagged, wm_detail = watermark_screen(img)
    if flagged:
        return ("watermark", "burned-in text screen: %s" % wm_detail)

    h64 = dhash(img)
    for handle, other in hashes.items():
        d = hamming(h64, other)
        if d <= DHASH_MAX_DISTANCE:
            return ("dupe", "dHash distance %d vs %s" % (d, handle))

    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    try:
        tmp.write(jpeg)
        tmp.close()
        try:
            vision, raw = vision_check(tmp.name)
        except (OSError, subprocess.SubprocessError, VisionInfraError) as exc:
            return ("vision-infra", "gem9 unavailable (%s) — refusing to accept unseen" % exc)
    finally:
        os.unlink(tmp.name)
    reasons = evaluate_vision(vision, cell)
    if reasons:
        return ("vision", "; ".join(reasons))

    parts = {
        "lic_id": lic_id, "info": info, "vision": vision, "raw": raw, "wm": wm_detail,
        "img_meta": {
            "width": img.size[0], "height": img.size[1],
            "megapixels": round(img.size[0] * img.size[1] / 1e6, 2),
            "sha256": hashlib.sha256(jpeg).hexdigest(),
            "bytes": len(jpeg),
            "dhash": dhash_hex(h64),
        },
    }
    return ("accept", "", parts, jpeg, img)


# --------------------------------------------------------------------------------------
# selftest — pure functions only, no network, no API key
# --------------------------------------------------------------------------------------
def cmd_selftest(_args):
    failures = []

    def check(name, ok, detail=""):
        print("  %s %s%s" % ("✓" if ok else "✗", name, "  %s" % detail if detail else ""))
        if not ok:
            failures.append(name)

    print("licence table")
    check("allow-list is exactly {9, 11, 4}", set(ALLOWED_LICENSES) == {"9", "11", "4"})
    check("search param matches the allow-list",
          set(LICENSE_SEARCH_PARAM.split(",")) == set(ALLOWED_LICENSES))
    check("allow and forbid lists are disjoint",
          not (set(ALLOWED_LICENSES) & set(FORBIDDEN_LICENSES)))
    check("every Flickr licence id 0-12 is classified",
          set(ALLOWED_LICENSES) | set(FORBIDDEN_LICENSES) == set(str(i) for i in range(13)))
    for bad in ("0", "1", "2", "3", "5", "6", "7", "8", "10", "12"):
        _, info, why = gate_license({"license": bad})
        if info or not why:
            check("licence %s rejected" % bad, False)
    check("all forbidden ids rejected with a reason", True)
    _, info, _ = gate_license({"license": "99"})
    check("unknown licence id refused rather than guessed", info is None)

    print("resolution gate")
    check("1024x683 (0.70MP) rejected", not meets_resolution(1024, 683))
    check("1200x800 (0.96MP) rejected — MP floor, not just short edge",
          not meets_resolution(1200, 800))
    check("900x900 (0.81MP) rejected", not meets_resolution(900, 900))
    check("2048x1365 (2.80MP) accepted", meets_resolution(2048, 1365))
    check("f1-redshirt's 333x500 would be refused", not meets_resolution(333, 500))

    print("dHash")
    ref = os.path.join(PERSONAS, "m1-stubble", "ref.jpg")
    other = os.path.join(PERSONAS, "f2-brunette", "ref.jpg")
    if not (os.path.exists(ref) and os.path.exists(other)):
        check("legacy refs present for the hash test", False, "%s / %s" % (ref, other))
    else:
        src = Image.open(ref)
        copies = []
        for scale, quality in ((0.55, 80), (0.40, 70)):
            buf = io.BytesIO()
            src.convert("RGB").resize((int(src.size[0] * scale), int(src.size[1] * scale)),
                                      Image.LANCZOS).save(buf, "JPEG", quality=quality)
            copies.append(dhash(Image.open(io.BytesIO(buf.getvalue()))))
        d_same = hamming(copies[0], copies[1])
        d_orig = hamming(dhash(src), copies[0])
        d_diff = hamming(dhash(src), dhash(Image.open(other)))
        check("two resized/re-encoded copies of one ref collide (<= %d)" % DHASH_MAX_DISTANCE,
              d_same <= DHASH_MAX_DISTANCE, "distance %d" % d_same)
        check("resized copy still matches the original", d_orig <= DHASH_MAX_DISTANCE,
              "distance %d" % d_orig)
        check("two different persona refs do NOT collide", d_diff > DHASH_MAX_DISTANCE,
              "distance %d" % d_diff)
        check("dhash_hex round-trips", int(dhash_hex(dhash(src)), 16) == dhash(src))

    print("burned-in-text screen (empirical anchors, legacy bank)")
    expect = {"f2-brunette": True, "m1-stubble": False, "f1-redshirt": False}
    for handle, want in sorted(expect.items()):
        p = os.path.join(PERSONAS, handle, "ref.jpg")
        if not os.path.exists(p):
            check("%s present" % handle, False)
            continue
        flagged, detail = watermark_screen(Image.open(p))
        check("%s %s" % (handle, "flags ('(c) stefano borghetto')" if want else "stays clean"),
              flagged == want, detail)
    p = os.path.join(PERSONAS, "f3-silver", "ref.jpg")
    if os.path.exists(p):
        flagged, detail = watermark_screen(Image.open(p))
        print("  i f3-silver (KNOWN BLIND SPOT: script watermark over hair-on-bokeh) "
              "flagged=%s  %s" % (flagged, detail))

    print("vision verdict evaluation")
    cell = {"gender": "male", "age_band": "40-49", "cell_id": "m4049-wh"}
    good = {"is_camera_photograph": True, "person_count": 1, "apparent_age_min": 42,
            "apparent_age_max": 48, "apparent_gender": "male", "face_clearly_visible": True,
            "face_obscured": False, "beauty_filtered": False,
            "visible_text_or_watermark": False, "recognizable_public_figure": False}
    check("clean candidate passes", evaluate_vision(good, cell) == [])
    for tweak, label in (({"is_camera_photograph": False}, "AI/CGI rejected"),
                         ({"person_count": 2}, "two people rejected"),
                         ({"apparent_age_min": 20, "apparent_age_max": 27}, "age outside band rejected"),
                         ({"apparent_gender": "female"}, "wrong gender rejected"),
                         ({"face_obscured": True}, "obscured face rejected"),
                         ({"beauty_filtered": True}, "retouched face rejected"),
                         ({"visible_text_or_watermark": True}, "watermark rejected"),
                         ({"recognizable_public_figure": True}, "celebrity rejected")):
        v = dict(good)
        v.update(tweak)
        check(label, evaluate_vision(v, cell) != [])
    check("unparseable vision output rejected (fails CLOSED, unlike article_images.py)",
          evaluate_vision(None, cell) != [])

    # Age gate. These four are the reason it is not a bare interval-overlap test.
    def age(lo, hi, c=cell):
        return evaluate_vision(dict(good, apparent_age_min=lo, apparent_age_max=hi), c)

    check("an estimate straddling the band edge still passes (38-44 in 40-49)", age(38, 44) == [])
    young = {"gender": "male", "age_band": "20-29", "cell_id": "m2029-wh"}
    check("APPARENT MINOR rejected (12-21 overlaps the 20-29 band but must never be sourced)",
          age(12, 21, young) != [])
    check("hedged estimate rejected (18-75 would otherwise satisfy every band in the taxonomy)",
          age(18, 75) != [])
    check("single-point touch rejected (29-70 must not land in the 20-29 cell)",
          age(29, 70, young) != [])
    check("centre outside the band rejected (52-58 is not a 40-49 face)", age(52, 58) != [])
    check("inverted min/max is normalised, not mis-read", age(48, 42) == [])

    print("hard constraints")

    class _BoomSession(object):
        """urllib3 quotes the whole request URL — api_key included — into its error text."""
        def get(self, *_a, **_k):
            raise requests.ConnectionError(
                "HTTPSConnectionPool(host='api.flickr.com', port=443): Max retries exceeded "
                "with url: /services/rest/?method=flickr.photos.search&api_key=SECRETKEY123"
                "&format=json (Caused by NewConnectionError(...))")

    try:
        flickr_call(_BoomSession(), "flickr.photos.search", "SECRETKEY123")
        msg = "<flickr_call did not raise>"
    except FlickrError as exc:
        msg = str(exc)
    check("API key never reaches a FlickrError message (cmd_fetch prints these verbatim)",
          "SECRETKEY123" not in msg, msg[:90])
    check("...and the exception class survives scrubbing, so the failure is still diagnosable",
          "ConnectionError" in msg)

    print("queries + handles")
    tax = _load(TAXONOMY, "taxonomy")
    sample = cells_by_id(tax)["m5059-hl"]
    qs, dropped = build_queries(sample, 6)
    check("query builder produces natural-language phrasings", len(qs) == 6 and dropped > 0,
          "e.g. %r (+%d capped)" % (qs[0], dropped))
    check("every taxonomy cell can build queries",
          all(build_queries(c, 4)[0] for c in tax["cells"]))
    check("handles are unique and filesystem-safe",
          next_handle("m3039-wh", set()) == "m3039-wh-01"
          and next_handle("m3039-wh", {"m3039-wh-01"}) == "m3039-wh-02")

    print("")
    if failures:
        sys.exit("✗ selftest FAILED: %s" % ", ".join(failures))
    print("✓ selftest passed")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan", help="what each cell still needs (no network)")
    p.set_defaults(fn=cmd_plan)

    f = sub.add_parser("fetch", help="fill ONE taxonomy cell from Flickr")
    f.add_argument("--cell", required=True, help="cell_id from personas/taxonomy.json")
    f.add_argument("--limit", type=int, default=None, help="accept at most N (default: the cell's shortfall)")
    f.add_argument("--dry-run", action="store_true",
                   help="run every gate for real but write nothing")
    f.add_argument("--pages", type=int, default=3,
                   help="pages per query (default 3; one page returns the same popular photos)")
    f.add_argument("--per-page", type=int, default=500, help="results per page, max 500")
    f.add_argument("--queries", type=int, default=12, help="cap on composed query phrasings")
    f.add_argument("--max-candidates", type=int, default=400,
                   help="stop after examining this many photos (reported at the end)")
    f.add_argument("--sleep", type=float, default=0.3,
                   help="seconds between Flickr calls (search pages AND per-candidate getSizes)")
    f.add_argument("--no-getsizes", action="store_true",
                   help="skip the flickr.photos.getSizes lookup; judge resolution on search extras only")
    f.set_defaults(fn=cmd_fetch)

    v = sub.add_parser("verify", help="re-run the gates over the bank on disk")
    v.add_argument("--vision", action="store_true",
                   help="also re-run gate 5 through gem9 (off by default: verify is otherwise offline)")
    v.set_defaults(fn=cmd_verify)

    ap_ = sub.add_parser("approve", help="Kevin's verdict — the ONLY way a face becomes usable")
    ap_.add_argument("handles", nargs="+", help="persona handles he looked at")
    ap_.add_argument("--reject", action="store_true", help="retire these instead of approving")
    ap_.add_argument("--reason", help="why, when rejecting")
    ap_.add_argument("--by", help="who approved (default: kevin)")
    ap_.set_defaults(fn=cmd_approve)

    s = sub.add_parser("selftest", help="exercise the pure functions (no network, no API key)")
    s.set_defaults(fn=cmd_selftest)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

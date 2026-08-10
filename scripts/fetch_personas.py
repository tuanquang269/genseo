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
import glob
import gzip
import hashlib
import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONAS = os.path.join(ROOT, "personas")
INDEX = os.path.join(PERSONAS, "index.json")
TAXONOMY = os.path.join(PERSONAS, "taxonomy.json")
GEM9 = "/Users/kevinkreative/.local/bin/gem9"
FLICKR_REST = "https://api.flickr.com/services/rest/"
OPENIMAGES_DIR = os.path.join(PERSONAS, "_openimages")
OPENIMAGES_INDEX = os.path.join(OPENIMAGES_DIR, "candidates.json.gz")
OPENIMAGES_VERDICTS = os.path.join(OPENIMAGES_DIR, "verdicts.jsonl")

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

# Flickr numeric ids are a Flickr fact. Every other source names licences with a slug
# ("cc-by-4.0", "cc0", "cc-by-3.0-tw"), so the table above cannot be the gate once a second
# backend exists. Enumerating the acceptable slugs does not survive contact with jurisdiction
# ports — there are dozens, they are minted without notice, and a missing one silently reads as
# "unknown, refuse" on a licence that is in fact fine. So the gate is a RULE over the slug.
#
# DENY runs first and wins. It is not the complement of ALLOW: `pd` and `public domain` are
# rejected on purpose even though they permit everything, because they are ASSERTIONS about
# status rather than grants, carrying no warranty — the same reason Flickr ids 7, 8 and 10 are
# in FORBIDDEN_LICENSES above. An empty slug is a reject, never a pass: a source that did not
# tell us the licence has not told us it is free.
LICENCE_DENY_RE = re.compile(r"-sa\b|-sa-|-nc\b|-nc-|-nd\b|-nd-|^pd|^public|^gfdl|^fal|"
                             r"^attribution$|^no[ -]known|^united[ -]states[ -]gov")
LICENCE_ALLOW_RE = re.compile(r"^cc0(-1\.0)?$|^cc-by-\d\.\d(-[a-z]{2,3})?$")
FLICKR_ID_TO_SLUG = {"9": "cc0-1.0", "11": "cc-by-4.0", "4": "cc-by-2.0"}


def licence_display(slug):
    """'cc-by-3.0-tw' -> ('CC BY 3.0 TW', canonical deed URL). Cosmetic only; the gate is the
    regex pair above. The deed URL is built from the slug rather than looked up so a port we
    have never seen still records a resolvable link in persona.json."""
    s = slug.lower()
    if s.startswith("cc0"):
        return "CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/"
    body = s[len("cc-by-"):]
    ver, _, port = body.partition("-")
    name = "CC BY %s%s" % (ver, (" " + port.upper()) if port else "")
    url = "https://creativecommons.org/licenses/by/%s/%s" % (ver, (port + "/") if port else "")
    return name, url


def licence_ok(slug):
    """Platform-neutral licence gate. Returns (info_or_None, reason).

    info = {"name","url","attribution","slug"} — the same shape ALLOWED_LICENSES carries, so
    everything downstream is indifferent to which backend produced the candidate."""
    s = (slug or "").strip().lower()
    if not s:
        return None, ("no licence reported — refusing. An absent licence is not a permissive "
                      "one; it is a source that did not answer the question")
    if LICENCE_DENY_RE.search(s):
        return None, ("licence %r is excluded by the spine (share-alike, non-commercial, "
                      "no-derivatives, or a status assertion rather than a grant)" % s)
    if not LICENCE_ALLOW_RE.match(s):
        return None, ("licence %r is not a form this script knows — refusing rather than "
                      "guessing what it permits" % s)
    name, url = licence_display(s)
    return {"name": name, "url": url, "attribution": not s.startswith("cc0"), "slug": s}, ""


def licence_name_ok(name):
    """Re-check a licence NAME already written into a persona.json. `verify` audits the bank on
    disk, where schema v3 records the slug but schema v2 kept only the display name — so the
    audit has to be able to run the same rule against the name. licence_display() is the exact
    inverse of this transform, which is why round-tripping it is safe."""
    slug = (name or "").strip().lower().replace(" ", "-")
    info, _ = licence_ok(slug)
    return info is not None

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
# Greyscale screen. Measured across the 44-face bank on 2026-08-10: the one true greyscale
# photograph (m6070-hl-01) has ZERO pixels above chroma 12, and the next lowest image in the
# whole bank has 1.8% of its pixels above chroma 30. There is no middle ground to tune against,
# which is exactly why this threshold is safe — and why it is the ONLY thing measured here.
# See monochrome_screen for why sepia and period photographs are NOT caught by pixels.
MONO_CHROMA = 12              # per-pixel max(R,G,B)-min(R,G,B) that counts as "has colour"
MONO_MIN_FRACTION = 0.001     # below this fraction of coloured pixels the file is greyscale
VISION_TIMEOUT = 180
# Statuses that mean "the router is busy", not "this photograph is bad". 502/503/504 are
# 9router or the provider shedding load; 429 is it asking for less. Everything else —
# a 400, a 401, a malformed answer — is a real fault that a retry only repeats.
VISION_TRANSIENT = ("HTTP 429", "HTTP 500", "HTTP 502", "HTTP 503", "HTTP 504")
VISION_INFRA_ABORT = 5        # consecutive gem9/9router failures that end the run
MIN_APPARENT_AGE = 18         # absolute floor — never source a face that could read as a minor
MAX_AGE_INTERVAL = 15         # a wider estimate than this is a hedge, not an answer


# Candidates are judged concurrently, because ~85% of a candidate's wall-clock is one gem9
# subprocess waiting on the network (measured 2026-08-10: 44 candidates in 11m26s = 15.6s each,
# of which the vision call is ~13s). At the ~2.3% acceptance rate a serial run measured, 200
# personas is ~8,700 candidates ≈ 38 hours; the whole harvest is bounded by a call we spend
# almost all of it merely waiting on.
#
# The concurrency deliberately does NOT extend to the asset host. upload.wikimedia.org rate-limits
# separately from the API and 429s far sooner — a throttle we only just fixed by switching to
# thumbnails — so downloads pass through a semaphore while the vision calls fan out. The
# parallelism belongs on the call we are waiting for, not on the host that asked us to slow down.
_DOWNLOAD_GATE = threading.BoundedSemaphore(2)
# And the router has a ceiling of its own, lower than either. Measured 2026-08-10: one gem9
# call answers in 5.5s, six concurrent ones drew five straight 502s, and a run at --workers 16
# managed 5.2 candidates a minute against 12/min at --workers 12 — the extra workers spent
# their time in the retry backoff they had themselves caused. Gating vision separately is what
# lets --workers describe how many candidates are IN FLIGHT (downloading, hashing, waiting)
# rather than how many may be shouting at 9router at once.
_VISION_GATE = threading.BoundedSemaphore(6)
_THREAD_LOCAL = threading.local()


def set_download_concurrency(n):
    global _DOWNLOAD_GATE
    _DOWNLOAD_GATE = threading.BoundedSemaphore(max(1, int(n)))


def set_vision_concurrency(n):
    global _VISION_GATE
    _VISION_GATE = threading.BoundedSemaphore(max(1, int(n)))


def worker_session(template):
    """A private requests.Session per worker thread.

    requests.Session is not documented as thread-safe, and its connection pool is the part that
    isn't. Threads share nothing here but the headers copied off the caller's session, so pooling
    still works INSIDE a thread and no two threads ever touch one pool."""
    sess = getattr(_THREAD_LOCAL, "session", None)
    if sess is None:
        sess = requests.Session()
        sess.headers.update(template.headers)
        _THREAD_LOCAL.session = sess
    return sess


# --------------------------------------------------------------------------------------
# verdict cache
# --------------------------------------------------------------------------------------
# The taxonomy has 50 cells and Open Images is ONE undifferentiated pool. Without a cache,
# filling cell 50 means re-judging every face the first 49 already refused — 50 x 15k model
# calls to source 200 photographs. So the vision answer is stored against the image, not
# against the cell that happened to ask for it, and evaluate_vision re-reads it for free.
#
# It is keyed on the SOURCE's own image id, which is why only the Open Images backend uses it:
# a Commons pageid is stable, but a Commons candidate carries a thumbnail URL whose geometry
# depends on the request, so "the same id" there does not mean "the same pixels".
_VERDICT_CACHE = {}
_VERDICT_LOCK = threading.Lock()


def verdict_cache_load():
    _VERDICT_CACHE.clear()
    if not os.path.exists(OPENIMAGES_VERDICTS):
        return 0
    with open(OPENIMAGES_VERDICTS) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue      # a half-written last line after a kill, not a reason to refuse to run
            if rec.get("image_id"):
                _VERDICT_CACHE[rec["image_id"]] = rec
    return len(_VERDICT_CACHE)


def verdict_cached(cand):
    if cand.get("platform") != "openimages":
        return None
    return _VERDICT_CACHE.get(str(cand.get("id")))


def verdict_remember(cand, **fields):
    """Append-only, because a worker thread crashing mid-rewrite must not be able to lose the
    thousands of model calls already banked. Appending one line can only ever lose that line."""
    if cand.get("platform") != "openimages":
        return
    rec = dict(fields)
    rec["image_id"] = str(cand.get("id"))
    rec["seen_date"] = time.strftime("%Y-%m-%d")
    with _VERDICT_LOCK:
        _VERDICT_CACHE[rec["image_id"]] = rec
        os.makedirs(os.path.dirname(OPENIMAGES_VERDICTS), exist_ok=True)
        with open(OPENIMAGES_VERDICTS, "a") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")


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

# --- Commons needs its own vocabulary, and the reason is structural -------------------
# Flickr's `text=` is fuzzy: extra words re-rank. Commons full-text ANDs every term, so each
# word added is a filter, not a nudge. Measured 2026-08-10 on the same corpus:
#   man                        128,099
#   man portrait                 4,685
#   man kitchen                    166
#   man kitchen candid portrait        0
# The 5-7 token phrases above are perfectly good Flickr queries and return literally nothing
# here. Two or three tokens is not a stylistic preference; it is the difference between a
# result set and an empty one.
COMMONS_SUBJECTS = {
    ("male", "20-29"): ["young man"], ("male", "30-39"): ["man"],
    ("male", "40-49"): ["man"], ("male", "50-59"): ["older man"],
    ("male", "60-70"): ["elderly man"],
    ("female", "20-29"): ["young woman"], ("female", "30-39"): ["woman"],
    ("female", "40-49"): ["woman"], ("female", "50-59"): ["older woman"],
    ("female", "60-70"): ["elderly woman"],
}
# One token each. Anything longer stacks another AND onto a corpus that is already small.
COMMONS_SCENES = ["portrait", "kitchen", "garden", "market", "outdoors", "smiling",
                  "cooking", "walking", "workshop", "cafe"]
COMMONS_ETHNICITY_HINTS = {
    "wh": [""], "hl": ["latino", "hispanic"], "bl": ["african"],
    "as": ["asian"], "mx": ["arab", "indigenous"],
}
# Named contemporary PROJECTS, and they matter more than any scene word.
#
# Measured 2026-08-10: every Commons licence category is dominated by whichever institution
# bulk-uploaded into it, because institutions upload in thousands and individuals in ones.
# CC0 is the Metropolitan Museum's art scans; `incategory:"CC-BY-4.0" incategory:"Portrait
# photographs"` is the Finnish Heritage Agency's 1901-1991 monochrome archive almost wholesale.
# The usable photographs are not spread thinly through the corpus waiting to be found by a
# better adjective — they are CONCENTRATED in a handful of contemporary batch-uploaded
# projects. So query the project by name and let geography carry the demographic, instead of
# asking full-text search to honour an ethnicity adjective it has no reason to honour.
#
# ⚠️ Every extra token ANDs. `"Wiki Loves Africa" portrait` collapses 3,153 hits to 5. These
# phrases go in BARE — never combined with a subject or scene word.
COMMONS_PROJECTS = {
    "hl": ['"Solo un milagro por persona"'],
    "bl": ['"Wiki Loves Africa"'],
    "as": ['"Wiki Loves Folklore"'],
    "mx": ['"Wiki Loves Folklore"', '"Wiki Loves Africa"'],
    "wh": [],
}

# The instruction is unchanged; the reason attached to it was wrong and is corrected here.
# "ima2 i2i drifts identity" was measured false on 2026-08-10 — a live hero opened beside its
# ref.jpg was recognisably the same man, down to the hairline and the brow crease. Feeding the
# ORIGINAL still matters, but because each generation is another lossy re-reading and chaining
# them compounds it, not because the chain would lose the face.
CAMERA_NOTES = ("indoor/ambient available light, real skin texture — always camera-match; "
                "ALWAYS feed THIS ref.jpg, never a previous gen (each gen is another lossy "
                "re-reading; chaining them compounds the drift in everything BUT the identity, "
                "which ima2 holds onto — measured 2026-08-10)")


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
# GATE P — personality / publicity rights
# --------------------------------------------------------------------------------------
# A CC licence is a COPYRIGHT licence and says so in its own text: CC BY 4.0 §2(b)(1) excludes
# publicity, privacy and personality rights from the grant, and CC0 §4 disclaims that it
# obtains any consent. So a photograph can be perfectly licensed and still be unusable in an
# advertisement for a supplement, because the photographer's permission was never the subject's.
#
# Commons is the only source that surfaces this as machine-readable state: extmetadata carries
# Restrictions="personality" (sometimes "trademarked", "insignia", or several joined by "|")
# when a file has that warning template. Measured on 2026-08-10, SEVEN of eight candidates from
# a plain `smiling woman` search carried it — this is the common case, not the corner case.
#
# One-way valve on purpose. A set flag REJECTS; an empty flag proves nothing at all, because the
# template is applied by volunteers and its absence is silence rather than clearance. So this
# gate can only ever remove candidates, and never certifies one.
PERSONALITY_FLAGS = ("personality", "trademarked", "insignia", "currency", "design")


def gate_personality(cand):
    """Returns (ok, reason). Never a green light — only a refusal."""
    raw = str(cand.get("restrictions") or "").strip().lower()
    if not raw:
        return True, ""
    hits = [f for f in PERSONALITY_FLAGS if f in raw]
    if hits:
        return False, ("source flags restrictions=%r — a CC licence covers copyright only "
                       "(CC BY 4.0 s2(b)(1) excludes publicity/personality rights), and this "
                       "file is marked as carrying exactly that kind of claim" % raw)
    return False, ("source flags restrictions=%r, a warning this script does not recognise — "
                   "refusing rather than deciding it is harmless" % raw)


# --------------------------------------------------------------------------------------
# GATE P2 — the same question, asked of Flickr
# --------------------------------------------------------------------------------------
# gate_personality reads Commons' extmetadata Restrictions field. openimages_candidate sets
# restrictions="" unconditionally, and Open Images supplies every candidate this pipeline
# actually walks — so the publicity-rights gate it already had is inert on the only corpus in
# use. Not broken: it answers a question Flickr's metadata does not contain.
#
# What Flickr does give is the TITLE, already sitting in the local index row, free to read. Run
# against the 24 machine-passed faces on 2026-08-10 it refused 15, and three of those had
# survived BOTH the vision gate and a careful look at the frame by eye:
#
#   m3039-wh-02  "Sam Rockwell en la presentación de Moon"          an actor, at a premiere
#   m3039-bl-01  "Stéphane Diagana se prète au jeu de l'interview"  a world champion, interviewed
#   f5059-wh-01  "Anita Ravna juni 2013"                            by a Sami political body
#
# recognizable_public_figure answered false for all three, and answered honestly. It asks the
# model what it KNOWS, and being famous is not a property of pixels — it is a property of the
# caption. Asking a photograph to disclose who someone is was always the wrong place to look,
# which is why adding sharper questions about the FRAME could never have closed this hole.
#
# Two adjacent capitalised words is a deliberately blunt test and it does misfire: "Kirkby
# Malzeard" is a village, "I'm Young" came off a t-shirt, about one in eight. The trade is not
# close. A false positive costs one photograph out of nine million candidates; a false negative
# puts a named actor in a supplement advertisement, which is the exact harm the whole CC-sourcing
# posture exists to avoid. Blunt and early beats precise and late.


def named_subject(text):
    """The first run of two or more adjacent name-like words, or None.

    A word qualifies when it opens uppercase, carries a lowercase letter and holds no digit.
    That admits "Rockwell" and "Tennø" while turning away the camera defaults this corpus is
    full of ("DSC07576", "IMG_2914") and bare initialisms ("MRI", "SCA"), which name an
    organisation rather than a person.

    TWO adjacent, because findability is what is being tested rather than naming as such:
    "Megan" alone identifies nobody you could look up, and "Anita Ravna" identifies someone you
    can find in one search.

    KNOWN BLIND SPOT, MEASURED RATHER THAN GUESSED. The whole test is built on letter case, so it
    cannot see a name written in a script that has none. 250 of the 11,345 walkable rows (2.2%)
    carry a title with no cased letter at all — 182 punctuation/numeric, then CJK 39, Hangul 9,
    Arabic 9, Katakana 7, Devanagari 2, Hebrew 1, Hiragana 1. "구본준 부회장" (a named vice
    chairman) passes this gate untouched, and so would any Han-character personal name.

    Left unfixed on purpose. A CJK name detector would have to guess from length — most of the
    real sample is scenery, not people ("模糊總是最美", "貨物整理中") — so it would refuse honest
    photographs to catch a handful, over 2.2% of the corpus. What covers those rows instead is the
    vision rubric's recognizable_public_figure / official_or_representative_capacity /
    identifying_text_in_frame. That is a weaker backstop, not an equal one: it asks the model what
    it KNOWS, which is the exact failure that made this gate necessary. So 2.2% of the walk is
    screened by the old, weaker instrument. Worth stating plainly rather than filing as done."""
    run = []
    for word in re.split(r"[^\w'’-]+", text or "") + [""]:
        word = word.strip("'’-")
        if (word and word[0].isupper() and any(c.islower() for c in word)
                and not any(c.isdigit() for c in word)):
            run.append(word)
        else:
            if len(run) >= 2:
                return " ".join(run)
            run = []
    return None


def gate_named_subject(cand):
    """Gate P2. Title only — no download, no model call, and no second opinion needed."""
    title = (cand.get("title") or (cand.get("raw") or {}).get("title") or "").strip()
    name = named_subject(title)
    if name:
        return False, ("title names someone (%r in %r) — the caption is the one piece of "
                       "evidence a vision model never sees, and a named subject is precisely "
                       "the publicity-rights claim a CC licence does not grant"
                       % (name, title[:60]))
    return True, ""


# --------------------------------------------------------------------------------------
# GATE C — re-host origin
# --------------------------------------------------------------------------------------
# Pexels, Unsplash, nappy and StockSnap are permanently out of this pipeline, and not on
# licence grounds: their own terms of service forbid using their photographs for machine
# learning, dataset building or model training, which is what anchoring a generator on a
# reference image is. That prohibition attaches to the PHOTOGRAPH, so it survives the trip
# through a mirror. Commons re-hosts a large number of them under a CC tag applied by the
# uploader, and prior sourcing passes had already scored several as usable picks.
#
# A mirror does not dissolve the origin's terms. Read the Credit/Artist HTML, which is where
# Commons records where a re-hosted file came from, and refuse on a match.
BANNED_ORIGINS = ("nappy.co", "unsplash.com", "pexels.com", "stocksnap.io", "pixabay.com",
                  "freepik.com", "burst.shopify.com", "reshot.com")


def gate_origin(cand):
    """Returns (ok, reason)."""
    blob = " ".join(str(cand.get(k) or "") for k in ("credit_blob", "author", "page_url")).lower()
    for host in BANNED_ORIGINS:
        if host in blob:
            return False, ("re-hosted from %s, whose own terms forbid using the photograph for "
                           "machine learning / dataset use — a mirror does not dissolve the "
                           "origin's terms" % host)
    return True, ""


# --------------------------------------------------------------------------------------
# GATE 1 — licence
# --------------------------------------------------------------------------------------
def gate_artwork(cand):
    """Gate A. A photograph OF a painting is not a photograph of a person, and every hour of
    this corpus is full of them. Title and description only — no download, no model call."""
    blob = "%s %s %s" % (cand.get("title") or "", (cand.get("raw") or {}).get("title") or "",
                         _strip_html((cand.get("raw") or {}).get("description") or ""))
    m = ARTWORK_RE.search(blob)
    if m:
        return False, ("title/description reads as artwork or an archive reproduction (%r) — "
                       "gate 5 would reject it as 'not a camera photograph' after paying for "
                       "the model call" % m.group(0))
    return True, ""


def gate_license(cand):
    """Read the licence back from the response; never assume the search filter held.
    Returns (license_slug, info_or_None, reason).

    Flickr answers with a numeric id whose meaning is Flickr's alone, so its backend translates
    to a slug at the boundary and the untranslatable ids keep their spelled-out refusal here."""
    raw = str(cand.get("license", "")).strip()
    if raw in FORBIDDEN_LICENSES:
        return raw, None, "licence %s forbidden: %s" % (raw, FORBIDDEN_LICENSES[raw])
    slug = cand.get("licence_slug") or FLICKR_ID_TO_SLUG.get(raw) or raw
    info, reason = licence_ok(slug)
    return slug, info, reason


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


# Flickr rate-limits the ORIGINAL size specifically, not the caller. Measured 2026-08-10: after
# a run at --download-concurrency 8, `_o.jpg` returned HTTP 429 on 12 of 12 serial requests half
# an hour later — while `_k`, `_h`, `_b` and the plain size all returned 200 for the SAME photo,
# in the same second, on the same connection. The limiter is attached to the resource, not to us,
# so backing off would have waited out a penalty that was never going to end on its own. The fix
# is to stop asking for the one size that is metered.
#
# `_k` is the 2048px-long-edge rendition, and it is not merely acceptable — it is everything the
# gates need. The watermark screen already works on a 720px copy (WM_WORK_EDGE), dHash resizes to
# 9x8 and is scale-free, and 2048 is two and a half times MIN_SHORT_EDGE. Flickr never upscales,
# so `_k` returns min(original, 2048) on the long edge: a small original arrives at its true size
# and fails the floor honestly, exactly as it would have.
#
# The one behaviour that changes: an ultra-wide original near the floor (say 2400x800, short edge
# 800) passed before and now arrives as 2048x683 and is refused. That is a stricter gate, not a
# looser one, and a 3:1 panorama was never going to be a usable ima2 face anchor.
#
# `_o` is deliberately NOT a rung. Falling back to it would reintroduce the metered resource one
# candidate at a time, which is the failure this ladder exists to end.
FLICKR_SIZE_LADDER = (("_k", "flickr-2048"), ("_h", "flickr-1600"))


def flickr_size_ladder(original_url):
    """[(url, label)] to try in order for a Flickr static URL, largest unmetered size first.

    Anything that is not a recognisable `_o` original is passed through untouched — a URL we
    cannot parse is not a URL we should be rewriting."""
    if not str(original_url or "").endswith("_o.jpg"):
        return [(original_url, "as-given")]
    stem = original_url[:-len("_o.jpg")]
    return [(stem + suf + ".jpg", label) for suf, label in FLICKR_SIZE_LADDER]


def largest_size(cand, key, session, allow_getsizes=True, sleep=0.0):
    """Largest DOWNLOADABLE size, dispatched on the backend that produced the candidate.

    Commons hands back the full asset's real geometry in the same response as the metadata, so
    its candidates arrive with `sizes` already complete and there is nothing further to ask.
    Open Images knows the original's byte count but not its geometry, so it returns zeros and
    the measurement moves to after the download — an honest "not known yet" rather than a
    guessed width the resolution gate would treat as fact.
    Flickr is the awkward one and the rest of this function is about it."""
    if cand.get("platform") == "openimages":
        rungs = flickr_size_ladder(cand["download_url"])
        return (0, 0, 0, rungs[0][0], rungs[0][1])
    if cand.get("platform") != "flickr":
        sizes = cand.get("sizes") or []
        return max(sizes) if sizes else None
    photo = cand.get("raw") or cand
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
# GATE 2.5 — greyscale screen
# --------------------------------------------------------------------------------------
def monochrome_screen(img):
    """Returns (flagged, detail). Catches TRUE greyscale only — deliberately.

    A black-and-white photograph is useless as a bank reference: ima2 anchors skin tone, hair
    colour and lighting on the ref, and there is none to anchor on. The bank had one
    (m6070-hl-01) and nothing measured it.

    The tempting move is a chroma threshold that also catches sepia and period photographs. It
    does not work, and the measurement is worth recording so nobody re-derives it. Across the
    whole bank on 2026-08-10:

        f3039-wh-04  a 1940s black-and-white photograph   p95 chroma 21, max  71
        f6070-wh-05  a colour studio portrait, grey seamless, cream cardigan
                                                          p95 chroma 10, max  88

    The period photograph is MORE colourful than the colour photograph by p95, because chroma
    statistics measure how colourful the SCENE is, not whether the film was. Hue coherence does
    not separate them either (R=0.09 for the period shot, 0.99 for the colour one — but 0.15
    for f4049-bl-01, a perfectly ordinary colour photograph, because many hues and pure chroma
    noise both read as incoherent). Any cut that catches the sepia one also throws away candid
    photographs taken in muted winter or indoor light, which is most of the good ones.

    So: pixels answer only the question pixels can answer. True greyscale has essentially no
    coloured pixels at all — zero above chroma 12 for m6070-hl-01, against 1.8% above chroma 30
    for the nearest colour image — and that gap is three orders of magnitude wide. Sepia, toning
    and period stock are handed to the vision rubric (`is_monochrome_or_period`), which is
    already looking at the photograph and can simply see it.

    A FRACTION rather than a max, because a single stray coloured pixel — a date stamp, a
    scanner artefact, one hot JPEG block — must not be able to certify a black-and-white scan
    as colour.
    """
    g = img.convert("RGB").copy()
    g.thumbnail((256, 256), Image.LANCZOS)
    a = np.asarray(g, dtype=np.int16)
    chroma = a.max(axis=2) - a.min(axis=2)
    frac = float((chroma > MONO_CHROMA).mean())
    return frac < MONO_MIN_FRACTION, "coloured-pixel fraction %.5f (floor %.5f)" % (
        frac, MONO_MIN_FRACTION)


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
    '"is_monochrome_or_period": true|false, '
    '"face_angle_reads": "frontal"|"three-quarter"|"profile"|"down-or-away", '
    '"studio_or_press_context": true|false, '
    '"official_or_representative_capacity": true|false, '
    '"identifying_text_in_frame": true|false, "minor_in_frame": true|false, '
    '"apparent_ethnicity": "<short phrase>", '
    '"ethnicity_group": "white"|"hispanic"|"black"|"asian"|"other"|"unclear", '
    '"notes": "<one short sentence>"}\n'
    "Definitions. is_camera_photograph: false for AI-generated, CGI, 3D render, painting, "
    "drawing or illustration. person_count: humans whose face is at least partly in frame. "
    "is_monochrome_or_period: true for black-and-white, greyscale, sepia, hand-tinted, "
    "duotone or otherwise colour-less photography, AND for any photograph that reads as "
    "historical rather than contemporary - period clothing, a vintage print, film-era "
    "processing. face_angle_reads: which ONE describes the head - frontal (both eyes and both "
    "cheeks visible, squarely toward camera), three-quarter (turned partly away, the far eye "
    "still visible), profile (side-on, only one eye visible), down-or-away (chin dropped "
    "toward the chest, head turned past profile, or the face otherwise not readable as a "
    "portrait). studio_or_press_context: true for a seamless studio backdrop, a professional "
    "headshot, a stage or podium, a press conference, a red carpet or any other posed "
    "media-production setting. "
    "official_or_representative_capacity: is the subject shown ACTING FOR someone other than "
    "themselves - speaking at a lectern, podium or on a stage, holding or wearing a "
    "presentation microphone, at a press conference or official backdrop, wearing a uniform or "
    "official insignia, or posed for a formal institutional portrait (faculty, corporate, "
    "party, government). Doing a job is NOT enough on its own: a chef cooking, a mechanic under "
    "a car or a nurse on a ward is working, not representing. Answer only from what the "
    "photograph shows; do not consider whether you recognise the person. "
    "identifying_text_in_frame: text anywhere in frame that could identify a SPECIFIC person, "
    "team, employer or private event - a personal name, a sports jersey bearing a team name or "
    "squad number, a name badge, a shirt printed for someone's party or wedding, a company "
    "uniform logo. Ordinary background signage, brand marks on ordinary clothing and unreadable "
    "text do not count. "
    "minor_in_frame: is any child, infant or baby present anywhere in the frame, INCLUDING one "
    "whose face is turned away, covered, asleep or inside a carrier, sling or pram. Answer this "
    "independently of person_count. "
    "face_obscured: sunglasses, a hand, a mask, hair or heavy shadow covering the face. "
    "beauty_filtered: skin smoothing, blemish removal, catalogue-style retouching, beauty-app "
    "filtering. visible_text_or_watermark: ANY burned-in text, credit line, logo, date stamp or "
    "signature anywhere in the frame. recognizable_public_figure: a celebrity, politician, "
    "athlete or other identifiable public person. ethnicity_group: which ONE of the five US "
    "census-style groups the person most plausibly reads as - white (white non-Hispanic), "
    "hispanic (Hispanic or Latino of any race), black (Black or African American), asian "
    "(East, Southeast or South Asian), other (Middle Eastern/North African, Native American, "
    "Pacific Islander, visibly multiracial). Answer \"unclear\" only when the image genuinely "
    "does not support a call; a guess you would not defend is worse than \"unclear\"."
)

# The free-text `apparent_ethnicity` was always advisory — the bank's own ethnicity_note says
# the gate REPORTS it and does not enforce it. That was survivable while queries carried the
# demographic ("african american woman kitchen"), because the search engine did the sorting.
# Open Images has no such lever: it is one undifferentiated pool of 15k faces, so if nothing
# enforces ethnicity then all 25 non-white cells fill with whatever the corpus skews toward,
# which the dataset's own card warns is Western. Hence a constrained token the taxonomy can
# actually match on, and a free-text phrase kept alongside it for a human to check by eye.
ETHNICITY_GROUP_TO_KEY = {
    "white": "wh", "hispanic": "hl", "black": "bl", "asian": "as", "other": "mx",
}

# Keys the rubric gained on 2026-08-10. The ~470 vision readings already banked in
# verdicts.jsonl predate them, and there is no way to answer them from a cached JSON — only
# from the photograph. evaluate_vision therefore treats a MISSING key as "not asked" rather
# than as a pass, and process_candidate re-asks the model for exactly those candidates that
# would otherwise be accepted. Cached REJECTIONS still replay for free (a period photograph
# cannot stop being the wrong gender), so the re-ask costs one call per face we were about to
# write into the bank anyway, not one per cached row.
# The second batch, added after the eye-QC of 2026-08-10 threw out 10 of 24 machine-passed
# faces. Two of those three gates already existed and were already enforced, which is the whole
# lesson: the model was not wrong, it was answering a different question from the one that
# mattered.
#
#   recognizable_public_figure asks about the MODEL'S knowledge. It answered false for a Chilean
#   ex-minister at a government lectern, an SFU faculty portrait and a Peruvian police officer —
#   honestly, because it does not know who any of them are. Whether a stranger is famous is
#   unanswerable from pixels; whether a photograph SHOWS someone speaking for an institution is
#   plainly visible, and it is the second question that decides the publicity-rights class.
#
#   visible_text_or_watermark was written for credit lines and date stamps, so the model read
#   "CEDAR RAPIDS 5" off a jersey and a shirt printed "affinity's 60th birthday", described both
#   in its notes, and still answered false. Not a contradiction — burned-in overlay and printed
#   garment text are different things, and only one of them names a person.
#
#   person_count is defined here as faces at least partly in frame, so a baby carried facing its
#   mother is correctly NOT counted. Correct, and not what I need to know.
#
# In every case the free-text `notes` field described the disqualifying thing accurately while
# the boolean beside it said no. The fix is a sharper question, not a better model — and the
# reason to ask rather than to keyword-scan the notes is that a question has a defined answer
# and prose does not.
VISION_RUBRIC_KEYS_ADDED = ("is_monochrome_or_period", "face_angle_reads",
                            "official_or_representative_capacity",
                            "identifying_text_in_frame", "minor_in_frame")
# A profile ref makes most of the 21-angle vocabulary unreachable: article_images.py anchors
# identity on ref.jpg, and asking ima2 for `front-level` from a 90-degree profile is asking it
# to invent the half of the face it was never shown. f3039-wh-06 is exactly that photograph.
FACE_ANGLE_ACCEPTED = ("frontal", "three-quarter")


# How many independent readings must agree before a face is written. See the CONFIRMATION note
# in process_candidate for the measurement that set this at two; the keys are positional so a
# third would only mean extending these tuples.
VISION_CONFIRMATIONS = 2
VISION_KEYS = ("vision", "vision2")
RAW_KEYS = ("raw", "raw2")


def vision_is_current(v):
    """Was this reading taken with the rubric we enforce today?"""
    return isinstance(v, dict) and all(k in v for k in VISION_RUBRIC_KEYS_ADDED)


def vision_readings(cached):
    """Every reading held for this image, oldest first. Rows written before the confirming call
    existed carry one; that is a shortfall to make up, not a reason to distrust the reading."""
    return [v for v in ((cached or {}).get(k) for k in VISION_KEYS) if isinstance(v, dict)]


def current_readings(cached):
    """(reading, raw text) for each held reading taken under today's rubric, oldest first.

    Paired by POSITION rather than zipped after the fact: `vision2` is stored beside `raw2`, and
    a row that somehow carries one without the other must not silently hand back the other
    reading's text as if it were the audit trail for this one.
    """
    out = []
    for vk, rk in zip(VISION_KEYS, RAW_KEYS):
        v = (cached or {}).get(vk)
        if vision_is_current(v):
            raw = (cached or {}).get(rk)
            out.append((v, raw if isinstance(raw, str) else ""))
    return out


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


def vision_is_transient(message):
    """Is this gem9 failure the router shedding load, or a real fault?

    Split out from vision_check purely so it is testable without a subprocess: the cost of
    getting it wrong is asymmetric and silent. Too broad and a genuine 400 gets retried
    three times per candidate; too narrow and a load blip ends the run through
    VISION_INFRA_ABORT, which reads to the operator as "this cell has no faces"."""
    return any(code in (message or "") for code in VISION_TRANSIENT)


def vision_check(image_path):
    """Returns (parsed_dict_or_None, raw_output). Raw is stored verbatim in persona.json.

    gem9 reports its own failures with sys.exit("gem9: HTTP 429: {...}") — a JSON error body
    on STDERR with a non-zero exit. Concatenating stderr into the parse made that body look
    like a verdict: it parses, it has no is_camera_photograph key, and every candidate came
    back rejected as "not a camera photograph". Read the exit status, and parse stdout only.

    Retried, for the same reason the download is. Measured 2026-08-10: a lone gem9 call
    answers in 5.5s, but six concurrent ones drew five straight `HTTP 502` from 9router — and
    a 502 is the router shedding load, which says nothing whatever about the photograph. Left
    unretried it took a run out through VISION_INFRA_ABORT, which is precisely the misreading
    that guard exists to prevent, arriving one layer lower down. Only transient statuses are
    retried; a malformed answer is not made truer by asking twice.
    """
    last = None
    for attempt in range(3):
        # Held around the call only. Sleeping through the back-off inside the gate would idle
        # a slot for everyone else, which is the failure this gate exists to stop.
        with _VISION_GATE:
            res = subprocess.run([GEM9, "-p", VISION_RUBRIC, image_path],
                                 capture_output=True, text=True, timeout=VISION_TIMEOUT)
        if res.returncode == 0:
            raw = (res.stdout or "").strip()
            parsed = _extract_json(raw)
            if parsed is not None:
                return parsed, raw
            # Exit 0 with nothing parseable is still an infra symptom, not a judgement on the
            # face — but it is not a load symptom either, so it does not earn a retry.
            raise VisionInfraError("gem9 exited 0 but returned no JSON: %r" % raw[:200])
        last = "gem9 exit %d: %s" % (res.returncode,
                                     (res.stderr or res.stdout or "").strip()[:200])
        if not vision_is_transient(last):
            break
        if attempt < 2:
            # Staggered by attempt AND by worker, or six workers that 502 together simply
            # retry together and reproduce the burst that caused it.
            time.sleep(4 * (attempt + 1) + random.uniform(0, 3))
    raise VisionInfraError(last)


ETHNICITY_PHRASE_HINTS = (
    # Ordered: the first hit wins, so the more specific phrase has to come first. "african
    # american" before "american", "south asian" before "asian", or a substring match places
    # the face in the wrong cell while looking like it worked.
    ("wh", ("white", "caucasian", "european", "anglo")),
    ("hl", ("hispanic", "latino", "latina", "latinx", "mexican", "puerto rican", "cuban")),
    ("bl", ("african american", "black", "afro", "african")),
    ("as", ("south asian", "east asian", "southeast asian", "asian", "chinese", "japanese",
            "korean", "indian", "filipino", "vietnamese", "thai")),
    ("mx", ("middle eastern", "north african", "mena", "arab", "native american",
            "indigenous", "pacific islander", "multiracial", "mixed")),
)


def ethnicity_key_of(v):
    """The taxonomy ethnicity key this verdict places the face in, or None.

    Two readings, in order of trust. `ethnicity_group` is a constrained token the rubric asks
    for outright, so it needs no interpretation. The free-text `apparent_ethnicity` is the
    fallback, and it exists because verdicts cached before the token was added would otherwise
    all have to be re-bought — a cache of thousands of model calls is worth a keyword table.
    Neither is a fact about the person; both are how the photograph reads, which is all a
    demographic-coverage target can ever be about."""
    group = str((v or {}).get("ethnicity_group") or "").strip().lower()
    if group in ETHNICITY_GROUP_TO_KEY:
        return ETHNICITY_GROUP_TO_KEY[group]
    if group == "unclear":
        return None
    phrase = str((v or {}).get("apparent_ethnicity") or "").strip().lower()
    for key, needles in ETHNICITY_PHRASE_HINTS:
        if any(n in phrase for n in needles):
            return key
    return None


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
    # .get, not [], and a REASON rather than a KeyError when the cell declares nothing. This
    # runs on a worker thread, where an exception surfaces as a crashed worker — which the
    # caller counts as a rejected photograph. A malformed taxonomy would then look like a run
    # of bad faces. Failing closed says the same "no" out loud, and the selftest asserts up
    # front that every real cell carries a key the rubric can actually produce.
    want_key = cell.get("ethnicity_key")
    seen_key = ethnicity_key_of(v)
    if not want_key:
        reasons.append("cell %r declares no ethnicity_key — refusing rather than sourcing into "
                       "a cell whose demographic target is unstated" % cell.get("cell_id"))
    elif seen_key is None:
        reasons.append("apparent ethnicity %r could not be placed in any of the five taxonomy "
                       "groups" % (v.get("ethnicity_group") or v.get("apparent_ethnicity")))
    elif seen_key != want_key:
        reasons.append("reads as %r, cell wants %r" % (seen_key, want_key))
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
    # `is True` and `if angle and`, so a reading taken before these keys existed passes here
    # rather than failing — see VISION_RUBRIC_KEYS_ADDED. Absent is "not asked", not "no".
    if v.get("is_monochrome_or_period") is True:
        reasons.append("black-and-white, toned or period photograph")
    angle = str(v.get("face_angle_reads") or "").strip().lower()
    if angle and angle not in FACE_ANGLE_ACCEPTED:
        reasons.append("face reads %r — the bank needs a frontal or three-quarter anchor" % angle)
    if v.get("official_or_representative_capacity") is True:
        # The one gate here that is about the SUBJECT rather than the picture. Anonymity is
        # what the whole CC-sourcing posture rests on: a stranger in a park has a claim in
        # principle, whereas a minister at a lectern or a professor in a faculty portrait is
        # someone whose professional likeness is already managed, and putting theirs behind a
        # supplement ad is the textbook false-endorsement case rather than a remote risk.
        reasons.append("shown in an official or representative capacity (lectern, stage, "
                       "uniform, institutional portrait)")
    if v.get("identifying_text_in_frame") is True:
        # Doubly disqualifying, and the second half is the part that is easy to miss: text that
        # names a team and a squad number does not merely identify him, it makes him findable
        # from a roster — and ima2 anchors on ref.jpg, so it will try to reproduce the lettering
        # into the generated frame as well.
        reasons.append("frame carries text identifying a person, team, employer or private event")
    if v.get("minor_in_frame") is True:
        # A child cannot consent and their guardian has not been asked, so this one is a floor
        # rather than a preference — the same reasoning as MIN_APPARENT_AGE, arriving by way of
        # the background instead of the subject.
        reasons.append("a child or infant is in the frame")
    # studio_or_press_context stays recorded and NOT enforced, and the eye-QC that added the
    # three gates above is also what settled that. Enforcing it would have cost 13 of 45 cached
    # accepts — 29%, and it emptied two of the thinnest cells outright — because it fires on a
    # plain studio portrait of an anonymous model, which is a face the bank wants. It is a proxy
    # for the question above, and now that the question is asked directly the proxy can go back
    # to what it is good for: contact_sheet.py prints it in the caption, so the eye pass sees
    # which frames to look at hardest.
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


def flickr_page_url(photo):
    owner = photo.get("path_alias") or photo.get("owner") or ""
    return "https://www.flickr.com/photos/%s/%s/" % (owner, photo["id"])


def flickr_author(photo):
    for k in ("realname", "ownername", "path_alias", "owner"):
        for v in [(photo.get(k) or "").strip()]:
            if v:
                return v
    return "unknown"


def flickr_search(session, key, text, page, per_page, _cat=None):
    """Returns (candidates, total_pages) in the NORMALIZED shape every gate downstream reads."""
    data = flickr_call(
        session, "flickr.photos.search", key,
        text=text, license=LICENSE_SEARCH_PARAM, safe_search=1, content_types=0,
        media="photos", sort="relevance", per_page=per_page, page=page,
        extras="license,owner_name,url_l,url_o,o_dims,path_alias,realname")
    photos = data.get("photos", {}) or {}
    out = []
    for p in photos.get("photo", []) or []:
        lic = str(p.get("license", "")).strip()
        out.append({
            "platform": "flickr",
            "id": str(p.get("id")),
            "title": (p.get("title") or "").strip(),
            "page_url": flickr_page_url(p),
            "author": flickr_author(p),
            "license": lic,                          # the raw id, so FORBIDDEN_LICENSES still speaks
            "licence_slug": FLICKR_ID_TO_SLUG.get(lic, ""),
            "sizes": sizes_from_extras(p),
            # Flickr exposes no personality-rights flag of any kind. Empty is honest here: the
            # gate is a one-way valve, so an absent flag was never a clearance anyway.
            "restrictions": "",
            "credit_blob": "",
            "raw": p,
        })
    return out, int(photos.get("pages", 0) or 0)


# --------------------------------------------------------------------------------------
# Wikimedia Commons
# --------------------------------------------------------------------------------------
# The only backend that needs no account, no key and no registration, which is the whole reason
# it is the default. Its Terms of Use were read in full on 2026-08-10: zero occurrences of
# "machine learning", "artificial intelligence", "dataset", "training" or "data mining", so
# unlike Pexels and Unsplash there is no ToS bar on using a file as a generator reference.
#
# What it is NOT is a bank of two hundred ordinary faces. Measured the same day: the whole
# structured-data human corpus under one licence is ~5,400 files, and it skews hard to named
# public figures, Wikimedia event photography, museum sculpture and archive scans — gate 5
# rejects those on `recognizable_public_figure`, but only after paying for the model call.
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
COMMONS_MIMES = ("image/jpeg", "image/png")
# One of the widths Commons' own download widget offers, so the render is normally cached
# already. See commons_candidate for why we fetch a thumbnail rather than the original at all.
COMMONS_THUMB_WIDTH = 2560
# One at a time, NEVER OR-ed. `incategory:A OR incategory:B` over two 8-million-file categories
# returns 974 results; the parser does not mean by it what a reader assumes it means.
#
# ORDER IS NOT COSMETIC, and it is the opposite of what it should intuitively be. CC0 asks for
# no attribution, so walking it first looks like the frugal choice. Measured 2026-08-10: it is
# the worst one. `incategory:"CC-zero" filetype:bitmap woman` returns the Metropolitan Museum's
# public-domain dump almost exclusively — Portrait_of_a_Woman_MET_DP161260, Marble_head_of_a_
# woman, Terracotta_statue, furniture plaques. Institutions releasing scans of dead artists'
# work pick CC0; living photographers uploading their own pictures pick CC BY. The licence
# correlates with the KIND of uploader, so the attribution-free category is precisely the one
# with no photographs of living people in it. CC BY 4.0 first, and it is also the newest
# instrument (2013+), so it skews to modern uploads rather than mass archive imports.
COMMONS_LICENCE_CATEGORIES = ("CC-BY-4.0", "CC-BY-3.0", "CC-BY-2.0", "CC-zero")

# Cheap string kill-list, run on title+description BEFORE anything is downloaded or shown to a
# vision model. The gate-5 rejections it replaces cost a gem9 call each and came back as
# "not a camera photograph (AI/CGI/illustration)" — technically right about a Vermeer, and a
# wasteful way to learn that a painting is not a photograph.
ARTWORK_RE = re.compile(
    # `met[ _]d[pt]` alone never fires: the accession runs on into digits (MET DP354965), so the
    # group's trailing \b lands between "P" and "3" and fails. \w* has to eat the number.
    r"\b(met[ _](?:d[pt]|ap|sf)\w*|painting|portrait of a|study of a|marble|terracotta|bronze|"
    r"statue|statuette|bust|relief|plaque|engraving|etching|lithograph|woodcut|drawing|"
    r"sketch|illustration|manuscript|fresco|mosaic|icon|sculpture|figurine|vase|amphora|"
    r"coin|medal|stamp|postcard|poster|caricature|cartoon|tapestry|embroidery|"
    r"daguerreotype|ambrotype|tintype|glass[ _]negative|cabinet[ _]card|carte[ _]de[ _]visite)\b",
    re.I)


class CommonsError(RuntimeError):
    pass


def commons_call(session, params, sleep=0.0, tries=4):
    """POST, always. A 50-title GET exceeds the URL length the API accepts and comes back 414;
    the failure looks like a network fault rather than a request that was too long.

    Anonymous callers get 429s in bursts, so back off and retry rather than treating a throttle
    as evidence about the photographs — the same trap largest_size() documents for Flickr."""
    body = dict(params, format="json", formatversion="2")
    for attempt in range(tries):
        if sleep:
            time.sleep(sleep)
        try:
            r = session.post(COMMONS_API, data=body, timeout=60)
        except requests.RequestException as exc:
            raise CommonsError("network: %s: %s" % (type(exc).__name__, exc))
        if r.status_code == 429:
            if attempt == tries - 1:
                raise CommonsError("HTTP 429 after %d attempts — throttled, not empty" % tries)
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code != 200:
            raise CommonsError("HTTP %s" % r.status_code)
        try:
            data = r.json()
        except ValueError:
            raise CommonsError("non-JSON response")
        if "error" in data:
            raise CommonsError("api: %s" % (data["error"].get("info") or data["error"]))
        return data
    raise CommonsError("unreachable")


def _strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(s or ""))).strip()


def commons_candidate(page):
    """One search hit -> the normalized shape, or None when it is not a usable image at all."""
    ii = (page.get("imageinfo") or [{}])[0]
    if (ii.get("mime") or "") not in COMMONS_MIMES:
        return None
    em = ii.get("extmetadata") or {}

    def meta(k):
        return str((em.get(k) or {}).get("value", "") or "").strip()

    # Prefer the rendered thumbnail over the original asset. This is not a bandwidth nicety:
    # upload.wikimedia.org 429s originals aggressively and the body of its own 429 says to
    # "instead use thumbnail images in sizes listed on https://w.wiki/GHai". Measured 2026-08-10:
    # a run against originals came back 43/60 [throttled] — two thirds of the corpus was never
    # judged, and a rate limit read as an empty corpus. COMMONS_THUMB_WIDTH is one of the widths
    # Commons itself offers, so the render is usually already cached and costs them nothing.
    thumb, tw, th = ii.get("thumburl") or "", ii.get("thumbwidth"), ii.get("thumbheight")
    url = thumb or ii.get("url") or ""
    # The asset URL now carries an ?utm_source= tail. Left on, it becomes part of the cache key
    # and of the provenance record, so two fetches of one file look like two files.
    url = url.split("?", 1)[0]
    try:
        if thumb and tw and th:
            w, h, label = int(tw), int(th), "commons-thumb-%d" % COMMONS_THUMB_WIDTH
        else:
            w, h, label = int(ii.get("width") or 0), int(ii.get("height") or 0), "commons-original"
    except (TypeError, ValueError):
        w = h = 0
        label = "commons-original"
    title = page.get("title") or ""
    return {
        "platform": "commons",
        "id": str(page.get("pageid") or title),
        "title": _strip_html(meta("ObjectName")) or title[5:],
        "page_url": "https://commons.wikimedia.org/wiki/" + urllib_quote(title),
        "author": _strip_html(meta("Artist")) or "unknown",
        "license": "",
        "licence_slug": meta("License").lower(),
        # One entry only, deliberately. Listing the original alongside the thumbnail would let
        # largest_size pick the original again and quietly undo the throttle fix.
        "sizes": [(w * h, w, h, url, label)] if (w and h and url) else [],
        "restrictions": meta("Restrictions"),
        # Credit and Artist are HTML and are where a re-hosted file names where it came from.
        # Keep them raw, unstripped: gate C matches on the href, which _strip_html would delete.
        "credit_blob": "%s %s" % (meta("Credit"), meta("Artist")),
        "raw": {"pageid": page.get("pageid"), "title": title, "description": meta("ImageDescription")},
    }


def urllib_quote(s):
    return requests.utils.quote(str(s).replace(" ", "_"), safe=":/")


def commons_search(session, _key, text, page, per_page, licence_category=None):
    """Returns (candidates, total_pages).

    `text` is AND-ed term by term — Commons full-text is not Flickr's fuzzy `text=`. Four scene
    words return zero where two return hundreds, which is why the Commons query composer builds
    SHORT queries and the Flickr one does not."""
    cat = licence_category or COMMONS_LICENCE_CATEGORIES[0]
    # filetype:bitmap is doing real work: namespace 6 is full of book scans and DjVu, and a
    # plain `man kitchen candid portrait` search returns PDFs of Victorian novels.
    srsearch = 'incategory:"%s" filetype:bitmap %s' % (cat, text)
    limit = min(int(per_page or 50), 50)   # 50 is the anonymous ceiling; asking 500 does not raise it
    data = commons_call(session, {
        "action": "query", "generator": "search", "gsrsearch": srsearch,
        "gsrnamespace": 6, "gsrlimit": limit, "gsroffset": max(0, (page - 1) * limit),
        "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime",
        # Asking for a width is what makes the API hand back a thumburl at all. 2560 rather than
        # 1280 because 1280 wide on a 16:9 frame is 720 tall — under our 800px short edge — so
        # the cheaper thumbnail would reject good photographs for a reason that has nothing to
        # do with the photograph. MediaWiki never upscales: when the original is smaller there
        # is no thumburl and commons_candidate falls back to it.
        "iiurlwidth": COMMONS_THUMB_WIDTH,
    })
    pages = (data.get("query") or {}).get("pages") or []
    out = [c for c in (commons_candidate(p) for p in pages) if c]
    # The API reports no page count for a generator search; "one more page exists if this one
    # came back full" is the honest reading, and cmd_fetch's own caps bound the walk.
    return out, (page + 1 if len(pages) >= limit else page)


# --------------------------------------------------------------------------------------
# Open Images  (key-free, and it never touches flickr.com)
# --------------------------------------------------------------------------------------
# Google publishes, in a plain public bucket, both the licence/URL metadata for the CC BY 2.0
# half of Flickr AND the MIAP annotations ("More Inclusive Annotations for People"), which box
# every person with a PERCEIVED gender and age presentation. That second file is the whole
# reason this backend exists. On Commons the dominant rejections were person_count != 1 and
# gender != cell — two questions no Commons metadata can answer, so we were paying a ~28s model
# call to ask them. MIAP answers both for nothing, before a single byte of pixel is fetched.
#
# On not crawling Flickr: flickr.com/robots.txt is `User-agent: * / Disallow: /`, with /search
# additionally denied even to the named allow-list. So we do not fetch a single page of it. The
# metadata comes from storage.googleapis.com and the pixels from staticflickr.com, whose own
# robots.txt is the single comment "# Nothing to see here" — no directives, nothing disallowed.
# The photo page URL is recorded for attribution, which CC BY 2.0 requires, and never requested.
OPENIMAGES_MIN_BYTES = 250_000
_OPENIMAGES_POOL = None
_OPENIMAGES_LOCK = threading.Lock()


def openimages_pool():
    """The whole index, loaded once. ~15k rows and about 1.5MB gzipped — small enough that
    paging it from memory is simpler and faster than any query engine we would have to keep."""
    global _OPENIMAGES_POOL
    with _OPENIMAGES_LOCK:
        if _OPENIMAGES_POOL is None:
            if not os.path.exists(OPENIMAGES_INDEX):
                sys.exit("✗ no Open Images index at %s — build it first:\n    python3 %s"
                         % (OPENIMAGES_INDEX, os.path.join(OPENIMAGES_DIR, "build_index.py")))
            with gzip.open(OPENIMAGES_INDEX, "rt") as fh:
                _OPENIMAGES_POOL = json.load(fh)
        return _OPENIMAGES_POOL


def openimages_candidate(rec):
    """One index row -> the normalized shape the gates already speak.

    `sizes` is deliberately EMPTY. Open Images records the original's byte count but not its
    geometry, and inventing a plausible-looking width here would be worse than admitting we do
    not know one: largest_size would hand the pre-download resolution gate a number that came
    from nowhere. process_candidate measures the real thing after the download instead."""
    return {
        "platform": "openimages",
        "id": rec["image_id"],
        "title": rec.get("title") or "",
        # The Flickr photo page. Recorded because CC BY 2.0 attribution points at it; never fetched.
        "page_url": rec.get("landing") or "",
        "author": rec.get("author") or "unknown",
        "license": "",
        "licence_slug": "cc-by-2.0",
        "sizes": [],
        "download_url": rec["url"],
        "restrictions": "",
        "credit_blob": "%s %s" % (rec.get("author") or "", rec.get("author_url") or ""),
        "raw": {"image_id": rec["image_id"], "split": rec.get("split"),
                "bytes": rec.get("bytes"), "miap_gender": rec.get("gender"),
                "miap_age": rec.get("age"), "box": rec.get("box"),
                "description": rec.get("title") or ""},
    }


def openimages_search(session, _key, text, page, per_page, _scope=None):
    """Returns (candidates, next_page). `text` is a filter descriptor, not a search phrase.

    There is no server here: the pool is local, so "search" means slice it. The order is
    shuffled under a FIXED seed derived from the filter — deterministic, so a re-run resumes
    the same walk rather than re-judging the same first page, but not corpus order, which on
    Open Images is upload order and would hand one cell a decade of one photographer."""
    want_gender = want_age = None
    for part in str(text or "").split(";"):
        k, _, val = part.partition("=")
        k = k.strip()
        if k == "gender":
            want_gender = val.strip()
        elif k == "age":
            want_age = val.strip()
    rows = [r for r in openimages_pool()
            if r.get("bytes", 0) >= OPENIMAGES_MIN_BYTES
            and (want_gender is None or r["gender"] == want_gender)]
    rows.sort(key=lambda r: r["image_id"])
    # Seeded on the GENDER alone, never on the whole descriptor. Every cell of one gender then
    # walks the same canonical order, which is what makes the verdict cache pay: cell two
    # replays cell one's judgements instead of judging a fresh shuffle of the same corpus.
    random.Random("openimages|gender=%s" % want_gender).shuffle(rows)
    if want_age:
        # A stable partition ON TOP of that order, applied after the shuffle so the preferred
        # rows keep their relative places. This is an ORDERING, not a filter: nothing is
        # excluded, the rest follow immediately behind, and vision still decides the band.
        # It exists because the corpus is lopsided — 13,639 rows read "Middle" against 877
        # "Older" — so a 60-70 cell walking the default order judges several hundred
        # thirty-somethings for every face it can use.
        rows = ([r for r in rows if r.get("age") == want_age]
                + [r for r in rows if r.get("age") != want_age])
    limit = max(1, int(per_page or 50))
    lo = max(0, (page - 1) * limit)
    chunk = rows[lo:lo + limit]
    return [openimages_candidate(r) for r in chunk], (page + 1 if len(chunk) >= limit else page)


SEARCH_BACKENDS = {"commons": commons_search, "flickr": flickr_search,
                   "openimages": openimages_search}


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


# What a quarantine was ABOUT, and therefore how far it reaches. Only a fault in the photograph
# itself travels with the pixels; the other two are faults in what we wrote down beside them, and
# barring the image for those would punish the photograph for our own bookkeeping.
QUARANTINE_LOCAL = (
    "pairing",    # she reads 52, not 45 — right face, wrong drawer; the next band should take her
    "metadata",   # we recorded the wrong photographer/licence; the bug is fixed, the pixels never
                  # were the problem, and a fresh walk records it correctly
)


def quarantine_blocks_readmission(doc):
    """Does this quarantine bar the face from the whole bank, or only from the cell it left?

    Default is the whole bank. A quarantine written before this distinction existed carries no
    `rejection_is_about` at all, and the safe reading of silence is the stricter one: a face
    wrongly barred can be released by hand, whereas a face wrongly re-admitted comes back silently
    under a new handle. Every such row has since been stamped explicitly, so the default now
    guards only future carelessness.
    """
    return (doc or {}).get("rejection_is_about") not in QUARANTINE_LOCAL


def quarantine_index():
    """(handle -> dhash, {photo_id}) for faces MOVED OUT of the bank, so it cannot re-admit them.

    persona_dirs() skips `_`-prefixed directories, which is what keeps a quarantined face out of
    the cell counts — and is also what would let the next walk over the same corpus find the same
    photograph, judge it again, and write it straight back in. Rejecting a face has to be a fact
    the bank remembers, not just a directory that moved.

    Deliberately hash-only, and deliberately separate from load_bank(): quarantine is a graveyard,
    not a shadow bank. Nothing here should ever be counted, picked, or approved.
    """
    out, photo_ids = {}, set()
    for qdir in sorted(glob.glob(os.path.join(PERSONAS, "_quarantine-*"))):
        for name in sorted(os.listdir(qdir)):
            pj = os.path.join(qdir, name, "persona.json")
            if not os.path.exists(pj):
                continue
            label = "%s/%s" % (os.path.basename(qdir), name)
            doc = _load(pj, "quarantined persona.json") or {}
            # The same split process_candidate already makes about cached verdicts: "the head is
            # in profile" is a fact about the PHOTOGRAPH and disqualifies it everywhere, while
            # "she reads 52, not 45" is a fact about the PAIRING and disqualifies it only from
            # the cell that happened to look. A boundary face is not a bad face — she is a face
            # in the wrong drawer, and the next band's walk over the same corpus is exactly what
            # puts her in the right one. Refusing her by hash would make that impossible.
            if not quarantine_blocks_readmission(doc):
                continue
            pid = (doc.get("source") or {}).get("photo_id")
            if pid:
                photo_ids.add(str(pid))
            stored = (doc.get("image") or {}).get("dhash")
            try:
                if stored:
                    out[label] = int(stored, 16)
                    continue
            except ValueError:
                pass
            ref = os.path.join(qdir, name, "ref.jpg")
            if os.path.exists(ref):
                out[label] = dhash(Image.open(ref))
    return out, photo_ids


AUTHOR_CAP_CELL = 1
AUTHOR_CAP_BANK = 3


def author_key_of(name):
    """Normalised photographer name, or "" when the source recorded none.

    "unknown" is deliberately NOT a key. Open Images leaves the Author field empty on a slice
    of rows, and folding all of those into one bucket would cap that entire slice of the corpus
    at three faces on the strength of a missing string."""
    s = " ".join(str(name or "").split()).lower()
    return "" if s in ("", "unknown") else s


def author_counts(bank, cell_id):
    """(per-cell, whole-bank) photographer tallies for the faces already on disk."""
    per_cell, per_bank = {}, {}
    for rec in bank.values():
        who = author_key_of((rec["doc"].get("source") or {}).get("author"))
        if not who:
            continue
        per_bank[who] = per_bank.get(who, 0) + 1
        if rec["doc"].get("cell_id") == cell_id:
            per_cell[who] = per_cell.get(who, 0) + 1
    return per_cell, per_bank


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
def build_commons_queries(cell):
    """Short AND-ed queries. Broadest first, so a small corpus is not spent on the narrowest
    phrasings — the opposite ordering of what reads naturally."""
    subjects = COMMONS_SUBJECTS[(cell["gender"], cell["age_band"])]
    hints = [h for h in COMMONS_ETHNICITY_HINTS[cell["ethnicity_key"]] if h]
    # Projects first and bare. They are the densest seam in the corpus for the thin cells, and
    # they are the one query shape a scene word can only damage. The age/gender split then
    # comes from the vision gate rather than from the query, which is where it belongs: an
    # adjective is a hint to a search engine, the gate is a measurement.
    out = list(COMMONS_PROJECTS.get(cell["ethnicity_key"], []))
    for subj in subjects:
        out.append(subj)
        for hint in hints:
            out.append("%s %s" % (hint, subj))
    for subj in subjects:
        for scene in COMMONS_SCENES:
            out.append("%s %s" % (subj, scene))
    for hint in hints:
        for scene in COMMONS_SCENES[:4]:
            out.append("%s %s %s" % (hint, subjects[0], scene))
    # The composer can overshoot: "african" + "elderly woman" + "portrait" is four AND-ed terms
    # and returns nothing. Drop them here rather than teaching every caller the token budget.
    return [q for q in out if commons_term_count(q) <= 3]


def commons_term_count(query):
    """AND-ed terms, not words. A quoted phrase is ONE term however many spaces it contains —
    counting words would throw away '"Solo un milagro por persona"' (5 words, 1 term, and the
    single densest seam of usable faces found in the whole corpus)."""
    rest, terms = re.sub(r'"[^"]*"', "", query), len(re.findall(r'"[^"]*"', query))
    return terms + len(rest.split())


def build_queries(cell, max_queries, source="flickr"):
    """Returns (queries, truncated_count)."""
    if source == "openimages":
        # One "query" only, and it is a filter, not a phrasing. The pool is local and already
        # annotated, so there is nothing a second wording could reach that the first cannot —
        # the walk is bounded by --pages x --per-page over a shuffled slice instead.
        gender = ("Predominantly Masculine" if cell["gender"] == "male"
                  else "Predominantly Feminine")
        desc = "gender=%s" % gender
        # MIAP records a coarse AgePresentation too, and the 50+ bands are precisely where the
        # corpus is thin. Asking for the "Older" rows FIRST is free — see openimages_search for
        # why it changes only the order — and it is the difference between the 72 slots in
        # those two bands being reachable and not.
        if cell["age_band"] in ("50-59", "60-70"):
            desc += ";age=Older"
        return [desc], 0
    if source == "commons":
        base = build_commons_queries(cell)
    elif cell["cell_id"] in QUERY_OVERRIDES:
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
def attribution_text(cand, info):
    if not info["attribution"]:
        return None
    return '"%s" by %s (%s), licensed under %s (%s)' % (
        (cand.get("title") or "untitled").strip(), cand.get("author") or "unknown",
        cand.get("page_url") or "", info["name"], info["url"])


def build_persona_doc(handle, cell, cand, lic_id, info, img_meta, vision, raw_verdict, wm_detail,
                      confirm_verdict=""):
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
        "ethnicity_note": ("sourced for cell %s (%s); the vision gate placed it there by how the "
                           "photograph READS, which is what a coverage target can measure and is "
                           "not a claim about the person — confirm by eye before first use"
                           % (cell["cell_id"], cell["ethnicity"])),
        "demo": "US %s%s, %s — candid available-light photograph" % (
            "man" if cell["gender"] == "male" else "woman", age_est,
            (isinstance(vision, dict) and vision.get("apparent_ethnicity")) or cell["ethnicity"]),
        "build_vibe": None,
        "source": {
            "platform": cand.get("platform") or "unknown",
            "page_url": cand.get("page_url") or "",
            "photo_id": str(cand.get("id") or ""),
            "author": cand.get("author") or "unknown",
            "license": info["name"],
            "license_url": info["url"],
            "attribution_required": bool(info["attribution"]),
            "attribution_text": attribution_text(cand, info),
        },
        "image": dict(img_meta),
        "qc": {
            "ai_verdict": raw_verdict,
            # The independent second reading that agreed. Kept verbatim rather than reduced to a
            # boolean: when a face is later disputed, the question is always which estimates the
            # two calls actually gave, and a `confirmed: true` cannot answer it.
            "ai_verdict_confirm": confirm_verdict,
            "watermark": False,
            "face_visible": True,
            "accepted_date": time.strftime("%Y-%m-%d"),
            "notes": ("machine gates passed: licence %s read back from the source, %.2fMP, "
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
    # Reported, never repaired: `plan` is the one subcommand whose whole job is to tell you
    # what is true, so it must not change what is true while you read it. The HAVE column
    # above counts these — the picker cannot see any of them.
    orphans = sorted(h for h in bank if h not in (_load(INDEX, "index").get("personas") or {}))
    if orphans:
        print("\n⚠ %d persona(s) on disk with NO index row — counted in HAVE above, but "
              "invisible to persona_picker.py: %s\n  The next `fetch` repairs them "
              "automatically (as PENDING)." % (len(orphans), ", ".join(orphans)))
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

        # Re-derived through the same spine the fetcher uses, not compared against a frozen list
        # of display names. A jurisdiction port (CC BY 3.0 TW) is minted without anyone telling
        # us, and an enumeration reads a perfectly fine licence as "unknown, refuse".
        lic = ((doc.get("source") or {}).get("license") or "").strip()
        if not licence_name_ok(lic):
            problems.append("licence %r does not pass the licence spine (CC0, or CC BY with no "
                            "SA/NC/ND term)" % lic)

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

        flagged, detail = monochrome_screen(img)
        if flagged:
            problems.append("greyscale: %s" % detail)

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
                    if vision.get("studio_or_press_context") is True:
                        # Recorded, not a problem — see evaluate_vision. Surfaced here because a
                        # verify run is the other place a human is already reading the bank.
                        notes.append("studio/press setting")
                    if args.update_qc:
                        # Off by default: "verify" that mutates the thing it verifies is a trap.
                        # On, it saves re-buying ~16s of model call per face the next time the
                        # rubric gains a key — and it is what puts the new fields where
                        # contact_sheet.py can caption them.
                        doc.setdefault("qc", {})["vision"] = vision
                        doc["qc"]["rubric_refreshed"] = time.strftime("%Y-%m-%d")
                        _atomic_write(os.path.join(PERSONAS, handle, "persona.json"), doc)
                        notes.append("qc rewritten")

        print("%-14s %-4s %s%s" % (handle, "FAIL" if problems else "PASS",
                                   "; ".join(problems) if problems else "clean",
                                   "   [%s]" % " ".join(notes) if notes else ""))
        failures += 1 if problems else 0
    print("\n%d/%d personas would fail the gates today." % (failures, len(bank)))
    if not args.vision:
        print("(gate 5 not run — pass --vision to re-check the bank through gem9)")
    sys.exit(1 if failures else 0)


def cmd_quarantine(args):
    """MOVE a face out of the bank, permanently, with the reason attached.

    Not `approve --reject`: that leaves the persona in place as `retired`, which is right for a
    face whose photograph is fine but whose LICENCE or rights we decided against — it stays where
    anyone can see what was retired and why. This is for a face that failed a machine gate, and
    the difference that matters is re-admission. A retired persona still occupies its handle and
    is still seen by the dHash check; a face that merely had its directory deleted would be found
    again by the next walk over the same corpus, judged again, and written straight back in.

    So the directory MOVES rather than being deleted (nothing here is recoverable from the
    source: the Flickr rendition can disappear, and `gone` is already a verdict this cache
    records), and quarantine_index() reads it back as a dHash and a photo_id the fetch path
    refuses. Rejecting a face has to be a fact the bank remembers.

    --about carves out the cases where that refusal would be WRONG. "The head is in profile" is a
    fact about the photograph and holds in every cell. "She reads 52, not 45" is a fact about the
    PAIRING: the face is not bad, she is in the wrong drawer, and refusing her by hash would stop
    the neighbouring band's walk from ever finding her — the free recovery the whole two-reading
    scheme is built on. "We credited the wrong photographer" is a fact about the METADATA, i.e.
    about us; the pixels were never in question, and once the bug is fixed a fresh walk records
    the right answer. Both of those still MOVE the face out of this cell, and both leave the
    corpus free to re-admit it correctly.
    """
    bank, index = load_bank(), _load(INDEX, "index")
    dest_root = os.path.join(PERSONAS, "_quarantine-%s" % args.reason)
    for handle in args.handles:
        if handle not in bank:
            sys.exit("✗ unknown persona %r — nothing moved" % handle)
        if os.path.exists(os.path.join(dest_root, handle)):
            sys.exit("✗ %s is already in %s — nothing moved"
                     % (handle, os.path.basename(dest_root)))
    os.makedirs(dest_root, exist_ok=True)
    moved = []
    for handle in args.handles:
        doc = bank[handle]["doc"]
        doc["status"] = "quarantined"
        doc["approved_by"] = None
        doc["flag_reason"] = args.note or args.reason
        doc["quarantined_date"] = time.strftime("%Y-%m-%d")
        doc["rejection_is_about"] = args.about
        _atomic_write(os.path.join(PERSONAS, handle, "persona.json"), doc)
        # Written BEFORE the move, so a crash between the two leaves a persona that still says
        # why it was condemned rather than one that silently reads as an ordinary pending face.
        shutil.move(os.path.join(PERSONAS, handle), os.path.join(dest_root, handle))
        index.get("personas", {}).pop(handle, None)
        moved.append(handle)
    _atomic_write(INDEX, index)
    print("✓ quarantined %d face(s) into %s/: %s"
          % (len(moved), os.path.basename(dest_root), ", ".join(moved)))
    if args.about in QUARANTINE_LOCAL:
        print("  Recorded as a fact about the %s, not the photograph: they are out of this cell, "
              "but the corpus may still re-admit them correctly." % args.about.upper())
    else:
        print("  Their dHash and photo_id are now refused by `fetch`, so the corpus cannot "
              "re-admit them. Nothing was deleted.")


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

    bank = load_bank()
    # Before anything is counted. A face stranded on disk by an earlier interrupted run is
    # counted by cell_counts() and invisible to the picker, so an unrepaired bank makes this
    # run fetch too few AND leaves the shortfall in place.
    repaired = reconcile_orphans(bank)
    if repaired:
        print("↺ repaired %d persona(s) left on disk without an index row by an interrupted "
              "run — added as PENDING: %s" % (len(repaired), ", ".join(repaired)))
    index = _load(INDEX, "index")
    per_cell, _ = cell_counts(bank)
    have = per_cell.get(cell["cell_id"], 0)
    needed = max(0, cell["target_count"] - have)
    if getattr(args, "depth", None) is not None:
        # A DEPTH, not a quantity: bring this cell up to N, and do nothing if it is already
        # there. --limit cannot express that, because it caps what THIS RUN adds, so a breadth
        # pass re-run after an interruption would hand a second face to every cell it had
        # already reached before any of the untouched cells got their first — the exact
        # inversion of what a breadth pass is for. Depth is a statement about the bank, so it
        # is idempotent, and an interrupted pass can simply be run again.
        needed = max(0, min(cell["target_count"], args.depth) - have)
    if args.limit is not None:
        # --limit is a CAP, always. It used to fall through to `args.limit` when the cell was
        # already full, which turned a safety brake into a request for N more faces than the
        # taxonomy asks for — and skewed the picker's pool rotation toward that one cell.
        needed = min(needed, args.limit)
    if needed <= 0:
        # Say which limit stopped it. "full (1/3)" while --depth 1 is in force reads as a cell
        # that has met the taxonomy's target, and a breadth pass logging that fifty times would
        # look exactly like a finished harvest.
        if have < cell["target_count"]:
            print("✓ cell %s is at depth %d (%d/%d toward target) — nothing to fetch this pass"
                  % (cell["cell_id"], args.depth, have, cell["target_count"]))
        else:
            print("✓ cell %s is full (%d/%d) — nothing to fetch"
                  % (cell["cell_id"], have, cell["target_count"]))
        return

    source = getattr(args, "source", "commons")
    search = SEARCH_BACKENDS[source]
    # Only Flickr needs a key, and api_key() exits when it is missing. Calling it for Commons
    # would make a keyless backend refuse to run for want of a key it never uses.
    key = api_key() if source == "flickr" else None
    session = requests.Session()
    # Wikimedia's UA policy wants a tool name, a version and a way to reach the operator; a
    # contact URI satisfies it without putting a personal address in an outbound header.
    session.headers["User-Agent"] = ("genseo-persona-sourcer/1.1 "
                                     "(https://wellnessnest.co) python-requests")

    queries, dropped = build_queries(cell, args.queries, source=source)
    # Commons licence categories are walked one at a time. `incategory:"A" OR incategory:"B"`
    # over two multi-million-file categories returns 974 results — the parser does not read it
    # the way a person does, and the failure is silent.
    lic_scopes = list(COMMONS_LICENCE_CATEGORIES) if source == "commons" else [None]
    # Quarantined faces are folded in here and NOT into cmd_verify's: this is the one place that
    # decides what may enter the bank, and it is the only place a graveyard belongs.
    hashes = bank_hashes(bank)
    q_hashes, q_photo_ids = quarantine_index()
    hashes.update(q_hashes)
    known_photo_ids = set(q_photo_ids)
    for rec in bank.values():
        pid = (rec["doc"].get("source") or {}).get("photo_id")
        if pid:
            known_photo_ids.add(str(pid))
    # Two photographs of one person by one photographer are not two faces, and dHash cannot see
    # it: a second frame from the same session — different pose, different crop — is nowhere
    # near identical as pixels. The first Open Images run put two accepts from a single
    # photographer into one cell for exactly that reason. The author is already in hand from
    # the index row, so this is the cheapest gate in the file: it spends a dict lookup and
    # saves a download plus a vision call.
    author_cell, author_bank = author_counts(bank, cell["cell_id"])
    author_skips = 0
    taken = taken_handles(bank, index)

    print("cell %s — %s %s %s | have %d, target %d, fetching up to %d"
          % (cell["cell_id"], cell["gender"], cell["age_band"], cell["ethnicity"],
             have, cell["target_count"], needed))
    if source == "flickr":
        print("source: flickr | licence filter: %s (%s)"
              % (LICENSE_SEARCH_PARAM, ", ".join(ALLOWED_LICENSES[i]["name"]
                                                 for i in LICENSE_SEARCH_PARAM.split(","))))
    elif source == "openimages":
        cached_n = verdict_cache_load()
        print("source: openimages | %d indexed candidates, all CC BY 2.0, byte floor %dKB | "
              "pixels from staticflickr.com, metadata from storage.googleapis.com, "
              "flickr.com never requested"
              % (len(openimages_pool()), OPENIMAGES_MIN_BYTES // 1000))
        print("verdict cache: %d image(s) already judged — replayed free, "
              "re-scored against this cell" % cached_n)
    else:
        print("source: commons | licence categories walked separately: %s"
              % ", ".join(lic_scopes))
    print("queries (%d%s), up to %d page(s) x %d results each:"
          % (len(queries), ", %d MORE AVAILABLE but capped by --queries" % dropped if dropped else "",
             args.pages, args.per_page))
    for q in queries:
        print("   %s" % q)
    if args.dry_run:
        print("DRY RUN: gates run for real, no persona is written to disk."
              + (" (The verdict cache IS still appended — a dry run is how we calibrate, and"
                 " throwing away the model calls it paid for would make calibration the most"
                 " expensive thing we do.)" if source == "openimages" else ""))
    print("")

    accepted, examined, seen_ids = [], 0, set()
    stop_reason = "queries exhausted"
    vision_infra_fails = 0
    set_download_concurrency(args.download_concurrency)
    set_vision_concurrency(args.vision_concurrency)
    # Licence scope is the OUTER loop, so each category is walked across every phrasing before
    # the next one starts. The order is COMMONS_LICENCE_CATEGORIES', which is deliberately not
    # the attribution-cheapest first — see the measurement recorded there.
    jobs = [(scope, q) for scope in lic_scopes for q in queries]
    # Built here rather than as a `with` around the loops purely so the loop body keeps its
    # indentation and stays diffable; shutdown() in the finally does what __exit__ would.
    pool = ThreadPoolExecutor(max_workers=max(1, args.workers))
    try:
        for scope, query in jobs:
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
                    photos, total_pages = search(session, key, query, page, args.per_page, scope)
                except (FlickrError, CommonsError) as exc:
                    print("  ✗ search failed (%s | page %d): %s" % (query, page, exc))
                    break
                if not photos:
                    break
                # One page = one batch, submitted together and consumed IN SUBMISSION ORDER.
                # Order matters for more than tidy output: vision_infra_fails counts
                # CONSECUTIVE failures, and "consecutive" only means anything against a fixed
                # sequence. as_completed() would make the abort threshold depend on which
                # worker happened to finish first.
                budget = args.max_candidates - examined
                batch = []
                for photo in photos:
                    if len(batch) >= budget:
                        break
                    pid = str(photo.get("id"))
                    if pid in seen_ids:
                        continue
                    seen_ids.add(pid)
                    if pid in known_photo_ids:
                        print("  · %-12s already in the bank" % pid)
                        continue
                    who = author_key_of(photo.get("author"))
                    if who and (author_cell.get(who, 0) >= AUTHOR_CAP_CELL
                                or author_bank.get(who, 0) >= AUTHOR_CAP_BANK):
                        # Counted rather than printed: at this depth of walk the line would
                        # repeat thousands of times. The total is reported at the end, because
                        # a cap nobody can see is a cap that looks like an empty corpus.
                        author_skips += 1
                        continue
                    batch.append((pid, photo))
                # The candidate travels WITH its future. It used to be looked up as `photo`,
                # the leftover loop variable from building the batch — which holds the LAST
                # photo of the page, so every accept on a page was written with that one's
                # author and landing URL. Seven distinct photographs went into the bank
                # credited to a single Flickr work. The pixels, hashes and vision verdict were
                # all correct, because those come back inside the future; only the fields read
                # from the enclosing scope were wrong, which is why it survived the accept
                # line's own output looking right.
                futures = [(pid, photo, pool.submit(process_candidate, photo, cell, key,
                                                    session, hashes, args))
                           for pid, photo in batch]
                tail_cancelled = False
                for i, (pid, cand, fut) in enumerate(futures):
                    if len(accepted) >= needed:
                        if not tail_cancelled:
                            tail_cancelled = True
                            # Cancel the WHOLE remaining tail in ONE pass, before waiting on
                            # anything. Cancelling one future at a time and blocking on each
                            # already-running one in between is a treadmill: while we wait for
                            # future N the pool dequeues N+1..N+workers and starts them, so the
                            # next future we reach is running too, cannot be cancelled, and we
                            # block on that one while the pool starts more. The walk never
                            # overtakes the workers, and a full --per-page batch runs to
                            # completion after the target was already met.
                            #
                            # Measured 2026-08-10, --per-page 500 --workers 12: a run that had
                            # everything it was asked for at 2.6s went on judging the rest of
                            # the page for 946 seconds — 84s of CPU inside 946s of wall-clock,
                            # i.e. almost pure waiting on gem9 calls whose verdicts were thrown
                            # away on arrival. pool.shutdown(cancel_futures=True) in the finally
                            # could not save it either, because the finally is downstream of
                            # this loop and the loop is what never ends.
                            for _, _, tail in futures[i:]:
                                tail.cancel()
                        # A future that had already started cannot be cancelled, so up to
                        # --workers extra candidates still get judged — they simply do not
                        # count as examined, because they were not.
                        if fut.cancelled():
                            continue
                        # And if it had already started, we still decline to ACT on it. Letting
                        # a late accept through put 10 faces in a cell that asks for 9 on the
                        # first Open Images run — the same overshoot the --limit cap exists to
                        # prevent, and for the same reason: the picker balances pool rotation
                        # against target_count, so an over-filled cell skews every draw after it.
                        try:
                            fut.result()
                        except Exception as exc:          # noqa: BLE001 - see below
                            # Raising here would kill a run that has already collected
                            # everything it was asked for, over a candidate whose verdict we
                            # had just decided to discard. Say it out loud and finish.
                            print("  · %-12s judged after the target was met; discarded (%s)"
                                  % (pid, exc))
                        continue
                    verdict = fut.result()
                    examined += 1
                    # An infra failure is NOT evidence the photo is bad. Left uncounted, a
                    # 9router outage renders as 400 content rejections and reads as "Flickr
                    # has nothing for this cell" — the operator rewrites good queries and
                    # burns the whole --max-candidates budget on doomed calls.
                    if verdict[0] == "vision-infra":
                        vision_infra_fails += 1
                        print("  ! %-12s [vision-infra] %s  (%d in a row)"
                              % (pid, verdict[1], vision_infra_fails))
                        if vision_infra_fails >= VISION_INFRA_ABORT:
                            # Cancel before unwinding, or exiting the pool's `with` blocks
                            # until every queued candidate has burned a doomed gem9 call.
                            for _, _, pending in futures:
                                pending.cancel()
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
                    # The authoritative dupe check. The worker compared against the bank as it
                    # stood when IT ran; siblings in the same batch have landed since, and two
                    # near-identical photographs would otherwise both pass — each invisible to
                    # the other. Serial, against the live dict, after every earlier accept.
                    h64 = int(doc_parts["img_meta"]["dhash"], 16)
                    clash = next(((hnd, hamming(h64, other)) for hnd, other in hashes.items()
                                  if hamming(h64, other) <= DHASH_MAX_DISTANCE), None)
                    if clash:
                        print("  ✗ %-12s [dupe] dHash distance %d vs %s (serial re-check: it "
                              "landed while this candidate was in flight)" % (pid, clash[1], clash[0]))
                        continue
                    # Same reason the dHash check above is repeated serially: the batch was
                    # filtered against the tallies as they stood when the PAGE was built, and a
                    # sibling by the same photographer may have been accepted since — each one
                    # invisible to the other while both were in flight.
                    who = author_key_of(cand.get("author"))
                    if who and (author_cell.get(who, 0) >= AUTHOR_CAP_CELL
                                or author_bank.get(who, 0) >= AUTHOR_CAP_BANK):
                        print("  ✗ %-12s [author] %s reached the cap while this candidate was "
                              "in flight" % (pid, cand.get("author")))
                        author_skips += 1
                        continue
                    handle = next_handle(cell["cell_id"], taken)
                    taken.add(handle)
                    doc = build_persona_doc(handle, cell, cand, doc_parts["lic_id"],
                                            doc_parts["info"], doc_parts["img_meta"],
                                            doc_parts["vision"], doc_parts["raw"], doc_parts["wm"],
                                            doc_parts.get("confirm_raw", ""))
                    # The bug above was invisible for a whole run because nothing ever checked
                    # that the credit written to disk belonged to the photograph downloaded.
                    # CC BY attribution has to point at the actual work, so this is a licence
                    # condition, not a tidiness one — assert it before the file is written.
                    if str(doc["source"]["photo_id"]) != str(pid):
                        sys.exit("✗ attribution mismatch: %s would be credited to photo %s but "
                                 "the image downloaded was %s. Refusing to write."
                                 % (handle, doc["source"]["photo_id"], pid))
                    ref = None if args.dry_run else write_persona(handle, doc, jpeg)
                    print("  ✓ %-12s [%s] → %s  %dx%d %.2fMP %s by %s"
                          % (pid, "would accept" if args.dry_run else "accept", handle,
                             img.size[0], img.size[1], img.size[0] * img.size[1] / 1e6,
                             doc_parts["info"]["name"], cand.get("author") or "unknown"))
                    accepted.append((handle, cell["pool_id"], ref))
                    hashes[handle] = int(doc_parts["img_meta"]["dhash"], 16)
                    if who:
                        author_cell[who] = author_cell.get(who, 0) + 1
                        author_bank[who] = author_bank.get(who, 0) + 1
                if total_pages and page >= total_pages:
                    break
                time.sleep(args.sleep)
    except _AbortRun:
        pass
    finally:
        # cancel_futures drops whatever is still queued. Without it an abort — the one case
        # where we already know the next call will fail too — waits out every candidate the
        # last page submitted.
        pool.shutdown(wait=True, cancel_futures=True)
        # write_persona() already committed each accept to disk. If we die here without
        # writing the index, those dirs are invisible to the picker forever while
        # cell_counts() still counts them as filled — capacity vanishes silently.
        if not args.dry_run:
            commit_accepted(accepted)

    print("\nexamined %d candidate(s), accepted %d of %d wanted — stopped: %s"
          % (examined, len(accepted), needed, stop_reason))
    if author_skips:
        print("NOTE: %d candidate(s) skipped by the photographer cap (%d per cell, %d per "
              "bank). They were never judged, so they are not in `examined` — a deep walk "
              "that ends short may simply have run out of NEW photographers."
              % (author_skips, AUTHOR_CAP_CELL, AUTHOR_CAP_BANK))
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


def reconcile_orphans(bank):
    """Give every persona DIRECTORY without an index row the PENDING row it should have had.

    The two halves of a persona are written at different times: write_persona() commits the
    directory the moment a candidate is accepted, and commit_accepted() writes the index rows
    once, from a finally, at the end of the run. Anything that stops the interpreter between
    those two points — SIGKILL, a power cut, `kill` before the handler above existed — leaves
    a face that load_bank() counts toward the cell target and persona_picker.py can never see,
    because the picker reads index.json and nothing else. Capacity disappears silently, which
    is the worst way for it to disappear: `plan` reports the cell as filling up.

    Repairing rather than deleting is the right call. The directory only exists because the
    candidate passed every machine gate, including the attribution assertion that runs before
    the file is written, and persona.json holds the licence record CC BY 2.0 requires. The one
    thing the row must NOT do is arrive active — the same rule commit_accepted() states, for
    the same reason: an "active" row IS the approval, and this repair path has judged nothing.

    Returns the handles repaired."""
    index = _load(INDEX, "index")
    people = index.setdefault("personas", {})
    orphans = sorted(h for h in bank if h not in people)
    if not orphans:
        return []
    for handle in orphans:
        doc = bank[handle]["doc"]
        people[handle] = {"handle": handle, "pool_id": doc.get("pool_id"),
                          "status": "pending", "ref": bank[handle]["ref"],
                          "used_count": 0, "last_used_seq": 0,
                          "gaze_used": [], "last_gaze": None, "angles_used": []}
    _atomic_write(INDEX, index)
    return orphans


def process_candidate(cand, cell, key, session, hashes, args):
    """Runs the gates cheapest-first. Returns a tuple whose first element is the gate that
    rejected it, or ("accept", "", parts, jpeg_bytes, image).

    P, P2 and C run FIRST, ahead of the licence gate, because all three are free string tests on
    metadata already in hand — and because all three answer a question a licence cannot. A file
    can be flawlessly CC BY and still be a portrait the source itself marks as carrying
    personality rights, a photograph whose caption names the person in it, or a re-host of a
    photograph whose origin forbids exactly this use.

    Runs on a worker thread. It reads `hashes` but never writes it: the authoritative dupe
    check is the serial one in cmd_fetch, because by the time this returns the bank may have
    grown by whatever the other workers accepted."""
    session = worker_session(session)
    ok, reason = gate_personality(cand)
    if not ok:
        return ("personality", reason)

    ok, reason = gate_named_subject(cand)
    if not ok:
        return ("named-subject", reason)

    ok, reason = gate_origin(cand)
    if not ok:
        return ("origin", reason)

    ok, reason = gate_artwork(cand)
    if not ok:
        return ("artwork", reason)

    lic_id, info, reason = gate_license(cand)
    if not info:
        return ("licence", reason)

    # A previous cell already paid for this face. A remembered REJECTION that had nothing to do
    # with the cell (not a photograph, two people, watermark, too small) is final and costs
    # nothing to repeat. A remembered vision answer is re-scored against THIS cell, because
    # "wrong gender for f3039-wh" is a fact about the pairing and not about the photograph.
    cached = verdict_cached(cand)
    if cached:
        if cached.get("reject"):
            return (cached["reject"][0], "%s [cached]" % cached["reject"][1])
        # EVERY reading we hold, not just the first: a candidate the confirming call disqualified
        # must fail here too, before the download, or the second opinion we paid for only ever
        # applies to the cell that happened to buy it.
        for v in vision_readings(cached):
            reasons = evaluate_vision(v, cell)
            if reasons:
                return ("vision", "%s [cached]" % "; ".join(reasons))

    try:
        size = largest_size(cand, key, session, allow_getsizes=not args.no_getsizes,
                            sleep=args.sleep)
    except FlickrError as exc:
        return ("api", "getSizes failed: %s" % exc)
    if not size:
        return ("resolution", "no downloadable size reported")
    _, w, h, url, label = size
    # `w and h` because a backend is allowed to say it does not know. Skipping the pre-check
    # then costs one download that the post-download check may still refuse; asserting a
    # geometry nobody measured would cost us good photographs on the strength of a guess.
    if w and h and not meets_resolution(w, h):
        return ("resolution", "%dx%d = %.2fMP short=%d (floor %.1fMP / %dpx) [%s]"
                % (w, h, w * h / 1e6, min(w, h), MIN_MEGAPIXELS, MIN_SHORT_EDGE, label))

    # upload.wikimedia.org rate-limits SEPARATELY from the API, and it 429s far sooner. Without
    # this retry a throttled run reports 30 straight "[download] 429" lines, which read as
    # thirty bad photographs — the same misreading VISION_INFRA_ABORT exists to prevent one
    # gate further down. A 429 is the host asking us to slow down; it says nothing about the file.
    # A rung that 404s means THAT RENDITION was never generated; the photograph may be perfectly
    # alive one rung down. Only the last rung is allowed to conclude "gone" from a 404 — reading
    # a missing size as a missing photograph would throw away good faces and, worse, cache the
    # mistake permanently.
    ladder = (flickr_size_ladder(cand["download_url"])
              if cand.get("platform") == "openimages" else [(url, label)])
    try:
        resp = None
        for rung, (rung_url, rung_label) in enumerate(ladder):
            for attempt in range(4):
                # The gate is around the request only. Holding a slot through the back-off would
                # let one throttled worker idle the asset host for everybody else.
                with _DOWNLOAD_GATE:
                    resp = session.get(rung_url, timeout=90)
                if resp.status_code == 429:
                    if attempt == 3:
                        return ("throttled", "HTTP 429 from the download host after 4 attempts — "
                                             "slow the run down; this is not a verdict on the photo")
                    time.sleep(5 * (attempt + 1))
                    continue
                break
            if resp.status_code == 404 and rung < len(ladder) - 1:
                continue
            if resp.status_code in (403, 404, 410):
                # Measured on a 30-file sample of Open Images originals: 3 were gone (two 404,
                # one 410). Flickr users delete and re-permission photographs, and a decade-old
                # index cannot know. Worth remembering, because it is permanent — unlike the
                # 429 above, which is the opposite of permanent.
                msg = "HTTP %d — the photograph is no longer served (tried %s)" % (
                    resp.status_code, ", ".join(l for _, l in ladder[:rung + 1]))
                verdict_remember(cand, reject=["gone", msg])
                return ("gone", msg)
            resp.raise_for_status()
            label = rung_label
            break
        jpeg, img = as_jpeg(resp.content)
    except (requests.RequestException, OSError, ValueError) as exc:
        return ("download", "%s" % exc)
    # Both floors, not just the megapixel one. A 3000x400 panorama is 1.2MP and would have
    # passed a bare MP check while carrying a 400px short edge — a third of what an ima2
    # reference needs. For a backend that advertises no geometry at all this is the ONLY
    # resolution gate there is, so it has to be the whole floor rather than half of it.
    if not meets_resolution(*img.size):
        msg = ("delivered file is %dx%d = %.2fMP short=%d (floor %.1fMP / %dpx)"
               % (img.size[0], img.size[1], img.size[0] * img.size[1] / 1e6, min(img.size),
                  MIN_MEGAPIXELS, MIN_SHORT_EDGE))
        verdict_remember(cand, reject=["resolution", msg])
        return ("resolution", msg)

    # Before the watermark screen because it is far cheaper, and cached because "this file has
    # no colour in it" is a permanent fact about the photograph rather than about this cell.
    # Sited here rather than up with the vision rubric on purpose: a candidate whose vision
    # reading is already cached skips the model call entirely, so a greyscale check that lived
    # only in the rubric would never run on the ~470 faces already banked.
    flagged, mono_detail = monochrome_screen(img)
    if flagged:
        msg = "greyscale — no colour to anchor skin tone or lighting on (%s)" % mono_detail
        verdict_remember(cand, reject=["monochrome", msg])
        return ("monochrome", msg)

    flagged, wm_detail = watermark_screen(img)
    if flagged:
        msg = "burned-in text screen: %s" % wm_detail
        verdict_remember(cand, reject=["watermark", msg])
        return ("watermark", msg)

    # list() rather than .items() directly: the serial accept path adds to this dict while
    # workers are running, and iterating a dict that another thread grows raises
    # RuntimeError("dictionary changed size during iteration") — which would surface as a
    # crashed worker, i.e. as a rejected photograph. list() is atomic under the GIL.
    # This snapshot is an EARLY-OUT, sited here to save a vision call on an obvious repeat;
    # cmd_fetch re-checks against the live bank before it accepts anything.
    h64 = dhash(img)
    for handle, other in list(hashes.items()):
        d = hamming(h64, other)
        if d <= DHASH_MAX_DISTANCE:
            return ("dupe", "dHash distance %d vs %s" % (d, handle))

    # CONFIRMATION. One reading cannot place a face in a ten-year band. Re-screening the bank on
    # 2026-08-10 took a SECOND reading of forty faces the first reading had already accepted, and
    # five of them changed band or ethnicity — every one a face whose estimate already sat on a
    # boundary (45-55 became 45-60; 24-32 became 20-30). Neither call is wrong: the model's
    # interval is simply wider than the band we sort into, so which side of the line a boundary
    # face falls on is decided by which call you happened to make. Sorting on one sample of a
    # quantity noisier than the bucket is how you get a bank that only looks stratified.
    #
    # So a face is written only when TWO independent readings both place it in this cell. The
    # second call is bought only for a candidate the first one accepted, and accepts are rare
    # (one per thirty to four hundred examined), so it costs a few percent of the run — and
    # nothing at all on replay, because both readings land in the cache and serve every later
    # cell. Total cost stays bounded at two calls per image for the life of the bank.
    #
    # A rejected boundary face is not lost either, which is what makes this affordable for the
    # thin cells. The cache stores READINGS, not verdicts, so when the neighbouring band's turn
    # comes, its walk replays these same two readings for free and accepts her there — which is
    # where a woman who reads 45-60 belonged in the first place.
    held = current_readings(cached)
    readings, raws = [v for v, _ in held], [r for _, r in held]

    while True:
        for v in readings:
            reasons = evaluate_vision(v, cell)
            if reasons:
                return ("vision", "; ".join(reasons))
        if len(readings) >= VISION_CONFIRMATIONS:
            break
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        try:
            tmp.write(jpeg)
            tmp.close()
            try:
                v, raw = vision_check(tmp.name)
            except (OSError, subprocess.SubprocessError, VisionInfraError) as exc:
                return ("vision-infra", "gem9 unavailable (%s) — refusing to accept unseen" % exc)
        finally:
            os.unlink(tmp.name)
        readings.append(v)
        raws.append(raw)
        # Banked BEFORE the verdict is read, and stored as the model's answers rather than as
        # pass/fail. "Wrong gender for f3039-wh" is a fact about the pairing; "two people in
        # frame" is a fact about the photograph. Only the second kind may be replayed, so the
        # cache keeps the raw readings and lets each cell draw its own conclusion.
        fields = {}
        for i, r in enumerate(readings):
            fields[VISION_KEYS[i]], fields[RAW_KEYS[i]] = r, raws[i]
        verdict_remember(cand, **fields)

    vision, raw = readings[0], (raws[0] if raws else "")
    confirm_raw = raws[1] if len(raws) > 1 else ""

    parts = {
        "lic_id": lic_id, "info": info, "vision": vision, "raw": raw, "wm": wm_detail,
        "confirm_raw": confirm_raw,
        "img_meta": {
            "width": img.size[0], "height": img.size[1],
            "megapixels": round(img.size[0] * img.size[1] / 1e6, 2),
            "sha256": hashlib.sha256(jpeg).hexdigest(),
            "bytes": len(jpeg),
            "dhash": dhash_hex(h64),
            # Which rendition these pixels came from. The bank contains both `flickr-original`
            # faces (fetched before 2026-08-10) and `flickr-2048` ones, and a file that does not
            # say which is a file nobody can reproduce.
            "rendition": label,
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

    print("licence spine (platform-neutral slugs)")
    for good in ("cc0-1.0", "cc0", "cc-by-4.0", "cc-by-2.0", "cc-by-3.0", "cc-by-3.0-tw",
                 "cc-by-2.5-in"):
        i, why = licence_ok(good)
        check("%s accepted" % good, i is not None, why)
    check("a jurisdiction port we have never seen still resolves a deed URL",
          licence_ok("cc-by-3.0-tw")[0]["url"].endswith("/by/3.0/tw/"))
    for bad in ("cc-by-sa-4.0", "cc-by-nc-2.0", "cc-by-nd-3.0", "cc-by-nc-sa-2.0",
                "public domain", "pd-old", "gfdl", "no known copyright restrictions",
                "attribution", "united states government work", "fal", ""):
        i, why = licence_ok(bad)
        check("%r refused" % bad, i is None and bool(why))
    check("CC0 needs no attribution; CC BY does",
          licence_ok("cc0-1.0")[0]["attribution"] is False
          and licence_ok("cc-by-4.0")[0]["attribution"] is True)
    check("display name round-trips back through the gate (what verify re-reads)",
          all(licence_name_ok(licence_ok(s)[0]["name"])
              for s in ("cc0-1.0", "cc-by-4.0", "cc-by-2.0", "cc-by-3.0-tw")))
    check("verify refuses a share-alike display name", not licence_name_ok("CC BY-SA 4.0"))
    check("a Commons slug reaches the gate without a Flickr id",
          gate_license({"licence_slug": "cc-by-4.0"})[1] is not None)
    check("a Flickr id still maps through FLICKR_ID_TO_SLUG",
          gate_license({"license": "11"})[1]["name"] == "CC BY 4.0")

    print("gate P — personality / publicity rights")
    check("no flag = no refusal (silence is not clearance, but it is not evidence either)",
          gate_personality({"restrictions": ""})[0])
    for flag in ("personality", "trademarked|personality", "insignia", "currency"):
        ok_, why = gate_personality({"restrictions": flag})
        check("restrictions=%r refused" % flag, not ok_ and "publicity" in why or not ok_)
    check("an UNRECOGNISED warning is also refused, not waved through",
          not gate_personality({"restrictions": "some-new-template-nobody-added-here"})[0])

    print("gate P2 — a caption that names the subject")
    # The three that mattered: each passed the vision gate AND a human look at the frame on
    # 2026-08-10, and the caption is the only place any of them was ever visible.
    for title, who in (("Sam Rockwell en la presentación de Moon", "Sam Rockwell"),
                       ("Stéphane Diagana se prète au jeu de l'interview", "Stéphane Diagana"),
                       ("Anita Ravna juni 2013", "Anita Ravna")):
        ok_, why = gate_named_subject({"title": title})
        check("%r refused before download" % who, not ok_ and who in why)
    # A trailing number, an all-caps prefix and bracketed junk must not hide the name.
    for title, who in (("Ana Moser (6)", "Ana Moser"),
                       ("Lena Ek - Riksdagsgruppen 2014", "Lena Ek"),
                       ("MRI 2013 SCA Alisabeth Merlo", "Alisabeth Merlo")):
        check("%r found in %r" % (who, title[:32]),
              named_subject(title) == who)
    # The camera defaults this corpus is mostly made of, which is the yield the gate must not eat.
    for title in ("DSC07576", "IMG_2914", "Untitled", "AppWorks", "Cynic", "P1010342"):
        check("%r survives gate P2" % title, gate_named_subject({"title": title})[0])
    check("a lone given name is not findable and is allowed through",
          gate_named_subject({"title": "Megan"})[0] and gate_named_subject({"title": "Sanne"})[0])
    check("an all-caps initialism is an organisation, not a person",
          named_subject("MRI SCA NPS") is None)
    # Documented cost, asserted so it stays visible rather than being rediscovered as a bug:
    # these are villages and t-shirt slogans, and they are refused anyway. See the gate comment
    # for why that trade is the right way round.
    for fp in ("Breakfast in Kirkby Malzeard", "Wylin cuz I'm Young tee"):
        check("known false positive %r is still refused, knowingly" % fp[:26],
              not gate_named_subject({"title": fp})[0])

    print("gate A — artwork / archive reproduction")
    for art in ("Portrait of a Woman MET DP161260", "Marble head of an elderly woman",
                "Terracotta statue of a young woman", "Study of a Young Woman",
                "Woman with a Lute MET DP354965", "1890 cabinet card of a lady"):
        ok_, why = gate_artwork({"title": art})
        check("%r refused before download" % art[:34], not ok_, why[:0])
    for real in ("Woman cooking in her kitchen", "Farmers market, Portland 2019",
                 "My mother in the garden"):
        check("%r survives gate A" % real[:30], gate_artwork({"title": real})[0])
    check("gate A also reads the Commons file description, not only the title",
          not gate_artwork({"title": "Untitled", "raw": {"description": "Oil painting, c.1650"}})[0])

    print("gate C — re-host origin")
    check("a plain Commons credit passes", gate_origin({"credit_blob": "Own work"})[0])
    for host in ("unsplash.com", "pexels.com", "nappy.co"):
        ok_, why = gate_origin({"credit_blob": '<a href="https://%s/photos/x">via</a>' % host})
        check("re-host from %s refused" % host, not ok_ and host in why)
    check("the origin is caught in ANY of credit/author/page_url",
          not gate_origin({"author": "uploaded from pexels.com"})[0])

    print("Commons query grammar")
    cq = build_commons_queries(cells_by_id(_load(TAXONOMY, "taxonomy"))["f6070-bl"])
    check("every Commons query is <= 3 AND-ed terms (4 tokens returns 0 on this corpus)",
          all(commons_term_count(q) <= 3 for q in cq),
          "longest: %r" % max(cq, key=commons_term_count))
    check("a quoted phrase counts as ONE term, not five",
          commons_term_count('"Solo un milagro por persona"') == 1
          and commons_term_count('"Wiki Loves Africa" woman portrait') == 3)
    check("the project query survives the term filter and leads the cell",
          cq[0] == '"Wiki Loves Africa"')
    check("a project phrase is never diluted with a scene or subject word",
          all(commons_term_count(q) == 1 for q in cq if q.startswith('"')))
    check("a cell with no named project still starts on its broadest phrasing",
          build_commons_queries(cells_by_id(_load(TAXONOMY, "taxonomy"))["f3039-wh"])[0]
          == "woman")
    check("commons queries never leak into the Flickr composer",
          build_queries(cells_by_id(_load(TAXONOMY, "taxonomy"))["f6070-bl"], 4)[0]
          != build_queries(cells_by_id(_load(TAXONOMY, "taxonomy"))["f6070-bl"], 4,
                           source="commons")[0])

    print("Commons candidate normalisation")
    cand = commons_candidate({
        "pageid": 42, "title": "File:Some woman.jpg",
        "imageinfo": [{"mime": "image/jpeg", "width": 2000, "height": 1500,
                       "url": "https://upload.wikimedia.org/x.jpg?utm_source=api",
                       "extmetadata": {"License": {"value": "cc-by-4.0"},
                                       "Artist": {"value": "<a href='/wiki/User:X'>X</a>"},
                                       "Credit": {"value": "Own work"},
                                       "Restrictions": {"value": ""}}}]})
    check("mime-gated, geometry carried, utm tail stripped",
          cand and cand["sizes"][0][3].endswith("/x.jpg") and cand["sizes"][0][0] == 3000000)
    check("author HTML flattened for display", cand["author"] == "X")
    check("credit_blob keeps the raw href gate C matches on",
          "href" in cand["credit_blob"])
    check("a PDF in namespace 6 is dropped, not scored",
          commons_candidate({"pageid": 1, "title": "File:Book.pdf",
                             "imageinfo": [{"mime": "application/pdf"}]}) is None)
    check("largest_size does not take the Flickr branch for a Commons candidate",
          largest_size(cand, None, None)[3].endswith("/x.jpg"))
    check("no thumburl falls back to the original rather than dropping the candidate",
          cand["sizes"][0][4] == "commons-original")
    thumbed = commons_candidate({
        "pageid": 43, "title": "File:Some man.jpg",
        "imageinfo": [{"mime": "image/jpeg", "width": 6000, "height": 4000,
                       "url": "https://upload.wikimedia.org/orig.jpg",
                       "thumburl": "https://upload.wikimedia.org/thumb/2560px-orig.jpg?utm_source=api",
                       "thumbwidth": 2560, "thumbheight": 1707,
                       "extmetadata": {"License": {"value": "cc-by-4.0"}}}]})
    # The whole point of the fix: the ORIGINAL must not survive anywhere in sizes, or
    # largest_size picks it (24MP beats 4.4MP) and the throttle comes straight back.
    check("thumbnail wins over the original, and the original is not left as an alternative",
          len(thumbed["sizes"]) == 1
          and thumbed["sizes"][0][3] == "https://upload.wikimedia.org/thumb/2560px-orig.jpg"
          and thumbed["sizes"][0][1:3] == (2560, 1707)
          and thumbed["sizes"][0][4] == "commons-thumb-2560")
    check("a 2560px thumbnail of a 16:9 frame still clears the short-edge floor",
          meets_resolution(COMMONS_THUMB_WIDTH, int(COMMONS_THUMB_WIDTH * 9 / 16)))

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

    print("greyscale screen (empirical anchors)")

    def anchor(handle):
        """Where a persona's ref lives — including after it has been quarantined.

        These anchors are photographs that were IN the bank and should not have been. Moving
        one out (never deleting it — that is the standing rule) must not quietly delete the
        evidence that the screen works, so the selftest follows it into quarantine.
        """
        for d in [PERSONAS] + sorted(glob.glob(os.path.join(PERSONAS, "_quarantine-*"))):
            p = os.path.join(d, handle, "ref.jpg")
            if os.path.exists(p):
                return p
        return None

    for handle, want, why in (
            ("m6070-hl-01", True, "true greyscale — flags"),
            ("f6070-wh-05", False, "muted COLOUR (grey seamless, cream knit) — stays clean; "
                                   "a p95-chroma cut would have wrongly killed this one")):
        p = anchor(handle)
        if not p:
            check("%s available as an anchor" % handle, False)
            continue
        flagged, detail = monochrome_screen(Image.open(p))
        check("%s %s" % (handle, why), flagged == want, detail)
    p = anchor("f3039-wh-04")
    if p:
        flagged, detail = monochrome_screen(Image.open(p))
        check("f3039-wh-04 (1940s b&w) is NOT caught by pixels — this is the documented limit, "
              "and why is_monochrome_or_period exists in the rubric", flagged is False, detail)

    print("vision verdict evaluation")
    cell = {"gender": "male", "age_band": "40-49", "cell_id": "m4049-wh", "ethnicity_key": "wh"}
    good = {"is_camera_photograph": True, "person_count": 1, "apparent_age_min": 42,
            "apparent_age_max": 48, "apparent_gender": "male", "face_clearly_visible": True,
            "face_obscured": False, "beauty_filtered": False,
            "visible_text_or_watermark": False, "recognizable_public_figure": False,
            "is_monochrome_or_period": False, "face_angle_reads": "three-quarter",
            "studio_or_press_context": False,
            "official_or_representative_capacity": False,
            "identifying_text_in_frame": False, "minor_in_frame": False,
            "ethnicity_group": "white", "apparent_ethnicity": "white"}
    check("clean candidate passes", evaluate_vision(good, cell) == [])
    for tweak, label in (({"is_camera_photograph": False}, "AI/CGI rejected"),
                         ({"person_count": 2}, "two people rejected"),
                         ({"apparent_age_min": 20, "apparent_age_max": 27}, "age outside band rejected"),
                         ({"apparent_gender": "female"}, "wrong gender rejected"),
                         ({"face_obscured": True}, "obscured face rejected"),
                         ({"beauty_filtered": True}, "retouched face rejected"),
                         ({"visible_text_or_watermark": True}, "watermark rejected"),
                         ({"recognizable_public_figure": True}, "celebrity rejected"),
                         ({"is_monochrome_or_period": True}, "b&w / period photograph rejected"),
                         ({"face_angle_reads": "profile"}, "pure profile rejected"),
                         ({"face_angle_reads": "down-or-away"}, "head down / turned away rejected"),
                         ({"official_or_representative_capacity": True},
                          "minister at a lectern / faculty portrait / uniform rejected"),
                         ({"identifying_text_in_frame": True},
                          "team jersey or someone's party shirt rejected"),
                         ({"minor_in_frame": True}, "child anywhere in the frame rejected")):
        v = dict(good)
        v.update(tweak)
        check(label, evaluate_vision(v, cell) != [])
    check("frontal accepted", evaluate_vision(dict(good, face_angle_reads="frontal"), cell) == [])
    check("unparseable vision output rejected (fails CLOSED, unlike article_images.py)",
          evaluate_vision(None, cell) != [])

    # The whole ~470-row verdict cache predates these two keys. If a missing key read as a
    # rejection, every cached candidate would fail the early-out in process_candidate and the
    # cache would be worthless; if it read as an ENFORCED pass, monochrome faces already in the
    # cache would sail through. It has to read as "not asked", with the re-ask done by
    # process_candidate for exactly the candidates that would otherwise be accepted.
    legacy = {k: v for k, v in good.items() if k not in VISION_RUBRIC_KEYS_ADDED}
    check("a pre-2026-08-10 cached reading still passes (missing key = not asked, not 'no')",
          evaluate_vision(legacy, cell) == [])
    check("...but is not mistaken for a current one", not vision_is_current(legacy))
    check("a reading taken under today's rubric is current", vision_is_current(good))
    check("studio_or_press_context is RECORDED, not enforced",
          evaluate_vision(dict(good, studio_or_press_context=True), cell) == [])

    # The three readings that got through on 2026-08-10, written as the model actually answered
    # them. Each old gate is left at the value it really returned, so these fail unless the NEW
    # gate catches them on its own — which is the entire point, since the old answers were not
    # mistakes.
    check("a minister at a government lectern is refused even though the model, honestly, does "
          "not recognise her",
          evaluate_vision(dict(good, recognizable_public_figure=False,
                               studio_or_press_context=True,
                               official_or_representative_capacity=True), cell) != [])
    check("a jersey reading team-and-number is refused even though it is not a watermark",
          evaluate_vision(dict(good, visible_text_or_watermark=False,
                               identifying_text_in_frame=True), cell) != [])
    check("a baby carried facing its mother is refused even though person_count=1 is correct",
          evaluate_vision(dict(good, person_count=1, minor_in_frame=True), cell) != [])
    check("...and working for a living is still not representing: the chef stays",
          evaluate_vision(dict(good, studio_or_press_context=False,
                               official_or_representative_capacity=False), cell) == [])

    # Confirmation. The re-screen on 2026-08-10 found five of forty accepted faces changing band
    # or ethnicity on a second reading, so a face is written only when two readings agree — and
    # the pairing of reading to raw text has to survive a half-written row.
    print("second-reading confirmation")
    older = dict(good, apparent_age_min=45, apparent_age_max=55)   # centre 50: passes 40-49 + 2
    newer = dict(good, apparent_age_min=45, apparent_age_max=60)   # centre 52: does not
    check("two readings held -> both are re-scored, so the disagreeing one still rejects",
          any(evaluate_vision(v, cell) for v in
              vision_readings({"vision": older, "vision2": newer})))
    check("the boundary face the confirm rejects is NOT lost — it passes the next band up",
          evaluate_vision(newer, dict(cell, age_band="50-59")) == [])
    check("a row holding one reading asks for one more (VISION_CONFIRMATIONS=%d)"
          % VISION_CONFIRMATIONS,
          len(current_readings({"vision": good, "raw": "a"})) < VISION_CONFIRMATIONS)
    check("readings pair with their OWN raw text, never the other one's",
          current_readings({"vision": good, "raw": "first", "vision2": newer, "raw2": "second"})
          == [(good, "first"), (newer, "second")])
    check("a reading whose raw text was never stored still pairs, with an empty string",
          current_readings({"vision": good, "vision2": newer, "raw2": "second"})
          == [(good, ""), (newer, "second")])
    check("a stale-rubric first reading does not shift the second one's raw text onto it",
          current_readings({"vision": legacy, "raw": "stale", "vision2": good, "raw2": "fresh"})
          == [(good, "fresh")])

    print("quarantine: what a rejection is ABOUT decides whether it is bank-wide")
    check("a profile shot is barred everywhere",
          quarantine_blocks_readmission({"rejection_is_about": "photograph"}))
    check("a boundary face is barred only from the cell she left, so the next band can take her",
          not quarantine_blocks_readmission({"rejection_is_about": "pairing"}))
    check("nor does OUR bookkeeping error bar the photograph — the pixels were never in question",
          not quarantine_blocks_readmission({"rejection_is_about": "metadata"}))
    check("silence reads as the strict case — a wrong bar is undone by hand, a wrong re-admission "
          "comes back unnoticed",
          quarantine_blocks_readmission({}) and quarantine_blocks_readmission(None))

    # Age gate. These four are the reason it is not a bare interval-overlap test.
    def age(lo, hi, c=cell):
        return evaluate_vision(dict(good, apparent_age_min=lo, apparent_age_max=hi), c)

    check("an estimate straddling the band edge still passes (38-44 in 40-49)", age(38, 44) == [])
    young = {"gender": "male", "age_band": "20-29", "cell_id": "m2029-wh", "ethnicity_key": "wh"}
    check("APPARENT MINOR rejected (12-21 overlaps the 20-29 band but must never be sourced)",
          age(12, 21, young) != [])
    check("hedged estimate rejected (18-75 would otherwise satisfy every band in the taxonomy)",
          age(18, 75) != [])
    check("single-point touch rejected (29-70 must not land in the 20-29 cell)",
          age(29, 70, young) != [])
    check("centre outside the band rejected (52-58 is not a 40-49 face)", age(52, 58) != [])
    check("inverted min/max is normalised, not mis-read", age(48, 42) == [])

    print("ethnicity placement")
    tax_cells = cells_by_id(_load(TAXONOMY, "taxonomy"))
    check("every taxonomy cell declares a key the rubric can actually produce",
          all(c.get("ethnicity_key") in set(ETHNICITY_GROUP_TO_KEY.values())
              for c in tax_cells.values()),
          "keys seen: %s" % ",".join(sorted({c.get("ethnicity_key") for c in tax_cells.values()})))
    check("constrained token beats conflicting free text (the token is what we asked for)",
          ethnicity_key_of({"ethnicity_group": "black", "apparent_ethnicity": "white"}) == "bl")
    check("'unclear' returns None and does NOT fall through to the free text — a model that "
          "declined to call it must not be overruled by its own hedge",
          ethnicity_key_of({"ethnicity_group": "unclear",
                            "apparent_ethnicity": "possibly white"}) is None)
    check("legacy verdict with no token still places via free text (cache stays worth keeping)",
          ethnicity_key_of({"apparent_ethnicity": "African American"}) == "bl")
    check("'South Asian' lands in as, not in the mx bucket",
          ethnicity_key_of({"apparent_ethnicity": "South Asian"}) == "as")
    check("'Middle Eastern' lands in mx", ethnicity_key_of({"apparent_ethnicity":
                                                            "Middle Eastern"}) == "mx")
    check("a phrase nothing matches returns None rather than a guess",
          ethnicity_key_of({"apparent_ethnicity": "hard to say"}) is None)
    check("wrong group rejected for the cell",
          evaluate_vision(dict(good, ethnicity_group="asian"), cell) != [])
    check("unplaceable ethnicity rejected, not waved through",
          evaluate_vision(dict(good, ethnicity_group="unclear",
                               apparent_ethnicity=""), cell) != [])

    print("Open Images backend")
    fake_pool = [{"image_id": "id%03d" % i, "split": "train",
                  "url": "https://live.staticflickr.com/x/%d_o.jpg" % i,
                  "landing": "https://www.flickr.com/photos/u/%d" % i,
                  "licence": "cc-by-2.0", "author": "u%d" % i, "author_url": "",
                  "title": "t%d" % i, "bytes": 100_000 + i * 20_000,
                  "gender": "Predominantly Feminine" if i % 2 else "Predominantly Masculine",
                  # Every seventh row reads "Older" — thin, like the corpus, and coprime with
                  # the gender parity so the Older rows are not all one gender.
                  "age": "Older" if i % 7 == 0 else "Middle",
                  "box": [0, 0, 1, 1], "occluded": 0, "truncated": 0}
                 for i in range(60)]
    globals()["_OPENIMAGES_POOL"] = fake_pool
    fem, nxt = openimages_search(None, None, "gender=Predominantly Feminine", 1, 10)
    check("gender filter is honoured (MIAP does this for free, ahead of any model call)",
          len(fem) == 10 and all(c["raw"]["miap_gender"] == "Predominantly Feminine" for c in fem))
    check("byte floor drops the small originals before they cost a download",
          all(c["raw"]["bytes"] >= OPENIMAGES_MIN_BYTES for c in fem))
    again, _ = openimages_search(None, None, "gender=Predominantly Feminine", 1, 10)
    check("page 1 is deterministic — a resumed run must not re-judge the same faces",
          [c["id"] for c in again] == [c["id"] for c in fem])
    page2, _ = openimages_search(None, None, "gender=Predominantly Feminine", nxt, 10)
    check("page 2 is disjoint from page 1", not ({c["id"] for c in page2} & {c["id"] for c in fem}))
    check("shuffled, not corpus order (upload order would hand a cell one photographer's decade)",
          [c["id"] for c in fem] != sorted(c["id"] for c in fem))
    check("candidate declares CC BY 2.0 and passes the licence spine",
          licence_ok(fem[0]["licence_slug"])[0] is not None)
    check("sizes is empty on purpose — a geometry nobody measured is not a fact",
          fem[0]["sizes"] == [] and largest_size(fem[0], None, None)[1:3] == (0, 0))
    tail, tail_next = openimages_search(None, None, "gender=Predominantly Feminine", 99, 10)
    check("walking off the end stops rather than looping", tail == [] and tail_next == 99)

    print("flickr size ladder")
    lad = flickr_size_ladder("https://live.staticflickr.com/1/2_3_o.jpg")
    check("the metered `_o` rendition is never requested — it is the ONLY size flickr rate-limits",
          all("_o.jpg" not in u for u, _ in lad))
    check("largest unmetered rendition first, and it is the 2048px one",
          lad[0] == ("https://live.staticflickr.com/1/2_3_k.jpg", "flickr-2048"))
    check("...with a real fallback below it, so a rendition that was never generated is not "
          "mistaken for a deleted photograph", len(lad) > 1)
    check("every rung clears MIN_SHORT_EDGE at ordinary aspect ratios — a rung that cannot "
          "pass the floor is a request spent to earn a rejection",
          meets_resolution(2048, 1365) and meets_resolution(1600, 1067)
          and not meets_resolution(1024, 683))
    check("a URL that is not a recognisable original is passed through untouched",
          flickr_size_ladder("https://example.org/x.png") == [("https://example.org/x.png",
                                                               "as-given")])
    check("openimages candidates enter the ladder at its first rung",
          largest_size(fem[0], None, None)[3].endswith("_k.jpg"))

    print("target-met teardown")
    # The treadmill, reproduced. One worker, a job that blocks until released, and a queue
    # behind it: the old code cancelled one future at a time and blocked on each running one
    # in between, so the pool kept dequeuing while the walk crawled and the whole batch ran.
    gate, started = threading.Event(), []
    tp = ThreadPoolExecutor(max_workers=1)

    def _job(n):
        started.append(n)
        gate.wait(10)
        return n

    tp_futs = [(n, tp.submit(_job, n)) for n in range(40)]
    while not started:
        time.sleep(0.01)                      # let worker 0 pick up job 0
    seen_after_target = False
    for i, (n, f) in enumerate(tp_futs):
        if n >= 1:                            # stand-in for "the target has been met"
            if not seen_after_target:
                seen_after_target = True
                for _, t in tp_futs[i:]:
                    t.cancel()
            if f.cancelled():
                continue
            gate.set()
            f.result()
    gate.set()
    tp.shutdown(wait=True, cancel_futures=True)
    check("cancelling the whole tail in ONE pass stops the pool dequeuing — only the "
          "already-running candidate is judged after the target is met, not the rest of the "
          "page (this ran a batch to completion for 946s of wall-clock on 2026-08-10)",
          len(started) <= 2)
    check("...and every future behind it really is cancelled, not merely skipped",
          all(f.cancelled() for n, f in tp_futs if n >= 2))

    print("orphan reconciliation")
    orphan_doc = {"pool_id": "f-30s", "cell_id": "f3039-wh"}
    fake_bank = {"zz-orphan-01": {"dir": "/nope", "doc": orphan_doc, "ref": "/nope/ref.jpg"},
                 "zz-known-01": {"dir": "/nope", "doc": orphan_doc, "ref": "/nope/ref.jpg"}}
    real_index, real_load, real_write = INDEX, _load, _atomic_write
    stash = {"personas": {"zz-known-01": {"handle": "zz-known-01", "status": "active"}}}
    written = {}
    globals()["_load"] = lambda p, w: json.loads(json.dumps(stash))
    globals()["_atomic_write"] = lambda p, d: written.update(d)
    try:
        got = reconcile_orphans(fake_bank)
    finally:
        globals()["_load"], globals()["_atomic_write"] = real_load, real_write
    check("a persona dir with no index row is repaired", got == ["zz-orphan-01"])
    check("...as PENDING, never active — this path has judged nothing, and an active row IS "
          "the approval that puts a face on a live og:image",
          written["personas"]["zz-orphan-01"]["status"] == "pending")
    check("...carrying the fields the picker's rotation reads, seeded rather than absent",
          written["personas"]["zz-orphan-01"]["angles_used"] == []
          and written["personas"]["zz-orphan-01"]["pool_id"] == "f-30s")
    check("an already-indexed persona is left exactly as it was — repair must never "
          "downgrade an approved face back to pending",
          written["personas"]["zz-known-01"]["status"] == "active")

    older, _ = openimages_search(None, None, "gender=Predominantly Feminine;age=Older", 1, 20)
    all_old = {r["image_id"] for r in fake_pool
               if r["age"] == "Older" and r["gender"] == "Predominantly Feminine"
               and r["bytes"] >= OPENIMAGES_MIN_BYTES}
    seen_ages = [c["raw"]["miap_age"] for c in older]
    check("age=Older front-loads every Older row a 60-70 cell could want",
          all_old and set(c["id"] for c in older[:len(all_old)]) == all_old)
    check("...and it is an ORDER, not a filter: every Older row precedes every Middle one, "
          "and the Middle rows are all still there",
          seen_ages == sorted(seen_ages, key=lambda a: a != "Older")
          and seen_ages.count("Middle") == len(older) - len(all_old))
    deep_plain = {c["id"] for c in openimages_search(
        None, None, "gender=Predominantly Feminine", 1, 60)[0]}
    deep_age = {c["id"] for c in openimages_search(
        None, None, "gender=Predominantly Feminine;age=Older", 1, 60)[0]}
    check("the two orders walk the SAME corpus, so an age-primed cell still hits the cache "
          "on everything an ordinary cell already judged", deep_plain == deep_age)
    globals()["_OPENIMAGES_POOL"] = None

    print("photographer cap")
    fake_bank = {
        "a-01": {"doc": {"cell_id": "f3039-wh", "source": {"author": "Jane  Doe"}}},
        "a-02": {"doc": {"cell_id": "f4049-wh", "source": {"author": "jane doe"}}},
        "a-03": {"doc": {"cell_id": "f4049-wh", "source": {"author": "unknown"}}},
        "a-04": {"doc": {"cell_id": "f4049-wh", "source": {"author": ""}}},
    }
    pc, pb = author_counts(fake_bank, "f3039-wh")
    check("whitespace and case are the same photographer", pb.get("jane doe") == 2)
    check("per-cell tally counts only this cell", pc.get("jane doe") == 1)
    check("a missing author is not a photographer — otherwise one blank field caps the corpus",
          "unknown" not in pb and "" not in pb and author_key_of("unknown") == ""
          and author_key_of(None) == "")
    check("one per cell, three per bank",
          pc["jane doe"] >= AUTHOR_CAP_CELL and pb["jane doe"] < AUTHOR_CAP_BANK)

    print("verdict cache")
    cache_tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    cache_tmp.close()
    real_path = OPENIMAGES_VERDICTS
    globals()["OPENIMAGES_VERDICTS"] = cache_tmp.name
    try:
        oi = {"platform": "openimages", "id": "abc123"}
        verdict_remember(oi, vision=dict(good, apparent_gender="female"), raw="{}")
        verdict_remember({"platform": "commons", "id": "999"}, reject=["watermark", "no"])
        check("only the Open Images backend writes (a Commons id does not mean the same pixels)",
              verdict_cached({"platform": "commons", "id": "999"}) is None)
        check("cache reloads from disk", verdict_cache_load() == 1)
        cached_v = verdict_cached(oi)["vision"]
        check("a verdict refused by one cell is re-scored, not replayed, for the next: "
              "'wrong gender' is a fact about the PAIRING",
              evaluate_vision(cached_v, cell) != []
              and evaluate_vision(cached_v, dict(cell, gender="female")) == [])
        with open(cache_tmp.name, "a") as fh:
            fh.write('{"image_id": "trunc"')          # what a kill mid-write leaves behind
        check("a half-written last line is skipped, not treated as a reason to refuse to run",
              verdict_cache_load() == 1)
    finally:
        globals()["OPENIMAGES_VERDICTS"] = real_path
        os.unlink(cache_tmp.name)
        _VERDICT_CACHE.clear()

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

    print("concurrency")
    template = requests.Session()
    template.headers["User-Agent"] = "selftest/1.0"
    seen_sessions, lock = [], threading.Lock()
    # The barrier is the test. Without it the four tasks are so short that one pool thread
    # runs all four before the others are even spawned — and the run then "passes" a
    # single-threaded execution as proof of thread isolation. Held objects, not id()s:
    # a freed session's id is free to reappear on the next one.
    barrier = threading.Barrier(4, timeout=10)

    def grab():
        # Twice on purpose: the same thread must be handed the same session both times, or
        # the connection pooling this is built on top of never actually pools.
        a, b = worker_session(template), worker_session(template)
        with lock:
            seen_sessions.append((a, b))
        barrier.wait()

    with ThreadPoolExecutor(max_workers=4) as tp:
        list(tp.map(lambda _: grab(), range(4)))
    check("a worker thread reuses its own session",
          all(a is b for a, b in seen_sessions))
    distinct = {id(a) for a, _ in seen_sessions}
    check("no two worker threads share a session (requests pools are not thread-safe)",
          len(distinct) == 4, "%d distinct across 4 threads" % len(distinct))
    check("the worker session inherits the UA the run identifies itself with",
          worker_session(template).headers.get("User-Agent") == "selftest/1.0")

    set_download_concurrency(3)
    held = [_DOWNLOAD_GATE.acquire(blocking=False) for _ in range(4)]
    for _ in range(sum(held)):
        _DOWNLOAD_GATE.release()
    check("the download gate admits exactly --download-concurrency at a time",
          held == [True, True, True, False])
    set_download_concurrency(0)
    check("a nonsensical download concurrency still admits one, never zero",
          _DOWNLOAD_GATE.acquire(blocking=False) and not _DOWNLOAD_GATE.acquire(blocking=False))
    _DOWNLOAD_GATE.release()
    set_download_concurrency(2)

    set_vision_concurrency(2)
    vheld = [_VISION_GATE.acquire(blocking=False) for _ in range(3)]
    for _ in range(sum(vheld)):
        _VISION_GATE.release()
    check("the vision gate admits exactly --vision-concurrency at a time",
          vheld == [True, True, False])
    check("the two gates are INDEPENDENT — --workers may stay high for downloading and "
          "hashing without piling that many callers onto 9router",
          _VISION_GATE is not _DOWNLOAD_GATE)
    set_vision_concurrency(0)
    check("a nonsensical vision concurrency still admits one, never zero",
          _VISION_GATE.acquire(blocking=False) and not _VISION_GATE.acquire(blocking=False))
    _VISION_GATE.release()
    set_vision_concurrency(6)

    check("a 502 from the router is transient — it is shedding load, not judging a photo",
          vision_is_transient("gem9 exit 1: gem9: HTTP 502: error code: 502"))
    check("...and so are 429/503/504",
          all(vision_is_transient("gem9: HTTP %s: x" % c) for c in ("429", "503", "504")))
    check("a 400 is NOT retried — asking twice does not make a bad request good",
          not vision_is_transient("gem9 exit 1: gem9: HTTP 400: bad request"))
    check("nor is an unparseable answer, which is a fault and not a load symptom",
          not vision_is_transient("gem9 exited 0 but returned no JSON: ''"))

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

    f = sub.add_parser("fetch", help="fill ONE taxonomy cell from a CC image source")
    f.add_argument("--cell", required=True, help="cell_id from personas/taxonomy.json")
    f.add_argument("--source", choices=sorted(SEARCH_BACKENDS), default="commons",
                   help="openimages (no key; MIAP pre-filters gender and person count, so it "
                        "spends far fewer vision calls per accept), commons (no key), or "
                        "flickr (needs FLICKR_API_KEY)")
    f.add_argument("--limit", type=int, default=None, help="accept at most N (default: the cell's shortfall)")
    f.add_argument("--depth", type=int, default=None,
                   help="bring the cell UP TO N faces, doing nothing if it is already there. "
                        "Unlike --limit this describes the bank rather than the run, so an "
                        "interrupted breadth pass can be re-run without deepening what it "
                        "already reached")
    f.add_argument("--dry-run", action="store_true",
                   help="run every gate for real but write nothing")
    f.add_argument("--pages", type=int, default=3,
                   help="pages per query (default 3; one page returns the same popular photos)")
    f.add_argument("--per-page", type=int, default=500,
                   help="results per page (Flickr max 500; Commons caps anonymous callers at 50)")
    f.add_argument("--queries", type=int, default=12, help="cap on composed query phrasings")
    f.add_argument("--max-candidates", type=int, default=400,
                   help="stop after examining this many photos (reported at the end)")
    f.add_argument("--sleep", type=float, default=0.3,
                   help="seconds between source calls (search pages AND per-candidate getSizes)")
    f.add_argument("--workers", type=int, default=6,
                   help="candidates judged concurrently (default 6). Almost all of a candidate's "
                        "wall-clock is one gem9 vision call this process only waits on.")
    f.add_argument("--download-concurrency", type=int, default=2,
                   help="simultaneous asset downloads (default 2, deliberately far below "
                        "--workers: upload.wikimedia.org throttles independently of the API)")
    f.add_argument("--vision-concurrency", type=int, default=6,
                   help="simultaneous gem9 vision calls (default 6). Also below --workers, and "
                        "for the same shape of reason: 9router sheds load above roughly six, "
                        "and a shed call costs a retry backoff far longer than the call itself.")
    f.add_argument("--no-getsizes", action="store_true",
                   help="skip the flickr.photos.getSizes lookup; judge resolution on search extras only")
    f.set_defaults(fn=cmd_fetch)

    v = sub.add_parser("verify", help="re-run the gates over the bank on disk")
    v.add_argument("--vision", action="store_true",
                   help="also re-run gate 5 through gem9 (off by default: verify is otherwise offline)")
    v.add_argument("--update-qc", action="store_true",
                   help="write the refreshed vision reading back into persona.json (needs "
                        "--vision). Use after the rubric gains a key, so the answer is bought once")
    v.set_defaults(fn=cmd_verify)

    ap_ = sub.add_parser("approve", help="Kevin's verdict — the ONLY way a face becomes usable")
    ap_.add_argument("handles", nargs="+", help="persona handles he looked at")
    ap_.add_argument("--reject", action="store_true", help="retire these instead of approving")
    ap_.add_argument("--reason", help="why, when rejecting")
    ap_.add_argument("--by", help="who approved (default: kevin)")
    ap_.set_defaults(fn=cmd_approve)

    q = sub.add_parser("quarantine",
                       help="MOVE failed faces out of the bank so the corpus cannot re-admit them")
    q.add_argument("handles", nargs="+")
    q.add_argument("--reason", required=True,
                   help="slug for the folder, e.g. pose / monochrome / band")
    q.add_argument("--note", help="the full reason, written into persona.json")
    q.add_argument("--about", default="photograph",
                   choices=("photograph",) + QUARANTINE_LOCAL,
                   help="what the rejection is about. 'photograph' (default) bars the image from "
                        "the whole bank; 'pairing' and 'metadata' bar it only from the cell it "
                        "left, leaving the corpus free to re-admit it correctly")
    q.set_defaults(fn=cmd_quarantine)

    s = sub.add_parser("selftest", help="exercise the pure functions (no network, no API key)")
    s.set_defaults(fn=cmd_selftest)

    a = ap.parse_args()
    a.fn(a)


def _install_sigterm_handler():
    """Make `kill <pid>` unwind through the finally blocks instead of vanishing.

    A harvest across fifty cells is a long-running background job, so stopping it is a normal
    operation, not a crash. Default SIGTERM kills the interpreter outright: cmd_fetch's
    `finally: commit_accepted(...)` never runs, and every face write_persona() already put on
    disk becomes an orphan — a directory load_bank() counts toward the cell target and
    persona_picker.py, which reads only index.json, can never select. Measured 2026-08-10:
    one `kill` stranded f4049-wh-01 exactly that way.

    Ctrl-C was always safe (KeyboardInterrupt is an exception, so finallys run); this gives
    `kill` the same guarantee. SIGKILL still cannot be caught — reconcile_orphans() at the
    top of the next fetch is the backstop for that."""
    import signal

    def _bye(signum, _frame):
        # SystemExit unwinds; sys.exit() from a handler does the same thing. Anything that
        # merely sets a flag would need every blocking call to poll it, and the longest wait
        # in this program is a subprocess we do not control.
        raise SystemExit("\n✗ interrupted by signal %d — committing what was accepted first"
                         % signum)

    signal.signal(signal.SIGTERM, _bye)


if __name__ == "__main__":
    _install_sigterm_handler()
    main()

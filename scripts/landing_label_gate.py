#!/usr/bin/env python3
"""Label gate for generated product shots (product-image-brandlock 3-pass gate, pass 2 = narrow text sweep).

  /usr/bin/python3 scripts/landing_label_gate.py <image> [--handle ageaura-pure-nmn-tmg-nad-complex]

Exit 0 only when every required string in product_refs/<handle>.label.json is read
letter-perfect (case/space-insensitive) and the read does not conflict with that
whitelist. Exit 1 is a failure. It is not a pass.

macOS Vision is required to PASS a whitelist pack shot
  The CLI OCRs the image at 2x with swift + scripts/tools/label_ocr.swift
  (VNRecognizeTextRequest). A missing label JSON, a missing image, swift missing
  or non-zero, an empty read, a timeout, or any platform other than macOS exits 1.
  There is no flag that skips OCR and still exits 0.

When this gate is not called
  Scene images, and landing specs that have no pack_images and do not claim a
  label-gate pass ("label gate PASS", landing_label_gate, PACK FACE WHITELIST),
  are not whitelist pack shots. validate_landing.py does not run this gate for
  those. A label file without product_refs/<handle>-cutout.png is the same case:
  omit pack_images and do not claim a pass (the real PDP photo or the curated
  png is the pack). Listing pack_images there is an omit error, not an OCR run.
  A pack shot that claims a whitelist when the cutout exists still fails closed
  when the label file or Vision is unavailable.

Unit tests pass ocr_lines into evaluate() so CI can prove the fail-closed
branches without Vision. The mark (logo) cannot be OCR'd: a 2x zoom against the
real pack is still required before shipping.
"""
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

import ageaura_rules
import brand_rules

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SWIFT_SCRIPT = os.path.join(ROOT, "scripts", "tools", "label_ocr.swift")
_GUMMY_COUNT = re.compile(r"\b(\d+)\s*gummies?\b", re.I)
_MG_DOSE = re.compile(r"\b\d+(?:\.\d+)?\s*mg\b", re.I)
_SERVING_30 = re.compile(r"\b30\s+servings?\b", re.I)
_WHITELIST_CLAIM = re.compile(
    r"label gate\s+PASS|landing_label_gate(?:\.py)?|PACK FACE WHITELIST",
    re.I,
)

# Quoted OCR misses for stocked products that still have no whitelist. These are
# notes, not required strings. Do not copy them into a .label.json.
_MISSING_NOTES = {
    "ageaura-pure-urolithin-a": (
        "This SKU is not an allowed AgeAura product. Do not create a promotion whitelist for it."
    ),
}
_NO_MG_NOTE = {
    "shilajit-shockwave": "shockwave label has no milligram token",
    "turkesterone-advanced-formula": "turkesterone label has no milligram token",
}
_CAPSULE_COUNT = re.compile(r"\b(\d+)\s*capsules?\b", re.I)


class LabelGateError(Exception):
    """Whitelist pack shot failed closed. Callers must not treat this as a skip or a pass."""


def norm(s):
    return re.sub(r"[^a-z0-9+*]", "", (s or "").lower())


def label_json_path(handle, root=None):
    root = ROOT if root is None else root
    return os.path.join(root, "product_refs", "%s.label.json" % handle)


def missing_label_note(handle):
    """Why a missing whitelist fails closed. Does not invent label text."""
    extra = _MISSING_NOTES.get(handle)
    note = (
        "FAIL CLOSED: no label whitelist at product_refs/%s.label.json. "
        "A pack shot that claims a label whitelist cannot pass without that file. "
        "macOS Vision is required to build one (swift scripts/tools/label_ocr.swift "
        "on the local pack PNG). Copy only lines the read got letter-perfect. "
        "Do not invent OCR text. A host without macOS Vision cannot PASS this gate; "
        "unit tests stub OCR lines and still must not report a pass."
    ) % handle
    if extra:
        note += " " + extra
    return note


def load_label_spec(handle, root=None):
    path = label_json_path(handle, root)
    if not os.path.isfile(path):
        raise LabelGateError(missing_label_note(handle))
    try:
        with open(path, encoding="utf-8") as fh:
            spec = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise LabelGateError(
            "FAIL CLOSED: label whitelist %s could not be read (%s). "
            "Refusing to treat the pack shot as PASS."
            % (os.path.basename(path), exc)
        )
    required = spec.get("required") if isinstance(spec, dict) else None
    if not isinstance(required, list) or not required:
        raise LabelGateError(
            "FAIL CLOSED: %s has no required whitelist strings. An empty whitelist is not a pass."
            % os.path.basename(path)
        )
    return spec


def claims_label_whitelist(spec):
    """True when the spec lists pack shots or says those shots used the label whitelist."""
    if spec.get("pack_images"):
        return True
    return bool(_WHITELIST_CLAIM.search(json.dumps(spec)))


def expected_gummy_counts(spec):
    """Gummy counts written on the label whitelist. Empty when the label has none."""
    blobs = [str(s) for s in (spec.get("required") or []) + (spec.get("optional") or [])]
    counts = []
    for blob in blobs:
        for match in _GUMMY_COUNT.finditer(blob):
            count = int(match.group(1))
            if count not in counts:
                counts.append(count)
    if counts or not re.search(r"\bgummies?\b", " ".join(blobs), re.I):
        return counts
    for blob in spec.get("required") or []:
        token = str(blob).strip()
        if re.fullmatch(r"\d+", token):
            count = int(token)
            if count not in counts:
                counts.append(count)
    return counts


def _bare_gummy_counts(spec, expected):
    bare = []
    for blob in spec.get("required") or []:
        token = str(blob).strip()
        if re.fullmatch(r"\d+", token) and int(token) in expected and int(token) not in bare:
            bare.append(int(token))
    return bare


def gummy_count_conflicts(spec, lines):
    expected = expected_gummy_counts(spec)
    if not expected:
        return []
    allowed = ", ".join(str(n) for n in expected)
    bare = _bare_gummy_counts(spec, expected)
    bad = []
    for line in lines:
        for match in _GUMMY_COUNT.finditer(line):
            count = int(match.group(1))
            if count not in expected:
                bad.append("%s (label gummy count is %s)" % (match.group(0), allowed))
        stripped = line.strip()
        if bare and re.fullmatch(r"\d+", stripped) and int(stripped) not in expected:
            bad.append("%s (label gummy count is %s)" % (stripped, allowed))
    return bad


def milligram_conflicts(spec, lines):
    """A whitelist with no milligram token rejects a milligram in the read."""
    note = _NO_MG_NOTE.get(spec.get("handle"))
    if not note:
        return []
    catalog = " ".join(str(s) for s in (spec.get("required") or []) + (spec.get("optional") or []))
    if _MG_DOSE.search(catalog):
        return []
    bad = []
    for line in lines:
        for match in _MG_DOSE.finditer(line):
            bad.append("invented milligram dose %s (%s)" % (match.group(0), note))
    return bad


def expected_capsule_counts(spec):
    """Capsule counts written on the Turkesterone whitelist. Empty for every other SKU."""
    if spec.get("handle") != "turkesterone-advanced-formula":
        return []
    blobs = [str(s) for s in (spec.get("required") or []) + (spec.get("optional") or [])]
    counts = []
    for blob in blobs:
        for match in _CAPSULE_COUNT.finditer(blob):
            count = int(match.group(1))
            if count not in counts:
                counts.append(count)
    if counts or not re.search(r"\bcapsules?\b", " ".join(blobs), re.I):
        return counts
    for blob in spec.get("required") or []:
        token = str(blob).strip()
        if re.fullmatch(r"\d+", token):
            count = int(token)
            if count not in counts:
                counts.append(count)
    return counts


def capsule_count_conflicts(spec, lines):
    expected = expected_capsule_counts(spec)
    if not expected:
        return []
    allowed = ", ".join(str(n) for n in expected)
    bare = []
    for blob in spec.get("required") or []:
        token = str(blob).strip()
        if re.fullmatch(r"\d+", token) and int(token) in expected and int(token) not in bare:
            bare.append(int(token))
    bad = []
    for line in lines:
        for match in _CAPSULE_COUNT.finditer(line):
            count = int(match.group(1))
            if count not in expected:
                bad.append("%s (label capsule count is %s)" % (match.group(0), allowed))
        stripped = line.strip()
        if bare and re.fullmatch(r"\d+", stripped) and int(stripped) not in expected:
            bad.append("%s (label capsule count is %s)" % (stripped, allowed))
    return bad


def serving_panel_conflicts(spec, lines):
    """A 60-DAY SUPPLY label does not support a 30-serving panel in the same read."""
    catalog = " ".join(str(s) for s in (spec.get("required") or []) + (spec.get("optional") or []))
    if not re.search(r"60-DAY SUPPLY", catalog, re.I) or _SERVING_30.search(catalog):
        return []
    bad = []
    for line in lines:
        match = _SERVING_30.search(line)
        if match:
            bad.append("%s (label says 60-DAY SUPPLY, not a 30-serving panel)" % match.group(0))
    return bad


def assess_lines(spec, lines):
    """Compare an OCR read to the whitelist. Does not call Vision."""
    blob = norm(" ".join(lines))
    missing = [s for s in spec["required"] if norm(s) not in blob]

    def word_norm(word):
        return re.sub(r"[^a-z0-9]", "", word.lower())

    vocab = {
        word_norm(word)
        for phrase in (spec["required"] + spec.get("optional", []))
        for word in str(phrase).split()
        if len(word_norm(word)) >= 4
    }
    garbled = []
    for line in lines:
        for word in line.split():
            token = word_norm(word)
            if len(token) >= 4 and token not in vocab:
                close = difflib.get_close_matches(token, vocab, n=1, cutoff=0.75)
                if close:
                    garbled.append("%s (~%s)" % (word, close[0]))
    conflicts = (gummy_count_conflicts(spec, lines) + milligram_conflicts(spec, lines)
                 + serving_panel_conflicts(spec, lines) + capsule_count_conflicts(spec, lines))
    return {
        "missing": missing,
        "garbled": garbled,
        "conflicts": conflicts,
        "ok": not missing and not garbled and not conflicts,
    }


def _upscale(image_path):
    image = Image.open(image_path).convert("RGB")
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    image.save(tmp)
    return tmp


def _run_swift(swift, script, image):
    return subprocess.run([swift, script, image], capture_output=True, text=True, timeout=180)


def read_ocr_lines(image_path, runner=None, platform=None, swift_bin=None, swift_script=None):
    """OCR one image. runner(swift, script, tmp_png) -> process with returncode/stdout/stderr.

    platform, swift_bin, and swift_script are injectable so tests can prove the
    fail-closed branches without macOS Vision.
    """
    host = sys.platform if platform is None else platform
    if host != "darwin":
        raise LabelGateError(
            "FAIL CLOSED: label OCR needs macOS Vision (swift + scripts/tools/label_ocr.swift). "
            "This host is %s. An unsupported platform is not a pass and not a skip "
            "for a whitelist pack shot." % host
        )
    if swift_bin is None:
        swift_bin = shutil.which("swift")
    if not swift_bin:
        raise LabelGateError(
            "FAIL CLOSED: swift is not on PATH, so macOS Vision OCR did not run. Missing swift is not a pass."
        )
    script = _SWIFT_SCRIPT if swift_script is None else swift_script
    if not os.path.isfile(script):
        raise LabelGateError(
            "FAIL CLOSED: %s is missing, so the label cannot be read. Refusing to treat that as PASS." % script
        )
    if not image_path or not os.path.isfile(image_path):
        raise LabelGateError("FAIL CLOSED: pack image not found (%s). Refusing to treat that as PASS." % image_path)
    tmp = _upscale(image_path)
    try:
        proc = (runner or _run_swift)(swift_bin, script, tmp)
    except subprocess.TimeoutExpired:
        raise LabelGateError("FAIL CLOSED: label OCR timed out. Refusing to treat a hung read as PASS.")
    except OSError as exc:
        raise LabelGateError("FAIL CLOSED: label OCR could not start (%s). Refusing to treat that as PASS." % exc)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    if proc.returncode != 0:
        detail = ((proc.stderr or proc.stdout or "").strip().splitlines() or ["no output"])[-1][:200]
        raise LabelGateError(
            "FAIL CLOSED: label_ocr.swift exited %s (%s). A failed OCR read is not a pass."
            % (proc.returncode, detail)
        )
    lines = [line.split("\t", 1)[1] for line in (proc.stdout or "").splitlines() if "\t" in line]
    if not any(line.strip() for line in lines):
        raise LabelGateError("FAIL CLOSED: OCR returned no text lines. An empty read is not a pass.")
    return lines


def evaluate(handle, image_path=None, ocr_lines=None, root=None, runner=None, platform=None, swift_bin=None, swift_script=None):
    """Check one whitelist pack shot.

    Pass ocr_lines to skip Vision (tests only). None means read the image, and a
    Vision failure raises LabelGateError instead of returning ok.
    A denied AgeAura handle fails closed even when a label file exists.
    """
    try:
        ageaura_rules.require_target(handle)
    except ageaura_rules.AgeAuraProductError as exc:
        raise LabelGateError("FAIL CLOSED: " + str(exc))
    spec = load_label_spec(handle, root)
    if ocr_lines is None:
        lines = read_ocr_lines(
            image_path, runner=runner, platform=platform, swift_bin=swift_bin, swift_script=swift_script
        )
    else:
        lines = [str(line) for line in ocr_lines]
        if not any(line.strip() for line in lines):
            raise LabelGateError("FAIL CLOSED: OCR returned no text lines. An empty read is not a pass.")
    result = assess_lines(spec, lines)
    result["lines"] = lines
    result["required_count"] = len(spec["required"])
    return result


def failure_text(result):
    parts = []
    if result["missing"]:
        parts.append("missing: " + "; ".join(result["missing"]))
    if result["garbled"]:
        parts.append("garbled: " + "; ".join(result["garbled"]))
    if result["conflicts"]:
        parts.append("conflict: " + "; ".join(result["conflicts"]))
    return " ".join(parts)


def _default_run_gate(root, image, handle):
    path = image if os.path.isabs(image) else os.path.join(root, image)
    proc = subprocess.run(
        [sys.executable, os.path.join(root, "scripts", "landing_label_gate.py"), path, "--handle", handle],
        capture_output=True, text=True,
    )
    lines = (proc.stdout or proc.stderr or "").strip().splitlines()
    return proc.returncode, (lines[-1] if lines else "no gate output")


def whitelist_pack_errors(spec, root=None, run_gate=None):
    """Hard errors for a spec that claims a label whitelist. Empty when none are claimed.

    run_gate(image, handle) -> (returncode, summary). The default subprocesses this
    script. A missing label file fails closed and does not call run_gate.
    A label file with no product_refs/<handle>-cutout.png does not call run_gate
    either: the spec must omit pack_images and use the curated pack photo.
    """
    root = ROOT if root is None else root
    if not claims_label_whitelist(spec):
        return []
    found = re.search(r"/products/([a-z0-9-]+)", json.dumps(spec))
    if not found:
        return ["FAIL CLOSED: pack shot claims a label whitelist but the spec has no /products/<handle>."]
    handle = found.group(1)
    if ageaura_rules.guard_product_handle(handle) is None:
        return ["pack_images label gate FAIL CLOSED: " + ageaura_rules.denial_message(handle)]
    if not os.path.isfile(label_json_path(handle, root)):
        return ["pack_images label gate FAIL CLOSED: " + missing_label_note(handle)]
    cutout = os.path.join(root, "product_refs", handle + "-cutout.png")
    if not os.path.isfile(cutout):
        # No generated-shot path exists. Running OCR here forced the 2026-10-16
        # turkesterone spec to keep a failed pack_images list, and the daily
        # reminder forced that list whenever a label file existed.
        return [(
            "omit pack_images for %s: product_refs/%s-cutout.png does not exist, "
            "so this is not a whitelist pack shot. Remove pack_images and do not "
            "claim a label-gate pass. Use the live PDP image or product_refs/%s.png."
        ) % (handle, handle, handle)]
    packs = spec.get("pack_images") or []
    if not packs:
        return [(
            "FAIL CLOSED: spec claims a label-gate pass for %s but pack_images is empty, "
            "so the whitelist was not checked."
        ) % handle]
    gate = run_gate or (lambda image, gated: _default_run_gate(root, image, gated))
    errors = []
    for image in packs:
        code, line = gate(image, handle)
        if code != 0:
            errors.append("pack_images %s: label gate FAIL (%s)" % (image, line[:120]))
    return errors


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or "--help" in argv or "-h" in argv:
        print(__doc__.strip())
        return 2
    args = [arg for arg in argv if not arg.startswith("--")]
    if "--handle" in argv:
        handle = argv[argv.index("--handle") + 1]
    else:
        handle = brand_rules.AGEAURA_OK
    if handle in args:
        args.remove(handle)
    if not args:
        print("FAIL CLOSED: no pack image path. Refusing to treat that as PASS.")
        return 1
    try:
        handle, _how = brand_rules.resolve_handle(handle)
    except brand_rules.GuardError as exc:
        print("✗ LABEL FAIL CLOSED: " + str(exc))
        return 1
    try:
        result = evaluate(handle, args[0])
    except LabelGateError as exc:
        print("✗ " + str(exc))
        return 1
    print("read:", " | ".join(result["lines"]))
    if not result["ok"]:
        print("✗ LABEL FAIL " + failure_text(result))
        return 1
    print("✓ LABEL PASS (%d required strings read letter-perfect)" % result["required_count"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

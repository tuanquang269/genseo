"""Brand guard: AgeAura promotion (Kevin 2026-10-06, re-audited 2026-10-09), the
FloraFresh formula (Kevin 2026-10-09), the Shilajit Shockwave pack label, the
Pure Shilajit Gold Resin pack label, the ShilaSource Himalayan Shilajit Resin
pack label, and the Turkesterone Advanced Formula pack label.

AgeAura may promote exactly one SKU:

    ageaura-pure-nmn-tmg-nad-complex
    https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex

Urolithin A, every other AgeAura handle (p2, duos, peptides), and
/collections/ageaura are denied. An ambiguous "AgeAura" with no NMN + TMG
product is not a second SKU: callers either reject it or lock it to the
allowed product via prepare_ticket / prepare_image_request.

FloraFresh copy follows its Supplement Facts label (Bacillus coagulans SNZ-1969,
1 billion CFU per 2 gummies), not the wrong PDP description. florafresh_rules.py
holds those facts.

Shilajit Shockwave copy follows product_refs/shilajit-shockwave.label.json.
shockwave_rules.py rejects a milligram amount, a serving count, or any other
dose that file does not list. The file has no milligram token and no volume
line. Gummies, Gold Resin, and ShilaSource resin are not this product.

Pure Shilajit Gold Resin copy follows product_refs/pure-shilajit-gold-resin.label.json.
gold_resin_rules.py rejects a milligram amount, a serving count, a volume, a
weight, a day-supply, or any other dose that file's required and optional lines
do not contain. The OCR serving line and 75% Fulvic are allowed only because
they are in that file. No milligram token was read. Gummies, Shockwave, and
ShilaSource resin are not this product.

ShilaSource Himalayan Shilajit Resin copy follows
product_refs/shilasource-himalayan-shilajit-resin.label.json.
shilasource_resin_rules.py rejects a milligram amount, a serving count, a
volume, a weight, a fulvic percentage, a mineral count, a day-supply, or any
other dose that file's required and optional lines do not contain. The fulvic
line, the net-weight line, and the split servings badge are allowed only
because they are in that file. No milligram token was read. Gummies, Shockwave,
and Gold Resin are not this product.

Turkesterone Advanced Formula copy follows
product_refs/turkesterone-advanced-formula.label.json.
turkesterone_rules.py rejects a milligram amount, a serving count, a capsule
count, a day-supply, or any other dose that file's required and optional lines
do not contain. The front-of-pack lines and the split 60 / Capsules badge are
allowed only because they are in that file. No milligram token and no
Supplement Facts panel were read. Bare "turkesterone" is the ingredient and is
not this SKU. Gummies, Shockwave, Gold Resin, and ShilaSource resin are not
this product.

assess() denies any FloraFresh, Shockwave, Gold Resin, ShilaSource resin, or
Turkesterone claim those modules reject, so every caller below enforces them.
Landing specs use spec_violations().

Listicle and advertorial UI colors follow product_refs/<handle>.palette.json
(Kevin 2026-10-09). packaging_palette.py rejects a hard-window landing spec or
landing ticket that opts out of a chromatic pack or forces a hue the file does
not list. The painted page is checked by scripts/landing_palette.py. See
docs/PACKAGING_PALETTE_GUARD.md.

Local llms.txt drafts omit denied handles. A FloraFresh, FusiForce, or
shilajit-gummies formula line is included only when it matches the label source
of truth (scripts/llms_formula.py). Shockwave, Gold Resin, ShilaSource resin,
and Turkesterone get a URL and no dose sentence.

The AgeAura handle allow/deny list lives in ageaura_rules.py. This module
merges it with the other product guards. Ticket builders, landing builders,
image prompts, the publisher, llms.txt drafts, and IndexNow call this module.
Do not copy the handle into a third file.
"""
import json
import os
import re

import ageaura_rules
import florafresh_rules as florafresh
import gold_resin_rules as gold_resin
import llms_formula
import packaging_palette
import shilasource_resin_rules as shilasource_resin
import shockwave_rules as shockwave
import turkesterone_rules as turkesterone

AGEAURA_OK = ageaura_rules.HANDLE
AGEAURA_OK_URL = ageaura_rules.PRODUCT_URL
AGEAURA_PRODUCT_LABEL = ageaura_rules.PRODUCT_LABEL
LOCK_LINE = (
    "AgeAura product (only): " + AGEAURA_PRODUCT_LABEL + " (" + AGEAURA_OK_URL + ")."
)
_FORCE_REASON = "AgeAura named without the Pure NMN + TMG NAD Complex (" + AGEAURA_OK + ")"

_UROLITHIN = re.compile(r"urolithin", re.I)
_AGEAURA = re.compile(r"ageaura", re.I)
_COLLECTION = re.compile(r"/collections/ageaura\b", re.I)
_OTHER_BUNDLE = re.compile(r"rejuvenation duo|essential longevity(?: duo)?", re.I)
_PEPTIDE = re.compile(
    r"ageaura[^\n]{0,40}peptides?|peptides?[^\n]{0,40}ageaura|longevity peptides?",
    re.I,
)
_NMN_TMG_PHRASE = re.compile(r"nmn\s*(\+|and|/)\s*tmg", re.I)
_NMN_WORD = re.compile(r"\bnmn\b", re.I)
_TMG_WORD = re.compile(r"\btmg\b", re.I)
# Paths and URLs are not brand copy. The SKU check still sees the raw text.
_PATHISH = re.compile(
    r"https?://\S+|\]\([^)]*\)|(?:src|href)=[\"'][^\"']+[\"']"
    r"|tmp_images/\S+|product_refs/\S+|(?:^|[\s\"'])/?[\w./~-]+\.(?:png|jpe?g|webp|gif|html|json|md)\b",
    re.I,
)


class GuardError(Exception):
    def __init__(self, reasons):
        self.reasons = tuple(reasons)
        super().__init__("; ".join(self.reasons))


class Decision:
    def __init__(self, action, handle=None, reasons=()):
        self.action = action  # allow | deny | force
        self.handle = handle
        self.reasons = tuple(reasons)


def normalize_handle(handle):
    """Lowercase product handle. Accepts a bare handle, /products/<handle>, or a product URL."""
    return ageaura_rules.normalize_handle(handle)


def product_allowed(handle):
    """True for non-AgeAura SKUs and for the one allowed AgeAura SKU.

    A bare brand token ``ageaura`` (no product) is not a handle and returns False.
    Call resolve_handle() when that token should be locked to the NMN + TMG SKU.
    The allow/deny list is ageaura_rules.py.
    """
    return ageaura_rules.product_allowed(handle)


def collection_allowed(handle):
    return (handle or "").strip().lower() != "ageaura"


def mentions_allowed_product(text):
    text = text or ""
    if AGEAURA_OK in text.lower():
        return True
    return bool(_AGEAURA.search(text) and _has_nmn_tmg(text))


def _has_nmn_tmg(text):
    if _NMN_TMG_PHRASE.search(text):
        return True
    return bool(_NMN_WORD.search(text) and _TMG_WORD.search(text))


def _visible(text):
    return _PATHISH.sub(" ", text or "")


def assess(text):
    """Classify promotion copy.

    deny  — Urolithin A, another AgeAura SKU, a banned bundle, /collections/ageaura,
            a FloraFresh formula claim its Supplement Facts label does not support,
            a Shilajit Shockwave milligram, serving, or other dose the pack
            label whitelist does not list, a Pure Shilajit Gold Resin milligram,
            serving, volume, weight, day-supply, or other dose its pack-label
            whitelist does not list, a ShilaSource resin milligram, serving,
            volume, weight, fulvic percentage, mineral count, day-supply, or
            other dose its pack-label whitelist does not list, or a
            Turkesterone Advanced Formula milligram, serving, capsule count,
            day-supply, or other dose its pack-label whitelist does not list
    force — AgeAura is named and the Pure NMN + TMG product is not
    allow — no AgeAura, or AgeAura is tied to that one product, and no FloraFresh,
            Shockwave, Gold Resin, ShilaSource resin, or Turkesterone label miss
    """
    decision = _ageaura_decision(text)
    extra = (florafresh.violations(text) + shockwave.violations(text)
             + gold_resin.violations(text) + shilasource_resin.violations(text)
             + turkesterone.violations(text))
    if not extra:
        return decision
    reasons = list(decision.reasons) if decision.action == "deny" else []
    if decision.action == "force":
        reasons.append(_FORCE_REASON)
    return Decision("deny", None, tuple(_dedupe(reasons + extra)))


def _ageaura_decision(text):
    text = text or ""
    reasons = list(ageaura_rules.text_target_violations(text))
    if _UROLITHIN.search(text):
        reasons.append("Urolithin")
    if _COLLECTION.search(text):
        reasons.append("/collections/ageaura")
    if _OTHER_BUNDLE.search(text):
        reasons.append("other AgeAura bundle")
    if _PEPTIDE.search(text):
        reasons.append("AgeAura peptides")
    deduped = _dedupe(reasons)
    if deduped:
        return Decision("deny", None, tuple(deduped))
    if _AGEAURA.search(_visible(text)) and not mentions_allowed_product(text):
        return Decision(
            "force",
            AGEAURA_OK,
            ("AgeAura named without the Pure NMN + TMG NAD Complex",),
        )
    handle = AGEAURA_OK if _AGEAURA.search(text) else None
    return Decision("allow", handle, ())


def violations(text):
    """Hard-fail strings for lint and the article/landing gates.

    Ambiguous AgeAura is a violation until prepare_ticket / prepare_promotion
    locks the copy to the allowed SKU. Denied SKUs, FloraFresh formula claims,
    Shockwave pack-label claims, Gold Resin pack-label claims, ShilaSource
    resin pack-label claims, and Turkesterone pack-label claims stay violations
    either way. A landing-ticket line that opts out of a committed packaging
    palette, or forces a hue that file does not list, is a violation too
    (scripts/packaging_palette.py).
    """
    return _dedupe(_decision_violations(assess(text)) + packaging_palette.ticket_violations(text))


def spec_violations(spec):
    """violations() for a landing spec (the parsed JSON).

    AgeAura reads the whole spec, as the gates always did. FloraFresh, Shockwave,
    Gold Resin, ShilaSource resin, and Turkesterone are checked field by field,
    so source notes and the citation list may record what a PDP says; product,
    offer, sticky_cta, trust, chip, and bullets count as product claims. A
    listicle/advertorial created on or after 2026-10-09 is also checked against
    product_refs/<handle>.palette.json.
    """
    out = _decision_violations(_ageaura_decision(json.dumps(spec)))
    out = _dedupe(out + ageaura_rules.spec_target_violations(spec))
    return _dedupe(out + florafresh.spec_violations(spec) + shockwave.spec_violations(spec)
                   + gold_resin.spec_violations(spec)
                   + shilasource_resin.spec_violations(spec)
                   + turkesterone.spec_violations(spec)
                   + packaging_palette.spec_violations(spec))


def _decision_violations(decision):
    if decision.action == "allow":
        return []
    if decision.action == "force":
        return [_FORCE_REASON]
    return list(decision.reasons)


def _dedupe(items):
    out = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def resolve_handle(handle):
    """Return (handle, how). ``how`` is allow or force. Denied handles raise GuardError.

    The bare brand token ``ageaura`` is forced to the Pure NMN + TMG handle.
    """
    raw = normalize_handle(handle)
    if raw == "ageaura":
        return AGEAURA_OK, "force"
    if not raw:
        raise GuardError(["empty product handle"])
    if not product_allowed(raw):
        raise GuardError(violations(raw) or ["denied product handle: " + raw])
    return raw, "allow"


def prepare_promotion(text, on_ambiguous="force"):
    """Return copy that is safe to emit.

    on_ambiguous="force" appends the locked NMN + TMG line.
    on_ambiguous="reject" raises GuardError instead.
    Denied SKUs always raise.
    """
    decision = assess(text)
    if decision.action == "deny":
        raise GuardError(decision.reasons)
    if decision.action == "force":
        if on_ambiguous == "reject":
            raise GuardError(decision.reasons)
        if on_ambiguous != "force":
            raise ValueError("on_ambiguous must be 'force' or 'reject'")
        return _lock(text)
    return text or ""


def prepare_ticket(text):
    """Ticket/landing-brief text. Ambiguous AgeAura is locked to the one SKU."""
    return prepare_promotion(text, on_ambiguous="force")


def _lock(text):
    if mentions_allowed_product(text or ""):
        return text or ""
    base = (text or "").rstrip()
    return (base + "\n" + LOCK_LINE) if base else LOCK_LINE


def prepare_image_request(prompt, handle_specs):
    """Return (prompt, handle_specs) safe to send to an image generator.

    Urolithin copy or a denied handle raises GuardError (the prompt is not rewritten
    into a picture of that SKU). A bare ``ageaura`` handle, or AgeAura copy with no
    product, is locked to the Pure NMN + TMG bottle.
    """
    prompt = prompt or ""
    decision = assess(prompt)
    if decision.action == "deny":
        raise GuardError(decision.reasons)
    if decision.action == "force":
        prompt = _lock(prompt)
    resolved = []
    for spec in handle_specs or []:
        if "://" in spec:
            handle, _how = resolve_handle(spec)
            resolved.append(handle)
            continue
        raw, sep, idx = spec.partition(":")
        handle, _how = resolve_handle(raw)
        resolved.append(handle + ":" + idx if sep and idx else handle)
    bad = violations(prompt + "\n" + "\n".join(resolved))
    if bad:
        raise GuardError(bad)
    return prompt, resolved


def asset_path_allowed(path):
    """False when a pack-shot path is the Urolithin bottle or another AgeAura SKU."""
    return ageaura_rules.asset_path_allowed(path)


def indexnow_urls(urls):
    """Split URLs into (kept, blocked). Blocked URLs name a denied AgeAura SKU."""
    kept, blocked = [], []
    for url in urls:
        if assess(url).action == "deny":
            blocked.append(url)
        else:
            kept.append(url)
    return kept, blocked


def handles_from_product_refs(refs_dir):
    """Product handles declared by product_refs/*.json (not *.label.json or *.palette.json)."""
    handles = []
    if not refs_dir or not os.path.isdir(refs_dir):
        return handles
    for name in sorted(os.listdir(refs_dir)):
        if not name.endswith(".json") or name.endswith(".label.json") or name.endswith(".palette.json"):
            continue
        handles.append(name[: -len(".json")])
    return handles


def assert_llms_text(text):
    """Raise GuardError when a local llms.txt draft is not safe to keep.

    The draft must not name Urolithin A, and it must pass the same violations()
    gate as publishable copy. Formula lines that do not match a label are omitted
    before this runs; they are never written through.
    """
    if re.search(r"urolithin", text or "", re.I):
        raise GuardError(["llms.txt draft included a Urolithin A product; refusing to write it"])
    bad = violations(text)
    if bad:
        raise GuardError(bad)


def llms_txt_draft(handles):
    """Local llms.txt body. Denied handles are omitted, never written.

    Returns (text, rejected_handles). A bare ``ageaura`` handle is rewritten to
    the allowed SKU. FloraFresh, FusiForce, and shilajit-gummies formula lines are
    appended only when llms_formula.formula_line() matches the label source of
    truth. The returned text itself passes assert_llms_text().
    """
    kept = []
    rejected = []
    for raw in handles or []:
        token = normalize_handle(raw) or (raw or "")
        if token == "ageaura":
            token = AGEAURA_OK
        if not product_allowed(token):
            rejected.append(normalize_handle(raw) or str(raw))
            continue
        if token and token not in kept:
            kept.append(token)
    lines = [
        "# Wellness Nest — llms.txt draft (local only, not published)",
        "# AgeAura promotes one SKU: the Pure NMN + TMG NAD Complex. Every other AgeAura handle is omitted.",
        "# Formula lines are included only when they match the label source of truth.",
        "",
    ]
    for handle in kept:
        if handle == AGEAURA_OK:
            lines.append("- [" + AGEAURA_PRODUCT_LABEL + "](" + AGEAURA_OK_URL + ")")
        else:
            lines.append("- https://wellnessnest.co/products/" + handle)
        formula = llms_formula.formula_line(handle)
        if formula:
            lines.append("  " + formula)
    text = "\n".join(lines) + "\n"
    assert_llms_text(text)
    return text, rejected


def assert_publishable(title, body):
    """Raise GuardError when a draft must not be published or updated."""
    bad = violations((title or "") + "\n" + (body or ""))
    if bad:
        raise GuardError(bad)

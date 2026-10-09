"""AgeAura promotion guard (Kevin 2026-10-06, re-audited 2026-10-09).

AgeAura may promote exactly one SKU:

    ageaura-pure-nmn-tmg-nad-complex
    https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex

Urolithin A, every other AgeAura handle (p2, duos, peptides), and
/collections/ageaura are denied. An ambiguous "AgeAura" with no NMN + TMG
product is not a second SKU: callers either reject it or lock it to the
allowed product via prepare_ticket / prepare_image_request.

This module is the only allow/deny list. Ticket builders, landing builders,
image prompts, the publisher, llms.txt drafts, and IndexNow call it.
Do not copy the handle into another file.
"""
import os
import re

AGEAURA_OK = "ageaura-pure-nmn-tmg-nad-complex"
AGEAURA_OK_URL = "https://wellnessnest.co/products/" + AGEAURA_OK
AGEAURA_PRODUCT_LABEL = "AgeAura Pure NMN + TMG NAD+ Complex"
LOCK_LINE = (
    "AgeAura product (only): " + AGEAURA_PRODUCT_LABEL + " (" + AGEAURA_OK_URL + ")."
)

_ASSET_SUFFIX = re.compile(r"-(?:cutout|label|ref|pack)$", re.I)
_PRODUCT_PATH = re.compile(r"/products/([a-z0-9-]+)", re.I)
_PRODUCT_EQ = re.compile(r"(?:^|[\s|])product=([a-z0-9-]+)", re.I)
# Product handles only. Campaign slugs such as ageaura-nmn-listicle-261008 are not SKUs.
_BARE_AGEAURA_PRODUCT = re.compile(
    r"\b(ageaura-pure-[a-z0-9-]+|ageaura-[a-z0-9-]*(?:urolithin|peptide|duo|bundle)[a-z0-9-]*)\b",
    re.I,
)
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
    h = (handle or "").strip().lower()
    if not h:
        return ""
    found = _PRODUCT_PATH.search(h)
    if found:
        h = found.group(1)
    elif "://" not in h:
        h = h.split(":", 1)[0]
        h = h.strip().strip("/")
        if h.startswith("products/"):
            h = h[len("products/"):]
    h = _ASSET_SUFFIX.sub("", h)
    return h


def product_allowed(handle):
    """True for non-AgeAura SKUs and for the one allowed AgeAura SKU.

    A bare brand token ``ageaura`` (no product) is not a handle and returns False.
    Call resolve_handle() when that token should be locked to the NMN + TMG SKU.
    """
    h = normalize_handle(handle)
    if not h:
        return True
    if "urolithin" in h:
        return False
    if h == "ageaura" or h.startswith("ageaura-"):
        return h == AGEAURA_OK
    return True


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

    deny  — Urolithin A, another AgeAura SKU, a banned bundle, or /collections/ageaura
    force — the brand is named and the Pure NMN + TMG product is not
    allow — no AgeAura, or AgeAura is tied to that one product
    """
    text = text or ""
    reasons = []
    handles = []
    for rx in (_PRODUCT_PATH, _BARE_AGEAURA_PRODUCT, _PRODUCT_EQ):
        handles.extend(m.group(1).lower() for m in rx.finditer(text))
    for h in sorted(set(handles)):
        if not product_allowed(h):
            reasons.append("denied product handle: " + h)
    if _UROLITHIN.search(text):
        reasons.append("Urolithin")
    if _COLLECTION.search(text):
        reasons.append("/collections/ageaura")
    if _OTHER_BUNDLE.search(text):
        reasons.append("other AgeAura bundle")
    if _PEPTIDE.search(text):
        reasons.append("AgeAura peptides")
    deduped = []
    for reason in reasons:
        if reason not in deduped:
            deduped.append(reason)
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
    locks the copy to the allowed SKU. Denied SKUs stay violations either way.
    """
    decision = assess(text)
    if decision.action == "allow":
        return []
    if decision.action == "force":
        return [
            "AgeAura named without the Pure NMN + TMG NAD Complex (" + AGEAURA_OK + ")"
        ]
    return list(decision.reasons)


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
    base = os.path.basename(path or "").lower()
    if "urolithin" in base:
        return False
    if "ageaura" not in base:
        return True
    stem = _ASSET_SUFFIX.sub("", base.split(".")[0])
    if stem == AGEAURA_OK or stem.startswith(AGEAURA_OK):
        return True
    if stem.startswith("ageaura-pure-") or "urolithin" in stem:
        return product_allowed(stem)
    return True


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
    """Product handles declared by product_refs/*.json (not *.label.json)."""
    handles = []
    if not refs_dir or not os.path.isdir(refs_dir):
        return handles
    for name in sorted(os.listdir(refs_dir)):
        if not name.endswith(".json") or name.endswith(".label.json"):
            continue
        handles.append(name[: -len(".json")])
    return handles


def llms_txt_draft(handles):
    """Local llms.txt body. Denied handles are omitted, never written.

    Returns (text, rejected_handles). A bare ``ageaura`` handle is rewritten to
    the allowed SKU. The returned text itself passes violations().
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
        "",
    ]
    for handle in kept:
        if handle == AGEAURA_OK:
            lines.append("- [" + AGEAURA_PRODUCT_LABEL + "](" + AGEAURA_OK_URL + ")")
        else:
            lines.append("- https://wellnessnest.co/products/" + handle)
    text = "\n".join(lines) + "\n"
    bad = violations(text)
    if bad:
        raise GuardError(bad)
    return text, rejected


def assert_publishable(title, body):
    """Raise GuardError when a draft must not be published or updated."""
    bad = violations((title or "") + "\n" + (body or ""))
    if bad:
        raise GuardError(bad)

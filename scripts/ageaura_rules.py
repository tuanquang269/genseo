#!/usr/bin/env python3
"""AgeAura product-handle allowlist.

Kevin 2026-10-06, re-audited 2026-10-09: AgeAura content may target one product
handle:

    ageaura-pure-nmn-tmg-nad-complex
    https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex

`ageaura-pure-urolithin-a` and any other Urolithin A AgeAura handle are denied.
Any other `ageaura-*` product handle (p2, duos, peptides) is denied too. This
module does not unpublish the live Urolithin PDP and does not invent a label
claim.

brand_rules.py merges these handle checks with the FloraFresh, Shockwave, Gold
Resin, ShilaSource resin, and Turkesterone label guards. Ticket builders and
validate_landing.py call require_target() / spec_target_violations() so a
ticket or landing spec cannot target a denied handle.

Do not paste --brief into a ticket. The brief names the refused handle, and
the copy gate would reject that ticket.

  python3 scripts/ageaura_rules.py --brief
  python3 scripts/ageaura_rules.py --handle ageaura-pure-nmn-tmg-nad-complex
  python3 scripts/ageaura_rules.py --handle ageaura-pure-urolithin-a
  python3 scripts/ageaura_rules.py "<text>" | <file>
  python3 scripts/ageaura_rules.py --spec landing_drafts/<slug>.json
"""
import json
import os
import re
import sys

HANDLE = "ageaura-pure-nmn-tmg-nad-complex"
PRODUCT_URL = "https://wellnessnest.co/products/" + HANDLE
PRODUCT_LABEL = "AgeAura Pure NMN + TMG NAD+ Complex"
DENIED_HANDLE = "ageaura-pure-urolithin-a"
ALLOWED_HANDLES = frozenset({HANDLE})
# The known refused SKU. classify_handle() also refuses any other handle that
# contains "urolithin" or any other ageaura-* product handle.
DENIED_HANDLES = frozenset({DENIED_HANDLE})
BRIEF = (
    "AgeAura product (only): " + PRODUCT_LABEL + " (" + PRODUCT_URL + "). "
    "Handle allowlist: " + HANDLE + ". "
    "Refuse " + DENIED_HANDLE + " and any other Urolithin A AgeAura handle. "
    "This guard does not unpublish the live Urolithin PDP."
)

ASSET_SUFFIX = re.compile(r"-(?:cutout|label|ref|pack)$", re.I)
_PRODUCT_PATH = re.compile(r"/products/([a-z0-9-]+)", re.I)
_PRODUCT_EQ = re.compile(r"(?:^|[\s|])product=([a-z0-9-]+)", re.I)
# Product handles only. Campaign slugs such as ageaura-nmn-listicle-261008 are not SKUs.
_BARE_AGEAURA_PRODUCT = re.compile(
    r"\b(ageaura-pure-[a-z0-9-]+|ageaura-[a-z0-9-]*(?:urolithin|peptide|duo|bundle)[a-z0-9-]*)\b",
    re.I,
)
_PRODUCT_FIELDS = frozenset({"product_ref", "sku", "product_handle"})


class AgeAuraProductError(Exception):
    def __init__(self, reasons):
        if isinstance(reasons, str):
            reasons = [reasons]
        self.reasons = tuple(reasons)
        super().__init__("; ".join(self.reasons))


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
    h = ASSET_SUFFIX.sub("", h)
    return h


def classify_handle(handle):
    """allow | deny | other.

    allow — the NMN + TMG handle
    deny  — Urolithin A (any handle containing urolithin), the bare token
            ``ageaura``, or any other ageaura-* handle
    other — empty, or a product that is not an AgeAura SKU
    """
    h = normalize_handle(handle)
    if not h:
        return "other"
    if h in DENIED_HANDLES or "urolithin" in h:
        return "deny"
    if h == "ageaura" or h.startswith("ageaura-"):
        return "allow" if h in ALLOWED_HANDLES else "deny"
    return "other"


def product_allowed(handle):
    """True for non-AgeAura SKUs and for the one allowed AgeAura SKU.

    A bare brand token ``ageaura`` returns False. Empty input returns True
    (no handle was supplied). Callers about to emit a target use require_target(),
    which rejects an empty handle.
    """
    return classify_handle(handle) != "deny"


def denial_message(handle):
    h = normalize_handle(handle) or (handle or "").strip().lower()
    return "denied product handle: " + h


def require_target(handle):
    """Return the normalized handle when it may be a ticket or landing target.

    Denied AgeAura handles raise AgeAuraProductError. A non-AgeAura product
    handle is returned unchanged. The bare token ``ageaura`` is denied here;
    brand_rules.resolve_handle() is what locks that token to the NMN SKU.
    """
    kind = classify_handle(handle)
    h = normalize_handle(handle)
    if kind == "deny":
        raise AgeAuraProductError([denial_message(handle)])
    if not h:
        raise AgeAuraProductError(["empty product handle"])
    return h


def guard_product_handle(handle):
    """Normalized handle, or None when this must not be emitted as a product target."""
    try:
        return require_target(handle)
    except AgeAuraProductError:
        return None


def handles_in_text(text):
    """Product handles named as /products/<handle>, product=<handle>, or an AgeAura SKU token.

    Campaign slugs (ageaura-nmn-listicle-261008) are not returned.
    """
    found = []
    for rx in (_PRODUCT_PATH, _BARE_AGEAURA_PRODUCT, _PRODUCT_EQ):
        found.extend(m.group(1).lower() for m in rx.finditer(text or ""))
    return sorted(set(found))


def text_target_violations(text):
    """Denied AgeAura product handles named in text. Does not judge other copy."""
    reasons = []
    for raw in handles_in_text(text):
        if classify_handle(raw) != "deny":
            continue
        msg = denial_message(raw)
        if msg not in reasons:
            reasons.append(msg)
    return reasons


def iter_structured_handles(obj, in_product=False):
    """Product-target fields. A page slug or root ``handle`` is not a product target."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                if key in _PRODUCT_FIELDS or key == "product" or (key == "handle" and in_product):
                    yield value
            elif isinstance(value, (dict, list)):
                yield from iter_structured_handles(value, in_product or key == "product")
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_structured_handles(item, in_product)


def spec_target_violations(spec):
    """Denied AgeAura handles a landing spec targets. No network."""
    if isinstance(spec, str):
        return text_target_violations(spec)
    reasons = text_target_violations(json.dumps(spec))
    seen = set(reasons)
    for raw in iter_structured_handles(spec):
        if classify_handle(raw) != "deny":
            continue
        msg = denial_message(raw)
        if msg not in seen:
            reasons.append(msg)
            seen.add(msg)
    return reasons


def article_link_allowed(handle):
    """False for a blog link that is a denied AgeAura product or names Urolithin.

    Ordinary article slugs that merely start with a brand word stay allowed.
    ``urolithin-a-old-page`` is not allowed. ``ageaura-nmn-listicle-261008`` is
    a campaign slug, not a product handle, and stays allowed.
    """
    h = normalize_handle(handle)
    if not h:
        return True
    if "urolithin" in h:
        return False
    if h in DENIED_HANDLES:
        return False
    if h.startswith("ageaura-pure-") or (
        h.startswith("ageaura-") and re.search(r"peptide|duo|bundle", h)
    ):
        return classify_handle(h) != "deny"
    return True


def asset_path_allowed(path):
    """False when a pack-shot path is the Urolithin bottle or another AgeAura SKU."""
    base = os.path.basename(path or "").lower()
    if "urolithin" in base:
        return False
    if "ageaura" not in base:
        return True
    stem = ASSET_SUFFIX.sub("", base.split(".")[0])
    if stem == HANDLE or stem.startswith(HANDLE):
        return True
    if stem.startswith("ageaura-pure-") or "urolithin" in stem:
        return product_allowed(stem)
    return True


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if "--brief" in argv:
        print(BRIEF)
        return 0
    if "--handle" in argv:
        idx = argv.index("--handle")
        if idx + 1 >= len(argv):
            print("ageaura_rules: --handle needs a product handle")
            return 2
        try:
            print(require_target(argv[idx + 1]))
            return 0
        except AgeAuraProductError as exc:
            print("✗ " + str(exc))
            return 1
    if len(args) != 1:
        print(__doc__.strip())
        return 2
    arg = args[0]
    raw = open(arg, encoding="utf-8").read() if os.path.isfile(arg) else arg
    bad = spec_target_violations(json.loads(raw)) if "--spec" in argv else text_target_violations(raw)
    for reason in bad:
        print("✗ " + reason)
    print("ageaura_rules: %d violation(s)" % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

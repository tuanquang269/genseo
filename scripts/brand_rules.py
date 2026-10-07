"""Store-wide link rules (Kevin 2026-10-07): AgeAura = NMN + TMG NAD+ Complex ONLY.
No other AgeAura product (p2 / Rejuvenation Duo, Essential Longevity Duo, ...), no /collections/ageaura,
no Urolithin. Used by validate_article.py (hard FAIL), the ticket builders, and lint_tickets.py."""
import re
AGEAURA_OK = "ageaura-pure-nmn-tmg-nad-complex"
_BANNED = [
    (re.compile(r'/products/(ageaura[a-z0-9-]*)', re.I), lambda m: m.group(1).lower() != AGEAURA_OK,
     "AgeAura product other than the NMN + TMG NAD+ Complex"),
    (re.compile(r'/collections/ageaura\b', re.I), lambda m: True, "/collections/ageaura"),
    (re.compile(r'urolithin', re.I), lambda m: True, "Urolithin"),
]
_URL = re.compile(r'https?://\S+|/blogs/[a-z0-9/-]+|\]\([^)]*\)|(?:src|href)=["\'][^"\']*["\']', re.I)
def violations(text):
    out = []
    text = text or ""
    for rx, bad, why in _BANNED:
        # Urolithin: visible text only (legacy handles keep the word in their URLs)
        src = _URL.sub(" ", text) if why == "Urolithin" else text
        for m in rx.finditer(src):
            if bad(m): out.append(f"{why}: {m.group(0)}")
    return sorted(set(out))
def product_allowed(handle):
    h = (handle or "").lower()
    return not (h.startswith("ageaura") and h != AGEAURA_OK) and "urolithin" not in h
def collection_allowed(handle):
    return (handle or "").lower() != "ageaura"

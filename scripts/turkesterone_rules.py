#!/usr/bin/env python3
"""Turkesterone Advanced Formula pack-label guard.

The pack-label whitelist is the source of truth for this one product:

    product_refs/turkesterone-advanced-formula.label.json

Copy that names Turkesterone Advanced Formula, Premium Turkesterone,
Turkesterone Advanced, or this SKU may repeat the required and optional lines.
The capsule badge was OCR'd as the separate lines "60" and "Capsules". Those
two lines are the capsule count. Copy may not state a milligram amount, a
serving count, a different capsule count, a day-supply, or any other dose
those lines do not contain. The file's source note is provenance, not a
whitelist. Bare "turkesterone" (the ingredient, including a trial dose) is out
of scope. Premium Himalayan Shilajit Gummies, Shilajit Shockwave, Pure Shilajit
Gold Resin, ShilaSource resin, AgeAura, and FloraFresh are different products
and are out of scope.

Dose phrases are read from the whitelist lines. Nothing in this module
hard-codes an allowed milligram, capsule count, or serving count.

brand_rules.assess() merges these violations. Landing specs go through
brand_rules.spec_violations().

  python3 scripts/turkesterone_rules.py --brief
  python3 scripts/turkesterone_rules.py "<text>" | <file>
  python3 scripts/turkesterone_rules.py --spec landing_drafts/<slug>.json
"""
import html
import json
import os
import re
import sys

HANDLE = "turkesterone-advanced-formula"
PRODUCT_URL = "https://wellnessnest.co/products/" + HANDLE
PRODUCT_NAME = "Turkesterone Advanced Formula"
LABEL_REL = "product_refs/" + HANDLE + ".label.json"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABEL_PATH = os.path.join(ROOT, LABEL_REL)
CODE = "turkesterone-label"

_PREFIX = "Turkesterone label: "


# Full product name, the front title "Premium Turkesterone", "Turkesterone Advanced",
# and the hyphenated handle. Bare "turkesterone" is the ingredient and is not this SKU.
_NAMED = re.compile(
    r"\b(?:premium\s+)?turkesterone\s+advanced(?:\s+formula)?\b"
    r"|\bpremium\s+turkesterone\b",
    re.I,
)
_PRODUCT_REF = re.compile(
    r"(?:https?://[^\s\"'<>()]*?)?/?\bproducts/" + re.escape(HANDLE)
    + r"(?:\.js(?:on)?|\.oembed)?(?:\?[^\s\"'<>()]*)?(?:#[^\s\"'<>()]*)?"
    r"|\b" + re.escape(HANDLE) + r"\b(?:-(?:cutout|label|ref|pack))?(?:\.(?:png|jpe?g|webp|json))?",
    re.I,
)
_ROW_TAG = re.compile(r"</?(?:tr|table|thead|tbody|tfoot)\b[^>]*>", re.I)
_CELL_TAG = re.compile(r"</?(?:td|th)\b[^>]*>", re.I)
_BLOCK_TAG = re.compile(
    r"</?(?:p|div|li|ul|ol|h[1-6]|br|hr|section|article|blockquote|figure|figcaption)\b[^>]*>",
    re.I,
)
_TAG = re.compile(r"<[^>]+>")
_PATHISH = re.compile(
    r"https?://\S+|\]\([^)]*\)|`[^`]+`"
    r"|(?<![\w.])/(?:blogs|collections|products|pages|policies|cdn|files)/[^\s\"'<>()`]*"
    r"|\b(?:tmp_images|product_refs|landing_drafts|published_drafts|logs|state|templates|scripts)/[^\s\"'<>()`]*"
    r"|[\w.~-]+\.(?:png|jpe?g|webp|gif|svg|json|md|csv|js|py|txt)\b",
    re.I,
)
_SLUG = re.compile(r"\b[a-z0-9]+(?:-[a-z0-9]+){3,}\b")
_CLAUSE_END = re.compile(r"[.!?]+(?=[\s\"')\]*_]|$)|[;\n\r\t]")
_NEG_CUE = re.compile(
    r"\b(?:not|no|never|without|nor|neither|none|isn't|aren't|doesn't|don't|didn't|won't|"
    r"cannot|can't|do\s+not|instead\s+of|rather\s+than|unlike|versus|\bvs\b|"
    r"wrong|incorrect|outdated|avoid|omit(?:ted)?|drop(?:ped)?|remov(?:e|ed))\b",
    re.I,
)
_NEG_BREAK = re.compile(r"\b(?:but|however|yet|although|though|while|whereas)\b", re.I)
_OTHER = re.compile(
    r"\b(?:other\s+brands?|another\s+brand|competitors?|brand\s+[a-z0-9]+|"
    r"florafresh|fusiforce|ageaura|menomate|shilasource|"
    r"shockwave|gummies|gold\s+resin|nmn|tmg|ecdysterone|tribulus)\b",
    re.I,
)
_CARRY = re.compile(
    r"^[\s\"'(*_-]*(?:it|its|it's|they|their|"
    r"the\s+(?:jar|tub|bottle|pack|label|serving|dose|formula)|"
    r"each\s+(?:jar|tub|serving|dose|capsule)|"
    r"this\s+(?:jar|tub|product|formula)|"
    r"a\s+serving|per\s+serving)\b",
    re.I,
)
_DOSE_LEAD = re.compile(
    r"^[\s\"'(*_-]*(?:\d+(?:\.\d+)?|one|two|three|five|ten|thirty|fifty|sixty|ninety)\b",
    re.I,
)
_STUDY = re.compile(
    r"\b(?:trials?|stud(?:y|ies|ied)|placebo|randomis(?:e|ed)|randomiz(?:e|ed)|"
    r"volunteers?|participants?|cohort|meta-analys\w*|et\s+al)\b",
    re.I,
)
_NUM = r"(?<![\w.,])(?P<n>\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)"
_MG = re.compile(_NUM + r"\s*-?\s*(?:mg|milligrams?)\b", re.I)
_MCG = re.compile(_NUM + r"\s*-?\s*(?:mcg|μg|µg|micrograms?)\b", re.I)
_GRAM = re.compile(_NUM + r"\s*-?\s*(?:grams?|g)\b", re.I)
_ML = re.compile(_NUM + r"\s*-?\s*(?:ml|millilit(?:er|re)s?)\b", re.I)
_FLOZ = re.compile(_NUM + r"\s*-?\s*(?:fl\.?\s*oz|fluid\s+ounces?)\b", re.I)
_OZ = re.compile(_NUM + r"\s*-?\s*oz\b", re.I)
_IU = re.compile(_NUM + r"\s*-?\s*iu\b", re.I)
_DROPS = re.compile(_NUM + r"\s*-?\s*(?:drops?|droppers?)\b", re.I)
_SERVINGS = re.compile(_NUM + r"\s*-?\s*servings?\b", re.I)
_WORD_NUM = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "ten": "10", "fifteen": "15", "twenty": "20", "thirty": "30", "forty": "40",
    "fifty": "50", "sixty": "60", "seventy": "70", "seventy five": "75",
    "eighty": "80", "ninety": "90", "hundred": "100",
}
_WORD_KEY = (
    r"seventy[\s-]+five|one|two|three|four|five|ten|fifteen|twenty|thirty|"
    r"forty|fifty|sixty|seventy|eighty|ninety|hundred"
)
_WORD_SERVINGS = re.compile(
    r"\b(?P<w>" + _WORD_KEY + r")\s*-?\s*servings?\b",
    re.I,
)
_SERVINGS_REV = re.compile(
    r"\bservings?\s+per\s+(?:container|pouch|pack|bottle|jar|tub|box)\s*[:#]?\s*(?P<n>\d{1,4})\b",
    re.I,
)
_DAY = re.compile(_NUM + r"\s*-?\s*day\s+supply\b", re.I)
_DAY_WORD = re.compile(
    r"\b(?P<w>thirty|sixty|ninety)\s*-?\s*day\s+supply\b",
    re.I,
)
_GUMMIES = re.compile(_NUM + r"\s*-?\s*gumm(?:y|ies)\b", re.I)
_CFU = re.compile(
    r"(?<![\w.,])(?P<n>\d+(?:\.\d+)?)\s*-?\s*(?:billion|million|bn)?\s*-?\s*cfus?\b"
    r"|\b(?P<w>one|two|fifteen)\s+billion\s+cfus?\b",
    re.I,
)
_MG_WORD = re.compile(
    r"\b(?P<w>one|two|three|four|five|ten|twenty|thirty|fifty|five\s+hundred|"
    r"two\s+hundred(?:\s+and\s+fifty)?)\s+milligrams?\b",
    re.I,
)
_ML_WORD = re.compile(
    r"\b(?P<w>one|two|ten|thirty)\s+millilit(?:er|re)s?\b",
    re.I,
)
_FLOZ_WORD = re.compile(
    r"\b(?P<w>one|two)\s+(?:fl\.?\s*oz|fluid\s+ounces?)\b",
    re.I,
)
_PCT = re.compile(
    r"(?<![\w.,])(?P<n>\d+(?:\.\d+)?)\s*%"
    r"|(?:standardiz(?:ed|ation)|extract|fulvic|purity)\s*(?:of\s+|to\s+|at\s+)?"
    r"(?P<n2>\d+(?:\.\d+)?)\s*%",
    re.I,
)
_CAPSULES = re.compile(
    _NUM + r"\s*-?\s*(?P<u>capsules?|caps?|caplets?|softgels?|tablets?)\b",
    re.I,
)
_WORD_CAPSULES = re.compile(
    r"\b(?P<w>" + _WORD_KEY + r")\s*-?\s*(?P<u>capsules?|caps?|caplets?|softgels?|tablets?)\b",
    re.I,
)
_CAPSULES_REV = re.compile(
    r"\b(?P<u>capsules?|caps?|caplets?|softgels?|tablets?)\s+per\s+"
    r"(?:container|bottle|jar|tub|pack)\s*[:#]?\s*(?P<n>\d{1,4})\b",
    re.I,
)
_COUNT = re.compile(_NUM + r"\s*-?\s*counts?\b", re.I)
_BARE_NUM = re.compile(r"^\d{1,4}$")
_CAPSULES_ONLY = re.compile(r"^capsules?$", re.I)

_SKIP_KEYS = frozenset((
    "url", "href", "image", "images", "pack_images", "avatar", "reference", "handle", "slug",
    "template", "template_suffix", "engine", "created", "store", "posture", "style", "icon",
    "kind", "image_note", "sources", "focal_y",
))
_ATTR_KEYS = frozenset(("product", "offer", "sticky_cta", "trust", "chip", "bullets", "product_bullets"))


def load_label():
    """Whitelist lines from required + optional, or None when that list is missing or empty.

    The file's source note is provenance. It is not a whitelist line, so an omitted
    misread in that note does not become an allowed dose.
    """
    try:
        with open(LABEL_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    tokens = [str(x).strip() for x in (data.get("required") or []) + (data.get("optional") or [])]
    tokens = [t for t in tokens if t]
    return tokens or None


def _joined_label():
    tokens = load_label()
    return ", ".join(tokens) if tokens else ""


LABEL_LINE = _joined_label()
TICKET_LINE = (
    "**Turkesterone Advanced Formula pack label (source of truth):** " + LABEL_LINE + ". "
    "No milligram amount and no Supplement Facts panel were read. Do not add one. "
    "The capsule badge is the separate lines in " + LABEL_REL + ". "
    "Do not state a milligram amount, a serving count, a different capsule count, or a day-supply."
)
LANDING_NOTE = (
    "pack label: " + LABEL_LINE + " (" + LABEL_REL + "); no milligram amount and no Supplement Facts "
    "panel in that file; do not state a serving count, a different capsule count, or a day-supply"
)


def _capsule_unit(word):
    w = (word or "").lower()
    if w.startswith("caplet"):
        return "caplets"
    if w.startswith("softgel"):
        return "softgels"
    if w.startswith("tablet"):
        return "tablets"
    if w in ("cap", "caps"):
        return "capsules"
    return "capsules"


def allowed_phrases(tokens):
    """Canonical dose phrases parsed from the whitelist lines themselves.

    A capsule badge that OCR split into a bare number line and a capsules-only
    line is one capsule count. No other number is joined to that word.
    """
    found = []
    for line in tokens or []:
        for _match, phrase in _dose_hits(line):
            if phrase not in found:
                found.append(phrase)
    capsules_word = False
    bare = []
    for line in tokens or []:
        stripped = (line or "").strip()
        if _CAPSULES_ONLY.fullmatch(stripped):
            capsules_word = True
        elif _BARE_NUM.fullmatch(stripped):
            phrase = _num(stripped) + " capsules"
            if phrase not in bare:
                bare.append(phrase)
    if capsules_word:
        for phrase in bare:
            if phrase not in found:
                found.append(phrase)
    return found


def in_scope(text):
    """True when the text names this SKU, not every mention of the ingredient."""
    text = text or ""
    return bool(_NAMED.search(text) or _PRODUCT_REF.search(text))


def violations(text, tokens=None):
    """Dose claims the whitelist does not support. [] when this SKU is not named."""
    text = text or ""
    if not in_scope(text):
        return []
    if tokens is None:
        tokens = load_label()
    if not tokens:
        return [_PREFIX + "pack label whitelist is missing or empty (" + LABEL_REL + ")"]
    return _scan(_visible(text), set(allowed_phrases(tokens)), attributed=False)


def spec_violations(spec, tokens=None):
    """violations() for a landing spec, field by field.

    Provenance notes (source, *_source, image_note) and the citation list are skipped.
    Strings under product / offer / sticky_cta / trust, and chip / bullets, count even
    when that string does not repeat the product name. chart.source is checked.
    """
    if not in_scope(json.dumps(spec, ensure_ascii=False)):
        return []
    if tokens is None:
        tokens = load_label()
    if not tokens:
        return [_PREFIX + "pack label whitelist is missing or empty (" + LABEL_REL + ")"]
    allowed = set(allowed_phrases(tokens))
    out = []
    for path, text, attributed in _spec_texts(spec, "", None, False):
        for reason in _scan(_visible(text), allowed, attributed):
            out.append(reason + " (" + path + ")")
    return _dedupe(out)


def _spec_texts(node, path, parent, attributed):
    if isinstance(node, dict):
        own = []
        for key, value in node.items():
            if _skip(key, parent):
                continue
            sub = path + "." + str(key) if path else str(key)
            attr = attributed or key in _ATTR_KEYS
            if isinstance(value, str) or (isinstance(value, list) and value
                                          and all(isinstance(x, str) for x in value)):
                strings = [value] if isinstance(value, str) else value
                if attr == attributed:
                    own.extend(strings)
                else:
                    yield sub, "\n".join(strings), attr
            elif isinstance(value, (dict, list)):
                for item in _spec_texts(value, sub, key, attr):
                    yield item
        if own:
            yield path or "spec", "\n".join(own), attributed
    elif isinstance(node, list):
        for i, value in enumerate(node):
            sub = "%s[%d]" % (path, i)
            if isinstance(value, str):
                yield sub, value, attributed
            elif isinstance(value, (dict, list)):
                for item in _spec_texts(value, sub, parent, attributed):
                    yield item


def _skip(key, parent):
    k = str(key).lower()
    if k == "source":
        return parent != "chart"
    return k in _SKIP_KEYS or k.endswith("_source")


def _visible(text):
    t = (text or "").replace("\u2019", "'").replace("\u2018", "'").replace("\u00a0", " ")
    t = t.replace("\u2010", "-").replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    t = _PRODUCT_REF.sub(" " + PRODUCT_NAME + " ", t)
    t = _ROW_TAG.sub(" \n ", t)
    t = _CELL_TAG.sub(" | ", t)
    t = _BLOCK_TAG.sub(" \n ", t)
    t = _TAG.sub(" ", t)
    t = html.unescape(t)
    t = _PATHISH.sub(" ", t)
    t = _SLUG.sub(" ", t)
    return t


def _clauses(visible):
    out, start = [], 0
    for match in _CLAUSE_END.finditer(visible):
        if match.start() > start:
            out.append((start, match.start(), match.group(0)))
        start = match.end()
    if start < len(visible):
        out.append((start, len(visible), ""))
    return out


def _negated(clause, start):
    pre = clause[max(0, start - 100):start]
    cues = list(_NEG_CUE.finditer(pre))
    if cues and not _NEG_BREAK.search(pre, cues[-1].end()):
        return True
    return False


def _other_only(clause):
    return bool(_OTHER.search(clause)) and not _NAMED.search(clause)


def _owned(clause, attributed, carried):
    return attributed or carried or bool(_NAMED.search(clause))


def _keep(clause, start, owned, studyish):
    """A dose match counts unless it is negated, another brand's clause, or an unowned study dose."""
    if _negated(clause, start) or _other_only(clause):
        return False
    if owned:
        return True
    if studyish:
        return False
    return True


def _num(raw):
    n = (raw or "").replace(",", "")
    if "." in n:
        whole, frac = n.split(".", 1)
        frac = frac.rstrip("0")
        whole = str(int(whole or "0"))
        return whole if not frac else whole + "." + frac
    return str(int(n))


def _word_num(raw):
    key = re.sub(r"[\s-]+", " ", (raw or "").lower()).strip()
    return _WORD_NUM[key]


def _dose_hits(clause):
    """(match, canonical phrase) for every dose token in clause."""
    hits = []
    for match in _MG.finditer(clause):
        hits.append((match, _num(match.group("n")) + " mg"))
    for match in _MG_WORD.finditer(clause):
        hits.append((match, re.sub(r"\s+", " ", match.group(0).strip())))
    for match in _MCG.finditer(clause):
        hits.append((match, _num(match.group("n")) + " mcg"))
    for match in _GRAM.finditer(clause):
        hits.append((match, _num(match.group("n")) + " g"))
    for match in _ML.finditer(clause):
        hits.append((match, _num(match.group("n")) + " ml"))
    for match in _ML_WORD.finditer(clause):
        hits.append((match, re.sub(r"\s+", " ", match.group(0).strip())))
    for match in _FLOZ.finditer(clause):
        hits.append((match, _num(match.group("n")) + " fl oz"))
    for match in _FLOZ_WORD.finditer(clause):
        hits.append((match, re.sub(r"\s+", " ", match.group(0).strip())))
    for match in _OZ.finditer(clause):
        if _FLOZ.search(clause, match.start(), match.end() + 1):
            continue
        hits.append((match, _num(match.group("n")) + " oz"))
    for match in _IU.finditer(clause):
        hits.append((match, _num(match.group("n")) + " IU"))
    for match in _DROPS.finditer(clause):
        unit = "dropper" if "dropper" in match.group(0).lower() else "drops"
        hits.append((match, _num(match.group("n")) + " " + unit))
    for match in _SERVINGS.finditer(clause):
        hits.append((match, _num(match.group("n")) + " servings"))
    for match in _WORD_SERVINGS.finditer(clause):
        hits.append((match, _word_num(match.group("w")) + " servings"))
    for match in _SERVINGS_REV.finditer(clause):
        hits.append((match, _num(match.group("n")) + " servings"))
    for match in _DAY.finditer(clause):
        hits.append((match, _num(match.group("n")) + "-day supply"))
    for match in _DAY_WORD.finditer(clause):
        hits.append((match, _word_num(match.group("w")) + "-day supply"))
    for match in _GUMMIES.finditer(clause):
        hits.append((match, _num(match.group("n")) + " gummies"))
    for match in _CFU.finditer(clause):
        hits.append((match, re.sub(r"\s+", " ", match.group(0).strip())))
    for match in _PCT.finditer(clause):
        n = match.group("n") or match.group("n2")
        hits.append((match, _num(n) + "%"))
    for match in _CAPSULES.finditer(clause):
        hits.append((match, _num(match.group("n")) + " " + _capsule_unit(match.group("u"))))
    for match in _WORD_CAPSULES.finditer(clause):
        hits.append((match, _word_num(match.group("w")) + " " + _capsule_unit(match.group("u"))))
    for match in _CAPSULES_REV.finditer(clause):
        hits.append((match, _num(match.group("n")) + " " + _capsule_unit(match.group("u"))))
    for match in _COUNT.finditer(clause):
        hits.append((match, _num(match.group("n")) + " count"))
    return hits


def _scan(visible, allowed, attributed):
    reasons = []
    prev_named, prev_delim, prev_window = False, "", ""
    for start, end, delim in _clauses(visible):
        clause = visible[start:end]
        if not clause.strip():
            prev_delim = delim
            continue
        carried = attributed or (prev_named and (
            prev_delim == ":" or bool(_CARRY.match(clause)) or bool(_DOSE_LEAD.match(clause))))
        owned = _owned(clause, attributed, carried)
        studyish = bool(_STUDY.search(prev_window[-180:] + " " + clause))
        _check_clause(clause, allowed, owned, studyish, reasons)
        prev_named = bool(_NAMED.search(clause)) or carried
        prev_delim = delim
        prev_window = (prev_window + " " + clause)[-240:]
    return _dedupe(reasons)


def _check_clause(clause, allowed, owned, studyish, reasons):
    for match, phrase in _dose_hits(clause):
        if not _keep(clause, match.start(), owned, studyish):
            continue
        if phrase in allowed:
            continue
        reasons.append(_PREFIX + phrase + " is not on the pack label whitelist")


def _dedupe(items):
    out = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if "--brief" in argv:
        print(TICKET_LINE)
        return 0
    if len(args) != 1:
        print(__doc__.strip())
        return 2
    arg = args[0]
    raw = open(arg, encoding="utf-8").read() if os.path.isfile(arg) else arg
    if "--spec" in argv:
        bad = spec_violations(json.loads(raw))
    else:
        bad = violations(raw)
    for reason in bad:
        print("x " + reason)
    print("turkesterone_rules: %d violation(s)" % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

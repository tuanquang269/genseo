#!/usr/bin/env python3
"""Premium Himalayan Shilajit Gummies pack-label guard (Kevin 2026-10-10).

The pack-label whitelist is the source of truth for this one product:

    product_refs/premium-himalayan-shilajit-gummies.label.json

That file's optional lines include "60 GUMMIES", "60-DAY SUPPLY", and
"1500mg Shilajit". They do not include a 30-serving panel, a 2-gummy serving,
or a 150 mg extract line. Copy that names this product may say 60 gummies and
a 60-day supply, and a milligram amount only when that exact token is in the
file. Shockwave, Gold Resin, and ShilaSource resin are different products and
are out of scope.

brand_rules.assess() merges these violations. Landing specs go through
brand_rules.spec_violations(). Keep the whitelist in the label file; do not
copy dose tokens into this module.

  python3 scripts/shilajit_gummies_rules.py --brief
  python3 scripts/shilajit_gummies_rules.py "<text>" | <file>
  python3 scripts/shilajit_gummies_rules.py --spec landing_drafts/<slug>.json
"""
import html
import json
import os
import re
import sys

HANDLE = "premium-himalayan-shilajit-gummies"
PRODUCT_URL = "https://wellnessnest.co/products/" + HANDLE
PRODUCT_NAME = "Premium Himalayan Shilajit Gummies"
LABEL_REL = "product_refs/" + HANDLE + ".label.json"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABEL_PATH = os.path.join(ROOT, LABEL_REL)

_PREFIX = "Shilajit gummies label: "
LABEL_LINE = PRODUCT_NAME + ", 60 gummies, 60-day supply"
TICKET_LINE = (
    "**Shilajit gummies pack label (source of truth):** " + LABEL_LINE + ". "
    "The whitelist does not include a 30-serving panel. Do not add a serving count or a milligram "
    "amount unless that exact token is in the file. File: " + LABEL_REL + "."
)
LANDING_NOTE = (
    "pack label: 60 gummies, 60-day supply (" + LABEL_REL + "); no 30-serving panel and no milligram "
    "amount beyond that file"
)

_PRODUCT = re.compile(
    r"premium[\s_-]+himalayan[\s_-]+shilajit[\s_-]+gummies"
    r"|\b" + re.escape(HANDLE) + r"\b",
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
    r"florafresh|fusiforce|ageaura|turkesterone|menomate|shockwave|"
    r"gold\s+resin|shilasource)\b",
    re.I,
)
_CARRY = re.compile(
    r"^[\s\"'(*_-]*(?:it|its|it's|they|the\s+(?:pouch|pack|label|count|gumm(?:y|ies))|"
    r"each\s+(?:pouch|pack|serving)|this\s+(?:pouch|pack))\b",
    re.I,
)
_STUDY = re.compile(
    r"\b(?:trials?|stud(?:y|ies|ied)|placebo|randomis(?:e|ed)|randomiz(?:e|ed)|"
    r"volunteers?|participants?|cohort|meta-analys\w*|et\s+al)\b",
    re.I,
)
_WORD_NUM = {"two": 2, "three": 3, "four": 4, "thirty": 30, "sixty": 60, "ninety": 90}
_PACK = re.compile(
    r"(?<![\d.,])(?P<n>\d{1,4})\s*-?\s*(?P<unit>gummies|gummy\s+count|counts?|ct)\b",
    re.I,
)
_WORD_PACK = re.compile(
    r"\b(?P<w>two|three|four|thirty|sixty|ninety)\s*-?\s*(?P<unit>gummies|counts?)\b",
    re.I,
)
_SERVINGS = re.compile(r"(?<![\d.,])(?P<n>\d{1,4})\s*-?\s*servings?\b", re.I)
_WORD_SERVINGS = re.compile(r"\b(?P<w>thirty|sixty|ninety)\s*-?\s*servings?\b", re.I)
_SERVINGS_REV = re.compile(
    r"\bservings?\s+per\s+(?:container|pouch|pack|bottle|jar)\s*[:#]?\s*(?P<n>\d{1,4})\b",
    re.I,
)
_PER_SERVING = re.compile(
    r"\bper\s+(?P<n>\d{1,2})\s*-?\s*gumm(?:y|ies)\b"
    r"|(?<![\d.,])(?P<n2>\d{1,2})\s*-?\s*gummies?\s+per\s+serving\b"
    r"|(?<![\d.,])(?P<n3>\d{1,2})\s*-?\s*gummy\s+serving\b"
    r"|(?<![\d.,])(?P<n4>\d{1,2})\s*-?\s*gummies?\s+(?:a|per)\s+day\b",
    re.I,
)
_DAY = re.compile(r"(?<![\d.,])(?P<n>\d{1,3})\s*-?\s*day\s+supply\b", re.I)
_MG = re.compile(r"(?<![\d.,])(?P<n>\d{1,3}(?:,\d{3})+|\d{1,5})\s*-?\s*mg\b", re.I)
_PER_SERVING_TAIL = re.compile(r"^\s*(?:per|/|a|each)\s+serving\b", re.I)
_PER_DAY_TAIL = re.compile(r"^\s*(?:a|per)\s+day\b", re.I)
_GUMMY_LINE = re.compile(r"(?<![\d.])(\d+)\s*-?\s*gummies?\b", re.I)
_DAY_LINE = re.compile(r"(?<![\d.])(\d+)\s*-?\s*day\s+supply\b", re.I)

_SKIP_KEYS = frozenset((
    "url", "href", "image", "images", "pack_images", "avatar", "reference", "handle", "slug",
    "template", "template_suffix", "engine", "created", "store", "posture", "style", "icon",
    "kind", "image_note", "sources", "focal_y",
))
_PRODUCT_BLOCKS = frozenset(("product", "offer", "sticky_cta", "trust"))
_ATTR_KEYS = frozenset(("product", "offer", "sticky_cta", "trust", "chip", "bullets", "product_bullets"))


def load_label():
    """Whitelist lines, or None when the pack label file is missing or empty."""
    try:
        with open(LABEL_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    tokens = [str(x).strip() for x in (data.get("required") or []) + (data.get("optional") or [])]
    tokens = [t for t in tokens if t]
    return tokens or None


def gummy_counts(tokens):
    """Pack counts written as 'N gummies' on a whitelist line. Bare integers are not a count."""
    found = []
    for line in tokens or []:
        for match in _GUMMY_LINE.finditer(line):
            found.append(int(match.group(1)))
    return sorted(set(found))


def day_supplies(tokens):
    """Day-supply counts written on a whitelist line ('60-DAY SUPPLY')."""
    found = []
    for line in tokens or []:
        for match in _DAY_LINE.finditer(line):
            found.append(int(match.group(1)))
    return sorted(set(found))


def listed(phrase, tokens):
    """True when phrase appears in a whitelist line, not as a suffix of a longer number."""
    want = re.sub(r"[^a-z0-9]", "", (phrase or "").lower())
    if not want:
        return False
    for line in tokens or []:
        norm = re.sub(r"[^a-z0-9]", "", line.lower())
        start = 0
        while True:
            i = norm.find(want, start)
            if i < 0:
                break
            before = norm[i - 1] if i else ""
            if not before.isdigit():
                return True
            start = i + 1
    return False


def in_scope(text):
    """True when the text names this product (full name or handle), not every shilajit SKU."""
    return bool(_PRODUCT.search(text or ""))


def violations(text, tokens=None):
    """Pack-label claims the whitelist does not support. [] when this product is not named."""
    text = text or ""
    if not in_scope(text):
        return []
    if tokens is None:
        tokens = load_label()
    if not tokens:
        return [_PREFIX + "pack label whitelist is missing or empty (" + LABEL_REL + ")"]
    return _scan(_visible(text), tokens, attributed=False)


def spec_violations(spec, tokens=None):
    """violations() for a landing spec, field by field.

    Provenance notes (source, *_source, image_note) and the citation list are skipped.
    Strings under product / offer / sticky_cta / trust, and chip / bullets, count even
    when that string does not repeat the product name.
    """
    if not in_scope(json.dumps(spec, ensure_ascii=False)):
        return []
    if tokens is None:
        tokens = load_label()
    if not tokens:
        return [_PREFIX + "pack label whitelist is missing or empty (" + LABEL_REL + ")"]
    out = []
    for path, text, attributed in _spec_texts(spec, "", None, False):
        for reason in _scan(_visible(text), tokens, attributed):
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
    return bool(_OTHER.search(clause)) and not _PRODUCT.search(clause)


def _owned(clause, attributed, carried):
    return attributed or carried or bool(_PRODUCT.search(clause))


def _hit(clause, start, owned):
    """A pack-count match counts unless it is negated or the clause is another brand."""
    if _negated(clause, start):
        return False
    if owned:
        return True
    return not _other_only(clause)


def _mg_listed(raw, tokens):
    plain = raw.replace(",", "")
    for phrase in (raw + " mg", plain + " mg", raw + "mg", plain + "mg"):
        if listed(phrase, tokens):
            return True
    return False


def _serving_listed(n, tokens):
    text = str(n)
    return (listed(text + " servings", tokens) or listed(text + " serving", tokens)
            or listed(text + "-serving", tokens))


def _scan(visible, tokens, attributed):
    reasons = []
    counts = gummy_counts(tokens)
    days = day_supplies(tokens)
    prev_named, prev_delim, prev_window = False, "", ""
    for start, end, delim in _clauses(visible):
        clause = visible[start:end]
        if not clause.strip():
            prev_delim = delim
            continue
        carried = attributed or (prev_named and (prev_delim == ":" or bool(_CARRY.match(clause))))
        owned = _owned(clause, attributed, carried)
        _check_clause(clause, tokens, counts, days, owned, prev_window, reasons)
        prev_named = bool(_PRODUCT.search(clause)) or carried
        prev_delim = delim
        prev_window = (prev_window + " " + clause)[-240:]
    return _dedupe(reasons)


def _check_clause(clause, tokens, counts, days, owned, prev_window, reasons):
    label_count = ("%d gummies" % counts[0]) if len(counts) == 1 else (
        "no gummy count in the whitelist" if not counts else "or ".join("%d gummies" % n for n in counts))

    def pack_hit(start):
        return _hit(clause, start, owned)

    for match in list(_PACK.finditer(clause)) + list(_WORD_PACK.finditer(clause)):
        if not pack_hit(match.start()):
            continue
        if match.re is _WORD_PACK:
            n = _WORD_NUM[match.group("w").lower()]
            unit = match.group("unit")
        else:
            n = int(match.group("n"))
            unit = match.group("unit")
        tail = clause[match.end():match.end() + 24]
        per_serving = bool(_PER_SERVING_TAIL.match(tail))
        per_day = bool(_PER_DAY_TAIL.match(tail))
        if per_serving and (listed("%d gummies per serving" % n, tokens) or listed("%d-gummy serving" % n, tokens)):
            continue
        if per_day and (listed("%d gummies a day" % n, tokens) or listed("%d gummies per day" % n, tokens)):
            continue
        if not per_serving and not per_day and n in counts:
            continue
        if per_serving:
            what = "%d gummies per serving" % n
        elif per_day:
            what = "%d gummies a day" % n
        else:
            what = "%d %s" % (n, unit)
        reasons.append(_PREFIX + what + " is not the pack count (label: " + label_count + ")")
    for match in _PER_SERVING.finditer(clause):
        if not pack_hit(match.start()):
            continue
        n = match.group("n") or match.group("n2") or match.group("n3") or match.group("n4")
        if listed(n + " gummies per serving", tokens) or listed(n + "-gummy serving", tokens):
            continue
        if listed(n + " gummies a day", tokens) or listed(n + " gummies per day", tokens):
            continue
        reasons.append(_PREFIX + n + " gummies per serving is not on the pack label whitelist")
    for match in list(_SERVINGS.finditer(clause)) + list(_WORD_SERVINGS.finditer(clause)):
        if not pack_hit(match.start()):
            continue
        n = str(_WORD_NUM[match.group("w").lower()]) if match.re is _WORD_SERVINGS else match.group("n")
        if _serving_listed(n, tokens):
            continue
        reasons.append(_PREFIX + n + " servings is not on the pack label whitelist")
    for match in _SERVINGS_REV.finditer(clause):
        if not pack_hit(match.start()):
            continue
        n = match.group("n")
        if _serving_listed(n, tokens):
            continue
        reasons.append(_PREFIX + n + " servings is not on the pack label whitelist")
    for match in _DAY.finditer(clause):
        if not pack_hit(match.start()):
            continue
        n = int(match.group("n"))
        if n in days or listed("%d-day supply" % n, tokens) or listed("%d day supply" % n, tokens):
            continue
        label_day = ("%d-day supply" % days[0]) if len(days) == 1 else "no day-supply line in the whitelist"
        reasons.append(_PREFIX + ("%d-day supply" % n) + " is not the pack supply (label: " + label_day + ")")
    studyish = bool(_STUDY.search(prev_window[-180:] + " " + clause))
    for match in _MG.finditer(clause):
        if _negated(clause, match.start()) or _other_only(clause):
            continue
        raw = match.group("n")
        if _mg_listed(raw, tokens):
            continue
        if not owned and studyish:
            continue
        reasons.append(_PREFIX + raw + " mg is not on the pack label whitelist")


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
    print("shilajit_gummies_rules: %d violation(s)" % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

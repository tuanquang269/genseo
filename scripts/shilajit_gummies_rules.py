#!/usr/bin/env python3
"""Premium Himalayan Shilajit Gummies pack-label guard (Kevin 2026-10-10).

The pack-label whitelist is the source of truth for this one product:

    product_refs/premium-himalayan-shilajit-gummies.label.json

That file's optional lines include "60 GUMMIES", "60-DAY SUPPLY", and
"1500mg Shilajit". They do not include a 30-serving panel, a 2-gummy serving,
a 150 mg extract line, or a gram amount. Copy that names this product may say
60 gummies and a 60-day supply, and a milligram or gram amount only when that
exact token is in the file. Serving counts written as words are read, so
twenty servings, forty servings, and fifteen servings fail. The product is in
scope under the full name, "Himalayan Shilajit Gummies", "Shilajit Gummies"
(including "Shilajit Gummies for Men"), or the handle. A milligram or gram in
the sentence right after that name is still this product's dose, including
when the previous sentence says trial or studied, and including a follow-up
that does not start with It or pouch. A denial ends at "and" or a new delivery
verb, and bare "no" also ends at a comma. The Pandit pattern stays allowed:
"The Pandit trial used 250 mg ... Premium Himalayan Shilajit Gummies are 60
gummies" and the same dose after one buffer sentence. Shockwave, Gold Resin,
and ShilaSource resin are different products and are out of scope.

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
    r"|himalayan[\s_-]+shilajit[\s_-]+gumm(?:y|ies)"
    r"|\bshilajit[\s_-]+gumm(?:y|ies)\b"
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
# "and" or a new delivery verb ends any denial ("is not a stimulant and delivers
# 250 mg", "without fillers delivers 150 mg"). A comma ends bare "no"
# ("no fillers, 250 mg"). "no 250 mg" and "do not claim 150 mg" stay denials.
_NO_GAP = re.compile(
    r"\band\b"
    r"|(?:\w+\s+){1,8}(?:delivers?|provides?|contains?|includes?|lists?|has|have|gives?|adds?|offers?)\b",
    re.I,
)
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
_WORD_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
}
_TENS_RE = "ninety|eighty|seventy|sixty|fifty|forty|thirty|twenty"
_ONES_RE = (
    "nineteen|eighteen|seventeen|sixteen|fifteen|fourteen|thirteen|twelve|eleven|"
    "ten|nine|eight|seven|six|five|four|three|two|one|zero|hundred"
)
_UNIT_RE = "nine|eight|seven|six|five|four|three|two|one"
_SPELLED = (
    r"(?<![\w-])(?P<w>" + _TENS_RE + r"|" + _ONES_RE + r")"
    r"(?:[\s-]+(?P<u>" + _UNIT_RE + r"))?(?!\w)"
)
_PACK = re.compile(
    r"(?<![\d.,])(?P<n>\d{1,4})\s*-?\s*(?P<unit>gummies|gummy\s+count|counts?|ct)\b",
    re.I,
)
_WORD_PACK = re.compile(
    r"\b(?P<w>two|three|four|thirty|sixty|ninety)\s*-?\s*(?P<unit>gummies|counts?)\b",
    re.I,
)
_SERVINGS = re.compile(r"(?<![\d.,])(?P<n>\d{1,4})\s*-?\s*servings?\b", re.I)
_WORD_SERVINGS = re.compile(_SPELLED + r"\s*-?\s*servings?\b", re.I)
_GRAM = re.compile(
    r"(?<![\d.,])(?P<n>\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*-?\s*(?:grams?|g)\b",
    re.I,
)
_WORD_GRAM = re.compile(_SPELLED + r"\s*-?\s*(?:grams?|g)\b", re.I)
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
    """True when the text names this product, not every shilajit SKU.

    Full name, "Himalayan Shilajit Gummies", "Shilajit Gummies" (including
    "Shilajit Gummies for Men"), or the handle. Shockwave, Gold Resin, and
    ShilaSource resin do not match.
    """
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


def _spelled_number(match):
    """Integer for a spelled amount. twenty-five is 25. thirty alone is 30."""
    n = _WORD_NUM[match.group("w").lower()]
    unit = match.group("u")
    if unit and 20 <= n < 100 and n % 10 == 0:
        n += _WORD_NUM[unit.lower()]
    return n


def _negated(clause, start):
    """True when a denial cue governs this match.

    Any denial ends at "and" or a new delivery verb, so "is not a stimulant
    and delivers 250 mg" and "without fillers delivers 150 mg" still count.
    Bare "no" and "without" also end at a comma ("no fillers, 250 mg").
    "Do not claim 30 servings or 150 mg" stays a denial. "no 250 mg" stays a
    denial because nothing sits between the cue and the dose.
    """
    pre = clause[max(0, start - 100):start]
    cues = list(_NEG_CUE.finditer(pre))
    if not cues:
        return False
    last = cues[-1]
    if _NEG_BREAK.search(pre, last.end()):
        return False
    gap = pre[last.end():]
    if _NO_GAP.search(gap):
        return False
    if last.group(0).lower() in ("no", "without") and "," in gap:
        return False
    return True


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


def _gram_listed(plain, tokens):
    phrases = []
    for n in plain:
        phrases.extend((n + " g", n + "g", n + " gram", n + " grams"))
    return any(listed(phrase, tokens) for phrase in phrases)


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
        _check_clause(clause, tokens, counts, days, owned, prev_window, prev_named, reasons)
        prev_named = bool(_PRODUCT.search(clause)) or carried
        prev_delim = delim
        prev_window = (prev_window + " " + clause)[-240:]
    return _dedupe(reasons)


def _check_clause(clause, tokens, counts, days, owned, prev_window, prev_named, reasons):
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
        n = str(_spelled_number(match)) if match.re is _WORD_SERVINGS else match.group("n")
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
    for match in list(_GRAM.finditer(clause)) + list(_WORD_GRAM.finditer(clause)):
        if _negated(clause, match.start()) or _other_only(clause):
            continue
        if match.re is _WORD_GRAM:
            plain = str(_spelled_number(match))
            forms = (plain,)
        else:
            raw = match.group("n")
            plain = raw.replace(",", "")
            forms = (raw, plain)
        if _gram_listed(forms, tokens):
            continue
        # Same window as a milligram: a foreign study dose stays allowed.
        # "were studied. Participants took 0.25 g" does not. "0.25 g" in the
        # sentence before the product name does not either, unless that
        # sentence is the study dose (the Pandit shape).
        if not owned and studyish and not prev_named:
            continue
        reasons.append(_PREFIX + plain + " g is not on the pack label whitelist")
    for match in _MG.finditer(clause):
        if _negated(clause, match.start()) or _other_only(clause):
            continue
        raw = match.group("n")
        if _mg_listed(raw, tokens):
            continue
        # A foreign study dose stays allowed. The sentence right after this
        # product's name does not: "were studied. Participants took 250 mg."
        if not owned and studyish and not prev_named:
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

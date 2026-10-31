#!/usr/bin/env python3
"""FusiForce pack-label guard (Kevin 2026-10-09).

The pack-label whitelist is the source of truth:

    product_refs/fusiforce-creatine-gummies.label.json

That file's required lines include Creatine, Monohydrate, Gummies, and 90.
Kevin 2026-10-23 (vault note newer than the 2026-10-08 OCR) adds
vault_servings: 30 servings and 3 gummies per serving. Those lines are not a
second pack count. The file does not include 84, a milligram amount, or ginseng.
Copy that names FusiForce may say creatine monohydrate, 90 gummies, 30 servings,
and 3 gummies per serving. It may not state 84 gummies, 25 mg, 50 mg, 5,000 mg,
any other serving count, any milligram amount, or ginseng unless that exact
token is in the whitelist file.

brand_rules.assess() merges these violations. Landing specs go through
brand_rules.spec_violations(). Keep the whitelist in the label file; do not
copy dose tokens into this module.

  python3 scripts/fusiforce_rules.py --brief
  python3 scripts/fusiforce_rules.py "<text>" | <file>
  python3 scripts/fusiforce_rules.py --spec landing_drafts/<slug>.json
"""
import html
import json
import os
import re
import sys

HANDLE = "fusiforce-creatine-gummies"
PRODUCT_URL = "https://wellnessnest.co/products/" + HANDLE
PRODUCT_NAME = "FusiForce Creatine Monohydrate Gummies"
LABEL_REL = "product_refs/" + HANDLE + ".label.json"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABEL_PATH = os.path.join(ROOT, LABEL_REL)

_PREFIX = "FusiForce label: "
LABEL_LINE = "Creatine Monohydrate Gummies, 90 gummies, 30 servings (3 gummies per serving)"
TICKET_LINE = (
    "**FusiForce pack label (source of truth):** " + LABEL_LINE + ". "
    "Kevin 2026-10-23: write 90 gummies / 30 servings (3 gummies per serving). "
    "Do not state 84 gummies, 25 mg, 50 mg, 5,000 mg, or ginseng. "
    "File: " + LABEL_REL + "."
)
LANDING_NOTE = (
    "pack label: " + LABEL_LINE + " (" + LABEL_REL + "); no milligram amount and no ginseng "
    "beyond that file"
)

_FUSI = re.compile(r"fusi[\s_-]?force|\b" + re.escape(HANDLE) + r"\b", re.I)
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
    r"shilajit|ageaura|florafresh|turkesterone|menomate)\b",
    re.I,
)
_CARRY = re.compile(
    r"^[\s\"'(*_-]*(?:it|its|it's|they|the\s+(?:pouch|pack|label|count|tub|bottle|serving)|"
    r"each\s+(?:pouch|pack|serving)|this\s+(?:pouch|pack))\b",
    re.I,
)
_PACK = re.compile(
    r"(?<![\d.,])(?P<n>\d{1,4})\s*-?\s*(?P<unit>gummies|gummy\s+count|counts?|ct)\b",
    re.I,
)
_EIGHTY_FOUR = re.compile(r"\beighty[\s-]*four\b", re.I)
_EQ84 = re.compile(r"28\s*[x×*]\s*3\s*=\s*84\b", re.I)
_SERVINGS = re.compile(r"(?<![\d.,])(?P<n>\d{1,4})\s*-?\s*servings?\b", re.I)
_PER_SERVING = re.compile(
    r"serving\s*\(\s*(?P<n>\d{1,2})\s*gummies\s*\)"
    r"|(?<![\d.,])(?P<n2>\d{1,2})\s*-?\s*gummies?\s+per\s+serving\b"
    r"|(?<![\d.,])per\s+(?P<n3>\d{1,2})\s*-?\s*gumm(?:y|ies)\b"
    r"|(?<![\d.,])(?P<n4>\d{1,2})\s*-?\s*gummy\s+serving\b",
    re.I,
)
_MG = re.compile(r"(?<![\d.,])(?P<n>\d{1,3}(?:,\d{3})+|\d{1,5})\s*-?\s*mg\b", re.I)
_GINSENG = re.compile(r"\b(?P<w>panax|ginsenosides?|ginseng)\b", re.I)
_PER_SERVING_TAIL = re.compile(r"^\s*(?:per|/|a|each)\s+serving\b", re.I)

_SKIP_KEYS = frozenset((
    "url", "href", "image", "images", "pack_images", "avatar", "reference", "handle", "slug",
    "template", "template_suffix", "engine", "created", "store", "posture", "style", "icon",
    "kind", "image_note", "sources", "focal_y",
))
_PRODUCT_BLOCKS = frozenset(("product", "offer", "sticky_cta", "trust"))


def load_label():
    """Whitelist lines, or None when the pack label file is missing or empty."""
    try:
        with open(LABEL_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    vault = data.get("vault_servings") or {}
    extra = vault.get("lines") if isinstance(vault, dict) else []
    tokens = [
        str(x).strip()
        for x in (data.get("required") or []) + (data.get("optional") or []) + list(extra or [])
    ]
    tokens = [t for t in tokens if t]
    return tokens or None


def pack_count(tokens):
    """The single integer whitelist line, or None when the file does not name exactly one."""
    nums = []
    for line in tokens or []:
        if re.fullmatch(r"\d+", line.strip()):
            nums.append(int(line))
    if len(nums) == 1:
        return nums[0]
    return None


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
    """True when the text names FusiForce or the product handle."""
    return bool(_FUSI.search(text or ""))


def violations(text, tokens=None):
    """Pack-label claims the whitelist does not support. [] when FusiForce is not named."""
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
    Strings under product / offer / sticky_cta / trust count even when they do not repeat the brand.
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
            attr = attributed or (not path and key in _PRODUCT_BLOCKS)
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
    t = t.replace("\u2010", "-").replace("\u2011", "-").replace("\u00d7", "x")
    t = _PRODUCT_REF.sub(" FusiForce ", t)
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
    for m in _CLAUSE_END.finditer(visible):
        if m.start() > start:
            out.append((start, m.start(), m.group(0)))
        start = m.end()
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
    return bool(_OTHER.search(clause)) and not _FUSI.search(clause)


def _hit(clause, start, owned):
    """A match is in play unless it is negated or the clause is about another brand."""
    if _negated(clause, start):
        return False
    if owned:
        return True
    return not _other_only(clause)


def _scan(visible, tokens, attributed):
    reasons = []
    count = pack_count(tokens)
    prev_fusi, prev_delim = False, ""
    for s, e, delim in _clauses(visible):
        clause = visible[s:e]
        if not clause.strip():
            continue
        fusi = bool(_FUSI.search(clause))
        carried = attributed or (prev_fusi and (prev_delim == ":" or bool(_CARRY.match(clause))))
        owned = fusi or carried
        _check_clause(clause, tokens, count, owned, reasons)
        prev_fusi = fusi or carried
        prev_delim = delim
    return _dedupe(reasons)


def _check_clause(clause, tokens, count, owned, reasons):
    for m in _PACK.finditer(clause):
        if not _hit(clause, m.start(), owned):
            continue
        n = int(m.group("n"))
        tail = clause[m.end():m.end() + 24]
        per_serving = bool(_PER_SERVING_TAIL.match(tail))
        if per_serving or n != count:
            if per_serving and listed("%d gummies per serving" % n, tokens):
                continue
            if not per_serving and n == count:
                continue
            what = "%d gummies per serving" % n if per_serving else "%d %s" % (n, m.group("unit"))
            label = ("%d gummies" % count) if count else "no pack count in the whitelist"
            reasons.append(_PREFIX + what + " is not the pack count (label: " + label + ")")
    if _EIGHTY_FOUR.search(clause) and re.search(r"gumm|count|pouch|pack", clause, re.I):
        m = _EIGHTY_FOUR.search(clause)
        if _hit(clause, m.start(), owned):
            label = ("%d gummies" % count) if count else "no pack count in the whitelist"
            reasons.append(_PREFIX + "eighty-four gummies is not the pack count (label: " + label + ")")
    m = _EQ84.search(clause)
    if m and _hit(clause, m.start(), owned):
        reasons.append(_PREFIX + "28 x 3 = 84 is not the pack count (label: 90 gummies)")
    for m in _SERVINGS.finditer(clause):
        if not _hit(clause, m.start(), owned):
            continue
        n = m.group("n")
        if listed(n + " servings", tokens) or listed(n + " serving", tokens):
            continue
        reasons.append(_PREFIX + n + " servings is not on the pack label whitelist")
    for m in _PER_SERVING.finditer(clause):
        if not _hit(clause, m.start(), owned):
            continue
        n = m.group("n") or m.group("n2") or m.group("n3") or m.group("n4")
        if listed(n + " gummies per serving", tokens) or listed(n + "-gummy serving", tokens):
            continue
        reasons.append(_PREFIX + n + " gummies per serving is not on the pack label whitelist")
    for m in _MG.finditer(clause):
        if not _hit(clause, m.start(), owned):
            continue
        raw = m.group("n")
        if listed(raw + " mg", tokens) or listed(raw.replace(",", "") + " mg", tokens):
            continue
        reasons.append(_PREFIX + raw + " mg is not on the pack label whitelist")
    for m in _GINSENG.finditer(clause):
        if not _hit(clause, m.start(), owned):
            continue
        word = m.group("w").lower()
        key = "ginsenoside" if word.startswith("ginsenoside") else word
        if listed(key, tokens):
            continue
        reasons.append(_PREFIX + m.group("w") + " is not on the pack label whitelist")


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
    print("fusiforce_rules: %d violation(s)" % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

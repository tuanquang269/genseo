#!/usr/bin/env python3
"""FloraFresh formula guard (Kevin 2026-10-09).

The Supplement Facts label is the source of truth for FloraFresh:

    per 2 gummies   SNZ-1969 Probiotic Blend (Bacillus coagulans, spore-based)   1 billion CFU
                    Vitamin C                                                     30 mg
                    Pineapple Fruit Powder (with bromelain)                       100 mg
    sweetened with maltitol + isomalt, so not sugar-free
    badges: Allergen Free, Vegan, Halal, Gluten Free

The live PDP description is wrong (15 billion CFU, four Lactobacillus strains, XOS,
D-mannose, sugar-free) and stays wrong until Kevin gives a GO for a store rewrite.
Copy that names FloraFresh must not carry that formula or cite the PDP for strains or CFU.

brand_rules.assess() merges these violations, so every brand_rules caller (ticket lint,
ticket and landing builders, topic_fitness, validate_article, image prompts,
shopify_publisher) enforces them. Landing specs go through brand_rules.spec_violations().
Keep the label facts here; do not copy them into another file.

  python3 scripts/florafresh_rules.py --brief                 # the formula line for briefs
  python3 scripts/florafresh_rules.py "<text>" | <file>       # exit 1 on a violation
  python3 scripts/florafresh_rules.py --spec landing_drafts/<slug>.json
"""
import html
import json
import os
import re
import sys

HANDLE = "florafresh-vaginal-probiotics-gummies"
PRODUCT_URL = "https://wellnessnest.co/products/" + HANDLE
PRODUCT_NAME = "FloraFresh Vaginal Probiotics Gummies"
STRAIN = "Bacillus coagulans SNZ-1969"
CFU = "1 billion CFU"
SERVING = "2 gummies"
LABEL_FACTS = (
    ("SNZ-1969 Probiotic Blend (Bacillus coagulans, spore-based)", "1 billion CFU"),
    ("Vitamin C", "30 mg"),
    ("Pineapple Fruit Powder (with bromelain)", "100 mg"),
)
SWEETENERS = ("maltitol", "isomalt")
BADGES = ("Allergen Free", "Vegan", "Halal", "Gluten Free")
FORMULA_LINE = (
    "per 2 gummies, " + STRAIN + " (spore-based) " + CFU + ", Vitamin C 30 mg and pineapple fruit powder "
    "100 mg (with bromelain); sweetened with maltitol and isomalt, so not sugar-free; label badges "
    + ", ".join(BADGES)
)
SOURCE_LINE = (
    "Cite the Supplement Facts label, never the live PDP description or an older FloraFresh article "
    "(both repeat a wrong formula); a PDP/label mismatch is a gate failure."
)
TICKET_LINE = "**FloraFresh formula (Supplement Facts label, the source of truth):** " + FORMULA_LINE + ". " + SOURCE_LINE
LANDING_NOTE = (
    "formula: Supplement Facts label only (" + STRAIN + ", " + CFU + " per 2 gummies, not sugar-free), "
    "never the PDP description"
)

_PREFIX = "FloraFresh formula: "
_LABEL_CFU = 1e9
_GUMMY_CFU = 5e8

_FLORAFRESH = re.compile(r"flora[\s_-]?fresh", re.I)

# Visible text: product links become a FloraFresh mention, other paths and files are not copy.
_PRODUCT_REF = re.compile(
    r"(?:https?://[^\s\"'<>()]*?)?/?\bproducts/" + re.escape(HANDLE)
    + r"(?:\.js(?:on)?|\.oembed)?(?:\?[^\s\"'<>()]*)?(?:#[^\s\"'<>()]*)?"
    r"|\b" + re.escape(HANDLE) + r"\b(?:-(?:cutout|label|ref|pack))?(?:\.(?:png|jpe?g|webp|json))?",
    re.I,
)
_ROW_TAG = re.compile(r"</?(?:tr|table|thead|tbody|tfoot)\b[^>]*>", re.I)
_CELL_TAG = re.compile(r"</?(?:td|th)\b[^>]*>", re.I)
_BLOCK_TAG = re.compile(
    r"</?(?:p|div|li|ul|ol|h[1-6]|br|hr|section|article|blockquote|figure|figcaption|header|footer|aside"
    r"|details|summary|dl|dt|dd)\b[^>]*>",
    re.I,
)
_TAG = re.compile(r"<[^>]+>")
_PATHISH = re.compile(
    r"https?://\S+"
    r"|\]\([^)]*\)"
    r"|(?<![\w.])/(?:blogs|collections|products|pages|policies|cdn|files|apps)/[^\s\"'<>()`]*"
    r"|\b(?:tmp_images|product_refs|landing_drafts|published_drafts|logs|state|templates|scripts|personas)/\S*"
    r"|[\w.~-]+\.(?:png|jpe?g|webp|gif|svg|avif|html?|json|md|csv|js|mjs|py|sh|txt)\b",
    re.I,
)
_SLUG = re.compile(r"\b[a-z0-9]+(?:-[a-z0-9]+){3,}\b")
_ABBREV = re.compile(r"\b(?:e\.g|i\.e|vs|approx|incl|cf)\.", re.I)
_GENUS = re.compile(r"\b([A-Z])\.\s+(?=[a-z]{3,})")
# Table rows stay one clause (cells are joined with "|"); dashes do not end a clause either.
_CLAUSE_END = re.compile(r"[.!?]+(?=[\s\"')\]*_]|$)|[;:\n\r\t\u2022\u00b7{}\[\]]|\",|\\n")

_NEG_CUE = re.compile(
    r"\b(?:not|no|never|without|nor|neither|none|isn't|aren't|doesn't|don't|didn't|won't|wasn't|weren't"
    r"|cannot|can't|instead\s+of|rather\s+than|unlike|vs|versus|compar(?:e|ed|es|ing|ison)"
    r"|(?<!more\s)(?<!over\s)(?<!greater\s)than|other\s+(?:brands?|products?|probiotics?|supplements?)"
    r"|another\s+brand|competitors?|competing|drop(?:s|ped)?|remov(?:e|es|ed)|delet(?:e|es|ed)|avoid|ignore"
    r"|wrong|incorrect|outdated|mislabel\w*|free\s+(?:of|from)|separate(?:ly)?|alongside"
    r"|trials?\s+used|studies\s+used)\b",
    re.I,
)
_NEG_BREAK = re.compile(
    r"\b(?:but|however|yet|although|though|while|whereas|plus|also"
    r"|and\s+(?:has|have|contains?|includes?|delivers?|packs?|adds?|uses?|offers?))\b",
    re.I,
)
_NEG_AFTER = re.compile(
    r"^[^\n]{0,35}?\b(?:dropped|removed|deleted|cut|wrong|incorrect|outdated|not\s+on\s+the\s+label"
    r"|description[\s-]+only|(?:is|are|was|were|does|do)\s+not|isn't|aren't|wasn't|weren't|doesn't|don't)\b",
    re.I,
)
_RESEARCH = re.compile(r"\b(?:stud(?:y|ies|ied)|trials?|research(?:ers)?|tested|meta-analys\w*|reviews?)\b", re.I)
_YES_NO = re.compile(r"^\W*(?:is|are|does|do|did|can|could|should|will|would|has|have)\b", re.I)
_CARRY = re.compile(
    r"^[\s\"'(*_-]*(?:it|its|it's|they|their|each\s+(?:gummy|serving|dose|pouch)|every\s+(?:gummy|serving|dose)"
    r"|(?:the|this|these|our)\s+(?:gumm(?:y|ies)|formula|blend|product|probiotic|supplement|serving|pouch))\b",
    re.I,
)

# Wrong-PDP fingerprints: blocked anywhere in FloraFresh copy unless negated.
_FP_15B = re.compile(
    r"\b(?:15|fifteen)[\s-]*(?:billion|bn)\b"
    r"|\b15[\s-]*b\b(?=[\s-]*(?:cfus?|colony|live|active|viable|probiotics?|cultures)\b)"
    r"|\b15,000,000,000\b"
    r"|\b(?:cfus?|colony[\s-]+forming[\s-]+units?)\b[^.\n\d]{0,20}?\b15[\s-]*b\b",
    re.I,
)
_FP_FOUR = re.compile(
    r"\b(?:four|4)[\s-]+(?:clinically|scientifically)[\s-]+(?:studied|proven|tested|researched|backed)[\s-]+"
    r"(?:\w*lactobacill\w*[\s-]+|probiotic[\s-]+)?strains?\b"
    r"|\b(?:four|4)[\s-]+(?:different[\s-]+)?\w*lactobacill\w*[\s-]+strains?\b",
    re.I,
)
_FP_XOS = re.compile(r"\bxos\b|\bxylo[\s-]*oligo[\s-]*saccharides?\b", re.I)
_FP_SUGAR_FREE = re.compile(
    r"\bsugar[\s-]*free\b|\bsugarless\b|\bzero[\s-]+sugars?\b|\bno[\s-]+sugars?\b(?![\s-]+(?:alcohols?|crash))",
    re.I,
)
_PDP_SPECIES = re.compile(r"\b(rhamnosus|reuteri|salivarius|gasseri)\b", re.I)

# Claims that are wrong when tied to FloraFresh, but fine in research copy.
_ORGANISM = re.compile(
    r"\b\w*lactobacill\w*|\bbifidobacter\w*|\bsaccharomyces\b|\bstreptococc\w*|\blactococc\w*|\benterococc\w*"
    r"|\bpediococc\w*|\bleuconostoc\b|\bweissella\b"
    r"|\b(?:rhamnosus|reuteri|salivarius|gasseri|crispatus|acidophilus|fermentum|plantarum|jensenii|paracasei"
    r"|casei|bulgaricus|helveticus|boulardii|thermophilus|bifidum|longum|breve|infantis|lactis|subtilis|clausii"
    r"|licheniformis|iners)\b"
    r"|\b(?:gr-1|rc-14|lgg|la-5|bb-12|hn001)\b",
    re.I,
)
# "Lactobacillus sporogenes" is an old name for B. coagulans; "-dominant flora" describes the vagina, not the gummy.
_ORGANISM_OK_AFTER = re.compile(r"[\s-]*(?:sporogenes\b|dominan\w*|dominat\w*|flora\b|microbio\w*|communit\w*)", re.I)
_MANNOSE = re.compile(r"\b(?:d[\s-]*)?mannose\b", re.I)
_PREBIOTIC = re.compile(
    r"\bprebiotics?\b|\bsynbiotics?\b|\binulin\b|\bfos\b|\bfructo[\s-]*oligo[\s-]*saccharides?\b|\bgos\b"
    r"|\bgalacto[\s-]*oligo[\s-]*saccharides?\b",
    re.I,
)
_COUNT_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
                "ten": 10, "eleven": 11, "twelve": 12}
_STRAIN_COUNT = re.compile(
    r"(?<![\w.-])(?P<n>two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d{1,2})[\s-]+"
    r"(?:(?:clinically|scientifically|well)[\s-]+(?:studied|proven|tested|researched|backed)[\s-]+"
    r"|(?:different|unique|targeted|specific|probiotic|live|beneficial|vaginal|researched|premium|key)[\s-]+"
    r"|\w*lactobacill\w*[\s-]+)*strains?\b"
    r"|\bmulti[\s-]*strains?\b",
    re.I,
)
_NUM = r"(?P<num>\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)"
_UNIT = r"(?P<unit>billion|bn|b|million|mn|m)"
_CFU_AFTER = re.compile(
    r"(?<![\w.,-])" + _NUM + r"(?:\s*-?\s*" + _UNIT + r")?\b[\s-]*(?:live\s+|active\s+|viable\s+)?"
    r"(?:cfus?\b|colony[\s-]+forming|cultures\b|organisms\b|bacteria\b|spores\b|probiotics?\b)",
    re.I,
)
_CFU_BEFORE = re.compile(
    r"\b(?:cfus?|colony[\s-]+forming[\s-]+units?)\b[^.\n\d]{0,25}?(?<![\w.,-])" + _NUM + r"\s*-?\s*" + _UNIT + r"\b",
    re.I,
)
_MULT = {"billion": 1e9, "bn": 1e9, "b": 1e9, "million": 1e6, "mn": 1e6, "m": 1e6}
_PER_GUMMY = re.compile(r"^[^.;\n]{0,20}?\b(?:per|each|a|one|1|every)\s+(?:single\s+)?gummy\b", re.I)
_PER_SERVING = re.compile(
    r"^[^.;\n]{0,20}?\b(?:per\s+(?:2|two)\s+gummies|per\s+serving|each\s+serving|per\s+day|a\s+day|daily)\b", re.I)

# Citing the PDP for the formula.
_PDP_WORD = re.compile(
    r"\bpdps?\b|\bproduct[\s-]+(?:page|description|listing|copy|detail\s+page)s?\b"
    r"|\b(?:shopify|store)\s+(?:page|description|listing)s?\b",
    re.I,
)
_FORMULA_WORD = re.compile(
    r"\bcfus?\b|\bstrains?\b|\bformula(?:s|tion)?\b|(?<!see\s)\bingredients?\b|\bprobiotic\s+blend\b"
    r"|\bprebiotics?\b|\bspecies\b",
    re.I,
)
_LABEL_WORD = re.compile(
    r"supplement[\s-]+facts|\b(?:the|its|their|florafresh'?s?|pack|product|printed)\s+label\b"
    r"|\blabel\s+(?:image|panel|formula|facts)\b",
    re.I,
)
_LABEL_STRAIN = re.compile(r"\bsnz[\s-]*1969\b|\bcoagulans\b", re.I)

_SKIP_KEYS = frozenset((
    "url", "href", "image", "images", "pack_images", "avatar", "reference", "handle", "slug", "template",
    "template_suffix", "engine", "created", "store", "posture", "style", "icon", "kind", "image_note",
    "sources", "focal_y",
))
_PRODUCT_BLOCKS = frozenset(("product", "offer", "sticky_cta", "trust"))


def in_scope(text):
    """True when the text names FloraFresh (brand, product URL, or handle)."""
    return bool(_FLORAFRESH.search(text or ""))


def violations(text):
    """Formula claims the Supplement Facts label does not support. [] when FloraFresh is not named."""
    text = text or ""
    if not in_scope(text):
        return []
    return _scan(text)


def spec_violations(spec):
    """violations() for a landing spec, field by field.

    Provenance notes (source, *_source, image_note) and the citation list are skipped, so a spec can
    record what the wrong PDP says. Strings under product / offer / sticky_cta / trust are product-card
    copy and count as FloraFresh claims even when the string does not repeat the brand.
    """
    if not in_scope(json.dumps(spec, ensure_ascii=False)):
        return []
    out = []
    for path, text, attributed in _spec_texts(spec, "", None, False):
        for reason in _scan(text, attributed):
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
    t = t.replace("\u2010", "-").replace("\u2011", "-")
    t = _PRODUCT_REF.sub(" FloraFresh product page ", t)
    t = _ROW_TAG.sub(" \n ", t)
    t = _CELL_TAG.sub(" | ", t)
    t = _BLOCK_TAG.sub(" \n ", t)
    t = _TAG.sub(" ", t)
    t = html.unescape(t)
    t = _PATHISH.sub(" ", t)
    t = _SLUG.sub(" ", t)
    t = _ABBREV.sub(lambda m: m.group(0).replace(".", ""), t)
    return _GENUS.sub(r"\1_ ", t)


def _clauses(visible):
    """(start, end, delimiter) for each clause of the visible text."""
    out, start = [], 0
    for m in _CLAUSE_END.finditer(visible):
        if m.start() > start:
            out.append((start, m.start(), m.group(0)))
        start = m.end()
    if start < len(visible):
        out.append((start, len(visible), ""))
    return out


def _negated(clause, start, end, lo=None):
    """A negation or contrast cue before the hit (unless a but/plus/also resets it), or a cue right after."""
    lo = max(0, start - 60) if lo is None else max(0, lo)
    pre = clause[lo:start]
    cues = list(_NEG_CUE.finditer(pre))
    if cues and not _NEG_BREAK.search(pre, cues[-1].end()):
        return True
    return bool(_NEG_AFTER.search(clause[end:end + 60]))


def _tied(clause, start, end, ff_spans, carried):
    """True when clause[start:end] is claimed for FloraFresh rather than for a study or another brand."""
    if carried:
        return not _negated(clause, start, end, lo=0)
    for fs, fe in ff_spans:
        if fe <= start and start - fe <= 120:
            if not _negated(clause, start, end, lo=fs - 30):
                return True
        elif fs >= end and fs - end <= 120:
            if not _NEG_CUE.search(clause[end:fs]) and not _negated(clause, start, end):
                return True
    return False


def _scan(text, attributed=False):
    visible = _visible(text)
    reasons = []
    prev_ff, prev_delim = False, ""
    for s, e, delim in _clauses(visible):
        clause = visible[s:e]
        if not clause.strip():
            continue
        ff_spans = [(m.start(), m.end()) for m in _FLORAFRESH.finditer(clause)]
        # "FloraFresh: 15 billion CFU" and "FloraFresh ... It has" both claim the next clause for the brand.
        carried = attributed or (prev_ff and (prev_delim == ":" or bool(_CARRY.match(clause))))
        question = delim.startswith("?") and bool(_YES_NO.match(clause))
        _check_fingerprints(clause, question, reasons)
        if (ff_spans or carried) and not question:
            _check_claims(clause, ff_spans, carried, reasons)
        prev_ff, prev_delim = bool(ff_spans) or carried, delim
    _check_pdp_species(visible, reasons)
    return _dedupe(reasons)


def _check_fingerprints(clause, question, reasons):
    rules = (
        (_FP_15B, "15 billion CFU is the wrong PDP figure (label: " + CFU + " per 2 gummies)", False),
        (_FP_FOUR, "four Lactobacillus strains is the wrong PDP formula (label: one strain, " + STRAIN + ")", False),
        (_FP_XOS, "XOS is not on the label", False),
        (_FP_SUGAR_FREE, "FloraFresh is not sugar-free (sweetened with maltitol and isomalt)", True),
    )
    for rx, reason, question_ok in rules:
        for m in rx.finditer(clause):
            if (question_ok and question) or _negated(clause, m.start(), m.end()):
                continue
            reasons.append(_PREFIX + reason)
            break


def _check_claims(clause, ff_spans, carried, reasons):
    def tied(m_start, m_end):
        return _tied(clause, m_start, m_end, ff_spans, carried)

    for m in _ORGANISM.finditer(clause):
        if _ORGANISM_OK_AFTER.match(clause, m.end()):
            continue
        if tied(m.start(), m.end()):
            reasons.append(_PREFIX + m.group(0) + " is not in FloraFresh (label strain: " + STRAIN + ")")
    for m in _MANNOSE.finditer(clause):
        if tied(m.start(), m.end()):
            reasons.append(_PREFIX + "D-mannose is not on the label")
            break
    for m in _PREBIOTIC.finditer(clause):
        if tied(m.start(), m.end()):
            reasons.append(_PREFIX + m.group(0).lower() + " is not on the label")
    for m in _STRAIN_COUNT.finditer(clause):
        word = (m.group("n") or "").lower()
        n = _COUNT_WORDS.get(word) or (int(word) if word.isdigit() else 2)
        if n >= 2 and tied(m.start(), m.end()):
            what = "multi-strain" if not word else str(n) + " strains"
            reasons.append(_PREFIX + what + " (label: one strain, " + STRAIN + ")")
    for start, end, value in _cfu_amounts(clause):
        problem = None if abs(value - 15e9) < 1 else _cfu_problem(clause, end, value)
        if problem is not None and tied(start, end):
            reasons.append(_PREFIX + _fmt_cfu(value) + problem + " (label: " + CFU + " per 2 gummies)")
    pdp = _PDP_WORD.search(clause)
    if (pdp and _FORMULA_WORD.search(clause) and not _LABEL_WORD.search(clause)
            and not _states_label_formula(clause) and not _negated(clause, pdp.start(), pdp.end())):
        reasons.append(_PREFIX + "strains/CFU cited from the PDP; cite the Supplement Facts label "
                       "(the PDP description is wrong)")


def _states_label_formula(clause):
    """True when the clause gives the label formula itself: the label strain, or only label CFU amounts."""
    if _LABEL_STRAIN.search(clause):
        return True
    amounts = list(_cfu_amounts(clause))
    return bool(amounts) and all(_cfu_problem(clause, end, value) is None for _start, end, value in amounts)


def _check_pdp_species(visible, reasons):
    hits = [(m.start(), m.end(), m.group(1).lower()) for m in _PDP_SPECIES.finditer(visible)]
    for i, (pos, end, _name) in enumerate(hits):
        if len({n for p, _e, n in hits[i:] if p - pos <= 250}) < 4:
            continue
        for s, e, _delim in _clauses(visible):
            if s <= pos < e:
                clause = visible[s:e]
                if _RESEARCH.search(clause[max(0, pos - s - 80):pos - s]) or _negated(clause, pos - s, end - s):
                    return
                break
        reasons.append(_PREFIX + "L. rhamnosus, reuteri, salivarius and gasseri together are the wrong PDP formula "
                                 "(label: " + STRAIN + ")")
        return


def _cfu_amounts(clause):
    seen = set()
    for rx in (_CFU_AFTER, _CFU_BEFORE):
        for m in rx.finditer(clause):
            num, unit = m.group("num"), (m.group("unit") or "").lower()
            if not unit and "," not in num:
                continue
            value = float(num.replace(",", "")) * _MULT.get(unit, 1.0)
            if value < 1e6 or m.start("num") in seen:
                continue
            seen.add(m.start("num"))
            yield m.start("num"), m.end(), value


def _cfu_problem(clause, end, value):
    """None when the amount matches the label (1 billion per 2 gummies, 500 million per gummy)."""
    tail = clause[end:end + 40]
    if abs(value - _LABEL_CFU) < 1:
        return " per gummy" if _PER_GUMMY.match(tail) else None
    if abs(value - _GUMMY_CFU) < 1:
        return " per serving" if _PER_SERVING.match(tail) else None
    return ""


def _fmt_cfu(value):
    if value >= 1e9:
        return "%g billion CFU" % (value / 1e9)
    if value >= 1e6:
        return "%g million CFU" % (value / 1e6)
    return "%g CFU" % value


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
    bad = spec_violations(json.loads(raw)) if "--spec" in argv else violations(raw)
    for reason in bad:
        print("✗ " + reason)
    print("florafresh_rules: %d violation(s)" % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

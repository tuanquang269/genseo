#!/usr/bin/env python3
"""Rights-gated first-hand experience block for Wellness Nest blog articles.

The registry is templates/first-hand-quotes.json. A quote is rendered only when
rights_confirmed is true and approved_by is a non-empty string, and only when
the quote passes the claim lint. Anything else is omitted. The article gate
fails a draft that pastes a registry quote the gate did not clear.

This module is for the blog article pipeline (validate_article.py and the
auto-publish writer). It does not publish, and it is not used by landing pages,
product pages, collections, or the theme.

  python3 scripts/first_hand_experience.py --lint
  python3 scripts/first_hand_experience.py --product ageaura-pure-nmn-tmg-nad-complex
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys

import ageaura_rules

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_REGISTRY = os.path.join(ROOT, "templates", "first-hand-quotes.json")

RESULTS_VARY = "Results vary."
SECTION_STYLE = (
    "border-left:4px solid #54b94a;background:#f6fbf5;"
    "border-radius:8px;padding:16px 20px;margin:20px 0;"
)
SKIP_REASON = "not rights-confirmed or approved_by is empty"

REQUIRED = (
    "id",
    "product_handle",
    "creator_display_name",
    "source",
    "quote",
    "timestamp_range",
    "timestamp_precision",
    "claim_check",
    "disclosure",
    "rights_confirmed",
    "approved_by",
)
PRECISIONS = frozenset({"scored-cut", "transcript-window", "full-vo"})
CLAIM_CHECKS = frozenset({"personal-feel", "structure/function"})

_DISPLAY = re.compile(r"^[A-Z][a-z]+ [A-Z]\.$")
_SOURCE = re.compile(r"^[0-9a-f]{8}$")
_STAMP = re.compile(r"^\d{1,2}:\d{2}(?:\.\d)?-\d{1,2}:\d{2}(?:\.\d)?$")
_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_BLOCK_ID = re.compile(r'data-genseo-first-hand="([^"]+)"')
_BLOCK_HANDLE = re.compile(r'data-genseo-first-hand-block="([^"]+)"')
_PRODUCT = re.compile(r"/products/([a-z0-9-]+)", re.I)

_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}
_BANNED = (
    ("disease", re.compile(r"\bdiseases?\b", re.I)),
    ("cure", re.compile(r"\bcures?\b|\bcured\b|\bcuring\b", re.I)),
    ("treat", re.compile(r"\btreats?\b|\btreated\b|\btreating\b|\btreatments?\b", re.I)),
    ("reverse aging", re.compile(r"\brevers(?:e|es|ed|ing)\b.{0,16}\baging\b", re.I)),
    ("anti-aging", re.compile(r"\banti[-\s]?aging\b", re.I)),
)
_EXCLUDED = (
    ("generic efficacy line", re.compile(r"a wellness brand that actually works", re.I)),
    ("call to action", re.compile(r"\btap the link\b|\bthank me later\b", re.I)),
    ("transcript hallucination", re.compile(r"thanks for watching", re.I)),
)
_MASS = re.compile(
    r"\b(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)\s*"
    r"(?:mg|mcg|μg|ug|iu|mls?|milligrams?|micrograms?|grams?)\b",
    re.I,
)
_GRAM = re.compile(r"\b\d+(?:\.\d+)?\s*g\b", re.I)
_COUNT = re.compile(
    r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
    r"(capsules?|gummies|tablets?|softgels?|servings?|drops?)\b",
    re.I,
)
_MULTI = re.compile(
    r"\b(?:twice|thrice|(?:two|three|four|\d+)\s+times)\s+(?:a|per|each)\s+day\b"
    r"|\b(?:twice|thrice|(?:two|three|four|\d+)\s+times)\s+daily\b",
    re.I,
)
_PAID_PARTNERSHIP = re.compile(r"paid\s+partnership", re.I)
_PAID_MARKER = re.compile(r"#ad\b|paid\s+creator", re.I)


def load_registry(path=None):
    path = path or DEFAULT_REGISTRY
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("quote registry must be a JSON object")
    return data


def _form_key(word):
    w = (word or "").strip().lower()
    if w.endswith("ies"):
        return w[:-3] + "y"
    if w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _count_value(token):
    token = token.lower()
    if token.isdigit():
        return int(token)
    return _NUMBER_WORDS[token]


def _dose_phrase(dose):
    if not isinstance(dose, dict):
        return "no label dose on file"
    count = dose.get("count")
    form = dose.get("form") or ""
    if count == 2 and _form_key(form) == "capsule":
        return "2 capsules daily"
    if count and form:
        schedule = dose.get("schedule") or ""
        return ("%s %s %s" % (count, form, schedule)).strip()
    return "no label dose on file"


def _products(registry):
    if not isinstance(registry, dict):
        return {}
    products = registry.get("products")
    return products if isinstance(products, dict) else {}


def _quotes(registry):
    if not isinstance(registry, dict):
        return []
    quotes = registry.get("quotes")
    return quotes if isinstance(quotes, list) else []


def disclosure_ok(text):
    text = text or ""
    return bool(_PAID_PARTNERSHIP.search(text) and _PAID_MARKER.search(text))


def is_cleared(entry):
    if not isinstance(entry, dict):
        return False
    if entry.get("rights_confirmed") is not True:
        return False
    approved = entry.get("approved_by")
    return isinstance(approved, str) and bool(approved.strip())


def lint_quote(entry, products=None):
    """Claim and disclosure problems for one quote. Empty means the line may render once cleared."""
    if not isinstance(entry, dict):
        return ["quote entry is not an object"]
    qid = entry.get("id") or "?"
    quote = entry.get("quote") or ""
    problems = []
    for label, rx in _BANNED:
        if rx.search(quote):
            problems.append("%s: quote contains %s" % (qid, label))
    for label, rx in _EXCLUDED:
        if rx.search(quote):
            problems.append("%s: quote contains excluded %s" % (qid, label))
    if not disclosure_ok(entry.get("disclosure") or ""):
        problems.append("%s: missing disclosure" % qid)
    handle = (entry.get("product_handle") or "").strip().lower()
    product = (products or {}).get(handle) or {}
    dose = product.get("label_dose") if isinstance(product, dict) else None
    phrase = _dose_phrase(dose if isinstance(dose, dict) else {})
    allowed_count = dose.get("count") if isinstance(dose, dict) else None
    allowed_form = _form_key(dose.get("form") if isinstance(dose, dict) else "")
    if _MASS.search(quote) or _GRAM.search(quote) or _MULTI.search(quote):
        problems.append("%s: dosage claim beyond the label (%s)" % (qid, phrase))
    for match in _COUNT.finditer(quote):
        count = _count_value(match.group(1))
        form = _form_key(match.group(2))
        if allowed_count is None or form != allowed_form or count != allowed_count:
            problems.append("%s: dosage claim beyond the label (%s)" % (qid, phrase))
            break
    return problems


def _renderable(entry, products):
    return is_cleared(entry) and not lint_quote(entry, products)


def schema_errors(registry):
    errors = []
    if not isinstance(registry, dict):
        return ["registry is not a JSON object"]
    if registry.get("version") != 1:
        errors.append("registry version must be 1")
    products = registry.get("products")
    if not isinstance(products, dict) or not products:
        errors.append("registry products must be a non-empty object")
        products = {}
    quotes = registry.get("quotes")
    if not isinstance(quotes, list):
        errors.append("registry quotes must be a list")
        return errors
    seen = set()
    for product_handle, product in products.items():
        if ageaura_rules.classify_handle(product_handle) == "deny":
            errors.append("%s: denied product handle" % product_handle)
        if not isinstance(product, dict):
            errors.append("%s: product entry is not an object" % product_handle)
            continue
        label = product.get("label")
        if not isinstance(label, str) or not label.strip():
            errors.append("%s: product label is empty" % product_handle)
        dose = product.get("label_dose")
        if not isinstance(dose, dict) or not isinstance(dose.get("count"), int) or not dose.get("form"):
            errors.append("%s: label_dose needs an integer count and a form" % product_handle)
        if ageaura_rules.normalize_handle(product_handle) == ageaura_rules.HANDLE:
            if label != ageaura_rules.PRODUCT_LABEL:
                errors.append("AgeAura product label does not match ageaura_rules.PRODUCT_LABEL")
            if not isinstance(dose, dict) or dose.get("count") != 2 or _form_key(dose.get("form") or "") != "capsule":
                errors.append("AgeAura label dose must stay 2 capsules daily")
    for index, entry in enumerate(quotes):
        where = "quotes[%d]" % index
        if not isinstance(entry, dict):
            errors.append("%s: not an object" % where)
            continue
        qid = entry.get("id") or where
        for key in REQUIRED:
            if key not in entry:
                errors.append("%s: missing %s" % (qid, key))
        if entry.get("id"):
            if not isinstance(entry["id"], str) or not _ID.match(entry["id"]):
                errors.append("%s: id must be lowercase hyphenated" % qid)
            elif entry["id"] in seen:
                errors.append("%s: duplicate id" % qid)
            else:
                seen.add(entry["id"])
        handle = entry.get("product_handle")
        if not isinstance(handle, str) or handle not in products:
            errors.append("%s: product_handle is not in products" % qid)
        elif ageaura_rules.classify_handle(handle) == "deny":
            errors.append("%s: denied product handle" % qid)
        name = entry.get("creator_display_name")
        if not isinstance(name, str) or not _DISPLAY.match(name):
            errors.append("%s: creator_display_name must be a first name plus last initial" % qid)
        source = entry.get("source")
        if not isinstance(source, str) or not _SOURCE.match(source):
            errors.append("%s: source must be the Trybe submission short id" % qid)
        quote = entry.get("quote")
        if not isinstance(quote, str) or quote != quote.strip() or not (20 <= len(quote) <= 240):
            errors.append("%s: quote must be 20 to 240 characters of trimmed text" % qid)
        stamp = entry.get("timestamp_range")
        if not isinstance(stamp, str) or not _STAMP.match(stamp):
            errors.append("%s: timestamp_range is not a clock range" % qid)
        precision = entry.get("timestamp_precision")
        if precision not in PRECISIONS:
            errors.append("%s: timestamp_precision is not a known value" % qid)
        elif precision == "full-vo" and not str(entry.get("timestamp_note") or "").strip():
            errors.append("%s: full-vo timestamp needs timestamp_note" % qid)
        if entry.get("claim_check") not in CLAIM_CHECKS:
            errors.append("%s: claim_check must be personal-feel or structure/function" % qid)
        if not isinstance(entry.get("disclosure"), str):
            errors.append("%s: disclosure must be a string" % qid)
        if not isinstance(entry.get("rights_confirmed"), bool):
            errors.append("%s: rights_confirmed must be a boolean" % qid)
        approved = entry.get("approved_by")
        if not isinstance(approved, str):
            errors.append("%s: approved_by must be a string" % qid)
        note = entry.get("timestamp_note")
        if note is not None and not isinstance(note, str):
            errors.append("%s: timestamp_note must be a string" % qid)
    return errors


def registry_problems(registry):
    problems = list(schema_errors(registry))
    products = _products(registry)
    for entry in _quotes(registry):
        if isinstance(entry, dict):
            problems.extend(lint_quote(entry, products))
    return problems


def _label(registry, handle):
    product = _products(registry).get(handle) or {}
    if isinstance(product, dict):
        label = product.get("label")
        if isinstance(label, str) and label.strip():
            return label.strip()
    return ""


def _matching(registry, handle, quote_id=None):
    handle = ageaura_rules.normalize_handle(handle)
    picked = []
    for entry in _quotes(registry):
        if not isinstance(entry, dict):
            continue
        if ageaura_rules.normalize_handle(entry.get("product_handle") or "") != handle:
            continue
        if quote_id and entry.get("id") != quote_id:
            continue
        picked.append(entry)
    return picked


def _quote_html(entry, label):
    qid = html.escape(entry["id"], quote=True)
    quote = html.escape(entry["quote"])
    name = html.escape(entry["creator_display_name"])
    if label:
        attribution = "%s, on %s" % (name, html.escape(label))
    else:
        attribution = name
    disclosure = html.escape(entry["disclosure"])
    return "\n".join((
        '<div data-genseo-first-hand="%s">' % qid,
        '<blockquote style="margin:0;padding:0;border:0;">',
        '<p style="margin:0;color:#1e3a29;font-size:1.05em;">%s</p>' % quote,
        "</blockquote>",
        '<p data-genseo-first-hand-attribution="%s" style="margin:10px 0 0;color:#1e3a29;font-weight:700;">%s</p>'
        % (qid, attribution),
        '<p data-genseo-first-hand-disclosure="%s" style="margin:4px 0 0;color:#444444;font-size:.92em;">%s</p>'
        % (qid, disclosure),
        '<p data-genseo-first-hand-note="%s" style="margin:4px 0 0;color:#444444;font-size:.92em;">%s</p>'
        % (qid, RESULTS_VARY),
        "</div>",
    ))


def render_block(registry, handle, quote_id=None):
    """HTML block for cleared quotes, or "" when the gate skips every line."""
    if schema_errors(registry):
        return ""
    handle = ageaura_rules.normalize_handle(handle)
    if not handle:
        return ""
    products = _products(registry)
    parts = []
    for entry in _matching(registry, handle, quote_id):
        if _renderable(entry, products):
            parts.append(_quote_html(entry, _label(registry, handle)))
    if not parts:
        return ""
    return (
        '<section data-genseo-first-hand-block="%s" style="%s">\n%s\n</section>'
        % (html.escape(handle, quote=True), SECTION_STYLE, "\n".join(parts))
    )


def skip_message(registry, handle, quote_id=None):
    schema = schema_errors(registry)
    if schema:
        return "WARN first-hand experience omitted: registry schema: " + "; ".join(schema[:4])
    handle = ageaura_rules.normalize_handle(handle)
    matched = _matching(registry, handle, quote_id)
    if quote_id and not matched:
        return "WARN first-hand experience omitted: no quote %s for %s" % (quote_id, handle or "(empty handle)")
    if not matched:
        return "WARN first-hand experience omitted: no quotes for %s" % (handle or "(empty handle)")
    products = _products(registry)
    bits = []
    for entry in matched:
        if _renderable(entry, products):
            continue
        qid = entry.get("id") or "?"
        if not is_cleared(entry):
            bits.append("%s (%s)" % (qid, SKIP_REASON))
        else:
            bits.append("%s (%s)" % (qid, "; ".join(lint_quote(entry, products))))
    if not bits:
        return ""
    return "WARN first-hand experience omitted for %s: %s" % (handle, "; ".join(bits))


def _norm(text):
    raw = re.sub(r"(?is)<!--.*?-->", " ", text or "")
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = (
        raw.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    return re.sub(r"\s+", " ", raw).strip()


def _contains_quote(text, quote):
    if not quote:
        return False
    if quote in (text or ""):
        return True
    return _norm(quote) in _norm(text)


def _check_used_quote(entry, text, ids_in_text, products, fails):
    qid = entry.get("id") or "?"
    problems = lint_quote(entry, products)
    if problems:
        fails.append("first-hand quote %s failed claim lint: %s" % (qid, "; ".join(problems)))
    if not is_cleared(entry):
        fails.append("unapproved first-hand quote pasted: %s" % qid)
    if problems or not is_cleared(entry):
        return
    if not _contains_quote(text, entry.get("quote") or ""):
        fails.append("first-hand quote %s text does not match the registry" % qid)
        return
    if qid not in ids_in_text:
        fails.append("first-hand quote %s is outside the first-hand block" % qid)
        return
    disclosure = entry.get("disclosure") or ""
    if disclosure not in (text or "") and _norm(disclosure) not in _norm(text):
        fails.append("first-hand quote %s missing disclosure" % qid)
    if RESULTS_VARY not in (text or ""):
        fails.append("first-hand quote %s missing results vary note" % qid)


def article_findings(text, registry=None, registry_path=None):
    """Return (fails, warns) for a blog draft or rendered article.

    A missing block is silent. A registry quote that shows up without clearance,
    or a first-hand block that fails the claim lint, is a failure.
    """
    fails = []
    warns = []
    if registry is None:
        try:
            registry = load_registry(registry_path)
        except (OSError, json.JSONDecodeError, ValueError):
            if _BLOCK_ID.search(text or ""):
                fails.append("first-hand experience block present but the quote registry is unreadable")
            return fails, warns
    text = text or ""
    products = _products(registry)
    known = {}
    for entry in _quotes(registry):
        if isinstance(entry, dict) and entry.get("id"):
            known[entry["id"]] = entry
    ids_in_text = set(_BLOCK_ID.findall(text))
    seen = set()
    for qid in sorted(ids_in_text):
        entry = known.get(qid)
        if entry is None:
            fails.append("unknown first-hand quote id: %s" % qid)
            continue
        seen.add(qid)
        _check_used_quote(entry, text, ids_in_text, products, fails)
    for entry in _quotes(registry):
        if not isinstance(entry, dict):
            continue
        qid = entry.get("id")
        if qid in seen:
            continue
        if _contains_quote(text, entry.get("quote") or ""):
            _check_used_quote(entry, text, ids_in_text, products, fails)
    return fails, warns


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="first_hand_experience.py",
        description="Render or lint the rights-gated first-hand experience block for a blog article."
    )
    parser.add_argument("--product", default="", help="product handle or /products/<handle> URL")
    parser.add_argument("--id", default="", help="one registry id; still rights-gated")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY)
    parser.add_argument("--lint", action="store_true", help="schema, disclosure, and claim lint")
    args = parser.parse_args(argv)
    try:
        registry = load_registry(args.registry)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("first-hand quote registry unreadable: %s" % exc, file=sys.stderr)
        return 1
    if args.lint:
        problems = registry_problems(registry)
        if problems:
            for line in problems:
                print(line, file=sys.stderr)
            return 1
        if not args.product:
            print("first-hand quotes: OK (%d)" % len(_quotes(registry)))
            return 0
    elif not args.product:
        parser.print_help(sys.stderr)
        return 2
    block = render_block(registry, args.product, quote_id=args.id or None)
    if not block:
        print(skip_message(registry, args.product, args.id or None), file=sys.stderr)
        return 0
    print(block)
    return 0


if __name__ == "__main__":
    sys.exit(main())

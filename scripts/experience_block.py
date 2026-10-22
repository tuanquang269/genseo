#!/usr/bin/env python3
"""First-hand experience block for blog articles.

Quotes render only from data/experience_quotes.json. A row with example: true
never renders. A row without usage_allowed, consent, and a source never renders.
If nothing matches the article's product and topic, the quote block is omitted.

The optional "How we checked this" line is not a testimonial. It names a label
check the article gate already runs. It is omitted for products that gate does
not check.

  python3 scripts/experience_block.py render --draft <file.md> [--with-method]
  python3 scripts/experience_block.py audit --draft <file.md>
  python3 scripts/experience_block.py lint

No network. Does not publish.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys

import brand_rules
import florafresh_rules
import geo_citability
import gold_resin_rules
import shilasource_resin_rules
import shockwave_rules
import turkesterone_rules

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(ROOT, "data", "experience_quotes.json")
MAX_QUOTES = 2

SOURCE_TYPES = ("verified_review", "creator_submission", "internal_staff_test")
SOURCE_LABEL = {
    "verified_review": "Verified review",
    "creator_submission": "Creator",
    "internal_staff_test": "Staff test",
}
RECEIVED = ("", "free", "purchased", "none")
FREE_DISCLOSURE = "Received product free"
_PLACEHOLDER_HOSTS = ("example.com", "example.org", "example.net", "localhost")
_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,80}$")
_PERSONA = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_URL = re.compile(r"^https?://[^\s\"'<>]+$")
_TAG_STOP = {"the", "and", "for", "how", "what", "why", "who", "with", "from", "this", "that", "usa"}
_PRODUCT_URL = re.compile(
    r"https?://wellnessnest\.co/products/([a-z0-9-]+)|/products/([a-z0-9-]+)",
    re.I,
)
_ASIDE = re.compile(
    r"<aside\b[^>]*data-gs-experience\s*=\s*[\"']block[\"'][^>]*>.*?</aside>",
    re.I | re.S,
)
_METHOD = re.compile(
    r"<p\b[^>]*data-gs-experience\s*=\s*[\"']method[\"'][^>]*>(.*?)</p>",
    re.I | re.S,
)
_QUOTE_NODE = re.compile(
    r"<blockquote\b([^>]*data-gs-experience\s*=\s*[\"']quote[\"'][^>]*)>(.*?)</blockquote>",
    re.I | re.S,
)
_STAR = re.compile(
    r"[★⭐☆]"
    r"|\b[1-5](?:\.\d)?\s*/\s*5\b"
    r"|\b[1-5](?:\.\d)?-star\b"
    r"|\b(?:five|[1-5])\s+stars?\b"
    r"|\bTrustScore\b"
    r"|\brated\s+[0-5](?:\.\d)?\s*(?:out of\s*5|/5|stars?)\b",
    re.I,
)
_TESTIMONIAL_PHRASE = re.compile(
    r"\bwhat (?:our )?customers say\b"
    r"|\bcustomer testimonials?\b"
    r"|\bverified buyers?\b"
    r"|\bverified purchases?\b"
    r"|\breal (?:customer )?reviews?\b",
    re.I,
)
_ATTR_QUOTE = re.compile(
    r"[\"“]([^\"”]{40,}?)[\"”]\s*[—–-]\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}"
)
_FIRST_PERSON = re.compile(r"\b(I|I've|I'm|my|we|our)\b")
_MD_QUOTE = re.compile(r"(?m)^>\s+\S")
_BARE_BQ = re.compile(
    r"<blockquote\b(?![^>]*data-gs-experience\s*=\s*[\"']quote[\"'])",
    re.I,
)
_PERSONAL = re.compile(
    r"\bour team tested\b"
    r"|\bwe (?:personally )?(?:tried|tested|started taking)\b"
    r"|\bwe have been taking\b"
    r"|\bI (?:personally )?(?:tried|tested|started taking|have been taking|keep taking)\b"
    r"|\bI've been (?:taking|using)\b"
    r"|\bmy own experience\b"
    r"|\bafter (?:I|we) (?:tried|used|started)\b"
    r"|\bpersonally (?:tried|used|tested|takes|take)\b",
    re.I,
)
_NAME_USE = re.compile(
    r"\b(?:takes|tried|swears by|has been taking|personally uses)\b",
    re.I,
)
_AUTHOR_SECTION = re.compile(
    r"(?is)(?:#{2,3}\s*|<h[23][^>]*>\s*)About the Author\s*(?:</h[23]>)?\s*(.{0,800})"
)
_FLORA_METHOD = (
    "How we checked this: " + florafresh_rules.PRODUCT_NAME
    + " sentences are checked before publish against the Supplement Facts label in "
    "scripts/florafresh_rules.py. That is a label check, not a personal trial and not a customer review."
)
_LABEL_MODULES = (
    shockwave_rules,
    gold_resin_rules,
    shilasource_resin_rules,
    turkesterone_rules,
)

COVERAGE_WARN = (
    "experience coverage: no first-hand block "
    "(no eligible quote in data/experience_quotes.json for this product and topic)"
)


def normalize_ws(text):
    return re.sub(r"\s+", " ", text or "").strip()


def _norm(text):
    text = re.sub(r"(?s)<[^>]+>", " ", text or "")
    text = html.unescape(text).replace("\u2019", "'").replace("\u2018", "'")
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _plain(raw):
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw or "")
    text = re.sub(r"(?s)<!--.*?-->", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text).replace("\u2019", "'").replace("\u2018", "'")
    return normalize_ws(text)


def _has_phrase(blob, phrase):
    phrase = _norm(phrase)
    if not phrase:
        return False
    return (" " + phrase + " ") in (" " + blob + " ")


def load_quotes(path=None):
    path = path or DEFAULT_PATH
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rows = data.get("quotes") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def product_handles(text):
    found = []
    for match in _PRODUCT_URL.finditer(text or ""):
        handle = (match.group(1) or match.group(2) or "").lower()
        if handle:
            found.append(handle)
    return found


def topic_blob(text):
    parts = []
    for rx in (
        r"(?is)<h[123][^>]*>(.*?)</h[123]>",
        r"(?m)^#{1,3}\s+(.+)$",
        r"(?is)<!--\s*meta_description:\s*(.*?)\s*-->",
    ):
        parts.extend(match.group(1) for match in re.finditer(rx, text or ""))
    return _norm(" ".join(parts))


def primary_product(text):
    handles = product_handles(text)
    if not handles:
        return ""
    counts = {}
    first = {}
    for index, handle in enumerate(handles):
        counts[handle] = counts.get(handle, 0) + 1
        first.setdefault(handle, index)
    return max(counts, key=lambda handle: (counts[handle], -first[handle]))


def _valid_date(value):
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", value or ""):
        return False
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _valid_tag(tag):
    if not isinstance(tag, str):
        return False
    norm = _norm(tag)
    return len(norm) >= 3 and norm not in _TAG_STOP


def _source_host(url):
    match = re.match(r"https?://([^/:]+)", url or "", re.I)
    return match.group(1).lower() if match else ""


def _label_method(module):
    return (
        "How we checked this: " + module.PRODUCT_NAME
        + " sentences are checked before publish against " + module.LABEL_REL
        + ". That is a pack-label check, not a personal trial and not a customer review."
    )


def method_line(text, root=None):
    """One sentence when the article gate already checks this product's label.

    Empty for every other product, including ones whose label file is used only
    by the landing gate or the llms.txt draft.
    """
    handle = primary_product(text)
    if not handle:
        return ""
    if handle == florafresh_rules.HANDLE:
        return _FLORA_METHOD
    root = ROOT if root is None else root
    for module in _LABEL_MODULES:
        if handle != module.HANDLE:
            continue
        if os.path.isfile(os.path.join(root, module.LABEL_REL)):
            return _label_method(module)
        return ""
    return ""


def claim_gate_failures(quote):
    """Article citability gate plus the brand/label gate, on the quote alone."""
    fails = list(geo_citability.compliance_issues(quote or ""))
    fails.extend(brand_rules.violations(quote or ""))
    return fails


def eligibility_problems(row):
    """Why a row must not render. example: true short-circuits the rest."""
    if not isinstance(row, dict):
        return ["row"]
    # Any truthy example flag excludes the row. Only a real JSON false, or an
    # omitted field, can proceed. The string "true" must not render.
    if row.get("example") is True or str(row.get("example") or "").strip().lower() in ("true", "yes", "1"):
        return ["example"]
    reasons = []
    if not _ID.match(str(row.get("id") or "")):
        reasons.append("id")
    if row.get("usage_allowed") is not True:
        reasons.append("usage_allowed")
    url = str(row.get("source_url") or "").strip()
    source_id = str(row.get("source_id") or "").strip()
    if not url and not source_id:
        reasons.append("source")
    if url and not _URL.match(url):
        reasons.append("source_url_scheme")
    elif url and _source_host(url) in _PLACEHOLDER_HOSTS:
        reasons.append("source_placeholder")
    quote = str(row.get("quote") or "").strip()
    if not quote:
        reasons.append("quote")
    elif quote[-1] not in ".!?":
        reasons.append("quote_punctuation")
    if not str(row.get("attribution") or "").strip():
        reasons.append("attribution")
    if row.get("source_type") not in SOURCE_TYPES:
        reasons.append("source_type")
    product = str(row.get("product") or "").strip().lower()
    if not product:
        reasons.append("product")
    elif not brand_rules.product_allowed(product):
        reasons.append("product_denied")
    tags = row.get("topic_tags")
    if not isinstance(tags, list) or not tags or not all(_valid_tag(tag) for tag in tags):
        reasons.append("topic_tags")
    if not _valid_date(str(row.get("date") or "")):
        reasons.append("date")
    if not str(row.get("consent") or "").strip():
        reasons.append("consent")
    received = row.get("received_product")
    if received not in RECEIVED:
        reasons.append("received_product")
    elif row.get("source_type") == "creator_submission" and received not in ("free", "purchased", "none"):
        reasons.append("received_product")
    if row.get("source_type") == "internal_staff_test" and not str(row.get("disclosure") or "").strip():
        reasons.append("disclosure")
    persona = str(row.get("persona_handle") or "").strip()
    if persona and not _PERSONA.match(persona):
        reasons.append("persona_handle")
    if quote and claim_gate_failures(quote):
        reasons.append("claim_gate")
    return reasons


def disclosure_lines(row):
    lines = []
    if row.get("received_product") == "free":
        lines.append(FREE_DISCLOSURE)
    extra = str(row.get("disclosure") or "").strip()
    if extra and extra not in lines:
        lines.append(extra)
    return lines


def _matches_article(row, text):
    handle = str(row.get("product") or "").strip().lower()
    if handle not in product_handles(text):
        return False
    blob = topic_blob(text)
    tags = row.get("topic_tags") if isinstance(row.get("topic_tags"), list) else []
    return any(_has_phrase(blob, tag) for tag in tags if isinstance(tag, str))


def _sort_key(row, hits):
    parts = str(row.get("date") or "").split("-")
    try:
        nums = tuple(int(part) for part in parts)
    except ValueError:
        nums = (0, 0, 0)
    return (-hits, tuple(-num for num in nums), str(row.get("id") or ""))


def select(text, rows=None):
    """Eligible quotes for this article, capped at two. Newest matching date first."""
    if rows is None:
        rows = load_quotes()
    blob = topic_blob(text)
    matched = []
    for row in rows:
        if eligibility_problems(row) or not _matches_article(row, text):
            continue
        tags = row.get("topic_tags") or []
        hits = sum(1 for tag in tags if isinstance(tag, str) and _has_phrase(blob, tag))
        matched.append((_sort_key(row, hits), row))
    matched.sort(key=lambda item: item[0])
    return [row for _key, row in matched[:MAX_QUOTES]]


def render_block(rows):
    """HTML for rows the caller already selected. Empty when rows is empty."""
    if not rows:
        return ""
    parts = [
        '<aside data-gs-experience="block" style="border-left:4px solid #1e3a29;'
        'background:#f6fbf5;border-radius:8px;padding:16px 20px;margin:28px 0;">',
        '<p style="margin:0 0 10px;font-weight:700;color:#1e3a29;">First-hand notes</p>',
    ]
    for row in rows:
        quote = html.escape(normalize_ws(str(row.get("quote") or "")), quote=True)
        attribution = html.escape(str(row.get("attribution") or "").strip(), quote=True)
        label = html.escape(SOURCE_LABEL.get(row.get("source_type"), ""), quote=True)
        date = html.escape(str(row.get("date") or "").strip(), quote=True)
        qid = html.escape(str(row.get("id") or "").strip(), quote=True)
        parts.append(
            '<blockquote data-gs-experience="quote" data-gs-quote-id="%s" '
            'style="margin:0 0 14px;padding:0;border:0;">' % qid
        )
        parts.append('<p style="margin:0 0 6px;">“%s”</p>' % quote)
        footer = "%s · %s · %s" % (attribution, label, date)
        url = str(row.get("source_url") or "").strip()
        if url:
            footer += ' · <a href="%s">Source</a>' % html.escape(url, quote=True)
        else:
            footer += " · Source ID: " + html.escape(str(row.get("source_id") or "").strip(), quote=True)
        parts.append('<footer style="margin:0;color:#444444;font-size:.95em;">%s</footer>' % footer)
        for line in disclosure_lines(row):
            parts.append(
                '<p data-gs-experience="disclosure" style="margin:6px 0 0;color:#1e3a29;font-size:.95em;">%s</p>'
                % html.escape(line, quote=True)
            )
        parts.append("</blockquote>")
    parts.append("</aside>")
    return "\n".join(parts)


def render_method(text, root=None):
    line = method_line(text, root=root)
    if not line:
        return ""
    return '<p data-gs-experience="method">%s</p>' % html.escape(line)


def render(text, rows=None, with_method=False, root=None):
    """Quote block, plus the method line when with_method is set and one exists."""
    chunks = []
    block = render_block(select(text, rows))
    if block:
        chunks.append(block)
    if with_method:
        method = render_method(text, root=root)
        if method:
            chunks.append(method)
    if not chunks:
        return ""
    return "\n\n" + "\n\n".join(chunks) + "\n\n"


def lint_catalog(rows=None):
    """Problems on real rows. Example rows are skipped."""
    if rows is None:
        rows = load_quotes()
    errors = []
    seen = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append("#%s: row" % index)
            continue
        ident = str(row.get("id") or ("#%s" % index))
        if row.get("example") is True:
            if not _ID.match(str(row.get("id") or "")):
                errors.append("%s: example row needs an id" % ident)
            continue
        if ident in seen:
            errors.append("%s: duplicate id" % ident)
        seen.add(ident)
        problems = eligibility_problems(row)
        if problems:
            errors.append("%s: %s" % (ident, ", ".join(problems)))
    return errors


def _strip_blocks(text):
    text = _ASIDE.sub(" ", text or "")
    text = _METHOD.sub(" ", text)
    return text


def _unwrap_quotes(text):
    text = normalize_ws(text)
    if len(text) >= 2 and text[0] in "\"“" and text[-1] in "\"”":
        return normalize_ws(text[1:-1])
    return text


def _quote_paragraph(inner):
    for match in re.finditer(r"<p\b([^>]*)>(.*?)</p>", inner, re.I | re.S):
        if re.search(r"data-gs-experience\s*=\s*[\"']disclosure[\"']", match.group(1), re.I):
            continue
        return _unwrap_quotes(_plain(match.group(2)))
    return ""


def _quote_id(attrs):
    match = re.search(r"data-gs-quote-id\s*=\s*[\"']([^\"']+)[\"']", attrs or "", re.I)
    return match.group(1) if match else ""


def _index(rows):
    found = {}
    for row in rows:
        if isinstance(row, dict) and row.get("id"):
            found.setdefault(str(row["id"]), row)
    return found


_AUTHOR_LINK = re.compile(
    r"\[([^\]]+)\]\((?:https?://wellnessnest\.co)?/pages/[a-z0-9-]+\)"
    r"|<a[^>]+href=[\"'](?:https?://wellnessnest\.co)?/pages/[a-z0-9-]+[\"'][^>]*>([^<]+)</a>",
    re.I,
)


def _author_names(text):
    section = _AUTHOR_SECTION.search(text or "")
    if not section:
        return []
    names = []
    for match in _AUTHOR_LINK.finditer(section.group(1)):
        names.append(normalize_ws(html.unescape(match.group(1) or match.group(2) or "")))
    return [name for name in names if len(name.split()) >= 2]


def _testimonial_failures(text):
    raw = _strip_blocks(text)
    plain = _plain(raw)
    fails = []
    if _STAR.search(plain):
        fails.append("star rating or review score outside the experience evidence")
    if _TESTIMONIAL_PHRASE.search(plain):
        fails.append("testimonial heading or verified-buyer line outside the experience evidence")
    if _MD_QUOTE.search(raw) or _BARE_BQ.search(raw):
        fails.append("blockquote is not an evidence quote")
    for match in _ATTR_QUOTE.finditer(plain):
        quoted = match.group(1)
        if _FIRST_PERSON.search(quoted) or _TESTIMONIAL_PHRASE.search(match.group(0)):
            fails.append("attributed testimonial is not in the experience evidence")
            break
    if _PERSONAL.search(plain):
        fails.append("personal-use claim is not backed by an evidence quote")
    for name in _author_names(raw):
        for found in re.finditer(re.escape(name), plain):
            window = plain[max(0, found.start() - 80):found.end() + 80]
            if _NAME_USE.search(window):
                fails.append(
                    "bylines must not say %s used the product unless that sentence is an evidence quote"
                    % name
                )
                break
    if re.search(r"data-gs-experience\s*=\s*[\"']quote[\"']", raw, re.I):
        fails.append("experience quote sits outside the evidence block")
    return fails


def _method_failures(text, root=None):
    grounded = method_line(text, root=root)
    fails = []
    rendered = [_plain(match.group(1)) for match in _METHOD.finditer(text or "")]
    for line in rendered:
        if line != grounded:
            fails.append("method line is not the label check this article gate runs")
    plain = _plain(text or "")
    if re.search(r"How we checked", plain, re.I):
        leftover = plain.replace(grounded, "", 1) if grounded else plain
        if not grounded or grounded not in plain or re.search(r"How we checked", leftover, re.I):
            fails.append("How we checked this does not match the label check this article gate runs")
    return fails


def _rendered_quote_failures(text, rows):
    fails = []
    asides = list(_ASIDE.finditer(text or ""))
    nodes = []
    for aside in asides:
        nodes.extend(_QUOTE_NODE.finditer(aside.group(0)))
        if not _QUOTE_NODE.search(aside.group(0)):
            fails.append("experience block is empty")
    outside = _strip_blocks(text or "")
    if _QUOTE_NODE.search(outside):
        fails.append("experience quote sits outside the evidence block")
    if len(nodes) > MAX_QUOTES:
        fails.append("experience block has %s quotes (cap is %s)" % (len(nodes), MAX_QUOTES))
    catalog = _index(rows)
    seen = set()
    for node in nodes:
        qid = _quote_id(node.group(1))
        if not qid:
            fails.append("rendered experience quote has no data-gs-quote-id")
            continue
        if qid in seen:
            fails.append("experience quote %s is repeated" % qid)
        seen.add(qid)
        row = catalog.get(qid)
        if row is None:
            fails.append("experience quote %s is not in the evidence file" % qid)
            continue
        problems = eligibility_problems(row)
        if problems:
            detail = ""
            if "claim_gate" in problems:
                gate = claim_gate_failures(str(row.get("quote") or ""))
                if gate:
                    detail = ": " + gate[0][:160]
            fails.append(
                "experience quote %s is not eligible (%s)%s" % (qid, ", ".join(problems), detail)
            )
            continue
        if not _matches_article(row, text):
            fails.append("experience quote %s does not match this article's product and topic" % qid)
            continue
        inner = node.group(2)
        got = _quote_paragraph(inner)
        want = normalize_ws(str(row.get("quote") or ""))
        if got != want:
            fails.append("experience quote %s text does not match the evidence file" % qid)
        footer_match = re.search(r"<footer\b[^>]*>(.*?)</footer>", inner, re.I | re.S)
        footer = _plain(footer_match.group(1)) if footer_match else ""
        attribution = normalize_ws(str(row.get("attribution") or ""))
        if attribution not in footer:
            fails.append("experience quote %s is missing its attribution" % qid)
        date = str(row.get("date") or "").strip()
        if date not in footer:
            fails.append("experience quote %s is missing its date" % qid)
        label = SOURCE_LABEL.get(row.get("source_type"), "")
        if label not in footer:
            fails.append("experience quote %s is missing its source type" % qid)
        url = str(row.get("source_url") or "").strip()
        hrefs = [html.unescape(href) for href in re.findall(r'href\s*=\s*["\']([^"\']+)["\']', inner, re.I)]
        if url:
            if url not in hrefs:
                fails.append("experience quote %s is missing its source URL" % qid)
        else:
            source_id = str(row.get("source_id") or "").strip()
            if ("Source ID: " + source_id) not in footer:
                fails.append("experience quote %s is missing its source ID" % qid)
        disclosed = [
            _plain(match.group(1))
            for match in re.finditer(
                r"<p\b[^>]*data-gs-experience\s*=\s*[\"']disclosure[\"'][^>]*>(.*?)</p>",
                inner,
                re.I | re.S,
            )
        ]
        required = disclosure_lines(row)
        for line in required:
            if line not in disclosed:
                fails.append("experience quote %s is missing the disclosure %r" % (qid, line))
        for line in disclosed:
            if line not in required:
                fails.append("experience quote %s has a disclosure that is not in the evidence file" % qid)
    return fails


def audit(text, rows=None, root=None):
    """Return (fails, warns). Warns when the quote block is absent. Does not fetch."""
    if rows is None:
        rows = load_quotes()
    text = text or ""
    fails = []
    fails.extend(_testimonial_failures(text))
    fails.extend(_method_failures(text, root=root))
    fails.extend(_rendered_quote_failures(text, rows))
    warns = []
    quote_rendered = bool(_QUOTE_NODE.search(text))
    if not quote_rendered and not _ASIDE.search(text):
        eligible = select(text, rows)
        if eligible:
            warns.append(
                "experience coverage: no first-hand block (%s eligible quote%s not rendered)"
                % (len(eligible), "" if len(eligible) == 1 else "s")
            )
        else:
            warns.append(COVERAGE_WARN)
    return fails, warns


def _read_draft(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def main(argv=None):
    parser = argparse.ArgumentParser(description="First-hand experience block (evidence file only).")
    sub = parser.add_subparsers(dest="command")
    render_parser = sub.add_parser("render", help="print the block, or nothing when there is no eligible quote")
    render_parser.add_argument("--draft", required=True)
    render_parser.add_argument("--with-method", action="store_true")
    audit_parser = sub.add_parser("audit", help="exit 1 when the draft fails the experience gate")
    audit_parser.add_argument("--draft", required=True)
    sub.add_parser("lint", help="exit 1 when a non-example row is not eligible")
    args = parser.parse_args(argv)
    if args.command == "render":
        sys.stdout.write(render(_read_draft(args.draft), with_method=args.with_method))
        return 0
    if args.command == "audit":
        fails, warns = audit(_read_draft(args.draft))
        for warning in warns:
            print("WARN " + warning)
        for fail in fails:
            print("FAIL " + fail)
        return 1 if fails else 0
    if args.command == "lint":
        errors = lint_catalog()
        for error in errors:
            print("FAIL " + error)
        if errors:
            return 1
        rows = load_quotes()
        real = sum(1 for row in rows if row.get("example") is not True)
        print("experience quotes: %s example, %s renderable" % (len(rows) - real, real))
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

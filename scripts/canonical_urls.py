#!/usr/bin/env python3
"""Canonical URL consistency for content GenSeo writes.

Google uses the chosen canonical as the URL it can cite in AI Overviews and
AI Mode (Search Engine Land, "Canonicalization and SEO: A guide for 2027",
2026-10-16, noted in the 2026-10-17 SEL digest). Internal links, the URL we
publish, and any Article JSON-LD GenSeo emits have to name that same clean URL.

Policy
------
AUTOFIX, applied by the publisher before the Shopify request (not a hard fail):
  http→https, strip www, lower-case the host and path, collapse repeated
  slashes, drop a trailing slash on a non-home path, drop tracking and variant
  parameters, rewrite /collections/<c>/products/<handle> to /products/<handle>.

WARN, left unchanged (ambiguous):
  a locale prefix (/fr/products/..., /es-es/blogs/...), any other query parameter.

FAIL (validate_article via geo_citability.assess; the publisher aborts too):
  a GenSeo Article / BlogPosting / NewsArticle mainEntityOfPage, url, or @id
  whose cleaned form is not the article URL. Homepage, product, collection,
  and other-article targets fail. A cosmetic mismatch with a known canonical
  is an autofix, not a fail. Theme JSON-LD is never a fail (draft PR #65).

The homepage is already canonical both with and without a trailing slash
(live tag is https://wellnessnest.co/). Mentioning the bare origin is not a finding.

geo_official_lint prints the same findings and still exits 0.
This module does not call Shopify.
"""
import html as htmlmod
import json
import re
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

HOST = "wellnessnest.co"
ORIGIN = "https://wellnessnest.co"
HOME = "https://wellnessnest.co/"
SOURCE = "https://searchengineland.com/canonicalization-seo-448161"
AUDIT_UA = "GenSeoCanonicalAudit/1.0 (+https://wellnessnest.co; read-only)"

SECTIONS = ("products", "collections", "blogs", "pages", "policies")
ARTICLE_TYPES = {"Article", "BlogPosting", "NewsArticle"}
# Parameters that are not the page. variant is a Shopify duplicate URL.
STRIP_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_name", "utm_cid", "utm_reader", "utm_viz_id", "utm_pubreferrer",
    "gclid", "gbraid", "wbraid", "dclid", "gclsrc", "fbclid", "msclkid",
    "ttclid", "twclid", "li_fat_id", "igshid", "mc_cid", "mc_eid", "srsltid",
    "yclid", "_ga", "_gl", "_kx", "gad_source", "gad_campaignid",
    "variant", "variants", "selling_plan",
    "pr_prod_strat", "pr_rec_id", "pr_ref_pid", "pr_seq", "pr_rec_pid", "pb",
}
_ASSET_EXT = (
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif", ".css", ".js",
    ".json", ".xml", ".atom", ".map", ".ico", ".pdf", ".mp4", ".webm",
)
_LOCALE = re.compile(r"^[a-z]{2}(?:-[a-z]{2})?$")
_COLL_PROD = re.compile(r"^/collections/([^/]+)/products/([^/]+)$")
_ARTICLE_PATH = re.compile(r"^/blogs/[^/]+/[^/]+$")
_PLAIN = re.compile(
    r"(?i)(?<![\w/])(?:"
    r"https?://(?:www\.)?wellnessnest\.co[^\s\"'<>)\\]*"
    r"|//(?:www\.)?wellnessnest\.co[^\s\"'<>)\\]*"
    r"|/(?:[a-z]{2}(?:-[a-z]{2})?/)?(?:products|collections|blogs|pages|policies)"
    r"(?:/[^\s\"'<>)\\]*)?"
    r")"
)
_FENCE = re.compile(r"(?s)```.*?```|`[^`\n]+`")
_SCRIPT = re.compile(r"(?is)<script\b([^>]*)>(.*?)</script>")
_STYLE = re.compile(r"(?is)<style\b[^>]*>.*?</style>")
_TRAIL = ".,;:"
_URL_CONT = re.compile(r"[A-Za-z0-9\-._~%:/?#\[\]@!$&'()*+,;=]")


def _strip_dropped(name):
    low = (name or "").lower()
    return low in STRIP_PARAMS or low.startswith("utm_")


def _logical(raw):
    text = htmlmod.unescape((raw or "").strip()).replace("\\/", "/")
    return text


def _home_path(path):
    return path in ("", "/")


def _section_of(path):
    """Return (locale or '', section or 'home' or '')."""
    parts = [p for p in path.split("/") if p]
    if not parts:
        return "", "home"
    if _LOCALE.match(parts[0].lower()) and len(parts) > 1 and parts[1].lower() in SECTIONS:
        return parts[0].lower(), parts[1].lower()
    if parts[0].lower() in SECTIONS:
        return "", parts[0].lower()
    if _home_path(path):
        return "", "home"
    return "", ""


def classify_link(raw):
    """Classify one wellnessnest URL. Does not rewrite locale-prefixed URLs.

    Returns a dict with action ignore|ok|autofix|warn, normalised (or None),
    rules, message, key (cleaned absolute form without a collection rewrite),
    collection_product, parameterised, locale.
    """
    original = raw or ""
    logical = _logical(original)
    trailing = ""
    while logical and logical[-1] in _TRAIL:
        trailing = logical[-1] + trailing
        logical = logical[:-1]
    empty = {
        "action": "ignore", "normalised": None, "rules": [], "message": "",
        "key": "", "collection_product": False, "parameterised": False,
        "locale": "", "original": original, "logical": logical,
    }
    if not logical:
        return empty
    relative = logical.startswith("/") and not logical.startswith("//")
    probe = logical
    if relative:
        probe = ORIGIN + logical
    elif logical.startswith("//"):
        probe = "https:" + logical
    parts = urlsplit(probe)
    host = (parts.hostname or "").lower()
    www = host.startswith("www.")
    if www:
        host = host[4:]
    if host != HOST:
        return empty
    path = parts.path or ""
    path = re.sub(r"/{2,}", "/", path)
    if path and not path.startswith("/"):
        path = "/" + path
    repeated = "//" in (parts.path or "")
    low_path = path.lower()
    case_change = low_path != path
    path = low_path
    locale, section = _section_of(path)
    if not section:
        return empty
    base_path = path
    if locale:
        base_path = "/" + "/".join(path.split("/")[2:])
        if not base_path.startswith("/"):
            base_path = "/" + base_path
    if any(base_path.lower().endswith(ext) for ext in _ASSET_EXT):
        return empty
    if base_path.startswith("/cdn/") or "/cdn/" in base_path:
        return empty

    bare = path[:-1] if path.endswith("/") and path != "/" else path
    if locale:
        bare_noloc = bare[len("/" + locale):] if bare.startswith("/" + locale + "/") else bare
    else:
        bare_noloc = bare
    coll = _COLL_PROD.match(bare_noloc)
    collection_product = bool(coll)

    pairs = parse_qsl(parts.query, keep_blank_values=True)
    dropped = []
    kept = []
    for key, val in pairs:
        if _strip_dropped(key):
            dropped.append(key.lower())
        else:
            kept.append((key, val))
    unknown = [key for key, _val in kept]

    rules = []
    scheme_host = (not relative) and (
        logical.lower().startswith("http://")
        or logical.startswith("//")
        or www
        or (parts.hostname or "") != (parts.hostname or "").lower()
        or (parts.hostname or "").lower() not in (HOST,)
    )
    if scheme_host:
        rules.append("scheme-host")
    if case_change:
        rules.append("letter-case")
    if repeated:
        rules.append("repeated-slash")
    slash = path.endswith("/") and not _home_path(path)
    if slash:
        rules.append("trailing-slash")
        path = path[:-1]
    if dropped:
        rules.append("drop-param")
    if collection_product and not locale:
        rules.append("collection-product-path")
        path = "/products/" + coll.group(2).lower()
    if unknown:
        rules.append("unknown-query")
    if locale:
        rules.append("locale-prefix")

    # Homepage slash is already canonical either way. Don't invent a rewrite
    # that only adds or removes it.
    home_only = _home_path(path) and not any(
        r in rules for r in (
            "scheme-host", "letter-case", "repeated-slash", "drop-param",
            "unknown-query", "locale-prefix", "collection-product-path",
        )
    )
    if home_only:
        rules = [r for r in rules if r != "trailing-slash"]

    key_path = path if not _home_path(path) else "/"
    query = urlencode(kept, doseq=True)
    fragment = parts.fragment
    if _home_path(key_path):
        absolute = HOME
    else:
        absolute = ORIGIN + key_path
    if query:
        absolute += "?" + query
    key = absolute
    display = absolute
    if fragment:
        display += "#" + fragment
    if relative and "scheme-host" not in rules and not logical.startswith("//"):
        rel = key_path if not _home_path(key_path) else "/"
        display = rel
        if query:
            display += "?" + query
        if fragment:
            display += "#" + fragment

    parameterised = bool(parts.query)
    info = {
        "action": "ok", "normalised": None, "rules": rules, "message": "",
        "key": key.split("#", 1)[0], "collection_product": collection_product,
        "parameterised": parameterised, "locale": locale, "original": original,
        "logical": logical, "dropped": dropped, "unknown": unknown,
    }
    if "locale-prefix" in rules:
        extra = ""
        if "drop-param" in rules:
            extra = " Locale prefix is ambiguous, so tracking parameters were not stripped."
        info["action"] = "warn"
        info["message"] = "locale-prefix: %s left unchanged.%s" % (logical, extra)
        return info
    autofix_rules = [r for r in rules if r not in ("unknown-query",)]
    if not autofix_rules and "unknown-query" in rules:
        names = ", ".join(unknown)
        info["action"] = "warn"
        info["message"] = "unknown-query (%s): %s left unchanged" % (names, logical)
        return info
    if not autofix_rules:
        info["rules"] = []
        return info
    info["action"] = "autofix"
    info["normalised"] = display
    bits = [r for r in ("scheme-host", "letter-case", "repeated-slash", "trailing-slash", "collection-product-path") if r in rules]
    if dropped:
        bits.append("drop-param (%s)" % ", ".join(dropped))
    info["message"] = "%s: %s → %s" % (", ".join(bits), logical, display)
    if unknown:
        info["also_warn"] = "unknown-query (%s): %s still has %s" % (
            ", ".join(unknown), display, ", ".join(unknown))
    return info


def _ranges(text):
    spans = []
    for rx, kind in ((_FENCE, "fence"), (_STYLE, "style"), (_SCRIPT, "script")):
        for match in rx.finditer(text):
            spans.append((match.start(), match.end(), kind, match))
    spans.sort()
    return spans


def _inside(pos, spans):
    for start, end, _kind, _match in spans:
        if start <= pos < end:
            return True
        if start > pos:
            return False
    return False


def _substitute(blob, old, new):
    """Replace old URL text, including JSON \\/ escaping, without eating a longer path."""
    if not old or old == new:
        return blob, 0
    total = 0
    pairs = []
    escaped_old = old.replace("/", "\\/")
    escaped_new = new.replace("/", "\\/")
    if "\\/" in blob and escaped_old != old:
        pairs.append((escaped_old, escaped_new))
    pairs.append((old, new))
    amp_old = old.replace("&", "&amp;")
    if amp_old != old:
        pairs.append((amp_old, new.replace("&", "&amp;")))
    for src, dst in pairs:
        if src == dst or src not in blob:
            continue
        pattern = re.compile(re.escape(src) + r"(?!" + _URL_CONT.pattern + r")")
        blob, count = pattern.subn(lambda _m, dest=dst: dest, blob)
        total += count
    return blob, total


def _types_of(node):
    kind = node.get("@type")
    if isinstance(kind, str):
        return [kind]
    if isinstance(kind, list):
        return [item for item in kind if isinstance(item, str)]
    return []


def _walk_articles(node, found):
    if isinstance(node, dict):
        if ARTICLE_TYPES.intersection(_types_of(node)):
            found.append(node)
        for value in node.values():
            _walk_articles(value, found)
    elif isinstance(node, list):
        for value in node:
            _walk_articles(value, found)


def _identity_refs(node):
    refs = []
    for key in ("@id", "url", "mainEntityOfPage"):
        if key not in node:
            continue
        value = node[key]
        if isinstance(value, str):
            refs.append((key, value))
        elif isinstance(value, dict):
            for inner in ("@id", "url"):
                if isinstance(value.get(inner), str):
                    refs.append(("%s.%s" % (key, inner), value[inner]))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    refs.append((key, item))
                elif isinstance(item, dict):
                    for inner in ("@id", "url"):
                        if isinstance(item.get(inner), str):
                            refs.append(("%s.%s" % (key, inner), item[inner]))
    return refs


def _preferred(url):
    """Absolute cleaned form used for identity comparison. None if not governed."""
    info = classify_link(url)
    if info["action"] == "ignore" and not info["key"]:
        # classify returns ignore for non-store URLs with an empty key
        if not info["logical"]:
            return None
        logical = info["logical"]
        if logical.startswith("/") or "wellnessnest.co" in logical.lower() or logical.startswith("//"):
            return None
        return None
    if not info["key"] and info["action"] == "ignore":
        return None
    if info["action"] == "ignore":
        return None
    # Rebuild the identity key: no collection rewrite, locale kept, tracking dropped.
    logical = info["logical"]
    relative = logical.startswith("/") and not logical.startswith("//")
    probe = ORIGIN + logical if relative else ("https:" + logical if logical.startswith("//") else logical)
    parts = urlsplit(probe)
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    path = path.lower()
    if path.endswith("/") and path != "/":
        path = path[:-1]
    if path in ("", "/"):
        path = "/"
    locale, section = _section_of(path if path != "/" else "/")
    if not section and path != "/":
        return None
    pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not _strip_dropped(k)]
    base = HOME if path == "/" else ORIGIN + path
    if pairs:
        base += "?" + urlencode(pairs, doseq=True)
    return base


def preferred_url(url):
    """Absolute cleaned URL for comparison. Collection paths are not rewritten."""
    return _preferred(url)


def cleaned_url(url):
    """Comparable https URL for any path on this host.

    Drops www, a trailing slash (the site root stays ``/``), and tracking
    parameters. Locale prefixes and collection paths stay. Empty when the
    host is not wellnessnest.co.
    """
    logical = _logical(url)
    if not logical:
        return ""
    if logical.startswith("/") and not logical.startswith("//"):
        logical = ORIGIN + logical
    elif logical.startswith("//"):
        logical = "https:" + logical
    parts = urlsplit(logical)
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host != HOST:
        return ""
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    path = path.lower() or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    pairs = [(key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True) if not _strip_dropped(key)]
    out = "https://%s%s" % (HOST, path)
    if pairs:
        out += "?" + urlencode(pairs, doseq=True)
    return out


identity_refs = _identity_refs


def _is_home_key(key):
    if not key:
        return False
    parts = urlsplit(key)
    return (parts.hostname or "").lower().endswith(HOST) and _home_path(parts.path) and not parts.query


def _is_article_key(key):
    if not key:
        return False
    parts = urlsplit(key)
    if (parts.hostname or "").lower() != HOST:
        return False
    return bool(_ARTICLE_PATH.match(parts.path or "")) and not parts.query


def _spell_ok(logical, target):
    """True when the raw identity string already is the target spelling.

    The homepage is accepted with or without a trailing slash. Any other
    difference, including a fragment, is rewritten.
    """
    left = _logical(logical).split("#", 1)[0]
    right = _logical(target).split("#", 1)[0]
    if "#" in _logical(logical) or "#" in _logical(target):
        if _logical(logical) != _logical(target):
            return False
    if left == right:
        return True
    return bool(_is_home_key(_preferred(left) or "") and _is_home_key(_preferred(right) or ""))


def _article_identity(node, canonical):
    """Findings for one Article node's identity fields. Does not rewrite."""
    findings = []
    refs = _identity_refs(node)
    if not refs:
        return findings
    canon_key = _preferred(canonical) if canonical else ""
    parsed = []
    for field, raw in refs:
        key = _preferred(raw)
        parsed.append((field, raw, key))
    keys = {key for _field, _raw, key in parsed if key}
    disagree = len(keys) > 1 and canon_key == ""
    for field, raw, key in parsed:
        logical = _logical(raw)
        if not key:
            findings.append({
                "severity": "fail",
                "rule": "canonical-mismatch",
                "message": "Article %s %s is not a wellnessnest.co URL" % (field, logical),
                "original": logical, "normalised": None,
            })
            continue
        if disagree:
            findings.append({
                "severity": "fail",
                "rule": "canonical-mismatch",
                "message": "Article identity fields disagree (%s is %s)" % (field, key),
                "original": logical, "normalised": None,
            })
            continue
        if canon_key:
            if key == canon_key:
                target = _logical(canonical).split("#", 1)[0]
                if not _spell_ok(logical, target):
                    findings.append(_autofix_identity(field, logical.split("#", 1)[0], target))
                continue
            findings.append({
                "severity": "fail",
                "rule": "canonical-mismatch",
                "message": "Article %s %s does not equal canonical %s" % (field, key, canon_key),
                "original": logical, "normalised": None,
            })
            continue
        # No known canonical (pre-publish draft).
        if _is_home_key(key):
            findings.append({
                "severity": "fail",
                "rule": "canonical-mismatch",
                "message": "Article %s %s points at the homepage, not the article" % (field, key),
                "original": logical, "normalised": None,
            })
            continue
        if not _is_article_key(key):
            locale, section = _section_of(urlsplit(key).path or "/")
            if locale and _is_article_key(ORIGIN + urlsplit(key).path[len("/" + locale):]):
                findings.append({
                    "severity": "warn",
                    "rule": "canonical-ambiguous",
                    "message": "locale-prefix: Article %s %s left unchanged (publish handle is not known yet)" % (field, key),
                    "original": logical, "normalised": None,
                })
                continue
            findings.append({
                "severity": "fail",
                "rule": "canonical-mismatch",
                "message": "Article %s %s is not the article URL" % (field, key),
                "original": logical, "normalised": None,
            })
            continue
        if urlsplit(key).query:
            findings.append({
                "severity": "warn",
                "rule": "canonical-ambiguous",
                "message": "unknown-query: Article %s %s left unchanged" % (field, key),
                "original": logical, "normalised": None,
            })
            continue
        if not _spell_ok(logical, key):
            findings.append(_autofix_identity(field, logical.split("#", 1)[0], key))
    return findings


def _autofix_identity(field, logical, target):
    return {
        "severity": "autofix",
        "rule": "canonical-autofix",
        "message": "Article %s %s → %s" % (field, logical, target),
        "original": logical,
        "normalised": target,
    }


def _json_strings(node, acc):
    if isinstance(node, dict):
        for value in node.values():
            _json_strings(value, acc)
    elif isinstance(node, list):
        for value in node:
            _json_strings(value, acc)
    elif isinstance(node, str):
        acc.append(node)


def rewrite_jsonld(body, canonical=None):
    """Return (new_body, findings). Identity failures are not rewritten."""
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return body, [{
            "severity": "warn",
            "rule": "canonical-ambiguous",
            "message": "JSON-LD block could not be parsed; left unchanged",
            "original": "", "normalised": None,
        }]
    articles = []
    _walk_articles(data, articles)
    findings = []
    handled = set()
    replacements = []
    for node in articles:
        for finding in _article_identity(node, canonical):
            findings.append(finding)
            if finding["severity"] == "autofix" and finding.get("original") and finding.get("normalised"):
                replacements.append((finding["original"], finding["normalised"]))
                handled.add(finding["original"])
            elif finding.get("original"):
                handled.add(_logical(finding["original"]))
    strings = []
    _json_strings(data, strings)
    for text in strings:
        if text in handled or _logical(text) in handled:
            continue
        candidates = []
        if "wellnessnest.co" in text.lower() or text.startswith("/"):
            if text.startswith("http") or text.startswith("//") or text.startswith("/"):
                candidates.append(text)
            else:
                for match in _PLAIN.finditer(text):
                    candidates.append(match.group(0))
        for cand in candidates:
            info = classify_link(cand)
            if info["action"] == "autofix" and info["normalised"]:
                findings.append({
                    "severity": "autofix",
                    "rule": "canonical-autofix",
                    "message": info["message"],
                    "original": info["logical"],
                    "normalised": info["normalised"],
                })
                replacements.append((info["logical"], info["normalised"]))
                if info.get("also_warn"):
                    findings.append({
                        "severity": "warn",
                        "rule": "canonical-ambiguous",
                        "message": info["also_warn"],
                        "original": info["logical"],
                        "normalised": info["normalised"],
                    })
            elif info["action"] == "warn":
                findings.append({
                    "severity": "warn",
                    "rule": "canonical-ambiguous",
                    "message": info["message"],
                    "original": info["logical"],
                    "normalised": None,
                })
    blob = body
    seen = set()
    for old, new in sorted(replacements, key=lambda pair: len(pair[0]), reverse=True):
        if (old, new) in seen:
            continue
        seen.add((old, new))
        blob, _count = _substitute(blob, old, new)
    return blob, findings


def iter_findings(text, canonical=None):
    """Every autofix, warn, and fail in a draft or article body. Theme not included."""
    text = text or ""
    spans = _ranges(text)
    findings = []
    # JSON-LD bodies first, using original indices.
    json_spans = []
    for match in _SCRIPT.finditer(text):
        attrs, body = match.group(1), match.group(2)
        if not re.search(r"(?i)type\s*=\s*['\"]application/ld\+json['\"]", attrs):
            continue
        if _inside(match.start(), [s for s in spans if s[2] == "fence"]):
            continue
        new_body, found = rewrite_jsonld(body, canonical)
        findings.extend(found)
        json_spans.append((match.start(2), match.end(2), new_body))
    rebuilt = text
    for start, end, new_body in sorted(json_spans, key=lambda item: item[0], reverse=True):
        rebuilt = rebuilt[:start] + new_body + rebuilt[end:]
    spans = _ranges(rebuilt)
    seen_warn = set()
    for match in _PLAIN.finditer(rebuilt):
        if _inside(match.start(), spans):
            continue
        raw = match.group(0)
        cut = raw
        while cut and cut[-1] in _TRAIL:
            cut = cut[:-1]
        info = classify_link(cut)
        if info["action"] == "autofix":
            findings.append({
                "severity": "autofix",
                "rule": "canonical-autofix",
                "message": info["message"],
                "original": info["logical"],
                "normalised": info["normalised"],
                "start": match.start(),
                "end": match.start() + len(cut),
            })
            if info.get("also_warn") and info["also_warn"] not in seen_warn:
                seen_warn.add(info["also_warn"])
                findings.append({
                    "severity": "warn",
                    "rule": "canonical-ambiguous",
                    "message": info["also_warn"],
                    "original": info["logical"],
                    "normalised": info["normalised"],
                })
        elif info["action"] == "warn" and info["message"] not in seen_warn:
            seen_warn.add(info["message"])
            findings.append({
                "severity": "warn",
                "rule": "canonical-ambiguous",
                "message": info["message"],
                "original": info["logical"],
                "normalised": None,
            })
    return findings, rebuilt


def normalise_document(text, canonical=None):
    """Apply autofixes. Returns (text, change messages). Fails are not rewritten away."""
    findings, rebuilt = iter_findings(text, canonical)
    # iter_findings already rewrote JSON-LD autofixes inside `rebuilt`, but plain
    # link autofixes are only described. Apply those span replacements now.
    spans = []
    for finding in findings:
        if finding["severity"] == "autofix" and "start" in finding and finding.get("normalised"):
            spans.append(finding)
    out = rebuilt
    for finding in sorted(spans, key=lambda item: item["start"], reverse=True):
        start, end = finding["start"], finding["end"]
        original_slice = out[start:end]
        repl = finding["normalised"]
        if "\\/" in original_slice:
            repl = repl.replace("/", "\\/")
        elif "&amp;" in original_slice:
            repl = repl.replace("&", "&amp;")
        out = out[:start] + repl + out[end:]
    messages = []
    seen = set()
    for finding in findings:
        if finding["severity"] != "autofix":
            continue
        msg = finding["message"]
        if msg in seen:
            continue
        seen.add(msg)
        messages.append(msg)
    return out, messages


def gate_messages(text, canonical=None):
    """(fails, warns) for validate_article / geo_citability.assess.

    Autofix is a warning prefixed with 'canonical autofix on publish:'.
    It does not fail the draft; the publisher rewrites those links.
    """
    findings, _rebuilt = iter_findings(text, canonical)
    fails = []
    warns = []
    seen = set()
    for finding in findings:
        msg = finding["message"]
        if not msg or msg in seen:
            continue
        seen.add(msg)
        if finding["severity"] == "fail":
            fails.append(msg)
        elif finding["severity"] == "warn":
            warns.append(msg)
        elif finding["severity"] == "autofix":
            warns.append("canonical autofix on publish: " + msg)
    return fails, warns


def lint_warnings(text, canonical=None):
    """geo_official_lint rows. Mismatches are warnings here; the gate hard-fails them."""
    fails, warns = gate_messages(text, canonical)
    rows = []
    for msg in fails:
        rows.append({
            "rule": "canonical-mismatch",
            "msg": msg + " (hard-fails validate_article; this lint does not block)",
            "match": msg[:180],
            "source": SOURCE,
        })
    for msg in warns:
        rule = "canonical-autofix" if msg.startswith("canonical autofix") else "canonical-ambiguous"
        rows.append({"rule": rule, "msg": msg, "match": msg[:180], "source": SOURCE})
    return rows


def iter_store_links(html):
    """Governed wellnessnest URLs outside scripts, styles, and code fences."""
    spans = _ranges(html or "")
    for match in _PLAIN.finditer(html or ""):
        if _inside(match.start(), spans):
            continue
        raw = match.group(0)
        cut = raw
        while cut and cut[-1] in _TRAIL:
            cut = cut[:-1]
        info = classify_link(cut)
        if info["action"] == "ignore":
            continue
        info = dict(info)
        info["start"] = match.start()
        yield info


def page_canonical(html):
    for tag in re.findall(r"(?is)<link\b[^>]*>", html or ""):
        if not re.search(r"(?i)\brel\s*=\s*['\"][^'\"]*\bcanonical\b", tag):
            continue
        match = re.search(r"(?i)\bhref\s*=\s*['\"]([^'\"]+)", tag)
        if match:
            return htmlmod.unescape(match.group(1).strip())
    return ""


def extract_article_body(html):
    """GenSeo's article HTML, or None when this is not a blog article template.

    The theme's Article node is rendered after article-template__back. Cutting
    there keeps that node out of the publish gate (draft PR #65).
    """
    if not html:
        return None
    marker = html.find("article-template__content")
    if marker < 0:
        return None
    start = html.rfind("<div", 0, marker)
    if start < 0:
        start = marker
    end = html.find("article-template__back", marker)
    if end < 0:
        end = len(html)
    return html[start:end]


def jsonld_nodes(html):
    """(script_start, parsed_or_None) for each JSON-LD script."""
    nodes = []
    for match in _SCRIPT.finditer(html or ""):
        attrs, body = match.group(1), match.group(2)
        if not re.search(r"(?i)type\s*=\s*['\"]application/ld\+json['\"]", attrs):
            continue
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            nodes.append((match.start(), None))
            continue
        nodes.append((match.start(), data))
    return nodes


def article_nodes_in(data):
    found = []
    if data is not None:
        _walk_articles(data, found)
    return found


def score_page(html, canonical=""):
    """Split a live article page into a body gate result and a theme report.

    Theme notes never count as publish failures.
    """
    if not canonical:
        canonical = page_canonical(html)
    body = extract_article_body(html)
    fails, warns = ([], [])
    if body is not None:
        fails, warns = gate_messages(body, canonical=canonical or None)
    body_start = html.find(body) if body else -1
    body_end = body_start + len(body) if body else -1
    theme = []
    body_articles = 0
    theme_articles = 0
    canon_key = _preferred(canonical) if canonical else ""
    for start, data in jsonld_nodes(html):
        in_body = body is not None and body_start <= start < body_end
        for node in article_nodes_in(data):
            if in_body:
                body_articles += 1
            else:
                theme_articles += 1
            if in_body:
                continue
            for ref in _identity_refs(node):
                field, raw = ref
                key = _preferred(raw) or _logical(raw)
                matches = bool(canon_key) and key == canon_key
                if not matches:
                    theme.append(
                        "theme Article %s %s does not equal canonical %s"
                        % (field, key, canon_key or "(none)")
                    )
    if theme_articles and body_articles:
        theme.insert(
            0,
            "%d Article nodes on the page (%d in the article body, %d from the theme). "
            "The extra theme node is draft PR #65, not this gate."
            % (body_articles + theme_articles, body_articles, theme_articles)
        )
    elif theme_articles + body_articles > 1:
        theme.insert(
            0,
            "%d Article nodes (body %d, theme %d)."
            % (body_articles + theme_articles, body_articles, theme_articles)
        )
    return {
        "body_found": body is not None,
        "canonical": canonical,
        "fails": fails,
        "warns": warns,
        "theme": theme,
        "article_nodes_body": body_articles,
        "article_nodes_theme": theme_articles,
    }


def _fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": AUDIT_UA, "Accept": "text/html"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            body = res.read(2_000_001)
            return res.status, res.geturl(), body.decode("utf-8", "replace"), ""
    except urllib.error.HTTPError as exc:
        payload = exc.read(2_000_001).decode("utf-8", "replace")
        final = exc.geturl() if hasattr(exc, "geturl") else url
        return exc.code, final, payload, ""
    except Exception as exc:
        return 0, url, "", "%s: %s" % (type(exc).__name__, exc)


def dry_urls(urls, rate=1.0):
    """Read-only GET of live articles. Exit 1 when the body would hard-fail."""
    exit_code = 0
    last = 0.0
    reports = []
    for url in urls:
        wait = rate - (time.monotonic() - last)
        if last and wait > 0:
            time.sleep(wait)
        last = time.monotonic()
        status, final, html, err = _fetch(url)
        print("DRY %s  HTTP %s  final %s" % (url, status or err, final))
        if not html:
            print("  fetch failed: %s" % (err or status))
            exit_code = 1
            continue
        report = score_page(html)
        reports.append(report)
        if not report["body_found"]:
            print("  no article-template__content; theme JSON-LD was not scored as a draft")
            exit_code = 1
            continue
        print("  BODY fails %d  warns %d  (canonical %s)" % (
            len(report["fails"]), len(report["warns"]), report["canonical"]))
        for line in report["fails"]:
            print("  FAIL %s" % line)
        for line in report["warns"]:
            print("  WARN %s" % line)
        if report["theme"]:
            print("  THEME (report only, not a publish failure):")
            for line in report["theme"]:
                print("  - %s" % line)
        else:
            print("  THEME none")
        if report["fails"]:
            print("  RESULT body FAIL")
            exit_code = 1
        else:
            print("  RESULT body PASS")
    return exit_code, reports


def main(argv):
    if "--live" in argv or "--apply" in argv:
        print("canonical_urls: refusing --live/--apply. This tool does not write to Shopify.")
        return 2
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print("Usage: python3 scripts/canonical_urls.py --dry-url URL [--dry-url URL ...]")
        print("       python3 scripts/canonical_urls.py --file DRAFT [--canonical URL]")
        print("Read-only. Autofix is reported, not written, except --file prints the plan.")
        return 0
    urls = []
    path = ""
    canonical = ""
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg == "--dry-url" and i + 1 < len(argv):
            urls.append(argv[i + 1])
            i += 2
            continue
        if arg == "--file" and i + 1 < len(argv):
            path = argv[i + 1]
            i += 2
            continue
        if arg == "--canonical" and i + 1 < len(argv):
            canonical = argv[i + 1]
            i += 2
            continue
        print("unknown argument: %s" % arg)
        return 2
    if urls:
        code, _reports = dry_urls(urls)
        return code
    if path:
        with open(path, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        fails, warns = gate_messages(text, canonical or None)
        for line in fails:
            print("FAIL %s" % line)
        for line in warns:
            print("WARN %s" % line)
        print("fails %d  warns %d" % (len(fails), len(warns)))
        return 1 if fails else 0
    print("pass --dry-url or --file")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

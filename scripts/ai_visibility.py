#!/usr/bin/env python3
"""Mention vs citation ledger for Wellness Nest AI visibility.

brand_mentioned and domain_cited are independent. A cell with no observation
stays unknown. This module does not call an API unless adapt() is confirmed
and the key (and, except for the Gemini model already used in this repo, the
model name) is already in the environment.

  python3 scripts/aeo_tracker.py template --out /tmp/ai-visibility-template.json
  python3 scripts/aeo_tracker.py validate
  python3 scripts/aeo_tracker.py report
  python3 scripts/aeo_tracker.py self-check
  python3 scripts/aeo_tracker.py adapt --platform gemini --prompt-id <id>
"""
import argparse
import csv
import datetime
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "ai_visibility")
CATALOG_PATH = os.path.join(DATA_DIR, "prompt_set.json")
PATTERN_PATH = os.path.join(DATA_DIR, "competitor_patterns.json")
LEDGER_PATH = os.path.join(DATA_DIR, "observations.json")
TOPIC_BANK_PATH = os.path.join(ROOT, "templates", "article-topic-bank.json")
OFFPAGE_SEED_DIR = os.path.join(ROOT, "data", "offpage_seeds")

# Same model string the legacy Gemini call in aeo_tracker.py already uses.
GEMINI_MODEL_DEFAULT = "gemini-1.5-flash"
OUR_DOMAIN = "wellnessnest.co"
TRI = ("yes", "no", "unknown")
SCHEMA = 1
MAX_ERRORS = 40
SNIPPET_MAX = 500
NOTES_MAX = 800

COMMANDS = ("template", "validate", "report", "self-check", "adapt")

# Frozen query lists from draft PR #75 (data/offpage_seeds/*.json on
# cursor/offpage-listicle-gap-1020). self-check fails if prompt_set.json drifts.
AGEAURA_QUERIES = (
    "best NMN supplement",
    "best NMN supplement 2026",
    "best NMN with TMG",
    "NMN vs NR",
    "best NAD+ supplement 2026",
    "best NAD booster supplement",
    "best NMN capsules",
    "NMN and TMG together",
    "best NMN supplement reddit",
    "top NMN brands compared",
    "best liposomal NMN",
    "pure NMN supplement brand",
    "best NMN for longevity",
    "NMN TMG stack review",
    "best NMN supplement third party tested",
    "NAD+ precursor comparison NMN NR",
    "best NMN powder",
    "Wonderfeel vs Tru Niagen",
)
SHILASOURCE_QUERIES = (
    "best shilajit resin",
    "best shilajit gummies",
    "best shilajit supplement",
    "pure Himalayan shilajit brand",
    "best shilajit 2026",
    "best shilajit resin reddit",
    "shilajit resin vs gummies",
    "best authentic shilajit",
    "best shilajit for men",
    "legitimate shilajit brands",
    "best Himalayan shilajit resin",
    "best shilajit supplement 2026",
    "shilajit brands compared",
    "best third party tested shilajit",
    "pure shilajit resin brands",
    "best shilajit drops",
    "shilajit resin brands reddit",
    "best shilajit gummies 2026",
)

CITABILITY_FIX = (
    "On-page citability: the product brand was named and wellnessnest.co was absent "
    "from the source list. Start with that brand's product URL, then the article that "
    "answers the prompt. scripts/geo_citability.py (via validate_article.py) checks the "
    "opening answer, two question-style H2s, an FAQ block, a /products/ URL, a related "
    "/blogs/news/ article, a primary-source link, and a descriptive image alt. "
    "See docs/GEO_CITABILITY_AUDIT_2026-10-17.md. This tracker does not re-score those pages."
)

USAGE = """\
Usage:
  python3 scripts/aeo_tracker.py template --out <file.json|file.csv>
  python3 scripts/aeo_tracker.py validate [ledger.json|ledger.csv]
  python3 scripts/aeo_tracker.py report [--ledger FILE] [--format markdown|json] [--out FILE]
  python3 scripts/aeo_tracker.py self-check
  python3 scripts/aeo_tracker.py adapt --platform <id> --prompt-id <id> [--write]
  python3 scripts/aeo_tracker.py "<query>"

template, validate, report, and self-check do not call an API.
adapt calls an API only when that platform's key is already set.
Google AI Mode and AI Overviews have no adapter.
A bare query is the legacy Gemini mention count. With no key it records unknown.
"""

_AGEAURA = re.compile(r"\bageaura\b", re.I)
_UROLITHIN = re.compile(r"urolithin", re.I)
_NMN_TMG = re.compile(r"\bnmn\b|\btmg\b", re.I)
_SHILA = re.compile(r"\bshila\s*source\b", re.I)
_FLORA = re.compile(r"\bflora\s*fresh\b", re.I)
_STORE = re.compile(r"wellness\s*nest|wellnessnest\.co", re.I)
# Brand and competitor hits inside a URL are the link, not the answer naming the brand.
_URL = re.compile(r"https?://[^\s)>\]]+")
_MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_OBSERVER = re.compile(r"^[A-Za-z0-9_.: @+-]{1,80}$")

ROW_KEYS = frozenset({
    "brand_id", "prompt_id", "platform", "observed",
    "brand_mentioned", "mention_snippet",
    "store_mentioned", "store_snippet",
    "domain_cited", "cited_url", "source_urls",
    "competitors", "observer", "observed_at", "notes",
})
REQUIRED_ROW_KEYS = ROW_KEYS - {"source_urls", "notes"}
COMP_KEYS = frozenset({"name", "mentioned", "mention_snippet", "cited", "cited_url"})
SECRET_ENV = (
    "GEMINI_API_KEY", "OPENAI_API_KEY", "PERPLEXITY_API_KEY", "XAI_API_KEY",
    "OPENAI_VISIBILITY_MODEL", "PERPLEXITY_MODEL", "XAI_VISIBILITY_MODEL",
    "GEMINI_VISIBILITY_MODEL",
)
CSV_FIELDS = [
    "brand_id", "prompt_id", "platform", "observed",
    "brand_mentioned", "mention_snippet",
    "store_mentioned", "store_snippet",
    "domain_cited", "cited_url", "source_urls",
    "competitors", "observer", "observed_at", "notes",
]


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_catalog(path=None):
    return load_json(path or CATALOG_PATH)


def load_patterns(path=None):
    raw = load_json(path or PATTERN_PATH)
    compiled = []
    for item in raw["patterns"]:
        flags = re.I if "i" in (item.get("flags") or "") else 0
        compiled.append({
            "brand_id": item["brand_id"],
            "name": item["name"],
            "pattern": item["pattern"],
            "compiled": re.compile(item["pattern"], flags),
        })
    return compiled


def brand_map(catalog):
    return {brand["id"]: brand for brand in catalog["brands"]}


def prompt_map(catalog):
    return {prompt["id"]: prompt for prompt in catalog["prompts"]}


def platform_map(catalog):
    return {item["id"]: item for item in catalog["platforms"]}


def prompts_for(catalog, brand_id):
    return [prompt for prompt in catalog["prompts"] if prompt["brand_id"] == brand_id]


def our_url(url):
    if not isinstance(url, str):
        return False
    raw = url.strip()
    if not raw or any(ch.isspace() for ch in raw):
        return False
    parts = urllib.parse.urlparse(raw)
    if parts.scheme not in ("http", "https") or parts.hostname is None:
        return False
    host = parts.hostname.lower()
    return host == OUR_DOMAIN or host.endswith("." + OUR_DOMAIN)


def public_url(url):
    """An http(s) URL with a host. Used for competitor citations."""
    if not isinstance(url, str):
        return False
    raw = url.strip()
    if not raw or any(ch.isspace() for ch in raw):
        return False
    parts = urllib.parse.urlparse(raw)
    return parts.scheme in ("http", "https") and bool(parts.hostname)


def fold_name(value):
    text = (value or "").casefold()
    for src, dst in (("ü", "u"), ("ä", "a"), ("ö", "o"), ("é", "e")):
        text = text.replace(src, dst)
    return re.sub(r"[^a-z0-9]+", "", text)


def snippet_around(text, match, radius=90):
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    snippet = " ".join(text[start:end].split())
    return snippet[:SNIPPET_MAX]


def match_ageaura(text):
    good = []
    bad = False
    for hit in _AGEAURA.finditer(text):
        window = snippet_around(text, hit, 80)
        if _UROLITHIN.search(window) and not _NMN_TMG.search(window):
            bad = True
            continue
        good.append(snippet_around(text, hit, 90))
    if good:
        return "yes", good[0], ""
    if bad:
        return "no", "", "AgeAura Urolithin A is not AgeAura Pure NMN + TMG NAD+ Complex."
    return "no", "", ""


def match_regex(text, pattern):
    hit = pattern.search(text)
    if not hit:
        return "no", ""
    return "yes", snippet_around(text, hit, 90)


def match_brand(brand_id, text):
    if brand_id == "ageaura":
        return match_ageaura(text)
    if brand_id == "shilasource":
        mentioned, snippet = match_regex(text, _SHILA)
        return mentioned, snippet, ""
    if brand_id == "florafresh":
        mentioned, snippet = match_regex(text, _FLORA)
        return mentioned, snippet, ""
    raise KeyError(brand_id)


def match_store(text):
    return match_regex(text, _STORE)


def snippet_supports_brand(brand_id, snippet):
    if brand_id == "ageaura":
        if not _AGEAURA.search(snippet or ""):
            return False
        if _UROLITHIN.search(snippet) and not _NMN_TMG.search(snippet):
            return False
        return True
    if brand_id == "shilasource":
        return bool(_SHILA.search(snippet or ""))
    if brand_id == "florafresh":
        return bool(_FLORA.search(snippet or ""))
    return False


def match_competitors(text, patterns, brand_id):
    found = []
    seen = set()
    for item in patterns:
        if item["brand_id"] != brand_id or item["name"] in seen:
            continue
        hit = item["compiled"].search(text)
        if not hit:
            continue
        seen.add(item["name"])
        found.append({
            "name": item["name"],
            "mentioned": "yes",
            "mention_snippet": snippet_around(text, hit, 80),
            "cited": "unknown",
            "cited_url": "",
        })
    return found


def classify_text_and_sources(text, sources, brand_id, patterns):
    """text is None when no answer was returned. sources is None when the API
    did not include a source list. An empty source list is a real 'no'."""
    notes = []
    if text is None:
        brand_mentioned, mention_snippet = "unknown", ""
        store_mentioned, store_snippet = "unknown", ""
        competitors = []
    else:
        prose = _URL.sub(" ", text)
        brand_mentioned, mention_snippet, brand_note = match_brand(brand_id, prose)
        if brand_note:
            notes.append(brand_note)
        store_mentioned, store_snippet = match_store(text)
        competitors = match_competitors(prose, patterns, brand_id)
    if sources is None:
        domain_cited, cited_url, source_urls = "unknown", "", None
        if text is not None:
            notes.append("sources list absent; domain_cited left unknown")
    else:
        urls = [item.strip() for item in sources if isinstance(item, str) and item.strip()]
        ours = [url for url in urls if our_url(url)]
        source_urls = urls
        if ours:
            domain_cited, cited_url = "yes", ours[0]
        else:
            domain_cited, cited_url = "no", ""
        notes.append("sources list present (%d)" % len(urls))
    observed = any(
        value in ("yes", "no")
        for value in (brand_mentioned, store_mentioned, domain_cited)
    )
    return {
        "observed": observed,
        "brand_mentioned": brand_mentioned,
        "mention_snippet": mention_snippet if brand_mentioned == "yes" else "",
        "store_mentioned": store_mentioned,
        "store_snippet": store_snippet if store_mentioned == "yes" else "",
        "domain_cited": domain_cited,
        "cited_url": cited_url if domain_cited == "yes" else "",
        "source_urls": source_urls,
        "competitors": competitors,
        "notes": " ".join(notes)[:NOTES_MAX],
    }


def blank_row(brand_id, prompt_id, platform):
    return {
        "brand_id": brand_id,
        "prompt_id": prompt_id,
        "platform": platform,
        "observed": False,
        "brand_mentioned": "unknown",
        "mention_snippet": "",
        "store_mentioned": "unknown",
        "store_snippet": "",
        "domain_cited": "unknown",
        "cited_url": "",
        "competitors": [],
        "observer": "",
        "observed_at": "",
        "notes": "",
    }


def template_document(catalog=None):
    catalog = catalog or load_catalog()
    rows = []
    for prompt in catalog["prompts"]:
        for platform in catalog["platforms"]:
            rows.append(blank_row(prompt["brand_id"], prompt["id"], platform["id"]))
    return {
        "schema": SCHEMA,
        "kind": "template",
        "note": (
            "Every row is unobserved. brand_mentioned and domain_cited stay unknown "
            "until you have seen the answer and the source list for that platform."
        ),
        "observations": rows,
    }


def _tri(value, label, errors, where):
    if not isinstance(value, str) or value.strip().lower() not in TRI:
        errors.append("%s: %s must be yes, no, or unknown" % (where, label))
        return "unknown"
    return value.strip().lower()


def _bool(value, where, errors):
    if isinstance(value, bool):
        return value
    errors.append("%s: observed must be true or false" % where)
    return False


def _check_date(value):
    if not isinstance(value, str) or not _DATE.match(value):
        return False
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _snippet_has_name(name, snippet, pattern=None):
    folded_snippet = fold_name(snippet)
    folded = fold_name(name)
    if folded and folded in folded_snippet:
        return True
    if pattern is not None and pattern.search(snippet or ""):
        return True
    for token in re.findall(r"[A-Za-z0-9]{4,}", name or ""):
        folded_token = fold_name(token)
        if folded_token and folded_token in folded_snippet:
            return True
    return False


def _pattern_for(patterns, brand_id, name):
    for item in patterns or []:
        if item["brand_id"] == brand_id and item["name"] == name:
            return item["compiled"]
    return None


def validate_competitor(comp, where, errors, brand_id, patterns):
    if not isinstance(comp, dict):
        errors.append("%s: competitor must be an object" % where)
        return
    extra = set(comp) - COMP_KEYS
    if extra:
        errors.append("%s: unknown competitor keys %s" % (where, ", ".join(sorted(extra))))
    missing = COMP_KEYS - set(comp)
    if missing:
        errors.append("%s: missing %s" % (where, ", ".join(sorted(missing))))
        return
    name = comp.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 80:
        errors.append("%s: competitor name is empty or too long" % where)
        name = ""
    mentioned = _tri(comp.get("mentioned"), "mentioned", errors, where)
    cited = _tri(comp.get("cited"), "cited", errors, where)
    snippet = comp.get("mention_snippet")
    url = comp.get("cited_url")
    if not isinstance(snippet, str):
        errors.append("%s: mention_snippet must be a string" % where)
        snippet = ""
    if not isinstance(url, str):
        errors.append("%s: cited_url must be a string" % where)
        url = ""
    if mentioned == "yes":
        if not snippet.strip():
            errors.append("%s: mentioned yes needs a snippet" % where)
        elif name and not _snippet_has_name(name, snippet, _pattern_for(patterns, brand_id, name)):
            errors.append("%s: snippet does not contain %s" % (where, name))
        elif len(snippet) > SNIPPET_MAX:
            errors.append("%s: snippet is longer than %d" % (where, SNIPPET_MAX))
    elif snippet.strip():
        errors.append("%s: snippet must be empty unless mentioned is yes" % where)
    if cited == "yes":
        if not public_url(url) or our_url(url):
            errors.append("%s: cited yes needs a competitor URL, not a wellnessnest.co URL" % where)
    elif url.strip():
        errors.append("%s: cited_url must be empty unless cited is yes" % where)
    if mentioned == "unknown" and cited == "unknown":
        errors.append("%s: competitor has no observation" % where)


def validate_row(row, catalog, patterns, index):
    errors = []
    where = "observations[%d]" % index
    if not isinstance(row, dict):
        return ["%s: row must be an object" % where]
    extra = set(row) - ROW_KEYS
    if extra:
        errors.append("%s: unknown keys %s" % (where, ", ".join(sorted(extra))))
    missing = REQUIRED_ROW_KEYS - set(row)
    if missing:
        errors.append("%s: missing %s" % (where, ", ".join(sorted(missing))))
        return errors

    brands = brand_map(catalog)
    prompts = prompt_map(catalog)
    platforms = platform_map(catalog)
    brand_id = row["brand_id"]
    prompt_id = row["prompt_id"]
    platform = row["platform"]
    if brand_id not in brands:
        errors.append("%s: unknown brand_id %s" % (where, brand_id))
    if prompt_id not in prompts:
        errors.append("%s: unknown prompt_id %s" % (where, prompt_id))
    elif prompts[prompt_id]["brand_id"] != brand_id:
        errors.append("%s: prompt %s belongs to %s" % (where, prompt_id, prompts[prompt_id]["brand_id"]))
    if platform not in platforms:
        errors.append("%s: unknown platform %s" % (where, platform))

    observed = _bool(row["observed"], where, errors)
    brand_mentioned = _tri(row["brand_mentioned"], "brand_mentioned", errors, where)
    store_mentioned = _tri(row["store_mentioned"], "store_mentioned", errors, where)
    domain_cited = _tri(row["domain_cited"], "domain_cited", errors, where)
    for label in ("mention_snippet", "store_snippet", "cited_url", "observer", "observed_at"):
        if not isinstance(row[label], str):
            errors.append("%s: %s must be a string" % (where, label))
    mention_snippet = row["mention_snippet"] if isinstance(row["mention_snippet"], str) else ""
    store_snippet = row["store_snippet"] if isinstance(row["store_snippet"], str) else ""
    cited_url = row["cited_url"] if isinstance(row["cited_url"], str) else ""
    observer = row["observer"] if isinstance(row["observer"], str) else ""
    observed_at = row["observed_at"] if isinstance(row["observed_at"], str) else ""
    notes = row.get("notes", "")
    if notes is None:
        notes = ""
    if not isinstance(notes, str):
        errors.append("%s: notes must be a string" % where)
        notes = ""
    elif len(notes) > NOTES_MAX:
        errors.append("%s: notes longer than %d" % (where, NOTES_MAX))

    if brand_mentioned == "yes":
        if not mention_snippet.strip():
            errors.append("%s: brand_mentioned yes needs a snippet" % where)
        elif not snippet_supports_brand(brand_id, mention_snippet):
            errors.append("%s: snippet does not show the tracked product brand" % where)
        elif len(mention_snippet) > SNIPPET_MAX:
            errors.append("%s: mention_snippet longer than %d" % (where, SNIPPET_MAX))
    elif mention_snippet.strip():
        errors.append("%s: mention_snippet must be empty unless brand_mentioned is yes" % where)

    if store_mentioned == "yes":
        if not store_snippet.strip() or not _STORE.search(store_snippet):
            errors.append("%s: store_mentioned yes needs a snippet that names Wellness Nest" % where)
        elif len(store_snippet) > SNIPPET_MAX:
            errors.append("%s: store_snippet longer than %d" % (where, SNIPPET_MAX))
    elif store_snippet.strip():
        errors.append("%s: store_snippet must be empty unless store_mentioned is yes" % where)

    source_urls = row.get("source_urls", None)
    if "source_urls" in row and source_urls is not None and not isinstance(source_urls, list):
        errors.append("%s: source_urls must be a list or null" % where)
        source_urls = None
    if isinstance(source_urls, list):
        if not all(isinstance(item, str) for item in source_urls):
            errors.append("%s: source_urls entries must be strings" % where)

    if domain_cited == "yes":
        if not our_url(cited_url):
            errors.append("%s: domain_cited yes needs an http(s) wellnessnest.co URL" % where)
        elif isinstance(source_urls, list) and cited_url not in source_urls:
            errors.append("%s: cited_url is not in source_urls" % where)
    elif cited_url.strip():
        errors.append("%s: cited_url must be empty unless domain_cited is yes" % where)
    if domain_cited == "no" and isinstance(source_urls, list) and any(our_url(item) for item in source_urls):
        errors.append("%s: domain_cited no contradicts a wellnessnest.co URL in source_urls" % where)
    if domain_cited == "unknown" and isinstance(source_urls, list):
        errors.append("%s: source_urls must be null while domain_cited is unknown" % where)

    measured = any(value in ("yes", "no") for value in (brand_mentioned, store_mentioned, domain_cited))
    if observed and not measured:
        errors.append("%s: observed true needs a yes or no on mention, store, or citation" % where)
    if measured and not observed:
        errors.append("%s: a yes or no requires observed true" % where)
    if observed:
        if not _OBSERVER.match(observer):
            errors.append("%s: observer is missing or has unexpected characters" % where)
        if not _check_date(observed_at):
            errors.append("%s: observed_at must be YYYY-MM-DD" % where)
    else:
        if observer.strip() or observed_at.strip():
            errors.append("%s: observer and observed_at stay empty while observed is false" % where)
        if isinstance(source_urls, list):
            errors.append("%s: source_urls stays null while observed is false" % where)

    competitors = row["competitors"]
    if not isinstance(competitors, list):
        errors.append("%s: competitors must be a list" % where)
        competitors = []
    if not observed and competitors:
        errors.append("%s: competitors stay empty while observed is false" % where)
    names = []
    for comp_index, comp in enumerate(competitors):
        validate_competitor(comp, "%s.competitors[%d]" % (where, comp_index), errors, brand_id, patterns)
        if isinstance(comp, dict) and isinstance(comp.get("name"), str):
            names.append(comp["name"].casefold())
    if len(names) != len(set(names)):
        errors.append("%s: duplicate competitor name" % where)
    return errors


def _signature(row):
    return (
        row.get("brand_id"), row.get("prompt_id"), row.get("platform"),
        row.get("observed"), row.get("observed_at"), row.get("observer"),
        row.get("brand_mentioned"), row.get("mention_snippet"),
        row.get("store_mentioned"), row.get("domain_cited"), row.get("cited_url"),
    )


def validate_ledger(doc, catalog=None, patterns=None):
    catalog = catalog or load_catalog()
    patterns = patterns if patterns is not None else load_patterns()
    errors = []
    if not isinstance(doc, dict):
        return ["ledger must be an object with an observations list"]
    if doc.get("schema", SCHEMA) != SCHEMA:
        errors.append("schema must be %d" % SCHEMA)
    rows = doc.get("observations")
    if not isinstance(rows, list):
        return errors + ["observations must be a list"]
    seen = {}
    for index, row in enumerate(rows):
        errors.extend(validate_row(row, catalog, patterns, index))
        if isinstance(row, dict):
            key = _signature(row)
            if key in seen:
                errors.append(
                    "observations[%d]: duplicate of observations[%d]" % (index, seen[key])
                )
            else:
                seen[key] = index
            if row.get("observed") is False:
                slot = (row.get("brand_id"), row.get("prompt_id"), row.get("platform"))
                blank_key = ("blank",) + slot
                if blank_key in seen:
                    errors.append("observations[%d]: repeated unobserved slot" % index)
                else:
                    seen[blank_key] = index
    return errors


def _slot_rows(rows, brand_id, prompt_id, platform):
    slot = [
        row for row in rows
        if row.get("brand_id") == brand_id
        and row.get("prompt_id") == prompt_id
        and row.get("platform") == platform
    ]
    observed = [row for row in slot if row.get("observed") is True]
    if observed:
        return observed
    return [blank_row(brand_id, prompt_id, platform)]


def gap_kind(row):
    if row.get("observed") is not True:
        return None
    mentioned = row.get("brand_mentioned")
    cited = row.get("domain_cited")
    if mentioned == "yes" and cited == "no":
        return "mentioned_not_cited"
    if mentioned == "no" and cited == "yes":
        return "cited_not_mentioned"
    return None


def build_matrix(catalog, rows):
    matrix = []
    for brand in catalog["brands"]:
        brand_prompts = prompts_for(catalog, brand["id"])
        for platform in catalog["platforms"]:
            cell = {
                "brand_id": brand["id"],
                "brand_label": brand["label"],
                "platform": platform["id"],
                "platform_label": platform["label"],
                "prompts": len(brand_prompts),
                "observed_rows": 0,
                "mention_yes": 0,
                "mention_no": 0,
                "mention_unknown": 0,
                "cite_yes": 0,
                "cite_no": 0,
                "cite_unknown": 0,
                "mentioned_not_cited": 0,
                "cited_not_mentioned": 0,
                "both_yes": 0,
                "both_no": 0,
                "incomplete": 0,
            }
            for prompt in brand_prompts:
                for row in _slot_rows(rows, brand["id"], prompt["id"], platform["id"]):
                    if row["observed"]:
                        cell["observed_rows"] += 1
                    cell["mention_" + row["brand_mentioned"]] += 1
                    cell["cite_" + row["domain_cited"]] += 1
                    kind = gap_kind(row)
                    if kind == "mentioned_not_cited":
                        cell["mentioned_not_cited"] += 1
                    elif kind == "cited_not_mentioned":
                        cell["cited_not_mentioned"] += 1
                    elif row["brand_mentioned"] == "yes" and row["domain_cited"] == "yes":
                        cell["both_yes"] += 1
                    elif row["brand_mentioned"] == "no" and row["domain_cited"] == "no":
                        cell["both_no"] += 1
                    if row["observed"] and (
                        row["brand_mentioned"] == "unknown" or row["domain_cited"] == "unknown"
                    ):
                        cell["incomplete"] += 1
            matrix.append(cell)
    return matrix


def collect_gaps(catalog, rows):
    prompts = prompt_map(catalog)
    brands = brand_map(catalog)
    gaps = []
    entity_notes = []
    competitor_hits = []
    for row in rows:
        if row.get("observed") is not True:
            continue
        prompt = prompts.get(row.get("prompt_id"), {})
        brand = brands.get(row.get("brand_id"), {})
        kind = gap_kind(row)
        if kind:
            gaps.append({
                "kind": kind,
                "brand_id": row["brand_id"],
                "brand_label": brand.get("label", row["brand_id"]),
                "product_url": brand.get("product_url", ""),
                "prompt_id": row["prompt_id"],
                "prompt": prompt.get("text", ""),
                "platform": row["platform"],
                "mention_snippet": row.get("mention_snippet") or "",
                "cited_url": row.get("cited_url") or "",
                "store_mentioned": row.get("store_mentioned"),
                "observed_at": row.get("observed_at") or "",
                "fix": CITABILITY_FIX if kind == "mentioned_not_cited" else entity_fix(catalog),
            })
        if row.get("brand_mentioned") == "no" and row.get("store_mentioned") == "yes":
            entity_notes.append({
                "brand_id": row["brand_id"],
                "prompt_id": row["prompt_id"],
                "prompt": prompt.get("text", ""),
                "platform": row["platform"],
                "store_snippet": row.get("store_snippet") or "",
                "also_gap": kind == "cited_not_mentioned",
            })
        for comp in row.get("competitors") or []:
            if comp.get("mentioned") == "yes":
                competitor_hits.append({
                    "brand_id": row["brand_id"],
                    "prompt_id": row["prompt_id"],
                    "platform": row["platform"],
                    "name": comp.get("name"),
                    "mention_snippet": comp.get("mention_snippet") or "",
                    "cited": comp.get("cited"),
                    "cited_url": comp.get("cited_url") or "",
                })
    gaps.sort(key=lambda item: (item["kind"], item["brand_id"], item["platform"], item["prompt_id"]))
    return gaps, entity_notes, competitor_hits


def entity_fix(catalog):
    names = [
        "%s (%s)" % (brand["product_name"], brand["product_url"])
        for brand in catalog["brands"]
    ]
    return (
        "Entity/brand fix: wellnessnest.co was in the sources and the product brand was not named. "
        "Use one canonical name. "
        + " ".join(names)
        + " The store name is Wellness Nest. Urolithin A is not the AgeAura product in this set."
    )


def _md_cell(value):
    return str(value).replace("|", "/")


def render_report(catalog, rows):
    matrix = build_matrix(catalog, rows)
    gaps, entity_notes, competitor_hits = collect_gaps(catalog, rows)
    # Each cell counts that brand's prompts, so the sum is prompts × platforms.
    slot_count = sum(cell["prompts"] for cell in matrix)
    observed_slots = 0
    for prompt in catalog["prompts"]:
        for platform in catalog["platforms"]:
            if any(
                row.get("observed") is True
                and row.get("prompt_id") == prompt["id"]
                and row.get("platform") == platform["id"]
                for row in rows
            ):
                observed_slots += 1
    lines = [
        "# Mention vs citation",
        "",
        "Prompts: %d (hypothesised, not observed). Platforms: %d. Slots: %d."
        % (len(catalog["prompts"]), len(catalog["platforms"]), slot_count),
        "Ledger rows: %d. Slots with at least one observed row: %d. Unobserved slots: %d."
        % (len(rows), observed_slots, slot_count - observed_slots),
        "Disagreement gaps: %d." % len(gaps),
        "",
        "brand_mentioned is the product brand. Wellness Nest in the answer is store_mentioned. "
        "domain_cited is a wellnessnest.co URL in the platform's source list. "
        "A URL written in the answer prose is not a citation. Unknown is not a no.",
        "",
        "## Matrix",
        "",
        "| Brand | Platform | Prompts | Observed | Mention yes | Mention no | Mention unknown | Cited yes | Cited no | Cited unknown | Mentioned but not cited | Cited but not mentioned |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cell in matrix:
        lines.append("| %s |" % " | ".join(_md_cell(item) for item in (
            cell["brand_label"], cell["platform_label"], cell["prompts"], cell["observed_rows"],
            cell["mention_yes"], cell["mention_no"], cell["mention_unknown"],
            cell["cite_yes"], cell["cite_no"], cell["cite_unknown"],
            cell["mentioned_not_cited"], cell["cited_not_mentioned"],
        )))
    lines.extend(["", "## Mentioned but not cited", ""])
    mentioned_gaps = [gap for gap in gaps if gap["kind"] == "mentioned_not_cited"]
    cited_gaps = [gap for gap in gaps if gap["kind"] == "cited_not_mentioned"]
    lines.extend(_render_gap_section(mentioned_gaps, CITABILITY_FIX))
    lines.extend(["", "## Cited but not mentioned", ""])
    lines.extend(_render_gap_section(cited_gaps, entity_fix(catalog)))
    lines.extend(["", "## Store named, product brand not", ""])
    if not entity_notes:
        lines.append("None.")
    else:
        lines.append(entity_fix(catalog))
        lines.append("")
        for note in entity_notes:
            lines.append(
                "- %s / %s / %s — store snippet: \"%s\""
                % (note["brand_id"], note["platform"], note["prompt"], note["store_snippet"])
            )
    lines.extend(["", "## Competitor hits", ""])
    if not competitor_hits:
        lines.append("None recorded. An unmatched name is not a confirmed absence.")
    else:
        lines.append("Recorded hits only. An unmatched name is not a confirmed absence.")
        lines.append("")
        for hit in competitor_hits:
            lines.append(
                "- %s / %s / %s — %s (%s) \"%s\""
                % (
                    hit["brand_id"], hit["platform"], hit["prompt_id"],
                    hit["name"], hit["cited"], hit["mention_snippet"],
                )
            )
    cautions = [prompt for prompt in catalog["prompts"] if prompt.get("paste_caution")]
    lines.extend(["", "## Prompt set", ""])
    lines.append(catalog.get("note", ""))
    if cautions:
        lines.append("")
        lines.append("FloraFresh topic-bank primaries with segment glue (still hypothesised):")
        for prompt in cautions:
            lines.append("- `%s` — %s" % (prompt["id"], prompt["text"]))
    lines.extend([
        "",
        "Off-page listicle gaps from draft PR #75 stay a separate measurement. "
        "Every row there has ai_citation_observed false and evidence web search rank. "
        "Do not copy those rows into this ledger as citations.",
        "",
    ])
    return "\n".join(lines)


def _render_gap_section(gaps, fix):
    if not gaps:
        return ["None.", "", fix, ""]
    lines = [fix, ""]
    for gap in gaps:
        lines.append(
            "- %s / %s / %s (`%s`, %s)"
            % (gap["brand_id"], gap["platform"], gap["prompt"], gap["prompt_id"], gap["observed_at"])
        )
        if gap["mention_snippet"]:
            lines.append("  - snippet: \"%s\"" % gap["mention_snippet"])
        if gap["cited_url"]:
            lines.append("  - cited URL: %s" % gap["cited_url"])
        if gap["product_url"]:
            lines.append("  - product URL: %s" % gap["product_url"])
    lines.append("")
    return lines


def report_payload(catalog, rows):
    gaps, entity_notes, competitor_hits = collect_gaps(catalog, rows)
    return {
        "schema": SCHEMA,
        "prompts": len(catalog["prompts"]),
        "platforms": len(catalog["platforms"]),
        "slots": len(catalog["prompts"]) * len(catalog["platforms"]),
        "ledger_rows": len(rows),
        "gaps": gaps,
        "entity_notes": entity_notes,
        "competitor_hits": competitor_hits,
        "matrix": build_matrix(catalog, rows),
    }


def rows_to_csv(rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        out = {key: row.get(key, "") for key in CSV_FIELDS}
        out["observed"] = "true" if row.get("observed") else "false"
        source_urls = row.get("source_urls", None)
        out["source_urls"] = "" if source_urls is None else json.dumps(source_urls)
        out["competitors"] = json.dumps(row.get("competitors") or [])
        writer.writerow(out)
    return buffer.getvalue()


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    raise ValueError("observed must be true or false")


def _parse_tri(value):
    text = str(value).strip().lower()
    if text not in TRI:
        raise ValueError("expected yes, no, or unknown")
    return text


def rows_from_csv(text):
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("csv has no header")
    missing = [field for field in CSV_FIELDS if field not in reader.fieldnames]
    if missing:
        raise ValueError("csv missing columns: " + ", ".join(missing))
    rows = []
    for raw in reader:
        source_raw = (raw.get("source_urls") or "").strip()
        if source_raw:
            source_urls = json.loads(source_raw)
        else:
            source_urls = None
        row = {
            "brand_id": (raw.get("brand_id") or "").strip(),
            "prompt_id": (raw.get("prompt_id") or "").strip(),
            "platform": (raw.get("platform") or "").strip(),
            "observed": _parse_bool(raw.get("observed")),
            "brand_mentioned": _parse_tri(raw.get("brand_mentioned")),
            "mention_snippet": raw.get("mention_snippet") or "",
            "store_mentioned": _parse_tri(raw.get("store_mentioned")),
            "store_snippet": raw.get("store_snippet") or "",
            "domain_cited": _parse_tri(raw.get("domain_cited")),
            "cited_url": raw.get("cited_url") or "",
            "source_urls": source_urls,
            "competitors": json.loads(raw.get("competitors") or "[]"),
            "observer": raw.get("observer") or "",
            "observed_at": (raw.get("observed_at") or "").strip(),
            "notes": raw.get("notes") or "",
        }
        if source_urls is None:
            row.pop("source_urls")
        rows.append(row)
    return rows


def load_ledger(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    if path.endswith(".csv"):
        with open(path, encoding="utf-8") as handle:
            rows = rows_from_csv(handle.read())
        return {"schema": SCHEMA, "observations": rows}
    doc = load_json(path)
    if isinstance(doc, list):
        return {"schema": SCHEMA, "observations": doc}
    if not isinstance(doc, dict) or not isinstance(doc.get("observations"), list):
        raise ValueError("ledger must be an object with an observations list")
    return doc


def observation_row(brand_id, prompt_id, platform, classified, observer, observed_at):
    row = {
        "brand_id": brand_id,
        "prompt_id": prompt_id,
        "platform": platform,
        "observed": classified["observed"],
        "brand_mentioned": classified["brand_mentioned"],
        "mention_snippet": classified["mention_snippet"],
        "store_mentioned": classified["store_mentioned"],
        "store_snippet": classified["store_snippet"],
        "domain_cited": classified["domain_cited"],
        "cited_url": classified["cited_url"],
        "competitors": classified["competitors"],
        "observer": observer if classified["observed"] else "",
        "observed_at": observed_at if classified["observed"] else "",
        "notes": classified["notes"],
    }
    if classified["source_urls"] is not None:
        row["source_urls"] = classified["source_urls"]
    return row


def redact(message, env):
    text = message or ""
    for name in SECRET_ENV:
        secret = env.get(name) or ""
        if secret and secret in text:
            text = text.replace(secret, "[redacted]")
    return text


def _model(env, name, default=""):
    value = (env.get(name) or default).strip()
    if value and not _MODEL.match(value):
        raise ValueError("model name has unexpected characters")
    return value


def build_request(adapter, prompt_text, key, model):
    if adapter == "gemini":
        return {
            "url": (
                "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"
                % model
            ),
            "headers": {"Content-Type": "application/json", "x-goog-api-key": key},
            "body": {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "tools": [{"google_search": {}}],
                "generationConfig": {"temperature": 0},
            },
        }
    if adapter == "openai":
        return {
            "url": "https://api.openai.com/v1/responses",
            "headers": {"Content-Type": "application/json", "Authorization": "Bearer " + key},
            "body": {"model": model, "tools": [{"type": "web_search"}], "input": prompt_text},
        }
    if adapter == "perplexity":
        return {
            "url": "https://api.perplexity.ai/chat/completions",
            "headers": {"Content-Type": "application/json", "Authorization": "Bearer " + key},
            "body": {"model": model, "messages": [{"role": "user", "content": prompt_text}]},
        }
    if adapter == "xai":
        return {
            "url": "https://api.x.ai/v1/chat/completions",
            "headers": {"Content-Type": "application/json", "Authorization": "Bearer " + key},
            "body": {"model": model, "messages": [{"role": "user", "content": prompt_text}]},
        }
    raise KeyError(adapter)


def _string_urls(values):
    urls = []
    for item in values or []:
        if isinstance(item, str) and item.strip():
            urls.append(item.strip())
        elif isinstance(item, dict):
            for key in ("url", "uri"):
                if isinstance(item.get(key), str) and item[key].strip():
                    urls.append(item[key].strip())
                    break
    return urls


def parse_gemini(payload):
    if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
        raise ValueError(payload["error"].get("message") or "gemini error")
    candidates = payload.get("candidates") if isinstance(payload, dict) else None
    if not candidates:
        return None, None
    candidate = candidates[0] or {}
    texts = []
    for part in ((candidate.get("content") or {}).get("parts") or []):
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            texts.append(part["text"])
    grounding = candidate.get("groundingMetadata")
    sources = None
    if isinstance(grounding, dict):
        sources = []
        for chunk in grounding.get("groundingChunks") or []:
            web = chunk.get("web") if isinstance(chunk, dict) else None
            if isinstance(web, dict) and isinstance(web.get("uri"), str):
                sources.append(web["uri"])
    if not texts and sources is None:
        return None, None
    return "\n".join(texts), sources


def parse_openai(payload):
    if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
        raise ValueError(payload["error"].get("message") or "openai error")
    texts = []
    saw_sources = False
    urls = []
    for item in (payload.get("output") or []) if isinstance(payload, dict) else []:
        if not isinstance(item, dict):
            continue
        for block in item.get("content") or []:
            if not isinstance(block, dict):
                continue
            if isinstance(block.get("text"), str):
                texts.append(block["text"])
            if "annotations" in block:
                saw_sources = True
                for ann in block.get("annotations") or []:
                    if (
                        isinstance(ann, dict)
                        and ann.get("type") == "url_citation"
                        and isinstance(ann.get("url"), str)
                    ):
                        urls.append(ann["url"])
    if isinstance(payload, dict) and "citations" in payload:
        saw_sources = True
        urls.extend(_string_urls(payload.get("citations")))
    if not texts and isinstance(payload, dict):
        choices = payload.get("choices") or []
        if choices and isinstance(choices[0], dict):
            content = ((choices[0].get("message") or {}).get("content"))
            if isinstance(content, str):
                texts.append(content)
    sources = urls if saw_sources else None
    if not texts and sources is None:
        return None, None
    return "\n".join(texts), sources


def parse_chat_citations(payload):
    if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
        raise ValueError(payload["error"].get("message") or "api error")
    text = None
    choices = payload.get("choices") if isinstance(payload, dict) else None
    if choices and isinstance(choices[0], dict):
        content = (choices[0].get("message") or {}).get("content")
        if isinstance(content, str):
            text = content
    if isinstance(payload, dict) and "citations" in payload:
        return text if text is not None else "", _string_urls(payload.get("citations"))
    return text, None


PARSERS = {
    "gemini": parse_gemini,
    "openai": parse_openai,
    "perplexity": parse_chat_citations,
    "xai": parse_chat_citations,
}


def urllib_transport(request, timeout=45):
    data = json.dumps(request["body"]).encode("utf-8")
    req = urllib.request.Request(
        request["url"], data=data, headers=request["headers"], method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(2_000_000)
    except urllib.error.HTTPError as exc:
        raise RuntimeError("HTTP %s" % exc.code) from None
    return json.loads(raw.decode("utf-8"))


def run_adapter(platform_id, prompt_id, env=None, transport=None, confirm=False, today=None):
    env = env if env is not None else {}
    if not confirm:
        return {"status": "skipped", "reason": "adapt was not confirmed", "observation": None}
    catalog = load_catalog()
    platforms = platform_map(catalog)
    prompts = prompt_map(catalog)
    platform = platforms.get(platform_id)
    prompt = prompts.get(prompt_id)
    if platform is None:
        return {"status": "error", "reason": "unknown platform", "observation": None}
    if prompt is None:
        return {"status": "error", "reason": "unknown prompt_id", "observation": None}
    if platform.get("adapter") is None:
        return {
            "status": "skipped",
            "reason": platform["label"] + " has no API; enter the row by hand",
            "observation": None,
        }
    key = (env.get(platform["env_key"]) or "").strip()
    if not key:
        return {
            "status": "skipped",
            "reason": platform["env_key"] + " is not set",
            "observation": None,
        }
    try:
        if platform["adapter"] == "gemini":
            model = _model(env, platform["env_model"], GEMINI_MODEL_DEFAULT)
        else:
            model = _model(env, platform["env_model"], "")
    except ValueError as exc:
        return {"status": "error", "reason": redact(str(exc), env), "observation": None}
    if not model:
        return {
            "status": "skipped",
            "reason": platform["env_model"] + " is not set; refusing to guess a model",
            "observation": None,
        }
    request = build_request(platform["adapter"], prompt["text"], key, model)
    if key in request["url"]:
        return {"status": "error", "reason": "refusing to put the API key in the URL", "observation": None}
    transport = transport or urllib_transport
    try:
        payload = transport(request)
        text, sources = PARSERS[platform["adapter"]](payload)
    except Exception as exc:
        return {"status": "error", "reason": redact(str(exc), env), "observation": None}
    classified = classify_text_and_sources(
        text, sources, prompt["brand_id"], load_patterns()
    )
    if not classified["observed"]:
        return {
            "status": "ok",
            "reason": "response had no answer text and no source list",
            "observation": None,
        }
    observed_at = today or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    row = observation_row(
        prompt["brand_id"], prompt["id"], platform["id"], classified,
        "adapter:" + platform["id"], observed_at,
    )
    errors = validate_row(row, catalog, load_patterns(), 0)
    if errors:
        return {"status": "error", "reason": "; ".join(errors), "observation": None}
    return {"status": "ok", "reason": "observed", "observation": row}


def append_observation(path, row, catalog=None):
    doc = load_ledger(path)
    doc.setdefault("observations", []).append(row)
    errors = validate_ledger(doc, catalog)
    if errors:
        raise ValueError(errors[0])
    _write_json(path, doc)


def _write_json(path, doc):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(doc, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(temporary, path)


def offpage_drift(catalog, seed_dir):
    problems = []
    expected = {"ageaura": AGEAURA_QUERIES, "shilasource": SHILASOURCE_QUERIES}
    for brand_id, filename in (("ageaura", "ageaura.json"), ("shilasource", "shilasource.json")):
        path = os.path.join(seed_dir, filename)
        if not os.path.exists(path):
            continue
        queries = load_json(path).get("queries")
        got = tuple(prompt["text"] for prompt in prompts_for(catalog, brand_id))
        if list(got) != list(queries):
            problems.append("offpage seed drift in " + filename)
        if got != expected[brand_id]:
            problems.append("prompt_set.json drifted from the frozen " + brand_id + " list")
    return problems


def frozen_query_problems(catalog):
    problems = []
    got_age = tuple(prompt["text"] for prompt in prompts_for(catalog, "ageaura"))
    got_shila = tuple(prompt["text"] for prompt in prompts_for(catalog, "shilasource"))
    if got_age != AGEAURA_QUERIES:
        problems.append("AgeAura prompts drifted from the PR #75 seed list")
    if got_shila != SHILASOURCE_QUERIES:
        problems.append("ShilaSource prompts drifted from the PR #75 seed list")
    return problems


def florafresh_bank_problems(catalog, bank_path=TOPIC_BANK_PATH):
    bank = load_json(bank_path)
    wanted = [
        topic for topic in bank.get("topics", [])
        if topic.get("product") == "florafresh-vaginal-probiotics-gummies"
    ]
    got = prompts_for(catalog, "florafresh")
    problems = []
    if [prompt.get("bank_id") for prompt in got] != [topic["id"] for topic in wanted]:
        problems.append("FloraFresh prompt order drifted from the topic bank")
    elif [prompt["text"] for prompt in got] != [topic["primary"] for topic in wanted]:
        problems.append("FloraFresh prompt text drifted from topic-bank primaries")
    return problems


def product_name_problems(catalog):
    problems = []
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import ageaura_rules
    import florafresh_rules
    import shilasource_resin_rules
    expected = {
        "ageaura": (ageaura_rules.PRODUCT_LABEL, ageaura_rules.PRODUCT_URL, ageaura_rules.HANDLE),
        "shilasource": (
            shilasource_resin_rules.PRODUCT_NAME,
            shilasource_resin_rules.PRODUCT_URL,
            shilasource_resin_rules.HANDLE,
        ),
        "florafresh": (
            florafresh_rules.PRODUCT_NAME,
            florafresh_rules.PRODUCT_URL,
            florafresh_rules.HANDLE,
        ),
    }
    for brand in catalog["brands"]:
        name, url, handle = expected[brand["id"]]
        if (brand["product_name"], brand["product_url"], brand["handle"]) != (name, url, handle):
            problems.append(brand["id"] + " product identity drifted from its guard")
    return problems


def self_check():
    problems = []
    try:
        catalog = load_catalog()
        patterns = load_patterns()
    except (OSError, ValueError, KeyError, re.error, json.JSONDecodeError) as exc:
        return ["catalog failed to load: " + str(exc)]
    if [item["id"] for item in catalog["platforms"]] != [
        "chatgpt", "gemini", "google_ai_mode", "ai_overviews", "perplexity", "grok"
    ]:
        problems.append("platform list drifted")
    if [brand["id"] for brand in catalog["brands"]] != ["ageaura", "shilasource", "florafresh"]:
        problems.append("brand list drifted")
    statuses = {prompt.get("prompt_status") for prompt in catalog["prompts"]}
    if statuses != {"hypothesised"}:
        problems.append("a prompt is marked as something other than hypothesised")
    if any("urolithin" in prompt["text"].lower() for prompt in catalog["prompts"]):
        problems.append("prompt text names Urolithin")
    problems.extend(frozen_query_problems(catalog))
    problems.extend(offpage_drift(catalog, OFFPAGE_SEED_DIR))
    problems.extend(florafresh_bank_problems(catalog))
    problems.extend(product_name_problems(catalog))
    brand_counts = {}
    for item in patterns:
        brand_counts[item["brand_id"]] = brand_counts.get(item["brand_id"], 0) + 1
    if brand_counts.get("ageaura") != 32 or brand_counts.get("shilasource") != 25:
        problems.append("competitor pattern counts drifted from PR #75")
    if any(item["brand_id"] == "florafresh" for item in patterns):
        problems.append("FloraFresh competitor patterns were added without a source list")
    template = template_document(catalog)
    problems.extend(validate_ledger(template, catalog, patterns))
    if os.path.exists(LEDGER_PATH):
        try:
            ledger = load_ledger(LEDGER_PATH)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            problems.append("ledger failed to load: " + str(exc))
        else:
            problems.extend(validate_ledger(ledger, catalog, patterns))
    prose = classify_text_and_sources(
        "See https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex for the bottle.",
        None, "ageaura", patterns,
    )
    if prose["domain_cited"] != "unknown" or prose["store_mentioned"] != "yes":
        problems.append("a prose URL was treated as a source-list citation or missed as the store")
    if prose["brand_mentioned"] != "no":
        problems.append("the store URL was treated as an AgeAura mention")
    urolithin = classify_text_and_sources(
        "AgeAura Urolithin A is a different bottle.", None, "ageaura", patterns,
    )
    if urolithin["brand_mentioned"] != "no":
        problems.append("Urolithin A counted as the tracked AgeAura product")
    return problems


def _print_errors(errors):
    for message in errors[:MAX_ERRORS]:
        print(message)
    if len(errors) > MAX_ERRORS:
        print("%d more" % (len(errors) - MAX_ERRORS))


def _refuse_ledger_overwrite(path):
    return os.path.abspath(path) == os.path.abspath(LEDGER_PATH)


def main(argv=None, env=None, transport=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(USAGE)
        return 0 if argv else 1
    if argv[0] not in COMMANDS:
        print(USAGE)
        return 1
    env = os.environ if env is None else env
    parser = argparse.ArgumentParser(prog="aeo_tracker.py", add_help=True)
    sub = parser.add_subparsers(dest="cmd", required=True)
    template = sub.add_parser("template")
    template.add_argument("--format", choices=("json", "csv"), default="json")
    template.add_argument("--out", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("path", nargs="?", default=LEDGER_PATH)
    report = sub.add_parser("report")
    report.add_argument("--ledger", default=LEDGER_PATH)
    report.add_argument("--format", choices=("markdown", "json"), default="markdown")
    report.add_argument("--out", default="")
    sub.add_parser("self-check")
    adapt = sub.add_parser("adapt")
    adapt.add_argument("--platform", required=True)
    adapt.add_argument("--prompt-id", required=True)
    adapt.add_argument("--write", action="store_true")
    adapt.add_argument("--ledger", default=LEDGER_PATH)
    args = parser.parse_args(argv)

    if args.cmd == "self-check":
        problems = self_check()
        if problems:
            _print_errors(problems)
            return 1
        catalog = load_catalog()
        print("✓ PASS")
        print("prompts=%d platforms=%d slots=%d" % (
            len(catalog["prompts"]), len(catalog["platforms"]),
            len(catalog["prompts"]) * len(catalog["platforms"]),
        ))
        return 0

    if args.cmd == "template":
        if _refuse_ledger_overwrite(args.out):
            print("refusing to overwrite the ledger with a blank template")
            return 1
        catalog = load_catalog()
        doc = template_document(catalog)
        errors = validate_ledger(doc, catalog)
        if errors:
            _print_errors(errors)
            return 1
        text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else rows_to_csv(doc["observations"])
        if args.out == "-":
            sys.stdout.write(text)
        else:
            parent = os.path.dirname(args.out)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as handle:
                handle.write(text)
            print("wrote %d unobserved rows to %s" % (len(doc["observations"]), args.out))
        return 0

    if args.cmd == "validate":
        try:
            doc = load_ledger(args.path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(str(exc))
            return 1
        errors = validate_ledger(doc)
        if errors:
            _print_errors(errors)
            return 1
        print("✓ PASS")
        print("rows=%d" % len(doc["observations"]))
        return 0

    if args.cmd == "report":
        catalog = load_catalog()
        if os.path.exists(args.ledger):
            try:
                doc = load_ledger(args.ledger)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                print(str(exc))
                return 1
            errors = validate_ledger(doc, catalog)
            if errors:
                _print_errors(errors)
                return 1
            rows = doc["observations"]
        else:
            rows = []
        if args.format == "json":
            text = json.dumps(report_payload(catalog, rows), indent=2, ensure_ascii=False) + "\n"
        else:
            text = render_report(catalog, rows)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as handle:
                handle.write(text)
            print("wrote " + args.out)
        else:
            sys.stdout.write(text)
        return 0

    result = run_adapter(
        args.platform, args.prompt_id, env=env, transport=transport, confirm=True
    )
    print("status: " + result["status"])
    print(result["reason"])
    if result.get("observation"):
        print(json.dumps(result["observation"], indent=2, ensure_ascii=False))
    if args.write and result.get("observation"):
        try:
            append_observation(args.ledger, result["observation"])
        except (OSError, ValueError) as exc:
            print(redact(str(exc), env))
            return 1
        print("appended to " + args.ledger)
    if result["status"] == "error":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

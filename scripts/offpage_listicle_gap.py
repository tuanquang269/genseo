#!/usr/bin/env python3
"""Off-page listicle gap check for Wellness Nest.

Reads hypothesised prompts and a sources file. With --fetch, it GETs each
page (robots.txt first, one retry after a 429, hard stop at the GET budget)
and re-checks whether the page names Wellness Nest, AgeAura, or ShilaSource.

This does not query ChatGPT, Perplexity, or Google AI Overviews. It does not
email anyone and it does not write to Shopify. A web-search rank is not an
AI citation. Scores are not traffic, volume, or authority figures.

AgeAura outreach names only AgeAura Pure NMN + TMG NAD+ Complex.
ShilaSource outreach names only ShilaSource Himalayan Shilajit Resin.

  python3 scripts/offpage_listicle_gap.py --check
  python3 scripts/offpage_listicle_gap.py --fetch --report docs/OFFPAGE_LISTICLE_GAP_2026-10-20.md
"""
import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import ageaura_rules
import shilasource_resin_rules

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SEEDS = os.path.join(ROOT, "data", "offpage_seeds")
DEFAULT_SOURCES = os.path.join(ROOT, "data", "offpage_sources_2026-10-20.json")
DEFAULT_REPORT = os.path.join(ROOT, "docs", "OFFPAGE_LISTICLE_GAP_2026-10-20.md")

UA = "GenSeoOffpageGap/1.0 (public research; +https://wellnessnest.co)"
GET_BUDGET = 200
MAX_BYTES = 1200000
MATCH_CHARS = 80000
EXCERPT_CHARS = 360

SHILA_HANDLE = "shilasource-himalayan-shilajit-resin"
SHILA_NAME = "ShilaSource Himalayan Shilajit Resin"
SHILA_URL = "https://wellnessnest.co/products/" + SHILA_HANDLE

PAGE_WEIGHT = {
    "listicle": 50,
    "comparison": 48,
    "roundup": 46,
    "directory": 42,
    "reddit": 24,
    "explainer": 16,
    "brand_roundup": 10,
    "affiliate_review": 8,
    "brand_review": 8,
    "review_directory": 6,
    "study": 0,
}
GAP_TYPES = frozenset(k for k, w in PAGE_WEIGHT.items() if w > 0)
PITCH_OK = frozenset({"listicle", "comparison", "roundup", "directory", "explainer"})

_MON = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)"
)
_DATE_TOKEN = (
    rf"(?:{_MON}\s+\d{{1,2}}(?:st|nd|rd|th)?,\s+\d{{4}}"
    rf"|\d{{1,2}}\s+{_MON}\s+\d{{4}}"
    rf"|{_MON}\s+\d{{4}})"
)
_DATE_RE = re.compile(rf"\b({_DATE_TOKEN})\b", re.I)
_CUE_DATE = re.compile(
    rf"(?i)(?:last\s+)?(?:updated|published|reviewed)[^\n]{{0,48}}?({_DATE_TOKEN})"
)
_TITLE = re.compile(r"(?is)<title[^>]*>(.*?)</title>")
_TAG = re.compile(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>")
_HTML = re.compile(r"(?s)<[^>]+>")
_WS = re.compile(r"\s+")
_BLOCK = re.compile(
    r"(access denied|just a moment|enable javascript|are you a robot|"
    r"captcha|sign in to continue|subscribe to (?:read|unlock)|"
    r"verify you are human)",
    re.I,
)

_US = {
    "ageaura": (
        ("AgeAura", re.compile(r"\bageaura\b", re.I)),
        ("Wellness Nest", re.compile(r"wellness\s*nest|wellnessnest\.co", re.I)),
    ),
    "shilasource": (
        ("ShilaSource", re.compile(r"\bshilasource\b", re.I)),
        ("Wellness Nest", re.compile(r"wellness\s*nest|wellnessnest\.co", re.I)),
    ),
}

def _rx(pattern):
    return re.compile(pattern, re.I)

# Distinctive brand strings seen on public roundups. A hit is a string match,
# not a claim that the brand was reviewed fairly.
_BRANDS = {
    "ageaura": (
        ("Transparent Labs", _rx(r"transparent\s+labs")),
        ("Renue By Science", _rx(r"renue\s+by\s+science|\brenue\b")),
        ("Neurogan", _rx(r"\bneurogan\b")),
        ("Toniiq", _rx(r"\btoniiq\b")),
        ("Codeage", _rx(r"\bcodeage\b")),
        ("Nutricost", _rx(r"\bnutricost\b")),
        ("ProHealth", _rx(r"pro\s*health")),
        ("Elysium", _rx(r"\belysium\b")),
        ("Cata-Kor", _rx(r"cata-?kor")),
        ("California Gold Nutrition", _rx(r"california\s+gold\s+nutrition")),
        ("Double Wood", _rx(r"double\s+wood")),
        ("PartiQlar", _rx(r"partiqlar")),
        ("Wonderfeel", _rx(r"\bwonderfeel\b")),
        ("Omre", _rx(r"\bomre\b")),
        ("Welzo", _rx(r"\bwelzo\b")),
        ("GenuinePurity", _rx(r"genuine\s*purity")),
        ("Hello100", _rx(r"hello\s*100")),
        ("BulkSupplements", _rx(r"bulk\s*supplements")),
        ("Natural Factors", _rx(r"natural\s+factors")),
        ("Genex Formulas", _rx(r"genex\s+formulas")),
        ("Upnourish", _rx(r"\bupnourish\b")),
        ("Innerbody Labs", _rx(r"innerbody\s+labs")),
        ("Tru Niagen", _rx(r"tru\s+niagen|\bniagen\b")),
        ("Life Extension", _rx(r"life\s+extension")),
        ("Thorne", _rx(r"\bthorne\b")),
        ("NOVOS", _rx(r"\bnovos\b")),
        ("DoNotAge", _rx(r"do\s*not\s*age")),
        ("Jinfiniti", _rx(r"\bjinfiniti\b")),
        ("Solensis", _rx(r"\bsolensis\b")),
        ("Manapura", _rx(r"\bmanapura\b")),
        ("Oakrus", _rx(r"\boakrus\b")),
        ("For Youth", _rx(r"for\s+youth\s+the\s+repair")),
    ),
    "shilasource": (
        ("Natural Shilajit", re.compile(r"naturalshilajit\.com|(?<!Himalayan )Natural Shilajit")),
        ("Mountaindrop", _rx(r"\bmountaindrop\b")),
        ("Chuga", _rx(r"\bchuga\b")),
        ("Pure Himalayan Shilajit", _rx(r"pure\s+himalayan\s+shilajit")),
        ("Life Cykel", _rx(r"life\s+cykel")),
        ("Pürblack", _rx(r"p[uü]rblack|p[uü]r\s+shilajit")),
        ("Puralis", _rx(r"\bpuralis\b")),
        ("Lotus Blooming", _rx(r"lotus\s+blooming")),
        ("Essencraft", _rx(r"\bessencraft\b")),
        ("Xara", _rx(r"\bxara\b")),
        ("Sunmed", _rx(r"\bsunmed\b")),
        ("Root Labs", _rx(r"root\s+labs")),
        ("Novomins", _rx(r"\bnovomins\b")),
        ("Nootropics Depot", _rx(r"nootropics\s+depot")),
        ("PrimaVie", _rx(r"\bprimavie\b")),
        ("Nugenix", _rx(r"\bnugenix\b")),
        ("WOWMD", _rx(r"\bwowmd\b")),
        ("VitaUp", _rx(r"\bvitaup\b")),
        ("Black Lotus", _rx(r"black\s+lotus")),
        ("Double Wood", _rx(r"double\s+wood")),
        ("YourHealthier", _rx(r"your\s*healthier")),
        ("Organifi", _rx(r"\borganifi\b")),
        ("Vitadote", _rx(r"\bvitadote\b")),
        ("Moon Juice", _rx(r"moon\s+juice")),
        ("Sulaiman Aftabi", _rx(r"sulaiman\s+aftabi")),
    ),
}

# Public contact-page candidates. A URL is stored only after a same-site HTTP 200.
CONTACT_TRIES = {
    "healthline.com": ["https://www.healthline.com/contact"],
    "fortune.com": [
        "https://fortune.com/2021/04/15/how-to-pitch-fortune-get-a-story-picked-up-business-magazine-freelance-work-pitching-advice/"
    ],
    "forbes.com": ["https://www.forbes.com/health/about-us/"],
    "verywellhealth.com": ["https://www.verywellhealth.com/about-us-5181458"],
    "innerbody.com": [
        "https://www.innerbody.com/about",
        "https://www.innerbody.com/contact",
    ],
    "the-best-supplement.com": [
        "https://www.the-best-supplement.com/about",
        "https://www.the-best-supplement.com/contact",
    ],
    "shilajitdb.com": ["https://shilajitdb.com/about"],
    "supplementscored.com": [
        "https://www.supplementscored.com/about",
        "https://www.supplementscored.com/contact",
    ],
    "longevitybenchmark.com": ["https://www.longevitybenchmark.com/about"],
    "verifiedsupplementdata.com": [
        "https://verifiedsupplementdata.com/about",
        "https://verifiedsupplementdata.com/contact",
    ],
    "bettervitals.com": [
        "https://www.bettervitals.com/contact",
        "https://www.bettervitals.com/about",
    ],
    "factually.co": ["https://factually.co/about", "https://factually.co/contact"],
    "usefulvitamins.com": ["https://usefulvitamins.com/contact"],
    "biohackblueprint.org": ["https://biohackblueprint.org/pages/contact"],
    "consumerlab.com": ["https://www.consumerlab.com/contact/"],
    "menshealth.com": ["https://www.menshealth.com/about/a26378436/contact-us/"],
}


def domain_of(url):
    host = urlparse(url or "").netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def html_to_text(raw):
    text = _TAG.sub(" ", raw or "")
    text = _HTML.sub(" ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def html_title(raw):
    match = _TITLE.search(raw or "")
    if not match:
        return ""
    return _WS.sub(" ", html.unescape(match.group(1))).strip()


_MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
_ISO_DAY = re.compile(r"(20\d{2})-(\d{2})-(\d{2})")


def find_date(text):
    """A date string shown near the top of the page, or ''."""
    head = (text or "")[:1500]
    cue = _CUE_DATE.search(head)
    if cue:
        return cue.group(1)
    early = _DATE_RE.search(head[:1200])
    if early:
        return early.group(1)
    return ""


def _iso_to_shown(value):
    match = _ISO_DAY.search(value or "")
    if not match:
        return ""
    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if not 1 <= month <= 12 or not 1 <= day <= 31:
        return ""
    return "%s %s, %s" % (_MONTHS[month - 1], day, year)


def _meta_values(raw, key):
    found = re.findall(
        r'(?i)(?:property|name)=["\']%s["\'][^>]*content=["\']([^"\']+)' % re.escape(key),
        raw,
    )
    found += re.findall(
        r'(?i)content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']%s["\']' % re.escape(key),
        raw,
    )
    found += re.findall(r'(?i)"%s"\s*:\s*"([^"]+)"' % re.escape(key), raw)
    return found


def find_html_date(raw):
    """dateModified, else datePublished, from meta or JSON-LD. Empty if neither is an ISO day."""
    chunk = (raw or "")[:300000]
    for key in ("dateModified", "article:modified_time", "datePublished", "article:published_time"):
        for value in _meta_values(chunk, key):
            shown = _iso_to_shown(value)
            if shown:
                return shown
    return ""


def match_brands(text, cluster):
    found = []
    for name, rx in _BRANDS.get(cluster, ()):
        hit = rx.search(text or "")
        if hit:
            found.append((hit.start(), name))
    found.sort()
    out = []
    for _pos, name in found:
        if name not in out:
            out.append(name)
    return out


def match_us(text, cluster):
    out = []
    for name, rx in _US.get(cluster, ()):
        if rx.search(text or "") and name not in out:
            out.append(name)
    return out


def _year_bonus(date_shown):
    if "2026" in (date_shown or ""):
        return 5
    if "2025" in (date_shown or ""):
        return 2
    return 0


def _confidence(basis):
    if basis == "fetched_body":
        return 1.0
    if basis == "search_snippet":
        return 0.55
    return 0.0


def offer_text(cluster):
    if cluster == "ageaura":
        return (
            "Draft only, do not email or submit a form. Offer one sample of "
            + ageaura_rules.PRODUCT_LABEL
            + " (" + ageaura_rules.PRODUCT_URL + "). "
            "Quote only lines in product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json. "
            "Do not add a milligram amount. "
            "A roster byline may be quoted only after Kevin names the person. "
            "Do not lead with a lab test or a COA. Link a report only if Kevin already published it as HTML."
        )
    if cluster == "shilasource":
        return (
            "Draft only, do not email or submit a form. Offer one sample of "
            + SHILA_NAME + " (" + SHILA_URL + "). "
            "Quote only lines in product_refs/shilasource-himalayan-shilajit-resin.label.json. "
            "Do not add a milligram amount, a mineral count, or a joined serving count. "
            "Other shilajit jars and the gummy format are separate products and are not this outreach SKU. "
            "A roster byline may be quoted only after Kevin names the person. "
            "Do not lead with a lab test or a COA."
        )
    raise ValueError("unknown cluster: " + str(cluster))


def outreach_for(rec):
    """Draft action for one source. Never a sent email."""
    if rec.get("us_mentioned"):
        action = "already_named"
        offer = "The page already names us. Do not pitch it as a gap. Do not repeat numbers from that page."
    elif not rec.get("is_gap"):
        action = "not_a_gap"
        offer = "No confirmed competitor roundup to pitch."
    elif rec.get("page_type") not in PITCH_OK:
        action = "do_not_pitch"
        kind = rec.get("page_type") or "page"
        if kind == "reddit":
            offer = (
                "Community thread. Do not pitch. A roster writer may answer the question "
                "only if Kevin asks for that reply."
            )
        elif kind == "brand_roundup":
            offer = (
                "Competitor-owned roundup. The Search Engine Land SOP marks vendor pages "
                "do-not-pitch, because the page will not add a rival as the pick."
            )
        else:
            offer = "Do not pitch this page type (" + kind + ")."
    else:
        action = "draft_only"
        offer = offer_text(rec.get("cluster"))
        blob = " ".join([rec.get("title") or "", rec.get("url") or ""])
        if rec.get("cluster") == "shilasource" and re.search(r"gumm", blob, re.I):
            offer += (
                " This URL is a gummy roundup. Do not offer the resin as a gummy, "
                "and do not pitch another jar under the resin name."
            )
    return {
        "action": action,
        "contact_url": rec.get("editor_contact_url") or "",
        "offer": offer,
        "product_url": ageaura_rules.PRODUCT_URL if rec.get("cluster") == "ageaura" else SHILA_URL,
    }


def apply_score(rec):
    out = dict(rec)
    out["ai_citation_observed"] = False
    if not out.get("evidence"):
        out["evidence"] = "web search rank"
    brands = list(out.get("competitor_brands") or [])
    basis = out.get("mention_basis") or "unreadable"
    page_type = out.get("page_type") or ""
    us = bool(out.get("us_mentioned"))
    is_gap = (
        (not us)
        and basis != "unreadable"
        and page_type in GAP_TYPES
        and len(brands) >= (2 if page_type == "explainer" else 1)
    )
    weight = PAGE_WEIGHT.get(page_type, 0)
    raw = weight + min(len(brands), 6) * 2 + _year_bonus(out.get("date_shown"))
    score = int(round(raw * _confidence(basis))) if is_gap else 0
    out["is_gap"] = bool(is_gap and score > 0)
    out["gap_score"] = score if out["is_gap"] else 0
    out["domain"] = domain_of(out.get("final_url") or out.get("url"))
    out["outreach"] = outreach_for(out)
    return out


def assess(rec, text=None, basis=None):
    """Score one source from page text, or from stored search fields when text is absent."""
    out = dict(rec)
    out["ai_citation_observed"] = False
    if text is not None and basis == "fetched_body":
        sample = text[:MATCH_CHARS]
        if not sample.strip() or _BLOCK.search(sample[:1500]):
            basis = "search_snippet" if rec.get("search_brands") is not None else "unreadable"
            prev = out.get("fetch_note") or ""
            extra = "fetched page was too short or blocked"
            out["fetch_note"] = (prev + "; " + extra) if prev else extra
        else:
            out["competitor_brands"] = match_brands(sample, rec.get("cluster"))
            out["us_marks"] = match_us(sample, rec.get("cluster"))
            out["us_mentioned"] = bool(out["us_marks"])
            out["date_shown"] = find_date(sample) or ""
            if out["date_shown"]:
                out["date_source"] = "page_text"
            out["opening_excerpt"] = sample[:EXCERPT_CHARS]
            out["body_chars"] = len(text)
            out["body_sha256"] = hashlib.sha256(sample.encode("utf-8", "replace")).hexdigest()[:16]
            out["mention_basis"] = "fetched_body"
            return apply_score(out)
    has_snippet = isinstance(rec.get("search_brands"), list) or rec.get("search_us_mentioned") is True
    if basis == "search_snippet" or (text is None and has_snippet
                                      and rec.get("mention_basis") != "fetched_body"):
        out["competitor_brands"] = list(rec.get("search_brands") or [])
        if rec.get("search_us_mentioned"):
            out["us_marks"] = list(rec.get("search_us_marks") or ["Wellness Nest"])
            out["us_mentioned"] = True
        else:
            out["us_marks"] = []
            out["us_mentioned"] = False
        out["date_shown"] = rec.get("date_shown") or rec.get("search_date") or ""
        out["mention_basis"] = "search_snippet"
        return apply_score(out)
    if rec.get("mention_basis") == "fetched_body" and "competitor_brands" in rec:
        return apply_score(out)
    out["competitor_brands"] = []
    out["us_marks"] = []
    out["us_mentioned"] = False
    out["mention_basis"] = "unreadable"
    out["date_shown"] = rec.get("date_shown") or ""
    return apply_score(out)


def rank_gaps(records, cluster, limit=15):
    rows = [r for r in records if r.get("cluster") == cluster and r.get("is_gap")]
    rows.sort(key=lambda r: (-r.get("gap_score", 0), -len(r.get("competitor_brands") or []), r.get("url") or ""))
    return rows[:limit]


def validate_seeds(directory):
    """Return (queries_by_cluster, problems)."""
    problems = []
    found = {}
    if not os.path.isdir(directory):
        return found, ["missing seeds directory: " + directory]
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(directory, name)
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        cluster = data.get("cluster")
        if data.get("prompt_status") != "hypothesised":
            problems.append(name + ": prompt_status must be hypothesised")
        queries = data.get("queries") or []
        if not queries or not all(isinstance(q, str) and q.strip() for q in queries):
            problems.append(name + ": queries must be non-empty strings")
        blob = json.dumps(data).lower()
        if "urolithin" in blob or "/collections/ageaura" in blob:
            problems.append(name + ": refused AgeAura target in the seed file")
        if cluster == "ageaura":
            try:
                ageaura_rules.require_target(data.get("product_handle"))
            except ageaura_rules.AgeAuraProductError as err:
                problems.append(name + ": " + str(err))
        elif cluster == "shilasource":
            if data.get("product_handle") != SHILA_HANDLE:
                problems.append(name + ": ShilaSource seed must target " + SHILA_HANDLE)
        else:
            problems.append(name + ": unknown cluster")
        found[cluster] = queries
    total = sum(len(v) for v in found.values())
    if total < 20 or total > 40:
        problems.append("seed query count %s is outside 20-40" % total)
    if "ageaura" not in found or "shilasource" not in found:
        problems.append("seeds need both ageaura and shilasource")
    return found, problems


def load_document(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        data = {"sources": data}
    data.setdefault("sources", [])
    data.setdefault("ai_citation_note", (
        "No ChatGPT, Perplexity, or Google AI Overview session was run. "
        "ai_citation_observed is false on every source."
    ))
    return data


def score_document(doc):
    doc = dict(doc)
    doc["sources"] = [assess(rec) for rec in doc.get("sources") or []]
    return doc


def guard_copy(text):
    problems = []
    problems.extend(ageaura_rules.text_target_violations(text))
    low = (text or "").lower()
    if "urolithin" in low:
        problems.append("urolithin named")
    if "/collections/ageaura" in low:
        problems.append("ageaura collection linked")
    if "cited by chatgpt" in low or "cited by perplexity" in low or "cited by ai overview" in low:
        problems.append("invented AI citation")
    if "domain rating" in low or "monthly traffic" in low or "search volume" in low:
        problems.append("invented traffic or authority figure")
    problems.extend(shilasource_resin_rules.violations(text))
    return problems


_DOSE_IN_LABEL = re.compile(
    r"\d+(?:\.\d+)?\s*(?:mg|mcg|g|oz|ml|%|servings?|capsules?)\b",
    re.I,
)


def safe_label(text):
    """Drop dose figures from a title so the report can name ShilaSource and still pass the resin lock."""
    return _DOSE_IN_LABEL.sub("a labeled amount", text or "")


def _fmt_brands(brands, limit=8):
    brands = brands or []
    shown = brands[:limit]
    extra = len(brands) - len(shown)
    text = ", ".join(shown) if shown else "(none confirmed)"
    if extra > 0:
        text += " (+%s more)" % extra
    return text


def render_report(doc, seeds):
    sources = doc.get("sources") or []
    log = doc.get("fetch_log") or {}
    lines = []
    lines.append("# Off-page listicle gap list — 2026-10-20")
    lines.append("")
    lines.append("Draft research for Wellness Nest. No email was sent. No Shopify write was made.")
    lines.append("")
    lines.append("Spark: Search Engine Land, [How to audit off-page AI search visibility and build a 90-day plan](https://searchengineland.com/audit-off-page-ai-search-visibility-90-day-plan-494866) (published October 12, 2026). The article says third-party listicles and comparison pages matter, and it sorts them by how often an AI-visibility tool retrieved them. This run did not use that tool. Every row has `ai_citation_observed: false`. The evidence field is `web search rank`, plus a page GET when the fetch succeeded.")
    lines.append("")
    lines.append(doc.get("ai_citation_note") or "")
    lines.append("")
    lines.append("## Products in scope")
    lines.append("")
    lines.append("- AgeAura outreach is only " + ageaura_rules.PRODUCT_LABEL + ": " + ageaura_rules.PRODUCT_URL)
    lines.append("- ShilaSource outreach is only " + SHILA_NAME + ": " + SHILA_URL)
    lines.append("- Pack lines that may be quoted live in the matching `product_refs/*.label.json` file. Do not add a milligram amount.")
    lines.append("")
    lines.append("## Hypothesised prompts")
    lines.append("")
    lines.append("These are hypothesised prompts, not questions observed in an answer engine.")
    lines.append("")
    for cluster in ("ageaura", "shilasource"):
        lines.append("### " + cluster)
        lines.append("")
        for query in seeds.get(cluster) or []:
            lines.append("- " + query + " — hypothesised")
        lines.append("")
    lines.append("## Fetch")
    lines.append("")
    lines.append("| Counter | Value |")
    lines.append("|---|---|")
    lines.append("| GET budget | %s |" % log.get("budget", GET_BUDGET))
    lines.append("| GETs used | %s |" % log.get("gets", 0))
    lines.append("| HTTP 200 | %s |" % log.get("http_200", 0))
    lines.append("| HTTP 429 | %s |" % log.get("http_429", 0))
    lines.append("| HTTP 404 | %s |" % log.get("http_404", 0))
    lines.append("| robots disallow | %s |" % log.get("robots_disallow", 0))
    lines.append("| other non-200 | %s |" % log.get("other_status", 0))
    lines.append("")
    if not log.get("gets"):
        lines.append("Fetch has not been run yet. Scores below use the search-snippet brand lists stored with each URL, at a lower confidence than a fetched page.")
        lines.append("")
    lines.append("The GET count includes robots.txt and contact-page checks, not only article URLs. A robots.txt Disallow skips that article URL. A 429 waits and retries once. A 403 on robots.txt is not treated as a disallow, because the rules were not readable; the article GET still counts toward the budget.")
    if log.get("notes"):
        lines.append("")
        lines.append(log["notes"])
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append("| Cluster | Sources | Already name us | Gaps |")
    lines.append("|---|---|---|---|")
    for cluster in ("ageaura", "shilasource"):
        rows = [r for r in sources if r.get("cluster") == cluster]
        named = [r for r in rows if r.get("us_mentioned")]
        gaps = [r for r in rows if r.get("is_gap")]
        lines.append("| %s | %s | %s | %s |" % (cluster, len(rows), len(named), len(gaps)))
    lines.append("")
    lines.append("## How a gap is scored")
    lines.append("")
    lines.append("A gap is a page that names at least one other brand and does not name Wellness Nest or the cluster brand. An explainer needs two other brands. Studies are not gaps. The score adds a page-type weight, up to six brands, and a small bonus when a 2025 or 2026 date is shown on the page. A search snippet is weighted lower than a fetched page. Competitor-owned roundups stay in the list and are marked do-not-pitch. A gummy URL can still score as a gap; the resin sample is not the pitch for that URL. Nothing here is a retrieval count.")
    lines.append("")
    for cluster, heading in (
        ("ageaura", "AgeAura Pure NMN + TMG"),
        ("shilasource", "ShilaSource / shilajit"),
    ):
        lines.append("## Top gaps — " + heading)
        lines.append("")
        top = rank_gaps(sources, cluster, 15)
        if len(top) < 15:
            lines.append("Confirmed gaps in this cluster: %s. The list is shorter than 15 because other checked URLs named us, named no competitor, or could not be read." % len(top))
            lines.append("")
        if not top:
            lines.append("No confirmed gap in this cluster.")
            lines.append("")
            continue
        for i, rec in enumerate(top, 1):
            title = safe_label(rec.get("title") or rec.get("url"))
            lines.append("### %s. %s" % (i, title))
            lines.append("")
            lines.append("- Score: %s. Type: %s. Domain: `%s`." % (
                rec.get("gap_score"), rec.get("page_type"), rec.get("domain")))
            lines.append("- URL: " + rec.get("url"))
            shown = rec.get("date_shown") or "not shown in the text we read"
            if rec.get("date_shown") and rec.get("date_source") == "html_meta":
                shown += " (from the page date meta; the byline was outside the first screen of prose)"
            lines.append("- Date shown: " + shown)
            if rec.get("read_note"):
                lines.append("- Note: " + rec["read_note"])
            lines.append("- How found: " + (rec.get("how_found") or "web search rank")
                         + ". Evidence: " + (rec.get("evidence") or "web search rank")
                         + ". Basis: " + (rec.get("mention_basis") or "unreadable")
                         + ". `ai_citation_observed: false`.")
            lines.append("- Other brands named: " + _fmt_brands(rec.get("competitor_brands")))
            lines.append("- Wellness Nest / cluster brand: absent")
            pitch = (rec.get("outreach") or {}).get("action") or ""
            contact = (rec.get("outreach") or {}).get("contact_url") or ""
            if contact:
                lines.append("- Editor contact page (public, checked this run): " + contact)
            else:
                lines.append("- Editor contact page: none confirmed")
            lines.append("- Outreach: " + pitch + ". " + (rec.get("outreach") or {}).get("offer", ""))
            lines.append("")
    lines.append("## Pages that already name us")
    lines.append("")
    named_rows = [r for r in sources if r.get("us_mentioned")]
    if not named_rows:
        lines.append("None of the checked URLs named Wellness Nest, AgeAura, or ShilaSource in the text this run used.")
        lines.append("")
    else:
        lines.append("These are not gaps. Do not paste their numbers into a pitch. Several shilajit reviews add figures that are not on the resin pack file.")
        lines.append("")
        for rec in named_rows:
            marks = ", ".join(rec.get("us_marks") or []) or "named"
            lines.append("- %s — %s — marks: %s — basis: %s" % (
                rec.get("cluster"), rec.get("url"), marks, rec.get("mention_basis")))
        lines.append("")
    lines.append("## 90-day sequence")
    lines.append("")
    lines.append("This follows the article's three streams (directories, outreach, objections) without pretending we measured retrievals.")
    lines.append("")
    lines.append("### Days 1-30 — lock the facts, still no send")
    lines.append("")
    lines.append("1. Treat this file as the source map. Do not assign a retrieval tier.")
    lines.append("2. Write one public HTML fact sheet per product. Use the label file only. Do not put the only copy of a proof in a PDF.")
    lines.append("3. Re-check each contact URL in the gap list. Drop any that no longer resolve.")
    lines.append("4. Kevin decides whether a sample may ship, and which roster person may be quoted.")
    lines.append("")
    lines.append("### Days 31-60 — draft pitches, highest independent score first")
    lines.append("")
    lines.append("1. Pitch only rows whose outreach action is `draft_only`.")
    lines.append("2. Skip `do_not_pitch` (Reddit, competitor-owned roundups, affiliate reviews, review directories).")
    lines.append("3. One publication at a time. Use the contact page. Do not harvest personal addresses from an old pitch article.")
    lines.append("4. Offer the sample, the label lines, and a roster quote if Kevin named the person. Do not lead with a lab test or a COA.")
    lines.append("5. AgeAura pitches name only the NMN + TMG product above.")
    lines.append("6. A gummy URL is not a resin pitch. Offer the resin sample on a resin or general shilajit ranking.")
    lines.append("")
    lines.append("### Days 61-90 — remeasure what this script can remeasure")
    lines.append("")
    lines.append("1. Run the fetch again. Compare `us_mentioned` with this file.")
    lines.append("2. A new mention on a page we fetched is the result this method can claim.")
    lines.append("3. An answer-engine citation still requires someone to observe that engine. This sequence does not do that.")
    lines.append("4. Trustpilot already lists Wellness Nest. This run did not census other directories.")
    lines.append("5. Pages that already name ShilaSource and add off-label figures are a correction decision, not a gap pitch.")
    lines.append("")
    lines.append("## Needs a Kevin GO")
    lines.append("")
    lines.append("- Sending any email, form, or sample.")
    lines.append("- Naming a roster person as the quote.")
    lines.append("- Publishing an HTML lab page, or leading a pitch with a COA. The house rule is that a lab test is not the lead advantage. The ShilaSource lab-as-the-pitch angle stays retired.")
    lines.append("- A reply on Reddit.")
    lines.append("- Asking a site that already names us to change a figure.")
    lines.append("- Paying for an AI-visibility tool if a real retrieval ranking is wanted later.")
    lines.append("")
    lines.append("## Rerun")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 scripts/offpage_listicle_gap.py --check")
    lines.append("python3 scripts/offpage_listicle_gap.py --fetch --report docs/OFFPAGE_LISTICLE_GAP_2026-10-20.md")
    lines.append("python3 -m unittest tests/test_offpage_listicle_gap.py")
    lines.append("```")
    lines.append("")
    text = "\n".join(lines)
    problems = guard_copy(text)
    if problems:
        raise SystemExit("report failed the copy guard: " + "; ".join(problems))
    return text


class Budget:
    def __init__(self, limit):
        self.limit = limit
        self.gets = 0
        self.http_200 = 0
        self.http_429 = 0
        self.http_404 = 0
        self.robots_disallow = 0
        self.other_status = 0

    def as_dict(self):
        return {
            "budget": self.limit,
            "gets": self.gets,
            "http_200": self.http_200,
            "http_429": self.http_429,
            "http_404": self.http_404,
            "robots_disallow": self.robots_disallow,
            "other_status": self.other_status,
        }

    def note(self, status):
        self.gets += 1
        if status == 200:
            self.http_200 += 1
        elif status == 429:
            self.http_429 += 1
        elif status == 404:
            self.http_404 += 1
        else:
            self.other_status += 1
        return self.gets <= self.limit


def _request(url):
    return Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,text/plain",
        "Accept-Encoding": "identity",
    })


def _read(opener, url, timeout):
    req = _request(url)
    try:
        resp = opener(req, timeout=timeout)
    except HTTPError as err:
        resp = err
    except (URLError, TimeoutError, OSError) as err:
        return {"status": 0, "body": b"", "final_url": url, "error": str(getattr(err, "reason", err))}
    status = getattr(resp, "status", None) or getattr(resp, "code", 200)
    try:
        body = resp.read(MAX_BYTES)
    except Exception as err:
        return {"status": int(status or 0), "body": b"", "final_url": url, "error": str(err)}
    final = resp.geturl() if hasattr(resp, "geturl") else url
    return {"status": int(status or 0), "body": body, "final_url": final, "error": ""}


def _decode(body):
    return (body or b"").decode("utf-8", "replace")


def robots_allows(robots_status, robots_body, page_url):
    """True when we may GET the page. 404 means no robots file. Other non-200 means unreadable, not a disallow."""
    if robots_status == 404:
        return True
    if robots_status != 200:
        return True
    from urllib.robotparser import RobotFileParser
    parser = RobotFileParser()
    parser.parse(_decode(robots_body).splitlines())
    return parser.can_fetch(UA, page_url)


def fetch_sources(doc, opener=None, sleeper=None, timeout=15, budget_limit=GET_BUDGET):
    opener = opener or urlopen
    sleeper = sleeper or time.sleep
    budget = Budget(budget_limit)
    robots_cache = {}
    contacts = {}
    out_sources = []

    def one_get(url):
        if budget.gets >= budget.limit:
            return {"status": 0, "body": b"", "final_url": url, "error": "budget", "skipped": True}
        sleeper(0.35 if budget.gets else 0)
        result = _read(opener, url, timeout)
        ok = budget.note(result["status"])
        result["over_budget"] = not ok
        if result["status"] == 429 and budget.gets < budget.limit:
            sleeper(8)
            result = _read(opener, url, timeout)
            budget.note(result["status"])
            result["retried_429"] = True
        return result

    for rec in doc.get("sources") or []:
      try:
        url = rec.get("url") or ""
        host = urlparse(url).netloc
        robots = robots_cache.get(host)
        if robots is None and url:
            robots_url = "%s://%s/robots.txt" % (urlparse(url).scheme or "https", host)
            robots = one_get(robots_url)
            robots_cache[host] = robots
        fetched = None
        note = ""
        if not url:
            note = "missing url"
        elif robots and robots.get("skipped"):
            note = "budget exhausted before robots"
        elif robots and not robots_allows(robots.get("status"), robots.get("body"), url):
            budget.robots_disallow += 1
            note = "robots disallow"
        else:
            if robots and robots.get("status") not in (200, 404, None):
                note = "robots status %s; page still requested" % robots.get("status")
            page = one_get(url)
            if page.get("skipped"):
                note = "budget exhausted"
            elif page.get("status") == 200:
                raw = _decode(page.get("body"))
                text = html_to_text(raw)
                title = html_title(raw)
                meta_date = "" if find_date(text) else find_html_date(raw)
                fetched = {
                    "ok": True,
                    "status": 200,
                    "final_url": page.get("final_url") or url,
                    "text": text,
                    "title": title,
                    "meta_date": meta_date,
                }
            else:
                note = (note + "; " if note else "") + "HTTP %s %s" % (page.get("status"), page.get("error") or "")
                fetched = {"ok": False, "status": page.get("status"), "note": note.strip("; ")}
        updated = dict(rec)
        if fetched and fetched.get("ok"):
            if fetched.get("title"):
                updated["title"] = fetched["title"]
            updated["http_status"] = 200
            updated["final_url"] = fetched.get("final_url")
            updated["fetch_note"] = note
            updated = assess(updated, fetched.get("text"), basis="fetched_body")
            if fetched.get("meta_date") and not updated.get("date_shown"):
                updated["date_shown"] = fetched["meta_date"]
                updated["date_source"] = "html_meta"
                updated = apply_score(updated)
        else:
            updated["http_status"] = (fetched or {}).get("status") or updated.get("http_status")
            if note:
                updated["fetch_note"] = note
            updated = assess(updated, None, basis="search_snippet" if rec.get("search_brands") is not None else None)
        out_sources.append(updated)
        print("fetched %s %s" % (updated.get("http_status"), url), file=sys.stderr)
      except Exception as err:
        failed = assess(dict(rec), None, basis="search_snippet" if isinstance(rec.get("search_brands"), list) else None)
        failed["fetch_note"] = "fetch error: " + str(err)
        out_sources.append(failed)
        print("error %s %s" % (rec.get("url"), err), file=sys.stderr)

    domains = sorted({domain_of(r.get("url")) for r in out_sources if r.get("is_gap") and r.get("page_type") in PITCH_OK})
    for host in domains:
        if host in contacts or budget.gets >= budget.limit:
            continue
        for candidate in CONTACT_TRIES.get(host, []):
            if budget.gets >= budget.limit:
                break
            try:
                page = one_get(candidate)
            except Exception as err:
                print("contact error %s %s" % (candidate, err), file=sys.stderr)
                continue
            final = page.get("final_url") or candidate
            if page.get("status") == 200 and (domain_of(final) == host or domain_of(candidate) == host):
                contacts[host] = final
                print("contact %s" % final, file=sys.stderr)
                break
    for rec in out_sources:
        host = domain_of(rec.get("url"))
        if host in contacts and rec.get("page_type") in PITCH_OK:
            rec["editor_contact_url"] = contacts[host]
            rec["outreach"] = outreach_for(rec)

    doc = dict(doc)
    doc["sources"] = out_sources
    doc["fetch_log"] = budget.as_dict()
    doc["fetched_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    return doc


def _summary(doc):
    sources = doc.get("sources") or []
    lines = []
    log = doc.get("fetch_log") or {}
    lines.append("gets: %s" % log.get("gets", 0))
    for cluster in ("ageaura", "shilasource"):
        rows = [r for r in sources if r.get("cluster") == cluster]
        named = sum(1 for r in rows if r.get("us_mentioned"))
        gaps = sum(1 for r in rows if r.get("is_gap"))
        lines.append("%s sources: %s gaps: %s already_mention_us: %s" % (cluster, len(rows), gaps, named))
        for rec in rank_gaps(rows, cluster, 5):
            lines.append("  top %s %s" % (rec.get("gap_score"), rec.get("url")))
    return "\n".join(lines)


def main(argv):
    parser = argparse.ArgumentParser(description="Score off-page listicle gaps. Does not email or publish.")
    parser.add_argument("--seeds", default=DEFAULT_SEEDS)
    parser.add_argument("--sources", default=DEFAULT_SOURCES)
    parser.add_argument("--report", default="")
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--budget", type=int, default=GET_BUDGET)
    args = parser.parse_args(argv)
    seeds, problems = validate_seeds(args.seeds)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 2
    doc = load_document(args.sources)
    if args.fetch:
        doc = fetch_sources(doc, budget_limit=args.budget)
        with open(args.sources, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    else:
        doc = score_document(doc)
    report_path = args.report
    if args.check and not report_path and not args.fetch:
        print(_summary(doc))
        print("seeds: %s" % sum(len(v) for v in seeds.values()))
        return 0
    if report_path or args.fetch:
        path = report_path or DEFAULT_REPORT
        text = render_report(doc, seeds)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("report: " + path)
    print(_summary(doc))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

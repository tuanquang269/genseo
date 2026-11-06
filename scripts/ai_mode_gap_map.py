#!/usr/bin/env python3
"""Map hypothesised AI Mode follow-ups onto AgeAura NMN + TMG headings.

The seed queries are hypothesised fan-out branches. This script does not call
Google AI Mode, and it does not invent search volumes or answer text.

Google's guidance (2026-10-08, recorded in knowledge_base/AEO_GEO_GUIDELINES.md
§6.1): a separate page for each fan-out query is scaled content abuse. A gap
here becomes an H2 or FAQ on a page that already exists, unless the seed marks
the branch as a thin URL to reject.

Coverage ignores denied AgeAura handles (see ageaura_rules.py). A heading on
those URLs is not coverage for AgeAura Pure NMN + TMG NAD+ Complex.

  python3 scripts/ai_mode_gap_map.py --lint-seed
  python3 scripts/ai_mode_gap_map.py --crawl \\
      --seed data/ai_mode_seeds/ageaura_nmn_tmg.json \\
      --crawl-out data/ai_mode_seeds/ageaura_nmn_tmg.crawl.json \\
      --report docs/AI_MODE_GAP_MAP_AGEAURA_2026-10-20.md
  python3 scripts/ai_mode_gap_map.py --from-crawl data/ai_mode_seeds/ageaura_nmn_tmg.crawl.json \\
      --report docs/AI_MODE_GAP_MAP_AGEAURA_2026-10-20.md

Public GETs only. Default cap is 200 requests. HTTP 429 backs off. No Shopify
writes.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

import ageaura_rules

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://wellnessnest.co"
PRODUCT_URL = ageaura_rules.PRODUCT_URL
ROBOTS_URL = SITE + "/robots.txt"
SITEMAP_URL = SITE + "/sitemap.xml"
UA = "GenSeoGapMap/1.0 (public read-only research; wellnessnest.co AgeAura cluster)"
MAX_GETS = 200
DEFAULT_DELAY = 1.0
BACKOFF_SECONDS = (5, 15, 45)
REQUEST_TIMEOUT = 25

CLUSTER_RE = re.compile(r"(nmn|tmg|\bnad\b|ageaura|nicotinamide)", re.I)
SM_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

CHROME = {
    "shop all",
    "learn",
    "help",
    "share",
    "your cart is empty",
    "subscribe to our emails",
    "your path to ultimate wellness",
    "our policy",
    "country/region",
    "country region",
    "language",
    "shop this article",
    "about the author",
    "frequently asked questions",
    "frequently asked question",
    "we have answers",
}
FOOTER = {"your path to ultimate wellness", "our policy"}

FLAG_NOTES = {
    "milligram": "The OCR label file has no milligram line. Do not copy this number into a new H2.",
    "percent": "A percent or trial figure needs the citation already on the page. Do not add a new one.",
    "dollar": "A dollar figure is a snapshot. Re-check the live product page before repeating it.",
    "urolithin": "Urolithin is not the AgeAura SKU this cluster may promote.",
    "other_sku": "Peptides or a duo are not the AgeAura SKU this cluster may promote.",
    "seven_actives": "The OCR label lines do not say seven actives. Verify before repeating.",
    "cofactor": "This cofactor is not an OCR label line. Verify before calling it an AgeAura ingredient.",
    "clinical_proof": "COA, lab-tested, or clinically tested is not a lead claim. Confirm the source first.",
    "disease": "Disease-treatment wording. Do not extend it.",
    "denied_product_url": "This URL is a denied AgeAura target. It does not count as coverage.",
    "denied_product_link": "This page links a denied AgeAura product. Do not use that link as the cluster target.",
}

FLAG_PATTERNS = (
    ("milligram", re.compile(r"\b\d[\d,]*\s*mg\b", re.I)),
    ("percent", re.compile(r"\b\d+(?:\.\d+)?\s*%")),
    ("dollar", re.compile(r"\$\s*\d")),
    ("urolithin", re.compile(r"\burolithin\b", re.I)),
    ("other_sku", re.compile(
        r"\b(?:longevity peptides|rejuvenation duo|essential longevity duo)\b",
        re.I,
    )),
    ("seven_actives", re.compile(r"\b(?:seven|7)\s+actives\b", re.I)),
    ("cofactor", re.compile(
        r"\b(?:quercetin|trans-resveratrol|apigenin|spermidine|methylfolate|l-5-mthf)\b",
        re.I,
    )),
    ("clinical_proof", re.compile(
        r"\b(?:clinically tested|clinically proven|lab-tested|third-party tested|"
        r"certificate of analysis|\bCOA\b)\b",
        re.I,
    )),
    ("disease", re.compile(
        r"\b(?:cures?|treats?|prevents?|reverses?)\b.{0,40}\b"
        r"(?:cancer|alzheimer(?:'?s)?|dementia|diabetes|heart disease)\b",
        re.I,
    )),
)

_WORD = re.compile(r"[^a-z0-9']+")


def norm(value):
    text = (value or "").lower().replace("+", " and ").replace("&", " and ")
    text = text.replace("’", "'").replace("“", " ").replace("”", " ")
    text = _WORD.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def phrase_in(phrase, text):
    """Whole-phrase match. The last word also matches a simple trailing plural."""
    needle = norm(phrase)
    hay = norm(text)
    if not needle or not hay:
        return False
    parts = needle.split(" ")
    last = parts[-1]
    # "capsule" matches "capsules". A word that already ends in s stays exact
    # ("reviews" must not also match an unrelated stem).
    last_pat = re.escape(last) if last.endswith("s") else re.escape(last) + "s?"
    if len(parts) == 1:
        body = last_pat
    else:
        body = " ".join(re.escape(part) for part in parts[:-1]) + " " + last_pat
    return re.search(r"(?<![a-z0-9])" + body + r"(?![a-z0-9])", hay) is not None


def groups_hit(text, groups):
    """True when one alternative matches. Each alternative is a list of phrases."""
    for alt in groups or []:
        if alt and all(phrase_in(part, text) for part in alt):
            return True
    return False


def is_chrome(text):
    n = norm(text)
    if not n or n in CHROME:
        return True
    if n.startswith("cart ") or n.startswith("get wellness nest"):
        return True
    return False


def coverage_allowed(url):
    """False for a denied AgeAura product URL or the AgeAura collection.

    A landing slug such as /pages/ageaura-pure-protocol is not a product handle.
    Only /products/<handle> and /collections/ageaura are judged here.
    """
    path = urlparse(url or "").path.lower()
    if "/collections/ageaura" in path or "urolithin" in path:
        return False
    if "/products/" not in path:
        return True
    for handle in ageaura_rules.handles_in_text(path):
        if ageaura_rules.classify_handle(handle) == "deny":
            return False
    return True


def kind_of(url):
    path = urlparse(url or "").path
    if path.startswith("/products/"):
        return "product"
    if path.startswith("/blogs/"):
        return "article"
    if path.startswith("/pages/"):
        return "landing"
    return "other"


def is_default_locale_content(url):
    path = urlparse(url or "").path
    return (
        path.startswith("/products/")
        or path.startswith("/pages/")
        or path.startswith("/blogs/")
    )


def is_english_sitemap(url):
    path = urlparse(url or "").path
    if path.count("/") != 1:
        return False
    name = path.rsplit("/", 1)[-1]
    return name.startswith((
        "sitemap_products_",
        "sitemap_pages_",
        "sitemap_articles_",
    ))


def select_cluster_urls(locs):
    """Cluster URLs from sitemap locs, plus the allowed product if missing."""
    found = []
    seen = set()
    for raw in locs:
        url = (raw or "").split("#", 1)[0].strip()
        if not url or not is_default_locale_content(url):
            continue
        url = url.split("?", 1)[0]
        if not CLUSTER_RE.search(url):
            continue
        if url in seen:
            continue
        seen.add(url)
        found.append(url)
    if PRODUCT_URL not in seen:
        found.insert(0, PRODUCT_URL)
    return found


def parse_locs(xml_bytes):
    """Sitemap <loc> values. A bad document returns an empty list."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []
    locs = []
    for node in root.iter(SM_NS + "loc"):
        if node.text:
            locs.append(node.text.strip())
    if locs:
        return locs
    # Some feeds omit the namespace.
    for node in root.iter("loc"):
        if node.text:
            locs.append(node.text.strip())
    return locs


def _excerpt(text, match, width=70):
    start = max(0, match.start() - width)
    end = min(len(text), match.end() + width)
    snip = re.sub(r"\s+", " ", text[start:end]).strip()
    return snip[:220]


# Cautionary sentences name a disease or a certificate in order to refuse it.
_DISEASE_CAUTION = re.compile(
    r"medical promise|should make you|structure/function|do not claim|not a treatment",
    re.I,
)
_PROOF_NEGATION = re.compile(
    r"\b(?:does not|do not|don't|not published|does not show|do not show|"
    r"have not|has not|not going to|no certificate|not show a)\b",
    re.I,
)


def _clause(text, start, end):
    """The sentence that holds a match, so a nearby caution does not hide a later claim."""
    begin = 0
    for mark in ".!?":
        found = text.rfind(mark, 0, start)
        if found + 1 > begin:
            begin = found + 1
    finish = len(text)
    for mark in ".!?":
        found = text.find(mark, end)
        if found >= 0:
            finish = min(finish, found + 1)
    return text[begin:finish]


def _skip_flag(kind, window):
    if kind == "disease" and _DISEASE_CAUTION.search(window):
        return True
    if kind == "clinical_proof" and _PROOF_NEGATION.search(window):
        return True
    return False


def flag_text(text, limit=2):
    """Claim flags. These are checks, not facts to republish."""
    flags = []
    blob = text or ""
    for kind, rx in FLAG_PATTERNS:
        excerpts = []
        for match in rx.finditer(blob):
            if _skip_flag(kind, _clause(blob, match.start(), match.end())):
                continue
            snip = _excerpt(blob, match)
            if snip not in excerpts:
                excerpts.append(snip)
            if len(excerpts) >= limit:
                break
        for snip in excerpts:
            flags.append({"kind": kind, "excerpt": snip})
    return flags


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.capture_script = False
        self.script = []
        self.cur = None
        self.buf = []
        self.headings = []
        self.seen_h1 = False
        self.ended = False
        self.in_content = False
        self.parts = []
        self.links = []
        self.noindex = False
        self.canonical = ""
        self.og_title = ""
        self.h1 = ""

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        attr = {k.lower(): (v or "") for k, v in attrs}
        if t in ("script", "style", "noscript"):
            self.skip += 1
            self.capture_script = t == "script" and "ld+json" in attr.get("type", "").lower()
            self.script = []
            return
        if self.skip:
            return
        if t == "meta":
            name = attr.get("name", "").lower()
            prop = attr.get("property", "").lower()
            content = attr.get("content", "")
            if name == "robots" and "noindex" in content.lower():
                self.noindex = True
            if prop == "og:title" and content.strip():
                self.og_title = re.sub(r"\s+", " ", content).strip()
        elif t == "link" and "canonical" in attr.get("rel", "").lower():
            self.canonical = attr.get("href", "").strip()
        elif t == "a" and self.in_content and not self.ended:
            href = attr.get("href", "")
            if href:
                self.links.append(href)
        if t in ("h1", "h2", "h3", "summary"):
            self.cur = t
            self.buf = []

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("script", "style", "noscript"):
            if self.skip:
                self.skip -= 1
            if t == "script" and self.capture_script:
                self._consume_json("".join(self.script))
            self.capture_script = False
            self.script = []
            return
        if self.skip or t != self.cur:
            return
        text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        self.cur = None
        self.buf = []
        if not text:
            return
        self._add_heading(t if t != "summary" else "summary", text)

    def handle_data(self, data):
        if self.skip:
            if self.capture_script:
                self.script.append(data)
            return
        if self.cur:
            self.buf.append(data)
        if self.in_content and not self.ended and data.strip():
            self.parts.append(data)

    def _add_heading(self, level, text):
        n = norm(text)
        if level in ("h1", "h2") and n in FOOTER and self.seen_h1:
            self.ended = True
            self.in_content = False
            return
        # FAQ JSON-LD often sits in <head>, before the visible h1. Keep those
        # questions. Drop them once the footer has started.
        if level == "faq":
            if self.ended or is_chrome(text):
                return
            self._remember(level, text)
            return
        if level == "h1" and not self.h1 and not is_chrome(text):
            self.h1 = text
            self.seen_h1 = True
            self.in_content = True
        if not self.seen_h1 or self.ended or is_chrome(text):
            return
        self._remember(level, text)

    def _remember(self, level, text):
        n = norm(text)
        if not n or is_chrome(text):
            return
        for item in self.headings:
            if norm(item["text"]) == n:
                # Prefer a visible heading over the same question from FAQ schema.
                if item["level"] == "faq" and level in ("h1", "h2", "h3", "summary"):
                    item["level"] = level
                    item["text"] = text[:240]
                return
        self.headings.append({"level": level, "text": text[:240]})

    def _consume_json(self, raw):
        if "Question" not in raw and "FAQPage" not in raw:
            return
        raw = raw.strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return
        self._walk(data)

    def _walk(self, obj):
        if isinstance(obj, list):
            for item in obj:
                self._walk(item)
            return
        if not isinstance(obj, dict):
            return
        types = obj.get("@type")
        if not isinstance(types, list):
            types = [types]
        if "Question" in types and isinstance(obj.get("name"), str):
            self._add_heading("faq", obj["name"])
        answer = obj.get("acceptedAnswer")
        if isinstance(answer, dict) and isinstance(answer.get("text"), str):
            self.parts.append(" ")
            self.parts.append(answer["text"])
        for value in obj.values():
            if isinstance(value, (dict, list)):
                self._walk(value)


def extract_page(html, url, status=200):
    """Headings, FAQ questions, and claim flags from one public HTML document."""
    parser = _PageParser()
    if isinstance(html, bytes):
        html = html.decode("utf-8", "replace")
    try:
        parser.feed(html or "")
        parser.close()
    except Exception:
        # A truncated page still keeps whatever was parsed before the error.
        pass
    text = re.sub(r"\s+", " ", "".join(parser.parts)).strip()
    heading_blob = " ".join(item["text"] for item in parser.headings)
    flags = flag_text((text + " " + heading_blob).strip())
    product_links = []
    denied_links = []
    for href in parser.links:
        for handle in ageaura_rules.handles_in_text(href):
            if handle not in product_links:
                product_links.append(handle)
            if ageaura_rules.classify_handle(handle) == "deny" and handle not in denied_links:
                denied_links.append(handle)
    for handle in denied_links:
        flags.append({
            "kind": "denied_product_link",
            "excerpt": "/products/" + handle,
        })
    allowed = coverage_allowed(url)
    if not allowed:
        flags.append({"kind": "denied_product_url", "excerpt": url})
    h1 = parser.h1
    built = {
        "url": url,
        "final_url": url,
        "status": status,
        "kind": kind_of(url),
        "noindex": parser.noindex,
        "canonical": parser.canonical,
        "og_title": parser.og_title,
        "h1": h1,
        "headings": parser.headings,
        "coverage_allowed": allowed,
        "product_links": product_links,
        "flags": flags,
    }
    built["indexable"] = ineligible_reason(built) == ""
    return built


def ineligible_reason(page):
    """Why a fetched page must not count as AgeAura NMN + TMG coverage."""
    if page.get("status") != 200:
        return "HTTP %s" % page.get("status")
    if page.get("noindex"):
        return "noindex"
    if not coverage_allowed(page.get("url") or ""):
        return "denied product URL"
    for heading in page.get("headings") or []:
        text = heading.get("text") or ""
        if phrase_in("urolithin", text) or phrase_in("longevity peptide", text) or phrase_in("rejuvenation duo", text):
            return "heading names a different AgeAura product"
    for flag in page.get("flags") or []:
        if flag.get("kind") in ("urolithin", "other_sku", "denied_product_url"):
            return "page names a different AgeAura product"
    return ""


def usable(page):
    return ineligible_reason(page) == ""


def _hits(page, groups):
    found = []
    for heading in page.get("headings") or []:
        if groups_hit(heading.get("text", ""), groups):
            found.append(heading)
    return found


def _pick(hits, home_urls):
    """Prefer the seed's home URLs, in order. hits are (page, heading)."""
    homes = [u.rstrip("/") for u in home_urls or []]
    for home in homes:
        for page, heading in hits:
            if (page.get("url") or "").rstrip("/") == home:
                return page, heading
    return hits[0]


def classify_query(query, pages):
    """COVERED, PARTIAL, or GAP for one hypothesised follow-up.

    Noindex URLs and denied product URLs never count as coverage.
    """
    homes = query.get("home_urls") or []
    indexable = [p for p in pages if usable(p)]
    hidden = [p for p in pages if p.get("status") == 200 and not usable(p)]

    cover = []
    for page in indexable:
        for heading in _hits(page, query.get("cover")):
            cover.append((page, heading))
    if cover:
        page, heading = _pick(cover, homes)
        return _row(query, "COVERED", page["url"], heading, "none", (
            "Heading on %s (%s): %s" % (page["url"], heading["level"], heading["text"])
        ))

    partial = []
    for page in indexable:
        matched = _hits(page, query.get("partial"))
        if matched:
            partial.append((page, matched[0]))
    note = _hidden_note(query, hidden)
    if not cover and not partial and query.get("gap_action") == "reject_thin":
        related = []
        for page in indexable:
            matched = _hits(page, query.get("related"))
            if matched:
                related.append((page, matched[0]))
        if related:
            page, heading = related[0]
            note = (
                "A related heading is already on %s (%s: %s). "
                "That heading is not a reason to add a new URL."
            ) % (page["url"], heading["level"], heading["text"])
            if _hidden_note(query, hidden):
                note = note + " " + _hidden_note(query, hidden)
    if partial:
        page, heading = _pick(partial, homes)
        reason = (
            "%s has “%s” (%s) and does not have this follow-up as its own heading. "
            "Add an H2 or FAQ on that page."
        ) % (page["url"], heading["text"], heading["level"])
        if note:
            reason = reason + " " + note
        return _row(query, "PARTIAL", page["url"], heading, "add_h2", reason)

    target = homes[0] if homes else ""
    action = query.get("gap_action") or "add_h2"
    if action == "add_h2":
        reason = (
            "No indexable heading matched. Add an H2 or FAQ on %s. "
            "A new URL for this follow-up would be another fan-out page."
        ) % (target or "the existing pillar")
    elif action == "reject_thin":
        reason = query.get("decision_reason") or "Thin fan-out URL. Do not create one."
    else:
        reason = query.get("decision_reason") or query.get("justification") or ""
    if note:
        reason = reason + " " + note
    return _row(query, "GAP", target, None, action, reason)


def _hidden_note(query, pages):
    for page in pages:
        matched = _hits(page, query.get("cover"))
        if matched:
            why = ineligible_reason(page) or "not eligible"
            return "A page (%s) has a matching heading and does not count: %s." % (why, page.get("url"))
    return ""


def _row(query, status, url, heading, action, reason):
    if status == "COVERED":
        action = "none"
    return {
        "id": query["id"],
        "query": query["query"],
        "branch": query.get("branch") or "",
        "pillar": query.get("pillar") or "",
        "label": query.get("label") or "hypothesised follow-up",
        "status": status,
        "page_url": url or "",
        "heading": (heading or {}).get("text", "") if heading else "",
        "heading_level": (heading or {}).get("level", "") if heading else "",
        "action": action,
        "suggested_heading": query.get("suggested_heading") or "",
        "evidence_boundary": query.get("evidence_boundary") or "",
        "priority": int(query.get("priority") or 99),
        "recheck": bool(query.get("recheck")),
        "reason": reason,
    }


def map_queries(seed, pages):
    return [classify_query(q, pages) for q in seed.get("queries") or []]


def summarize(rows):
    counts = {"COVERED": 0, "PARTIAL": 0, "GAP": 0, "add_h2": 0, "reject_thin": 0, "new_article": 0}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        if row["status"] == "GAP":
            counts[row["action"]] = counts.get(row["action"], 0) + 1
        elif row["status"] == "PARTIAL" and row["action"] == "add_h2":
            counts["add_h2"] += 1
    return counts


def lint_seed(seed):
    """Structural checks. No network."""
    errors = []
    if not isinstance(seed, dict):
        return ["seed is not an object"]
    note = seed.get("not_observed") or ""
    if "not observed" not in note.lower() and "not pulled from google ai mode" not in note.lower():
        errors.append("not_observed must say these queries were not observed in AI Mode")
    pillars = seed.get("pillars") or []
    pillar_ids = set()
    for pillar in pillars:
        pid = pillar.get("id")
        pillar_ids.add(pid)
        url = pillar.get("url") or ""
        if not url.startswith(SITE + "/"):
            errors.append("pillar %s URL is not on wellnessnest.co" % pid)
        if not coverage_allowed(url):
            errors.append("pillar %s uses a denied AgeAura URL" % pid)
        if pid == "pdp" and url.rstrip("/") != PRODUCT_URL:
            errors.append("pdp pillar must be the allowed NMN + TMG product")
    queries = seed.get("queries") or []
    if not (30 <= len(queries) <= 60):
        errors.append("query count %d is outside 30-60" % len(queries))
    seen = set()
    for query in queries:
        qid = query.get("id")
        if not qid or qid in seen:
            errors.append("duplicate or empty query id %s" % qid)
        seen.add(qid)
        if query.get("label") != "hypothesised follow-up":
            errors.append("%s label must be hypothesised follow-up" % qid)
        blob = json.dumps(query).lower()
        for banned in ("search volume", "observed in ai mode", "people also ask", "ai mode suggested"):
            if banned in blob:
                errors.append("%s contains %r" % (qid, banned))
        if query.get("pillar") not in pillar_ids:
            errors.append("%s pillar is not defined" % qid)
        action = query.get("gap_action")
        if action not in ("add_h2", "reject_thin", "new_article"):
            errors.append("%s gap_action is invalid" % qid)
        cover = query.get("cover")
        if not isinstance(cover, list) or not cover or any(not isinstance(a, list) or not a for a in cover):
            errors.append("%s cover phrases are missing" % qid)
        partial = query.get("partial", [])
        if not isinstance(partial, list) or any(not isinstance(a, list) for a in partial):
            errors.append("%s partial phrases are invalid" % qid)
        if action == "add_h2":
            homes = query.get("home_urls") or []
            if not homes:
                errors.append("%s add_h2 needs a home URL" % qid)
            heading = query.get("suggested_heading") or ""
            if not heading.endswith("?"):
                errors.append("%s suggested heading should be a question" % qid)
            if not query.get("evidence_boundary"):
                errors.append("%s needs an evidence boundary" % qid)
        if action == "reject_thin" and not (query.get("decision_reason") or "").strip():
            errors.append("%s reject_thin needs a decision reason" % qid)
        if action == "new_article":
            why = (query.get("justification") or query.get("decision_reason") or "").strip()
            if len(why) < 40:
                errors.append("%s new_article needs a justification" % qid)
        for url in query.get("home_urls") or []:
            if not str(url).startswith(SITE + "/"):
                errors.append("%s home URL is off-site" % qid)
            if not coverage_allowed(url):
                errors.append("%s home URL is a denied AgeAura target" % qid)
    return errors


def urllib_request(url, timeout=REQUEST_TIMEOUT, ua=UA):
    req = urllib.request.Request(url, headers={
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, res.read(), res.geturl(), ""
    except urllib.error.HTTPError as exc:
        body = exc.read() if exc.fp else b""
        return exc.code, body, url, ""
    except Exception as exc:
        return 0, b"", url, type(exc).__name__ + ": " + str(exc)[:180]


def fetch_one(url, state, request_fn, sleep_fn):
    """One URL, with 429 backoff. Each attempt counts toward the GET cap."""
    if state["gets"] and state["delay"]:
        sleep_fn(state["delay"])
    attempt = 0
    while True:
        if state["gets"] >= state["max_gets"]:
            state["incomplete"] = True
            return {"status": 0, "body": b"", "final_url": url, "error": "budget", "url": url}
        state["gets"] += 1
        status, body, final, err = request_fn(url)
        if status == 429 and attempt < len(BACKOFF_SECONDS):
            sleep_fn(BACKOFF_SECONDS[attempt])
            attempt += 1
            continue
        return {
            "status": status,
            "body": body if isinstance(body, bytes) else bytes(body or b""),
            "final_url": final or url,
            "error": err or "",
            "url": url,
        }


def crawl(seed=None, max_gets=MAX_GETS, delay=DEFAULT_DELAY, request_fn=None, sleep_fn=None, log=None):
    """Polite public crawl of the AgeAura NMN + TMG cluster. Returns a snapshot.

    `seed` is accepted so the CLI can pass the file it just linted. The product
    URL is always the AgeAura allowlist, not a URL typed into the seed.
    """
    if seed is not None and not isinstance(seed, dict):
        raise TypeError("seed must be a dict")
    request_fn = request_fn or urllib_request
    sleep_fn = sleep_fn or time.sleep
    log = log or (lambda *_a: None)
    state = {"gets": 0, "max_gets": max_gets, "delay": delay, "incomplete": False}
    errors = []

    def pull(url):
        got = fetch_one(url, state, request_fn, sleep_fn)
        log("GET %s %s" % (got["status"], url))
        if got["error"] and got["error"] != "budget":
            errors.append({"url": url, "error": got["error"], "status": got["status"]})
        return got

    robots = pull(ROBOTS_URL)
    sitemap_url = SITEMAP_URL
    if robots["status"] == 200:
        for line in robots["body"].decode("utf-8", "replace").splitlines():
            if line.lower().startswith("sitemap:"):
                sitemap_url = line.split(":", 1)[1].strip()
                break
    index = pull(sitemap_url)
    children = []
    if index["status"] == 200 and index["error"] != "budget":
        for loc in parse_locs(index["body"]):
            if is_english_sitemap(loc):
                children.append(loc)
    locs = []
    for child in children:
        if state["incomplete"]:
            break
        doc = pull(child)
        if doc["status"] == 200 and doc["error"] != "budget":
            locs.extend(parse_locs(doc["body"]))
    urls = select_cluster_urls(locs)
    pages = []
    for url in urls:
        if state["incomplete"]:
            errors.append({"url": url, "error": "not fetched: GET budget", "status": 0})
            continue
        got = pull(url)
        if got["error"] == "budget" or got["status"] != 200:
            errors.append({"url": url, "error": got["error"] or ("HTTP %s" % got["status"]), "status": got["status"]})
            pages.append({
                "url": url,
                "final_url": got.get("final_url") or url,
                "status": got["status"],
                "kind": kind_of(url),
                "noindex": False,
                "canonical": "",
                "og_title": "",
                "h1": "",
                "headings": [],
                "coverage_allowed": coverage_allowed(url),
                "indexable": False,
                "product_links": [],
                "flags": [],
            })
            continue
        page = extract_page(got["body"], url, status=200)
        page["final_url"] = got["final_url"]
        pages.append(page)
    return {
        "fetched_at": datetime.now().astimezone().isoformat(timespec="minutes"),
        "gets": state["gets"],
        "max_gets": max_gets,
        "incomplete": state["incomplete"],
        "product_url": PRODUCT_URL,
        "urls_selected": len(urls),
        "errors": errors,
        "pages": pages,
    }


def _md(text):
    return (text or "").replace("\n", " ").replace("|", "/").strip()


def additions_for(rows, pillar_id, limit=10):
    picked = [
        r for r in rows
        if r["pillar"] == pillar_id and r["action"] == "add_h2" and r["status"] in ("PARTIAL", "GAP")
    ]
    picked.sort(key=lambda r: (r["priority"], r["id"]))
    return picked[:limit], len(picked)


def render_report(seed, crawl, rows):
    counts = summarize(rows)
    pages = crawl.get("pages") or []
    indexable = [p for p in pages if p.get("indexable")]
    lines = []
    a = lines.append
    a("# AI Mode follow-up gap map — AgeAura NMN + TMG — 2026-10-20")
    a("")
    a("Read-only map of **hypothesised** follow-up questions onto public Wellness Nest headings. This run did not open Google AI Mode. None of these queries were observed there. There are no search volumes and no invented AI answers.")
    a("")
    a(seed.get("not_observed") or "")
    a("")
    a("Fan-out rule used here: a sub-question is an H2 or FAQ on a page that already exists. A new URL is the exception, and this cluster does not earn one. That follows the 2026-10-08 Google guidance recorded in `knowledge_base/AEO_GEO_GUIDELINES.md` (a separate page per fan-out query is scaled content abuse) and the Search Engine Land digest of 2026-10-10 (follow-up branches as a content map, with claim labels).")
    a("")
    a("Product rule: AgeAura copy in this map promotes only [%s](%s). Headings on any other AgeAura product URL do not count as coverage." % (
        ageaura_rules.PRODUCT_LABEL, PRODUCT_URL,
    ))
    a("")
    a("Label boundary: %s" % _md(seed.get("label_boundary")))
    a("")
    a("This document does not publish, update, or redirect any URL.")
    a("")
    a("## Crawl")
    a("")
    a("| | |")
    a("|---|---|")
    a("| Fetched | %s |" % _md(crawl.get("fetched_at")))
    a("| GETs | %s (cap %s) |" % (crawl.get("gets"), crawl.get("max_gets")))
    a("| URLs selected | %s |" % crawl.get("urls_selected"))
    a("| Pages stored | %s |" % len(pages))
    a("| Indexable and allowed | %s |" % len(indexable))
    a("| HTTP or fetch errors | %s |" % len(crawl.get("errors") or []))
    a("| Incomplete (budget) | %s |" % ("yes" if crawl.get("incomplete") else "no"))
    a("")
    if crawl.get("errors"):
        a("Fetch notes:")
        a("")
        for err in (crawl.get("errors") or [])[:20]:
            a("- `%s` — %s" % (err.get("status"), _md(err.get("url"))))
        a("")
    a("## Coverage counts")
    a("")
    a("| Status | Queries |")
    a("|---|---|")
    a("| COVERED | %d |" % counts["COVERED"])
    a("| PARTIAL | %d |" % counts["PARTIAL"])
    a("| GAP | %d |" % counts["GAP"])
    a("| H2/FAQ additions (partial + gap) | %d |" % counts["add_h2"])
    a("| GAP rejected as a thin new URL | %d |" % counts["reject_thin"])
    a("| GAP justified as a new article | %d |" % counts["new_article"])
    a("")
    a("PARTIAL means an existing indexable page is on the parent topic and should gain the specific H2 or FAQ. GAP means no indexable heading matched. A GAP can still be an addition on a named page. It is not permission to open a new URL.")
    a("")
    a("## Claims to verify")
    a("")
    a("These are flags on the crawled pages. They are not suggestions to repeat the wording. The H2 list below stays inside the label boundary unless a line says a human has to check a source first.")
    a("")
    by_kind = {}
    for page in pages:
        for flag in page.get("flags") or []:
            by_kind.setdefault(flag["kind"], []).append((page, flag))
    if not by_kind:
        a("No claim patterns fired on the extracted text.")
        a("")
    else:
        for kind in FLAG_NOTES:
            hits = by_kind.get(kind) or []
            if not hits:
                continue
            pages_hit = []
            seen_urls = set()
            for page, _flag in hits:
                if page["url"] not in seen_urls:
                    seen_urls.add(page["url"])
                    pages_hit.append(page["url"])
            a("### %s — %d page(s)" % (kind, len(pages_hit)))
            a("")
            a(FLAG_NOTES[kind])
            a("")
            shown = 0
            for page, flag in hits:
                if shown >= 8:
                    break
                a("- %s — “%s”" % (page["url"], _md(flag.get("excerpt"))))
                shown += 1
            if len(hits) > 8:
                a("- … %d more excerpt(s) in the crawl snapshot." % (len(hits) - 8))
            a("")
    landings = [p for p in pages if p.get("kind") == "landing"]
    denied_pages = [p for p in pages if not coverage_allowed(p.get("url") or "")]
    blocked = [p for p in pages if p.get("status") == 200 and ineligible_reason(p)]
    blank = [
        p for p in pages
        if p.get("status") == 200 and not (p.get("headings") or []) and not ineligible_reason(p)
    ]
    a("## Existing landings and pages that do not count")
    a("")
    a("These landing URLs are already on the public sitemap. Do not add another listicle for the same follow-ups. Unpublishing or redirecting any URL that still returns HTTP 200 needs a separate GO. This map does not change them.")
    a("")
    a("A blank H1 means the public HTML had no content heading. Client-rendered copy was not guessed, and the URL was not treated as proof that the topic is missing.")
    a("")
    if not landings:
        a("No landing URLs were in the crawl snapshot.")
        a("")
    for page in landings:
        why = ineligible_reason(page)
        state = "counted when a heading matches" if not why else "not counted (" + why + ")"
        a("- %s — HTTP %s — %s — H1: %s" % (
            page["url"], page.get("status"), state, _md(page.get("h1")) or "(none)",
        ))
    a("")
    if denied_pages:
        a("Denied product URLs. They are not pillars:")
        a("")
        for page in denied_pages:
            a("- %s — HTTP %s — H1: %s" % (page["url"], page.get("status"), _md(page.get("h1")) or "(none)"))
        a("")
    if blocked:
        a("HTTP 200 pages excluded from coverage, because they are noindex, a denied product, or they name Urolithin, peptides, or a duo:")
        a("")
        for page in blocked:
            a("- %s — %s" % (page["url"], ineligible_reason(page)))
        a("")
    if blank:
        a("HTTP 200 pages with no content heading in the HTML:")
        a("")
        for page in blank:
            a("- %s" % page["url"])
        a("")
    a("## Do not create these URLs")
    a("")
    rejected = [r for r in rows if r["status"] == "GAP" and r["action"] == "reject_thin"]
    if not rejected:
        a("None of the hypothesised follow-ups were rejected.")
        a("")
    for row in rejected:
        a("- **%s** — %s" % (_md(row["query"]), _md(row["reason"])))
    a("")
    a("## Justified new articles")
    a("")
    fresh = [r for r in rows if r["status"] == "GAP" and r["action"] == "new_article"]
    if not fresh:
        a("None. The public cluster already has pillars and spoke articles. New follow-ups in this seed belong on those URLs or are rejected as thin pages.")
        a("")
    for row in fresh:
        a("- **%s** — %s" % (_md(row["query"]), _md(row["reason"])))
    a("")
    recheck = [r for r in rows if r["status"] == "COVERED" and r["recheck"]]
    a("## Covered headings that still need a source check")
    a("")
    a("The question is already a heading. That is not permission to add numbers. Where the claim-flag section lists the same URL, keep the heading and check the sentences under it.")
    a("")
    if not recheck:
        a("None of the covered queries were marked for a source check.")
        a("")
    for row in recheck:
        a("- **%s** — %s %s: “%s”" % (
            _md(row["query"]), row["page_url"], row["heading_level"], _md(row["heading"]),
        ))
    a("")
    a("## Top H2 / FAQ additions by pillar")
    a("")
    a("Up to 10 per pillar, highest priority first. Each line is a hypothesised follow-up that is PARTIAL or an add-on GAP. The boundary is the only wording guidance. It is not a drafted answer.")
    a("")
    for pillar in seed.get("pillars") or []:
        pid = pillar["id"]
        owned = [r for r in rows if r["pillar"] == pid]
        c_cov = sum(1 for r in owned if r["status"] == "COVERED")
        c_part = sum(1 for r in owned if r["status"] == "PARTIAL")
        c_gap = sum(1 for r in owned if r["status"] == "GAP")
        add_rows, total = additions_for(rows, pid, 10)
        a("### %s" % pillar.get("name"))
        a("")
        a("Primary: %s" % pillar.get("url"))
        a("")
        a("Assigned follow-ups: %d covered, %d partial, %d gap." % (c_cov, c_part, c_gap))
        a("")
        if pillar.get("siblings"):
            a("Sibling URLs (do not open another page beside these):")
            a("")
            for sib in pillar["siblings"]:
                a("- %s" % sib)
            a("")
        if not add_rows:
            a("No H2 addition from this seed. The assigned follow-ups already have a heading, or they were rejected as thin URLs.")
            a("")
            continue
        if total > 10:
            a("Showing 10 of %d additions." % total)
            a("")
        for i, row in enumerate(add_rows, 1):
            a("%d. **%s** (%s, priority %d)" % (i, _md(row["suggested_heading"]), row["status"], row["priority"]))
            a("   - Follow-up: %s" % _md(row["query"]))
            a("   - Page: %s" % row["page_url"])
            if row["heading"]:
                a("   - Nearby heading: %s “%s”" % (row["heading_level"], _md(row["heading"])))
            a("   - Why: %s" % _md(row["reason"]))
            a("   - Boundary: %s" % _md(row["evidence_boundary"]))
            a("")
    a("## Appendix — every hypothesised follow-up")
    a("")
    for row in rows:
        a("- `%s` **%s** — %s" % (row["status"], _md(row["query"]), row["page_url"] or "(no page)"))
        if row["heading"]:
            a("  - %s: %s" % (row["heading_level"], _md(row["heading"])))
        if row["status"] != "COVERED" and row["suggested_heading"]:
            a("  - Suggested: %s" % _md(row["suggested_heading"]))
        a("  - %s" % _md(row["reason"]))
    a("")
    a("## How to rerun")
    a("")
    a("```bash")
    a("python3 scripts/ai_mode_gap_map.py --crawl \\")
    a("  --seed data/ai_mode_seeds/ageaura_nmn_tmg.json \\")
    a("  --crawl-out data/ai_mode_seeds/ageaura_nmn_tmg.crawl.json \\")
    a("  --report docs/AI_MODE_GAP_MAP_AGEAURA_2026-10-20.md")
    a("```")
    a("")
    a("Mapping only, from the saved crawl snapshot:")
    a("")
    a("```bash")
    a("python3 scripts/ai_mode_gap_map.py --from-crawl data/ai_mode_seeds/ageaura_nmn_tmg.crawl.json \\")
    a("  --report docs/AI_MODE_GAP_MAP_AGEAURA_2026-10-20.md")
    a("```")
    a("")
    return "\n".join(lines).rstrip() + "\n"


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def main(argv):
    parser = argparse.ArgumentParser(description="AgeAura AI Mode follow-up gap map (read-only).")
    parser.add_argument("--seed", default=os.path.join(ROOT, "data/ai_mode_seeds/ageaura_nmn_tmg.json"))
    parser.add_argument("--lint-seed", action="store_true")
    parser.add_argument("--crawl", action="store_true")
    parser.add_argument("--from-crawl", default="")
    parser.add_argument("--crawl-out", default="")
    parser.add_argument("--report", default="")
    parser.add_argument("--max-gets", type=int, default=MAX_GETS)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    args = parser.parse_args(argv)
    seed = load_json(args.seed)
    problems = lint_seed(seed)
    if problems:
        for item in problems:
            print("seed: " + item, file=sys.stderr)
        return 2
    if args.lint_seed and not args.crawl and not args.from_crawl:
        print("seed ok: %d queries" % len(seed["queries"]))
        return 0
    if args.crawl and args.from_crawl:
        print("use either --crawl or --from-crawl", file=sys.stderr)
        return 2
    if not args.crawl and not args.from_crawl:
        parser.print_help()
        return 2
    if args.crawl:
        if args.max_gets > MAX_GETS:
            print("--max-gets cannot exceed %d" % MAX_GETS, file=sys.stderr)
            return 2
        crawl_doc = crawl(
            seed,
            max_gets=args.max_gets,
            delay=args.delay,
            log=lambda msg: print(msg, file=sys.stderr),
        )
        if args.crawl_out:
            os.makedirs(os.path.dirname(args.crawl_out), exist_ok=True)
            with open(args.crawl_out, "w", encoding="utf-8") as handle:
                json.dump(crawl_doc, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
    else:
        crawl_doc = load_json(args.from_crawl)
    rows = map_queries(seed, crawl_doc.get("pages") or [])
    counts = summarize(rows)
    print(
        "gets=%s pages=%s covered=%s partial=%s gap=%s add_h2=%s reject_thin=%s new_article=%s"
        % (
            crawl_doc.get("gets"),
            len(crawl_doc.get("pages") or []),
            counts["COVERED"],
            counts["PARTIAL"],
            counts["GAP"],
            counts["add_h2"],
            counts["reject_thin"],
            counts["new_article"],
        )
    )
    if args.report:
        os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as handle:
            handle.write(render_report(seed, crawl_doc, rows))
        print("report " + args.report)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

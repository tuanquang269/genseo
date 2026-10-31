#!/usr/bin/env python3
"""Shared cluster map, topic rank, and in-body link helpers for Wellness Nest GEO.

Stdlib only. No Shopify calls. Product copy for new topics is limited to
ShilaSource Himalayan Shilajit Resin, AgeAura Pure NMN + TMG, and FloraFresh.
"""
from __future__ import annotations

import csv
import datetime as dt
import html
import json
import os
import re

import ageaura_rules
import florafresh_rules
import shilasource_resin_rules
import topic_fitness as tf

BLOG_ORIGIN = "https://wellnessnest.co"
BLOG_PATH = "/blogs/news/"
BLOG_ID = "104008483131"
ICT = dt.timezone(dt.timedelta(hours=7))

RESIN = "shilasource-himalayan-shilajit-resin"
AGEAURA = "ageaura-pure-nmn-tmg-nad-complex"
FLORA = "florafresh-vaginal-probiotics-gummies"
ALLOWED_PRODUCTS = {
    "shilajit": RESIN,
    "ageaura-nmn": AGEAURA,
    "florafresh": FLORA,
}

# First matching rule wins only as a fallback. assign_cluster uses the earliest
# match in the text, then the menopause exception below.
CLUSTERS = [
    {
        "id": "florafresh",
        "label": "FloraFresh and vaginal probiotics",
        "product": FLORA,
        "rx": re.compile(
            r"florafresh|vaginal|bacillus|coagulans|intimate|\bbv\b|yeast infection|"
            r"birth control|\bprobiotic",
            re.I,
        ),
    },
    {
        "id": "ageaura-nmn",
        "label": "AgeAura NMN, NAD+, and TMG",
        "product": AGEAURA,
        "rx": re.compile(r"\bnmn\b|\bnad\+?\b|\btmg\b|ageaura|nicotinamide|trimethylglycine", re.I),
    },
    {
        "id": "shilajit",
        "label": "ShilaSource and shilajit",
        "product": RESIN,
        "rx": re.compile(r"shilajit|shilasource|fulvic", re.I),
    },
    {
        "id": "creatine",
        "label": "Creatine and FusiForce",
        "product": None,
        "rx": re.compile(r"creatine|fusiforce", re.I),
    },
    {
        "id": "turkesterone",
        "label": "Turkesterone",
        "product": None,
        "rx": re.compile(r"turkesterone|ecdyster", re.I),
    },
    {
        "id": "menopause",
        "label": "Menopause archive",
        "product": None,
        "rx": re.compile(r"menomate|menopause|hot flash", re.I),
    },
    {
        "id": "healthy-aging",
        "label": "Healthy aging",
        "product": None,
        "rx": re.compile(r"healthy aging|longevity|cellular energy", re.I),
    },
]

HEAD_TERMS = {
    "florafresh": {"florafresh", "vaginal", "probiotic", "probiotics", "bacillus", "coagulans", "flora"},
    "ageaura-nmn": {"nmn", "nad", "tmg", "ageaura", "nicotinamide", "trimethylglycine"},
    "shilajit": {"shilajit", "shilasource", "fulvic", "ayurveda", "ayurvedic"},
    "creatine": {"creatine", "fusiforce"},
    "turkesterone": {"turkesterone", "ecdysterone", "ecdysteroid"},
    "menopause": {"menomate", "menopause"},
    "healthy-aging": {"aging", "longevity"},
    "other": set(),
}

INGREDIENT = {
    "shilajit": "shilajit resin",
    "ageaura-nmn": "nmn",
    "florafresh": "vaginal probiotics",
}

BRAND_WORDS = {"wellness", "nest", "wellnessnest", "wellnes", "welness", "wellnest"}
STOP = BRAND_WORDS | {
    "the", "a", "an", "of", "for", "to", "in", "on", "and", "or", "with", "from", "by",
    "your", "you", "can", "do", "does", "is", "are", "what", "when", "where", "how",
    "us", "usa", "www", "http", "https", "com", "co", "while", "everyday", "every",
    "day", "that", "this", "about", "into", "than", "then", "just", "not", "its",
    "it", "at", "as", "be", "if", "per", "take", "taking", "drink", "drinking",
    "using", "use", "make", "get", "daily",
}

MODIFIER_SEGMENT = {
    "for men": "for-men",
    "for women": "for-women",
    "for beginners": "beginners",
    "for seniors": "seniors",
    "for athletes": "athletes",
    "for runners": "athletes",
    "for fertility": "fertility",
    "over 40": "midlife",
    "over 50": "midlife",
    "over 60": "seniors",
    "side effects": "side-effects",
    "dosage": "dosage",
    "how to take": "how-to-take",
    "how much": "dosage",
    "how long": "how-long",
    "vs": "versus",
    "versus": "versus",
    "before bed": "timing",
    "morning or night": "timing",
    "empty stomach": "how-to-take",
    "with food": "timing",
    "where to buy": "buy",
    "where can i buy": "buy",
    "buy": "buy",
    "price": "price",
    "cost": "price",
    "how much does": "price",
}

SMALL_WORDS = {"a", "an", "the", "and", "or", "with", "for", "of", "to", "in", "on", "vs"}
CAPS = {"nmn": "NMN", "nad": "NAD", "tmg": "TMG", "us": "US", "cfu": "CFU", "nad+": "NAD+"}

FAQ_RX = re.compile(
    r"<h2\b[^>]*>\s*(?:Frequently Asked Questions|FAQs?)\b",
    re.I,
)
JSONLD_RX = re.compile(r"<script\b[^>]*type=[\"']application/ld\+json[\"']", re.I)
HANDLE_RX = re.compile(r"^[a-z0-9][a-z0-9-]{0,160}$")
MARKER = "data-genseo-cluster-link"
BANNED_TOPIC = re.compile(
    r"urolithin|peptides?|menomate|musclemax|sugar[-\s]?free|15\s*billion|\bxos\b|d-mannose",
    re.I,
)
SHILAJIT_OTHER_SKU = re.compile(r"gumm|shockwave|gold\s+resin", re.I)


def now_ict():
    return dt.datetime.now(ICT)


def cluster_by_id(cid):
    for c in CLUSTERS:
        if c["id"] == cid:
            return c
    return None


def assign_cluster(text):
    """Return a cluster id for a title, query, or abstract."""
    raw = text or ""
    low = raw.lower()
    meno = re.search(r"menomate|menopause|hot flash", low)
    vaginal = re.search(r"florafresh|vaginal|bacillus|coagulans", low)
    if meno and not vaginal:
        return "menopause"
    hits = []
    for c in CLUSTERS:
        if c["id"] == "menopause":
            continue
        m = c["rx"].search(raw)
        if m:
            hits.append((m.start(), CLUSTERS.index(c), c["id"]))
    if not hits:
        return "other"
    hits.sort()
    return hits[0][2]


def article_url(handle):
    return BLOG_ORIGIN + BLOG_PATH + handle


def safe_handle(handle):
    h = (handle or "").strip().lower()
    if not HANDLE_RX.fullmatch(h):
        return False
    if h.startswith("gsl-"):
        return False
    if "landing-listicle" in h or h.startswith("landing-"):
        return False
    return True


def is_dupe_handle(handle):
    h = (handle or "").lower()
    if "copy-of" in h or "news-copy" in h or h.endswith("-copy"):
        return True
    m = re.search(r"-(\d+)$", h)
    if not m:
        return False
    num = m.group(1)
    if num in {"2024", "2025", "2026", "2027", "2028"}:
        return False
    return len(num) <= 2


def handle_from_url(url):
    if not url or "/blogs/" not in url:
        return ""
    path = url.split("#", 1)[0].split("?", 1)[0].rstrip("/")
    handle = path.rsplit("/", 1)[-1].lower()
    return handle if safe_handle(handle) or HANDLE_RX.fullmatch(handle or "") else ""


def _int(value):
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def load_json_articles(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = data.get("articles") if isinstance(data, dict) else data
    out = []
    for row in rows or []:
        handle = (row.get("handle") or handle_from_url(row.get("url") or "")).lower()
        if not handle:
            continue
        out.append({
            "id": str(row.get("id") or ""),
            "handle": handle,
            "title": (row.get("title") or "").strip(),
            "url": row.get("url") or article_url(handle),
            "blog": str(row.get("blog") or row.get("blog_id") or BLOG_ID),
            "words": _int(row.get("words")),
            "created": row.get("created") or row.get("published_at") or "",
            "source": row.get("source") or "json",
        })
    return out


def load_csv_articles(path):
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            url = row.get("url") or row.get("Article Link") or row.get("link") or ""
            handle = (row.get("handle") or handle_from_url(url)).lower()
            if not handle:
                continue
            title = (row.get("title") or row.get("Title") or row.get("Keyword") or "").strip()
            blog = (row.get("blog") or "news").strip()
            out.append({
                "id": str(row.get("id") or ""),
                "handle": handle,
                "title": title,
                "url": url or article_url(handle),
                "blog": blog,
                "words": _int(row.get("words") or row.get("word_count")),
                "created": row.get("created") or row.get("Posted Date") or "",
                "sg_imp": _int(row.get("sg_imp")),
                "sg_clicks": _int(row.get("sg_clicks")),
                "sg_pos": _float(row.get("sg_pos")),
                "source": "csv",
            })
    return out


def load_tracker(path):
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            url = row.get("Article Link") or row.get("url") or ""
            handle = handle_from_url(url)
            if not handle:
                continue
            keyword = (row.get("Keyword") or "").strip()
            out.append({
                "id": "",
                "handle": handle,
                "title": keyword,
                "url": url,
                "blog": BLOG_ID,
                "words": 0,
                "created": row.get("Posted Date") or "",
                "source": "tracker",
            })
    return out


def merge_articles(json_rows=None, csv_rows=None, tracker_rows=None):
    """CSV and tracker are the live catalog when either exists.

    Handles that appear only in existing_articles.json stay in the map as
    stale_only and are not pillar or link targets. A CSV row keeps its title
    when the tracker only has a keyword.
    """
    by = {}
    csv_rows = list(csv_rows or [])
    tracker_rows = list(tracker_rows or [])
    live_mode = bool(csv_rows or tracker_rows)
    for row in csv_rows:
        if row.get("blog") not in ("news", BLOG_ID, "104008483131", ""):
            continue
        by[row["handle"]] = dict(row, stale_only=False)
    for row in tracker_rows:
        cur = by.get(row["handle"])
        if cur:
            if not cur.get("title") and row.get("title"):
                cur["title"] = row["title"]
            if row.get("created") and not cur.get("created"):
                cur["created"] = row["created"]
            continue
        item = dict(row, stale_only=False)
        if not item.get("title"):
            item["title"] = item["handle"].replace("-", " ")
        by[row["handle"]] = item
    for row in json_rows or []:
        cur = by.get(row["handle"])
        if cur:
            if row.get("id") and not cur.get("id"):
                cur["id"] = row["id"]
            if row.get("words") and not cur.get("words"):
                cur["words"] = row["words"]
            if len(row.get("title") or "") > len(cur.get("title") or "") and cur.get("source") == "tracker":
                cur["title"] = row["title"]
            continue
        if live_mode:
            by[row["handle"]] = dict(row, stale_only=True)
        else:
            by[row["handle"]] = dict(row, stale_only=False)
    for row in by.values():
        if not row.get("title"):
            row["title"] = row["handle"].replace("-", " ")
        if not row.get("url"):
            row["url"] = article_url(row["handle"])
    return list(by.values())


def read_gsc_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def current_period_rows(rows):
    """Keep the current window when the export has one.

    Vault gsc-daily files include period=current and period=prior. Summing both
    blends two weeks and moves queries in and out of the position 8 to 30 band.
    A file with no period column (fixtures, older exports) is used as-is.
    """
    rows = list(rows or [])
    periods = set()
    for row in rows:
        period = (row.get("period") or "").strip().lower()
        if period:
            periods.add(period)
    if "current" not in periods:
        return rows
    return [row for row in rows if (row.get("period") or "").strip().lower() == "current"]


def aggregate_gsc(rows):
    """Sum impressions across the vault export. Position is impression-weighted."""
    pages = {}
    queries = {}
    for row in current_period_rows(rows):
        query = (row.get("query") or row.get("key") or "").strip()
        page = row.get("page") or ""
        imp = _int(row.get("impressions"))
        clk = _int(row.get("clicks"))
        pos = _float(row.get("position"))
        if imp <= 0 and clk <= 0:
            continue
        handle = handle_from_url(page)
        if handle:
            bucket = pages.setdefault(handle, {"impressions": 0, "clicks": 0, "pos_num": 0.0})
            bucket["impressions"] += imp
            bucket["clicks"] += clk
            bucket["pos_num"] += pos * imp
        if not query:
            continue
        q = queries.setdefault(query, {
            "query": query, "impressions": 0, "clicks": 0, "pos_num": 0.0, "pages": {},
        })
        q["impressions"] += imp
        q["clicks"] += clk
        q["pos_num"] += pos * imp
        if handle:
            q["pages"][handle] = q["pages"].get(handle, 0) + imp
    for bucket in list(pages.values()) + list(queries.values()):
        imp = bucket["impressions"]
        bucket["position"] = round(bucket["pos_num"] / imp, 2) if imp else None
    return pages, queries


def _tokens(text):
    return re.findall(r"[a-z0-9+]+", (text or "").lower())


def longest_modifier(text):
    low = (text or "").lower()
    found = [m for m in tf.SEGMENT_MODIFIERS if m in low and m in MODIFIER_SEGMENT]
    if not found:
        return ""
    return max(found, key=len)


def gap_tokens(text, cluster_id):
    mods = [m for m in tf.SEGMENT_MODIFIERS if m in (text or "").lower()]
    mod_words = set()
    for m in mods:
        mod_words.update(m.split())
    head = HEAD_TERMS.get(cluster_id, set())
    out = []
    for tok in _tokens(text):
        if tok in mod_words or tok in head or tok in STOP or tok in BRAND_WORDS:
            continue
        if len(tok) <= 2:
            continue
        out.append(tok)
    return out


def build_primary(cluster_id, query):
    """Return (primary, segment) or None when no honest segment modifier fits."""
    if cluster_id not in ALLOWED_PRODUCTS:
        return None
    q = re.sub(r"\s+", " ", (query or "").lower()).strip()
    q = re.sub(r"\b(wellness\s*nest|wellnessnest|wellnes\s*nest|welness\s*nest)\b", " ", q)
    q = re.sub(r"[^a-z0-9+\s-]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    found = longest_modifier(q)
    if found:
        return q[:140].strip(), MODIFIER_SEGMENT[found]
    ingredient = INGREDIENT[cluster_id]
    rules = (
        (r"coffee", "how to take %s with coffee" % ingredient, "how-to-take"),
        (r"alcohol|hangover", "%s side effects with alcohol" % ingredient, "side-effects"),
        (r"empty stomach", "how to take %s on an empty stomach" % ingredient, "how-to-take"),
        (r"\bwomen\b|\bwoman\b|\bfemale\b", "%s for women" % ingredient, "for-women"),
        (r"\bmen\b", "%s for men" % ingredient, "for-men"),
        (r"senior|over 60|older adult", "%s for seniors" % ingredient, "seniors"),
        (r"beginner", "%s for beginners" % ingredient, "beginners"),
        (r"athlete|runner|workout|exercise|training", "%s for athletes" % ingredient, "athletes"),
        (r"fertil|sperm", "%s for fertility" % ingredient, "fertility"),
        (r"price|cost|how much", "%s price" % ingredient, "price"),
        (r"where to buy|\bbuy\b", "where to buy %s" % ingredient, "buy"),
        (r"how long", "how long does %s take" % ingredient, "how-long"),
        (r"side effect|safety", "%s side effects" % ingredient, "side-effects"),
        (r"dosage|dose|how many|\bcfu\b", "%s dosage" % ingredient, "dosage"),
        (r"\bvs\b|versus", "%s vs capsules" % ingredient, "versus"),
        (r"morning|night|before bed", "%s morning or night" % ingredient, "timing"),
    )
    for rx, primary, segment in rules:
        if re.search(rx, q):
            if segment == "for-men" and re.search(r"women|woman|female", q):
                continue
            return primary, segment
    return None


def _blob(article):
    return ((article.get("title") or "") + " " + (article.get("handle") or "")).lower()


def is_covered(query, primary, articles, cluster_id):
    blobs = [_blob(a) for a in articles if not a.get("stale_only")]
    extras = gap_tokens(query or primary, cluster_id)
    if extras:
        return any(all(tok in blob for tok in extras) for blob in blobs)
    phrase = longest_modifier(primary or query)
    if not phrase:
        return bool(blobs)
    return any(phrase in blob for blob in blobs)


UNSAFE_QUERY = re.compile(
    r"pregnan|pcos|cancer|tumou?r|\bdisease\b|diagnos|\bcure\b|\btreat(?:ment|ing)?\b|"
    r"vaginosis|yeast infection|anti-inflammatory|testosterone",
    re.I,
)


def query_blocked(cluster_id, query):
    """True when a query must not become a new ticket."""
    q = query or ""
    if BANNED_TOPIC.search(q) or UNSAFE_QUERY.search(q):
        return True
    if cluster_id == "shilajit" and SHILAJIT_OTHER_SKU.search(q):
        return True
    if cluster_id == "ageaura-nmn" and re.search(r"urolithin|peptide", q, re.I):
        return True
    if cluster_id != "florafresh" and re.search(r"\bgummies\b", q, re.I):
        return True
    return False


def pure_brand_query(query):
    tokens = [t for t in _tokens(query) if t not in STOP and t not in {"shilajit", "nmn", "nad", "tmg"}]
    words = _tokens(query)
    if not words:
        return True
    useful = [w for w in words if w not in BRAND_WORDS and w not in STOP]
    return not useful


def guide_bonus(title):
    t = (title or "").lower()
    if re.search(r"\b(what is|introduction|ultimate guide|complete guide|overview)\b", t):
        return 40
    if re.search(r"\bguide\b", t):
        return 25
    return 0


def pillar_score(article):
    if article.get("stale_only") or is_dupe_handle(article.get("handle")):
        return -1000
    if not safe_handle(article.get("handle")) or not ageaura_rules.article_link_allowed(article.get("handle")):
        return -1000
    imp = article.get("impressions") or 0
    clk = article.get("clicks") or 0
    words = article.get("words") or 0
    pos = article.get("position")
    pos_bonus = max(0, 35 - pos) if pos and imp else 0
    return imp * 2 + clk * 20 + min(words, 3500) / 30.0 + guide_bonus(article.get("title")) + pos_bonus


def _top_queries(handle, queries, limit=5):
    rows = []
    for q in queries.values():
        imp = q["pages"].get(handle, 0)
        if imp <= 0 or pure_brand_query(q["query"]):
            continue
        rows.append({
            "query": q["query"],
            "impressions": imp,
            "position": q.get("position"),
        })
    rows.sort(key=lambda r: (-r["impressions"], r["query"]))
    return rows[:limit]


def build_map(articles, gsc_rows=None, intake_items=None, meta=None):
    pages, queries = aggregate_gsc(gsc_rows or [])
    grouped = {c["id"]: [] for c in CLUSTERS}
    grouped["other"] = []
    for article in articles:
        if article.get("blog") not in ("news", BLOG_ID, "104008483131", "", None):
            continue
        handle = article["handle"]
        stats = pages.get(handle) or {}
        if not stats and article.get("sg_imp"):
            stats = {
                "impressions": article.get("sg_imp") or 0,
                "clicks": article.get("sg_clicks") or 0,
                "position": article.get("sg_pos") or None,
            }
        item = dict(article)
        item["impressions"] = stats.get("impressions") or 0
        item["clicks"] = stats.get("clicks") or 0
        item["position"] = stats.get("position")
        item["queries"] = _top_queries(handle, queries)
        cid = assign_cluster(((item.get("title") or "") + " " + handle.replace("-", " ")).strip())
        item["cluster"] = cid
        grouped.setdefault(cid, []).append(item)

    clusters = []
    for spec in CLUSTERS + [{"id": "other", "label": "Unclustered", "product": None}]:
        members = grouped.get(spec["id"]) or []
        members.sort(key=lambda a: (-pillar_score(a), -len(a.get("title") or ""), a["handle"]))
        live = [a for a in members if not a.get("stale_only")]
        pillar = None
        for candidate in live:
            if pillar_score(candidate) <= -1000:
                continue
            if other_sku_handle(spec["id"], candidate.get("handle")):
                continue
            pillar = candidate
            break
        spokes = []
        for a in members:
            if pillar and a["handle"] == pillar["handle"]:
                continue
            spokes.append(_public_article(a))
        gaps = _gaps(spec["id"], live, queries, intake_items or [], len(live))
        clusters.append({
            "id": spec["id"],
            "label": spec.get("label") or spec["id"],
            "product": spec.get("product"),
            "allowed_new": spec["id"] in ALLOWED_PRODUCTS,
            "pillar": _public_article(pillar) if pillar else None,
            "spokes": spokes,
            "spoke_count": len(spokes),
            "article_count": len(live),
            "stale_count": sum(1 for a in members if a.get("stale_only")),
            "gaps": gaps,
        })
    payload = {
        "built": (meta or {}).get("built") or now_ict().date().isoformat(),
        "article_count": sum(c["article_count"] for c in clusters),
        "cluster_count": sum(1 for c in clusters if c["article_count"]),
        "pillar_count": sum(1 for c in clusters if c["pillar"]),
        "sources": (meta or {}).get("sources") or {},
        "clusters": clusters,
    }
    return payload


def _public_article(article):
    if not article:
        return None
    return {
        "id": article.get("id") or "",
        "handle": article["handle"],
        "title": article.get("title") or "",
        "url": article.get("url") or article_url(article["handle"]),
        "words": article.get("words") or 0,
        "impressions": article.get("impressions") or 0,
        "clicks": article.get("clicks") or 0,
        "position": article.get("position"),
        "stale_only": bool(article.get("stale_only")),
        "dupe": is_dupe_handle(article.get("handle")),
        "queries": article.get("queries") or [],
        "score": round(pillar_score(article), 2),
    }


def _gaps(cluster_id, articles, queries, intake_items, spoke_count):
    gaps = []
    seen = set()
    for q in queries.values():
        query = q["query"]
        pos = q.get("position")
        if pos is None or pos < 8 or pos > 30:
            continue
        if q["impressions"] < 3 or pure_brand_query(query):
            continue
        if assign_cluster(query) != cluster_id:
            continue
        if query_blocked(cluster_id, query):
            continue
        built = build_primary(cluster_id, query)
        if not built:
            continue
        primary, segment = built
        if is_covered(query, primary, articles, cluster_id):
            continue
        key = primary
        if key in seen:
            continue
        seen.add(key)
        gaps.append({
            "query": query,
            "primary": primary,
            "segment": segment,
            "impressions": q["impressions"],
            "position": pos,
            "source": "gsc",
            "fresh": False,
            "spoke_count": spoke_count,
        })
    for item in intake_items:
        if item.get("cluster") != cluster_id:
            continue
        title = item.get("title") or ""
        if query_blocked(cluster_id, title):
            continue
        built = build_primary(cluster_id, title)
        if not built:
            continue
        primary, segment = built
        if primary in seen or is_covered(title, primary, articles, cluster_id):
            continue
        seen.add(primary)
        gaps.append({
            "query": title,
            "primary": primary,
            "segment": segment,
            "impressions": 0,
            "position": None,
            "source": "intake",
            "fresh": True,
            "spoke_count": spoke_count,
            "url": item.get("url") or "",
        })
    gaps.sort(key=lambda g: (-rank_gap(g), g["primary"]))
    return gaps[:12]


def rank_gap(gap):
    pos = gap.get("position")
    impr = gap.get("impressions") or 0
    band = pos is not None and 8 <= pos <= 30
    score = impr if band else 0
    if gap.get("fresh") or gap.get("source") == "intake":
        score += 40
    if (gap.get("spoke_count") or 0) < 5:
        score += 15
    return score


def fit_title(core):
    suffix = " (US 2026)"
    core = re.sub(r"\s+", " ", core).strip()
    if len(core) + len(suffix) <= 60:
        return core + suffix
    room = 60 - len(suffix)
    cut = core[:room].rsplit(" ", 1)[0].rstrip(" :-")
    if len(cut) < 12:
        cut = core[:room].rstrip(" :-")
    return cut + suffix


def title_from_primary(primary):
    words = (primary or "").split()
    out = []
    for i, word in enumerate(words):
        if word in CAPS:
            out.append(CAPS[word])
        elif i and word in SMALL_WORDS:
            out.append(word)
        else:
            out.append(word[:1].upper() + word[1:])
    return fit_title(" ".join(out))


def guard_topic_text(text, product):
    """Empty list means the brief may be offered to refill."""
    reasons = []
    if product not in ALLOWED_PRODUCTS.values():
        reasons.append("product is not ShilaSource resin, AgeAura NMN + TMG, or FloraFresh")
    try:
        ageaura_rules.require_target(product)
    except ageaura_rules.AgeAuraProductError as exc:
        reasons.extend(exc.reasons)
    if BANNED_TOPIC.search(text or ""):
        reasons.append("brief contains a banned product or formula phrase")
    reasons.extend(florafresh_rules.violations(text or ""))
    reasons.extend(shilasource_resin_rules.violations(text or ""))
    reasons.extend(ageaura_rules.text_target_violations(text or ""))
    if product == AGEAURA and "products/" in (text or "") and AGEAURA not in (text or ""):
        reasons.append("AgeAura copy must use the NMN + TMG product URL")
    return reasons


def topics_from_map(cluster_map, bank=None, limit=8):
    topics = []
    segments = segment_names(bank)
    products = (bank or {}).get("products") or {h: {} for h in ALLOWED_PRODUCTS.values()}
    for cluster in cluster_map.get("clusters") or []:
        if cluster.get("id") not in ALLOWED_PRODUCTS:
            continue
        product = cluster.get("product") or ALLOWED_PRODUCTS[cluster["id"]]
        if product not in products:
            continue
        pillar = (cluster.get("pillar") or {}).get("handle") or ""
        links = [pillar] if pillar else []
        for spoke in cluster.get("spokes") or []:
            if spoke.get("stale_only") or spoke.get("dupe"):
                continue
            if spoke.get("handle") and spoke["handle"] not in links:
                links.append(spoke["handle"])
            if len(links) >= 4:
                break
        for gap in cluster.get("gaps") or []:
            if query_blocked(cluster["id"], gap.get("query") or ""):
                continue
            primary = (gap.get("primary") or "").strip()
            segment = gap.get("segment") or ""
            if not primary or segment not in segments:
                continue
            if not longest_modifier(primary):
                continue
            title = title_from_primary(primary)
            if len(title) > 60:
                continue
            template = "COMPARISON" if segment == "versus" else (
                "LISTICLE" if segment in ("how-to-take", "dosage", "buy") else "EDITORIAL"
            )
            evidence = _evidence(cluster["id"], product)
            angle = _angle(cluster["id"], product)
            intent = "A reader searching this cluster gap who needs the next specific answer."
            secondary = [cluster["label"], segment.replace("-", " ")]
            fanout = _fanout(cluster, product)
            brief = " ".join([primary, title, angle, evidence] + secondary + fanout)
            if guard_topic_text(brief, product):
                continue
            topics.append({
                "id": "cluster-" + re.sub(r"[^a-z0-9]+", "-", primary).strip("-")[:48],
                "product": product,
                "primary": primary,
                "title": title,
                "secondary": secondary,
                "segment": segment,
                "intent": intent,
                "template": template,
                "angle": angle,
                "fanout": fanout,
                "evidence": evidence,
                "link": links[:4],
                "rank": rank_gap(gap),
                "cluster": cluster["id"],
            })
    topics.sort(key=lambda t: (-t["rank"], t["id"]))
    kept = []
    seen = set()
    for topic in topics:
        if topic["primary"] in seen or topic["id"] in seen:
            continue
        seen.add(topic["primary"])
        seen.add(topic["id"])
        kept.append(topic)
        if len(kept) >= limit:
            break
    return kept


def segment_names(bank):
    """Segment ids a topic may use. The topic bank stores them as dict keys."""
    raw = (bank or {}).get("segments")
    if isinstance(raw, dict):
        return set(raw)
    if isinstance(raw, (list, tuple, set)):
        return set(raw)
    return set(MODIFIER_SEGMENT.values())


def _evidence(cluster_id, product):
    if product == FLORA:
        return (
            "FloraFresh formula stays on the Supplement Facts label: "
            + florafresh_rules.STRAIN + ", " + florafresh_rules.CFU
            + " per 2 gummies. Do not copy the live PDP description. "
            "Open a PubMed or NIH page from wellness intake before citing a study."
        )
    if product == RESIN:
        return (
            "Hero product is ShilaSource Himalayan Shilajit Resin. "
            "Repeat only lines on the pack-label whitelist. Do not invent a dose. "
            "Open a PubMed or NIH page from wellness intake before citing a study."
        )
    if product == AGEAURA:
        return (
            "AgeAura means AgeAura Pure NMN + TMG only. Link only "
            "https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex. "
            "Open a PubMed or NIH page from wellness intake before citing a study."
        )
    return "Open a primary source before citing a study."


def _angle(cluster_id, product):
    if product == FLORA:
        return "One FloraFresh spoke for a query the cluster does not answer yet."
    if product == RESIN:
        return "One ShilaSource resin spoke for a query the shilajit cluster does not answer yet."
    if product == AGEAURA:
        return "One AgeAura NMN + TMG spoke for a query the NAD cluster does not answer yet."
    return "One spoke for an open cluster query."


def _fanout(cluster, product):
    out = []
    pillar = cluster.get("pillar") or {}
    if pillar.get("title"):
        out.append(to_question(pillar["title"]))
    for spoke in cluster.get("spokes") or []:
        if spoke.get("stale_only") or spoke.get("dupe"):
            continue
        out.append(to_question(spoke.get("title") or spoke.get("handle") or ""))
        if len(out) >= 4:
            break
    if len(out) < 3:
        out.append("What should a US buyer check on the label before using it?")
    clean = []
    for line in out:
        if guard_topic_text(line, product):
            continue
        clean.append(line)
    if len(clean) < 3:
        clean.append("What should a US buyer check on the label before using it?")
    return clean[:4]


def to_question(text):
    t = re.sub(r"\s*\((?:US\s*)?20\d\d\)\s*", "", text or "").strip()
    t = re.sub(r"\s+", " ", t)
    if not t:
        return "What should you read next in this cluster?"
    if t.endswith("?"):
        return t
    if re.match(r"^(how|what|when|where|why|can|does|do|is|are|should)\b", t, re.I):
        return t + "?"
    if len(t) > 80:
        t = t[:77].rsplit(" ", 1)[0]
    return "What should you know about " + t + "?"


def render_markdown(cluster_map):
    lines = [
        "# Wellness Nest topic clusters",
        "",
        "Built %s. Articles %s. Clusters with articles %s. Pillars %s." % (
            cluster_map.get("built") or "",
            cluster_map.get("article_count") or 0,
            cluster_map.get("cluster_count") or 0,
            cluster_map.get("pillar_count") or 0,
        ),
        "",
        "A pillar is the strongest live article in the cluster (Search Console weight plus length and a guide-style title). Spokes are the other articles. Gaps are Search Console queries in positions 8 to 30, or fresh intake titles, that no spoke answers yet. When the export has a current period, only that window is counted. New topic picks are limited to ShilaSource resin, AgeAura Pure NMN + TMG, and FloraFresh.",
        "",
    ]
    sources = cluster_map.get("sources") or {}
    if sources:
        lines.append("Sources: " + ", ".join("%s=%s" % (k, v) for k, v in sources.items()) + ".")
        lines.append("")
    for cluster in cluster_map.get("clusters") or []:
        if not cluster.get("article_count") and not cluster.get("gaps"):
            continue
        lines.append("## %s" % cluster["label"])
        lines.append("")
        lines.append("Id: `%s`. Live articles: %s. Stale handles kept out of links: %s." % (
            cluster["id"], cluster.get("article_count") or 0, cluster.get("stale_count") or 0,
        ))
        pillar = cluster.get("pillar")
        if pillar:
            lines.append("")
            lines.append("Pillar: [%s](%s) (%s words, %s impressions, position %s)." % (
                pillar.get("title") or pillar["handle"],
                pillar.get("url") or article_url(pillar["handle"]),
                pillar.get("words") or 0,
                pillar.get("impressions") or 0,
                pillar.get("position") if pillar.get("position") is not None else "n/a",
            ))
        else:
            lines.append("")
            lines.append("Pillar: none yet.")
        lines.append("")
        lines.append("Spokes:")
        if not cluster.get("spokes"):
            lines.append("- none")
        for spoke in cluster.get("spokes") or []:
            flag = " stale" if spoke.get("stale_only") else ""
            lines.append("- [%s](%s)%s" % (
                spoke.get("title") or spoke["handle"],
                spoke.get("url") or article_url(spoke["handle"]),
                flag,
            ))
        lines.append("")
        lines.append("Gaps:")
        if not cluster.get("gaps"):
            lines.append("- none")
        for gap in cluster.get("gaps") or []:
            lines.append("- `%s` | primary `%s` | impr %s | pos %s | %s" % (
                gap.get("query"), gap.get("primary"), gap.get("impressions"),
                gap.get("position") if gap.get("position") is not None else "n/a",
                gap.get("source"),
            ))
        lines.append("")
    lines.append("New articles should link to the pillar and to two or more spokes in the body, then add a What to ask next list. That list is not an FAQ and must not add a second FAQPage block.")
    lines.append("")
    text = "\n".join(lines)
    return text.replace("\u2014", " - ").replace("\u2013", " - ")


def link_targets(cluster, handle, sibling_limit=4):
    """Pillar plus up to sibling_limit spokes, skipping self, dupes, and denied slugs."""
    if not cluster:
        return []
    targets = []
    pillar = (cluster.get("pillar") or {}).get("handle")
    if pillar and pillar != handle and _linkable(pillar):
        targets.append(("pillar", pillar))
    siblings = []
    for spoke in cluster.get("spokes") or []:
        h = spoke.get("handle")
        if not h or h == handle or h == pillar:
            continue
        if spoke.get("stale_only") or spoke.get("dupe") or not _linkable(h):
            continue
        if other_sku_handle(cluster.get("id"), h):
            continue
        siblings.append(spoke)
    siblings.sort(key=lambda s: (-(s.get("impressions") or 0), -(s.get("words") or 0), s["handle"]))
    for spoke in siblings[:sibling_limit]:
        targets.append(("sibling", spoke["handle"]))
    return targets


def other_sku_handle(cluster_id, handle):
    """Gummies, Shockwave, and Gold Resin stay out of new ShilaSource resin links."""
    if cluster_id != "shilajit":
        return False
    return bool(SHILAJIT_OTHER_SKU.search((handle or "").replace("-", " ")))


def _linkable(handle):
    return safe_handle(handle) and ageaura_rules.article_link_allowed(handle)


def _member_index(cluster):
    idx = {}
    pillar = cluster.get("pillar")
    if pillar and pillar.get("handle"):
        idx[pillar["handle"]] = pillar
    for spoke in cluster.get("spokes") or []:
        if spoke.get("handle"):
            idx[spoke["handle"]] = spoke
    return idx


SIBLING_SENTENCES = (
    "A related page in this cluster is %s.",
    "Readers who want the next specific answer can read %s.",
    "Another page that stays on this topic is %s.",
    "For a different question in the same cluster, read %s.",
)
PILLAR_SENTENCE = (
    "The pillar page for this topic is %s, which is the broader guide the rest of the cluster points back to."
)


def title_blocked(text):
    """True when an anchor would repeat a banned product or a wrong formula."""
    text = text or ""
    if BANNED_TOPIC.search(text):
        return True
    if florafresh_rules.violations(text):
        return True
    if shilasource_resin_rules.violations(text):
        return True
    if ageaura_rules.text_target_violations(text):
        return True
    return False


def anchor_text(title):
    clean = re.sub(r"\s+", " ", title or "").strip()
    if not clean or title_blocked(clean):
        return "the related article in this cluster"
    if len(clean) > 110:
        clean = clean[:107].rsplit(" ", 1)[0].strip()
    return clean or "the related article in this cluster"


def _sentence(kind, link_html, sibling_index):
    if kind == "pillar":
        return PILLAR_SENTENCE % link_html
    return SIBLING_SENTENCES[sibling_index % len(SIBLING_SENTENCES)] % link_html


def contextual_paragraphs(article_handle, cluster):
    idx = _member_index(cluster)
    paragraphs = []
    sibling_index = 0
    for kind, handle in link_targets(cluster, article_handle or ""):
        member = idx.get(handle) or {"handle": handle, "title": handle.replace("-", " ")}
        url = member.get("url") or article_url(handle)
        title = member.get("title") or handle.replace("-", " ")
        visible = html.escape(anchor_text(title))
        html_anchor = '<a href="%s" %s="body-%s">%s</a>' % (
            html.escape(url, quote=True), MARKER, html.escape(handle, quote=True), visible,
        )
        sentence = _sentence(kind, html_anchor, sibling_index)
        if kind != "pillar":
            sibling_index += 1
        paragraphs.append(
            '<p %s="body-%s">%s</p>' % (MARKER, html.escape(handle, quote=True), sentence)
        )
    return paragraphs


def contextual_markdown(article_handle, cluster):
    """In-body sentences for a new draft. The article handle may be empty when it is not in the map yet."""
    if not cluster:
        return ""
    idx = _member_index(cluster)
    lines = []
    sibling_index = 0
    for kind, handle in link_targets(cluster, article_handle or ""):
        member = idx.get(handle) or {"handle": handle, "title": handle.replace("-", " ")}
        url = member.get("url") or article_url(handle)
        title = member.get("title") or handle.replace("-", " ")
        link = "[%s](%s)" % (anchor_text(title).replace("]", ""), url)
        lines.append(_sentence(kind, link, sibling_index))
        lines.append("")
        if kind != "pillar":
            sibling_index += 1
    return "\n".join(lines)


def related_questions(article_handle, cluster, limit=5):
    """3 to 5 follow-ups when the cluster has enough other pages. Fewer when it does not."""
    if not cluster:
        return []
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 5
    limit = max(1, min(5, limit))
    idx = _member_index(cluster)
    questions = []
    for _kind, handle in link_targets(cluster, article_handle or ""):
        member = idx.get(handle) or {}
        query = ""
        for row in member.get("queries") or []:
            if row.get("query") and not pure_brand_query(row["query"]) and not title_blocked(row["query"]):
                query = row["query"]
                break
        text = to_question(query or member.get("title") or handle.replace("-", " "))
        if title_blocked(text):
            text = to_question(member.get("title") or "")
        if title_blocked(text):
            text = "What does the next page in this cluster cover?"
        questions.append({
            "handle": handle,
            "url": member.get("url") or article_url(handle),
            "question": text,
        })
        if len(questions) >= limit:
            break
    return questions[:5]


def related_questions_html(questions):
    if not questions:
        return ""
    items = []
    for q in questions[:5]:
        items.append(
            '<li><a href="%s" %s="next-%s">%s</a></li>' % (
                html.escape(q["url"], quote=True),
                MARKER,
                html.escape(q["handle"], quote=True),
                html.escape(q["question"]),
            )
        )
    return (
        '<section class="genseo-related-questions" %s="related-questions">'
        "<h2>What to ask next</h2>"
        "<p>These questions link to other articles in the same cluster. They are follow-ups, not a second FAQ.</p>"
        "<ul>%s</ul></section>" % (MARKER, "".join(items))
    )


def related_questions_markdown(questions):
    if not questions:
        return ""
    lines = [
        "## What to ask next",
        "",
        "These questions link to other articles in the same cluster. Place this section before the FAQ heading. Do not add schema for this section.",
        "",
    ]
    for q in questions[:5]:
        lines.append("- [%s](%s)" % (q["question"].replace("]", ""), q["url"]))
    lines.append("")
    return "\n".join(lines)


def _href_present(body, url):
    return url in (body or "")


def _marker_present(body, token):
    return ('%s="%s"' % (MARKER, token)) in (body or "")


def plan_article_html(body, article_handle, cluster):
    """Return (new_body, added) where added is a list of {kind, handle, url}."""
    body = body or ""
    added = []
    paragraphs = []
    if cluster:
        for para, (kind, handle) in zip(
            contextual_paragraphs(article_handle, cluster),
            link_targets(cluster, article_handle),
        ):
            url = article_url(handle)
            if _marker_present(body, "body-" + handle) or _href_present(body, url):
                continue
            paragraphs.append(para)
            added.append({"kind": kind, "handle": handle, "url": url})
    section = ""
    questions = related_questions(article_handle, cluster) if cluster else []
    if questions and not _marker_present(body, "related-questions"):
        # Drop questions whose marker is already present. Keep the href even if
        # a contextual paragraph in this same edit points at the same article.
        fresh = []
        for q in questions:
            if _marker_present(body, "next-" + q["handle"]):
                continue
            fresh.append(q)
            added.append({"kind": "question", "handle": q["handle"], "url": q["url"]})
        section = related_questions_html(fresh)
        if not fresh:
            section = ""
            added = [a for a in added if a["kind"] != "question"]
    if not paragraphs and not section:
        return body, []
    chunk = "\n".join(paragraphs)
    if section:
        if chunk:
            chunk += "\n"
        chunk += section
    match = FAQ_RX.search(body)
    if match:
        new_body = body[:match.start()] + chunk + "\n" + body[match.start():]
    else:
        match = JSONLD_RX.search(body)
        if match:
            new_body = body[:match.start()] + chunk + "\n" + body[match.start():]
        else:
            new_body = body.rstrip() + "\n" + chunk + "\n"
    return new_body, added


def cluster_index(cluster_map):
    return {c["id"]: c for c in cluster_map.get("clusters") or []}


def article_cluster(cluster_map, handle):
    for cluster in cluster_map.get("clusters") or []:
        pillar = (cluster.get("pillar") or {}).get("handle")
        if pillar == handle:
            return cluster
        for spoke in cluster.get("spokes") or []:
            if spoke.get("handle") == handle:
                return cluster
    return None


def assert_blog_article_endpoint(url):
    """Refuse any Admin URL that is not one blog article or the article index."""
    path = url.split("?", 1)[0]
    if any(bit in path for bit in ("/products", "/pages", "/collections", "/themes", "/redirects")):
        raise RuntimeError("refusing non-article Shopify path")
    if not re.search(r"/blogs/%s/articles(\.json|/\d+\.json)?$" % re.escape(str(BLOG_ID)), path):
        raise RuntimeError("refusing URL outside blog %s articles" % BLOG_ID)
    return url

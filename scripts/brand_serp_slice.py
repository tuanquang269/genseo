#!/usr/bin/env python3
"""Slice a GSC daily CSV into house-brand vs other queries.

Reads the vault export (period, date, query, page, country, device, clicks,
impressions, ctr, position). Compares period=current with period=prior inside
each file. Does not call Shopify, Search Console, or a SERP API.

The CSV reader is wn_clusters.read_gsc_csv. Store-name spellings come from
wn_clusters.BRAND_WORDS, matched as phrases: a lone "wellness" or "nest" is
not the store. House product lines are the hero SKUs in AGENTS.md. Bare
"turkesterone" stays in the other group because it is the ingredient, not the
SKU (scripts/turkesterone_rules.py).

wn_clusters.pure_brand_query answers a different question (a query with no
topic left after brand words are removed). "wellness nest shilajit" is a house
brand query here and is not a pure brand query there.

Position is sum(position * impressions) / sum(impressions). Device and date
rows are folded. The ctr column is ignored.

Usage:
    python3 scripts/brand_serp_slice.py \
        --csv ~/genseo-wt/inputs/2026-10-21-gsc-raw.csv \
        --csv ~/PATI/LLM-Wiki/90-sources/gsc-daily/2026-10-20-gsc-raw.csv \
        --report docs/BRAND_SERP_DEFENCE_2026-10-21.md \
        --json docs/brand-serp-2026-10-21.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from collections import defaultdict
from urllib.parse import quote_plus, urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wn_clusters as wc

RESERVED = {
    "blogs", "products", "collections", "pages", "policies", "tools",
    "cart", "account", "search", "apps", "checkouts", "admin", "cdn",
}
PAID_KINDS = {"home", "product", "collection", "page", "cart", "checkout"}
PERIODS = ("current", "prior")
REVIEW_CANON = "/blogs/news/wellness-nest-shilajit-reviews-what-85-buyers-report"
NAMED_PATHS = (
    "/",
    "/de",
    "/fr",
    "/pages/100-shilajit",
    "/de/pages/100-shilajit",
    "/fr/pages/100-shilajit",
    "/it/pages/100-shilajit",
    "/products/premium-himalayan-shilajit-gummies",
    "/products/fusiforce-creatine-gummies",
    "/collections/shilajit-wellness-stack",
    REVIEW_CANON,
    "/hr" + REVIEW_CANON,
    "/cs" + REVIEW_CANON,
)
DEFAULT_FOCUS = (
    ("wellness nest shilajit", "slide"),
    ("wellness nest", "slide"),
    ("wellnessnest", "slide"),
    ("creatine fusiforce", "slide"),
    ("wellnessnest.co", "control"),
)

# Hero lines from AGENTS.md / the vault product table. "gold resin" counts
# only together with "shilajit", so "mars gold resin" stays out.
_LINE_TOKEN = re.compile(
    r"\b(?:fusiforce|shilasource|florafresh|ageaura|menomate|shockwave)\b",
    re.I,
)
_GOLD = re.compile(r"gold\s+resin", re.I)
_SHILAJIT = re.compile(r"shilajit", re.I)

GL = {
    "usa": "us", "gbr": "uk", "can": "ca", "aus": "au", "nzl": "nz",
    "deu": "de", "fra": "fr", "ita": "it", "esp": "es", "nld": "nl",
    "bel": "be", "aut": "at", "che": "ch", "pol": "pl", "cze": "cz",
    "hun": "hu", "dnk": "dk", "swe": "se", "nor": "no", "fin": "fi",
    "prt": "pt", "grc": "gr", "rou": "ro", "irl": "ie", "hrv": "hr",
    "svk": "sk", "grc": "gr",
    "vnm": "vn", "jpn": "jp", "kor": "kr", "ind": "in",
    "sgp": "sg", "mys": "my", "phl": "ph", "idn": "id", "tha": "th",
    "bra": "br", "mex": "mx", "are": "ae", "sau": "sa", "pak": "pk",
    "lbn": "lb", "zaf": "za", "tur": "tr", "ukr": "ua", "grc": "gr",
}
HL = {
    "deu": "de", "aut": "de", "che": "de", "fra": "fr", "ita": "it",
    "esp": "es", "nld": "nl", "pol": "pl", "cze": "cs", "hun": "hu",
    "prt": "pt", "grc": "el", "rou": "ro", "dnk": "da", "swe": "sv",
    "jpn": "ja", "kor": "ko", "vnm": "vi",
}
COUNTRY_NAME = {
    "usa": "United States", "gbr": "United Kingdom", "can": "Canada",
    "aus": "Australia", "nzl": "New Zealand", "deu": "Germany",
    "fra": "France", "ita": "Italy", "esp": "Spain", "nld": "Netherlands",
    "bel": "Belgium", "aut": "Austria", "che": "Switzerland", "pol": "Poland",
    "cze": "Czechia", "hun": "Hungary", "dnk": "Denmark", "swe": "Sweden",
    "nor": "Norway", "fin": "Finland", "prt": "Portugal", "grc": "Greece",
    "rou": "Romania", "irl": "Ireland", "hrv": "Croatia", "svk": "Slovakia",
    "vnm": "Vietnam", "jpn": "Japan", "kor": "South Korea", "ind": "India",
    "sgp": "Singapore", "mys": "Malaysia", "phl": "Philippines",
    "idn": "Indonesia", "tha": "Thailand", "bra": "Brazil", "mex": "Mexico",
    "are": "United Arab Emirates", "sau": "Saudi Arabia", "pak": "Pakistan",
    "lbn": "Lebanon", "zaf": "South Africa", "tur": "Turkey", "ukr": "Ukraine",
}


def store_brand_re(words=None):
    """Phrase matcher built only from wn_clusters.BRAND_WORDS."""
    words = words if words is not None else wc.BRAND_WORDS
    parts = []
    if "wellnessnest" in words:
        parts.append(r"wellnessnest(?:\.co)?")
    for left in ("wellness", "wellnes", "welness"):
        if left in words and "nest" in words:
            parts.append(r"%s\s+nest" % left)
    if "wellnest" in words:
        parts.append(r"\bwellnest\b")
    if not parts:
        raise RuntimeError("BRAND_WORDS has no store-name phrase")
    return re.compile("|".join(parts), re.I)


STORE_RX = store_brand_re()


def norm_query(query):
    return re.sub(r"\s+", " ", (query or "").strip().lower())


def brand_reason(query):
    text = norm_query(query)
    store = bool(STORE_RX.search(text))
    line = bool(_LINE_TOKEN.search(text) or (_GOLD.search(text) and _SHILAJIT.search(text)))
    if store and line:
        return "store+line"
    if store:
        return "store"
    if line:
        return "line"
    return ""


def is_house_brand(query):
    return bool(brand_reason(query))


def as_int(value):
    if value is None or value == "":
        return 0
    return int(round(float(value)))


def as_float(value):
    if value is None or value == "":
        return 0.0
    return float(value)


def new_bucket():
    return {"clicks": 0, "impressions": 0, "pos_num": 0.0}


def add_bucket(bucket, clicks, impressions, position):
    bucket["clicks"] += clicks
    bucket["impressions"] += impressions
    if impressions:
        bucket["pos_num"] += float(position) * impressions


def merge_bucket(dst, src):
    dst["clicks"] += src["clicks"]
    dst["impressions"] += src["impressions"]
    dst["pos_num"] += src["pos_num"]


def position_of(bucket):
    if not bucket or not bucket.get("impressions"):
        return None
    return bucket["pos_num"] / bucket["impressions"]


def ctr_of(bucket):
    if not bucket or not bucket.get("impressions"):
        return None
    return bucket["clicks"] / bucket["impressions"]


def finish_bucket(bucket):
    return {
        "clicks": bucket["clicks"],
        "impressions": bucket["impressions"],
        "pos_num": bucket["pos_num"],
        "position": position_of(bucket),
        "ctr": ctr_of(bucket),
    }


def url_parts(url):
    raw = (url or "").strip()
    empty = {
        "path": "", "locale": "", "canonical": "", "kind": "",
        "host": "", "ours": False,
    }
    if not raw or raw.startswith(("#", "mailto:", "javascript:", "tel:")):
        return empty
    raw = raw.split("#", 1)[0].split("?", 1)[0].strip()
    if raw.startswith("//"):
        raw = "https:" + raw
    host = ""
    if raw.startswith("/"):
        path = raw
        ours = True
    elif "://" in raw:
        parsed = urlsplit(raw)
        host = (parsed.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        path = parsed.path or "/"
        ours = host in ("", "wellnessnest.co")
    else:
        return empty
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    path = path.lower() or "/"
    segments = [s for s in path.split("/") if s]
    locale = ""
    if segments and re.fullmatch(r"[a-z]{2}", segments[0]) and segments[0] not in RESERVED:
        locale = segments[0]
        rest = segments[1:]
        canonical = "/" + "/".join(rest) if rest else "/"
    else:
        canonical = path
    return {
        "path": path,
        "locale": locale,
        "canonical": canonical,
        "kind": page_kind(canonical),
        "host": host,
        "ours": ours,
    }


def page_kind(canonical):
    canon = canonical or "/"
    if canon in ("", "/"):
        return "home"
    if canon == "/collections" or canon.startswith("/collections/"):
        return "collection"
    if canon.startswith("/blogs/"):
        return "blog"
    if canon.startswith("/products/"):
        return "product"
    if canon.startswith("/pages/"):
        return "page"
    if canon.startswith("/policies/"):
        return "policy"
    if canon.startswith("/tools/"):
        return "tool"
    if canon == "/cart" or canon.startswith("/cart/"):
        return "cart"
    if canon.startswith("/checkouts"):
        return "checkout"
    return "other"


def blog_handle_from_url(url):
    info = url_parts(url)
    if not info["ours"]:
        return ""
    canon = info["canonical"]
    prefix = "/blogs/news/"
    if not canon.startswith(prefix):
        return ""
    handle = canon[len(prefix):]
    if not handle or "/" in handle:
        return ""
    if not wc.HANDLE_RX.fullmatch(handle):
        return ""
    return handle


def label_date(path):
    match = re.search(r"(20\d{2}-\d{2}-\d{2})", os.path.basename(path or ""))
    return match.group(1) if match else ""


def _period_pair():
    return {name: new_bucket() for name in PERIODS}


def analyze_rows(rows, source=""):
    site = _period_pair()
    segments = {True: _period_pair(), False: _period_pair()}
    slices = defaultdict(_period_pair)
    kinds = defaultdict(_period_pair)
    queries = {}
    pages = {}
    brand_pages = {}
    dates = {name: [] for name in PERIODS}
    used = {name: 0 for name in PERIODS}
    ignored = 0

    for row in rows or []:
        period = (row.get("period") or "current").strip().lower() or "current"
        if period not in PERIODS:
            ignored += 1
            continue
        clicks = as_int(row.get("clicks"))
        impressions = as_int(row.get("impressions"))
        position = as_float(row.get("position"))
        if clicks == 0 and impressions == 0:
            continue
        query = norm_query(row.get("query") or row.get("key") or "")
        if not query:
            ignored += 1
            continue
        info = url_parts(row.get("page") or "")
        if not info["path"]:
            ignored += 1
            continue
        reason = brand_reason(query)
        brand = bool(reason)
        country = (row.get("country") or "").strip().lower() or "(blank)"
        day = (row.get("date") or "").strip()
        if day:
            dates[period].append(day)

        add_bucket(site[period], clicks, impressions, position)
        add_bucket(segments[brand][period], clicks, impressions, position)
        add_bucket(slices[(brand, info["kind"], country)][period], clicks, impressions, position)
        locale_flag = "locale" if info["locale"] else "unprefixed"
        add_bucket(kinds[(locale_flag, info["kind"])][period], clicks, impressions, position)
        used[period] += 1

        q = queries.get(query)
        if q is None:
            q = {
                "query": query,
                "brand": brand,
                "reason": reason,
                "metrics": _period_pair(),
                "pages": {},
                "countries": defaultdict(_period_pair),
            }
            queries[query] = q
        add_bucket(q["metrics"][period], clicks, impressions, position)
        add_bucket(q["countries"][country][period], clicks, impressions, position)
        page = q["pages"].get(info["path"])
        if page is None:
            page = {"info": info, "metrics": _period_pair()}
            q["pages"][info["path"]] = page
        add_bucket(page["metrics"][period], clicks, impressions, position)

        for index in (pages, brand_pages if brand else None):
            if index is None:
                continue
            owned = index.get(info["path"])
            if owned is None:
                owned = {"info": info, "metrics": _period_pair()}
                index[info["path"]] = owned
            add_bucket(owned["metrics"][period], clicks, impressions, position)

    _check(site, segments)
    return _finalize(source, site, segments, slices, kinds, queries, pages, brand_pages, dates, used, ignored)


def analyze_csv(path):
    return analyze_rows(wc.read_gsc_csv(path), source=path)


def _check(site, segments):
    for period in PERIODS:
        clicks = segments[True][period]["clicks"] + segments[False][period]["clicks"]
        impressions = segments[True][period]["impressions"] + segments[False][period]["impressions"]
        pos_num = segments[True][period]["pos_num"] + segments[False][period]["pos_num"]
        if clicks != site[period]["clicks"] or impressions != site[period]["impressions"]:
            raise RuntimeError("segment totals do not add up to the site for %s" % period)
        if abs(pos_num - site[period]["pos_num"]) > 1e-6:
            raise RuntimeError("position weight does not add up for %s" % period)


def _date_span(days):
    if not days:
        return {"date_min": "", "date_max": "", "distinct_dates": 0}
    ordered = sorted(set(days))
    return {"date_min": ordered[0], "date_max": ordered[-1], "distinct_dates": len(ordered)}


def _url_row(info, metrics):
    return {
        "path": info["path"],
        "locale": info["locale"],
        "canonical": info["canonical"],
        "kind": info["kind"],
        "current": finish_bucket(metrics["current"]),
        "prior": finish_bucket(metrics["prior"]),
    }


def _canonical_rows(url_rows):
    groups = {}
    for url in url_rows:
        key = url["canonical"] or url["path"]
        group = groups.get(key)
        if group is None:
            group = {
                "canonical": key,
                "kind": url["kind"],
                "locales": set(),
                "current": new_bucket(),
                "prior": new_bucket(),
            }
            groups[key] = group
        group["locales"].add(url["locale"])
        for period in PERIODS:
            merge_bucket(group[period], {
                "clicks": url[period]["clicks"],
                "impressions": url[period]["impressions"],
                "pos_num": url[period]["pos_num"],
            })
    out = []
    for group in groups.values():
        out.append({
            "canonical": group["canonical"],
            "kind": group["kind"],
            "locales": sorted(group["locales"], key=lambda code: (code != "", code)),
            "current": finish_bucket(group["current"]),
            "prior": finish_bucket(group["prior"]),
        })
    out.sort(key=lambda row: (-max(row["current"]["impressions"], row["prior"]["impressions"]), row["canonical"]))
    return out


def _finalize(source, site, segments, slices, kinds, queries, pages, brand_pages, dates, used, ignored):
    query_rows = []
    for query in queries.values():
        urls = [_url_row(page["info"], page["metrics"]) for page in query["pages"].values()]
        urls.sort(key=lambda row: (-row["current"]["impressions"], -row["prior"]["impressions"], row["path"]))
        countries = []
        for country, metrics in query["countries"].items():
            countries.append({
                "country": country,
                "current": finish_bucket(metrics["current"]),
                "prior": finish_bucket(metrics["prior"]),
            })
        countries.sort(key=lambda row: (-row["current"]["impressions"], row["country"]))
        current_urls = sum(1 for row in urls if row["current"]["impressions"])
        prior_urls = sum(1 for row in urls if row["prior"]["impressions"])
        query_rows.append({
            "query": query["query"],
            "brand": query["brand"],
            "reason": query["reason"],
            "current": finish_bucket(query["metrics"]["current"]),
            "prior": finish_bucket(query["metrics"]["prior"]),
            "urls": urls,
            "countries": countries,
            "canonicals": _canonical_rows(urls),
            "current_url_count": current_urls,
            "prior_url_count": prior_urls,
            "locale_impressions": {
                "current": sum(row["current"]["impressions"] for row in urls if row["locale"]),
                "prior": sum(row["prior"]["impressions"] for row in urls if row["locale"]),
            },
        })
    query_rows.sort(key=lambda row: (-row["current"]["impressions"], row["query"]))

    def page_list(index):
        rows = [_url_row(page["info"], page["metrics"]) for page in index.values()]
        rows.sort(key=lambda row: (-row["current"]["impressions"], row["path"]))
        return rows

    kind_rows = []
    for (locale_flag, kind), metrics in kinds.items():
        kind_rows.append({
            "locale": locale_flag,
            "kind": kind,
            "current": finish_bucket(metrics["current"]),
            "prior": finish_bucket(metrics["prior"]),
        })
    kind_rows.sort(key=lambda row: (-row["current"]["impressions"], row["locale"], row["kind"]))

    slice_rows = []
    for (brand, kind, country), metrics in slices.items():
        slice_rows.append({
            "brand": brand,
            "kind": kind,
            "country": country,
            "current": finish_bucket(metrics["current"]),
            "prior": finish_bucket(metrics["prior"]),
        })
    slice_rows.sort(key=lambda row: (-row["current"]["impressions"], row["country"], row["kind"]))

    periods = {}
    for name in PERIODS:
        periods[name] = dict(finish_bucket(site[name]), **_date_span(dates[name]), rows=used[name])
    segment_out = {}
    for flag, label in ((True, "brand"), (False, "nonbrand")):
        segment_out[label] = {name: finish_bucket(segments[flag][name]) for name in PERIODS}

    return {
        "source": source,
        "label_date": label_date(source),
        "ignored_rows": ignored,
        "periods": periods,
        "segments": segment_out,
        "queries": query_rows,
        "pages": page_list(pages),
        "brand_pages": page_list(brand_pages),
        "kinds": kind_rows,
        "slices": slice_rows,
    }


def cannibal_queries(analysis):
    rows = []
    for query in analysis["queries"]:
        if not query["brand"]:
            continue
        if query["current_url_count"] >= 2 or query["prior_url_count"] >= 2:
            rows.append(query)
    return rows


def mix_at_prior_positions(analysis):
    """Site position using the current impression split and the prior segment positions."""
    return _reweight(analysis, impression_period="current", position_period="prior")


def prior_mix_at_current_positions(analysis):
    """Site position using the prior impression split and the current segment positions."""
    return _reweight(analysis, impression_period="prior", position_period="current")


def _reweight(analysis, impression_period, position_period):
    total = 0
    weighted = 0.0
    for label in ("brand", "nonbrand"):
        impressions = analysis["segments"][label][impression_period]["impressions"]
        position = analysis["segments"][label][position_period]["position"]
        if impressions and position is None:
            return None
        total += impressions
        weighted += impressions * (position or 0.0)
    if not total:
        return None
    return weighted / total


def inclusive_overlap(start_a, end_a, start_b, end_b):
    if not (start_a and end_a and start_b and end_b):
        return None
    start = max(start_a, start_b)
    end = min(end_a, end_b)
    if start > end:
        return None
    return start, end


def day_after(earlier, later):
    if not earlier or not later:
        return False
    return dt.date.fromisoformat(later) == dt.date.fromisoformat(earlier) + dt.timedelta(days=1)


def manual_search_url(query, country):
    gl = GL.get(country, "")
    hl = HL.get(country, "en")
    url = "https://www.google.com/search?q=%s&hl=%s&pws=0" % (quote_plus(query), hl)
    if gl:
        url += "&gl=%s" % gl
    return url


def default_serp_probe():
    names = sorted(
        key for key in os.environ
        if any(token in key.upper() for token in ("SERP", "CSE", "BING", "BRAVE", "VALUESERP"))
    )
    key_file = os.path.expanduser("~/.config/claude-seo/google-api.json")
    return {
        "called": False,
        "env_names": names,
        "google_api_file_present": os.path.exists(key_file),
        "reason": (
            "No SERP, CSE, Bing, Brave, or ValueSERP variable is set"
            if not names else
            "Search-like env names are present (%s); this run still did not call them" % ", ".join(names)
        ),
    }


def focus_rows(analysis, focus=None):
    focus = focus or DEFAULT_FOCUS
    by_query = {row["query"]: row for row in analysis["queries"]}
    out = []
    for query, role in focus:
        found = by_query.get(query)
        if found is None:
            out.append({"query": query, "role": role, "missing": True})
        else:
            row = dict(found)
            row["role"] = role
            row["missing"] = False
            out.append(row)
    return out


def fmt_pos(bucket_or_pos):
    if isinstance(bucket_or_pos, dict):
        pos = bucket_or_pos.get("position")
    else:
        pos = bucket_or_pos
    if pos is None:
        return "n/a"
    return "%.1f" % pos


def fmt_pct(part, whole):
    if not whole:
        return "n/a"
    return "%.1f%%" % (100.0 * part / whole)


def fmt_ctr(bucket):
    ctr = bucket.get("ctr") if isinstance(bucket, dict) else None
    if ctr is None:
        return "n/a"
    return "%.2f%%" % (100.0 * ctr)


def fmt_delta_int(current, prior):
    return "%+d" % (current - prior)


def fmt_pos_delta(current, prior):
    if current is None or prior is None:
        return "n/a"
    return "%+.1f" % (current - prior)


def cell(value):
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell(col) for col in row) + " |")
    return lines


def locale_list(codes):
    return ", ".join(code or "unprefixed" for code in codes)


def _metric_cells(bucket):
    return [
        bucket["clicks"],
        bucket["impressions"],
        fmt_pct(bucket["clicks"], bucket["impressions"]),
        fmt_pos(bucket),
    ]


def finding_lines(analysis, focus=None):
    current = analysis["periods"]["current"]
    prior = analysis["periods"]["prior"]
    brand = analysis["segments"]["brand"]
    other = analysis["segments"]["nonbrand"]
    lines = []
    lines.append(
        "Current dates in this CSV: %s to %s (%d distinct dates, %d rows). "
        "%d clicks, %d impressions, weighted position %s. "
        "Prior dates: %s to %s (%d distinct dates, %d rows). "
        "%d clicks, %d impressions, weighted position %s."
        % (
            current["date_min"], current["date_max"], current["distinct_dates"], current["rows"],
            current["clicks"], current["impressions"], fmt_pos(current),
            prior["date_min"], prior["date_max"], prior["distinct_dates"], prior["rows"],
            prior["clicks"], prior["impressions"], fmt_pos(prior),
        )
    )
    lines.append(
        "House-brand queries: position %s prior to %s current (%s), impressions %d to %d (%s), "
        "clicks %d to %d (%s). Other queries: position %s prior to %s current (%s), "
        "impressions %d to %d (%s), clicks %d to %d (%s)."
        % (
            fmt_pos(brand["prior"]), fmt_pos(brand["current"]),
            fmt_pos_delta(brand["current"]["position"], brand["prior"]["position"]),
            brand["prior"]["impressions"], brand["current"]["impressions"],
            fmt_delta_int(brand["current"]["impressions"], brand["prior"]["impressions"]),
            brand["prior"]["clicks"], brand["current"]["clicks"],
            fmt_delta_int(brand["current"]["clicks"], brand["prior"]["clicks"]),
            fmt_pos(other["prior"]), fmt_pos(other["current"]),
            fmt_pos_delta(other["current"]["position"], other["prior"]["position"]),
            other["prior"]["impressions"], other["current"]["impressions"],
            fmt_delta_int(other["current"]["impressions"], other["prior"]["impressions"]),
            other["prior"]["clicks"], other["current"]["clicks"],
            fmt_delta_int(other["current"]["clicks"], other["prior"]["clicks"]),
        )
    )
    lines.append(
        "House-brand queries are %s of current impressions and %s of current clicks "
        "(prior impressions %s, prior clicks %s)."
        % (
            fmt_pct(brand["current"]["impressions"], current["impressions"]),
            fmt_pct(brand["current"]["clicks"], current["clicks"]),
            fmt_pct(brand["prior"]["impressions"], prior["impressions"]),
            fmt_pct(brand["prior"]["clicks"], prior["clicks"]),
        )
    )
    mixed = mix_at_prior_positions(analysis)
    rated = prior_mix_at_current_positions(analysis)
    if mixed is not None and prior["position"] is not None and current["position"] is not None:
        mix_gap = mixed - prior["position"]
        pos_gap = current["position"] - mixed
        lines.append(
            "Accounting split of the site position, still only this CSV: prior site %s, "
            "current site %s. Current impression split at the prior segment positions would be %s "
            "(%s from the mix). Prior impression split at the current segment positions would be %s. "
            "From the mix-held figure to the actual current figure is %s. "
            "Mix piece %+.1f. Position piece %+.1f. Those two pieces sum to the site change. "
            "This split does not name another website."
            % (
                fmt_pos(prior), fmt_pos(current), fmt_pos(mixed), fmt_pos_delta(mixed, prior["position"]),
                fmt_pos(rated), fmt_pos_delta(current["position"], mixed),
                mix_gap, pos_gap,
            )
        )
    for query in focus_rows(analysis, focus):
        lines.extend(_query_finding(query))
    return lines


def _query_finding(query):
    if query.get("missing"):
        return ["%s: no rows in this CSV." % query["query"]]
    role = "Control query. " if query.get("role") == "control" else ""
    lines = [(
        "%s%s: position %s prior, %s current (%s); impressions %d prior, %d current (%s); "
        "clicks %d prior, %d current (%s); URLs with impressions %d prior, %d current."
        % (
            role, query["query"],
            fmt_pos(query["prior"]), fmt_pos(query["current"]),
            fmt_pos_delta(query["current"]["position"], query["prior"]["position"]),
            query["prior"]["impressions"], query["current"]["impressions"],
            fmt_delta_int(query["current"]["impressions"], query["prior"]["impressions"]),
            query["prior"]["clicks"], query["current"]["clicks"],
            fmt_delta_int(query["current"]["clicks"], query["prior"]["clicks"]),
            query["prior_url_count"], query["current_url_count"],
        )
    )]
    busiest = _busiest_current_url(query)
    if busiest is not None:
        lines.append(
            "On \"%s\", the current URL with the most impressions is %s: "
            "%d impressions at position %s. The query average is %s across %d URLs."
            % (
                query["query"], busiest["path"], busiest["current"]["impressions"],
                fmt_pos(busiest["current"]), fmt_pos(query["current"]),
                query["current_url_count"],
            )
        )
    strongest = _strongest_current_url(query, floor=10)
    if strongest is not None and (busiest is None or strongest["path"] != busiest["path"]):
        lines.append(
            "On \"%s\", the strongest position among URLs with at least 10 current impressions is %s "
            "at %s (%d impressions)."
            % (
                query["query"], strongest["path"], fmt_pos(strongest["current"]),
                strongest["current"]["impressions"],
            )
        )
    lines.append(
        "On \"%s\", locale-prefixed URLs are %d of %d current impressions (%s); "
        "prior %d of %d (%s)."
        % (
            query["query"],
            query["locale_impressions"]["current"], query["current"]["impressions"],
            fmt_pct(query["locale_impressions"]["current"], query["current"]["impressions"]),
            query["locale_impressions"]["prior"], query["prior"]["impressions"],
            fmt_pct(query["locale_impressions"]["prior"], query["prior"]["impressions"]),
        )
    )
    for group in query["canonicals"]:
        if group["kind"] != "blog":
            continue
        if max(group["current"]["impressions"], group["prior"]["impressions"]) < 10:
            continue
        lines.append(
            "On \"%s\", blog canonical %s (%s): position %s prior, %s current; "
            "impressions %d prior, %d current."
            % (
                query["query"], group["canonical"], locale_list(group["locales"]),
                fmt_pos(group["prior"]), fmt_pos(group["current"]),
                group["prior"]["impressions"], group["current"]["impressions"],
            )
        )
    return lines


def _busiest_current_url(query):
    ranked = [url for url in query["urls"] if url["current"]["impressions"]]
    if not ranked:
        return None
    return max(ranked, key=lambda url: (url["current"]["impressions"], -(url["current"]["position"] or 999)))


def _strongest_current_url(query, floor=10):
    ranked = [
        url for url in query["urls"]
        if url["current"]["impressions"] >= floor and url["current"]["position"] is not None
    ]
    if not ranked:
        return None
    return min(ranked, key=lambda url: (url["current"]["position"], -url["current"]["impressions"]))


def _select_urls(query, url_min, url_limit):
    ranked = sorted(
        query["urls"],
        key=lambda url: (-max(url["current"]["impressions"], url["prior"]["impressions"]), url["path"]),
    )
    chosen = [
        url for url in ranked
        if max(url["current"]["impressions"], url["prior"]["impressions"]) >= url_min
    ][:url_limit]
    chosen_paths = {url["path"] for url in chosen}
    rest = [url for url in ranked if url["path"] not in chosen_paths]
    rest_current = sum(url["current"]["impressions"] for url in rest)
    rest_prior = sum(url["prior"]["impressions"] for url in rest)
    return chosen, rest, rest_current, rest_prior


def _bucket_row(label, bucket, extra=None):
    row = [label, bucket["clicks"], bucket["impressions"], fmt_pct(bucket["clicks"], bucket["impressions"]), fmt_pos(bucket)]
    if extra:
        row.extend(extra)
    return row


def render_report(analyses, focus=None, url_min=10, url_limit=40, paid_min=20, serp_probe=None):
    if not analyses:
        raise RuntimeError("no CSV analyses")
    primary = analyses[0]
    probe = serp_probe if serp_probe is not None else default_serp_probe()
    title_date = primary["label_date"] or primary["periods"]["current"]["date_max"] or "undated"
    lines = [
        "# Brand SERP defence — %s" % title_date,
        "",
        "Read-only diagnosis of the Wellness Nest house-brand position slide. "
        "Every figure is summed from the Search Console CSV named below. "
        "This file does not edit the theme, the homepage, products, collections, "
        "pages, checkout, landing listicles, or any blog article.",
        "",
        "## Sources and method",
        "",
        "Primary file: `%s`." % (primary["source"] or "(rows in memory)"),
        "",
        "Reader: `wn_clusters.read_gsc_csv`. Store-name phrases are built from "
        "`wn_clusters.BRAND_WORDS` (wellness nest, wellnessnest, and the misspellings "
        "wellnes nest, welness nest, wellnest). A lone \"wellness\" or \"nest\" is not the store. "
        "House lines: fusiforce, shilasource, florafresh, ageaura, menomate, shockwave, "
        "and gold resin only when the query also says shilajit. "
        "Bare turkesterone stays with the other queries.",
        "",
        "Position is impression-weighted across date and device. The CSV `ctr` column is not used. "
        "A query average can sit in the 20s while one of our URLs on that query is still near the top, "
        "because the average mixes every URL that received impressions.",
        "",
        "Windows are the minimum and maximum `date` values present on the rows, not a date typed in by hand.",
        "",
        "## Findings",
        "",
    ]
    for line in finding_lines(primary, focus):
        lines.append("- %s" % line)
    lines.extend(_totals_section(primary))
    lines.extend(_shift_section(primary))
    lines.extend(_focus_table(primary, focus))
    lines.extend(_canonical_section(primary, focus))
    lines.extend(_url_section(primary, focus, url_min, url_limit))
    lines.extend(_country_section(primary, focus))
    lines.extend(_cannibal_section(primary))
    lines.extend(_kind_section(primary))
    lines.extend(_named_section(primary))
    lines.extend(_other_section(primary))
    if len(analyses) > 1:
        lines.extend(_earlier_section(primary, analyses[1:], focus))
    lines.extend(_serp_section(primary, focus, probe))
    lines.extend(_suggestion_section(primary, paid_min))
    lines.extend(_blog_section(primary, focus))
    lines.extend(_go_section(primary, focus, probe))
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _totals_section(analysis):
    current = analysis["periods"]["current"]
    prior = analysis["periods"]["prior"]
    brand = analysis["segments"]["brand"]
    other = analysis["segments"]["nonbrand"]
    lines = ["", "## Site totals", ""]
    lines.extend(md_table(
        ["slice", "clicks", "impressions", "CTR", "position", "prior clicks", "prior impressions", "prior position"],
        [
            ["site", current["clicks"], current["impressions"], fmt_ctr(current),
             fmt_pos(current), prior["clicks"], prior["impressions"], fmt_pos(prior)],
            ["house brand", brand["current"]["clicks"], brand["current"]["impressions"],
             fmt_ctr(brand["current"]), fmt_pos(brand["current"]),
             brand["prior"]["clicks"], brand["prior"]["impressions"], fmt_pos(brand["prior"])],
            ["other", other["current"]["clicks"], other["current"]["impressions"],
             fmt_ctr(other["current"]), fmt_pos(other["current"]),
             other["prior"]["clicks"], other["prior"]["impressions"], fmt_pos(other["prior"])],
        ],
    ))
    lines.append("")
    lines.append(
        "House-brand rows and other rows add up to the site row. Ignored rows: %d."
        % analysis["ignored_rows"]
    )
    return lines


def _shift_section(analysis):
    mixed = mix_at_prior_positions(analysis)
    rated = prior_mix_at_current_positions(analysis)
    lines = ["", "## Where the site average moved", ""]
    lines.extend(md_table(
        ["figure", "position"],
        [
            ["Prior site, as summed", fmt_pos(analysis["periods"]["prior"])],
            ["Current impression split at prior segment positions", fmt_pos(mixed)],
            ["Prior impression split at current segment positions", fmt_pos(rated)],
            ["Current site, as summed", fmt_pos(analysis["periods"]["current"])],
        ],
    ))
    lines.append("")
    lines.append(
        "Segment means house-brand queries versus every other query. "
        "The two counterfactuals are arithmetic on those four buckets."
    )
    return lines


def _focus_table(analysis, focus):
    lines = ["", "## Focus queries", ""]
    rows = []
    for query in focus_rows(analysis, focus):
        if query.get("missing"):
            rows.append([query["query"], query["role"], "0", "0", "n/a", "0", "0", "n/a", "0"])
            continue
        rows.append([
            query["query"], query["role"],
            query["current"]["clicks"], query["current"]["impressions"], fmt_pos(query["current"]),
            query["prior"]["clicks"], query["prior"]["impressions"], fmt_pos(query["prior"]),
            query["current_url_count"],
        ])
    lines.extend(md_table(
        ["query", "role", "clicks", "impressions", "position", "prior clicks", "prior impressions", "prior position", "current URLs"],
        rows,
    ))
    return lines


def _canonical_section(analysis, focus):
    lines = ["", "## Locale-duplicate groups on the focus queries", ""]
    lines.append(
        "URLs that share a path after the locale prefix is removed. "
        "Position is impression-weighted across those URLs."
    )
    lines.append("")
    for query in focus_rows(analysis, focus):
        lines.append("### %s" % query["query"])
        lines.append("")
        if query.get("missing"):
            lines.append("No rows.")
            lines.append("")
            continue
        groups = query["canonicals"][:8]
        rows = []
        for group in groups:
            rows.append([
                group["canonical"], group["kind"], locale_list(group["locales"]),
                group["current"]["impressions"], fmt_pos(group["current"]),
                group["prior"]["impressions"], fmt_pos(group["prior"]),
            ])
        lines.extend(md_table(
            ["canonical path", "kind", "locales", "impressions", "position", "prior impressions", "prior position"],
            rows,
        ))
        lines.append("")
    return lines


def _url_section(analysis, focus, url_min, url_limit):
    lines = ["", "## URLs competing on the focus queries", ""]
    lines.append(
        "A URL is listed when the larger of its current and prior impressions is at least %d, "
        "up to %d URLs per query. Pass --json to write every URL."
        % (url_min, url_limit)
    )
    lines.append("")
    for query in focus_rows(analysis, focus):
        lines.append("### %s" % query["query"])
        lines.append("")
        if query.get("missing"):
            lines.append("No rows.")
            lines.append("")
            continue
        chosen, rest, rest_current, rest_prior = _select_urls(query, url_min, url_limit)
        rows = []
        for url in chosen:
            rows.append([
                url["path"], url["kind"], url["locale"] or "unprefixed",
                url["current"]["clicks"], url["current"]["impressions"], fmt_pos(url["current"]),
                url["prior"]["clicks"], url["prior"]["impressions"], fmt_pos(url["prior"]),
            ])
        lines.extend(md_table(
            ["path", "kind", "locale", "clicks", "impressions", "position", "prior clicks", "prior impressions", "prior position"],
            rows,
        ))
        lines.append("")
        lines.append(
            "URLs under that cutoff: %d, with %d current impressions and %d prior impressions."
            % (len(rest), rest_current, rest_prior)
        )
        lines.append("")
    return lines


def _country_section(analysis, focus):
    lines = ["", "## Top countries on the focus queries", ""]
    lines.append("Country codes are the CSV values. Position is impression-weighted inside that country.")
    lines.append("")
    for query in focus_rows(analysis, focus):
        lines.append("### %s" % query["query"])
        lines.append("")
        if query.get("missing"):
            lines.append("No rows.")
            lines.append("")
            continue
        rows = []
        for country in query["countries"][:8]:
            if country["current"]["impressions"] == 0 and country["prior"]["impressions"] == 0:
                continue
            name = COUNTRY_NAME.get(country["country"], "")
            label = country["country"] if not name else "%s (%s)" % (country["country"], name)
            rows.append([
                label,
                country["current"]["clicks"], country["current"]["impressions"], fmt_pos(country["current"]),
                country["prior"]["impressions"], fmt_pos(country["prior"]),
            ])
        lines.extend(md_table(
            ["country", "clicks", "impressions", "position", "prior impressions", "prior position"],
            rows,
        ))
        lines.append("")
    return lines


def _cannibal_section(analysis):
    rows = cannibal_queries(analysis)
    lines = ["", "## Brand queries with two or more URLs", ""]
    lines.append(
        "%d house-brand queries have two or more URLs with impressions in the current window "
        "or in the prior window. The focus section above lists every competing URL for the named queries. "
        "This table is the rest of the brand set, one row per query."
        % len(rows)
    )
    lines.append("")
    table = []
    for query in rows:
        top = query["urls"][0]["path"] if query["urls"] else ""
        table.append([
            query["query"], query["reason"],
            query["current"]["impressions"], fmt_pos(query["current"]),
            query["prior"]["impressions"], fmt_pos(query["prior"]),
            query["current_url_count"],
            fmt_pct(query["locale_impressions"]["current"], query["current"]["impressions"]),
            top,
        ])
    lines.extend(md_table(
        ["query", "match", "impressions", "position", "prior impressions", "prior position", "current URLs", "locale share", "top current path"],
        table,
    ))
    return lines


def _kind_section(analysis):
    lines = ["", "## House-brand impressions by template", ""]
    lines.append(
        "House-brand queries only. \"Locale\" means the URL has a two-letter prefix such as /de or /fr. "
        "\"Unprefixed\" means it does not."
    )
    lines.append("")
    combined = defaultdict(lambda: {name: new_bucket() for name in PERIODS})
    for page in analysis["brand_pages"]:
        flag = "locale" if page["locale"] else "unprefixed"
        slot = combined[(flag, page["kind"])]
        for period in PERIODS:
            merge_bucket(slot[period], page[period])
    rows = []
    for (flag, kind), metrics in combined.items():
        rows.append((
            metrics["current"]["impressions"],
            flag, kind, finish_bucket(metrics["current"]), finish_bucket(metrics["prior"]),
        ))
    rows.sort(key=lambda item: (-item[0], item[1], item[2]))
    lines.extend(md_table(
        ["locale", "kind", "impressions", "position", "prior impressions", "prior position"],
        [
            [flag, kind, cur["impressions"], fmt_pos(cur), pri["impressions"], fmt_pos(pri)]
            for _, flag, kind, cur, pri in rows
        ],
    ))
    return lines


def _named_section(analysis):
    by_path = {page["path"]: page for page in analysis["pages"]}
    lines = ["", "## Named URLs across every query", ""]
    lines.append(
        "These paths are the ones named in the 2026-10-21 GSC note (home, locale homes, "
        "100-shilajit templates, the gummies and FusiForce products, the shilajit collection, "
        "and the shilajit review article). Figures are the CSV rollup of every query on that path."
    )
    lines.append("")
    rows = []
    for path in NAMED_PATHS:
        page = by_path.get(path)
        if page is None:
            rows.append([path, "0", "0", "n/a", "0", "0", "n/a"])
            continue
        rows.append([
            path, page["current"]["clicks"], page["current"]["impressions"], fmt_pos(page["current"]),
            page["prior"]["clicks"], page["prior"]["impressions"], fmt_pos(page["prior"]),
        ])
    lines.extend(md_table(
        ["path", "clicks", "impressions", "position", "prior clicks", "prior impressions", "prior position"],
        rows,
    ))
    return lines


def _other_section(analysis):
    others = [query for query in analysis["queries"] if not query["brand"]]
    others.sort(key=lambda query: (-query["current"]["impressions"], query["query"]))
    lines = ["", "## Other queries with the most impressions", ""]
    lines.append("Shown so the house-brand cut can be checked against the next-largest queries. Top 12.")
    lines.append("")
    rows = []
    for query in others[:12]:
        rows.append([
            query["query"], query["current"]["clicks"], query["current"]["impressions"], fmt_pos(query["current"]),
            query["prior"]["impressions"], fmt_pos(query["prior"]),
        ])
    lines.extend(md_table(
        ["query", "clicks", "impressions", "position", "prior impressions", "prior position"],
        rows,
    ))
    return lines


def _earlier_section(primary, earlier, focus):
    lines = ["", "## Earlier export", ""]
    lines.append(
        "Each file is compared with its own prior window. The files overlap, so one file is not subtracted from the other."
    )
    for analysis in earlier:
        current = analysis["periods"]["current"]
        primary_current = primary["periods"]["current"]
        overlap = inclusive_overlap(
            primary_current["date_min"], primary_current["date_max"],
            current["date_min"], current["date_max"],
        )
        lines.append("")
        lines.append("File: `%s`." % analysis["source"])
        lines.append("")
        if overlap:
            lines.append(
                "Current-window overlap with the primary file: %s to %s."
                % overlap
            )
        else:
            lines.append("Current windows do not overlap.")
        if day_after(current["date_max"], primary_current["date_max"]):
            lines.append("")
            lines.append(
                "The primary current window ends one day after this file's current window (%s, then %s)."
                % (current["date_max"], primary_current["date_max"])
            )
        both_worse = (
            primary["periods"]["current"]["position"] is not None
            and primary["periods"]["prior"]["position"] is not None
            and current["position"] is not None
            and analysis["periods"]["prior"]["position"] is not None
            and primary["periods"]["current"]["position"] > primary["periods"]["prior"]["position"]
            and current["position"] > analysis["periods"]["prior"]["position"]
        )
        if both_worse:
            lines.append("")
            lines.append(
                "In both files the current site position is weaker than that file's own prior window "
                "(%s to %s here; %s to %s in the primary file)."
                % (
                    fmt_pos(analysis["periods"]["prior"]), fmt_pos(current),
                    fmt_pos(primary["periods"]["prior"]), fmt_pos(primary["periods"]["current"]),
                )
            )
        lines.append("")
        rows = []
        for query in focus_rows(analysis, focus):
            if query.get("missing"):
                rows.append([query["query"], "n/a", "0", "n/a", "0"])
                continue
            rows.append([
                query["query"], fmt_pos(query["prior"]), query["prior"]["impressions"],
                fmt_pos(query["current"]), query["current"]["impressions"],
            ])
        lines.extend(md_table(
            ["query", "prior position", "prior impressions", "current position", "current impressions"],
            rows,
        ))
    return lines


def _serp_countries(query):
    picked = []
    seen = set()
    for country in query["countries"]:
        if country["current"]["impressions"] <= 0:
            continue
        if len(picked) < 5 or country["country"] in ("usa", "deu", "fra"):
            if country["country"] not in seen:
                picked.append(country)
                seen.add(country["country"])
    return picked


def _serp_section(analysis, focus, probe):
    lines = ["", "## SERP snapshot — needs a manual check", ""]
    lines.append(probe.get("reason") or "No SERP API was called.")
    if probe.get("google_api_file_present"):
        lines.append("")
        lines.append(
            "A Google API file exists on this machine. It was not read and it was not sent to a search API. "
            "A CrUX key is not a SERP result."
        )
    lines.append("")
    lines.append(
        "This run did not fetch Google, Bing, or any other result page. "
        "The links below are for a person to open. They are not captured rankings. "
        "Our own URL positions are the CSV tables above."
    )
    lines.append("")
    rows = []
    for query in focus_rows(analysis, focus):
        if query.get("missing"):
            rows.append([query["query"], "(no rows)", "", "", "", ""])
            continue
        countries = _serp_countries(query)
        if not countries:
            rows.append([query["query"], "(no current impressions)", "", "", "", ""])
            continue
        for country in countries:
            code = country["country"]
            name = COUNTRY_NAME.get(code, "unmapped country code")
            gl = GL.get(code, "")
            rows.append([
                query["query"],
                code,
                name,
                gl or "(no gl map)",
                country["current"]["impressions"],
                manual_search_url(query["query"], code),
            ])
    lines.extend(md_table(
        ["query", "CSV country", "name", "Google gl", "current impressions", "manual URL"],
        rows,
    ))
    lines.append("")
    lines.append(
        "Open a manual URL signed out, or with personalization off. Record the domains in positions 1–10. "
        "That list is still empty in this report."
    )
    return lines


def _suggestion_section(analysis, paid_min):
    locale_rows = []
    plain_rows = []
    for page in analysis["brand_pages"]:
        if page["kind"] not in PAID_KINDS:
            continue
        if max(page["current"]["impressions"], page["prior"]["impressions"]) < paid_min:
            continue
        target = locale_rows if page["locale"] else plain_rows
        target.append(page)
    lines = ["", "## Suggestion only — do not edit these templates", ""]
    lines.append(
        "Home, product, collection, page, cart, and checkout URLs are paid-traffic or market templates. "
        "Do not edit them from this report. No localized title is written here. "
        "The lever to review later, with a GO, is hreflang and the localized title on the locale copies."
    )
    lines.append("")
    lines.append("### Locale copies on house-brand queries")
    lines.append("")
    lines.append(_paid_table(locale_rows) or "None at the impression cutoff.")
    lines.append("")
    lines.append("### Unprefixed home, product, collection, page, cart, and checkout URLs")
    lines.append("")
    lines.append(
        "These also compete for house-brand queries. Do not edit them in a blog task. "
        "No new title is proposed."
    )
    lines.append("")
    lines.append(_paid_table(plain_rows) or "None at the impression cutoff.")
    lines.append("")
    lines.append("Impression cutoff for both tables: %d (the larger of current and prior)." % paid_min)
    return lines


def _paid_table(pages):
    if not pages:
        return ""
    rows = []
    for page in pages:
        rows.append([
            page["path"], page["kind"], page["locale"] or "unprefixed",
            page["current"]["clicks"], page["current"]["impressions"], fmt_pos(page["current"]),
            page["prior"]["impressions"], fmt_pos(page["prior"]),
        ])
    return "\n".join(md_table(
        ["path", "kind", "locale", "clicks", "impressions", "position", "prior impressions", "prior position"],
        rows,
    ))


def _blog_section(analysis, focus):
    lines = ["", "## Blog URLs on the focus queries", ""]
    lines.append(
        "Blog paths only. Locale copies of one article share a canonical path. "
        "Link proposals for stored blog bodies are a separate file, "
        "`docs/BRAND_BLOG_ANCHOR_PROPOSALS_2026-10-21.md`, and are not applied here."
    )
    lines.append("")
    rows = []
    for query in focus_rows(analysis, focus):
        if query.get("missing"):
            continue
        for url in query["urls"]:
            if url["kind"] != "blog":
                continue
            if url["current"]["impressions"] == 0 and url["prior"]["impressions"] == 0:
                continue
            rows.append([
                query["query"], url["path"], url["locale"] or "unprefixed",
                url["current"]["clicks"], url["current"]["impressions"], fmt_pos(url["current"]),
                url["prior"]["impressions"], fmt_pos(url["prior"]),
            ])
    if not rows:
        lines.append("No blog URL in this CSV has impressions on the focus queries.")
        return lines
    lines.extend(md_table(
        ["query", "path", "locale", "clicks", "impressions", "position", "prior impressions", "prior position"],
        rows,
    ))
    return lines


def _go_section(analysis, focus, probe):
    manual = 0
    for query in focus_rows(analysis, focus):
        if query.get("missing"):
            continue
        manual += len(_serp_countries(query))
    lines = ["", "## What needs a GO", ""]
    lines.append(
        "- Manual SERP check: %d query-and-country rows in the snapshot section. "
        "This run did not collect another site's rankings%s."
        % (manual, "" if probe.get("called") else " and did not call a SERP API")
    )
    lines.append(
        "- Blog body edits: brand-anchor sentences in the proposal file. "
        "Applying them writes article HTML on the news blog and needs a GO. This PR does not apply them."
    )
    lines.append(
        "- Hreflang or localized titles on the locale copies in the suggestion section. "
        "Those URLs are home, product, collection, and page templates. This PR does not edit them."
    )
    lines.append(
        "- No ticket was added to the daily queue, and nothing was published."
    )
    return lines


def public_payload(analyses):
    payload = []
    for analysis in analyses:
        brand = [query for query in analysis["queries"] if query["brand"]]
        others = [query for query in analysis["queries"] if not query["brand"]]
        others.sort(key=lambda query: (-query["current"]["impressions"], query["query"]))
        copied = dict(analysis)
        copied["queries"] = brand
        copied["other_queries_top"] = [
            {key: query[key] for key in ("query", "current", "prior", "current_url_count")}
            for query in others[:15]
        ]
        copied["query_counts"] = {"brand": len(brand), "other": len(others)}
        copied.pop("slices", None)
        payload.append(copied)
    return {"files": payload}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Slice a GSC CSV into house-brand vs other queries")
    parser.add_argument("--csv", action="append", required=True, help="GSC CSV with period, query, page, country")
    parser.add_argument("--report", required=True, help="Markdown path to write")
    parser.add_argument("--json", dest="json_path", help="JSON path for the full brand tables")
    parser.add_argument("--url-min", type=int, default=10)
    parser.add_argument("--url-limit", type=int, default=40)
    parser.add_argument("--paid-min", type=int, default=20)
    args = parser.parse_args(argv)
    analyses = [analyze_csv(path) for path in args.csv]
    report = render_report(
        analyses,
        url_min=args.url_min,
        url_limit=args.url_limit,
        paid_min=args.paid_min,
    )
    os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as handle:
        handle.write(report)
    if args.json_path:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_path)), exist_ok=True)
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump(public_payload(analyses), handle, indent=2, sort_keys=True)
            handle.write("\n")
    primary = analyses[0]
    current = primary["periods"]["current"]
    print(
        "wrote %s | current clicks %d impressions %d position %s"
        % (args.report, current["clicks"], current["impressions"], fmt_pos(current))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

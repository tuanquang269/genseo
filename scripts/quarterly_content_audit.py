#!/usr/bin/env python3
"""Quarterly content audit for the Wellness Nest news blog.

Read-only. Builds a KEEP / REFRESH / CONSOLIDATE / PRUNE sheet from the local
catalog (cluster map, article CSV/JSON, tracker) and, with --crawl, a polite
public read of wellnessnest.co blog URLs. It does not publish, redirect,
unpublish, or edit Shopify.

Thresholds reuse the live pipeline instead of a second copy:

- title near-duplicate: topic_fitness.DUP_JACCARD (0.72) and topic_fitness.sig_words
- clusters and segment ids: wn_clusters.assign_cluster / MODIFIER_SEGMENT / HEAD_TERMS
- thin body: 700 words (build_consolidation_map REDIRECT)
- prune age: 100 days (prune_dead; any measured impression keeps the URL)
- climb / CTR: position >= 13, and refresh_targets CTR band (pos 2–8, CTR < 2%)

  python3 scripts/quarterly_content_audit.py --self-check
  python3 scripts/quarterly_content_audit.py --day 2026-10-20
  python3 scripts/quarterly_content_audit.py --crawl --max-gets 200 --day 2026-10-20

Traffic cells say "needs GSC data" unless --gsc points at a real export.
Word counts stay blank when they were not measured. Nothing here is invented.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html as html_lib
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topic_fitness as tf
import wn_clusters as wc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://wellnessnest.co"
BLOG_PREFIX = SITE + "/blogs/news/"
USER_AGENT = (
    "GenSeoQuarterlyAudit/1.0 (+https://wellnessnest.co; read-only quarterly content audit)"
)

THIN_WORDS = 700
VERY_THIN_WORDS = 400
PILLAR_MIN_WORDS = 1500
STALE_DAYS = 180
PRUNE_MIN_AGE_DAYS = 100
TITLE_DUP_JACCARD = tf.DUP_JACCARD
NEAR_JACCARD = 0.60
BODY_DUP_JACCARD = 0.72
BODY_MIN_TOKENS = 25
# A shared form word ("gummies") is not a second angle. Identical single
# qualifiers still count (two "with coffee" pages).
FORM_WORDS = {"gummies", "gummy", "capsules", "capsule", "resin", "powder", "drops"}
CLIMB_POS = 13.0
CTR_LO = 2.0
CTR_HI = 8.0
CTR_FLOOR = 0.02
CTR_MIN_IMP = 20
LOW_IMP = 20
NEEDS_GSC = "needs GSC data"
NOT_MEASURED = "not measured"
MAX_GETS_DEFAULT = 200
BULK_LASTMOD_SHARE = 0.40

ACTIONS = ("PRUNE", "CONSOLIDATE", "REFRESH", "KEEP")
REPORT_ONLY = "report only"

CONTENT_DROP = {
    "what", "how", "why", "when", "where", "who", "which", "per", "day", "days",
    "week", "weeks", "many", "much", "does", "did", "can", "your", "from", "this",
    "that", "have", "has", "was", "were", "been", "will", "may", "more", "most",
    "some", "any", "all", "out", "our", "should", "actually", "really", "just",
    "not", "its", "into", "than", "about", "over", "under", "things", "thing",
    "know", "show", "shows", "shown", "check", "checks", "real", "need", "needs",
    "used", "using", "trial", "trials", "human", "facts", "fact", "rules", "rule",
    "tips", "tip", "yes", "right", "before", "after",
}

SERIAL_RX = re.compile(
    r"menomate\s+(journey|meal plan)|month\s+\d+\s*[-–—]\s*week\s+\d+|set\s+\d+\s*[-–—]\s*week\s+\d+",
    re.I,
)
MAP_SECTION = re.compile(r"(?m)^(?=## )")
MAP_ID = re.compile(r"^Id: `([a-z0-9-]+)`", re.M)
MAP_LINK = re.compile(
    r"\[([^\]]+)\]\((https://wellnessnest\.co/blogs/news/([a-z0-9-]+))\)(?:\s*\((\d+)\s+words\b[^)]*\))?"
)
PILLAR_LINE = re.compile(r"(?m)^Pillar:\s+")
HREF_RX = re.compile(
    r"""href=["'](?:https://wellnessnest\.co)?/blogs/news/([a-z0-9-]+)""",
    re.I,
)
ARTICLE_SITEMAP_RX = re.compile(
    r"https://wellnessnest\.co/sitemap_articles_\d+\.xml(?:\?[^#\s]*)?"
)
TIME_RX = re.compile(r"""<time\b[^>]*\bdatetime=["']([^"']+)["']""", re.I)
META_RX = re.compile(r"<meta\b[^>]*>", re.I)
CONTENT_RX = re.compile(r"""content=["']([^"']*)["']""", re.I)

CSV_FIELDS = [
    "url",
    "title",
    "cluster",
    "primary_query",
    "primary_query_source",
    "word_count",
    "word_count_source",
    "last_updated",
    "last_updated_source",
    "internal_links_in",
    "duplicate_siblings",
    "suggested_action",
    "merge_into",
    "reason",
    "gsc_clicks",
    "gsc_impressions",
    "gsc_position",
    "gsc_note",
]


def parse_date(value):
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return value
    if isinstance(value, dt.datetime):
        return value.date()
    match = re.search(r"(\d{4}-\d{2}-\d{2})", str(value or ""))
    if not match:
        return None
    year, month, day = (int(part) for part in match.group(1).split("-"))
    try:
        return dt.date(year, month, day)
    except ValueError:
        return None


def age_days(day, today):
    if not day or not today:
        return None
    return (today - day).days


def cluster_label(cid):
    spec = wc.cluster_by_id(cid)
    if spec:
        return spec["label"]
    if cid == "other":
        return "Unclustered"
    return cid or "Unclustered"


def title_jaccard(left, right):
    a = tf.sig_words(left or "")
    b = tf.sig_words(right or "")
    if len(a) < 2 or len(b) < 2:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def segment_ids(title):
    low = (title or "").lower()
    found = set()
    for phrase, seg in wc.MODIFIER_SEGMENT.items():
        if re.search(r"\b" + re.escape(phrase) + r"\b", low):
            found.add(seg)
    return frozenset(found)


def content_tokens(title, cluster_id):
    words = set(tf.sig_words(title or ""))
    words -= wc.HEAD_TERMS.get(cluster_id, set())
    words -= CONTENT_DROP
    low = (title or "").lower()
    for phrase in wc.MODIFIER_SEGMENT:
        if re.search(r"\b" + re.escape(phrase) + r"\b", low):
            words -= set(phrase.split())
    return frozenset(w for w in words if len(w) > 2 and w not in CONTENT_DROP)


def body_signature(text):
    opening = (text or "")[:2500]
    return frozenset(tf.sig_words(opening))


def variant_base(handle):
    h = (handle or "").lower()
    if not wc.is_dupe_handle(h):
        return ""
    if h.endswith("-copy"):
        return h[:-5]
    if "copy-of-" in h:
        return h.split("copy-of-", 1)[-1]
    match = re.search(r"-(\d+)$", h)
    if match:
        return h[: -(len(match.group(1)) + 1)]
    return ""


def is_serial(title, cluster_id):
    return cluster_id == "menopause" and bool(SERIAL_RX.search(title or ""))


def query_key(text):
    words = tf.sig_words(text or "")
    if len(words) < 2:
        return tuple()
    return tuple(sorted(words))


def title_as_query(title):
    text = re.sub(r"\([^)]*\)", " ", title or "")
    text = re.sub(r"\b20\d{2}\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -:")
    return text[:140]


def scope_for(url, handle=""):
    """Blog news articles are in scope. Everything else is report only."""
    handle = (handle or wc.handle_from_url(url or "")).lower()
    path = (url or "").split("?", 1)[0].split("#", 1)[0]
    if handle.startswith("gsl-") or "landing-listicle" in handle or handle.startswith("landing-"):
        return REPORT_ONLY
    if "/blogs/news/" in path and handle:
        return "blog"
    return REPORT_ONLY


def same_segment_duplicate(left, right):
    if left.get("cluster") != right.get("cluster"):
        return False
    segs = left.get("segment_ids") or frozenset()
    if not segs or segs != (right.get("segment_ids") or frozenset()):
        return False
    ca = left.get("content_tokens") or frozenset()
    cb = right.get("content_tokens") or frozenset()
    if not ca and not cb:
        return True
    if not ca or not cb:
        return False
    inter = ca & cb
    if not inter:
        return False
    if inter <= FORM_WORDS and not (ca - FORM_WORDS) and not (cb - FORM_WORDS):
        return False
    if len(inter) >= 2:
        return True
    if ca == cb == inter and not (inter <= FORM_WORDS):
        return True
    union = ca | cb
    return bool(union) and (len(inter) / len(union)) >= TITLE_DUP_JACCARD


def overlap_kind(left, right):
    """Return a consolidate edge label, or '' when the pages stay separate."""
    if left.get("handle") == right.get("handle"):
        return ""
    if left.get("scope") != "blog" or right.get("scope") != "blog":
        return ""
    same_cluster = left.get("cluster") == right.get("cluster")
    jac = title_jaccard(left.get("title"), right.get("title"))
    # Template titles ("how long does X take to work") match across clusters.
    # Cross-cluster title merges need a near-identical token set.
    if jac >= TITLE_DUP_JACCARD and (same_cluster or jac >= 0.90):
        return "title %.2f" % jac
    lb = left.get("body_tokens") or frozenset()
    rb = right.get("body_tokens") or frozenset()
    if len(lb) >= BODY_MIN_TOKENS and len(rb) >= BODY_MIN_TOKENS:
        union = lb | rb
        body_score = len(lb & rb) / len(union) if union else 0.0
        if body_score >= BODY_DUP_JACCARD and (same_cluster or body_score >= 0.90):
            return "body %.2f" % body_score
    lq = left.get("query_key") or tuple()
    rq = right.get("query_key") or tuple()
    lsrc = left.get("primary_query_source")
    rsrc = right.get("primary_query_source")
    if lq and lq == rq and lsrc in {"tracker", "gsc"} and rsrc in {"tracker", "gsc"}:
        return "primary query"
    if is_serial(left.get("title"), left.get("cluster")) and is_serial(right.get("title"), right.get("cluster")):
        return "menomate serial"
    if same_segment_duplicate(left, right):
        segs = ",".join(sorted(left.get("segment_ids") or []))
        return "segment %s" % segs
    return ""


def near_kind(left, right):
    if left.get("scope") != "blog" or right.get("scope") != "blog":
        return ""
    if left.get("cluster") != right.get("cluster"):
        handle_hit = variant_base(left.get("handle")) == right.get("handle") or variant_base(right.get("handle")) == left.get("handle")
        if not handle_hit:
            return ""
    jac = title_jaccard(left.get("title"), right.get("title"))
    base_hit = variant_base(left.get("handle")) == right.get("handle") or variant_base(right.get("handle")) == left.get("handle")
    if base_hit and jac < TITLE_DUP_JACCARD:
        return "handle variant"
    if left.get("cluster") == right.get("cluster") and NEAR_JACCARD <= jac < TITLE_DUP_JACCARD:
        shared = (left.get("content_tokens") or frozenset()) & (right.get("content_tokens") or frozenset())
        if shared and not shared <= FORM_WORDS:
            return "near title %.2f" % jac
    return ""


class _UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))

    def find(self, idx):
        while self.parent[idx] != idx:
            self.parent[idx] = self.parent[self.parent[idx]]
            idx = self.parent[idx]
        return idx

    def union(self, left, right):
        ra, rb = self.find(left), self.find(right)
        if ra != rb:
            self.parent[rb] = ra


def gsc_measured(article):
    return article.get("gsc_state") == "measured"


def strength_key(article):
    words = article.get("words") or 0
    inbound = article.get("inbound") if isinstance(article.get("inbound"), int) else 0
    pillar = 1 if article.get("is_pillar") else 0
    published = article.get("published")
    date_key = (1, -published.toordinal()) if published else (0, 0)
    if gsc_measured(article):
        pos = article.get("gsc_position")
        return (
            article.get("gsc_clicks") or 0,
            article.get("gsc_impressions") or 0,
            -(pos if isinstance(pos, (int, float)) else 999),
            pillar,
            words,
            inbound,
            date_key,
        )
    return (pillar, words, inbound, date_key)


def assign_overlap(articles):
    """Group blog rows that should consolidate. Near misses stay on the row."""
    indexes = [i for i, row in enumerate(articles) if row.get("scope") == "blog" and _groupable(row)]
    uf = _UnionFind(len(articles))
    edge = {}
    for pos, i in enumerate(indexes):
        for j in indexes[pos + 1:]:
            kind = overlap_kind(articles[i], articles[j])
            if kind:
                uf.union(i, j)
                edge[(i, j)] = kind
    groups = defaultdict(list)
    for i in indexes:
        groups[uf.find(i)].append(i)
    for members in groups.values():
        if len(members) < 2:
            continue
        winner_i = max(members, key=lambda i: strength_key(articles[i]))
        winner = articles[winner_i]
        losers = []
        for i in members:
            if i == winner_i:
                continue
            row = articles[i]
            kind = overlap_kind(row, winner) or edge.get((min(i, winner_i), max(i, winner_i))) or "grouped overlap"
            row["merge_into"] = winner.get("url") or ""
            row["overlap_edge"] = kind
            row["consolidate"] = True
            losers.append(row.get("handle") or "")
        winner["group_losers"] = losers
        winner["is_group_winner"] = True
    for pos, i in enumerate(indexes):
        nears = []
        for j in indexes[pos + 1:]:
            kind = near_kind(articles[i], articles[j])
            if not kind:
                continue
            nears.append((articles[j].get("handle") or "", kind))
            articles[j].setdefault("_near_back", []).append((articles[i].get("handle") or "", kind))
        if nears:
            articles[i].setdefault("near_pairs", []).extend(nears)
    for row in articles:
        extra = row.pop("_near_back", [])
        if extra:
            row.setdefault("near_pairs", []).extend(extra)


def _groupable(row):
    if row.get("redirect_handle"):
        return False
    if row.get("http_status") in (404, 410):
        return False
    if row.get("frozen") or (row.get("handle") or "").startswith("generated-article"):
        return False
    return True


def sibling_text(row):
    parts = []
    if row.get("consolidate") and row.get("merge_into"):
        handle = wc.handle_from_url(row.get("merge_into") or "")
        parts.append("%s [%s]" % (handle, row.get("overlap_edge") or "overlap"))
        for handle in row.get("group_losers") or []:
            parts.append("%s [consolidate candidate]" % handle)
    seen = {part.split(" ", 1)[0] for part in parts}
    for handle, kind in row.get("near_pairs") or []:
        if handle and handle not in seen:
            parts.append("%s [%s]" % (handle, kind))
            seen.add(handle)
    return "; ".join(parts)


def _measured_int(value):
    return value if isinstance(value, int) else None


def prune_reason(row, today, cluster_size):
    if row.get("is_pillar") or row.get("is_group_winner"):
        return ""
    if row.get("frozen") or (row.get("handle") or "").startswith("generated-article"):
        return ""
    published = row.get("published")
    age = age_days(published, today)
    if age is None or age <= PRUNE_MIN_AGE_DAYS:
        return ""
    words = row.get("words")
    if gsc_measured(row):
        clicks = row.get("gsc_clicks") or 0
        imps = row.get("gsc_impressions") or 0
        if clicks > 0 or imps > 0:
            return ""
        if words is None or words >= THIN_WORDS:
            return ""
        return (
            "GSC export shows zero clicks and zero impressions, the body is %s words "
            "(under %s), and the publish date is %s days old. Proposal: noindex or "
            "unpublish, then redirect, after approval."
            % (words, THIN_WORDS, age)
        )
    inbound = row.get("inbound")
    complete = bool(row.get("bodies_complete"))
    if (
        words is not None
        and words < VERY_THIN_WORDS
        and complete
        and inbound == 0
        and cluster_size > 1
    ):
        return (
            "Body is %s words (under %s), no other news article links here, "
            "the publish date is %s days old, and this cluster has other pages. "
            "Traffic cells say needs GSC data, so this prune is structural. "
            "Approval still needs a Search Console check before any URL change."
            % (words, VERY_THIN_WORDS, age)
        )
    return ""


def refresh_reasons(row, today):
    reasons = []
    words = row.get("words")
    updated = row.get("updated") or row.get("published")
    age = age_days(row.get("published"), today)
    updated_age = age_days(updated, today)
    if row.get("is_pillar") and words is not None and words < PILLAR_MIN_WORDS:
        reasons.append(
            "Pillar body is %s words, under the %s-word pillar depth."
            % (words, PILLAR_MIN_WORDS)
        )
    if words is not None and words < THIN_WORDS:
        reasons.append("Body is %s words, under the %s-word thin line." % (words, THIN_WORDS))
    if updated_age is not None and updated_age > STALE_DAYS:
        reasons.append("Last updated %s (%s days ago)." % (updated.isoformat(), updated_age))
    if gsc_measured(row):
        clicks = row.get("gsc_clicks") or 0
        imps = row.get("gsc_impressions") or 0
        pos = row.get("gsc_position")
        if isinstance(pos, (int, float)) and imps >= CTR_MIN_IMP and pos >= CLIMB_POS:
            reasons.append(
                "GSC average position %.1f with %s impressions. Append depth and keep the title."
                % (pos, imps)
            )
        if (
            isinstance(pos, (int, float))
            and CTR_LO <= pos < CTR_HI
            and imps >= CTR_MIN_IMP
            and (clicks / imps if imps else 0) < CTR_FLOOR
        ):
            reasons.append(
                "GSC position %.1f with CTR %.1f%% on %s impressions. Sharpen the meta and keep the title."
                % (pos, (100.0 * clicks / imps) if imps else 0, imps)
            )
        if clicks == 0 and 0 < imps < LOW_IMP and words is not None and words < THIN_WORDS:
            reasons.append(
                "GSC shows %s impressions and zero clicks, under the consolidation-map floor of %s. "
                "An impression was measured, so the proposal is a refresh."
                % (imps, LOW_IMP)
            )
        if clicks == 0 and imps == 0 and (words is None or words >= THIN_WORDS) and age and age > PRUNE_MIN_AGE_DAYS:
            reasons.append(
                "GSC export shows zero clicks and zero impressions. The body is long enough "
                "that the proposal is a refresh rather than a removal."
            )
    for handle, kind in row.get("near_pairs") or []:
        reasons.append("Overlap with %s (%s)." % (handle, kind))
        break
    return reasons


def lone_suffix_note(row, handles):
    base = variant_base(row.get("handle") or "")
    if not base or base in handles:
        return ""
    return "Handle ends in a copy suffix and the base URL %s is not in this catalog." % base


def decide(row, today, cluster_size, handles):
    if row.get("scope") != "blog":
        target = row.get("url") or row.get("handle") or ""
        return REPORT_ONLY, "Outside the news blog (%s). Listed for the owner; no edit is proposed." % target
    if row.get("frozen") or (row.get("handle") or "").startswith("generated-article"):
        return "KEEP", "Frozen or generated-article recovery handle. Left off the prune list."
    if row.get("redirect_handle"):
        final = row.get("final_url") or ""
        if scope_for(final, row.get("redirect_handle")) == "blog":
            return (
                "KEEP",
                "Public URL already redirects to %s. Leave that redirect in place." % final,
            )
        return (
            REPORT_ONLY,
            "News URL redirects to %s, which is outside the blog. No edit to that destination is proposed."
            % final,
        )
    if row.get("consolidate"):
        bits = [
            "Consolidate into %s (%s)." % (row.get("merge_into") or "", row.get("overlap_edge") or "overlap")
        ]
        if gsc_measured(row) and (row.get("gsc_clicks") or 0) > 0:
            bits.append(
                "Higher risk: GSC clicks are %s. Merge the unique sections before any redirect."
                % row.get("gsc_clicks")
            )
        if row.get("is_pillar"):
            bits.append("Higher risk: this URL is the cluster pillar.")
        bits.append("Merge unique sections into the stronger page, unpublish this URL, then add the redirect after approval.")
        return "CONSOLIDATE", " ".join(bits)
    if row.get("http_status") in (404, 410):
        return (
            "PRUNE",
            "Public article URL returned HTTP %s. Confirm the path is gone before any redirect is added."
            % row.get("http_status"),
        )
    note = lone_suffix_note(row, handles)
    if row.get("is_group_winner"):
        losers = ", ".join(row.get("group_losers") or [])
        lead = "Stronger page for consolidate candidate(s): %s. Absorb useful sections here before any redirect." % losers
        extra = refresh_reasons(row, today)
        if extra:
            text = lead + " " + " ".join(extra)
        else:
            text = lead
        if note:
            text = text + " " + note
        return ("REFRESH" if extra else "KEEP"), text
    reason = prune_reason(row, today, cluster_size)
    if reason:
        return "PRUNE", reason + ((" " + note) if note else "")
    extra = refresh_reasons(row, today)
    if extra:
        text = " ".join(extra)
        if note:
            text += " " + note
        return "REFRESH", text
    text = "Distinct page in its cluster, with no thin, stale, or duplicate signal on the fields that were measured."
    if gsc_measured(row) and (row.get("gsc_clicks") or 0) == 0 and (row.get("gsc_impressions") or 0) == 0:
        text = "No thin or duplicate signal. GSC export shows no clicks or impressions yet."
    if note:
        text += " " + note
    return "KEEP", text


def prepare_row(raw):
    handle = (raw.get("handle") or wc.handle_from_url(raw.get("url") or "")).lower()
    url = raw.get("url") or (wc.article_url(handle) if handle else "")
    computed_scope = scope_for(url, handle)
    # Landing listicles and non-blog URLs stay report-only even if a caller
    # passed scope=blog.
    if computed_scope == REPORT_ONLY:
        scope = REPORT_ONLY
    else:
        scope = raw.get("scope") or computed_scope
    cluster = raw.get("cluster") or ""
    title = (raw.get("title") or "").strip()
    if scope == "blog" and not cluster:
        cluster = wc.assign_cluster(((title + " " + handle.replace("-", " ")).strip()))
    words = raw.get("words")
    if words is not None:
        try:
            words = int(words)
        except (TypeError, ValueError):
            words = None
        if words is not None and words <= 0 and raw.get("words_source") == "cluster_map":
            words = None
    row = {
        "handle": handle,
        "url": url,
        "title": title,
        "cluster": cluster or "other",
        "cluster_label": raw.get("cluster_label") or cluster_label(cluster or "other"),
        "is_pillar": bool(raw.get("is_pillar")),
        "words": words if words is None or words > 0 or raw.get("words_source") not in {"", "cluster_map", None} else words,
        "words_source": raw.get("words_source") or "",
        "published": parse_date(raw.get("published")),
        "updated": parse_date(raw.get("updated")),
        "updated_source": raw.get("updated_source") or "",
        "primary_query": (raw.get("primary_query") or "").strip(),
        "primary_query_source": raw.get("primary_query_source") or "",
        "inbound": raw.get("inbound") if isinstance(raw.get("inbound"), int) else raw.get("inbound"),
        "outbound": raw.get("outbound"),
        "body_seen": bool(raw.get("body_seen")),
        "body_tokens": raw.get("body_tokens"),
        "bodies_complete": bool(raw.get("bodies_complete")),
        "http_status": raw.get("http_status"),
        "final_url": raw.get("final_url") or "",
        "redirect_handle": raw.get("redirect_handle") or "",
        "frozen": bool(raw.get("frozen")),
        "scope": scope,
        "gsc_state": raw.get("gsc_state") or "",
        "gsc_clicks": raw.get("gsc_clicks"),
        "gsc_impressions": raw.get("gsc_impressions"),
        "gsc_position": raw.get("gsc_position"),
        "gsc_note": raw.get("gsc_note") or "",
        "merge_into": "",
        "overlap_edge": "",
        "consolidate": False,
        "is_group_winner": False,
        "group_losers": [],
        "near_pairs": [],
    }
    if row["words"] == 0 and row["words_source"] in {"", "cluster_map"}:
        row["words"] = None
    row["segment_ids"] = segment_ids(title) if scope == "blog" else frozenset()
    row["content_tokens"] = content_tokens(title, row["cluster"]) if scope == "blog" else frozenset()
    if row["primary_query"] and row["primary_query_source"] in {"tracker", "gsc"}:
        row["query_key"] = query_key(row["primary_query"])
    else:
        row["query_key"] = tuple()
    if not row["updated"] and row["published"]:
        row["updated"] = row["published"]
        if not row["updated_source"]:
            row["updated_source"] = "published"
    return row


def apply_missing_gsc(rows):
    for row in rows:
        if row.get("gsc_state") == "measured":
            continue
        row["gsc_state"] = "missing"
        row["gsc_clicks"] = NEEDS_GSC
        row["gsc_impressions"] = NEEDS_GSC
        row["gsc_position"] = NEEDS_GSC
        row["gsc_note"] = NEEDS_GSC


def apply_gsc(rows, gsc_rows):
    pages, queries = wc.aggregate_gsc(gsc_rows)
    for row in rows:
        if row.get("scope") != "blog":
            continue
        row["gsc_state"] = "measured"
        stat = pages.get(row["handle"])
        if not stat:
            row["gsc_clicks"] = 0
            row["gsc_impressions"] = 0
            row["gsc_position"] = None
            row["gsc_note"] = "no row in export"
        else:
            row["gsc_clicks"] = stat.get("clicks") or 0
            row["gsc_impressions"] = stat.get("impressions") or 0
            row["gsc_position"] = stat.get("position")
            row["gsc_note"] = "export"
        if row.get("primary_query_source") == "tracker" and row.get("primary_query"):
            row["query_key"] = query_key(row["primary_query"])
            continue
        top = wc._top_queries(row["handle"], queries, limit=1)
        if top and not row.get("primary_query"):
            row["primary_query"] = top[0]["query"]
            row["primary_query_source"] = "gsc"
            row["query_key"] = query_key(row["primary_query"])


def ensure_primary_queries(rows):
    for row in rows:
        if row.get("scope") != "blog":
            continue
        if row.get("primary_query"):
            continue
        row["primary_query"] = title_as_query(row.get("title") or row.get("handle") or "")
        row["primary_query_source"] = "title"


def ensure_pillars(rows):
    by = defaultdict(list)
    for row in rows:
        if row.get("scope") == "blog":
            by[row["cluster"]].append(row)
    for members in by.values():
        if any(member.get("is_pillar") for member in members):
            continue
        live = [m for m in members if not m.get("frozen")]
        if not live:
            continue
        def score(member):
            return wc.pillar_score({
                "handle": member.get("handle"),
                "title": member.get("title"),
                "words": member.get("words") or 0,
                "impressions": member.get("gsc_impressions") if gsc_measured(member) else 0,
                "clicks": member.get("gsc_clicks") if gsc_measured(member) else 0,
                "position": member.get("gsc_position") if gsc_measured(member) else None,
                "stale_only": False,
            })
        best = max(live, key=lambda member: (score(member), len(member.get("title") or ""), member.get("handle") or ""))
        best["is_pillar"] = True
        best["pillar_source"] = "scored"


def recompute_inbound(rows):
    if not any("outbound" in row and row.get("outbound") is not None for row in rows):
        return
    inbound = defaultdict(set)
    for row in rows:
        outbound = row.get("outbound") or []
        for handle in outbound:
            if handle and handle != row.get("handle"):
                inbound[handle].add(row.get("handle"))
    blog = [row for row in rows if row.get("scope") == "blog"]
    complete = bool(blog) and all(row.get("body_seen") for row in blog)
    for row in rows:
        if row.get("scope") != "blog":
            continue
        row["inbound"] = len(inbound.get(row.get("handle"), ()))
        row["bodies_complete"] = complete


def audit_rows(raw_rows, today, gsc_rows=None, assign_pillars=True):
    rows = [prepare_row(raw) for raw in raw_rows]
    if gsc_rows is not None:
        apply_gsc(rows, gsc_rows)
    apply_missing_gsc(rows)
    ensure_primary_queries(rows)
    if assign_pillars:
        ensure_pillars(rows)
    recompute_inbound(rows)
    sizes = Counter(row["cluster"] for row in rows if row.get("scope") == "blog")
    handles = {row["handle"] for row in rows if row.get("handle")}
    assign_overlap(rows)
    for row in rows:
        action, reason = decide(row, today, sizes.get(row.get("cluster"), 0), handles)
        row["suggested_action"] = action
        row["reason"] = re.sub(r"\s+", " ", reason).strip()
        row["duplicate_siblings"] = sibling_text(row)
        row["cluster_size"] = sizes.get(row.get("cluster"), 0)
    return rows


def blank_gsc_cells(row):
    if row.get("gsc_state") == "measured":
        pos = row.get("gsc_position")
        pos_text = "" if pos is None else pos
        return row.get("gsc_clicks"), row.get("gsc_impressions"), pos_text, row.get("gsc_note") or "export"
    return NEEDS_GSC, NEEDS_GSC, NEEDS_GSC, NEEDS_GSC


def sheet_row(row):
    clicks, imps, pos, note = blank_gsc_cells(row)
    updated = row.get("updated") or row.get("published")
    inbound = row.get("inbound")
    return {
        "url": row.get("url") or "",
        "title": row.get("title") or "",
        "cluster": row.get("cluster") or "",
        "primary_query": row.get("primary_query") or "",
        "primary_query_source": row.get("primary_query_source") or "",
        "word_count": "" if row.get("words") is None else row.get("words"),
        "word_count_source": row.get("words_source") or "",
        "last_updated": updated.isoformat() if updated else "",
        "last_updated_source": row.get("updated_source") or "",
        "internal_links_in": NOT_MEASURED if not isinstance(inbound, int) else inbound,
        "duplicate_siblings": row.get("duplicate_siblings") or "",
        "suggested_action": row.get("suggested_action") or "",
        "merge_into": row.get("merge_into") or "",
        "reason": row.get("reason") or "",
        "gsc_clicks": clicks,
        "gsc_impressions": imps,
        "gsc_position": pos,
        "gsc_note": note,
    }


def action_counts(rows):
    counts = Counter(row.get("suggested_action") for row in rows)
    return {name: counts.get(name, 0) for name in list(ACTIONS) + [REPORT_ONLY]}


def _md_cell(value):
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def render_csv(rows):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    ordered = sorted(rows, key=_sheet_sort)
    for row in ordered:
        writer.writerow(sheet_row(row))
    return buf.getvalue()


def _sheet_sort(row):
    action = row.get("suggested_action") or ""
    order = {name: i for i, name in enumerate(list(ACTIONS) + [REPORT_ONLY])}
    return (order.get(action, 9), row.get("cluster") or "", row.get("handle") or "")


def _consolidate_rank(row):
    serial = 1 if "menomate serial" in (row.get("overlap_edge") or "") else 0
    score = 0.0
    match = re.search(r"(\d+\.\d+)", row.get("overlap_edge") or "")
    if match:
        score = float(match.group(1))
    words = row.get("words") if isinstance(row.get("words"), int) else 10 ** 9
    return (serial, -score, words, row.get("handle") or "")


def top_rows(rows, action, limit=10):
    picked = [row for row in rows if row.get("suggested_action") == action]
    if action == "CONSOLIDATE":
        picked.sort(key=_consolidate_rank)
    elif action == "PRUNE":
        picked.sort(key=lambda row: (row.get("words") if isinstance(row.get("words"), int) else 10 ** 9, row.get("handle") or ""))
    return picked[:limit]


def render_markdown(rows, meta):
    counts = action_counts(rows)
    lines = [
        "# Quarterly content audit %s" % (meta.get("day") or ""),
        "",
        "Read-only proposal sheet for published `wellnessnest.co` news articles. "
        "No Shopify write, redirect, unpublish, or theme edit was made.",
        "",
        "Rules: `docs/quarterly-content-audit.md`.",
        "",
        "## Counts",
        "",
        "| Action | Articles |",
        "| --- | ---: |",
    ]
    for name in list(ACTIONS) + [REPORT_ONLY]:
        lines.append("| %s | %s |" % (name, counts.get(name, 0)))
    lines.append("| Blog articles in the sheet | %s |" % sum(1 for row in rows if row.get("scope") == "blog"))
    lines.append("")
    lines.append("## Sources")
    lines.append("")
    for key, value in (meta.get("sources") or {}).items():
        lines.append("- %s: %s" % (key, value))
    if meta.get("bulk_lastmod_days"):
        lines.append(
            "- Sitemap lastmod days treated as a bulk touch (not an editorial update): %s"
            % ", ".join(meta.get("bulk_lastmod_days"))
        )
    if meta.get("crawl"):
        lines.append("- Public GETs: %s (cap %s)" % (meta["crawl"].get("gets"), meta["crawl"].get("max_gets")))
        if meta["crawl"].get("stopped"):
            lines.append("- Crawl stop: %s" % meta["crawl"]["stopped"])
    lines.append("")
    lines.append("## Owner decisions")
    lines.append("")
    for item in meta.get("decisions") or []:
        lines.append("- %s" % item)
    lines.append("")
    lines.append("## Top consolidate candidates")
    lines.append("")
    consolidates = top_rows(rows, "CONSOLIDATE", 10)
    if not consolidates:
        lines.append("None under the current rules.")
    for row in consolidates:
        lines.append("- `%s`" % (row.get("url") or ""))
        lines.append("  - %s" % _md_cell(row.get("title")))
        lines.append("  - cluster `%s`; merge into `%s`" % (row.get("cluster"), row.get("merge_into") or ""))
        lines.append("  - %s" % _md_cell(row.get("reason")))
    lines.append("")
    lines.append("## Top prune candidates")
    lines.append("")
    prunes = top_rows(rows, "PRUNE", 10)
    if not prunes:
        lines.append("None under the current rules.")
    for row in prunes:
        lines.append("- `%s`" % (row.get("url") or ""))
        lines.append("  - %s" % _md_cell(row.get("title")))
        lines.append("  - cluster `%s`; words %s" % (row.get("cluster"), row.get("words") if row.get("words") is not None else "unknown"))
        lines.append("  - %s" % _md_cell(row.get("reason")))
    lines.append("")
    report_only = [row for row in rows if row.get("suggested_action") == REPORT_ONLY]
    lines.append("## Report only")
    lines.append("")
    if not report_only:
        lines.append("No non-blog URLs were in the article catalog. Home, collections, products, checkout, and landing listicles were not crawled.")
    else:
        for row in report_only:
            lines.append("- `%s` — %s" % (row.get("url") or row.get("handle") or "", _md_cell(row.get("reason"))))
    lines.append("")
    lines.append("## Decision sheet")
    lines.append("")
    header = CSV_FIELDS
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    for row in sorted(rows, key=_sheet_sort):
        sheet = sheet_row(row)
        lines.append("| " + " | ".join(_md_cell(sheet[field]) for field in header) + " |")
    lines.append("")
    return "\n".join(lines)


def articles_from_markdown(text):
    """Titles and URLs from docs/CLUSTER_MAP.md. Impression figures in the prose are ignored."""
    out = []
    seen = set()
    for part in MAP_SECTION.split(text or ""):
        id_match = MAP_ID.search(part)
        if not id_match:
            continue
        cid = id_match.group(1)
        pillar_zone = False
        # Links that sit on the Pillar: line are the pillar. Later bullet links are spokes.
        pillar_handles = set()
        for line in part.splitlines():
            if PILLAR_LINE.match(line):
                pillar_zone = True
            elif line.startswith("Spokes:") or line.startswith("Gaps:") or line.startswith("- "):
                pillar_zone = False
            for match in MAP_LINK.finditer(line):
                title, url, handle, words = match.group(1), match.group(2), match.group(3), match.group(4)
                if handle in seen and handle not in pillar_handles:
                    if pillar_zone:
                        for row in out:
                            if row["handle"] == handle:
                                row["is_pillar"] = True
                    continue
                seen.add(handle)
                is_pillar = bool(pillar_zone)
                if is_pillar:
                    pillar_handles.add(handle)
                word_count = int(words) if words and int(words) > 0 else None
                out.append({
                    "handle": handle,
                    "title": html_lib.unescape(title).strip(),
                    "url": url,
                    "cluster": cid,
                    "is_pillar": is_pillar,
                    "words": word_count,
                    "words_source": "cluster_map" if word_count else "",
                    "scope": "blog",
                })
    return out


def articles_from_cluster_json(cluster_map):
    out = []
    for cluster in (cluster_map or {}).get("clusters") or []:
        cid = cluster.get("id") or "other"
        members = []
        pillar = cluster.get("pillar")
        if pillar:
            members.append((pillar, True))
        for spoke in cluster.get("spokes") or []:
            members.append((spoke, False))
        for member, is_pillar in members:
            handle = (member.get("handle") or "").lower()
            if not handle:
                continue
            words = member.get("words") or 0
            out.append({
                "handle": handle,
                "title": (member.get("title") or "").strip(),
                "url": member.get("url") or wc.article_url(handle),
                "cluster": cid,
                "is_pillar": is_pillar,
                "words": words if words > 0 else None,
                "words_source": "cluster_map" if words and words > 0 else "",
                "scope": "blog",
            })
    return out


def _upsert(by, row):
    handle = (row.get("handle") or "").lower()
    if not handle:
        return
    cur = by.get(handle)
    if not cur:
        by[handle] = dict(row, handle=handle)
        return
    if row.get("title") and (not cur.get("title") or (cur.get("title_from_keyword") and len(row["title"]) > len(cur.get("title") or ""))):
        cur["title"] = row["title"]
        cur["title_from_keyword"] = False
    if row.get("cluster") and (not cur.get("cluster") or cur.get("cluster") == "other"):
        cur["cluster"] = row["cluster"]
    if row.get("is_pillar"):
        cur["is_pillar"] = True
    if row.get("words") and not cur.get("words"):
        cur["words"] = row["words"]
        cur["words_source"] = row.get("words_source") or cur.get("words_source") or ""
    if row.get("url"):
        cur["url"] = row["url"]
    if row.get("primary_query") and not cur.get("primary_query"):
        cur["primary_query"] = row["primary_query"]
        cur["primary_query_source"] = row.get("primary_query_source") or ""
    if row.get("published") and not cur.get("published"):
        cur["published"] = row["published"]
        if row.get("published_source"):
            cur["published_source"] = row["published_source"]
    for key in ("updated", "updated_source", "body_text", "body_seen", "outbound", "http_status", "final_url", "redirect_handle", "words_source"):
        if row.get(key) and not cur.get(key):
            cur[key] = row[key]


def load_tracker_rows(path):
    out = []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            url = (row.get("Article Link") or row.get("url") or "").strip()
            article_handle = wc.handle_from_url(url)
            if not article_handle:
                continue
            keyword = (row.get("Keyword") or "").strip()
            out.append({
                "handle": article_handle,
                "title": keyword,
                "title_from_keyword": True,
                "url": url,
                "primary_query": keyword,
                "primary_query_source": "tracker",
                "published": parse_date(row.get("Posted Date") or ""),
                "published_source": "tracker" if parse_date(row.get("Posted Date") or "") else "",
                "updated_source": "tracker" if parse_date(row.get("Posted Date") or "") else "",
                "scope": "blog",
            })
    return out


def load_local(root, map_md="", map_json="", tracker="", csv_path="", json_path=""):
    """Merge the committed cluster map with whatever local caches exist."""
    root = root or ROOT
    sources = {}
    by = {}
    map_md = map_md or os.path.join(root, "docs", "CLUSTER_MAP.md")
    map_json = map_json or os.path.join(root, "state", "cluster_map.json")
    tracker = tracker or os.path.join(root, "PUBLISHED_ARTICLES_TRACKER.csv")
    csv_path = csv_path or os.path.join(root, "ALL_ARTICLES.csv")
    json_path = json_path or os.path.join(root, "existing_articles.json")
    if map_json and os.path.isfile(map_json):
        with open(map_json, encoding="utf-8") as handle:
            data = json.load(handle)
        for row in articles_from_cluster_json(data):
            _upsert(by, row)
        sources["cluster_map_json"] = map_json
    if map_md and os.path.isfile(map_md):
        with open(map_md, encoding="utf-8") as handle:
            text = handle.read()
        for row in articles_from_markdown(text):
            _upsert(by, row)
        sources["cluster_map_md"] = map_md
    if json_path and os.path.isfile(json_path):
        for row in wc.load_json_articles(json_path):
            words = row.get("words") or 0
            _upsert(by, {
                "handle": row["handle"],
                "title": row.get("title") or "",
                "url": row.get("url") or "",
                "words": words if words > 0 else None,
                "words_source": "existing_articles" if words > 0 else "",
                "published": row.get("created") or "",
                "scope": "blog",
            })
        sources["articles_json"] = json_path
    if csv_path and os.path.isfile(csv_path):
        for row in wc.load_csv_articles(csv_path):
            if row.get("blog") not in ("news", wc.BLOG_ID, "104008483131", "", None):
                continue
            words = row.get("words") or 0
            _upsert(by, {
                "handle": row["handle"],
                "title": row.get("title") or "",
                "url": row.get("url") or "",
                "words": words if words > 0 else None,
                "words_source": "all_articles_csv" if words > 0 else "",
                "published": row.get("created") or "",
                "scope": "blog",
            })
        sources["articles_csv"] = csv_path
    if tracker and os.path.isfile(tracker):
        for row in load_tracker_rows(tracker):
            _upsert(by, row)
        sources["tracker"] = tracker
    frozen = set()
    frozen_path = os.path.join(root, "frozen_articles.txt")
    if os.path.isfile(frozen_path):
        with open(frozen_path, encoding="utf-8") as handle:
            frozen = {line.split("#", 1)[0].strip() for line in handle if line.split("#", 1)[0].strip()}
        sources["frozen"] = frozen_path
    rows = []
    for handle, row in sorted(by.items()):
        row["handle"] = handle
        if not row.get("url"):
            row["url"] = wc.article_url(handle)
        if not row.get("scope"):
            row["scope"] = scope_for(row["url"], handle)
        if handle in frozen or str(row.get("id") or "") in frozen:
            row["frozen"] = True
        rows.append(row)
    return rows, sources


def xml_text_nodes(text, local_name):
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    values = []
    for el in root.iter():
        if el.tag.split("}")[-1] == local_name and el.text:
            values.append(html_lib.unescape(el.text.strip()))
    return values


def english_article_sitemaps(index_xml):
    out = []
    for loc in xml_text_nodes(index_xml, "loc"):
        if ARTICLE_SITEMAP_RX.fullmatch(loc):
            out.append(loc)
    return out


def parse_article_sitemap(text):
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    rows = []
    for el in root.iter():
        if el.tag.split("}")[-1] != "url":
            continue
        loc, lastmod, title = "", "", ""
        for child in list(el):
            tag = child.tag.split("}")[-1]
            if tag == "loc" and child.text:
                loc = html_lib.unescape(child.text.strip())
            elif tag == "lastmod" and child.text:
                lastmod = child.text.strip()
            elif tag == "title" and child.text and not title:
                title = html_lib.unescape(child.text.strip())
        if not loc:
            continue
        handle = wc.handle_from_url(loc)
        scope = scope_for(loc, handle)
        rows.append({
            "handle": handle,
            "url": loc,
            "title": title,
            "sitemap_lastmod": lastmod,
            "scope": scope,
        })
    return rows


def parse_atom(text):
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    entries = []
    for el in root.iter():
        if el.tag.split("}")[-1] != "entry":
            continue
        title = published = updated = content = link = ""
        for child in list(el):
            tag = child.tag.split("}")[-1]
            if tag == "title" and child.text:
                title = html_lib.unescape(child.text.strip())
            elif tag == "published" and child.text:
                published = child.text.strip()
            elif tag == "updated" and child.text:
                updated = child.text.strip()
            elif tag == "content" and child.text:
                content = child.text
            elif tag == "link":
                href = child.attrib.get("href") or ""
                if "/blogs/news/" in href:
                    link = href
        handle = wc.handle_from_url(link)
        if not handle:
            continue
        entries.append({
            "handle": handle,
            "url": link,
            "title": title,
            "published": published,
            "updated": updated,
            "content": content,
        })
    return entries


def meta_content(page, prop):
    for match in META_RX.finditer(page or ""):
        tag = match.group(0)
        if prop.lower() not in tag.lower():
            continue
        content = CONTENT_RX.search(tag)
        if content:
            return html_lib.unescape(content.group(1)).strip()
    return ""


def html_to_text(fragment):
    cleaned = re.sub(r"(?is)<(script|style|noscript)\b[^>]*>.*?</\1>", " ", fragment or "")
    cleaned = re.sub(r"(?is)<[^>]+>", " ", cleaned)
    cleaned = html_lib.unescape(cleaned).replace("\xa0", " ")
    return cleaned


def count_words(text):
    return len(re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", text or ""))


def main_content_fragment(page):
    """Legacy GemPages articles have no articleBody. Use the theme main landmark."""
    start = re.search(r"""id=["']MainContent["']""", page or "", re.I)
    if not start:
        return ""
    footer = re.search(r"<footer\b", page[start.end():], re.I)
    end = start.end() + footer.start() if footer else len(page)
    return page[start.end():end]


def extract_fragment(page):
    """Return the article body HTML, or '' when the page has no article body."""
    if not page:
        return ""
    body = re.search(r"""itemprop=["']articleBody["'][^>]*>""", page, re.I)
    start = None
    if body:
        start = body.end()
    else:
        article = re.search(r"<article\b[^>]*>", page, re.I)
        if article:
            start = article.end()
    if start is None:
        # Atom content is a fragment with no article wrapper.
        if "<html" not in page.lower() and "<p" in page.lower():
            return page
        return main_content_fragment(page)
    end = len(page)
    for marker in ("article-template__social-sharing", "</article>"):
        pos = page.lower().find(marker.lower(), start)
        if pos != -1:
            end = min(end, pos)
    return page[start:end]


def outbound_handles(fragment, self_handle=""):
    found = []
    seen = set()
    for handle in HREF_RX.findall(fragment or ""):
        handle = handle.lower()
        if handle == (self_handle or "").lower() or handle in seen:
            continue
        if not wc.safe_handle(handle) and not wc.HANDLE_RX.fullmatch(handle):
            continue
        seen.add(handle)
        found.append(handle)
    return found


def jsonld_date(page, key):
    match = re.search(r'"%s"\s*:\s*"(\d{4}-\d{2}-\d{2})' % re.escape(key), page or "")
    return match.group(1) if match else ""


def extract_article_fields(page, self_handle=""):
    fragment = extract_fragment(page)
    text = html_to_text(fragment) if fragment else ""
    published = ""
    time_match = TIME_RX.search(page or "")
    if time_match:
        published = time_match.group(1)
    if not published:
        published = jsonld_date(page, "datePublished")
    words = count_words(text) if fragment else None
    return {
        "title": meta_content(page, "og:title"),
        "published": published,
        "words": words,
        "body_text": text,
        "outbound": outbound_handles(fragment, self_handle),
        "body_seen": fragment != "",
    }


def bulk_lastmod_days(dates, today, share=BULK_LASTMOD_SHARE):
    """A lastmod day shared by a large slice of the sitemap is a regeneration, not an edit."""
    counted = [day for day in dates if day]
    if not counted:
        return set()
    counts = Counter(counted)
    limit = max(1, int(len(counted) * share))
    bulk = set()
    for day, count in counts.items():
        if count < limit:
            continue
        if today and abs((day - today).days) <= 3:
            bulk.add(day)
    return bulk


def apply_sitemap_rows(rows, sitemap_rows, today):
    by = {row["handle"]: row for row in rows if row.get("handle")}
    lastmods = []
    for item in sitemap_rows:
        day = parse_date(item.get("sitemap_lastmod"))
        if day and item.get("scope") == "blog":
            lastmods.append(day)
    bulk = bulk_lastmod_days(lastmods, today)
    report_only = []
    for item in sitemap_rows:
        if item.get("scope") != "blog":
            report_only.append({
                "url": item.get("url") or "",
                "title": item.get("title") or "",
                "handle": item.get("handle") or "",
                "scope": REPORT_ONLY,
            })
            continue
        handle = item.get("handle") or ""
        row = by.get(handle)
        if not row:
            row = {
                "handle": handle,
                "url": item.get("url") or wc.article_url(handle),
                "title": item.get("title") or "",
                "scope": "blog",
            }
            rows.append(row)
            by[handle] = row
        elif item.get("title") and not row.get("title"):
            row["title"] = item["title"]
        lastmod = parse_date(item.get("sitemap_lastmod"))
        row["sitemap_lastmod"] = lastmod
        if lastmod and lastmod not in bulk:
            current = parse_date(row.get("updated"))
            if not current or lastmod > current:
                row["updated"] = lastmod
                row["updated_source"] = "sitemap_lastmod"
        if not row.get("published") and lastmod and lastmod not in bulk:
            row["published"] = lastmod
            row["published_source"] = "sitemap_lastmod"
            row["updated_source"] = row.get("updated_source") or "sitemap_lastmod"
    return bulk, report_only


def apply_body(row, fields, source):
    if fields.get("title") and (not row.get("title") or row.get("title_from_keyword")):
        row["title"] = fields["title"]
        row["title_from_keyword"] = False
    published = parse_date(fields.get("published"))
    if published and (not row.get("published") or row.get("published_source") in {"", "sitemap_lastmod", "tracker", None}):
        row["published"] = published
        row["published_source"] = source
    current_updated = parse_date(row.get("updated"))
    if published and (not current_updated or row.get("updated_source") in {"", "tracker", "published", None}):
        row["updated"] = published
        row["updated_source"] = source
    elif published and current_updated and published > current_updated and row.get("updated_source") == "sitemap_lastmod":
        # The sitemap clock is behind the visible publish time.
        row["updated"] = published
        row["updated_source"] = source
    if fields.get("words") is not None:
        row["words"] = fields["words"]
        row["words_source"] = source
    if fields.get("body_text"):
        row["body_tokens"] = body_signature(fields["body_text"])
    row["outbound"] = fields.get("outbound") or []
    row["body_seen"] = bool(fields.get("body_seen"))


class PoliteClient:
    """Sequential public GETs with a cap, a delay, and backoff on HTTP 429."""

    def __init__(self, max_gets=MAX_GETS_DEFAULT, delay=0.4, sleep=None, opener=None):
        self.max_gets = max_gets
        self.delay = delay
        self.sleep = sleep or time.sleep
        self.opener = opener
        self.gets = 0
        self.stopped = ""
        self._gap = delay

    def get(self, url):
        if self.stopped:
            return None
        attempt = 0
        while attempt < 3:
            if self.gets >= self.max_gets:
                self.stopped = "max gets %s" % self.max_gets
                return None
            if self.gets:
                self.sleep(self._gap)
            self.gets += 1
            attempt += 1
            status, body, final_url, headers = self._read(url)
            if status == 429:
                retry = headers.get("Retry-After") if headers else None
                try:
                    wait = float(retry)
                except (TypeError, ValueError):
                    wait = min(60.0, 5.0 * (2 ** (attempt - 1)))
                self._gap = max(self._gap, wait)
                self.sleep(wait)
                continue
            if status in (502, 503) and attempt < 3:
                self._gap = min(30.0, max(self._gap, self.delay) * 2)
                continue
            self._gap = self.delay
            return {"status": status, "body": body, "final_url": final_url or url, "headers": headers or {}}
        self.stopped = "backoff exhausted after HTTP 429"
        return None

    def _read(self, url):
        if self.opener:
            return self.opener(url)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                charset = resp.headers.get_content_charset() or "utf-8"
                return resp.status, raw.decode(charset, "replace"), resp.geturl(), dict(resp.headers)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace") if exc.fp else ""
            return exc.code, body, url, dict(exc.headers or {})
        except OSError:
            return 0, "", url, {}


def crawl_public(rows, client, today):
    """Fill titles, dates, word counts, and in-body links from the public blog.

    Only the English article sitemap, the news Atom feed, and /blogs/news/
    article URLs are requested. Locale, product, collection, and page sitemaps
    are not fetched.
    """
    meta = {"gets": 0, "max_gets": client.max_gets, "stopped": "", "atom": 0, "html": 0, "sitemap_urls": 0}
    index = client.get(SITE + "/sitemap.xml")
    if not index or index["status"] != 200:
        meta["stopped"] = client.stopped or "sitemap index unavailable"
        meta["gets"] = client.gets
        return [], meta
    sitemap_locs = english_article_sitemaps(index["body"])
    parsed = []
    for loc in sitemap_locs:
        payload = client.get(loc)
        if not payload or payload["status"] != 200:
            break
        parsed.extend(parse_article_sitemap(payload["body"]))
    bulk, report_only = apply_sitemap_rows(rows, parsed, today)
    meta["sitemap_urls"] = len(parsed)
    meta["bulk_lastmod_days"] = sorted(day.isoformat() for day in bulk)
    atom = client.get(SITE + "/blogs/news.atom")
    atom_handles = set()
    if atom and atom["status"] == 200:
        for entry in parse_atom(atom["body"]):
            atom_handles.add(entry["handle"])
            fields = extract_article_fields(entry.get("content") or "", entry["handle"])
            if entry.get("published"):
                fields["published"] = entry["published"]
            if entry.get("title") and not fields.get("title"):
                fields["title"] = entry["title"]
            row = next((item for item in rows if item.get("handle") == entry["handle"]), None)
            if row is None:
                row = {"handle": entry["handle"], "url": entry["url"], "title": entry.get("title") or "", "scope": "blog"}
                rows.append(row)
            elif entry.get("title"):
                fields["title"] = fields.get("title") or entry["title"]
            apply_body(row, fields, "atom")
            meta["atom"] += 1
    for row in list(rows):
        if client.stopped:
            break
        if row.get("scope") != "blog":
            continue
        if row.get("body_seen") and isinstance(row.get("words"), int):
            continue
        url = row.get("url") or wc.article_url(row["handle"])
        if "/blogs/news/" not in url:
            continue
        payload = client.get(url)
        if payload is None:
            break
        meta["html"] += 1
        if meta["html"] % 15 == 0:
            print("crawl html %s gets %s" % (meta["html"], client.gets), flush=True)
        row["http_status"] = payload["status"]
        final = payload.get("final_url") or url
        row["final_url"] = final
        final_handle = wc.handle_from_url(final)
        if payload["status"] == 200 and final_handle and final_handle != row.get("handle"):
            row["redirect_handle"] = final_handle
        if payload["status"] == 200 and scope_for(final, final_handle) == "blog":
            fields = extract_article_fields(payload["body"], row.get("handle") or "")
            apply_body(row, fields, "html")
        elif payload["status"] in (404, 410):
            row["body_seen"] = True
            row["outbound"] = []
    meta["gets"] = client.gets
    meta["stopped"] = client.stopped
    return report_only, meta


def owner_decisions(rows, meta):
    items = [
        "Every CONSOLIDATE or PRUNE row waits for Kevin. This file is a proposal.",
        "REFRESH on a ranking URL stays append-only and keeps the current title until a CTR diagnosis says otherwise.",
        "A redirect is added only after the loser is unpublished. A URL that still returns 200 is not 301'd.",
        "Home, collections, product pages, checkout, and ad landing listicles are out of scope.",
    ]
    if not meta.get("gsc"):
        items.append(
            "No GSC export was loaded. Traffic cells say needs GSC data. Re-run with --gsc on the Mac vault file before approving a prune that Search Console might reverse."
        )
    menopause = [row for row in rows if row.get("cluster") == "menopause" and row.get("scope") == "blog"]
    if menopause:
        items.append(
            "MenoMate is not on sale. Serial journey and meal-plan posts are consolidate proposals into the stronger archive URL. Distinct menopause explainers are judged on their own rows. Retiring the whole archive is a separate owner decision."
        )
    serial = [
        row for row in rows
        if row.get("scope") == "blog" and "menomate serial" in (row.get("overlap_edge") or "")
    ]
    if serial:
        winner = next((row for row in rows if row.get("url") == serial[0].get("merge_into")), None)
        measured = [row for row in serial + ([winner] if winner else []) if isinstance(row.get("words"), int)]
        if winner and measured:
            longest = max(measured, key=lambda row: row.get("words") or 0)
            if longest.get("handle") != winner.get("handle"):
                items.append(
                    "The menopause serial survivor is the cluster-map pillar %s (%s words). %s is longer (%s words). Confirm the surviving URL before any merge."
                    % (winner.get("handle"), winner.get("words"), longest.get("handle"), longest.get("words"))
                )
    missing_words = sum(1 for row in rows if row.get("scope") == "blog" and row.get("words") is None)
    if missing_words:
        items.append("%s blog rows have no measured word count. Those rows are not pruned for length." % missing_words)
    if meta.get("bulk_lastmod_days"):
        items.append(
            "Sitemap lastmod on %s is treated as a bulk touch, so staleness uses the article publish time when one was read."
            % ", ".join(meta["bulk_lastmod_days"])
        )
    return items


def build_audit(raw_rows, today, gsc_rows=None, assign_pillars=True, meta=None):
    rows = audit_rows(raw_rows, today, gsc_rows=gsc_rows, assign_pillars=assign_pillars)
    info = dict(meta or {})
    info["day"] = today.isoformat()
    info.setdefault("sources", {})
    info["gsc"] = bool(gsc_rows is not None)
    info["decisions"] = owner_decisions(rows, info)
    return rows, info


def write_outputs(rows, meta, out_md, out_csv):
    os.makedirs(os.path.dirname(os.path.abspath(out_md)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(out_csv)), exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as handle:
        handle.write(render_markdown(rows, meta))
    with open(out_csv, "w", encoding="utf-8", newline="") as handle:
        handle.write(render_csv(rows))


def self_check():
    today = dt.date(2026, 10, 20)
    strong = {
        "handle": "nmn-dosage-guide",
        "title": "NMN Dosage: How Much NMN Per Day",
        "url": wc.article_url("nmn-dosage-guide"),
        "cluster": "ageaura-nmn",
        "is_pillar": True,
        "words": 1900,
        "published": "2026-09-01",
        "scope": "blog",
        "body_seen": True,
        "inbound": 3,
    }
    weak = {
        "handle": "how-much-nmn-per-day",
        "title": "How Much NMN Per Day: What Trials Used",
        "url": wc.article_url("how-much-nmn-per-day"),
        "cluster": "ageaura-nmn",
        "is_pillar": False,
        "words": 1600,
        "published": "2026-09-02",
        "scope": "blog",
        "body_seen": True,
        "inbound": 1,
    }
    rows = audit_rows([strong, weak], today, assign_pillars=False)
    by = {row["handle"]: row for row in rows}
    if by["how-much-nmn-per-day"]["suggested_action"] != "CONSOLIDATE":
        raise SystemExit("self-check: dosage pair should consolidate")
    if by["nmn-dosage-guide"]["suggested_action"] not in {"KEEP", "REFRESH"}:
        raise SystemExit("self-check: stronger dosage page should stay")
    product = audit_rows([{"url": SITE + "/products/example", "title": "Example", "handle": "example"}], today, assign_pillars=False)
    if product[0]["suggested_action"] != REPORT_ONLY:
        raise SystemExit("self-check: product URL must be report only")
    if product[0]["gsc_clicks"] != NEEDS_GSC:
        raise SystemExit("self-check: missing GSC must be labelled")
    print("quarterly content audit self-check: ok")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only quarterly news-blog content audit.")
    parser.add_argument("--root", default=ROOT)
    parser.add_argument("--map-md", default="")
    parser.add_argument("--map-json", default="")
    parser.add_argument("--tracker", default="")
    parser.add_argument("--csv", default="")
    parser.add_argument("--json", default="")
    parser.add_argument("--gsc", default="", help="real GSC csv; omit to label traffic cells needs GSC data")
    parser.add_argument("--crawl", action="store_true", help="polite public GETs of blog URLs only")
    parser.add_argument("--max-gets", type=int, default=MAX_GETS_DEFAULT)
    parser.add_argument("--delay", type=float, default=0.4)
    parser.add_argument("--day", default="", help="audit date YYYY-MM-DD (default: today ICT)")
    parser.add_argument("--out-md", default="")
    parser.add_argument("--out-csv", default="")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    if args.day:
        today = parse_date(args.day)
        if not today:
            raise SystemExit("--day must be YYYY-MM-DD")
    else:
        today = wc.now_ict().date()
    raw, sources = load_local(
        args.root,
        map_md=args.map_md,
        map_json=args.map_json,
        tracker=args.tracker,
        csv_path=args.csv,
        json_path=args.json,
    )
    meta = {"sources": sources, "crawl": None, "bulk_lastmod_days": []}
    if args.crawl:
        client = PoliteClient(max_gets=args.max_gets, delay=args.delay)
        report_only, crawl_meta = crawl_public(raw, client, today)
        meta["crawl"] = crawl_meta
        meta["bulk_lastmod_days"] = crawl_meta.get("bulk_lastmod_days") or []
        meta["sources"]["public_crawl"] = "wellnessnest.co blog sitemap, atom, article HTML; GETs %s" % crawl_meta.get("gets")
        for item in report_only:
            raw.append(item)
    gsc_rows = None
    if args.gsc:
        if not os.path.isfile(args.gsc):
            raise SystemExit("GSC file not found: %s" % args.gsc)
        gsc_rows = wc.read_gsc_csv(args.gsc)
        meta["sources"]["gsc"] = args.gsc
    else:
        meta["sources"]["gsc"] = NEEDS_GSC
    if not any(scope_for(row.get("url") or "", row.get("handle") or "") == "blog" or row.get("scope") == "blog" for row in raw):
        raise SystemExit("no blog articles in the local catalog")
    rows, info = build_audit(raw, today, gsc_rows=gsc_rows, assign_pillars=True, meta=meta)
    day = today.isoformat()
    out_md = args.out_md or os.path.join(args.root, "reports", "quarterly-content-audit-%s.md" % day)
    out_csv = args.out_csv or os.path.join(args.root, "reports", "quarterly-content-audit-%s.csv" % day)
    write_outputs(rows, info, out_md, out_csv)
    counts = action_counts(rows)
    print(
        "quarterly audit %s blog=%s KEEP=%s REFRESH=%s CONSOLIDATE=%s PRUNE=%s report_only=%s"
        % (
            day,
            sum(1 for row in rows if row.get("scope") == "blog"),
            counts["KEEP"],
            counts["REFRESH"],
            counts["CONSOLIDATE"],
            counts["PRUNE"],
            counts[REPORT_ONLY],
        )
    )
    print("md %s" % out_md)
    print("csv %s" % out_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

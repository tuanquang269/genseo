#!/usr/bin/env python3
"""Weekly AI referrer report for wellnessnest.co.

Counts sessions and orders by referrer domain. Does not count by UTM.
Read-only: ShopifyQL via Admin GraphQL, or an orders referrer URL read.
Never mutates the shop, never edits a page or theme, never requests a new scope.

  python3 scripts/ai_referrer_report.py
  python3 scripts/ai_referrer_report.py --since 2026-10-14 --until 2026-10-20
  python3 scripts/ai_referrer_report.py --csv export.csv --csv-complete
  python3 scripts/ai_referrer_report.py --template

Missing numbers stay "unknown". A domain that a finished ShopifyQL group-by
did not return is 0. A truncated group-by is unknown, not a partial total.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

STORE_LABEL = "wellnessnest.co"
API_VERSION = os.environ.get("SHOPIFY_API_VERSION", "2026-04")
BUG_WINDOW_START = date(2026, 10, 15)
BUG_WINDOW_END = date(2026, 10, 20)
SEL_URL = (
    "https://searchengineland.com/chatgpt-appears-to-drop-utm-tracking-"
    "making-ai-referral-traffic-harder-to-measure-496552"
)
SEL_NOTE = (
    "Search Engine Land reported on 2026-10-15 that ChatGPT links may have "
    "dropped utm_source=chatgpt.com and may suppress the HTTP referrer, so "
    "some visits show up as direct. OpenAI has not confirmed it."
)
SCOPE_NEEDED = "needs scope read_reports"
ROW_LIMIT = 1000
SOURCE_LIMIT = 50
ORDER_PAGE = 50
ORDER_CAP = 2000

# Parent hosts. A subdomain counts (www is stripped first). x.com does not
# count as Grok. google.com does not count as Gemini. openai.com does not
# count as ChatGPT.
CANONICAL = (
    ("ChatGPT", ("chatgpt.com", "chat.openai.com")),
    ("Perplexity", ("perplexity.ai",)),
    ("Gemini", ("gemini.google.com", "bard.google.com")),
    ("Copilot", ("copilot.microsoft.com",)),
    ("Claude", ("claude.ai",)),
    ("Grok", ("grok.com", "x.ai")),
)
EXTRA = (
    ("You.com", ("you.com",)),
    ("Phind", ("phind.com",)),
    ("Meta AI", ("meta.ai",)),
    ("Poe", ("poe.com",)),
    ("DeepSeek", ("deepseek.com", "chat.deepseek.com")),
)
ENGINE_DOMAINS = {name: domains for name, domains in CANONICAL + EXTRA}
CANONICAL_NAMES = [name for name, _domains in CANONICAL]

BLANK_TOKENS = {
    "",
    "-",
    "none",
    "null",
    "direct",
    "(direct)",
    "not set",
    "(not set)",
    "n/a",
    "na",
}

DOMAIN_HEADERS = {
    "referrer_domain",
    "session_referrer_domain",
    "order_referrer_domain",
    "referring_domain",
    "referrer_host",
}
SESSION_HEADERS = {"sessions", "session", "online_store_sessions"}
ORDER_HEADERS = {"orders", "num_orders", "order_count"}
DAY_HEADERS = {"day", "date"}
UTM_HEADERS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
    "order_utm_source",
}

SHOPIFYQL_GQL = """query ShopifyQLRead($q: String!) {
  shopifyqlQuery(query: $q) {
    parseErrors
    tableData { columns { name dataType } rows }
  }
}"""

ORDERS_GQL = """query AiReferrerOrders($cursor: String, $search: String!) {
  orders(first: %d, after: $cursor, query: $search, sortKey: CREATED_AT) {
    pageInfo { hasNextPage endCursor }
    nodes {
      customerJourneySummary { lastVisit { referrerUrl } }
    }
  }
}""" % ORDER_PAGE

_TOKEN_RE = re.compile(r"shpat_[A-Za-z0-9]+|shpca_[A-Za-z0-9]+|shpss_[A-Za-z0-9]+")


class ReportError(Exception):
    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


def redact(text):
    return _TOKEN_RE.sub("[redacted]", text or "")


def normalize_header(value):
    return re.sub(r"[^a-z0-9]+", "_", (value or "").strip().lower()).strip("_")


def parse_int(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float):
        if value < 0 or value != int(value):
            return None
        return int(value)
    text = str(value).strip().replace(",", "")
    if text.lower() in {"", "null", "none", "unknown", "n/a", "na"}:
        return None
    if re.fullmatch(r"\d+", text):
        return int(text)
    if re.fullmatch(r"\d+\.0+", text):
        return int(text.split(".", 1)[0])
    return None


def parse_day(value):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def normalize_host(value):
    if value is None or isinstance(value, bool):
        return None
    if not isinstance(value, str):
        value = str(value)
    raw = value.strip().lower()
    if raw in BLANK_TOKENS:
        return None
    if "://" in raw:
        host = urllib.parse.urlparse(raw).hostname
    else:
        raw = raw.split("/")[0].split("?")[0].split("#")[0]
        if raw.count(":") == 1 and raw.rsplit(":", 1)[1].isdigit():
            raw = raw.split(":", 1)[0]
        host = raw
    if not host:
        return None
    host = host.strip(".").lower()
    if host.startswith("www."):
        host = host[4:]
    if host in BLANK_TOKENS or not host:
        return None
    return host


def engine_for_host(host):
    if not host:
        return None
    for name, domains in CANONICAL + EXTRA:
        for domain in domains:
            if host == domain or host.endswith("." + domain):
                return name
    return None


def overlaps_bug_window(since, until):
    return not (until < BUG_WINDOW_START or since > BUG_WINDOW_END)


def bug_overlap_phrase(since, until):
    if not overlaps_bug_window(since, until):
        return "This report does not overlap that window."
    start = max(since, BUG_WINDOW_START)
    end = min(until, BUG_WINDOW_END)
    return "This report overlaps that window (%s through %s)." % (
        start.isoformat(),
        end.isoformat(),
    )


def default_window(today):
    until = today - timedelta(days=1)
    since = until - timedelta(days=6)
    return since, until


def sessions_by_domain_ql(since, until, limit=ROW_LIMIT):
    return (
        "FROM sessions\n"
        "  SHOW sessions\n"
        "  GROUP BY referrer_domain\n"
        "  SINCE %s UNTIL %s\n"
        "  ORDER BY sessions DESC\n"
        "  LIMIT %d" % (since.isoformat(), until.isoformat(), int(limit))
    )


def orders_by_domain_ql(since, until, limit=ROW_LIMIT):
    return (
        "FROM sales\n"
        "  SHOW orders\n"
        "  GROUP BY order_referrer_domain\n"
        "  SINCE %s UNTIL %s\n"
        "  ORDER BY orders DESC\n"
        "  LIMIT %d" % (since.isoformat(), until.isoformat(), int(limit))
    )


def direct_sessions_ql(since, until):
    return (
        "FROM sessions\n"
        "  SHOW sessions\n"
        "  GROUP BY referrer_source\n"
        "  SINCE %s UNTIL %s\n"
        "  LIMIT %d" % (since.isoformat(), until.isoformat(), SOURCE_LIMIT)
    )


def direct_orders_ql(since, until):
    return (
        "FROM sales\n"
        "  SHOW orders\n"
        "  GROUP BY order_referrer_source\n"
        "  SINCE %s UNTIL %s\n"
        "  LIMIT %d" % (since.isoformat(), until.isoformat(), SOURCE_LIMIT)
    )


def utm_chatgpt_sessions_ql(since, until):
    return (
        "FROM sessions\n"
        "  SHOW sessions\n"
        "  WHERE utm_source CONTAINS 'chatgpt'\n"
        "  GROUP BY utm_source\n"
        "  SINCE %s UNTIL %s\n"
        "  LIMIT %d" % (since.isoformat(), until.isoformat(), SOURCE_LIMIT)
    )


def cell(value):
    if value is None:
        return "unknown"
    return str(value)


def _add(current, number):
    if number is None or current is None:
        return None
    return current + number


def index_domains(rows, domain_field, metric_field):
    """Map normalized host -> count. Blank referrer is returned separately.

    A metric cell that does not parse makes that host unknown (None).
    """
    if rows is None:
        return None, None, False
    hosts = {}
    blank = 0
    saw_blank = False
    blank_bad = False
    for row in rows:
        number = parse_int(row.get(metric_field))
        host = normalize_host(row.get(domain_field))
        if host is None:
            saw_blank = True
            if number is None:
                blank_bad = True
            else:
                blank += number
            continue
        if host not in hosts:
            hosts[host] = number
        else:
            hosts[host] = _add(hosts[host], number)
    if blank_bad:
        blank = None
    return hosts, blank, saw_blank


def allocate(hosts, mode):
    """Roll hosts into engines.

    mode complete: a missing engine is 0.
    mode partial: only engines present in hosts get a number; others stay unknown.
    mode unknown: every engine and the other-domain total are unknown.
    """
    engines = {name: None for name in CANONICAL_NAMES}
    extra = {}
    if mode == "unknown" or hosts is None:
        return engines, extra, None
    if mode == "complete":
        engines = {name: 0 for name in CANONICAL_NAMES}
        seen = {name: True for name in CANONICAL_NAMES}
        other = 0
        other_set = True
    else:
        seen = {name: False for name in CANONICAL_NAMES}
        other = None
        other_set = False
    for host, number in hosts.items():
        engine = engine_for_host(host)
        if engine is None:
            if not other_set:
                other = number
                other_set = True
            else:
                other = _add(other, number)
            continue
        if engine in engines:
            if not seen[engine]:
                engines[engine] = number
                seen[engine] = True
            else:
                engines[engine] = _add(engines[engine], number)
        elif engine not in extra:
            extra[engine] = number
        else:
            extra[engine] = _add(extra[engine], number)
    return engines, extra, other


def blank_metric(saw_blank, blank_value, mode):
    if mode == "unknown":
        return None
    if saw_blank:
        return blank_value
    if mode == "complete":
        return 0
    return None


def sum_metrics(values):
    if any(value is None for value in values):
        return None
    return sum(values)


def _extra_value(mapping, name, mode):
    if name in mapping:
        return mapping[name]
    if mode == "complete":
        return 0
    return None


def _show_extra(sessions, orders):
    if sessions is None or orders is None:
        return True
    return sessions > 0 or orders > 0


def engine_rows(session_engines, order_engines, session_extra, order_extra, sessions_mode, orders_mode):
    rows = []
    for name in CANONICAL_NAMES:
        rows.append({
            "name": name,
            "domains": ", ".join(ENGINE_DOMAINS[name]),
            "sessions": session_engines.get(name),
            "orders": order_engines.get(name),
            "extra": False,
        })
    extra_names = []
    for name, _domains in EXTRA:
        if name in session_extra or name in order_extra:
            extra_names.append(name)
    for name in list(session_extra) + list(order_extra):
        if name not in extra_names:
            extra_names.append(name)
    for name in extra_names:
        sessions = _extra_value(session_extra, name, sessions_mode)
        orders = _extra_value(order_extra, name, orders_mode)
        if not _show_extra(sessions, orders):
            continue
        rows.append({
            "name": name,
            "domains": ", ".join(ENGINE_DOMAINS.get(name, ())),
            "sessions": sessions,
            "orders": orders,
            "extra": True,
        })
    return rows


def pick_label(rows, field, metric, label, complete):
    if rows is None or not complete:
        return None
    total = 0
    found = False
    for row in rows:
        raw = row.get(field)
        if raw is None or str(raw).strip().lower() != label:
            continue
        found = True
        number = parse_int(row.get(metric))
        if number is None:
            return None
        total += number
    if not found:
        return 0
    return total


def utm_diagnostic(rows, complete):
    """Return (chatgpt.com sessions, other utm rows). Not an engine count."""
    if rows is None or not complete:
        return None, []
    exact = 0
    found = False
    others = []
    for row in rows:
        raw = row.get("utm_source")
        if raw is None:
            continue
        number = parse_int(row.get("sessions"))
        if str(raw).strip().lower() == "chatgpt.com":
            found = True
            if number is None:
                return None, others
            exact += number
        elif number is not None:
            others.append((str(raw), number))
    if not found:
        exact = 0
    return exact, others


def build_report(
    since,
    until,
    session_rows,
    order_rows,
    sessions_mode,
    orders_mode,
    direct_session_rows,
    direct_sessions_complete,
    direct_order_rows,
    direct_orders_complete,
    utm_rows,
    utm_complete,
    source,
    token_source,
    shop,
    queried_at,
    notes,
    scope_message=None,
):
    s_hosts, s_blank, s_saw = index_domains(session_rows, "referrer_domain", "sessions")
    o_hosts, o_blank, o_saw = index_domains(order_rows, "order_referrer_domain", "orders")
    s_engines, s_extra, s_other = allocate(s_hosts, sessions_mode)
    o_engines, o_extra, o_other = allocate(o_hosts, orders_mode)
    rows = engine_rows(
        s_engines, o_engines, s_extra, o_extra, sessions_mode, orders_mode
    )
    utm_exact, utm_other = utm_diagnostic(utm_rows, utm_complete)
    return {
        "since": since,
        "until": until,
        "queried_at": queried_at,
        "source": source,
        "token_source": token_source,
        "shop": shop,
        "sessions_mode": sessions_mode,
        "orders_mode": orders_mode,
        "engines": rows,
        "ai_sessions": sum_metrics([row["sessions"] for row in rows]),
        "ai_orders": sum_metrics([row["orders"] for row in rows]),
        "blank_sessions": blank_metric(s_saw, s_blank, sessions_mode),
        "blank_orders": blank_metric(o_saw, o_blank, orders_mode),
        "other_sessions": s_other,
        "other_orders": o_other,
        "direct_sessions": pick_label(
            direct_session_rows, "referrer_source", "sessions", "direct", direct_sessions_complete
        ),
        "direct_orders": pick_label(
            direct_order_rows, "order_referrer_source", "orders", "direct", direct_orders_complete
        ),
        "utm_chatgpt_sessions": utm_exact,
        "utm_other": utm_other,
        "notes": list(notes),
        "scope_message": scope_message,
    }


def render_report(report):
    since = report["since"].isoformat()
    until = report["until"].isoformat()
    lines = [
        "# Weekly AI referrer report — %s" % STORE_LABEL,
        "",
        "- Period: %s through %s" % (since, until),
        "- Counted by: referrer domain. Not counted by UTM.",
        "- Sessions field: ShopifyQL `sessions.referrer_domain`.",
        "- Orders field: ShopifyQL `sales.order_referrer_domain` (the sessions schema on API %s has no orders column)." % API_VERSION,
        "- Queried at: %s" % report["queried_at"],
        "- Source: %s" % report["source"],
    ]
    if report.get("token_source"):
        lines.append("- Credential source: %s. No new scope was requested." % report["token_source"])
    if report.get("shop"):
        lines.append("- Admin shop: %s" % report["shop"])
    lines.append("- Shop timezone: ShopifyQL applies the shop timezone to SINCE and UNTIL.")
    if report.get("scope_message"):
        lines.extend(["", report["scope_message"]])
    lines.extend([
        "",
        "## Possible ChatGPT UTM-bug window",
        "",
        "Flagged window: %s through %s." % (
            BUG_WINDOW_START.isoformat(),
            BUG_WINDOW_END.isoformat(),
        ),
        SEL_NOTE,
        "Article: %s" % SEL_URL,
        bug_overlap_phrase(report["since"], report["until"]),
        "The ChatGPT row is the referrer-domain count only. It is not a UTM count.",
        "A lower domain count inside the flagged window is not evidence that ChatGPT traffic stopped.",
        "Blank referrer domains and direct sessions are not relabeled as ChatGPT.",
        "This report does not estimate a correction for the UTM-bug window.",
        "Missing data is unknown.",
        "",
        "Diagnostic, not a count: sessions with utm_source=chatgpt.com in this period: %s." % cell(
            report.get("utm_chatgpt_sessions")
        ),
        "Those sessions are not included in the ChatGPT row.",
    ])
    for label, number in report.get("utm_other") or []:
        lines.append(
            "Other utm_source value containing chatgpt (not counted): %s = %s." % (label, number)
        )
    lines.extend([
        "",
        "## Sessions and orders by AI referrer domain",
        "",
        "Subdomains of the listed hosts count. www is ignored. x.com is not Grok. google.com is not Gemini. openai.com is not ChatGPT.",
        "Sessions and orders are separate queries. Do not read the pair as a conversion rate.",
        "",
        "| Engine | Domains counted | Sessions | Orders |",
        "| --- | --- | --- | --- |",
    ])
    for row in report["engines"]:
        lines.append("| %s | %s | %s | %s |" % (
            row["name"], row["domains"], cell(row["sessions"]), cell(row["orders"])
        ))
    lines.extend([
        "",
        "AI total (engine rows only): sessions %s, orders %s." % (
            cell(report["ai_sessions"]), cell(report["ai_orders"])
        ),
        "",
        "## Not an AI referrer",
        "",
        "Blank referrer domain, referrer_source = direct, and other domains are different ShopifyQL cuts. Do not add them together.",
        "",
        "| Bucket | Sessions | Orders |",
        "| --- | --- | --- |",
        "| Blank referrer domain | %s | %s |" % (
            cell(report["blank_sessions"]), cell(report["blank_orders"])
        ),
        "| referrer_source = direct | %s | %s |" % (
            cell(report["direct_sessions"]), cell(report["direct_orders"])
        ),
        "| Other referrer domains | %s | %s |" % (
            cell(report["other_sessions"]), cell(report["other_orders"])
        ),
        "",
    ])
    if report.get("notes"):
        lines.append("## Notes")
        lines.append("")
        for note in report["notes"]:
            lines.append("- %s" % note)
        lines.append("")
    lines.append(
        "CSV import, when ShopifyQL is unavailable: `python3 scripts/ai_referrer_report.py --csv export.csv --csv-complete --since %s --until %s`."
        % (since, until)
    )
    lines.append("")
    return "\n".join(lines)


def template_report(today=None):
    today = today or date(2026, 10, 21)
    since, until = default_window(today)
    return build_report(
        since=since,
        until=until,
        session_rows=None,
        order_rows=None,
        sessions_mode="unknown",
        orders_mode="unknown",
        direct_session_rows=None,
        direct_sessions_complete=False,
        direct_order_rows=None,
        direct_orders_complete=False,
        utm_rows=None,
        utm_complete=False,
        source="template — not a store read",
        token_source="",
        shop="",
        queried_at="not run",
        notes=[
            "Template only. Every number is unknown until a ShopifyQL read or a CSV import fills it.",
            "Do not replace unknown with a guess.",
        ],
    )


def _pick_header(fieldnames, choices):
    for name in fieldnames:
        if normalize_header(name) in choices:
            return name
    return None


def load_csv_text(text, since, until):
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ReportError("CSV has no header row.")
    headers = [normalize_header(name) for name in reader.fieldnames]
    domain_name = _pick_header(reader.fieldnames, DOMAIN_HEADERS)
    if domain_name is None:
        if any(name in UTM_HEADERS for name in headers):
            raise ReportError(
                "This file has UTM columns and no referrer domain. This report does not count by UTM."
            )
        raise ReportError("CSV needs a referrer domain column. This report does not count by UTM.")
    session_name = _pick_header(reader.fieldnames, SESSION_HEADERS)
    order_name = _pick_header(reader.fieldnames, ORDER_HEADERS)
    if session_name is None and order_name is None:
        raise ReportError("CSV needs a sessions or orders column.")
    day_name = _pick_header(reader.fieldnames, DAY_HEADERS)
    session_rows = []
    order_rows = []
    for raw in reader:
        if raw is None:
            continue
        if day_name:
            raw_day = raw.get(day_name)
            if not str(raw_day or "").strip():
                raise ReportError("CSV day column has a blank date. The file was not imported.")
            day = parse_day(raw_day)
            if day is None:
                raise ReportError("CSV day column has an unreadable date. The file was not imported.")
            if day < since or day > until:
                continue
        host_value = raw.get(domain_name)
        if session_name is not None:
            session_rows.append({
                "referrer_domain": host_value,
                "sessions": raw.get(session_name),
            })
        if order_name is not None:
            order_rows.append({
                "order_referrer_domain": host_value,
                "orders": raw.get(order_name),
            })
    return session_rows, order_rows, session_name is not None, order_name is not None


def report_from_csv(text, since, until, complete, queried_at, path_label):
    session_rows, order_rows, has_sessions, has_orders = load_csv_text(text, since, until)
    mode = "complete" if complete else "partial"
    sessions_mode = mode if has_sessions else "unknown"
    orders_mode = mode if has_orders else "unknown"
    if not has_sessions:
        session_rows = None
    if not has_orders:
        order_rows = None
    note = (
        "CSV import from %s. Omitted engines count as 0."
        % path_label
        if complete
        else "CSV import from %s. Omitted engines stay unknown. Pass --csv-complete when the file is the full domain export."
        % path_label
    )
    return build_report(
        since=since,
        until=until,
        session_rows=session_rows,
        order_rows=order_rows,
        sessions_mode=sessions_mode,
        orders_mode=orders_mode,
        direct_session_rows=None,
        direct_sessions_complete=False,
        direct_order_rows=None,
        direct_orders_complete=False,
        utm_rows=None,
        utm_complete=False,
        source="CSV import. Shopify was not called.",
        token_source="",
        shop="",
        queried_at=queried_at,
        notes=[note, "Direct referrer_source is unknown on CSV import."],
    )


def referrer_value(record):
    """Referrer URL only. landing_site / landingPage is the on-site landing URL."""
    if not isinstance(record, dict):
        return None
    for key in ("referring_site", "referringSite", "referrer_url", "referrerUrl"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value
    summary = record.get("customerJourneySummary") or {}
    if not isinstance(summary, dict):
        return None
    visit = summary.get("lastVisit") or {}
    if not isinstance(visit, dict):
        return None
    value = visit.get("referrerUrl")
    if isinstance(value, str) and value.strip():
        return value
    return None


def orders_from_records(records):
    """One order per record, counted by referring host. Returns aggregate rows."""
    hosts = {}
    blank = 0
    for record in records:
        host = normalize_host(referrer_value(record))
        if host is None:
            blank += 1
            continue
        hosts[host] = hosts.get(host, 0) + 1
    rows = [{"order_referrer_domain": host, "orders": count} for host, count in hosts.items()]
    if blank:
        rows.append({"order_referrer_domain": None, "orders": blank})
    return rows


def _rows_from_table(table):
    columns = [col.get("name") for col in (table.get("columns") or [])]
    rows = []
    for row in table.get("rows") or []:
        if isinstance(row, dict):
            rows.append(row)
        elif isinstance(row, list):
            rows.append(dict(zip(columns, row)))
        else:
            raise ReportError("Unexpected ShopifyQL row.")
    return rows


def _scope_text(text):
    blob = (text or "").lower()
    markers = ("access denied", "read_reports", "not authorized", "required access", "forbidden")
    return any(marker in blob for marker in markers)


class HTTPQuerier:
    """Read-only Admin GraphQL. The documents are queries, never mutations."""

    def __init__(self, shop, token, opener=None, api_version=None):
        self.shop = shop
        self.token = token
        self.opener = opener or urllib.request.urlopen
        self.api_version = api_version or API_VERSION

    def graphql(self, document, variables):
        stripped = document.lstrip()
        if not stripped.startswith("query"):
            raise ReportError("Refusing a GraphQL document that is not a query.")
        if re.search(r"\bmutation\b", document):
            raise ReportError("Refusing a GraphQL mutation.")
        url = "https://%s/admin/api/%s/graphql.json" % (self.shop, self.api_version)
        payload = json.dumps({"query": document, "variables": variables}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "X-Shopify-Access-Token": self.token,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with self.opener(req, timeout=60) as res:
                status = getattr(res, "status", 200)
                body = res.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            status = exc.code
            return self._http_failure(status, body)
        except urllib.error.URLError as exc:
            return {"ok": False, "rows": [], "needs_scope": False, "error": redact(str(exc.reason))}
        if status in (401, 403):
            return self._http_failure(status, body)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return {"ok": False, "rows": [], "needs_scope": False, "error": "Shopify returned non-JSON."}
        return data

    def _http_failure(self, status, body):
        message = "Shopify HTTP %s. %s" % (status, SCOPE_NEEDED)
        detail = redact(body)[:300]
        if detail:
            message = "%s %s" % (message, detail)
        return {
            "ok": False,
            "rows": [],
            "needs_scope": True,
            "error": message,
            "top": True,
        }

    def shopifyql(self, statement):
        data = self.graphql(SHOPIFYQL_GQL, {"q": statement})
        if data.get("top") or data.get("ok") is False:
            return data
        errors = data.get("errors") or []
        if errors:
            text = "; ".join(redact(err.get("message") or str(err)) for err in errors)
            return {
                "ok": False,
                "rows": [],
                "needs_scope": _scope_text(text),
                "error": text,
            }
        node = (data.get("data") or {}).get("shopifyqlQuery")
        if not node:
            return {"ok": False, "rows": [], "needs_scope": False, "error": "shopifyqlQuery returned nothing."}
        parse_errors = node.get("parseErrors") or []
        if parse_errors:
            text = "; ".join(redact(str(item)) for item in parse_errors)
            return {
                "ok": False,
                "rows": [],
                "needs_scope": _scope_text(text),
                "error": text,
            }
        table = node.get("tableData") or {}
        try:
            rows = _rows_from_table(table)
        except ReportError as exc:
            return {"ok": False, "rows": [], "needs_scope": False, "error": str(exc)}
        return {"ok": True, "rows": rows, "needs_scope": False, "error": ""}

    def order_records(self, since, until):
        end = until + timedelta(days=1)
        search = "created_at:>=%s created_at:<%s" % (since.isoformat(), end.isoformat())
        cursor = None
        records = []
        while True:
            data = self.graphql(ORDERS_GQL, {"cursor": cursor, "search": search})
            if data.get("top") or data.get("ok") is False or data.get("errors"):
                text = data.get("error") or "; ".join(
                    err.get("message") or str(err) for err in (data.get("errors") or [])
                )
                return {
                    "ok": False,
                    "rows": [],
                    "truncated": False,
                    "needs_scope": _scope_text(text) or bool(data.get("needs_scope")),
                    "error": redact(text),
                }
            orders = ((data.get("data") or {}).get("orders") or {})
            nodes = orders.get("nodes") or []
            records.extend(nodes)
            page = orders.get("pageInfo") or {}
            if len(records) > ORDER_CAP:
                return {
                    "ok": False,
                    "rows": [],
                    "truncated": True,
                    "needs_scope": False,
                    "error": "Order referrer read exceeded %d orders. Orders are unknown." % ORDER_CAP,
                }
            if not page.get("hasNextPage"):
                break
            cursor = page.get("endCursor")
            if not cursor:
                break
        return {"ok": True, "rows": records, "truncated": False, "needs_scope": False, "error": ""}


def _mode_from_result(result, limit):
    if not result.get("ok"):
        return "unknown", None, result
    rows = result.get("rows") or []
    if limit and len(rows) >= limit:
        failed = dict(result)
        failed["error"] = "Query returned %d rows, the limit of %d. Counts for that query are unknown." % (
            len(rows), limit
        )
        return "unknown", None, failed
    return "complete", rows, result


def fetch_shopify_report(since, until, querier, shop, token_source, queried_at, limit=ROW_LIMIT):
    notes = []
    scope_bits = []
    sessions = querier.shopifyql(sessions_by_domain_ql(since, until, limit))
    orders = querier.shopifyql(orders_by_domain_ql(since, until, limit))
    direct_sessions = querier.shopifyql(direct_sessions_ql(since, until))
    direct_orders = querier.shopifyql(direct_orders_ql(since, until))
    utm = querier.shopifyql(utm_chatgpt_sessions_ql(since, until))

    s_mode, s_rows, s_meta = _mode_from_result(sessions, limit)
    o_mode, o_rows, o_meta = _mode_from_result(orders, limit)
    if s_meta.get("needs_scope"):
        scope_bits.append(s_meta.get("error") or SCOPE_NEEDED)
    if s_meta.get("error") and s_mode != "complete":
        err = s_meta["error"]
        if s_meta.get("needs_scope") and SCOPE_NEEDED not in err:
            err = SCOPE_NEEDED + ". " + err
        notes.append("Sessions: %s" % err)
    if (
        not orders.get("ok")
        and not orders.get("needs_scope")
        and hasattr(querier, "order_records")
    ):
        fallback = querier.order_records(since, until)
        if fallback.get("ok") and not fallback.get("truncated"):
            o_rows = orders_from_records(fallback.get("rows") or [])
            o_mode = "complete"
            notes.append(
                "Orders were counted from order referrer URLs (referring_site / referrerUrl). landing_site was not used. ShopifyQL sales query: %s"
                % (o_meta.get("error") or "unavailable")
            )
        else:
            if o_meta.get("error"):
                notes.append("Orders: %s" % o_meta["error"])
            if fallback.get("error"):
                err = fallback["error"]
                if fallback.get("needs_scope") and SCOPE_NEEDED not in err and "needs scope read_orders" not in err:
                    err = "needs scope read_orders. " + err
                notes.append("Order referrer URL read: %s" % err)
            if fallback.get("needs_scope"):
                scope_bits.append(fallback.get("error") or "needs scope read_orders")
            o_mode, o_rows = "unknown", None
    elif o_meta.get("error") and o_mode != "complete":
        err = o_meta["error"]
        if o_meta.get("needs_scope") and SCOPE_NEEDED not in err:
            err = SCOPE_NEEDED + ". " + err
        notes.append("Orders: %s" % err)
    if o_meta.get("needs_scope") and o_mode != "complete":
        scope_bits.append(o_meta.get("error") or SCOPE_NEEDED)

    ds_mode, ds_rows, ds_meta = _mode_from_result(direct_sessions, SOURCE_LIMIT)
    do_mode, do_rows, do_meta = _mode_from_result(direct_orders, SOURCE_LIMIT)
    utm_mode, utm_rows, utm_meta = _mode_from_result(utm, SOURCE_LIMIT)
    for label, meta, mode in (
        ("Direct sessions", ds_meta, ds_mode),
        ("Direct orders", do_meta, do_mode),
        ("UTM diagnostic", utm_meta, utm_mode),
    ):
        if meta.get("error") and mode != "complete":
            notes.append("%s: %s" % (label, meta["error"]))

    both_failed = s_mode != "complete" and o_mode != "complete"
    scope_message = SCOPE_NEEDED if both_failed and scope_bits else None
    return build_report(
        since=since,
        until=until,
        session_rows=s_rows,
        order_rows=o_rows,
        sessions_mode=s_mode,
        orders_mode=o_mode,
        direct_session_rows=ds_rows,
        direct_sessions_complete=ds_mode == "complete",
        direct_order_rows=do_rows,
        direct_orders_complete=do_mode == "complete",
        utm_rows=utm_rows,
        utm_complete=utm_mode == "complete",
        source="ShopifyQL read via Admin GraphQL shopifyqlQuery. No Shopify write.",
        token_source=token_source,
        shop=shop,
        queried_at=queried_at,
        notes=notes,
        scope_message=scope_message,
    ), both_failed


def load_credentials():
    try:
        import shopify_auth
        shop, token, source = shopify_auth.pick({"read_reports"})
    except SystemExit as exc:
        raise ReportError("No Shopify token loaded (%s)." % exc)
    if not shop or not token:
        raise ReportError("No Shopify token loaded.")
    return shop, token, source


def _parse_date(value, flag):
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ReportError("%s must be YYYY-MM-DD." % flag)


def _write(text, out_path):
    if not out_path or out_path == "-":
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
        return
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def main(argv=None, querier_factory=None, today=None, now=None):
    parser = argparse.ArgumentParser(description="Weekly AI referrer report by domain, not by UTM.")
    parser.add_argument("--since", help="Inclusive start date YYYY-MM-DD. Default: 7 complete days ending yesterday.")
    parser.add_argument("--until", help="Inclusive end date YYYY-MM-DD.")
    parser.add_argument("--csv", help="Shopify Analytics export with a referrer domain column.")
    parser.add_argument(
        "--csv-complete",
        action="store_true",
        help="The CSV lists every referrer domain. Omitted engines count as 0. Without this flag they stay unknown.",
    )
    parser.add_argument("--template", action="store_true", help="Print the report template. No network.")
    parser.add_argument("--out", default="-", help="Output path. Default stdout.")
    parser.add_argument("--limit", type=int, default=ROW_LIMIT, help="ShopifyQL row limit. Hitting it makes that metric unknown.")
    args = parser.parse_args(argv)
    clock = now or datetime.now(timezone.utc)
    queried_at = clock.replace(microsecond=0).isoformat()
    if args.template:
        text = render_report(template_report(today or date(2026, 10, 21)))
        _write(text, args.out)
        return 0
    day = today or clock.date()
    since = _parse_date(args.since, "--since") if args.since else default_window(day)[0]
    until = _parse_date(args.until, "--until") if args.until else default_window(day)[1]
    if since > until:
        raise ReportError("--since is after --until.")
    if args.csv:
        with open(args.csv, encoding="utf-8-sig") as handle:
            text_csv = handle.read()
        report = report_from_csv(text_csv, since, until, args.csv_complete, queried_at, args.csv)
        _write(render_report(report), args.out)
        return 0
    if querier_factory is not None:
        querier = querier_factory()
        shop, token_source = "test-shop.myshopify.com", "test"
    else:
        shop, token, token_source = load_credentials()
        querier = HTTPQuerier(shop, token)
    report, both_failed = fetch_shopify_report(
        since, until, querier, shop, token_source, queried_at, limit=args.limit
    )
    _write(render_report(report), args.out)
    if report.get("scope_message") and both_failed:
        sys.stderr.write(report["scope_message"] + "\n")
        sys.stderr.write(
            "This script does not request a new token or a new scope. "
            "Import a Shopify Analytics export with a referrer domain column: "
            "python3 scripts/ai_referrer_report.py --csv export.csv --csv-complete "
            "--since %s --until %s\n" % (since.isoformat(), until.isoformat())
        )
        return 2
    if both_failed:
        sys.stderr.write("Sessions and orders are unknown.\n")
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ReportError as exc:
        sys.stderr.write(str(exc) + "\n")
        if "does not count by UTM" in str(exc) or "referrer domain" in str(exc):
            sys.stderr.write(
                "Export the referrer domain column from Shopify Analytics, not the UTM columns.\n"
            )
        sys.exit(exc.code)

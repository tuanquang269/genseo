"""GEO traffic report for wellnessnest.co.

Prints direct sessions that land on a deep content page: Shopify referrer_source
is direct, referrer_url is empty, and every UTM field is empty. That line is a
proxy for AI-assistant clicks after referrer and UTM stripping. It is not
attributed AI traffic.

Source: ShopifyQL `sessions` through the Admin API (read-only). The same token
the rest of GenSeo uses. Search Console cannot split direct vs referral or
landing page, so this report does not read it.

  python3 scripts/geo_traffic_report.py
  python3 scripts/geo_traffic_report.py --since 2026-10-02 --until 2026-10-19

When a required field is missing, or a pull would be partial, the report prints
`data not available from shopifyql` and no session totals.
"""
import argparse
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request

from deep_content_pages import DEEP_CONTENT_PAGE, is_deep_content_page

SOURCE = "shopifyql"
SUSPECTED_UTM_DROP = datetime.date(2026, 10, 9)
ANNOTATION = (
    "2026-10-09 is the suspected date AI assistants stopped passing UTMs. "
    "Direct sessions on deep content pages are a proxy for those referrals, "
    "not attributed AI traffic."
)
SECTION = "Direct traffic to deep content pages (proxy, not attributed AI traffic)"
UTM_FIELDS = (
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
)
DIRECT_FIELDS = ("day", "landing_page_path", "sessions", "referrer_source", "referrer_url") + UTM_FIELDS
TOTAL_FIELDS = ("day", "sessions")
ROW_LIMIT = 10000
API_VERSION = os.environ.get("SHOPIFY_API_VERSION", "2026-04")
_TOKEN_RE = re.compile(r"shpat_[A-Za-z0-9]+")

DIRECT_QUERY = """
FROM sessions
SHOW sessions
WHERE referrer_source = 'direct'
  AND referrer_url IS NULL
  AND utm_source IS NULL
  AND utm_medium IS NULL
  AND utm_campaign IS NULL
  AND utm_term IS NULL
  AND utm_content IS NULL
GROUP BY day, landing_page_path, referrer_source, referrer_url, utm_source, utm_medium, utm_campaign, utm_term, utm_content
SINCE {since} UNTIL {until}
LIMIT {limit}
""".strip()

TOTAL_QUERY = """
FROM sessions
SHOW sessions
GROUP BY day
SINCE {since} UNTIL {until}
LIMIT {limit}
""".strip()


def data_not_available(detail):
    detail = " ".join(str(detail).split())
    detail = _TOKEN_RE.sub("[redacted]", detail)
    if detail:
        return f"data not available from {SOURCE}: {detail}"
    return f"data not available from {SOURCE}"


def _blank(value):
    return value is None or str(value).strip() == ""


def is_direct_no_referrer_no_utm(row):
    """True only when the row shows Shopify direct, no referrer URL, and no UTM.

    A missing key is not treated as empty. Callers check the column list first.
    """
    source = row["referrer_source"]
    if source is None or str(source).strip().lower() != "direct":
        return False
    if not _blank(row["referrer_url"]):
        return False
    for field in UTM_FIELDS:
        if not _blank(row[field]):
            return False
    return True


def parse_day(value):
    text = str(value).strip()
    if len(text) < 10:
        raise ValueError(f"bad day {value!r}")
    return datetime.date.fromisoformat(text[:10])


def parse_count(value):
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"bad sessions {value!r}")
    if isinstance(value, int):
        count = value
    elif isinstance(value, str) and value.strip().isdigit():
        count = int(value.strip())
    else:
        raise ValueError(f"bad sessions {value!r}")
    if count < 0:
        raise ValueError(f"bad sessions {value!r}")
    return count


def _missing(columns, required):
    have = set(columns or [])
    return [field for field in required if field not in have]


def _pct(part, whole):
    if not whole:
        return "n/a"
    return f"{(100.0 * part / whole):.1f}%"


def _day_count(count):
    return "1 day" if count == 1 else f"{count} days"


def _window_line(label, items):
    if not items:
        return f"{label}: no days in this pull"
    deep = sum(item["deep"] for item in items)
    total = sum(item["total"] for item in items)
    span = f"{items[0]['day'].isoformat()} .. {items[-1]['day'].isoformat()}"
    average = deep / len(items)
    return (
        f"{label} ({span}, {_day_count(len(items))}): "
        f"direct_deep {deep} / total {total} ({_pct(deep, total)}); "
        f"daily average {average:.1f} direct_deep sessions"
    )


def _note(day, today):
    notes = []
    if day == SUSPECTED_UTM_DROP:
        notes.append("suspected UTM drop")
    if today is not None and day == today:
        notes.append("day still in progress")
    return "; ".join(notes)


def render_report(direct_rows, total_rows, direct_columns, total_columns, since=None, until=None, truncated=False, today=None):
    """Text of the report. Numbers come only from the rows passed in.

    `today` is the calendar day still in progress. That day stays in the table
    with the count the source returned, and stays out of the before/after averages.
    """
    if truncated:
        return data_not_available(
            "the ShopifyQL pull hit its row limit, so the totals would be partial"
        )
    missing_direct = _missing(direct_columns, DIRECT_FIELDS)
    missing_total = _missing(total_columns, TOTAL_FIELDS)
    if missing_direct or missing_total:
        fields = ", ".join(missing_direct + missing_total)
        return data_not_available(f"missing field(s): {fields}")
    if not total_rows:
        return data_not_available("the sessions query returned no days")

    try:
        totals = {}
        for row in total_rows:
            day = parse_day(row["day"])
            totals[day] = totals.get(day, 0) + parse_count(row["sessions"])
        deep_by_day = {day: 0 for day in totals}
        for row in direct_rows:
            if not is_direct_no_referrer_no_utm(row):
                continue
            if not is_deep_content_page(row["landing_page_path"]):
                continue
            day = parse_day(row["day"])
            if day not in totals:
                return data_not_available(
                    f"direct rows include {day.isoformat()}, which is missing from the sessions total"
                )
            deep_by_day[day] += parse_count(row["sessions"])
    except (KeyError, ValueError) as exc:
        return data_not_available(exc)

    days = sorted(totals)
    items = []
    for day in days:
        deep = deep_by_day[day]
        total = totals[day]
        if deep > total:
            return data_not_available(
                f"direct_deep sessions exceed total sessions on {day.isoformat()}"
            )
        items.append({"day": day, "deep": deep, "total": total, "note": _note(day, today)})

    window = ""
    if since and until:
        window = f"Window requested: {since} .. {until}\n"
    lines = [
        "GEO traffic report",
        f"Source: {SOURCE} sessions (Shopify Admin API, read-only)",
        SECTION,
        f"Definition: {DEEP_CONTENT_PAGE['description']}",
        f"Annotation: {ANNOTATION}",
        window.rstrip(),
        "",
        "| date | direct_deep_sessions | total_sessions | share_of_total | note |",
        "|---|---:|---:|---:|---|",
    ]
    for item in items:
        lines.append(
            f"| {item['day'].isoformat()} | {item['deep']} | {item['total']} | "
            f"{_pct(item['deep'], item['total'])} | {item['note']} |"
        )
    complete = [item for item in items if today is None or item["day"] != today]
    before = [item for item in complete if item["day"] < SUSPECTED_UTM_DROP]
    after = [item for item in complete if item["day"] >= SUSPECTED_UTM_DROP]
    lines.append("")
    lines.append(_window_line("Before 2026-10-09", before))
    lines.append(_window_line("On and after 2026-10-09", after))
    if before and after:
        before_avg = sum(item["deep"] for item in before) / len(before)
        after_avg = sum(item["deep"] for item in after) / len(after)
        lines.append(
            "Daily-average change (on and after minus before): "
            f"{after_avg - before_avg:+.1f} direct_deep sessions"
        )
    for item in items:
        if today is not None and item["day"] == today:
            lines.append(
                f"{item['day'].isoformat()} is still in progress: "
                f"direct_deep {item['deep']} / total {item['total']} so far "
                f"({_pct(item['deep'], item['total'])}). "
                "Left out of the before/after averages."
            )
    return "\n".join(line for line in lines if line is not None).rstrip() + "\n"


def _config_path():
    return os.path.expanduser(os.environ.get("GENSEO_CONFIG", "~/.genseo/shopify_token.json"))


def _shopifyql(shop, token, query):
    body = json.dumps({
        "query": "query($q:String!){shopifyqlQuery(query:$q){parseErrors tableData{columns{name} rows}}}",
        "variables": {"q": query},
    }).encode()
    req = urllib.request.Request(
        f"https://{shop}/admin/api/{API_VERSION}/graphql.json",
        data=body,
        headers={
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as res:
        payload = json.load(res)
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"])[:500])
    data = (payload.get("data") or {}).get("shopifyqlQuery") or {}
    parse_errors = data.get("parseErrors") or []
    if parse_errors:
        raise RuntimeError("parse error: " + " ".join(str(item) for item in parse_errors)[:500])
    table = data.get("tableData") or {}
    columns = [col.get("name") for col in (table.get("columns") or [])]
    rows = table.get("rows") or []
    return columns, rows


def _split_range(since, until):
    if since >= until:
        return None
    mid = since + datetime.timedelta(days=(until - since).days // 2)
    right = mid + datetime.timedelta(days=1)
    if right > until or mid < since:
        return None
    return (since, mid), (right, until)


def _pull_range(shop, token, template, since, until, limit, depth=0):
    query = template.format(since=since.isoformat(), until=until.isoformat(), limit=limit)
    columns, rows = _shopifyql(shop, token, query)
    if len(rows) < limit:
        return columns, rows
    parts = _split_range(since, until)
    if parts is None or depth > 16:
        raise RuntimeError(
            f"ShopifyQL returned {limit} rows for {since.isoformat()} .. {until.isoformat()} "
            "and the range cannot be split, so the pull may be partial"
        )
    left_cols, left_rows = _pull_range(shop, token, template, parts[0][0], parts[0][1], limit, depth + 1)
    right_cols, right_rows = _pull_range(shop, token, template, parts[1][0], parts[1][1], limit, depth + 1)
    columns = left_cols or right_cols or columns
    return columns, left_rows + right_rows


def fetch_report(since, until, limit=ROW_LIMIT):
    path = _config_path()
    if not os.path.isfile(path):
        return data_not_available(f"shopify token file is not configured ({path})")
    with open(path) as handle:
        cfg = json.load(handle)
    shop = cfg.get("shop")
    token = cfg.get("access_token")
    if not shop or not token:
        return data_not_available("shopify token file has no shop or access token")
    try:
        direct_columns, direct_rows = _pull_range(shop, token, DIRECT_QUERY, since, until, limit)
        total_columns, total_rows = _pull_range(shop, token, TOTAL_QUERY, since, until, limit)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        return data_not_available(f"HTTP {exc.code} {detail}")
    except urllib.error.URLError as exc:
        return data_not_available(f"request failed: {exc.reason}")
    except (OSError, json.JSONDecodeError, RuntimeError, KeyError, TypeError, ValueError) as exc:
        return data_not_available(exc)
    return render_report(
        direct_rows,
        total_rows,
        direct_columns,
        total_columns,
        since=since.isoformat(),
        until=until.isoformat(),
        today=datetime.date.today(),
    )


def _date_arg(text):
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD, got {text}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="GEO traffic report: direct sessions on deep content pages")
    parser.add_argument("--since", type=_date_arg, default=datetime.date(2026, 10, 2))
    parser.add_argument("--until", type=_date_arg, default=datetime.date.today())
    parser.add_argument("--limit", type=int, default=ROW_LIMIT)
    args = parser.parse_args(argv)
    if args.since > args.until:
        print("since is after until", file=sys.stderr)
        return 2
    if args.limit < 1:
        print("limit must be at least 1", file=sys.stderr)
        return 2
    text = fetch_report(args.since, args.until, args.limit)
    print(text, end="" if text.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

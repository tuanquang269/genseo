"""AI referrer report. No network. Domain counts only; UTM is not a count."""
import io
import json
import os
import sys
import unittest
import urllib.error
from datetime import date, datetime, timezone
from contextlib import redirect_stderr, redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import ai_referrer_report as report

SINCE = date(2026, 10, 14)
UNTIL = date(2026, 10, 20)
WHEN = "2026-10-21T01:00:00+00:00"


def ok(rows):
    return {"ok": True, "rows": rows, "needs_scope": False, "error": ""}


def fail(error, scope=False):
    return {"ok": False, "rows": [], "needs_scope": scope, "error": error}


class Querier:
    def __init__(self, mapping):
        self.mapping = mapping
        self.order_called = False
        self.sql = []

    def shopifyql(self, sql):
        self.sql.append(sql)
        if "utm_source" in sql:
            return self.mapping["utm"]
        if "GROUP BY referrer_source" in sql:
            return self.mapping["direct_sessions"]
        if "GROUP BY order_referrer_source" in sql:
            return self.mapping["direct_orders"]
        if "GROUP BY order_referrer_domain" in sql:
            return self.mapping["orders"]
        if "GROUP BY referrer_domain" in sql:
            return self.mapping["sessions"]
        raise AssertionError(sql)

    def order_records(self, since, until):
        self.order_called = True
        if "fallback" not in self.mapping:
            raise AssertionError("order referrer fallback should not run")
        return self.mapping["fallback"]


def base_map(**overrides):
    mapping = {
        "sessions": ok([
            {"referrer_domain": None, "sessions": "20"},
            {"referrer_domain": "gemini.google.com", "sessions": "1"},
            {"referrer_domain": "my.many.chat", "sessions": "9"},
            {"referrer_domain": "google.com", "sessions": "7"},
        ]),
        "orders": ok([
            {"order_referrer_domain": None, "orders": "5"},
            {"order_referrer_domain": "gemini.google.com", "orders": "1"},
        ]),
        "direct_sessions": ok([
            {"referrer_source": "Direct", "sessions": "10"},
            {"referrer_source": "social", "sessions": "4"},
        ]),
        "direct_orders": ok([
            {"order_referrer_source": "search", "orders": "3"},
        ]),
        "utm": ok([
            {"utm_source": "chatgpt.com", "sessions": "2"},
            {"utm_source": "chatgpt", "sessions": "9"},
        ]),
    }
    mapping.update(overrides)
    return mapping


def fetch(mapping, limit=1000):
    querier = Querier(mapping)
    built, both_failed = report.fetch_shopify_report(
        SINCE, UNTIL, querier, "wellnessnest1.myshopify.com", "genseo-publisher", WHEN, limit=limit
    )
    return built, both_failed, querier


def engine(built, name):
    for row in built["engines"]:
        if row["name"] == name:
            return row
    raise AssertionError(name)


class Classify(unittest.TestCase):
    def test_known_hosts_and_rejected_lookalikes(self):
        cases = {
            "chatgpt.com": "ChatGPT",
            "HTTPS://WWW.ChatGPT.com:443/share/abc?utm_source=chatgpt.com": "ChatGPT",
            "chat.openai.com": "ChatGPT",
            "platform.openai.com": None,
            "openai.com": None,
            "my.many.chat": None,
            "gemini.google.com": "Gemini",
            "bard.google.com": "Gemini",
            "google.com": None,
            "news.google.com": None,
            "perplexity.ai": "Perplexity",
            "www.perplexity.ai": "Perplexity",
            "copilot.microsoft.com": "Copilot",
            "microsoft.com": None,
            "claude.ai": "Claude",
            "foo.claude.ai": "Claude",
            "grok.com": "Grok",
            "grok.x.ai": "Grok",
            "x.ai": "Grok",
            "x.com": None,
            "twitter.com": None,
            "": None,
            None: None,
        }
        for raw, expected in cases.items():
            self.assertEqual(report.engine_for_host(report.normalize_host(raw)), expected, raw)

    def test_landing_site_is_not_a_referrer(self):
        host = report.normalize_host(report.referrer_value({
            "referring_site": "",
            "landing_site": "https://wellnessnest.co/?utm_source=chatgpt.com",
            "customerJourneySummary": {"lastVisit": {"landingPage": "https://chatgpt.com/ignored"}},
        }))
        self.assertIsNone(host)
        counted = report.orders_from_records([
            {
                "referring_site": "https://www.chatgpt.com/s/abc?utm_source=chatgpt.com",
                "landing_site": "https://wellnessnest.co/blogs/news/example",
            },
            {
                "referring_site": "",
                "landing_site": "https://wellnessnest.co/?utm_source=chatgpt.com",
            },
            {
                "customerJourneySummary": {
                    "lastVisit": {
                        "referrerUrl": "https://claude.ai/chat/xyz",
                        "landingPage": "https://wellnessnest.co/products/x",
                    }
                }
            },
            {"referring_site": "https://x.com/grok", "landing_site": "https://wellnessnest.co/"},
        ])
        by_host = {row["order_referrer_domain"]: row["orders"] for row in counted}
        self.assertEqual(by_host["chatgpt.com"], 1)
        self.assertEqual(by_host["claude.ai"], 1)
        self.assertEqual(by_host[None], 1)
        self.assertEqual(by_host["x.com"], 1)
        self.assertIsNone(report.engine_for_host("x.com"))


class Window(unittest.TestCase):
    def test_inclusive_edges(self):
        self.assertTrue(report.overlaps_bug_window(date(2026, 10, 15), date(2026, 10, 15)))
        self.assertTrue(report.overlaps_bug_window(date(2026, 10, 20), date(2026, 10, 20)))
        self.assertTrue(report.overlaps_bug_window(date(2026, 10, 14), date(2026, 10, 20)))
        self.assertFalse(report.overlaps_bug_window(date(2026, 10, 14), date(2026, 10, 14)))
        self.assertFalse(report.overlaps_bug_window(date(2026, 10, 21), date(2026, 10, 27)))
        self.assertIn("does not overlap", report.bug_overlap_phrase(date(2026, 10, 21), date(2026, 10, 21)))
        self.assertIn("2026-10-15 through 2026-10-20", report.bug_overlap_phrase(SINCE, UNTIL))

    def test_default_week_ending_yesterday(self):
        self.assertEqual(report.default_window(date(2026, 10, 21)), (SINCE, UNTIL))


class Counts(unittest.TestCase):
    def test_domain_counts_ignore_utm_blank_and_lookalikes(self):
        built, both_failed, querier = fetch(base_map())
        self.assertFalse(both_failed)
        self.assertFalse(querier.order_called)
        chatgpt = engine(built, "ChatGPT")
        gemini = engine(built, "Gemini")
        self.assertEqual(chatgpt["sessions"], 0)
        self.assertEqual(chatgpt["orders"], 0)
        self.assertEqual(gemini["sessions"], 1)
        self.assertEqual(gemini["orders"], 1)
        self.assertEqual(built["ai_sessions"], 1)
        self.assertEqual(built["ai_orders"], 1)
        self.assertEqual(built["blank_sessions"], 20)
        self.assertEqual(built["blank_orders"], 5)
        self.assertEqual(built["other_sessions"], 16)
        self.assertEqual(built["direct_sessions"], 10)
        self.assertEqual(built["direct_orders"], 0)
        self.assertEqual(built["utm_chatgpt_sessions"], 2)
        self.assertEqual(built["utm_other"], [("chatgpt", 9)])
        text = report.render_report(built)
        self.assertIn("Not counted by UTM.", text)
        self.assertIn("| ChatGPT | chatgpt.com, chat.openai.com | 0 | 0 |", text)
        self.assertIn("utm_source=chatgpt.com in this period: 2.", text)
        self.assertIn("chatgpt = 9", text)
        self.assertIn("Do not add them together.", text)
        self.assertIn("does not estimate a correction", text)
        self.assertNotIn("| ChatGPT | chatgpt.com, chat.openai.com | 2 |", text)
        self.assertNotIn("%", text)
        for sql in querier.sql:
            if "utm_source" in sql:
                continue
            self.assertNotIn("utm_", sql)

    def test_truncated_group_by_is_unknown_not_zero(self):
        built, both_failed, _querier = fetch(base_map(), limit=2)
        self.assertTrue(both_failed)
        self.assertIsNone(engine(built, "ChatGPT")["sessions"])
        self.assertIsNone(engine(built, "Gemini")["sessions"])
        text = report.render_report(built)
        self.assertIn("| ChatGPT | chatgpt.com, chat.openai.com | unknown | unknown |", text)
        self.assertIn("the limit of 2", text)

    def test_unreadable_cell_does_not_become_zero(self):
        mapping = base_map(sessions=ok([
            {"referrer_domain": "chatgpt.com", "sessions": "3"},
            {"referrer_domain": "chat.openai.com", "sessions": ""},
        ]))
        built, _both, _querier = fetch(mapping)
        self.assertIsNone(engine(built, "ChatGPT")["sessions"])
        self.assertIsNone(built["ai_sessions"])

    def test_scope_failure_message_and_no_order_walk(self):
        mapping = base_map(
            sessions=fail("Access denied for shopifyqlQuery. Required access: read_reports", scope=True),
            orders=fail("Access denied for shopifyqlQuery. Required access: read_reports", scope=True),
            direct_sessions=fail("denied", scope=True),
            direct_orders=fail("denied", scope=True),
            utm=fail("denied", scope=True),
        )
        built, both_failed, querier = fetch(mapping)
        self.assertTrue(both_failed)
        self.assertFalse(querier.order_called)
        self.assertEqual(built["scope_message"], report.SCOPE_NEEDED)
        text = report.render_report(built)
        self.assertIn("needs scope read_reports", text)
        self.assertIn("unknown", text)
        buf = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(err):
            code = report.main(
                ["--since", "2026-10-14", "--until", "2026-10-20"],
                querier_factory=lambda: Querier(mapping),
                now=datetime(2026, 10, 21, tzinfo=timezone.utc),
            )
        self.assertEqual(code, 2)
        self.assertIn("needs scope read_reports", buf.getvalue())
        self.assertIn("does not request a new token", err.getvalue())

    def test_order_url_fallback_when_sales_query_fails(self):
        mapping = base_map(orders=fail("Column Not Found: order_referrer_domain"))
        mapping["fallback"] = {
            "ok": True,
            "truncated": False,
            "needs_scope": False,
            "error": "",
            "rows": [
                {"referring_site": "https://chatgpt.com/a", "landing_site": "https://wellnessnest.co/"},
                {"referring_site": "", "landing_site": "https://wellnessnest.co/?utm_source=chatgpt.com"},
            ],
        }
        built, both_failed, querier = fetch(mapping)
        self.assertFalse(both_failed)
        self.assertTrue(querier.order_called)
        self.assertEqual(engine(built, "ChatGPT")["orders"], 1)
        self.assertEqual(built["blank_orders"], 1)
        self.assertIn("landing_site was not used", " ".join(built["notes"]))


class CsvImport(unittest.TestCase):
    def test_partial_csv_leaves_omitted_engines_unknown(self):
        with open(os.path.join(ROOT, "tests/fixtures/ai_referrer_week.csv"), encoding="utf-8") as handle:
            text = handle.read()
        built = report.report_from_csv(text, SINCE, UNTIL, False, WHEN, "week.csv")
        self.assertEqual(engine(built, "ChatGPT")["sessions"], 6)
        self.assertIsNone(engine(built, "ChatGPT")["orders"])
        self.assertEqual(engine(built, "Gemini")["sessions"], 4)
        self.assertIsNone(engine(built, "Claude")["sessions"])
        self.assertEqual(engine(built, "Grok")["sessions"], 2)
        self.assertEqual(engine(built, "Grok")["orders"], 1)
        self.assertEqual(engine(built, "Perplexity")["sessions"], None)
        self.assertEqual(built["blank_sessions"], 20)
        self.assertIsNone(built["direct_sessions"])
        self.assertIsNone(built["ai_sessions"])
        names = [row["name"] for row in built["engines"]]
        self.assertNotIn("x.com", names)

    def test_complete_csv_counts_omitted_engines_as_zero(self):
        text = "referrer_domain,sessions,orders\ngemini.google.com,4,0\n"
        built = report.report_from_csv(text, SINCE, UNTIL, True, WHEN, "full.csv")
        self.assertEqual(engine(built, "ChatGPT")["sessions"], 0)
        self.assertEqual(engine(built, "Gemini")["sessions"], 4)
        self.assertEqual(built["ai_sessions"], 4)
        self.assertEqual(built["blank_sessions"], 0)

    def test_missing_orders_column_stays_unknown(self):
        text = "referrer_domain,sessions\nchatgpt.com,3\n"
        built = report.report_from_csv(text, SINCE, UNTIL, True, WHEN, "sessions.csv")
        self.assertEqual(engine(built, "ChatGPT")["sessions"], 3)
        self.assertIsNone(engine(built, "ChatGPT")["orders"])
        self.assertIsNone(built["ai_orders"])

    def test_utm_only_file_is_rejected(self):
        path = os.path.join(ROOT, "tests/fixtures/ai_referrer_utm_only.csv")
        with self.assertRaises(report.ReportError) as caught:
            report.main(["--csv", path, "--since", "2026-10-14", "--until", "2026-10-20"])
        self.assertIn("does not count by UTM", str(caught.exception))
        self.assertEqual(caught.exception.code, 2)

    def test_bad_day_is_not_imported(self):
        with self.assertRaises(report.ReportError):
            report.report_from_csv(
                "referrer_domain,sessions,day\nchatgpt.com,3,not-a-day\n",
                SINCE, UNTIL, True, WHEN, "bad.csv",
            )


class HttpRead(unittest.TestCase):
    def test_graphql_document_is_a_query(self):
        self.assertTrue(report.SHOPIFYQL_GQL.lstrip().startswith("query"))
        self.assertTrue(report.ORDERS_GQL.lstrip().startswith("query"))
        self.assertNotIn("mutation", report.SHOPIFYQL_GQL)
        self.assertNotIn("mutation", report.ORDERS_GQL)
        querier = report.HTTPQuerier("shop.example", "shpat_LOCALTEST")
        with self.assertRaises(report.ReportError):
            querier.graphql("mutation { shop { name } }", {})

    def test_error_body_redacts_token(self):
        def opener(req, timeout=60):
            raise urllib.error.HTTPError(
                req.full_url, 403, "no", hdrs=None, fp=io.BytesIO(b'{"token":"shpat_SECRETSECRET"}')
            )

        querier = report.HTTPQuerier("shop.example", "shpat_LOCALTEST", opener=opener)
        result = querier.shopifyql("FROM sessions SHOW sessions")
        self.assertTrue(result["needs_scope"])
        self.assertIn("needs scope read_reports", result["error"])
        self.assertNotIn("SECRETSECRET", result["error"])
        self.assertNotIn("shpat_LOCALTEST", result["error"])

    def test_list_rows_and_order_pages(self):
        pages = [
            {
                "data": {
                    "orders": {
                        "pageInfo": {"hasNextPage": True, "endCursor": "c1"},
                        "nodes": [{"customerJourneySummary": {"lastVisit": {"referrerUrl": "https://www.chatgpt.com/a"}}}],
                    }
                }
            },
            {
                "data": {
                    "orders": {
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [{"customerJourneySummary": {"lastVisit": {"referrerUrl": "https://claude.ai/b"}}}],
                    }
                }
            },
        ]

        class Opener:
            def __init__(self):
                self.n = 0

            def __call__(self, req, timeout=60):
                body = json.dumps(pages[self.n])
                self.n += 1
                return _Resp(body)

        querier = report.HTTPQuerier("shop.example", "token", opener=Opener())
        result = querier.order_records(SINCE, UNTIL)
        self.assertTrue(result["ok"])
        rows = report.orders_from_records(result["rows"])
        hosts = {row["order_referrer_domain"]: row["orders"] for row in rows}
        self.assertEqual(hosts["chatgpt.com"], 1)
        self.assertEqual(hosts["claude.ai"], 1)

        old = report.ORDER_CAP
        report.ORDER_CAP = 1
        try:
            capped = report.HTTPQuerier("shop.example", "token", opener=Opener())
            limited = capped.order_records(SINCE, UNTIL)
        finally:
            report.ORDER_CAP = old
        self.assertFalse(limited["ok"])
        self.assertTrue(limited["truncated"])

    def test_shopifyql_list_row(self):
        payload = {
            "data": {
                "shopifyqlQuery": {
                    "parseErrors": [],
                    "tableData": {
                        "columns": [{"name": "referrer_domain"}, {"name": "sessions"}],
                        "rows": [["gemini.google.com", "4"]],
                    },
                }
            }
        }

        def opener(req, timeout=60):
            return _Resp(json.dumps(payload))

        querier = report.HTTPQuerier("shop.example", "token", opener=opener)
        result = querier.shopifyql("FROM sessions SHOW sessions")
        self.assertTrue(result["ok"])
        self.assertEqual(result["rows"], [{"referrer_domain": "gemini.google.com", "sessions": "4"}])


class Template(unittest.TestCase):
    def test_template_is_unknown_and_flags_the_window(self):
        text = report.render_report(report.template_report())
        self.assertIn("2026-10-15 through 2026-10-20", text)
        self.assertIn("This report overlaps that window", text)
        self.assertIn("| ChatGPT | chatgpt.com, chat.openai.com | unknown | unknown |", text)
        self.assertIn("not a store read", text)
        self.assertNotIn("shpat_", text)
        path = os.path.join(ROOT, "docs/AI_REFERRER_REPORT_TEMPLATE.md")
        with open(path, encoding="utf-8") as handle:
            self.assertIn(text, handle.read())


class _Resp:
    def __init__(self, body, status=200):
        self.status = status
        self._body = body.encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


if __name__ == "__main__":
    unittest.main()

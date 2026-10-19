"""Deep content pages and the GEO traffic report's direct-session line."""
import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import deep_content_pages as pages
import geo_traffic_report as report


class DeepContentDefinition(unittest.TestCase):
    def test_rules_live_in_one_constant(self):
        names = [name for name, _pattern in pages.DEEP_CONTENT_PAGE["counts"]]
        self.assertEqual(names, ["blog_article", "guide", "listicle_or_landing"])
        text = pages.DEEP_CONTENT_PAGE["description"]
        for phrase in (
            "blog article",
            "guide",
            "listicle/landing",
            "blog index",
            "Home",
            "collections index",
            "cart",
            "checkout",
            "account",
            "search",
            "policy",
        ):
            self.assertIn(phrase, text)

    def test_articles_guides_and_landing_pages_count(self):
        self.assertTrue(pages.is_deep_content_page(
            "/blogs/news/when-to-take-shilajit-morning-or-night-us-2026"
        ))
        self.assertTrue(pages.is_deep_content_page(
            "/bg/blogs/news/shilajit-gold-resin-review-is-75-worth-it-us-2026"
        ))
        self.assertTrue(pages.is_deep_content_page(
            "https://wellnessnest.co/blogs/news/Foo-Bar/"
        ))
        self.assertTrue(pages.is_deep_content_page("/guides/how-to-take-nmn"))
        self.assertTrue(pages.is_deep_content_page("/de/guides/nmn/week-1"))
        self.assertTrue(pages.is_deep_content_page(
            "/pages/10-reasons-why-creatine-is-for-skinny-people"
        ))
        self.assertTrue(pages.is_deep_content_page(
            "https://wellnessnest.co/it/pages/shilasource-himalayan-shilajit-resin-it-2?utm_source=chatgpt.com"
        ))
        self.assertTrue(pages.is_deep_content_page("/es-es/pages/gp-sr-av-2"))

    def test_home_index_cart_checkout_account_search_and_policy_do_not(self):
        rejected = [
            "/",
            "",
            "https://wellnessnest.co",
            "https://wellnessnest.co/",
            "/?utm_source=chatgpt.com",
            "/fr",
            "/de/",
            "/collections",
            "/collections/",
            "/collections/all",
            "/es-es/collections",
            "/de/collections/all",
            "/cart",
            "/de/cart",
            "/checkout",
            "/checkout/123/do/abc/shoppay",
            "/de/checkouts/c/token",
            "/account",
            "/account/login",
            "/de/account/orders",
            "/search",
            "/search?q=nmn",
            "/de/search",
            "/policies/privacy-policy",
            "/de/policies/refund-policy",
            "/pages/privacy-policy",
            "/pages/terms-of-service",
            "/blogs",
            "/blogs/news",
            "/blogs/news/",
            "/blogs/news/tagged",
            "/blogs/news/tagged/nmn",
            "/guides",
            "/pages",
            "/products/ageaura-pure-nmn-tmg-nad-complex",
            "/collections/best-seller",
            "/apps/17TRACK",
            "/de/apps/17TRACK",
            "/pl/tools/recurring/login",
        ]
        for path in rejected:
            self.assertFalse(pages.is_deep_content_page(path), path)


def _row(day, path, sessions, source="direct", referrer=None, **utm):
    row = {
        "day": day,
        "landing_page_path": path,
        "sessions": sessions,
        "referrer_source": source,
        "referrer_url": referrer,
        "utm_source": None,
        "utm_medium": None,
        "utm_campaign": None,
        "utm_term": None,
        "utm_content": None,
    }
    row.update(utm)
    return row


class DirectSessionRule(unittest.TestCase):
    def test_direct_requires_the_label_an_empty_referrer_and_empty_utms(self):
        clean = _row("2026-10-09", "/blogs/news/nmn-guide", 2)
        self.assertTrue(report.is_direct_no_referrer_no_utm(clean))
        self.assertTrue(report.is_direct_no_referrer_no_utm(
            _row("2026-10-09", "/pages/listicle", "2", source=" Direct ")
        ))
        self.assertFalse(report.is_direct_no_referrer_no_utm(
            _row("2026-10-09", "/blogs/news/nmn-guide", 2, utm_source="chatgpt.com")
        ))
        self.assertFalse(report.is_direct_no_referrer_no_utm(
            _row("2026-10-09", "/blogs/news/nmn-guide", 2, referrer="https://chatgpt.com/")
        ))
        self.assertFalse(report.is_direct_no_referrer_no_utm(
            _row("2026-10-09", "/blogs/news/nmn-guide", 2, source="search")
        ))
        self.assertFalse(report.is_direct_no_referrer_no_utm(
            _row("2026-10-09", "/blogs/news/nmn-guide", 2, source=None)
        ))
        self.assertFalse(report.is_direct_no_referrer_no_utm(
            _row("2026-10-09", "/blogs/news/nmn-guide", 2, utm_content="link_in_bio")
        ))


class ReportLine(unittest.TestCase):
    def setUp(self):
        self.direct = [
            _row("2026-10-08", "/blogs/news/when-to-take-shilajit-morning-or-night-us-2026", "4"),
            _row("2026-10-08", "/", 10),
            _row("2026-10-08", "/blogs/news/nmn-guide", 6, utm_source="chatgpt.com"),
            _row("2026-10-08", "/blogs/news/nmn-guide", 3, referrer="wellnessnest.co/pages/listicle"),
            _row("2026-10-08", "/products/ageaura-pure-nmn-tmg-nad-complex", 5),
            _row("2026-10-09", "/pages/10-reasons-why-creatine-is-for-skinny-people", 5),
            _row("2026-10-09", "/de/guides/nmn/week-1", 2),
            _row("2026-10-09", "/products/florafresh-vaginal-probiotics-gummies", 7),
            _row("2026-10-09", "/checkout/123/do/abc", 1),
            _row("2026-10-09", "/blogs/news/nmn-guide", 9, source="social"),
        ]
        self.totals = [
            {"day": "2026-10-08", "sessions": "40"},
            {"day": "2026-10-09", "sessions": 20},
        ]
        self.columns = list(self.direct[0].keys())
        self.total_columns = ["day", "sessions"]

    def test_daily_share_before_after_and_oct_9_annotation(self):
        text = report.render_report(
            self.direct, self.totals, self.columns, self.total_columns,
            since="2026-10-08", until="2026-10-09",
        )
        self.assertIn(report.SECTION, text)
        self.assertIn("proxy, not attributed AI traffic", text)
        self.assertIn("2026-10-09 is the suspected date AI assistants stopped passing UTMs", text)
        self.assertIn("| 2026-10-08 | 4 | 40 | 10.0% |  |", text)
        self.assertIn("| 2026-10-09 | 7 | 20 | 35.0% | suspected UTM drop |", text)
        self.assertIn("Before 2026-10-09 (2026-10-08 .. 2026-10-08, 1 day): direct_deep 4 / total 40 (10.0%)", text)
        self.assertIn("On and after 2026-10-09 (2026-10-09 .. 2026-10-09, 1 day): direct_deep 7 / total 20 (35.0%)", text)
        self.assertIn("Daily-average change (on and after minus before): +3.0 direct_deep sessions", text)
        self.assertNotIn("data not available from shopifyql", text)
        self.assertNotIn("chatgpt.com", text)

    def test_empty_direct_rows_are_zero_when_the_total_came_back(self):
        text = report.render_report([], self.totals, self.columns, self.total_columns)
        self.assertIn("| 2026-10-08 | 0 | 40 | 0.0% |  |", text)
        self.assertIn("| 2026-10-09 | 0 | 20 | 0.0% | suspected UTM drop |", text)

    def test_missing_utm_field_prints_unavailable_and_no_totals(self):
        columns = [name for name in self.columns if name != "utm_campaign"]
        text = report.render_report(self.direct, self.totals, columns, self.total_columns)
        self.assertIn("data not available from shopifyql", text)
        self.assertIn("utm_campaign", text)
        self.assertNotIn("direct_deep_sessions", text)
        self.assertNotIn("35.0%", text)

    def test_truncated_pull_does_not_print_numbers(self):
        text = report.render_report(
            self.direct, self.totals, self.columns, self.total_columns, truncated=True,
        )
        self.assertIn("data not available from shopifyql", text)
        self.assertNotIn("10.0%", text)
        self.assertNotIn("suspected UTM drop", text)

    def test_no_session_days_is_unavailable(self):
        text = report.render_report([], [], self.columns, self.total_columns)
        self.assertEqual(
            text.strip(),
            "data not available from shopifyql: the sessions query returned no days",
        )

    def test_unparseable_count_is_unavailable(self):
        totals = [{"day": "2026-10-09", "sessions": "about 20"}]
        text = report.render_report([], totals, self.columns, self.total_columns)
        self.assertIn("data not available from shopifyql", text)
        self.assertNotIn("share_of_total", text)

    def test_direct_day_missing_from_total_is_unavailable(self):
        totals = [{"day": "2026-10-08", "sessions": 40}]
        text = report.render_report(self.direct, totals, self.columns, self.total_columns)
        self.assertIn("data not available from shopifyql", text)
        self.assertIn("2026-10-09", text)
        self.assertNotIn("share_of_total", text)

    def test_deep_above_total_is_unavailable(self):
        direct = [_row("2026-10-09", "/guides/how-to-take-nmn", 5)]
        totals = [{"day": "2026-10-09", "sessions": 4}]
        text = report.render_report(direct, totals, self.columns, self.total_columns)
        self.assertIn("data not available from shopifyql", text)
        self.assertIn("exceed total", text)

    def test_drop_date_constant(self):
        self.assertEqual(report.SUSPECTED_UTM_DROP, datetime.date(2026, 10, 9))


if __name__ == "__main__":
    unittest.main()

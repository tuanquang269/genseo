"""Draft dead-link check: HTTP 429 is unverified, not a pass.

Shopify rate limits wellnessnest.co with 429. The old check treated that
status as live after a few retries, so a dead internal link could ride
through validate_article.py --draft as PASS. These tests stub the HTTP
stack. They do not open a socket.
"""
import datetime
import email.utils
import os
import socket
import sys
import unittest
import urllib.request
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import validate_article as va


class _FakeResponse(object):
    def __init__(self, status, headers):
        self.status = status
        self.headers = headers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _ScriptedOpener(object):
    """build_opener stand-in. Each open() returns the next scripted status."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.timeouts = []

    def open(self, req, timeout=None):
        self.requests.append(req)
        self.timeouts.append(timeout)
        if not self.responses:
            raise AssertionError("dead-link check made an extra HTTP request")
        status, headers = self.responses.pop(0)
        return _FakeResponse(status, headers)


def _http_date(delta):
    moment = datetime.datetime.now(datetime.timezone.utc) + delta
    return email.utils.format_datetime(moment, usegmt=True)


class DraftLink429Tests(unittest.TestCase):
    def setUp(self):
        self._network = mock.patch.object(
            socket, "create_connection",
            side_effect=AssertionError("live HTTP is not allowed in this test"))
        self._network.start()
        self.addCleanup(self._network.stop)

    def _check(self, responses, tries=None):
        opener = _ScriptedOpener(responses)
        sleeps = []
        kwargs = {"sleep": sleeps.append}
        if tries is not None:
            kwargs["tries"] = tries
        with mock.patch.object(va.urllib.request, "build_opener", return_value=opener):
            outcome = va.check_link(
                "https://wellnessnest.co/products/missing", **kwargs)
        return outcome, sleeps, opener

    def test_persistent_429_is_unverified_and_honors_retry_after(self):
        outcome, sleeps, opener = self._check(
            [(429, {"Retry-After": "4"})] * 3)
        self.assertEqual(outcome, va.UNVERIFIED)
        self.assertEqual(len(opener.requests), va.LINK_TRIES)
        self.assertEqual(sleeps, [4.0, 4.0])
        self.assertEqual(opener.timeouts, [va.LINK_TIMEOUT] * 3)
        self.assertEqual(opener.requests[0].get_method(), "GET")
        self.assertIn("Mozilla/5.0", opener.requests[0].get_header("User-agent"))
        self.assertTrue(
            opener.requests[0].full_url.startswith("https://wellnessnest.co/"))

    def test_429_that_clears_counts_as_live(self):
        outcome, sleeps, opener = self._check([
            (429, {"Retry-After": "2"}),
            (200, {}),
        ])
        self.assertEqual(outcome, va.OK)
        self.assertEqual(sleeps, [2.0])
        self.assertEqual(len(opener.requests), 2)

    def test_429_then_404_is_dead(self):
        outcome, sleeps, opener = self._check([
            (429, {"Retry-After": "1"}),
            (404, {}),
        ])
        self.assertEqual(outcome, va.DEAD)
        self.assertEqual(sleeps, [1.0])
        self.assertEqual(len(opener.requests), 2)

    def test_404_and_410_do_not_retry(self):
        for status in (404, 410):
            outcome, sleeps, opener = self._check([(status, {})])
            self.assertEqual(outcome, va.DEAD, status)
            self.assertEqual(sleeps, [])
            self.assertEqual(len(opener.requests), 1)

    def test_redirect_and_200_are_live_without_a_second_request(self):
        for status in (200, 301, 302, 307, 308):
            outcome, sleeps, opener = self._check([(status, {"Location": "https://wellnessnest.co/elsewhere"})])
            self.assertEqual(outcome, va.OK, status)
            self.assertEqual(sleeps, [])
            self.assertEqual(len(opener.requests), 1, status)

    def test_retry_after_is_capped(self):
        outcome, sleeps, _opener = self._check(
            [(429, {"Retry-After": "3600"})] * 3)
        self.assertEqual(outcome, va.UNVERIFIED)
        self.assertEqual(sleeps, [va.RETRY_AFTER_CAP, va.RETRY_AFTER_CAP])

    def test_missing_or_useless_retry_after_uses_backoff(self):
        for header in ({}, {"Retry-After": "0"}, {"Retry-After": "soon"},
                       {"Retry-After": "-5"}, {"Retry-After": "  "}):
            outcome, sleeps, _opener = self._check([(429, header)] * 3)
            self.assertEqual(outcome, va.UNVERIFIED, header)
            self.assertEqual(sleeps, [1.5, 3.0], header)

    def test_future_http_date_is_honored_and_a_far_date_is_capped(self):
        soon = _http_date(datetime.timedelta(seconds=5))
        outcome, sleeps, _opener = self._check([
            (429, {"Retry-After": soon}),
            (200, {}),
        ])
        self.assertEqual(outcome, va.OK)
        self.assertEqual(len(sleeps), 1)
        self.assertGreater(sleeps[0], 2.5)
        self.assertLessEqual(sleeps[0], va.RETRY_AFTER_CAP)

        later = _http_date(datetime.timedelta(hours=3))
        outcome, sleeps, _opener = self._check(
            [(429, {"Retry-After": later})] * 3)
        self.assertEqual(outcome, va.UNVERIFIED)
        self.assertEqual(sleeps, [va.RETRY_AFTER_CAP, va.RETRY_AFTER_CAP])

    def test_past_http_date_keeps_the_backoff(self):
        outcome, sleeps, _opener = self._check(
            [(429, {"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"})] * 3)
        self.assertEqual(outcome, va.UNVERIFIED)
        self.assertEqual(sleeps, [1.5, 3.0])

    def test_one_try_does_not_sleep_after_the_only_429(self):
        outcome, sleeps, opener = self._check(
            [(429, {"Retry-After": "30"})], tries=1)
        self.assertEqual(outcome, va.UNVERIFIED)
        self.assertEqual(sleeps, [])
        self.assertEqual(len(opener.requests), 1)

    def test_non_429_errors_ignore_retry_after_and_stay_dead(self):
        outcome, sleeps, _opener = self._check(
            [(500, {"Retry-After": "1"})] * 3)
        self.assertEqual(outcome, va.DEAD)
        self.assertEqual(sleeps, [1.5, 3.0])

        outcome, sleeps, _opener = self._check([(0, None)] * 3)
        self.assertEqual(outcome, va.DEAD)
        self.assertEqual(sleeps, [1.5, 3.0])

    def test_503_and_430_stay_transient_after_the_budget(self):
        # Pre-existing rule: these codes are not called dead. Only 429 is unverified.
        for status in (503, 430):
            outcome, sleeps, _opener = self._check(
                [(status, {"Retry-After": "1"})] * 3)
            self.assertEqual(outcome, va.OK, status)
            self.assertEqual(sleeps, [1.5, 3.0], status)

    def test_fetch_link_turns_a_network_error_into_status_zero(self):
        class _Down(object):
            def open(self, req, timeout=None):
                raise OSError("connection refused")

        with mock.patch.object(va.urllib.request, "build_opener", return_value=_Down()):
            self.assertEqual(
                va.fetch_link("https://wellnessnest.co/products/x"), (0, None))

    def test_status_handler_replaces_the_default_error_processor(self):
        handler = va._KeepStatus()
        response = mock.Mock(status=429)
        self.assertIs(handler.http_response(None, response), response)
        self.assertIs(handler.https_response(None, response), response)
        opener = va.urllib.request.build_opener(va._KeepStatus)
        processors = opener.process_response.get("http", [])
        self.assertEqual(
            [type(item) for item in processors if isinstance(item, urllib.request.HTTPErrorProcessor)],
            [va._KeepStatus])

    def test_unverified_links_block_pass_with_exit_3(self):
        url = "https://wellnessnest.co/products/missing-sku"
        fails, warns, link_exit = va.assess_internal_links(
            [url], check=lambda _url: va.UNVERIFIED)
        self.assertEqual(fails, [])
        self.assertEqual(link_exit, va.EXIT_UNVERIFIED)
        self.assertEqual(va.final_exit(fails, link_exit), 3)
        self.assertIn("/products/missing-sku", warns[0])
        self.assertIn("WARN/UNVERIFIED", warns[0])
        self.assertNotIn("PASS", warns[0])
        line = va.result_line(va.EXIT_UNVERIFIED)
        self.assertIn("WARN/UNVERIFIED", line)
        self.assertIn("HTTP 429", line)
        self.assertNotIn("PASS", line)
        self.assertNotIn("✓ PASS", line)

    def test_dead_link_still_fails_and_a_live_link_can_pass(self):
        fails, warns, link_exit = va.assess_internal_links(
            ["https://wellnessnest.co/products/gone"], check=lambda _url: va.DEAD)
        self.assertEqual(warns, [])
        self.assertIn("dead/404 links: /products/gone", fails[0])
        self.assertEqual(va.final_exit(fails, link_exit), 1)
        self.assertIn("DO NOT PUBLISH", va.result_line(1))
        self.assertNotIn("PASS", va.result_line(1))

        fails, warns, link_exit = va.assess_internal_links(
            ["https://wellnessnest.co/products/live"], check=lambda _url: va.OK)
        self.assertEqual(fails, [])
        self.assertEqual(warns, [])
        self.assertEqual(va.final_exit(fails, link_exit), 0)
        self.assertIn("✓ PASS", va.result_line(0))

    def test_a_dead_link_outranks_a_rate_limit(self):
        def check(url):
            if url.endswith("/gone"):
                return va.DEAD
            return va.UNVERIFIED

        fails, warns, link_exit = va.assess_internal_links([
            "https://wellnessnest.co/products/gone",
            "https://wellnessnest.co/products/maybe",
        ], check=check)
        self.assertTrue(any("dead/404" in item for item in fails))
        self.assertTrue(any("WARN/UNVERIFIED" in item for item in warns))
        self.assertEqual(va.final_exit(fails, link_exit), 1)

    def test_unverified_warnings_cap_at_six_and_still_block(self):
        urls = ["https://wellnessnest.co/products/p%d" % i for i in range(7)]
        fails, warns, link_exit = va.assess_internal_links(
            urls, check=lambda _url: va.UNVERIFIED)
        self.assertEqual(fails, [])
        self.assertEqual(len(warns), 6)
        self.assertEqual(va.final_exit(fails, link_exit), va.EXIT_UNVERIFIED)

    def test_gate_source_no_longer_treats_429_as_live(self):
        path = os.path.join(ROOT, "scripts", "validate_article.py")
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        self.assertNotIn('return code in ("429", "430", "503")', source)
        self.assertIn("assess_internal_links", source)
        self.assertIn("final_exit", source)
        self.assertIn("result_line", source)
        self.assertIn("sys.exit(exit_code)", source)


if __name__ == "__main__":
    unittest.main()

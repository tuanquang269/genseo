"""IndexNow planner tests. No live HTTP."""
from __future__ import annotations

import json
import os
import sys
import unittest
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import indexnow_ping  # noqa: E402


KEY = "abcdef0123456789"
URL = "https://wellnessnest.co/blogs/news/when-to-take-nmn"


class _Resp:
    def __init__(self, code, body):
        self._code = code
        self._body = body.encode("utf-8") if isinstance(body, str) else body

    def getcode(self):
        return self._code

    def read(self):
        return self._body

    def close(self):
        return None


class _Opener:
    def __init__(self, key_body=KEY, key_code=200, post_code=202):
        self.calls = []
        self.key_body = key_body
        self.key_code = key_code
        self.post_code = post_code

    def __call__(self, req, timeout=20):
        self.calls.append(req)
        if req.get_method() == "GET":
            return _Resp(self.key_code, self.key_body)
        return _Resp(self.post_code, "")


class IndexNowPlanTests(unittest.TestCase):
    def test_missing_key_skips_without_calling_opener(self):
        opener = _Opener()
        result = indexnow_ping.execute([URL], env={}, opener=opener)
        self.assertEqual(result["action"], "skip")
        self.assertIn("INDEXNOW_KEY is not set", result["message"])
        self.assertEqual(opener.calls, [])
        self.assertIsNone(result["payload"])

    def test_placeholder_key_is_treated_as_unset(self):
        result = indexnow_ping.plan([URL], env={"INDEXNOW_KEY": "YOUR_INDEXNOW_KEY"})
        self.assertEqual(result["action"], "skip")

    def test_dry_run_builds_payload_and_does_not_call_opener(self):
        opener = _Opener()
        env = {"INDEXNOW_KEY": KEY, "INDEXNOW_DRY_RUN": "1"}
        result = indexnow_ping.execute([URL], env=env, opener=opener)
        self.assertEqual(result["action"], "dry-run")
        self.assertEqual(opener.calls, [])
        self.assertEqual(result["payload"]["host"], "wellnessnest.co")
        self.assertEqual(result["payload"]["key"], KEY)
        self.assertEqual(result["payload"]["keyLocation"], f"https://wellnessnest.co/{KEY}.txt")
        self.assertEqual(result["payload"]["urlList"], [URL])
        self.assertIn("no request sent", result["message"])

    def test_key_location_override_must_stay_on_the_store_host(self):
        env = {
            "INDEXNOW_KEY": KEY,
            "INDEXNOW_KEY_LOCATION": "https://wellnessnest.co/pages/indexnow-key",
            "INDEXNOW_DRY_RUN": "true",
        }
        result = indexnow_ping.plan([URL], env=env)
        self.assertEqual(result["payload"]["keyLocation"], "https://wellnessnest.co/pages/indexnow-key")
        bad = indexnow_ping.plan(
            [URL],
            env={"INDEXNOW_KEY": KEY, "INDEXNOW_KEY_LOCATION": "https://cdn.shopify.com/key.txt"},
        )
        self.assertEqual(bad["action"], "invalid")
        self.assertIn("same host", bad["message"])

    def test_invalid_key_does_not_send(self):
        opener = _Opener()
        result = indexnow_ping.execute([URL], env={"INDEXNOW_KEY": "short"}, opener=opener)
        self.assertEqual(result["action"], "invalid")
        self.assertEqual(opener.calls, [])
        self.assertNotIn("short", result["message"])

    def test_send_preflights_then_posts(self):
        opener = _Opener()
        env = {"INDEXNOW_KEY": KEY}
        result = indexnow_ping.execute([URL], env=env, opener=opener)
        self.assertEqual(result["action"], "send")
        self.assertEqual(result["status"], 202)
        self.assertEqual([req.get_method() for req in opener.calls], ["GET", "POST"])
        post = opener.calls[1]
        self.assertEqual(post.full_url, indexnow_ping.DEFAULT_ENDPOINT)
        body = json.loads(post.data.decode("utf-8"))
        self.assertEqual(body["urlList"], [URL])
        self.assertIn("SUCCESS (202)", result["message"])

    def test_send_skips_post_when_key_file_mismatches(self):
        opener = _Opener(key_body="<html>not the key</html>", key_code=200)
        result = indexnow_ping.execute([URL], env={"INDEXNOW_KEY": KEY}, opener=opener)
        self.assertEqual(result["action"], "skip")
        self.assertEqual([req.get_method() for req in opener.calls], ["GET"])
        self.assertIn("no IndexNow POST", result["message"])

    def test_send_skips_post_when_key_file_404(self):
        def opener(req, timeout=20):
            raise urllib.error.HTTPError(req.full_url, 404, "missing", urllib.request.Request(req.full_url).headers, None)

        result = indexnow_ping.execute([URL], env={"INDEXNOW_KEY": KEY}, opener=opener)
        self.assertEqual(result["action"], "skip")
        self.assertIn("HTTP 404", result["message"])

    def test_brand_guard_blocks_denied_ageaura_urls(self):
        opener = _Opener()
        result = indexnow_ping.execute(
            [URL, "https://wellnessnest.co/products/ageaura-pure-urolithin-a"],
            env={"INDEXNOW_KEY": KEY},
            opener=opener,
        )
        self.assertEqual(result["action"], "invalid")
        self.assertIsNone(result["payload"])
        self.assertEqual(opener.calls, [])
        self.assertIn("AgeAura guard", result["message"])
        dry = indexnow_ping.plan(
            ["https://wellnessnest.co/collections/ageaura"],
            env={"INDEXNOW_KEY": KEY, "INDEXNOW_DRY_RUN": "1"},
        )
        self.assertEqual(dry["action"], "invalid")

    def test_foreign_url_is_rejected(self):
        result = indexnow_ping.plan(
            ["https://example.com/blogs/news/x"],
            env={"INDEXNOW_KEY": KEY, "INDEXNOW_DRY_RUN": "1"},
        )
        self.assertEqual(result["action"], "invalid")

    def test_article_url_uses_news_blog(self):
        self.assertEqual(
            indexnow_ping.article_url("when-to-take-nmn", env={}),
            URL,
        )

    def test_publisher_has_no_hardcoded_key(self):
        with open(os.path.join(ROOT, "scripts", "shopify_publisher.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn("YOUR_INDEXNOW_KEY", src)
        self.assertIn("indexnow_ping.execute", src)

    def test_self_check_makes_no_network_call(self):
        self.assertEqual(indexnow_ping.self_check(), 0)

    def test_setup_script_does_not_call_shopify(self):
        with open(os.path.join(ROOT, "scripts", "setup_indexnow.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn("urlopen", src)
        self.assertNotIn("admin/api", src)
        self.assertNotIn("access_token", src)


if __name__ == "__main__":
    unittest.main()

"""First publish uses the article URL Shopify returns on create.

Shopify is mocked. Nothing here opens a socket, and nothing is published.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import urllib.parse
from contextlib import redirect_stdout
from unittest.mock import patch
from uuid import uuid4

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

BLOG_ID = "55"
ARTICLE_ID = 4242
BLOG_HANDLE = "field-notes"
RETURNED_HANDLE = "morning-walk-notes-2"
TITLE_SLUG = "morning-walk-notes"
PUBLIC_URL = "https://wellnessnest.co/blogs/%s/%s" % (BLOG_HANDLE, RETURNED_HANDLE)
SHOP = "fixture-shop.invalid"
BUY = (
    "Buy [the pouch](https://wellnessnest.co/products/foo"
    "?selling_plan=123&utm_source=x&variant=9)."
)
BYLINE = (
    "\n### About the Author\n"
    "[Mike Moretti](/pages/mike-moretti) — Co-founder, Wellness Nest\n"
)


class LiveShopifyBlocked(BaseException):
    """A test tried to call a host other than the fixture. Not a Shopify error."""


def _jsonld(url):
    body = json.dumps({
        "@type": "Article",
        "@id": url,
        "url": url,
        "mainEntityOfPage": url,
    })
    return '<script type="application/ld+json">%s</script>' % body


def _draft_text(identity_url, byline=False):
    parts = [
        "# Morning Walk Notes",
        "",
        "A short note about a morning walk. " + BUY,
        "",
        _jsonld(identity_url),
    ]
    if byline:
        parts.append(BYLINE)
    return "\n".join(parts) + "\n"


class _Resp:
    def __init__(self, payload, code=200):
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload).encode()
        self._payload = payload
        self._code = code

    def read(self):
        return self._payload

    def getcode(self):
        return self._code


class ShopifyFake:
    """Admin API double. Refuses any host except fixture-shop.invalid."""

    def __init__(self, blog_handle=BLOG_HANDLE, article_handle=RETURNED_HANDLE, article_id=ARTICLE_ID):
        self.blog_handle = blog_handle
        self.article_handle = article_handle
        self.article_id = article_id
        self.calls = []

    def urlopen(self, req, *args, **kwargs):
        if not hasattr(req, "get_method"):
            raise LiveShopifyBlocked("urlopen was not a Request: %r" % (req,))
        url = req.full_url
        method = req.get_method()
        host = urllib.parse.urlsplit(url).netloc
        if host != SHOP:
            raise LiveShopifyBlocked("blocked Shopify host %s %s" % (method, url))
        raw = req.data
        body = json.loads(raw.decode()) if raw else None
        self.calls.append({"method": method, "url": url, "body": body})
        path = urllib.parse.urlsplit(url).path
        article = {"id": self.article_id, "handle": self.article_handle}
        if method == "GET" and path.endswith("/blogs/%s.json" % BLOG_ID):
            return _Resp({"blog": {"id": int(BLOG_ID), "handle": self.blog_handle}})
        if method == "POST" and path.endswith("/blogs/%s/articles.json" % BLOG_ID):
            return _Resp({"article": dict(article, title=(body or {}).get("article", {}).get("title"))})
        if method == "DELETE" and path.endswith("/articles/%s.json" % self.article_id):
            return _Resp({})
        if method == "PUT" and path.endswith("/articles/%s.json" % self.article_id):
            sent = (body or {}).get("article") or {}
            return _Resp({"article": dict(article, handle=sent.get("handle") or self.article_handle)})
        if method == "GET" and path.endswith("/articles/%s/metafields.json" % self.article_id):
            return _Resp({"metafields": []})
        if method == "POST" and path.endswith("/articles/%s/metafields.json" % self.article_id):
            return _Resp({"metafield": {"id": 7, "namespace": "global", "key": "title_tag", "type": "string"}})
        if method == "GET" and path.endswith("/articles/%s.json" % self.article_id):
            return _Resp({"article": dict(article, body_html="<p>x</p>")})
        return _Resp({"article": article, "blog": {"handle": self.blog_handle}, "metafields": []})


class FirstPublishURL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="t29-first-publish-")
        cls.cfg = os.path.join(cls.tmpdir, "shopify_token.json")
        with open(cls.cfg, "w", encoding="utf-8") as handle:
            json.dump({"shop": SHOP, "access_token": "shpat_fixture_only"}, handle)
        cls._old_config = os.environ.get("GENSEO_CONFIG")
        if "shopify_publisher" not in sys.modules and "genseo_config" not in sys.modules:
            os.environ["GENSEO_CONFIG"] = cls.cfg
        import shopify_publisher as pub
        cls.pub = pub
        if cls._old_config is None:
            os.environ.pop("GENSEO_CONFIG", None)
        else:
            os.environ["GENSEO_CONFIG"] = cls._old_config

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def setUp(self):
        self.pub.CONFIG_PATH = self.cfg
        self.output = ""

    def _draft(self, text):
        path = os.path.join(self.tmpdir, "draft-%s.md" % uuid4().hex)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return path

    def _calls(self, fake):
        for call in fake.calls:
            self.assertTrue(call["url"].startswith("https://%s/" % SHOP), call["url"])
            self.assertNotIn("myshopify.com", call["url"])
        return [(call["method"], urllib.parse.urlsplit(call["url"]).path) for call in fake.calls]

    def _run(self, fake, path, live=False):
        buf = io.StringIO()
        try:
            with patch.object(self.pub.time, "sleep", lambda *_a, **_k: None), \
                 patch.object(self.pub.urllib.request, "urlopen", fake.urlopen), \
                 redirect_stdout(buf):
                self.pub.do_publish(path, BLOG_ID, live=live)
        finally:
            self.output = buf.getvalue()

    def _shell(self, fake):
        posts = [
            call for call in fake.calls
            if call["method"] == "POST" and call["url"].endswith("/articles.json")
        ]
        self.assertEqual(len(posts), 1, self._calls(fake))
        article = posts[0]["body"]["article"]
        self.assertIs(article["published"], False)
        self.assertNotIn("body_html", article)
        self.assertNotIn("handle", article)
        self.assertEqual(article["title"], "Morning Walk Notes")
        return article

    def _puts(self, fake):
        return [call for call in fake.calls if call["method"] == "PUT"]

    def test_reserve_uses_the_handle_shopify_returns(self):
        fake = ShopifyFake()
        with patch.object(self.pub.urllib.request, "urlopen", fake.urlopen):
            article_id, url, handle, blog = self.pub.reserve_first_publish_url(
                SHOP, "shpat_fixture_only", BLOG_ID, "Morning Walk Notes", "Wellness Nest Editorial Team")
        self.assertEqual(article_id, ARTICLE_ID)
        self.assertEqual(blog, BLOG_HANDLE)
        self.assertEqual(handle, RETURNED_HANDLE)
        self.assertNotEqual(handle, TITLE_SLUG)
        self.assertEqual(url, PUBLIC_URL)
        self._shell(fake)
        self.assertEqual([call["method"] for call in fake.calls], ["GET", "POST"])

    def test_publish_checks_jsonld_against_the_returned_url(self):
        fake = ShopifyFake()
        path = self._draft(_draft_text(PUBLIC_URL, byline=True))
        self._run(fake, path, live=False)
        self.assertIn("Article JSON-LD must match %s" % PUBLIC_URL, self.output)
        self.assertNotIn("/blogs/news/%s" % TITLE_SLUG, self.output)
        self._shell(fake)
        puts = self._puts(fake)
        self.assertEqual(len(puts), 1, self._calls(fake))
        article = puts[0]["body"]["article"]
        self.assertIs(article["published"], False)
        self.assertEqual(article["handle"], RETURNED_HANDLE)
        self.assertEqual(article["author"], "Mike Moretti")
        self.assertIn(PUBLIC_URL, article["body_html"])
        self.assertIn("selling_plan=123", article["body_html"])
        self.assertNotIn("utm_", article["body_html"])
        self.assertNotIn("variant", article["body_html"])
        self.assertNotIn(TITLE_SLUG + '"', article["body_html"])
        methods = [call["method"] for call in fake.calls]
        self.assertLess(methods.index("POST"), methods.index("PUT"))
        with open(path, encoding="utf-8") as handle:
            saved = handle.read()
        self.assertIn("selling_plan=123", saved)
        self.assertNotIn("utm_", saved)

    def test_live_flag_publishes_only_after_the_url_is_known(self):
        fake = ShopifyFake()
        path = self._draft(_draft_text(PUBLIC_URL))
        self._run(fake, path, live=True)
        self.assertIn(PUBLIC_URL, self.output)
        published_true = []
        for index, call in enumerate(fake.calls):
            article = (call["body"] or {}).get("article") if call["body"] else None
            if article and article.get("published") is True:
                published_true.append(index)
        self.assertEqual(len(published_true), 1, self._calls(fake))
        self.assertEqual(fake.calls[published_true[0]]["method"], "PUT")
        self.assertGreater(published_true[0], 1)
        self.assertIs(fake.calls[1]["body"]["article"]["published"], False)
        self.assertEqual(fake.calls[1]["method"], "POST")
        self.assertIn(PUBLIC_URL, fake.calls[published_true[0]]["body"]["article"]["body_html"])

    def test_title_slug_jsonld_is_rejected_and_not_published(self):
        fake = ShopifyFake()
        slug_url = "https://wellnessnest.co/blogs/%s/%s" % (BLOG_HANDLE, TITLE_SLUG)
        path = self._draft(_draft_text(slug_url))
        with self.assertRaises(SystemExit) as caught:
            self._run(fake, path, live=True)
        self.assertEqual(caught.exception.code, 2)
        self.assertIn(PUBLIC_URL, self.output)
        self.assertIn("ABORT", self.output)
        self._shell(fake)
        self.assertEqual(self._puts(fake), [])
        self.assertFalse(any(
            (call["body"] or {}).get("article", {}).get("published") is True
            for call in fake.calls if call["body"]
        ))
        methods = [call["method"] for call in fake.calls]
        self.assertEqual(methods, ["GET", "POST", "DELETE"])
        self.assertIn("/articles/%s.json" % ARTICLE_ID, fake.calls[-1]["url"])

    def test_locale_alias_of_the_same_article_stays_a_warning(self):
        fake = ShopifyFake()
        locale = "https://wellnessnest.co/fr/blogs/%s/%s" % (BLOG_HANDLE, RETURNED_HANDLE)
        path = self._draft(_draft_text(locale))
        self._run(fake, path, live=False)
        self.assertIn("locale-prefix", self.output)
        self.assertNotIn("ABORT", self.output)
        self.assertEqual(self._puts(fake)[0]["body"]["article"]["published"], False)
        self.assertIn("/fr/blogs/%s/%s" % (BLOG_HANDLE, RETURNED_HANDLE), self.output)
        self.assertNotIn("DELETE", [call["method"] for call in fake.calls])
        with open(path, encoding="utf-8") as handle:
            saved = handle.read()
        self.assertIn("selling_plan=123", saved)
        self.assertIn("/fr/blogs/%s/%s" % (BLOG_HANDLE, RETURNED_HANDLE), saved)

    def test_locale_alias_of_a_different_article_fails(self):
        fake = ShopifyFake()
        locale = "https://wellnessnest.co/fr/blogs/%s/other-article" % BLOG_HANDLE
        path = self._draft(_draft_text(locale))
        with self.assertRaises(SystemExit) as caught:
            self._run(fake, path, live=True)
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual([call["method"] for call in fake.calls], ["GET", "POST", "DELETE"])
        self.assertEqual(self._puts(fake), [])

    def test_homepage_identity_fails_before_any_shopify_call(self):
        fake = ShopifyFake()
        text = "\n".join([
            "# Morning Walk Notes",
            "",
            "A short note about a morning walk.",
            "",
            '<script type="application/ld+json">{"@type":"Article","mainEntityOfPage":"https://wellnessnest.co/"}</script>',
            "",
        ])
        path = self._draft(text)
        with self.assertRaises(SystemExit) as caught:
            self._run(fake, path, live=True)
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(fake.calls, [])
        self.assertIn("homepage", self.output)

    def test_unusable_article_handle_deletes_the_shell(self):
        fake = ShopifyFake(article_handle="not_a_handle")
        path = self._draft(_draft_text(PUBLIC_URL))
        with self.assertRaises(SystemExit) as caught:
            self._run(fake, path, live=True)
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("no deterministic article URL", self.output)
        self.assertEqual([call["method"] for call in fake.calls], ["GET", "POST", "DELETE"])
        self._shell(fake)
        self.assertEqual(self._puts(fake), [])

    def test_unusable_blog_handle_does_not_create(self):
        fake = ShopifyFake(blog_handle="News Blog")
        path = self._draft(_draft_text(PUBLIC_URL))
        with self.assertRaises(SystemExit) as caught:
            self._run(fake, path, live=True)
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual([call["method"] for call in fake.calls], ["GET"])
        self.assertIn("no deterministic article URL", self.output)


if __name__ == "__main__":
    unittest.main()

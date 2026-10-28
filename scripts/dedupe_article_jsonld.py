#!/usr/bin/env python3
"""Remove redundant Article JSON-LD from Shopify article bodies.

The theme main-article section already emits Article JSON-LD. Copies appended to
body_html are the duplicate. This script removes only those script blocks.
FAQPage blocks stay. Default is --dry-run. --apply writes to the live store and
was not run for the 2026-10-20 change.

Auth is scripts/shopify_publisher.py load_shop_auth(). Never print the token.

Usage:
  python3 scripts/dedupe_article_jsonld.py
  python3 scripts/dedupe_article_jsonld.py --dry-run --limit 5
  python3 scripts/dedupe_article_jsonld.py --exclude-handles handles.txt
  python3 scripts/dedupe_article_jsonld.py --apply --backup-dir DIR
  python3 scripts/dedupe_article_jsonld.py --restore DIR
  python3 scripts/dedupe_article_jsonld.py --restore DIR --apply
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

# Exact element the publisher appends. The first </script> closes it.
_SCRIPT_OPEN = '<script type="application/ld+json">'
_SCRIPT_CLOSE = "</script>"
_LDJSON_SCRIPT_RE = re.compile(
    r'<script type="application/ld\+json">.*?</script>',
    re.DOTALL,
)
_ARTICLE_TYPES = frozenset(("Article", "BlogPosting", "NewsArticle"))
_MIN_INTERVAL = 0.5  # at most ~2 Admin API requests/second
_BACKUP_KEYS = ("id", "handle", "blog_id", "body_html")


class ShopifyHttpError(Exception):
    def __init__(self, code, reason):
        self.code = code
        super().__init__("Shopify HTTP %s %s" % (code, reason))


def _is_article_type(value):
    """True when @type is Article, BlogPosting, NewsArticle, or a list of those."""
    if isinstance(value, str):
        return value in _ARTICLE_TYPES
    if isinstance(value, list):
        return any(isinstance(item, str) and item in _ARTICLE_TYPES for item in value)
    return False


def strip_article_jsonld(html):
    """Drop Article / BlogPosting / NewsArticle JSON-LD script blocks.

    Returns (html, removed_count). A block is removed only when its root JSON
    object has an article @type. An @graph array with no root @type stays.
    Malformed JSON stays. FAQPage and every other byte stay as they were.
    """
    if not isinstance(html, str):
        raise TypeError("body_html must be a str")
    removed = 0

    def replace(match):
        nonlocal removed
        block = match.group(0)
        inner = block[len(_SCRIPT_OPEN):-len(_SCRIPT_CLOSE)]
        try:
            data = json.loads(inner.strip())
        except json.JSONDecodeError:
            return block
        if isinstance(data, dict) and _is_article_type(data.get("@type")):
            removed += 1
            return ""
        return block

    return _LDJSON_SCRIPT_RE.sub(replace, html), removed


def backup_record(article, blog_id):
    """JSON object written to {id}.json before a PUT. body_html is the original."""
    return {
        "id": article["id"],
        "handle": article["handle"],
        "blog_id": blog_id,
        "body_html": article.get("body_html"),
    }


def _safe_id(value):
    if isinstance(value, bool) or value is None:
        raise ValueError("bad id")
    if isinstance(value, int):
        if value < 0:
            raise ValueError("bad id")
        return str(value)
    if isinstance(value, str) and value.isdigit():
        return value
    raise ValueError("bad id")


def write_backup(directory, record):
    """Create {id}.json exclusively. Refuses to overwrite an existing backup."""
    os.makedirs(directory, exist_ok=True)
    article_id = _safe_id(record["id"])
    path = os.path.join(directory, article_id + ".json")
    payload = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        raise FileExistsError("backup already exists for article %s" % article_id)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise
    return path


def load_backup(path):
    name = os.path.basename(path)
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("backup is not an object: %s" % name)
    for key in _BACKUP_KEYS:
        if key not in data:
            raise ValueError("backup missing %s: %s" % (key, name))
    try:
        if _safe_id(data["id"]) != os.path.splitext(name)[0]:
            raise ValueError("backup id does not match filename")
        _safe_id(data["blog_id"])
    except ValueError:
        raise ValueError("backup has a bad id: %s" % name)
    body = data["body_html"]
    if body is not None and not isinstance(body, str):
        raise ValueError("backup body_html is not a string: %s" % name)
    return data


def load_exclude(path):
    """Handles to skip, one per line. Blank lines and # comments are ignored."""
    if not path:
        return set()
    found = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            handle = line.strip()
            if not handle or handle.startswith("#"):
                continue
            found.add(handle)
    return found


def next_page_url(link_header):
    """Shopify Link header rel=next URL, or None. Refuses a non-https target."""
    if not link_header:
        return None
    for part in str(link_header).split(","):
        if 'rel="next"' not in part:
            continue
        start = part.find("<")
        end = part.find(">")
        if start == -1 or end <= start:
            continue
        url = part[start + 1:end]
        if not url.startswith("https://"):
            raise ValueError("pagination link is not https")
        return url
    return None


def retry_after_seconds(raw):
    """Seconds to wait after HTTP 429. Non-numeric Retry-After waits 2 seconds."""
    if raw is None or str(raw).strip() == "":
        return 2.0
    try:
        return max(0.0, float(str(raw).strip()))
    except ValueError:
        return 2.0


def _drain(err):
    try:
        err.read()
    except Exception:
        pass


class AdminClient:
    """Admin REST client. The token is not included in repr or error text."""

    def __init__(self, shop, token, api, min_interval=_MIN_INTERVAL):
        self.shop = shop
        self.api = api
        self._token = token
        self._min_interval = min_interval
        self._next_ok = 0.0

    def _pace(self):
        delay = self._next_ok - time.monotonic()
        if delay > 0:
            time.sleep(delay)

    def _mark(self):
        self._next_ok = time.monotonic() + self._min_interval

    def request(self, url, payload=None, method="GET"):
        data = None
        headers = {
            "X-Shopify-Access-Token": self._token,
            "Accept": "application/json",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        last_code = 429
        for attempt in range(6):
            self._pace()
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=90) as res:
                    raw = res.read()
                    link = res.headers.get("Link")
                self._mark()
            except urllib.error.HTTPError as err:
                _drain(err)
                self._mark()
                last_code = err.code
                if err.code == 429 and attempt < 5:
                    time.sleep(min(retry_after_seconds(err.headers.get("Retry-After")), 120.0))
                    continue
                raise ShopifyHttpError(err.code, getattr(err, "reason", "") or "") from None
            except urllib.error.URLError:
                self._mark()
                raise
            try:
                parsed = json.loads(raw.decode("utf-8")) if raw else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ShopifyHttpError(200, "response was not JSON") from None
            return parsed, link
        raise ShopifyHttpError(last_code, "retry limit reached")

    def put_body(self, blog_id, article_id, body_html):
        url = "https://%s/admin/api/%s/blogs/%s/articles/%s.json" % (
            self.shop, self.api, _safe_id(blog_id), _safe_id(article_id))
        data, _link = self.request(
            url,
            {"article": {"id": article_id, "body_html": body_html}},
            "PUT",
        )
        if not isinstance(data, dict) or "article" not in data:
            raise ShopifyHttpError(200, "update did not return an article")
        return data


def connect():
    """Same auth file as the publisher. Does not print the token."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import shopify_publisher
    shop, token = shopify_publisher.load_shop_auth()
    return shop, token, shopify_publisher.API


def iter_blogs(client):
    url = "https://%s/admin/api/%s/blogs.json?limit=250&fields=id,handle" % (
        client.shop, client.api)
    while url:
        data, link = client.request(url)
        if not isinstance(data, dict) or "blogs" not in data:
            raise ShopifyHttpError(200, "blog list missing")
        for blog in data["blogs"]:
            yield blog
        url = next_page_url(link)


def iter_articles(client, blog_id):
    # published_status=any includes drafts. The REST default is published only.
    url = (
        "https://%s/admin/api/%s/blogs/%s/articles.json"
        "?limit=250&published_status=any&fields=id,handle,body_html"
        % (client.shop, client.api, _safe_id(blog_id))
    )
    while url:
        data, link = client.request(url)
        if not isinstance(data, dict) or "articles" not in data:
            raise ShopifyHttpError(200, "article list missing")
        for article in data["articles"]:
            yield article
        url = next_page_url(link)


def _article_label(article):
    aid = article.get("id")
    if isinstance(aid, int) and not isinstance(aid, bool):
        return str(aid)
    return "unknown"


def scan(client, args, exclude):
    mode = "apply" if args.apply else "dry-run"
    scanned = matched = excluded = blogs = 0
    try:
        for blog in iter_blogs(client):
            blogs += 1
            blog_id = blog.get("id")
            for article in iter_articles(client, blog_id):
                if args.limit is not None and matched >= args.limit:
                    break
                scanned += 1
                handle = article.get("handle") or ""
                if handle in exclude:
                    excluded += 1
                    continue
                body = article.get("body_html")
                if not isinstance(body, str) or not body:
                    continue
                new_html, found = strip_article_jsonld(body)
                if not found:
                    continue
                again, leftover = strip_article_jsonld(new_html)
                if leftover or again != new_html:
                    print("refusing article %s: strip is not stable" % _article_label(article),
                          file=sys.stderr)
                    return 1
                if args.apply:
                    backed_up = False
                    try:
                        _safe_id(article.get("id"))
                        _safe_id(blog_id)
                        record = backup_record(article, blog_id)
                        record["body_html"] = body
                        write_backup(args.backup_dir, record)
                        backed_up = True
                        client.put_body(blog_id, article["id"], new_html)
                    except FileExistsError as exc:
                        print(exc, file=sys.stderr)
                        return 1
                    except ShopifyHttpError as exc:
                        tail = "; backup kept, live body not confirmed" if backed_up else ""
                        print("%s while updating article %s%s" % (exc, _article_label(article), tail),
                              file=sys.stderr)
                        return 1
                    except urllib.error.URLError:
                        tail = "; backup kept, live body not confirmed" if backed_up else ""
                        print("Shopify request failed (URLError) while updating article %s%s"
                              % (_article_label(article), tail), file=sys.stderr)
                        return 1
                    except OSError:
                        print("backup write failed for article %s" % _article_label(article),
                              file=sys.stderr)
                        return 1
                    except (ValueError, KeyError):
                        print("refusing article %s: backup record is incomplete" % _article_label(article),
                              file=sys.stderr)
                        return 1
                    action = "applied"
                else:
                    action = "dry-run"
                matched += 1
                print("%s\t%s\tblocks=%s\t%s" % (article.get("id"), handle, found, action))
            if args.limit is not None and matched >= args.limit:
                break
    except ShopifyHttpError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except urllib.error.URLError:
        print("Shopify request failed (URLError)", file=sys.stderr)
        return 1
    print("scanned=%s matched=%s excluded=%s blogs=%s mode=%s" % (
        scanned, matched, excluded, blogs, mode))
    return 0


def restore(client, args, exclude):
    mode = "restore" if args.apply else "restore-dry-run"
    names = sorted(
        name for name in os.listdir(args.restore) if re.fullmatch(r"\d+\.json", name)
    )
    matched = excluded = 0
    try:
        for name in names:
            if args.limit is not None and matched >= args.limit:
                break
            path = os.path.join(args.restore, name)
            record = load_backup(path)
            handle = record.get("handle") or ""
            if handle in exclude:
                excluded += 1
                continue
            if args.apply:
                client.put_body(record["blog_id"], record["id"], record["body_html"])
                action = "restored"
            else:
                action = "restore-dry-run"
            matched += 1
            print("%s\t%s\tblocks=backup\t%s" % (record["id"], handle, action))
    except (ShopifyHttpError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except urllib.error.URLError:
        print("Shopify request failed (URLError)", file=sys.stderr)
        return 1
    print("backups=%s matched=%s excluded=%s mode=%s" % (
        len(names), matched, excluded, mode))
    return 0


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Strip redundant Article JSON-LD from Shopify article body_html. "
                    "FAQPage stays. Default is dry-run. Does not print the access token."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="print id, handle, and Article blocks found (this is the default)")
    parser.add_argument("--apply", action="store_true",
                        help="PUT stripped body_html, or PUT backups when used with --restore")
    parser.add_argument("--backup-dir",
                        help="required with --apply (scan): write {id}.json before each PUT")
    parser.add_argument("--exclude-handles",
                        help="text file of handles to skip, one per line")
    parser.add_argument("--limit", type=int, default=None,
                        help="stop after N articles that have an Article block, or N backups")
    parser.add_argument("--restore", metavar="DIR",
                        help="read {id}.json backups; PUT body_html back only with --apply")
    return parser.parse_args(argv)


def validate_args(args):
    if args.dry_run and args.apply:
        return "pass either --dry-run or --apply"
    if args.limit is not None and args.limit < 1:
        return "--limit must be a positive integer"
    if args.backup_dir and args.restore:
        return "--backup-dir is not used with --restore"
    if args.backup_dir and not args.apply:
        return "--backup-dir is only used with --apply"
    if args.apply and not args.restore and not args.backup_dir:
        return "--backup-dir is required with --apply"
    if args.exclude_handles and not os.path.isfile(args.exclude_handles):
        return "exclude file not found"
    if args.restore and not os.path.isdir(args.restore):
        return "restore dir not found"
    return None


def main(argv=None):
    args = parse_args(argv)
    err = validate_args(args)
    if err:
        print(err, file=sys.stderr)
        return 2
    shop, token, api = connect()
    client = AdminClient(shop, token, api)
    exclude = load_exclude(args.exclude_handles)
    if args.restore:
        return restore(client, args, exclude)
    return scan(client, args, exclude)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""IndexNow pings for Wellness Nest article URLs.

Network happens only when a caller asks to send (a live publish/update, or
``--send``). A missing ``INDEXNOW_KEY`` skips with a log line. ``--dry-run`` and
``INDEXNOW_DRY_RUN=1`` build the JSON body and do not open a socket.

This module does not write the Shopify theme, pages, or robots.txt, and it does
not upload the key file. Hosting that file is a manual step — see
``docs/indexnow-and-llms-txt.md``.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_HOST = "wellnessnest.co"
DEFAULT_BLOG = "news"
DEFAULT_ENDPOINT = "https://api.indexnow.org/indexnow"
KEY_RE = re.compile(r"[A-Za-z0-9-]{8,128}")
HANDLE_RE = re.compile(r"[a-z0-9-]+")
HOST_RE = re.compile(r"[a-z0-9.-]+")
_TRUTHY = {"1", "true", "yes", "on"}


def _env(env, name, default=""):
    source = os.environ if env is None else env
    return (source.get(name) or default).strip()


def resolve_key(env=None):
    """Return INDEXNOW_KEY, or empty when unset / still a placeholder."""
    key = _env(env, "INDEXNOW_KEY")
    if not key or key.startswith("YOUR_"):
        return ""
    return key


def key_is_valid(key):
    return bool(key) and bool(KEY_RE.fullmatch(key))


def dry_run_enabled(env=None):
    return _env(env, "INDEXNOW_DRY_RUN").lower() in _TRUTHY


def skip_key_check_enabled(env=None):
    return _env(env, "INDEXNOW_SKIP_KEY_CHECK").lower() in _TRUTHY


def host_name(env=None):
    host = _env(env, "INDEXNOW_HOST", DEFAULT_HOST).lower()
    if not HOST_RE.fullmatch(host) or ".." in host:
        raise ValueError(f"INDEXNOW_HOST is not a bare hostname: {host!r}")
    return host


def endpoint_url(env=None):
    return _env(env, "INDEXNOW_ENDPOINT", DEFAULT_ENDPOINT) or DEFAULT_ENDPOINT


def key_location_for(key, env=None):
    host = host_name(env)
    explicit = _env(env, "INDEXNOW_KEY_LOCATION")
    loc = explicit or f"https://{host}/{key}.txt"
    parsed = urllib.parse.urlparse(loc)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("INDEXNOW_KEY_LOCATION must be an https URL on the store host, with no query or userinfo")
    if parsed.netloc.lower() != host:
        raise ValueError(
            f"INDEXNOW_KEY_LOCATION host must be {host} (IndexNow requires the key file on the same host)"
        )
    return loc


def article_url(article_handle, env=None):
    """Public article URL. The store has one blog, ``news``, unless INDEXNOW_BLOG_HANDLE overrides it."""
    handle = (article_handle or "").strip().strip("/")
    blog = _env(env, "INDEXNOW_BLOG_HANDLE", DEFAULT_BLOG)
    if not HANDLE_RE.fullmatch(handle):
        raise ValueError(f"refusing IndexNow URL for unexpected article handle: {article_handle!r}")
    if not HANDLE_RE.fullmatch(blog):
        raise ValueError(f"INDEXNOW_BLOG_HANDLE is not a handle: {blog!r}")
    return f"https://{host_name(env)}/blogs/{blog}/{handle}"


def assert_store_url(url, env=None):
    host = host_name(env)
    parsed = urllib.parse.urlparse((url or "").strip())
    if parsed.scheme != "https" or parsed.username or parsed.password:
        raise ValueError(f"IndexNow URL must be https://{host}/... without userinfo")
    if parsed.netloc.lower() != host:
        raise ValueError(f"IndexNow URL must be on {host}, got {url!r}")
    if not parsed.path or parsed.path == "/":
        raise ValueError(f"IndexNow URL needs a path: {url!r}")
    return urllib.parse.urlunsplit(("https", host, parsed.path, "", ""))


def build_payload(urls, env=None):
    key = resolve_key(env)
    clean = [assert_store_url(u, env) for u in urls if u]
    if not clean:
        raise ValueError("IndexNow urlList is empty")
    if len(clean) > 10000:
        raise ValueError("IndexNow accepts at most 10000 URLs per request")
    return {
        "host": host_name(env),
        "key": key,
        "keyLocation": key_location_for(key, env),
        "urlList": clean,
    }


def plan(urls, env=None, force_dry_run=False):
    """Decide skip / dry-run / invalid / send. No I/O."""
    key = resolve_key(env)
    if not key:
        return {
            "action": "skip",
            "payload": None,
            "status": None,
            "message": (
                "IndexNow Auto-Ping: SKIPPED (INDEXNOW_KEY is not set; no request sent). "
                "Host the key file and export INDEXNOW_KEY before a live publish will ping. "
                "See docs/indexnow-and-llms-txt.md."
            ),
        }
    if not key_is_valid(key):
        return {
            "action": "invalid",
            "payload": None,
            "status": None,
            "message": (
                "IndexNow Auto-Ping: SKIPPED (INDEXNOW_KEY must be 8–128 characters "
                f"of [A-Za-z0-9-]; got length {len(key)}. No request sent)."
            ),
        }
    try:
        payload = build_payload(urls, env)
    except ValueError as exc:
        return {
            "action": "invalid",
            "payload": None,
            "status": None,
            "message": f"IndexNow Auto-Ping: SKIPPED ({exc}). No request sent.",
        }
    if force_dry_run or dry_run_enabled(env):
        shown = dict(payload)
        return {
            "action": "dry-run",
            "payload": payload,
            "status": None,
            "message": (
                "IndexNow Auto-Ping: DRY-RUN (no request sent). "
                f"endpoint={endpoint_url(env)} body={json.dumps(shown, sort_keys=True)}"
            ),
        }
    return {"action": "send", "payload": payload, "status": None, "message": ""}


def _read(res):
    try:
        raw = res.read()
        code = res.getcode()
    finally:
        close = getattr(res, "close", None)
        if close:
            close()
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", "replace")
    else:
        text = raw or ""
    return code, text


def _open(opener, req):
    fn = opener or urllib.request.urlopen
    try:
        return fn(req, timeout=20)
    except TypeError:
        return fn(req)


def preflight_key_file(payload, opener=None):
    """GET the key file. IndexNow will reject the ping unless the body is the key."""
    loc = payload["keyLocation"]
    req = urllib.request.Request(loc, method="GET", headers={"User-Agent": "GenSeo-IndexNow/1.0"})
    try:
        res = _open(opener, req)
    except urllib.error.HTTPError as exc:
        return False, f"key file {loc} returned HTTP {exc.code}; no IndexNow POST"
    except Exception as exc:
        return False, f"key file {loc} was not fetched ({exc}); no IndexNow POST"
    code, text = _read(res)
    body = text.strip().lstrip("\ufeff")
    if code != 200 or body != payload["key"]:
        return False, (
            f"key file {loc} did not return the key as the entire body (HTTP {code}); "
            "no IndexNow POST. Host the file first — see docs/indexnow-and-llms-txt.md."
        )
    return True, ""


def post_payload(payload, opener=None, env=None):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint_url(env),
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "GenSeo-IndexNow/1.0"},
        method="POST",
    )
    res = _open(opener, req)
    code, _text = _read(res)
    if code not in (200, 202):
        raise RuntimeError(f"IndexNow HTTP {code}")
    return code


def execute(urls, env=None, opener=None, force_dry_run=False, force_send=False):
    """Print one log line and return the plan result. POST only when action is send."""
    if force_send and (force_dry_run or dry_run_enabled(env)):
        message = "IndexNow Auto-Ping: SKIPPED (--send ignored because INDEXNOW_DRY_RUN or --dry-run is set)."
        print(message)
        return {"action": "skip", "payload": None, "status": None, "message": message}
    planned = plan(urls, env=env, force_dry_run=force_dry_run and not force_send)
    if planned["action"] != "send":
        print(planned["message"])
        return planned
    try:
        if not skip_key_check_enabled(env):
            ok, why = preflight_key_file(planned["payload"], opener=opener)
            if not ok:
                message = f"IndexNow Auto-Ping: SKIPPED ({why})"
                print(message)
                return {
                    "action": "skip",
                    "payload": planned["payload"],
                    "status": None,
                    "message": message,
                }
        code = post_payload(planned["payload"], opener=opener, env=env)
    except Exception as exc:
        message = f"IndexNow Auto-Ping: FAILED -> {exc}"
        print(message)
        return {"action": "failed", "payload": planned["payload"], "status": None, "message": message}
    n = len(planned["payload"]["urlList"])
    target = planned["payload"]["urlList"][0] if n == 1 else f"{n} URLs"
    message = f"IndexNow Auto-Ping: SUCCESS ({code}) for {target}"
    print(message)
    return {"action": "send", "payload": planned["payload"], "status": code, "message": message}


def self_check():
    """In-process smoke test. Does not open a socket."""
    calls = []

    def _boom(*_a, **_k):
        calls.append(1)
        raise AssertionError("network opener was called")

    skipped = execute(["https://wellnessnest.co/blogs/news/example"], env={}, opener=_boom)
    if skipped["action"] != "skip" or calls:
        raise SystemExit("self-check failed: missing key should skip with no network")
    env = {
        "INDEXNOW_KEY": "abcdef0123456789",
        "INDEXNOW_DRY_RUN": "1",
    }
    dry = execute(
        ["https://wellnessnest.co/blogs/news/example"],
        env=env,
        opener=_boom,
    )
    if dry["action"] != "dry-run" or calls or dry["payload"]["keyLocation"] != (
        "https://wellnessnest.co/abcdef0123456789.txt"
    ):
        raise SystemExit("self-check failed: dry-run payload")
    if "urolithin" in json.dumps(dry["payload"]).lower():
        raise SystemExit("self-check failed: unexpected payload text")
    print("IndexNow self-check: PASS (no network)")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--self-check" in argv:
        return self_check()
    if "--send" in argv and "--dry-run" in argv:
        print("Pass only one of --dry-run or --send. Nothing was sent.", file=sys.stderr)
        return 2
    force_send = "--send" in argv
    force_dry = "--dry-run" in argv or not force_send
    urls = []
    args = [a for a in argv if a not in ("--send", "--dry-run")]
    i = 0
    while i < len(args):
        if args[i] == "--url" and i + 1 < len(args):
            urls.append(args[i + 1])
            i += 2
            continue
        print(f"Unknown argument: {args[i]}", file=sys.stderr)
        print("Usage: python3 scripts/indexnow_ping.py [--dry-run|--send] --url https://wellnessnest.co/...", file=sys.stderr)
        return 2
    if not urls:
        print("Pass --url, or run --self-check. Nothing was sent.", file=sys.stderr)
        return 2
    result = execute(urls, force_dry_run=force_dry and not force_send, force_send=force_send)
    if result["action"] == "failed":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

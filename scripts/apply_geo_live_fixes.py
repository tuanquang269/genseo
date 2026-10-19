#!/usr/bin/env python3
"""Show or materialize the prepared GEO fixes for already-live articles.

Reads docs/geo-live-fixes-2026-10-19.json. The default is a dry run: GET the
public page, extract the article body, and print a unified diff. Nothing is
written.

  python3 scripts/apply_geo_live_fixes.py
  python3 scripts/apply_geo_live_fixes.py --ticket CA1009-1

  python3 scripts/apply_geo_live_fixes.py --apply

--apply writes the patched article body (and a one-line title file when the
title changes) under docs/geo-live-fixes-out/. That directory is local. This
script does not call the Shopify Admin API, does not publish, and does not
edit the live page. A future store update is a separate decision.

--html-dir DIR reads DIR/<ticket>.html instead of the network (tests).
--offline skips the optional re-check of source URLs.
"""
import argparse
import difflib
import html as htmlmod
import json
import os
import re
import sys
import urllib.request

import florafresh_rules
import geo_citability

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_FIXES = os.path.join(ROOT, "docs", "geo-live-fixes-2026-10-19.json")
DEFAULT_OUT = os.path.join(ROOT, "docs", "geo-live-fixes-out")
_UA = geo_citability._UA
_SUFFIX = " – Wellness Nest"


class ApplyError(Exception):
    pass


def load_fixes(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data.get("posts"), list):
        raise ApplyError("fixes file has no posts list")
    return data


def fetch_page(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        status = getattr(resp, "status", None) or resp.getcode()
        body = resp.read().decode("utf-8", "replace")
    return int(status), body


def h1_text(page):
    match = re.search(r"<h1[^>]*>(.*?)</h1>", page or "", re.I | re.S)
    if not match:
        return ""
    text = re.sub(r"<[^>]+>", "", match.group(1))
    return re.sub(r"\s+", " ", htmlmod.unescape(text)).strip()


def extract_article_body(page):
    """The article body inside itemprop=articleBody, including its wrapper div."""
    marker = page.find('itemprop="articleBody"')
    if marker < 0:
        raise ApplyError("no itemprop=articleBody on the page")
    start = page.rfind("<div", 0, marker)
    if start < 0:
        raise ApplyError("articleBody has no opening div")
    pos = start
    depth = 0
    while pos < len(page):
        open_at = page.find("<div", pos)
        close_at = page.find("</div>", pos)
        if close_at < 0:
            break
        if open_at != -1 and open_at < close_at:
            depth += 1
            pos = open_at + 4
        else:
            depth -= 1
            pos = close_at + 6
            if depth == 0:
                return page[start:pos]
    raise ApplyError("articleBody div did not close")


def apply_replacements(html, replacements):
    updated = html
    for rep in replacements:
        find = rep["find"]
        count = int(rep.get("count", 1))
        found = updated.count(find)
        kind = rep.get("kind", "replace")
        if found != count:
            raise ApplyError(
                f"{kind}: expected {count} match(es), found {found}"
            )
        updated = updated.replace(find, rep["replace"])
    return updated


def title_tag_length(h1, suffix=_SUFFIX):
    return len(h1) + len(suffix)


def _diff(before, after, label):
    lines = list(difflib.unified_diff(
        before.splitlines(),
        after.splitlines(),
        fromfile=label + ".live",
        tofile=label + ".patched",
        lineterm="",
    ))
    return "\n".join(lines)


_JSONLD = re.compile(
    r"(?is)<script\b[^>]*type\s*=\s*[\"']application/ld\+json[\"'][^>]*>(.*?)</script>"
)


def jsonld_blocks(body):
    return [match.group(1).strip() for match in _JSONLD.finditer(body or "")]


def check_jsonld(ticket, before, after):
    """A snippet that also lives in a JSON-LD string must not break that script.

    Visible HTML and the FAQ JSON mirror often share a sentence. A replacement
    that inserts href=\"...\" into the mirror splits the JSON string. Single
    quotes in the attribute keep both copies valid.
    """
    before_blocks = jsonld_blocks(before)
    after_blocks = jsonld_blocks(after)
    if len(before_blocks) != len(after_blocks):
        raise ApplyError(ticket + ": patch changed the JSON-LD script count")
    for index, (old, new) in enumerate(zip(before_blocks, after_blocks), start=1):
        if old == new:
            continue
        try:
            json.loads(new)
        except json.JSONDecodeError as exc:
            raise ApplyError(
                "%s: patched JSON-LD block %s does not parse (%s)"
                % (ticket, index, exc.msg)
            )


def check_clean(ticket, body):
    fails, _warns = geo_citability.assess(body, require_meta=False)
    flora = florafresh_rules.violations(body)
    problems = [f"gate: {item}" for item in fails] + [f"florafresh: {item}" for item in flora]
    if problems:
        raise ApplyError(ticket + " still fails after the patch: " + "; ".join(problems[:6]))


def recheck_sources(posts):
    """GET/HEAD each distinct source_url once. 404/410 fails the run."""
    seen = []
    for post in posts:
        for rep in post.get("replacements") or []:
            url = rep.get("source_url")
            if url and url not in seen:
                seen.append(url)
    bad = []
    for url in seen:
        status, loop = geo_citability.fetch_status(url)
        print(f"source {status} {url}")
        if loop or status in (404, 410) or (500 <= status <= 599 and status != 503):
            bad.append(f"{status} {url}")
    if bad:
        raise ApplyError("source URL check failed: " + "; ".join(bad))


def render_post(post, page):
    ticket = post["ticket"]
    body = extract_article_body(page)
    patched = apply_replacements(body, post.get("replacements") or [])
    if patched != body:
        check_jsonld(ticket, body, patched)
    if post.get("expect_clean", True) and post.get("replacements"):
        check_clean(ticket, patched)
    title = post.get("title")
    live_h1 = h1_text(page)
    title_block = ""
    if title:
        if live_h1 != title["from"]:
            raise ApplyError(
                f"{ticket}: live H1 {live_h1!r} != fixes from {title['from']!r}"
            )
        new = title["to"]
        if title_tag_length(new) > 70:
            raise ApplyError(f"{ticket}: proposed title tag is {title_tag_length(new)} (>70)")
        title_block = (
            f"TITLE {ticket}\n"
            f"- {title['from']}  (tag {title_tag_length(title['from'])})\n"
            f"+ {new}  (tag {title_tag_length(new)})\n"
        )
    body_diff = _diff(body, patched, ticket) if patched != body else ""
    return {
        "ticket": ticket,
        "title_block": title_block,
        "body_diff": body_diff,
        "patched": patched,
        "title_to": title["to"] if title else None,
        "changed": bool(title_block or body_diff),
    }


def write_local(result, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    body_path = os.path.join(out_dir, result["ticket"] + ".body.html")
    with open(body_path, "w", encoding="utf-8") as fh:
        fh.write(result["patched"])
    written = [body_path]
    if result["title_to"]:
        title_path = os.path.join(out_dir, result["ticket"] + ".title.txt")
        with open(title_path, "w", encoding="utf-8") as fh:
            fh.write(result["title_to"] + "\n")
        written.append(title_path)
    return written


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixes", default=DEFAULT_FIXES)
    parser.add_argument("--ticket", action="append", default=[])
    parser.add_argument("--apply", action="store_true",
                        help="write patched HTML under docs/geo-live-fixes-out/ (local only)")
    parser.add_argument("--out-dir", default=DEFAULT_OUT)
    parser.add_argument("--html-dir", default="",
                        help="read <dir>/<ticket>.html instead of fetching")
    parser.add_argument("--offline", action="store_true",
                        help="do not re-check source URLs")
    args = parser.parse_args(argv)
    data = load_fixes(args.fixes)
    posts = data["posts"]
    if args.ticket:
        wanted = set(args.ticket)
        posts = [p for p in posts if p["ticket"] in wanted]
        missing = wanted - {p["ticket"] for p in posts}
        if missing:
            raise ApplyError("unknown ticket(s): " + ", ".join(sorted(missing)))
    if not posts:
        raise ApplyError("no posts selected")

    mode = "LOCAL APPLY (files only, no Shopify)" if args.apply else "DRY RUN (no files, no Shopify)"
    print(mode)
    print(f"fixes: {args.fixes}")
    print(f"posts: {len(posts)}")

    if not args.offline and not args.html_dir:
        recheck_sources(posts)

    results = []
    for post in posts:
        ticket = post["ticket"]
        if args.html_dir:
            path = os.path.join(args.html_dir, ticket + ".html")
            with open(path, encoding="utf-8") as fh:
                page = fh.read()
            print(f"\n=== {ticket} local {path} ===")
        else:
            status, page = fetch_page(post["url"])
            print(f"\n=== {ticket} HTTP {status} {post['url']} ===")
            if status != 200:
                raise ApplyError(f"{ticket}: page HTTP {status}")
        result = render_post(post, page)
        if result["title_block"]:
            print(result["title_block"].rstrip())
        if result["body_diff"]:
            print(result["body_diff"])
        elif not result["title_block"]:
            raise ApplyError(f"{ticket}: patch made no difference")
        else:
            print("(no body change)")
        results.append(result)

    if args.apply:
        print("\nWriting local files. Live pages were not edited.")
        for result in results:
            for path in write_local(result, args.out_dir):
                print("  wrote", path)
    else:
        print("\nDry run only. Re-run with --apply to write local files. Live pages were not edited.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except ApplyError as exc:
        print("ERROR:", exc, file=sys.stderr)
        sys.exit(1)

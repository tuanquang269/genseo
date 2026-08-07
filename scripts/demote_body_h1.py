#!/usr/bin/env python3
"""Demote the duplicate <h1> inside article body_html to <h2>.

The blog template already emits the article title as the page h1
(`article-template__title`). 153 of 704 published articles ALSO open their body
with an h1 repeating that same title, so every one of those pages renders the
same heading twice at h1 level.

Scope is deliberately narrow: only the first body h1, and only when its text
matches the article title. Articles whose body h1 says something *different* are
reported, not touched — changing a heading that carries its own text is an
editorial call, not a mechanical one.

Reversible: every edit records the exact original open/close tags in
backups/<date>/h1_demote_log.json.

ponytail: string surgery on the first h1 rather than an HTML parser. The input is
Shopify body_html, the target is one tag pair, and a parser would rewrite the
whole document on the way out — which is a much bigger diff to trust.

Usage:
    python3 scripts/demote_body_h1.py --selftest
    python3 scripts/demote_body_h1.py --dry-run
    python3 scripts/demote_body_h1.py --apply
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CONFIG = os.path.expanduser("~/.genseo/shopify_token.json")
API_VERSION = "2026-04"
BLOGS = {104008483131: "news"}

with open(CONFIG) as handle:
    CFG = json.load(handle)
SHOP, TOKEN = CFG["shop"], CFG["access_token"]
HDR = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}

OPEN_RE = re.compile(r"<h1\b([^>]*)>", re.I)
CLOSE_RE = re.compile(r"</h1\s*>", re.I)


def strip_tags(markup):  # not named `html` — that would shadow the stdlib module
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", markup)).strip()


def first_h1(body):
    """(open_start, open_end, close_start, close_end, inner_text) of the first h1."""
    om = OPEN_RE.search(body)
    if not om:
        return None
    cm = CLOSE_RE.search(body, om.end())
    if not cm:
        return None
    return om.start(), om.end(), cm.start(), cm.end(), strip_tags(body[om.end():cm.start()])


def demote(body, attrs_keep=True):
    """Rewrite only the first h1 pair to h2, preserving its attributes."""
    found = first_h1(body)
    if not found:
        return body, None
    o_s, o_e, c_s, c_e, _ = found
    attrs = OPEN_RE.match(body, o_s).group(1) if attrs_keep else ""
    original = (body[o_s:o_e], body[c_s:c_e])
    new = body[:o_s] + f"<h2{attrs}>" + body[o_e:c_s] + "</h2>" + body[c_e:]
    return new, original


def titles_match(h1_text, title):
    # Entities must be decoded first: body_html carries "Sleep &amp; Recovery" while
    # the title field carries "Sleep & Recovery", and stripping punctuation turns the
    # entity into a bare "amp" token that makes identical headings look different.
    norm = lambda s: re.sub(r"[^a-z0-9]+", " ", html.unescape(s).lower()).strip()
    a, b = norm(h1_text), norm(title)
    return bool(a) and (a == b or a[:60] == b[:60])


def api(path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"https://{SHOP}/admin/api/{API_VERSION}/{path}",
                                 data=data, method=method, headers=HDR)
    return json.loads(urllib.request.urlopen(req, timeout=45).read())


def all_articles():
    out = []
    for blog in BLOGS:
        url = (f"https://{SHOP}/admin/api/{API_VERSION}/blogs/{blog}/articles.json"
               f"?limit=250&fields=id,handle,title,body_html&published_status=published")
        while url:
            resp = urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=60)
            for art in json.loads(resp.read())["articles"]:
                out.append((blog, art["id"], art["handle"], art["title"], art.get("body_html") or ""))
            url = None
            for part in resp.headers.get("Link", "").split(","):
                if 'rel="next"' in part:
                    url = part[part.find("<") + 1:part.find(">")]
    return out


def selftest():
    body = '<h1 class="t" id="x">Expired Protein Powder</h1><p>hi</p><h2>Sub</h2>'
    new, orig = demote(body)
    assert new == '<h2 class="t" id="x">Expired Protein Powder</h2><p>hi</p><h2>Sub</h2>', new
    assert orig == ('<h1 class="t" id="x">', '</h1>'), orig
    assert new.count("<h1") == 0 and new.count("</h1>") == 0

    # only the FIRST h1 is touched — a second one is a separate editorial decision
    two = "<h1>A</h1><p>x</p><h1>B</h1>"
    new2, _ = demote(two)
    assert new2 == "<h2>A</h2><p>x</p><h1>B</h1>", new2

    # inner markup survives
    inner = "<h1>Whey <em>Isolate</em> Guide</h1>"
    assert demote(inner)[0] == "<h2>Whey <em>Isolate</em> Guide</h2>"
    assert first_h1(inner)[4] == "Whey Isolate Guide"

    # no h1 at all is a no-op, not a crash
    assert demote("<p>none</p>") == ("<p>none</p>", None)
    # unclosed h1 must be left alone rather than half-rewritten
    assert demote("<h1>oops<p>x</p>") == ("<h1>oops<p>x</p>", None)

    assert titles_match("Expired Protein Powder!", "expired protein powder")
    assert not titles_match("Best Creatine", "Best Whey Protein")
    # the entity bug the first dry-run exposed: 16 identical headings looked different
    assert titles_match("NOW Magnesium: SG Sleep &amp; Recovery Guide (2026)",
                        "NOW Magnesium: SG Sleep & Recovery Guide (2026)")
    assert titles_match("Alive Men&rsquo;s Multivitamin", "Alive Men\u2019s Multivitamin")
    print("selftest OK")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not (args.apply or args.dry_run):
        parser.error("pass --dry-run, --apply or --selftest")

    arts = all_articles()
    hits, different, log = [], [], []
    for blog, aid, handle, title, body in arts:
        found = first_h1(body)
        if not found:
            continue
        if titles_match(found[4], title):
            hits.append((blog, aid, handle, title, body))
        else:
            different.append((handle, found[4][:70], title[:60]))

    print(f"{len(arts)} published articles")
    print(f"  {len(hits)} with a body h1 duplicating the title  -> demote to h2")
    print(f"  {len(different)} with a body h1 saying something else -> REPORTED ONLY\n")

    for handle, h1text, title in different:
        print(f"   report  {handle[:46]:48} h1={h1text!r}")

    if args.dry_run:
        for _, _, handle, _, _ in hits[:10]:
            print(f"   demote  {handle[:60]}")
        print(f"   ... and {max(0, len(hits) - 10)} more")
        return 0

    for i, (blog, aid, handle, _, body) in enumerate(hits, 1):
        new, orig = demote(body)
        if orig is None or new == body:
            print(f"SKIP {handle}: nothing changed", file=sys.stderr)
            continue
        api(f"blogs/{blog}/articles/{aid}.json", method="PUT",
            payload={"article": {"id": aid, "body_html": new}})
        log.append({"id": aid, "handle": handle, "blog": BLOGS[blog],
                    "open_tag": orig[0], "close_tag": orig[1]})
        if i % 25 == 0:
            print(f"   {i}/{len(hits)}")
        time.sleep(0.55)

    out = BASE / "backups" / datetime.date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    (out / "h1_demote_log.json").write_text(json.dumps(log, indent=2))
    print(f"\napplied: {len(log)} article(s) demoted\nlog: {out / 'h1_demote_log.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

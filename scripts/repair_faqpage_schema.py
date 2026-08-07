#!/usr/bin/env python3
"""Repair the invalid FAQPage JSON-LD on 32 published articles.

The article pipeline built each `FAQPage` block by serialising the visible Q&A, including an
"About the Author" entry whose answer contains the author bio *plus a whole nested*
`<script type="application/ld+json">…</script>`. A literal `</script>` inside a JSON string closes
the script element for every HTML parser, so the block is truncated on the live page and the FAQPage
is invalid — Google sees no FAQ markup at all. Confirmed by fetching the pages: the truncation is real,
not an artefact of how we read them.

All 32 share one shape (1 `<h2>Frequently Asked Questions</h2>`, 1 `<h3>About the Author</h3>`,
exactly 1 broken block), so the repair is mechanical: rebuild `mainEntity` from the visible h3+p pairs
with any nested script stripped, and drop "About the Author" — a bio is not a question, and it is the
sole reason the block broke.

The visible HTML is not touched. Only the schema block is rewritten.

Usage:
    python3 scripts/repair_faqpage_schema.py --dry-run
    python3 scripts/repair_faqpage_schema.py --apply
    python3 scripts/repair_faqpage_schema.py --apply --limit 3      # canary first
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import sys
import time
import urllib.request

CONFIG = os.path.expanduser("~/.genseo/shopify_token.json")
API = "2026-04"
BASE = pathlib.Path(__file__).resolve().parent.parent
TARGETS = BASE / "backups" / "2026-08-05" / "faqpage_repair_targets.json"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
AUTH = json.load(open(CONFIG))
SHOP, TOKEN = AUTH["shop"], AUTH["access_token"]
HDR = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}
BLOG_ID = {"nutrition": 100000000001, "training": 100000000002}
LDJSON = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


def api(path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"https://{SHOP}/admin/api/{API}/{path}",
                                 data=data, method=method, headers=HDR)
    return json.loads(urllib.request.urlopen(req, timeout=90).read())


def parses(raw):
    try:
        json.loads(raw)
        return True
    except Exception:
        return False


def visible_faq(body):
    """(question, answer_html) per h3+p pair under the FAQ h2, excluding the author bio."""
    start = body.find("<h2>Frequently Asked Questions</h2>")
    if start < 0:
        return []
    out = []
    for m in re.finditer(r"<h3>(.*?)</h3>\s*<p>(.*?)</p>", body[start:], re.S):
        q = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
        if q.lower().startswith("about the author"):
            continue
        out.append((q, m.group(2)))
    return out


def faq_schema(pairs):
    def clean(html):
        # the whole point: no nested script tag may survive into a JSON string
        html = re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)
        return re.sub(r"\s+", " ", html).strip()
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": clean(a)}}
                       for q, a in pairs],
    }, indent=2, ensure_ascii=False)


def repair(body):
    """Return (new_body, question_count) or (None, reason)."""
    pairs = visible_faq(body)
    if len(pairs) < 2:
        return None, f"only {len(pairs)} visible FAQ pair(s)"
    blocks = LDJSON.findall(body)
    broken = [b for b in blocks if not parses(b)]
    # A block can be valid JSON and still wrong: if the bio had no nested script the FAQPage parses
    # but carries "About the Author" as a Question. Same defect, same rebuild.
    bio_q = [b for b in blocks if parses(b)
             and json.loads(b).get("@type") == "FAQPage"
             and any("about the author" in q.get("name", "").lower()
                     for q in json.loads(b).get("mainEntity", []))]
    if not broken and not bio_q:
        return None, "no broken block"
    if len(broken) + len(bio_q) != 1:
        return None, f"{len(broken)} broken + {len(bio_q)} bio-question blocks, expected 1 total"
    stale = set(broken) | set(bio_q)
    schema = faq_schema(pairs)
    if "</script" in schema:
        return None, "rebuilt schema still contains a script terminator"
    new = LDJSON.sub(
        lambda m: (f'<script type="application/ld+json">\n{schema}\n</script>'
                   if m.group(1) in stale else m.group(0)), body)
    after = LDJSON.findall(new)
    if any(not parses(b) for b in after):
        return None, "a block is still broken after repair"
    if '"@type": "FAQPage"' not in new:
        return None, "FAQPage missing after repair"
    return new, len(pairs)


def live_ok(blog, handle):
    url = f"https://yourdomain.com/blogs/{blog}/{handle}?nc={int(time.time())}"
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45)
    if r.status != 200:
        return False, f"HTTP {r.status}"
    html = r.read().decode("utf-8", "replace")
    blocks = LDJSON.findall(html)
    bad = [b for b in blocks if not parses(b)]
    types = [json.loads(b).get("@type") for b in blocks if parses(b)]
    if bad:
        return False, f"{len(bad)} broken block(s) still on the page"
    if "FAQPage" not in types:
        return False, f"no valid FAQPage; types={types}"
    n = len(json.loads(next(b for b in blocks if '"FAQPage"' in b))["mainEntity"])
    return True, f"{len(blocks)} valid blocks, FAQPage with {n} questions"


def selftest():
    # the already-repaired Impact Whey hub must now pass, and its FAQPage must be valid
    body = api("blogs/100000000001/articles/100000000099.json")["article"]["body_html"]
    assert all(parses(b) for b in LDJSON.findall(body)), "the reference article is broken"
    assert repair(body)[0] is None, "repair() should refuse an already-valid article"
    # a synthetic broken block must be detected and repaired
    fake = ('<h2>Frequently Asked Questions</h2><h3>Q one?</h3><p>A one.</p>'
            '<h3>Q two?</h3><p>A two.</p><h3>About the Author</h3><p>Bio.</p>'
            '<script type="application/ld+json">\n{"@type":"FAQPage","mainEntity":[{"text":"'
            '<script type=\\"application/ld+json\\">{}</script>"}\n</script>')
    out, n = repair(fake)
    assert out and n == 2, f"synthetic repair failed: {out and n}"
    got = json.loads(next(b for b in LDJSON.findall(out) if '"FAQPage"' in b))
    assert [q["name"] for q in got["mainEntity"]] == ["Q one?", "Q two?"], got
    assert "About the Author" not in out.split("application/ld+json")[-1]
    print("selftest OK — refuses valid articles, repairs a synthetic broken one, drops the bio")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, help="stop after N articles (canary run)")
    a = ap.parse_args()
    if not (a.apply or a.dry_run):
        ap.error("pass --dry-run or --apply")
    selftest()

    targets = json.loads(TARGETS.read_text())
    if a.limit:
        targets = targets[:a.limit]
    print(f"\n{len(targets)} article(s) targeted\n")

    out = BASE / "backups" / datetime.date.today().isoformat()
    plan, skipped = [], []
    for t in targets:
        art = api(f"blogs/{BLOG_ID[t['blog']]}/articles/{t['id']}.json")["article"]
        new, res = repair(art["body_html"])
        if new is None:
            skipped.append((t["handle"], res))
            continue
        plan.append((t, art, new, res))

    for t, art, _, n in plan:
        print(f"   {n} questions  {t['blog']:9} {t['handle'][:66]}")
    if skipped:
        print(f"\nskipped {len(skipped)}:")
        for h, why in skipped:
            print(f"   {why:42} {h[:56]}")
    if a.dry_run:
        print(f"\ndry-run: {len(plan)} would be repaired, {len(skipped)} skipped")
        return 0
    if not plan:
        print("nothing to do")
        return 0

    out.mkdir(parents=True, exist_ok=True)
    # A canary run (--limit 3) backs up 3 bodies; the full run then plans only the remaining 29,
    # so writing the file fresh would DROP the canary's pre-edit bodies and leave those three
    # unrevertable. Merge, and never overwrite an existing entry — the earliest capture is the
    # only one that predates any edit.
    backup_path = out / "faqpage_repair_backup.json"
    entries = {}
    if backup_path.is_file():
        entries = {e["handle"]: e for e in json.loads(backup_path.read_text())}
    for t, art, _, _ in plan:
        entries.setdefault(t["handle"], {"handle": t["handle"], "blog": t["blog"],
                                        "id": t["id"], "body_html": art["body_html"]})
    backup_path.write_text(json.dumps(list(entries.values()), indent=1))
    print(f"\nbackup: {backup_path} ({len(entries)} bodies)")

    written, errs = 0, []
    for t, art, new, n in plan:
        try:
            api(f"blogs/{BLOG_ID[t['blog']]}/articles/{t['id']}.json", "PUT",
                {"article": {"id": t["id"], "body_html": new}})
            written += 1
        except Exception as exc:
            errs.append((t["handle"], f"{type(exc).__name__}: {exc}"))
        time.sleep(0.35)
    print(f"wrote {written}/{len(plan)}, {len(errs)} write error(s)")

    print("\nverifying live...")
    time.sleep(5)
    good, bad = 0, []
    for t, _, _, _ in plan:
        try:
            ok, detail = live_ok(t["blog"], t["handle"])
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        if ok:
            good += 1
        else:
            bad.append((t["handle"], detail))
        time.sleep(1.2)

    log_path = out / "faqpage_repair_log.json"
    runs = json.loads(log_path.read_text()).get("runs", []) if log_path.is_file() else []
    runs.append({"written": written, "verified": good, "write_errors": errs,
                 "verify_failures": bad, "skipped": skipped})
    log_path.write_text(json.dumps({"runs": runs,
                                    "total_verified": sum(r["verified"] for r in runs)}, indent=1))
    print(f"verified live: {good}/{len(plan)}")
    for h, why in bad:
        print(f"   FAIL {h[:56]}: {why}", file=sys.stderr)
    print(f"log: {out / 'faqpage_repair_log.json'}")
    return 1 if (bad or errs) else 0


if __name__ == "__main__":
    sys.exit(main())

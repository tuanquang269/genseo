#!/usr/bin/env python3
"""Add outbound citations to the top articles by SG impressions (ACTION-PLAN 2.2).

The corpus makes nutrition and health claims with zero external links. In a YMYL
vertical that is the cheapest remaining E-E-A-T and AI-citability gap.

**Every source below was verified live before being written into this file, and is
verified again over HTTP on every run** — a source that stops resolving is dropped
rather than published. That guard exists because the failure mode here is not a bug,
it is a fabricated PMID or DOI, which is worse than no citation at all.

What this does NOT do: per-claim inline citation. Matching an individual sentence to
an individual study needs a human read of each article; doing it by model is exactly
how invented references get shipped. This appends a topic-matched References block,
which is honest about being general background.

ponytail: topic detection is keyword matching on title+body, not a classifier. It
misfires toward *fewer* citations (unmatched article gets only the HSA link), which
is the safe direction. Upgrade only if the miss rate actually matters.

Usage:
    python3 scripts/add_outbound_citations.py --dry-run [--limit 40]
    python3 scripts/add_outbound_citations.py --apply [--limit 40]
"""
import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gsc_fetcher import get_service

BASE = Path(__file__).resolve().parent.parent
CONFIG = os.path.expanduser("~/.genseo/shopify_token.json")
API_VERSION = "2026-04"
BLOGS = {104008483131: "news"}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
MARKER = "<!-- genseo-sources -->"
MAX_LINKS = 4

# key -> (url, anchor text, publisher, substring that must appear in the live page)
SOURCES = {
    "fda": ("https://www.fda.gov/food/dietary-supplements",
            "Dietary Supplements — FDA guidance",
            "U.S. Food and Drug Administration", "dietary supplement"),
    "issn_protein": ("https://jissn.biomedcentral.com/articles/10.1186/s12970-017-0177-8",
                     "ISSN Position Stand: Protein and Exercise",
                     "Journal of the International Society of Sports Nutrition", "protein"),
    "pubmed_permeal": ("https://pubmed.ncbi.nlm.nih.gov/29497353/",
                       "How much protein can the body use in a single meal?",
                       "PubMed", "protein"),
    "medline_protein": ("https://medlineplus.gov/dietaryproteins.html",
                        "Dietary proteins", "MedlinePlus, U.S. National Library of Medicine", "protein"),
    "issn_creatine": ("https://jissn.biomedcentral.com/articles/10.1186/s12970-017-0173-z",
                      "ISSN Position Stand: Safety and Efficacy of Creatine Supplementation",
                      "Journal of the International Society of Sports Nutrition", "creatine"),
    "issn_caffeine": ("https://jissn.biomedcentral.com/articles/10.1186/s12970-020-00383-4",
                      "ISSN Position Stand: Caffeine and Exercise Performance",
                      "Journal of the International Society of Sports Nutrition", "caffeine"),
    "issn_betaalanine": ("https://jissn.biomedcentral.com/articles/10.1186/s12970-015-0090-y",
                         "ISSN Position Stand: Beta-Alanine",
                         "Journal of the International Society of Sports Nutrition", "beta-alanine"),
    "issn_hmb": ("https://jissn.biomedcentral.com/articles/10.1186/1550-2783-10-6",
                 "ISSN Position Stand: Beta-Hydroxy-Beta-Methylbutyrate (HMB)",
                 "Journal of the International Society of Sports Nutrition", "hmb"),
    "issn_timing": ("https://jissn.biomedcentral.com/articles/10.1186/s12970-017-0189-4",
                    "ISSN Position Stand: Nutrient Timing",
                    "Journal of the International Society of Sports Nutrition", "nutrient timing"),
    "pmc_recovery": ("https://pmc.ncbi.nlm.nih.gov/articles/PMC5852800/",
                     "Post-exercise muscle protein remodeling",
                     "PubMed Central", "muscle protein"),
    "nccih_omega3": ("https://www.nccih.nih.gov/health/omega3-supplements-in-depth",
                     "Omega-3 supplements: what you need to know",
                     "U.S. National Center for Complementary and Integrative Health", "omega-3"),
    "nccih_probiotics": ("https://www.nccih.nih.gov/health/probiotics-what-you-need-to-know",
                         "Probiotics: usefulness and safety",
                         "U.S. National Center for Complementary and Integrative Health", "probiotic"),
    "nccih_melatonin": ("https://www.nccih.nih.gov/health/melatonin-what-you-need-to-know",
                        "Melatonin: what you need to know",
                        "U.S. National Center for Complementary and Integrative Health", "melatonin"),
    "nccih_ashwagandha": ("https://www.nccih.nih.gov/health/ashwagandha",
                          "Ashwagandha: usefulness and safety",
                          "U.S. National Center for Complementary and Integrative Health", "ashwagandha"),
    "medline_supp": ("https://medlineplus.gov/dietarysupplements.html",
                     "Dietary supplements", "MedlinePlus, U.S. National Library of Medicine", "supplement"),
}

# ordered: first match wins the top slots. HSA is appended to every article because
# every one of these pages sells into US.
TOPICS = [
    (r"\bcreatine\b|creakong|crea-8", ["issn_creatine"]),
    (r"beta[- ]?alanine|carnosine", ["issn_betaalanine"]),
    (r"\bhmb\b|hydroxy.?methylbutyrate", ["issn_hmb"]),
    (r"pre[- ]?workout|caffeine|energy drink", ["issn_caffeine"]),
    (r"omega[- ]?3|fish oil|\bepa\b|\bdha\b", ["nccih_omega3"]),
    (r"probiotic|gut health|digest|\bibs\b", ["nccih_probiotics"]),
    (r"sleep|melatonin|insomnia|recovery at night", ["nccih_melatonin"]),
    (r"ashwagandha|ksm-?66|adaptogen", ["nccih_ashwagandha"]),
    (r"intra[- ]?workout|post[- ]?workout|nutrient timing|\beaa\b|\bbcaa\b",
     ["issn_timing", "pmc_recovery"]),
    (r"multivitamin|immun|vitamin [cd]\b|\bzinc\b", ["medline_supp"]),
    (r"protein|whey|isolate|casein|amino", ["issn_protein", "pubmed_permeal", "medline_protein"]),
]

with open(CONFIG) as handle:
    CFG = json.load(handle)
SHOP, TOKEN = CFG["shop"], CFG["access_token"]
HDR = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}


def api(path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"https://{SHOP}/admin/api/{API_VERSION}/{path}",
                                 data=data, method=method, headers=HDR)
    return json.loads(urllib.request.urlopen(req, timeout=45).read())


def verify_sources():
    """Re-check every source over HTTP. A source that 404s or drifts is dropped."""
    live = {}
    for key, (url, anchor, publisher, must) in SOURCES.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            if resp.status == 200 and must.lower() in body.lower():
                live[key] = (url, anchor, publisher)
            else:
                print(f"  DROP {key}: status={resp.status} topic-match={must.lower() in body.lower()}",
                      file=sys.stderr)
        except Exception as exc:
            print(f"  DROP {key}: {type(exc).__name__}: {exc}", file=sys.stderr)
        time.sleep(0.6)
    return live


def top_articles(limit):
    svc = get_service()
    end = datetime.date.today() - datetime.timedelta(days=2)
    start = end - datetime.timedelta(days=90)
    rows = svc.searchanalytics().query(siteUrl="https://wellnessnest.co/", body={
        "startDate": str(start), "endDate": str(end), "dimensions": ["page"],
        "dimensionFilterGroups": [{"filters": [
            {"dimension": "country", "operator": "equals", "expression": "usa"}]}],
        "rowLimit": 25000}).execute().get("rows", [])
    scored = {}
    for row in rows:
        url = row["keys"][0]
        if "/blogs/" not in url or "#" in url:  # anchor rows are the same page
            continue
        handle = url.rstrip("/").split("/")[-1]
        scored[handle] = scored.get(handle, 0) + int(row["impressions"])
    return sorted(scored.items(), key=lambda kv: -kv[1])[:limit]


def shopify_articles():
    idx = {}
    for blog in BLOGS:
        url = (f"https://{SHOP}/admin/api/{API_VERSION}/blogs/{blog}/articles.json"
               f"?limit=250&fields=id,handle,title,body_html&published_status=published")
        while url:
            resp = urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=60)
            for art in json.loads(resp.read())["articles"]:
                idx[art["handle"]] = (blog, art["id"], art["title"], art.get("body_html") or "")
            url = None
            for part in resp.headers.get("Link", "").split(","):
                if 'rel="next"' in part:
                    url = part[part.find("<") + 1:part.find(">")]
    return idx


def has_outbound(body):
    """External links already present, ignoring our own domain and social profiles."""
    skip = ("wellnessnest.co", "facebook.com", "instagram.com", "tiktok.com",
            "youtube.com", "twitter.com", "x.com", "shopify.com", "cdn.shopify")
    for href in re.findall(r'href="(https?://[^"]+)"', body, re.I):
        if not any(s in href.lower() for s in skip):
            return True
    return False


def prose(body):
    """Article prose with link text removed.

    The hub-and-spoke internal-link boxes we added earlier name every category we
    sell, so matching raw body_html made a water-bottle guide look like it was about
    creatine and caffeine. Anchor text is navigation, not subject matter — drop it.
    """
    body = re.sub(r"<a\b[^>]*>.*?</a>", " ", body, flags=re.S | re.I)
    body = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", body, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", body).lower()


def pick(title, body, live):
    """Score every topic, then take the strongest — no early exit.

    Title evidence outweighs body evidence 10:1: an article is about what its title
    says it is about, and a passing mention in the prose is not a topic.
    """
    head, text = title.lower(), prose(body)[:20000]
    scored = []
    for pattern, want in TOPICS:
        in_title = len(re.findall(pattern, head))
        if not in_title:
            # Body evidence alone is not enough. A shaker-bottle guide says "protein"
            # a dozen times without being about protein science, and citing a position
            # stand there is a worse signal than citing nothing.
            continue
        scored.append((in_title * 10 + min(len(re.findall(pattern, text)), 6), want))
    scored.sort(key=lambda s: -s[0])
    if not scored:
        # No topic in the title: fall back to the general dietary-supplement reference
        # rather than guessing. Fewer, right citations beat more, wrong ones.
        scored = [(0, ["medline_supp"])]

    keys = []
    for _, want in scored:
        for k in want:
            if k in live and k not in keys:
                keys.append(k)
        if len(keys) >= MAX_LINKS - 1:
            break
    keys = keys[:MAX_LINKS - 1]
    if "hsa" in live:
        keys.append("hsa")
    return keys


def block(keys, live):
    items = "".join(
        f'\n    <li><a href="{live[k][0]}" target="_blank" rel="noopener">{live[k][1]}</a>'
        f" &mdash; {live[k][2]}</li>"
        for k in keys)
    return (f'\n{MARKER}\n<section class="genseo-sources">\n'
            f"  <h2>Sources &amp; further reading</h2>\n"
            f"  <p>Nutrition, dosing and safety guidance in this guide is grounded in the "
            f"following independent sources. Product-specific figures come from the "
            f"manufacturer&rsquo;s own label.</p>\n  <ul>{items}\n  </ul>\n</section>\n")


def selftest():
    """The failure this guards: a water-bottle guide cited as a caffeine study.

    Runs offline against a fake `live` map, so it needs no network and no Shopify.
    """
    live = {k: (v[0], v[1], v[2]) for k, v in SOURCES.items()}
    linkbox = ('<div><a href="/collections/creatine">Creatine</a>'
               '<a href="/collections/pre-workout">Pre-Workout caffeine</a>'
               '<a href="/collections/probiotics">gut health digest</a></div>')

    # A shaker guide whose prose is full of "protein" must NOT be cited as protein science.
    bottle = "<p>Shakers and bottles for your protein shake. Protein powder fits. Protein.</p>"
    got = pick("The Ultimate Owala US Store Guide 2026", bottle + linkbox, live)
    assert got == ["medline_supp", "hsa"], f"body words leaked into a bottle guide: {got}"

    got = pick("1 Scoop of Whey: How Many Calories and Protein?",
               "<p>Whey protein per scoop. Protein quality and protein content.</p>" + linkbox, live)
    assert "issn_protein" in got, f"protein article missed protein sources: {got}"
    assert "nccih_melatonin" not in got and "issn_caffeine" not in got, f"junk topics: {got}"

    got = pick("7 Best Creatine Supplements US", "<p>creatine monohydrate creatine loading</p>", live)
    assert got[0] == "issn_creatine", f"creatine article ranked wrong: {got}"

    got = pick("Best Sleeping Supplement in the US", "<p>sleep quality, melatonin dosage</p>", live)
    assert "nccih_melatonin" in got, f"sleep article missed melatonin: {got}"

    assert all(g[-1] == "hsa" for g in [got]), "HSA must always be last"
    print("selftest OK")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not (args.apply or args.dry_run):
        parser.error("pass --dry-run, --apply or --selftest")

    print("Verifying source URLs...")
    live = verify_sources()
    print(f"{len(live)}/{len(SOURCES)} sources live\n")
    if "hsa" not in live:
        print("FAIL: the HSA source did not verify; refusing to run.", file=sys.stderr)
        return 1

    tops = top_articles(args.limit)
    idx = shopify_articles()
    frozen = set()
    ff = BASE / "frozen_articles.txt"
    if ff.exists():
        frozen = {l.split("#")[0].strip() for l in ff.read_text().splitlines() if l.split("#")[0].strip()}

    done, skipped, log = 0, [], []
    for handle, imp in tops:
        if handle not in idx:
            skipped.append((handle, imp, "not a published article"))
            continue
        blog, aid, title, body = idx[handle]
        if MARKER in body:
            skipped.append((handle, imp, "already has a sources block"))
            continue
        if has_outbound(body):
            skipped.append((handle, imp, "already cites an external source"))
            continue
        keys = pick(title, body, live)
        if len(keys) < 2:
            skipped.append((handle, imp, f"only {len(keys)} source matched"))
            continue
        print(f"{imp:6d} imp  {handle[:58]:60} {', '.join(keys)}")
        if args.apply:
            if str(aid) in frozen:
                # frozen protects TITLE/meta; body append is what the money-page fix used
                print("          (frozen id — body append only, title untouched)")
            api(f"blogs/{blog}/articles/{aid}.json", method="PUT",
                payload={"article": {"id": aid, "body_html": body + block(keys, live)}})
            log.append({"handle": handle, "id": aid, "blog": BLOGS[blog],
                        "imp": imp, "sources": keys})
            time.sleep(0.6)
        done += 1

    if args.apply and log:
        out = BASE / "backups" / datetime.date.today().isoformat()
        out.mkdir(parents=True, exist_ok=True)
        (out / "citations_log.json").write_text(json.dumps(log, indent=2))
        print(f"\nlog: {out / 'citations_log.json'}")

    print(f"\n{'applied' if args.apply else 'dry-run'}: {done} article(s) cited, {len(skipped)} skipped")
    for handle, imp, why in skipped[:20]:
        print(f"   skip {imp:6d} imp  {handle[:52]:54} {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

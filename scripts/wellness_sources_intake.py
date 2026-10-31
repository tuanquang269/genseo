#!/usr/bin/env python3
"""Daily intake of authoritative wellness sources for Wellness Nest clusters.

Reads PubMed (E-utilities esearch + esummary), NIH ODS fact sheets, and optional
health news RSS. If NCBI returns a block page, the same queries are read from
Europe PMC MEDLINE records. Polite: identifying User-Agent, robots.txt, and a delay.
Writes ~/PATI/LLM-Wiki/90-sources/wellness-intake/YYYY-MM-DD.md plus a state JSON.

  python3 scripts/wellness_sources_intake.py --dry-run
  python3 scripts/wellness_sources_intake.py --fixtures tests/fixtures/geo_clusters/intake.json --out-dir /tmp/out --state /tmp/state.json
No Shopify writes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wn_clusters as wc

UA = "Mozilla/5.0 (compatible; WellnessNest-GEO-Intake/1.0; +https://wellnessnest.co; research reading)"
TOOL = "wellnessnest_geo"
EMAIL = "support@wellnessnest.co"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT = os.path.expanduser(os.environ.get("GENSEO_VAULT", "~/PATI/LLM-Wiki"))
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

PUBMED_QUERIES = [
    "shilajit",
    "nicotinamide mononucleotide supplementation",
    "NAD supplementation aging",
    "trimethylglycine supplementation",
    "Bacillus coagulans",
    "vaginal probiotics",
    "healthy aging NAD",
]
# Title must name the ingredient. Abstract-only hits pull in unrelated papers.
TITLE_OK = {
    "shilajit": re.compile(r"shilajit|mumio|mumie|moomiyo|asphaltum", re.I),
    "nicotinamide mononucleotide supplementation": re.compile(r"nicotinamide mononucleotide|\bnmn\b", re.I),
    "NAD supplementation aging": re.compile(r"\bnad\b|nicotinamide|\bnmn\b", re.I),
    "trimethylglycine supplementation": re.compile(r"trimethylglycine|\btmg\b|\bbetaine\b", re.I),
    "Bacillus coagulans": re.compile(r"bacillus coagulans|weizmannia coagulans", re.I),
    "vaginal probiotics": re.compile(r"probiotic", re.I),
    "healthy aging NAD": re.compile(r"\bnad\b|nicotinamide|\bnmn\b", re.I),
}
QUERY_CLUSTER = {
    "shilajit": "shilajit",
    "nicotinamide mononucleotide supplementation": "ageaura-nmn",
    "NAD supplementation aging": "ageaura-nmn",
    "trimethylglycine supplementation": "ageaura-nmn",
    "Bacillus coagulans": "florafresh",
    "vaginal probiotics": "florafresh",
    "healthy aging NAD": "ageaura-nmn",
}
DROP_TITLE = re.compile(
    r"\brabbits?\b|\bpoultry\b|\bbroiler\b|fattening|glioblastoma|zebrafish|"
    r"one-pot|secretome|nanoparticle",
    re.I,
)
ODS_URLS = [
    "https://ods.od.nih.gov/factsheets/list-all/",
    "https://ods.od.nih.gov/factsheets/Probiotics-Consumer/",
    "https://ods.od.nih.gov/factsheets/Probiotics-HealthProfessional/",
]
RSS_URLS = [
    "https://www.nih.gov/news-events/news-releases/feed",
    "https://www.sciencedaily.com/rss/health_medicine.xml",
]
RSS_KEEP = re.compile(
    r"shilajit|nmn|\bnad\b|nicotinamide|\btmg\b|trimethylglycine|betaine|"
    r"probiotic|bacillus|coagulans|vaginal",
    re.I,
)
TAG_RX = re.compile(r"<[^>]+>")


def sha256_text(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def robots_decision(robots_txt, url, ua=UA):
    """Return (allowed, crawl_delay_seconds). Unreadable robots allows the URL."""
    import urllib.robotparser
    rp = urllib.robotparser.RobotFileParser()
    rp.parse((robots_txt or "").splitlines())
    try:
        allowed = rp.can_fetch(ua, url)
    except Exception:
        allowed = True
    delay = None
    try:
        delay = rp.crawl_delay(ua) or rp.crawl_delay("*")
    except Exception:
        delay = None
    return allowed, float(delay or 0)


def strip_html(text):
    text = TAG_RX.sub(" ", text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def pubmed_esearch_url(term, retmax, reldate):
    params = {
        "db": "pubmed",
        "term": term,
        "retmax": str(retmax),
        "retmode": "json",
        "sort": "pub_date",
        "datetype": "edat",
        "reldate": str(reldate),
        "tool": TOOL,
        "email": EMAIL,
    }
    return EUTILS + "esearch.fcgi?" + urllib.parse.urlencode(params)


def pubmed_esummary_url(pmids):
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
        "tool": TOOL,
        "email": EMAIL,
    }
    return EUTILS + "esummary.fcgi?" + urllib.parse.urlencode(params)


def ncbi_html_block(body):
    text = body or ""
    head = text.lstrip()[:80].lower()
    sample = text[:4000].lower()
    return head.startswith("<") or "blocked diagnostic" in sample or "access denied" in sample


def parse_esearch(body):
    """Return (pmids, error). An HTML block page is an error, not an empty result."""
    if ncbi_html_block(body):
        return [], "NCBI block page"
    try:
        data = json.loads(body)
    except ValueError:
        return [], "not-json"
    result = data.get("esearchresult")
    if not isinstance(result, dict):
        return [], "no esearchresult"
    if result.get("ERROR"):
        return [], str(result.get("ERROR"))[:160]
    return list(result.get("idlist") or []), None


def europepmc_url(term, retmax):
    tokens = [
        tok for tok in re.findall(r"[A-Za-z0-9+]+", term)
        if len(tok) >= 3 and tok.lower() not in {"and", "the", "for", "with"}
    ]
    parts = []
    for tok in tokens:
        parts.append("(TITLE:%s OR ABSTRACT:%s)" % (tok, tok))
    if not parts:
        parts.append("(TITLE:%s OR ABSTRACT:%s)" % (term, term))
    query = "(" + " AND ".join(parts) + ") AND SRC:MED"
    params = {
        "query": query,
        "format": "json",
        "pageSize": str(min(20, max(int(retmax) * 8, int(retmax)))),
        "sort": "P_PDATE_D desc",
        "resultType": "core",
    }
    return "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(params)


def clean_text(text):
    text = html.unescape(text or "")
    text = strip_html(text)
    return re.sub(r"\s+", " ", text).strip()


def title_ok(term, title):
    if DROP_TITLE.search(title or ""):
        return False
    if term == "vaginal probiotics" and not re.search(r"vaginal", title or "", re.I):
        return False
    rule = TITLE_OK.get(term)
    if rule is None:
        return True
    return bool(rule.search(title or ""))


def parse_europepmc(body, term, limit=3):
    if ncbi_html_block(body):
        return [], "html-block"
    try:
        data = json.loads(body)
    except ValueError:
        return [], "not-json"
    rows = ((data.get("resultList") or {}).get("result")) or []
    if isinstance(rows, dict):
        rows = [rows]
    items = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if (row.get("source") or "MED") not in ("MED", "PMC"):
            continue
        pmid = str(row.get("pmid") or "").strip()
        title = clean_text(row.get("title") or "")
        if not pmid or not title or not title_ok(term, title):
            continue
        journal = clean_text(row.get("journalTitle") or "")
        if not journal:
            info = ((row.get("journalInfo") or {}).get("journal") or {})
            journal = clean_text(info.get("title") or "")
        names = []
        author_list = (row.get("authorList") or {}).get("author") or []
        if isinstance(author_list, dict):
            author_list = [author_list]
        for author in author_list[:3]:
            if isinstance(author, dict) and author.get("fullName"):
                names.append(author["fullName"])
        if not names and row.get("authorString"):
            names = [part.strip() for part in str(row["authorString"]).split(",")[:3] if part.strip()]
        items.append({
            "pmid": pmid,
            "title": title,
            "journal": journal,
            "date": row.get("firstPublicationDate") or row.get("pubYear") or "",
            "authors": ", ".join(names),
            "via": "europepmc",
            "query_cluster": QUERY_CLUSTER.get(term) or "",
        })
        if len(items) >= limit:
            break
    return items, None


def parse_esummary(body):
    try:
        data = json.loads(body)
    except ValueError:
        return []
    result = data.get("result") or {}
    uids = result.get("uids") or []
    items = []
    for uid in uids:
        row = result.get(uid) or {}
        if not isinstance(row, dict) or row.get("error"):
            continue
        authors = row.get("authors") or []
        names = []
        if isinstance(authors, list):
            for author in authors[:3]:
                if isinstance(author, dict) and author.get("name"):
                    names.append(author["name"])
        title = clean_text(row.get("title") or "")
        items.append({
            "pmid": str(uid),
            "title": title,
            "journal": row.get("fulljournalname") or row.get("source") or "",
            "date": row.get("pubdate") or row.get("sortpubdate") or "",
            "authors": ", ".join(names),
        })
    return items


def highlight_pubmed(item):
    who = item.get("authors") or "authors not listed"
    return (
        "%s. %s, %s. %s. Cluster: %s. Open the PubMed record before any article cites it."
        % (
            item["title"].rstrip("."),
            item.get("journal") or "journal not listed",
            item.get("date") or "date not listed",
            who,
            item.get("cluster") or "other",
        )
    )


def parse_rss(body, limit=8):
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return []
    items = []
    for node in root.iter("item"):
        title = _text(node, "title")
        link = _text(node, "link")
        summary = strip_html(_text(node, "description"))[:400]
        blob = title + " " + summary
        if not RSS_KEEP.search(blob):
            continue
        items.append({
            "title": title,
            "url": link,
            "summary": summary,
            "date": _text(node, "pubDate"),
        })
        if len(items) >= limit:
            break
    return items


def _text(node, tag):
    el = node.find(tag)
    if el is None or el.text is None:
        return ""
    return re.sub(r"\s+", " ", el.text).strip()


def ods_highlight(url, text, previous_hash):
    plain = strip_html(text)
    digest = sha256_text(plain)
    mentions = [w for w in ("shilajit", "NMN", "NAD", "TMG", "probiotic", "Bacillus") if w.lower() in plain.lower()]
    status = "seen"
    if not previous_hash:
        status = "new"
    elif previous_hash != digest:
        status = "changed"
    title = "NIH ODS"
    m = re.search(r"<title>(.*?)</title>", text or "", re.I | re.S)
    if m:
        title = strip_html(m.group(1))[:160]
    mention = ", ".join(mentions) if mentions else "none of the watched terms"
    highlight = "%s. Watched terms on the page: %s. Status: %s." % (title, mention, status)
    return {
        "url": url,
        "title": title,
        "text_hash": digest,
        "status": status,
        "highlight": highlight,
        "cluster": wc.assign_cluster(title + " " + plain[:500]),
    }


def classify_status(key, digest, state):
    prev = (state.get("items") or {}).get(key) or {}
    if not prev:
        return "new"
    if prev.get("sha256") != digest:
        return "changed"
    return "seen"


def render_note(day, pubmed, ods, rss, skipped):
    lines = []
    body = []
    body.append("# Wellness source intake %s" % day)
    body.append("")
    body.append(
        "Polite read of PubMed, NIH Office of Dietary Supplements fact sheets, and optional health news. "
        "Each item is assigned to a Wellness Nest topic cluster. This note is not a claim to publish. "
        "A writer opens the source and logs it before citing a number or a mechanism."
    )
    body.append("")
    body.append("## PubMed")
    body.append("")
    if not pubmed:
        body.append("No PubMed records in this run.")
        body.append("")
    for cluster in _group(pubmed):
        body.append("### %s" % cluster)
        body.append("")
        for item in _group(pubmed)[cluster]:
            body.append("- **Highlight:** %s" % item["highlight"])
            body.append("  - PMID: %s" % item["pmid"])
            body.append("  - Status: %s" % item["status"])
            body.append("  - URL: %s" % item["url"])
            body.append("")
    body.append("## NIH ODS")
    body.append("")
    if not ods:
        body.append("No ODS pages in this run.")
        body.append("")
    for item in ods:
        body.append("- **Highlight:** %s" % item["highlight"])
        body.append("  - Cluster: %s" % item.get("cluster"))
        body.append("  - URL: %s" % item["url"])
        body.append("")
    body.append("## News")
    body.append("")
    if not rss:
        body.append("No matching news items.")
        body.append("")
    for item in rss:
        body.append("- **Highlight:** %s Cluster: %s. Open the article before citing it." % (
            item["title"].rstrip("."), item.get("cluster") or "other",
        ))
        if item.get("summary"):
            body.append("  - Page excerpt: %s" % item["summary"][:280])
        body.append("  - Status: %s" % item.get("status"))
        body.append("  - URL: %s" % item.get("url"))
        body.append("")
    if skipped:
        body.append("## Skipped")
        body.append("")
        for line in skipped:
            body.append("- %s" % line)
        body.append("")
    body.append("## Counts")
    body.append("")
    body.append("- PubMed items: %s" % len(pubmed))
    body.append("- ODS pages: %s" % len(ods))
    body.append("- News items: %s" % len(rss))
    body.append("")
    text = "\n".join(body)
    digest = sha256_text(text)
    lines.append("---")
    lines.append("source_url: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi")
    lines.append("ingested: %s" % day)
    lines.append("sha256: %s" % digest)
    lines.append("tags: [brand, compliance]")
    lines.append("---")
    lines.append("")
    lines.append(text)
    return "\n".join(lines) + "\n", digest


def _group(items):
    out = {}
    for item in items:
        out.setdefault(item.get("cluster") or "other", []).append(item)
    return out


def items_from_fixture(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data


def live_pubmed(getter, retmax, reldate, skipped):
    """PubMed E-utilities first. Europe PMC MEDLINE records if NCBI returns a block page."""
    pmids = []
    fallback_rows = []
    noted = False
    for term in PUBMED_QUERIES:
        url = pubmed_esearch_url(term, retmax, reldate)
        status, body, err = getter(url)
        ids, perr = ([], err or ("HTTP %s" % status)) if (err or status != 200) else parse_esearch(body)
        if perr:
            if not noted:
                skipped.append(
                    "PubMed E-utilities unavailable (%s). Using Europe PMC MEDLINE records for the same queries."
                    % perr
                )
                noted = True
            status2, body2, err2 = getter(europepmc_url(term, retmax))
            if err2 or status2 != 200:
                skipped.append("Europe PMC failed for %s (%s)" % (term, err2 or status2))
                continue
            rows, eerr = parse_europepmc(body2, term, retmax)
            if eerr:
                skipped.append("Europe PMC unreadable for %s (%s)" % (term, eerr))
                continue
            fallback_rows.extend(rows)
        else:
            pmids.extend(ids)
    uniq = []
    seen = set()
    for pmid in pmids:
        if pmid not in seen:
            seen.add(pmid)
            uniq.append(pmid)
    summarized = []
    if uniq:
        status, body, err = getter(pubmed_esummary_url(uniq[:40]))
        if err or status != 200 or ncbi_html_block(body):
            skipped.append("PubMed esummary failed (%s)" % (err or status or "NCBI block page"))
        else:
            summarized = parse_esummary(body)
    have = {row["pmid"] for row in summarized}
    for row in fallback_rows:
        if row["pmid"] in have:
            continue
        have.add(row["pmid"])
        summarized.append(row)
    return summarized


def decorate_pubmed(rows, state):
    items = []
    for row in rows:
        cluster = wc.assign_cluster(row["title"])
        if cluster == "other" and row.get("query_cluster"):
            cluster = row["query_cluster"]
        row = dict(row, cluster=cluster)
        digest = sha256_text("|".join([row["title"], row["journal"], row["date"]]))
        key = "pubmed:" + row["pmid"]
        status = classify_status(key, digest, state)
        url = "https://pubmed.ncbi.nlm.nih.gov/%s/" % row["pmid"]
        item = dict(row, url=url, status=status, sha256=digest, kind="pubmed", id=key)
        item["highlight"] = highlight_pubmed(item)
        items.append(item)
    return items


def decorate_rss(rows, state):
    items = []
    for row in rows:
        cluster = wc.assign_cluster((row.get("title") or "") + " " + (row.get("summary") or ""))
        digest = sha256_text((row.get("title") or "") + "|" + (row.get("url") or ""))
        key = "rss:" + digest[:16]
        status = classify_status(key, digest, state)
        items.append(dict(row, cluster=cluster, status=status, sha256=digest, kind="rss", id=key))
    return items


def update_state(state, day, pubmed, ods, rss):
    items = dict(state.get("items") or {})
    for item in pubmed + rss:
        prev = items.get(item["id"]) or {}
        items[item["id"]] = {
            "sha256": item["sha256"],
            "title": item.get("title") or "",
            "cluster": item.get("cluster") or "",
            "url": item.get("url") or "",
            "kind": item.get("kind") or "",
            "first_seen": prev.get("first_seen") or day,
            "last_seen": day,
        }
    ods_state = dict(state.get("ods") or {})
    for item in ods:
        prev = ods_state.get(item["url"]) or {}
        ods_state[item["url"]] = {
            "sha256": item["text_hash"],
            "title": item.get("title") or "",
            "last_seen": day,
            "last_changed": day if item["status"] in ("new", "changed") else prev.get("last_changed") or day,
        }
    return {"updated": day, "items": items, "ods": ods_state}


class PoliteClient:
    def __init__(self, delay, max_crawl_delay, sleeper, opener):
        self.delay = delay
        self.max_crawl_delay = max_crawl_delay
        self.sleeper = sleeper
        self.opener = opener
        self.hosts = {}
        self.skipped = []

    def _host(self, url):
        parts = urllib.parse.urlparse(url)
        base = "%s://%s" % (parts.scheme, parts.netloc)
        if base in self.hosts:
            return self.hosts[base]
        robots_url = base + "/robots.txt"
        status, body, err = self._raw(robots_url, honor_robots=False)
        text = body if not err and status == 200 else ""
        if err or status != 200:
            self.skipped.append("robots unreadable for %s (%s); default allow" % (parts.netloc, err or status))
        allowed_delay = 0
        self.hosts[base] = {"robots": text, "next": 0.0, "blocked": False}
        # crawl-delay is read per URL inside get()
        self.hosts[base]["seed_delay"] = allowed_delay
        return self.hosts[base]

    def _raw(self, url, honor_robots=True):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        try:
            with self.opener(req, timeout=45) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    raw = gzip.decompress(raw)
                return resp.status, raw.decode("utf-8", "replace"), None
        except urllib.error.HTTPError as exc:
            return exc.code, "", "HTTP %s" % exc.code
        except Exception as exc:
            return 0, "", type(exc).__name__

    def get(self, url):
        host = self._host(url)
        allowed, crawl = robots_decision(host["robots"], url)
        if not allowed:
            self.skipped.append("robots disallow %s" % url)
            return 0, "", "robots-disallow"
        wait = max(self.delay, crawl or 0)
        if crawl and crawl > self.max_crawl_delay:
            self.skipped.append("crawl-delay %ss exceeds cap for %s" % (crawl, url))
            return 0, "", "crawl-delay"
        self.sleeper(wait)
        return self._raw(url)


def default_opener(req, timeout=45):
    return urllib.request.urlopen(req, timeout=timeout)


def run(args, getter=None, fixture=None):
    day = args.day or wc.now_ict().date().isoformat()
    state = {}
    if args.state and os.path.isfile(args.state) and not args.fresh_state:
        with open(args.state, encoding="utf-8") as f:
            state = json.load(f)
    skipped = []
    if fixture is None and args.fixtures:
        fixture = items_from_fixture(args.fixtures)
    if fixture is not None:
        pubmed_rows = fixture.get("pubmed") or []
        ods = []
        prev_ods = state.get("ods") or {}
        for row in fixture.get("ods") or []:
            ods.append(ods_highlight(row.get("url") or "", row.get("text") or row.get("html") or "", (prev_ods.get(row.get("url") or "") or {}).get("sha256")))
        rss_rows = fixture.get("rss") or []
    else:
        client = getter or PoliteClient(args.delay, args.max_crawl_delay, time.sleep, default_opener)
        pubmed_rows = live_pubmed(client.get, args.retmax, args.reldate, skipped)
        ods = []
        prev_ods = state.get("ods") or {}
        for url in ODS_URLS:
            status, body, err = client.get(url)
            if err or status != 200:
                skipped.append("ODS fetch failed %s (%s)" % (url, err or status))
                continue
            prev = (prev_ods.get(url) or {}).get("sha256")
            ods.append(ods_highlight(url, body, prev))
        rss_rows = []
        if not args.no_rss:
            for url in RSS_URLS:
                status, body, err = client.get(url)
                if err or status != 200:
                    skipped.append("RSS fetch failed %s (%s)" % (url, err or status))
                    continue
                rss_rows.extend(parse_rss(body))
        if isinstance(client, PoliteClient):
            skipped.extend(client.skipped)
    pubmed = decorate_pubmed(pubmed_rows, state)
    rss = decorate_rss(rss_rows, state)
    note, _digest = render_note(day, pubmed, ods, rss, skipped)
    new_state = update_state(state, day, pubmed, ods, rss)
    wrote = []
    if not args.dry_run:
        out_dir = args.out_dir or os.path.join(VAULT, "90-sources", "wellness-intake")
        os.makedirs(out_dir, exist_ok=True)
        dest = os.path.join(out_dir, day + ".md")
        with open(dest, "w", encoding="utf-8") as f:
            f.write(note)
        wrote.append(dest)
        if args.state:
            os.makedirs(os.path.dirname(os.path.abspath(args.state)), exist_ok=True)
            with open(args.state, "w", encoding="utf-8") as f:
                json.dump(new_state, f, indent=2)
                f.write("\n")
            wrote.append(args.state)
    print(note)
    if wrote:
        print("wrote: " + ", ".join(wrote))
    print("counts pubmed=%s ods=%s rss=%s skipped=%s" % (len(pubmed), len(ods), len(rss), len(skipped)))
    if fixture is None and not pubmed and not ods and not rss and skipped:
        return 2
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Wellness source intake for Wellness Nest clusters.")
    ap.add_argument("--dry-run", action="store_true", help="print the note and do not write files")
    ap.add_argument("--fixtures", help="JSON fixture bundle; no network")
    ap.add_argument("--out-dir", help="directory for YYYY-MM-DD.md (default: vault 90-sources/wellness-intake)")
    ap.add_argument("--state", default=os.path.join(ROOT, "state", "wellness-intake.json"))
    ap.add_argument("--fresh-state", action="store_true", help="ignore an existing state file")
    ap.add_argument("--day", help="YYYY-MM-DD (default: today ICT)")
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--max-crawl-delay", type=float, default=15.0, help="skip a host whose robots crawl-delay is above this (seconds)")
    ap.add_argument("--retmax", type=int, default=3)
    ap.add_argument("--reldate", type=int, default=365)
    ap.add_argument("--no-rss", action="store_true")
    args = ap.parse_args(argv)
    if args.fixtures and args.dry_run:
        pass
    return run(args)


if __name__ == "__main__":
    sys.exit(main())

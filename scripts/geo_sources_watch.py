#!/usr/bin/env python3
"""GEO official-sources watcher — change-aware daily scraper (stdlib only; Python 3.9+; runs on box or either Mac).

Sources (Kevin 2026-10-08):
  google    Google Search Central: /search/docs/* (nav), /crawling/docs/*, /search/updates, Search Central blog
  xai       docs.x.ai developers/tools/* (web search, x search, citations ...)
  openai    developers.openai.com /api/docs/bots + web-search / deep-research guides
  anthropic privacy.claude.com /en/* help-center articles (crawler + privacy)

Modes:
  --mode baseline   discover + fetch every in-scope page, store hash + text snapshot (blog: posts >= --blog-since)
  --mode daily      discover; fetch new URLs, re-check tracked pages (blog: only new posts and posts < 120 days old);
                    report NEW / CHANGED / REMOVED pages with line diffs
Outputs:
  <state>/url-hashes.json                 one record per URL: source, title, sha256, first_seen, last_changed, ...
  <state>/snapshots/<source>/<id>.md      extracted main text (used for diffs)
  <state>/runs/<date>.json                machine-readable change list for that run
  <out>/geo-official-changes-<date>.md    human/agent-readable change list + diffs (input for the vault digest)
Politeness: robots.txt checked per URL (urllib.robotparser), Crawl-delay honored (min --delay s), one request at
a time per host, identifying User-Agent, conditional GET (ETag / Last-Modified) where the server supports it.
Exit: 0 ok (changes or not), 2 = partial (some fetch errors), 1 = fatal.
"""
import argparse, datetime as dt, difflib, gzip, hashlib, html, json, os, re, sys, threading, time
import urllib.error, urllib.parse, urllib.request, urllib.robotparser
from html.parser import HTMLParser

UA = "Mozilla/5.0 (compatible; PATI-GEO-Watch/1.0; +https://wellnessnest.co; daily docs change check)"
ICT = dt.timezone(dt.timedelta(hours=7))
BLOG_RECHECK_DAYS = 120


def now_ict():
    return dt.datetime.now(ICT)


# ---------------------------------------------------------------- HTTP + robots
class Host:
    def __init__(self, base, min_delay):
        self.base = base
        self.rp = urllib.robotparser.RobotFileParser()
        self.rp.set_url(base + "/robots.txt")
        try:
            raw = http_get(base + "/robots.txt")[1].decode("utf-8", "ignore")
            self.rp.parse(raw.splitlines())
        except Exception:
            self.rp.parse([])  # unreachable robots -> RobotFileParser default allow (RFC 9309 4xx semantics)
        cd = None
        try:
            cd = self.rp.crawl_delay(UA) or self.rp.crawl_delay("*")
        except Exception:
            pass
        self.delay = max(min_delay, float(cd or 0))
        self.lock = threading.Lock()
        self.last = 0.0

    def allowed(self, url):
        try:
            return self.rp.can_fetch(UA, url)
        except Exception:
            return True

    def get(self, url, headers=None):
        with self.lock:
            wait = self.last + self.delay - time.time()
            if wait > 0:
                time.sleep(wait)
            try:
                return http_get(url, headers)
            finally:
                self.last = time.time()


def http_get(url, headers=None, timeout=60, tries=3, _hops=0):
    h = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
         "Accept-Encoding": "gzip"}
    h.update(headers or {})
    last = None
    for a in range(tries):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout)
            body = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                body = gzip.decompress(body)
            return r.status, body, dict(r.headers), r.geturl()
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location") and _hops < 5:
                # Python < 3.11 urllib does not follow 308; follow manually (GET only)
                nxt = urllib.parse.urljoin(url, e.headers["Location"])
                return http_get(nxt, headers, timeout, tries, _hops + 1)
            if e.code == 304:
                return 304, b"", dict(e.headers), url
            if e.code in (404, 410):
                return e.code, b"", dict(e.headers), url
            last = e
            if e.code == 429 or e.code >= 500:
                time.sleep(5 * (a + 1) + (int(e.headers.get("Retry-After", "0") or 0) if str(e.headers.get("Retry-After", "")).isdigit() else 0))
                continue
            raise
        except Exception as e:  # timeouts, resets
            last = e
            time.sleep(3 * (a + 1))
    raise last


# ---------------------------------------------------------------- extraction
BLOCK = {"p", "div", "section", "li", "ul", "ol", "table", "tr", "br", "h1", "h2", "h3", "h4", "h5", "h6", "pre",
         "blockquote", "dt", "dd", "dl", "article", "main", "header", "footer", "aside", "figure", "figcaption", "hr", "td", "th"}
SKIP = {"script", "style", "svg", "noscript", "nav", "button", "template", "iframe", "form", "select", "devsite-feedback",
        "devsite-thumb-rating", "devsite-hats-survey", "devsite-toc"}
VOID = {"br", "img", "hr", "meta", "link", "input", "source", "wbr", "col", "area", "base", "embed", "param", "track"}


class Extract(HTMLParser):
    """Collect text inside the first container matching (tag, class-substring) — or the whole body."""

    def __init__(self, containers):
        super().__init__(convert_charrefs=True)
        self.containers = containers
        self.depth = 0          # depth inside chosen container (0 = not inside)
        self.done = False
        self.skip = 0
        self.out = []
        self.title = ""
        self.in_title = False
        self.h1 = ""
        self.in_h1 = False
        self.prefix = ""
        self.pre = 0

    def _match(self, tag, attrs):
        cls = dict(attrs).get("class", "") or ""
        for t, c in self.containers:
            if tag == t and (c is None or c in cls.split() or (c and c in cls)):
                return True
        return False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        if self.done:
            return
        if self.depth == 0:
            if self._match(tag, attrs):
                self.depth = 1
            return
        if tag in VOID:
            if tag == "br" and not self.skip:
                self.out.append("\n")
            return
        self.depth += 1
        a = dict(attrs)
        if not self.skip and (tag in SKIP or (a.get("aria-hidden") == "true" and tag in ("span", "div"))
                              or "devsite-article-meta" in (a.get("class") or "") or "devsite-breadcrumb" in (a.get("class") or "")):
            self.skip = self.depth  # skip everything until this element closes
            return
        if self.skip:
            return
        if tag == "h1":
            self.in_h1 = True
        if tag == "pre":
            self.pre += 1
        if tag in BLOCK:
            self.out.append("\n")
        if re.fullmatch(r"h[1-6]", tag):
            self.out.append("#" * int(tag[1]) + " ")
        elif tag == "li":
            self.out.append("- ")
        elif tag in ("td", "th"):
            self.out.append(" | ")
        elif tag == "code":
            self.out.append("`")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if self.done or self.depth == 0 or tag in VOID:
            return
        if not self.skip:
            if tag == "h1":
                self.in_h1 = False
            if tag == "pre" and self.pre:
                self.pre -= 1
            if tag == "code":
                self.out.append("`")
            if tag in BLOCK:
                self.out.append("\n")
        if self.skip and self.depth == self.skip:
            self.skip = 0
        self.depth -= 1
        if self.depth == 0:
            self.done = True

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.depth and not self.skip and not self.done:
            self.out.append(data if self.pre else data.replace("\n", " "))
            if self.in_h1:
                self.h1 += data


CONTAINERS = {
    "developers.google.com": [("div", "devsite-article-body"), ("article", None), ("main", None)],
    "docs.x.ai": [("main", None)],
    "developers.openai.com": [("article", None), ("main", None)],
    "privacy.claude.com": [("article", None), ("main", None)],
}
VOLATILE = [
    re.compile(r"(?im)^\s*Updated (over |about )?(a|an|\d+) (minute|hour|day|week|month|year)s? ago\s*$"),
    re.compile(r"(?im)^\s*Updated (yesterday|today|this week)\s*$"),
    re.compile(r"(?i)\bUpdated (over |about )?(a|an|\d+) (minute|hour|day|week|month|year)s? ago\b"),
    re.compile(r"(?im)^\s*(Was this (page|article) helpful\??|Did this answer your question\?).*$"),
    re.compile(r"(?im)^.*(😞|😐|😃).*$"),
]
LAST_UPDATED = re.compile(r"Last updated (\d{4}-\d{2}-\d{2}) UTC")


def extract(url, body):
    host = urllib.parse.urlsplit(url).netloc
    raw = body.decode("utf-8", "ignore")
    p = None
    for c in CONTAINERS.get(host, []) + [("main", None), ("article", None), ("body", None)]:
        p = Extract([c])
        p.feed(raw)
        if len("".join(p.out).strip()) > 200:
            break
    text = "".join(p.out)
    text = html.unescape(text)
    lines = []
    for ln in text.split("\n"):
        ln = re.sub(r"[ \t\u00a0]+", " ", ln).strip()
        if ln and ln not in ("-", "|", "``"):
            lines.append(ln)
    text = "\n".join(lines)
    for rx in VOLATILE:
        text = rx.sub("", text)
    text = re.sub(r"\n{2,}", "\n", text).strip()
    m = LAST_UPDATED.search(raw)
    title = (p.h1 or p.title).strip()
    title = re.sub(r"\s+", " ", title).split(" | ")[0].strip()
    return title, text, (m.group(1) if m else "")


# ---------------------------------------------------------------- discovery
def links(html_text, base, pattern):
    out = set()
    for h in re.findall(r'href="([^"#?]+)', html_text):
        u = urllib.parse.urljoin(base, h)
        if re.match(pattern, u):
            out.add(u.rstrip("/") if not u.endswith("/api/docs/bots/") else u)
    return out


def sitemap_locs(xml):
    return [(m.group(1).strip(), (m.group(2) or "").strip()) for m in
            re.finditer(r"<url>\s*<loc>([^<]+)</loc>(?:\s*<lastmod>([^<]+)</lastmod>)?", xml)]


def discover_google(host, mode, blog_since, state):
    G = "https://developers.google.com"
    pages, blog = {}, {}
    t = host.get(G + "/search/docs")[1].decode("utf-8", "ignore")
    for u in links(t, G, r"^https://developers\.google\.com/search/docs(/[a-z0-9\-/]+)?$"):
        pages[u] = {"kind": "doc"}
    t = host.get(G + "/crawling/docs/crawlers-fetchers/overview-google-crawlers")[1].decode("utf-8", "ignore")
    for u in links(t, G, r"^https://developers\.google\.com/crawling/docs/[a-z0-9\-/]+$"):
        pages[u] = {"kind": "doc"}
    for extra in ("/search/updates", "/search/docs/fundamentals/ai-optimization-guide", "/search/docs/appearance/ai-features"):
        pages[G + extra] = {"kind": "doc"}
    # blog: full index page lists every post; RSS feed has the newest with pubDate
    t = host.get(G + "/search/blog")[1].decode("utf-8", "ignore")
    for u in links(t, G, r"^https://developers\.google\.com/search/blog/(\d{4})/(\d{2})/[A-Za-z0-9\-_.]+$"):
        if u.endswith((".doc", ".pdf", ".png")):
            continue
        blog[u] = {"kind": "blog"}
    try:
        f = host.get(G + "/search/blog/feed.xml")[1].decode("utf-8", "ignore")
        for m in re.finditer(r"<link>(https://developers\.google\.com/search/blog/[^<]+)</link>\s*<description>.*?</description>\s*<pubDate>([^<]+)</pubDate>", f, re.S):
            blog[m.group(1).rstrip("/")] = {"kind": "blog", "pubdate": m.group(2)}
    except Exception:
        pass
    cutoff = blog_since
    recheck = (now_ict() - dt.timedelta(days=BLOG_RECHECK_DAYS)).strftime("%Y-%m")
    for u, meta in blog.items():
        ym = "-".join(re.search(r"/blog/(\d{4})/(\d{2})/", u).groups())
        meta["ym"] = ym
        known = u in state
        if mode == "baseline":
            meta["fetch"] = ym >= cutoff
        else:  # daily: new posts always; known posts only while recent
            meta["fetch"] = (not known) or ym >= recheck
        pages[u] = meta
    return pages


def discover_xai(host, mode, blog_since, state):
    xml = host.get("https://docs.x.ai/sitemap.xml")[1].decode("utf-8", "ignore")
    out = {}
    for u, lm in sitemap_locs(xml):
        if re.search(r"/developers/tools/|citation|web-search|x-search|live-search", u):
            out[u.rstrip("/")] = {"kind": "doc", "lastmod": lm}
    out.setdefault("https://docs.x.ai/developers/tools/web-search", {"kind": "doc"})
    return out


OPENAI_KEEP = re.compile(r"^https://developers\.openai\.com/api/docs/(bots/?|guides/tools-web-search/?|guides/deep-research/?|guides/agents-api/tools/web-search/?)$")


def discover_openai(host, mode, blog_since, state):
    xml = host.get("https://developers.openai.com/sitemap-0.xml")[1].decode("utf-8", "ignore")
    out = {}
    for u, lm in sitemap_locs(xml):
        if OPENAI_KEEP.match(u) or re.search(r"/api/docs/[^ ]*(crawler|publisher|robots)", u):
            out[u] = {"kind": "doc", "lastmod": lm}
    out.setdefault("https://developers.openai.com/api/docs/bots/", {"kind": "doc"})
    return out


def discover_anthropic(host, mode, blog_since, state):
    xml = host.get("https://privacy.claude.com/sitemap.xml")[1].decode("utf-8", "ignore")
    out = {}
    for u, lm in sitemap_locs(xml):
        if u.startswith("https://privacy.claude.com/en/"):
            prev = state.get(u, {})
            # sitemap lastmod is reliable here -> daily: only re-fetch when it moved (or weekly safety re-check)
            stale = (now_ict() - dt.datetime.fromisoformat(prev.get("last_checked", "2000-01-01T00:00:00+07:00"))).days >= 7
            out[u] = {"kind": "collection" if "/collections/" in u else "doc", "lastmod": lm,
                      "fetch": mode == "baseline" or not prev or prev.get("lastmod") != lm or stale}
    return out


SOURCES = {
    "google": ("https://developers.google.com", discover_google, "Google Search Central"),
    "xai": ("https://docs.x.ai", discover_xai, "xAI docs (Grok tools)"),
    "openai": ("https://developers.openai.com", discover_openai, "OpenAI developer docs (bots)"),
    "anthropic": ("https://privacy.claude.com", discover_anthropic, "Anthropic Privacy Center"),
}


# ---------------------------------------------------------------- state
def load_json(p, default):
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return default


def save_json(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True, ensure_ascii=False)
    os.replace(tmp, p)


def snap_path(state_dir, source, url):
    return os.path.join(state_dir, "snapshots", source, hashlib.sha1(url.encode()).hexdigest()[:16] + ".md")


def short_diff(old, new, limit=40):
    add, rem = [], []
    for ln in difflib.unified_diff(old.split("\n"), new.split("\n"), lineterm="", n=0):
        if ln.startswith(("+++", "---", "@@")):
            continue
        (add if ln.startswith("+") else rem).append(ln[1:])
    return add[:limit], rem[:limit], len(add), len(rem)


# ---------------------------------------------------------------- run
def run_source(name, args, state, results, lock):
    base, disc, label = SOURCES[name]
    host = Host(base, args.delay)
    try:
        found = disc(host, args.mode, args.blog_since, state)
    except Exception as e:
        with lock:
            results["errors"].append({"source": name, "url": base, "error": "discovery failed: %r" % e})
        return
    today = now_ict().isoformat(timespec="seconds")
    n = 0
    for url, meta in sorted(found.items()):
        prev = state.get(url)
        if prev is None:
            with lock:
                state[url] = prev = {"source": name, "kind": meta.get("kind"), "first_seen": today, "hash": "",
                                     "baseline": args.mode == "baseline"}
            is_new = args.mode != "baseline"
        else:
            is_new = False
        prev["missing_runs"] = 0
        if meta.get("lastmod"):
            prev["sitemap_lastmod"] = meta["lastmod"]
        if meta.get("pubdate"):
            prev["pubdate"] = meta["pubdate"]
        if not meta.get("fetch", True):
            if is_new and meta.get("kind") == "blog":
                pass
            continue
        if args.max_pages and n >= args.max_pages:
            break
        if not host.allowed(url):
            prev["robots_blocked"] = True
            continue
        n += 1
        hdr = {}
        if prev.get("etag") and prev.get("hash"):
            hdr["If-None-Match"] = prev["etag"]
        if prev.get("last_modified") and prev.get("hash"):
            hdr["If-Modified-Since"] = prev["last_modified"]
        try:
            status, body, headers, final = host.get(url, hdr)
        except Exception as e:
            with lock:
                results["errors"].append({"source": name, "url": url, "error": repr(e)[:200]})
            continue
        prev["last_checked"] = today
        if status == 304:
            continue
        if status in (404, 410):
            if prev.get("hash") and prev.get("status") != status:
                with lock:
                    results["removed"].append({"source": name, "url": url, "title": prev.get("title", ""), "status": status})
            prev["status"] = status
            continue
        prev["status"] = status
        prev["etag"] = headers.get("ETag") or headers.get("Etag") or ""
        prev["last_modified"] = headers.get("Last-Modified") or ""
        if meta.get("lastmod"):
            prev["lastmod"] = meta["lastmod"]
        title, text, last_upd = extract(final, body)
        h = hashlib.sha256(text.encode()).hexdigest()
        sp = snap_path(args.state_dir, name, url)
        old_text = ""
        if os.path.exists(sp):
            with open(sp) as f:
                old_text = f.read()
        rec = {"source": name, "url": url, "title": title, "kind": meta.get("kind"), "page_last_updated": last_upd,
               "chars": len(text)}
        if not prev.get("hash"):
            if is_new:
                rec["excerpt"] = text[:1200]
                with lock:
                    results["new"].append(rec)
            else:
                with lock:
                    results["baselined"] += 1
            prev["last_changed"] = today
        elif prev["hash"] != h:
            if old_text:
                add, rem, na, nr = short_diff(old_text, text)
            else:
                add, rem, na, nr = [], [], -1, -1
            if na == 0 and nr == 0:
                pass
            else:
                rec.update({"added": add, "removed": rem, "n_added": na, "n_removed": nr})
                with lock:
                    results["changed"].append(rec)
                prev["last_changed"] = today
        prev.update({"hash": h, "title": title, "page_last_updated": last_upd})
        os.makedirs(os.path.dirname(sp), exist_ok=True)
        with open(sp, "w") as f:
            f.write(text)
    # URLs that vanished from discovery
    for url, prev in list(state.items()):
        if prev.get("source") == name and url not in found and prev.get("status") != 404:
            prev["missing_runs"] = prev.get("missing_runs", 0) + 1
            if prev["missing_runs"] == 2 and prev.get("hash"):
                with lock:
                    results["removed"].append({"source": name, "url": url, "title": prev.get("title", ""), "status": "not in index/sitemap for 2 runs"})
    with lock:
        results["fetched"][name] = n
        results["tracked"][name] = sum(1 for v in state.values() if v.get("source") == name)


def write_md(path, res, date):
    L = ["---", "type: geo-official-changes", "date: %s" % date, "timezone: Asia/Saigon",
         "generated_by: geo_sources_watch.py (%s)" % res["mode"], "host: %s" % res["host"],
         "new: %d" % len(res["new"]), "changed: %d" % len(res["changed"]), "removed: %d" % len(res["removed"]),
         "errors: %d" % len(res["errors"]), "---", "",
         "# GEO official sources — raw change list %s" % date, "",
         "Machine output. The routine turns this into `geo-official-digest-%s.md` (what changed + so what for GenSeo)." % date, ""]
    L.append("Fetched this run: " + ", ".join("%s %d" % kv for kv in sorted(res["fetched"].items())))
    L.append("Tracked URLs: " + ", ".join("%s %d" % kv for kv in sorted(res["tracked"].items())))
    L.append("")
    for sec in ("new", "changed", "removed"):
        L.append("## %s (%d)" % (sec.upper(), len(res[sec])))
        for r in res[sec]:
            L.append("### [%s] %s" % (r["source"], r.get("title") or r["url"]))
            L.append("- URL: %s" % r["url"])
            if r.get("page_last_updated"):
                L.append("- Page 'Last updated': %s" % r["page_last_updated"])
            if sec == "new" and r.get("excerpt"):
                L.append("- Excerpt:\n\n```\n%s\n```" % r["excerpt"][:1200])
            if sec == "changed":
                if r.get("n_added", 0) < 0:
                    L.append("- Content hash changed (no previous snapshot on this host — compare with the baseline note).")
                else:
                    L.append("- Lines added %d / removed %d (first 40 each):" % (r["n_added"], r["n_removed"]))
                    if r["added"]:
                        L.append("\n```diff\n" + "\n".join("+ " + x for x in r["added"]) + "\n```")
                    if r["removed"]:
                        L.append("\n```diff\n" + "\n".join("- " + x for x in r["removed"]) + "\n```")
            if sec == "removed":
                L.append("- Status: %s" % r.get("status"))
            L.append("")
        if not res[sec]:
            L.append("_none_\n")
    if res["errors"]:
        L.append("## FETCH ERRORS (%d)" % len(res["errors"]))
        for e in res["errors"][:50]:
            L.append("- [%s] %s — %s" % (e["source"], e["url"], e["error"]))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["baseline", "daily"], default="daily")
    ap.add_argument("--sources", default="google,xai,openai,anthropic")
    ap.add_argument("--state-dir", default=os.path.expanduser("~/geo-sources-state"))
    ap.add_argument("--out-dir", default=None, help="where geo-official-changes-<date>.md goes (default <state>/out)")
    ap.add_argument("--seed-hashes", default=None, help="url-hashes.json from the vault to bootstrap an empty state dir")
    ap.add_argument("--blog-since", default="2024-01", help="baseline: fetch blog posts from this YYYY-MM on")
    ap.add_argument("--delay", type=float, default=1.0, help="min seconds between requests per host")
    ap.add_argument("--max-pages", type=int, default=0)
    ap.add_argument("--date", default=None)
    args = ap.parse_args()
    args.state_dir = os.path.abspath(os.path.expanduser(args.state_dir))
    out_dir = os.path.abspath(os.path.expanduser(args.out_dir or os.path.join(args.state_dir, "out")))
    date = args.date or now_ict().strftime("%Y-%m-%d")
    hp = os.path.join(args.state_dir, "url-hashes.json")
    state = load_json(hp, {})
    if not state and args.seed_hashes and os.path.exists(args.seed_hashes):
        state = load_json(args.seed_hashes, {})
        print("seeded state from", args.seed_hashes, len(state), "urls")
    if args.mode == "daily" and not state:
        print("no state yet -> run --mode baseline first", file=sys.stderr)
        return 1
    lockp = os.path.join(args.state_dir, "run.lock")
    os.makedirs(args.state_dir, exist_ok=True)
    try:
        os.mkdir(lockp)
    except FileExistsError:
        if time.time() - os.stat(lockp).st_mtime < 3 * 3600:
            print("another run holds", lockp, file=sys.stderr)
            return 1
    try:
        res = {"mode": args.mode, "date": date, "host": os.uname().nodename, "started": now_ict().isoformat(timespec="seconds"),
               "new": [], "changed": [], "removed": [], "errors": [], "fetched": {}, "tracked": {}, "baselined": 0}
        lock = threading.Lock()
        ths = [threading.Thread(target=run_source, args=(s, args, state, res, lock)) for s in args.sources.split(",") if s in SOURCES]
        [t.start() for t in ths]
        [t.join() for t in ths]
        res["finished"] = now_ict().isoformat(timespec="seconds")
        save_json(hp, state)
        meta = load_json(os.path.join(args.state_dir, "meta.json"), {})
        meta.update({"last_run": res["finished"], "last_mode": args.mode, "last_host": res["host"]})
        if args.mode == "baseline":
            meta["baseline_at"] = res["finished"]
        save_json(os.path.join(args.state_dir, "meta.json"), meta)
        save_json(os.path.join(args.state_dir, "runs", "%s-%s.json" % (date, args.mode)), res)
        write_md(os.path.join(out_dir, "geo-official-changes-%s.md" % date), res, date)
        print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in res.items()}, indent=1))
        return 2 if res["errors"] else 0
    finally:
        try:
            os.rmdir(lockp)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())

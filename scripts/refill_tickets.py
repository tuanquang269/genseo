#!/usr/bin/env python3
"""Refill daily-tickets.md with gated, product-mapped PENDING article tickets (Kevin 2026-10-09: the
queue ran empty and the daily runner stopped at 1/5).

  python3 scripts/refill_tickets.py --count 8 --dry-run     # print the batch + every rejection; queue + board untouched
  python3 scripts/refill_tickets.py --count 8               # append a `# BATCH` + update board/ideas.csv
  python3 scripts/refill_tickets.py --if-below 4 --count 6  # no-op while >= 4 tickets are open (wrapper hook)
  python3 scripts/refill_tickets.py --count 8 --prefix MB --day 2026-10-12  # ids for that date; stamp stays now
  python3 scripts/refill_tickets.py --self-test             # offline fixtures: no network, writes nothing

The daily low-water call is --if-below, --count, and --prefix only. That path stays
ticket-only: public storefront reads, then append daily-tickets.md and board/ideas.csv.
Do not add a paid Ads or LLM miner behind those flags. A short bank is exit 3; the
wrapper writes state/queue-low-water.marker and does not spend money.

Candidates: board/ideas.csv rows with status=idea first, then templates/article-topic-bank.json topics
(priority, then the family with the fewest live articles). GENSEO_CLUSTER_PICKER=1 (default unset)
also prepends topics from state/cluster_map.json. The daily wrapper does not set that variable,
so the 5 article job is unchanged. Each must pass, in order, against the store
read live at run time:
  1 complete brief: product, primary, secondary, intent, angle, title <= 60 chars, known segment + template
  2 brand_rules / ageaura_rules (AgeAura handle = NMN + TMG Complex only; ageaura-pure-urolithin-a and any
    other Urolithin A AgeAura handle fail closed; FloraFresh formula = its Supplement Facts
    label, never the PDP description; Shilajit Shockwave doses = its pack-label whitelist, which has no
    milligram token; Pure Shilajit Gold Resin doses = its pack-label whitelist, which has the OCR
    serving line and 75% Fulvic and no milligram token; ShilaSource Himalayan Shilajit Resin doses =
    its pack-label whitelist, front-of-pack lines only, no milligram token) + the bank's banned terms,
    on the brief and on the rendered ticket.
    A FloraFresh ticket also carries florafresh_rules.TICKET_LINE (the label formula).
    A Shilajit Shockwave ticket also carries shockwave_rules.TICKET_LINE (the pack label).
    A Pure Shilajit Gold Resin ticket also carries gold_resin_rules.TICKET_LINE (the pack label).
    A ShilaSource resin ticket also carries shilasource_resin_rules.TICKET_LINE (the pack label).
    A Turkesterone Advanced Formula ticket also carries turkesterone_rules.TICKET_LINE (the pack label)
  3 hero and inline products live and in stock (products.json); a live collection to link
  4 not a covered topic (queue header rule 6: MenoMate / meal plans, shilajit foundations, ...)
  5 not already in daily-tickets.md, any status: same primary, title overlap, or same family + segment
  6 not already live: same family + segment, title overlap >= topic_fitness.DUP_JACCARD, or same slug.
    Inventory = paginated blog listing + sitemap + Atom feed, full titles from Atom / og:title (the listing
    cuts card titles at ~47 chars), plus existing_articles.json / ALL_ARTICLES.csv /
    PUBLISHED_ARTICLES_TRACKER.csv when present (drafts count)
  7 topic_fitness.assess on the primary AND the title, strict (live inventory loaded), under every
    stocked-brand token they contain: PASS, or REVIEW [covered-segment] — greenlit by Kevin's standing
    approval for mined queues (2026-08-13)
  8 STEP 0 suggest.json: no live article targets the primary
Selection: at most --max-per-family per family, then the best remaining topics if the batch is still short.
Order: round-robin by family, never the same template twice running. The batch is appended only if the
whole file passes lint_tickets.py.

Exit: 0 done (or nothing to do) · 3 fewer than --count passed (add topics to the bank or the board) ·
1 failed closed (store unreadable, bad input, lint failure, queue changed underneath) — nothing written.
"""
import argparse, csv, datetime as dt, html, json, os, re, subprocess, sys, tempfile, time
import urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import ageaura_rules as ar  # noqa: E402
import brand_rules as br  # noqa: E402
import florafresh_rules as ff  # noqa: E402
import gold_resin_rules as gr  # noqa: E402
import shilasource_resin_rules as sr  # noqa: E402
import shockwave_rules as sw  # noqa: E402
import turkesterone_rules as tk  # noqa: E402
import topic_fitness as tf  # noqa: E402

SITE = "https://wellnessnest.co"
BLOG = "news"
QUEUE = os.path.join(ROOT, "daily-tickets.md")
BANK = os.path.join(ROOT, "templates", "article-topic-bank.json")
BOARD = os.path.join(ROOT, "board", "ideas.csv")
CACHE = os.path.join(ROOT, "state", "refill_cache.json")
LINT = os.path.join(ROOT, "scripts", "lint_tickets.py")
ICT = dt.timezone(dt.timedelta(hours=7))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"}
OPEN_RX = re.compile(r"^(- \[ \]|## \[ \])", re.M)  # the daily wrapper's open-ticket count
HEAD_RX = re.compile(r"^(?:- |## )(?:\*\*)?\[([^\]]*)\](?!\()(.*)$")
ROW_RX = re.compile(r"^\|\s*~~#?([A-Z]*\d+(?:-\d+)?)~~[^|]*\|\s*\[([^\]]+)\]\(([^)\s]+)\)")  # shipped-batch table
CARD_RX = re.compile(r'href="/blogs/%s/([a-z0-9][a-z0-9-]*)"[^>]*>([^<]*)<' % BLOG)
OG_RX = re.compile(r'<meta\s+(?=[^>]*property="og:title")[^>]*content="([^"]*)"')
CANON_RX = re.compile(r'<link\s+rel="canonical"\s+href="[^"]*/blogs/%s/([a-z0-9][a-z0-9-]*)"' % BLOG)
TEMPLATES = ("EDITORIAL", "STORY", "LISTICLE", "COMPARISON")
REQUIRED = ("product", "primary", "title", "secondary", "segment", "intent", "template", "angle")
MAX_TITLE = 60
RANK = {"PASS": 0, "REVIEW": 1, "FAIL": 2}
GREENLIT = "allowed under Kevin's standing greenlight for mined queues (2026-08-13)"
BOARD_FIELDS = ["id", "status", "product", "primary_keyword", "secondary", "working_title", "segment", "intent",
                "template", "angle", "volume", "source", "ticket_id", "added", "updated", "last_check"]
HEADER = """# BATCH {day} (refill_tickets.py — ids #{first}…#{last})

Built by `scripts/refill_tickets.py` at {stamp} ICT from `templates/article-topic-bank.json` + `board/ideas.csv`
(search volume: No data — GSC/Ads not used). Every ticket passed, against the live store at build time:
brand_rules + `lint_tickets.py` · hero product live and in stock · not a covered topic (header rule 6) ·
not already queued · not live ({n_live} published articles: {src}; one article per brand + segment) ·
`topic_fitness.py` strict on primary and title · STEP 0 suggest.json.
A `topic_fitness` REVIEW [covered-segment] verdict is {greenlit}.
A topic is a brief, not copy: source every claim or cut it.

**Rules for this batch:** from the 2026-10-08 batch rules — fan-out answers, a "Where to buy <product> in the US"
section (live price, the ticket's product link only), roster.json byline only (never an invented person or
credential), the logged fact-check pass (`logs/claims/<slug>.md`; delete unconfirmed claims), the brand gate.
Blog 104008483131, publish `--live`. Images: people lane. Run persona_picker.py once. The hero is the picked face plus the real pack unless pick prints NO-FACE. One inline image uses that face. The other inline images have no recognizable face but still show a hand, forearm, or body cropped below the eyes. A no-face image is the fallback for one frame after a face refusal or two QC misses, not a batch-wide ban. The MacBook article plist sets `GENSEO_NO_FACE=0`, and that value does not switch the lane. Prices were read live at build time; re-check the PDP while writing.
"""


class Refuse(Exception):
    """Fail closed: nothing is written."""


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def norm_kw(s):
    return " ".join(re.findall(r"[a-z0-9]+", (s or "").lower()))


def jaccard(a, b):
    x, y = tf.sig_words(a or ""), tf.sig_words(b or "")
    return len(x & y) / len(x | y) if x and y else 0.0


def money(price):
    v = float(price)
    return f"${v:.0f}" if v == int(v) else f"${v:.2f}"


# ---------- topic bank ----------

def load_bank(path):
    b = json.loads(read(path))
    b["segments_rx"] = {k: re.compile(v) for k, v in b["segments"].items()}
    b["covered_rx"] = [re.compile(p) for p in b["covered_topics"]]
    b["banned_rx"] = [re.compile(p, re.I) for p in b["banned_terms"]]
    b["family_rx"] = {f: re.compile(r"\b(%s)" % "|".join(re.escape(t) for t in terms))
                      for f, terms in b["families"].items()}
    return b


def families_of(text, bank):
    t = (text or "").lower()
    return {f for f, rx in bank["family_rx"].items() if rx.search(t)}


def segments_of(text, bank):
    t = (text or "").lower()
    return {s for s, rx in bank["segments_rx"].items() if rx.search(t)}


def banned(text, bank):
    return br.violations(text) + [f"banned term /{rx.pattern}/" for rx in bank["banned_rx"] if rx.search(text)]


def guard_hero(handle):
    """Normalized hero/inline handle. A denied AgeAura handle raises brand_rules.GuardError."""
    try:
        return ar.require_target(handle)
    except ar.AgeAuraProductError as exc:
        raise br.GuardError(list(exc.reasons))


def lint_bank(bank, year="2026"):
    """Problems in the topic bank (run by --self-test on the real file)."""
    errs, seen = [], set()
    for h, p in bank["products"].items():
        if ar.classify_handle(h) == "deny":
            errs.append(f"products: {h} is banned by brand_rules")
        if p.get("family") not in bank["families"]:
            errs.append(f"products: {h} has unknown family {p.get('family')!r}")
        if not p.get("name") or not p.get("collections"):
            errs.append(f"products: {h} needs a name and collections")
        errs += [f"products: {h} lists banned collection {c}" for c in p.get("collections", [])
                 if not br.collection_allowed(c)]
    for t in bank["topics"]:
        tid = t.get("id", "?")
        if tid in seen:
            errs.append(f"{tid}: duplicate id")
        seen.add(tid)
        miss = [k for k in ("id", "priority", "link", "fanout", "evidence") + REQUIRED if not t.get(k)]
        if miss:
            errs.append(f"{tid}: missing {', '.join(miss)}")
            continue
        title = t["title"].replace("{year}", year)
        if len(title) > MAX_TITLE:
            errs.append(f"{tid}: title is {len(title)} chars (max {MAX_TITLE})")
        if t["primary"] != " ".join(t["primary"].lower().split()):
            errs.append(f"{tid}: primary must be lowercase, single-spaced")
        errs += [f"{tid}: product {h} is not in products" for h in [t["product"]] + t.get("inline", [])
                 if h not in bank["products"]]
        if t["segment"] not in bank["segments"]:
            errs.append(f"{tid}: unknown segment {t['segment']!r}")
        elif t["segment"] not in segments_of(t["primary"], bank):
            errs.append(f"{tid}: the primary does not match its segment {t['segment']!r}")
        if t["template"] not in TEMPLATES:
            errs.append(f"{tid}: unknown template {t['template']!r}")
        for text in (t["primary"], title.lower()):
            if not any(re.search(r"\b%s\b" % re.escape(m), text) for m in tf.SEGMENT_MODIFIERS):
                errs.append(f"{tid}: {text!r} has no topic_fitness SEGMENT_MODIFIER (strict gate FAILs [covered])")
        bad = [h for h in t["link"] if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", h) or not ar.article_link_allowed(h)]
        if bad:
            errs.append(f"{tid}: bad link handles {bad}")
        hits = banned(" ".join([t["primary"], title, t["intent"], t["angle"], t["evidence"]]
                               + t["secondary"] + t["fanout"]), bank)
        if hits:
            errs.append(f"{tid}: {'; '.join(hits)}")
    return errs


# ---------- queue + board ----------

def parse_queue(text):
    """Every ticket (open, DONE, x, SKIPPED…, and the struck-through rows of a shipped-batch table) with id,
    title, primary and template."""
    out, cur = [], None
    for line in text.splitlines():
        m, row = HEAD_RX.match(line), ROW_RX.match(line)
        if m:
            cur = {"status": m.group(1).strip(), "head": m.group(2), "body": ""}
            out.append(cur)
        elif row:
            out.append({"status": "DONE", "head": "", "body": "", "id": row.group(1), "title": row.group(2)})
            cur = None
        elif line.startswith("#"):
            cur = None
        elif cur is not None:
            cur["body"] += line + "\n"
    for t in out:
        s = t["status"]
        t["state"] = ("open" if not s else "done" if re.match(r"(DONE|x\b)", s, re.I) else
                      "skipped" if s.upper().startswith("SKIPPED") else "other")
        m = re.search(r"#([A-Z]*\d+(?:-\d+)?)", t["head"])
        t.setdefault("id", m.group(1) if m else "")
        m = re.search(r"`([^`]+)`", t["head"])
        t.setdefault("title", m.group(1) if m else "")
        m = (re.search(r"\*\*Primary keyword:\*\*\s*`([^`]+)`", t["head"] + "\n" + t["body"])
             or re.search(r"(?:^|\*\*)\s*#[A-Z]*[\d-]+ — ([^*]+)\*\*", t["head"]))
        t["primary"] = " ".join(m.group(1).lower().split()) if m else ""
        m = re.search(r"\*\*Template:\*\*\s*([A-Z]+)", t["body"])
        t["template"] = m.group(1) if m else ""
    return out


def next_ids(text, prefix, day, k):
    mmdd = day.strftime("%m%d")
    used = [int(n) for n in re.findall(r"#%s%s-(\d+)\b" % (prefix, mmdd), text)]
    start = max(used, default=0) + 1
    return [f"{prefix}{mmdd}-{start + i}" for i in range(k)]


def batch_day(now, day_arg):
    """Calendar date for the batch title and ticket ids. Empty keeps `now` (today ICT).
    A Monday queue prepared the evening before passes `--day` so ids are `#MBmmdd-N` for that
    Monday. The build stamp, the in-stock date, and the dedup date stay on `now` — the clock
    that actually read the store."""
    if not day_arg:
        return now.date()
    try:
        return dt.date.fromisoformat(day_arg)
    except ValueError as e:
        raise Refuse(f"--day must be YYYY-MM-DD, got {day_arg!r}") from e


def read_board(path):
    if not os.path.exists(path):
        return [], list(BOARD_FIELDS)
    with open(path, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        rows, fields = list(rd), list(rd.fieldnames or [])
    return rows, fields + [k for k in BOARD_FIELDS if k not in fields]


def write_board(path, rows, fields):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def update_board(rows, queue, picked, rejected, day):
    """Sync queued rows whose ticket was flipped DONE/SKIPPED, upsert the new tickets as `queued`, and note
    why board ideas were rejected. picked = [(candidate, ticket id)], rejected = [(candidate, reason)]."""
    day = str(day)
    state = {t["id"]: t["state"] for t in queue if t["id"]}
    for r in rows:
        st = state.get((r.get("ticket_id") or "").lstrip("#"))
        if (r.get("status") or "") == "queued" and st in ("done", "skipped"):
            r["status"], r["updated"] = st, day
    by_id = {r.get("id"): r for r in rows}
    for c, tid in picked:
        r = by_id.get(c["id"])
        if r is None:
            r = by_id[c["id"]] = {"added": day}
            rows.append(r)
        for k, v in {"id": c["id"], "product": c["product"], "primary_keyword": c["primary"],
                     "secondary": "; ".join(c["secondary"]), "working_title": c["title"], "segment": c["segment"],
                     "intent": c["intent"], "template": c["template"], "angle": c["angle"], "volume": "No data",
                     "source": c["source"], "added": day}.items():
            if not r.get(k) or k not in ("volume", "source", "added"):
                r[k] = v
        r.update(status="queued", ticket_id=f"#{tid}", updated=day, last_check=f"{day} queued as #{tid}")
    for c, why in rejected:
        if c["source"] == "board" and c["id"] in by_id:
            by_id[c["id"]]["last_check"] = f"{day} rejected: {why}"[:300]
    return rows


# ---------- live store ----------

def fetch(url, tries=3, timeout=25):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404 or i == tries - 1:
                raise
        except OSError:
            if i == tries - 1:
                raise
        time.sleep(2 ** i)


def listing_page(n):
    found = {}
    for h, txt in CARD_RX.findall(fetch(f"{SITE}/blogs/{BLOG}?page={n}")):
        t = html.unescape(" ".join(txt.split()))
        if len(t) > len(found.get(h, "")):
            found[h] = t
    return found


def blog_listing():
    """handle -> title for every published article: the paginated listing is the one complete, current
    source (the sitemap lags new posts and re-handled pages; the Atom feed stops at 30)."""
    out, n = {}, 1
    with ThreadPoolExecutor(4) as ex:
        while n < 400:
            pages = list(ex.map(listing_page, range(n, n + 4)))
            fresh = sum(1 for p in pages for h in p if h not in out)
            for p in pages:
                for h, t in p.items():
                    if len(t) > len(out.get(h, "")):
                        out[h] = t
            if not fresh or any(not p for p in pages):
                return out
            n += 4
    return out


def sitemap_handles():
    out = {}
    for loc in re.findall(r"<loc>(%s/sitemap_articles_\d+\.xml[^<]*)</loc>" % re.escape(SITE), fetch(f"{SITE}/sitemap.xml")):
        for h in re.findall(r"<loc>%s/blogs/%s/([a-z0-9-]+)</loc>" % (re.escape(SITE), BLOG), fetch(html.unescape(loc))):
            out[h] = ""
    return out


def atom_titles():
    out = {}
    for e in re.findall(r"<entry>(.*?)</entry>", fetch(f"{SITE}/blogs/{BLOG}.atom"), re.S):
        h = re.search(r'href="%s/blogs/%s/([a-z0-9-]+)"' % (re.escape(SITE), BLOG), e)
        t = re.search(r"<title>([^<]*)</title>", e)
        if h:
            out[h.group(1)] = html.unescape(t.group(1)).strip() if t else ""
    return out


def article_meta(handle):
    """(og:title, current handle) of an article page; a renamed handle redirects to its current one, and a
    deleted article (404) has no current handle."""
    try:
        page = fetch(f"{SITE}/blogs/{BLOG}/{handle}", tries=2)
    except urllib.error.HTTPError as e:
        return "", (None if e.code == 404 else handle)
    except OSError:
        return "", handle
    m, c = OG_RX.search(page), CANON_RX.search(page)
    return (html.unescape(m.group(1)).strip() if m else ""), (c.group(1) if c else handle)


def is_cut(title):
    return title.endswith(("...", "…"))


def merge_titles(listing, sources, meta):
    """handle -> title of every live article. The listing cuts card titles at ~47 chars, which hides dedup
    words like 'workout', so a full title from `sources` (Atom) or meta(handle) replaces every cut or empty
    one. A stale sitemap still lists renamed and deleted handles: renamed ones fold into their current
    handle, deleted ones drop out."""
    titles = dict(listing)
    for src in sources:
        for h, t in src.items():
            cur = titles.setdefault(h, "")
            if t and not is_cut(t) and (not cur or is_cut(cur)):
                titles[h] = t
    todo = [h for h, t in titles.items() if not t or is_cut(t)]
    with ThreadPoolExecutor(6) as ex:
        for h, (full, now) in zip(todo, ex.map(meta, todo)):
            cut = titles.pop(h)
            if now is None or (now != h and titles.get(now)):
                continue
            titles[now] = full or cut.rstrip(".…").strip() or now.replace("-", " ")
    return titles


def read_store():
    """(products, collections -> member handles, [(handle, title)] of every published article)."""
    prods = {}
    for p in json.loads(fetch(f"{SITE}/products.json?limit=250"))["products"]:
        vs = p.get("variants") or [{}]
        prods[p["handle"]] = {"title": p["title"], "price": vs[0].get("price") or "0",
                              "available": any(v.get("available") for v in vs)}
    colls = {}
    for c in json.loads(fetch(f"{SITE}/collections.json?limit=250"))["collections"]:
        members = json.loads(fetch(f"{SITE}/collections/{c['handle']}/products.json?limit=250"))["products"]
        colls[c["handle"]] = [p["handle"] for p in members]
    listing = blog_listing()
    if not listing:
        print("  ! the blog listing parsed 0 articles (theme change?) — using sitemap + Atom + og:title only")
    sources = []
    for name, source in (("sitemap", sitemap_handles), ("Atom feed", atom_titles)):
        try:
            sources.append(source())
        except (OSError, ValueError) as e:
            print(f"  ! {name} unreadable ({e}) — continuing without it")
    titles = merge_titles(listing, sources, article_meta)
    if len(titles) < 10:
        raise Refuse(f"live article inventory looks broken ({len(titles)} articles) — refusing to dedup blind")
    return prods, colls, sorted(titles.items())


def save_cache(store, stamp):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump({"at": stamp, "products": store[0], "collections": store[1], "articles": store[2]}, f)


def load_cache():
    if not os.path.exists(CACHE):
        raise Refuse("--offline needs state/refill_cache.json — run once online first")
    c = json.loads(read(CACHE))
    print(f"  (offline: store snapshot from {c['at']} — STEP 0 must re-check every ticket)")
    return c["products"], c["collections"], [tuple(a) for a in c["articles"]]


def local_inventory():
    """(handle, title) pairs from the Mac's gitignored caches — drafts included, which suggest.json cannot see."""
    out = []
    p = os.path.join(ROOT, "existing_articles.json")
    if os.path.exists(p):
        try:
            out += [(a.get("handle") or "", a.get("title") or "") for a in json.loads(read(p))]
        except (ValueError, AttributeError) as e:
            print(f"  ! existing_articles.json unreadable ({e}) — skipped")
    for name, tcol, ucol in (("ALL_ARTICLES.csv", "title", "url"),
                             ("PUBLISHED_ARTICLES_TRACKER.csv", "Keyword", "Article Link")):
        p = os.path.join(ROOT, name)
        if not os.path.exists(p):
            continue
        try:
            with open(p, newline="", encoding="utf-8-sig") as f:
                for r in csv.DictReader(f):
                    m = re.search(r"/blogs/[a-z0-9-]+/([a-z0-9-]+)", r.get(ucol) or "")
                    out.append((m.group(1) if m else "", (r.get(tcol) or "").strip()))
        except (csv.Error, ValueError) as e:
            print(f"  ! {name} unreadable ({e}) — skipped")
    return [(h, t) for h, t in out if h or t]


# ---------- candidates + gates ----------

def build_ctx(bank, queue, store, local, now, suggest):
    prods, colls, live = store
    arts, seen = [], set()
    for h, t in list(live) + list(local):
        t = t or h.replace("-", " ")
        if (h, t) not in seen:
            seen.add((h, t))
            arts.append({"handle": h, "title": t, "fams": families_of(f"{t} {h.replace('-', ' ')}", bank),
                         "segs": segments_of(t, bank)})
    for q in queue:
        q["fams"], q["segs"] = families_of(f"{q['title']} {q['primary']}", bank), segments_of(f"{q['title']} {q['primary']}", bank)
    live_h = {h for h, _ in live}
    fam_count = {f: len({a["handle"] for a in arts if f in a["fams"] and a["handle"] in live_h}) for f in bank["families"]}
    return {"bank": bank, "queue": queue, "products": prods, "collections": colls, "articles": arts,
            "live_handles": live_h, "local": bool(local), "fam_count": fam_count, "day": now.date(),
            "stamp": now.strftime("%Y-%m-%d %H:%M"), "suggest": suggest, "passed": []}


def norm_cand(d, bank, source, priority, order):
    c = {k: (d.get(k) or "").strip() for k in ("product", "title", "segment", "intent", "angle", "evidence")}
    c.update(id=d.get("id") or slug(d.get("primary")), source=source, priority=priority, order=order,
             primary=" ".join((d.get("primary") or "").lower().split()),
             template=(d.get("template") or "").strip().upper(),
             **{k: list(d.get(k) or []) for k in ("inline", "secondary", "fanout", "link")})
    c["family"] = bank["products"].get(c["product"], {}).get("family", "")
    c["fams"] = {c["family"]} - {""}
    c["segs"] = ({c["segment"]} - {""}) | segments_of(c["primary"], bank)
    return c


def cluster_picker_topics(bank):
    """Optional GEO cluster topics. Off unless GENSEO_CLUSTER_PICKER is 1, true, yes, or on."""
    flag = os.environ.get("GENSEO_CLUSTER_PICKER", "").strip().lower()
    if flag not in ("1", "true", "yes", "on"):
        return []
    try:
        import cluster_topic_picker
        return cluster_topic_picker.candidates_for_refill(bank, root=ROOT)
    except Exception as exc:
        print("  ! GENSEO_CLUSTER_PICKER is set, picker skipped (%s: %s)" % (type(exc).__name__, exc))
        return []


def candidates(bank, rows, ctx):
    """Board ideas (status=idea; a matching bank topic fills their blanks) first, then bank topics that are
    not on the board yet — best first. Returns (candidates, bank ids the board holds as queued/done/skipped)."""
    year = str(ctx["day"].year)
    topics = {t["id"]: dict(t, title=t["title"].replace("{year}", year)) for t in bank["topics"]}
    on_board, out = {}, []
    for i, r in enumerate(rows):
        rid, st = (r.get("id") or "").strip(), (r.get("status") or "").strip().lower()
        if rid:
            on_board[rid] = st
        if st != "idea":
            continue
        d = dict(topics.get(rid, {}))
        d.update({k: v for k, v in {
            "id": rid, "product": r.get("product"), "primary": r.get("primary_keyword"),
            "title": (r.get("working_title") or "").replace("{year}", year),
            "secondary": [s.strip() for s in (r.get("secondary") or "").split(";") if s.strip()],
            "segment": r.get("segment"), "intent": r.get("intent"), "template": r.get("template"),
            "angle": r.get("angle")}.items() if v})
        out.append(norm_cand(d, bank, "board", 0, i))
    for i, (tid, t) in enumerate(topics.items()):
        if tid not in on_board:
            out.append(norm_cand(t, bank, "topic-bank", t.get("priority", 9), 1000 + i))
    for i, extra in enumerate(cluster_picker_topics(bank)):
        out.append(norm_cand(extra, bank, "cluster-picker", -1, i))
    out.sort(key=lambda c: (c["priority"], ctx["fam_count"].get(c["family"], 0), c["order"]))
    return out, [tid for tid in topics if on_board.get(tid) not in (None, "idea")]


def fitness(text, articles):
    """topic_fitness.assess under every stocked-brand token in `text`; the worst verdict wins. assess() uses
    whichever token set iteration yields first, so one call can PASS under 'fusiforce' where 'creatine
    gummies' FAILs [covered]."""
    toks = sorted(b for b in tf.STOCKED_BRANDS if b in text.lower()) or [None]
    orig, worst = tf.STOCKED_BRANDS, None
    try:
        for tok in toks:
            if tok:
                tf.STOCKED_BRANDS = {tok}
            tf._ARTIDX.clear()  # keyed by id(list): a freed list's id can be reused by the next one
            r = tf.assess(text, articles=articles)
            if worst is None or RANK[r[0]] > RANK[worst[0]]:
                worst = r
    finally:
        tf.STOCKED_BRANDS = orig
    return worst


def fit_ok(r):
    return r[0] == "PASS" or (r[0] == "REVIEW" and r[1] == "covered-segment")


def clash(c, t):
    """Why candidate c duplicates t (a queued ticket, a live article or an earlier candidate), or ''."""
    if t.get("primary") and t["primary"] == c["primary"]:
        return "same primary keyword"
    for a in (c["title"], c["primary"]):
        for b in (t.get("title"), t.get("primary")):
            if b and jaccard(a, b) >= tf.DUP_JACCARD:
                return f"title overlap {jaccard(a, b):.2f}"
    shared = c["segs"] & t["segs"]
    if c["family"] in t["fams"] and shared:
        return f"{c['family']} + {'/'.join(sorted(shared))}"
    return ""


def pick_collections(c, ctx):
    """Up to 2 live, allowed collections from the product's list — ones that contain the product first;
    best-seller as a browse link when none is left."""
    have = [h for h in ctx["bank"]["products"][c["product"]]["collections"]
            if h in ctx["collections"] and br.collection_allowed(h)]
    have.sort(key=lambda h: c["product"] not in ctx["collections"][h])
    if not have and "best-seller" in ctx["collections"]:
        have = ["best-seller"]
    return have[:2]


def step0(c, ctx):
    """STEP 0 suggest.json -> (reject reason or '', note for the ticket)."""
    if ctx["suggest"] != "live":
        return "", "suggest.json not checked at build time — STEP 0 must check"
    url = (f"{SITE}/search/suggest.json?q={urllib.parse.quote(c['primary'])}"
           "&resources%5Btype%5D=article&resources%5Blimit%5D=10")
    try:
        hits = [(a.get("title") or "", (a.get("url") or "").split("?")[0])
                for a in json.loads(fetch(url, tries=2))["resources"]["results"].get("articles", [])]
    except (OSError, ValueError, KeyError) as e:
        return "", f"suggest.json unreachable at build time ({type(e).__name__}) — STEP 0 must check"
    for title, link in hits:
        h = link.rstrip("/").rsplit("/", 1)[-1]
        a = {"title": title, "fams": families_of(f"{title} {h.replace('-', ' ')}", ctx["bank"]),
             "segs": segments_of(title, ctx["bank"])}
        why = "targets the primary" if re.search(r"\b%s\b" % re.escape(norm_kw(c["primary"])), norm_kw(title)) else clash(c, a)
        if why:
            return f"STEP 0 suggest.json: live article ({why}) — “{title}” {link}", ""
    if not hits:
        return "", f"suggest.json 0 article matches ({ctx['stamp']} ICT)"
    return "", (f"suggest.json {len(hits)} match(es), none targets this primary: "
                f"{'; '.join(t for t, _ in hits[:3])} ({ctx['stamp']} ICT)")


def check(c, ctx):
    """Gates 1-8 in order -> (first failure reason, None) or (None, info for render)."""
    bank, prods = ctx["bank"], ctx["products"]
    pages = [c["product"]] + c["inline"]
    miss = [k for k in REQUIRED if not c.get(k)]
    if miss:
        return f"incomplete brief: no {', '.join(miss)}", None
    if c["segment"] not in bank["segments"]:
        return f"unknown segment {c['segment']!r} (add it to the bank's segments)", None
    if c["template"] not in TEMPLATES:
        return f"unknown template {c['template']!r}", None
    if len(c["title"]) > MAX_TITLE:
        return f"title is {len(c['title'])} chars (max {MAX_TITLE})", None
    unmapped = [h for h in pages if h not in bank["products"]]
    if unmapped:
        return f"not in the bank's products map: {', '.join(unmapped)}", None
    bad = []
    for h in pages:
        try:
            guard_hero(h)
        except br.GuardError:
            bad.append(h)
    if bad:
        return f"brand_rules: {', '.join(bad)} is not an allowed product", None
    hits = banned(" ".join([c["primary"], c["title"], c["intent"], c["angle"], c["evidence"]]
                           + c["secondary"] + c["fanout"]), bank)
    if hits:
        return f"banned in the brief: {'; '.join(hits)}", None
    for h in pages:
        if h not in prods:
            return f"/products/{h} is not on the live store", None
        if not prods[h]["available"]:
            return f"/products/{h} is sold out", None
    colls = pick_collections(c, ctx)
    if not colls:
        return "no live collection to link (validate_article.py needs 2 collection links)", None
    text = f"{c['primary']} {c['title']}".lower()
    hit = next((rx.pattern for rx in bank["covered_rx"] if rx.search(text)), None)
    if hit:
        return f"covered topic (queue header rule 6): /{hit}/", None
    for t in ctx["queue"]:
        why = clash(c, t)
        if why:
            status = re.sub(r"\s*https?://\S+", "", t["status"])[:30] or "open"
            return f"already queued ({why}): #{t['id'] or '?'} [{status}] “{t['title'] or t['primary']}”", None
    for t in ctx["passed"]:
        why = clash(c, t)
        if why:
            return f"duplicates {t['id']} earlier in this run ({why})", None
    for a in ctx["articles"]:
        why = clash(c, a) or (slug(c["title"]) == a["handle"] and "same slug")
        if why:
            return f"already live ({why}): “{a['title']}” /blogs/{BLOG}/{a['handle']}", None
    fits = [fitness(c["primary"], ctx["articles"]), fitness(c["title"], ctx["articles"])]
    for which, r in zip(("primary", "title"), fits):
        if not fit_ok(r):
            return f"topic_fitness {r[0]} [{r[1]}] on the {which}: {r[2][:110]}", None
    why, note = step0(c, ctx)
    if why:
        return why, None
    links = [h for h in c["link"] if h in ctx["live_handles"] and ar.article_link_allowed(h)]
    info = {"verdict": max(fits, key=lambda r: RANK[r[0]]), "suggest": note, "colls": colls, "links": links,
            "dropped": [h for h in c["link"] if h not in links]}
    hits = banned(render(c, "XX0000-0", ctx, info), bank)
    if hits:
        return f"banned in the rendered ticket: {'; '.join(hits)}", None
    return None, info


# ---------- batch ----------

def select(passed, count, cap):
    """At most `cap` per family first; only if that leaves the batch short do the next-best fill it."""
    out, per = [], {}
    for c in passed:
        if len(out) < count and per.get(c["family"], 0) < cap:
            out.append(c)
            per[c["family"]] = per.get(c["family"], 0) + 1
    taken = {c["id"] for c in out}
    return out + [c for c in passed if c["id"] not in taken][:max(0, count - len(out))]


def order(batch, last_template):
    """Never the same template twice running whenever the mix allows it (the most frequent remaining template
    goes first — greedy without that look-ahead strands e.g. two EDITORIALs at the end), then, where that leaves
    a choice, not the same family twice running; ties keep the round-robin-by-family order."""
    fams = list(dict.fromkeys(c["family"] for c in batch))
    lanes = {f: [c for c in batch if c["family"] == f] for f in fams}
    rr = []
    while any(lanes.values()):
        rr += [lanes[f].pop(0) for f in fams if lanes[f]]
    out, prev_t, prev_f = [], last_template, None
    while rr:
        left = {}
        for c in rr:
            left[c["template"]] = left.get(c["template"], 0) + 1
        i = min(range(len(rr)), key=lambda k: (rr[k]["template"] == prev_t, -left[rr[k]["template"]],
                                               rr[k]["family"] == prev_f, k))
        c = rr.pop(i)
        out.append(c)
        prev_t, prev_f = c["template"], c["family"]
    return out


def render(c, tid, ctx, info):
    guard_hero(c["product"])
    for h in c.get("inline") or []:
        guard_hero(h)
    bank, prods = ctx["bank"], ctx["products"]
    name = bank["products"][c["product"]]["name"]

    def membership(h):
        if c["product"] in ctx["collections"].get(h, []):
            return "contains it"
        return f"browse link — {name} is not in it, never claim it is"

    cols = info["colls"]
    coll = (f"`/collections/{cols[0]}` twice ({membership(cols[0])})" if len(cols) == 1 else
            ", ".join(f"`/collections/{h}` ({membership(h)})" for h in cols))
    if c["product"] == br.AGEAURA_OK:
        coll += " · no other AgeAura product and no AgeAura collection link (brand_rules)"
    v, code = info["verdict"][0], info["verdict"][1]
    out = [f"- [ ] **#{tid} — {c['primary']}** — `{c['title']}`",
           f"  - **Primary keyword:** `{c['primary']}` · **Secondary:** {', '.join(c['secondary'])}",
           f"  - **Search intent:** {c['intent']}",
           f"  - **Template:** {c['template']} · **Gate:** topic_fitness {v} [{code}]"
           + (f" → {GREENLIT}" if v == "REVIEW" else "") + f" · STEP 0: {info['suggest']}",
           f"  - **Hero product:** `/products/{c['product']}` ({name}, {money(prods[c['product']]['price'])}, "
           f"in stock {ctx['day']})"]
    if c["inline"]:
        out.append("  - **Inline (comparison only):** " + ", ".join(
            f"`/products/{h}` ({bank['products'][h]['name']}, {money(prods[h]['price'])})" for h in c["inline"]))
    if ff.HANDLE in [c["product"]] + c["inline"]:
        out.append("  - " + ff.TICKET_LINE)
    if sw.HANDLE in [c["product"]] + c["inline"]:
        out.append("  - " + sw.TICKET_LINE)
    if gr.HANDLE in [c["product"]] + c["inline"]:
        out.append("  - " + gr.TICKET_LINE)
    if sr.HANDLE in [c["product"]] + c["inline"]:
        out.append("  - " + sr.TICKET_LINE)
    if tk.HANDLE in [c["product"]] + c["inline"]:
        out.append("  - " + tk.TICKET_LINE)
    out += [f"  - **Collection links (≥2, verify live):** {coll}", f"  - **Angle:** {c['angle']}"]
    if c["fanout"]:
        out.append("  - **Fan-out answers to cover:** " + "; ".join(c["fanout"]))
    out.append("  - **Evidence to fetch & confirm (claims log):** " + (
        c["evidence"] or "every number, study and dose from a source fetched at write time — cut what you cannot confirm"))
    if info["links"]:
        out.append("  - **Link, don't restate:** " + ", ".join(f"`/blogs/{BLOG}/{h}`" for h in info["links"]))
    src = "blog listing + sitemap + Atom" + (" + local caches" if ctx["local"] else "")
    out += ["  - **Author:** roster.json byline — exact name + bio resolved at write time; never invent a person, "
            "reviewer or credential",
            f"  - **Dedup note:** {c['family']} + {c['segment']} checked {ctx['day']} against "
            f"{len(ctx['live_handles'])} live articles ({src}) and all {len(ctx['queue'])} tickets in this file; "
            "STEP 0 re-checks at write time"]
    return "\n".join(out)


def batch_header(ctx, ids):
    return HEADER.format(day=ctx["day"], first=ids[0], last=ids[-1], stamp=ctx["stamp"],
                         n_live=len(ctx["live_handles"]), greenlit=GREENLIT,
                         src="blog listing + sitemap + Atom" + (" + local caches" if ctx["local"] else ""))


def append_block(path, block, expect):
    """Append through a temp copy that must pass lint_tickets.py first, so the live queue never holds an
    unlinted batch."""
    if read(path) != expect:
        raise Refuse(f"{os.path.basename(path)} changed while refilling — nothing written; re-run")
    fd, tmp = tempfile.mkstemp(prefix=".refill-", suffix=".md", dir=os.path.dirname(os.path.abspath(path)))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(expect.rstrip("\n") + "\n\n" + block.rstrip("\n") + "\n")
        r = subprocess.run([sys.executable, LINT, tmp], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        if r.returncode != 0:
            raise Refuse(f"lint_tickets.py rejected the batch — nothing written:\n{r.stdout}{r.stderr}")
        os.chmod(tmp, os.stat(path).st_mode & 0o777)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def refill(a):
    text = read(a.queue)
    n_open = len(OPEN_RX.findall(text))
    if a.if_below is not None and n_open >= a.if_below:
        print(f"refill_tickets: {n_open} open ticket(s) >= {a.if_below} — nothing to do")
        return 0
    if a.count < 1:
        print("refill_tickets: --count < 1 — nothing to do")
        return 0
    try:
        bank = load_bank(a.bank)
    except (OSError, ValueError, KeyError, re.error) as e:
        raise Refuse(f"topic bank unreadable ({type(e).__name__}: {e})")
    rows, fields = read_board(a.board)
    queue = parse_queue(text)
    now = dt.datetime.now(ICT)
    if a.offline:
        store = load_cache()
    else:
        try:
            store = read_store()
        except (OSError, ValueError, KeyError) as e:
            raise Refuse(f"live store unreadable ({type(e).__name__}: {e}) — failing closed")
        save_cache(store, now.strftime("%Y-%m-%d %H:%M ICT"))
    ctx = build_ctx(bank, queue, store, local_inventory(), now, "skip" if a.offline or a.no_suggest else "live")
    ids_day = batch_day(now, a.day)
    cands, held = candidates(bank, rows, ctx)
    print(f"refill_tickets: {n_open} open ticket(s) · {ctx['stamp']} ICT · {len(ctx['live_handles'])} live articles"
          f"{' + local caches' if ctx['local'] else ''} · {sum(1 for p in store[0].values() if p['available'])} "
          f"products in stock · {len(cands)} candidate topic(s)"
          + (f" ({len(held)} bank topic(s) already on the board)" if held else ""))
    passed, rejected = [], []
    for c in cands:
        why, info = check(c, ctx)
        if why:
            rejected.append((c, why))
            print(f"  ✗ {c['id']}: {why}")
        else:
            c["info"] = info
            passed.append(c)
            ctx["passed"].append(c)
            for h in info["dropped"]:
                print(f"  ! {c['id']}: /blogs/{BLOG}/{h} is not live — left out of the ticket")
    last_tpl = next((t["template"] for t in reversed(queue) if t["template"]), None)
    batch = order(select(passed, a.count, a.max_per_family), last_tpl)
    chosen = {c["id"] for c in batch}
    reserve = [c["id"] for c in passed if c["id"] not in chosen]
    if reserve:
        print("  reserve (passes today, not queued): " + ", ".join(reserve))
    if not batch:
        print(f"✗ 0 of {len(cands)} topic(s) passed — add topics to templates/article-topic-bank.json or board/ideas.csv")
        return 3
    ids = next_ids(text, a.prefix, ids_day, len(batch))
    block = (batch_header(dict(ctx, day=ids_day), ids) + "\n"
             + "\n\n".join(render(c, tid, ctx, c["info"]) for c, tid in zip(batch, ids)) + "\n")
    if a.dry_run:
        print(f"---- dry run: {len(batch)} ticket(s); queue and board untouched ----\n{block}")
    else:
        append_block(a.queue, block, text)
        write_board(a.board, update_board(rows, queue, list(zip(batch, ids)), rejected, ctx["day"]), fields)
        print(f"✓ appended {len(batch)} ticket(s) to {os.path.relpath(a.queue, ROOT)} — {n_open + len(batch)} open now; "
              f"{os.path.relpath(a.board, ROOT)} updated")
        for c, tid in zip(batch, ids):
            print(f"  #{tid:<12} {c['template']:<10}  {c['title']}")
    if len(batch) < a.count:
        print(f"! only {len(batch)} of {a.count} passed — add topics to templates/article-topic-bank.json or board/ideas.csv")
        return 3
    return 0


# ---------- self-test (offline) ----------

FIX_QUEUE = """# Daily ticket queue (fixture)

## Rules
6. Prose that mentions a `[ ]` ticket and a link:
- [a markdown link](https://example.com)

## [DONE 2026-08-07 https://wellnessnest.co/blogs/news/creatine-gummies-vs-powder] Ticket #1 — NEW ARTICLE

- **Primary keyword:** `creatine gummies vs powder`
- **Template:** EDITORIAL

## [ ] Ticket #2 — NEW ARTICLE

- **Primary keyword:** `turkesterone for women`

# BATCH 2026-08-13

| # | Title | Brand · segment | Products |
|---|---|---|---|
| ~~15~~ ✅ | [Shilajit Side Effects: 7 Signs (US 2026)](https://wellnessnest.co/blogs/news/shilajit-side-effects) — LIVE | shilajit · side effects | resin |

## Shipped without a ticket

- **[DONE 2026-08-13] #23 — turkesterone timing** — mined on the day because the queue was
  empty. → https://wellnessnest.co/blogs/news/turkesterone-timing

# BATCH 2026-10-08

- [DONE 2026-10-09 https://wellnessnest.co/blogs/news/nmn-and-alcohol] **#MB1008-5 — nmn and alcohol** (buffer) — `NMN and Alcohol: Can You Drink? (US 2026)`
  - **Primary keyword:** `nmn and alcohol` · **Secondary:** nmn hangover
  - **Template:** STORY · **Gate:** topic_fitness PASS [brand]

- [SKIPPED-UNFIT 2026-10-09 needs vetting] **#CA1009-3 — shilajit for women** — `Shilajit for Women: 4 Facts (US 2026)`
  - **Template:** LISTICLE
"""
FIX_LIVE = [
    ("creatine-gummies-for-women-5-facts", "Creatine Gummies for Women: 5 Facts (US 2026)"),
    ("how-long-does-turkesterone-take-to-work-us-2026", "How Long Does Turkesterone Take to Work? (US 2026)"),
    ("vaginal-probiotics-which-strains-actually-work-us-2026", "Vaginal Probiotics: Which Strains Actually Work? (US 2026)"),
    ("nmn-and-tmg-together-why-the-pairing-matters-us-2026", "NMN and TMG Together: Why the Pairing Matters (US 2026)"),
    ("shilajit-resin-guide", "Shilajit Resin: What It Is and How to Use It"),
]
FIX_COLLS = {"best-seller": ["fusiforce-creatine-gummies", "florafresh-vaginal-probiotics-gummies"],
             "mens-essential-collection": ["fusiforce-creatine-gummies", "turkesterone-advanced-formula"],
             "shilajit-wellness-stack": ["shilasource-himalayan-shilajit-resin", "turkesterone-advanced-formula"],
             "womens-essentials-collection": ["florafresh-vaginal-probiotics-gummies"],
             "ageaura": ["ageaura-pure-nmn-tmg-p2"]}
FIX_GOOD = {"id": "good", "product": "florafresh-vaginal-probiotics-gummies",
            "primary": "vaginal probiotics morning or night",
            "title": "When to Take Vaginal Probiotics: Morning or Night? (US 2026)",
            "secondary": ["best time to take vaginal probiotics"], "segment": "timing",
            "intent": "buyer who wants one daily routine", "template": "LISTICLE",
            "angle": "Consistency beats clock time.", "fanout": ["with food or not"],
            "evidence": "Probiotic survival with vs without a meal — fetch and confirm.",
            "link": ["vaginal-probiotics-which-strains-actually-work-us-2026", "urolithin-a-old-page", "not-a-live-page"]}


def fixture_ctx(bank, queue):
    prods = {h: {"title": p["name"], "price": "59.99", "available": h != "shilajit-shockwave"}
             for h, p in bank["products"].items()}
    prods["ageaura-pure-nmn-tmg-p2"] = {"title": "AgeAura duo", "price": "59.95", "available": True}
    return build_ctx(bank, queue, (prods, FIX_COLLS, FIX_LIVE), [], dt.datetime(2026, 10, 9, 9, 0, tzinfo=ICT), "skip")


def self_test():
    results = []

    def t(name, cond, detail=""):
        results.append(bool(cond))
        print(f"  {'✓' if cond else '✗'} {name}" + (f" — got {detail}" if not cond and detail != "" else ""))

    bank = load_bank(BANK)
    errs = lint_bank(bank)
    t(f"topic bank lints clean ({len(bank['topics'])} topics)", not errs, "; ".join(errs[:6]))

    q = parse_queue(FIX_QUEUE)
    t("queue parse: 6 tickets incl. a shipped-table row and a bold DONE head; prose `[ ]` and links ignored",
      [x["id"] for x in q] == ["1", "2", "15", "23", "MB1008-5", "CA1009-3"], [x["id"] for x in q])
    t("queue parse: states", [x["state"] for x in q] == ["done", "open", "done", "done", "done", "skipped"],
      [x["state"] for x in q])
    t("queue parse: primaries (field and head fallbacks)",
      [x["primary"] for x in q] == ["creatine gummies vs powder", "turkesterone for women", "", "turkesterone timing",
                                    "nmn and alcohol", "shilajit for women"], [x["primary"] for x in q])
    t("queue parse: a table row's title comes from its link", q[2]["title"] == "Shilajit Side Effects: 7 Signs (US 2026)",
      q[2]["title"])
    t("open count = the wrapper's grep", len(OPEN_RX.findall(FIX_QUEUE)) == 1)
    t("ids continue after the highest used", next_ids(FIX_QUEUE, "CA", dt.date(2026, 10, 9), 2) == ["CA1009-4", "CA1009-5"])
    fixed = dt.datetime(2026, 10, 11, 18, 43, tzinfo=ICT)
    t("--day overrides the batch date", batch_day(fixed, "2026-10-12") == dt.date(2026, 10, 12))
    t("--day empty keeps the clock date", batch_day(fixed, None) == dt.date(2026, 10, 11))
    try:
        batch_day(fixed, "1012")
        bad_day = False
    except Refuse:
        bad_day = True
    t("--day rejects a non-ISO date", bad_day)
    t("families_of", families_of("NMN + TMG for runners", bank) == {"nmn"}
      and families_of("FloraFresh for BV", bank) == {"probiotic"})
    t("segments_of", segments_of("vaginal probiotics morning or night", bank) == {"timing"}
      and "athletes" in segments_of("nmn for runners", bank)
      and segments_of("NMN and Exercise: Before or After a Workout? (US 2026)", bank) == {"athletes", "timing"}
      and segments_of("creatine gummies on rest days", bank) == {"rest-days"}
      and segments_of("vaginal probiotics while traveling", bank) == {"travel"}
      and segments_of("Best Time to Take Creatine: Before or After? (US 2026)", bank) == {"timing"})

    calls = []

    def fake_meta(h):
        calls.append(h)
        return {"c-cut": ("C Full Title (US 2026)", "c-cut"), "renamed": ("B SEO Title | Wellness Nest", "b"),
                "deleted": ("", None)}.get(h, ("", h))

    m = merge_titles({"a-cut": "A Long Title That Gets Cut...", "b": "B Short (US 2026)", "c-cut": "C Full Ti…",
                      "e-cut": "E Title Cut..."},
                     [{"a-cut": "", "d-new": "", "renamed": "", "deleted": ""},
                      {"a-cut": "A Long Title That Gets Cut Here (US 2026)"}], fake_meta)
    t("titles: full titles replace the listing's cut ones, a stale sitemap's renamed handle folds in and its "
      "deleted one drops; pages fetched only for cut or empty titles",
      m == {"a-cut": "A Long Title That Gets Cut Here (US 2026)", "b": "B Short (US 2026)",
            "c-cut": "C Full Title (US 2026)", "e-cut": "E Title Cut", "d-new": "d new"}
      and sorted(calls) == ["c-cut", "d-new", "deleted", "e-cut", "renamed"], (m, sorted(calls)))

    r = fitness("fusiforce creatine gummies for women", [{"title": FIX_LIVE[0][1], "handle": FIX_LIVE[0][0]}])
    t("topic_fitness: worst verdict across stocked-brand tokens ('creatine gummies' FAIL beats 'fusiforce' PASS)",
      r[:2] == ("FAIL", "covered"), r[:2])
    t("topic_fitness: STOCKED_BRANDS restored afterwards", {"fusiforce", "creatine gummies", "nmn"} <= tf.STOCKED_BRANDS)

    ctx = fixture_ctx(bank, q)

    def gate(ctx_, **kw):
        c = norm_cand(dict(FIX_GOOD, **kw), ctx_["bank"], "topic-bank", 1, 0)
        why, info = check(c, ctx_)
        return why, info, c

    why, info, good = gate(ctx)
    t("a clean topic passes all 8 gates", why is None, why)
    if info:
        t("verdict REVIEW [covered-segment] is carried to the ticket", info["verdict"][:2] == ("REVIEW", "covered-segment"),
          info["verdict"][:2])
        t("non-live and urolithin link handles are left out",
          info["links"] == ["vaginal-probiotics-which-strains-actually-work-us-2026"], info["links"])
        t("offline STEP 0 is flagged for the writer", "STEP 0 must check" in info["suggest"])
        text = render(good, "CA1009-4", ctx, info)
        t("rendered ticket carries every field", all(k in text for k in (
            "**Primary keyword:**", "**Secondary:**", "**Search intent:**", "**Template:**", "**Hero product:**",
            "**Collection links", "**Angle:**", "**Author:**", "**Dedup note:**")))
        t("rendered ticket counts as open for the wrapper", OPEN_RX.match(text) is not None)
        t("rendered ticket is brand-clean", not banned(text, bank), banned(text, bank))
        t("FloraFresh ticket carries the Supplement Facts label formula", ff.TICKET_LINE in text)
        t("FloraFresh ticket: no Shockwave pack-label line", sw.TICKET_LINE not in text)
        t("FloraFresh ticket: no Gold Resin pack-label line", gr.TICKET_LINE not in text)
        t("FloraFresh ticket: no ShilaSource resin pack-label line", sr.TICKET_LINE not in text)
        t("FloraFresh ticket: no Turkesterone pack-label line", tk.TICKET_LINE not in text)
        header = batch_header(ctx, ["CA1009-4", "CA1009-4"])
        t("batch header is brand-clean and sets no image override",
          not banned(header, bank) and "ALL images NO-FACE" not in header)

    tampered = dict(bank, products=dict(bank["products"], **{"ageaura-pure-nmn-tmg-p2": {
        "name": "AgeAura duo", "family": "nmn", "collections": ["best-seller"]}}))
    rejects = [
        ("AgeAura duo product (brand_rules)", fixture_ctx(tampered, parse_queue(FIX_QUEUE)),
         dict(product="ageaura-pure-nmn-tmg-p2", primary="nmn morning or night",
              title="NMN: Morning or Night? (US 2026)"), "brand_rules"),
        ("Urolithin in the angle", ctx, dict(angle="Compare it with Urolithin A."), "banned"),
        ("FloraFresh 15 billion CFU in the secondary (label: 1 billion)", ctx,
         dict(secondary=["15 billion cfu probiotic"]), "banned"),
        ("FloraFresh formula cited from the PDP", ctx,
         dict(evidence="FloraFresh CFU and strains from the live PDP."), "banned"),
        ("sold-out hero product", ctx, dict(product="shilajit-shockwave", primary="shilajit shockwave for athletes",
                                            title="Shilajit Shockwave for Athletes (US 2026)", segment="athletes"),
         "sold out"),
        ("covered topic (rule 6)", ctx, dict(title="Menopause Probiotics: Morning or Night? (US 2026)"), "covered topic"),
        ("same primary already queued", ctx, dict(product="turkesterone-advanced-formula", primary="turkesterone for women",
                                                  title="Turkesterone for Women: 3 Facts (US 2026)", segment="for-women"),
         "already queued"),
        ("family + segment already live", ctx, dict(product="turkesterone-advanced-formula",
                                                    primary="turkesterone results how long",
                                                    title="Turkesterone Results: How Long Until They Show? (US 2026)",
                                                    segment="how-long"), "already live"),
        ("no segment modifier (topic_fitness FAIL)", ctx, dict(product="fusiforce-creatine-gummies",
                                                               primary="creatine gummies energy boost",
                                                               title="Creatine Gummies Energy Boost Facts (US 2026)",
                                                               segment="caffeine"), "topic_fitness FAIL"),
        ("title over 60 chars", ctx, dict(title="When to Take Vaginal Probiotics: Morning or Night? A US Guide 2026"), "chars"),
        ("unknown segment", ctx, dict(segment="zodiac"), "unknown segment"),
    ]
    for name, ctx_, kw, want in rejects:
        why, _, _ = gate(ctx_, **kw)
        t(f"rejects: {name}", why is not None and want in why, why)
    ctx["passed"].append(good)
    why, _, _ = gate(ctx, id="good-2", primary="best time of day for vaginal probiotics",
                     title="Vaginal Probiotics: Best Time of Day? (US 2026)")
    t("rejects: same family + segment as a topic passed earlier in the run", why is not None and "earlier in this run" in why, why)
    ctx["passed"].clear()

    why, info, nmn = gate(ctx, product="ageaura-pure-nmn-tmg-nad-complex", primary="nmn for runners",
                          title="NMN for Runners: What a 6-Week Trial Found (US 2026)", segment="athletes",
                          template="STORY", link=[])
    t("AgeAura NMN + TMG topic passes", why is None, why)
    if info:
        text = render(nmn, "CA1009-5", ctx, info)
        t("AgeAura ticket: best-seller twice as a browse link, no AgeAura collection",
          "`/collections/best-seller` twice (browse link" in text and "/collections/ageaura" not in text)
        t("AgeAura ticket: no FloraFresh formula line", ff.TICKET_LINE not in text)
        t("AgeAura ticket: no Shockwave pack-label line", sw.TICKET_LINE not in text)
        t("AgeAura ticket: no Gold Resin pack-label line", gr.TICKET_LINE not in text)
        t("AgeAura ticket: no ShilaSource resin pack-label line", sr.TICKET_LINE not in text)
        t("AgeAura ticket: no Turkesterone pack-label line", tk.TICKET_LINE not in text)

    sw_cand = norm_cand(dict(FIX_GOOD, id="sw", product="shilajit-shockwave",
                             primary="shilajit shockwave for athletes",
                             title="Shilajit Shockwave for Athletes (US 2026)",
                             secondary=["shockwave drops for training"], segment="athletes",
                             intent="athlete comparing a drops format", template="EDITORIAL",
                             angle="What the drops format changes about a daily routine.",
                             fanout=["how do you take shilajit drops"],
                             evidence="Pack label identity lines only.",
                             link=[]), ctx["bank"], "topic-bank", 1, 0)
    sw_info = {"verdict": ("PASS", "brand"), "suggest": "offline",
               "colls": ["shilajit-wellness-stack", "mens-essential-collection"], "links": []}
    sw_text = render(sw_cand, "CA1009-9", ctx, sw_info)
    t("Shockwave ticket carries the pack-label line", sw.TICKET_LINE in sw_text)
    t("Shockwave ticket: no Gold Resin pack-label line", gr.TICKET_LINE not in sw_text)
    t("Shockwave ticket: no ShilaSource resin pack-label line", sr.TICKET_LINE not in sw_text)
    t("Shockwave ticket: no Turkesterone pack-label line", tk.TICKET_LINE not in sw_text)
    t("Shockwave ticket is brand-clean", not br.violations(sw_text), br.violations(sw_text))

    gr_cand = norm_cand(dict(FIX_GOOD, id="gr", product="pure-shilajit-gold-resin",
                             primary="shilajit gold resin for athletes",
                             title="Shilajit Gold Resin for Athletes (US 2026)",
                             secondary=["gold resin jar for training"], segment="athletes",
                             intent="athlete comparing a resin jar", template="EDITORIAL",
                             angle="What the jar format changes about a daily routine.",
                             fanout=["how do you take shilajit resin"],
                             evidence="Pack label lines only.",
                             link=[]), ctx["bank"], "topic-bank", 1, 0)
    gr_info = {"verdict": ("PASS", "brand"), "suggest": "offline",
               "colls": ["shilajit-wellness-stack", "mens-essential-collection"], "links": []}
    gr_text = render(gr_cand, "CA1009-8", ctx, gr_info)
    t("Gold Resin ticket carries the pack-label line", gr.TICKET_LINE in gr_text)
    t("Gold Resin ticket: no Shockwave pack-label line", sw.TICKET_LINE not in gr_text)
    t("Gold Resin ticket: no ShilaSource resin pack-label line", sr.TICKET_LINE not in gr_text)
    t("Gold Resin ticket: no Turkesterone pack-label line", tk.TICKET_LINE not in gr_text)
    t("Gold Resin ticket is brand-clean", not br.violations(gr_text), br.violations(gr_text))

    sr_cand = norm_cand(dict(FIX_GOOD, id="sr", product="shilasource-himalayan-shilajit-resin",
                             primary="shilajit resin for athletes",
                             title="ShilaSource Resin for Athletes (US 2026)",
                             secondary=["shilasource resin for training"], segment="athletes",
                             intent="athlete comparing a resin jar", template="EDITORIAL",
                             angle="What the jar format changes about a daily routine.",
                             fanout=["how do you take shilajit resin"],
                             evidence="Pack label lines only.",
                             link=[]), ctx["bank"], "topic-bank", 1, 0)
    sr_info = {"verdict": ("PASS", "brand"), "suggest": "offline",
               "colls": ["shilajit-wellness-stack", "mens-essential-collection"], "links": []}
    sr_text = render(sr_cand, "CA1010-1", ctx, sr_info)
    t("ShilaSource resin ticket carries the pack-label line", sr.TICKET_LINE in sr_text)
    t("ShilaSource resin ticket: no Shockwave pack-label line", sw.TICKET_LINE not in sr_text)
    t("ShilaSource resin ticket: no Gold Resin pack-label line", gr.TICKET_LINE not in sr_text)
    t("ShilaSource resin ticket: no Turkesterone pack-label line", tk.TICKET_LINE not in sr_text)
    t("ShilaSource resin ticket is brand-clean", not br.violations(sr_text), br.violations(sr_text))

    tk_cand = norm_cand(dict(FIX_GOOD, id="tk", product="turkesterone-advanced-formula",
                             primary="turkesterone for athletes",
                             title="Turkesterone for Athletes (US 2026)",
                             secondary=["turkesterone drug test"], segment="athletes",
                             intent="athlete checking a capsule jar", template="EDITORIAL",
                             angle="What the jar front actually lists.",
                             fanout=["what does the jar front show"],
                             evidence="Pack label lines only.",
                             link=[]), ctx["bank"], "topic-bank", 1, 0)
    tk_info = {"verdict": ("PASS", "brand"), "suggest": "offline",
               "colls": ["mens-essential-collection", "shilajit-wellness-stack"], "links": []}
    tk_text = render(tk_cand, "CA1010-2", ctx, tk_info)
    t("Turkesterone ticket carries the pack-label line", tk.TICKET_LINE in tk_text)
    t("Turkesterone ticket: no Shockwave pack-label line", sw.TICKET_LINE not in tk_text)
    t("Turkesterone ticket: no Gold Resin pack-label line", gr.TICKET_LINE not in tk_text)
    t("Turkesterone ticket: no ShilaSource resin pack-label line", sr.TICKET_LINE not in tk_text)
    t("Turkesterone ticket is brand-clean", not br.violations(tk_text), br.violations(tk_text))

    mk = [("1", "probiotic", "LISTICLE"), ("2", "probiotic", "COMPARISON"), ("3", "turkesterone", "EDITORIAL"),
          ("4", "creatine", "LISTICLE"), ("5", "creatine", "LISTICLE"), ("6", "nmn", "EDITORIAL")]
    o = order([{"id": i, "family": f, "template": tp} for i, f, tp in mk], "LISTICLE")
    t("order: no template twice running (incl. the queue's last one)",
      all(x["template"] != y["template"] for x, y in zip([{"template": "LISTICLE"}] + o, o)), [x["template"] for x in o])
    t("order: no family twice running", all(x["family"] != y["family"] for x, y in zip(o, o[1:])), [x["family"] for x in o])
    mk = [("1", "probiotic", "STORY"), ("2", "creatine", "EDITORIAL"), ("3", "turkesterone", "COMPARISON"),
          ("4", "shilajit", "LISTICLE"), ("5", "creatine", "EDITORIAL"), ("6", "shilajit", "EDITORIAL")]
    o = order([{"id": i, "family": f, "template": tp} for i, f, tp in mk], "LISTICLE")
    t("order: no template twice running when half the batch shares one (no EDITORIAL pair stranded at the end)",
      all(x["template"] != y["template"] for x, y in zip([{"template": "LISTICLE"}] + o, o)), [x["template"] for x in o])
    sel = select([{"id": str(i), "family": f} for i, f in enumerate(["a", "a", "a", "b"])], 3, 2)
    t("select: family cap first, then fill", [c["id"] for c in sel] == ["0", "1", "3"], [c["id"] for c in sel])

    with tempfile.TemporaryDirectory() as d:
        board = os.path.join(d, "board", "ideas.csv")
        rows = [{"id": "old", "status": "queued", "ticket_id": "#MB1008-5"},
                {"id": "idea-1", "status": "idea", "volume": "320"}]
        write_board(board, update_board(rows, q, [(good, "CA1009-4")], [], dt.date(2026, 10, 9)), list(BOARD_FIELDS))
        back, fields = read_board(board)
        st = {r["id"]: r for r in back}
        t("board: queued row flips to done when its ticket is DONE", st["old"]["status"] == "done", st["old"])
        t("board: new ticket upserted as queued, volume 'No data'",
          st["good"]["status"] == "queued" and st["good"]["ticket_id"] == "#CA1009-4" and st["good"]["volume"] == "No data")
        t("board: existing columns and values preserved", fields == BOARD_FIELDS and st["idea-1"]["volume"] == "320")

        path = os.path.join(d, "daily-tickets.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(FIX_QUEUE)
        block = batch_header(ctx, ["CA1009-4", "CA1009-4"]) + "\n" + render(good, "CA1009-4", ctx, gate(ctx)[1])
        append_block(path, block, FIX_QUEUE)
        after = read(path)
        t("append: lint-clean batch written; open count +1", after.startswith(FIX_QUEUE.rstrip("\n"))
          and len(OPEN_RX.findall(after)) == 2)
        for name, bad_block, expect in (
                ("a banned link in an open ticket", "- [ ] **#CA1009-9 — x** — `X`\n  - see /collections/ageaura", after),
                ("a queue that changed underneath", block, FIX_QUEUE)):
            try:
                append_block(path, bad_block, expect)
                refused = False
            except Refuse:
                refused = True
            t(f"append: refuses {name}, file untouched", refused and read(path) == after)
    print(f"self-test: {sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Refill daily-tickets.md with gated, product-mapped article tickets.")
    ap.add_argument("--count", type=int, default=8, help="new tickets to add (default 8)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the batch and every rejection; queue and board untouched")
    ap.add_argument("--if-below", type=int, metavar="K", help="do nothing while K or more tickets are open")
    ap.add_argument("--prefix", default=os.environ.get("GENSEO_TICKET_PREFIX", "RF"),
                    help="ticket id prefix, 1-4 capitals: MM Mini wrapper, MB MacBook, CA Cursor cloud (default RF "
                         "or $GENSEO_TICKET_PREFIX)")
    ap.add_argument("--day", default=None, metavar="YYYY-MM-DD",
                    help="batch date for the title and ticket ids (default: today ICT). "
                         "The build stamp, in-stock date, and dedup date stay the real clock, "
                         "so a Monday queue can be prepared the evening before.")
    ap.add_argument("--max-per-family", type=int, default=2, help="spread: per-family cap before filling (default 2)")
    ap.add_argument("--queue", default=QUEUE)
    ap.add_argument("--bank", default=BANK)
    ap.add_argument("--board", default=BOARD)
    ap.add_argument("--offline", action="store_true",
                    help="use the last store snapshot (state/refill_cache.json); suggest.json not checked")
    ap.add_argument("--no-suggest", action="store_true", help="skip the STEP 0 suggest.json pre-check")
    ap.add_argument("--self-test", action="store_true", help="offline fixtures; no network, writes nothing")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not re.fullmatch(r"[A-Z]{1,4}", a.prefix):
        print("✗ --prefix must be 1-4 capital letters")
        return 1
    try:
        return refill(a)
    except Refuse as e:
        print(f"✗ {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

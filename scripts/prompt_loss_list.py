#!/usr/bin/env python3
"""Score 30 buyer prompts against local blog titles and propose gaps that pass the dup gate.

Reads the committed cluster map, daily-tickets.md, the topic bank, and the frozen
PR #81 prompt texts. Writes docs/PROMPT_LOSS_LIST.md and
docs/PROMPT_LOSS_TOPIC_PROPOSALS.md. Does not append to the live queue, does not
read or write Shopify, and does not call a paid API.

  python3 scripts/prompt_loss_list.py
  python3 scripts/prompt_loss_list.py --check

Exit 0 when the report is consistent. Exit 2 when the prompt file, the ledger,
or an output path is refused.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ageaura_rules as ar
import brand_rules as br
import florafresh_rules as ff
import refill_tickets as rt
import shilasource_resin_rules as sr
import topic_fitness as tf
import wn_clusters as wc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LISTED = "2026-10-21"
PROMPTS = os.path.join(ROOT, "data", "prompt_loss", "buyer_prompts.json")
MAP_MD = os.path.join(ROOT, "docs", "CLUSTER_MAP.md")
QUEUE = os.path.join(ROOT, "daily-tickets.md")
LEDGER = os.path.join(ROOT, "data", "ai_visibility", "observations.json")
CATALOG = os.path.join(ROOT, "tests", "fixtures", "prompt_loss", "visibility_prompts.json")
BANK = os.path.join(ROOT, "templates", "article-topic-bank.json")
REPORT = os.path.join(ROOT, "docs", "PROMPT_LOSS_LIST.md")
PROPOSALS = os.path.join(ROOT, "docs", "PROMPT_LOSS_TOPIC_PROPOSALS.md")

BRANDS = {
    "ageaura": {
        "name": "AgeAura",
        "cluster_id": "ageaura-nmn",
        "product": "ageaura-pure-nmn-tmg-nad-complex",
        "family": "nmn",
    },
    "shilasource": {
        "name": "ShilaSource",
        "cluster_id": "shilajit",
        "product": "shilasource-himalayan-shilajit-resin",
        "family": "shilajit",
    },
    "florafresh": {
        "name": "FloraFresh",
        "cluster_id": "florafresh",
        "product": "florafresh-vaginal-probiotics-gummies",
        "family": "probiotic",
    },
}
FUNNEL = {
    "best": "consideration",
    "for-condition": "consideration",
    "vs": "evaluation",
    "where-to-buy": "decision",
    "price": "decision",
}
INTENT_RX = {
    "best": re.compile(r"\bbest\b(?!\s+time\b)", re.I),
    "vs": re.compile(r"\bvs\.?\b|\bversus\b", re.I),
    "where-to-buy": re.compile(r"\bwhere to buy\b", re.I),
    "price": re.compile(r"\b(?:price|cost|how much does|per serving)\b", re.I),
    "for-condition": re.compile(
        r"\bfor (?:men|women|beginners|seniors|athletes|runners)\b|"
        r"\bover \d+\b|\bafter \d+\b|\bfor fertility\b",
        re.I,
    ),
}
PLATFORMS = ("chatgpt", "gemini", "google_ai_mode", "ai_overviews", "perplexity", "grok")
BRAND_CLUSTERS = frozenset(spec["cluster_id"] for spec in BRANDS.values())
FORBIDDEN = frozenset(("daily-tickets.md", "daily-landing-tickets.md"))
GAP_FIELDS = (
    "primary", "title", "segment", "template", "secondary",
    "search_intent", "angle", "evidence", "link",
)
LINK_RX = re.compile(
    r"\[([^\]]+)\]\(https://wellnessnest\.co/blogs/news/([a-z0-9-]+)\)"
)
ID_RX = re.compile(r"^Id: `([a-z0-9-]+)`", re.M)
BUILT_RX = re.compile(r"Built (\d{4}-\d{2}-\d{2})")
BLOG_URL = re.compile(r"https://wellnessnest\.co/blogs/news/([a-z0-9-]+)")
NEAREST_FLOOR = 0.4
SEL_PIZZI = (
    "https://searchengineland.com/how-to-prioritize-seo-content-updates-and-new-opportunities-497220"
)
SEL_GEO = "https://searchengineland.com/what-is-generative-engine-optimization-geo-444418"


class Refuse(Exception):
    """An output path is the live queue. Nothing is written."""


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def load_json(path):
    return json.loads(read(path))


def norm_text(text):
    return " ".join(re.findall(r"[a-z0-9]+", (text or "").lower()))


def cell(value):
    text = value if value else "—"
    return text.replace("|", "\\|").replace("\n", " ")


def blob(article):
    return (article["title"] + " " + article["handle"].replace("-", " ")).lower()


def has_token(text, token):
    return re.search(r"\b" + re.escape(token.lower()) + r"\b", text) is not None


def other_sku_penalty(article):
    handle = article["handle"]
    if "gold-resin" in handle or "shockwave" in handle:
        return 1
    return 0


def articles_from_map_md(text):
    articles, order = [], 0
    for part in re.split(r"\n(?=## )", text):
        found = ID_RX.search(part)
        if not found:
            continue
        cluster_id = found.group(1)
        for line in part.splitlines():
            role = "pillar" if line.lstrip().startswith("Pillar:") else "spoke"
            for title, handle in LINK_RX.findall(line):
                if any(a["handle"] == handle for a in articles):
                    continue
                articles.append({
                    "title": title,
                    "handle": handle,
                    "cluster_id": cluster_id,
                    "role": role,
                    "source": "cluster-map",
                    "order": order,
                })
                order += 1
    return articles


def articles_from_map_json(data):
    articles, order = [], 0
    for cluster in data.get("clusters") or []:
        cluster_id = cluster.get("id") or ""
        rows = []
        pillar = cluster.get("pillar")
        if pillar:
            rows.append(("pillar", pillar))
        for spoke in cluster.get("spokes") or []:
            rows.append(("spoke", spoke))
        for role, row in rows:
            if not row or row.get("stale_only") or row.get("dupe"):
                continue
            handle = row.get("handle") or ""
            if not handle or any(a["handle"] == handle for a in articles):
                continue
            articles.append({
                "title": row.get("title") or "",
                "handle": handle,
                "cluster_id": cluster_id,
                "role": role,
                "source": "cluster-map",
                "order": order,
            })
            order += 1
    return articles


def articles_from_queue(text, known):
    """DONE blog URLs that the cluster map does not already list.

    Open tickets are not treated as published. Urolithin and other clusters
    stay out of this coverage set.
    """
    out, order = [], 0
    for ticket in rt.parse_queue(text or ""):
        if ticket.get("state") != "done":
            continue
        raw = ticket.get("status", "") + " " + ticket.get("head", "")
        for handle in BLOG_URL.findall(raw):
            if handle in known or any(a["handle"] == handle for a in out):
                continue
            if not ar.article_link_allowed(handle):
                continue
            title = ticket.get("title") or handle.replace("-", " ")
            cluster_id = wc.assign_cluster(title + " " + handle.replace("-", " "))
            if cluster_id not in BRAND_CLUSTERS:
                continue
            out.append({
                "title": title,
                "handle": handle,
                "cluster_id": cluster_id,
                "role": "queue-live",
                "source": "ticket-queue",
                "order": order,
            })
            order += 1
    return out


def load_articles(map_path, queue_text):
    if map_path.endswith(".json"):
        data = load_json(map_path)
        if not isinstance(data, dict):
            raise ValueError("cluster map JSON must be an object")
        articles = articles_from_map_json(data)
        built = str(data.get("built") or "")
    else:
        text = read(map_path)
        articles = articles_from_map_md(text)
        found = BUILT_RX.search(text)
        built = found.group(1) if found else ""
    extra = articles_from_queue(queue_text, {a["handle"] for a in articles})
    for item in extra:
        item["order"] += len(articles)
    return articles + extra, built, extra


def load_prompts(path):
    data = load_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("prompts"), list):
        raise ValueError("prompts file must be an object with a prompts list")
    return data["prompts"]


def load_catalog(path):
    data = load_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("prompts"), list):
        raise ValueError("prompt catalog must be an object with a prompts list")
    return data["prompts"]


def load_ledger(path):
    if not path or not os.path.isfile(path):
        return {"state": "missing", "rows": []}
    data = load_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("observations"), list):
        raise ValueError("ledger must be an object with an observations list")
    rows = data["observations"]
    return {"state": "ok" if rows else "empty", "rows": rows}


def visibility_dup(text, catalog):
    own = norm_text(text)
    best_id, best_score = "", 0.0
    for item in catalog:
        other = item.get("text") or ""
        if own and own == norm_text(other):
            return "exact match of %s" % item.get("id", "?")
        score = rt.jaccard(text, other)
        if score > best_score:
            best_id, best_score = item.get("id", "?"), score
    if best_score >= tf.DUP_JACCARD:
        return "token overlap with %s" % best_id
    return ""


def nearest_prompt(text, catalog):
    best_id, best_score = "", 0.0
    for item in catalog:
        score = rt.jaccard(text, item.get("text") or "")
        if score > best_score:
            best_id, best_score = item.get("id", ""), score
    if best_score >= NEAREST_FLOOR:
        return best_id
    return ""


def _yn(value):
    if value in ("yes", "no", "unknown"):
        return value
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "unknown"


def _platform(row):
    plat = str(row.get("platform") or "").strip().lower()
    if plat in PLATFORMS:
        return plat
    observer = str(row.get("observer") or "").strip().lower()
    if observer in PLATFORMS:
        return observer
    return ""


def visibility_label(prompt_id, ledger):
    """One line for this prompt id. Unobserved cells stay unknown. No rate."""
    real = []
    for row in ledger.get("rows") or []:
        if not isinstance(row, dict) or row.get("prompt_id") != prompt_id:
            continue
        if row.get("observed") is not True:
            continue
        if not row.get("observer") or not row.get("observed_at"):
            continue
        real.append(row)
    if not real:
        return "unknown"
    parts, seen = [], set()
    for row in real:
        plat = _platform(row) or "unspecified"
        if plat in seen:
            continue
        seen.add(plat)
        cited = _yn(row.get("domain_cited"))
        bit = "%s: mentioned %s, cited %s" % (plat, _yn(row.get("brand_mentioned")), cited)
        if cited == "yes" and row.get("cited_url"):
            bit += " (%s)" % row["cited_url"]
        parts.append(bit)
    named = {plat for plat in seen if plat in PLATFORMS}
    if named != set(PLATFORMS):
        parts.append("other platforms unknown")
    return "; ".join(parts)


def portfolio_problems(prompts):
    problems = []
    if len(prompts) != 30:
        problems.append("expected 30 prompts, found %d" % len(prompts))
    counts = {}
    for prompt in prompts:
        counts[prompt.get("brand_id")] = counts.get(prompt.get("brand_id"), 0) + 1
    for brand_id, spec in BRANDS.items():
        if counts.get(brand_id) != 10:
            problems.append("%s has %d prompts, expected 10" % (spec["name"], counts.get(brand_id, 0)))
        intents = {p.get("intent") for p in prompts if p.get("brand_id") == brand_id}
        missing = [name for name in FUNNEL if name not in intents]
        if missing:
            problems.append("%s is missing intent %s" % (spec["name"], ", ".join(missing)))
    return problems


def schema_problems(prompts):
    problems, seen = [], set()
    for prompt in prompts:
        pid = prompt.get("id") or "?"
        if pid in seen:
            problems.append("%s: duplicate id" % pid)
        seen.add(pid)
        brand = BRANDS.get(prompt.get("brand_id"))
        if not brand:
            problems.append("%s: unknown brand" % pid)
        else:
            for key in ("cluster_id", "product", "family"):
                if prompt.get(key) != brand[key]:
                    problems.append("%s: %s does not match %s" % (pid, key, prompt.get("brand_id")))
        intent = prompt.get("intent")
        if intent not in FUNNEL:
            problems.append("%s: unknown intent" % pid)
        elif prompt.get("funnel_stage") != FUNNEL[intent]:
            problems.append("%s: funnel does not match intent" % pid)
        if not prompt.get("text"):
            problems.append("%s: missing text" % pid)
        anchors = prompt.get("anchors")
        if not isinstance(anchors, list) or not anchors:
            problems.append("%s: anchors must be a non-empty list" % pid)
        if not isinstance(prompt.get("focus"), list):
            problems.append("%s: focus must be a list" % pid)
    return problems


def catalog_problems(prompts, catalog):
    problems = []
    for prompt in prompts:
        why = visibility_dup(prompt.get("text") or "", catalog)
        if why:
            problems.append("%s duplicates the prompt set (%s)" % (prompt.get("id"), why))
    return problems


def _focus_hits(prompt, article):
    text = blob(article)
    return sum(1 for token in prompt.get("focus") or [] if has_token(text, token))


def _intent_hit(prompt, article):
    return 1 if INTENT_RX[prompt["intent"]].search(article["title"]) else 0


def _anchors_ok(prompt, article):
    text = blob(article)
    return all(has_token(text, token) for token in prompt["anchors"])


def classify_prompt(prompt, articles):
    pool = [a for a in articles if a["cluster_id"] == prompt["cluster_id"]]
    hits = [a for a in pool if _anchors_ok(prompt, a)]
    full = [
        a for a in hits
        if _focus_hits(prompt, a) == len(prompt.get("focus") or []) and _intent_hit(prompt, a)
    ]
    if full:
        match = min(full, key=lambda a: (
            other_sku_penalty(a),
            0 if a["role"] == "pillar" else 1,
            0 if a["source"] == "cluster-map" else 1,
            a["order"],
        ))
        return "covered", match, "title matches the buyer intent"
    if hits:
        match = min(hits, key=lambda a: (
            -_focus_hits(prompt, a),
            -_intent_hit(prompt, a),
            other_sku_penalty(a),
            -rt.jaccard(prompt["text"], a["title"]),
            0 if a["role"] == "pillar" else 1,
            0 if a["source"] == "cluster-map" else 1,
            a["order"],
        ))
        missing = [token for token in prompt.get("focus") or [] if not has_token(blob(match), token)]
        bits = []
        if missing:
            bits.append("misses " + ", ".join(missing))
        if not _intent_hit(prompt, match):
            bits.append("misses the %s wording" % prompt["intent"])
        return "weak", match, "; ".join(bits) or "partial title"
    return "gap", None, "no title has every anchor"


def _clash_article(article, bank):
    text = "%s %s" % (article["title"], article["handle"].replace("-", " "))
    return {
        "title": article["title"],
        "handle": article["handle"],
        "primary": "",
        "fams": rt.families_of(text, bank),
        "segs": rt.segments_of(text, bank),
    }


def _clash_ticket(ticket, bank):
    title = ticket.get("title") or ""
    primary = ticket.get("primary") or ""
    return {
        "title": title,
        "primary": primary,
        "id": ticket.get("id") or "",
        "fams": rt.families_of("%s %s" % (title, primary), bank),
        "segs": rt.segments_of("%s %s" % (title, primary), bank),
    }


def _candidate(prompt, bank):
    primary = " ".join((prompt.get("primary") or "").lower().split())
    segment = prompt.get("segment") or ""
    return {
        "primary": primary,
        "title": prompt.get("title") or "",
        "family": prompt["family"],
        "fams": {prompt["family"]},
        "segs": ({segment} - {""}) | rt.segments_of(primary, bank),
        "segment": segment,
        "template": prompt.get("template") or "",
        "product": prompt["product"],
    }


def _strip_score(text):
    return re.sub(r"\s*\(overlap [0-9.]+\)", "", text or "")


def gate_gap(prompt, articles, tickets, catalog, bank):
    """First failure wins. A pass is a rendered ticket whose brand lint is empty."""
    missing = [key for key in GAP_FIELDS if not prompt.get(key)]
    if missing:
        return "incomplete brief: no %s" % ", ".join(missing), None
    primary = " ".join(prompt["primary"].lower().split())
    title = prompt["title"]
    if len(title) > rt.MAX_TITLE:
        return "title is %d chars (max %d)" % (len(title), rt.MAX_TITLE), None
    if prompt["segment"] not in bank["segments"]:
        return "unknown segment %r" % prompt["segment"], None
    if prompt["segment"] not in rt.segments_of(primary, bank):
        return "primary does not match segment %s" % prompt["segment"], None
    if prompt["template"] not in rt.TEMPLATES:
        return "unknown template %s" % prompt["template"], None
    query = " ".join([primary, title, prompt["text"]])
    if wc.query_blocked(prompt["cluster_id"], query):
        return "query_blocked", None
    if prompt["cluster_id"] == "florafresh" and re.search(r"\bfor men\b", primary):
        return "product-fit: FloraFresh is not a for-men product", None
    brief = " ".join([
        primary, title, prompt["text"], prompt["angle"], prompt["evidence"],
        " ".join(prompt["secondary"]), prompt["product"],
    ])
    guarded = wc.guard_topic_text(brief, prompt["product"])
    if guarded:
        return "guard: %s" % "; ".join(guarded), None
    banned = rt.banned(brief, bank)
    if banned:
        return "banned: %s" % "; ".join(banned), None
    covered = next((rx.pattern for rx in bank["covered_rx"] if rx.search("%s %s" % (primary, title.lower()))), None)
    if covered:
        return "covered topic (queue header rule 6): /%s/" % covered, None
    fitness_rows = [{"title": a["title"], "handle": a["handle"]} for a in articles]
    verdicts = []
    for which, text in (("primary", primary), ("title", title)):
        result = rt.fitness(text, fitness_rows)
        verdicts.append(result)
        if not rt.fit_ok(result):
            return "topic_fitness %s [%s] on the %s: %s" % (
                result[0], result[1], which, _strip_score(result[2])[:180]
            ), None
    candidate = _candidate(prompt, bank)
    for article in articles:
        why = rt.clash(candidate, _clash_article(article, bank))
        if why:
            return "already live (%s): %s" % (why, article["title"]), None
    for ticket in tickets:
        why = rt.clash(candidate, _clash_ticket(ticket, bank))
        if why:
            label = ticket.get("title") or ticket.get("primary") or "?"
            return "already queued (%s): #%s %s" % (why, ticket.get("id") or "?", label), None
    why = visibility_dup(primary, catalog)
    if why:
        return "prompt set (%s)" % why, None
    bad_links = [h for h in prompt["link"] if not ar.article_link_allowed(h)]
    if bad_links:
        return "link handle is not allowed: %s" % ", ".join(bad_links), None
    verdict = max(verdicts, key=lambda row: rt.RANK[row[0]])
    rendered = render_ticket(prompt, "PL1021-0", bank, verdict)
    lint = br.violations(rendered)
    if lint:
        return "rendered ticket: %s" % "; ".join(lint), None
    return "", {"verdict": verdict, "prompt": prompt}


def render_ticket(prompt, tid, bank, verdict):
    product = bank["products"][prompt["product"]]
    name = product["name"]
    cols = [h for h in product.get("collections") or [] if br.collection_allowed(h)][:2]
    coll = ", ".join("`/collections/%s`" % h for h in cols)
    coll += " (membership not re-checked; do not claim membership)"
    if prompt["product"] == br.AGEAURA_OK:
        coll += "; an AgeAura collection link is not allowed"
    code = "%s [%s]" % (verdict[0], verdict[1])
    lines = [
        "- [ ] **#%s — %s** — `%s`" % (tid, prompt["primary"], prompt["title"]),
        "  - **Primary keyword:** `%s` · **Secondary:** %s" % (
            " ".join(prompt["primary"].lower().split()), ", ".join(prompt["secondary"])
        ),
        "  - **Search intent:** %s" % prompt["search_intent"],
        "  - **Template:** %s · **Gate:** topic_fitness %s" % (prompt["template"], code),
        "  - **Hero product:** `/products/%s` (%s)" % (prompt["product"], name),
        "  - **Price:** not recorded. Re-check `/products/%s.js` before any draft. Do not invent a price." % prompt["product"],
    ]
    if prompt["product"] == ff.HANDLE:
        lines.append("  - " + ff.TICKET_LINE)
    if prompt["product"] == sr.HANDLE:
        lines.append("  - " + sr.TICKET_LINE)
    lines += [
        "  - **Collection links:** %s" % coll,
        "  - **Angle:** %s" % prompt["angle"],
        "  - **Evidence to fetch and confirm:** %s" % prompt["evidence"],
        "  - **Link, do not restate:** " + ", ".join("`/blogs/news/%s`" % h for h in prompt["link"]),
        "  - **Author:** roster.json byline, resolved at write time. Do not invent a person, reviewer, or credential.",
        "  - **Dedup note:** suggest.json was not called. Not appended to daily-tickets.md.",
    ]
    return "\n".join(lines)


def evaluate(prompts, articles, queue_text, catalog, ledger, bank, portfolio=False):
    problems = []
    if portfolio:
        problems.extend(portfolio_problems(prompts))
    problems.extend(schema_problems(prompts))
    problems.extend(catalog_problems(prompts, catalog))
    tickets = rt.parse_queue(queue_text or "")
    if problems:
        return {"problems": problems, "rows": [], "passed": [], "withheld": [], "tickets": tickets}
    rows, passed, withheld = [], [], []
    for prompt in prompts:
        status, match, note = classify_prompt(prompt, articles)
        row = {
            "prompt": prompt,
            "status": status,
            "article": match,
            "note": note,
            "ai": visibility_label(prompt["id"], ledger),
            "nearest": nearest_prompt(prompt["text"], catalog),
            "gate": "",
        }
        if status == "gap":
            reason, info = gate_gap(prompt, articles, tickets, catalog, bank)
            if reason:
                row["gate"] = reason
                withheld.append(row)
            else:
                row["gate"] = "pass"
                passed.append(info)
        rows.append(row)
    rendered = []
    for index, info in enumerate(passed, start=1):
        tid = "PL1021-%d" % index
        text = render_ticket(info["prompt"], tid, bank, info["verdict"])
        rendered.append({"id": tid, "prompt": info["prompt"], "text": text})
    return {
        "problems": [],
        "rows": rows,
        "passed": rendered,
        "withheld": withheld,
        "tickets": tickets,
    }


def _brand_name(prompt):
    return BRANDS[prompt["brand_id"]]["name"]


def _article_cell(article):
    if not article:
        return "—"
    text = "%s (`/blogs/news/%s`)" % (article["title"], article["handle"])
    if article["source"] != "cluster-map":
        text += " — published after the cluster map"
    return text


def _counts(rows):
    table = {brand: {"covered": 0, "weak": 0, "gap": 0} for brand in BRANDS}
    for row in rows:
        table[row["prompt"]["brand_id"]][row["status"]] += 1
    return table


def render_report(result, meta):
    rows = result["rows"]
    counts = _counts(rows)
    brands = list(BRANDS)
    lines = [
        "# Buyer prompt-loss list",
        "",
        "Listed %s. Blog articles only. No Shopify write, no theme edit, no paid-traffic page." % LISTED,
        "",
        "## Why this list",
        "",
        "Search Engine Land, 20 Oct 2026, read for the 21 Oct digest:",
        "",
        "- [How to prioritize SEO content updates and new opportunities](%s) (Gaetano Pizzi). A new URL is for a customer need the site does not already cover. When a page already answers the question, update that page." % SEL_PIZZI,
        "- [What is generative engine optimization (GEO)](%s) (Leigh Mckenzie). A buyer prompt asks which product to buy for a person in a specific situation. A mention and a citation are different measurements. This file does not record either one unless the ledger has a real observation." % SEL_GEO,
        "",
        "The 30 prompts extend the 51 hypothesised prompts from PR #81. They do not copy those strings. AI visibility stays unknown unless `data/ai_visibility/observations.json` has a row with `observed: true`, an observer, and a date.",
        "",
        "## How a row was scored",
        "",
        "Coverage uses titles and handles from `docs/CLUSTER_MAP.md` (built %s, %d articles) plus %d DONE `/blogs/news/` URLs in `daily-tickets.md` that are not already in the map. Open tickets are not treated as published articles. They do block a new proposal." % (
            meta["built"] or "unknown", meta["map_count"], len(meta["queue_live"])
        ),
        "",
    ]
    if meta["queue_live"]:
        lines.append("Added from the queue, and not used as the matching article for any of the 30:")
        lines.append("")
        for article in meta["queue_live"]:
            lines.append("- `%s` — %s" % (article["handle"], article["title"]))
        lines.append("")
    lines += [
        "- **covered**: a title in that brand's cluster contains every anchor and every focus token, and the title matches the buyer intent (best, vs, where to buy, price, or for-condition).",
        "- **weak**: a title contains every anchor, and it misses the intent or a focus token. The named article is the closest one. The action is to update that article.",
        "- **gap**: no title contains every anchor.",
        "",
        "A gap is offered as a topic proposal only when `topic_fitness`, `wn_clusters.query_blocked`, and `refill_tickets.clash` all pass against the map and against every ticket in `daily-tickets.md`. A failure is withheld. Nothing is appended to the live queue. Traffic numbers are not copied into this file.",
        "",
        "## Counts",
        "",
        "| Status | %s | Total |" % " | ".join(BRANDS[b]["name"] for b in brands),
        "| --- | %s | --- |" % " | ".join("---" for _ in brands),
    ]
    for status in ("covered", "weak", "gap"):
        nums = [counts[b][status] for b in brands]
        lines.append("| %s | %s | %d |" % (status, " | ".join(str(n) for n in nums), sum(nums)))
    observed = sum(1 for row in rows if row["ai"] != "unknown")
    lines += [
        "",
        "AI visibility rows with `observed: true`: %d. Ledger: %s." % (observed, meta["ledger_state"]),
        "",
        "Proposals passed: %d. Withheld: %d." % (len(result["passed"]), len(result["withheld"])),
        "",
        "## The 30 prompts",
        "",
        "| ID | Brand | Funnel | Intent | Prompt | Status | Article | AI visibility | Nearest prompt-set row |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        prompt = row["prompt"]
        lines.append("| %s |" % " | ".join(cell(part) for part in (
            prompt["id"],
            _brand_name(prompt),
            prompt["funnel_stage"],
            prompt["intent"],
            prompt["text"],
            row["status"],
            _article_cell(row["article"]),
            row["ai"],
            row["nearest"],
        )))
    lines += ["", "## Weak: update these articles", ""]
    weak = [row for row in rows if row["status"] == "weak"]
    if not weak:
        lines.append("None.")
    else:
        lines.append("| ID | Article | What the title misses |")
        lines.append("| --- | --- | --- |")
        for row in weak:
            lines.append("| %s | %s | %s |" % (
                cell(row["prompt"]["id"]), cell(_article_cell(row["article"])), cell(row["note"])
            ))
    lines += ["", "## Gaps and the dup/cluster gate", ""]
    gaps = [row for row in rows if row["status"] == "gap"]
    if not gaps:
        lines.append("None.")
    else:
        lines.append("| ID | Primary | Gate |")
        lines.append("| --- | --- | --- |")
        for row in gaps:
            lines.append("| %s | %s | %s |" % (
                cell(row["prompt"]["id"]),
                cell(row["prompt"].get("primary") or ""),
                cell(row["gate"]),
            ))
    lines += [
        "",
        "## AI visibility",
        "",
        "PR #81's ledger is not on this branch, so every cell above is unknown unless a local `data/ai_visibility/observations.json` was passed in. Unknown is not a no. This file does not turn the empty ledger into a mention or a citation.",
        "",
        "Join key is `prompt_id` only. The 51 hypothesised prompts are a different set, so their rows are not copied onto these 30.",
        "",
        "## What needs a GO",
        "",
        "- Appending any proposal to `daily-tickets.md`. This run passed %d." % len(result["passed"]),
        "- Publishing or updating a live post. A weak row names the article to update, and this run does not update it.",
        "- Filling the AI visibility ledger, or running an adapter. Do not treat this file as a measured AI result.",
        "- A new URL for a withheld gap. The gate reason is the reason to leave it.",
        "",
    ]
    return "\n".join(lines)


def render_proposals(result):
    lines = [
        "# Topic proposals from the buyer prompt-loss list",
        "",
        "DO NOT paste into daily-tickets.md without Kevin's GO. This file is not the live queue.",
        "",
        "Listed %s. Passed: %d. Withheld: %d." % (LISTED, len(result["passed"]), len(result["withheld"])),
        "",
        "suggest.json was not called. No Shopify read. No price was recorded.",
        "",
        "## Passed",
        "",
    ]
    if not result["passed"]:
        lines.append("None. The dup/cluster gate did not pass a new URL. Update the article named on a weak row, or leave a covered row alone.")
    else:
        for item in result["passed"]:
            lines.append(item["text"])
            lines.append("")
    lines += ["", "## Withheld", ""]
    if not result["withheld"]:
        lines.append("None.")
    else:
        lines.append("| ID | Primary | Reason |")
        lines.append("| --- | --- | --- |")
        for row in result["withheld"]:
            reason = (row["gate"] or "").replace("|", "\\|")
            if len(reason) > 220:
                reason = reason[:217] + "..."
            lines.append("| %s | %s | %s |" % (
                row["prompt"]["id"], row["prompt"].get("primary") or "", reason
            ))
    lines.append("")
    return "\n".join(lines)


def forbidden_path(path):
    if os.path.basename(os.path.abspath(path)) in FORBIDDEN:
        return True
    real = os.path.realpath(path)
    root = os.path.realpath(ROOT)
    return any(real == os.path.join(root, name) for name in FORBIDDEN)


def write_outputs(report_path, proposals_path, report, proposals):
    for path in (report_path, proposals_path):
        if forbidden_path(path):
            raise Refuse("refusing to write %s" % os.path.basename(path))
    for path, text in ((report_path, report), (proposals_path, proposals)):
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)


def run(paths, portfolio=True):
    prompts = load_prompts(paths["prompts"])
    catalog = load_catalog(paths["catalog"])
    ledger = load_ledger(paths["ledger"])
    bank = rt.load_bank(paths["bank"])
    queue_text = read(paths["queue"]) if os.path.isfile(paths["queue"]) else ""
    articles, built, extra = load_articles(paths["map"], queue_text)
    result = evaluate(prompts, articles, queue_text, catalog, ledger, bank, portfolio=portfolio)
    result["meta"] = {
        "built": built,
        "map_count": sum(1 for a in articles if a["source"] == "cluster-map"),
        "queue_live": extra,
        "ledger_state": ledger["state"],
    }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Buyer prompt-loss list. Does not write the live queue.")
    parser.add_argument("--prompts", default=PROMPTS)
    parser.add_argument("--map", default=MAP_MD)
    parser.add_argument("--queue", default=QUEUE)
    parser.add_argument("--ledger", default=LEDGER)
    parser.add_argument("--catalog", default=CATALOG)
    parser.add_argument("--bank", default=BANK)
    parser.add_argument("--report", default=REPORT)
    parser.add_argument("--proposals", default=PROPOSALS)
    parser.add_argument("--check", action="store_true", help="score only; write nothing")
    args = parser.parse_args(argv)
    paths = {
        "prompts": args.prompts,
        "map": args.map,
        "queue": args.queue,
        "ledger": args.ledger,
        "catalog": args.catalog,
        "bank": args.bank,
    }
    try:
        result = run(paths, portfolio=True)
    except (ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Refuse as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if result["problems"]:
        for problem in result["problems"]:
            print(problem, file=sys.stderr)
        return 2
    report = render_report(result, result["meta"])
    proposals = render_proposals(result)
    if args.check:
        sys.stdout.write(report)
        return 0
    try:
        write_outputs(args.report, args.proposals, report, proposals)
    except Refuse as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print("prompts %d covered %d weak %d gap %d passed %d withheld %d" % (
        len(result["rows"]),
        sum(1 for row in result["rows"] if row["status"] == "covered"),
        sum(1 for row in result["rows"] if row["status"] == "weak"),
        sum(1 for row in result["rows"] if row["status"] == "gap"),
        len(result["passed"]),
        len(result["withheld"]),
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())

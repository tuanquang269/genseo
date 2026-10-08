#!/usr/bin/env python3
"""geo_official_lint.py: WARN-only GEO checks from the official-source rules
(knowledge_base/AEO_GEO_GUIDELINES.md §6). Never blocks publishing: always exits 0.
It does not replace or loosen scripts/validate_article.py.

Usage: python3 scripts/geo_official_lint.py ARTICLE.(html|md) [--title "..."] [--json]
"""
import json, re, sys, html as _html
from datetime import date

RULES = [
    ("back-reference", r"\b(as (mentioned|discussed|noted|explained|stated) (above|earlier|before|previously)|building on the previous section|in the previous section)\b",
     "Section depends on earlier text; make each H2 self-contained (AEO_GEO §1).", "knowledge_base/AEO_GEO_GUIDELINES.md §1"),
    ("unsupported-superlative", r"\bwellness nest\b[^.]{0,40}\b(is|are)\b[^.]{0,20}\b(the )?(best|leading|#1|number one|no\.? ?1|top-rated|most trusted|best retailer)\b",
     "Superlative about Wellness Nest; keep only if a cited, verifiable source supports it (fact-check all text).", "https://developers.google.com/search/docs/fundamentals/using-gen-ai-content"),
    ("unverified-store-claim", r"\b(visit our (store|shop)|pick ?up (your order|in[- ]store|at (our|wellness nest'?s?) store)|same[- ]day delivery|local warehouse|in-store pickup)\b",
     "Physical store / pickup / same-day claim; remove unless Kevin confirmed it's true.", "knowledge_base/AEO_GEO_GUIDELINES.md §6.5"),
    ("fake-freshness", r"\b(updated (daily|weekly|every day)|freshly updated|newly updated for)\b",
     "Freshness wording; only claim 'updated' when the main content substantially changed.", "https://developers.google.com/search/docs/fundamentals/creating-helpful-content"),
    ("invented-credential", r"\b(board[- ]certified|clinically proven|doctor[- ]approved|dietitian[- ]approved|fda[- ]approved)\b",
     "Credential/approval claim; needs a verifiable source (supplements are not FDA-approved).", "https://developers.google.com/search/docs/fundamentals/creating-helpful-content"),
]
AUTH_DOMAINS = ("pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov", "nih.gov", "ods.od.nih.gov", "fda.gov",
                "cdc.gov", "who.int", "cochrane", "nejm.org", "jamanetwork.com", "bmj.com", "thelancet.com",
                "efsa.europa.eu", "nhs.uk", "doi.org")

def strip_tags(s):
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    return _html.unescape(re.sub(r"(?s)<[^>]+>", " ", s))

def lint(raw, title=""):
    out = []
    text = re.sub(r"\s+", " ", strip_tags(raw))
    hay = (title + " . " + text)
    for rid, pat, msg, src in RULES:
        for m in re.finditer(pat, hay, re.I):
            ctx = hay[max(0, m.start()-50):m.end()+50].strip()
            out.append({"rule": rid, "msg": msg, "match": ctx, "source": src})
    # images without alt (HTML) or empty markdown alt
    imgs = re.findall(r"(?is)<img\b[^>]*>", raw)
    no_alt = [i for i in imgs if not re.search(r'\balt\s*=\s*"[^"]{3,}"', i)]
    no_alt += re.findall(r"!\[\s*\]\([^)]*\)", raw)
    if no_alt:
        out.append({"rule": "image-alt", "msg": f"{len(no_alt)} image(s) without descriptive alt text (fact-check alt text too).",
                    "match": "", "source": "https://developers.google.com/search/docs/fundamentals/using-gen-ai-content"})
    # stale year in title
    yrs = [int(y) for y in re.findall(r"\b(20[12]\d)\b", title)]
    if yrs and max(yrs) < date.today().year:
        out.append({"rule": "stale-title-year", "msg": f"Title year {max(yrs)} is older than the current year.",
                    "match": title, "source": "https://developers.google.com/search/docs/appearance/publication-dates"})
    # multiple Article JSON-LD nodes
    n_art = len(re.findall(r'"@type"\s*:\s*"(?:Article|BlogPosting|NewsArticle)"', raw))
    if n_art > 1:
        out.append({"rule": "duplicate-article-schema", "msg": f"{n_art} Article/BlogPosting nodes; emit one with consistent dates.",
                    "match": "", "source": "https://developers.google.com/search/docs/appearance/publication-dates"})
    # authoritative citations (inference rule)
    links = re.findall(r'(?i)(?:href\s*=\s*"|\]\()(https?://[^")\s]+)', raw)
    if not any(any(d in l.lower() for d in AUTH_DOMAINS) for l in links):
        out.append({"rule": "no-primary-source", "msg": "No link to a primary study or regulator (PubMed/NIH/FDA/CDC/WHO...). Inference rule for AI-search citability.",
                    "match": "", "source": "https://developers.openai.com/api/docs/guides/deep-research"})
    return out

def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__); return 0
    title = ""
    if "--title" in argv:
        title = argv[argv.index("--title") + 1]
    raw = open(argv[1], encoding="utf-8", errors="replace").read()
    if not title:
        m = re.search(r"(?is)<title>(.*?)</title>|<h1[^>]*>(.*?)</h1>|^#\s+(.+)$", raw, re.M)
        if m:
            title = strip_tags(next(g for g in m.groups() if g)).strip()
    res = lint(raw, title)
    if "--json" in argv:
        print(json.dumps({"warnings": res, "count": len(res)}, ensure_ascii=False, indent=1))
    else:
        for w in res:
            print(f"WARN [{w['rule']}] {w['msg']}" + (f" | …{w['match'][:140]}…" if w['match'] else "") + f" ({w['source']})")
        print(f"geo_official_lint: {len(res)} warning(s) (WARN-only, not a gate)")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:  # never block the pipeline
        print(f"geo_official_lint: skipped ({type(e).__name__}: {e})"); sys.exit(0)

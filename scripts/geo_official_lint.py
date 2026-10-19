#!/usr/bin/env python3
"""geo_official_lint.py: WARN-only GEO checks from the official-source rules
(knowledge_base/AEO_GEO_GUIDELINES.md §6, including the 2026-10-09 gap-fill).
Never blocks publishing: always exits 0.
It does not replace or loosen scripts/validate_article.py.

Canonical URL checks (2026-10-19, SEL canonicalization guide) are printed here
as canonical-mismatch, canonical-ambiguous, and canonical-autofix. A mismatch
hard-fails validate_article.py; this script still exits 0. The publisher
applies canonical-autofix before the Shopify request.

Usage: python3 scripts/geo_official_lint.py ARTICLE.(html|md) [--title "..."] [--json]
"""
import json, re, sys, html as _html
from datetime import date

import canonical_urls

G_HELPFUL = "https://developers.google.com/search/docs/fundamentals/creating-helpful-content"
G_GENAI = "https://developers.google.com/search/docs/fundamentals/using-gen-ai-content"
G_AI = "https://developers.google.com/search/docs/fundamentals/ai-optimization-guide"
G_DATES = "https://developers.google.com/search/docs/appearance/publication-dates"
G_SD = "https://developers.google.com/search/docs/appearance/structured-data/sd-policies"
G_MERCHANT = "https://developers.google.com/search/docs/appearance/structured-data/merchant-listing"
G_FEATURES = "https://developers.google.com/search/docs/appearance/ai-features"
G_BACK = "https://developers.google.com/search/blog/2026/04/back-button-hijacking"
O_BOTS = "https://developers.openai.com/api/docs/bots"
O_DEEP = "https://developers.openai.com/api/docs/guides/deep-research"
X_WEB = "https://docs.x.ai/developers/tools/web-search"
A_CRAWL = "https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler"
SEC = "knowledge_base/AEO_GEO_GUIDELINES.md"

RULES = [
    ("back-reference", r"\b(as (mentioned|discussed|noted|explained|stated) (above|earlier|before|previously)|building on the previous section|in the previous section)\b",
     "Section depends on earlier text; make each H2 self-contained (AEO_GEO §1).", SEC + " §1"),
    ("unsupported-superlative", r"\bwellness nest\b[^.]{0,40}\b(is|are)\b[^.]{0,20}\b(the )?(best|leading|#1|number one|no\.? ?1|top-rated|most trusted|best retailer)\b",
     "Superlative about Wellness Nest; keep only if a cited, verifiable source supports it (fact-check all text).", G_GENAI),
    ("unverified-store-claim",
     r"\b(?:visit our (?:store|shop|showroom)|come visit (?:our|the) (?:store|shop)|"
     r"pick[- ]?up (?:your order|in[- ]store|at (?:our|the|wellness nest'?s?) store)|"
     r"(?:in[- ]store|curbside|store) pick[- ]?up|"
     r"same[- ]day (?:delivery|shipping|pickup|dispatch)|"
     r"local warehouse|physical (?:store|storefront|shop)|brick-and-mortar|"
     r"our (?:retail store|showroom)|buy in[- ]store|in[- ]store stock)\b",
     "Physical store / pickup / same-day claim; remove unless Kevin confirmed it's true.", SEC + " §6.5"),
    ("fake-freshness", r"\b(updated (daily|weekly|every day)|freshly updated|newly updated for)\b",
     "Freshness wording; only claim 'updated' when the main content substantially changed.", G_HELPFUL),
    ("invented-credential", r"\b(board[- ]certified|clinically proven|doctor[- ]approved|dietitian[- ]approved|fda[- ]approved)\b",
     "Credential/approval claim; needs a verifiable source (supplements are not FDA-approved).", G_HELPFUL),
]

_LLMS = (
    re.compile(r"\bllms\.txt\b[^.]{0,80}\b(?:is required|are required|will (?:help|boost|improve)|"
               r"improves?(?: your)? rankings?|gets? you (?:cited|ranked)|required for|"
               r"helps? (?:google|chatgpt|claude|grok|ai overviews?))\b", re.I),
    re.compile(r"\b(?:add|publish|include|create|upload|need|needs|must (?:have|add|publish|include))\b"
               r"[^.]{0,50}\bllms\.txt\b[^.]{0,60}\b(?:rank|ranking|cited|ai overview|chatgpt|claude|grok|google)\b", re.I),
)
_BING = re.compile(
    r"\bchatgpt\b[^.]{0,70}\b(?:uses|powered by|based on|indexes|indexed by|comes from|runs on)\b[^.]{0,40}\bbing\b"
    r"|\bbing(?:'s)? index\b[^.]{0,50}\bchatgpt\b", re.I)
_GEXT = (
    re.compile(r"\bgoogle-extended\b[^.]{0,100}\b(?:block|disallow|disable|remove|stop|exclude|prevent)\w*"
               r"\b[^.]{0,60}\b(?:google search|ai overviews?|ai mode|rankings?)\b", re.I),
    re.compile(r"\b(?:block|disallow|disable)\w*\b[^.]{0,50}\bgoogle-extended\b[^.]{0,80}"
               r"\b(?:google search|ai overviews?|ai mode)\b", re.I),
)
_GUESSED_BOT = re.compile(r"\b(?:grok[\s-]?bot|xai[\s-]?bot|x\.ai[\s-]?bot)\b", re.I)
_CLAUDE_VER = re.compile(r"\b(?:claudebot|claude-searchbot|claude-user)/\d+(?:\.\d+)?\b", re.I)
_FAKE_OAI = re.compile(r"\b(?:chatgptbot|openai-searchbot|gpt-searchbot|oai-bot)\b", re.I)
_OAI_MAJOR = re.compile(r"\b(?:OAI-SearchBot|GPTBot)/(\d+)", re.I)
_OAI_EXACT = re.compile(r"\b(?:ChatGPT-User|OAI-AdsBot)/(\d+(?:\.\d+)?)\b", re.I)
_LIVE = re.compile(
    r"\b(?:indexnow|bing webmaster(?: tools)?|(?:google )?search console|\bgsc\b)\b"
    r"[^.]{0,70}\b(?:is|are|was|were)\s+(?:already\s+)?(?:live|verified|connected|active|enabled|set up|receiving)\b",
    re.I)
_WE_LIVE = re.compile(
    r"\b(?:we|wellness nest|this store|wellnessnest\.co)\b[^.]{0,60}"
    r"\b(?:submitted|verified|pinged|enabled|connected)\b[^.]{0,50}"
    r"\b(?:indexnow|bing webmaster|search console)\b", re.I)
_CHUNK = re.compile(
    r"\bchunk(?:ed|ing)?\s+(?:the\s+|this\s+|our\s+)?(?:page|article|content|copy)\s+for\s+(?:the\s+)?(?:ai|llms?|chatgpt|geo)\b"
    r"|\bideal\s+(?:page\s+|article\s+|word\s+)?length\b[^.]{0,50}\b(?:for\s+)?(?:ai|llms?|geo|aeo|chatgpt|ai\s+overviews?)\b",
    re.I)
_BACK = re.compile(r"\bonpopstate\b|\b(?:hijack|trap|block|disable)s?\s+the\s+back\s+button\b", re.I)
_BOTWALL = re.compile(
    r"\b(?:cf-turnstile|g-recaptcha|h-captcha|hcaptcha|data-sitekey)\b"
    r"|\b(?:complete|solve|pass)\s+(?:the\s+|a\s+)?captcha\b|\bcloudflare\s+challenge\b", re.I)
_GENERIC_STEM = re.compile(
    r"^(?:img|image|photo|picture|screenshot|untitled|dscn?|dsc)(?:[_-]?\d+)?$", re.I)
_IMG_EXT = re.compile(r"\.(?:png|jpe?g|webp|gif|avif)$", re.I)
_MONTHS = {}
for _i, _name in enumerate(
        ["january", "february", "march", "april", "may", "june",
         "july", "august", "september", "october", "november", "december"], 1):
    _MONTHS[_name] = _i
    _MONTHS[_name[:3]] = _i
_MONTHS["sept"] = 9

AUTH_DOMAINS = ("pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov", "nih.gov", "ods.od.nih.gov", "fda.gov",
                "cdc.gov", "who.int", "cochrane", "nejm.org", "jamanetwork.com", "bmj.com", "thelancet.com",
                "efsa.europa.eu", "nhs.uk", "doi.org", "regulations.gov", "examine.com",
                "usada.org", "wada-ama.org", "ncaa.org")

def _negated(hay, start, end):
    """Skip a hit that the draft itself is warning against."""
    pre = hay[max(0, start - 80):start]
    hit = hay[start:end]
    post = hay[end:end + 40]
    if re.search(r"\b(do not|don'?t|does not|doesn'?t|never|without|unless)\b", pre, re.I):
        return True
    if re.search(r"\b(no|not|isn'?t|aren'?t)\b\W{0,16}$", pre, re.I):
        return True
    if re.search(r"\b(not|never)\b", hit, re.I):
        return True
    if re.search(r"^\W*(?:is|are)?\W*(?:not|n'?t)\b", post, re.I):
        return True
    return False

def _emit(out, hay, match, rid, msg, src):
    if _negated(hay, match.start(), match.end()):
        return
    ctx = hay[max(0, match.start() - 50):match.end() + 50].strip()
    out.append({"rule": rid, "msg": msg, "match": ctx, "source": src})

def _scan(out, hay, pattern, rid, msg, src):
    for match in pattern.finditer(hay):
        _emit(out, hay, match, rid, msg, src)

def strip_tags(s):
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    return _html.unescape(re.sub(r"(?s)<[^>]+>", " ", s))

def _visible_dates(text, labels):
    found = []
    for label in labels:
        lab = re.escape(label)
        for match in re.finditer(rf"\b{lab}\b\s*:?\s*(\d{{4}}-\d{{2}}-\d{{2}})", text, re.I):
            found.append(match.group(1))
        for match in re.finditer(
                rf"\b{lab}\b\s*:?\s*([A-Za-z]+)\s+(\d{{1,2}}),?\s+(\d{{4}})", text, re.I):
            mon = _MONTHS.get(match.group(1).lower())
            day = int(match.group(2))
            if mon and 1 <= day <= 31:
                found.append(f"{int(match.group(3)):04d}-{mon:02d}-{day:02d}")
    return found

def _json_dates(raw, key):
    return re.findall(rf'"{key}"\s*:\s*"(\d{{4}}-\d{{2}}-\d{{2}})', raw)

def _date_conflict(out, raw, text, key, labels):
    visible = set(_visible_dates(text, labels))
    marked = set(_json_dates(raw, key))
    if visible and marked and visible.isdisjoint(marked):
        out.append({
            "rule": "date-mismatch",
            "msg": f"Visible {labels[0]} {sorted(visible)[0]} does not match {key} {sorted(marked)[0]} (dates must agree).",
            "match": "",
            "source": G_DATES,
        })

def _image_srcs(raw):
    srcs = re.findall(r'(?is)<img\b[^>]*\bsrc\s*=\s*["\']([^"\']+)', raw)
    srcs += re.findall(r'!\[[^\]]*\]\(\s*<?([^)\s>]+)', raw)
    return srcs

def _generic_name(src):
    path = src.split("?", 1)[0].split("#", 1)[0]
    name = path.rstrip("/").rsplit("/", 1)[-1]
    if not _IMG_EXT.search(name) or "." not in name:
        return False
    return bool(_GENERIC_STEM.match(name.rsplit(".", 1)[0]))

def lint(raw, title=""):
    out = []
    text = re.sub(r"\s+", " ", strip_tags(raw))
    hay = (title + " . " + text)
    for rid, pat, msg, src in RULES:
        for match in re.finditer(pat, hay, re.I):
            _emit(out, hay, match, rid, msg, src)
    _scan(out, hay, _LLMS[0], "llms-txt-ranking",
          "Draft claims llms.txt is required or helps rankings. Google ignores it; don't say it helps.",
          G_AI)
    _scan(out, hay, _LLMS[1], "llms-txt-ranking",
          "Draft claims llms.txt is required or helps rankings. Google ignores it; don't say it helps.",
          G_AI)
    _scan(out, hay, _BING, "chatgpt-bing-index",
          "Draft says ChatGPT search uses Bing's index. OpenAI's bots docs do not say that.",
          O_BOTS)
    for pat in _GEXT:
        _scan(out, hay, pat, "google-extended-blocks-search",
              "Draft says blocking Google-Extended removes Google Search or AI Overviews. It does not.",
              G_FEATURES)
    _scan(out, hay, _GUESSED_BOT, "invented-crawler-ua",
          "Guessed xAI crawler token. docs.x.ai publishes no GrokBot / xAI-Bot rule.",
          X_WEB)
    _scan(out, hay, _CLAUDE_VER, "invented-crawler-ua",
          "Invented Claude UA version. Anthropic publishes the bot names, not version strings.",
          A_CRAWL)
    _scan(out, hay, _FAKE_OAI, "invented-crawler-ua",
          "Invented OpenAI crawler name. Use OAI-SearchBot, GPTBot, ChatGPT-User, or OAI-AdsBot.",
          O_BOTS)
    for match in _OAI_MAJOR.finditer(hay):
        if match.group(1) != "1":
            _emit(out, hay, match, "invented-crawler-ua",
                  "OpenAI documents OAI-SearchBot/1.x and GPTBot/1.x, not this version.",
                  O_BOTS)
    for match in _OAI_EXACT.finditer(hay):
        if match.group(1) != "1.0":
            _emit(out, hay, match, "invented-crawler-ua",
                  "OpenAI documents ChatGPT-User/1.0 and OAI-AdsBot/1.0, not this version.",
                  O_BOTS)
    _scan(out, hay, _LIVE, "indexnow-gsc-bing-live",
          "Draft says IndexNow, Search Console, or Bing Webmaster is live. Kevin has not hosted the keys.",
          SEC + " §6.9")
    _scan(out, hay, _WE_LIVE, "indexnow-gsc-bing-live",
          "Draft says IndexNow, Search Console, or Bing Webmaster is live. Kevin has not hosted the keys.",
          SEC + " §6.9")
    _scan(out, hay, _CHUNK, "chunk-for-ai",
          "Draft chunks a page or states an ideal length for AI. Google says not to.",
          G_AI)
    _scan(out, raw, _BACK, "back-button-hijack",
          "Back-button trap. Remove it; Google has treated this as spam since 2026-06-15.",
          G_BACK)
    _scan(out, raw, _BOTWALL, "bot-challenge",
          "Bot challenge or CAPTCHA in the draft. Anthropic's bots will not bypass CAPTCHAs.",
          A_CRAWL)
    imgs = re.findall(r"(?is)<img\b[^>]*>", raw)
    no_alt = [i for i in imgs if not re.search(r'\balt\s*=\s*"[^"]{3,}"', i)]
    no_alt += re.findall(r"!\[\s*\]\([^)]*\)", raw)
    if no_alt:
        out.append({"rule": "image-alt", "msg": f"{len(no_alt)} image(s) without descriptive alt text (fact-check alt text too).",
                    "match": "", "source": G_GENAI})
    generic = [src for src in _image_srcs(raw) if _generic_name(src)]
    if generic:
        out.append({"rule": "generic-image-filename",
                    "msg": f"{len(generic)} image file name(s) are placeholders ({generic[0]}). Use a descriptive name.",
                    "match": generic[0], "source": X_WEB})
    yrs = [int(y) for y in re.findall(r"\b(20[12]\d)\b", title)]
    if yrs and max(yrs) < date.today().year:
        out.append({"rule": "stale-title-year", "msg": f"Title year {max(yrs)} is older than the current year.",
                    "match": title, "source": G_DATES})
    n_art = len(re.findall(r'"@type"\s*:\s*"(?:Article|BlogPosting|NewsArticle)"', raw))
    if n_art > 1:
        out.append({"rule": "duplicate-article-schema", "msg": f"{n_art} Article/BlogPosting nodes; emit one with consistent dates.",
                    "match": "", "source": G_DATES})
    if re.search(r'"aggregateRating"|"reviewCount"|"@type"\s*:\s*"Review"', raw) and not re.search(
            r"\b(reviews?|ratings?|stars?)\b", text, re.I):
        out.append({"rule": "schema-review-not-visible",
                    "msg": "Review or aggregateRating markup with no visible review text. Markup must match the page.",
                    "match": "", "source": G_SD})
    if re.search(r'"priceValidUntil"|"validThrough"', raw) and not re.search(
            r"\b(sale|discount|compare[- ]at)\b", text, re.I):
        out.append({"rule": "sale-window-unmarked",
                    "msg": "priceValidUntil/validThrough is only for an active sale window. Say so in the visible text, or remove it.",
                    "match": "", "source": G_MERCHANT})
    _date_conflict(out, raw, text, "datePublished", ("Published",))
    _date_conflict(out, raw, text, "dateModified", ("Last updated", "Date modified"))
    links = re.findall(r'(?i)(?:href\s*=\s*"|\]\()(https?://[^")\s]+)', raw)
    if not any(any(d in link.lower() for d in AUTH_DOMAINS) for link in links):
        out.append({"rule": "no-primary-source", "msg": "No link to a primary study or regulator (PubMed/NIH/FDA/CDC/WHO, DOI, regulations.gov, Examine, USADA, or WADA). Inference rule for AI-search citability.",
                    "match": "", "source": O_DEEP})
    out.extend(canonical_urls.lint_warnings(raw))
    return out

def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__); return 0
    title = ""
    if "--title" in argv:
        title = argv[argv.index("--title") + 1]
    with open(argv[1], encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    if not title:
        m = re.search(r"(?is)<title>(.*?)</title>|<h1[^>]*>(.*?)</h1>", raw)
        if not m:
            m = re.search(r"^#\s+(.+)$", raw, re.M)
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

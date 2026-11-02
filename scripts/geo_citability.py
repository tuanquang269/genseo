#!/usr/bin/env python3
"""Citability checks the article gate can enforce without touching the theme.

Used by validate_article.py. Pure checks take HTML (markdown drafts are converted
first). Link status is injected so tests never hit the network; fetch_status()
is the live curl helper.
"""
import html as htmlmod
import re
import subprocess

import geo_official_lint

# Hosts that count as a citable study or regulator. geo_official_lint.AUTH_DOMAINS
# is the shared list (PubMed/NIH/FDA/CDC/WHO/DOI plus the 2026-10-17 additions).
PRIMARY_SOURCE_DOMAINS = geo_official_lint.AUTH_DOMAINS

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
_STATUS_CACHE = {}

_SKIP_HOST_SUFFIX = (
    "wellnessnest.co", "shopify.com", "shopifycdn.com", "schema.org", "w3.org",
    "googleapis.com", "gstatic.com", "google.com",
    "facebook.com", "fb.com", "twitter.com", "x.com", "t.co", "pinterest.com",
    "instagram.com", "linkedin.com", "tiktok.com", "youtube.com", "youtu.be",
    "reddit.com", "whatsapp.com", "wa.me",
)
_INTERNAL = re.compile(
    r"https://wellnessnest\.co/(?:"
    r"products/[a-z0-9-]+|collections/[a-z0-9-]+|pages/[a-z0-9-]+|policies/[a-z0-9-]+|"
    r"blogs/[a-z0-9-]+(?:/[a-z0-9-]+)?)",
    re.I,
)
_HREF = re.compile(r"""(?i)(?:href\s*=\s*["']|\]\()(https?://[^"'\)\s>]+)""")
_QSTART = re.compile(
    r"^(what|how|why|when|where|which|who|does|do|did|is|are|can|should|will|could|would)\b",
    re.I,
)
_THROAT = re.compile(
    r"^(in this (article|guide|post|review)|welcome to|let'?s dive|"
    r"are you wondering|if you(?:'ve| have) ever wondered|"
    r"this (article|guide|post) (will|covers|explains))\b",
    re.I,
)
_META = re.compile(r"(?is)<!--\s*meta_description:\s*(.*?)\s*-->")
_PUBLISHED_LINE = re.compile(
    r"(?im)(?:^|>)\s*Published:\s*"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},\s+\d{4}"
)
_NEG = re.compile(
    r"\b(not|no|never|don'?t|do not|does not|cannot|can't|isn't|won't|without|"
    r"neither|nor|"
    r"medical promise|structure/function|do not claim)\b",
    re.I,
)
# Describing a cure claim is not making one. "We promise to cure an infection"
# does not match this and still fails.
_CLAIM_CAUTION = re.compile(
    r"\bbe cautious with claims\b|\bclaims that promise to cure\b",
    re.I,
)
_DISEASE = re.compile(
    r"\b(cures?|cured|treats?|treated|prevents?|prevented|reverses?|reversed)\b"
    r".{0,60}\b(cancer|diabetes|alzheimer'?s?|dementia|covid-19|covid|"
    r"an infection|the infection|infertility|bacterial vaginosis|\bbv\b|\buti\b|"
    r"depression|heart disease|obesity|erectile dysfunction)\b",
    re.I,
)
_FDA = re.compile(r"\b(is|are|was|were)\s+fda[-\s]?approved\b", re.I)
_CLINICAL = re.compile(r"\bclinically proven\b", re.I)
_GUARANTEE = re.compile(r"\bguaranteed?\b.{0,40}\b(results?|cure|weight loss)\b", re.I)
_GENERIC_ALT = re.compile(r"(image|photo|img|picture|hero|banner|thumbnail|placeholder)", re.I)


def _plain(raw):
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw or "")
    text = re.sub(r"(?s)<!--.*?-->", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", htmlmod.unescape(text)).strip()


def _sentences(raw):
    text = _plain(raw)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"“])", text)
    return [p.strip() for p in parts if p.strip()]


def opening_paragraph(html):
    """First real paragraph (>=20 visible words), skipping spacer/hidden paragraphs."""
    for match in re.finditer(r"<p[^>]*>(.*?)</p>", html or "", re.S | re.I):
        block = match.group(0)
        if "display:none" in block.lower() or "spacer" in block.lower():
            continue
        text = re.sub(r"(?s)<!--.*?-->", "", match.group(1))
        text = re.sub(r"(?s)<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", htmlmod.unescape(text)).strip()
        if len(text.split()) >= 20:
            return text
    return ""


def _host(url):
    match = re.match(r"https?://([^/]+)", url, re.I)
    if not match:
        return ""
    return match.group(1).lower().split(":")[0]


def _skipped_host(host):
    return any(host == suffix or host.endswith("." + suffix) for suffix in _SKIP_HOST_SUFFIX)


def hrefs(html):
    found = []
    for match in _HREF.finditer(html or ""):
        url = htmlmod.unescape(match.group(1)).split("#", 1)[0].strip()
        if url.startswith("http"):
            found.append(url)
    return found


def is_primary_source(url):
    low = (url or "").lower()
    return any(domain in low for domain in PRIMARY_SOURCE_DOMAINS)


def external_urls(html):
    """Outbound http(s) links a citation check should resolve. Order-stable, de-duplicated."""
    seen = []
    for url in hrefs(html):
        host = _host(url)
        if not host or _skipped_host(host):
            continue
        if url not in seen:
            seen.append(url)
    return seen[:30]


def internal_urls(html):
    """Absolute wellnessnest product, collection, page, policy, and article URLs."""
    seen = []
    for match in _INTERNAL.finditer(html or ""):
        url = match.group(0)
        if url not in seen:
            seen.append(url)
    return seen


def _h2_texts(html):
    texts = []
    for match in re.finditer(r"<h2[^>]*>(.*?)</h2>", html or "", re.I | re.S):
        text = _plain(match.group(1))
        if text:
            texts.append(text)
    return texts


def _question_heading(text):
    stripped = text.strip()
    return stripped.endswith("?") or bool(_QSTART.match(stripped))


def _faq_questions(html):
    questions = re.findall(r"<p[^>]*>\s*<strong>([^<]*\?)\s*</strong>", html or "", re.I)
    questions += re.findall(r"<h3[^>]*>([^<]*\?)\s*</h3>", html or "", re.I | re.S)
    return [re.sub(r"\s+", " ", q).strip() for q in questions]


def _image_tags(html):
    tags = []
    for tag in re.findall(r"<img\b[^>]*>", html or "", re.I):
        if "display:none" in tag.lower() or "spacer" in tag.lower():
            continue
        tags.append(tag)
    return tags


def _alt_text(tag):
    match = re.search(r'\balt\s*=\s*(["\'])(.*?)\1', tag, re.I | re.S)
    if not match:
        return None
    return htmlmod.unescape(match.group(2)).strip()


def compliance_issues(html):
    """Affirmative disease-cure, FDA-approval, or clinically-proven claims.

    A sentence that negates the claim (including neither/nor), asks it as a
    question, labels it a medical promise, or warns about claims that promise
    to cure is the copy we want. It is not a failure.
    """
    fails = []
    for sentence in _sentences(html):
        if "?" in sentence or _NEG.search(sentence) or _CLAIM_CAUTION.search(sentence):
            continue
        disease = _DISEASE.search(sentence)
        if disease:
            fails.append("disease-cure claim: " + sentence[:160])
            continue
        if _FDA.search(sentence):
            fails.append("FDA-approval claim: " + sentence[:160])
        elif _CLINICAL.search(sentence):
            fails.append("clinically proven claim: " + sentence[:160])
        elif _GUARANTEE.search(sentence):
            fails.append("guaranteed-result claim: " + sentence[:160])
    return fails[:6]


def citation_issues(results):
    """Split resolved link results into hard failures and inconclusive warnings.

    results: iterable of (url, http_status, redirect_loop).
    404/410, a redirect loop, and a hard 5xx fail the draft.
    401/403/408/429/503 and a timeout (status 0) are warnings: academic hosts
    often answer 403 to a datacenter, which is not proof the citation is dead.
    2xx and 3xx, including PubMed 203, pass.
    """
    fails = []
    warns = []
    for url, status, loop in results:
        if loop:
            fails.append(f"citation redirect loop: {url}")
            continue
        try:
            code = int(status)
        except (TypeError, ValueError):
            code = 0
        if code in (404, 410) or (500 <= code <= 599 and code != 503):
            fails.append(f"citation HTTP {code}: {url}")
        elif code == 0 or code in (401, 403, 408, 429, 430, 503) or code >= 400:
            warns.append(
                f"citation check inconclusive HTTP {code}: {url} "
                "(403/429/503 and timeouts are not treated as dead)"
            )
    return fails[:8], warns[:8]


def fetch_status(url, timeout=12):
    """Return (http_status, redirect_loop) for one URL. Cached per process.

    HEAD first. GET when HEAD is missing, blocked, or a 4xx/5xx, because some
    hosts 404 a HEAD that a browser GET would open.
    """
    if url in _STATUS_CACHE:
        return _STATUS_CACHE[url]

    def once(head):
        cmd = [
            "curl", "-sS", "-L", "--max-redirs", "6", "-A", _UA,
            "-o", "/dev/null", "-w", "%{http_code}",
            "--connect-timeout", "8", "--max-time", str(timeout),
        ]
        if head:
            cmd.append("-I")
        cmd.append(url)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        except (subprocess.TimeoutExpired, OSError):
            return 0, False
        loop = res.returncode == 47
        raw = (res.stdout or "").strip()
        try:
            code = int(raw)
        except ValueError:
            code = 0
        return code, loop

    status, loop = once(True)
    if loop or status in (0, 400, 401, 403, 404, 405, 408, 410, 429, 500, 501, 502, 503):
        got, got_loop = once(False)
        loop = loop or got_loop
        if got:
            status = got
    _STATUS_CACHE[url] = (status, loop)
    return status, loop


def assess(html, require_meta=False):
    """Return (fails, warns) for citability rules the draft itself can satisfy."""
    html = html or ""
    fails = []
    warns = []

    opening = opening_paragraph(html)
    if opening:
        words = len(opening.split())
        if words < 30:
            fails.append(f"answer block {words} words (need at least 30; target 40–60)")
        elif not (40 <= words <= 70):
            warns.append(f"answer block {words} words (target 40–60)")
        if _THROAT.match(opening):
            fails.append("answer block is throat-clearing; state the answer in the first sentence")
    # A missing opening paragraph is already a hard fail in validate_article.py.

    if _PUBLISHED_LINE.search(html):
        fails.append(
            "hand-written Published: date — the theme already prints the date, and a body "
            "date has disagreed with that header by one day (US Pacific vs UTC)"
        )

    headings = _h2_texts(html)
    questions = [h for h in headings if _question_heading(h)
                 and not re.search(r"\b(faq|frequently asked questions)\b", h, re.I)]
    if len(questions) < 2:
        fails.append(
            f"need ≥2 question-style H2s (What/How/Does… or a heading that ends in ?), found {len(questions)}"
        )
    if not any(re.search(r"\b(faq|frequently asked questions)\b", h, re.I) for h in headings):
        fails.append("no FAQ heading (## Frequently Asked Questions)")
    faq_n = len(_faq_questions(html))
    if faq_n < 3:
        fails.append(f"only {faq_n} visible FAQ questions (need ≥3)")

    urls = hrefs(html)
    if not any(re.search(r"wellnessnest\.co/products/[a-z0-9-]+", u, re.I) for u in urls):
        fails.append("no https://wellnessnest.co/products/<handle> link")
    if not any(re.search(r"wellnessnest\.co/blogs/news/[a-z0-9-]+", u, re.I) for u in urls):
        fails.append("no related https://wellnessnest.co/blogs/news/<handle> article link")
    if not any(is_primary_source(u) for u in urls):
        fails.append(
            "no primary-source link (PubMed, NIH, FDA, CDC, WHO, DOI, regulations.gov, "
            "Examine, USADA, or WADA)"
        )

    weak_alt = 0
    for tag in _image_tags(html):
        alt = _alt_text(tag)
        if alt is None or len(alt) < 8 or _GENERIC_ALT.fullmatch(alt):
            weak_alt += 1
    if weak_alt:
        fails.append(f"{weak_alt} image(s) missing a descriptive alt (at least a short phrase)")

    if require_meta:
        match = _META.search(html)
        if not match:
            fails.append("missing <!-- meta_description: ... --> (120–165 characters)")
        else:
            desc = re.sub(r"\s+", " ", htmlmod.unescape(match.group(1))).strip()
            if not (120 <= len(desc) <= 165):
                fails.append(f"meta description {len(desc)} characters (need 120–165)")

    fails.extend(compliance_issues(html))
    return fails, warns

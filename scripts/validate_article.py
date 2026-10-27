#!/usr/bin/env python3
"""
validate_article.py — Mechanical quality gate for GenSeo articles.
Runs the SELF-AUDIT checklist as code so a cheap model CANNOT publish thin content
by mistake. The publisher skill calls this FIRST; non-zero exit = do not publish.

Usage: python3 validate_article.py <article.html|article.md> [--draft]
Exit 0 = PASS (publish allowed). Exit 1 = FAIL (prints what's missing).
Exit 3 = WARN/UNVERIFIED. The dead-link check still saw HTTP 429 after retries.
         Publish stays blocked until those links get a real response.
Also verifies that every linked product/collection/author URL is live.
"""
import sys, os, re, glob, json, subprocess, tempfile, time, datetime, email.utils, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genseo_roster
import brand_rules as _br
import geo_citability

# Single source of truth: roster.json (see scripts/genseo_roster.py). Empty roster
# blocks publishing by design — fill roster.json with real, consenting people.
ROSTER_PAGES=genseo_roster.PAGES
APPROVED_BIOS=genseo_roster.BIOS
FAKE_AUTHORS=("Author One","Author Two","Author Three","Author Four",
              "Author Five","Author Six","Author Seven")
              # Donor package's sanitized placeholder bylines — a model must never
              # resurrect them. Add any byline you ever have to remove.
# US-market anchor: the answer block must place the reader geographically the way the
# donor system anchored on its market. Case-sensitive so the pronoun "us" can't pass.
MARKET_RE=re.compile(r'\bU\.?S\.?A?\.?\b|\bUnited States\b|\bAmericans?\b')
# Draft mode converts `### About the Author` to `<h3>…</h3>` before the checks run, so the bio
# must be found in BOTH forms — a markdown-only pattern silently passes every real draft.
BIO_RE=re.compile(r'(?is)(?:#{2,3}\s*|<h[23][^>]*>\s*)About the Author\s*(?:</h[23]>)?\s*(.{0,600})')
MIN_INLINE_IMAGES=3   # every review/product article must have >=3 in-body images (1 per product; hero excluded)


def _strip_approved(text):
    """Drop roster-approved bios and names before the invented-credential scan.
    Kevin's call 2026-08-07: the approved byline itself may carry a title
    ("Dr. Marcus Hale"), so the gate polices only what a model ADDS beyond the
    vetted roster entry — strip bios first, then names (bios contain the name)."""
    for b in APPROVED_BIOS: text = text.replace(b, "")
    for n in genseo_roster.NAMES.values(): text = text.replace(n, "")
    return text

# ---------------------------------------------------------------------------
# QRG content-quality gate (added 2026-07-30)
#
# The checks above are all STRUCTURAL: they prove an article has a table, a
# price, links, images. Nothing measured whether the prose was any good, which
# is exactly what the May 2026 core update punished us for. These thresholds
# close that gap using the claude-seo scorers, which key off Google's Sept 2025
# Quality Rater Guidelines (§4.6.5 scaled content abuse, §4.6.6, §4.6 filler).
#
# Thresholds are DERIVED, not guessed: all 534 drafts in published_drafts/ were
# scored on 2026-07-30 and the cut lines sit just past the p90 tail.
#   overall  min=66  p10=83  p50=93  p90=98
#   filler   p50=0   p90=18  max=75
#   ai       p50=0   p90=15  max=45
#   repetition p50=10 p90=13 max=30      density p10=0.609
# Combined FAIL rule flags 53/534 = 9.9% of historical drafts.
#
# Escape hatch: GENSEO_QRG_ADVISORY=1 downgrades these to warnings.
# A missing scorer is NOT that hatch. It prints "QRG scoring unavailable: …"
# and stays a warning. Thresholds apply only to measured scores. The
# auto-publish skill (STEP 6) hard-fails low scores; it does not hold a
# draft whose scorer never ran. Do not invent a score and do not call a
# paid API to replace the launcher.
QRG_MIN_OVERALL=80
QRG_MAX_FILLER=25
QRG_MAX_AI=25
QRG_WARN_REPETITION=20
QRG_WARN_DENSITY=0.55
QRG_LAUNCHER_GLOB="~/.claude/plugins/marketplaces/*claude-seo*/bin/claude-seo"

def _claude_seo_bin():
    """Locate the claude-seo launcher. Glob so a marketplace rename can't break us."""
    for p in glob.glob(os.path.expanduser(QRG_LAUNCHER_GLOB)):
        if os.access(p, os.X_OK):
            return p
    return None

def _claude_seo_env():
    """The Antigravity cron runs outside Claude Code, so it does not inherit the
    CLAUDE_SEO_* vars from ~/.claude/settings.json. Pin them here or the launcher
    falls back to Homebrew python 3.14, whose broken pyexpat makes the runtime
    unusable (see wiki/tools/homebrew-python314-pyexpat-broken-venv.md)."""
    env=os.environ.copy()
    if not env.get("CLAUDE_SEO_PYTHON"):
        cands=sorted(glob.glob(os.path.expanduser(
            "~/.local/share/uv/python/cpython-3.1[2-9]*/bin/python3.1[2-9]")))
        if cands:
            env["CLAUDE_SEO_PYTHON"]=cands[-1]
    env.setdefault("CLAUDE_SEO_DATA_DIR",
                   os.path.expanduser("~/Library/Application Support/claude-seo"))
    env.pop("CLAUDE_PLUGIN_DATA", None)   # leaks in from whichever plugin ran last
    return env

def _qrg_flat(note):
    """One log field: no tabs or newlines."""
    return " ".join(str(note).split())


def qrg_log_column(qrg, note):
    """validate_runs.log column. A skip names the reason; it is not a bare qrg=skip."""
    if note:
        return "qrg=skip:" + _qrg_flat(note)[:160]
    q=qrg["quality"]
    return "qrg=%s/%s/%s" % (q["overall_quality"], q["filler_score"], q["ai_pattern_score"])


def qrg_report(qrg, note):
    """Return (hard_fails, warnings, line).

    A non-empty note means the claude-seo scorer did not return usable scores.
    That is a warning. The draft is not held. Measured scores still hard-fail
    the thresholds above unless GENSEO_QRG_ADVISORY=1.
    """
    if note:
        flat=_qrg_flat(note)
        return [], ["QRG quality scoring skipped (%s)" % note], "QRG scoring unavailable: %s" % flat
    try:
        q,v=qrg["quality"],qrg["verify"]
        overall=q["overall_quality"]
        filler=q["filler_score"]
        ai=q["ai_pattern_score"]
        rep=q["repetition_score"]
        density=q["information_density"]
        matches=q["matches"]
        claims=v["claim_count"]
        uncited=v["uncited_count"]
        ratio=v["uncited_ratio"]
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        flat="scorer JSON unusable (%s)" % _qrg_flat(exc)
        return [], ["QRG quality scoring skipped (%s)" % flat], "QRG scoring unavailable: %s" % flat
    advisory=os.environ.get("GENSEO_QRG_ADVISORY")=="1"
    hard=[]
    warns=[]
    hits=lambda lst: ", ".join(lst[:6]) if lst else "none"
    line=(f"QRG: overall {overall}/100 "
          f"filler {filler} ai {ai} "
          f"repetition {rep} density {density} "
          f"| claims {claims} uncited {uncited}")
    sink=warns if advisory else hard
    if overall < QRG_MIN_OVERALL:
        sink.append(f"QRG overall quality {overall}/100 below {QRG_MIN_OVERALL} "
                    f"(scaled-content-abuse risk; p10 of our own corpus is 83)")
    if filler >= QRG_MAX_FILLER:
        sink.append(f"filler score {filler} >= {QRG_MAX_FILLER} — remove: "
                    f"{hits(matches.get('filler') or [])}")
    if ai >= QRG_MAX_AI:
        sink.append(f"AI-pattern score {ai} >= {QRG_MAX_AI} — rewrite: "
                    f"{hits(matches.get('ai_patterns') or [])}")
    if rep >= QRG_WARN_REPETITION:
        warns.append(f"repetition {rep} (p90 of corpus is 13) — likely restating the same point")
    if density < QRG_WARN_DENSITY:
        warns.append(f"information density {density} < {QRG_WARN_DENSITY} — padded prose")
    if claims >= 3 and ratio >= 1.0:
        warns.append(f"{claims} factual claims, none cited — add a source or drop the numbers")
    return hard, warns, line


def qrg_scores(plain_text):
    """Score prose quality + citation gaps. Returns (scores_dict, note) where a
    non-empty note means scoring was skipped and nothing should be enforced."""
    binary=_claude_seo_bin()
    if not binary:
        return None, "claude-seo runtime not installed (%s)" % QRG_LAUNCHER_GLOB
    env=_claude_seo_env()
    tmp=None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(plain_text); tmp=fh.name
        out={}
        # content_verify exits 1 when uncited_ratio > its own --threshold (default 0.4).
        # We do our own thresholding below, so neutralise its gate with --threshold 1
        # and treat any non-zero exit as a genuine failure.
        for script,key,extra in (("content_quality.py","quality",[]),
                                 ("content_verify.py","verify",["--threshold","1"])):
            res=subprocess.run([binary,"run",script,tmp,"--json",*extra],
                               capture_output=True, text=True, timeout=120, env=env)
            if res.returncode!=0:
                return None, f"{script} exited {res.returncode}: {res.stderr.strip()[:120]}"
            out[key]=json.loads(res.stdout)
        return out, ""
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    finally:
        if tmp:
            try: os.unlink(tmp)
            except OSError: pass

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# Dead-link outcomes. HTTP 429 is indeterminate: Shopify is rate-limiting, so a
# dead internal URL can wear the same status as a live one.
OK="ok"
DEAD="dead"
UNVERIFIED="unverified"
# Same convention as fetch_personas: exit 3 means the check did not finish.
# Exit 0 is the only publishable result. The headless prompt requires exit 0.
EXIT_UNVERIFIED=3
LINK_TRIES=3
# A Retry-After of hours must not stall the daily gate. Typical Shopify
# buckets ask for a second or two, which sit under this cap.
RETRY_AFTER_CAP=8.0
LINK_TIMEOUT=15

class _KeepStatus(urllib.request.HTTPErrorProcessor):
    """Hand the status back to the dead-link check, including 3xx, 4xx, and 429.

    The default processor turns 3xx into a followed redirect and 4xx into an
    exception. This check decides what each code means. A 301 stays a 301.
    """
    def http_response(self, request, response):
        return response
    https_response=http_response

def _status_code(code):
    if isinstance(code, bool) or code is None:
        return 0
    try:
        return int(code)
    except (TypeError, ValueError):
        try:
            return int(str(code).strip() or "0")
        except (TypeError, ValueError):
            return 0

def _retry_after_seconds(value, now=None):
    """Retry-After as delay-seconds, or as seconds until an HTTP-date.

    Unusable values (blank, negative, not a date) return None so the caller
    keeps its own backoff.
    """
    if value is None:
        return None
    text=str(value).strip()
    if not text:
        return None
    try:
        delay=float(text)
    except ValueError:
        delay=None
    if delay is not None:
        if delay<0:
            return None
        return delay
    try:
        parsed=email.utils.parsedate_to_datetime(text)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed=parsed.replace(tzinfo=datetime.timezone.utc)
    if now is None:
        now=datetime.datetime.now(datetime.timezone.utc)
    return (parsed-now).total_seconds()

def _wait_seconds(attempt, retry_after, now=None):
    """Seconds to sleep before the next try.

    A positive Retry-After is the wait (then capped). A missing, zero, or
    negative header keeps the previous backoff: 1.5s, then 3s.
    """
    fallback=1.5*(attempt+1)
    honored=_retry_after_seconds(retry_after, now=now)
    if honored is None or honored<=0:
        delay=fallback
    else:
        delay=honored
    if delay<0:
        delay=0.0
    return min(float(delay), RETRY_AFTER_CAP)

def fetch_link(url, timeout=LINK_TIMEOUT):
    """GET one URL. Return (status, Retry-After or None).

    Browser UA: Shopify throttles bare clients and that used to mark live
    pages dead (2026-08-09). Network errors return (0, None).
    """
    req=urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    opener=urllib.request.build_opener(_KeepStatus)
    try:
        with opener.open(req, timeout=timeout) as resp:
            headers=getattr(resp, "headers", None)
            retry=headers.get("Retry-After") if headers is not None else None
            return _status_code(getattr(resp, "status", 0)), retry
    except Exception:
        return 0, None

def check_link(url, fetch=None, sleep=None, tries=LINK_TRIES):
    """Return OK, DEAD, or UNVERIFIED.

    2xx and 301/302/307/308 are live. 404 and 410 are dead on the first answer.
    HTTP 429 retries up to `tries` times. The wait honors Retry-After when the
    header is a positive delay, and falls back to the backoff otherwise.
    Still 429 is UNVERIFIED. 430 and 503 stay non-dead after that budget
    (transient responses this gate already refused to call dead). Any other
    code left at the end is dead.
    """
    fetch=fetch or fetch_link
    sleep=sleep or time.sleep
    code=0
    for attempt in range(tries):
        retry_after=None
        try:
            code, retry_after=fetch(url)
        except Exception:
            code, retry_after=0, None
        code=_status_code(code)
        if 200<=code<300 or code in (301, 302, 307, 308):
            return OK
        if code in (404, 410):
            return DEAD
        if attempt<tries-1:
            header=retry_after if code==429 else None
            sleep(_wait_seconds(attempt, header))
    if code==429:
        return UNVERIFIED
    if code in (430, 503):
        return OK
    return DEAD

def unverified_link_warning(url):
    short=url.replace("https://wellnessnest.co", "") or url
    return ("WARN/UNVERIFIED link HTTP 429 after %d tries: %s "
            "(Shopify rate limit; the link was not confirmed live)"
            % (LINK_TRIES, short))

def assess_internal_links(urls, check=None):
    """Split internal URLs into dead fails and 429 warnings.

    Returns (fail_messages, warn_messages, link_exit). link_exit is 1 when a
    link is dead, 3 when the only problem is a rate limit, else 0.
    """
    check=check or check_link
    dead=[]
    unverified=[]
    for u in urls:
        outcome=check(u)
        if outcome==DEAD:
            dead.append(u)
        elif outcome==UNVERIFIED:
            unverified.append(u)
        elif outcome!=OK:
            dead.append(u)
    fails=[]
    warns=[]
    if dead:
        fails.append("dead/404 links: "+", ".join(
            d.replace("https://wellnessnest.co", "") for d in dead[:6]))
    for u in unverified[:6]:
        warns.append(unverified_link_warning(u))
    if dead:
        link_exit=1
    elif unverified:
        link_exit=EXIT_UNVERIFIED
    else:
        link_exit=0
    return fails, warns, link_exit

def final_exit(fails, link_exit):
    """Hard failures exit 1. A 429-only dead-link check exits 3."""
    if fails or link_exit==1:
        return 1
    if link_exit==EXIT_UNVERIFIED:
        return EXIT_UNVERIFIED
    return 0

def result_line(exit_code):
    if exit_code==EXIT_UNVERIFIED:
        return ("RESULT: ✗ WARN/UNVERIFIED — dead-link check still got HTTP 429 "
                "after %d tries. Publish stays blocked until wellnessnest.co "
                "answers those links." % LINK_TRIES)
    if exit_code!=0:
        return "RESULT: ✗ DO NOT PUBLISH — fix the above and re-validate."
    return "RESULT: ✓ PASS — safe to publish."

def test_author_gate():
    """python3 scripts/validate_article.py --self-check-author"""
    if not genseo_roster.ROSTER:
        print("✗ roster.json is EMPTY — fill /Users/kevinkreative/genseo/roster.json with real people")
        print("  (see scripts/genseo_roster.py for the format). Publishing is blocked until then.")
        sys.exit(1)
    handle, entry = next(iter(genseo_roster.ROSTER.items()))
    name, bio = entry["name"], entry["bio"]
    good=(f"## Frequently Asked Questions\n### Q?\nA.\n\n### About the Author\n"
          f"[{name}](/pages/{handle}) — {bio} "
          f"{name} contributes product comparisons and supplement buying guidance for US readers.")
    assert not _author_fails(good), _author_fails(good)
    assert _author_fails(good.replace(bio, f"{name} is a Strength Coach with over 8 years of experience."))
    assert _author_fails(good.replace(f"{name}](/pages/{handle}", "Author Four](/pages/author-four"))
    # the real --draft path sees HTML headings, not markdown ones
    as_html=good.replace("### About the Author", "<h3>About the Author</h3>")
    assert not _author_fails(as_html), _author_fails(as_html)
    assert _author_fails(as_html.replace(bio, f"{name} is a Strength Coach & Fitness Specialist."))
    print(f"author gate self-check OK — roster has {len(genseo_roster.ROSTER)} author(s), "
          "invented credential and resurrected placeholder byline both fail")


def _author_fails(md):
    """The author-gate rules only, so the self-check does not need a whole valid article."""
    fails=[]
    for name in FAKE_AUTHORS:
        if re.search(rf"\b{re.escape(name)}\b", md): fails.append(f"fabricated byline: {name}")
    bio=BIO_RE.search(md)
    if bio:
        bio=bio.group(1)
        cred=re.search(r'(?i)\b(Dr\.|\bMD\b|PhD|\bRD\b|Registered Dietitian|CISSN|Certified [A-Z]|'
                       r'\d+\+?\s*years of experience|Strength Coach|Endocrinolog|Naturopath|Physician)', _strip_approved(bio))
        if cred: fails.append(f"invented credential: {cred.group(1)}")
        if not any(s[:60].lower() in bio.lower() for s in APPROVED_BIOS):
            fails.append("bio not approved sentence")
    return fails


def main():
    if "--self-check-author" in sys.argv:
        test_author_gate(); return 0
    path=sys.argv[1]
    # --draft mode: validating the .md draft BEFORE publish (FAQ schema is added by the
    # publisher post-conversion, so don't hard-fail on schema; warn instead).
    draft_mode="--draft" in sys.argv
    raw=open(path, encoding="utf-8", errors="ignore").read()
    # If validating a markdown draft, convert headings/links to HTML-equivalent so the
    # structural checks work the same way they will after the publisher's md->html step.
    if draft_mode and path.endswith(".md"):
        html=raw
        html=re.sub(r'^###\s+(.*)$', r'<h3>\1</h3>', html, flags=re.M)
        html=re.sub(r'^##\s+(.*)$',  r'<h2>\1</h2>', html, flags=re.M)
        html=re.sub(r'^#\s+(.*)$',   r'<h1>\1</h1>', html, flags=re.M)
        html=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', html)
        html=re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img alt="\1" src="\2">', html)
        # markdown tables -> mark presence
        if re.search(r'^\|.*\|\s*$', html, flags=re.M) and re.search(r'^\|[-: |]+\|\s*$', html, flags=re.M):
            html+="\n<table><th>markdown-table</th></table>"
        # first PLAIN-TEXT paragraph as answer block — skip any line already starting
        # with a tag or comment (the skill's mandatory line-2 `<!-- meta_description -->`
        # otherwise becomes the "first paragraph" and every correct draft fails)
        html=re.sub(r'^(?!<|\s*$)(.+)$', r'<p>\1</p>', html, count=1, flags=re.M)
    else:
        html=raw
    text=re.sub(r'<script[^>]*>.*?</script>','',html,flags=re.S)  # exclude schema from word count
    words=len(re.sub(r'<[^>]*>',' ',text).split())
    fails=[]; warns=[]

    # word count: hard floor catches thin content; long pillar/comparison/refresh content is
    # legitimate (skill allows 1500–2500+), so only WARN above 2800 to flag possible padding.
    if words<900: fails.append(f"word count {words} below 900 (too thin)")
    elif words>2800: warns.append(f"word count {words} >2800 — confirm it's depth, not padding")
    # H1: Shopify renders the ARTICLE TITLE as the page H1, so body_html should NOT
    # contain its own <h1> (that would create a duplicate H1). Title keyword/US
    # is enforced at the title level, not here. Just flag accidental in-body <h1>.
    h1s=re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.S|re.I)
    if len(h1s)>1: fails.append(f"{len(h1s)} <h1> in body — Shopify already renders the title as H1; remove in-body H1s")
    # TITLE CTR check (draft mode only — the `# ` line IS the title that earns the SERP click)
    if draft_mode and h1s:
        t=re.sub(r'<[^>]*>','',h1s[0]).strip()
        # The theme appends " – Wellness Nest" (~16). An H1 over 50 makes a title
        # tag over ~66, which is the band that truncated on the 2026-10-17 audit.
        if len(t)>50: warns.append(
            f"title {len(t)} chars (>50). The theme appends ' – Wellness Nest' (~16), "
            f"so the title tag truncates past ~70: {t[:60]}…")
        if re.match(r'(?i)^(the ultimate guide to|complete guide to|the complete guide to)\b', t) \
           or re.search(r'(?i)(complete|ultimate).{0,20}(review|guide).{0,15}(&|and).{0,15}(guide|sourcing)', t):
            warns.append(f"title uses generic boilerplate (low CTR) — add a number/benefit/hook: {t[:60]}")
        # TOPIC FITNESS backstop (data-derived 2026-07-22): stop the dead-content patterns that our
        # own GSC proves earn ~0 SG clicks. Hard-fail flavour/recipe variants, collection-owned head
        # terms, and sub-demand topics. Only WARN on near-duplicate — a legitimate REFRESH matches
        # its own title; hard dup-prevention lives in ticket-gen + SKILL STEP 0.5.
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import topic_fitness as tf
            tv, tcode, twhy = tf.assess(t,
                articles=tf._load(f"{tf.ROOT}/existing_articles.json", []),
                collections=tf._load(f"{tf.ROOT}/existing_collections.json", []))
            if tv == 'FAIL' and tcode in ('flavour', 'headterm', 'demand'):
                fails.append(f"topic fitness — {twhy}")
            elif tv != 'PASS':
                warns.append(f"topic fitness ({tcode}) — {twhy}")
        except Exception as e:
            warns.append(f"topic_fitness check skipped ({e})")
    # answer block: the first REAL paragraph (skip publisher-injected spacer/comment/hidden
    # paragraphs, e.g. <p><img style="display:none" alt="spacer"><!-- meta_description --></p>).
    # A "real" paragraph has >=20 words of visible text after stripping tags+comments.
    answer=geo_citability.opening_paragraph(html)
    if answer:
        if not MARKET_RE.search(answer): fails.append("answer block missing US-market anchor (US / United States / American)")
    else:
        fails.append("no opening <p> answer block (>=20 words)")
    # h2 count + locality
    h2s=re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.S|re.I)
    if len(h2s)<3: fails.append(f"need ≥3 <h2>, found {len(h2s)}")
    loc_h2=sum(1 for h in h2s if MARKET_RE.search(re.sub(r'<[^>]*>','',h)))
    if loc_h2<1: warns.append("no <h2> contains a US-market anchor")
    # table
    if '<table' not in html: fails.append("no comparison <table>")
    # USD price presence (donor's $check was dead code; the working check is $-digits)
    if not re.search(r'\$\s?\d', html): fails.append("no USD price range (e.g. $25–$40)")
    # collection links >=2
    colls=re.findall(r'https://wellnessnest\.co(/collections/[a-z0-9-]+)', html)
    if len(colls)<2: fails.append(f"need ≥2 /collections/ links, found {len(colls)}")
    # FAQ + FAQPage schema (in draft mode, schema is added post-conversion -> warn only)
    if 'FAQPage' not in html:
        (warns if draft_mode else fails).append("no FAQPage schema (publisher must append it after md->html)")
    # FAQ count, question-style H2s, product/related/primary links, alt text,
    # meta length, hand-written dates, and disease claims: geo_citability.assess.
    # author: named staff member + live page
    author_pages=set(re.findall(r'(/pages/[a-z-]+)', html))
    if not ROSTER_PAGES:
        fails.append("author roster EMPTY — fill /Users/kevinkreative/genseo/roster.json (real people only)")
    elif not (author_pages & ROSTER_PAGES): fails.append("no roster author /pages/ link")
    if author_pages & ROSTER_PAGES and not re.search(r'"@type"\s*:\s*"Person"', html):
        # publisher injects Person JSON-LD after md->html, so a draft can't have it yet
        (warns if draft_mode else fails).append("staff author must use Person schema (publisher adds it post-conversion)")
    # A real name with an invented credential is the same YMYL fabrication as a fake doctor, and
    # instructions in SKILL.md have not held before, so it is enforced here as code. Only the
    # vetted bio sentence per author is allowed; anything the model adds about them fails.
    for name in FAKE_AUTHORS:
        # case-sensitive: the Title Case placeholder names can't collide with prose
        # like "the author one might expect"
        if re.search(rf"\b{re.escape(name)}\b", html):
            fails.append(f"fabricated author byline: {name}")
    bio=BIO_RE.search(html)
    bio=bio.group(1) if bio else ""
    if bio:
        cred=re.search(r'(?i)\b(Dr\.|\bMD\b|PhD|\bRD\b|Registered Dietitian|CISSN|Certified [A-Z]|'
                       r'\d+\+?\s*years of experience|Strength Coach|Endocrinolog|Naturopath|Physician)', _strip_approved(bio))
        if cred: fails.append(f"invented credential in author bio: {cred.group(1)}")
        if not any(s[:60].lower() in bio.lower() for s in APPROVED_BIOS):
            fails.append("author bio is not the approved sentence for that staff member")
    # brand mentions
    if html.count('Wellness Nest')<2: warns.append("brand 'Wellness Nest' used <2 times")
    # inline image COUNT — HARD gate (added 2026-07-26). The cheap model silently stopped generating
    # in-body images ~Jul22 and 18 articles published with ZERO inline images because the rule (SKILL
    # STEP 5: "1 lifestyle image per product, hero is never enough") was instruction-only — nothing
    # mechanical enforced it. This is that enforcement. Hero/cover is set as article.image (NOT body),
    # and publisher spacer imgs are display:none, so real in-body <img> = actual inline product images.
    imgs=re.findall(r'<img[^>]*>', html)
    real_imgs=[i for i in imgs if 'display:none' not in i.lower() and 'spacer' not in i.lower()]
    # In a .md draft the FIRST image tag is the hero: shopify_publisher.do_publish promotes it to
    # article.image and STRIPS it from the body. So a draft needs hero + MIN_INLINE_IMAGES tags to
    # land MIN_INLINE_IMAGES inline. Counting a draft's tags against the post-publish floor was off
    # by one and passed drafts that published one image short of the rule this gate exists for.
    md_draft=draft_mode and path.endswith(".md")
    need=MIN_INLINE_IMAGES+1 if md_draft else MIN_INLINE_IMAGES
    if len(real_imgs)<need:
        fails.append(f"only {len(real_imgs)} body image tag(s) — need ≥{need} "
                     f"({MIN_INLINE_IMAGES} inline, 1 lifestyle image per product"
                     f"{' + the hero, which the publisher strips out of the body' if md_draft else ''}"
                     f"). Generate product images (SKILL STEP 5).")

    # Every referenced local image must EXIST ON DISK, and be a file the QC gate passed.
    # Until 2026-08-13 this gate counted markdown tags and nothing else, so run 20260813-0847
    # printed "✓ PASS" on a draft whose hero was quarantined and whose other 3 image files had
    # never been written. A tag is a promise; the file is the delivery. Only the instruction-level
    # "abort if image generation fails" stood between that draft and a live page full of broken
    # images — which is exactly the instruction-only pattern this whole file exists to replace.
    if draft_mode:
        base=os.path.dirname(os.path.abspath(path))
        bad=[]
        for src in re.findall(r'<img[^>]*\bsrc=["\']([^"\']+)["\']', html):
            if re.match(r'(?i)https?://|data:', src):
                continue
            p=src if os.path.isabs(src) else os.path.join(base, src)
            if not os.path.exists(p):
                bad.append(f"{src} → no such file")
            elif os.path.getsize(p)==0:
                bad.append(f"{src} → 0 bytes")
            elif "QC-FAILED" in os.path.basename(p).upper():
                bad.append(f"{src} → quarantined by vision QC, must never be published")
        if bad:
            fails.append("image file(s) the draft references are not deliverable: "+"; ".join(bad))

    # brand rules (Kevin 2026-10-07, SKU audit 2026-10-09): AgeAura = the Pure NMN + TMG
    # NAD Complex only. Any other AgeAura handle, and a bare "AgeAura" with no NMN + TMG
    # product, are hard fails. FloraFresh claims follow its Supplement Facts label, never the
    # PDP description (Kevin 2026-10-09; scripts/brand_rules.py + florafresh_rules.py).
    # Shilajit Shockwave doses follow product_refs/shilajit-shockwave.label.json
    # (no milligram token; scripts/shockwave_rules.py).
    # Pure Shilajit Gold Resin doses follow product_refs/pure-shilajit-gold-resin.label.json
    # (OCR serving line and 75% Fulvic; no milligram token; scripts/gold_resin_rules.py).
    # ShilaSource Himalayan Shilajit Resin doses follow
    # product_refs/shilasource-himalayan-shilajit-resin.label.json
    # (front-of-pack lines only; no milligram token; scripts/shilasource_resin_rules.py).
    # Turkesterone Advanced Formula doses follow
    # product_refs/turkesterone-advanced-formula.label.json
    # (front-of-pack lines only; split 60 / Capsules badge; no milligram token;
    # scripts/turkesterone_rules.py).
    _v=_br.violations(html)
    if _v: fails.append("brand rule — banned link(s)/mentions/claims: "+"; ".join(_v[:6]))

    # Citability (answer shape, FAQ, question H2s, product + related article,
    # primary source, alt text, draft meta length, no hand-written Published date).
    cite_fails, cite_warns = geo_citability.assess(html, require_meta=draft_mode)
    fails.extend(cite_fails)
    warns.extend(cite_warns)
    dead_cites, soft_cites = geo_citability.citation_issues(
        [(u, *geo_citability.fetch_status(u)) for u in geo_citability.external_urls(html)])
    fails.extend(dead_cites)
    warns.extend(soft_cites)

    # link liveness (products, collections, article URLs, pages, policies, author pages).
    # HTTP 429 is indeterminate: check_link retries, and a rate limit that is
    # still there becomes WARN/UNVERIFIED (exit 3). Publish stays blocked.
    urls=list(geo_citability.internal_urls(html))
    for ap in sorted(author_pages & ROSTER_PAGES):
        absu="https://wellnessnest.co"+ap
        if absu not in urls:
            urls.append(absu)
    link_fails, link_warns, link_exit=assess_internal_links(urls)
    fails.extend(link_fails)
    warns.extend(link_warns)

    # ---- QRG prose-quality gate -------------------------------------------
    # Score the VISIBLE PROSE only. Do not hand a whole rendered page to the
    # scorers: theme nav and product grids inflate the token count and the price
    # figures register as uncited statistics (measured 2026-07-30 on a live URL:
    # 140k tokens, 87 bogus "uncited statistics").
    plain=re.sub(r'<[^>]*>',' ',re.sub(r'<!--.*?-->','',text,flags=re.S))
    plain=re.sub(r'[ \t]+',' ',plain).strip()
    qrg,qrg_note=qrg_scores(plain)
    qrg_fails,qrg_warns,qrg_line=qrg_report(qrg, qrg_note)
    fails.extend(qrg_fails)
    warns.extend(qrg_warns)

    print(f"=== VALIDATE {path} ===")
    print(f"words(content only): {words}  | h1:{len(h1s)} h2:{len(h2s)} table:{'<table' in html} faqschema:{'FAQPage' in html} collections:{len(colls)}")
    if qrg_line: print(qrg_line)
    if warns:
        print("WARNINGS:"); [print("  ⚠ "+w) for w in warns]
    exit_code=final_exit(fails, link_exit)
    # run-log: ground-truth that the gate fired (read by the operator to confirm the skill loaded)
    try:
        with open("/Users/kevinkreative/genseo/validate_runs.log","a") as lg:
            verdict={0:"PASS",1:"FAIL",EXIT_UNVERIFIED:"UNVERIFIED"}.get(exit_code,"FAIL")
            qcol=qrg_log_column(qrg, qrg_note)
            bits=list(fails)
            bits.extend(w for w in warns if "UNVERIFIED" in w)
            lg.write(f"{datetime.datetime.now().isoformat(timespec='seconds')}\t{verdict}\twords={words}\t{qcol}\t{path}\t{';'.join(bits)[:200]}\n")
    except Exception:
        pass

    if exit_code==1:
        print("FAILED:"); [print("  ✗ "+f) for f in fails]
        if any(f.startswith(("filler score","AI-pattern score")) for f in fails):
            csbin=_claude_seo_bin()
            if csbin:
                print(f"\n  Deterministic 1:1 phrase cleanup (review the diff, it does not add content):")
                print(f"    {csbin} run content_humanize.py {path} -o {path}.cleaned")
    print("\n"+result_line(exit_code))
    sys.exit(exit_code)

if __name__=="__main__":
    main()

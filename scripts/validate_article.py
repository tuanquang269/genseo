#!/usr/bin/env python3
"""
validate_article.py — Mechanical quality gate for GenSeo articles.
Runs the SELF-AUDIT checklist as code so a cheap model CANNOT publish thin content
by mistake. The publisher skill calls this FIRST; non-zero exit = do not publish.

Usage: python3 validate_article.py <article.html|article.md>
Exit 0 = PASS (publish allowed). Exit 1 = FAIL (prints what's missing).
Also verifies that every linked product/collection/author URL returns 200.
"""
import sys, os, re, glob, json, subprocess, tempfile, urllib.request, urllib.error
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genseo_roster
import brand_rules as _br
import geo_citability
import first_hand_experience as _fh

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

def http_ok(url):
    # Shopify throttles bursts of bare no-UA requests, which made this report live URLs as
    # dead (2026-08-09: /pages/dr-marcus-hale + both AgeAura PDPs all 200 on manual curl).
    # Browser UA + retry/backoff, and a throttle/transient code never counts as dead.
    import subprocess, time
    for attempt in range(3):
        try:
            res = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-A", UA, "-w", "%{http_code}", url],
                capture_output=True, text=True, timeout=15)
            code = res.stdout.strip()
        except Exception:
            code = ""
        if code.startswith("2") or code in ("301", "302", "307", "308"):
            return True
        if code in ("404", "410"):
            return False          # a real dead link — no point retrying
        if attempt < 2:
            time.sleep(1.5 * (attempt + 1))
    return code in ("429", "430", "503")  # throttled/transient → don't fail the article on it

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


def draft_struct_html(raw):
    """HTML the draft structural checks see.

    Images before links. ![alt](https://...) matches the link pattern.
    The old order turned a Shopify CDN image into an <a>, so the <img>
    counter saw 0. A remote src is still a fail. See remote_image_fail.
    Reference images (![alt][id] with [id]: url) become <img> as well.
    markdown.markdown(..., extensions=['extra']) emits that tag, and a
    remote definition used to skip this gate entirely.
    Newlines and tabs are normalized first, the same way that parser expands
    them, so a tab or CR in a reference definition cannot hide the URL.
    Inline images keep nested alt brackets and <url> destinations. A raw
    <img> or <source> that spans lines is joined before the first-paragraph
    wrap, which used to split src onto a line the tag regex missed.
    """
    html=_normalize_md_ws(raw)
    html=re.sub(r'^###\s+(.*)$', r'<h3>\1</h3>', html, flags=re.M)
    html=re.sub(r'^##\s+(.*)$',  r'<h2>\1</h2>', html, flags=re.M)
    html=re.sub(r'^#\s+(.*)$',   r'<h1>\1</h1>', html, flags=re.M)
    html=_replace_inline_images(html)
    html=_expand_reference_images(html)
    html=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', html)
    # markdown tables -> mark presence
    if re.search(r'^\|.*\|\s*$', html, flags=re.M) and re.search(r'^\|[-: |]+\|\s*$', html, flags=re.M):
        html+="\n<table><th>markdown-table</th></table>"
    # Join multiline image tags before the paragraph pass. That pass wraps
    # the first plain line, which used to be the src line of <img\nsrc="...">.
    html=_flatten_image_tags(html)
    # first PLAIN-TEXT paragraph as answer block — skip any line already starting
    # with a tag or comment (the skill's mandatory line-2 `<!-- meta_description -->`
    # otherwise becomes the "first paragraph" and every correct draft fails)
    html=re.sub(r'^(?!<|\s*$)(.+)$', r'<p>\1</p>', html, count=1, flags=re.M)
    return html


def _normalize_md_ws(text):
    """CRLF to LF, then tabs to spaces. Python-Markdown does this before references."""
    text=(text or "").replace("\r\n", "\n").replace("\r", "\n")
    return text.expandtabs(4)


def _replace_inline_images(text):
    """Turn ![alt](dest) into <img>, including forms the one-line regex dropped.

    Nested brackets in the alt, a destination in <angle> brackets, a quoted
    title that itself contains ')', and parentheses inside the URL are all
    images markdown.markdown will publish. The old [^)]+ pattern stopped at
    the first ')' and left the remote URL as plain text.
    """
    text=text or ""
    out=[]
    i=0
    n=len(text)
    while i<n:
        if text.startswith("![", i) and (i==0 or text[i-1]!="\\"):
            alt, j, ok=_parse_md_alt(text, i+1)
            if ok and j<n and text[j]=="(":
                src, k, ok2=_parse_md_dest(text, j)
                if ok2:
                    out.append('<img alt="%s" src="%s">' % (_esc_attr(alt), _esc_attr(src)))
                    i=k
                    continue
            # ![alt][id] is a reference image. Leave it for _expand_reference_images.
        out.append(text[i])
        i+=1
    return "".join(out)


def _parse_md_alt(text, i):
    """text[i] is the '[' of ![. Return (alt, index after ']', ok)."""
    if i>=len(text) or text[i]!="[":
        return None, i, False
    i+=1
    depth=1
    buf=[]
    n=len(text)
    while i<n and depth:
        c=text[i]
        if c=="\\" and i+1<n:
            buf.append(text[i+1])
            i+=2
            continue
        if c=="[":
            depth+=1
            buf.append(c)
        elif c=="]":
            depth-=1
            if depth==0:
                return "".join(buf), i+1, True
            buf.append(c)
        else:
            buf.append(c)
        i+=1
    return None, i, False


def _skip_md_ws(text, i):
    n=len(text)
    while i<n and text[i] in " \t\n":
        i+=1
    return i


def _skip_md_title(text, i):
    """Skip an optional markdown link title. Return the index after it."""
    n=len(text)
    i=_skip_md_ws(text, i)
    if i>=n:
        return i
    if text[i] in "'\"":
        q=text[i]
        j=text.find(q, i+1)
        if j<0:
            return i
        return j+1
    if text[i]=="(":
        depth=1
        i+=1
        while i<n and depth:
            if text[i]=="(":
                depth+=1
            elif text[i]==")":
                depth-=1
            i+=1
        return i
    return i


def _dest_without_title(body):
    body=(body or "").strip()
    titled=re.search(r'\s+(?P<q>["\']).*?(?P=q)\s*$', body, re.S)
    if titled and titled.start()>0:
        return body[:titled.start()].strip()
    paren=re.search(r'\s+\([^)]*\)\s*$', body, re.S)
    if paren and paren.start()>0:
        return body[:paren.start()].strip()
    return body


def _parse_md_dest(text, i):
    """text[i] is the '(' of a markdown destination. Return (src, index after ')', ok)."""
    if i>=len(text) or text[i]!="(":
        return None, i, False
    i+=1
    n=len(text)
    i=_skip_md_ws(text, i)
    if i<n and text[i]=="<":
        end=text.find(">", i+1)
        if end<0:
            return None, i, False
        src=text[i+1:end].strip()
        i=_skip_md_title(text, end+1)
        i=_skip_md_ws(text, i)
        if i<n and text[i]==")":
            return src, i+1, True
        return None, i, False
    start=i
    depth=1
    quote=None
    while i<n:
        c=text[i]
        if quote:
            if c==quote:
                quote=None
            i+=1
            continue
        # A title is whitespace plus a quote. An apostrophe inside a URL is not.
        if c in "'\"" and i>start and text[i-1] in " \t\n":
            quote=c
            i+=1
            continue
        if c=="(":
            depth+=1
        elif c==")":
            depth-=1
            if depth==0:
                return _dest_without_title(text[start:i]), i+1, True
        i+=1
    return None, i, False


def _flatten_image_tags(html):
    """One line per <img> and <source>, so a newline cannot hide src or srcset."""
    def flat(match):
        return re.sub(r'[ \t\r\n]+', ' ', match.group(0))
    html=re.sub(r'(?is)<img\b'+_TAG_BODY+r'>', flat, html)
    html=re.sub(r'(?is)<source\b'+_TAG_BODY+r'>', flat, html)
    return html


# shopify_publisher uploads an absolute path only when the string itself
# starts with /Users or /private, and (once it knows the draft) a relative
# assets/<slug>/<file> joined to the draft directory. Do not import the
# publisher. realpath of that relative form has to stay inside the draft's
# assets directory, not merely the draft folder. /Users/../../etc/passwd
# exists, and on macOS it resolves under /private/etc.
_TAG_BODY=r'''(?:[^>"']|"[^"]*"|'[^']*')*'''
_IMG_TAG_RE=re.compile(r'(?is)<img\b'+_TAG_BODY+'>')
_SOURCE_TAG_RE=re.compile(r'(?is)<source\b'+_TAG_BODY+'>')
# Coffee draft and the localized drafts: assets/<slug>/<file> beside the markdown.
_ASSET_REL_RE=re.compile(
    r'^assets/[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$')
# Same shape as markdown's ReferenceProcessor, so ![alt][id] + [id]: url
# becomes an <img> the file check can see.
_REF_DEF_RE=re.compile(
    r'^[ ]{0,3}\[([^\[\]]*)\]:[ ]*\n?[ ]*([^\s]+)[ ]*(?:\n[ ]*)?'
    r'(?:(?:["\']).*["\'][ ]*|\(.*\)[ ]*)?$',
    re.M)
_IMG_EXPLICIT_REF_RE=re.compile(r'!\[([^\]]*)\][ \t]*\n?[ \t]*\[([^\]]*)\]')
_IMG_SHORT_REF_RE=re.compile(r'!\[([^\]]+)\](?![ \t]*[\[(])')


class _TagAttrs(HTMLParser):
    """Attribute list for one start tag, in source order.

    html.parser reads <img/src="https://..."> (no space) and does not treat
    ` src=` inside a quoted alt as an attribute. Duplicate src/srcset values
    are kept; the first quoted-src regex used to stop on an alt bait path.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.attrs=[]

    def handle_starttag(self, tag, attrs):
        self.attrs=attrs

    def handle_startendtag(self, tag, attrs):
        self.attrs=attrs


def _parse_tag_attrs(tag):
    parser=_TagAttrs()
    try:
        parser.feed(tag)
        parser.close()
    except Exception:
        return []
    return parser.attrs


def _srcset_urls(value):
    urls=[]
    for part in (value or "").split(","):
        part=part.strip()
        if not part:
            continue
        urls.append(part.split()[0])
    return urls


def _image_urls(tag):
    """Every src and srcset URL on one <img> or <source> tag."""
    urls=[]
    for name, value in _parse_tag_attrs(tag):
        if value is None:
            continue
        low=name.lower()
        if low=="src":
            urls.append(value)
        elif low=="srcset":
            urls.extend(_srcset_urls(value))
    return urls


def img_tag_src(tag):
    """First src attribute, including unquoted src= and <img/src=...>."""
    for name, value in _parse_tag_attrs(tag):
        if name.lower()=="src" and value is not None:
            return value
    return None


def _remote_url_image_message(src):
    return (src+" → remote URL image: download it to a local file. "
            "Save the bytes on an absolute /Users or /private path, "
            "or assets/<slug>/<file> inside the draft directory. "
            "shopify_publisher uploads those paths and sets article.image from the first local file.")


def _data_uri_image_message(src):
    return (src+" → data URI image: write the bytes to a local file. "
            "Save them on an absolute /Users or /private path, "
            "or assets/<slug>/<file> inside the draft directory. "
            "shopify_publisher uploads those paths and sets article.image from the first local file.")


def _not_local_image_message(src):
    return (src+" → not a publisher-local image: shopify_publisher uploads only "
            "an absolute /Users or /private file, or assets/<slug>/<file> "
            "inside the draft directory.")


def _outside_root_message(src):
    return src+" → resolves outside allowed image roots"


def _abs_local_root(src):
    """Prefix the publisher treats as a local file, or None.

    The next character has to be the end or a slash, so /private-evil is
    not a /private path.
    """
    for root in ("/Users", "/private"):
        if src==root or src.startswith(root+"/"):
            return root
    return None


def _stays_under(path, root):
    """True when normpath and realpath both stay inside root.

    normpath rejects /Users/../../etc/passwd before macOS realpath follows
    /etc -> /private/etc and lands back under /private. realpath rejects a
    symlink whose lexical path is inside the root and whose target is not.
    """
    root_n=os.path.abspath(root)
    lex=os.path.abspath(os.path.normpath(path))
    if lex!=root_n and not lex.startswith(root_n+os.sep):
        return False
    real=os.path.realpath(path)
    root_r=os.path.realpath(root)
    try:
        return os.path.commonpath([real, root_r])==root_r
    except ValueError:
        return False


def remote_image_fail(src, base=None):
    """Fail a draft image shopify_publisher will not upload.

    http(s), a protocol-relative // host, the same URLs wrapped in <angle>
    brackets, and the same URLs with leading whitespace are remote. data:
    is inline, not a file. An absolute /Users or /private path is local
    only when realpath stays inside that prefix. assets/<slug>/<file> is
    local when base is the draft directory and realpath stays inside that
    draft's assets directory. A symlink from assets/<slug>/<file> to
    another file in the draft folder, or to anywhere else, is not. Any
    other relative path is not.
    """
    root=_abs_local_root(src)
    if root:
        if _stays_under(src, root):
            return ""
        return _outside_root_message(src)
    stripped=_unwrap_angle(src)
    if re.match(r'(?i)https?://', stripped) or stripped.startswith("//"):
        return _remote_url_image_message(src)
    if re.match(r'(?i)data:', stripped):
        return _data_uri_image_message(src)
    if base and not os.path.isabs(src):
        joined=os.path.join(base, src)
        if not _stays_under(joined, base):
            return _outside_root_message(src)
        if _ASSET_REL_RE.match(src):
            assets_root=os.path.join(base, "assets")
            if not _stays_under(joined, assets_root):
                return _outside_root_message(src)
            return ""
    return _not_local_image_message(src)


def _unwrap_angle(src):
    """Strip one pair of markdown <angle> brackets around a destination."""
    stripped=(src or "").strip()
    if len(stripped)>=2 and stripped[0]=="<" and stripped[-1]==">":
        return stripped[1:-1].strip()
    return stripped


def _norm_ref_id(text):
    return re.sub(r'\s+', ' ', (text or '').strip().lower())


def _esc_attr(value):
    return (value or "").replace("&", "&amp;").replace('"', "&quot;")


def _reference_defs(text):
    """id -> url. Later definitions overwrite, matching Python-Markdown."""
    refs={}
    for match in _REF_DEF_RE.finditer(text or ""):
        ref_id=_norm_ref_id(match.group(1))
        if not ref_id:
            continue
        refs[ref_id]=match.group(2).lstrip("<").rstrip(">")
    return refs


def _expand_reference_images(text):
    """Turn reference-style images into <img> tags.

    Inline ![alt](url) is already converted. ![alt][id], ![alt][], and
    shortcut ![alt] stay as text unless this runs, so a [id]: https://...
    definition never reaches the src check.
    """
    refs=_reference_defs(text)
    if not refs:
        return text

    def explicit(match):
        alt=match.group(1)
        raw=match.group(2).strip()
        src=refs.get(_norm_ref_id(raw if raw else alt))
        if src is None:
            return match.group(0)
        return '<img alt="%s" src="%s">' % (_esc_attr(alt), _esc_attr(src))

    text=_IMG_EXPLICIT_REF_RE.sub(explicit, text)

    def shortcut(match):
        alt=match.group(1)
        src=refs.get(_norm_ref_id(alt))
        if src is None:
            return match.group(0)
        return '<img alt="%s" src="%s">' % (_esc_attr(alt), _esc_attr(src))

    return _IMG_SHORT_REF_RE.sub(shortcut, text)


def _md_image_skipped(tag, base):
    """True when an <img> must not fill the inline-image floor."""
    urls=_image_urls(tag)
    if not urls:
        return False
    return any(remote_image_fail(src, base) for src in urls)


def visible_body_images(html, md_draft, base=None):
    """In-body <img> tags that count toward the floor.

    A .md draft must not let a data: URI, a remote URL, a srcset URL, a
    bare relative path, or a path that realpath leaves the allowed root
    satisfy the floor. assets/<slug>/<file> counts only when realpath
    stays inside the draft's assets directory: the publisher uploads that
    form and strips the first local file into article.image.
    """
    real=[]
    for tag in _IMG_TAG_RE.findall(html):
        low=tag.lower()
        if 'display:none' in low or 'spacer' in low:
            continue
        if md_draft and _md_image_skipped(tag, base):
            continue
        real.append(tag)
    return real


def _iter_image_tags(html):
    for tag in _IMG_TAG_RE.findall(html):
        yield tag
    for tag in _SOURCE_TAG_RE.findall(html):
        yield tag


def draft_image_file_fails(html, base):
    """Non-deliverable image URLs. The same rule for every --draft suffix.

    src and srcset on <img>, and srcset on <source>, are all image loads.
    A path is deliverable only when it is publisher-local and the realpath
    is a real file inside an allowed root.
    """
    bad=[]
    for tag in _iter_image_tags(html):
        for src in _image_urls(tag):
            msg=remote_image_fail(src, base)
            if msg:
                bad.append(msg)
                continue
            p=src if os.path.isabs(src) else os.path.join(base, src)
            if not os.path.isfile(p):
                bad.append(f"{src} → no such file")
            elif os.path.getsize(p)==0:
                bad.append(f"{src} → 0 bytes")
            elif "QC-FAILED" in os.path.basename(p).upper():
                bad.append(f"{src} → quarantined by vision QC, must never be published")
    return bad


def draft_image_gate(path, html):
    """--draft image gate. .html is held to the same rule as .md.

    The old gate called remote_image_fail only when the path ended in .md,
    so a published HTML body full of CDN srcs was skipped.
    """
    base=os.path.dirname(os.path.abspath(path))
    return draft_image_file_fails(html, base)


def _dup_cluster_lines(raw, h1s, h2s, path):
    """Publish-time query-cluster check. Warn-only unless GENSEO_DUP_CLUSTER_BLOCK=1.

    An exact primary-query match stays a warning by default so the daily lane
    cannot block on it. A missing catalog or an unexpected error is a skip
    warning, never a failure.
    """
    if not h1s:
        return [], []
    try:
        import dup_cluster_gate as gate
        title = re.sub(r"<[^>]*>", "", h1s[0]).strip()
        heads = [re.sub(r"<[^>]*>", "", h).strip() for h in h2s]
        km = re.search(r"<!--\s*primary_keyword:\s*(.*?)\s*-->", raw or "", re.I)
        keyword = km.group(1).strip() if km else title
        slug = os.path.splitext(os.path.basename(path or ""))[0]
        report = gate.assess(title=title, keyword=keyword, h2s=heads, slug=slug)
        return gate.gate_lines(report)
    except Exception as e:
        return [], ["dup_cluster_gate skipped (%s)" % e]


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
        html=draft_struct_html(raw)
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
    # Near-duplicate / query-cluster gate (warn-only). Isolated from the hard
    # fails above: GENSEO_DUP_CLUSTER_BLOCK=1 is the only way an exact primary
    # query becomes a publish block. Local catalog only.
    if draft_mode and h1s:
        dup_fails, dup_warns = _dup_cluster_lines(raw, h1s, h2s, path)
        fails.extend(dup_fails)
        warns.extend(dup_warns)
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
    # In a .md draft the FIRST image tag is the hero: shopify_publisher.do_publish promotes it to
    # article.image and STRIPS it from the body. So a draft needs hero + MIN_INLINE_IMAGES tags to
    # land MIN_INLINE_IMAGES inline. Counting a draft's tags against the post-publish floor was off
    # by one and passed drafts that published one image short of the rule this gate exists for.
    # Non-local srcs (data:, http(s), //host, bare relative paths, srcset URLs,
    # and paths that realpath leaves the allowed root) do not count toward that
    # floor. assets/<slug>/<file> inside the draft directory does count.
    # Four data URIs used to pass the count and the file check together.
    md_draft=draft_mode and path.endswith(".md")
    real_imgs=visible_body_images(html, md_draft, os.path.dirname(os.path.abspath(path)))
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
    # Any --draft file, not only .md. A CDN src in published HTML used to be
    # skipped because remote_image_fail ran only for the .md suffix.
    if draft_mode:
        bad=draft_image_gate(path, html)
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

    # First-hand experience quotes (blog articles only). The helper omits any
    # registry line that is not rights_confirmed with approved_by set. A draft
    # that pastes one of those lines, or a block that fails the claim lint, fails
    # here. No block and no registry sentence is silent, so live output is unchanged
    # until Kevin clears a line. This check does not choose a byline.
    fh_fails, fh_warns = _fh.article_findings(html)
    fails.extend(fh_fails)
    warns.extend(fh_warns)

    # Citability (answer shape, FAQ, question H2s, product + related article,
    # primary source, alt text, draft meta length, no hand-written Published date).
    cite_fails, cite_warns = geo_citability.assess(html, require_meta=draft_mode)
    fails.extend(cite_fails)
    warns.extend(cite_warns)
    dead_cites, soft_cites = geo_citability.citation_issues(
        [(u, *geo_citability.fetch_status(u)) for u in geo_citability.external_urls(html)])
    fails.extend(dead_cites)
    warns.extend(soft_cites)

    # link liveness (products, collections, article URLs, pages, policies, author pages)
    urls=set(geo_citability.internal_urls(html))
    dead=[u for u in urls if not http_ok(u)]
    # author pages
    for ap in (author_pages & ROSTER_PAGES):
        if not http_ok("https://wellnessnest.co"+ap): dead.append("https://wellnessnest.co"+ap)
    if dead:
        fails.append("dead/404 links: "+", ".join(d.replace('https://wellnessnest.co','') for d in dead[:6]))

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
    # run-log: ground-truth that the gate fired (read by the operator to confirm the skill loaded)
    try:
        import datetime
        with open("/Users/kevinkreative/genseo/validate_runs.log","a") as lg:
            verdict="FAIL" if fails else "PASS"
            qcol=qrg_log_column(qrg, qrg_note)
            lg.write(f"{datetime.datetime.now().isoformat(timespec='seconds')}\t{verdict}\twords={words}\t{qcol}\t{path}\t{';'.join(fails)[:200]}\n")
    except Exception:
        pass

    if fails:
        print("FAILED:"); [print("  ✗ "+f) for f in fails]
        if any(f.startswith(("filler score","AI-pattern score")) for f in fails):
            csbin=_claude_seo_bin()
            if csbin:
                print(f"\n  Deterministic 1:1 phrase cleanup (review the diff, it does not add content):")
                print(f"    {csbin} run content_humanize.py {path} -o {path}.cleaned")
        print("\nRESULT: ✗ DO NOT PUBLISH — fix the above and re-validate.")
        sys.exit(1)
    print("\nRESULT: ✓ PASS — safe to publish.")
    sys.exit(0)

if __name__=="__main__":
    main()

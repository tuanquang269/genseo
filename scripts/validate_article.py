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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genseo_roster

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
QRG_MIN_OVERALL=80
QRG_MAX_FILLER=25
QRG_MAX_AI=25
QRG_WARN_REPETITION=20
QRG_WARN_DENSITY=0.55

def _claude_seo_bin():
    """Locate the claude-seo launcher. Glob so a marketplace rename can't break us."""
    for p in glob.glob(os.path.expanduser(
            "~/.claude/plugins/marketplaces/*claude-seo*/bin/claude-seo")):
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

def qrg_scores(plain_text):
    """Score prose quality + citation gaps. Returns (scores_dict, note) where a
    non-empty note means scoring was skipped and nothing should be enforced."""
    binary=_claude_seo_bin()
    if not binary:
        return None, "claude-seo runtime not installed"
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

def http_ok(url):
    import subprocess
    try:
        res = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url], capture_output=True, text=True, timeout=10)
        return res.stdout.strip() in ("200", "301", "302", "429")
    except Exception:
        return False

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
        if re.search(rf"\b{re.escape(name)}\b", md, re.I): fails.append(f"fabricated byline: {name}")
    bio=BIO_RE.search(md)
    if bio:
        bio=bio.group(1)
        cred=re.search(r'(?i)\b(Dr\.|\bMD\b|PhD|\bRD\b|Registered Dietitian|CISSN|Certified [A-Z]|'
                       r'\d+\+?\s*years of experience|Strength Coach|Endocrinolog|Naturopath|Physician)', bio)
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
            html+="\n<table><th>md-table</th></table>"
        # first non-heading paragraph as answer block
        html=re.sub(r'^(?!<h|<a|<img|\s*$)(.+)$', r'<p>\1</p>', html, count=1, flags=re.M)
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
        if len(t)>65: warns.append(f"title {len(t)} chars (>65 truncates in Google → lower CTR): {t[:60]}…")
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
    def visible_text(frag):
        f=re.sub(r'<!--.*?-->','',frag,flags=re.S)   # drop HTML comments
        f=re.sub(r'<[^>]*>','',f)                     # drop tags
        return f.strip()
    answer=None
    for pm in re.finditer(r'<p[^>]*>(.*?)</p>', html, re.S|re.I):
        # skip hidden/spacer paragraphs
        if 'display:none' in pm.group(0).lower() or 'spacer' in pm.group(0).lower():
            continue
        txt=visible_text(pm.group(1))
        if len(txt.split())>=20:
            answer=txt; break
    if answer is not None:
        aw=len(answer.split())
        if not (30<=aw<=90): warns.append(f"answer block {aw} words (target 40–60)")
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
    # FAQ questions can be <p><strong>Q?</strong> OR <h3>Q?</h3> (publisher uses h3)
    faq_qs=re.findall(r'<p[^>]*>\s*<strong>([^<]*\?)\s*</strong>', html)
    faq_qs+=re.findall(r'<h3[^>]*>([^<]*\?)\s*</h3>', html)
    if len(faq_qs)<3: warns.append(f"only {len(faq_qs)} visible FAQ questions")
    # author: named staff member + live page
    author_pages=set(re.findall(r'(/pages/[a-z-]+)', html))
    if not ROSTER_PAGES:
        fails.append("author roster EMPTY — fill /Users/kevinkreative/genseo/roster.json (real people only)")
    elif not (author_pages & ROSTER_PAGES): fails.append("no roster author /pages/ link")
    if author_pages & ROSTER_PAGES and not re.search(r'"@type"\s*:\s*"Person"', html):
        fails.append("staff author must use Person schema")
    # A real name with an invented credential is the same YMYL fabrication as a fake doctor, and
    # instructions in SKILL.md have not held before, so it is enforced here as code. Only the
    # vetted bio sentence per author is allowed; anything the model adds about them fails.
    for name in FAKE_AUTHORS:
        if re.search(rf"\b{re.escape(name)}\b", html, re.I):
            fails.append(f"fabricated author byline: {name}")
    bio=BIO_RE.search(html)
    bio=bio.group(1) if bio else ""
    if bio:
        cred=re.search(r'(?i)\b(Dr\.|\bMD\b|PhD|\bRD\b|Registered Dietitian|CISSN|Certified [A-Z]|'
                       r'\d+\+?\s*years of experience|Strength Coach|Endocrinolog|Naturopath|Physician)', bio)
        if cred: fails.append(f"invented credential in author bio: {cred.group(1)}")
        if not any(s[:60].lower() in bio.lower() for s in APPROVED_BIOS):
            fails.append("author bio is not the approved sentence for that staff member")
    # brand mentions
    if html.count('Wellness Nest')<2: warns.append("brand 'Wellness Nest' used <2 times")
    # images alt
    imgs=re.findall(r'<img[^>]*>', html)
    noalt=[i for i in imgs if 'alt=' not in i or re.search(r'alt=["\']\s*["\']',i)]
    if imgs and noalt: warns.append(f"{len(noalt)} image(s) missing alt text")
    # inline image COUNT — HARD gate (added 2026-07-26). The cheap model silently stopped generating
    # in-body images ~Jul22 and 18 articles published with ZERO inline images because the rule (SKILL
    # STEP 5: "1 lifestyle image per product, hero is never enough") was instruction-only — nothing
    # mechanical enforced it. This is that enforcement. Hero/cover is set as article.image (NOT body),
    # and publisher spacer imgs are display:none, so real in-body <img> = actual inline product images.
    real_imgs=[i for i in imgs if 'display:none' not in i.lower() and 'spacer' not in i.lower()]
    if len(real_imgs)<MIN_INLINE_IMAGES:
        fails.append(f"only {len(real_imgs)} inline body image(s) — need ≥{MIN_INLINE_IMAGES} "
                     f"(1 lifestyle image per product; hero/cover doesn't count). Generate product images (SKILL STEP 5).")

    # link liveness (products, collections, author pages)
    urls=set(re.findall(r'https://wellnessnest\.co/(?:products|collections|blogs)/[a-z0-9-]+', html))
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
    qrg_line=""
    if qrg_note:
        warns.append(f"QRG quality scoring skipped ({qrg_note})")
    else:
        q,v=qrg["quality"],qrg["verify"]
        advisory=os.environ.get("GENSEO_QRG_ADVISORY")=="1"
        sink=warns if advisory else fails
        hits=lambda lst: ", ".join(lst[:6]) if lst else "none"
        qrg_line=(f"QRG: overall {q['overall_quality']}/100 "
                  f"filler {q['filler_score']} ai {q['ai_pattern_score']} "
                  f"repetition {q['repetition_score']} density {q['information_density']} "
                  f"| claims {v['claim_count']} uncited {v['uncited_count']}")
        if q["overall_quality"] < QRG_MIN_OVERALL:
            sink.append(f"QRG overall quality {q['overall_quality']}/100 below {QRG_MIN_OVERALL} "
                        f"(scaled-content-abuse risk; p10 of our own corpus is 83)")
        if q["filler_score"] >= QRG_MAX_FILLER:
            sink.append(f"filler score {q['filler_score']} >= {QRG_MAX_FILLER} — remove: "
                        f"{hits(q['matches']['filler'])}")
        if q["ai_pattern_score"] >= QRG_MAX_AI:
            sink.append(f"AI-pattern score {q['ai_pattern_score']} >= {QRG_MAX_AI} — rewrite: "
                        f"{hits(q['matches']['ai_patterns'])}")
        if q["repetition_score"] >= QRG_WARN_REPETITION:
            warns.append(f"repetition {q['repetition_score']} (p90 of corpus is 13) — likely restating the same point")
        if q["information_density"] < QRG_WARN_DENSITY:
            warns.append(f"information density {q['information_density']} < {QRG_WARN_DENSITY} — padded prose")
        if v["claim_count"] >= 3 and v["uncited_ratio"] >= 1.0:
            warns.append(f"{v['claim_count']} factual claims, none cited — add a source or drop the numbers")

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
            qcol=f"qrg={qrg['quality']['overall_quality']}/{qrg['quality']['filler_score']}/{qrg['quality']['ai_pattern_score']}" if qrg else "qrg=skip"
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

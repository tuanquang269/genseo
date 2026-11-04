#!/usr/bin/env python3
"""Cherish Journal daily auto-publish (launchd com.pati.genseo-cherish, 07:45 ICT). Calendar rows with approval=auto only.

  1. run_store --apply --generate --hold for the day (default: tomorrow, ICT). Every run_store gate runs (template rules machine,
     hero budget/hero_set, number/fact checks, product-handle guard, isolation guard). Articles are created UNPUBLISHED.
  2. Fidelity gate per held post on a hidden noindex journal-qa copy: gate selftest first, noindex read in Chrome, copies deleted after.
  3. PASS -> publish, read back, gate again on the real URL (FAIL -> unpublish). Any failure leaves the article unpublished.
  4. ~/PATI/work/cherish-seo/daily/<run date>.md lists the published links and every row that did not publish.

  /usr/bin/python3 cherish_auto.py [--day YYYY-MM-DD] [--skip-generate]
The MAIN theme is read, never written. No Wellness Nest path is touched.
"""
import argparse
import csv
import datetime as dt
import fcntl
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from store_profiles import Profile, StoreGuardError, ROOT, require  # noqa: E402
import run_store  # noqa: E402

ICT = ZoneInfo('Asia/Ho_Chi_Minh')
PY = '/usr/bin/python3'  # has bs4, Playwright, Pillow, numpy
QA_PY = '/opt/homebrew/bin/python3'  # qa_stage -> the shared store adapter needs Python 3.10+ (3.9 fails on `str | None`)
SKILL = Path.home()/'.claude/skills/shopify-article-template-genseo/scripts'
WORK = Path.home()/'PATI/work/cherish-seo'
GATE_PROFILE = WORK/'genseo-auto/store.json'
STATE = ROOT/'state'/'cherish'


def log(*a):
    print(dt.datetime.now(ICT).strftime('%H:%M:%S'), *a, flush=True)


# Values the Journal shell prints from metafields and theme settings, never from the writer's page (the day-23 truth pages carry the same).
# ponytail: constants mirror the live shell; change them with the theme (journal shell snippet, band guarantee setting).
SHELL_IMG = {'width': '1122', 'height': '1402', 'sizes': '(min-width:1100px) 720px, 100vw', 'loading': 'eager'}
SHIP_LINE = '100 nights from delivery · you keep it · no return postage · free US standard shipping at $69+ · fulfilled and shipped in the US in 1–3 working days on average, with tracking'


def set_attrs(tag, attrs):
    for key, value in attrs.items():
        tag, n = re.subn(rf'\s{key}="[^"]*"', f' {key}="{value}"', tag)
        tag = tag if n else tag.replace('<img', f'<img {key}="{value}"', 1)
    return tag


def shell_owned(page):
    """The truth page as the shell prints it: hero and card image boxes, band guarantee line, sticky bar (from journal.pick)."""
    hero = {k: SHELL_IMG[k] for k in ('width', 'height')}
    page = re.sub(r'(<figure class="hero">\s*)(<img\b[^>]*>)', lambda m: m.group(1) + set_attrs(m.group(2), hero), page, count=1)
    def card(m, widths):   # the shell prints the image URL list per card type: pick 300/600/1200 (src 600), mini 200/400/800 (src 400)
        base = re.search(r'src="([^"]+?)&(?:amp;)?width=\d+"', m.group(2)).group(1)
        srcset = ', '.join(f'{base}&amp;width={w} {w}w' for w in widths)
        return m.group(1) + set_attrs(m.group(2), dict(SHELL_IMG, src=f'{base}&amp;width={widths[1]}', srcset=srcset))
    page = re.sub(r'(<div class="pick"[^>]*>\s*)(<img\b[^>]*>)', lambda m: card(m, (300, 600, 1200)), page)
    # band minis only: style 3 also uses .mini inside the article, which the shell prints as written
    page = re.sub(r'<section class="band".*?</section>', lambda b: re.sub(r'(<div class="mini"[^>]*>\s*)(<img\b[^>]*>)', lambda m: card(m, (200, 400, 800)), b.group(0)), page, flags=re.S)
    page = re.sub(r'(<section class="band"[^>]*>.*?<p class="small">)[^<]*(</p>)', lambda m: m.group(1) + SHIP_LINE + m.group(2), page, count=1, flags=re.S)
    if 'class="stick"' not in page:
        pick = re.search(r'<div class="pick"[^>]*>.*?<b>(.*?)</b>.*?<a class="btn" href="(/products/[a-z0-9-]+)"', page, re.S)
        if pick:
            page = page.replace('</body>', f'<div class="stick" id="stick" aria-hidden="true"><b>{pick.group(1)}</b><a class="btn" href="{pick.group(2)}" tabindex="-1">See it</a></div>\n</body>', 1)
    return page


def gate_page(page, template):
    """The fidelity gate's truth page: the writer's filled template with the approved CSS and the approved sticky-bar script
    (minus the preview label toggle, whose button the writer removed)."""
    style = re.search(r'<style\b[^>]*>.*?</style>', template, re.S).group(0)
    script = re.findall(r'<script>(.*?)</script>', template, re.S)[-1]
    script = '\n'.join(line for line in script.split('\n') if "getElementById('tgl')" not in line)
    marker = '<!-- Approved CSS is inserted by the runner. -->'
    page = page.replace(marker, style, 1) if marker in page else page.replace('</head>', style + '</head>', 1)
    require(style in page and '</body>' in page, 'Gate page assembly failed')
    page = shell_owned(page)
    return page.replace('</body>', '<script>' + script + '</script>\n</body>', 1)


def noindex(url):
    """robots meta as real Chrome sees it (curl gets HTTP 429 on this store)."""
    code = ('import sys\nfrom playwright.sync_api import sync_playwright\n'
            'with sync_playwright() as p:\n'
            ' b=p.chromium.launch(channel="chromium",args=["--disable-gpu"]); pg=b.new_page(); pg.goto(sys.argv[1],wait_until="domcontentloaded",timeout=90000)\n'
            ' m=pg.query_selector(\'meta[name="robots"]\'); print(m.get_attribute("content") if m else ""); b.close()\n')
    out = subprocess.run([PY, '-c', code, url], capture_output=True, text=True, timeout=180)
    return 'noindex' in out.stdout.lower()


def fidelity(pairs, run_id, theme, qa_copy, rundir):
    """One retry with a fresh run id (a reused id replays old verdicts): an image that did not load is a network blip; a real difference fails twice."""
    ok, last = fidelity_once(pairs, run_id, theme, qa_copy, rundir)
    return (ok, last) if ok else fidelity_once(pairs, run_id + '-r2', theme, qa_copy, rundir)


def fidelity_once(pairs, run_id, theme, qa_copy, rundir):
    env = dict(os.environ, JOURNAL_PROFILE=str(GATE_PROFILE))
    env.pop('GATE_QA_COPY', None)
    if qa_copy:
        env['GATE_QA_COPY'] = '1'
    logf = rundir/f'gate-{run_id}.log'
    with logf.open('w') as f:
        code = subprocess.call([PY, '-I', str(SKILL/'fidelity_gate.py'), '--theme', str(theme), '--pairs', str(pairs),
                                '--jobs', '2', '--run-id', run_id], stdout=f, stderr=subprocess.STDOUT, env=env, timeout=3600)
    last = (logf.read_text().strip().splitlines() or [''])[-1]
    return code == 0 and 'GATE: PASS' in last, last


def qa_stage(cmd, rundir, targets=None):
    args = [QA_PY, str(SKILL/'qa_stage.py'), '--profile', str(GATE_PROFILE)] + (['--targets', str(targets)] if targets else []) + [cmd]
    out = subprocess.run(args, cwd=rundir, capture_output=True, text=True, timeout=900)
    (rundir/f'qa-{cmd}.log').write_text(out.stdout + out.stderr)
    require(out.returncode == 0, f'qa_stage {cmd} failed: ' + (out.stdout + out.stderr)[-400:])


def save_ledger(ledger):
    path = STATE/'articles.json'
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(ledger, indent=2) + '\n')
    temp.replace(path)


def next_day(profile):
    """One calendar day per run, the first from today that still has an unpublished auto row (Kevin 2026-10-30).
    "Tomorrow" broke when earlier runs had already published days ahead: 29 and 30 Oct got no new post."""
    open_days = sorted({r['day'] for r in eligible_rows(profile)})
    return open_days[0] if open_days else dt.datetime.now(ICT).date().isoformat()


LOW_ROWS = 14  # two days at daily_volume 7


def eligible_rows(profile, today=None):
    """Unpublished approval=auto calendar rows from today on: the work the runner can still publish."""
    today = today or dt.datetime.now(ICT).date().isoformat()
    ledger_path = STATE/'articles.json'
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    rows = csv.DictReader(profile.read_context(profile.data['calendar']).splitlines())
    return [r for r in rows if r['day'] >= today and r['approval'] == 'auto'
            and not ledger.get(r['uniqueness_key'], {}).get('published')]


def incident(kind, shortfall, cause, action, checkpoint='next run 07:45 ICT (catch-up 09:45)'):
    """One Lark message per kind per ICT day through the existing GenSEO bot. Never raises."""
    try:
        subprocess.run(['/bin/bash', str(ROOT/'scripts'/'notify_lark.sh'), '--incident', 'cherish', kind,
                        shortfall, cause, action, checkpoint], timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        log('incident not sent:', error)


def queue_check(profile):
    n = len(eligible_rows(profile))
    if n < LOW_ROWS:
        incident('queue-empty' if n == 0 else 'queue-low', f'{n} eligible calendar rows < {LOW_ROWS} (2 days at 7/day)',
                 'calendar.csv has too few unpublished approval=auto rows', 'add researched rows to genseo-400/calendar.csv')
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--day', default=None, help='Calendar day; default = first day from today with an unpublished auto row')
    ap.add_argument('--skip-generate', action='store_true', help='Gate and publish rows already held (no writer call)')
    args = ap.parse_args(argv)
    started = dt.datetime.now(ICT)
    profile = Profile('cherish')
    if args.day is None:
        # One publishing day per calendar day: the 09:45 catch-up only runs when 07:45 published nothing.
        report = WORK/'daily'/f'{started.date().isoformat()}.md'
        if report.exists() and re.search(r'· published: [1-9]', report.read_text()):
            log('already published today, skip'); return 0
        args.day = next_day(profile)
    require(profile.credential_domain() == 'uxfaue-s1.myshopify.com', 'Not the Cherish store')
    rows = [r for r in profile.calendar(args.day) if r['approval'] == 'auto']
    rundir = WORK/'genseo-auto/runs'/f"{args.day}-{started:%H%M}"
    rundir.mkdir(parents=True, exist_ok=True)
    notes, results = [], []
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE/'auto.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise StoreGuardError('Another Cherish auto run is active')
        log('day', args.day, 'auto rows', len(rows))
        if rows and not args.skip_generate:
            try:
                code = run_store.main(['--store', 'cherish', '--day', args.day, '--apply', '--generate', '--hold'])
                log('run_store exit', code)
            except StoreGuardError as error:
                notes.append(f'run_store stopped: {error}')
        from store_publisher import Shopify
        api = Shopify(profile)
        api.identity()
        main_theme = next(t['id'] for t in api.request('/admin/api/2026-04/themes.json')['themes'] if t['role'] == 'main')
        ledger = json.loads((STATE/'articles.json').read_text())
        topics = {r['uniqueness_key']: r for r in rows}
        held = {t: e for t, e in ledger.items() if t in topics and e.get('held') and not e['published'] and 'gate' not in e}
        domain, blog = profile.data['domain'], profile.data['blog_handle']
        if held:
            ok, last = fidelity_selftest(rundir)
            if not ok:
                notes.append('Fidelity gate selftest failed, nothing published: ' + last)
                held = {}
        targets = {e['handle']: str(e['id']) for e in held.values()}
        passed = {}
        if targets:
            (rundir/'targets.json').write_text(json.dumps(targets, indent=1))
            try:
                qa_stage('create', rundir, rundir/'targets.json')
                for topic, e in held.items():
                    row = topics[topic]
                    package = json.loads((ROOT/'stores/cherish/drafts'/f"{row['day']}-{row['slot']}.json").read_text())
                    template, _ = profile.template(row['style'])
                    tpl = rundir/f"style-{row['style']}-{e['handle']}.html"
                    tpl.write_text(gate_page(package['body_html'], template))
                    qa_url = f"https://{domain}/blogs/{profile_gate()['qa_blog_handle']}/{e['handle']}"
                    if not noindex(qa_url):
                        e['gate'] = 'FAIL: QA copy is not noindex in Chrome'
                        continue
                    pairs = rundir/f"qa-{e['handle']}.json"
                    pairs.write_text(json.dumps([{'style': row['style'], 'slug': e['handle'], 'tpl': str(tpl),
                                                  'live_url': qa_url + '?preview_theme_id={theme}'}], indent=1))
                    ok, last = fidelity(pairs, f"auto-{args.day}-{row['slot']}-{started:%H%M}-qa", main_theme, True, rundir)
                    e['gate_run'] = f"auto-{args.day}-{row['slot']}-{started:%H%M}-qa"
                    log('gate', row['slot'], e['handle'], last)
                    if ok:
                        passed[topic] = tpl
                    else:
                        e['gate'] = 'FAIL: ' + last
            finally:
                qa_stage('delete', rundir)
        for topic, tpl in passed.items():
            e, row = held[topic], topics[topic]
            path = f"/admin/api/2026-04/blogs/{api.blog()}/articles/{e['id']}.json"
            url = f"https://{domain}/blogs/{blog}/{e['handle']}"
            try:
                api.request(path, {'article': {'id': e['id'], 'published': True}}, method='PUT')
                require(bool(api.request(path)['article'].get('published_at')), 'Publication status readback failed')
                pairs = rundir/f"live-{e['handle']}.json"
                pairs.write_text(json.dumps([{'style': row['style'], 'slug': e['handle'], 'tpl': str(tpl), 'url': url}], indent=1))
                ok, last = fidelity(pairs, f"auto-{args.day}-{row['slot']}-{started:%H%M}-live", main_theme, False, rundir)
                log('post-publish gate', row['slot'], e['handle'], last)
            except run_store.ROW_ERRORS as error:
                ok, last = False, f'publish step error: {error}'
            if ok:
                e.update(gate='PASS', published=True, url=url, published_on=dt.datetime.now(ICT).isoformat(timespec='seconds'))
            else:
                api.request(path, {'article': {'id': e['id'], 'published': False}}, method='PUT')
                require(not api.request(path)['article'].get('published_at'), 'Unpublish readback failed for ' + str(e['id']))
                e['gate'] = 'FAIL after publish (unpublished again): ' + last
        ledger.update(held)
        save_ledger(ledger)
        for topic, row in sorted(topics.items(), key=lambda kv: int(kv[1]['slot'])):
            results.append((row, ledger.get(topic)))
        failures = [json.loads(l) for l in (STATE/'failures.jsonl').read_text().splitlines()] if (STATE/'failures.jsonl').exists() else []
        failures = {f['slot']: f['error'] for f in failures if f['day'] == args.day and f['at'] >= started.isoformat(timespec='seconds')}
        write_daily(args.day, started, results, failures, notes, rundir)
    pub = sum(1 for _, e in results if e and e.get('published'))
    if rows and not pub:
        incident('batch-failed', f'0/{len(rows)} posts published for calendar day {args.day}',
                 '; '.join(notes)[:300] or 'every row failed a gate (see daily list)',
                 f'read {WORK}/daily/{started.date().isoformat()}.md and {rundir}')
    queue_check(profile)
    return 0 if all(e and e.get('published') for _, e in results) and not notes else 2


def profile_gate():
    return json.loads(GATE_PROFILE.read_text())


def fidelity_selftest(rundir):
    ok, last = selftest_once(rundir)
    return (ok, last) if ok else selftest_once(rundir)   # one retry: a control that fails on an unloaded image is a network blip


def selftest_once(rundir):
    env = dict(os.environ, JOURNAL_PROFILE=str(GATE_PROFILE))
    env.pop('GATE_QA_COPY', None)
    logf = rundir/'gate-selftest.log'
    with logf.open('w') as f:
        code = subprocess.call([PY, '-I', str(SKILL/'fidelity_gate.py'), '--selftest'], stdout=f, stderr=subprocess.STDOUT,
                               env=env, timeout=3600, cwd=rundir)
    last = (logf.read_text().strip().splitlines() or [''])[-1]
    return code == 0, last


def write_daily(day, started, results, failures, notes, rundir):
    out = WORK/'daily'/f'{started.date().isoformat()}.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    pub = [(r, e) for r, e in results if e and e.get('published')]
    lines = [f'# Cherish Journal auto-publish — {started.date().isoformat()}', '',
             f'Calendar day {day} · approval=auto rows: {len(results)} · published: {len(pub)} · job `com.pati.genseo-cherish` · run `{rundir}`', '',
             '## Published', '']
    lines += [f"{i}. [{r['primary_keyword']}]({e['url']}) (slot {r['slot']}, style {r['style']})" for i, (r, e) in enumerate(pub, 1)] or ['None.']
    lines += ['', '## Not published (left unpublished, needs a look)', '']
    rest = []
    for r, e in results:
        if e and e.get('published'):
            continue
        why = (e or {}).get('gate') or failures.get(r['slot']) or ('held, not gated' if e else 'not written')
        admin = f" · [admin](https://admin.shopify.com/store/uxfaue-s1/content/articles/{e['id']})" if e else ''
        rest.append(f"- slot {r['slot']} `{r['primary_keyword']}`{admin}: {why}")
    lines += rest or ['None.']
    if notes:
        lines += ['', '## Run notes', ''] + [f'- {n}' for n in notes]
    text = '\n'.join(lines) + '\n'
    out.write_text((out.read_text() + '\n---\n\n' if out.exists() else '') + text)
    log('daily list', out)


def blocked(error):
    """A run that stops before its daily list: one incident, exit 1. A renamed approved input is 'missing-source'."""
    print('Cherish auto blocked:', str(error), file=sys.stderr)
    kind = 'missing-source' if 'Missing approved input' in str(error) else 'batch-failed'
    incident(kind, 'batch did not start or stopped early', str(error)[:300],
             'fix the named input or guard, then rerun scripts/cherish_auto.py')
    return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (StoreGuardError, subprocess.SubprocessError, OSError, json.JSONDecodeError) as error:
        sys.exit(blocked(error))

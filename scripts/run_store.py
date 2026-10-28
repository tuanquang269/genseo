#!/usr/bin/env python3
"""Explicit-store runner. Dry runs never call an AI model or write to Shopify."""
import argparse
import datetime as dt
import fcntl
import hashlib
import html
import http.client
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

from store_profiles import Profile, StoreGuardError, ROOT, require
from store_article import prepare_html, validate_schema, soup


def norm(text):
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def read_package(path, profile, row, live_products=None):
    package = json.loads(path.read_text())
    for key, value in [('store', profile.store), ('day', row['day']), ('slot', row['slot'])]:
        require(str(package.get(key)) == value, 'Article package identity mismatch: '+key)
    require(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', package.get('handle', '')), 'Invalid article handle')
    require(1 <= len(package.get('title', '')) <= 60, 'Title must be 1–60 characters')
    require(120 <= len(package.get('meta_description', '')) <= 165, 'Meta description must be 120–165 characters')
    body = package.get('body_html', '')
    profile.check_text(' '.join(str(package.get(k,'')) for k in ('title','meta_description','body_html')))
    require('<article' in body and 'application/ld+json' in body, 'Full template and JSON-LD are required')
    require(not re.search(r'<script(?![^>]*type=[\'"]application/(?:ld\+json|json)[\'"])[^>]*>', body, re.I), 'Executable script is not allowed')
    require(not re.search(r'\son\w+\s*=|javascript:', body, re.I), 'Executable HTML is not allowed')
    parsed = soup(body)
    require(not parsed.select('iframe, object, embed, form, link[rel="stylesheet"]'), 'Unapproved embedded content')
    for node in parsed.select('[href], [data-product]'):
        if node.has_attr('href'):
            profile.check_text(html.unescape(node['href']))
        if node.has_attr('data-product'):
            profile.check_handle(node['data-product'])
    template, rules = profile.template(row['style'])
    match = re.search(r'<script[^>]*id="rules-machine"[^>]*>(.*?)</script>', body, re.S)
    require(match is not None and json.loads(match.group(1)) == rules, 'Article changed approved template rules')
    require(not re.search(r'clinically proven|cures? insomnia|softer every wash|softer by day 100|\bluxury\b', body, re.I), 'Unsupported or banned claim')
    package['raw_html'], package['style'], package['keyword'] = body, row['style'], row['primary_keyword']  # journal-v1 reads the full page; prepare_html strips the sticky bar
    body = prepare_html(body, template)
    package['body_html'] = body
    validate_schema(body, package, profile)
    facts = package.get('facts', [])
    require(isinstance(facts, list) and facts, 'Fact-check evidence is required')
    plain = html.unescape(re.sub(r'<[^>]*>', ' ', body))
    for fact in facts:
        require(set(('claim','source','quote')) <= fact.keys(), 'Fact evidence is incomplete')
        require(fact['claim'] and norm(fact['claim']) in norm(plain), 'Fact claim is absent from the article')
        source = fact['source']
        live_sources = {f"shopify://{profile.data['shop']}/products/{h}": product
                        for h,product in (live_products or {}).items()}
        if source in live_sources:
            evidence = html.unescape(re.sub(r'<[^>]*>', ' ', json.dumps(live_sources[source],ensure_ascii=False)))
        elif source in profile.data['context'] or source == profile.data['registry']:
            evidence = profile.read_context(source)
        else:
            require(source in row['evidence_urls'].split('|'), 'Unapproved fact source')
            with urllib.request.urlopen(urllib.request.Request(source, headers={'User-Agent':'GenSEO/1.0 fact-check'}), timeout=40) as res:
                evidence = res.read(4_000_000).decode('utf-8', errors='replace')
            evidence = html.unescape(re.sub(r'<[^>]*>', ' ', evidence))
        require(len(fact['quote']) >= 12 and norm(fact['quote']) in norm(evidence), 'Fact quote is not in its source')
    # Numerical body claims must be explicitly listed, including prices and dimensions.
    article = re.search(r'<article\b[^>]*>(.*?)</article>', body, re.S)
    require(article is not None, 'Article body missing')
    prose = re.sub(r'<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>', '', article.group(1), flags=re.S)
    prose = html.unescape(re.sub(r'<[^>]*>', ' ', prose))
    for sentence in re.split(r'[.!?\n]', prose):
        sentence = ' '.join(sentence.split())
        if re.search(r'\d', sentence):
            require(any(norm(sentence) in norm(f['claim']) or norm(f['claim']) in norm(sentence) for f in facts), 'Numerical claim lacks fact evidence')
    return package


def render_gate(profile, package, row, directory):
    # check.py runs machine rules only for style-* filenames. Never skip that branch.
    path = directory / f"style-{row['style']}-{row['day']}-{row['slot']}.html"
    path.write_text(package['body_html'])
    gate = profile.data['gates'][0]
    done = subprocess.run([sys.executable, gate, str(path)], capture_output=True, text=True, timeout=300)
    sys.stdout.write(done.stdout)
    require(done.returncode == 0, 'Render gate (check.py) failed: ' + (done.stdout + done.stderr)[-1500:])


def duplicate_guard(package, row, existing):
    title = set(norm(package['title']).split())
    for article in existing:
        other = set(norm(article.get('title','')).split())
        overlap = len(title & other) / max(1, len(title | other))
        require(package['handle'] != article['handle'] and norm(package['title']) != norm(article.get('title','')) and overlap < 0.85,
                'Duplicate or near-duplicate topic already exists (including unpublished drafts)')
        require(norm(row['primary_keyword']) != norm(article.get('title','')), 'Keyword already covered')


ROUTER = 'https://ai.patigroup.com/v1/messages'  # Fixed OAuth router host. Never a local router, the Railway app, or a per-token AI API.


class RouterRetry(Exception):
    pass


def read_stream(lines):
    """Anthropic SSE lines -> (text, stop_reason). A stream that ends without message_stop is incomplete."""
    text, stop, done = [], None, False
    for raw in lines:
        line = raw.decode('utf-8') if isinstance(raw, bytes) else raw
        if not line.startswith('data:'):
            continue
        event = json.loads(line[5:])
        kind = event.get('type')
        if kind == 'content_block_delta' and event['delta'].get('type') == 'text_delta':
            text.append(event['delta']['text'])
        elif kind == 'message_delta':
            stop = event['delta'].get('stop_reason') or stop
        elif kind == 'message_stop':
            done = True
        elif kind == 'error':
            raise RouterRetry('Writer stream error: ' + json.dumps(event.get('error'))[:300])
    if not done:
        raise RouterRetry('Writer stream ended early')
    return ''.join(text), stop


def router_call(payload, key, attempts=4, wait=20):
    """Stream the reply. Cloudflare in front of the router ends a request with HTTP 524 when no byte arrives for 100 s
    (00.6-mistakes 2026-10-15); a full article takes minutes, a stream sends bytes from the first second.
    Retries 429, 5xx (524 included), network errors and broken streams with backoff."""
    body = json.dumps(dict(payload, stream=True)).encode()
    headers = {'Authorization': 'Bearer '+key, 'x-api-key': key, 'anthropic-version': '2023-06-01',
               'Content-Type': 'application/json', 'Accept': 'text/event-stream', 'User-Agent': 'curl/8.7.1'}
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(ROUTER, data=body, headers=headers), timeout=300) as response:
                return read_stream(response)
        except urllib.error.HTTPError as error:
            if error.code != 429 and error.code < 500:
                raise StoreGuardError(f'Writer request refused: HTTP {error.code}')
            reason = f'HTTP {error.code}'
        except (RouterRetry, urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as error:
            reason = str(error)[:200]
        print(f'Writer attempt {attempt}/{attempts} failed: {reason}', file=sys.stderr)
        if attempt < attempts:
            time.sleep(wait * 2 ** (attempt - 1))
    raise StoreGuardError('Writer unavailable after retries: ' + reason)


def router_key():
    env = {}
    for line in Path('/Users/kevinkreative/PATI/LLM-Wiki/.env').read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=',1)
            env[k.strip().removeprefix('export ')] = v.strip().strip('"').strip("'")
    key = os.environ.get('NINE_ROUTER_KEY') or env.get('NINE_ROUTER_KEY')
    require(bool(key), 'OAuth router key is unavailable')
    return key


def fetch_evidence(row):
    """Readable evidence pages only. A blocked page (403, 429) is listed so the writer does not cite it."""
    evidence, unreadable = {}, []
    for source in row['evidence_urls'].split('|'):
        try:
            with urllib.request.urlopen(urllib.request.Request(source, headers={'User-Agent':'GenSEO/1.0 evidence'}), timeout=40) as response:
                raw = response.read(4_000_000).decode('utf-8', errors='replace')
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException):
            unreadable.append(source)
            continue
        raw = re.sub(r'<(?:script|style)\b[^>]*>.*?</(?:script|style)>', '', raw, flags=re.S)
        evidence[source] = html.unescape(re.sub(r'<[^>]*>', ' ', raw))[:30000]
    return evidence, unreadable


def stem(url):
    return re.sub(r'\.\w+$', '', (url or '').split('?')[0].rsplit('/', 1)[-1])


def pick_hero(api, row, articles, budget):
    """First photo of the target product that no Journal article uses as its hero and that fits the hero budget at width 1100.
    ponytail: no automatic hero set; a product with only heavy unused photos fails the row (build a set by hand, hero_budget.py)."""
    from journal_fields import served_kb
    used = {stem((a.get('image') or {}).get('src')) for a in articles}
    product = api.product(row['target_product_handle'])
    for image in product.get('images', []):
        if stem(image['src']) in used:
            continue
        if not budget or served_kb(image['src']) <= int(budget):
            return {'src': image['src'], 'alt': image.get('alt') or 'The Cherish Company — ' + product['title']}
    raise StoreGuardError('No unused hero photo within the hero budget for ' + row['target_product_handle'])


def finalize_page(page, template, row, package, hero, day):
    """Machine-owned values the shell prints from metafields: hero tag, Updated date, and the BlogPosting fields
    (image, dates, description, wordCount, about). The writer cannot count words; the runner can."""
    from journal_fields import count_words, plain
    approved = soup(template).select_one('figure.hero img')
    src = hero['src']
    tag = (f'<img src="{src}&width=1100" srcset="' + ', '.join(f'{src}&width={w} {w}w' for w in (550, 750, 1100, 2200)) +
           f'" sizes="{approved["sizes"]}" width="{approved["width"]}" height="{approved["height"]}" alt="{html.escape(hero["alt"])}"' +
           (' fetchpriority="high"' if approved.has_attr('fetchpriority') else '') + '>')
    page, n = re.subn(r'(<figure class="hero">\s*)<img\b[^>]*>', lambda m: m.group(1) + tag, page, count=1)
    require(n == 1, 'Hero figure is missing')
    human = f'{day:%b} {day.day}, {day.year}'
    page, n = re.subn(r'(<p class="meta">.*?<span>)Updated [^<]*(</span>)', lambda m: m.group(1) + 'Updated ' + human + m.group(2), page, count=1, flags=re.S)
    require(n == 1, 'Updated date is missing from the meta row')
    article = page[page.index('<article'):page.index('</article>')]
    match = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', page, re.S)
    require(match is not None, 'JSON-LD is missing')
    graph = json.loads(match.group(2))
    post = next(n for n in graph['@graph'] if n.get('@type') == 'BlogPosting')
    post.update({'headline': package['title'], 'description': package['meta_description'], 'image': src.split('?')[0],
                 'datePublished': day.isoformat(), 'dateModified': day.isoformat(),
                 'about': plain(row['primary_keyword']), 'wordCount': count_words(article)})
    return page[:match.start(2)] + json.dumps(graph, ensure_ascii=False) + page[match.end(2):]


WRITER_RULES = """
WRITER RULES (the runner gates every one; a failure returns here with the error):
- Fill the approved template. Keep every element, class, id and order. Replace only the text, links, product cards and FAQ. Delete the .preview bar, every .spec / .spec-sec annotation and every executable script. Keep the <!-- Approved CSS is inserted by the runner. --> comment where it is.
- Hero: keep <figure class="hero"><img ...> with the alt text you see; the runner sets the hero photo, the BlogPosting image, dates, wordCount and about.
- Date: write "Updated {human}" in the meta row and {iso} for datePublished and dateModified.
- Every digit inside <article> must be in a sentence that a facts item covers (claim text appears in that sentence). Write offer, guarantee, shipping and competitor numbers as words. Use digits only for product facts the LIVE PRODUCT FACTS prove (prices as $NN.NN or $NN exactly as a variant price).
- Every facts item: claim = an exact phrase from the article; source = an evidence URL from SOURCE EVIDENCE, an approved context path, or shopify://<shop>/products/<handle> for a supplied live product; quote = 12+ characters copied exactly from that source text.
- Do not cite or link the UNREADABLE SOURCES. Every product link and data-product handle is an allowed product handle. Product card prices equal a current variant price.
- Hit every #rules-machine limit (words, h2, question h2, cards, images, authority links, Journal links, table, rows, sources). Title and H1 are equal and at most 60 characters. Meta description 120 to 165 characters.
- No ratings, review counts, or our own reviews. No health, cure, certification or "luxury" claims.
"""


def generate(profile, row, path, live_products, hero, day, feedback=None):
    """Use the existing OAuth-backed hosted router. No tools, skills, or global context."""
    key = router_key()
    evidence, unreadable = fetch_evidence(row)
    prompt = profile.prompt(row) + '\nLIVE PRODUCT FACTS:\n' + json.dumps(live_products, ensure_ascii=False)
    prompt += '\nSOURCE EVIDENCE:\n' + json.dumps(evidence, ensure_ascii=False)
    prompt += '\nUNREADABLE SOURCES (do not cite):\n' + json.dumps(unreadable)
    prompt += '\nHERO PHOTO (runner-owned):\n' + json.dumps(hero, ensure_ascii=False)
    prompt += WRITER_RULES.format(human=f'{day:%b} {day.day}, {day.year}', iso=day.isoformat())
    if feedback:
        prompt += '\nYOUR PREVIOUS PACKAGE FAILED THIS GATE. Fix it and return a complete new package:\n' + feedback[:4000]
    prompt += '\nReturn only the JSON package. No code fences. Remove preview controls, spec annotations, and executable scripts. Keep the full HTML document for the render gate. The publisher extracts the article fragment.'
    payload = {'model': profile.data['writer_model'], 'max_tokens':32000,
               'messages':[{'role':'user','content': prompt}]}
    text, stop = router_call(payload, key)
    require(stop == 'end_turn', 'Writer response is incomplete')
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip())
    package = json.loads(text)
    require(package.get('store') == profile.store, 'Writer returned the wrong store')
    template, _ = profile.template(row['style'])
    package['body_html'] = finalize_page(package['body_html'], template, row, package, hero, day)
    path.write_text(json.dumps(package, ensure_ascii=False, indent=2)+'\n')


ROW_ERRORS = (StoreGuardError, subprocess.SubprocessError, OSError, json.JSONDecodeError, KeyError, ValueError)


def check_package(api, profile, row, path, existing, state):
    candidate = json.loads(path.read_text())
    profile.check_text(candidate.get('body_html',''))
    handles = {row['target_product_handle']} | profile.linked_handles(candidate.get('body_html',''))
    live_products = {h:api.product(h) for h in handles}
    package = read_package(path, profile, row, live_products)
    duplicate_guard(package, row, existing)
    # Each own-product card uses that product's current variant prices.
    for card in soup(package['body_html']).select('[data-product]'):
        handle = card['data-product']
        if handle not in live_products:
            live_products[handle] = api.product(handle)
        prices = {str(v['price']) for v in live_products[handle]['variants']}
        for price in re.findall(r'\$\s*(\d+\.\d{2})', card.get_text(' ',strip=True)):
            require(price in prices, 'Product card price is not current')
    render_gate(profile, package, row, state)
    return package


def prepare_row(api, profile, row, path, existing, state, generate_on, attempts=3):
    """Gate a package. With --generate and no package on disk, write it and send each gate failure back to the writer (max `attempts`).
    A package that never passes is moved to <name>.failed.json so a rerun writes a fresh one."""
    if not (generate_on and not path.exists()):
        require(path.is_file(), 'Missing article package: '+str(path))
        return check_package(api, profile, row, path, existing, state)
    template, _ = profile.template(row['style'])
    handles = {row['target_product_handle']} | profile.linked_handles(template)
    live_products = {h: api.product(h) for h in handles}
    hero = pick_hero(api, row, existing, profile.data.get('hero_budget_kb'))
    day = dt.datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).date()
    feedback = None
    for attempt in range(1, attempts + 1):
        try:
            generate(profile, row, path, live_products, hero, day, feedback)
            return check_package(api, profile, row, path, existing, state)
        except ROW_ERRORS as error:
            feedback = f'{type(error).__name__}: {error}'
            print(f"Slot {row['slot']} attempt {attempt}/{attempts} failed: {feedback[:300]}", file=sys.stderr)
            if attempt == attempts:
                if path.exists():
                    path.replace(path.with_suffix('.failed.json'))
                raise


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--store', required=True, choices=['wellnessnest','cherish'])
    ap.add_argument('--day', default=dt.datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).date().isoformat())
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--print-prompt', action='store_true')
    ap.add_argument('--slot')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--generate', action='store_true', help='Use the OAuth router to write missing packages; requires --apply')
    ap.add_argument('--packages-dir', type=Path)
    ap.add_argument('--hold', action='store_true', help='Create approval=auto rows unpublished for the fidelity gate (cherish_auto.py publishes); a failed row is recorded, the rest continue')
    args = ap.parse_args(argv)
    profile = Profile(args.store)
    profile.credential_domain()
    require(not args.generate or args.apply, '--generate requires --apply')
    require(not args.hold or args.apply, '--hold requires --apply')
    require(not args.apply or not (args.dry_run or args.print_prompt), 'Preview flags cannot be combined with --apply')
    if args.store == 'wellnessnest':
        require(not args.generate and not args.packages_dir and not args.hold, 'Legacy Wellness Nest keeps its own writer and queues')
        env = dict(os.environ, GENSEO_STORE='wellnessnest')
        command = ['bash', profile.data['legacy_runner']]
        if args.dry_run or args.print_prompt or not args.apply:
            command.append('--print-prompt')
        return subprocess.call(command, env=env)
    rows = profile.calendar(args.day)
    if args.slot:
        rows = [r for r in rows if r['slot'] == args.slot]
        require(bool(rows), 'No calendar row for this slot')
    if args.print_prompt:
        require(len(rows) == 1, '--print-prompt requires a single --slot')
        print(profile.prompt(rows[0]))
        return 0
    print(json.dumps({'store':args.store,'shop':profile.data['shop'],'blog':profile.data['blog_handle'],
                      'day':args.day,'daily_volume':profile.data['daily_volume'],
                      'rows':[{'slot':r['slot'],'style':r['style'],'approval':r['approval'],'keyword':r['primary_keyword']} for r in rows],
                      'mode':'apply' if args.apply else 'dry-run'},indent=2))
    if not args.apply:
        for row in rows:
            profile.prompt(row)  # Prove all context and template inputs load, without a model.
        return 0
    from store_publisher import Shopify
    state = ROOT/'state'/args.store
    state.mkdir(parents=True, exist_ok=True)
    packages = args.packages_dir or ROOT/'stores'/args.store/'drafts'
    packages.mkdir(parents=True, exist_ok=True)
    with (state/'daily.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise StoreGuardError('Another run for this store is active')
        ledger_path = state/'articles.json'
        ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
        api = Shopify(profile)
        api.identity()
        blog = api.blog()
        existing = api.articles(blog)
        failures = []
        for row in rows:
            topic = row['uniqueness_key']
            if topic in ledger:
                print('Already completed:', topic)
                continue
            path = packages/f"{row['day']}-{row['slot']}.json"
            try:
                package = prepare_row(api, profile, row, path, existing, state, args.generate)
                # Refresh just before the write so a peer's draft also prevents a duplicate.
                duplicate_guard(package, row, api.articles(blog))
                live = row['approval'] == 'auto' and not args.hold
                result = api.publish(package, blog, live)
            except ROW_ERRORS as error:
                if not args.hold:
                    raise
                # --hold: one failed row never stops the day. The row stays unwritten or unpublished and goes on the daily list.
                failure = {'event': 'row-failed', 'store': profile.store, 'day': row['day'], 'slot': row['slot'],
                           'keyword': row['primary_keyword'], 'error': f'{type(error).__name__}: {error}'[:600],
                           'at': dt.datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(timespec='seconds')}
                failures.append(failure)
                with (state/'failures.jsonl').open('a') as f:
                    f.write(json.dumps(failure)+'\n')
                print(json.dumps(failure), file=sys.stderr)
                continue
            entry = {'id':result['id'], 'handle':result['handle'], 'published':live,
                     'day':row['day'],'slot':row['slot'],'approval':row['approval'],
                     'profile_sha256':profile.fingerprint(), 'package_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            if args.hold and row['approval'] == 'auto':
                entry['held'] = True   # cherish_auto.py publishes it only after the fidelity gate passes
            ledger[topic] = entry
            temp = ledger_path.with_suffix('.tmp')
            temp.write_text(json.dumps(ledger,indent=2)+'\n'); temp.replace(ledger_path)
            existing.append(result)
            if entry.get('held'):
                print('Held unpublished for the fidelity gate:', result['id'], result['handle'])
            elif not live:
                # Local review notification. launchd stdout is also captured in the review log.
                notice = {'event':'kevin-review-required','store':profile.store, **entry,
                          'admin_url':f"https://{profile.data['shop']}/admin/articles/{result['id']}"}
                with (state/'review-notifications.jsonl').open('a') as f:
                    f.write(json.dumps(notice)+'\n')
                print(json.dumps(notice))
            else:
                print('Published:', f"https://{profile.data['domain']}/blogs/{profile.data['blog_handle']}/{result['handle']}")
        if failures:
            return 2
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (StoreGuardError, subprocess.SubprocessError, OSError, json.JSONDecodeError) as error:
        print('GenSEO blocked:', str(error), file=sys.stderr)
        sys.exit(1)

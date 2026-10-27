#!/usr/bin/env python3
"""Explicit-store runner. Dry runs never call an AI model or write to Shopify."""
import argparse
import datetime as dt
import fcntl
import hashlib
import html
import json
import os
import re
import subprocess
import sys
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
    subprocess.run([sys.executable, gate, str(path)], check=True, timeout=300)


def duplicate_guard(package, row, existing):
    title = set(norm(package['title']).split())
    for article in existing:
        other = set(norm(article.get('title','')).split())
        overlap = len(title & other) / max(1, len(title | other))
        require(package['handle'] != article['handle'] and norm(package['title']) != norm(article.get('title','')) and overlap < 0.85,
                'Duplicate or near-duplicate topic already exists (including unpublished drafts)')
        require(norm(row['primary_keyword']) != norm(article.get('title','')), 'Keyword already covered')


def generate(profile, row, path, live_products):
    """Use the existing OAuth-backed hosted router. No tools, skills, or global context."""
    env = {}
    for line in Path('/Users/kevinkreative/PATI/LLM-Wiki/.env').read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=',1)
            env[k.strip().removeprefix('export ')] = v.strip().strip('"').strip("'")
    key = os.environ.get('NINE_ROUTER_KEY') or env.get('NINE_ROUTER_KEY')
    require(bool(key), 'OAuth router key is unavailable')
    # Fixed host. Never use a local router, the Railway app, or a per-token AI API.
    evidence = {}
    for source in row['evidence_urls'].split('|'):
        with urllib.request.urlopen(urllib.request.Request(source, headers={'User-Agent':'GenSEO/1.0 evidence'}), timeout=40) as response:
            raw = response.read(4_000_000).decode('utf-8', errors='replace')
        raw = re.sub(r'<(?:script|style)\b[^>]*>.*?</(?:script|style)>', '', raw, flags=re.S)
        evidence[source] = html.unescape(re.sub(r'<[^>]*>', ' ', raw))[:30000]
    prompt = profile.prompt(row) + '\nLIVE PRODUCT FACTS:\n' + json.dumps(live_products, ensure_ascii=False)
    prompt += '\nSOURCE EVIDENCE:\n' + json.dumps(evidence, ensure_ascii=False)
    prompt += '\nReturn only the JSON package. No code fences. Remove preview controls, spec annotations, and executable scripts. Keep the full HTML document for the render gate. The publisher extracts the article fragment.'
    payload = {'model': profile.data['writer_model'], 'max_tokens':24000,
               'messages':[{'role':'user','content': prompt}]}
    req = urllib.request.Request('https://ai.patigroup.com/v1/messages', data=json.dumps(payload).encode(),
                                headers={'Authorization':'Bearer '+key, 'x-api-key':key,
                                         'anthropic-version':'2023-06-01','Content-Type':'application/json','User-Agent':'curl/8.7.1'})
    with urllib.request.urlopen(req, timeout=600) as response:
        out = json.load(response)
    require(out.get('stop_reason') == 'end_turn', 'Writer response is incomplete')
    text = ''.join(b.get('text','') for b in out['content'] if b['type']=='text').strip()
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text)
    package = json.loads(text)
    require(package.get('store') == profile.store, 'Writer returned the wrong store')
    path.write_text(json.dumps(package, ensure_ascii=False, indent=2)+'\n')


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
    args = ap.parse_args(argv)
    profile = Profile(args.store)
    profile.credential_domain()
    require(not args.generate or args.apply, '--generate requires --apply')
    require(not args.apply or not (args.dry_run or args.print_prompt), 'Preview flags cannot be combined with --apply')
    if args.store == 'wellnessnest':
        require(not args.generate and not args.packages_dir, 'Legacy Wellness Nest keeps its own writer and queues')
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
        for row in rows:
            topic = row['uniqueness_key']
            if topic in ledger:
                print('Already completed:', topic)
                continue
            path = packages/f"{row['day']}-{row['slot']}.json"
            if not path.exists() and args.generate:
                template, _ = profile.template(row['style'])
                handles = {row['target_product_handle']} | profile.linked_handles(template)
                live_products = {h: api.product(h) for h in handles}
                generate(profile, row, path, live_products)
            require(path.is_file(), 'Missing article package: '+str(path))
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
            # Refresh just before the write so a peer's draft also prevents a duplicate.
            duplicate_guard(package, row, api.articles(blog))
            live = row['approval'] == 'auto'
            result = api.publish(package, blog, live)
            entry = {'id':result['id'], 'handle':result['handle'], 'published':live,
                     'day':row['day'],'slot':row['slot'],'approval':row['approval'],
                     'profile_sha256':profile.fingerprint(), 'package_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            ledger[topic] = entry
            temp = ledger_path.with_suffix('.tmp')
            temp.write_text(json.dumps(ledger,indent=2)+'\n'); temp.replace(ledger_path)
            existing.append(result)
            if not live:
                # Local review notification. launchd stdout is also captured in the review log.
                notice = {'event':'kevin-review-required','store':profile.store, **entry,
                          'admin_url':f"https://{profile.data['shop']}/admin/articles/{result['id']}"}
                with (state/'review-notifications.jsonl').open('a') as f:
                    f.write(json.dumps(notice)+'\n')
                print(json.dumps(notice))
            else:
                print('Published:', f"https://{profile.data['domain']}/blogs/{profile.data['blog_handle']}/{result['handle']}")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (StoreGuardError, subprocess.SubprocessError, OSError, json.JSONDecodeError) as error:
        print('GenSEO blocked:', str(error), file=sys.stderr)
        sys.exit(1)

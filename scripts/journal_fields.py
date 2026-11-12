"""Cherish Journal article contract "journal-v1": body + `journal.*` metafields + template_suffix.

The Liquid shell (templates/article.style-*.json) owns the frame. This module turns an
approved-template post into the three things GenSEO may write:
  body_html       answer box .. end of related/sources. No <style>, <script>, dek, inline TOC, band.
  metafields      13 `journal.*` ARTICLE metafields (schema: blog-templates-liquid-plan-261027 section 6).
  template_suffix `style-<id>`.
Python 3.9 safe. bs4 is imported only by from_document().
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re

from store_profiles import StoreGuardError

NAMESPACE = 'journal'
STYLES = ['1', '2', '3', '4a', '4b', '4c', '4d']
SHIP_LINE_HINT = '100 nights from delivery'  # the band guarantee line is a theme setting, never a metafield


class JournalError(StoreGuardError):  # run_store.py catches StoreGuardError and prints 'GenSEO blocked'
    pass


def need(ok, message):
    if not ok:
        raise JournalError(message)


# key, name, type, description, validations (Shopify names), JSON/text limit used by check()
DEFINITIONS = [
    ('style', 'Journal style', 'single_line_text_field', 'Template style id (1, 2, 3, 4a-4d).',
     [('choices', json.dumps(STYLES, separators=(',', ':')))]),
    ('crumb', 'Journal breadcrumb label', 'single_line_text_field', 'Short breadcrumb label.', [('max', '60')]),
    ('kicker', 'Journal kicker', 'single_line_text_field', 'Small label above the H1.', [('max', '40')]),
    ('dek', 'Journal dek', 'multi_line_text_field', 'One or two sentences under the H1.', [('max', '400')]),
    ('updated_on', 'Journal updated on', 'date', 'Date printed as "Updated Mon D, YYYY".', []),
    ('read_minutes', 'Journal read minutes', 'number_integer', 'Reading time in minutes.',
     [('min', '1'), ('max', '30')]),
    ('meta_note', 'Journal meta note', 'single_line_text_field', 'Last item of the byline row.', [('max', '60')]),
    ('hero_caption', 'Journal hero caption', 'single_line_text_field', 'Figcaption under the hero image.',
     [('max', '160')]),
    ('toc', 'Journal table of contents', 'json', 'JSON [{id, label, rail_label?}]; ids exist in the body.', []),
    ('pick', 'Journal pick', 'json',
     'JSON {handle, image, alt, kicker, title, cta, sticky}; rail card and sticky bar. No price.', []),
    ('band', 'Journal end band', 'json',
     'JSON {h2, p, minis:[{handle,image,alt,title,note,cta}]} or {h2, p, cta:{handle,label}}.', []),
    ('faq', 'Journal FAQ', 'json', 'JSON [{q, a}] plain text; equal to the visible FAQ in the body.', []),
    ('schema_extra', 'Journal extra schema', 'json', 'One schema.org node (ItemList or HowTo). Omitted when none.', []),
]
TYPES = {d[0]: d[2] for d in DEFINITIONS}
KEYS = [d[0] for d in DEFINITIONS]
# Blog-index topic chips (plan part 1, section 8). Tags are controlled: 1-3 values from this list, nothing else.
CHIP_TAGS = ['Hot sleepers', 'Night sweats', 'Care guides', 'Buying guides', 'Comparisons', 'Gift guides']
LIMITS = {'crumb': 60, 'kicker': 40, 'dek': 400, 'meta_note': 60, 'hero_caption': 160}


def plain(text):
    """Visible text of a snippet: tags dropped, entities decoded, whitespace collapsed (NBSP kept)."""
    text = html.unescape(re.sub(r'<[^>]+>', ' ', text or ''))
    return re.sub(r'[ \t\r\n]+', ' ', text).strip()


def norm(text):
    return re.sub(r'\s+', ' ', plain(text)).strip()


# Hero weight budget (A-fix round 4): the hero as Chrome downloads it at width 1100 (WebP) must stay <= HERO_BUDGET_KB, otherwise mobile LCP
# misses 2.5 s. Shopify's CDN re-encodes any transformed width at a fixed high quality, so the lever is a hero SET: one pass-through file per
# srcset width (same photo, same aspect ratio, lighter encode), stored as journal.hero_set. Build one with
# ~/PATI/work/cherish-seo/journal-data/hero_budget.py (build_set) or `convert.py --make-heroes`.
HERO_BUDGET_KB = 120
HERO_SET_KEYS = ('550', '750', '1100', '1200', '2200')


def check_hero_set(hero_set):
    """journal.hero_set = {"550": url, "750": url, "1100": url, "1200": url, "2200": url}: Shopify Files URLs of pass-through files."""
    need(isinstance(hero_set, dict) and set(hero_set) == set(HERO_SET_KEYS), 'journal.hero_set needs exactly the keys ' + ', '.join(HERO_SET_KEYS))
    for k, url in hero_set.items():
        need(re.match(r'https://cdn\.shopify\.com/s/files/.+\.webp(\?v=\d+)?$', str(url)), f'journal.hero_set[{k}] must be a Shopify Files .webp URL')
    return hero_set


def hero_set_from_srcset(srcset):
    """A hero srcset of five pass-through Files URLs (no width parameter, descriptors 550 / 750 / 1100 / 1200 / 2200) is a hero set; any other srcset is not."""
    entries = [e.strip().rsplit(' ', 1) for e in html.unescape(srcset or '').split(', ') if e.strip()]
    found = {w[:-1]: u for u, w in entries if len(entries) == 5 and w.endswith('w') and 'width=' not in u}
    return found if set(found) == set(HERO_SET_KEYS) else None


def served_kb(src, width=1100):
    """The hero as Chrome would download it at `width` (WebP negotiated), in KB. One network GET."""
    import urllib.request
    url = f"{src}{'&' if '?' in src else '?'}width={width}"
    req = urllib.request.Request(url, headers={'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8', 'User-Agent': 'Mozilla/5.0 Chrome/130'})
    return round(len(urllib.request.urlopen(req, timeout=60).read()) / 1024)


def check_hero_weight(kb_at_1100, budget=HERO_BUDGET_KB):
    """kb_at_1100: the hero as served at width 1100 (served_kb)."""
    need(kb_at_1100 <= budget, f'Hero weighs {kb_at_1100} KB at width 1100, over the {budget} KB budget: build a hero set (journal_fields.HERO_BUDGET_KB, journal-data/hero_budget.py)')


def _jd(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


def assemble(body, f, image=None, hero_set=None):
    """body: article body HTML. f: normalised fields. image: {src, alt} of the hero (article.image)."""
    body = body.strip()
    for k in ('style', 'crumb', 'kicker', 'dek', 'updated_on', 'read_minutes', 'meta_note', 'hero_caption',
              'toc', 'pick', 'band', 'faq'):
        need(f.get(k) not in (None, '', []), 'Missing journal field: ' + k)
    need(f['style'] in STYLES, 'Unknown style ' + str(f['style']))
    for k, limit in LIMITS.items():
        need(len(f[k]) <= limit and f[k] == plain(f[k]), f'{k} must be plain text <= {limit} chars')
    need(1 <= int(f['read_minutes']) <= 30, 'read_minutes out of range')
    dt.date.fromisoformat(f['updated_on'])
    need(4 <= len(f['toc']) <= 14, 'toc must hold 4-14 items')
    for item in f['toc']:
        need(set(item) <= {'id', 'label', 'rail_label'} and item['id'] and item['label'], 'Bad toc item')
        need(re.search(r'\bid="%s"' % re.escape(item['id']), body), 'toc id not in body: ' + item['id'])
    need(set(f['pick']) == {'handle', 'image', 'alt', 'kicker', 'title', 'cta', 'sticky'}, 'pick keys')
    need(all(f['pick'].values()), 'pick has an empty value')
    band = f['band']
    need(band.get('h2') and band.get('p'), 'band needs h2 and p')
    need(bool(band.get('minis')) != bool(band.get('cta')), 'band needs minis or cta, not both')
    for mini in band.get('minis') or []:
        need(set(mini) == {'handle', 'image', 'alt', 'title', 'note', 'cta'}, 'mini keys')
    need(len(f['faq']) >= 3 and all(set(x) == {'q', 'a'} for x in f['faq']), 'faq needs 3+ {q,a}')
    check_body(body)
    need([norm(x['q']) for x in f['faq']] == visible_faq(body, 'q') and
         [norm(x['a']) for x in f['faq']] == visible_faq(body, 'a'), 'journal.faq differs from the visible FAQ')
    values = {k: f.get(k) for k in KEYS}
    metafields = []
    for key in KEYS:
        v = values[key]
        if key == 'schema_extra' and v is None:
            continue
        if key == 'read_minutes':
            v = str(int(v))
        elif TYPES[key] == 'json':
            v = _jd(v)
        metafields.append({'namespace': NAMESPACE, 'key': key, 'type': TYPES[key], 'value': v})
    parts = {'body_html': body, 'metafields': metafields, 'template_suffix': 'style-' + f['style']}
    if hero_set:
        parts['metafields'].append({'namespace': NAMESPACE, 'key': 'hero_set', 'type': 'json', 'value': _jd(check_hero_set(hero_set))})
    if image:
        need(image.get('src', '').startswith('https://') and image.get('alt'), 'Hero image needs an https src and alt')
        parts['image'] = image
    return parts


def check_body(body):
    for pattern, why in ((r'<style\b', '<style>'), (r'<script\b', '<script>'), (r'<h1\b', '<h1>'),
                         (r'class="dek"', 'dek'), (r'class="toc inline"|class="toc\b', 'TOC'),
                         (r'<section\b[^>]*class="band"', 'end band'), (r'class="(?:rail|stick)\b', 'rail or sticky bar'),
                         (r'application/ld\+json', 'JSON-LD'), (r'<figure\b[^>]*class="hero"', 'hero')):
        need(not re.search(pattern, body), 'Body must not hold ' + why)
    need(body.startswith('<div class="answer"'), 'Body must start with the short answer box')
    need(re.search(r'class="faq"', body), 'Body must hold the FAQ')


def visible_faq(body, part):
    """Question (summary h3) or answer (div) text of every FAQ item in the body, normalised."""
    block = re.search(r'<div class="faq">(.*)', body, re.S)
    need(block is not None, 'FAQ block missing')
    out = []
    for m in re.finditer(r'<details\b[^>]*>\s*<summary>(.*?)</summary>\s*<div>(.*?)</div>\s*</details>', block.group(1), re.S):
        out.append(norm(m.group(1 if part == 'q' else 2)))
    return out


def parts_to_fields(parts):
    """Inverse of assemble() for the metafields: {key: python value}."""
    out = {}
    for m in parts['metafields']:
        out[m['key']] = json.loads(m['value']) if m['type'] == 'json' else (
            int(m['value']) if m['type'] == 'number_integer' else m['value'])
    return out


def readback_check(parts, body_html, metafields):
    """After a write: body has no CSS/JS/JSON-LD and every journal metafield equals what was written."""
    need(not re.search(r'<style\b|<script\b', body_html or ''), 'Readback body holds <style> or <script>')
    need(norm(body_html) == norm(parts['body_html']), 'Body differs after write')
    got = {(m['namespace'], m['key']): m for m in metafields}
    for m in parts['metafields']:
        row = got.get((m['namespace'], m['key']))
        need(row is not None, 'Metafield missing after write: ' + m['key'])
        # REST returns number_integer values as ints, GraphQL as strings: compare as text
        same = (json.loads(row['value']) == json.loads(m['value'])) if m['type'] == 'json' else str(row['value']) == str(m['value'])
        need(same, 'Metafield differs after write: ' + m['key'])


# ---------------------------------------------------------------- full approved-template document
def toc_items(inline, rail, text):
    """Inline TOC labels; a rail entry whose text differs becomes rail_label (the shell prints it in the rail)."""
    short = {a['href'].lstrip('#'): text(a) for a in rail.select('li a')} if rail is not None else {}
    items = []
    for a in inline.select('li a'):
        item = {'id': a['href'].lstrip('#'), 'label': text(a)}
        if short.get(item['id']) not in (None, item['label']):
            item['rail_label'] = short[item['id']]
        items.append(item)
    return items

def from_document(doc_html, style, keyword=None):
    """Parse the writer's full approved-template page (header, article, rail, band, JSON-LD). keyword adds journal.about; journal.word_count is always added."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(doc_html, 'html.parser')
    art = soup.select_one('.layout article')
    need(art is not None, 'Approved layout is missing')
    toc_node = art.select_one('details.toc.inline')
    need(toc_node is not None, 'Inline TOC is missing')
    # String slice, not bs4 output: the body must keep its exact bytes.
    anchor = doc_html.index('class="toc inline"')
    start = doc_html.index('</details>', anchor) + len('</details>')
    body = doc_html[start:doc_html.index('</article>', start)]
    text = lambda node: norm(node.get_text(' ', strip=True)) if node is not None else ''
    meta = [text(s) for s in art.select('p.meta span')]
    need(len(meta) == 4, 'Meta row must hold 4 items')
    crumb = text(soup.select_one('nav.crumbs')).split('›')[-1].strip()
    graph = []
    for node in soup.select('script[type="application/ld+json"]'):
        graph += json.loads(node.get_text())['@graph']
    faq = [{'q': plain(n['name']), 'a': plain(n['acceptedAnswer']['text'])}
           for n in next(g for g in graph if g['@type'] == 'FAQPage')['mainEntity']]
    extra = [g for g in graph if g['@type'] in ('ItemList', 'HowTo')]
    need(len(extra) <= 1, 'More than one extra schema node')
    pick_node = soup.select_one('aside.rail .pick')
    need(pick_node is not None, 'Rail pick card is missing')
    stick = soup.select_one('.stick b')
    band_node = soup.select_one('section.band')
    need(band_node is not None, 'End band is missing')
    pick = {'handle': handle_of(pick_node.select_one('a.btn')['href']), 'image': bare_image(pick_node.img['src']),
            'alt': html.unescape(pick_node.img['alt']), 'kicker': text(pick_node.select_one('.kicker')),
            'title': text(pick_node.b), 'cta': text(pick_node.select_one('a.btn')),
            'sticky': text(stick) or text(pick_node.b)}
    band = {'h2': text(band_node.h2), 'p': text(band_node.h2.find_next_sibling('p'))}
    minis = band_node.select('.mini')
    if minis:
        band['minis'] = [{'handle': m['data-product'], 'image': bare_image(m.img['src']), 'alt': html.unescape(m.img['alt']),
                          'title': text(m.b), 'note': text(m.span), 'cta': text(m.a)} for m in minis]
    else:
        link = band_node.select_one('a.btn')
        band['cta'] = {'handle': handle_of(link['href']), 'label': text(link)}
    fields = {
        'style': style, 'crumb': crumb, 'kicker': text(art.select_one('p.kicker')), 'dek': text(art.select_one('p.dek')),
        'updated_on': dt.datetime.strptime(meta[1].replace('Updated ', ''), '%b %d, %Y').date().isoformat(),
        'read_minutes': int(meta[2].split()[0]), 'meta_note': 'Facts checked against our product pages' if 'competitor' in meta[3].lower() else meta[3],  # Kevin 11-12: never publish competitor-copy notes
        'hero_caption': text(art.select_one('figure.hero figcaption')),
        'toc': toc_items(toc_node, soup.select_one('aside.rail details.toc'), text),
        'pick': pick, 'band': band, 'faq': faq, 'schema_extra': extra[0] if extra else None}
    hero = art.select_one('figure.hero img')
    need(hero is not None, 'Hero image is missing')
    hero_set = hero_set_from_srcset(hero.get('srcset', ''))
    # with a hero set the article image (social card, fallback) is the largest file of the set, like journal.hero
    src = bare_image(hero_set['2200'] if hero_set else hero['src'])
    parts = assemble(body, fields, {'src': src, 'alt': html.unescape(hero['alt'])}, hero_set)
    parts['metafields'] += optional_fields(doc_html[doc_html.index('<article'):doc_html.index('</article>')], keyword)
    return parts


def handle_of(href):
    m = re.search(r'/products/([a-z0-9-]+)', href)
    need(m is not None, 'Not a product link: ' + href)
    return m.group(1)


def bare_image(src):
    return re.sub(r'&(?:amp;)?width=\d+$', '', src)


def file_name(url):
    """File name of a Shopify CDN URL, query string dropped."""
    return (url or '').split('?')[0].rsplit('/', 1)[-1]


def count_words(article_html):
    """BlogPosting wordCount, same rule as the day-1 builder: article text (header + hero + inline TOC + body), spec labels removed."""
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", plain(re.sub(r'<p class="spec">.*?</p>', '', article_html, flags=re.S))))


def optional_fields(article_html, keyword=None):
    """Optional journal.* keys the shell reads in journal-jsonld: about (the post's primary keyword) and word_count."""
    out = [{'namespace': NAMESPACE, 'key': 'word_count', 'type': 'number_integer', 'value': str(count_words(article_html))}]
    if keyword:
        out.insert(0, {'namespace': NAMESPACE, 'key': 'about', 'type': 'single_line_text_field', 'value': plain(keyword)})
    return out


def hero_field(gid):
    """journal.hero = Files id (MediaImage) of the ORIGINAL hero upload. Shopify re-encodes an article image, so only a Files id gives a
    hero that is byte-equal to the approved template (the shell prints journal.hero, then falls back to article.image)."""
    need(re.fullmatch(r'gid://shopify/MediaImage/\d+', gid or ''), 'journal.hero needs a MediaImage id')
    return {'namespace': NAMESPACE, 'key': 'hero', 'type': 'file_reference', 'value': gid}


# ---------------------------------------------------------------- data rules for the blog index
def check_tags(tags):
    """Controlled tags: 1-3 from CHIP_TAGS (case and spacing ignored). Returns canonical labels."""
    by_key = {re.sub(r'[^a-z]+', '', t.lower()): t for t in CHIP_TAGS}
    out = []
    for tag in tags or []:
        label = by_key.get(re.sub(r'[^a-z]+', '', str(tag).lower()))
        need(label is not None, f'Tag "{tag}" is not in the fixed list: {", ".join(CHIP_TAGS)}')
        if label not in out:
            out.append(label)
    need(1 <= len(out) <= 3, 'An article needs 1-3 tags from the fixed list')
    return out


def check_unique_hero(src, articles):
    """The blog index shows one hero per card. Block a hero whose source file name another article already uses."""
    name = lambda url: re.sub(r'\.\w+$', '', ((url or '').split('?')[0].rsplit('/', 1)[-1]))
    mine = name(src)
    for article in articles:
        other = (article.get('image') or {}).get('src', '')
        need(not mine or name(other) != mine, f"Hero image {mine} is already used by article {article.get('id')}")

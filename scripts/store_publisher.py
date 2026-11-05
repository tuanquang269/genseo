"""Cherish article writes. The legacy Wellness Nest publisher remains separate."""
import importlib.util
import __future__
import json
import re
import time
import urllib.error
import urllib.request
from store_profiles import require
from store_article import article_fragment, validate_schema, soup
import journal_fields


FILES_QUERY = 'query($q:String!){ files(first:5, query:$q){ nodes{ id fileStatus ... on MediaImage{ image{ url } } } } }'


class Shopify:
    def __init__(self, profile):
        require(profile.store in ('cherish', 'southedc'), 'Use the legacy publisher for Wellness Nest')
        self.profile = profile
        profile.credential_domain()
        self.domain = profile.data['shop']
        if profile.store == 'southedc':   # shop-app.py: client-credentials token per store alias
            app = profile.adapter()
            self.auth = type('Auth', (), {'token': staticmethod(lambda live=True: app.token(app.store_id('southedc')))})
            return
        path = profile.data['credential']['adapter']
        spec = importlib.util.spec_from_file_location('cherish_genseo_auth', path)
        self.auth = importlib.util.module_from_spec(spec)
        # macOS /usr/bin/python3 is 3.9. The shared adapter has 3.10 union
        # annotations. Postpone annotations without changing that shared file.
        source = spec.loader.get_source(spec.name)
        exec(compile(source, path, 'exec', flags=__future__.annotations.compiler_flag,
                     dont_inherit=True), self.auth.__dict__)
        self.domain = profile.data['shop']

    def request(self, path, payload=None, method=None):
        require(path.startswith('/admin/api/2026-04/'), 'Unapproved Shopify API path')
        body = json.dumps(payload, ensure_ascii=False) if payload is not None else None
        # Check before token refresh, and again immediately before the article write.
        self.profile.credential_domain()
        if body is not None:
            self.profile.assert_write(self.domain, body)
        token = self.auth.token(live=True)
        if body is not None:
            self.profile.assert_write(self.domain, body)
        request = urllib.request.Request('https://'+self.domain+path,
                   data=body.encode() if body is not None else None,
                   headers={'X-Shopify-Access-Token': token, 'Content-Type': 'application/json'}, method=method)
        for attempt in range(4):   # Shopify rejects a throttled call (HTTP 429) unapplied, so a retry cannot double-write
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    return json.load(response)
            except urllib.error.HTTPError as error:
                if error.code != 429 or attempt == 3:
                    raise
                time.sleep(float(error.headers.get('Retry-After') or 2) * (attempt + 1))

    def identity(self):
        shop = self.request('/admin/api/2026-04/shop.json')['shop']
        require(shop['myshopify_domain'] == self.domain, 'Token belongs to another store')
        require(shop['domain'].removeprefix('www.') == self.profile.data['domain'], 'Storefront domain mismatch')

    def blog(self):
        blogs = self.request('/admin/api/2026-04/blogs.json')['blogs']
        found = [b for b in blogs if b['handle'] == self.profile.data['blog_handle']]
        require(len(found) == 1, 'Blog handle is missing or ambiguous')
        return found[0]['id']

    def articles(self, blog):
        # Includes unpublished articles. A public search misses review drafts.
        results, since = [], 0
        while True:
            batch = self.request(f'/admin/api/2026-04/blogs/{blog}/articles.json?limit=250&since_id={since}')['articles']
            results.extend(batch)
            if len(batch) < 250:
                return results
            next_id = max(int(a['id']) for a in batch)
            require(next_id > since, 'Article pagination did not advance')
            since = next_id

    def product(self, handle):
        self.profile.check_handle(handle)
        rows = self.request('/admin/api/2026-04/products.json?handle='+handle)['products']
        require(len(rows) == 1 and rows[0]['handle'] == handle, 'Product does not exist in this store')
        require(rows[0]['status'] == 'active', 'Product is not active')
        return rows[0]

    def collection(self, handle):
        """A published own-store collection (custom or smart): the live source for offer facts (which styles are in an offer)."""
        require(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', handle) is not None, 'Invalid collection handle')
        for kind in ('custom_collections', 'smart_collections'):
            rows = self.request(f'/admin/api/2026-04/{kind}.json?handle={handle}')[kind]
            if rows and rows[0]['handle'] == handle and rows[0].get('published_at'):
                return {k: rows[0].get(k) for k in ('handle', 'title', 'body_html', 'updated_at')}
        require(False, 'Collection is not published in this store: ' + handle)

    def hero_gid(self, src):
        """Files id (MediaImage) of the hero file named in `src`. Read-only GraphQL query; exactly one READY image must match."""
        name = journal_fields.file_name(src)
        out = self.request('/admin/api/2026-04/graphql.json', {'query': FILES_QUERY, 'variables': {'q': 'filename:' + name}})
        hits = [n for n in out['data']['files']['nodes']
                if n.get('image') and journal_fields.file_name(n['image']['url']) == name and n.get('fileStatus') == 'READY']
        require(len(hits) == 1, f'Hero file {name} must exist once in Shopify Files (journal.hero needs its id)')
        return hits[0]['id']

    def publish_journal(self, package, blog, live):
        """Contract journal-v1: body + journal.* metafields + template_suffix. No CSS, no JSON-LD in the body."""
        parts = journal_fields.from_document(package['raw_html'], package['style'], package.get('keyword'))
        # journal.hero: the original upload from Files, not the re-encoded article.image (the fidelity gate fails on that encode noise)
        parts['metafields'].append(journal_fields.hero_field(self.hero_gid(parts['image']['src'])))
        tags = journal_fields.check_tags(package.get('tags'))
        journal_fields.check_unique_hero(parts['image']['src'], self.articles(blog))
        budget = self.profile.data.get('hero_budget_kb')   # opt-in per store profile (cherish: 120): a hero over budget needs a hero set
        if budget and not any(m['key'] == 'hero_set' for m in parts['metafields']):
            journal_fields.check_hero_weight(journal_fields.served_kb(parts['image']['src']), int(budget))
        self.profile.check_text(' '.join([parts['body_html']] + [m['value'] for m in parts['metafields']]))
        article = {'title': package['title'], 'handle': package['handle'], 'body_html': parts['body_html'],
                   'template_suffix': parts['template_suffix'], 'tags': ', '.join(tags), 'image': parts['image'],
                   'published': False, 'author': self.profile.data['name'],
                   'metafields': [{'namespace': 'global', 'key': 'description_tag',
                                   'value': package['meta_description'], 'type': 'single_line_text_field'}] + parts['metafields']}
        result = self.request(f'/admin/api/2026-04/blogs/{blog}/articles.json', {'article': article})['article']
        path = f"/admin/api/2026-04/blogs/{blog}/articles/{result['id']}.json"
        readback = self.request(path)['article']
        require(readback['handle'] == package['handle'], 'Handle readback failed')
        require(not readback.get('published_at'), 'Article was not created unpublished')
        require(readback.get('template_suffix') == parts['template_suffix'], 'template_suffix readback failed')
        stored = self.request(f"/admin/api/2026-04/articles/{result['id']}/metafields.json")['metafields']
        journal_fields.readback_check(parts, readback['body_html'], stored)
        require(len(soup(readback['body_html']).select('img')) == len(soup(parts['body_html']).select('img')),
                'Images lost in Shopify readback')
        require(bool(readback.get('image')), 'Hero image (article.image) was not stored')
        if live:
            self.request(path, {'article': {'id': result['id'], 'published': True}}, method='PUT')
            readback = self.request(path)['article']
            require(bool(readback.get('published_at')), 'Publication status readback failed')
        return readback

    def publish(self, package, blog, live):
        self.identity()
        if self.profile.data.get('article_contract') == 'journal-v1':
            return self.publish_journal(package, blog, live)
        fragment = article_fragment(package['body_html'], 'genseo-'+self.profile.store)
        article = {'title': package['title'], 'handle': package['handle'],
                   'body_html': fragment, 'published': False,
                   'author': self.profile.data['name'],
                   'metafields': [{'namespace': 'global', 'key': 'description_tag',
                                   'value': package['meta_description'], 'type': 'single_line_text_field'}]}
        # Always verify the real Shopify body while it is still unpublished.
        result = self.request(f'/admin/api/2026-04/blogs/{blog}/articles.json', {'article': article})['article']
        path = f"/admin/api/2026-04/blogs/{blog}/articles/{result['id']}.json"
        readback = self.request(path)['article']
        require(readback['handle'] == package['handle'], 'Handle readback failed')
        require(not readback.get('published_at'), 'Article was not created unpublished')
        validate_schema(readback['body_html'], package, self.profile)
        rendered = soup(readback['body_html'])
        require(rendered.select_one('#genseo-'+self.profile.store) is not None and rendered.style is not None,
                'Article layout or styles missing in Shopify readback')
        require(len(rendered.select('img')) == len(soup(fragment).select('img')), 'Images lost in Shopify readback')
        self.profile.check_text(readback['body_html'])
        if live:
            self.request(path, {'article': {'id':result['id'], 'published':True}}, method='PUT')
            readback = self.request(path)['article']
            require(bool(readback.get('published_at')), 'Publication status readback failed')
        return readback

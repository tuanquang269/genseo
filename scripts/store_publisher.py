"""Cherish article writes. The legacy Wellness Nest publisher remains separate."""
import importlib.util
import __future__
import json
import urllib.request
from store_profiles import require
from store_article import article_fragment, validate_schema, soup


class Shopify:
    def __init__(self, profile):
        require(profile.store == 'cherish', 'Use the legacy publisher for Wellness Nest')
        self.profile = profile
        profile.credential_domain()
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
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.load(response)

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

    def publish(self, package, blog, live):
        self.identity()
        fragment = article_fragment(package['body_html'])
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
        require(rendered.select_one('#genseo-cherish') is not None and rendered.style is not None,
                'Article layout or styles missing in Shopify readback')
        require(len(rendered.select('img')) == len(soup(fragment).select('img')), 'Images lost in Shopify readback')
        self.profile.check_text(readback['body_html'])
        if live:
            self.request(path, {'article': {'id':result['id'], 'published':True}}, method='PUT')
            readback = self.request(path)['article']
            require(bool(readback.get('published_at')), 'Publication status readback failed')
        return readback

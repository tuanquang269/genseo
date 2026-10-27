"""journal-v1 contract: post -> body + journal.* metafields + template_suffix. No network, no Shopify writes."""
import importlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEO = Path.home() / 'PATI/work/cherish-seo'
sys.path[:0] = [str(ROOT / 'scripts'), str(SEO / 'journal-data'), str(SEO / 'day1')]
import journal_fields as jf
import convert
from store_profiles import Profile, StoreGuardError
from store_publisher import Shopify

POSTS = ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7']
KEYS = ['style', 'crumb', 'kicker', 'dek', 'updated_on', 'read_minutes', 'meta_note', 'hero_caption', 'toc', 'pick', 'band', 'faq']


class JournalFieldsTests(unittest.TestCase):
    def test_p1_keys_and_clean_body(self):
        parts = convert.from_post(importlib.import_module('p1').POST)
        self.assertEqual([m['key'] for m in parts['metafields']], KEYS)  # style 1 has no schema_extra
        self.assertEqual(parts['template_suffix'], 'style-1')
        self.assertFalse(re.search(r'<style|<script|class="dek"|toc inline|section class="band"', parts['body_html']))
        faq = next(m for m in parts['metafields'] if m['key'] == 'faq')
        self.assertEqual([x['q'] for x in json.loads(faq['value'])], jf.visible_faq(parts['body_html'], 'q'))
        self.assertEqual([x['a'] for x in json.loads(faq['value'])], jf.visible_faq(parts['body_html'], 'a'))

    def test_post_dict_and_full_page_give_the_same_package(self):
        # GenSEO reads the writer's full page; convert.py reads the post dict. Both must agree for every day-1 post.
        for name in POSTS:
            post = importlib.import_module(name).POST
            page = next(SEO.glob(f"day1/style-{post['style']}-*.html")).read_text()
            a, b = convert.from_post(post), jf.from_document(page, post['style'])
            self.assertEqual(a['body_html'], b['body_html'], name)
            self.assertEqual(a['metafields'], b['metafields'], name)
            self.assertEqual(a['image'], b['image'], name)

    def test_rules_reject_bad_input(self):
        post = importlib.import_module('p1').POST
        with self.assertRaises(jf.JournalError):
            jf.assemble('<style>x</style>' + post['body'], {})
        with self.assertRaises(jf.JournalError):
            jf.check_tags(['hot sleepers', 'random tag'])
        self.assertEqual(jf.check_tags(['hot-sleepers', 'Comparisons']), ['Hot sleepers', 'Comparisons'])
        with self.assertRaises(jf.JournalError):
            jf.check_unique_hero('https://cdn/x/cherish-PDP-0620.webp', [{'id': 1, 'image': {'src': 'https://cdn/y/cherish-PDP-0620.webp?v=1'}}])

    def test_publisher_writes_journal_package_and_reads_it_back(self):
        profile = Profile('cherish')
        self.assertEqual(profile.data['article_contract'], 'journal-v1')
        post = importlib.import_module('p6').POST
        page = next(SEO.glob(f"day1/style-{post['style']}-*.html")).read_text()
        calls, store = [], {}

        class Fake(Shopify):
            def __init__(self):
                self.profile = profile

            def request(self, path, payload=None, method=None):
                calls.append((method or ('POST' if payload else 'GET'), path))
                if '/articles.json' in path and payload is None:
                    return {'articles': []}
                if path.endswith('/articles.json'):
                    a = dict(payload['article'], id=9, published_at=None, image={'src': 'x'})
                    store.update(a)
                    return {'article': a}
                if path.endswith('/metafields.json'):
                    return {'metafields': store['metafields']}
                if method == 'PUT':
                    store['published_at'] = '2026-10-28'
                    return {'article': store}
                return {'article': store} if path.endswith('9.json') else {'shop': {}}

            def identity(self):
                pass

        package = {'title': post['h1'], 'handle': post['slug'], 'meta_description': 'm' * 130, 'tags': ['Buying guides', 'Night sweats'],
                   'raw_html': page, 'style': post['style']}
        out = Fake().publish(package, 1, False)
        self.assertEqual(out['template_suffix'], 'style-4c')
        self.assertFalse(re.search(r'<style|<script|ld\+json', out['body_html']))
        self.assertEqual(store['tags'], 'Buying guides, Night sweats')
        self.assertEqual(sum(k['key'] in jf.KEYS for k in store['metafields']), 13)
        self.assertEqual([m for m, _ in calls].count('PUT'), 0)
        # live: unpublished first, then one PUT. A readback that lost a metafield never reaches the PUT.
        calls.clear(); store.clear()
        Fake().publish(package, 1, True)
        self.assertEqual([m for m, _ in calls].count('PUT'), 1)
        calls.clear(); store.clear()

        class Lossy(Fake):
            def request(self, path, payload=None, method=None):
                out = super().request(path, payload, method)
                if path.endswith('/metafields.json'):
                    out = {'metafields': [m for m in out['metafields'] if m['key'] != 'faq']}
                return out

        with self.assertRaises(jf.JournalError):
            Lossy().publish(package, 1, True)
        self.assertEqual([m for m, _ in calls].count('PUT'), 0)


if __name__ == '__main__':
    unittest.main()

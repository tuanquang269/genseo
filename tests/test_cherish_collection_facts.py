"""Offer membership ("Buy 1 Get 1 Free") has a citable live source: the linked offer collection. python3 -I tests/test_cherish_collection_facts.py"""
import sys, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'scripts'))
import run_store as r
from store_profiles import StoreGuardError

prof = types.SimpleNamespace(data={'domain': 'thecherishcompany.com', 'shop': 'uxfaue-s1.myshopify.com'})
html = ('<a href="/collections/buy-one-get-one-free-1">x</a><a href="https://thecherishcompany.com/collections/blankets">y</a>'
        '<a href="https://rival.com/collections/sale">z</a><a href="/collections/draft-only">d</a>')
assert r.linked_collections(prof, html) == {'buy-one-get-one-free-1', 'blankets', 'draft-only'}

def coll(h):
    if h == 'draft-only':
        raise StoreGuardError('Collection is not published in this store: ' + h)
    return {'handle': h, 'title': h, 'body_html': '<p>qualifies for our Buy 1, Get 1 Free offer</p>', 'updated_at': ''}
got = r.live_collections(types.SimpleNamespace(collection=coll), prof, html)
assert set(got) == {'buy-one-get-one-free-1', 'blankets'}, got   # unpublished is never evidence
assert 'shopify://{shop}/collections/<handle>' in r.WRITER_RULES and 'LIVE COLLECTION FACTS' in r.WRITER_RULES
print('collection facts OK')

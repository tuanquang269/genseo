"""Run: python3 -B tests/test_refill_admin_fallback.py. No network."""
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import refill_tickets as r

with patch.object(r, 'read_store_public', side_effect=HTTPError(r.SITE, 429, 'throttle', {}, None)), patch.object(r, 'read_store_admin', return_value='fresh') as admin:
    assert r.read_store() == 'fresh'
    admin.assert_called_once()
with patch.object(r, 'read_store_public', side_effect=HTTPError(r.SITE, 403, 'denied', {}, None)), patch.object(r, 'read_store_admin') as admin:
    try:
        r.read_store()
        assert False, 'Only HTTP 429 permits fallback'
    except HTTPError as error:
        assert error.code == 403
    admin.assert_not_called()

stamp = '2026-01-01T00:00:00+00:00'
product = dict(handle='live', title='Live', status='active', published_at=stamp,
               variants=[dict(price='12.00', inventory_management='shopify', inventory_quantity=0, inventory_policy='deny')])
articles = [dict(handle=f'a-{i}', title=f'Article {i}', published_at=stamp) for i in range(10)]
def paginate(path):
    if path.startswith('products.json'):
        return [product, dict(product, handle='draft', status='draft'), dict(product, handle='hidden', published_at=None)]
    if path.startswith('custom_collections'):
        return [dict(id=1, handle='live-collection', published_at=stamp), dict(id=2, handle='hidden', published_at=None)]
    if path.startswith('smart_collections'):
        return []
    if path.startswith('blogs.json'):
        return [dict(id=3, handle=r.BLOG)]
    return articles + [dict(handle='future', title='Future', published_at='2099-01-01T00:00:00Z')]
with patch.dict(sys.modules, {'fetch_all_articles': SimpleNamespace(paginate=paginate)}):
    products, collections, live = r.read_store_admin()
    assert set(products) == {'live'} and not products['live']['available']
    assert collections == {'live-collection': ['live']} and len(live) == 10
    product['variants'][0]['inventory_policy'] = 'continue'
    assert r.read_store_admin()[0]['live']['available']
    articles.clear()
    try:
        r.read_store_admin()
        assert False, 'Incomplete inventory must fail closed'
    except r.Refuse:
        pass
print('refill Admin fallback: PASS')

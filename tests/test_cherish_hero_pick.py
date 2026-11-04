"""pick_hero: never reuses a used hero, never passes an over-budget photo, and names the weights when it fails. python3 tests/test_cherish_hero_pick.py"""
import sys, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'scripts'))
import run_store as r, journal_fields
from store_profiles import StoreGuardError

imgs = [{'src': f'https://cdn.shopify.com/s/files/1/x/products/cherish-PDP-007{i}.webp?v=1'} for i in range(4)]
api = types.SimpleNamespace(product=lambda h: {'title': 'GlaciRest', 'images': imgs})
kb = {'cherish-PDP-0070': 90, 'cherish-PDP-0071': 132, 'cherish-PDP-0072': 259, 'cherish-PDP-0073': 110}
_orig = journal_fields.served_kb
journal_fields.served_kb = lambda src, width=1100: kb[r.stem(src)]
row = {'target_product_handle': 'glacirest'}
used = [{'image': {'src': imgs[0]['src']}}]
assert r.stem(r.pick_hero(api, row, used, 120)['src']) == 'cherish-PDP-0073'   # 0070 used, 0071/0072 heavy
try:
    r.pick_hero(api, row, used + [{'image': {'src': imgs[3]['src']}}], 120); raise AssertionError('reused or over budget')
except StoreGuardError as e:
    assert 'cherish-PDP-0071 132 KB' in str(e) and '2 already a Journal hero' in str(e) and 'build_set' in str(e), e
journal_fields.served_kb = _orig
print('hero pick OK')

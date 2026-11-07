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

# Kevin D1: a heavy photo with a lighter set (hero-sets.json) is used through the set; an 800 px photo fills 1100/1200/2200 with its 800 file
F = 'https://cdn.shopify.com/s/files/1/x/files/cherish-journal-hero-0072-{}.webp?v=2'
sets = {'cherish-PDP-0072': {'files': {str(w): {'url': F.format(w)} for w in (550, 750, 800)}}, '_retired': {}}
assert r.hero_slots(sets['cherish-PDP-0072']) == [(550, F.format(550)), (750, F.format(750)), (1100, F.format(800)), (1200, F.format(800)), (2200, F.format(800))]
_fk = r.file_kb; r.file_kb = lambda url: 78
used2 = used + [{'image': {'src': imgs[3]['src']}}]                     # 0070, 0073 used; 0071 heavy, no set; 0072 heavy, has a set
hero = r.pick_hero(api, row, used2, 120, sets)
assert hero['set'] and hero['src'] == F.format(800), hero
assert journal_fields.hero_set_from_srcset(', '.join(f'{u} {w}w' for w, u in hero['set'])) is not None   # publisher reads it as journal.hero_set
# the set's photo is used once it is a hero (the article image carries the set file name)
try:
    r.pick_hero(api, row, used2 + [{'image': {'src': F.format(800)}}], 120, sets); raise AssertionError('set photo reused')
except StoreGuardError:
    pass
r.file_kb = lambda url: 150                                              # a set still over budget is never used
try:
    r.pick_hero(api, row, used2, 120, sets); raise AssertionError('over-budget set used')
except StoreGuardError as e:
    assert '(set 150 KB)' in str(e), e
r.file_kb = _fk
journal_fields.served_kb = _orig
print('hero pick OK')

"""Render-gate fail tells the writer the exact word and image shortfall. python3 tests/test_cherish_shortfall.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'scripts'))
import run_store as r
rules = {'words': [1500, 2500], 'cards': [3, 5], 'img': [6, 9]}
out = "   RULES FAIL ['words', 'images'] words=1396 h2=9 qh2=5 cards=3 imgs=5 authority=2 journal=3"
hint = r.shortfall_hint(out, rules)
assert 'holds 1396 words; the minimum is 1500' in hint and 'aim for 2000' in hint and 'Add about 604' in hint, hint
assert 'IMAGES: 5 images; the minimum is 6' in hint and 'add 1 more .pcard' in hint, hint
assert r.shortfall_hint("RULES FAIL ['cards'] words=1600 h2=9 qh2=5 cards=2 imgs=6", rules) == ''
assert r.shortfall_hint('RULES PASS', rules) == ''
assert 'keep every product card' in r.WRITER_RULES
print('shortfall OK')

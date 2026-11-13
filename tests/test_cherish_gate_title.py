"""Truth page <title> = article title, as the live shell prints it (slot 2 2026-11-04: writer added " | The Cherish Company").
python3 tests/test_cherish_gate_title.py"""
import sys, inspect
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import cherish_auto as c
page = '<html><head><title>Best Robe (2027) | The Cherish Company</title></head><body><p>x</p></body></html>'
tpl = '<style>p{}</style><script>a()</script>'
out = c.gate_page(page, tpl, 'Best Robe (2027)')
assert '<title>Best Robe (2027)</title>' in out and 'The Cherish Company</title>' not in out, out
assert '<title>Best Robe (2027) | The Cherish Company</title>' in c.gate_page(page, tpl)   # no title given: page as written
assert "gate_page(package['body_html'], template, package['title'])" in inspect.getsource(c.main)
print('gate title OK')

# Publisher normalizes competitor metadata, but never article prose.
page = '<p class="meta"><span>By <b>The Cherish Company</b></span><span>Updated Nov 13, 2026</span><span>8 min read</span><span>Competitor lines cited only from pages opened this day</span></p><p><span>Competitor context stays in the body</span></p>'
out = c.shell_owned(page)
assert '<span>Facts checked against our product pages</span>' in out
assert '<span>Competitor context stays in the body</span>' in out
assert c.shell_owned(out) == out
assert c.shell_owned('<p class="meta"><span>Product facts checked today</span></p>') == '<p class="meta"><span>Product facts checked today</span></p>'
print('gate meta note OK')

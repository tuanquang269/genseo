"""finalize_page: the sticky bar names and links the rail pick, as the Journal shell prints it from journal.pick (slot 4 2026-11-04).
python3 tests/test_cherish_sticky_pick.py"""
import sys, re, datetime as dt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import run_store as r
page = ('<figure class="hero"><img src="a"></figure><aside class="rail"><div class="pick"><img src="p"><b>AltiCoddle six-layer</b>'
        '<a class="btn" href="/products/alticoddle-six">See</a></div></aside>'
        '<div class="stick" id="stick" aria-hidden="true"><b>GlaciRest</b><a class="btn" href="/products/glacirest-x" tabindex="-1">See it</a></div>')
src = r.finalize_page.__code__
# run only the sticky rewrite: the same regex block finalize_page applies after the hero swap
code = Path(r.__file__).read_text()
block = code[code.index("    pick = re.search(r'<div class=\"pick\""):code.index("flags=re.S)\n", code.index("    pick = re.search(r'<div class=\"pick\""))+len("flags=re.S)\n")]
ns = {'re': re, 'page': page}; exec('\n'.join(l[4:] for l in block.splitlines()), ns)
out = ns['page']
assert '<b>AltiCoddle six-layer</b><a class="btn" href="/products/alticoddle-six" tabindex="-1">' in out and 'glacirest' not in out.lower(), out
print('sticky pick OK')

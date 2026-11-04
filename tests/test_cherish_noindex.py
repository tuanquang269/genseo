"""noindex(): a 429 or browser error is retried and named, never read as 'no noindex'. python3 -I tests/test_cherish_noindex.py"""
import subprocess, sys, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'scripts'))
import cherish_auto as c

def fake(outputs):
    it = iter(outputs)
    return lambda *a, **k: types.SimpleNamespace(stdout=next(it), stderr='Traceback\nError: boom', returncode=0)

import unittest.mock as um
_patches = [um.patch.object(c.time, 'sleep', lambda s: None), um.patch.object(c, 'subprocess', types.SimpleNamespace(run=None, SubprocessError=subprocess.SubprocessError))]
for _p in _patches: _p.start()
c.subprocess.run = fake(['{"status": 429, "robots": ""}', '{"status": 200, "robots": "noindex,nofollow"}'])
assert c.noindex('u') == (True, "robots='noindex,nofollow'")
c.subprocess.run = fake(['{"status": 429, "robots": ""}'] * 3)
ok, why = c.noindex('u'); assert not ok and 'HTTP 429' in why, why
c.subprocess.run = fake(['', '', ''])
ok, why = c.noindex('u'); assert not ok and 'boom' in why, why
c.subprocess.run = fake(['{"status": 200, "robots": "index,follow"}'])
assert c.noindex('u') == (False, "robots='index,follow'")
for _p in _patches: _p.stop()   # never leak into the unittest run (the suite imports every test_*.py)
print('noindex OK')

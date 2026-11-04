"""A fidelity FAIL names the failing cells and the first DOM difference (slot 3 on 11-04 said only 'GATE: FAIL'). python3 -I tests/test_cherish_gate_why.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'scripts'))
import cherish_auto as c
why = c.gate_why(Path(__file__).resolve().parent/'fixtures'/'gate_why')
assert '4d@1440: pixel FAIL (14 tiles), dom (lines) FAIL (2)' in why, why
assert '$69+' in why and '4+ items' in why, why
assert 'no REPORT.md' in c.gate_why(Path('/nonexistent'))
print('gate_why OK')

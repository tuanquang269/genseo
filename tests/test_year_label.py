"""Tip #1 next-year label: style 2/4c rows from Oct 1 carry next year; others none. python3 -I tests/test_year_label.py"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'scripts'))
from run_store import year_label
assert year_label({'day': '2026-11-03', 'style': '4c'}) == '2027'
assert year_label({'day': '2026-10-01', 'style': '2'}) == '2027'
assert year_label({'day': '2026-09-30', 'style': '4c'}) == ''
assert year_label({'day': '2027-02-01', 'style': '4c'}) == ''
assert year_label({'day': '2026-11-03', 'style': '1'}) == ''
# the label is stripped before the numeric-claim check
assert not re.search(r'\d', re.sub(r'(?<!\w)#\d+\b|\(20\d\d\)', '', 'Best Duvet for Night Sweats (2027)'))
print('year_label OK')

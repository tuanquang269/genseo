#!/usr/bin/env python3
"""Fail (exit 2) if any OPEN ticket names a banned AgeAura SKU or a bare AgeAura with no NMN + TMG product,
or makes a FloraFresh formula claim its Supplement Facts label does not support (15 billion CFU, Lactobacillus
strains, XOS, D-mannose, sugar-free, or strains/CFU taken from the PDP description).

The rules live in brand_rules.py (FloraFresh label facts: florafresh_rules.py). Builders must prepare_ticket()
before appending so an ambiguous AgeAura line is locked to ageaura-pure-nmn-tmg-nad-complex instead of failing
here. Closed tickets (DONE, SKIPPED, ...) are history and are not linted.
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brand_rules as br
path = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/genseo/daily-tickets.md")
blocks = re.split(r'\n(?=- \[|## \[)', open(path).read())
bad = []
for b in blocks:
    if not re.match(r'(- \[ \]|## \[ \])', b): continue
    v = br.violations(b)
    if v: bad.append((b.split('\n')[0][:90], v))
for t, v in bad: print(f"BANNED in open ticket: {t}\n   {'; '.join(v)}")
print(f"lint_tickets: {len(bad)} open ticket(s) with brand-rule violations")
sys.exit(2 if bad else 0)

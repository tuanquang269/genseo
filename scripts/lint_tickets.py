#!/usr/bin/env python3
"""Fail (exit 2) if any OPEN ticket names a banned AgeAura SKU or a bare AgeAura with no NMN + TMG product,
makes a FloraFresh formula claim its Supplement Facts label does not support (15 billion CFU, Lactobacillus
strains, XOS, D-mannose, sugar-free, or strains/CFU taken from the PDP description), states a Shilajit
Shockwave milligram, serving count, or other dose its pack-label whitelist does not list, states a
Pure Shilajit Gold Resin milligram, serving count, volume, weight, day-supply, or other dose its
pack-label whitelist does not list, or states a ShilaSource Himalayan Shilajit Resin milligram,
serving count, volume, weight, fulvic percentage, mineral count, day-supply, or other dose its
pack-label whitelist does not list.

The rules live in brand_rules.py (FloraFresh: florafresh_rules.py; Shockwave: shockwave_rules.py;
Gold Resin: gold_resin_rules.py; ShilaSource resin: shilasource_resin_rules.py). Builders must
prepare_ticket() before appending so an ambiguous AgeAura line is locked to
ageaura-pure-nmn-tmg-nad-complex instead of failing here. Closed tickets (DONE, SKIPPED, ...) are
history and are not linted.
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

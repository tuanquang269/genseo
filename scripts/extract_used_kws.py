import re

with open('/Users/kevinkreative/genseo/GENSEO_30_DAY_SCHEDULE.md') as f:
    content = f.read()

# Extract all secondary keyword lines (which contain ALL keywords used per ticket)
secondary = re.findall(r'\*\*Secondary Keywords\*\*: `([^`]+)`', content)
all_used = set()
for line in secondary:
    for kw in line.split(", "):
        all_used.add(kw.strip().lower())

# Also extract primary keywords
primary = re.findall(r'\*\*Primary Keyword\*\*: `([^`]+)`', content)
for kw in primary:
    all_used.add(kw.strip().lower())

print(f"Total unique keywords already used in Round 1: {len(all_used)}")
for kw in sorted(list(all_used))[:10]:
    print(f"  - {kw}")
print("...")

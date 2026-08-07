#!/usr/bin/env python3
"""autocomplete_candidates.py — FREE external demand source (no API key, no paid SEO tool).

Google Autocomplete only suggests phrases that have real search volume, and it can be geo-scoped
to {{MARKET}} (gl=sg). So it's an approximate-but-honest demand signal for topics we can't see in
our own GSC yet (we have no page -> no impressions). Seeds = brands we stock + core categories,
each expanded with commercial modifiers; harvest SG suggestions, dedup, then filter through
topic_fitness so we KEEP only genuine uncovered new-article topics (drop head-terms owned by a
collection, near-duplicates, dead flavour variants, and brands already covered by an article).

No volume numbers or competitor rankings (that needs a paid tool) — this is the "tương đối" check.
Output: a ranked candidate list to vet/convert into tickets (does NOT auto-publish).

Usage: autocomplete_candidates.py [out.txt] [--depth 1|2]
"""
import json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topic_fitness as tf

ROOT = "/Users/kevinkreative/genseo"
MODIFIERS = ["{{market}}", "review", "best", "worth it", ""]   # commercial/review intent seeds
CATEGORIES = ["whey protein", "creatine", "pre workout", "mass gainer", "fat burner", "bcaa",
              "eaa", "collagen", "multivitamin", "fish oil omega", "protein bar", "casein",
              "plant protein", "electrolyte", "greens superfood", "test booster"]

# NAVIGATIONAL / company-info / off-geo noise — autocomplete surfaces these on brand seeds
# ("allmax nutrition headquarters/owner/canada/india") but they are useless for a SG shopper and
# would make thin pages. Drop any candidate containing one of these tokens.
NAV_STOP = {'headquarters', 'owner', 'inc', 'ltd', 'llc', 'country', 'origin', 'ceo', 'founder',
            'wikipedia', 'wiki', 'stock', 'share', 'net worth', 'networth', 'address', 'phone',
            'hiring', 'jobs', 'careers', 'career', 'meaning', 'definition', 'salary', 'revenue',
            'canada', 'india', 'usa', 'uk', 'us', 'philippines', 'malaysia', 'australia', 'nz',
            'indonesia', 'vietnam', 'europe', 'reddit', 'amazon', 'iherb', 'lazada', 'shopee',
            'discount code', 'coupon', 'promo code', 'login', 'app', 'contact', 'email',
            'recall', 'lawsuit', 'scam', 'fake', 'expired', 'banned'}
# commercial/product signal — a candidate must have at least ONE (a product noun, intent word, or
# '{{market}}') so we keep "best force factor test booster" but drop bare "force factor brands".
COMMERCIAL = tf.PRODUCT_NOUNS | tf.INTENT | {'{{market}}', 'sg', 'best', 'top', 'flavor', 'flavour', 'price'}


def suggest(q):
    url = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(
        {"client": "chrome", "hl": "en", "gl": "sg", "q": q})
    r = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        return json.load(urllib.request.urlopen(r, timeout=10))[1]
    except Exception:
        return []


def seeds():
    """stocked brands (from the catalog snapshot) + core categories."""
    out = list(CATEGORIES)
    try:
        vend = json.load(open(f"{ROOT}/catalog_vendors.json"))
        for v, c in vend.items():
            instock = c[1] if isinstance(c, list) else c.get('instock', 0)
            if instock >= 3 and v.lower() not in ('your brand', 'your brand', 'unknown', ''):
                out.append(v.lower())
    except Exception:
        out += [b for b in tf.STOCKED_BRANDS]
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out = args[0] if args else f"{ROOT}/autocomplete-new-candidates.txt"
    depth = 2 if '--depth' in sys.argv and sys.argv[sys.argv.index('--depth') + 1] == '2' else 1

    arts = tf._load(f"{ROOT}/existing_articles.json", [])
    colls = tf._load(f"{ROOT}/existing_collections.json", [])
    raw = f"{ROOT}/autocomplete_raw.json"

    if '--from-cache' in sys.argv and os.path.exists(raw):
        harvested = set(json.load(open(raw)))
        seed_list = []
    else:
        harvested = set()
        seed_list = seeds()
        for s in seed_list:
            for m in MODIFIERS:
                for sug in suggest(f"{s} {m}".strip()):
                    harvested.add(sug.lower().strip())
                time.sleep(0.15)
        if depth == 2:
            for sug in list(harvested):
                if any(b in sug for b in ('review', 'vs', 'best')):
                    for s2 in suggest(sug):
                        harvested.add(s2.lower().strip())
                    time.sleep(0.15)
        json.dump(sorted(harvested), open(raw, "w"))

    def is_noise(q):
        toks = set(q.split())
        if toks & NAV_STOP or any(p in q for p in NAV_STOP if ' ' in p):
            return True                          # navigational / off-geo / company-info
        if not (set(re.findall(r'[a-z0-9]+', q)) & COMMERCIAL):
            return True                          # no product/intent signal -> bare brand-info
        return False

    keep, buckets, dropped_noise = [], {}, 0
    seen_topic = set()
    for q in sorted(harvested):
        if len(q) < 6:
            continue
        if is_noise(q):
            dropped_noise += 1
            continue
        v, code, why = tf.assess(q, articles=arts, collections=colls)  # no pos: ranking guard off (see note)
        buckets[code] = buckets.get(code, 0) + 1
        if v != 'PASS':
            continue
        # dedup to ONE topic per brand + product-noun (else 16 "allmax ..." rows collapse to a few)
        brand = next((b for b in tf.STOCKED_BRANDS if b in q), '')
        nouns = tuple(sorted(w for w in re.findall(r'[a-z0-9]+', q) if w in tf.PRODUCT_NOUNS))
        key = (brand, nouns)
        if key in seen_topic:
            continue
        seen_topic.add(key)
        keep.append((q, why))

    keep.sort()
    with open(out, "w") as f:
        f.write(f"# Autocomplete-mined NEW-article candidates (SG geo, free). {len(harvested)} phrases "
                f"harvested; {dropped_noise} dropped as navigational/off-geo noise; {len(keep)} distinct "
                "PASS topics (deduped to one per brand+product).\n"
                "# No pos data (autocomplete gives none) so the anti-cannibalization RANK guard is OFF here —\n"
                "# vet each against live rank before ticketing (STEP 0 dup-check is the publish-time backstop).\n\n"
                + "\n".join(f"- {q}   ({why[:60]})" for q, why in keep))
    print(f"autocomplete: {len(harvested)} harvested, {dropped_noise} noise dropped, "
          f"{len(keep)} distinct PASS topics -> {os.path.basename(out)}")
    print(f"  verdicts (post-noise): {buckets}")


if __name__ == '__main__':
    main()

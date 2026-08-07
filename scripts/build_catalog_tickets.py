#!/usr/bin/env python3
"""build_catalog_tickets.py — the SUSTAINABLE new-article pipeline.

Problem it solves: GSC-visible new-article demand is ~exhausted (of 359 SG demand queries only
4 are genuine uncovered new-article topics; the rest are head-terms/collection work or pages we
already rank = refresh). But there is demand we CANNOT see in GSC yet: for a brand we stock but
have NO page for, we earn zero impressions -> GSC shows zero demand -> yet the brand IS searched
before purchase. The first review/where-to-buy page captures that latent demand. The proven
winning pattern on this store is exactly that: stocked-brand review / comparison / where-to-buy
(Owala guide 54 clicks, Myprotein review 17, Muscle Blaze 13).

So this generator sources candidates from the LIVE CATALOG (brands we actually stock, in-stock
only) instead of GSC. For every brand we sell with real depth and no existing article, it emits
ONE quality brand-review ticket. Verified in-stock (no 404 risk) and gated by topic_fitness
(skips brands already covered). Priority brands first, then by in-stock SKU depth.

Output = same rich-brief format as build_rich_tickets.py, so the Antigravity cron consumes it
identically. Refuses to overwrite an existing ticket file (won't clobber the cron's live queue).

Usage: build_catalog_tickets.py [out.md] [--min-sku 3]
"""
import json, os, re, sys, urllib.request
from collections import defaultdict

ROOT = "/Users/kevinkreative/genseo"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topic_fitness as tf
import build_rich_tickets as brt   # reuse theme_for / brands_for / angle_for / AUTHORS / tc

cfg = json.load(open(os.path.expanduser('~/.genseo/shopify_token.json')))
SHOP, TOKEN = cfg['shop'], cfg['access_token']
API = f"https://{SHOP}/admin/api/2026-04"

# brands that are our own house label / not a real third-party brand to review
SKIP_VENDORS = {'your brand', 'your brand', 'unknown', ''}
MIN_SKU = 3   # need real range depth — a 1-2 SKU brand isn't worth a dedicated review page

# Shopify productType is a noisy taxonomy, so DON'T use it in the title — brands are searched by
# NAME ("Force Factor review {{market}}"), not by category noun. Use it ONLY to pick the right
# collection / author / comparison-table. First keyword that matches the dominant productType wins.
# (collection must exist in brt.COLLECTIONS; author-key must exist in brt.AUTHORS)
CATEGORY_MAP = [
 (('hair', 'skin', 'nail', 'collagen', 'beauty'), 'collagen', 'dietetics', 'beauty/collagen products (type, dose, format)'),
 (('amino', 'bcaa', 'eaa', 'glutamine', 'intra'), 'intra-workout', 'sports', 'amino/BCAA products (ratio, EAAs, dose)'),
 (('pre-workout', 'pre workout', 'preworkout', 'pump'), 'pre-workout', 'training', 'pre-workouts (caffeine, key actives, focus vs pump)'),
 (('fat burn', 'thermogenic', 'weight', 'lean', 'burner'), 'fat-burner', 'medical', 'fat burners (stimulant vs non-stim, actives)'),
 (('creatine',), 'creatine', 'sports', 'creatine products (form, dose, price per serving)'),
 (('omega', 'fish oil', 'epa', 'dha'), 'omega-3-fish-oils', 'clinical', 'omega-3 products (EPA/DHA per serving, price)'),
 (('immune', 'immunity', 'elderberry'), 'immune-support', 'clinical', 'immune supplements compared'),
 (('probiotic', 'digest', 'gut', 'enzyme', 'fibre'), 'digestive-support', 'clinical', 'digestive/probiotic options'),
 (('sleep', 'melatonin'), 'sleep-improvement', 'clinical', 'sleep supplements (ingredient, dose, timing)'),
 (('men',), 'mens-health', 'clinical', "men's health supplements (actives, dose, who it's for)"),
 (('women',), 'womens-health', 'clinical', "women's health supplements (actives, dose, who it's for)"),
 (('child', 'kids', 'kid'), 'childrens-health', 'clinical', "kids' supplements (actives, dose, format)"),
 (('whey', 'protein', 'isolate', 'casein'), 'whey-protein', 'sports', 'proteins (type, protein per serving, price)'),
 (('bottle', 'shaker', 'accessor'), 'shakers-bottle', 'fitness', 'accessories (type, capacity, price)'),
]
CATEGORY_DEFAULT = ('vitamin-wellness', 'clinical', 'the products in this range (form, dose, who it\'s for)')


def category_for(ptype):
    """dominant productType -> (category-collection, author-key, table-subject)."""
    pl = (ptype or '').lower()
    for kws, coll, author, table in CATEGORY_MAP:
        if any(k in pl for k in kws):
            return coll, author, table
    return CATEGORY_DEFAULT


def tc(q):
    """title-case a topic (mirror of build_rich_tickets' nested helper)."""
    small = {'in', 'of', 'the', 'for', 'a', 'to', 'vs', 'and', 'with'}
    return " ".join(w if w in small else w.capitalize() for w in q.split())


def gql(q, v=None):
    body = json.dumps({"query": q, "variables": v or {}}).encode()
    r = urllib.request.Request(f"{API}/graphql.json", data=body,
        headers={"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r))


def catalog():
    """normalised-brand -> {display, instock, types(Counter), handle(sample in-stock product)}.
    Merges vendor-name casing variants ("Nutricost"/"nutricost", "Now Foods"/"now foods") that
    Shopify stores as distinct vendor strings but are the same brand — else we'd ticket it twice."""
    v = {}
    cursor = None
    q = '''query($c:String){products(first:250,after:$c,query:"status:active"){
      pageInfo{hasNextPage endCursor}
      edges{node{vendor productType handle totalInventory}}}}'''
    while True:
        d = gql(q, {"c": cursor})
        pd = d['data']['products']
        for e in pd['edges']:
            n = e['node']
            if (n['totalInventory'] or 0) <= 0:
                continue
            ven = (n['vendor'] or '').strip()
            k = tf._norm(ven)
            if not k:
                continue
            rec = v.setdefault(k, {'display': ven, 'instock': 0, 'types': defaultdict(int), 'handle': None})
            if len(ven) > len(rec['display']):   # keep the most complete casing as display
                rec['display'] = ven
            rec['instock'] += 1
            if n.get('productType'):
                rec['types'][n['productType']] += 1
            if not rec['handle']:
                rec['handle'] = n['handle']
        if not pd['pageInfo']['hasNextPage']:
            break
        cursor = pd['pageInfo']['endCursor']
    return v


def collection_handle(brand):
    """the brand's own collection handle if the store has one (else None)."""
    bn = tf._norm(brand)
    for c in brt.COLLECTIONS:
        if tf._norm(c) == bn or bn in tf._norm(c):
            return c
    return None


ANGLE = ("Brand review / where-to-buy — direct verdict up top (who it's for, is it worth it), "
         "then a comparison table of this brand's range we stock, then where to buy in SG with {{CURRENCY}} price.")


def render_ticket(c, num):
    """render one PASS candidate as a rich-brief ticket block (list of lines)."""
    links = []
    if c['own_coll']:
        links.append(c['own_coll'])            # the brand's OWN collection — the most relevant link
    if c['cat_coll'] not in links:
        links.append(c['cat_coll'])            # the product category collection
    for extra in ('vitamin-wellness', 'general-health', 'whey-protein'):
        if len(links) >= 2:
            break
        if extra not in links and extra in brt.COLLECTIONS:
            links.append(extra)
    coll_links = " , ".join(f"/collections/{h}" for h in links[:3])
    pbs = brt.brands_for(f"{c['brand']} {c['type']}", c['table'])
    pb_str = ", ".join(f"{n} (/collections/{coll})" if coll else f"{n} (link products)" for n, coll in pbs) \
             or "no specific priority brand fits — use the best products you stock"
    author = brt.AUTHORS[c['author_key']]
    return [
        f"### 📝 Ticket #{num} — Brand Review: {tc(c['brand'])} {{MARKET}}",
        f"- **Brand focus**: `{c['brand']}`  ({c['instock']} in-stock SKU; latent brand-search demand — we have no page yet)",
        f"- **Angle**: {ANGLE}",
        f"- **MUST link these collections (≥2)**: `{coll_links}`",
        f"- **Feature priority brands** (naturally, for cross-sell — never fake): {pb_str}",
        f"- **Comparison table subject**: {c['table']}",
        f"- **Assigned author**: {author}",
        f"- **Anchor product** (verified in-stock, safe to link): `/products/{c['handle']}`",
        "- **Dedup**: no existing article for this brand (STEP 0 will re-verify live).",
        "- **Action**: [ ] PENDING",
        "**🤖 Auto-Publish Trigger Prompt:**",
        "```markdown",
        (f"/genseo-auto-publish CREATE A [NEW ARTICLE]. Title Focus: \"A Creative and Engaging SEO "
         f"Title for '{tc(c['brand'])} Review' in {{MARKET}}\". ANGLE: {ANGLE} MUST link collections: "
         f"{coll_links}. Anchor product (in-stock, real): /products/{c['handle']}. Feature priority "
         f"brands naturally for cross-sell: {pb_str}. Comparison table: {c['table']}. Author: {author}. "
         f"Default BLOG_ID is 104008483131."),
        "```",
        "",
    ]


def build_candidates():
    """returns (passed, review, skipped_covered, skipped_thin) from the live catalog + article cache."""
    arts = tf._load(f"{ROOT}/existing_articles.json", [])
    colls = tf._load(f"{ROOT}/existing_collections.json", [])
    blobs = [tf._norm(a.get('title', '') + ' ' + a.get('handle', '')) for a in arts]
    cat = catalog()
    prio = {tf._norm(b[0]) for b in brt.PRIORITY_BRANDS}
    passed, review, skipped_covered, skipped_thin = [], [], 0, 0
    for k, rec in cat.items():
        ven = rec['display']
        if ven.lower() in SKIP_VENDORS:
            continue
        if rec['instock'] < MIN_SKU:
            skipped_thin += 1
            continue
        # 1 brand = 1 page. If the brand name appears in ANY existing article, we already have brand
        # content — skip (topic_fitness's noun-based coverage misses "brand review" vs "brand omega 3",
        # so check the brand name directly here).
        if any(k in b for b in blobs):
            skipped_covered += 1
            continue
        dtype = max(rec['types'].items(), key=lambda x: x[1])[0] if rec['types'] else ''
        # gate on brand-review intent. Brand NAME is what people search — productType only picks
        # the collection/author (via category_for), never the title.
        v, code, why = tf.assess(f"{ven} review {{market}}", articles=arts, collections=colls)
        if v == 'FAIL':          # head-term / dup
            skipped_covered += 1
            continue
        coll, author_key, table = category_for(dtype)
        rec2 = {'brand': ven, 'type': dtype, 'instock': rec['instock'], 'handle': rec['handle'],
                'is_prio': k in prio, 'own_coll': collection_handle(ven),
                'cat_coll': coll, 'author_key': author_key, 'table': table}
        (passed if v == 'PASS' else review).append(rec2)
    # priority brands first, then by in-stock depth (our investment = the demand proxy)
    passed.sort(key=lambda c: (not c['is_prio'], -c['instock']))
    review.sort(key=lambda c: -c['instock'])
    return passed, review, skipped_covered, skipped_thin


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    global MIN_SKU
    if '--min-sku' in sys.argv:
        MIN_SKU = int(sys.argv[sys.argv.index('--min-sku') + 1])

    # --append MODE: add only NEW (not-already-in-queue) brand tickets to an existing queue file,
    # renumbering after its highest ticket. Idempotent — safe to run daily to refill a low queue.
    if '--append' in sys.argv:
        queue = sys.argv[sys.argv.index('--append') + 1]
        if not os.path.isabs(queue):
            queue = f"{ROOT}/{queue}"
        content = open(queue).read()
        have = {tf._norm(m) for m in re.findall(r'Brand Review: (.+?) {{MARKET}}', content)}
        passed, _, _, _ = build_candidates()
        fresh = [c for c in passed if tf._norm(c['brand']) not in have]
        if not fresh:
            print(f"catalog --append: 0 new brands to add (queue already has all {len(passed)} eligible)")
            return
        nums = [int(n) for n in re.findall(r'^### 📝 Ticket #(\d+)', content, flags=re.M)]
        start = max(nums) + 1 if nums else 1
        block = ["", "## 🗓️ Catalog Brand-Coverage (latent-demand, sourced from live stock)", ""]
        for i, c in enumerate(fresh):
            block += render_ticket(c, start + i)
        with open(queue, "a") as f:
            f.write("\n".join(block) + "\n")
        print(f"catalog --append: added {len(fresh)} new brand tickets (#{start}-#{start+len(fresh)-1}) "
              f"to {os.path.basename(queue)}: {', '.join(c['brand'] for c in fresh)}")
        return

    # default MODE: write a fresh standalone ticket file (won't clobber an existing one)
    out = args[0] if args else f"{ROOT}/catalog-brand-tickets.md"
    if os.path.exists(out):
        print(f"refusing to overwrite existing {os.path.basename(out)} — delete it first, pass a new name, or use --append")
        sys.exit(2)
    passed, review, skipped_covered, skipped_thin = build_candidates()
    L = ["# 🗓️ Catalog Brand-Coverage — NEW-ARTICLE tickets (sustainable pipeline)", "",
         f"*Source: LIVE catalog — brands we stock (in-stock ≥{MIN_SKU} SKU) with NO existing article. "
         "Captures latent brand-search demand GSC can't show (no page = no impressions yet). "
         "Winning pattern: stocked-brand review + where-to-buy. All in-stock (no 404s). "
         "Only topic_fitness PASS brands (vouched, stocked) are ticketed here; unvouched brands go to "
         "the `-needs-review.txt` sidecar for me to vet (add to STOCKED_BRANDS) before ticketing.*", "",
         "## 🎯 PRIORITY BRANDS (feature FIRST, naturally, for cross-sell): "
         "**Mutant · PVL · Ghost · JNX · Pure Protein · Dymatize · PB2**", ""]
    for i, c in enumerate(passed):
        L += render_ticket(c, i + 1)
    open(out, "w").write("\n".join(L))
    if review:
        rf = out.rsplit('.md', 1)[0] + "-needs-review.txt"
        open(rf, "w").write(
            "# Catalog brands NOT yet vouched (not in topic_fitness STOCKED_BRANDS). Vet SG demand +\n"
            "# whether a dedicated brand review is worth it; if yes, add the brand to STOCKED_BRANDS and\n"
            "# re-run. Sorted by in-stock SKU depth.\n\n"
            + "\n".join(f"- {c['brand']}  ({c['instock']} SKU, type: {c['type']})" for c in review))
    print(f"catalog brand-coverage: {len(passed)} PASS tickets -> {os.path.basename(out)}; "
          f"{len(review)} unvouched brands -> sidecar")
    print(f"  skipped: {skipped_covered} already-covered brands, {skipped_thin} thin (<{MIN_SKU} SKU)")


if __name__ == '__main__':
    main()

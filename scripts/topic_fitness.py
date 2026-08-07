#!/usr/bin/env python3
"""topic_fitness.py — decide whether a NEW-ARTICLE topic is worth publishing.

Data-derived gate (2026-07-22 audit): of 806 blog pages with SG impressions only ~12% earn
any SG click; the DEAD ones are generic flavour/recipe/variant pages ("coffee protein shake",
"fruity pebbles protein", "banana protein powder") — 0 clicks, ~0 impressions. The WINNERS are
specific brand/product reviews, comparisons, and where-to-buy pages for items we stock (Owala
store guide, Myprotein/Muscle Blaze/Mutant reviews, "best place to buy Transparent Labs",
"Myprotein vs Optimum Nutrition"). So a topic earns a NEW article only if it looks like a
winner and is not already covered.

Verdicts: PASS (exit 0), REVIEW (exit 2 — allowed but flagged), FAIL (exit 1 — do not create).

Rules (a heuristic gate — tune the lists as data grows):
  FAIL  near-duplicate of an existing live article (we already have the page)
  FAIL  bare category head-term a COLLECTION owns ("best protein powder {{market}}") -> the
        collection page should win it, a new article would cannibalise it
  FAIL  flavour/recipe variant with no stocked brand + no purchase intent (the dead pattern)
  FAIL  explicit SG demand floor breached (--sg-imp below MIN_IMP)
  PASS  names a stocked brand AND has review/comparison/buy intent (the winning pattern)
  REVIEW everything else (genuine ingredient/how-to gap, or ambiguous — a human/Claude decides)

Usage:
  topic_fitness.py "Atlas Whey Review {{MARKET}}" [--sg-imp 140]
  topic_fitness.py "coffee protein shake {{market}}"
  topic_fitness.py --self-check
"""
import json, re, sys

ROOT = "/Users/kevinkreative/genseo"
MIN_IMP = 20          # below this SG demand, not worth a dedicated page
DUP_JACCARD = 0.72    # significant-word overlap with an existing title = duplicate
RANK_FLOOR = 8        # if we already rank SG pos <= this, a NEW page cannibalises the winner (refresh instead)

# brands we actually stock (lowercase substrings). Names a specific entity => winner-shaped.
STOCKED_BRANDS = {
 'mutant','pvl','pure vita labs','ghost','jnx','pure protein','dymatize','pb2','optimum nutrition','myprotein',
 'muscletech','musclepharm','cellucor','kaged','labrada','allmax','applied nutrition','isopure',
 'quest','barebells','bsn','nutrex','rsp','evlution','evl','science in sport','amazing grass',
 'garden of life','now foods','now sports','california gold','natrol','nutricost','sports research','muscleblaze',
 'muscle blaze','atlas','agym','cbum','nutrabio','gold standard','iso100','iso 100','serious mass',
 'combat','xtend','c4','creakong','hydroxycut','owala','blender bottle','blenderbottle',
 'lean body','emerald labs','redcon1','bpi','force factor','goli','neocell','youtheory',
 'sambucol','olly','titan whey','iso surge','maxines','impact whey',
 'platinum hydro','hydro whey','childlife','doctors best',"doctor's best",'solaray','paradise herbs','north coast naturals','natures way',"nature's way",'21st century','mrm',
}
# NOTE: fairlife / meiji / ntuc / fairprice are NOT here on purpose — we don't SELL them. They are
# comparison/informational brands (like the meiji drink page), so their query variants land in REVIEW
# (a human/Claude decides), never auto-PASS as a "winning stocked-brand" article.
# NOTE: bare ingredients (ksm-66, ashwagandha, carnitine, creatine, collagen...) are deliberately
# NOT "brands" — an ingredient guide has no specific product entity, so it lands in REVIEW for a
# human/Claude to confirm real demand before writing (that is how the NutraBio spokes were vetted).
# purchase / comparison intent signals (winning shape)
INTENT = {'review','vs','versus','worth it','worth buying','best place to buy','where to buy',
          'is it good','is it worth','price','cost','buy','honest','compare','comparison','good or'}
# flavour/recipe modifiers that are DEAD when standalone (our 0-click pattern)
DEAD_FLAVOUR = {'coffee','mocha','latte','cappuccino','banana','strawberry','mango','salted caramel',
 'fruity pebbles','reese','reeses','cereal','cookie','oreo','pancake','waffle','smoothie','recipe',
 'ice cream','milkshake','birthday cake','cinnamon','matcha','taro','horlicks','milo','fruity',
 'peanut butter cup','s\'mores','smores','marshmallow','honey','vanilla latte'}
# product-category nouns — used with a brand to detect "we already cover this brand+product"
PRODUCT_NOUNS = {'whey','isolate','creatine','preworkout','pre-workout','mass','gainer','bcaa','eaa',
 'amino','casein','collagen','protein','milk','shake','bar','iso','energy','drink','water','bottle',
 'tumbler','omega','multivitamin','burner','carnitine','glutamine','hydro','syntha','pump','review',
 'store','outlet','freesip','test','supplements','powder','nutrition','isogold'}
# category head-terms a COLLECTION owns — a new article cannibalises them
COLLECTION_HEADTERMS = [
 'best protein powder','protein powder {{market}}','buy protein powder','best whey','whey protein powder',
 'best creatine','creatine {{market}}','best pre workout','best pre-workout','best fat burner',
 'best collagen','best multivitamin','best mass gainer','mass gainer {{market}}','supplements {{market}}',
 'best supplement brand','best supplement store','best protein brand','best amino','best bcaa',
 'protein bars {{market}}','best protein bar',
]

def sig_words(s):
    stop = {'in','of','the','for','a','to','vs','and','with','is','it','{{market}}','best','review','2026','2025','sg','guide','ultimate'}
    return {w for w in re.findall(r'[a-z0-9]+', s.lower()) if len(w) > 2 and w not in stop}

def has_any(text, needles):
    t = text.lower()
    return any(n in t for n in needles)

def _norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

_ARTIDX = {}
def _article_index(articles):
    """(cached) list of (normalised-blob, token-set) per existing article — for coverage checks."""
    k = id(articles)
    if k not in _ARTIDX:
        idx = []
        for a in articles:
            blob = a.get('title', '') + ' ' + a.get('handle', '')
            idx.append((_norm(blob), set(re.findall(r'[a-z0-9]+', blob.lower()))))
        _ARTIDX[k] = idx
    return _ARTIDX[k]

def assess(topic, sg_imp=None, articles=None, collections=None, pos=None):
    """Return (verdict, code, reason). verdict in {PASS, REVIEW, FAIL}.
    code lets callers set severity per reason (e.g. the publish gate treats 'dup' as a warning
    since a legit REFRESH matches its own title, but 'flavour'/'headterm' as hard fails).
    pos (optional) = our current avg SG rank for the query; ranking page-1 already means a new
    article would cannibalise the page that's already winning."""
    t = topic.lower().strip()

    if sg_imp is not None and sg_imp < MIN_IMP:
        return 'FAIL', 'demand', f'SG demand {sg_imp} imp < floor {MIN_IMP} — no audience'

    if pos is not None and 0 < pos <= RANK_FLOOR:
        return 'FAIL', 'ranking', f'we already rank SG pos {pos:.0f} for this — a new page cannibalises the page already winning it; refresh/leave that page'

    # near-duplicate vs existing live articles
    if articles:
        tw = sig_words(t)
        if tw:
            for a in articles:
                aw = sig_words(a['title'])
                if not aw:
                    continue
                j = len(tw & aw) / len(tw | aw)
                if j >= DUP_JACCARD:
                    return 'FAIL', 'dup', f'near-duplicate of existing article "{a["title"][:50]}" (overlap {j:.2f}) — refresh it, do not recreate'

    # bare category head-term owned by a collection (and NOT a specific-brand angle)
    brand_hit = next((b for b in STOCKED_BRANDS if b in t), None)
    if not brand_hit and has_any(t, COLLECTION_HEADTERMS):
        return 'FAIL', 'headterm', 'category head-term owned by a collection page — strengthen the collection, a new article would cannibalise it'

    # ALREADY-COVERED: we have an article about this brand + product category already. A new one
    # would cannibalise it; the many sub-intent query variants ("<brand> nutrition facts / review /
    # macros / is it good") should all be won by that ONE existing page (refresh it, don't recreate).
    if brand_hit and articles:
        bn = _norm(brand_hit)
        qnouns = {w for w in re.findall(r'[a-z0-9]+', t) if w in PRODUCT_NOUNS}
        for blob, toks in _article_index(articles):
            if bn in blob and (qnouns & toks or not qnouns):
                shared = qnouns & toks
                return 'FAIL', 'covered', (f'brand "{brand_hit}"' + (f' + {"/".join(sorted(shared))}' if shared else '')
                    + ' is already covered by an existing article — refresh it or pick a genuinely distinct product/angle, do not create a near-duplicate')

    # dead flavour/recipe variant with no brand + no strong intent
    flav = next((f for f in DEAD_FLAVOUR if re.search(r'\b'+re.escape(f), t)), None)
    if flav and not brand_hit:
        return 'FAIL', 'flavour', f'flavour/recipe variant "{flav}" with no stocked brand — this pattern earns ~0 SG clicks (dead content)'

    # winning shape: specific stocked brand + review/buy intent
    if brand_hit and has_any(t, INTENT):
        return 'PASS', 'brand_intent', f'winning pattern — specific stocked brand ("{brand_hit}") + commercial/review intent'

    # brand named but no explicit intent word (still likely a product page) -> pass, softer
    if brand_hit:
        return 'PASS', 'brand', f'names a stocked brand ("{brand_hit}") — product/brand page, viable'

    # everything else: a genuine ingredient/how-to gap can be fine, but no clear winner signal
    return 'REVIEW', 'review', 'no stocked-brand + intent signal and not clearly dead — confirm it fills a real demand gap before writing'


def _load(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default


def self_check():
    arts = _load(f"{ROOT}/existing_articles.json", [])
    # (topic, sg_imp, articles, want). PASS cases use [] to test the winner-shape logic in isolation
    # (with the real catalog they'd correctly be 'covered' — we already have Atlas/Myprotein pages).
    cases = [
        ("Atlas Whey Review: Is It Worth It in {{MARKET}}? (2026)", None, [], 'PASS'),   # winner shape
        ("Myprotein vs Optimum Nutrition: Which is Best?", None, [], 'PASS'),           # winner shape
        ("coffee protein shakes {{market}}", None, arts, 'FAIL'),
        ("banana protein powder {{market}}", None, arts, 'FAIL'),
        ("best protein powder {{market}}", None, arts, 'FAIL'),        # collection head-term
        ("supplements {{market}}", None, arts, 'FAIL'),
        ("some niche topic", 5, arts, 'FAIL'),                        # demand floor
        ("KSM-66 Ashwagandha {{MARKET}}: Benefits & Dosage", None, arts, 'REVIEW'),  # ingredient gap, no brand
        ("mutant whey isolate", None, arts, 'FAIL'),                  # brand+product we already cover
        ("meiji high protein milk nutrition facts", None, arts, 'REVIEW'),  # not a stocked brand -> human decides
        ("Owala Outlet {{MARKET}}", None, [], 'FAIL', 2.6),            # we already rank pos 2.6 -> cannibalise
        ("Amazing Grass Green Superfood Review", None, [], 'PASS', 17.1),  # weak rank + stocked brand -> genuine
    ]
    ok = True
    for topic, imp, a, want, *rest in cases:
        p = rest[0] if rest else None
        v, code, why = assess(topic, sg_imp=imp, articles=a, pos=p)
        flag = '✓' if v == want else '✗'
        if v != want:
            ok = False
        print(f"  {flag} [{v:6}] want {want:6} — {topic[:48]}  ({why[:60]})")
    assert ok, "self-check failed"
    print("self-check PASSED")


def main():
    if '--self-check' in sys.argv:
        self_check(); return
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print("usage: topic_fitness.py \"topic\" [--sg-imp N] | --self-check"); sys.exit(2)
    topic = args[0]
    imp = None
    if '--sg-imp' in sys.argv:
        imp = int(sys.argv[sys.argv.index('--sg-imp') + 1])
    arts = _load(f"{ROOT}/existing_articles.json", [])
    colls = _load(f"{ROOT}/existing_collections.json", [])
    v, code, why = assess(topic, sg_imp=imp, articles=arts, collections=colls)
    print(f"{v} [{code}]: {why}")
    sys.exit({'PASS': 0, 'REVIEW': 2, 'FAIL': 1}[v])


if __name__ == '__main__':
    main()

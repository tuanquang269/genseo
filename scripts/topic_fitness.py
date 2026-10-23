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
  FAIL  brand_rules: a FloraFresh formula claim its Supplement Facts label does not support
        [florafresh-formula], a FusiForce pack-count or dose claim the label whitelist
        does not list [fusiforce-label], a Premium Himalayan Shilajit Gummies
        pack-count or milligram claim the label whitelist does not list
        [shilajit-gummies-label], a Shilajit Shockwave milligram, serving, or other dose the
        pack label does not list [shockwave-label], a Pure Shilajit Gold Resin milligram,
        serving, volume, weight, day-supply, or other dose its pack label does not list
        [gold-resin-label], a ShilaSource resin milligram, serving, volume, weight,
        fulvic percentage, mineral count, day-supply, or other dose its pack label
        does not list [shilasource-resin-label], a Turkesterone Advanced Formula
        milligram, serving, capsule count, day-supply, or other dose its pack
        label does not list [turkesterone-label], or an AgeAura SKU other than the
        NMN + TMG Complex [ageaura-sku]
  FAIL  near-duplicate of an existing live article (we already have the page)
  FAIL  bare category head-term a COLLECTION owns ("best protein powder us") -> the
        collection page should win it, a new article would cannibalise it
  FAIL  flavour/recipe variant with no stocked brand + no purchase intent (the dead pattern)
  FAIL  explicit SG demand floor breached (--sg-imp below MIN_IMP)
  PASS  names a stocked brand AND has review/comparison/buy intent (the winning pattern)
  REVIEW everything else (genuine ingredient/how-to gap, or ambiguous — a human/Claude decides)

Usage:
  topic_fitness.py "Atlas Whey Review US" [--sg-imp 140]
  topic_fitness.py "coffee protein shake us"
  topic_fitness.py --self-check
"""
import json, re, sys
import brand_rules as br
import florafresh_rules as ff
import fusiforce_rules as fu
import gold_resin_rules as gr
import shilajit_gummies_rules as sg
import shilasource_resin_rules as sr
import shockwave_rules as sw
import turkesterone_rules as tk

ROOT = "/Users/kevinkreative/genseo"
MIN_IMP = 20          # below this SG demand, not worth a dedicated page
DUP_JACCARD = 0.72    # significant-word overlap with an existing title = duplicate
RANK_FLOOR = 8        # if we already rank SG pos <= this, a NEW page cannibalises the winner (refresh instead)

# brands we actually stock (lowercase substrings). Names a specific entity => winner-shaped.
# wellnessnest.co is an OWN-BRAND store: only house brands + their hero ingredients count
# as stocked entities. (Donor retailer's 60-brand list removed 2026-08-07.)
STOCKED_BRANDS = {
 'shilasource','shilajit','fusiforce','florafresh','menomate','turkesterone',
 'ageaura','wellness nest','wellnessnest','nmn','tmg',
 'creatine gummies','vaginal probiotic','feminine probiotic','menopause probiotic',
}
# Urolithin A and longevity peptides are not stocked promotion targets. AgeAura is the
# NMN + TMG Complex only — brand_rules.assess() FAIL-closes any topic that names another SKU.
_DONOR_BRANDS_REMOVED = {
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
# Audience / intent modifiers that make a topic a genuinely different article from the general
# brand page. "shilajit benefits" and "shilajit benefits for men" are two articles with two
# buyers and two SERPs; the blunt brand-substring rule below would kill the second one purely
# because the catalog contains any page mentioning the brand. The Jaccard near-duplicate check
# earlier in assess() is the real guard against recreating a page we have.
SEGMENT_MODIFIERS = [
 'for men','for women','for beginners','for seniors','for athletes','for runners','for fertility',
 'over 40','over 50','over 60','side effects','dosage','how to take','how much','how long',
 'vs','versus','before bed','morning or night','empty stomach','with food',
 # Buy intent, added 2026-08-12. It was missing, and the omission was expensive: "where to buy
 # wellness nest shilajit" hit the 'covered' branch as a hard FAIL — write nothing — even though
 # no live title covers buy intent (checked: 0 of 61 articles contain "where to buy", "buy",
 # "price" or "cost"). Every other distinct intent here gets REVIEW, i.e. "write it only if the
 # ticket brief greenlit this exact topic", which is the correct answer for a commercial-intent
 # page that no existing article competes with. This does NOT loosen cannibalisation: the moment
 # one buy-intent article exists, seg_taken flips and the branch goes back to FAIL.
 'where to buy','where can i buy','buy','price','cost','how much does',
]
# category head-terms a COLLECTION owns — a new article cannibalises them
COLLECTION_HEADTERMS = [
 'best protein powder','protein powder us','buy protein powder','best whey','whey protein powder',
 'best creatine','creatine us','best pre workout','best pre-workout','best fat burner',
 'best collagen','best multivitamin','best mass gainer','mass gainer us','supplements us',
 'best supplement brand','best supplement store','best protein brand','best amino','best bcaa',
 'protein bars us','best protein bar',
]

def sig_words(s):
    stop = {'in','of','the','for','a','to','vs','and','with','is','it','us','best','review','2026','2025','sg','guide','ultimate'}
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

    ff_bad = ff.violations(topic)
    if ff_bad:
        return ('FAIL', 'florafresh-formula',
                'FloraFresh follows its Supplement Facts label (' + ff.STRAIN + ', ' + ff.CFU
                + ' per 2 gummies), not the PDP description: ' + '; '.join(ff_bad))

    fu_bad = fu.violations(topic)
    if fu_bad:
        return ('FAIL', 'fusiforce-label',
                'FusiForce follows its pack label (' + fu.LABEL_LINE + '); '
                '84 gummies, milligram amounts, serving counts, and ginseng are not on that whitelist: '
                + '; '.join(fu_bad))

    sg_bad = sg.violations(topic)
    if sg_bad:
        return ('FAIL', 'shilajit-gummies-label',
                'Premium Himalayan Shilajit Gummies follow the pack label (' + sg.LABEL_LINE
                + '); a 30-serving panel and milligram amounts not in that file fail closed: '
                + '; '.join(sg_bad))

    sw_bad = sw.violations(topic)
    if sw_bad:
        return ('FAIL', sw.CODE,
                'Shilajit Shockwave follows the pack label (' + sw.LABEL_LINE
                + '); a milligram amount, serving count, or other dose not in that file fails closed: '
                + '; '.join(sw_bad))

    gr_bad = gr.violations(topic)
    if gr_bad:
        return ('FAIL', gr.CODE,
                'Pure Shilajit Gold Resin follows the pack label (' + gr.LABEL_LINE
                + '); a milligram amount, a different serving count, volume, weight, day-supply, '
                + 'or other dose not in that file fails closed: '
                + '; '.join(gr_bad))

    sr_bad = sr.violations(topic)
    if sr_bad:
        return ('FAIL', sr.CODE,
                'ShilaSource Himalayan Shilajit Resin follows the pack label (' + sr.LABEL_LINE
                + '); a milligram amount, a different serving count, volume, weight, fulvic percentage, '
                + 'mineral count, day-supply, or other dose not in that file fails closed: '
                + '; '.join(sr_bad))

    tk_bad = tk.violations(topic)
    if tk_bad:
        return ('FAIL', tk.CODE,
                'Turkesterone Advanced Formula follows the pack label (' + tk.LABEL_LINE
                + '); a milligram amount, a serving count, a different capsule count, a day-supply, '
                + 'or other dose not in that file fails closed: '
                + '; '.join(tk_bad))

    if br.assess(topic).action == "deny":
        return ('FAIL', 'ageaura-sku',
                'AgeAura promotes only the Pure NMN + TMG NAD Complex (' + br.AGEAURA_OK
                + '); this topic names a banned SKU')

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
        seg = next((s for s in SEGMENT_MODIFIERS
                    if re.search(r'\b' + re.escape(s) + r'\b', t)), None)
        # `seg_taken` asks "has this SAME BRAND already had its <segment> article written?" — so the
        # search has to be brand-scoped. Until 2026-08-13 it scanned every title on the blog, which
        # made an unrelated page veto the segment: "Shilajit for Women" came back FAIL[covered]
        # because "Creatine for Women Over 40" contains "for women", and "Turkesterone vs
        # Ecdysterone" because "Creatine Gummies vs Powder" contains "vs". Both are genuine gaps
        # that cannibalise nothing. The blunter the shared modifier ("vs", "how much", "buy"), the
        # more topics one page silently locked out — and with "vs" and "for women" both spent, most
        # of the comparison and audience long-tail was unreachable, which is a large part of why
        # the ticket queue looked exhausted. Scoping it to articles that actually mention the brand
        # keeps the anti-cannibalisation guarantee exactly as strong: the page that would compete
        # is by definition a page about the same brand.
        seg_taken = bool(seg) and any(
            re.search(r'\b' + re.escape(seg) + r'\b', a.get('title', '').lower())
            for a in articles
            if bn in _norm(a.get('title', '') + ' ' + a.get('handle', '')))
        for blob, toks in _article_index(articles):
            if bn in blob and (qnouns & toks or not qnouns):
                if seg and not seg_taken:
                    return 'REVIEW', 'covered-segment', (
                        f'brand "{brand_hit}" has a general article, but "{seg}" is an audience/intent '
                        'no existing title covers — distinct enough to write IF the ticket brief '
                        'greenlit this exact topic; link the general page instead of restating it')
                shared = qnouns & toks
                return 'FAIL', 'covered', (f'brand "{brand_hit}"' + (f' + {"/".join(sorted(shared))}' if shared else '')
                    + ' is already covered by an existing article — refresh it or pick a genuinely distinct product/angle, do not create a near-duplicate')

    # dead flavour/recipe variant with no brand + no strong intent
    flav = next((f for f in DEAD_FLAVOUR if re.search(r'\b'+re.escape(f), t)), None)
    if flav and not brand_hit:
        return 'FAIL', 'flavour', f'flavour/recipe variant "{flav}" with no stocked brand — this pattern earns ~0 US clicks (dead content)'

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


_SEG_FIXTURE = [
    {'title': 'Shilajit Resin: What It Is and How to Use It', 'handle': 'shilajit-resin-guide'},
    {'title': 'Shilajit Benefits for Women: What Changes After 40', 'handle': 'shilajit-women-40'},
]


def self_check():
    arts = _load(f"{ROOT}/existing_articles.json", [])
    # (topic, sg_imp, articles, want). PASS cases use [] to test the winner-shape logic in isolation
    # (with the real catalog they'd correctly be 'covered' — we already have Atlas/Myprotein pages).
    cases = [
        ("FusiForce Creatine Gummies Review: Worth It? (2026)", None, [], 'PASS'),  # winner shape, house brand
        ("Turkesterone vs Ecdysterone: Which is Best?", None, [], 'PASS'),          # winner shape
        ("coffee protein shakes us", None, arts, 'FAIL'),
        ("banana protein powder us", None, arts, 'FAIL'),
        ("best protein powder us", None, arts, 'FAIL'),        # collection head-term
        ("supplements us", None, arts, 'FAIL'),
        ("some niche topic", 5, arts, 'FAIL'),                        # demand floor
        ("KSM-66 Ashwagandha US: Benefits & Dosage", None, arts, 'REVIEW'),  # ingredient gap, no brand
        ("shilajit benefits for health and vitality", None, arts, 'FAIL'),   # brand+topic we already cover
        # Both covered-segment branches, on a FIXTURE not the live catalog. This case used to run
        # against `arts` and silently went stale the moment we published "Shilajit Benefits for
        # Men" — the gate was then right and the test was wrong, which is the worst way round.
        ("shilajit benefits for men", None, _SEG_FIXTURE, 'REVIEW'),   # segment no existing title owns
        ("shilajit benefits for women", None, _SEG_FIXTURE, 'FAIL'),   # segment an existing title owns
        ("meiji high protein milk nutrition facts", None, arts, 'REVIEW'),  # not a stocked brand -> human decides
        ("FloraFresh Vaginal Probiotics US", None, [], 'FAIL', 2.6),  # we already rank pos 2.6 -> cannibalise
        ("MenoMate Menopause Probiotic Review", None, [], 'PASS', 17.1),  # weak rank + stocked brand -> genuine
        ("Urolithin A benefits review", None, [], 'FAIL'),                 # banned AgeAura SKU
        ("AgeAura review", None, [], 'PASS'),                              # brand is allowed; ticket builder locks the SKU
        ("FloraFresh 1 billion CFU review", None, [], 'FAIL'),             # retired count (label: 15B CFU)
        ("FloraFresh 1B CFU review", None, [], 'FAIL'),                    # same retired count
        ("FloraFresh 15B CFU review", None, [], 'PASS'),                   # Kevin 2026-10-21 label count
        ("FloraFresh sugar free gummies review", None, [], 'FAIL'),        # label: maltitol + isomalt
        ("FloraFresh Bacillus coagulans SNZ-1969 review", None, [], 'PASS'),  # the label strain
        ("FusiForce 84 gummies review", None, [], 'FAIL'),                     # pack label is 90 gummies
        ("FusiForce creatine monohydrate gummies review", None, [], 'PASS'),   # whitelist identity
        ("Premium Himalayan Shilajit Gummies 30 servings review", None, [], 'FAIL'),  # not on the pack label
        ("Premium Himalayan Shilajit Gummies review", None, [], 'PASS'),       # 60 gummies, no invented panel
        ("Shilajit Shockwave 500 mg review", None, [], 'FAIL'),                # pack label has no milligram
        ("Shilajit Shockwave review", None, [], 'PASS'),                       # identity only, no invented dose
        ("Pure Shilajit Gold Resin 500 mg review", None, [], 'FAIL'),          # pack label has no milligram
        ("Pure Shilajit Gold Resin review", None, [], 'PASS'),                 # whitelist lines only
        ("ShilaSource Himalayan Shilajit Resin 500 mg review", None, [], 'FAIL'),  # pack label has no milligram
        ("ShilaSource Himalayan Shilajit Resin review", None, [], 'PASS'),     # whitelist lines only
        ("Turkesterone Advanced Formula 500 mg review", None, [], 'FAIL'),     # pack label has no milligram
        ("Turkesterone Advanced Formula review", None, [], 'PASS'),            # front lines only
        ("Turkesterone vs Ecdysterone 500 mg", None, [], 'PASS'),              # ingredient trial dose, not the SKU
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

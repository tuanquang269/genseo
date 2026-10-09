#!/usr/bin/env python3
"""
build_rich_tickets.py — Generate Jun26-120-tickets.md with a PRE-DECIDED rich brief per
ticket, so the cheap Antigravity model executes instead of guessing. Decisions banked here:
collection links, content angle/intent, comparison-table subject, assigned author, priority
brands to feature, dedup note. Sourced from sg_demand_runway.csv, deduped vs ALL_ARTICLES.csv.
"""
import csv, re
import brand_rules as br

ROOT="/Users/kevinkreative/genseo"

# ---- live collections (verified present on store) ----
COLLECTIONS=set("all allmax-nutrition amazing-grass antioxidant-support applied-nutrition barebells blenderbottle bsn california-gold-nutrition casein-protein cellucor childrens-health collagen creatine digestive-support doctors-best dymatize-nutrition evlution-nutrition fat-burner garden-of-life general-health ghost glutamine goli gym-accessories herbal-plant-supplements hydroxycut immune-support intra-workout jnx-sports kaged-muscle l-carnitine labrada mass-gainer mens-health mrm musclepharm muscletech mutant myprotein-us natrol naturade natural-factors natures-way neocell now-foods nutrex-research nutricost omega-3-fish-oils optimum-nutrition-us orgain owala perfect-sports plant-based-protein post-workout pre-workout protein-bar-meal-replacement pvl-nutrition quest-protein-bar rainbow-light rsp-nutrition science-in-sport shakers-bottle sleep-improvement sports-research vitamin-wellness whey-protein womens-health xtend youtheory yumearth".split())

# ---- PRIORITY BRANDS (verified live). Ordered by business priority. ----
# brand -> (collection-or-None, product-keywords-for-context, relevant-topic-keywords)
PRIORITY_BRANDS=[
 ("Mutant","mutant",["whey","protein","mass gainer","creatine","pre workout","bcaa","iso"]),
 ("PVL","pvl-nutrition",["whey","isolate","protein","creatine","iso gold"]),
 ("Ghost","ghost",["whey","protein","pre workout","energy","bcaa","amino","legend"]),
 ("JNX Sports","jnx-sports",["pre workout","creatine","fat burner","the curse","omen","ripper"]),
 ("Pure Protein",None,["protein bar","whey","protein crisp","popped","snack","bar"]),  # no collection -> link products
 ("Dymatize","dymatize-nutrition",["whey","iso 100","isolate","protein","mass gainer","casein"]),
 ("PB2",None,["peanut butter","pb2","powdered peanut","snack"]),  # no collection
]
# NOT yet live — never link until they arrive:
BRANDS_NOT_LIVE=["Bronson","Transparent Labs"]

# ---- theme -> primary collection + author (by expertise) ----
# author roster (live /pages/) assigned by editorial coverage
# Derived from roster.json (small team: every expertise key maps to the first
# roster author until Kevin assigns per-topic owners). Empty roster -> empty dict,
# and ticket generation fails loudly instead of inventing a byline.
import genseo_roster
AUTHORS={}
if genseo_roster.NAMES:
    _h, _n = next(iter(genseo_roster.NAMES.items()))
    AUTHORS={k: f"{_n} (/pages/{_h})" for k in
             ("clinical","sports","dietetics","training","fitness","medical","founder")}

# theme rules: (match keywords) -> (collections[], author-key, table-subject)
THEME_RULES=[
 ("Collagen & Beauty",["collagen","neocell","peptide","beauty","skin","youtheory"],
    ["collagen"], "dietetics", "collagen products you stock (type, dose, format)"),
 ("Sleep & Recovery",["sleep","melatonin","olly","rest","insomnia"],
    ["sleep-improvement","natrol"], "clinical", "sleep supplements (ingredient, dose, timing)"),
 ("Immunity & Wellness",["immune","immunity","vitamin c","zinc","sambucol","elderberry"],
    ["immune-support","vitamin-wellness"], "clinical", "immune supplements compared"),
 ("Multivitamin & General Health",["multivitamin","vitamin","mens","womens","alive","mineral","general health","wellness","greens"],
    ["vitamin-wellness","general-health"], "clinical", "multivitamins (coverage, dose, who it's for)"),
 ("Fish Oil & Omega",["fish oil","omega","krill","epa","dha"],
    ["omega-3-fish-oils"], "clinical", "omega-3 products (EPA/DHA per serving, price)"),
 ("Digestive & Gut",["probiotic","iotics","digest","gut","fibre","enzyme"],
    ["digestive-support"], "clinical", "digestive/probiotic options"),
 ("Mass Gainer & Bulking",["mass gainer","gainer","serious mass","bulk","pro gainer","combat xl","weight gain"],
    ["mass-gainer"], "training", "mass gainers (calories, protein, price per serving)"),
 ("Creatine",["creatine"],
    ["creatine"], "sports", "creatine products (form, dose, price per serving)"),
 ("Pre-Workout & Energy",["pre workout","preworkout","energy gel","gu energy","pump","caffeine","quadralean","thermogenic","the curse","omen"],
    ["pre-workout"], "training", "pre-workouts (caffeine, key actives, focus vs pump)"),
 ("Fat Burner",["fat burn","thermogenic","hydroxycut","weight loss","lean","ripped"],
    ["fat-burner"], "medical", "fat burners (stimulant vs non-stim, actives)"),
 ("Protein Bars & Snacks",["protein bar","bars","crisp","snack","peanut butter","pb2","cookie","wafer","popped"],
    ["protein-bar-meal-replacement"], "dietetics", "protein bars/snacks (protein, sugar, taste)"),
 ("Meal Replacement",["meal replacement","mrp","shake meal"],
    ["protein-bar-meal-replacement"], "dietetics", "meal replacement options (calories, protein, convenience)"),
 ("Shaker & Accessories",["owala","blender bottle","shaker","tritan","radian","bottle","water bottle","insulated"],
    ["owala","blenderbottle","shakers-bottle"], "fitness", "shaker/bottle models (capacity, material, price)"),
 ("Casein & Slow Protein",["casein","slow protein","night protein"],
    ["casein-protein"], "sports", "casein options (slow-release, dose, price)"),
 ("Plant Protein",["plant protein","vegan","pea protein","soy protein","rice protein"],
    ["plant-based-protein"], "dietetics", "plant proteins (source blend, complete profile, taste)"),
 ("Store & Brand Intent",["supplement store","supplement shop","online supplement","gym supplement","sports supplement","shop nutrition","purchase vitamins","trusted","premium","science backed","brand us","nutrition supplements","health supplement"],
    ["protein-powder","creatine","vitamin-wellness"], "founder", "top categories & priority brands we carry (with $price ranges)"),
 ("Amino & BCAA",["bcaa","eaa","amino","glutamine","intra workout","xtend"],
    ["best-amino-acids","intra-workout"], "sports", "amino/BCAA products (ratio, EAAs, dose)"),
]
DEFAULT=("Whey & Protein",["whey-protein","protein-powder"],"sports","whey proteins (type, protein per serving, price)")

def theme_for(q):
    ql=q.lower()
    for name,kws,colls,author,table in THEME_RULES:
        if any(k in ql for k in kws):
            return name,[c for c in colls if c in COLLECTIONS],author,table
    return DEFAULT[0],[c for c in DEFAULT[1] if c in COLLECTIONS],DEFAULT[2],DEFAULT[3]

# module-level rotation counter so brand naming is fair across all 120 tickets
_BRAND_USE={b[0]:0 for b in PRIORITY_BRANDS}
def brands_for(q, theme_table):
    """Which priority brands naturally fit this topic? (in-stock only).
    Returns up to 3, but rotates so lower-priority-but-relevant brands (Dymatize, Pure
    Protein, PB2) also get featured across the schedule instead of always Mutant/PVL/Ghost."""
    ql=(q+" "+theme_table).lower()
    fits=[(name,coll) for name,coll,kws in [(b[0],b[1],b[2]) for b in PRIORITY_BRANDS]
          if any(k in ql for k in kws)]
    if len(fits)<=3:
        for n,_ in fits: _BRAND_USE[n]+=1
        return fits
    # >3 fit: keep business order but rotate the tail so all relevant brands surface over time.
    # Always keep the single top-priority match, then pick the 2 least-used-so-far among the rest.
    head=[fits[0]]
    rest=sorted(fits[1:], key=lambda x:_BRAND_USE[x[0]])[:2]
    chosen=head+rest
    for n,_ in chosen: _BRAND_USE[n]+=1
    return chosen

def angle_for(q, pos):
    ql=q.lower()
    pos=float(pos)
    if any(w in ql for w in ["store","shop","online","buy","where","purchase","brand us","trusted","premium"]):
        return "Commercial/transactional — position Your Brand as the answer; lead with authenticity, range, fast SG delivery, price."
    if any(w in ql for w in ["review","best","vs","compare","top"]):
        return "Comparison/buying-guide — direct verdict up top, then a comparison table of the options we stock."
    if pos>30:
        return "Foundational/informational — we rank poorly, so go deep: define the term, the science, then which products to buy. Win the answer box."
    return "Informational+commercial — answer the question first, then guide to the right product to buy in SG."

def main():
    import sys as _s
    _in = _s.argv[_s.argv.index('--in')+1] if '--in' in _s.argv else f"{ROOT}/blog_ticket_candidates.csv"
    cands=list(csv.DictReader(open(_in)))
    for r in cands: r['imp']=int(r['imp']); r['pos']=float(r['pos'])
    # dedupe among candidates (keep highest imp per normalized key)
    def key(q):
        s=re.sub(r'[^a-z0-9 ]',' ',q.lower()); return " ".join(sorted(set(w for w in s.split() if len(w)>2)))
    seen={}; uniq=[]
    for r in sorted(cands,key=lambda x:-x['imp']):
        k=key(r['query'])
        if k in seen: continue
        seen[k]=1; uniq.append(r)
    # TOPIC FITNESS filter (2026-07-22, data-derived): drop dead-pattern / already-covered /
    # collection-owned / sub-demand topics BEFORE they become tickets, so the cheap model is never
    # asked to write content our own GSC proves earns ~0 SG clicks. This is the real fix for the
    # flavour-spam: word-set dedup let "coffee shake"/"banana powder" through; this catches them.
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    import topic_fitness as tf
    _arts=tf._load(f"{ROOT}/existing_articles.json",[]); _colls=tf._load(f"{ROOT}/existing_collections.json",[])
    kept=[]; review=[]; dropped={}
    for r in uniq:
        v,code,why=tf.assess(r['query'], sg_imp=r.get('imp'), articles=_arts, collections=_colls, pos=r.get('pos'))
        if v=='FAIL': dropped[code]=dropped.get(code,0)+1; continue
        if v=='REVIEW': review.append((r['query'],why)); continue   # needs human vetting, not auto-fed to the model
        kept.append(r)   # PASS only — the proven winning pattern
    print(f"topic-fitness: auto-ticket {len(kept)} PASS, held {len(review)} for review, dropped {sum(dropped.values())} FAIL {dict(dropped)}")
    if review and len(_sys.argv)>=2:
        rf=_sys.argv[1].rsplit('.md',1)[0]+"-needs-review.txt"
        open(rf,"w").write("# Topic-fitness REVIEW — vet before writing (no clear winner signal)\n"
                           +"\n".join(f"- {q}  — {w}" for q,w in review))
        print(f"  -> {len(review)} review topics written to {_os.path.basename(rf)}")
    uniq=kept
    # secondary keywords: same-theme neighbors
    for r in uniq:
        r['theme'],r['colls'],r['author_key'],r['table']=theme_for(r['query'])
    by_theme={}
    for r in uniq: by_theme.setdefault(r['theme'],[]).append(r)

    tickets=sorted(uniq,key=lambda x:-x['imp'])[:120]
    kept_tickets=[]
    for r in tickets:
        if br.assess(r['query']).action == "deny":
            print(f"brand guard: skipped query {r['query']!r}")
            continue
        kept_tickets.append(r)
    tickets=kept_tickets

    def tc(q):
        small={'in','of','the','for','a','to','vs','and','with'}
        return " ".join(w if w in small else w.capitalize() for w in q.split())

    L=[]
    L.append("# 🗓️ Jun 2026: 120 SG-Demand Content Schedule — RICH BRIEFS")
    L.append("")
    L.append("*Target Geo: US. Source: GSC SG under-served demand (imp≥20, pos>8, 90d), deduped vs 632 existing articles. Each ticket is a pre-decided brief so the model executes instead of guessing.*")
    L.append("")
    L.append("> **How the cron runs this:** \"continue with next N tickets in Jun26-120-tickets.md\". Each invokes `/genseo-auto-publish`, which enforces STEP 0 (live duplicate-check) and STEP 6 (validate_article.py must print ✓ PASS).")
    L.append("")
    L.append("## 🎯 PRIORITY BRANDS (feature these FIRST, naturally — never force into an unrelated topic)")
    L.append("When the topic allows, recommend/compare these in-stock brands before others:")
    L.append("**1. Mutant** · **2. PVL** · **3. Ghost** · **4. JNX Sports** · **5. Pure Protein** · **6. Dymatize** · **7. PB2**")
    L.append("")
    L.append("⛔ **NOT yet in stock — do NOT mention or link (would 404):** Bronson, Transparent Labs. Revisit when they land. (Nutrabio is now IN STOCK — OK to feature.)")
    L.append("")
    L.append("**Quality bar (auto-enforced):** 900–1400 words · answer-first block w/ 'US' · 1 comparison table · 'Where to Buy in the US' + $price · ≥2 collection links · 4 FAQs (≥1 SG) · named author w/ live /pages/ · Article+FAQPage schema · real product links (no 404s) · not a duplicate.")
    L.append("")

    day=0
    for i,r in enumerate(tickets):
        if i%3==0:
            day+=1; L.append(f"## 🌅 Day {day}")
        q=r['query']
        colls=r['colls'] or ["protein-powder"]
        coll_links=" , ".join(f"/collections/{c}" for c in colls[:2])
        secs=[x['query'] for x in by_theme[r['theme']]
              if x['query']!=q and br.assess(x['query']).action != "deny"][:3]
        sec_str=", ".join([q]+secs)
        author=AUTHORS[r['author_key']]
        pb=brands_for(q, r['table'])
        pb_str=", ".join(f"{n}" + (f" (/collections/{c})" if c else " (link products)") for n,c in pb) if pb else "no specific priority brand fits — use the best products you stock"
        angle=angle_for(q, r['pos'])

        block=[
            f"### 📝 Ticket #{i+1} — {r['theme']}: {tc(q)}",
            f"- **Primary keyword**: `{q}`  (SG: {r['imp']} imp/90d @ pos {r['pos']})",
            f"- **Secondary keywords**: `{sec_str}`",
            f"- **Angle**: {angle}",
            f"- **MUST link these collections (≥2)**: `{coll_links}`",
            f"- **Priority brands to feature** (naturally, if relevant): {pb_str}",
            f"- **Comparison table subject**: {r['table']}",
            f"- **Assigned author**: {author}",
            f"- **Dedup**: we already have articles near this keyword — take the angle above, do NOT rewrite an existing one (STEP 0 will verify).",
            f"- **Action**: [ ] PENDING",
            "**🤖 Auto-Publish Trigger Prompt:**",
            "```markdown",
            f"/genseo-auto-publish CREATE A [NEW ARTICLE]. Title Focus: \"A Creative and Engaging SEO Title for '{tc(q)}' in the US\". Target Keywords: {sec_str}. ANGLE: {angle} MUST link collections: {coll_links}. Feature priority brands first if relevant: {pb_str}. Comparison table: {r['table']}. Author: {author}. Default BLOG_ID is 104008483131.",
            "```",
            "",
        ]
        try:
            block=br.prepare_ticket("\n".join(block)).splitlines()
        except br.GuardError as e:
            print(f"brand guard: skipped ticket {q!r}: {e}")
            continue
        L.extend(block)

    import sys, os
    _pos = [a for i,a in enumerate(sys.argv[1:],1)
            if not a.startswith('--') and sys.argv[i-1] != '--in']
    if not _pos:
        print("usage: build_rich_tickets.py <output.md> [--in candidates.csv]   (refuses to overwrite)"); sys.exit(1)
    out = _pos[0]
    if os.path.exists(out):
        print(f"✗ {out} exists — will not overwrite a ticket queue (DONE markers would be lost). Pick a new name."); sys.exit(1)
    open(out, "w").write("\n".join(L))

    from collections import Counter
    print(f"Built {len(tickets)} rich-brief tickets across {day} days")
    print("Theme distribution:", dict(Counter(t['theme'] for t in tickets)))
    print("Author distribution:", dict(Counter(AUTHORS[t['author_key']].split('(')[0].strip() for t in tickets)))
    # brand coverage
    bc=Counter()
    for t in tickets:
        for n,c in brands_for(t['query'], t['table']): bc[n]+=1
    print("Priority-brand fit counts:", dict(bc))

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Task 5 (Kevin 2026-10-08 14:27 ICT): build the 3 Wellness Nest listicle specs from the AgeAura v3 skeleton.
Facts: PDP /products/<h>.js + PDP text (2026-10-08), Europe PMC abstracts, state/trustpilot/wellnessnest.json (verbatim)."""
import json, copy, os, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import brand_rules
ROOT = os.path.expanduser("~/genseo")
base = json.load(open(f"{ROOT}/landing_drafts/ageaura-nmn-listicle-261008.json"))
TP = {r["id"]: r for r in json.load(open(f"{ROOT}/state/trustpilot/wellnessnest.json"))["reviews"]}
def rv(i, verified_label=True):
    r = TP[i]; assert r["rating"] >= 4
    d = datetime.date.fromisoformat(r["published"][:10])
    o = {"stars": r["rating"], "quote": r["text"].strip(), "name": r["name"], "meta": f"{r['country']} · {d.strftime('%b %Y')}", "url": f"https://www.trustpilot.com/reviews/{i}"}
    if r.get("verified"): o["verified"] = True
    return o
def A(url, txt): return f'<a href="{url}" target="_blank" rel="noopener">{txt}</a>'
D = lambda d: f"https://doi.org/{d}"
KREIDER, HULTMAN, PEREIRA, CHILI, LIN, ANTONIO = map(D, ["10.1186/s12970-017-0173-z", "10.1152/jappl.1996.81.1.232", "10.3390/jfmk11010105", "10.2147/OAJSM.S123529", "10.3389/fnut.2026.1921827", "10.1186/s12970-021-00412-w"])
PANDIT, KELLER, PINGALI, YADAV, SAPER, STOHS, CHANDRA = map(D, ["10.1111/and.12482", "10.1186/s12970-019-0270-2", "10.1016/j.phymed.2022.154334", "10.7759/cureus.102372", "10.1001/jama.300.8.915", "10.1002/ptr.5018", "10.4103/0253-7176.106022"])
HOWTO = "https://wellnessnest.co/blogs/news/how-to-take-shilajit-resin-dissolve-it-right-us-2026"
SRC = {
 KREIDER: "Kreider RB et al. International Society of Sports Nutrition position stand: safety and efficacy of creatine supplementation in exercise, sport, and medicine. J Int Soc Sports Nutr 2017;14:18. doi:10.1186/s12970-017-0173-z",
 HULTMAN: "Hultman E, Söderlund K, Timmons JA, Cederblad G, Greenhaff PL. Muscle creatine loading in men. J Appl Physiol 1996;81(1):232-237. doi:10.1152/jappl.1996.81.1.232",
 PEREIRA: "Pereira F, Forbes SC, Romano V, Christopher P, Santana JC, Antonio J. Effects of Creatine Monohydrate Gummies on Performance and Body Composition in Female Beach Volleyball Athletes. J Funct Morphol Kinesiol 2026;11(1):105. doi:10.3390/jfmk11010105",
 CHILI: "Chilibeck PD, Kaviani M, Candow DG, Zello GA. Effect of creatine supplementation during resistance training on lean tissue mass and muscular strength in older adults: a meta-analysis. Open Access J Sports Med 2017;8:213-226. doi:10.2147/OAJSM.S123529",
 LIN: "Lin Y, Zhu W, Hong B. Effects of creatine supplementation on exercise performance, physiological outcomes, and body composition in females engaged in exercise or training: a systematic review and multilevel meta-analysis. Front Nutr 2026;13:1921827. doi:10.3389/fnut.2026.1921827",
 ANTONIO: "Antonio J et al. Common questions and misconceptions about creatine supplementation: what does the scientific evidence really show? J Int Soc Sports Nutr 2021;18(1):13. doi:10.1186/s12970-021-00412-w",
 PANDIT: "Pandit S et al. Clinical evaluation of purified Shilajit on testosterone levels in healthy volunteers. Andrologia 2016;48(5):570-575. doi:10.1111/and.12482",
 KELLER: "Keller JL, Housh TJ, Hill EC, Smith CM, Schmidt RJ, Johnson GO. The effects of Shilajit supplementation on fatigue-induced decreases in muscular strength and serum hydroxyproline levels. J Int Soc Sports Nutr 2019;16(1):3. doi:10.1186/s12970-019-0270-2",
 PINGALI: "Pingali U, Nutalapati C. Shilajit extract reduces oxidative stress, inflammation, and bone loss to dose-dependently preserve bone mineral density in postmenopausal women with osteopenia: a randomized, double-blind, placebo-controlled trial. Phytomedicine 2022;105:154334. doi:10.1016/j.phymed.2022.154334",
 YADAV: "Yadav D et al. Safety and Efficacy of TruBlk Shilajit Resin Supplementation on Physical Performance and Blood Biomarkers in Healthy Adults: A 28-Day Open-Label Pilot Study. Cureus 2026;18(1):e102372. doi:10.7759/cureus.102372",
 SAPER: "Saper RB et al. Lead, mercury, and arsenic in US- and Indian-manufactured Ayurvedic medicines sold via the Internet. JAMA 2008;300(8):915-923. doi:10.1001/jama.300.8.915",
 STOHS: "Stohs SJ. Safety and efficacy of shilajit (mumie, moomiyo). Phytother Res 2014;28(4):475-479. doi:10.1002/ptr.5018",
 CHANDRA: "Chandrasekhar K, Kapoor J, Anishetty S. A prospective, randomized double-blind, placebo-controlled study of safety and efficacy of a high-concentration full-spectrum extract of ashwagandha root in reducing stress and anxiety in adults. Indian J Psychol Med 2012;34(3):255-262. doi:10.4103/0253-7176.106022",
 HOWTO: "Wellness Nest. How to Take Shilajit Resin: Dissolve It Right (US 2026). wellnessnest.co, October 5, 2026.",
}
TRUST_SRC = "TrustScore/count: state/trustpilot/wellnessnest.json (trustpilot.com/review/wellnessnest.co, read 2026-10-08). Guarantee + free-shipping threshold: /policies/refund-policy and the site ticker."
def img(slug, n): return f"tmp_images/landing-{slug}/{n}.webp"
LIVE = {"fusiforce-creatine-listicle-261008": "creatine-gummies-research",
        "shilasource-resin-listicle-261008": "shilajit-resin-research",
        "shilajit-gummies-listicle-261008": "shilajit-gummies-research"}
def page(slug, product_handle, pname, d):
    try:
        product_handle, _how = brand_rules.resolve_handle(product_handle)
    except brand_rules.GuardError as e:
        raise SystemExit("✗ AgeAura guard: " + str(e))
    s = copy.deepcopy(base)
    for k in ("live", "live_approved"): s.pop(k, None)
    pdp = f"https://wellnessnest.co/products/{product_handle}"
    live_handle = LIVE.get(slug)   # Kevin GO 2026-10-08 15:51 ICT: clean customer-facing handle (301 from the gsl-preview handle)
    if live_handle:
        s.update({"live": True, "live_approved": "Kevin 2026-10-08 15:51 ICT"})
    s.update({"store": "wellnessnest", "slug": slug, "handle": live_handle or f"gsl-preview-{slug}", "created": "2026-10-08", "daily": False,
              "title": d["title"], "meta_description": d["meta"], "style": "premium", "template_suffix": d.get("suffix", "gsl-ref-listicle-v4")})
    s["hero"] = {"accent": d["accent"], "title": d["htitle"], "summary_html": "<strong>Summary:</strong> " + d["summary"],
                 "kicker": f"Evidence review · {len(d['sources'])} studies cited", "image": img(slug, d.get("hero_img", "hero")), "alt": d["hero_alt"],
                 "chip": d["chip"], "cta": {"label": "SEE INGREDIENTS", "href": pdp},
                 "image_note": "Generated with the real pack as reference (ima2, article_images.py --qc, cutout of PDP image 0), label gate PASS (scripts/landing_label_gate.py vs product_refs/%s.label.json), mark zoom-checked at 2x, 2026-10-08." % product_handle,
                 "source": d["chip_src"], "focal_y": d.get("focal_y", 0.3)}
    s["items"] = d["items"]
    s["bridge"] = {"title": d["bridge_title"], "body": d["bridge"], "image": img(slug, d.get("ledge_img", "ledge")), "alt": d["ledge_alt"]}
    ex = rv(d["expert_id"])
    s["expert"] = {"title": "TrustScore 4.2 from 1,144 Trustpilot Reviews", "stars": ex["stars"], "quote": ex["quote"],
                   "author": f"{ex['name']} · Wellness Nest customer on Trustpilot",
                   "source": f"{ex['url']} ({ex['stars']}-star review, published {TP[d['expert_id']]['published'][:10]}, verbatim; TrustScore 4.2 and 1,144 reviews as displayed on trustpilot.com/review/wellnessnest.co, read 2026-10-08). Store-level review, not a product-effect claim.",
                   "image": img(slug, d.get("dark_img", "dark")), "alt": d["dark_alt"],
                   "reviews": [rv(i) for i in d["review_ids"]],
                   "reviews_source": "Verbatim 4-5 star Trustpilot reviews from state/trustpilot/wellnessnest.json (ids in URLs); 'Verified' only where Trustpilot marks the review verified. Service/quality reviews, no product-effect claims."}
    o = d["offer"]
    s["offer"] = {"pill": o["pill"], "accent": o["accent"], "title": o["title"], "sub": o["sub"], "cta": "SEE INGREDIENTS", "href": pdp,
                  "meta": ["<b>90-Day</b> Guarantee", "<b>FREE</b> shipping $70+"], "guarantee": "Your first order is covered by our 90-Day Money-Back Guarantee.",
                  "image": img(slug, d.get("offer_img", "offer")), "alt": o["alt"],
                  "source": f"{pdp} (fetched 2026-10-08); refund + free-shipping threshold from /policies/refund-policy and the site ticker banner",
                  "rating_html": "<b>4.2</b> TrustScore · 1,144 reviews on Trustpilot",
                  "price": {"now": o["now"], "was": o["was"], "tag": o["tag"], "note": o["note"]}, "bullets": o["bullets"], "price_source": o["price_source"]}
    s["product"] = {"name": pname, "image": img(slug, d.get("offer_img", "offer")), "bullets": d["product_bullets"], "source": f"{pdp} (PDP + supplement facts, fetched 2026-10-08)"}
    s["sources"] = [{"label": SRC[u], "url": u} for u in d["sources"]]
    s["trust"] = base["trust"][:3] + [{"icon": "leaf", "html": d["trust4"]}]
    s["trust_source"] = TRUST_SRC + " " + d["trust4_src"]
    s["sticky_cta"] = {"name": d["sticky"], "note": f"From {o['now']}", "cta": "SEE INGREDIENTS", "href": pdp}
    s["pack_images"] = [img(slug, d.get(k + "_img", k)) for k in ("hero", "offer", "dark", "ledge")]
    bad = brand_rules.spec_violations(s)
    if bad:
        raise SystemExit("✗ brand guard: refusing to write " + slug + ": " + "; ".join(bad))
    json.dump(s, open(f"{ROOT}/landing_drafts/{slug}.json", "w"), indent=1, ensure_ascii=False)
    print("wrote", slug)

# ---------------------------------------------------------------- FusiForce
FF = "fusiforce-creatine-listicle-261008"
page(FF, "fusiforce-creatine-gummies", "FusiForce Creatine Monohydrate Gummies", {
 "title": "7 Facts About Creatine Without the Scoop", "accent": "7 Facts", "htitle": "About Creatine Without the Scoop",
 "meta": "Creatine without the scoop: what research shows, the first creatine gummy trial, results with training after 50 and in women, and what to check on a label.",
 "summary": "What creatine research shows, what a gummy trial found, and what to check if powder never stuck for you.",
 "hero_alt": "FusiForce Creatine Monohydrate Gummies pouch on a travertine podium with green apples",
 "chip": "90 gummies · 2 flavors", "chip_src": "Chip = PDP pack label (90 GUMMIES) and PDP variants Green Apple + Blueberry, read 2026-10-08.", "focal_y": 0.3,
 "items": [
  {"title": "Monohydrate is the studied form", "body": f"<p>Most creatine research uses one form: creatine monohydrate. A {A(ANTONIO, '2021 expert review')} counts more than 500 peer-reviewed papers on creatine supplementation.</p><p>No other form has been shown to beat it. So the first word to look for on any label, powder or gummy, is monohydrate.</p>",
   "evidence": "Expert review, J Int Soc Sports Nutr 2021", "source": ANTONIO, "image": img(FF, "row1"), "alt": "A wooden scoop of white powder beside a glass of water and a green apple", "evidence_label": "Expert review · Antonio et al., JISSN 2021"},
  {"title": "A small daily amount works too", "body": f"<p>You don't need a loading phase. In a {A(HULTMAN, 'classic muscle biopsy study')}, a high-dose load raised muscle creatine about 20% in 6 days.</p><p>A low daily dose reached the same 20% rise by day 28, just more slowly. Steady daily intake gets you there.</p>",
   "evidence": "Human study, J Appl Physiol 1996", "source": HULTMAN,
   "chart": {"kind": "bars", "title": "Rise in muscle creatine", "legend": [{"label": "Low daily dose", "highlight": True}, {"label": "High-dose load"}],
             "bars": [{"label": "Day 6, high-dose load", "value": 20, "display": "≈20%"}, {"label": "Day 28, low daily dose", "value": 20, "display": "≈20%", "highlight": True, "inbar": "Daily"}],
             "source": "Hultman et al., J Appl Physiol 1996. 31 men; 20 g/day for 6 days vs 3 g/day for 28 days, muscle total creatine."},
   "evidence_label": "Human study · Hultman et al., J Appl Physiol 1996"},
  {"title": "Gummies were tested in a trial", "body": f"<p>Does creatine still work in a gummy? A {A(PEREIRA, '10-week randomized trial')} gave 32 female beach volleyball athletes creatine gummies daily or no supplement.</p><p>The gummy group jumped higher and changed direction faster. Lean mass did not differ between groups. One small trial, but a real one.</p>",
   "evidence": "Randomized controlled trial, J Funct Morphol Kinesiol 2026", "source": PEREIRA, "image": img(FF, "row3"), "alt": "A volleyball resting on sand beside a net post at sunset", "evidence_label": "Randomized trial · Pereira et al., 2026"},
  {"title": "With training, more lean mass", "body": f"<p>A {A(CHILI, 'meta-analysis of 22 trials')} pooled 721 adults with average ages of 57 to 70. All did resistance training two to three times a week.</p><p>Adding creatine gave 1.37 kg more lean mass than training alone, plus stronger chest and leg presses. The key word is training.</p>",
   "evidence": "Meta-analysis (22 RCTs, 721 adults), Open Access J Sports Med 2017", "source": CHILI,
   "chart": {"kind": "stats", "title": "Older adults who trained: 22 trials", "stats": [{"value": "22", "label": "Trials pooled", "highlight": True}, {"value": "721", "label": "Adults, avg age 57 to 70"}, {"value": "+1.37 kg", "label": "Lean mass vs placebo"}],
             "source": "Chilibeck PD et al. Open Access J Sports Med 2017;8:213-226. Creatine vs placebo during resistance training."},
   "evidence_label": "Meta-analysis of 22 RCTs · Chilibeck et al., 2017"},
  {"title": "Women see small, real gains", "body": f"<p>Evidence in women has been thinner. A {A(LIN, '2026 meta-analysis')} gathered 34 studies of women who exercise or train, with 692 participants.</p><p>It found small positive effects on strength and power. The authors rate certainty as low, so expect modest changes, not dramatic ones.</p>",
   "evidence": "Systematic review and meta-analysis, Front Nutr 2026", "source": LIN, "image": img(FF, "row5"), "alt": "Light sage dumbbells, a rolled linen mat and a water bottle by a window", "evidence_label": "Meta-analysis (34 studies in women) · Lin et al., 2026"},
  {"title": "No head-to-head with powder", "body": "<p>The gummy trial compared creatine gummies with no supplement. We found no published trial comparing gummies with powder directly.</p><p>So the case for gummies rests on the same monohydrate research, plus convenience. The amount per serving is what to check.</p>",
   "evidence": "Evidence gap: Europe PMC search 2026-10-08, no gummy vs powder trial to cite", "image": img(FF, "row6"), "alt": "Printed research papers, reading glasses and a green apple on linen", "evidence_label": "Literature check · no gummy vs powder trial found", "layout": "callout"},
  {"title": "Well tolerated in healthy adults", "body": f"<p>The {A(KREIDER, 'ISSN position stand')} concludes that creatine is safe and well tolerated in healthy people, in studies lasting up to five years.</p><p>Taking medication or managing a kidney condition? Ask your doctor first. Daily use is what the research tested.</p>",
   "evidence": "Position stand, J Int Soc Sports Nutr 2017", "source": KREIDER, "image": img(FF, "row7"), "alt": "A glass of water and a small dish of pale green gummies on a travertine counter", "evidence_label": "Position stand · Kreider et al., JISSN 2017"}],
 "bridge_title": "The best form is the one you take",
 "bridge": "<p>Creatine works through steady daily intake, so the format you will keep using matters most.</p><p>One option: FusiForce Creatine Monohydrate Gummies put creatine monohydrate in a chewable green apple or blueberry gummy, with Panax ginseng extract on the same label. The product page says it is lab-tested after cooking in ISO 17025-accredited facilities.</p><p>Taking medication or managing a health condition? Check with your doctor first.</p>",
 "ledge_alt": "The FusiForce creatine gummies pouch on an oak counter beside a glass of water",
 "expert_id": "690df5b7c3d5e30ef725b48d", "dark_alt": "The FusiForce creatine gummies pouch on a travertine podium against deep green",
 "review_ids": ["69281b1420fb2a718fed2339", "6a8df7438bab5ca2e585cf7f", "69341178ff47bac5ca887d02"],
 "offer": {"pill": "⚡️ FUSIFORCE CREATINE GUMMIES", "accent": "Creatine Monohydrate", "title": "in a Chewable Gummy", "sub": "Creatine monohydrate in a green apple or blueberry gummy. $69.99 on the product page.",
  "alt": "FusiForce Creatine Monohydrate Gummies pouch on stacked travertine discs", "now": "$49.99", "was": "$69.99", "tag": "Save $20",
  "note": "with Subscribe & Save, delivered every 4 weeks. Or $69.99 one-time.",
  "bullets": ["<b>5,000 mg creatine monohydrate</b> per 3-gummy serving", "Lab-tested after cooking in ISO 17025-accredited facilities (product page)", "Plus Panax ginseng root extract (10% ginsenosides)", "Green Apple or Blueberry · 90 gummies per pouch", "90-day money-back guarantee on your first order"],
  "price_source": "PDP /products/fusiforce-creatine-gummies.js 2026-10-08: price 69.99 (both variants); selling plan 'Deliver every 4 weeks' 28.58% = $49.99 (plan 9850224955), shown in the PDP buy box as 'Billed every 4 weeks $49.99'. compare_at_price 114.73 deliberately NOT used (no strike-through against it). Bullets: PDP title/description '5,000 mg per 3-gummy serving', 'Panax ginseng (10% ginsenosides)', variants, pack '90 GUMMIES'."},
 "product_image": "https://wellnessnest.co/cdn/shop/files/" , "product_bullets": ["5,000 mg creatine monohydrate per serving (3 gummies)", "Panax ginseng root extract (10% ginsenosides)", "Green Apple and Blueberry flavors, 90 gummies per pouch"],
 "sources": [ANTONIO, HULTMAN, PEREIRA, CHILI, LIN, KREIDER],
 "trust4": "<b>Lab-tested</b> <small>after cooking, per product page</small>", "trust4_src": "Lab-tested: PDP description 'lab-tested after cooking in ISO 17025-accredited facilities' (Kevin-approved 2026-10-08, pending manual update).", "sticky": "FusiForce Creatine Gummies"})

# ---------------------------------------------------------------- ShilaSource resin
SR = "shilasource-resin-listicle-261008"
page(SR, "shilasource-himalayan-shilajit-resin", "ShilaSource Himalayan Shilajit Resin", {
 "title": "7 Things to Know Before You Try Shilajit Resin", "accent": "7 Things", "htitle": "to Know Before You Try Shilajit Resin",
 "meta": "What shilajit is, what the human trials tested (testosterone, strength, bone density), what they did not, why purity matters, and how resin is taken.",
 "summary": "What shilajit is, what the few human trials tested, what they did not, and how to choose and take a resin.",
 "hero_alt": "ShilaSource Himalayan Shilajit Resin tube and jar on a dark travertine podium",
 "chip": "75 servings per jar (label)", "chip_src": "Chip = PDP pack label '75 SERVINGS' (PDP text: 'featured package states 75 servings'), read 2026-10-08.", "focal_y": 0.3,
 "items": [
  {"title": "It's a resin from mountain rock", "body": f"<p>Shilajit is a dark, sticky, mineral-rich resin that seeps from mountain rock. It has a long history in Ayurvedic tradition.</p><p>A {A(STOHS, '2014 safety review')} names fulvic acid and dibenzo-α-pyrones as key compounds, and notes that well-controlled human studies are relatively few.</p>",
   "evidence": "Review, Phytother Res 2014", "source": STOHS, "image": img(SR, "row1"), "alt": "Dark mineral resin seeping from a crack in layered mountain rock", "evidence_label": "Safety review · Stohs, Phytother Res 2014"},
  {"title": "Men 45 to 55: testosterone rose", "body": f"<p>In a {A(PANDIT, '90-day placebo-controlled trial')}, healthy men aged 45 to 55 took purified shilajit twice a day.</p><p>Total testosterone, free testosterone and DHEAS rose significantly versus placebo, while LH and FSH stayed steady. A purified extract, tested in men only.</p>",
   "evidence": "Human RCT, Andrologia 2016", "source": PANDIT, "image": img(SR, "row2"), "alt": "Leather hiking boots and a trekking pole on a granite boulder above a misty valley", "evidence_label": "Human RCT · Pandit et al., Andrologia 2016"},
  {"title": "Strength held up better", "body": f"<p>In an {A(KELLER, '8-week trial')}, 63 active men took a lower dose, a higher dose or placebo, then did a hard leg-fatigue test.</p><p>Among the stronger half, the higher-dose group lost 8.9% of strength versus 16.0% on placebo. The lower dose matched placebo.</p>",
   "evidence": "Human RCT, J Int Soc Sports Nutr 2019", "source": KELLER,
   "chart": {"kind": "bars", "title": "Strength lost after fatigue (lower is better)", "legend": [{"label": "Higher dose", "highlight": True}, {"label": "Lower dose / placebo"}],
             "bars": [{"label": "Higher dose", "value": 8.9, "display": "8.9%", "highlight": True, "inbar": "Best"}, {"label": "Lower dose", "value": 17.0, "display": "17.0%"}, {"label": "Placebo", "value": 16.0, "display": "16.0%"}],
             "source": "Keller et al., JISSN 2019. 63 men, 8 weeks, 500 vs 250 mg/day PrimaVie shilajit vs placebo; adjusted mean % decline in MVIC, upper-50th-percentile strength subgroup."},
   "evidence_label": "Human RCT · Keller et al., JISSN 2019"},
  {"title": "Bone density in women 45 to 65", "body": f"<p>A {A(PINGALI, '48-week trial')} followed 60 postmenopausal women with low bone density. They took a shilajit extract at one of two doses, or placebo.</p><p>Bone density kept falling on placebo, but the loss was smaller with the extract, more so at the higher dose. One trial, one specific extract.</p>",
   "evidence": "Human RCT, Phytomedicine 2022", "source": PINGALI, "image": img(SR, "row4"), "alt": "Walking shoes and a linen jacket on a sunlit stone garden bench", "evidence_label": "Human RCT · Pingali & Nutalapati, 2022"},
  {"title": "Purity matters with resins", "body": f"<p>Ayurvedic products can carry heavy metals. A {A(SAPER, 'JAMA study')} tested 193 Ayurvedic products bought online: 20.7% contained lead, mercury or arsenic.</p><p>So ask any shilajit seller about lab testing for your batch, not just a general claim.</p>",
   "evidence": "Product testing study, JAMA 2008", "source": SAPER,
   "chart": {"kind": "stats", "title": "Ayurvedic products bought online", "stats": [{"value": "193", "label": "Products tested", "highlight": True}, {"value": "20.7%", "label": "Lead, mercury or arsenic"}, {"value": "75%", "label": "Of those claimed GMP"}],
             "source": "Saper RB et al. JAMA 2008;300(8):915-923. X-ray fluorescence testing of 193 products bought online in 2005."},
   "evidence_label": "Product testing · Saper et al., JAMA 2008"},
  {"title": "The resin form is barely studied", "body": f"<p>The controlled trials above used purified, standardized extracts in capsules. Resin itself has far less evidence.</p><p>The one resin study we found was a {A(YADAV, '28-day pilot')} in 25 men with no placebo group. Promising, but not proof.</p>",
   "evidence": "Evidence gap: Europe PMC search 2026-10-08; only resin study = open-label pilot, Cureus 2026", "source": YADAV, "image": img(SR, "row6"), "alt": "Research papers, reading glasses and an amber dish with a drop of resin on slate", "evidence_label": "Literature check · resin: one open-label pilot only", "layout": "callout"},
  {"title": "How resin is usually taken", "body": f"<p>Resin is usually dissolved: a {A(HOWTO, 'pea-size piece')} stirred into warm, not boiling, water or tea until no dark lumps remain.</p><p>The serving on your own jar's label is the one to use. Labels differ between brands.</p>",
   "evidence": "Wellness Nest usage guide (Oct 2026)", "source": HOWTO, "image": img(SR, "row7"), "alt": "A cup of warm tea with a piece of dark resin dissolving into amber swirls", "evidence_label": "Usage guide · Wellness Nest, Oct 2026"}],
 "bridge_title": "Pick the format you will keep",
 "bridge": "<p>Every trial here tested daily use over weeks or months. A routine you can keep matters more than any single serving.</p><p>One option: ShilaSource Himalayan Shilajit Resin, a resin you dissolve in a warm drink. Its pack states 70% Fulvic Acid* and Lab-Tested for Purity*.</p><p>Taking medication or managing a health condition? Check with your doctor first.</p>",
 "ledge_alt": "The ShilaSource shilajit resin tube and jar on a stone counter beside a cup of tea",
 "expert_id": "698a106be72503d576b56410", "dark_alt": "The ShilaSource shilajit resin tube and jar on a slate podium in warm light",
 "review_ids": ["69a7e1c6034b5ce74072c814", "69cfdb42313f8a8159e4feb4", "69281b1420fb2a718fed2339"],
 "offer": {"pill": "⚡️ SHILASOURCE SHILAJIT RESIN", "accent": "Himalayan Resin", "title": "for a Warm Daily Drink", "sub": "Himalayan shilajit resin you dissolve in water or tea. $59.99 on the product page.",
  "alt": "ShilaSource Himalayan Shilajit Resin tube and jar on stacked travertine discs", "now": "$39.99", "was": "$59.99", "tag": "Save $20",
  "note": "with Subscribe & Save, delivered every 4 weeks. Or $59.99 one-time.",
  "bullets": ["<b>1.06 oz (30 g) jar</b> of Himalayan shilajit resin, 75 servings as labeled", "70% Fulvic Acid* · Lab-Tested for Purity* (as printed on the pack)", "Dissolve in warm water or tea, as the label directs", "90-day money-back guarantee on your first order"],
  "price_source": "PDP text 2026-10-08: 'Subscription: $39.99 charged every 4 weeks for one jar; $116.97 every 12 weeks for three jars', one-time $59.99; /products/shilasource-himalayan-shilajit-resin.js plan 9850323259 = 3999. compare_at 99.98 NOT used. Bullets: pack label 1.06oz (30g), 75 SERVINGS; PDP 'featured package states 75 servings'."},
 "product_image": "", "product_bullets": ["1.06 oz (30 g) jar; the package states 75 servings", "Taken dissolved in warm (not boiling) water or tea, following the label"],
 "sources": [STOHS, PANDIT, KELLER, PINGALI, SAPER, YADAV],
 "trust4": "<b>70% Fulvic Acid*</b> <small>Lab-Tested for Purity*, per pack</small>", "trust4_src": "Pack label text '70% Fulvic Acid*', 'Lab-Tested for Purity*' (Kevin-approved 2026-10-08, pending manual update).", "sticky": "ShilaSource Shilajit Resin"})

# ---------------------------------------------------------------- Shilajit gummies
SG = "shilajit-gummies-listicle-261008"
page(SG, "premium-himalayan-shilajit-gummies", "Premium Himalayan Shilajit Gummies", {
 "title": "7 Things to Check Before Buying Shilajit Gummies", "accent": "7 Things", "htitle": "to Check Before Buying Shilajit Gummies",
 "meta": "What shilajit trials actually used, what they found, how to read the extract line and herb amounts on a gummy label, and why batch testing matters.",
 "summary": "What shilajit trials actually used, what they found, and how to read a gummy label before you buy.",
 "hero_alt": "Premium Himalayan Shilajit Gummies pouch on a travertine podium",
 "chip": "60 gummies · 30 servings", "chip_src": "Chip = pack label '60 GUMMIES' + PDP supplement facts 'Servings per container 30' (2 gummies), read 2026-10-08.", "focal_y": 0.3,
 "items": [
  {"title": "Trials used capsule extracts", "body": f"<p>Shilajit's human trials did not test gummies. They used purified, standardized extracts in capsules, as in a {A(KELLER, '2019 strength trial')} and a {A(PINGALI, '2022 bone trial')}.</p><p>A gummy is a different format. That is fine, but it means the label, not the research, tells you what you get.</p>",
   "evidence": "Study design of the cited RCTs", "source": KELLER, "image": img(SG, "row1"), "alt": "Raw mineral rock, a dish of dark resin and a dish of dark gummies on travertine", "evidence_label": "Study design · Keller 2019, Pingali 2022"},
  {"title": "Testosterone rose in older men", "body": f"<p>In a {A(PANDIT, '90-day placebo-controlled trial')}, healthy men aged 45 to 55 took purified shilajit twice daily.</p><p>Total and free testosterone rose significantly versus placebo. Men only, one extract, one trial: a signal worth knowing, not a promise.</p>",
   "evidence": "Human RCT, Andrologia 2016", "source": PANDIT,
   "chart": {"kind": "stats", "title": "Purified shilajit vs placebo", "stats": [{"value": "90", "label": "Days, twice daily", "highlight": True}, {"value": "45 to 55", "label": "Age of the men"}, {"value": "T ↑", "label": "Testosterone vs placebo"}],
             "source": "Pandit S et al. Andrologia 2016;48(5):570-575. Randomised, double-blind, placebo-controlled; 250 mg purified shilajit twice daily."},
   "evidence_label": "Human RCT · Pandit et al., Andrologia 2016"},
  {"title": "Read the extract line", "body": "<p>Gummy labels can list shilajit two ways: the extract itself, or a larger raw-resin equivalent based on a ratio such as 10:1.</p><p>The trials report extract amounts. So when you compare products, or compare a label with a study, compare extract with extract.</p>",
   "evidence": "Label reading; extract amounts per Pandit 2016, Keller 2019, Pingali 2022", "source": PANDIT, "image": img(SG, "row3b"), "alt": "A magnifying glass on a blank card beside dark gummies on travertine", "evidence_label": "Label literacy · how trials report amounts"},
  {"title": "Strength held up at a higher dose", "body": f"<p>In an {A(KELLER, '8-week trial')}, 63 active men took a lower dose, a higher dose or placebo, then did a hard leg-fatigue test.</p><p>Among the stronger half, the higher-dose group lost 8.9% of strength versus 16.0% on placebo. The lower dose matched placebo.</p>",
   "evidence": "Human RCT, J Int Soc Sports Nutr 2019", "source": KELLER,
   "chart": {"kind": "bars", "title": "Strength lost after fatigue (lower is better)", "legend": [{"label": "Higher dose", "highlight": True}, {"label": "Lower dose / placebo"}],
             "bars": [{"label": "Higher dose", "value": 8.9, "display": "8.9%", "highlight": True, "inbar": "Best"}, {"label": "Lower dose", "value": 17.0, "display": "17.0%"}, {"label": "Placebo", "value": 16.0, "display": "16.0%"}],
             "source": "Keller et al., JISSN 2019. 63 men, 8 weeks, 500 vs 250 mg/day PrimaVie shilajit vs placebo; adjusted mean % decline in MVIC, upper-50th-percentile strength subgroup."},
   "evidence_label": "Human RCT · Keller et al., JISSN 2019"},
  {"title": "Blends: check each herb's amount", "body": f"<p>Many shilajit gummies add herbs like ashwagandha. Those herbs have their own trials, at their own doses.</p><p>In one {A(CHANDRA, '60-day trial')}, ashwagandha root extract lowered stress scores and cortisol versus placebo. Compare a blend's amounts with the doses used in trials like that.</p>",
   "evidence": "Human RCT (ashwagandha only), Indian J Psychol Med 2012", "source": CHANDRA, "image": img(SG, "row5"), "alt": "Dried ashwagandha roots, a bowl of root powder and fresh ginger on linen", "evidence_label": "Human RCT (ashwagandha only) · Chandrasekhar et al., 2012"},
  {"title": "No trial tested shilajit gummies", "body": "<p>We found no published trial of shilajit in gummy form, or of shilajit blended with these herbs.</p><p>So a gummy's case rests on the separate ingredient research plus convenience. Many people simply find a pre-measured gummy easier than a sticky resin.</p>",
   "evidence": "Evidence gap: Europe PMC search 2026-10-08, no shilajit gummy or blend trial to cite", "image": img(SG, "row6"), "alt": "Printed research papers, reading glasses and a dish of dark gummies on linen", "evidence_label": "Literature check · no gummy or blend trial found", "layout": "callout"},
  {"title": "Ask about batch lab testing", "body": f"<p>Ayurvedic products can carry heavy metals. A {A(SAPER, 'JAMA study')} found lead, mercury or arsenic in 20.7% of Ayurvedic products bought online.</p><p>Before buying any shilajit product, ask the seller whether a lab report exists for your batch.</p>",
   "evidence": "Product testing study, JAMA 2008", "source": SAPER, "image": img(SG, "row7"), "alt": "Laboratory glassware and a blank clipboard on a travertine bench", "evidence_label": "Product testing · Saper et al., JAMA 2008"}],
 "bridge_title": "If a gummy fits your routine",
 "bridge": "<p>The trials tested daily use for weeks or months. A pre-measured gummy takes the guesswork out of each serving.</p><p>One option: Premium Himalayan Shilajit Gummies pair shilajit extract with ashwagandha, gokshura, black musli and four more botanicals. Its pack lists 75% Fulvic Acid and 85+ Trace Minerals; its extract per serving is lower than in the trials above.</p><p>Taking medication? Check with your doctor first.</p>",
 "ledge_alt": "The shilajit gummies pouch on a travertine shelf beside a glass of water",
 "expert_id": "691f0f09c54c63dff6a97114", "dark_alt": "The shilajit gummies pouch on a travertine podium against deep green",
 "review_ids": ["698ae799ef38ae92b56412c4", "695555ad937e0e68e1689468", "699e2077993dde2ca3ba9ebb"],
 "offer": {"pill": "⚡️ HIMALAYAN SHILAJIT GUMMIES", "accent": "Shilajit + 7 Botanicals", "title": "in Two Gummies a Day", "sub": "A chewable shilajit and botanical blend. $59.99 on the product page.",
  "alt": "Premium Himalayan Shilajit Gummies pouch on stacked travertine discs", "now": "$39.99", "was": "$59.99", "tag": "Save $20",
  "note": "with Subscribe & Save, delivered every 4 weeks. Or $59.99 one-time.",
  "bullets": ["<b>150 mg shilajit extract (10:1)</b> per 2-gummy serving", "75% Fulvic Acid · 85+ Trace Minerals (as printed on the pack)", "With ashwagandha, ginger, black musli, gokshura, kaunch, ginseng and akarkara", "60 gummies · 30 servings per pouch", "90-day money-back guarantee on your first order"],
  "price_source": "PDP text 2026-10-08: 'One-time purchase is $59.99. Current recurring options are $39.99 every 4 weeks for 1 pouch, or $116.97 every 12 weeks for 3 pouches'; .js plan 9850290491 = 3999. compare_at 99.98 NOT used. Bullets: PDP supplement facts (2 gummies, 30 servings; shilajit resin from 150 mg of 10:1 extract; ashwagandha, ginger, black musli, gokshura, kaunch, ginseng, akarkara) + pack '60 GUMMIES'."},
 "product_image": "", "product_bullets": ["Shilajit resin from 150 mg of 10:1 extract (1,500 mg equivalent) per 2-gummy serving", "Ashwagandha, ginger, black musli, gokshura, kaunch, ginseng and akarkara on the same label", "60 gummies, 30 servings per pouch"],
 "sources": [PANDIT, KELLER, PINGALI, CHANDRA, SAPER],
 "trust4": "<b>85+ Trace Minerals</b> <small>75% Fulvic Acid, per pack</small>", "trust4_src": "Pack label text '85+ Trace Minerals', '75% Fulvic Acid' (Kevin-approved 2026-10-08, pending manual update).", "sticky": "Shilajit Gummies"})

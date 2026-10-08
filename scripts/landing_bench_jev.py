#!/usr/bin/env python3
"""Blind A/B benchmark of two landing pages with JEV Ultrafast (jev-latest, TypeSafe System One), Kevin 2026-10-08.

  /usr/bin/python3 scripts/landing_bench_jev.py <ref.json> <new.json> --label r0 [--calls 4] [--cap 0.30]
Inputs = scripts/landing_bench_extract.mjs output (page text + neutral desktop/mobile measurements + image alts;
JEV is text-only, so screenshots enter as those measurements). Each call shows BOTH pages as "page_A"/"page_B"
with the order randomized per call, and scores each page on the same 12-criterion rubric (design-taste-frontend
anti-slop criteria + DTC conversion criteria), 5 anchored levels -> 0-10. Averages over --calls.
Results: state/bench/scores.json (appended per label), spend: state/bench/jev-ledger.json. Key from
~/.config/typesafe/env (never printed).
"""
import json, os, random, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

API, MODEL = "https://api.typesafe.ai/v1/systemone", "jev-latest"
PRICE_PER_TOKEN = 0.020311662 / 483611          # ≈ $0.042 / Mtok input (PATI ledgers 2026-09/10), output free
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = os.path.join(ROOT, "state", "bench")
LEDGER, SCORES = os.path.join(BENCH, "jev-ledger.json"), os.path.join(BENCH, "scores.json")

# criterion -> (instruction, 5 anchors worst..best). T = design-taste-frontend, D = DTC conversion.
RUBRIC = {
 "hook_headline": ("D: How strongly do the H1 and summary make a 40+ supplement shopper want to keep reading (specific, benefit- or curiosity-led, clear promise)?",
  ["Flat, confusing or label-like", "Clear topic, weak pull", "Decent pull, somewhat generic or long", "Strong, specific promise or curiosity", "Irresistible, specific and instantly clear"]),
 "scannability": ("D/T: Can a skimmer get the point from numbered subheads, short paragraphs and visual breaks? Use `measurements` (paragraph_words_median/max, paragraphs_over_60_words, headings).",
  ["Wall of text", "Hard to skim, long paragraphs", "Skimmable with effort", "Easy to skim, short blocks, clear subheads", "Effortless: every subhead tells the story on its own"]),
 "proof_credibility": ("D: How credible is the evidence? Reward specific, sourced, verifiable facts and honest limits; penalize vague 'studies show', unsourced numbers, inflated or impossible claims and typos in credentials.",
  ["Unsupported or dubious claims", "Mostly vague claims", "Some specifics, few sources", "Specific and mostly sourced", "Specific, sourced, verifiable and honest about limits"]),
 "offer_cta": ("D: How clear and compelling is the offer and call to action (what you get, price/offer, guarantee, CTA label that fits on one line, CTA placement)? Do NOT reward fake urgency (countdowns, 'sell-out risk') unless clearly real.",
  ["No clear offer or CTA", "CTA exists, offer unclear", "Clear CTA, plain offer", "Clear offer, price/guarantee, strong CTA", "Compelling, specific offer with a single clear, well-placed CTA"]),
 "mobile_readability": ("T/D: Judge the 375px `measurements.mobile`: H1 lines, body font size, paragraph length, screens_tall, small text blocks, overflow. Is it comfortable to read on a phone?",
  ["Broken or very hard on mobile", "Readable but tiring (long blocks, tiny text, very long page)", "Acceptable", "Comfortable: big type, short blocks, sensible length", "Excellent mobile reading experience"]),
 "image_relevance": ("T/D: From `image_alts`, image counts and image_area_share, how relevant and supportive are the images (real scenes/product that match the copy, not generic filler)?",
  ["No or irrelevant images", "Mostly generic filler", "Relevant but generic", "Relevant, specific, support each point", "Every image reinforces its section and the product is shown clearly"]),
 "brand_consistency": ("T: Visual and verbal consistency: one accent colour, consistent shapes (distinct_accent_bg_colors, distinct_corner_radii), coherent voice and product naming from top to bottom.",
  ["Inconsistent and messy", "Several inconsistencies", "Mostly consistent", "Consistent and on-brand", "Fully coherent brand system"]),
 "trust_signals": ("D: Trust: named author with credible role, real customer reviews/rating, guarantee, disclaimers. Penalize typos in credentials and unverifiable crowd claims.",
  ["No trust signals or dubious ones", "Weak", "Some trust signals", "Solid: author, review, guarantee", "Strong, specific and believable trust signals"]),
 "no_ai_slop": ("T (design-taste-frontend AI tells): penalize em-dashes (`measurements.em_dashes`), filler phrasing, hedging overload, generic AI cadence, hype clichés, broken/hallucinated phrases, typos.",
  ["Reads clearly AI/templated or sloppy", "Many tells", "Some tells", "Few tells, human voice", "Crafted, human, zero tells"]),
 "typography_hierarchy": ("T: Typographic hierarchy from measurements: H1 size and lines (max 2 on desktop), body size, line length ~45-75 chars, consistent heading levels.",
  ["Poor hierarchy", "Weak", "Adequate", "Clear hierarchy, comfortable measure", "Excellent, premium hierarchy"]),
 "hero_discipline": ("T: Hero discipline: headline at most 2 lines on desktop, summary at most ~20-30 words, first screen (`first_screen`) shows headline, author and a strong visual or the first point without clutter.",
  ["Cluttered or overflowing hero", "Overlong headline/summary", "Acceptable", "Tight hero, fits the first screen", "Crisp hero that fits and hooks instantly"]),
 "persuasion_flow": ("D: Does the page build a logical case from reasons to product to offer, so the CTA feels earned (bridge from evidence to product, objections handled)?",
  ["No flow", "Disjointed", "Basic flow", "Logical, builds desire", "Seamless, the CTA feels inevitable"]),
}


def key():
    for line in open(os.path.expanduser("~/.config/typesafe/env")):
        line = line.strip().removeprefix("export ")
        if line.startswith("TYPESAFE_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("TYPESAFE_API_KEY missing")


def page_state(d):
    slim = lambda m: {k: v for k, v in m.items() if k not in ("headings",)}
    return {"text": d["text"][:7000], "headings": d["desktop"]["headings"],
            "measurements": {"desktop_1440": slim(d["desktop"]), "mobile_375": slim(d["mobile"])}}


def questions():
    q = {}
    for side in ("A", "B"):
        for c, (ins, levels) in RUBRIC.items():
            q[f"{side}__{c}"] = {"type": "score", "instructions": f"Judge ONLY `page_{side}`. {ins}", "criteria": levels}
    return q


FRAMES = ["You are a panel of senior DTC conversion copywriters and landing-page designers reviewing two supplement listicle pages (pre-sell pages that end in a product offer). Judge each page on its own merits; the products differ, judge the craft.",
          "Blind design + CRO review. Two long-form listicle landing pages for dietary supplements, shown as page_A and page_B (order is random). Rate each against the rubric as a demanding creative director would."]


def call(payload, k):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8", "replace")
    for attempt in range(3):
        try:
            req = urllib.request.Request(API, data=body, headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=90).read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 503, 529) and attempt < 2:
                import time; time.sleep(3); continue
            raise


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    opt = lambda n, d: sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
    label, n_calls, cap = opt("--label", "run"), int(opt("--calls", "4")), float(opt("--cap", "0.30"))
    ref, new = json.load(open(a[0])), json.load(open(a[1]))
    os.makedirs(BENCH, exist_ok=True)
    led = json.load(open(LEDGER)) if os.path.exists(LEDGER) else {"cap": cap, "spent": 0.0, "calls": 0, "tokens": 0}
    rng = random.Random(f"{label}-{len(new['text'])}")
    plans = []
    for i in range(n_calls):
        ref_is_a = (i % 2 == 0) if rng.random() < 0.5 else (i % 2 == 1)
        pa, pb = (ref, new) if ref_is_a else (new, ref)
        st = {"task": FRAMES[(i // 2) % len(FRAMES)], "page_A": page_state(pa), "page_B": page_state(pb)}
        plans.append((ref_is_a, {"model": MODEL, "state": st, "questions": questions()}))
    est = sum(len(json.dumps(p)) * 1.6 / 4 for _, p in plans) * PRICE_PER_TOKEN
    if led["spent"] + est * 1.3 > cap:
        sys.exit(f"cap: spent ${led['spent']:.4f} + est ${est:.4f} would pass ${cap}")
    k = key()
    with ThreadPoolExecutor(4) as ex:
        outs = list(ex.map(lambda p: call(p[1], k), plans))
    per = {"ref": {c: [] for c in RUBRIC}, "new": {c: [] for c in RUBRIC}}
    for (ref_is_a, _), r in zip(plans, outs):
        tok = (r.get("usage") or {}).get("input_tokens", 0)
        led["spent"] += tok * PRICE_PER_TOKEN; led["tokens"] += tok; led["calls"] += 1
        ans = r["answers"]
        for c, (_, levels) in RUBRIC.items():
            for side in ("A", "B"):
                who = "ref" if (side == "A") == ref_is_a else "new"
                per[who][c].append(ans[f"{side}__{c}"]["score"] / (len(levels) - 1) * 10)
    json.dump(led, open(LEDGER, "w"), indent=1)
    avg = {w: {c: round(sum(v) / len(v), 2) for c, v in d.items()} for w, d in per.items()}
    for w in avg:
        avg[w]["OVERALL"] = round(sum(avg[w][c] for c in RUBRIC) / len(RUBRIC), 2)
    worse = [c for c in RUBRIC if avg["new"][c] < avg["ref"][c]]
    allr = json.load(open(SCORES)) if os.path.exists(SCORES) else {}
    allr[label] = {"avg": avg, "raw": per, "orders_ref_is_A": [p[0] for p in plans], "worse_criteria": worse, "model": outs[0].get("model")}
    json.dump(allr, open(SCORES, "w"), indent=1)
    print(f"{'criterion':22} {'ref':>6} {'new':>6}")
    for c in list(RUBRIC) + ["OVERALL"]:
        print(f"{c:22} {avg['ref'][c]:6.2f} {avg['new'][c]:6.2f}{'  <' if c in worse else ''}")
    print(f"new worse on {len(worse)}: {worse}")
    print(f"JEV {outs[0].get('model')} · calls {len(outs)} · ledger ${led['spent']:.5f} total ({led['tokens']:,} tokens)")


if __name__ == "__main__":
    main()

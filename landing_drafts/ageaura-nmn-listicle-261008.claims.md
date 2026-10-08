# Claims log — ageaura-nmn-listicle-261008

| Claim (as written on page) | Source | How verified |
|---|---|---|
| "NMN is a precursor your body converts into NAD⁺" | AgeAura PDP description, product/ingredients accordion: fetched `https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex` 2026-10-08 | Verbatim from live PDP copy ("NMN … naturally occurring precursor to NAD⁺") |
| "A 66-person trial: NAD+/NADH rose 11.3% at 30 days, 38% at 60 days (vs 14.3% placebo) on 300 mg/day NMN" | Huang H et al., Front Aging 2022. doi:10.3389/fragi.2022.851698 (Europe PMC PMID 35821806 / PMC9261366) | Fetched abstract via Europe PMC REST this run; numbers copied from abstractText verbatim |
| "A 12-week trial in older adults: NMN group had a shorter 4-m walking time and higher blood NAD⁺ than placebo; sleep quality also improved; no significant difference on the main stepping test" | Morifuji M et al., Geroscience 2024. doi:10.1007/s11357-024-01204-1 (Europe PMC PMID 38789831 / PMC11336149) | Fetched abstract via Europe PMC REST this run |
| "A 6–12 week trial in older men: NAD⁺ and its metabolites rose; gait speed and one grip test showed nominal (not strongly powered) improvement; body composition did not change" | Igarashi M et al., npj Aging 2022;8:5. doi:10.1038/s41514-022-00084-z (Europe PMC PMID 35927255 / PMC9158788) | Fetched abstract via Europe PMC REST this run |
| "A meta-analysis of 12 trials, 513 people: NMN reliably raised blood NAD levels, but most other outcomes (glucose, lipids) did not differ significantly from placebo" | Zhang J, Poon ETC, Wong SHS. Crit Rev Food Sci Nutr 2025;65(22):4382-4400. doi:10.1080/10408398.2024.2387324 (Europe PMC PMID 39116016) | Fetched abstract via Europe PMC REST this run |
| "No published human trial has tested NMN and TMG given together as one combined dose — the pairing is a formulation choice, not a tested combination" | Absence claim: Europe PMC + PubMed search this run for "NMN TMG combined trial" and "NMN betaine combination RCT" returned no RCT testing the pair together (only single-ingredient trials, and industry blog posts making the mechanistic case) | Searched this run; stated as an evidence gap, not a tested fact |
| "A 6-week trial: 1.5–6 g/day betaine (TMG) lowered fasting homocysteine 12–20% vs placebo" | Olthof MR et al., J Nutr 2003;133(12):4135-8. doi:10.1093/jn/133.12.4135 (Europe PMC PMID 14652361) | Fetched abstract via Europe PMC REST this run |
| "TMG is paired with NMN to support methylation pathways that run alongside NAD⁺ metabolism" | AgeAura PDP ingredients accordion, fetched 2026-10-08 | Verbatim paraphrase of PDP copy ("Helps support methylation pathways that run alongside NAD metabolism") |
| Product name, image, bullets (NMN, TMG, Quercetin, Trans-Resveratrol, Apigenin, Folate, Spermidine; vegan capsule; gluten/soy/dairy/fish/shellfish free; contains wheat) | `https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.js` + PDP ingredients accordion, fetched 2026-10-08 | Verbatim from live PDP JSON + accordion text |
| Price $69.95 | `ageaura-pure-nmn-tmg-nad-complex.js`, fetched 2026-10-08: `price: 6995` | Direct from Shopify product JSON (cents) |
| "90-Day Money-Back Guarantee" | PDP accordion "90-Day Guarantee" + `/policies/refund-policy`, both fetched 2026-10-08 | Verbatim text match on both pages |
| "Free shipping on orders over $70" | PDP ticker banner, fetched 2026-10-08: "🚚 Free Shipping on Orders Over $70" | Verbatim from live PDP markup |
| Trustpilot TrustScore 4.2, 1,144 reviews (count shown with thousands comma as displayed) | `state/trustpilot/wellnessnest.json`, `fetched_at: 2026-10-08T04:16:17Z` | Read exactly from the refreshed file; not re-scraped this run |
| Expert slot: Elaine Goddard, 5★, "Its made me feel so much better. I'd recommend to anyone give it a try, see how you feel after a month xx" | `state/trustpilot/wellnessnest.json` review id `6907a3d86be977ba29ea36b9`, published 2025-11-02 | Verbatim quote + name exactly as in the refreshed Trustpilot file; this is a general Wellness Nest review (file carries no AgeAura-specific 4-5★ review today), so the attribution line says "Wellness Nest customer on Trustpilot," not AgeAura-specific |

## What was deliberately left out
- No stated NMN or TMG dose anywhere in body copy (narrative text) — only the product card mirrors what the live PDP prints (500 mg NMN, 250 mg TMG per daily serving of 2 capsules).
- No claim that NMN/TMG "reverses aging," "extends lifespan," or any disease claim — none of the cited trials measured lifespan, disease prevention, or reversal of aging; copy says what each trial measured and didn't measure.
- No COA / lab-testing claim (AgeAura has no COA yet per `brand/ageaura.json` note + `[[no-coa-competitive-advantage]]`).
- No star rating or review specific to AgeAura or NMN — only the Wellness Nest storewide Trustpilot TrustScore/review, and one verbatim storewide review (not product-specific) in the expert slot, because the Trustpilot file carries no AgeAura-tagged review.
- No mention of Urolithin A or peptides (forbidden for AgeAura per `brand/ageaura.json`).
- No countdown timer or scarcity line (`topbar.deadline` left null).
- No numbered item names or links the product; product first appears in the bridge, per hybrid posture.

## v2 — Grok Bot review edits (2026-10-08 ~11:55 ICT), re-verified against the sources
| Block | Change | Verified |
|---|---|---|
| Row 02 | "placebo barely moved" → NMN +11.3% (d30) / +38% (d60) vs placebo no change (d30) / +14.3% (d60) | Huang 2022 abstract (Europe PMC) |
| Row 03 | title "Older men…" → "Older adults…" (trial = 60 older adults, not men only); sleep wording = better PSQI scores at week 12 | Morifuji 2024 abstract |
| Row 05 | unsourced "NMN uses up methyl groups" → nicotinamide cleared partly by methylation, 2-PY/4-PY measured (Morifuji 2024); betaine lowered fasting homocysteine within 6 weeks (Olthof 2003), both linked inline | Europe PMC abstracts |
| Bridge/offer | "once-daily capsule routine" → "one daily two-capsule serving" | PDP: "Each daily serving (2 capsules) contains: 500mg NMN … 250mg TMG" |
| 08 expert slot | general "made me feel so much better" review (implied effect on an AgeAura page) → 5★ service/subscription review by Lisa Acton (GB, 2026-03-05), verbatim | state/trustpilot/wellnessnest.json (__NEXT_DATA__, read 2026-10-08), review id 69a9b43fff0a1314dbd8a581 |
| Row 07 image | was a duplicate of the bridge image → fresh no-face scene `sq-row7` (article_images.py --square --ugc --qc, QC PASS) | — |
| Offer/product image | PDP image 0 is a composite with a hand + benefit-claim overlays → curated real pack crop `product_refs/ageaura-pure-nmn-tmg-nad-complex.png` (no overlays; every PDP image carries text/hands/faces) | product_refs json: cropped from the live PDP |

## v3 edits (2026-10-08, benchmark round 1 vs reference listicle)
Copy tightened for scannability/mobile (no claim added; every number keeps its source link):
- H1 → "7 Things Research Shows About NMN After 40"; summary 41 → 27 words; item titles ≤ 34 chars.
- Row 02 title "NAD+ rose 38% in 60 days" = Huang 2022 NAD+/NADH +38% at day 60 vs baseline (placebo +14.3%), abstract.
- Row 03 "finished a 4-meter walk faster than placebo" = Morifuji 2024 secondary outcome; primary (stepping test) n.s. stated.
- Row 04 chart label "Most markers unchanged" = Zhang 2025 meta-analysis (glucose/lipid outcomes mostly n.s.; NAD+ up).
- Row 05 trimmed; Olthof 2003 homocysteine statement unchanged.
- Bridge: doctor line kept as its own sentence. Offer CTA "SEE INGREDIENTS".
- All em/en dashes removed (incl. chart sources and source labels: page ranges use "-").
Images: new no-face, no-product scenes sq-row1b (water + plain unbranded capsules), sq-row3b (older adults walking, from behind),
sq-row4b (research papers; used on row 06). QC PASS (article_images.py --qc). Alts describe the scene.

## v4 — visual overhaul (2026-10-08, template gsl-ref-listicle-v2 / style premium)
- Hero now shows the product (Kevin's explicit ask: "product above the fold"). Posture = Kevin's call (PATI-ADAPTATION #1); the DTC skill default would keep the pack below the bridge.
- Pack shots (hero, offer, expert, bridge) are GENERATED with the real bottle cutout as the reference (product_refs/ageaura-pure-nmn-tmg-nad-complex-cutout.png, lifted from the PDP image). Kevin asked for generated premium shots, so this deviates from PATI-ADAPTATION #7 ("the real pack"). Every one passed: vision QC, landing_label_gate.py (all 12 label strings OCR'd letter-perfect) and a 2x zoom check of the mark (one pointed leaf + two S-curves = the real pack). Fallback composites of the real cutout are in tmp_images (v3-*-pack.webp).
- Row images: one art direction (ivory/sand/sage, morning light, travertine + linen). No faces (row 3 couple is from behind, heads out of frame).
- Trust strip: 4.2 TrustScore · 1,144 reviews (state/trustpilot/wellnessnest.json); 90-day money-back guarantee on the first order + free shipping $70+ (wellnessnest.co policy pages, as in v3); vegan capsules (label).
- Review cards: 3 extra real 5-star Trustpilot reviews, quoted verbatim with their URLs (Tonya, Jindřich Pavlíček, Martin Mc Cartney JNR) + the existing Lisa Acton review.
- Offer price: $59.46 = PDP selling plan "1 product every 4 weeks at 15% discount" on $69.95 (/products/ageaura-pure-nmn-tmg-nad-complex.js, 2026-10-08). Shown as Subscribe & Save vs the one-time price; no compare_at is invented.
- Offer bullets = label facts only (500 mg NMN + 250 mg TMG per serving; quercetin, trans-resveratrol, apigenin, folate, spermidine; 60 vegan capsules / 30 servings) + the real guarantee.
- Chart: Huang 2022 values unchanged (Day 30 +11.3%, Day 60 +38% NMN, placebo +14.3%).

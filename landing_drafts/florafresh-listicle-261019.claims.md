# FloraFresh daily routine listicle claims log

Created: 2026-10-19. Draft-only. Claim count: 14. Placeholders: 0.

| # | Claim | Source fetched/read this run | Verification and limits |
|---|---|---|---|
| 1 | Repetition in a familiar setting supports habit formation | Lally et al., European Journal of Social Psychology 2010, https://doi.org/10.1002/ejsp.674 ; original paper PDF https://www.flexyourbrain.com/wp-content/uploads/2015/10/UL-STUDY-66-Days-IJSP_998-1009.pdf | Research agent fetched original PDF abstract. Eating, drinking and activity actions, not supplements or vaginal health. |
| 2 | 96 volunteers, 12 weeks, daily chosen action | Same original Lally paper | Enrollment and observation period, not a claim that everyone formed a habit. 82 supplied sufficient data; no outcome percentage used. |
| 3 | Missing one opportunity did not materially affect habit formation | Same original Lally paper | Not permission to double supplement servings. No gummy-versus-capsule comparison. |
| 4 | Different types of probiotics may have different effects | https://www.nccih.nih.gov/health/probiotics-usefulness-and-safety | Fetched this run. No transfer of another organism's benefit to this product. |
| 5 | BV symptoms need clinical evaluation; antibiotic treatment is described | https://www.cdc.gov/bacterial-vaginosis/about/index.html | Research agent fetched. No implication this gummy treats, prevents or improves BV. |
| 6 | FloraFresh is a gummy product in a dusty-pink pouch | Live https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies and .js; product_refs/florafresh-vaginal-probiotics-gummies.png | HTML and JSON saved in sources/. Real curated pack used, not gallery claims overlays. |
| 7 | Pineapple fruit powder 100 mg with bromelain per 2 gummies | Approved Supplement Facts transcription, scripts/florafresh_rules.py --brief | Label-only exception. Quantity appears only in offer/product cards. Largest mass ingredient listed first. |
| 8 | Vitamin C 30 mg per 2 gummies | Same approved Supplement Facts transcription | Never sourced from PDP description. |
| 9 | Bacillus coagulans SNZ-1969, 1 billion CFU per 2 gummies | Same approved Supplement Facts transcription | No efficacy promise, no other organism or CFU count. Front-label OCR JSON is NOT the Supplement Facts source. |
| 10 | Contains maltitol and isomalt; not sugar-free; vegan label badge | Same approved Supplement Facts transcription | Required house label characterization. Do not infer sugar content from sugar alcohols; no grams of sugar stated. |
| 11 | $40.99 one-time; $35.25 monthly subscription | Live product .js, variant 51093850390843; plan 9909109051 | Allocation 3525 cents, current price 4099. One product every month, recurring. Strike anchor is real one-time price, not $57.99 compare-at. Other plans omitted, no lowest-price claim. |
| 12 | 90-day refund policy with eligibility; free shipping over $69 | Live product banner and https://wellnessnest.co/policies/refund-policy | Fetched HTML/text in sources/. First orders only, conditions/exclusions apply. No unconditional risk-free claim. |
| 13 | TrustScore 4.2, 1,144 store reviews | state/trustpilot/wellnessnest.json fetched_at 2026-10-19T03:00:23.231Z, https://www.trustpilot.com/review/wellnessnest.co | Exact score/count. Store score, not product rating. No rounding or 5-star aggregate claim. |
| 14 | Three real five-star service reviews | Tonya https://www.trustpilot.com/reviews/6abe1771497e18bd92cada2f (2026-10-01); Mel Barrett https://www.trustpilot.com/reviews/6a8df7438bab5ca2e585cf7f (2026-08-25); Sheila George https://www.trustpilot.com/reviews/6a6290e86c004fbb3f74b3a9 (2026-07-24) | Verbatim strings including trailing spaces from today's permitted snapshot. Only Tonya marked verified. Sheila's quote also occupies main proof slot. Store service, not clinical endorsement. |

## Editorial guidance, not measured outcomes

Seven numbered suggestions are an editorial list count, not seven study findings. Pills being a chore is framed conditionally. No claim that gummies improve adherence versus capsules. Checking sweeteners and planning a reminder are suggestions, not clinical findings. Chart 02 shows study design, not effect size; chart 04 is a labeled checklist, not invented statistics. Both retain unique generated image assets in the spec, while the reference renderer uses chart media in those slots.

## Image provenance

Fresh slug: landing-florafresh-listicle-261019. row1 through row7 and avatar generated in foreground via article_images.py --square --ugc --qc with the required common ART direction and no people's faces. All passed QC; row1 and row3 required one retry each. No persona references. Each numbered row owns a unique scene.

Pack slots use product_refs/florafresh-vaginal-probiotics-gummies.png converted to padded real-pack.webp (32,276 bytes). No cutout exists; pack_images omitted. No generated pack or whitelist assertion, no label-gate PASS claimed. Read original pack and 2x logo crop: vertical white Wellness Nest text, stylized ribbon/leaf W retained. Real pack reused only in hero/bridge/proof/offer/product slots, not numbered-row scenes. No lifestyle pack generation.

Live gallery inspection found misleading asset names: FloraFresh_-_Vaginal_Probiotics_Gummies_Fact.png contains testimonials, not Supplement Facts. Its downloaded filename supplement-facts.png is historical capture only, NOT a verified facts panel or page asset. Gallery assets repeat unsupported claims and include faces. All excluded from page. Approved local Supplement Facts transcription remains the formula authority.

Palette source: product_refs/florafresh-vaginal-probiotics-gummies.palette.json, #d17a85, hue 12.3. No opt-out or recolor override.

## Deliberately excluded

Wrong PDP formula; sugar-free claim; vaginal pH, odor, infection or fertility outcomes; gummy adherence superiority; fixed time to habit formation; customer-count gallery overlays; clinical recommendations or invented experts; unconditional guarantees; countdowns; urgency; lab/COA selling claims. NIH ODS returned a bot wall and was not used. ISAPP abstract fetched but not used because it did not establish the needed specific claim.

## Copy craft pass

Six-part toolkit: clear audience and routine hook; concrete breakfast/planner/label visuals; every external claim mapped above; objections cover pills, sweeteners, evidence limits, symptoms and recurring price; ease and predictability emphasized without forced novelty/speed claims; plain verbs retained where stronger verbs would overstate evidence. Seven short rows, two paragraphs each; evidence-gap callout. Primary conversion goal is label inspection, not a treatment promise. Benchmark structure retained without borrowing competitor claims.

## Run results

- validate_landing.py: PASS, zero placeholders, three store links checked.
- landing_publisher.py local preview: PASS. Packaging hue and all contrast checks PASS.
- landing_qa.mjs: no overflow, clipped text, small targets or broken images at 375, 768 and 1440. Desktop/mobile screenshots read visually. Sticky probes returned null, so sticky reveal is not verified by this local QA.
- Inline assert checks: reviews match source text/name/rating exactly; seven unique numbered-row images; every numbered row has two paragraphs of 15-30 words. PASS.
- Advisory copy_hardrules_gate.py: exit 1, only expected page-context findings: approved product-card amounts and FDA disclaimer disease verbs. No other findings. This is not recorded as a PASS.
- JEV benchmark, four calls: new 6.55 vs reference 4.95 overall. New lower on headline hook (4.35 vs 7.58), offer CTA (4.42 vs 5.48), mobile readability (4.03 vs 6.23); higher on other nine criteria. Overall win, not a section-by-section sweep. Output bench.json plus benchmark ledger. No efficacy or urgency claims added to improve scores.
- landing_publisher.py --draft: page 166314115387 created UNPUBLISHED; handle gsl-preview-florafresh-listicle-261019. No live action, theme installation, article/ticket change or commit.
- Real-storefront guarded QA deferred to the wrapper as requested; local screenshots are not claimed as real-storefront approval.

# Claims log: AgeAura NMN + TMG listicle

Fetched: 2026-10-17. Product: `ageaura-pure-nmn-tmg-nad-complex`.

| Claim | Source | How verified |
|---|---|---|
| AgeAura product identity is Pure NMN + TMG NAD+ Complex | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | Live PDP and `/products/<handle>.js` fetched this run; handle allowlist checked with `scripts/ageaura_rules.py`. |
| PDP price is $69.95 one-time | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.js | Live JSON fetched this run: variant price `6995`. |
| Subscribe & Save is $59.46 every four weeks at 15% discount | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.js | Live JSON fetched this run: selling plan `9884729659`, 15% adjustment, allocation `5946`. |
| PDP lists 500 mg NMN and 250 mg TMG per daily serving | https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex | PDP HTML fetched this run; amounts kept in product and offer blocks only. |
| Product label states 60 Capsules and 30 Servings | `product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json` | Existing OCR-accepted label record; no dosage claim added to narrative. |
| Huang trial tested NMN in 66 adults aged 40 to 65 for 60 days; NAD+/NADH rose 38% from baseline in the NMN group and 14.3% in placebo | https://doi.org/10.3389/fragi.2022.851698 | Europe PMC core record fetched this run; figures copied from abstract. |
| Morifuji trial tested NMN in 60 older adults for 12 weeks; four-meter walk result differed, primary stepping test did not | https://doi.org/10.1007/s11357-024-01204-1 | Europe PMC core record fetched this run; abstract distinguishes primary and secondary outcomes. |
| Olthof trial tested betaine separately in healthy adults for six weeks | https://doi.org/10.1093/jn/133.12.4135 | Europe PMC core record fetched this run; abstract reports four groups and fasting homocysteine findings. |
| No combined NMN + TMG human trial found in targeted search | https://europepmc.org/search?query=nicotinamide%20mononucleotide%20trimethylglycine | Europe PMC search fetched this run; zero hits for title/abstract query. Framed as an evidence gap, not proof of impossibility. |
| TrustScore 4.2, 1,144 reviews, and three service reviews | `state/trustpilot/wellnessnest.json`, https://www.trustpilot.com/review/wellnessnest.co | State file fetched at `2026-10-17T02:30:17Z`; quotes copied verbatim, all 5-star URLs retained. Reviews describe service/subscription only, not product efficacy. |
| 90-day guarantee and free shipping over $69 | Live PDP and https://wellnessnest.co/policies/refund-policy | PDP/policy HTML fetched this run; wording limited to published store language. |

## Deliberately left out

- No claim that NMN + TMG works better together. No combined human trial was found.
- No claim that NMN increases energy, reverses aging, extends life, treats disease, or improves cognition. The label's marketing phrases are not presented as clinical findings.
- No TMG claim about NAD+ production. The betaine study was separate and measured homocysteine.
- No expert quote, invented testimonial, countdown, scarcity, fake rating, or fabricated review.
- No COA, laboratory-testing, purity, or third-party-verification claim. PATI rules prohibit presenting those as an AgeAura advantage.
- No dosage-with-units in numbered narrative rows. Amounts appear only in product/offer copy sourced to the PDP.
- No competitor, Urolithin A, peptide, or alternate AgeAura handle.

## Image QA

- All images generated foreground-only with `scripts/article_images.py --square --qc`; no-face editorial scenes passed QC.
- `hero.webp`, `offer.webp`, `expert.webp`, and `bridge.webp` composite the real `product_refs/ageaura-pure-nmn-tmg-nad-complex-cutout.png`.
- `scripts/landing_label_gate.py` returned `LABEL PASS` for all four pack images on 2026-10-17.
- 2x mark crop visually matches the cutout's black stacked S-curved mark and vertical Wellness Nest wordmark.
- No generated image used twice for numbered rows. Every numbered row has a distinct image.

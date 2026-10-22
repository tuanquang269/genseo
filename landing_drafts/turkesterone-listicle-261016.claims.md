# Claims log: Turkesterone listicle

Checked again 2026-10-16 from this review. Read-only GETs only. No Shopify write.

| Claim | Source | How verified |
|---|---|---|
| Acute human study enrolled 11 apparently healthy males and measured IGF-1 and resting metabolic rate before, 3 hours, and 24 hours after ingestion | [Harris et al., Muscles 2024](https://doi.org/10.3390/muscles3040031) | Europe PMC abstract fetched 2026-10-16. Abstract: "eleven apparently healthy males" and samples "pre-, 3H post-, and 24H post-ingestion." |
| No significant condition, time, or interaction effects. IGF-1 rose without reaching significance. | [Harris et al., Muscles 2024](https://doi.org/10.3390/muscles3040031) | Europe PMC abstract: "failed to reveal any significant main condition, time, or interaction main effects" and "non-significant serum IGF-1 concentrations increased." |
| Ecdysterone and turkesterone are two named compounds in a 2024 narrative review. The paper is a review, not a controlled trial. | [Todorova et al., Nutrients 2024](https://doi.org/10.3390/nu16091382) | Europe PMC record fetched 2026-10-16. Authors are Todorova V, Ivanova S, Chakarov D, Kraev K, Ivanov K. Publication type is Review. The earlier "Wozniak" byline was wrong and was removed. |
| 2025 paper studied maral root, ecdysterone, and turkesterone in *Caenorhabditis elegans*, not people, and not this product | [IJMS 2025](https://doi.org/10.3390/ijms26083739) | Europe PMC abstract fetched 2026-10-16 |
| Title, one-time price $75.00, compare-at $119.98, featured image, in stock, no selling plan | [Live PDP JSON](https://wellnessnest.co/products/turkesterone-advanced-formula.js) | Fetched 2026-10-16. `price` 7500, `compare_at_price` 11998, `selling_plan_groups` empty. |
| Pack lines used in copy: wellness nest, Premium Turkesterone, Advanced Formula, 60, Capsules, Dietary Supplement | `product_refs/turkesterone-advanced-formula.label.json` | Whitelist read 2026-10-16. `60` and `Capsules` are separate lines. Copy says 60 capsules only in that form. |
| 90-day money-back guarantee on the first order, with eligibility rules | [Refund policy](https://wellnessnest.co/policies/refund-policy) | Fetched 2026-10-16. First order of each product, request within 90 days of delivery, other limits on the policy. |
| Free shipping on orders over $69 | Live storefront ticker | Homepage and the Turkesterone product page both showed "Free Shipping on Orders Over $69" on 2026-10-16. The earlier "$70+" line was wrong. |

## Deliberately omitted

- No milligram amount, serving count, day-supply, or "take 2 daily." The label whitelist has no Supplement Facts panel. The live PDP description does state 500 mg turkesterone, 300 mg KSM-66 ashwagandha, 250 mg tongkat ali, 250 mg colostrum, 10 mg BioPerine, and "60 capsules per bottle. Take 2 daily with food." Those numbers are not on the whitelist (RapidOCR did not agree on the ingredient lines, and no milligram token was read). They are not used as page claims.
- No product-effect claim from the PDP description.
- The 2024 review abstract does not say "evidence remains limited." That sentence was removed. The limited human result is the Harris abstract, cited on its own row.
- No claim that ecdysterone findings are turkesterone findings.
- No claim that the worm study predicts human muscle growth. The abstract's healthspan sentence is about ecdysterone in *C. elegans*, and the page does not repeat it as a human or product result.
- No claim that this exact product has a published human trial.
- No `pack_images` entry and no whitelist pack-shot pass. There is no `product_refs/turkesterone-advanced-formula-cutout.png`. Hero, bridge, expert, and offer use the live PDP photo.
- TrustScore 4.2, the 1,144 count, and the three review quotes are still the Mac run's `state/trustpilot/wellnessnest.json` lines. Trustpilot returned a bot wall here, and `state/` is not in git, so this review did not re-verify them.

## Left for Kevin

- Trustpilot score, count, and the Tonya, Martin, and Jindřich quotes need a fresh read of Trustpilot before the page is approved.
- The jar photo shows ingredient lines the whitelist does not accept (KSM-66, colostrum, tongkat ali, BioPerine). The page shows the real PDP photo and does not transcribe those lines into claims.

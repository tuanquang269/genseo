# QA: Turkesterone listicle, 2026-10-16

Unpublished draft only. No Shopify write, no publish, no theme edit.

Spec: `landing_drafts/turkesterone-listicle-261016.json`
Handle: `gsl-preview-turkesterone-listicle-261016`
Template: `gsl-ref-listicle-v2` with `style: premium` (the daily listicle lane). The reference structure is the gsl-ref listicle. v1 has no premium CSS, and `validate_landing.py` rejects premium on v1, so the suffix stays v2.

The 2026-10-16 daily commit (`9f6bdc6`) recorded `validate=1`, `qa=ok`, `palette=ok`, `real=skip`, and no Shopify page.

## Gates

| Check | Before | After |
|---|---|---|
| `validate_landing.py` | Fail. On this machine the spec's `pack_images` entry fails closed (no macOS Vision), and the scene files in `tmp_images/` are gitignored so they were missing. The Mac run failed validate with the images present. The claims log says the generated pack shot did not pass OCR, and the spec still listed `pack_images`, which is a whitelist claim. | Pass, after `pack_images` was removed and the gate only asks for generated pack shots when a cutout exists. |
| `turkesterone_rules.py --spec` | Pass (0) | Pass (0) |
| `packaging_palette.py --spec` | Pass (0) | Pass (0) |
| `landing_palette.py check` (rendered body) | Pass on the Mac (`palette=ok`). Not re-run here before the re-render because Pillow was missing, then the render passed. | Pass. Pack file hue 142.5 `#2c7f28`. CTA `#023902` hue 143, accent `#32742f` hue 143, sage `#ebf5e9` hue 141. Accent chroma 0.123. WCAG AA pairs all at least 5.11:1. |
| `brand_rules.spec_violations` | Pass (0) | Pass (0) |
| Local layout check, Chrome, 375 / 768 / 1440 | Mac `qa.json` was ok (no overflow, no clipped text, no broken images). | Same: no overflow, no broken images, no horizontally clipped text. |
| Shopify real QA | Skipped. No page was created. | Still skipped. This review did not create a page. |

`turkesterone_rules.py` on the full `body.html` still flags CSS percentages (100%, 60%, and so on) because the stylesheet sits in the same file as the product name. The committed body from `9f6bdc6` fails the same way. The visible copy, with `<style>` removed, has 0 violations.

## What was wrong, and what changed

- **Author.** The Nutrients 2024 review is Todorova et al., not Wozniak. Europe PMC record for doi:10.3390/nu16091382, fetched 2026-10-16. The chart credit and the source line now say Todorova.
- **Unsupported "limited evidence" sentence.** That review's abstract does not say the evidence is limited. The row now says the paper is a review of two named plant steroids, not a controlled trial. The limited human result stays on the Harris 2024 row, which the abstract supports: 11 apparently healthy males, IGF-1 and resting metabolic rate at baseline, 3 hours, and 24 hours, no significant condition, time, or interaction effect, and a non-significant IGF-1 rise.
- **Shipping.** The page said free shipping at $70+. The live homepage and the product page ticker, fetched 2026-10-16, say "Free Shipping on Orders Over $69". Copy now says over $69.
- **Price and guarantee, kept.** PDP JSON: $75.00, compare-at $119.98, no selling plan. Refund policy: 90-day money-back guarantee on the first order, with eligibility rules. The offer line now says eligibility rules apply.
- **Hero, bridge, and expert showed the wrong pictures.** The hero used the research-papers still and the alt claimed a jar. The bridge reused the blank-grid still. The expert reused the lab still, with a jar alt. There is no cutout, so those three slots plus the offer now use the live PDP pack photo. The "60 capsules" chip sits on the jar. Scene rows keep their own stills.
- **Chart label "Compound B"** read like a missing word. It now says "Different compound". The row still does not use the product name before the bridge.
- **Alts** now describe the pictures (timer and notebook, grid paper, gym bag, PDP jar).
- **`pack_images` removed.** Listing it claimed a whitelist pack shot. OCR had already failed, there is no cutout, and `docs/LABEL_OCR_GATE.md` says this SKU uses the real PDP photo and must not claim a label-gate pass. `validate_landing.py` was also requiring `pack_images` whenever a label file exists, which forced the claim. It now requires that list only when `product_refs/<handle>-cutout.png` exists.

## Label whitelist vs the public PDP

The whitelist exists: `product_refs/turkesterone-advanced-formula.label.json`. Copy may use the front lines, including the split `60` / `Capsules` badge. It may not add a milligram, a serving count, a different capsule count, or a day-supply.

Fetched from `https://wellnessnest.co/products/turkesterone-advanced-formula.js` and **not** used as claims, because they are not on that whitelist:

- 500 mg turkesterone
- 300 mg KSM-66 ashwagandha
- 250 mg tongkat ali
- 250 mg colostrum (15% IgG)
- 10 mg BioPerine
- "Take 2 daily with food"
- "5 synergistic ingredients"

The PDP photo shows some of those ingredient names on the jar. RapidOCR did not agree on those lines, so they were left out of the whitelist and they are not transcribed into the page. The photo itself is the live pack shot.

## Layout

Desktop and mobile screenshots are `landing_drafts/turkesterone-listicle-261016/desktop.jpg` and `mobile.jpg`.

- UI greens track the pack (`#2c7f28`, black lid). CTA, top bar, numbers, and the offer pill are the dark green the palette gate measured.
- The hero product is visible above the fold. The offer card repeats the same pack, the $75.00 price, the $119.98 compare-at, and a "SEE INGREDIENTS" button to the live PDP.
- "FREE shipping over $69" wraps onto a second line inside the offer meta. It is fully visible at 1440 and 375.
- The byline role "Wellness Nest editorial team" wraps so "team" sits on its own line. That role string is the daily-lane byline. Left as is.
- Scene stills in these shots were rebuilt from the committed full-page jpeg, because `tmp_images/` is gitignored. They are softer than the Mac originals. If those originals are still on the Mac, keep them and re-render. The pack slots should use the live PDP image either way.
- The byline mark in these shots is a crop of the purple flower on the PDP photo, for the same reason. A Mac `avatar.webp` from the daily run can replace it on re-render.

## Left for Kevin

- TrustScore 4.2, the count 1,144, and the Tonya, Martin, and Jindřich quotes are still the Mac run's `state/trustpilot/wellnessnest.json` lines. Trustpilot returned a bot wall from this environment, and `state/` is not in git. Confirm them before approval.
- Whether the page should ever state the PDP milligram lines. That needs a new label read in the whitelist. This draft does not add one.
- This PR also changes `scripts/validate_landing.py`, so it was not merged. The page is still not on Shopify.

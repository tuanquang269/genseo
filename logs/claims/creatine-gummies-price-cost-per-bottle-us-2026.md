# Claim checks — CA1016-5

Checked 2026-10-18. Automated source review; not a human or laboratory review. Title, meta, table, FAQ and alt text checked against these same sources. No powder price, independent assay, shipping speed, customer count or health-outcome claim asserted.

Claim | Source URL | fetched+confirmed Y/N
--- | --- | ---
FusiForce product price is $69.99 at check time | https://wellnessnest.co/products/fusiforce-creatine-gummies.js and https://wellnessnest.co/products/fusiforce-creatine-gummies | Y — HTTP 200; price 6999 cents; rendered listing $69.99
Green Apple and Blueberry variants both list $69.99 | https://wellnessnest.co/products/fusiforce-creatine-gummies.js | Y — both variants 6999 cents
Green Apple pack is a bright-green stand-up pouch, not a bottle | https://wellnessnest.co/products/fusiforce-creatine-gummies | Y — curated PDP crop product_refs/fusiforce-creatine-gummies.png visually opened; matches product_refs/fusiforce-creatine-gummies.json
Pictured Green Apple pack count is 90 gummies | https://wellnessnest.co/products/fusiforce-creatine-gummies | Y — visibly printed 90 GUMMIES on curated live-PDP crop; matches product_refs/fusiforce-creatine-gummies.label.json
Live product description states a three-gummy serving and three gummies daily | https://wellnessnest.co/products/fusiforce-creatine-gummies.js | Y — fetched description; stated amount, not independent testing
Live product page states 5,000 mg creatine per serving | https://wellnessnest.co/products/fusiforce-creatine-gummies and https://wellnessnest.co/products/fusiforce-creatine-gummies.js | Y — rendered page and description agree; explicitly attributed to seller, not an assay
90 gummies divided by three per serving equals 30 calculated servings | https://wellnessnest.co/products/fusiforce-creatine-gummies | Y — arithmetic from confirmed pack count and live description; conditional on purchased package matching
$69.99 divided by 30 equals $2.333, approximately $2.33 per serving before checkout charges | https://wellnessnest.co/products/fusiforce-creatine-gummies | Y — arithmetic; runnable assert retained below
If purchased pack confirms 90 gummies and three daily, calculated supply is 30 days and product-only cost about $2.33/day | https://wellnessnest.co/products/fusiforce-creatine-gummies.js | Y — explicitly conditional arithmetic, not unconditional supply claim
FDA is not authorized to approve supplements for safety and effectiveness before marketing | https://www.fda.gov/food/dietary-supplements/information-consumers-using-dietary-supplements | Y — HTTP 200 fetched with browser User-Agent; exact DSHEA statement confirmed
FusiForce, two browse collections, three related guides and author page are linked as live destinations | https://wellnessnest.co/products/fusiforce-creatine-gummies ; https://wellnessnest.co/collections/best-seller ; https://wellnessnest.co/collections/mens-essential-collection ; https://wellnessnest.co/blogs/news/where-to-buy-creatine-gummies-5-label-checks-us-2026 ; https://wellnessnest.co/blogs/news/creatine-gummies-dosage-how-many-a-day-us-2026 ; https://wellnessnest.co/blogs/news/creatine-gummies-vs-powder-which-should-you-actually-take ; https://wellnessnest.co/pages/dr-marcus-hale | Y — product/collections/guides fetched HTTP 200; author checked by validator before publish

## Runnable arithmetic check

```bash
python3 - <<'PY'
from decimal import Decimal, ROUND_HALF_UP
count, serving, daily = 90, 3, 3
price = Decimal('69.99')
assert count // serving == 30 and count % serving == 0
assert count // daily == 30
assert (price / (count // serving)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP) == Decimal('2.33')
assert Decimal('2.33') * 30 != price  # rounded daily cost must not replace pack price
print('PASS: conditional serving and daily-cost arithmetic')
PY
```

## Research limits

WebSearch was attempted twice (creatine gummies price/cost versus powder); both calls returned zero result blocks. No top-three ranking or PAA claims are asserted. NIH ODS consumer fetch returned 403; no NIH claims included. FDA source fetched successfully through urllib with browser User-Agent. No same-day powder quote was verified: draft does not state a powder price or that either format is cheaper. Marketing claims on the FusiForce PDP were not independently verified and are explicitly not endorsed. Image QC: four final PASS, two inline rerolls; no-face lane throughout, curated reference used for every product image.

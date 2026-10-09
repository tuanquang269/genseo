# AgeAura product guard (2026-10-09)

AgeAura promotes one SKU:

`https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex`

The handle `ageaura-pure-urolithin-a`, every other AgeAura handle, and `/collections/ageaura` must not enter a new ticket, landing brief, listicle, advertorial, image prompt, llms.txt draft, or IndexNow submission.

The allow/deny list is `scripts/brand_rules.py`. Ticket builders, landing builders, `article_images.py` / `ad_assets.py`, `shopify_publisher.py` (publish, update, and IndexNow), and `scripts/llms_txt_draft.py` call it. `lint_tickets.py` and `validate_article.py` / `validate_landing.py` fail closed on the same helper. An ambiguous "AgeAura" with no NMN + TMG product is rejected by the gates and locked to the Pure NMN + TMG product by `prepare_ticket()` / `prepare_image_request()`.

```bash
python3 -m unittest tests/test_ageaura_guard.py
python3 scripts/llms_txt_draft.py --from-product-refs
```

The llms command writes a local draft only. It does not upload. FloraFresh, FusiForce, and shilajit-gummies formula lines are included only when they match the label source of truth (`scripts/llms_formula.py`, `docs/LABEL_OCR_GATE.md`). The Urolithin A PDP is omitted.

## Left for a Kevin GO

- The live PDP `https://wellnessnest.co/products/ageaura-pure-urolithin-a` was still HTTP 200 on 2026-10-09. This change does not unpublish it and does not edit the theme or store settings.
- The already-published Urolithin article and the DONE ticket in `daily-tickets.md` stay as they are.
- `product_refs/ageaura-pure-urolithin-a.json` stays on disk as a packaging record. Generators refuse that handle instead of downloading the live PDP.

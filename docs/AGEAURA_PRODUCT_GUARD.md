# AgeAura product guard (2026-10-09, handle gate 2026-10-10)

AgeAura promotes one SKU:

`https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex`

The handle allow/deny list is `scripts/ageaura_rules.py` (`ALLOWED_HANDLES` / `DENIED_HANDLES`, `classify_handle`, `require_target`). `scripts/brand_rules.py` merges that list with the other product guards. Do not copy the handle into a third file.

`ageaura-pure-urolithin-a`, any other handle containing `urolithin`, every other `ageaura-*` product handle, and `/collections/ageaura` must not be the target of a new ticket, landing brief, listicle, advertorial, image prompt, llms.txt draft, or IndexNow submission. `require_target()` raises before a builder writes `product=<handle>` or `/products/<handle>`. `validate_landing.ageaura_target_errors()` fails a spec whose product handle, `product_ref`, or `/products/` URL is denied, including when the visible name still says NMN + TMG. A campaign slug such as `ageaura-nmn-listicle-261008` is not a product handle.

```bash
python3 scripts/ageaura_rules.py --brief
python3 scripts/ageaura_rules.py --handle ageaura-pure-nmn-tmg-nad-complex
python3 -m unittest tests/test_ageaura_handle_gate.py tests/test_ageaura_guard.py
python3 scripts/llms_txt_draft.py --from-product-refs
```

`--brief` names the refused handle for the operator. Do not paste it into a ticket.

The llms command writes a local draft only. It does not upload. FloraFresh, FusiForce, and shilajit-gummies formula lines are included only when they match the label source of truth (`scripts/llms_formula.py`, `docs/LABEL_OCR_GATE.md`). The Urolithin A PDP is omitted.

## Left for a Kevin GO

- The live PDP `https://wellnessnest.co/products/ageaura-pure-urolithin-a` was still HTTP 200 on 2026-10-09. This change does not unpublish it and does not edit the theme or store settings.
- The already-published Urolithin article and the DONE ticket in `daily-tickets.md` stay as they are.
- `product_refs/ageaura-pure-urolithin-a.json` stays on disk as a packaging record. Generators refuse that handle instead of downloading the live PDP.

# Local llms.txt draft

`llms.txt` in this directory is a local draft. It is not uploaded to Shopify, and it is not a ranking file (see `knowledge_base/AEO_GEO_GUIDELINES.md` §6.8).

Regenerate it with:

```bash
python3 scripts/llms_txt_draft.py --from-product-refs --out deploy/llms-txt/llms.txt
```

Formula lines are included only when they match the label source of truth. The Urolithin A PDP is omitted. See `docs/LABEL_OCR_GATE.md`.

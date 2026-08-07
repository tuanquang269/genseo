# Theme assets (versioned copies)

- `shop-this-article.liquid` — copy of `sections/shop-this-article.liquid` on the LIVE theme
  `183190880571` ("WN Shopify Theme - 02072026"), wellnessnest1.myshopify.com. Deployed
  2026-08-07 from ~/Downloads/shop-this-article.liquid with 4 mods: (1) content selector
  `[id^="BlogContent-"]`, (2) recolor to WN green `#54b94a` (+ darkened accents, white button
  label), (3) `{% schema %}` block appended, (4) handle split chain `| remove: '\'` (strips the
  JSON-LD escaped-quote artifact). Wired into `templates/article.json`
  (order: main, shop-this-article, newsletter).
- This is a DIFF BASE, not a deploy source — the live theme asset is the truth. Re-fetch via
  Admin API before editing; after any theme-side change, refresh this copy.

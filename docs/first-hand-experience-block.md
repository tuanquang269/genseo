# First-hand experience block

Blog articles can show one or two real quotes. The block is optional. If `data/experience_quotes.json` has no eligible quote for that product and topic, the block is left out. Nothing is invented to fill the space.

Search Engine Land's 16 October 2026 piece ("Human experience is your content's biggest differentiator") is the reason this exists. A made-up customer, a made-up star rating, or a byline that says the author tried the product is an FTC and brand-safety problem on a supplement article. This pipeline does not do that.

Landing pages are a separate path. Their review cards stay under `scripts/validate_landing.py`. Do not copy those cards into the blog file from this doc.

## What renders

`scripts/experience_block.py` is the only renderer.

```bash
python3 scripts/experience_block.py render --draft published_drafts/<slug>.md
python3 scripts/experience_block.py render --draft published_drafts/<slug>.md --with-method
python3 scripts/experience_block.py audit --draft published_drafts/<slug>.md
python3 scripts/experience_block.py lint
```

`render` prints a quote block or prints nothing. Paste a non-empty quote block verbatim above `### About the Author`, with a blank line before and after. If stdout is empty, do not add a heading, a placeholder, or a generic sentence.

The block carries the quote, the attribution, the source type, the date, and a source link or a source id. It does not show stars.

`--with-method` may also print a "How we checked this" line. That line is not a testimonial. Paste it only when the command prints it. Do not write your own version.

## Evidence file

`data/experience_quotes.json` is the contract. Rows with `"example": true` document the shape and never render, including the complete-looking sample whose `usage_allowed` is true. The quote text on those rows says `EXAMPLE SHAPE ONLY` so it cannot be mistaken for a person.

A row renders only when every one of these is true:

| Field | Rule |
|---|---|
| `example` | Omitted or false. `true` never renders. |
| `id` | Lowercase letters, digits, hyphens. Stable. |
| `product` | Shopify handle the article links, and not a denied AgeAura handle. |
| `topic_tags` | One or more phrases. At least one must appear in the article title, an H2/H3, or the meta description. A mention only in the body does not match. Tags shorter than 3 characters are rejected. |
| `quote` | The exact sentence to show. It must end with `.`, `!`, or `?`. |
| `attribution` | The name or label that may be shown. |
| `source_type` | `verified_review`, `creator_submission`, or `internal_staff_test`. |
| `source_url` or `source_id` | At least one. A URL must be `http` or `https`. `example.com` and `localhost` do not count. |
| `date` | `YYYY-MM-DD`. |
| `usage_allowed` | JSON boolean `true`. The string `"true"` does not count. |
| `consent` | Where consent lives (a file, a ticket, a date). This note is not printed. An empty consent field blocks the row. |
| `received_product` | Required for `creator_submission`: `free`, `purchased`, or `none`. `free` prints `Received product free`. |
| `disclosure` | Required for `internal_staff_test`. Printed when set. Use it for an employment or material-connection line the person agreed to. |
| `persona_handle` | Optional roster handle when the quote is that person's own note. It does not let the byline say they use the product. The byline stays the roster sentence. |

At most two quotes are printed. A closer topic match comes first, then a newer date.

The quote text also has to pass the article claim gate: `geo_citability.compliance_issues` and `brand_rules.violations`. A cure, treat, or prevent claim, an FDA-approval claim, a "clinically proven" claim, or a label claim those modules reject (for example a sugar-free FloraFresh line) does not render. The same gate still runs on the whole article, so a quote cannot sneak a claim past `validate_article.py`.

`python3 scripts/experience_block.py lint` exits 1 when a non-example row fails those rules.

## How the team adds a real quote

1. Start from a real source you can point at: a review URL or review id, a creator's submitted line, or a staff note a named person actually wrote.
2. Copy the words verbatim. Do not tidy them into a stronger claim. Do not add a star rating, a result they did not state, or a disease outcome.
3. Fill `consent` with where the usage permission is recorded, and set `usage_allowed` to `true` only after that permission exists.
4. Set `received_product` to `free` when the person got the product free. The block then prints `Received product free`. `purchased` and `none` print no automatic line. `none` means you are attesting there is no material connection. The script does not infer that.
5. For a staff note, set `source_type` to `internal_staff_test`, set `persona_handle` to their roster handle, and put the disclosure they agreed to in `disclosure` (for example that they work on the brand).
6. Pick `topic_tags` that are in the titles you want the quote to join. A shipping comment tagged only `shipping` will not attach to an article whose title and headings never say shipping.
7. Run `lint`, then `render` on a draft that links the product. Confirm the stdout is the quote you added and that `audit` does not fail.
8. Update `tests/test_experience_block.py` `test_shipped_catalog_is_examples_only`. That test is the tripwire that this file still has no live quote. A real row should fail `example: true` and should pass `lint`.

Do not add a quote you would not show a regulator next to its source URL.

## How we checked this

Some products already have a label check inside `validate_article.py`. For those, `--with-method` prints one sentence that names the check and says it is not a personal trial:

| Product | What the sentence points at |
|---|---|
| FloraFresh | `scripts/florafresh_rules.py` (Supplement Facts: the strain and CFU live there, not in the front-of-pouch OCR file) |
| Shilajit Shockwave | `product_refs/shilajit-shockwave.label.json` |
| Pure Shilajit Gold Resin | `product_refs/pure-shilajit-gold-resin.label.json` |
| ShilaSource Himalayan Shilajit Resin | `product_refs/shilasource-himalayan-shilajit-resin.label.json` |
| Turkesterone Advanced Formula | `product_refs/turkesterone-advanced-formula.label.json` |

The sentence does not restate a dose. The primary product is the handle linked most often in the draft. Other products get no method line, because this script will not claim a check the article gate does not run.

The article gate does not compute a price per serving. It only checks that a dollar amount appears. This block does not say we did price math.

## Gate

`validate_article.py` and `shopify_publisher.py` both call `experience_block.audit` before a publish or update. The publisher call happens before image upload and before the article request.

Hard fails:

- A rendered quote with no id, no matching evidence row, `usage_allowed` not true, `example: true`, a missing source, or a claim-gate failure.
- Quote text, attribution, date, source, or disclosure that does not match the row.
- More than two quotes.
- A star rating, a "what customers say" / verified-buyer line, a markdown or HTML blockquote, or an attributed first-person quote outside the block.
- "I tried", "our team tested", and the same personal-use lines, including in the byline. A quote inside the block may contain those words. The byline may not.
- A "How we checked this" sentence that is not the one method line above.

Warning, not a failure: the article has no experience block. While the file has only example rows, every article warns. Do not invent a quote to clear it. `✓ PASS` still prints when nothing else fails.

## Decisions that need a GO

These are not done in this change:

- Importing reviews from the Shopify review app, Judge.me, or the Trustpilot snapshot the landing drafts use (`state/trustpilot/`, gitignored). Some of those lines are store-service comments. At least one landing quote states a disease outcome the claim gate would reject. Each blog row still needs its own source, date, consent note, and `usage_allowed: true`.
- Who may write an `internal_staff_test`, and the exact disclosure sentence.
- A price-per-serving line. That needs a real calculation the article pipeline stores, which it does not do today.
- A method line for FusiForce, AgeAura, or shilajit gummies. FusiForce and the gummies label files feed the llms.txt draft and the landing label gate, not the article dose check. AgeAura's article gate is the SKU lock (Pure NMN + TMG only), not a label-dose read.

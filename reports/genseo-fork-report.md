# GenSEO multi-store fork, 2026-10-27

The fork now has separate Wellness Nest and Cherish profiles. New runs require
`--store`. The original Wellness Nest daily job, writer prompt, queue, and daily
volume stay unchanged. The installed job currently targets five posts per day.
No Cherish job was installed. No article was created, changed, or published.

## Implementation

- `scripts/run_store.py` is the explicit-store entry point. `stores/<id>/profile.json`
  owns the store domains, credential source, context files, templates, calendar,
  volume, and gates. Unknown stores and foreign context paths fail before writing.
- Cherish uses live store `uxfaue-s1.myshopify.com`, storefront
  `thecherishcompany.com`, and blog `news` (Journal, ID `106996400355`). Its
  `SHOPIFY_CHERISH_LIVE_*` keys stay in the vault `.env`. The shared `t3_store.py`
  handles client credentials. Secret values do not enter writer context or reports.
- Cherish loads its hub, v4 brand system, product copy sources, ID registry, seven
  approved templates, and 250-row calendar. The cap is seven posts per day. The
  first 21 rows must require Kevin. The writer has no tools, global skills, or
  shared agent memory. It uses `cc/claude-sonnet-5-5` on the hosted OAuth router.
- `approval=kevin` creates an unpublished article and a local review notification.
  `approval=auto` publishes after the gates pass. Notices go to stdout and
  `state/cherish/review-notifications.jsonl`. No external message was sent.
- Gates check foreign store links and handles, live product status and prices,
  source quotes, numerical claims, duplicate calendar topics, and existing
  article handles and near-duplicate titles. Existing drafts are included.
  The render gate uses the approved template's exact `#rules-machine` block.
  FAQ answers must match the schema. A failure stops the run.
- Shopify writes re-check domain and credential source. Legacy Wellness Nest
  helpers refuse a Cherish selection. They also guard their Shopify transport.
  Articles are first created unpublished. A failed Shopify body readback blocks
  the change to live. Article CSS is scoped to the article. Preview labels and store chrome are removed.

## Verification

- 20 focused isolation, credential, template, schema, approval, and compatibility
  tests passed with `/usr/bin/python3`. Tests reject foreign context and product
  links in both directions. A wrong-domain write stops before authentication or network.
- Wellness Nest dry-run output is byte-identical before and after the change.
  Both SHA-256 values are
  `98738c08984affd83f8a2ff2bf6c17e7fd06087d924c166d01e8b78da4b485aa`.
  Evidence: `reports/wellnessnest-dry-run-before.txt` and `reports/wellnessnest-dry-run-after.txt`.
- Cherish dry-run loaded all seven first-day slots with `approval=kevin`.
  Read-only Shopify checks confirmed the live identity, blog, and seven existing
  articles. The Wellness Nest active catalog snapshot contains 21 handles.
- All seven prepared Cherish templates passed `tools/check.py` at 1440, 1100,
  900, 600, and 390 px. All machine rules passed. Fonts loaded, images loaded,
  and the minimum text size was 15.5 px. Evidence: `reports/template-render-gate.txt`.
- Python compilation and plist validation passed. The old full suite was also run.
  It reported two Python failures in queue-state assertions and two shell-file
  failures. The Python tests expect old landing queue contents. The article prompt
  test expects an open queue, but the local completion ledger has none. Those
  source and queue files are unchanged by this fork. The workspace-status shell
  test ran while this implementation was editing files. Its separate re-run passed
  all 238 assertions with an unchanged workspace. The GenSEO vault note has no lint findings.

## Enable only after Kevin approves the first 21 posts

The supplied file is `deploy/com.pati.genseo-cherish.plist`. It runs at 07:45 in
the machine's local timezone. This Mac uses Asia/Ho_Chi_Minh. RunAtLoad is false.

```bash
cp /Users/kevinkreative/genseo/deploy/com.pati.genseo-cherish.plist /Users/kevinkreative/Library/LaunchAgents/com.pati.genseo-cherish.plist
launchctl enable "gui/$(id -u)/com.pati.genseo-cherish"
launchctl bootstrap "gui/$(id -u)" /Users/kevinkreative/Library/LaunchAgents/com.pati.genseo-cherish.plist
```

## Limits and downstream effects

No AI generation or Shopify article write was executed in this lane. The OAuth
model catalog was read and the Sonnet 5.5 route was present. Live publish and
readback still need the approved first-post run. Evidence and numerical checks
cannot prove every paraphrased claim. Kevin reviews the first 21 posts.

The new explicit profile loader rejects foreign context. The original Wellness
Nest agent still has its existing tool permissions; this fork does not create an
OS filesystem sandbox for that legacy agent. Its guarded Shopify writes block
cross-store content and credentials. Keep the legacy runner for Wellness Nest.

Changing calendar length or adding a store needs a reviewed profile and guard
update. Missing packages stop a non-generation run. Missing evidence, dependencies,
or render assets stop publication. A duplicate found in Shopify after a local
ledger loss needs operator reconciliation; it is not silently recreated.

Rollback: revert this fork commit. Keep the pre-fork baseline commit `ec7a54e`.
The Wellness Nest installed wrapper and launchd plist were not changed.

VERDICT: DONE_WITH_CONCERNS — the fork and isolation gates are implemented; Cherish scheduling remains disabled pending first-21 approval and a live article check.

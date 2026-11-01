# Reconcile byline + FloraFresh 15B — 2026-10-31

One draft off `origin/main` `6c46771` so Kevin can land this instead of choosing between conflicting drafts #82 and #94. Nothing here was published. #82, #88, and #94 were left open.

Checked this run, read-only: `https://wellnessnest.co/pages/mike-moretti` returns **404**. `https://wellnessnest.co/pages/dr-marcus-hale` returns **200**. No Shopify page was created. No headshot was added (`roster.json` `headshot` is null).

## Policy this branch enforces

- Blog and new article tickets use **Mike Moretti**. The sentence after the link is the roster bio, copied verbatim: "Mike Moretti is a co-founder of Wellness Nest and the brand's public face." The role "Co-founder, Wellness Nest" is a field. A role-only line fails `validate_article.py` (`author bio is not the approved sentence`).
- A blog draft that names **Dr. Marcus Hale** or `/pages/dr-marcus-hale` fails the blog gate.
- Landing pages and listicles stay **Dr. Marcus Hale**. `genseo_roster.landing_default()` returns him. `scripts/run_landing_headless.sh` and `skills/genseo-landing-pages/SKILL.md` name him. They do not tell the landing lane to byline Mike.
- FloraFresh count is **15B CFU** of Bacillus coagulans SNZ-1969 per 2 gummies. `1 billion CFU` and `1B CFU` fail the linter. AgeAura stays the NMN + TMG complex only.
- A first-hand creator block renders only when `rights_confirmed` is true and `approved_by` is set. Every seeded line is still off, so the helper prints nothing.

## What came from which draft

| Source | Taken | Left there |
|---|---|---|
| #88 `cursor/florafresh-15b-mike-moretti-0e04` | FloraFresh 15B guard. `scripts/florafresh_rules.py` is byte-identical on #88, #90, #94, and #96 (sha256 `e1bc1c53bda7`). Tests and `docs/FLORAFRESH_FORMULA_GUARD.md` are the #88/#94 pair: a historical listicle that still says 1 billion CFU fails `--spec`. Ticket, topic-bank, and ideas copy that still named the retired count was moved to 15B. | The landing-runner sentence that switched new pages to Mike. |
| #94 `cursor/kevin-facts-guards-1024` | Roster facts and the blog gate. `roster.json` bio, role, null headshot, `default_for: ["blog"]`. `scripts/genseo_roster.py` reads this checkout's `roster.json` (`GENSEO_ROSTER_PATH` overrides; Mac path is the fallback). `blog_default()` is Mike. `landing_default()` is Hale. `tests/test_roster_byline.py`, `tests/test_blog_byline.py`, `scripts/build_rich_tickets.py`, `scripts/refill_tickets.py`. Content-writer and auto-publish byline text (copy the bio; Hale fails a blog draft; landing keeps Hale). | Two landing prompts that #88's merge had flipped to Mike: the byline sentence in `scripts/run_landing_headless.sh`, and the "Mike Moretti, fresh" bullet in `skills/genseo-landing-pages/SKILL.md`. This branch puts both back on Hale. Writer prompts that said "copy that role" and "do not invent a longer bio" were aligned with the gate, which requires the roster bio. |
| #82 `cursor/first-hand-experience-block-2d23` | Rights-gated block, unchanged in behavior: `scripts/first_hand_experience.py`, `templates/first-hand-quotes.json`, `templates/first-hand-experience-block.md`, `docs/FIRST_HAND_EXPERIENCE.md`, `tests/test_first_hand_experience.py`, the article-template note, and the SEO guideline line. Wired into `validate_article.py` and the two article skills **after** the #94 byline text. The block is blog-only and does not set a byline. Seeded quotes are AgeAura NMN + TMG (`ageaura-pure-nmn-tmg-nad-complex`) and stay off until Kevin sets both rights fields. | #82's landing sentence "New pages default to Mike Moretti" and its shorter roster bio (`"Co-founder, Wellness Nest"` with TODO strings in `headshot` and `page`). Those fight the Hale landing rule and the #94 vault bio. |
| #90 `cursor/combine-9-10-on-88-1023` | Nothing beyond the shared FloraFresh file, which already matches #88. | FusiForce and Shilajit gummies label guards, and the publisher/landing-builder edits that carry them. |
| #96 `cursor/landing-drafts-price-sweep-1026` | Nothing. The FloraFresh rules file matches. | Price-sweep landing drafts. #96 also rewrote FloraFresh listicle specs to 15B and flipped `tests/test_florafresh_guard.py` so `florafresh-listicle-261009.json` is expected to pass. This branch keeps the #88/#94 test: that file still says 1 billion CFU, and `--spec` exits 1. |

## Suite

`bash tests/run_suite.sh` on this branch (Pillow installed in the VM so the suite's interpreter can import PIL; that install is not a repo change):

- Shell files: 13 passed, 0 failed
- Python: 355 tests, 4 failed

The same 4 fail on `origin/main` at `6c46771`. They were not edited here:

- `test_landing_rotation.OpenQueueTests.test_rebalanced_open_tickets_include_both_priorities` (1 open landing line, test wants at least 7)
- `test_packaging_palette.PaletteFiles.test_remaining_pack_shots_match_the_png` (FusiForce `#97c344` vs `#9ac547`)
- `test_packaging_palette.PaletteFiles.test_shilasource_file_is_the_measured_neutral_pack` (cluster share rounding)
- `test_queue_closures.FreshCheckoutTests.test_tracked_files_close_todays_tickets_without_a_ledger` (first open landing line is Shilajit Shockwave, test wants Gold Resin)

`tests.test_roster_byline`, `tests.test_blog_byline`, `tests.test_first_hand_experience`, and `tests.test_florafresh_guard` passed. `lint_tickets.py daily-tickets.md` exited 0.

## Still needs Kevin

1. **Create `/pages/mike-moretti` on Shopify** and point it at the roster bio. Until that URL returns HTTP 200, a Mike blog draft fails the live-link check. Do not create it from this repo. Hale's page is already live, which is why landing can keep using him.
2. **A real Mike headshot**, if a photo should appear. `headshot` stays null. The two PDP portraits are not a source. Do not invent one.
3. **Creator usage rights** for the first-hand lines, if any should run. Set `rights_confirmed` and `approved_by` on only the quotes that may publish. A Trybe approve is not that permission. Until then the block stays out of articles.
4. **Unpublished FloraFresh drafts that still say 1 billion CFU** now fail `florafresh_rules.py --spec`. That includes `landing_drafts/florafresh-listicle-261009.json` and `landing_drafts/florafresh-listicle-261019.json`. The closed landing ticket `[DRAFT 2026-10-19 page 166314115387]` still records 1 billion CFU. #96 rewrote the specs (and a lot of prices). This branch did not. Live posts were not edited.
5. After this lands, **#82, #88, and #94 can be closed as superseded**. #90 still holds the gummies and FusiForce guards. #96 still holds the price sweep. This draft does not close any of them.

# First-hand experience quotes (blog articles)

Optional block for a Wellness Nest **blog article**. It is one creator or customer line, with the person's name, a paid-partnership disclosure, and a results-vary note. Search Engine Land's 17 and 20 October 2026 digests treat first-hand experience as an E-E-A-T signal for AI answers and organic results.

The block is off until Kevin confirms usage rights and the exact lines. Seeded entries stay `rights_confirmed: false` and `approved_by: ""`, so the helper prints nothing and live articles do not change.

This is the blog pipeline only (`scripts/validate_article.py`, `scripts/first_hand_experience.py`). It is not wired to Home, collections, product pages, landing pages, listicles, checkout, or the theme.

Creators named here are quote attributions. They are not roster authors. Do not add a credential, and do not put these names in `roster.json`.

## Add a quote

1. Copy a contiguous excerpt from a transcript you already have. Do not paraphrase, and do not add a result, a number, or a name that is not in that transcript.
2. `creator_display_name` is a first name plus a last initial (`Kenzie R.`).
3. `source` is the Trybe submission short id (`086ac23e`), not the long uuid.
4. `claim_check` is `personal-feel` or `structure/function`.
5. `disclosure` has to include `Paid partnership` and either `#ad` or `paid creator`.
6. Append the object to `templates/first-hand-quotes.json` with `rights_confirmed` false and `approved_by` `""`.
7. Run `python3 scripts/first_hand_experience.py --lint`. It must print `first-hand quotes: OK`.

Leave out generic efficacy lines (`a wellness brand that actually works`), CTAs (`tap the link`, `thank me later`), and the whisper hallucination `Thanks for watching`.

## Approval

Kevin approves two things before any line can render:

1. **Usage rights** for that creator's words on the wellnessnest.co blog. A Trybe Approve is not this permission, and it is not a Meta spend decision.
2. **The exact lines.** Set `rights_confirmed` to `true` and `approved_by` to his name on only the objects that may run. Leave the rest false and blank.

Both fields are required. Either one alone still skips the line.

## How an article gets the block

```bash
python3 scripts/first_hand_experience.py --product ageaura-pure-nmn-tmg-nad-complex
python3 scripts/first_hand_experience.py --product ageaura-pure-nmn-tmg-nad-complex --id hillary-e16b6841-two-capsules
```

Paste stdout only, with a blank line before and after, once, before `## Frequently Asked Questions`. A stderr `WARN` means the gate skipped the line. Do not copy a quote out of the JSON file or this doc.

`validate_article.py` stays quiet when the block is absent. It fails a draft that pastes a registry line the gate did not clear, a block whose text does not match the registry, a missing disclosure, a missing results-vary note, or a line that fails the claim lint.

## Lint

`python3 scripts/first_hand_experience.py --lint` flags a quote that contains disease, cure, treat, reverse aging, or anti-aging. It also flags a dose other than the label serving, and a missing disclosure.

The AgeAura pack label on file (`product_refs/ageaura-pure-nmn-tmg-nad-complex.label.json`) lists `60`, `Capsules`, and `30 Servings`. That is 2 capsules per serving. No milligram amount was read. The gate allows "two capsules" (including at breakfast or in the morning) and rejects any other capsule count, any mass unit, and more than once a day. The pack line `Supports Healthy Aging` is not the banned phrase anti-aging. Do not add it to a quote unless a transcript actually says it.

## Seeded lines (not cleared)

Kenzie R. is Trybe `086ac23e` (verdict 2026-10-20). Hillary H. is Trybe `e16b6841` (verdict 2026-10-19). Product handle: `ageaura-pure-nmn-tmg-nad-complex`. Hillary's whisper file is one block, so three of her lines use the full 28.9s file as the range. The `0:12-0:15` cut is the card's scored window for the two-capsule line. Kenzie's `0:00-0:02` is the opening clause; the card places the next marketing line at about 0:02, and that marketing line is not in the registry. `0:04-0:10` and `0:15-0:24` are the transcript's sentence windows.

| id | creator | time | quote |
|---|---|---|---|
| `kenzie-086ac23e-fewer-bottles` | Kenzie R. | 0:00-0:02 | Turns out I didn't need another bottle. I needed fewer |
| `kenzie-086ac23e-kids-routine` | Kenzie R. | 0:04-0:10 | support my active athletic goals and keeping up with my kids. |
| `kenzie-086ac23e-3pm` | Kenzie R. | 0:12-0:15 | it has helped me with no more afternoon crashes at 3 p.m. |
| `kenzie-086ac23e-two-capsules` | Kenzie R. | 0:15-0:24 | Keep your wellness routine simple and take two capsules at breakfast or in the morning time. |
| `hillary-e16b6841-twelve-bottles` | Hillary H. | 0:00-0:28.9 | I'm done having to use 12 different bottles just to feel like a functioning adult. |
| `hillary-e16b6841-handful` | Hillary H. | 0:00-0:28.9 | I used to take a handful of pills every morning. |
| `hillary-e16b6841-two-capsules` | Hillary H. | 0:12-0:15 | Now just two capsules with breakfast. |
| `hillary-e16b6841-3pm` | Hillary H. | 0:00-0:28.9 | I also used to dread the 3 p.m. because of the energy drop. Now it's just another hour of my day. |

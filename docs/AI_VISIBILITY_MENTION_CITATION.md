# AI visibility: mention vs citation

Search Engine Land, 14 October 2026: a brand can be named in an answer and still miss the source link, and the two lists differ by platform. This ledger records them separately.

Platforms: ChatGPT, Gemini, Google AI Mode, AI Overviews, Perplexity, Grok/X.

Brands:

- AgeAura Pure NMN + TMG NAD+ Complex. `brand_mentioned` matches AgeAura. A Urolithin-only mention does not count.
- Wellness Nest / ShilaSource shilajit. `brand_mentioned` matches ShilaSource. "Wellness Nest" alone is `store_mentioned`.
- FloraFresh Vaginal Probiotics Gummies. `brand_mentioned` matches FloraFresh.

`domain_cited` is yes only when a `wellnessnest.co` URL is in that platform's source list. A URL written in the answer prose sets `store_mentioned`. The product slug inside that URL does not count as `brand_mentioned`.

Anything not seen stays `unknown` and `observed: false`. Unknown is not a no.

## Commands

```bash
python3 scripts/aeo_tracker.py self-check
python3 scripts/aeo_tracker.py template --out /tmp/ai-visibility-template.json
python3 scripts/aeo_tracker.py validate data/ai_visibility/observations.json
python3 scripts/aeo_tracker.py report
python3 scripts/aeo_tracker.py adapt --platform gemini --prompt-id ageaura-01-best-nmn-supplement
```

`template`, `validate`, `report`, and `self-check` do not call an API. `template` will not overwrite `data/ai_visibility/observations.json`.

The shipped ledger is empty. Add a row only after a person, or a confirmed adapter call, has seen that answer. Keep working copies outside the empty file until the row is real.

## What the report does with a disagreement

- **Mentioned but not cited.** The product brand was named and `wellnessnest.co` was absent from the sources. Fix on-page citability (`scripts/geo_citability.py`, `docs/GEO_CITABILITY_AUDIT_2026-10-17.md`).
- **Cited but not mentioned.** A `wellnessnest.co` URL was in the sources and the product brand was not named. Fix the canonical name on that page.
- **Store named, product brand not.** Entity note. It is a gap of the second kind only when the citation field is also yes.

## Prompt set

51 hypothesised prompts. 18 AgeAura and 18 ShilaSource are the query lists from draft PR #75 (`cursor/offpage-listicle-gap-1020`, `data/offpage_seeds`). 15 FloraFresh prompts are topic-bank primaries. Five of those primaries are segment glue (`paste_caution` on the prompt). They were not observed in an answer engine.

PR #75's pages are a different measurement: `ai_citation_observed: false`, evidence `web search rank`. Do not copy them in as citations. Competitor name patterns are the string list from that draft, used only to mark a name that appears in answer text. FloraFresh has no pattern list because that draft did not record one. An unmatched name is not a confirmed absence.

## Adapters

| Platform | Runs when |
|---|---|
| Gemini | `GEMINI_API_KEY` is set. Model defaults to `gemini-1.5-flash` (the model this repo already calls). `GEMINI_VISIBILITY_MODEL` overrides it. |
| ChatGPT | `OPENAI_API_KEY` and `OPENAI_VISIBILITY_MODEL` are both set. |
| Perplexity | `PERPLEXITY_API_KEY` and `PERPLEXITY_MODEL` are both set. |
| Grok/X | `XAI_API_KEY` and `XAI_VISIBILITY_MODEL` are both set. The request does not add a search tool; citation stays unknown unless the response includes a `citations` list. |
| Google AI Mode, AI Overviews | No adapter. Enter the row by hand. |

A missing key or a missing model skips. A failed call writes nothing. `--write` appends only a row that validates.

The old `python3 scripts/aeo_tracker.py "query"` loop still runs. With no key it writes `AEO_ACTION_TICKETS.md` in this repo with both fields unknown. With a key it counts mentions in answer text and leaves citation unknown.

# Ticket refill — keep `daily-tickets.md` stocked

The daily wrapper hard-stops when no ticket is open; on 2026-10-09 that ended the day at 1/5.
`scripts/refill_tickets.py` appends gated, product-mapped PENDING tickets in the house format. It never
invents topics (it picks from `board/ideas.csv` rows with `status=idea`, then
`templates/article-topic-bank.json`) and it never writes to Shopify — it only reads the public storefront.

## Commands

```bash
python3 scripts/refill_tickets.py --self-test             # offline checks + topic-bank lint, writes nothing
python3 scripts/refill_tickets.py --count 8 --dry-run     # live store read; prints the batch + every rejection
python3 scripts/refill_tickets.py --count 8 --prefix MM   # append a "# BATCH" and update board/ideas.csv
python3 scripts/refill_tickets.py --if-below 5 --count 8  # do nothing while 5 or more tickets are open
python3 scripts/refill_tickets.py --count 8 --prefix MB --day 2026-10-12  # ids for a future day
```

- `--prefix` sets the ticket ids (`#MM1009-1`, …; numbering continues after the highest used that day): `MM` Mac
  Mini, `MB` MacBook, `CA` Cursor Cloud. Default `$GENSEO_TICKET_PREFIX`, else `RF`.
- `--day YYYY-MM-DD` sets the batch title date and the ids (default: today ICT). The build stamp, the
  in-stock date, and the dedup date stay the real clock, so a Monday MacBook queue can be prepared the
  evening before as `#MBmmdd-N`.
- `--max-per-family 2` spreads the batch across products before filling. `--offline` reuses the last store
  snapshot (`state/refill_cache.json`, gitignored) and skips STEP 0; `--no-suggest` skips STEP 0 only.
- Exit `0` done (or nothing to do) · `3` fewer than `--count` passed — whatever passed was appended; add topics ·
  `1` failed closed (store unreadable, bad topic bank, lint failure, queue changed underneath) — nothing written.

## What every ticket passed

brand_rules (AgeAura = NMN + TMG Complex only, no Urolithin, no banned links; FloraFresh claims only from its
Supplement Facts label, never the PDP description) → hero product live and in stock,
plus a live collection to link → not a covered topic (queue header rule 6) → not already in `daily-tickets.md`
in any status → not already live (same family + segment, title overlap ≥ `topic_fitness.DUP_JACCARD`, same
slug; checked against the full blog listing with full titles, plus `existing_articles.json` and the tracker CSVs
when present) → `topic_fitness.assess()` strict on primary and title: PASS, or REVIEW [covered-segment] under
Kevin's standing greenlight for mined queues (2026-08-13) → STEP 0 `suggest.json`. The batch is appended only if
the whole file passes `lint_tickets.py`. The writer still runs STEP 0 and every gate at write time.

## Daily wrapper hook (Mac)

`deploy/grokbot-genseo-daily.sh` calls refill right before its empty-queue stop, at most once per run, when
open tickets < (`GENSEO_DAILY_TARGET` − live today):

```bash
refill_tickets.py --if-below <still to publish> --count <still to publish − open + GENSEO_REFILL_BUFFER (3)> \
                  --prefix <$GENSEO_TICKET_PREFIX, else MM on the Mini (primary), MB on the MacBook (standby)>
```

It then commits `daily-tickets.md` + `board/ideas.csv` locally (`queue: refill_tickets.py on <host>`); on a Mac
that pushes, the runner's next publish push carries it. Exit 3 or 1 is logged to `logs/daily/<date>.log` and the
run continues with whatever is open (still stopping at 0, as before). The call is capped at 10 minutes.

**Off by default.** To turn it on for a Mac:

```bash
cd ~/genseo && git pull                                   # this repo version
cp ~/genseo/deploy/grokbot-genseo-daily.sh ~/bin/         # launchd runs the ~/bin copy
P=~/Library/LaunchAgents/com.pati.genseo-daily.plist
plutil -replace EnvironmentVariables.GENSEO_AUTO_REFILL -string 1 "$P"
launchctl bootout gui/$(id -u) "$P"; launchctl bootstrap gui/$(id -u) "$P"
```

To check what it would add without waiting for 07:30: `python3 scripts/refill_tickets.py --if-below 5 --count 8 --dry-run`.

## Runway

One article per brand + segment, ever, so each bank topic is used once. After the 2026-10-09 batch
(#CA1009-1…10) the bank holds 6 reserve topics, which is one more refill. To add runway:

- add a row to `board/ideas.csv` with `status=idea` (product handle, primary_keyword, working_title, segment,
  intent, template, angle; `secondary` separated by `;`), or a bank topic (rules in the bank's `_note`), then
  run `--self-test` and `--dry-run`;
- mine real demand (GSC, or the Google Ads recipe in `skills/genseo-auto-publish/references/ads-article-mining.md`)
  into board ideas, with the real volume in `volume`;
- a new segment needs a `topic_fitness.SEGMENT_MODIFIERS` entry — Kevin's call, not an agent's.

## Ideas board

`board/ideas.csv`: `id,status,product,primary_keyword,secondary,working_title,segment,intent,template,angle,volume,
source,ticket_id,added,updated,last_check`. `status`: `idea` → `queued` (refill appended it as `ticket_id`) →
`done` / `skipped` (synced from the queue on every refill). `volume` holds real data only, otherwise `No data`.
A rejected idea stays `idea`, and `last_check` gets the reason.

Cursor cloud agents may run `--self-test`, `--dry-run`, and a real run with `--prefix CA` committed in a PR;
publishing stays on the Macs.

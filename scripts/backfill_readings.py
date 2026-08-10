#!/usr/bin/env python3
"""Fold the re-screen's readings back into the verdict cache, where they can actually be used.

`verify --vision --update-qc` buys a fresh reading of every banked face and writes it to that
face's own persona.json. That is the right place for provenance and the wrong place for reuse:
the fetch path never opens a persona.json, so as things stand the harvest would pay for those
readings a second time, and could get a different answer.

Append-only, like verdict_remember: the merged row carries the other readings forward rather than
replacing them wholesale.

WHAT CHANGED ON THE SECOND RUN. The first version skipped any row whose two slots were both full,
on the reasoning that a full row is already at the confirmation count. That was true while the
incoming reading was merely *another* reading. It stopped being true the moment the rubric gained
official_or_representative_capacity, identifying_text_in_frame and minor_in_frame: now both held
readings are STALE and the incoming one is the only CURRENT one in existence for that image.
Skipping it would leave the row unable to confirm anything, and would throw away the single
reading that can answer the three questions that just threw out ten faces.

So a full row now gives up its OLDEST STALE slot. Never a current one — that would trade a
reading that can confirm for another that can, gaining nothing and losing an independent opinion.
Stale still means "cannot confirm", not "cannot object": a stale reading left in place keeps
rejecting candidates at the pre-download early-out on age, gender and ethnicity, which is why
they are worth keeping right up until the moment something strictly better needs the slot.
"""
import glob
import json
import os
import sys

sys.path.insert(0, "/Users/kevinkreative/genseo/scripts")
os.chdir("/Users/kevinkreative/genseo")
import fetch_personas as fp  # noqa: E402

APPLY = "--apply" in sys.argv

# cmd_fetch does this; importing the module does not, and a silently empty cache would make every
# row here look like a first sighting and quietly drop the readings already held.
print("verdict cache: %d row(s)" % fp.verdict_cache_load())

merged, skipped, no_id, already = [], [], 0, 0

for pj in sorted(glob.glob("personas/*/persona.json") +
                 glob.glob("personas/_quarantine-*/*/persona.json")):
    doc = json.load(open(pj))
    if (doc.get("source") or {}).get("platform") != "openimages":
        continue
    # `photo_id` IS the Open Images image_id for this backend (16 hex chars), and the verdict
    # cache is keyed on exactly that.
    image_id = str((doc.get("source") or {}).get("photo_id") or "")
    if not image_id:
        no_id += 1
        continue
    fresh = doc.get("qc", {}).get("vision")
    if not isinstance(fresh, dict) or not fp.vision_is_current(fresh):
        skipped.append(os.path.dirname(pj))
        continue

    row = dict(fp._VERDICT_CACHE.get(image_id) or {})
    # Copy SLOT BY SLOT rather than rebuilding from current_readings(), which drops stale
    # readings — right for judging, wrong for copying, because dropping one from the ROW throws
    # the estimate away instead of merely declining to count it.
    fields, stale_slots = {}, []
    for vk, rk in zip(fp.VISION_KEYS, fp.RAW_KEYS):
        held = row.get(vk)
        if isinstance(held, dict):
            fields[vk] = held
            if isinstance(row.get(rk), str):
                fields[rk] = row[rk]
            if not fp.vision_is_current(held):
                stale_slots.append(vk)

    if any(row.get(vk) == fresh for vk in fp.VISION_KEYS):
        already += 1
        continue

    free = [vk for vk in fp.VISION_KEYS if vk not in fields]
    if free:
        slot, verb = free[0], "fills"
    elif stale_slots:
        # Oldest stale first: VISION_KEYS is ordered, so stale_slots is too.
        slot, verb = stale_slots[0], "displaces stale"
    else:
        already += 1
        continue

    fields[slot] = fresh
    fields[fp.RAW_KEYS[fp.VISION_KEYS.index(slot)]] = json.dumps(fresh, sort_keys=True)
    merged.append((image_id, os.path.dirname(pj), slot, verb,
                   len(fp.current_readings(fields)), fields))

print("%d image(s) gain the fresh reading" % len(merged))
for iid, where, slot, verb, n, _ in merged:
    print("   %-40s %s  %s %-7s -> %d current"
          % (os.path.relpath(where, "personas"), iid[:12], verb, slot, n))
print("\n%d already current in every slot, %d have no current reading on disk, %d no image_id"
      % (already, len(skipped), no_id))

if not APPLY:
    print("\n(dry run — pass --apply to write)")
    sys.exit(0)

for iid, _, _, _, _, fields in merged:
    fp.verdict_remember({"platform": "openimages", "id": iid}, **fields)
print("\n✓ wrote %d merged row(s) to %s" % (len(merged), fp.OPENIMAGES_VERDICTS))

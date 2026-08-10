#!/usr/bin/env python3
"""Persona rotation engine for the GenSeo image lane.

WHY THIS EXISTS. Rotation state used to live as free text inside the "Posted Date" column
of PUBLISHED_ARTICLES_TRACKER.csv, and the agent had to grep it and reason about it every
run. With 4 personas that limped along; a parse of the live tracker on 2026-08-09 pulled
`no-contact`, `bank` and `-m1-stubble` out as if they were persona handles. At 200 personas
that approach silently degrades into "reuse whatever the regex happened to match", which is
exactly the failure Kevin flagged when the /blogs/news grid read as machine-made.

So: persona.json = IMMUTABLE provenance. personas/index.json = MUTABLE rotation state,
written only here, atomically. The calling agent does not decide the persona — it asks.

    pick    choose hero persona + hero gaze + hero shot + inline gaze for ONE article
    commit  record the assignment after a SUCCESSFUL publish (never before)
    status  human-readable bank health

Runs under /usr/bin/python3 (3.9) — stdlib only, no PIL, no numpy, so it is safe from the
split-interpreter trap that bites the rest of this repo.
"""
import argparse
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# status -> selection tier. Anything NOT in here is unusable: "pending" (machine-gated by
# fetch_personas.py but never seen by Kevin) and "retired" (licence or QC failure) both.
SELECTABLE = {"active": 0, "flagged": 1}   # flagged = last resort, still warned about
INDEX = os.path.join(ROOT, "personas", "index.json")
TAXONOMY = os.path.join(ROOT, "personas", "taxonomy.json")


def _load(path, what):
    try:
        with open(path) as fh:
            return json.load(fh)
    except FileNotFoundError:
        sys.exit("✗ %s missing: %s — the bank is not initialised" % (what, path))
    except json.JSONDecodeError as exc:
        # Never guess past a corrupt state file: guessing means silently repeating a persona.
        sys.exit("✗ %s is corrupt (%s): %s — restore from git, do NOT hand-edit mid-run"
                 % (what, exc, path))


def _atomic_write(path, doc):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(doc, fh, indent=1)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def resolve_pools(tax, audience, brand):
    """audience token wins; brand is the fallback. An unmapped value is a hard error —
    silently defaulting to some pool is how a men's article gets a woman's face."""
    routing = tax["audience_routing"]
    if audience:
        if audience not in routing:
            sys.exit("✗ unknown --audience %r. Valid: %s"
                     % (audience, ", ".join(sorted(routing))))
        return audience, routing[audience]
    if brand:
        fb = tax["brand_fallback_audience"]
        if brand not in fb:
            sys.exit("✗ unknown --brand %r. Valid: %s" % (brand, ", ".join(sorted(fb))))
        tok = fb[brand]
        return tok, routing[tok]
    sys.exit("✗ pick requires --audience or --brand (see personas/taxonomy.json)")


def _spread(seq_items, handle, seq):
    """Deterministic but DE-CORRELATED choice. Taking seq_items[0] made every fresh persona
    start on to-camera-3q-left — reproducing the identical-look-direction grid this engine
    exists to prevent. crc32 (not hash(), which is PYTHONHASHSEED-salted and would differ
    between the pick run and any later audit) gives a stable per-persona offset."""
    import zlib
    return seq_items[(zlib.crc32(handle.encode()) + seq) % len(seq_items)]


def gaze_ids(tax):
    return [g["id"] for g in tax["gaze_values"]]


def gaze_family(tax, gid):
    for g in tax["gaze_values"]:
        if g["id"] == gid:
            return g["family"]
    return None


def choose_gaze(tax, entry, handle, seq, exclude=()):
    """A reused persona posed the same way is the tell. Prefer a gaze this persona has
    never had; the to-camera family may never repeat two articles running (Kevin, 2026-08-09).

    Gaze is a SOFT preference and may recycle — unlike face_angle, which is a hard rule and
    may not. Keeping them in separate functions is deliberate: the moment the two share a
    relaxation path, the hard rule inherits the soft rule's fallback and stops being hard."""
    values = [g for g in gaze_ids(tax) if g not in exclude]
    last = entry.get("last_gaze")
    if last:
        values = [g for g in values if g != last]
        if gaze_family(tax, last) == "to-camera":
            values = [g for g in values if gaze_family(tax, g) != "to-camera"]
    used = set(entry.get("gaze_used") or [])
    fresh = [g for g in values if g not in used]
    pool = fresh or values
    if not pool:  # every value excluded — relax the "never used" preference, keep the hard bans
        pool = [g for g in gaze_ids(tax) if g != last and g not in exclude] or gaze_ids(tax)
    return _spread(pool, handle, seq), bool(fresh)


def angle_ids(tax):
    return [a["id"] for a in tax["face_angle_values"]]


def angle_phrase(tax, aid):
    for a in tax["face_angle_values"]:
        if a["id"] == aid:
            return a["phrase"]
    return None


def unused_angles(tax, entry, exclude=()):
    """HARD RULE (Kevin, 2026-08-10): never the same face angle twice for one model.

    No fallback, by construction. Every other preference in this file degrades gracefully when
    it runs out of room — gaze recycles, shots relax their window — because those are tells,
    and a repeated tell is a cosmetic loss. This one does not degrade, because the rule Kevin
    stated has no 'unless the bank is thin' clause in it. A persona with no unused angle left
    is simply not a candidate; see the filter in cmd_pick, which drops it before it can be
    chosen rather than choosing it and then improvising."""
    used = set(entry.get("angles_used") or [])
    return [a for a in angle_ids(tax) if a not in used and a not in exclude]


def choose_angle(tax, entry, handle, seq, exclude=()):
    pool = unused_angles(tax, entry, exclude)
    if not pool:
        return None
    return _spread(pool, handle, seq)


def choose_shot(tax, index, handle, seq):
    recent = list(index.get("recent_shots") or [])[-3:]
    fresh = [s for s in tax["shot_values"] if s not in recent]
    if not fresh:  # 6 values vs a 3-deep window can't actually empty; belt and braces
        fresh = tax["shot_values"]
    return _spread(fresh, handle, seq)


def cmd_pick(args):
    tax, index = _load(TAXONOMY, "taxonomy"), _load(INDEX, "index")
    token, pools = resolve_pools(tax, args.audience, args.brand)
    seq = index.get("seq", 0) + 1
    out = {"seq": seq, "audience": token, "pools": pools, "warnings": []}

    cyc = index.get("no_face_cycle") or {"period": 3, "position": 0}
    pos = (cyc.get("position", 0) + 1) % max(1, cyc.get("period", 3))
    if not args.force_face and cyc.get("period") and pos == 0:
        out.update(hero="NO-FACE", hero_ref=None, hero_gaze=None, hero_face_angle=None,
                   hero_shot=choose_shot(tax, index, "no-face", seq), inline_gaze=None,
                   inline_face_angle=None,
                   note=("no-face hero this cycle: a face + a pack on every single row is the "
                         "structural tell that rotating the pose cannot reach. Compose "
                         "product-in-a-real-scene or scene-only; still --product-ref + --qc, "
                         "still no --ugc. Do NOT substitute a face by hand."))
        print(json.dumps(out, indent=1))
        return

    cands, pending, exhausted = [], 0, []
    for h, e in (index.get("personas") or {}).items():
        if e.get("pool_id") not in pools:
            continue
        # ALLOW-list, deliberately. Skipping only "retired" meant every status a future writer
        # invents is selectable by default — and fetch_personas.py is exactly such a writer.
        # This engine never opens persona.json, so `approved_by` there has no reader: the
        # status in THIS file is what stands between a machine-gated face and a live og:image.
        tier = SELECTABLE.get(e.get("status"))
        if tier is None:
            if e.get("status") == "pending":
                pending += 1
            continue
        if not os.path.exists(e.get("ref") or ""):
            out["warnings"].append("%s: ref.jpg missing on disk, skipped" % h)
            continue
        # An article can consume TWO angles from one persona (hero + the inline persona-in-scene),
        # so a persona with one angle left is not a candidate. Excluding here rather than at
        # assignment time is the whole point: pick one with too few angles and the only ways out
        # are to reuse an angle (breaks Kevin's rule) or to hand back a persona the caller cannot
        # actually use (breaks the caller). Neither is a decision this engine gets to make.
        left = len(unused_angles(tax, e))
        if left < 2:
            exhausted.append((h, left))
            continue
        cands.append((tier,
                      pools.index(e["pool_id"]),                  # preferred pool first
                      e.get("last_used_seq", 0),                  # LRU
                      h, e))
    if pending:
        out["warnings"].append(
            "%d face(s) in these pools are PENDING approval and cannot be used yet" % pending)
    if exhausted:
        out["warnings"].append(
            "%d persona(s) have spent all %d face angles and are done as heroes: %s"
            % (len(exhausted), len(angle_ids(tax)),
               ", ".join("%s (%d left)" % (h, n) for h, n in exhausted)))
    if not cands:
        sys.exit("✗ no usable persona for audience %r (pools %s)%s. Bank needs expansion — "
                 "do NOT invent a face; use a no-face hero and report it."
                 % (token, pools,
                    "; %d await approval" % pending if pending else ""))
    cands.sort()
    tier, _, last_seq, handle, entry = cands[0]
    if tier == 1:
        out["warnings"].append(
            "using FLAGGED persona %s (%s) — no clean face exists in pools %s"
            % (handle, (entry.get("flag_reason") or "see persona.json"), pools))
    gap = seq - (last_seq or 0)
    if gap <= 2:
        out["warnings"].append(
            "%s was hero %d article(s) ago — pool %s is too thin to space heroes properly"
            % (handle, gap, entry.get("pool_id")))

    hero_gaze, fresh = choose_gaze(tax, entry, handle, seq)
    if not fresh:
        out["warnings"].append("%s has now used every gaze value; recycling" % handle)
    # Exclude the whole FAMILY, not just the id, when the hero looks at camera. Excluding the
    # bare id let hero=just-past-lens pair with inline=at-lens: the same person, twice in one
    # article, both meeting the reader's eye, differing by a few degrees no reader perceives.
    # That is the tell Kevin named on 2026-08-09 ("image show them look in the same direction"),
    # and it survived the fix because the code was comparing tokens where he was comparing looks.
    drop = tuple(g for g in gaze_ids(tax)
                 if g == hero_gaze or (gaze_family(tax, hero_gaze) == "to-camera"
                                       and gaze_family(tax, g) == "to-camera"))
    inline_gaze, _ = choose_gaze(tax, entry, handle, seq + 1, exclude=drop)

    hero_angle = choose_angle(tax, entry, handle, seq)
    inline_angle = choose_angle(tax, entry, handle, seq + 1, exclude=(hero_angle,))
    if not hero_angle or not inline_angle:   # the <2 filter above should make this unreachable
        sys.exit("✗ %s cannot supply two unused face angles — the candidate filter let an "
                 "exhausted persona through. This is a bug; fix it rather than reusing an angle."
                 % handle)
    left = len(unused_angles(tax, entry)) - 2
    if left <= 3:
        out["warnings"].append(
            "%s has %d unused face angle(s) left after this article, then it is spent forever"
            % (handle, left))

    out.update(hero=handle, hero_ref=entry["ref"], hero_gaze=hero_gaze,
               hero_face_angle=hero_angle, hero_face_angle_phrase=angle_phrase(tax, hero_angle),
               hero_shot=choose_shot(tax, index, handle, seq), inline_gaze=inline_gaze,
               inline_face_angle=inline_angle,
               inline_face_angle_phrase=angle_phrase(tax, inline_angle),
               hero_used_count=entry.get("used_count", 0),
               angles_left_after=left,
               note=("hero = %s. Feed THIS ref.jpg, never a previous gen. Pass --face-angle %s "
                     "to article_images.py for the hero and --face-angle %s for the inline "
                     "persona-in-scene; the wrapper rejects an angle this persona has already "
                     "spent, so do not substitute your own. Put the angle phrase in the prompt "
                     "verbatim, and say the gaze in plain words alongside it — they are separate "
                     "axes: the angle is where the HEAD points, the gaze is where the EYES point "
                     "within it." % (handle, hero_angle, inline_angle)))
    print(json.dumps(out, indent=1))


def cmd_commit(args):
    index = _load(INDEX, "index")
    if args.expect_seq is not None and args.expect_seq != index.get("seq", 0) + 1:
        sys.exit("✗ seq race: expected %d, state is at %d — another run committed first. "
                 "Re-run pick." % (args.expect_seq, index.get("seq", 0) + 1))
    index["seq"] = index.get("seq", 0) + 1
    cyc = index.setdefault("no_face_cycle", {"period": 3, "position": 0})
    cyc["position"] = (cyc.get("position", 0) + 1) % max(1, cyc.get("period", 3))

    if args.shot:
        index["recent_shots"] = (list(index.get("recent_shots") or []) + [args.shot])[-6:]
    if args.hero and args.hero != "NO-FACE":
        e = (index.get("personas") or {}).get(args.hero)
        if not e:
            sys.exit("✗ unknown persona %r — commit refused" % args.hero)
        tax = _load(TAXONOMY, "taxonomy")
        vocab, spent = set(angle_ids(tax)), set(e.get("angles_used") or [])
        angles = [a for a in (args.face_angle, args.inline_face_angle) if a]
        if not angles:
            sys.exit("✗ commit of a face hero requires --face-angle. The angle history IS the "
                     "hard rule; an unrecorded angle is an angle that will be handed out again.")
        for a in angles:
            if a not in vocab:
                sys.exit("✗ %r is not a face angle in taxonomy.json — commit refused" % a)
            # Refuse rather than dedupe. `if a not in used: append` — the shape used for gaze
            # right below — would make a repeat commit a silent no-op, so the one event that
            # proves the rule was broken would leave no trace anywhere.
            if a in spent:
                sys.exit("✗ %s has already used face angle %r. Kevin's hard rule is one angle "
                         "per model, once, ever — this article must be regenerated with an "
                         "angle from `persona_picker.py pick`, not committed." % (args.hero, a))
        if len(set(angles)) != len(angles):
            sys.exit("✗ hero and inline were given the SAME face angle (%s) — that is the rule "
                     "broken inside a single article" % angles[0])
        e.setdefault("angles_used", []).extend(angles)
        e["used_count"] = e.get("used_count", 0) + 1
        e["last_used_seq"] = index["seq"]
        for g in (args.gaze, args.inline_gaze):
            if g and g not in (e.get("gaze_used") or []):
                e.setdefault("gaze_used", []).append(g)
        if args.gaze:
            e["last_gaze"] = args.gaze
    index["recent_heroes"] = (list(index.get("recent_heroes") or []) + [args.hero or "NO-FACE"])[-8:]
    _atomic_write(INDEX, index)
    print("✓ committed seq=%d hero=%s angle=%s inline-angle=%s gaze=%s shot=%s"
          % (index["seq"], args.hero, args.face_angle, args.inline_face_angle,
             args.gaze, args.shot))


def cmd_status(_args):
    tax, index = _load(TAXONOMY, "taxonomy"), _load(INDEX, "index")
    ppl = index.get("personas") or {}
    print("bank: %d personas / %d target   seq=%d"
          % (len(ppl), tax["total_slots"], index.get("seq", 0)))
    print("no-face cycle: every %s heroes, position %s"
          % (index.get("no_face_cycle", {}).get("period"),
             index.get("no_face_cycle", {}).get("position")))
    per = len(angle_ids(tax))
    usable = [e for e in ppl.values() if e.get("status") in SELECTABLE]
    spent = sum(len(e.get("angles_used") or []) for e in usable)
    print("face angles: %d spent / %d available (%d personas x %d angles); %d persona(s) spent out"
          % (spent, len(usable) * per, len(usable), per,
             len([e for e in usable if len(unused_angles(tax, e)) < 2])))
    print("recent shots: %s" % ", ".join(index.get("recent_shots") or []) or "-")
    print()
    print("%-8s %6s %6s  %s" % ("POOL", "HAVE", "TARGET", "STATUS"))
    for p in tax["rotation_pools"]:
        have = [h for h, e in ppl.items() if e.get("pool_id") == p["pool_id"]]
        clean = [h for h in have if ppl[h].get("status") == "active"]
        mark = "OK" if len(clean) >= 3 else ("THIN" if clean else "EMPTY — no usable face")
        # Only "active" and "flagged" can be picked. Folding the unusable states into one
        # "(n flagged)" note read as "there is a fallback here" when there isn't. Name each.
        counts = [(s, len([h for h in have if ppl[h].get("status") == s]))
                  for s in ("flagged", "pending", "retired")]
        extra = ", ".join("%d %s" % (n, s) for s, n in counts if n)
        print("%-8s %6d %6d  %s%s" % (p["pool_id"], len(have), p["target_count"], mark,
                                      " (%s)" % extra if extra else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("pick", help="choose persona+gaze+shot for one article")
    p.add_argument("--audience", help="token from taxonomy.json audience_routing")
    p.add_argument("--brand", help="fallback when the ticket names no audience")
    p.add_argument("--force-face", action="store_true",
                   help="override the scheduled no-face hero (use sparingly)")
    p.set_defaults(fn=cmd_pick)

    c = sub.add_parser("commit", help="record the assignment AFTER a successful publish")
    c.add_argument("--hero", required=True, help="persona handle, or NO-FACE")
    c.add_argument("--gaze")
    c.add_argument("--inline-gaze")
    c.add_argument("--face-angle", help="hero face angle from pick — required for a face hero")
    c.add_argument("--inline-face-angle", help="face angle of the inline persona-in-scene, if any")
    c.add_argument("--shot")
    c.add_argument("--expect-seq", type=int, help="seq from pick; guards against overlapping runs")
    c.set_defaults(fn=cmd_commit)

    s = sub.add_parser("status", help="bank health per rotation pool")
    s.set_defaults(fn=cmd_status)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

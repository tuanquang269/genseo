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


def choose_gaze(tax, entry, handle, seq, exclude=()):
    """A reused persona posed the same way is the tell. Prefer a gaze this persona has
    never had; `to-camera-*` may never repeat two articles running (Kevin, 2026-08-09)."""
    values = [g for g in tax["gaze_values"] if g not in exclude]
    last = entry.get("last_gaze")
    if last:
        values = [g for g in values if g != last]
        if last.startswith("to-camera"):
            values = [g for g in values if not g.startswith("to-camera")]
    used = set(entry.get("gaze_used") or [])
    fresh = [g for g in values if g not in used]
    pool = fresh or values
    if not pool:  # every value excluded — relax the "never used" preference, keep the hard bans
        pool = [g for g in tax["gaze_values"] if g != last and g not in exclude] or tax["gaze_values"]
    return _spread(pool, handle, seq), bool(fresh)


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
        out.update(hero="NO-FACE", hero_ref=None, hero_gaze=None,
                   hero_shot=choose_shot(tax, index, "no-face", seq), inline_gaze=None,
                   note=("no-face hero this cycle: a face + a pack on every single row is the "
                         "structural tell gaze rotation cannot reach. Compose product-in-a-real-"
                         "scene or scene-only; still --product-ref + --qc, still no --ugc."))
        print(json.dumps(out, indent=1))
        return

    cands = []
    for h, e in (index.get("personas") or {}).items():
        if e.get("pool_id") not in pools or e.get("status") == "retired":
            continue
        if not os.path.exists(e.get("ref") or ""):
            out["warnings"].append("%s: ref.jpg missing on disk, skipped" % h)
            continue
        cands.append((0 if e.get("status") == "active" else 1,   # flagged = last resort
                      pools.index(e["pool_id"]),                  # preferred pool first
                      e.get("last_used_seq", 0),                  # LRU
                      h, e))
    if not cands:
        sys.exit("✗ no usable persona for audience %r (pools %s). Bank needs expansion — "
                 "do NOT invent a face; use a no-face hero and report it." % (token, pools))
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
    inline_gaze, _ = choose_gaze(tax, entry, handle, seq + 1, exclude=(hero_gaze,))
    out.update(hero=handle, hero_ref=entry["ref"], hero_gaze=hero_gaze,
               hero_shot=choose_shot(tax, index, handle, seq), inline_gaze=inline_gaze,
               hero_used_count=entry.get("used_count", 0),
               note=("hero = %s. Feed THIS ref.jpg, never a previous gen. Say the gaze in plain "
                     "words in the prompt. Inline persona-in-scene reuses the SAME face (one "
                     "person's story) but MUST use inline_gaze, not hero_gaze." % handle))
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
        e["used_count"] = e.get("used_count", 0) + 1
        e["last_used_seq"] = index["seq"]
        for g in (args.gaze, args.inline_gaze):
            if g and g not in (e.get("gaze_used") or []):
                e.setdefault("gaze_used", []).append(g)
        if args.gaze:
            e["last_gaze"] = args.gaze
    index["recent_heroes"] = (list(index.get("recent_heroes") or []) + [args.hero or "NO-FACE"])[-8:]
    _atomic_write(INDEX, index)
    print("✓ committed seq=%d hero=%s gaze=%s shot=%s"
          % (index["seq"], args.hero, args.gaze, args.shot))


def cmd_status(_args):
    tax, index = _load(TAXONOMY, "taxonomy"), _load(INDEX, "index")
    ppl = index.get("personas") or {}
    print("bank: %d personas / %d target   seq=%d"
          % (len(ppl), tax["total_slots"], index.get("seq", 0)))
    print("no-face cycle: every %s heroes, position %s"
          % (index.get("no_face_cycle", {}).get("period"),
             index.get("no_face_cycle", {}).get("position")))
    print("recent shots: %s" % ", ".join(index.get("recent_shots") or []) or "-")
    print()
    print("%-8s %6s %6s  %s" % ("POOL", "HAVE", "TARGET", "STATUS"))
    for p in tax["rotation_pools"]:
        have = [h for h, e in ppl.items() if e.get("pool_id") == p["pool_id"]]
        clean = [h for h in have if ppl[h].get("status") == "active"]
        flagged = [h for h in have if ppl[h].get("status") == "flagged"]
        retired = [h for h in have if ppl[h].get("status") == "retired"]
        mark = "OK" if len(clean) >= 3 else ("THIN" if clean else "EMPTY — no usable face")
        # Retired faces are NOT selectable, so folding them into a "(n flagged)" note read as
        # "there is a fallback here" when there isn't one. Name the two states separately.
        extra = ", ".join(x for x in ("%d flagged" % len(flagged) if flagged else "",
                                      "%d retired" % len(retired) if retired else "") if x)
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
    c.add_argument("--shot")
    c.add_argument("--expect-seq", type=int, help="seq from pick; guards against overlapping runs")
    c.set_defaults(fn=cmd_commit)

    s = sub.add_parser("status", help="bank health per rotation pool")
    s.set_defaults(fn=cmd_status)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

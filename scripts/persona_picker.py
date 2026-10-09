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

    pick     choose hero persona + hero gaze + hero shot + inline gaze for ONE article,
             and RESERVE what it issues (see below)
    commit   close the reservation after a SUCCESSFUL publish (never before)
    release  hand a reservation back, for a run that never published
    status   human-readable bank health

PICK RESERVES; COMMIT ONLY CONFIRMS. pick used to be a pure read: it printed an assignment and
wrote nothing, and the spend was recorded by commit — which the agent runs BY HAND, only after a
live publish. Anything at all between those two points (a publisher crash, a QC re-roll hitting
its cap, a token expiry, the agent simply not issuing the last command) left the angles unspent,
and because selection is deterministic the very next pick returned a byte-identical assignment:
the same face at the same head angle on two live og:images, with nothing anywhere recording that
it happened. So pick now spends optimistically and commit converts reserved -> used.

The failure directions are not symmetrical, which is what decides it. A reservation abandoned by
a dead run burns two angles out of 21 per persona and 4,200 across a full bank — nothing. An
angle re-issued breaks the one rule Kevin wrote in capitals. `release` exists for the run that
knows it failed; silence costs almost nothing.

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
# Faces admitted before the vision rubric asked about expression. m3039-as-02's own QC
# notes read "Man making a silly face" / "exaggerated facial expression". Keep this
# identical to fetch_personas.IDENTITY_BLOCKLIST. The handle is refused even when the
# row's booleans have been cleared.
IDENTITY_BLOCKLIST = frozenset({"m3039-as-02"})
INDEX = os.path.join(ROOT, "personas", "index.json")
TAXONOMY = os.path.join(ROOT, "personas", "taxonomy.json")


def identity_refusal(entry, handle=None):
    """Why this row must not be a hero / identity anchor, or None if it may.

    Missing booleans default to usable. The bank predates the fields, and a missing
    key is not evidence of a gurn. An explicit exaggerated_expression true, an explicit
    usable_as_identity_reference false, or IDENTITY_BLOCKLIST, refuses. NO-FACE is not
    a persona and is not passed here.
    """
    entry = entry or {}
    handle = handle or entry.get("handle") or ""
    if handle in IDENTITY_BLOCKLIST:
        return "blocklisted: QC notes a silly/exaggerated face, not an identity anchor"
    if entry.get("exaggerated_expression") is True:
        return "exaggerated_expression is true"
    if entry.get("usable_as_identity_reference") is False:
        return "usable_as_identity_reference is false"
    return None


def _refuse_identity_hero(hero, entry):
    """Commit must not record a face the picker is not allowed to issue."""
    if not hero or hero == "NO-FACE":
        return
    why = identity_refusal(entry, hero)
    if why:
        sys.exit("✗ %s cannot be a hero / identity reference (%s). "
                 "Release the reservation if this article never published; "
                 "do not commit this face." % (hero, why))


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
    """Only the angles the generator can actually deliver AND the judge can actually verify.

    Every persona prompt carries an identity-match clause, and QC check 4 asks whether the
    candidate reads as the same person as the reference photograph. A `half-back-*` angle hides
    the face by definition, so it contradicts both: on run 20260813-0847 ima2 resolved the
    conflict toward profile on 3 of 3 rolls and burned the whole re-roll budget, and even a
    perfect render would leave the judge grading a face it cannot see. The angles stay in the
    vocabulary — `angle_phrase` still resolves them, so an angle already spent keeps printing —
    they are simply never ISSUED again. Flag lives in taxonomy.json, not here, so the two
    readers (this picker and article_images.py) cannot drift apart.

    Capacity after the cut: 15 angles x 42 selectable personas = 630, at 2 per article."""
    return [a["id"] for a in tax["face_angle_values"] if a.get("renderable", True)]


def angle_phrase(tax, aid):
    """Phrase + frame_hint, the same string article_images.py builds.

    The hint is not decoration. "Turned about 35 degrees to their left" is subject-relative, and
    on 2026-08-13 both ima2 and the QC judge read it viewer-relative and mirrored the render —
    the judge could not catch it because it made the identical flip. The hint restates the angle
    as which frame edge the nose points at and which ear is nearest the lens, which neither side
    has to invert. It is emitted here so the prompt the agent writes and the rubric the judge
    reads are quoting one definition."""
    for a in tax["face_angle_values"]:
        if a["id"] == aid:
            return " — ".join(x for x in (a["phrase"], a.get("frame_hint")) if x)
    return None


def unused_angles(tax, entry, exclude=()):
    """HARD RULE (Kevin, 2026-08-10): never the same face angle twice for one model.

    No fallback, by construction. Every other preference in this file degrades gracefully when
    it runs out of room — gaze recycles, shots relax their window — because those are tells,
    and a repeated tell is a cosmetic loss. This one does not degrade, because the rule Kevin
    stated has no 'unless the bank is thin' clause in it. A persona with no unused angle left
    is simply not a candidate; see the filter in cmd_pick, which drops it before it can be
    chosen rather than choosing it and then improvising.

    RESERVED counts as gone. An angle handed to a caller that has not yet published is not
    available to the next caller — that is the whole of finding #3, and it is why the two lists
    are separate rather than one. They cannot be merged: article_images.py refuses any angle
    found in `angles_used`, so writing a just-issued angle there would make the wrapper reject
    the angle it was handed thirty seconds earlier."""
    used = set(entry.get("angles_used") or []) | set(entry.get("angles_reserved") or [])
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


def _reserve(index, out, pos, cycle_before):
    """Spend, atomically, everything this pick just issued — then let the caller print it.

    Order matters and is the opposite of the obvious one: write first, print second. Printing
    first and writing after would reintroduce the same gap in miniature, and a caller that read
    the JSON off stdout and then saw a non-zero exit would have no way to know whether the state
    moved. Write-then-print means the JSON on stdout is, by construction, a description of what
    is already on disk."""
    seq = out["seq"]
    index["seq"] = seq
    cyc = index.setdefault("no_face_cycle", {"period": 3, "position": 0})
    cyc["position"] = pos
    if out.get("hero_shot"):
        index["recent_shots"] = (list(index.get("recent_shots") or []) + [out["hero_shot"]])[-6:]
    index["recent_heroes"] = (list(index.get("recent_heroes") or [])
                              + [out.get("hero") or "NO-FACE"])[-8:]

    hero = out.get("hero")
    angles = [a for a in (out.get("hero_face_angle"), out.get("inline_face_angle")) if a]
    if hero and hero != "NO-FACE":
        e = index["personas"][hero]
        e["angles_reserved"] = list(e.get("angles_reserved") or []) + angles
        e["last_used_seq"] = seq
        for g in (out.get("hero_gaze"), out.get("inline_gaze")):
            if g and g not in (e.get("gaze_used") or []):
                e.setdefault("gaze_used", []).append(g)
        if out.get("hero_gaze"):
            e["last_gaze"] = out["hero_gaze"]

    index.setdefault("reservations", {})[str(seq)] = {
        "seq": seq, "hero": hero or "NO-FACE", "audience": out.get("audience"),
        "hero_face_angle": out.get("hero_face_angle"),
        "inline_face_angle": out.get("inline_face_angle"),
        "hero_gaze": out.get("hero_gaze"), "inline_gaze": out.get("inline_gaze"),
        "shot": out.get("hero_shot"), "cycle_position_before": cycle_before}
    _atomic_write(INDEX, index)
    out["reserved"] = True
    out["release_if_unpublished"] = (
        "persona_picker.py release --seq %d   # ONLY if this article never went live" % seq)
    return out


def cmd_pick(args):
    tax, index = _load(TAXONOMY, "taxonomy"), _load(INDEX, "index")
    token, pools = resolve_pools(tax, args.audience, args.brand)
    seq = index.get("seq", 0) + 1
    out = {"seq": seq, "audience": token, "pools": pools, "warnings": []}

    cyc = index.get("no_face_cycle") or {"period": 3, "position": 0}
    cycle_before = cyc.get("position", 0)
    pos = (cycle_before + 1) % max(1, cyc.get("period", 3))
    if not args.force_face and cyc.get("period") and pos == 0:
        out.update(hero="NO-FACE", hero_ref=None, hero_gaze=None, hero_face_angle=None,
                   hero_shot=choose_shot(tax, index, "no-face", seq), inline_gaze=None,
                   inline_face_angle=None,
                   note=("no-face hero this cycle: a face + a pack on every single row is the "
                         "structural tell that rotating the pose cannot reach. Compose "
                         "product-in-a-real-scene or scene-only; still --product-ref + --qc, "
                         "still no --ugc. Do NOT substitute a face by hand."))
        # A no-face pick reserves too, even though it spends no angle. The cycle position is
        # the thing being spent here: it used to advance only in commit, so two picks without a
        # commit between them both landed on the same position — the faceless hero either
        # repeating or, far more often, never arriving. One in three heroes carrying no face is
        # the only lever that reaches the structural tell, so its bookkeeping is not optional.
        _reserve(index, out, pos, cycle_before)
        print(json.dumps(out, indent=1))
        return out

    cands, pending, exhausted, skipped_identity = [], 0, [], []
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
        why = identity_refusal(e, h)
        if why:
            # A gurn that reached status=active is still not a hero. Skipping here, not at
            # commit, is what keeps the og:image from being issued in the first place.
            skipped_identity.append(h)
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
    if skipped_identity:
        out["warnings"].append(
            "%d persona(s) skipped as hero/identity (exaggerated expression, "
            "usable_as_identity_reference false, or blocklist): %s"
            % (len(skipped_identity), ", ".join(sorted(skipped_identity))))
    if pending:
        out["warnings"].append(
            "%d face(s) in these pools are PENDING approval and cannot be used yet" % pending)
    if exhausted:
        out["warnings"].append(
            "%d persona(s) have spent all %d face angles and are done as heroes: %s"
            % (len(exhausted), len(angle_ids(tax)),
               ", ".join("%s (%d left)" % (h, n) for h, n in exhausted)))
    if not cands:
        # DEGRADE to no-face, do not abort. This branch used to sys.exit(1) while its own message
        # told the caller to "use a no-face hero" — an instruction the caller could not follow,
        # because it received a non-zero exit and no JSON. Harmless while the bank had faces;
        # the moment all four personas were retired (2026-08-10) it became every pick, and the
        # headless runner would have read the whole image lane as a hard failure.
        # An empty bank is a known, expected, already-handled state — the no_face_cycle branch
        # above emits exactly this shape — so it belongs on the degrade path, not the error path.
        # The two genuinely unusable inputs (bad audience token, unreadable state file) still
        # exit non-zero; being short of faces is not one of them.
        out["warnings"].append(
            "no usable persona for audience %r (pools %s)%s%s — falling back to a NO-FACE hero. "
            "Bank needs expansion; do NOT invent a face and do NOT reuse a spent angle."
            % (token, pools,
               "; %d await approval" % pending if pending else "",
               "; %d angle-exhausted" % len(exhausted) if exhausted else ""))
        out.update(hero="NO-FACE", hero_ref=None, hero_gaze=None, hero_face_angle=None,
                   hero_shot=choose_shot(tax, index, "no-face", seq), inline_gaze=None,
                   inline_face_angle=None,
                   note=("NO-FACE hero because the bank could not supply one, not because the "
                         "cycle called for it. Compose product-in-a-real-scene or scene-only; "
                         "still --product-ref + --qc, still no --ugc. Report the shortfall."))
        _reserve(index, out, pos, cycle_before)
        print(json.dumps(out, indent=1))
        return out
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
                     "within it. Both angles are RESERVED as of now: no later pick can be handed "
                     "them, whether or not this article ever ships." % (handle, hero_angle,
                                                                       inline_angle)))
    _reserve(index, out, pos, cycle_before)
    print(json.dumps(out, indent=1))
    return out


def cmd_commit(args):
    index = _load(INDEX, "index")
    resv = index.get("reservations") or {}
    if resv:
        return _close_reservation(index, resv, args)
    return _legacy_commit(index, args)


def _close_reservation(index, resv, args):
    """Convert a reservation into history. pick already moved the counters; this only records
    that the article went LIVE, and checks that what shipped is what was issued."""
    if args.expect_seq is None:
        sys.exit("✗ commit needs --expect-seq now that pick reserves. Outstanding reservation(s): "
                 "%s. Pass the seq that pick printed for THIS article."
                 % ", ".join(sorted(resv, key=int)))
    r = resv.get(str(args.expect_seq))
    if r is None:
        sys.exit("✗ no outstanding reservation for seq %d — either it was already committed "
                 "(a double commit) or this call was written by hand. Outstanding: %s. Never "
                 "hand-edit index.json; re-run pick if you need a fresh assignment."
                 % (args.expect_seq, ", ".join(sorted(resv, key=int)) or "none"))

    hero = args.hero or "NO-FACE"
    if hero != r["hero"]:
        sys.exit("✗ seq %d was issued hero %r, commit reports %r. The reservation is the record "
                 "of what this article was allowed to use; publishing something else means the "
                 "issued angles are burned and the shipped one is unrecorded. Fix the article, "
                 "or `release --seq %d` if it never published."
                 % (r["seq"], r["hero"], hero, r["seq"]))

    if hero != "NO-FACE":
        e = (index.get("personas") or {}).get(hero)
        _refuse_identity_hero(hero, e)
        if not e:
            sys.exit("✗ unknown persona %r — commit refused" % hero)
        issued = [a for a in (r.get("hero_face_angle"), r.get("inline_face_angle")) if a]
        given = [a for a in (args.face_angle, args.inline_face_angle) if a]
        if not given:
            sys.exit("✗ commit of a face hero requires --face-angle. The angle history IS the "
                     "hard rule; an unrecorded angle is an angle that will be handed out again.")
        if sorted(given) != sorted(issued):
            # Worth checking precisely because nothing else can. article_images.py refuses a
            # SPENT angle, so it catches a repeat; it cannot catch a fresh angle the agent chose
            # for itself, and that angle would ship live with no ledger entry at all.
            sys.exit("✗ seq %d issued face angles %s but commit reports %s. Regenerate the images "
                     "with the issued angles, or `release --seq %d` and start over — do not "
                     "commit an angle the picker never handed out."
                     % (r["seq"], issued, given, r["seq"]))
        spent = set(e.get("angles_used") or [])
        for a in issued:
            # Refuse rather than dedupe. `if a not in used: append` would make a repeat a silent
            # no-op, so the one event that proves the rule was broken would leave no trace.
            if a in spent:
                sys.exit("✗ %s has already used face angle %r. Kevin's hard rule is one angle "
                         "per model, once, ever." % (hero, a))
        e["angles_used"] = list(e.get("angles_used") or []) + issued
        e["angles_reserved"] = [a for a in (e.get("angles_reserved") or []) if a not in issued]
        e["used_count"] = e.get("used_count", 0) + 1

    index["reservations"].pop(str(r["seq"]), None)
    _atomic_write(INDEX, index)
    print("✓ committed seq=%d hero=%s angle=%s inline-angle=%s gaze=%s shot=%s"
          % (r["seq"], hero, r.get("hero_face_angle"), r.get("inline_face_angle"),
             r.get("hero_gaze"), r.get("shot")))


def _legacy_commit(index, args):
    """The pre-reservation path, kept verbatim for a state file with no reservations — either
    written before this change or belonging to a run that picked under the old code. Delete it
    once no such run can be in flight."""
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
        _refuse_identity_hero(args.hero, e)
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


def cmd_release(args):
    """Hand back a reservation for an article that never published.

    The caller ASSERTS the article is not live. Nothing here can check that, which is why the
    rollback is deliberately narrow: reserved angles come off, `angles_used` is never touched.
    A released angle can be issued again; a used one never can, and release must not be able to
    turn the second into the first."""
    index = _load(INDEX, "index")
    resv = index.get("reservations") or {}
    r = resv.get(str(args.seq))
    if r is None:
        sys.exit("✗ no outstanding reservation for seq %d. Outstanding: %s"
                 % (args.seq, ", ".join(sorted(resv, key=int)) or "none"))
    hero, freed = r.get("hero"), []
    if hero and hero != "NO-FACE":
        e = (index.get("personas") or {}).get(hero) or {}
        issued = {a for a in (r.get("hero_face_angle"), r.get("inline_face_angle")) if a}
        freed = [a for a in (e.get("angles_reserved") or []) if a in issued]
        e["angles_reserved"] = [a for a in (e.get("angles_reserved") or []) if a not in issued]

    # Roll the cycle back only when this is the newest reservation — with a later pick on top,
    # the position no longer describes this article and moving it would corrupt that one instead.
    # Everything else (seq, recent_heroes) stays: seq is a counter, not a census.
    if index.get("seq") == r["seq"] and r.get("cycle_position_before") is not None:
        index.setdefault("no_face_cycle", {})["position"] = r["cycle_position_before"]
        for key, val in (("recent_shots", r.get("shot")), ("recent_heroes", hero)):
            lst = list(index.get(key) or [])
            if val and lst and lst[-1] == val:
                index[key] = lst[:-1]

    index["reservations"].pop(str(args.seq), None)
    _atomic_write(INDEX, index)
    print("✓ released seq=%d hero=%s; %d angle(s) returned to the pool: %s"
          % (args.seq, hero, len(freed), ", ".join(freed) or "-"))


def cmd_status(_args):
    tax, index = _load(TAXONOMY, "taxonomy"), _load(INDEX, "index")
    ppl = index.get("personas") or {}
    print("bank: %d personas / %d target   seq=%d"
          % (len(ppl), tax["total_slots"], index.get("seq", 0)))
    print("no-face cycle: every %s heroes, position %s"
          % (index.get("no_face_cycle", {}).get("period"),
             index.get("no_face_cycle", {}).get("position")))
    per = len(angle_ids(tax))
    usable = [e for h, e in ppl.items()
              if e.get("status") in SELECTABLE and not identity_refusal(e, h)]
    blocked = sorted(h for h, e in ppl.items() if identity_refusal(e, h))
    if blocked:
        print("identity-blocked (not a hero): %s" % ", ".join(blocked))
    spent = sum(len(e.get("angles_used") or []) for e in usable)
    held = sum(len(e.get("angles_reserved") or []) for e in usable)
    print("face angles: %d spent + %d reserved / %d available (%d personas x %d angles); "
          "%d persona(s) spent out"
          % (spent, held, len(usable) * per, len(usable), per,
             len([e for e in usable if len(unused_angles(tax, e)) < 2])))
    print("recent shots: %s" % ", ".join(index.get("recent_shots") or []) or "-")
    # Surface these loudly: an angle burned by a run that died is invisible everywhere else, and
    # the whole point of the reservation is that it costs something real.
    for key in sorted(index.get("reservations") or {}, key=int):
        r = index["reservations"][key]
        print("  ⏳ reservation seq=%s hero=%s angles=%s — commit it after the article goes live, "
              "or `release --seq %s`"
              % (key, r.get("hero"),
                 "+".join(a for a in (r.get("hero_face_angle"), r.get("inline_face_angle")) if a)
                 or "-", key))
    print()
    print("%-8s %6s %6s  %s" % ("POOL", "HAVE", "TARGET", "STATUS"))
    for p in tax["rotation_pools"]:
        have = [h for h, e in ppl.items() if e.get("pool_id") == p["pool_id"]]
        clean = [h for h in have
                 if ppl[h].get("status") == "active" and not identity_refusal(ppl[h], h)]
        mark = "OK" if len(clean) >= 3 else ("THIN" if clean else "EMPTY — no usable face")
        # Only "active" and "flagged" can be picked. Folding the unusable states into one
        # "(n flagged)" note read as "there is a fallback here" when there isn't. Name each.
        counts = [(s, len([h for h in have if ppl[h].get("status") == s]))
                  for s in ("flagged", "pending", "retired")]
        bits = ["%d %s" % (n, s) for s, n in counts if n]
        n_id = len([h for h in have if identity_refusal(ppl[h], h)])
        if n_id:
            bits.append("%d identity-blocked" % n_id)
        extra = ", ".join(bits)
        print("%-8s %6d %6d  %s%s" % (p["pool_id"], len(have), p["target_count"], mark,
                                      " (%s)" % extra if extra else ""))


def cmd_selftest(_args):
    """Drive the reservation lifecycle against a sandbox copy of the state file.

    The defect this exists to pin down was invisible inside any single function: pick was
    correct, commit was correct, and the loss happened in the gap between them. So the test
    drives the COMMANDS in sequence, on a state file of its own, and asserts on what lands on
    disk — not on return values, which is the layer that was already telling the truth."""
    global INDEX
    import contextlib
    import io
    import shutil

    failures = []

    def check(label, ok, detail=""):
        print("%s %s%s" % ("✓" if ok else "✗", label, ("  " + detail) if detail else ""))
        if not ok:
            failures.append(label)

    tax = _load(TAXONOMY, "taxonomy")
    aud = sorted(tax["audience_routing"])[0]
    pool = tax["audience_routing"][aud][0]
    sandbox = tempfile.mkdtemp(prefix="picker-selftest-")
    real_index = INDEX
    try:
        ref = os.path.join(sandbox, "ref.jpg")
        with open(ref, "wb") as fh:
            fh.write(b"\xff\xd8\xff")
        INDEX = os.path.join(sandbox, "index.json")
        # ONE selectable persona, deliberately. With two selectable faces, the LRU tie-break
        # hands the second pick a different face and the test passes without ever exercising
        # the reservation. The other three are in the same pool and must be skipped: a gurn,
        # a row marked unusable as an identity reference, and m3039-as-02 with flags that
        # look fine (the blocklist still refuses it).
        def _row(handle, **extra):
            base = {"handle": handle, "pool_id": pool, "status": "active", "ref": ref,
                    "used_count": 0, "last_used_seq": 0, "gaze_used": [], "last_gaze": None,
                    "angles_used": [], "angles_reserved": []}
            base.update(extra)
            return base

        _atomic_write(INDEX, {
            "seq": 0, "no_face_cycle": {"period": 3, "position": 0},
            "recent_shots": [], "recent_heroes": [],
            "personas": {
                "t-01": _row("t-01"),
                "gurn-01": _row("gurn-01", exaggerated_expression=True,
                                usable_as_identity_reference=True),
                "plain-bad": _row("plain-bad", exaggerated_expression=False,
                                  usable_as_identity_reference=False),
                "m3039-as-02": _row("m3039-as-02", exaggerated_expression=False,
                                    usable_as_identity_reference=True),
            }})

        def pick(**kw):
            ns = argparse.Namespace(audience=aud, brand=None, force_face=False)
            for k, v in kw.items():
                setattr(ns, k, v)
            with contextlib.redirect_stdout(io.StringIO()):
                return cmd_pick(ns)

        def commit(**kw):
            ns = argparse.Namespace(hero=None, gaze=None, inline_gaze=None, face_angle=None,
                                    inline_face_angle=None, shot=None, expect_seq=None)
            for k, v in kw.items():
                setattr(ns, k, v)
            with contextlib.redirect_stdout(io.StringIO()):
                return cmd_commit(ns)

        def release(seq):
            with contextlib.redirect_stdout(io.StringIO()):
                return cmd_release(argparse.Namespace(seq=seq))

        def refused(fn, *a, **kw):
            try:
                with contextlib.redirect_stderr(io.StringIO()):
                    fn(*a, **kw)
            except SystemExit:
                return True
            return False

        def state():
            return _load(INDEX, "index")

        def angles(out):
            return [out.get("hero_face_angle"), out.get("inline_face_angle")]

        check("missing flags default to a usable identity",
              identity_refusal({"handle": "t-01", "status": "active"}) is None)
        check("exaggerated_expression refuses a hero",
              identity_refusal({"handle": "x", "exaggerated_expression": True}) is not None)
        check("usable_as_identity_reference false refuses a hero",
              identity_refusal({"handle": "x", "exaggerated_expression": False,
                                "usable_as_identity_reference": False}) is not None)
        check("m3039-as-02 is refused even when both flags say usable",
              identity_refusal({"handle": "m3039-as-02", "exaggerated_expression": False,
                                "usable_as_identity_reference": True}) is not None)

        p1 = pick()
        check("pick will not hero a gurn, a non-identity ref, or m3039-as-02",
              p1["hero"] == "t-01"
              and any("m3039-as-02" in w and "gurn-01" in w and "plain-bad" in w
                      for w in (p1.get("warnings") or [])),
              "hero=%s warnings=%s" % (p1.get("hero"), p1.get("warnings")))
        s1 = state()
        check("pick writes before it prints",
              s1.get("seq") == 1 and "1" in (s1.get("reservations") or {}),
              "seq=%s reservations=%s" % (s1.get("seq"), sorted(s1.get("reservations") or {})))
        check("the issued angles are held against the persona",
              sorted(s1["personas"]["t-01"]["angles_reserved"]) == sorted(angles(p1)))

        p2 = pick()
        # The regression itself: on 2026-08-10 two consecutive picks on the live bank came back
        # byte-identical — same hero, same hero_face_angle, same inline_face_angle — because
        # neither had spent anything.
        check("a second pick without a commit cannot repeat the first",
              p2["hero"] == p1["hero"] and not (set(angles(p1)) & set(angles(p2))),
              "%s vs %s" % (angles(p1), angles(p2)))
        check("both picks are still only reservations, nothing used yet",
              state()["personas"]["t-01"]["angles_used"] == []
              and len(state()["personas"]["t-01"]["angles_reserved"]) == 4)

        check("commit without --expect-seq is refused once reservations exist",
              refused(commit, hero=p2["hero"], face_angle=p2["hero_face_angle"],
                      inline_face_angle=p2["inline_face_angle"]))
        stray = [a for a in angle_ids(tax) if a not in angles(p1) + angles(p2)][0]
        check("commit of an angle the picker never issued is refused",
              refused(commit, hero=p2["hero"], face_angle=stray,
                      inline_face_angle=p2["inline_face_angle"], expect_seq=p2["seq"]))
        check("commit against the wrong hero is refused",
              refused(commit, hero="somebody-else", face_angle=p2["hero_face_angle"],
                      inline_face_angle=p2["inline_face_angle"], expect_seq=p2["seq"]))

        commit(hero=p2["hero"], face_angle=p2["hero_face_angle"],
               inline_face_angle=p2["inline_face_angle"], expect_seq=p2["seq"],
               gaze=p2["hero_gaze"], shot=p2["hero_shot"])
        e = state()["personas"]["t-01"]
        check("commit moves reserved -> used and closes the reservation",
              sorted(e["angles_used"]) == sorted(angles(p2))
              and sorted(e["angles_reserved"]) == sorted(angles(p1))
              and str(p2["seq"]) not in state()["reservations"]
              and e["used_count"] == 1)
        check("committing the same reservation twice is refused",
              refused(commit, hero=p2["hero"], face_angle=p2["hero_face_angle"],
                      inline_face_angle=p2["inline_face_angle"], expect_seq=p2["seq"]))

        release(p1["seq"])
        e = state()["personas"]["t-01"]
        check("release returns the reserved angles and touches nothing used",
              e["angles_reserved"] == [] and sorted(e["angles_used"]) == sorted(angles(p2))
              and not state()["reservations"])
        check("a released angle is available again, a used angle is not",
              set(angles(p1)) <= set(unused_angles(tax, e))
              and not (set(angles(p2)) & set(unused_angles(tax, e))))

        # The no-face cycle: period 3, and pick (not commit) is what advances it.
        idx = state()
        idx["no_face_cycle"] = {"period": 3, "position": 2}
        _atomic_write(INDEX, idx)
        n1 = pick()
        check("the cycle's no-face hero fires on pick", n1["hero"] == "NO-FACE")
        before = state()["no_face_cycle"]["position"]
        n2 = pick()
        check("the next pick is NOT no-face — the cycle advanced without a commit",
              n2["hero"] != "NO-FACE",
              "position %s -> %s" % (before, state()["no_face_cycle"]["position"]))
        commit(hero="NO-FACE", expect_seq=n1["seq"])
        check("a no-face reservation can be committed",
              str(n1["seq"]) not in state()["reservations"])
        release(n2["seq"])
        check("releasing the newest reservation rewinds the cycle position",
              state()["no_face_cycle"]["position"] == before,
              "back to %s" % before)

        ang = angles(p2)
        idx = state()
        idx.setdefault("reservations", {})["99"] = {
            "seq": 99, "hero": "m3039-as-02",
            "hero_face_angle": ang[0], "inline_face_angle": ang[1],
        }
        _atomic_write(INDEX, idx)
        check("commit of blocklisted m3039-as-02 is refused even when its flags look usable",
              refused(commit, hero="m3039-as-02", face_angle=ang[0],
                      inline_face_angle=ang[1], expect_seq=99))
        check("a refused identity commit does not close the reservation",
              "99" in (state().get("reservations") or {}))

        _atomic_write(INDEX, {
            "seq": 0, "no_face_cycle": {"period": 3, "position": 1},
            "recent_shots": [], "recent_heroes": [],
            "personas": {"gurn-01": _row("gurn-01", exaggerated_expression=True,
                                         usable_as_identity_reference=False)}})
        g = pick(force_face=True)
        check("a pool whose only face is a gurn degrades to NO-FACE",
              g["hero"] == "NO-FACE", "hero=%s" % g.get("hero"))
    finally:
        INDEX = real_index
        shutil.rmtree(sandbox, ignore_errors=True)

    print()
    if failures:
        sys.exit("✗ selftest FAILED: %s" % ", ".join(failures))
    print("✓ selftest passed")


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
    c.add_argument("--expect-seq", type=int,
                   help="seq from pick — names WHICH reservation this commit closes (required)")
    c.set_defaults(fn=cmd_commit)

    r = sub.add_parser("release", help="hand back a reservation for an article that never published")
    r.add_argument("--seq", type=int, required=True, help="seq from the pick being abandoned")
    r.set_defaults(fn=cmd_release)

    s = sub.add_parser("status", help="bank health per rotation pool")
    s.set_defaults(fn=cmd_status)

    t = sub.add_parser("selftest", help="exercise the reservation lifecycle on a sandbox copy")
    t.set_defaults(fn=cmd_selftest)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

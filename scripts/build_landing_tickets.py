#!/usr/bin/env python3
"""Daily listicle-landing ticket builder (Kevin 2026-10-08: 1 listicle landing DRAFT per day, Kevin approves).

  /usr/bin/python3 scripts/build_landing_tickets.py            # add ONE ticket if the queue has no open one
  /usr/bin/python3 scripts/build_landing_tickets.py --dry-run  # show the pick, write nothing
  /usr/bin/python3 scripts/build_landing_tickets.py --force    # add one even if an open ticket exists

Queue: daily-landing-tickets.md, one line per ticket:
  - [ ] listicle | <store> | product=<handle> · angle: <brief> (added YYYY-MM-DD)
Done lines are re-tagged by run_landing_daily.sh: - [DRAFT YYYY-MM-DD page <id>] / - [FAILED YYYY-MM-DD ...].

Product pick: live https://wellnessnest.co/products.json, filtered to real single SKUs (product_type set, not
shipping protection / reserve / multi-pack bundles), ageaura_rules.require_target (AgeAura = NMN + TMG Complex
only; ageaura-pure-urolithin-a and any other Urolithin A AgeAura handle fail closed), a curated packaging ref in product_refs/<handle>.png and an entry in
templates/landing/listicle-angles.json. Rotation, one landing a day:
  Recency is the last real dated landing. A spec counts only when `created` is YYYY-MM-DD.
  An undated spec does not count, and a file's modification time is never a landing date.
  A queue line counts when it is a DRAFT or a published page; the date in that tag is the
  landing day. FAILED lines are not landings. Open `- [ ]` lines are the upcoming days, in
  file order, one per day — the `(added ...)` stamp is not a use date.
  The product on the previous day is not picked again, unless it is the only eligible product.
  ShilaSource resin and AgeAura Pure NMN + TMG are priority products. In the 7-day window
  ending on the day being filled, each eligible priority product appears at least as often
  as the busiest other product. A priority that is behind that pace is the next pick when
  that is not a back-to-back day.
  Otherwise the least-recently-used eligible product is next. A tie goes to a priority
  product, then to catalog order.
Angle: the least-used angle for that product. The new line must pass brand_rules + lint_tickets.py.
FloraFresh lines also carry florafresh_rules.LANDING_NOTE (formula from the Supplement Facts label, never the PDP).
Shilajit Shockwave lines carry shockwave_rules.LANDING_NOTE (identity lines only; no dose the label file omits).
Pure Shilajit Gold Resin lines carry gold_resin_rules.LANDING_NOTE (the OCR serving line and 75% Fulvic; no milligram and no other dose).
ShilaSource resin lines carry shilasource_resin_rules.LANDING_NOTE (front-of-pack lines only; no milligram and no other dose).
Turkesterone Advanced Formula lines carry turkesterone_rules.LANDING_NOTE (front-of-pack lines only; the split capsule badge; no milligram and no Supplement Facts dose).
A product with product_refs/<handle>.palette.json also carries packaging_palette.landing_note
(UI colors match that file; do not opt out or force a conflicting hue).
"""
import datetime as dt, json, os, re, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import ageaura_rules as ar  # noqa: E402
import brand_rules as br  # noqa: E402
import florafresh_rules as ff  # noqa: E402
import gold_resin_rules as gr  # noqa: E402
import packaging_palette as pp  # noqa: E402
import shilasource_resin_rules as sr  # noqa: E402
import shockwave_rules as sw  # noqa: E402
import turkesterone_rules as tk  # noqa: E402

QUEUE = os.path.join(ROOT, "daily-landing-tickets.md")
ANGLES = os.path.join(ROOT, "templates", "landing", "listicle-angles.json")
ICT = dt.timezone(dt.timedelta(hours=7))
HEADER = """# GenSeo DAILY listicle landing queue (1 unpublished draft per day — Kevin approves, never auto-live)

Built by `scripts/build_landing_tickets.py`, consumed by `scripts/run_landing_daily.sh` (launchd com.pati.genseo-landing).
Shopify PAGES with handle `gsl-preview-*`: never counted toward the 5/day article target. Guard: `scripts/landing_guard.py`.
Format: `- [ ] listicle | <store> | product=<handle> · angle: <brief> (added YYYY-MM-DD)`

"""
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) GenSeo-landing-builder"}
BUNDLE = re.compile(r"(reserve|pack|single-jar|single-bottle|-p\d+$|duo|bundle|shipping-protection)", re.I)
# Owner priority for creative and landing work (Kevin 2026-10-17). Order is the tie-break.
PRIORITY_HANDLES = (
    "shilasource-himalayan-shilajit-resin",
    "ageaura-pure-nmn-tmg-nad-complex",
)
FAIRNESS_DAYS = 7
_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_PRODUCT = re.compile(r"product=([a-z0-9-]+)")
_REAL_LINE = re.compile(r"^- \[(?:DRAFT|PUBLISHED|LIVE)\b")
_OPEN_LINE = re.compile(r"^- \[ \] ")
_HANDLE = re.compile(r"^[a-z0-9-]+$")
_SPEC_URL = re.compile(r"wellnessnest\.co/products/([a-z0-9-]+)")


def today():
    return dt.datetime.now(ICT).date()


def live_products():
    d = json.load(urllib.request.urlopen(urllib.request.Request("https://wellnessnest.co/products.json?limit=250", headers=UA), timeout=30))
    return {p["handle"]: p for p in d["products"]}


def _iso(raw):
    try:
        return dt.date.fromisoformat(raw)
    except ValueError:
        return None


def created_day(spec):
    """YYYY-MM-DD from a spec's `created` field, or None when the spec is undated.

    File modification time is not a landing date.
    """
    if not isinstance(spec, dict):
        return None
    raw = spec.get("created")
    if not isinstance(raw, str) or not _DATE.fullmatch(raw.strip()):
        return None
    return _iso(raw.strip())


def spec_landings(spec):
    """(date, handle) pairs for one spec. Empty when `created` is missing or not a date."""
    day = created_day(spec)
    if day is None:
        return []
    handles = set(_SPEC_URL.findall(json.dumps(spec)))
    prod = spec.get("product")
    if isinstance(prod, dict) and isinstance(prod.get("handle"), str):
        handle = prod["handle"].strip().lower()
        if _HANDLE.fullmatch(handle):
            handles.add(handle)
    hero = pp.hero_handle(spec)
    if hero and _HANDLE.fullmatch(hero):
        handles.add(hero)
    return [(day, h) for h in sorted(handles)]


def parse_queue(text):
    """(real landings, open handles in file order).

    A real landing is a DRAFT or published line. Its landing day is the first
    YYYY-MM-DD on the line (the status tag), not a later `(added ...)` stamp.
    FAILED lines are attempts, not landings. Open lines are upcoming days.
    """
    real, open_handles = [], []
    for line in (text or "").splitlines():
        found = _PRODUCT.search(line)
        if not found:
            continue
        handle = found.group(1)
        if _OPEN_LINE.match(line):
            open_handles.append(handle)
            continue
        if not _REAL_LINE.match(line):
            continue
        dates = [d for d in (_iso(raw) for raw in _DATE.findall(line)) if d]
        if dates:
            real.append((dates[0], handle))
    return real, open_handles


def collect_uses(queue_text, specs):
    """Dated landings plus open handles. The same (date, handle) counts once."""
    real = set()
    for spec in specs or []:
        for pair in spec_landings(spec):
            real.add(pair)
    queued, open_handles = parse_queue(queue_text or "")
    real.update(queued)
    return {"real": sorted(real), "open": open_handles}


def history(queue_path=None, drafts_dir=None):
    """Dated landings from the queue file and landing_drafts/*.json.

    Undated specs contribute nothing. Modification time is not read.
    """
    path = queue_path or QUEUE
    text = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    folder = drafts_dir or os.path.join(ROOT, "landing_drafts")
    specs = []
    if os.path.isdir(folder):
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".json"):
                continue
            try:
                with open(os.path.join(folder, name), encoding="utf-8") as fh:
                    specs.append(json.load(fh))
            except Exception:
                continue
    return collect_uses(text, specs)


def schedule(uses, today):
    """Place open tickets on the upcoming days and return (events, next_day).

    Events are (date, handle) in order. `next_day` is the empty day a new
    ticket would fill. A landing already dated today or later pushes the
    first open ticket to the following day.
    """
    events = sorted(uses.get("real") or [])
    latest = events[-1][0] if events else None
    cursor = today if latest is None or latest < today else latest + dt.timedelta(days=1)
    for handle in uses.get("open") or []:
        events.append((cursor, handle))
        cursor += dt.timedelta(days=1)
    return events, cursor


def _counts(events, day):
    start = day - dt.timedelta(days=FAIRNESS_DAYS - 1)
    counts = {}
    for when, handle in events:
        if start <= when < day:
            counts[handle] = counts.get(handle, 0) + 1
    return counts


def _others_max(counts, priority):
    skip = set(priority)
    best = 0
    for handle, count in counts.items():
        if handle not in skip and count > best:
            best = count
    return best


def _fair(counts, required, priority):
    busiest = _others_max(counts, priority)
    return all(counts.get(handle, 0) >= busiest for handle in required)


def choose_product(eligible, events, day, order=None, priority=None):
    """Handle to schedule on `day`.

    `events` are landings and already-queued days. `eligible` is the product
    catalog that may be chosen. Back-to-back with the previous day is refused
    while another eligible product exists. Among the rest, a priority product
    that is behind the busiest other product in the 7-day window wins; otherwise
    the least recently used product wins, with a priority tie-break.
    """
    priority = tuple(priority or PRIORITY_HANDLES)
    seen, eligible_list = set(), []
    for handle in eligible:
        if handle and handle not in seen:
            seen.add(handle)
            eligible_list.append(handle)
    if not eligible_list:
        raise ValueError("no eligible product")
    order = list(order or eligible_list)
    live_priority = [handle for handle in priority if handle in seen]
    previous = {
        handle for when, handle in events
        if when == day - dt.timedelta(days=1) and handle in seen
    }
    pool = [handle for handle in eligible_list if handle not in previous] or eligible_list
    before = _counts(events, day)
    busiest = _others_max(before, priority)
    last = {}
    for when, handle in events:
        if when < day and (handle not in last or when > last[handle]):
            last[handle] = when

    def deficit(handle):
        if handle not in live_priority:
            return 0
        return max(0, busiest - before.get(handle, 0))

    def fair_after(handle):
        counts = dict(before)
        counts[handle] = counts.get(handle, 0) + 1
        return _fair(counts, live_priority, priority)

    fair_pool = [handle for handle in pool if fair_after(handle)]
    use = fair_pool or pool

    def prio_rank(handle):
        try:
            return priority.index(handle)
        except ValueError:
            return len(priority)

    def cat_rank(handle):
        try:
            return order.index(handle)
        except ValueError:
            return len(order)

    use.sort(key=lambda handle: (
        -deficit(handle), last.get(handle, dt.date.min), prio_rank(handle), cat_rank(handle)))
    return use[0]


def next_product(uses, eligible, order=None, on=None, priority=None):
    """(handle, day) the builder would append for this history."""
    events, day = schedule(uses, on or today())
    return choose_product(eligible, events, day, order, priority), day


def angle_counts(handle):
    c = {}
    if os.path.exists(QUEUE):
        with open(QUEUE, encoding="utf-8") as fh:
            queued = fh.readlines()
        for line in queued:
            if f"product={handle} " in line or line.rstrip().endswith(f"product={handle}"):
                m = re.search(r"angle: (.*?)(?: · audience:.*?)?(?: \(added \d{4}-\d{2}-\d{2}\))?$", line.strip())
                if m:
                    c[m.group(1)] = c.get(m.group(1), 0) + 1
    return c


def refused_angle_keys(angles):
    """Angle-catalog keys that are denied AgeAura product handles."""
    refused = []
    for key in angles:
        if str(key).startswith("_"):
            continue
        if ar.classify_handle(key) == "deny":
            refused.append(key)
    return refused


def ticket_line(handle, store, angle, audience, added):
    """One landing-queue line. A denied AgeAura handle raises brand_rules.GuardError."""
    try:
        handle = ar.require_target(handle)
    except ar.AgeAuraProductError as exc:
        raise br.GuardError(list(exc.reasons))
    line = "- [ ] listicle | %s | product=%s · angle: %s · audience: %s" % (
        store, handle, angle, audience)
    if handle == ff.HANDLE:
        line += " · " + ff.LANDING_NOTE
    if handle == sw.HANDLE:
        line += " · " + sw.LANDING_NOTE
    if handle == gr.HANDLE:
        line += " · " + gr.LANDING_NOTE
    if handle == sr.HANDLE:
        line += " · " + sr.LANDING_NOTE
    if handle == tk.HANDLE:
        line += " · " + tk.LANDING_NOTE
    note = pp.landing_note(handle)
    if note:
        line += " · " + note
    line += " (added %s)" % added
    return line


def eligible_handles(products, angles):
    """Catalog handles that can take a landing today, plus the skip reasons."""
    cands, why, order = [], {}, []
    for handle in angles:
        if str(handle).startswith("_"):
            continue
        order.append(handle)
        product = products.get(handle)
        if not product:
            why[handle] = "not on the live store"
            continue
        if BUNDLE.search(handle) or not product.get("product_type"):
            why[handle] = "bundle / non-SKU"
            continue
        if ar.classify_handle(handle) == "deny":
            why[handle] = "ageaura product guard"
            continue
        if not any(v.get("available") for v in product.get("variants", [])):
            why[handle] = "sold out"
            continue
        if not os.path.exists(os.path.join(ROOT, "product_refs", f"{handle}.png")):
            why[handle] = "no curated product_refs png"
            continue
        cands.append(handle)
    return cands, why, order


def pick(products, angles, uses, on=None):
    day = on or today()
    cands, why, order = eligible_handles(products, angles)
    if not cands:
        sys.exit(f"✗ no eligible product: {why}")
    events, slot = schedule(uses, day)
    handle = choose_product(cands, events, slot, order)
    meta = angles[handle]
    cnt = angle_counts(handle)
    angle = sorted(meta["angles"], key=lambda a: (cnt.get(a, 0), meta["angles"].index(a)))[0]
    last = [when for when, used in events if used == handle and when < slot]
    age = (slot - max(last)).days if last else 99999
    return handle, meta, angle, slot, age, why


def main():
    dry, force = "--dry-run" in sys.argv, "--force" in sys.argv
    q = open(QUEUE).read() if os.path.exists(QUEUE) else HEADER
    open_lines = [l for l in q.splitlines() if l.startswith("- [ ] ")]
    if open_lines and not force:
        print(f"queue already has an open ticket: {open_lines[0]}")
        return
    raw_angles = json.load(open(ANGLES))
    angles = {}
    for key in refused_angle_keys(raw_angles):
        print(f"ageaura guard: dropped landing angle key {key}")
    for key, meta in raw_angles.items():
        if key.startswith("_") or ar.classify_handle(key) != "deny":
            angles[key] = meta
    h, meta, angle, slot, age, why = pick(live_products(), angles, history())
    try:
        line = ticket_line(h, meta["store"], angle, meta.get("audience", ""), today())
        line = br.prepare_ticket(line)
    except br.GuardError as e:
        sys.exit(f"✗ brand_rules rejected the ticket: {e}")
    v = br.violations(line)
    if v:
        sys.exit(f"✗ brand_rules rejected the ticket: {v}")
    when = "never" if age > 10000 else f"{age} day(s) before {slot.isoformat()}"
    print(f"pick: {h} ({when})")
    if why:
        print("skipped:", "; ".join(f"{k}: {v}" for k, v in why.items()))
    print(line)
    if dry:
        return
    if not q.endswith("\n"):
        q += "\n"
    open(QUEUE, "w").write(q + line + "\n")
    r = subprocess.run(["/usr/bin/python3", os.path.join(ROOT, "scripts", "lint_tickets.py"), QUEUE], capture_output=True, text=True)
    if r.returncode != 0:
        open(QUEUE, "w").write(q)  # roll back
        sys.exit(f"✗ lint_tickets failed, ticket NOT added:\n{r.stdout}{r.stderr}")
    print("added to daily-landing-tickets.md (lint ok)")


if __name__ == "__main__":
    main()

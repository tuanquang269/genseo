#!/usr/bin/env python3
"""Daily listicle-landing ticket builder (Kevin 2026-10-08: 1 listicle landing DRAFT per day, Kevin approves).

  /usr/bin/python3 scripts/build_landing_tickets.py            # add ONE ticket if the queue has no open one
  /usr/bin/python3 scripts/build_landing_tickets.py --dry-run  # show the pick, write nothing
  /usr/bin/python3 scripts/build_landing_tickets.py --force    # add one even if an open ticket exists

Queue: daily-landing-tickets.md, one line per ticket:
  - [ ] listicle | <store> | product=<handle> · angle: <brief> (added YYYY-MM-DD)
Done lines are re-tagged by run_landing_daily.sh: - [DRAFT YYYY-MM-DD page <id>] / - [FAILED YYYY-MM-DD ...].

Product pick: live https://wellnessnest.co/products.json, filtered to real single SKUs (product_type set, not
shipping protection / reserve / multi-pack bundles), brand_rules.product_allowed (AgeAura = NMN + TMG Complex
only, no Urolithin), a curated packaging ref in product_refs/<handle>.png and an entry in
templates/landing/listicle-angles.json. Rotation: least-recently-used product, never one used in the last
GENSEO_LANDING_NO_REPEAT_DAYS days (default 6) — history = every dated line in the queue + landing_drafts/*.json.
Angle: the least-used angle for that product. The new line must pass brand_rules + lint_tickets.py.
FloraFresh lines also carry florafresh_rules.LANDING_NOTE (formula from the Supplement Facts label, never the PDP).
Shilajit gummies lines carry shilajit_gummies_rules.LANDING_NOTE (60 gummies, 60-day supply; no 30-serving panel).
"""
import datetime as dt, json, os, re, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import brand_rules as br  # noqa: E402
import florafresh_rules as ff  # noqa: E402
import shilajit_gummies_rules as sg  # noqa: E402

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


def today():
    return dt.datetime.now(ICT).date()


def live_products():
    d = json.load(urllib.request.urlopen(urllib.request.Request("https://wellnessnest.co/products.json?limit=250", headers=UA), timeout=30))
    return {p["handle"]: p for p in d["products"]}


def history():
    """handle -> list of dates it was used for a landing page (queue lines + spec files)."""
    used = {}
    if os.path.exists(QUEUE):
        for line in open(QUEUE):
            m = re.search(r"product=([a-z0-9-]+)", line)
            if not m:
                continue
            ds = re.findall(r"(\d{4}-\d{2}-\d{2})", line)
            if ds:
                used.setdefault(m.group(1), []).append(max(ds))
    d = os.path.join(ROOT, "landing_drafts")
    for f in os.listdir(d):
        if f.endswith(".json"):
            try:
                s = json.load(open(os.path.join(d, f)))
            except Exception:
                continue
            hs = re.findall(r"wellnessnest\.co/products/([a-z0-9-]+)", json.dumps(s))
            day = dt.datetime.fromtimestamp(os.path.getmtime(os.path.join(d, f)), ICT).date().isoformat()
            for h in set(hs):
                used.setdefault(h, []).append(s.get("created") or day)
    return used


def angle_counts(handle):
    c = {}
    if os.path.exists(QUEUE):
        for line in open(QUEUE):
            if f"product={handle} " in line or line.rstrip().endswith(f"product={handle}"):
                m = re.search(r"angle: (.*?)(?: · audience:.*?)?(?: \(added \d{4}-\d{2}-\d{2}\))?$", line.strip())
                if m:
                    c[m.group(1)] = c.get(m.group(1), 0) + 1
    return c


def pick(products, angles, used, window):
    t = today()
    cands, why = [], {}
    for h, meta in angles.items():
        if h.startswith("_"):
            continue
        p = products.get(h)
        if not p:
            why[h] = "not on the live store"; continue
        if BUNDLE.search(h) or not p.get("product_type"):
            why[h] = "bundle / non-SKU"; continue
        if not br.product_allowed(h):
            why[h] = "brand_rules"; continue
        if not any(v.get("available") for v in p.get("variants", [])):
            why[h] = "sold out"; continue
        if not os.path.exists(os.path.join(ROOT, "product_refs", f"{h}.png")):
            why[h] = "no curated product_refs png"; continue
        last = max(used.get(h, ["1970-01-01"]))
        age = (t - dt.date.fromisoformat(last)).days
        cands.append((age, h))
    if not cands:
        sys.exit(f"✗ no eligible product: {why}")
    fresh = [c for c in cands if c[0] >= window]
    pool = fresh or cands            # everything used inside the window -> still take the least recent one
    pool.sort(key=lambda c: (-c[0], list(angles).index(c[1])))
    age, h = pool[0]
    meta = angles[h]
    cnt = angle_counts(h)
    angle = sorted(meta["angles"], key=lambda a: (cnt.get(a, 0), meta["angles"].index(a)))[0]
    return h, meta, angle, age, (not fresh), why


def main():
    dry, force = "--dry-run" in sys.argv, "--force" in sys.argv
    q = open(QUEUE).read() if os.path.exists(QUEUE) else HEADER
    open_lines = [l for l in q.splitlines() if l.startswith("- [ ] ")]
    if open_lines and not force:
        print(f"queue already has an open ticket: {open_lines[0]}")
        return
    window = int(os.environ.get("GENSEO_LANDING_NO_REPEAT_DAYS", "6"))
    raw_angles = json.load(open(ANGLES))
    angles = {}
    for key, meta in raw_angles.items():
        if key.startswith("_") or br.product_allowed(key):
            angles[key] = meta
        else:
            print(f"ageaura guard: dropped landing angle key {key}")
    h, meta, angle, age, stale, why = pick(live_products(), angles, history(), window)
    line = f"- [ ] listicle | {meta['store']} | product={h} · angle: {angle} · audience: {meta.get('audience', '')}"
    if h == ff.HANDLE:
        line += " · " + ff.LANDING_NOTE
    if h == sg.HANDLE:
        line += " · " + sg.LANDING_NOTE
    line += f" (added {today()})"
    try:
        line = br.prepare_ticket(line)
    except br.GuardError as e:
        sys.exit(f"✗ brand_rules rejected the ticket: {e}")
    v = br.violations(line)
    if v:
        sys.exit(f"✗ brand_rules rejected the ticket: {v}")
    print(f"pick: {h} (last used {'never' if age > 10000 else f'{age} day(s) ago'}{'; every product used inside the window — LRU fallback' if stale else ''})")
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

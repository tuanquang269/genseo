#!/usr/bin/env python3
"""Regression monitoring for the pages that actually earn SG traffic.

Why this exists: we edit live Shopify constantly, much of it driven by a cheap
model, and it has silently failed at least twice (dropped the 6th product from
the NutraBio pillar; marked a CTR ticket DONE while the metafields stayed empty).
Both were caught by hand. This turns "verify the live page, not the ticket" into
a diff you can run.

Wraps claude-seo's drift scripts, which snapshot title, meta description,
canonical, robots, H1/H2/H3, JSON-LD, Open Graph, status code and content hashes
into SQLite (~/.cache/claude-seo/drift/baselines.db), then classify changes with
17 rules across CRITICAL / WARNING / INFO.

Targets live in drift_targets.txt (one URL per line, '#' comments allowed) so the
watch list is editable without touching code.

Usage:
    python3 scripts/seo_drift.py baseline          # snapshot every target
    python3 scripts/seo_drift.py baseline --only protein-powder
    python3 scripts/seo_drift.py compare           # diff every target vs baseline
    python3 scripts/seo_drift.py compare --fail-on-critical   # for a pre/post-sprint check
    python3 scripts/seo_drift.py history <url>

Run `baseline` BEFORE a batch of edits and `compare` after.

READING THE OUTPUT: ignore INFO. The `content_hash_changed` rule fired on 26 of 30
pages within a minute of taking the baselines (measured 2026-07-30), because the
Shopify theme emits volatile markup on every request. INFO is noise on this store.
CRITICAL and WARNING are the signal, which is why --fail-on-critical exists.

ponytail: --skip-cwv is the default because a PSI call per URL turns a 2-minute
sweep into a 15-minute one. The API key IS configured now (2026-07-30), so --cwv
works and adds LCP/INP/CLS. Use it on the baseline and on before/after checks, not
on every routine compare. Note CrUX is a 28-day rolling p75: a CWV diff taken a
day after an edit shows nothing. Product URLs have no CrUX data at all
(insufficient Chrome traffic) so their CWV fields stay empty.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ROOT / "drift_targets.txt"
LOG = ROOT / "drift_runs.log"


def claude_seo_bin():
    for p in glob.glob(os.path.expanduser(
            "~/.claude/plugins/marketplaces/*claude-seo*/bin/claude-seo")):
        if os.access(p, os.X_OK):
            return p
    sys.exit("claude-seo runtime not found. Install the plugin, then run `/seo setup`.")


def runtime_env():
    """Pin CLAUDE_SEO_PYTHON so this works from cron too, not just inside Claude
    Code. Homebrew python3 on this machine has a broken pyexpat and cannot build
    the runtime venv (wiki/tools/homebrew-python314-pyexpat-broken-venv.md)."""
    env = os.environ.copy()
    if not env.get("CLAUDE_SEO_PYTHON"):
        cands = sorted(glob.glob(os.path.expanduser(
            "~/.local/share/uv/python/cpython-3.1[2-9]*/bin/python3.1[2-9]")))
        if cands:
            env["CLAUDE_SEO_PYTHON"] = cands[-1]
    env.setdefault("CLAUDE_SEO_DATA_DIR",
                   os.path.expanduser("~/Library/Application Support/claude-seo"))
    env.pop("CLAUDE_PLUGIN_DATA", None)
    return env


def load_targets(only=None):
    if not TARGETS.is_file():
        sys.exit(f"missing {TARGETS}")
    urls = []
    for line in TARGETS.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line.startswith("http"):
            urls.append(line)
    if only:
        urls = [u for u in urls if only in u]
        if not urls:
            sys.exit(f"no target matches {only!r}")
    return urls


def run_script(script, args, env, binary, timeout=240):
    return subprocess.run([binary, "run", script, *args],
                          capture_output=True, text=True, timeout=timeout, env=env)


def short(url):
    return re.sub(r"^https?://wellnessnest\.co", "", url) or "/"


def cmd_baseline(args):
    binary, env = claude_seo_bin(), runtime_env()
    urls = load_targets(args.only)
    flags = [] if args.cwv else ["--skip-cwv"]
    ok = failed = 0
    for i, url in enumerate(urls, 1):
        res = run_script("drift_baseline.py", [*flags, url], env, binary)
        if res.returncode == 0:
            ok += 1
            status = "ok"
        else:
            failed += 1
            status = f"FAIL rc={res.returncode} {res.stderr.strip()[:90]}"
        print(f"[{i:2d}/{len(urls)}] {short(url)[:70]:72s} {status}", flush=True)
    print(f"\nbaselines captured: {ok} ok, {failed} failed")
    return 1 if failed else 0


NOISY_RULES = {
    # Measured 2026-07-30: three PSI mobile runs on the unchanged homepage returned
    # performance 76, 90 and 95 across cache windows (identical within a window,
    # because PSI caches). rule_12 fires on any 10-point drop, so a 19-point lab
    # swing with zero site change guarantees false WARNINGs. Field data (rule_11
    # cwv_regressed) is a 28-day p75 and IS trustworthy — that is the CWV signal.
    "perf_score_dropped",
}


def parse_findings(stdout):
    """drift_compare prints a human summary then a JSON payload. Verified shape
    (2026-07-30): {"summary": {critical, warning, info}, "triggered_findings":
    [{rule, severity, old_value, new_value, message}], "untriggered_findings":[...]}.
    Only triggered findings matter. Falls back to counting severity words so a
    future format change degrades instead of crashing the sweep.

    Counts are recomputed from the triggered findings rather than read from
    `summary`, because NOISY_RULES are dropped first and the summary would still
    include them."""
    brace = stdout.find("{")
    if brace == -1:
        return None, {sev: 0 for sev in ("CRITICAL", "WARNING", "INFO")}
    try:
        data = json.loads(stdout[brace:])
    except json.JSONDecodeError:
        return None, {
            sev: len(re.findall(rf"\b{sev}\b", stdout))
            for sev in ("CRITICAL", "WARNING", "INFO")
        }
    triggered = [c for c in (data.get("triggered_findings") or [])
                 if c.get("rule") not in NOISY_RULES]
    counts = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
    for c in triggered:
        sev = str(c.get("severity", "")).upper()
        if sev in counts:
            counts[sev] += 1
    return triggered, counts


def cmd_selftest(args):
    """The parser is the one piece here that can silently lie: a wrong key name
    reports 'clean' for a page that actually regressed. Guard it."""
    payload = json.dumps({
        "summary": {"critical": 1, "warning": 2, "info": 1},
        "triggered_findings": [
            {"rule": "title_changed", "severity": "CRITICAL", "message": "x"},
            {"rule": "cwv_regressed", "severity": "WARNING", "message": "y"},
            {"rule": "perf_score_dropped", "severity": "WARNING", "message": "noise"},
            {"rule": "content_hash_changed", "severity": "INFO", "message": "z"},
        ],
    })
    found, counts = parse_findings("Human preamble line\n" + payload)
    assert counts == {"CRITICAL": 1, "WARNING": 1, "INFO": 1}, counts
    assert [c["rule"] for c in found] == ["title_changed", "cwv_regressed",
                                          "content_hash_changed"], found

    # no JSON at all, and unparseable JSON, must degrade rather than raise
    assert parse_findings("no json here")[1] == {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
    assert parse_findings("{not json")[0] is None
    print("parse_findings ok")
    return 0


def cmd_compare(args):
    binary, env = claude_seo_bin(), runtime_env()
    urls = load_targets(args.only)
    flags = [] if args.cwv else ["--skip-cwv"]
    totals = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
    problems = []
    errors = 0

    for i, url in enumerate(urls, 1):
        res = run_script("drift_compare.py", [*flags, url], env, binary)
        if res.returncode not in (0, 1):  # 1 = drift detected, not a tool error
            errors += 1
            print(f"[{i:2d}/{len(urls)}] {short(url)[:70]:72s} ERROR {res.stderr.strip()[:80]}")
            continue
        changes, counts = parse_findings(res.stdout)
        for sev in totals:
            totals[sev] += counts[sev]
        tag = ("clean" if not any(counts.values())
               else " ".join(f"{s[0]}{counts[s]}" for s in ("CRITICAL", "WARNING", "INFO") if counts[s]))
        print(f"[{i:2d}/{len(urls)}] {short(url)[:70]:72s} {tag}", flush=True)
        if counts["CRITICAL"] or counts["WARNING"]:
            problems.append((url, changes, counts, res.stdout))

    print(f"\n=== totals: {totals['CRITICAL']} CRITICAL, {totals['WARNING']} WARNING, "
          f"{totals['INFO']} INFO across {len(urls)} pages ({errors} errors) ===")

    for url, changes, counts, raw in problems:
        print(f"\n--- {short(url)} ---")
        if changes:
            for c in changes:
                sev = str(c.get("severity", "?")).upper()
                if sev == "INFO":
                    continue
                print(f"  [{sev}] {c.get('rule', '?')}: {c.get('message', '')}")
                old, new = c.get("old_value"), c.get("new_value")
                if old != new:
                    print(f"          was: {str(old)[:100]}")
                    print(f"          now: {str(new)[:100]}")
        else:
            print(raw.strip()[:1200])

    try:
        import datetime
        with LOG.open("a") as lg:
            lg.write(f"{datetime.datetime.now().isoformat(timespec='seconds')}\t"
                     f"pages={len(urls)}\tcritical={totals['CRITICAL']}\t"
                     f"warning={totals['WARNING']}\tinfo={totals['INFO']}\terrors={errors}\n")
    except OSError:
        pass

    if args.fail_on_critical and totals["CRITICAL"]:
        return 1
    return 1 if errors else 0


def cmd_history(args):
    binary, env = claude_seo_bin(), runtime_env()
    res = run_script("drift_history.py", ["-n", str(args.limit), args.url], env, binary)
    print(res.stdout or res.stderr)
    return res.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("baseline", help="snapshot the current state of every target")
    b.add_argument("--only", help="substring filter on the target URLs")
    b.add_argument("--cwv", action="store_true", help="include Core Web Vitals (needs a PageSpeed API key)")
    b.set_defaults(func=cmd_baseline)

    c = sub.add_parser("compare", help="diff every target against its baseline")
    c.add_argument("--only", help="substring filter on the target URLs")
    c.add_argument("--cwv", action="store_true")
    c.add_argument("--fail-on-critical", action="store_true",
                   help="exit 1 when any CRITICAL change is found")
    c.set_defaults(func=cmd_compare)

    sub.add_parser("selftest", help="check the findings parser").set_defaults(func=cmd_selftest)

    h = sub.add_parser("history", help="show stored history for one URL")
    h.add_argument("url")
    h.add_argument("--limit", "-n", type=int, default=20)
    h.set_defaults(func=cmd_history)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Heartbeat gate for an off-Mac article failover. Does not publish.

The MacBook daily lane (deploy/grokbot-genseo-daily.sh) stays primary. This
script only decides whether that lane has already covered today's ICT articles.
It reads the public atom feed and the committed ticket file. It does not call
the article publisher, a model router, or an image tool.

Off unless GENSEO_CLOUD_FAILOVER is exactly "1" (the GitHub Actions variable
defaults to unset). A gap after the late cutoff still exits fail-closed: the
publish arm is not in this scaffold. See docs/CLOUD_FAILOVER_FEASIBILITY.md.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import socket
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import genseo_roster  # noqa: E402  absolute Mac path; empty on a Linux checkout is expected
import validate_article  # noqa: E402  QRG skip note only; does not score or call a network

ICT = dt.timezone(dt.timedelta(hours=7))
DEFAULT_CUTOFF = "18:30"  # ICT, after 14:47 plus the 50-minute peer window
DEFAULT_TARGET = 5
DEFAULT_PEER_MIN = 50
LOCK_STALE_SEC = 21600
FEED_TIMEOUT_SEC = 45
FLAG = "GENSEO_CLOUD_FAILOVER"

DONE_RE = re.compile(r"\[DONE\s+(\d{4}-\d{2}-\d{2})\b")
OPEN_RE = re.compile(r"^(?:- \[ \]|## \[ \])", re.M)
_SECRET_RE = re.compile(
    r"(shpat_[A-Za-z0-9]+|sk-ant-[A-Za-z0-9_\-]+|sk-[A-Za-z0-9]{20,})"
)


def redact(text):
    """Drop credential-shaped substrings. Public article URLs may remain."""
    if not text:
        return ""
    cleaned = _SECRET_RE.sub("[redacted]", str(text))
    cleaned = " ".join(cleaned.split())
    return cleaned[:240]


def flag_enabled(value):
    return value == "1"


def parse_cutoff(value):
    """Return minutes from midnight, or None when the value is not HH:MM."""
    if not isinstance(value, str):
        return None
    parts = value.split(":")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        return None
    hour, minute = int(parts[0]), int(parts[1])
    if hour > 23 or minute > 59:
        return None
    return hour * 60 + minute


def parse_target(value):
    if isinstance(value, bool) or not isinstance(value, int):
        text = str(value)
        if not text.isdigit() or text == "0":
            return None
        return int(text)
    if value < 1:
        return None
    return value


def minutes_ict(moment):
    return moment.hour * 60 + moment.minute


def count_repo_record(text, day):
    """Return (done_today, open_tickets) from a daily-tickets.md body.

    done_today counts `[DONE YYYY-MM-DD` headings for that ICT date. Open
    tickets use the same line pattern as deploy/grokbot-genseo-daily.sh.
    """
    done = len([item for item in DONE_RE.findall(text or "") if item == day])
    open_n = len(OPEN_RE.findall(text or ""))
    return done, open_n


def classify_lock(lock_dir, now_epoch, stale_sec, pid_alive, pid_is_wrapper):
    """Read-only view of state/daily.lock. Does not create or remove it.

    Returns "absent", "held", or "stale". "held" means stand down. A missing
    PID is held until stale_sec so a lock that is still being stamped is not
    treated as free. A dead PID is stale immediately. This cannot see a lock
    on another machine.
    """
    if not lock_dir or not os.path.isdir(lock_dir):
        return "absent"
    try:
        age = now_epoch - os.stat(lock_dir).st_mtime
    except OSError:
        return "held"
    if age < 0:
        age = 0
    pid_path = os.path.join(lock_dir, "pid")
    if not os.path.isfile(pid_path):
        return "held" if age < stale_sec else "stale"
    try:
        with open(pid_path, encoding="utf-8") as handle:
            raw = handle.read().strip()
    except OSError:
        return "held" if age < stale_sec else "stale"
    if not raw.isdigit() or raw == "0":
        return "held" if age < stale_sec else "stale"
    pid = int(raw)
    try:
        alive = bool(pid_alive(pid))
    except OSError:
        alive = False
    if not alive:
        return "stale"
    try:
        wrapper = bool(pid_is_wrapper(pid))
    except OSError:
        wrapper = False
    if wrapper:
        return "held"
    return "held" if age < stale_sec else "stale"


def pid_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    stat_path = "/proc/%s/stat" % pid
    try:
        with open(stat_path, encoding="utf-8") as handle:
            stat = handle.read()
    except OSError:
        return True
    end = stat.rfind(")")
    if end < 0:
        return True
    rest = stat[end + 1:].split()
    if not rest:
        return True
    return rest[0] not in ("Z", "z")


def cmd_is_daily_wrapper(cmd):
    """True when the command is the article wrapper, not a tool that names the file."""
    cmd = (cmd or "").strip()
    if "grokbot-genseo-daily" not in cmd:
        return False
    parts = cmd.split()
    if not parts:
        return False
    token = parts[0].rsplit("/", 1)[-1]
    if token in ("grokbot-genseo-daily", "grokbot-genseo-daily.sh"):
        return True
    if token in ("bash", "sh"):
        return any("grokbot-genseo-daily" in part for part in parts[1:])
    return False


def pid_is_daily_wrapper(pid):
    path = "/proc/%s/cmdline" % pid
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError:
        return False
    cmd = raw.replace(b"\x00", b" ").decode("utf-8", "replace")
    return cmd_is_daily_wrapper(cmd)


def probe_dependencies(env=None, token_path=None, which=None, roster_nonempty=None, qrg_bin=None):
    """Presence checks only. Values of env vars are never copied into the result."""
    env = os.environ if env is None else env
    gaps = []
    warnings = []
    nine_present = bool(env.get("NINE_ROUTER_KEY"))
    if not nine_present:
        gaps.append("NINE_ROUTER_KEY")
    anthropic_set = bool(env.get("ANTHROPIC_API_KEY"))
    if anthropic_set:
        gaps.append("ANTHROPIC_API_KEY-must-stay-unset")
    if token_path is None:
        configured = env.get("GENSEO_CONFIG", "~/.genseo/shopify_token.json")
        token_path = os.path.expanduser(configured)
    token_present = os.path.isfile(token_path)
    if not token_present:
        gaps.append("shopify-token-file")

    def present(name, fallback=None):
        if which is not None:
            return bool(which(name))
        if shutil.which(name):
            return True
        return bool(fallback and os.path.isfile(fallback))

    if not present("claude"):
        gaps.append("claude-cli")
    if not present("ima2"):
        gaps.append("ima2")
    if not present("cwebp"):
        gaps.append("cwebp")
    if not present("gem9", "/Users/kevinkreative/.local/bin/gem9"):
        gaps.append("gem9")
    if roster_nonempty is None:
        roster_nonempty = bool(genseo_roster.NAMES)
    if not roster_nonempty:
        gaps.append("roster-empty")
    if qrg_bin is None:
        qrg_bin = validate_article._claude_seo_bin()
    qrg_present = bool(qrg_bin)
    if not qrg_present:
        warnings.append(
            "claude-seo runtime not installed (%s)" % validate_article.QRG_LAUNCHER_GLOB
        )
    guards_ok = True
    try:
        import brand_rules  # noqa: F401
        import geo_citability  # noqa: F401
    except Exception as exc:  # noqa: BLE001 — report the type, never a credential
        guards_ok = False
        gaps.append("validator-import")
        warnings.append(type(exc).__name__)
    return {
        "gaps": gaps,
        "warnings": warnings,
        "nine_router_key_present": nine_present,
        "anthropic_api_key_set": anthropic_set,
        "shopify_token_file_present": token_present,
        "roster_nonempty": bool(roster_nonempty),
        "qrg_launcher_present": qrg_present,
        "label_guards_loaded": guards_ok,
        "geo_citability_loaded": guards_ok,
        "publish_arm": False,
        "paid_api_called": False,
    }


def _decision(action, reason, exit_code, **details):
    body = {
        "action": action,
        "reason": reason,
        "publish": False,
        "paid_api_called": False,
        "exit_code": exit_code,
    }
    body.update(details)
    return body


def evaluate(snap):
    """Decide stand-down, disabled, or fail-closed. Never returns publish=true.

    snap keys used: enabled, now, cutoff_minutes, target, live_count, feed_error,
    peer_active, repo_done_today, open_tickets, lock, lint_ok, gaps, warnings,
    tickets_error. Missing keys are fail-closed once the flag is on, except
    fields that a stand-down does not need to read.
    """
    if not snap.get("enabled"):
        return _decision("disabled", "flag-off", 0, enabled=False)

    target = snap.get("target")
    if not isinstance(target, int) or isinstance(target, bool) or target < 1:
        return _decision("fail-closed", "bad-target", 2, enabled=True)
    now = snap.get("now")
    cutoff = snap.get("cutoff_minutes")
    if not isinstance(now, dt.datetime) or not isinstance(cutoff, int):
        return _decision("fail-closed", "bad-clock", 2, enabled=True, target=target)

    base = {
        "enabled": True,
        "target": target,
        "now_ict": now.isoformat(),
        "cutoff_ict": "%02d:%02d" % (cutoff // 60, cutoff % 60),
        "lock": snap.get("lock") or "absent",
        "warnings": list(snap.get("warnings") or []),
    }
    feed_error = snap.get("feed_error")
    live = snap.get("live_count")
    if feed_error or not isinstance(live, int) or isinstance(live, bool) or live < 0:
        base.update(live_count=live if isinstance(live, int) and not isinstance(live, bool) else -1,
                    feed_error=redact(feed_error or "feed-unreadable"),
                    would_fill=None)
        return _decision("fail-closed", "feed-unreadable", 2, **base)

    base.update(live_count=live, would_fill=max(0, target - live), feed_error=None)
    if minutes_ict(now) < cutoff:
        return _decision("stand-down", "before-cutoff", 0, **base)
    if live >= target:
        return _decision("stand-down", "feed-at-target", 0, **base)

    peer = snap.get("peer_active")
    if peer is True:
        return _decision("stand-down", "peer-window", 0, peer_active=True, **base)
    if peer is not False:
        return _decision("fail-closed", "peer-unknown", 2, peer_active=None, **base)
    base["peer_active"] = False

    if snap.get("lock") == "held":
        return _decision("stand-down", "lane-lock", 0, **base)

    if snap.get("tickets_error"):
        return _decision(
            "fail-closed", "tickets-unreadable", 2,
            tickets_error=redact(snap.get("tickets_error")), **base
        )
    repo_done = snap.get("repo_done_today")
    open_n = snap.get("open_tickets")
    if (not isinstance(repo_done, int) or isinstance(repo_done, bool)
            or not isinstance(open_n, int) or isinstance(open_n, bool)):
        return _decision("fail-closed", "tickets-unreadable", 2, **base)
    base.update(repo_done_today=repo_done, open_tickets=open_n)
    if repo_done >= target:
        return _decision("stand-down", "repo-record-at-target", 0, **base)
    if open_n <= 0:
        return _decision("stand-down", "queue-empty", 0, **base)

    if snap.get("lint_ok") is not True:
        reason = "ticket-lint" if snap.get("lint_ok") is False else "lint-not-run"
        return _decision("fail-closed", reason, 2, **base)

    gaps = list(snap.get("gaps") or [])
    if "publish-arm-disabled" not in gaps:
        gaps.append("publish-arm-disabled")
    base["gaps"] = gaps
    return _decision("fail-closed", "publish-blocked", 2, **base)


def fetch_count(day, script_path, python):
    try:
        proc = subprocess.run(
            [python, script_path, "--date", day],
            capture_output=True, text=True, timeout=FEED_TIMEOUT_SEC,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"live_count": -1, "feed_error": redact(exc), "peer_active": None}
    lines = [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]
    err = redact(proc.stderr)
    if proc.returncode != 0 or not lines:
        return {"live_count": -1, "feed_error": err or "feed-exit-%s" % proc.returncode,
                "peer_active": None}
    last = lines[-1]
    if last.startswith("-") or not last.isdigit():
        return {"live_count": -1, "feed_error": err or "feed-unreadable", "peer_active": None}
    return {"live_count": int(last), "feed_error": None, "peer_active": None}


def fetch_peer(day, peer_min, local_log, script_path, python):
    try:
        proc = subprocess.run(
            [python, script_path, "--date", day, "--peer-active", str(peer_min),
             "--local-log", local_log],
            capture_output=True, text=True, timeout=FEED_TIMEOUT_SEC,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"peer_active": None, "feed_error": redact(exc), "peer_note": ""}
    note = redact((proc.stdout or "").strip())
    err = redact(proc.stderr)
    if proc.returncode == 3:
        return {"peer_active": True, "feed_error": None, "peer_note": note}
    if proc.returncode == 0:
        return {"peer_active": False, "feed_error": None, "peer_note": note}
    return {"peer_active": None, "feed_error": err or note or "peer-exit-%s" % proc.returncode,
            "peer_note": note}


def read_tickets(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read(), None
    except OSError as exc:
        return None, type(exc).__name__


def run_lint(tickets_path, python=None):
    python = python or sys.executable
    lint = os.path.join(ROOT, "scripts", "lint_tickets.py")
    try:
        proc = subprocess.run(
            [python, lint, tickets_path],
            capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, redact(exc)
    line = ""
    for row in (proc.stdout or "").splitlines():
        if row.startswith("lint_tickets:"):
            line = row.strip()
    return proc.returncode == 0, line or redact(proc.stderr) or "lint-exit-%s" % proc.returncode


def public_probe(probe):
    """Booleans and gap names. No env values."""
    return {
        "gaps": list(probe.get("gaps") or []),
        "warnings": list(probe.get("warnings") or []),
        "nine_router_key_present": bool(probe.get("nine_router_key_present")),
        "anthropic_api_key_set": bool(probe.get("anthropic_api_key_set")),
        "shopify_token_file_present": bool(probe.get("shopify_token_file_present")),
        "roster_nonempty": bool(probe.get("roster_nonempty")),
        "qrg_launcher_present": bool(probe.get("qrg_launcher_present")),
        "label_guards_loaded": bool(probe.get("label_guards_loaded")),
        "geo_citability_loaded": bool(probe.get("geo_citability_loaded")),
        "publish_arm": False,
        "paid_api_called": False,
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description="Decide whether the MacBook article lane already covered today. Does not publish."
    )
    parser.add_argument("--tickets", default=os.path.join(ROOT, "daily-tickets.md"))
    parser.add_argument("--lock-dir", default=os.path.join(ROOT, "state", "daily.lock"))
    parser.add_argument("--local-log", default="")
    return parser


def main(argv=None, env=None, now=None, fetch_count_fn=None, fetch_peer_fn=None,
         read_tickets_fn=None, lint_fn=None, probe_fn=None, lock_fn=None):
    env = os.environ if env is None else env
    args = build_parser().parse_args(argv)
    enabled = flag_enabled(env.get(FLAG, ""))
    if not enabled:
        body = _decision("disabled", "flag-off", 0, enabled=False, runner=socket.gethostname())
        return body

    now = now or dt.datetime.now(ICT)
    if now.tzinfo is None:
        now = now.replace(tzinfo=ICT)
    else:
        now = now.astimezone(ICT)
    day = now.date().isoformat()
    cutoff = parse_cutoff(env.get("GENSEO_CLOUD_CUTOFF_ICT", DEFAULT_CUTOFF))
    target = parse_target(env.get("GENSEO_DAILY_TARGET", str(DEFAULT_TARGET)))
    peer_raw = env.get("GENSEO_PEER_WINDOW_MIN", str(DEFAULT_PEER_MIN))
    if not str(peer_raw).isdigit() or int(peer_raw) < 1:
        peer_min = None
    else:
        peer_min = int(peer_raw)
    header = {"enabled": True, "runner": socket.gethostname(), "day_ict": day}
    if cutoff is None:
        return _decision("fail-closed", "bad-cutoff", 2, **header)
    if target is None:
        return _decision("fail-closed", "bad-target", 2, **header)
    if peer_min is None:
        return _decision("fail-closed", "bad-peer-window", 2, **header)

    script_path = os.path.join(ROOT, "scripts", "genseo_published_today.py")
    python = env.get("GENSEO_PYTHON", sys.executable)
    fetch_count_fn = fetch_count_fn or (
        lambda: fetch_count(day, script_path, python)
    )
    feed = fetch_count_fn()
    past_cutoff = isinstance(cutoff, int) and minutes_ict(now) >= cutoff
    live = feed.get("live_count")
    need_peer = (
        past_cutoff and not feed.get("feed_error")
        and isinstance(live, int) and not isinstance(live, bool) and 0 <= live
        and isinstance(target, int) and live < target and peer_min is not None
    )
    if need_peer:
        local_log = args.local_log or os.path.join(
            ROOT, "state", "published-by-%s.log" % socket.gethostname().split(".")[0]
        )
        fetch_peer_fn = fetch_peer_fn or (
            lambda: fetch_peer(day, peer_min, local_log, script_path, python)
        )
        peer = fetch_peer_fn()
        if peer.get("feed_error"):
            feed["feed_error"] = peer["feed_error"]
            feed["live_count"] = -1
        feed["peer_active"] = peer.get("peer_active")
        feed["peer_note"] = peer.get("peer_note") or ""

    tickets_error = None
    repo_done = None
    open_n = None
    text = None
    if read_tickets_fn is None:
        text, tickets_error = read_tickets(args.tickets)
    else:
        text, tickets_error = read_tickets_fn()
    if text is not None and not tickets_error:
        repo_done, open_n = count_repo_record(text, day)

    lock_fn = lock_fn or (
        lambda: classify_lock(
            args.lock_dir, int(now.timestamp()), LOCK_STALE_SEC, pid_alive, pid_is_daily_wrapper
        )
    )
    try:
        lock_state = lock_fn()
    except OSError:
        lock_state = "held"

    probe_fn = probe_fn or (lambda: probe_dependencies(env=env))
    probe = public_probe(probe_fn())

    snap = {
        "enabled": True,
        "now": now,
        "cutoff_minutes": cutoff,
        "target": target,
        "live_count": feed.get("live_count"),
        "feed_error": feed.get("feed_error"),
        "peer_active": feed.get("peer_active"),
        "repo_done_today": repo_done,
        "open_tickets": open_n,
        "tickets_error": tickets_error,
        "lock": lock_state,
        "lint_ok": None,
        "gaps": list(probe["gaps"]),
        "warnings": list(probe["warnings"]),
    }
    peek = evaluate(dict(snap, lint_ok=True, gaps=[]))
    if peek["reason"] == "publish-blocked":
        lint_fn = lint_fn or (lambda: run_lint(args.tickets, python))
        lint_ok, lint_line = lint_fn()
        snap["lint_ok"] = bool(lint_ok)
        snap["lint_line"] = lint_line
    body = evaluate(snap)
    body["runner"] = socket.gethostname()
    body["day_ict"] = day
    body["dependencies"] = probe
    body["publish"] = False
    body["paid_api_called"] = False
    if feed.get("peer_note"):
        body["peer_note"] = feed["peer_note"]
    if snap.get("lint_line"):
        body["lint_line"] = redact(snap["lint_line"])
    return body


def emit(body):
    text = json.dumps(body, indent=1, sort_keys=True)
    sys.stdout.write(text + "\n")
    sys.stderr.write(
        "genseo-cloud-failover: %s %s publish=false\n" % (body.get("action"), body.get("reason"))
    )


if __name__ == "__main__":
    decision = main()
    emit(decision)
    sys.exit(int(decision.get("exit_code") or 0))

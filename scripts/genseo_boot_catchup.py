#!/usr/bin/env python3
"""Opt-in boot/login catch-up for a GenSeo morning slot missed while powered off.

launchd coalesces StartCalendarInterval fires that pass during sleep. It does
not replay a slot that passed while the Mac was powered off (man launchd.plist).
On 2026-10-19 the MacBook was off until 08:09 ICT, so 07:30 and 08:05 never
fired. RunAtLoad on com.pati.genseo-daily or com.pati.genseo-landing is the
wrong fix: scripts/genseo_self_apply.sh refuses a plist whose RunAtLoad is not
false, because bootstrap would start that job, and a load-time start would
also run before the first slot and on every login.

This program is a separate agent, com.pati.genseo-catchup. RunAtLoad is true
and there is no calendar. Self-apply does not install it. On each load it
decides, per lane, whether to start that lane's existing command. Those
commands already begin with caffeinate -i -s. This agent is started under
caffeinate as well and waits until any lane it started has exited. It does
not call launchctl, does not pass --live, and does not publish.

Install (runs the decision once, because RunAtLoad is true):

  cp ~/genseo/deploy/com.pati.genseo-catchup.plist ~/Library/LaunchAgents/com.pati.genseo-catchup.plist && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-catchup.plist

Uninstall:

  launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-catchup.plist; rm -f ~/Library/LaunchAgents/com.pati.genseo-catchup.plist

bootout fails if the label is not loaded. If it is already loaded, bootout
that plist path before bootstrap. Offline: bash tests/test_boot_catchup.sh
"""
import errno
import json
import os
import plistlib
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ICT = timezone(timedelta(hours=7))
ARTICLE_SLOTS = ((7, 30), (8, 5), (14, 47))
LANDING_SLOTS = ((8, 15), (9, 20), (16, 15))
DEFER_MINUTES = 15
ARTICLE_LOCK_STALE_SEC = 21600
LANDING_LOCK_STALE_SEC = 14400
LANES = ("article", "landing")
LANE_LABEL = {
    "article": "com.pati.genseo-daily",
    "landing": "com.pati.genseo-landing",
}
LANE_PLIST = {
    "article": "com.pati.genseo-daily.macbook.plist",
    "landing": "com.pati.genseo-landing.macbook.plist",
}
LANE_INSTALLED = {
    "article": "com.pati.genseo-daily.plist",
    "landing": "com.pati.genseo-landing.plist",
}
FORBIDDEN = ("--live", "shopify_publisher", "kickstart", "launchctl")
DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
INSTALL_COMMAND = (
    "cp ~/genseo/deploy/com.pati.genseo-catchup.plist "
    "~/Library/LaunchAgents/com.pati.genseo-catchup.plist && "
    "launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-catchup.plist"
)
UNINSTALL_COMMAND = (
    "launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.pati.genseo-catchup.plist; "
    "rm -f ~/Library/LaunchAgents/com.pati.genseo-catchup.plist"
)


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def slot_minutes(slot):
    hour, minute = slot
    return hour * 60 + minute


def format_hhmm(minutes):
    return "%02d:%02d" % (minutes // 60, minutes % 60)


def parse_hhmm(text):
    parts = text.split(":")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise ValueError("clock must be HH:MM")
    hour, minute = int(parts[0]), int(parts[1])
    if hour > 23 or minute > 59:
        raise ValueError("clock must be HH:MM")
    return hour * 60 + minute


def decide_lane(now_minutes, slots, done, locked, already_fired, readable=True, defer_minutes=DEFER_MINUTES):
    """Return (action, reason). action is 'start' or 'skip'.

    unreadable, already-done, and in-progress exit before a clock check.
    before-first-slot leaves the upcoming fire to launchd. after-last-slot
    is the quiet period from that lane's last calendar minute through the
    next morning: a batch started then can still be running at 07:30.
    next-slot-soon (this slot's minute, or within defer_minutes of the next)
    also belongs to launchd. missed-morning-slot is the gap after a slot
    has passed when the next one is not soon and the last one is still ahead.
    """
    if not readable:
        return "skip", "unreadable"
    if done:
        return "skip", "already-done"
    if locked:
        return "skip", "in-progress"
    if already_fired:
        return "skip", "already-fired"
    if not isinstance(now_minutes, int) or now_minutes < 0 or now_minutes >= 24 * 60:
        return "skip", "clock-invalid"
    times = sorted(slot_minutes(slot) for slot in slots)
    if not times:
        return "skip", "after-last-slot"
    first, last = times[0], times[-1]
    if now_minutes < first:
        return "skip", "before-first-slot"
    if now_minutes >= last:
        return "skip", "after-last-slot"
    upcoming = [item for item in times if item >= now_minutes]
    if not upcoming or upcoming[0] - now_minutes <= defer_minutes:
        return "skip", "next-slot-soon"
    return "start", "missed-morning-slot"


def pid_alive(pid):
    try:
        os.kill(pid, 0)
    except OSError as exc:
        # EPERM means the pid exists and is owned by someone else. kill -0
        # treats that as alive; ESRCH is the dead case.
        return exc.errno == errno.EPERM
    return True


def read_pid_file(directory):
    path = os.path.join(directory, "pid")
    try:
        with open(path, "r") as handle:
            text = handle.read().strip()
    except OSError:
        return None
    if text.isdigit() and int(text) > 0:
        return int(text)
    return None


def _age_seconds(path, now):
    return now - os.stat(path).st_mtime


def article_lock_held(path, now, alive=None, stale_sec=ARTICLE_LOCK_STALE_SEC):
    """True when the article wrapper would refuse this lock.

    A dead PID is not held: the wrapper takes that lock immediately. A missing
    PID is held until the directory is older than the stale window, matching
    scripts/genseo_daily_lock.sh. A path that exists and is not a directory
    is held so this program does not start a second batch against it.
    """
    if alive is None:
        alive = pid_alive
    if os.path.lexists(path) and not os.path.isdir(path):
        return True
    if not os.path.isdir(path):
        return False
    pid = read_pid_file(path)
    if pid is not None:
        return alive(pid)
    try:
        age = _age_seconds(path, now)
    except OSError:
        return True
    return age <= stale_sec


def landing_lock_held(path, now, stale_sec=LANDING_LOCK_STALE_SEC):
    """True when run_landing_daily.sh would exit 0 on this lock directory.

    The landing wrapper steals the directory only after 4 hours. It does not
    read the owner pid before that. A non-directory at the lock path is held.
    """
    if os.path.lexists(path) and not os.path.isdir(path):
        return True
    if not os.path.isdir(path):
        return False
    try:
        age = _age_seconds(path, now)
    except OSError:
        return True
    return age <= stale_sec


def stamp_path(state_dir, day, lane):
    return os.path.join(state_dir, "%s-%s.started" % (day, lane))


def claim_stamp(path, body):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(path, flags, 0o644)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            return "exists"
        return "error"
    try:
        os.write(fd, body.encode("utf-8"))
    finally:
        os.close(fd)
    return "claimed"


def release_stamp(path):
    try:
        os.remove(path)
    except OSError:
        return


def guard_live(env):
    if env.get("GENSEO_CATCHUP_TEST") == "1":
        raise RuntimeError("live probe refused in test mode")


def python_bin():
    if os.path.isfile("/usr/bin/python3") and os.access("/usr/bin/python3", os.X_OK):
        return "/usr/bin/python3"
    return sys.executable


def read_article_count(repo, env):
    guard_live(env)
    script = os.path.join(repo, "scripts", "genseo_published_today.py")
    try:
        proc = subprocess.run(
            [python_bin(), script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=45,
            cwd=repo,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    lines = proc.stdout.decode("utf-8", "replace").strip().splitlines()
    if proc.returncode != 0 or not lines:
        return None
    last = lines[-1].strip()
    if last.isdigit():
        return int(last)
    return None


def read_landing_done(repo, env):
    """True when today's gsl- page exists, False when the slot is free, None if unreadable."""
    guard_live(env)
    script = os.path.join(repo, "scripts", "landing_guard.py")
    try:
        proc = subprocess.run(
            [python_bin(), script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=45,
            cwd=repo,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode == 3:
        return True
    if proc.returncode == 0:
        return False
    return None


def genseo_home(env):
    home = env.get("HOME", "")
    if not home:
        raise ValueError("HOME is unset")
    return os.path.join(home, "genseo")


def live_facts(lane, env, repo, now_epoch):
    guard_live(env)
    root = genseo_home(env)
    if lane == "article":
        lock = article_lock_held(os.path.join(root, "state", "daily.lock"), now_epoch)
        count = read_article_count(repo, env)
        if count is None:
            return {"done": False, "locked": lock, "readable": False}
        target = 5
        spec = load_plist(plist_for_lane(lane, env, repo, live=True))
        if spec is not None:
            raw = spec["plist_env"].get("GENSEO_DAILY_TARGET", "5")
            if raw.isdigit():
                target = int(raw)
        return {"done": count >= target, "locked": lock, "readable": True}
    lock = landing_lock_held(os.path.join(root, "state", "landing-daily.lock"), now_epoch)
    done = read_landing_done(repo, env)
    if done is None:
        return {"done": False, "locked": lock, "readable": False}
    return {"done": done, "locked": lock, "readable": True}


def test_flag(env, name, default=None):
    if name not in env or env[name] == "":
        if default is None:
            raise ValueError("missing %s" % name)
        return default
    if env[name] not in ("0", "1"):
        raise ValueError("%s must be 0 or 1" % name)
    return env[name] == "1"


def test_facts(lane, env, state_dir, day):
    prefix = "GENSEO_CATCHUP_ARTICLE_" if lane == "article" else "GENSEO_CATCHUP_LANDING_"
    fired = test_flag(env, prefix + "FIRED", False) or os.path.exists(stamp_path(state_dir, day, lane))
    return {
        "done": test_flag(env, prefix + "DONE"),
        "locked": test_flag(env, prefix + "LOCKED"),
        "readable": test_flag(env, prefix + "READABLE", True),
        "already_fired": fired,
    }


def clock_of(env, test):
    if not test:
        now = datetime.now(ICT)
        return now.date().isoformat(), now.hour * 60 + now.minute
    day = env.get("GENSEO_CATCHUP_DAY", "")
    if not DAY_RE.match(day):
        raise ValueError("GENSEO_CATCHUP_DAY must be YYYY-MM-DD")
    if "GENSEO_CATCHUP_NOW" not in env:
        raise ValueError("missing GENSEO_CATCHUP_NOW")
    return day, parse_hhmm(env["GENSEO_CATCHUP_NOW"])


def state_dir_of(env, test):
    if test:
        path = env.get("GENSEO_CATCHUP_STATE_DIR", "")
        if not path:
            raise ValueError("missing GENSEO_CATCHUP_STATE_DIR")
        return path
    override = env.get("GENSEO_CATCHUP_STATE_DIR", "")
    if override:
        return override
    return os.path.join(genseo_home(env), "state", "catchup")


def plist_for_lane(lane, env, repo, live):
    if not live:
        override = env.get("GENSEO_CATCHUP_ARTICLE_PLIST" if lane == "article" else "GENSEO_CATCHUP_LANDING_PLIST", "")
        if override:
            return override
        return os.path.join(repo, "deploy", LANE_PLIST[lane])
    home = env.get("HOME", "")
    installed = os.path.join(home, "Library", "LaunchAgents", LANE_INSTALLED[lane])
    if os.path.isfile(installed) and not os.path.islink(installed):
        return installed
    return os.path.join(repo, "deploy", LANE_PLIST[lane])


def with_caffeinate(argv):
    if argv and os.path.basename(argv[0]) == "caffeinate":
        return list(argv)
    return ["/usr/bin/caffeinate", "-i", "-s"] + list(argv)


def load_plist(path):
    try:
        with open(path, "rb") as handle:
            data = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException, ValueError):
        return None
    argv = data.get("ProgramArguments")
    if not isinstance(argv, list) or not argv:
        return None
    raw_env = data.get("EnvironmentVariables") or {}
    if not isinstance(raw_env, dict):
        return None
    return {
        "argv": with_caffeinate([str(item) for item in argv]),
        "plist_env": {str(key): str(value) for key, value in raw_env.items()},
        "label": data.get("Label"),
        "path": path,
    }


def forbidden(argv):
    blob = " ".join(argv)
    return any(token in blob for token in FORBIDDEN)


def child_environment(parent, plist_env):
    child = dict(parent)
    for key in list(child):
        if key.startswith("GENSEO_CATCHUP_"):
            del child[key]
    child.update(plist_env)
    return child


def public_env(env):
    out = {}
    for key in sorted(env):
        if not key.startswith("GENSEO_"):
            continue
        if any(word in key for word in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
            continue
        out[key] = env[key]
    return out


def format_line(day, now_minutes, lane, action, reason, argv):
    line = "catchup %s %s ICT %s %s %s" % (day, format_hhmm(now_minutes), lane, action, reason)
    if argv:
        line += " " + " ".join(argv)
    return line


def command_for(lane, env, repo, live):
    spec = load_plist(plist_for_lane(lane, env, repo, live))
    if spec is None:
        return None, "plist-unreadable"
    if spec["label"] != LANE_LABEL[lane]:
        return None, "label-mismatch"
    if forbidden(spec["argv"]):
        return None, "command-refused"
    spec["env"] = child_environment(env, spec["plist_env"])
    return spec, ""


def evaluate_lane(lane, slots, env, repo, state_dir, day, now_minutes, test, now_epoch):
    if test:
        facts = test_facts(lane, env, state_dir, day)
    else:
        facts = live_facts(lane, env, repo, now_epoch)
        facts["already_fired"] = os.path.exists(stamp_path(state_dir, day, lane))
    action, reason = decide_lane(
        now_minutes,
        slots,
        facts["done"],
        facts["locked"],
        facts["already_fired"],
        facts["readable"],
    )
    spec = None
    if action != "start":
        return action, reason, spec
    spec, problem = command_for(lane, env, repo, live=not test)
    if problem:
        return "skip", problem, None
    body = "reason=%s\nnow=%s\nday=%s\nlane=%s\n" % (reason, format_hhmm(now_minutes), day, lane)
    claimed = claim_stamp(stamp_path(state_dir, day, lane), body)
    if claimed == "exists":
        return "skip", "already-fired", None
    if claimed != "claimed":
        return "skip", "stamp-unwritable", None
    return "start", reason, spec


def record_launch(state_dir, lane, spec):
    path = os.path.join(state_dir, "launched.jsonl")
    row = {"lane": lane, "argv": spec["argv"], "env": public_env(spec["env"])}
    with open(path, "a") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def spawn_lanes(jobs, repo):
    procs = []
    for lane, spec, stamp in jobs:
        try:
            proc = subprocess.Popen(spec["argv"], env=spec["env"], cwd=repo)
        except OSError:
            release_stamp(stamp)
            procs.append((lane, None))
            continue
        procs.append((lane, proc))
    rc = 0
    codes = []
    for lane, proc in procs:
        if proc is None:
            codes.append((lane, 127))
            if rc == 0:
                rc = 127
            continue
        code = proc.wait()
        codes.append((lane, code))
        if code != 0 and rc == 0:
            rc = code
    return rc, codes


def run(env):
    test = env.get("GENSEO_CATCHUP_TEST") == "1"
    repo = repo_root()
    day, now_minutes = clock_of(env, test)
    state_dir = state_dir_of(env, test)
    os.makedirs(state_dir, exist_ok=True)
    now_epoch = datetime.now(ICT).timestamp()
    lines = []
    jobs = []
    slots_for = {"article": ARTICLE_SLOTS, "landing": LANDING_SLOTS}
    for lane in LANES:
        action, reason, spec = evaluate_lane(
            lane, slots_for[lane], env, repo, state_dir, day, now_minutes, test, now_epoch
        )
        argv = spec["argv"] if spec is not None else None
        lines.append(format_line(day, now_minutes, lane, action, reason, argv))
        if action == "start" and spec is not None:
            if test:
                record_launch(state_dir, lane, spec)
            else:
                jobs.append((lane, spec, stamp_path(state_dir, day, lane)))
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    log_path = os.path.join(state_dir, "catchup.log")
    try:
        with open(log_path, "a") as handle:
            handle.write(text)
    except OSError:
        pass
    if test or not jobs:
        return 0
    rc, codes = spawn_lanes(jobs, repo)
    for lane, code in codes:
        sys.stdout.write("catchup %s %s ICT %s exit %s\n" % (day, format_hhmm(now_minutes), lane, code))
    return rc


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--print-install" in argv:
        sys.stdout.write(INSTALL_COMMAND + "\n")
        return 0
    if "--print-uninstall" in argv:
        sys.stdout.write(UNINSTALL_COMMAND + "\n")
        return 0
    if argv:
        sys.stderr.write("usage: genseo_boot_catchup.py [--print-install|--print-uninstall]\n")
        return 2
    try:
        return run(os.environ)
    except ValueError as exc:
        sys.stderr.write("catchup: %s\n" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())

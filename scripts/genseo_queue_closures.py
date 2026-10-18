#!/usr/bin/env python3
"""Remember tickets closed on a day-run branch so a return to origin/main does not reopen them.

daily-tickets.md and daily-landing-tickets.md on origin/main stay the open
queue. A publish that landed on article/* or publish/* flips those lines only
in that branch. Checking main back out would put the same tickets first in
the batch; three duplicate skips then stop the day.

state/queue-closures.json is gitignored per-Mac state. The daily open-count
and the QUEUE POINTER skip entries in it. The branch ref keeps the commits.

    genseo_queue_closures.py count --queue daily-tickets.md
    genseo_queue_closures.py first --queue daily-tickets.md
    genseo_queue_closures.py record --repo . --base origin/main [--head HEAD] [--dry-run]

count and first print the effective open queue. A missing ledger is an empty
ledger. A ledger that cannot be read exits 2 so callers fail closed.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

LEDGER_NAME = os.path.join("state", "queue-closures.json")
QUEUES = ("daily-tickets.md", "daily-landing-tickets.md")
ICT = dt.timezone(dt.timedelta(hours=7))
CHECK = re.compile(r"^(?:- |## )\[([^\]]*)\](.*)$")
TICKET_ID = re.compile(r"#([A-Z]{1,4}\d{4}-\d+)\b")
WS = re.compile(r"\s+")


def norm_ws(text):
    return WS.sub(" ", text).strip()


def checkbox_lines(text):
    if not text:
        return []
    out = []
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        matched = CHECK.match(line)
        if not matched:
            continue
        inner = matched.group(1)
        body = norm_ws(matched.group(2))
        ids = TICKET_ID.findall(line)
        out.append({
            "open": inner == " ",
            "inner": inner.strip(),
            "body": body,
            "ticket_id": ids[0] if ids else "",
            "line": line,
        })
    return out


def closures_between(head_text, base_text, queue):
    """Closed lines on head whose open counterpart is still open on base."""
    by_id = {}
    by_body = {}
    for row in checkbox_lines(base_text):
        if not row["open"]:
            continue
        if row["ticket_id"]:
            by_id.setdefault(row["ticket_id"], row)
        if row["body"]:
            by_body.setdefault(row["body"], row)
    found = []
    seen = set()
    for row in checkbox_lines(head_text):
        if row["open"]:
            continue
        if row["ticket_id"] and row["ticket_id"] in by_id:
            key = "id:" + row["ticket_id"]
            ticket_id = row["ticket_id"]
            body = ""
        elif not row["ticket_id"] and row["body"] and row["body"] in by_body:
            key = "body:" + row["body"]
            ticket_id = ""
            body = row["body"]
        else:
            continue
        if key in seen:
            continue
        seen.add(key)
        found.append({
            "queue": queue,
            "key": key,
            "ticket_id": ticket_id,
            "body": body,
            "status": row["inner"][:300],
        })
    return found


def ledger_path(repo):
    return os.path.join(os.path.abspath(repo), LEDGER_NAME)


def load_ledger(path):
    if not os.path.isfile(path):
        return {"version": 1, "entries": []}
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("unreadable queue ledger %s (%s)" % (path, exc))
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("entries"), list):
        raise ValueError("queue ledger %s is not version 1" % path)
    return data


def save_ledger(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
        fh.write("\n")
    os.replace(tmp, path)


def merge_entries(existing, new_rows, recorded_at, branch, head_sha, base_sha):
    order = []
    index = {}
    for entry in existing:
        if not isinstance(entry, dict):
            continue
        key = (entry.get("queue"), entry.get("key"))
        if key in index or not key[0] or not key[1]:
            continue
        index[key] = entry
        order.append(key)
    for row in new_rows:
        entry = {
            "queue": row["queue"],
            "key": row["key"],
            "ticket_id": row["ticket_id"],
            "body": row["body"],
            "status": row["status"],
            "branch": branch,
            "head": head_sha,
            "base": base_sha,
            "recorded_at": recorded_at,
        }
        key = (entry["queue"], entry["key"])
        if key not in index:
            order.append(key)
        index[key] = entry
    return [index[key] for key in order]


def hidden(row, entries, queue):
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("queue") != queue:
            continue
        if entry.get("ticket_id") and row["ticket_id"] == entry["ticket_id"]:
            return True
        if not entry.get("ticket_id") and entry.get("body") and row["body"] == entry["body"]:
            return True
    return False


def effective_open_lines(text, entries, queue):
    out = []
    for row in checkbox_lines(text):
        if row["open"] and not hidden(row, entries, queue):
            out.append(row["line"])
    return out


def repo_of(queue, repo_arg):
    if repo_arg:
        return os.path.abspath(repo_arg)
    return os.path.dirname(os.path.abspath(queue))


def queue_basename(queue):
    return os.path.basename(os.path.abspath(queue))


def read_queue(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def git_env():
    env = os.environ.copy()
    for key in (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
        "GIT_COMMON_DIR", "GIT_NAMESPACE",
    ):
        env.pop(key, None)
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def git_bytes(repo, rev, rel):
    proc = subprocess.run(
        ["git", "-C", repo, "show", "%s:%s" % (rev, rel)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=git_env(),
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "replace")


def git_one(repo, *args):
    proc = subprocess.run(
        ["git", "-C", repo, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=git_env(),
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "replace").strip()


def cmd_count(queue, repo_arg):
    repo = repo_of(queue, repo_arg)
    data = load_ledger(ledger_path(repo))
    lines = effective_open_lines(read_queue(queue), data["entries"], queue_basename(queue))
    print(len(lines))
    return 0


def cmd_first(queue, repo_arg):
    repo = repo_of(queue, repo_arg)
    data = load_ledger(ledger_path(repo))
    lines = effective_open_lines(read_queue(queue), data["entries"], queue_basename(queue))
    if lines:
        print(lines[0])
    return 0


def cmd_record(repo, base, head, dry_run):
    repo = os.path.abspath(repo)
    if git_one(repo, "rev-parse", "--verify", "--quiet", base) is None:
        print("queue closures: base ref missing (%s)" % base, file=sys.stderr)
        return 1
    if git_one(repo, "rev-parse", "--verify", "--quiet", head) is None:
        print("queue closures: head ref missing (%s)" % head, file=sys.stderr)
        return 1
    branch = git_one(repo, "rev-parse", "--abbrev-ref", head) or head
    head_sha = git_one(repo, "rev-parse", head) or ""
    base_sha = git_one(repo, "rev-parse", base) or ""
    found = []
    for rel in QUEUES:
        head_text = git_bytes(repo, head, rel)
        base_text = git_bytes(repo, base, rel)
        if head_text is None and base_text is None:
            continue
        found.extend(closures_between(head_text, base_text, rel))
    path = ledger_path(repo)
    if dry_run:
        print("would record: %d queue closure(s) against %s" % (len(found), base))
        return 0
    try:
        data = load_ledger(path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    now = dt.datetime.now(ICT).isoformat(timespec="seconds")
    data["entries"] = merge_entries(data["entries"], found, now, branch, head_sha, base_sha)
    data["version"] = 1
    if found or os.path.isfile(path):
        save_ledger(path, data)
    print("recorded: %d queue closure(s) against %s" % (len(found), base))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Per-Mac ledger of tickets closed off main")
    sub = parser.add_subparsers(dest="cmd")
    count = sub.add_parser("count")
    count.add_argument("--queue", required=True)
    count.add_argument("--repo", default="")
    first = sub.add_parser("first")
    first.add_argument("--queue", required=True)
    first.add_argument("--repo", default="")
    record = sub.add_parser("record")
    record.add_argument("--repo", required=True)
    record.add_argument("--base", required=True)
    record.add_argument("--head", default="HEAD")
    record.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.cmd == "count":
        try:
            return cmd_count(args.queue, args.repo)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        except OSError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if args.cmd == "first":
        try:
            return cmd_first(args.queue, args.repo)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        except OSError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if args.cmd == "record":
        return cmd_record(args.repo, args.base, args.head, args.dry_run)
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

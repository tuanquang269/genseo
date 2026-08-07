#!/usr/bin/env python3
"""Keep a ticket queue file lean: move every DONE/SKIP ticket out to a sibling
`<stem>-archive.md`, leaving the active file with the header + structure + only PENDING tickets.

Model: everything before the first `##`/`###` heading is the HEADER (kept). The rest is a
sequence of chunks, each starting at a heading and running to the next heading:
  - a chunk whose heading is a real ticket (`... Ticket <id-with-a-digit>`) is a TICKET —
    moved to the archive if DONE/SKIP, kept if pending;
  - any other heading (rules, `## 🌅 Day N` dividers, `## After the cluster`) is STRUCTURAL —
    kept in place, UNLESS it has no body left (a bare divider), in which case it's dropped.

Ticket ids may be numeric (`#4`, `23`) or letter-prefixed (`B1`) — both match. Status is read
from the heading (`[DONE...]`/`[SKIP...]`) OR a `- **Action**: [DONE...]` line in the body.

Idempotent. Usage: archive_done_tickets.py <file.md> [--apply]   (dry-run without --apply)
"""
import re, sys, os

HEAD_RE = re.compile(r'^#{2,3}\s')
# a real ticket heading: "Ticket" then optional #, optional letter, then a DIGIT
# (so "Ticket #4", "Ticket 23", "Ticket B1" match; "...every ticket)" does not — no digit)
TICKET_RE = re.compile(r'^#{2,3}\s.*\bTicket\s*#?[A-Za-z]?\d', re.I)
DONE_RE = re.compile(r'\[(?:DONE|SKIP)', re.I)


def is_ticket(chunk):
    return bool(TICKET_RE.match(chunk.splitlines()[0]))


def is_done(chunk):
    head = chunk.splitlines()[0]
    if DONE_RE.search(head):
        return True
    m = re.search(r'^-\s*\*\*Action\*\*:\s*(\[[^\]]*\])', chunk, re.M)
    return bool(m and DONE_RE.search(m.group(1)))


def empty_structural(chunk):
    """A structural chunk with no real body (just the heading + blank/`---` lines)."""
    body = ''.join(chunk.splitlines(keepends=True)[1:])
    return re.fullmatch(r'[\s\-—]*', body) is not None


def main():
    path = sys.argv[1]
    apply = '--apply' in sys.argv
    lines = open(path).read().splitlines(keepends=True)

    first = next((i for i, l in enumerate(lines) if HEAD_RE.match(l)), len(lines))
    header = ''.join(lines[:first])

    # segment the rest at every heading
    chunks, cur = [], []
    for l in lines[first:]:
        if HEAD_RE.match(l):
            if cur:
                chunks.append(''.join(cur))
            cur = [l]
        else:
            cur.append(l)
    if cur:
        chunks.append(''.join(cur))

    active, move = [], []
    for c in chunks:
        if is_ticket(c):
            (move if is_done(c) else active).append(c)
        elif not empty_structural(c):        # keep non-empty structure; drop bare dividers
            active.append(c)

    pending = sum(1 for c in active if is_ticket(c))

    if not apply:
        print(f"dry-run {os.path.basename(path)}: {len(move)} DONE/SKIP would archive, {pending} pending stay")
        return

    stem = path[:-3] if path.endswith('.md') else path
    arch = f"{stem}-archive.md"
    if move:
        head_note = '' if os.path.exists(arch) else f"# Archive — completed tickets from {os.path.basename(path)}\n\n"
        with open(arch, 'a') as f:
            f.write(head_note + ''.join(move))
    with open(path, 'w') as f:
        f.write(header + ''.join(active))
    print(f"✓ {os.path.basename(path)}: archived {len(move)}, kept {pending} pending"
          + (f" → {os.path.basename(arch)}" if move else ""))


if __name__ == '__main__':
    main()

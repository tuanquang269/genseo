"""Disk paths for images named in a blog draft.

`validate_article.py --draft` keeps an absolute src as written and joins every
other non-remote src to the draft file's directory. The committed
`published_drafts/nmn-and-coffee-us-2026.md` uses that relative form:

    assets/nmn-and-coffee-us-2026/hero.webp

`shopify_publisher.py` opens that same relative form once it knows which draft
file it is publishing. The join is the draft's directory, so a worktree does
not need the bytes to also sit in another checkout.

The joined path is then realpath-checked. `../`, a symlink, or an absolute
token that resolves outside the draft directory is refused before `open()`.
`/Users` and `/private` absolutes are returned unchanged only when the caller
has no draft file.
"""
import os
import re

_REMOTE = re.compile(r"(?i)https?://|data:")


class DraftImagePathError(ValueError):
    """Image token resolves outside the draft file's directory.

    Fail closed: callers must not open the path. The publisher aborts before
    upload.
    """


def _draft_root(draft_path):
    return os.path.realpath(os.path.dirname(os.path.abspath(draft_path)))


def _require_inside(token, candidate, draft_path):
    """Return `candidate` only when its realpath is strictly inside the draft folder."""
    root = _draft_root(draft_path)
    try:
        resolved = os.path.realpath(candidate)
    except OSError as exc:
        raise DraftImagePathError(
            f"refusing image path {token!r}: cannot resolve {candidate!r} ({exc})"
        ) from exc
    try:
        inside = os.path.commonpath([root, resolved]) == root
    except ValueError:
        inside = False
    # commonpath is not a string prefix: draft-evil must not match draft.
    # The draft directory itself is not an image file inside the tree.
    if not inside or resolved == root:
        raise DraftImagePathError(
            f"refusing image path {token!r}: resolves to {resolved!r}, "
            f"outside the draft folder {root!r}"
        )
    return candidate


def disk_path(token, draft_path=None):
    """Path `open()` can use for a markdown image token, or None.

    `token` is the exact string inside `![alt](token)`. Relative results use
    the same join as `validate_article.py --draft`, then a realpath jail.
    Anything that resolves outside the draft file's directory raises
    DraftImagePathError. Remote URLs, `/blogs/` and `/cdn/` phantoms are not
    publisher-local files.
    """
    if not token or _REMOTE.match(token):
        return None
    if token.startswith("/blogs/") or token.startswith("/cdn/"):
        return None
    if os.path.isabs(token):
        if not draft_path:
            if token.startswith("/Users") or token.startswith("/private"):
                return token
            return None
        return _require_inside(token, token, draft_path)
    if not draft_path:
        return None
    base = os.path.dirname(os.path.abspath(draft_path))
    joined = os.path.join(base, token)
    # join() drops `base` when `token` is absolute. isabs() above already
    # handled that. The realpath check still refuses a relative token whose
    # `..` or symlink leaves the draft folder.
    return _require_inside(token, joined, draft_path)

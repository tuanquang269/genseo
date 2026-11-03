"""Disk paths for images named in a blog draft.

`validate_article.py --draft` keeps an absolute src as written and joins every
other non-remote src to the draft file's directory. The committed
`published_drafts/nmn-and-coffee-us-2026.md` uses that relative form:

    assets/nmn-and-coffee-us-2026/hero.webp

`shopify_publisher.py` uploads `/Users` and `/private` absolutes, plus this
same relative form once it knows which draft file it is publishing. The join
is the draft's directory, so a worktree does not need the bytes to also sit
in another checkout.
"""
import os
import re

_REMOTE = re.compile(r"(?i)https?://|data:")


def disk_path(token, draft_path=None):
    """Path `open()` can use for a markdown image token, or None.

    `token` is the exact string inside `![alt](token)`. Relative results use
    the same join as `validate_article.py --draft`. Remote URLs, `/blogs/` and
    `/cdn/` phantoms, and any other absolute path are not publisher-local files.
    """
    if not token or _REMOTE.match(token):
        return None
    if os.path.isabs(token):
        if token.startswith("/Users") or token.startswith("/private"):
            return token
        return None
    if not draft_path:
        return None
    base = os.path.dirname(os.path.abspath(draft_path))
    return os.path.join(base, token)

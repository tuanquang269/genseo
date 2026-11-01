"""Author roster — the SINGLE source of truth for every byline the pipeline may use.

Edit roster.json at the repo root of THIS checkout. Do NOT re-introduce per-script
ROSTER dicts; validate_article.py, shopify_publisher.py, repair_schema.py and
fix_untitled.py all import this module.

roster.json format (handles starting with "_" are ignored):

    {
      "jane-doe": {
        "name": "Jane Doe",
        "bio": "Jane Doe is ... (EXACT approved sentence; the gate matches its first 60 chars)",
        "role": "optional",
        "page": "/pages/jane-doe",
        "headshot": null,
        "default_for": ["blog"]
      }
    }

`name` and `bio` are required. `role`, `page`, `headshot`, and `default_for` are
optional. `page`, when set, must be `/pages/<handle>`. `headshot` is a real image
path or null. Null is a placeholder: do not invent a photo.

Rules (enforced by validate_article.py):
  * bios must be the approved sentence verbatim — no invented credentials
    (no Dr./MD/PhD/RD/CISSN unless that approved sentence already contains it)
  * the publish gate still requires a LIVE page at
    https://wellnessnest.co/pages/<handle> (HTTP 200). Adding a roster entry
    does not create that page.
  * empty roster = publishing is blocked, by design
  * blog drafts use blog_default() (Kevin 2026-10-21: Mike Moretti).
    A Dr. Marcus Hale blog byline fails validate_article.py.
    Landing pages use landing_default() (Dr. Marcus Hale).
"""
import os

_MAC_ROSTER = "/Users/kevinkreative/genseo/roster.json"
_REPO_ROSTER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "roster.json")

# Blog default (Kevin 2026-10-21). These do not depend on the Mac roster file.
DEFAULT_BLOG_HANDLE = "mike-moretti"
DEFAULT_BLOG_NAME = "Mike Moretti"
DEFAULT_BLOG_ROLE = "Co-founder, Wellness Nest"


def roster_path():
    """Roster file for the checkout that is running.

    Prefer roster.json next to this script. On the Mac daily checkout that is
    the same file as /Users/kevinkreative/genseo/roster.json. A worktree keeps
    its own copy, so an author added on a branch is what this checkout's gate
    checks, without editing the main checkout. GENSEO_ROSTER_PATH overrides both.
    """
    override = os.environ.get("GENSEO_ROSTER_PATH")
    if override:
        return override
    if os.path.isfile(_REPO_ROSTER):
        return _REPO_ROSTER
    return _MAC_ROSTER


def _validate(roster):
    blogs = []
    for handle, entry in roster.items():
        page = entry.get("page")
        if page is not None and page != "/pages/" + handle:
            raise ValueError("roster handle %s has page %s; expected /pages/%s" % (handle, page, handle))
        if "headshot" in entry:
            shot = entry.get("headshot")
            if shot is not None and (
                not isinstance(shot, str) or not shot.strip()
                or shot.strip().upper().startswith("PLACEHOLDER")
            ):
                raise ValueError("roster %s headshot must be a real path or null" % handle)
        if "blog" in (entry.get("default_for") or []):
            blogs.append(handle)
    if len(blogs) > 1:
        raise ValueError("roster.json has more than one blog default: %s" % ", ".join(blogs))


def load(path=None):
    import json
    path = path or roster_path()
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = json.load(f)
    roster = {h: v for h, v in data.items()
              if not h.startswith("_") and isinstance(v, dict) and v.get("name")}
    _validate(roster)
    return roster


def _flagged(kind):
    hits = [(h, v) for h, v in ROSTER.items() if kind in (v.get("default_for") or [])]
    if len(hits) > 1:
        raise ValueError("roster.json has more than one %s default: %s" % (
            kind, ", ".join(h for h, _ in hits)))
    return hits[0] if hits else None


def blog_default():
    """Byline for a new Wellness Nest blog draft.

    Kevin 2026-10-21: blog posts use co-founder Mike Moretti. The entry with
    "blog" in default_for wins. Otherwise the first roster person.
    """
    return _flagged("blog") or (next(iter(ROSTER.items())) if ROSTER else None)


def landing_default():
    """Byline for a new landing page. Dr. Marcus Hale, unless default_for says otherwise."""
    flagged = _flagged("landing")
    if flagged:
        return flagged
    entry = ROSTER.get("dr-marcus-hale")
    if entry:
        return "dr-marcus-hale", entry
    return None


ROSTER_PATH = roster_path()
ROSTER = load()                                    # handle -> entry
NAMES = {h: v["name"] for h, v in ROSTER.items()}  # handle -> display name
PAGES = {f"/pages/{h}" for h in ROSTER}
BIOS = tuple(v["bio"] for v in ROSTER.values() if v.get("bio"))

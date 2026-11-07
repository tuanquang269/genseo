"""Author roster — the SINGLE source of truth for every byline the pipeline may use.

Edit roster.json at the repo root. Do NOT re-introduce per-script ROSTER dicts;
validate_article.py, shopify_publisher.py, repair_schema.py and fix_untitled.py
all import this module, so the three-way drift the donor store suffered from
cannot recur.

roster.json format (handles starting with "_" are ignored):

    {
      "jane-doe": {
        "name": "Jane Doe",
        "bio": "Jane Doe is ... (EXACT approved sentence; the gate matches its first 60 chars)"
      }
    }

Rules (enforced by validate_article.py):
  * every handle must have a LIVE page at https://wellnessnest.co/pages/<handle>
  * bios must be the approved sentence verbatim — no invented credentials
    (no Dr./MD/PhD/RD/CISSN unless the person actually holds it)
  * empty roster = publishing is blocked, by design
"""
import json
import os

ROSTER_PATH = "/Users/kevinkreative/genseo/roster.json"


def load():
    if not os.path.exists(ROSTER_PATH):
        return {}
    with open(ROSTER_PATH) as f:
        data = json.load(f)
    return {h: v for h, v in data.items()
            if not h.startswith("_") and isinstance(v, dict) and v.get("name")}


ROSTER = load()                                    # handle -> {"name":…, "bio":…}
NAMES = {h: v["name"] for h, v in ROSTER.items()}  # handle -> display name
PAGES = {f"/pages/{h}" for h in ROSTER}
BIOS = tuple(v["bio"] for v in ROSTER.values() if v.get("bio"))

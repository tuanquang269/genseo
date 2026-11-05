#!/usr/bin/env python3
"""Canonical entity names for GenSeo drafts.

data/entity_canonical_names.json is the proposed map. variant_warnings() is a
WARN for validate_article.py. A non-canonical spelling does not fail publish.

  python3 scripts/entity_names.py <draft.md>
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_PATH = os.path.join(ROOT, "data", "entity_canonical_names.json")

_URL = re.compile(r"https?://\S+|www\.\S+", re.I)
_TAG = re.compile(r"(?is)<script[^>]*>.*?</script>|<style[^>]*>.*?</style>|<[^>]+>")


def load_map(path=None):
    with open(path or MAP_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    if "entities" not in data:
        raise ValueError("canonical name map has no entities")
    return data


def visible_text(html):
    """Drop tags and URLs so a domain cannot trip a brand-spelling warning."""
    text = _TAG.sub(" ", html or "")
    text = _URL.sub(" ", text)
    return text


def variant_warnings(html, path=None):
    """WARN strings for non-canonical spellings. Empty when the draft is clean.

    One warning per entity. URLs are ignored, so wellnessnest.co is quiet.
    """
    text = visible_text(html)
    warnings = []
    for entity in load_map(path)["entities"]:
        canonical = entity["canonical"]
        for pattern in entity.get("warn_patterns") or []:
            match = re.search(pattern, text)
            if not match:
                continue
            warnings.append(
                "entity name: %r is not the canonical %s name %r"
                % (match.group(0), entity["id"], canonical)
            )
            break
    return warnings


def main(argv):
    if len(argv) != 1:
        print("usage: python3 scripts/entity_names.py <draft.md>", file=sys.stderr)
        return 2
    with open(argv[0], encoding="utf-8", errors="ignore") as fh:
        warnings = variant_warnings(fh.read())
    for warning in warnings:
        print("WARN " + warning)
    print("entity-name warnings: %d" % len(warnings))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

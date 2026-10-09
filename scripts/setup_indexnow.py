#!/usr/bin/env python3
"""Print IndexNow hosting steps. Does not call Shopify.

An older copy of this file created a theme template and a page on the live
store. That write path is removed. Hosting the key file is manual — see
docs/indexnow-and-llms-txt.md.
"""
from __future__ import annotations

import os
import sys

DOC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "indexnow-and-llms-txt.md")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    print("IndexNow setup does not upload anything to Shopify.")
    print(f"Read {DOC}")
    print("1. Pick a key locally: 8–128 characters, only [A-Za-z0-9-]. Do not commit it.")
    print("2. Host a text file whose entire body is that key.")
    print("   Preferred URL: https://wellnessnest.co/<key>.txt")
    print("   Or any other https URL on wellnessnest.co, then set INDEXNOW_KEY_LOCATION to it.")
    print("3. export INDEXNOW_KEY='<key>'")
    print("4. python3 scripts/indexnow_ping.py --dry-run --url https://wellnessnest.co/blogs/news/<handle>")
    print("5. After curl shows the key URL body equals the key, the next live publish can ping.")
    print("   One-off: python3 scripts/indexnow_ping.py --send --url https://wellnessnest.co/blogs/news/<handle>")
    if "--apply" in argv or "--upload" in argv:
        print("Refusing --apply/--upload. This script no longer writes the theme, pages, or key file.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

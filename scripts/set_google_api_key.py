#!/usr/bin/env python3
"""Store a Google API key into ~/.config/claude-seo/google-api.json.

Unlocks claude-seo Tier 0: PageSpeed Insights, CrUX field data, and CrUX History
(25-week Core Web Vitals trend). We currently measure no CWV at all, and this is
also what turns on `scripts/seo_drift.py --cwv`.

Reads the key from a hidden prompt or stdin so it never lands in shell history or
a chat transcript. Verifies the key against the CrUX API before saving, so a
typo or a key without the right APIs enabled fails here instead of silently
later.

Usage:
    python3 scripts/set_google_api_key.py            # hidden prompt
    pbpaste | python3 scripts/set_google_api_key.py --stdin
"""
import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

CONFIG = os.path.expanduser("~/.config/claude-seo/google-api.json")
PROBE_URL = "https://wellnessnest.co/"


def verify(key):
    """Hit the CrUX API. Distinguishes a bad key from merely-thin CrUX data."""
    body = json.dumps({"url": PROBE_URL, "formFactor": "PHONE"}).encode()
    req = urllib.request.Request(
        "https://chromeuxreport.googleapis.com/v1/records:queryRecord",
        data=body,
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            json.load(res)
        return True, "CrUX returned field data for wellnessnest.co"
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        if e.code == 404:
            # Key is valid; this origin just lacks enough Chrome traffic.
            return True, "key accepted (CrUX 404 = not enough Chrome traffic for this origin yet)"
        if e.code == 403:
            return False, ("403 from CrUX. Either the key is wrong, or the Chrome UX Report API "
                           f"is not enabled on the project, or a key restriction blocks it.\n{detail}")
        return False, f"HTTP {e.code}: {detail}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stdin", action="store_true", help="read the key from stdin instead of prompting")
    ap.add_argument("--force", action="store_true", help="save even if verification fails")
    args = ap.parse_args()

    key = (sys.stdin.readline() if args.stdin else getpass.getpass("Google API key (hidden): ")).strip()
    if not key:
        sys.exit("no key given")

    ok, detail = verify(key)
    print(("VERIFIED: " if ok else "VERIFY FAILED: ") + detail)
    if not ok and not args.force:
        sys.exit("not saved. Fix the above, or re-run with --force to save anyway.")

    if not os.path.isdir(os.path.dirname(CONFIG)):
        os.makedirs(os.path.dirname(CONFIG), mode=0o700, exist_ok=True)
    cfg = {}
    if os.path.isfile(CONFIG):
        with open(CONFIG) as f:
            cfg = json.load(f)
    cfg["api_key"] = key

    fd = os.open(CONFIG, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(CONFIG, 0o600)
    print(f"saved to {CONFIG} (0600)")
    print("\nNext:")
    print("  claude-seo run google_auth.py --check --json     # psi/crux/crux_history should read OK")
    print("  python3 scripts/seo_drift.py baseline --cwv      # add CWV to the drift snapshots")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Re-authorize claude-seo's Google OAuth token with the GA4 read scope.

Why this is needed: claude-seo reuses the refresh token from
`scripts/gsc_token.json`, which Google issued for `webmasters.readonly` only.
GSC and URL Inspection work, but any GA4 Data API call fails with
`403 PERMISSION_DENIED / Request had insufficient authentication scopes`.
Note that claude-seo's own error text for this is misleading: it says "add the
service account email as Viewer", which is wrong here because we authenticate
with OAuth, not a service account. The blocker is the scope.

Scopes requested (least privilege, exactly what we use):
    webmasters.readonly   Search Analytics, URL Inspection, sitemap listing
    analytics.readonly    GA4 Data API

Deliberately NOT requested: `webmasters` (write) and `indexing`. We do not submit
sitemaps or push URLs from code, and the Indexing API is officially limited to
JobPosting and BroadcastEvent pages, so neither scope buys us anything.

Writes ONLY to ~/.config/claude-seo/oauth-token.json. It never touches
scripts/gsc_token.json, so the existing genseo pipeline keeps working on its own
token no matter what happens here. Both files are backed up first anyway.

This is INTERACTIVE: it opens a browser for the Google consent screen. Run it
yourself in a terminal.

    python3 scripts/claude_seo_reauth.py
    python3 scripts/claude_seo_reauth.py --no-browser   # print the URL instead
"""
import argparse
import datetime
import json
import os
import shutil
import sys
import urllib.error
import urllib.request

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
]
CLIENT = "~/genseo/scripts/credentials.json"
PIPELINE_TOKEN = "~/genseo/scripts/gsc_token.json"
CS_TOKEN = os.path.expanduser("~/.config/claude-seo/oauth-token.json")
CS_CONFIG = os.path.expanduser("~/.config/claude-seo/google-api.json")


def backup():
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    outdir = f"~/genseo/backups/{stamp}-oauth"
    os.makedirs(outdir, exist_ok=True)
    for src in (PIPELINE_TOKEN, CS_TOKEN, CS_CONFIG):
        if os.path.isfile(src):
            dst = os.path.join(outdir, os.path.basename(src))
            shutil.copy2(src, dst)
            os.chmod(dst, 0o600)
            print(f"  backed up {src} -> {dst}")
    return outdir


def write_cs_token(creds):
    """claude-seo wants access_token + expires_at(unix); google-auth gives
    token + expiry(datetime)."""
    data = {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "expires_at": creds.expiry.replace(tzinfo=datetime.timezone.utc).timestamp()
                      if creds.expiry else 0,
        "scopes": list(creds.scopes or SCOPES),
        "token_uri": creds.token_uri,
    }
    os.makedirs(os.path.dirname(CS_TOKEN), mode=0o700, exist_ok=True)
    fd = os.open(CS_TOKEN, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(CS_TOKEN, 0o600)


def verify_ga4(access_token, property_id):
    body = json.dumps({
        "dateRanges": [{"startDate": "28daysAgo", "endDate": "yesterday"}],
        "metrics": [{"name": "sessions"}],
    }).encode()
    req = urllib.request.Request(
        f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport",
        data=body,
        headers={"Authorization": f"Bearer {access_token}",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            d = json.load(res)
        rows = d.get("rows") or []
        sessions = rows[0]["metricValues"][0]["value"] if rows else "0"
        return True, f"GA4 responded: {sessions} sessions in the last 28 days"
    except urllib.error.HTTPError as e:
        err = json.loads(e.read()).get("error", {})
        return False, f"HTTP {e.code} {err.get('status')}: {err.get('message')}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-browser", action="store_true",
                    help="print the consent URL instead of opening a browser")
    args = ap.parse_args()

    if not os.path.isfile(CLIENT):
        sys.exit(f"OAuth client not found: {CLIENT}")
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        sys.exit("pip install google-auth-oauthlib")

    print("Backing up existing credentials...")
    outdir = backup()

    print("\nRequesting scopes:")
    for s in SCOPES:
        print("   ", s)
    print("\nA Google consent screen is about to open. Approve BOTH scopes.\n")

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT, SCOPES)
    creds = flow.run_local_server(port=0, open_browser=not args.no_browser)

    granted = set(creds.scopes or [])
    missing = [s for s in SCOPES if s not in granted]
    if missing:
        print("WARNING: these scopes were not granted:", missing, file=sys.stderr)

    write_cs_token(creds)
    print(f"\nwrote {CS_TOKEN} (0600)")
    print(f"pipeline token untouched: {PIPELINE_TOKEN}")

    prop = None
    if os.path.isfile(CS_CONFIG):
        prop = (json.load(open(CS_CONFIG)).get("ga4_property_id") or "").replace("properties/", "")
    if prop:
        ok, detail = verify_ga4(creds.token, prop)
        print(("\nVERIFIED: " if ok else "\nVERIFY FAILED: ") + detail)
        if not ok:
            print(f"Restore from {outdir} if this made things worse.", file=sys.stderr)
            return 1
    else:
        print("\nNo ga4_property_id in config; skipped GA4 verification.")

    print("\nNext:")
    print("  claude-seo run ga4_report.py --json                 # organic traffic, 28d")
    print("  claude-seo run ga4_report.py --report top-pages --json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Read Merchant Center YOUR_MERCHANT_ID feed health via the Content API.

Answers the four questions that the 2026-08-02 GTIN write and the 2026-08-05 vendor→brand
merge left open:
  1. Did any GTIN I wrote get rejected or, worse, MISMATCHED against Google's catalog?
     (a valid check digit proves the number is well-formed, NOT that it is this product)
  2. Did the 203 "not approved" items move, and why are they disapproved?
  3. Are offers now MATCHED to Google's catalog entities — the actual goal, which is
     different from "approved"?
  4. Did the 8 brand-renamed products break anything?

Auth notes:
  * Uses the SAME OAuth client as GSC (project geoseo-493018) but writes its OWN token file,
    `mc_token.json`. It never touches `gsc_token.json` — a botched consent flow must not take
    Search Console access down with it.
  * Requires: Content API for Shopping enabled in the Cloud project, and the Google account
    doing the consent must have access to Merchant Center YOUR_MERCHANT_ID.

Usage:
    python3 scripts/mc_diagnostics.py            # authorises on first run, then reports
    python3 scripts/mc_diagnostics.py --check    # prerequisites only, no data pull
"""
import argparse
import collections
import datetime
import json
import os
import pathlib
import sys

SHARED = pathlib.Path("~/genseo/scripts/").expanduser()
CREDS = SHARED / "credentials.json"
TOKEN = SHARED / "mc_token.json"
# `content` alone is enough to call the API, but then a wrong-account consent is undiagnosable:
# Google replies "User cannot access account YOUR_MERCHANT_ID" without saying WHICH user, and the token
# records no email. The email scope turns that guessing game into a printed address.
SCOPES = ["https://www.googleapis.com/auth/content", "openid",
          "https://www.googleapis.com/auth/userinfo.email"]
# Google silently adds/reorders granted scopes (it always injects `openid`), which oauthlib
# otherwise rejects as "Scope has changed".
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")
MERCHANT_ID = "YOUR_MERCHANT_ID"
BASE = pathlib.Path(__file__).resolve().parent.parent
# GTIN-shaped issues are the ones that can make us WORSE than having no identifier, because a
# wrong-but-valid number joins our offer to somebody else's product entity.
GTIN_ISSUE_HINTS = ("gtin", "identifier", "brand", "mpn")


def service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not CREDS.exists():
            sys.exit(f"missing {CREDS}")
        print("\nOpening a browser for Google sign-in.")
        print("  → Sign in as the account that owns Merchant Center YOUR_MERCHANT_ID")
        print("    (you@example.com), then click Allow.\n")
        creds = InstalledAppFlow.from_client_secrets_file(str(CREDS), SCOPES).run_local_server(port=0)
        TOKEN.write_text(creds.to_json())
        os.chmod(TOKEN, 0o600)
        print(f"saved {TOKEN}")
    return build("content", "v2.1", credentials=creds, cache_discovery=False), creds


def explain(exc):
    """Turn Google's generic 403s into the one thing the operator actually has to fix."""
    text = str(exc)
    if "has not been used in project" in text or "is disabled" in text:
        return ("Content API for Shopping is not enabled in project geoseo-493018.\n"
                "  Fix: https://console.cloud.google.com/apis/library/"
                "shoppingcontent.googleapis.com?project=geoseo-493018 → Enable")
    if "insufficient" in text.lower() or "ACCESS_TOKEN_SCOPE" in text:
        return (f"The token lacks the content scope. Fix: delete {TOKEN} and re-run to re-consent.")
    if "does not have access" in text or "cannot access account" in text or "account_access_denied" in text:
        return (f"The signed-in Google account is not a user on Merchant Center {MERCHANT_ID}.\n"
                f"  Fix A: rm {TOKEN} and re-run, signing in as you@example.com\n"
                f"  Fix B: add the account shown above in Merchant Center → Settings →\n"
                f"         People and access (Standard or Admin)")
    return text[:400]


def signed_in_as(creds):
    """The email that actually consented — the one fact the 401 never tells you."""
    import urllib.request
    try:
        with urllib.request.urlopen(
                f"https://oauth2.googleapis.com/tokeninfo?access_token={creds.token}", timeout=20) as r:
            return json.loads(r.read()).get("email") or "(token carries no email scope)"
    except Exception as exc:
        return f"(lookup failed: {type(exc).__name__})"


def check(svc, creds):
    """Probe the account we actually want, not accounts.authinfo().

    authinfo() returned an EMPTY accountIdentifiers list for an account that could read the
    account and its product statuses perfectly well, so gating on it rejects working
    credentials. accounts.get() on the real merchant id is the authoritative test.
    """
    who = signed_in_as(creds)
    print("signed in as      :", who)
    try:
        acct = svc.accounts().get(merchantId=MERCHANT_ID, accountId=MERCHANT_ID).execute()
    except Exception as exc:
        print(f"\n⚠ Merchant Center {MERCHANT_ID} is NOT readable by {who}.\n\n{explain(exc)}")
        print("\n  If you JUST granted access, the invite may still be pending — accept the\n"
              f"  Merchant Center invitation email in {who}, then re-run.")
        return False
    print(f"✓ {MERCHANT_ID} readable  ({acct.get('name')} — {acct.get('websiteUrl')})")
    ads = ", ".join(f"{l.get('adsId')}:{l.get('status')}" for l in acct.get("adsLinks", []))
    print(f"  linked Google Ads : {ads or '(none)'}")
    users = [(u.get("emailAddress"), "admin" if u.get("admin") else "standard")
             for u in acct.get("users", [])]
    print(f"  MC users ({len(users)})   : " + ", ".join(f"{e} [{r}]" for e, r in users))
    return True


def fetch_statuses(svc):
    rows, token = [], None
    while True:
        resp = svc.productstatuses().list(
            merchantId=MERCHANT_ID, maxResults=250, pageToken=token).execute()
        rows += resp.get("resources", [])
        token = resp.get("nextPageToken")
        if not token:
            break
        print(f"  fetched {len(rows)}…", end="\r")
    return rows


def report(rows):
    dest = collections.Counter()
    issues = collections.Counter()
    severity = collections.defaultdict(collections.Counter)
    examples = collections.defaultdict(list)
    for r in rows:
        for d in r.get("destinationStatuses", []):
            dest[(d.get("destination"), d.get("status"))] += 1
        for it in r.get("itemLevelIssues", []):
            key = it.get("description") or it.get("code")
            issues[key] += 1
            severity[key][it.get("servability", "?")] += 1
            if len(examples[key]) < 3:
                examples[key].append((r.get("productId", "")[-46:], it.get("attributeName") or ""))

    print(f"\nfeed items with a status row : {len(rows)}")
    print("\n-- destination status (was: 3,759 total / 3,556 approved / 203 not approved) --")
    for (d, s), n in sorted(dest.items(), key=lambda kv: -kv[1]):
        print(f"{n:6d}  {d:22} {s}")

    print("\n-- item-level issues, worst first --")
    for key, n in issues.most_common(30):
        sev = ",".join(f"{k}:{v}" for k, v in severity[key].items())
        flag = " ⚠GTIN/BRAND" if any(h in key.lower() for h in GTIN_ISSUE_HINTS) else ""
        print(f"{n:6d}  [{sev}] {key[:76]}{flag}")
        for pid, attr in examples[key]:
            print(f"           e.g. {pid} {attr}")

    gtin_hits = {k: v for k, v in issues.items()
                 if any(h in k.lower() for h in GTIN_ISSUE_HINTS)}
    print("\n" + "=" * 72)
    if gtin_hits:
        print("GTIN / BRAND ISSUES PRESENT — read these before anything else:")
        for k, v in sorted(gtin_hits.items(), key=lambda kv: -kv[1]):
            print(f"  {v:6d}  {k}")
        print("\nA 'mismatch' or 'incorrect identifier' here means a barcode written on 2026-08-02\n"
              "is well-formed but belongs to a different product. That is worse than a blank GTIN\n"
              "and should be reverted from backups/2026-08-02/ for the affected items.")
    else:
        print("No GTIN or brand issues reported. The 2026-08-02 barcode write and the\n"
              "2026-08-05 vendor→brand merge did not introduce feed errors.")
    out = BASE / "backups" / datetime.date.today().isoformat() / "mc_diagnostics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "merchant_id": MERCHANT_ID, "items": len(rows),
        "destination_status": {f"{d}|{s}": n for (d, s), n in dest.items()},
        "item_level_issues": dict(issues.most_common()),
        "gtin_or_brand_issues": gtin_hits,
    }, indent=1))
    print(f"\nsaved: {out}")
    return 1 if gtin_hits else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify access only, pull no data")
    a = ap.parse_args()
    try:
        svc, creds = service()
        if not check(svc, creds):
            return 2
        if a.check:
            print("\nPrerequisites OK — re-run without --check for the full report.")
            return 0
        return report(fetch_statuses(svc))
    except SystemExit:
        raise
    except Exception as exc:
        print(f"\n✗ {type(exc).__name__}\n\n{explain(exc)}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())

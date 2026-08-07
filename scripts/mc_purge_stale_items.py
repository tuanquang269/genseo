#!/usr/bin/env python3
"""MC-2: delete the 83 stale Merchant Center items that no system owns.

These are NOT pushed by the Shopify "Google & YouTube" app. Two proofs:
  * the app's ids look like `online:en:SG:shopify_SG_<product>_<variant>`; these look like
    `online:en:SG:<digits>_<digits>`
  * their `link` points at COLLECTION urls with `?variant=` (e.g. /collections/bpi-sports-copy,
    a junk collection ACTION-PLAN 0.4 already slates for deletion), which the app never emits

So nothing will ever correct them, and nothing will re-push them after deletion. Both of the
feed's "Missing product price" errors live in this set, plus a mis-branding (an Applied
Nutrition product sold as brand "Your Brand").

Also removes the pseudo-product literally titled "Free Shipping" (MC-5) if it is app-pushed —
that one is a cart mechanic, not a product, so it is excluded from the Google channel in
Shopify instead of deleted here (see --report).

Every item is exported in full before deletion; `--revert` re-inserts from that export.

Usage:
    python3 scripts/mc_purge_stale_items.py --report
    python3 scripts/mc_purge_stale_items.py --apply --limit 2      # canary
    python3 scripts/mc_purge_stale_items.py --apply
    python3 scripts/mc_purge_stale_items.py --revert
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import sys
import time
import urllib.request

MERCHANT_ID = "YOUR_MERCHANT_ID"
SHARED = pathlib.Path("~/genseo/scripts/").expanduser()
TOKEN = SHARED / "mc_token.json"
SCOPES = ["https://www.googleapis.com/auth/content", "openid",
          "https://www.googleapis.com/auth/userinfo.email"]
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")
BASE = pathlib.Path(__file__).resolve().parent.parent
OUT = BASE / "backups" / datetime.date.today().isoformat()
EXPORT = OUT / "mc_stale_items_export.json"
LOG = OUT / "mc_purge_log.json"
# The app's own ids always carry this marker. Anything else in the feed is orphaned.
APP_ID = re.compile(r"shopify_SG_\d+_\d+$")


def service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    creds.refresh(Request())
    return build("content", "v2.1", credentials=creds, cache_discovery=False)


def all_products(svc):
    out, tok = [], None
    while True:
        r = svc.products().list(merchantId=MERCHANT_ID, maxResults=250, pageToken=tok).execute()
        out += r.get("resources", [])
        tok = r.get("nextPageToken")
        if not tok:
            return out


def classify(products):
    stale = [p for p in products if not APP_ID.search(p.get("id", ""))]
    app = [p for p in products if APP_ID.search(p.get("id", ""))]
    return stale, app


def sole_feed_row(stale, app, shopify_id_for_handle):
    """Orphan rows that are the ONLY feed presence for a live product — never delete these.

    Found the hard way: 21 of the 83 orphans point at real product pages, and 20 of those
    products (4,212 units of Mutant and Ghost stock, priority brands #1 and #3) have NO
    app-pushed row at all. Deleting the orphan would have removed them from Google Shopping
    outright. The app's row is matched on the Shopify PRODUCT ID inside the feed id, not on the
    handle in the link — handles differ between the two sources.
    """
    app_ids = " ".join(p.get("id", "") for p in app)
    protected, deletable = [], []
    for p in stale:
        m = re.search(r"/products/([^/?#]+)", p.get("link") or "")
        pid = shopify_id_for_handle(m.group(1)) if m else None
        if pid and f"shopify_SG_{pid}_" not in app_ids:
            protected.append(p)
        else:
            deletable.append(p)
    return protected, deletable


SHOPIFY = json.load(open(SHARED / "shopify_token.json"))


def shopify_id_for_handle(handle, _cache={}):
    if handle in _cache:
        return _cache[handle]
    body = json.dumps({"query": "query($h:String!){productByIdentifier(identifier:{handle:$h}){id}}",
                       "variables": {"h": handle}}).encode()
    req = urllib.request.Request(
        f"https://{SHOPIFY['shop']}/admin/api/2026-04/graphql.json", data=body,
        headers={"X-Shopify-Access-Token": SHOPIFY["access_token"], "Content-Type": "application/json"})
    node = (json.loads(urllib.request.urlopen(req, timeout=60).read())
            .get("data", {}) or {}).get("productByIdentifier")
    _cache[handle] = node["id"].split("/")[-1] if node else None
    return _cache[handle]


def selftest():
    app_like = {"id": "online:en:SG:shopify_SG_8367326986422_44425374761142"}
    stale_like = {"id": "online:en:SG:3253673306134090152_521666026075726977"}
    s, a = classify([app_like, stale_like])
    assert [p["id"] for p in s] == [stale_like["id"]], s
    assert [p["id"] for p in a] == [app_like["id"]], a
    # a local-channel app item must also be recognised as app-owned, never as stale
    loc = {"id": "local:en:SG:shopify_SG_1_2"}
    assert classify([loc])[0] == [], "local app items must not be classified stale"
    # the guard: an orphan whose product has no app row must be protected, not deleted
    orphan = {"id": "online:en:SG:1_2", "link": "https://x/products/mutant-madness"}
    prot, dele = sole_feed_row([orphan], [{"id": "online:en:SG:shopify_SG_999_1"}], lambda h: "7422553718966")
    assert prot == [orphan] and dele == [], (prot, dele)
    prot, dele = sole_feed_row([orphan], [{"id": "online:en:SG:shopify_SG_7422553718966_5"}], lambda h: "7422553718966")
    assert dele == [orphan] and prot == [], (prot, dele)
    print("selftest OK — app ids kept, orphans selected, local safe, sole-feed-row protected")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--limit", type=int, help="canary: delete only the first N")
    a = ap.parse_args()
    if not (a.report or a.apply or a.revert):
        ap.error("pass --report, --apply or --revert")
    selftest()
    svc = service()

    if a.revert:
        if not EXPORT.is_file():
            sys.exit(f"no export at {EXPORT}")
        items = {i["id"]: i for i in json.loads(EXPORT.read_text())}
        deleted = json.loads(LOG.read_text())["deleted"] if LOG.is_file() else []
        restored = 0
        for pid in deleted:
            item = dict(items[pid])
            for k in ("id", "kind", "source"):
                item.pop(k, None)
            svc.products().insert(merchantId=MERCHANT_ID, body=item).execute()
            restored += 1
            time.sleep(0.3)
        print(f"re-inserted {restored}/{len(deleted)}")
        return 0

    products = all_products(svc)
    stale_all, app = classify(products)
    protected, stale = sole_feed_row(stale_all, app, shopify_id_for_handle)
    print(f"\nfeed items {len(products)}: {len(app)} app-pushed, {len(stale_all)} orphaned")
    print(f"  {len(stale)} deletable, {len(protected)} PROTECTED (sole feed row for a live product)\n")
    if protected:
        print("  PROTECTED — deleting these would remove the product from Google Shopping entirely:")
        for p in protected:
            print(f"      {(p.get('title') or '?')[:62]}")
        prot_path = OUT / "mc_protected_sole_feed_rows.json"
        OUT.mkdir(parents=True, exist_ok=True)
        prot_path.write_text(json.dumps(protected, indent=1, ensure_ascii=False))
        print(f"      -> {prot_path}\n")

    # what exactly are we deleting — grouped by where the link points
    kinds = {}
    for p in stale:
        link = p.get("link") or ""
        kind = ("collection URL" if "/collections/" in link
                else "product URL" if "/products/" in link else "other")
        kinds.setdefault(kind, []).append(p)
    for kind, ps in sorted(kinds.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(ps):3d}  link points at a {kind}")
        for p in ps[:3]:
            print(f"          {(p.get('title') or '?')[:56]}  brand={p.get('brand')!r}")
    # anything app-pushed that is not a real product (MC-5) — reported, not deleted here
    fake = [p for p in app if re.fullmatch(r"(?i)free shipping|shipping|tip|donation",
                                           (p.get("title") or "").strip())]
    if fake:
        print(f"\n  NOT deleted here (app-pushed, fix in Shopify by removing from the Google "
              f"sales channel): {[p.get('title') for p in fake]}")

    if a.report:
        OUT.mkdir(parents=True, exist_ok=True)
        EXPORT.write_text(json.dumps(stale, indent=1, ensure_ascii=False))
        print(f"\nexported {len(stale)} items -> {EXPORT}  (this file is the undo)")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    if not EXPORT.is_file():
        EXPORT.write_text(json.dumps(stale, indent=1, ensure_ascii=False))
        print(f"\nexported {len(stale)} -> {EXPORT}")
    targets = stale[:a.limit] if a.limit else stale
    done, errs = [], []
    for p in targets:
        try:
            svc.products().delete(merchantId=MERCHANT_ID, productId=p["id"]).execute()
            done.append(p["id"])
        except Exception as exc:
            errs.append((p["id"], f"{type(exc).__name__}: {str(exc)[:120]}"))
        time.sleep(0.3)
    prior = json.loads(LOG.read_text())["deleted"] if LOG.is_file() else []
    LOG.write_text(json.dumps({"deleted": sorted(set(prior) | set(done)),
                               "errors": errs}, indent=1))
    print(f"\ndeleted {len(done)}/{len(targets)}, {len(errs)} error(s); log {LOG}")
    for pid, why in errs:
        print(f"   FAIL {pid[-40:]}: {why}", file=sys.stderr)

    # products.list is EVENTUALLY CONSISTENT — it kept reporting all 83 orphans minutes after a
    # confirmed delete. products.get is authoritative, so verify each id individually.
    still = []
    for pid in done:
        try:
            svc.products().get(merchantId=MERCHANT_ID, productId=pid).execute()
            still.append(pid)
        except Exception:
            pass
    print(f"confirmed gone: {len(done) - len(still)}/{len(done)}"
          + (f"  STILL PRESENT: {still}" if still else ""))
    print(f"protected and untouched: {len(protected)}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())

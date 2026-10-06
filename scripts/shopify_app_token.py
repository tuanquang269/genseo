#!/usr/bin/env python3
"""Admin API token for Kevin's CLI control app via the OAuth client-credentials grant (no secrets printed).

  /usr/bin/python3 scripts/shopify_app_token.py            # prints shop, granted scopes, expiry
Reads SHOPIFY_CLI_APP_{SHOP,CLIENT_ID,CLIENT_SECRET} from ~/genseo/.env (gitignored, chmod 600).
Caches the token in ~/.genseo/cli_app_token.json (chmod 600) until shortly before it expires.
Import: from shopify_app_token import get_token -> (shop, token, scopes)
"""
import json, os, time, urllib.parse, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.expanduser("~/.genseo/cli_app_token.json")


def _env():
    d = {}
    for line in open(os.path.join(ROOT, ".env")):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def get_token(force=False):
    e = _env()
    shop = e["SHOPIFY_CLI_APP_SHOP"]
    if not force and os.path.exists(CACHE):
        c = json.load(open(CACHE))
        if c.get("shop") == shop and c.get("expires_at", 0) > time.time() + 300:
            return shop, c["access_token"], c.get("scope", "")
    body = urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": e["SHOPIFY_CLI_APP_CLIENT_ID"],
                                   "client_secret": e["SHOPIFY_CLI_APP_CLIENT_SECRET"]}).encode()
    req = urllib.request.Request(f"https://{shop}/admin/oauth/access_token", data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=30))
    except urllib.error.HTTPError as ex:
        raise SystemExit(f"token exchange failed: HTTP {ex.code} {ex.read()[:300].decode(errors='replace')}")
    rec = {"shop": shop, "access_token": r["access_token"], "scope": r.get("scope", ""),
           "expires_at": time.time() + int(r.get("expires_in", 86399))}
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    fd = os.open(CACHE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(rec, f)
    return shop, rec["access_token"], rec["scope"]


if __name__ == "__main__":
    shop, tok, scope = get_token(force=True)
    print("shop:", shop)
    print("token: obtained (not printed), prefix", tok[:6])
    print("scopes:", scope)
    print("write_themes:", "write_themes" in scope.split(","), "| write_content:", "write_content" in scope.split(","))

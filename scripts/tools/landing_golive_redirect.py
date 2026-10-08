#!/usr/bin/env python3
"""Task 6 go-live helper. Prints no credentials.
  golive_redirect.py check  <old-handle> <new-handle>   read-only: is new handle free? existing redirects?
  golive_redirect.py create <old-handle> <new-handle>   create ONE 301 /pages/<old> -> /pages/<new> only if none exists from <old>."""
import json, os, sys, urllib.request, urllib.parse
sys.path.insert(0, os.path.expanduser("~/genseo/scripts"))
import genseo_config as cfg
from shopify_auth import pick
mode, old, new = sys.argv[1:4]
need = {"read_online_store_pages"} if mode == "check" else {"write_online_store_navigation"}
shop, token, src = pick(need)
H = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
def api(p, data=None, method="GET"):
    req = urllib.request.Request(f"https://{shop}/admin/api/{cfg.API}/{p}", data=json.dumps(data).encode() if data else None, method=method, headers=H)
    return json.load(urllib.request.urlopen(req, timeout=30))
def redirects(**q): return api("redirects.json?limit=250&" + urllib.parse.urlencode(q))["redirects"]
if mode == "check":
    hits = [p for pub in ("published", "unpublished") for p in api(f"pages.json?limit=250&published_status={pub}&handle={new}&fields=id,handle,published_at")["pages"] if p["handle"] == new]
    print("pages with new handle:", [(p["id"], bool(p["published_at"])) for p in hits])
    print("redirects from /pages/" + new, [(x["id"], x["target"]) for x in redirects(path="/pages/" + new)])
    print("redirects from /pages/" + old, [(x["id"], x["target"]) for x in redirects(path="/pages/" + old)])
    print("redirects to /pages/" + new, [(x["id"], x["path"]) for x in redirects(target="/pages/" + new)])
else:
    ex = redirects(path="/pages/" + old)
    if ex:
        print("exists, not creating:", [(x["id"], x["target"]) for x in ex]); sys.exit(0)
    r = api("redirects.json", {"redirect": {"path": "/pages/" + old, "target": "/pages/" + new}}, "POST")["redirect"]
    print("created redirect", r["id"], r["path"], "->", r["target"])

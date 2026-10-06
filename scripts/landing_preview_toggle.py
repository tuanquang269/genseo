#!/usr/bin/env python3
"""Temporarily show/hide GenSeo THROWAWAY preview pages (handle must start with gsl-preview-).
usage: landing_preview_toggle.py on|off|status <page_id> [<page_id> ...]
       landing_preview_toggle.py push-template <suffix>   # re-upload OUR gsl-ref-* template only
       landing_preview_toggle.py push-body <spec.json>    # re-render body (uses cdn_map) and PUT body_html, keeps published state
Kevin 2026-10-06: approved short live QA windows for gsl-preview-* pages only."""
import json, os, sys, time, urllib.request, urllib.error
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["GENSEO_PUBLISHER_REEXEC"] = "1"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import genseo_config as cfg
from shopify_auth import pick
api = cfg.API
shop, token, AUTH_SRC = pick({"write_themes", "write_online_store_pages", "read_themes"})  # CLI app first, GenSeo token fallback
H = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
def call(path, method="GET", data=None):
    r = urllib.request.Request(f"https://{shop}/admin/api/{api}/{path}", method=method, headers=H,
                               data=json.dumps(data).encode() if data is not None else None)
    return json.load(urllib.request.urlopen(r, timeout=60))
cmd = sys.argv[1]
print("auth:", AUTH_SRC)
if cmd in ("on", "off", "status"):
    for pid in sys.argv[2:]:
        p = call(f"pages/{pid}.json")["page"]
        if not p["handle"].startswith("gsl-preview-"):
            sys.exit(f"✗ refuse: page {pid} handle {p['handle']} is not a gsl-preview- throwaway")
        if cmd != "status":
            p = call(f"pages/{pid}.json", "PUT", {"page": {"id": int(pid), "published": cmd == "on"}})["page"]
        print(time.strftime("%H:%M:%S"), pid, p["handle"], "VISIBLE" if p.get("published_at") else "HIDDEN", p.get("published_at"), p.get("template_suffix"))
elif cmd == "push-template":
    suf = sys.argv[2]
    if not suf.startswith("gsl-ref-"):
        sys.exit("✗ only gsl-ref-* templates (GenSeo-owned new files)")
    key = f"templates/page.{suf}.liquid"
    tid = call("themes.json?role=main")["themes"][0]["id"]
    call(f"themes/{tid}/assets.json?asset[key]={key}")  # must already exist (ours)
    val = open(os.path.join(ROOT, "templates", "landing", f"page.{suf}.liquid")).read()
    call(f"themes/{tid}/assets.json", "PUT", {"asset": {"key": key, "value": val}})
    print("updated", key, "in theme", tid, len(val), "bytes")
elif cmd == "push-body":
    import re
    spec_p = sys.argv[2]; spec = json.load(open(spec_p))
    d = os.path.join(os.path.dirname(spec_p), spec["slug"])
    rec = json.load(open(os.path.join(d, "shopify.json"))); cache = json.load(open(os.path.join(d, "cdn_map.json")))
    body = open(os.path.join(d, "body.html")).read()
    for k, v in cache.items():
        body = body.replace(f'="{k}"', f'="{v}"')
    if re.search(r'(?:src|srcset|data-gslfp-thumb)="/', body):
        sys.exit("✗ local image paths remain (new image? run the publisher draft path)")
    p = call(f"pages/{rec['page_id']}.json")["page"]
    if not p["handle"].startswith("gsl-preview-"):
        sys.exit("✗ refuse: not a gsl-preview- page")
    p = call(f"pages/{rec['page_id']}.json", "PUT", {"page": {"id": rec["page_id"], "body_html": body}})["page"]
    print("body updated", p["handle"], "VISIBLE" if p.get("published_at") else "HIDDEN")

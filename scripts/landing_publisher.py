#!/usr/bin/env python3
"""Validate -> render -> (optionally) push a GenSeo landing page to Shopify as a PAGE.

  /usr/bin/python3 scripts/landing_publisher.py landing_drafts/<slug>.json            # local preview only (default)
  /usr/bin/python3 scripts/landing_publisher.py landing_drafts/<slug>.json --draft    # Shopify page, published:false
  ... --draft --install-template   # also adds templates/page.<suffix>.liquid to the live theme if (and only if) it does not exist
  GENSEO_LANDING_LIVE_OK=1 /usr/bin/python3 scripts/landing_publisher.py <spec> --live   # visible page (Kevin GO only)

Why a Shopify PAGE and not a blog article (decision 2026-10-06):
  * the reference layouts are /pages/ sales pages (listicle + advertorial), not SEO articles;
  * pages never appear in /blogs/news.atom, so they can NEVER count toward — or trip — the
    5/day article target and the two-Mac live-count guard (genseo_published_today.py);
  * validate_article.py's article gates (FAQ schema, ≥900 words, collections, author page) do not
    fit a sales page; validate_landing.py is the gate here.
Theme (vault: wellnessnest-advertorial-builder gotchas #1-#3, crawl-funnel-to-shopify): the live theme has NO default
page template, so the page gets template_suffix (spec "template_suffix", default genseo-landing-v1; advertorial
samples use genseo-landing-takeover-v1 which hides theme chrome). The template files are generated into
templates/landing/page.<suffix>.liquid. --draft does not need them (unpublished page). --live first checks the live
theme for templates/page.<suffix>.liquid and refuses if it is missing; --install-template uploads it (needs
write_themes + GENSEO_LANDING_LIVE_OK=1). Bump the suffix (-v2) whenever the template changes (compiled-template cache).
GemPages caches rendered HTML per URL: iterate on a throwaway handle, publish the real handle once.
Re-running updates the same page (id stored in landing_drafts/<slug>/shopify.json) — never a duplicate.
--live is refused unless GENSEO_LANDING_LIVE_OK=1 AND validate_landing.py --strict passes (0 placeholders).
"""
import json, os, re, subprocess, sys, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = "/usr/bin/python3"


def run(*args):
    r = subprocess.run([PY, *args], cwd=ROOT)
    return r.returncode


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mode = "live" if "--live" in sys.argv else "draft" if "--draft" in sys.argv else "preview"
    if len(args) != 1:
        sys.exit(__doc__)
    spec_path = os.path.abspath(args[0])
    spec = json.load(open(spec_path))
    if mode == "live" and os.environ.get("GENSEO_LANDING_LIVE_OK") != "1":
        sys.exit("✗ --live refused: landing pages go live only on Kevin's explicit GO (set GENSEO_LANDING_LIVE_OK=1 for that run).")
    vargs = ["scripts/validate_landing.py", spec_path] + (["--strict"] if mode == "live" else [])
    if run(*vargs) != 0:
        sys.exit("✗ validate_landing.py failed — fix the spec first")
    if run("scripts/landing_render.py", spec_path) != 0:
        sys.exit("✗ render failed")
    out_dir = os.path.join(os.path.dirname(spec_path), spec["slug"])
    print(f"PREVIEW: file://{out_dir}/preview.html")
    if mode == "preview":
        return
    os.environ["GENSEO_PUBLISHER_REEXEC"] = "1"   # import-only: never let shopify_publisher re-exec us
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import genseo_config as cfg
    from shopify_publisher import upload_image_to_shopify_files
    from shopify_auth import pick
    api = cfg.API
    # One token for the whole job (plan 2026-10-06, switched 2026-10-08 once Kevin granted write_files): template,
    # page and Files image uploads all run on Kevin's CLI control app '0ps Dashboard' (client-credentials).
    # pick() falls back to the GenSeo publisher token only if the CLI app ever loses one of these scopes
    # (or GENSEO_FORCE_PUBLISHER_TOKEN=1).
    shop, token, src = pick({"write_themes", "read_themes", "write_online_store_pages", "write_files"})
    f_shop, f_token, f_src = shop, token, src
    print(f"auth: template+pages+Files via {src}")
    body = open(os.path.join(out_dir, "body.html")).read()
    cache_p = os.path.join(out_dir, "cdn_map.json")
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    for local in sorted(set(re.findall(r'(?:src|srcset|data-gslfp-thumb)="(/[^"]+\.(?:webp|png|jpe?g))"', body))):
        if local not in cache:
            url = upload_image_to_shopify_files(f_shop, f_token, local)
            if not url:
                sys.exit(f"✗ image upload failed: {local}")
            cache[local] = url
        body = body.replace(f'="{local}"', f'="{cache[local]}"')
    json.dump(cache, open(cache_p, "w"), indent=1)
    if re.search(r'(?:src|srcset|data-gslfp-thumb)="/', body):
        sys.exit("✗ local image paths remain after upload")
    rec_p = os.path.join(out_dir, "shopify.json")
    rec = json.load(open(rec_p)) if os.path.exists(rec_p) else {}
    suffix = spec.get("template_suffix", "genseo-landing-v1")
    tkey = f"templates/page.{suffix}.liquid"
    if mode == "draft" and "--install-template" in sys.argv:
        # NEW theme file only (Kevin 2026-10-06): GET first; if the key exists, never overwrite — bump the suffix.
        hdr_r = {"X-Shopify-Access-Token": token}
        tid = json.load(urllib.request.urlopen(urllib.request.Request(
            f"https://{shop}/admin/api/{api}/themes.json?role=main", headers=hdr_r), timeout=30))["themes"][0]["id"]
        try:
            urllib.request.urlopen(urllib.request.Request(
                f"https://{shop}/admin/api/{api}/themes/{tid}/assets.json?asset[key]={tkey}", headers=hdr_r), timeout=30)
            print(f"= {tkey} already exists in theme {tid}: NOT overwritten (bump template_suffix to ship a change)")
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            val = open(os.path.join(ROOT, "templates", "landing", f"page.{suffix}.liquid")).read()
            urllib.request.urlopen(urllib.request.Request(f"https://{shop}/admin/api/{api}/themes/{tid}/assets.json", method="PUT",
                data=json.dumps({"asset": {"key": tkey, "value": val}}).encode(),
                headers={**hdr_r, "Content-Type": "application/json"}), timeout=60)
            print(f"+ installed NEW {tkey} in live theme {tid} (new file; no existing theme file touched)")
    if mode == "live":
        hdr_r = {"X-Shopify-Access-Token": token}
        themes = json.load(urllib.request.urlopen(urllib.request.Request(
            f"https://{shop}/admin/api/{api}/themes.json?role=main", headers=hdr_r), timeout=30))["themes"]
        tid = themes[0]["id"]
        try:
            urllib.request.urlopen(urllib.request.Request(
                f"https://{shop}/admin/api/{api}/themes/{tid}/assets.json?asset[key]={tkey}", headers=hdr_r), timeout=30)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            if "--install-template" not in sys.argv:
                sys.exit(f"✗ live theme has no {tkey}: the page would 404. Re-run with --install-template (write_themes) after Kevin's GO.")
            val = open(os.path.join(ROOT, "templates", "landing", f"page.{suffix}.liquid")).read()
            urllib.request.urlopen(urllib.request.Request(f"https://{shop}/admin/api/{api}/themes/{tid}/assets.json", method="PUT",
                data=json.dumps({"asset": {"key": tkey, "value": val}}).encode(),
                headers={**hdr_r, "Content-Type": "application/json"}), timeout=60)
            print(f"installed {tkey} in theme {tid}")
    page = {"title": spec["title"], "handle": spec.get("handle", spec["slug"]), "body_html": body, "published": mode == "live",
            "template_suffix": suffix}
    if spec.get("meta_description"):
        page["metafields"] = [{"namespace": "global", "key": "description_tag",
                               "value": spec["meta_description"], "type": "single_line_text_field"}]
    hdr = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    if rec.get("page_id"):
        page["id"] = rec["page_id"]
        req = urllib.request.Request(f"https://{shop}/admin/api/{api}/pages/{rec['page_id']}.json",
                                     data=json.dumps({"page": page}).encode(), headers=hdr, method="PUT")
    else:
        req = urllib.request.Request(f"https://{shop}/admin/api/{api}/pages.json",
                                     data=json.dumps({"page": page}).encode(), headers=hdr, method="POST")
    res = json.load(urllib.request.urlopen(req, timeout=60))["page"]
    rec = {"page_id": res["id"], "handle": res["handle"], "published_at": res.get("published_at"), "mode": mode,
           "admin": f"https://admin.shopify.com/store/{shop.split('.')[0]}/content/pages/{res['id']}"}
    json.dump(rec, open(rec_p, "w"), indent=1)
    print(f"ADMIN: {rec['admin']}")
    print(f"STATE: {'LIVE' if res.get('published_at') else 'UNPUBLISHED DRAFT'} · handle /pages/{res['handle']}")


if __name__ == "__main__":
    main()

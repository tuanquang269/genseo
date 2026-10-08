#!/usr/bin/env python3
"""REAL Shopify render QA for a GenSeo landing draft (Kevin 2026-10-08: a local render passed review while his preview
showed something else; approval is on the real storefront render only).

  /usr/bin/python3 scripts/landing_real_qa.py landing_drafts/<slug>.json [--no-window]

1. Parity, read-only, page stays hidden: the MAIN (published) theme holds templates/page.<suffix>.liquid and it is
   byte-identical to templates/landing/page.<suffix>.liquid; page.template_suffix == spec suffix; the page's visible
   text == the local body.html visible text (catches an old body); every <img> is on cdn.shopify.com.
2. Storefront screenshots (skip with --no-window or GENSEO_LANDING_REAL_QA_WINDOW=0): only for gsl-preview- handles.
   It shows the page for about 40 s (landing_preview_toggle.py on), runs scripts/landing_live_shot.mjs (fresh context,
   ?v= cache-buster) to make <out>/real-{desktop,mobile,offer}.png, then ALWAYS hides it again in a finally block and
   re-reads the page to confirm it is hidden. This uses the short gsl-preview QA window Kevin approved (2026-10-06,
   asked for in the daily lane on 2026-10-08). The run_landing_daily.sh post-check force-hides any visible page anyway.
   Checks: HTTP 200, the premium CSS really applied (hero radius), the offer box shows the spec's offer title, no
   horizontal overflow, none of our images broken, and the sticky CTA hidden at the top, shown after the bridge,
   hidden on the offer.
Writes <out>/real_qa.json. Exit 0 = PASS, 1 = FAIL.
"""
import hashlib, html, json, os, re, subprocess, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts")); os.environ["GENSEO_PUBLISHER_REEXEC"] = "1"
import genseo_config as cfg
from shopify_auth import pick

STORE_URL = "https://wellnessnest.co"


def vis_text(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def main():
    spec_p = sys.argv[1]; window = "--no-window" not in sys.argv and os.environ.get("GENSEO_LANDING_REAL_QA_WINDOW", "1") == "1"
    spec = json.load(open(os.path.join(ROOT, spec_p) if not os.path.isabs(spec_p) else spec_p))
    out = os.path.join(ROOT, "landing_drafts", spec["slug"]); pid = json.load(open(os.path.join(out, "shopify.json")))["page_id"]
    suffix = spec.get("template_suffix", "")
    shop, tok, _ = pick({"read_themes", "read_online_store_pages"})
    def get(path):
        r = urllib.request.Request(f"https://{shop}/admin/api/{cfg.API}/{path}", headers={"X-Shopify-Access-Token": tok})
        return json.load(urllib.request.urlopen(r, timeout=60))
    res = {"page_id": pid, "checks": {}, "fails": []}
    def check(name, ok, info=""):
        res["checks"][name] = {"ok": bool(ok), "info": info}
        if not ok: res["fails"].append(f"{name}: {info}")
    main_theme = get("themes.json?role=main")["themes"][0]
    key = f"templates/page.{suffix}.liquid"
    try:
        live_tpl = get(f"themes/{main_theme['id']}/assets.json?asset[key]={key}")["asset"].get("value", "")
    except Exception as e:
        live_tpl = None
    loc_p = os.path.join(ROOT, "templates", "landing", f"page.{suffix}.liquid")
    loc_tpl = open(loc_p).read() if os.path.exists(loc_p) else None
    sha = lambda s: hashlib.sha1(s.encode()).hexdigest()[:12] if s is not None else None
    check("template_in_main_theme", live_tpl is not None, f"{key} in theme {main_theme['id']} ({main_theme['name']})")
    check("template_matches_local", live_tpl is not None and live_tpl == loc_tpl,
          f"live {sha(live_tpl)} vs local {sha(loc_tpl)} (a CSS change needs a NEW suffix; never overwrite)")
    page = get(f"pages/{pid}.json")["page"]
    check("template_suffix", page.get("template_suffix") == suffix, f"page {page.get('template_suffix')!r} vs spec {suffix!r}")
    check("body_text_matches_local", vis_text(page["body_html"]) == vis_text(open(os.path.join(out, "body.html")).read()),
          "Shopify body_html visible text vs local body.html (old body pushed?)")
    srcs = re.findall(r'(?:src|srcset)="([^"]+)"', page["body_html"])
    check("images_on_cdn", srcs and all(s.startswith("https://cdn.shopify.com/") for s in srcs), f"{len(srcs)} srcs")
    res["was_hidden"] = not page.get("published_at")
    if window:
        if not page["handle"].startswith("gsl-preview-"):
            check("window_allowed", False, f"handle {page['handle']} is not gsl-preview-: no live window")
        else:
            url = f"{STORE_URL}/pages/{page['handle']}"
            tog = lambda s: subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "landing_preview_toggle.py"), s, str(pid)],
                                           capture_output=True, text=True, timeout=120)
            try:
                if res["was_hidden"]:
                    tog("on"); time.sleep(4)
                env = dict(os.environ, NODE_PATH=subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip())
                r = subprocess.run(["node", os.path.join(ROOT, "scripts", "landing_live_shot.mjs"), url, os.path.join(out, "real")],
                                   capture_output=True, text=True, timeout=600, env=env)
                facts = json.load(open(os.path.join(out, "real.json"))) if r.returncode == 0 else None
            finally:
                if res["was_hidden"]:
                    tog("off")
            after = get(f"pages/{pid}.json")["page"]
            check("hidden_again", (not after.get("published_at")) if res["was_hidden"] else True, f"published_at={after.get('published_at')}")
            if not facts:
                check("storefront_shot", False, (r.stderr or r.stdout)[-300:])
            else:
                res["storefront"] = facts
                for vp in ("desktop", "mobile"):
                    f = facts[vp]
                    check(f"{vp}_http", f["http"] == 200, str(f["http"]))
                    if spec.get("style") == "premium":
                        check(f"{vp}_premium_css", f["premium_markup"] and f["premium_css_applied"] not in (None, "0px"), str(f["premium_css_applied"]))
                    title = re.sub(r"<[^>]+>", "", (spec.get("offer") or {}).get("title", ""))
                    check(f"{vp}_offer_is_current", (title or "") in (f["offer_text"] or ""), f"offer box shows: {(f['offer_text'] or '')[:90]}")
                    check(f"{vp}_no_overflow", not f["overflow"], "")
                    check(f"{vp}_images_ok", not f["broken"], str(f["broken"][:2]))
                sc = facts["mobile"].get("sticky_check")
                if spec.get("sticky_cta"):
                    check("sticky_cta", sc and sc["top"] is not True and sc["after_bridge"] is True and sc["on_offer"] is not True, json.dumps(sc)[:200])
    res["verdict"] = "PASS" if not res["fails"] else "FAIL"
    json.dump(res, open(os.path.join(out, "real_qa.json"), "w"), indent=1, ensure_ascii=False)
    for k, v in res["checks"].items():
        print(("✓ " if v["ok"] else "✗ ") + k + (f"  {v['info']}" if not v["ok"] or k.startswith("template") else ""))
    print(f"REAL QA {res['verdict']}" + (f" ({len(res['fails'])} fail)" if res["fails"] else ""))
    sys.exit(0 if not res["fails"] else 1)


if __name__ == "__main__":
    main()

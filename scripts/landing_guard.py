#!/usr/bin/env python3
"""Daily landing-page guard (Kevin 2026-10-08): at most ONE GenSeo landing draft per day, on whichever Mac runs.

The two Macs share no writable state, so the STORE is the shared state: count Shopify pages whose handle starts
with 'gsl-' and that were CREATED today (Asia/Saigon calendar day, published or not).

  /usr/bin/python3 scripts/landing_guard.py            # prints the count + pages; exit 0 = slot free
  /usr/bin/python3 scripts/landing_guard.py --json
exit 0 = fewer than GENSEO_LANDING_DAILY_MAX (default 1) gsl- pages created today -> may build one
exit 3 = today's quota is used (a draft already exists) -> stand down
exit 1 = Shopify unreadable -> fail CLOSED (callers must not build)
Also used by landing_publisher.py right before it POSTs a NEW page when GENSEO_LANDING_DAILY=1.
"""
import datetime as dt, json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ.setdefault("GENSEO_PUBLISHER_REEXEC", "1")
ICT = dt.timezone(dt.timedelta(hours=7))
PREFIX = "gsl-"


def todays_pages():
    import genseo_config as cfg
    from shopify_auth import pick
    shop, token, src = pick({"read_online_store_pages"})
    start = dt.datetime.now(ICT).replace(hour=0, minute=0, second=0, microsecond=0)
    url = (f"https://{shop}/admin/api/{cfg.API}/pages.json?limit=250&published_status=any"
           f"&created_at_min={start.isoformat()}&fields=id,handle,title,created_at,published_at")
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"X-Shopify-Access-Token": token}), timeout=30))
    pages = [p for p in r.get("pages", []) if (p.get("handle") or "").startswith(PREFIX)
             and dt.datetime.fromisoformat(p["created_at"]).astimezone(ICT).date() == start.date()]
    return start.date().isoformat(), pages, src


def main():
    limit = int(os.environ.get("GENSEO_LANDING_DAILY_MAX", "1"))
    try:
        day, pages, src = todays_pages()
    except Exception as e:  # fail closed
        print(f"landing_guard: Shopify unreadable ({type(e).__name__}: {str(e)[:160]}) — fail closed")
        sys.exit(1)
    if "--json" in sys.argv:
        print(json.dumps({"day_ict": day, "limit": limit, "count": len(pages), "pages": pages, "auth": src}))
    else:
        for p in pages:
            print(f"  {p['id']} /pages/{p['handle']} created {p['created_at']} {'LIVE' if p.get('published_at') else 'unpublished'}")
        print(f"landing_guard: {len(pages)}/{limit} gsl- page(s) created {day} (ICT)")
    sys.exit(3 if len(pages) >= limit else 0)


if __name__ == "__main__":
    main()

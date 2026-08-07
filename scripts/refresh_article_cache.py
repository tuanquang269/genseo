import time
#!/usr/bin/env python3
"""Refresh the anti-cannibalization caches that topic_fitness.py + build_rich_tickets.py rely on:
existing_articles.json (all live blog article titles/handles, both blogs) and
existing_collections.json. Stale caches = the duplicate check misses newly-published pages, so
this must run periodically (wired into the daily cleaning task). Idempotent, read-only on Shopify."""
import json, os, re, urllib.request

ROOT = "~/genseo"
cfg = json.load(open(os.path.expanduser('~/.genseo/shopify_token.json')))
shop, token = cfg['shop'], cfg['access_token']
API = f"https://{shop}/admin/api/2026-04"


def get(url):
    for attempt in range(5):
        try:
            time.sleep(1.0)
            r = urllib.request.Request(url, headers={"X-Shopify-Access-Token": token})
            resp = urllib.request.urlopen(r)
            return json.load(resp), resp.headers.get('Link', '')
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                time.sleep(3.0 * (attempt + 1))
                continue
            raise


def main():
    arts = []
    for blog in ('100000000001', '100000000002'):
        url = f"{API}/blogs/{blog}/articles.json?limit=250&fields=id,title,handle"
        while url:
            d, link = get(url)
            arts += [{'id': a['id'], 'title': a['title'], 'handle': a['handle'], 'blog': blog} for a in d['articles']]
            m = re.search(r'<([^>]+)>;\s*rel="next"', link)
            url = m.group(1) if m else None
    json.dump(arts, open(f"{ROOT}/existing_articles.json", "w"))

    colls = []
    for kind in ('custom_collections', 'smart_collections'):
        d, _ = get(f"{API}/{kind}.json?limit=250&fields=id,title,handle")
        colls += [{'title': c['title'], 'handle': c['handle']} for c in d.get(kind, [])]
    json.dump(colls, open(f"{ROOT}/existing_collections.json", "w"))
    print(f"✓ cache refreshed: {len(arts)} articles, {len(colls)} collections")


if __name__ == '__main__':
    main()

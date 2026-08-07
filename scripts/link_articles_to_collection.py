#!/usr/bin/env python3
"""Append a 'Shop the range' link box to blog articles relevant to a collection —
internal-link equity for striking-distance collection pages.

APPEND-ONLY: the box is inserted just before the article's FAQ heading (or at the
end); existing content is never reworded. Skips frozen articles, articles that
already link to the collection, and never edits more than --limit articles per run.

Usage:
  python3 link_articles_to_collection.py <collection_handle> "<title regex>" --limit 12 [--apply]
Example:
  python3 link_articles_to_collection.py protein-powder "whey|protein powder|isolate|casein" --limit 12 --apply
"""
import argparse, json, os, re, sys, urllib.request, datetime

CONFIG_PATH = os.path.expanduser('~/.genseo/shopify_token.json')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOGS = {104008483131: 'news'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('collection_handle')
    ap.add_argument('pattern', help='case-insensitive regex matched against article titles')
    ap.add_argument('--limit', type=int, default=12)
    ap.add_argument('--apply', action='store_true', help='without this flag: dry-run, list only')
    a = ap.parse_args()

    auth = json.load(open(CONFIG_PATH))
    shop, token = auth['shop'], auth['access_token']

    def req(path, method='GET', payload=None):
        r = urllib.request.Request(f"https://{shop}/admin/api/2026-04/{path}",
            data=json.dumps(payload).encode() if payload else None, method=method,
            headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"})
        return urllib.request.urlopen(r)

    # collection title for the box heading
    col = json.loads(req(f"custom_collections.json?handle={a.collection_handle}&fields=id,title").read()).get('custom_collections', []) \
       or json.loads(req(f"smart_collections.json?handle={a.collection_handle}&fields=id,title").read()).get('smart_collections', [])
    if not col:
        print(f"✗ collection {a.collection_handle} not found"); sys.exit(1)
    col_title, col_url = col[0]['title'], f"/collections/{a.collection_handle}"

    frozen = set()
    ff = os.path.join(BASE_DIR, 'frozen_articles.txt')
    if os.path.exists(ff):
        frozen = {l.split('#')[0].strip() for l in open(ff) if l.split('#')[0].strip()}

    box = (f'\n<p class="genseo-collection-link">🛒 <strong>Ready to buy? '
           f'<a href="{col_url}">Shop the full {col_title} range in {{MARKET}}</a></strong> — '
           f'100% authentic, fast local delivery.</p>\n')

    pat = re.compile(a.pattern, re.I)
    edited = 0
    for blog in BLOGS:
        url = f"https://{shop}/admin/api/2026-04/blogs/{blog}/articles.json?limit=250&published_status=published&fields=id,title,handle,body_html"
        while url and edited < a.limit:
            r = req(url.replace(f"https://{shop}/admin/api/2026-04/", ""))
            data = json.loads(r.read())
            for art in data['articles']:
                if edited >= a.limit: break
                if str(art['id']) in frozen: continue
                if art['handle'].startswith('generated-article'): continue  # recovery artifacts, not worth link equity
                if not pat.search(art['title']): continue
                body = art['body_html'] or ''
                if col_url in body: continue  # already links to this collection
                m = re.search(r'<h2[^>]*>\s*(?:Frequently Asked|FAQs?)', body, re.I)
                new_body = (body[:m.start()] + box + body[m.start():]) if m else body + box
                print(f"{'EDIT' if a.apply else 'would edit'}: [{blog}] {art['handle']}")
                if a.apply:
                    req(f"blogs/{blog}/articles/{art['id']}.json", 'PUT',
                        {"article": {"id": art['id'], "body_html": new_body}})
                edited += 1
            url = None
            for part in r.headers.get('Link', '').split(','):
                if 'rel="next"' in part:
                    url = part[part.find('<')+1:part.find('>')]
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    if a.apply:
        with open(os.path.join(BASE_DIR, 'collection_seo_runs.log'), 'a') as f:
            f.write(f"{stamp} | linked {edited} articles -> {col_url}\n")
    print(f"{'✓ edited' if a.apply else 'dry-run:'} {edited} articles -> {col_url}")


if __name__ == '__main__':
    main()

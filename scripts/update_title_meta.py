#!/usr/bin/env python3
"""CTR-sprint tool: update ONLY the SEO title + meta description of a live Shopify
resource (article / product / collection / page) via the standard `global.title_tag`
/ `global.description_tag` metafields. Never touches body, H1, handle, or images —
so a cheap model literally cannot damage the page content with it.

Usage:
  python3 update_title_meta.py --type article --id 123 --blog 104008483131 \
      --keyword "meiji protein milk" --title "New SERP Title" --meta "New meta description."

Mechanical gates (exit 1, nothing written):
  - title must contain --keyword (case-insensitive) and be <=60 chars
  - meta must be 120-165 chars
  - frozen article IDs (frozen_articles.txt) are refused
Logs old->new to ctr_sprint_runs.log (reversible by re-running with the old values).
"""
import argparse, json, os, re, sys, urllib.request, datetime

CONFIG_PATH = os.path.expanduser('~/.genseo/shopify_token.json')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FREEZE_FILE = os.path.join(BASE_DIR, 'frozen_articles.txt')
LOG_FILE = os.path.join(BASE_DIR, 'ctr_sprint_runs.log')
API = '2026-04'

# REST metafield paths per resource type (articles are blog-scoped)
PATHS = {
    'article':    'blogs/{blog}/articles/{id}',
    'product':    'products/{id}',
    'collection': 'collections/{id}',
    'page':       'pages/{id}',
}


def req(shop, token, path, method='GET', payload=None):
    url = f"https://{shop}/admin/api/{API}/{path}"
    data = json.dumps(payload).encode() if payload else None
    r = urllib.request.Request(url, data=data, method=method,
        headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r).read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--type', required=True, choices=PATHS)
    ap.add_argument('--id', required=True)
    ap.add_argument('--blog', default='104008483131')
    ap.add_argument('--keyword', required=True, help='primary keyword — must appear in the new title')
    ap.add_argument('--title', required=True, help='new SEO title (<=60 chars)')
    ap.add_argument('--meta', required=True, help='new meta description (120-165 chars)')
    a = ap.parse_args()

    # ── normalize stray shell-escaped dollar signs (ticket examples show `S\$`; the shell
    # sometimes leaks the backslash or eats the `$` — heal both fields before validating) ──
    a.title = a.title.replace('\\$', '$')
    a.meta = a.meta.replace('\\$', '$')

    # ── gates ──
    errs = []
    if len(a.title) > 60: errs.append(f"title is {len(a.title)} chars (max 60)")
    if a.keyword.lower() not in a.title.lower(): errs.append(f'keyword "{a.keyword}" not in title')
    # No prices in the TITLE: at 60 chars an exact price gets truncated to junk ("from S$54")
    # and prices go stale. Prices belong in the meta description only.
    if re.search(r'(S\$|$|\$)\s?\d', a.title): errs.append("price in title — move the S$ price to the meta; titles must be evergreen (they truncate at 60 chars)")
    if not (120 <= len(a.meta) <= 165): errs.append(f"meta is {len(a.meta)} chars (need 120-165)")
    for b in ('bronson', 'transparent labs'):
        if b in (a.title + a.meta).lower(): errs.append(f'out-of-stock brand "{b}" mentioned')
    if a.type == 'article' and os.path.exists(FREEZE_FILE):
        with open(FREEZE_FILE) as f:
            frozen = {l.split('#')[0].strip() for l in f if l.split('#')[0].strip()}
        if a.id in frozen: errs.append(f"article {a.id} is FROZEN (frozen_articles.txt)")
    if errs:
        for e in errs: print(f"✗ {e}")
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        auth = json.load(f)
    shop, token = auth['shop'], auth['access_token']
    base = PATHS[a.type].format(blog=a.blog, id=a.id)

    # existing global.title_tag / description_tag metafields (update vs create)
    existing = {m['key']: m for m in req(shop, token, f"{base}/metafields.json?namespace=global").get('metafields', [])}
    old = {k: existing.get(k, {}).get('value', '(unset)') for k in ('title_tag', 'description_tag')}

    for key, value in (('title_tag', a.title), ('description_tag', a.meta)):
        mf = {"namespace": "global", "key": key, "type": "single_line_text_field", "value": value}
        if key in existing:
            req(shop, token, f"metafields/{existing[key]['id']}.json", 'PUT', {"metafield": {"id": existing[key]['id'], "value": value, "type": "single_line_text_field"}})
        else:
            req(shop, token, f"{base}/metafields.json", 'POST', {"metafield": mf})

    stamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"{stamp} | {a.type} {a.id} | kw={a.keyword} | title: {old['title_tag']!r} -> {a.title!r} | meta: {old['description_tag']!r} -> {a.meta!r}\n")
    print(f"✓ {a.type} {a.id} SEO updated")
    print(f"  title: {old['title_tag']} \n      -> {a.title}")
    print(f"  meta : -> {a.meta}")


if __name__ == '__main__':
    main()

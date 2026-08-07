#!/usr/bin/env python3
"""Prune DEAD articles: published pages earning ZERO Google impressions in 90 days
(GLOBAL, not just SG — a page with foreign traffic is not low-quality to Google and
is left alone). Dead weight dilutes sitewide quality post-May-2026 core update.

Guardrails:
  - only articles CREATED >100 days ago (young pages legitimately lack data)
  - global impressions == 0 (any impression anywhere = keep)
  - frozen IDs and generated-article-* recovery handles skipped
  - unpublish + 301 to the most related collection (keyword map), fallback blog index
  - --limit per run (default 40) so changes land in batches; fully logged/reversible

Usage: prune_dead.py [--apply] [--limit 40]
Log: backups/<date>/prune_log.json
"""
import argparse, datetime, json, os, re, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gsc_fetcher import get_service

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.expanduser('~/.genseo/shopify_token.json')
BLOGS = {104008483131: 'news'}
# keyword -> redirect-target collection (first match wins, checked in order)
TARGETS = [
    (r'whey|protein powder|isolate|casein|protein', '/collections/protein-powder'),
    (r'creatine', '/collections/creatine'),
    (r'gainer|bulk|mass', '/collections/mass-gainer'),
    (r'pre.?workout|energy|pump|caffeine', '/collections/pre-workout'),
    (r'vitamin|multivitamin|immune|immunity', '/collections/vitamin-wellness'),
    (r'collagen|beauty|skin|hair', '/collections/collagen'),
    (r'fat.?burn|weight.?loss|slim|diet|appetite', '/collections/fat-burner'),
    (r'bar|snack|cookie|meal replacement', '/collections/protein-bar-meal-replacement'),
    (r'shaker|bottle|owala', '/collections/shakers-bottle'),
    (r'sleep|melatonin|magnesium', '/collections/sleep-improvement'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--limit', type=int, default=40)
    a = ap.parse_args()

    svc = get_service()
    end = datetime.date.today() - datetime.timedelta(days=2)
    start = end - datetime.timedelta(days=90)
    rows = svc.searchanalytics().query(siteUrl='https://wellnessnest.co/', body={
        'startDate': str(start), 'endDate': str(end), 'dimensions': ['page'],
        'rowLimit': 25000}).execute().get('rows', [])  # GLOBAL: no country filter
    alive = set()
    for r in rows:
        u = r['keys'][0].split('#')[0]
        if '/blogs/' in u:
            alive.add(u.rstrip('/').split('/')[-1])

    auth = json.load(open(CONFIG_PATH))
    frozen = set()
    ff = os.path.join(BASE, 'frozen_articles.txt')
    if os.path.exists(ff):
        frozen = {l.split('#')[0].strip() for l in open(ff) if l.split('#')[0].strip()}
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=100)).isoformat()

    log, done = [], 0
    for blog, blogname in BLOGS.items():
        url = f"https://{auth['shop']}/admin/api/2026-04/blogs/{blog}/articles.json?limit=250&fields=id,handle,title,created_at&published_status=published"
        while url and done < a.limit:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"X-Shopify-Access-Token": auth['access_token']}))
            for art in json.loads(r.read())['articles']:
                if done >= a.limit:
                    break
                h = art['handle']
                if h in alive or str(art['id']) in frozen or h.startswith('generated-article'):
                    continue
                if art['created_at'] > cutoff:
                    continue
                text = (art['title'] + ' ' + h).lower()
                target = next((t for pat, t in TARGETS if re.search(pat, text)), f'/blogs/{blogname}')
                print(f"{'PRUNE' if a.apply else 'would prune'}: {h[:60]} → {target}")
                if a.apply:
                    hdr = {"X-Shopify-Access-Token": auth['access_token'], "Content-Type": "application/json"}
                    urllib.request.urlopen(urllib.request.Request(
                        f"https://{auth['shop']}/admin/api/2026-04/blogs/{blog}/articles/{art['id']}.json",
                        data=json.dumps({"article": {"id": art['id'], "published": False}}).encode(), method='PUT', headers=hdr))
                    red = urllib.request.urlopen(urllib.request.Request(
                        f"https://{auth['shop']}/admin/api/2026-04/redirects.json",
                        data=json.dumps({"redirect": {"path": f"/blogs/{blogname}/{h}", "target": target}}).encode(),
                        method='POST', headers=hdr))
                    log.append({"handle": h, "id": art['id'], "blog": blog, "target": target,
                                "redirect_id": json.loads(red.read())['redirect']['id']})
                done += 1
            url = None
            for p in r.headers.get('Link', '').split(','):
                if 'rel="next"' in p:
                    url = p[p.find('<')+1:p.find('>')]
    if a.apply and log:
        d = os.path.join(BASE, 'backups', datetime.date.today().isoformat())
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'prune_log.json'), 'a') as f:
            json.dump(log, f, indent=2)
    print(f"\n{'pruned' if a.apply else 'dry-run'}: {done} articles (limit {a.limit})")


if __name__ == '__main__':
    main()

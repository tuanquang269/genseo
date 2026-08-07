#!/usr/bin/env python3
"""Generate a CTR-sprint ticket list from GSC {{MARKET}} data.

Selects pages ranking pos 4-12 with >=100 SG impressions (28d) whose CTR is under
half the expected CTR for their position — i.e. pages that rank but don't win the
click. Each ticket is executable by a cheap model with ONE command
(scripts/update_title_meta.py), which never touches page content.

Usage: python3 scripts/build_ctr_tickets.py <output.md>
"""
import json, os, sys, urllib.request, collections, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gsc_fetcher import get_service

SITE = 'https://wellnessnest.co/'
CONFIG_PATH = os.path.expanduser('~/.genseo/shopify_token.json')
BLOGS = {104008483131: 'news'}
EXPECT = {1:0.25,2:0.15,3:0.10,4:0.065,5:0.05,6:0.04,7:0.03,8:0.025,9:0.02,10:0.018,11:0.015,12:0.012}
# brand-navigation pages: their "impressions" are mostly sitelinks on the brand query —
# a title rewrite would hurt navigation and win nothing.
EXCLUDE_PATHS = {'/', '/pages/about-us', '/pages/contact-us', '/pages/shopbycategory',
                 '/pages/warehouse-sale', '/collections/frontpage', '/collections/ultimate-sup',
                 '/collections'}
BRAND_QUERY_WORDS = ('your brand', 'your brand')


def shopify(path):
    auth = json.load(open(CONFIG_PATH))
    r = urllib.request.Request(f"https://{auth['shop']}/admin/api/2026-04/{path}",
                               headers={"X-Shopify-Access-Token": auth['access_token']})
    return json.loads(urllib.request.urlopen(r).read())


def article_index():
    """handle -> (blog_id, article_id, title), paginated across both blogs"""
    idx = {}
    auth = json.load(open(CONFIG_PATH))
    for blog in BLOGS:
        url = f"https://{auth['shop']}/admin/api/2026-04/blogs/{blog}/articles.json?limit=250&fields=id,handle,title"
        while url:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"X-Shopify-Access-Token": auth['access_token']}))
            for a in json.loads(r.read())['articles']:
                idx[a['handle']] = (blog, a['id'], a['title'])
            url = None
            for part in r.headers.get('Link', '').split(','):
                if 'rel="next"' in part:
                    url = part[part.find('<')+1:part.find('>')]
    return idx


def main():
    out_path = sys.argv[1]
    svc = get_service()
    end = datetime.date.today() - datetime.timedelta(days=2)
    start = end - datetime.timedelta(days=28)
    rows = svc.searchanalytics().query(siteUrl=SITE, body={
        'startDate': str(start), 'endDate': str(end),
        'dimensions': ['page', 'query'],
        'dimensionFilterGroups': [{'filters': [{'dimension':'country','operator':'equals','expression':'{{COUNTRY_CODE}}'}]}],
        'rowLimit': 25000}).execute().get('rows', [])

    pages = collections.defaultdict(list)
    for r in rows:
        url = r['keys'][0].split('#')[0]
        pages[url].append(r)

    frozen = set()
    ff = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frozen_articles.txt')
    if os.path.exists(ff):
        frozen = {l.split('#')[0].strip() for l in open(ff) if l.split('#')[0].strip()}

    art_idx = article_index()
    candidates = []
    for url, qrows in pages.items():
        path = url.replace('https://wellnessnest.co', '') or '/'
        if path in EXCLUDE_PATHS:
            continue
        # drop brand-navigation queries before judging the page
        qrows = [r for r in qrows if not any(b in r['keys'][1] for b in BRAND_QUERY_WORDS)]
        imp = sum(r['impressions'] for r in qrows)
        clk = sum(r['clicks'] for r in qrows)
        if imp < 100:
            continue
        pos = sum(r['position'] * r['impressions'] for r in qrows) / imp
        if not (3.5 <= pos <= 12.5):
            continue
        exp_ctr = EXPECT.get(round(pos), 0.012)
        if clk / imp >= 0.5 * exp_ctr:
            continue  # CTR already acceptable for this position
        missed = exp_ctr * imp - clk
        candidates.append((missed, url, path, pos, imp, clk, sorted(qrows, key=lambda r: -r['impressions'])[:5]))
    candidates.sort(key=lambda c: -c[0])

    tickets, skipped = [], []
    for missed, url, path, pos, imp, clk, top in candidates:
        handle = path.rstrip('/').split('/')[-1]
        if '/blogs/' in path:
            if handle not in art_idx:
                skipped.append(f"{path} (article not found)"); continue
            blog, aid, title = art_idx[handle]
            if str(aid) in frozen:
                skipped.append(f"{path} (FROZEN)"); continue
            rtype, rid, extra = 'article', aid, f"--blog {blog} "
        elif '/products/' in path:
            res = shopify(f"products.json?handle={handle}&fields=id,title").get('products', [])
            if not res: skipped.append(f"{path} (product not found)"); continue
            rtype, rid, title, extra = 'product', res[0]['id'], res[0]['title'], ''
        elif '/collections/' in path:
            res = shopify(f"custom_collections.json?handle={handle}&fields=id,title").get('custom_collections', []) \
               or shopify(f"smart_collections.json?handle={handle}&fields=id,title").get('smart_collections', [])
            if not res: skipped.append(f"{path} (collection not found)"); continue
            rtype, rid, title, extra = 'collection', res[0]['id'], res[0]['title'], ''
        elif '/pages/' in path:
            res = shopify(f"pages.json?handle={handle}&fields=id,title").get('pages', [])
            if not res: skipped.append(f"{path} (page not found)"); continue
            rtype, rid, title, extra = 'page', res[0]['id'], res[0]['title'], ''
        else:
            skipped.append(f"{path} (unknown type)"); continue
        tickets.append(dict(missed=missed, url=url, pos=pos, imp=imp, clk=clk, top=top,
                            rtype=rtype, rid=rid, title=title, extra=extra))

    with open(out_path, 'w') as f:
        f.write(f"""# 🎯 CTR Sprint Tickets — generated {datetime.date.today()} (GSC SG {start} → {end})

**Goal:** these pages already rank pos 4–12 in {{MARKET}} but lose the click. Fix = a better
SERP title + meta description. **Nothing else.**

## ⛔ HARD RULES (read before every ticket)
1. Your ONLY action per ticket = write a new SEO title + meta, then run the ONE command given.
   Do NOT edit the article body, do NOT use the publisher, Shopify MCP, GraphQL, or any other tool.
2. `update_title_meta.py` changes only the SERP title/meta (SEO metafields) — the on-page H1 and
   content stay untouched. It is the gate: if it prints ✗, fix the title/meta and re-run.
3. TITLE rules (WIN THE CLICK): ≤60 chars · primary keyword at the front · ONE concrete hook
   (an S$ price, a number, "(2026)", or a question) · NEVER "Ultimate Guide"/"Complete Guide"/
   "Everything You Need" boilerplate · must clearly beat the current title, not reword it.
4. META rules: 120–165 chars · first sentence answers the query · add one differentiator
   ({{CURRENCY}} price, "100% authentic", "next-day SG delivery").
5. Never mention Bronson or Transparent Labs (not in stock).
6. After ✓, mark the ticket `[DONE YYYY-MM-DD]` and record the new title in the ticket.

> 💡 **How to run:** operator says *"continue with the next 3 tickets in jul27-ctr-sprint-tickets.md"*.
> Find the first `[PENDING]` ticket, do it, mark it, continue.

---
""")
        for i, t in enumerate(tickets, 1):
            qlines = '\n'.join(f"  - `{r['keys'][1]}` — pos {r['position']:.1f}, {r['impressions']} imp, {r['clicks']} clicks"
                               for r in t['top'])
            kw = t['top'][0]['keys'][1]
            f.write(f"""## Ticket {i} — [PENDING]
- **URL**: {t['url']}
- **Type/ID**: {t['rtype']} {t['rid']}
- **Now**: pos {t['pos']:.1f} · {t['imp']} imp · {t['clk']} clicks (28d SG) · missing ~{t['missed']:.0f} clicks/28d
- **CURRENT TITLE**: {t['title']}
- **PRIMARY KEYWORD**: `{kw}`
- **Top SG queries**:
{qlines}
- **RUN** (fill in your new title + meta):
```
python3 /Users/kevinkreative/genseo/scripts/update_title_meta.py --type {t['rtype']} --id {t['rid']} {t['extra']}--keyword "{kw}" --title "NEW TITLE HERE" --meta "NEW META HERE"
```
- **Result**: (record new title after ✓)

---
""")
    print(f"✓ {len(tickets)} tickets -> {out_path}")
    for s in skipped: print(f"  skipped: {s}")


if __name__ == '__main__':
    main()

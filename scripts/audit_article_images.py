#!/usr/bin/env python3
"""
audit_article_images.py — post-publish detector for the "no inline images" regression (2026-07-26).

The STEP 6 validator now HARD-fails drafts with <3 inline images, but the cheap model has a history
of skipping gates / publishing via the wrong path (Shopify MCP) — so this is defense-in-depth: it
reads the LIVE published articles and flags any with fewer than MIN inline body images, independent
of how they were published. Wire the --recent form into daily cleaning so an image-less article can
never sit live undetected again.

Hero/cover is stored as article.image (NOT body_html), and publisher spacers are display:none, so
real in-body <img> = actual inline product images.

Usage:
  audit_article_images.py --recent 48        # articles published/updated in last 48h with <3 imgs
  audit_article_images.py --limit 60         # scan newest 60 (default)
  audit_article_images.py --min 3            # threshold (default 3)
  audit_article_images.py --ticket out.md    # also write a regeneration ticket for the flagged ones
"""
import json, urllib.request, sys, datetime

from genseo_config import SHOP, TOKEN, API
BLOGS={"nutrition":100000000001, "training":100000000002}
import re

def api(url):
    req=urllib.request.Request(url, headers={"X-Shopify-Access-Token":TOKEN})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())

def inline_imgs(body):
    imgs=re.findall(r'<img[^>]*>', body or "")
    return [i for i in imgs if 'display:none' not in i.lower() and 'spacer' not in i.lower()]

def main():
    a=sys.argv
    MIN=int(a[a.index('--min')+1]) if '--min' in a else 3
    limit=int(a[a.index('--limit')+1]) if '--limit' in a else 60
    recent_h=int(a[a.index('--recent')+1]) if '--recent' in a else None
    since=a[a.index('--since')+1] if '--since' in a else None   # created_at >= YYYY-MM-DD
    ticket=a[a.index('--ticket')+1] if '--ticket' in a else None
    cutoff=None
    if recent_h:
        cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=recent_h))

    flagged=[]
    for bname, bid in BLOGS.items():
        arts=api(f"https://{SHOP}/admin/api/{API}/blogs/{bid}/articles.json?limit={limit}&fields=id,title,handle,created_at,updated_at,image,body_html").get('articles',[])
        for art in arts:
            if cutoff:
                ts=art.get('updated_at') or art.get('created_at')
                if ts and datetime.datetime.fromisoformat(ts) < cutoff:
                    continue
            if since and (art.get('created_at') or '')[:10] < since:
                continue
            n=len(inline_imgs(art.get('body_html')))
            if n < MIN:
                flagged.append({"id":art['id'],"blog":bname,"handle":art['handle'],
                                "title":art['title'],"date":(art.get('created_at') or '')[:10],"imgs":n})
    flagged.sort(key=lambda x:x['date'], reverse=True)
    scope=f"last {recent_h}h" if recent_h else f"newest {limit}/blog"
    print(f"=== image audit ({scope}, min {MIN} inline imgs) — {len(flagged)} article(s) UNDER threshold ===")
    for f in flagged:
        print(f"  {f['date']}  imgs={f['imgs']}  id={f['id']}  {f['title'][:52]}")

    if ticket and flagged:
        L=[f"# 🖼️ IMAGE REGENERATION TICKET — {len(flagged)} articles below {MIN} inline images",
           f"# Generated {datetime.date.today().isoformat()} by audit_article_images.py. These published articles",
           "# have too few in-body product images (the ~Jul22 regression). For EACH article:",
           "#   1. Fetch the LIVE body (it is the source of truth) and save it as a markdown draft.",
           "#   2. Per SKILL genseo-auto-publish STEP 5, generate 1 lifestyle image PER product discussed",
           "#      (image-to-image from the real product photo; NO hero — the cover already exists).",
           "#   3. Insert each as `![alt](/ABSOLUTE/local/path.png)` in that product's section. LOCAL paths only",
           "#      — never pre-baked CDN URLs (publisher uploads local files and rewrites them).",
           "#   4. Re-publish with:  python3 ~/genseo/scripts/shopify_publisher.py \\",
           "#         update <draft.md> 100000000001 <ARTICLE_ID>",
           "#      (NOT patch_images.py — that only handles its own hardcoded ticket map, not arbitrary IDs.)",
           "# Keep title, body copy, schema and author UNCHANGED — this is IMAGES-ONLY (insert), append-only.",
           "# Verify after each: python3 ~/genseo/scripts/verify_published.py <ARTICLE_ID> 100000000001",
           "# Re-run `audit_article_images.py --since 2026-07-22` at the end; the count must drop to 0.", ""]
        for f in flagged:
            L.append(f"- [ ] `{f['id']}` ({f['blog']}, {f['date']}, {f['imgs']} imgs) — {f['title']}")
            L.append(f"      /blogs/{f['blog']}/{f['handle']}")
        open(ticket,"w").write("\n".join(L))
        print(f"\nRegeneration ticket -> {ticket}")

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""
fix_broken_title_articles.py — Fix articles whose YAML front-matter leaked into the
body (title stuck as 'Generated Article'). Parses the leaked block, sets the real
title + SEO metafields, strips the front-matter block from body_html.

Dry-run by default; --apply to push. Scans ALL nutrition+training articles for the
'Generated Article' title OR a leaked 'title:' block at the top of the body.
"""
import json, urllib.request, re, sys, datetime, os

from genseo_config import SHOP, TOKEN, API
BLOGS={"news4008483131}
ROOT="/Users/kevinkreative/genseo"
LOG=f"{ROOT}/backups/{datetime.date.today().strftime('%Y%m%d')}/title_fix_log.json"

def api(url, data=None, method="GET"):
    req=urllib.request.Request(url, data=(json.dumps(data).encode() if data else None), method=method,
        headers={"X-Shopify-Access-Token":TOKEN,"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())

def paginate(blog_id):
    out=[]; url=f"https://{SHOP}/admin/api/{API}/blogs/{blog_id}/articles.json?limit=250&fields=id,title,handle,body_html,published_at"
    while url:
        req=urllib.request.Request(url, headers={"X-Shopify-Access-Token":TOKEN})
        res=urllib.request.urlopen(req); d=json.loads(res.read())
        out.extend(d['articles'])
        nxt=None
        for part in res.headers.get('Link','').split(','):
            if 'rel="next"' in part: nxt=part[part.find('<')+1:part.find('>')]
        url=nxt
    return out

def parse_frontmatter(body):
    """Extract title/seo_title/seo_description from a leaked front-matter block."""
    fields={}
    for key in ['title','seo_title','seo_description']:
        m=re.search(rf'{key}:\s*"([^"]+)"', body)
        if m: fields[key]=m.group(1)
    return fields

def strip_frontmatter(body):
    # remove leading <hr>...front-matter...<hr> block (the leaked YAML)
    # pattern: optional <hr>, a <p> containing title:/seo_title:/status:, then <hr>
    new=re.sub(r'^\s*(<hr\s*/?>)?\s*<p>\s*title:.*?status:\s*"[^"]*"\s*</p>\s*(<hr\s*/?>)?',
               '', body, count=1, flags=re.S|re.I)
    return new.strip()

def main():
    apply="--apply" in sys.argv
    print(f"=== fix_broken_title_articles.py — {'APPLY' if apply else 'DRY-RUN'} ===\n")
    log=[]
    for bname,bid in BLOGS.items():
        for a in paginate(bid):
            body=a.get('body_html') or ''
            broken = a['title'].strip()=='Generated Article' or bool(re.match(r'^\s*(<hr[^>]*>)?\s*<p>\s*title:\s*"', body, re.I))
            if not broken: continue
            fm=parse_frontmatter(body)
            if not fm.get('title'):
                print(f"[{a['id']}] '{a['title']}' — broken but couldn't parse title; SKIP manual\n"); continue
            new_body=strip_frontmatter(body)
            print(f"[{bname}/{a['handle']}] id={a['id']}")
            print(f"   title : {a['title']!r} -> {fm['title']!r}")
            print(f"   seo   : {fm.get('seo_title','(none)')[:60]}")
            print(f"   body  : {len(body)} -> {len(new_body)} chars (stripped front-matter)")
            if apply:
                # update title + body
                api(f"https://{SHOP}/admin/api/{API}/blogs/{bid}/articles/{a['id']}.json",
                    {"article":{"id":a['id'],"title":fm['title'],"body_html":new_body}}, "PUT")
                # SEO metafields
                for k,mfkey in [('seo_title','title_tag'),('seo_description','description_tag')]:
                    if fm.get(k):
                        api(f"https://{SHOP}/admin/api/{API}/articles/{a['id']}/metafields.json",
                            {"metafield":{"namespace":"global","key":mfkey,"value":fm[k],"type":"single_line_text_field"}}, "POST")
                print("   ✓ APPLIED")
                log.append({"id":a['id'],"old_title":a['title'],"new_title":fm['title']})
            print()
    if apply and log:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        json.dump(log, open(LOG,"w"), indent=2)
        print(f"Fixed {len(log)} articles -> logged to {LOG}")
    elif not apply:
        print("Re-run with --apply to fix.")

if __name__=="__main__":
    main()

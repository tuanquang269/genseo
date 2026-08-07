#!/usr/bin/env python3
"""
expand_article.py — Surgically enrich ONE article: insert a hand-written enrichment
HTML block (comparison table + $pricing + internal links) before the
'About the Author' section, append FAQPage schema, and align the Article schema
author from the generic Org to the named Person.

Reads enrichment HTML from a file. Dry-run by default; --apply to push.
Usage: python3 expand_article.py <article_id> <blog_id> <enrichment_html_file> <author_name> [--apply]
"""
import json, urllib.request, sys, re

from genseo_config import SHOP, TOKEN, API

def api(url, data=None, method="GET"):
    req=urllib.request.Request(url, data=(json.dumps(data).encode() if data else None), method=method,
        headers={"X-Shopify-Access-Token":TOKEN,"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())

def main():
    aid=sys.argv[1]; bid=sys.argv[2]; enrich_file=sys.argv[3]; author=sys.argv[4]
    apply="--apply" in sys.argv
    enrich=open(enrich_file).read()

    a=api(f"https://{SHOP}/admin/api/{API}/blogs/{bid}/articles/{aid}.json")['article']
    body=a['body_html']
    orig_words=len(re.sub(r'<[^>]*>',' ',body).split())

    # 1) insert enrichment before "About the Author" (h3 or h2)
    m=re.search(r'(<h[23][^>]*>\s*(?:<strong>)?\s*About the Author)', body, re.I)
    if m:
        new_body=body[:m.start()] + enrich + "\n" + body[m.start():]
    else:
        # fallback: insert before the closing ld+json script
        idx=body.find('<script type="application/ld+json">')
        new_body=(body[:idx]+enrich+"\n"+body[idx:]) if idx>=0 else body+enrich

    # 2) align Article schema author Organization -> Person (named)
    new_body=re.sub(
        r'"author":\s*\{\s*"@type":\s*"Organization",\s*"name":\s*"[^"]*"\s*\}',
        f'"author": {{"@type": "Person", "name": "{author}"}}',
        new_body)

    new_words=len(re.sub(r'<[^>]*>',' ',new_body).split())
    print(f"article {aid}: {a['title'][:55]}")
    print(f"  words: {orig_words} -> {new_words}  (+{new_words-orig_words})")
    print(f"  enrichment inserted before About-the-Author: {'About the Author' in body}")
    print(f"  FAQPage in enrichment: {'FAQPage' in enrich}")
    print(f"  author aligned to: {author}")
    if apply:
        api(f"https://{SHOP}/admin/api/{API}/blogs/{bid}/articles/{aid}.json",
            {"article":{"id":int(aid),"body_html":new_body}}, "PUT")
        print("  ✅ APPLIED")
    else:
        print("  (dry-run) add --apply to push")

if __name__=="__main__":
    main()

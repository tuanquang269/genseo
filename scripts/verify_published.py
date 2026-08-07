#!/usr/bin/env python3
"""
verify_published.py — POST-PUBLISH gate. Fetches the LIVE article from Shopify and
confirms the publish actually added everything (schema, author, table). This catches the
failure where a model publishes via the wrong path (MCP/GraphQL/curl) that skips schema.

Usage: python3 verify_published.py <ARTICLE_ID> [BLOG_ID]
Exit 0 = live article is good. Exit 1 = something missing → re-publish via the python publisher.
"""
import sys, json, urllib.request, re

from genseo_config import SHOP, TOKEN, API

def main():
    aid=sys.argv[1]
    blog=sys.argv[2] if len(sys.argv)>2 else "104008483131"
    req=urllib.request.Request(f"https://{SHOP}/admin/api/{API}/blogs/{blog}/articles/{aid}.json",
        headers={"X-Shopify-Access-Token":TOKEN})
    a=json.loads(urllib.request.urlopen(req).read())["article"]
    b=a.get("body_html") or ""
    fails=[]
    if a.get("title","").strip() in ("","Generated Article"): fails.append("title is empty/'Generated Article'")
    if "FAQPage" not in b: fails.append("no FAQPage schema in live body (publish path skipped schema → use shopify_publisher.py)")
    if "application/ld+json" not in b: fails.append("no JSON-LD schema at all (wrong publish path)")
    if '"@type": "Person"' not in b and '"@type":"Person"' not in b:
        fails.append("Article schema author is not a named Person")
    if "<table" not in b: fails.append("no comparison <table> in live body")
    if not a.get("author") or a["author"].strip()=="Your Brand Research Team":
        fails.append(f"author field is generic ('{a.get('author')}')")

    print(f"=== VERIFY LIVE article {aid} ===")
    print(f"  title: {a.get('title')}")
    print(f"  handle: {a.get('handle')}")
    print(f"  author: {a.get('author')}")
    print(f"  FAQPage:{('FAQPage' in b)}  ld+json:{('application/ld+json' in b)}  table:{('<table' in b)}")
    if fails:
        print("FAILED:"); [print("  ✗ "+f) for f in fails]
        print("\nRESULT: ✗ Re-publish with: python3 /Users/kevinkreative/genseo/scripts/shopify_publisher.py update <draft.md> "+blog+" "+aid)
        sys.exit(1)
    print("\nRESULT: ✓ Live article verified — schema, author, table all present.")
    sys.exit(0)

if __name__=="__main__":
    main()

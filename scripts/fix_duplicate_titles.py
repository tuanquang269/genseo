"""
Fix Duplicate Titles — Batch Script (v2)
Fetches articles one page at a time (10 per page), checks for duplicate H1,
and strips it from body_html.
"""
import json
import os
import re
import sys
import urllib.request
import time

CONFIG_PATH = os.path.expanduser("~/.genseo/shopify_token.json")
BLOG_ID = sys.argv[1] if len(sys.argv) > 1 else "104008483131"

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def fetch_articles_page(shop, token, blog_id, since_id=0):
    """Fetch one page of articles (10 at a time)."""
    url = f"https://{shop}/admin/api/2026-04/blogs/{blog_id}/articles.json?limit=10&since_id={since_id}"
    req = urllib.request.Request(url, headers={"X-Shopify-Access-Token": token})
    res = urllib.request.urlopen(req, timeout=30)
    data = json.loads(res.read())
    return data.get("articles", [])

def has_duplicate_h1(title, body_html):
    """Check if body_html contains an <h1> that matches the article title."""
    if not body_html:
        return False
    h1_match = re.search(r'<h1>(.*?)</h1>', body_html, re.IGNORECASE | re.DOTALL)
    if not h1_match:
        return False
    h1_text = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
    return h1_text.lower() == title.strip().lower()

def strip_h1_from_body(body_html):
    """Remove the first <h1>...</h1> from body_html."""
    return re.sub(r'\s*<h1>.*?</h1>\s*', '', body_html, count=1, flags=re.IGNORECASE | re.DOTALL)

def update_article_body(shop, token, blog_id, article_id, new_body):
    """Update just the body_html of an article."""
    url = f"https://{shop}/admin/api/2026-04/blogs/{blog_id}/articles/{article_id}.json"
    payload = json.dumps({"article": {"id": article_id, "body_html": new_body}}).encode()
    req = urllib.request.Request(url, data=payload, 
                                 headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"},
                                 method="PUT")
    res = urllib.request.urlopen(req, timeout=30)
    return json.loads(res.read())

def main():
    config = load_config()
    shop = config["shop"]
    token = config["access_token"]
    
    print(f"🔍 Scanning articles in blog {BLOG_ID} for duplicate H1 titles...\n")
    
    fixed = 0
    skipped = 0
    errors = 0
    since_id = 0
    page = 0
    
    while True:
        page += 1
        print(f"--- Page {page} (since_id={since_id}) ---")
        try:
            articles = fetch_articles_page(shop, token, BLOG_ID, since_id)
        except Exception as e:
            print(f"  ❌ Fetch failed: {e}")
            break
        
        if not articles:
            print("  No more articles.")
            break
        
        for art in articles:
            aid = art["id"]
            title = art.get("title", "")
            body = art.get("body_html", "")
            
            if has_duplicate_h1(title, body):
                print(f"  🔧 FIXING: [{aid}] {title[:60]}...")
                new_body = strip_h1_from_body(body)
                try:
                    update_article_body(shop, token, BLOG_ID, aid, new_body)
                    print(f"     ✅ H1 stripped from body.")
                    fixed += 1
                    time.sleep(0.5)  # Rate limit
                except Exception as e:
                    print(f"     ❌ Failed: {e}")
                    errors += 1
            else:
                print(f"  ⏭  OK: [{aid}] {title[:60]}")
                skipped += 1
        
        since_id = articles[-1]["id"]
        time.sleep(0.5)  # Rate limit between pages
    
    print(f"\n{'='*60}")
    print(f"  📊 BATCH FIX RESULTS")
    print(f"  ✅ Fixed:   {fixed} articles (duplicate H1 removed)")
    print(f"  ⏭  OK:      {skipped} articles (no duplicate)")
    print(f"  ❌ Errors:  {errors}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

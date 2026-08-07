#!/usr/bin/env python3
"""
fix_duplicate_h1.py
Strips the leading <h1> tag from article body_html for all affected articles.
Shopify theme renders the title separately — having <h1> in body causes duplicates.
"""

import json, os, re, requests, time

TOKEN_FILE = os.path.expanduser('~/.genseo/shopify_token.json')
BLOG_ID = 104008483131

with open(TOKEN_FILE) as f:
    creds = json.load(f)

shop = creds['shop']
token = creds['access_token']
headers = {'X-Shopify-Access-Token': token, 'Content-Type': 'application/json'}

def get_all_articles():
    articles = []
    url = f'https://{shop}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json?limit=250'
    resp = requests.get(url, headers=headers)
    articles.extend(resp.json().get('articles', []))
    return articles

def strip_leading_h1(body_html):
    """Remove the first <h1>...</h1> tag if it's at the very start of the body."""
    stripped = body_html.strip()
    # Match <h1> at the start (with optional attributes)
    match = re.match(r'^<h1[^>]*>.*?</h1>\s*', stripped, re.DOTALL | re.IGNORECASE)
    if match:
        return stripped[match.end():].strip()
    return None  # Not affected, return None to skip

def fix_article(article):
    art_id = article['id']
    title = article['title'][:65]
    body = article.get('body_html', '')
    
    new_body = strip_leading_h1(body)
    if new_body is None:
        return False  # Not affected
    
    # Push update
    payload = {'article': {'id': art_id, 'body_html': new_body}}
    url = f'https://{shop}/admin/api/2024-01/blogs/{BLOG_ID}/articles/{art_id}.json'
    resp = requests.put(url, headers=headers, json=payload)
    
    if resp.status_code == 200:
        print(f'  ✅ Fixed: [{art_id}] {title}')
        return True
    else:
        print(f'  ❌ Failed ({resp.status_code}): [{art_id}] {title}')
        print(f'     Response: {resp.text[:200]}')
        return False

print('🔍 Fetching all articles...')
all_articles = get_all_articles()
print(f'   Found {len(all_articles)} articles total\n')

fixed = 0
skipped = 0
failed = 0

for i, article in enumerate(all_articles):
    body = article.get('body_html', '')
    if not body.strip().startswith('<h1'):
        skipped += 1
        continue
    
    success = fix_article(article)
    if success:
        fixed += 1
    else:
        failed += 1
    
    # Rate limit: stay well under 2 req/sec
    time.sleep(0.6)

print(f'\n📊 Done!')
print(f'   ✅ Fixed:   {fixed}')
print(f'   ⏭  Skipped: {skipped}')
print(f'   ❌ Failed:  {failed}')

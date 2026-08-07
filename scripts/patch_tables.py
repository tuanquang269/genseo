import json
import urllib.request
import re
import sys
import os

CONFIG_PATH = os.path.expanduser('~/.genseo/shopify_token.json')
BLOG_ID = "100000000001"

def main():
    if not os.path.exists(CONFIG_PATH):
        print("Error: auth.json not found.")
        sys.exit(1)
        
    with open(CONFIG_PATH, 'r') as f:
        auth_data = json.load(f)
        
    shop = auth_data['shop']
    token = auth_data['access_token']
    
    print(f"Connecting to {shop} (Blog ID: {BLOG_ID})...")
    
    # Step 1: Fetch the most recent 50 articles
    list_url = f"https://{shop}/admin/api/2026-04/blogs/{BLOG_ID}/articles.json?limit=50"
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    
    req = urllib.request.Request(list_url, headers=headers)
    try:
        response = urllib.request.urlopen(req)
        res_data = json.loads(response.read())
    except Exception as e:
        print(f"Failed to fetch articles: {e}")
        sys.exit(1)
        
    articles = res_data.get("articles", [])
    print(f"Found {len(articles)} articles in blog. Checking for tables...")
    
    table_style = """<style>
.article-table-wrapper {
  width: 100% !important;
  overflow-x: auto !important;
  -webkit-overflow-scrolling: touch !important;
  margin: 20px 0 !important;
}
.article-table-wrapper table {
  width: 100% !important;
  border-collapse: collapse !important;
  min-width: 600px !important;
}
</style>
"""

    patched_count = 0
    for article in articles:
        article_id = article["id"]
        title = article["title"]
        body_html = article.get("body_html", "")
        
        if "<table>" in body_html:
            # Check if it's already wrapped
            if '<div class="article-table-wrapper">' in body_html:
                print(f"  - '{title}' (ID: {article_id}) already contains responsive table wrap.")
                continue
                
            print(f"  * Patching tables in '{title}' (ID: {article_id})...")
            
            # Wrap tables
            new_body = re.sub(
                r'(?<!<div class="article-table-wrapper">)<table>',
                r'<div class="article-table-wrapper"><table>',
                body_html
            )
            new_body = re.sub(
                r'</table>(?!</div>)',
                r'</table></div>',
                new_body
            )
            
            # Prepend table_style
            if ".article-table-wrapper" not in new_body:
                new_body = table_style + new_body
                
            # Step 2: Send PUT request to update article
            update_url = f"https://{shop}/admin/api/2026-04/blogs/{BLOG_ID}/articles/{article_id}.json"
            update_payload = {
                "article": {
                    "id": article_id,
                    "body_html": new_body
                }
            }
            
            update_req = urllib.request.Request(
                update_url,
                data=json.dumps(update_payload).encode('utf-8'),
                headers=headers,
                method="PUT"
            )
            try:
                urllib.request.urlopen(update_req)
                print(f"    ✓ Successfully updated and patched table style on storefront!")
                patched_count += 1
            except Exception as e:
                print(f"    ✗ Failed to update article: {e}")
                
    print(f"\nCompleted! Patched and updated {patched_count} active article(s) on the live storefront.")

if __name__ == "__main__":
    main()

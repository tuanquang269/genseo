import sys
import json
import os
import urllib.request
import urllib.parse
import time

CONFIG_PATH = os.path.expanduser("~/.genseo/shopify_token.json")

def bulk_update_author(blog_id):
    if not os.path.exists(CONFIG_PATH):
        print("Error: Not authenticated.")
        sys.exit(1)
        
    with open(CONFIG_PATH, 'r') as f:
        auth_data = json.load(f)
        
    shop = auth_data['shop']
    token = auth_data['access_token']
    
    # Fetch articles
    url = f"https://{shop}/admin/api/2026-04/blogs/{blog_id}/articles.json?limit=250"
    req = urllib.request.Request(url, headers={"X-Shopify-Access-Token": token})
    try:
        res = urllib.request.urlopen(req)
        data = json.loads(res.read())
        articles = data.get('articles', [])
        
        print(f"Found {len(articles)} articles in blog {blog_id}.")
        updated_count = 0
        for article in articles:
            article_id = article['id']
            current_author = article.get('author', '')
            
            if current_author != 'Author One':
                print(f"Updating '{article['title']}'...")
                
                update_url = f"https://{shop}/admin/api/2026-04/blogs/{blog_id}/articles/{article_id}.json"
                payload = {
                    "article": {
                        "id": article_id,
                        "author": "Author One"
                    }
                }
                
                update_req = urllib.request.Request(
                    update_url, 
                    data=json.dumps(payload).encode('utf-8'), 
                    headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"},
                    method='PUT'
                )
                urllib.request.urlopen(update_req)
                updated_count += 1
                time.sleep(0.5) # prevent API rate limits
                
        print(f"Done! Successfully updated author to 'Author One' for {updated_count} articles.")
        
    except Exception as e:
        print(f"Failed: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode())
        sys.exit(1)

if __name__ == "__main__":
    bulk_update_author("104008483131")

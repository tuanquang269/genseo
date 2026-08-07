import os
import json
import urllib.request
import random
import string

CONFIG_PATH = os.path.expanduser("~/.genseo/shopify_token.json")

def setup_indexnow():
    with open(CONFIG_PATH, 'r') as f:
        auth = json.load(f)
    shop, token = auth['shop'], auth['access_token']

    # 1. Generate 32-char key
    key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
    print(f"Generated IndexNow Key: {key}")

    # 2. Get main theme
    req = urllib.request.Request(f"https://{shop}/admin/api/2026-04/themes.json", headers={"X-Shopify-Access-Token": token})
    themes = json.loads(urllib.request.urlopen(req).read())['themes']
    theme_id = next(t['id'] for t in themes if t['role'] == 'main')

    # 3. Create page.indexnow.liquid template
    template_content = "{% layout none %}{{ page.content | strip_html }}"
    url = f"https://{shop}/admin/api/2026-04/themes/{theme_id}/assets.json"
    payload = {
        "asset": {
            "key": "templates/page.indexnow.liquid",
            "value": template_content
        }
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), 
                                 headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"},
                                 method='PUT')
    urllib.request.urlopen(req)
    print("Created template 'page.indexnow.liquid'")

    # 4. Create the Page in Shopify
    page_payload = {
        "page": {
            "title": "IndexNow Verification Key",
            "body_html": key,
            "handle": "indexnow-key",
            "template_suffix": "indexnow",
            "published": True
        }
    }
    # Check if page already exists
    req = urllib.request.Request(f"https://{shop}/admin/api/2026-04/pages.json?handle=indexnow-key", headers={"X-Shopify-Access-Token": token})
    existing_pages = json.loads(urllib.request.urlopen(req).read())['pages']
    
    if existing_pages:
        page_id = existing_pages[0]['id']
        url = f"https://{shop}/admin/api/2026-04/pages/{page_id}.json"
        req = urllib.request.Request(url, data=json.dumps(page_payload).encode('utf-8'), headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"}, method='PUT')
    else:
        url = f"https://{shop}/admin/api/2026-04/pages.json"
        req = urllib.request.Request(url, data=json.dumps(page_payload).encode('utf-8'), headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"}, method='POST')
        
    res = urllib.request.urlopen(req)
    page_data = json.loads(res.read())['page']
    
    print(f"Created IndexNow Page!")
    print(f"Key Location URL: https://{shop}/pages/{page_data['handle']}")
    
    # 5. Let's do an initial Ping to IndexNow for the Creatine Article
    ping_payload = {
        "host": shop,
        "key": key,
        "keyLocation": f"https://{shop}/pages/{page_data['handle']}",
        "urlList": [
            f"https://{shop}/blogs/nutrition/7-best-creatine-supplements-{{market}}"
        ]
    }
    ping_url = "https://api.indexnow.org/indexnow"
    req = urllib.request.Request(ping_url, data=json.dumps(ping_payload).encode('utf-8'), headers={"Content-Type": "application/json; charset=utf-8"}, method='POST')
    try:
        ping_res = urllib.request.urlopen(req)
        print(f"Pinged IndexNow! Status: {ping_res.getcode()}")
    except Exception as e:
        print(f"Failed to ping IndexNow: {e}")

setup_indexnow()

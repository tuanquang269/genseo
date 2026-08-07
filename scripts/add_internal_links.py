import json
import urllib.request
import os

CONFIG_PATH = os.path.expanduser('~/.genseo/shopify_token.json')
with open(CONFIG_PATH, 'r') as f:
    auth = json.load(f)
shop = auth['shop']
token = auth['access_token']
blog_id = 100000000001

targets = {
    "everything-you-need-to-know-about-meiji-protein-in-{{market}}": {
        "title": "🌱 Dairy-Free? Explore Our Plant-Based Protein Guides"
    },
    "5-best-vegan-protein-powders-in-{{market}}-2026-ranked-by-our-nutrition-team": {
        "title": "🌱 Explore More Plant-Based Protein Guides"
    }
}

links_html = """
  <ul style="list-style-type: none; padding-left: 0;">
    <li style="margin-bottom: 10px;">👉 <strong><a href="https://yourdomain.com/blogs/nutrition/the-ultimate-guide-to-soy-protein-in-{{market}}-the-comprehensive-plant-based-masterclass">The Comprehensive Guide to Soy Protein in {{MARKET}}</a></strong></li>
    <li style="margin-bottom: 10px;">👉 <strong><a href="https://yourdomain.com/blogs/nutrition/the-ultimate-guide-to-plant-protein-powder-in-{{market}}">{{MARKET}}'s Ultimate Guide to Plant Protein Powders</a></strong></li>
    <li style="margin-bottom: 0;">👉 <strong><a href="https://yourdomain.com/blogs/nutrition/the-ultimate-guide-to-myprotein-soy-protein-isolate-in-{{market}}">Myprotein Soy Protein Isolate: In-Depth Review</a></strong></li>
  </ul>
</div>
"""

# Fetch all articles to find IDs
url = f"https://{shop}/admin/api/2026-04/blogs/{blog_id}/articles.json?limit=250"
req = urllib.request.Request(url, headers={"X-Shopify-Access-Token": token})
articles = json.loads(urllib.request.urlopen(req).read())['articles']

for a in articles:
    handle = a['handle']
    if handle in targets:
        article_id = a['id']
        body_html = a['body_html']
        
        # Don't add twice
        if "The Comprehensive Guide to Soy Protein" in body_html:
            print(f"Skipping {handle} - links already exist.")
            continue
            
        block = f"""
<div class="related-articles-block" style="background-color: #f4f4f4; padding: 20px; border-left: 5px solid #d32f2f; margin-top: 30px; margin-bottom: 30px;">
  <h3 style="margin-top: 0;">{targets[handle]['title']}</h3>
{links_html}
"""
        # Inject block before FAQ or at the end
        if '<h2 id="frequently-asked-questions"' in body_html:
            new_body = body_html.replace('<h2 id="frequently-asked-questions"', block + '\n<h2 id="frequently-asked-questions"')
        elif '<h2>Frequently Asked Questions' in body_html:
            new_body = body_html.replace('<h2>Frequently Asked Questions', block + '\n<h2>Frequently Asked Questions')
        elif '<h2 id="conclusion"' in body_html:
            new_body = body_html.replace('<h2 id="conclusion"', block + '\n<h2 id="conclusion"')
        elif '<h2>Conclusion' in body_html:
            new_body = body_html.replace('<h2>Conclusion', block + '\n<h2>Conclusion')
        else:
            if '<script type="application/ld+json">' in body_html:
                new_body = body_html.replace('<script type="application/ld+json">', block + '\n<script type="application/ld+json">', 1)
            else:
                new_body = body_html + '\n' + block
                
        # Update article
        api_url = f"https://{shop}/admin/api/2026-04/blogs/{blog_id}/articles/{article_id}.json"
        payload = {"article": {"id": article_id, "body_html": new_body}}
        
        req_put = urllib.request.Request(api_url, data=json.dumps(payload).encode("utf-8"), headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"}, method="PUT")
        urllib.request.urlopen(req_put)
        print(f"Successfully injected internal links into: {handle}")

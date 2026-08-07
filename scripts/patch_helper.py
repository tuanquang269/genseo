import os, sys, json, re, urllib.request

SHOP = __import__("genseo_config").SHOP
TOKEN = __import__("genseo_config").TOKEN
API = "2026-04"
BLOG = "100000000001"
DRAFT_DIR = "~/genseo/published_drafts"
TMP_DIR = "~/genseo/tmp_images"
CATALOG_PATH = os.path.join(TMP_DIR, "product_catalog.json")

os.makedirs(DRAFT_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

with open(CATALOG_PATH) as f:
    CATALOG = json.load(f)

def clean_body_and_format(body):
    body = re.sub(r'<script type="application/ld\+json">.*?</script>', '', body, flags=re.DOTALL)
    body = re.sub(r'<style>.*?</style>', '', body, flags=re.DOTALL)
    body = re.sub(r'<div class="article-table-wrapper">\s*(<table>.*?</table>)\s*</div>', r'\1', body, flags=re.DOTALL)
    
    # fix FAQ header for publisher regex
    body = re.sub(r'<h2>\s*(Frequently Asked Questions|FAQs?)\s*</h2>', r'## \1', body, flags=re.IGNORECASE)
    
    # convert <h3> inside FAQ section to ###
    faq_match = re.search(r'(##\s+(?:Frequently Asked Questions|FAQs?).*)', body, flags=re.DOTALL | re.IGNORECASE)
    if faq_match:
        faq_block = faq_match.group(1)
        # convert <h3>...</h3> to ### ...
        fixed_faq = re.sub(r'<h3>\s*(.*?)\s*</h3>', r'### \1', faq_block)
        body = body[:faq_match.start(1)] + fixed_faq
        
    # fix author link for publisher regex: convert <a href="/pages/handle">Name</a> -> [Name](/pages/handle)
    def fix_author_link(m):
        author_html = m.group(0)
        return re.sub(r'<a\s+href="(/pages/[a-z-]+)">([^<]+)</a>', r'[\2](\1)', author_html)
    
    body = re.sub(r'(<h3>About the Author</h3>.*)', fix_author_link, body, flags=re.DOTALL | re.IGNORECASE)
    return body

def fetch_live_draft(article_id):
    url = f"https://{SHOP}/admin/api/{API}/blogs/{BLOG}/articles/{article_id}.json"
    req = urllib.request.Request(url, headers={"X-Shopify-Access-Token": TOKEN})
    a = json.loads(urllib.request.urlopen(req).read())["article"]
    
    title = a["title"]
    body = a.get("body_html", "")
    body = clean_body_and_format(body)
    
    draft_path = os.path.join(DRAFT_DIR, f"draft_{article_id}.md")
    draft_content = f"# {title}\n\n" + body.strip()
    
    with open(draft_path, 'w', encoding='utf-8') as f:
        f.write(draft_content)
        
    print(f"✓ Fetched live article {article_id} -> {draft_path}")
    return draft_path, title, body

def find_ref_images(keywords, prefix):
    headers = {"User-Agent": "Mozilla/5.0"}
    downloaded = []
    for i, kw in enumerate(keywords):
        save_name = f"{prefix}_{i}"
        dest = os.path.join(TMP_DIR, f"{save_name}.png")
        found = False
        for p in CATALOG:
            if kw.lower() in p["title"].lower() and p.get("image_src"):
                img_url = p["image_src"]
                try:
                    r = urllib.request.Request(img_url, headers=headers)
                    data = urllib.request.urlopen(r, timeout=10).read()
                    if len(data) > 5000:
                        with open(dest, "wb") as f:
                            f.write(data)
                        print(f"  ✓ Ref photo for '{kw}' -> {dest} ({p['title'][:40]})")
                        downloaded.append((kw, dest))
                        found = True
                        break
                except Exception:
                    continue
        if not found:
            for p in CATALOG:
                if p.get("image_src"):
                    try:
                        r = urllib.request.Request(p["image_src"], headers=headers)
                        data = urllib.request.urlopen(r, timeout=10).read()
                        if len(data) > 5000:
                            with open(dest, "wb") as f:
                                f.write(data)
                            print(f"  ⚠ Fallback ref photo for '{kw}' -> {dest}")
                            downloaded.append((kw, dest))
                            break
                    except Exception:
                        continue
    return downloaded

if __name__ == "__main__":
    aid = sys.argv[1]
    fetch_live_draft(aid)

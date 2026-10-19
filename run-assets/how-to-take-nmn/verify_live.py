"""Read-only post-publish check for CA1016-9. Run from the repository root."""
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from genseo_config import API, SHOP, TOKEN

request = urllib.request.Request(
    f"https://{SHOP}/admin/api/{API}/blogs/104008483131/articles/634944684347.json",
    headers={"X-Shopify-Access-Token": TOKEN},
)
with urllib.request.urlopen(request, timeout=60) as response:
    article = json.load(response)["article"]
assert article["published_at"], "article is unpublished"
print("published_at:", article["published_at"])
inline = re.findall(r'<img[^>]+src="([^"]+)"', article["body_html"])
assert len(inline) == 3, inline
url = "https://wellnessnest.co/blogs/news/" + article["handle"]
with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as response:
    assert response.status == 200
    page = response.read().decode()
print("frontend: HTTP 200 (Mozilla/5.0)")
assert "__shop-this-article" in page, "widget absent"
handles = re.findall(r'data-liquid-handles=["\x27]([^"\x27]*)', page)
assert any("ageaura-pure-nmn-tmg-nad-complex" in value for value in handles), handles
print("widget handles:", handles)
for image in [article["image"]["src"], *inline]:
    image = html.unescape(image)
    assert image.startswith("https://cdn.shopify.com/"), image
    with urllib.request.urlopen(urllib.request.Request(image, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as response:
        content_type = response.headers.get("Content-Type", "")
        data = response.read()
        assert response.status == 200 and content_type.startswith("image/") and len(data) > 1000
        print("image: HTTP 200", content_type, len(data), "bytes")
    filename = image.split("?")[0].rsplit("/", 1)[-1]
    rendered = [html.unescape(src) for src in re.findall(r'<img[^>]+src="([^"]+)"', page) if filename in src]
    assert rendered, "image not present in frontend img elements"
    rendered_url = ("https:" + rendered[0]) if rendered[0].startswith("//") else rendered[0]
    with urllib.request.urlopen(urllib.request.Request(rendered_url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as response:
        assert response.status == 200 and response.headers.get("Content-Type", "").startswith("image/")
        assert len(response.read()) > 1000
assert "FAQPage" in page
schema_count = len(re.findall(r'"@type"\s*:\s*"(?:Article|BlogPosting)"', page))
print("Article/BlogPosting schemas:", schema_count)
body_schema_count = len(re.findall(r'"@type"\s*:\s*"(?:Article|BlogPosting)"', article["body_html"]))
assert body_schema_count == 1, "duplicate or missing Article schema in publisher body"
if schema_count != 1:
    print("WARNING: theme adds a second Article schema; theme edits require separate approval")
print("PASS: hero + 3 inline CDN images and rendered-body sources; public widget, timestamp, body schema")

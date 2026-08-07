import json
import urllib.request
import sys
import argparse

shop = __import__("genseo_config").SHOP
token = __import__("genseo_config").TOKEN

parser = argparse.ArgumentParser(description="Push collection HTML and SEO metadata to Shopify")
parser.add_argument("handle", help="Collection handle (e.g., fat-burner)")
parser.add_argument("html_file", help="Path to HTML file for body_html")
parser.add_argument("--title", help="SEO title tag (max 70 chars)", default=None)
parser.add_argument("--meta-description", help="SEO meta description (max 160 chars)", default=None)
args = parser.parse_args()

handle = args.handle
file_path = args.html_file

with open(file_path, "r") as f:
    html_content = f.read()

# Query Smart Collections
req = urllib.request.Request(f"https://{shop}/admin/api/2026-04/smart_collections.json?handle={handle}", headers={"X-Shopify-Access-Token": token})
res = urllib.request.urlopen(req)
data = json.loads(res.read())

collection_id = None
collection_type = None

if data.get('smart_collections') and len(data['smart_collections']) > 0:
    collection_id = data['smart_collections'][0]['id']
    collection_type = "smart_collections"
else:
    # Query Custom Collections
    req = urllib.request.Request(f"https://{shop}/admin/api/2026-04/custom_collections.json?handle={handle}", headers={"X-Shopify-Access-Token": token})
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    if data.get('custom_collections') and len(data['custom_collections']) > 0:
        collection_id = data['custom_collections'][0]['id']
        collection_type = "custom_collections"

if not collection_id:
    print(f"Error: Could not find collection with handle '{handle}'")
    sys.exit(1)

print(f"Found Collection ID: {collection_id} ({collection_type})")

# Build the update payload
collection_key = "smart_collection" if collection_type == "smart_collections" else "custom_collection"
update_data = {"id": collection_id, "body_html": html_content}

# Add SEO metafields if provided
metafields = []
if args.title:
    metafields.append({
        "namespace": "global",
        "key": "title_tag",
        "value": args.title,
        "type": "single_line_text_field"
    })
    print(f"SEO Title: {args.title}")

if args.meta_description:
    metafields.append({
        "namespace": "global",
        "key": "description_tag",
        "value": args.meta_description,
        "type": "single_line_text_field"
    })
    print(f"SEO Meta Description: {args.meta_description}")

if metafields:
    update_data["metafields"] = metafields

update_payload = {collection_key: update_data}

req_update = urllib.request.Request(
    f"https://{shop}/admin/api/2026-04/{collection_type}/{collection_id}.json",
    data=json.dumps(update_payload).encode('utf-8'),
    headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"},
    method="PUT"
)
try:
    res_update = urllib.request.urlopen(req_update)
    result = json.loads(res_update.read())
    print("SUCCESS: Updated Shopify Collection layout.")
    if args.title or args.meta_description:
        print("SUCCESS: Updated SEO title and/or meta description.")
except Exception as e:
    print(f"Error updating collection: {e}")
    if hasattr(e, 'read'):
        print(e.read().decode())

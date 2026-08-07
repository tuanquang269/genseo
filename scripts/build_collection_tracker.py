"""
build_collection_tracker.py
-----------------------------
Fetches all /collections/ URLs from Google Search Console,
aggregates their keyword performance, and writes a tracker CSV.

Columns:
  Collection Name | Link | Keywords It Ranks For | Last Updated |
  Previous Checked Date | Last Avg Position (SG) | Current Avg Position (SG)

Usage:
  python3 scripts/build_collection_tracker.py
Output:
  /Users/kevinkreative/genseo/COLLECTION_TRACKER.csv
"""

import sys, subprocess, os, csv, json, datetime, urllib.request

# ---------------------------------------------------------------------------
# 1. Ensure Google API packages are available
# ---------------------------------------------------------------------------
def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--user", "--quiet"])

try:
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    print("Installing required Google API packages...")
    install('google-api-python-client')
    install('google-auth-httplib2')
    install('google-auth-oauthlib')
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

# ---------------------------------------------------------------------------
# 2. Config
# ---------------------------------------------------------------------------
SITE_URL     = "https://wellnessnest.co"
SHOP         = __import__("genseo_config").SHOP
SHOPIFY_TOKEN = __import__("genseo_config").TOKEN
SCRIPT_DIR   = os.path.dirname(os.path.realpath(__file__))
TOKEN_PATH   = os.path.join(SCRIPT_DIR, "gsc_token.json")
CREDS_PATH   = os.path.join(SCRIPT_DIR, "credentials.json")
OUTPUT_CSV   = "/Users/kevinkreative/genseo/COLLECTION_TRACKER.csv"

# GSC date range: last 90 days
TODAY      = datetime.date.today()
END_DATE   = TODAY.strftime("%Y-%m-%d")
START_DATE = (TODAY - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
CHECKED_DATE = TODAY.strftime("%Y-%m-%d")

# ---------------------------------------------------------------------------
# 3. GSC auth
# ---------------------------------------------------------------------------
def get_service():
    if not os.path.exists(CREDS_PATH):
        print(f"Error: {CREDS_PATH} not found.")
        sys.exit(1)
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, ['https://www.googleapis.com/auth/webmasters.readonly'])
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDS_PATH, ['https://www.googleapis.com/auth/webmasters.readonly'])
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    return build('searchconsole', 'v1', credentials=creds)

# ---------------------------------------------------------------------------
# 4. Fetch all pages from GSC filtered to /collections/
# ---------------------------------------------------------------------------
def fetch_all_collection_pages(service):
    print("Fetching all collection pages from GSC...")
    request = {
        "startDate": START_DATE,
        "endDate": END_DATE,
        "dimensions": ["page"],
        "dimensionFilterGroups": [{
            "filters": [{
                "dimension": "page",
                "expression": "/collections/",
                "operator": "contains"
            }]
        }],
        "rowLimit": 1000
    }
    resp = service.searchanalytics().query(siteUrl=SITE_URL, body=request).execute()
    rows = resp.get("rows", [])
    # Filter to only /collections/ URLs (exclude /collections/all, brand sub-paths etc)
    pages = []
    for row in rows:
        url = row["keys"][0]
        # Only top-level collection pages (no query strings, no deep sub-paths beyond /collections/handle)
        path = url.replace(SITE_URL, "")
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2 and parts[0] == "collections":
            pages.append(url)
    # Deduplicate
    pages = list(dict.fromkeys(pages))
    print(f"  Found {len(pages)} collection pages in GSC.")
    return pages

# ---------------------------------------------------------------------------
# 5. Fetch keywords for a specific page
# ---------------------------------------------------------------------------
def fetch_keywords_for_page(service, page_url):
    request = {
        "startDate": START_DATE,
        "endDate": END_DATE,
        "dimensions": ["query"],
        "dimensionFilterGroups": [{
            "filters": [{
                "dimension": "page",
                "expression": page_url,
                "operator": "equals"
            }]
        }],
        "rowLimit": 50
    }
    try:
        resp = service.searchanalytics().query(siteUrl=SITE_URL, body=request).execute()
        rows = resp.get("rows", [])
        return rows
    except Exception as e:
        print(f"  WARNING: Could not fetch keywords for {page_url}: {e}")
        return []

# ---------------------------------------------------------------------------
# 6. Fetch collection "updated_at" from Shopify API
# ---------------------------------------------------------------------------
def fetch_shopify_collection_dates():
    """Returns dict: handle -> updated_at date string"""
    dates = {}
    headers = {"X-Shopify-Access-Token": SHOPIFY_TOKEN}

    for ctype in ["smart_collections", "custom_collections"]:
        url = f"https://{SHOP}/admin/api/2026-04/{ctype}.json?limit=250&fields=id,handle,updated_at,title"
        req = urllib.request.Request(url, headers=headers)
        try:
            data = json.loads(urllib.request.urlopen(req).read())
            for col in data.get(ctype.replace("_collections", ""), data.get(ctype, [])):
                # API key differs: smart_collection vs custom_collection
                items = data.get("smart_collections", data.get("custom_collections", []))
            for col in items:
                handle = col.get("handle", "")
                raw_date = col.get("updated_at", "")
                # Parse to YYYY-MM-DD
                if raw_date:
                    dates[handle] = raw_date[:10]
        except Exception as e:
            print(f"  WARNING: Could not fetch Shopify {ctype}: {e}")
    return dates

# ---------------------------------------------------------------------------
# 7. Load previous CSV data (for "Previous Checked Date" and "Last Avg Pos")
# ---------------------------------------------------------------------------
def load_previous_data():
    prev = {}
    if not os.path.exists(OUTPUT_CSV):
        return prev
    with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            link = row.get("Link", "").strip()
            if link:
                prev[link] = {
                    "previous_checked": row.get("Previous Checked Date", ""),
                    "last_avg_position": row.get("Current Avg Position (US)", ""),
                }
    return prev

# ---------------------------------------------------------------------------
# 8. Derive collection name from URL handle
# ---------------------------------------------------------------------------
def handle_to_name(url):
    path = url.replace(SITE_URL, "").strip("/")
    parts = path.split("/")
    handle = parts[-1] if len(parts) >= 2 else path
    return handle.replace("-", " ").title()

# ---------------------------------------------------------------------------
# 9. Main
# ---------------------------------------------------------------------------
def main():
    print(f"=== Collection Tracker Builder ===")
    print(f"Date range: {START_DATE} → {END_DATE}")
    print()

    # Load previous state
    prev_data = load_previous_data()
    print(f"Loaded {len(prev_data)} previous records from existing CSV.")

    # Fetch Shopify updated_at dates
    print("Fetching Shopify collection dates...")
    shopify_dates = fetch_shopify_collection_dates()
    print(f"  Got dates for {len(shopify_dates)} collections.")

    # Connect to GSC
    service = get_service()

    # Get all collection pages
    all_pages = fetch_all_collection_pages(service)

    results = []
    for i, page_url in enumerate(all_pages, 1):
        # Extract handle from URL
        path = page_url.replace(SITE_URL, "").strip("/")
        parts = [p for p in path.split("/") if p]
        handle = parts[1] if len(parts) >= 2 else parts[0] if parts else "unknown"

        collection_name = handle_to_name(page_url)
        print(f"  [{i}/{len(all_pages)}] {collection_name} ({handle})")

        # Fetch keywords
        keyword_rows = fetch_keywords_for_page(service, page_url)

        if not keyword_rows:
            avg_position = ""
            top_keywords = ""
        else:
            # Compute impression-weighted average position
            total_impressions = sum(r["impressions"] for r in keyword_rows)
            if total_impressions > 0:
                weighted_pos = sum(r["position"] * r["impressions"] for r in keyword_rows) / total_impressions
            else:
                weighted_pos = sum(r["position"] for r in keyword_rows) / len(keyword_rows)

            avg_position = f"{weighted_pos:.1f}"

            # Top keywords: sort by impressions desc, take top 5
            sorted_kws = sorted(keyword_rows, key=lambda r: r["impressions"], reverse=True)
            top_keywords = " | ".join(
                f"{r['keys'][0]} (pos {r['position']:.0f}, {r['impressions']}imp)"
                for r in sorted_kws[:5]
            )

        # Shopify last updated
        last_updated = shopify_dates.get(handle, "")

        # Previous data
        prev = prev_data.get(page_url, {})
        previous_checked = prev.get("previous_checked", "")
        last_avg_position = prev.get("last_avg_position", "")

        results.append({
            "Collection Name": collection_name,
            "Link": page_url,
            "Keywords It Ranks For": top_keywords,
            "Last Updated": last_updated,
            "Previous Checked Date": previous_checked,
            "Last Avg Position (US)": last_avg_position,
            "Current Avg Position (US)": avg_position,
            "Checked Date": CHECKED_DATE,
        })

    # Sort by Current Avg Position (ascending = best rank first), empty last
    def sort_key(r):
        val = r["Current Avg Position (US)"]
        try:
            return float(val)
        except:
            return 9999.0

    results.sort(key=sort_key)

    # Write CSV
    fieldnames = [
        "Collection Name",
        "Link",
        "Keywords It Ranks For",
        "Last Updated",
        "Previous Checked Date",
        "Last Avg Position (US)",
        "Current Avg Position (US)",
        "Checked Date",
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print()
    print(f"✅ Done! Written {len(results)} collection rows to:")
    print(f"   {OUTPUT_CSV}")
    print()
    print("Top 10 collections by current average position:")
    print(f"{'Collection':<35} {'Avg Pos':>8}  Link")
    print("-" * 80)
    for r in results[:10]:
        pos = r["Current Avg Position (US)"] or "N/A"
        name = r["Collection Name"][:33]
        print(f"  {name:<33} {pos:>8}  {r['Link']}")

if __name__ == "__main__":
    main()

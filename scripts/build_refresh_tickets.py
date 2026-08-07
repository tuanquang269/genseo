import os
import sys
import json
import datetime
import urllib.request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from collections import defaultdict

# --- Configuration ---
GSC_SITE_URL = "https://yourdomain.com/" 
BLOG_ID = "100000000001"
SKILL_DIR = os.path.expanduser("~/genseo/scripts/")
GSC_TOKEN_PATH = os.path.join(SKILL_DIR, 'gsc_token.json')
GSC_CREDS_PATH = os.path.join(SKILL_DIR, 'credentials.json')
SHOPIFY_TOKEN_PATH = os.path.join(SKILL_DIR, 'shopify_token.json')
OUTPUT_FILE = os.path.join(os.getcwd(), "GENSEO_REFRESH_SCHEDULE.md")

# Fallback Paths
if not os.path.exists(GSC_CREDS_PATH): GSC_CREDS_PATH = os.path.join(os.getcwd(), 'scripts', 'credentials.json')
if not os.path.exists(GSC_TOKEN_PATH): GSC_TOKEN_PATH = os.path.join(os.getcwd(), 'scripts', 'gsc_token.json')

def get_gsc_service():
    if not os.path.exists(GSC_TOKEN_PATH):
        print("Error: GSC token not found. Please authenticate GSC first.")
        sys.exit(1)
    creds = Credentials.from_authorized_user_file(GSC_TOKEN_PATH, ['https://www.googleapis.com/auth/webmasters.readonly'])
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(GSC_TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    return build('searchconsole', 'v1', credentials=creds)

def fetch_gsc_slice(service, start_days_ago, end_days_ago):
    end_date = (datetime.date.today() - datetime.timedelta(days=end_days_ago)).strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=start_days_ago)).strftime('%Y-%m-%d')
    
    request = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['page', 'query'],
        'dimensionFilterGroups': [{
            'filters': [{'dimension': 'country', 'operator': 'equals', 'expression': '{{COUNTRY_CODE}}'}]
        }],
        'rowLimit': 10000
    }
    try:
        response = service.searchanalytics().query(siteUrl=GSC_SITE_URL, body=request).execute()
        return response.get('rows', [])
    except Exception as e:
        print(f"Error fetching GSC data: {e}")
        return []

def get_shopify_articles():
    if not os.path.exists(SHOPIFY_TOKEN_PATH): return {}
    with open(SHOPIFY_TOKEN_PATH, 'r') as f: auth = json.load(f)
    url = f"https://{auth['shop']}/admin/api/2026-04/blogs/{BLOG_ID}/articles.json?limit=250"
    req = urllib.request.Request(url, headers={"X-Shopify-Access-Token": auth['access_token']})
    try:
        res = urllib.request.urlopen(req)
        data = json.loads(res.read())
        return {str(article['handle']): str(article['id']) for article in data.get('articles', [])}
    except Exception as e:
        print(f"Error fetching Shopify articles: {e}")
        return {}

def analyze_and_build(t1_rows, t2_rows, shopify_map):
    # Data Structs
    t1_map = defaultdict(lambda: defaultdict(dict)) # page -> query -> data
    t2_map = defaultdict(lambda: defaultdict(dict))
    
    for row in t1_rows:
        if "/blogs/nutrition/" in row['keys'][0]:
            t1_map[row['keys'][0]][row['keys'][1]] = row
            
    for row in t2_rows:
        if "/blogs/nutrition/" in row['keys'][0]:
            t2_map[row['keys'][0]][row['keys'][1]] = row

    tier1_decay = []
    tier2_low_hanging = []
    tier3_ctr_trap = []
    tier4_cannibal = defaultdict(list)
    
    # 1. First Pass: Single URL analysis
    for url, queries in t1_map.items():
        handle = url.split("/")[-1]
        if handle not in shopify_map: continue
        article_id = shopify_map[handle]
        
        # Aggregate Top Query manually (highest impressions T1)
        sorted_qs = sorted(queries.items(), key=lambda item: item[1]['impressions'], reverse=True)
        if not sorted_qs: continue
        
        top_query = sorted_qs[0][0]
        q_data_t1 = sorted_qs[0][1]
        q_data_t2 = t2_map.get(url, {}).get(top_query, {'impressions': 0, 'clicks': 0, 'position': 0})
        
        # Cannibalization Map Builder
        if q_data_t1['impressions'] > 50:
            tier4_cannibal[top_query].append({'url': url, 'article_id': article_id, 'imp': q_data_t1['impressions'], 'pos': q_data_t1['position']})
        
        # Calculate overall page CTR in T1
        total_page_imp_t1 = sum(q['impressions'] for q in queries.values())
        total_page_clicks_t1 = sum(q['clicks'] for q in queries.values())
        page_ctr_t1 = total_page_clicks_t1 / total_page_imp_t1 if total_page_imp_t1 > 0 else 0
        
        # Tier 1: The Bleeding Giants (Decay Analysis)
        # Dropped > 30% in impressions, DROPPED > 1.0 spots, and past impressions > 150
        if q_data_t2['impressions'] > 150 and q_data_t1['impressions'] < (q_data_t2['impressions'] * 0.70):
            if q_data_t1['position'] > q_data_t2['position'] + 1.0:
                tier1_decay.append({
                    'url': url, 'article_id': article_id, 'kw': top_query,
                    'reason': f"Rank dropped from {q_data_t2['position']:.1f} to {q_data_t1['position']:.1f}. Impressions collapsed from {q_data_t2['impressions']} to {q_data_t1['impressions']} (Lost Share of Voice).",
                    'priority': q_data_t2['impressions'] - q_data_t1['impressions']
                })
                continue # Skip assigning to other tiers if it's bleeding heavily
        
        # Tier 2: Striking Distance (Low-Hanging)
        if 11.0 <= q_data_t1['position'] <= 25.0 and total_page_imp_t1 > 100:
            # Check if it is NOT declining (i.e. stable or growing)
            if q_data_t1['impressions'] >= q_data_t2['impressions'] * 0.80:
                tier2_low_hanging.append({
                    'url': url, 'article_id': article_id, 'kw': top_query,
                    'reason': f"Stable Position {q_data_t1['position']:.1f} with {total_page_imp_t1} impressions. Needs entity bump.",
                    'priority': total_page_imp_t1
                })
                continue
                
        # Tier 3: The CTR Trap
        if q_data_t1['position'] <= 10.0 and total_page_imp_t1 > 300 and page_ctr_t1 < 0.015:
            tier3_ctr_trap.append({
                'url': url, 'article_id': article_id, 'kw': top_query,
                'reason': f"Page 1 (Pos {q_data_t1['position']:.1f}) but CTR is terrible ({page_ctr_t1*100:.2f}%). Impressions: {total_page_imp_t1}.",
                'priority': total_page_imp_t1
            })
            
    # Process Tier 4 Cannibalization (Filter list)
    cannibals_out = []
    for kw, urls in tier4_cannibal.items():
        if len(urls) > 1: # More than 1 URL fighting for same keyword
            urls.sort(key=lambda x: x['imp'], reverse=True)
            cannibals_out.append({
                'kw': kw,
                'urls': urls,
                'reason': f"Found {len(urls)} articles cannibalizing '{kw}'. URL1 Pos: {urls[0]['pos']:.1f}, URL2 Pos: {urls[1]['pos']:.1f}",
                'priority': urls[0]['imp']
            })

    # Sort priorities
    tier1_decay.sort(key=lambda x: x['priority'], reverse=True)
    tier2_low_hanging.sort(key=lambda x: x['priority'], reverse=True)
    tier3_ctr_trap.sort(key=lambda x: x['priority'], reverse=True)
    cannibals_out.sort(key=lambda x: x['priority'], reverse=True)
    
    # Write output
    with open(OUTPUT_FILE, 'w') as f:
        f.write("# 🔄 GENSEO Content Refresh Schedule (V2 Enterprise)\n\n")
        f.write("> **System:** Analyzed Last 90 days vs Previous 90 days. Filtered specifically for SGP traffic to eliminate global seasonality noise.\n\n")
        
        ticket_num = 1
        
        # TIER 1
        f.write("## 🚨 Tier 1: The Bleeding Giants (Severe Position & Traffic Decay)\n")
        if not tier1_decay: f.write("*No bleeding URLs detected.* \n\n")
        for item in tier1_decay[:5]:
            f.write(f"### 📝 Ticket #{ticket_num} - [DEEP REFRESH]\n")
            f.write(f"- **Target URL**: {item['url']}\n- **Primary Keyword**: `{item['kw']}`\n- **Diagnostic**: {item['reason']}\n")
            f.write("**🤖 Auto-Publish Trigger Prompt:**\n```markdown\n")
            f.write(f"/genseo-auto-publish [REFRESH EXISTING]. The article {item['url']} suffers severe decay. Execute a [DEEP REFRESH] targeting \"{item['kw']}\". Restructure headings and add updated tables. Default BLOG_ID is {BLOG_ID}. ARTICLE_ID is {item['article_id']}.\n```\n\n")
            ticket_num += 1

        # TIER 2
        f.write("## 🍏 Tier 2: Striking Distance (Page 2 Low-Hanging Fruits)\n")
        if not tier2_low_hanging: f.write("*No stable page 2 URLs detected.* \n\n")
        for item in tier2_low_hanging[:5]:
            f.write(f"### 📝 Ticket #{ticket_num} - [SURGICAL PATCH - ENTITY]\n")
            f.write(f"- **Target URL**: {item['url']}\n- **Primary Keyword**: `{item['kw']}`\n- **Diagnostic**: {item['reason']}\n")
            f.write("**🤖 Auto-Publish Trigger Prompt:**\n```markdown\n")
            f.write(f"/genseo-auto-publish [REFRESH EXISTING]. The article {item['url']} is stuck on Page 2. Execute a [SURGICAL PATCH - ENTITY] targeting \"{item['kw']}\". Add FAQs and LSI keywords without rewriting the core body. Default BLOG_ID is {BLOG_ID}. ARTICLE_ID is {item['article_id']}.\n```\n\n")
            ticket_num += 1
            
        # TIER 3
        f.write("## 🪤 Tier 3: The CTR Trap (Top 10 but ignored)\n")
        if not tier3_ctr_trap: f.write("*No terrible CTR anomalies detected.* \n\n")
        for item in tier3_ctr_trap[:5]:
            f.write(f"### 📝 Ticket #{ticket_num} - [HEADLINE REWRITE]\n")
            f.write(f"- **Target URL**: {item['url']}\n- **Primary Keyword**: `{item['kw']}`\n- **Diagnostic**: {item['reason']}\n")
            f.write("**🤖 Auto-Publish Trigger Prompt:**\n```markdown\n")
            f.write(f"/genseo-auto-publish [REFRESH EXISTING]. The article {item['url']} suffers terrible CTR. Execute a [HEADLINE REWRITE] targeting \"{item['kw']}\" to aggressively match search intent and drive clicks. Default BLOG_ID is {BLOG_ID}. ARTICLE_ID is {item['article_id']}.\n```\n\n")
            ticket_num += 1

        # TIER 4
        f.write("## 👻 Tier 4: The Cannibalization Zones (URL Conflict)\n")
        if not cannibals_out: f.write("*No severe cannibalizations detected.* \n\n")
        for idx, item in enumerate(cannibals_out[:5]):
            f.write(f"### 📝 Ticket #{ticket_num} - [MERGE OR KILL]\n")
            f.write(f"- **Cannibalized Keyword**: `{item['kw']}`\n- **Diagnostic**: {item['reason']}\n")
            for u in item['urls']: f.write(f"  - Conflict URL: {u['url']} (Impressions: {u['imp']}, Pos: {u['pos']:.1f})\n")
            f.write("**🤖 Auto-Publish Trigger Prompt:**\n*(A human needs to decide which URL to keep as Pillar, then instruct Agent to merge the content and redirect the loser.)*\n\n")
            ticket_num += 1
            
    print(f"Schedule generated at: {OUTPUT_FILE}")
    print(f"Total Refresh Tickets: {ticket_num - 1}")

if __name__ == "__main__":
    service = get_gsc_service()
    
    print("Fetching GSC Base T1 (Last 90 days)...")
    t1_data = fetch_gsc_slice(service, 90, 0)
    print("Fetching GSC History T2 (Previous 90 days)...")
    t2_data = fetch_gsc_slice(service, 180, 91)
    
    print("Fetching live Shopify Articles to map URLs to Article IDs...")
    shopify_map = get_shopify_articles()
    
    print("Executing Enterprise-Grade Decay & Quadrant Analysis...")
    analyze_and_build(t1_data, t2_data, shopify_map)

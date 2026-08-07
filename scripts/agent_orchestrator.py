import sys
import os
import datetime
import json

# Add shared skills to path so we can reuse gsc_fetcher authentication
sys.path.append(os.path.expanduser("~/genseo/scripts/"))
import gsc_fetcher

def check_rankings(site_url, threshold=5.0):
    service = gsc_fetcher.get_service()
    
    today = datetime.date.today()
    # Current Period: Last 7 days
    c_end = today.strftime('%Y-%m-%d')
    c_start = (today - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Previous Period: 7 days before that
    p_end = (today - datetime.timedelta(days=8)).strftime('%Y-%m-%d')
    p_start = (today - datetime.timedelta(days=15)).strftime('%Y-%m-%d')
    
    def get_data(s_date, e_date):
        request = {
            'startDate': s_date,
            'endDate': e_date,
            'dimensions': ['query', 'page'],
            'dimensionFilterGroups': [{
                'filters': [{
                    'dimension': 'country',
                    'operator': 'equals',
                    'expression': '{{COUNTRY_CODE}}'
                }]
            }],
            'rowLimit': 500
        }
        res = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
        data = {}
        for row in res.get('rows', []):
            query_key = row['keys'][0]
            page_url = row['keys'][1]
            data[(query_key, page_url)] = row['position']
        return data

    print(f"Fetching GSC data for {site_url}...")
    current_data = get_data(c_start, c_end)
    previous_data = get_data(p_start, p_end)
    
    tickets = []
    
    for (query, url), c_pos in current_data.items():
        if (query, url) in previous_data:
            p_pos = previous_data[(query, url)]
            drop = c_pos - p_pos  
            if drop >= threshold:
                tickets.append({
                    "keyword": query,
                    "url": url,
                    "previous_rank": round(p_pos, 1),
                    "current_rank": round(c_pos, 1),
                    "drop": round(drop, 1),
                    "clicks": 0
                })

    # Fetch 6-month traffic for sorting
    print("Fetching 180-day traffic data for sorting priorities...")
    t_end = today.strftime('%Y-%m-%d')
    t_start = (today - datetime.timedelta(days=180)).strftime('%Y-%m-%d')
    request_6m = {
        'startDate': t_start,
        'endDate': t_end,
        'dimensions': ['query', 'page'],
        'dimensionFilterGroups': [{'filters': [{'dimension': 'country', 'operator': 'equals', 'expression': '{{COUNTRY_CODE}}'}]}],
        'rowLimit': 5000
    }
    
    try:
        res_6m = service.searchanalytics().query(siteUrl=site_url, body=request_6m).execute()
        for row in res_6m.get('rows', []):
            q_key = row['keys'][0]
            p_url = row['keys'][1]
            # Match traffic to any generated tickets
            for t in tickets:
                if t['keyword'] == q_key and t['url'] == p_url:
                    t['clicks'] = row.get('clicks', 0)
    except Exception as e:
        print(f"Error fetching 6m traffic: {e}")

    # Sort tickets by highest clicks over the last 6 months
    tickets.sort(key=lambda x: x['clicks'], reverse=True)
                
    if not tickets:
        print("No organic drops found over threshold. Injecting a mock drop for test validation...")
        tickets.append({
            "keyword": "test mock mutant whey review",
            "url": "https://yourdomain.com/products/mutant-whey",
            "previous_rank": 2.1,
            "current_rank": 10.4,
            "drop": 8.3
        })

    generate_tickets_markdown(tickets)

def generate_tickets_markdown(tickets):
    file_path = os.path.expanduser("~/genseo/SEO_ACTION_TICKETS.md")
    
    content = "# 🚨 SEO Agent Action Tickets\n\n"
    content += "*The Orchestrator has detected significant ranking drops. Please copy the prompt below and feed it to the Strategist Agent.* \n\n"
    for t in tickets:
        url_path = t['url'].replace("https://yourdomain.com", "").strip()
        
        if url_path == "" or url_path == "/":
            page_type = "Homepage"
        elif "/products/" in t['url']:
            page_type = "Product Page"
        elif "/collections/" in t['url']:
            page_type = "Collection Page"
        else:
            page_type = "Blog"
            
        content += f"## Keyword Alert: `{t['keyword']}`\n"
        content += f"- **Target URL**: {t['url']} ({page_type})\n"
        content += f"- **Past 6M Traffic**: {t['clicks']} Clicks\n"
        content += f"- **Previous Rank**: {t['previous_rank']} \n"
        content += f"- **Current Rank**: {t['current_rank']} (Drop of {t['drop']} positions) \n\n"
        
        content += "### 🤖 Trigger Prompt for `genseo-seo-strategist`:\n"
        content += "```markdown\n"
        
        if page_type in ["Product Page", "Collection Page", "Homepage"]:
            content += f"URGENT RANKING DROP: Our {page_type} (`{t['url']}`) has dropped from position {t['previous_rank']} to {t['current_rank']} for the highly-converting keyword '{t['keyword']}'.\n"
            content += f"DO NOT edit the {page_type} directly. Instead, generate a Strategic Brief for a SUPPORTING BLOG ARTICLE (or refresh an existing related blog). The goal of this blog piece is to capture informational intent around '{t['keyword']}' and funnel that authority by placing a strong internal link pointing back to `{t['url']}` to push its ranking back up.\n"
        else:
            content += f"URGENT RANKING DROP: The blog post (`{t['url']}`) tracking for the keyword '{t['keyword']}' has inexplicably fallen from position {t['previous_rank']} down to {t['current_rank']}.\n"
            content += "Please read the Knowledge Base rules (EEAT and AEO_GEO) and generate an emergency Strategic Brief to REFRESH this exact blog post. Identify semantic gaps, specify which FAQs we are missing, and formulate an outline to regain the top 3 spots. Once done, issue the handoff to `genseo-content-refresh` to execute the changes on Shopify.\n"
            
        content += "```\n\n---\n\n"
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Action tickets generated: {file_path}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("site_url", help="GSC Site URL (e.g., sc-domain:yourdomain.com)")
    parser.add_argument("--threshold", type=float, default=5.0, help="Drop threshold to trigger action")
    args = parser.parse_args()
    
    check_rankings(args.site_url, args.threshold)

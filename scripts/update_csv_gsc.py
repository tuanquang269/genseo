import sys
import os
import csv
import datetime

# Import GSC auth
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from gsc_fetcher import get_service

CSV_FILE = "~/genseo/PUBLISHED_ARTICLES_TRACKER.csv"
SITE_URL = "https://yourdomain.com/"

def fetch_page_data_30_days():
    service = get_service()
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')

    request = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['page'],
        'rowLimit': 25000
    }

    print(f"Fetching GSC data for {SITE_URL} from {start_date} to {end_date}...")
    response = service.searchanalytics().query(siteUrl=SITE_URL, body=request).execute()
    
    page_stats = {}
    if 'rows' in response:
        for row in response['rows']:
            page = row['keys'][0]
            page_stats[page] = {
                'clicks': row['clicks'],
                'impressions': row['impressions'],
                'position': row['position']
            }
    return page_stats

def update_csv():
    page_stats = fetch_page_data_30_days()
    print(f"Fetched stats for {len(page_stats)} pages.")

    rows = []
    headers = []
    
    with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        for row in reader:
            if row:
                rows.append(row)
                
    # New columns
    col_imp = "Impressions (30 Days)"
    col_pos = "Average Position"
    col_clk = "Clicks"
    
    for col in [col_imp, col_pos, col_clk]:
        if col not in headers:
            headers.append(col)
            
    idx_imp = headers.index(col_imp)
    idx_pos = headers.index(col_pos)
    idx_clk = headers.index(col_clk)
    idx_link = headers.index("Article Link")
    
    updated_count = 0
    for row in rows:
        # pad row if necessary
        while len(row) < len(headers):
            row.append("")
            
        link = row[idx_link]
        if link in page_stats:
            stats = page_stats[link]
            row[idx_imp] = str(stats['impressions'])
            row[idx_pos] = f"{stats['position']:.2f}"
            row[idx_clk] = str(stats['clicks'])
            updated_count += 1
        else:
            row[idx_imp] = "0"
            row[idx_pos] = "0.00"
            row[idx_clk] = "0"

    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
        
    print(f"CSV updated successfully. {updated_count} articles had GSC data out of {len(rows)}.")

if __name__ == '__main__':
    update_csv()

import sys
import os
import csv
from datetime import datetime

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from gsc_fetcher import get_service

def check_indexing_status():
    service = get_service()
    site_url = 'https://wellnessnest.co/'
    csv_file = '/Users/kevinkreative/genseo/PUBLISHED_ARTICLES_TRACKER.csv'
    
    rows = []
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows.append(header)
        for row in reader:
            rows.append(row)
            
    print(f"Checking index status for {len(rows)-1} published articles...\n")
    
    # Header:
    # 0: Ticket, 1: Keyword, 2: Article Link, 3: Posted Date, 
    # 4: Has Indexed, 5: Last Check Index Date, 6: Has Tried Request To Index, 7: Last Request Index Date
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    for i in range(1, len(rows)):
        url = rows[i][2]
        has_indexed = rows[i][4]
        
        if has_indexed == "Yes":
            continue
            
        request = {
            'inspectionUrl': url,
            'siteUrl': site_url
        }
        
        try:
            response = service.urlInspection().index().inspect(body=request).execute()
            result = response.get('inspectionResult', {})
            index_status = result.get('indexStatusResult', {}).get('coverageState', 'Unknown')
            
            print(f"[{url.split('/')[-1]}] -> {index_status}")
            
            # Update CSV
            if "Submitted and indexed" in index_status or "Indexed, not submitted in sitemap" in index_status:
                rows[i][4] = "Yes"
            else:
                rows[i][4] = "No"
                
            rows[i][5] = today
            
        except Exception as e:
            print(f"[{url.split('/')[-1]}] -> Error: {str(e)[:100]}")

    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
        
    print("\nCSV Tracker updated with latest index statuses.")

if __name__ == '__main__':
    check_indexing_status()

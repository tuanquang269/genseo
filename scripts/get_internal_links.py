import csv
import sys
import random

def get_links(csv_path):
    power_pages = []
    target_pages = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    avg_pos_str = row.get('Average Position')
                    if avg_pos_str is None or avg_pos_str.strip() == '':
                        continue
                    avg_pos = float(avg_pos_str)
                    
                    clicks_str = row.get('Clicks', '0')
                    if clicks_str is None or clicks_str.strip() == '':
                        clicks_str = '0'
                    clicks = int(clicks_str)
                    
                    imp_str = row.get('Impressions (30 Days)', '0')
                    if imp_str is None or imp_str.strip() == '':
                        imp_str = '0'
                    impressions = int(imp_str)
                    
                    link = row.get('Article Link', '')
                    keyword = row.get('Keyword', '')
                    
                    if not link or link.strip() == '':
                        continue
                        
                    # Power Pages: Clicks > 0 OR Impressions > 100
                    if clicks > 0 or impressions > 100:
                        power_pages.append({'keyword': keyword, 'link': link, 'score': clicks * 10 + impressions})
                    
                    # Target Pages: Position between 5 and 15
                    if 5 <= avg_pos <= 15:
                        target_pages.append({'keyword': keyword, 'link': link, 'pos': avg_pos})
                        
                except ValueError:
                    pass
    except FileNotFoundError:
        print(f"Error: Could not find CSV file at {csv_path}")
        sys.exit(1)

    power_pages.sort(key=lambda x: x['score'], reverse=True)
    target_pages.sort(key=lambda x: x['pos'])

    # Get top 5 of each, then randomly select 1-2 to avoid always linking the exact same page
    top_power = power_pages[:10]
    top_target = target_pages[:10]
    
    selected_power = random.sample(top_power, min(2, len(top_power))) if top_power else []
    selected_target = random.sample(top_target, min(2, len(top_target))) if top_target else []

    print("=== RECOMMENDED INTERNAL LINKS FOR THIS ARTICLE ===")
    print("\n[POWER PAGES] (High Traffic/Impressions) - Link TO these to pass juice:")
    for p in selected_power:
        print(f"- Keyword: {p['keyword']}\n  URL: {p['link']}")
        
    print("\n[TARGET PAGES] (Striking Distance: Pos 5-15) - Link TO these to boost their ranking:")
    for t in selected_target:
        print(f"- Keyword: {t['keyword']}\n  URL: {t['link']}")

if __name__ == "__main__":
    get_links('~/genseo/PUBLISHED_ARTICLES_TRACKER.csv')

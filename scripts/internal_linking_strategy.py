import csv
import sys

def analyze_tracker(csv_path):
    power_pages = []
    target_pages = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Chuyển đổi an toàn
                    avg_pos_str = row.get('Average Position')
                    if avg_pos_str is None or avg_pos_str.strip() == '':
                        continue
                    avg_pos = float(avg_pos_str)
                    
                    clicks_str = row.get('Clicks', '0')
                    if clicks_str is None or clicks_str.strip() == '':
                        clicks_str = '0'
                    clicks = int(clicks_str)
                    
                    link = row.get('Article Link', '')
                    keyword = row.get('Keyword', '')
                    
                    if avg_pos <= 3 and clicks > 0:
                        power_pages.append({'keyword': keyword, 'link': link, 'pos': avg_pos, 'clicks': clicks})
                    elif 5 <= avg_pos <= 10:
                        target_pages.append({'keyword': keyword, 'link': link, 'pos': avg_pos, 'clicks': clicks})
                except ValueError:
                    pass
    except FileNotFoundError:
        print(f"Error: Could not find CSV file at {csv_path}")
        return

    print("=== POWER PAGES (Nguồn Link - Top 1-3) ===")
    for p in sorted(power_pages, key=lambda x: x['clicks'], reverse=True)[:5]:
        print(f"- {p['keyword']} (Pos: {p['pos']}, Clicks: {p['clicks']}) -> {p['link']}")
        
    print("\n=== TARGET PAGES (Đích đến - Cận Top 5-10) ===")
    for p in sorted(target_pages, key=lambda x: x['pos'])[:5]:
        print(f"- {p['keyword']} (Pos: {p['pos']}, Clicks: {p['clicks']}) -> {p['link']}")

if __name__ == "__main__":
    analyze_tracker('~/genseo/PUBLISHED_ARTICLES_TRACKER.csv')

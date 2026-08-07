import csv
import sys
from datetime import datetime

def generate_tickets(csv_path, output_path):
    candidates = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                imp_str = row.get('Impressions (30 Days)', '0').strip()
                if not imp_str: imp_str = '0'
                impressions = int(imp_str)
                
                pos_str = row.get('Average Position', '0').strip()
                if not pos_str: continue
                pos = float(pos_str)
                
                clicks_str = row.get('Clicks', '0').strip()
                if not clicks_str: clicks_str = '0'
                clicks = int(clicks_str)
                
                link = row.get('Article Link', '').strip()
                keyword = row.get('Keyword', '').strip()
                
                if not link or not keyword or impressions < 5:
                    continue
                    
                ctr = (clicks / impressions) * 100 if impressions > 0 else 0
                
                tier = 0
                action = ""
                diagnostic = ""
                
                if pos > 15:
                    tier = 1 # Bleeding / Major Opps
                    action = "[DEEP REFRESH]"
                    diagnostic = f"Rank is poor (Pos {pos:.1f}). High search volume (Impressions: {impressions}) but low visibility."
                elif 5 < pos <= 15:
                    tier = 2 # Striking distance
                    action = "[CONTENT EXPANSION & REFRESH]"
                    diagnostic = f"Striking Distance (Pos {pos:.1f}). Impressions: {impressions}. Needs an extra push to hit Top 3."
                elif pos <= 5 and ctr < 3.0:
                    tier = 3 # CTR Trap
                    action = "[HEADLINE REWRITE]"
                    diagnostic = f"Top Ranking (Pos {pos:.1f}) but poor CTR ({ctr:.2f}%). Impressions: {impressions}, Clicks: {clicks}."
                else:
                    continue
                    
                candidates.append({
                    'tier': tier,
                    'action': action,
                    'diagnostic': diagnostic,
                    'impressions': impressions,
                    'pos': pos,
                    'ctr': ctr,
                    'clicks': clicks,
                    'link': link,
                    'keyword': keyword
                })
            except Exception as e:
                pass

    # Sort candidates
    tier1 = sorted([c for c in candidates if c['tier'] == 1], key=lambda x: x['impressions'], reverse=True)
    tier2 = sorted([c for c in candidates if c['tier'] == 2], key=lambda x: x['impressions'], reverse=True)
    tier3 = sorted([c for c in candidates if c['tier'] == 3], key=lambda x: x['impressions'], reverse=True)
    
    selected = []
    
    # Try to get 30 tickets
    # Distribute: take all Tier 1 if good, then Tier 2, then Tier 3
    selected.extend(tier1[:10])
    selected.extend(tier2[:15])
    selected.extend(tier3[:5])
    
    # If not enough, grab more from wherever available
    if len(selected) < 30:
        remaining_t1 = [c for c in tier1 if c not in selected]
        remaining_t2 = [c for c in tier2 if c not in selected]
        remaining_t3 = [c for c in tier3 if c not in selected]
        all_remaining = sorted(remaining_t1 + remaining_t2 + remaining_t3, key=lambda x: x['impressions'], reverse=True)
        needed = 30 - len(selected)
        selected.extend(all_remaining[:needed])
        
    # Re-sort selected by Tier, then by Impressions
    selected.sort(key=lambda x: (x['tier'], -x['impressions']))

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 🔄 GENSEO 2nd Round Content Refresh Schedule (30 Tickets)\n\n")
        f.write("> **System:** Analyzed GSC Data (Impressions, Position, Clicks) to identify the highest ROI refresh opportunities.\n\n")
        
        current_tier = 0
        ticket_num = 1
        
        for c in selected:
            if c['tier'] != current_tier:
                current_tier = c['tier']
                if current_tier == 1:
                    f.write("## 🚨 Tier 1: The Bleeding Giants & Major Opportunities (Pos > 15, High Imps)\n")
                    f.write("*Requires complete restructuring, new entities, and aggressive internal linking.*\n\n")
                elif current_tier == 2:
                    f.write("## 🍏 Tier 2: Striking Distance (Pos 5 - 15)\n")
                    f.write("*Page 2 / Low Page 1. Needs content expansion, updated FAQs, and fresh images to push into Top 3.*\n\n")
                elif current_tier == 3:
                    f.write("## 🪤 Tier 3: The CTR Trap (Pos 1 - 5, Low CTR)\n")
                    f.write("*Ranking well but ignored by users. Needs aggressive Headline rewrites and Meta Description optimization.*\n\n")
            
            f.write(f"### 📝 Ticket #{ticket_num} - {c['action']}\n")
            f.write(f"- **Target URL**: {c['link']}\n")
            f.write(f"- **Primary Keyword**: `{c['keyword']}`\n")
            f.write(f"- **Diagnostic**: {c['diagnostic']}\n")
            f.write(f"- **Action**: [PENDING]\n")
            f.write("**🤖 Auto-Publish Trigger Prompt:**\n")
            f.write("```markdown\n")
            
            if c['action'] == "[HEADLINE REWRITE]":
                f.write(f"/genseo-auto-publish [REFRESH EXISTING]. The article {c['link']} suffers terrible CTR. Execute a {c['action']} targeting \"{c['keyword']}\" to aggressively match search intent and drive clicks. Default BLOG_ID is 104008483131.\n")
            else:
                f.write(f"/genseo-auto-publish [REFRESH EXISTING]. The article {c['link']} suffers decay or is stuck. Execute a {c['action']} targeting \"{c['keyword']}\". Restructure headings, add updated tables, and ensure strong internal linking. Default BLOG_ID is 104008483131.\n")
                
            f.write("```\n\n")
            ticket_num += 1

if __name__ == "__main__":
    generate_tickets('/Users/kevinkreative/genseo/PUBLISHED_ARTICLES_TRACKER.csv', '/Users/kevinkreative/genseo/2ndRound_30_tickets_refresh.md')
    print("Successfully generated /Users/kevinkreative/genseo/2ndRound_30_tickets_refresh.md")

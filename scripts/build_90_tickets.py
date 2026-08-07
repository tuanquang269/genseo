import pandas as pd
import sys, os, datetime

sys.path.append(os.path.expanduser("/Users/kevinkreative/genseo/scripts/"))
import gsc_fetcher

file_path = "~/path/to/your/keyword-report.xlsx"

try:
    df = pd.read_excel(file_path, skiprows=2)
    if "Search term" not in df.columns:
        df = pd.read_excel(file_path)
    df["Clicks"] = pd.to_numeric(df["Clicks"], errors="coerce").fillna(0)
    df["Impr."] = pd.to_numeric(df["Impr."], errors="coerce").fillna(0)
    
    # Pre-clean
    df["Search term"] = df["Search term"].astype(str)
    df = df[~df["Search term"].str.contains("ultimate|sup", case=False, na=False)]
    df = df[~df["Search term"].str.contains("Total:", case=False, na=False)]
    ads_data = df.sort_values(by=["Clicks", "Impr."], ascending=False).to_dict('records')
except Exception as e:
    print("Error reading excel:", e)
    ads_data = []

print("Fetching GSC Cannibalization Data...")
service = gsc_fetcher.get_service()
today = datetime.date.today()
t_end = today.strftime("%Y-%m-%d")
t_start = (today - datetime.timedelta(days=180)).strftime("%Y-%m-%d")

req = {
    "startDate": t_start,
    "endDate": t_end,
    "dimensions": ["query", "page"],
    "dimensionFilterGroups": [{"filters": [{"dimension": "country", "operator": "equals", "expression": "usa"}]}],
    "rowLimit": 5000
}
res = service.searchanalytics().query(siteUrl="https://wellnessnest.co/", body=req).execute()

cannibal_map = {}
for row in res.get("rows", []):
    q = row["keys"][0]
    page = row["keys"][1]
    if q not in cannibal_map:
        cannibal_map[q] = []
    cannibal_map[q].append(page)

all_keywords = []
for row in ads_data:
    all_keywords.append({"q": row["Search term"], "impr": row["Impr."], "source": "Ads"})

req_gsc = {
    "startDate": t_start,
    "endDate": t_end,
    "dimensions": ["query"],
    "dimensionFilterGroups": [{"filters": [{"dimension": "country", "operator": "equals", "expression": "usa"}]}],
    "rowLimit": 3000
}
res_gsc = service.searchanalytics().query(siteUrl="https://wellnessnest.co/", body=req_gsc).execute()
for row in res_gsc.get("rows", []):
    q = row["keys"][0]
    impr = row["impressions"]
    if "ultimate" not in q.lower() and "sup" not in q.lower():
        all_keywords.append({"q": q, "impr": impr, "source": "GSC"})

seen = set()
deduped = []
all_keywords.sort(key=lambda x: x["impr"], reverse=True)
for item in all_keywords:
    if item["q"] not in seen:
        seen.add(item["q"])
        deduped.append(item)

from collections import defaultdict
clusters = defaultdict(list)
for item in deduped:
    q = str(item["q"]).lower()
    if len(q.split()) < 2: continue
    
    if "whey" in q or "protein" in q: key = "Whey & Protein"
    elif "creatine" in q: key = "Creatine"
    elif "mass" in q or "gainer" in q: key = "Mass Gainers"
    elif "pre workout" in q or "pump" in q: key = "Pre-Workout"
    elif "amino" in q or "bcaa" in q or "eaa" in q: key = "Amino Acids"
    elif "fat" in q or "carnitine" in q or "loss" in q: key = "Fat Burners"
    elif "myprotein" in q: key = "MyProtein Brand"
    elif "mutant" in q: key = "Mutant Brand"
    elif "optimum nutrition" in q or " on " in q: key = "Optimum Nutrition Brand"
    elif "bottle" in q or "shaker" in q or "owala" in q: key = "Accessories"
    else: key = "General Fitness & Health"
    
    clusters[key].append(item["q"])

articles = []
for topic_cat, kws in clusters.items():
    for i in range(0, len(kws), 4):
        chunk = kws[i:i+4]
        if len(chunk) < 2: continue
        
        has_cannibalization = False
        for target_kw in chunk:
            target_blogs = [p for p in cannibal_map.get(target_kw, []) if "/blogs/" in p]
            if target_blogs:
                has_cannibalization = True
                break
                
        if has_cannibalization:
            continue
            
        articles.append({"category": topic_cat, "keywords": chunk})
        if len(articles) >= 90: break
    if len(articles) >= 90: break

out_lines = ["# 🗓️ 30-Day Automated SEO Content Schedule (3 Articles / Day)\n"]
out_lines.append("*Target Geo: US. Goal: Dominate the local SERP with 90 high-value contextual topics.*")
out_lines.append("> 💡 **How to run this:** Copy the Trigger Prompt for the specific ticket and paste it to the AI. It will auto-execute the entire pipeline.\n\n")

day = 1
for i, art in enumerate(articles[:90]):
    if i % 3 == 0:
        out_lines.append(f"## 🌅 Day {day}")
        day += 1
        
    main_kw = art["keywords"][0].title()
    all_kws_str = ", ".join(art["keywords"])

    action = "[NEW ARTICLE]"
    ranked_url = "None"
            
    out_lines.append(f"### 📝 Ticket #{i+1} - {art['category']}")
    out_lines.append(f"- **Primary Keyword**: `{art['keywords'][0]}`")
    out_lines.append(f"- **Secondary Keywords**: `{all_kws_str}`")
    out_lines.append(f"- **Action**: {action}")
    out_lines.append(f"**🤖 Auto-Publish Trigger Prompt:**")
    out_lines.append("```markdown")
    out_lines.append(f"/genseo-auto-publish CREATE A [NEW ARTICLE]. Title Focus: \"The Ultimate Guide to {main_kw} in the US\". Target Keywords: {all_kws_str}. Default BLOG_ID is 104008483131.")
    out_lines.append("```\n")

with open("/Users/kevinkreative/genseo/GENSEO_30_DAY_SCHEDULE.md", "w") as f:
    f.write("\n".join(out_lines))

print("Done! Generated 90 articles plan.")

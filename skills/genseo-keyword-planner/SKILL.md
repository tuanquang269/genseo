---
name: genseo-keyword-planner
description: >
  Use when the user asks to "lên kế hoạch từ khóa", "phân nhóm từ khóa", "topic clustering", 
  or when the user provides a Google Ads or GSC exported CSV/Excel and wants to turn them into SEO Content Plans.
  Do NOT use when the user just wants to find a single keyword (use read_url_content or search_web instead).
metadata: {"clawdbot":{"emoji":"📊","requires":{"commands":["python3"]},"os":["linux","darwin","win32"]}}
---

# GenSeo Keyword Planner

Turns a raw list of keywords (e.g. from Google Ads, GSC, Ahrefs) into structured SEO Content Plans using Topic Clustering.

## When to Use
- User provides a CSV/Excel file of keywords and asks for a content plan.
- User asks to fetch data directly from Google Search Console.
- Core intent is to group related keywords (Topic Cluster).

## Steps

1. **Understand Input (CRITICAL):**
   - **Data Source:** Check if the user provided a local file. If NOT, ask for their GSC Site URL and run `python3 ~/genseo/scripts/gsc_fetcher.py fetch_top_keywords <SITE_URL>` to download the top 4000 queries. If `credentials.json` is missing, inform the user to place it in `~/genseo/scripts/credentials.json`.
   - **MUST VALIDATE Target Language and Target Geography (Geo):** Ask the user or deduce from the website (e.g. "the US" -> English). All output MUST strictly follow this Target Language.
   - **MANDATORY CLEANING:** When reading exported files (like Google Ads `.xlsx`), you MUST strip out any platform-generated summary footer rows (e.g. words starting with "Total: Account", "Total: Search terms", or missing search terms) before beginning any clustering. Never include "Total:" as a keyword.

2. **Run Analysis & Clustering:**
   - Filter out branded or irrelevant terms, sort by the core metric (e.g. Impressions, Clicks), and cluster them.
   - Divide them into manageable plans (20-200 keywords per plan).

3. **Cannibalization Check (CRITICAL PRE-REQUISITE):**
   - BEFORE proposing any new article titles, you MUST check if the keywords in each cluster already rank on the website.
   - Run a Python script utilizing `gsc_fetcher` (or search the website directly if no GSC available) to see if existing URLs already rank for these top keywords.
   - If an existing URL (especially a Blog URL) ranks for the target keywords, **do not propose a new article**. You must mandate updating the existing article.

4. **Format Output:**
   - Group the clustered keywords logically. Assign each group a working Title, Search Intent, and Target Audience (*All in the Target Language*).
   - **Actionable Brief Ideas MUST be strictly tagged:** 
     - Tag `[REFRESH EXISTING]` and provide the URL if the site already has a related article.
     - Tag `[NEW ARTICLE]` only if there is absolutely no existing coverage.
   - Output structured plans or save them to text/CSV files.

## Quick Reference
- Standard chunk size for GenSeo: 20 -> 200 keywords per plan.
- Command for GSC: `python3 ~/genseo/scripts/gsc_fetcher.py fetch_top_keywords <SITE_URL>`

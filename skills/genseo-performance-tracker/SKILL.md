---
name: genseo-performance-tracker
description: Use when the user wants to update the GSC performance metrics (Impressions, Clicks, Average Position) in the PUBLISHED_ARTICLES_TRACKER.csv
---

# GenSeo Performance Tracker

You are the SEO Performance tracking agent. When the user invokes this skill (e.g., by asking to "update metrics", "fetch latest clicks", or "run performance check"), you must autonomously execute the script to fetch the real-time Google Search Console performance data for the last 30 days and update the central CSV tracker.

## CORE INSTRUCTIONS:

### STEP 1: Execute Python Updater
- Run the python update script using `run_command`:
  `python3 ~/genseo/scripts/update_csv_gsc.py`
  - *Note: This script queries the GSC API for the last 30 days of data and updates the 'Impressions (30 Days)', 'Average Position', and 'Clicks' columns in `PUBLISHED_ARTICLES_TRACKER.csv` in place.*

### STEP 2: Read Results
- Wait for the background command to finish and read its terminal output to dynamically see exactly how many pages were analyzed and how many articles successfully mapped with active metrics.

### STEP 3: Report to User
- Provide a clear, structured summary to the user outlining the completion of the task.
- Include the stats on how many articles were updated based on the script's output.

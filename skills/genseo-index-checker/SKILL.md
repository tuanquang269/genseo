---
name: genseo-index-checker
description: >
  Autonomous script to check the indexing status of all un-indexed published articles across the Shopify store and update the CSV tracker.
metadata: {"clawdbot":{"emoji":"🔍","requires":{"commands":["python3"]},"os":["linux","darwin","win32"]}}
---

# GenSeo Index Checker

You are the SEO Indexing verification agent. When the user invokes this skill, you must autonomously execute the checking workflow to fetch the real-time Google Search Console index status of recently published articles and update the central CSV tracker.

## CORE INSTRUCTIONS:

### STEP 1: Execute Python Checker
- Run the python verification script using `run_command`:
  `python3 ~/genseo/scripts/check_indexing.py`
  - *Note: This script will automatically parse `PUBLISHED_ARTICLES_TRACKER.csv`, skip anything that is already identically marked as "Yes", query the GSC URL Inspection API for any "No" values, and rewrite the CSV in place with updated statuses and the current timestamp.*

### STEP 2: Read Results
- Wait for the background command to finish and read its terminal output to dynamically see exactly which URLs were successfully queried and what standard googlebot response was received (e.g. "Discovered - currently not indexed", "Submitted and indexed", etc).

### STEP 3: Report to User
- Provide a clear, structured summary to the user outlining the changes. 
- Celebrate any articles that magically changed from "No" to "Yes" today.
- Reassure the user that articles marked "Discovered - currently not indexed" are securely in the queue.

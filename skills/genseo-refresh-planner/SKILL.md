---
name: genseo-refresh-planner
description: >
  Use when the user asks to "build a refresh schedule", "xây dựng lịch refresh", 
  "lọc bài cũ", or "decay analysis". This skill runs the Python script to fetch GSC data 
  and Shopify Articles and outputs a prioritized `GENSEO_REFRESH_SCHEDULE.md` file.
metadata: {"clawdbot":{"emoji":"📅","requires":{"commands":["python3"]},"os":["linux","darwin","win32"]}}
---

# GenSeo Refresh Planner

This skill identifies decaying and underperforming content on Shopify by cross-referencing Google Search Console (GSC) ranking data with Shopify's Article APIs.

## When to Use
- User asks: "Build a list of URLs needed for content refresh"
- User asks for "decay analysis"

## Workflow

1. **Information Verification:**
   - Ensure you are operating within the `genseo` workspace.
   - The orchestrator script is located at `scripts/build_refresh_tickets.py`.

2. **Execute the Builder Script:**
   - Run the builder using the `run_command` tool:
     `python3 scripts/build_refresh_tickets.py`
   - Wait for it to fetch GSC data and map `ARTICLE_ID` from Shopify.

3. **Verify the Output:**
   - Use `view_file` to inspect `GENSEO_REFRESH_SCHEDULE.md` to ensure the layout contains the exact Auto-Publish Trigger Prompts.

4. **Report Back:**
   - Present the top 3 highest priority Tickets from Phase 1 to the user.
   - Let them know that they can start running the tickets using the orchestrator!

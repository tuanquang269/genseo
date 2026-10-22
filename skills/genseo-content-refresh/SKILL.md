---
name: genseo-content-refresh
description: >
  Use when the user asks to "làm mới nội dung", "content refresh", "cập nhật bài viết cũ", 
  or when the user wants to improve the ranking of an existing article using GSC data (Google Search Console).
metadata: {"clawdbot":{"emoji":"🔄","requires":{"commands":["python3"]},"os":["linux","darwin","win32"]}}
---

# GenSeo Content Refresh (The Patching Muscle)

This skill acts as the Execution layer for the "Feedback Loop". It takes a Strategic Brief (from the `genseo-seo-strategist`) and patches an existing live article.

## When to Use
- The Orchestrator detected a ranking drop, the Strategist formulated a Brief, and now the live article needs to be refreshed.
- User wants to patch an existing article with new AEO/GEO formats.

## Steps

0. **Acknowledge Brief:**
   - Confirm you have received a Strategic Brief from the Strategist.

1. **Fetch Existing Content:**
   - Ask the user for the Shopify Blog ID or Live URL. 
   - Use the `read_url_content` tool to pull the current text of the live article.

2. **Patching (Execution):**
   - Inject the new optimizations dictated by the Strategist (e.g., adding an Entity Table, restructuring the top paragraph, or adding the strict `## Frequently Asked Questions` block).
   - *CRITICAL:* Do not ruin the overall flow. Only apply the surgical patches requested by the Brief.
   - Do not invent a testimonial, a star rating, or a "we tested it" line. A first-hand quote is appended only when `python3 scripts/experience_block.py render --draft <draft>.md` prints one (`usage_allowed: true` in `data/experience_quotes.json`). Empty stdout means add nothing. See `docs/first-hand-experience-block.md`.
   - Retain existing Shopify image CDN links wherever possible to avoid broken images.
   - **⚠️ Image Rule During Refresh (MANDATORY):** If the refresh adds or expands coverage of any product that does not already have a dedicated image in that section, you MUST generate one. Follow the same rule as new articles: **1 lifestyle image per product, per section**. Download the real product image from the Shopify CDN first (`curl -o`), then pass it into `ImagePaths` when calling `generate_image`. Never add a new product section without a corresponding image.

3. **Publish to Shopify (UPDATE MODE):**
   - Ask the user for the `ARTICLE_ID` associated with this live post.
   - Write the patched markdown to a local file.
   - Run the publisher using the `update` command to silently overwrite the live article (preventing duplicates):
     `python3 ~/genseo/scripts/shopify_publisher.py update <YOUR_SAVED_MD> <BLOG_ID> <ARTICLE_ID>`
     *(Note: Ensure the local script handles overwriting effectively and does not duplicate).*

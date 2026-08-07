---
name: genseo-shopify-publisher
description: >
  Publish SEO generated markdown articles directly to the Shopify store. 
  Handles automated HTML conversion, image upload to Shopify CDN, and post-publish image verification.
metadata: {"clawdbot":{"emoji":"🚀","requires":{"commands":["python3"]},"os":["linux","darwin","win32"]}}
---

# GenSeo Shopify Publisher

A tool to auto-publish Markdown articles straight to your Shopify Blog.

## Prerequisites
- Custom App Client ID and Secret from Shopify Partner Dashboard.
- Knowing your `.myshopify.com` exact shop url.

## Steps

1. **Authentication Check:**
   - If this is the FIRST time the user is pushing an article, ask the user for:
     1. Shop URL (e.g. `your-store.myshopify.com`)
     2. Client ID
     3. Client Secret
   - Before running the auth command, tell the user they MUST go to their App's setup page in Shopify Partners and Add "Allowed redirection URL": `http://localhost:3456/`
   - Run: `python3 ~/genseo/scripts/shopify_publisher.py auth <SHOP> <CLIENT_ID> <SECRET>`
   - The user must click the generated link to approve the App.

2. **Blog ID Query:**
   - Ask the user which Blog ID they want to publish the article to (Shopify has multiple blogs, e.g. "News", "Fitness Blog"). If the user doesn't know, provide instructions on how to find the Blog ID (e.g., look at the URL in the Shopify Admin when managing that blog).

3. **Publishing:**
   - Once authenticated, and once you have the Blog ID.
   - Run the command to publish the selected markdown article path:
   `python3 ~/genseo/scripts/shopify_publisher.py publish <MD_FILEPATH> <BLOG_ID>`

4. **Post-Publish Image Verification (MANDATORY — DO NOT SKIP):**
   - The publisher script now automatically runs image verification and prints a report.
   - **You MUST read the verification output** and check for one of these lines:
     - ✅ `IMAGE VERIFICATION PASSED` → Images are live. Safe to report success to user.
     - ⚠ `PARTIAL` → Some images uploaded but not all. Warn the user.
     - ✗ `IMAGE VERIFICATION FAILED` → Images are broken. Run patch script immediately:
       `python3 ~/genseo/scripts/patch_images.py <ARTICLE_ID>`
   - **NEVER tell the user the article is complete until you see the ✅ PASSED line.**

## Quick Notes
- The python script automatically converts the Markdown (including links) to Shopify-compatible HTML.
- Images are uploaded via the Shopify Files GraphQL API (staged upload) — not theme assets.
- The draft markdown file is updated in-place with real CDN URLs after successful upload.
- If images fail, the `patch_images.py` script can fix any published article by article ID.

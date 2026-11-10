# Mobile clutter audit — wellnessnest.co blog — 2026-10-21

Read-only public GET with a mobile Safari user agent. No Shopify Admin API, no theme edit, no publish. Fixes below are suggestions.

## Why these signals

The vault at ~/PATI/LLM-Wiki has no `90-sources/search-engine-land/sel-digest-2026-10-21.md`. The freshest digest on disk is `sel-digest-2026-10-20.md` (content pruning, social search, local AI). The clutter spark is Search Engine Land, 20 October 2026, [Google's clutterScore](https://searchengineland.com/google-clutterscore-seo-497178): intrusive pop-ups, sticky and floating layers, third-party scripts, and repeated templates. That article says the leaked field has no public formula, so this audit does not invent a clutterScore. `knowledge_base/AEO_GEO_GUIDELINES.md` already forbids a forced interstitial on an article. Existing writers were not extended: `scripts/patch_mobile.py` pushes collection HTML, `scripts/audit_article_images.py` reads the Admin API, and `scripts/patch_tables.py` writes article bodies. The spacer-image skip and the `article-table-wrapper` name are reused as checks only.

## How a number is labeled

A viewport fact this GET cannot see is the string `unknown`. Declared CSS pixels are the sizes written in the page, not a layout measurement. `cls` is unknown on every post.

## Selection

Selected the 5 newest `/blogs/news/` entries from the public Atom feed. Product, collection, home, checkout, and landing URLs are ignored. The tracker is a cross-check, not the sort. Shared titles in this set: vaginal probiotics on an empty stomach: us guide (vaginal-probiotics-on-an-empty-stomach-us-guide-1, vaginal-probiotics-on-an-empty-stomach-us-guide). Consolidation is a separate decision and needs Kevin GO. Feed: https://wellnessnest.co/blogs/news.atom.

| Published | Handle | Tracker | Highest |
|---|---|---|---|
| 2026-10-20T20:40:36-07:00 | `vaginal-probiotics-on-an-empty-stomach-us-guide-1` | CA1017-6 | high |
| 2026-10-20T20:11:03-07:00 | `vaginal-probiotics-on-an-empty-stomach-us-guide` | no | high |
| 2026-10-20T19:16:26-07:00 | `nmn-while-traveling-with-food-5-us-tips` | CA1017-5 | high |
| 2026-10-20T18:14:11-07:00 | `how-much-turkesterone-on-rest-days-in-the-us` | CA1017-4 | high |
| 2026-10-20T02:18:35-07:00 | `creatine-gummies-while-traveling-how-much-us-2026` | CA1017-3 | high |

## Repeated theme findings

These high or medium theme issues used the same wording on every fetched post.

- **popups_sticky_interstitials** (high). Initial HTML references unexpected host(s): shopify.jsdeliver.cloud, cartassure, 240.1.2.3.
  - Remove the unexpected script and any header item that references it, after a theme backup. Report only, needs Kevin GO.
- **popups_sticky_interstitials** (high). Shop-this-article CSS sets position:fixed and stretches it to both side edges along the bottom. Trigger aria-expanded is false. Whether JavaScript hides the control is unknown.
  - Do not pin a shop bar over the article on mobile. Keep the product mention inline. Report only, needs Kevin GO.
- **popups_sticky_interstitials** (medium). Overlay-vendor script host(s) loaded: static.klaviyo.com. No vendor form was required to record the script. Whether a popup opens after JavaScript is unknown.
  - Replace a full-screen email popup with an inline form that does not cover the article. Report only, needs Kevin GO.
- **tap_targets** (medium). Declared box 40.0x40.0 px on .sta__close is under 48 px. Rendered size is unknown.
  - Raise the declared width and height of that control to at least 48px. Report only, needs Kevin GO.
- **font_line_length** (medium). Declared font-size under 16px: .sta__trigger at 13.0, .sta__trigger-label at 13.0, .sta__count at 12.0.
  - Use at least 16px for the shop-bar label. Report only, needs Kevin GO.
- **above_the_fold** (medium). One ticker sits before the H1, repeated as 36 item nodes (3 unique message(s)). Rendered bar height is unknown. Above-the-fold element count is unknown.
  - Keep a single line in the ticker instead of repeating the same messages in the HTML. Report only, needs Kevin GO.

## Per post

### Vaginal Probiotics on an Empty Stomach: US Guide

- URL: https://wellnessnest.co/blogs/news/vaginal-probiotics-on-an-empty-stomach-us-guide-1
- Published: 2026-10-20T20:40:36-07:00
- Article words: 1292
- Highest severity: high

#### content_start — low

- **low** (article). The article body has 1 block element(s) before the first answer paragraph.
  - Move the answer paragraph above the introductory blocks. Suggestion only. This audit does not edit the article.

#### popups_sticky_interstitials — high

- **high** (theme). Initial HTML references unexpected host(s): shopify.jsdeliver.cloud, cartassure, 240.1.2.3.
  - Remove the unexpected script and any header item that references it, after a theme backup. Report only, needs Kevin GO.
- **high** (theme). Shop-this-article CSS sets position:fixed and stretches it to both side edges along the bottom. Trigger aria-expanded is false. Whether JavaScript hides the control is unknown.
  - Do not pin a shop bar over the article on mobile. Keep the product mention inline. Report only, needs Kevin GO.
- **medium** (theme). Overlay-vendor script host(s) loaded: static.klaviyo.com. No vendor form was required to record the script. Whether a popup opens after JavaScript is unknown.
  - Replace a full-screen email popup with an inline form that does not cover the article. Report only, needs Kevin GO.
- **low** (theme). position:sticky is declared for .section-header.
  - A sticky header is theme chrome. Leave it unless it stacks with the ticker and the shop bar. Report only, needs Kevin GO.
- **info** (theme). A CRO app script is on the page. What it injects on this mobile GET is unknown.
  - No change suggested until the injected layer is identified. Report only, needs Kevin GO.
- **info** (theme). Section shell(s) with no control text in the initial HTML: promo-popup, global-music-player, scroll-to-top. Rendered behavior is unknown.
  - No change suggested from the empty shell alone. Report only, needs Kevin GO.

#### images — high

- **high** (article). 4 content image(s) have no width and height and no aspect-ratio style. CLS is unknown.
  - Add width and height attributes that match each file's pixel size. Suggestion only. This audit does not edit the article.
- **info** (theme). The article header image carries class mobile-hidden. Whether the phone hides it is unknown without the theme stylesheet.
  - No change suggested from the class name alone. Report only, needs Kevin GO.

#### cta_density — medium

- **medium** (mixed). 5 CTA block(s) across 1292 article words, 3.87 per 1,000 words (inline product links 3, shop cards 1, newsletter forms 1).
  - Keep one product mention in the article. The shop card and the email form are theme sections. Report only, needs Kevin GO. Suggestion only. This audit does not edit the article.
- **low** (article). The same product URL is linked 3 times in the article body.
  - Keep a single product link near the label mention. Suggestion only. This audit does not edit the article.

#### wide_overflow — medium

- **medium** (article). 1 table(s) in the article have no overflow wrapper. Whether they overflow a phone viewport is unknown.
  - Wrap each table in a div with class article-table-wrapper and overflow-x:auto. Do not run scripts/patch_tables.py from this audit; that script writes article HTML. Suggestion only. This audit does not edit the article.

#### tap_targets — medium

- **medium** (theme). Declared box 40.0x40.0 px on .sta__close is under 48 px. Rendered size is unknown.
  - Raise the declared width and height of that control to at least 48px. Report only, needs Kevin GO.

#### font_line_length — medium

- **medium** (theme). Declared font-size under 16px: .sta__trigger at 13.0, .sta__trigger-label at 13.0, .sta__count at 12.0.
  - Use at least 16px for the shop-bar label. Report only, needs Kevin GO.
- **info** (article). Relative font-size present (0.85em). Rendered px is unknown.
  - No change suggested until the computed pixel size is known. Suggestion only. This audit does not edit the article.

#### above_the_fold — medium

- **medium** (theme). One ticker sits before the H1, repeated as 36 item nodes (3 unique message(s)). Rendered bar height is unknown. Above-the-fold element count is unknown.
  - Keep a single line in the ticker instead of repeating the same messages in the HTML. Report only, needs Kevin GO.

### Vaginal Probiotics on an Empty Stomach: US Guide

- URL: https://wellnessnest.co/blogs/news/vaginal-probiotics-on-an-empty-stomach-us-guide
- Published: 2026-10-20T20:11:03-07:00
- Article words: 1275
- Highest severity: high

#### content_start — low

- **low** (article). The article body has 1 block element(s) before the first answer paragraph.
  - Move the answer paragraph above the introductory blocks. Suggestion only. This audit does not edit the article.

#### popups_sticky_interstitials — high

- **high** (theme). Initial HTML references unexpected host(s): shopify.jsdeliver.cloud, cartassure, 240.1.2.3.
  - Remove the unexpected script and any header item that references it, after a theme backup. Report only, needs Kevin GO.
- **high** (theme). Shop-this-article CSS sets position:fixed and stretches it to both side edges along the bottom. Trigger aria-expanded is false. Whether JavaScript hides the control is unknown.
  - Do not pin a shop bar over the article on mobile. Keep the product mention inline. Report only, needs Kevin GO.
- **medium** (theme). Overlay-vendor script host(s) loaded: static.klaviyo.com. No vendor form was required to record the script. Whether a popup opens after JavaScript is unknown.
  - Replace a full-screen email popup with an inline form that does not cover the article. Report only, needs Kevin GO.
- **low** (theme). position:sticky is declared for .section-header.
  - A sticky header is theme chrome. Leave it unless it stacks with the ticker and the shop bar. Report only, needs Kevin GO.
- **info** (theme). A CRO app script is on the page. What it injects on this mobile GET is unknown.
  - No change suggested until the injected layer is identified. Report only, needs Kevin GO.
- **info** (theme). Section shell(s) with no control text in the initial HTML: promo-popup, global-music-player, scroll-to-top. Rendered behavior is unknown.
  - No change suggested from the empty shell alone. Report only, needs Kevin GO.

#### images — high

- **high** (article). 5 content image(s) have no width and height and no aspect-ratio style. CLS is unknown.
  - Add width and height attributes that match each file's pixel size. Suggestion only. This audit does not edit the article.
- **info** (theme). The article header image carries class mobile-hidden. Whether the phone hides it is unknown without the theme stylesheet.
  - No change suggested from the class name alone. Report only, needs Kevin GO.

#### cta_density — medium

- **medium** (mixed). 5 CTA block(s) across 1275 article words, 3.92 per 1,000 words (inline product links 3, shop cards 1, newsletter forms 1).
  - Keep one product mention in the article. The shop card and the email form are theme sections. Report only, needs Kevin GO. Suggestion only. This audit does not edit the article.
- **low** (article). The same product URL is linked 3 times in the article body.
  - Keep a single product link near the label mention. Suggestion only. This audit does not edit the article.

#### wide_overflow — medium

- **medium** (article). 1 table(s) in the article have no overflow wrapper. Whether they overflow a phone viewport is unknown.
  - Wrap each table in a div with class article-table-wrapper and overflow-x:auto. Do not run scripts/patch_tables.py from this audit; that script writes article HTML. Suggestion only. This audit does not edit the article.

#### tap_targets — medium

- **medium** (theme). Declared box 40.0x40.0 px on .sta__close is under 48 px. Rendered size is unknown.
  - Raise the declared width and height of that control to at least 48px. Report only, needs Kevin GO.

#### font_line_length — medium

- **medium** (theme). Declared font-size under 16px: .sta__trigger at 13.0, .sta__trigger-label at 13.0, .sta__count at 12.0.
  - Use at least 16px for the shop-bar label. Report only, needs Kevin GO.

#### above_the_fold — medium

- **medium** (theme). One ticker sits before the H1, repeated as 36 item nodes (3 unique message(s)). Rendered bar height is unknown. Above-the-fold element count is unknown.
  - Keep a single line in the ticker instead of repeating the same messages in the HTML. Report only, needs Kevin GO.

### NMN While Traveling With Food: 5 US Tips

- URL: https://wellnessnest.co/blogs/news/nmn-while-traveling-with-food-5-us-tips
- Published: 2026-10-20T19:16:26-07:00
- Article words: 1306
- Highest severity: high

#### content_start — info

- **info** (article). The first long paragraph is the start of the article body (184 markup bytes inside the article before that paragraph).
  - No change suggested.

#### popups_sticky_interstitials — high

- **high** (theme). Initial HTML references unexpected host(s): shopify.jsdeliver.cloud, cartassure, 240.1.2.3.
  - Remove the unexpected script and any header item that references it, after a theme backup. Report only, needs Kevin GO.
- **high** (theme). Shop-this-article CSS sets position:fixed and stretches it to both side edges along the bottom. Trigger aria-expanded is false. Whether JavaScript hides the control is unknown.
  - Do not pin a shop bar over the article on mobile. Keep the product mention inline. Report only, needs Kevin GO.
- **medium** (theme). Overlay-vendor script host(s) loaded: static.klaviyo.com. No vendor form was required to record the script. Whether a popup opens after JavaScript is unknown.
  - Replace a full-screen email popup with an inline form that does not cover the article. Report only, needs Kevin GO.
- **low** (theme). position:sticky is declared for .section-header.
  - A sticky header is theme chrome. Leave it unless it stacks with the ticker and the shop bar. Report only, needs Kevin GO.
- **info** (theme). A CRO app script is on the page. What it injects on this mobile GET is unknown.
  - No change suggested until the injected layer is identified. Report only, needs Kevin GO.
- **info** (theme). Section shell(s) with no control text in the initial HTML: promo-popup, global-music-player, scroll-to-top. Rendered behavior is unknown.
  - No change suggested from the empty shell alone. Report only, needs Kevin GO.

#### images — high

- **high** (article). 3 content image(s) have no width and height and no aspect-ratio style. CLS is unknown.
  - Add width and height attributes that match each file's pixel size. Suggestion only. This audit does not edit the article.
- **info** (theme). The article header image carries class mobile-hidden. Whether the phone hides it is unknown without the theme stylesheet.
  - No change suggested from the class name alone. Report only, needs Kevin GO.

#### cta_density — medium

- **medium** (mixed). 6 CTA block(s) across 1306 article words, 4.59 per 1,000 words (inline product links 4, shop cards 1, newsletter forms 1).
  - Keep one product mention in the article. The shop card and the email form are theme sections. Report only, needs Kevin GO. Suggestion only. This audit does not edit the article.
- **low** (article). The same product URL is linked 4 times in the article body.
  - Keep a single product link near the label mention. Suggestion only. This audit does not edit the article.

#### wide_overflow — medium

- **medium** (article). 1 table(s) in the article have no overflow wrapper. Whether they overflow a phone viewport is unknown.
  - Wrap each table in a div with class article-table-wrapper and overflow-x:auto. Do not run scripts/patch_tables.py from this audit; that script writes article HTML. Suggestion only. This audit does not edit the article.

#### tap_targets — medium

- **medium** (theme). Declared box 40.0x40.0 px on .sta__close is under 48 px. Rendered size is unknown.
  - Raise the declared width and height of that control to at least 48px. Report only, needs Kevin GO.

#### font_line_length — medium

- **medium** (theme). Declared font-size under 16px: .sta__trigger at 13.0, .sta__trigger-label at 13.0, .sta__count at 12.0.
  - Use at least 16px for the shop-bar label. Report only, needs Kevin GO.
- **info** (article). Relative font-size present (0.85em). Rendered px is unknown.
  - No change suggested until the computed pixel size is known. Suggestion only. This audit does not edit the article.

#### above_the_fold — medium

- **medium** (theme). One ticker sits before the H1, repeated as 36 item nodes (3 unique message(s)). Rendered bar height is unknown. Above-the-fold element count is unknown.
  - Keep a single line in the ticker instead of repeating the same messages in the HTML. Report only, needs Kevin GO.

### How Much Turkesterone on Rest Days in the US?

- URL: https://wellnessnest.co/blogs/news/how-much-turkesterone-on-rest-days-in-the-us
- Published: 2026-10-20T18:14:11-07:00
- Article words: 1261
- Highest severity: high

#### content_start — info

- **info** (article). The first long paragraph is the start of the article body (184 markup bytes inside the article before that paragraph).
  - No change suggested.

#### popups_sticky_interstitials — high

- **high** (theme). Initial HTML references unexpected host(s): shopify.jsdeliver.cloud, cartassure, 240.1.2.3.
  - Remove the unexpected script and any header item that references it, after a theme backup. Report only, needs Kevin GO.
- **high** (theme). Shop-this-article CSS sets position:fixed and stretches it to both side edges along the bottom. Trigger aria-expanded is false. Whether JavaScript hides the control is unknown.
  - Do not pin a shop bar over the article on mobile. Keep the product mention inline. Report only, needs Kevin GO.
- **medium** (theme). Overlay-vendor script host(s) loaded: static.klaviyo.com. No vendor form was required to record the script. Whether a popup opens after JavaScript is unknown.
  - Replace a full-screen email popup with an inline form that does not cover the article. Report only, needs Kevin GO.
- **low** (theme). position:sticky is declared for .section-header.
  - A sticky header is theme chrome. Leave it unless it stacks with the ticker and the shop bar. Report only, needs Kevin GO.
- **info** (theme). A CRO app script is on the page. What it injects on this mobile GET is unknown.
  - No change suggested until the injected layer is identified. Report only, needs Kevin GO.
- **info** (theme). Section shell(s) with no control text in the initial HTML: promo-popup, global-music-player, scroll-to-top. Rendered behavior is unknown.
  - No change suggested from the empty shell alone. Report only, needs Kevin GO.

#### images — high

- **high** (article). 3 content image(s) have no width and height and no aspect-ratio style. CLS is unknown.
  - Add width and height attributes that match each file's pixel size. Suggestion only. This audit does not edit the article.
- **info** (theme). The article header image carries class mobile-hidden. Whether the phone hides it is unknown without the theme stylesheet.
  - No change suggested from the class name alone. Report only, needs Kevin GO.

#### cta_density — medium

- **medium** (mixed). 5 CTA block(s) across 1261 article words, 3.97 per 1,000 words (inline product links 3, shop cards 1, newsletter forms 1).
  - Keep one product mention in the article. The shop card and the email form are theme sections. Report only, needs Kevin GO. Suggestion only. This audit does not edit the article.
- **low** (article). The same product URL is linked 3 times in the article body.
  - Keep a single product link near the label mention. Suggestion only. This audit does not edit the article.

#### wide_overflow — medium

- **medium** (article). 1 table(s) in the article have no overflow wrapper. Whether they overflow a phone viewport is unknown.
  - Wrap each table in a div with class article-table-wrapper and overflow-x:auto. Do not run scripts/patch_tables.py from this audit; that script writes article HTML. Suggestion only. This audit does not edit the article.

#### tap_targets — medium

- **medium** (theme). Declared box 40.0x40.0 px on .sta__close is under 48 px. Rendered size is unknown.
  - Raise the declared width and height of that control to at least 48px. Report only, needs Kevin GO.

#### font_line_length — medium

- **medium** (theme). Declared font-size under 16px: .sta__trigger at 13.0, .sta__trigger-label at 13.0, .sta__count at 12.0.
  - Use at least 16px for the shop-bar label. Report only, needs Kevin GO.
- **info** (article). Relative font-size present (0.85em). Rendered px is unknown.
  - No change suggested until the computed pixel size is known. Suggestion only. This audit does not edit the article.

#### above_the_fold — medium

- **medium** (theme). One ticker sits before the H1, repeated as 36 item nodes (3 unique message(s)). Rendered bar height is unknown. Above-the-fold element count is unknown.
  - Keep a single line in the ticker instead of repeating the same messages in the HTML. Report only, needs Kevin GO.

### Creatine Gummies While Traveling: How Much? US 2026

- URL: https://wellnessnest.co/blogs/news/creatine-gummies-while-traveling-how-much-us-2026
- Published: 2026-10-20T02:18:35-07:00
- Article words: 1473
- Highest severity: high

#### content_start — info

- **info** (article). The first long paragraph is the start of the article body (184 markup bytes inside the article before that paragraph).
  - No change suggested.

#### popups_sticky_interstitials — high

- **high** (theme). Initial HTML references unexpected host(s): shopify.jsdeliver.cloud, cartassure, 240.1.2.3.
  - Remove the unexpected script and any header item that references it, after a theme backup. Report only, needs Kevin GO.
- **high** (theme). Shop-this-article CSS sets position:fixed and stretches it to both side edges along the bottom. Trigger aria-expanded is false. Whether JavaScript hides the control is unknown.
  - Do not pin a shop bar over the article on mobile. Keep the product mention inline. Report only, needs Kevin GO.
- **medium** (theme). Overlay-vendor script host(s) loaded: static.klaviyo.com. No vendor form was required to record the script. Whether a popup opens after JavaScript is unknown.
  - Replace a full-screen email popup with an inline form that does not cover the article. Report only, needs Kevin GO.
- **low** (theme). position:sticky is declared for .section-header.
  - A sticky header is theme chrome. Leave it unless it stacks with the ticker and the shop bar. Report only, needs Kevin GO.
- **info** (theme). A CRO app script is on the page. What it injects on this mobile GET is unknown.
  - No change suggested until the injected layer is identified. Report only, needs Kevin GO.
- **info** (theme). Section shell(s) with no control text in the initial HTML: promo-popup, global-music-player, scroll-to-top. Rendered behavior is unknown.
  - No change suggested from the empty shell alone. Report only, needs Kevin GO.

#### images — high

- **high** (article). 3 content image(s) have no width and height and no aspect-ratio style. CLS is unknown.
  - Add width and height attributes that match each file's pixel size. Suggestion only. This audit does not edit the article.
- **info** (theme). The article header image carries class mobile-hidden. Whether the phone hides it is unknown without the theme stylesheet.
  - No change suggested from the class name alone. Report only, needs Kevin GO.

#### cta_density — medium

- **medium** (mixed). 5 CTA block(s) across 1473 article words, 3.39 per 1,000 words (inline product links 3, shop cards 1, newsletter forms 1).
  - Keep one product mention in the article. The shop card and the email form are theme sections. Report only, needs Kevin GO. Suggestion only. This audit does not edit the article.
- **low** (article). The same product URL is linked 3 times in the article body.
  - Keep a single product link near the label mention. Suggestion only. This audit does not edit the article.

#### wide_overflow — medium

- **medium** (article). 1 table(s) in the article have no overflow wrapper. Whether they overflow a phone viewport is unknown.
  - Wrap each table in a div with class article-table-wrapper and overflow-x:auto. Do not run scripts/patch_tables.py from this audit; that script writes article HTML. Suggestion only. This audit does not edit the article.

#### tap_targets — medium

- **medium** (theme). Declared box 40.0x40.0 px on .sta__close is under 48 px. Rendered size is unknown.
  - Raise the declared width and height of that control to at least 48px. Report only, needs Kevin GO.

#### font_line_length — medium

- **medium** (theme). Declared font-size under 16px: .sta__trigger at 13.0, .sta__trigger-label at 13.0, .sta__count at 12.0.
  - Use at least 16px for the shop-bar label. Report only, needs Kevin GO.

#### above_the_fold — medium

- **medium** (theme). One ticker sits before the H1, repeated as 36 item nodes (3 unique message(s)). Rendered bar height is unknown. Above-the-fold element count is unknown.
  - Keep a single line in the ticker instead of repeating the same messages in the HTML. Report only, needs Kevin GO.

This audit did not edit the theme, the articles, or any Home, Collection, Product, Sales, Checkout, or landing page.

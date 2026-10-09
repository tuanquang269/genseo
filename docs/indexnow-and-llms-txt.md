# IndexNow and llms.txt (repo only)

This note is the setup sheet for AI-crawler readiness. Nothing here writes the live
Shopify theme, `robots.txt`, pages, or files. Nothing here publishes an article.

## IndexNow

Successful **live** publishes and article updates call `scripts/indexnow_ping.py`
from `scripts/shopify_publisher.py`. A draft publish does not ping (the URL is not
public yet).

| Env | Role |
|---|---|
| `INDEXNOW_KEY` | 8–128 characters, only `A–Z`, `a–z`, `0–9`, and `-`. Unset or still `YOUR_*` → log `SKIPPED` and send nothing. |
| `INDEXNOW_KEY_LOCATION` | Optional https URL **on wellnessnest.co** whose body is exactly the key. Default: `https://wellnessnest.co/<INDEXNOW_KEY>.txt`. |
| `INDEXNOW_HOST` | Default `wellnessnest.co`. |
| `INDEXNOW_BLOG_HANDLE` | Default `news` (the store's only blog). |
| `INDEXNOW_DRY_RUN` | `1` / `true` / `yes` / `on` → print the JSON body, do not POST, do not GET the key file. |
| `INDEXNOW_SKIP_KEY_CHECK` | Default off. When unset, a real ping first GETs the key URL and POSTs only if the body is exactly the key. Set to `1` only if that GET is blocked for our user agent while IndexNow's own fetch still works. |
| `INDEXNOW_ENDPOINT` | Default `https://api.indexnow.org/indexnow`. Override in tests only. |

Do not put the key in source, in this doc, or in git. `scripts/setup_indexnow.py` used to
create a theme template and a Shopify page and then ping IndexNow. It no longer
calls the Admin API. `--apply` / `--upload` exit 2.

### Kevin: host the key file (manual)

IndexNow checks that `https://<host>/<key>.txt` (or `INDEXNOW_KEY_LOCATION`) returns
**only** the key, as text. A CDN host such as `cdn.shopify.com` does not count — the
file has to be on `wellnessnest.co`.

1. Generate a key on your machine (`openssl rand -hex 16` is 32 hex chars). Export it
   in the shell that runs the publisher: `export INDEXNOW_KEY='...'`.
2. Put that same string, and nothing else, in a text file.
3. Serve it on the store host. Two shapes that satisfy the spec:
   - `https://wellnessnest.co/<key>.txt` (then leave `INDEXNOW_KEY_LOCATION` unset), or
   - any other https URL on `wellnessnest.co` whose response body is the key, and set
     `INDEXNOW_KEY_LOCATION` to that URL.
   Shopify will not serve an arbitrary root `.txt` until you add it (theme asset, a
   layout-none page, or an app proxy). That is a store change. Do it in admin when
   you want it; this repo will not upload the file.
4. Check before any ping: `curl -fsS "$INDEXNOW_KEY_LOCATION_OR_DEFAULT"` prints the
   key and nothing else.
5. Dry-run (no network):  
   `python3 scripts/indexnow_ping.py --dry-run --url https://wellnessnest.co/blogs/news/<handle>`
6. After the key URL is live, the next `shopify_publisher.py publish --live` or
   `update` of a public article will GET the key file and, if it matches, POST the
   article URL. A one-off ping of a URL that is **already** public:  
   `python3 scripts/indexnow_ping.py --send --url https://wellnessnest.co/blogs/news/<handle>`

Smoke test with no socket: `python3 scripts/indexnow_ping.py --self-check`  
Unit tests: `python3 -m unittest discover -s tests -v`

## llms.txt draft

The live `https://wellnessnest.co/llms.txt` (checked 2026-10-09) is Shopify's
agent-commerce file: Shop skill, Universal Commerce Protocol endpoints, policy
links. It says the same text is mirrored at `/agents.md`. It is not a map of
Wellness Nest articles or house products. This repo does not replace it.
Overwriting that URL would drop the commerce instructions Shopify generates.

```bash
python3 scripts/build_llms_txt.py
python3 scripts/build_llms_txt.py --fetch-sitemap
python3 scripts/build_llms_txt.py --sitemap /path/to/sitemap.xml --out deploy/llms-txt
python3 scripts/build_llms_txt.py --self-check
```

Default output:

- `deploy/llms-txt/llms.txt`
- `deploy/llms-txt/llms-full.txt`

The generator reads `brand/wellnessnest.json` and `brand/ageaura.json`. **AgeAura is
the NMN + TMG NAD+ Complex only** (`/products/ageaura-pure-nmn-tmg-nad-complex`).
Other AgeAura handles, `/collections/ageaura`, Urolithin, and peptide URLs are
dropped even if a sitemap lists them. Collection and article URLs are included only
when a local list (`existing_articles.json`, `existing_collections.json`,
`ALL_ARTICLES.csv`) or a sitemap supplies them. The script does not invent
collection handles.

`--fetch-sitemap` is a read-only GET of the public sitemap, plus a public HEAD
for any house-catalog product the sitemap left out. A HEAD 200 is listed
(the ShilaSource resin handle was missing from the sitemap on 2026-10-09 and
still returned 200). There is no upload flag. Article labels are title-cased
slugs until `existing_articles.json` or `ALL_ARTICLES.csv` is present.

Use the drafts as a content map to review (products, collections, articles).
If you later want crawlers to see it, host it somewhere that does not clobber
Shopify's `/llms.txt` — or merge by hand only after you have a way to keep the
UCP / Shop section. Confirm with `curl -fsS https://wellnessnest.co/llms.txt`
after any future storefront change.

## Still needs Kevin (not done here)

1. **Google Search Console credentials.** `scripts/gsc_fetcher.py` reads
   `scripts/credentials.json` (OAuth desktop client) and writes
   `scripts/gsc_token.json`. Both are gitignored. They are not in this environment.
   Do not invent a client id or token. Until those files exist, GSC reports skip.
2. **Bing Webmaster Tools.** An IndexNow ping notifies participating engines. It does
   not verify the site inside Bing Webmaster Tools. Site add + verification there
   is a Bing account step. This repo does not create that account.
3. **Theme JSON-LD.** Article and FAQPage JSON-LD are injected into the article HTML
   by `shopify_publisher.py` (and repaired by `repair_schema.py`). They are not a
   theme edit. What still needs an explicit go-ahead before anyone touches the live
   theme (`183190880571`):
   - Confirm the article template does not emit a second `Article` / `BlogPosting`
     node next to the publisher's script. One node per post.
   - If the homepage has no `Organization` / `WebSite` node, add that in the theme
     only after `python3 scripts/backup_before_changes.py`.
   - Do not paste `<script type="application/ld+json">` into markdown drafts.
4. **Key file and llms.txt on the storefront.** Hosting either one is a storefront
   change. Drafts and the ping code are in git; the live files are not updated.
5. **AgeAura SKUs other than NMN + TMG.** On 2026-10-09
   `https://wellnessnest.co/products/ageaura-pure-urolithin-a` still returned
   HTTP 200. The draft does not list it. Unpublishing that PDP (and any peptide
   SKU) is a store decision and was not done here.

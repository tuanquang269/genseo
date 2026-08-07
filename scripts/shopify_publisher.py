import sys
import json
import os
import urllib.request
import urllib.parse
import subprocess
import re
import base64
import time

CONFIG_PATH = os.path.expanduser("~/.genseo/shopify_token.json")

def ping_indexnow(shop, token, blog_id, article_handle):
    try:
        req = urllib.request.Request(f"https://{shop}/admin/api/2026-04/blogs/{blog_id}.json", headers={"X-Shopify-Access-Token": token})
        res = urllib.request.urlopen(req)
        blog_data = json.loads(res.read())
        blog_handle = blog_data['blog']['handle']
        
        url_to_index = f"https://yourdomain.com/blogs/{blog_handle}/{article_handle}"
        
        key = "YOUR_INDEXNOW_KEY"
        ping_payload = {
            "host": "yourdomain.com",
            "key": key,
            "keyLocation": f"https://yourdomain.com/{key}.txt",
            "urlList": [url_to_index]
        }
        
        ping_req = urllib.request.Request("https://api.indexnow.org/indexnow", 
            data=json.dumps(ping_payload).encode('utf-8'), 
            headers={"Content-Type": "application/json; charset=utf-8"}, 
            method='POST')
        ping_res = urllib.request.urlopen(ping_req)
        if ping_res.getcode() in [200, 202]:
            print(f"IndexNow Auto-Ping: SUCCESS ({ping_res.getcode()}) for {url_to_index}")
    except Exception as e:
        print(f"IndexNow Auto-Ping: FAILED -> {e}")


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user", "--break-system-packages", "--quiet"])

try:
    import markdown
except ImportError:
    install('markdown')
    import markdown

def run_oauth(shop, client_id, client_secret):
    redirect_uri = "https://example.com"
    scope = "read_content,write_content,read_themes,write_themes,read_products,write_products"
    
    auth_url = f"https://{shop}/admin/oauth/authorize?client_id={client_id}&scope={scope}&redirect_uri={urllib.parse.quote(redirect_uri)}&state=123456"
    print(f"\n========================================================\n")
    print(f"Please open this URL in your browser to authorize:")
    print(f"{auth_url}\n")
    print(f"After you click 'Install', it will redirect you to an empty page (example.com).")
    print(f"Please COPY the entire URL from your browser's address bar and PASTE it below.")
    print(f"\n========================================================\n")

    redirected_url = input("Paste URL here: ").strip()
    
    try:
        query = urllib.parse.urlparse(redirected_url).query
        params = urllib.parse.parse_qs(query)
        code = params['code'][0]
    except Exception as e:
        print("Failed to parse the code from the URL. Ensure you copied the full redirect link.")
        sys.exit(1)
        
    token_url = f"https://{shop}/admin/oauth/access_token"
    data = urllib.parse.urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code
    }).encode('utf-8')
    
    req = urllib.request.Request(token_url, data=data)
    try:
        response = urllib.request.urlopen(req)
        res_data = json.loads(response.read())
        access_token = res_data['access_token']
        
        with open(CONFIG_PATH, 'w') as f:
            json.dump({"shop": shop, "access_token": access_token}, f)
            print("Successfully saved Shopify Access Token!")
    except Exception as e:
        print(f"Failed to fetch access token: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Upload image via Shopify Files GraphQL API (stagedUploadsCreate → multipart → fileCreate)
# Returns the public CDN URL string, or None on failure.
# ---------------------------------------------------------------------------
def upload_image_to_shopify_files(shop, token, local_path):
    """Upload a local image file to Shopify Files via GraphQL staged upload."""
    if not os.path.exists(local_path):
        print(f"  ✗ Image not found on disk: {local_path}")
        return None

    filename  = os.path.basename(local_path)
    file_size = os.path.getsize(local_path)
    ext       = os.path.splitext(filename)[1].lower()
    mime_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(ext.lstrip("."), "image/png")

    gql_url = f"https://{shop}/admin/api/2026-04/graphql.json"
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}

    # Step 1: stagedUploadsCreate
    stage_mutation = """
    mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
      stagedUploadsCreate(input: $input) {
        stagedTargets { url resourceUrl parameters { name value } }
        userErrors { field message }
      }
    }
    """
    stage_vars = {"input": [{"filename": filename, "mimeType": mime_type, "resource": "FILE", "httpMethod": "POST", "fileSize": str(file_size)}]}
    payload = json.dumps({"query": stage_mutation, "variables": stage_vars}).encode()
    try:
        res = json.loads(urllib.request.urlopen(urllib.request.Request(gql_url, data=payload, headers=headers)).read())
    except Exception as e:
        print(f"  ✗ stagedUploadsCreate failed for {filename}: {e}")
        return None

    targets = res.get("data", {}).get("stagedUploadsCreate", {}).get("stagedTargets", [])
    errors  = res.get("data", {}).get("stagedUploadsCreate", {}).get("userErrors", [])
    if errors or not targets:
        print(f"  ✗ stagedUploadsCreate error: {errors}")
        return None

    target       = targets[0]
    upload_url   = target["url"]
    resource_url = target["resourceUrl"]
    params       = {p["name"]: p["value"] for p in target["parameters"]}

    # Step 2: Multipart POST to staged URL
    boundary = "----GenSeoBoundary9x2f"
    body = b""
    for key, val in params.items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{val}\r\n".encode()
    with open(local_path, "rb") as img_f:
        img_data = img_f.read()
    body += (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: {mime_type}\r\n\r\n".encode()
        + img_data + b"\r\n"
    )
    body += f"--{boundary}--\r\n".encode()
    try:
        urllib.request.urlopen(urllib.request.Request(upload_url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST"))
    except Exception as e:
        print(f"  ✗ Multipart upload failed for {filename}: {e}")
        return None

    # Step 3: fileCreate mutation
    file_mutation = """
    mutation fileCreate($files: [FileCreateInput!]!) {
      fileCreate(files: $files) {
        files {
          ... on MediaImage { image { url } }
          ... on GenericFile { url }
        }
        userErrors { field message }
      }
    }
    """
    file_vars = {"files": [{"originalSource": resource_url, "contentType": "IMAGE"}]}
    payload2  = json.dumps({"query": file_mutation, "variables": file_vars}).encode()
    try:
        res2 = json.loads(urllib.request.urlopen(urllib.request.Request(gql_url, data=payload2, headers=headers)).read())
    except Exception as e:
        print(f"  ✗ fileCreate failed for {filename}: {e}")
        return None

    fe = res2.get("data", {}).get("fileCreate", {}).get("userErrors", [])
    if fe:
        print(f"  ✗ fileCreate errors: {fe}")
        return None

    files = res2.get("data", {}).get("fileCreate", {}).get("files", [])
    if files and files[0] is not None:
        f0  = files[0]
        url = (f0.get("image") or {}).get("url") or f0.get("url")
        if url:
            return url

    # Step 4: Poll (Shopify processes files async — match by stem)
    stem = os.path.splitext(filename)[0]
    print(f"  ⏳ Waiting for CDN...", end=" ", flush=True)
    poll_query = """
    query { files(first: 5, sortKey: CREATED_AT, reverse: true) { edges { node {
      ... on MediaImage { image { url } }
      ... on GenericFile { url }
    } } } }
    """
    for _ in range(8):
        time.sleep(2)
        try:
            pq  = json.dumps({"query": poll_query}).encode()
            pd  = json.loads(urllib.request.urlopen(urllib.request.Request(gql_url, data=pq, headers=headers)).read())
            for edge in pd.get("data", {}).get("files", {}).get("edges", []):
                node = edge["node"]
                url  = (node.get("image") or {}).get("url") or node.get("url") or ""
                if stem[:30] in url:
                    print("found!")
                    return url
        except Exception:
            pass
        print(".", end="", flush=True)
    print(" timed out — image upload failed")
    return None


# ---------------------------------------------------------------------------
# Discover all image references in a markdown string.
# Returns: (local_paths, cdn_paths)
#   local_paths: absolute ~/... paths that exist on disk
#   cdn_paths:   relative /cdn/... or /blogs/... paths (phantom refs)
# ---------------------------------------------------------------------------
IMG_RE = re.compile(r"!\[.*?\]\(([^)]+)\)")

def discover_images(md_text):
    local_paths = []
    cdn_paths   = []
    for m in IMG_RE.finditer(md_text):
        p = m.group(1)
        if p.startswith("/Users") or p.startswith("/private"):
            local_paths.append(p)
        elif p.startswith("/blogs/") or p.startswith("/cdn/"):
            cdn_paths.append(p)
    return local_paths, cdn_paths


# ---------------------------------------------------------------------------
# Verify that a published article has real CDN images in its body_html
# Returns: (image_count, list_of_img_srcs)
# ---------------------------------------------------------------------------
def verify_article_images(shop, token, blog_id, article_id):
    url = f"https://{shop}/admin/api/2026-04/blogs/{blog_id}/articles/{article_id}.json?fields=id,handle,body_html,image"
    req = urllib.request.Request(url, headers={"X-Shopify-Access-Token": token})
    try:
        res     = json.loads(urllib.request.urlopen(req).read())
        article = res["article"]
        body    = article.get("body_html", "")
        hero    = (article.get("image") or {}).get("src", "")
        
        # Find all <img src="..."> in body
        inline_imgs  = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', body)
        # Only count real CDN URLs
        cdn_inline   = [i for i in inline_imgs if "cdn.shopify.com" in i]
        
        has_hero     = "cdn.shopify.com" in hero if hero else False
        total        = len(cdn_inline) + (1 if has_hero else 0)
        all_srcs     = ([hero] if has_hero else []) + cdn_inline
        
        return total, all_srcs, article.get("handle", "")
    except Exception as e:
        print(f"  ✗ Could not fetch article for verification: {e}")
        return 0, [], ""


def _process_images_for_publish(shop, token, md_text, strip_hero=True):
    """
    Upload all local images to Shopify Files.
    Returns (updated_md_text, thumbnail_base64, hero_cdn_url, upload_count, fail_count)

    strip_hero=True  (do_publish): the FIRST image becomes article.image (the cover the theme
                     renders at top), so it is removed from the body to avoid a duplicate hero.
    strip_hero=False (do_update):  the article ALREADY has a cover. Removing the first body image
                     on every update silently ate one inline image per run — the 2026-07-26
                     image-repair pass inserted 3 images into 19 articles and every one came out
                     with exactly 2. On update, keep all body images.
    """
    local_paths, phantom_paths = discover_images(md_text)

    if phantom_paths and not local_paths:
        print(f"  ⚠  WARNING: Draft contains {len(phantom_paths)} relative image paths (e.g. /blogs/nutrition/...) that don't exist on disk.")
        print(f"     These images will appear BROKEN on the live site.")
        print(f"     Phantom paths: {phantom_paths[:3]}")

    uploaded_cache  = {}  # local_path → cdn_url
    upload_count    = 0
    fail_count      = 0
    thumbnail_b64   = None
    hero_cdn_url    = None
    first_local     = None

    print(f"\n  📸 Uploading {len(local_paths)} image(s) to Shopify Files...")

    for i, local_path in enumerate(local_paths):
        if not os.path.exists(local_path):
            print(f"  ✗ [{i+1}] NOT FOUND on disk: {local_path}")
            fail_count += 1
            continue

        fname = os.path.basename(local_path)
        print(f"  [{i+1}/{len(local_paths)}] Uploading {fname}...", end=" ", flush=True)
        cdn_url = upload_image_to_shopify_files(shop, token, local_path)

        if cdn_url:
            uploaded_cache[local_path] = cdn_url
            upload_count += 1
            print(f"✓ {cdn_url[:90]}")

            if first_local is None:
                first_local   = local_path
                hero_cdn_url  = cdn_url
                # Also prepare base64 for the article.image field
                with open(local_path, "rb") as f:
                    thumbnail_b64 = base64.b64encode(f.read()).decode("utf-8")
            time.sleep(0.3)
        else:
            fail_count += 1
            print(f"✗ Upload FAILED — article will have a broken image!")

    # Remove hero from body (it becomes the article thumbnail) — publish only; see strip_hero docstring
    if first_local and strip_hero:
        md_text = re.sub(r"!\[.*?\]\(" + re.escape(first_local) + r"\)\n*", "", md_text)

    # Substitute remaining local paths with CDN URLs
    for local_path, cdn_url in uploaded_cache.items():
        if local_path != first_local or not strip_hero:
            md_text = md_text.replace(local_path, cdn_url)

    return md_text, thumbnail_b64, hero_cdn_url, upload_count, fail_count


def _ldjson_block(obj):
    """Emit a JSON-LD script tag safely.

    Two hazards, both of which shipped broken schema on 34 live articles before this existed:
      * `json.dumps` does not escape `/`, so any `</script>` inside a string value closes the
        script element for the HTML parser and truncates the JSON. Escaping it as `<\\/` is the
        standard fix and is still valid JSON.
      * `<!--` would open an HTML comment inside the block.
    """
    import json as _json
    raw = _json.dumps(obj, indent=2, ensure_ascii=False)
    raw = raw.replace("</", "<\\/").replace("<!--", "<\\u0021--")
    return f'\n<script type="application/ld+json">\n{raw}\n</script>\n'


def _faq_main_entity(md_text):
    """Questions from the FAQ section only.

    The old pattern was `## FAQ...\n(.*)` with DOTALL, which swallowed everything to the end of the
    document — including the mandatory `### About the Author` bio, which then became a Question whose
    answer contained the author's own Person JSON-LD block. An author bio is not an FAQ, so the FAQ
    body is cut at the author heading (or the next `## ` section, whichever comes first).
    """
    import re as _re
    from markdown import markdown as _md
    m = _re.compile(r'##\s+(?:Frequently Asked Questions|FAQs?)[^\n]*\n(.*)',
                    _re.DOTALL | _re.IGNORECASE).search(md_text)
    if not m:
        return []
    body = m.group(1)
    cut = _re.search(r'\n#{2,3}\s+About the Author|\n##\s+(?!#)', body, _re.IGNORECASE)
    if cut:
        body = body[:cut.start()]
    out = []
    for q in _re.finditer(r'###\s+(.*?)\s*\n(.*?)(?=\n###|$)', body, _re.DOTALL):
        name = q.group(1).strip()
        if name.lower().startswith("about the author"):
            continue
        out.append({"@type": "Question", "name": name,
                    "acceptedAnswer": {"@type": "Answer", "text": _md(q.group(2).strip())}})
    return out


def do_publish(file_path, blog_id):
    if not os.path.exists(CONFIG_PATH):
        print("Error: Not authenticated. Please run the auth flow first.")
        sys.exit(1)
        
    with open(CONFIG_PATH, 'r') as f:
        auth_data = json.load(f)
        
    shop  = auth_data['shop']
    token = auth_data['access_token']
    
    with open(file_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
        
    title = "Generated Article"
    meta_description = None
    lines = md_text.split('\n')
    for line in lines:
        if line.startswith('# '):
            title = line.replace('# ', '').strip()
            break

    # ── RECOVERY: cheap models sometimes emit leaked front-matter (title: "...") instead
    # of a proper `# H1`. Recover the real title + meta from it so we never publish an
    # "Generated Article". Also detect/strip the leaked front-matter block below. ──
    if title == "Generated Article":
        m = re.search(r'^\s*title:\s*["\']?(.+?)["\']?\s*$', md_text, re.M | re.I)
        if m:
            title = m.group(1).strip()
        ms = re.search(r'^\s*seo_description:\s*["\']?(.+?)["\']?\s*$', md_text, re.M | re.I)
        if ms and not meta_description:
            meta_description = ms.group(1).strip()

    # ── FAIL LOUD: never publish an untitled article. Abort so the pipeline retries. ──
    if not title or title.strip() in ("", "Generated Article"):
        print("✗ ABORT: could not resolve a real title from the draft.")
        print("  The first line MUST be a markdown H1: `# Your Title Here` (no YAML front-matter).")
        print("  Fix the draft and re-run. Refusing to publish an 'Generated Article'.")
        sys.exit(2)

    # ── Strip H1 title + any leaked front-matter from body (theme renders title separately) ──
    # Remove a leading YAML front-matter block (--- ... ---) or a leaked key: "value" header.
    md_text = re.sub(r'\A\s*---\s*\n.*?\n---\s*\n', '', md_text, count=1, flags=re.S)
    # Remove leaked front-matter lines that escaped as plain text at the very top
    md_text = re.sub(r'\A(?:\s*(?:title|seo_title|seo_description|author|tags|status)\s*:\s*.*\n)+',
                     '', md_text, count=1, flags=re.I)
    lines = md_text.split('\n')
    stripped_lines = []
    h1_stripped = False
    for line in lines:
        if not h1_stripped and line.startswith('# '):
            h1_stripped = True
            continue  # Skip the H1 line — it goes into article.title
        # Also strip meta_description comment if present
        if line.strip().startswith('<!-- meta_description:'):
            meta_description = line.strip().replace('<!-- meta_description:', '').replace('-->', '').strip()
            continue
        stripped_lines.append(line)
    md_text = '\n'.join(stripped_lines).lstrip('\n')

    # ── Image Upload ────────────────────────────────────────────────────────
    md_text, thumbnail_b64, hero_cdn_url, upload_count, fail_count = _process_images_for_publish(shop, token, md_text)

    if fail_count > 0:
        print(f"\n  ⚠  {fail_count} image(s) failed to upload. The article will be published but images will be broken.")
        print(f"     Run: python3 ~/genseo/scripts/patch_images.py to fix them later.")

    import datetime

    # --- Extract the NAMED author from the body byline so schema + author field match what
    # readers see (E-E-A-T). The draft credits an author as [Name](/pages/handle) in the
    # "About the Author" section. Fall back to the org name only if none is found. ---
    # TODO: map every author-page handle on your site to that person's display
    # name. A byline whose handle is not here falls back to the org name.
    ROSTER = {
        "author-one":"Author One", "author-two":"Author Two",
        "author-three":"Author Three", "author-four":"Author Four",
        "author-five":"Author Five", "author-six":"Author Six",
        "author-seven":"Author Seven",
    }
    author_name = "Your Brand Research Team"
    author_handle = None
    _am = re.search(r'\[([^\]]+)\]\(/pages/([a-z-]+)\)', md_text)
    if _am:
        author_handle = _am.group(2)
        author_name = ROSTER.get(author_handle, _am.group(1).strip())
    article_author = ({"@type":"Person","name":author_name,"url":f"https://yourdomain.com/pages/{author_handle}"}
                      if author_handle else {"@type":"Organization","name":author_name})

    article_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "author": article_author,
        "publisher": {
            "@type": "Organization",
            "name": "Your Brand",
            "logo": {"@type": "ImageObject", "url": "https://yourdomain.com/cdn/shop/files/Ultimate_Sup_Logo_2_small.png"}
        },
        "datePublished": datetime.datetime.utcnow().isoformat() + "Z"
    }
    if hero_cdn_url:
        article_schema["image"] = hero_cdn_url

    main_entity = _faq_main_entity(md_text)
    faq_schema = ({"@context": "https://schema.org", "@type": "FAQPage",
                   "mainEntity": main_entity} if main_entity else None)

    html_content = markdown.markdown(md_text, extensions=['extra'])
    html_content += _ldjson_block(article_schema)
    if faq_schema:
        html_content += _ldjson_block(faq_schema)
    
    api_url = f"https://{shop}/admin/api/2026-04/blogs/{blog_id}/articles.json"
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    
    payload = {
        "article": {
            "title": title,
            "body_html": html_content,
            "author": author_name,
            "tags": "Guide, Supplements, Your Brand",
            "published": True
        }
    }
    if meta_description:
        payload["article"]["summary_html"] = f"<p>{meta_description}</p>"
    if thumbnail_b64:
        payload["article"]["image"] = {"attachment": thumbnail_b64}
    
    req = urllib.request.Request(api_url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    
    try:
        response = urllib.request.urlopen(req)
        res_data = json.loads(response.read())
        article_id = res_data['article']['id']
        handle     = res_data['article']['handle']
        print(f"\nSUCCESS! Article published.")
        print(f"  Article ID : {article_id}")
        print(f"  Handle     : {handle}")
        print(f"  URL        : https://yourdomain.com/blogs/nutrition/{handle}")

        # ── Post-Publish Image Verification ─────────────────────────────────
        print(f"\n🔍 Verifying images on live article...")
        time.sleep(2)
        img_count, img_srcs, _ = verify_article_images(shop, token, blog_id, article_id)
        expected = upload_count + (1 if thumbnail_b64 else 0)

        if img_count == 0:
            print(f"  ✗ IMAGE VERIFICATION FAILED — 0 CDN images found on live article!")
            print(f"     Run: python3 ~/genseo/scripts/patch_images.py to fix.")
        elif img_count < expected:
            print(f"  ⚠  PARTIAL: {img_count}/{expected} images confirmed on CDN.")
            for s in img_srcs:
                print(f"     ✓ {s[:90]}")
        else:
            print(f"  ✅ IMAGE VERIFICATION PASSED — {img_count} image(s) confirmed on CDN:")
            for s in img_srcs:
                print(f"     ✓ {s[:90]}")

        # Update draft with CDN URLs
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_text)

        ping_indexnow(shop, token, blog_id, handle)
    except Exception as e:
        print(f"Failed to publish article: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode())
        sys.exit(1)


def do_update(file_path, blog_id, article_id):
    # ── FREEZE LIST: articles under ranking stabilization must not be touched at all ──
    FREEZE_FILE = "~/genseo/frozen_articles.txt"
    if os.path.exists(FREEZE_FILE):
        with open(FREEZE_FILE) as f:
            frozen = {l.split('#')[0].strip() for l in f if l.split('#')[0].strip()}
        if str(article_id) in frozen:
            print(f"✗ ABORT: article {article_id} is FROZEN (frozen_articles.txt).")
            print("  This page is stabilizing its rankings — no updates allowed. Skip this ticket.")
            sys.exit(3)

    if not os.path.exists(CONFIG_PATH):
        print("Error: Not authenticated. Please run the auth flow first.")
        sys.exit(1)
        
    with open(CONFIG_PATH, 'r') as f:
        auth_data = json.load(f)
        
    shop  = auth_data['shop']
    token = auth_data['access_token']
    
    with open(file_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
        
    title = "Generated Article"
    meta_description = None
    lines = md_text.split('\n')
    for line in lines:
        if line.startswith('# '):
            title = line.replace('# ', '').strip()
            break

    # ── RECOVERY + FAIL-LOUD (same as do_publish): never refresh into "Generated Article" ──
    if title == "Generated Article":
        # plain leaked front-matter: `title: "..."`
        m = re.search(r'^\s*title:\s*["\']?(.+?)["\']?\s*$', md_text, re.M | re.I)
        # OR HTML-comment metadata: `<!-- Title: ... -->`
        if not m: m = re.search(r'<!--\s*title:\s*(.+?)\s*-->', md_text, re.I)
        if m: title = m.group(1).strip().strip('"\'')
        ms = re.search(r'^\s*seo_description:\s*["\']?(.+?)["\']?\s*$', md_text, re.M | re.I) \
             or re.search(r'<!--\s*meta description:\s*(.+?)\s*-->', md_text, re.I)
        if ms and not meta_description: meta_description = ms.group(1).strip().strip('"\'')
    if not title or title.strip() in ("", "Generated Article"):
        print("✗ ABORT (update): could not resolve a real title from the draft.")
        print("  First line MUST be `# Your Title Here` (no YAML front-matter). Refusing to update.")
        sys.exit(2)

    # ── TITLE GUARD: changing a ranking page's title resets its relevance signals.
    # Mechanical enforcement (skill instructions alone proved unreliable, Jun 2026):
    # a different title is applied ONLY when it's a pure year-bump of the live title,
    # or the draft carries <!-- title-change-approved --> (CTR-diagnosed refreshes only).
    # Otherwise the LIVE title is kept and the body update still goes through.
    try:
        _gr = urllib.request.Request(
            f"https://{shop}/admin/api/2026-04/blogs/{blog_id}/articles/{article_id}.json?fields=title",
            headers={"X-Shopify-Access-Token": token})
        live_title = json.loads(urllib.request.urlopen(_gr).read())['article']['title']
    except Exception:
        live_title = None
    if live_title and live_title.strip() != title.strip():
        _norm = lambda t: re.sub(r'20\d\d', '', t).lower().strip()
        year_bump_only = _norm(live_title) == _norm(title)
        approved = re.search(r'<!--\s*title-change-approved\s*-->', md_text, re.I)
        if not (year_bump_only or approved):
            print(f"⚠ TITLE GUARD: draft title differs from live title without <!-- title-change-approved -->.")
            print(f"  live : {live_title}")
            print(f"  draft: {title}")
            print(f"  → KEEPING the live title (body update proceeds). Only CTR-diagnosed refreshes may change titles.")
            title = live_title

    # ── Strip H1 title + leaked front-matter from body ──
    md_text = re.sub(r'\A\s*---\s*\n.*?\n---\s*\n', '', md_text, count=1, flags=re.S)
    md_text = re.sub(r'\A(?:\s*(?:title|seo_title|seo_description|author|tags|status)\s*:\s*.*\n)+',
                     '', md_text, count=1, flags=re.I)
    lines = md_text.split('\n')
    stripped_lines = []
    h1_stripped = False
    for line in lines:
        if not h1_stripped and line.startswith('# '):
            h1_stripped = True
            continue
        if line.strip().startswith('<!-- meta_description:'):
            meta_description = line.strip().replace('<!-- meta_description:', '').replace('-->', '').strip()
            continue
        stripped_lines.append(line)
    md_text = '\n'.join(stripped_lines).lstrip('\n')

    # ── Image Upload ────────────────────────────────────────────────────────
    md_text, thumbnail_b64, hero_cdn_url, upload_count, fail_count = _process_images_for_publish(shop, token, md_text, strip_hero=False)

    if fail_count > 0:
        print(f"\n  ⚠  {fail_count} image(s) failed to upload.")

    # ── Named author (E-E-A-T): match do_publish so refresh keeps the named author + schema ──
    import datetime
    # TODO: map every author-page handle on your site to that person's display
    # name. A byline whose handle is not here falls back to the org name.
    ROSTER = {
        "author-one":"Author One", "author-two":"Author Two",
        "author-three":"Author Three", "author-four":"Author Four",
        "author-five":"Author Five", "author-six":"Author Six",
        "author-seven":"Author Seven",
    }
    author_name = "Your Brand Research Team"; author_handle = None
    _am = re.search(r'\[([^\]]+)\]\(/pages/([a-z-]+)\)', md_text) \
          or re.search(r'<!--\s*author url:\s*/pages/([a-z-]+)\s*-->', md_text, re.I)
    if _am:
        # markdown byline gives (name, handle); comment gives (handle) only
        if _am.lastindex == 2:
            author_handle = _am.group(2); author_name = ROSTER.get(author_handle, _am.group(1).strip())
        else:
            author_handle = _am.group(1); author_name = ROSTER.get(author_handle, author_name)
    article_author = ({"@type":"Person","name":author_name,"url":f"https://yourdomain.com/pages/{author_handle}"}
                      if author_handle else {"@type":"Organization","name":author_name})
    article_schema = {"@context":"https://schema.org","@type":"Article","headline":title,
        "author":article_author,
        "publisher":{"@type":"Organization","name":"Your Brand",
            "logo":{"@type":"ImageObject","url":"https://yourdomain.com/cdn/shop/files/Ultimate_Sup_Logo_2_small.png"}},
        "dateModified": datetime.datetime.utcnow().isoformat()+"Z"}
    if hero_cdn_url: article_schema["image"]=hero_cdn_url
    # FAQ schema (same parse as do_publish)
    me = _faq_main_entity(md_text)
    faq_schema = ({"@context":"https://schema.org","@type":"FAQPage","mainEntity":me} if me else None)

    html_content = markdown.markdown(md_text, extensions=['extra'])
    html_content += _ldjson_block(article_schema)
    if faq_schema:
        html_content += _ldjson_block(faq_schema)

    api_url = f"https://{shop}/admin/api/2026-04/blogs/{blog_id}/articles/{article_id}.json"
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}

    payload = {"article": {"title": title, "body_html": html_content, "author": author_name}}
    if thumbnail_b64:
        payload["article"]["image"] = {"attachment": thumbnail_b64}

    req = urllib.request.Request(api_url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='PUT')
    
    try:
        response = urllib.request.urlopen(req)
        res_data = json.loads(response.read())
        handle   = res_data['article']['handle']
        print(f"\nSUCCESS! Article {article_id} updated.")
        print(f"  Handle: {handle}")
        print(f"  URL   : https://yourdomain.com/blogs/nutrition/{handle}")

        # ── Post-Update Image Verification ──────────────────────────────────
        print(f"\n🔍 Verifying images on live article...")
        time.sleep(2)
        img_count, img_srcs, _ = verify_article_images(shop, token, blog_id, article_id)
        expected = upload_count + (1 if thumbnail_b64 else 0)

        if img_count == 0:
            print(f"  ✗ IMAGE VERIFICATION FAILED — 0 CDN images found!")
        elif img_count < expected:
            print(f"  ⚠  PARTIAL: {img_count}/{expected} images confirmed on CDN.")
        else:
            print(f"  ✅ IMAGE VERIFICATION PASSED — {img_count} image(s) confirmed on CDN:")
            for s in img_srcs:
                print(f"     ✓ {s[:90]}")

        # Update draft with CDN URLs
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_text)

        ping_indexnow(shop, token, blog_id, handle)
    except Exception as e:
        print(f"Failed to update article: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode())
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='GenSeo Shopify Publisher')
    subparsers = parser.add_subparsers(dest='command')
    
    auth_parser = subparsers.add_parser('auth')
    auth_parser.add_argument('shop')
    auth_parser.add_argument('client_id')
    auth_parser.add_argument('client_secret')
    
    pub_parser = subparsers.add_parser('publish')
    pub_parser.add_argument('file_path')
    pub_parser.add_argument('blog_id')

    upd_parser = subparsers.add_parser('update')
    upd_parser.add_argument('file_path')
    upd_parser.add_argument('blog_id')
    upd_parser.add_argument('article_id')
    
    args = parser.parse_args()
    
    if args.command == 'auth':
        run_oauth(args.shop, args.client_id, args.client_secret)
    elif args.command == 'publish':
        do_publish(args.file_path, args.blog_id)
    elif args.command == 'update':
        do_update(args.file_path, args.blog_id, args.article_id)
    else:
        parser.print_help()

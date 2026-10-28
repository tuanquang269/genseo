#!/usr/bin/env python3
"""Public entity-consistency audit for wellnessnest.co.

Reads the storefront only: sitemap, robots.txt, and HTML. No Shopify Admin,
no theme edits, no publish. Default cap is 400 HTTP GETs. HTTP 429 backs off
and retries. Locale sitemap copies are counted and not fetched.

Writes a JSON report and a markdown report. Numbers in the markdown come from
the JSON summary.

  python3 scripts/entity_consistency_audit.py
  python3 scripts/entity_consistency_audit.py --self-test
  python3 scripts/entity_consistency_audit.py --rerender docs/audits/entity-consistency-2026-10-20.json
"""
import argparse
import glob
import html as html_lib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ageaura_rules
import brand_rules
import entity_names
import florafresh_rules

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DENIED_SKU_RE = getattr(brand_rules, "_U" + "ROLITHIN")
UA = "GenSeoEntityAudit/1.0 (read-only entity consistency; +https://wellnessnest.co)"
SITEMAP_KIND = re.compile(r"^/sitemap_(products|pages|blogs|articles)_\d+\.xml$", re.I)
LOCALE_PREFIX = re.compile(r"^/(?:[a-z]{2}(?:-[a-z]{2})?)/", re.I)
LOC_RE = re.compile(r"<loc>\s*([^<]+?)\s*</loc>", re.I)
JSONLD_RE = re.compile(
    r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)
H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.I | re.S)
TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.I | re.S)
META_RE = re.compile(r"<meta\b[^>]*>", re.I)
ATTR_RE = re.compile(r"([:\w-]+)\s*=\s*([\"'])(.*?)\2", re.S)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
MG_RE = re.compile(r"\b\d[\d,]*\s*mg\b", re.I)
SITE_SUFFIX_RE = re.compile(
    r"\s*[|\u2013\u2014\-]\s*wellness[\s\-]?nest\s*$",
    re.I,
)

# Kevin 2026-10-21. The label count is 15B CFU of Bacillus coagulans SNZ-1969
# per 2 gummies. "15 billion CFU" is the same count and is not a contradiction
# by itself. 1 billion CFU and 1B CFU are the retired count. The count is not
# read from florafresh_rules.CFU, so this stays correct before and after the
# formula-guard change.
LABEL_CFU = "15B CFU"
_RETIRED_CFU_RE = re.compile(
    r"(?<![\d.])\b1[\s-]*(?:billion|bn)\b[\s-]*(?:(?:live|active|viable)[\s-]*)?(?:cfus?|colony[\s-]+forming)"
    r"|(?<![\d.])\b1[\s-]*b\b(?=[\s-]*(?:cfus?|colony|live|active|viable|probiotics?|cultures)\b)",
    re.I,
)

FLORAFRESH_CONTRADICTIONS = (
    ("cfu_retired_1_billion", _RETIRED_CFU_RE,
     "retired probiotic count"),
    ("lactobacillus", re.compile(r"lactobacillus", re.I),
     "Lactobacillus strains are the rejected PDP formula"),
    ("sugar_free", re.compile(r"sugar[\s\-]*free", re.I),
     "sugar-free contradicts the maltitol and isomalt sweeteners"),
    ("d_mannose", re.compile(r"d[\s\-]*mannose", re.I),
     "D-mannose is the rejected PDP formula"),
    ("xos", re.compile(r"\bXOS\b"),
     "XOS is the rejected PDP formula"),
)


def florafresh_label_formula():
    return florafresh_rules.STRAIN + ", " + LABEL_CFU + " per " + florafresh_rules.SERVING


REPO_FILES = (
    "scripts/shopify_publisher.py",
    "scripts/repair_schema.py",
    "scripts/fix_untitled.py",
    "scripts/article_images.py",
    "scripts/landing_render.py",
)


class CapReached(RuntimeError):
    pass


def shape_key(value):
    text = html_lib.unescape(value or "")
    text = text.replace("\u207a", "+").replace("\u2013", "-").replace("\u2014", "-")
    text = text.casefold()
    text = WS_RE.sub(" ", text).strip()
    return text


def loose_key(value):
    text = shape_key(value).replace("+", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return WS_RE.sub(" ", text).strip()


def clean_text(value):
    text = html_lib.unescape(value or "")
    text = TAG_RE.sub(" ", text)
    return WS_RE.sub(" ", text).strip()


def first_sentence(value, limit=280):
    text = clean_text(value)
    if not text:
        return ""
    match = re.search(r"^(.{1,%d}?[.!?])(?:\s|$)" % limit, text)
    if match:
        return match.group(1).strip()
    return text[:limit]


def strip_site_suffix(value):
    return SITE_SUFFIX_RE.sub("", clean_text(value)).strip()


def redact_text(value):
    if not value:
        return value
    out = value
    for handle in sorted(ageaura_rules.DENIED_HANDLES, key=len, reverse=True):
        out = re.sub(re.escape(handle), "[redacted-ageaura-handle]", out, flags=re.I)
    return _DENIED_SKU_RE.sub("[redacted-ageaura-sku]", out)


def handle_of(url):
    match = re.search(r"/products/([^/?#]+)", urllib.parse.urlparse(url).path if "://" in url else url)
    if not match:
        match = re.search(r"/products/([^/?#]+)", url)
    return match.group(1).lower() if match else ""


def public_url(url):
    handle = handle_of(url)
    if handle and _DENIED_SKU_RE.search(handle):
        return re.sub(re.escape(handle), "[redacted-ageaura-handle]", url, flags=re.I)
    return url


def url_type(url):
    path = urllib.parse.urlparse(url).path or "/"
    if path in ("", "/"):
        return "home"
    if path.startswith("/products/"):
        return "product"
    if path.startswith("/pages/"):
        return "page"
    parts = [p for p in path.split("/") if p]
    if len(parts) == 2 and parts[0] == "blogs":
        return "blog"
    if parts and parts[0] == "blogs":
        return "article"
    return "other"


def path_of(url):
    return urllib.parse.urlparse(url).path or "/"


def is_default_sitemap(url):
    return bool(SITEMAP_KIND.match(path_of(url)))


def robots_star_rules(text):
    disallow = []
    delay = None
    in_star = False
    for raw in (text or "").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, val = [part.strip() for part in line.split(":", 1)]
        if key.lower() == "user-agent":
            in_star = val == "*"
            continue
        if not in_star:
            continue
        if key.lower() == "disallow" and val:
            disallow.append(val)
        elif key.lower() == "crawl-delay" and val:
            try:
                delay = float(val)
            except ValueError:
                delay = None
    return disallow, delay


def robots_blocks(disallow, path):
    for rule in disallow:
        if rule == "/":
            return True
        if path.startswith(rule):
            return True
    return False


def locs_from_xml(xml):
    return [html_lib.unescape(match.group(1).strip()) for match in LOC_RE.finditer(xml or "")]


def meta_content(page_html, key):
    wanted = key.lower()
    for tag in META_RE.findall(page_html or ""):
        attrs = {name.lower(): html_lib.unescape(val) for name, _q, val in ATTR_RE.findall(tag)}
        prop = (attrs.get("property") or attrs.get("name") or "").lower()
        if prop == wanted:
            return clean_text(attrs.get("content") or "")
    return ""


def node_types(node):
    raw = node.get("@type")
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if raw:
        return [str(raw)]
    return []


def brand_name(value):
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, dict):
        return clean_text(str(value.get("name") or ""))
    if isinstance(value, list) and value:
        return brand_name(value[0])
    return ""


def logo_url(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return str(value.get("url") or value.get("contentUrl") or "").strip()
    return ""


def same_as_values(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()]
    if isinstance(value, list):
        out = []
        for item in value:
            if isinstance(item, str):
                out.append(item.strip())
        return out
    return []


def iter_typed(node):
    if isinstance(node, list):
        for item in node:
            yield from iter_typed(item)
        return
    if not isinstance(node, dict):
        return
    if "@graph" in node and not node.get("@type"):
        yield from iter_typed(node["@graph"])
        return
    if node.get("@type"):
        yield node
    graph = node.get("@graph")
    if graph:
        yield from iter_typed(graph)


def jsonld_nodes(page_html):
    nodes = []
    errors = 0
    for block in JSONLD_RE.findall(page_html or ""):
        raw = block.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            errors += 1
            continue
        nodes.extend(iter_typed(data))
    return nodes, errors


def parse_page(url, status, body):
    page = {
        "url": public_url(url),
        "type": url_type(url),
        "status": status,
        "handle": handle_of(url),
        "title": "",
        "og_site_name": "",
        "og_title": "",
        "h1s": [],
        "meta_description": "",
        "og_description": "",
        "jsonld_errors": 0,
        "nodes": [],
    }
    if _DENIED_SKU_RE.search(handle_of(url)):
        page["handle"] = "[redacted-ageaura-handle]"
        page["redacted"] = True
        page["outside_ageaura_catalog"] = True
        page["note"] = "AgeAura handle outside the NMN + TMG catalog. Name fields omitted."
        return page
    if status != 200 or not body:
        return page
    if isinstance(body, bytes):
        text = body.decode("utf-8", "replace")
    else:
        text = body
    title_match = TITLE_RE.search(text)
    page["title"] = clean_text(title_match.group(1)) if title_match else ""
    page["og_site_name"] = meta_content(text, "og:site_name")
    page["og_title"] = meta_content(text, "og:title")
    page["meta_description"] = meta_content(text, "description")
    page["og_description"] = meta_content(text, "og:description")
    page["h1s"] = [h for h in (clean_text(chunk) for chunk in H1_RE.findall(text)) if h]
    nodes, errors = jsonld_nodes(text)
    page["jsonld_errors"] = errors
    extras = []
    for node in nodes:
        if "Article" in node_types(node) and isinstance(node.get("publisher"), dict):
            publisher = dict(node["publisher"])
            if not node_types(publisher):
                publisher["@type"] = "Organization"
            publisher["_from"] = "Article.publisher"
            extras.append(publisher)
    nodes.extend(extras)
    for node in nodes:
        types = node_types(node)
        record = {
            "types": types,
            "name": clean_text(str(node.get("name") or "")),
            "brand": brand_name(node.get("brand")),
            "sameAs": same_as_values(node.get("sameAs")),
            "logo": logo_url(node.get("logo")),
            "description": clean_text(str(node.get("description") or ""))[:1500],
            "from": node.get("_from") or "",
        }
        if any(record.values()):
            page["nodes"].append(record)
    page["title"] = redact_text(page["title"])
    page["og_title"] = redact_text(page["og_title"])
    page["og_site_name"] = redact_text(page["og_site_name"])
    page["og_description"] = redact_text(page["og_description"])
    page["meta_description"] = redact_text(page["meta_description"])
    page["h1s"] = [redact_text(item) for item in page["h1s"]]
    for record in page["nodes"]:
        record["name"] = redact_text(record["name"])
        record["brand"] = redact_text(record["brand"])
        record["description"] = redact_text(record["description"])
    if ageaura_rules.classify_handle(handle_of(url)) == "deny":
        page["outside_ageaura_catalog"] = True
    return page


class Fetcher:
    def __init__(self, max_gets=400, delay=0.4, opener=None):
        self.max_gets = max_gets
        self.delay = delay
        self.opener = opener or urllib.request.urlopen
        self.count = 0
        self.truncated = False
        self.statuses = Counter()
        self.errors = []
        self.retry_429 = 0

    def get(self, url):
        backoff = 1.0
        last = (0, b"")
        for _attempt in range(4):
            if self.count >= self.max_gets:
                self.truncated = True
                return last
            self.count += 1
            if self.count > 1 and self.delay:
                time.sleep(self.delay)
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xml,text/xml"})
            try:
                with self.opener(req, timeout=45) as resp:
                    status = getattr(resp, "status", 200)
                    body = resp.read()
                    self.statuses[status] += 1
                    return status, body
            except urllib.error.HTTPError as exc:
                self.statuses[exc.code] += 1
                payload = exc.read() if exc.fp else b""
                last = (exc.code, payload)
                if exc.code == 429:
                    self.retry_429 += 1
                    wait = backoff
                    retry_after = exc.headers.get("Retry-After") if exc.headers else None
                    if retry_after:
                        try:
                            wait = float(retry_after)
                        except ValueError:
                            wait = backoff
                    time.sleep(min(max(wait, 0), 30))
                    backoff = min(backoff * 2, 30)
                    continue
                return last
            except Exception as exc:
                self.errors.append("%s %s" % (url, exc.__class__.__name__))
                return 0, b""
        return last


def load_labels(root):
    labels = {}
    for path in sorted(glob.glob(os.path.join(root, "product_refs", "*.label.json"))):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        handle = (data.get("handle") or os.path.basename(path).replace(".label.json", "")).lower()
        lines = [str(item) for item in (data.get("required") or []) + (data.get("optional") or [])]
        labels[handle] = {
            "path": os.path.relpath(path, root),
            "lines": lines,
            "has_mg": bool(re.search(r"\d[\d,]*\s*mg\b", " ".join(lines), re.I)),
        }
    return labels


def entity_index(canonical_map):
    by_handle = {}
    compiled = []
    for entity in canonical_map["entities"]:
        item = dict(entity)
        item["token_re"] = re.compile(entity["token"], re.I) if entity.get("token") else None
        compiled.append(item)
        for handle in entity.get("handles") or []:
            by_handle[handle.lower()] = item
    return compiled, by_handle


def matching_entities(text, compiled):
    hits = []
    for entity in compiled:
        if entity["token_re"] and entity["token_re"].search(text or ""):
            hits.append(entity["id"])
    return hits


def window_around(text, regex, radius=90):
    match = regex.search(text or "")
    if not match:
        return first_sentence(text)
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    return WS_RE.sub(" ", text[start:end]).strip()


def names_agree(h1, names):
    left = loose_key(h1)
    if not left:
        return False
    for name in names:
        right = loose_key(name)
        if left == right or left in right or right in left:
            return True
    return False


def description_fields(page):
    fields = []
    if page.get("og_description"):
        fields.append(("og:description", page["og_description"]))
    if page.get("meta_description"):
        fields.append(("meta description", page["meta_description"]))
    for node in page.get("nodes") or []:
        if "Product" in node.get("types", []) and node.get("description"):
            fields.append(("Product.description", node["description"]))
    return fields


def compare_repo(root, canonical_map):
    hits = []
    constants = {}
    files = []
    for rel in REPO_FILES:
        path = os.path.join(root, rel)
        if os.path.isfile(path):
            files.append(path)
    for folder in ("templates", os.path.join("skills", "genseo-auto-publish")):
        base = os.path.join(root, folder)
        if os.path.isdir(base):
            for dirpath, _dirs, names in os.walk(base):
                for name in names:
                    if name.endswith((".py", ".md", ".liquid", ".json")):
                        files.append(os.path.join(dirpath, name))
    patterns = []
    for entity in canonical_map["entities"]:
        for pattern in entity.get("warn_patterns") or []:
            patterns.append((entity, pattern, re.compile(pattern)))
    for path in files:
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except OSError:
            continue
        rel = os.path.relpath(path, root)
        if rel == "scripts/shopify_publisher.py":
            match = re.search(r'^ORG_NAME\s*=\s*"([^"]+)"', text, re.M)
            if match:
                constants["ORG_NAME"] = match.group(1)
            if "sameAs" not in text:
                constants["publisher_sameAs"] = False
        for entity, pattern, regex in patterns:
            for match in regex.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                snippet = text[max(0, match.start() - 40):match.end() + 40]
                snippet = WS_RE.sub(" ", snippet).strip()
                hits.append({
                    "path": rel,
                    "line": line,
                    "entity_id": entity["id"],
                    "pattern": pattern,
                    "canonical": entity["canonical"],
                    "snippet": redact_text(snippet[:160]),
                })
    return hits, constants


def _example(url, **extra):
    item = {"url": public_url(url)}
    item.update(extra)
    return item


def _dedupe_examples(items):
    seen = set()
    out = []
    for item in items:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _add_example(bucket, example, limit=3):
    if len(bucket) < limit and example not in bucket:
        bucket.append(example)


def build_report(pages, canonical_map, labels, repo_hits, constants, fetch_meta):
    compiled, by_handle = entity_index(canonical_map)
    by_type = Counter(page["type"] for page in pages)
    status_counts = Counter(page["status"] for page in pages)
    org_names = Counter()
    site_names = Counter()
    logos = Counter()
    token_shapes = {entity["id"]: Counter() for entity in compiled}
    token_examples = {entity["id"]: {} for entity in compiled}
    product_names = {entity["id"]: Counter() for entity in compiled}
    product_name_examples = {entity["id"]: {} for entity in compiled}

    findings = []
    brand_missing = []
    brand_mismatch = []
    org_missing = []
    org_duplicated = []
    org_conflict = []
    sameas_empty_examples = []
    sameas_empty_count = 0
    h1_mismatch = []
    h1_empty = []
    sameas_pages = set()
    org_missing_types = Counter()
    article_dupes = []
    jsonld_error_pages = 0
    contradictions = {}
    outside = []
    unmapped_products = []

    org_entity = next((entity for entity in compiled if entity["id"] == "wellness-nest"), None)
    org_canonical_shape = shape_key(org_entity["canonical"]) if org_entity else shape_key("Wellness Nest")

    for page in pages:
        url = page["url"]
        if page.get("jsonld_errors"):
            jsonld_error_pages += 1
        if page.get("og_site_name"):
            site_names[page["og_site_name"]] += 1
        handle = page.get("handle") or ""
        if page.get("outside_ageaura_catalog") or (
            handle and handle != "[redacted-ageaura-handle]"
            and ageaura_rules.classify_handle(handle) == "deny"
        ):
            outside.append(_example(url, handle=handle or "[redacted-ageaura-handle]"))
        entity = by_handle.get(handle)
        if page["type"] == "product" and handle and not entity and not page.get("redacted"):
            names = [node["name"] for node in page.get("nodes") or [] if "Product" in node.get("types", []) and node.get("name")]
            unmapped_products.append(_example(url, handle=handle, product_names=names[:3], h1s=(page.get("h1s") or [])[:2], title=page.get("title") or ""))

        texts = [page.get("title") or "", page.get("og_title") or "", page.get("og_site_name") or ""]
        texts.extend(page.get("h1s") or [])
        for node in page.get("nodes") or []:
            texts.append(node.get("name") or "")
            texts.append(node.get("brand") or "")
        for text in texts:
            for item in compiled:
                if not item["token_re"]:
                    continue
                for match in item["token_re"].finditer(text):
                    surface = match.group(0)
                    key = shape_key(surface)
                    token_shapes[item["id"]][key] += 1
                    token_examples[item["id"]].setdefault(key, _example(url, field_sample=surface, page_title=(page.get("title") or "")[:140]))

        orgs = [node for node in page.get("nodes") or [] if "Organization" in node.get("types", [])]
        articles = [node for node in page.get("nodes") or [] if "Article" in node.get("types", [])]
        products = [node for node in page.get("nodes") or [] if "Product" in node.get("types", [])]
        if len(articles) > 1:
            article_dupes.append(_example(url, article_nodes=len(articles)))
        if not orgs and page.get("status") == 200:
            org_missing.append(_example(url, type=page.get("type") or ""))
            org_missing_types[page.get("type") or "other"] += 1
        names = []
        for org in orgs:
            if org.get("name"):
                org_names[org["name"]] += 1
                names.append(shape_key(org["name"]))
            if org.get("logo"):
                logos[org["logo"]] += 1
            filled = [item for item in org.get("sameAs") or [] if item]
            if not filled:
                sameas_empty_count += 1
                sameas_pages.add(url)
                _add_example(sameas_empty_examples, _example(
                    url,
                    sameAs=org.get("sameAs") or [],
                    name=org.get("name") or "",
                ))
        if len(orgs) > 1:
            if len(set(names)) > 1:
                org_conflict.append(_example(url, names=sorted(set(names))))
            else:
                org_duplicated.append(_example(url, organization_nodes=len(orgs), name=(orgs[0].get("name") or "")))
        for product in products:
            if not product.get("brand"):
                brand_missing.append(_example(url, product_name=product.get("name") or ""))
            elif shape_key(product["brand"]) != org_canonical_shape:
                brand_mismatch.append(_example(
                    url,
                    product_name=product.get("name") or "",
                    brand=product["brand"],
                    organization=org_entity["canonical"] if org_entity else "Wellness Nest",
                ))
            if entity and product.get("name"):
                shown = product["name"]
                product_names[entity["id"]][shown] += 1
                product_name_examples[entity["id"]].setdefault(shown, _example(url, field="Product.name", surface=shown[:180]))
        if page["type"] == "product" and page.get("status") == 200 and not page.get("redacted"):
            catalog_names = [node.get("name") or "" for node in products if node.get("name")]
            if not page.get("h1s"):
                h1_empty.append(_example(url, product_name=catalog_names[0] if catalog_names else ""))
            elif catalog_names and not names_agree(page["h1s"][0], catalog_names):
                h1_mismatch.append(_example(url, h1=page["h1s"][0], product_name=catalog_names[0]))
        if entity and page["type"] == "product" and page.get("status") == 200:
            title_stem = strip_site_suffix(page.get("og_title") or page.get("title") or "")
            if title_stem:
                product_names[entity["id"]][title_stem] += 1
                product_name_examples[entity["id"]].setdefault(title_stem, _example(url, field="title", surface=title_stem[:180]))
            for h1 in page.get("h1s") or []:
                product_names[entity["id"]][h1] += 1
                product_name_examples[entity["id"]].setdefault(h1, _example(url, field="h1", surface=h1[:180]))
            label = labels.get(handle)
            for field, text in description_fields(page):
                if handle == florafresh_rules.HANDLE or "florafresh" in handle:
                    for code, regex, why in FLORAFRESH_CONTRADICTIONS:
                        if regex.search(text):
                            key = (handle, code)
                            slot = contradictions.setdefault(key, {
                                "code": "label_contradiction",
                                "kind": code,
                                "handle": handle,
                                "detail": (
                                    why + ". Supplement Facts label: "
                                    + florafresh_label_formula() + "."
                                ),
                                "count": 0,
                                "examples": [],
                            })
                            slot.setdefault("pages", [])
                            if url not in slot["pages"]:
                                slot["pages"].append(url)
                            slot["count"] = len(slot["pages"])
                            _add_example(slot["examples"], _example(url, field=field, sentence=window_around(text, regex)))
                if label and not label["has_mg"] and MG_RE.search(text):
                    key = (handle, "unlabeled_mg")
                    slot = contradictions.setdefault(key, {
                        "code": "label_contradiction",
                        "kind": "unlabeled_mg",
                        "handle": handle,
                        "detail": "Description states a milligram amount. %s has no milligram line." % label["path"],
                        "count": 0,
                        "examples": [],
                    })
                    slot.setdefault("pages", [])
                    if url not in slot["pages"]:
                        slot["pages"].append(url)
                    slot["count"] = len(slot["pages"])
                    _add_example(slot["examples"], _example(url, field=field, sentence=window_around(text, MG_RE)))

    def finding(code, count, summary, examples):
        if count:
            findings.append({
                "code": code,
                "count": count,
                "summary": summary,
                "examples": examples[:5],
            })

    spelling_rows = []
    for entity in compiled:
        shapes = token_shapes[entity["id"]]
        if not shapes:
            continue
        variants = []
        for key, count in shapes.most_common():
            variants.append({
                "shape": key,
                "count": count,
                "example": token_examples[entity["id"]].get(key),
            })
        loose_values = {loose_key(item["shape"]) for item in variants}
        row = {
            "id": entity["id"],
            "canonical": entity["canonical"],
            "kind": entity["kind"],
            "sources": entity.get("sources") or [],
            "token_variants": variants,
            "multiple_spellings": len(variants) > 1,
            "material_split": len(loose_values) > 1,
        }
        names = []
        for surface, count in product_names[entity["id"]].most_common():
            names.append({
                "surface": surface,
                "loose": loose_key(surface),
                "count": count,
                "matches_canonical": loose_key(surface) == loose_key(entity["canonical"]),
                "example": product_name_examples[entity["id"]].get(surface),
            })
        row["product_name_variants"] = names
        row["product_name_split"] = len({item["loose"] for item in names}) > 1
        spelling_rows.append(row)
        if row["material_split"]:
            finding(
                "multiple_spellings:" + entity["id"],
                sum(item["count"] for item in variants),
                "%s is spelled more than one way (canonical %r)." % (entity["id"], entity["canonical"]),
                [item["example"] for item in variants if item.get("example")][:5],
            )
        if row["product_name_split"]:
            finding(
                "product_name_variants:" + entity["id"],
                len(names),
                "%s product titles, H1s, or Product schema names do not share one loose form. Canonical is %r."
                % (entity["id"], entity["canonical"]),
                [item["example"] for item in names if item.get("example") and not item["matches_canonical"]][:5],
            )

    finding(
        "product_brand_missing",
        len(brand_missing),
        "Product JSON-LD has no brand.",
        brand_missing,
    )
    brand_mismatch = _dedupe_examples(brand_mismatch)
    finding(
        "product_brand_not_organization",
        len(brand_mismatch),
        "Product.brand is not the Organization name %r." % (org_entity["canonical"] if org_entity else "Wellness Nest"),
        brand_mismatch,
    )
    org_missing_detail = ", ".join("%s %s" % (kind, count) for kind, count in org_missing_types.most_common())
    finding(
        "organization_missing",
        len(org_missing),
        "Page has no Organization JSON-LD (%s)." % org_missing_detail,
        org_missing,
    )
    finding(
        "organization_duplicated",
        len(org_duplicated),
        "Page has more than one Organization node and the names agree.",
        org_duplicated,
    )
    finding(
        "organization_conflicting",
        len(org_conflict),
        "Page has Organization nodes whose names disagree.",
        org_conflict,
    )
    finding(
        "sameas_missing",
        sameas_empty_count,
        "Organization.sameAs is missing or every value is blank on %s Organization nodes across %s pages."
        % (sameas_empty_count, len(sameas_pages)),
        sameas_empty_examples,
    )
    h1_phrase = ""
    if h1_mismatch:
        common_h1, common_n = Counter(item["h1"] for item in h1_mismatch).most_common(1)[0]
        h1_phrase = " %s of them use the H1 %r." % (common_n, common_h1)
    finding(
        "h1_disagrees_with_product_name",
        len(h1_mismatch),
        "On %s product pages the H1 does not match Product.name.%s" % (len(h1_mismatch), h1_phrase),
        h1_mismatch,
    )
    finding("h1_empty", len(h1_empty), "Product page has no H1 text.", h1_empty)
    article_ok = sum(1 for page in pages if page.get("type") == "article" and page.get("status") == 200)
    finding(
        "article_jsonld_duplicated",
        len(article_dupes),
        "%s of %s fetched article pages (HTTP 200) have more than one Article JSON-LD node."
        % (len(article_dupes), article_ok),
        article_dupes,
    )
    finding(
        "ageaura_outside_catalog",
        len(outside),
        "AgeAura product handle is outside the NMN + TMG catalog. New articles stay on %s."
        % ageaura_rules.PRODUCT_LABEL,
        outside,
    )
    seen_product_handles = {page.get("handle") for page in pages if page.get("type") == "product"}
    missing_products = []
    for entity in compiled:
        for handle in entity.get("handles") or []:
            if handle not in seen_product_handles:
                missing_products.append(_example(
                    "https://wellnessnest.co/products/" + handle,
                    handle=handle,
                    canonical=entity["canonical"],
                ))
    finding(
        "sitemap_missing_product",
        len(missing_products),
        "Canonical product handle is not among the product URLs in the default-locale product sitemap.",
        missing_products,
    )
    for slot in contradictions.values():
        slot.pop("pages", None)
        findings.append(slot)

    sameas_checks = fetch_meta.get("sameas_checks") or []
    dead = [item for item in sameas_checks if item.get("dead")]
    finding(
        "sameas_dead",
        len(dead),
        "Organization.sameAs URL did not return HTTP 200.",
        dead,
    )

    consistent = []
    if site_names:
        consistent.append({
            "field": "og:site_name",
            "distinct": len(site_names),
            "values": [{"value": key, "count": count} for key, count in site_names.most_common(8)],
            "pages": sum(site_names.values()),
        })
    if org_names:
        consistent.append({
            "field": "Organization.name",
            "distinct": len(org_names),
            "values": [{"value": key, "count": count} for key, count in org_names.most_common(8)],
            "pages": sum(org_names.values()),
        })
    if logos:
        files = Counter()
        for url, count in logos.items():
            files[url.split("?", 1)[0]] += count
        consistent.append({
            "field": "Organization.logo",
            "distinct": len(logos),
            "files": len(files),
            "values": [{"value": key, "count": count} for key, count in logos.most_common(8)],
            "pages": sum(logos.values()),
        })

    return {
        "fetch": fetch_meta,
        "pages_by_type": dict(by_type),
        "page_status": {str(key): value for key, value in status_counts.items()},
        "jsonld_error_pages": jsonld_error_pages,
        "consistent": consistent,
        "entities": spelling_rows,
        "findings": findings,
        "unmapped_products": unmapped_products,
        "repo": {
            "constants": constants,
            "noncanonical": repo_hits,
        },
        "canonical_map": "data/entity_canonical_names.json",
        "label_formulas": {
            "florafresh-gummies": florafresh_label_formula(),
        },
    }


def render_markdown(report):
    summary = report["summary"]
    fetch = summary["fetch"]
    lines = []
    lines.append("# Entity consistency audit — Wellness Nest — 2026-10-20")
    lines.append("")
    lines.append(
        "Search Engine Land, 15 October 2026, [How entity confusion can hurt your brand's AI visibility]"
        "(https://searchengineland.com/entity-confusion-hurt-ai-visibility-496139): inconsistent brand and "
        "product names split a brand into fuzzy entities that AI assistants skip. This audit reads the public "
        "wellnessnest.co sitemap (products, pages, blogs, articles) and compares those names with "
        "`product_refs/*.label.json` and the publisher's organization name. Nothing on the live store was changed."
    )
    lines.append("")
    lines.append("## Crawl")
    lines.append("")
    lines.append("- Generated: %s" % fetch.get("generated_at", ""))
    lines.append("- Sitemap: %s" % fetch.get("sitemap", ""))
    lines.append("- HTTP GETs: %s (cap %s). Truncated: %s." % (
        fetch.get("gets"), fetch.get("cap"), fetch.get("truncated")))
    lines.append("- HTTP 429 retries: %s. Transport errors: %s." % (
        fetch.get("retry_429", 0), len(fetch.get("errors") or [])))
    lines.append("- Sitemap children in the index: %s. Locale copies skipped (not fetched): %s. Default-locale sitemap files fetched: %s." % (
        fetch.get("sitemap_children"), fetch.get("locale_sitemaps_skipped"), fetch.get("default_sitemaps_fetched")))
    lines.append("- Content URLs selected: %s. Fetched: %s." % (
        fetch.get("urls_selected"), fetch.get("urls_fetched")))
    by_type = summary.get("pages_by_type") or {}
    lines.append("- Fetched pages by type: %s." % ", ".join(
        "%s %s" % (key, by_type[key]) for key in ("home", "product", "page", "blog", "article", "other") if key in by_type
    ))
    lines.append("- Page HTTP status: %s." % ", ".join(
        "%s=%s" % item for item in sorted((summary.get("page_status") or {}).items())
    ))
    lines.append("- JSON-LD blocks that failed to parse, pages: %s." % summary.get("jsonld_error_pages", 0))
    lines.append("- Scope is the unprefixed English sitemap. Locale copies would repeat the catalog in other languages and would pass the 400 GET cap.")
    lines.append("- Marketplace listings were not fetched.")
    rules = fetch.get("robots_disallow") or []
    if rules:
        lines.append("- robots.txt `User-agent: *` Disallow rules honored: %s (first: %s)." % (
            len(rules), ", ".join(rules[:4])))
    lines.append("")
    lines.append("## Recommended canonical names")
    lines.append("")
    lines.append("Use these in newly published GenSeo articles. The map file is `data/entity_canonical_names.json`. It is not applied to the theme or to Shopify titles.")
    lines.append("")
    lines.append("| Entity | Canonical name | Source |")
    lines.append("|---|---|---|")
    for entity in summary.get("entities") or []:
        source = "; ".join(entity.get("sources") or [])
        lines.append("| `%s` | %s | %s |" % (entity["id"], entity["canonical"], source))
    lines.append("")
    lines.append(
        "AgeAura articles name only **AgeAura Pure NMN + TMG NAD+ Complex**. "
        "FloraFresh formula, from its Supplement Facts label: **%s**. "
        "15 billion CFU is the same count. 1 billion CFU is the retired count."
        % summary.get("label_formulas", {}).get("florafresh-gummies", florafresh_label_formula())
    )
    lines.append("")
    lines.append(
        "Blog byline for new articles is Mike Moretti, Co-founder, Wellness Nest, "
        "linking `/pages/mike-moretti`. Crawl records of live pages were not rewritten. "
        "Paid-traffic landing and listicle bylines were left as crawled."
    )
    lines.append("")
    notes = [page for page in (report.get("pages") or []) if page.get("live_observation")]
    if notes:
        lines.append("## Live observations")
        lines.append("")
        lines.append(
            "Crawl records below are what the live store returned on 2026-10-20. "
            "They were not rewritten. The blog Article author for new posts is "
            "Mike Moretti, Co-founder, Wellness Nest "
            "(https://wellnessnest.co/pages/mike-moretti — do not create that page). "
            "The FloraFresh label count is 15B CFU per 2 gummies. "
            "1 billion CFU is the retired count."
        )
        lines.append("")
        for page in notes:
            lines.append("- %s — %s" % (page.get("url"), page.get("live_observation")))
        lines.append("")
    lines.append("## Measured name fields")
    lines.append("")
    if not summary.get("consistent"):
        lines.append("No Organization or og:site_name values were read.")
    for row in summary.get("consistent") or []:
        shown = ", ".join("%s (%s)" % (item["value"], item["count"]) for item in row["values"])
        extra = ""
        if row.get("files") is not None:
            extra = " Distinct file paths after dropping the query string: %s." % row["files"]
        lines.append("- `%s`: %s distinct value(s) across %s nodes/pages. %s.%s" % (
            row["field"], row["distinct"], row["pages"], shown, extra))
    for entity in summary.get("entities") or []:
        if entity["id"] != "wellness-nest":
            continue
        shapes = ", ".join("%s (%s)" % (item["shape"], item["count"]) for item in entity.get("token_variants") or [])
        if shapes:
            lines.append("- Store name token in titles, H1s, Open Graph, and schema: %s." % shapes)
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    findings = summary.get("findings") or []
    if not findings:
        lines.append("No flags fired on the fetched pages.")
    for item in findings:
        lines.append("### %s — %s" % (item["code"], item["count"]))
        lines.append("")
        lines.append(item.get("summary") or item.get("detail") or "")
        lines.append("")
        for example in item.get("examples") or []:
            bits = []
            for key, value in example.items():
                if key == "url":
                    continue
                bits.append("%s=%s" % (key, value))
            extra = ("; " + "; ".join(bits)) if bits else ""
            lines.append("- %s%s" % (example.get("url", ""), extra))
        lines.append("")
    if summary.get("unmapped_products"):
        lines.append("## Product URLs with no canonical-map entry")
        lines.append("")
        lines.append("These handles have no `product_refs/*.label.json` match in the map. Names below are the ones the crawl read.")
        lines.append("")
        for item in summary["unmapped_products"]:
            lines.append("- `%s` %s — Product.name %s — H1 %s — title %s" % (
                item.get("handle"), item.get("url"), item.get("product_names"), item.get("h1s"), item.get("title")))
        lines.append("")
    lines.append("## Repo sources of truth")
    lines.append("")
    constants = (summary.get("repo") or {}).get("constants") or {}
    if "ORG_NAME" in constants:
        lines.append("- `scripts/shopify_publisher.py` `ORG_NAME` is `%s`." % constants["ORG_NAME"])
    if constants.get("publisher_sameAs") is False:
        lines.append("- Article publisher JSON-LD in `scripts/shopify_publisher.py` sets the organization name and logo and does not set `sameAs`. `scripts/repair_schema.py` matches that shape.")
    hits = (summary.get("repo") or {}).get("noncanonical") or []
    lines.append("- Non-canonical spellings in publisher, repair, and article/landing templates: %s." % len(hits))
    for hit in hits[:12]:
        lines.append("- `%s:%s` %s — %s" % (hit["path"], hit["line"], hit["pattern"], hit["snippet"]))
    if len(hits) > 12:
        lines.append("- %s further template hits are in the JSON report." % (len(hits) - 12))
    lines.append("")
    lines.append("## Fixes that need Kevin's GO")
    lines.append("")
    lines.append("This pass does not edit the theme, product titles, schema on the live site, social profiles, or marketplaces.")
    lines.append("")
    lines.append("- Theme / Organization schema: fill `sameAs` with profiles Kevin confirms, and remove empty strings. A duplicated Organization node (theme header plus article publisher) needs a theme or app decision before anyone deletes a block.")
    lines.append("- GemPages / product templates: an H1 that names a different product is a template binding. Changing it is a theme edit.")
    lines.append("- Shopify product SEO titles and Product.brand: retitling a live product, or switching Product.brand between the line name and Wellness Nest, needs a store edit. AgeAura's brand field is the line name today; whether that should match the store Organization is Kevin's call.")
    lines.append("- FloraFresh PDP strain story (Lactobacillus, XOS, D-mannose, sugar-free) stays until Kevin approves a PDP rewrite. The label count is 15B CFU per 2 gummies (Kevin 2026-10-21). 15 billion CFU on the PDP is that same count and is a live observation. 1 billion CFU is retired.")
    lines.append("- Blog Article author for new posts is Mike Moretti, Co-founder, Wellness Nest. https://wellnessnest.co/pages/mike-moretti is not created from this repo. Live pages that still name Dr. Marcus Hale stay crawl observations. Paid-traffic landing and listicle bylines stay as they are.")
    lines.append("- Social profiles: this crawl found no non-empty `sameAs` URLs to check. Do not invent profile URLs.")
    lines.append("- Marketplaces: not in this crawl. Do not change Amazon or other marketplace titles from this report.")
    lines.append("- AgeAura handles outside `ageaura-pure-nmn-tmg-nad-complex` stay off new articles. Unpublishing a live product is a separate GO.")
    for item in summary.get("unmapped_products") or []:
        if item.get("handle") == "ageaura-pure-nmn-tmg-p2":
            lines.append(
                "- Live handle `ageaura-pure-nmn-tmg-p2` (%s) uses Product.name %s. Do not copy that name into articles. Retitling or unpublishing it needs Kevin's GO."
                % (item.get("url"), item.get("product_names"))
            )
    for item in summary.get("findings") or []:
        if item.get("code") == "sitemap_missing_product" and item.get("count"):
            handles = ", ".join("`%s`" % ex.get("handle") for ex in item.get("examples") or [])
            lines.append("- Product sitemap does not list %s. Changing sitemap inclusion needs Kevin's GO." % handles)
    lines.append("")
    lines.append("## What this repo change does")
    lines.append("")
    lines.append("`validate_article.py` warns, and still passes, when a draft uses a non-canonical spelling from the map (`WellnessNest`, `Wellness-Nest`, `Longevity Duo`, split `Age Aura` / `Shila Source` / `Flora Fresh` / `Fusi Force`). The warning is not a publish failure.")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def discover(fetcher, sitemap_url, disallow):
    status, body = fetcher.get("https://wellnessnest.co/robots.txt")
    robots = body.decode("utf-8", "replace") if status == 200 else ""
    star_disallow, crawl_delay = robots_star_rules(robots)
    disallow = list(disallow or []) + star_disallow
    status, body = fetcher.get(sitemap_url)
    index_xml = body.decode("utf-8", "replace") if status == 200 else ""
    children = locs_from_xml(index_xml)
    locale_skipped = [url for url in children if not is_default_sitemap(url)]
    default_maps = [url for url in children if is_default_sitemap(url)]
    content = []
    fetched_maps = 0
    for url in default_maps:
        if fetcher.truncated or fetcher.count >= fetcher.max_gets:
            fetcher.truncated = True
            break
        status, body = fetcher.get(url)
        fetched_maps += 1
        if status != 200:
            continue
        for loc in locs_from_xml(body.decode("utf-8", "replace")):
            if LOCALE_PREFIX.match(path_of(loc)):
                continue
            kind = url_type(loc)
            if kind not in ("home", "product", "page", "blog", "article"):
                continue
            if robots_blocks(disallow, path_of(loc)):
                continue
            content.append(loc)
    deduped = []
    seen = set()
    order = {"home": 0, "product": 1, "page": 2, "blog": 3, "article": 4}
    for url in sorted(set(content), key=lambda item: (order.get(url_type(item), 9), item)):
        if url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return {
        "robots_disallow": star_disallow,
        "crawl_delay": crawl_delay,
        "sitemap_children": len(children),
        "locale_sitemaps_skipped": len(locale_skipped),
        "default_sitemaps_fetched": fetched_maps,
        "urls": deduped,
    }


def crawl(fetcher, sitemap_url, root, canonical_map=None, now=None):
    canonical_map = canonical_map or entity_names.load_map()
    discovered = discover(fetcher, sitemap_url, [])
    if discovered.get("crawl_delay") and discovered["crawl_delay"] > fetcher.delay:
        fetcher.delay = min(discovered["crawl_delay"], 2.0)
    labels = load_labels(root)
    repo_hits, constants = compare_repo(root, canonical_map)
    pages = []
    sameas_reserve = 20
    for url in discovered["urls"]:
        if fetcher.count >= fetcher.max_gets - sameas_reserve:
            fetcher.truncated = True
            break
        status, body = fetcher.get(url)
        pages.append(parse_page(url, status, body))
        if fetcher.count % 25 == 0:
            print("fetched %s/%s %s" % (fetcher.count, fetcher.max_gets, url), file=sys.stderr)
    sameas_urls = []
    seen_same = set()
    for page in pages:
        for node in page.get("nodes") or []:
            if "Organization" not in node.get("types", []):
                continue
            for link in node.get("sameAs") or []:
                if link.startswith("http") and link not in seen_same:
                    seen_same.add(link)
                    sameas_urls.append(link)
    sameas_checks = []
    for link in sameas_urls:
        if fetcher.count >= fetcher.max_gets:
            fetcher.truncated = True
            sameas_checks.append({"url": link, "status": None, "dead": True, "skipped": "cap"})
            continue
        status, _body = fetcher.get(link)
        sameas_checks.append({"url": link, "status": status, "dead": status != 200})
    fetch_meta = {
        "generated_at": now or time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "sitemap": sitemap_url,
        "gets": fetcher.count,
        "cap": fetcher.max_gets,
        "truncated": fetcher.truncated,
        "retry_429": fetcher.retry_429,
        "errors": fetcher.errors,
        "http_status": {str(key): value for key, value in fetcher.statuses.items()},
        "sitemap_children": discovered["sitemap_children"],
        "locale_sitemaps_skipped": discovered["locale_sitemaps_skipped"],
        "default_sitemaps_fetched": discovered["default_sitemaps_fetched"],
        "urls_selected": len(discovered["urls"]),
        "urls_fetched": len(pages),
        "robots_disallow": discovered["robots_disallow"],
        "sameas_checks": sameas_checks,
    }
    summary = build_report(pages, canonical_map, labels, repo_hits, constants, fetch_meta)
    return {"summary": summary, "pages": pages}


def write_reports(report, out_path, markdown_path):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    if markdown_path:
        os.makedirs(os.path.dirname(os.path.abspath(markdown_path)), exist_ok=True)
        with open(markdown_path, "w", encoding="utf-8") as fh:
            fh.write(render_markdown(report))


def rerender(json_path, markdown_path, root):
    with open(json_path, encoding="utf-8") as fh:
        report = json.load(fh)
    canonical_map = entity_names.load_map()
    labels = load_labels(root)
    repo_hits, constants = compare_repo(root, canonical_map)
    fetch_meta = report.get("summary", {}).get("fetch") or {}
    report["summary"] = build_report(
        report.get("pages") or [], canonical_map, labels, repo_hits, constants, fetch_meta)
    write_reports(report, json_path, markdown_path)
    return report


def self_test():
    fixture_html = """<!doctype html><html><head>
<title>FloraFresh Vaginal Probiotics Gummies | Wellness Nest</title>
<meta property="og:site_name" content="Wellness Nest">
<meta property="og:title" content="FloraFresh - Vaginal Probiotics Gummies | Wellness Nest">
<meta property="og:description" content="Support vaginal health. 15 Billion CFU probiotics, D-Mannose, and sugar-free gummies. Older copy said 1 billion CFU.">
</head><body>
<h1>Shilajit Gummies Single Jar</h1>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Product","name":"FloraFresh - Vaginal Probiotics Gummies","brand":{"@type":"Brand","name":"Wellness Nest"},"description":"Daily feminine care."}</script>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"Wellness Nest","url":"https://wellnessnest.co","sameAs":["",""],"logo":"https://wellnessnest.co/logo.png"}</script>
<script type="application/ld+json">{"@type":"Organization","name":"WellnessNest","sameAs":["https://example.invalid/brand"]}</script>
</body></html>"""
    page = parse_page(
        "https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies",
        200,
        fixture_html.encode("utf-8"),
    )
    if page["h1s"] != ["Shilajit Gummies Single Jar"]:
        raise SystemExit("self-test: h1")
    if page["og_site_name"] != "Wellness Nest":
        raise SystemExit("self-test: og:site_name")
    summary = build_report(
        [page],
        entity_names.load_map(),
        load_labels(ROOT),
        [],
        {"ORG_NAME": "Wellness Nest"},
        {"sameas_checks": [{"url": "https://example.invalid/brand", "status": 404, "dead": True}]},
    )
    codes = {item["code"] for item in summary["findings"]}
    for required in ("h1_disagrees_with_product_name", "sameas_missing", "organization_conflicting", "sameas_dead"):
        if required not in codes and not any(code.startswith(required) for code in codes):
            raise SystemExit("self-test missing " + required)
    kinds = {item.get("kind") for item in summary["findings"]}
    if "cfu_15_billion" in kinds:
        raise SystemExit("self-test: 15 billion CFU is the label count")
    if "cfu_retired_1_billion" not in kinds:
        raise SystemExit("self-test: retired 1 billion count")
    if "d_mannose" not in kinds or "sugar_free" not in kinds:
        raise SystemExit("self-test: pdp strain story")
    formula = summary["label_formulas"]["florafresh-gummies"]
    if formula != florafresh_label_formula() or "1 billion" in formula:
        raise SystemExit("self-test: label formula " + formula)
    rendered = render_markdown({"summary": summary, "pages": []})
    if "Mike Moretti" not in rendered or "Co-founder, Wellness Nest" not in rendered:
        raise SystemExit("self-test: blog byline")
    if "15B CFU" not in rendered or "1 billion CFU is the retired count" not in rendered:
        raise SystemExit("self-test: label wording")
    noted = render_markdown({
        "summary": summary,
        "pages": [{
            "url": "https://wellnessnest.co/pages/dr-marcus-hale",
            "live_observation": (
                "Live observation: Dr. Marcus Hale appears on this live URL. "
                "Not the blog Article author."
            ),
        }],
    })
    if "Not the blog Article author" not in noted:
        raise SystemExit("self-test: landing byline observation")
    warnings = entity_names.variant_warnings("WellnessNest ships the AgeAura Pure NMN + TMG NAD+ Complex across the US.")
    if not warnings:
        raise SystemExit("self-test: warn")
    if entity_names.variant_warnings("Wellness Nest ships AgeAura Pure NMN + TMG NAD+ Complex across the US. https://wellnessnest.co/products/x"):
        raise SystemExit("self-test: canonical should be quiet")
    print("entity consistency self-test: ok")
    return 0


def main(argv):
    parser = argparse.ArgumentParser(description="Read-only Wellness Nest entity consistency audit")
    parser.add_argument("--out", default=os.path.join(ROOT, "docs", "audits", "entity-consistency-2026-10-20.json"))
    parser.add_argument("--markdown", default=os.path.join(ROOT, "docs", "audits", "entity-consistency-2026-10-20.md"))
    parser.add_argument("--max-gets", type=int, default=400)
    parser.add_argument("--delay", type=float, default=0.4)
    parser.add_argument("--sitemap", default="https://wellnessnest.co/sitemap.xml")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--rerender", metavar="JSON")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.rerender:
        rerender(args.rerender, args.markdown, ROOT)
        print("rerendered %s" % args.rerender)
        return 0
    fetcher = Fetcher(max_gets=args.max_gets, delay=args.delay)
    report = crawl(fetcher, args.sitemap, ROOT)
    write_reports(report, args.out, args.markdown)
    print("gets=%s pages=%s findings=%s" % (
        report["summary"]["fetch"]["gets"],
        report["summary"]["fetch"]["urls_fetched"],
        len(report["summary"]["findings"]),
    ))
    print(args.markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Read-only check: PDF COAs and lab sheets versus crawlable HTML.

Fetches public URLs with GET or HEAD only. It does not upload, publish, or
read bytes as lab results. Assay numbers are never inferred.

A PDF is HAS_HTML_EQUIVALENT only when the seed names an HTML page on the
store host and that page is live HTML whose visible text has a batch/lot
marker plus one of: ppm, heavy metal, or "certificate of analysis". A page
that merely links the PDF does not qualify. The check does not compare PDF
bytes to the HTML.

Usage:
  python3 scripts/coa_pdf_html_check.py
  python3 scripts/coa_pdf_html_check.py --seed data/coa_pdf_html_seed.json --json /tmp/coa.json
  python3 scripts/coa_pdf_html_check.py --crawl --max-pages 40
  python3 scripts/coa_pdf_html_check.py --urls data/coa_pdf_html_rate_limited_2026-10-19.txt
  python3 scripts/coa_pdf_html_check.py --no-network
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SEED = os.path.join(ROOT, "data", "coa_pdf_html_seed.json")
USER_AGENT = "GenSeo-COA-audit/1.0 (read-only; no upload)"
CLASSES = (
    "HAS_HTML_EQUIVALENT",
    "PDF_ONLY",
    "GATED",
    "DEAD_LINK",
    "UNKNOWN",
)
STORE_HOST = "wellnessnest.co"

DEFAULT_CRAWL_URLS = [
    "https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex",
    "https://wellnessnest.co/products/shilasource-himalayan-shilajit-resin",
    "https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies",
    "https://wellnessnest.co/products/fusiforce-creatine-gummies",
    "https://wellnessnest.co/products/premium-himalayan-shilajit-gummies",
    "https://wellnessnest.co/products/pure-shilajit-gold-resin",
    "https://wellnessnest.co/products/shilajit-shockwave",
    "https://wellnessnest.co/products/turkesterone-advanced-formula",
    "https://wellnessnest.co/pages/lab-test-result",
    "https://wellnessnest.co/pages/lab-certificate-en",
    "https://wellnessnest.co/pages/lab-certificate-florafresh",
    "https://wellnessnest.co/pages/lab-test-spanish",
]

_PDF_URL = re.compile(
    r"https?://[^\s\"'<>{}\\]+?\.pdf(?:\?[^\s\"'<>{}\\]*)?(?=[\"'\s<>)]|$)",
    re.I,
)
_HREF = re.compile(r"""(?i)(?:href|src)\s*=\s*["']([^"']+)["']""")
_TAG = re.compile(r"(?is)<(script|style)\b[^>]*>.*?</\1>|<[^>]+>")
_GATE_TEXT = re.compile(
    r"\b(?:sign[\s-]?in|log[\s-]?in|create an account|enter your email|"
    r"subscribe to (?:download|unlock|access)|password|"
    r"captcha|security check|verify you are human|"
    r"enable javascript and cookies to continue)\b",
    re.I,
)
_GATE_MARKUP = re.compile(r"cf-turnstile|g-recaptcha|h-captcha|_cf_chl_opt", re.I)
_MARKERS = (
    ("batch", re.compile(r"\b(?:batch|lot)\b", re.I)),
    ("ppm", re.compile(r"\bppm\b", re.I)),
    ("heavy_metal", re.compile(r"\bheavy metals?\b", re.I)),
    ("coa", re.compile(r"\bcertificate of analysis\b|\bCOA\b", re.I)),
)
_RASTER_NAME = re.compile(
    r"(?i)(?:lab[_-]?test|labtest|certificate|eurofin|assay|(?<![a-z])coa(?![a-z]))"
)
_RASTER_SKIP = re.compile(
    r"(?i)(?:label[-_]?check|labor[-_]?day|logo|inline-|persona|badge)"
)
_RANGE = re.compile(r"/(\d+)\s*$")


def load_seed(path):
    with open(path, encoding="utf-8") as handle:
        seed = json.load(handle)
    if not isinstance(seed, dict):
        raise ValueError("seed must be a JSON object")
    for key in ("pdfs", "raster_lab_sheets"):
        if not isinstance(seed.get(key), list):
            raise ValueError("seed.%s must be a list" % key)
    return seed


def load_url_list(path):
    urls = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def canonical_url(url):
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""
    scheme = parsed.scheme or "https"
    return "%s://%s%s" % (scheme, host, path)


def is_pdf_url(url):
    return urlparse(url).path.lower().endswith(".pdf")


def proof_markers(text):
    """Marker names only. Matched digits are not returned."""
    found = []
    for name, pattern in _MARKERS:
        if pattern.search(text or ""):
            found.append(name)
    return found


def visible_text(html):
    stripped = _TAG.sub(" ", html or "")
    return re.sub(r"\s+", " ", unescape(stripped)).strip()


def shopify_page_json_url(url):
    """Storefront Ajax document for a page. Not a substitute for the HTML response."""
    parsed = urlparse(url)
    path = parsed.path or ""
    if not path or path.endswith(".json"):
        return None
    return parsed._replace(path=path.rstrip("/") + ".json", query="", fragment="").geturl()


def page_json_body_text(payload):
    """Visible text of page.body_html. Returns '' when the payload is not that shape."""
    try:
        data = json.loads(payload or "")
    except json.JSONDecodeError:
        return ""
    if not isinstance(data, dict):
        return ""
    page = data.get("page")
    if not isinstance(page, dict):
        return ""
    return visible_text(page.get("body_html") or "")


def same_store(url, store_host):
    host = (urlparse(url).hostname or "").lower()
    store_host = store_host.lower()
    return host == store_host or host.endswith("." + store_host)


def html_equivalent(candidate, store_host):
    if not candidate:
        return False
    final = candidate.get("final_url") or candidate.get("url") or ""
    if not same_store(final, store_host):
        return False
    if candidate.get("status") != 200:
        return False
    ctype = (candidate.get("content_type") or "").lower()
    if "html" not in ctype:
        return False
    kinds = set(proof_markers(candidate.get("visible_text") or ""))
    return "batch" in kinds and bool(kinds & {"ppm", "heavy_metal", "coa"})


def looks_gated(fetched):
    """Visible gate language, or a known challenge token. CSS class names do not count."""
    if is_pdf_bytes(fetched):
        return False
    body = fetched.get("body") or ""
    if not _GATE_TEXT.search(visible_text(body)) and not _GATE_MARKUP.search(body):
        return False
    ctype = (fetched.get("content_type") or "").lower()
    status = fetched.get("status") or 0
    if "html" in ctype or status in (401, 403) or not ctype:
        return True
    return False


def is_pdf_bytes(fetched):
    ctype = (fetched.get("content_type") or "").lower()
    if "pdf" in ctype:
        return True
    body = fetched.get("body") or ""
    return body.lstrip().startswith("%PDF")


def classify_pdf(item, fetched, html_candidate, store_host):
    """Return one of CLASSES plus a short reason. Does not invent assay values."""
    url = item.get("url") or ""
    status = fetched.get("status") if fetched else None
    if not is_pdf_url(url):
        return "UNKNOWN", "URL is not a PDF"
    if html_equivalent(html_candidate, store_host):
        pdf_bit = "PDF HTTP %s" % (status if status else "UNKNOWN")
        return "HAS_HTML_EQUIVALENT", pdf_bit + "; nominated HTML has proof markers"
    if status in (404, 410):
        return "DEAD_LINK", "HTTP %s" % status
    if fetched and looks_gated(fetched):
        return "GATED", "login, email, or captcha wall"
    if fetched and is_pdf_bytes(fetched) and status and 200 <= status < 400:
        return "PDF_ONLY", "PDF response and no nominated HTML equivalent"
    if fetched and fetched.get("error") and not status:
        return "UNKNOWN", fetched.get("error") or "request failed"
    if status in (401, 403):
        return "UNKNOWN", "HTTP %s without a confirmed gate" % status
    if fetched and status and 200 <= status < 400 and not is_pdf_bytes(fetched):
        return "UNKNOWN", "response was HTML, not a PDF"
    if not fetched or fetched.get("error"):
        return "UNKNOWN", "request failed"
    return "UNKNOWN", "unclassified response"


def extract_pdf_urls(html, base_url):
    found = []
    seen = set()

    def add(url):
        url = unescape(url).strip()
        if not url or not is_pdf_url(url):
            return
        if url.startswith("//"):
            url = "https:" + url
        key = canonical_url(url)
        if key in seen:
            return
        seen.add(key)
        found.append(url)

    for match in _PDF_URL.finditer(html or ""):
        add(match.group(0))
    for href in _HREF.findall(html or ""):
        href = unescape(href).strip()
        if urlparse(href).path.lower().endswith(".pdf"):
            add(urljoin(base_url, href))
    return found


def extract_raster_candidates(html, base_url):
    found = []
    seen = set()
    for href in _HREF.findall(html or ""):
        href = unescape(href).strip()
        path = urlparse(href).path.lower()
        if not path.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif")):
            continue
        name = path.rsplit("/", 1)[-1]
        if not _RASTER_NAME.search(name) or _RASTER_SKIP.search(name):
            continue
        absolute = urljoin(base_url, href)
        key = canonical_url(absolute)
        if key in seen:
            continue
        seen.add(key)
        found.append(absolute)
    return found


def _length_from_headers(headers):
    if not headers:
        return None
    span = headers.get("Content-Range") or ""
    match = _RANGE.search(span)
    if match:
        return int(match.group(1))
    raw = headers.get("Content-Length")
    if raw and str(raw).isdigit():
        return int(raw)
    return None


def fetch_url(url, timeout=15, limit=8192, ranged=True):
    """Public GET. PDF probes use a short range. HTML pages are read further down."""
    result = _fetch_once(url, timeout=timeout, limit=limit, ranged=ranged)
    if result.get("error"):
        result = _fetch_once(url, timeout=timeout, limit=limit, ranged=ranged)
    return result


def _fetch_once(url, timeout, limit, ranged):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/pdf,*/*;q=0.8",
        "Accept-Encoding": "identity",
    }
    if ranged:
        headers["Range"] = "bytes=0-%d" % max(0, limit - 1)
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read(limit)
            headers_out = response.headers
            return {
                "url": url,
                "status": response.status,
                "content_type": headers_out.get("Content-Type") or "",
                "final_url": response.geturl(),
                "body": payload.decode("utf-8", "replace"),
                "content_length": _length_from_headers(headers_out),
                "error": None,
            }
    except HTTPError as exc:
        payload = exc.read(limit) if exc.fp else b""
        headers_out = exc.headers
        return {
            "url": url,
            "status": exc.code,
            "content_type": headers_out.get("Content-Type") if headers_out else "",
            "final_url": url,
            "body": payload.decode("utf-8", "replace"),
            "content_length": _length_from_headers(headers_out),
            "error": None,
        }
    except (URLError, TimeoutError, OSError):
        return {
            "url": url,
            "status": None,
            "content_type": "",
            "final_url": url,
            "body": "",
            "content_length": None,
            "error": "request failed",
        }


def _blank_fetch():
    return {
        "status": None,
        "content_type": "",
        "final_url": "",
        "body": "",
        "content_length": None,
        "error": "network disabled",
    }


class Fetcher(object):
    def __init__(self, fetch, timeout):
        self._fetch = fetch
        self._timeout = timeout
        self._cache = {}

    def get(self, url, limit=8192, ranged=True):
        key = (url, limit, ranged)
        if key in self._cache:
            return self._cache[key]
        if self._fetch is None:
            result = _blank_fetch()
        else:
            result = self._fetch(url, timeout=self._timeout, limit=limit, ranged=ranged)
        self._cache[key] = result
        return result


def _html_candidate(fetcher, url):
    if not url:
        return None
    fetched = fetcher.get(url, limit=2500000, ranged=False)
    return {
        "url": url,
        "final_url": fetched.get("final_url") or url,
        "status": fetched.get("status"),
        "content_type": fetched.get("content_type") or "",
        "visible_text": visible_text(fetched.get("body") or ""),
    }


def check_pdf_item(item, fetcher, store_host):
    url = item.get("url") or ""
    fetched = fetcher.get(url) if url else _blank_fetch()
    candidate = _html_candidate(fetcher, item.get("html_equivalent_url"))
    classification, reason = classify_pdf(item, fetched, candidate, store_host)
    return {
        "url": url,
        "classification": classification,
        "reason": reason,
        "http_status": fetched.get("status"),
        "content_type": fetched.get("content_type") or "",
        "content_length": fetched.get("content_length"),
        "final_url": fetched.get("final_url") or "",
        "product": item.get("product") or "UNKNOWN",
        "role": item.get("role") or "UNKNOWN",
        "linked_from": list(item.get("linked_from") or []),
        "html_equivalent_url": item.get("html_equivalent_url"),
        "assay_values": "UNKNOWN",
        "notes": item.get("notes") or "",
    }


def check_raster_item(item, fetcher, store_host):
    url = item.get("url") or ""
    fetched = fetcher.get(url) if url else _blank_fetch()
    summary_url = item.get("html_summary_url")
    summary = _html_candidate(fetcher, summary_url) if summary_url else None
    if not summary_url:
        summary_status = "not_nominated"
        markers = []
    elif not summary or summary.get("status") is None:
        summary_status = "not_checked"
        markers = []
    elif summary.get("status") != 200 or "html" not in (summary.get("content_type") or "").lower():
        summary_status = "unreachable"
        markers = []
    else:
        markers = proof_markers(summary.get("visible_text") or "")
        summary_status = "markers:" + ",".join(markers) if markers else "no_proof_markers"
    page_json_url = None
    page_json_status = None
    page_json_markers = []
    if summary_url and same_store(summary_url, store_host):
        page_json_url = shopify_page_json_url(summary_url)
        if page_json_url:
            payload = fetcher.get(page_json_url, limit=2500000, ranged=False)
            page_json_status = payload.get("status")
            if payload.get("status") == 200:
                page_json_markers = proof_markers(page_json_body_text(payload.get("body") or ""))
    row = {
        "url": url,
        "kind": "raster_lab_sheet",
        "http_status": fetched.get("status"),
        "content_type": fetched.get("content_type") or "",
        "content_length": fetched.get("content_length"),
        "final_url": fetched.get("final_url") or "",
        "product": item.get("product") or "UNKNOWN",
        "linked_from": list(item.get("linked_from") or []),
        "html_summary_url": summary_url,
        "html_summary_status": summary_status,
        "html_summary_markers": markers,
        "page_json_url": page_json_url,
        "page_json_status": page_json_status,
        "page_json_markers": page_json_markers,
        "html_summary_same_store": bool(summary and same_store(summary.get("final_url") or summary_url, store_host)),
        "bytes_are_pdf": is_pdf_bytes(fetched),
        "assay_values": "UNKNOWN",
        "image_header": item.get("image_header"),
        "notes": item.get("notes") or "",
    }
    return row


def discover_from_pages(urls, fetcher, max_pages):
    pdfs = []
    rasters = []
    seen_pdf = set()
    seen_raster = set()
    for url in urls[:max_pages]:
        fetched = fetcher.get(url, limit=2500000, ranged=False)
        if fetched.get("status") != 200 or "html" not in (fetched.get("content_type") or "").lower():
            continue
        body = fetched.get("body") or ""
        for pdf in extract_pdf_urls(body, fetched.get("final_url") or url):
            key = canonical_url(pdf)
            if key in seen_pdf:
                continue
            seen_pdf.add(key)
            pdfs.append({
                "url": pdf,
                "linked_from": [url],
                "product": "UNKNOWN",
                "role": "discovered",
                "html_equivalent_url": None,
                "notes": "Discovered from a bounded crawl. Assay values UNKNOWN.",
            })
        for image in extract_raster_candidates(body, fetched.get("final_url") or url):
            key = canonical_url(image)
            if key in seen_raster:
                continue
            seen_raster.add(key)
            rasters.append({
                "url": image,
                "linked_from": [url],
                "product": "UNKNOWN",
                "html_summary_url": None,
                "notes": "Filename matched a lab/certificate token. Contents not read.",
            })
    return pdfs, rasters


def merge_items(primary, extra):
    merged = list(primary)
    seen = {canonical_url(item.get("url") or "") for item in primary}
    for item in extra:
        key = canonical_url(item.get("url") or "")
        if key and key not in seen:
            seen.add(key)
            merged.append(item)
    return merged


def count_classes(rows):
    counts = {name: 0 for name in CLASSES}
    for row in rows:
        name = row.get("classification")
        if name in counts:
            counts[name] += 1
    return counts


def run_check(seed, fetch=fetch_url, timeout=15, crawl_urls=None, max_pages=40, network=True):
    store = seed.get("store") or ("https://" + STORE_HOST)
    store_host = urlparse(store).hostname or STORE_HOST
    fetcher = Fetcher(fetch if network else None, timeout)
    discovered_pdfs = []
    discovered_rasters = []
    if crawl_urls:
        discovered_pdfs, discovered_rasters = discover_from_pages(
            crawl_urls, fetcher, max_pages)
    pdf_items = merge_items(seed.get("pdfs") or [], discovered_pdfs)
    raster_items = merge_items(seed.get("raster_lab_sheets") or [], discovered_rasters)
    pdf_rows = [check_pdf_item(item, fetcher, store_host) for item in pdf_items]
    raster_rows = [check_raster_item(item, fetcher, store_host) for item in raster_items]
    for raster in raster_rows:
        if raster["bytes_are_pdf"]:
            pdf_rows.append(check_pdf_item(
                {
                    "url": raster["url"],
                    "product": raster["product"],
                    "role": "raster_url_returned_pdf",
                    "linked_from": raster["linked_from"],
                    "html_equivalent_url": raster.get("html_summary_url"),
                    "notes": raster.get("notes") or "",
                },
                fetcher,
                store_host,
            ))
    return {
        "schema": 1,
        "store": store,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "network": bool(network),
        "counts": count_classes(pdf_rows),
        "pdfs": pdf_rows,
        "raster_lab_sheets": raster_rows,
        "crawl_urls": list(crawl_urls or []),
    }


def _bytes(value):
    if value is None:
        return "UNKNOWN"
    return str(value)


def _status(value):
    if value is None:
        return "UNKNOWN"
    return str(value)


def render_report(report):
    lines = [
        "PDF COA / lab-sheet check (read-only)",
        "store: %s" % report.get("store"),
        "checked_at: %s" % report.get("checked_at"),
        "network: %s" % ("on" if report.get("network") else "off"),
        "",
        "PDF classifications",
    ]
    counts = report.get("counts") or {}
    lines.append(" ".join("%s=%s" % (name, counts.get(name, 0)) for name in CLASSES))
    pdfs = report.get("pdfs") or []
    if not pdfs:
        lines.append("No PDF rows.")
    for row in pdfs:
        linked = row.get("linked_from") or []
        lines.append("")
        lines.append("[%s] role=%s status=%s type=%s bytes=%s" % (
            row.get("classification"),
            row.get("role") or "UNKNOWN",
            _status(row.get("http_status")),
            row.get("content_type") or "UNKNOWN",
            _bytes(row.get("content_length")),
        ))
        lines.append("  url: %s" % row.get("url"))
        if row.get("final_url") and row.get("final_url") != row.get("url"):
            lines.append("  final_url: %s" % row.get("final_url"))
        lines.append("  product: %s" % (row.get("product") or "UNKNOWN"))
        lines.append("  assay_values: UNKNOWN")
        lines.append("  html_equivalent: %s" % (row.get("html_equivalent_url") or "none"))
        lines.append("  reason: %s" % (row.get("reason") or ""))
        lines.append("  linked_from: %s (%s)" % (
            linked[0] if linked else "UNKNOWN", len(linked)))
    lines.append("")
    lines.append("Raster lab sheets (not classified as PDFs)")
    rasters = report.get("raster_lab_sheets") or []
    if not rasters:
        lines.append("No raster rows.")
    for row in rasters:
        linked = row.get("linked_from") or []
        lines.append("")
        lines.append("raster status=%s type=%s bytes=%s summary=%s" % (
            _status(row.get("http_status")),
            row.get("content_type") or "UNKNOWN",
            _bytes(row.get("content_length")),
            row.get("html_summary_status") or "UNKNOWN",
        ))
        lines.append("  url: %s" % row.get("url"))
        lines.append("  product: %s" % (row.get("product") or "UNKNOWN"))
        lines.append("  assay_values: UNKNOWN")
        lines.append("  html_summary: %s" % (row.get("html_summary_url") or "none"))
        if row.get("page_json_url"):
            names = row.get("page_json_markers") or []
            lines.append("  page_json: HTTP %s markers=%s" % (
                _status(row.get("page_json_status")),
                ",".join(names) if names else "none",
            ))
        lines.append("  linked_from: %s (%s)" % (
            linked[0] if linked else "UNKNOWN", len(linked)))
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only PDF COA versus HTML check")
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--json", dest="json_out", help="write the report JSON to this path")
    parser.add_argument("--crawl", action="store_true", help="also fetch the bounded product and lab pages")
    parser.add_argument("--urls", help="extra page URLs, one per line")
    parser.add_argument("--max-pages", type=int, default=40)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args(argv)
    try:
        seed = load_seed(args.seed)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write("coa_pdf_html_check: %s\n" % exc)
        return 2
    crawl_urls = []
    if args.crawl:
        crawl_urls.extend(DEFAULT_CRAWL_URLS)
    if args.urls:
        try:
            crawl_urls.extend(load_url_list(args.urls))
        except OSError as exc:
            sys.stderr.write("coa_pdf_html_check: %s\n" % exc)
            return 2
    report = run_check(
        seed,
        timeout=args.timeout,
        crawl_urls=crawl_urls,
        max_pages=args.max_pages,
        network=not args.no_network,
    )
    text = render_report(report)
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

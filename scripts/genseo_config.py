"""Single source of truth for Shopify store credentials.

Reads JSON from $GENSEO_CONFIG, else ~/.genseo/shopify_token.json:

    {"shop": "your-store.myshopify.com", "access_token": "shpat_..."}

Never commit that file. Every script in this package imports SHOP/TOKEN/API
from here, so you configure the store exactly once.
"""
import json
import os
import sys

API = os.environ.get("SHOPIFY_API_VERSION", "2026-04")

CONFIG_PATH = os.path.expanduser(
    os.environ.get("GENSEO_CONFIG", "~/.genseo/shopify_token.json")
)


def _load():
    if not os.path.exists(CONFIG_PATH):
        sys.exit(
            f"GenSeo: missing config {CONFIG_PATH}\n"
            "  Create it from config.example.json:\n"
            "    mkdir -p ~/.genseo && cp config.example.json ~/.genseo/shopify_token.json\n"
            "    chmod 600 ~/.genseo/shopify_token.json\n"
            "  Then fill in your shop domain and Admin API access token."
        )
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    for key in ("shop", "access_token"):
        if not cfg.get(key) or str(cfg[key]).startswith(("your-", "shpat_YOUR_")):
            sys.exit(f"GenSeo: {CONFIG_PATH} has no real value for '{key}'.")
    return cfg


if os.environ.get("GENSEO_STORE", "wellnessnest") != "wellnessnest":
    sys.exit("GenSEO: legacy scripts are Wellness Nest only; use run_store.py --store.")

_CFG = _load()
SHOP = _CFG["shop"]
TOKEN = _CFG["access_token"]


# Legacy scripts are the Wellness Nest compatibility lane. A Cherish run must use
# run_store.py, which never imports this module or the Wellness Nest knowledge base.
if SHOP != "wellnessnest1.myshopify.com":
    sys.exit("GenSEO: Wellness Nest credential domain mismatch.")


def assert_legacy_request(request):
    """Enforce identity on every urllib Shopify write, including old helper scripts."""
    import urllib.parse
    from store_profiles import Profile, require
    if not hasattr(request, "get_method"):
        return
    url = urllib.parse.urlsplit(request.full_url)
    if "/admin/" not in url.path:
        return
    require(url.hostname == SHOP, "Legacy Shopify request targets another store")
    if request.get_method() in ("GET", "HEAD"):
        return
    profile = Profile("wellnessnest")
    profile.credential_domain()
    headers = {k.lower(): v for k, v in request.header_items()}
    require(headers.get("x-shopify-access-token") == TOKEN, "Legacy write uses a different credential")
    if request.data:
        text = request.data.decode("utf-8", errors="replace")
        # Decode JSON first: escaped quotes (\\") would otherwise end up inside the product handle.
        try:
            import json as _json
            def _strings(v):
                if isinstance(v, str): yield v
                elif isinstance(v, dict): yield from (s for x in v.values() for s in _strings(x))
                elif isinstance(v, list): yield from (s for x in v for s in _strings(x))
            text = "\n".join(_strings(_json.loads(text)))
        except ValueError:
            text = text.replace("\\/", "/")
        profile.check_text(text)


# All existing Shopify helpers import this module. Keep one transport guard so
# alternate publisher functions cannot omit the store assertion.
import urllib.request as _urllib_request
if not getattr(_urllib_request.urlopen, "_genseo_store_guard", False):
    _original_urlopen = _urllib_request.urlopen

    def _guarded_urlopen(request, *args, **kwargs):
        assert_legacy_request(request)
        return _original_urlopen(request, *args, **kwargs)

    _guarded_urlopen._genseo_store_guard = True
    _urllib_request.urlopen = _guarded_urlopen

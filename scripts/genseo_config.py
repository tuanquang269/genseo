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


_CFG = _load()
SHOP = _CFG["shop"]
TOKEN = _CFG["access_token"]

#!/usr/bin/env python3
"""Pick the Admin API token for a job (Kevin 2026-10-06): prefer Kevin's CLI control app (client-credentials,
scripts/shopify_app_token.py) when its granted scopes cover the job; otherwise fall back to the GenSeo publisher
token (genseo_config). Tokens are never printed.
2026-10-08: the CLI app ('0ps Dashboard') now has write_files too, so landing template + pages + Files image uploads
all resolve to "cli-app"; the GenSeo article pipeline does not use pick() and is unchanged.
    from shopify_auth import pick
    shop, token, source = pick({"write_themes", "write_online_store_pages"})
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def pick(need):
    need = set(need)
    if os.environ.get("GENSEO_FORCE_PUBLISHER_TOKEN") != "1":
        try:
            from shopify_app_token import get_token
            shop, tok, scope = get_token()
            have = set(scope.split(","))
            have |= {"read_" + x[6:] for x in have if x.startswith("write_")}   # Shopify omits read_X once write_X is granted
            if need <= have:
                return shop, tok, "cli-app"
        except (Exception, SystemExit):
            pass
    os.environ.setdefault("GENSEO_PUBLISHER_REEXEC", "1")
    import genseo_config as cfg
    return cfg.SHOP, cfg.TOKEN, "genseo-publisher"

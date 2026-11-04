"""Legacy write guard: a valid product link inside JSON-encoded body_html passes; a bad handle still fails."""
import json, os, sys, unittest, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import genseo_config as cfg

def req(html):
    body = json.dumps({"article": {"body_html": html}}).encode()
    url = f"https://{cfg.SHOP}/admin/api/2025-01/blogs/1/articles.json"
    return urllib.request.Request(url, data=body, method="POST", headers={"X-Shopify-Access-Token": cfg.TOKEN})

class T(unittest.TestCase):
    def test_valid_link_passes(self):
        cfg.assert_legacy_request(req('<a href="/products/ageaura-pure-nmn-tmg-nad-complex">NMN</a>'))
    def test_bad_handle_fails(self):
        with self.assertRaises(BaseException):
            cfg.assert_legacy_request(req('<a href="/products/not-a-real-handle-xyz">x</a>'))
    def test_cross_store_fails(self):
        with self.assertRaises(BaseException):
            cfg.assert_legacy_request(req('<a href="https://thecherishcompany.com/products/x">x</a>'))

if __name__ == "__main__":
    unittest.main()

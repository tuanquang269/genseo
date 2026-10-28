import os, re, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
class NoBodyArticle(unittest.TestCase):
    def test_publisher_does_not_emit_body_article(self):
        s = open(os.path.join(ROOT, "scripts", "shopify_publisher.py")).read()
        self.assertNotIn("_ldjson_block(article_schema)", s)
    def test_repair_schema_does_not_add_article(self):
        s = open(os.path.join(ROOT, "scripts", "repair_schema.py")).read()
        self.assertNotRegex(s, r'if "application/ld\+json" not in body or')
if __name__ == "__main__":
    unittest.main()

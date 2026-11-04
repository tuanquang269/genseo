"""Kevin 2026-11-04: article body must not carry the visible image-credits block."""
import os, unittest
SRC = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "shopify_publisher.py")).read()
class T(unittest.TestCase):
    def test_credits_not_appended(self):
        self.assertNotIn("html_content += credits_html", SRC)
if __name__ == "__main__":
    unittest.main()

import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import cluster_internal_links as cil


class GemPagesSkip(unittest.TestCase):
    def test_live_html_gempages_detected(self):
        body = "<p>" + " ".join("word%d" % i for i in range(60)) + "</p>"
        self.assertTrue(cil.live_uses_gempages("x", body, fetch=lambda u: "gempages " * 12 + body))
        self.assertFalse(cil.live_uses_gempages("x", body, fetch=lambda u: "<script>gempages</script><article>" + body + "</article>"))
        self.assertTrue(cil.live_uses_gempages("x", body, fetch=lambda u: "<article><p>other builder text</p></article>"))

    def test_fetch_error_skips(self):
        def boom(u):
            raise OSError("down")
        self.assertTrue(cil.live_uses_gempages("x", fetch=boom))

    def test_gempages_body_skipped_in_plan(self):
        arts = [{"id": 1, "handle": "a", "body_html": "<h2>Design by GemPages</h2>", "blog_id": "news"}]
        updates, skipped = cil.plan_updates(arts, {"clusters": []})
        self.assertEqual(updates, [])
        self.assertIn(("a", "GemPages body"), skipped)


if __name__ == "__main__":
    unittest.main()

"""llms.txt draft generator tests. No live HTTP and no store upload."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import build_llms_txt  # noqa: E402
import brand_rules  # noqa: E402


FIXTURE = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex</loc></url>
      <url><loc>https://wellnessnest.co/products/ageaura-pure-urolithin-a</loc></url>
      <url><loc>https://wellnessnest.co/products/ageaura-longevity-peptides</loc></url>
      <url><loc>https://wellnessnest.co/products/fusiforce-creatine-gummies</loc></url>
      <url><loc>https://wellnessnest.co/products/musclemax-whey</loc></url>
      <url><loc>https://wellnessnest.co/collections/ageaura</loc></url>
      <url><loc>https://wellnessnest.co/collections/shilajit-wellness-stack</loc></url>
      <url><loc>https://wellnessnest.co/collections/mens-essential-collection</loc></url>
      <url><loc>https://wellnessnest.co/blogs/news/when-to-take-nmn</loc></url>
      <url><loc>https://wellnessnest.co/blogs/news/urolithin-a-guide</loc></url>
      <url><loc>https://wellnessnest.co/pages/about</loc></url>
      <url><loc>https://wellnessnest.co/pages/bfcm-sale-page-ttest</loc></url>
      <url><loc>https://wellnessnest.co/policies/refund-policy</loc></url>
    </urlset>
    """)


class LlmsDraftTests(unittest.TestCase):
    def _from_fixture(self):
        _kind, locs = build_llms_txt.parse_sitemap_xml(FIXTURE)
        return build_llms_txt.build_document(
            ROOT,
            sitemap_urls=locs,
            generated_on="2026-10-09",
            source_notes=["fixture"],
            fetched_products=True,
        )

    def test_ageaura_is_nmn_tmg_only(self):
        llms, full, doc = self._from_fixture()
        blob = llms + full
        self.assertIn("ageaura-pure-nmn-tmg-nad-complex", blob)
        self.assertNotIn("urolithin", blob.lower())
        self.assertNotIn("peptide", blob.lower())
        self.assertNotIn("musclemax", blob.lower())
        self.assertNotIn("/collections/ageaura", blob)
        handles = [row["handle"] for row in doc["products"]]
        self.assertEqual(handles.count(brand_rules.AGEAURA_OK), 1)
        self.assertTrue(all(not h.startswith("ageaura") or h == brand_rules.AGEAURA_OK for h in handles))
        self.assertIn("shilajit-wellness-stack", blob)
        self.assertIn("Men's Essential Collection", llms)
        self.assertIn("when-to-take-nmn", blob)
        self.assertNotIn("urolithin-a-guide", blob)
        self.assertIn("/pages/about", blob)
        self.assertIn("/policies/refund-policy", blob)
        self.assertNotIn("bfcm-sale-page", blob)
        self.assertIn("Not uploaded", blob)

    def test_offline_catalog_does_not_invent_collections(self):
        llms, _full, doc = build_llms_txt.build_document(ROOT, generated_on="2026-10-09")
        self.assertEqual(doc["collections"], [])
        self.assertNotIn("## Collections", llms)
        self.assertIn("does not guess collection handles", llms)
        handles = {row["handle"] for row in doc["products"]}
        self.assertIn(brand_rules.AGEAURA_OK, handles)
        self.assertIn("fusiforce-creatine-gummies", handles)
        self.assertIn("shilasource-himalayan-shilajit-resin", handles)
        self.assertNotIn("ageaura-pure-urolithin-a", handles)

    def test_public_head_keeps_catalog_product_missing_from_sitemap(self):
        _llms, full, doc = build_llms_txt.build_document(
            ROOT,
            sitemap_urls=["https://wellnessnest.co/products/fusiforce-creatine-gummies"],
            generated_on="2026-10-09",
            fetched_products=True,
            confirm_url=lambda url: url.endswith("/products/shilasource-himalayan-shilajit-resin"),
        )
        handles = [row["handle"] for row in doc["products"]]
        self.assertIn("shilasource-himalayan-shilajit-resin", handles)
        self.assertIn("HEAD returned 200", full)
        self.assertNotIn("ageaura-pure-urolithin-a", handles)

    def test_local_collection_list_is_used_when_sitemap_has_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "existing_collections.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(
                    [
                        {"title": "Shilajit Wellness Stack", "handle": "shilajit-wellness-stack"},
                        {"title": "AgeAura", "handle": "ageaura"},
                    ],
                    fh,
                )
            _llms, _full, doc = build_llms_txt.build_document(
                ROOT, collections_path=path, generated_on="2026-10-09"
            )
        handles = [row["handle"] for row in doc["collections"]]
        self.assertEqual(handles, ["shilajit-wellness-stack"])

    def test_self_check_makes_no_network_call(self):
        self.assertEqual(build_llms_txt.self_check(), 0)

    def test_cli_writes_drafts_without_fetch_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "build_llms_txt.py"), "--out", tmp],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("Not uploaded", proc.stdout)
            with open(os.path.join(tmp, "llms.txt"), encoding="utf-8") as fh:
                llms = fh.read()
            self.assertIn("ageaura-pure-nmn-tmg-nad-complex", llms)
            self.assertNotIn("urolithin", llms.lower())
            self.assertFalse(os.path.exists(os.path.join(tmp, "README.md")))


if __name__ == "__main__":
    unittest.main()

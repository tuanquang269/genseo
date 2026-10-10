"""AgeAura may promote only the Pure NMN + TMG NAD Complex."""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import brand_rules as br
import topic_fitness as tf

NMN = "ageaura-pure-nmn-tmg-nad-complex"
URO = "ageaura-pure-urolithin-a"


class AgeAuraGuardTests(unittest.TestCase):
    def test_nmn_handle_passes(self):
        self.assertTrue(br.product_allowed(NMN))
        self.assertTrue(br.product_allowed("https://wellnessnest.co/products/" + NMN))
        self.assertEqual(br.assess("AgeAura Pure NMN + TMG NAD Complex").action, "allow")
        self.assertEqual(br.violations("/products/" + NMN), [])
        self.assertEqual(br.resolve_handle(NMN), (NMN, "allow"))

    def test_urolithin_handle_and_title_rejected(self):
        self.assertFalse(br.product_allowed(URO))
        self.assertFalse(br.product_allowed("https://wellnessnest.co/products/" + URO))
        self.assertFalse(br.product_allowed(URO + ":0"))
        decision = br.assess("AgeAura Pure Urolithin A")
        self.assertEqual(decision.action, "deny")
        self.assertTrue(br.violations("AgeAura Pure Urolithin A"))
        self.assertTrue(any("Urolithin" in v for v in br.violations("/products/" + URO)))
        with self.assertRaises(br.GuardError):
            br.resolve_handle(URO)
        with self.assertRaises(br.GuardError):
            br.prepare_ticket("Hero product: /products/" + URO)
        self.assertFalse(br.product_allowed("ageaura-pure-nmn-tmg-p2"))
        self.assertTrue(br.violations("/collections/ageaura"))

    def test_ambiguous_ageaura_rejected_or_forced(self):
        self.assertEqual(br.assess("AgeAura").action, "force")
        self.assertTrue(br.violations("Is AgeAura legit?"))
        with self.assertRaises(br.GuardError):
            br.prepare_promotion("AgeAura review", on_ambiguous="reject")
        locked = br.prepare_ticket("AgeAura review for adults over 40")
        self.assertIn(NMN, locked)
        self.assertIn("NMN + TMG", locked)
        self.assertEqual(br.violations(locked), [])
        self.assertEqual(br.assess(locked).action, "allow")
        handle, how = br.resolve_handle("ageaura")
        self.assertEqual((handle, how), (NMN, "force"))

    def test_other_brands_unchanged(self):
        text = "FusiForce creatine gummies review"
        self.assertTrue(br.product_allowed("fusiforce-creatine-gummies"))
        self.assertEqual(br.assess(text).action, "allow")
        self.assertEqual(br.prepare_ticket(text), text)

    def test_campaign_slug_is_not_a_sku(self):
        path = "tmp_images/landing-ageaura-nmn-listicle-261008/sq-avatar.webp"
        self.assertEqual(br.violations(path), [])
        self.assertTrue(br.asset_path_allowed(
            "product_refs/ageaura-pure-nmn-tmg-nad-complex-cutout.png"))
        self.assertFalse(br.asset_path_allowed("product_refs/" + URO + ".png"))

    def test_image_prompt_and_indexnow_and_llms(self):
        prompt, specs = br.prepare_image_request("a bottle of AgeAura on the counter", ["ageaura"])
        self.assertIn(NMN, prompt)
        self.assertEqual(specs, [NMN])
        self.assertEqual(br.violations(prompt), [])
        with self.assertRaises(br.GuardError):
            br.prepare_image_request("AgeAura Pure Urolithin A bottle", [URO])
        kept, blocked = br.indexnow_urls([
            "https://wellnessnest.co/blogs/news/nmn-and-alcohol-can-you-drink-while-taking-nmn-us",
            "https://wellnessnest.co/products/" + URO,
            "https://wellnessnest.co/blogs/news/urolithin-a-benefits-the-40-problem-us-buyers-miss",
        ])
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(blocked), 2)
        text, rejected = br.llms_txt_draft([NMN, URO, "ageaura", "fusiforce-creatine-gummies"])
        self.assertIn(NMN, text)
        self.assertNotIn("urolithin", text.lower())
        self.assertIn(URO, rejected)
        self.assertEqual(br.violations(text), [])
        br.assert_publishable(
            "NMN and Alcohol",
            "AgeAura Pure NMN + TMG NAD Complex https://wellnessnest.co/products/" + NMN,
        )
        with self.assertRaises(br.GuardError):
            br.assert_publishable("Urolithin A benefits", "shop the bottle")

    def test_product_ref_catalog_drops_urolithin(self):
        handles = br.handles_from_product_refs(os.path.join(ROOT, "product_refs"))
        self.assertIn(URO, handles)
        self.assertIn(NMN, handles)
        text, rejected = br.llms_txt_draft(handles)
        self.assertIn(NMN, text)
        self.assertNotIn("urolithin", text.lower())
        self.assertIn(URO, rejected)

    def test_live_landing_specs_pass(self):
        # shilajit-gummies-listicle-261008.json states a 30-serving panel and 150 mg.
        # tests/test_shilajit_gummies_guard.py asserts that copy fails closed.
        for name in (
            "ageaura-nmn-listicle-261008.json",
            "fusiforce-creatine-listicle-261008.json",
        ):
            with open(os.path.join(ROOT, "landing_drafts", name), encoding="utf-8") as fh:
                raw = fh.read()
            self.assertEqual(br.violations(raw), [], name)
            self.assertEqual(br.violations(json.dumps(json.loads(raw))), [], name)

    def test_topic_fitness_blocks_urolithin_and_keeps_ageaura(self):
        verdict, code, _why = tf.assess("urolithin a benefits review")
        self.assertEqual(verdict, "FAIL")
        self.assertEqual(code, "ageaura-sku")
        verdict, _code, _why = tf.assess("AgeAura review")
        self.assertEqual(verdict, "PASS")

    def test_call_sites_use_the_shared_helper(self):
        rels = [
            "scripts/lint_tickets.py",
            "scripts/validate_article.py",
            "scripts/validate_landing.py",
            "scripts/build_landing_tickets.py",
            "scripts/build_catalog_tickets.py",
            "scripts/build_rich_tickets.py",
            "scripts/build_ctr_tickets.py",
            "scripts/build_refresh_tickets.py",
            "scripts/generate_refresh_tickets.py",
            "scripts/refresh_targets.py",
            "scripts/build_120_tickets.py",
            "scripts/build_90_tickets.py",
            "scripts/autocomplete_candidates.py",
            "scripts/topic_fitness.py",
            "scripts/landing_render.py",
            "scripts/landing_publisher.py",
            "scripts/landing_label_gate.py",
            "scripts/landing_pack_shots.py",
            "scripts/article_images.py",
            "scripts/ad_assets.py",
            "scripts/shopify_publisher.py",
            "scripts/llms_txt_draft.py",
            "scripts/tools/landing_task5_specs.py",
        ]
        for rel in rels:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("brand_rules", text, rel)


if __name__ == "__main__":
    unittest.main()

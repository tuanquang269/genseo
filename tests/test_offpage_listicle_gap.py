"""Mention detection and gap scores. No network."""
import json
import os
import sys
import unittest
from io import BytesIO
from urllib.error import HTTPError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import offpage_listicle_gap as gap
import shilasource_resin_rules


def source(**overrides):
    rec = {
        "id": "aa-fixture",
        "cluster": "ageaura",
        "url": "https://example.com/best-nmn",
        "title": "Best NMN",
        "page_type": "listicle",
        "how_found": "web search rank",
        "evidence": "web search rank",
        "ai_citation_observed": True,
        "search_brands": ["PartiQlar", "Wonderfeel"],
        "search_us_mentioned": False,
        "search_date": "October 16, 2026",
        "seed_queries": ["best NMN supplement"],
    }
    rec.update(overrides)
    return rec


class MentionDetection(unittest.TestCase):
    def test_competitors_without_us_are_a_gap(self):
        rec = gap.assess(source(), "PartiQlar and Wonderfeel lead this NMN list.", basis="fetched_body")
        self.assertFalse(rec["ai_citation_observed"])
        self.assertEqual(rec["evidence"], "web search rank")
        self.assertIn("PartiQlar", rec["competitor_brands"])
        self.assertIn("Wonderfeel", rec["competitor_brands"])
        self.assertFalse(rec["us_mentioned"])
        self.assertTrue(rec["is_gap"])
        self.assertGreater(rec["gap_score"], 0)
        self.assertEqual(rec["outreach"]["action"], "draft_only")
        self.assertIn(gap.ageaura_rules.PRODUCT_URL, rec["outreach"]["offer"])

    def test_ageaura_on_the_page_is_not_a_gap(self):
        text = "PartiQlar, Wonderfeel, and AgeAura Pure NMN are compared here."
        rec = gap.assess(source(), text, basis="fetched_body")
        self.assertTrue(rec["us_mentioned"])
        self.assertIn("AgeAura", rec["us_marks"])
        self.assertFalse(rec["is_gap"])
        self.assertEqual(rec["gap_score"], 0)
        self.assertEqual(rec["outreach"]["action"], "already_named")

    def test_wellness_nest_counts_for_shilajit(self):
        rec = gap.assess(source(
            cluster="shilasource",
            page_type="listicle",
            search_brands=["Pürblack"],
        ), "Pürblack and Wellness Nest both sell resin.", basis="fetched_body")
        self.assertTrue(rec["us_mentioned"])
        self.assertFalse(rec["is_gap"])

    def test_separated_words_are_not_the_brand(self):
        text = "A wellness routine is hard to build. The nest of studies is large. PartiQlar is named."
        rec = gap.assess(source(), text, basis="fetched_body")
        self.assertFalse(rec["us_mentioned"])
        self.assertTrue(rec["is_gap"])

    def test_generic_natural_shilajit_is_not_the_brand(self):
        generic = gap.match_brands(
            "that natural shilajit is more than the sum of its parts",
            "shilasource",
        )
        himalayan_line = gap.match_brands(
            "Himalayan Natural Shilajit Gummies from another seller",
            "shilasource",
        )
        brand = gap.match_brands(
            "Top pick Natural Shilajit resin at naturalshilajit.com",
            "shilasource",
        )
        self.assertNotIn("Natural Shilajit", generic)
        self.assertNotIn("Natural Shilajit", himalayan_line)
        self.assertIn("Natural Shilajit", brand)

    def test_html_meta_date_prefers_modified(self):
        raw = (
            '<meta property="article:published_time" content="2024-09-29T16:25:38.000Z">'
            '<meta property="article:modified_time" content="2025-11-18T16:25:38.000Z">'
        )
        self.assertEqual(gap.find_html_date(raw), "November 18, 2025")
        self.assertEqual(gap.find_html_date("<html>no date</html>"), "")

    def test_gummy_roundup_does_not_pitch_the_resin_as_a_gummy(self):
        rec = gap.assess(source(
            cluster="shilasource",
            title="Best Shilajit Gummies (2026)",
            url="https://example.com/best-gummies",
            search_brands=["Pürblack"],
        ), "Pürblack leads the gummy ranking.", basis="fetched_body")
        self.assertEqual(rec["outreach"]["action"], "draft_only")
        self.assertIn("Do not offer the resin as a gummy", rec["outreach"]["offer"])

    def test_shilasource_token_is_us(self):
        rec = gap.assess(source(cluster="shilasource"), "ShilaSource resin next to Pürblack.", basis="fetched_body")
        self.assertIn("ShilaSource", rec["us_marks"])
        self.assertFalse(rec["is_gap"])

    def test_input_cannot_force_an_ai_citation(self):
        rec = gap.assess(source(ai_citation_observed=True))
        self.assertFalse(rec["ai_citation_observed"])
        self.assertEqual(rec["mention_basis"], "search_snippet")


class Scoring(unittest.TestCase):
    def test_independent_listicle_outranks_a_competitor_roundup_and_reddit(self):
        page = "Nutricost, Double Wood, and ProHealth are on the list."
        editorial = gap.assess(source(page_type="listicle"), page, basis="fetched_body")
        owned = gap.assess(source(
            id="owned", url="https://omre.co/best", page_type="brand_roundup",
        ), page + " Omre is the pick.", basis="fetched_body")
        thread = gap.assess(source(
            id="thread", url="https://www.reddit.com/r/NMN/comments/1/x", page_type="reddit",
        ), page, basis="fetched_body")
        self.assertGreater(editorial["gap_score"], owned["gap_score"])
        self.assertGreater(editorial["gap_score"], thread["gap_score"])
        self.assertEqual(owned["outreach"]["action"], "do_not_pitch")
        self.assertEqual(thread["outreach"]["action"], "do_not_pitch")

    def test_snippet_scores_lower_than_a_fetched_page(self):
        fetched = gap.assess(source(), "PartiQlar and Wonderfeel.", basis="fetched_body")
        snippet = gap.assess(source())
        self.assertGreater(fetched["gap_score"], snippet["gap_score"])
        self.assertEqual(snippet["mention_basis"], "search_snippet")

    def test_explainer_needs_two_brands(self):
        one = gap.assess(source(page_type="explainer"), "Only PartiQlar is named.", basis="fetched_body")
        two = gap.assess(source(page_type="explainer"), "PartiQlar and Wonderfeel are named.", basis="fetched_body")
        self.assertFalse(one["is_gap"])
        self.assertTrue(two["is_gap"])

    def test_unreadable_page_is_not_a_gap(self):
        rec = gap.assess(source(search_brands=None), None)
        self.assertEqual(rec["mention_basis"], "unreadable")
        self.assertFalse(rec["is_gap"])

    def test_stored_fetch_is_not_downgraded_to_the_snippet(self):
        fetched = gap.assess(source(search_brands=["Omre"]), "Nutricost and Double Wood only.", basis="fetched_body")
        again = gap.assess(fetched)
        self.assertEqual(again["mention_basis"], "fetched_body")
        self.assertIn("Nutricost", again["competitor_brands"])
        self.assertNotIn("Omre", again["competitor_brands"])

    def test_date_shown_near_the_top_is_kept(self):
        self.assertEqual(gap.find_date("Published: October 12, 2026 at 9:00 am"), "October 12, 2026")
        self.assertEqual(gap.find_date("Last updated: Nov 18th, 2025\n\nBody"), "Nov 18th, 2025")
        self.assertEqual(gap.find_date("Last reviewed Apr 2026 by the desk"), "Apr 2026")
        late = ("word " * 400) + "Updated October 2, 2024"
        self.assertEqual(gap.find_date(late), "")

    def test_top_list_is_capped_and_ordered(self):
        rows = []
        for i, weight in enumerate(("reddit", "listicle", "brand_roundup")):
            rows.append(gap.assess(source(
                id="r%s" % i,
                url="https://example.com/%s" % i,
                page_type=weight,
            ), "PartiQlar and Wonderfeel.", basis="fetched_body"))
        top = gap.rank_gaps(rows, "ageaura", limit=2)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0]["page_type"], "listicle")


class FetchPolicy(unittest.TestCase):
    def test_robots_disallow_does_not_get_the_article(self):
        seen = []

        def opener(req, timeout=15):
            seen.append(req.full_url)
            if req.full_url.endswith("/robots.txt"):
                body = b"User-agent: *\nDisallow: /best-nmn\n"
                return _Resp(200, body, req.full_url)
            raise AssertionError("article was fetched: " + req.full_url)

        doc = gap.fetch_sources(
            {"sources": [source()]},
            opener=opener,
            sleeper=lambda _s: None,
            budget_limit=20,
        )
        self.assertEqual(len(seen), 1)
        self.assertIn("robots disallow", doc["sources"][0].get("fetch_note") or "")
        self.assertGreaterEqual(doc["fetch_log"]["robots_disallow"], 1)
        self.assertEqual(doc["sources"][0]["mention_basis"], "search_snippet")

    def test_429_retries_once(self):
        calls = {"page": 0}
        slept = []

        def opener(req, timeout=15):
            if req.full_url.endswith("/robots.txt"):
                raise HTTPError(req.full_url, 404, "missing", {}, BytesIO(b""))
            calls["page"] += 1
            if calls["page"] == 1:
                raise HTTPError(req.full_url, 429, "slow", {}, BytesIO(b"slow"))
            html = "<html><title>Best NMN</title><body>%s</body></html>" % ("Nutricost and Double Wood. " * 40)
            return _Resp(200, html.encode(), req.full_url)

        doc = gap.fetch_sources(
            {"sources": [source(search_brands=["Omre"])]},
            opener=opener,
            sleeper=slept.append,
            budget_limit=20,
        )
        self.assertIn(8, slept)
        row = doc["sources"][0]
        self.assertEqual(row["http_status"], 200)
        self.assertEqual(row["mention_basis"], "fetched_body")
        self.assertIn("Nutricost", row["competitor_brands"])
        self.assertNotIn("Omre", row["competitor_brands"])
        self.assertFalse(row["ai_citation_observed"])
        self.assertGreaterEqual(doc["fetch_log"]["http_429"], 1)

    def test_contact_page_must_be_same_site(self):
        old = dict(gap.CONTACT_TRIES)
        gap.CONTACT_TRIES = {"example.com": [
            "https://example.com/missing",
            "https://example.com/contact",
        ]}

        def opener(req, timeout=15):
            if req.full_url.endswith("/robots.txt"):
                raise HTTPError(req.full_url, 404, "missing", {}, BytesIO(b""))
            if req.full_url.endswith("/missing"):
                raise HTTPError(req.full_url, 404, "no", {}, BytesIO(b"no"))
            if req.full_url.endswith("/contact"):
                return _Resp(200, b"<html><title>Contact</title><body>Write to the desk.</body></html>", req.full_url)
            html = "<html><title>Best NMN</title><body>%s</body></html>" % ("PartiQlar and Wonderfeel. " * 40)
            return _Resp(200, html.encode(), req.full_url)

        try:
            doc = gap.fetch_sources(
                {"sources": [source()]},
                opener=opener,
                sleeper=lambda _s: None,
                budget_limit=20,
            )
        finally:
            gap.CONTACT_TRIES = old
        self.assertEqual(doc["sources"][0]["editor_contact_url"], "https://example.com/contact")
        self.assertEqual(doc["sources"][0]["outreach"]["contact_url"], "https://example.com/contact")

    def test_a_timeout_keeps_the_snippet_and_finishes(self):
        def opener(req, timeout=15):
            raise TimeoutError("timed out")

        doc = gap.fetch_sources(
            {"sources": [source()]},
            opener=opener,
            sleeper=lambda _s: None,
            budget_limit=6,
        )
        self.assertEqual(len(doc["sources"]), 1)
        self.assertEqual(doc["sources"][0]["mention_basis"], "search_snippet")
        self.assertTrue(doc["sources"][0]["is_gap"])

    def test_meta_date_fills_a_page_whose_prose_has_no_byline(self):
        html = (
            "<html><title>Best NMN</title>"
            '<meta property="article:published_time" content="2026-10-16T21:58:32-00:00">'
            "<body><p>PartiQlar and Wonderfeel lead the list.</p></body></html>"
        )

        def opener(req, timeout=15):
            if req.full_url.endswith("/robots.txt"):
                raise HTTPError(req.full_url, 404, "missing", {}, BytesIO(b""))
            return _Resp(200, html.encode(), req.full_url)

        doc = gap.fetch_sources(
            {"sources": [source(search_date="")]},
            opener=opener,
            sleeper=lambda _s: None,
            budget_limit=6,
        )
        row = doc["sources"][0]
        self.assertEqual(row["date_shown"], "October 16, 2026")
        self.assertEqual(row["date_source"], "html_meta")


class RepoFiles(unittest.TestCase):
    def test_seeds_are_hypothesised_and_in_range(self):
        seeds, problems = gap.validate_seeds(os.path.join(ROOT, "data", "offpage_seeds"))
        self.assertEqual(problems, [], problems)
        total = sum(len(v) for v in seeds.values())
        self.assertGreaterEqual(total, 20)
        self.assertLessEqual(total, 40)
        self.assertIn("best NMN with TMG", seeds["ageaura"])
        self.assertIn("best shilajit resin", seeds["shilasource"])
        joined = " ".join(seeds["ageaura"] + seeds["shilasource"]).lower()
        self.assertNotIn("urolithin", joined)

    def test_catalog_report_stays_inside_the_product_locks(self):
        path = os.path.join(ROOT, "data", "offpage_sources_2026-10-20.json")
        doc = gap.score_document(gap.load_document(path))
        seeds, problems = gap.validate_seeds(os.path.join(ROOT, "data", "offpage_seeds"))
        self.assertEqual(problems, [])
        text = gap.render_report(doc, seeds)
        self.assertIn("hypothesised", text)
        self.assertIn("`ai_citation_observed: false`", text)
        self.assertIn(gap.ageaura_rules.PRODUCT_URL, text)
        self.assertIn(gap.SHILA_URL, text)
        self.assertNotIn("urolithin", text.lower())
        self.assertNotIn("/collections/ageaura", text)
        self.assertEqual(shilasource_resin_rules.violations(text), [])
        self.assertEqual(gap.guard_copy(text), [])
        aa = gap.rank_gaps(doc["sources"], "ageaura", 15)
        ss = gap.rank_gaps(doc["sources"], "shilasource", 15)
        self.assertGreaterEqual(len(aa), 10)
        self.assertGreaterEqual(len(ss), 8)
        self.assertTrue(all(not r["us_mentioned"] for r in aa + ss))
        owned = [r for r in doc["sources"] if r["id"] == "aa-omre-best"][0]
        self.assertEqual(owned["outreach"]["action"], "do_not_pitch")
        named = [r for r in doc["sources"] if r["id"] == "ss-trustpilot"][0]
        self.assertTrue(named["us_mentioned"])
        self.assertFalse(named["is_gap"])


class _Resp:
    def __init__(self, status, body, url):
        self.status = status
        self._body = body
        self._url = url

    def read(self, _n=None):
        return self._body

    def geturl(self):
        return self._url


if __name__ == "__main__":
    unittest.main()

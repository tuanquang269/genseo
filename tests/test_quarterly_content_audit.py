"""Decision rules for the quarterly news-blog audit. No network."""
import datetime as dt
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import quarterly_content_audit as q

TODAY = dt.date(2026, 10, 20)
SITE = "https://wellnessnest.co"


def blog(**kwargs):
    handle = kwargs.get("handle", "nmn-guide")
    row = {
        "handle": handle,
        "title": "What Is NMN: A Complete Guide",
        "url": "%s/blogs/news/%s" % (SITE, handle),
        "cluster": "ageaura-nmn",
        "is_pillar": False,
        "words": 1800,
        "words_source": "html",
        "published": "2026-09-01",
        "scope": "blog",
        "body_seen": True,
        "inbound": 2,
        "bodies_complete": True,
        "http_status": 200,
    }
    row.update(kwargs)
    if "url" not in kwargs:
        row["url"] = "%s/blogs/news/%s" % (SITE, row["handle"])
    return row


def actions(rows, gsc=None, assign_pillars=False):
    audited = q.audit_rows(rows, TODAY, gsc_rows=gsc, assign_pillars=assign_pillars)
    return {row["handle"]: row for row in audited}


class DecisionTests(unittest.TestCase):
    def test_same_segment_dosage_consolidates_weaker_page(self):
        found = actions([
            blog(handle="nmn-dosage-guide", title="NMN Dosage: How Much NMN Per Day", words=1900, is_pillar=True),
            blog(handle="how-much-nmn-per-day", title="How Much NMN Per Day: What Trials Used", words=1600),
        ])
        self.assertEqual(found["how-much-nmn-per-day"]["suggested_action"], "CONSOLIDATE")
        self.assertIn("nmn-dosage-guide", found["how-much-nmn-per-day"]["merge_into"])
        self.assertIn(found["nmn-dosage-guide"]["suggested_action"], {"KEEP", "REFRESH"})

    def test_cross_cluster_template_titles_stay_separate(self):
        found = actions([
            blog(
                handle="how-long-does-nmn-take-to-work",
                title="How Long Does NMN Take to Work? Week by Week",
                cluster="ageaura-nmn",
                is_pillar=True,
            ),
            blog(
                handle="how-long-does-creatine-take-to-work",
                title="How Long Does Creatine Take to Work? Week by Week",
                cluster="creatine",
                is_pillar=True,
            ),
        ])
        self.assertEqual(found["how-long-does-nmn-take-to-work"]["suggested_action"], "KEEP")
        self.assertEqual(found["how-long-does-creatine-take-to-work"]["suggested_action"], "KEEP")

    def test_empty_stomach_is_not_merged_into_how_to_take(self):
        found = actions([
            blog(
                handle="how-to-take-creatine-gummies",
                title="How to Take Creatine Gummies in the US",
                cluster="creatine",
                is_pillar=True,
            ),
            blog(
                handle="creatine-gummies-on-an-empty-stomach",
                title="Creatine Gummies on an Empty Stomach: US Guide",
                cluster="creatine",
            ),
        ])
        self.assertNotEqual(found["creatine-gummies-on-an-empty-stomach"]["suggested_action"], "CONSOLIDATE")

    def test_more_specific_audience_stays_separate(self):
        found = actions([
            blog(handle="nmn-for-women", title="NMN for Women: What Changes", is_pillar=True),
            blog(handle="nmn-for-women-over-50", title="NMN for Women Over 50: What to Expect"),
        ])
        self.assertNotEqual(found["nmn-for-women-over-50"]["suggested_action"], "CONSOLIDATE")

    def test_different_versus_pages_stay_separate(self):
        found = actions([
            blog(handle="nmn-vs-nr", title="NMN vs NR: What Trials Say", is_pillar=True),
            blog(handle="nmn-vs-tmg", title="NMN Alone vs NMN and Resveratrol: Which Fits"),
        ])
        self.assertNotEqual(found["nmn-vs-tmg"]["suggested_action"], "CONSOLIDATE")

    def test_identical_title_consolidates_the_shorter_page(self):
        found = actions([
            blog(handle="nmn-guide", title="What Is NMN: A Complete Guide", words=2200, is_pillar=True),
            blog(handle="what-is-nmn-complete-guide", title="What Is NMN: A Complete Guide", words=500),
        ])
        loser = found["what-is-nmn-complete-guide"]
        self.assertEqual(loser["suggested_action"], "CONSOLIDATE")
        self.assertIn("title", loser["overlap_edge"])

    def test_zero_impression_thin_old_page_is_prune(self):
        found = actions([
            blog(handle="nmn-pillar", title="What Is NMN: A Complete Guide", words=2000, is_pillar=True),
            blog(handle="thin-old", title="A short NMN storage note for travelers", words=300, published="2025-01-01"),
        ], gsc=[{"query": "other", "page": SITE + "/blogs/news/someone-else", "impressions": "3", "clicks": "0", "position": "9"}])
        thin = found["thin-old"]
        self.assertEqual(thin["suggested_action"], "PRUNE")
        self.assertEqual(thin["gsc_clicks"], 0)
        self.assertEqual(thin["gsc_impressions"], 0)
        self.assertEqual(thin["gsc_note"], "no row in export")

    def test_clicks_block_prune_and_request_refresh(self):
        found = actions([
            blog(handle="nmn-pillar", words=2000, is_pillar=True),
            blog(handle="thin-clicks", title="NMN storage on a trip", words=400, published="2025-01-01"),
        ], gsc=[{
            "query": "nmn storage",
            "page": SITE + "/blogs/news/thin-clicks",
            "impressions": "12",
            "clicks": "2",
            "position": "14",
        }])
        self.assertEqual(found["thin-clicks"]["suggested_action"], "REFRESH")
        self.assertEqual(found["thin-clicks"]["gsc_clicks"], 2)

    def test_long_zero_impression_page_is_refresh(self):
        found = actions([
            blog(handle="old-long", title="What Is NMN: A Complete Guide", words=1600, published="2025-01-01", is_pillar=True),
        ], gsc=[])
        self.assertEqual(found["old-long"]["suggested_action"], "REFRESH")
        self.assertIn("zero impressions", found["old-long"]["reason"])

    def test_low_impressions_stay_refresh(self):
        found = actions([
            blog(handle="low", title="NMN storage facts", words=400, published="2025-01-01"),
            blog(handle="nmn-pillar", words=2000, is_pillar=True),
        ], gsc=[{
            "query": "nmn storage",
            "page": SITE + "/blogs/news/low",
            "impressions": "8",
            "clicks": "0",
            "position": "18",
        }])
        self.assertEqual(found["low"]["suggested_action"], "REFRESH")

    def test_structural_prune_without_gsc_is_very_thin_only(self):
        found = actions([
            blog(handle="nmn-pillar", words=2000, is_pillar=True),
            blog(handle="stub", title="NMN stub", words=280, published="2025-01-01", inbound=0),
            blog(handle="medium", title="NMN medium note about bottles", words=520, published="2025-01-01", inbound=0),
        ])
        self.assertEqual(found["stub"]["suggested_action"], "PRUNE")
        self.assertEqual(found["medium"]["suggested_action"], "REFRESH")
        self.assertEqual(found["stub"]["gsc_clicks"], q.NEEDS_GSC)
        self.assertIn("needs GSC data", found["stub"]["reason"])

    def test_missing_gsc_cells_are_labelled(self):
        found = actions([blog()])
        row = found["nmn-guide"]
        self.assertEqual(row["gsc_clicks"], q.NEEDS_GSC)
        self.assertEqual(row["gsc_impressions"], q.NEEDS_GSC)
        self.assertEqual(row["gsc_position"], q.NEEDS_GSC)
        sheet = q.sheet_row(row)
        self.assertEqual(sheet["gsc_note"], q.NEEDS_GSC)
        self.assertNotEqual(sheet["word_count"], 0)

    def test_young_thin_page_is_not_pruned(self):
        found = actions([
            blog(handle="nmn-pillar", words=2000, is_pillar=True),
            blog(handle="new-thin", title="NMN new thin note", words=250, published="2026-10-01", inbound=0),
        ], gsc=[])
        self.assertNotEqual(found["new-thin"]["suggested_action"], "PRUNE")

    def test_only_page_in_a_cluster_is_not_structurally_pruned(self):
        found = actions([
            blog(handle="lonely", title="Ayurveda overview note", cluster="other", words=250, published="2025-01-01", inbound=0),
        ])
        self.assertNotEqual(found["lonely"]["suggested_action"], "PRUNE")

    def test_404_is_prune(self):
        found = actions([blog(handle="gone", http_status=404, words=2000)])
        self.assertEqual(found["gone"]["suggested_action"], "PRUNE")
        self.assertIn("404", found["gone"]["reason"])

    def test_frozen_and_generated_handles_stay(self):
        found = actions([
            blog(handle="frozen-nmn", title="Frozen NMN note", words=200, published="2024-01-01", frozen=True),
            blog(handle="generated-article-12", title="Generated", words=100, published="2024-01-01"),
        ], gsc=[])
        self.assertEqual(found["frozen-nmn"]["suggested_action"], "KEEP")
        self.assertEqual(found["generated-article-12"]["suggested_action"], "KEEP")

    def test_product_collection_and_landing_are_report_only(self):
        found = actions([
            {"url": SITE + "/products/ageaura-pure-nmn-tmg-nad-complex", "title": "AgeAura", "handle": "ageaura-pure-nmn-tmg-nad-complex"},
            {"url": SITE + "/collections/best-seller", "title": "Best", "handle": "best-seller"},
            {"url": SITE + "/", "title": "Home", "handle": ""},
            blog(handle="gsl-shilajit-offer", title="Offer"),
        ])
        for handle in ("ageaura-pure-nmn-tmg-nad-complex", "best-seller", "gsl-shilajit-offer"):
            self.assertEqual(found[handle]["suggested_action"], q.REPORT_ONLY)
        home = next(row for row in found.values() if row["url"] == SITE + "/")
        self.assertEqual(home["suggested_action"], q.REPORT_ONLY)

    def test_pillar_is_protected_without_gsc(self):
        found = actions([
            blog(handle="nmn-guide", title="What Is NMN: A Complete Guide", words=800, is_pillar=True),
            blog(handle="nmn-guide-b", title="What Is NMN: A Complete Guide", words=2400),
        ])
        self.assertNotEqual(found["nmn-guide"]["suggested_action"], "CONSOLIDATE")
        self.assertEqual(found["nmn-guide-b"]["suggested_action"], "CONSOLIDATE")

    def test_more_clicks_can_outrank_a_pillar(self):
        page = SITE + "/blogs/news/nmn-guide-b"
        found = actions([
            blog(handle="nmn-guide", title="What Is NMN: A Complete Guide", words=2400, is_pillar=True),
            blog(handle="nmn-guide-b", title="What Is NMN: A Complete Guide", words=900),
        ], gsc=[
            {"query": "what is nmn", "page": page, "impressions": "40", "clicks": "6", "position": "8"},
            {"query": "what is nmn", "page": SITE + "/blogs/news/nmn-guide", "impressions": "4", "clicks": "0", "position": "20"},
        ])
        self.assertEqual(found["nmn-guide"]["suggested_action"], "CONSOLIDATE")
        self.assertIn("pillar", found["nmn-guide"]["reason"].lower())

    def test_menomate_serial_consolidates_into_the_stronger_archive_url(self):
        found = actions([
            blog(
                handle="journey-w6",
                title="The MenoMate Journey: Month 2 - Week 6: How Black Cohosh Can Help",
                cluster="menopause",
                is_pillar=True,
                words=1200,
            ),
            blog(
                handle="journey-w8",
                title="The MenoMate Journey: Month 2 - Week 8: How Curry Leaf Can Help",
                cluster="menopause",
                words=900,
            ),
            blog(
                handle="symptoms",
                title="The 5 Worst Menopause Symptoms Nobody Listed",
                cluster="menopause",
                words=1500,
            ),
        ])
        self.assertEqual(found["journey-w8"]["suggested_action"], "CONSOLIDATE")
        self.assertIn("journey-w6", found["journey-w8"]["merge_into"])
        self.assertNotEqual(found["symptoms"]["suggested_action"], "CONSOLIDATE")

    def test_shorter_serial_pillar_is_named_for_the_owner(self):
        rows, info = q.build_audit([
            blog(
                handle="journey-w6",
                title="The MenoMate Journey: Month 2 - Week 6: How Black Cohosh Can Help",
                cluster="menopause",
                is_pillar=True,
                words=1009,
            ),
            blog(
                handle="meal-w3",
                title="The MenoMate Meal Plan: Set 1 - Week 3: Why You Need Spice",
                cluster="menopause",
                words=1507,
            ),
        ], TODAY, assign_pillars=False)
        text = " ".join(info["decisions"])
        self.assertIn("journey-w6", text)
        self.assertIn("meal-w3", text)
        self.assertIn("1507", text)
        found = {row["handle"]: row for row in rows}
        self.assertEqual(found["meal-w3"]["suggested_action"], "CONSOLIDATE")
        self.assertIn("journey-w6", found["meal-w3"]["merge_into"])

    def test_numbered_handle_with_a_different_title_is_refresh(self):
        found = actions([
            blog(handle="from-stiff-to-strong", title="How Menopause Affects Your Gut", cluster="menopause", is_pillar=True),
            blog(handle="from-stiff-to-strong-1", title="From Stiff to Strong: Joint Pain During Menopause", cluster="menopause"),
        ])
        self.assertEqual(found["from-stiff-to-strong-1"]["suggested_action"], "REFRESH")
        self.assertIn("handle variant", found["from-stiff-to-strong-1"]["duplicate_siblings"])

    def test_copied_opening_consolidates(self):
        tokens = frozenset("term%d" % i for i in range(40))
        found = actions([
            blog(handle="keep-body", title="Shilajit resin sourcing overview", cluster="shilajit", words=2000, is_pillar=True, body_tokens=tokens),
            blog(handle="copy-body", title="Quality control in the mountains", cluster="shilajit", words=700, body_tokens=tokens),
        ])
        self.assertEqual(found["copy-body"]["suggested_action"], "CONSOLIDATE")
        self.assertIn("body", found["copy-body"]["overlap_edge"])

    def test_group_winner_is_not_pruned(self):
        found = actions([
            blog(handle="winner", title="What Is NMN: A Complete Guide", words=500, is_pillar=True),
            blog(handle="loser", title="What Is NMN: A Complete Guide", words=300, published="2025-01-01"),
        ], gsc=[])
        self.assertEqual(found["loser"]["suggested_action"], "CONSOLIDATE")
        self.assertNotEqual(found["winner"]["suggested_action"], "PRUNE")

    def test_stale_distinct_page_is_refresh(self):
        found = actions([blog(handle="stale", published="2025-01-01", words=1800, is_pillar=True)])
        self.assertEqual(found["stale"]["suggested_action"], "REFRESH")
        self.assertIn("Last updated", found["stale"]["reason"])

    def test_short_pillar_is_refresh(self):
        found = actions([blog(handle="short-pillar", words=1100, is_pillar=True)])
        self.assertEqual(found["short-pillar"]["suggested_action"], "REFRESH")
        self.assertIn("Pillar", found["short-pillar"]["reason"])

    def test_climb_and_ctr_positions_refresh(self):
        climb = actions([
            blog(handle="climb", words=1800, is_pillar=True),
        ], gsc=[{
            "query": "nmn guide",
            "page": SITE + "/blogs/news/climb",
            "impressions": "40",
            "clicks": "1",
            "position": "15",
        }])
        self.assertEqual(climb["climb"]["suggested_action"], "REFRESH")
        ctr = actions([
            blog(handle="ctr", words=1800, is_pillar=True),
        ], gsc=[{
            "query": "nmn guide",
            "page": SITE + "/blogs/news/ctr",
            "impressions": "100",
            "clicks": "1",
            "position": "4",
        }])
        self.assertEqual(ctr["ctr"]["suggested_action"], "REFRESH")
        self.assertIn("CTR", ctr["ctr"]["reason"])

    def test_healthy_page_is_keep(self):
        found = actions([
            blog(handle="healthy", words=1800, is_pillar=True),
        ], gsc=[{
            "query": "nmn guide",
            "page": SITE + "/blogs/news/healthy",
            "impressions": "100",
            "clicks": "8",
            "position": "4",
        }])
        self.assertEqual(found["healthy"]["suggested_action"], "KEEP")

    def test_template_near_title_without_shared_angle_is_not_a_refresh(self):
        found = actions([
            blog(
                handle="turk-alcohol",
                title="Turkesterone and Alcohol: 6 Things to Know",
                cluster="turkesterone",
                is_pillar=True,
            ),
            blog(
                handle="turk-creatine",
                title="Turkesterone and Creatine: 6 Things to Know",
                cluster="turkesterone",
            ),
        ])
        self.assertEqual(found["turk-alcohol"]["suggested_action"], "KEEP")
        self.assertEqual(found["turk-creatine"]["suggested_action"], "KEEP")


class CatalogAndCrawlTests(unittest.TestCase):
    def test_cluster_map_markdown_keeps_words_and_drops_impressions(self):
        text = "\n".join([
            "## Example",
            "",
            "Id: `ageaura-nmn`. Live articles: 2.",
            "",
            "Pillar: [NMN Dosage](https://wellnessnest.co/blogs/news/nmn-dosage) (1900 words, 73 impressions, position 4.20).",
            "",
            "Spokes:",
            "- [Other NMN](https://wellnessnest.co/blogs/news/other-nmn)",
            "",
        ])
        parsed = q.articles_from_markdown(text)
        self.assertEqual(len(parsed), 2)
        pillar = next(row for row in parsed if row["handle"] == "nmn-dosage")
        self.assertTrue(pillar["is_pillar"])
        self.assertEqual(pillar["words"], 1900)
        self.assertNotIn("impressions", pillar)
        audited = q.audit_rows(parsed, TODAY, assign_pillars=False)
        self.assertTrue(all(row["gsc_impressions"] == q.NEEDS_GSC for row in audited))

    def test_committed_cluster_map_parses_blog_urls_only(self):
        path = os.path.join(ROOT, "docs", "CLUSTER_MAP.md")
        with open(path, encoding="utf-8") as handle:
            parsed = q.articles_from_markdown(handle.read())
        self.assertGreaterEqual(len(parsed), 100)
        self.assertTrue(all("/blogs/news/" in row["url"] for row in parsed))
        self.assertTrue(any(row["is_pillar"] and row["words"] for row in parsed))

    def test_english_article_sitemaps_skip_locale_and_products(self):
        index = """<?xml version="1.0"?>
        <sitemapindex>
          <sitemap><loc>https://wellnessnest.co/sitemap_products_1.xml</loc></sitemap>
          <sitemap><loc>https://wellnessnest.co/sitemap_articles_1.xml</loc></sitemap>
          <sitemap><loc>https://wellnessnest.co/fr/sitemap_articles_1.xml</loc></sitemap>
        </sitemapindex>
        """
        self.assertEqual(
            q.english_article_sitemaps(index),
            ["https://wellnessnest.co/sitemap_articles_1.xml"],
        )

    def test_bulk_lastmod_day_is_not_an_editorial_update(self):
        today = dt.date(2026, 10, 20)
        days = [today] * 8 + [dt.date(2025, 8, 13)]
        bulk = q.bulk_lastmod_days(days, today)
        self.assertEqual(bulk, {today})

    def test_polite_client_stops_at_the_get_cap(self):
        calls = []

        def opener(url):
            calls.append(url)
            return (200, "ok", url, {})

        client = q.PoliteClient(max_gets=2, delay=0, sleep=lambda _s: None, opener=opener)
        self.assertIsNotNone(client.get("https://wellnessnest.co/blogs/news/a"))
        self.assertIsNotNone(client.get("https://wellnessnest.co/blogs/news/b"))
        self.assertIsNone(client.get("https://wellnessnest.co/blogs/news/c"))
        self.assertEqual(len(calls), 2)
        self.assertIn("max gets", client.stopped)

    def test_polite_client_backs_off_on_429(self):
        slept = []
        state = {"n": 0}

        def opener(_url):
            state["n"] += 1
            if state["n"] < 3:
                return (429, "", "https://wellnessnest.co/blogs/news/a", {"Retry-After": "0"})
            return (200, "ok", "https://wellnessnest.co/blogs/news/a", {})

        client = q.PoliteClient(max_gets=6, delay=0, sleep=lambda wait: slept.append(wait), opener=opener)
        result = client.get("https://wellnessnest.co/blogs/news/a")
        self.assertEqual(result["status"], 200)
        self.assertGreaterEqual(client.gets, 3)
        self.assertTrue(slept)

    def test_crawl_reads_blog_urls_only(self):
        requested = []
        index = """<?xml version="1.0"?>
        <sitemapindex>
          <sitemap><loc>https://wellnessnest.co/sitemap_products_1.xml</loc></sitemap>
          <sitemap><loc>https://wellnessnest.co/sitemap_collections_1.xml</loc></sitemap>
          <sitemap><loc>https://wellnessnest.co/sitemap_articles_1.xml</loc></sitemap>
          <sitemap><loc>https://wellnessnest.co/fr/sitemap_articles_1.xml</loc></sitemap>
        </sitemapindex>
        """
        articles = """<?xml version="1.0"?>
        <urlset>
          <url>
            <loc>https://wellnessnest.co/blogs/news/nmn-guide</loc>
            <lastmod>2026-01-02T00:00:00Z</lastmod>
          </url>
          <url><loc>https://wellnessnest.co/products/nope</loc></url>
        </urlset>
        """
        atom = '<feed xmlns="http://www.w3.org/2005/Atom"></feed>'
        body = (
            "<html><head><meta property=\"og:title\" content=\"NMN Guide\"></head>"
            "<article><div itemprop=\"articleBody\"><p>%s</p>"
            "<a href=\"/blogs/news/other-nmn\">Other</a></div></article>"
            "<time datetime=\"2026-02-01T00:00:00Z\">February 1, 2026</time></html>"
        ) % ("nmn dosage evidence " * 40)

        def opener(url):
            requested.append(url)
            if url == SITE + "/sitemap.xml":
                return (200, index, url, {})
            if url == SITE + "/sitemap_articles_1.xml":
                return (200, articles, url, {})
            if url == SITE + "/blogs/news.atom":
                return (200, atom, url, {})
            if url == SITE + "/blogs/news/nmn-guide":
                return (200, body, url, {})
            raise AssertionError("unexpected GET %s" % url)

        client = q.PoliteClient(max_gets=20, delay=0, sleep=lambda _s: None, opener=opener)
        rows = []
        report_only, meta = q.crawl_public(rows, client, TODAY)
        self.assertTrue(all("/products" not in url and "/collections" not in url and "/fr/" not in url for url in requested))
        self.assertEqual(report_only[0]["url"], SITE + "/products/nope")
        guide = next(row for row in rows if row["handle"] == "nmn-guide")
        self.assertGreater(guide["words"], 40)
        self.assertEqual(guide["words_source"], "html")
        self.assertIn("other-nmn", guide["outbound"])
        self.assertLessEqual(meta["gets"], 20)
        self.assertEqual(guide["published"], dt.date(2026, 2, 1))

    def test_legacy_page_uses_main_content_and_jsonld_date(self):
        page = (
            "<html><head>"
            '<script type="application/ld+json">{"datePublished":"2025-07-21T21:02:05Z"}</script>'
            '<meta property="og:title" content="Introducing The MenoMate Meal Plan"></head>'
            '<div id="MainContent"><style>.x{color:red}</style><p>%s</p>'
            '<a href="/blogs/news/menomate-guide">guide</a></div>'
            "<footer>shop</footer></html>"
        ) % ("protein serving " * 80)
        fields = q.extract_article_fields(page, "intro-menomate-meal-plan")
        self.assertTrue(fields["body_seen"])
        self.assertGreater(fields["words"], 50)
        self.assertNotIn("color", fields["body_text"])
        self.assertEqual(fields["published"], "2025-07-21")
        self.assertIn("menomate-guide", fields["outbound"])

    def test_article_body_still_beats_main_content(self):
        page = (
            "<html><div id=\"MainContent\">nav chrome words that should not count "
            "<article><div itemprop=\"articleBody\"><p>nmn dose</p></div></article>"
            "<footer>end</footer></div></html>"
        )
        fields = q.extract_article_fields(page, "nmn-guide")
        self.assertEqual(fields["words"], 2)
        self.assertNotIn("chrome", fields["body_text"])

    def test_self_check_stays_offline(self):
        self.assertEqual(q.self_check(), 0)


if __name__ == "__main__":
    unittest.main()

"""Offline GEO cluster map, source intake, topic picker, and in-body links.

No network. No Shopify writes. Fixtures live in tests/fixtures/geo_clusters/.
"""
import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import build_cluster_map
import cluster_internal_links as cil
import cluster_related_questions as crq
import cluster_topic_picker as picker
import refill_tickets as rt
import wellness_sources_intake as intake
import wn_clusters as wc

FIX = os.path.join(ROOT, "tests", "fixtures", "geo_clusters")
PY = sys.executable


def _bank():
    return {
        "topics": [],
        "products": {
            wc.RESIN: {"family": "shilajit", "name": "ShilaSource Himalayan Shilajit Resin"},
            wc.AGEAURA: {"family": "nmn", "name": "AgeAura Pure NMN + TMG"},
            wc.FLORA: {"family": "probiotic", "name": "FloraFresh"},
        },
        "segments": {
            "beginners": "beginners",
            "for-women": "for women",
            "for-men": "for men",
            "how-to-take": "how to take",
            "dosage": "dosage",
            "side-effects": "side effects",
            "seniors": "seniors",
            "athletes": "athletes",
            "price": "price",
            "buy": "buy",
            "versus": "versus",
            "timing": "timing",
            "how-long": "how long",
            "fertility": "fertility",
            "midlife": "midlife",
        },
        "families": {"shilajit": ["shilajit"], "nmn": ["nmn"], "probiotic": ["probiotic"]},
    }


def _map(intake_items=None):
    articles = wc.merge_articles(
        wc.load_json_articles(os.path.join(FIX, "articles.json")),
        wc.load_csv_articles(os.path.join(FIX, "articles.csv")),
        wc.load_tracker(os.path.join(FIX, "tracker.csv")),
    )
    gsc = wc.read_gsc_csv(os.path.join(FIX, "gsc.csv"))
    items = intake_items if intake_items is not None else [{
        "title": "How to take Bacillus coagulans on an empty stomach",
        "cluster": "florafresh",
        "url": "https://pubmed.ncbi.nlm.nih.gov/1003/",
        "source": "intake",
    }]
    return wc.build_map(articles, gsc, items, {"built": "2026-10-20", "sources": {"fixture": FIX}})


def _cluster(data, cid):
    for cluster in data["clusters"]:
        if cluster["id"] == cid:
            return cluster
    raise AssertionError(cid)


class AssignAndGuards(unittest.TestCase):
    def test_cluster_assignment_and_handles(self):
        self.assertEqual(wc.assign_cluster("NMN and NAD+ with TMG"), "ageaura-nmn")
        self.assertEqual(wc.assign_cluster("Bacillus coagulans vaginal probiotics"), "florafresh")
        self.assertEqual(wc.assign_cluster("shilajit resin fulvic"), "shilajit")
        self.assertEqual(wc.assign_cluster("shilajit in ayurveda"), "shilajit")
        self.assertEqual(wc.assign_cluster("What is Ayurveda"), "other")
        self.assertEqual(wc.assign_cluster("Probiotics and Birth Control"), "florafresh")
        self.assertEqual(wc.assign_cluster("Probiotics for BV"), "florafresh")
        self.assertEqual(wc.assign_cluster("menopause hot flash support"), "menopause")
        self.assertTrue(wc.other_sku_handle("shilajit", "best-shilajit-gummies-2026"))
        self.assertFalse(wc.other_sku_handle("shilajit", "what-is-shilajit-guide"))
        self.assertEqual(wc.assign_cluster("creatine gummies"), "creatine")
        self.assertFalse(wc.safe_handle("gsl-shilajit-listicle"))
        self.assertFalse(wc.safe_handle("landing-nmn"))
        self.assertTrue(wc.is_dupe_handle("news-copy-of-joint-pain-5"))
        self.assertFalse(wc.is_dupe_handle("nmn-for-seniors-2026"))
        self.assertFalse(wc.ageaura_rules.article_link_allowed("urolithin-a-old-page"))

    def test_blog_endpoint_refuses_other_resources(self):
        ok = "https://shop.example/admin/api/2026-04/blogs/%s/articles/9.json" % wc.BLOG_ID
        self.assertTrue(wc.assert_blog_article_endpoint(ok).endswith("articles/9.json"))
        for bad in (
            "https://shop.example/admin/api/2026-04/products/1.json",
            "https://shop.example/admin/api/2026-04/pages/1.json",
            "https://shop.example/admin/api/2026-04/collections/1.json",
            "https://shop.example/admin/api/2026-04/themes/1/assets.json",
            "https://shop.example/admin/api/2026-04/blogs/999/articles/1.json",
        ):
            with self.assertRaises(RuntimeError):
                wc.assert_blog_article_endpoint(bad)

    def test_topic_text_stays_on_allowed_products(self):
        flora = wc._evidence("florafresh", wc.FLORA)
        resin = wc._evidence("shilajit", wc.RESIN)
        aura = wc._evidence("ageaura-nmn", wc.AGEAURA)
        self.assertIn("SNZ-1969", flora)
        self.assertIn("15B CFU", flora)
        self.assertNotIn("1 billion CFU", flora)
        self.assertNotIn("1B CFU", flora)
        self.assertNotIn("sugar-free", flora.lower())
        self.assertEqual(wc.guard_topic_text(flora, wc.FLORA), [])
        self.assertEqual(wc.guard_topic_text(resin, wc.RESIN), [])
        self.assertEqual(wc.guard_topic_text(aura, wc.AGEAURA), [])
        self.assertIn("ageaura-pure-nmn-tmg-nad-complex", aura)
        bad = "FloraFresh is sugar-free with 1 billion CFU from four Lactobacillus strains and XOS."
        self.assertTrue(wc.guard_topic_text(bad, wc.FLORA))
        self.assertTrue(wc.guard_topic_text("buy urolithin a", wc.AGEAURA))
        self.assertTrue(wc.query_blocked("shilajit", "shilajit gummies price"))
        self.assertTrue(wc.query_blocked("shilajit", "menomate menopause"))
        self.assertTrue(wc.query_blocked("florafresh", "vaginal probiotics and pregnancy outcomes"))
        self.assertTrue(wc.query_blocked("ageaura-nmn", "anti-inflammatory effects of NMN after exercise"))
        self.assertFalse(wc.query_blocked("shilajit", "shilajit for beginners"))


class MapAndTopics(unittest.TestCase):
    def setUp(self):
        self.data = _map()

    def test_pillar_is_the_guide_and_stale_json_is_not_a_target(self):
        shila = _cluster(self.data, "shilajit")
        self.assertEqual(shila["pillar"]["handle"], "what-is-shilajit-guide")
        self.assertGreater(shila["pillar"]["impressions"], 0)
        handles = [s["handle"] for s in shila["spokes"]]
        self.assertIn("old-shilajit-foundation", handles)
        stale = [s for s in shila["spokes"] if s["handle"] == "old-shilajit-foundation"][0]
        self.assertTrue(stale["stale_only"])
        targets = [h for _k, h in wc.link_targets(shila, "shilajit-for-athletes-trial")]
        self.assertNotIn("urolithin-a-old-page", targets)
        self.assertNotIn("gsl-shilajit-listicle", targets)
        self.assertNotIn("old-shilajit-foundation", targets)
        self.assertNotIn("news-copy-of-joint-pain-5", targets)
        self.assertIn("what-is-shilajit-guide", targets)
        self.assertGreaterEqual(len(targets), 3)
        self.assertLessEqual(len(targets), 5)

    def test_gaps_are_position_band_and_product_limited(self):
        shila = _cluster(self.data, "shilajit")
        queries = [g["query"] for g in shila["gaps"]]
        self.assertIn("shilajit for beginners", queries)
        self.assertNotIn("shilajit side effects", queries)
        self.assertNotIn("shilajit gummies price", queries)
        self.assertNotIn("wellness nest", queries)
        self.assertNotIn("nmn price", queries)
        topics = wc.topics_from_map(self.data, _bank(), limit=8)
        primaries = [t["primary"] for t in topics]
        products = {t["product"] for t in topics}
        self.assertIn("shilajit for beginners", primaries)
        self.assertIn("nmn for women", primaries)
        self.assertTrue(any("vaginal probiotics for women" in p for p in primaries))
        self.assertTrue(any("empty stomach" in p for p in primaries))
        self.assertEqual(products, {wc.RESIN, wc.AGEAURA, wc.FLORA})
        for topic in topics:
            self.assertNotIn("gummies", topic["primary"])
            self.assertNotIn("urolithin", topic["primary"])
            self.assertNotIn("menomate", topic["primary"])
            self.assertLessEqual(len(topic["title"]), 60)
            self.assertIn("US 2026", topic["title"])
            self.assertEqual(wc.guard_topic_text(
                " ".join([topic["primary"], topic["title"], topic["evidence"], topic["angle"]]),
                topic["product"],
            ), [])
            if topic["product"] == wc.AGEAURA:
                self.assertIn("https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex", topic["evidence"])
        self.assertTrue(topics[0]["rank"] >= topics[-1]["rank"])

    def test_gsc_current_period_is_not_mixed_with_prior(self):
        rows = [
            {"period": "prior", "query": "shilajit for beginners", "page": "https://wellnessnest.co/",
             "impressions": "1000", "clicks": "9", "position": "4"},
            {"period": "current", "query": "shilajit for beginners", "page": "https://wellnessnest.co/",
             "impressions": "20", "clicks": "0", "position": "14"},
            {"period": "current", "query": "shilajit for beginners", "page": "https://wellnessnest.co/blogs/news/what-is-shilajit-guide",
             "impressions": "5", "clicks": "1", "position": "12"},
        ]
        _pages, queries = wc.aggregate_gsc(rows)
        self.assertEqual(queries["shilajit for beginners"]["impressions"], 25)
        self.assertNotEqual(queries["shilajit for beginners"]["impressions"], 1025)
        kept = wc.current_period_rows([{"query": "nmn dosage", "impressions": "3", "position": "16"}])
        self.assertEqual(len(kept), 1)

    def test_segment_names_accept_the_topic_bank_dict(self):
        self.assertIn("beginners", wc.segment_names(_bank()))
        self.assertIn("how-to-take", wc.segment_names(None) or wc.segment_names({}))


class QuestionsAndLinks(unittest.TestCase):
    def setUp(self):
        self.data = _map()
        self.shila = _cluster(self.data, "shilajit")

    def test_new_article_gets_sentences_and_three_to_five_questions(self):
        questions = wc.related_questions("", self.shila, limit=5)
        self.assertGreaterEqual(len(questions), 3)
        self.assertLessEqual(len(questions), 5)
        handles = [q["handle"] for q in questions]
        self.assertEqual(len(handles), len(set(handles)))
        self.assertIn(self.shila["pillar"]["handle"], handles)
        md = crq.package_markdown("", self.shila)
        self.assertIn("## What to ask next", md)
        self.assertIn("The pillar page for this topic is", md)
        self.assertNotIn("### ", md)
        self.assertNotIn("FAQPage", md)
        html = wc.related_questions_html(questions)
        self.assertNotIn("FAQPage", html)
        self.assertNotIn("application/ld+json", html)
        self.assertIn('data-genseo-cluster-link="related-questions"', html)
        self.assertIn("<h2>What to ask next</h2>", html)
        body = "<h2>Frequently Asked Questions</h2><h3>Shipping?</h3><p>Yes.</p>"
        new_body, added = wc.plan_article_html(body, "shilajit-for-athletes-trial", self.shila)
        self.assertTrue(added)
        self.assertLess(new_body.index("What to ask next"), new_body.index("Frequently Asked Questions"))
        self.assertIn("<p data-genseo-cluster-link=", new_body)
        self.assertGreaterEqual(sum(1 for a in added if a["kind"] != "question"), 2)
        again, added2 = wc.plan_article_html(new_body, "shilajit-for-athletes-trial", self.shila)
        self.assertEqual(added2, [])
        self.assertEqual(again, new_body)
        faq_only = __import__("re").search(
            r"##\s+(?:Frequently Asked Questions|FAQs?)[^\n]*\n(.*)",
            md + "\n## Frequently Asked Questions\n\n### How long does shipping take?\n\nThree to five days.\n",
            __import__("re").I | __import__("re").S,
        )
        self.assertIsNotNone(faq_only)
        self.assertNotIn("What to ask next", faq_only.group(1))
        self.assertIn("How long does shipping take?", faq_only.group(1))

    def test_existing_href_is_not_inserted_again(self):
        url = wc.article_url("what-is-shilajit-guide")
        body = "<p>See <a href=\"%s\">guide</a>.</p><h2>Frequently Asked Questions</h2>" % url
        _new, added = wc.plan_article_html(body, "shilajit-price-cost", self.shila)
        kinds = {(a["kind"], a["handle"]) for a in added}
        self.assertNotIn(("pillar", "what-is-shilajit-guide"), kinds)

    def test_sugar_free_title_does_not_become_the_anchor(self):
        self.assertEqual(
            wc.anchor_text("FloraFresh is sugar-free with 1B CFU"),
            "the related article in this cluster",
        )
        self.assertIn("Shilajit", wc.anchor_text("What Is Shilajit: A Complete Guide"))

    def test_plan_skips_landing_and_limits(self):
        articles = [
            {"id": 1, "handle": "gsl-shilajit-listicle", "title": "x", "body_html": "<p>a</p>", "blog_id": wc.BLOG_ID},
            {"id": 2, "handle": "shilajit-price-cost", "title": "p", "body_html": "<p>a</p><h2>Frequently Asked Questions</h2>", "blog_id": wc.BLOG_ID},
            {"id": 3, "handle": "shilajit-for-seniors-checks", "title": "s", "body_html": "<p>a</p>", "blog_id": wc.BLOG_ID},
        ]
        updates, skipped = cil.plan_updates(articles, self.data, limit=1)
        self.assertEqual(len(updates), 1)
        self.assertTrue(any(h == "gsl-shilajit-listicle" for h, _r in skipped))

    def test_dry_run_does_not_put_and_rollback_restores_only_with_apply(self):
        articles = [{
            "id": 2,
            "handle": "shilajit-price-cost",
            "title": "p",
            "body_html": "<p>a</p><h2>Frequently Asked Questions</h2>",
            "blog_id": wc.BLOG_ID,
        }]

        class Store:
            def __init__(self):
                self.puts = []

            def put_body(self, article_id, body):
                self.puts.append((article_id, body))

        store = Store()
        args = argparse.Namespace(
            apply=False, dry_run=True, rollback=None, map="", articles=None,
            from_shopify=False, report=None, limit=None,
        )
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cil.run(args, store=store, articles=articles, cluster_map=self.data), 0)
        self.assertEqual(store.puts, [])
        updates, _skipped = cil.plan_updates(articles, self.data, limit=None)
        with tempfile.TemporaryDirectory() as d:
            path = cil.write_backup(updates, d)
            self.assertTrue(path.endswith(".json"))
            with open(path, encoding="utf-8") as backup_f:
                payload = json.load(backup_f)
            self.assertEqual(payload["kind"], "genseo-cluster-links")
            self.assertEqual(str(payload["blog_id"]), wc.BLOG_ID)
            self.assertIn("Frequently Asked Questions", payload["articles"][0]["body_html"])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cil.apply_rollback(path, store, apply=False), 0)
            self.assertEqual(store.puts, [])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cil.apply_rollback(path, store, apply=True), 0)
            self.assertEqual(store.puts[0][0], 2)
            self.assertIn("Frequently Asked Questions", store.puts[0][1])
            payload["kind"] = "other"
            bad = os.path.join(d, "bad.json")
            with open(bad, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            with self.assertRaises(SystemExit):
                cil.apply_rollback(bad, store, apply=True)


class PickerHook(unittest.TestCase):
    def test_flag_defaults_off_and_on_prepends_candidates(self):
        data = _map()
        bank = _bank()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "cluster_map.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            old_flag = os.environ.pop("GENSEO_CLUSTER_PICKER", None)
            old_map = os.environ.get("GENSEO_CLUSTER_MAP")
            try:
                os.environ.pop("GENSEO_CLUSTER_PICKER", None)
                os.environ["GENSEO_CLUSTER_MAP"] = path
                self.assertEqual(rt.cluster_picker_topics(bank), [])
                os.environ["GENSEO_CLUSTER_PICKER"] = "0"
                self.assertEqual(rt.cluster_picker_topics(bank), [])
                os.environ["GENSEO_CLUSTER_PICKER"] = "1"
                picked = rt.cluster_picker_topics(bank)
                self.assertTrue(picked)
                self.assertTrue(all(t["product"] in (wc.RESIN, wc.AGEAURA, wc.FLORA) for t in picked))
                full = rt.load_bank(os.path.join(ROOT, "templates", "article-topic-bank.json"))
                ctx = {"day": __import__("datetime").date(2026, 10, 20), "fam_count": {}}
                cands, _held = rt.candidates(full, [], ctx)
                self.assertEqual(cands[0]["source"], "cluster-picker")
                self.assertEqual(cands[0]["priority"], -1)
                self.assertTrue(any(c["source"] == "topic-bank" for c in cands))
            finally:
                if old_flag is None:
                    os.environ.pop("GENSEO_CLUSTER_PICKER", None)
                else:
                    os.environ["GENSEO_CLUSTER_PICKER"] = old_flag
                if old_map is None:
                    os.environ.pop("GENSEO_CLUSTER_MAP", None)
                else:
                    os.environ["GENSEO_CLUSTER_MAP"] = old_map


class IntakeOffline(unittest.TestCase):
    def test_parsers_and_robots(self):
        ids, err = intake.parse_esearch('{"esearchresult":{"idlist":["1001","1002"]}}')
        self.assertIsNone(err)
        self.assertEqual(ids, ["1001", "1002"])
        blocked, berr = intake.parse_esearch("<html><body>blocked diagnostic</body></html>")
        self.assertEqual(blocked, [])
        self.assertTrue(berr)
        epmc, eerr = intake.parse_europepmc(json.dumps({
            "resultList": {"result": [{
                "source": "MED",
                "pmid": "555",
                "title": "Shilajit and exercise performance",
                "abstractText": "Adults took shilajit.",
                "journalTitle": "Journal of Ethnopharmacology",
                "pubYear": "2026",
                "authorString": "Rao A, Lee B",
            }]}
        }), "shilajit")
        self.assertIsNone(eerr)
        self.assertEqual(epmc[0]["pmid"], "555")
        self.assertEqual(epmc[0]["via"], "europepmc")
        rows = intake.parse_esummary(json.dumps({
            "result": {
                "uids": ["1001"],
                "1001": {
                    "title": "Shilajit supplementation and exercise",
                    "fulljournalname": "Journal of Ethnopharmacology",
                    "pubdate": "2026 Sep",
                    "authors": [{"name": "Rao A"}],
                },
            }
        }))
        self.assertEqual(rows[0]["pmid"], "1001")
        decorated = intake.decorate_pubmed(rows, {})
        self.assertEqual(decorated[0]["cluster"], "shilajit")
        self.assertEqual(decorated[0]["status"], "new")
        rss = intake.parse_rss(
            "<rss><channel><item><title>NIH notes NAD research</title>"
            "<link>https://www.nih.gov/news/nad</link><description>NAD aging</description></item>"
            "<item><title>Sports scores</title><link>https://example.com/s</link>"
            "<description>unrelated</description></item></channel></rss>"
        )
        self.assertEqual(len(rss), 1)
        self.assertIn("NAD", rss[0]["title"])
        allowed, delay = intake.robots_decision("User-agent: *\nDisallow: /secret\nCrawl-delay: 2\n", "https://example.com/secret")
        self.assertFalse(allowed)
        self.assertEqual(delay, 2.0)
        allowed_ok, _delay = intake.robots_decision("User-agent: *\nAllow: /\n", "https://example.com/fact")
        self.assertTrue(allowed_ok)
        first = intake.ods_highlight("https://ods.od.nih.gov/factsheets/Probiotics-Consumer/", "<title>Probiotics</title><p>Bacillus coagulans</p>", None)
        self.assertEqual(first["status"], "new")
        self.assertEqual(first["cluster"], "florafresh")
        second = intake.ods_highlight("https://ods.od.nih.gov/factsheets/Probiotics-Consumer/", "<title>Probiotics</title><p>Bacillus coagulans updated</p>", first["text_hash"])
        self.assertEqual(second["status"], "changed")

    def test_polite_client_honors_robots_without_network(self):
        calls = []

        class Resp:
            def __init__(self, body):
                self.status = 200
                self.headers = {}
                self._body = body

            def read(self):
                return self._body

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def opener(req, timeout=45):
            calls.append(req.full_url)
            if req.full_url.endswith("/robots.txt"):
                return Resp(b"User-agent: *\nDisallow: /blocked\nCrawl-delay: 99\n")
            return Resp(b"should-not-fetch")

        client = intake.PoliteClient(0, 8, lambda _n: None, opener)
        status, _body, err = client.get("https://example.test/blocked/page")
        self.assertEqual(status, 0)
        self.assertEqual(err, "robots-disallow")
        self.assertTrue(all(u.endswith("/robots.txt") for u in calls))
        status, _body, err = client.get("https://example.test/open")
        self.assertEqual(err, "crawl-delay")

    def test_fixtures_dry_run_writes_nothing_and_apply_writes_the_note(self):
        with tempfile.TemporaryDirectory() as d:
            state = os.path.join(d, "state.json")
            out = os.path.join(d, "notes")
            args = argparse.Namespace(
                dry_run=True, fixtures=os.path.join(FIX, "intake.json"), out_dir=out, state=state,
                fresh_state=False, day="2026-10-20", delay=0, max_crawl_delay=8, retmax=1,
                reldate=30, no_rss=False,
            )
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(intake.run(args), 0)
            self.assertFalse(os.path.exists(state))
            self.assertFalse(os.path.exists(out))
            args.dry_run = False
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(intake.run(args), 0)
            with open(os.path.join(out, "2026-10-20.md"), encoding="utf-8") as note_f:
                note = note_f.read()
            self.assertIn("Highlight:", note)
            self.assertIn("shilajit", note.lower())
            self.assertIn("Cluster:", note)
            with open(state, encoding="utf-8") as state_f:
                saved = json.load(state_f)
            self.assertIn("pubmed:1001", saved["items"])
            proc = subprocess.run(
                [PY, os.path.join(ROOT, "scripts", "wellness_sources_intake.py"),
                 "--fixtures", os.path.join(FIX, "intake.json"), "--dry-run", "--day", "2026-10-20",
                 "--state", os.path.join(d, "missing.json")],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("PubMed", proc.stdout)


class CliFixtures(unittest.TestCase):
    def test_cluster_map_and_picker_cli_stay_offline(self):
        with tempfile.TemporaryDirectory() as d:
            out_json = os.path.join(d, "map.json")
            out_md = os.path.join(d, "map.md")
            proc = subprocess.run(
                [PY, os.path.join(ROOT, "scripts", "build_cluster_map.py"),
                 "--json", os.path.join(FIX, "articles.json"),
                 "--csv", os.path.join(FIX, "articles.csv"),
                 "--tracker", os.path.join(FIX, "tracker.csv"),
                 "--gsc", os.path.join(FIX, "gsc.csv"),
                 "--intake", os.path.join(FIX, "intake-state.json"),
                 "--out-json", out_json, "--out-md", out_md,
                 "--no-vault", "--day", "2026-10-20"],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("pillars=", proc.stdout)
            with open(out_md, encoding="utf-8") as map_f:
                text = map_f.read()
            self.assertIn("What Is Shilajit: A Complete Guide", text)
            self.assertNotIn("—", text)
            picked = subprocess.run(
                [PY, os.path.join(ROOT, "scripts", "cluster_topic_picker.py"),
                 "--map", out_json, "--json", "--limit", "5"],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(picked.returncode, 0, picked.stderr)
            rows = json.loads(picked.stdout)
            self.assertTrue(rows)
            self.assertTrue(all(r["product"] in (wc.RESIN, wc.AGEAURA, wc.FLORA) for r in rows))
            pack = subprocess.run(
                [PY, os.path.join(ROOT, "scripts", "cluster_related_questions.py"),
                 "--map", out_json, "--query", "shilajit for beginners", "--package"],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(pack.returncode, 0, pack.stderr)
            self.assertIn("What to ask next", pack.stdout)
            self.assertIn("/blogs/news/", pack.stdout)
            missing = subprocess.run(
                [PY, os.path.join(ROOT, "scripts", "cluster_related_questions.py"),
                 "--map", os.path.join(d, "nope.json"), "--handle", "nmn-guide"],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(missing.returncode, 0)
            self.assertIn("missing", missing.stdout)


if __name__ == "__main__":
    unittest.main()

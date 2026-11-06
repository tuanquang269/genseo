"""Mapping tests for the AgeAura AI Mode gap map. No network."""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import ai_mode_gap_map as gap

SEED_PATH = os.path.join(ROOT, "data/ai_mode_seeds/ageaura_nmn_tmg.json")
PDP = "https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex"
DENIED = "https://wellnessnest.co/products/ageaura-pure-nmn-tmg-p2"
ARTICLE = "https://wellnessnest.co/blogs/news/nmn-and-tmg-together-why-the-pairing-matters-us-2026"
DOSE = "https://wellnessnest.co/blogs/news/nmn-tmg-dosage-how-much-per-day"


def page(url, headings, **extra):
    body = {
        "url": url,
        "status": 200,
        "kind": gap.kind_of(url),
        "noindex": False,
        "h1": headings[0]["text"] if headings else "",
        "headings": headings,
        "coverage_allowed": gap.coverage_allowed(url),
        "indexable": True,
        "flags": [],
    }
    body["indexable"] = (
        body["status"] == 200 and body["coverage_allowed"] and not body["noindex"]
    )
    body.update(extra)
    if "indexable" not in extra:
        body["indexable"] = (
            body["status"] == 200 and body["coverage_allowed"] and not body["noindex"]
        )
    return body


def h(level, text):
    return {"level": level, "text": text}


ARTICLE_HTML = """<html><head>
<script type="application/ld+json">{"@type":"FAQPage","mainEntity":[
 {"@type":"Question","name":"Can you take NMN and TMG at the same time?",
  "acceptedAnswer":{"@type":"Answer","text":"One note cites 250 mg."}}
]}</script>
<title>Visa</title>
<meta property="og:title" content="NMN and TMG Together">
</head><body>
<h2>Your cart is empty</h2>
<summary>Shop All</summary>
<h1>NMN and TMG Together</h1>
<p>The article body names 500 mg from a trial.</p>
<a href="https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex">AgeAura</a>
<a href="/products/ageaura-pure-nmn-tmg-p2">other</a>
<h2>Your Path to Ultimate Wellness</h2>
<h2>Footer claims it cures cancer</h2>
</body></html>"""


class PhraseMatch(unittest.TestCase):
    def test_plural_and_word_boundaries(self):
        self.assertTrue(gap.phrase_in("capsule", "Why two capsules, not one?"))
        self.assertTrue(gap.phrase_in("side effect", "NMN side effects"))
        self.assertFalse(gap.phrase_in("fast", "Faster walking in older adults"))
        self.assertFalse(gap.phrase_in("men", "NMN for women"))
        self.assertFalse(gap.phrase_in("50", "500 mg NMN"))
        self.assertTrue(gap.phrase_in("nmn and tmg", "NMN + TMG Together"))
        self.assertFalse(gap.phrase_in("methyl", "Promotes Methylation Balance"))
        self.assertTrue(gap.phrase_in("methylation", "Promotes Methylation Balance"))

    def test_groups_are_alternatives(self):
        self.assertTrue(gap.groups_hit("How much TMG with NMN?", [["how much", "tmg"]]))
        self.assertFalse(gap.groups_hit("How much TMG with NMN?", [["ratio"]]))
        self.assertFalse(gap.groups_hit("anything", []))


class Extract(unittest.TestCase):
    def test_content_window_faq_and_flags(self):
        parsed = gap.extract_page(ARTICLE_HTML, ARTICLE)
        texts = [item["text"] for item in parsed["headings"]]
        self.assertIn("NMN and TMG Together", texts)
        self.assertIn("Can you take NMN and TMG at the same time?", texts)
        self.assertNotIn("Your cart is empty", texts)
        self.assertNotIn("Footer claims it cures cancer", texts)
        self.assertTrue(parsed["indexable"])
        kinds = {flag["kind"] for flag in parsed["flags"]}
        self.assertIn("milligram", kinds)
        self.assertIn("denied_product_link", kinds)
        self.assertNotIn("disease", kinds)
        self.assertIn("ageaura-pure-nmn-tmg-nad-complex", parsed["product_links"])

    def test_denied_product_url_is_not_coverage(self):
        parsed = gap.extract_page("<h1>AgeAura</h1><h2>Same time</h2>", DENIED)
        self.assertFalse(parsed["coverage_allowed"])
        self.assertFalse(parsed["indexable"])
        self.assertIn("denied_product_url", {flag["kind"] for flag in parsed["flags"]})

    def test_caution_is_not_stored_as_a_disease_claim(self):
        html = (
            "<h1>Where to buy NMN</h1>"
            "<p>Treats diabetes is a medical promise that should make you leave.</p>"
            "<p>This capsule treats diabetes.</p>"
            "<p>The product page does not show a certificate of analysis.</p>"
            "<p>Padding sentence about the label lines and the bottle count only.</p>"
            "<p>Every batch is third-party tested for identity.</p>"
        )
        parsed = gap.extract_page(html, ARTICLE)
        disease = [flag["excerpt"] for flag in parsed["flags"] if flag["kind"] == "disease"]
        proof = [flag["excerpt"] for flag in parsed["flags"] if flag["kind"] == "clinical_proof"]
        self.assertEqual(len(disease), 1)
        self.assertIn("This capsule treats diabetes", disease[0])
        self.assertTrue(any("third-party tested" in item for item in proof))
        self.assertFalse(any("certificate of analysis" in item.lower() for item in proof))

    def test_protocol_page_does_not_count_as_nmn_coverage(self):
        html = (
            "<h1>The Complete AgeAura Longevity Protocol</h1>"
            "<h3>Pure Urolithin A</h3>"
            "<h2>Can you take NMN and TMG at the same time?</h2>"
            "<p>500 mg Urolithin A and longevity peptides.</p>"
        )
        url = "https://wellnessnest.co/pages/ageaura-protocol-2"
        self.assertTrue(gap.coverage_allowed(url))
        self.assertTrue(gap.coverage_allowed(
            "https://wellnessnest.co/pages/ageaura-pure-protocol"
        ))
        parsed = gap.extract_page(html, url)
        self.assertFalse(parsed["indexable"])
        self.assertIn("different AgeAura product", gap.ineligible_reason(parsed))
        row = gap.classify_query({
            "id": "same-time",
            "query": "Can you take NMN and TMG at the same time?",
            "pillar": "pairing",
            "branch": "together",
            "label": "hypothesised follow-up",
            "cover": [["same time"]],
            "partial": [],
            "related": [],
            "home_urls": [ARTICLE],
            "gap_action": "add_h2",
            "suggested_heading": "Can you take NMN and TMG at the same time?",
            "evidence_boundary": "label",
            "priority": 1,
        }, [parsed])
        self.assertNotEqual(row["status"], "COVERED")
        self.assertIn("different AgeAura product", row["reason"])

    def test_link_before_the_article_h1_is_ignored(self):
        html = (
            '<a href="/products/ageaura-pure-nmn-tmg-p2">nav</a>'
            "<h1>NMN and TMG</h1><p>No milligram here.</p>"
        )
        parsed = gap.extract_page(html, ARTICLE)
        self.assertEqual(parsed["product_links"], [])
        self.assertFalse(any(flag["kind"] == "denied_product_link" for flag in parsed["flags"]))


class Classify(unittest.TestCase):
    def setUp(self):
        self.pages = [
            page(PDP, [h("h1", "AgeAura Pure NMN + TMG NAD+ Complex"), h("h2", "Ingredients")]),
            page(ARTICLE, [
                h("h1", "NMN and TMG Together"),
                h("h3", "Can you take NMN and TMG at the same time?"),
            ]),
            page(DOSE, [h("h1", "NMN TMG dosage: how much per day")]),
            page(DENIED, [h("h2", "Can you take NMN and TMG at the same time?")], indexable=False),
        ]

    def test_covered_uses_the_home_page_when_both_match(self):
        query = {
            "id": "same-time",
            "query": "Can you take NMN and TMG at the same time?",
            "branch": "together",
            "pillar": "pairing",
            "label": "hypothesised follow-up",
            "cover": [["same time"]],
            "partial": [["nmn and tmg"]],
            "home_urls": [ARTICLE, PDP],
            "gap_action": "add_h2",
            "suggested_heading": "Can you take NMN and TMG at the same time?",
            "evidence_boundary": "label only",
            "priority": 1,
        }
        row = gap.classify_query(query, self.pages)
        self.assertEqual(row["status"], "COVERED")
        self.assertEqual(row["page_url"], ARTICLE)
        self.assertEqual(row["action"], "none")
        self.assertNotEqual(row["page_url"], DENIED)

    def test_partial_names_the_page_that_should_gain_an_h2(self):
        query = {
            "id": "empty",
            "query": "Can you take NMN and TMG on an empty stomach?",
            "branch": "timing",
            "pillar": "timing",
            "label": "hypothesised follow-up",
            "cover": [["empty stomach"]],
            "partial": [["how much"], ["dosage"]],
            "home_urls": [DOSE, ARTICLE],
            "gap_action": "add_h2",
            "suggested_heading": "Does the label say to take it on an empty stomach?",
            "evidence_boundary": "Do not invent a number.",
            "priority": 2,
        }
        row = gap.classify_query(query, self.pages)
        self.assertEqual(row["status"], "PARTIAL")
        self.assertEqual(row["action"], "add_h2")
        self.assertEqual(row["page_url"], DOSE)
        self.assertIn("empty stomach", row["suggested_heading"])

    def test_gap_add_h2_points_at_the_home_url(self):
        query = {
            "id": "storage",
            "query": "How should you store the bottle?",
            "pillar": "pdp",
            "branch": "product",
            "label": "hypothesised follow-up",
            "cover": [["storage"], ["refrigerate"]],
            "partial": [],
            "home_urls": [PDP],
            "gap_action": "add_h2",
            "suggested_heading": "Does the label say how to store the bottle?",
            "evidence_boundary": "Do not invent a shelf life.",
            "priority": 3,
            "decision_reason": "",
        }
        row = gap.classify_query(query, self.pages)
        self.assertEqual(row["status"], "GAP")
        self.assertEqual(row["action"], "add_h2")
        self.assertEqual(row["page_url"], PDP)

    def test_gap_reject_and_new_article(self):
        rejected = gap.classify_query({
            "id": "reddit",
            "query": "reddit reviews",
            "pillar": "pdp",
            "branch": "buy",
            "label": "hypothesised follow-up",
            "cover": [["reddit"]],
            "partial": [],
            "home_urls": [],
            "gap_action": "reject_thin",
            "suggested_heading": "",
            "evidence_boundary": "",
            "priority": 9,
            "decision_reason": "Thin fan-out page. Do not create one.",
        }, self.pages)
        self.assertEqual(rejected["status"], "GAP")
        self.assertEqual(rejected["action"], "reject_thin")
        fresh = gap.classify_query({
            "id": "new",
            "query": "A distinct buyer job with its own evidence file",
            "pillar": "pdp",
            "branch": "product",
            "label": "hypothesised follow-up",
            "cover": [["evidence file"]],
            "partial": [],
            "home_urls": [],
            "gap_action": "new_article",
            "suggested_heading": "",
            "evidence_boundary": "",
            "priority": 9,
            "decision_reason": "This fixture is the only case that earns its own URL because no pillar exists.",
            "justification": "This fixture is the only case that earns its own URL because no pillar exists.",
        }, self.pages)
        self.assertEqual(fresh["action"], "new_article")
        counts = gap.summarize([rejected, fresh])
        self.assertEqual(counts["GAP"], 2)
        self.assertEqual(counts["reject_thin"], 1)
        self.assertEqual(counts["new_article"], 1)
        self.assertEqual(counts["add_h2"], 0)

    def test_related_heading_does_not_turn_a_thin_url_into_an_addition(self):
        buy = page(
            "https://wellnessnest.co/blogs/news/where-to-buy-nmn-in-the-us-fda-status-explained-2026",
            [h("h3", "Why did Amazon stop selling NMN?")],
        )
        row = gap.classify_query({
            "id": "amazon",
            "query": "Is AgeAura NMN sold on Amazon?",
            "pillar": "buy",
            "branch": "buy",
            "label": "hypothesised follow-up",
            "cover": [["ageaura", "amazon"]],
            "partial": [],
            "related": [["amazon"]],
            "home_urls": [],
            "gap_action": "reject_thin",
            "suggested_heading": "",
            "evidence_boundary": "",
            "priority": 80,
            "decision_reason": "A marketplace URL is a thin fan-out page.",
        }, [buy])
        self.assertEqual(row["status"], "GAP")
        self.assertEqual(row["action"], "reject_thin")
        self.assertIn("Why did Amazon stop selling NMN?", row["reason"])
        self.assertNotIn("Add an H2", row["reason"])

    def test_noindex_heading_does_not_count_as_covered(self):
        hidden = page(ARTICLE, [h("h2", "Empty stomach rules")], noindex=True, indexable=False)
        query = {
            "id": "empty",
            "query": "empty stomach",
            "pillar": "timing",
            "branch": "timing",
            "label": "hypothesised follow-up",
            "cover": [["empty stomach"]],
            "partial": [],
            "home_urls": [PDP],
            "gap_action": "add_h2",
            "suggested_heading": "Does the label mention an empty stomach?",
            "evidence_boundary": "absence",
            "priority": 1,
        }
        row = gap.classify_query(query, [hidden])
        self.assertEqual(row["status"], "GAP")
        self.assertIn("noindex", row["reason"])


class SeedFile(unittest.TestCase):
    def test_real_seed_lints(self):
        with open(SEED_PATH, encoding="utf-8") as handle:
            seed = json.load(handle)
        self.assertEqual(gap.lint_seed(seed), [])
        self.assertGreaterEqual(len(seed["queries"]), 30)
        self.assertLessEqual(len(seed["queries"]), 60)
        actions = {query["gap_action"] for query in seed["queries"]}
        self.assertIn("add_h2", actions)
        self.assertIn("reject_thin", actions)
        self.assertNotIn("new_article", actions)
        for query in seed["queries"]:
            self.assertEqual(query["label"], "hypothesised follow-up")
            self.assertNotIn("volume", json.dumps(query).lower())


class CrawlFixture(unittest.TestCase):
    def test_sitemap_filter_and_budget_and_backoff(self):
        index = """<?xml version="1.0"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <sitemap><loc>https://wellnessnest.co/sitemap_articles_1.xml</loc></sitemap>
          <sitemap><loc>https://wellnessnest.co/fr/sitemap_articles_1.xml</loc></sitemap>
        </sitemapindex>"""
        articles = """<?xml version="1.0"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://wellnessnest.co/blogs/news/nmn-and-tmg-together-why-the-pairing-matters-us-2026</loc></url>
          <url><loc>https://wellnessnest.co/blogs/news/creatine-gummies-unrelated</loc></url>
          <url><loc>%s</loc></url>
        </urlset>""" % DENIED
        html = b"<html><body><h1>NMN and TMG Together</h1><h2>Same time dosing</h2></body></html>"
        docs = {
            gap.ROBOTS_URL: (200, b"User-agent: *\nAllow: /\nSitemap: https://wellnessnest.co/sitemap.xml\n"),
            gap.SITEMAP_URL: (200, index.encode()),
            "https://wellnessnest.co/sitemap_articles_1.xml": (200, articles.encode()),
            ARTICLE: (200, html),
            DENIED: (200, html),
            PDP: (200, b"<html><body><h1>AgeAura Pure NMN + TMG NAD+ Complex</h1></body></html>"),
        }
        calls = []

        def request(url):
            calls.append(url.split("?", 1)[0])
            status, body = docs.get(url.split("?", 1)[0], (404, b""))
            return status, body, url, ""

        sleeps = []
        snapshot = gap.crawl(
            {"product_url": PDP},
            max_gets=20,
            delay=0.25,
            request_fn=request,
            sleep_fn=sleeps.append,
            log=lambda *_a: None,
        )
        urls = [item["url"] for item in snapshot["pages"]]
        self.assertIn(ARTICLE, urls)
        self.assertIn(PDP, urls)
        self.assertIn(DENIED, urls)
        self.assertNotIn("https://wellnessnest.co/blogs/news/creatine-gummies-unrelated", urls)
        self.assertNotIn("https://wellnessnest.co/fr/sitemap_articles_1.xml", calls)
        self.assertFalse(snapshot["incomplete"])
        self.assertLessEqual(snapshot["gets"], 20)
        self.assertGreaterEqual(len(sleeps), 1)
        self.assertEqual(sleeps[0], 0.25)

        state = {"gets": 0, "max_gets": 3, "delay": 0, "incomplete": False}
        first = {"n": 0}

        def flaky(url):
            first["n"] += 1
            if first["n"] == 1:
                return 429, b"", url, ""
            return 200, b"ok", url, ""

        waits = []
        got = gap.fetch_one(PDP, state, flaky, waits.append)
        self.assertEqual(got["status"], 200)
        self.assertEqual(waits, [5])
        self.assertEqual(state["gets"], 2)

        stopped = {"gets": 1, "max_gets": 1, "delay": 0, "incomplete": False}
        blocked = gap.fetch_one(PDP, stopped, flaky, lambda _s: None)
        self.assertEqual(blocked["error"], "budget")
        self.assertTrue(stopped["incomplete"])


class Report(unittest.TestCase):
    def test_report_labels_hypotheses_and_counts(self):
        with open(SEED_PATH, encoding="utf-8") as handle:
            seed = json.load(handle)
        rows = [
            {
                "id": "servings", "query": "How many capsules are in the bottle?",
                "branch": "product", "pillar": "pdp", "label": "hypothesised follow-up",
                "status": "PARTIAL", "page_url": PDP, "heading": "Ingredients",
                "heading_level": "h2", "action": "add_h2",
                "suggested_heading": "How many capsules and servings are on the bottle?",
                "evidence_boundary": "Repeat 60 Capsules and 30 Servings.",
                "priority": 1, "recheck": False,
                "reason": "The product page has Ingredients and not the count.",
            },
            {
                "id": "reddit", "query": "reddit reviews", "branch": "buy", "pillar": "pdp",
                "label": "hypothesised follow-up", "status": "GAP", "page_url": "",
                "heading": "", "heading_level": "", "action": "reject_thin",
                "suggested_heading": "", "evidence_boundary": "", "priority": 80,
                "recheck": False, "reason": "Thin fan-out page. Do not create one.",
            },
        ]
        # The renderer groups by the seed's pillar list, so trim to the rows we assert.
        seed = dict(seed)
        seed["pillars"] = [pillar for pillar in seed["pillars"] if pillar["id"] == "pdp"]
        crawl = {
            "fetched_at": "2026-10-20T11:00+07:00",
            "gets": 4,
            "max_gets": 200,
            "incomplete": False,
            "urls_selected": 2,
            "errors": [],
            "pages": [
                page(PDP, [h("h1", "AgeAura Pure NMN + TMG NAD+ Complex")], flags=[
                    {"kind": "milligram", "excerpt": "500 mg"},
                ]),
                page("https://wellnessnest.co/pages/nmn-after-40-research", [h("h1", "NMN after 40")]),
            ],
        }
        text = gap.render_report(seed, crawl, rows)
        self.assertIn("hypothesised", text.lower())
        self.assertIn("did not open Google AI Mode", text)
        self.assertIn("| COVERED | 0 |", text)
        self.assertIn("| PARTIAL | 1 |", text)
        self.assertIn("| GAP | 1 |", text)
        self.assertIn("How many capsules and servings are on the bottle?", text)
        self.assertIn("Thin fan-out page", text)
        self.assertIn("500 mg", text)
        self.assertNotIn("monthly searches", text)
        self.assertNotIn("AI Mode suggested", text)
        top, total = gap.additions_for(rows, "pdp", limit=10)
        self.assertEqual(total, 1)
        self.assertEqual(top[0]["id"], "servings")


if __name__ == "__main__":
    unittest.main()

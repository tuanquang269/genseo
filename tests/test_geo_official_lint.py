"""WARN-only GEO lint. These checks never become a publish gate."""
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import geo_official_lint as geo

SCRIPT = os.path.join(ROOT, "scripts", "geo_official_lint.py")
GUIDE = os.path.join(ROOT, "knowledge_base", "AEO_GEO_GUIDELINES.md")

# The 2026-10-09 gap-fill banned the substring outright so §6 would not recommend
# the refused AgeAura SKU. Later deny lines have to name that SKU. A mention is
# allowed only in the same sentence as a refusal or an absence, and not when that
# sentence also recommends it. A bare "never" or "do not" is not a refusal
# ("Do not forget Urolithin A" is still a recommendation).
_UROLITHIN = re.compile(r"urolithin", re.I)
_UROLITHIN_DENY = re.compile(
    r"\b(?:is|are)\s+refused\b(?!\s+by\s+(?:nobody|no one))"
    r"|\brefused by\b(?!\s+(?:nobody|no one))"
    r"|\bfail-closed\b"
    r"|\bno palette file\b"
    r"|\bdoes not unpublish\b",
    re.I,
)
_UROLITHIN_PROMO = re.compile(
    r"\b(?:buy|shop|order|supports?|benefits?|best|recommend(?:ed|s)?|ideal|helps?|hero)\b"
    r"|\blink(?:s|ed|ing)?\s+(?:only\s+)?to\b",
    re.I,
)
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-Z*`])|\n+")


def urolithin_promotions(text):
    """Sentences that name Urolithin outside a same-sentence deny or absence."""
    bad = []
    seen = 0
    for sentence in _SENTENCE_BREAK.split(text):
        sentence = " ".join(sentence.split())
        hits = _UROLITHIN.findall(sentence)
        if not sentence or not hits:
            continue
        seen += len(hits)
        if not _UROLITHIN_DENY.search(sentence) or _UROLITHIN_PROMO.search(sentence):
            bad.append(sentence)
    total = len(_UROLITHIN.findall(text))
    if seen != total:
        bad.append(f"splitter dropped urolithin mentions: saw {seen} of {total}")
    return bad

CLEAN = """# NMN and TMG

**NMN and TMG are listed together on the AgeAura Pure NMN + TMG label.** Order online; ships across the US.

A plain-language overview is on the [NIH Office of Dietary Supplements](https://ods.od.nih.gov/factsheets/list-all/).

![AgeAura NMN and TMG serving facts](images/ageaura-nmn-tmg-serving-facts.webp)
"""


def ids(text, title=""):
    return {item["rule"] for item in geo.lint(text, title)}


class CleanDraft(unittest.TestCase):
    def test_clean_markdown_has_no_warnings(self):
        self.assertEqual(ids(CLEAN), set())

    def test_documented_user_agents_are_quiet(self):
        text = CLEAN + (
            "\nLogs may show OAI-SearchBot/1.3, GPTBot/1.2, ChatGPT-User/1.0, "
            "or OAI-AdsBot/1.0. Claude-SearchBot and Claude-User have no published version.\n"
        )
        self.assertNotIn("invented-crawler-ua", ids(text))

    def test_negated_claims_are_quiet(self):
        text = CLEAN + (
            "\nThese supplements are not FDA-approved. "
            "Wellness Nest is not the best retailer. "
            "We do not offer same-day shipping or a physical store. "
            "Do not claim IndexNow is live. "
            "Do not say ChatGPT search uses Bing. "
            "Do not write that blocking Google-Extended removes AI Overviews. "
            "Do not add GrokBot or ClaudeBot/1.0. "
            "There is no ideal page length for AI. "
            "Do not add an onpopstate trap.\n"
        )
        found = ids(text)
        for rule in (
            "invented-credential", "unsupported-superlative", "unverified-store-claim",
            "indexnow-gsc-bing-live", "chatgpt-bing-index", "google-extended-blocks-search",
            "invented-crawler-ua", "chunk-for-ai", "back-button-hijack",
        ):
            self.assertNotIn(rule, found, rule)


class OfficialSourceWarnings(unittest.TestCase):
    def test_store_superlative_and_credential(self):
        text = CLEAN + (
            "\nWellness Nest is the best retailer. Visit our store for same-day shipping "
            "and curbside pickup. The formula is FDA-approved and clinically proven. "
            "It was freshly updated for this week.\n"
        )
        found = ids(text)
        self.assertIn("unsupported-superlative", found)
        self.assertIn("unverified-store-claim", found)
        self.assertIn("invented-credential", found)
        self.assertIn("fake-freshness", found)

    def test_back_reference_and_empty_alt(self):
        text = CLEAN + "\nAs mentioned above, the dose is on the label.\n![](images/ageaura-nmn-tmg-serving-facts.webp)\n"
        found = ids(text)
        self.assertIn("back-reference", found)
        self.assertIn("image-alt", found)

    def test_llms_txt_and_bing_and_google_extended(self):
        text = CLEAN + (
            "\nAdd an llms.txt file to rank in Google. "
            "ChatGPT search uses Bing's index. "
            "Blocking Google-Extended removes AI Overviews.\n"
        )
        found = ids(text)
        self.assertIn("llms-txt-ranking", found)
        self.assertIn("chatgpt-bing-index", found)
        self.assertIn("google-extended-blocks-search", found)

    def test_invented_crawlers_and_live_claims(self):
        text = CLEAN + (
            "\nBlock GrokBot and xAI-Bot in robots.txt. "
            "Allow Claude-SearchBot/1.0 and ChatGPTBot. "
            "OAI-SearchBot/2.0 and ChatGPT-User/1.2 are the tokens. "
            "IndexNow is live and Google Search Console is verified. "
            "Wellness Nest submitted the sitemap to Bing Webmaster.\n"
        )
        found = ids(text)
        self.assertIn("invented-crawler-ua", found)
        self.assertIn("indexnow-gsc-bing-live", found)

    def test_chunking_back_button_and_captcha(self):
        text = CLEAN + (
            "\nWe chunked this article for AI. The ideal page length for AI Overviews is 800 words.\n"
            "<script>window.onpopstate = function () { location.href = '/offer'; }</script>\n"
            "<div class=\"g-recaptcha\" data-sitekey=\"x\"></div>\n"
        )
        found = ids(text)
        self.assertIn("chunk-for-ai", found)
        self.assertIn("back-button-hijack", found)
        self.assertIn("bot-challenge", found)

    def test_generic_filename(self):
        text = CLEAN + "\n![AgeAura NMN and TMG label](images/IMG_1234.jpg)\n"
        self.assertIn("generic-image-filename", ids(text))
        self.assertNotIn("generic-image-filename", ids(CLEAN))

    def test_schema_dates_reviews_and_sale_window(self):
        bad = CLEAN + """
Published: October 8, 2026
Last updated: October 9, 2026
<script type="application/ld+json">
{"@type":"Article","datePublished":"2026-01-01","dateModified":"2026-01-02","aggregateRating":{"@type":"AggregateRating","reviewCount":"9"},"priceValidUntil":"2026-12-01"}
</script>
<script type="application/ld+json">
{"@type":"BlogPosting","headline":"second"}
</script>
"""
        found = ids(bad)
        self.assertIn("date-mismatch", found)
        self.assertIn("schema-review-not-visible", found)
        self.assertIn("sale-window-unmarked", found)
        self.assertIn("duplicate-article-schema", found)

        good = CLEAN + """
Published: 2026-10-08
Last updated: October 9, 2026
This on sale price is backed by 12 visible reviews.
<script type="application/ld+json">
{"@type":"Article","datePublished":"2026-10-08","dateModified":"2026-10-09","priceValidUntil":"2026-12-01"}
</script>
"""
        quiet = ids(good)
        self.assertNotIn("date-mismatch", quiet)
        self.assertNotIn("schema-review-not-visible", quiet)
        self.assertNotIn("sale-window-unmarked", quiet)
        self.assertNotIn("duplicate-article-schema", quiet)

    def test_stale_title_year(self):
        old = date.today().year - 1
        self.assertIn("stale-title-year", ids(CLEAN, title=f"NMN guide {old}"))
        self.assertNotIn("stale-title-year", ids(CLEAN, title=f"NMN guide {date.today().year}"))


class GuidelinesAndCli(unittest.TestCase):
    def test_guidelines_cite_the_gap_fill(self):
        with open(GUIDE, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("Rules 20–39", text)
        self.assertIn("### 6.6 Crawlers, user agents, and robots.txt (2026-10-09)", text)
        self.assertIn("### 6.7 Citation patterns (2026-10-09)", text)
        self.assertIn("### 6.8 Structured data and llms.txt (2026-10-09)", text)
        self.assertIn("### 6.9 What not to change without a Kevin GO (2026-10-09)", text)
        self.assertIn("geo-official-digest-2026-10-08.md", text)
        self.assertIn("https://developers.openai.com/api/docs/bots", text)
        self.assertIn("https://docs.x.ai/developers/tools/citations", text)
        self.assertIn("https://privacy.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler", text)
        self.assertIn("https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec", text)
        self.assertIn("https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex", text)
        self.assertIn("Bacillus coagulans SNZ-1969", text)
        self.assertIn("1 billion CFU", text)
        self.assertIn(
            "`ageaura-pure-urolithin-a` and any other Urolithin A AgeAura handle are refused",
            text,
        )
        self.assertIn("does not unpublish the live Urolithin PDP", text)
        self.assertIn("AgeAura Urolithin has no palette file", text)
        self.assertEqual(urolithin_promotions(text), [])
        for number in range(20, 40):
            self.assertIn(f"{number}. **2026-10-09", text)

    def test_urolithin_deny_is_allowed_and_a_recommendation_is_not(self):
        denied = (
            "`ageaura-pure-urolithin-a` and any other Urolithin A AgeAura handle are refused "
            "by `scripts/ageaura_rules.py`.\n"
            "This guard does not unpublish the live Urolithin PDP.\n"
            "AgeAura Urolithin has no palette file.\n"
        )
        self.assertEqual(urolithin_promotions(denied), [])
        recommendations = (
            "AgeAura Urolithin A supports healthy aging.",
            "The hero product is /products/ageaura-pure-urolithin-a.",
            "Do not forget Urolithin A for muscle recovery.",
            "Urolithin A is never a bad choice.",
            "Shop Urolithin A. The peptide SKU is refused.",
            "Urolithin A is refused by nobody and is the best AgeAura product.",
            "AgeAura links only to the Urolithin PDP.",
        )
        for sample in recommendations:
            self.assertTrue(urolithin_promotions(sample), sample)

    def test_guidelines_do_not_trip_new_claim_rules(self):
        with open(GUIDE, encoding="utf-8") as fh:
            text = fh.read()
        found = ids(text)
        allowed = {"back-reference", "no-primary-source"}
        self.assertTrue(found <= allowed, sorted(found - allowed))

    def test_cli_is_warn_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "draft.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(CLEAN + "\nChatGPT search uses Bing's index.\n")
            help_run = subprocess.run([sys.executable, SCRIPT, "--help"], capture_output=True, text=True)
            self.assertEqual(help_run.returncode, 0)
            missing = subprocess.run([sys.executable, SCRIPT, os.path.join(tmp, "missing.md")],
                                     capture_output=True, text=True)
            self.assertEqual(missing.returncode, 0)
            self.assertIn("skipped", missing.stdout)
            warned = subprocess.run([sys.executable, SCRIPT, path, "--json"], capture_output=True, text=True)
            self.assertEqual(warned.returncode, 0)
            payload = json.loads(warned.stdout)
            bing = [item for item in payload["warnings"] if item["rule"] == "chatgpt-bing-index"]
            self.assertEqual(len(bing), 1)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(geo.main(["geo_official_lint.py", path]), 0)
            self.assertIn("WARN-only", buf.getvalue())


if __name__ == "__main__":
    unittest.main()

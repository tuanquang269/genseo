"""Citability gate. These checks fail a draft; they do not fetch the network."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import geo_citability as geo
import geo_official_lint

OPENING = (
    "Creatine gummies on rest days still belong in a US routine because muscle creatine stores "
    "stay elevated only when the labeled serving continues between workouts and skipping those "
    "days lets stores fall back toward baseline for many adults who train three days a week. "
    "Use the serving printed on the product you bought rather than a loading number copied from a forum."
)
META = (
    "Creatine gummies on rest days in the US: keep the labeled serving, what a trial compared, "
    "and how FusiForce lists that serving on the pouch."
)


def page(**overrides):
    body = {
        "opening": OPENING,
        "meta": META,
        "h2a": "Should you take creatine gummies on rest days?",
        "h2b": "How much creatine is on the FusiForce label?",
        "product": "https://wellnessnest.co/products/fusiforce-creatine-gummies",
        "related": "https://wellnessnest.co/blogs/news/creatine-gummies-loading-phase-is-it-needed-us-2026",
        "source": "https://pubmed.ncbi.nlm.nih.gov/29138605/",
        "alt": "FusiForce pouch on a kitchen counter beside a water glass",
        "extra": "",
    }
    body.update(overrides)
    return f"""<h1>Creatine gummies on rest days</h1>
<!-- meta_description: {body['meta']} -->
<p>{body['opening']}</p>
<h2>{body['h2a']}</h2>
<p>Yes. <a href="{body['source']}">A trial</a> kept the daily dose.</p>
<h2>{body['h2b']}</h2>
<p>Read <a href="{body['product']}">the product page</a>.</p>
<h2>Frequently Asked Questions</h2>
<h3>Do rest days change the serving?</h3>
<p>No.</p>
<h3>Can you skip a day in the US?</h3>
<p>Stores fall. See <a href="{body['related']}">the loading guide</a>.</p>
<h3>Where can you buy creatine gummies in the US?</h3>
<p>On the product page.</p>
<img alt="{body['alt']}" src="images/fusiforce-rest-day-counter.webp">
{body['extra']}
"""


class CleanDraft(unittest.TestCase):
    def test_word_and_meta_lengths_are_inside_the_band(self):
        self.assertGreaterEqual(len(OPENING.split()), 40)
        self.assertLessEqual(len(OPENING.split()), 70)
        self.assertGreaterEqual(len(META), 120)
        self.assertLessEqual(len(META), 165)

    def test_clean_html_has_no_citability_failures(self):
        fails, warns = geo.assess(page(), require_meta=True)
        self.assertEqual(fails, [], fails)
        self.assertEqual(warns, [])

    def test_meta_not_required_on_rendered_html(self):
        html = page().replace(f"<!-- meta_description: {META} -->", "")
        fails, _warns = geo.assess(html, require_meta=False)
        self.assertFalse(any("meta description" in f for f in fails))


class StructuralFailures(unittest.TestCase):
    def test_one_question_heading_fails(self):
        fails, _warns = geo.assess(page(h2b="Read the serving on the pouch"))
        self.assertTrue(any("question-style" in f for f in fails), fails)

    def test_short_answer_and_throat_clearing_fail(self):
        short = (
            "Creatine on rest days still matters for adults in the US who lift "
            "a few times a week and want a simple rule."
        )
        fails, _warns = geo.assess(page(opening=short))
        self.assertTrue(any("answer block" in f for f in fails), fails)
        throat = (
            "In this article we explain creatine gummies for readers in the US who train "
            "a few days a week and want a simple rest-day rule they can follow without "
            "copying a loading plan from a forum or a comment thread online today."
        )
        fails, _warns = geo.assess(page(opening=throat))
        self.assertTrue(any("throat-clearing" in f for f in fails), fails)

    def test_long_answer_warns(self):
        long = OPENING + " " + " ".join(["Extra"] * 20)
        _fails, warns = geo.assess(page(opening=long))
        self.assertTrue(any("answer block" in w for w in warns), warns)

    def test_missing_faq_product_related_and_source(self):
        html = page(
            product="https://example.com/not-a-product",
            related="https://example.com/not-an-article",
            source="https://example.com/blog/opinion",
        ).replace("<h2>Frequently Asked Questions</h2>", "<h2>More reading</h2>")
        html = html.replace("<h3>", "<h2>").replace("</h3>", "</h2>")
        fails, _warns = geo.assess(html, require_meta=True)
        joined = " ".join(fails)
        self.assertIn("FAQ heading", joined)
        self.assertIn("products/", joined)
        self.assertIn("blogs/news", joined)
        self.assertIn("primary-source", joined)

    def test_meta_length_and_published_line(self):
        fails, _warns = geo.assess(page(meta="Too short to be a snippet."), require_meta=True)
        self.assertTrue(any("meta description" in f for f in fails), fails)
        fails, _warns = geo.assess(
            page(extra="<p>Published: October 17, 2026. Educational only.</p>"),
            require_meta=True,
        )
        self.assertTrue(any("Published" in f for f in fails), fails)

    def test_weak_alt_fails_and_a_phrase_does_not(self):
        fails, _warns = geo.assess(page(alt="photo"), require_meta=True)
        self.assertTrue(any("alt" in f for f in fails), fails)
        fails, _warns = geo.assess(page(alt=""), require_meta=True)
        self.assertTrue(any("alt" in f for f in fails), fails)


class Compliance(unittest.TestCase):
    def test_affirmative_disease_and_approval_claims_fail(self):
        fails = geo.compliance_issues(
            "FloraFresh cures bacterial vaginosis. NMN is FDA-approved. "
            "The gummies are clinically proven. It delivers guaranteed results."
        )
        joined = " ".join(fails)
        self.assertIn("disease-cure", joined)
        self.assertIn("FDA-approval", joined)
        self.assertIn("clinically proven", joined)
        self.assertIn("guaranteed-result", joined)

    def test_negated_and_educational_claims_pass(self):
        text = (
            "No product with the same number will prevent, treat, or cure an infection. "
            "Do not use a supplement as a substitute for care that treats an infection. "
            "Treats diabetes or reverses aging is a medical promise, not a supplement claim. "
            "NMN is not FDA-approved. "
            "Does paying more make a supplement FDA-approved? "
            "If a retailer says FDA approved NMN, ask what that phrase means. "
            "These trials do not supply a guaranteed result."
        )
        self.assertEqual(geo.compliance_issues(text), [])


class Links(unittest.TestCase):
    def test_external_and_internal_urls(self):
        html = page(extra=(
            '<a href="https://www.facebook.com/sharer.php?u=1">share</a>'
            '<a href="https://doi.org/10.3390/nu14040755">doi</a>'
            '<a href="https://wellnessnest.co/blogs/news">index</a>'
            '<a href="https://wellnessnest.co/pages/mike-moretti">author</a>'
        ))
        external = geo.external_urls(html)
        self.assertIn("https://doi.org/10.3390/nu14040755", external)
        self.assertIn("https://pubmed.ncbi.nlm.nih.gov/29138605/", external)
        self.assertFalse(any("facebook.com" in u for u in external))
        self.assertFalse(any("wellnessnest.co" in u for u in external))
        internal = geo.internal_urls(html)
        self.assertIn(
            "https://wellnessnest.co/blogs/news/creatine-gummies-loading-phase-is-it-needed-us-2026",
            internal,
        )
        self.assertIn("https://wellnessnest.co/blogs/news", internal)
        self.assertIn("https://wellnessnest.co/pages/mike-moretti", internal)
        self.assertIn("https://wellnessnest.co/products/fusiforce-creatine-gummies", internal)

    def test_regulations_examine_and_usada_count_as_primary(self):
        for url in (
            "https://www.regulations.gov/document/FDA-2023-P-0872-2754",
            "https://examine.com/supplements/creatine/",
            "https://www.usada.org/dietary-supplements/athletes-need-know-ecdysteroids/",
            "https://doi.org/10.3390/nu14040755",
        ):
            self.assertTrue(geo.is_primary_source(url), url)
        self.assertFalse(geo.is_primary_source("https://www.flickr.com/photos/darkcurrent/15320196908"))

    def test_citation_status_classes(self):
        fails, warns = geo.citation_issues([
            ("https://www.usada.org/missing/", 404, False),
            ("https://doi.org/10.1000/example", 403, False),
            ("https://pubmed.ncbi.nlm.nih.gov/29138605/", 203, False),
            ("https://example.com/loop", 301, True),
            ("https://example.com/down", 500, False),
            ("https://example.com/timeout", 0, False),
        ])
        joined_f = " ".join(fails)
        joined_w = " ".join(warns)
        self.assertIn("404", joined_f)
        self.assertIn("redirect loop", joined_f)
        self.assertIn("500", joined_f)
        self.assertNotIn("403", joined_f)
        self.assertNotIn("203", joined_f)
        self.assertIn("403", joined_w)
        self.assertIn("HTTP 0", joined_w)

    def test_lint_accepts_an_fda_docket(self):
        text = "FDA docket: [the petition](https://www.regulations.gov/document/FDA-2023-P-0872-2754)\n"
        self.assertNotIn("no-primary-source", {item["rule"] for item in geo_official_lint.lint(text)})

    def test_validator_wires_the_gate(self):
        path = os.path.join(ROOT, "scripts", "validate_article.py")
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("geo_citability.assess", source)
        self.assertIn("geo_citability.citation_issues", source)
        self.assertIn("geo_citability.internal_urls", source)
        self.assertNotIn("len(t)>65", source)


class Prompts(unittest.TestCase):
    def test_writer_prompts_name_the_new_gate(self):
        for rel in (
            "skills/genseo-auto-publish/SKILL.md",
            "skills/genseo-content-writer/SKILL.md",
        ):
            with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("question-style", text.lower() if "auto-publish" in rel else text)
            self.assertIn("120–165", text)
            self.assertIn("Published:", text)
            self.assertIn("primary-source" if "auto-publish" in rel else "primary-source", text)


if __name__ == "__main__":
    unittest.main()

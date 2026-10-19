"""First-hand experience block. No network. Example rows never render."""
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import experience_block as exp
import florafresh_rules
import shockwave_rules


def article(product="florafresh-vaginal-probiotics-gummies", title="Do vaginal probiotics help in the US?", extra=""):
    return (
        "# %s\n\n"
        "<!-- meta_description: A US shopper note about the label. -->\n\n"
        "See https://wellnessnest.co/products/%s for the panel.\n\n"
        "## What should the label say?\n\n"
        "Read the serving on the pouch.\n%s"
    ) % (title, product, extra)


def good_row(**overrides):
    row = {
        "id": "fixture-review-1",
        "example": False,
        "product": "florafresh-vaginal-probiotics-gummies",
        "topic_tags": ["probiotics"],
        "quote": "The pouch arrived on time and the serving directions on the label were easy to find.",
        "attribution": "Fixture Reviewer",
        "source_type": "verified_review",
        "source_url": "https://reviews.example-source.test/quote-1",
        "source_id": "",
        "date": "2026-02-02",
        "usage_allowed": True,
        "consent": "fixture consent recorded 2026-02-02",
        "received_product": "purchased",
        "disclosure": "",
        "persona_handle": "",
    }
    row.update(overrides)
    return row


class Selection(unittest.TestCase):
    def test_no_quotes_omits_the_block(self):
        self.assertEqual(exp.render(article(), []), "")
        self.assertNotIn("First-hand", exp.render(article(), []))
        fails, warns = exp.audit(article(), [])
        self.assertEqual(fails, [])
        self.assertIn(exp.COVERAGE_WARN, warns)

    def test_example_flag_alone_blocks_a_complete_row(self):
        row = good_row(example=True, usage_allowed=True, received_product="free")
        self.assertEqual(exp.eligibility_problems(row), ["example"])
        self.assertEqual(exp.eligibility_problems(good_row(example="true")), ["example"])
        self.assertEqual(exp.select(article(), [row]), [])
        self.assertEqual(exp.render(article(), [row]), "")

    def test_shipped_catalog_is_examples_only(self):
        rows = exp.load_quotes()
        self.assertTrue(rows)
        self.assertEqual(exp.lint_catalog(rows), [])
        for row in rows:
            self.assertIs(row.get("example"), True, row.get("id"))
            self.assertIn("EXAMPLE SHAPE ONLY", row.get("quote") or "")
        flora = article()
        self.assertEqual(exp.select(flora, rows), [])
        self.assertEqual(exp.render(flora, rows), "")
        self.assertNotIn("Example entry", exp.render(flora, rows))

    def test_ineligible_rows_are_not_selected(self):
        missing_source = good_row(source_url="", source_id="")
        denied = good_row(usage_allowed=False)
        placeholder = good_row(source_url="https://example.com/not-a-review")
        string_flag = good_row(usage_allowed="true")
        urolithin = good_row(product="ageaura-pure-urolithin-a")
        no_consent = good_row(consent="")
        self.assertIn("source", exp.eligibility_problems(missing_source))
        self.assertIn("usage_allowed", exp.eligibility_problems(denied))
        self.assertIn("source_placeholder", exp.eligibility_problems(placeholder))
        self.assertIn("usage_allowed", exp.eligibility_problems(string_flag))
        self.assertIn("product_denied", exp.eligibility_problems(urolithin))
        self.assertIn("consent", exp.eligibility_problems(no_consent))
        self.assertEqual(exp.select(article(), [missing_source, denied, placeholder, urolithin]), [])

    def test_product_and_topic_must_both_match(self):
        row = good_row()
        self.assertEqual(exp.select(article(product="fusiforce-creatine-gummies"), [row]), [])
        other_topic = article(title="What is creatine monohydrate?")
        other_topic = other_topic.replace("## What should the label say?", "## What is a serving?")
        self.assertEqual(exp.select(other_topic, [row]), [])
        self.assertEqual(exp.select(article(), [row]), [row])

    def test_cap_is_two_newest_matching_quotes(self):
        older = good_row(id="fixture-old", date="2026-01-01")
        middle = good_row(id="fixture-mid", date="2026-02-02", source_url="https://reviews.example-source.test/quote-2")
        newest = good_row(id="fixture-new", date="2026-03-03", source_url="https://reviews.example-source.test/quote-3")
        picked = exp.select(article(), [older, newest, middle])
        self.assertEqual([row["id"] for row in picked], ["fixture-new", "fixture-mid"])
        rendered = exp.render(article(), [older, newest, middle])
        self.assertIn("fixture-new", rendered)
        self.assertIn("fixture-mid", rendered)
        self.assertNotIn("fixture-old", rendered)

    def test_staff_test_without_a_disclosure_is_ineligible(self):
        row = good_row(source_type="internal_staff_test", disclosure="", persona_handle="ada-example")
        self.assertIn("disclosure", exp.eligibility_problems(row))

    def test_free_product_renders_the_disclosure_line(self):
        row = good_row(source_type="creator_submission", received_product="free")
        block = exp.render(article(), [row])
        self.assertIn(exp.FREE_DISCLOSURE, block)
        self.assertIn("https://reviews.example-source.test/quote-1", block)
        self.assertIn("Fixture Reviewer", block)
        self.assertNotIn("★", block)
        self.assertNotIn("-star", block)
        fails, warns = exp.audit(article(extra="\n\n" + block), [row])
        self.assertEqual(fails, [], fails)
        self.assertEqual(warns, [])

    def test_purchased_row_does_not_invent_a_free_product_line(self):
        block = exp.render(article(), [good_row()])
        self.assertNotIn(exp.FREE_DISCLOSURE, block)

    def test_source_id_is_printed_when_there_is_no_url(self):
        row = good_row(source_url="", source_id="review-fixture-9")
        block = exp.render(article(), [row])
        self.assertIn("Source ID: review-fixture-9", block)
        self.assertNotIn("href=", block)
        fails, warns = exp.audit(article(extra="\n\n" + block), [row])
        self.assertEqual(fails, [], fails)
        self.assertEqual(warns, [])


class ClaimGate(unittest.TestCase):
    def test_disease_quote_is_rejected_by_the_article_gate(self):
        row = good_row(quote="This gummy cures bacterial vaginosis.")
        self.assertIn("claim_gate", exp.eligibility_problems(row))
        self.assertEqual(exp.select(article(), [row]), [])
        forced = exp.render_block([row])
        fails, _warns = exp.audit(article(extra="\n\n" + forced), [row])
        self.assertTrue(any("claim_gate" in fail for fail in fails), fails)

    def test_negated_disease_sentence_follows_the_article_gate(self):
        row = good_row(quote="These gummies do not cure bacterial vaginosis.")
        self.assertNotIn("claim_gate", exp.eligibility_problems(row))

    def test_brand_label_gate_rejects_a_sugar_free_florafresh_quote(self):
        row = good_row(quote="FloraFresh is sugar-free.")
        self.assertIn("claim_gate", exp.eligibility_problems(row))
        self.assertEqual(exp.select(article(), [row]), [])

    def test_selector_calls_the_citability_gate(self):
        row = good_row()
        with mock.patch.object(
            exp.geo_citability, "compliance_issues", return_value=["disease-cure claim: fixture"]
        ):
            self.assertIn("claim_gate", exp.eligibility_problems(row))
            self.assertEqual(exp.select(article(), [row]), [])


class Testimonials(unittest.TestCase):
    def test_star_rating_and_attributed_quote_fail_outside_the_block(self):
        fails, _warns = exp.audit(article(extra="\n\nReaders give it 5 stars.\n"), [])
        self.assertTrue(any("star rating" in fail for fail in fails), fails)
        line = (
            'Mina wrote "I take the gummies every morning and I tell my sister about the pouch." '
            "— Mina Cole"
        )
        fails, _warns = exp.audit(article(extra="\n\n" + line + "\n"), [])
        self.assertTrue(any("attributed testimonial" in fail for fail in fails), fails)

    def test_study_attribution_is_not_a_testimonial(self):
        line = (
            'The paper said "muscle creatine stores stayed higher when the daily serving continued." '
            "— Hultman"
        )
        fails, _warns = exp.audit(article(extra="\n\n" + line + "\n"), [])
        self.assertEqual(fails, [], fails)

    def test_markdown_blockquote_fails(self):
        fails, _warns = exp.audit(article(extra="\n\n> The label lists one strain.\n"), [])
        self.assertTrue(any("blockquote" in fail for fail in fails), fails)

    def test_personal_use_in_the_byline_fails(self):
        extra = (
            "\n\n### About the Author\n\n"
            "[Ada Example](/pages/ada-example) takes this product every morning.\n"
        )
        fails, _warns = exp.audit(article(extra=extra), [])
        self.assertTrue(any("Ada Example" in fail for fail in fails), fails)

    def test_personal_use_inside_an_evidence_quote_does_not_fail(self):
        row = good_row(quote="I tried the pouch and the label was easy to read.")
        block = exp.render(article(), [row])
        body = article(extra="\n\n" + block + "\n\n### About the Author\n\n[Ada Example](/pages/ada-example) covers label reading.\n")
        fails, warns = exp.audit(body, [row])
        self.assertEqual(fails, [], fails)
        self.assertEqual(warns, [])

    def test_rendered_quote_must_match_the_file_and_keep_its_source(self):
        row = good_row()
        block = exp.render_block([row]).replace(
            "The pouch arrived on time and the serving directions on the label were easy to find.",
            "A different sentence that was not in the file.",
        )
        fails, _warns = exp.audit(article(extra="\n\n" + block), [row])
        self.assertTrue(any("does not match the evidence file" in fail for fail in fails), fails)
        stripped = exp.render_block([row]).replace('href="https://reviews.example-source.test/quote-1"', 'href="https://reviews.example-source.test/other"')
        fails, _warns = exp.audit(article(extra="\n\n" + stripped), [row])
        self.assertTrue(any("source URL" in fail for fail in fails), fails)

    def test_missing_free_disclosure_fails(self):
        row = good_row(source_type="creator_submission", received_product="free")
        block = exp.render_block([row]).replace(exp.FREE_DISCLOSURE, "Thanks for reading")
        fails, _warns = exp.audit(article(extra="\n\n" + block), [row])
        self.assertTrue(any("disclosure" in fail for fail in fails), fails)

    def test_three_rendered_quotes_fail_the_cap(self):
        rows = [
            good_row(id="fixture-a", date="2026-03-03", source_url="https://reviews.example-source.test/a"),
            good_row(id="fixture-b", date="2026-02-02", source_url="https://reviews.example-source.test/b"),
            good_row(id="fixture-c", date="2026-01-01", source_url="https://reviews.example-source.test/c"),
        ]
        block = exp.render_block(rows)
        fails, _warns = exp.audit(article(extra="\n\n" + block), rows)
        self.assertTrue(any("cap" in fail for fail in fails), fails)


class MethodLine(unittest.TestCase):
    def test_florafresh_names_the_label_check_the_gate_runs(self):
        line = exp.method_line(article())
        self.assertIn("scripts/florafresh_rules.py", line)
        self.assertIn(florafresh_rules.PRODUCT_NAME, line)
        self.assertIn("not a personal trial", line)
        self.assertNotIn("1 billion", line)

    def test_shockwave_names_its_pack_label_file(self):
        body = article(
            product=shockwave_rules.HANDLE,
            title="What is Shilajit Shockwave?",
        )
        line = exp.method_line(body)
        self.assertIn(shockwave_rules.LABEL_REL, line)
        self.assertIn("not a personal trial", line)

    def test_products_the_article_gate_does_not_label_check_stay_quiet(self):
        for handle, title in (
            ("fusiforce-creatine-gummies", "Do creatine gummies belong on rest days?"),
            ("ageaura-pure-nmn-tmg-nad-complex", "What is NMN with TMG?"),
            ("premium-himalayan-shilajit-gummies", "What is in shilajit gummies?"),
        ):
            self.assertEqual(exp.method_line(article(product=handle, title=title)), "", handle)

    def test_method_line_does_not_replace_a_missing_quote_block(self):
        rendered = exp.render(article(), [], with_method=True)
        self.assertIn("data-gs-experience=\"method\"", rendered)
        self.assertNotIn("data-gs-experience=\"quote\"", rendered)
        fails, warns = exp.audit(article(extra="\n\n" + rendered), [])
        self.assertEqual(fails, [], fails)
        self.assertIn(exp.COVERAGE_WARN, warns)

    def test_hand_written_method_line_fails(self):
        fails, _warns = exp.audit(
            article(extra="\n\nHow we checked this: we tried the pouch at home.\n"),
            [],
        )
        self.assertTrue(any("How we checked this" in fail for fail in fails), fails)

    def test_fusiforce_does_not_accept_a_florafresh_method_sentence(self):
        body = article(product="fusiforce-creatine-gummies", title="Do creatine gummies belong on rest days?")
        pasted = exp.render_method(article())
        fails, _warns = exp.audit(body + "\n\n" + pasted, [])
        self.assertTrue(fails, fails)


class Wiring(unittest.TestCase):
    def test_validator_and_publisher_call_the_audit_before_a_write(self):
        with open(os.path.join(ROOT, "scripts", "validate_article.py"), encoding="utf-8") as fh:
            validator = fh.read()
        self.assertIn("experience_block.audit", validator)
        with open(os.path.join(ROOT, "scripts", "shopify_publisher.py"), encoding="utf-8") as fh:
            publisher = fh.read()
        publish = publisher.split("def do_publish", 1)[1].split("def do_update", 1)[0]
        update = publisher.split("def do_update", 1)[1]
        self.assertLess(publish.index("_refuse_experience_block("), publish.index("_process_images_for_publish("))
        self.assertLess(
            update.index("_refuse_experience_block("),
            update.index("articles/{article_id}.json?fields=title"),
        )

    def test_writer_docs_forbid_invented_quotes(self):
        for rel in (
            "skills/genseo-auto-publish/SKILL.md",
            "docs/first-hand-experience-block.md",
            "skills/genseo-auto-publish/references/article-templates.md",
        ):
            with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("experience_block.py", text, rel)
            self.assertIn("usage_allowed", text, rel)

    def test_cli_render_is_empty_and_lint_passes(self):
        script = os.path.join(ROOT, "scripts", "experience_block.py")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "draft.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(article())
            rendered = subprocess.run(
                [sys.executable, script, "render", "--draft", path],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            self.assertEqual(rendered.stdout, "")
            audited = subprocess.run(
                [sys.executable, script, "audit", "--draft", path],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(audited.returncode, 0, audited.stdout)
            self.assertIn("experience coverage", audited.stdout)
        linted = subprocess.run(
            [sys.executable, script, "lint"],
            capture_output=True, text=True, check=False, cwd=ROOT,
        )
        self.assertEqual(linted.returncode, 0, linted.stdout)
        self.assertIn("0 renderable", linted.stdout)

    def test_markdown_extra_keeps_the_quote_block(self):
        try:
            import markdown
        except ImportError:
            self.skipTest("markdown is not installed")
        row = good_row()
        source = article() + "\n\n" + exp.render_block([row]) + "\n"
        html = markdown.markdown(source, extensions=["extra"])
        self.assertIn('data-gs-experience="quote"', html)
        self.assertIn('data-gs-quote-id="fixture-review-1"', html)
        self.assertIn(row["quote"], html)
        self.assertIn(row["source_url"], html)
        fails, _warns = exp.audit(html, [row])
        self.assertEqual(fails, [], fails)


if __name__ == "__main__":
    unittest.main()

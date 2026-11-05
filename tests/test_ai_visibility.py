"""Mention vs citation ledger. No network. Fixtures are shapes, not live captures."""
import contextlib
import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import aeo_tracker
import ai_visibility
import geo_citability

SCRIPT = os.path.join(ROOT, "scripts", "aeo_tracker.py")
PY = sys.executable
SECRET_KEYS = (
    "GEMINI_API_KEY", "OPENAI_API_KEY", "PERPLEXITY_API_KEY", "XAI_API_KEY",
    "OPENAI_VISIBILITY_MODEL", "PERPLEXITY_MODEL", "XAI_VISIBILITY_MODEL",
    "GEMINI_VISIBILITY_MODEL",
)


def catalog():
    return ai_visibility.load_catalog()


def first_prompt(brand_id):
    return ai_visibility.prompts_for(catalog(), brand_id)[0]


def quiet_env():
    env = os.environ.copy()
    for key in SECRET_KEYS:
        env.pop(key, None)
    return env


def valid_row(**overrides):
    row = {
        "brand_id": "ageaura",
        "prompt_id": first_prompt("ageaura")["id"],
        "platform": "chatgpt",
        "observed": True,
        "brand_mentioned": "yes",
        "mention_snippet": "AgeAura Pure NMN came up in the answer.",
        "store_mentioned": "no",
        "store_snippet": "",
        "domain_cited": "no",
        "cited_url": "",
        "competitors": [],
        "observer": "Kevin",
        "observed_at": "2026-10-20",
        "notes": "fixture",
    }
    row.update(overrides)
    return row


def errors_for(**overrides):
    return ai_visibility.validate_ledger({"schema": 1, "observations": [valid_row(**overrides)]})


class PromptSet(unittest.TestCase):
    def test_size_and_status(self):
        data = catalog()
        self.assertEqual(len(data["prompts"]), 51)
        self.assertEqual(len(data["platforms"]), 6)
        self.assertEqual(
            [item["id"] for item in data["platforms"]],
            ["chatgpt", "gemini", "google_ai_mode", "ai_overviews", "perplexity", "grok"],
        )
        self.assertEqual({prompt["prompt_status"] for prompt in data["prompts"]}, {"hypothesised"})
        self.assertFalse(any("urolithin" in prompt["text"].lower() for prompt in data["prompts"]))

    def test_frozen_queries_match_pr75(self):
        data = catalog()
        age = tuple(prompt["text"] for prompt in data["prompts"] if prompt["brand_id"] == "ageaura")
        shila = tuple(prompt["text"] for prompt in data["prompts"] if prompt["brand_id"] == "shilasource")
        self.assertEqual(age, ai_visibility.AGEAURA_QUERIES)
        self.assertEqual(shila, ai_visibility.SHILASOURCE_QUERIES)
        self.assertEqual(len(age), 18)
        self.assertEqual(len(shila), 18)

    def test_florafresh_primaries_match_the_topic_bank(self):
        problems = ai_visibility.florafresh_bank_problems(catalog())
        self.assertEqual(problems, [])
        flora = [prompt for prompt in catalog()["prompts"] if prompt["brand_id"] == "florafresh"]
        self.assertEqual(len(flora), 15)
        self.assertTrue(any(prompt.get("paste_caution") for prompt in flora))

    def test_competitor_patterns_match_pr75_counts(self):
        patterns = ai_visibility.load_patterns()
        self.assertEqual(sum(1 for item in patterns if item["brand_id"] == "ageaura"), 32)
        self.assertEqual(sum(1 for item in patterns if item["brand_id"] == "shilasource"), 25)
        self.assertFalse(any(item["brand_id"] == "florafresh" for item in patterns))

    def test_shipped_ledger_has_no_observations(self):
        ledger = ai_visibility.load_ledger(ai_visibility.LEDGER_PATH)
        self.assertEqual(ledger["observations"], [])

    def test_offpage_seed_drift_is_quiet_when_the_files_are_absent(self):
        self.assertFalse(os.path.isdir(ai_visibility.OFFPAGE_SEED_DIR))
        self.assertEqual(ai_visibility.offpage_drift(catalog(), ai_visibility.OFFPAGE_SEED_DIR), [])

    def test_offpage_seed_drift_flags_a_changed_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "ageaura.json"), "w", encoding="utf-8") as handle:
                json.dump({"queries": ["different prompt"]}, handle)
            problems = ai_visibility.offpage_drift(catalog(), tmp)
        self.assertTrue(any("ageaura.json" in item for item in problems))


class Validator(unittest.TestCase):
    def test_blank_template_validates(self):
        doc = ai_visibility.template_document()
        self.assertEqual(len(doc["observations"]), 306)
        self.assertEqual(ai_visibility.validate_ledger(doc), [])
        self.assertTrue(all(row["observed"] is False for row in doc["observations"]))
        self.assertTrue(all(row["brand_mentioned"] == "unknown" for row in doc["observations"]))
        self.assertTrue(all(row["domain_cited"] == "unknown" for row in doc["observations"]))
        self.assertTrue(all(row["competitors"] == [] for row in doc["observations"]))

    def test_valid_disagreement_rows(self):
        cited = valid_row(
            brand_mentioned="no",
            mention_snippet="",
            domain_cited="yes",
            cited_url="https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex",
        )
        self.assertEqual(ai_visibility.validate_ledger({"observations": [valid_row(), cited]}), [])

    def test_rejects_invented_shapes(self):
        self.assertTrue(errors_for(brand_mentioned="yes", mention_snippet=""))
        self.assertTrue(errors_for(mention_snippet="Urolithin A only"))
        self.assertTrue(errors_for(
            brand_mentioned="yes",
            mention_snippet="AgeAura Urolithin A is a different bottle.",
        ))
        self.assertTrue(errors_for(observed=False, brand_mentioned="yes"))
        self.assertTrue(errors_for(
            brand_mentioned="unknown", mention_snippet="",
            store_mentioned="unknown", domain_cited="unknown", observed=True,
        ))
        self.assertTrue(errors_for(domain_cited="yes", cited_url=""))
        self.assertTrue(errors_for(domain_cited="yes", cited_url="https://example.com/nmn"))
        self.assertTrue(errors_for(domain_cited="no", cited_url="https://wellnessnest.co/"))
        self.assertTrue(errors_for(domain_cited="unknown", source_urls=[]))
        self.assertTrue(errors_for(
            competitors=[{
                "name": "Tru Niagen",
                "mentioned": "yes",
                "mention_snippet": "Tru Niagen was named",
                "cited": "yes",
                "cited_url": "https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex",
            }]
        ))
        self.assertTrue(errors_for(brand_mentioned="no", mention_snippet="AgeAura was named"))
        self.assertTrue(errors_for(observer="", observed_at=""))

    def test_store_snippet_and_competitor_hit(self):
        row = valid_row(
            store_mentioned="yes",
            store_snippet="Wellness Nest ships the bottle.",
            competitors=[{
                "name": "Tru Niagen",
                "mentioned": "yes",
                "mention_snippet": "Tru Niagen was next to it.",
                "cited": "unknown",
                "cited_url": "",
            }],
        )
        self.assertEqual(ai_visibility.validate_ledger({"observations": [row]}), [])

    def test_csv_roundtrip(self):
        doc = ai_visibility.template_document()
        text = ai_visibility.rows_to_csv(doc["observations"])
        rows = ai_visibility.rows_from_csv(text)
        self.assertEqual(len(rows), 306)
        self.assertEqual(ai_visibility.validate_ledger({"observations": rows}), [])
        header = next(csv.reader(io.StringIO(text)))
        self.assertIn("domain_cited", header)
        self.assertIn("brand_mentioned", header)


class MatrixAndGaps(unittest.TestCase):
    def test_empty_ledger_is_all_unknown_and_has_no_gaps(self):
        data = catalog()
        matrix = ai_visibility.build_matrix(data, [])
        self.assertEqual(sum(cell["prompts"] for cell in matrix), 306)
        age_chatgpt = next(
            cell for cell in matrix
            if cell["brand_id"] == "ageaura" and cell["platform"] == "chatgpt"
        )
        self.assertEqual(age_chatgpt["mention_unknown"], 18)
        self.assertEqual(age_chatgpt["cite_unknown"], 18)
        self.assertEqual(age_chatgpt["mention_yes"], 0)
        self.assertEqual(age_chatgpt["mentioned_not_cited"], 0)
        gaps, notes, hits = ai_visibility.collect_gaps(data, [])
        self.assertEqual(gaps, [])
        self.assertEqual(notes, [])
        self.assertEqual(hits, [])

    def test_gap_kinds_and_fix_paths(self):
        data = catalog()
        mentioned = valid_row()
        cited = valid_row(
            prompt_id=ai_visibility.prompts_for(data, "ageaura")[1]["id"],
            platform="perplexity",
            brand_mentioned="no",
            mention_snippet="",
            domain_cited="yes",
            cited_url="https://wellnessnest.co/blogs/news/where-to-buy-nmn-in-the-us-fda-status-explained-2026",
        )
        unknown = valid_row(
            prompt_id=ai_visibility.prompts_for(data, "ageaura")[2]["id"],
            platform="gemini",
            brand_mentioned="yes",
            domain_cited="unknown",
        )
        gaps, _, _ = ai_visibility.collect_gaps(data, [mentioned, cited, unknown])
        kinds = {gap["prompt_id"]: gap["kind"] for gap in gaps}
        self.assertEqual(kinds[mentioned["prompt_id"]], "mentioned_not_cited")
        self.assertEqual(kinds[cited["prompt_id"]], "cited_not_mentioned")
        self.assertNotIn(unknown["prompt_id"], kinds)
        by_kind = {gap["kind"]: gap["fix"] for gap in gaps}
        self.assertIn("geo_citability.py", by_kind["mentioned_not_cited"])
        self.assertIn("question-style", by_kind["mentioned_not_cited"])
        self.assertIn("AgeAura Pure NMN + TMG NAD+ Complex", by_kind["cited_not_mentioned"])
        self.assertIn("Entity/brand", by_kind["cited_not_mentioned"])

    def test_blank_slot_does_not_double_count_and_yields_to_an_observation(self):
        data = catalog()
        prompt_id = first_prompt("ageaura")["id"]
        blank = ai_visibility.blank_row("ageaura", prompt_id, "chatgpt")
        matrix = ai_visibility.build_matrix(data, [blank])
        cell = next(item for item in matrix if item["brand_id"] == "ageaura" and item["platform"] == "chatgpt")
        self.assertEqual(cell["mention_unknown"], 18)
        observed = valid_row()
        matrix = ai_visibility.build_matrix(data, [blank, observed])
        cell = next(item for item in matrix if item["brand_id"] == "ageaura" and item["platform"] == "chatgpt")
        self.assertEqual(cell["mention_yes"], 1)
        self.assertEqual(cell["mention_unknown"], 17)
        self.assertEqual(cell["mentioned_not_cited"], 1)

    def test_store_named_without_the_product_brand(self):
        row = valid_row(
            brand_mentioned="no",
            mention_snippet="",
            store_mentioned="yes",
            store_snippet="Wellness Nest was the store name in the answer.",
            domain_cited="unknown",
        )
        _, notes, _ = ai_visibility.collect_gaps(catalog(), [row])
        self.assertEqual(len(notes), 1)
        self.assertEqual(ai_visibility.gap_kind(row), None)

    def test_citability_hint_uses_the_gate_language(self):
        fails, _warns = geo_citability.assess("<p>Short.</p><h2>Label</h2>")
        blob = " ".join(fails).lower()
        for needle in ("question-style", "faq", "products/", "blogs/news", "primary-source"):
            self.assertIn(needle, blob)
        self.assertIn("question-style", ai_visibility.CITABILITY_FIX)
        self.assertIn("primary-source", ai_visibility.CITABILITY_FIX)


class Classify(unittest.TestCase):
    def setUp(self):
        self.patterns = ai_visibility.load_patterns()

    def classify(self, text, sources=None, brand="ageaura"):
        return ai_visibility.classify_text_and_sources(text, sources, brand, self.patterns)

    def test_prose_url_is_not_a_citation(self):
        result = self.classify(
            "Buy it at https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex today.",
            None,
        )
        self.assertEqual(result["domain_cited"], "unknown")
        self.assertEqual(result["store_mentioned"], "yes")
        self.assertEqual(result["brand_mentioned"], "no")
        self.assertTrue(result["observed"])

    def test_gemini_text_without_grounding_leaves_citation_unknown(self):
        text, sources = ai_visibility.parse_gemini({
            "candidates": [{"content": {"parts": [{"text": "AgeAura Pure NMN is one option."}]}}]
        })
        result = self.classify(text, sources)
        self.assertEqual(result["brand_mentioned"], "yes")
        self.assertIn("AgeAura", result["mention_snippet"])
        self.assertEqual(result["domain_cited"], "unknown")
        self.assertIsNone(result["source_urls"])

    def test_grounding_without_our_domain_is_a_no(self):
        text, sources = ai_visibility.parse_gemini({
            "candidates": [{
                "content": {"parts": [{"text": "AgeAura Pure NMN is one option."}]},
                "groundingMetadata": {"groundingChunks": [{"web": {"uri": "https://example.com/nmn"}}]},
            }]
        })
        result = self.classify(text, sources)
        self.assertEqual(result["domain_cited"], "no")
        self.assertEqual(result["source_urls"], ["https://example.com/nmn"])

    def test_grounding_with_our_domain_is_a_yes(self):
        url = "https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex"
        text, sources = ai_visibility.parse_gemini({
            "candidates": [{
                "content": {"parts": [{"text": "Other brands only."}]},
                "groundingMetadata": {"groundingChunks": [{"web": {"uri": url}}]},
            }]
        })
        result = self.classify(text, sources)
        self.assertEqual(result["brand_mentioned"], "no")
        self.assertEqual(result["domain_cited"], "yes")
        self.assertEqual(result["cited_url"], url)

    def test_empty_source_list_is_a_no_and_a_missing_list_is_unknown(self):
        self.assertEqual(self.classify("AgeAura.", [])["domain_cited"], "no")
        self.assertEqual(self.classify("AgeAura.", None)["domain_cited"], "unknown")

    def test_urolithin_is_not_the_tracked_product(self):
        result = self.classify("AgeAura Urolithin A is a different bottle.")
        self.assertEqual(result["brand_mentioned"], "no")
        self.assertIn("Urolithin", result["notes"])

    def test_openai_url_citation_and_perplexity_and_grok_sources(self):
        url = "https://wellnessnest.co/products/florafresh-vaginal-probiotics-gummies"
        text, sources = ai_visibility.parse_openai({
            "output": [{
                "content": [{
                    "type": "output_text",
                    "text": "FloraFresh is one gummy.",
                    "annotations": [{"type": "url_citation", "url": url}],
                }]
            }]
        })
        flora = self.classify(text, sources, "florafresh")
        self.assertEqual(flora["brand_mentioned"], "yes")
        self.assertEqual(flora["domain_cited"], "yes")
        text, sources = ai_visibility.parse_chat_citations({
            "choices": [{"message": {"content": "No brand here."}}],
            "citations": ["https://example.com/a"],
        })
        self.assertEqual(self.classify(text, sources)["domain_cited"], "no")
        text, sources = ai_visibility.parse_chat_citations({
            "choices": [{"message": {"content": "See https://wellnessnest.co/products/x"}}],
        })
        grok = self.classify(text, sources, "shilasource")
        self.assertEqual(grok["domain_cited"], "unknown")
        self.assertEqual(grok["store_mentioned"], "yes")
        self.assertEqual(grok["brand_mentioned"], "no")

    def test_competitor_hits_are_mentions_only(self):
        result = self.classify(
            "Tru Niagen and Renue show up. For Youth the repair is a different line. For Youth alone is not the pattern.",
            ["https://example.com/nmn"],
        )
        names = {item["name"] for item in result["competitors"]}
        self.assertIn("Tru Niagen", names)
        self.assertIn("Renue By Science", names)
        self.assertIn("For Youth", names)
        self.assertTrue(all(item["cited"] == "unknown" for item in result["competitors"]))
        row = ai_visibility.observation_row(
            "ageaura", first_prompt("ageaura")["id"], "chatgpt", result, "Kevin", "2026-10-20",
        )
        self.assertEqual(ai_visibility.validate_ledger({"observations": [row]}), [])
        missed = self.classify("For Youth ships a bottle.", None)
        self.assertNotIn("For Youth", {item["name"] for item in missed["competitors"]})

    def test_shilasource_pattern_keeps_the_pr75_natural_shilajit_rule(self):
        hit = self.classify("Stock comes from naturalshilajit.com this week.", None, "shilasource")
        self.assertIn("Natural Shilajit", {item["name"] for item in hit["competitors"]})
        plain = self.classify("People say natural shilajit a lot.", None, "shilasource")
        self.assertNotIn("Natural Shilajit", {item["name"] for item in plain["competitors"]})

    def test_no_text_and_no_sources_stays_unobserved(self):
        result = self.classify(None, None)
        self.assertFalse(result["observed"])
        self.assertEqual(result["brand_mentioned"], "unknown")
        self.assertEqual(result["domain_cited"], "unknown")
        self.assertEqual(result["competitors"], [])


class Adapter(unittest.TestCase):
    def test_skip_without_a_key_does_not_call_transport(self):
        called = []

        def transport(_request):
            called.append(1)
            raise AssertionError("network")

        result = ai_visibility.run_adapter(
            "gemini", first_prompt("ageaura")["id"],
            env={}, transport=transport, confirm=True, today="2026-10-20",
        )
        self.assertEqual(result["status"], "skipped")
        self.assertIn("GEMINI_API_KEY", result["reason"])
        self.assertEqual(called, [])
        self.assertIsNone(result["observation"])

    def test_unconfirmed_adapt_does_not_call_transport(self):
        called = []

        def transport(_request):
            called.append(1)

        result = ai_visibility.run_adapter(
            "gemini", first_prompt("ageaura")["id"],
            env={"GEMINI_API_KEY": "test-key"}, transport=transport, confirm=False,
        )
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(called, [])

    def test_manual_platforms_skip(self):
        called = []
        result = ai_visibility.run_adapter(
            "ai_overviews", first_prompt("ageaura")["id"],
            env={"GEMINI_API_KEY": "test-key"},
            transport=lambda _request: called.append(1),
            confirm=True,
        )
        self.assertEqual(result["status"], "skipped")
        self.assertIn("no API", result["reason"])
        self.assertEqual(called, [])
        mode = ai_visibility.run_adapter(
            "google_ai_mode", first_prompt("shilasource")["id"],
            env={}, transport=lambda _request: called.append(1), confirm=True,
        )
        self.assertEqual(mode["status"], "skipped")

    def test_openai_without_a_model_does_not_guess(self):
        called = []
        result = ai_visibility.run_adapter(
            "chatgpt", first_prompt("florafresh")["id"],
            env={"OPENAI_API_KEY": "test-key"},
            transport=lambda _request: called.append(1),
            confirm=True,
        )
        self.assertEqual(result["status"], "skipped")
        self.assertIn("OPENAI_VISIBILITY_MODEL", result["reason"])
        self.assertEqual(called, [])

    def test_gemini_request_keeps_the_key_out_of_the_url_and_parses_a_fixture(self):
        request = ai_visibility.build_request(
            "gemini", "best NMN supplement", "test-key", ai_visibility.GEMINI_MODEL_DEFAULT
        )
        self.assertNotIn("test-key", request["url"])
        self.assertEqual(request["headers"]["x-goog-api-key"], "test-key")
        self.assertIn("gemini-1.5-flash", request["url"])
        self.assertEqual(request["body"]["tools"], [{"google_search": {}}])
        captured = []

        def transport(req):
            captured.append(req)
            return {"candidates": [{"content": {"parts": [{"text": "AgeAura Pure NMN is named."}]}}]}

        result = ai_visibility.run_adapter(
            "gemini", first_prompt("ageaura")["id"],
            env={"GEMINI_API_KEY": "test-key"}, transport=transport,
            confirm=True, today="2026-10-20",
        )
        self.assertEqual(result["status"], "ok")
        row = result["observation"]
        self.assertEqual(row["brand_mentioned"], "yes")
        self.assertEqual(row["domain_cited"], "unknown")
        self.assertEqual(row["observer"], "adapter:gemini")
        self.assertEqual(row["observed_at"], "2026-10-20")
        self.assertEqual(ai_visibility.validate_ledger({"observations": [row]}), [])
        self.assertEqual(captured[0]["url"], request["url"])

    def test_redact_strips_the_key(self):
        text = ai_visibility.redact("boom test-key in the message", {"GEMINI_API_KEY": "test-key"})
        self.assertNotIn("test-key", text)
        self.assertIn("[redacted]", text)

    def test_write_appends_only_a_valid_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "observations.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"schema": 1, "observations": []}, handle)

            def transport(_request):
                return {"candidates": [{"content": {"parts": [{"text": "AgeAura Pure NMN is named."}]}}]}

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = ai_visibility.main([
                    "adapt", "--platform", "gemini", "--prompt-id", first_prompt("ageaura")["id"],
                    "--write", "--ledger", path,
                ], env={"GEMINI_API_KEY": "test-key"}, transport=transport)
            self.assertEqual(code, 0, buf.getvalue())
            doc = ai_visibility.load_ledger(path)
            self.assertEqual(len(doc["observations"]), 1)
            self.assertEqual(doc["observations"][0]["domain_cited"], "unknown")


class LegacyScan(unittest.TestCase):
    def test_mock_mode_does_not_invent_a_score_or_call_the_network(self):
        called = []

        def boom(*_args, **_kwargs):
            called.append(1)
            raise RuntimeError("network")

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ticket.md")
            buf = io.StringIO()
            with mock.patch("urllib.request.urlopen", boom):
                with contextlib.redirect_stdout(buf):
                    aeo_tracker.run_aeo_scan("best NMN supplement", environ={}, ticket_path=path)
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            printed = buf.getvalue()
        self.assertEqual(called, [])
        self.assertIn("MOCK mode", printed)
        self.assertIn("GEMINI_API_KEY", printed)
        self.assertIn("brand_mentioned: unknown", text)
        self.assertIn("domain_cited: unknown", text)
        self.assertIn("observed: false", text)
        self.assertNotIn("1/5", text)
        self.assertNotIn("AI Overviews", text)
        self.assertNotIn("AI Overview", text)

    def test_observed_text_splits_mention_from_citation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ticket.md")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                aeo_tracker.run_aeo_scan(
                    "best NMN supplement",
                    ask=lambda _query: "nobody matched",
                    environ={"GEMINI_API_KEY": "test-key"},
                    ticket_path=path,
                    iterations=1,
                    threshold=1,
                )
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            printed = buf.getvalue()
        self.assertIn("Mention: no.", printed)
        self.assertIn("Citation: unknown.", printed)
        self.assertIn("mention count: 0/1", text)
        self.assertIn("domain_cited: unknown", text)
        self.assertNotIn("AI Overviews", text)

    def test_api_error_does_not_become_a_miss(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ticket.md")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                aeo_tracker.run_aeo_scan(
                    "best NMN supplement",
                    ask=lambda _query: None,
                    environ={"GEMINI_API_KEY": "test-key"},
                    ticket_path=path,
                    iterations=1,
                    threshold=1,
                )
            self.assertFalse(os.path.exists(path))
            self.assertIn("No ticket", buf.getvalue())

    def test_default_ticket_path_stays_in_this_repo(self):
        path = aeo_tracker.default_ticket_path()
        self.assertEqual(os.path.dirname(path), ROOT)
        self.assertTrue(path.endswith("AEO_ACTION_TICKETS.md"))


class Cli(unittest.TestCase):
    def test_self_check_report_template_and_adapt_skip(self):
        env = quiet_env()
        self_check = subprocess.run(
            [PY, SCRIPT, "self-check"], cwd=ROOT, env=env,
            capture_output=True, text=True,
        )
        self.assertEqual(self_check.returncode, 0, self_check.stdout + self_check.stderr)
        self.assertIn("✓ PASS", self_check.stdout)
        self.assertIn("prompts=51", self_check.stdout)
        self.assertIn("slots=306", self_check.stdout)

        report = subprocess.run(
            [PY, SCRIPT, "report"], cwd=ROOT, env=env,
            capture_output=True, text=True,
        )
        self.assertEqual(report.returncode, 0, report.stdout + report.stderr)
        self.assertIn("Slots: 306", report.stdout)
        self.assertIn("Disagreement gaps: 0", report.stdout)
        self.assertIn("## Mentioned but not cited", report.stdout)
        self.assertIn("## Cited but not mentioned", report.stdout)
        self.assertIn("geo_citability.py", report.stdout)
        self.assertIn("ai_citation_observed", report.stdout)
        self.assertIn("segment glue", report.stdout)
        self.assertIn("Grok/X", report.stdout)
        self.assertIn("Google AI Mode", report.stdout)

        usage = subprocess.run([PY, SCRIPT], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(usage.returncode, 1)
        self.assertIn("template", usage.stdout)

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "template.json")
            made = subprocess.run(
                [PY, SCRIPT, "template", "--out", out], cwd=ROOT, env=env,
                capture_output=True, text=True,
            )
            self.assertEqual(made.returncode, 0, made.stderr)
            checked = subprocess.run(
                [PY, SCRIPT, "validate", out], cwd=ROOT, env=env,
                capture_output=True, text=True,
            )
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            refused = subprocess.run(
                [PY, SCRIPT, "template", "--out", ai_visibility.LEDGER_PATH],
                cwd=ROOT, env=env, capture_output=True, text=True,
            )
            self.assertEqual(refused.returncode, 1)
            self.assertIn("refusing", refused.stdout)
            with open(ai_visibility.LEDGER_PATH, encoding="utf-8") as handle:
                ledger = json.load(handle)
            self.assertEqual(ledger["observations"], [])

        adapt = subprocess.run(
            [PY, SCRIPT, "adapt", "--platform", "gemini", "--prompt-id", first_prompt("ageaura")["id"]],
            cwd=ROOT, env=env, capture_output=True, text=True,
        )
        self.assertEqual(adapt.returncode, 0, adapt.stdout + adapt.stderr)
        self.assertIn("skipped", adapt.stdout)
        self.assertIn("GEMINI_API_KEY is not set", adapt.stdout)

        bad = subprocess.run(
            [PY, SCRIPT, "validate", os.path.join(ROOT, "data", "ai_visibility", "missing.json")],
            cwd=ROOT, env=env, capture_output=True, text=True,
        )
        self.assertEqual(bad.returncode, 1)


if __name__ == "__main__":
    unittest.main()

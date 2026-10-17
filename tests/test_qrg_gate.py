"""QRG skip is a named warning. Measured scores still hard-fail."""
import os
import sys
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import validate_article as va


def measured(**overrides):
    quality = {
        "overall_quality": 90,
        "filler_score": 0,
        "ai_pattern_score": 0,
        "repetition_score": 0,
        "information_density": 0.8,
        "matches": {"filler": ["very unique"], "ai_patterns": ["delve"]},
    }
    quality.update(overrides)
    return {
        "quality": quality,
        "verify": {"claim_count": 0, "uncited_count": 0, "uncited_ratio": 0},
    }


class QrgSkipTests(unittest.TestCase):
    def test_missing_launcher_names_the_reason_and_does_not_hold(self):
        with mock.patch.object(va, "_claude_seo_bin", return_value=None):
            scores, note = va.qrg_scores("plain prose")
        self.assertIsNone(scores)
        self.assertIn("claude-seo runtime not installed", note)
        self.assertIn("claude-seo", note)
        fails, warns, line = va.qrg_report(scores, note)
        self.assertEqual(fails, [])
        self.assertTrue(warns)
        self.assertTrue(line.startswith("QRG scoring unavailable:"))
        self.assertNotIn("\n", line)
        self.assertNotIn("\t", line)

    def test_low_measured_scores_hard_fail(self):
        fails, _warns, line = va.qrg_report(
            measured(overall_quality=70, filler_score=30, ai_pattern_score=30), "")
        self.assertTrue(any("overall quality" in item for item in fails))
        self.assertTrue(any("filler score" in item for item in fails))
        self.assertTrue(line.startswith("QRG:"))

    def test_advisory_moves_measured_failures_to_warnings(self):
        previous = os.environ.get("GENSEO_QRG_ADVISORY")
        os.environ["GENSEO_QRG_ADVISORY"] = "1"
        try:
            fails, warns, line = va.qrg_report(
                measured(overall_quality=70, filler_score=30), "")
        finally:
            if previous is None:
                os.environ.pop("GENSEO_QRG_ADVISORY", None)
            else:
                os.environ["GENSEO_QRG_ADVISORY"] = previous
        self.assertEqual(fails, [])
        self.assertTrue(any("overall quality" in item for item in warns))
        self.assertTrue(line.startswith("QRG:"))

    def test_log_column_flattens_the_skip_reason(self):
        column = va.qrg_log_column(None, "line one\nline\ttwo")
        self.assertTrue(column.startswith("qrg=skip:"))
        self.assertNotIn("\n", column)
        self.assertNotIn("\t", column)
        self.assertIn("line one line two", column)

    def test_malformed_scorer_json_is_unavailable(self):
        fails, warns, line = va.qrg_report({"quality": "nope"}, "")
        self.assertEqual(fails, [])
        self.assertTrue(any("unusable" in item for item in warns))
        self.assertTrue(line.startswith("QRG scoring unavailable:"))

    def test_skill_documents_the_skip(self):
        path = os.path.join(ROOT, "skills", "genseo-auto-publish", "SKILL.md")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("QRG scoring unavailable:", text)
        self.assertIn("does not fail the draft", text)


if __name__ == "__main__":
    unittest.main()

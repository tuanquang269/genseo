"""Queue closures survive a return to the open ticket file on main.

No Shopify, no network. A temp git repo stands in for the day-run branch.

    python3 -m unittest tests/test_queue_closures.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import genseo_queue_closures as qc  # noqa: E402


ARTICLE = """- [ ] **#CA1016-2 — shilajit on an empty stomach** — `Title`
- [ ] **#CA1016-7 — vaginal probiotics over 60** — `Next`
"""
ARTICLE_CLOSED = ARTICLE.replace(
    "- [ ] **#CA1016-2",
    "- [DONE 2026-10-18 https://wellnessnest.co/blogs/news/shilajit-on-an-empty-stomach-yes-or-no-in-the-us] **#CA1016-2",
    1,
)
LANDING = """- [ ] listicle | wellnessnest | product=premium-himalayan-shilajit-gummies · angle: gummies (added 2026-10-16)
- [ ] listicle | wellnessnest | product=florafresh-vaginal-probiotics-gummies · angle: flora (added 2026-10-16)
"""
LANDING_CLOSED = LANDING.replace(
    "- [ ] listicle | wellnessnest | product=premium-himalayan-shilajit-gummies",
    "- [DRAFT 2026-10-18 page 166299173179] listicle | wellnessnest | product=premium-himalayan-shilajit-gummies",
    1,
)


def git(repo, *args, check=True):
    proc = subprocess.run(["git", "-C", repo, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and proc.returncode != 0:
        raise AssertionError("%s failed: %s" % (" ".join(args), proc.stderr))
    return proc


class ClosureUnitTests(unittest.TestCase):
    def test_article_id_and_landing_body_are_recorded(self):
        article = qc.closures_between(ARTICLE_CLOSED, ARTICLE, "daily-tickets.md")
        landing = qc.closures_between(LANDING_CLOSED, LANDING, "daily-landing-tickets.md")
        self.assertEqual([row["ticket_id"] for row in article], ["CA1016-2"])
        self.assertEqual(landing[0]["ticket_id"], "")
        self.assertIn("premium-himalayan-shilajit-gummies", landing[0]["body"])
        self.assertNotIn("florafresh", landing[0]["body"])

    def test_open_lines_skip_the_ledger_and_keep_the_next_ticket(self):
        entries = qc.closures_between(ARTICLE_CLOSED, ARTICLE, "daily-tickets.md")
        entries.extend(qc.closures_between(LANDING_CLOSED, LANDING, "daily-landing-tickets.md"))
        article_open = qc.effective_open_lines(ARTICLE, entries, "daily-tickets.md")
        landing_open = qc.effective_open_lines(LANDING, entries, "daily-landing-tickets.md")
        self.assertEqual(len(article_open), 1)
        self.assertIn("#CA1016-7", article_open[0])
        self.assertNotIn("#CA1016-2", article_open[0])
        self.assertEqual(len(landing_open), 1)
        self.assertIn("florafresh", landing_open[0])

    def test_a_line_closed_on_both_sides_is_not_recorded(self):
        self.assertEqual(qc.closures_between(ARTICLE_CLOSED, ARTICLE_CLOSED, "daily-tickets.md"), [])

    def test_corrupt_ledger_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "state"))
            path = os.path.join(tmp, "state", "queue-closures.json")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("{")
            queue = os.path.join(tmp, "daily-tickets.md")
            with open(queue, "w", encoding="utf-8") as fh:
                fh.write(ARTICLE)
            rc = qc.main(["count", "--queue", queue, "--repo", tmp])
            self.assertEqual(rc, 2)


class ClosureGitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "queue-test@example.com")
        git(self.repo, "config", "user.name", "queue-test")
        git(self.repo, "config", "commit.gpgsign", "false")
        with open(os.path.join(self.repo, ".gitignore"), "w", encoding="utf-8") as fh:
            fh.write("state/\n")
        with open(os.path.join(self.repo, "daily-tickets.md"), "w", encoding="utf-8") as fh:
            fh.write(ARTICLE)
        with open(os.path.join(self.repo, "daily-landing-tickets.md"), "w", encoding="utf-8") as fh:
            fh.write(LANDING)
        git(self.repo, "add", ".gitignore", "daily-tickets.md", "daily-landing-tickets.md")
        git(self.repo, "commit", "-m", "open queue")
        git(self.repo, "checkout", "-b", "article/ca1016-2")
        with open(os.path.join(self.repo, "daily-tickets.md"), "w", encoding="utf-8") as fh:
            fh.write(ARTICLE_CLOSED)
        with open(os.path.join(self.repo, "daily-landing-tickets.md"), "w", encoding="utf-8") as fh:
            fh.write(LANDING_CLOSED)
        git(self.repo, "add", "daily-tickets.md", "daily-landing-tickets.md")
        git(self.repo, "commit", "-m", "closed on the article branch")

    def tearDown(self):
        self.tmp.cleanup()

    def test_record_is_idempotent_and_dry_run_does_not_write(self):
        rc = qc.main(["record", "--repo", self.repo, "--base", "main", "--head", "HEAD", "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertFalse(os.path.exists(os.path.join(self.repo, "state", "queue-closures.json")))
        rc = qc.main(["record", "--repo", self.repo, "--base", "main", "--head", "article/ca1016-2"])
        self.assertEqual(rc, 0)
        rc = qc.main(["record", "--repo", self.repo, "--base", "main", "--head", "article/ca1016-2"])
        self.assertEqual(rc, 0)
        with open(os.path.join(self.repo, "state", "queue-closures.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        ids = [entry["ticket_id"] for entry in data["entries"]]
        self.assertEqual(ids.count("CA1016-2"), 1)
        self.assertEqual(len(data["entries"]), 2)
        git(self.repo, "checkout", "main")
        with open(os.path.join(self.repo, "daily-tickets.md"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("- [ ] **#CA1016-2", text)
        first = qc.effective_open_lines(text, data["entries"], "daily-tickets.md")
        self.assertEqual(len(first), 1)
        self.assertTrue(first[0].startswith("- [ ] **#CA1016-7"))
        self.assertNotIn("#CA1016-2", first[0])


if __name__ == "__main__":
    unittest.main()

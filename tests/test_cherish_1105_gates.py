"""Cherish 2026-11-05 err log root causes. python3 tests/test_cherish_1105_gates.py
1 NIA 405 to a script UA (browser UA retry) · 2 numeric gate: clock times, check dates, rank cells, "N Reasons" count
3 meta row is runner-owned · 4 writer told it runs unattended · 5 shortfall hint covers cards + journal links · 6 PAINT_JS makes lazy images eager."""
import inspect, sys, unittest, urllib.error
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import run_store as rs


class T(unittest.TestCase):
    def test_numeric_noise_is_not_a_claim(self):
        for s in ['If it holds onto moisture, you will be clammy at 3 am', 'Sources checked on November 5, 2026',
                  'ettitude, best sheets for night sweats , checked 2026-11-05: fabric comparison', 'Posted in spring 2025',
                  '2', 'One r/Bedding post from April 2025 says it cleanly']:
            self.assertNotRegex(rs.not_claims(s), r'\d', s)
        self.assertNotRegex(rs.not_claims('6 Reasons a Waffle Throw Is the Summer Layer', reasons=6), r'\d')
        for s in ['It is 100% cotton', 'The large is 60 × 80 in', 'From $69', '6 Reasons a Waffle Throw', 'The guarantee runs 100 nights']:
            self.assertRegex(rs.not_claims(s, reasons=7), r'\d', s)   # real facts still need a claim

    def test_405_retries_with_browser_ua(self):
        rs.fetch_page.cache_clear()
        calls = []
        class R:
            def __enter__(s): return s
            def __exit__(s, *a): pass
            def read(s, n): return b'Hot flashes'
        def fake(req, timeout):
            calls.append(req.get_header('User-agent'))
            if len(calls) == 1:
                raise urllib.error.HTTPError(req.full_url, 405, 'Not Allowed', {}, None)
            return R()
        with mock.patch('urllib.request.urlopen', fake):
            self.assertEqual(rs.fetch_page('https://www.nia.nih.gov/x'), 'Hot flashes')
        self.assertEqual(calls[1], rs.BROWSER_UA)

    def test_meta_row_runner_owned(self):
        src = inspect.getsource(rs.finalize_page)
        self.assertIn("re.search(r'<p class=\"meta\">.*?</p>', template", src)

    def test_writer_runs_unattended(self):
        self.assertIn('Never ask a question', rs.WRITER_RULES)

    def test_shortfall_hint_cards_journal(self):
        out = "RULES FAIL ['words', 'cards', 'images', 'journal_links'] words=1542 h2=8 qh2=6 cards=1 imgs=5 authority=5 journal=1 tables=1"
        hint = rs.shortfall_hint(out, {'words': [1500, 2200], 'img': [6, 10], 'cards': [2, 2], 'journal_links': 2})
        self.assertIn('CARDS: 1', hint)
        self.assertIn('JOURNAL LINKS: 1', hint)

    def test_paint_forces_eager(self):
        import fidelity_gate
        self.assertIn("i.loading = 'eager'", fidelity_gate.PAINT_JS)


if __name__ == '__main__':
    unittest.main()

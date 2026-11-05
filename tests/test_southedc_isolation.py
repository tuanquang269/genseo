"""SouthEDC isolation checks. Offline: no Shopify, no network, no paid API.
Run: python3 tests/test_southedc_isolation.py (from ~/genseo) or via tests/run_suite.sh.
Tests marked expectedFailure wait for the guard-code edits listed in the 2026-11-05 SouthEDC scaffold report.
When a guard edit lands, its test turns into an "unexpected success": remove that decorator."""
import csv
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
WORK = Path.home() / 'PATI/work/southedc-seo'
PROFILE = ROOT / 'stores/southedc/profile.json'
STYLES = ['1-problem-solution', '2-buyers-guide', '3-care-guide', '4a-material-vs', '4b-brand-vs', '4c-best-x', '4d-n-reasons']
TEMPLATES = [WORK / f'blog-styles/style-{s}.html' for s in STYLES]
OWN_FILES = [PROFILE, WORK / 'calendar.csv', WORK / 'southedc-product-registry.csv', WORK / 'brand-notes.md', WORK / 'index-audit.md',
             WORK / 'blog-styles/tools/check.py', WORK / 'blog-styles/tools/tpl.py', WORK / 'blog-styles/tools/build_templates.py', *TEMPLATES]
FOREIGN = ('thecherishcompany.com', 'uxfaue-s1', 'wellnessnest.co', 'wellnessnest1', 'cherish', 'wellness nest')
# Topic guard: no gun-use instruction, no ballistics, no legal advice. "carry" alone is allowed.
BANNED = re.compile(r'ballistic|calib(er|re)|stopping power|\bdraw(ing)?\b|drill|how to shoot|shooting|\bfire\b|trigger|ammo|ammunition'
                    r'|\blaws?\b|legal|reciprocity|permit|license|licence|constitutional', re.I)


def profile():
    return json.loads(PROFILE.read_text())


def calendar():
    return list(csv.DictReader((WORK / 'calendar.csv').read_text().splitlines()))


class SouthEDCIsolation(unittest.TestCase):
    def test_domain_shop_pair(self):
        p = profile()
        self.assertEqual((p['id'], p['domain'], p['shop']), ('southedc', 'southedc.store', 'wellness-nest-de.myshopify.com'))
        self.assertEqual(p['article_contract'], 'fragment-v1')
        self.assertEqual(p['daily_volume'], 3)
        c = p['credential']
        self.assertEqual(c['kind'], 'client-credentials')
        self.assertEqual(c['keys'], ['SHOPIFY_SOUTHEDC_CLIENT_ID', 'SHOPIFY_SOUTHEDC_CLIENT_SECRET'])
        self.assertTrue(all(k.startswith(c['prefix']) for k in c['keys']))

    def test_profile_inputs_exist_and_stay_in_southedc_tree(self):
        p = profile()
        paths = [*p['context'], *p['templates'], *p['gates'], p['calendar'], p['registry']]
        for s in paths:
            path = Path(s).resolve()
            self.assertTrue(path.is_file(), s)
            self.assertIn(WORK.resolve(), path.parents, s)

    def test_no_foreign_store_names(self):
        for f in OWN_FILES:
            text = f.read_text().lower()
            for name in FOREIGN:
                self.assertNotIn(name, text, f'{name!r} in {f}')

    def test_calendar_shape(self):
        rows = calendar()
        p = profile()
        self.assertEqual(len(rows), p['calendar_rows'])
        handles = {r['product_handle'] for r in csv.DictReader((WORK / 'southedc-product-registry.csv').read_text().splitlines())}
        per_day = {}
        for r in rows:
            self.assertEqual(r['approval'], 'auto')
            self.assertIn(r['target_product_handle'], handles)
            self.assertIn(r['style'], {s.split('-')[0] for s in STYLES})
            per_day[r['day']] = per_day.get(r['day'], 0) + 1
        self.assertLessEqual(max(per_day.values()), p['daily_volume'])
        self.assertEqual(len({r['primary_keyword'] for r in rows}), len(rows), 'duplicate primary keyword')

    def test_calendar_has_no_banned_topics(self):
        for r in calendar():
            text = ' '.join(r[k] for k in ('angle', 'primary_keyword', 'secondary_keywords', 'uniqueness_key'))
            self.assertIsNone(BANNED.search(text), f"banned topic in row {r['day']} {r['primary_keyword']!r}")

    def test_templates_are_fragment_v1(self):
        for t in TEMPLATES:
            html = t.read_text()
            self.assertEqual(html.count('id="genseo-southedc"'), 1, t.name)
            self.assertRegex(html, r'<script[^>]*id="rules-machine"[^>]*>\s*\{', t.name)
            self.assertNotIn('#genseo-cherish', html)

    # ---- guard code that does not know 'southedc' yet -------------------------------------------------

    def test_profile_guard_accepts_southedc(self):
        from store_profiles import Profile
        self.assertEqual(Profile('southedc').data['shop'], 'wellness-nest-de.myshopify.com')

    def test_run_store_cli_accepts_southedc(self):
        src = (ROOT / 'scripts/run_store.py').read_text()
        m = re.search(r"add_argument\('--store'[^)]*choices=\[([^\]]*)\]", src)
        self.assertIn("'southedc'", m.group(1))

    def test_publisher_accepts_southedc(self):
        src = (ROOT / 'scripts/store_publisher.py').read_text()
        self.assertNotIn("require(profile.store == 'cherish'", src)
        self.assertNotIn("'#genseo-cherish'", src)

    def test_scope_css_uses_store_root(self):
        import store_article
        self.assertIn('#genseo-southedc', store_article.scope_css('p{color:red}', 'genseo-southedc'))


if __name__ == '__main__':
    unittest.main(verbosity=2)

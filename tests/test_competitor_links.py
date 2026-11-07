"""REFLINK-FIX 2026-10-28: competitor anchors get nofollow; competitor link rules fire. Offline.
  /usr/bin/python3 tests/test_competitor_links.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
import run_store as rs


class P:
    data = {'competitor_domains': ['bearaby.com', 'brooklinen.com']}


class CompetitorLinks(unittest.TestCase):
    def test_nofollow_added(self):
        page = ('<a href="https://www.brooklinen.com/products/x" rel="noopener">B</a>'
                '<a href="https://shop.bearaby.com/products/y">Y</a><a href="https://medlineplus.gov/a" rel="noopener">M</a>')
        out = rs.nofollow_competitors(page, P.data['competitor_domains'])
        self.assertEqual(out.count('rel="nofollow noopener"'), 2)
        self.assertIn('<a href="https://medlineplus.gov/a" rel="noopener">', out)
        self.assertEqual(rs.nofollow_competitors('<a href="https://notbearaby.com/x">', ['bearaby.com']), '<a href="https://notbearaby.com/x">')
        self.assertEqual(rs.nofollow_competitors('<a href="https://bearaby.com.evil/x">', ['bearaby.com']), '<a href="https://bearaby.com.evil/x">')

    def test_rules(self):
        ok = '<ol class="sources"><li><a href="https://bearaby.com/products/the-napper" rel="nofollow noopener">B</a>. Checked: 10 lb.</li></ol>'
        alt = {'primary_keyword': 'bearaby weighted blanket alternative', 'uniqueness_key': ''}
        other = {'primary_keyword': 'percale vs sateen', 'uniqueness_key': ''}
        self.assertEqual(rs.competitor_problems(ok, P, alt), [])
        self.assertTrue(rs.competitor_problems(ok, P, other))                                   # not that brand's article
        self.assertTrue(rs.competitor_problems(ok.replace('/products/the-napper', '/blogs/x'), P, alt))  # blog page
        self.assertTrue(rs.competitor_problems('<p><a href="https://bearaby.com/products/a" rel="nofollow">B</a></p>', P, alt))  # body link
        self.assertTrue(rs.competitor_problems(ok.replace('nofollow ', ''), P, alt))            # no nofollow
        self.assertTrue(rs.competitor_problems(ok + ok, P, alt))                                # duplicate
        self.assertTrue(rs.competitor_problems('<li>Page title and product menu.</li>', P, alt))  # vague note


if __name__ == '__main__':
    unittest.main()

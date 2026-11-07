#!/usr/bin/env python3
"""Daily 08:45 ranking block for 1.4 (Chief trigger). One line per store from GSC, $0 (OAuth token, no AI).
  /usr/bin/python3 scripts/rank_report.py            -> stdout, max 8 lines, blocker line first
Window: last 7 complete days (GSC lags ~2 days) vs the 7 days before. Query-level average position.
top3/10/20 = queries with >= 1 impression whose average position is <= 3 / 10 / 20. new = queries with >= MIN_IMP impressions in this window absent last window.
ponytail: query-level, not page-level; add page split when a store needs per-article tracking."""
import datetime as dt
import sys
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')
from google.oauth2.credentials import Credentials  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402

SITES = [('WN', 'sc-domain:wellnessnest.co'), ('Cherish', 'sc-domain:thecherishcompany.com'), ('SouthEDC', 'sc-domain:southedc.store')]
MIN_IMP = 3   # a 1-impression query is noise, not a new keyword
TOKEN = Path(__file__).resolve().parent/'gsc_token.json'


def rows(svc, site, start, end):
    body = {'startDate': start.isoformat(), 'endDate': end.isoformat(), 'dimensions': ['query'], 'rowLimit': 25000}
    return {r['keys'][0]: r for r in svc.searchanalytics().query(siteUrl=site, body=body).execute().get('rows', [])}


def summary(now, before):
    tops = [sum(1 for r in now.values() if r['position'] <= k) for k in (3, 10, 20)]
    clicks = sum(r['clicks'] for r in now.values())
    imp = sum(r['impressions'] for r in now.values())
    pos = sum(r['position'] * r['impressions'] for r in now.values()) / imp if imp else 0
    imp0 = sum(r['impressions'] for r in before.values())
    pos0 = sum(r['position'] * r['impressions'] for r in before.values()) / imp0 if imp0 else 0
    tops0 = [sum(1 for r in before.values() if r['position'] <= k) for k in (3, 10, 20)]
    new = sorted((q for q in now if q not in before and now[q]['position'] <= 20 and now[q]['impressions'] >= MIN_IMP), key=lambda q: now[q]['position'])
    return tops, tops0, clicks, imp, pos, pos0, new


def main():
    svc = build('searchconsole', 'v1', credentials=Credentials.from_authorized_user_file(str(TOKEN)), cache_discovery=False)
    end = dt.date.today() - dt.timedelta(days=2)
    w = (end - dt.timedelta(days=6), end)
    w0 = (w[0] - dt.timedelta(days=7), w[0] - dt.timedelta(days=1))
    lines, blockers = [], []
    for name, site in SITES:
        try:
            now, before = rows(svc, site, *w), rows(svc, site, *w0)
        except Exception as error:  # noqa: BLE001 - one store's API error must not hide the others
            blockers.append(f'{name} GSC error: {str(error)[:80]}')
            continue
        tops, tops0, clicks, imp, pos, pos0, new = summary(now, before)
        if not imp:
            blockers.append(f'{name} has 0 impressions (not indexed by Google)')
        d = lambda a, b: f'{a}({a - b:+d})'
        lines.append(f'{name}: top3 {d(tops[0], tops0[0])} · top10 {d(tops[1], tops0[1])} · top20 {d(tops[2], tops0[2])} · '
                     f'avg pos {pos:.1f} (was {pos0:.1f}) · {clicks} clicks / {imp} impr · new top20: '
                     + (', '.join(f'"{q}" {now[q]["position"]:.0f}' for q in new[:3]) or 'none'))
    head = 'BLOCKER: ' + '; '.join(blockers) if blockers else f'BLOCKER: none · GSC {w[0]:%m-%d}..{w[1]:%m-%d} vs prior 7 d'
    print('\n'.join([head] + lines[:7]))


if __name__ == '__main__':
    sys.exit(main())

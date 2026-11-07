"""Reddit evidence is read from Arctic-Shift; a non-Reddit URL is not routed there."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
import run_store as r

def test_reddit_route():
    calls = []
    r.reddit_text, orig = (lambda pid: calls.append(pid) or 'body'), r.reddit_text
    try:
        assert r.fetch_page('https://www.reddit.com/r/Bedding/comments/1k4tby6/') == 'body'
        assert r.fetch_page('https://old.reddit.com/r/Menopause/comments/1nprv8d/slug/') == 'body'
        assert calls == ['1k4tby6', '1nprv8d']
        assert r.REDDIT_THREAD.match('https://www.goodhousekeeping.com/x') is None
    finally:
        r.reddit_text = orig

if __name__ == '__main__':
    test_reddit_route(); print('PASS')

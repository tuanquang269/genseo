"""The fidelity gate backs off a Shopify "Browser verification" page and never captures it (2026-11-04: 'no region root found').
python3 tests/test_cherish_gate_challenge.py"""
import http.server, threading, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import fidelity_gate as g
from playwright.sync_api import sync_playwright
hits = {'n': 0}
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        hits['n'] += 1
        ok = self.path == '/ok' or (self.path == '/flaky' and hits['n'] > 1)
        self.send_response(200 if ok else 403); self.send_header('Content-Type', 'text/html'); self.end_headers()
        self.wfile.write(b'<title>Post</title><div class="layout">x</div>' if ok else b'<title>Browser verification</title>')
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{srv.server_port}'
with sync_playwright() as p:
    b = p.chromium.launch(channel="chromium", args=["--disable-gpu"])
    ctx = g.new_context(b, 390); ctx.unroute('**/*'); pg = ctx.new_page()
    assert g.goto_past_challenge(pg, base + '/flaky', waits=(0.1,)).status == 200 and pg.query_selector('.layout')
    try:
        g.goto_past_challenge(pg, base + '/blocked', waits=(0.1, 0.1)); raise AssertionError('challenge page passed')
    except RuntimeError as e:
        assert 'store bot challenge: HTTP 403' in str(e), e
    b.close()
srv.shutdown(); print('gate challenge OK')

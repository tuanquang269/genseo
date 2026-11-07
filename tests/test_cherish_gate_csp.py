"""The fidelity gate injects its CSS on a CSP store page (live Cherish: nonce-only style-src). python3 tests/test_cherish_gate_csp.py"""
import http.server, threading, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import fidelity_gate as g
from playwright.sync_api import sync_playwright

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Security-Policy', "style-src 'nonce-abc'"); self.end_headers()
        self.wfile.write(b'<html><body><p id="x">hi</p></body></html>')
    def log_message(self, *a): pass

srv = http.server.HTTPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as p:
    b = p.chromium.launch(channel="chromium", args=["--disable-gpu"])
    ctx = g.new_context(b, 390); ctx.unroute('**/*')   # route_filter blocks third parties; the test page is local
    pg = ctx.new_page(); pg.goto(f'http://127.0.0.1:{srv.server_port}/')
    pg.add_style_tag(content='#x{color:rgb(1,2,3)}')   # crashed before bypass_csp
    assert pg.eval_on_selector('#x', 'e => getComputedStyle(e).color') == 'rgb(1, 2, 3)'
    b.close()
srv.shutdown(); print('gate CSP OK')

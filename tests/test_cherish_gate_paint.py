"""The fidelity gate waits for a late image to paint before a screenshot (2026-11-04: blank template .pick photo, pixel FAIL).
python3 tests/test_cherish_gate_paint.py"""
import http.server, io, threading, time, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import fidelity_gate as g
from PIL import Image
from playwright.sync_api import sync_playwright

buf = io.BytesIO(); Image.new('RGB', (200, 200), (200, 0, 0)).save(buf, 'PNG'); PNG = buf.getvalue()
PAGE = b'<html><body style="margin:0;background:#fff"><img id="i" width="200" height="200"><script>setTimeout(()=>{document.getElementById("i").src="/a.png"},50)</script></body></html>'

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/a.png': time.sleep(0.8)
        body, kind = (PNG, 'image/png') if self.path == '/a.png' else (PAGE, 'text/html')
        self.send_response(200); self.send_header('Content-Type', kind); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass

srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as p:
    b = p.chromium.launch(channel="chromium", args=["--disable-gpu"])
    ctx = g.new_context(b, 390); ctx.unroute('**/*')
    pg = ctx.new_page(); pg.goto(f'http://127.0.0.1:{srv.server_port}/'); pg.wait_for_timeout(150)
    assert pg.evaluate(g.PAINT_JS) == 0
    px = Image.open(io.BytesIO(pg.screenshot(clip={'x': 0, 'y': 0, 'width': 200, 'height': 200}))).convert('RGB').getpixel((100, 100))
    assert px[0] > 150 and px[1] < 60, f'image not painted: {px}'
    b.close()
srv.shutdown(); print('gate paint OK')

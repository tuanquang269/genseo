import { createRequire } from 'module'; const require = createRequire(import.meta.url); const { chromium } = require('playwright');
// usage: node compare.mjs <url> <out.png> <width>
const [,, url, out, w] = process.argv;
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: +w, height: 900 }, deviceScaleFactor: 1 });
await p.goto(url, { waitUntil: 'load', timeout: 60000 });
await p.addStyleTag({ content: '.scroll-trigger{opacity:1!important;transform:none!important;animation:none!important}' });
await p.evaluate(async () => { document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager'); for (let y = 0; y < document.body.scrollHeight; y += 500) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 50)); } window.scrollTo(0, 0); });
await p.waitForTimeout(1200);
await p.screenshot({ path: out, fullPage: true });
const ov = await p.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
console.log(out, 'overflow-x:', ov);
await b.close();

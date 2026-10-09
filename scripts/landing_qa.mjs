// Acceptance checks from the vault skill §7 (responsive + sticky reveal), on the LOCAL preview.
//   NODE_PATH=$(npm root -g) node scripts/landing_qa.mjs landing_drafts/<slug>/preview.html
// Writes desktop.png / mobile.png / sticky-top.png / sticky-bridge.png next to the preview and prints a JSON report.
import { createRequire } from "module";
import path from "path";
const require = createRequire(import.meta.url);
const { chromium } = require(path.join(process.env.NODE_PATH || "", "playwright"));
const file = path.resolve(process.argv[2]); const dir = path.dirname(file); const url = "file://" + file;
const browser = await chromium.launch();
const report = { file, widths: {} };
for (const w of [375, 768, 1440]) {
  const p = await browser.newPage({ viewport: { width: w, height: 900 } });
  await p.goto(url); await p.waitForTimeout(800);
  // full-page shots: force lazy images to load (otherwise everything below the fold is a blank slot)
  await p.evaluate(async () => {
    document.querySelectorAll("img[loading=lazy]").forEach(i => i.loading = "eager");
    for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
    window.scrollTo(0, 0);
    await Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; setTimeout(r, 8000); })));
  });
  await p.waitForTimeout(300);
  report.widths[w] = await p.evaluate(() => ({
    overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
    smallTargets: [...document.querySelectorAll(".gsl-landing a[target=_blank]")].filter(a => a.getBoundingClientRect().height < 44).length,
    brokenImages: [...document.querySelectorAll(".gsl-ref img, .gsl-landing img")].filter(i => !i.naturalWidth).map(i => i.currentSrc || i.src).slice(0, 5),
    headings: [...document.querySelectorAll(".gsl-landing h1,.gsl-landing h2")].map(h => h.tagName).join("").replace(/H2+/g, "H2…"),
    clipped: [...document.querySelectorAll(".gsl-ref *")].filter(e => {   // text cut off: own text wider than its box (offer pill 2026-10-09), scrollers excluded
      if (![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return false;
      const cs = getComputedStyle(e), r = e.getBoundingClientRect(); if (!r.width || cs.display === "none" || cs.visibility === "hidden" || cs.textOverflow === "ellipsis") return false;   // hidden sticky bar / deliberate ellipsis
      for (let a = e; a && a !== document.body; a = a.parentElement) if (/auto|scroll/.test(getComputedStyle(a).overflowX)) return false;   // swipe carousels are meant to run off-screen
      return e.scrollWidth > e.clientWidth + 1 || r.right > innerWidth + 1 || r.left < -1; }).map(e => (e.className || e.tagName) + ": " + e.textContent.trim().slice(0, 40)).slice(0, 5),
    palette: (() => { const q = s => document.querySelector(s), c = (s, p) => q(s) ? getComputedStyle(q(s))[p] : null;   // effective colors, for the pack-palette gate
      return { cta_bg: c(".gslp-hero .gslp-btn", "backgroundColor"), accent: c(".gslp-hero .rblha__accent", "color"), kicker: c(".gslp-kicker", "color"),
               topbar_bg: c(".rbltb", "backgroundColor"), pill_bg: c(".rblof__pill", "backgroundColor"), offer_cta_bg: c(".rblof a[href*='/products/']", "backgroundColor") }; })(),
  }));
  if (w === 1440) await p.screenshot({ path: path.join(dir, "desktop.png"), fullPage: true });
  if (w === 375) await p.screenshot({ path: path.join(dir, "mobile.png"), fullPage: true });
  await p.close();
}
const p = await browser.newPage({ viewport: { width: 1280, height: 900 } });
await p.goto(url); await p.waitForTimeout(800);
const barVisible = () => p.evaluate(() => {
  const z = document.querySelector(".gsl-sticky-zone"); if (!z) return null;
  const bar = z.lastElementChild.getBoundingClientRect();
  return bar.top < innerHeight && bar.bottom > 0;
});
report.stickyAtTop = await barVisible();
await p.screenshot({ path: path.join(dir, "sticky-top.png") });
await p.evaluate(() => { const z = document.querySelector(".gsl-sticky-zone"); if (z) window.scrollTo(0, z.getBoundingClientRect().top + scrollY + 200); });
await p.waitForTimeout(400);
report.stickyInZone = await barVisible();
await p.screenshot({ path: path.join(dir, "sticky-zone.png") });
console.log(JSON.stringify(report, null, 1));
await browser.close();

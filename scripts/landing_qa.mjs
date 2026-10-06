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
  report.widths[w] = await p.evaluate(() => ({
    overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
    smallTargets: [...document.querySelectorAll(".gsl-landing a[target=_blank]")].filter(a => a.getBoundingClientRect().height < 44).length,
    headings: [...document.querySelectorAll(".gsl-landing h1,.gsl-landing h2")].map(h => h.tagName).join("").replace(/H2+/g, "H2…"),
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

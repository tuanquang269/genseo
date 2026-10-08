// Real Trustpilot reviews for GenSeo landing pages (Kevin 2026-10-08: 4–5★ only, verbatim, from
// trustpilot.com/review/wellnessnest.co). curl/WebFetch hit a bot wall, so this reads __NEXT_DATA__ in a real
// Chromium (headless first, then a visible window as fallback — works from launchd in the GUI session).
//   NODE_PATH=$(npm root -g) node scripts/trustpilot_reviews.mjs [pages=4]
// Writes state/trustpilot/wellnessnest.json: {fetched_at, url, trustScore, numberOfReviews, reviews:[4–5★ only]}.
// Exit 0 = file written with >= 1 review; exit 1 = could not read Trustpilot (the caller must NOT invent reviews).
import { createRequire } from "module";
import fs from "fs";
import path from "path";
const require = createRequire(import.meta.url);
const { chromium } = require(path.join(process.env.NODE_PATH || "", "playwright"));
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const OUT = path.join(ROOT, "state", "trustpilot", "wellnessnest.json");
const BASE = "https://www.trustpilot.com/review/wellnessnest.co";
const PAGES = parseInt(process.argv[2] || "4", 10);

async function readAll(headless) {
  const opts = { headless };
  let browser;
  try { browser = await chromium.launch({ ...opts, channel: "chrome" }); } catch { browser = await chromium.launch(opts); }
  const ctx = await browser.newContext({ locale: "en-US", userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36" });
  const page = await ctx.newPage();
  const out = { bu: null, reviews: [] };
  try {
    for (let pg = 1; pg <= PAGES; pg++) {
      await page.goto(BASE + (pg > 1 ? `?page=${pg}` : ""), { waitUntil: "domcontentloaded", timeout: 60000 });
      let raw = null;
      for (let i = 0; i < 20 && !raw; i++) {
        raw = await page.evaluate(() => document.getElementById("__NEXT_DATA__")?.textContent || null).catch(() => null);
        if (!raw) await page.waitForTimeout(1500);
      }
      if (!raw) { if (pg === 1) throw new Error("no __NEXT_DATA__ (bot wall?)"); break; }
      const pp = JSON.parse(raw).props.pageProps;
      if (pg === 1) out.bu = pp.businessUnit || {};
      const rs = pp.reviews || [];
      if (!rs.length) break;
      for (const r of rs) out.reviews.push({
        id: r.id, rating: r.rating, title: r.title, text: r.text, name: r.consumer?.displayName,
        country: r.consumer?.countryCode, published: r.dates?.publishedDate, experienced: r.dates?.experiencedDate,
        verified: !!r.labels?.verification?.isVerified, url: `https://www.trustpilot.com/reviews/${r.id}`, page: pg });
    }
  } finally { await browser.close(); }
  return out;
}

let res = null, err = null;
for (const headless of [true, false]) {
  try { res = await readAll(headless); if (res.bu && res.reviews.length) break; } catch (e) { err = e; res = null; }
}
if (!res || !res.bu) { console.error("✗ Trustpilot unreadable:", err?.message || "no data"); process.exit(1); }
const good = res.reviews.filter(r => r.rating >= 4 && (r.text || "").trim());
const rec = { fetched_at: new Date().toISOString(), url: BASE, trustScore: res.bu.trustScore, stars: res.bu.stars,
  numberOfReviews: res.bu.numberOfReviews, displayName: res.bu.displayName,
  note: "4–5★ reviews only, verbatim from __NEXT_DATA__. Quote text exactly; name as shown; TrustScore/count exactly as here (page shows the count with a thousands comma).",
  reviews: good };
fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(rec, null, 1));
console.log(`✓ Trustpilot: TrustScore ${rec.trustScore}, ${rec.numberOfReviews} reviews; kept ${good.length} of ${res.reviews.length} (4–5★) -> ${path.relative(ROOT, OUT)}`);
if (!good.length) process.exit(1);

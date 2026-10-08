// Benchmark extractor for landing pages (Kevin 2026-10-08: score GenSeo listicles vs the reference with JEV, which is
// text-only, so the visual side is turned into neutral, mechanical measurements taken the same way on both pages).
//   NODE_PATH=$(npm root -g) node scripts/landing_bench_extract.mjs <url|file> <out_prefix>
// Writes <out_prefix>-desktop.png (1440), <out_prefix>-mobile.png (375) and <out_prefix>.json {text, desktop{}, mobile{}}.
import { createRequire } from "module";
import fs from "fs";
import path from "path";
const require = createRequire(import.meta.url);
const { chromium } = require(path.join(process.env.NODE_PATH || "", "playwright"));
const [, , target, outPrefix] = process.argv;
const url = /^https?:|^file:/.test(target) ? target : "file://" + path.resolve(target);
const browser = await chromium.launch();
const res = { url };

async function measure(w, h) {
  const p = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
  await p.goto(url, { waitUntil: "load", timeout: 60000 });
  await p.addStyleTag({ content: ".scroll-trigger{opacity:1!important;transform:none!important;animation:none!important}" });
  await p.evaluate(async () => {
    document.querySelectorAll("img[loading=lazy]").forEach(i => i.loading = "eager");
    for (let y = 0; y < document.body.scrollHeight; y += 500) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 50)); }
    window.scrollTo(0, 0);
    await Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; setTimeout(r, 6000); })));
  });
  await p.waitForTimeout(800);
  await p.screenshot({ path: `${outPrefix}-${w > 800 ? "desktop" : "mobile"}.png`, fullPage: true });
  const m = await p.evaluate((H) => {
    const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 2 && r.height > 2 && s.visibility !== "hidden" && s.display !== "none" && +s.opacity > 0.05; };
    const root = document.querySelector("main") || document.body;
    const Y = el => Math.round(el.getBoundingClientRect().top + scrollY);
    const ps = [...root.querySelectorAll("p, li")].filter(e => vis(e) && e.innerText.trim().split(/\s+/).length >= 6);
    const fs = e => parseFloat(getComputedStyle(e).fontSize);
    const words = ps.map(e => e.innerText.trim().split(/\s+/).length);
    const measureCh = ps.map(e => Math.round(e.getBoundingClientRect().width / (fs(e) * 0.5)));
    const h1 = root.querySelector("h1");
    const lines = e => e ? Math.round(e.getBoundingClientRect().height / (parseFloat(getComputedStyle(e).lineHeight) || fs(e) * 1.2)) : null;
    const imgs = [...root.querySelectorAll("img")].filter(i => vis(i) && i.getBoundingClientRect().width > 60);
    const pageH = document.documentElement.scrollHeight, W = innerWidth;
    const ctas = [...root.querySelectorAll("a, button")].filter(a => {
      if (!vis(a)) return false; const r = a.getBoundingClientRect(); const s = getComputedStyle(a);
      const bg = s.backgroundColor; return r.height >= 34 && r.width >= 120 && bg && !/rgba\(0, 0, 0, 0\)|transparent/.test(bg) && a.innerText.trim().length > 2;
    }).map(a => ({ text: a.innerText.trim().replace(/\s+/g, " ").slice(0, 60), y: Y(a), h: Math.round(a.getBoundingClientRect().height), wraps: a.getBoundingClientRect().height > 70 }));
    const txt = root.innerText;
    const accents = new Set([...root.querySelectorAll("a, button, [class*=pill], [class*=badge], [class*=btn]")].filter(vis)
      .map(e => getComputedStyle(e).backgroundColor).filter(c => !/rgba\(0, 0, 0, 0\)|rgb\(255, 255, 255\)/.test(c)));
    const radii = new Set([...root.querySelectorAll("img, a, button, div")].filter(vis).map(e => getComputedStyle(e).borderTopLeftRadius).filter(r => r !== "0px"));
    const heads = [...root.querySelectorAll("h1,h2,h3")].filter(vis).map(h => `${h.tagName}:${h.innerText.trim().replace(/\s+/g, " ").slice(0, 90)}`);
    const firstScreen = [...root.querySelectorAll("h1,h2,h3,p,img,a,button")].filter(e => vis(e) && e.getBoundingClientRect().top < H && e.getBoundingClientRect().bottom > 0)
      .map(e => e.tagName === "IMG" ? `IMG(${Math.round(e.getBoundingClientRect().width)}x${Math.round(e.getBoundingClientRect().height)})` : `${e.tagName}:${e.innerText.trim().replace(/\s+/g, " ").slice(0, 70)}`).filter(s => !/:$/.test(s)).slice(0, 14);
    const small = [...root.querySelectorAll("p, li, span, a")].filter(e => vis(e) && e.children.length === 0 && e.innerText.trim().length > 20 && fs(e) < 13).length;
    const med = a => a.length ? a.slice().sort((x, y) => x - y)[Math.floor(a.length / 2)] : null;
    return {
      viewport: `${W}x${H}`, page_height_px: pageH, screens_tall: +(pageH / H).toFixed(1),
      h1: h1 ? { text: h1.innerText.trim().replace(/\s+/g, " "), font_px: fs(h1), lines: lines(h1) } : null,
      headings: heads.slice(0, 30), heading_count: heads.length,
      body_font_px_median: med(ps.map(fs)), body_line_height_ratio: ps.length ? +(parseFloat(getComputedStyle(ps[0]).lineHeight) / fs(ps[0])).toFixed(2) : null,
      paragraph_words_median: med(words), paragraph_words_max: Math.max(0, ...words), paragraphs_over_60_words: words.filter(x => x > 60).length,
      line_length_chars_median: med(measureCh), paragraphs: ps.length,
      image_alts: imgs.map(i => `${Math.round(i.getBoundingClientRect().width)}x${Math.round(i.getBoundingClientRect().height)} ${(i.alt || "(no alt)").slice(0, 110)}`).slice(0, 16),
      images: imgs.length, image_area_share: +(imgs.reduce((s, i) => s + i.getBoundingClientRect().width * i.getBoundingClientRect().height, 0) / (W * pageH)).toFixed(3),
      ctas: ctas.slice(0, 12), cta_count: ctas.length, first_cta_y: ctas.length ? Math.min(...ctas.map(c => c.y)) : null, wrapped_ctas: ctas.filter(c => c.wraps).length,
      first_screen: firstScreen, small_text_blocks_under_13px: small,
      em_dashes: (txt.match(/—/g) || []).length, en_dashes: (txt.match(/–/g) || []).length,
      distinct_accent_bg_colors: accents.size, distinct_corner_radii: radii.size,
      has_countdown: /\b\d{1,2}\s*:\s*\d{2}\s*:\s*\d{2}\b|\bhrs?\b.*\bmins?\b/i.test(txt),
      star_or_rating_mentions: (txt.match(/★|stars?|TrustScore|rating|reviews?/gi) || []).length,
      horizontal_overflow: document.documentElement.scrollWidth > innerWidth + 1,
    };
  }, h);
  const text = await p.evaluate(() => (document.querySelector("main") || document.body).innerText.replace(/\n{3,}/g, "\n\n").trim());
  await p.close();
  return { m, text };
}
const d = await measure(1440, 900), mo = await measure(375, 812);
res.desktop = d.m; res.mobile = mo.m; res.text = d.text;
fs.writeFileSync(`${outPrefix}.json`, JSON.stringify(res, null, 1));
console.log(`${outPrefix}: text ${res.text.length} chars · desktop ${d.m.screens_tall} screens · mobile ${mo.m.screens_tall} screens · CTAs ${d.m.cta_count} · em-dashes ${d.m.em_dashes}`);
await browser.close();

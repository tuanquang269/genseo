// Screenshot the REAL Shopify storefront render of a landing page (not the local preview.html).
// Kevin 2026-10-08: a local render passed review while the storefront showed something else, so QA must see Shopify.
//   NODE_PATH=$(npm root -g) node scripts/landing_live_shot.mjs <storefront url> <out_prefix>
// Fresh browser context per viewport + ?v=<timestamp> cache-buster. Writes <out_prefix>-desktop.png,
// <out_prefix>-mobile.png, <out_prefix>-offer.png (offer box element at desktop) and <out_prefix>.json (DOM facts).
import { createRequire } from "module";
import fs from "fs";
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const [url0, out] = process.argv.slice(2);
if (!url0 || !out) { console.error("usage: landing_live_shot.mjs <url> <out_prefix>"); process.exit(2); }
const url = url0 + (url0.includes("?") ? "&" : "?") + "v=" + Date.now();
const b = await chromium.launch();
const facts = { url };
for (const [name, vp, mobile] of [["desktop", { width: 1440, height: 900 }, false], ["mobile", { width: 375, height: 812 }, true]]) {
  const ctx = await b.newContext({ viewport: vp, isMobile: mobile, hasTouch: mobile, deviceScaleFactor: mobile ? 2 : 1 });   // no extra headers: a custom Cache-Control header breaks the theme cross-origin fetches (CORS)
  const p = await ctx.newPage();
  const resp = await p.goto(url, { waitUntil: "domcontentloaded", timeout: 90000 });
  await p.addStyleTag({ content: ".scroll-trigger{opacity:1!important;transform:none!important;animation:none!important}" });
  await p.evaluate(async () => {
    document.querySelectorAll("img[loading=lazy]").forEach(i => i.loading = "eager");
    for (let y = 0; y < document.body.scrollHeight; y += 500) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
    window.scrollTo(0, 0);
    await Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; setTimeout(r, 6000); })));
  });
  await p.waitForTimeout(4000);
  const f = await p.evaluate(() => {
    const q = s => document.querySelector(s);
    const hero = q(".gslp-hero__in"), offer = q(".rblof");
    return {
      title: document.title, status_text: document.body.innerText.slice(0, 80),
      body_class: document.body.className.slice(0, 160),
      gsl_ref: !!q(".gsl-ref"), premium_markup: !!hero, premium_css_applied: hero ? getComputedStyle(hero).borderRadius : null,
      // v3 (2026-10-08) makes the mobile hero full-bleed (radius 0): the pill kicker radius is the premium probe there
      premium_kicker_radius: q(".gslp-kicker") ? getComputedStyle(q(".gslp-kicker")).borderRadius : null,
      premium_css_in_dom: [...document.querySelectorAll("style")].some(s => s.textContent.includes("--gp-forest")),
      offer_text: offer ? offer.innerText.replace(/\s+/g, " ").slice(0, 220) : null,
      old_v2_offer_copy: document.body.innerText.includes("Two Ingredients"),
      sticky: !!q("[data-gslp-sticky]"),
      imgs: document.images.length, broken: [...document.images].filter(i => i.getAttribute("src") && i.complete && !i.naturalWidth).map(i => i.src).slice(0, 5),   // theme placeholders with src="" are not ours
      overflow: document.documentElement.scrollWidth > innerWidth + 1, height: document.documentElement.scrollHeight,
      clipped: [...document.querySelectorAll(".gsl-ref *")].filter(e => {   // text cut off: own text wider than its box (offer pill 2026-10-09), scrollers excluded
      if (![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return false;
      const cs = getComputedStyle(e), r = e.getBoundingClientRect(); if (!r.width || cs.display === "none" || cs.visibility === "hidden" || cs.textOverflow === "ellipsis") return false;   // hidden sticky bar / deliberate ellipsis
      for (let a = e; a && a !== document.body; a = a.parentElement) if (/auto|scroll/.test(getComputedStyle(a).overflowX)) return false;   // swipe carousels are meant to run off-screen
      return e.scrollWidth > e.clientWidth + 1 || r.right > innerWidth + 1 || r.left < -1; }).map(e => (e.className || e.tagName) + ": " + e.textContent.trim().slice(0, 40)).slice(0, 5),
    palette: (() => { const q = s => document.querySelector(s), c = (s, p) => q(s) ? getComputedStyle(q(s))[p] : null;   // effective colors, for the pack-palette gate
      return { cta_bg: c(".gslp-hero .gslp-btn", "backgroundColor"), accent: c(".gslp-hero .rblha__accent", "color"), kicker: c(".gslp-kicker", "color"),
               topbar_bg: c(".rbltb", "backgroundColor"), pill_bg: c(".rblof__pill", "backgroundColor"), offer_cta_bg: c(".rblof a[href*='/products/']", "backgroundColor") }; })(),
    };
  });
  facts[name] = { http: resp.status(), ...f };
  if (name === "mobile" && facts.mobile.sticky) {   // (before the fullPage shot, which resizes the viewport) sticky CTA: hidden at top, shown between bridge and offer, hidden on the offer
    const st = () => p.evaluate(() => { const bar = document.querySelector("[data-gslp-sticky]"); const o = document.getElementById("gsl-offer"); const r = o && o.getBoundingClientRect();
      const rows = document.querySelectorAll(".rb-section--listicle-image-text"); const bt = rows[rows.length - 1].getBoundingClientRect().top;
      return bar.classList.contains("is-on") ? true : `off(scrollY=${Math.round(scrollY)} vh=${innerHeight} offerTop=${r && Math.round(r.top)} bridgeTop=${Math.round(bt)} rows=${rows.length} cls=${bar.className})`; });
    const y = await p.evaluate(() => { const abs = e => e.getBoundingClientRect().top + scrollY; const rows = document.querySelectorAll(".rb-section--listicle-image-text");
      return { bridge: abs(rows[rows.length - 1]), offer: abs(document.getElementById("gsl-offer") || document.querySelector(".rblof")) }; });
    const at = async v => { await p.evaluate(v => window.scrollTo(0, v), v); await p.waitForTimeout(1800); return st(); };   // storefront main thread is busy with apps: give the 400 ms check time
    facts.mobile.sticky_check = { top: await at(0), after_bridge: await at(Math.round((y.bridge + y.offer) / 2)), on_offer: await at(y.offer + 150) };
  }
  await p.evaluate(() => window.scrollTo(0, 0)); await p.waitForTimeout(800);
  await p.screenshot({ path: `${out}-${name}.png`, fullPage: true, timeout: 120000 });
  if (name === "desktop") {   // crop from the full page so the theme's sticky header never covers the offer box
    const r = await p.evaluate(() => { const e = document.querySelector(".rb-section--listicle-offer") || document.querySelector(".rblof"); if (!e) return null;
      const b = e.getBoundingClientRect(); return { x: 0, y: Math.max(0, b.top + scrollY), width: innerWidth, height: b.height }; });
    if (r) await p.screenshot({ path: `${out}-offer.png`, fullPage: true, clip: r, timeout: 120000 });
  }
  await ctx.close();
}
await b.close();
fs.writeFileSync(`${out}.json`, JSON.stringify(facts, null, 1));
console.log(JSON.stringify(facts, null, 1));

#!/usr/bin/env python3
"""Journal fidelity gate (store-agnostic copy): approved static template vs the live Liquid article (or the blog index vs the approved mock).
Store settings come from the profile JSON in $JOURNAL_PROFILE (keys domain, blog_handle, qa_blog_handle); without it the Cherish defaults apply.
Cherish original (kept as the history of the gate): ~/PATI/work/cherish-seo/fidelity/fidelity_gate.py.

Rule: the approved HTML is the truth. Any difference in the compared region = FAIL. No "close enough".
Spec: plans/261024-1953-cherish-shopify-live-launch/blog-templates-liquid-plan-261027-briefs.md part 2 section 1.
Checks per style x width: (a) pixel diff  (b) computed style + hover/focus + sticky  (c) DOM structure + order
(d) head + JSON-LD  (e) the template's own #rules-machine limits re-run on the live page.

Usage (see README.md):
  python3 -I fidelity_gate.py --theme <preview_theme_id> --pairs pairs.json
  python3 -I fidelity_gate.py --simulate --pairs pairs.json          # swap harness on MAIN, labelled SIMULATED
  python3 -I fidelity_gate.py --pairs index-pair.json --kind blog
  python3 -I fidelity_gate.py --selftest
"""
from __future__ import annotations

import os
import sys

# The default python3 on this Mac (uv 3.12) has no numpy/Pillow/playwright; /usr/bin/python3 (3.9) has all three in the
# user site, which `-I` hides. Re-run once under the interpreter that has them, keeping `python3 -I ...` working.
try:
    import numpy  # noqa: F401
    import PIL  # noqa: F401
    import playwright  # noqa: F401
except ImportError:
    if os.environ.get("FG_REEXEC") != "1":
        os.environ["FG_REEXEC"] = "1"
        os.execv("/usr/bin/python3", ["/usr/bin/python3", "-E"] + sys.argv)
    sys.exit("fidelity_gate: numpy, Pillow and playwright are required (/usr/bin/python3 has them)")

import argparse
import csv
import difflib
import json
import re
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
_PROFILE = json.loads(Path(os.environ["JOURNAL_PROFILE"]).expanduser().read_text()) if os.environ.get("JOURNAL_PROFILE") else {}
DOMAIN = _PROFILE.get("domain", "thecherishcompany.com")
BLOG = _PROFILE.get("blog_handle", "news")
QA_BLOG = _PROFILE.get("qa_blog_handle", "journal-qa")
SEO = Path(_PROFILE.get("work_dir", HERE.parent)).expanduser()  # holds day1/ (template copies), blog-index/ (mock); selftest + --simulate read them
RUNS = Path(_PROFILE.get("runs_dir", SEO / "fidelity" / "runs")).expanduser()  # run folders; never inside the skill
WIDTHS = (1440, 1100, 900, 600, 390)
VIEW_H = {390: 844}
DEFAULT_H = 900
SITE_HOSTS = (DOMAIN, "cdn.shopify.com", "fonts.googleapis.com", "fonts.gstatic.com", "shopify.com")
SCOPE_CLASSES = {"jn", "cw"}  # theme scope class (live) and the day-1 body scope class: not part of the comparison
SITEWIDE_TYPES = {"Organization", "WebSite"}  # sitewide JSON-LD printed by snippets/site-jsonld.liquid on every page: store chrome, not article
SIMULATED_HOST = _PROFILE.get("simulated_host", f"https://{DOMAIN}/blogs/{BLOG}/best-blanket-for-hot-sleepers")
PIXEL_THRESHOLD = 0.05
TILE = 200
TILE_MAX_FRAC = 0.0001  # 0.01 %
CLUSTER = 4

INJECT_CSS = ("*,*::before,*::after{transition:none!important;animation:none!important;scroll-behavior:auto!important;"
              "caret-color:transparent!important}")

# ---------------------------------------------------------------- properties

TEXT_PROPS = ["font-family", "font-size", "font-weight", "font-style", "font-variation-settings", "line-height", "letter-spacing",
              "text-transform", "text-decoration-line", "text-underline-offset", "text-align", "color"]
BOX_PROPS = ["background-color", "margin-top", "margin-right", "margin-bottom", "margin-left", "padding-top", "padding-right",
             "padding-bottom", "padding-left", "border-top-width", "border-top-style", "border-top-color", "border-right-width",
             "border-right-style", "border-right-color", "border-bottom-width", "border-bottom-style", "border-bottom-color",
             "border-left-width", "border-left-style", "border-left-color", "border-radius", "width", "max-width", "row-gap",
             "column-gap", "grid-template-columns", "display", "position", "top", "aspect-ratio", "object-fit",
             "visibility", "opacity", "transform", "box-shadow", "list-style-type", "overflow-x", "overflow-y", "float", "content"]
PSEUDO_PROPS = ["content", "display", "position", "left", "top", "width", "height", "color", "background-color", "font-family",
                "font-size", "font-weight", "line-height", "letter-spacing", "text-transform", "margin-top", "margin-bottom",
                "margin-left", "margin-right", "float", "border-top-width", "border-top-color", "padding-left"]
STATE_PROPS = ["color", "background-color", "outline-width", "outline-style", "outline-color", "outline-offset", "box-shadow",
               "text-decoration-line", "text-decoration-color", "text-decoration-style"]
ALL_PROPS = TEXT_PROPS + BOX_PROPS

ATTRS_KEEP = ["id", "href", "rel", "role", "loading", "width", "height", "alt", "src", "srcset", "sizes", "fetchpriority", "open",
              "data-l", "data-product", "start", "style", "tabindex", "scope", "target", "type", "aria-label", "aria-labelledby",
              "aria-hidden", "aria-expanded", "aria-controls", "aria-current", "aria-describedby", "aria-live"]

# ---------------------------------------------------------------- page JS

# One pass over the region: assigns data-fg to every element, returns the flat node list (elements + text nodes).
COLLECT_JS = r"""(cfg) => {
  const { sets, scope, textProps, boxProps, pseudoProps, attrs, regionTop } = cfg;
  let roots = [], kind = null;
  for (const set of sets) {
    const first = document.querySelector(set[0]);
    if (first) { roots = set.map(s => [...document.querySelectorAll(s)]).map(l => l[l.length - 1]).filter(Boolean); kind = set[0]; break; }
  }
  if (!roots.length) return { error: 'no region root found (tried ' + sets.map(s => s[0]).join(', ') + ')' };
  roots.sort((a, b) => (a.compareDocumentPosition(b) & 4) ? -1 : 1);
  const sx = window.scrollX, sy = window.scrollY;
  const top0 = Math.min(...roots.filter(r => r.getClientRects().length).map(r => r.getBoundingClientRect().top + sy));  // a display:none .stick (>= 1100) has top 0 and must not set the origin (lane C)
  const bot0 = Math.max(...roots.filter(r => !r.matches('.stick')).map(r => r.getBoundingClientRect().bottom + sy));
  const SKIP = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'LINK', 'META']);
  const norm = s => s.replace(/[ \t\r\n\f\v]+/g, ' ');
  const cleanCls = e => [...(e.classList || [])].filter(c => !scope.includes(c));
  const tagOf = e => (e.tagName === 'MAIN' && e.id === 'post') ? 'div' : e.tagName.toLowerCase();   // S1 (coordinator 2026-10-27): main#post == div#post, structure only; the store layout already prints <main id="main">
  const pathOf = e => {
    const parts = [];
    for (let n = e; n && n.nodeType === 1 && n !== document.body; n = n.parentElement) {
      let s = tagOf(n);
      if (n.id) s += '#' + n.id;
      const c = cleanCls(n).slice(0, 2); if (c.length) s += '.' + c.join('.');
      const sib = n.parentElement ? [...n.parentElement.children].filter(x => x.tagName === n.tagName) : [];
      if (sib.length > 1) s += ':nth-of-type(' + (sib.indexOf(n) + 1) + ')';
      parts.unshift(s);
      if (roots.includes(n)) break;
    }
    return parts.join(' > ');
  };
  const out = []; let idx = 0;
  const walk = (el, depth) => {
    if (SKIP.has(el.tagName)) return;
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    el.setAttribute('data-fg', String(idx));
    const node = { k: 'el', i: idx++, d: depth, tag: tagOf(el), cls: cleanCls(el), path: pathOf(el), attrs: {}, cs: {}, ps: {},
      box: { x: r.left + sx, y: (!el.getClientRects().length || (r.width === 0 && r.height === 0)) ? 0 : (el.closest('.stick') ? r.top : r.top + sy - top0), w: r.width, h: r.height }, own: '' };  // lane C: display:none boxes and fixed bars have no place in the region (their y depended on the store header height)
    for (const a of attrs) if (el.hasAttribute(a)) node.attrs[a] = el.getAttribute(a);
    for (const a of el.attributes) if (a.name.startsWith('data-') && !['data-fg', 'data-l', 'data-product'].includes(a.name)) node.attrs[a.name] = a.value;
    for (const p of textProps) node.cs[p] = cs.getPropertyValue(p);
    for (const p of boxProps) node.cs[p] = cs.getPropertyValue(p);
    for (const ps of ['::before', '::after']) {
      const pc = getComputedStyle(el, ps);
      if (pc.getPropertyValue('content') !== 'none' && pc.getPropertyValue('content') !== 'normal') {
        const o = {}; for (const p of pseudoProps) o[p] = pc.getPropertyValue(p); node.ps[ps] = o;
      }
    }
    out.push(node);
    if (el.namespaceURI === 'http://www.w3.org/2000/svg') return;
    for (const ch of el.childNodes) {
      if (ch.nodeType === 3) {
        const t = norm(ch.textContent);
        if (t.trim()) { node.own += (node.own ? ' ' : '') + t.trim(); out.push({ k: 'tx', d: depth + 1, text: t.trim(), pre: /^\s/.test(t), post: /\s$/.test(t) }); }
      } else if (ch.nodeType === 1) walk(ch, depth + 1);
    }
  };
  for (const r of roots) { r.__fgroot = true; walk(r, 0); }
  return { kind, nodes: out, region: { top: top0, bottom: bot0, h: bot0 - top0, width: document.documentElement.clientWidth, scrollW: document.documentElement.scrollWidth,
           docH: document.documentElement.scrollHeight }, imgs: roots.flatMap(r => [...r.querySelectorAll('img')]).filter(i => i.getClientRects().length).map(i => ({ s: (i.currentSrc || i.src).split('/').pop().slice(0, 60), ok: i.complete && i.naturalWidth > 0 })),
           rootSelectors: roots.map(r => r.tagName.toLowerCase() + (r.className ? '.' + String(r.className).split(' ')[0] : '')) };
}"""

FONTS_JS = r"""async () => {
  const sha = async buf => [...new Uint8Array(await crypto.subtle.digest('SHA-256', buf))].map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 12);
  const out = [];
  for (const st of document.querySelectorAll('style')) {
    for (const m of st.textContent.matchAll(/@font-face\s*\{[^}]*?font-family:\s*['"]?([^;'"]+)['"]?;[^}]*?url\((data:[^)]+)\)/g)) {
      try { const b = atob(m[2].split(',')[1]); const a = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i); out.push({ name: m[1], sha: await sha(a), bytes: a.length }); } catch (e) {}
    }
  }
  for (const e of performance.getEntriesByType('resource')) {
    if (!/\.woff2?(\?|$)/.test(e.name)) continue;
    try { const buf = await (await fetch(e.name)).arrayBuffer(); out.push({ name: e.name.split('/').pop().split('?')[0], sha: await sha(buf), bytes: buf.byteLength }); } catch (err) { out.push({ name: e.name.split('/').pop(), sha: 'fetch-failed', bytes: 0 }); }
  }
  return out;
}"""

HEAD_JS = r"""() => {
  const m = (sel, attr) => { const e = document.querySelector(sel); return e ? e.getAttribute(attr) : null; };
  const metas = {};
  for (const e of document.querySelectorAll('meta[property], meta[name]')) { const k = e.getAttribute('property') || e.getAttribute('name'); (metas[k] = metas[k] || []).push(e.getAttribute('content')); }
  return { title: document.title, description: m('meta[name="description"]', 'content'), canonical: m('link[rel="canonical"]', 'href'),
    ogType: m('meta[property="og:type"]', 'content'), robots: m('meta[name="robots"]', 'content'),
    ld: [...document.querySelectorAll('script[type="application/ld+json"]')].map(s => s.textContent), metas,
    rules: (document.getElementById('rules-machine') || {}).textContent || null };
}"""

RULES_JS = r"""(m) => {
  const art = (document.querySelector('main#post article') || document.querySelector('article')).cloneNode(true);
  art.querySelectorAll('.spec, script, style, template, noscript').forEach(e => e.remove());
  const words = (art.textContent.match(/[A-Za-z0-9][A-Za-z0-9'’-]*/g) || []).length;
  const h2s = [...art.querySelectorAll('h2')].map(h => h.textContent.trim());
  const qh2 = h2s.filter(t => t.endsWith('?')).length;
  const cards = art.querySelectorAll('.pcard').length;
  const imgs = document.querySelectorAll('article img, .rail img, section.band img').length;
  const ext = [...art.querySelectorAll('a[href^="http"]')].map(a => a.href);
  const authority = ext.filter(h => /nih\.gov|ncbi|pubmed|medlineplus|nidirect|cdc\.gov/.test(h)).length;
  const journal = art.querySelectorAll('a[href^="/blogs/news/"]').length;
  const tables = art.querySelectorAll('table').length, rows = art.querySelectorAll('table tbody tr').length;
  const sources = art.querySelectorAll('.sources a[href^="http"]').length;
  const h1 = (document.querySelector('h1') || { textContent: '' }).textContent.trim();
  const faqVis = [...document.querySelectorAll('.faq summary h3')].map(h => h.textContent.trim());
  return { words, h2: h2s.length, qh2, cards, imgs, authority, journal, tables, rows, sources, h1len: h1.length, faqVis };
}"""
RULES_JS = RULES_JS.replace("/blogs/news/", f"/blogs/{BLOG}/")  # store profile: blog handle

CHROME_JS = r"""() => {
  const sel = document.querySelector('.layout') ? ['.layout', 'section.band'] : document.querySelector('main#journal') ? ['main#journal', 'section.band'] : ['article.article'];
  const roots = sel.map(s => [...document.querySelectorAll(s)].pop()).filter(Boolean);
  if (!roots.length) return { above: '', below: '', aboveH: 0, belowH: 0 };
  const vis = n => { const p = n.parentElement; if (!p || ['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'TITLE'].includes(p.tagName)) return false; const c = getComputedStyle(p); return c.display !== 'none' && c.visibility !== 'hidden'; };
  const inside = n => roots.some(r => r.contains(n)) || (n.parentElement && n.parentElement.closest('.stick, dialog'));
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); const above = [], below = []; let n, seen = false;
  while ((n = w.nextNode())) {
    if (!n.textContent.trim() || !vis(n)) continue;
    if (inside(n)) { seen = true; continue; }
    (seen ? below : above).push(n.textContent.trim());
  }
  const r1 = roots[0].getBoundingClientRect(), r2 = roots[roots.length - 1].getBoundingClientRect();
  return { above: above.join(' | ').slice(0, 240), below: below.join(' | ').slice(0, 240), aboveH: Math.round(r1.top + scrollY), belowH: Math.round(document.documentElement.scrollHeight - (r2.bottom + scrollY)) };
}"""

STICKY_JS = r"""(cfg) => {
  const hero = document.querySelector('figure.hero') || document.querySelector('.article__hero');
  const stick = document.querySelector('.stick'), rail = document.querySelector('.rail-in'), layout = document.querySelector('.layout');
  const rs = x => Math.round(x * 2) / 2;
  const out = {};
  const fixedChrome = () => [...document.querySelectorAll('body *')].filter(e => ['fixed', 'sticky'].includes(getComputedStyle(e).position)
      && !e.closest('.layout, .stick, section.band, dialog, [class*="shopify-pc__banner"], #PBarNextFrameWrapper, [id*="preview-bar"]') && e.getClientRects().length && !e.closest('[hidden]'))
      .map(e => ({ el: e.tagName.toLowerCase() + '.' + String(e.className).split(' ')[0], r: e.getBoundingClientRect() })).filter(o => o.r.height > 0 && o.r.width > 0);
  if (cfg.mode === 'stick') {
    const b = hero ? hero.getBoundingClientRect().bottom + scrollY : 600;
    window.scrollTo(0, b + 60);
    return new Promise(res => setTimeout(() => {
      if (!stick) return res({ present: false });
      const c = getComputedStyle(stick), r = stick.getBoundingClientRect();
      res({ present: true, transform: c.transform, visibility: c.visibility, display: c.display, ariaHidden: stick.getAttribute('aria-hidden'), on: stick.classList.contains('on'),
        bottom: rs(innerHeight - r.bottom), h: rs(r.height), w: rs(r.width), tabindex: (stick.querySelector('a') || {}).tabIndex });
    }, 500));
  }
  if (cfg.mode === 'rail') {
    if (!rail || !layout) return { present: false };
    const L = layout.getBoundingClientRect(); const y = L.top + scrollY + (L.height - innerHeight) / 2;
    // lane A (A-fix S6): deterministic header state. Scroll DOWN into place (the store header hides, as for a reader), read the rail (= the template's state),
    // then scroll UP 40 px (the store header returns): the rail card must not sit under it.
    window.scrollTo(0, Math.max(0, y - 120));
    return new Promise(res => setTimeout(() => { window.scrollTo(0, y); setTimeout(() => {
      const c = getComputedStyle(rail), r = rail.getBoundingClientRect(); const first = { top: c.top, rectTop: rs(r.top), rectH: rs(r.height), position: c.position };
      window.scrollBy(0, -40);
      setTimeout(() => {
        const r2 = rail.getBoundingClientRect();
        const over = fixedChrome().filter(f => f.r.bottom > r2.top && f.r.top < r2.bottom && f.r.right > r2.left && f.r.left < r2.right).map(f => f.el);
        res({ present: true, position: first.position, top: first.top, rectTop: first.rectTop, rectH: first.rectH, chromeOverlap: over.join(',') });
      }, 700);
    }, 500); }, 300));
  }
  return {};
}"""

ISOLATE_JS = r"""() => {
  const roots = [...document.querySelectorAll('[data-fg]')].filter(e => e.__fgroot);
  const keep = new Set(); for (const r of roots) for (let n = r; n; n = n.parentElement) keep.add(n);
  for (const el of keep) { if (roots.includes(el)) continue; for (const c of el.children) if (!keep.has(c)) c.style.setProperty('display', 'none', 'important'); }
  for (const e of document.querySelectorAll('dialog, [role=dialog]')) if (!keep.has(e)) e.style.setProperty('display', 'none', 'important');
  window.scrollTo(0, 0);
  const t = Math.min(...roots.map(r => r.getBoundingClientRect().top + scrollY));
  const b = Math.max(...roots.filter(r => !r.matches('.stick')).map(r => r.getBoundingClientRect().bottom + scrollY));
  return { top: t, bottom: b };
}"""

# complete != painted. ISOLATE_JS and the rail/stick scroll re-lay out the page, so a srcset image can pick a new candidate and
# show blank until it arrives (2026-11-04: template-side .pick photo captured blank, 6-10 tile pixel FAIL on slots 1 and 2).
# Called right before every screenshot: wait for every image to finish, decode it, then two frames. No threshold changes.
PAINT_JS = r"""async () => {
  const t0 = Date.now();
  while (Date.now() - t0 < 8000 && [...document.images].some(i => !i.complete)) await new Promise(r => setTimeout(r, 100));
  await Promise.all([...document.images].filter(i => i.complete && i.naturalWidth > 0).map(i => i.decode().catch(() => {})));
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  return [...document.images].filter(i => !i.complete).length;
}"""

IMAGES_JS = r"""async () => {
  for (const i of document.images) { if (i.loading === 'lazy') i.loading = 'eager'; i.decoding = 'sync'; }
  const h = document.documentElement.scrollHeight;
  for (let y = 0; y < h; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 30)); }
  window.scrollTo(0, 0);
  const t0 = Date.now();
  while (Date.now() - t0 < 12000) {
    const pend = [...document.images].filter(i => !i.complete);
    if (!pend.length) break;
    await new Promise(r => setTimeout(r, 100));
  }
  await document.fonts.ready;
  return { total: document.images.length, incomplete: [...document.images].filter(i => !i.complete).length,
           broken: [...document.images].filter(i => i.complete && i.naturalWidth === 0).map(i => i.src.slice(-60)) };
}"""

# ---------------------------------------------------------------- helpers


def hnorm(u):
    """Normalise an href/src: drop the store host and the preview/version query noise."""
    if u is None:
        return None
    try:
        p = urlparse(u)
    except Exception:
        return u
    if p.netloc and p.netloc.endswith(DOMAIN) and not p.path.startswith("/cdn/"):
        u = p.path + ("?" + p.query if p.query else "") + ("#" + p.fragment if p.fragment else "")
        p = urlparse(u)
    if u.startswith(f"/blogs/{QA_BLOG}"):  # QA staging copy: same article under the real blog
        u = f"/blogs/{BLOG}" + u[len(f"/blogs/{QA_BLOG}"):]
        p = urlparse(u)
    if p.query:
        q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k not in ("preview_theme_id", "v", "pr_prod_strat", "pr_rec_id", "pr_rec_pid", "pr_ref_pid", "pr_seq")]
        u = p._replace(query=urlencode(q)).geturl()
    return u


def src_norm(u):
    """image src: file name + width param only (host, folder, ?v= differ between template CDN and theme CDN)."""
    if u is None:
        return None
    p = urlparse(u)
    q = dict(parse_qsl(p.query))
    name = re.sub(r"_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?=\.\w+$)", "", p.path.rsplit("/", 1)[-1])  # Shopify adds _<uuid> when it copies a file into /articles/ (lane C)
    return name + (("?width=" + q["width"]) if "width" in q else "")


def srcset_norm(s):
    if s is None:
        return None
    parts = [x.strip() for x in s.split(",") if x.strip()]
    return ", ".join(src_norm(x.rsplit(" ", 1)[0]) + " " + x.rsplit(" ", 1)[1] if " " in x else src_norm(x) for x in parts)


def num_round(v):
    return re.sub(r"-?\d*\.\d+", lambda m: ("%.2f" % float(m.group())).rstrip("0").rstrip("."), v) if isinstance(v, str) else v


def color_norm(v):
    m2 = re.fullmatch(r"color\(srgb ([\d.]+) ([\d.]+) ([\d.]+)(?: / ([\d.]+))?\)", v.strip()) if isinstance(v, str) else None
    if m2:
        r, g, b = (int(round(float(m2.group(i)) * 255)) for i in (1, 2, 3))
        a = round(float(m2.group(4)), 2) if m2.group(4) else 1.0
        return "#%02X%02X%02X" % (r, g, b) + ("" if a == 1.0 else "/%s" % a)
    m = re.fullmatch(r"rgba?\(([^)]*)\)", v.strip()) if isinstance(v, str) else None
    if not m:
        return v
    p = [x.strip() for x in m.group(1).replace("/", ",").split(",")]
    try:
        r, g, b = (int(round(float(x))) for x in p[:3])
        a = round(float(p[3]), 2) if len(p) > 3 else 1.0
    except ValueError:
        return v
    return "#%02X%02X%02X" % (r, g, b) + ("" if a == 1.0 else "/%s" % a)


def pv(prop, v):
    if v is None:
        return ""
    if "color" in prop or prop == "color":
        # box-shadow / border colours embed colours: normalise whole rgb() tokens
        return re.sub(r"(?:rgba?|color)\([^)]*\)", lambda m: color_norm(m.group()), v)
    if prop == "font-family":
        return v.split(",")[0].strip().strip("\"'")
    if prop == "box-shadow":
        return re.sub(r"rgba?\([^)]*\)", lambda m: color_norm(m.group()), num_round(v))
    return num_round(v)


def rs(x):
    return round(x * 2) / 2


def tn(text):
    return text.replace(" ", "\\u00a0")


def node_line(n):
    a = n["attrs"]
    bits = [n["tag"]]
    if n["cls"]:
        bits.append("." + ".".join(n["cls"]))
    if "id" in a:
        bits.append("#" + a["id"])
    for k in ATTRS_KEEP:
        if k == "id" or k not in a:
            continue
        v = a[k]
        if k == "href":
            v = hnorm(v)
        elif k == "src":
            v = src_norm(v)
        elif k == "srcset":
            v = srcset_norm(v)
        elif k == "style":
            v = re.sub(r"\s+", " ", v).strip()
        bits.append("[%s=%s]" % (k, v))
    for k in sorted(a):
        if k.startswith("data-") and k not in ("data-l", "data-product"):
            bits.append("[%s=%s]" % (k, a[k]))
    return "  " * n["d"] + " ".join(bits)


def serialise(nodes):
    lines = []
    for n in nodes:
        if n["k"] == "el":
            lines.append(node_line(n))
        else:
            lines.append("  " * n["d"] + '"' + tn(n["text"]) + '"')
    return lines


def sig(n):
    return n["tag"] + "|" + ".".join(n["cls"])


# ---------------------------------------------------------------- pixel diff (pixelmatch port)


def _yiq(rgb):
    r, g, b = rgb[..., 0].astype(np.float64), rgb[..., 1].astype(np.float64), rgb[..., 2].astype(np.float64)
    y = r * 0.29889531 + g * 0.58662247 + b * 0.11448223
    i = r * 0.59597799 - g * 0.27417610 - b * 0.32180189
    q = r * 0.21147017 - g * 0.52261711 + b * 0.31114694
    return y, i, q


def color_delta_arr(a, b):
    ya, ia, qa = _yiq(a)
    yb, ib, qb = _yiq(b)
    y, i, q = ya - yb, ia - ib, qa - qb
    return 0.5053 * y * y + 0.299 * i * i + 0.1957 * q * q


def _y_signed(img, x1, y1, x2, y2):
    a = img[y1, x1].astype(np.float64)
    b = img[y2, x2].astype(np.float64)
    return (a[0] * 0.29889531 + a[1] * 0.58662247 + a[2] * 0.11448223) - (b[0] * 0.29889531 + b[1] * 0.58662247 + b[2] * 0.11448223)


def _many_siblings(img, x1, y1):
    h, w = img.shape[:2]
    x0, y0, x2, y2 = max(x1 - 1, 0), max(y1 - 1, 0), min(x1 + 1, w - 1), min(y1 + 1, h - 1)
    zeroes = 1 if (x1 in (x0, x2) or y1 in (y0, y2)) else 0
    for x in range(x0, x2 + 1):
        for y in range(y0, y2 + 1):
            if x == x1 and y == y1:
                continue
            if (img[y1, x1] == img[y, x]).all():
                zeroes += 1
            if zeroes > 2:
                return True
    return False


def _antialiased(img, x1, y1, img2):
    h, w = img.shape[:2]
    x0, y0, x2, y2 = max(x1 - 1, 0), max(y1 - 1, 0), min(x1 + 1, w - 1), min(y1 + 1, h - 1)
    zeroes = 1 if (x1 in (x0, x2) or y1 in (y0, y2)) else 0
    mn = mx = 0.0
    minx = miny = maxx = maxy = None
    for x in range(x0, x2 + 1):
        for y in range(y0, y2 + 1):
            if x == x1 and y == y1:
                continue
            d = _y_signed(img, x1, y1, x, y)
            if d == 0:
                zeroes += 1
                if zeroes > 2:
                    return False
            elif d < mn:
                mn, minx, miny = d, x, y
            elif d > mx:
                mx, maxx, maxy = d, x, y
    if mn == 0 or mx == 0:
        return False
    return ((_many_siblings(img, minx, miny) and _many_siblings(img2, minx, miny))
            or (_many_siblings(img, maxx, maxy) and _many_siblings(img2, maxx, maxy)))


def pixel_diff(a_img, b_img):
    """Returns (ok, failing tiles list, diff PNG as PIL image, stats). Images are PIL RGB; heights are padded with magenta."""
    A, B = np.array(a_img.convert("RGB")), np.array(b_img.convert("RGB"))
    H, W = max(A.shape[0], B.shape[0]), max(A.shape[1], B.shape[1])

    def pad(X):
        o = np.empty((H, W, 3), np.uint8)
        o[:] = (255, 0, 255)
        o[:X.shape[0], :X.shape[1]] = X
        return o
    A, B = pad(A), pad(B)
    max_delta = 35215 * PIXEL_THRESHOLD * PIXEL_THRESHOLD
    diff = np.zeros((H, W), bool)
    for y0 in range(0, H, 800):  # chunked: a 9,000 px tall float64 delta is ~300 MB per array
        diff[y0:y0 + 800] = color_delta_arr(A[y0:y0 + 800], B[y0:y0 + 800]) > max_delta
    n = int(diff.sum())
    if 0 < n <= 60000:
        ys, xs = np.nonzero(diff)
        for y, x in zip(ys, xs):
            if _antialiased(A, x, y, B) or _antialiased(B, x, y, A):
                diff[y, x] = False
    n_final = int(diff.sum())
    # tiles
    tiles = []
    for ty in range(0, H, TILE):
        for tx in range(0, W, TILE):
            t = diff[ty:ty + TILE, tx:tx + TILE]
            c = int(t.sum())
            if c > t.size * TILE_MAX_FRAC:
                tiles.append({"x": tx, "y": ty, "px": c, "frac": round(c / t.size, 5)})
    # 4x4 solid clusters over the whole image
    ii = np.pad(diff.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    win = ii[CLUSTER:, CLUSTER:] - ii[:-CLUSTER, CLUSTER:] - ii[CLUSTER:, :-CLUSTER] + ii[:-CLUSTER, :-CLUSTER]
    clusters = int((win == CLUSTER * CLUSTER).sum())
    # diff overlay: faint template, red diff
    ov = (A.astype(np.float32) * 0.25 + 191).astype(np.uint8)
    ov[diff] = (255, 0, 0)
    ok = not tiles and clusters == 0 and A.shape == B.shape and a_img.size == b_img.size
    return ok, tiles, Image.fromarray(ov), {"diff_px": n_final, "raw_diff_px": n, "clusters": clusters, "size_tpl": a_img.size, "size_live": b_img.size}


# ---------------------------------------------------------------- browser side


def route_filter(ctx):
    pat = re.compile(r"^https?://(?!(%s)).*" % "|".join(re.escape(h) for h in SITE_HOSTS).replace(re.escape(DOMAIN), r"([^/]+\.)?" + re.escape(DOMAIN)))
    ctx.route(pat, lambda r: r.abort() if r.request.resource_type in ("script", "xhr", "fetch", "ping", "other", "websocket", "eventsource") else r.continue_())


def new_context(browser, width):
    # bypass_csp: the live store sends a nonce-only style-src CSP; without it the gate's own inject CSS (add_style_tag) crashes
    # the cell on the real URL (slot 5, 2026-11-04). It changes only what the gate may inject, never what the page renders.
    ctx = browser.new_context(viewport={"width": width, "height": VIEW_H.get(width, DEFAULT_H)}, device_scale_factor=1, bypass_csp=True,
                              reduced_motion="reduce", locale="en-US", timezone_id="America/New_York",
                              user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36")
    route_filter(ctx)
    return ctx


def force_state(cdp, node_id, states):
    cdp.send("CSS.forcePseudoState", {"nodeId": node_id, "forcedPseudoClasses": states})


def hover_focus(page, cdp, node_count_ids):
    """For every a/button/summary in the region (data-fg set): read STATE_PROPS under forced :hover and :focus-visible."""
    ids = page.evaluate("[...document.querySelectorAll('[data-fg]')].filter(e => e.matches('a,button,summary')).map(e => +e.getAttribute('data-fg'))")
    doc = cdp.send("DOM.getDocument", {"depth": 0})
    res = {}
    read = "(i) => { const e = document.querySelector('[data-fg=\"' + i + '\"]'); const c = getComputedStyle(e); return Object.fromEntries(%s.map(p => [p, c.getPropertyValue(p)])); }" % json.dumps(STATE_PROPS)
    for i in ids:
        q = cdp.send("DOM.querySelector", {"nodeId": doc["root"]["nodeId"], "selector": '[data-fg="%d"]' % i})
        nid = q["nodeId"]
        if not nid:
            continue
        r = {}
        for st in ("hover", "focus-visible"):
            force_state(cdp, nid, [st])
            r[st] = page.evaluate(read, i)
            force_state(cdp, nid, [])
        res[i] = r
    return res


def prepare(page, mutate=None):
    page.add_style_tag(content=INJECT_CSS)
    page.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close && d.close())")
    if mutate:
        page.evaluate(mutate)
        page.wait_for_timeout(150)
    img = page.evaluate(IMAGES_JS)
    page.wait_for_timeout(250)
    return img


def swap_js(art, body):
    return """() => {
      document.querySelector('.article__title').textContent = %s;
      const m = document.querySelector('.article__meta'); m.innerHTML = '<time>October 28, 2026</time> <span aria-hidden="true">·</span> <span>The Cherish Company</span>';
      const h = document.querySelector('.article__hero img'); if (h) { h.removeAttribute('srcset'); h.src = %s; h.alt = %s; }
      document.querySelector('.article__content').innerHTML = %s;
      document.title = %s;
    }""" % (json.dumps(art["title"]), json.dumps(art["img"] + ("&" if "?" in art["img"] else "?") + "width=1440"), json.dumps(art.get("alt") or ""), json.dumps(body), json.dumps(art.get("seo_title", art["title"])))


CHALLENGE = ("browser verification", "verify your browser")

def goto_past_challenge(page, source, waits=(30, 60, 120)):
    """Load `source`. Shopify bot protection answers a busy headless browser with a "Browser verification" page (HTTP 403, sometimes
    200/404), which has no article: 2026-11-04 it showed as "no region root found" and robots=''. Back off and reload; if the store still
    challenges, raise a named error (a FAIL, never a pass). Local files never see it."""
    for wait in (0,) + tuple(waits):
        if wait:
            page.wait_for_timeout(wait * 1000)
        r = page.goto(source, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(600)
        title = (page.title() or "").lower()
        if not any(c in title for c in CHALLENGE) and not (r and r.status in (403, 429)):
            return r
    raise RuntimeError(f"store bot challenge: HTTP {r.status if r else 0} '{page.title()}' after {len(waits)} back-offs (not a page difference)")

def capture_side(browser, width, source, cfg, out_dir, side, mutate=None):
    """Load one side, collect everything. Returns a dict (JSON-able) and writes <side>.png (+ crops)."""
    ctx = new_context(browser, width)
    page = ctx.new_page()
    res = {"side": side, "url": source}
    try:
        goto_past_challenge(page, source)
        res["images"] = prepare(page, mutate)
        res["head"] = page.evaluate(HEAD_JS)
        res["chrome"] = page.evaluate(CHROME_JS)
        res["fonts"] = page.evaluate(FONTS_JS)
        # sticky tests before anything is hidden: they must see the real chrome
        if width < 1100:
            res["stick"] = page.evaluate(STICKY_JS, {"mode": "stick"})
            page.evaluate("window.scrollTo(0,0)")
            page.wait_for_timeout(200)
        else:
            res["rail"] = page.evaluate(STICKY_JS, {"mode": "rail"})
            page.evaluate("window.scrollTo(0,0)")
            page.wait_for_timeout(200)
        page.evaluate(PAINT_JS)  # the rail/stick scroll can start new srcset fetches: collect only after they land (selftest control 8)
        coll = page.evaluate(COLLECT_JS, {"sets": cfg["root_sets"], "scope": sorted(SCOPE_CLASSES), "textProps": TEXT_PROPS, "boxProps": BOX_PROPS,
                                          "pseudoProps": PSEUDO_PROPS, "attrs": ATTRS_KEEP, "regionTop": 0})
        if "error" in coll:
            res["error"] = coll["error"]
            return res
        res["coll"] = coll
        res["rules"] = page.evaluate(RULES_JS, None) if cfg.get("rules", True) else None
        cdp = ctx.new_cdp_session(page)
        cdp.send("DOM.enable")
        cdp.send("CSS.enable")
        res["states"] = hover_focus(page, cdp, None)
        # isolate the region and capture it
        iso = page.evaluate(ISOLATE_JS)
        page.wait_for_timeout(150)
        top = int(iso["top"])
        height = int(round(iso["bottom"])) - top
        res["iso"] = iso
        res["png"] = str(out_dir / (side + ".png"))
        shoot(page, top, height, width, out_dir / (side + ".png"))
        # sticky crops (isolated page: same background under both)
        if width < 1100 and res.get("stick", {}).get("present"):
            hero_b = page.evaluate("(() => { const h = document.querySelector('figure.hero'); return h ? h.getBoundingClientRect().bottom + scrollY : 600; })()")
            page.evaluate("y => window.scrollTo(0, y)", hero_b + 60)
            page.wait_for_timeout(450)
            r = page.evaluate("(() => { const s = document.querySelector('.stick'); const b = s.getBoundingClientRect(); return {x: b.left, y: b.top, w: b.width, h: b.height}; })()")
            if r["h"] > 0 and r["w"] > 0 and r["y"] < page.viewport_size["height"]:
                page.evaluate(PAINT_JS)
                page.screenshot(path=str(out_dir / (side + "-stick.png")), clip={"x": r["x"], "y": r["y"], "width": r["w"], "height": min(r["h"], page.viewport_size["height"] - r["y"])})
                res["stick_png"] = str(out_dir / (side + "-stick.png"))
        if width >= 1100 and res.get("rail", {}).get("present"):
            page.evaluate("() => { const L = document.querySelector('.layout').getBoundingClientRect(); window.scrollTo(0, L.top + scrollY + (L.height - innerHeight) / 2); }")
            page.wait_for_timeout(450)
            r = page.evaluate("(() => { const s = document.querySelector('.rail-in'); const b = s.getBoundingClientRect(); return {x: b.left, y: b.top, w: b.width, h: b.height}; })()")
            vh = page.viewport_size["height"]
            if r["h"] > 0 and 0 <= r["y"] < vh:
                page.evaluate(PAINT_JS)
                page.screenshot(path=str(out_dir / (side + "-rail.png")), clip={"x": r["x"], "y": r["y"], "width": r["w"], "height": min(r["h"], vh - r["y"])})
                res["rail_png"] = str(out_dir / (side + "-rail.png"))
        return res
    finally:
        ctx.close()


def shoot(page, top, height, width, path, chunk=6000):
    parts = []
    y = 0
    while y < height:
        h = min(chunk, height - y)
        tmp = str(path) + ".part.png"
        page.evaluate(PAINT_JS)
        page.screenshot(path=tmp, full_page=True, clip={"x": 0, "y": top + y, "width": width, "height": h})
        parts.append(Image.open(tmp).convert("RGB").copy())
        y += h
    os.path.exists(str(path) + ".part.png") and os.remove(str(path) + ".part.png")
    img = Image.new("RGB", (width, max(height, 1)), (255, 255, 255))
    y = 0
    for p in parts:
        img.paste(p, (0, y))
        y += p.size[1]
    img.save(path)


# ---------------------------------------------------------------- comparison


def align(tn_, ln_):
    """Pair elements of both sides: structure signature first, then (tag, own text) for the leftovers."""
    te = [n for n in tn_ if n["k"] == "el"]
    le = [n for n in ln_ if n["k"] == "el"]
    sm = difflib.SequenceMatcher(None, [sig(n) for n in te], [sig(n) for n in le], autojunk=False)
    pairs, used_t, used_l = [], set(), set()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                pairs.append((te[i1 + k], le[j1 + k], "structure"))
                used_t.add(i1 + k)
                used_l.add(j1 + k)
    # leftovers by tag + own text
    by_text = {}
    for j, n in enumerate(le):
        if j not in used_l and n["own"]:
            by_text.setdefault((n["tag"], n["own"]), []).append(j)
    for i, n in enumerate(te):
        if i in used_t or not n["own"]:
            continue
        c = by_text.get((n["tag"], n["own"]))
        if c:
            j = c.pop(0)
            pairs.append((n, le[j], "text"))
            used_t.add(i)
            used_l.add(j)
    missing = [te[i] for i in range(len(te)) if i not in used_t]
    extra = [le[j] for j in range(len(le)) if j not in used_l]
    pairs.sort(key=lambda p: p[0]["i"])
    return pairs, missing, extra


def brief(n):
    c = n["cs"]
    return "%s %s/%s ls %s %s align %s %gx%g" % (pv("font-family", c.get("font-family")), c.get("font-size"), c.get("line-height"), c.get("letter-spacing"),
                                              pv("color", c.get("color")), c.get("text-align"), rs(n["box"]["w"]), rs(n["box"]["h"]))


def style_rows(pairs, missing, extra, t_states, l_states, width):
    rows = []

    def add(sel, text, prop, a, b, note=""):
        rows.append({"width": width, "selector": sel, "text": text[:40], "property": prop, "tpl": a, "live": b, "note": note})
    prev_dy = 0
    for t, l, how in pairs:
        sel = t["path"]
        tx = t["own"]
        if how == "text":
            add(sel, tx, "(match)", "structure differs", l["path"], "paired by tag+text")
        for p in ALL_PROPS:
            a, b = pv(p, t["cs"].get(p)), pv(p, l["cs"].get(p))
            if a != b:
                add(sel, tx, p, a, b)
        # boxes: y only where the shift starts (every later element repeats the same offset)
        tb, lb = t["box"], l["box"]
        for k in ("x", "w", "h"):
            if rs(tb[k]) != rs(lb[k]):
                add(sel, tx, k, "%gpx" % rs(tb[k]), "%gpx" % rs(lb[k]))
        dy = rs(lb["y"]) - rs(tb["y"])
        if dy != prev_dy:
            add(sel, tx, "y", "%gpx" % rs(tb["y"]), "%gpx" % rs(lb["y"]), "layout shift starts here (Δ %+g px)" % dy)
            prev_dy = dy
        for ps in set(t["ps"]) | set(l["ps"]):
            ta, la = t["ps"].get(ps), l["ps"].get(ps)
            if ta is None or la is None:
                add(sel + ps, tx, "content", ta["content"] if ta else "(none)", la["content"] if la else "(none)")
                continue
            for p in PSEUDO_PROPS:
                a, b = pv(p, ta.get(p)), pv(p, la.get(p))
                if a != b:
                    add(sel + ps, tx, p, a, b)
        ts, ls = t_states.get(str(t["i"])) or t_states.get(t["i"]), l_states.get(str(l["i"])) or l_states.get(l["i"])
        if ts and ls:
            for st in ("hover", "focus-visible"):
                for p in STATE_PROPS:
                    a, b = pv(p, ts[st].get(p)), pv(p, ls[st].get(p))
                    if a != b:
                        add(sel, tx, ":%s %s" % (st, p), a, b)
        elif ts and not ls:
            add(sel, tx, ":hover/:focus-visible", "interactive", "not interactive")
    for t in missing:
        add(t["path"], t["own"], "(element)", "present: " + brief(t), "MISSING on live")
    for l in extra:
        add(l["path"], l["own"], "(element)", "absent", "EXTRA on live: " + brief(l))
    return rows


def dom_diff(tn_, ln_):
    a, b = serialise(tn_), serialise(ln_)
    return list(difflib.unified_diff(a, b, "template", "live", lineterm="", n=1))


def ld_nodes(texts):
    out = []
    errs = []
    for t in texts:
        try:
            j = json.loads(t)
        except Exception as e:
            errs.append("JSON-LD does not parse: %s" % str(e)[:80])
            continue
        items = j.get("@graph", [j]) if isinstance(j, dict) else j
        for n in items:
            if isinstance(n, dict):
                out.append(n)
    return out, errs


def urlnorm_json(o, other):
    """Compare two JSON values; strings that are URLs on the store host compare by path."""
    def host_strip(s):
        if isinstance(s, str) and re.match(r"https?://\S+\.(webp|jpe?g|png)(\?\S*)?$", s):
            return src_norm(s)  # images: file name only (the theme prints /cdn/shop/articles/<file>_<uuid>.webp, the template the product file); lane C
        return hnorm(s) if isinstance(s, str) and s.startswith("http") else s
    if isinstance(o, dict):
        return {k: urlnorm_json(v, None) for k, v in o.items()}
    if isinstance(o, list):
        return [urlnorm_json(v, None) for v in o]
    return host_strip(o)


def tnode(n):
    t = n.get("@type")
    return t if isinstance(t, str) else "+".join(t or [])


def schema_check(t_head, l_head, strict=False, simulated=False):
    rows = []
    tn_, _ = ld_nodes(t_head["ld"])
    ln_, errs = ld_nodes(l_head["ld"])
    rows += [("jsonld", "parse", "ok", e) for e in errs]
    excluded = [tnode(n) for n in ln_ if tnode(n) in SITEWIDE_TYPES]
    ln_ = [n for n in ln_ if tnode(n) not in SITEWIDE_TYPES]
    tn_ = [n for n in tn_ if tnode(n) not in SITEWIDE_TYPES]
    from collections import Counter
    for side, nodes in (("live", ln_), ("template", tn_)):
        for ty, c in Counter(tnode(n) for n in nodes).items():
            if c > 1:
                rows.append(("jsonld", "duplicate @type", "1", "%d x %s on %s" % (c, ty, side)))
    tmap = {tnode(n): n for n in tn_}
    lmap = {tnode(n): n for n in ln_}
    for ty in sorted(set(tmap) | set(lmap)):
        a, b = tmap.get(ty), lmap.get(ty)
        if a is None:
            rows.append(("jsonld", ty, "absent", "EXTRA node on live"))
            continue
        if b is None:
            rows.append(("jsonld", ty, "present", "MISSING on live"))
            continue
        na, nb = urlnorm_json(a, None), urlnorm_json(b, None)
        diff_keys(na, nb, ty, rows)
    # FAQ text == visible FAQ text (live)
    faq = lmap.get("FAQPage")
    vis = (l_head.get("faq_vis") or [])
    if faq is not None:
        names = [q.get("name") for q in faq.get("mainEntity", [])]
        if names != vis:
            rows.append(("jsonld", "FAQPage text", "visible FAQ", "FAQ schema questions ≠ visible FAQ (%d vs %d)" % (len(names), len(vis))))
    # head
    exp = {"title": t_head["title"], "description": t_head["description"], "canonical": hnorm(t_head["canonical"]),
           "ogType": "article", "robots": None}
    if t_head["ogType"] or strict:
        exp["ogType"] = t_head["ogType"]
    live = {"title": l_head["title"], "description": l_head["description"], "canonical": hnorm(l_head["canonical"]), "ogType": l_head["ogType"], "robots": l_head["robots"]}
    for k in (() if simulated else ("title", "description", "canonical")):  # simulated host page: its title/description/canonical belong to another post
        if exp[k] != live[k]:
            rows.append(("head", k, exp[k], live[k]))
    if live["ogType"] != exp["ogType"]:
        rows.append(("head", "og:type", exp["ogType"] + (" (plan: template has none, SEO fix = article)" if not t_head["ogType"] else ""), live["ogType"]))
    if strict:
        if live["robots"] != t_head["robots"]:
            rows.append(("head", "robots", t_head["robots"], live["robots"]))
    elif live["robots"] and "noindex" in live["robots"].lower() and not os.environ.get("GATE_QA_COPY"):  # QA staging copy in blog journal-qa is noindex on purpose
        rows.append(("head", "robots", "index (template copy carries a preview-only noindex)", live["robots"]))
    elif t_head["robots"] and not live["robots"]:
        pass  # template preview noindex is an artefact of the preview copy; live must be indexable
    return rows, excluded


def diff_keys(a, b, path, rows):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                rows.append(("jsonld", path + "." + k, "absent", json.dumps(b[k])[:90]))
            elif k not in b:
                rows.append(("jsonld", path + "." + k, json.dumps(a[k])[:90], "MISSING"))
            else:
                diff_keys(a[k], b[k], path + "." + k, rows)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            rows.append(("jsonld", path, "len %d" % len(a), "len %d" % len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            diff_keys(x, y, "%s[%d]" % (path, i), rows)
    elif a != b:
        # dates: the template carries a fixed example date; the live date is the real publish date. Compare format only.
        if re.fullmatch(r"\d{4}-\d\d-\d\d.*", str(a)) and re.fullmatch(r"\d{4}-\d\d-\d\d.*", str(b)) and path.endswith(("datePublished", "dateModified")):
            if len(str(a)) != len(str(b)):
                rows.append(("jsonld", path, str(a), str(b) + "  (date FORMAT differs)"))
            return
        rows.append(("jsonld", path, str(a)[:90], str(b)[:90]))


def rules_check(m, r):
    def rng(v, x):
        return x[0] <= v <= x[1]
    c = {"words": rng(r["words"], m["words"]), "h2": rng(r["h2"], m["h2"]), "question_h2": r["qh2"] >= m["q_h2"], "cards": rng(r["cards"], m["cards"]),
         "images": rng(r["imgs"], m["img"]), "authority": r["authority"] >= m["authority"], "journal_links": r["journal"] >= m["journal_links"], "h1<=60": r["h1len"] <= 60}
    if "table" in m:
        c["table"] = r["tables"] >= (1 if m["table"] is True else int(m["table"]))
    if "comparison_rows" in m:
        c["comparison_rows"] = r["rows"] >= int(m["comparison_rows"])
    if "sources" in m:
        c["sources"] = r["sources"] >= int(m["sources"])
    return c


def sticky_rows(t, l, width):
    rows = []

    def add(sel, prop, a, b):
        rows.append({"width": width, "selector": sel, "text": "", "property": prop, "tpl": a, "live": b, "note": "state"})
    for key, sel in (("stick", ".stick (after hero leaves view)"), ("rail", ".rail-in (scrolled to 50 %)")):
        a, b = t.get(key), l.get(key)
        if a is None and b is None:
            continue
        a, b = a or {"present": False}, b or {"present": False}
        for k in sorted(set(a) | set(b)):
            va, vb = pv(k, str(a.get(k))), pv(k, str(b.get(k)))
            if k == "chromeOverlap":
                if vb not in ("", "None"):
                    add(sel, "sticky card hidden behind sticky store chrome", "no overlap", vb)
                continue
            if va != vb:
                add(sel, k, va, vb)
    return rows


# ---------------------------------------------------------------- one (pair, width)


def run_one(job):
    pair, width, run_dir, kind, simulate = job
    sid = pair["style"]
    out = Path(run_dir) / str(sid) / str(width)
    out.mkdir(parents=True, exist_ok=True)
    cfg = {"root_sets": [[".layout", "section.band", ".stick"], ["article.article"]], "rules": kind == "article"}
    if kind == "blog":
        cfg["root_sets"] = [["main#journal", "section.band"], ["main.jx", "section.band"], ["main#main"]]
    t0 = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chromium", args=["--disable-gpu"])   # lane A: software raster; GPU raster flipped ~850 px of one hero photo row between two captures of the SAME page
        try:
            tpl_src = Path(os.path.expanduser(pair["tpl"])).as_uri() if not pair["tpl"].startswith("http") else pair["tpl"]
            tpl = capture_side(browser, width, tpl_src, cfg, out, "tpl")
            live_url, mutate = pair.get("live_url") or pair["url"], pair.get("mutate")
            if simulate:
                arts = json.loads((SEO / "tpl-review" / "articles.json").read_text())
                art = arts[pair["slug"]]
                body = (SEO / "day1" / "bodies" / (pair["slug"] + ".html")).read_text()
                live_url, mutate = SIMULATED_HOST, swap_js(art, body)
            live = capture_side(browser, width, live_url, cfg, out, "live", mutate)
        finally:
            browser.close()
    v = evaluate(tpl, live, out, sid, width, kind, simulate, pair.get("strict_head"))
    v["seconds"] = round(time.time() - t0, 1)
    (out / "verdict.json").write_text(json.dumps(v, indent=1))
    return v


def run_one_safe(job):
    """A crashed cell is a FAIL with the error recorded, never a crashed run. One retry for browser/network hiccups."""
    last = None
    for attempt in (1, 2):
        try:
            return run_one(job)
        except Exception as e:  # noqa: BLE001
            last = "%s: %s" % (type(e).__name__, str(e)[:200])
            time.sleep(2)
    pair, width = job[0], job[1]
    v = {"style": pair["style"], "width": width, "simulated": bool(job[4]), "error": last, "pass": False, "ok_ignoring_simulated": False,
         "pixel": {"ok": False, "tiles": 0, "height_delta": 0}, "styles": {"ok": False, "rows": 0}, "dom": {"ok": False, "lines": 0},
         "schema": {"ok": False, "rows": 0}, "rules": {"ok": False, "failed": ["cell crashed: " + last]}, "seconds": 0}
    out = Path(job[2]) / str(pair["style"]) / str(width)
    out.mkdir(parents=True, exist_ok=True)
    (out / "verdict.json").write_text(json.dumps(v, indent=1))
    return v


def evaluate(tpl, live, out, sid, width, kind, simulate, pair_strict=False):
    v = {"style": sid, "width": width, "simulated": bool(simulate)}
    if "error" in tpl or "error" in live:
        msg = "tpl: %s | live: %s" % (tpl.get("error"), live.get("error"))
        v.update({"pixel": {"ok": False, "tiles": 0, "error": msg}, "styles": {"ok": False, "rows": 1}, "dom": {"ok": False, "lines": 1},
                  "schema": {"ok": False, "rows": 0}, "rules": {"ok": False, "failed": [msg[:80]]}, "error": msg, "pass": False, "ok_ignoring_simulated": False})
        (out / "styles.csv").write_text("width,selector,text,property,tpl,live,note\n%d,(region),,(root),present,%s,\n" % (width, live.get("error", "")))
        (out / "dom.diff").write_text("REGION ROOT MISSING: " + msg + "\n")
        return v
    tn_, ln_ = tpl["coll"]["nodes"], live["coll"]["nodes"]
    # (a) pixels
    a_img, b_img = Image.open(tpl["png"]), Image.open(live["png"])
    ok, tiles, ov, st = pixel_diff(a_img, b_img)
    extra = []
    for key, name in (("stick_png", "stick"), ("rail_png", "rail")):
        if tpl.get(key) and live.get(key):
            ok2, t2, ov2, st2 = pixel_diff(Image.open(tpl[key]), Image.open(live[key]))
            ov2.save(out / ("diff-%s.png" % name))
            if not ok2:
                ok = False
                tiles += [dict(t, part=name) for t in t2] or [{"part": name, "x": 0, "y": 0, "px": st2["diff_px"], "frac": 1}]
            extra.append(name)
        elif (tpl.get(key) is None) != (live.get(key) is None):
            ok = False
            tiles.append({"part": name, "x": 0, "y": 0, "px": 0, "frac": 1, "note": "%s crop exists on %s only" % (name, "template" if tpl.get(key) else "live")})
    ov.save(out / "diff.png")
    # deepest element at the centre of each failing tile: from the node boxes (region-relative)
    els = [n for n in ln_ if n["k"] == "el" and n["box"]["w"] > 0]
    for t in tiles:
        if "part" in t:
            continue
        cx, cy = t["x"] + TILE / 2, t["y"] + TILE / 2
        best = None
        for n in els:
            b = n["box"]
            if b["x"] <= cx <= b["x"] + b["w"] and b["y"] <= cy <= b["y"] + b["h"]:
                best = n
        t["live_element"] = best["path"] if best else "(none)"
    bad_imgs = [("template", i["s"]) for i in tpl["coll"]["imgs"] if not i["ok"]] + [("live", i["s"]) for i in live["coll"]["imgs"] if not i["ok"]]
    if bad_imgs:
        ok = False  # a region image that did not load makes every pixel verdict untrustworthy: fail loudly
    v["pixel"] = {"ok": ok, "tiles": len(tiles), "images_not_loaded": bad_imgs[:6], "diff_px": st["diff_px"], "clusters": st["clusters"], "size_tpl": list(st["size_tpl"]), "size_live": list(st["size_live"]),
                  "height_delta": st["size_live"][1] - st["size_tpl"][1], "first_tiles": tiles[:8]}
    # (c) DOM
    dd = dom_diff(tn_, ln_)
    (out / "dom.diff").write_text("\n".join(dd) + ("\n" if dd else ""))
    changed = [x for x in dd if x[:1] in "+-" and not x.startswith(("+++", "---"))]
    v["dom"] = {"ok": not changed, "lines": len(changed)}
    # (b) styles
    pairs, missing, extra_n = align(tn_, ln_)
    rows = style_rows(pairs, missing, extra_n, tpl["states"], live["states"], width)
    rows += sticky_rows(tpl, live, width)
    for k, s in (("stick", tpl.get("stick")), ("rail", tpl.get("rail"))):
        pass
    with open(out / "styles.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["width", "selector", "text", "property", "tpl", "live", "note"])
        w.writeheader()
        w.writerows(rows)
    first_top = next((r for r in rows if r["property"] == "y"), None)
    v["styles"] = {"ok": not rows, "rows": len(rows), "first_top_diff": (first_top["selector"] + " " + first_top["tpl"] + "→" + first_top["live"]) if first_top else None}
    # (d) head and schema
    t_head, l_head = tpl["head"], live["head"]
    l_head["faq_vis"] = (live.get("rules") or {}).get("faqVis")
    srows, excluded = schema_check(t_head, l_head, strict=bool(pair_strict), simulated=simulate)
    (out / "schema.json").write_text(json.dumps([{"area": a, "item": b, "tpl": c, "live": d} for a, b, c, d in srows], indent=1))
    v["schema"] = {"ok": not srows, "rows": len(srows), "excluded_sitewide_nodes": excluded}
    # (e) rules
    if kind == "article" and live.get("rules") and t_head.get("rules"):
        m = json.loads(t_head["rules"])
        rc, tc = rules_check(m, live["rules"]), rules_check(m, tpl["rules"])
        v["rules"] = {"ok": all(rc.values()), "failed": [k for k, x in rc.items() if not x], "template_failed": [k for k, x in tc.items() if not x],
                      "live": {k: live["rules"][k] for k in ("words", "h2", "qh2", "cards", "imgs", "authority", "journal", "tables", "rows", "sources")}}
    else:
        v["rules"] = {"ok": kind != "article", "failed": ["no #rules-machine / article region"] if kind == "article" else []}
    v["chrome"] = {"enforced": False, "tpl": tpl["chrome"], "live": live["chrome"], "equal": tpl["chrome"]["above"] == live["chrome"]["above"] and tpl["chrome"]["below"] == live["chrome"]["below"]}
    v["images"] = {"tpl": tpl["images"], "live": live["images"]}
    ts, ls = {f["sha"] for f in tpl["fonts"]}, {f["sha"] for f in live["fonts"]}
    v["fonts"] = {"info_only": True, "tpl": [(f["name"], f["sha"], f["bytes"]) for f in tpl["fonts"]], "live": [(f["name"], f["sha"], f["bytes"]) for f in live["fonts"]], "same_binaries": ts == ls and bool(ts)}
    v["pass"] = all(v[k]["ok"] for k in ("pixel", "styles", "dom", "schema", "rules")) and not simulate
    v["ok_ignoring_simulated"] = all(v[k]["ok"] for k in ("pixel", "styles", "dom", "schema", "rules"))
    return v


# ---------------------------------------------------------------- selftest (positive controls)

CONTROLS = [
    ("clean copy (negative control: must PASS)", None, "pass", None),
    ("1 h2 margin-top 48px instead of 56px", "() => { document.querySelectorAll('h2').forEach(h => h.style.marginTop = '48px'); }", "styles", ("h2", "margin-top", "56px", "48px")),
    ("2 one word bolded", "() => { const p = document.querySelector('.answer p:last-child'); p.innerHTML = p.innerHTML.replace(/\\b(cotton)\\b/, '<b>$1</b>'); }", "dom", None),
    ("3 hero ratio 4:5 instead of 4:3", "() => { const i = document.querySelector('.hero img'); i.style.aspectRatio = '4/5'; }", "pixel+styles", ("img", "aspect-ratio", "4 / 3", "4 / 5")),
    ("4 duplicate BlogPosting", "() => { const s = document.querySelector('script[type=\"application/ld+json\"]'); const j = JSON.parse(s.textContent); const bp = j['@graph'].find(n => n['@type'] === 'BlogPosting'); j['@graph'].push(JSON.parse(JSON.stringify(bp))); s.textContent = JSON.stringify(j); }", "schema", None),
    ("5 button hover colour changed", "() => { const st = document.createElement('style'); st.textContent = '.btn:hover{background:#000!important}'; document.head.append(st); }", "styles", (".btn", ":hover background-color", None, None)),
    ("5b link focus ring colour changed (390 only)", "() => { const st = document.createElement('style'); st.textContent = '.btn:focus-visible{outline-color:#f00!important;outline-style:solid!important}'; document.head.append(st); }", "styles", (".btn", ":focus-visible outline-color", None, None), (390,)),
    ("6 sticky bar stays hidden (390 only)", "() => { const st = document.createElement('style'); st.textContent = '.stick.on{transform:translateY(110%)!important}'; document.head.append(st); }", "styles", (".stick", "transform", None, None), (390,)),
    ("7 rail sticky top 40px instead of 24px (1440 only)", "() => { const st = document.createElement('style'); st.textContent = '.rail-in{top:40px!important}'; document.head.append(st); }", "styles", (".rail-in", "top", "24px", "40px"), (1440,)),
    ("8 blog index, clean copy (must PASS)", None, "pass", None, {"widths": (1440, 390), "kind": "blog"}),
    ("9 blog index, one chip label changed", "() => { const a = document.querySelector('.chips a'); a.firstChild.textContent = 'All posts '; }", "dom", None, {"widths": (1440,), "kind": "blog"}),
]


def selftest(args):
    tpl = sorted((SEO / "day1").glob("style-1-*.html"))[0]
    run_dir = RUNS / ("selftest-" + datetime.now().strftime("%y%m%d-%H%M"))
    ok_all = True
    log = []
    mock = SEO / "blog-index" / "blog-index-mock.html"
    for ci, (name, mutate, expect, detail, *wd) in enumerate(CONTROLS):
        o = wd[0] if wd else (1440, 390)
        o = o if isinstance(o, dict) else {"widths": o, "kind": "article"}
        src = mock if o["kind"] == "blog" else tpl
        for width in o["widths"]:
            pair = {"style": "selftest-%d" % ci, "tpl": str(src), "live_url": src.as_uri(), "mutate": mutate, "strict_head": True}
            v = run_one((pair, width, str(run_dir), o["kind"], False))
            rows = list(csv.DictReader(open(run_dir / pair["style"] / str(width) / "styles.csv")))
            dd = (run_dir / pair["style"] / str(width) / "dom.diff").read_text()
            sch = json.loads((run_dir / pair["style"] / str(width) / "schema.json").read_text())
            if expect == "pass":
                caught = v["ok_ignoring_simulated"]
                evidence = "no differences" if caught else "UNEXPECTED FAIL: " + json.dumps({k: v[k] for k in ("pixel", "styles", "dom", "schema", "rules")})[:300]
            elif expect == "styles":
                hit = [r for r in rows if r["property"] == detail[1] and (detail[0] in r["selector"] or r["selector"].endswith(detail[0]))]
                if detail[2]:
                    hit = [r for r in hit if r["tpl"] == detail[2] and r["live"] == detail[3]]
                caught = bool(hit) and not v["styles"]["ok"]
                evidence = "%s %s %s→%s" % (hit[0]["selector"][-40:], hit[0]["property"], hit[0]["tpl"], hit[0]["live"]) if hit else "NOT CAUGHT"
            elif expect == "pixel+styles":
                hit = [r for r in rows if r["property"] == "aspect-ratio" and "img" in r["selector"]]
                caught = bool(hit) and not v["pixel"]["ok"] and v["pixel"]["tiles"] > 0
                evidence = ("%s aspect-ratio %s→%s; %d pixel tiles" % (hit[0]["selector"][-30:], hit[0]["tpl"], hit[0]["live"], v["pixel"]["tiles"])) if hit else "NOT CAUGHT"
            elif expect == "dom":
                changed = [x for x in dd.splitlines() if x[:1] in "+-" and not x.startswith(("+++", "---"))]
                caught = bool(changed) and not v["dom"]["ok"]
                evidence = changed[0].strip()[:90] if changed else "NOT CAUGHT"
            elif expect == "schema":
                hit = [r for r in sch if r["item"] == "duplicate @type"]
                caught = bool(hit) and not v["schema"]["ok"]
                evidence = hit[0]["live"] if hit else "NOT CAUGHT"
            else:
                caught = False
                evidence = "?"
            ok_all &= caught
            log.append((name, width, caught, evidence))
            print("%-48s %5d  %s  %s" % (name, width, "OK  " if caught else "FAIL", evidence), flush=True)
    print("SELFTEST:", "PASS (all controls behave)" if ok_all else "FAIL (a control was not caught: the gate is broken)")
    (RUNS.parent / "selftest-last.txt").write_text("\n".join("%-48s %5d  %s  %s" % (n, w, "OK" if c else "FAIL", e) for n, w, c, e in log) + "\nSELFTEST: %s\n" % ("PASS" if ok_all else "FAIL"))
    return 0 if ok_all else 1


# ---------------------------------------------------------------- report

EXCLUDED = """## Excluded from the comparison (Kevin, 2026-10-27: keep the store header)

| Excluded | Template side | Live side | Why |
|---|---|---|---|
| Announcement / top bar | `.topbar` | store announcement bar | store chrome; Kevin keeps it (part 1 § 9 Q1) |
| Header and navigation | `header.site` | store header (+ sticky state) | store chrome |
| Footer | `footer.foot` | store footer | store chrome |
| Promo pop-up, cart drawer, preview bar | none | `dialog`, cart drawer, any fixed/sticky element outside the region | store chrome; hidden before every capture |
| Template-only preview parts | `.preview`, `#rules`, `.spec` labels | none | never part of a live post (already removed in the day-1 copies) |
| Sitewide JSON-LD | none | `Organization` + `WebSite` nodes printed by `snippets/site-jsonld.liquid` | store-level schema, not article schema |

Compared (everything else): from the top of `.layout` (breadcrumb) to the bottom of `section.band`, plus `.stick` (sticky bar) and the rail inside `.layout`.
For `--kind blog`: `main#journal` and the end band. Chrome is read and reported (below) but never fails the gate.
The template's preview-only `<meta robots noindex>` is not expected on live: live must be indexable. `og:type` expected = `article` (part 1 § 4 item 14).
"""


def tail_match(tail, pat):
    """tail = last CSS-path segment, e.g. div#stick.stick; pat = tag plus classes, e.g. div.stick."""
    m = re.match(r"([a-z0-9]+)(?:#[^.:]*)?((?:\.[^.#:]+)*)", re.sub(r":nth-of-type\(\d+\)", "", tail))
    tag, *cls = pat.split(".")
    return bool(m) and m.group(1) == tag and all(c in m.group(2).split(".") for c in cls)


def any_row(rows, sel=None, end=None, prop=None, live=None, tpl=None):
    for r in rows:
        if sel and sel not in r["selector"]:
            continue
        if end and not tail_match(r["selector"].split(" > ")[-1], end):
            continue
        if prop and r["property"] != prop:
            continue
        if live and live not in r["live"]:
            continue
        if tpl and tpl not in r["tpl"]:
            continue
        return r
    return None


def coverage(run_dir):
    """Part 1 § 4 deviations -> the first gate row that proves each one on the simulated baseline."""
    rows, dom, sch, meta = [], "", [], []
    for f in Path(run_dir).glob("*/*/styles.csv"):
        rows += list(csv.DictReader(open(f)))
    for f in Path(run_dir).glob("*/*/dom.diff"):
        dom += f.read_text()
    for f in Path(run_dir).glob("*/*/schema.json"):
        sch += json.loads(f.read_text())
    P = lambda **k: any_row(rows, **k)  # noqa: E731
    items = [
        ("1", "Header order (crumbs → kicker → H1 → dek → meta → hero → TOC → answer)", P(live="MISSING", end="nav.crumbs") or P(live="MISSING", end="p.label.kicker")),
        ("2", "H1 font, size, line-height, tracking, alignment, axes", P(end="h1", prop="font-size") and P(end="h1", prop="letter-spacing") and P(end="h1", prop="text-align") and P(end="h1", prop="font-variation-settings")),
        ("3", "Meta line: text, format, size, colour, alignment, borders", P(live="MISSING", end="p.meta") and P(live="EXTRA", end="p.article__meta") and ("Updated" in dom)),
        ("4", "Body text 16→17 px, line-height, letter-spacing", P(end="p", prop="font-size") and P(end="p", prop="line-height") and P(end="p", prop="letter-spacing")),
        ("5", "H2 size, margin-top, tracking", P(end="h2", prop="margin-top") or P(end="h2", prop="font-size")),
        ("6", "H3 margin-top", P(end="h3", prop="margin-top")),
        ("7", "Column width 720 vs 750/780/688/860/560/350", P(end="p", prop="w") or P(end="h2", prop="w")),
        ("8", "Hero ratio 4:3, caption, sizes", P(end="img", prop="aspect-ratio") and P(live="MISSING", end="figcaption") and ("sizes=" in dom)),
        ("9", "Inline TOC visible ≥ 1100 (must hide)", P(end="details.toc", prop="display")),
        ("10", "Rail, sticky bar, breadcrumb, kicker missing", P(live="MISSING", end="aside.rail") and P(live="MISSING", end="div.stick") and P(live="MISSING", end="nav.crumbs") and P(live="MISSING", end="p.label.kicker")),
        ("11", "End band boxed, not full-bleed; band link colour", P(end="section.band", prop="w") or P(end="section.band", prop="x")),
        ("12", "Footer back link '← Journal' (not in template)", P(live="EXTRA", end="footer.article__footer") or P(live="EXTRA", end="a.article__back")),
        ("13", "JSON-LD: duplicate BlogPosting and BreadcrumbList", any(r["item"] == "duplicate @type" and "BlogPosting" in r["live"] for r in sch) and any(r["item"] == "duplicate @type" and "BreadcrumbList" in r["live"] for r in sch)),
        ("14", "og:type website instead of article (title pattern: see note)", any(r["item"] == "og:type" for r in sch)),
        ("15", "Top bar text / header nav (chrome): excluded by Kevin", "excluded"),
        ("16", "Fonts: different binaries (glyphs checked by pixel diff; binaries listed in verdict.json `fonts`)", "info"),
        ("17", "Colours equal (no `color`/`background-color` row expected on body text)", "info"),
    ]
    lines = ["## Part 1 § 4 coverage (SIMULATED baseline)", "", "| # | Deviation | Found by the gate | Evidence |", "|---|---|---|---|"]
    ok_all = True
    for n, label, hit in items:
        if hit == "excluded":
            lines.append("| %s | %s | excluded | chrome row only |" % (n, label))
        elif hit == "info":
            lines.append("| %s | %s | info | see verdict.json |" % (n, label))
        else:
            ok_all &= bool(hit)
            ev = "dom.diff / schema.json" if hit is True else ""
            if isinstance(hit, dict):
                ev = "`%s` %s: `%s` → `%s`" % (hit["selector"].split(" > ")[-1][:40], hit["property"], hit["tpl"][:40].replace("|", "/"), hit["live"][:40].replace("|", "/"))
            lines.append("| %s | %s | %s | %s |" % (n, label, "YES" if hit else "**NO**", ev))
    lines.append("")
    lines.append("Item 14 title pattern: the template pattern `<Short title> | Cherish` is checked at the live stage by the `title` row; the simulated host page carries another post's `<title>`, so the row is skipped in SIMULATED mode.")
    return lines, ok_all


def write_report(run_dir, verdicts, args, simulate, kind, runtime):
    lines = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    all_ok = all(v.get("pass") for v in verdicts)
    lines.append("# Fidelity gate run %s — %s" % (Path(run_dir).name, "SIMULATED (never counts for acceptance)" if simulate else "preview theme " + str(args.theme)))
    lines.append("")
    lines.append("Run at %s Asia/Saigon · kind `%s` · %d style×width cells · %.1f min · folder `%s`" % (ts, kind, len(verdicts), runtime / 60, run_dir))
    lines.append("")
    lines.append("| style | width | pixel | styles (rows) | dom (lines) | schema (rows) | rules | Δ height | s |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for v in sorted(verdicts, key=lambda x: (str(x["style"]), -x["width"])):
        lines.append("| %s | %d | %s (%s tiles) | %s (%s) | %s (%s) | %s (%s) | %s | %+d px | %s |" % (
            v["style"], v["width"], "ok" if v["pixel"]["ok"] else "FAIL", v["pixel"].get("tiles"), "ok" if v["styles"]["ok"] else "FAIL", v["styles"]["rows"],
            "ok" if v["dom"]["ok"] else "FAIL", v["dom"]["lines"], "ok" if v["schema"]["ok"] else "FAIL", v["schema"].get("rows", ""),
            "ok" if v["rules"]["ok"] else "FAIL " + ",".join(v["rules"].get("failed", [])), v["pixel"].get("height_delta", 0), v.get("seconds")))
    lines.append("")
    lines.append(EXCLUDED)
    c = [v for v in verdicts if v.get("chrome")]
    if c:
        lines.append("### Chrome (reported, never fails)")
        lines.append("")
        lines.append("| style · width | template above region | live above region | template below | live below |")
        lines.append("|---|---|---|---|---|")
        for v in sorted(c, key=lambda x: (str(x["style"]), -x["width"]))[:4]:
            ch = v["chrome"]
            lines.append("| %s · %d | %s | %s | %s | %s |" % (v["style"], v["width"], ch["tpl"]["above"][:80].replace("|", "/"), ch["live"]["above"][:80].replace("|", "/"), ch["tpl"]["below"][:50].replace("|", "/"), ch["live"]["below"][:50].replace("|", "/")))
        lines.append("")
    fv = next((v for v in verdicts if v.get("fonts")), None)
    if fv:
        lines.append("### Font binaries (information only; glyph equality is judged by the pixel diff)")
        lines.append("")
        lines.append("| side | file / family | sha256 (12) | bytes |")
        lines.append("|---|---|---|---|")
        for side in ("tpl", "live"):
            for n, h, b in fv["fonts"][side]:
                lines.append("| %s | %s | `%s` | %s |" % (side, n, h, b))
        lines.append("")
        lines.append("Same binaries on both sides: **%s**." % fv["fonts"]["same_binaries"])
        lines.append("")
    for sid in sorted({str(v["style"]) for v in verdicts}):
        for w in (1440, 390):
            f = Path(run_dir) / sid / str(w) / "styles.csv"
            if not f.exists():
                continue
            rows = list(csv.DictReader(open(f)))
            if not rows:
                continue
            by = {}
            for r in rows:
                by[r["property"]] = by.get(r["property"], 0) + 1
            lines.append("### Style %s · %d px — %d rows; by property: %s" % (sid, w, len(rows), ", ".join("%s %d" % kv for kv in sorted(by.items(), key=lambda kv: -kv[1])[:8])))
            lines.append("")
            lines.append("| element (CSS path tail) | text | property | template | live |")
            lines.append("|---|---|---|---|---|")
            seen, n = set(), 0
            for r in rows:
                k = (r["selector"].split(" > ")[-1], r["property"])
                if k in seen:
                    continue
                seen.add(k)
                lines.append("| `%s` | %s | %s | `%s` | `%s` |" % (r["selector"][-70:], r["text"].replace("|", "/"), r["property"], r["tpl"][:50].replace("|", "/"), r["live"][:60].replace("|", "/")))
                n += 1
                if n >= 14:
                    break
            lines.append("")
    if simulate and kind == "article":
        cov, _ = coverage(run_dir)
        lines += cov
        lines.append("")
    lines.append("GATE: %s" % ("PASS" if all_ok and not simulate else "FAIL" + (" (SIMULATED run: never a PASS)" if simulate else "")))
    (Path(run_dir) / "REPORT.md").write_text("\n".join(lines) + "\n")
    return all_ok


# ---------------------------------------------------------------- main


def load_pairs(path, theme, only, kind):
    pairs = json.loads(Path(path).read_text())
    out = []
    for p in pairs:
        if only and str(p["style"]) not in only:
            continue
        p = dict(p)
        if theme and p.get("live_url"):
            p["live_url"] = p["live_url"].replace("<id>", str(theme)).replace("{theme}", str(theme))
        if theme and "url" in p:
            u = p["url"].replace("<id>", str(theme)).replace("{theme}", str(theme))
            if "preview_theme_id" not in u:
                u += ("&" if "?" in u else "?") + "preview_theme_id=" + str(theme)
            p["url"] = u
        out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pairs", default=str(SEO / "fidelity" / "pairs.json"))
    ap.add_argument("--theme", help="preview theme id (appended to each live url as ?preview_theme_id=)")
    ap.add_argument("--only", help="comma list of style ids, e.g. 4c or 1,3")
    ap.add_argument("--widths", help="comma list, default 1440,1100,900,600,390")
    ap.add_argument("--kind", choices=["article", "blog"], default="article")
    ap.add_argument("--simulate", action="store_true", help="swap harness on a published MAIN post; run is labelled SIMULATED")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run-id", help="reuse runs/<run-id>; cells that already have a verdict.json are not re-run (resume after a timeout)")
    ap.add_argument("--jobs", type=int, default=2, help="parallel Chrome processes (RAM: keep <= 3)")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest(args))
    widths = [int(w) for w in args.widths.split(",")] if args.widths else list(WIDTHS)
    only = set(args.only.split(",")) if args.only else None
    pairs = load_pairs(args.pairs, args.theme, only, args.kind)
    if not pairs:
        sys.exit("no pairs selected")
    if args.kind == "article" and not args.simulate and not args.theme and any("preview_theme_id" not in p.get("url", "") for p in pairs):
        sys.exit("live mode needs --theme <preview_theme_id> (or --simulate for the swap harness)")
    run_dir = RUNS / (args.run_id or datetime.now().strftime("%y%m%d-%H%M"))
    run_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(p, w, str(run_dir), args.kind, args.simulate) for p in pairs for w in widths]
    done = {}
    for j in list(jobs):
        f = run_dir / str(j[0]["style"]) / str(j[1]) / "verdict.json"
        if args.run_id and f.exists():
            v = json.loads(f.read_text())
            if not v.get("error"):
                done[(str(j[0]["style"]), j[1])] = v
                jobs.remove(j)
    t0 = time.time()
    verdicts = list(done.values())
    with ProcessPoolExecutor(max_workers=max(1, args.jobs)) as ex:
        for v in ex.map(run_one_safe, jobs):
            verdicts.append(v)
            print("%-4s %5d  pixel=%s styles=%s dom=%s schema=%s rules=%s  Δh=%+d  %ss" % (
                v["style"], v["width"], v["pixel"]["ok"], v["styles"]["rows"], v["dom"]["lines"], v["schema"]["ok"], v["rules"]["ok"], v["pixel"].get("height_delta", 0), v.get("seconds")), flush=True)
    ok = write_report(run_dir, verdicts, args, args.simulate, args.kind, time.time() - t0)
    print("run folder:", run_dir)
    print("GATE:", "PASS" if ok and not args.simulate else "FAIL")
    sys.exit(0 if ok and not args.simulate else 1)


if __name__ == "__main__":
    main()

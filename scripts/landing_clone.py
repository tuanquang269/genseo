#!/usr/bin/env python3
"""Reference-replica renderer for GenSeo landing pages (engine "ref").

  /usr/bin/python3 scripts/landing_clone.py landing_drafts/<slug>.json

Kevin 2026-10-06: the listicle and advertorial templates are EXACT replicas of the reference pages
(omnicreatine.com /pages/10-reasons-why-creatine-is-for-skinny-people and /pages/advv-1, local clone
~/PATI/work/omnicreatine-local-clone served on :8790). Same section order, markup, class names, spacing
and type scale; only copy, product data, images and brand tokens change.

How:
  * markup below mirrors the reference sections verbatim (rbltb, rblha, rblit--v2, rble--v2, rblof, rblft
    for the listicle; rblh, rblit, rble, featured product (rbp-head + nw-bundle), rblr, rbq for the
    advertorial). Section wrappers keep the rb-section--* classes the reference CSS keys on.
  * CSS = the reference's own section CSS files (templates/landing/ref/css/, copied from the clone) +
    templates/landing/ref/extra.css, all SCOPED under .gsl-ref so nothing leaks into the theme, then
    brand-swapped (reference navy/blue palette -> Wellness Nest greens, Satoshi -> brand font).
  * images: every slot is cropped from a GenSeo-generated square (scripts/article_images.py --qc, no faces)
    to the reference slot's aspect (desktop <img> + mobile <source>), webp < 80 KB. Real PDP pack shots
    only where the reference shows the product (offer card, featured-product gallery).
  * countdown timers / sell-out risk render ONLY with a real deadline (spec topbar.deadline); none today.
Outputs landing_drafts/<slug>/{body.html,preview.html,img/*} and the theme templates
templates/landing/page.<suffix>.liquid (CSS inline, {{ page.content }}).
"""
import html, json, os, re, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "templates", "landing", "ref")
SVG = json.load(open(os.path.join(REF, "svg.json")))
E = html.escape

CSS_FILES = {
    "listicle": ["rebrand-tokens.css", "rebrand-listicle-timer-bar.css", "rebrand-listicle-hero-article.css",
                 "rebrand-listicle-image-text.css", "rebrand-listicle-expert.css", "rebrand-listicle-offer.css",
                 "rebrand-listicle-footer.css"],
    "advertorial": ["rebrand-tokens.css", "rebrand-listicle-hero.css", "rebrand-listicle-image-text.css",
                    "rebrand-listicle-expert.css", "rebrand-fp-header.css", "nw-bundle.css",
                    "rebrand-featured-product.css", "component-icon-text-row.css", "rebrand-listicle-reviews.css",
                    "rebrand-faq.css", "rebrand-listicle-footer.css"],
}

# reference palette -> brand palette (Wellness Nest: primary #54b94a, dark #3a9e40, ink #1e3a29)
def palette(brand):
    c = brand.get("colors", {})
    ink = c.get("ink", "#1e3a29")
    return [
        ("#0d1e39", ink), ("#193b68", "#2b5a36"), ("#193B68", "#2b5a36"), ("#265392", c.get("primary_dark", "#3a9e40")),
        ("#6c93c2", c.get("primary_light", "#8ee085")), ("#6C93C2", c.get("primary_light", "#8ee085")),
        ("#517ebd", "#8ee085"), ("#3667aa", "#6cc862"), ("#1b4f97", c.get("primary", "#54b94a")),
        ("#0e3a77", "#3a9e40"), ("#002458", "#2a7a30"), ("#1f477d", "#3a9e40"), ("#0b2d5f", "#2b5a36"),
        ("#061633", "#14281c"), ("#001b52", ink), ("#020917", "#0f1f15"), ("#0040C1", "#3a9e40"),
        ("#dce6f0", "#e7f4e4"), ("#f5f8ff", c.get("bg_soft", "#f6fbf5")), ("#F5F8FF", "#f6fbf5"),
        ("#bed1e4", "#cfe8cb"), ("#b2ccff", "#bfe6b9"), ("#D1E0FF", "#d7f0d3"), ("#239627", c.get("star", "#54b94a")),
        ("rgba(13,30,57,", "rgba(30,58,41,"), ("rgba(13, 30, 57,", "rgba(30, 58, 41,"),
        ("rgba(81,126,189,", "rgba(84,185,74,"), ("#026", ink), ("#22c55e", c.get("star", "#54b94a")),
    ]


def brand_swap(s, pal):
    for a, b in pal:
        s = s.replace(a, b)
    return s


def split_top(sel):
    out, depth, cur = [], 0, ""
    for ch in sel:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur); cur = ""
        else:
            cur += ch
    out.append(cur)
    return [x.strip() for x in out if x.strip()]


def scope_css(css, scope=".gsl-ref"):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            break
        prelude = css[i:j].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == "{":
                depth += 1
            elif css[k] == "}":
                depth -= 1
            k += 1
        body = css[j + 1:k - 1]
        if prelude.startswith(("@media", "@supports", "@container")):
            out.append(prelude + "{" + scope_css(body, scope) + "}")
        elif prelude.startswith("@"):
            out.append(prelude + "{" + body + "}")
        else:
            sels = []
            for s in split_top(prelude):
                if s.startswith((":root", "html", "body")):
                    s = re.sub(r"^(:root|html|body)", scope, s)
                    sels.append(s)
                else:
                    sels.append(scope + " " + s)
            out.append(",".join(sels) + "{" + body + "}")
        i = k
    return "".join(out)


def build_css(kind, brand):
    # The gsl-ref-* theme template is ONE shared file installed in the live theme with the base store's palette, so a
    # sub-brand spec (AgeAura "extends" wellnessnest) must render with that same palette — otherwise the preview and
    # templates/landing/page.<suffix>.liquid drift from what the live page actually shows (fixed 2026-10-08).
    vis = load_brand(brand["extends"]) if brand.get("extends") else brand
    pal = palette(vis)
    font = brand.get("fonts", {}).get("body", "Montserrat, sans-serif")
    raw = ""
    for f in CSS_FILES[kind]:
        raw += open(os.path.join(REF, "css", f)).read() + "\n"
    raw += open(os.path.join(REF, "extra.css")).read()
    raw = raw.replace('"Satoshi", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', font)
    raw = re.sub(r'Satoshi Variable,\s*Satoshi,\s*sans-serif|Satoshi,\s*sans-serif', "var(--rb-f)", raw)
    raw = raw.replace('var(--rb-f, "Satoshi Variable", "Satoshi", sans-serif)', "var(--rb-f)")
    css = scope_css(brand_swap(raw, pal))
    css += ".gsl-ref{--rb-f:%s;font-family:var(--rb-f)}" % font
    return css


# ---------- images ----------
def crop_to(src, aspect, width, out, max_kb=78):
    im = Image.open(os.path.join(ROOT, src) if not os.path.isabs(src) else src).convert("RGB")
    w, h = im.size
    if w / h > aspect:
        nw = int(h * aspect); x = (w - nw) // 2; im = im.crop((x, 0, x + nw, h))
    else:
        nh = int(w / aspect); y = (h - nh) // 2; im = im.crop((0, y, w, y + nh))
    height = int(round(width / aspect))
    im = im.resize((width, height), Image.LANCZOS)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    for q in (82, 76, 70, 64, 58, 52, 46):
        im.save(out, "WEBP", quality=q, method=6)
        if os.path.getsize(out) <= max_kb * 1024:
            break
    return width, height


class Imgs:
    """Crops generated squares into the reference slot sizes; returns absolute local paths (publisher uploads)."""
    def __init__(self, out_dir):
        self.dir = os.path.join(out_dir, "img")

    def slot(self, src, name, d_aspect, d_w, m_aspect=None, m_w=750):
        if not src:
            return None
        if src.startswith("http"):
            return {"d": src, "m": src, "dw": d_w, "dh": int(d_w / d_aspect)}
        d = os.path.join(self.dir, f"{name}-d.webp")
        dw, dh = crop_to(src, d_aspect, d_w, d)
        m = os.path.join(self.dir, f"{name}-m.webp")
        crop_to(src, m_aspect or d_aspect, m_w, m)
        return {"d": d, "m": m, "dw": dw, "dh": dh}


def picture(img, alt, disp_w, disp_h, eager=False):
    if not img:
        return ""
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<picture><source media="(max-width: 749px)" srcset="{img["m"]}"><img src="{img["d"]}" alt="{E(alt)}" '
            f'width="{disp_w}" height="{disp_h}" {load}></picture>')


def stars(n=5, svg="star", total=5):
    on = SVG[svg]
    off = on.replace('fill="#239627"', 'fill="#cbd5e1"').replace('fill="currentColor"', 'fill="#cbd5e1"')
    return "".join(on if i < n else off for i in range(total))


def chart_html(ch):
    if ch.get("kind") == "stats":
        tiles = "".join(f'<div class="gslc__stat{" is-hl" if t.get("highlight") else ""}"><b>{E(t["value"])}</b><span>{E(t["label"])}</span></div>' for t in ch["stats"])
        return (f'<div class="gslc gslc--stats" role="img" aria-label="{E(ch["title"])}"><p class="gslc__title">{E(ch["title"])}</p>'
                f'<div class="gslc__stats">{tiles}</div><p class="gslc__src">{E(ch["source"])}</p></div>')
    mx = max(b["value"] for b in ch["bars"]) or 1
    cols, labels = "", ""
    for b in ch["bars"]:
        hpct = max(8, int(round(100 * b["value"] / mx * 0.78)))
        hl = " is-hl" if b.get("highlight") else ""
        cols += (f'<div class="gslc__col"><span class="gslc__val">{E(b.get("display", str(b["value"])))}</span>'
                 f'<span class="gslc__bar{hl}" style="height:{hpct}%"></span></div>')
        labels += f'<span>{E(b["label"])}</span>'
    legend = "".join(f'<span><i class="{ "is-hl" if l.get("highlight") else "" }"></i>{E(l["label"])}</span>' for l in ch.get("legend", []))
    return (f'<div class="gslc" role="img" aria-label="{E(ch["title"])}"><p class="gslc__title">{E(ch["title"])}</p>'
            + (f'<div class="gslc__legend">{legend}</div>' if legend else "")
            + f'<div class="gslc__plot">{cols}</div><div class="gslc__labels">{labels}</div>'
            f'<p class="gslc__src">{E(ch["source"])}</p></div>')


def sec(kind, inner, extra=""):
    return f'<section class="rb-section rb-section--{kind}"{extra}>{inner}</section>\n'


# ---------- listicle (reference: /pages/10-reasons-why-creatine-is-for-skinny-people) ----------
def render_listicle(spec, imgs):
    out = []
    tb = spec.get("topbar") or {}
    labels = "".join(f"<span>{E(x)}</span>" for x in tb.get("labels", []))
    if tb.get("deadline"):
        chip = ('<div class="rbltb__chip" data-rbltb-timer data-deadline="%s"><span class="rbltb__unit"><b data-rbltb-h>00</b><i>HRS</i></span>'
                '<span class="rbltb__colon">:</span><span class="rbltb__unit"><b data-rbltb-m>00</b><i>MIN</i></span>'
                '<span class="rbltb__colon">:</span><span class="rbltb__unit"><b data-rbltb-s>00</b><i>SEC</i></span></div>') % E(tb["deadline"])
        out.append(sec("listicle-timer-bar", f'<div class="rbltb"><div class="rbltb__labels">{labels}</div>{chip}</div>'))
    else:
        out.append(sec("listicle-timer-bar", f'<div class="rbltb rbltb--nochip"><div class="rbltb__labels">{labels}</div></div>'))
    h = spec["hero"]; by = spec.get("byline", {})
    av = imgs.slot(by.get("avatar"), "avatar", 1.0, 96, 1.0, 96)
    av_html = f'<img src="{av["d"]}" alt="{E(by.get("name",""))}" width="48" height="48" loading="eager">' if av else ""
    out.append(sec("listicle-hero-article",
        f'<div class="rblha"><div class="rblha__card"><h1 class="rblha__title"><span class="rblha__accent">{E(h["accent"])}</span> {E(h["title"])}</h1>'
        f'<div class="rblha__author"><div class="rblha__avatar">{av_html}</div><div class="rblha__author-text">'
        f'<p class="rblha__author-name">By <b>{E(by.get("name",""))}{(" | " + E(by["role"])) if by.get("role") else ""}</b></p>'
        f'<p class="rblha__updated">Last Updated {E(spec.get("updated",""))}</p></div></div></div>'
        f'<div class="rblha__summary"><p>{h["summary_html"]}</p></div></div>'))
    rows = list(spec["items"]) + ([dict(spec["bridge"], _bridge=True)] if spec.get("bridge") else [])
    for i, it in enumerate(rows):
        side = "left" if i % 2 == 0 else "right"
        n = f"{i+1:02d}"
        if it.get("chart"):
            media = chart_html(it["chart"])
        else:
            im = imgs.slot(it.get("image"), f"row{i+1}", 616 / 590, 924, 1.0, 750)
            media = picture(im, it.get("alt", it["title"]), 616, 590)
        out.append(sec("listicle-image-text",
            f'<div class="rblit rblit--image-{side} rblit--v2"><div class="rblit__inner"><div class="rblit__content">'
            f'<div class="rblit__header"><div class="rblit__eyebrow" aria-label="Section {n}"><span>{n}</span></div>'
            f'<h2 class="rblit__title">{E(it["title"])}</h2></div><div class="rblit__body">{it["body"]}</div></div>'
            f'<div class="rblit__media-wrap"><div class="rblit__media">{media}</div></div></div></div>'))
    ex = spec.get("expert")
    if ex:
        n = f"{len(rows)+1:02d}"
        im = imgs.slot(ex.get("image"), "expert", 616 / 560, 924, 900 / 734, 750)
        out.append(sec("listicle-expert",
            f'<div class="rble rble--v2"><div class="rble__inner"><div class="rble__content"><div class="rble__header">'
            f'<div class="rble__eyebrow" aria-label="Section {n}"><span>{n}</span></div><h2 class="rble__title">{E(ex["title"])}</h2></div>'
            f'<div class="rble__review"><div class="rble__stars" aria-label="{ex.get("stars",5)} star review">{stars(ex.get("stars",5))}</div>'
            f'<div class="rble__quote"><p>“{E(ex["quote"])}”</p></div><div class="rble__author">{SVG["badge"]}<p>{E(ex["author"])}</p></div></div></div>'
            f'<div class="rble__media">{picture(im, ex.get("alt", ex["title"]), 616, 560)}</div></div></div>'))
    of = spec["offer"]
    risk = ""
    if of.get("meta"):
        risk = (f'<div class="rblof__risk"><p>{of["meta"][0]}</p><span class="rblof__divider"></span><p>{of["meta"][1]}</p></div>')
    deal = f'<p class="rblof__deal">DEAL ENDING IN: <b data-rblof-timer data-deadline="{E(tb["deadline"])}">--:--:--</b></p>' if tb.get("deadline") else ""
    out.append(sec("listicle-offer",
        f'<div class="rblof" id="gsl-offer"><div class="rblof__pill">{E(of["pill"])}</div><div class="rblof__card">'
        f'<div class="rblof__media"><img src="{of["image"]}" alt="{E(of.get("alt",""))}" loading="lazy" width="800" height="800"></div>'
        f'<div class="rblof__content"><h2 class="rblof__title"><span class="rblof__accent">{E(of["accent"])}</span> {E(of["title"])}</h2>'
        f'<div class="rblof__sub"><p>{E(of["sub"])}</p></div><div class="rblof__cta-wrap"><a class="rblof__cta" href="{E(of["href"])}">{E(of["cta"])}</a>{deal}</div>'
        f'<div class="rblof__meta">{risk}<p class="rblof__guarantee">{E(of["guarantee"])}</p></div></div></div></div>'))
    ft = spec.get("footer", {})
    # theme chrome kept (takeover false) → the theme footer already prints the copyright; keep only the FDA line
    copy = f'<p class="rblft__copyright">{E(ft.get("copyright",""))}</p>' if spec.get("takeover") else ""
    out.append(sec("listicle-footer", f'<div class="rblft"><p class="rblft__disclaimer">{E(ft.get("disclaimer",""))}</p>{copy}</div>'))
    return "".join(out)


# ---------- advertorial (reference: /pages/advv-1) ----------
ICON_CAL = '<svg viewBox="0 0 24 24" fill="none" stroke="#265392" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></svg>'
ICON_BOX = '<svg viewBox="0 0 24 24" fill="none" stroke="#265392" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 8l-9-5-9 5 9 5 9-5z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/></svg>'
ICON_SHIELD = '<svg viewBox="0 0 24 24" fill="none" stroke="#265392" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4z"/><path d="M9 12l2 2 4-4"/></svg>'
ICON_USER = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/></svg>'
ICON_BAG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 8h14l-1 13H6L5 8z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/></svg>'


def render_advertorial(spec, imgs, brand):
    out = []
    hd = spec.get("header")
    if hd:
        out.append(f'<div class="gslh"><div class="gslh__in"><a class="gslh__shop" href="#featured-product">{E(hd.get("shop_text","Shop Now"))}</a>'
                   f'<a class="gslh__logo" href="{E(brand["domain"])}/"><img src="{E(hd["logo"])}" alt="{E(brand["name"])}" width="160" height="34"></a>'
                   f'<div class="gslh__icons"><a href="{E(brand["domain"])}/account" aria-label="Account">{ICON_USER}</a>'
                   f'<a href="{E(brand["domain"])}/cart" aria-label="Cart">{ICON_BAG}</a></div></div></div>\n')
    h = spec["hero"]
    im = imgs.slot(h.get("image"), "hero", 616 / 700, 880, 616 / 700, 750)
    out.append(sec("listicle-hero",
        f'<div class="rblh"><div class="rblh__inner"><div class="rblh__media">{picture(im, h.get("alt", spec["title"]), 616, 700, eager=True)}</div>'
        f'<div class="rblh__content"><h1 class="rblh__title">{E(h["title"])}</h1><div class="rblh__body"><p>{h["body_html"]}</p></div>'
        f'<div class="rblh__cta"><a class="rblh__button" href="#featured-product"><span>{E(h["cta"])}</span>{SVG["hero_arrow"]}</a>'
        f'<div class="rblh__guarantee">{SVG["shield"]}<p>{E(h["guarantee"])}</p></div></div></div></div></div>'))
    for i, it in enumerate(spec["items"]):
        side = "right" if i % 2 == 0 else "left"
        if it.get("chart"):
            media = chart_html(it["chart"])
        else:
            imr = imgs.slot(it.get("image"), f"row{i+1}", 616 / 590, 924, 1.0, 750)
            media = picture(imr, it.get("alt", it["title"]), 616, 590)
        out.append(sec("listicle-image-text",
            f'<div class="rblit rblit--image-{side}"><div class="rblit__inner"><div class="rblit__content">'
            f'<div class="rblit__header"><div class="rblit__eyebrow" aria-label="Section {i+1}"><span>{i+1}</span></div>'
            f'<h2 class="rblit__title">{E(it["title"])}</h2></div><div class="rblit__body">{it["body"]}</div></div>'
            f'<div class="rblit__media-wrap"><div class="rblit__media">{media}</div></div></div></div>'))
    ex = spec.get("expert")
    if ex:
        n = len(spec["items"]) + 1
        imx = imgs.slot(ex.get("image"), "expert", 616 / 560, 924, 900 / 1261, 750)
        out.append(sec("listicle-expert",
            f'<div class="rble"><div class="rble__inner"><div class="rble__content"><div class="rble__header">'
            f'<div class="rble__eyebrow" aria-label="Section {n}"><span>{n}</span></div><h2 class="rble__title">{E(ex["title"])}</h2></div>'
            f'<div class="rble__review"><div class="rble__stars" aria-label="{ex.get("stars",5)} star review">{stars(ex.get("stars",5))}</div>'
            f'<div class="rble__quote"><p>“{E(ex["quote"])}”</p></div><div class="rble__author">{SVG["badge"]}<p>{E(ex["author"])}</p></div></div></div>'
            f'<div class="rble__media">{picture(imx, ex.get("alt", ex["title"]), 616, 560)}</div></div></div>'))
    out.append(render_featured_product(spec, imgs))
    tl = spec.get("testimonials") or []
    if tl:
        cards = ""
        for t in tl:
            det = "".join(f"<p>{E(d)}</p>" for d in t.get("details", []))
            cards += (f'<article class="rblr__card" role="listitem"><div class="rblr__top"><div class="rblr__stars" aria-label="{t.get("stars",5)} star review">{stars(t.get("stars",5))}</div>'
                      f'<div class="rblr__copy"><h3>{E(t["title"])}</h3><p>“{E(t["quote"])}”</p></div></div>'
                      f'<div class="rblr__meta"><div class="rblr__name">{SVG["badge"]}<p>{E(t["name"])}</p></div><div class="rblr__details">{det}</div></div></article>')
        dots = "".join(f'<span class="{"is-active" if k == 0 else ""}" data-rblr-dot></span>' for k in range(len(tl)))
        out.append(sec("listicle-reviews",
            f'<div class="rblr" data-rblr-section="gsl"><h2 class="rblr__title">{E(spec.get("testimonials_heading","What Our Customers Say"))}</h2>'
            f'<div class="rblr__track-wrap"><div class="rblr__track" role="list" tabindex="0" aria-label="Customer reviews" data-rblr-track>{cards}</div>'
            f'<div class="rblr__dots" aria-hidden="true">{dots}</div></div>'
            + (f'<p class="gslr__src">{spec["testimonials_source_html"]}</p>' if spec.get("testimonials_source_html") else "")
            + '</div>'))
    fq = spec.get("faq") or []
    if fq:
        items = ""
        for k, f in enumerate(fq):
            items += (f'<details class="rbq-it"{" open" if k == 0 else ""}><summary class="rbq-sm"><span>{E(f["q"])}</span>'
                      f'<span class="rbq-ic" aria-hidden="true">{SVG["faq_plus"]}</span></summary><div class="rbq-an"><p>{f["a"]}</p></div></details>')
        imf = imgs.slot(spec.get("faq_image"), "faq", 720 / 1036, 720, 720 / 1036, 750)
        fc = spec.get("faq_cta", {})
        out.append(sec("faq",
            f'<div class="rbq-w"><div class="rbq-i"><div class="rbq-l"><h2 class="rbq-tt">FAQs</h2><div class="rbq-list">{items}</div>'
            f'<div class="rbq-cta"><a class="rb-btn-primary rbq-bn" href="#featured-product"><span>{E(fc.get("text","Shop now"))}</span>{SVG["faq_arrow"]}</a>'
            f'<div class="rb-guarantee">{SVG["rb_guarantee"]}<p>{E(fc.get("guarantee",""))}</p></div></div></div>'
            f'<div class="rbq-r"><div class="rbq-img">{picture(imf, spec.get("faq_alt","FAQs"), 720, 1036)}</div></div></div></div>'))
    ft = spec.get("footer", {})
    if ft.get("columns"):
        cols = "".join(f'<div class="gslf__col"><h3>{E(c["heading"])}</h3><ul>' + "".join(f'<li><a href="{E(l["href"])}">{E(l["text"])}</a></li>' for l in c["links"]) + "</ul></div>" for c in ft["columns"])
        nav = "".join(f'<a href="{E(l["href"])}">{E(l["text"])}</a>' for l in ft.get("legal", []))
        out.append(f'<footer class="gslf"><div class="gslf__in"><div class="gslf__cols">{cols}</div>'
                   f'<div class="gslf__logo" aria-hidden="true"><img src="{E(ft["logo"])}" alt="" loading="lazy" width="420" height="90"></div>'
                   f'<div class="gslf__bottom"><span>{E(ft.get("copyright",""))}</span><nav>{nav}</nav></div>'
                   f'<div class="gslf__disc"><p>{E(ft.get("disclaimer",""))}</p></div></div></footer>\n')
    return "".join(out)


def render_featured_product(spec, imgs):
    p = spec["product"]
    gal = []
    for k, g in enumerate(p.get("gallery", [])):
        s = imgs.slot(g["image"], f"gal{k+1}", 1.0, 800, 1.0, 750) if not g["image"].startswith("http") else {"d": g["image"], "m": g["image"]}
        gal.append((s, g.get("alt", p["name"])))
    main = gal[0][0]["d"] if gal else ""
    thumbs = "".join(f'<button type="button" class="gslfp__thumb{" is-active" if k == 0 else ""}" data-gslfp-thumb="{E(s["d"])}" aria-label="Show image {k+1}"><img src="{E(s["d"])}" alt="{E(a)}" loading="lazy" width="160" height="160"></button>' for k, (s, a) in enumerate(gal))
    tps = "".join(f'<li class="rbp-tp"><span class="rbp-tp-ic" aria-hidden="true">{SVG["tp_tick"]}</span><span>{E(t)}</span></li>' for t in p.get("tps", []))
    opts = ""
    for k, o in enumerate(p["options"]):
        tag = f'<div class="nw-bundle-item-tag">{E(o["tag"])}</div>' if o.get("tag") else ""
        comp = (f'<span class="visually-hidden">Regular price</span><s>{E(o["compare"])}</s>') if o.get("compare") else ""
        disc = f'<div class="nw-bundle-item-discount"><span class="nw-bundle-item-discount-text">{E(o["badge"])}</span></div>' if o.get("badge") else ""
        opts += (f'<div class="nw-bundle-item"><input type="radio" name="gsl-bundle" id="gsl-bundle-{k}" value="{o["variant_id"]}" data-qty="{o.get("qty",1)}" '
                 f'data-plan="{o.get("selling_plan","")}"{" checked" if k == 0 else ""}><label for="gsl-bundle-{k}">{tag}'
                 f'<div class="nw-bundle-item-radio" aria-hidden="true"><span class="nw-bundle-item-radio-icon"></span></div>'
                 f'<div class="nw-bundle-item-title"><span class="nw-bundle-item-pack-title">{E(o["title"])}</span><span class="nw-bundle-item-perday-title">{E(o["sub"])}</span></div>'
                 f'{disc}<div class="nw-bundle-item-price">{comp}<span class="visually-hidden">Sale price</span><span class="nw-bundle-item-price-value">{E(o["price"])}</span></div></label></div>')
    o0 = p["options"][0]
    icons = [ICON_CAL, ICON_BOX, ICON_SHIELD]
    itr = "".join(f'<div class="icon-text-row__item"><div class="icon-text-row__icon">{icons[k % 3]}</div><div class="icon-text-row__text">{E(t)}</div></div>' for k, t in enumerate(p.get("icon_row", [])))
    once = p.get("buy_once")
    once_html = ""
    if once:
        once_html = (f'<div class="gslfp__once"><button type="submit" form="gsl-once-form">{E(once["text"])}</button>'
                     f'<p>{E(once.get("note",""))}</p></div>'
                     f'<form id="gsl-once-form" method="post" action="/cart/add" hidden><input type="hidden" name="id" value="{once["variant_id"]}"><input type="hidden" name="quantity" value="1"></form>')
    rating = ""
    if p.get("rating_line"):
        rating = f'<div class="rbp-rating"><div class="rbp-stars" aria-hidden="true">{stars(p.get("rating_stars",5), "rbp_star")}</div><span class="rbp-rating-txt">{E(p["rating_line"])}</span></div>'
    hl = f'<p class="rbp-highlight">{E(p["highlight"])}</p>' if p.get("highlight") else ""
    return sec("featured-product",
        f'<div class="rebrand gslfp" id="featured-product"><div class="gslfp__grid"><div class="gslfp__media">'
        f'<div class="gslfp__main"><img src="{E(main)}" alt="{E(p["name"])}" width="800" height="800" loading="lazy" data-gslfp-main>'
        f'<button type="button" class="gslfp__nav gslfp__nav--prev" aria-label="Previous image" data-gslfp-step="-1">{SVG["gal_prev"]}</button>'
        f'<button type="button" class="gslfp__nav gslfp__nav--next" aria-label="Next image" data-gslfp-step="1">{SVG["gal_next"]}</button></div>'
        f'<div class="gslfp__thumbs">{thumbs}</div></div>'
        f'<div class="gslfp__info product__info-container"><div class="rbp-head"><div class="rbp-head-top">{rating}<h2 class="rbp-title">{E(p["name"])}</h2></div>'
        f'<div class="rbp-desc"><p>{E(p["desc"])}</p></div>{hl}</div><ul class="rbp-tps">{tps}</ul>'
        f'<form class="nw-bundle-wrap" method="post" action="/cart/add" data-gsl-bundle><input type="hidden" name="id" value="{o0["variant_id"]}">'
        f'<input type="hidden" name="quantity" value="{o0.get("qty",1)}"><input type="hidden" name="selling_plan" value="{o0.get("selling_plan","")}">'
        f'<div class="nw-subscribe-section"><p class="h3 nw-subscribe-title">{E(p.get("options_title","Subscribe & Save:"))}</p><div class="nw-bundle-items" role="radiogroup">{opts}</div></div>'
        f'<div class="nw-bundle-cta"><button class="button" type="submit"><span class="button-text">{E(p["cta"])}</span>{SVG["btn_arrow"]}</button></div></form>'
        f'<div class="icon-text-row"><div class="icon-text-row__container">{itr}</div></div>{once_html}</div></div></div>', ' id="gsl-fp"')


JS = r"""<script>(function(){
var r=document.querySelector('.gsl-ref');if(!r)return;
/* featured product gallery */
var main=r.querySelector('[data-gslfp-main]'),th=[].slice.call(r.querySelectorAll('[data-gslfp-thumb]')),ix=0;
function show(i){if(!th.length)return;ix=(i+th.length)%th.length;main.src=th[ix].getAttribute('data-gslfp-thumb');th.forEach(function(t,k){t.classList.toggle('is-active',k===ix)});}
th.forEach(function(t,k){t.addEventListener('click',function(){show(k)})});
[].forEach.call(r.querySelectorAll('[data-gslfp-step]'),function(b){b.addEventListener('click',function(){show(ix+parseInt(b.getAttribute('data-gslfp-step'),10))})});
/* bundle radios -> cart form (variant / quantity / selling plan) */
var f=r.querySelector('[data-gsl-bundle]');
if(f){[].forEach.call(f.querySelectorAll('input[name=gsl-bundle]'),function(x){x.addEventListener('change',function(){
f.querySelector('[name=id]').value=x.value;f.querySelector('[name=quantity]').value=x.getAttribute('data-qty');
var sp=f.querySelector('[name=selling_plan]');sp.value=x.getAttribute('data-plan')||'';sp.disabled=!sp.value;})});
var sp0=f.querySelector('[name=selling_plan]');sp0.disabled=!sp0.value;}
/* reviews carousel dots (reference rblr script) */
var tr=r.querySelector('[data-rblr-track]');if(tr){var cards=[].slice.call(tr.querySelectorAll('.rblr__card')),dots=[].slice.call(r.querySelectorAll('[data-rblr-dot]'));
function upd(){var c=tr.scrollLeft+tr.clientWidth/2,best=0,bd=1e9;cards.forEach(function(cd,i){var d=Math.abs(cd.offsetLeft+cd.offsetWidth/2-c);if(d<bd){bd=d;best=i}});dots.forEach(function(d,i){d.classList.toggle('is-active',i===best)})}
tr.addEventListener('scroll',function(){requestAnimationFrame(upd)},{passive:true});upd();}
/* countdowns: only when the spec carries a real deadline (data-deadline ISO) */
[].forEach.call(r.querySelectorAll('[data-deadline]'),function(el){var end=new Date(el.getAttribute('data-deadline'));if(isNaN(end))return;
function t(){var s=Math.max(0,Math.floor((end-new Date())/1000)),h=String(Math.floor(s/3600)).padStart(2,'0'),m=String(Math.floor(s%3600/60)).padStart(2,'0'),ss=String(s%60).padStart(2,'0');
var H=el.querySelector('[data-rbltb-h]');if(H){H.textContent=h;el.querySelector('[data-rbltb-m]').textContent=m;el.querySelector('[data-rbltb-s]').textContent=ss}else{el.textContent=h+':'+m+':'+ss}}t();setInterval(t,1000)});
})();</script>"""


def load_brand(store):
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from landing_render import load_brand as lb
    return lb(store)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sp = os.path.abspath(sys.argv[1])
    spec = json.load(open(sp))
    brand = load_brand(spec.get("store", "wellnessnest"))
    out_dir = os.path.join(os.path.dirname(sp), spec["slug"])
    os.makedirs(out_dir, exist_ok=True)
    imgs = Imgs(out_dir)
    kind = spec["template"]
    # The gsl-ref-* theme template is ONE shared file installed in the live theme with the base store's palette, so a
    # sub-brand spec (AgeAura "extends" wellnessnest) must render with that same palette — otherwise the preview and
    # templates/landing/page.<suffix>.liquid drift from what the live page actually shows (fixed 2026-10-08).
    vis = load_brand(brand["extends"]) if brand.get("extends") else brand
    pal = palette(vis)
    inner = render_listicle(spec, imgs) if kind == "listicle" else render_advertorial(spec, imgs, brand)
    body = brand_swap(f'<div class="gsl-ref gsl-ref--{kind}">\n{inner}</div>\n', pal)
    js = brand_swap(JS, pal)   # lives in the theme template (Shopify page bodies are not a place for scripts)
    open(os.path.join(out_dir, "body.html"), "w").write(body)
    css = build_css(kind, vis)
    open(os.path.join(out_dir, "page.css"), "w").write(css)
    font_link = brand.get("fonts", {}).get("preview_font_link", "")
    hide = open(os.path.join(ROOT, "templates", "landing", "hide_theme_chrome.html")).read().replace("{% layout none %}", "layout-none") if spec.get("takeover") else ""   # a Liquid tag inside a CSS comment would still execute
    suffix = spec.get("template_suffix")
    if suffix:
        tpl = ("{% comment %}GenSeo reference-replica template (" + kind + "), generated by scripts/landing_clone.py — do not edit by hand; "
               "re-render and bump the suffix instead (compiled-template cache).{% endcomment %}\n"
               + (f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="{font_link}" rel="stylesheet">\n' if font_link else "")
               + hide + f'<style id="gsl-ref-css">{css}</style>\n<div class="gsl-ref-page">{{{{ page.content }}}}</div>\n' + js + "\n")
        open(os.path.join(ROOT, "templates", "landing", f"page.{suffix}.liquid"), "w").write(tpl)
    prev_body = re.sub(r'(src|srcset)="(/[^"]+)"', lambda m: f'{m.group(1)}="file://{m.group(2)}"', body)
    preview = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
               f'<title>{E(spec["title"])}</title>' + (f'<link href="{font_link}" rel="stylesheet">' if font_link else "")
               + f'<style>body{{margin:0;background:#fff}}{css}</style></head><body>{prev_body}{js}</body></html>')
    open(os.path.join(out_dir, "preview.html"), "w").write(preview)
    n_img = len(os.listdir(imgs.dir)) if os.path.isdir(imgs.dir) else 0
    big = [f for f in (os.listdir(imgs.dir) if os.path.isdir(imgs.dir) else []) if os.path.getsize(os.path.join(imgs.dir, f)) > 80 * 1024]
    print(f"rendered {kind}: {out_dir}/preview.html · body {len(body)//1024} KB · css {len(css)//1024} KB · {n_img} crops" + (f" · >80KB: {big}" if big else ""))
    if big:
        sys.exit(1)


if __name__ == "__main__":
    main()

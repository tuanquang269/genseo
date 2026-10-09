#!/usr/bin/env python3
"""Render a GenSeo landing page (template 'listicle' or 'advertorial') from a JSON spec + store brand tokens.

  /usr/bin/python3 scripts/landing_render.py landing_drafts/<slug>.json
      -> landing_drafts/<slug>/body.html     Shopify-safe body_html (inline CSS only, no <style>/<script>)
      -> landing_drafts/<slug>/preview.html  standalone local preview (store header, fonts, body)

Structure is reverse-engineered from the two reference pages served on the MacBook at :8790
(~/PATI/work/omnicreatine-local-clone — rb-section--listicle-* sections), re-skinned with the
store's brand tokens (brand/<store>.json). See templates/landing/README.md for the section map
and the spec schema. Nothing here invents copy: every string comes from the spec, and any
"[[PLACEHOLDER: ...]]" renders as a visible yellow chip so it can never pass as real.

Theme delivery follows Kevin's vault skill `claude-design-dtc-listicle-advertorial` (+ PATI-ADAPTATION.md) and the
WellnessNest theme gotchas (`wellnessnest-advertorial-builder`, `crawl-funnel-to-shopify`): the live theme has NO
default page template, so every landing page renders through `templates/page.<suffix>.liquid` (written to
templates/landing/ by this script). That template holds the ONLY <style> block (reset + the one grid media query,
namespaced `gsl-` / `[data-gsl-*]` so nothing collides with the dawn-derived theme) and outputs {{ page.content }}.
body_html itself stays inline-CSS-only; without the template it degrades to a clean single column.
Funnel order (posture "hybrid"/"editorial"): no product in the numbered findings; the bridge (daily use ->
format friction -> "convenience is part of consistency" -> product as one option) opens the sticky zone, so the
sticky bar only appears once the bridge scrolls in (CSS position:sticky at the end of that zone, no JS).
"""
import html, json, os, re, sys
import brand_rules

GRID_CSS = ("<style id=\"gsl-base\">.gsl-landing *{box-sizing:border-box}.gsl-landing img{max-width:100%}"
            ".gsl-landing a:focus-visible{outline:3px solid #1e3a29;outline-offset:2px}"
            "[data-gsl-row]{grid-template-columns:1fr}[data-gsl-split]{grid-template-columns:1fr}"
            "@media (min-width:760px){[data-gsl-row]{grid-template-columns:2fr 1fr}[data-gsl-split]{grid-template-columns:1fr 1fr}}"
            "@media (prefers-reduced-motion:reduce){.gsl-landing *{scroll-behavior:auto!important}}</style>")
SHELL = 1160

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PH_RE = re.compile(r"\[\[PLACEHOLDER:\s*(.*?)\]\]", re.S)
ALLOWED = {"p", "strong", "em", "a", "ul", "ol", "li", "br", "b", "i", "sup"}


def load_brand(store):
    b = json.load(open(os.path.join(ROOT, "brand", f"{store}.json")))
    if b.get("extends"):
        base = load_brand(b["extends"])
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                base[k] = {**base[k], **v}
            else:
                base[k] = v
        b = base
    return b


class R:
    def __init__(self, brand):
        self.b = brand; self.c = brand["colors"]; self.f = brand["fonts"]; self.r = brand["radius"]

    # ---------- text helpers ----------
    def ph(self, s):
        c = self.c
        return PH_RE.sub(lambda m: (f'<span style="background:{c["placeholder_bg"]};color:{c["placeholder_text"]};'
                                    f'border:1px dashed {c["placeholder_text"]};border-radius:6px;padding:1px 6px;'
                                    f'font-weight:600;">⚠ PLACEHOLDER: {m.group(1)}</span>'), s)

    def t(self, s):
        """plain text field -> escaped, placeholders highlighted"""
        return self.ph(html.escape(s or ""))

    def rich(self, s):
        """limited-HTML field: drop any tag not in ALLOWED, strip attributes except a[href]"""
        def fix(m):
            close, tag, attrs = m.group(1), m.group(2).lower(), m.group(3) or ""
            if tag not in ALLOWED:
                return ""
            if tag == "a" and not close:
                h = re.search(r'href="([^"]+)"', attrs)
                return (f'<a href="{html.escape(h.group(1))}" style="color:{self.c["primary_dark"]};'
                        f'text-decoration:underline;">' if h else "<a>")
            if tag == "p" and not close:
                return f'<p style="margin:0 0 14px;line-height:1.7;">'
            return f"<{close}{tag}>"
        out = re.sub(r"<(/?)([a-zA-Z0-9]+)([^>]*)>", fix, s or "")
        if not out.lstrip().startswith("<"):
            out = f'<p style="margin:0 0 14px;line-height:1.7;">{out}</p>'
        return self.ph(out)

    # ---------- atoms ----------
    def tag(self, name, style, inner):
        return f'<{name} style="{style}">{inner}</{name}>'

    def btn(self, cta, big=True, dark=False):
        if not cta:
            return ""
        bg = self.c["ink"] if dark else self.c["primary"]
        pad = "16px 38px" if big else "12px 28px"
        return (f'<a href="{html.escape(cta["href"])}" target="_blank" rel="noopener" style="display:inline-block;min-height:44px;background:{bg};color:#ffffff;'
                f'font-weight:700;font-family:{self.f["body"]};letter-spacing:.04em;text-transform:uppercase;'
                f'padding:{pad};border-radius:{self.r["button"]};text-decoration:none;font-size:15px;">'
                f'{self.t(cta["text"])} &rarr;</a>')

    def img(self, src, alt, radius=None, h=None, contain=False):
        if not src:
            return ""
        if not src.startswith("http"):          # spec paths are repo-relative (tmp_images/<slug>/<name>.webp)
            src = os.path.join(ROOT, src)
        st = f"width:100%;height:{h}px;object-fit:cover;" if h else "width:100%;height:auto;"
        if contain:                              # real pack shot: never crop (vault skill §6)
            st = "width:100%;height:auto;object-fit:contain;"
        return (f'<img src="{html.escape(src)}" alt="{html.escape(alt or "")}" loading="lazy" '
                f'style="display:block;{st}border-radius:{radius or self.r["image"]};">')

    def pill(self, text, dark=False):
        bg, fg = (self.c["ink"], "#ffffff") if dark else (self.c["primary"], "#ffffff")
        return (f'<span style="display:inline-block;background:{bg};color:{fg};font-weight:700;font-size:13px;'
                f'padding:3px 12px;border-radius:{self.r["pill"]};letter-spacing:.05em;">{text}</span>')

    def stars(self, color=None):
        return f'<span style="color:{color or self.c["star"]};letter-spacing:2px;font-size:16px;">★★★★★</span>'

    def wrap(self, inner, bg=None, pad="40px 20px", color=None):
        return (f'<div style="background:{bg or "transparent"};padding:{pad};{"color:"+color+";" if color else ""}">'
                f'<div style="max-width:{SHELL}px;margin:0 auto;">{inner}</div></div>')

    def h(self, level, text, size, color=None, extra=""):
        return (f'<h{level} style="font-family:{self.f["heading"]};font-weight:{self.f["heading_weight"]};'
                f'letter-spacing:{self.f["heading_letter_spacing"]};font-size:{size};line-height:1.2;margin:0 0 14px;'
                f'color:{color or self.c["ink"]};{extra}">{text}</h{level}>')

    # ---------- shared sections ----------
    def announcement(self, spec):
        a = spec.get("announcement")
        if not a:
            return ""
        return (f'<div style="background:{self.c["ink"]};color:#ffffff;text-align:center;padding:9px 16px;'
                f'font-size:13px;font-weight:600;letter-spacing:.04em;">{self.t(a)}</div>')

    def chart(self, ch):
        if not ch:
            return ""
        mx = max(b["value"] for b in ch["bars"]) or 1
        bars = ""
        for b in ch["bars"]:
            pct = max(4, int(100 * b["value"] / mx))
            col = self.c["primary"] if b.get("highlight") else self.c["border"]
            bars += (f'<div style="display:flex;align-items:center;gap:10px;margin:8px 0;">'
                     f'<div style="flex:0 0 38%;font-size:13px;color:{self.c["muted"]};">{self.t(b["label"])}</div>'
                     f'<div style="flex:1;background:{self.c["bg_panel"]};border-radius:8px;height:26px;">'
                     f'<div style="width:{pct}%;background:{col};height:26px;border-radius:8px;display:flex;align-items:center;'
                     f'justify-content:flex-end;padding-right:8px;box-sizing:border-box;font-size:12px;font-weight:700;'
                     f'color:{"#ffffff" if b.get("highlight") else self.c["ink"]};">{self.t(b.get("display", str(b["value"])))}</div></div></div>')
        src = self.tag("p", f'margin:10px 0 0;font-size:11px;color:{self.c["muted"]};', "Source: " + self.t(ch["source"])) if ch.get("source") else ""
        return (f'<div style="background:#ffffff;border:1px solid {self.c["border"]};border-radius:{self.r["card"]};'
                f'padding:20px 22px;box-shadow:0 2px 10px rgba(0,0,0,.04);">'
                f'{self.h(3, self.t(ch["title"]), "18px", extra="text-align:center;")}{bars}{src}</div>')

    def expert(self, ex):
        if not ex:
            return ""
        c = self.c
        quote = (f'<div style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.15);'
                 f'border-radius:{self.r["card"]};padding:22px;text-align:center;margin-top:18px;">'
                 f'{self.stars(c["primary_light"])}<p style="margin:12px 0;font-size:16px;line-height:1.6;color:#ffffff;">'
                 f'&ldquo;{self.t(ex["quote"])}&rdquo;</p><p style="margin:0;font-size:13px;color:{c["primary_light"]};">'
                 f'&#10003; {self.t(ex["attribution"])}</p></div>')
        left = (f'<div style="flex:1 1 320px;">{self.pill(ex.get("number",""), dark=False) if ex.get("number") else ""}'
                f'{self.h(2, self.t(ex["heading"]), "30px", color="#ffffff", extra="margin-top:12px;")}'
                f'{self.tag("div", "color:#e8e8ee;font-size:15px;line-height:1.7;", self.rich(ex["body"])) if ex.get("body") else ""}{quote}</div>')
        right = f'<div style="flex:1 1 300px;">{self.img(ex.get("image"), ex.get("alt",""))}</div>' if ex.get("image") else ""
        return self.wrap(f'<div style="display:flex;flex-wrap:wrap;gap:32px;align-items:center;">{left}{right}</div>',
                         bg=f'linear-gradient(135deg,{c["dark_section"]},{c["ink"]})', pad="56px 20px")

    def testimonials(self, ts, heading):
        if not ts:
            return ""
        cards = ""
        for t in ts:
            cards += (f'<div style="flex:1 1 260px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.15);'
                      f'border-radius:{self.r["card"]};padding:20px;color:#ffffff;">{self.stars(self.c["primary_light"])}'
                      f'<p style="font-weight:700;margin:10px 0 6px;">{self.t(t.get("title",""))}</p>'
                      f'<p style="margin:0 0 12px;font-size:14px;line-height:1.6;color:#e8e8ee;">&ldquo;{self.t(t["quote"])}&rdquo;</p>'
                      f'<p style="margin:0;font-size:13px;color:{self.c["primary_light"]};">&#9679; {self.t(t["name"])}</p>'
                      f'{self.tag("p", "margin:4px 0 0;font-size:12px;color:#c9c9d3;", self.t(t["detail"])) if t.get("detail") else ""}</div>')
        return self.wrap(self.h(2, self.t(heading), "32px", color="#ffffff", extra="text-align:center;margin-bottom:26px;")
                         + f'<div style="display:flex;flex-wrap:wrap;gap:18px;">{cards}</div>',
                         bg=f'linear-gradient(135deg,{self.c["dark_section"]},{self.c["ink"]})', pad="56px 20px")

    def faq(self, faqs):
        if not faqs:
            return ""
        items = "".join(
            f'<details style="background:#ffffff;border:1px solid {self.c["border"]};border-radius:12px;padding:14px 18px;margin:10px 0;">'
            f'<summary style="cursor:pointer;font-weight:700;color:{self.c["ink"]};">{self.t(f["q"])}</summary>'
            f'<div style="margin-top:10px;color:{self.c["text"]};font-size:15px;">{self.rich(f["a"])}</div></details>' for f in faqs)
        return self.wrap(self.h(2, "FAQs", "32px") + items, bg=self.c["bg_soft"], pad="48px 20px")

    def sources(self, srcs):
        if not srcs:
            return ""
        li = "".join(f'<li style="margin:4px 0;"><a href="{html.escape(s["url"])}" style="color:{self.c["muted"]};" rel="nofollow noopener">{self.t(s["label"])}</a></li>' for s in srcs)
        return self.wrap(f'<p style="font-weight:700;margin:0 0 6px;color:{self.c["ink"]};font-size:14px;">Sources</p>'
                         f'<ol style="margin:0;padding-left:20px;font-size:12px;color:{self.c["muted"]};">{li}</ol>', pad="24px 20px")

    def footer(self, spec):
        return (f'<div style="background:{self.c["ink"]};color:#ffffff;text-align:center;padding:22px 16px;font-size:12px;line-height:1.6;">'
                f'<p style="margin:0 0 6px;">{html.escape(self.b["disclaimer"])}</p>'
                f'<p style="margin:0;opacity:.8;">&copy; 2026 {html.escape(self.b.get("legal_footer", self.b["name"]))}</p></div>')

    def sticky(self, spec):
        s = spec.get("sticky_cta")
        if not s:
            return ""
        return (f'<div style="position:sticky;bottom:0;z-index:20;background:rgba(255,255,255,.97);border-top:1px solid {self.c["border"]};'
                f'box-shadow:0 -4px 14px rgba(0,0,0,.06);padding:10px 16px;display:flex;flex-wrap:wrap;align-items:center;'
                f'justify-content:center;gap:14px;"><span style="font-weight:700;color:{self.c["ink"]};font-size:14px;">'
                f'{self.t(s.get("label",""))}</span>{self.btn(s, big=False)}</div>')

    def item_row(self, i, it, n_style, flip=False):
        img = it.get("image")
        media = (self.img(img, it.get("alt", "")) if img else self.chart(it.get("chart"))) if (img or it.get("chart")) else ""
        if n_style == "pill":
            num = self.pill(f"{i:02d}", dark=True)
        elif n_style == "circle":
            num = (f'<span style="display:inline-flex;width:34px;height:34px;border-radius:50%;border:2px solid {self.c["ink"]};'
                   f'align-items:center;justify-content:center;font-weight:700;color:{self.c["ink"]};">{i}</span>')
        else:
            num = ""
        label = self.tag("p", f"margin:10px 0 0;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:{self.c['primary_dark']};",
                         "Evidence: " + self.t(it["evidence"])) if it.get("evidence") else ""
        text = (f'<div>{num}{self.h(2, self.t(it["title"]), "28px", extra="margin-top:12px;")}'
                f'<div style="color:{self.c["text"]};font-size:17px;">{self.rich(it["body"])}</div>{label}'
                f'{self.tag("div", "margin-top:14px;", self.chart(it["chart"])) if (img and it.get("chart")) else ""}</div>')
        grid = "display:grid;gap:36px;align-items:center;margin:0 0 56px;"
        if not media:
            return f'<div style="margin:0 0 56px;max-width:760px;">{text}</div>'
        return f'<div data-gsl-row style="{grid}">{text}<div>{media}</div></div>'

    def prose(self, heading, body, eyebrow=None):
        eb = self.tag("p", f"margin:0 0 8px;font-weight:700;color:{self.c['primary_dark']};letter-spacing:.06em;font-size:13px;text-transform:uppercase;", self.t(eyebrow)) if eyebrow else ""
        return (f'<div style="max-width:760px;">{eb}{self.h(2, self.t(heading), "30px") if heading else ""}'
                f'<div style="color:{self.c["text"]};font-size:17px;">{self.rich(body)}</div></div>')

    def bridge(self, b):
        """daily use -> format friction -> convenience is part of consistency -> product as one option"""
        if not b:
            return ""
        media = f'<div>{self.img(b.get("image"), b.get("alt", ""))}</div>' if b.get("image") else ""
        inner = self.prose(b.get("heading"), b["body"], b.get("eyebrow"))
        body = f'<div data-gsl-row style="display:grid;gap:36px;align-items:center;">{inner}{media}</div>' if media else inner
        return self.wrap(body, bg=self.c["bg_soft"], pad="48px 20px")

    def checklist(self, ck):
        if not ck:
            return ""
        li = "".join(f'<li style="margin:10px 0;padding-left:30px;position:relative;"><span style="position:absolute;left:0;top:0;'
                     f'color:{self.c["primary"]};font-weight:700;">&#10003;</span>{self.t(x)}</li>' for x in ck["items"])
        return self.wrap(f'<div style="max-width:760px;">{self.h(2, self.t(ck["heading"]), "28px")}'
                         f'{self.tag("p", "margin:0 0 8px;color:" + self.c["muted"] + ";font-size:15px;", self.t(ck["intro"])) if ck.get("intro") else ""}'
                         f'<ul style="list-style:none;padding:0;margin:0;font-size:16px;color:{self.c["text"]};">{li}</ul></div>', pad="40px 20px")

    def final_cta(self, f):
        if not f:
            return ""
        return self.wrap(f'<div style="max-width:760px;margin:0 auto;text-align:center;">{self.h(2, self.t(f["heading"]), "30px")}'
                         f'{self.tag("p", "margin:0 0 20px;color:" + self.c["text"] + ";font-size:16px;line-height:1.6;", self.t(f["body"])) if f.get("body") else ""}'
                         f'{self.btn(f["cta"])}</div>', bg=self.c["bg_panel"], pad="48px 20px")

    # ---------- templates ----------
    def sticky_zone(self, s, inner_parts):
        """sticky bar = last child of the zone, so it only sticks while the zone (bridge -> end) is in view"""
        bar = self.sticky(s)
        return f'<div class="gsl-sticky-zone">{"".join(x for x in inner_parts if x)}{bar}</div>'

    def listicle(self, s):
        c = self.c
        posture = s.get("posture", "hybrid")
        title = self.t(s["title"])
        if s.get("title_highlight"):
            hl = html.escape(s["title_highlight"])
            title = title.replace(hl, f'<span style="color:{c["primary"]};">{hl}</span>', 1)
        by = s.get("byline", {})
        header = (f'<div style="background:#ffffff;border-radius:20px;padding:32px 30px;max-width:760px;'
                  f'box-shadow:0 4px 20px rgba(0,0,0,.05);">{self.h(1, title, "clamp(30px, 2vw + 22px, 40px)")}'
                  f'<p style="margin:10px 0 0;font-size:13px;color:{c["muted"]};">By <strong>{self.t(by.get("name",""))}</strong>'
                  f'{(" | " + self.t(by["role"])) if by.get("role") else ""}<br>Last updated {self.t(s.get("updated",""))}</p></div>'
                  + (f'<p style="margin:22px 0 0;font-size:16px;color:{c["text"]};max-width:760px;line-height:1.65;"><strong>Summary:</strong> {self.t(s["summary"])}</p>' if s.get("summary") else ""))
        out = [self.announcement(s) if posture != "editorial" else "", self.wrap(header, bg=c["bg_soft"], pad="40px 20px")]
        if s.get("intro"):
            out.append(self.wrap(self.prose(None, s["intro"]), pad="40px 20px 0"))
        rows = "".join(self.item_row(i + 1, it, "pill") for i, it in enumerate(s["items"]))
        out.append(self.wrap(rows, pad="48px 20px 8px"))
        out.append(self.expert(s.get("expert")))
        zone = [self.bridge(s.get("bridge")), self.offer(s.get("offer"), s.get("product")), self.checklist(s.get("checklist")),
                self.testimonials(s.get("testimonials"), s.get("testimonials_heading", "What Customers Say")) if posture != "editorial" else "",
                self.faq(s.get("faq")), self.final_cta(s.get("final_cta")), self.sources(s.get("sources"))]
        out.append(self.sticky_zone(s, zone) if posture != "editorial" else "".join(z for z in zone if z))
        out.append(self.footer(s))
        return "\n".join(x for x in out if x)

    def offer(self, o, p):
        if not o:
            return ""
        c = self.c
        img = self.img((p or {}).get("image"), (p or {}).get("name", ""), radius="12px", contain=True)
        facts = "".join(f'<li style="margin:6px 0;">&#10003; {self.t(b)}</li>' for b in (p or {}).get("bullets", []))
        inner = (f'<div data-gsl-split style="display:grid;gap:0;border:2px dashed {c["ink"]};border-radius:22px;background:#ffffff;overflow:hidden;">'
                 f'<div style="background:{c["bg_soft"]};padding:26px;display:flex;align-items:center;justify-content:center;">{img}</div>'
                 f'<div style="padding:34px 30px;text-align:center;">'
                 f'{self.pill(self.t(o["badge"]), dark=True) if o.get("badge") else ""}'
                 f'{self.h(2, self.t(o["headline"]), "32px", extra="margin-top:14px;")}'
                 f'<p style="color:{c["muted"]};font-size:15px;line-height:1.6;margin:0 0 14px;">{self.t(o.get("subhead",""))}</p>'
                 + (f'<ul style="list-style:none;padding:0;margin:0 auto 18px;text-align:left;display:inline-block;color:{c["text"]};font-size:15px;">{facts}</ul>' if facts else "")
                 + f'<div>{self.btn(o["cta"])}</div>'
                 + "".join(f'<p style="margin:14px 0 0;font-size:13px;color:{c["muted"]};">{self.t(x)}</p>' for x in o.get("fine_print", []))
                 + "</div></div>")
        return self.wrap(inner, bg=c["bg_panel"], pad="48px 20px")

    def product_block(self, p):
        if not p:
            return ""
        c = self.c
        bullets = "".join(f'<li style="margin:6px 0;">&#10003; {self.t(b)}</li>' for b in p.get("bullets", []))
        opts = ""
        for o in p.get("options", []):
            opts += (f'<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;border:2px solid '
                     f'{c["primary"] if o.get("highlight") else c["border"]};border-radius:12px;padding:12px 16px;margin:8px 0;'
                     f'background:{c["bg_soft"] if o.get("highlight") else "#ffffff"};"><div><strong>{self.t(o["label"])}</strong>'
                     f'<div style="font-size:12px;color:{c["muted"]};">{self.t(o.get("note",""))}</div></div>'
                     f'<strong style="font-size:18px;color:{c["ink"]};white-space:nowrap;">{self.t(o["price"])}</strong></div>')
        rating = f'<p style="margin:0 0 8px;font-size:13px;color:{c["muted"]};">{self.stars()} {self.t(p["rating_line"])}</p>' if p.get("rating_line") else ""
        inner = (f'<div data-gsl-split style="display:grid;gap:36px;align-items:start;">'
                 f'<div style="background:{c["bg_soft"]};border-radius:{self.r["image"]};padding:20px;">{self.img(p.get("image"), p.get("name",""), contain=True)}</div>'
                 f'<div>{rating}{self.h(2, self.t(p["name"]), "30px")}'
                 f'<p style="color:{c["text"]};font-size:16px;line-height:1.6;">{self.t(p.get("blurb",""))}</p>'
                 f'<ul style="list-style:none;padding:0;margin:0 0 16px;color:{c["text"]};font-size:15px;">{bullets}</ul>'
                 f'{opts}<div style="text-align:center;margin-top:16px;">{self.btn(p["cta"])}</div>'
                 + "".join(f'<p style="text-align:center;margin:10px 0 0;font-size:12px;color:{c["muted"]};">{self.t(x)}</p>' for x in p.get("fine_print", []))
                 + "</div></div>")
        return self.wrap(inner, pad="56px 20px")

    def advertorial(self, s):
        c = self.c
        posture = s.get("posture", "advertorial")
        hero = s["hero"]
        top = (f'<div style="background:#ffffff;border-bottom:1px solid {c["border"]};padding:12px 20px;">'
               f'<div style="max-width:{SHELL}px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;">'
               f'<a href="{html.escape(self.b["domain"])}" style="font-weight:700;font-size:13px;color:{c["ink"]};text-decoration:none;letter-spacing:.06em;">SHOP NOW</a>'
               f'<img src="{html.escape(self.b["logo"])}" alt="{html.escape(self.b["name"])}" style="height:34px;width:auto;">'
               f'<span style="width:70px;"></span></div></div>') if s.get("mini_header", True) else ""
        hero_cta = self.btn(hero.get("cta"), dark=True) if posture == "advertorial" else ""
        hero_html = (f'<div data-gsl-split style="display:grid;gap:36px;align-items:center;">'
                     f'<div>{self.img(hero.get("image"), hero.get("alt",""))}</div>'
                     f'<div>{self.tag("p", "margin:0 0 8px;font-weight:700;color:" + c["primary_dark"] + ";letter-spacing:.06em;font-size:13px;text-transform:uppercase;", self.t(hero["eyebrow"])) if hero.get("eyebrow") else ""}'
                     f'{self.h(1, self.t(s["title"]), "clamp(30px, 2vw + 22px, 40px)")}'
                     f'<p style="font-size:17px;line-height:1.65;color:{c["text"]};margin:0 0 22px;">{self.t(hero.get("subhead",""))}</p>'
                     f'{hero_cta}'
                     f'{self.tag("p", "margin:12px 0 0;font-size:13px;color:" + c["muted"] + ";", "&#128737; " + self.t(hero["trust_line"])) if hero.get("trust_line") else ""}'
                     f'</div></div>')
        by = s.get("byline", {})
        byline = (f'<p style="margin:0 0 30px;font-size:13px;color:{c["muted"]};">By <strong>{self.t(by.get("name",""))}</strong>'
                  f' &middot; Updated {self.t(s.get("updated",""))}</p>') if by else ""
        rows = "".join(self.item_row(i + 1, it, "circle") for i, it in enumerate(s["items"]))
        head = [self.announcement(s) if posture != "editorial" else "", top, self.wrap(hero_html, bg=c["bg_soft"], pad="40px 20px")]
        body = [self.wrap(byline + rows, pad="48px 20px 8px"), self.expert(s.get("expert")), self.bridge(s.get("bridge")),
                self.product_block(s.get("product")), self.checklist(s.get("checklist")),
                self.testimonials(s.get("testimonials"), s.get("testimonials_heading", "What Customers Say")) if posture != "editorial" else "",
                self.faq(s.get("faq")), self.final_cta(s.get("final_cta")), self.sources(s.get("sources"))]
        if posture == "advertorial":          # reference scaffolding: sticky for the whole page after the hero
            out = head + [self.sticky_zone(s, body)]
        else:                                  # hybrid/editorial: sticky zone starts at the bridge
            k = 2
            out = head + body[:k] + ([self.sticky_zone(s, body[k:])] if posture != "editorial" else body[k:])
        out.append(self.footer(s))
        return "\n".join(x for x in out if x)


def liquid_template(brand, takeover=False):
    """templates/page.<suffix>.liquid — the theme has no default page template (gotcha #1)."""
    chrome = ""
    if takeover:
        hc = os.path.join(ROOT, "templates", "landing", "hide_theme_chrome.html")
        chrome = open(hc).read() if os.path.exists(hc) else ""
    return ("{%- comment -%} GenSeo landing page (listicle/advertorial). Generated by scripts/landing_render.py.\n"
            "  Renders page.content (inline-CSS body_html). The ONLY stylesheet: reset + one grid media query,\n"
            "  namespaced gsl- / [data-gsl-*] so it cannot collide with the dawn-derived theme. Bump the suffix\n"
            "  (-v2, -v3) on every change: Shopify caches compiled templates. {%- endcomment -%}\n"
            + GRID_CSS + "\n" + chrome + "\n{{ page.content }}\n")


def render(spec_path):
    raw = open(spec_path).read()
    bad = brand_rules.spec_violations(json.loads(raw))
    if bad:
        sys.exit("✗ brand guard: " + "; ".join(bad))
    if json.loads(raw).get("engine") == "ref":   # reference replicas (Kevin 2026-10-06) -> landing_clone.py
        import subprocess
        sys.exit(subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "landing_clone.py"), spec_path]).returncode)
    spec = json.load(open(spec_path))
    brand = load_brand(spec["store"])
    r = R(brand)
    body_inner = getattr(r, spec["template"])(spec)
    body = (f'<div class="gsl-landing gsl-{spec["template"]}" style="font-family:{brand["fonts"]["body"]};'
            f'color:{brand["colors"]["text"]};background:{brand["colors"]["bg"]};margin:0;line-height:1.6;">\n{body_inner}\n</div>')
    out_dir = os.path.join(os.path.dirname(os.path.abspath(spec_path)), spec["slug"])
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, "body.html"), "w").write(body)
    tdir = os.path.join(ROOT, "templates", "landing")
    for suffix, tk in (("genseo-landing-v1", False), ("genseo-landing-takeover-v1", True)):
        open(os.path.join(tdir, f"page.{suffix}.liquid"), "w").write(liquid_template(brand, tk))
    preview = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
               f'<title>{html.escape(spec["title"])} — PREVIEW (not published)</title>'
               f'<link rel="stylesheet" href="{brand["fonts"]["preview_font_link"]}">{GRID_CSS}</head>'
               f'<body style="margin:0;background:{brand["colors"]["bg"]};">'
               f'<div style="background:#111;color:#ffd84d;font:600 12px/1.4 monospace;padding:6px 12px;text-align:center;">'
               f'LOCAL PREVIEW · {html.escape(brand["name"])} · template={spec["template"]} · posture={spec.get("posture", "hybrid" if spec["template"]=="listicle" else "advertorial")} '
               f'· page template: {html.escape(spec.get("template_suffix", "genseo-landing-v1"))} · NOT PUBLISHED</div>'
               f'{body}</body></html>')
    open(os.path.join(out_dir, "preview.html"), "w").write(preview)
    n_ph = len(PH_RE.findall(json.dumps(spec)))
    print(f"✓ rendered {spec['template']} for {brand['name']}: {out_dir}/body.html + preview.html ({n_ph} placeholder(s))")
    return out_dir


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    render(sys.argv[1])

#!/usr/bin/env python3
"""Packaging palette for GenSeo landing pages (Kevin 2026-10-09: "the listicle's UI/UX colors must be congruent with
the product's packaging colors, for this page and every listicle later").

  /usr/bin/python3 scripts/landing_palette.py extract <image> [<image> ...]   # k-means pack colors (JSON)
  /usr/bin/python3 scripts/landing_palette.py show <spec>                       # pack colors + token map for a spec
  /usr/bin/python3 scripts/landing_palette.py check <spec> [--json]             # QA gate on the RENDERED body.html

How it works
  1. PACK COLORS: the committed source of truth is product_refs/<handle>.palette.json when that
     file exists (scripts/packaging_palette.py). k-means (OKLab, k=6) over product_refs/<handle>.png
     (+ any spec "pack_palette_images") is the cross-check and the fallback for a product with no file.
     When both <handle>.png and <handle>-cutout.png exist, the PNG is the measurement. The cutout is
     used only if that PNG is missing, and the two are not mixed. Near-white / near-black / transparent
     pixels are ignored. The "pack hue" is the heaviest chromatic cluster (OKLCh chroma >= 0.035). A pack
     with < 8 % chromatic pixels is "neutral": the page keeps the house palette unless the palette file
     says otherwise. A hard-window page fails when the photo hue disagrees with the file, or when the
     spec opts out of a chromatic file.
  2. TOKENS: every      house-brand color literal in the compiled page CSS (the shared gsl-ref-* theme template, Wellness
     Nest greens, hue 95..170 deg) and in the page body (inline SVG fills) is re-hued to the pack hue. Each new color
     keeps the ORIGINAL relative luminance (WCAG Y), so every text/CTA contrast ratio stays exactly what the
     template already passes; chroma is scaled toward the pack's chroma and clipped to the sRGB gamut.
     A pale surface (OKLab L > 0.88) is raised until its chroma clears TOKEN_CHROMA, so a low-chroma pack
     still passes the not-grey floor. The hue does not change.
  3. DELIVERY (no theme edit): landing_clone.py puts the remapped declarations in a <style id="gsl-pal"> at the top
     of the PAGE BODY and adds class gsl-pal to the wrapper. Selectors are re-emitted as .gsl-ref.gsl-pal ... (one
     class more specific than the template) for EVERY declaration of an affected property family, colored or not, so
     the per-property cascade is the template's own cascade, recolored. The shared template (and every other live
     page on it) is untouched; a page without a palette renders exactly as before.
  4. GATE (check): effective tokens = template defaults overridden by the body block. FAIL when the CTA (--gp-forest),
     accent (--gp-accent) or soft surface (--gp-sage) hue is more than HUE_TOL deg from the pack hue, when the accent is
     near-grey, or when a text/CTA pair is under WCAG AA 4.5:1. landing_real_qa.py runs the same hue test on the
     storefront's computed styles.
Spec keys: "palette": "auto" (default for specs created >= 2026-10-09) | "off" | {"hue": <deg>, "chroma": <0..0.3>}
(manual override, still gated); "pack_palette_images": [extra pack shots]; "product_ref": <handle> (else derived
from offer.href / sticky_cta.href /products/<handle>).
"""
import json, math, os, re, sys

import packaging_palette as packaging

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTO_FROM = "2026-10-09"          # specs created on/after this date get the pack palette by default and a hard gate
HOUSE_HUE = (95.0, 170.0)         # OKLCh hue band of the Wellness Nest greens the template ships with
HUE_TOL = 30.0                    # gate: max OKLCh hue distance page token -> pack hue
MIN_CHROMA = 0.035                # chromatic cluster / accent must be at least this colorful
TOKEN_CHROMA = 0.012              # forest, accent, and sage must clear this or the gate treats them as grey
FAMILIES = ("color", "background", "border", "outline", "fill", "stroke", "box-shadow", "text-shadow",
            "text-decoration", "caret-color", "accent-color", "column-rule", "--")


# ---------- color math (sRGB <-> OKLab, WCAG luminance) ----------
def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c):
    c = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return c * 255.0


def rgb_to_oklab(rgb):
    r, g, b = (_lin(x) for x in rgb)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def oklab_to_lin(lab):
    L, a, b = lab
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def lch(rgb):
    L, a, b = rgb_to_oklab(rgb)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def luminance(rgb):
    r, g, b = (_lin(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(c1, c2):
    a, b = sorted((luminance(c1), luminance(c2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def hue_dist(h1, h2):
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


def _from_lch(L, C, h):
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    return oklab_to_lin((L, a, b))


def _in_gamut(lin, eps=1e-4):
    return all(-eps <= x <= 1 + eps for x in lin)


def make_color(target_y, C, h):
    """Color with hue h, chroma <= C (gamut-clipped) and WCAG relative luminance == target_y."""
    def y_of(L, c):
        lin = _from_lch(L, c, h)
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2], lin
    for _ in range(40):
        lo, hi = 0.0, 1.0
        for _ in range(40):                     # bisection on OKLab L for the target luminance
            mid = (lo + hi) / 2
            y, lin = y_of(mid, C)
            lo, hi = (mid, hi) if y < target_y else (lo, mid)
        y, lin = y_of((lo + hi) / 2, C)
        if _in_gamut(lin):
            break
        C *= 0.92                               # out of sRGB: reduce chroma, keep hue + luminance
    return tuple(max(0, min(255, round(_gam(min(1.0, max(0.0, x)))))) for x in lin)


def hexc(rgb):
    return "#%02x%02x%02x" % tuple(rgb)


def parse_color(s):
    s = s.strip().lower()
    if s.startswith("#"):
        h = s[1:]
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h[:3])
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)), None
    n = re.findall(r"[\d.]+%?", s)
    rgb = tuple(int(float(x)) for x in n[:3])
    return rgb, (n[3] if len(n) > 3 else None)


# ---------- pack color extraction ----------
def _measure_size(width, height, size):
    """Thumbnail box with Pillow's aspect rounding. (160, 160) is the measure size."""
    x, y = math.floor(size[0]), math.floor(size[1])
    if x >= width and y >= height:
        return width, height
    aspect = width / height

    def round_aspect(number, key):
        return max(min(math.floor(number), math.ceil(number), key=key), 1)

    if x / y >= aspect:
        x = round_aspect(y * aspect, key=lambda n: abs(aspect - n / y))
    else:
        y = round_aspect(x / aspect, key=lambda n: 0 if n == 0 else abs(aspect - x / n))
    return x, y


def _thumbnail_for_measure(im, size=(160, 160)):
    """Downscale the way Pillow 12's BICUBIC thumbnail did.

    product_refs/*.palette.json was measured with that thumbnail. Pillow 13
    forwards reducing_gap into the RGBA resize and, when height shrinks more
    than twice the width, runs the vertical resample first. Either change moves
    the k-means clusters. Horizontal then vertical BICUBIC, with reducing_gap
    left off, matches those files on Pillow 12 and 13.
    """
    from PIL import Image

    tw, th = _measure_size(im.width, im.height, size)
    if (tw, th) == (im.width, im.height):
        return im
    # RGBa keeps the premultiplied pixels across both passes. Pillow's own
    # resize does that inside one call; splitting the passes on RGBA would
    # un-premultiply in between and shift the clusters.
    work = im.convert("RGBa")
    filt = Image.Resampling.BICUBIC if hasattr(Image, "Resampling") else Image.BICUBIC
    if tw != work.width:
        work = work.resize((tw, work.height), filt, reducing_gap=None)
    if th != work.height:
        work = work.resize((tw, th), filt, reducing_gap=None)
    return work.convert(im.mode)


def extract(paths, k=6, seed=7):
    import numpy as np
    from PIL import Image
    px = []
    for p in paths:
        im = _thumbnail_for_measure(Image.open(p).convert("RGBA"))
        a = np.asarray(im).reshape(-1, 4)
        px.append(a[a[:, 3] > 200][:, :3])
    px = np.concatenate(px).astype(float)
    lab = np.array([rgb_to_oklab(tuple(p)) for p in px])
    C = np.hypot(lab[:, 1], lab[:, 2])
    keep = ~(((lab[:, 0] > 0.93) & (C < 0.03)) | (lab[:, 0] < 0.12))     # white backgrounds/text, black ink
    lab, px = lab[keep], px[keep]
    if len(lab) < 50:
        return []
    rng = np.random.default_rng(seed)
    cent = lab[rng.choice(len(lab), k, replace=False)]
    for _ in range(30):
        lab_d = ((lab[:, None, :] - cent[None, :, :]) ** 2).sum(-1)
        lbl = lab_d.argmin(1)
        new = np.array([lab[lbl == i].mean(0) if (lbl == i).any() else cent[i] for i in range(k)])
        if np.allclose(new, cent, atol=1e-5):
            break
        cent = new
    out = []
    for i in range(k):
        m = lbl == i
        if not m.any():
            continue
        rgb = tuple(int(x) for x in px[m].mean(0).round())
        L, c, h = lch(rgb)
        out.append({"hex": hexc(rgb), "share": round(float(m.mean()), 4), "L": round(L, 3), "C": round(c, 3), "h": round(h, 1)})
    return sorted(out, key=lambda d: -d["share"])


def pack_hue(colors):
    chrom = [c for c in colors if c["C"] >= MIN_CHROMA]
    share = sum(c["share"] for c in chrom)
    if share < 0.08:
        return None
    top = max(chrom, key=lambda c: c["share"])
    return {"hue": top["h"], "chroma": top["C"], "hex": top["hex"], "chromatic_share": round(share, 3)}


def product_handle(spec):
    if spec.get("product_ref"):
        return spec["product_ref"]
    for blk in (spec.get("offer", {}), spec.get("sticky_cta", {}), spec.get("hero", {}).get("cta", {})):
        m = re.search(r"/products/([a-z0-9-]+)", blk.get("href", ""))
        if m:
            return m.group(1)
    return None


def pack_images(spec):
    """Pack photo for the cross-check.

    product_refs/<handle>.png is the measurement behind product_refs/<handle>.palette.json.
    A cutout is only the fallback when that PNG is missing. Mixing both would make k-means
    disagree with the committed file. Spec pack_palette_images are extra shots after that photo.
    """
    h = product_handle(spec)
    imgs = []
    if h:
        for suf in (".png", "-cutout.png"):
            p = os.path.join(ROOT, "product_refs", h + suf)
            if os.path.exists(p):
                imgs.append(p)
                break
    imgs += [p if os.path.isabs(p) else os.path.join(ROOT, p) for p in spec.get("pack_palette_images", [])]
    return h, [p for p in imgs if os.path.exists(p)]


def wants_palette(spec):
    v = spec.get("palette", "auto" if spec.get("created", "") >= AUTO_FROM else "off")
    return v != "off" and spec.get("engine") == "ref"


def resolve(spec):
    """-> {"hue","chroma","pack":[...],"handle",...} or None (house palette)."""
    if not wants_palette(spec):
        return None
    v = spec.get("palette")
    h, imgs = pack_images(spec)
    colors = extract(imgs) if imgs else []
    ph = pack_hue(colors) if colors else None
    sot = packaging.load(h) if h else None
    if sot and sot.get("kind") == "neutral":
        return None
    if sot and sot.get("kind") == "chromatic" and sot.get("hue") is not None:
        ph = {"hue": float(sot["hue"]), "chroma": float(sot.get("chroma") or (ph or {}).get("chroma") or 0.1),
              "hex": sot.get("hex") or "", "sot": True}
        tol = float(sot.get("hue_tolerance", HUE_TOL))
        if isinstance(v, dict) and "hue" in v and hue_dist(float(v["hue"]), ph["hue"]) <= tol:
            ph = {**ph, "hue": float(v["hue"]), "chroma": float(v.get("chroma", ph["chroma"])),
                  "hex": v.get("hex") or ph["hex"], "manual": True}
        return {**ph, "handle": h, "images": [os.path.relpath(p, ROOT) for p in imgs],
                "pack": colors or sot.get("clusters") or []}
    if isinstance(v, dict) and "hue" in v:
        ph = {"hue": float(v["hue"]), "chroma": float(v.get("chroma", ph["chroma"] if ph else 0.1)), "hex": v.get("hex", ""), "manual": True}
    if not ph:
        return None
    return {**ph, "handle": h, "images": [os.path.relpath(p, ROOT) for p in imgs], "pack": colors}


# ---------- remapping ----------
REF_CHROMA = lch((0x54, 0xb9, 0x4a))[1]     # house primary green


def remap_color(rgb, pal):
    L, C, h = lch(rgb)
    if C < 0.003 or not (HOUSE_HUE[0] <= h <= HOUSE_HUE[1]):
        return None
    pc = pal["chroma"]
    c2 = C * max(0.85, min(1.3, pc / REF_CHROMA))
    pale = L > 0.88
    if L < 0.5:                                  # deep tones stay rich (berry, not brown)
        c2 = max(c2, 0.8 * pc)
    elif pale:                                   # pale surfaces read as a tint of the pack, not grey
        fade = max(0.5, min(1.0, (1 - L) / 0.07))
        tint = min(0.035, 0.3 * pc) * fade
        # A low-chroma pack's 0.3*pc tint can land under TOKEN_CHROMA. The gate would then
        # fail a page that was painted from that pack's own file. Hold the floor.
        c2 = max(c2, tint, TOKEN_CHROMA)
    y = luminance(rgb)
    out = make_color(y, c2, pal["hue"])
    if pale:
        # sRGB rounding can drop a requested 0.012 under the gate. Step up until it clears.
        for _ in range(8):
            if lch(out)[1] >= TOKEN_CHROMA or c2 >= 0.035:
                break
            c2 = min(0.035, c2 + 0.004)
            out = make_color(y, c2, pal["hue"])
    return out


def darken_to(rgb, bgs, ratio=4.6):
    """Same hue/chroma, lower luminance until contrast >= ratio against every bg (WCAG AA text)."""
    L, C, h = lch(rgb)
    y = luminance(rgb)
    out = rgb
    while any(contrast(out, b) < ratio for b in bgs) and y > 0.01:
        y *= 0.95
        out = make_color(y, C, h)
    return out


COLOR_RE = re.compile(r"#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{4}\b|#[0-9a-fA-F]{3}\b|rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(?:,\s*[\d.]+\s*)?\)")


def remap_text(s, pal, cache=None):
    cache = {} if cache is None else cache

    def sub(m):
        lit = m.group(0)
        if lit not in cache:
            rgb, alpha = parse_color(lit)
            new = remap_color(rgb, pal)
            if new is not None and hexc(rgb) in pal.get("aa_text", ()):
                new = darken_to(new, [(255, 255, 255)] + [remap_color(parse_color(b)[0], pal) or parse_color(b)[0] for b in pal.get("aa_bg", ())])
            if new is None:
                cache[lit] = lit
            elif alpha is None:
                h = lit[1:]
                cache[lit] = hexc(new) + (h[6:] if len(h) == 8 else h[3] * 2 if len(h) == 4 else "")   # keep #rrggbbaa / #rgba alpha
            else:
                cache[lit] = "rgba(%d,%d,%d,%s)" % (*new, alpha)
        return cache[lit]
    return COLOR_RE.sub(sub, s)


def _split(s, sep):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == sep and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return out


def parse_rules(css):
    """Flat list of (media_prelude or None, selector, body) for a minified/regular stylesheet (one @media level)."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rules, i, n = [], 0, len(css)

    def block(start):
        depth, j = 0, start
        while j < n:
            if css[j] == "{":
                depth += 1
            elif css[j] == "}":
                depth -= 1
                if depth == 0:
                    return j
            j += 1
        return n
    while i < n:
        j = css.find("{", i)
        if j < 0:
            break
        pre = css[i:j].strip()
        end = block(j)
        inner = css[j + 1:end]
        if pre.startswith("@media") or pre.startswith("@supports"):
            for _, sel, body in parse_rules(inner):
                rules.append((pre, sel, body))
        elif not pre.startswith("@"):
            rules.append((None, pre, inner))
        i = end + 1
    return rules


def _family(prop):
    p = prop.strip().lower()
    return next((f for f in FAMILIES if p == f or p.startswith(f + "-") or (f == "--" and p.startswith("--"))), None)


def build_override(css, pal):
    """Recolored copy of every declaration of an affected property family, one class more specific (.gsl-pal)."""
    rules = parse_rules(css)
    hit = set()
    for _, _, body in rules:
        for d in _split(body, ";"):
            if ":" in d and remap_text(d, pal) != d:
                prop = d.split(":", 1)[0].strip().lower()
                hit.add(prop if prop.startswith("--") else _family(prop))
    cache, out = {}, []
    for media, sel, body in rules:
        sels = [s.strip() for s in _split(sel, ",") if s.strip().startswith(".gsl-ref")]
        if not sels:
            continue
        decls = []
        for d in _split(body, ";"):
            if ":" not in d:
                continue
            prop = d.split(":", 1)[0].strip().lower()
            if (prop in hit) if prop.startswith("--") else (_family(prop) in hit):
                decls.append(remap_text(d.strip(), pal, cache))
        if decls:
            s2 = ",".join(re.sub(r"^\.gsl-ref(?![\w-])", ".gsl-ref.gsl-pal", s) for s in sels)
            r = s2 + "{" + ";".join(decls) + "}"
            out.append(("@media" in (media or "") or "@supports" in (media or "")) and f"{media}{{{r}}}" or r)
    return "".join(out)


def apply_to_body(body, css, pal, extra_css=""):
    """Body with the palette <style> block + gsl-pal wrapper class + recolored inline literals."""
    tok, _ = effective_tokens(css, "")
    pal = dict(pal, aa_text={hexc(parse_color(tok[k])[0]) for k in ("--gp-accent", "--gp-ink", "--gp-text", "--gp-muted") if k in tok},
               aa_bg=[tok[k] for k in ("--gp-sage", "--gp-sage-2", "--gp-bone") if k in tok])
    style = f'<style id="gsl-pal">/* GenSeo pack palette: hue {pal["hue"]:.0f} from {pal.get("handle")} (scripts/landing_palette.py) */{build_override(css, pal)}{extra_css}</style>\n'
    body = remap_text(body, pal)
    body = re.sub(r'<div class="gsl-ref gsl-ref--(\w+)">', lambda m: style + f'<div class="gsl-ref gsl-pal gsl-ref--{m.group(1)}">', body, count=1)
    return body


# ---------- gate ----------
TOKENS = ("--gp-forest", "--gp-accent", "--gp-ink", "--gp-text", "--gp-muted", "--gp-sage", "--gp-sage-2", "--gp-bone", "--gp-line")


def effective_tokens(page_css, body):
    tok = {}
    for m in re.finditer(r"\.gsl-ref\{([^}]*--gp-forest[^}]*)\}", page_css):
        for d in m.group(1).split(";"):
            if d.strip().startswith("--gp-") and ":" in d:
                k, v = d.split(":", 1)
                tok[k.strip()] = v.strip()
    blk = re.search(r'<style id="gsl-pal">(.*?)</style>', body, re.S)
    if blk:
        for m in re.finditer(r"\.gsl-ref\.gsl-pal\{([^}]*)\}", blk.group(1)):
            for d in m.group(1).split(";"):
                if d.strip().startswith("--gp-") and ":" in d:
                    k, v = d.split(":", 1)
                    tok[k.strip()] = v.strip()
    return {k: v for k, v in tok.items() if k in TOKENS}, bool(blk)


def judge(tokens, pal, has_block=True):
    """List of (name, ok, detail)."""
    res = []
    rgb = {k: parse_color(v)[0] for k, v in tokens.items() if COLOR_RE.fullmatch(v.strip())}
    for k in ("--gp-forest", "--gp-accent", "--gp-sage"):
        if k not in rgb:
            res.append((f"hue{k}", False, "token missing"))
            continue
        L, C, h = lch(rgb[k])
        d = hue_dist(h, pal["hue"])
        ok = d <= HUE_TOL and (C >= TOKEN_CHROMA)
        res.append((f"hue{k}", ok, f"{hexc(rgb[k])} hue {h:.0f} vs pack {pal['hue']:.0f} (d={d:.0f}, tol {HUE_TOL:.0f}) C={C:.3f}"))
    if "--gp-accent" in rgb:
        C = lch(rgb["--gp-accent"])[1]
        res.append(("accent_chroma", C >= MIN_CHROMA, f"accent chroma {C:.3f} (min {MIN_CHROMA})"))
    W = (255, 255, 255)
    pairs = [("--gp-ink", W), ("--gp-text", W), ("--gp-muted", W), ("--gp-accent", W), ("--gp-ink", "--gp-sage"),
             ("--gp-text", "--gp-sage"), ("--gp-muted", "--gp-sage"), ("--gp-accent", "--gp-sage"), (W, "--gp-forest")]
    for fg, bg in pairs:
        a = W if fg == W else rgb.get(fg)
        b = W if bg == W else rgb.get(bg)
        if a is None or b is None:
            continue
        cr = contrast(a, b)
        name = f"{'#fff' if fg == W else fg} on {'#fff' if bg == W else bg}"
        res.append((f"aa {name}", cr >= 4.5, f"{cr:.2f}:1"))
    res.append(("palette_block_in_body", has_block, "body carries <style id=gsl-pal>" if has_block else "no gsl-pal block: page renders the house greens"))
    return res


def judge_neutral(tokens, sot, has_block):
    """Neutral pack: near-grey tokens pass. House greens pass only when the file allows them."""
    res = []
    rgb = {k: parse_color(v)[0] for k, v in tokens.items() if COLOR_RE.fullmatch(v.strip())}
    allow_house = bool(sot.get("house_palette_allowed"))
    note = sot.get("packaging_note") or "neutral pack"
    for k in ("--gp-forest", "--gp-accent", "--gp-sage"):
        if k not in rgb:
            res.append((f"hue{k}", False, "token missing"))
            continue
        _L, C, h = lch(rgb[k])
        if C < MIN_CHROMA:
            res.append((f"hue{k}", True, f"{hexc(rgb[k])} neutral C={C:.3f} ({note})"))
        elif allow_house and HOUSE_HUE[0] <= h <= HOUSE_HUE[1]:
            res.append((f"hue{k}", True, f"{hexc(rgb[k])} house-green fallback hue {h:.0f} (not read off the bottle)"))
        else:
            res.append((f"hue{k}", False, f"{hexc(rgb[k])} hue {h:.0f} conflicts with neutral pack ({note})"))
    # The untouched house template is the allowed fallback. Its accent contrast is the template's own.
    # AA applies once a palette block repaints the page.
    if has_block:
        W = (255, 255, 255)
        pairs = [("--gp-ink", W), ("--gp-text", W), ("--gp-muted", W), ("--gp-accent", W), ("--gp-ink", "--gp-sage"),
                 ("--gp-text", "--gp-sage"), ("--gp-muted", "--gp-sage"), ("--gp-accent", "--gp-sage"), (W, "--gp-forest")]
        for fg, bg in pairs:
            a = W if fg == W else rgb.get(fg)
            b = W if bg == W else rgb.get(bg)
            if a is None or b is None:
                continue
            cr = contrast(a, b)
            name = f"{'#fff' if fg == W else fg} on {'#fff' if bg == W else bg}"
            res.append((f"aa {name}", cr >= 4.5, f"{cr:.2f}:1"))
        if not allow_house:
            res.append(("palette_block_in_body", False, "neutral pack was recolored"))
    return res


def _file_rows(spec, extracted):
    rows = []
    for item in packaging.spec_violations(spec) + packaging.image_violations(spec, extracted):
        rows.append(("sot", False, item))
    return rows


def _emit(rep, rows, as_json, headline=None):
    bad = [r for r in rows if not r[1]]
    hard = rep["hard"]
    rep["checks"] = [{"check": n, "ok": ok, "detail": d} for n, ok, d in rows]
    rep["result"] = "PASS" if not bad else ("FAIL" if hard else "WARN")
    if as_json:
        print(json.dumps(rep, indent=1))
    else:
        if headline:
            print(headline)
        for n, ok, d in rows:
            print(f"{'✓' if ok else '✗'} {n}  {d}")
        print(f"palette gate: {rep['result']}")
    return 1 if rep["result"] == "FAIL" else 0


def check(spec_path, as_json=False):
    spec = json.load(open(spec_path))
    out_dir = os.path.join(os.path.dirname(os.path.abspath(spec_path)), spec["slug"])
    hard = spec.get("created", "") >= AUTO_FROM and spec.get("palette") != "off"
    h, imgs = pack_images(spec)
    colors = extract(imgs) if imgs else []
    extracted = pack_hue(colors) if colors else None
    sot = packaging.load(h) if h else None
    if sot and sot.get("kind") == "chromatic" and spec.get("created", "") >= AUTO_FROM:
        hard = True
    ph = extracted
    if sot and sot.get("kind") == "chromatic" and sot.get("hue") is not None:
        ph = {"hue": float(sot["hue"]), "chroma": float(sot.get("chroma") or (extracted or {}).get("chroma") or 0.1),
              "hex": sot.get("hex") or "", "chromatic_share": (extracted or {}).get("chromatic_share", 1), "sot": True}
    rep = {"spec": spec_path, "handle": h, "pack_images": [os.path.relpath(p, ROOT) for p in imgs],
           "pack": colors, "pack_hue": ph, "hard": hard, "palette_file": (sot or {}).get("_path")}
    file_rows = _file_rows(spec, extracted)
    if sot and sot.get("kind") == "neutral":
        body = open(os.path.join(out_dir, "body.html")).read()
        css = open(os.path.join(out_dir, "page.css")).read()
        tok, blk = effective_tokens(css, body)
        rows = judge_neutral(tok, sot, blk) + file_rows
        rep["tokens"] = tok
        return _emit(rep, rows, as_json, f"pack {h}: neutral file ({sot.get('packaging_note')})")
    if not ph:
        if file_rows and hard:
            rep["why"] = file_rows[0][2]
            return _emit(rep, file_rows, as_json, f"palette: FAIL ({rep['why']})" if hard else None)
        rep["result"] = "SKIP"
        rep["why"] = "no pack ref image" if not imgs else "neutral pack (house palette allowed)"
        print(json.dumps(rep, indent=1) if as_json else f"palette: SKIP ({rep['why']})")
        return 0
    body = open(os.path.join(out_dir, "body.html")).read()
    css = open(os.path.join(out_dir, "page.css")).read()
    tok, blk = effective_tokens(css, body)
    rows = judge(tok, ph, blk) + file_rows
    rep["tokens"] = tok
    share = ph.get("chromatic_share")
    share_s = f"{share:.0%}" if isinstance(share, (int, float)) else "n/a"
    source = "palette file" if ph.get("sot") else "pack photo"
    headline = (f"pack {h}: hue {ph['hue']:.0f} ({ph['hex']}, {source}, chromatic {share_s}) · colors "
                + " ".join(f"{c['hex']}:{c['share']:.0%}" for c in colors))
    return _emit(rep, rows, as_json, headline)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "extract":
        cols = extract(sys.argv[2:])
        print(json.dumps({"colors": cols, "pack_hue": pack_hue(cols)}, indent=1))
    elif cmd == "show":
        spec = json.load(open(sys.argv[2]))
        pal = resolve(spec)
        print(json.dumps(pal, indent=1))
    elif cmd == "check":
        sys.exit(check(sys.argv[2], "--json" in sys.argv))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

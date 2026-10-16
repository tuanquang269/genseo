#!/usr/bin/env python3
"""Gate for GenSeo landing pages (listicle / advertorial). Exit 0 = may render/draft.

  /usr/bin/python3 scripts/validate_landing.py landing_drafts/<slug>.json [--strict]

--strict (required by landing_publisher.py --live): zero placeholders allowed.
Checks: schema, ageaura_rules.spec_target_violations (AgeAura product handle allowlist:
ageaura-pure-nmn-tmg-nad-complex only; ageaura-pure-urolithin-a and any other Urolithin A
AgeAura handle fail closed), brand_rules.spec_violations (AgeAura = the NMN + TMG SKU only; FloraFresh formula = its
Supplement Facts label, never the PDP description; Shilajit Shockwave doses = its pack-label whitelist,
which has no milligram token — scripts/shockwave_rules.py; Pure Shilajit Gold Resin doses = its
pack-label whitelist, which has the OCR serving line and 75% Fulvic and no milligram token —
scripts/gold_resin_rules.py; ShilaSource Himalayan Shilajit Resin doses = its pack-label whitelist,
front-of-pack lines only, no milligram token — scripts/shilasource_resin_rules.py; Turkesterone
Advanced Formula doses = its pack-label whitelist, front-of-pack lines only, split capsule badge,
no milligram token — scripts/turkesterone_rules.py; listicle/advertorial
UI colors vs product_refs/<handle>.palette.json — scripts/packaging_palette.py, hard for specs created
>= 2026-10-09), forbidden terms per store (AgeAura: urolithin/peptide), banned filler, every
number in copy carries a source link or a placeholder, testimonials/expert quotes are either
placeholders or carry a "source", byline is on roster.json, all wellnessnest.co links 200,
images exist (local) or are https and < 80 KB as served with Accept: image/webp, no dosage-with-units
outside the product/offer card, no product named in the numbered findings for posture hybrid/editorial
(vault skill claude-design-dtc-listicle-advertorial + PATI-ADAPTATION.md), taste rules from the
2026-10-08 benchmark (no em/en dashes, paragraphs <= 40 words, H1 <= 55 chars, CTA <= 3 words; errors when
"daily": true), claims log landing_drafts/<slug>.claims.md exists (versioned next to the spec).
Premium pack_images (or a spec that claims a label-gate pass) fail closed when the label JSON is
missing, OCR fails, or the host has no macOS Vision. That is not a skip. See docs/LABEL_OCR_GATE.md.
"""
import json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import ageaura_rules as ar  # noqa: E402
import brand_rules as br  # noqa: E402
import landing_label_gate as llg  # noqa: E402
from landing_render import load_brand, PH_RE  # noqa: E402

BANNED = ["when it comes to", "furthermore,", "navigating the", "elevate your", "game-changer", "game changer",
          "state-of-the-art", "cutting-edge", "transform your", "the cornerstone of", "at its core",
          "in the realm of", "let's dive in", "let's dive into", "ultimately,", "in summary,", "delve into",
          "by leveraging", "miracle", "cure", "guaranteed results", "doctor recommended"]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
REQ = {"listicle": ["title", "items", "offer", "product"], "advertorial": ["title", "hero", "items", "product", "faq"]}
# engine "ref" (scripts/landing_clone.py, reference replicas) adds: testimonials/expert need a "source"; review
# stars/TrustScore must be copied from the source as displayed (no rounding) — the claims log records them.


def strings(o, path=""):
    if isinstance(o, str):
        yield path, o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from strings(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from strings(v, f"{path}[{i}]")


def ageaura_target_errors(spec):
    """Denied AgeAura product handles this landing spec targets. No network."""
    return ar.spec_target_violations(spec)


def http_ok(u):
    for _ in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=20)
            return r.status
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                continue
            return e.code
        except Exception:
            continue
    return 0


def premium_pack_list_message(spec, root=None):
    """Return the pack_images reminder, or None.

    A premium page lists generated pack shots only when a cutout exists, because
    that is the whitelist-shot path. A label file without a cutout (Turkesterone,
    and the same no-cutout case in docs/LABEL_OCR_GATE.md) uses the real PDP photo
    and must not claim a label-gate pass, so an empty pack_images list is correct.
    """
    root = ROOT if root is None else root
    if spec.get("style") != "premium":
        return None
    found = re.search(r"/products/([a-z0-9-]+)", json.dumps(spec))
    if not found:
        return None
    handle = found.group(1)
    label = os.path.join(root, "product_refs", handle + ".label.json")
    cutout = os.path.join(root, "product_refs", handle + "-cutout.png")
    packs = spec.get("pack_images") or []
    claimed = llg.claims_label_whitelist(spec)
    if os.path.isfile(label) and os.path.isfile(cutout) and not packs and not claimed:
        return "product has a label json: list every generated pack shot in pack_images so the label gate runs"
    return None


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    strict = "--strict" in sys.argv
    if len(a) != 1:
        sys.exit(__doc__)
    spec = json.load(open(a[0]))
    brand = load_brand(spec.get("store", ""))
    errs, warns = [], []
    t = spec.get("template")
    if t not in REQ:
        errs.append(f"template must be one of {list(REQ)}")
    for k in REQ.get(t, []):
        if not spec.get(k):
            errs.append(f"missing required field: {k}")
    if not re.fullmatch(r"[a-z0-9-]{3,80}", spec.get("slug", "")):
        errs.append("slug must be a lowercase handle")
    blob = json.dumps(spec)
    # Kevin 2026-10-09, any store's page: Urolithin and any non-NMN+TMG AgeAura SKU; FloraFresh claims off its label.
    brand_errs = []
    for v in ageaura_target_errors(spec) + br.spec_violations(spec):
        if v not in brand_errs:
            brand_errs.append(v)
    for v in brand_errs:
        errs.append("brand guard: " + v)
    blob = blob.lower()
    if brand.get("allowed_products"):
        for h in sorted(set(re.findall(r"wellnessnest\.co/products/([a-z0-9-]+)", blob))):
            if h not in brand["allowed_products"]:
                errs.append(f"product link /products/{h} is not in {brand['name']} allowed_products {brand['allowed_products']}")
        if "/collections/" in blob:
            errs.append(f"{brand['name']}: collection links are not allowed (single-product scope)")
    for term in brand.get("forbidden_terms", []):
        if term in blob:
            errs.append(f"forbidden term for {brand['name']}: '{term}'")
    for path, s in strings(spec):
        low = s.lower()
        for b in BANNED:
            if re.search(r"(?<![a-z])" + re.escape(b) + r"(?![a-z])", low) and not path.endswith(("url", "href", "image", "disclaimer")):
                errs.append(f"banned phrase '{b}' in {path}")
    # numbers need a source link (or a placeholder) in the same block
    blocks = [("items[%d]" % i, it) for i, it in enumerate(spec.get("items", []))]
    for name in ("hero", "offer", "product", "expert"):
        if spec.get(name):
            blocks.append((name, spec[name]))
    for name, blk in blocks:
        txt = json.dumps({k: v for k, v in blk.items() if k not in ("image", "alt", "cta", "options", "price", "chart")})
        nums = re.findall(r"(?<![#\w/.-])\d[\d,.]*\s?(?:%|mg|g\b|kg|days?|weeks?|people|customers|servings|participants)", txt)
        if nums and "href" not in txt and not PH_RE.search(txt) and not blk.get("source"):
            errs.append(f"{name}: numbers {nums[:3]} with no source link / placeholder / source field")
        if blk.get("chart") and not blk["chart"].get("source"):
            errs.append(f"{name}.chart has no source")
    for i, ts in enumerate(spec.get("testimonials", [])):
        if not PH_RE.search(json.dumps(ts)) and not ts.get("source"):
            errs.append(f"testimonials[{i}] is not a placeholder and has no source (no invented testimonials)")
    ex = spec.get("expert")
    if ex and not PH_RE.search(ex.get("quote", "")) and not ex.get("source"):
        errs.append("expert.quote must be a placeholder or carry a source")
    pr = spec.get("product") or {}
    if pr.get("rating_line") and not PH_RE.search(pr["rating_line"]) and not pr.get("rating_source"):
        errs.append("product.rating_line must be a placeholder or carry rating_source")
    roster = json.load(open(os.path.join(ROOT, "roster.json")))
    names = {v["name"] for k, v in roster.items() if isinstance(v, dict) and "name" in v}
    by = (spec.get("byline") or {}).get("name")
    if by and by not in names:
        errs.append(f"byline '{by}' is not on roster.json")
    for path, s in strings(spec):
        if path.endswith("image") and s:
            if s.startswith("http"):
                if not s.startswith("https://"):
                    errs.append(f"{path}: non-https image")
            elif not os.path.exists(os.path.join(ROOT, s)):
                errs.append(f"{path}: image file missing {s}")
            elif not (s.startswith("tmp_images/") or "/tmp_images/" in s):
                warns.append(f"{path}: local image not from article_images.py (QC unknown)")
    links = set(re.findall(r'https://wellnessnest\.co/[^"\s<)\\]+', json.dumps(spec)))
    for u in sorted(links):
        if "/cdn/" in u:
            continue
        code = http_ok(u)
        if code in (301, 302, 303) and re.search(r"wellnessnest\.co/(account|cart)(/|$)", u):
            continue   # account/cart legitimately redirect to login/checkout
        if code != 200:
            errs.append(f"link {u} -> HTTP {code}")
    claims = os.path.splitext(os.path.abspath(a[0]))[0] + ".claims.md"
    if not os.path.exists(claims):
        errs.append(f"claims log missing: {claims}")
    # PATI-ADAPTATION #6: narrative/body copy carries no dosage-with-units; only the product/offer card mirrors the PDP
    DOSE = re.compile(r"\d[\d,.]*\s?(?:mg|mcg|µg|g|grams?|iu)\b(?:\s?/\s?(?:day|d|kg))?", re.I)
    for path, s_ in strings({k: v for k, v in spec.items() if k not in ("product", "offer", "sticky_cta", "meta_description")}):
        if path.endswith(("image", "url", "href", "source")):
            continue
        hit = DOSE.search(re.sub(r"<a [^>]*>", "", s_))
        if hit:
            errs.append(f"dosage-with-units in body copy {path}: '{hit.group(0)}' (product/offer card only)")
    # funnel order: hybrid/editorial = no product in the numbered findings (product first appears at the bridge)
    posture = spec.get("posture", "hybrid" if t == "listicle" else "advertorial")
    if posture in ("hybrid", "editorial"):
        pname = (spec.get("product") or {}).get("name", "").split()[0].lower() if spec.get("product") else ""
        for i, it in enumerate(spec.get("items", [])):
            blob_i = json.dumps({k: v for k, v in it.items() if k not in ("image", "alt")}).lower()
            if (pname and pname in blob_i) or "/products/" in blob_i:
                errs.append(f"items[{i}] names/links the product before the bridge (posture {posture})")
        if spec.get("sticky_cta") and not spec.get("bridge"):
            errs.append("sticky_cta without a bridge: the sticky bar may only appear after the bridge")
    # PATI-ADAPTATION #8: every image < 80 KB, measured from the CDN with Accept: image/webp
    for path, s_ in strings(spec):
        if path.endswith("image") and s_:
            if s_.startswith("https://"):
                try:
                    r = urllib.request.urlopen(urllib.request.Request(s_, headers={"User-Agent": UA, "Accept": "image/webp,image/*"}), timeout=20)
                    n = len(r.read())
                    if n > 80 * 1024:
                        errs.append(f"{path}: {n//1024} KB as served (webp) > 80 KB")
                except Exception as e:
                    errs.append(f"{path}: image fetch failed {e}")
            elif os.path.exists(os.path.join(ROOT, s_)) and os.path.getsize(os.path.join(ROOT, s_)) > 80 * 1024:
                errs.append(f"{path}: local image > 80 KB")
    # design-taste-frontend + DTC benchmark (2026-10-08, state/bench): scannable, mobile-first copy.
    # Errors for daily-lane specs ("daily": true), warnings for hand-built pages.
    taste = errs if spec.get("daily") else warns
    VIS = re.compile(r"(\.(url|href|image|evidence|source)$)|^\.(reference|handle|slug|template|template_suffix|engine|created|store|posture)$")
    for path, s_ in strings(spec):
        if (VIS.search(path) and not path.endswith(".chart.source")) or path.startswith(".product.source"):
            continue
        if re.search("[\u2014\u2013]", s_):
            taste.append(f"em/en dash in visible copy {path} (taste rule: use a comma, colon, period or 'to')")
    def words(h):
        return len(re.sub(r"<[^>]+>", " ", h).split())
    for name, blk in [("items[%d]" % i, it) for i, it in enumerate(spec.get("items", []))] + [("bridge", spec.get("bridge") or {})]:
        for j, para in enumerate(re.findall(r"<p>(.*?)</p>", blk.get("body", ""), re.S)):
            if words(para) > 40:
                taste.append(f"{name}.body p[{j}] has {words(para)} words (max 40; aim 15-30 for mobile scanning)")
        if len(re.sub(r"<[^>]+>", "", blk.get("body", ""))) > 520:
            taste.append(f"{name}.body is {len(re.sub(r'<[^>]+>', '', blk.get('body', '')))} chars (max 520 per row)")
        for st in (blk.get("chart") or {}).get("stats", []):
            if len(st.get("label", "")) > 24 or len(st.get("value", "")) > 8:
                taste.append(f"{name}.chart stat '{st.get('value')}/{st.get('label')}' too long (value <= 8, label <= 24 chars)")
    for i, it in enumerate(spec.get("items", [])):
        if len(it.get("title", "")) > 34:
            taste.append(f"items[{i}].title is {len(it['title'])} chars (max 34: 2 lines on mobile)")
    hero = spec.get("hero") or {}
    h1 = (hero.get("accent", "") + " " + hero.get("title", "")).strip()
    if len(h1) > 48:
        taste.append(f"H1 is {len(h1)} chars (max 48 so it fits 2 lines desktop / 3 lines mobile)")
    if words(hero.get("summary_html", "")) > 32:
        taste.append(f"hero summary is {words(hero.get('summary_html', ''))} words (max 32)")
    cta = (spec.get("offer") or {}).get("cta", "")
    if len(cta.split()) > 3:
        taste.append(f"offer.cta '{cta}' is more than 3 words (taste: CTA must never wrap)")
    # Premium listicle layer (Kevin 2026-10-08 visual overhaul, templates/landing/ref/premium.css): structure + pack-label gate.
    if spec.get("style") == "premium":
        if spec.get("template_suffix") not in ("gsl-ref-listicle-v2", "gsl-ref-listicle-v3", "gsl-ref-listicle-v4"):   # v3/v4 = v2 + mobile-only layer
            errs.append("style premium needs template_suffix gsl-ref-listicle-v2/-v3/-v4 (the v1 theme file has no premium CSS)")
        if not hero.get("image"):
            taste.append("premium hero needs hero.image (product shot above the fold, Kevin 2026-10-08)")
        if (spec.get("offer") or {}).get("price") and not (spec.get("offer") or {}).get("price_source"):
            errs.append("offer.price needs offer.price_source (the PDP /products/<handle>.js selling plan; no invented anchors)")
        for i, r in enumerate((spec.get("expert") or {}).get("reviews", [])):
            if int(r.get("stars", 0)) < 4 or "trustpilot.com/reviews/" not in r.get("url", ""):
                errs.append(f"expert.reviews[{i}] must be a real 4-5 star Trustpilot review with its trustpilot.com/reviews/ URL")
        pack_msg = premium_pack_list_message(spec)
        if pack_msg:
            taste.append(pack_msg)
        claimed = llg.claims_label_whitelist(spec)
        # pack_images, or copy that claims a label-gate pass, fails closed when the
        # whitelist is missing or landing_label_gate.py does not exit 0. A missing
        # file is not a skip. Scene-only specs (no pack_images, no claim) are.
        if claimed:
            errs.extend(llg.whitelist_pack_errors(spec, ROOT))
    n_ph = len(PH_RE.findall(json.dumps(spec)))
    if strict and n_ph:
        errs.append(f"--strict: {n_ph} placeholder(s) remain — fill them with sourced facts or remove the block")
    for w in warns:
        print("⚠", w)
    for e in errs:
        print("✗", e)
    print(f"placeholders: {n_ph} · links checked: {len(links)}")
    if errs:
        print("✗ DO NOT RENDER/DRAFT"); sys.exit(1)
    print("✓ PASS"); sys.exit(0)


if __name__ == "__main__":
    main()

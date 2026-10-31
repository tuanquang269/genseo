# Article Templates — 4 dạng bài rotate (Kevin chốt "Full pack" 2026-08-09)

> Kevin's order (2026-08-08): "thử xem có làm thêm template bên blog này được không? Rotate các
> dạng bài khác nhau" — reference = the GemPages joint-pain article
> (`/blogs/news/news-copy-of-from-stiff-to-strong…`). That page's layout lives ENTIRELY in its
> `body_html` (gp-* classes inline) — no template suffix, no theme change. So we reproduce the
> *reading experience* with our own styled-HTML blocks inside `body_html`. GemPages app itself is
> NOT automatable; these blocks are.
>
> Mechanics: `shopify_publisher.py` converts the draft with `markdown.markdown(md, extensions=['extra'])`
> — raw block-level HTML passes through UNTOUCHED as long as (1) a blank line sits before and after
> the block, (2) prose stays in markdown OUTSIDE the blocks. Never put markdown syntax inside a block.
> `validate_article.py` counts markdown `##` headings / tables / `![...]()` images — so sections stay
> markdown `##`, the comparison table stays a markdown table, images stay markdown tags. Blocks are
> ACCENTS, not the skeleton. Hero rule (model + product, persona rotated) applies to ALL templates.

## Template registry + selection rule

| Key | Dạng | When (intent match on the ticket keyword) |
|-----|------|-------------------------------------------|
| `EDITORIAL` | Answer-first guide (default hiện tại) | how/what/why/dosage/"for women/men" informational |
| `STORY` | Story/PAS advertorial-organic (bài joint-pain style) | symptom/pain/journey keywords: "joint pain", "fatigue", "menopause", benefits-for-X with a lived problem |
| `LISTICLE` | Numbered cards | "best X", "top X", "X mistakes/side effects/reasons" |
| `COMPARISON` | VS + verdict | "X vs Y", "which should you", "alternative to" |

Selection: ticket `type:` field wins if present (e.g. `type: LISTICLE`). Otherwise match intent per
the table. When two templates both fit, prefer the one NOT used in the previous article (variety
guard — check the tracker `template:` note of the last row). Log `template:<KEY>` in the tracker
CSV row and state it in the run report.

## Shared block kit (inline CSS only, `gs-` prefix, WN green `#54b94a`, dark `#1e3a29`)

All blocks are body_html-safe: no `<style>` tag, no external classes, no scripts. Copy verbatim,
swap only text/href. Blank line REQUIRED before and after each block in the .md draft.

### 1. Section banner (STORY headline accent — use ABOVE a `##` heading, not instead of it)

```html
<div style="background:linear-gradient(90deg,#54b94a,#3a9e40);border-radius:10px;padding:14px 20px;margin:28px 0 4px;">
<p style="margin:0;color:#ffffff;font-weight:700;font-size:1.05em;letter-spacing:.02em;">PHẦN LABEL NGẮN (VD: THE HIDDEN CONNECTION)</p>
</div>
```

### 2. CTA button (→ /products/ hoặc /collections/; widget shop-this-article tự bắt link /products/, cap 12)

```html
<p style="text-align:center;margin:26px 0;">
<a href="https://wellnessnest.co/products/HANDLE" style="display:inline-block;background:#54b94a;color:#ffffff;font-weight:700;padding:14px 34px;border-radius:999px;text-decoration:none;">CTA TEXT — VD: See the full ingredient panel →</a>
</p>
```

### 3. Product card (STORY/LISTICLE cuối bài — ảnh = CDN url ĐÃ upload của chính bài này, không hotlink ngoài)

```html
<div style="border:2px solid #54b94a;border-radius:14px;padding:20px;margin:28px 0;text-align:center;background:#f6fbf5;">
<p style="margin:0 0 6px;font-weight:700;color:#1e3a29;font-size:1.15em;">PRODUCT NAME</p>
<p style="margin:0 0 14px;color:#444444;">One-line why-this-product tied to the article's mechanism.</p>
<a href="https://wellnessnest.co/products/HANDLE" style="display:inline-block;background:#1e3a29;color:#ffffff;font-weight:700;padding:12px 30px;border-radius:999px;text-decoration:none;">Shop PRODUCT →</a>
</div>
```

### 4. Icon checklist (STORY "recognize the signs" beat)

```html
<div style="background:#f6fbf5;border-left:4px solid #54b94a;border-radius:8px;padding:16px 20px;margin:20px 0;">
<p style="margin:0 0 8px;">✅ &nbsp;Sign or takeaway one</p>
<p style="margin:0 0 8px;">✅ &nbsp;Sign or takeaway two</p>
<p style="margin:0;">✅ &nbsp;Sign or takeaway three</p>
</div>
```

### 5. Numbered listicle card header (LISTICLE — one per item, item title stays a markdown `##` BELOW it)

```html
<div style="display:flex;align-items:center;gap:14px;margin:34px 0 2px;">
<div style="background:#54b94a;color:#ffffff;font-weight:800;font-size:1.3em;border-radius:50%;width:46px;height:46px;line-height:46px;text-align:center;flex:none;">1</div>
<div style="height:2px;background:#dbeedb;flex:1;"></div>
</div>
```

### 6. Verdict box (COMPARISON — after the markdown table)

```html
<div style="background:#1e3a29;border-radius:14px;padding:20px 24px;margin:26px 0;">
<p style="margin:0 0 6px;color:#8ee085;font-weight:700;letter-spacing:.04em;">OUR VERDICT</p>
<p style="margin:0;color:#ffffff;">Two-sentence verdict: who should pick which, stated plainly.</p>
</div>
```

## Per-template blueprint

**EDITORIAL** (unchanged default): answer-first intro → `##` sections → markdown table → FAQ.
Blocks allowed: 1 CTA button mid-article + optional checklist. Keep it clean.

**STORY** (bài joint-pain làm chuẩn): hero → answer-first intro (vẫn bắt buộc — AEO) → 3–5 story
beats, mỗi beat = section banner + `##` + prose (PAS: problem lived-in → agitate với mechanism
thật → solution) → icon checklist "signs" → supplement section với CTA button → product card cuối.
Giữ giọng educational authority-share, KHÔNG salesy ([[ad-tone-soft-authority-share]] vibe, organic lane).

**LISTICLE** (craft: [[advertorial-listicle-presell-framework]] bản organic): answer-first intro →
mỗi item = numbered card header + `##` item title → prose ngắn + ảnh nếu là product-item →
verdict box tóm "which one for whom" → product card. Số item 5–8; item 1 đặt mạnh nhất.

**COMPARISON**: answer-first verdict NGAY intro (người đọc vs-intent muốn đáp án) → `##` per
contender → markdown comparison table (validator cần) → verdict box → CTA button. Đối thủ
non-PATI: spec đọc từ PDP live của họ, không bịa ([[ads-article-mining]] rule).

### 7. First-hand experience (optional, all four templates)

Not a fifth template. One block, before `## Frequently Asked Questions`. Run `python3 scripts/first_hand_experience.py --product <handle>` and paste stdout only. Empty stdout means the registry lines for that product are still rights-gated: do not invent a quote and do not copy one from `templates/first-hand-quotes.json`. The helper prints a `<blockquote>` plus attribution, a paid-partnership disclosure, and `Results vary.` Shape and tokens: `templates/first-hand-experience-block.md`. Approval: `docs/FIRST_HAND_EXPERIENCE.md`.

## Guardrails

- Validator gates không đổi: word count theo intent, H2 markdown, ≥1 markdown table (COMPARISON/
  EDITORIAL bắt buộc; STORY/LISTICLE vẫn nên có 1 bảng nhỏ cho AEO), ≥3 inline images, citations.
- Images: hero rule + i5.2 inline UGC không đổi theo template.
- Mọi block phải render đứng một mình — không lồng block trong block, không markdown trong block.
- KHÔNG copy gp-* classes/GemPages markup — theme không có CSS cho chúng ngoài trang gốc.
- First-hand creator or customer lines come only from `python3 scripts/first_hand_experience.py`. This block is not a landing-page review card.
- Compliance/claims: organic educational lane — cơ chế thật, trích nguồn, no dosage-with-units
  trong body ([[ad-script-no-ingredient-dosage]] tinh thần áp cho blog claims về SP).

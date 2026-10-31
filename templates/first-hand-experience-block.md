# First-hand experience block

Blog articles only. The HTML is produced by `scripts/first_hand_experience.py`. Do not copy a quote into a draft by hand. If the command prints nothing, the article has no quote block.

Colors are the shared blog block kit (`#54b94a`, `#1e3a29`, `#f6fbf5`). This is not a landing-page review card.

```bash
python3 scripts/first_hand_experience.py --product <handle>
```

The command prints a block only when `rights_confirmed` is true, `approved_by` is set, and the claim lint passes. Shape:

```html
<section data-genseo-first-hand-block="PRODUCT_HANDLE" style="border-left:4px solid #54b94a;background:#f6fbf5;border-radius:8px;padding:16px 20px;margin:20px 0;">
<div data-genseo-first-hand="QUOTE_ID">
<blockquote style="margin:0;padding:0;border:0;">
<p style="margin:0;color:#1e3a29;font-size:1.05em;">QUOTE TEXT</p>
</blockquote>
<p data-genseo-first-hand-attribution="QUOTE_ID" style="margin:10px 0 0;color:#1e3a29;font-weight:700;">FIRST L., on PRODUCT LABEL</p>
<p data-genseo-first-hand-disclosure="QUOTE_ID" style="margin:4px 0 0;color:#444444;font-size:.92em;">Paid partnership (#ad)</p>
<p data-genseo-first-hand-note="QUOTE_ID" style="margin:4px 0 0;color:#444444;font-size:.92em;">Results vary.</p>
</div>
</section>
```

Leave a blank line before and after the block in the markdown draft. Place it before `## Frequently Asked Questions`. Registry, approval, and the claim lint: `docs/FIRST_HAND_EXPERIENCE.md`.

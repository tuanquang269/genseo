# GenSeo

Toàn bộ hướng dẫn vận hành nằm ở @AGENTS.md — đọc file đó trước khi chạy lệnh.

Tóm tắt 1 dòng: pipeline SEO tự động ghi lên store Shopify thật; không publish bài
nào chưa qua `python3 scripts/validate_article.py <draft>.md --draft` với `✓ PASS`.

## Scope gate waivers

When the prompt contains `SCOPE_WAIVER (Kevin, standing approval for unpublished draft listicles)`, the always-on file-count scope gate is off for that landing run. Do not show a menu. Do not wait. Do not ask "Proceed with the full unpublished draft package?" Write `landing_drafts/<slug>.json` and the unpublished draft. Do not publish live.

When the prompt contains `SCOPE_WAIVER (Kevin, standing approval for the daily blog article)`, the always-on file-count scope gate is off for that article run. Do not show a menu. Do not wait. Do not ask which file set to write. Do not ask "Proceed with the full live publish package?" Write the one ticket draft, images, claims log, tracker row, and ticket update. Publish that blog article live only after `validate_article.py` prints PASS, using `scripts/shopify_publisher.py`. Do not publish a landing-page listicle.

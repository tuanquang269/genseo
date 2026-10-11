# GenSeo

Toàn bộ hướng dẫn vận hành nằm ở @AGENTS.md — đọc file đó trước khi chạy lệnh.

Tóm tắt 1 dòng: pipeline SEO tự động ghi lên store Shopify thật; không publish bài
nào chưa qua `python3 scripts/validate_article.py <draft>.md --draft` với `✓ PASS`.

## Unpublished listicle drafts

When the prompt contains `SCOPE_WAIVER`, the always-on file-count scope gate is off. Do not show a menu because the page needs more than 2 files. Do not wait. Do not ask "Proceed with the full unpublished draft package?" Write `landing_drafts/<slug>.json` and the unpublished draft. Do not publish live.

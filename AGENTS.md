# AGENTS.md — sổ tay vận hành GenSeo (dành cho AI agent)

Bạn đang ở trong một pipeline SEO tự động ghi **trực tiếp lên store Shopify thật**.
Đọc hết file này trước khi chạy lệnh đầu tiên. Thứ tự đọc: file này →
`LOCALIZE.md` → `SETUP.md` → skill tương ứng với việc cần làm.

## ⛔ 6 luật cứng — vi phạm là phá site

1. **Không publish bài nào chưa `✓ PASS` gate.** Gate là
   `python3 scripts/validate_article.py <draft>.md --draft`. Exit 1 = không publish,
   không "hầu như đạt", không tự nới tiêu chuẩn. Sửa bài rồi chạy lại.
2. **Chỉ publish bằng `scripts/shopify_publisher.py`.** Không dùng Shopify MCP,
   GraphQL, hay REST tay — các đường đó không gắn JSON-LD, bài sẽ mất schema.
3. **Không bịa tác giả.** Chỉ dùng tên trong roster (`/Users/kevinkreative/genseo/roster.json` — nguồn duy nhất).
   Không gắn `Dr./MD/PhD/RD/CISSN` cho ai không có. Bịa tác giả có bằng y khoa trên
   nội dung sức khoẻ là lỗi nặng nhất pipeline này có thể tạo ra.
4. **Không link tới sản phẩm/collection không tồn tại.** Verify URL live trước khi
   chèn. Link 404 sẽ bị gate chặn — và nếu lọt thì làm hỏng trang.
5. **Refresh là APPEND-ONLY.** Bài đang có thứ hạng: giữ nguyên body và title đang
   rank, chỉ thêm phần còn thiếu. Đổi title của trang đang rank = reset tín hiệu.
6. **Ghi hàng loạt: `backup_before_changes.py` → `--dry-run` → đọc → mới `--apply`.**
   Chưa bao giờ 301 một URL còn trả 200: phải `published:false` trước, rồi mới redirect.

## Lần đầu tiên (chỉ làm 1 lần)

```bash
# ✅ SETUP + LOCALIZE đã hoàn tất 2026-08-07 (wellnessnest.co) — KHÔNG làm lại.
# Tự kiểm tra trước khi chạy ticket:
python3 scripts/validate_article.py --self-check-author   # exit 1 + "roster EMPTY" = Kevin chưa điền roster.json (blocker thật)
python3 scripts/fetch_all_articles.py                     # API + token ok? (GSC skip = bình thường)
grep -rn "{{[A-Z_]*}}\|1000000000" scripts/ skills/ knowledge_base/ docs/ \
  | grep -v _DONOR_BRANDS_REMOVED                          # phải ra 0 dòng
```

Lệnh 3 còn ra kết quả → có placeholder mới lọt vào — sửa file đó (KHÔNG chạy sed hàng loạt của SETUP.md cũ).

## Playbook theo việc

### A. Viết 1 bài mới từ ticket
Skill: `genseo-auto-publish` (đọc cả file, 10 STEP, đừng bỏ STEP nào).

```bash
# STEP 6 — gate (bắt buộc, trước khi publish)
python3 scripts/validate_article.py published_drafts/<ten-bai>.md --draft
# STEP 7 — publish
python3 scripts/shopify_publisher.py publish published_drafts/<ten-bai>.md <BLOG_ID>
# STEP 8 — verify (2 gate: bài live + schema)
python3 scripts/verify_published.py <ARTICLE_ID> <BLOG_ID>
python3 scripts/repair_schema.py <ARTICLE_ID>      # chỉ khi verify báo thiếu schema
```
STEP 0 (check trùng trên site thật) và STEP 0.5 (topic fitness) là **chống lãng phí** —
bỏ 2 bước đó là cách nhanh nhất tạo ra bài tự cạnh tranh với bài cũ.

### B. Làm mới 1 bài cũ đang tụt
Skill: `genseo-refresh`. Cần `ARTICLE_ID` + keyword.

```bash
python3 scripts/validate_article.py published_drafts/<draft>.md --draft
python3 scripts/shopify_publisher.py update published_drafts/<draft>.md <BLOG_ID> <ARTICLE_ID>
python3 scripts/repair_schema.py <ARTICLE_ID> && python3 scripts/verify_published.py <ARTICLE_ID> <BLOG_ID>
```
Chẩn đoán trước khi sửa: hạng ≥13 → cần **CLIMB** (thêm chiều sâu, GIỮ title).
Hạng tốt mà không ai click → cần **CTR** (được phép viết lại title/meta).

### C. SEO cho collection
Skill: `genseo-collection-optimizer`.
```bash
python3 scripts/inspect_collection_seo.py <handle>
python3 scripts/collection_seo.py <handle> ...      # hoặc push_collection.py
```

### D. Dọn dẹp hằng ngày (4 lệnh, chạy được không cần model thông minh)
```bash
python3 scripts/repair_schema.py --recent 24    # dựng lại schema/author bị hỏng trong 24h
python3 scripts/fix_untitled.py --apply         # cứu bài mất title, tự xử lý bài trùng
python3 scripts/find_dupes.py --apply           # gộp + 301 bài cannibalize (có log revert)
python3 scripts/verify_published.py <ID> <BLOG> # spot-check 1 bài mới nhất
```
Đây là lớp **tự chữa lỗi**. Nó tồn tại vì model rẻ hay bỏ bước; các script này xác
định và idempotent nên chạy lại nhiều lần vô hại. Nên đặt cron cuối ngày.

### E. Sinh ticket mới (khi hết việc)
```bash
python3 scripts/refill_tickets.py --count 8 --dry-run  # nạp lại daily-tickets.md từ topic bank + board (đã qua gate); bỏ --dry-run để ghi — docs/TICKET_REFILL.md
python3 scripts/build_catalog_tickets.py    # brand mình bán mà chưa có bài
python3 scripts/build_ctr_tickets.py        # bài rank tốt nhưng CTR kém
python3 scripts/refresh_targets.py          # bài cần refresh (attribution theo page)
python3 scripts/build_rich_tickets.py       # ticket giàu brief từ nhu cầu GSC
```
Ticket càng chốt sẵn (collection link, góc bài, bảng so sánh, tác giả) thì model càng
ít đoán. Xem `tickets.example.md` để biết format.

### F. Traffic tụt — chẩn đoán trước, đừng sửa bừa
```bash
python3 scripts/sg_report.py                # báo cáo tổng theo thị trường
python3 scripts/diagnose_decline.py         # tụt ở đâu: query / page / hạng
python3 scripts/diagnose_concentration.py   # traffic dồn vào ít trang?
python3 scripts/brand_article_overlap.py    # blog có ăn tranh query brand của product?
python3 scripts/topic_fitness.py            # trang nào không xứng tồn tại
python3 scripts/seo_drift.py                # có gì thay đổi ngoài ý muốn?
```
Nguyên tắc: **chứng minh nguyên nhân trước khi đổi bất cứ gì.** Bài học từ hệ thống
gốc: một đợt refresh 5 bài làm tụt hạng cả 5 vì đổi title của trang đang rank —
không ai kiểm chứng giả thuyết trước.

## Bản đồ

| Cần gì | Ở đâu |
|---|---|
| Quy trình viết bài | `skills/genseo-auto-publish/SKILL.md` (file quan trọng nhất) |
| Luật AEO/GEO + E-E-A-T | `knowledge_base/*.md` |
| Cổng chất lượng | `scripts/validate_article.py` |
| Publish/update + schema + ảnh CDN | `scripts/shopify_publisher.py` |
| Credentials | `scripts/genseo_config.py` → `~/.genseo/shopify_token.json` |
| Data GSC | `scripts/gsc_fetcher.py` |
| Bối cảnh vì sao có cái gate | `docs/WORKFLOW_UPGRADE.md` |

## Lỗi thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `missing config ~/.genseo/shopify_token.json` | `SETUP.md` bước 1 |
| 401/403 từ Shopify | token thiếu scope (`write_content`, `write_products`, `write_themes`, `read/write_files`) |
| 404 khi thao tác article | sai blog ID (blog thật duy nhất: `news`=104008483131) hoặc article ID không tồn tại |
| Gate FAIL ở phần author | `roster.json` rỗng/thiếu người đó, hoặc `/pages/<handle>` chưa live trên site |
| Bài live nhưng không có schema | publish sai đường (luật #2). Chữa: `repair_schema.py <ID>` |
| Bài tên "Generated Article" | model ghi metadata dạng HTML comment thay vì `# H1`. Chữa: `fix_untitled.py --apply`. **Đừng xoá** — đó là bài thật bị lỗi title |
| `FileNotFoundError` một file csv/md | thiếu data đầu vào; xem `LOCALIZE.md` mục 5 để sinh |

## Đừng làm

- Đừng sửa file trong `scripts/` để "cho gate pass". Gate là tài sản của hệ thống.
- Đừng patch theme khi chưa `backup_before_changes.py`.
- Đừng chạy hàng loạt refresh trước khi 1 lô nhỏ chứng minh hạng có hồi.
- Đừng tự viết `<script type="application/ld+json">` vào markdown — publisher tự sinh.
- Đừng đặt CDN URL vào draft; dùng đường dẫn ảnh local, publisher tự upload.

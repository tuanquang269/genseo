# LOCALIZE.md — đọc file này TRƯỚC KHI chạy bất cứ thứ gì

> **Dành cho AI agent:** đây là checklist bắt buộc (quy trình vận hành ở `AGENTS.md`). Hệ thống này được bóc ra từ một
> store thật, mọi thứ mang tính riêng của store đó đã bị thay bằng **placeholder**.
> Nhiệm vụ của bạn: thay hết placeholder theo store của người dùng, rồi báo lại
> danh sách đã thay. Đừng chạy publish khi còn placeholder — gate sẽ fail (đúng).

Tìm tất cả placeholder còn lại bất cứ lúc nào:

```bash
grep -rn "{{[A-Z_]*}}\|1000000000\|your-store\|yourdomain\|Author One\|REPLACE ME" . | grep -v LOCALIZE.md
```

---

## 1. Store + credentials (bắt buộc)

| Placeholder | Thay bằng | Ở đâu |
|---|---|---|
| `your-store.myshopify.com` | shop domain | `config.example.json` → `~/.genseo/shopify_token.json` |
| `shpat_YOUR_ADMIN_API_TOKEN` | Admin API token | cùng file trên |
| `100000000001` | blog ID chính | rải trong `scripts/` |
| `100000000002` | blog ID thứ hai (nếu có 2 blog) | `scripts/` |
| `100000000003` | blog ID thứ ba (nếu có) | `scripts/` |
| `100000000010` | theme ID (main theme) | các script `*_theme.py` |
| `100000000099` | article ID mẫu trong test/self-check | vài script |
| `yourdomain.com` | domain thật | `scripts/validate_article.py` và một số script khác |
| `YOUR_INDEXNOW_KEY` | key IndexNow | `scripts/shopify_publisher.py`, `setup_indexnow.py` |
| `YOUR_MERCHANT_ID` | Merchant Center ID | `scripts/mc_diagnostics.py` |

Chi tiết từng bước: `SETUP.md`.

## 2. Thị trường (market) — placeholder `{{...}}`

Hệ thống gốc nhắm **một thị trường duy nhất**, nên placeholder là:

| Placeholder | Nghĩa | Ví dụ |
|---|---|---|
| `{{MARKET}}` | tên nước/vùng, dùng trong H1, prose, FAQ | `Vietnam` |
| `{{market}}` | dạng chữ thường trong slug/handle | `vietnam` |
| `{{MARKET_ADJ}}` | dạng tính từ | `Vietnamese` |
| `{{MARKET_ABBR}}` | viết tắt, dùng trong docs/skill | `VN` |
| `{{CURRENCY}}` | mã tiền tệ hiển thị trong bài | `VND` |
| `{{COUNTRY_CODE}}` | mã country 3 ký tự của Google Search Console | `vnm` |
| `{{LOCALITY}}` | tên quận/khu vực để tạo tín hiệu local | `Cầu Giấy`, `Thủ Đức` |

`{{LOCALITY}}` xuất hiện nhiều lần và **cần nhiều giá trị khác nhau** — skill yêu cầu
≥2 địa danh khác nhau trong mỗi bài. Thay bằng danh sách địa danh của bạn, đừng lặp
lại một cái.

⚠️ `{{COUNTRY_CODE}}` là **quan trọng nhất** trong nhóm này: các script report/diagnose
lọc GSC theo country. Sai mã = số liệu sai (gộp cả traffic nước khác vào).

Ngoài ra hãy tự đổi cho phù hợp thị trường (không phải placeholder, phải đọc và sửa):

- **Link authority trích dẫn** trong `knowledge_base/` và `skills/`: bản gốc dùng cơ
  quan y tế của thị trường cũ (`hsa.gov.sg`) và vài blog địa phương. Đổi sang cơ quan
  tương ứng ở nước bạn; giữ nguyên các nguồn quốc tế (PubMed, Examine.com, NIH).
- **Ngôn ngữ bài viết**: skill hiện viết tiếng Anh. Muốn tiếng Việt thì sửa STEP viết
  trong `skills/genseo-auto-publish/SKILL.md` và các check chữ trong
  `scripts/validate_article.py` (nó đếm từ, dò cụm tiếng Anh).

## 3. Roster tác giả (bắt buộc — nếu không gate luôn FAIL)

`Author One` … `Author Seven` + handle `/pages/author-one` … là placeholder. Phải đồng
bộ **cả 3 chỗ**, nếu lệch nhau thì bài không publish được:

1. `skills/genseo-auto-publish/SKILL.md` — bảng roster (`REPLACE ME`) + bio cố định
2. `scripts/validate_article.py` — `ROSTER_PAGES` và `APPROVED_BIOS`
3. `scripts/shopify_publisher.py` — dict `ROSTER` (xuất hiện 2 lần: publish và update)

Và mỗi tác giả phải có trang `/pages/<handle>` **sống thật** trên site.

Nguyên tắc không được bỏ (lý do hệ thống gốc từng gặp sự cố YMYL nghiêm trọng):

- Chỉ dùng **người thật**. Không bịa tên tác giả.
- Không gắn `Dr.` / `MD` / `PhD` / `RD` / `CISSN` cho người không có bằng đó.
- Bio là **văn bản cố định**, copy nguyên văn; model không được tự thêm chi tiết về
  người thật (số năm kinh nghiệm, chứng chỉ, chuyên môn).
- `FAKE_AUTHORS` trong `validate_article.py` đang **rỗng**. Nếu bạn từng phải xoá một
  byline bịa, thêm tên đó vào đây để model không dựng lại nó.

## 4. Quy tắc thương mại (phải tự điền)

Trong `skills/genseo-auto-publish/SKILL.md` và `skills/genseo-refresh/SKILL.md`, mục
**PRIORITY BRANDS** đang trống. Điền:

- thứ tự brand bạn muốn đẩy trước trong bài so sánh / gợi ý sản phẩm;
- brand bạn **không** bán → cấm nhắc, cấm link (link 404 sẽ bị gate chặn).

## 5. Dữ liệu đầu vào (không có trong gói)

Gói này là **hệ thống**, không có data. Tự sinh:

```bash
python3 scripts/fetch_all_articles.py        # existing_articles.json
python3 scripts/build_catalog_tickets.py     # ticket từ catalog
python3 scripts/build_ctr_tickets.py         # ticket CTR từ GSC
python3 scripts/refresh_targets.py           # target refresh (page-level)
```

Script nào báo `FileNotFoundError` là đang thiếu 1 file data — đọc tên file trong lỗi
rồi tìm script `build_*`/`fetch_*` tương ứng để sinh ra.

## 6. Đã bị bỏ khỏi gói (nếu cần thì viết lại)

Các script batch dưới đây là loại "chạy một lần", thân script chỉ là danh sách
article ID / slug của store cũ nên đã bị xoá. Nếu cần chức năng tương đương, hãy viết
lại bằng các tool tổng quát còn trong gói:

| Đã bỏ | Nó làm gì | Dùng cái này thay thế |
|---|---|---|
| `patch_images.py`, `patch_article_images.py` | patch ảnh cho 1 lô bài cụ thể | `audit_article_images.py` để tìm bài thiếu ảnh, rồi `shopify_publisher.py update` |
| `link_push_batch.py`, `internal_link_push.py` | đẩy internal link từ bài mạnh sang bài cận top | `get_internal_links.py`, `add_internal_links.py`, `link_articles_to_collection.py` + logic trong `docs/internal_linking_strategy.md` |
| `merge_dup_titles.py`, `apply_redirects.py` | gộp cluster trùng + 301 | `find_dupes.py --apply` (tự phát hiện, unpublish rồi mới 301, có log revert) |
| `patch_seo.py`, `patch_aeo.py` | patch title/meta/AEO cho 1 lô bài | `update_title_meta.py`, `patch_collection_seo.py` |
| `triage_thin.py` | phân loại bài mỏng: giữ / mở rộng / redirect | `topic_fitness.py` + `redirect_thin_batch.py` |
| `fetch_product_images.py` | tải ảnh cho 1 danh sách product handle | viết lại 10 dòng: gọi `/admin/api/<ver>/products.json` rồi tải `image.src` |
| `audit_ctr_collections.py` | audit CTR cho vài collection cụ thể | `build_ctr_tickets.py`, `inspect_collection_seo.py` |

Thứ tự an toàn khi thao tác hàng loạt: `backup_before_changes.py` → chạy `--dry-run`
→ đọc kỹ → mới `--apply`.

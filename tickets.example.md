# Ticket queue — ví dụ

Đây là format input của pipeline. Agent được lệnh *"continue with the next ticket in
tickets.example.md"*, nó lấy ticket pending kế tiếp, chạy `genseo-auto-publish`, rồi
tick `[x]`.

Ticket càng "giàu" — chốt sẵn collection link, góc bài, chủ đề bảng so sánh, tác giả —
thì model rẻ càng ít phải đoán. Đây là lý do chất lượng ổn định.

## Quy tắc chung (đọc trước mỗi ticket)

1. Mọi internal link phải trỏ tới URL đang LIVE. Link 404 sẽ bị gate chặn.
2. Không tạo bài mới cho keyword đã có bài — bổ sung vào bài cũ (`genseo-refresh`).
3. Byline lấy từ roster trong `genseo-auto-publish`. Không tự bịa tên.
4. Publish bằng `scripts/shopify_publisher.py`, không dùng đường khác (nếu không sẽ mất schema).

---

## [ ] Ticket #1 — NEW ARTICLE

- **Primary keyword:** `best creatine for beginners <thị trường của bạn>`
- **Secondary:** creatine monohydrate dosage, creatine loading phase, creatine side effects
- **Search intent:** informational, người mua lần đầu
- **Collection links (≥2, verify live):** `/collections/creatine`, `/collections/protein-powder`
- **Hero product:** `/products/<handle-thật-đang-còn-hàng>`
- **Comparison table:** 4 sản phẩm creatine — giá/lần dùng, dạng, hàm lượng
- **Angle:** không tồn tại query "creatine nào tốt nhất", chỉ có "loading hay không" — trả lời trước ở answer block
- **Author:** Mike Moretti (/pages/mike-moretti) — Co-founder, Wellness Nest. TODO: no approved headshot and the author page is not confirmed live.
- **Dedup note:** chưa có bài nào nhắm keyword này (đã check ngày <date>)

## [ ] Ticket #2 — REFRESH EXISTING

- **Article ID:** `<id-lấy-từ-fetch_all_articles.py>`
- **URL:** `https://wellnessnest.co/blogs/news/<handle>`
- **Diagnosis:** CTR (đang top 5 nhưng gần như không có click) → sửa title/meta, **giữ nguyên body**
- **Queries cần chiếm:** liệt kê query GSC thật kèm impressions
- **Rule:** append-only. Trang đang rank thì KHÔNG đổi title trừ khi chẩn đoán là CTR.

# Chiến Lược Internal Linking Mới (Dựa theo bài viết)

## Tư Tưởng Cốt Lõi
1. **Link là khoản đầu tư:** Không đi link bừa bãi. Chỉ dồn "sức mạnh" (authority) từ trang mạnh sang trang cần đẩy.
2. **Nguồn link (Source):** Bắt buộc phải là bài viết đang có traffic và thứ hạng tốt (Top 1-3).
3. **Đích đến (Target):** Bài viết đang ở vị trí "cận top" (Top 5-10) để tạo cú hích lên Top 1-3.
4. **Vòng lặp tăng trưởng:** Sau khi bài đích (Target) lên top và có traffic, nó sẽ trở thành Nguồn link (Source) để đẩy bài khác.
5. **Topical Authority:** Liên kết các bài viết cùng chủ đề để Google hiểu website bao phủ toàn diện chủ đề đó.

## Cách Áp Dụng Cho GenSEO
Trong bối cảnh tool GenSEO đang chạy auto publish:

1. **Thay đổi cách chọn Internal Link trong `genseo-auto-publish` và `genseo-content-writer`:**
   - Hiện tại: GenSEO tự động lấy bài viết ngẫu nhiên hoặc bài liên quan.
   - Hướng mới:
     - **Bước 1:** Dựa vào file GSC Data (hoặc `PUBLISHED_ARTICLES_TRACKER.csv` nếu có tracking Performance) lọc ra danh sách bài viết "Mạnh" (Top 1-3, có traffic).
     - **Bước 2:** Lọc ra danh sách bài "Cận Top" (Top 5-10) cần đẩy.
     - **Bước 3:** Khi viết bài mới hoặc dùng tool Refresh, chèn link từ "Bài Mạnh" trỏ về "Bài Cận Top" hoặc "Bài Mới".
     - **Bước 4:** Update lại hệ thống link liên tục.

2. **Cập nhật Kỹ Năng / Tool (Đề xuất):**
   - Tạo một script / tool phân tích `PUBLISHED_ARTICLES_TRACKER.csv` hoặc GSC để tự động phân loại: `Power Pages` (Nguồn) và `Target Pages` (Đích).
   - Khi chạy `genseo-content-refresh`, tool sẽ tự động mở `Power Pages` và thêm link trỏ về `Target Pages`.


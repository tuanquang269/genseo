# Cài đặt

> ## ✅ LOCALIZATION COMPLETED 2026-08-07 — wellnessnest.co
> Mọi giá trị trong repo này ĐÃ là giá trị THẬT của store (blog `news`=104008483131,
> theme 183190880571, domain wellnessnest.co, US/$). File này giữ lại làm tài liệu
> lịch sử. **TUYỆT ĐỐI KHÔNG chạy lại các lệnh sed/replace bên dưới** — chạy lại sẽ
> phá giá trị thật. Roster tác giả = `/Users/kevinkreative/genseo/roster.json` (nguồn duy nhất).

> Làm xong file này rồi đọc **`LOCALIZE.md`** để thay hết placeholder
> (thị trường, roster tác giả, priority brands). Bỏ bước đó thì gate sẽ chặn publish.

## 0. Yêu cầu

- Python 3.9+ (thư viện chuẩn là đủ; `gsc_fetcher.py` tự `pip install` Google client)
- Một Shopify store + **Admin API access token** (custom app)
- Một AI agent chạy được skill markdown (Claude Code, Antigravity, ...)
- Không bắt buộc: Google Search Console API, image-gen cho ảnh bài viết

## 1. Shopify credentials

Shopify admin → Settings → Apps and sales channels → Develop apps → Create an app →
Configure Admin API scopes. Bản gốc dùng: `write_content`, `write_products`,
`write_themes`, `read_files` + `write_files`. Install app → copy Admin API access
token (`shpat_...`).

```bash
mkdir -p ~/.genseo
cp config.example.json ~/.genseo/shopify_token.json
chmod 600 ~/.genseo/shopify_token.json
# sửa file: điền "shop" và "access_token" thật
```

Mọi script đọc SHOP/TOKEN qua `scripts/genseo_config.py`, nên chỉ cần khai báo 1 lần.
Muốn đổi chỗ file config: `export GENSEO_CONFIG=/path/to/config.json`.

## 2. Blog ID

Blog ID trong code là placeholder. Lấy ID thật:

```bash
python3 -c "import sys; sys.path.insert(0,'scripts'); import urllib.request,json,genseo_config as c; \
print(json.load(urllib.request.urlopen(urllib.request.Request(f'https://{c.SHOP}/admin/api/{c.API}/blogs.json', \
headers={'X-Shopify-Access-Token': c.TOKEN})))['blogs'])"
```

Rồi thay placeholder (blog chính = `104008483131`, blog thứ hai = `104008483131`):

```bash
grep -rl 104008483131 scripts/ | xargs sed -i '' 's/104008483131/<BLOG_ID_THAT>/g'
```

## 2b. Domain và theme ID

Vài script kiểm tra internal link theo domain, và các script patch theme dùng theme ID:

```bash
grep -rl wellnessnest.co scripts/ | xargs sed -i '' 's/yourdomain\.com/<domain-cua-ban>/g'
grep -rn 183190880571 scripts/    # theme ID placeholder — lấy ID thật:
# python3 -c "..."  → GET /admin/api/<ver>/themes.json, lấy theme role=main
```

## 3. Google Search Console (không bắt buộc, nhưng gần như mọi thứ hay đều cần)

Google Cloud Console → tạo project → bật **Search Console API** → tạo OAuth client
(Desktop app) → tải về thành `scripts/credentials.json`. Lần chạy đầu sẽ mở browser
và ghi `scripts/gsc_token.json`.

```bash
python3 scripts/gsc_fetcher.py --help
```

Lưu ý: scope `webmasters.readonly` **không** submit được sitemap / index request —
làm tay trong GSC UI.

## 4. Cài skills

Copy `skills/genseo-*` vào thư mục skill của agent, ví dụ Claude Code:

```bash
cp -r skills/genseo-* ~/.claude/skills/
```

Mở `skills/genseo-auto-publish/SKILL.md` và điền những chỗ `REPLACE ME`:

- **bảng roster tác giả** — người thật trong team bạn, mỗi người 1 trang
  `/pages/<handle>` sống trên site. Publisher từ chối byline lạ.
- **priority brands** — vendor nào ưu tiên, vendor nào KHÔNG được link.
- các mốc thị trường (bản gốc nhắm Singapore) → đổi sang thị trường của bạn.

## 5. Chạy thử an toàn

```bash
python3 scripts/fetch_all_articles.py                    # xác nhận API chạy
python3 scripts/validate_article.py mybai.md --draft     # thử gate, không ghi gì
python3 scripts/backup_before_changes.py                 # backup trước khi ghi
```

Sau đó mới cho agent chạy 1 ticket, xem live, rồi mới bật cron.

## Nếu lỗi

| Lỗi | Nguyên nhân |
|---|---|
| `missing config ~/.genseo/shopify_token.json` | chưa làm bước 1 |
| 401/403 từ Shopify | thiếu scope, hoặc token của app khác |
| 404 khi thao tác article | blog ID vẫn là placeholder (bước 2) |
| `FileNotFoundError` một file `.csv`/`.md` | file dữ liệu không nằm trong gói — sinh nó (xem README) |
| Gate luôn FAIL ở phần author | chưa điền roster + chưa tạo `/pages/<handle>` |

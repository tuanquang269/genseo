# GenSeo — autonomous SEO pipeline for a Shopify store

GenSeo là một hệ thống SEO tự động cho Shopify: một AI agent đọc "ticket", viết bài
theo chuẩn E-E-A-T/AEO, **bị một cổng kiểm tra máy chặn nếu bài mỏng**, rồi tự publish
kèm schema, ảnh và internal link. Phần thắng của hệ thống không nằm ở model — nằm ở
**cái gate** và ở các script tự chữa lỗi sau khi publish.

> ⚠️ Các script trong `scripts/` ghi trực tiếp lên store thật qua Shopify Admin API
> (sửa bài, unpublish, tạo 301, patch theme). Chạy trên store thử trước.
> Nhiều script có `--dry-run` / `--apply`: mặc định xem trước, chỉ ghi khi có `--apply`.

## 3 lớp

| Lớp | Ở đâu | Việc |
|---|---|---|
| **Brain** — skills | `skills/genseo-*/SKILL.md` | prompt/quy trình cho AI agent. `genseo-auto-publish` là orchestrator chính. |
| **Hands** — scripts | `scripts/*.py` | gọi Shopify/GSC API: publish, sửa schema, gộp bài trùng, redirect, báo cáo. Python thuần, không cần framework. |
| **Rules** — knowledge base | `knowledge_base/*.md` | luật AEO/GEO + E-E-A-T mà skill phải tuân theo. |

## Vòng chạy hằng ngày

1. **Ticket** → một file markdown (xem `tickets.example.md`): mỗi ticket = 1 bài, đã
   chốt trước keyword, collection để link, góc nội dung, tác giả.
2. **Cron / lệnh tay** bảo agent: *"continue with the next ticket in <file>.md"*.
3. Agent chạy `genseo-auto-publish`: check trùng trên site thật → research → viết →
   tạo ảnh → **GATE** → publish.
4. **Gate** = `python3 scripts/validate_article.py <file>.md --draft`. Exit 1 = không
   được publish. Đây là thứ quan trọng nhất trong repo: model rẻ chỉ làm đúng những gì
   bị kiểm tra bằng máy, checklist "tự đánh giá" thì nó tick bừa.
5. **Publish** qua `scripts/shopify_publisher.py` (gắn Article + FAQPage JSON-LD, tác
   giả có thật, upload ảnh lên CDN).
6. **Dọn dẹp hằng ngày** — 4 lệnh xác định, không phụ thuộc model:
   ```bash
   python3 scripts/repair_schema.py --recent 24    # dựng lại schema/author bị hỏng
   python3 scripts/fix_untitled.py --apply         # cứu bài mất title
   python3 scripts/find_dupes.py --apply           # gộp/redirect bài trùng
   python3 scripts/verify_published.py <id>        # spot-check
   ```

## Skills

| Skill | Việc |
|---|---|
| `genseo-auto-publish` | orchestrator: viết + gate + publish 1 bài mới (file lớn nhất, đọc trước) |
| `genseo-refresh` | làm mới bài CŨ tại chỗ, **append-only**, không đổi URL, giữ title đang rank |
| `genseo-content-writer` | writer thuần cho model rẻ (template + self-audit) |
| `genseo-seo-strategist` | đọc data → ra content brief, không viết bài |
| `genseo-collection-optimizer` | SEO cho trang collection (title/meta/mô tả) |
| `genseo-keyword-planner` | CSV keyword (GSC/Google Ads) → topic cluster |
| `genseo-content-refresh`, `genseo-refresh-planner` | lớp lập kế hoạch refresh |
| `genseo-seo-optimizer` | triage `CRAWL_REPORT.csv` từ sitemap crawler |
| `genseo-index-checker`, `genseo-performance-tracker`, `genseo-aeo-tracker` | theo dõi index / thứ hạng / brand mention trong AI |

Skill là file markdown thường — chạy được với Claude Code, Antigravity, hay bất kỳ
agent nào đọc được skill/prompt. Bản gốc chạy trên Antigravity (vì có sẵn image-gen).

## Script đáng đọc trước

| Script | Việc |
|---|---|
| `validate_article.py` | **cổng chất lượng**: ≥900 từ, có bảng, giá SGD, ≥2 link collection, tác giả thật, FAQ, không link 404, ≥3 ảnh inline, độ khớp chủ đề, title ≤60 ký tự |
| `shopify_publisher.py` | publish/update: HTML, schema, ảnh CDN, IndexNow ping |
| `repair_schema.py` | dựng lại JSON-LD **từ HTML đã render** — idempotent, không quan tâm bài được publish bằng đường nào |
| `gsc_fetcher.py` | lấy data Search Console (query/page/country) |
| `seo_drift.py` | snapshot + diff các element SEO để phát hiện regression |
| `sitemap_crawler.py` | crawl sitemap, tìm 404/lỗi cấu trúc |
| `build_rich_tickets.py`, `build_ctr_tickets.py`, `refresh_targets.py` | sinh ticket từ data GSC |
| `find_dupes.py` | xử lý cannibalization: phát hiện bài trùng, unpublish trước rồi mới 301, có log revert |
| `backup_before_changes.py` | chạy TRƯỚC mọi thao tác hàng loạt |

## Không có trong gói này

Đây là **hệ thống**, không phải dữ liệu. Các file input sau đã bị loại bỏ — bạn tự
sinh cho store của mình:

- ticket queues (`*-tickets.md`) → tự sinh bằng `build_*_tickets.py` từ GSC của bạn
- `PUBLISHED_ARTICLES_TRACKER.csv`, `COLLECTION_TRACKER.csv`, `frozen_articles.txt`
- `existing_articles.json`, `shopify_products_all.json` → sinh bằng `fetch_all_articles.py`
- toàn bộ draft đã publish, ảnh, log, backup, báo cáo audit

Script nào thiếu input sẽ báo lỗi thiếu file — đọc tên file trong lỗi rồi sinh nó.

**AI agent: đọc `AGENTS.md` trước tiên** (sổ tay vận hành: luật cứng, playbook theo
việc, lệnh cụ thể, lỗi thường gặp). Rồi `LOCALIZE.md` — liệt kê mọi placeholder phải thay cho
đúng store/thị trường của bạn. Cài đặt: `SETUP.md`. Thêm ngữ cảnh: `docs/WORKFLOW_UPGRADE.md` (vì sao có cái gate),
`docs/10_step_article.md` (quy trình viết), `docs/internal_linking_strategy.md`.


## Multi-store runs (2026-10-27)

Use an explicit store on the new entry point. The existing Wellness Nest launchd job,
queue, writer prompt, image rules, and schedule stay in place.

```bash
/usr/bin/python3 scripts/run_store.py --store wellnessnest --dry-run
/usr/bin/python3 scripts/run_store.py --store cherish --day 2026-10-28 --dry-run
/usr/bin/python3 scripts/run_store.py --store cherish --day 2026-10-28 --slot 1 --print-prompt
```

Each `stores/<id>/profile.json` owns its context allowlist, storefront and Admin
store domains, credential source, blog handle, templates, calendar, daily volume,
and gates. Cherish uses `SHOPIFY_CHERISH_LIVE_*` through the shared `t3_store.py`
client-credentials adapter. Secret values never enter writer context. The writer
receives approved store files only. Cherish uses the verified `cc/claude-sonnet-5-5` model. It has no tools, shared skills, or global
agent memory. The writer uses the fixed hosted OAuth router at `ai.patigroup.com`.
It does not use a local model or a per-token AI provider. No model call runs in a dry run.

Cherish reads the approved 250-row calendar. Its current cap is seven posts per day.
The first 21 rows must retain `approval=kevin`. A later calendar size change needs
an explicit profile/code review. Each article package is JSON with `store`, `day`,
`slot`, `title`, `handle`, `meta_description`, `body_html`, and `facts`. Each fact
has `claim`, `source`, and `quote`. Sources must be approved profile context or the
row's evidence URLs. Live product facts can cite `shopify://<shop>/products/<handle>`. Use an approved full-page template. Remove preview labels and
executable scripts. The runner restores the approved CSS. It checks the template's
unchanged `#rules-machine` rules and FAQ schema against visible answers.

```bash
# Create missing packages through the OAuth writer, then run all gates.
/usr/bin/python3 scripts/run_store.py --store cherish --day 2026-10-28 --apply --generate
# Use packages written by a separate approved writing lane instead.
/usr/bin/python3 scripts/shopify_publisher.py --store cherish --day 2026-10-28 --apply --packages-dir /absolute/package/directory
```

Package names are `YYYY-MM-DD-<slot>.json`. Default: `stores/cherish/drafts/`.
The publish path checks the store and live product catalog, current prices,
evidence quotes, numerical claims, duplicate titles/handles (including drafts),
and the existing `blog-styles/tools/check.py` render gate. A failed gate stops
the run. Registry and calendar handles must belong to the selected store. Links
to another store's product fail. All Shopify writes re-check the store domain
and the credential domain. Legacy Wellness Nest scripts refuse a Cherish selection.

The Shopify body contains scoped article CSS, the approved article layout, and
BlogPosting, BreadcrumbList, and FAQPage schema. It excludes preview controls and
store header/footer. Every article is created unpublished. A readback checks the returned handle,
layout, image count, FAQ schema, and store boundary before an auto-approved article
is changed to live. Per-store locks, completion state, and local
review notifications live in `state/cherish/`. Review notices also go to stdout.
No Slack or email message is sent. If a post is already in Shopify but the local
ledger is absent, the duplicate guard blocks it for operator reconciliation.

`approval=kevin` creates an unpublished article and a review notice.
`approval=auto` publishes after all gates pass. Fact quotes and number checks are
mechanical checks. They do not prove every paraphrased claim. Kevin reviews the
first 21 posts before the coordinator enables daily generation.

The Cherish plist is supplied in `deploy/com.pati.genseo-cherish.plist`. It has
not been installed or loaded. After Kevin approves the first 21 posts, run:

```bash
cp /Users/kevinkreative/genseo/deploy/com.pati.genseo-cherish.plist /Users/kevinkreative/Library/LaunchAgents/com.pati.genseo-cherish.plist
launchctl enable "gui/$(id -u)/com.pati.genseo-cherish"
launchctl bootstrap "gui/$(id -u)" /Users/kevinkreative/Library/LaunchAgents/com.pati.genseo-cherish.plist
```

The job runs at 07:45 in the machine's local timezone (Asia/Ho_Chi_Minh on this
Mac). `RunAtLoad` is false. Check the machine timezone before enabling it elsewhere.
Use `/usr/bin/python3`; this Mac has BeautifulSoup and Playwright on that interpreter.
A missing library or browser fails the render gate and blocks publication.

Validation: `/usr/bin/python3 -m unittest discover -s tests -p test_store_isolation.py -v`.

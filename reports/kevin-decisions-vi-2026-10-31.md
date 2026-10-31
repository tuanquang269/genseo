# Quyết định cho anh — 2026-10-31

Bản này chỉ để anh đọc và quyết. Không có PR nào vào `main`, không PR nào bị đóng, không bài nào được publish. `origin/main` vẫn là `6c46771` ("Publish shilajit loading with food article"). Trên main, FloraFresh trong `scripts/florafresh_rules.py` vẫn là `CFU = "1 billion CFU"` và `_LABEL_CFU = 1e9` cho đến khi bước 20–22 vào main.

Nguồn danh sách: [bản merge plan 2026-10-30](https://github.com/tuanquang269/genseo/pull/100) (`reports/draft-pr-merge-plan-2026-10-30.md`). Em lấy `origin/main`, bỏ qua main local trên Mac (lane Cherish).

## TL;DR — 3 quyết định

1. **Chờ trang Mike trước khi land [#90](https://github.com/tuanquang269/genseo/pull/90) → [#88](https://github.com/tuanquang269/genseo/pull/88) → [#91](https://github.com/tuanquang269/genseo/pull/91).** `https://wellnessnest.co/pages/mike-moretti` vẫn HTTP 404 (2026-10-31 01:47:44 GMT, HEAD, không redirect). `https://wellnessnest.co/pages/dr-marcus-hale` cùng phiên là HTTP 200 (01:47:39 GMT). Em không tạo trang. Ba PR đã được đối chiếu với `origin/main` và vẫn là draft. Guard 15B CFU và byline blog Mike Moretti nằm trên #90 và #88. Byline landing trên #90 và #91 vẫn là Dr. Marcus Hale.

2. **Land ngay bắt đầu ở [#98](https://github.com/tuanquang269/genseo/pull/98), rồi chuỗi sạch bước 2–19.** Suite trên `origin/main` đang fail 2 test landing-queue cho đến khi #98 vào. Em không merge #98. Trong chuỗi đó không có quyết định sản phẩm mới. [#71](https://github.com/tuanquang269/genseo/pull/71) vào main trước, rồi mới retarget [#73](https://github.com/tuanquang269/genseo/pull/73) về main.

3. **Năm PR chờ anh: [#58](https://github.com/tuanquang269/genseo/pull/58), [#85](https://github.com/tuanquang269/genseo/pull/85), [#92](https://github.com/tuanquang269/genseo/pull/92), [#93](https://github.com/tuanquang269/genseo/pull/93), [#96](https://github.com/tuanquang269/genseo/pull/96).** Plan `9830990139` (ShilaSource, 8 tuần, $56.69) vẫn không được viết vào copy. [#89](https://github.com/tuanquang269/genseo/pull/89) nằm trong #91 — để mở.

## Wait-stack em đã chuẩn bị

Mỗi nhánh merge `origin/main` riêng. Không rebase, không force-push, không xếp ba PR lên nhau.

| PR | Nhánh | Head sau pass này | So với `origin/main` | Draft |
| --- | --- | --- | --- | --- |
| [#90](https://github.com/tuanquang269/genseo/pull/90) | `cursor/combine-9-10-on-88-1023` | `c3de3b81` — merge `origin/main` vào tip cũ `4386e48` | Trước pass: chậm 23 commit. Sau: chậm 0, hơn 5 | Vẫn draft |
| [#88](https://github.com/tuanquang269/genseo/pull/88) | `cursor/florafresh-15b-mike-moretti-0e04` | `b622718` — đã chứa `6c46771` từ 2026-10-28 | `git merge origin/main` báo already up to date. Không commit mới | Vẫn draft |
| [#91](https://github.com/tuanquang269/genseo/pull/91) | `cursor/untracked-drafts-15b-1024` | `ade6dd7` — đã chứa `6c46771` | Already up to date. Không commit mới | Vẫn draft |

#90 merge sạch (ort), không conflict marker. Em giữ phía 15B và Mike:

- `scripts/florafresh_rules.py`: `CFU = "15B CFU"`, `_LABEL_CFU = 15e9`. Blob trùng #88 (`da0a0736`).
- `scripts/genseo_roster.py`: `DEFAULT_BLOG_NAME = "Mike Moretti"`.
- `scripts/run_landing_headless.sh` và `skills/genseo-landing-pages/SKILL.md` trên #90: byline landing vẫn **Dr. Marcus Hale**, role "Wellness Nest editorial team".
- Ticket FloraFresh đang mở trên #90 ghi 15B CFU. Các dòng "1 billion CFU" còn lại nằm trong ticket đã đóng.
- Guard FusiForce và shilajit gummies của #90 còn nguyên.
- `python3 -m unittest tests.test_florafresh_guard tests.test_blog_byline tests.test_fusiforce_guard tests.test_shilajit_gummies_guard` trên #90 sau merge: 78 tests, OK. Em không chạy lại full suite; hai test đỏ trên main vẫn là việc của #98.

#88 cũng là 15B và Mike cho **blog**. Hai file prompt landing trên chính #88 lại ghi byline listicle mới là Mike Moretti và "Do not byline Dr. Marcus Hale" (`scripts/run_landing_headless.sh`, `skills/genseo-landing-pages/SKILL.md`). #90, #91 và main giữ Hale. Em không sửa #88 vì nhánh đã chứa main, không có conflict để giải. Em thử merge #88 vào #90 đã refresh trên một bản tạm và không push. Cây nội dung trùng cây của #90 (`d17b048`). Hale, 15B, và guard FusiForce / shilajit gummies của #90 còn nguyên. Thứ tự land vẫn là #90 rồi #88.

#91 chỉ sửa `published_drafts/`. Draft FloraFresh trên nhánh đó là 15 tỷ CFU của SNZ-1969 mỗi 2 gummies, byline `[Mike Moretti](/pages/mike-moretti) — Co-founder, Wellness Nest`. File guard `scripts/florafresh_rules.py` trên #91 vẫn là bản main (1 billion), vì PR này không đụng file đó. Câu "1 billion CFU" còn trong bài dosage là liều thử nghiệm Lactobacillus (NCT03688321), không phải dòng label FloraFresh. #91 vào sau #90 và #88 thì guard 15B đã có sẵn. Prompt landing trên #91 vẫn là Hale.

Trang Mike: HEAD `https://wellnessnest.co/pages/mike-moretti` lúc 2026-10-31 01:40:33 GMT là HTTP 404, và lúc 01:47:44 GMT vẫn HTTP 404, không có `Location`. GET cùng URL ra title "404 Not Found – Wellness Nest". Em không tạo page.

## Land ngay — bước 1–19

Chuỗi này `git merge-tree` sạch trên plan 2026-10-30. FloraFresh trên main vẫn 1 tỷ CFU cho đến bước 20. Không đụng theme. #46 và #50 là draft chưa publish.

| Bước | PR | Việc |
| --- | --- | --- |
| 1 | [#98](https://github.com/tuanquang269/genseo/pull/98) | Hai test landing-queue trỏ ticket Shockwave đang mở. Đây là fix suite. Land trước mọi refresh của #95. Em không merge trong pass này. |
| 2 | [#84](https://github.com/tuanquang269/genseo/pull/84) | Audit mobile clutter cho bài blog, read-only. |
| 3 | [#86](https://github.com/tuanquang269/genseo/pull/86) | Ghi chú brand-SERP cho slide vị trí 2026-10-21. |
| 4 | [#83](https://github.com/tuanquang269/genseo/pull/83) | Báo cáo AI referrer theo domain, theo tuần. |
| 5 | [#78](https://github.com/tuanquang269/genseo/pull/78) | Audit nội dung news-blog theo quý, read-only. |
| 6 | [#75](https://github.com/tuanquang269/genseo/pull/75) | Gap listicle off-page cho AgeAura và ShilaSource. |
| 7 | [#72](https://github.com/tuanquang269/genseo/pull/72) | Gap map AgeAura. Sản phẩm trong map là AgeAura Pure NMN + TMG NAD+ Complex. Đoạn crawl có chữ Urolithin là claim cần kiểm, không phải SKU mới. |
| 8 | [#70](https://github.com/tuanquang269/genseo/pull/70) | Audit read-only: PDF COA so với HTML crawl được. |
| 9 | [#69](https://github.com/tuanquang269/genseo/pull/69) | Session đi thẳng vào deep content trên báo cáo GEO. |
| 10 | [#81](https://github.com/tuanquang269/genseo/pull/81) | Tách mention và citation. Một mention chỉ có Urolithin không tính là AgeAura. |
| 11 | [#65](https://github.com/tuanquang269/genseo/pull/65) | Điểm GEO sau gate và file fix sẵn. `scripts/apply_geo_live_fixes.py` mặc định dry-run, `--apply` chỉ ghi dưới `docs/geo-live-fixes-out/`, không gọi Shopify Admin API. |
| 12 | [#64](https://github.com/tuanquang269/genseo/pull/64) | Catch-up đăng nhập opt-in khi lỡ slot sáng. Plist nằm trong `deploy/`. Self-apply không cài plist và không gọi `launchctl`. |
| 13 | [#87](https://github.com/tuanquang269/genseo/pull/87) | Đề xuất FAQ striking-distance. Khối birth-control dùng SNZ-1969, 15B CFU mỗi 2 gummies, byline Mike Moretti. Merge bốn doc không sửa bài live. Áp một khối vào bài live vẫn chờ trang Mike trả 200. |
| 14 | [#46](https://github.com/tuanquang269/genseo/pull/46) | QA listicle Turkesterone chưa publish (`gsl-preview-turkesterone-listicle-261016`). Để unpublished. |
| 15 | [#50](https://github.com/tuanquang269/genseo/pull/50) | QA listicle AgeAura NMN + TMG chưa publish (`gsl-preview-ageaura-nmn-tmg-listicle-261017`). Land trước mọi refresh sau của #96 để phần Huang / sao / offer còn. PR không đổi binding Kaching. |
| 16 | [#67](https://github.com/tuanquang269/genseo/pull/67) | Check canonical URL trước publish, kèm crawl 2026-10-19. |
| 17 | [#97](https://github.com/tuanquang269/genseo/pull/97) | Shopify HTTP 429 trên dead-link check của draft là `UNVERIFIED`, exit 3. Exit 0 mới là pass. 404 hoặc 410 vẫn exit 1. |
| 18 | [#71](https://github.com/tuanquang269/genseo/pull/71) | Audit entity và bản đồ tên canonical. FloraFresh trong map đó là 15B CFU của SNZ-1969. Merge #71 vào main trước khi retarget #73. |
| 19 | [#73](https://github.com/tuanquang269/genseo/pull/73) | Một block Article JSON-LD mỗi bài. Base trên GitHub hiện là nhánh của #71, không phải main. Sau khi #71 ở trên main, retarget #73 về main rồi merge. Đề xuất `sameAs` của Organization nằm trong body PR. Diff không sửa file theme. |

## Chờ trang Mike Moretti — bước 20–22

Publisher vẫn check URL live. Draft blog mới ký Mike sẽ fail check đó cho đến khi `/pages/mike-moretti` trả 200. Anh chọn một trong hai: tạo trang (ngoài repo này), hoặc chấp nhận draft blog mới fail-closed đến khi trang có. Guard 15B đi cùng hai pull #90 và #88. Không có draft hiện tại nào chỉ đổi mỗi guard.

Quyết định trang này cũng chặn việc áp khối FAQ của #87 và refresh #94.

| Bước | PR | Việc |
| --- | --- | --- |
| 20 | [#90](https://github.com/tuanquang269/genseo/pull/90) | Guard label FusiForce và shilajit gummies. `scripts/florafresh_rules.py` trùng blob #88 (`da0a0736`, 15B). Land **trước** #88. Thứ tự ngược lại conflict `daily-landing-tickets.md`. Head mới `c3de3b81` đã chứa main. |
| 21 | [#88](https://github.com/tuanquang269/genseo/pull/88) | Guard FloraFresh hiện tại (`15B CFU` / `15e9`) và byline blog Mike Moretti. #88 không phải tổ tiên của #90. Blog byline Hale thì fail. Hale ở lại `roster.json` cho landing. Sau refresh này, merge #88 lên #90 không đổi file nào: prompt landing Mike trên #88 không ghi đè Hale của #90. Land #88 một mình, trước #90, thì prompt listicle mới trên #88 chuyển sang Mike. |
| 22 | [#91](https://github.com/tuanquang269/genseo/pull/91) | Bốn draft FloraFresh trước đó chỉ có trên Mac, cộng 16 file của #89. Đếm 15 tỷ CFU SNZ-1969 mỗi 2 gummies. Byline blog Mike Moretti. Publish các draft đó chờ trang tác giả. |

## Chờ anh

| PR | Vì sao chờ | Conflict với cây 22 pull |
| --- | --- | --- |
| [#58](https://github.com/tuanquang269/genseo/pull/58) | Anh đã bảo chờ. Merge sẽ đăng ký `.github/workflows/genseo-cloud-failover.yml` (18:30 và 22:00 ICT, thêm `workflow_dispatch`). Job bỏ qua trừ khi biến repo `GENSEO_CLOUD_FAILOVER` là `1`. Script fail-closed và không publish. | Sạch. Chờ vì đăng ký workflow, không phải vì conflict. |
| [#85](https://github.com/tuanquang269/genseo/pull/85) | PR nói append queue hoặc chạy visibility live vẫn cần GO. Script từ chối ghi `daily-tickets.md`. | `knowledge_base/AEO_GEO_GUIDELINES.md` (chung với #83). |
| [#92](https://github.com/tuanquang269/genseo/pull/92) | Hai claims log còn câu hỏi: Mike Moretti hay byline roster, giá $59.99 cũ trên trang review, và liều gummies. Log cũng ghi selling plan ShilaSource `9830990139`, nhóm "Delivery every 8 weeks", allocation 5669 ($56.69). Cách tính charge chưa chốt. | `roster.json`, `scripts/genseo_roster.py`. |
| [#93](https://github.com/tuanquang269/genseo/pull/93) | Draft refresh FAQ cho ba URL đang live. Nhánh mang thêm một bản sửa rule 15B. Khi refresh, giữ 17 file dưới `drafts/gsc-2026-10-24/`. Draft birth-control và period nêu SNZ-1969 và không ghi số CFU. Plan này không publish chúng. | 16 file, liệt kê trong merge plan. |
| [#96](https://github.com/tuanquang269/genseo/pull/96) | Giá landing chưa publish được kéo theo product JSON public (fetch 2026-10-26). Bảng pack trong vault vẫn là nguồn kia. Sweep ghi ShilaSource Automatic Refill $49.99 / $44.99 / $39.99 (plan `10022748475` / `10022781243` / `10022814011`) và cố ý bỏ plan `9830990139` ($56.69, 8 tuần). Cách Kaching charge plan đó vẫn mở. #96 cũng port guard 15B; `scripts/florafresh_rules.py` auto-merge, doc guard và test thì không. | 20 file sau khi #46 và #50 đã trong cây, gồm listicle AgeAura `261017` và `landing_drafts/turkesterone-listicle-261016.claims.md`. |

Khi nào refresh #96: giữ byte guard FloraFresh của #88 / #90, giữ phần QA không phải giá của #46 và #50, và chỉ ghi giá từ nguồn anh chỉ định. Plan `9830990139` ở ngoài copy cho khách cho đến khi charge 8 tuần $56.69 được xác nhận.

## Để mở

Em không đóng PR nào.

### Close-candidate sau này

| PR | Quan hệ | Khi nào mới thành close-candidate |
| --- | --- | --- |
| [#89](https://github.com/tuanquang269/genseo/pull/89) | Một commit là tổ tiên của #91. 16 file `published_drafts/`. #91 thêm bốn file: `are-vaginal-probiotics-worth-it-how-much-2026.md`, `vaginal-probiotics-empty-stomach-us-2026.md`, `vaginal-probiotics-on-an-empty-stomach-us-2026.md`, `where-to-buy-vaginal-probiotics-in-the-us-5-checks-2026.md`. Merge #89 sau #91 là merge rỗng. | Sau khi #91 ở trên main. Để mở đến đó. |
| [#68](https://github.com/tuanquang269/genseo/pull/68) | Block experience cũ, evidence-only (`scripts/experience_block.py`). #82 là block sau, có cổng rights (`scripts/first_hand_experience.py`). | Nếu #82 là block sẽ ship. Refresh #68 là một thiết kế thứ hai, không phải commit sót. |
| [#9](https://github.com/tuanquang269/genseo/pull/9), [#10](https://github.com/tuanquang269/genseo/pull/10) | Đang mở, không phải draft, cả hai `CONFLICTING` với main. #90 là bản port lên rule file hiện tại. | Sau khi #90 được nhận làm bản port. Để mở đến đó. |
| [#99](https://github.com/tuanquang269/genseo/pull/99) | Báo cáo readiness 2026-10-28. Một file. Sạch với cây 22 pull. | Sau khi plan 2026-10-30 là bản anh giữ. File không đụng report này. |

#88 không phải close-candidate khi chưa có #90 trên main. #90 đã chứa `origin/main` qua `c3de3b81`, và không chứa commit merge `b622718` của #88. Nội dung guard 15B thì trùng. Land #88 trước #90 vẫn là thứ tự sai.

#95 không phải close-candidate. Phần sửa test process-list chỉ có trên #95.

#98 không phải close-candidate. Đó là fix landing-queue.

### Để mở đến khi có refresh

Các PR này conflict với cây 22 pull. Conflict là text. Để mở đến khi refresh tồn tại.

| Bước | PR | Cách giữ khi refresh |
| --- | --- | --- |
| 23 | [#95](https://github.com/tuanquang269/genseo/pull/95) | Sau #98. Conflict `tests/test_landing_rotation.py` và `tests/test_queue_closures.py` cả hai thứ tự. Giữ assertion Shockwave của #98 trên hai file đó. Lấy fixture process-list của #95 trong `scripts/genseo_self_apply.sh`, `scripts/genseo_sync_main.sh`, `tests/test_self_apply.sh`, `tests/test_sync_main.sh`. Bốn file đó auto-merge với #64. #95 refresh được ngay sau #98, không cần chờ bước 20–22. |
| 24 | [#77](https://github.com/tuanquang269/genseo/pull/77) | Sau #71 và #97. Một conflict: `scripts/validate_article.py`. Giữ check entity và exit 3 `UNVERIFIED` cho 429. Thêm gate cụm gần-trùng, warn-only. |
| 25 | [#82](https://github.com/tuanquang269/genseo/pull/82) | Sau #88. Conflict `scripts/validate_article.py`, `skills/genseo-auto-publish/SKILL.md`, `skills/genseo-content-writer/SKILL.md`. Block first-hand có cổng rights. Quote có sẵn tắt trừ khi `rights_confirmed` và `approved_by` được set. Giữ rule #88 (blog Hale thì fail), hành vi 429 của #97, và sửa validator của #71 / #67. |
| 26 | [#94](https://github.com/tuanquang269/genseo/pull/94) | Sau #88 và #97, và sau cùng quyết định trang tác giả với bước 20. Tám conflict: `DAILY-RUN.md`, `daily-tickets.md`, `roster.json`, `scripts/genseo_roster.py`, `scripts/refill_tickets.py`, `scripts/validate_article.py`, `skills/genseo-auto-publish/SKILL.md`, `skills/genseo-content-writer/SKILL.md`. #94 thêm bio nguyên văn của Mike và headshot null, nhưng gate của nó vẫn nhận blog byline Dr. Marcus Hale. Giữ rule #88: blog Hale thì fail. Lấy câu bio và headshot null ở chỗ khớp rule đó. Landing vẫn Hale. |

## Ngoài bốn nhóm

[#1](https://github.com/tuanquang269/genseo/pull/1) ở lại GO theme / IndexNow. Ping của publisher bị env-gate. PR không upload theme. Vẫn conflict với main, nên không nằm trong thứ tự này.

[#38](https://github.com/tuanquang269/genseo/pull/38) là bootstrap Mac Mini, đang `CONFLICTING`, ngoài đoàn draft.

AgeAura trong các diff này là NMN + TMG. Chữ "urolithin" trong #1, #72, #75, #81, #68, #82 là guard, audit, hoặc quote crawl.

Pass này không sửa theme, không sửa trang paid-traffic, không gửi email, không đụng Meta, không ghi Shopify.

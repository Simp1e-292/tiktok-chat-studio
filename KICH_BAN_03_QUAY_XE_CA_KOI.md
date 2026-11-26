# KỊCH BẢN TẬP 3 — "QUAY XE HỒ CÁ KOI" (VĂN PHÒNG KHỦNG LONG)

- **Series:** Trọn bộ chuỗi *"Hố Trạm Cân"* (Tập 1: Bể Bơi Vô Cực → Tập 2: Hồ Cá Koi Của Sếp → **Tập 3: Quay Xe Hồ Cá Koi**)
- **Tên nhóm chat:** `Văn Phòng Khủng Long` (Avatar: `assets/avatar_khung_long_cua_thep.jpg`)
- **Định dạng dựng:** Chuẩn **Con Bò Đi Làm** (1 bong bóng = 1 cảnh cuốn chiếu, ảnh/GIF tách riêng `media_shot` cỡ lớn, header ẩn/hiện theo nhịp, không banner spoil đầu video, không `đang nhập...`)
- **Âm thanh:** Chuẩn **Carbon AB_07 Tempo-Locked (`mode="all_conbo"`)** — `TELL ~5.80 syl/s` | `ASK ~5.85 syl/s` | `DROP ~5.15 syl/s`, khóa `-12.8 LUFS`
- **Thời lượng dự kiến:** `~47 – 50 giây` (25 cảnh)

---

## DIỄN BIẾN CHI TIẾT (25 CẢNH — CUỐN CHIẾU 1 BONG BÓNG / 1 CẢNH)

| # | Cảnh / Loại | Header | Nhân vật | Register | Hiển thị trên màn hình | Thoại TTS chuẩn (Carbon AB_07) | Media / SFX sau câu |
|:-:|:--|:-:|:--|:-:|:--|:--|:--|
| **1** | `msg` (`clear`) | ON | **Sếp** | `TELL` | `Hôm qua anh xin báo giá hồ cá Koi khắp nơi rồi.` | `Hôm qua anh xin báo giá hồ cá coi khắp nơi rồi.` | `pop` (`0.26s`) |
| **2** | `msg` (`append_same`) | ON | **Sếp** | `TELL` | `Nhưng mà…` | `Nhưng mà.` | `pop` (`0.26s`) |
| **3** | `msg` (`append_same`) | ON | **Sếp** | `TELL` | `Thôi hủy, quay lại làm TRẠM CÂN nhé anh em.` | `Thôi hủy, quay lại làm trạm cân nhé anh em.` | `pop` + `inception.mp3` (`1.25s`) |
| **4** | `msg` (`clear`) | OFF | **Tùng em (Thiết kế)** | `ASK` | `Ơ… em vừa thức trắng đêm vẽ 3D hồ cá Koi xong?!` | `Ơ, em vừa thức trắng đêm vẽ ba đê hồ cá coi xong?` | `pop` (`0.22s`) |
| **5** | `media_shot` | OFF | **Tùng em (Thiết kế)** | — | *(Chỉ GIF sốc/cạn lời cỡ lớn)* | — | `wait_a_minute_tight.wav` (`1.05s`) |
| **6** | `msg` (`clear`) | OFF | **Tùng anh (Xưởng)** | `ASK` | `Hôm trước bể bơi, hôm qua cá Koi, nay lại trạm cân?!` | `Hôm trước bể bơi, hôm qua cá coi, nay lại trạm cân?` | `pop` (`0.26s`) |
| **7** | `msg` (`append_same`) | OFF | **Tùng anh (Xưởng)** | `ASK` | `Đất xưởng chứ có phải đồ chơi đâu anh!` | `Đất xưởng chứ có phải đồ chơi đâu anh?` | `pop` (`0.28s`) |
| **8** | `msg` (`clear`) | ON | **Thanh Hải (Kế toán)** | `TELL` | `Khoan đã, hôm qua anh bảo đối tác chiến lược cơ mà?` | `Khoan đã, hôm qua anh bảo đối tác chiến lược cơ mà.` | `pop` (`0.26s`) |
| **9** | `msg` (`append_new`) | ON | **Sếp** | `TELL` | `Thì bà ấy chỉ đích danh bên thi công cá Koi cho anh.` | `Thì bà ấy chỉ đích danh bên thi công cá coi cho anh.` | `pop` (`0.26s`) |
| **10** | `msg` (`append_same`) | ON | **Sếp** | `TELL` | `Sáng nay anh mới tra ra.` | `Sáng nay anh mới tra ra.` | `pop` (`0.26s`) |
| **11** | `msg` (`clear`) | OFF | **Trang (CSKH)** | `ASK` | `Tra ra bên đó hét giá chát quá à sếp?` | `Tra ra bên đó hét giá chát quá à sếp?` | `pop` (`0.22s`) |
| **12** | `msg` (`clear`) | ON | **Sếp** | `DROP` | `Không.` | `Không.` | `pop` + `ding.mp3` (`0.65s`) |
| **13** | `msg` (`append_new`) | ON | **Trang (CSKH)** | `ASK` | `Thế sao anh quay xe gấp thế?` | `Thế sao anh quay xe gấp thế?` | `pop` (`0.24s`) |
| **14** | `msg` (`clear`) | ON | **Sếp** | `TELL` | `Chủ công ty bán cá với làm hồ Koi đó là tình nhân của bà đối tác.` | `Chủ công ty bán cá với làm hồ coi đó là tình nhân của bà đối tác.` | `pop` (`0.22s`) |
| **15** | `media_shot` | OFF | **Trang (CSKH)** | — | `🤯` + *(GIF sốc toàn tập / chó quay mặt ngơ ngác cỡ lớn)* | — | `metal_boom.mp3` (`1.05s`) |
| **16** | `msg` (`clear`) | OFF | **Kim (Nhân sự)** | `ASK` | `Thế còn dự án to bên Cổ Loa của bà ấy thì sao anh?` | `Thế còn dự án to bên Cổ Loa của bà ấy thì sao anh?` | `pop` (`0.24s`) |
| **17** | `msg` (`clear`) | ON | **Sếp** | `TELL` | `Dự án đó cũng…` | `Dự án đó cũng.` | `pop` (`0.24s`) |
| **18** | `msg` (`append_same`) | ON | **Sếp** | `DROP` | `Xịt lốp luôn rồi.` | `Xịt lốp luôn rồi.` | `pop` (`0.22s`) |
| **19** | `media_shot` | OFF | **Sếp** | — | *(GIF bất lực / ông hói chống nạnh cỡ lớn)* | — | `emotional_damage_tight.wav` (`2.40s`) |
| **20** | `msg` (`clear`) | ON | **Thanh Hải (Kế toán)** | `TELL` | `May hôm qua em chưa chuyển cọc bên cá Koi 🙂` | `May hôm qua em chưa chuyển cọc bên cá coi.` | `pop` (`0.28s`) |
| **21** | `msg` (`append_same`) | ON | **Thanh Hải (Kế toán)** | `TELL` | `Nhưng tiền phạt dời lịch trạm cân thì trừ vào đâu anh?` | `Nhưng tiền phạt dời lịch trạm cân thì trừ vào đâu anh?` | `pop` + `rimshot.mp3` (`1.15s`) |
| **22** | `sys_recall` | ON | *(Hệ thống)* | — | `🔕 Sếp đã tắt thông báo nhóm` | — | `bruh.mp3` (`0.95s`) |
| **23** | `msg` (`clear`) | OFF | **Tùng em (Thiết kế)** | `ASK` | `Thế bản vẽ 3D hồ cá Koi của em để làm gì giờ 😭` | `Thế bản vẽ ba đê hồ cá coi của em để làm gì giờ?` | `pop` (`0.22s`) |
| **24** | `media_shot` | OFF | **Tùng em (Thiết kế)** | — | `😭` + *(GIF khóc ròng / cạn lời cỡ lớn)* | — | `sadness-1.mp3` (`1.25s`) |
| **25** | `end_card` | ON | **End Card** | `TELL` | `Sếp quay xe khét lẹt: Công ty ae từng bị đối tác "lùa gà" chưa? 😂👇` | `Sếp quay xe khét lẹt, công ty anh em từng bị đối tác lùa gà chưa? Bình luận bên dưới, theo dõi xem tập bốn trạm cân có xong nổi không nhé!` | GIF + `wow.mp3` (`1.15s`) |

---

## ĐIỂM NHẤN KỊCH BẢN (ĐÚNG CÔNG THỨC VIRAL CON BÒ ĐI LÀM)
1. **Hook 0–3 giây không spoil:** Mở đầu Sếp vừa báo xin xong báo giá hồ cá Koi → ngắt 1 nhịp *"Nhưng mà…"* → lật kèo ngay lập tức *"Thôi hủy, quay lại làm TRẠM CÂN"* (bắt trọn khán giả từ Tập 1 & Tập 2 lẫn người mới xem).
2. **Đòn đối đáp `"Không."` chuẩn `Video_mẫu.mp4` (#11–#14):** Tạo đúng nhịp câu mồi → chốt 1 chữ `DROP` *"Không."* → hỏi vặn → thả cú twist *"Chủ công ty bán cá với làm hồ Koi đó là tình nhân của bà đối tác."*
3. **Twist kép (Double Punchline #14 + #18):** Chưa kịp hoàn hồn vì bị dắt mối bán cá Koi cho tình nhân, Kim hỏi thăm dự án Cổ Loa → Sếp chốt lạnh `DROP` *"Xịt lốp luôn rồi."* nổ thẳng `EMOTIONAL DAMAGE!`.
4. **Cú kết nhớ dai thương hiệu nhân vật (#20–#23):** Thanh Hải Kế toán vẫn tỉnh táo giữ tiền cọc + hỏi xoáy tiền phạt → Sếp dùng chiêu mới **`🔕 Sếp đã tắt thông báo nhóm`** (nâng cấp từ chiêu thu hồi tin nhắn Tập 2!) → Tùng em ôm bản vẽ 3D khóc ròng, mở cầu sang Tập 4.

---

## CAPTION & BÌNH LUẬN GHIM ĐỀ XUẤT (TIKTOK)
- **Caption:** `Tập 3 | Hôm qua xin báo giá hồ cá Koi rầm rộ, sáng nay Sếp quay xe 180 độ về lại trạm cân vì cú twist không ai ngờ tới 😭 #vanphongkhunglong #chuyencongso #dilam #vanphong #haihuoc`
- **Bình luận ghim:** `Thương nhất anh em nào trong kèo này: 1️⃣ Sếp bị đối tác "lùa gà" — 2️⃣ Tùng em thức đêm vẽ 3D — 3️⃣ Nhà thầu trạm cân đứng hình 3 tập? 😂👇`

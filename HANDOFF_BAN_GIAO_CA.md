# 🔄 HANDOFF BÀN GIAO CA — DỰ ÁN KÊNH TIKTOK "VĂN PHÒNG CỬA THÉP" & CÔNG NGHỆ DỰNG VIDEO

> **Thời điểm cập nhật:** 19/11/2026 16:45 (GMT+7)  
> **Workspace cục bộ:** `d:\LISP CAD\TEST\MAKE DEFFIRENT\thuong mai dien tu`  
> **Repo GitHub:** `https://github.com/Simp1e-292/tiktok-chat-studio.git` (nhánh `main`)  
> **Lưu ý Google Drive (`D:`):** Nếu chạy `git` gặp lỗi `fatal: bad object refs/desktop.ini`, chạy `fix_gdrive_sync.bat` hoặc xóa `desktop.ini` ẩn trong `.git/`.  
> **Lưu ý bảo mật:** File `.env` chứa API key ElevenLabs đã nằm trong `.gitignore` (chỉ lưu local, không đẩy lên GitHub).

---

## 1. TỔNG QUAN QUYẾT ĐỊNH & TIẾN ĐỘ HIỆN TẠI

### 1.1. Tách 2 tuyến làm việc & Chốt lập kênh TikTok mới
- **Kênh cũ `@bothuibanhang`:** Đã kiểm toán (`12` follow, `8` video, `3.145` view, `0` comment, `0` share, bỏ trống từ `03/2023`, sai tệp bán tạp hóa). **Quyết định:** Không dùng nữa, lập **kênh mới hoàn toàn** chuyên series *Chuyện Văn Phòng Cửa Thép* (xem [PHAN_TICH_KENH_VA_KE_HOACH_VIDEO.md](file:///d:/LISP%20CAD/TEST/MAKE%20DEFFIRENT/thuong%20mai%20dien%20tu/PHAN_TICH_KENH_VA_KE_HOACH_VIDEO.md) & [KE_HOACH_KENH_MOI_CUA_THEP.md](file:///d:/LISP%20CAD/TEST/MAKE%20DEFFIRENT/thuong%20mai%20dien%20tu/KE_HOACH_KENH_MOI_CUA_THEP.md)).

### 1.2. Đột phá Giọng Đọc Thuần Việt (`VieNeu-TTS` Offline 100% Miễn Phí)
- **Vấn đề gặp phải với `edge-tts` & ElevenLabs Free:**
  - `edge-tts` chỉ có 2 giọng tin tức phẳng, đọc hơi robot.
  - Gói Free API của ElevenLabs khóa giọng Việt trong Voice Library (`402 paid_plan_required`), còn 9 giọng premade (`Adam`, `Callum`, `Lily`…) đọc tiếng Việt bị mất dấu và dính ending sound tiếng Anh.
- **Giải pháp đã cài đặt & kiểm chứng thành công:**
  - Cài **`vieneu 3.8.4` (`VieNeu-TTS`)** chạy offline miễn phí 100% trên CPU (`onnxruntime`), có sẵn **25 giọng thuần Việt Bắc – Trung – Nam** (không giới hạn ký tự).
  - **Lưu ý kỹ thuật cực quan trọng khi xử lý file âm thanh `VieNeu-TTS`:** Không nén trực tiếp từ `.wav` 48kHz sang `.mp3` qua bản `ffmpeg.exe` đi kèm CapCut (sẽ bị cắt ngắn file còn ~1s). Hãy giữ nguyên file **`.wav` 48kHz** gốc cho `pyJianYingDraft` và `ffmpeg` trộn âm!

### 1.3. Pipeline Sản Xuất Thế Hệ Mới (Ảnh Thật + GIF Meme Động + SFX Đa Dạng)
- Đã nâng cấp [app.js](file:///d:/LISP%20CAD/TEST/MAKE%20DEFFIRENT/thuong%20mai%20dien%20tu/app.js#L1005-L1012) hỗ trợ chèn ảnh thực tế và ảnh động GIF (`msg.media`) vào trong bong bóng chat nhóm.
- **Kho tài nguyên đã sưu tầm sẵn:**
  - Ảnh & GIF trong `assets/episode1_media/`: ảnh cửa thép 4 cánh thật (`steel_door_4canh.jpg`), 4 GIF meme đã kiểm tra (`confused.gif`, `this_is_fine.gif`, `shocked.gif`, `clap.gif`).
  - Kho SFX Meme trong `assets/sfx_pack/`: `windows-error.mp3`, `inception.mp3`, `bruh.mp3`, `huh.mp3`, `rimshot.mp3`, `ding.mp3`, `wow.mp3`, `wait_a_minute.mp3`, `sadness-1.mp3`, kèm `sfx_pop.mp3`, `sfx_ting.mp3`.
- **Script dựng tự động (không giới hạn 8 tin nhắn nữa):**
  - [generate_episode1_v2_vieneu.py](file:///d:/LISP%20CAD/TEST/MAKE%20DEFFIRENT/thuong%20mai%20dien%20tu/generate_episode1_v2_vieneu.py): Tạo đủ 14 file `.wav` từ 9 giọng `VieNeu-TTS` (`Adam bựa`, `Thiện Minh`, `Phạm Tuyên`, `Hải Đăng`, `Ngọc Huyền`, `Trúc Ly`, `Đoan Trang`, `Ngọc Linh`, `Ngọc Trân`) + xuất `manifest.json`.
  - [render_episode1_v2_frames.js](file:///d:/LISP%20CAD/TEST/MAKE%20DEFFIRENT/thuong%20mai%20dien%20tu/render_episode1_v2_frames.js): Chụp khung chat Retina qua Chrome Headless (`node_modules/puppeteer-core` đã cài sẵn), tự chụp chuỗi 12 frame cho các tin có GIF để GIF chuyển động thật trong video.
  - [render_episode1_v2_video.py](file:///d:/LISP%20CAD/TEST/MAKE%20DEFFIRENT/thuong%20mai%20dien%20tu/render_episode1_v2_video.py): Ghép khung iPhone Titanium + banner Hook/CTA + lồng chuỗi GIF + trộn âm thanh + xuất MP4 (`video_tap_01_v2_quen_tat_layer_cad.mp4`: `78,55s`, `53,21 MB`) và đồng bộ CapCut Desktop (`Cua_Thep_Tap_01_V2`).

---

## 2. HỒ SƠ 22 NHÂN SỰ CÔNG TY (ĐÃ XÁC NHẬN & CHƯA XÁC NHẬN GIỚI TÍNH)

- **Thiết kế (8):** Hảo, Tùng anh *(Nam — `Phạm Tuyên`)*, Tùng em *(Nam — `Hải Đăng`)*, Toàn, Hải, Trưởng *(Nam — `Thiện Minh`)*, Tú, Nga *(Nữ duy nhất — `Trúc Ly`)*.
- **CSKH (5):** **Tiến Hải** *(đã xác nhận: Nam — `Adam bựa`)*, Bình, **Trang** *(Nữ — `Ngọc Huyền`)*, Linh, Ánh.
- **Mua hàng (2):** Nga *(Nữ)*, **Minh Châm** *(đã xác nhận: Nữ — `Ngọc Linh`)*.
- **Nhân sự (3):** Thuỳ, **Kim** *(đã xác nhận: Nữ, gốc Đắk Lắk — `Ngọc Trân` giọng Trung)*, Hà.
- **Kế toán (4):** **Thanh Hải** *(đã xác nhận: Nữ — `Đoan Trang`)*, Phạm Thảo, Thanh Vân, Ngọc Lan.
- *(Cần xác nhận thêm giới tính trước khi viết thoại cho Tập 2–7: Toàn, Tú, Bình, Linh, Ánh, Hảo, Hải TK, Thuỳ, Hà, Phạm Thảo, Thanh Vân, Ngọc Lan).*

---

## 3. TRẠNG THÁI TẬP 1 ĐÃ HOÀN THÀNH

- File kịch bản mới nhất: [KICH_BAN_01_CUA_KHAC_TEN_CRUSH.md](file:///d:/LISP%20CAD/TEST/MAKE%20DEFFIRENT/thuong%20mai%20dien%20tu/KICH_BAN_01_CUA_KHAC_TEN_CRUSH.md) (Bản đời thật v2: **"Quên Tắt Layer CAD Khi Xuất CNC"** — 14 tin nhắn, 1 ảnh thật, 4 GIF động, 10 cue SFX).
- File video đã render xong trên máy: `video_tap_01_v2_quen_tat_layer_cad.mp4` (`78,55s`, `53,21 MB`, nằm ngoài Git vì file nặng).
- Dự án CapCut Desktop đã đồng bộ sẵn: `C:\Users\KhunG LonG\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft\Cua_Thep_Tap_01_V2`.

---

## 4. VIỆC CẦN LÀM TIẾP Ở CA SAU (NEXT STEPS)

1. **Duyệt & tinh chỉnh nhịp Tập 1 v2 (nếu cần):**
   - Nếu người dùng muốn video dưới `60s` (gọn nhanh hơn mức `78,55s` hiện tại), chỉ cần rút gọn nhẹ câu 3, 8, 12 trong `generate_episode1_v2_vieneu.py` và chạy lại `render_episode1_v2_video.py`.
2. **Làm ấm nick TikTok mới 48–72h & đăng Tập 1:**
   - Theo checklist trong [KE_HOACH_KENH_MOI_CUA_THEP.md](file:///d:/LISP%20CAD/TEST/MAKE%20DEFFIRENT/thuong%20mai%20dien%20tu/KE_HOACH_KENH_MOI_CUA_THEP.md), chọn khung giờ `11h30–12h30` hoặc `19h30–20h30`.
3. **Viết & dựng tiếp Tập 2–7 theo công thức v2 (Đời thật + Ảnh thật/GIF + SFX + `VieNeu-TTS`):**
   - Bắt đầu bằng việc hỏi nhanh giới tính các nhân sự sẽ góp mặt ở Tập 2–3 (Toàn, Tú, Bình, Linh, Phạm Thảo, Thanh Vân) rồi viết JSON kịch bản + render hàng loạt.
4. **Nâng cấp tùy chọn (HyperFrames / Cloned Voices):**
   - Có thể nâng cấp bước `render_episode1_v2_frames.js` sang **HyperFrames** (khi muốn hiệu ứng nảy tin nhắn iOS + 3 chấm đang gõ mượt hoàn toàn) hoặc thu mẫu 5 giây giọng thật anh chị em công ty đưa vào `tts.infer(..., ref_audio=...)` của `VieNeu-TTS`.

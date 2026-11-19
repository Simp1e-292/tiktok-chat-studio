# ⚡ TIKTOK CHAT STUDIO v4.0 — VISUAL BUILDER, CAPCUT 4-TRACK & 9:16 MP4 STUDIO

> **Hệ thống dựng Video Hội Thoại TikTok & TikTok Shop hoàn chỉnh** — Hợp nhất mượt mà **Chat 1-1 (Tạp Hóa Cô Ba)**, **Group Chat đa thành viên (Cửa Thép Luxury)**, **Bài Đăng Tuyển Dụng FB** và **Backend xuất bản CapCut / MP4 1080×1920 + Edge-TTS 1.0x** trong cùng một ứng dụng thống nhất.

---

## 1. 🎯 KIẾN TRÚC KÉP (STATIC WEB + LOCAL SERVER PRO)

TikTok Chat Studio v4.0 chạy mượt mà theo 2 chế độ tự động nhận diện:

1. **🌐 Chế Độ Web Tĩnh (Mở trực tiếp `index.html`, GitHub Pages hoặc Vercel):**
   - Không cần backend, mở là chạy ngay.
   - Đầy đủ 3 chế độ sân khấu (**💬 Chat 1-1**, **👥 Group Chat**, **📢 Bài FB**), kho kịch bản & nhân vật lưu bền vững trong **IndexedDB** (`db.js`), nén ảnh tự động bằng Canvas, trình tạo kịch bản **Gemini AI**, tải/xem thử giọng thu âm riêng, chụp ảnh PNG (`.PNG`), quay video WebM kèm âm thanh (`.WEBM`), và tải gói mẫu CapCut `assets/Cua_Thep_TikTok_Luxury.zip`.
2. **🟢 Chế Độ Local Server Nâng Cao (`CHAY_STUDIO.bat` / `CHAY_STUDIO.sh`):**
   - Khởi động [`studio_server.py`](studio_server.py) (mặc định `http://localhost:8000`).
   - Kích hoạt giọng đọc AI Tiếng Việt tự nhiên **Microsoft Edge-TTS Neural** (`vi-VN-HoaiMyNeural`, `vi-VN-NamMinhNeural`), xuất **Gói Dự Án CapCut 4-Track (`.ZIP`)** cài đặt 1-Click và **Render Video MP4 1080×1920 30fps** trực tiếp từ kịch bản vừa soạn trên web!

---

## 2. ✨ CÁC TÍNH NĂNG CỐT LÕI ĐÃ KHÔI PHỤC & CHUẨN HÓA

### 2.1. Bố cục Studio 3 Cột & 3 Chế Độ Sân Khấu
* **💬 Chat 1-1 (Messenger iOS):** Đầy đủ kịch bản mẫu **Tạp Hóa & Sức Khỏe Cô Ba** (`scenario_1`, `scenario_2`), thẻ sản phẩm TikTok Shop, sticker Nút Like, thanh nhập liệu tùy chọn bật/tắt (tự lưu vào IndexedDB).
* **👥 Group Chat (Messenger Nhóm):** Hỗ trợ không giới hạn thành viên (mặc định **Văn Phòng Cửa Thép Luxury** với 5 nhân vật: Sếp Minh, Vy, Hải, Thắng, Anh Khách), đổi tên nhóm, chọn hình nền, chỉnh màu bong bóng chat và đếm thành viên.
* **📢 Bài Đăng Tuyển Dụng FB (FB Post Mockup):** Tạo mockup bài đăng Facebook 9:16 có ảnh đại diện, nội dung, ảnh đính kèm và lượt thích/bình luận.

### 2.2. Quản Lý Kịch Bản, Nhân Vật & AI Script Builder
* **📚 Lưu trữ bền vững trong IndexedDB (`db.js`):** Tự do tạo mới, sửa, xóa, Xuất/Nhập JSON kịch bản và nhân vật không lo giới hạn `localStorage`.
* **👤 Nhân vật toàn quyền + Voice Recorder/Upload:** Mỗi nhân vật cấu hình được vai trò (`Chủ tiệm` / `Khách hàng`), ảnh đại diện (tự nén JPEG siêu nhẹ), giọng đọc Neural Edge-TTS, tốc độ/cao độ, và cho phép tải file âm thanh lồng tiếng riêng (`.mp3`/`.wav`/`.ogg`).
* **✨ Tạo Kịch Bản Bằng Gemini AI:** Nhập mô tả ý tưởng + API Key (lưu an toàn trên trình duyệt qua IndexedDB) để sinh tự động chuỗi hội thoại JSON hoàn chỉnh nạp thẳng vào sân khấu.

### 2.3. Tầng Audio, Quay Web & Xuất Bản CapCut / MP4 Chuyên Nghiệp
* **🔊 Audio Routing Khớp Ngược WebM (`recorder.js` & `app.js`):** Toàn bộ SFX Ting/Pop và giọng đọc Edge-TTS / Custom Audio được hòa âm qua `Web Audio API` (`MediaStreamAudioDestinationNode`), giúp chức năng **⏺ Ghi Hình Web (.WEBM)** thu trọn cả hình và tiếng sắc nét.
* **📦 Xuất Gói CapCut 4-Track Tự Động (`capcut_draft_generator.py`):**
  * **Track 1:** Nền 1080×1920 blur ánh sáng dịu mắt.
  * **Track 2:** Chuỗi frame PNG giao diện điện thoại `720×1520` RGBA bo góc sắc nét do [`render_frames.js`](render_frames.js) chụp bằng Chromium Headless.
  * **Track 3 & 4:** Hiệu ứng Ting/Pop + Giọng đọc **1.0x** khớp chính xác từng microsecond.
  * Đóng gói kèm bộ cài đặt 1-Click **`CAI_DAT_VAO_CAPCUT.bat`** (Windows) và **`CAI_DAT_VAO_CAPCUT.command`** (macOS) tự động chỉnh chuẩn đường dẫn CapCut Desktop.
* **🎬 Render Video MP4 Trực Tiếp (`render_chotcoc_30s_video.py`):** Kết hợp frame PNG + nền 1080×1920 + âm thanh trộn 44.1kHz thành file `.MP4` H.264/AAC sẵn sàng đăng TikTok Reels.

---

## 3. 🚀 HƯỚNG DẪN KHỞI CHẠY NHANH

### Cách 1: Chạy Đầy Đủ Tính Năng (Khuyên dùng trên máy tính)
* **Windows:** Nhấp đúp file **`CHAY_STUDIO.bat`** (tự dọn `desktop.ini` nếu dùng Google Drive, cài thiếu thư viện Python/Node nếu cần và mở trình duyệt).
* **macOS / Linux:**
  ```bash
  chmod +x CHAY_STUDIO.sh
  ./CHAY_STUDIO.sh
  ```

### Cách 2: Chạy Web Tĩnh Nhanh
* Mở trực tiếp **`index.html`** trong Chrome/Edge/Safari, hoặc chạy một HTTP server tĩnh bất kỳ (ví dụ `npx serve .` / GitHub Pages / Vercel).

### Yêu Cầu Hệ Thống Cho Render Video MP4 / CapCut Động
* **Python 3.10+** (`pip install -r requirements.txt`: `pyJianYingDraft`, `edge-tts`, `gTTS`, `Pillow`)
* **Node.js 18+** (`npm install` cho `puppeteer-core` và Chromium/Chrome)
* **FFmpeg & FFprobe** nằm trên `PATH` (dùng cho chuẩn hóa thời lượng audio & render `.mp4`)

---

## 4. 📂 CẤU TRÚC THƯ MỤC DỰ ÁN

```text
tiktok-chat-studio/
 ├── index.html                   # Giao diện Studio 3 cột + sân khấu Preview 9:16
 ├── style.css                    # Toàn bộ giao diện & chủ đề Messenger / Group / FB Post
 ├── db.js                        # Tầng lưu trữ IndexedDB (nhân vật, kịch bản, cài đặt, API key)
 ├── recorder.js                  # Chụp ảnh PNG, quay WebM (Canvas + Web Audio)
 ├── app.js                       # Trái tim điều phối Studio, Playback, TTS/SFX, AI Builder & Export API
 ├── studio_server.py             # Local HTTP + REST API (/api/health, /api/tts, /api/export-capcut, /api/export-mp4)
 ├── capcut_draft_generator.py    # Bộ sinh dự án CapCut 4-track + bộ cài đặt 1-Click Win/Mac (.ZIP)
 ├── render_frames.js             # Headless Chromium chụp frame PNG bo góc RGBA từ Studio
 ├── render_chotcoc_30s_video.py  # Bộ kết xuất Video MP4 1080x1920 H.264/AAC chuẩn TikTok
 ├── render_30s_video.py          # Script CLI dựng video mẫu Cô Ba (Vitamin C)
 ├── render_comedy_30s_video.py   # Script CLI dựng video mẫu Cô Ba (Hài giải gan)
 ├── CHAY_STUDIO.bat              # Script khởi động 1-Click trên Windows
 ├── CHAY_STUDIO.sh               # Script khởi động 1-Click trên macOS / Linux
 ├── fix_gdrive_sync.bat          # Dọn file rác desktop.ini của Google Drive trên Windows
 ├── requirements.txt             # Thư viện Python cần thiết
 ├── package.json                 # Thư viện Node.js (puppeteer-core, html-to-image, qrcode)
 └── assets/                      # Hình ảnh avatar, sản phẩm, SFX Ting/Pop, video mẫu & gói CapCut mẫu
```

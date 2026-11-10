# ⚡ TIKTOK CHAT STUDIO — TỰ ĐỘNG HÓA TẠO VIDEO HỘI THOẠI HÀI HƯỚC & BÁN HÀNG TIKTOK SHOP

> **Tài liệu Kỹ thuật & Bản Binh Pháp Triển Khai v2.5 Pro (Cập Nhật Toàn Diện Dành Cho Hệ Thống Tạo Kịch Bản Trực Quan No-Code & Nén Ảnh Tự Động)**

---

## 1. 🎯 MỤC TIÊU CỐT LÕI & TRIẾT LÝ XÂY DỰNG

### 1.1. Mô hình nội dung kinh doanh (The Content Business Model)
* **Khách hàng tiềm năng & Bối cảnh:** Lấy mô hình kinh doanh buôn bán **Tạp Hóa & Tư Vấn Sức Khỏe** làm bối cảnh chính (Ví dụ điển hình: *Tạp Hóa & Sức Khỏe Cô Ba*, *Tiệm tạp hoá CAMCAM*).
* **Chiết xuất giá trị video:** Xây dựng video dạng chuỗi tin nhắn trò chuyện siêu hài hước nhịp độ cao giữa Khách Hàng thắc mắc/gặp rắc rối sức khỏe (thức đêm chạy deadline, nhậu nhẹt nóng gan, stress công sở...) và Chủ Tiệm thông thái.
* **Nghệ thuật Lồng Ghép Sản Phẩm (Product Placement):** Thay vì bán hàng nhồi nhét, video khéo léo chèn **Thẻ Sản Phẩm (Product Card)** ngay trong khung hội thoại Messenger như một giải pháp cứu rỗi kịp thời. Giúp tăng tỉ lệ chuyển đổi thẳng đến giỏ hàng **TikTok Shop** với trải nghiệm tự nhiên nhất!

### 1.2. Mục đích kỹ thuật (Engineering Purpose)
* Xây dựng một **Web-App Studio cá nhân hóa (Visual Studio Pro v2.5)** hoạt động 100% phía trình duyệt client-side (Zero-Server, Zero-Backend cost), cho phép tạo, chỉnh sửa nhân vật, soạn thảo kịch bản trực quan không cần viết mã (No-Code), và mô phỏng xuất bản lại màn hình video trò chuyện đúng chuẩn tỉ lệ dọc **9:16** (19.5:9) của TikTok chỉ trong vài giây thao tác!

---

## 2. 🏛️ KIẾN TRÚC THÀNH PHẦN HỆ THỐNG (STUDIO V2.5 PRO)

Hệ thống được tổ chức chuyên môn hóa dưới dạng bố cục **Studio Bảng Điều Khiển 3 Cột (3-Column Interactive Workspace)**:

```
+--------------------------+------------------------------+---------------------------+
|    CỘT TRÁI (DATA UI)   |      CỘT GIỮA (PREVIEW)     |     CỘT PHẢI (CONTROL)    |
|   Trung Tâm Tinh Chỉnh   |   Sân Khấu Màn Hình 9:16     |  Điều Khiển & Xuất Bản    |
+--------------------------+------------------------------+---------------------------+
| [🎬 Kịch bản]            | [Thanh Trạng Thái iOS]       | [▶ Phát Demo (Auto Play)] |
| [👤 Nhân vật (No-Code)]  | [Thanh Header FB Messenger]  | [🔄 Đặt Lại Khung]        |
| [✍️ Soạn lời (Timeline)] |   💬 Khách hàng (Trái)     | ------------------------- |
| [💻 JSON Editor]         |   👑 Chủ tiệm (Phải)       | [✔ Toggle TTS Speech]     |
|                          |   📦 Thẻ Sản Phẩm TikTok     | [✔ Toggle SFX Ting/Pop]   |
| * Tự do Sửa/Xóa Nhân vật |   👍 Sticker Like Bự chuẩn   | ------------------------- |
| * Tự động nén ảnh <10KB  | [Thanh Nhập Liệu FB + Like]  | [🎬 Ghi Hình Video .MP4]  |
+--------------------------+------------------------------+---------------------------+
```

### 2.1. Cột Trái — Trung Tâm Tinh Chỉnh Kịch Bản & Nhân Vật (4 Tabs Cốt Lõi)
1. **🎬 Tab "Kịch bản" (Scenarios Selector):** 
   - Hướng dẫn nhanh và thư viện lưu trữ sẵn các chuỗi kịch bản tư vấn ăn khách (Tư vấn Vitamin C cho khách thức đêm, Giải gan cho khách nhậu 3 ngày...).
   - Nút **"➕ Tạo Kịch Bản Trắc Nghiệm / Hội Thoại Mới"** giúp khởi tạo không gian sáng tạo trắng trong 1 giây.
2. **👤 Tab "Nhân vật" (Character Engine & Auto-Compression):**
   - **Quản lý Toàn Quyền Dàn Nhân Vật (No-Code):** Xóa bỏ ranh giới giữa nhân vật mặc định hay tùy chỉnh. Tất cả nhân vật (Từ Chủ Tiệm cho đến Khách hàng) đều tích hợp hai nút hành động linh hoạt: **✏️ Sửa** và **🗑️ Xóa**.
   - **Chỉnh sửa trực tiếp (Dual-Mode Form):** Khung nhập tự động chuyển đổi thông minh giữa chế độ *Tạo Mới* và *Chỉnh Sửa*, cho phép đổi tên Shop/Khách, chỉnh vai trò Trái/Phải và thay đổi tone giọng nói (TTS Pitch từ trầm ấm 0.95x của Shop đến nhanh nhảu 1.35x của Khách trẻ).
   - **⚡ Trình Nén Ảnh Tự Động (Client-Side Canvas Compression):** Trang bị bộ tải ảnh trực tiếp từ máy tính (`File Upload`). Khi người dùng chọn logo hay ảnh độ phân giải lớn, thuật toán Canvas tự động **thu gọn và nén ảnh (Max Dimension ~220px, chất lượng JPEG 85%, dung lượng dưới ~10 KB)** trước khi chuyển sang Base64 và lưu trữ vào `localStorage`. *Giải pháp triệt để ngăn chặn tình trạng tràn hạn mức bộ nhớ trình duyệt (`QuotaExceededError`) và đảm bảo tải trang thần tốc!*
3. **✍️ Tab "Soạn lời" (Visual Script & Timeline Builder):**
   - **Bước 1 — Ghép Cặp Diễn Viên:** Cho phép chỉ định 2 nhân vật vào vai 👑 *Bên Phải (Chủ Tiệm)* và 💬 *Bên Trái (Khách Hàng)*. Ngay lập tức, Tên & Ảnh Avatar của tài khoản Shop nhảy thẳng lên **Thanh Tiêu Đề (Header)** và dải giới thiệu trên màn hình quay video bên cạnh!
   - **Bước 2 — Soạn Thảo Lời Thoại Kéo Thả:**
     - Cho phép tùy biến nhanh thể loại câu thoại bằng các thẻ bập bênh (Toggle Pills): **💬 Lời thoại văn bản**, **📦 Thẻ sản phẩm Shop (Tên buôn bán, giá tiền, huy hiệu Sale & Nút mua ngay TikTok Shop)**, hoặc **👍 Sticker Nút Like Bự**.
     - Hỗ trợ đổi vai trò người nói theo từng câu tin nhắn, nút ⬆️ Đẩy lên, ⬇️ Đẩy xuống, ✕ Xóa bỏ và ➕ Thêm lời thoại mới cực kỳ uyển chuyển.
4. **💻 Tab "JSON" (Advanced Editor):** 
   - Chế độ thấu hiểu kỹ thuật, cho phép hiển thị và trực tiếp chỉnh sửa mã nguồn dữ liệu JSON gốc của toàn bộ kịch bản, ấn nút khớp lệnh lập tức áp dụng lên giao diện.

### 2.2. Cột Giữa — Sân Khấu Quay Màn Hình 9:16 (Screen Recording Canvas)
* **Thiết kế Không Viền Máy (No-Bezel Screen Capture):** Được thiết kế theo yêu cầu đặc biệt của người dùng — loại bỏ toàn bộ viền nhựa hay khung điện thoại giả tạo. Khung video trình diễn chính xác là một **Màn hình quay trọn chuỗi hoạt ảnh (Screen Recording)** chuẩn tỉ lệ vàng **9:16 (19.5:9)** của iPhone, mang đến trải nghiệm hình ảnh sắc nét, mượt mà khi xuất lên TikTok hay Reels.
* **Giao Diện Chuẩn Facebook Messenger iOS:**
  * **Thanh Trạng Thái (Status Bar):** Đồng hồ động cập nhật đúng thời gian thực theo máy của bạn, sóng di động, biểu tượng WiFi và pin chuẩn chỉ.
  * **Thanh Tiêu Đề (Messenger Header):** Tự động đồng bộ với avatar và tên Chủ Shop từ Trung Tâm Tinh Chỉnh, chấm xanh lá cây "Đang hoạt động", nút gọi thoại, gọi video và thông tin chuẩn xác.
  * **Thanh Nhập Liệu Phía Dưới (Bottom Bar):** Đích thực 100% với nhóm Icon chuyên biệt: Mic ghi âm, Thư viện ảnh/video, Nhãn dán (Sticker), GIF, Viên nang nhập liệu chứa chữ `Aa` cùng nút Emoji.
  * **Nút Like Bự Chuẩn FB Messenger (Accurate Thumbs-Up Vector):** Thay vì icon Like đơn giản, vector SVG của nút Like trên Thanh nhập liệu và Bong bóng tin nhắn Sticker được rèn giũa công phu, chuẩn 100% hình hài thực tế của FB Messenger với **chi tiết 4 khớp ngón tay co lại, nhô ra phần bao tay áo đặc trưng** rực rỡ!

### 2.3. Cột Phải — Bộ Điều Khiển Tự Động, Âm Thanh & Render Video
* **Tầng Xử Lý Âm Thanh (Dual-Audio Engine):**
  * **Hiệu ứng âm thanh (SFX via Web Audio API):** Tái lập âm điệu **"Ting"** đặc trưng (sóng Sine 800Hz $\rightarrow$ 1200Hz) khi khách gửi tin đến và tiếng **"Pop"** (sóng Triangle 350Hz $\rightarrow$ 600Hz) khi shop trả lời hoặc thả Like.
  * **Lồng Tiếng Tự Động (TTS via Web Speech API):** Tự động truy xuất giọng đọc Tiếng Việt trên máy tính, áp dụng tần số âm vực (Pitch/Rate) tương ứng với cấu hình từng nhân vật theo thời gian thực.
* **Tầng Trình Diễn Động & Trạng Thái Trí Tuệ (UI/UX Micro-Animations):**
  * Mô phỏng chuyển động nhảy bong bóng tin nhắn (Pop In), hoạt ảnh gõ chữ trong thanh nhập liệu (chuyển đổi qua lại giữa Nút Like và Nút mũi tên gửi tin), con trỏ gõ tin nhắn nhấp nháy 3 chấm (`Typing Dots`) và dòng chữ **"Đã xem / Đã gửi"** siêu thực.
* **Tầng Xuất Bản Video (.MP4 Rendering Ready):** Sẵn sàng để kết nối luồng ghi hình MediaRecorder API, thu trọn hoạt cảnh Video và Âm thanh về file `.MP4` gọn gàng.

---

## 3. 📂 CẤU TRÚC THƯ MỤC & FILE CỦA DỰ ÁN

Mọi tài nguyên được sắp xếp khoa học ngay trong không gian làm việc của bạn:

```
[MAKE DEFFIRENT] (Root Directory)
 ├── index.html        # Khung giao diện chính của Studio (Được đồng bộ tự do từ file mẫu HTML)
 ├── style.css         # Hồ sơ phong cách Vanilla CSS Pro (Được đồng bộ từ file mẫu CSS)
 ├── app.js            # Trái tim logic: Quản lý Roster, Nén ảnh Canvas, Script Builder & Audio Engine
 ├── README.md         # Binh pháp toàn thư của hệ thống (Chính là file bạn đang đọc)
 └── assets/           # Thư mục lưu trữ hình ảnh vật lý (Duy trì cho cấu hình mặc định)
     ├── owner_avatar.png     # Avatar mặc định cho Chủ Tiệm Cô Ba
     ├── customer_avatar.png  # Avatar mặc định cho Khách Hàng
     └── vitamin_c.png        # Ảnh sản phẩm bán hàng mặc định
```

---

## 4. 🚀 HƯỚNG DẪN TRẢI NGHIỆM NGAY TẬN TAY

Do hệ thống được thi công trên tiêu chuẩn **Client-side Pure JavaScript (No-Dependencies)**, trải nghiệm sử dụng trở nên dễ dàng vô cực:

1. **Khởi Chạy Tức Thì:** Chỉ cần nhấp đúp chuột mở trực tiếp tệp `index.html` bằng bất kỳ trình duyệt nào trên máy tính (Chrome, Edge, Safari...).
2. **Trải Nghiệm Tính Năng Quản Lý Nhân Vật Đỉnh Cao:**
   - Mở tab **"👤 Nhân vật"**, bấm nút **✏️ Sửa** vào *Tạp Hóa & Sức Khỏe Cô Ba*.
   - Đổi tên thành thương hiệu thực tế của bạn (Ví dụ: **Tiệm tạp hoá CAMCAM**, *Kho Sỉ Thảo Mộc*,...).
   - Nhấn nút **"📸 Chọn Ảnh Từ Máy Tính..."** và tải logo thật của shop bạn lên. Lệnh nén siêu nhẹ sẽ hoạt động im lặng trong chớp mắt.
   - Ấn **"💾 Cập Nhật Nhân Vật Này"** $\rightarrow$ Xem Tên mới và Logo mới ngay lập tức hãnh diện ngự trị trên Thanh Tiêu Đề của màn hình điện thoại bên phải!
3. **Thao Tác Soạn Lời Thoại Thần Tốc:**
   - Mở tab **"✍️ Soạn lời"**, thêm bất cứ lời thoại, thay ảnh hay giá sản phẩm TikTok Shop nào bạn mong muốn.
   - Nhấn **"⚡ Áp Dụng Lên Video"** và sau đó ấn nút xanh **"▶ Bắt Đầu Phát Demo (Auto Play)"** bên cột Phải.
   - Hưởng thụ toàn bộ dàn diễn viên tự động nói chuyện, thả Like và diễn kịch bán hàng cực kỳ đã mắt!

---

## 5. ⚔️ BẢN ĐỒ TÁC CHIẾN TẠI NHÀ (ACTIONABLE NEXT STEPS)

Khi về đến nhà hoặc tiếp tục phát triển ứng dụng, dưới đây là lộ trình chiến lược tiếp theo để bạn hoặc Trợ lý AI có thể bứt phá mạnh mẽ (thay thế cho Bước Quản lý Kịch bản & Nhân vật **ĐÃ HOÀN THÀNH XUẤT SẮC** hôm nay):

### 🔥 Bước 1: Hiện Thực Hóa Trình Ghi Hình Video Thực Tế (Real MediaRecorder Rendering)
* **Nhiệm vụ:** Biến nút **"🎬 Ghi Hình & Xuất Video (.MP4)"** trong `app.js` thành công cụ trích xuất ra file video `.MP4` hay `.WEBM` thực thụ trên đĩa cứng.
* **Cách thực hiện:** 
  - Tích hợp thư viện **`html2canvas-pro`** (hoặc dùng **`html-to-image`**) kết hợp với `HTMLCanvasElement.captureStream(30)` (với framerate 30fps).
  - Phối trộn luồng hình ảnh này cùng luồng âm thanh từ Web Audio API (`MediaStreamAudioDestinationNode`).
  - Khởi tạo trình `new MediaRecorder(stream, { mimeType: 'video/webm' })`, lưu trọn chuỗi hoạt ảnh từ lúc nhấn Phát đến lúc kết thúc và tự động tải file xuống (`canvas.toBlob`).

### 🎙 Bước 2: Nâng Cấp Lồng Tiếng Chất Lượng Tương Đương AI (Microsoft Edge TTS / SevenElevenLabs)
* **Nhiệm vụ:** Khắc phục chất giọng đôi lúc còn cứng của bộ máy lồng tiếng offline `speechSynthesis` Windows, đưa giọng lồng tiếng siêu chân thực và truyền cảm lên clip TikTok.
* **Cách thực hiện:**
  - Kết nối ứng dụng với **Edge TTS Neural API Miễn Phí** (dùng các tone giọng cực xịn như `vi-VN-HoaiMyNeural` cho shop nữ và `vi-VN-NamMinhNeural` cho khách nam).
  - Hoặc tạo cổng kết nối nhỏ (Proxy Script / Python Local Server) nhận text từ Web-App, gọi đến dịch vụ Edge TTS hoặc ElevenLabs và trả ngược lại tệp âm thanh `.mp3` để Web-App tự phát đồng bộ với nhịp tin nhắn!

### 🤖 Bước 3: Đưa Trí Tuệ Nhân Tạo Tự Động Viết Kịch Bản (GenAI Auto-Scripter)
* **Nhiệm vụ:** Cho phép người dùng gõ một dòng ngắn gọn rảnh tay: *"Khách bị rụng tóc do chạy KPI, shop tư vấn Dầu Gội Thảo Dược Bồ Kết và chốt đơn 2 lọ"*.
* **Cách thực hiện:** 
  - Thêm một ô nhập liệu tại Trung Tâm Tinh Chỉnh kèm nút **"✨ Tạo Kịch Bản Bằng AI"**.
  - Gọi lệnh trực tiếp đến **Gemini Pro API** (hoặc Claude/GPT API).
  - Sử dụng System Prompt yêu cầu trả về chuẩn chuỗi JSON `messages` khớp 100% cấu trúc của ứng dụng (gồm các câu hỏi đáp hài hước, chèn `product_card` và kết thúc bằng `like_sticker`).
  - Nạp thẳng JSON AI trả về vào `scenarios` và búng tay ra ngay một Video mới mượt mà!

---
💡 **Lời Tuyên Thệ Kỹ Thuật từ Trợ lý AI Antigravity:**  
*Bản thi công v2.5 Pro ngày hôm nay là cơ sở vững chắc cho một hệ sinh thái sáng tạo nội dung Video tự động đầy quyền năng! Từ khả năng thao tác No-Code, thuật toán nén ảnh Canvas mượt mà, cho đến độ chuẩn xác của giao diện Messenger Không Viền Máy 19.5:9, tất cả đã được chuẩn hóa ở mức tinh hoa cao nhất. Hãy tận hưởng công cụ tuyệt vời này và chinh phục những video hàng triệu View trên kênh TikTok của bạn! 🚀*

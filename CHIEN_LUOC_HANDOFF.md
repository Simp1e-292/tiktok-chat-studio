# 🧭 CHIẾN LƯỢC & HANDOFF — TIKTOK CHAT STUDIO v2.5 Pro

> **File này dùng để chuyển giao cho AI tiếp theo (Gemini/Claude/GPT).**  
> Đọc file này = hiểu toàn bộ dự án + biết chính xác phải làm gì tiếp.  
> Cập nhật lần cuối: 2026-08-07 14:59 (ICT)

---

## 1. DỰ ÁN LÀ GÌ?

**TikTok Chat Studio** — Web-app tạo video TikTok dạng đoạn chat hài hước mô phỏng Facebook Messenger.

**Quy trình sử dụng:**
1. Người dùng tạo nhân vật (Chủ tiệm tạp hóa + Khách hàng) với avatar riêng
2. Soạn kịch bản hội thoại (khách hỏi vấn đề sức khỏe → shop tư vấn → chèn Product Card → chốt đơn)
3. Nhấn Play → Hệ thống tự động diễn kịch với hiệu ứng âm thanh + lồng tiếng
4. Nhấn Ghi Hình → Xuất file video `.webm` tải về máy → Đăng TikTok

**Mục tiêu kinh doanh:** Tạo video quảng cáo sản phẩm sức khỏe trên TikTok Shop một cách nhanh chóng, không cần quay phim thủ công.

---

## 2. CẤU TRÚC FILE HIỆN TẠI

```
d:/LISP CAD/TEST/MAKE DEFFIRENT/
├── index.html       (24 KB)  — Giao diện chính, bố cục 3 cột
├── style.css        (32 KB)  — Toàn bộ CSS + Visual Effects
├── app.js           (45 KB)  — Logic chính: nhân vật, kịch bản, audio, phát demo
├── db.js            (7.5 KB) — [MỚI] IndexedDB storage thay localStorage
├── recorder.js      (8.4 KB) — [MỚI] Ghi hình thật qua MediaRecorder
├── README.md        (15 KB)  — Tài liệu kỹ thuật chi tiết
├── LOGO.png         (139 KB) — Logo shop (đã nén)
└── assets/
    ├── owner_avatar.png     (162 KB) — Avatar mặc định Chủ Tiệm
    ├── customer_avatar.png  (147 KB) — Avatar mặc định Khách
    └── vitamin_c.png        (152 KB) — Ảnh sản phẩm mẫu
```

**Lưu ý quan trọng:**
- File `KIEN_TRUC_VA_KE_HOACH_DEPLOY.md` là tài liệu cũ, có thể xóa
- KHÔNG CÒN file `gemini-code-*.html` hay `gemini-code-*.css` (đã xóa, dồn vào `index.html` + `style.css`)
- CSS được nạp đơn giản qua `<link href="style.css">`
- JS load theo thứ tự: `db.js` → `recorder.js` → `app.js`
- CDN duy nhất: `html-to-image` (v1.11.11) cho chức năng ghi hình

---

## 3. KIẾN TRÚC KỸ THUẬT

### 3.1 Giao diện — 3 cột

| Cột Trái | Cột Giữa | Cột Phải |
|---|---|---|
| 4 tab: Kịch bản, Nhân vật, Soạn lời, JSON | Màn hình iPhone 9:16 giả lập FB Messenger | Điều khiển: Phát, Reset, TTS, SFX, Ghi hình |

### 3.2 Lưu trữ — Dual-Write Strategy

```
app.js saveCharactersToStorage()
  ├── IndexedDB (primary, không giới hạn) — qua db.js
  └── localStorage (fallback, giới hạn 5MB) — cho tương thích ngược
```

Khi khởi tạo: `DOMContentLoaded` → `migrateFromLocalStorage()` → nạp từ IndexedDB → render

### 3.3 Ghi hình — recorder.js

```
.phone-frame (DOM) → html-to-image.toPng() → Canvas 540x960 (15fps)
                                                    ↓
                                            captureStream(30)
                                                    ↓
                                     MediaRecorder → Blob → download .webm
```

### 3.4 Âm thanh — Hai tầng

1. **SFX (Web Audio API):** `playSFX('ting'|'pop'|'special')` — oscillator tổng hợp
2. **TTS (speechSynthesis):** `speakText(text, pitch, callback)` — giọng offline

### 3.5 Dữ liệu kịch bản — JSON structure

```json
{
  "title": "Tên kịch bản",
  "ownerCharId": "char_owner_coba",
  "customerCharId": "char_cust_sieuhai",
  "messages": [
    { "id": "msg_1", "sender": "customer|owner", "type": "text|product_card|like_sticker",
      "content": "Nội dung", "delay": 1400, "sfx": "ting|pop|special",
      "price": "99.000₫", "discount": "-20%", "image": "assets/vitamin_c.png" }
  ]
}
```

---

## 4. TRẠNG THÁI HIỆN TẠI — CÁI GÌ XONG, CÁI GÌ CHƯA

### ✅ ĐÃ HOÀN THÀNH
- [x] Giao diện Messenger chuẩn FB iOS (no-bezel, tỉ lệ 19.5:9)
- [x] CRUD nhân vật đầy đủ (Tạo/Sửa/Xóa, upload avatar, nén ảnh tự động)
- [x] Soạn kịch bản trực quan (timeline builder, 3 loại tin nhắn)
- [x] Phát demo tự động (auto play + typing indicator + seen status)
- [x] SFX Ting/Pop qua Web Audio API
- [x] TTS lồng tiếng cơ bản (speechSynthesis)
- [x] IndexedDB storage thay localStorage (module db.js)
- [x] Recording engine (module recorder.js) — code đã viết
- [x] Visual effects CSS (zoom-in, shake, glow, recording pulse)
- [x] Nén ảnh assets (giảm tổng 7.2MB → 0.6MB)
- [x] Dọn file trùng lặp

### ⚠️ CẦN TEST & DEBUG
- [ ] **Test ghi hình thực tế**: Mở `index.html` trên Chrome → nhấn 🎬 Ghi Hình → phát demo → dừng → kiểm tra file `.webm` có tải về không, có hình không
- [ ] **Test IndexedDB**: Tạo 5+ nhân vật với avatar ảnh thật → reload trang → dữ liệu phải còn nguyên
- [ ] **Test visual effects**: Các animation zoom/shake/glow có hiển thị đúng trong video ghi lại không

### ❌ CHƯA LÀM — LỘ TRÌNH TIẾP THEO (3 Giai đoạn)

Sắp theo thứ tự ưu tiên kinh doanh:

---

## 5. GIAI ĐOẠN TIẾP THEO — CHI TIẾT KỸ THUẬT

### 🔴 GĐ1: Debug & Hoàn thiện Recording Engine (ƯU TIÊN CAO NHẤT)

**Vấn đề có thể gặp khi test:**

1. **html-to-image CDN không load** (nếu mở file HTML trực tiếp bằng `file://` protocol):
   - Giải pháp: Chạy local server (`python -m http.server 8000` hoặc dùng Live Server extension)
   - Hoặc tải `html-to-image.min.js` về thư mục assets/ và link local

2. **CORS/tainted canvas lỗi** khi chụp ảnh chứa avatar base64:
   - Kiểm tra `recorder.js` dòng `htmlToImage.toPng()` options: thêm `useCORS: true`

3. **Video đen/trống** — do html-to-image chụp không kịp 15fps:
   - Giảm capture rate xuống 10fps (thay `66ms` → `100ms` trong `_startCaptureLoop`)
   - Hoặc tăng kích thước canvas xuống 360x640

4. **Audio không ghi được** — do AudioContext chưa resume:
   - Kiểm tra `initAudio()` được gọi trước `startRecording()`
   - Thêm `audioCtx.resume()` nếu state = suspended

**File cần sửa:** `recorder.js`, `app.js`

**Cách test:**
```
1. cd "d:/LISP CAD/TEST/MAKE DEFFIRENT"
2. python -m http.server 8000
3. Mở Chrome → http://localhost:8000
4. Nhấn 🎬 Ghi Hình → chờ kịch bản chạy xong → nhấn ⏹ Dừng
5. File .webm phải tự tải về
6. Mở file .webm kiểm tra hình ảnh + âm thanh
```

---

### 🟡 GĐ2: Giọng nói AI chất lượng cao (Edge TTS)

**Người dùng ĐÃ CÓ Python.** Phương án: Python local server + edge-tts package.

**Bước 1:** Cài đặt
```bash
pip install edge-tts flask flask-cors
```

**Bước 2:** Tạo file `tts_server.py`:
```python
from flask import Flask, request, send_file
from flask_cors import CORS
import edge_tts
import asyncio
import tempfile
import os

app = Flask(__name__)
CORS(app)

@app.route('/tts', methods=['POST'])
def text_to_speech():
    data = request.json
    text = data.get('text', '')
    voice = data.get('voice', 'vi-VN-HoaiMyNeural')
    # Giọng có sẵn: vi-VN-HoaiMyNeural (nữ), vi-VN-NamMinhNeural (nam)
    
    async def generate():
        communicate = edge_tts.Communicate(text, voice)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        await communicate.save(tmp.name)
        return tmp.name
    
    filepath = asyncio.run(generate())
    response = send_file(filepath, mimetype='audio/mpeg')
    
    @response.call_on_close
    def cleanup():
        os.unlink(filepath)
    
    return response

if __name__ == '__main__':
    app.run(port=5000, debug=True)
```

**Bước 3:** Sửa `app.js` hàm `speakText()`:
- Thay `speechSynthesis` bằng `fetch('http://localhost:5000/tts', { method: 'POST', body: JSON.stringify({text, voice}) })`
- Nhận file mp3 → tạo `Audio()` object → phát
- Fallback về `speechSynthesis` nếu server không chạy

**Bước 4:** Người dùng MUỐN import giọng tùy chỉnh (file .mp3/.wav tìm trên mạng):
- Thêm field "🎤 Tải file giọng mẫu" vào form nhân vật (tab Nhân vật)
- Lưu file audio vào IndexedDB (dùng `db.js` — dbPut với Blob)
- Khi phát, kiểm tra nhân vật có custom voice → phát file đó thay TTS

---

### 🟢 GĐ3: AI tự viết kịch bản (Gemini API)

**Người dùng chưa có API key** nhưng sẵn sàng tạo.

**Bước 1:** Hướng dẫn tạo key
- Truy cập https://aistudio.google.com
- Đăng nhập Google → Create API Key → Copy

**Bước 2:** Thêm UI vào tab Kịch bản (cột Trái):
```html
<div class="ai-generator">
    <input id="ai-topic" placeholder="Mô tả chủ đề video (VD: Khách bị rụng tóc, shop tư vấn dầu gội)">
    <input id="ai-api-key" type="password" placeholder="Dán API Key Gemini vào đây">
    <button onclick="generateWithAI()">✨ Tạo Kịch Bản Bằng AI</button>
</div>
```

**Bước 3:** Hàm `generateWithAI()` trong `app.js`:
```javascript
async function generateWithAI() {
    const topic = document.getElementById('ai-topic').value;
    const apiKey = document.getElementById('ai-api-key').value;
    
    const systemPrompt = `Bạn là biên kịch video TikTok hài hước cho tiệm tạp hóa bán sản phẩm sức khỏe.
Tạo kịch bản hội thoại Messenger gồm 5-7 tin nhắn giữa khách hàng (customer) và chủ tiệm (owner).
Cấu trúc: khách hỏi vấn đề → shop tư vấn → chèn product_card → khách chốt đơn → thả like.
Trả về ĐÚNG format JSON sau, KHÔNG kèm markdown:
{"title":"...","messages":[{"sender":"customer|owner","type":"text|product_card|like_sticker","content":"...","price":"...","discount":"...","delay":1500,"sfx":"ting|pop|special"}]}`;

    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            contents: [{ parts: [{ text: systemPrompt + '\n\nChủ đề: ' + topic }] }]
        })
    });
    
    const data = await response.json();
    const text = data.candidates[0].content.parts[0].text;
    const parsed = JSON.parse(text);
    // Nạp vào scenarios và render...
}
```

---

## 6. MỤC TIÊU DÀI HẠN CỦA NGƯỜI DÙNG

Người dùng đã chia sẻ các mục tiêu quan trọng:

1. **Chạy Online trên điện thoại** — Không muốn ôm máy tính. Mục tiêu cuối: deploy lên Vercel/Netlify, mở URL trên phone → tạo video ngay.

2. **Tạo hàng loạt nhân vật** với avatar khác nhau — Đây là lý do chuyển sang IndexedDB (không giới hạn dung lượng).

3. **Thêm hiệu ứng bắt mắt** trước khi đăng — Đã thêm CSS animations (zoom, shake, glow). Có thể mở rộng thêm: filter màu, text overlay, watermark.

4. **Import giọng nói tùy chỉnh** — Cop nhặt giọng hay trên mạng → tải lên app → dùng làm giọng cho nhân vật.

---

## 7. LƯU Ý KỸ THUẬT CHO AI TIẾP THEO

1. **KHÔNG tạo file mới trừ khi thật cần thiết.** Sửa trực tiếp `app.js`, `index.html`, `style.css`.

2. **Test bằng local server** vì `html-to-image` CDN sẽ bị block bởi CORS nếu mở bằng `file://`:
   ```
   cd "d:/LISP CAD/TEST/MAKE DEFFIRENT"
   python -m http.server 8000
   ```

3. **Người dùng giao tiếp bằng tiếng Việt.** Trả lời bằng tiếng Việt.

4. **Encoding:** Tất cả file dùng UTF-8. Tên biến/hàm trong code dùng tiếng Anh. Comment trong code dùng tiếng Việt.

5. **Không dùng framework** (no React, no Vue, no Tailwind). Vanilla HTML + CSS + JS thuần.

6. **Hàm quan trọng cần biết trong app.js:**
   - `saveOrUpdateCharacter()` — Lưu/cập nhật nhân vật
   - `renderCharacterRoster()` — Render danh sách nhân vật
   - `renderScriptBuilder()` — Render timeline lời thoại
   - `runScenario()` — Phát demo tự động
   - `resetChat()` — Reset khung chat
   - `simulateRecord()` — Bắt đầu/dừng ghi hình (gọi recorder.js)
   - `switchTab(name)` — Chuyển tab: 'cards', 'characters', 'builder', 'json'

7. **Hàm quan trọng trong db.js:**
   - `saveCharactersToIndexedDB(roster)` — Lưu mảng nhân vật
   - `loadCharactersFromIndexedDB()` — Đọc mảng nhân vật
   - `migrateFromLocalStorage()` — Chuyển dữ liệu cũ sang IndexedDB

8. **Hàm quan trọng trong recorder.js:**
   - `startRecording(targetElement, audioCtx)` — Bắt đầu ghi
   - `stopRecording()` — Dừng ghi + tự tải file
   - `isRecordingSupported()` — Kiểm tra trình duyệt hỗ trợ
   - `isCurrentlyRecording()` — Đang ghi hay không

---

## 8. THỨ TỰ ƯU TIÊN CHO PHIÊN LÀM VIỆC TIẾP THEO

```
1. Test Recording Engine → Debug nếu cần → Đảm bảo xuất được .webm thật
2. Tạo tts_server.py → Tích hợp Edge TTS vào app.js  
3. Thêm chức năng import giọng tùy chỉnh (.mp3/.wav)
4. Tích hợp Gemini API → AI tự viết kịch bản
5. Chuẩn bị deploy online (Vercel/Netlify) cho dùng trên điện thoại
```

---

*Tài liệu này được tạo bởi Claude Opus 4.6 — phiên 07/08/2026.*

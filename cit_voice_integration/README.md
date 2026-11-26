# Tích hợp thử nghiệm CIT Voice Studio (`cit_voice_integration`)

Thư mục này tách riêng hoàn toàn khỏi pipeline cũ để test **CIT Voice Studio (v1.0.7)** mà không ảnh hưởng code đang chạy.

## Cấu trúc thư mục
- `cit-voice-studio/` — Mã nguồn clone từ `Cuongyd196/cit-voice-studio` (môi trường ảo `.venv` riêng bằng `uv`, Python 3.12, giao diện web đã build sẵn).
- `cit_voice_client.py` — Client gọi REST API (`http://127.0.0.1:8001`), chỉ dùng thư viện chuẩn của Python.
- `audio_engine_cit.py` — Adapter tương thích với `synthesize_dual_gender()` trong `audio_engine_conbo.py` (xuất WAV 44.1kHz stereo đã `silenceremove` + `manifest.json`).
- `test_cit_integration.py` — Script chạy kiểm thử 5 bài test (health/voices, câu ngắn + thẻ cảm xúc `[cười]`/`[nghỉ]`, adapter dual-gender trích Tập 2 Hồ Cá Koi, xuất `.srt`, và hội thoại đa nhân vật).
- `start_cit_server.bat` — Khởi động nhanh server tại `http://127.0.0.1:8001`.
- `test_output/` — Các file audio/SRT sinh ra khi chạy test để bạn nghe trực tiếp.

## Cách dùng nhanh

### 1. Bật server CIT Voice Studio
Chạy `start_cit_server.bat` (hoặc trong PowerShell):
```powershell
cd cit_voice_integration\cit-voice-studio
uv run --no-sync vieneu-stream
```
Mở trình duyệt tại `http://127.0.0.1:8001` để dùng giao diện (đổi model sang **VieNeu-TTS v3 Turbo d3**, quản lý **Từ điển phát âm**, hoặc **Nhân bản giọng** trên waveform).

### 2. Chạy bài test tích hợp
```powershell
python cit_voice_integration\test_cit_integration.py
```

### 3. Bật tăng tốc GPU NVIDIA (tùy chọn — máy bạn có GTX 1660 6GB)
Mặc định đang cài bản nhẹ **CPU INT8 ONNX** (không cần PyTorch). Nếu muốn thử GPU NVIDIA:
```powershell
cd cit_voice_integration\cit-voice-studio
uv sync --group gpu-app
```
(Sẽ tải thêm ~3.5 GB PyTorch CUDA 12.8; hoặc có thể bấm trực tiếp **Cài hỗ trợ GPU** trong mục Cài đặt của giao diện web).

### 4. Cách gắn vào pipeline render chính (khi thấy ổn)
Trong script render (ví dụ `render_ho_ca_koi_pro.py`), chỉ cần đổi từ `synthesize_dual_gender` sang:
```python
import sys
sys.path.insert(0, "cit_voice_integration")
from audio_engine_cit import synthesize_dual_gender_cit

manifest = synthesize_dual_gender_cit(
    items=SCRIPT_ITEMS,
    out_dir=OUT_DIR,
    male_voice="Adam bựa",
    female_voice="Trúc Ly",
    male_speed=1.10,
    female_speed=1.08,
)
```

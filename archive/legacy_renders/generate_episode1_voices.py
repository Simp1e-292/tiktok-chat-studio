import os
import json
import subprocess
from pathlib import Path
from elevenlabs.client import ElevenLabs

# Đọc API Key từ .env hoặc biến môi trường
def get_api_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if key:
        return key
    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("ELEVENLABS_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise ValueError("Không tìm thấy ELEVENLABS_API_KEY trong .env hoặc biến môi trường!")

key = get_api_key()
client = ElevenLabs(api_key=key)

VOICE_MAP = {
    "char_tien_hai": {"name": "Callum", "id": "N2lVS1w4EtoT3dr4eOWO"},
    "char_truong":   {"name": "Adam",   "id": "pNInz6obpgDQGcFmaJgB"},
    "char_tung_anh": {"name": "Charlie","id": "IKne3meq5aSn9XLyUdCD"},
    "char_tung_em":  {"name": "Antoni", "id": "ErXwobaYiN019PkySvjV"},
    "char_trang":    {"name": "Lily",   "id": "pFZP5JQG7iQjIQuC4Bku"},
    "char_nga_tk":   {"name": "Jessica","id": "cgSgspJ2msm6clMCkdW9"},
    "char_thanh_hai":{"name": "Matilda","id": "XrExE9yKIg1WjnnlVkGX"},
    "char_minh_cham":{"name": "Bella",  "id": "EXAVITQu4vr4xnSDxMaL"},
    "char_kim":      {"name": "Laura",  "id": "FGY2WhTYpPnrIDTdsKH5"},
}

# 13 tin nhắn từ KICH_BAN_01_CUA_KHAC_TEN_CRUSH.md
MESSAGES = [
    {
        "id": "m1",
        "senderId": "char_tien_hai",
        "senderName": "Tiến Hải (CSKH)",
        "content": "Toang rồi! Khách Ecopark gọi, cửa vừa lắp có khắc chữ TÙNG ❤ TRANG to đùng!",
        "tts": "Toang rồi! Khách Ecopark gọi, cửa vừa lắp có khắc chữ Tùng tim Trang to đùng!",
        "sfx": "pop"
    },
    {
        "id": "m2",
        "senderId": "char_truong",
        "senderName": "Trưởng (Thiết kế)",
        "content": "Bản vẽ của ai? Tùng anh hay Tùng em, khai mau!",
        "tts": "Bản vẽ của ai? Tùng anh hay Tùng em, khai mau!",
        "sfx": "ting"
    },
    {
        "id": "m3",
        "senderId": "char_tung_anh",
        "senderName": "Tùng anh (Thiết kế)",
        "content": "Em có vợ con rồi nhé, đừng ai nhìn em! 🙏",
        "tts": "Em có vợ con rồi nhé, đừng ai nhìn em!",
        "sfx": "ting"
    },
    {
        "id": "m4",
        "senderId": "char_tung_em",
        "senderName": "Tùng em (Thiết kế)",
        "content": "Dạ… em vẽ làm quà sinh nhật, lỡ gửi nhầm file xuống xưởng ạ 😭",
        "tts": "Dạ… em vẽ làm quà sinh nhật, lỡ gửi nhầm file xuống xưởng ạ.",
        "sfx": "ting"
    },
    {
        "id": "m5",
        "senderId": "char_trang",
        "senderName": "Trang (CSKH)",
        "content": "Khoan… Trang nào? Trang chăm sóc khách hàng này á?! 😳",
        "tts": "Khoan… Trang nào? Trang chăm sóc khách hàng này á?!",
        "sfx": "pop"
    },
    {
        "id": "m6",
        "senderId": "char_nga_tk",
        "senderName": "Nga (Thiết kế)",
        "content": "Cả phòng thiết kế biết từ năm ngoái rồi, mỗi chị Trang không biết 🙂",
        "tts": "Cả phòng thiết kế biết từ năm ngoái rồi, mỗi chị Trang không biết.",
        "sfx": "ting"
    },
    {
        "id": "m7",
        "senderId": "char_thanh_hai",
        "senderName": "Thanh Hải (Kế toán)",
        "content": "Cánh cửa 18 triệu. Chị trừ dần vào lương Tùng em nhé!",
        "tts": "Cánh cửa mười tám triệu. Chị trừ dần vào lương Tùng em nhé!",
        "sfx": "ting"
    },
    {
        "id": "m8",
        "senderId": "char_minh_cham",
        "senderName": "Minh Châm (Mua hàng)",
        "content": "Mua hàng báo: phôi cánh đó hết rồi, đặt lại mất 2 tuần!",
        "tts": "Mua hàng báo: phôi cánh đó hết rồi, đặt lại mất hai tuần!",
        "sfx": "ting"
    },
    {
        "id": "m9",
        "senderId": "char_tien_hai",
        "senderName": "Tiến Hải (CSKH)",
        "content": "KHOAN!!! Khách gọi lại! Chồng chị ấy tên Tùng, chị tên Trang, đúng kỷ niệm 10 năm cưới, chị khóc luôn!",
        "tts": "Khoan! Khách gọi lại! Chồng chị ấy tên Tùng, chị tên Trang, đúng kỷ niệm mười năm cưới, chị khóc luôn!",
        "sfx": "special"
    },
    {
        "id": "m10",
        "senderId": "char_tien_hai",
        "senderName": "Tiến Hải (CSKH)",
        "content": "Chốt thêm 2 bộ cho nhà nội nhà ngoại, khắc y chang!",
        "tts": "Chốt thêm hai bộ cho nhà nội nhà ngoại, khắc y chang!",
        "sfx": "pop"
    },
    {
        "id": "m11",
        "senderId": "char_thanh_hai",
        "senderName": "Thanh Hải (Kế toán)",
        "content": "…Thôi, không trừ lương nữa. Thưởng nóng!",
        "tts": "…Thôi, không trừ lương nữa. Thưởng nóng!",
        "sfx": "ting"
    },
    {
        "id": "m12",
        "senderId": "char_trang",
        "senderName": "Trang (CSKH)",
        "content": "Thế… quà sinh nhật của em đâu? 🙈",
        "tts": "Thế… quà sinh nhật của em đâu?",
        "sfx": "pop"
    },
    {
        "id": "m13",
        "senderId": "char_kim",
        "senderName": "Kim (Nhân sự)",
        "content": "Thứ Bảy em mang cà phê Buôn Ma Thuột lên, mừng cặp đôi đầu tiên của công ty! ☕💘",
        "tts": "Thứ Bảy em mang cà phê Buôn Ma Thuột lên, mừng cặp đôi đầu tiên của công ty!",
        "sfx": "ting"
    }
]

if __name__ == "__main__":
    out_dir = Path("d:/LISP CAD/TEST/MAKE DEFFIRENT/thuong mai dien tu/elevenlabs_episode1_voices")
    out_dir.mkdir(parents=True, exist_ok=True)

    total_dur = 0.0
    print("=== BẮT ĐẦU TỔNG HỢP 13 GIỌNG ĐỌC ELEVENLABS CHO TẬP 1 ===")

    for i, msg in enumerate(MESSAGES, start=1):
        speaker_info = VOICE_MAP[msg["senderId"]]
        voice_name = speaker_info["name"]
        voice_id = speaker_info["id"]
        text = msg["tts"]
        out_file = out_dir / f"voice_{i:02d}_{msg['senderId']}_{voice_name}.mp3"
        
        print(f"[{i:02d}/13] {msg['senderName']} ({voice_name}): \"{text[:35]}...\"")
        
        try:
            audio = client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_multilingual_v2"
            )
            with open(out_file, "wb") as f:
                for chunk in audio:
                    f.write(chunk)
            
            # probe duration
            cmd = [
                r"C:\Users\KhunG LonG\AppData\Local\CapCut\Apps\9.7.1.4203\ffprobe.exe",
                "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(out_file)
            ]
            dur = float(subprocess.check_output(cmd).decode().strip())
            total_dur += dur
            msg["audio_file"] = out_file.name
            msg["duration_sec"] = dur
            print(f"   -> OK: {dur:.2f}s ({out_file.stat().st_size} bytes)")
        except Exception as e:
            print(f"   -> LỖI: {e}")

    print(f"\n HOÀN TẤT! Tổng thời lượng 13 câu thoại: {total_dur:.2f} giây")
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(MESSAGES, f, ensure_ascii=False, indent=2)

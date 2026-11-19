#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tổng hợp 13 giọng đọc thuần Việt cho Tập 1 ("Cánh Cửa Khắc Tên Crush") bằng VieNeu-TTS
- 100% giọng người Việt Bắc/Trung tự nhiên, có dấu chuẩn xác, miễn phí offline không giới hạn ký tự
- Lưu ra MP3 + manifest.json trong vieneu_episode1_voices/
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from vieneu import Vieneu


def _setup_ffmpeg():
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    local_apps = Path(os.path.expandvars(r"%LOCALAPPDATA%\CapCut\Apps"))
    if local_apps.is_dir():
        for exe in sorted(local_apps.rglob("ffmpeg.exe"), reverse=True):
            tool_dir = str(exe.parent)
            if tool_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = tool_dir + os.pathsep + os.environ.get("PATH", "")
            break


_setup_ffmpeg()

VOICE_MAP = {
    "char_tien_hai":  "Adam bựa",     # Nam · Bắc · Tự nhiên (bắt đầu & cao trào cực cuốn)
    "char_truong":    "Thiện Minh",   # Nam · Bắc · Nghiêm nghị
    "char_tung_anh":  "Phạm Tuyên",   # Nam · Bắc · Tự nhiên
    "char_tung_em":   "Hải Đăng",     # Nam · Bắc · Trẻ trung
    "char_trang":     "Ngọc Huyền",   # Nữ · Bắc · Tự nhiên nhẹ nhàng
    "char_nga_tk":    "Trúc Ly",      # Nữ · Bắc · Tinh nghịch
    "char_thanh_hai": "Đoan Trang",   # Nữ · Bắc · Sắc sảo
    "char_minh_cham": "Ngọc Linh",    # Nữ · Bắc · Dứt khoát
    "char_kim":       "Ngọc Trân",    # Nữ · Trung · Duyên dáng (Kim Đắk Lắk)
}

MESSAGES = [
    {
        "id": "m1",
        "type": "text",
        "senderId": "char_tien_hai",
        "senderName": "Tiến Hải (CSKH)",
        "content": "Toang rồi! Khách Ecopark gọi, cửa vừa lắp có khắc chữ TÙNG ❤ TRANG to đùng!",
        "tts": "Toang rồi! Khách Ecopark gọi, cửa vừa lắp có khắc chữ Tùng tim Trang to đùng!",
        "sfx": "pop"
    },
    {
        "id": "m2",
        "type": "text",
        "senderId": "char_truong",
        "senderName": "Trưởng (Thiết kế)",
        "content": "Bản vẽ của ai? Tùng anh hay Tùng em, khai mau!",
        "tts": "Bản vẽ của ai? Tùng anh hay Tùng em, khai mau!",
        "sfx": "ting"
    },
    {
        "id": "m3",
        "type": "text",
        "senderId": "char_tung_anh",
        "senderName": "Tùng anh (Thiết kế)",
        "content": "Em có vợ con rồi nhé, đừng ai nhìn em! 🙏",
        "tts": "Em có vợ con rồi nhé, đừng ai nhìn em!",
        "sfx": "ting"
    },
    {
        "id": "m4",
        "type": "text",
        "senderId": "char_tung_em",
        "senderName": "Tùng em (Thiết kế)",
        "content": "Dạ… em vẽ làm quà sinh nhật, lỡ gửi nhầm file xuống xưởng ạ 😭",
        "tts": "Dạ, em vẽ làm quà sinh nhật, lỡ gửi nhầm phai xuống xưởng ạ.",
        "sfx": "ting"
    },
    {
        "id": "m5",
        "type": "text",
        "senderId": "char_trang",
        "senderName": "Trang (CSKH)",
        "content": "Khoan… Trang nào? Trang chăm sóc khách hàng này á?! 😳",
        "tts": "Khoan, Trang nào? Trang chăm sóc khách hàng này á?!",
        "sfx": "pop"
    },
    {
        "id": "m6",
        "type": "text",
        "senderId": "char_nga_tk",
        "senderName": "Nga (Thiết kế)",
        "content": "Cả phòng thiết kế biết từ năm ngoái rồi, mỗi chị Trang không biết 🙂",
        "tts": "Cả phòng thiết kế biết từ năm ngoái rồi, mỗi chị Trang không biết.",
        "sfx": "ting"
    },
    {
        "id": "m7",
        "type": "text",
        "senderId": "char_thanh_hai",
        "senderName": "Thanh Hải (Kế toán)",
        "content": "Cánh cửa 18 triệu. Chị trừ dần vào lương Tùng em nhé!",
        "tts": "Cánh cửa mười tám triệu. Chị trừ dần vào lương Tùng em nhé!",
        "sfx": "ting"
    },
    {
        "id": "m8",
        "type": "text",
        "senderId": "char_minh_cham",
        "senderName": "Minh Châm (Mua hàng)",
        "content": "Mua hàng báo: phôi cánh đó hết rồi, đặt lại mất 2 tuần!",
        "tts": "Mua hàng báo: phôi cánh đó hết rồi, đặt lại mất hai tuần!",
        "sfx": "ting"
    },
    {
        "id": "m9",
        "type": "text",
        "senderId": "char_tien_hai",
        "senderName": "Tiến Hải (CSKH)",
        "content": "KHOAN!!! Khách gọi lại! Chồng chị ấy tên Tùng, chị tên Trang, đúng kỷ niệm 10 năm cưới, chị khóc luôn!",
        "tts": "Khoan! Khách gọi lại! Chồng chị ấy tên Tùng, chị tên Trang, đúng kỷ niệm mười năm cưới, chị khóc luôn!",
        "sfx": "special"
    },
    {
        "id": "m10",
        "type": "text",
        "senderId": "char_tien_hai",
        "senderName": "Tiến Hải (CSKH)",
        "content": "Chốt thêm 2 bộ cho nhà nội nhà ngoại, khắc y chang!",
        "tts": "Chốt thêm hai bộ cho nhà nội nhà ngoại, khắc y chang!",
        "sfx": "pop"
    },
    {
        "id": "m11",
        "type": "text",
        "senderId": "char_thanh_hai",
        "senderName": "Thanh Hải (Kế toán)",
        "content": "…Thôi, không trừ lương nữa. Thưởng nóng!",
        "tts": "Thôi, không trừ lương nữa. Thưởng nóng!",
        "sfx": "ting"
    },
    {
        "id": "m12",
        "type": "text",
        "senderId": "char_trang",
        "senderName": "Trang (CSKH)",
        "content": "Thế… quà sinh nhật của em đâu? 🙈",
        "tts": "Thế, quà sinh nhật của em đâu?",
        "sfx": "pop"
    },
    {
        "id": "m13",
        "type": "text",
        "senderId": "char_kim",
        "senderName": "Kim (Nhân sự)",
        "content": "Thứ Bảy em mang cà phê Buôn Ma Thuột lên, mừng cặp đôi đầu tiên của công ty! ☕💘",
        "tts": "Thứ Bảy em mang cà phê Buôn Ma Thuột lên, mừng cặp đôi đầu tiên của công ty!",
        "sfx": "ting"
    }
]


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent / "vieneu_episode1_voices"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Xóa các file .mp3 lỗi bị cắt từ lần trước (nếu có)
    for old_mp3 in out_dir.glob("*.mp3"):
        old_mp3.unlink(missing_ok=True)

    print("=== KHỞI TẠO VIENEU-TTS (GIỌNG THUẦN VIỆT BẮC/TRUNG) ===")
    tts = Vieneu()
    total_dur = 0.0

    for i, msg in enumerate(MESSAGES, start=1):
        voice_name = VOICE_MAP[msg["senderId"]]
        wav_file = out_dir / f"voice_{i:02d}_{msg['senderId']}.wav"

        print(f"[{i:02d}/13] {msg['senderName']} -> [{voice_name}]: \"{msg['tts']}\"")
        audio = tts.infer(text=msg["tts"], voice=voice_name)
        tts.save(audio, str(wav_file))

        dur = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(wav_file)
        ]).decode().strip())
        total_dur += dur
        msg["audio_file"] = wav_file.name
        msg["voice_name"] = voice_name
        msg["duration_sec"] = dur
        print(f"   -> OK: {dur:.2f}s")

    print(f"\nHOÀN TẤT VIENEU-TTS! Tổng thời lượng 13 câu: {total_dur:.2f}s")
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(MESSAGES, f, ensure_ascii=False, indent=2)

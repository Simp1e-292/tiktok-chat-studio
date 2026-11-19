#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tổng hợp 14 giọng đọc thuần Việt cho Tập 1 v2 ("Quên tắt layer CAD khi xuất CNC") bằng VieNeu-TTS
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
    "char_tien_hai":  "Adam bựa",     # Nam · Bắc · Tự nhiên
    "char_truong":    "Thiện Minh",   # Nam · Bắc · Kể chuyện trầm
    "char_tung_anh":  "Phạm Tuyên",   # Nam · Bắc · Tự nhiên
    "char_tung_em":   "Hải Đăng",     # Nam · Bắc · Trẻ trung
    "char_trang":     "Ngọc Huyền",   # Nữ · Bắc · Nhẹ nhàng
    "char_nga_tk":    "Trúc Ly",      # Nữ · Bắc · Tinh nghịch
    "char_thanh_hai": "Đoan Trang",   # Nữ · Bắc · Sắc sảo
    "char_minh_cham": "Ngọc Linh",    # Nữ · Bắc · Dứt khoát
    "char_kim":       "Ngọc Trân",    # Nữ · Trung · Duyên dáng
}

MESSAGES = [
    {
        "id": "m1",
        "type": "text",
        "senderId": "char_tien_hai",
        "senderName": "Tiến Hải (CSKH)",
        "content": "Cấp báo ae ơi!! Xưởng vừa gửi ảnh nghiệm thu phôi cửa nhà anh Hùng Ecopark… ai xuất file CNC đấy?!",
        "tts": "Cấp báo anh em ơi! Xưởng vừa gửi ảnh nghiệm thu phôi cửa nhà anh Hùng Ê cô pác, ai xuất phai xi en xi đấy?!",
        "media": "assets/episode1_media/steel_door_4canh.jpg",
        "is_gif": False,
        "sfx": "assets/sfx_pack/windows-error.mp3"
    },
    {
        "id": "m2",
        "type": "text",
        "senderId": "char_truong",
        "senderName": "Trưởng (Thiết kế)",
        "content": "Ủa bình thường mà? Pano cửa 4 cánh vân gỗ đẹp thế kia còn kêu gì?",
        "tts": "Ủa bình thường mà? Pa nô cửa bốn cánh vân gỗ đẹp thế kia còn kêu gì?",
        "media": None,
        "is_gif": False,
        "sfx": "assets/sfx_pack/inception.mp3"
    },
    {
        "id": "m3",
        "type": "text",
        "senderId": "char_tien_hai",
        "senderName": "Tiến Hải (CSKH)",
        "content": "Anh zoom kỹ lên góc ô thoáng bên phải kìa!! Có dòng chữ \"Trang CSKH nhớ rep ib anh Tùng nhé ❤\" cắt laser nét căng luôn!!",
        "tts": "Anh dum kỹ lên góc ô thoáng bên phải kìa! Có dòng chữ Trang chăm sóc khách hàng nhớ rép in bốc anh Tùng nhé, cắt la de nét căng luôn!",
        "media": "assets/episode1_media/confused.gif",
        "is_gif": True,
        "sfx": "assets/sfx_pack/bruh.mp3"
    },
    {
        "id": "m4",
        "type": "text",
        "senderId": "char_tung_anh",
        "senderName": "Tùng anh (Thiết kế)",
        "content": "Khoan đã nhé! Tao có vợ 2 con rồi, ko liên quan gì tới vụ này đâu đấy!!",
        "tts": "Khoan đã nhé! Tao có vợ hai con rồi, không liên quan gì tới vụ này đâu đấy!",
        "media": None,
        "is_gif": False,
        "sfx": "assets/sfx_pack/huh.mp3"
    },
    {
        "id": "m5",
        "type": "text",
        "senderId": "char_tung_em",
        "senderName": "Tùng em (Thiết kế)",
        "content": "Chết cha em rồi… tối qua em vẽ test mẫu tặng sinh nhật, quên tắt layer ghi chú lúc xuất file cắt… 😭",
        "tts": "Chết cha em rồi, tối qua em vẽ tét mẫu tặng sinh nhật, quên tắt lây ơ ghi chú lúc xuất phai cắt.",
        "media": "assets/episode1_media/this_is_fine.gif",
        "is_gif": True,
        "sfx": "assets/sfx_ting.mp3"
    },
    {
        "id": "m6",
        "type": "text",
        "senderId": "char_trang",
        "senderName": "Trang (CSKH)",
        "content": "Ơ khoan… Trang CSKH là em á?! Sao anh vẽ cửa mà lại viết tên em lên đấy?! 😳",
        "tts": "Ơ khoan, Trang chăm sóc khách hàng là em á?! Sao anh vẽ cửa mà lại viết tên em lên đấy?!",
        "media": None,
        "is_gif": False,
        "sfx": "assets/sfx_pack/huh.mp3"
    },
    {
        "id": "m7",
        "type": "text",
        "senderId": "char_nga_tk",
        "senderName": "Nga (Thiết kế)",
        "content": "Cả phòng thiết kế biết ông Tùng em thích bà từ năm ngoái rồi, mỗi bà ngây thơ thôi 🙂",
        "tts": "Cả phòng thiết kế biết ông Tùng em thích bà từ năm ngoái rồi, mỗi bà ngây thơ thôi.",
        "media": "assets/episode1_media/shocked.gif",
        "is_gif": True,
        "sfx": "assets/sfx_pack/rimshot.mp3"
    },
    {
        "id": "m8",
        "type": "text",
        "senderId": "char_thanh_hai",
        "senderName": "Thanh Hải (Kế toán)",
        "content": "Thôi khỏi yêu đương! Phôi cửa thép 4 cánh 28 triệu, trừ thẳng vào lương Tùng em 6 tháng nhé!",
        "tts": "Thôi khỏi yêu đương! Phôi cửa thép bốn cánh hai mươi tám triệu, trừ thẳng vào lương Tùng em sáu tháng nhé!",
        "media": None,
        "is_gif": False,
        "sfx": "assets/sfx_ting.mp3"
    },
    {
        "id": "m9",
        "type": "text",
        "senderId": "char_minh_cham",
        "senderName": "Minh Châm (Mua hàng)",
        "content": "Mua hàng báo: tấm thép khổ lớn mã này vừa hết, đặt lại chờ 10 ngày, kịp giao ko?!",
        "tts": "Mua hàng báo: tấm thép khổ lớn mã này vừa hết, đặt lại chờ mười ngày, kịp giao không?!",
        "media": None,
        "is_gif": False,
        "sfx": "assets/sfx_pop.mp3"
    },
    {
        "id": "m10",
        "type": "text",
        "senderId": "char_tien_hai",
        "senderName": "Tiến Hải (CSKH)",
        "content": "KHOAN ĐÃ CẢ NHÀ!! Em vừa lỡ bấm nhầm gửi ảnh xưởng cho… chị vợ anh Hùng xem rồi!!",
        "tts": "Khoan đã cả nhà! Em vừa lỡ bấm nhầm gửi ảnh xưởng cho chị vợ anh Hùng xem rồi!",
        "media": None,
        "is_gif": False,
        "sfx": "assets/sfx_pack/ding.mp3"
    },
    {
        "id": "m11",
        "type": "text",
        "senderId": "char_truong",
        "senderName": "Trưởng (Thiết kế)",
        "content": "Mày toang hẳn luôn rồi Hải ơi! Khách chửi sao?!",
        "tts": "Mày toang hẳn luôn rồi Hải ơi! Khách chửi sao?!",
        "media": None,
        "is_gif": False,
        "sfx": "assets/sfx_pack/windows-error.mp3"
    },
    {
        "id": "m12",
        "type": "text",
        "senderId": "char_tien_hai",
        "senderName": "Tiến Hải (CSKH)",
        "content": "Chị ấy cười ngất bảo: dễ thương thế, tha cho thằng bé đi! Chị đặt luôn 3 bộ cửa phòng ngủ nữa, giảm giá nhẹ làm quà cưới 2 đứa!! 😂",
        "tts": "Chị ấy cười ngất bảo: dễ thương thế, tha cho thằng bé đi! Chị đặt luôn ba bộ cửa phòng ngủ nữa, giảm giá nhẹ làm quà cưới hai đứa!",
        "media": "assets/episode1_media/clap.gif",
        "is_gif": True,
        "sfx": "assets/sfx_pack/wow.mp3"
    },
    {
        "id": "m13",
        "type": "text",
        "senderId": "char_thanh_hai",
        "senderName": "Thanh Hải (Kế toán)",
        "content": "…Thôi xóa biên bản trừ lương! Cuối tuần nhớ mang thiệp hồng qua phòng Kế toán nhé!",
        "tts": "Thôi xóa biên bản trừ lương! Cuối tuần nhớ mang thiệp hồng qua phòng Kế toán nhé!",
        "media": None,
        "is_gif": False,
        "sfx": "assets/sfx_pop.mp3"
    },
    {
        "id": "m14",
        "type": "text",
        "senderId": "char_kim",
        "senderName": "Kim (Nhân sự)",
        "content": "Nhân sự tài trợ 10 cân cà phê Buôn Ma Thuột mời cả xưởng ăn mừng đôi mới công ty nha! ☕💘",
        "tts": "Nhân sự tài trợ mười cân cà phê Buôn Ma Thuột mời cả xưởng ăn mừng đôi mới công ty nha!",
        "media": None,
        "is_gif": False,
        "sfx": "assets/sfx_ting.mp3"
    }
]


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent / "vieneu_episode1_v2_voices"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== KHỞI TẠO VIENEU-TTS CHO TẬP 1 v2 (ĐỜI THẬT + GIF + SFX) ===")
    tts = Vieneu()
    total_dur = 0.0

    for i, msg in enumerate(MESSAGES, start=1):
        voice_name = VOICE_MAP[msg["senderId"]]
        wav_file = out_dir / f"voice_{i:02d}_{msg['senderId']}.wav"

        print(f"[{i:02d}/14] {msg['senderName']} -> [{voice_name}]")
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

    print(f"\nHOÀN TẤT VIENEU-TTS v2! Tổng thời lượng 14 câu: {total_dur:.2f}s")
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(MESSAGES, f, ensure_ascii=False, indent=2)

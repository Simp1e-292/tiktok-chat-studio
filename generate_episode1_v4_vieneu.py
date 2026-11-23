#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tổng hợp giọng đọc thuần Việt (VieNeu-TTS) cho Tập 1 v4 (POV Chủ máy Tùng em + Trưởng phòng TK)
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
    "TH": "Adam bựa",     # Tiến Hải (CSKH)
    "TG": "Ngọc Huyền",   # Trang (CSKH)
    "TE": "Hải Đăng",     # Tùng em (Thiết kế - POV Chủ máy bên phải)
    "TA": "Phạm Tuyên",   # Tùng anh (Xưởng)
    "TP": "Thiện Minh",   # Trưởng phòng TK
    "KT": "Đoan Trang",   # Thanh Hải (Kế toán)
    "KM": "Ngọc Trân",    # Kim (Nhân sự - Đắk Lắk)
}

ITEMS = [
    {"idx": 1,  "kind": "msg", "side": "left",  "code": "TH", "sender": "Tiến Hải (CSKH)",     "dept": "CSKH",     "color": "#2563eb", "text": "Alo cứu bồ gấp!! Em đang nhà anh Khánh nghiệm thu, sao 2 cánh cửa 2 hướng vân thế này?? 😭", "tts": "A lô cứu bồ gấp! Em đang nhà anh Khánh nghiệm thu, sao hai cánh cửa hai hướng vân thế này?", "img": "assets/ep1_v3/door_mismatch.png", "sfx": "assets/sfx_pack/windows-error.mp3", "typing": False},
    {"idx": 2,  "kind": "msg", "side": "left",  "code": "TG", "sender": "Trang (CSKH)",        "dept": "CSKH",     "color": "#db2777", "text": 'Ủa @Tùng em, hôm trước khách dặn làm cửa "độc bản" à??', "mention": "@Tùng em", "tts": "Ủa Tùng em, hôm trước khách dặn làm cửa độc bản à?", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 3,  "kind": "msg", "side": "right", "code": "TE", "sender": "Tùng em (Thiết kế)",  "dept": "Thiết kế", "color": "#16a34a", "text": "Đừng đổ tôi bà ơi! File CAD xuất chuẩn đét, chắc ông xưởng dán phim lúc buồn ngủ r!", "tts": "Đừng đổ tôi bà ơi! Phai két xuất chuẩn đét, chắc ông xưởng dán phim lúc buồn ngủ rồi!", "sfx": "assets/sfx_pop.mp3", "typing": True},
    {"idx": 4,  "kind": "msg", "side": "left",  "code": "TA", "sender": "Tùng anh (Xưởng)",    "dept": "Xưởng",    "color": "#0d9488", "text": "Khoan nhé em trai! BV ko ghi hướng vân thì xưởng tự hiểu là làm cho nó khác bọt còn gì", "tts": "Khoan nhé em trai! Bản vẽ không ghi hướng vân thì xưởng tự hiểu là làm cho nó khác bọt còn gì.", "sfx": "assets/sfx_pack/huh.mp3", "typing": True},
    {"idx": 5,  "kind": "msg", "side": "left",  "code": "TG", "sender": "Trang (CSKH)",        "dept": "CSKH",     "color": "#db2777", "text": 'Anh Khánh nhắn đúng câu "làm cho nó sang" thôi, ai bảo khác bọt đâu anh 💀', "tts": "Anh Khánh nhắn đúng câu làm cho nó sang thôi, ai bảo khác bọt đâu anh.", "img": "assets/ep1_v3/msg_khach_sang.png", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 6,  "kind": "msg", "side": "left",  "code": "TA", "sender": "Tùng anh (Xưởng)",    "dept": "Xưởng",    "color": "#0d9488", "text": "Thì vân ngang nhìn nhà nó rộng, chả sang là gì!", "tts": "Thì vân ngang nhìn nhà nó rộng, chả sang là gì!", "meme_gif": "assets/episode1_media/confused.gif", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 7,  "kind": "msg", "side": "right", "code": "TE", "sender": "Tùng em (Thiết kế)",  "dept": "Thiết kế", "color": "#16a34a", "text": "Vân DỌC mới tôn trần cao anh ơi, nhà này trần thấp tè!", "tts": "Vân dọc mới tôn trần cao anh ơi, nhà này trần thấp tè!", "sfx": "assets/sfx_pop.mp3", "typing": True},
    {"idx": 8,  "kind": "msg", "side": "left",  "code": "TH", "sender": "Tiến Hải (CSKH)",     "dept": "CSKH",     "color": "#2563eb", "text": "Hai ông im hộ tôi cái… anh Khánh đang đứng sau lưng đọc chung nhóm chat này luôn ạ 🥲", "tts": "Hai ông im hộ tôi cái, anh Khánh đang đứng sau lưng đọc chung nhóm chát này luôn ạ.", "meme_gif": "assets/episode1_media/this_is_fine.gif", "sfx": "assets/sfx_pack/bruh.mp3", "typing": False},
    {"idx": 9,  "kind": "msg", "side": "left",  "code": "TP", "sender": "Trưởng phòng TK",     "dept": "Thiết kế", "color": "#1e3a8a", "text": "Ai duyệt cái bản vẽ này?", "tts": "Ai duyệt cái bản vẽ này?", "seen": "Đã xem 9 người", "extra_pause": 1.1, "sfx": "assets/sfx_pack/inception.mp3", "typing": False},
    {"idx": 10, "kind": "msg", "side": "right", "code": "TE", "sender": "Tùng em (Thiết kế)",  "dept": "Thiết kế", "color": "#16a34a", "text": "Dạ anh duyệt sáng thứ 3 lúc đang uống trà đá ngoài cổng ạ", "tts": "Dạ anh duyệt sáng thứ ba lúc đang uống trà đá ngoài cổng ạ.", "img": "assets/ep1_v3/msg_truong_ok.png", "sfx": "assets/sfx_pack/rimshot.mp3", "typing": True},
    {"idx": 11, "kind": "msg", "side": "left",  "code": "TP", "sender": "Trưởng phòng TK",     "dept": "Thiết kế", "color": "#1e3a8a", "text": "Chắc do thằng Hải chụp ngược sáng nhìn lú đấy, anh về trước đây", "tts": "Chắc do thằng Hải chụp ngược sáng nhìn lú đấy, anh về trước đây.", "sfx": "assets/sfx_ting.mp3", "typing": False, "recall_id": "msg_11"},
    {"idx": 12, "kind": "sys_recall", "target_id": "msg_11", "text": "Trưởng phòng TK đã thu hồi một tin nhắn", "sfx": "assets/sfx_pack/metal_boom.mp3", "hold": 1.4},
    {"idx": 13, "kind": "msg", "side": "left",  "code": "KT", "sender": "Thanh Hải (Kế toán)", "dept": "Kế toán",  "color": "#ea580c", "text": "Chụp màn hình kịp rồi nha anh Trưởng phòng 🙂 Mà 40% tiền cọc cuối anh Khánh chuyển chưa đấy Hải?", "tts": "Chụp màn hình kịp rồi nha anh Trưởng phòng. Mà bốn mươi phần trăm tiền cọc cuối anh Khánh chuyển chưa đấy Hải?", "img": "assets/ep1_v3/msg_thuhoi_capture.png", "meme_gif": "assets/episode1_media/shocked.gif", "sfx": "assets/sfx_pack/ding.mp3", "typing": False},
    {"idx": 14, "kind": "msg", "side": "left",  "code": "TH", "sender": "Tiến Hải (CSKH)",     "dept": "CSKH",     "color": "#2563eb", "text": "KHOAN CẢ NHÀ!! Em vừa định xin lỗi, thì anh Khánh bảo… ko bắt đền nữa!", "tts": "Khoan cả nhà! Em vừa định xin lỗi, thì anh Khánh bảo, không bắt đền nữa!", "sfx": "assets/sfx_pop.mp3", "typing": True},
    {"idx": 15, "kind": "msg", "side": "left",  "code": "TA", "sender": "Tùng anh (Xưởng)",    "dept": "Xưởng",    "color": "#0d9488", "text": "Thật á?! Thế bảo anh về đón con đây!", "tts": "Thật á? Thế bảo anh về đón con đây!", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 16, "kind": "msg", "side": "left",  "code": "TH", "sender": "Tiến Hải (CSKH)",     "dept": "CSKH",     "color": "#2563eb", "text": "Nhưng ổng bảo giữ nguyên cửa, điều kiện là… tối nay em Trang CSKH phải qua gặp riêng ổng nói chuyện mới chịu ký nghiệm thu 😳", "tts": "Nhưng ổng bảo giữ nguyên cửa, điều kiện là tối nay em Trang chăm sóc khách hàng phải qua gặp riêng ổng nói chuyện mới chịu ký nghiệm thu.", "sfx": "assets/sfx_pack/huh.mp3", "typing": True},
    {"idx": 17, "kind": "msg", "side": "right", "code": "TE", "sender": "Tùng em (Thiết kế)",  "dept": "Thiết kế", "color": "#16a34a", "text": "CÁI GÌ CƠ?! Gặp Trang làm gì?? Anh Hải giữ chân ổng lại, em phi xe sang ngay bây giờ!!", "tts": "Cái gì cơ?! Gặp Trang làm gì? Anh Hải giữ chân ổng lại, em phi xe sang ngay bây giờ!", "sfx": "assets/sfx_pack/windows-error.mp3", "typing": True},
    {"idx": 18, "kind": "msg", "side": "left",  "code": "KM", "sender": "Kim (Nhân sự)",       "dept": "Nhân sự",  "color": "#92400e", "text": "Thứ 7 mai lên văn phòng sớm hóng nha cả nhà, Nhân sự bao cà phê Đắk Lắk ☕🔥", "tts": "Thứ bảy mai lên văn phòng sớm hóng nha cả nhà, Nhân sự bao cà phê Đắc Lắc!", "seen": "Đã xem 12 người", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 19, "kind": "end_card", "text": "Anh Khánh đòi gặp Trang làm gì? Chờ Tập 2 tối mai 👀", "sfx": "assets/sfx_pack/wow.mp3", "meme_gif": "assets/episode1_media/clap.gif", "hold": 3.0},
]


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent / "vieneu_episode1_v4_voices"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== TẠO GIỌNG ĐỌC VIENEU-TTS CHO TẬP 1 v4 (POV CHỦ MÁY + TRƯỞNG PHÒNG TK) ===")
    tts = Vieneu()
    total_speech = 0.0

    for it in ITEMS:
        if it["kind"] != "msg":
            continue
        voice_name = VOICE_MAP[it["code"]]
        raw_wav = out_dir / f"raw_{it['idx']:02d}.wav"
        fit_wav = out_dir / f"voice_{it['idx']:02d}_{it['code']}.wav"

        audio = tts.infer(text=it["tts"], voice=voice_name)
        tts.save(audio, str(raw_wav))
        dur = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(raw_wav)
        ]).decode().strip())

        # Cho thoại nhanh gọn tự nhiên 1.08x nhẹ ở các câu quá 3.5s để tổng thời lượng cân đối ~55-60s
        if dur > 4.2:
            spd = min(1.18, dur / 3.8)
            subprocess.run([
                "ffmpeg", "-y", "-i", str(raw_wav),
                "-af", f"atempo={spd:.3f}",
                str(fit_wav)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            final_dur = float(subprocess.check_output([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(fit_wav)
            ]).decode().strip())
        else:
            shutil.copy2(raw_wav, fit_wav)
            final_dur = dur

        raw_wav.unlink(missing_ok=True)
        it["audio_file"] = fit_wav.name
        it["voice_name"] = voice_name
        it["duration_sec"] = final_dur
        total_speech += final_dur
        print(f"[{it['idx']:02d}] ({it['side']:5s}) {it['sender']:20s} -> {final_dur:.2f}s")

    print(f"Tổng thời lượng thoại thuần: {total_speech:.2f}s")
    (out_dir / "manifest.json").write_text(json.dumps(ITEMS, ensure_ascii=False, indent=2), encoding="utf-8")

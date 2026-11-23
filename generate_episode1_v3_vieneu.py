#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tổng hợp giọng đọc thuần Việt (VieNeu-TTS) cho Video Test v3 ("2 cánh 2 hướng vân")
- Giữ NGUYÊN 100% văn bản hiển thị trong brief (ko, r, BV, DỌC...)
- TTS đọc tròn chữ tự nhiên theo ngữ cảnh công sở
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
    "TH": "Adam bựa",     # Tiến Hải (CSKH) - Nam
    "TG": "Ngọc Huyền",   # Trang (CSKH) - Nữ
    "TE": "Hải Đăng",     # Tùng em (Thiết kế) - Nam trẻ
    "TA": "Phạm Tuyên",   # Tùng anh (Xưởng) - Nam cứng đầu
    "TR": "Thiện Minh",   # Trưởng (Thiết kế) - Nam trầm
    "KT": "Đoan Trang",   # Thanh Hải (Kế toán) - Nữ lạnh lùng
}

# Đúng 20 mục theo thứ tự & timestamp trong brief (giữ nguyên text 100%)
ITEMS = [
    {"idx": 1,  "t": 0.0,  "kind": "msg", "code": "TH", "sender": "Tiến Hải (CSKH)",     "dept": "CSKH",     "color": "#2563eb", "text": "Anh chị ơi anh Khánh hỏi sao 2 cánh 2 loại vân 😐", "tts": "Anh chị ơi, anh Khánh hỏi sao hai cánh hai loại vân?", "img": "assets/ep1_v3/door_mismatch.png", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 2,  "t": 3.0,  "kind": "msg", "code": "TG", "sender": "Trang (CSKH)",        "dept": "CSKH",     "color": "#db2777", "text": "@Tùng em vân sao vậy", "mention": "@Tùng em", "tts": "Tùng em, vân sao vậy?", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 3,  "t": 5.5,  "kind": "msg", "code": "TE", "sender": "Tùng em (Thiết kế)",  "dept": "Thiết kế", "color": "#16a34a", "text": "BV em vẽ đúng, xưởng dán sai r", "tts": "Bản vẽ em vẽ đúng, xưởng dán sai rồi.", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 4,  "t": 8.0,  "kind": "msg", "code": "TA", "sender": "Tùng anh (Xưởng)",    "dept": "Xưởng",    "color": "#0d9488", "text": "BV ko ghi hướng vân thì xưởng biết đường nào", "tts": "Bản vẽ không ghi hướng vân thì xưởng biết đường nào.", "sfx": "assets/sfx_ting.mp3", "typing": True},
    {"idx": 5,  "t": 10.5, "kind": "msg", "code": "TG", "sender": "Trang (CSKH)",        "dept": "CSKH",     "color": "#db2777", "text": 'Anh Khánh chỉ nói "cho nó sang" thôi mà', "tts": "Anh Khánh chỉ nói cho nó sang thôi mà.", "img": "assets/ep1_v3/msg_khach_sang.png", "sfx": "assets/sfx_ting.mp3", "typing": True},
    {"idx": 6,  "t": 13.0, "kind": "msg", "code": "TA", "sender": "Tùng anh (Xưởng)",    "dept": "Xưởng",    "color": "#0d9488", "text": "Sang là vân ngang", "tts": "Sang là vân ngang.", "sfx": "assets/sfx_ting.mp3", "meme_gif": "assets/episode1_media/confused.gif", "meme_sfx": "assets/sfx_pack/huh.mp3", "typing": False},
    {"idx": 7,  "t": 15.5, "kind": "msg", "code": "TE", "sender": "Tùng em (Thiết kế)",  "dept": "Thiết kế", "color": "#16a34a", "text": "Sang là vân DỌC", "tts": "Sang là vân dọc!", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 8,  "t": 18.0, "kind": "msg", "code": "TH", "sender": "Tiến Hải (CSKH)",     "dept": "CSKH",     "color": "#2563eb", "text": "Anh Khánh đang đứng cạnh em ạ 🥲", "tts": "Anh Khánh đang đứng cạnh em ạ.", "sfx": "assets/sfx_pack/windows-error.mp3", "meme_gif": "assets/episode1_media/this_is_fine.gif", "typing": True},
    {"idx": 9,  "t": 20.5, "kind": "msg", "code": "TR", "sender": "Trưởng (Thiết kế)",   "dept": "Thiết kế", "color": "#1e3a8a", "text": "Ai duyệt bản vẽ này?", "tts": "Ai duyệt bản vẽ này?", "seen": "Đã xem 8 người", "sfx": "assets/sfx_pack/inception.mp3", "typing": False},
    {"idx": 10, "t": 23.5, "kind": "msg", "code": "TE", "sender": "Tùng em (Thiết kế)",  "dept": "Thiết kế", "color": "#16a34a", "text": "Dạ anh duyệt thứ 3 ạ", "tts": "Dạ anh duyệt thứ ba ạ.", "img": "assets/ep1_v3/msg_truong_ok.png", "sfx": "assets/sfx_pack/rimshot.mp3", "typing": False},
    {"idx": 11, "t": 26.0, "kind": "msg", "code": "TR", "sender": "Trưởng (Thiết kế)",   "dept": "Thiết kế", "color": "#1e3a8a", "text": "Lỗi này bộ phận nào tự xử nhé", "tts": "Lỗi này bộ phận nào tự xử nhé.", "sfx": "assets/sfx_ting.mp3", "typing": True, "recall_id": "msg_11"},
    {"idx": 12, "t": 28.0, "kind": "msg", "code": "TA", "sender": "Tùng anh (Xưởng)",    "dept": "Xưởng",    "color": "#0d9488", "text": "Anh 2 con đang đóng học phí nha 🥲", "tts": "Anh hai con đang đóng học phí nha.", "sfx": "assets/sfx_pack/bruh.mp3", "typing": True},
    {"idx": 13, "t": 30.0, "kind": "sys_recall", "target_id": "msg_11", "text": "Trưởng đã thu hồi một tin nhắn", "sfx": "assets/sfx_pack/metal_boom.mp3"},
    {"idx": 14, "t": 32.0, "kind": "msg", "code": "TG", "sender": "Trang (CSKH)",        "dept": "CSKH",     "color": "#db2777", "text": "Anh Trưởng vừa nhắn gì vậy ạ?", "tts": "Anh Trưởng vừa nhắn gì vậy ạ?", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 15, "t": 34.5, "kind": "msg", "code": "KT", "sender": "Thanh Hải (Kế toán)", "dept": "Kế toán",  "color": "#ea580c", "text": "Chụp rồi nè", "tts": "Chụp rồi nè.", "img": "assets/ep1_v3/msg_thuhoi_capture.png", "meme_gif": "assets/episode1_media/shocked.gif", "sfx": "assets/sfx_pack/ding.mp3", "typing": False},
    {"idx": 16, "t": 37.0, "kind": "msg", "code": "KT", "sender": "Thanh Hải (Kế toán)", "dept": "Kế toán",  "color": "#ea580c", "text": "Mà anh Khánh chuyển cọc chưa? Chưa thấy tiền", "tts": "Mà anh Khánh chuyển cọc chưa? Chưa thấy tiền.", "sfx": "assets/sfx_ting.mp3", "typing": True},
    {"idx": 17, "t": 39.5, "kind": "msg", "code": "TH", "sender": "Tiến Hải (CSKH)",     "dept": "CSKH",     "color": "#2563eb", "text": "Vậy giờ em nói gì với anh Khánh ạ?", "tts": "Vậy giờ em nói gì với anh Khánh ạ?", "seen": "Đã xem 11 người", "sfx": "assets/sfx_ting.mp3", "typing": True},
    {"idx": 18, "t": 43.0, "kind": "time_sep", "text": "23:58", "sfx": "assets/sfx_pop.mp3"},
    {"idx": 19, "t": 44.5, "kind": "msg", "code": "TH", "sender": "Tiến Hải (CSKH)",     "dept": "CSKH",     "color": "#2563eb", "text": "Anh chị ơi?", "tts": "Anh chị ơi?", "seen": "Đã xem 11 người", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 20, "t": 47.0, "kind": "end_card", "text": "7h30 sáng mai họp. Ai gánh? Tập 2 👀", "sfx": "assets/sfx_pack/wow.mp3", "meme_gif": "assets/episode1_media/clap.gif"},
]


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent / "vieneu_episode1_v3_voices"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== TẠO GIỌNG ĐỌC THUẦN VIỆT VIENEU-TTS CHO VIDEO v3 (48-52s) ===")
    tts = Vieneu()

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

        # Tính khoảng trống an toàn tới item kế tiếp để giọng đọc không bị đè lên nhau
        next_t = next((x["t"] for x in ITEMS if x["idx"] == it["idx"] + 1), 50.0)
        max_slot = max(1.2, (next_t - it["t"]) - 0.18)
        if it["idx"] == 9:
            max_slot = 1.6  # chừa ~1.4-1.5s im lặng sau "Ai duyệt bản vẽ này?"
        if it["idx"] == 17:
            max_slot = 2.0  # chừa ~1.5-2s im lặng cuối với "Đã xem 11 người"

        if dur > max_slot:
            # Tăng nhẹ atempo vừa đủ khít slot (giữ nguyên âm sắc tiếng Việt)
            spd = min(1.38, dur / max_slot)
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
        it["raw_dur"] = dur
        it["duration_sec"] = final_dur
        print(f"[{it['idx']:02d}] t={it['t']:4.1f}s | {it['sender']:20s} | raw={dur:.2f}s -> fit={final_dur:.2f}s (slot={max_slot:.2f}s)")

    (out_dir / "manifest.json").write_text(json.dumps(ITEMS, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Hoàn tất manifest v3:", out_dir / "manifest.json")

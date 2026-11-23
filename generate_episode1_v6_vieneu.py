#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tổng hợp giọng đọc VieNeu-TTS cho Tập 1 v6 (~50 giây chốt đăng TikTok)
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
    "TE": "Hải Đăng",     # Tùng em (Thiết kế)
    "TA": "Phạm Tuyên",   # Tùng anh (Xưởng)
    "TP": "Thiện Minh",   # Trưởng phòng TK
    "KT": "Đoan Trang",   # Thanh Hải (Kế toán)
    "ME": "Xuân Vĩnh",    # Bạn — Nhân viên Thiết kế ẩn danh (POV bên phải)
}

ITEMS = [
    {"idx": 1,  "kind": "msg", "side": "left",  "code": "TH", "sender": "Tiến Hải (CSKH)",     "color": "#2563eb", "text": "Alo cứu gấp!! Cửa nhà anh Khánh 2 cánh 2 hướng vân thế này?? 😭", "tts": "A lô cứu gấp! Cửa nhà anh Khánh hai cánh hai hướng vân thế này?", "img": "assets/ep1_v3/door_mismatch.png", "sfx": "assets/sfx_pack/windows-error.mp3", "typing": False},
    {"idx": 2,  "kind": "msg", "side": "left",  "code": "TE", "sender": "Tùng em (Thiết kế)",  "color": "#16a34a", "text": "File CAD xuất chuẩn đét, chắc xưởng dán phim lúc buồn ngủ r!", "tts": "Phai két xuất chuẩn đét, chắc xưởng dán phim lúc buồn ngủ rồi!", "sfx": "assets/sfx_pop.mp3", "typing": True},
    {"idx": 3,  "kind": "msg", "side": "left",  "code": "TA", "sender": "Tùng anh (Xưởng)",    "color": "#0d9488", "text": "BV ko ghi hướng vân thì xưởng tự hiểu thôi", "tts": "Bản vẽ không ghi hướng vân thì xưởng tự hiểu thôi.", "sfx": "assets/sfx_pack/huh.mp3", "typing": False},
    {"idx": 4,  "kind": "msg", "side": "left",  "code": "TG", "sender": "Trang (CSKH)",        "color": "#db2777", "text": 'Khách nhắn đúng câu "làm cho nó sang" thôi mà 💀', "tts": "Khách nhắn đúng câu làm cho nó sang thôi mà.", "quote": {"sender": "Anh Khánh (Khách)", "initials": "AK", "color": "#0e7490", "time": "T2 14:20", "badge": "Tin nhắn cũ", "pre": "Làm mẫu nào ", "hl": '"cho nó sang"', "post": " em nhé"}, "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 5,  "kind": "msg", "side": "left",  "code": "TA", "sender": "Tùng anh (Xưởng)",    "color": "#0d9488", "text": "Vân ngang nhìn nhà rộng, chả sang là gì!", "tts": "Vân ngang nhìn nhà rộng, chả sang là gì!", "meme_gif": "assets/episode1_media/confused.gif", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 6,  "kind": "msg", "side": "left",  "code": "TE", "sender": "Tùng em (Thiết kế)",  "color": "#16a34a", "text": "Vân DỌC mới tôn trần cao, nhà này trần thấp tè!", "highlight_word": "DỌC", "tts": "Vân dọc mới tôn trần cao, nhà này trần thấp tè!", "sfx": "assets/sfx_pop.mp3", "typing": False},
    {"idx": 7,  "kind": "msg", "side": "left",  "code": "TH", "sender": "Tiến Hải (CSKH)",     "color": "#2563eb", "text": "Im hộ cái… anh Khánh đang đứng sau lưng đọc chung nhóm chat ạ 🥲", "tts": "Im hộ cái, anh Khánh đang đứng sau lưng đọc chung nhóm chát ạ.", "meme_gif": "assets/episode1_media/this_is_fine.gif", "sfx": "assets/sfx_pack/bruh.mp3", "typing": False},
    {"idx": 8,  "kind": "msg", "side": "right", "code": "ME", "sender": "Bạn",                 "color": "#4f46e5", "text": "Ối dồi ôi, tắt máy giả vờ mất mạng lẹ!! 🤣", "tts": "Ối dồi ôi, tắt máy giả vờ mất mạng lẹ!", "sfx": "assets/sfx_pop.mp3", "typing": True},
    {"idx": 9,  "kind": "msg", "side": "left",  "code": "TP", "sender": "Trưởng phòng TK",     "color": "#1e3a8a", "text": "Ai duyệt bản vẽ này?", "tts": "Ai duyệt bản vẽ này?", "seen": "Đã xem 9 người", "extra_pause": 0.70, "sfx": "assets/sfx_pack/inception.mp3", "typing": False},
    {"idx": 10, "kind": "msg", "side": "left",  "code": "TE", "sender": "Tùng em (Thiết kế)",  "color": "#16a34a", "text": "Dạ anh duyệt thứ 3 lúc uống trà đá ngoài cổng ạ", "tts": "Dạ anh duyệt thứ ba lúc uống trà đá ngoài cổng ạ.", "quote": {"sender": "Trưởng phòng TK", "initials": "TP", "color": "#1e3a8a", "time": "Thứ 3 • 09:15", "badge": "Đã duyệt", "pre": "", "hl": "OK làm đi", "post": ", khách gấp"}, "sfx": "assets/sfx_pack/rimshot.mp3", "typing": False},
    {"idx": 11, "kind": "msg", "side": "left",  "code": "TP", "sender": "Trưởng phòng TK",     "color": "#1e3a8a", "text": "Chắc Hải chụp ngược sáng nhìn lú đấy, anh về trước", "tts": "Chắc Hải chụp ngược sáng nhìn lú đấy, anh về trước.", "sfx": "assets/sfx_ting.mp3", "typing": False, "recall_id": "msg_11"},
    {"idx": 12, "kind": "sys_recall", "target_id": "msg_11", "text": "Trưởng phòng TK đã thu hồi một tin nhắn", "sfx": "assets/sfx_pack/metal_boom.mp3", "hold": 1.15},
    {"idx": 13, "kind": "msg", "side": "left",  "code": "KT", "sender": "Thanh Hải (Kế toán)", "color": "#ea580c", "text": "Chụp màn hình kịp rồi nha anh 🙂 Anh Khánh chuyển cọc cuối chưa?", "tts": "Chụp màn hình kịp rồi nha anh. Anh Khánh chuyển cọc cuối chưa?", "quote": {"sender": "Trưởng phòng TK", "initials": "TP", "color": "#1e3a8a", "time": "16:50", "badge": "Đã chụp lại", "pre": "Chắc Hải ", "hl": "chụp ngược sáng", "post": " nhìn lú đấy"}, "sfx": "assets/sfx_pack/ding.mp3", "typing": False},
    {"idx": 14, "kind": "msg", "side": "left",  "code": "TH", "sender": "Tiến Hải (CSKH)",     "color": "#2563eb", "text": "Ổng bắt làm lại cánh phải. CN này nhập trạch, ko kịp là Trang qua gặp ổng xin khất đấy 😭", "tts": "Ổng bắt làm lại cánh phải. Chủ nhật này nhập trạch, không kịp là Trang qua gặp ổng xin khất đấy!", "sfx": "assets/sfx_pack/huh.mp3", "typing": True},
    {"idx": 15, "kind": "msg", "side": "left",  "code": "TA", "sender": "Tùng anh (Xưởng)",    "color": "#0d9488", "text": "CN xưởng nghỉ mà 🥲 2 con anh hứa đi công viên", "tts": "Chủ nhật xưởng nghỉ mà, hai con anh hứa đi công viên.", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 16, "kind": "msg", "side": "left",  "code": "TH", "sender": "Tiến Hải (CSKH)",     "color": "#2563eb", "text": "Anh chị ơi?? @Trang CSKH chuẩn bị tinh thần nhé 😰", "mention": "@Trang", "tts": "Anh chị ơi? Trang chăm sóc khách hàng chuẩn bị tinh thần nhé.", "seen": "Đã xem 11 người", "extra_pause": 0.45, "sfx": "assets/sfx_pop.mp3", "typing": True},
    {"idx": 17, "kind": "end_card", "text": "CN có kịp ko hay Trang phải đi gặp anh Khánh? Chờ Tập 2 👀", "sfx": "assets/sfx_pack/wow.mp3", "meme_gif": "assets/episode1_media/clap.gif", "hold": 2.30},
]


def _probe_duration(wav_path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(wav_path)
    ]).decode().strip())


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent / "vieneu_episode1_v6_voices"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== TẠO GIỌNG ĐỌC VIENEU-TTS CHO TẬP 1 v6 (~50s CHỐT TIKTOK) ===")
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
        dur = _probe_duration(raw_wav)

        # Điều chỉnh nhịp nhanh gọn chuẩn TikTok (1.06x - 1.18x) để tổng video rơi đúng ~50s
        target_cap = 3.2 if len(it["tts"]) > 65 else 2.65
        if dur > target_cap:
            spd = min(1.20, max(1.06, dur / target_cap))
            subprocess.run([
                "ffmpeg", "-y", "-i", str(raw_wav),
                "-af", f"atempo={spd:.3f}",
                str(fit_wav)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            final_dur = _probe_duration(fit_wav)
        else:
            shutil.copy2(raw_wav, fit_wav)
            final_dur = dur

        raw_wav.unlink(missing_ok=True)
        it["audio_file"] = fit_wav.name
        it["voice_name"] = voice_name
        it["duration_sec"] = final_dur
        total_speech += final_dur
        print(f"[{it['idx']:02d}] ({it['side']:5s}) {it['sender']:20s} -> {final_dur:.2f}s (gốc {dur:.2f}s)")

    print(f"Tổng thời lượng thoại thuần: {total_speech:.2f}s")
    (out_dir / "manifest.json").write_text(json.dumps(ITEMS, ensure_ascii=False, indent=2), encoding="utf-8")

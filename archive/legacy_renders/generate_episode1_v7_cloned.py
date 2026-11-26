#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tổng hợp giọng đọc VieNeu-TTS v7 (Clone 2 chất giọng nam chuẩn từ Video_mẫu.mp4 + top giọng nữ ⭐):
- KHÔNG ép atempo gây méo tiếng
- Kiểm soát temperature/repetition_penalty để không vấp/lặp chữ
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

WORKSPACE = Path(__file__).resolve().parent
REF_ANH = WORKSPACE / "assets" / "voice_refs" / "ref_giong_anh_mau.wav"
REF_EM = WORKSPACE / "assets" / "voice_refs" / "ref_giong_em_mau.wav"

# Nam trẻ (Tiến Hải, Tùng em, Bạn) & Nam trầm (Tùng anh, Trưởng phòng TK) clone trực tiếp từ Video_mẫu.mp4
# 2 nhân vật nữ dùng 2 giọng ⭐ mượt nhất của VieNeu
SPEAKER_CONFIG = {
    "TH": {"ref_audio": str(REF_EM),  "voice": None,         "label": "Clone Nam trẻ (Video_mẫu)"},
    "TE": {"ref_audio": str(REF_EM),  "voice": None,         "label": "Clone Nam trẻ (Video_mẫu)"},
    "ME": {"ref_audio": str(REF_EM),  "voice": None,         "label": "Clone Nam trẻ (Video_mẫu)"},
    "TA": {"ref_audio": str(REF_ANH), "voice": None,         "label": "Clone Nam trầm (Video_mẫu)"},
    "TP": {"ref_audio": str(REF_ANH), "voice": None,         "label": "Clone Nam trầm (Video_mẫu)"},
    "TG": {"ref_audio": None,         "voice": "Ngọc Huyền", "label": "⭐ Ngọc Huyền"},
    "KT": {"ref_audio": None,         "voice": "Trúc Ly",    "label": "⭐ Trúc Ly"},
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
    {"idx": 9,  "kind": "msg", "side": "left",  "code": "TP", "sender": "Trưởng phòng TK",     "color": "#1e3a8a", "text": "Ai duyệt bản vẽ này?", "tts": "Ai duyệt bản vẽ này?", "seen": "Đã xem 9 người", "extra_pause": 0.65, "sfx": "assets/sfx_pack/inception.mp3", "typing": False},
    {"idx": 10, "kind": "msg", "side": "left",  "code": "TE", "sender": "Tùng em (Thiết kế)",  "color": "#16a34a", "text": "Dạ anh duyệt thứ 3 lúc uống trà đá ngoài cổng ạ", "tts": "Dạ anh duyệt thứ ba lúc uống trà đá ngoài cổng ạ.", "quote": {"sender": "Trưởng phòng TK", "initials": "TP", "color": "#1e3a8a", "time": "Thứ 3 • 09:15", "badge": "Đã duyệt", "pre": "", "hl": "OK làm đi", "post": ", khách gấp"}, "sfx": "assets/sfx_pack/rimshot.mp3", "typing": False},
    {"idx": 11, "kind": "msg", "side": "left",  "code": "TP", "sender": "Trưởng phòng TK",     "color": "#1e3a8a", "text": "Chắc Hải chụp ngược sáng nhìn lú đấy, anh về trước", "tts": "Chắc Hải chụp ngược sáng nhìn lú đấy, anh về trước.", "sfx": "assets/sfx_ting.mp3", "typing": False, "recall_id": "msg_11"},
    {"idx": 12, "kind": "sys_recall", "target_id": "msg_11", "text": "Trưởng phòng TK đã thu hồi một tin nhắn", "sfx": "assets/sfx_pack/metal_boom.mp3", "hold": 1.15},
    {"idx": 13, "kind": "msg", "side": "left",  "code": "KT", "sender": "Thanh Hải (Kế toán)", "color": "#ea580c", "text": "Chụp màn hình kịp rồi nha anh 🙂 Anh Khánh chuyển cọc cuối chưa?", "tts": "Chụp màn hình kịp rồi nha anh. Anh Khánh chuyển cọc cuối chưa?", "quote": {"sender": "Trưởng phòng TK", "initials": "TP", "color": "#1e3a8a", "time": "16:50", "badge": "Đã chụp lại", "pre": "Chắc Hải ", "hl": "chụp ngược sáng", "post": " nhìn lú đấy"}, "sfx": "assets/sfx_pack/ding.mp3", "typing": False},
    {"idx": 14, "kind": "msg", "side": "left",  "code": "TH", "sender": "Tiến Hải (CSKH)",     "color": "#2563eb", "text": "Ổng bắt làm lại cánh phải. CN này nhập trạch, ko kịp là Trang qua gặp ổng xin khất đấy 😭", "tts": "Ổng bắt làm lại cánh phải. Chủ nhật này nhập trạch, không kịp là Trang qua gặp ổng xin khất đấy!", "sfx": "assets/sfx_pack/huh.mp3", "typing": True},
    {"idx": 15, "kind": "msg", "side": "left",  "code": "TA", "sender": "Tùng anh (Xưởng)",    "color": "#0d9488", "text": "CN xưởng nghỉ mà 🥲 2 con anh hứa đi công viên", "tts": "Chủ nhật xưởng nghỉ mà, hai con anh hứa đi công viên.", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 16, "kind": "msg", "side": "left",  "code": "TH", "sender": "Tiến Hải (CSKH)",     "color": "#2563eb", "text": "Anh chị ơi?? @Trang CSKH chuẩn bị tinh thần nhé 😰", "mention": "@Trang", "tts": "Anh chị ơi? Trang chăm sóc khách hàng chuẩn bị tinh thần nhé.", "seen": "Đã xem 11 người", "extra_pause": 0.40, "sfx": "assets/sfx_pop.mp3", "typing": True},
    {"idx": 17, "kind": "end_card", "text": "CN có kịp ko hay Trang phải đi gặp anh Khánh? Chờ Tập 2 👀", "sfx": "assets/sfx_pack/wow.mp3", "meme_gif": "assets/episode1_media/clap.gif", "hold": 2.30},
]


def _probe_duration(wav_path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(wav_path)
    ]).decode().strip())


if __name__ == "__main__":
    out_dir = WORKSPACE / "vieneu_episode1_v7_voices"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== TẠO GIỌNG ĐỌC CLONE TỪ VIDEO MẪU (TẬP 1 v7) ===")
    tts = Vieneu()
    total_speech = 0.0

    for it in ITEMS:
        if it["kind"] != "msg":
            continue
        cfg = SPEAKER_CONFIG[it["code"]]
        raw_wav = out_dir / f"raw_{it['idx']:02d}.wav"
        fit_wav = out_dir / f"voice_{it['idx']:02d}_{it['code']}.wav"

        # Tự động thử lại nếu model bị "babble" kéo dài bất thường (vd > 0.36s/từ + 1.0s)
        word_cnt = max(1, len(it["tts"].split()))
        max_expected_dur = word_cnt * 0.34 + 1.15
        for attempt in range(4):
            audio = tts.infer(
                text=it["tts"],
                ref_audio=cfg["ref_audio"],
                voice=cfg["voice"],
                temperature=0.62 if attempt > 0 else 0.68,
                top_k=18 if attempt > 0 else 20,
                top_p=0.90,
                repetition_penalty=1.35 + attempt * 0.05,
                max_new_frames=min(220, int(word_cnt * 16 + 35)),
                denoise=True,
            )
            tts.save(audio, str(raw_wav))
            raw_dur = _probe_duration(raw_wav)
            if raw_dur <= max_expected_dur:
                break
            print(f"  [!] Câu #{it['idx']} dài bất thường ({raw_dur:.2f}s > {max_expected_dur:.2f}s), thử lại lần {attempt + 2}...")

        # Chỉ cắt khoảng lặng đuôi > 0.25s ở ngưỡng rất nhẹ (-55dB) để KHÔNG bao giờ xén mất âm đầu ("Dạ...")
        subprocess.run([
            "ffmpeg", "-y", "-i", str(raw_wav),
            "-af", "areverse,silenceremove=start_periods=1:start_threshold=-55dB,areverse",
            str(fit_wav)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        final_dur = _probe_duration(fit_wav)
        if final_dur < 0.4:
            shutil.copy2(raw_wav, fit_wav)
            final_dur = _probe_duration(fit_wav)
        raw_wav.unlink(missing_ok=True)

        it["audio_file"] = fit_wav.name
        it["voice_name"] = cfg["label"]
        it["duration_sec"] = final_dur
        total_speech += final_dur
        print(f"[{it['idx']:02d}] ({cfg['label']:27s}) {it['sender']:20s} -> {final_dur:.2f}s")

    print(f"Tổng thời lượng thoại thuần (tự nhiên 1.0x): {total_speech:.2f}s")
    (out_dir / "manifest.json").write_text(json.dumps(ITEMS, ensure_ascii=False, indent=2), encoding="utf-8")

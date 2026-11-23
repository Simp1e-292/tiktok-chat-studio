#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tổng hợp giọng đọc VieNeu-TTS cho Tập 1 v5:
- Tỉ lệ khung điện thoại chuẩn V2 (810x1710 căn giữa trên nền 1080x1920)
- Tùng em (Thiết kế) về bên trái như bình thường
- Góc nhìn POV chủ máy bên phải: 1 nhân viên Thiết kế khác không đặt tên,
  thi thoảng thêm mấy câu "ối dồi ôi" biểu cảm
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
    "TE": "Hải Đăng",     # Tùng em (Thiết kế - bên trái)
    "TA": "Phạm Tuyên",   # Tùng anh (Xưởng)
    "TP": "Thiện Minh",   # Trưởng phòng TK
    "KT": "Đoan Trang",   # Thanh Hải (Kế toán)
    "KM": "Ngọc Trân",    # Kim (Nhân sự)
    "ME": "Xuân Vĩnh",    # Bạn — Nhân viên Thiết kế khác (POV ẩn danh bên phải)
}

ITEMS = [
    {"idx": 1,  "kind": "msg", "side": "left",  "code": "TH", "sender": "Tiến Hải (CSKH)",     "dept": "CSKH",     "color": "#2563eb", "text": "Alo cứu bồ gấp!! Em đang nhà anh Khánh nghiệm thu, sao 2 cánh cửa 2 hướng vân thế này?? 😭", "tts": "A lô cứu bồ gấp! Em đang nhà anh Khánh nghiệm thu, sao hai cánh cửa hai hướng vân thế này?", "v4_src": "voice_01_TH.wav", "img": "assets/ep1_v3/door_mismatch.png", "sfx": "assets/sfx_pack/windows-error.mp3", "typing": False},
    {"idx": 2,  "kind": "msg", "side": "left",  "code": "TG", "sender": "Trang (CSKH)",        "dept": "CSKH",     "color": "#db2777", "text": 'Ủa @Tùng em, hôm trước khách dặn làm cửa "độc bản" à??', "mention": "@Tùng em", "tts": "Ủa Tùng em, hôm trước khách dặn làm cửa độc bản à?", "v4_src": "voice_02_TG.wav", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 3,  "kind": "msg", "side": "left",  "code": "TE", "sender": "Tùng em (Thiết kế)",  "dept": "Thiết kế", "color": "#16a34a", "text": "Đừng đổ tôi bà ơi! File CAD xuất chuẩn đét, chắc ông xưởng dán phim lúc buồn ngủ r!", "tts": "Đừng đổ tôi bà ơi! Phai két xuất chuẩn đét, chắc ông xưởng dán phim lúc buồn ngủ rồi!", "v4_src": "voice_03_TE.wav", "sfx": "assets/sfx_pop.mp3", "typing": True},
    {"idx": 4,  "kind": "msg", "side": "left",  "code": "TA", "sender": "Tùng anh (Xưởng)",    "dept": "Xưởng",    "color": "#0d9488", "text": "Khoan nhé em trai! BV ko ghi hướng vân thì xưởng tự hiểu là làm cho nó khác bọt còn gì", "tts": "Khoan nhé em trai! Bản vẽ không ghi hướng vân thì xưởng tự hiểu là làm cho nó khác bọt còn gì.", "v4_src": "voice_04_TA.wav", "sfx": "assets/sfx_pack/huh.mp3", "typing": True},
    {"idx": 5,  "kind": "msg", "side": "right", "code": "ME", "sender": "Bạn",                  "dept": "Thiết kế", "color": "#4f46e5", "text": "Ối dồi ôi, kèo này có biến to rồi mấy ông ơi 💀", "tts": "Ối dồi ôi, kèo này có biến to rồi mấy ông ơi!", "sfx": "assets/sfx_pop.mp3", "typing": True},
    {"idx": 6,  "kind": "msg", "side": "left",  "code": "TG", "sender": "Trang (CSKH)",        "dept": "CSKH",     "color": "#db2777", "text": 'Anh Khánh nhắn đúng câu "làm cho nó sang" thôi, ai bảo khác bọt đâu anh 💀', "tts": "Anh Khánh nhắn đúng câu làm cho nó sang thôi, ai bảo khác bọt đâu anh.", "v4_src": "voice_05_TG.wav", "img": "assets/ep1_v3/msg_khach_sang.png", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 7,  "kind": "msg", "side": "left",  "code": "TA", "sender": "Tùng anh (Xưởng)",    "dept": "Xưởng",    "color": "#0d9488", "text": "Thì vân ngang nhìn nhà nó rộng, chả sang là gì!", "tts": "Thì vân ngang nhìn nhà nó rộng, chả sang là gì!", "v4_src": "voice_06_TA.wav", "meme_gif": "assets/episode1_media/confused.gif", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 8,  "kind": "msg", "side": "left",  "code": "TE", "sender": "Tùng em (Thiết kế)",  "dept": "Thiết kế", "color": "#16a34a", "text": "Vân DỌC mới tôn trần cao anh ơi, nhà này trần thấp tè!", "highlight_word": "DỌC", "tts": "Vân dọc mới tôn trần cao anh ơi, nhà này trần thấp tè!", "v4_src": "voice_07_TE.wav", "sfx": "assets/sfx_pop.mp3", "typing": True},
    {"idx": 9,  "kind": "msg", "side": "left",  "code": "TH", "sender": "Tiến Hải (CSKH)",     "dept": "CSKH",     "color": "#2563eb", "text": "Hai ông im hộ tôi cái… anh Khánh đang đứng sau lưng đọc chung nhóm chat này luôn ạ 🥲", "tts": "Hai ông im hộ tôi cái, anh Khánh đang đứng sau lưng đọc chung nhóm chát này luôn ạ.", "v4_src": "voice_08_TH.wav", "meme_gif": "assets/episode1_media/this_is_fine.gif", "sfx": "assets/sfx_pack/bruh.mp3", "typing": False},
    {"idx": 10, "kind": "msg", "side": "right", "code": "ME", "sender": "Bạn",                  "dept": "Thiết kế", "color": "#4f46e5", "text": "Ối dồi ôi vãi chưởng, tắt máy giả vờ mất mạng lẹ!! 🤣", "tts": "Ối dồi ôi vãi chưởng, tắt máy giả vờ mất mạng lẹ!", "sfx": "assets/sfx_pop.mp3", "typing": True},
    {"idx": 11, "kind": "msg", "side": "left",  "code": "TP", "sender": "Trưởng phòng TK",     "dept": "Thiết kế", "color": "#1e3a8a", "text": "Ai duyệt cái bản vẽ này?", "tts": "Ai duyệt cái bản vẽ này?", "v4_src": "voice_09_TP.wav", "seen": "Đã xem 9 người", "extra_pause": 1.0, "sfx": "assets/sfx_pack/inception.mp3", "typing": False},
    {"idx": 12, "kind": "msg", "side": "left",  "code": "TE", "sender": "Tùng em (Thiết kế)",  "dept": "Thiết kế", "color": "#16a34a", "text": "Dạ anh duyệt sáng thứ 3 lúc đang uống trà đá ngoài cổng ạ", "tts": "Dạ anh duyệt sáng thứ ba lúc đang uống trà đá ngoài cổng ạ.", "v4_src": "voice_10_TE.wav", "img": "assets/ep1_v3/msg_truong_ok.png", "sfx": "assets/sfx_pack/rimshot.mp3", "typing": True},
    {"idx": 13, "kind": "msg", "side": "left",  "code": "TP", "sender": "Trưởng phòng TK",     "dept": "Thiết kế", "color": "#1e3a8a", "text": "Chắc do thằng Hải chụp ngược sáng nhìn lú đấy, anh về trước đây", "tts": "Chắc do thằng Hải chụp ngược sáng nhìn lú đấy, anh về trước đây.", "v4_src": "voice_11_TP.wav", "sfx": "assets/sfx_ting.mp3", "typing": False, "recall_id": "msg_13"},
    {"idx": 14, "kind": "sys_recall", "target_id": "msg_13", "text": "Trưởng phòng TK đã thu hồi một tin nhắn", "sfx": "assets/sfx_pack/metal_boom.mp3", "hold": 1.35},
    {"idx": 15, "kind": "msg", "side": "left",  "code": "KT", "sender": "Thanh Hải (Kế toán)", "dept": "Kế toán",  "color": "#ea580c", "text": "Chụp màn hình kịp rồi nha anh Trưởng phòng 🙂 Mà 40% tiền cọc cuối anh Khánh chuyển chưa đấy Hải?", "tts": "Chụp màn hình kịp rồi nha anh Trưởng phòng. Mà bốn mươi phần trăm tiền cọc cuối anh Khánh chuyển chưa đấy Hải?", "v4_src": "voice_13_KT.wav", "img": "assets/ep1_v3/msg_thuhoi_capture.png", "meme_gif": "assets/episode1_media/shocked.gif", "sfx": "assets/sfx_pack/ding.mp3", "typing": False},
    {"idx": 16, "kind": "msg", "side": "left",  "code": "TH", "sender": "Tiến Hải (CSKH)",     "dept": "CSKH",     "color": "#2563eb", "text": "KHOAN CẢ NHÀ!! Em vừa định xin lỗi, thì anh Khánh bảo… ko bắt đền nữa!", "tts": "Khoan cả nhà! Em vừa định xin lỗi, thì anh Khánh bảo, không bắt đền nữa!", "v4_src": "voice_14_TH.wav", "sfx": "assets/sfx_pop.mp3", "typing": True},
    {"idx": 17, "kind": "msg", "side": "left",  "code": "TA", "sender": "Tùng anh (Xưởng)",    "dept": "Xưởng",    "color": "#0d9488", "text": "Thật á?! Thế bảo anh về đón con đây!", "tts": "Thật á? Thế bảo anh về đón con đây!", "v4_src": "voice_15_TA.wav", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 18, "kind": "msg", "side": "left",  "code": "TH", "sender": "Tiến Hải (CSKH)",     "dept": "CSKH",     "color": "#2563eb", "text": "Nhưng ổng bảo giữ nguyên cửa, điều kiện là… tối nay em Trang CSKH phải qua gặp riêng ổng nói chuyện mới chịu ký nghiệm thu 😳", "tts": "Nhưng ổng bảo giữ nguyên cửa, điều kiện là tối nay em Trang chăm sóc khách hàng phải qua gặp riêng ổng nói chuyện mới chịu ký nghiệm thu.", "v4_src": "voice_16_TH.wav", "sfx": "assets/sfx_pack/huh.mp3", "typing": True},
    {"idx": 19, "kind": "msg", "side": "left",  "code": "TE", "sender": "Tùng em (Thiết kế)",  "dept": "Thiết kế", "color": "#16a34a", "text": "CÁI GÌ CƠ?! Gặp Trang làm gì?? Anh Hải giữ chân ổng lại, em phi xe sang ngay bây giờ!!", "tts": "Cái gì cơ?! Gặp Trang làm gì? Anh Hải giữ chân ổng lại, em phi xe sang ngay bây giờ!", "v4_src": "voice_17_TE.wav", "sfx": "assets/sfx_pack/windows-error.mp3", "typing": True},
    {"idx": 20, "kind": "msg", "side": "right", "code": "ME", "sender": "Bạn",                  "dept": "Thiết kế", "color": "#4f46e5", "text": "Ối dồi ôi plot twist căng đét, mai hóng tiếp!! 👀🔥", "tts": "Ối dồi ôi, pờ lót tuýt căng đét, mai hóng tiếp!", "sfx": "assets/sfx_pop.mp3", "typing": True},
    {"idx": 21, "kind": "msg", "side": "left",  "code": "KM", "sender": "Kim (Nhân sự)",       "dept": "Nhân sự",  "color": "#92400e", "text": "Thứ 7 mai lên văn phòng sớm hóng nha cả nhà, Nhân sự bao cà phê Đắk Lắk ☕🔥", "tts": "Thứ bảy mai lên văn phòng sớm hóng nha cả nhà, Nhân sự bao cà phê Đắc Lắc!", "v4_src": "voice_18_KM.wav", "seen": "Đã xem 12 người", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 22, "kind": "end_card", "text": "Anh Khánh đòi gặp Trang làm gì? Chờ Tập 2 tối mai 👀", "sfx": "assets/sfx_pack/wow.mp3", "meme_gif": "assets/episode1_media/clap.gif", "hold": 3.0},
]


def _probe_duration(wav_path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(wav_path)
    ]).decode().strip())


if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    v4_dir = base / "vieneu_episode1_v4_voices"
    out_dir = base / "vieneu_episode1_v5_voices"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== TỔNG HỢP GIỌNG ĐỌC VIENEU-TTS CHO TẬP 1 v5 (POV NHÂN VIÊN THIẾT KẾ ẨN DANH) ===")
    tts = None
    total_speech = 0.0

    for it in ITEMS:
        if it["kind"] != "msg":
            continue
        fit_wav = out_dir / f"voice_{it['idx']:02d}_{it['code']}.wav"
        voice_name = VOICE_MAP[it["code"]]

        v4_file = v4_dir / it["v4_src"] if it.get("v4_src") else None
        if v4_file and v4_file.exists():
            shutil.copy2(v4_file, fit_wav)
            final_dur = _probe_duration(fit_wav)
            src_tag = "reused-v4"
        else:
            if tts is None:
                tts = Vieneu()
            raw_wav = out_dir / f"raw_{it['idx']:02d}.wav"
            audio = tts.infer(text=it["tts"], voice=voice_name)
            tts.save(audio, str(raw_wav))
            dur = _probe_duration(raw_wav)
            if dur > 3.6:
                spd = min(1.18, dur / 3.2)
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
            src_tag = "new-tts"

        it["audio_file"] = fit_wav.name
        it["voice_name"] = voice_name
        it["duration_sec"] = final_dur
        total_speech += final_dur
        print(f"[{it['idx']:02d}] ({it['side']:5s}, {src_tag:9s}) {it['sender']:20s} -> {final_dur:.2f}s")

    print(f"Tổng thời lượng thoại thuần: {total_speech:.2f}s")
    (out_dir / "manifest.json").write_text(json.dumps(ITEMS, ensure_ascii=False, indent=2), encoding="utf-8")

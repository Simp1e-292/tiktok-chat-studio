#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tổng hợp giọng đọc (Clone Video_mẫu.mp4 + Ngọc Huyền / Trúc Ly) và SFX chuyển cảnh 21:00 Đêm
cho tập: "BỂ BƠI VÔ CỰC CỦA SẾP"
"""

import os
import json
import shutil
import subprocess
import numpy as np
import soundfile as sf
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

SPEAKER_CONFIG = {
    "TE":  {"ref_audio": str(REF_EM),  "voice": None,         "label": "Clone Nam trẻ (Video_mẫu)"},
    "TH":  {"ref_audio": str(REF_EM),  "voice": None,         "label": "Clone Nam trẻ (Video_mẫu)"},
    "POV": {"ref_audio": str(REF_EM),  "voice": None,         "label": "Clone Nam trẻ (Video_mẫu)"},
    "SEP": {"ref_audio": str(REF_ANH), "voice": None,         "label": "Clone Nam trầm (Video_mẫu)"},
    "TG":  {"ref_audio": None,         "voice": "Ngọc Huyền", "label": "⭐ Ngọc Huyền"},
    "KT":  {"ref_audio": None,         "voice": "Trúc Ly",    "label": "⭐ Trúc Ly"},
}

ITEMS = [
    {"idx": 1,  "kind": "msg", "side": "left",  "code": "TE",  "sender": "Tùng em (Thiết kế)",  "color": "#16a34a", "text": "SẾP ƠIIIIIIIIIII", "tts": "Sếp ơi!", "img": "assets/ep_be_boi/ho_mong_tram_can.jpg", "sfx": "assets/sfx_pack/windows-error.mp3", "typing": False},
    {"idx": 2,  "kind": "msg", "side": "left",  "code": "TE",  "sender": "Tùng em (Thiết kế)",  "color": "#16a34a", "text": "Đào hố gì thế sếp?", "tts": "Đào hố gì thế sếp?", "sfx": "assets/sfx_ting.mp3", "typing": False},
    {"idx": 3,  "kind": "msg", "side": "left",  "code": "SEP", "sender": "Sếp",                 "color": "#1e3a8a", "text": "Bể bơi vô cực. Hè này cho ae tắm mát.", "tts": "Bể bơi vô cực. Hè này cho anh em tắm mát.", "sfx": "assets/sfx_pack/ding.mp3", "typing": True},
    {"idx": 4,  "kind": "msg", "side": "left",  "code": "TG",  "sender": "Trang (CSKH)",        "color": "#db2777", "text": "Ối sếp đẹp trai thế!! 😍", "tts": "Ối sếp đẹp trai thế!", "meme_gif": "assets/episode1_media/clap.gif", "sfx": "assets/sfx_pack/wow.mp3", "typing": False},
    {"idx": 5,  "kind": "msg", "side": "left",  "code": "TH",  "sender": "Tiến Hải (CSKH)",     "color": "#2563eb", "text": "Chị em mặc bikini nhé! Em xin chân cứu hộ", "tts": "Chị em mặc bi ki ni nhé! Em xin chân cứu hộ.", "sfx": "assets/sfx_pop.mp3", "typing": False},
    {"idx": 6,  "kind": "msg", "side": "left",  "code": "KT",  "sender": "Thanh Hải (Kế toán)", "color": "#ea580c", "text": "Hố móng trạm cân 80 tấn. Bơi lội cái giề? 🙂", "tts": "Hố móng trạm cân tám mươi tấn. Bơi lội cái giề?", "meme_gif": "assets/episode1_media/confused.gif", "sfx": "assets/sfx_pack/bruh.mp3", "typing": True},
    {"idx": 7,  "kind": "msg", "side": "right", "code": "POV", "sender": "Bạn",                 "color": "#4f46e5", "text": "Như… 💀", "tts": "Như.", "sfx": "assets/sfx_pack/sadness-1.mp3", "typing": True},
    {"idx": 8,  "kind": "msg", "side": "left",  "code": "SEP", "sender": "Sếp",                 "color": "#1e3a8a", "text": "😂 Tối tan ca nhìn đường. Đứa nào lao xe xuống đấy thì tự múc đất chôn nhé.", "tts": "Tối tan ca nhìn đường. Đứa nào lao xe xuống đấy thì tự múc đất chôn nhé.", "sfx": "assets/sfx_pack/rimshot.mp3", "typing": False},
    {"idx": 9,  "kind": "msg", "side": "left",  "code": "TE",  "sender": "Tùng em (Thiết kế)",  "color": "#16a34a", "text": "Mưa to 1 cái là thành bể bơi thật đấy sếp ơi.", "tts": "Mưa to một cái là thành bể bơi thật đấy sếp ơi.", "sfx": "assets/sfx_pop.mp3", "typing": True},
    {"idx": 10, "kind": "msg", "side": "left",  "code": "SEP", "sender": "Sếp",                 "color": "#1e3a8a", "text": "Mày chỉ toàn mồm thối! Tao xem dự báo rồi, tuần này nắng ráo.", "tts": "Mày chỉ toàn mồm thối! Tao xem dự báo rồi, tuần này nắng ráo.", "sfx": "assets/sfx_pack/huh.mp3", "typing": False},
    {"idx": 11, "kind": "sys_time", "text": "⏰ 21:00 ĐÊM — Trời đổ mưa như trút ⛈️", "sfx": "assets/ep_be_boi/clock_tick_rain.wav", "hold": 1.75},
    {"idx": 12, "kind": "msg", "side": "left",  "code": "TH",  "sender": "Tiến Hải (CSKH)",     "color": "#2563eb", "text": "CẤP BÁOOOOOOO!! 🌊😱", "tts": "Cấp báo!", "img": "assets/ep_be_boi/mua_ngap_ho.jpg", "meme_gif": "assets/episode1_media/shocked.gif", "sfx": "assets/sfx_pack/inception.mp3", "typing": False},
    {"idx": 13, "kind": "msg", "side": "left",  "code": "SEP", "sender": "Sếp",                 "color": "#1e3a8a", "text": "Thằng Tùng em đâu? Mai lên công ty mày biết tay tao!", "tts": "Thằng Tùng em đâu? Mai lên công ty mày biết tay tao!", "sfx": "assets/sfx_pack/windows-error.mp3", "typing": True},
    {"idx": 14, "kind": "msg", "side": "left",  "code": "TE",  "sender": "Tùng em (Thiết kế)",  "color": "#16a34a", "text": "Em xin phép mai làm online tránh bão ạ 😭", "tts": "Em xin phép mai làm on lai tránh bão ạ!", "meme_gif": "assets/episode1_media/this_is_fine.gif", "sfx": "assets/sfx_pack/metal_boom.mp3", "typing": True, "extra_pause": 0.45},
    {"idx": 15, "kind": "end_card", "text": "Theo ae mai Tùng em có bị trừ lương ko? 😂👀", "sfx": "assets/sfx_pack/wow.mp3", "meme_gif": "assets/episode1_media/clap.gif", "hold": 2.40},
]


def _build_clock_tick_rain_sfx(out_path: Path):
    """Tạo hiệu ứng tiếng đồng hồ tích tắc chuyển sang mưa rào & sấm nhẹ (1.75s)"""
    sr = 44100
    dur = 1.75
    n = int(sr * dur)
    buf = np.zeros(n, dtype=np.float32)

    # 3 tiếng tick-tock sắc gọn lúc 0.05s, 0.42s, 0.78s
    for idx, t0 in enumerate([0.05, 0.42, 0.78]):
        i0 = int(t0 * sr)
        t_tick = np.arange(int(0.055 * sr)) / sr
        freq = 1650.0 if idx % 2 == 0 else 1250.0
        click = np.sin(2 * np.pi * freq * t_tick) * np.exp(-t_tick * 95.0) * 0.55
        buf[i0:i0 + len(click)] += click

    # Tiếng mưa rào + sấm trầm từ 0.85s -> 1.75s
    rng = np.random.default_rng(42)
    i_rain = int(0.82 * sr)
    m = n - i_rain
    t_rain = np.arange(m) / sr
    white = rng.normal(0.0, 1.0, m).astype(np.float32)
    # Làm mượt thành tiếng mưa & rumble
    rain = np.convolve(white, np.ones(18, dtype=np.float32) / 18.0, mode="same")
    thunder = np.sin(2 * np.pi * 62.0 * t_rain) * np.exp(-t_rain * 2.4) * 0.45
    env = np.minimum(1.0, t_rain / 0.12) * np.minimum(1.0, (m / sr - t_rain) / 0.25)
    buf[i_rain:] += (rain * 0.22 + thunder) * env

    buf = np.clip(buf, -0.92, 0.92)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_path), buf, sr)


def _probe_duration(wav_path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(wav_path)
    ]).decode().strip())


if __name__ == "__main__":
    sfx_p = WORKSPACE / "assets" / "ep_be_boi" / "clock_tick_rain.wav"
    _build_clock_tick_rain_sfx(sfx_p)
    print(f"Đã tạo SFX chuyển cảnh: {sfx_p}")

    out_dir = WORKSPACE / "vieneu_be_boi_voices"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== TỔNG HỢP GIỌNG CLONE CHO TẬP 'BỂ BƠI VÔ CỰC CỦA SẾP' ===")
    tts = Vieneu()
    total_speech = 0.0

    for it in ITEMS:
        if it["kind"] != "msg":
            continue
        cfg = SPEAKER_CONFIG[it["code"]]
        raw_wav = out_dir / f"raw_{it['idx']:02d}.wav"
        fit_wav = out_dir / f"voice_{it['idx']:02d}_{it['code']}.wav"

        word_cnt = max(1, len(it["tts"].split()))
        max_expected_dur = word_cnt * 0.35 + 1.15
        for attempt in range(4):
            audio = tts.infer(
                text=it["tts"],
                ref_audio=cfg["ref_audio"],
                voice=cfg["voice"],
                temperature=0.62 if attempt > 0 else 0.68,
                top_k=18 if attempt > 0 else 20,
                top_p=0.90,
                repetition_penalty=1.35 + attempt * 0.05,
                max_new_frames=min(230, int(word_cnt * 16 + 38)),
                denoise=True,
            )
            tts.save(audio, str(raw_wav))
            raw_dur = _probe_duration(raw_wav)
            if raw_dur <= max_expected_dur:
                break
            print(f"  [!] Câu #{it['idx']} dài bất thường ({raw_dur:.2f}s > {max_expected_dur:.2f}s), thử lại lần {attempt + 2}...")

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

    print(f"Tổng thời lượng thoại thuần: {total_speech:.2f}s")
    (out_dir / "manifest.json").write_text(json.dumps(ITEMS, ensure_ascii=False, indent=2), encoding="utf-8")

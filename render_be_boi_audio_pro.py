#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render bản nâng cấp âm thanh chuẩn Con Bò Đi Làm cho tập "BỂ BƠI VÔ CỰC CỦA SẾP":
- 1 giọng kể duy nhất siêu mượt (Edge-TTS vi-VN-NamMinhNeural +12%) + giọng nữ nhẹ ở End Card
- Cắt sạch khoảng im lặng chết (Dead Air từ 29% -> <2%)
- Nhạc nền hài hước bản quyền 0% (bgm_office_comedy_loop.wav) + tự động Sidechain Ducking + Music Drop tại cú twist
- Tách đôi SFX: pop nhẹ đầu tin nhắn + SFX Reaction đánh ĐÚNG SAU PUNCHLINE
- Master 2-pass chuẩn -14.5 LUFS
- Xuất MP4: video_be_boi_audio_pro.mp4
"""

import json
import shutil
import subprocess
from pathlib import Path

from audio_engine_conbo import (
    DEFAULT_BGM,
    mix_conbo_audio,
    probe_duration,
    setup_ffmpeg,
    synthesize_dual_gender,
)

WORKSPACE = Path(__file__).resolve().parent
VOICES_DIR = WORKSPACE / "conbo_be_boi_voices"
FRAMES_DIR = WORKSPACE / "be_boi_audio_pro_frames"
OUTPUT_MP4 = WORKSPACE / "video_be_boi_audio_pro.mp4"

# Cặp giọng NAM / NỮ đã chốt chính thức (100% offline VieNeu, đồng chất miền Bắc)
MALE_VOICE = ("vieneu", "Adam bựa")
FEMALE_VOICE = ("vieneu", "Trúc Ly")

# Kịch bản tối ưu nhịp thở vừa phải (không ngợp mắt) + tách chuẩn gender Nam/Nữ + SFX đánh SAU punchline
ITEMS = [
    {
        "idx": 1, "kind": "msg", "side": "left", "code": "TE", "gender": "male",
        "sender": "Tùng em (Thiết kế)", "color": "#16a34a",
        "text": "SẾP ƠIIIIIIIIIII", "tts": "Sếp ơi!",
        "img": "assets/ep_be_boi/ho_mong_tram_can.jpg",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.08, "post_gap": 0.45,
    },
    {
        "idx": 2, "kind": "msg", "side": "left", "code": "TE", "gender": "male",
        "sender": "Tùng em (Thiết kế)", "color": "#16a34a",
        "text": "Đào hố gì thế sếp?", "tts": "Đào hố gì thế sếp?",
        "pop_sfx": "assets/sfx_pop.mp3",
        "after_sfx": "assets/sfx_pack/huh.mp3", "after_sfx_dur": 1.25, "after_sfx_vol": 0.68,
        "typing": False, "voice_delay": 0.08, "post_gap": 0.95,
    },
    {
        "idx": 3, "kind": "msg", "side": "left", "code": "SEP", "gender": "male",
        "sender": "Sếp", "color": "#1e3a8a",
        "text": "Bể bơi vô cực. Hè này cho ae tắm mát.",
        "tts": "Bể bơi vô cực, hè này cho anh em tắm mát!",
        "pop_sfx": "assets/sfx_pop.mp3",
        "after_sfx": "assets/sfx_pack/ding.mp3", "after_sfx_dur": 1.25, "after_sfx_vol": 0.58,
        "typing": False, "voice_delay": 0.08, "post_gap": 0.68,
    },
    {
        "idx": 4, "kind": "msg", "side": "left", "code": "TG", "gender": "female",
        "sender": "Trang (CSKH)", "color": "#db2777",
        "text": "Ối sếp đẹp trai thế!! 😍", "tts": "Ối, sếp đẹp trai thế!",
        "meme_gif": "assets/episode1_media/clap.gif",
        "pop_sfx": "assets/sfx_pop.mp3",
        "after_sfx": "assets/sfx_pack/wow.mp3", "after_sfx_dur": 1.45, "after_sfx_vol": 0.65,
        "typing": False, "voice_delay": 0.08, "post_gap": 1.08,
    },
    {
        "idx": 5, "kind": "msg", "side": "left", "code": "TH", "gender": "male",
        "sender": "Tiến Hải (CSKH)", "color": "#2563eb",
        "text": "Chị em mặc bikini nhé! Em xin chân cứu hộ",
        "tts": "Chị em mặc bi ki ni nhé, em xin chân cứu hộ!",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.08, "post_gap": 0.42,
    },
    {
        "idx": 6, "kind": "msg", "side": "left", "code": "KT", "gender": "female",
        "sender": "Thanh Hải (Kế toán)", "color": "#ea580c",
        "text": "Hố móng trạm cân 80 tấn. Bơi lội cái giề? 🙂",
        "tts": "Hố móng trạm cân tám mươi tấn, bơi lội cái giề?",
        "meme_gif": "assets/episode1_media/confused.gif",
        "pop_sfx": "assets/sfx_pop.mp3",
        "after_sfx": "assets/sfx_pack/bruh.mp3", "after_sfx_dur": 0.84, "after_sfx_vol": 0.82,
        "music_drop": True,
        "typing": True, "typing_dur": 0.25, "voice_delay": 0.08, "post_gap": 1.02,
    },
    {
        "idx": 7, "kind": "msg", "side": "left", "code": "SEP", "gender": "male",
        "sender": "Sếp", "color": "#1e3a8a",
        "text": "😂 Tối tan ca nhìn đường. Đứa nào lao xe xuống đấy thì tự múc đất chôn nhé.",
        "tts": "Tối tan ca nhìn đường, đứa nào lao xe xuống đấy thì tự múc đất chôn nhé!",
        "pop_sfx": "assets/sfx_pop.mp3",
        "after_sfx": "assets/sfx_pack/rimshot.mp3", "after_sfx_dur": 1.70, "after_sfx_vol": 0.72,
        "typing": False, "voice_delay": 0.08, "post_gap": 1.28,
    },
    {
        "idx": 8, "kind": "msg", "side": "left", "code": "TE", "gender": "male",
        "sender": "Tùng em (Thiết kế)", "color": "#16a34a",
        "text": "Mưa to 1 cái là thành bể bơi thật đấy sếp ơi.",
        "tts": "Mưa to một cái là thành bể bơi thật đấy sếp ơi.",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.08, "post_gap": 0.38,
    },
    {
        "idx": 9, "kind": "msg", "side": "left", "code": "SEP", "gender": "male",
        "sender": "Sếp", "color": "#1e3a8a",
        "text": "Mày chỉ toàn mồm thối! Tao xem dự báo rồi, tuần này nắng ráo.",
        "tts": "Mày chỉ toàn mồm thối, tao xem dự báo rồi, tuần này nắng ráo!",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.08, "post_gap": 0.42,
    },
    {
        "idx": 10, "kind": "sys_time",
        "text": "⏰ 21:00 ĐÊM — Trời đổ mưa như trút ⛈️",
        "after_sfx": "assets/ep_be_boi/clock_tick_rain.wav", "after_sfx_vol": 0.92,
        "music_drop": True,
        "hold": 1.80,
    },
    {
        "idx": 11, "kind": "msg", "side": "left", "code": "TH", "gender": "male",
        "sender": "Tiến Hải (CSKH)", "color": "#2563eb",
        "text": "CẤP BÁOOOOOOO!! 🌊😱", "tts": "Cấp báo!",
        "img": "assets/ep_be_boi/mua_ngap_ho.jpg",
        "meme_gif": "assets/episode1_media/shocked.gif",
        "after_sfx": "assets/sfx_pack/inception.mp3", "after_sfx_dur": 2.00, "after_sfx_vol": 0.82,
        "music_drop": True,
        "typing": False, "voice_delay": 0.08, "post_gap": 1.50,
    },
    {
        "idx": 12, "kind": "msg", "side": "left", "code": "SEP", "gender": "male",
        "sender": "Sếp", "color": "#1e3a8a",
        "text": "Thằng Tùng em đâu? Mai lên công ty mày biết tay tao!",
        "tts": "Thằng Tùng em đâu? Mai lên công ty mày biết tay tao!",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.08, "post_gap": 0.45,
    },
    {
        "idx": 13, "kind": "msg", "side": "left", "code": "TE", "gender": "male",
        "sender": "Tùng em (Thiết kế)", "color": "#16a34a",
        "text": "Em xin phép mai làm online tránh bão ạ 😭",
        "tts": "Em xin phép mai làm on lai tránh bão ạ!",
        "meme_gif": "assets/episode1_media/this_is_fine.gif",
        "pop_sfx": "assets/sfx_pop.mp3",
        "after_sfx": "assets/sfx_pack/metal_boom.mp3", "after_sfx_dur": 1.25, "after_sfx_vol": 0.78,
        "music_drop": True,
        "typing": True, "typing_dur": 0.24, "voice_delay": 0.08, "post_gap": 1.20,
    },
    {
        "idx": 14, "kind": "end_card", "code": "CTA", "gender": "female",
        "text": "Theo ae mai Tùng em có bị trừ lương ko? 😂👀",
        "tts": "Theo anh em, mai Tùng em có bị trừ lương không? Bình luận bên dưới nhé!",
        "meme_gif": "assets/episode1_media/shocked.gif",
        "after_sfx": "assets/sfx_pack/wow.mp3", "after_sfx_dur": 1.65, "after_sfx_vol": 0.62,
        "voice_delay": 0.08, "post_gap": 1.55,
    },
]


def _pick_h264_codec_args():
    try:
        enc_out = subprocess.check_output(["ffmpeg", "-encoders"], stderr=subprocess.STDOUT).decode(errors="ignore")
    except Exception:
        enc_out = ""
    if "libx264" in enc_out:
        return ["-c:v", "libx264", "-preset", "medium", "-crf", "19"]
    if "h264_mf" in enc_out:
        return ["-c:v", "h264_mf", "-b:v", "6M"]
    return ["-c:v", "mpeg4", "-q:v", "3"]


def main():
    setup_ffmpeg()
    print("=" * 68)
    print("🎙️ RENDER DEMO ÂM THANH CHUẨN CON BÒ ĐI LÀM (CÁCH 1)")
    print("=" * 68)

    # 1. Tổng hợp giọng tách chuẩn NAM / NỮ (giữ nguyên tốc độ đọc mượt, tự động trim silence)
    manifest_path = synthesize_dual_gender(
        items=ITEMS,
        out_dir=VOICES_DIR,
        male_spec=MALE_VOICE,
        female_spec=FEMALE_VOICE,
        end_card_spec=FEMALE_VOICE,
        edge_rate="+12%",
        vieneu_speed=1.10,
    )

    # 2. Chụp khung hình Center-Focus theo nhịp mới siêu gọn
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    subprocess.check_call(
        [
            "node",
            str(WORKSPACE / "render_be_boi_center_frames.js"),
            str(FRAMES_DIR),
            str(manifest_path),
        ]
    )

    items_by_idx = {it["idx"]: it for it in json.loads(manifest_path.read_text(encoding="utf-8"))}
    events = json.loads((FRAMES_DIR / "events_timeline.json").read_text(encoding="utf-8"))
    total_dur = sum(ev["duration"] for ev in events)
    print(f"  Tổng thời lượng nhịp mới: {total_dur:.2f}s ({len(events)} sự kiện)")

    # 3. Mix âm thanh chuẩn Con Bò (BGM + Ducking + Music Drop + After-SFX + 2-pass -14.5 LUFS)
    mixed_wav = FRAMES_DIR / "be_boi_audio_pro_mixed.wav"
    mix_conbo_audio(
        items_by_idx=items_by_idx,
        events=events,
        voices_dir=VOICES_DIR,
        output_wav=mixed_wav,
        total_dur=total_dur,
        bgm_path=DEFAULT_BGM,
        bgm_volume=0.24,
        voice_delay_sec=0.08,
    )

    # 4. Ghép video MP4
    concat_txt = FRAMES_DIR / "concat_pro.txt"
    tick = 0.085
    last_img = None
    with open(concat_txt, "w", encoding="utf-8") as f:
        f.write("ffconcat version 1.0\n")
        for ev in events:
            fs = ev["frames"]
            if len(fs) == 1:
                p = (FRAMES_DIR / fs[0]).as_posix()
                f.write(f"file '{p}'\n")
                f.write(f"duration {ev['duration']:.3f}\n")
                last_img = p
            else:
                rem = ev["duration"]
                fi = 0
                while rem > 0.005:
                    dt = min(tick, rem)
                    p = (FRAMES_DIR / fs[fi % len(fs)]).as_posix()
                    f.write(f"file '{p}'\n")
                    f.write(f"duration {dt:.3f}\n")
                    last_img = p
                    rem -= dt
                    fi += 1
        f.write(f"file '{last_img}'\n")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_txt),
            "-i",
            str(mixed_wav),
            *_pick_h264_codec_args(),
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-t",
            f"{total_dur:.2f}",
            "-movflags",
            "+faststart",
            str(OUTPUT_MP4),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    dur = probe_duration(OUTPUT_MP4)
    size_mb = OUTPUT_MP4.stat().st_size / (1024 * 1024)
    print(f"\n✅ HOÀN TẤT VIDEO AUDIO PRO: {OUTPUT_MP4} ({dur:.2f}s, {size_mb:.2f} MB)")


if __name__ == "__main__":
    main()

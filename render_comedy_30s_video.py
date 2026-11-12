#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Renderer: Video Hài Hước Văn Phòng Cửa Thép (~30s)
Chủ đề: Thuần giải trí - Test xe nâng húc cửa, búa tạ nảy ngược, kế toán đòi trừ 5 triệu, Sếp bao lẩu dê.
Tốc độ nói: 1.15x (chậm rãi, tự nhiên, rõ từng chữ, giữ trọn nhịp hài)
5 Tracks tích hợp: Nền Anime Sky + Khung Chat iPhone + SFX + Giọng ADAM & Nhân Vật + Subtitles
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

try:
    from gtts import gTTS
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "gTTS"])
    from gtts import gTTS

WORKSPACE = Path("/home/antigravity")
WORK_DIR = WORKSPACE / "comedy_30s_work"
WORK_DIR.mkdir(parents=True, exist_ok=True)

FRAMES_DIR = WORKSPACE / "render_30s_frames"
ASSETS_DIR = WORKSPACE / "capcut_projects" / "Cua_Thep_TikTok_Luxury" / "assets"
OUTPUT_MP4 = WORKSPACE / "video_mau_cua_thep_30s.mp4"

# 8 câu thoại kịch bản THUẦN GIẢI TRÍ
COMEDY_DIALOGUES = [
    {
        "id": "msg_1",
        "index": 1,
        "frame": "frame_1.png",
        "role": "sep",
        "text": "Hải Kỹ Thuật! Camera xưởng báo động đỏ! Cậu vừa lái xe nâng húc thẳng vào cửa chính công ty đấy à?!",
        "sfx": "sfx_pop.mp3",
        "speed": 1.15,
        "sub": "SẾP TỔNG: Cậu vừa lái xe nâng húc thẳng vào cửa chính đấy à?!"
    },
    {
        "id": "msg_2",
        "index": 2,
        "frame": "frame_2.png",
        "role": "hai",
        "text": "Oan cho em quá Sếp ơi! Em đang test độ bền cửa thép chịu lực mười tấn cho khách xem thôi mà!",
        "sfx": "sfx_ting.mp3",
        "speed": 1.15,
        "sub": "HẢI KT: Em đang test độ bền chịu lực 10 tấn thôi mà! 😅"
    },
    {
        "id": "msg_3",
        "index": 3,
        "frame": "frame_3.png",
        "role": "vy",
        "text": "Báo cáo Sếp: Xe nâng gãy đôi càng rồi ạ, còn cánh cửa thép thì đến một vết xước cũng không có!",
        "sfx": "sfx_ting.mp3",
        "speed": 1.15,
        "sub": "VY KẾ TOÁN: Xe nâng gãy đôi càng, cửa thì không một vết xước! 😂"
    },
    {
        "id": "msg_4",
        "index": 4,
        "frame": "frame_4.png",
        "role": "thang",
        "text": "Em vừa lấy búa tạ mười cân phang thử, búa nảy ngược lại suýt đập trúng trán em đây này Sếp!",
        "sfx": "sfx_ting.mp3",
        "speed": 1.15,
        "sub": "THẮNG: Búa tạ 10kg đập vào nảy ngược lại suýt trúng trán! 🔨"
    },
    {
        "id": "msg_5",
        "index": 5,
        "frame": "frame_5.png",
        "role": "hai",
        "text": "Cửa thép nhà mình thế này trộm vào chỉ có nước ngồi khóc xin ngụm nước rồi đi về thôi Sếp ạ!",
        "sfx": "sfx_ting.mp3",
        "speed": 1.15,
        "sub": "HẢI KT: Trộm vào chỉ có nước ngồi khóc xin nước rồi về! 🤣"
    },
    {
        "id": "msg_6",
        "index": 6,
        "frame": "frame_6.png",
        "role": "vy",
        "text": "Cửa đỉnh thật nhưng tiền sửa xe nâng năm triệu thì trừ vào lương anh Hải hay lương Sếp đây ạ?",
        "sfx": "sfx_ting.mp3",
        "speed": 1.15,
        "sub": "VY KẾ TOÁN: Tiền sửa xe nâng 5 triệu trừ lương ai đây ạ? 📝"
    },
    {
        "id": "msg_7",
        "index": 7,
        "frame": "frame_7.png",
        "role": "hai",
        "text": "Ủa em Vy?! Người cùng một nhà sao em quay xe khét lẹt vậy em?! Cứu em Sếp ơi!",
        "sfx": "sfx_ting.mp3",
        "speed": 1.15,
        "sub": "HẢI KT: Người một nhà sao em quay xe khét lẹt vậy em?! 😭"
    },
    {
        "id": "msg_8",
        "index": 8,
        "frame": "frame_8.png",
        "role": "sep",
        "text": "Trừ lương Hải! Nhưng tối nay Sếp bao cả xưởng nồi lẩu dê vì cửa quá đỉnh! Duyệt luôn!",
        "sfx": "sfx_pop.mp3",
        "speed": 1.15,
        "sub": "SẾP TỔNG: Trừ lương Hải! Nhưng tối nay Sếp bao lẩu dê cả xưởng! 👍"
    }
]

def synthesize_voices():
    print("[1/5] Tổng hợp giọng đọc tự nhiên (tốc độ chậm 1.15x, chuẩn ADAM & đa nhân vật)...")
    total_voice_dur = 0.0

    for d in COMEDY_DIALOGUES:
        raw_tts = WORK_DIR / f"raw_{d['id']}.mp3"
        filtered_tts = WORK_DIR / f"voice_{d['id']}.mp3"

        tts = gTTS(text=d["text"], lang="vi", slow=False)
        tts.save(str(raw_tts))

        role = d["role"]
        spd = d["speed"]
        if role == "sep":
            # ADAM style: Deep bass boost 120Hz + lower pitch formant
            flt = f"atempo={spd},asetrate=44100*0.93,aresample=44100,equalizer=f=120:width_type=o:width=1:g=5,volume=1.25"
        elif role == "vy":
            # Vy kế toán: Cheerful, clear female
            flt = f"atempo={spd},asetrate=44100*1.15,aresample=44100,volume=1.15"
        elif role == "thang":
            # Thắng công trình: Rugged contractor
            flt = f"atempo={spd},asetrate=44100*1.02,aresample=44100,volume=1.15"
        else: # hai
            # Hải kỹ thuật: Young technician
            flt = f"atempo={spd},asetrate=44100*1.04,aresample=44100,volume=1.15"

        cmd = [
            "ffmpeg", "-y", "-i", str(raw_tts),
            "-filter:a", flt,
            "-vn", str(filtered_tts)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        dur = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(filtered_tts)
        ]).decode().strip())

        d["voice_path"] = filtered_tts
        d["voice_dur"] = dur
        total_voice_dur += dur
        print(f"  - [{d['id']}] {role}: {dur:.2f}s -> {d['sub']}")

    print(f"  Tổng thời lượng giọng đọc: {total_voice_dur:.2f}s")
    return total_voice_dur

def calculate_timeline(total_voice_dur):
    print("[2/5] Tính toán timeline đồng bộ cho video ~30s...")
    TARGET_TOTAL = 31.00  # 31.0 giây chuẩn nhịp hài kịch
    INTRO_DUR = 0.40

    rem = TARGET_TOTAL - INTRO_DUR - total_voice_dur
    pause_per_step = max(0.12, rem / 8.0)

    timeline = []
    timeline.append({
        "frame": "frame_0.png",
        "start": 0.0,
        "duration": INTRO_DUR,
        "dialogue": None
    })

    curr = INTRO_DUR
    for i, d in enumerate(COMEDY_DIALOGUES):
        v_dur = d["voice_dur"]
        if i < len(COMEDY_DIALOGUES) - 1:
            step_dur = v_dur + pause_per_step
        else:
            step_dur = TARGET_TOTAL - curr

        d["start_time"] = curr
        timeline.append({
            "frame": d["frame"],
            "start": curr,
            "duration": step_dur,
            "dialogue": d
        })
        curr += step_dur

    print(f"  Khung 0: 0.00s -> {INTRO_DUR:.2f}s (Intro)")
    for item in timeline[1:]:
        d = item["dialogue"]
        print(f"  Khung {d['index']}: {item['start']:.2f}s -> {item['start']+item['duration']:.2f}s (Thoại: {d['voice_dur']:.2f}s)")
    total_dur = timeline[-1]["start"] + timeline[-1]["duration"]
    print(f"  Tổng thời lượng video: {total_dur:.2f}s")
    return timeline, total_dur

def render_composite_frames():
    print("[3/5] Render 9 khung hình composite 1080x1920 (Hi-Res Phone Mockup + Drop Shadow)...")
    bg_raw = Image.open(ASSETS_DIR / "bg_anime_sky.jpg").convert("RGBA")
    bg_base = bg_raw.resize((1080, 1920), Image.Resampling.LANCZOS)
    bg_base = bg_base.filter(ImageFilter.GaussianBlur(radius=3))
    darken = Image.new("RGBA", (1080, 1920), (0, 0, 0, 45))
    bg_base = Image.alpha_composite(bg_base, darken)

    phone_w, phone_h = 864, 1824
    px = (1080 - phone_w) // 2
    py = (1920 - phone_h) // 2

    mask = Image.new("L", (phone_w, phone_h), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([(0, 0), (phone_w, phone_h)], radius=42, fill=255)

    shadow_pad = 60
    shadow = Image.new("RGBA", (phone_w + shadow_pad * 2, phone_h + shadow_pad * 2), (0, 0, 0, 0))
    draw_shadow = ImageDraw.Draw(shadow)
    draw_shadow.rounded_rectangle(
        [(shadow_pad, shadow_pad + 14), (shadow_pad + phone_w, shadow_pad + phone_h + 14)],
        radius=44, fill=(0, 0, 0, 130)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=25))

    bezel = Image.new("RGBA", (phone_w + 6, phone_h + 6), (0, 0, 0, 0))
    draw_bezel = ImageDraw.Draw(bezel)
    draw_bezel.rounded_rectangle([(0, 0), (phone_w + 5, phone_h + 5)], radius=44, outline=(30, 41, 59, 255), width=3)

    for i in range(9):
        frame_name = f"frame_{i}.png"
        phone_src = FRAMES_DIR / frame_name
        phone_img = Image.open(phone_src).convert("RGBA")
        phone_resized = phone_img.resize((phone_w, phone_h), Image.Resampling.LANCZOS)

        canvas = bg_base.copy()
        canvas.paste(shadow, (px - shadow_pad, py - shadow_pad), shadow)
        canvas.paste(bezel, (px - 3, py - 3), bezel)
        canvas.paste(phone_resized, (px, py), mask)

        out_path = WORK_DIR / f"comp_{i}.png"
        canvas.convert("RGB").save(out_path, quality=98)
        print(f"  - Đã xuất composite: comp_{i}.png")

    print("  Hoàn tất render 9 khung hình composite!")

def build_audio_track(timeline, total_dur):
    print("[4/5] Trộn âm thanh đa kênh (SFX Ting/Pop + Giọng ADAM & Nhân Vật)...")
    inputs = []
    filter_complex = []
    input_idx = 0

    for item in timeline[1:]:
        d = item["dialogue"]
        start_ms = int(d["start_time"] * 1000)

        # 1. SFX
        sfx_path = ASSETS_DIR / d["sfx"]
        inputs.extend(["-i", str(sfx_path)])
        filter_complex.append(f"[{input_idx}:a]adelay={start_ms}|{start_ms},volume=1.0[sfx_{d['index']}];")
        input_idx += 1

        # 2. Voiceover
        voice_path = d["voice_path"]
        inputs.extend(["-i", str(voice_path)])
        voice_start_ms = start_ms + 40
        filter_complex.append(f"[{input_idx}:a]adelay={voice_start_ms}|{voice_start_ms},volume=1.25[voc_{d['index']}];")
        input_idx += 1

    all_labels = []
    for item in timeline[1:]:
        idx = item["dialogue"]["index"]
        all_labels.append(f"[sfx_{idx}]")
        all_labels.append(f"[voc_{idx}]")

    num_streams = len(all_labels)
    filter_str = "".join(filter_complex) + f"{''.join(all_labels)}amix=inputs={num_streams}:duration=longest:dropout_transition=0,volume=1.35[aout]"

    audio_out = WORK_DIR / "comedy_mixed_audio.wav"
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[aout]",
        "-t", f"{total_dur:.2f}",
        "-ar", "44100",
        "-ac", "2",
        str(audio_out)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"  Đã trộn âm thanh hoàn tất: {audio_out}")
    return audio_out

def render_final_video(timeline, audio_path, total_dur):
    print("[5/5] Mã hóa Video MP4 1080x1920 30fps bằng ffmpeg...")
    concat_txt = WORK_DIR / "concat_comedy.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        f.write("ffconcat version 1.0\n")
        for item in timeline:
            f.write(f"file '{WORK_DIR / ('comp_' + item['frame'].replace('frame_', ''))}'\n")
            f.write(f"duration {item['duration']:.3f}\n")
        f.write(f"file '{WORK_DIR / ('comp_' + timeline[-1]['frame'].replace('frame_', ''))}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "19",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{total_dur:.2f}",
        "-movflags", "+faststart",
        str(OUTPUT_MP4)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    dur = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(OUTPUT_MP4)
    ]).decode().strip()
    size_mb = OUTPUT_MP4.stat().st_size / (1024 * 1024)

    print("=" * 60)
    print("🎬 RENDER VIDEO HÀI HƯỚC CỬA THÉP 30S HOÀN TẤT XUẤT SẮC!")
    print(f"📁 Đường dẫn: {OUTPUT_MP4}")
    print(f"⏱️ Thời lượng: {float(dur):.2f} giây")
    print(f"💾 Dung lượng: {size_mb:.2f} MB")
    print("=" * 60)

if __name__ == "__main__":
    dur = synthesize_voices()
    tl, total_dur = calculate_timeline(dur)
    render_composite_frames()
    aud = build_audio_track(tl, total_dur)
    render_final_video(tl, aud, total_dur)

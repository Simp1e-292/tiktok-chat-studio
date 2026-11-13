#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Renderer: Video Mẫu Cửa Thép Luxury 30s
Render video chuẩn TikTok 1080x1920 30fps với:
- 5 Tracks tích hợp: Nền Anime Sky + Khung Chat iPhone Retina + SFX + Giọng ADAM & Đa Nhân Vật + Subtitles
- Thời lượng chuẩn xác 30.0 giây
- Mã hóa H.264 / AAC tương thích 100% mọi thiết bị
"""

import os
import sys
import json
import math
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


def _setup_capcut_ffmpeg_path():
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    local_apps = Path(os.path.expandvars(r"%LOCALAPPDATA%\CapCut\Apps"))
    if local_apps.is_dir():
        for exe in sorted(local_apps.rglob("ffmpeg.exe"), reverse=True):
            tool_dir = str(exe.parent)
            if tool_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = tool_dir + os.pathsep + os.environ.get("PATH", "")
            break


_setup_capcut_ffmpeg_path()

WORKSPACE = Path(__file__).resolve().parent
WORK_DIR = WORKSPACE / "render_30s"
WORK_DIR.mkdir(parents=True, exist_ok=True)

ASSETS_DIR = WORKSPACE / "capcut_projects" / "Cua_Thep_TikTok_Luxury" / "assets"
OUTPUT_MP4 = WORKSPACE / "video_mau_cua_thep_30s.mp4"

# 8 tin nhắn kịch bản
DIALOGUES = [
    {
        "id": "msg_1",
        "index": 1,
        "frame": "frame_1.png",
        "role": "sep",
        "src_voice": "voice_1_sep.mp3",
        "sfx": "sfx_pop.mp3",
        "speed": 1.44,
        "sub": "SẾP TỔNG: Nghiệm thu biệt thự Vinhome 50 bộ Cửa Thép thế nào rồi?!"
    },
    {
        "id": "msg_2",
        "index": 2,
        "frame": "frame_2.png",
        "role": "hai",
        "src_voice": "voice_2_hai.mp3",
        "sfx": "sfx_ting.mp3",
        "speed": 1.44,
        "sub": "HẢI KỸ THUẬT: Đập búa tạ 5kg mỏi tay không móp một ly!"
    },
    {
        "id": "msg_3",
        "index": 3,
        "frame": "frame_3.png",
        "role": "hai",
        "src_voice": "voice_3_hai.mp3",
        "sfx": "sfx_ting.mp3",
        "speed": 1.44,
        "sub": "HẢI: Đèn khò 1000°C gioăng chống cháy nở kín mít!"
    },
    {
        "id": "msg_4",
        "index": 4,
        "frame": "frame_4.png",
        "role": "vy",
        "src_voice": "voice_4_vy.mp3",
        "sfx": "sfx_ting.mp3",
        "speed": 1.44,
        "sub": "VY DỰ ÁN: Khách bắn cọc 350 triệu chốt thêm 80 bộ nữa! 🎉"
    },
    {
        "id": "msg_5",
        "index": 5,
        "frame": "frame_5.png",
        "role": "narrator",
        "src_voice": "voice_5_narrator.mp3",
        "sfx": "sfx_ting.mp3",
        "speed": 1.46,
        "sub": "⭐ CỬA THÉP VÂN GỖ 90P - KHÓA FACE ID CAO CẤP ⭐"
    },
    {
        "id": "msg_6",
        "index": 6,
        "frame": "frame_6.png",
        "role": "thang",
        "src_voice": "voice_6_thang.mp3",
        "sfx": "sfx_ting.mp3",
        "speed": 1.44,
        "sub": "THẮNG: Đang chở phụ kiện tới lắp hoàn thiện cho khách!"
    },
    {
        "id": "msg_7",
        "index": 7,
        "frame": "frame_7.png",
        "role": "hai",
        "src_voice": "voice_7_hai.mp3",
        "sfx": "sfx_ting.mp3",
        "speed": 1.44,
        "sub": "HẢI: Chiều nay Sếp có khao xưởng lẩu dê bia không?!"
    },
    {
        "id": "msg_8",
        "index": 8,
        "frame": "frame_8.png",
        "role": "sep",
        "src_voice": "voice_8_sep.mp3",
        "sfx": "sfx_pop.mp3",
        "speed": 1.42,
        "sub": "SẾP TỔNG: Duyệt luôn! Cả xưởng chuẩn bị liên hoan nhé! 👍"
    }
]

def prepare_voices():
    print("[1/5] Xử lý âm thanh giọng đọc tối ưu cho thời lượng 30s...")
    voice_files = []
    total_voice_dur = 0.0

    for d in DIALOGUES:
        src = ASSETS_DIR / d["src_voice"]
        dst = WORK_DIR / f"fast_{d['src_voice']}"
        speed = d["speed"]
        
        cmd = [
            "ffmpeg", "-y", "-i", str(src),
            "-filter:a", f"atempo={speed}",
            "-vn", str(dst)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        probe = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(dst)
        ]).decode().strip()
        dur = float(probe)
        d["voice_path"] = dst
        d["voice_dur"] = dur
        total_voice_dur += dur
        voice_files.append((d["id"], dur))
        print(f"  - [{d['id']}] {d['role']}: {dur:.2f}s (tốc độ {speed}x)")
    
    print(f"  Tổng thời lượng giọng đọc: {total_voice_dur:.2f}s")
    return total_voice_dur

def calculate_timeline(total_voice_dur):
    print("[2/5] Tính toán timeline đồng bộ chính xác 30.00 giây...")
    TARGET_TOTAL = 30.00
    INTRO_DUR = 0.40
    
    # 7 khoảng nghỉ giữa 8 câu thoại
    # Remaining time distributed among pauses and outro
    rem = TARGET_TOTAL - INTRO_DUR - total_voice_dur
    pause_per_step = max(0.04, rem / 8.0)
    outro_dur = max(0.2, rem - (pause_per_step * 7.0))
    
    timeline = []
    # Frame 0: Intro
    timeline.append({
        "frame": "frame_0.png",
        "start": 0.0,
        "duration": INTRO_DUR,
        "dialogue": None
    })
    
    curr = INTRO_DUR
    for i, d in enumerate(DIALOGUES):
        v_dur = d["voice_dur"]
        # Duration this frame is displayed
        if i < len(DIALOGUES) - 1:
            step_dur = v_dur + pause_per_step
        else:
            step_dur = TARGET_TOTAL - curr # Exact match to 30.0s
            
        d["start_time"] = curr
        timeline.append({
            "frame": d["frame"],
            "start": curr,
            "duration": step_dur,
            "dialogue": d
        })
        curr += step_dur
        
    print(f"  Khung hình 0: 0.00s -> {INTRO_DUR:.2f}s (Intro)")
    for item in timeline[1:]:
        d = item["dialogue"]
        print(f"  Khung hình {d['index']}: {item['start']:.2f}s -> {item['start']+item['duration']:.2f}s (Thoại: {d['voice_dur']:.2f}s)")
    print(f"  Tổng thời lượng timeline: {timeline[-1]['start'] + timeline[-1]['duration']:.2f}s")
    return timeline

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

    # Mask bo góc điện thoại
    mask = Image.new("L", (phone_w, phone_h), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([(0, 0), (phone_w, phone_h)], radius=42, fill=255)

    # Đổ bóng mềm sang trọng (Soft Ambient Drop Shadow)
    shadow_pad = 60
    shadow = Image.new("RGBA", (phone_w + shadow_pad * 2, phone_h + shadow_pad * 2), (0, 0, 0, 0))
    draw_shadow = ImageDraw.Draw(shadow)
    draw_shadow.rounded_rectangle(
        [(shadow_pad, shadow_pad + 14), (shadow_pad + phone_w, shadow_pad + phone_h + 14)],
        radius=44, fill=(0, 0, 0, 130)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=25))

    # Viền kim loại Titanium siêu mỏng
    bezel = Image.new("RGBA", (phone_w + 6, phone_h + 6), (0, 0, 0, 0))
    draw_bezel = ImageDraw.Draw(bezel)
    draw_bezel.rounded_rectangle([(0, 0), (phone_w + 5, phone_h + 5)], radius=44, outline=(30, 41, 59, 255), width=3)

    for i in range(9):
        frame_name = f"frame_{i}.png"
        phone_src = ASSETS_DIR / frame_name
        phone_img = Image.open(phone_src).convert("RGBA")
        phone_resized = phone_img.resize((phone_w, phone_h), Image.Resampling.LANCZOS)

        canvas = bg_base.copy()
        # Paste shadow
        canvas.paste(shadow, (px - shadow_pad, py - shadow_pad), shadow)
        # Paste bezel
        canvas.paste(bezel, (px - 3, py - 3), bezel)
        # Paste phone
        canvas.paste(phone_resized, (px, py), mask)

        out_path = WORK_DIR / f"comp_{i}.png"
        canvas.convert("RGB").save(out_path, quality=98)
        print(f"  - Đã xuất composite: comp_{i}.png")
    
    print("  Hoàn tất render 9 khung hình composite!")

def build_audio_track(timeline):
    print("[4/5] Trộn âm thanh đa kênh (SFX + Giọng ADAM & Nhân Vật)...")
    # Danh sách các luồng âm thanh
    inputs = []
    filter_complex = []
    input_idx = 0

    # Duyệt qua các câu thoại để thêm SFX và Voiceover vào đúng timestamp
    for item in timeline[1:]:
        d = item["dialogue"]
        start_ms = int(d["start_time"] * 1000)

        # 1. SFX
        sfx_path = ASSETS_DIR / d["sfx"]
        inputs.extend(["-i", str(sfx_path)])
        # Delay sfx
        filter_complex.append(f"[{input_idx}:a]adelay={start_ms}|{start_ms},volume=1.0[sfx_{d['index']}];")
        input_idx += 1

        # 2. Voiceover
        voice_path = d["voice_path"]
        inputs.extend(["-i", str(voice_path)])
        # Voice bắt đầu sau sfx 40ms cho tự nhiên
        voice_start_ms = start_ms + 40
        filter_complex.append(f"[{input_idx}:a]adelay={voice_start_ms}|{voice_start_ms},volume=1.25[voc_{d['index']}];")
        input_idx += 1

    # Gom tất cả luồng lại để amix
    all_labels = []
    for item in timeline[1:]:
        idx = item["dialogue"]["index"]
        all_labels.append(f"[sfx_{idx}]")
        all_labels.append(f"[voc_{idx}]")

    num_streams = len(all_labels)
    filter_str = "".join(filter_complex) + f"{''.join(all_labels)}amix=inputs={num_streams}:duration=longest:dropout_transition=0,volume=1.4[aout]"

    audio_out = WORK_DIR / "final_mixed_audio.wav"
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[aout]",
        "-t", "30.0",
        "-ar", "44100",
        "-ac", "2",
        str(audio_out)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"  Đã trộn âm thanh hoàn tất: {audio_out}")
    return audio_out

def _pick_h264_codec_args():
    try:
        enc_out = subprocess.check_output(["ffmpeg", "-encoders"], stderr=subprocess.STDOUT).decode(errors="ignore")
    except Exception:
        enc_out = ""
    if "libx264" in enc_out:
        return ["-c:v", "libx264", "-preset", "medium", "-crf", "19"]
    if "h264_mf" in enc_out:
        return ["-c:v", "h264_mf", "-b:v", "5M"]
    return ["-c:v", "mpeg4", "-q:v", "3"]


def render_final_video(timeline, audio_path):
    print("[5/5] Mã hóa Video MP4 1080x1920 30fps hoàn chỉnh bằng ffmpeg...")
    concat_txt = WORK_DIR / "concat_video.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        f.write("ffconcat version 1.0\n")
        for item in timeline:
            img_p = (WORK_DIR / ('comp_' + item['frame'].replace('frame_', ''))).as_posix()
            f.write(f"file '{img_p}'\n")
            f.write(f"duration {item['duration']:.3f}\n")
        # Concat demuxer requirement: repeat last file without duration
        last_p = (WORK_DIR / ('comp_' + timeline[-1]['frame'].replace('frame_', ''))).as_posix()
        f.write(f"file '{last_p}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-i", str(audio_path),
        *_pick_h264_codec_args(),
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", "30.0",
        "-movflags", "+faststart",
        str(OUTPUT_MP4)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Probe output
    dur = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(OUTPUT_MP4)
    ]).decode().strip()
    size_mb = OUTPUT_MP4.stat().st_size / (1024 * 1024)

    print("=" * 60)
    print("🎬 RENDER VIDEO 30S HOÀN TẤT XUẤT SẮC!")
    print(f"📁 Đường dẫn: {OUTPUT_MP4}")
    print(f"⏱️ Thời lượng: {float(dur):.2f} giây")
    print(f"💾 Dung lượng: {size_mb:.2f} MB")
    print("=" * 60)

if __name__ == "__main__":
    dur = prepare_voices()
    tl = calculate_timeline(dur)
    render_composite_frames()
    aud = build_audio_track(tl)
    render_final_video(tl, aud)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Renderer: Xuất Video MP4 Trực Tiếp 1080x1920 30fps (H.264/AAC)
Hỗ trợ CẢ kịch bản mặc định (Chốt Cọc Cửa Thép) LẪN bất kỳ kịch bản JSON nào từ Web Studio!
- Tích hợp khung điện thoại bo góc trong suốt + Drop Shadow + Ti viễn mượt trên nền Anime Sky / Custom
- Âm thanh đa kênh: SFX Ting/Pop + Lồng tiếng 1.0x chuẩn từng nhân vật
"""

import os
import re
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

from capcut_draft_generator import (
    WORKSPACE,
    ASSETS_DIR,
    setup_capcut_ffmpeg_path,
    clean_desktop_ini,
    normalize_scenario_items,
    ensure_frames_and_assets,
    calculate_synced_timeline,
    pick_h264_codec_args,
)

setup_capcut_ffmpeg_path()

DEFAULT_WORK_DIR = WORKSPACE / "chotcoc_work"
DEFAULT_OUTPUT_MP4 = ASSETS_DIR / "video_mau_cua_thep_30s.mp4"


def render_composite_frames(assets_dir: Path, work_dir: Path, timeline_steps: list):
    """Render từng khung hình composite 1080x1920 (Hi-Res Phone Mockup + Ambient Drop Shadow)"""
    print("[3/5] Render khung hình composite 1080x1920 (Hi-Res Phone Mockup + Drop Shadow)...")
    work_dir.mkdir(parents=True, exist_ok=True)

    bg_canvas_path = assets_dir / "bg_canvas_1080x1920.jpg"
    if not bg_canvas_path.exists():
        bg_canvas_path = ASSETS_DIR / "bg_anime_sky.jpg"
    bg_raw = Image.open(bg_canvas_path).convert("RGBA")
    bg_base = bg_raw.resize((1080, 1920), Image.Resampling.LANCZOS)

    phone_w, phone_h = 864, 1824
    px = (1080 - phone_w) // 2
    py = (1920 - phone_h) // 2

    mask = Image.new("L", (phone_w, phone_h), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([(0, 0), (phone_w, phone_h)], radius=29, fill=255)

    shadow_pad = 64
    shadow = Image.new("RGBA", (phone_w + shadow_pad * 2, phone_h + shadow_pad * 2), (0, 0, 0, 0))
    draw_shadow = ImageDraw.Draw(shadow)
    draw_shadow.rounded_rectangle(
        [(shadow_pad, shadow_pad + 16), (shadow_pad + phone_w, shadow_pad + phone_h + 16)],
        radius=32,
        fill=(0, 0, 0, 140),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=24))

    rendered_names = set()
    for step in timeline_steps:
        frame_name = step["frame"]
        if frame_name in rendered_names:
            continue
        rendered_names.add(frame_name)

        phone_src = assets_dir / frame_name
        phone_img = Image.open(phone_src).convert("RGBA")
        phone_resized = phone_img.resize((phone_w, phone_h), Image.Resampling.LANCZOS)

        # Kết hợp alpha channel gốc từ Chromium với mask bo góc để viền mịn tuyệt đối
        r_ch, g_ch, b_ch, a_ch = phone_resized.split()
        from PIL import ImageChops
        merged_alpha = ImageChops.darker(a_ch, mask)
        phone_masked = Image.merge("RGBA", (r_ch, g_ch, b_ch, merged_alpha))

        canvas = bg_base.copy()
        canvas = Image.alpha_composite(canvas, _paste_rgba_full(canvas.size, shadow, (px - shadow_pad, py - shadow_pad)))
        canvas.paste(phone_masked, (px, py), phone_masked)

        out_path = work_dir / f"comp_{frame_name}"
        canvas.convert("RGB").save(out_path, quality=96)
        print(f"  - Đã xuất composite: comp_{frame_name}")

    print(f"  Hoàn tất render {len(rendered_names)} khung hình composite!")


def _paste_rgba_full(size, overlay, offset):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    layer.paste(overlay, offset)
    return layer


def _amix_supports_normalize() -> bool:
    try:
        out = subprocess.check_output(["ffmpeg", "-h", "filter=amix"], stderr=subprocess.STDOUT).decode(errors="ignore")
        return "normalize" in out
    except Exception:
        return False


def build_audio_track(assets_dir: Path, work_dir: Path, timeline_steps: list, total_dur_s: float) -> Path:
    """Trộn âm thanh đa kênh (SFX Ting/Pop + Voiceover 1.0x)"""
    print("[4/5] Trộn âm thanh đa kênh (SFX Ting/Pop + Giọng Lồng Tiếng 1.0x)...")
    work_dir.mkdir(parents=True, exist_ok=True)
    audio_out = work_dir / "chotcoc_mixed_audio.wav"

    inputs = []
    filter_complex = []
    all_labels = []
    input_idx = 0

    for step in timeline_steps[1:]:
        start_ms = int(round(step["start_us"] / 1000.0))
        idx = step["index"]

        sfx_name = step.get("sfx")
        if sfx_name:
            sfx_path = assets_dir / sfx_name
            if sfx_path.exists():
                inputs.extend(["-i", str(sfx_path)])
                filter_complex.append(f"[{input_idx}:a]adelay={start_ms}|{start_ms},volume=0.85[sfx_{idx}];")
                all_labels.append(f"[sfx_{idx}]")
                input_idx += 1

        voice_name = step.get("voice")
        if voice_name:
            voice_path = assets_dir / voice_name
            if voice_path.exists():
                inputs.extend(["-i", str(voice_path)])
                voice_start_ms = start_ms + 40
                filter_complex.append(f"[{input_idx}:a]adelay={voice_start_ms}|{voice_start_ms},volume=1.15[voc_{idx}];")
                all_labels.append(f"[voc_{idx}]")
                input_idx += 1

    if not all_labels:
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", f"{total_dur_s:.3f}", str(audio_out),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return audio_out

    num_streams = len(all_labels)
    if num_streams == 1:
        label = all_labels[0]
        filter_str = "".join(filter_complex).rstrip(";")
        # Rename single label to [aout]
        last_tag = label
        filter_str = filter_str[:-len(last_tag)] + "[aout]"
    elif _amix_supports_normalize():
        filter_str = (
            "".join(filter_complex)
            + f"{''.join(all_labels)}amix=inputs={num_streams}:duration=longest:dropout_transition=0:normalize=0,alimiter=limit=0.95[aout]"
        )
    else:
        gain = max(1.25, min(float(num_streams) * 0.65, 4.0))
        filter_str = (
            "".join(filter_complex)
            + f"{''.join(all_labels)}amix=inputs={num_streams}:duration=longest:dropout_transition=0,volume={gain:.2f}[aout]"
        )

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[aout]",
        "-t", f"{total_dur_s:.3f}",
        "-ar", "44100",
        "-ac", "2",
        str(audio_out),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"  Đã trộn âm thanh hoàn tất: {audio_out}")
    return audio_out


def render_final_video(work_dir: Path, timeline_steps: list, audio_path: Path, total_dur_s: float, output_mp4: Path):
    """Mã hóa Video MP4 1080x1920 30fps bằng ffmpeg"""
    print("[5/5] Mã hóa Video MP4 1080x1920 30fps bằng ffmpeg...")
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    concat_txt = work_dir / "concat_chotcoc.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        f.write("ffconcat version 1.0\n")
        for step in timeline_steps:
            img_p = (work_dir / f"comp_{step['frame']}").as_posix()
            dur_s = step["duration_us"] / 1000000.0
            f.write(f"file '{img_p}'\n")
            f.write(f"duration {dur_s:.4f}\n")
        last_p = (work_dir / f"comp_{timeline_steps[-1]['frame']}").as_posix()
        f.write(f"file '{last_p}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-i", str(audio_path),
        "-vf", "fps=30,format=yuv420p",
        *pick_h264_codec_args(),
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{total_dur_s:.3f}",
        "-movflags", "+faststart",
        str(output_mp4),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    try:
        dur = float(
            subprocess.check_output([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(output_mp4),
            ]).decode().strip()
        )
    except Exception:
        dur = total_dur_s
    size_mb = output_mp4.stat().st_size / (1024 * 1024)

    print("=" * 60)
    print("🎬 RENDER VIDEO MP4 1080x1920 HOÀN TẤT XUẤT SẮC!")
    print(f"📁 Đường dẫn: {output_mp4}")
    print(f"⏱️ Thời lượng: {dur:.2f} giây")
    print(f"💾 Dung lượng: {size_mb:.2f} MB")
    print("=" * 60)
    return {"output_mp4": output_mp4, "duration_s": dur, "size_mb": size_mb}


def render_mp4_video(
    scenario_data: dict = None,
    characters: list = None,
    output_mp4: Path = DEFAULT_OUTPUT_MP4,
    work_dir: Path = None,
    force_render_frames: bool = False,
):
    """Hàm API chính để xuất Video MP4 1080x1920 từ kịch bản mặc định hoặc Web Studio JSON"""
    clean_desktop_ini(WORKSPACE)
    w_dir = work_dir or DEFAULT_WORK_DIR
    w_dir.mkdir(parents=True, exist_ok=True)
    assets_sub = w_dir / "assets"

    dialogue_items, theme, wallpaper = normalize_scenario_items(scenario_data, characters)

    payload_tmp = None
    if scenario_data is not None:
        payload_tmp = w_dir / "_render_payload.json"
        payload_tmp.write_text(
            json.dumps({"scenario": scenario_data, "characters": characters or []}, ensure_ascii=False),
            encoding="utf-8",
        )
        force_render_frames = True
    else:
        # Tận dụng lại các frame & voice sẵn có của Cửa Thép nếu vừa generate bên capcut_projects
        capcut_default_assets = WORKSPACE / "capcut_projects" / "Cua_Thep_TikTok_Luxury" / "assets"
        if capcut_default_assets.is_dir() and not force_render_frames:
            assets_sub.mkdir(parents=True, exist_ok=True)
            for src in capcut_default_assets.glob("*"):
                if src.is_file():
                    shutil.copy2(src, assets_sub / src.name)

    ensure_frames_and_assets(
        assets_sub,
        dialogue_items=dialogue_items,
        theme=theme,
        wallpaper=wallpaper,
        scenario_payload_path=payload_tmp,
        force_render_frames=force_render_frames,
    )

    if payload_tmp and payload_tmp.exists():
        payload_tmp.unlink(missing_ok=True)

    timeline_steps, total_duration_us = calculate_synced_timeline(assets_sub, dialogue_items)
    total_dur_s = total_duration_us / 1000000.0

    render_composite_frames(assets_sub, w_dir, timeline_steps)
    audio_path = build_audio_track(assets_sub, w_dir, timeline_steps, total_dur_s)
    return render_final_video(w_dir, timeline_steps, audio_path, total_dur_s, Path(output_mp4))


def main():
    parser = argparse.ArgumentParser(description="Render MP4 1080x1920 - TikTok Chat Studio")
    parser.add_argument("--scenario", help="Đường dẫn tới file JSON kịch bản xuất từ Web Studio")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_MP4), help="Đường dẫn file .mp4 đầu ra")
    parser.add_argument("--force-render", action="store_true", help="Render lại toàn bộ frames PNG từ trình duyệt")
    args = parser.parse_args()

    scenario_data = None
    characters = None
    if args.scenario:
        raw = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "scenario" in raw:
            scenario_data = raw["scenario"]
            characters = raw.get("characters")
        else:
            scenario_data = raw

    render_mp4_video(
        scenario_data=scenario_data,
        characters=characters,
        output_mp4=Path(args.output),
        force_render_frames=args.force_render,
    )


if __name__ == "__main__":
    main()

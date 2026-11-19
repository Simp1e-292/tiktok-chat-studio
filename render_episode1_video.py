#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video & CapCut Draft Renderer: Tập 1 - "Cánh Cửa Khắc Tên Crush"
- Sử dụng 13 file giọng đọc ElevenLabs (eleven_multilingual_v2) trong elevenlabs_episode1_voices/
- Render 14 khung hình chat Messenger Retina qua Chrome Headless (render_episode1_frames.js)
- Ghép nền Anime Sky + khung iPhone Titanium + Hook 3 giây đầu + CTA Tập 2
- Xuất video MP4 hoàn chỉnh: video_tap_01_cua_khac_ten_crush.mp4
- Tự động đóng gói bản CapCut Desktop 4 Tracks: Cua_Thep_Tap_01_Crush
"""

import os
import sys
import json
import uuid
import stat
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont


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

# Robust rmtree for Windows (Google Drive desktop.ini)
_orig_rmtree = shutil.rmtree
def _safe_rmtree(path, *args, **kwargs):
    def on_err(func, p, exc):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except Exception:
            pass
    if sys.version_info >= (3, 12):
        kwargs.setdefault("onexc", on_err)
    else:
        kwargs.setdefault("onerror", on_err)
    try:
        return _orig_rmtree(path, *args, **kwargs)
    except Exception:
        subprocess.run(f'attrib -r -h -s "{path}" /s /d', shell=True, capture_output=True)
        return _orig_rmtree(path, *args, **kwargs)
shutil.rmtree = _safe_rmtree

WORKSPACE = Path(__file__).resolve().parent
ASSETS_DIR = WORKSPACE / "assets"
VOICES_DIR = WORKSPACE / "vieneu_episode1_voices"
FRAMES_DIR = WORKSPACE / "episode1_frames"
WORK_DIR = WORKSPACE / "episode1_work"
WORK_DIR.mkdir(parents=True, exist_ok=True)

MANIFEST_PATH = VOICES_DIR / "manifest.json"
OUTPUT_MP4 = WORKSPACE / "video_tap_01_cua_khac_ten_crush.mp4"
PROJECT_NAME = "Cua_Thep_Tap_01_Crush"


def _pick_h264_codec_args():
    try:
        enc_out = subprocess.check_output(["ffmpeg", "-encoders"], stderr=subprocess.STDOUT).decode(errors="ignore")
    except Exception:
        enc_out = ""
    if "libx264" in enc_out:
        return ["-c:v", "libx264", "-preset", "medium", "-crf", "19"]
    if "h264_mf" in enc_out:
        return ["-c:v", "h264_mf", "-b:v", "6M"]
    if "h264_nvenc" in enc_out:
        return ["-c:v", "h264_nvenc", "-b:v", "6M"]
    return ["-c:v", "mpeg4", "-q:v", "3"]


def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int):
    words = text.split()
    lines = []
    curr = []
    for w in words:
        test = " ".join(curr + [w])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_w or not curr:
            curr.append(w)
        else:
            lines.append(" ".join(curr))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))
    return lines


def _draw_top_banner(canvas: Image.Image, text: str, bg_color, border_color, text_color=(255, 255, 255), font_size=36):
    draw = ImageDraw.Draw(canvas, "RGBA")
    font = _load_font(font_size, bold=True)
    max_text_w = 880
    lines = _wrap_text(draw, text, font, max_text_w)

    line_heights = []
    max_line_w = 0
    for ln in lines:
        bb = draw.textbbox((0, 0), ln, font=font)
        w = bb[2] - bb[0]
        h = bb[3] - bb[1]
        max_line_w = max(max_line_w, w)
        line_heights.append(h)

    line_gap = 10
    total_text_h = sum(line_heights) + line_gap * max(0, len(lines) - 1)
    pad_x, pad_y = 38, 18
    box_w = min(980, max_line_w + pad_x * 2)
    box_h = total_text_h + pad_y * 2

    x0 = (1080 - box_w) // 2
    y0 = max(24, (155 - box_h) // 2)
    x1 = x0 + box_w
    y1 = y0 + box_h

    draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=24, fill=bg_color, outline=border_color, width=3)

    curr_y = y0 + pad_y - 3
    for idx, ln in enumerate(lines):
        bb = draw.textbbox((0, 0), ln, font=font)
        lw = bb[2] - bb[0]
        lx = (1080 - lw) // 2
        draw.text((lx, curr_y), ln, font=font, fill=text_color)
        curr_y += line_heights[idx] + line_gap


def ensure_frames():
    expected = [FRAMES_DIR / f"frame_{i}.png" for i in range(14)]
    if all(p.exists() and p.stat().st_size > 1000 for p in expected):
        print("[1/5] Đã có sẵn 14 khung hình PNG trong episode1_frames/.")
        return
    print("[1/5] Đang render 14 khung hình chat Retina bằng Chrome...")
    subprocess.check_call([
        "node",
        str(WORKSPACE / "render_episode1_frames.js"),
        str(FRAMES_DIR),
        str(MANIFEST_PATH),
    ])


def load_timeline():
    print("[2/5] Tính toán timeline khớp 13 giọng đọc VieNeu-TTS...")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        messages = json.load(f)

    INTRO_DUR = 0.50
    PAUSE_BETWEEN = 0.22
    OUTRO_PAD = 0.55

    timeline = [{
        "index": 0,
        "frame": "frame_0.png",
        "start": 0.0,
        "duration": INTRO_DUR,
        "msg": None,
        "voice_path": None,
        "sfx_path": None,
    }]

    curr = INTRO_DUR
    for i, m in enumerate(messages, start=1):
        v_path = VOICES_DIR / m["audio_file"]
        dur = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(v_path)
        ]).decode().strip())
        m["duration_sec"] = dur

        step_dur = dur + (OUTRO_PAD if i == len(messages) else PAUSE_BETWEEN)
        sfx_key = m.get("sfx", "ting")
        sfx_name = "sfx_pop.mp3" if sfx_key in ("pop", "special") else "sfx_ting.mp3"

        timeline.append({
            "index": i,
            "frame": f"frame_{i}.png",
            "start": curr,
            "duration": step_dur,
            "msg": m,
            "voice_path": v_path,
            "voice_dur": dur,
            "sfx_path": ASSETS_DIR / sfx_name,
        })
        print(f"  - [{i:02d}] {m['senderName']}: {curr:.2f}s -> {curr + step_dur:.2f}s (thoại {dur:.2f}s)")
        curr += step_dur

    total_dur = curr
    print(f"  Tổng thời lượng Tập 1: {total_dur:.2f} giây")
    return timeline, total_dur


def render_composite_frames():
    print("[3/5] Ghép 14 khung hình composite 1080x1920 (Mockup iPhone + Hook Overlay)...")
    bg_raw = Image.open(ASSETS_DIR / "bg_anime_sky.jpg").convert("RGBA")
    bg_base = bg_raw.resize((1080, 1920), Image.Resampling.LANCZOS)
    bg_base = bg_base.filter(ImageFilter.GaussianBlur(radius=4))
    darken = Image.new("RGBA", (1080, 1920), (15, 23, 42, 75))
    bg_base = Image.alpha_composite(bg_base, darken)

    phone_w, phone_h = 810, 1710
    px = (1080 - phone_w) // 2
    py = 165

    mask = Image.new("L", (phone_w, phone_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (phone_w, phone_h)], radius=40, fill=255)

    shadow_pad = 55
    shadow = Image.new("RGBA", (phone_w + shadow_pad * 2, phone_h + shadow_pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [(shadow_pad, shadow_pad + 12), (shadow_pad + phone_w, shadow_pad + phone_h + 12)],
        radius=42, fill=(0, 0, 0, 145)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=22))

    bezel = Image.new("RGBA", (phone_w + 6, phone_h + 6), (0, 0, 0, 0))
    ImageDraw.Draw(bezel).rounded_rectangle(
        [(0, 0), (phone_w + 5, phone_h + 5)],
        radius=42, outline=(30, 41, 59, 255), width=3
    )

    for i in range(14):
        phone_img = Image.open(FRAMES_DIR / f"frame_{i}.png").convert("RGBA")
        phone_resized = phone_img.resize((phone_w, phone_h), Image.Resampling.LANCZOS)

        canvas = bg_base.copy()
        canvas.paste(shadow, (px - shadow_pad, py - shadow_pad), shadow)
        canvas.paste(bezel, (px - 3, py - 3), bezel)
        canvas.paste(phone_resized, (px, py), mask)

        if i in (0, 1):
            _draw_top_banner(
                canvas,
                "Thiết kế khắc tên crush lên cửa khách… và cái kết!",
                bg_color=(220, 38, 38, 235),
                border_color=(254, 240, 138, 255),
                text_color=(255, 255, 255),
                font_size=34,
            )
        elif i == 13:
            _draw_top_banner(
                canvas,
                "Tập 2: Tùng em tặng quà gì cho Trang? Comment nhé!",
                bg_color=(15, 118, 110, 238),
                border_color=(153, 246, 228, 255),
                text_color=(255, 255, 255),
                font_size=33,
            )
        else:
            _draw_top_banner(
                canvas,
                "CHUYỆN VĂN PHÒNG CỬA THÉP • TẬP 1",
                bg_color=(15, 23, 42, 200),
                border_color=(56, 189, 248, 200),
                text_color=(224, 242, 254),
                font_size=29,
            )

        out_path = WORK_DIR / f"comp_{i}.png"
        canvas.convert("RGB").save(out_path, quality=95)

    print("  Đã xuất xong 14 khung composite.")


def build_audio_track(timeline, total_dur):
    print("[4/5] Trộn 13 giọng đọc VieNeu-TTS + SFX Ting/Pop...")
    inputs = []
    filter_parts = []
    input_idx = 0
    labels = []

    for item in timeline[1:]:
        idx = item["index"]
        start_ms = int(item["start"] * 1000)

        # SFX tại thời điểm tin nhắn bật lên
        inputs.extend(["-i", str(item["sfx_path"])])
        filter_parts.append(f"[{input_idx}:a]adelay={start_ms}|{start_ms},volume=0.85[sfx_{idx}];")
        labels.append(f"[sfx_{idx}]")
        input_idx += 1

        # Voiceover bắt đầu ngay sau SFX 50ms
        inputs.extend(["-i", str(item["voice_path"])])
        v_start_ms = start_ms + 50
        filter_parts.append(f"[{input_idx}:a]adelay={v_start_ms}|{v_start_ms},volume=1.35[voc_{idx}];")
        labels.append(f"[voc_{idx}]")
        input_idx += 1

    n_streams = len(labels)
    filter_str = "".join(filter_parts) + f"{''.join(labels)}amix=inputs={n_streams}:duration=longest:normalize=0[aout]"

    audio_out = WORK_DIR / "ep1_mixed_audio.wav"
    subprocess.run([
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[aout]",
        "-t", f"{total_dur:.2f}",
        "-ar", "44100",
        "-ac", "2",
        str(audio_out)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return audio_out


def render_final_mp4(timeline, audio_path, total_dur):
    print("[5/5] Mã hóa Video MP4 1080x1920 30fps...")
    concat_txt = WORK_DIR / "concat_ep1.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        f.write("ffconcat version 1.0\n")
        for item in timeline:
            img_p = (WORK_DIR / f"comp_{item['index']}.png").as_posix()
            f.write(f"file '{img_p}'\n")
            f.write(f"duration {item['duration']:.3f}\n")
        last_p = (WORK_DIR / f"comp_{timeline[-1]['index']}.png").as_posix()
        f.write(f"file '{last_p}'\n")

    subprocess.run([
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
        "-t", f"{total_dur:.2f}",
        "-movflags", "+faststart",
        str(OUTPUT_MP4)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    dur = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(OUTPUT_MP4)
    ]).decode().strip())
    size_mb = OUTPUT_MP4.stat().st_size / (1024 * 1024)
    print(f"  MP4 hoàn tất: {OUTPUT_MP4} ({dur:.2f}s, {size_mb:.2f} MB)")


def sync_capcut_draft(timeline, total_dur):
    """Tạo luôn bản Draft 4 Tracks trên CapCut Desktop để bạn có thể chỉnh/export lại nếu muốn"""
    try:
        from pyJianYingDraft import DraftFolder, VideoSegment, AudioSegment, TrackSpec, TrackType, trange, AudioMaterial
    except ImportError:
        return

    from capcut_draft_generator import post_process_capcut_draft

    local_capcut_dir = Path(os.path.expandvars(r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft"))
    if not local_capcut_dir.is_dir():
        return

    temp_root = WORKSPACE / "capcut_projects"
    temp_root.mkdir(parents=True, exist_ok=True)
    draft_folder = DraftFolder(str(temp_root))
    script = draft_folder.create_draft(PROJECT_NAME, 1080, 1920, fps=30, allow_replace=True)

    proj_dir = temp_root / PROJECT_NAME
    proj_assets = proj_dir / "assets"
    proj_assets.mkdir(parents=True, exist_ok=True)

    # Copy frames, voices, sfx, bg vào assets của project
    shutil.copy2(ASSETS_DIR / "bg_anime_sky.jpg", proj_assets / "bg_anime_sky.jpg")
    for sfx_name in ("sfx_pop.mp3", "sfx_ting.mp3"):
        shutil.copy2(ASSETS_DIR / sfx_name, proj_assets / sfx_name)
    for item in timeline:
        # Dùng luôn khung composite hoặc frame gốc cho CapCut (dùng frame gốc để dễ tách background)
        shutil.copy2(FRAMES_DIR / item["frame"], proj_assets / item["frame"])
        if item["voice_path"]:
            shutil.copy2(item["voice_path"], proj_assets / item["voice_path"].name)

    total_us = int(round(total_dur * 1_000_000))
    script.append_track(TrackSpec(TrackType.video, name="Track_Background"))
    script.append_track(TrackSpec(TrackType.video, name="Track_PhoneScreen"))
    script.append_track(TrackSpec(TrackType.audio, name="Track_AudioSFX"))
    script.append_track(TrackSpec(TrackType.audio, name="Track_Voiceover"))

    script.add_segment(VideoSegment(str(proj_assets / "bg_anime_sky.jpg"), trange(0, total_us)), track="Track_Background")

    for item in timeline:
        s_us = int(round(item["start"] * 1_000_000))
        d_us = int(round(item["duration"] * 1_000_000))
        script.add_segment(VideoSegment(str(proj_assets / item["frame"]), trange(s_us, d_us)), track="Track_PhoneScreen")

        if item["sfx_path"]:
            sfx_mat = AudioMaterial(str(proj_assets / item["sfx_path"].name))
            script.add_segment(AudioSegment(sfx_mat, trange(s_us, min(sfx_mat.duration, d_us)), volume=0.85), track="Track_AudioSFX")
        if item["voice_path"]:
            v_mat = AudioMaterial(str(proj_assets / item["voice_path"].name))
            script.add_segment(AudioSegment(v_mat, trange(s_us + 50_000, v_mat.duration), volume=1.3), track="Track_Voiceover")

    script.save()

    dest_dir = local_capcut_dir / PROJECT_NAME
    if dest_dir.exists():
        shutil.rmtree(dest_dir, ignore_errors=True)
    shutil.copytree(proj_dir, dest_dir, ignore=shutil.ignore_patterns("desktop.ini"))
    # Đảm bảo thumbnail là frame_1 của Tập 1
    post_process_capcut_draft(dest_dir, PROJECT_NAME, total_us)

    root_meta_path = local_capcut_dir / "root_meta_info.json"
    if root_meta_path.exists():
        try:
            with open(dest_dir / "draft_meta_info.json", "r", encoding="utf-8") as fm:
                d_meta = json.load(fm)
            with open(root_meta_path, "r", encoding="utf-8") as fr:
                r_data = json.load(fr)
            all_drafts = r_data.get("all_draft_store", [])
            entry = next((d for d in all_drafts if d.get("draft_name") == PROJECT_NAME), None)
            if not entry:
                entry = {"draft_name": PROJECT_NAME}
                all_drafts.insert(0, entry)
            entry.update({
                "draft_id": d_meta["draft_id"],
                "draft_fold_path": dest_dir.as_posix(),
                "draft_root_path": local_capcut_dir.as_posix(),
                "draft_json_file": (dest_dir / "draft_content.json").as_posix(),
                "draft_cover": (dest_dir / "draft_cover.jpg").as_posix(),
                "draft_new_version": "164.0.0",
                "tm_duration": total_us,
            })
            with open(root_meta_path, "w", encoding="utf-8") as fr:
                json.dump(r_data, fr, ensure_ascii=False)
        except Exception as e:
            print(f"[CapCut Sync Warning] {e}")

    print(f"  Đã đồng bộ thêm dự án CapCut Desktop: {dest_dir}")


if __name__ == "__main__":
    print("=" * 60)
    print("🎬 RENDER TẬP 1: CÁNH CỬA KHẮC TÊN CRUSH (ELEVENLABS VOICES)")
    print("=" * 60)
    ensure_frames()
    tl, total_dur = load_timeline()
    render_composite_frames()
    aud = build_audio_track(tl, total_dur)
    render_final_mp4(tl, aud, total_dur)
    sync_capcut_draft(tl, total_dur)
    print("\n✅ HOÀN TẤT XUẤT SẮC VIDEO TẬP 1!")

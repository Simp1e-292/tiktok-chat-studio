#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video & CapCut Draft Renderer: Tập 1 v2 - "Quên Tắt Layer CAD Khi Xuất CNC"
- Đọc 14 giọng thuần Việt (VieNeu-TTS) từ vieneu_episode1_v2_voices/
- Hỗ trợ ảnh thực tế + GIF meme động chạy mượt bên trong khung chat Messenger
- Trộn 8+ loại SFX Meme có fade-out sạch sẽ (không lấn giọng thoại)
- Xuất video MP4: video_tap_01_v2_quen_tat_layer_cad.mp4
- Đồng bộ CapCut Desktop: Cua_Thep_Tap_01_V2
"""

import os
import sys
import json
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
VOICES_DIR = WORKSPACE / "vieneu_episode1_v2_voices"
FRAMES_DIR = WORKSPACE / "episode1_v2_frames"
WORK_DIR = WORKSPACE / "episode1_v2_work"
WORK_DIR.mkdir(parents=True, exist_ok=True)

MANIFEST_PATH = VOICES_DIR / "manifest.json"
FRAMES_INDEX_PATH = FRAMES_DIR / "frames_index.json"
OUTPUT_MP4 = WORKSPACE / "video_tap_01_v2_quen_tat_layer_cad.mp4"
PROJECT_NAME = "Cua_Thep_Tap_01_V2"


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
    lines, curr = [], []
    for w in words:
        test = " ".join(curr + [w])
        bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] <= max_w or not curr:
            curr.append(w)
        else:
            lines.append(" ".join(curr))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))
    return lines


def _draw_top_banner(canvas: Image.Image, text: str, bg_color, border_color, text_color=(255, 255, 255), font_size=34):
    draw = ImageDraw.Draw(canvas, "RGBA")
    font = _load_font(font_size, bold=True)
    lines = _wrap_text(draw, text, font, 880)

    line_heights, max_line_w = [], 0
    for ln in lines:
        bb = draw.textbbox((0, 0), ln, font=font)
        max_line_w = max(max_line_w, bb[2] - bb[0])
        line_heights.append(bb[3] - bb[1])

    gap = 10
    total_h = sum(line_heights) + gap * max(0, len(lines) - 1)
    pad_x, pad_y = 36, 18
    box_w = min(980, max_line_w + pad_x * 2)
    box_h = total_h + pad_y * 2

    x0 = (1080 - box_w) // 2
    y0 = max(24, (155 - box_h) // 2)
    draw.rounded_rectangle([(x0, y0), (x0 + box_w, y0 + box_h)], radius=24, fill=bg_color, outline=border_color, width=3)

    curr_y = y0 + pad_y - 3
    for idx, ln in enumerate(lines):
        bb = draw.textbbox((0, 0), ln, font=font)
        lx = (1080 - (bb[2] - bb[0])) // 2
        draw.text((lx, curr_y), ln, font=font, fill=text_color)
        curr_y += line_heights[idx] + gap


def ensure_frames():
    if FRAMES_INDEX_PATH.exists():
        data = json.loads(FRAMES_INDEX_PATH.read_text(encoding="utf-8"))
        if len(data) == 15 and all((FRAMES_DIR / fn).exists() for s in data for fn in s["frames"]):
            print("[1/5] Đã có sẵn bộ khung hình (gồm GIF động) trong episode1_v2_frames/.")
            return data
    print("[1/5] Đang chụp khung hình & chuỗi GIF động bằng Chrome Headless...")
    subprocess.check_call([
        "node",
        str(WORKSPACE / "render_episode1_v2_frames.js"),
        str(FRAMES_DIR),
        str(MANIFEST_PATH),
    ])
    return json.loads(FRAMES_INDEX_PATH.read_text(encoding="utf-8"))


def load_timeline(frames_index):
    print("[2/5] Tính toán timeline khớp 14 giọng VieNeu-TTS & SFX...")
    messages = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    INTRO_DUR = 0.45
    PAUSE_BETWEEN = 0.20
    OUTRO_PAD = 0.65

    # Các SFX có nhịp mở đầu mạnh cần cho thoại vào sau 0.35s để nghe rõ tiếng meme
    LONG_HIT_SFX = {"windows-error.mp3", "inception.mp3", "bruh.mp3", "huh.mp3", "rimshot.mp3", "wow.mp3", "ding.mp3"}

    timeline = [{
        "step": 0,
        "frames": frames_index[0]["frames"],
        "start": 0.0,
        "duration": INTRO_DUR,
        "msg": None,
        "voice_path": None,
        "sfx_path": None,
        "voice_offset": 0.0,
    }]

    curr = INTRO_DUR
    for i, m in enumerate(messages, start=1):
        v_path = VOICES_DIR / m["audio_file"]
        dur = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(v_path)
        ]).decode().strip())

        sfx_rel = m.get("sfx", "assets/sfx_ting.mp3")
        sfx_path = WORKSPACE / sfx_rel
        sfx_name = sfx_path.name
        voice_offset = 0.38 if sfx_name in LONG_HIT_SFX else 0.08

        pad = OUTRO_PAD if i == len(messages) else PAUSE_BETWEEN
        step_dur = voice_offset + dur + pad

        timeline.append({
            "step": i,
            "frames": frames_index[i]["frames"],
            "start": curr,
            "duration": step_dur,
            "msg": m,
            "voice_path": v_path,
            "voice_dur": dur,
            "sfx_path": sfx_path,
            "voice_offset": voice_offset,
        })
        print(f"  - [{i:02d}] {m['senderName']} ({sfx_name}): {curr:.2f}s -> {curr + step_dur:.2f}s (thoại {dur:.2f}s)")
        curr += step_dur

    print(f"  Tổng thời lượng Tập 1 v2: {curr:.2f} giây")
    return timeline, curr


def render_composite_frames(timeline):
    print("[3/5] Ghép nền + khung iPhone Titanium + Hook/CTA cho tất cả frame...")
    bg_raw = Image.open(ASSETS_DIR / "bg_anime_sky.jpg").convert("RGBA")
    bg_base = bg_raw.resize((1080, 1920), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(radius=4))
    bg_base = Image.alpha_composite(bg_base, Image.new("RGBA", (1080, 1920), (15, 23, 42, 75)))

    phone_w, phone_h = 810, 1710
    px, py = (1080 - phone_w) // 2, 165

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
    ImageDraw.Draw(bezel).rounded_rectangle([(0, 0), (phone_w + 5, phone_h + 5)], radius=42, outline=(30, 41, 59, 255), width=3)

    rendered_count = 0
    for item in timeline:
        s = item["step"]
        comp_list = []
        for fn in item["frames"]:
            phone_img = Image.open(FRAMES_DIR / fn).convert("RGBA").resize((phone_w, phone_h), Image.Resampling.LANCZOS)
            canvas = bg_base.copy()
            canvas.paste(shadow, (px - shadow_pad, py - shadow_pad), shadow)
            canvas.paste(bezel, (px - 3, py - 3), bezel)
            canvas.paste(phone_img, (px, py), mask)

            if s in (0, 1):
                _draw_top_banner(
                    canvas,
                    "Thiết kế quên tắt layer nháp CAD… báo hại cả công ty!",
                    bg_color=(220, 38, 38, 235),
                    border_color=(254, 240, 138, 255),
                    font_size=33,
                )
            elif s == 14:
                _draw_top_banner(
                    canvas,
                    "Tùng em tặng gì xin lỗi Trang? Comment nhé!",
                    bg_color=(15, 118, 110, 238),
                    border_color=(153, 246, 228, 255),
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

            out_name = f"comp_{fn}"
            canvas.convert("RGB").save(WORK_DIR / out_name, quality=94)
            comp_list.append(out_name)
            rendered_count += 1
        item["comp_frames"] = comp_list

    print(f"  Đã tạo xong {rendered_count} khung hình composite (bao gồm hiệu ứng GIF động).")


def build_audio_track(timeline, total_dur):
    print("[4/5] Trộn 14 giọng VieNeu-TTS + bộ SFX Meme...")
    inputs, filter_parts, labels = [], [], []
    input_idx = 0

    for item in timeline[1:]:
        idx = item["step"]
        start_ms = int(item["start"] * 1000)

        # SFX: giới hạn tối đa 1.35s kèm fade-out mượt để không đè giọng thoại
        inputs.extend(["-i", str(item["sfx_path"])])
        filter_parts.append(
            f"[{input_idx}:a]atrim=0:1.35,afade=t=out:st=0.75:d=0.60,adelay={start_ms}|{start_ms},volume=0.72[sfx_{idx}];"
        )
        labels.append(f"[sfx_{idx}]")
        input_idx += 1

        # Voiceover
        inputs.extend(["-i", str(item["voice_path"])])
        v_start_ms = start_ms + int(item["voice_offset"] * 1000)
        filter_parts.append(f"[{input_idx}:a]adelay={v_start_ms}|{v_start_ms},volume=1.40[voc_{idx}];")
        labels.append(f"[voc_{idx}]")
        input_idx += 1

    filter_str = "".join(filter_parts) + f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0[aout]"
    audio_out = WORK_DIR / "ep1_v2_mixed_audio.wav"
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
    print("[5/5] Mã hóa Video MP4 1080x1920 30fps (có GIF chuyển động mượt)...")
    concat_txt = WORK_DIR / "concat_ep1_v2.txt"
    frame_tick = 0.085
    last_written = None

    with open(concat_txt, "w", encoding="utf-8") as f:
        f.write("ffconcat version 1.0\n")
        for item in timeline:
            frames = item["comp_frames"]
            if len(frames) == 1:
                img_p = (WORK_DIR / frames[0]).as_posix()
                f.write(f"file '{img_p}'\n")
                f.write(f"duration {item['duration']:.3f}\n")
                last_written = img_p
            else:
                # Lặp chuỗi frame GIF cho đủ thời lượng của tin nhắn
                rem = item["duration"]
                fi = 0
                while rem > 0.005:
                    dt = min(frame_tick, rem)
                    img_p = (WORK_DIR / frames[fi % len(frames)]).as_posix()
                    f.write(f"file '{img_p}'\n")
                    f.write(f"duration {dt:.3f}\n")
                    last_written = img_p
                    rem -= dt
                    fi += 1
        f.write(f"file '{last_written}'\n")

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
    """Đồng bộ bản nháp CapCut 4 tracks gồm ảnh cửa thật, khung chat, SFX Meme & giọng VieNeu"""
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

    shutil.copy2(ASSETS_DIR / "bg_anime_sky.jpg", proj_assets / "bg_anime_sky.jpg")
    total_us = int(round(total_dur * 1_000_000))

    script.append_track(TrackSpec(TrackType.video, name="Track_Background"))
    script.append_track(TrackSpec(TrackType.video, name="Track_PhoneScreen"))
    script.append_track(TrackSpec(TrackType.audio, name="Track_AudioSFX"))
    script.append_track(TrackSpec(TrackType.audio, name="Track_Voiceover"))

    script.add_segment(VideoSegment(str(proj_assets / "bg_anime_sky.jpg"), trange(0, total_us)), track="Track_Background")

    for item in timeline:
        s_us = int(round(item["start"] * 1_000_000))
        d_us = int(round(item["duration"] * 1_000_000))

        # Dùng frame đầu mỗi bước cho CapCut Track_PhoneScreen
        rep_frame = item["frames"][0]
        shutil.copy2(FRAMES_DIR / rep_frame, proj_assets / rep_frame)
        script.add_segment(VideoSegment(str(proj_assets / rep_frame), trange(s_us, d_us)), track="Track_PhoneScreen")

        if item["sfx_path"]:
            sfx_dst = proj_assets / item["sfx_path"].name
            if not sfx_dst.exists():
                shutil.copy2(item["sfx_path"], sfx_dst)
            sfx_mat = AudioMaterial(str(sfx_dst))
            script.add_segment(
                AudioSegment(sfx_mat, trange(s_us, min(sfx_mat.duration, min(d_us, 1_350_000))), volume=0.72),
                track="Track_AudioSFX"
            )
        if item["voice_path"]:
            v_dst = proj_assets / item["voice_path"].name
            shutil.copy2(item["voice_path"], v_dst)
            v_mat = AudioMaterial(str(v_dst))
            v_off_us = int(round(item["voice_offset"] * 1_000_000))
            script.add_segment(AudioSegment(v_mat, trange(s_us + v_off_us, v_mat.duration), volume=1.35), track="Track_Voiceover")

    script.save()
    dest_dir = local_capcut_dir / PROJECT_NAME
    if dest_dir.exists():
        shutil.rmtree(dest_dir, ignore_errors=True)
    shutil.copytree(proj_dir, dest_dir, ignore=shutil.ignore_patterns("desktop.ini"))
    post_process_capcut_draft(dest_dir, PROJECT_NAME, total_us)

    # Đặt draft_cover bằng khung step_01.png (có ảnh cửa thật)
    step1 = FRAMES_DIR / "step_01.png"
    if step1.exists():
        Image.open(step1).convert("RGB").save(dest_dir / "draft_cover.jpg", "JPEG")

    root_meta_path = local_capcut_dir / "root_meta_info.json"
    if root_meta_path.exists():
        try:
            d_meta = json.loads((dest_dir / "draft_meta_info.json").read_text(encoding="utf-8"))
            r_data = json.loads(root_meta_path.read_text(encoding="utf-8"))
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
            root_meta_path.write_text(json.dumps(r_data, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"[CapCut Sync Warning] {e}")

    print(f"  Đã đồng bộ bản CapCut Desktop: {dest_dir}")


if __name__ == "__main__":
    print("=" * 65)
    print("🎬 RENDER TẬP 1 v2: QUÊN TẮT LAYER CAD (ẢNH THẬT + GIF + SFX)")
    print("=" * 65)
    f_idx = ensure_frames()
    tl, total_dur = load_timeline(f_idx)
    render_composite_frames(tl)
    aud = build_audio_track(tl, total_dur)
    render_final_mp4(tl, aud, total_dur)
    sync_capcut_draft(tl, total_dur)
    print("\n✅ HOÀN TẤT VIDEO TẬP 1 v2!")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render Video Test v3 ("Cửa lắp xong, 2 cánh 2 hướng vân. Ai chịu?? 💀")
- Giữ NGUYÊN từng chữ của 20 mục, đúng thời lượng 50.0s (48-52s), 1080x1920, 30fps
- Không nhạc nền, giữ nguyên giọng đọc VieNeu-TTS + SFX (ting / bùm thu hồi / meme) + Meme GIF
"""

import os
import json
import shutil
import subprocess
from pathlib import Path


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
VOICES_DIR = WORKSPACE / "vieneu_episode1_v3_voices"
FRAMES_DIR = WORKSPACE / "episode1_v3_frames"
MANIFEST_PATH = VOICES_DIR / "manifest.json"
TIMELINE_PATH = FRAMES_DIR / "events_timeline.json"
OUTPUT_MP4 = WORKSPACE / "video_tap_01_v3_hai_huong_van.mp4"


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
    print("=" * 65)
    print("🎬 RENDER VIDEO TEST v3: 2 CÁNH 2 HƯỚNG VÂN (50.0 GIÂY)")
    print("=" * 65)

    # 1. Chụp khung hình HTML (20 mục + đang nhập + GIF động)
    print("[1/3] Chụp khung hình giao diện chat qua Chrome...")
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    subprocess.check_call(["node", str(WORKSPACE / "render_episode1_v3_frames.js")])

    items = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    events = json.loads(TIMELINE_PATH.read_text(encoding="utf-8"))
    total_dur = sum(ev["duration"] for ev in events)
    print(f"  Tổng thời lượng timeline: {total_dur:.2f}s ({len(events)} sự kiện)")

    # 2. Trộn âm thanh: SFX + Giọng đọc VieNeu-TTS (KHÔNG nhạc nền)
    print("[2/3] Trộn 17 giọng đọc VieNeu-TTS + SFX ting/bùm/meme...")
    inputs, filter_parts, labels = [], [], []
    in_idx = 0

    for it in items:
        start_ms = int(round(it["t"] * 1000))
        sfx_rel = it.get("sfx")
        if sfx_rel:
            sfx_p = WORKSPACE / sfx_rel
            inputs.extend(["-i", str(sfx_p)])
            vol = "0.90" if it["kind"] == "sys_recall" else "0.68"
            filter_parts.append(
                f"[{in_idx}:a]atrim=0:1.15,afade=t=out:st=0.65:d=0.50,adelay={start_ms}|{start_ms},volume={vol}[sfx_{it['idx']}];"
            )
            labels.append(f"[sfx_{it['idx']}]")
            in_idx += 1

        if it.get("meme_sfx"):
            msfx_p = WORKSPACE / it["meme_sfx"]
            inputs.extend(["-i", str(msfx_p)])
            m_ms = start_ms + 900
            filter_parts.append(
                f"[{in_idx}:a]atrim=0:0.9,afade=t=out:st=0.5:d=0.4,adelay={m_ms}|{m_ms},volume=0.55[msfx_{it['idx']}];"
            )
            labels.append(f"[msfx_{it['idx']}]")
            in_idx += 1

        if it["kind"] == "msg" and it.get("audio_file"):
            v_p = VOICES_DIR / it["audio_file"]
            inputs.extend(["-i", str(v_p)])
            v_ms = start_ms + 80
            filter_parts.append(f"[{in_idx}:a]adelay={v_ms}|{v_ms},volume=1.45[voc_{it['idx']}];")
            labels.append(f"[voc_{it['idx']}]")
            in_idx += 1

    filter_str = "".join(filter_parts) + f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0[aout]"
    mixed_wav = FRAMES_DIR / "v3_mixed_audio.wav"
    subprocess.run([
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[aout]",
        "-t", f"{total_dur:.2f}",
        "-ar", "44100",
        "-ac", "2",
        str(mixed_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # 3. Render MP4 bằng ffconcat
    print("[3/3] Xuất file MP4 1080x1920 30fps...")
    concat_txt = FRAMES_DIR / "concat_v3.txt"
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

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-i", str(mixed_wav),
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
    print(f"\n✅ HOÀN TẤT: {OUTPUT_MP4} ({dur:.2f}s, {size_mb:.2f} MB)")


if __name__ == "__main__":
    main()

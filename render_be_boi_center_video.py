#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render Video: "BỂ BƠI VÔ CỰC CỦA SẾP" — Format Phương án A (Center-Focus Cinema chuẩn Con Bò Đi Làm)
- Nền đen tuyền 1080x1920, dải chat khóa chặt ở Vùng Vàng giữa màn hình (né 100% UI TikTok Trên/Dưới/Phải)
- Cỡ chữ khổng lồ 44px, mỗi nhịp chỉ hiện đúng nhân vật đang nói + ảnh thật & GIF meme động
- Xuất MP4: video_be_boi_center_cinema.mp4
- Đồng bộ thẳng CapCut Desktop: Cua_Thep_Be_Boi_Center
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from export_to_capcut import export_project


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
VOICES_DIR = WORKSPACE / "vieneu_be_boi_voices"
FRAMES_DIR = WORKSPACE / "be_boi_center_frames"
MANIFEST_PATH = VOICES_DIR / "manifest.json"
TIMELINE_PATH = FRAMES_DIR / "events_timeline.json"
OUTPUT_MP4 = WORKSPACE / "video_be_boi_center_cinema.mp4"


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
    print("🎬 RENDER VIDEO: BỂ BƠI VÔ CỰC — FORMAT CENTER-FOCUS (CON BÒ ĐI LÀM)")
    print("=" * 65)

    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    subprocess.check_call(["node", str(WORKSPACE / "render_be_boi_center_frames.js")])

    items = {it["idx"]: it for it in json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))}
    events = json.loads(TIMELINE_PATH.read_text(encoding="utf-8"))
    total_dur = sum(ev["duration"] for ev in events)
    print(f"  Tổng thời lượng: {total_dur:.2f}s ({len(events)} sự kiện)")

    inputs, filter_parts, labels = [], [], []
    in_idx = 0

    for ev in events:
        if ev["action"] != "item":
            continue
        it = items[ev["item_idx"]]
        start_ms = int(round(ev["time"] * 1000))

        sfx_rel = it.get("sfx")
        if sfx_rel:
            sfx_p = WORKSPACE / sfx_rel
            inputs.extend(["-i", str(sfx_p)])
            if it["kind"] == "end_card":
                filter_parts.append(
                    f"[{in_idx}:a]atrim=0:2.30,afade=t=out:st=1.75:d=0.55,adelay={start_ms}|{start_ms},volume=0.58[sfx_{it['idx']}];"
                )
            elif it["kind"] == "sys_time":
                filter_parts.append(
                    f"[{in_idx}:a]atrim=0:1.75,afade=t=out:st=1.35:d=0.40,adelay={start_ms}|{start_ms},volume=0.90[sfx_{it['idx']}];"
                )
            else:
                filter_parts.append(
                    f"[{in_idx}:a]atrim=0:1.05,afade=t=out:st=0.55:d=0.50,adelay={start_ms}|{start_ms},volume=0.52[sfx_{it['idx']}];"
                )
            labels.append(f"[sfx_{it['idx']}]")
            in_idx += 1

        if it["kind"] == "msg" and it.get("audio_file"):
            v_p = VOICES_DIR / it["audio_file"]
            inputs.extend(["-i", str(v_p)])
            v_ms = start_ms + 140
            filter_parts.append(
                f"[{in_idx}:a]highpass=f=80,acompressor=threshold=-16dB:ratio=2.2:attack=15:release=180,adelay={v_ms}|{v_ms},volume=1.05[voc_{it['idx']}];"
            )
            labels.append(f"[voc_{it['idx']}]")
            in_idx += 1

    filter_str = (
        "".join(filter_parts)
        + f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0,"
        + "loudnorm=I=-14:TP=-1.0:LRA=7[aout]"
    )
    mixed_wav = FRAMES_DIR / "be_boi_center_mixed_audio.wav"
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

    concat_txt = FRAMES_DIR / "concat_be_boi_center.txt"
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
    print(f"\n✅ HOÀN TẤT VIDEO CENTER-FOCUS: {OUTPUT_MP4} ({dur:.2f}s, {size_mb:.2f} MB)")

    export_project(
        project_name="Cua_Thep_Be_Boi_Center",
        frames_dir=FRAMES_DIR,
        voices_dir=VOICES_DIR,
        voice_delay_sec=0.14,
    )


if __name__ == "__main__":
    main()

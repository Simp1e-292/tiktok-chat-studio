#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xuất dự án video (kèm từng track Hình/GIF động, SFX, Voiceover rời) thẳng vào CapCut Desktop PC
để người dùng chỉnh thêm nhạc nền / phụ đề / hiệu ứng và xuất video đăng TikTok.

Hỗ trợ xuất:
1. Cua_Thep_Be_Boi_Vo_Cuc ("Bể Bơi Vô Cực Của Sếp" — 40.90s)
2. Cua_Thep_Tap_01_V7     ("Tập 1: Cửa 2 Hướng Vân" — 57.33s)
"""

import os
import json
import stat
import sys
import shutil
import subprocess
from pathlib import Path
from PIL import Image
from pyJianYingDraft import (
    DraftFolder,
    VideoSegment,
    VideoMaterial,
    AudioSegment,
    TrackSpec,
    TrackType,
    trange,
    AudioMaterial,
)

from capcut_draft_generator import post_process_capcut_draft


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


def _pick_h264_codec_args():
    try:
        enc_out = subprocess.check_output(["ffmpeg", "-encoders"], stderr=subprocess.STDOUT).decode(errors="ignore")
    except Exception:
        enc_out = ""
    if "libx264" in enc_out:
        return ["-c:v", "libx264", "-preset", "fast", "-crf", "18"]
    if "h264_mf" in enc_out:
        return ["-c:v", "h264_mf", "-b:v", "6M"]
    return ["-c:v", "mpeg4", "-q:v", "3"]


def _build_gif_clip_mp4(frames_dir: Path, frame_names: list, duration_sec: float, out_mp4: Path):
    """Đóng gói chuỗi frame GIF động thành video MP4 không tiếng (dư nhẹ 0.25s để không bị lệch khung CapCut)"""
    concat_file = out_mp4.with_suffix(".txt")
    tick = 0.085
    padded_sec = duration_sec + 0.25
    rem = padded_sec
    fi = 0
    last_img = None
    with open(concat_file, "w", encoding="utf-8") as f:
        f.write("ffconcat version 1.0\n")
        while rem > 0.005:
            dt = min(tick, rem)
            p = (frames_dir / frame_names[fi % len(frame_names)]).as_posix()
            f.write(f"file '{p}'\n")
            f.write(f"duration {dt:.3f}\n")
            last_img = p
            rem -= dt
            fi += 1
        f.write(f"file '{last_img}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        *_pick_h264_codec_args(),
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-an",
        "-t", f"{padded_sec:.3f}",
        str(out_mp4),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    concat_file.unlink(missing_ok=True)


def export_project(
    project_name: str,
    frames_dir: Path,
    voices_dir: Path,
    voice_delay_sec: float = 0.14,
):
    local_capcut_dir = Path(os.path.expandvars(r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft"))
    if not local_capcut_dir.is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục CapCut Desktop: {local_capcut_dir}")

    timeline_path = frames_dir / "events_timeline.json"
    manifest_path = voices_dir / "manifest.json"
    if not timeline_path.exists() or not manifest_path.exists():
        raise FileNotFoundError(f"Thiếu frames hoặc manifest trong {frames_dir} / {voices_dir}")

    events = json.loads(timeline_path.read_text(encoding="utf-8"))
    items = {it["idx"]: it for it in json.loads(manifest_path.read_text(encoding="utf-8"))}
    total_dur = sum(ev["duration"] for ev in events)
    total_us = int(round(total_dur * 1_000_000))

    temp_root = WORKSPACE / "capcut_projects"
    temp_root.mkdir(parents=True, exist_ok=True)
    draft_folder = DraftFolder(str(temp_root))
    script = draft_folder.create_draft(project_name, 1080, 1920, fps=30, allow_replace=True)

    proj_dir = temp_root / project_name
    proj_assets = proj_dir / "assets"
    proj_assets.mkdir(parents=True, exist_ok=True)

    script.append_track(TrackSpec(TrackType.video, name="Track_ChatVideo"))
    script.append_track(TrackSpec(TrackType.audio, name="Track_SFX"))
    script.append_track(TrackSpec(TrackType.audio, name="Track_Voiceover"))

    for ev in events:
        s_us = int(round(ev["time"] * 1_000_000))
        d_us = int(round(ev["duration"] * 1_000_000))
        frames = ev["frames"]

        if len(frames) == 1:
            fn = frames[0]
            dst_img = proj_assets / fn
            shutil.copy2(frames_dir / fn, dst_img)
            script.add_segment(VideoSegment(str(dst_img), trange(s_us, d_us)), track="Track_ChatVideo")
        else:
            clip_name = f"seg_ev_{ev['ev_index']:02d}.mp4"
            dst_clip = proj_assets / clip_name
            _build_gif_clip_mp4(frames_dir, frames, ev["duration"], dst_clip)
            v_mat = VideoMaterial(str(dst_clip))
            seg_d_us = min(d_us, v_mat.duration)
            script.add_segment(
                VideoSegment(v_mat, trange(s_us, seg_d_us), source_timerange=trange(0, seg_d_us)),
                track="Track_ChatVideo",
            )

        if ev["action"] == "item":
            it = items[ev["item_idx"]]
            sfx_rel = it.get("sfx")
            if sfx_rel:
                sfx_src = WORKSPACE / sfx_rel
                sfx_dst = proj_assets / sfx_src.name
                if not sfx_dst.exists():
                    shutil.copy2(sfx_src, sfx_dst)
                sfx_mat = AudioMaterial(str(sfx_dst))
                if it["kind"] == "end_card":
                    max_sfx = 2_300_000
                    vol = 0.65
                elif it["kind"] in ("sys_time", "sys_recall"):
                    max_sfx = 1_750_000
                    vol = 0.90
                else:
                    max_sfx = 1_100_000
                    vol = 0.58
                seg_dur = min(sfx_mat.duration, min(d_us, max_sfx))
                script.add_segment(AudioSegment(sfx_mat, trange(s_us, seg_dur), volume=vol), track="Track_SFX")

            if it["kind"] == "msg" and it.get("audio_file"):
                v_src = voices_dir / it["audio_file"]
                v_dst = proj_assets / v_src.name
                if not v_dst.exists():
                    shutil.copy2(v_src, v_dst)
                v_mat = AudioMaterial(str(v_dst))
                v_start_us = s_us + int(round(voice_delay_sec * 1_000_000))
                script.add_segment(AudioSegment(v_mat, trange(v_start_us, v_mat.duration), volume=1.08), track="Track_Voiceover")

    script.save()

    dest_dir = local_capcut_dir / project_name
    if dest_dir.exists():
        shutil.rmtree(dest_dir, ignore_errors=True)
    shutil.copytree(proj_dir, dest_dir, ignore=shutil.ignore_patterns("desktop.ini"))

    # Chuẩn hóa tất cả đường dẫn bên trong draft trỏ thẳng vào thư mục CapCut Desktop đích
    post_process_capcut_draft(dest_dir, project_name, total_us, target_path=dest_dir)

    # Đặt ảnh bìa dự án bằng khung đầu tiên (ev_00.png)
    cover_src = frames_dir / "ev_00.png"
    if cover_src.exists():
        Image.open(cover_src).convert("RGB").save(dest_dir / "draft_cover.jpg", "JPEG", quality=92)

    # Đăng ký vào root_meta_info.json để hiện ngay trên màn hình chính CapCut
    root_meta_path = local_capcut_dir / "root_meta_info.json"
    if root_meta_path.exists():
        d_meta = json.loads((dest_dir / "draft_meta_info.json").read_text(encoding="utf-8"))
        r_data = json.loads(root_meta_path.read_text(encoding="utf-8"))
        all_drafts = r_data.get("all_draft_store", [])
        entry = next((d for d in all_drafts if d.get("draft_name") == project_name), None)
        if not entry:
            entry = {"draft_name": project_name}
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

    print(f"✅ Đã xuất CapCut Desktop: {project_name} ({total_dur:.2f}s) -> {dest_dir}")


if __name__ == "__main__":
    export_project(
        project_name="Cua_Thep_Be_Boi_Vo_Cuc",
        frames_dir=WORKSPACE / "be_boi_frames",
        voices_dir=WORKSPACE / "vieneu_be_boi_voices",
        voice_delay_sec=0.14,
    )
    export_project(
        project_name="Cua_Thep_Tap_01_V7",
        frames_dir=WORKSPACE / "episode1_v7_frames",
        voices_dir=WORKSPACE / "vieneu_episode1_v7_voices",
        voice_delay_sec=0.14,
    )

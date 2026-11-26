#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adapter tích hợp CIT Voice Studio API vào pipeline video TikTok hiện tại.

Tương thích định dạng `items` và `manifest.json` của `audio_engine_conbo.py`,
nhưng thay vì khởi tạo `Vieneu()` mới mỗi lần chạy script, adapter gọi trực tiếp
tới local server CIT Voice Studio (http://127.0.0.1:8001) — tận dụng model
đang chạy sẵn trên RAM/VRAM (kể cả VieNeu-TTS v3 Turbo d3), từ điển phát âm,
thẻ cảm xúc [cười] / [thở dài] / [hắng giọng] và giọng clone lưu trong app.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from cit_voice_client import CitVoiceClient


def setup_ffmpeg() -> None:
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    local_apps = Path(os.path.expandvars(r"%LOCALAPPDATA%\CapCut\Apps"))
    if local_apps.is_dir():
        for exe in sorted(local_apps.rglob("ffmpeg.exe"), reverse=True):
            tool_dir = str(exe.parent)
            if tool_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = tool_dir + os.pathsep + os.environ["PATH"]
            break


def probe_duration(path: Path) -> float:
    return float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ]
        )
        .decode()
        .strip()
    )


def _trim_and_convert_wav(src_audio: Path, dst_wav: Path, extra_speed: float = 1.0) -> float:
    """Chuyển sang WAV 44.1kHz stereo và cắt sạch khoảng lặng thừa đầu/cuối."""
    filters = [
        "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-42dB",
        "areverse",
        "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-42dB",
        "areverse",
    ]
    if abs(extra_speed - 1.0) > 0.005:
        filters.append(f"atempo={extra_speed:.3f}")
    filters.append("apad=pad_dur=0.025")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src_audio),
            "-af",
            ",".join(filters),
            "-ar",
            "44100",
            "-ac",
            "2",
            str(dst_wav),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return probe_duration(dst_wav)


def synthesize_dual_gender_cit(
    items: List[Dict],
    out_dir: Path,
    male_voice: str = "Adam bựa",
    female_voice: str = "Trúc Ly",
    end_card_voice: Optional[str] = None,
    male_speed: float = 1.10,
    female_speed: float = 1.08,
    temperature: float = 0.65,
    base_url: str = "http://127.0.0.1:8001",
    api_key: Optional[str] = None,
    reuse_cache: bool = True,
    use_pronunciation_dict: bool = True,
    seed: Optional[int] = None,
) -> Path:
    """
    Drop-in replacement cho `synthesize_dual_gender` dùng CIT Voice Studio API.
    Giữ nguyên cấu trúc `manifest.json` để mix tiếp với BGM/SFX và render video.
    """
    setup_ffmpeg()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    client = CitVoiceClient(base_url=base_url, api_key=api_key)
    health = client.wait_ready(timeout_sec=30.0)
    engine_name = health.get("engine", "cit-voice-studio")

    manifest_path = out_dir / "manifest.json"
    prev_map: Dict[int, Dict] = {}
    if reuse_cache and manifest_path.exists():
        try:
            for prev in json.loads(manifest_path.read_text(encoding="utf-8")):
                prev_map[prev.get("idx")] = prev
        except Exception:
            prev_map = {}

    manifest_out: List[Dict] = []

    for it in items:
        row = dict(it)
        is_end = it.get("kind") == "end_card"
        needs_voice = (it.get("kind") == "msg" and it.get("tts")) or (
            is_end and it.get("tts")
        )
        if not needs_voice:
            manifest_out.append(row)
            continue

        gender = row.get("gender", "female" if is_end else "male")
        row["gender"] = gender

        if is_end and end_card_voice:
            voice_id = end_card_voice
        elif gender == "female":
            voice_id = female_voice
        else:
            voice_id = male_voice

        speed = female_speed if gender == "female" else male_speed
        used_label = f"cit:{engine_name}:{voice_id}"
        final_wav = out_dir / f"voice_{it['idx']:02d}_{it.get('code', gender.upper())}.wav"

        prev = prev_map.get(it["idx"])
        if (
            reuse_cache
            and prev
            and final_wav.exists()
            and prev.get("tts") == it.get("tts")
            and prev.get("voice_name") == used_label
            and prev.get("audio_file") == final_wav.name
            and prev.get("speed") == speed
            and prev.get("temperature") == temperature
        ):
            dur = probe_duration(final_wav)
            row.update(
                {
                    "audio_file": final_wav.name,
                    "voice_name": used_label,
                    "speed": speed,
                    "temperature": temperature,
                    "duration_sec": round(dur, 4),
                }
            )
            manifest_out.append(row)
            print(f"  [CACHE] #{it['idx']:02d} ({gender.upper()} | {voice_id}) {dur:.2f}s")
            continue

        raw_wav = out_dir / f"raw_cit_{it['idx']:02d}.wav"
        try:
            meta = client.generate_to_file(
                text=it["tts"],
                out_path=raw_wav,
                voice_id=voice_id,
                speed=speed,
                temperature=temperature,
                fmt="wav",
                use_pronunciation_dict=use_pronunciation_dict,
                seed=seed,
            )
            # Speed đã xử lý ngay trong CIT Voice Studio API nên ffmpeg chỉ trim silence + chuẩn hóa 44.1kHz stereo
            dur = _trim_and_convert_wav(raw_wav, final_wav, extra_speed=1.0)
        finally:
            raw_wav.unlink(missing_ok=True)

        row.update(
            {
                "audio_file": final_wav.name,
                "voice_name": used_label,
                "speed": speed,
                "temperature": temperature,
                "duration_sec": round(dur, 4),
                "cit_elapsed_sec": meta.get("elapsed_seconds"),
                "cit_rtf": meta.get("rtf"),
                "cit_sample_rate": meta.get("sample_rate"),
            }
        )
        manifest_out.append(row)
        print(
            f"  [OK] #{it['idx']:02d} ({gender.upper()} | {voice_id}) "
            f"dur={dur:.2f}s | gen={meta.get('elapsed_seconds')}s | RTF={meta.get('rtf')} — {it['tts']}"
        )

    manifest_path.write_text(
        json.dumps(manifest_out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest_path

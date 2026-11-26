#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CARBON AB_07 VOICE & AUDIO PIPELINE — Tích hợp chuẩn vào dự án Video TikTok
==========================================================================
Đóng gói trọn bộ công thức âm thanh từ file chuẩn đã chốt:
`AB_07_CHECK_CoSFX_CungAmLuong_12.7LUFS.wav`

Gồm 3 thành phần cốt lõi:
1. Mô hình `Blaze AI VieNeu-TTS v3 Turbo d3 (FP32, 48kHz)` chạy trong `.venv` Python 3.12
   (tự động gọi ngầm từ Python 3.14 của dự án chính — không xung đột môi trường).
2. Tự động phân 3 tầng giọng (`TELL ~130Hz`, `ASK ~164Hz`, `DROP ~104Hz`) từ `assets/voice_refs_carbon/`
   + chấm điểm chọn Best-of-4 take tự nhiên (không dùng `atempo` gây méo phụ âm).
3. Mixer chuẩn `AB_07`:
   - Cắt ồm `<95Hz` & `-3.0dB @ 180Hz`, đẩy rõ thân `750Hz (+1.8dB)`, bù độ đanh nảy chữ `2500Hz (+4.2dB)`.
   - Giữ trọn `pop_sfx` đầu tin nhắn + `after_sfx` sau câu chốt + tùy chọn BGM ducking / Music Drop.
   - Chuẩn hóa 2-pass đạt đúng `-12.8 LUFS` (ngang bằng bản gốc Con Bò `-12.7 LUFS`).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

THIS_DIR = Path(__file__).resolve().parent
WORKSPACE = THIS_DIR.parent
CIT_VENV_PY = THIS_DIR / "cit-voice-studio" / ".venv" / "Scripts" / "python.exe"
CARBON_REFS_DIR = WORKSPACE / "assets" / "voice_refs_carbon"
DEFAULT_BGM = WORKSPACE / "assets" / "sfx_pack" / "bgm_office_comedy_loop.wav"


def setup_ffmpeg() -> None:
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    local_apps = Path(os.path.expandvars(r"%LOCALAPPDATA%\CapCut\Apps"))
    if local_apps.is_dir():
        for exe in sorted(local_apps.rglob("ffmpeg.exe"), reverse=True):
            tool_dir = str(exe.parent)
            if tool_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = tool_dir + os.pathsep + os.environ.get("PATH", "")
            break


def probe_duration(path: Path) -> float:
    setup_ffmpeg()
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


def infer_register_for_item(it: Dict) -> str:
    """
    Tự động chọn tầng giọng `TELL` / `ASK` / `DROP` cho từng tin nhắn nếu kịch bản không ghi cứng `it["register"]`:
    - Nếu có `it["register"]` in ("TELL", "ASK", "DROP") -> ưu tiên tuyệt đối.
    - Câu hỏi (`?`) hoặc lời cướp nhịp ngạc nhiên (`Ơ,`, `Ủa`, `Sao `, `Thế sao`, `Hả`) -> `ASK` (~164 Hz).
    - Câu chốt ngắn mặt lạnh / buông xuôi (`Không.`, `Phải liều thôi`, `Phải chịu`, <= 5 từ mang tính chốt) -> `DROP` (~104 Hz).
    - Còn lại -> `TELL` (~130 Hz đĩnh đạc).
    """
    explicit = str(it.get("register", "")).upper().strip()
    if explicit in ("TELL", "ASK", "DROP"):
        return explicit

    tts_text = str(it.get("tts") or it.get("text") or "").strip()
    low = tts_text.lower()
    words = tts_text.split()

    if "?" in tts_text or low.startswith(("ơ,", "ơ ", "ủa", "sao ", "thế sao", "thế anh", "thế mai")):
        return "ASK"

    drop_keywords = (
        "không.",
        "phải liều thôi",
        "phải chịu",
        "dị ứng",
        "thủ lĩnh",
        "hết cứu",
        "chịu rồi",
        "thôi xong",
    )
    if len(words) <= 5 and any(k in low for k in drop_keywords):
        return "DROP"
    if any(k in low for k in ("phải liều thôi", "phải chịu thôi", "phải chịu, phải chịu")):
        return "DROP"

    return "TELL"


def synthesize_carbon_voices(
    items: List[Dict],
    out_dir: Path,
    mode: str = "all_conbo",
    female_voice: str = "Trúc Ly",
    end_card_female: bool = True,
    n_candidates: int = 6,
    reuse_cache: bool = True,
) -> Path:
    """
    Tổng hợp thoại cho toàn bộ `ITEMS` của một tập video và xuất `manifest.json` chuẩn:
    - `mode="all_conbo"`  : Mọi nhân vật chat đều dùng giọng nam Carbon 3 tầng (chuẩn kênh Con Bò Đi Làm gốc).
    - `mode="dual_gender"`: Nhân vật `"gender": "male"` dùng Carbon 3 tầng; `"gender": "female"` dùng `Trúc Ly` (FP32).
    """
    setup_ffmpeg()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    job_file = out_dir / "_carbon_job.json"
    job_payload = {
        "items": items,
        "out_dir": str(out_dir.resolve()),
        "refs_dir": str(CARBON_REFS_DIR.resolve()),
        "mode": mode,
        "female_voice": female_voice,
        "end_card_female": end_card_female,
        "n_candidates": n_candidates,
        "reuse_cache": reuse_cache,
    }
    job_file.write_text(json.dumps(job_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    try:
        subprocess.run(
            [str(CIT_VENV_PY), "-u", str(Path(__file__).resolve()), "--worker-job", str(job_file)],
            env=env,
            check=True,
        )
    finally:
        job_file.unlink(missing_ok=True)

    return out_dir / "manifest.json"


def _run_worker_job(job_path: Path) -> int:
    """Chạy bên trong `.venv` Python 3.12 của CIT Voice Studio."""
    import librosa
    import numpy as np
    import soundfile as sf

    cit_root = THIS_DIR / "cit-voice-studio"
    sys.path.insert(0, str(cit_root))
    sys.path.insert(0, str(cit_root / "src"))
    from apps.runtime_paths import setup_hf_home

    setup_hf_home()
    from vieneu import Vieneu

    setup_ffmpeg()
    job = json.loads(job_path.read_text(encoding="utf-8"))
    items: List[Dict] = job["items"]
    out_dir = Path(job["out_dir"])
    refs_dir = Path(job["refs_dir"])
    mode = job["mode"]
    female_voice = job["female_voice"]
    end_card_female = bool(job["end_card_female"])
    n_candidates = int(job["n_candidates"])
    reuse_cache = bool(job["reuse_cache"])

    refs = {
        "TELL": refs_dir / "ref_TELL.wav",
        "ASK": refs_dir / "ref_ASK.wav",
        "DROP": refs_dir / "ref_DROP.wav",
    }
    for k, rp in refs.items():
        if not rp.exists():
            raise FileNotFoundError(f"Thiếu file mẫu giọng Carbon '{k}' tại: {rp}")

    manifest_path = out_dir / "manifest.json"
    prev_map: Dict[int, Dict] = {}
    if reuse_cache and manifest_path.exists():
        try:
            for prev in json.loads(manifest_path.read_text(encoding="utf-8")):
                prev_map[prev.get("idx")] = prev
        except Exception:
            prev_map = {}

    tts = None

    def get_tts():
        nonlocal tts
        if tts is None:
            print("  [Carbon] Đang nạp Blaze AI VieNeu-TTS v3 Turbo d3 (FP32 48kHz)...")
            tts = Vieneu(
                mode="v3turbo",
                backbone_repo="cuongyd196/VieNeu-TTS-v3-Turbo-d3",
                precision="fp32",
                backend="onnx",
            )
        return tts

    target_f0_map = {"TELL": 131.0, "ASK": 162.0, "DROP": 104.0}
    target_sps_map = {"TELL": 5.80, "ASK": 5.85, "DROP": 5.15}
    all_temps = [0.42, 0.46, 0.50, 0.54, 0.58, 0.62]
    temps = all_temps[: max(1, min(len(all_temps), n_candidates))]
    manifest_out: List[Dict] = []

    def count_vi_syllables(txt: str) -> int:
        cleaned = re.sub(r"[^\w\s\-À-ỹ]", " ", txt)
        return max(1, len([w for w in re.split(r"[\s\-]+", cleaned) if w]))

    def calc_active_sps(wav_arr: np.ndarray, sample_rate: int, n_syl: int) -> float:
        ivs = librosa.effects.split(wav_arr, top_db=35, frame_length=1024, hop_length=256)
        voiced_dur = sum((b - a) for a, b in ivs) / float(sample_rate) if len(ivs) else (len(wav_arr) / float(sample_rate))
        return n_syl / max(0.12, voiced_dur)

    def apply_micro_atempo(wav_arr: np.ndarray, sample_rate: int, rate: float, idx_tag: int) -> np.ndarray:
        tmp_in = out_dir / f"_tmp_in_{idx_tag}.wav"
        tmp_out = out_dir / f"_tmp_out_{idx_tag}.wav"
        try:
            sf.write(str(tmp_in), wav_arr, sample_rate)
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(tmp_in),
                    "-af",
                    f"atempo={rate:.4f}",
                    "-ar",
                    str(sample_rate),
                    "-ac",
                    "1",
                    str(tmp_out),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            clamped, _ = sf.read(str(tmp_out))
            if clamped.ndim > 1:
                clamped = clamped.mean(axis=1)
            clamped = clamped.astype(np.float32)
            trimmed_c, _ = librosa.effects.trim(clamped, top_db=48, frame_length=1024, hop_length=256)
            return trimmed_c if len(trimmed_c) > int(0.15 * sample_rate) else clamped
        finally:
            tmp_in.unlink(missing_ok=True)
            tmp_out.unlink(missing_ok=True)

    for it in items:
        row = dict(it)
        is_end = it.get("kind") == "end_card"
        needs_voice = (it.get("kind") == "msg" and it.get("tts")) or (is_end and it.get("tts"))
        if not needs_voice:
            manifest_out.append(row)
            continue

        orig_gender = row.get("gender", "female" if is_end else "male")
        use_female = (is_end and end_card_female) or (mode == "dual_gender" and orig_gender == "female")

        if use_female:
            reg = "FEMALE"
            voice_tag = f"carbon_d3_fp32:preset:{female_voice}"
            row["gender"] = "female"
        else:
            reg = infer_register_for_item(row)
            voice_tag = f"carbon_d3_fp32:3reg:{reg}"
            row["gender"] = "male"
            row["register"] = reg

        final_wav = out_dir / f"voice_{it['idx']:02d}_{it.get('code', 'VOC')}.wav"
        prev = prev_map.get(it["idx"])
        if (
            reuse_cache
            and prev
            and final_wav.exists()
            and prev.get("tts") == it.get("tts")
            and prev.get("voice_name") == voice_tag
            and prev.get("audio_file") == final_wav.name
        ):
            dur = probe_duration(final_wav)
            row["audio_file"] = final_wav.name
            row["voice_name"] = voice_tag
            row["duration_sec"] = round(dur, 4)
            if "active_sps" in prev:
                row["active_sps"] = prev["active_sps"]
            if "n_syl" in prev:
                row["n_syl"] = prev["n_syl"]
            if "f0_hz" in prev:
                row["f0_hz"] = prev["f0_hz"]
            manifest_out.append(row)
            print(f"  [CACHE] #{it['idx']:02d} [{voice_tag}] {dur:.2f}s")
            continue

        engine = get_tts()
        sr = engine.sample_rate
        text = str(it["tts"]).strip()
        n_syl = count_vi_syllables(text)
        active_sps_logged = 0.0
        atempo_used = 1.0

        if use_female:
            raw = engine.infer(
                text=text,
                voice=female_voice,
                temperature=0.58,
                top_k=22,
                top_p=0.92,
                repetition_penalty=1.25,
                apply_watermark=False,
            )
            trimmed, _ = librosa.effects.trim(raw.astype(np.float32), top_db=46)
            best_wav = trimmed if len(trimmed) > int(0.18 * sr) else raw.astype(np.float32)
            f0_logged = 0.0
            active_sps_logged = calc_active_sps(best_wav, sr, n_syl)
        else:
            target_f0 = target_f0_map[reg]
            target_sps = target_sps_map[reg]
            best_sc = -1e9
            best_wav = None
            f0_logged = 0.0
            active_sps_logged = target_sps

            for k, temp in enumerate(temps):
                np.random.seed(2000 + int(it["idx"]) * 41 + k * 17)
                raw = engine.infer(
                    text=text,
                    ref_audio=refs[reg],
                    denoise=False,
                    use_ref_codes=True,
                    temperature=temp,
                    top_k=20 if reg == "DROP" else 24,
                    top_p=0.92,
                    repetition_penalty=1.25,
                    apply_watermark=False,
                )
                trimmed, _ = librosa.effects.trim(raw.astype(np.float32), top_db=48, frame_length=1024, hop_length=256)
                if len(trimmed) < int(0.15 * sr):
                    trimmed = raw.astype(np.float32)
                active_sps = calc_active_sps(trimmed, sr, n_syl)

                f0 = librosa.yin(trimmed, fmin=70, fmax=270, sr=sr, frame_length=2048, hop_length=512)
                frms = librosa.feature.rms(y=trimmed, frame_length=2048, hop_length=512)[0]
                mask = (frms > (np.sqrt(np.mean(trimmed**2)) * 0.32)) & (f0 > 72) & (f0 < 260)
                vf0 = f0[mask]
                if len(vf0) < 3:
                    sc = -500.0 - abs(active_sps - target_sps) * 28.0
                    med_f0 = 0.0
                else:
                    med_f0 = float(np.median(vf0))
                    st_err = abs(12.0 * np.log2(med_f0 / target_f0))
                    if active_sps < 4.5 or active_sps > 6.3:
                        sc = -200.0 - st_err * 5.0 - abs(active_sps - target_sps) * 28.0
                    else:
                        sc = 100.0 - st_err * 5.0 - abs(active_sps - target_sps) * 28.0

                if sc > best_sc:
                    best_sc = sc
                    best_wav = trimmed
                    f0_logged = med_f0
                    active_sps_logged = active_sps

            # Micro-Pace Clamp: khóa cứng active_sps vào đúng dải mục tiêu (TELL/ASK: 5.55-6.05, DROP: 4.95-5.35)
            lo_band, hi_band = (4.95, 5.35) if reg == "DROP" else (5.55, 6.05)
            if best_wav is not None and (active_sps_logged < lo_band or active_sps_logged > hi_band):
                rate = float(np.clip(target_sps / max(0.5, active_sps_logged), 0.90, 1.12))
                best_wav = apply_micro_atempo(best_wav, sr, rate, int(it["idx"]))
                atempo_used = rate
                active_sps_logged = calc_active_sps(best_wav, sr, n_syl)

        # Fade mượt 12ms đầu / 25ms cuối + chuẩn hóa RMS đồng nhất giữa các câu
        fade_in = min(int(0.012 * sr), len(best_wav) // 4)
        fade_out = min(int(0.025 * sr), len(best_wav) // 4)
        out_arr = best_wav.copy()
        if fade_in > 4:
            out_arr[:fade_in] *= np.linspace(0.0, 1.0, fade_in, dtype=np.float32)
        if fade_out > 4:
            out_arr[-fade_out:] *= np.linspace(1.0, 0.0, fade_out, dtype=np.float32)

        rms = float(np.sqrt(np.mean(out_arr**2)) + 1e-9)
        target_rms = 0.125 if reg != "DROP" else 0.120
        out_arr = np.clip(out_arr * (target_rms / rms), -0.95, 0.95)

        sf.write(str(final_wav), out_arr, sr)
        dur = round(len(out_arr) / sr, 4)
        row["audio_file"] = final_wav.name
        row["voice_name"] = voice_tag
        row["duration_sec"] = dur
        row["n_syl"] = n_syl
        row["active_sps"] = round(active_sps_logged, 2)
        row["f0_hz"] = round(f0_logged, 1)
        row["atempo_applied"] = round(atempo_used, 3)
        manifest_out.append(row)
        f0_str = f"F0={f0_logged:5.1f}Hz | " if f0_logged > 0 else ""
        at_str = f" (atempo={atempo_used:.2f})" if abs(atempo_used - 1.0) > 1e-3 else ""
        print(f"  [OK] #{it['idx']:02d} [{voice_tag:26s}] {f0_str}sps={active_sps_logged:4.2f}/s{at_str} | dur={dur:.2f}s — {text}")

    manifest_path.write_text(json.dumps(manifest_out, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def mix_carbon_ab07_audio(
    items_by_idx: Dict[int, Dict],
    events: List[Dict],
    voices_dir: Path,
    output_wav: Path,
    total_dur: float,
    bgm_path: Optional[Path] = None,
    bgm_volume: float = 0.14,
    voice_delay_sec: float = 0.05,
    target_lufs: float = -12.8,
) -> Path:
    """
    Mixer đạt chuẩn âm thanh `AB_07_CHECK_CoSFX_CungAmLuong_12.7LUFS.wav`:
    - EQ giọng Nam Carbon: cắt ồm `95Hz` & `-3.0dB @ 180Hz`, đẩy thân `750Hz (+1.8dB)`, bù đanh sáng `2500Hz (+4.2dB)`.
    - Nén chặt `ratio 3.2:1` cho chữ giòn nảy đều trên loa điện thoại.
    - Pop đầu tin nhắn + After-SFX đánh sát +25ms ngay sau chữ cuối.
    - BGM mặc định tắt (`bgm_path=None` giống hệt bản gốc Con Bò Đi Làm) hoặc bật nhỏ `0.12-0.15` có Music Drop.
    - Chuẩn hóa 2-pass `ebur128` khóa chính xác `-12.8 LUFS`.
    """
    setup_ffmpeg()

    inputs: List[str] = []
    filter_parts: List[str] = []
    speech_labels: List[str] = []
    sfx_labels: List[str] = []
    in_idx = 0
    drop_windows = []

    for ev in events:
        if ev["action"] != "item":
            continue
        it = items_by_idx[ev["item_idx"]]
        start_s = float(ev["time"])
        ev_dur = float(ev["duration"])
        start_ms = int(round(start_s * 1000))

        if it.get("music_drop") or it.get("kind") in ("sys_time", "sys_recall"):
            if it.get("kind") in ("sys_time", "sys_recall"):
                drop_windows.append((max(0.0, start_s - 0.05), start_s + ev_dur))
            elif it.get("audio_file"):
                v_end = start_s + voice_delay_sec + float(it.get("duration_sec", 0.0))
                drop_windows.append((max(0.0, v_end - 0.10), min(total_dur, start_s + ev_dur)))

        pop_rel = it.get("pop_sfx")
        if pop_rel:
            pop_p = WORKSPACE / pop_rel
            if pop_p.exists():
                inputs.extend(["-i", str(pop_p)])
                filter_parts.append(
                    f"[{in_idx}:a]atrim=0:0.14,afade=t=out:st=0.08:d=0.06,"
                    f"adelay={start_ms}|{start_ms},volume=0.26[pop_{it['idx']}];"
                )
                sfx_labels.append(f"[pop_{it['idx']}]")
                in_idx += 1

        v_end_ms = start_ms + int(round(voice_delay_sec * 1000))
        if it.get("audio_file"):
            v_p = voices_dir / it["audio_file"]
            inputs.extend(["-i", str(v_p)])
            v_ms = start_ms + int(round(voice_delay_sec * 1000))
            v_end_ms = v_ms + int(round(float(it.get("duration_sec", 0.0)) * 1000))

            if it.get("gender") == "female":
                eq_chain = (
                    "highpass=f=100,"
                    "equalizer=f=240:t=q:w=1.1:g=1.5,"
                    "equalizer=f=2400:t=q:w=1.2:g=2.2,"
                    "acompressor=threshold=-19dB:ratio=3.0:attack=8:release=95:makeup=2.5"
                )
            else:
                # Công thức EQ chính xác của AB_07
                eq_chain = (
                    "highpass=f=95,"
                    "equalizer=f=180:t=q:w=1.0:g=-3.0,"
                    "equalizer=f=750:t=q:w=1.0:g=1.8,"
                    "equalizer=f=2500:t=q:w=1.1:g=4.2,"
                    "acompressor=threshold=-20dB:ratio=3.2:attack=6:release=90:makeup=3.0"
                )
            filter_parts.append(
                f"[{in_idx}:a]{eq_chain},adelay={v_ms}|{v_ms},volume=1.05[voc_{it['idx']}];"
            )
            speech_labels.append(f"[voc_{it['idx']}]")
            in_idx += 1

        after_rel = it.get("after_sfx")
        if after_rel:
            sfx_p = WORKSPACE / after_rel
            if sfx_p.exists():
                inputs.extend(["-i", str(sfx_p)])
                if it.get("kind") in ("sys_time", "sys_recall"):
                    sfx_ms = start_ms
                    nat_dur = probe_duration(sfx_p)
                    sfx_dur = min(nat_dur, max(0.5, float(it.get("after_sfx_dur", ev_dur))))
                    sfx_vol = float(it.get("after_sfx_vol", 0.88))
                else:
                    sfx_ms = v_end_ms + 25
                    nat_dur = probe_duration(sfx_p)
                    sfx_dur = min(nat_dur, float(it.get("after_sfx_dur", min(nat_dur, 1.45))))
                    sfx_vol = float(it.get("after_sfx_vol", 0.72))

                fade_d = min(0.18, sfx_dur * 0.16)
                fade_st = max(0.05, sfx_dur - fade_d)
                filter_parts.append(
                    f"[{in_idx}:a]atrim=0:{sfx_dur:.3f},afade=t=out:st={fade_st:.3f}:d={fade_d:.3f},"
                    f"adelay={sfx_ms}|{sfx_ms},volume={sfx_vol:.2f}[asfx_{it['idx']}];"
                )
                sfx_labels.append(f"[asfx_{it['idx']}]")
                in_idx += 1

    bgm_label = None
    if bgm_path and Path(bgm_path).exists() and bgm_volume > 0.001:
        inputs.extend(["-stream_loop", "-1", "-i", str(bgm_path)])
        bgm_in = in_idx
        in_idx += 1
        bgm_chain = [
            f"atrim=0:{total_dur:.3f}",
            f"volume={bgm_volume:.3f}",
            "lowpass=f=4500",
            "afade=t=in:st=0:d=0.18",
            f"afade=t=out:st={max(0.0, total_dur - 0.45):.3f}:d=0.45",
        ]
        for t0, t1 in drop_windows:
            if t1 > t0 + 0.05:
                bgm_chain.append(f"volume=enable='between(t,{t0:.3f},{t1:.3f})':volume=0.0")
        filter_parts.append(f"[{bgm_in}:a]{','.join(bgm_chain)}[bgm_raw];")
        bgm_label = "[bgm_raw]"

    mix_inputs = []
    if speech_labels:
        filter_parts.append(
            f"{''.join(speech_labels)}amix=inputs={len(speech_labels)}:duration=longest:normalize=0[voc_bus];"
        )
        if bgm_label:
            filter_parts.append("[voc_bus]asplit=2[voc_main][voc_sc];")
            filter_parts.append(
                f"{bgm_label}[voc_sc]sidechaincompress=threshold=0.04:ratio=3.5:attack=15:release=180[bgm_ducked];"
            )
            mix_inputs.extend(["[voc_main]", "[bgm_ducked]"])
        else:
            mix_inputs.append("[voc_bus]")
    elif bgm_label:
        mix_inputs.append(bgm_label)

    mix_inputs.extend(sfx_labels)
    pre_wav = output_wav.with_name(output_wav.stem + "_premaster.wav")
    filter_parts.append(
        f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=longest:normalize=0,"
        f"alimiter=limit=0.92[preout]"
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex",
            "".join(filter_parts),
            "-map",
            "[preout]",
            "-t",
            f"{total_dur:.3f}",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(pre_wav),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    # Pass 2: Đo ebur128 thực tế và nâng chính xác lên `target_lufs` (-12.8 LUFS chuẩn AB_07)
    err = subprocess.run(
        ["ffmpeg", "-nostats", "-i", str(pre_wav), "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
    ).stderr
    m_lufs = re.findall(r"I:\s*([-\d\.]+)\s*LUFS", err)
    cur_lufs = float(m_lufs[-1]) if m_lufs else -16.0
    gain_db = target_lufs - cur_lufs

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(pre_wav),
            "-af",
            f"volume={gain_db:.2f}dB,alimiter=limit=0.84:level=false",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(output_wav),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    pre_wav.unlink(missing_ok=True)
    return output_wav


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--worker-job":
        sys.exit(_run_worker_job(Path(sys.argv[2])))
    print("Module carbon_voice_pipeline sẵn sàng. Import từ script render của bạn.")

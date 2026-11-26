#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zero-shot Voice Cloning Cover Generator (VieNeu-TTS v3 Turbo từ CIT Voice Studio)
Dùng 3 mẫu giọng tách sạch 0% SFX từ Video_mẫu.mp4 + căn chính xác nhịp độ tiết tấu
và khoảng nghỉ comic beat của bản gốc.

Xuất 2 bộ file cho mỗi cấu hình:
  1. AB_*.wav  : Đối chiếu 1-1 đúng thoại bản gốc Video_mẫu.mp4
  2. MOI_*.wav : Kiểm chứng trên kịch bản MỚI (Tập 2 - Hồ Cá Koi)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import librosa
import numpy as np
import soundfile as sf

BASE = Path(__file__).resolve().parent
CIT_ROOT = BASE / "cit-voice-studio"
sys.path.insert(0, str(CIT_ROOT))
sys.path.insert(0, str(CIT_ROOT / "src"))

# Dùng lại cache model đã tải sẵn của CIT Voice Studio
from apps.runtime_paths import setup_hf_home

setup_hf_home()
from vieneu import Vieneu

REFS_DIR = BASE / "voice_analysis" / "refs_clean"
PROFILE_PATH = BASE / "voice_analysis" / "video_mau_profile.json"
OUT_DIR = BASE / "voice_covers_v2_clone"
TMP_DIR = OUT_DIR / "_tmp"

# Kịch bản A/B đối chiếu 1-1 bản gốc (text, atempo_speed, pause_after_sec)
AB_SCENE: List[Tuple[str, float, float]] = [
    ("Thích là một chuyện.", 1.12, 0.44),
    ("Hạch toán chi phí là chuyện khác.", 1.08, 0.50),
    ("Và từ đó anh trở thành", 1.05, 0.30),
    ("một người cuồng mèo?", 1.12, 0.45),
    ("Không.", 0.96, 0.56),
    ("Thế anh trở thành gì?", 1.12, 0.46),
    ("Thủ lĩnh loài bò.", 0.96, 0.25),
]

# Kịch bản MỚI trích Tập 2 (Hồ Cá Koi) để kiểm chứng nói câu mới có giữ nguyên độ bựa & nhịp không
NEW_SCENE: List[Tuple[str, float, float]] = [
    ("Anh có chuyện muốn nói.", 1.08, 0.36),
    ("Hố trước sân sửa thành hồ cá Koi nhé.", 1.06, 0.48),
    ("Ơ, thế là chuyển từ bơi sang câu cá à sếp?", 1.14, 0.46),
    ("Quả này anh nghĩ rồi.", 1.05, 0.42),
    ("Phải liều thôi.", 0.96, 0.52),
    ("Chụp màn hình rồi nha anh.", 1.12, 0.34),
    ("Chậm đơn khách chửi thì anh tự nghe máy.", 1.04, 0.25),
]

# 6 cấu hình clone sạch (so sánh 3 đoạn ref sạch × denoise × temperature × use_ref_codes)
CLONE_CONFIGS = [
    {
        "id": "01_RefA_KeChuyen_NoDenoise",
        "ref": REFS_DIR / "refA_sach_ke_chuyen.wav",
        "denoise": False,
        "use_ref_codes": True,
        "temperature": 0.45,
        "top_k": 20,
        "top_p": 0.92,
        "rep_pen": 1.25,
        "note": "Mẫu kể chuyện sạch 6.1s · tắt denoise giữ trọn màu âm 48kHz · temp 0.45",
    },
    {
        "id": "02_RefB_MatLanh_NoDenoise",
        "ref": REFS_DIR / "refB_sach_deadpan.wav",
        "denoise": False,
        "use_ref_codes": True,
        "temperature": 0.40,
        "top_k": 18,
        "top_p": 0.90,
        "rep_pen": 1.25,
        "note": "Mẫu mặt lạnh/chốt bựa 7.1s · tắt denoise · temp 0.40 cực deadpan",
    },
    {
        "id": "03_RefC_TongHop_NoDenoise",
        "ref": REFS_DIR / "refC_sach_tong_hop.wav",
        "denoise": False,
        "use_ref_codes": True,
        "temperature": 0.48,
        "top_k": 22,
        "top_p": 0.92,
        "rep_pen": 1.25,
        "note": "Mẫu tổng hợp hỏi+đáp+chốt 7.5s · tắt denoise · linh hoạt nhiều kiểu câu",
    },
    {
        "id": "04_RefB_TuNhien_Temp065",
        "ref": REFS_DIR / "refB_sach_deadpan.wav",
        "denoise": False,
        "use_ref_codes": True,
        "temperature": 0.65,
        "top_k": 28,
        "top_p": 0.95,
        "rep_pen": 1.20,
        "note": "Mẫu mặt lạnh · tăng temp 0.65 cho ngữ điệu thoáng/tự nhiên hơn",
    },
    {
        "id": "05_RefB_DenoiseOn",
        "ref": REFS_DIR / "refB_sach_deadpan.wav",
        "denoise": True,
        "use_ref_codes": True,
        "temperature": 0.45,
        "top_k": 20,
        "top_p": 0.92,
        "rep_pen": 1.25,
        "note": "Mẫu mặt lạnh · bật bộ lọc denoise của VieNeu để so độ sạch",
    },
    {
        "id": "06_RefC_PureEmb_NoRefCodes",
        "ref": REFS_DIR / "refC_sach_tong_hop.wav",
        "denoise": False,
        "use_ref_codes": False,
        "temperature": 0.50,
        "top_k": 22,
        "top_p": 0.92,
        "rep_pen": 1.25,
        "note": "Chỉ dùng speaker embedding (bỏ ref_codes) để so độ trong trẻo",
    },
]


def setup_ffmpeg() -> None:
    if shutil.which("ffmpeg"):
        return
    local_apps = Path(os.path.expandvars(r"%LOCALAPPDATA%\CapCut\Apps"))
    if local_apps.is_dir():
        for exe in sorted(local_apps.rglob("ffmpeg.exe"), reverse=True):
            os.environ["PATH"] = str(exe.parent) + os.pathsep + os.environ.get("PATH", "")
            return
    raise RuntimeError("Không tìm thấy ffmpeg!")


def trim_and_pace_segment(wav_arr: np.ndarray, sr: int, speed: float) -> np.ndarray:
    """Trim sạch khoảng lặng đầu/cuối từng câu + chỉnh nhịp atempo chuẩn không méo cao độ."""
    src_p = TMP_DIR / "seg_in.wav"
    dst_p = TMP_DIR / "seg_out.wav"
    sf.write(str(src_p), wav_arr.astype(np.float32), sr)

    filters = [
        "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-40dB",
        "areverse",
        "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-40dB",
        "areverse",
    ]
    if abs(speed - 1.0) > 0.01:
        filters.append(f"atempo={speed:.3f}")
    filters.append("apad=pad_dur=0.015")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src_p),
            "-af",
            ",".join(filters),
            "-ar",
            str(sr),
            "-ac",
            "1",
            str(dst_p),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    y, _ = sf.read(str(dst_p), dtype="float32")
    src_p.unlink(missing_ok=True)
    dst_p.unlink(missing_ok=True)
    return y


def master_clean(src_wav: Path, dst_wav: Path) -> None:
    """Mastering trong suốt (không bóp méo màu giọng clone): chỉ cắt ù <75Hz + nén nhẹ + -14.5 LUFS."""
    filters = [
        "highpass=f=75",
        "acompressor=threshold=-18dB:ratio=2.4:attack=10:release=100:makeup=2",
        "loudnorm=I=-14.5:TP=-1.2:LRA=7",
    ]
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src_wav),
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


def measure_likeness(wav_path: Path, ref_profile: dict) -> dict:
    y, sr = librosa.load(str(wav_path), sr=24000, mono=True)
    y_trim, _ = librosa.effects.trim(y, top_db=30)

    f0, voiced, prob = librosa.pyin(
        y_trim, fmin=65.0, fmax=260.0, sr=sr, frame_length=2048, hop_length=256
    )
    mask = voiced & (prob > 0.65) & (~np.isnan(f0))
    vf0 = f0[mask]
    f0_med = float(np.median(vf0)) if len(vf0) > 5 else 0.0
    f0_iqr_st = (
        float(12.0 * np.log2(np.percentile(vf0, 75) / np.percentile(vf0, 25)))
        if len(vf0) > 5
        else 0.0
    )

    S = np.abs(librosa.stft(y_trim, n_fft=2048, hop_length=512)) ** 2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    psd = S.mean(axis=1)
    warm_pct = float(100.0 * psd[(freqs >= 200) & (freqs < 500)].sum() / (psd.sum() + 1e-12))

    mfcc = librosa.feature.mfcc(y=y_trim, sr=sr, n_mfcc=13).mean(axis=1)
    ref_mfcc = np.array(ref_profile["spectral"]["mfcc_mean"], dtype=np.float32)
    a, b = mfcc[1:], ref_mfcc[1:]
    mfcc_cos = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

    ref_f0 = float(ref_profile["f0_hz"]["median"])
    f0_diff_st = float(12.0 * np.log2(f0_med / ref_f0)) if f0_med > 0 else 99.0

    score = (
        mfcc_cos * 60.0
        - abs(f0_diff_st) * 3.0
        - abs(f0_iqr_st - ref_profile["f0_hz"]["iqr_semitones"]) * 2.0
        - abs(warm_pct - ref_profile["spectral"]["band_energy_pct"]["warmth_200_500"]) * 0.25
    )
    return {
        "dur_s": round(len(y) / sr, 2),
        "f0_median_hz": round(f0_med, 1),
        "f0_diff_semitones": round(f0_diff_st, 2),
        "f0_iqr_semitones": round(f0_iqr_st, 2),
        "warmth_200_500_pct": round(warm_pct, 1),
        "mfcc_cosine": round(mfcc_cos, 4),
        "similarity_score": round(score, 2),
    }


def render_scene_clone(
    tts,
    scene: List[Tuple[str, float, float]],
    cfg: dict,
    out_wav: Path,
) -> None:
    sr = tts.sample_rate
    chunks: List[np.ndarray] = []
    for text, spd, pause_s in scene:
        wav = tts.infer(
            text=text,
            ref_audio=cfg["ref"],
            denoise=cfg["denoise"],
            use_ref_codes=cfg["use_ref_codes"],
            temperature=cfg["temperature"],
            top_k=cfg["top_k"],
            top_p=cfg["top_p"],
            repetition_penalty=cfg["rep_pen"],
            apply_watermark=False,
        )
        y_seg = trim_and_pace_segment(wav, sr=sr, speed=spd)
        chunks.append(y_seg)
        if pause_s > 0:
            chunks.append(np.zeros(int(round(pause_s * sr)), dtype=np.float32))

    raw_full = TMP_DIR / "full_raw.wav"
    sf.write(str(raw_full), np.concatenate(chunks), sr)
    master_clean(raw_full, out_wav)
    raw_full.unlink(missing_ok=True)


def main() -> int:
    setup_ffmpeg()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    ref_profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

    # Copy đoạn gốc A/B vào chung thư mục để bật so sánh ngay
    src_ab = BASE / "voice_covers" / "00_GOC_Video_mau_AB_25s_47s.wav"
    if src_ab.exists():
        shutil.copy2(src_ab, OUT_DIR / src_ab.name)

    print("Đang nạp VieNeu-TTS v3 Turbo (int8 ONNX từ cache CIT Voice Studio)...")
    tts = Vieneu(mode="v3turbo", precision="int8", backend="onnx")
    print(f"Sẵn sàng (sr={tts.sample_rate}Hz)\n")

    results = []
    for cfg in CLONE_CONFIGS:
        cid = cfg["id"]
        ab_wav = OUT_DIR / f"AB_{cid}.wav"
        new_wav = OUT_DIR / f"MOI_HoCaKoi_{cid}.wav"

        print(f"--- Đang tạo {cid} ---")
        render_scene_clone(tts, AB_SCENE, cfg, ab_wav)
        render_scene_clone(tts, NEW_SCENE, cfg, new_wav)

        feats = measure_likeness(ab_wav, ref_profile)
        rec = {
            "id": cid,
            "ab_file": ab_wav.name,
            "new_script_file": new_wav.name,
            "note": cfg["note"],
            **feats,
        }
        results.append(rec)
        print(
            f"  [OK] {ab_wav.name:36s} | F0={feats['f0_median_hz']:5.1f}Hz ({feats['f0_diff_semitones']:+5.2f}st) | "
            f"IQR={feats['f0_iqr_semitones']:4.2f}st | Warm={feats['warmth_200_500_pct']:4.1f}% | "
            f"MFCC={feats['mfcc_cosine']:.4f} | Score={feats['similarity_score']:5.2f}"
        )

    shutil.rmtree(TMP_DIR, ignore_errors=True)
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    report_p = OUT_DIR / "clone_report.json"
    report_p.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nHOÀN TẤT! Báo cáo lưu tại: {report_p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

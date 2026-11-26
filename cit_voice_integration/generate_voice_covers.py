#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phân tích đối chiếu toàn bộ giọng nam (CIT Voice Studio + Edge-TTS) với Video_mẫu.mp4
và xuất bộ giọng COVER đã căn chuẩn:
  1. Nhịp độ tiết tấu từng câu (tốc độ nhanh/chậm theo pha dẫn -> hỏi -> chốt)
  2. Khoảng nghỉ comic beat chính xác tới mili-giây (đo trực tiếp từ Video_mẫu.mp4)
  3. Chuỗi DSP định hình màu âm chuẩn Video_mẫu.mp4 (dày dải 200-500Hz, gọt chói >4.8kHz, nén động lực ~7dB, -14.5 LUFS)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import librosa
import numpy as np
import soundfile as sf

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from cit_voice_client import CitVoiceClient

PROFILE_PATH = BASE / "voice_analysis" / "video_mau_profile.json"
OUT_DIR = BASE / "voice_covers"
RAW_DIR = OUT_DIR / "_raw_tmp"

# Đoạn thoại chuẩn A/B test lấy đúng các câu đặc trưng nhất của Video_mẫu.mp4
# Mỗi tuple: (text, target_speed_ratio, pause_after_sec, role_note)
# Nhịp được căn chuẩn theo profile đo được từ Video_mẫu.mp4:
#   - Dẫn/lập luận: ~4.7-5.2 syl/s | Ngắt giữa 2 vế: 0.45s
#   - Hỏi gắt: ~5.2 syl/s | Ngắt trước cú twist: 0.48s
#   - Chốt deadpan ("Không.", "Thủ lĩnh loài bò."): chậm hơn ~0.95-1.00x, dứt khoát
SCENE_LINES = [
    ("Thích là một chuyện.", 1.12, 0.44, "setup_fast"),
    ("Hạch toán chi phí là chuyện khác.", 1.08, 0.52, "deadpan_fact"),
    ("Và từ đó anh trở thành", 1.04, 0.30, "build_up"),
    ("một người cuồng mèo?", 1.12, 0.46, "question_hook"),
    ("Không.", 0.96, 0.56, "flat_drop"),
    ("Thế anh trở thành gì?", 1.14, 0.46, "quick_ask"),
    ("Thủ lĩnh loài bò.", 0.96, 0.25, "punchline"),
]

# Danh sách toàn bộ giọng nam Bắc + 1 giọng Nam nổi bật trong CIT Voice Studio
CIT_MALE_CANDIDATES = [
    ("Minh Đức", "Tin tức · Bắc (nghiêm túc/deadpan)"),
    ("Hải Đăng", "Tự nhiên · Bắc"),
    ("Thiện Minh", "Kể chuyện · Bắc"),
    ("Thanh Bình", "Kể chuyện · Bắc"),
    ("Quốc Tuấn", "Tự nhiên · Bắc"),
    ("Phạm Tuyên", "Tự nhiên · Bắc"),
    ("Xuân Vĩnh", "Tự nhiên · Bắc"),
    ("Thiền Tâm Đức", "Kể chuyện · Bắc (trầm)"),
    ("Adam bựa", "Tự nhiên · Bắc (đang dùng)"),
    ("Adam", "Tự nhiên · Nam"),
]


def setup_ffmpeg() -> str:
    ff = shutil.which("ffmpeg")
    if ff:
        return str(Path(ff).parent)
    local_apps = Path(os.path.expandvars(r"%LOCALAPPDATA%\CapCut\Apps"))
    if local_apps.is_dir():
        for exe in sorted(local_apps.rglob("ffmpeg.exe"), reverse=True):
            tool_dir = str(exe.parent)
            os.environ["PATH"] = tool_dir + os.pathsep + os.environ.get("PATH", "")
            return tool_dir
    raise RuntimeError("Không tìm thấy ffmpeg!")


def trim_segment_to_array(wav_path: Path, target_sr: int = 48000, extra_atempo: float = 1.0) -> np.ndarray:
    """Cắt sạch im lặng đầu/cuối từng câu bằng ffmpeg để khóa nhịp độ chuẩn tới từng 10ms."""
    tmp_out = wav_path.with_suffix(".trim.wav")
    filters = [
        "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-40dB",
        "areverse",
        "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-40dB",
        "areverse",
    ]
    if abs(extra_atempo - 1.0) > 0.01:
        filters.append(f"atempo={extra_atempo:.3f}")
    filters.append("apad=pad_dur=0.015")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(wav_path),
            "-af",
            ",".join(filters),
            "-ar",
            str(target_sr),
            "-ac",
            "1",
            str(tmp_out),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    y, _ = sf.read(str(tmp_out), dtype="float32")
    tmp_out.unlink(missing_ok=True)
    return y


def apply_conbo_dsp(
    src_wav: Path,
    dst_wav: Path,
    pitch_semitones: float = 0.0,
    sr: int = 48000,
) -> None:
    """
    Áp chuỗi DSP khớp màu âm Video_mẫu.mp4:
    - Tùy chọn dịch cao độ nhẹ giữ tốc độ (asetrate + aresample + atempo)
    - HPF 80Hz, boost ấm 280Hz (+3.5dB), rõ chữ 2.2kHz (+1.5dB), gọt chói LPF 5.2kHz
    - Nén chặt (acompressor) để dynamic range ~7dB giống giọng TV/TikTok deadpan
    - Chuẩn hóa âm lượng -14.5 LUFS
    """
    filters: List[str] = []

    if abs(pitch_semitones) >= 0.15:
        ratio = 2.0 ** (pitch_semitones / 12.0)
        new_sr = int(round(sr * ratio))
        inv_tempo = 1.0 / ratio
        filters.append(f"asetrate={new_sr}")
        filters.append(f"aresample={sr}")
        filters.append(f"atempo={inv_tempo:.4f}")

    filters.extend(
        [
            "highpass=f=80",
            "equalizer=f=280:t=q:w=1.1:g=3.5",
            "equalizer=f=900:t=q:w=1.2:g=-1.2",
            "equalizer=f=2200:t=q:w=1.4:g=1.8",
            "lowpass=f=5200",
            "acompressor=threshold=-20dB:ratio=3.5:attack=8:release=90:makeup=3",
            "loudnorm=I=-14.5:TP=-1.5:LRA=6",
        ]
    )

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


def measure_voice_features(wav_path: Path, ref_profile: dict) -> dict:
    """Đo F0, độ phẳng ngữ điệu, spectral centroid, dải ấm 200-500Hz và độ tương đồng MFCC vs Video_mẫu."""
    y, sr = librosa.load(str(wav_path), sr=24000, mono=True)
    y_trim, _ = librosa.effects.trim(y, top_db=30)

    f0, voiced, prob = librosa.pyin(
        y_trim, fmin=65.0, fmax=260.0, sr=sr, frame_length=2048, hop_length=256
    )
    mask = voiced & (prob > 0.65) & (~np.isnan(f0))
    vf0 = f0[mask]

    if len(vf0) > 5:
        f0_med = float(np.median(vf0))
        f0_iqr_st = float(12.0 * np.log2(np.percentile(vf0, 75) / np.percentile(vf0, 25)))
    else:
        f0_med = 0.0
        f0_iqr_st = 0.0

    # Spectral & MFCC
    S = np.abs(librosa.stft(y_trim, n_fft=2048, hop_length=512)) ** 2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    psd = S.mean(axis=1)
    total_e = psd.sum() + 1e-12
    warm_pct = float(100.0 * psd[(freqs >= 200) & (freqs < 500)].sum() / total_e)
    centroid = float(np.median(librosa.feature.spectral_centroid(y=y_trim, sr=sr)))
    mfcc = librosa.feature.mfcc(y=y_trim, sr=sr, n_mfcc=13).mean(axis=1)

    ref_mfcc = np.array(ref_profile["spectral"]["mfcc_mean"], dtype=np.float32)
    # Cosine similarity bỏ hệ số MFCC[0] (năng lượng tổng) để chỉ so sánh màu giọng thuần túy
    a = mfcc[1:]
    b = ref_mfcc[1:]
    mfcc_cos = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

    ref_f0 = float(ref_profile["f0_hz"]["median"])
    f0_diff_st = float(12.0 * np.log2(f0_med / ref_f0)) if f0_med > 0 else 99.0

    # Điểm tổng hợp (cao hơn = giống màu giọng & độ phẳng deadpan của Video_mẫu hơn)
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
        "centroid_hz": round(centroid, 1),
        "warmth_200_500_pct": round(warm_pct, 1),
        "mfcc_cosine": round(mfcc_cos, 4),
        "similarity_score": round(score, 2),
    }


def synthesize_cit_scene(
    client: CitVoiceClient,
    voice_id: str,
    out_raw_wav: Path,
    temperature: float = 0.45,
    base_speed_mult: float = 1.0,
) -> Path:
    """
    Tổng hợp toàn bộ đoạn thoại theo từng câu với temperature thấp (0.45 -> deadpan ổn định),
    trim sạch im lặng từng câu rồi ghép đúng khoảng nghỉ comic beat chuẩn Video_mẫu.mp4.
    """
    sr = 48000
    chunks: List[np.ndarray] = []
    for idx, (text, spd, pause_s, _role) in enumerate(SCENE_LINES):
        seg_wav = RAW_DIR / f"seg_{idx:02d}.wav"
        eff_speed = round(min(1.45, max(0.80, spd * base_speed_mult)), 3)
        client.generate_to_file(
            text=text,
            out_path=seg_wav,
            voice_id=voice_id,
            speed=eff_speed,
            temperature=temperature,
            fmt="wav",
            seed=42,
        )
        y_seg = trim_segment_to_array(seg_wav, target_sr=sr, extra_atempo=1.0)
        chunks.append(y_seg)
        if pause_s > 0:
            chunks.append(np.zeros(int(round(pause_s * sr)), dtype=np.float32))
        seg_wav.unlink(missing_ok=True)

    full_audio = np.concatenate(chunks)
    out_raw_wav.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_raw_wav), full_audio, sr)
    return out_raw_wav


def synthesize_edge_scene(
    out_raw_wav: Path,
    voice: str = "vi-VN-NamMinhNeural",
    base_rate_pct: int = 12,
    pitch_hz: str = "+0Hz",
) -> Optional[Path]:
    """Dùng system Python (có edge-tts) để tổng hợp bản cover Edge-TTS khớp từng nhịp."""
    sr = 48000
    chunks: List[np.ndarray] = []
    sys_python = shutil.which("python")
    if not sys_python:
        return None

    for idx, (text, spd, pause_s, _role) in enumerate(SCENE_LINES):
        # Đổi hệ số tốc độ từng câu sang % của Edge-TTS
        rate_val = int(round((spd - 1.0) * 100 + base_rate_pct))
        rate_str = f"+{rate_val}%" if rate_val >= 0 else f"{rate_val}%"
        mp3_path = RAW_DIR / f"edge_{idx:02d}.mp3"

        code = (
            "import asyncio, edge_tts, sys\n"
            "async def go():\n"
            "    c = edge_tts.Communicate(sys.argv[1], voice=sys.argv[2], rate=sys.argv[3], pitch=sys.argv[4])\n"
            "    await c.save(sys.argv[5])\n"
            "asyncio.run(go())\n"
        )
        proc = subprocess.run(
            [sys_python, "-c", code, text, voice, rate_str, pitch_hz, str(mp3_path)],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0 or not mp3_path.exists():
            print(f"  [!] Edge-TTS lỗi câu {idx}: {proc.stderr.strip()}")
            return None

        y_seg = trim_segment_to_array(mp3_path, target_sr=sr, extra_atempo=1.0)
        chunks.append(y_seg)
        if pause_s > 0:
            chunks.append(np.zeros(int(round(pause_s * sr)), dtype=np.float32))
        mp3_path.unlink(missing_ok=True)

    full_audio = np.concatenate(chunks)
    out_raw_wav.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_raw_wav), full_audio, sr)
    return out_raw_wav


def main() -> int:
    setup_ffmpeg()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    ref_profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    ref_f0 = ref_profile["f0_hz"]["median"]
    print(
        f"MỤC TIÊU Video_mẫu.mp4: F0={ref_f0} Hz | IQR={ref_profile['f0_hz']['iqr_semitones']} st | "
        f"Warmth(200-500Hz)={ref_profile['spectral']['band_energy_pct']['warmth_200_500']:.1f}% | "
        f"Speed={ref_profile['rhythm']['syl_per_sec_median']} syl/s\n"
    )

    client = CitVoiceClient("http://127.0.0.1:8001")
    client.wait_ready(timeout_sec=30.0)

    results: List[dict] = []

    print("=== BƯỚC 1: SÀNG LỌC TOÀN BỘ 10 GIỌNG NAM CIT VOICE STUDIO (KHÓA NHỊP TIẾT TẤU) ===")
    for idx, (vid, note) in enumerate(CIT_MALE_CANDIDATES, start=1):
        safe_name = (
            vid.replace(" ", "_")
            .replace("Đ", "D")
            .replace("đ", "d")
            .replace("ứ", "u")
            .replace("ả", "a")
            .replace("ă", "a")
            .replace("ệ", "e")
            .replace("ì", "i")
            .replace("ố", "o")
            .replace("ấ", "a")
            .replace("ạ", "a")
            .replace("ê", "e")
            .replace("â", "a")
            .replace("ĩ", "i")
            .replace("ề", "e")
            .replace("ự", "u")
            .replace("ư", "u")
        )
        raw_wav = RAW_DIR / f"cit_{idx:02d}_{safe_name}.wav"
        synthesize_cit_scene(client, vid, raw_wav, temperature=0.45)
        feats = measure_voice_features(raw_wav, ref_profile)

        # Bản mộc chuẩn nhịp (chỉ chuẩn hóa nhẹ -14.5 LUFS, không đổi pitch)
        clean_dst = OUT_DIR / f"01_CIT_Moc_{idx:02d}_{safe_name}.wav"
        apply_conbo_dsp(raw_wav, clean_dst, pitch_semitones=0.0)

        rec = {
            "engine": "CIT-VieNeu",
            "voice": vid,
            "note": note,
            "raw_path": str(raw_wav),
            "cover_file": clean_dst.name,
            **feats,
        }
        results.append(rec)
        print(
            f"  [{idx:02d}] {vid:15s} | F0={feats['f0_median_hz']:5.1f}Hz ({feats['f0_diff_semitones']:+5.2f}st) | "
            f"IQR={feats['f0_iqr_semitones']:4.2f}st | MFCC={feats['mfcc_cosine']:.3f} | Score={feats['similarity_score']:5.2f}"
        )

    print("\n=== BƯỚC 2: TẠO BẢN COVER EDGE-TTS (NAMMINH) CĂN ĐÚNG PITCH & NHỊP CON BÒ ===")
    edge_presets = [
        ("Edge_NamMinh_Deadpan_Goc", 10, "+0Hz", 0.0, "NamMinh gốc + nhịp Con Bò + EQ ấm"),
        ("Edge_NamMinh_Bua_CaoHon", 12, "+6Hz", 0.0, "NamMinh nâng nhẹ pitch (+6Hz) cho gần F0 ~159Hz"),
        ("Edge_NamMinh_Tram_MatLanh", 8, "-4Hz", 0.0, "NamMinh trầm hơn (-4Hz) kiểu sếp mặt lạnh"),
    ]
    for pname, brate, phz, dsp_st, pnote in edge_presets:
        raw_wav = RAW_DIR / f"{pname}.wav"
        ok = synthesize_edge_scene(raw_wav, base_rate_pct=brate, pitch_hz=phz)
        if ok:
            feats = measure_voice_features(raw_wav, ref_profile)
            dst = OUT_DIR / f"02_{pname}.wav"
            apply_conbo_dsp(raw_wav, dst, pitch_semitones=dsp_st)
            rec = {
                "engine": "Edge-TTS",
                "voice": pname,
                "note": pnote,
                "raw_path": str(raw_wav),
                "cover_file": dst.name,
                **feats,
            }
            results.append(rec)
            print(
                f"  [EDGE] {pname:26s} | F0={feats['f0_median_hz']:5.1f}Hz ({feats['f0_diff_semitones']:+5.2f}st) | "
                f"IQR={feats['f0_iqr_semitones']:4.2f}st | MFCC={feats['mfcc_cosine']:.3f} | Score={feats['similarity_score']:5.2f}"
            )

    print("\n=== BƯỚC 3: TẠO BẢN COVER PRO (PITCH-MATCHED + EQ CON BÒ) CHO TOP 3 GIỌNG CIT ===")
    cit_sorted = sorted(
        [r for r in results if r["engine"] == "CIT-VieNeu"],
        key=lambda x: x["similarity_score"],
        reverse=True,
    )
    top3 = cit_sorted[:3]
    pro_covers = []
    for rank, item in enumerate(top3, start=1):
        raw_wav = Path(item["raw_path"])
        # Tính lượng dịch pitch tối ưu về gần 159 Hz (giới hạn trong [-2.0, +2.0] semitones để giữ tự nhiên, không robot)
        needed_st = -float(item["f0_diff_semitones"])
        clamped_st = max(-2.0, min(2.0, needed_st * 0.7))
        safe = Path(item["cover_file"]).stem.split("_", 3)[-1]
        pro_dst = OUT_DIR / f"00_TOP{rank}_COVER_PRO_{safe}.wav"
        apply_conbo_dsp(raw_wav, pro_dst, pitch_semitones=clamped_st)
        pro_feats = measure_voice_features(pro_dst, ref_profile)
        pro_rec = {
            "rank": rank,
            "voice": item["voice"],
            "pitch_shift_st": round(clamped_st, 2),
            "cover_file": pro_dst.name,
            **pro_feats,
        }
        pro_covers.append(pro_rec)
        print(
            f"  [TOP {rank}] {pro_dst.name:36s} (shift {clamped_st:+.2f}st) -> "
            f"F0={pro_feats['f0_median_hz']:5.1f}Hz | Warmth={pro_feats['warmth_200_500_pct']}% | "
            f"MFCC={pro_feats['mfcc_cosine']:.3f} | Score={pro_feats['similarity_score']:5.2f}"
        )

    # Xuất thêm đúng đoạn cắt tương ứng từ Video_mẫu.mp4 (24.8s -> 46.8s) để người dùng bật A/B so trực tiếp!
    ref_ab = OUT_DIR / "00_GOC_Video_mau_AB_25s_47s.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            "24.8",
            "-to",
            "46.8",
            "-i",
            str(BASE / "voice_analysis" / "video_mau_48k.wav"),
            "-ar",
            "44100",
            "-ac",
            "2",
            str(ref_ab),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    # Dọn file raw tạm
    shutil.rmtree(RAW_DIR, ignore_errors=True)

    summary = {
        "reference": {
            "file": ref_ab.name,
            "f0_median_hz": ref_f0,
            "f0_iqr_semitones": ref_profile["f0_hz"]["iqr_semitones"],
            "syl_per_sec_median": ref_profile["rhythm"]["syl_per_sec_median"],
            "warmth_200_500_pct": ref_profile["spectral"]["band_energy_pct"]["warmth_200_500"],
        },
        "top_pro_covers": pro_covers,
        "all_candidates_ranked": sorted(results, key=lambda x: x["similarity_score"], reverse=True),
    }
    report_path = OUT_DIR / "cover_comparison_report.json"
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nHOÀN TẤT! Báo cáo lưu tại: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

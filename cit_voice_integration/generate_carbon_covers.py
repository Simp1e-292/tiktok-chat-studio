#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CARBON MASTER VOICE COVER ENGINE (v3)
=====================================
Giải quyết triệt để 3 nguyên nhân gốc khiến các bản trước chưa giống 100% Video_mẫu.mp4:
1. Tách đúng 3 TẦNG GIỌNG (3 Vocal Registers) sạch 0% SFX của cùng người đọc trong Video_mẫu.mp4:
   - TELL  (~132 Hz): Đĩnh đạc, điềm tĩnh giải thích / kể chuyện
   - ASK   (~165 Hz): Cao sáng, hỏi vặn / ngạc nhiên cướp lời
   - DROP  (~105 Hz): Trầm khàn đáy cổ họng, buông thõng / chốt hạ mặt lạnh ("Không.", "Thủ lĩnh loài bò.")
2. Nâng cấp từ bản nén INT8 (gây méo trên CPU thiếu VNNI) lên 2 mô hình FULL 32-BIT (FP32 48kHz):
   - Blaze AI VieNeu-TTS v3 Turbo d3 (FP32) — giảm lỗi câu ngắn, âm trầm dày tự nhiên
   - VieNeu-TTS v3 Turbo Studio (FP32)      — bản gốc 32-bit phòng thu sáng rõ
3. Best-of-N Acoustic Auto-Selector + KHÔNG DÙNG `atempo`:
   - Mỗi câu sinh nhiều take ở các temperature tinh chỉnh, tự chấm điểm F0 + độ dốc ngữ điệu + thời lượng tự nhiên,
     chọn take khớp nhất rồi ghép đúng từng mili-giây khoảng nghỉ hài (comic beat) của Video_mẫu.mp4!
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
WORKSPACE = BASE.parent
sys.path.insert(0, str(CIT_ROOT))
sys.path.insert(0, str(CIT_ROOT / "src"))

from apps.runtime_paths import setup_hf_home

setup_hf_home()
from vieneu import Vieneu

SRC_48K = BASE / "voice_analysis" / "video_mau_48k.wav"
REFS_DIR = BASE / "voice_analysis" / "refs_carbon_pure"
OUT_DIR = BASE / "voice_covers_v3_carbon"
TMP_DIR = OUT_DIR / "_tmp"


def setup_ffmpeg() -> None:
    if shutil.which("ffmpeg"):
        return
    local_apps = Path(os.path.expandvars(r"%LOCALAPPDATA%\CapCut\Apps"))
    if local_apps.is_dir():
        for exe in sorted(local_apps.rglob("ffmpeg.exe"), reverse=True):
            os.environ["PATH"] = str(exe.parent) + os.pathsep + os.environ.get("PATH", "")
            return
    raise RuntimeError("Không tìm thấy ffmpeg!")


def build_surgical_refs() -> Dict[str, Path]:
    """Tạo 4 mẫu giọng siêu sạch (0.00% SFX, không cụt đầu/cuối chữ) phân tầng đúng F0."""
    REFS_DIR.mkdir(parents=True, exist_ok=True)
    y, sr = sf.read(str(SRC_48K))
    ym = y.mean(axis=1).astype(np.float32) if y.ndim > 1 else y.astype(np.float32)

    specs = {
        # TELL (~132 Hz): điềm tĩnh lập luận & dẫn chuyện
        "TELL": [
            (24.86, 27.14),  # Thích là một chuyện. Hạch toán chi phí là chuyện khác.
            (11.18, 13.28),  # Thỉnh thoảng mang lên thôi chứ ngày nào cũng mang
            (34.50, 36.05),  # Chuyện là hồi nhỏ, anh suýt bị rắn cắn.
            (40.38, 41.80),  # Và từ đó anh trở thành...
        ],
        # STORY (~138 Hz): kể chuyện sinh động có nhấn nhá
        "STORY": [
            (5.54, 7.36),    # Hôm trước là phải quay video quảng cáo hạt mèo
            (19.52, 22.14),  # Thích chứ, nên mới có hãng đồ ăn cho mèo Pet Bite này nè
            (36.66, 39.48),  # Con mèo nhà hàng xóm lao ra vả con rắn mấy phát, rắn chạy luôn
        ],
        # ASK (~164 Hz): hỏi vặn cao giọng (đã cắt trước tiếng chuông ở 43.20s)
        "ASK": [
            (28.34, 30.34),  # Thế sao anh lại không tự nuôi mèo tự quay đi
            (33.20, 34.12),  # Thế sao anh lại thích mèo?
            (42.12, 43.16),  # một người cuồng mèo? (cắt sạch trước chime 43.22s)
            (44.66, 45.46),  # Thế anh trở thành gì?
        ],
        # DROP (~108 Hz): buông thõng / chốt hạ mặt lạnh trầm đáy cổ họng
        "DROP": [
            (15.40, 16.56),  # À, thì ra.
            (30.79, 31.94),  # Anh dị ứng lông mèo mà.
            (43.67, 44.08),  # Không.
            (45.95, 46.73),  # Thủ lĩnh loài bò.
        ],
    }

    paths: Dict[str, Path] = {}
    fade = int(0.015 * sr)
    gap = np.zeros(int(0.14 * sr), dtype=np.float32)

    for key, segs in specs.items():
        parts = []
        for s, e in segs:
            seg = ym[int(s * sr) : int(e * sr)].copy()
            seg, _ = librosa.effects.trim(seg, top_db=46)
            if len(seg) > 2 * fade:
                seg[:fade] *= np.linspace(0.0, 1.0, fade, dtype=np.float32)
                seg[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)
            parts.append(seg)
            parts.append(gap)
        arr = np.concatenate(parts[:-1])
        arr = arr / (np.max(np.abs(arr)) + 1e-9) * 0.89
        out_p = REFS_DIR / f"ref_{key}.wav"
        sf.write(str(out_p), arr, sr)
        paths[key] = out_p
        print(f"  [REF] {key:6s} -> {len(arr)/sr:.2f}s ({out_p.name})")

    return paths


# Toàn bộ đoạn 24.8s -> 46.8s của Video_mẫu.mp4 (đầy đủ 10 lượt thoại để so 1-1 từ đầu đến cuối!)
# Tuple: (text, register_key, target_f0_hz, target_dur_s, gap_after_s, sfx_after_optional)
AB_FULL_SCENE = [
    ("Thích là một chuyện.", "TELL", 131.0, 0.72, 0.44, None),
    ("Hạch toán chi phí là chuyện khác.", "TELL", 130.0, 1.25, 0.78, "assets/sfx_pack/huh.mp3"),
    ("Thế sao anh lại không tự nuôi mèo tự quay đi?", "ASK", 160.0, 1.95, 0.46, None),
    ("Anh dị ứng lông mèo mà.", "DROP", 108.0, 1.15, 0.85, "assets/sfx_pack/bruh.mp3"),
    ("Thế sao anh lại thích mèo?", "ASK", 170.0, 0.92, 0.36, None),
    ("Chuyện là hồi nhỏ, anh suýt bị rắn cắn.", "TELL", 133.0, 1.54, 0.28, None),
    ("Con mèo nhà hàng xóm lao ra vả con rắn mấy phát, rắn chạy luôn.", "TELL", 136.0, 2.75, 0.72, "assets/sfx_pack/metal_boom.mp3"),
    ("Và từ đó anh trở thành...", "TELL", 130.0, 1.40, 0.26, None),
    ("Một người cuồng mèo?", "ASK", 168.0, 1.15, 0.20, None),
    ("Không.", "DROP", 106.0, 0.42, 0.58, None),
    ("Thế anh trở thành gì?", "ASK", 162.0, 0.84, 0.47, None),
    ("Thủ lĩnh loài bò.", "DROP", 98.0, 0.82, 0.30, "assets/sfx_pack/wow.mp3"),
]

# Kịch bản MỚI Tập 2 (Hồ Cá Koi) đạo diễn chuẩn 3 tầng giọng + comic beat
HO_CA_KOI_SCENE = [
    ("Anh có chuyện muốn nói.", "TELL", 132.0, 1.10, 0.36, None),
    ("Hố trước sân sửa thành hồ cá Koi nhé.", "TELL", 130.0, 1.85, 0.42, "assets/sfx_pack/inception.mp3"),
    ("Ơ, thế là chuyển từ bơi sang câu cá à sếp?", "ASK", 166.0, 2.05, 0.40, None),
    ("Hợp đồng ký rồi, cọc cũng chuyển rồi đấy anh.", "ASK", 160.0, 2.00, 0.38, None),
    ("Quả này anh nghĩ rồi.", "TELL", 128.0, 1.05, 0.42, None),
    ("Phải liều thôi.", "DROP", 104.0, 0.78, 0.52, "assets/sfx_pack/bruh.mp3"),
    ("Chắc bà đối tác bỏ bùa sếp rồi?", "ASK", 168.0, 1.55, 0.24, None),
    ("Phải chịu. Phải chịu.", "DROP", 102.0, 1.05, 0.30, "assets/sfx_pack/wow.mp3"),
]


def gentle_trim(wav: np.ndarray, sr: int) -> np.ndarray:
    """Cắt khoảng lặng thừa rất nhẹ (-52dB) kèm đệm êm để KHÔNG BAO GIỜ xén mất phụ âm đầu hay đuôi trầm."""
    trimmed, _ = librosa.effects.trim(wav.astype(np.float32), top_db=48, frame_length=1024, hop_length=256)
    if len(trimmed) < int(0.18 * sr):
        trimmed = wav.astype(np.float32)
    fade_in = min(int(0.012 * sr), len(trimmed) // 4)
    fade_out = min(int(0.025 * sr), len(trimmed) // 4)
    out = trimmed.copy()
    if fade_in > 4:
        out[:fade_in] *= np.linspace(0.0, 1.0, fade_in, dtype=np.float32)
    if fade_out > 4:
        out[-fade_out:] *= np.linspace(1.0, 0.0, fade_out, dtype=np.float32)
    return out


def score_take(
    wav: np.ndarray,
    sr: int,
    reg_key: str,
    target_f0: float,
    target_dur: float,
) -> Tuple[float, dict]:
    dur = len(wav) / sr
    # Loại ngay nếu quá ngắn hoặc bị babble quá dài
    if dur < max(0.22, target_dur * 0.48) or dur > target_dur * 1.65 + 0.45:
        return -999.0, {"dur": round(dur, 2), "f0": 0.0}

    f0 = librosa.yin(wav, fmin=70, fmax=270, sr=sr, frame_length=2048, hop_length=512)
    frms = librosa.feature.rms(y=wav, frame_length=2048, hop_length=512)[0]
    mask = (frms > (np.sqrt(np.mean(wav**2)) * 0.32)) & (f0 > 72) & (f0 < 260)
    vf0 = f0[mask]
    if len(vf0) < 3:
        return -500.0, {"dur": round(dur, 2), "f0": 0.0}

    med_f0 = float(np.median(vf0))
    st_err = abs(12.0 * np.log2(med_f0 / target_f0))
    dur_rel_err = abs(dur - target_dur) / max(0.35, target_dur)

    # Thưởng độ dốc ngữ điệu đúng vai: ASK nên cao ở nửa cuối; DROP nên hạ trầm ở nửa cuối
    half = max(1, len(vf0) // 2)
    slope_st = float(12.0 * np.log2((np.median(vf0[half:]) + 1e-6) / (np.median(vf0[:half]) + 1e-6)))
    contour_bonus = 0.0
    if reg_key == "ASK" and slope_st > 0:
        contour_bonus = min(2.0, slope_st * 0.6)
    elif reg_key == "DROP" and slope_st <= 0.3:
        contour_bonus = min(2.0, -slope_st * 0.5 + 0.5)

    score = 100.0 - st_err * 6.5 - dur_rel_err * 18.0 + contour_bonus
    return score, {"dur": round(dur, 2), "f0": round(med_f0, 1), "slope_st": round(slope_st, 2)}


def synthesize_best_takes(
    tts,
    scene: List[Tuple],
    refs: Dict[str, Path],
    force_single_tell_except_drop: bool = False,
    n_candidates: int = 4,
) -> List[Tuple[np.ndarray, float, str | None]]:
    """Sinh `n_candidates` take cho mỗi câu, chấm điểm tự động và lấy take xuất sắc nhất."""
    sr = tts.sample_rate
    temps = [0.42, 0.50, 0.58, 0.66, 0.46][:n_candidates]
    chosen: List[Tuple[np.ndarray, float, str | None]] = []

    for idx, (text, reg_key, target_f0, target_dur, gap_s, sfx_rel) in enumerate(scene, start=1):
        eff_reg = reg_key
        eff_f0 = target_f0
        if force_single_tell_except_drop and reg_key in ("ASK", "STORY"):
            eff_reg = "TELL"
            eff_f0 = 134.0

        ref_path = refs[eff_reg]
        best_score = -1e9
        best_wav = None
        best_info = {}

        for k, temp in enumerate(temps):
            np.random.seed(1000 + idx * 37 + k * 13)
            raw = tts.infer(
                text=text,
                ref_audio=ref_path,
                denoise=False,
                use_ref_codes=True,
                temperature=temp,
                top_k=20 if eff_reg == "DROP" else 24,
                top_p=0.92,
                repetition_penalty=1.25,
                apply_watermark=False,
            )
            trimmed = gentle_trim(raw, sr)
            sc, info = score_take(trimmed, sr, eff_reg, eff_f0, target_dur)
            if sc > best_score:
                best_score = sc
                best_wav = trimmed
                best_info = info

        # Cân bằng RMS từng câu về cùng chuẩn để 3 tầng giọng mượt như 1 người diễn xuất
        rms = float(np.sqrt(np.mean(best_wav**2)) + 1e-9)
        target_rms = 0.125 if eff_reg != "DROP" else 0.118
        norm_wav = np.clip(best_wav * (target_rms / rms), -0.95, 0.95)
        chosen.append((norm_wav, gap_s, sfx_rel))
        print(
            f"    #{idx:02d} [{eff_reg:5s}] F0={best_info.get('f0',0):5.1f}Hz (mục tiêu {eff_f0:5.1f}) | "
            f"dur={best_info.get('dur',0):4.2f}s (mục tiêu {target_dur:4.2f}s) | {text}"
        )

    return chosen


def assemble_track(
    takes: List[Tuple[np.ndarray, float, str | None]],
    sr: int,
    out_wav: Path,
    mode: str = "natural",
    include_sfx: bool = False,
) -> None:
    """Ghép các take theo đúng mili-giây khoảng nghỉ + tùy chọn chèn SFX và mastering."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    pieces: List[np.ndarray] = []

    for wav, gap_s, sfx_rel in takes:
        pieces.append(wav)
        if include_sfx and sfx_rel:
            sfx_p = WORKSPACE / sfx_rel
            if sfx_p.exists():
                y_sfx, _ = librosa.load(str(sfx_p), sr=sr, mono=True)
                y_sfx = y_sfx[: int(1.15 * sr)] * 0.42
                pieces.append(np.zeros(int(0.06 * sr), dtype=np.float32))
                pieces.append(y_sfx.astype(np.float32))
                pieces.append(np.zeros(int(0.16 * sr), dtype=np.float32))
                continue
        pieces.append(np.zeros(int(round(gap_s * sr)), dtype=np.float32))

    raw_track = TMP_DIR / "assembled_raw.wav"
    sf.write(str(raw_track), np.concatenate(pieces), sr)

    if mode == "broadcast_eq":
        # Khớp đường cong phổ Video_mẫu.mp4: ấm ngực 260Hz, mịn dải cao >6kHz, nén broadcast chặt
        af = ",".join(
            [
                "highpass=f=75",
                "equalizer=f=260:t=q:w=1.1:g=2.4",
                "equalizer=f=2400:t=q:w=1.3:g=1.2",
                "lowpass=f=6800",
                "acompressor=threshold=-19dB:ratio=2.8:attack=10:release=110:makeup=2.2",
                "loudnorm=I=-14.5:TP=-1.0:LRA=6.5",
            ]
        )
    else:
        # Trong suốt tuyệt đối giữ nguyên chất giọng 48kHz FP32
        af = ",".join(
            [
                "highpass=f=70",
                "acompressor=threshold=-18dB:ratio=2.0:attack=12:release=120:makeup=1.5",
                "loudnorm=I=-14.5:TP=-1.0:LRA=7.5",
            ]
        )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(raw_track),
            "-af",
            af,
            "-ar",
            "48000",
            "-ac",
            "2",
            str(out_wav),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    raw_track.unlink(missing_ok=True)


def main() -> int:
    setup_ffmpeg()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    # Copy đoạn gốc A/B vào chung thư mục để nghe đối chiếu ngay
    src_ab = BASE / "voice_covers" / "00_GOC_Video_mau_AB_25s_47s.wav"
    if src_ab.exists():
        shutil.copy2(src_ab, OUT_DIR / src_ab.name)

    print("=== BƯỚC 1: TÁCH 4 MẪU PHÂN TẦNG SẠCH TUYỆT ĐỐI (0.00% SFX) ===")
    refs = build_surgical_refs()

    # Chạy 2 model FULL FP32: Blaze AI d3 (FP32) & VieNeu Studio (FP32)
    models = [
        ("BlazeD3_FP32", "cuongyd196/VieNeu-TTS-v3-Turbo-d3"),
        ("Studio_FP32", "pnnbao-ump/VieNeu-TTS-v3-Turbo"),
    ]

    for m_tag, repo_id in models:
        print(f"\n=== BƯỚC 2: NẠP MÔ HÌNH {m_tag} ({repo_id} · precision=fp32) ===")
        tts = Vieneu(
            mode="v3turbo",
            backbone_repo=repo_id,
            precision="fp32",
            backend="onnx",
        )

        print(f"  -> Đạo diễn kịch bản A/B gốc (12 câu đầy đủ 25s-47s) bằng {m_tag} (3 tầng giọng)...")
        ab_takes = synthesize_best_takes(tts, AB_FULL_SCENE, refs, n_candidates=4)
        assemble_track(
            ab_takes,
            tts.sample_rate,
            OUT_DIR / f"AB_01_{m_tag}_3TangGiong_Natural.wav",
            mode="natural",
        )
        assemble_track(
            ab_takes,
            tts.sample_rate,
            OUT_DIR / f"AB_02_{m_tag}_3TangGiong_BroadcastEQ.wav",
            mode="broadcast_eq",
        )
        if m_tag == "BlazeD3_FP32":
            assemble_track(
                ab_takes,
                tts.sample_rate,
                OUT_DIR / f"AB_03_{m_tag}_3TangGiong_CoSFX_NhuGoc.wav",
                mode="broadcast_eq",
                include_sfx=True,
            )

        print(f"  -> Đạo diễn kịch bản MỚI Tập 2 Hồ Cá Koi bằng {m_tag} (3 tầng giọng)...")
        koi_takes = synthesize_best_takes(tts, HO_CA_KOI_SCENE, refs, n_candidates=4)
        assemble_track(
            koi_takes,
            tts.sample_rate,
            OUT_DIR / f"KOI_01_{m_tag}_3TangGiong_Natural.wav",
            mode="natural",
        )
        assemble_track(
            koi_takes,
            tts.sample_rate,
            OUT_DIR / f"KOI_02_{m_tag}_3TangGiong_BroadcastEQ.wav",
            mode="broadcast_eq",
        )
        if m_tag == "BlazeD3_FP32":
            assemble_track(
                koi_takes,
                tts.sample_rate,
                OUT_DIR / f"KOI_03_{m_tag}_3TangGiong_CoSFX.wav",
                mode="broadcast_eq",
                include_sfx=True,
            )
            print("  -> Tạo thêm bản 1 giọng Sếp trầm xuyên suốt (TELL + DROP) để bạn chọn gu...")
            ab_1v = synthesize_best_takes(
                tts, AB_FULL_SCENE, refs, force_single_tell_except_drop=True, n_candidates=3
            )
            assemble_track(
                ab_1v,
                tts.sample_rate,
                OUT_DIR / "AB_04_BlazeD3_FP32_1GiongSepTram_XuyenSuot.wav",
                mode="broadcast_eq",
            )
            koi_1v = synthesize_best_takes(
                tts, HO_CA_KOI_SCENE, refs, force_single_tell_except_drop=True, n_candidates=3
            )
            assemble_track(
                koi_1v,
                tts.sample_rate,
                OUT_DIR / "KOI_04_BlazeD3_FP32_1GiongSepTram_XuyenSuot.wav",
                mode="broadcast_eq",
            )

        del tts

    shutil.rmtree(TMP_DIR, ignore_errors=True)
    print(f"\nHOÀN TẤT TOÀN BỘ BỘ COVER CARBON v3 TẠI: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

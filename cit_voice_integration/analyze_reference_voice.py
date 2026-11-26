#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phân tích sâu âm thanh giọng nói & nhịp độ tiết tấu của Video_mẫu.mp4:
- Tách đoạn thoại (VAD / energy + harmonic pitch)
- Đo F0 (cao độ nền: median, mean, std, IQR, min/max)
- Đo tốc độ nói (âm tiết / giây) và độ dài khoảng nghỉ giữa các câu / cụm
- Đo phân bổ dải tần (6-band EQ profile), spectral centroid, dynamic range, MFCC
"""

from __future__ import annotations

import json
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

BASE = Path(__file__).resolve().parent
WAV_PATH = BASE / "voice_analysis" / "video_mau_mono24k.wav"

# Các câu thoại nghe được trong Video_mẫu.mp4 kèm số âm tiết ước tính & mốc gần đúng (giây)
# (những đoạn sạch giọng, tách khỏi SFX nổ/cười)
UTTERANCES = [
    (0.0, 1.8, 7, "Hôm sau để nhà nhé các em"),
    (2.1, 4.4, 13, "Sao vậy anh? Hôm trước anh bảo được mang lên thoải mái mà"),
    (5.3, 8.2, 16, "Hôm trước là phải quay video quảng cáo hạt mèo nên anh mới bảo thế"),
    (8.6, 10.6, 11, "Quay xong rồi thì để mấy bé ở nhà nhé"),
    (11.1, 14.3, 14, "Thỉnh thoảng mang lên thôi chứ ngày nào cũng mang... tốn hạt lắm"),
    (15.2, 18.6, 11, "À, thì ra. Trước anh bảo anh thích mèo cơ mà"),
    (19.5, 22.4, 14, "Thích chứ, nên mới có hãng đồ ăn cho mèo Pet Bite này nè"),
    (22.9, 24.4, 6, "Thế sao đuổi tụi nó về?"),
    (24.9, 27.5, 12, "Thích là một chuyện. Hạch toán chi phí là chuyện khác"),
    (28.2, 30.7, 11, "Thế sao anh lại không tự nuôi mèo tự quay đi"),
    (30.9, 32.3, 6, "Anh dị ứng lông mèo mà"),
    (33.3, 34.5, 6, "Thế sao anh lại thích mèo?"),
    (34.7, 36.4, 9, "Chuyện là hồi nhỏ, anh suýt bị rắn cắn"),
    (36.7, 39.6, 15, "Con mèo nhà hàng xóm lao ra vả con rắn mấy phát, rắn chạy luôn"),
    (40.4, 43.3, 11, "Và từ đó anh trở thành... một người cuồng mèo?"),
    (43.7, 46.7, 11, "Không. Thế anh trở thành gì? Thủ lĩnh loài bò"),
]


def analyze_audio(wav_path: Path) -> dict:
    y, sr = sf.read(str(wav_path))
    if y.ndim > 1:
        y = y.mean(axis=1)
    y = y.astype(np.float32)
    total_dur = len(y) / sr

    # Tách các vùng có âm thanh (không phải im lặng)
    intervals = librosa.effects.split(y, top_db=32, frame_length=1024, hop_length=256)
    seg_info = []
    for s, e in intervals:
        t0, t1 = s / sr, e / sr
        if t1 - t0 >= 0.08:
            seg_info.append((round(t0, 3), round(t1, 3), round(t1 - t0, 3)))

    # Đo F0 bằng pYIN trên toàn file (giới hạn dải giọng nam 65 - 260 Hz)
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y, fmin=65.0, fmax=260.0, sr=sr, frame_length=2048, hop_length=256
    )

    # Chỉ lấy khung giọng nói rõ (voiced_prob > 0.65) trong các cửa sổ thoại
    times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=256)
    voice_mask = np.zeros_like(voiced_flag, dtype=bool)
    speech_samples = []
    utt_stats = []

    for u_start, u_end, syl_count, text in UTTERANCES:
        i0, i1 = int(u_start * sr), min(len(y), int(u_end * sr))
        seg = y[i0:i1]
        # Trim im lặng đầu cuối từng câu để đo tốc độ nói thực tế
        trimmed, idx = librosa.effects.trim(seg, top_db=30)
        act_start = u_start + idx[0] / sr
        act_end = u_start + idx[1] / sr
        act_dur = max(0.05, act_end - act_start)
        syl_rate = syl_count / act_dur

        fmask = (times >= act_start) & (times <= act_end) & voiced_flag & (voiced_prob > 0.65)
        voice_mask |= fmask
        uf0 = f0[fmask]
        uf0 = uf0[~np.isnan(uf0)]

        # Đếm khoảng nghỉ bên trong câu (>80ms)
        sub_ints = librosa.effects.split(trimmed, top_db=30, frame_length=512, hop_length=128)
        internal_gaps = []
        for k in range(len(sub_ints) - 1):
            gap = (sub_ints[k + 1][0] - sub_ints[k][1]) / sr
            if gap >= 0.06:
                internal_gaps.append(round(gap, 3))

        speech_samples.append(trimmed)
        utt_stats.append(
            {
                "window": [round(act_start, 2), round(act_end, 2)],
                "dur_s": round(act_dur, 2),
                "syllables": syl_count,
                "syl_per_sec": round(syl_rate, 2),
                "f0_median_hz": round(float(np.median(uf0)), 1) if len(uf0) else None,
                "f0_iqr_hz": round(float(np.percentile(uf0, 75) - np.percentile(uf0, 25)), 1) if len(uf0) else None,
                "internal_gaps_s": internal_gaps,
                "text": text,
            }
        )

    all_f0 = f0[voice_mask]
    all_f0 = all_f0[~np.isnan(all_f0)]
    y_speech = np.concatenate(speech_samples)

    # Phân bổ năng lượng 6 dải tần (dB tương đối)
    S = np.abs(librosa.stft(y_speech, n_fft=2048, hop_length=512)) ** 2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    psd = S.mean(axis=1)
    total_e = psd.sum() + 1e-12
    bands = [
        ("sub_chest_80_200", 80, 200),
        ("warmth_200_500", 200, 500),
        ("mid_500_1200", 500, 1200),
        ("presence_1200_3500", 1200, 3500),
        ("sibilance_3500_7000", 3500, 7000),
        ("air_7000_11000", 7000, 11000),
    ]
    band_pct = {}
    band_db = {}
    for name, f_lo, f_hi in bands:
        m = (freqs >= f_lo) & (freqs < f_hi)
        e = float(psd[m].sum())
        band_pct[name] = round(100.0 * e / total_e, 2)
        band_db[name] = round(10.0 * np.log10(e / total_e + 1e-12), 2)

    centroid = float(np.median(librosa.feature.spectral_centroid(y=y_speech, sr=sr)))
    rolloff = float(np.median(librosa.feature.spectral_rolloff(y=y_speech, sr=sr, roll_percent=0.85)))
    mfcc = librosa.feature.mfcc(y=y_speech, sr=sr, n_mfcc=13).mean(axis=1)
    rms = librosa.feature.rms(y=y_speech)[0]
    rms_db = 20.0 * np.log10(rms + 1e-9)
    dyn_range_db = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 20))

    # Đo khoảng nghỉ giữa các câu liên tiếp
    inter_gaps = []
    for k in range(len(utt_stats) - 1):
        g = utt_stats[k + 1]["window"][0] - utt_stats[k]["window"][1]
        inter_gaps.append(round(g, 2))

    syl_rates = [u["syl_per_sec"] for u in utt_stats]

    result = {
        "duration_s": round(total_dur, 2),
        "sample_rate": sr,
        "f0_hz": {
            "median": round(float(np.median(all_f0)), 1),
            "mean": round(float(np.mean(all_f0)), 1),
            "std": round(float(np.std(all_f0)), 1),
            "p10": round(float(np.percentile(all_f0, 10)), 1),
            "p25": round(float(np.percentile(all_f0, 25)), 1),
            "p75": round(float(np.percentile(all_f0, 75)), 1),
            "p90": round(float(np.percentile(all_f0, 90)), 1),
            "iqr": round(float(np.percentile(all_f0, 75) - np.percentile(all_f0, 25)), 1),
            "iqr_semitones": round(
                float(12.0 * np.log2(np.percentile(all_f0, 75) / np.percentile(all_f0, 25))), 2
            ),
        },
        "rhythm": {
            "syl_per_sec_median": round(float(np.median(syl_rates)), 2),
            "syl_per_sec_mean": round(float(np.mean(syl_rates)), 2),
            "syl_per_sec_range": [round(min(syl_rates), 2), round(max(syl_rates), 2)],
            "inter_utterance_gaps_s": inter_gaps,
            "inter_gap_median_s": round(float(np.median(inter_gaps)), 2),
        },
        "spectral": {
            "centroid_hz": round(centroid, 1),
            "rolloff85_hz": round(rolloff, 1),
            "dynamic_range_db": round(dyn_range_db, 1),
            "band_energy_pct": band_pct,
            "band_energy_db": band_db,
            "mfcc_mean": [round(float(x), 3) for x in mfcc],
        },
        "utterances": utt_stats,
    }
    return result


if __name__ == "__main__":
    res = analyze_audio(WAV_PATH)
    out_json = BASE / "voice_analysis" / "video_mau_profile.json"
    out_json.write_text(json.dumps(res, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2, default=float))

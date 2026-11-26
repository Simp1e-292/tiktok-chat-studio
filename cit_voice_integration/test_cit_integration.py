#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script kiểm thử toàn diện tích hợp CIT Voice Studio (API + Adapter Pipeline).
Chạy sau khi server CIT Voice Studio đã bật ở http://127.0.0.1:8001.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from audio_engine_cit import synthesize_dual_gender_cit
from cit_voice_client import CitVoiceClient

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "test_output"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = CitVoiceClient("http://127.0.0.1:8001")

    print("=== 1. KIỂM TRA SERVER (/health & /voices) ===")
    health = client.wait_ready(timeout_sec=120.0)
    print(json.dumps(health, ensure_ascii=False, indent=2))

    voices = client.list_voices()
    voice_names = [v.get("id") for v in voices]
    print(f"Tổng số giọng sẵn có: {len(voice_names)}")
    print("Giọng mẫu:", ", ".join(voice_names[:10]))

    male_voice = "Adam bựa" if "Adam bựa" in voice_names else voice_names[0]
    female_voice = "Trúc Ly" if "Trúc Ly" in voice_names else voice_names[0]
    print(f"Giọng test chọn -> Nam: '{male_voice}' | Nữ: '{female_voice}'\n")

    print("=== 2. TEST CÂU NGẮN + THẺ CẢM XÚC + THẺ NGHỈ ===")
    short_cases = [
        ("short_01_ua.wav", "Ủa? Thật á sếp?", male_voice),
        ("short_02_chot.wav", "Chốt đơn!", female_voice),
        (
            "short_03_emotion.wav",
            "Chụp màn hình rồi nha anh. [cười] Chậm đơn khách chửi thì anh tự nghe máy. [nghỉ 0.5s] Nhớ nhé!",
            female_voice,
        ),
    ]
    for fname, text, vid in short_cases:
        meta = client.generate_to_file(
            text=text,
            out_path=OUT_DIR / "single_tests" / fname,
            voice_id=vid,
            speed=1.08,
            temperature=0.65,
        )
        print(
            f"  [OK] {fname}: dur={meta['duration_seconds']}s, "
            f"gen={meta['elapsed_seconds']}s, RTF={meta['rtf']}, "
            f"sr={meta['sample_rate']}Hz, size={meta['bytes']:,}B"
        )

    print("\n=== 3. TEST ADAPTER PIPELINE DUAL-GENDER (TRÍCH TẬP 2 HỒ CÁ KOI) ===")
    sample_items = [
        {
            "idx": 1,
            "kind": "msg",
            "code": "TRANG",
            "gender": "female",
            "tts": "Một con Porsche đỗ ngay trước cửa. Quả này thật hết nước chấm!",
        },
        {
            "idx": 5,
            "kind": "msg",
            "code": "SEP",
            "gender": "male",
            "tts": "Anh có chuyện muốn nói. Hố trước sân sửa thành hồ cá Koi nhé.",
        },
        {
            "idx": 6,
            "kind": "msg",
            "code": "TUNG_EM",
            "gender": "male",
            "tts": "Ơ, thế là chuyển từ bơi sang câu cá à sếp?",
        },
        {
            "idx": 13,
            "kind": "msg",
            "code": "HAI",
            "gender": "female",
            "tts": "Chụp màn hình rồi nha anh. Chậm đơn khách chửi thì anh tự nghe máy.",
        },
    ]
    manifest_path = synthesize_dual_gender_cit(
        items=sample_items,
        out_dir=OUT_DIR / "dual_gender_ep2",
        male_voice=male_voice,
        female_voice=female_voice,
        male_speed=1.10,
        female_speed=1.08,
        temperature=0.65,
        reuse_cache=False,
    )
    print(f"  -> Đã xuất manifest: {manifest_path}")

    print("\n=== 4. TEST XUẤT AUDIO + PHỤ ĐỀ .SRT ===")
    srt_res = client.generate_with_subtitles(
        text="Đối tác đi Porsche ghé xưởng. Tối về sếp đòi sửa hố trạm cân thành hồ cá Koi. [cười] Công ty anh em có sếp thế này không?",
        voice_id=female_voice,
        speed=1.08,
    )
    srt_dir = OUT_DIR / "subtitles"
    srt_dir.mkdir(parents=True, exist_ok=True)
    (srt_dir / "ep2_intro.wav").write_bytes(srt_res["audio_bytes"])
    (srt_dir / "ep2_intro.srt").write_text(srt_res["srt"], encoding="utf-8")
    print(
        f"  [OK] ep2_intro.wav + .srt: dur={srt_res['duration_seconds']}s, "
        f"gen={srt_res['elapsed_seconds']}s, RTF={srt_res['rtf']}, cues={len(srt_res['cues'])}"
    )
    print("  Nội dung SRT:\n" + srt_res["srt"].strip())

    print("\n=== 5. TEST HỘI THOẠI ĐA NHÂN VẬT (/api/tts/conversation) ===")
    conv_bytes, conv_meta = client.conversation(
        turns=[
            {"speaker": "Sếp", "text": "Quả này anh nghĩ rồi. Phải liều thôi.", "voice_id": male_voice},
            {"speaker": "Trang", "text": "Chắc bà đối tác bỏ bùa sếp rồi!", "voice_id": female_voice},
        ],
        silence_duration=0.30,
        speed=1.08,
    )
    conv_path = OUT_DIR / "conversation_ep2.wav"
    conv_path.write_bytes(conv_bytes)
    print(
        f"  [OK] {conv_path.name}: dur={conv_meta['duration_seconds']}s, "
        f"gen={conv_meta['elapsed_seconds']}s, turns={conv_meta['turns_count']}, size={len(conv_bytes):,}B"
    )

    print("\nTẤT CẢ BÀI TEST TÍCH HỢP CIT VOICE STUDIO ĐÃ PASS!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

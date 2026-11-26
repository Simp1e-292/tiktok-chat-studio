#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render Tập 2: "HỒ CÁ KOI CỦA SẾP" — Văn Phòng Khủng Long (Chuẩn Con Bò Đi Làm + Carbon AB_07 Tempo-Locked)
- Speaking Tempo khóa chuẩn Video_mẫu.mp4 (TELL ~5.80 syl/s | ASK ~5.85 syl/s | DROP ~5.15 syl/s, Best-of-6 + Micro-Pace Clamp).
- Cut Tempo siết dồn dập chuẩn bản gốc (đối đáp nối liền 0.22-0.30s, cảnh ảnh/Meme SFX gọn 0.95-1.35s).
- Xuất MP4: video_tap_02_ho_ca_koi.mp4 (1080x1920, 30fps, AAC 192k, -12.8 LUFS)
"""

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "cit_voice_integration"))
from carbon_voice_pipeline import (
    mix_carbon_ab07_audio,
    probe_duration,
    setup_ffmpeg,
    synthesize_carbon_voices,
)

WORKSPACE = Path(__file__).resolve().parent
VOICES_DIR = WORKSPACE / "carbon_ho_ca_koi_voices"
FRAMES_DIR = WORKSPACE / "ho_ca_koi_frames"
STAGE_HTML = WORKSPACE / "render_ho_ca_koi_stage.html"
OUTPUT_MP4 = WORKSPACE / "video_tap_02_ho_ca_koi.mp4"

ITEMS = [
    # --- MỞ MÀN: 3 CẢNH (1 câu đầu -> thêm câu dưới -> chỉ mỗi cái ảnh) ---
    {
        "idx": 1, "kind": "msg", "side": "left", "code": "TG", "gender": "female", "register": "TELL",
        "sender": "Trang (CSKH)", "color": "#db2777",
        "show_header": True, "stack_mode": "clear",
        "text": "Một con Porsche đỗ ngay trước cửa.",
        "tts": "Một con Pót-sơ đỗ ngay trước cửa.",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.06, "post_gap": 0.26,
    },
    {
        "idx": 2, "kind": "msg", "side": "left", "code": "TG", "gender": "female", "register": "TELL",
        "sender": "Trang (CSKH)", "color": "#db2777",
        "show_header": True, "stack_mode": "append_same",
        "text": "Quả này thật hết nước chấm!! 😍",
        "tts": "Quả này thật hết nước chấm!",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.06, "post_gap": 0.22,
    },
    {
        "idx": 3, "kind": "media_shot", "code": "TG",
        "sender": "Trang (CSKH)", "color": "#db2777",
        "show_header": False, "hide_sender": True,
        "img": "assets/ep_ho_ca_koi/doi_tac_nu_cua_xuong.jpg",
        "pop_sfx": "assets/sfx_pop.mp3",
        "after_sfx": "assets/sfx_pack/wow.mp3", "after_sfx_dur": 1.05, "after_sfx_vol": 0.62,
        "hold": 1.20,
    },

    # --- KIM BỒI THÊM THÔNG TIN + CẢNH GIF RIÊNG ---
    {
        "idx": 4, "kind": "msg", "side": "left", "code": "KM", "gender": "female", "register": "TELL",
        "sender": "Kim (Nhân sự)", "color": "#9333ea",
        "show_header": False, "stack_mode": "clear",
        "text": "Đối tác bên Long Biên, thấy bảo dự án Vin Cổ Loa",
        "tts": "Đối tác bên Long Biên, thấy bảo dự án Vinh Cổ Loa.",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.06, "post_gap": 0.24,
    },
    {
        "idx": 5, "kind": "media_shot", "code": "KM",
        "sender": "Kim (Nhân sự)", "color": "#9333ea",
        "show_header": False,
        "meme_gif": "assets/memes_ep2/leo_cheers.gif",
        "pop_sfx": "assets/sfx_pop.mp3",
        "after_sfx": "assets/sfx_pack/ding.mp3", "after_sfx_dur": 0.70, "after_sfx_vol": 0.45,
        "hold": 0.95,
    },

    # --- CHUYỂN CẢNH FULLSCREEN TWO HOURS LATER ---
    {
        "idx": 6, "kind": "sys_time",
        "card_title": "TWO HOURS LATER...",
        "after_sfx": "assets/ep_ho_ca_koi/two_hours_later_tight.wav",
        "after_sfx_dur": 1.57, "after_sfx_vol": 0.92,
        "music_drop": True,
        "hold": 1.72,
    },

    # --- SẾP CÔNG BỐ CÚ TWIST: BẬT TỪNG CÂU 1 ---
    {
        "idx": 7, "kind": "msg", "side": "left", "code": "SEP", "gender": "male", "register": "TELL",
        "sender": "Sếp", "color": "#1e3a8a",
        "show_header": True, "stack_mode": "clear",
        "text": "Anh có chuyện muốn nói.",
        "tts": "Anh có chuyện muốn nói.",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.06, "post_gap": 0.28,
    },
    {
        "idx": 8, "kind": "msg", "side": "left", "code": "SEP", "gender": "male", "register": "TELL",
        "sender": "Sếp", "color": "#1e3a8a",
        "show_header": True, "stack_mode": "append_same",
        "text": "Hố trước sân sửa thành HỒ CÁ KOI nhé.",
        "tts": "Hố trước sân sửa thành hồ cá coi nhé.",
        "pop_sfx": "assets/sfx_pop.mp3",
        "after_sfx": "assets/sfx_pack/inception.mp3", "after_sfx_dur": 1.25, "after_sfx_vol": 0.78,
        "music_drop": True,
        "typing": False, "voice_delay": 0.06, "post_gap": 1.35,
    },

    # --- TÙNG EM PHẢN ỨNG + CẢNH GIF RIÊNG ---
    {
        "idx": 9, "kind": "msg", "side": "left", "code": "TE", "gender": "male", "register": "ASK",
        "sender": "Tùng em (Thiết kế)", "color": "#16a34a",
        "show_header": False, "stack_mode": "clear",
        "text": "Ơ… thế là chuyển từ bơi sang câu cá à sếp?",
        "tts": "Ơ, thế là chuyển từ bơi sang câu cá à sếp?",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.06, "post_gap": 0.22,
    },
    {
        "idx": 10, "kind": "media_shot", "code": "TE",
        "sender": "Tùng em (Thiết kế)", "color": "#16a34a",
        "show_header": False,
        "meme_gif": "assets/memes_ep2/deadpool_wtf.gif",
        "after_sfx": "assets/ep_ho_ca_koi/wait_a_minute_tight.wav", "after_sfx_dur": 0.93, "after_sfx_vol": 0.86,
        "music_drop": True,
        "hold": 1.05,
    },

    # --- TÙNG ANH XẢ 2 CÂU CUỐN CHIẾU ---
    {
        "idx": 11, "kind": "msg", "side": "left", "code": "TA", "gender": "male", "register": "ASK",
        "sender": "Tùng anh (Xưởng)", "color": "#0d9488",
        "show_header": False, "stack_mode": "clear",
        "text": "Bỏ trạm cân thì xe Vendor vào cân kiểu gì anh?!",
        "tts": "Bỏ trạm cân thì xe ven đơ vào cân kiểu gì anh?",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.06, "post_gap": 0.26,
    },
    {
        "idx": 12, "kind": "msg", "side": "left", "code": "TA", "gender": "male", "register": "ASK",
        "sender": "Tùng anh (Xưởng)", "color": "#0d9488",
        "show_header": False, "stack_mode": "append_same",
        "text": "Hay lại quay lại cái máng lợn đầu KCN!",
        "tts": "Hay lại quay lại cái máng lợn đầu khu công nghiệp?",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.06, "post_gap": 0.30,
    },

    # --- THANH HẢI DẰN MẶT + SẾP ĐÁP TRẢ NỐI DƯỚI (TELL -> DROP CHỐT 3 CHỮ) + GIF BATMAN ---
    {
        "idx": 13, "kind": "msg", "side": "left", "code": "KT", "gender": "female", "register": "TELL",
        "sender": "Thanh Hải (Kế toán)", "color": "#ea580c",
        "show_header": True, "stack_mode": "clear",
        "text": "Hợp đồng ký rồi, cọc cũng chuyển rồi đấy anh",
        "tts": "Hợp đồng ký rồi, cọc cũng chuyển rồi đấy anh.",
        "pop_sfx": "assets/sfx_pop.mp3",
        "after_sfx": "assets/sfx_pack/ding.mp3", "after_sfx_dur": 0.80, "after_sfx_vol": 0.58,
        "typing": False, "voice_delay": 0.06, "post_gap": 0.92,
    },
    {
        "idx": 14, "kind": "msg", "side": "left", "code": "SEP", "gender": "male", "register": "TELL",
        "sender": "Sếp", "color": "#1e3a8a",
        "show_header": True, "stack_mode": "append_new",
        "text": "Quả này anh nghĩ rồi.",
        "tts": "Quả này anh nghĩ rồi.",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.06, "post_gap": 0.26,
    },
    {
        "idx": 15, "kind": "msg", "side": "left", "code": "SEP", "gender": "male", "register": "DROP",
        "sender": "Sếp", "color": "#1e3a8a",
        "show_header": True, "stack_mode": "append_same",
        "text": "Phải liều thôi",
        "tts": "Phải liều thôi.",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.06, "post_gap": 0.22,
    },
    {
        "idx": 16, "kind": "media_shot", "code": "SEP",
        "sender": "Sếp", "color": "#1e3a8a",
        "show_header": False,
        "meme_gif": "assets/memes_ep2/facepalm.gif",
        "after_sfx": "assets/sfx_pack/bruh.mp3", "after_sfx_dur": 0.84, "after_sfx_vol": 0.80,
        "hold": 0.95,
    },

    # --- TRANG CÀ KHỊA + CẢNH GIF LIẾC MẮT RIÊNG ---
    {
        "idx": 17, "kind": "msg", "side": "left", "code": "TG", "gender": "female", "register": "ASK",
        "sender": "Trang (CSKH)", "color": "#db2777",
        "show_header": False, "stack_mode": "clear",
        "text": "Chắc bà đối tác bỏ bùa Sếp rồi 😏",
        "tts": "Chắc bà đối tác bỏ bùa sếp rồi?",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.06, "post_gap": 0.22,
    },
    {
        "idx": 18, "kind": "media_shot", "code": "TG",
        "sender": "Trang (CSKH)", "color": "#db2777",
        "show_header": False,
        "meme_gif": "assets/memes_ep2/side_eye.gif",
        "after_sfx": "assets/sfx_pack/rimshot.mp3", "after_sfx_dur": 1.15, "after_sfx_vol": 0.72,
        "hold": 1.25,
    },

    # --- SẾP LỠ MỒM 2 CÂU (TELL -> DROP CHỐT 3 CHỮ) -> THU HỒI ---
    {
        "idx": 19, "kind": "msg", "side": "left", "code": "SEP", "gender": "male", "register": "TELL",
        "sender": "Sếp", "color": "#1e3a8a",
        "show_header": True, "stack_mode": "clear",
        "text": "Đối tác chiến lược toàn diện của anh đấy.",
        "tts": "Đối tác chiến lược toàn diện của anh đấy.",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.06, "post_gap": 0.26,
    },
    {
        "idx": 20, "kind": "msg", "side": "left", "code": "SEP", "gender": "male", "register": "DROP",
        "sender": "Sếp", "color": "#1e3a8a",
        "show_header": True, "stack_mode": "append_same",
        "text": "Phải chịu, phải chịu",
        "tts": "Phải chịu thôi.",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.06, "post_gap": 0.30,
    },
    {
        "idx": 21, "kind": "sys_recall",
        "show_header": True,
        "text": "Sếp đã thu hồi một tin nhắn",
        "after_sfx": "assets/sfx_pack/metal_boom.mp3", "after_sfx_dur": 1.00, "after_sfx_vol": 0.82,
        "music_drop": True,
        "hold": 1.10,
    },

    # --- KẾ TOÁN CHỤP MÀN HÌNH 2 CÂU CUỐN CHIẾU -> EMOTIONAL DAMAGE ---
    {
        "idx": 22, "kind": "msg", "side": "left", "code": "KT", "gender": "female", "register": "TELL",
        "sender": "Thanh Hải (Kế toán)", "color": "#ea580c",
        "show_header": True, "stack_mode": "clear",
        "text": "Chụp màn hình rồi nha anh 🙂",
        "tts": "Chụp màn hình rồi nha anh.",
        "screenshot_quote": {
            "sender": "Sếp",
            "time": "21:33",
            "text": "Đối tác chiến lược toàn diện của anh đấy. Phải chịu, phải chịu",
        },
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.06, "post_gap": 0.28,
    },
    {
        "idx": 23, "kind": "msg", "side": "left", "code": "KT", "gender": "female", "register": "TELL",
        "sender": "Thanh Hải (Kế toán)", "color": "#ea580c",
        "show_header": True, "stack_mode": "append_same",
        "text": "Chậm đơn khách chửi thì anh tự nghe máy.",
        "tts": "Chậm đơn khách chửi thì anh tự nghe máy.",
        "pop_sfx": "assets/sfx_pop.mp3",
        "after_sfx": "assets/ep_ho_ca_koi/emotional_damage_tight.wav", "after_sfx_dur": 2.40, "after_sfx_vol": 0.90,
        "music_drop": True,
        "typing": False, "voice_delay": 0.06, "post_gap": 2.48,
    },

    # --- KIM CHỐT HẠ + CẢNH GIF PATRICK RIÊNG ---
    {
        "idx": 24, "kind": "msg", "side": "left", "code": "KM", "gender": "female", "register": "ASK",
        "sender": "Kim (Nhân sự)", "color": "#9333ea",
        "show_header": False, "stack_mode": "clear",
        "text": "Thế mai nhà thầu sang ai tiếp 😭",
        "tts": "Thế mai nhà thầu sang ai tiếp?",
        "pop_sfx": "assets/sfx_pop.mp3",
        "typing": False, "voice_delay": 0.06, "post_gap": 0.22,
    },
    {
        "idx": 25, "kind": "media_shot", "code": "KM",
        "sender": "Kim (Nhân sự)", "color": "#9333ea",
        "show_header": False, "reaction_emoji": "😭",
        "meme_gif": "assets/memes_ep2/crying_man.gif",
        "after_sfx": "assets/sfx_pack/sadness-1.mp3", "after_sfx_dur": 1.20, "after_sfx_vol": 0.68,
        "music_drop": True,
        "hold": 1.30,
    },

    # --- END CARD CTA ---
    {
        "idx": 26, "kind": "end_card", "code": "CTA", "gender": "female", "register": "TELL",
        "show_header": True,
        "text": "Sếp chiều đối tác bất chấp: Công ty ae có giống vậy không? 😂👇",
        "tts": "Sếp chiều đối tác bất chấp, công ty anh em có giống vậy không? Bình luận bên dưới, theo dõi chờ tập ba nhé!",
        "meme_gif": "assets/memes_ep2/homer_bush.gif",
        "after_sfx": "assets/sfx_pack/wow.mp3", "after_sfx_dur": 1.15, "after_sfx_vol": 0.62,
        "voice_delay": 0.06, "post_gap": 1.28,
    },
]


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


def _print_tempo_report(manifest_rows):
    voice_rows = [r for r in manifest_rows if r.get("audio_file") and "active_sps" in r]
    if not voice_rows:
        return
    sps_all = [float(r["active_sps"]) for r in voice_rows]
    mean_sps = sum(sps_all) / len(sps_all)
    std_sps = math.sqrt(sum((x - mean_sps) ** 2 for x in sps_all) / len(sps_all))
    print("\n" + "-" * 78)
    print("📊 BẢNG KIỂM TRA SPEAKING TEMPO (active_sps — âm tiết/giây)")
    print("-" * 78)
    print(f"{'Idx':>4} | {'Reg':<4} | {'Syl':>3} | {'Dur':>5} | {'F0(Hz)':>6} | {'SPS':>5} | {'Atempo':>6} | Nội dung")
    for r in voice_rows:
        print(
            f"#{r['idx']:02d}  | {r.get('register',''):<4} | {r.get('n_syl',0):>3} | "
            f"{r.get('duration_sec',0):>4.2f}s | {r.get('f0_hz',0):>6.1f} | "
            f"{r.get('active_sps',0):>5.2f} | {r.get('atempo_applied',1.0):>6.3f} | {r.get('tts','')}"
        )
    print("-" * 78)
    print(f"  Mean active_sps = {mean_sps:.2f} syl/s | Std = {std_sps:.2f} syl/s (mục tiêu < 0.35 syl/s)")
    print("-" * 78 + "\n")


def main():
    setup_ffmpeg()
    print("=" * 68)
    print("🎬 RENDER TẬP 2 (CON BÒ TEMPO-LOCKED + CARBON AB_07): HỒ CÁ KOI CỦA SẾP")
    print("=" * 68)

    manifest_path = synthesize_carbon_voices(
        items=ITEMS,
        out_dir=VOICES_DIR,
        mode="all_conbo",
        end_card_female=False,
        n_candidates=6,
        reuse_cache=True,
    )

    manifest_rows = json.loads(manifest_path.read_text(encoding="utf-8"))
    _print_tempo_report(manifest_rows)

    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    subprocess.check_call(
        [
            "node",
            str(WORKSPACE / "render_ho_ca_koi_frames.js"),
            str(FRAMES_DIR),
            str(manifest_path),
            str(STAGE_HTML),
        ]
    )

    items_by_idx = {it["idx"]: it for it in manifest_rows}
    events = json.loads((FRAMES_DIR / "events_timeline.json").read_text(encoding="utf-8"))
    total_dur = sum(ev["duration"] for ev in events)
    print(f"  Tổng thời lượng Tập 2: {total_dur:.2f}s ({len(events)} sự kiện)")

    mixed_wav = FRAMES_DIR / "ho_ca_koi_mixed.wav"
    mix_carbon_ab07_audio(
        items_by_idx=items_by_idx,
        events=events,
        voices_dir=VOICES_DIR,
        output_wav=mixed_wav,
        total_dur=total_dur,
        bgm_path=None,
        voice_delay_sec=0.06,
        target_lufs=-12.8,
    )

    concat_txt = FRAMES_DIR / "concat_ho_ca_koi.txt"
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

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_txt),
            "-i",
            str(mixed_wav),
            *_pick_h264_codec_args(),
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-t",
            f"{total_dur:.2f}",
            "-movflags",
            "+faststart",
            str(OUTPUT_MP4),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    dur = probe_duration(OUTPUT_MP4)
    size_mb = OUTPUT_MP4.stat().st_size / (1024 * 1024)
    print(f"\n✅ HOÀN TẤT TẬP 2 (TEMPO-LOCKED + CARBON AB_07): {OUTPUT_MP4} ({dur:.2f}s, {size_mb:.2f} MB)")


if __name__ == "__main__":
    main()

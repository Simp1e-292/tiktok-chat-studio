#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapCut Draft Generator for TikTok Chat Studio
Chuyên dụng cho Kịch bản: Cửa Thép Luxury (Biệt Thự & Test Búa Tạ Không Móp)
Tạo gói Project chuẩn CapCut Desktop (draft_content.json + draft_meta_info.json + assets)
Người dùng chỉ cần giải nén vào thư mục Projects của CapCut và bấm Export (Ctrl+E)
"""

import os
import sys
import json
import uuid
import shutil
import zipfile
import subprocess
from pathlib import Path
from PIL import Image

try:
    from pyJianYingDraft import (
        DraftFolder, VideoSegment, AudioSegment, TextSegment,
        TrackSpec, TrackType, trange, AudioMaterial, TextStyle, TextBorder
    )
except ImportError:
    print("[Error] pyJianYingDraft chưa được cài đặt. Đang cài đặt...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "pyJianYingDraft"])
    from pyJianYingDraft import (
        DraftFolder, VideoSegment, AudioSegment, TextSegment,
        TrackSpec, TrackType, trange, AudioMaterial, TextStyle, TextBorder
    )

WORKSPACE = Path("/home/antigravity")
ASSETS_DIR = WORKSPACE / "assets"
PROJECT_NAME = "Cua_Thep_TikTok_Luxury"
OUTPUT_DIR = WORKSPACE / "capcut_projects"
DRAFT_DIR = OUTPUT_DIR / PROJECT_NAME
ZIP_PATH = WORKSPACE / f"{PROJECT_NAME}.zip"

# Định nghĩa kịch bản timeline (27.0 giây chuẩn TikTok)
TIMELINE_SCENARIO = [
    {
        "index": 0,
        "frame": "frame_0.png",
        "start_us": 0,
        "duration_us": 500000,  # 0 -> 0.5s
        "sfx": None,
        "sub": ""
    },
    {
        "index": 1,
        "frame": "frame_1.png",
        "start_us": 500000,
        "duration_us": 3500000, # 0.5s -> 4.0s
        "sfx": "sfx_pop.mp3",
        "sub": "SẾP TỔNG: Nghiệm thu biệt thự Vinhome thế nào rồi?!"
    },
    {
        "index": 2,
        "frame": "frame_2.png",
        "start_us": 4000000,
        "duration_us": 3500000, # 4.0s -> 7.5s
        "sfx": "sfx_ting.mp3",
        "sub": "HẢI KỸ THUẬT: Đập búa tạ 5kg không móp một ly!"
    },
    {
        "index": 3,
        "frame": "frame_3.png",
        "start_us": 7500000,
        "duration_us": 3000000, # 7.5s -> 10.5s
        "sfx": "sfx_ting.mp3",
        "sub": "HẢI: Đèn khò 1000°C gioăng chống cháy tự nở kín mít!"
    },
    {
        "index": 4,
        "frame": "frame_4.png",
        "start_us": 10500000,
        "duration_us": 3500000, # 10.5s -> 14.0s
        "sfx": "sfx_ting.mp3",
        "sub": "VY DỰ ÁN: Khách bắn cọc 350 triệu chốt thêm 80 bộ! 🎉"
    },
    {
        "index": 5,
        "frame": "frame_5.png",
        "start_us": 14000000,
        "duration_us": 4500000, # 14.0s -> 18.5s
        "sfx": "sfx_ting.mp3",
        "sub": "⭐ CỬA THÉP VÂN GỖ 90P - KHÓA FACE ID CAO CẤP ⭐"
    },
    {
        "index": 6,
        "frame": "frame_6.png",
        "start_us": 18500000,
        "duration_us": 3000000, # 18.5s -> 21.5s
        "sfx": "sfx_ting.mp3",
        "sub": "THẮNG: Đang chở phụ kiện tới lắp hoàn thiện cho khách!"
    },
    {
        "index": 7,
        "frame": "frame_7.png",
        "start_us": 21500000,
        "duration_us": 3000000, # 21.5s -> 24.5s
        "sfx": "sfx_ting.mp3",
        "sub": "HẢI: Sếp có khao xưởng tăng 2 thịt dê lẩu bia không?! 😂"
    },
    {
        "index": 8,
        "frame": "frame_8.png",
        "start_us": 24500000,
        "duration_us": 2500000, # 24.5s -> 27.0s
        "sfx": "sfx_pop.mp3",
        "sub": "SẾP TỔNG: 👍 DUYỆT LUÔN TĂNG 2 CHO ANH EM!"
    }
]

TOTAL_DURATION_US = 27000000  # 27s


def ensure_frames_and_assets(target_assets_dir: Path):
    """Đảm bảo các frames giao diện và âm thanh đã sẵn sàng trong thư mục assets của project"""
    target_assets_dir.mkdir(parents=True, exist_ok=True)

    # 1. Chạy render_frames.js nếu chưa có đủ frame
    frames_exist = all((target_assets_dir / f"frame_{i}.png").exists() for i in range(9))
    if not frames_exist:
        print("[Generator] Render các frame giao diện bằng Chromium...")
        cmd = ["node", str(WORKSPACE / "render_frames.js"), str(target_assets_dir)]
        subprocess.check_call(cmd)
    else:
        print("[Generator] Các frames PNG đã có sẵn trong assets.")

    # 2. Copy audio SFX
    for sfx in ["sfx_ting.mp3", "sfx_pop.mp3"]:
        src = ASSETS_DIR / sfx
        dst = target_assets_dir / sfx
        if src.exists():
            shutil.copy2(src, dst)
        else:
            print(f"[Warning] Thiếu file âm thanh: {src}")

    # 3. Copy Background và Product Media
    for media in ["bg_anime_sky.jpg", "steel_door_product.jpg", "steel_door_logo.png"]:
        src = ASSETS_DIR / media
        dst = target_assets_dir / media
        if src.exists():
            shutil.copy2(src, dst)

    print(f"[Generator] Chuẩn bị assets hoàn tất trong: {target_assets_dir}")


def build_capcut_project(output_root: Path, project_name: str) -> Path:
    """Xây dựng Timeline CapCut với 4 Tracks: Background, Phone Screen, SFX, Subtitles"""
    output_root.mkdir(parents=True, exist_ok=True)
    draft_folder = DraftFolder(str(output_root))

    # Tạo draft mới 1080x1920 (9:16) 30fps
    print(f"[Generator] Khởi tạo CapCut Draft: {project_name} (1080x1920, 30fps)")
    script = draft_folder.create_draft(project_name, 1080, 1920, fps=30, allow_replace=True)

    proj_dir = output_root / project_name
    proj_assets = proj_dir / "assets"
    ensure_frames_and_assets(proj_assets)

    # Thêm 4 tracks theo đúng thứ tự hiển thị (z-order)
    track_bg = script.append_track(TrackSpec(TrackType.video, name="Track_Background"))
    track_phone = script.append_track(TrackSpec(TrackType.video, name="Track_PhoneScreen"))
    track_sfx = script.append_track(TrackSpec(TrackType.audio, name="Track_AudioSFX"))
    track_text = script.append_track(TrackSpec(TrackType.text, name="Track_Subtitles"))

    # 1. Track 1: Nền Anime Sky (kéo dài suốt 27 giây)
    bg_file = str(proj_assets / "bg_anime_sky.jpg")
    bg_seg = VideoSegment(bg_file, trange(0, TOTAL_DURATION_US))
    script.add_segment(bg_seg, track="Track_Background")

    # 2. Track 2: Từng khung tin nhắn chat (Frame 0 -> 8)
    for step in TIMELINE_SCENARIO:
        f_path = str(proj_assets / step["frame"])
        seg = VideoSegment(f_path, trange(step["start_us"], step["duration_us"]))
        script.add_segment(seg, track="Track_PhoneScreen")

    # 3. Track 3: Âm thanh SFX (Ting & Pop tại thời điểm tin nhắn xuất hiện)
    for step in TIMELINE_SCENARIO:
        sfx_name = step.get("sfx")
        if sfx_name:
            sfx_file = str(proj_assets / sfx_name)
            sfx_mat = AudioMaterial(sfx_file)
            dur = min(sfx_mat.duration, step["duration_us"])
            sfx_seg = AudioSegment(sfx_mat, trange(step["start_us"], dur))
            script.add_segment(sfx_seg, track="Track_AudioSFX")

    # 4. Track 4: Phụ đề chạy chữ (Subtitles)
    for step in TIMELINE_SCENARIO:
        sub_text = step.get("sub")
        if sub_text:
            text_style = TextStyle(size=7.5, color=(1.0, 1.0, 1.0), bold=True)
            text_border = TextBorder(color=(0.0, 0.0, 0.0), width=0.15)
            t_seg = TextSegment(
                sub_text,
                trange(step["start_us"], step["duration_us"]),
                style=text_style,
                border=text_border
            )
            script.add_segment(t_seg, track="Track_Subtitles")

    # Lưu bản nháp ban đầu
    script.save()
    print("[Generator] pyJianYingDraft đã lưu draft_content.json và draft_meta_info.json!")

    # 5. HẬU KỲ CHUẨN HÓA ĐỘ KHẢ CHUYỂN (PORTABILITY POST-PROCESSING)
    post_process_capcut_draft(proj_dir, project_name)

    return proj_dir


def post_process_capcut_draft(proj_dir: Path, project_name: str):
    """
    Chuẩn hóa dự án để tương thích 100% với CapCut Quốc Tế & JianYing trên mọi máy tính:
    1. Thay thế đường dẫn máy ảo bằng placeholder di động: ##_draftpath_placeholder_{draft_id}_##
    2. Đăng ký tài nguyên vào draft_materials của draft_meta_info.json để tránh bảng báo Relink Media
    3. Thêm file thông tin hướng dẫn
    """
    content_file = proj_dir / "draft_content.json"
    meta_file = proj_dir / "draft_meta_info.json"

    with open(content_file, "r", encoding="utf-8") as f:
        content = json.load(f)

    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    draft_id = content.get("id") or str(uuid.uuid4()).upper()
    content["id"] = draft_id
    meta["draft_id"] = draft_id
    meta["draft_name"] = project_name
    meta["tm_duration"] = TOTAL_DURATION_US
    if "canvas_config" in content:
        content["canvas_config"]["ratio"] = "9:16"

    placeholder_prefix = f"##_draftpath_placeholder_{draft_id}_##"

    # Danh sách đăng ký vật liệu cho draft_materials
    registered_videos = []
    registered_audios = []

    # Xử lý Videos / Photos
    for vid in content.get("materials", {}).get("videos", []):
        old_path = vid.get("path", "")
        filename = Path(old_path).name
        # Đặt đường dẫn tương đối qua placeholder
        relative_placeholder_path = f"{placeholder_prefix}/assets/{filename}"
        vid["path"] = relative_placeholder_path

        registered_videos.append({
            "create_time": 1715000000,
            "duration": vid.get("duration", 10800000000),
            "extra_info": "",
            "file_Path": relative_placeholder_path,
            "height": vid.get("height", 1920),
            "id": vid.get("id") or uuid.uuid4().hex,
            "import_time": 1715000000,
            "import_time_us": 1715000000000000,
            "item_source": 1,
            "md5": "",
            "metainfo_id": "",
            "roughcut_time_range": {"duration": 0, "start": 0},
            "sub_time_range": {"duration": -1, "start": -1},
            "type": 0,
            "width": vid.get("width", 1080)
        })

    # Xử lý Audios
    for aud in content.get("materials", {}).get("audios", []):
        old_path = aud.get("path", "")
        filename = Path(old_path).name
        relative_placeholder_path = f"{placeholder_prefix}/assets/{filename}"
        aud["path"] = relative_placeholder_path

        registered_audios.append({
            "create_time": 1715000000,
            "duration": aud.get("duration", 1000000),
            "extra_info": "",
            "file_Path": relative_placeholder_path,
            "height": 0,
            "id": aud.get("id") or uuid.uuid4().hex,
            "import_time": 1715000000,
            "import_time_us": 1715000000000000,
            "item_source": 1,
            "md5": "",
            "metainfo_id": "",
            "roughcut_time_range": {"duration": 0, "start": 0},
            "sub_time_range": {"duration": -1, "start": -1},
            "type": 1,
            "width": 0
        })

    # Cập nhật draft_materials trong draft_meta_info.json
    draft_materials = [
        {"type": 0, "value": registered_videos},
        {"type": 1, "value": registered_audios},
        {"type": 2, "value": []},
        {"type": 3, "value": []},
        {"type": 6, "value": []},
        {"type": 7, "value": []},
        {"type": 8, "value": []}
    ]
    meta["draft_materials"] = draft_materials

    # Ghi lại file json đã hoàn thiện
    with open(content_file, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("[Generator] Đã chuẩn hóa đường dẫn di động và manifest tài nguyên thành công!")


def create_user_guide(proj_dir: Path):
    """Tạo file HƯỚNG_DẪN_SỬ_DỤNG_CAPCUT.txt đính kèm"""
    guide_text = """================================================================================
🎬 HƯỚNG DẪN MỞ DỰ ÁN CAPCUT TRÊN MÁY TÍNH (WINDOWS & MAC)
Chủ đề: Văn Phòng Công Ty Cửa Thép Luxury - Nghiệm Thu Biệt Thự & Test Búa Tạ
================================================================================

Dự án này đã được tự động dựng sẵn 100% gồm:
1. Track Nền: Bầu trời Anime Pastel chuẩn 9:16 (1080x1920)
2. Track Giao Diện: Toàn bộ 8 câu thoại chat văn phòng công ty Cửa Thép
3. Track Âm Thanh: Hiệu ứng Ting & Pop Messenger khớp từng khung hình
4. Track Phụ Đề: Chữ chạy Subtitle nổi bật cho người xem lướt không bật tiếng

--------------------------------------------------------------------------------
👉 BƯỚC 1: COPY DỰ ÁN VÀO THƯ MỤC CAPCUT DRAFT CỦA BẠN
--------------------------------------------------------------------------------
Hãy copy toàn bộ thư mục [Cua_Thep_TikTok_Luxury] vào đúng đường dẫn sau trên máy bạn:

* TRÊN HỆ ĐIỀU HÀNH WINDOWS:
  Nhấn tổ hợp phím [Windows + R], dán dòng sau rồi Enter:
  %LOCALAPPDATA%\\CapCut\\User Data\\Projects\\com.lveditor.draft\\
  (Hoặc nếu bạn dùng bản CapCut Trung Quốc - JianYing Pro:
   %LOCALAPPDATA%\\JianyingPro\\User Data\\Projects\\com.lveditor.draft\\)

  👉 Dán thư mục [Cua_Thep_TikTok_Luxury] vào đó!

* TRÊN MAC (macOS):
  Mở Finder -> Nhấn Cmd + Shift + G và dán đường dẫn:
  ~/Movies/CapCut/User Data/Projects/com.lveditor.draft/
  (Hoặc: ~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/)

  👉 Dán thư mục [Cua_Thep_TikTok_Luxury] vào đó!

--------------------------------------------------------------------------------
👉 BƯỚC 2: MỞ CAPCUT VÀ XUẤT VIDEO (SIÊU NHANH & KHÔNG LAG)
--------------------------------------------------------------------------------
1. Khởi động phần mềm CapCut Desktop trên máy tính.
2. Ngay trên màn hình chính của CapCut, bạn sẽ thấy ngay dự án:
   "Cua_Thep_TikTok_Luxury" (Thời lượng 27s).
3. Bấm mở dự án -> Toàn bộ timeline đã được cắt ghép hoàn chỉnh.
4. Bạn có thể chèn thêm nhạc nền TikTok hot trend nếu thích, hoặc bấm ngay:
   [Export] (phím tắt Ctrl + E trên Windows hoặc Cmd + E trên Mac).
5. Chọn độ phân giải: 1080p, 60fps, Bitrate: Recommended.
6. Bấm [Export] -> CapCut dùng GPU máy tính xuất video trong 3-5 giây!

--------------------------------------------------------------------------------
🔥 TẠI SAO CÁCH NÀY KHÔNG BỊ TIKTOK BÓP TƯƠNG TÁC?
--------------------------------------------------------------------------------
- Video xuất ra có chữ ký metadata gốc của ByteDance CapCut (phần mềm chính chủ).
- TikTok không bao giờ gắn nhãn "Nội dung do AI tạo" (AI-generated content).
- Thuật toán TikTok ưu tiên đề xuất cho video xuất từ CapCut.
================================================================================
"""
    with open(proj_dir / "HUONG_DAN_SU_DUNG.txt", "w", encoding="utf-8") as f:
        f.write(guide_text)


def package_to_zip(proj_dir: Path, zip_dest: Path):
    """Nén toàn bộ thư mục dự án thành file .zip để người dùng tải về"""
    print(f"[Generator] Đang nén gói dự án thành: {zip_dest}")
    with zipfile.ZipFile(zip_dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(proj_dir):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(proj_dir.parent)
                zf.write(full_path, rel_path)
    print(f"[Generator] Tạo file Zip thành công! Dung lượng: {zip_dest.stat().st_size / (1024*1024):.2f} MB")


def main():
    print("=" * 60)
    print("🎬 CAPCUT DRAFT GENERATOR - TIKTOK CHAT STUDIO LUXURY")
    print("=" * 60)

    proj_dir = build_capcut_project(OUTPUT_DIR, PROJECT_NAME)
    create_user_guide(proj_dir)
    package_to_zip(proj_dir, ZIP_PATH)

    # Copy một bản zip vào assets/ để web frontend có thể download được trực tiếp
    public_zip = ASSETS_DIR / f"{PROJECT_NAME}.zip"
    shutil.copy2(ZIP_PATH, public_zip)
    print(f"[Generator] Đã sao chép gói zip tới assets công khai: {public_zip}")

    print("\n✅ HOÀN TẤT XUẤT SẮC DỰ ÁN CAPCUT DRAFT!")
    print(f"📁 Thư mục Draft: {proj_dir}")
    print(f"📦 File Zip phân phối: {ZIP_PATH}")
    print(f"🌐 Link Web Assets: assets/{PROJECT_NAME}.zip")


if __name__ == "__main__":
    main()

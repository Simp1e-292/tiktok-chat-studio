#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapCut Draft Generator for TikTok Chat Studio
Chuyên dụng cho Kịch bản: Cửa Thép Luxury (Chốt Cọc 100 Bộ Biệt Thự)
Tạo gói Project chuẩn CapCut Desktop với 4 TRACKS ĐỘC LẬP:
- Track 1: Video Nền Anime Sky (1080x1920)
- Track 2: Video Giao Diện Chat iPhone Retina (9 frames tuần tự - đã có sẵn chữ sắc nét)
- Track 3: Audio SFX (Ting & Pop Messenger)
- Track 4: Audio Lồng Tiếng Voiceover Từng Nhân Vật (Tốc độ chuẩn 1.0x tự nhiên)

Người dùng chỉ cần mở CapCut Desktop và bấm Export (Ctrl+E)
"""

import os
import sys
import time
import json
import uuid
import stat
import shutil
import zipfile
import subprocess
from pathlib import Path
from PIL import Image


def _setup_capcut_ffmpeg_path():
    """Tự động tìm ffmpeg/ffprobe đi kèm CapCut Desktop trên Windows và thêm vào PATH"""
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    local_apps = Path(os.path.expandvars(r"%LOCALAPPDATA%\CapCut\Apps"))
    if local_apps.is_dir():
        for exe in sorted(local_apps.rglob("ffmpeg.exe"), reverse=True):
            tool_dir = str(exe.parent)
            if tool_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = tool_dir + os.pathsep + os.environ.get("PATH", "")
            break


def clean_desktop_ini(root_dir: Path):
    """Dọn sạch các file hệ thống desktop.ini do Google Drive tự sinh gây lỗi Git / Zip / CapCut"""
    if not root_dir.exists():
        return
    removed = 0
    for ini_file in root_dir.rglob("desktop.ini"):
        try:
            os.chmod(ini_file, stat.S_IWRITE)
            ini_file.unlink()
            removed += 1
        except Exception:
            try:
                subprocess.run(f'attrib -r -h -s "{ini_file}"', shell=True, capture_output=True)
                ini_file.unlink()
                removed += 1
            except Exception:
                pass
    if removed:
        print(f"[GoogleDrive-Fix] Đã dọn {removed} file desktop.ini trong {root_dir.name}")


_setup_capcut_ffmpeg_path()

# Robust rmtree for Windows (handles hidden/system/readonly desktop.ini)
_orig_rmtree = shutil.rmtree
def _safe_rmtree(path, *args, **kwargs):
    def on_err(func, p, exc):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except Exception:
            pass
    if sys.version_info >= (3, 12):
        if "onexc" not in kwargs:
            kwargs["onexc"] = on_err
    else:
        if "onerror" not in kwargs:
            kwargs["onerror"] = on_err
    try:
        return _orig_rmtree(path, *args, **kwargs)
    except Exception:
        try:
            subprocess.run(f'attrib -r -h -s "{path}" /s /d', shell=True, capture_output=True)
            return _orig_rmtree(path, *args, **kwargs)
        except Exception:
            pass
shutil.rmtree = _safe_rmtree

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

try:
    from gtts import gTTS
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "gTTS"])
    from gtts import gTTS

WORKSPACE = Path(__file__).resolve().parent
ASSETS_DIR = WORKSPACE / "assets"
PROJECT_NAME = "Cua_Thep_TikTok_Luxury"
OUTPUT_DIR = WORKSPACE / "capcut_projects"
DRAFT_DIR = OUTPUT_DIR / PROJECT_NAME
ZIP_PATH = WORKSPACE / f"{PROJECT_NAME}.zip"

# Định nghĩa dữ liệu thoại kịch bản Văn Phòng Cửa Thép
RAW_DIALOGUE = [
    {
        "id": "gmsg_1",
        "index": 1,
        "frame": "frame_1.png",
        "sender": "SẾP TỔNG",
        "role": "sep",
        "text": "Vy ơi! Tình hình đi chốt cọc một trăm bộ cửa thép biệt thự cho bác đại gia thế nào rồi?!",
        "sfx": "sfx_pop.mp3",
        "sub": "SẾP TỔNG: Chốt cọc 100 bộ cửa thép cho đại gia thế nào rồi?!"
    },
    {
        "id": "gmsg_2",
        "index": 2,
        "frame": "frame_2.png",
        "sender": "Vy Dự Án (Sale)",
        "role": "vy",
        "text": "Ban đầu bác chủ nhà khó tính lắm Sếp, bảo cửa thép mà không cách âm thì không lấy!",
        "sfx": "sfx_ting.mp3",
        "sub": "VY SALE: Bác bảo cửa thép mà không cách âm thì không lấy! 😅"
    },
    {
        "id": "gmsg_3",
        "index": 3,
        "frame": "frame_3.png",
        "sender": "Hải Kỹ Thuật",
        "role": "hai",
        "text": "Thế là em đứng ngoài gào như loa phường, còn bác đứng trong phòng nghe nhạc thiền êm ru Sếp ạ!",
        "sfx": "sfx_ting.mp3",
        "sub": "HẢI KT: Em gào như loa phường, bác nghe nhạc thiền êm ru! 😂"
    },
    {
        "id": "gmsg_4",
        "index": 4,
        "frame": "frame_4.png",
        "sender": "Thắng Công Trình",
        "role": "thang",
        "text": "Chưa hết đâu Sếp, bác còn dắt cả con chó Bec-giê ra cắn thử cửa, chó gãy cụt mất một cái răng!",
        "sfx": "sfx_ting.mp3",
        "sub": "THẮNG: Bác dắt chó Bec-giê ra cắn thử, chó gãy cụt cái răng! 🐕"
    },
    {
        "id": "gmsg_5",
        "index": 5,
        "frame": "frame_5.png",
        "sender": "Vy Dự Án (Sale)",
        "role": "vy",
        "text": "Bác ưng quá cười bảo: Cửa này vợ tao cằn nhằn đóng cửa là yên tĩnh tuyệt đối! Bác chuyển cọc luôn hai trăm triệu!",
        "sfx": "sfx_ting.mp3",
        "sub": "VY SALE: Cửa này vợ cằn nhằn đóng lại là yên! Bác cọc 200tr! 💸"
    },
    {
        "id": "gmsg_6",
        "index": 6,
        "frame": "frame_6.png",
        "sender": "SẾP TỔNG",
        "role": "sep",
        "text": "Haha đỉnh quá! Thế tiền cọc hai trăm triệu đã nổi trong tài khoản công ty chưa?!",
        "sfx": "sfx_pop.mp3",
        "sub": "SẾP TỔNG: Haha đỉnh! Tiền cọc 200tr đã nổi tài khoản chưa?!"
    },
    {
        "id": "gmsg_7",
        "index": 7,
        "frame": "frame_7.png",
        "sender": "Vy Dự Án (Sale)",
        "role": "vy",
        "text": "Dạ nổi rồi ạ! Nhưng bác trừ lại hai triệu tiền đi bọc răng sứ cho con Bec-giê Sếp ơi!",
        "sfx": "sfx_ting.mp3",
        "sub": "VY SALE: Nổi rồi ạ! Nhưng bác trừ 2tr bọc răng sứ cho chó! 🦷"
    },
    {
        "id": "gmsg_8",
        "index": 8,
        "frame": "frame_8.png",
        "sender": "SẾP TỔNG",
        "role": "sep",
        "text": "Trừ vào lương Hải! Còn lại tối nay Sếp bao cả công ty liên hoan bia hơi ăn mừng! Duyệt luôn!",
        "sfx": "sfx_pop.mp3",
        "sub": "SẾP TỔNG: Trừ lương Hải! Tối nay Sếp bao bia hơi cả công ty! 👍"
    }
]


def get_media_duration_us(file_path: str) -> int:
    """Đo thời lượng file audio chính xác theo microsecond (us) qua pymediainfo hoặc ffprobe"""
    try:
        from pymediainfo import MediaInfo
        info = MediaInfo.parse(file_path)
        for track in info.tracks:
            if track.track_type in ('Audio', 'Video') and track.duration:
                return int(round(float(track.duration) * 1000))
    except Exception:
        pass

    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        sec = float(subprocess.check_output(cmd).decode().strip())
        return int(round(sec * 1000000))
    except Exception:
        # Fallback ước tính dung lượng file mp3 (128kbps)
        size_bytes = os.path.getsize(file_path)
        sec = size_bytes / 16000.0
        return int(round(sec * 1000000))


def generate_voiceovers(target_assets_dir: Path):
    """
    Tạo 8 file lồng tiếng từng nhân vật chuẩn tốc độ 1.0x (tự nhiên, rõ chữ):
    - Sếp Tổng: Nam trầm uy lực phong cách ADAM (vi-VN-NamMinhNeural, 1.0x)
    - Vy Sale: Nữ tươi vui, ngọt ngào (vi-VN-HoaiMyNeural, 1.0x)
    - Hải Kỹ Thuật: Nam trẻ trung (vi-VN-NamMinhNeural, 1.0x)
    - Thắng Công Trình: Nam công trình khỏe khoắn (vi-VN-NamMinhNeural, 1.0x)
    """
    print("[VoiceEngine] Đang khởi tạo bộ giọng đọc lồng tiếng chuẩn tốc độ 1.0x...")
    target_assets_dir.mkdir(parents=True, exist_ok=True)

    import asyncio
    try:
        import edge_tts
        has_edge_tts = True
    except ImportError:
        has_edge_tts = False

    async def _render_edge(text: str, voice: str, out_file: Path):
        c = edge_tts.Communicate(text, voice, rate="+0%")
        await c.save(str(out_file))

    for item in RAW_DIALOGUE:
        voice_filename = f"voice_{item['index']}_{item['role']}.mp3"
        out_path = target_assets_dir / voice_filename

        # Chọn giọng theo vai
        if item["role"] == "vy":
            voice_name = "vi-VN-HoaiMyNeural"
        else:
            voice_name = "vi-VN-NamMinhNeural"

        # Tạo mới giọng đọc ở tốc độ chuẩn 1.0x (có retry 3 lần tránh lỗi mạng tạm thời)
        success = False
        if has_edge_tts:
            for attempt in range(1, 4):
                try:
                    asyncio.run(_render_edge(item["text"], voice_name, out_path))
                    if out_path.exists() and out_path.stat().st_size > 1000:
                        success = True
                        break
                except Exception as e:
                    print(f" [VoiceEngine Retry {attempt}/3] Edge-TTS lỗi ở câu {item['index']}: {e}")
                    time.sleep(1.0)
            if not success:
                print(f" [VoiceEngine Warning] Chuyển sang gTTS cho câu {item['index']}")

        if not success:
            tts = gTTS(item["text"], lang="vi")
            tts.save(str(out_path))

        dur_us = get_media_duration_us(str(out_path))
        item["voice_file"] = voice_filename
        item["voice_dur_us"] = dur_us
        print(f" - [Voice 1.0x - {item['index']}] {item['sender']} ({item['role']}): {dur_us/1000000:.2f}s -> {voice_filename}")

    print("[VoiceEngine] Đã tổng hợp thành công toàn bộ 8 file lồng tiếng chuẩn tốc độ 1.0x!")


def ensure_frames_and_assets(target_assets_dir: Path):
    """Đảm bảo các frames giao diện và âm thanh đã sẵn sàng trong thư mục assets của project"""
    target_assets_dir.mkdir(parents=True, exist_ok=True)

    # 1. Kiểm tra frames hoặc trích xuất từ zip có sẵn
    frames_exist = all((target_assets_dir / f"frame_{i}.png").exists() for i in range(9))
    if not frames_exist:
        # Thử trích xuất từ file zip mẫu có sẵn trước
        sample_zip = ASSETS_DIR / f"{PROJECT_NAME}.zip"
        if not sample_zip.exists():
            sample_zip = WORKSPACE.parent / f"{PROJECT_NAME}.zip"
        
        extracted_from_zip = False
        if sample_zip.exists():
            print(f"[Generator] Đang trích xuất frames có sẵn từ: {sample_zip.name}...")
            with zipfile.ZipFile(sample_zip, 'r') as zf:
                for member in zf.namelist():
                    if "/assets/frame_" in member or member.startswith("assets/frame_"):
                        fname = Path(member).name
                        with open(target_assets_dir / fname, "wb") as f_out:
                            f_out.write(zf.read(member))
            frames_exist = all((target_assets_dir / f"frame_{i}.png").exists() for i in range(9))
            if frames_exist:
                extracted_from_zip = True
                print("[Generator] Đã trích xuất thành công toàn bộ frames Retina từ kho lưu trữ!")

        if not extracted_from_zip and not frames_exist:
            print("[Generator] Render các frame giao diện bằng Chromium...")
            cmd = ["node", str(WORKSPACE / "render_frames.js"), str(target_assets_dir)]
            subprocess.check_call(cmd)
    else:
        print("[Generator] Các frames PNG đã có sẵn trong assets.")

    # 2. Sinh toàn bộ file giọng nói lồng tiếng
    generate_voiceovers(target_assets_dir)

    # 3. Copy audio SFX
    for sfx in ["sfx_ting.mp3", "sfx_pop.mp3"]:
        src = ASSETS_DIR / sfx
        dst = target_assets_dir / sfx
        if src.exists():
            shutil.copy2(src, dst)
        else:
            print(f"[Warning] Thiếu file âm thanh: {src}")

    # 4. Copy Background và Product Media
    for media in ["bg_anime_sky.jpg", "steel_door_product.jpg", "steel_door_logo.png"]:
        src = ASSETS_DIR / media
        dst = target_assets_dir / media
        if src.exists():
            shutil.copy2(src, dst)

    print(f"[Generator] Chuẩn bị assets hoàn tất trong: {target_assets_dir}")


def calculate_synced_timeline(assets_dir: Path):
    """
    Tính toán thời gian biểu Timeline khớp từng microsecond theo độ dài thực tế của giọng đọc:
    - Frame 0 (Màn hình chờ): 0.0s -> 0.5s (500,000 us)
    - Từng câu thoại: Bắt đầu khi tin nhắn nảy lên, kéo dài bằng thời lượng giọng đọc + 0.3s nghỉ
    """
    timeline = []
    current_time_us = 500000  # Bắt đầu câu đầu tiên ở 0.5s

    # Bước 0: Màn hình mở đầu
    timeline.append({
        "index": 0,
        "frame": "frame_0.png",
        "start_us": 0,
        "duration_us": 500000,
        "sfx": None,
        "voice": None,
        "sub": ""
    })

    pause_between_us = 300000  # Nghỉ 0.3s giữa các câu nói để tự nhiên

    for item in RAW_DIALOGUE:
        voice_path = str(assets_dir / item["voice_file"])
        voice_dur = get_media_duration_us(voice_path)
        step_duration = voice_dur + pause_between_us

        timeline.append({
            "index": item["index"],
            "frame": item["frame"],
            "start_us": current_time_us,
            "duration_us": step_duration,
            "sfx": item["sfx"],
            "voice": item["voice_file"],
            "voice_dur_us": voice_dur,
            "sub": item["sub"]
        })

        current_time_us += step_duration

    total_us = current_time_us
    print(f"[TimelineSync] Tổng thời lượng video được đồng bộ giọng đọc: {total_us / 1000000:.2f} giây.")
    return timeline, total_us


def build_capcut_project(output_root: Path, project_name: str) -> Path:
    """Xây dựng Timeline CapCut 4 Tracks: Background, Phone Screen, SFX, Voiceover (1.0x, không chữ đè)"""
    output_root.mkdir(parents=True, exist_ok=True)
    draft_folder = DraftFolder(str(output_root))

    proj_dir = output_root / project_name
    print(f"[Generator] Khởi tạo CapCut Draft: {project_name} (1080x1920, 30fps)")
    script = draft_folder.create_draft(project_name, 1080, 1920, fps=30, allow_replace=True)

    proj_assets = proj_dir / "assets"
    ensure_frames_and_assets(proj_assets)
    timeline_steps, total_duration_us = calculate_synced_timeline(proj_assets)

    # Thêm 4 tracks theo đúng thứ tự (z-order) - Không chèn Text đè vì frame chat đã có chữ sẵn
    track_bg = script.append_track(TrackSpec(TrackType.video, name="Track_Background"))
    track_phone = script.append_track(TrackSpec(TrackType.video, name="Track_PhoneScreen"))
    track_sfx = script.append_track(TrackSpec(TrackType.audio, name="Track_AudioSFX"))
    track_voice = script.append_track(TrackSpec(TrackType.audio, name="Track_Voiceover"))

    # 1. Track 1: Nền Anime Sky (kéo dài suốt video)
    bg_file = str(proj_assets / "bg_anime_sky.jpg")
    bg_seg = VideoSegment(bg_file, trange(0, total_duration_us))
    script.add_segment(bg_seg, track="Track_Background")

    # 2. Track 2: Từng khung tin nhắn chat (Frame 0 -> 8, giao diện đã chứa sẵn chữ tin nhắn sắc nét)
    for step in timeline_steps:
        f_path = str(proj_assets / step["frame"])
        seg = VideoSegment(f_path, trange(step["start_us"], step["duration_us"]))
        script.add_segment(seg, track="Track_PhoneScreen")

    # 3. Track 3: Âm thanh SFX (Ting & Pop tại thời điểm tin nhắn xuất hiện)
    for step in timeline_steps:
        sfx_name = step.get("sfx")
        if sfx_name:
            sfx_file = str(proj_assets / sfx_name)
            sfx_mat = AudioMaterial(sfx_file)
            dur = min(sfx_mat.duration, step["duration_us"])
            sfx_seg = AudioSegment(sfx_mat, trange(step["start_us"], dur), volume=0.85)
            script.add_segment(sfx_seg, track="Track_AudioSFX")

    # 4. Track 4: Giọng Đọc Lồng Tiếng Voiceover Từng Nhân Vật Chuẩn Tốc Độ 1.0x
    for step in timeline_steps:
        voice_file = step.get("voice")
        if voice_file:
            v_path = str(proj_assets / voice_file)
            v_mat = AudioMaterial(v_path)
            v_seg = AudioSegment(v_mat, trange(step["start_us"], v_mat.duration), volume=1.3)
            script.add_segment(v_seg, track="Track_Voiceover")

    # Lưu bản nháp ban đầu
    script.save()
    print("[Generator] pyJianYingDraft đã lưu draft_content.json và draft_meta_info.json (4 tracks sạch sẽ, không text đè)!")

    # 6. HẬU KỲ CHUẨN HÓA ĐỘ KHẢ CHUYỂN (PORTABILITY POST-PROCESSING)
    post_process_capcut_draft(proj_dir, project_name, total_duration_us)

    return proj_dir


def post_process_capcut_draft(proj_dir: Path, project_name: str, total_duration_us: int):
    """
    Chuẩn hóa dự án để tương thích 100% với CapCut Quốc Tế & JianYing trên Windows:
    1. Thiết lập đường dẫn thực tế tuyệt đối cho CapCut Desktop
    2. Đăng ký tài nguyên vào draft_materials của draft_meta_info.json
    3. Tạo ảnh thumbnail draft_cover.jpg
    4. Đồng bộ chính xác draft_id và version
    """
    content_file = proj_dir / "draft_content.json"
    meta_file = proj_dir / "draft_meta_info.json"
    cover_file = proj_dir / "draft_cover.jpg"

    # Tạo thumbnail draft_cover.jpg từ frame_1 hoặc bg_anime_sky
    frame1 = proj_dir / "assets" / "frame_1.png"
    if frame1.exists():
        im = Image.open(frame1)
        im.convert("RGB").save(cover_file, "JPEG")

    with open(content_file, "r", encoding="utf-8") as f:
        content = json.load(f)

    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    draft_id = content.get("id") or str(uuid.uuid4()).upper()
    content["id"] = draft_id
    content["new_version"] = "191.0.0"
    content["last_modified_platform"] = {
        "os": "windows",
        "os_version": "10.0.19045",
        "app_id": 359289,
        "app_version": "9.7.1"
    }

    meta["draft_id"] = draft_id
    meta["draft_name"] = project_name
    meta["tm_duration"] = total_duration_us
    meta["draft_new_version"] = "164.0.0"
    meta["draft_cover"] = cover_file.as_posix()
    meta["draft_fold_path"] = proj_dir.as_posix()
    meta["draft_root_path"] = proj_dir.parent.as_posix()

    if "canvas_config" in content:
        content["canvas_config"]["ratio"] = "9:16"

    proj_posix = proj_dir.as_posix()

    # Danh sách đăng ký vật liệu cho draft_materials
    registered_videos = []
    registered_audios = []

    # Xử lý Videos / Photos với đường dẫn tuyệt đối chuẩn xác
    for vid in content.get("materials", {}).get("videos", []):
        filename = Path(vid.get("path", "")).name
        full_abs_path = f"{proj_posix}/assets/{filename}"
        vid["path"] = full_abs_path

        registered_videos.append({
            "create_time": 1715000000,
            "duration": vid.get("duration", 10800000000),
            "extra_info": "",
            "file_Path": full_abs_path,
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

    # Xử lý Audios (SFX + Voiceovers)
    for aud in content.get("materials", {}).get("audios", []):
        filename = Path(aud.get("path", "")).name
        full_abs_path = f"{proj_posix}/assets/{filename}"
        aud["path"] = full_abs_path

        registered_audios.append({
            "create_time": 1715000000,
            "duration": aud.get("duration", 1000000),
            "extra_info": "",
            "file_Path": full_abs_path,
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

    print("[Generator] Đã chuẩn hóa đường dẫn tuyệt đối và manifest tài nguyên thành công!")


def create_user_guide(proj_dir: Path, total_duration_s: float):
    """Tạo file HƯỚNG_DẪN_SỬ_DỤNG_CAPCUT.txt đính kèm"""
    guide_text = f"""================================================================================
🎬 HƯỚNG DẪN MỞ DỰ ÁN CAPCUT TRÊN MÁY TÍNH (WINDOWS & MAC)
Chủ đề: Văn Phòng Công Ty Cửa Thép Luxury - Chốt Cọc 100 Bộ Biệt Thự
Thời lượng: {total_duration_s:.1f} giây • 4 Tracks Sạch Sẽ (Không Chữ Đè) • Giọng Chuẩn 1.0x
================================================================================

Dự án này đã được tự động dựng sẵn 100% gồm:
1. Track Nền: Bầu trời Anime Pastel chuẩn 9:16 (1080x1920)
2. Track Giao Diện: Toàn bộ 9 khung hình tin nhắn chat iPhone Retina (đã có chữ sẵn trong khung chat)
3. Track Âm Thanh SFX: Hiệu ứng Ting & Pop Messenger khớp từng khung hình
4. Track Giọng Đọc (Voiceover - Tốc độ chuẩn 1.0x tự nhiên):
   - Giọng Sếp Tổng: Nam trầm (vi-VN-NamMinhNeural)
   - Giọng Vy Sale: Nữ tươi vui (vi-VN-HoaiMyNeural)
   - Giọng Hải Kỹ Thuật & Thắng Công Trình: Nam rõ chữ (vi-VN-NamMinhNeural)

--------------------------------------------------------------------------------
👉 BƯỚC 1: COPY DỰ ÁN VÀO THƯ MỤC CAPCUT DRAFT CỦA BẠN
--------------------------------------------------------------------------------
(Nếu bạn chạy capcut_draft_generator.py trên Windows, hệ thống đã tự chép và chuẩn hóa đường dẫn sẵn vào CapCut Desktop rồi!)

* TRÊN HỆ ĐIỀU HÀNH WINDOWS:
  Nhấn tổ hợp phím [Windows + R], dán dòng sau rồi Enter:
  %LOCALAPPDATA%\\CapCut\\User Data\\Projects\\com.lveditor.draft\\
  (Hoặc nếu bạn dùng bản CapCut Trung Quốc - JianYing Pro:
   %LOCALAPPDATA%\\JianyingPro\\User Data\\Projects\\com.lveditor.draft\\)

* TRÊN MAC (macOS):
  Mở Finder -> Nhấn Cmd + Shift + G và dán đường dẫn:
  ~/Movies/CapCut/User Data/Projects/com.lveditor.draft/

--------------------------------------------------------------------------------
👉 BƯỚC 2: MỞ CAPCUT VÀ XUẤT VIDEO (SIÊU NHANH & KHÔNG LAG)
--------------------------------------------------------------------------------
1. Khởi động phần mềm CapCut Desktop trên máy tính.
2. Ngay trên màn hình chính của CapCut, bạn sẽ thấy ngay dự án:
   "Cua_Thep_TikTok_Luxury" (Thời lượng ~{total_duration_s:.0f}s).
3. Bấm mở dự án -> Toàn bộ 4 tracks đã khớp giọng đọc 1.0x.
4. Bấm ngay: [Export] (phím tắt Ctrl + E trên Windows hoặc Cmd + E trên Mac).
5. Chọn độ phân giải: 1080p, 60fps, Bitrate: Recommended -> Xuất video trong 3-5 giây!
================================================================================
"""
    with open(proj_dir / "HUONG_DAN_SU_DUNG.txt", "w", encoding="utf-8") as f:
        f.write(guide_text)


def package_to_zip(proj_dir: Path, zip_dest: Path):
    """Nén toàn bộ thư mục dự án thành file .zip để người dùng tải về (bỏ qua desktop.ini)"""
    print(f"[Generator] Đang nén gói dự án thành: {zip_dest}")
    with zipfile.ZipFile(zip_dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(proj_dir):
            for file in files:
                if file.lower() == "desktop.ini":
                    continue
                full_path = Path(root) / file
                rel_path = full_path.relative_to(proj_dir.parent)
                zf.write(full_path, rel_path)
    print(f"[Generator] Tạo file Zip thành công! Dung lượng: {zip_dest.stat().st_size / (1024*1024):.2f} MB")


def main():
    print("=" * 60)
    print("🎬 CAPCUT DRAFT GENERATOR - TIKTOK CHAT STUDIO LUXURY")
    print("🔊 TÍCH HỢP GIỌNG ĐỌC CHUẨN 1.0X • 4 TRACKS SẠCH KHÔNG CHỮ ĐÈ")
    print("=" * 60)

    clean_desktop_ini(WORKSPACE)
    proj_dir = build_capcut_project(OUTPUT_DIR, PROJECT_NAME)
    
    with open(proj_dir / "draft_meta_info.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    total_dur_us = int(meta.get("tm_duration", 43000000))
    total_dur_s = total_dur_us / 1000000.0

    create_user_guide(proj_dir, total_dur_s)
    package_to_zip(proj_dir, ZIP_PATH)

    # Tự động đồng bộ thẳng vào thư mục CapCut Desktop trên Windows (nếu có)
    local_capcut_dir = os.path.expandvars(r'%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft')
    if os.path.isdir(local_capcut_dir):
        dest_capcut_draft = Path(local_capcut_dir) / PROJECT_NAME
        if dest_capcut_draft.exists():
            shutil.rmtree(dest_capcut_draft, ignore_errors=True)
        shutil.copytree(proj_dir, dest_capcut_draft, ignore=shutil.ignore_patterns("desktop.ini"))

        # Chuẩn hóa lại toàn bộ đường dẫn tuyệt đối TRÊN CHÍNH THƯ MỤC ĐÍCH của CapCut Desktop
        post_process_capcut_draft(dest_capcut_draft, PROJECT_NAME, total_dur_us)
        with open(dest_capcut_draft / "draft_meta_info.json", "r", encoding="utf-8") as f_dest_meta:
            dest_meta = json.load(f_dest_meta)
        
        # Cập nhật root_meta_info.json của CapCut Desktop để nhận diện ngay lập tức
        root_meta_path = Path(local_capcut_dir) / "root_meta_info.json"
        if root_meta_path.exists():
            try:
                with open(root_meta_path, "r", encoding="utf-8") as f_root:
                    r_data = json.load(f_root)
                all_drafts = r_data.get("all_draft_store", [])
                entry = next((d for d in all_drafts if d.get("draft_name") == PROJECT_NAME), None)
                if not entry:
                    entry = {"draft_name": PROJECT_NAME}
                    all_drafts.insert(0, entry)
                entry.update({
                    "draft_id": dest_meta["draft_id"],
                    "draft_fold_path": dest_capcut_draft.as_posix(),
                    "draft_root_path": Path(local_capcut_dir).as_posix(),
                    "draft_json_file": (dest_capcut_draft / "draft_content.json").as_posix(),
                    "draft_cover": (dest_capcut_draft / "draft_cover.jpg").as_posix(),
                    "draft_new_version": "164.0.0",
                    "tm_duration": total_dur_us
                })
                with open(root_meta_path, "w", encoding="utf-8") as f_root:
                    json.dump(r_data, f_root, ensure_ascii=False)
            except Exception as e:
                print(f"[Warning] Không thể cập nhật root_meta_info.json: {e}")

        print(f"\n🚀 [CapCut Auto-Sync] Đã cài đặt dự án trực tiếp vào CapCut Desktop!")
        print(f"👉 Đường dẫn: {dest_capcut_draft}")
        print("💡 Bạn chỉ cần mở phần mềm CapCut Desktop lên là sẽ thấy ngay dự án để xuất video!")

    # Copy một bản zip vào assets/ để web frontend có thể download được trực tiếp
    public_zip = ASSETS_DIR / f"{PROJECT_NAME}.zip"
    shutil.copy2(ZIP_PATH, public_zip)
    print(f"[Generator] Đã sao chép gói zip tới assets công khai: {public_zip}")

    print("\n✅ HOÀN TẤT XUẤT SẮC DỰ ÁN CAPCUT DRAFT KÈM GIỌNG ĐỌC!")
    print(f"📁 Thư mục Draft: {proj_dir}")
    print(f"⏱️ Tổng thời lượng: {total_dur_s:.1f} giây")
    print(f"📦 File Zip phân phối: {ZIP_PATH}")
    print(f"🌐 Link Web Assets: assets/{PROJECT_NAME}.zip")


if __name__ == "__main__":
    main()

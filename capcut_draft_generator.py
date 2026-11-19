#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapCut Draft Generator for TikTok Chat Studio
Hỗ trợ CẢ kịch bản mặc định (Cửa Thép Luxury) LẪN bất kỳ kịch bản JSON nào từ Web Studio!
Tạo gói Project chuẩn CapCut Desktop (Windows & Mac) với 4 TRACKS ĐỘC LẬP:
- Track 1: Video Nền 1080x1920 (Anime Sky / Sunset / Custom)
- Track 2: Video Giao Diện Chat iPhone Retina (bo góc trong suốt, không đè chữ)
- Track 3: Audio SFX (Ting & Pop Messenger)
- Track 4: Audio Lồng Tiếng Voiceover Từng Nhân Vật (Tốc độ chuẩn 1.0x tự nhiên)

Bao gồm bộ cài đặt 1-Click trong file .ZIP (CAI_DAT_VAO_CAPCUT.bat / .command) để mở được
ngay trên bất kỳ máy tính Windows/Mac nào mà không bị lỗi mất đường dẫn!
"""

import os
import re
import sys
import time
import json
import uuid
import stat
import base64
import shutil
import hashlib
import zipfile
import argparse
import subprocess
from pathlib import Path


def _pip_install(package_spec: str):
    """Cài đặt gói Python tương thích cả pip mới (--break-system-packages) lẫn pip cũ trên Windows"""
    cmd = [sys.executable, "-m", "pip", "install", package_spec]
    try:
        help_out = subprocess.check_output(
            [sys.executable, "-m", "pip", "install", "--help"],
            stderr=subprocess.STDOUT,
        ).decode(errors="ignore")
        if "--break-system-packages" in help_out and sys.prefix == sys.base_prefix:
            cmd.append("--break-system-packages")
    except Exception:
        pass
    subprocess.check_call(cmd)


def ensure_python_deps():
    """Đảm bảo Pillow, pyJianYingDraft, gTTS và edge-tts đều sẵn sàng"""
    for mod, pkg in [
        ("PIL", "Pillow"),
        ("pyJianYingDraft", "pyJianYingDraft"),
        ("gtts", "gTTS"),
        ("edge_tts", "edge-tts"),
    ]:
        try:
            __import__(mod)
        except ImportError:
            print(f"[Setup] Đang cài đặt thư viện còn thiếu: {pkg}...")
            try:
                _pip_install(pkg)
            except Exception as exc:
                print(f"[Warning] Không thể tự cài {pkg}: {exc}")


ensure_python_deps()

from PIL import Image, ImageDraw, ImageFilter  # noqa: E402
from pyJianYingDraft import (  # noqa: E402
    DraftFolder, VideoSegment, AudioSegment, ClipSettings,
    TrackSpec, TrackType, trange, AudioMaterial
)

try:
    from gtts import gTTS  # noqa: E402
except ImportError:
    gTTS = None


def setup_capcut_ffmpeg_path():
    """Tự động tìm ffmpeg/ffprobe đi kèm CapCut Desktop (hoặc hệ thống) và thêm vào PATH"""
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    candidates = []
    if os.name == "nt":
        for env_var in ("LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)"):
            base = os.environ.get(env_var)
            if base:
                candidates.append(Path(base) / "CapCut" / "Apps")
                candidates.append(Path(base) / "JianyingPro" / "Apps")
    elif sys.platform == "darwin":
        candidates.append(Path("/Applications/CapCut.app/Contents"))
    for root in candidates:
        if root.is_dir():
            for exe_name in ("ffmpeg.exe", "ffmpeg"):
                for exe in sorted(root.rglob(exe_name), reverse=True):
                    tool_dir = str(exe.parent)
                    if tool_dir not in os.environ.get("PATH", ""):
                        os.environ["PATH"] = tool_dir + os.pathsep + os.environ.get("PATH", "")
                    return


def clean_desktop_ini(root_dir: Path):
    """Dọn sạch các file hệ thống desktop.ini do Google Drive tự sinh gây lỗi Git / Zip / CapCut"""
    if not root_dir or not root_dir.exists():
        return
    removed = 0
    for ini_file in root_dir.rglob("desktop.ini"):
        try:
            os.chmod(ini_file, stat.S_IWRITE)
            ini_file.unlink()
            removed += 1
        except Exception:
            if os.name == "nt":
                try:
                    subprocess.run(f'attrib -r -h -s "{ini_file}"', shell=True, capture_output=True)
                    ini_file.unlink()
                    removed += 1
                except Exception:
                    pass
    if removed:
        print(f"[GoogleDrive-Fix] Đã dọn {removed} file desktop.ini trong {root_dir.name}")


setup_capcut_ffmpeg_path()

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
        if os.name == "nt":
            try:
                subprocess.run(f'attrib -r -h -s "{path}" /s /d', shell=True, capture_output=True)
                return _orig_rmtree(path, *args, **kwargs)
            except Exception:
                pass


shutil.rmtree = _safe_rmtree

WORKSPACE = Path(__file__).resolve().parent
ASSETS_DIR = WORKSPACE / "assets"
TTS_CACHE_DIR = ASSETS_DIR / ".tts_cache"
DEFAULT_PROJECT_NAME = "Cua_Thep_TikTok_Luxury"
OUTPUT_DIR = WORKSPACE / "capcut_projects"

# Dữ liệu thoại mặc định (Kịch bản Hài Hước Chốt Cọc Cửa Thép)
RAW_DIALOGUE = [
    {
        "id": "gmsg_1",
        "index": 1,
        "frame": "frame_1.png",
        "sender": "SẾP TỔNG",
        "role": "sep",
        "voice": "vi-VN-NamMinhNeural",
        "text": "Vy ơi! Tình hình đi chốt cọc 100 bộ cửa thép biệt thự cho bác đại gia thế nào rồi?!",
        "sfx": "sfx_pop.mp3",
    },
    {
        "id": "gmsg_2",
        "index": 2,
        "frame": "frame_2.png",
        "sender": "Vy Dự Án (Sale)",
        "role": "vy",
        "voice": "vi-VN-HoaiMyNeural",
        "text": "Ban đầu bác chủ nhà khó tính lắm Sếp, bảo cửa thép mà không cách âm thì không lấy! 😅",
        "sfx": "sfx_ting.mp3",
    },
    {
        "id": "gmsg_3",
        "index": 3,
        "frame": "frame_3.png",
        "sender": "Hải Kỹ Thuật",
        "role": "hai",
        "voice": "vi-VN-NamMinhNeural",
        "text": "Thế là em đứng ngoài gào như loa phường, còn bác đứng trong phòng nghe nhạc thiền êm ru Sếp ạ! 😂",
        "sfx": "sfx_ting.mp3",
    },
    {
        "id": "gmsg_4",
        "index": 4,
        "frame": "frame_4.png",
        "sender": "Thắng Công Trình",
        "role": "thang",
        "voice": "vi-VN-NamMinhNeural",
        "text": "Chưa hết đâu Sếp, bác còn dắt cả con chó Bec-giê ra cắn thử cửa, chó gãy cụt mất một cái răng! 🐕",
        "sfx": "sfx_ting.mp3",
    },
    {
        "id": "gmsg_5",
        "index": 5,
        "frame": "frame_5.png",
        "sender": "Vy Dự Án (Sale)",
        "role": "vy",
        "voice": "vi-VN-HoaiMyNeural",
        "text": "Bác ưng quá cười bảo: 'Cửa này vợ tao cằn nhằn đóng cửa là yên tĩnh tuyệt đối!' Bác chuyển cọc luôn 200 triệu! 💸",
        "sfx": "sfx_ting.mp3",
    },
    {
        "id": "gmsg_6",
        "index": 6,
        "frame": "frame_6.png",
        "sender": "SẾP TỔNG",
        "role": "sep",
        "voice": "vi-VN-NamMinhNeural",
        "text": "Haha đỉnh quá! Thế tiền cọc 200 triệu đã nổi trong tài khoản công ty chưa?!",
        "sfx": "sfx_pop.mp3",
    },
    {
        "id": "gmsg_7",
        "index": 7,
        "frame": "frame_7.png",
        "sender": "Vy Dự Án (Sale)",
        "role": "vy",
        "voice": "vi-VN-HoaiMyNeural",
        "text": "Dạ nổi rồi ạ! Nhưng bác trừ lại 2 triệu tiền đi bọc răng sứ cho con Bec-giê Sếp ơi! 🦷",
        "sfx": "sfx_ting.mp3",
    },
    {
        "id": "gmsg_8",
        "index": 8,
        "frame": "frame_8.png",
        "sender": "SẾP TỔNG",
        "role": "sep",
        "voice": "vi-VN-NamMinhNeural",
        "text": "Trừ vào lương Hải! Còn lại tối nay Sếp bao cả công ty liên hoan bia hơi ăn mừng! Duyệt luôn! 👍",
        "sfx": "sfx_pop.mp3",
    },
]


def _clean_tts_text(text: str) -> str:
    """Làm sạch emoji / ký tự thừa để TTS đọc tự nhiên hơn"""
    if not text:
        return ""
    # Loại bỏ các emoji ngoài khối văn bản chuẩn để tránh TTS đọc ký tự lạ
    cleaned = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]+", " ", str(text))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def get_media_duration_us(file_path: str) -> int:
    """Đo thời lượng file audio chính xác theo microsecond (us)"""
    try:
        from pymediainfo import MediaInfo
        info = MediaInfo.parse(file_path)
        for track in info.tracks:
            if track.track_type in ("Audio", "Video") and track.duration:
                return int(round(float(track.duration) * 1000))
    except Exception:
        pass

    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]
        sec = float(subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip())
        return max(100000, int(round(sec * 1000000)))
    except Exception:
        size_bytes = os.path.getsize(file_path)
        sec = max(0.5, size_bytes / 16000.0)
        return int(round(sec * 1000000))


def pick_h264_codec_args():
    """Chọn encoder H.264 khả dụng (libx264 hoặc Windows h264_mf/nvenc/qsv/macOS videotoolbox)"""
    try:
        enc_out = subprocess.check_output(["ffmpeg", "-encoders"], stderr=subprocess.STDOUT).decode(errors="ignore")
    except Exception:
        enc_out = ""
    if "libx264" in enc_out:
        return ["-c:v", "libx264", "-preset", "medium", "-crf", "21"]
    if "h264_nvenc" in enc_out:
        return ["-c:v", "h264_nvenc", "-b:v", "4M"]
    if "h264_qsv" in enc_out:
        return ["-c:v", "h264_qsv", "-b:v", "4M"]
    if "h264_mf" in enc_out:
        return ["-c:v", "h264_mf", "-b:v", "4M"]
    if "h264_videotoolbox" in enc_out:
        return ["-c:v", "h264_videotoolbox", "-b:v", "4M"]
    return ["-c:v", "mpeg4", "-q:v", "4"]


def _infer_voice_for_char(char: dict) -> str:
    """Suy luận giọng Neural Edge-TTS phù hợp cho nhân vật"""
    if char and char.get("voice"):
        return str(char["voice"])
    name_l = (char.get("name") or "").lower() if char else ""
    pitch = float(char.get("pitch", 1.0)) if char else 1.0
    female_hints = ("vy", "cô ", "chị ", "em gái", "nữ", "lan", "mai", "hoa", "linh", "ngọc", "trang")
    if any(h in name_l for h in female_hints) or pitch >= 1.22:
        return "vi-VN-HoaiMyNeural"
    return "vi-VN-NamMinhNeural"


def normalize_scenario_items(scenario_data: dict = None, characters: list = None):
    """Chuẩn hóa danh sách hội thoại từ Web Studio JSON hoặc mặc định RAW_DIALOGUE"""
    if not scenario_data:
        return [dict(item) for item in RAW_DIALOGUE], "group_messenger", "assets/bg_anime_sky.jpg"

    chars = characters or []
    char_by_id = {c.get("id"): c for c in chars if c.get("id")}
    char_by_name = {c.get("name"): c for c in chars if c.get("name")}
    owner_char = char_by_id.get(scenario_data.get("ownerCharId")) or next(
        (c for c in chars if c.get("role") == "owner"), None
    )
    cust_char = char_by_id.get(scenario_data.get("customerCharId")) or next(
        (c for c in chars if c.get("role") == "customer"), None
    )

    theme = scenario_data.get("theme") or "messenger_ios"
    wallpaper = scenario_data.get("bgWallpaper") or "assets/bg_anime_sky.jpg"
    messages = scenario_data.get("messages") or []

    items = []
    for idx, msg in enumerate(messages, start=1):
        msg_type = msg.get("type") or "text"
        if theme == "group_messenger":
            char = (
                char_by_id.get(msg.get("senderId"))
                or char_by_name.get(msg.get("senderName"))
                or owner_char
                or (chars[0] if chars else None)
            )
            sender_name = msg.get("senderName") or (char.get("name") if char else f"Nhân vật {idx}")
            role_slug = re.sub(r"[^a-z0-9]+", "_", sender_name.lower()).strip("_") or f"char_{idx}"
        else:
            is_cust = (msg.get("sender") == "customer")
            char = cust_char if is_cust else owner_char
            sender_name = (char.get("name") if char else None) or ("Khách hàng" if is_cust else "Chủ tiệm")
            role_slug = "customer" if is_cust else "owner"

        sfx_key = msg.get("sfx") or ("ting" if msg.get("sender") == "customer" else "pop")
        sfx_file = "sfx_ting.mp3" if sfx_key == "ting" else "sfx_pop.mp3"

        raw_text = msg.get("content") or ""
        if msg_type == "like_sticker" or raw_text.strip() == "👍":
            speak_text = ""
        elif msg_type == "product_card":
            price = msg.get("price") or ""
            speak_text = f"{raw_text}. Giá chỉ {price}." if price else raw_text
        else:
            speak_text = raw_text

        items.append({
            "id": msg.get("id") or f"msg_{idx}",
            "index": idx,
            "frame": f"frame_{idx}.png",
            "sender": sender_name,
            "role": role_slug[:18],
            "type": msg_type,
            "voice": _infer_voice_for_char(char),
            "custom_audio": char.get("customVoiceDataUrl") if char else None,
            "text": speak_text,
            "sfx": sfx_file,
        })

    return items, theme, wallpaper


_EDGE_TTS_TLS_FAILED = False


def synthesize_voice_file(
    text: str,
    voice_name: str,
    out_path: Path,
    rate: str = "+0%",
    custom_audio_data_url: str = None,
    fallback_zip_member: str = None,
):
    """
    Tổng hợp giọng đọc 1.0x chất lượng cao:
    1. Nếu có custom_audio_data_url -> chuyển đổi sang mp3
    2. Kiểm tra cache theo hash(voice + rate + text)
    3. Gọi Edge-TTS (có proxy nếu tồn tại)
    4. Nếu lỗi mạng, thử trích voice mẫu trùng khớp từ zip có sẵn (nếu có) hoặc gTTS
    5. Nếu hoàn toàn offline, tạo audio im lặng ước lượng để pipeline không bao giờ gãy
    """
    global _EDGE_TTS_TLS_FAILED
    out_path.parent.mkdir(parents=True, exist_ok=True)
    TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Custom audio uploaded by user
    if custom_audio_data_url and isinstance(custom_audio_data_url, str) and "base64," in custom_audio_data_url:
        try:
            b64_part = custom_audio_data_url.split("base64,", 1)[1]
            raw_bytes = base64.b64decode(b64_part)
            tmp_in = out_path.with_suffix(".custom_in")
            tmp_in.write_bytes(raw_bytes)
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(tmp_in), "-acodec", "libmp3lame", "-ar", "44100", str(out_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            tmp_in.unlink(missing_ok=True)
            if out_path.exists() and out_path.stat().st_size > 500:
                return out_path
        except Exception as exc:
            print(f"[VoiceEngine] Custom audio fallback: {exc}")

    clean_text = _clean_tts_text(text) or text
    cache_key = hashlib.sha256(f"{voice_name}|{rate}|{clean_text}".encode("utf-8")).hexdigest()[:20]
    cached_file = TTS_CACHE_DIR / f"{cache_key}.mp3"

    if cached_file.exists() and cached_file.stat().st_size > 1000:
        shutil.copy2(cached_file, out_path)
        return out_path

    # 2. Edge-TTS
    import asyncio
    try:
        import edge_tts
        has_edge = True
    except ImportError:
        has_edge = False

    if has_edge and not _EDGE_TTS_TLS_FAILED:
        proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")

        async def _render_edge():
            c = edge_tts.Communicate(clean_text, voice_name, rate=rate, proxy=proxy_url)
            await c.save(str(out_path))

        for attempt in range(1, 3):
            try:
                asyncio.run(_render_edge())
                if out_path.exists() and out_path.stat().st_size > 1000:
                    shutil.copy2(out_path, cached_file)
                    return out_path
            except Exception as exc:
                err_msg = str(exc)
                print(f" [VoiceEngine Retry {attempt}/2] Edge-TTS lỗi: {exc}")
                if "SSLCert" in err_msg or "CERTIFICATE_VERIFY_FAILED" in err_msg:
                    _EDGE_TTS_TLS_FAILED = True
                    break
                time.sleep(0.5)

    # 3. Nếu chạy với kịch bản mặc định mà offline Edge-TTS, ưu tiên lấy giọng Adam/Hoài Mỹ có sẵn trong zip
    if fallback_zip_member:
        for cand_zip in [ASSETS_DIR / f"{DEFAULT_PROJECT_NAME}.zip", WORKSPACE / f"{DEFAULT_PROJECT_NAME}.zip"]:
            if cand_zip.exists():
                try:
                    with zipfile.ZipFile(cand_zip, "r") as zf:
                        for member in zf.namelist():
                            if member.endswith("/" + fallback_zip_member) or member == fallback_zip_member:
                                data = zf.read(member)
                                if len(data) > 1000:
                                    out_path.write_bytes(data)
                                    shutil.copy2(out_path, cached_file)
                                    return out_path
                except Exception:
                    pass

    # 4. Fallback sang gTTS (phân biệt nhẹ cao độ Nam/Nữ nếu có ffmpeg)
    if gTTS is not None:
        try:
            raw_gtts = out_path.with_suffix(".gtts_raw.mp3")
            tts = gTTS(clean_text, lang="vi")
            tts.save(str(raw_gtts))
            if raw_gtts.exists() and raw_gtts.stat().st_size > 800:
                if "NamMinh" in (voice_name or "") and shutil.which("ffmpeg"):
                    try:
                        subprocess.run(
                            [
                                "ffmpeg", "-y", "-i", str(raw_gtts),
                                "-filter:a", "asetrate=44100*0.90,atempo=1.111,aresample=44100",
                                "-c:a", "libmp3lame", "-q:a", "4", str(out_path),
                            ],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=True,
                        )
                        raw_gtts.unlink(missing_ok=True)
                    except Exception:
                        shutil.move(str(raw_gtts), str(out_path))
                else:
                    shutil.move(str(raw_gtts), str(out_path))
                if out_path.exists() and out_path.stat().st_size > 800:
                    shutil.copy2(out_path, cached_file)
                    return out_path
        except Exception as exc:
            print(f" [VoiceEngine Warning] gTTS lỗi: {exc}")

    # 5. Offline silent placeholder
    est_sec = max(1.5, len(clean_text) * 0.075)
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", f"{est_sec:.2f}", "-c:a", "libmp3lame", "-q:a", "4", str(out_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return out_path


def generate_voiceovers(target_assets_dir: Path, dialogue_items: list, is_default_cua_thep: bool = True):
    """Tạo toàn bộ file lồng tiếng 1.0x cho từng câu thoại"""
    print("[VoiceEngine] Đang khởi tạo bộ giọng đọc lồng tiếng chuẩn tốc độ 1.0x...")
    target_assets_dir.mkdir(parents=True, exist_ok=True)

    for item in dialogue_items:
        if not item.get("text"):
            item["voice_file"] = None
            item["voice_dur_us"] = 1200000  # 1.2s cho Sticker Like
            continue

        voice_filename = f"voice_{item['index']}_{item['role']}.mp3"
        out_path = target_assets_dir / voice_filename
        voice_name = item.get("voice") or "vi-VN-NamMinhNeural"
        fallback_member = voice_filename if is_default_cua_thep else None

        synthesize_voice_file(
            item["text"],
            voice_name=voice_name,
            out_path=out_path,
            rate="+0%",
            custom_audio_data_url=item.get("custom_audio"),
            fallback_zip_member=fallback_member,
        )

        dur_us = get_media_duration_us(str(out_path))
        item["voice_file"] = voice_filename
        item["voice_dur_us"] = dur_us
        print(f" - [Voice 1.0x - {item['index']}] {item['sender']} ({voice_name}): {dur_us/1000000:.2f}s -> {voice_filename}")

    print(f"[VoiceEngine] Đã hoàn tất âm thanh cho {len(dialogue_items)} lời thoại!")


def prepare_background_canvas(wallpaper_source: str, target_path: Path, theme: str):
    """Tạo ảnh nền chuẩn 1080x1920 mượt mà, không bị viền đen khi đưa vào CapCut"""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    im = None
    if wallpaper_source and wallpaper_source.startswith("data:image") and "base64," in wallpaper_source:
        try:
            import io
            b64 = wallpaper_source.split("base64,", 1)[1]
            im = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
        except Exception:
            im = None
    elif wallpaper_source:
        src = WORKSPACE / wallpaper_source if not Path(wallpaper_source).is_absolute() else Path(wallpaper_source)
        if src.exists():
            im = Image.open(src).convert("RGB")

    if im is None:
        fallback = ASSETS_DIR / "bg_anime_sky.jpg"
        if fallback.exists():
            im = Image.open(fallback).convert("RGB")

    if im is not None:
        # Center-crop resize to fill 1080x1920
        tw, th = 1080, 1920
        sw, sh = im.size
        scale = max(tw / sw, th / sh)
        nw, nh = int(round(sw * scale)), int(round(sh * scale))
        resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
        left = (nw - tw) // 2
        top = (nh - th) // 2
        cropped = resized.crop((left, top, left + tw, top + th))
        if theme != "group_messenger":
            cropped = cropped.filter(ImageFilter.GaussianBlur(radius=8))
        else:
            cropped = cropped.filter(ImageFilter.GaussianBlur(radius=2))
        overlay = Image.new("RGBA", (tw, th), (10, 15, 28, 55))
        comp = Image.alpha_composite(cropped.convert("RGBA"), overlay).convert("RGB")
        comp.save(target_path, "JPEG", quality=94)
    else:
        bg = Image.new("RGB", (1080, 1920), (15, 23, 42))
        bg.save(target_path, "JPEG", quality=92)


def ensure_node_modules():
    """Đảm bảo puppeteer-core đã được cài đặt trước khi chạy render_frames.js"""
    nm = WORKSPACE / "node_modules" / "puppeteer-core"
    if nm.exists():
        return
    npm_exe = shutil.which("npm")
    if npm_exe and (WORKSPACE / "package.json").exists():
        print("[Setup] Đang cài đặt node_modules (puppeteer-core)...")
        cmd = [npm_exe, "ci" if (WORKSPACE / "package-lock.json").exists() else "install", "--no-audit", "--no-fund"]
        subprocess.check_call(cmd, cwd=str(WORKSPACE))


def ensure_frames_and_assets(
    target_assets_dir: Path,
    dialogue_items: list,
    theme: str,
    wallpaper: str,
    scenario_payload_path: Path = None,
    force_render_frames: bool = False,
):
    """Đảm bảo toàn bộ frames PNG, giọng đọc, SFX và hình nền sẵn sàng"""
    target_assets_dir.mkdir(parents=True, exist_ok=True)
    num_frames = len(dialogue_items) + 1  # frame_0 .. frame_N

    frames_exist = (not force_render_frames) and all(
        (target_assets_dir / f"frame_{i}.png").exists() for i in range(num_frames)
    )
    if not frames_exist:
        ensure_node_modules()
        print("[Generator] Đang render các frame giao diện sắc nét bằng Chromium...")
        cmd = ["node", str(WORKSPACE / "render_frames.js"), str(target_assets_dir)]
        if scenario_payload_path:
            cmd.append(str(scenario_payload_path))
        elif theme == "group_messenger":
            cmd.append("scenario_group_cuathep")
        subprocess.check_call(cmd, cwd=str(WORKSPACE))
    else:
        print("[Generator] Các frames PNG đã có sẵn trong assets.")

    generate_voiceovers(target_assets_dir, dialogue_items, is_default_cua_thep=(scenario_payload_path is None))

    for sfx in ["sfx_ting.mp3", "sfx_pop.mp3"]:
        src = ASSETS_DIR / sfx
        dst = target_assets_dir / sfx
        if src.exists():
            shutil.copy2(src, dst)
        else:
            print(f"[Warning] Thiếu file âm thanh: {src}")

    prepare_background_canvas(wallpaper, target_assets_dir / "bg_canvas_1080x1920.jpg", theme)

    for media in ["bg_anime_sky.jpg", "steel_door_product.jpg", "steel_door_logo.png"]:
        src = ASSETS_DIR / media
        dst = target_assets_dir / media
        if src.exists():
            shutil.copy2(src, dst)

    print(f"[Generator] Chuẩn bị assets hoàn tất trong: {target_assets_dir}")


def calculate_synced_timeline(assets_dir: Path, dialogue_items: list):
    """Tính thời gian biểu khớp microsecond theo độ dài thực tế của giọng đọc"""
    timeline = [
        {
            "index": 0,
            "frame": "frame_0.png",
            "start_us": 0,
            "duration_us": 500000,
            "sfx": None,
            "voice": None,
        }
    ]
    current_time_us = 500000
    pause_between_us = 300000

    for item in dialogue_items:
        if item.get("voice_file"):
            voice_path = str(assets_dir / item["voice_file"])
            voice_dur = get_media_duration_us(voice_path)
            step_duration = voice_dur + pause_between_us
        else:
            voice_dur = 0
            step_duration = int(item.get("voice_dur_us") or 1200000)

        timeline.append({
            "index": item["index"],
            "frame": item["frame"],
            "start_us": current_time_us,
            "duration_us": step_duration,
            "sfx": item.get("sfx"),
            "voice": item.get("voice_file"),
            "voice_dur_us": voice_dur,
        })
        current_time_us += step_duration

    print(f"[TimelineSync] Tổng thời lượng video: {current_time_us / 1000000:.2f} giây.")
    return timeline, current_time_us


def post_process_capcut_draft(proj_dir: Path, project_name: str, total_duration_us: int, target_path: Path = None):
    """
    Chuẩn hóa dự án để tương thích 100% với CapCut Quốc Tế & JianYing trên Windows/Mac.
    target_path: đường dẫn đích thực tế nơi CapCut mở draft (mặc định là proj_dir).
    """
    content_file = proj_dir / "draft_content.json"
    meta_file = proj_dir / "draft_meta_info.json"
    cover_file = proj_dir / "draft_cover.jpg"

    effective_dir = (target_path or proj_dir).resolve()
    effective_posix = effective_dir.as_posix()

    frame1 = proj_dir / "assets" / "frame_1.png"
    bg_file = proj_dir / "assets" / "bg_canvas_1080x1920.jpg"
    cover_src = frame1 if frame1.exists() else bg_file
    if cover_src.exists():
        im = Image.open(cover_src)
        im.convert("RGB").save(cover_file, "JPEG", quality=90)

    with open(content_file, "r", encoding="utf-8") as f:
        content = json.load(f)
    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    draft_id = content.get("id") or str(uuid.uuid4()).upper()
    content["id"] = draft_id
    content["new_version"] = "191.0.0"
    content["last_modified_platform"] = {
        "os": "macos" if sys.platform == "darwin" else "windows",
        "os_version": "10.0.19045",
        "app_id": 359289,
        "app_version": "9.7.1",
    }

    if "canvas_config" in content:
        content["canvas_config"]["ratio"] = "9:16"
        content["canvas_config"]["width"] = 1080
        content["canvas_config"]["height"] = 1920

    now_s = int(time.time())
    now_us = now_s * 1000000

    meta["draft_id"] = draft_id
    meta["draft_name"] = project_name
    meta["tm_duration"] = total_duration_us
    meta["draft_new_version"] = "164.0.0"
    meta["draft_cover"] = f"{effective_posix}/draft_cover.jpg"
    meta["draft_fold_path"] = effective_posix
    meta["draft_root_path"] = effective_dir.parent.as_posix()
    meta["tm_draft_create"] = meta.get("tm_draft_create") or now_us
    meta["tm_draft_modified"] = now_us

    registered_videos = []
    registered_audios = []
    total_assets_size = 0
    assets_sub = proj_dir / "assets"
    if assets_sub.exists():
        total_assets_size = sum(p.stat().st_size for p in assets_sub.rglob("*") if p.is_file())
    meta["draft_timeline_materials_size_"] = total_assets_size

    for vid in content.get("materials", {}).get("videos", []):
        filename = Path(vid.get("path", "")).name
        full_abs_path = f"{effective_posix}/assets/{filename}"
        vid["path"] = full_abs_path
        registered_videos.append({
            "create_time": now_s,
            "duration": vid.get("duration", 10800000000),
            "extra_info": "",
            "file_Path": full_abs_path,
            "height": vid.get("height", 1920),
            "id": vid.get("id") or uuid.uuid4().hex,
            "import_time": now_s,
            "import_time_us": now_us,
            "item_source": 1,
            "md5": "",
            "metainfo_id": "",
            "roughcut_time_range": {"duration": 0, "start": 0},
            "sub_time_range": {"duration": -1, "start": -1},
            "type": 0,
            "width": vid.get("width", 1080),
        })

    for aud in content.get("materials", {}).get("audios", []):
        filename = Path(aud.get("path", "")).name
        full_abs_path = f"{effective_posix}/assets/{filename}"
        aud["path"] = full_abs_path
        registered_audios.append({
            "create_time": now_s,
            "duration": aud.get("duration", 1000000),
            "extra_info": "",
            "file_Path": full_abs_path,
            "height": 0,
            "id": aud.get("id") or uuid.uuid4().hex,
            "import_time": now_s,
            "import_time_us": now_us,
            "item_source": 1,
            "md5": "",
            "metainfo_id": "",
            "roughcut_time_range": {"duration": 0, "start": 0},
            "sub_time_range": {"duration": -1, "start": -1},
            "type": 1,
            "width": 0,
        })

    meta["draft_materials"] = [
        {"type": 0, "value": registered_videos},
        {"type": 1, "value": registered_audios},
        {"type": 2, "value": []},
        {"type": 3, "value": []},
        {"type": 6, "value": []},
        {"type": 7, "value": []},
        {"type": 8, "value": []},
    ]

    with open(content_file, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[Generator] Đã chuẩn hóa manifest & đường dẫn CapCut: {effective_posix}")


def create_portable_installers(proj_dir: Path, project_name: str):
    """
    Tạo bộ cài đặt 1-Click bên trong file .ZIP để người dùng giải nén trên BẤT KỲ máy Windows/Mac nào
    và chỉ cần bấm đúp là dự án tự cài đúng vào CapCut Desktop với đường dẫn chuẩn 100%!
    """
    ps1_content = f"""$ErrorActionPreference = "Stop"
$src = $PSScriptRoot
if (-not $src) {{ $src = (Get-Location).Path }}

$roots = @(
    (Join-Path $env:LOCALAPPDATA 'CapCut\\User Data\\Projects\\com.lveditor.draft'),
    (Join-Path $env:LOCALAPPDATA 'JianyingPro\\User Data\\Projects\\com.lveditor.draft')
)
$targetRoot = $roots | Where-Object {{ Test-Path $_ }} | Select-Object -First 1
if (-not $targetRoot) {{
    $targetRoot = $roots[0]
    New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null
}}

$dest = Join-Path $targetRoot '{project_name}'
if (Test-Path $dest) {{ Remove-Item -Recurse -Force $dest }}
Copy-Item -Recurse -Force $src $dest

Get-ChildItem -Path $dest -Filter 'desktop.ini' -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

$destPosix = $dest -replace '\\\\', '/'
$rootPosix = $targetRoot -replace '\\\\', '/'

foreach ($jf in @('draft_content.json', 'draft_meta_info.json')) {{
    $p = Join-Path $dest $jf
    if (Test-Path $p) {{
        $txt = [System.IO.File]::ReadAllText($p, [System.Text.Encoding]::UTF8)
        $txt = [regex]::Replace($txt, '"(?:[A-Za-z]:|/)[^"\\r\\n]*/assets/([^"]+)"', ('"' + $destPosix + '/assets/$1"'))
        $txt = [regex]::Replace($txt, '"draft_fold_path"\\s*:\\s*"[^"]*"', ('"draft_fold_path": "' + $destPosix + '"'))
        $txt = [regex]::Replace($txt, '"draft_root_path"\\s*:\\s*"[^"]*"', ('"draft_root_path": "' + $rootPosix + '"'))
        $txt = [regex]::Replace($txt, '"draft_cover"\\s*:\\s*"[^"]*"', ('"draft_cover": "' + $destPosix + '/draft_cover.jpg"'))
        [System.IO.File]::WriteAllText($p, $txt, (New-Object System.Text.UTF8Encoding $false))
    }}
}}

$meta = [System.IO.File]::ReadAllText((Join-Path $dest 'draft_meta_info.json'), [System.Text.Encoding]::UTF8) | ConvertFrom-Json
$rootMetaPath = Join-Path $targetRoot 'root_meta_info.json'
if (Test-Path $rootMetaPath) {{
    $rm = [System.IO.File]::ReadAllText($rootMetaPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
    $list = @($rm.all_draft_store | Where-Object {{ $_.draft_name -ne '{project_name}' }})
    $entry = [PSCustomObject]@{{
        draft_name = '{project_name}'
        draft_id = $meta.draft_id
        draft_fold_path = $destPosix
        draft_root_path = $rootPosix
        draft_json_file = ($destPosix + '/draft_content.json')
        draft_cover = ($destPosix + '/draft_cover.jpg')
        draft_new_version = '164.0.0'
        draft_is_invisible = $false
        draft_cloud_last_action_download = $false
        draft_timeline_materials_size_ = [int64]($meta.draft_timeline_materials_size_)
        tm_duration = [int64]($meta.tm_duration)
        tm_draft_create = [int64]($meta.tm_draft_create)
        tm_draft_modified = [int64]($meta.tm_draft_modified)
    }}
    $rm.all_draft_store = @($entry) + $list
    [System.IO.File]::WriteAllText($rootMetaPath, ($rm | ConvertTo-Json -Depth 12), (New-Object System.Text.UTF8Encoding $false))
}}

Write-Host ("[OK] Da cai dat vao CapCut Desktop: " + $dest) -ForegroundColor Green
"""
    (proj_dir / "_install_capcut.ps1").write_text(ps1_content, encoding="utf-8-sig")

    bat_content = f"""@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================================
echo   CAI DAT DU AN CAPCUT: {project_name}
echo ========================================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0_install_capcut.ps1"
if errorlevel 1 (
    echo [LOI] Khong the cai dat tu dong. Kiem tra lai thu muc CapCut hoac quyen truy cap!
) else (
    echo.
    echo Hay mo CapCut Desktop ^(tat mo lai neu dang mo^) va bam Export ^(Ctrl+E^)!
)
pause
"""
    (proj_dir / "CAI_DAT_VAO_CAPCUT.bat").write_text(bat_content, encoding="utf-8")

    mac_cmd = f"""#!/bin/bash
set -e
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
CAPCUT_ROOT="$HOME/Movies/CapCut/User Data/Projects/com.lveditor.draft"
mkdir -p "$CAPCUT_ROOT"
DEST_DIR="$CAPCUT_ROOT/{project_name}"
rm -rf "$DEST_DIR"
cp -R "$SRC_DIR" "$DEST_DIR"
python3 - <<PY
import json, re, time
from pathlib import Path
dest = Path("$DEST_DIR")
dest_p = dest.as_posix()
root_p = Path("$CAPCUT_ROOT").as_posix()
for jf in ("draft_content.json", "draft_meta_info.json"):
    p = dest / jf
    if p.exists():
        txt = p.read_text(encoding="utf-8")
        txt = re.sub(r'"(?:[A-Za-z]:|/)[^"\\r\\n]*/assets/([^"]+)"', f'"{{dest_p}}/assets/\\\\1"', txt)
        p.write_text(txt, encoding="utf-8")
meta_p = dest / "draft_meta_info.json"
if meta_p.exists():
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    meta["draft_fold_path"] = dest_p
    meta["draft_root_path"] = root_p
    meta["draft_cover"] = f"{{dest_p}}/draft_cover.jpg"
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    rm_p = Path("$CAPCUT_ROOT") / "root_meta_info.json"
    if rm_p.exists():
        rm = json.loads(rm_p.read_text(encoding="utf-8"))
        stores = [d for d in rm.get("all_draft_store", []) if d.get("draft_name") != "{project_name}"]
        tmpl = dict(stores[0]) if stores else {{}}
        tmpl.update({{
            "draft_name": "{project_name}",
            "draft_id": meta["draft_id"],
            "draft_fold_path": dest_p,
            "draft_root_path": root_p,
            "draft_json_file": f"{{dest_p}}/draft_content.json",
            "draft_cover": f"{{dest_p}}/draft_cover.jpg",
            "draft_new_version": "164.0.0",
            "draft_is_invisible": False,
            "draft_cloud_last_action_download": False,
            "draft_timeline_materials_size_": meta.get("draft_timeline_materials_size_", 0),
            "tm_duration": meta.get("tm_duration", 0),
            "tm_draft_create": meta.get("tm_draft_create", int(time.time() * 1000000)),
            "tm_draft_modified": int(time.time() * 1000000),
        }})
        rm["all_draft_store"] = [tmpl] + stores
        rm_p.write_text(json.dumps(rm, ensure_ascii=False), encoding="utf-8")
PY
echo "✅ Đã cài đặt thành công vào CapCut Desktop: $DEST_DIR"
"""
    mac_path = proj_dir / "CAI_DAT_VAO_CAPCUT.command"
    mac_path.write_text(mac_cmd, encoding="utf-8")
    try:
        os.chmod(mac_path, 0o755)
    except Exception:
        pass


def create_user_guide(proj_dir: Path, project_name: str, total_duration_s: float):
    """Tạo file hướng dẫn ngắn gọn trong gói zip"""
    guide_text = f"""================================================================================
🎬 HƯỚNG DẪN MỞ DỰ ÁN CAPCUT: {project_name}
Thời lượng: {total_duration_s:.1f} giây • 4 Tracks Sạch Sẽ • Giọng Chuẩn 1.0x
================================================================================

👉 CÁCH NHANH NHẤT (KHUYÊN DÙNG - 1 CLICK):
   1. Giải nén toàn bộ thư mục "{project_name}" ra máy tính.
   2. Mở thư mục vừa giải nén và nhấp đúp chạy file:
      - Windows: CAI_DAT_VAO_CAPCUT.bat
      - macOS:   CAI_DAT_VAO_CAPCUT.command
   3. Mở CapCut Desktop -> Chọn dự án "{project_name}" -> Bấm Export (Ctrl+E)!

👉 LƯU Ý NẾU CHÉP THỦ CÔNG:
   Nếu bạn copy thư mục thủ công vào:
     %LOCALAPPDATA%\\CapCut\\User Data\\Projects\\com.lveditor.draft\\
   Hãy nhớ chạy CAI_DAT_VAO_CAPCUT.bat (hoặc bấm nút Relink Media nếu CapCut hỏi),
   vì CapCut Desktop dùng đường dẫn tuyệt đối theo từng máy tính!
================================================================================
"""
    (proj_dir / "HUONG_DAN_SU_DUNG.txt").write_text(guide_text, encoding="utf-8")


def sync_to_local_capcut(proj_dir: Path, project_name: str, total_dur_us: int):
    """Tự động cài đặt thẳng vào CapCut Desktop nếu có trên Windows hoặc macOS"""
    capcut_roots = []
    if os.name == "nt":
        capcut_roots.append(Path(os.path.expandvars(r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft")))
        capcut_roots.append(Path(os.path.expandvars(r"%LOCALAPPDATA%\JianyingPro\User Data\Projects\com.lveditor.draft")))
    elif sys.platform == "darwin":
        capcut_roots.append(Path.home() / "Movies/CapCut/User Data/Projects/com.lveditor.draft")

    synced_paths = []
    for root_dir in capcut_roots:
        if not root_dir.is_dir():
            continue
        dest_capcut_draft = root_dir / project_name
        if dest_capcut_draft.exists():
            shutil.rmtree(dest_capcut_draft, ignore_errors=True)
        shutil.copytree(proj_dir, dest_capcut_draft, ignore=shutil.ignore_patterns("desktop.ini"))

        # Chuẩn hóa lại toàn bộ đường dẫn trên chính thư mục đích của CapCut Desktop
        post_process_capcut_draft(dest_capcut_draft, project_name, total_dur_us, target_path=dest_capcut_draft)
        dest_meta = json.loads((dest_capcut_draft / "draft_meta_info.json").read_text(encoding="utf-8"))

        root_meta_path = root_dir / "root_meta_info.json"
        if root_meta_path.exists():
            try:
                r_data = json.loads(root_meta_path.read_text(encoding="utf-8"))
                all_drafts = r_data.get("all_draft_store", [])
                template_entry = dict(all_drafts[0]) if all_drafts else {}
                all_drafts = [d for d in all_drafts if d.get("draft_name") != project_name]

                new_entry = {
                    **template_entry,
                    "draft_name": project_name,
                    "draft_id": dest_meta["draft_id"],
                    "draft_fold_path": dest_capcut_draft.as_posix(),
                    "draft_root_path": root_dir.as_posix(),
                    "draft_json_file": (dest_capcut_draft / "draft_content.json").as_posix(),
                    "draft_cover": (dest_capcut_draft / "draft_cover.jpg").as_posix(),
                    "draft_new_version": "164.0.0",
                    "draft_is_invisible": False,
                    "draft_cloud_last_action_download": False,
                    "draft_timeline_materials_size_": dest_meta.get("draft_timeline_materials_size_", 0),
                    "tm_duration": total_dur_us,
                    "tm_draft_create": dest_meta.get("tm_draft_create", int(time.time() * 1000000)),
                    "tm_draft_modified": int(time.time() * 1000000),
                }
                all_drafts.insert(0, new_entry)
                r_data["all_draft_store"] = all_drafts
                root_meta_path.write_text(json.dumps(r_data, ensure_ascii=False), encoding="utf-8")
            except Exception as exc:
                print(f"[Warning] Không thể cập nhật root_meta_info.json: {exc}")

        synced_paths.append(dest_capcut_draft)
        print(f"\n🚀 [CapCut Auto-Sync] Đã cài đặt dự án trực tiếp vào CapCut Desktop: {dest_capcut_draft}")
    return synced_paths


def package_to_zip(proj_dir: Path, zip_dest: Path):
    """Nén toàn bộ thư mục dự án thành file .zip (bỏ qua desktop.ini)"""
    zip_dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"[Generator] Đang nén gói dự án thành: {zip_dest}")
    with zipfile.ZipFile(zip_dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(proj_dir):
            for file in sorted(files):
                if file.lower() == "desktop.ini":
                    continue
                full_path = Path(root) / file
                rel_path = full_path.relative_to(proj_dir.parent)
                zf.write(full_path, rel_path)
    print(f"[Generator] Tạo file Zip thành công! Dung lượng: {zip_dest.stat().st_size / (1024*1024):.2f} MB")


def generate_capcut_draft(
    scenario_data: dict = None,
    characters: list = None,
    project_name: str = DEFAULT_PROJECT_NAME,
    output_root: Path = OUTPUT_DIR,
    zip_path: Path = None,
    sync_to_capcut: bool = True,
    force_render_frames: bool = False,
):
    """
    Hàm API chính: Sinh hoàn chỉnh dự án CapCut 4 Tracks + file .ZIP di động
    từ kịch bản mặc định hoặc kịch bản JSON tùy biến từ Web Studio!
    """
    clean_desktop_ini(WORKSPACE)
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", project_name or DEFAULT_PROJECT_NAME).strip("_") or DEFAULT_PROJECT_NAME

    output_root.mkdir(parents=True, exist_ok=True)
    draft_folder = DraftFolder(str(output_root))
    proj_dir = output_root / safe_name

    print(f"[Generator] Khởi tạo CapCut Draft: {safe_name} (1080x1920, 30fps)")
    script = draft_folder.create_draft(safe_name, 1080, 1920, fps=30, allow_replace=True)

    proj_assets = proj_dir / "assets"
    dialogue_items, theme, wallpaper = normalize_scenario_items(scenario_data, characters)

    payload_tmp = None
    if scenario_data is not None:
        payload_tmp = proj_dir / "_render_payload.json"
        payload_tmp.write_text(
            json.dumps({"scenario": scenario_data, "characters": characters or []}, ensure_ascii=False),
            encoding="utf-8",
        )
        force_render_frames = True

    ensure_frames_and_assets(
        proj_assets,
        dialogue_items=dialogue_items,
        theme=theme,
        wallpaper=wallpaper,
        scenario_payload_path=payload_tmp,
        force_render_frames=force_render_frames,
    )

    if payload_tmp and payload_tmp.exists():
        payload_tmp.unlink(missing_ok=True)

    timeline_steps, total_duration_us = calculate_synced_timeline(proj_assets, dialogue_items)

    script.append_track(TrackSpec(TrackType.video, name="Track_Background"))
    script.append_track(TrackSpec(TrackType.video, name="Track_PhoneScreen"))
    script.append_track(TrackSpec(TrackType.audio, name="Track_AudioSFX"))
    script.append_track(TrackSpec(TrackType.audio, name="Track_Voiceover"))

    # 1. Track 1: Nền 1080x1920 phủ kín khung 9:16
    bg_file = str(proj_assets / "bg_canvas_1080x1920.jpg")
    bg_seg = VideoSegment(bg_file, trange(0, total_duration_us))
    script.add_segment(bg_seg, track="Track_Background")

    # 2. Track 2: Khung màn hình iPhone bo góc (scale ~0.88 để lộ viền nền thẩm mỹ)
    phone_clip = ClipSettings(scale_x=0.88, scale_y=0.88)
    for step in timeline_steps:
        f_path = str(proj_assets / step["frame"])
        if not Path(f_path).exists():
            continue
        seg = VideoSegment(f_path, trange(step["start_us"], step["duration_us"]), clip_settings=phone_clip)
        script.add_segment(seg, track="Track_PhoneScreen")

    # 3. Track 3: SFX Ting & Pop
    for step in timeline_steps:
        sfx_name = step.get("sfx")
        if sfx_name:
            sfx_file = proj_assets / sfx_name
            if sfx_file.exists():
                sfx_mat = AudioMaterial(str(sfx_file))
                dur = min(sfx_mat.duration, step["duration_us"])
                sfx_seg = AudioSegment(sfx_mat, trange(step["start_us"], dur), volume=0.85)
                script.add_segment(sfx_seg, track="Track_AudioSFX")

    # 4. Track 4: Voiceover 1.0x
    for step in timeline_steps:
        voice_file = step.get("voice")
        if voice_file:
            v_path = proj_assets / voice_file
            if v_path.exists():
                v_mat = AudioMaterial(str(v_path))
                v_seg = AudioSegment(v_mat, trange(step["start_us"], v_mat.duration), volume=1.3)
                script.add_segment(v_seg, track="Track_Voiceover")

    script.save()
    post_process_capcut_draft(proj_dir, safe_name, total_duration_us, target_path=proj_dir)

    total_dur_s = total_duration_us / 1000000.0
    create_user_guide(proj_dir, safe_name, total_dur_s)
    create_portable_installers(proj_dir, safe_name)

    final_zip = zip_path or (WORKSPACE / f"{safe_name}.zip")
    package_to_zip(proj_dir, final_zip)

    synced_paths = []
    if sync_to_capcut:
        synced_paths = sync_to_local_capcut(proj_dir, safe_name, total_duration_us)

    return {
        "project_name": safe_name,
        "proj_dir": proj_dir,
        "zip_path": final_zip,
        "duration_s": total_dur_s,
        "synced_paths": synced_paths,
    }


def main():
    parser = argparse.ArgumentParser(description="CapCut Draft Generator - TikTok Chat Studio")
    parser.add_argument("--scenario", help="Đường dẫn tới file JSON kịch bản xuất từ Web Studio")
    parser.add_argument("--name", default=DEFAULT_PROJECT_NAME, help="Tên dự án CapCut")
    parser.add_argument("--no-sync", action="store_true", help="Không tự chép vào thư mục CapCut Desktop")
    parser.add_argument("--force-render", action="store_true", help="Render lại toàn bộ frames PNG từ trình duyệt")
    args = parser.parse_args()

    print("=" * 64)
    print("🎬 CAPCUT DRAFT GENERATOR - TIKTOK CHAT STUDIO PRO")
    print("🔊 TÍCH HỢP GIỌNG ĐỌC CHUẨN 1.0X • 4 TRACKS • 1-CLICK INSTALLER")
    print("=" * 64)

    scenario_data = None
    characters = None
    if args.scenario:
        raw = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "scenario" in raw:
            scenario_data = raw["scenario"]
            characters = raw.get("characters")
        else:
            scenario_data = raw

    result = generate_capcut_draft(
        scenario_data=scenario_data,
        characters=characters,
        project_name=args.name,
        sync_to_capcut=not args.no_sync,
        force_render_frames=args.force_render,
    )

    # Nếu là dự án mặc định thì cập nhật luôn assets/Cua_Thep_TikTok_Luxury.zip cho web static
    if not args.scenario and result["project_name"] == DEFAULT_PROJECT_NAME:
        public_zip = ASSETS_DIR / f"{DEFAULT_PROJECT_NAME}.zip"
        shutil.copy2(result["zip_path"], public_zip)
        print(f"[Generator] Đã cập nhật gói zip công khai: {public_zip}")

    print("\n✅ HOÀN TẤT XUẤT SẮC DỰ ÁN CAPCUT DRAFT!")
    print(f"📁 Thư mục Draft: {result['proj_dir']}")
    print(f"⏱️ Tổng thời lượng: {result['duration_s']:.1f} giây")
    print(f"📦 File Zip di động: {result['zip_path']}")


if __name__ == "__main__":
    main()

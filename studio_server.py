#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
studio_server.py — Local Server cho TikTok Chat Studio Pro
Cung cấp:
- Phục vụ tĩnh Web App (http://localhost:8000) không lỗi CORS
- GET  /api/health        -> Trạng thái server, FFmpeg, TTS, CapCut Desktop
- POST /api/tts           -> Tổng hợp giọng đọc AI (Edge-TTS / gTTS + Cache) trả về .mp3
- POST /api/export-capcut -> Render Frames + Voice 1.0x -> Gói dự án CapCut 4 Tracks (.zip) + Auto-Sync
- POST /api/export-mp4    -> Render trực tiếp Video MP4 1080x1920 H.264/AAC
"""

import os
import re
import sys
import json
import time
import shutil
import socket
import tempfile
import argparse
import threading
import mimetypes
import webbrowser
from pathlib import Path
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from capcut_draft_generator import (
    WORKSPACE,
    ASSETS_DIR,
    TTS_CACHE_DIR,
    DEFAULT_PROJECT_NAME,
    clean_desktop_ini,
    setup_capcut_ffmpeg_path,
    synthesize_voice_file,
    generate_capcut_draft,
    ensure_node_modules,
)
from render_chotcoc_30s_video import render_mp4_video

setup_capcut_ffmpeg_path()

EXPORTS_DIR = WORKSPACE / "studio_exports"
_EXPORT_LOCK = threading.Lock()


def _detect_capcut_dir():
    candidates = []
    if os.name == "nt":
        candidates.append(Path(os.path.expandvars(r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft")))
        candidates.append(Path(os.path.expandvars(r"%LOCALAPPDATA%\JianyingPro\User Data\Projects\com.lveditor.draft")))
    elif sys.platform == "darwin":
        candidates.append(Path.home() / "Movies/CapCut/User Data/Projects/com.lveditor.draft")
    for p in candidates:
        if p.is_dir():
            return str(p)
    return None


def _get_capabilities():
    def _has_mod(name):
        try:
            __import__(name)
            return True
        except Exception:
            return False

    return {
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "ffprobe": bool(shutil.which("ffprobe")),
        "pyJianYingDraft": _has_mod("pyJianYingDraft"),
        "edge_tts": _has_mod("edge_tts"),
        "gTTS": _has_mod("gtts"),
        "node": bool(shutil.which("node")),
        "puppeteer": (WORKSPACE / "node_modules" / "puppeteer-core").is_dir(),
        "capcut_dir": _detect_capcut_dir(),
    }


def _safe_slug(name: str, fallback: str = "Studio_Project") -> str:
    raw = str(name or "").strip()
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", raw).strip("_")
    return (cleaned[:48] or fallback)


class StudioRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WORKSPACE), **kwargs)

    def end_headers(self):
        # Đảm bảo không bị CORS hoặc cache cũ khi chỉnh sửa Web Studio
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if self.path.startswith("/api/") or self.path.endswith((".html", ".js", ".css")) or self.path == "/":
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def guess_type(self, path):
        ctype, encoding = mimetypes.guess_type(path)
        if str(path).endswith(".js"):
            return "application/javascript; charset=utf-8"
        if str(path).endswith(".css"):
            return "text/css; charset=utf-8"
        if str(path).endswith(".html"):
            return "text/html; charset=utf-8"
        return ctype or "application/octet-stream"

    def log_message(self, format, *args):
        # Giảm nhiễu log file tĩnh, chỉ in các API request hoặc lỗi HTTP >= 400
        path = getattr(self, "path", "")
        code = args[1] if len(args) > 1 else ""
        if str(path).startswith("/api/") or (str(code).isdigit() and int(code) >= 400):
            sys.stdout.write(f"[StudioServer] {self.address_string()} - {format % args}\n")
            sys.stdout.flush()

    def _read_json_body(self, max_bytes: int = 64 * 1024 * 1024):
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        if length > max_bytes:
            raise ValueError("Payload vượt quá giới hạn 64MB")
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def _send_file_download(self, file_path: Path, content_type: str, download_name: str, extra_headers: dict = None):
        size = file_path.stat().st_size
        try:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(size))
            self.send_header("Content-Disposition", f'attachment; filename="{download_name}"')
            self.send_header("Access-Control-Expose-Headers", "X-CapCut-Synced, X-CapCut-Duration, Content-Disposition")
            if extra_headers:
                for k, v in extra_headers.items():
                    self.send_header(k, str(v))
            self.end_headers()
            with open(file_path, "rb") as f:
                shutil.copyfileobj(f, self.wfile, length=256 * 1024)
        except BrokenPipeError:
            pass

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self):
        clean_path = self.path.split("?", 1)[0]
        if clean_path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        if clean_path == "/api/health":
            self._send_json({
                "ok": True,
                "service": "TikTok Chat Studio Local Server",
                "workspace": str(WORKSPACE),
                "capabilities": _get_capabilities(),
            })
            return
        super().do_GET()

    def do_POST(self):
        clean_path = self.path.split("?", 1)[0]
        if clean_path == "/api/tts":
            self._handle_tts()
            return
        if clean_path == "/api/export-capcut":
            self._handle_export_capcut()
            return
        if clean_path == "/api/export-mp4":
            self._handle_export_mp4()
            return
        self._send_json({"ok": False, "error": f"Endpoint không tồn tại: {clean_path}"}, status=404)

    def _handle_tts(self):
        try:
            data = self._read_json_body()
            text = str(data.get("text") or "").strip()
            if not text:
                self._send_json({"ok": False, "error": "Thiếu nội dung văn bản (text)"}, status=400)
                return
            voice = str(data.get("voice") or "vi-VN-NamMinhNeural").strip()
            rate = str(data.get("rate") or "+0%").strip()

            EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=str(EXPORTS_DIR), suffix=".mp3", delete=False) as tf:
                tmp_mp3 = Path(tf.name)
            try:
                synthesize_voice_file(text, voice_name=voice, out_path=tmp_mp3, rate=rate)
                raw = tmp_mp3.read_bytes()
            finally:
                tmp_mp3.unlink(missing_ok=True)

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        except Exception as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=500)

    def _handle_export_capcut(self):
        try:
            data = self._read_json_body()
            scenario = data.get("scenario")
            characters = data.get("characters") or []
            if not scenario or not scenario.get("messages"):
                self._send_json({"ok": False, "error": "Kịch bản rỗng, hãy thêm ít nhất 1 tin nhắn!"}, status=400)
                return

            req_name = data.get("projectName") or scenario.get("title") or DEFAULT_PROJECT_NAME
            safe_name = _safe_slug(req_name, fallback=DEFAULT_PROJECT_NAME)
            sync_flag = bool(data.get("syncToCapCut", True))

            EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
            zip_out = EXPORTS_DIR / f"{safe_name}.zip"

            with _EXPORT_LOCK:
                ensure_node_modules()
                result = generate_capcut_draft(
                    scenario_data=scenario,
                    characters=characters,
                    project_name=safe_name,
                    output_root=WORKSPACE / "capcut_projects",
                    zip_path=zip_out,
                    sync_to_capcut=sync_flag,
                    force_render_frames=True,
                )

            synced_count = len(result.get("synced_paths") or [])
            self._send_file_download(
                result["zip_path"],
                content_type="application/zip",
                download_name=f"{result['project_name']}.zip",
                extra_headers={
                    "X-CapCut-Synced": "1" if synced_count > 0 else "0",
                    "X-CapCut-Duration": f"{result['duration_s']:.2f}",
                },
            )
        except Exception as exc:
            import traceback
            traceback.print_exc()
            self._send_json({"ok": False, "error": f"Lỗi tạo gói CapCut: {exc}"}, status=500)

    def _handle_export_mp4(self):
        try:
            if not shutil.which("ffmpeg"):
                self._send_json(
                    {"ok": False, "error": "Chưa tìm thấy FFmpeg trên máy để xuất MP4! Hãy cài FFmpeg hoặc dùng tính năng Xuất Gói CapCut (.ZIP)."},
                    status=500,
                )
                return

            data = self._read_json_body()
            scenario = data.get("scenario")
            characters = data.get("characters") or []
            if not scenario or not scenario.get("messages"):
                self._send_json({"ok": False, "error": "Kịch bản rỗng, hãy thêm ít nhất 1 tin nhắn!"}, status=400)
                return

            req_name = data.get("projectName") or scenario.get("title") or "TikTok_Video"
            safe_name = _safe_slug(req_name, fallback="TikTok_Video")
            EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
            mp4_out = EXPORTS_DIR / f"{safe_name}.mp4"
            work_sub = EXPORTS_DIR / f"_work_{safe_name}"

            with _EXPORT_LOCK:
                ensure_node_modules()
                result = render_mp4_video(
                    scenario_data=scenario,
                    characters=characters,
                    output_mp4=mp4_out,
                    work_dir=work_sub,
                    force_render_frames=True,
                )

            self._send_file_download(
                result["output_mp4"],
                content_type="video/mp4",
                download_name=f"{safe_name}.mp4",
                extra_headers={
                    "X-CapCut-Duration": f"{result['duration_s']:.2f}",
                },
            )
        except Exception as exc:
            import traceback
            traceback.print_exc()
            self._send_json({"ok": False, "error": f"Lỗi render MP4: {exc}"}, status=500)


def _find_available_port(preferred_port: int) -> int:
    for p in range(preferred_port, preferred_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return preferred_port


def run_server(port: int = 8000, open_browser: bool = True):
    clean_desktop_ini(WORKSPACE)
    TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    chosen_port = _find_available_port(port)
    server = ThreadingHTTPServer(("127.0.0.1", chosen_port), StudioRequestHandler)
    url = f"http://localhost:{chosen_port}"

    caps = _get_capabilities()
    print("=" * 68)
    print(f"⚡ TIKTOK CHAT STUDIO SERVER ĐANG CHẠY TẠI: {url}")
    print(f"   • FFmpeg:           {'✅ Sẵn sàng' if caps['ffmpeg'] else '❌ Thiếu'}")
    print(f"   • pyJianYingDraft:  {'✅ Sẵn sàng' if caps['pyJianYingDraft'] else '❌ Thiếu'}")
    print(f"   • Edge-TTS / gTTS:  {'✅ Edge-TTS' if caps['edge_tts'] else '❌'} / {'✅ gTTS' if caps['gTTS'] else '❌'}")
    print(f"   • Chromium Export:  {'✅ Node+Puppeteer' if (caps['node'] and caps['puppeteer']) else '⚠️ Sẽ tự cài khi export'}")
    print(f"   • CapCut Desktop:   {caps['capcut_dir'] or 'ℹ️ Không tìm thấy thư mục local (vẫn tải .ZIP 1-Click bình thường)'}")
    print("   Nhấn Ctrl+C để tắt server.")
    print("=" * 68)

    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[StudioServer] Đang tắt server...")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TikTok Chat Studio Local Backend Server")
    parser.add_argument("--port", type=int, default=8000, help="Cổng HTTP (mặc định 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Không tự mở trình duyệt")
    args = parser.parse_args()
    run_server(port=args.port, open_browser=not args.no_browser)

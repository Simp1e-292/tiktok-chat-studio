#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Client gọn nhẹ (chỉ dùng Python stdlib, không cần cài thêm thư viện)
để kết nối tới CIT Voice Studio Local/LAN REST API (mặc định http://127.0.0.1:8001).
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class CitVoiceError(RuntimeError):
    """Lỗi khi gọi API CIT Voice Studio."""


class CitVoiceClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8001",
        api_key: Optional[str] = None,
        timeout: float = 180.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        if extra:
            headers.update(extra)
        return headers

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[bytes, Dict[str, str]]:
        url = f"{self.base_url}{path}"
        data = None
        extra_headers: Dict[str, str] = {}
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            extra_headers["Content-Type"] = "application/json; charset=utf-8"

        req = urllib.request.Request(
            url=url,
            data=data,
            headers=self._headers(extra_headers),
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as resp:
                body = resp.read()
                resp_headers = {k.lower(): v for k, v in resp.headers.items()}
                return body, resp_headers
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            raise CitVoiceError(f"HTTP {exc.code} {path}: {err_body}") from exc
        except urllib.error.URLError as exc:
            raise CitVoiceError(f"Không kết nối được tới {url}: {exc.reason}") from exc

    def health(self, timeout: float = 5.0) -> Dict[str, Any]:
        body, _ = self._request("GET", "/health", timeout=timeout)
        return json.loads(body.decode("utf-8"))

    def wait_ready(self, timeout_sec: float = 180.0, poll_interval: float = 1.5) -> Dict[str, Any]:
        deadline = time.time() + timeout_sec
        last_err: Optional[str] = None
        while time.time() < deadline:
            try:
                info = self.health(timeout=3.0)
                if info.get("status") == "ok":
                    return info
                last_err = f"status={info.get('status')} ({info.get('message', '')})"
            except Exception as exc:
                last_err = str(exc)
            time.sleep(poll_interval)
        raise CitVoiceError(f"CIT Voice Studio chưa sẵn sàng sau {timeout_sec:.0f}s: {last_err}")

    def list_voices(self) -> List[Dict[str, Any]]:
        body, _ = self._request("GET", "/voices", timeout=15.0)
        return json.loads(body.decode("utf-8"))

    def generate(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        temperature: float = 0.7,
        fmt: str = "wav",
        use_pronunciation_dict: bool = True,
        seed: Optional[int] = None,
        language: Optional[str] = None,
    ) -> Tuple[bytes, Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "text": text,
            "speed": speed,
            "temperature": temperature,
            "format": fmt,
            "use_pronunciation_dict": use_pronunciation_dict,
        }
        if voice_id:
            payload["voice_id"] = voice_id
        if seed is not None:
            payload["seed"] = seed
        if language:
            payload["language"] = language

        t0 = time.perf_counter()
        audio_bytes, headers = self._request("POST", "/api/tts/generate", payload=payload)
        wall_sec = time.perf_counter() - t0

        meta = {
            "content_type": headers.get("content-type", "audio/wav"),
            "duration_seconds": _to_float(headers.get("x-duration-seconds")),
            "elapsed_seconds": _to_float(headers.get("x-elapsed-seconds")) or round(wall_sec, 3),
            "rtf": _to_float(headers.get("x-rtf")),
            "sample_rate": _to_int(headers.get("x-sample-rate")),
            "ai_generated": headers.get("x-ai-generated"),
            "wall_seconds": round(wall_sec, 3),
        }
        return audio_bytes, meta

    def generate_to_file(self, text: str, out_path: Path, **kwargs: Any) -> Dict[str, Any]:
        audio_bytes, meta = self.generate(text=text, **kwargs)
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(audio_bytes)
        meta["path"] = str(out_path)
        meta["bytes"] = len(audio_bytes)
        return meta

    def generate_with_subtitles(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        temperature: float = 0.7,
        fmt: str = "wav",
        use_pronunciation_dict: bool = True,
        seed: Optional[int] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "text": text,
            "speed": speed,
            "temperature": temperature,
            "format": fmt,
            "use_pronunciation_dict": use_pronunciation_dict,
        }
        if voice_id:
            payload["voice_id"] = voice_id
        if seed is not None:
            payload["seed"] = seed
        if language:
            payload["language"] = language

        body, _ = self._request("POST", "/api/tts/generate-with-subtitles", payload=payload)
        data = json.loads(body.decode("utf-8"))
        data["audio_bytes"] = base64.b64decode(data["audio_base64"])
        return data

    def conversation(
        self,
        turns: List[Dict[str, str]],
        silence_duration: float = 0.35,
        speed: float = 1.0,
        temperature: float = 0.7,
        fmt: str = "wav",
        seed: Optional[int] = None,
        language: Optional[str] = None,
    ) -> Tuple[bytes, Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "turns": turns,
            "silence_duration": silence_duration,
            "speed": speed,
            "temperature": temperature,
            "format": fmt,
        }
        if seed is not None:
            payload["seed"] = seed
        if language:
            payload["language"] = language

        t0 = time.perf_counter()
        audio_bytes, headers = self._request("POST", "/api/tts/conversation", payload=payload)
        wall_sec = time.perf_counter() - t0
        meta = {
            "content_type": headers.get("content-type", "audio/wav"),
            "duration_seconds": _to_float(headers.get("x-duration-seconds")),
            "elapsed_seconds": _to_float(headers.get("x-elapsed-seconds")) or round(wall_sec, 3),
            "turns_count": _to_int(headers.get("x-turns-count")),
            "sample_rate": _to_int(headers.get("x-sample-rate")),
            "wall_seconds": round(wall_sec, 3),
        }
        return audio_bytes, meta


def _to_float(val: Optional[str]) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except ValueError:
        return None


def _to_int(val: Optional[str]) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except ValueError:
        return None

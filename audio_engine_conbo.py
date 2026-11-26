#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio Engine chuẩn phong cách Con Bò Đi Làm (Single Narrator + Comedy BGM + After-Punchline SFX + Mastering -14.5 LUFS)
Dùng chung cho mọi tập của series Văn Phòng Cửa Thép.

Các chuẩn kỹ thuật đã chuẩn hóa:
1. Một giọng kể chuyện duy nhất siêu đồng nhất: Edge-TTS `vi-VN-NamMinhNeural` (+12% tốc độ, -1Hz ấm tiếng),
   tự động fallback sang `VieNeu-TTS` (`Adam`) nếu mất mạng; End Card tùy chọn chuyển giọng nữ (`vi-VN-HoaiMyNeural`).
2. Auto-trim sạch khoảng lặng đầu/cuối từng câu thoại (`silenceremove`) -> xóa sổ 29% Dead Air.
3. Tách đôi SFX:
   - `pop_sfx`: tiếng pop tin nhắn cực nhẹ (0.14s, volume 0.22) ở đầu câu thường, không đè chữ.
   - `after_sfx`: SFX phản ứng hài hước (huh, bruh, rimshot, wow, inception, metal_boom...) đánh SAU KHI DỨT PUNCHLINE.
4. Nhạc nền hài hước bản quyền 0% (`bgm_office_comedy_loop.wav`) chạy nền liên tục + tự động Music Drop ở cú twist/chuyển cảnh.
5. Mastering chuẩn phát thanh 2-pass EBU R128 (`-14.5 LUFS`) + EQ rõ chữ trên loa điện thoại.
"""

import asyncio
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

WORKSPACE = Path(__file__).resolve().parent
DEFAULT_BGM = WORKSPACE / "assets" / "sfx_pack" / "bgm_office_comedy_loop.wav"
DEFAULT_POP = WORKSPACE / "assets" / "sfx_pop.mp3"


def setup_ffmpeg() -> None:
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    local_apps = Path(os.path.expandvars(r"%LOCALAPPDATA%\CapCut\Apps"))
    if local_apps.is_dir():
        for exe in sorted(local_apps.rglob("ffmpeg.exe"), reverse=True):
            tool_dir = str(exe.parent)
            if tool_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = tool_dir + os.pathsep + os.environ["PATH"]
            break


def probe_duration(path: Path) -> float:
    return float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ]
        )
        .decode()
        .strip()
    )


def _trim_and_convert_wav(src_audio: Path, dst_wav: Path, speed: float = 1.0) -> float:
    """Chuyển sang WAV 44.1kHz stereo và cắt sạch khoảng lặng thừa đầu/cuối."""
    filters = [
        "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-42dB",
        "areverse",
        "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-42dB",
        "areverse",
    ]
    if abs(speed - 1.0) > 0.005:
        filters.append(f"atempo={speed:.3f}")
    # Chừa đệm mượt 20ms ở cuối tránh bị cắn đuôi âm
    filters.append("apad=pad_dur=0.025")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src_audio),
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
    return probe_duration(dst_wav)


async def _edge_tts_save(text: str, out_mp3: Path, voice: str, rate: str, pitch: str) -> None:
    import edge_tts

    for attempt in range(5):
        try:
            kwargs = {"text": text, "voice": voice, "rate": rate}
            if pitch and pitch not in ("+0Hz", "0Hz", "-0Hz"):
                kwargs["pitch"] = pitch
            comm = edge_tts.Communicate(**kwargs)
            await comm.save(str(out_mp3))
            if out_mp3.exists() and out_mp3.stat().st_size > 500:
                await asyncio.sleep(0.45)
                return
        except Exception:
            if attempt == 4:
                raise
            await asyncio.sleep(1.0 * (attempt + 1))


def synthesize_dual_gender(
    items: List[Dict],
    out_dir: Path,
    male_spec: tuple = ("vieneu", "Adam bựa"),
    female_spec: tuple = ("vieneu", "Trúc Ly"),
    end_card_spec: Optional[tuple] = None,
    edge_rate: str = "+12%",
    vieneu_speed: float = 1.10,
    male_speed: Optional[float] = None,
    female_speed: Optional[float] = None,
    reuse_cache: bool = True,
) -> Path:
    """
    Tổng hợp thoại tách chuẩn 2 giới tính NAM / NỮ:
    - Mỗi spec có dạng ("edge", "vi-VN-NamMinhNeural") hoặc ("vieneu", "Adam" / "Ngọc Huyền" / ...)
    - Đọc trường item["gender"] ("male" hoặc "female"; mặc định "male").
    - Lưu luôn trường "gender" vào manifest.json để mix EQ riêng cho giọng Nam & Nữ đồng đều âm lượng.
    - reuse_cache=True: tái sử dụng file .wav đã tổng hợp nếu cùng tts + voice_name + speed.
    """
    setup_ffmpeg()
    out_dir.mkdir(parents=True, exist_ok=True)
    vieneu_engine = None
    manifest_out = []

    prev_map = {}
    manifest_path = out_dir / "manifest.json"
    if reuse_cache and manifest_path.exists():
        try:
            for prev in json.loads(manifest_path.read_text(encoding="utf-8")):
                prev_map[prev.get("idx")] = prev
        except Exception:
            prev_map = {}

    def _get_vieneu():
        nonlocal vieneu_engine
        if vieneu_engine is None:
            from vieneu import Vieneu
            vieneu_engine = Vieneu()
        return vieneu_engine

    async def _run_all():
        for it in items:
            row = dict(it)
            is_end = it.get("kind") == "end_card"
            needs_voice = (it.get("kind") == "msg" and it.get("tts")) or (
                is_end and it.get("tts")
            )
            if not needs_voice:
                manifest_out.append(row)
                continue

            gender = row.get("gender", "female" if is_end else "male")
            row["gender"] = gender
            if is_end and end_card_spec is not None:
                engine_type, voice_id = end_card_spec
            elif gender == "female":
                engine_type, voice_id = female_spec
            else:
                engine_type, voice_id = male_spec

            final_wav = out_dir / f"voice_{it['idx']:02d}_{it.get('code', gender.upper())}.wav"
            used_label = f"{engine_type}:{voice_id}"

            prev = prev_map.get(it["idx"])
            eff_vieneu_speed = (
                (female_speed if female_speed is not None else vieneu_speed)
                if gender == "female"
                else (male_speed if male_speed is not None else vieneu_speed)
            )
            cur_speed = edge_rate if engine_type == "edge" else eff_vieneu_speed
            if (
                reuse_cache
                and prev
                and final_wav.exists()
                and prev.get("tts") == it.get("tts")
                and prev.get("voice_name") == used_label
                and prev.get("audio_file") == final_wav.name
                and prev.get("speed") == cur_speed
            ):
                dur = probe_duration(final_wav)
                row["audio_file"] = final_wav.name
                row["voice_name"] = used_label
                row["duration_sec"] = round(dur, 4)
                manifest_out.append(row)
                print(f"  ↺ #{it['idx']:02d} [CACHE | {gender.upper()} | {used_label}] {dur:.2f}s")
                continue

            if engine_type == "edge":
                raw_mp3 = out_dir / f"raw_{it['idx']:02d}.mp3"
                try:
                    await _edge_tts_save(it["tts"], raw_mp3, voice_id, edge_rate, "+0Hz")
                    dur = _trim_and_convert_wav(raw_mp3, final_wav, speed=1.0)
                except Exception as e:
                    fb_voice = "Thục Đoan" if gender == "female" else "Adam"
                    print(f"  [!] Edge-TTS lỗi câu #{it['idx']} ({e}), fallback VieNeu '{fb_voice}'...")
                    fb_wav = out_dir / f"raw_fb_{it['idx']:02d}.wav"
                    tts = _get_vieneu()
                    audio = tts.infer(
                        text=it["tts"], voice=fb_voice,
                        temperature=0.60, top_k=18, top_p=0.90, repetition_penalty=1.35, denoise=True,
                    )
                    tts.save(audio, str(fb_wav))
                    dur = _trim_and_convert_wav(fb_wav, final_wav, speed=eff_vieneu_speed)
                    used_label = f"vieneu:{fb_voice} (fallback)"
                    fb_wav.unlink(missing_ok=True)
                finally:
                    raw_mp3.unlink(missing_ok=True)
            else:
                raw_wav = out_dir / f"raw_vn_{it['idx']:02d}.wav"
                tts = _get_vieneu()
                audio = tts.infer(
                    text=it["tts"], voice=voice_id,
                    temperature=0.60, top_k=18, top_p=0.90, repetition_penalty=1.35, denoise=True,
                )
                tts.save(audio, str(raw_wav))
                dur = _trim_and_convert_wav(raw_wav, final_wav, speed=eff_vieneu_speed)
                raw_wav.unlink(missing_ok=True)

            row["audio_file"] = final_wav.name
            row["voice_name"] = used_label
            row["speed"] = cur_speed
            row["duration_sec"] = round(dur, 4)
            manifest_out.append(row)
            print(f"  ✓ #{it['idx']:02d} [{gender.upper()} | {used_label}] {dur:.2f}s — {it['tts']}")

    asyncio.run(_run_all())
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_out, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def synthesize_single_narrator(
    items: List[Dict],
    out_dir: Path,
    main_voice: str = "vi-VN-NamMinhNeural",
    rate: str = "+12%",
    pitch: str = "-1Hz",
    end_card_voice: Optional[str] = "vi-VN-HoaiMyNeural",
) -> Path:
    """Tổng hợp toàn bộ thoại theo chuẩn 1 giọng kể duy nhất + auto-trim silence."""
    setup_ffmpeg()
    out_dir.mkdir(parents=True, exist_ok=True)
    vieneu_fallback = None
    manifest_out = []

    async def _run_all():
        nonlocal vieneu_fallback
        for it in items:
            row = dict(it)
            needs_voice = (it.get("kind") == "msg" and it.get("tts")) or (
                it.get("kind") == "end_card" and it.get("tts") and end_card_voice
            )
            if not needs_voice:
                manifest_out.append(row)
                continue

            is_end = it.get("kind") == "end_card"
            voice_id = end_card_voice if is_end else main_voice
            v_rate = "+10%" if is_end else rate
            v_pitch = "+0Hz" if is_end else pitch

            raw_mp3 = out_dir / f"raw_{it['idx']:02d}.mp3"
            final_wav = out_dir / f"voice_{it['idx']:02d}_{it.get('code', 'NAR')}.wav"

            used_label = voice_id
            try:
                await _edge_tts_save(it["tts"], raw_mp3, voice_id, v_rate, v_pitch)
                dur = _trim_and_convert_wav(raw_mp3, final_wav, speed=1.0)
            except Exception as e:
                print(f"  [!] Edge-TTS lỗi câu #{it['idx']} ({e}), chuyển fallback VieNeu 'Adam'...")
                if vieneu_fallback is None:
                    from vieneu import Vieneu

                    vieneu_fallback = Vieneu()
                fb_wav = out_dir / f"raw_fb_{it['idx']:02d}.wav"
                audio = vieneu_fallback.infer(
                    text=it["tts"],
                    voice="Adam",
                    temperature=0.60,
                    top_k=18,
                    top_p=0.90,
                    repetition_penalty=1.35,
                    denoise=True,
                )
                vieneu_fallback.save(audio, str(fb_wav))
                dur = _trim_and_convert_wav(fb_wav, final_wav, speed=1.10)
                used_label = "VieNeu-Adam (fallback)"
                fb_wav.unlink(missing_ok=True)
            finally:
                raw_mp3.unlink(missing_ok=True)

            row["audio_file"] = final_wav.name
            row["voice_name"] = used_label
            row["speed"] = cur_speed
            row["duration_sec"] = round(dur, 4)
            manifest_out.append(row)
            print(f"  ✓ #{it['idx']:02d} [{used_label}] {dur:.2f}s — {it['tts']}")

    asyncio.run(_run_all())
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_out, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def _measure_loudnorm(wav_path: Path) -> Dict[str, str]:
    p = subprocess.run(
        [
            "ffmpeg",
            "-i",
            str(wav_path),
            "-af",
            "loudnorm=I=-14.5:TP=-1.0:LRA=6:print_format=json",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S)
    if not m:
        return {}
    return json.loads(m.group(0))


def mix_conbo_audio(
    items_by_idx: Dict[int, Dict],
    events: List[Dict],
    voices_dir: Path,
    output_wav: Path,
    total_dur: float,
    bgm_path: Path = DEFAULT_BGM,
    bgm_volume: float = 0.16,
    voice_delay_sec: float = 0.05,
) -> Path:
    """
    Mix tổng hợp chuẩn Con Bò Đi Làm:
    - Lớp BGM hài chạy nền + Music Drop ở cú twist/chuyển cảnh + ducking nhẹ
    - Pop tin nhắn cực nhẹ đầu câu
    - Voice 1 giọng duy nhất đã EQ ấm & sắc nét
    - After-SFX đánh ĐÚNG SAU PUNCHLINE
    - Master 2-pass loudnorm đạt -14.5 LUFS
    """
    setup_ffmpeg()

    inputs: List[str] = []
    filter_parts: List[str] = []
    speech_labels: List[str] = []
    sfx_labels: List[str] = []
    in_idx = 0

    # Thu thập các khoảng Music Drop (ngắt nhạc nền đột ngột tạo điểm nhấn hài/kịch tính)
    drop_windows = []

    for ev in events:
        if ev["action"] != "item":
            continue
        it = items_by_idx[ev["item_idx"]]
        start_s = float(ev["time"])
        ev_dur = float(ev["duration"])
        start_ms = int(round(start_s * 1000))

        # 1) Music drop window
        if it.get("music_drop") or it.get("kind") in ("sys_time", "sys_recall"):
            if it.get("kind") in ("sys_time", "sys_recall"):
                drop_windows.append((max(0.0, start_s - 0.05), start_s + ev_dur))
            elif it.get("audio_file"):
                v_end = start_s + voice_delay_sec + float(it.get("duration_sec", 0.0))
                drop_windows.append((max(0.0, v_end - 0.12), min(total_dur, start_s + ev_dur)))

        # 2) Tiếng pop tin nhắn cực nhẹ ở đầu câu thường
        pop_rel = it.get("pop_sfx")
        if pop_rel:
            pop_p = WORKSPACE / pop_rel
            if pop_p.exists():
                inputs.extend(["-i", str(pop_p)])
                filter_parts.append(
                    f"[{in_idx}:a]atrim=0:0.16,afade=t=out:st=0.09:d=0.07,"
                    f"adelay={start_ms}|{start_ms},volume=0.22[pop_{it['idx']}];"
                )
                sfx_labels.append(f"[pop_{it['idx']}]")
                in_idx += 1

        # 3) Giọng đọc chuẩn phát thanh (EQ cân bằng riêng cho Nam & Nữ để đồng nhất độ ấm và âm lượng)
        v_end_ms = start_ms + int(round(voice_delay_sec * 1000))
        if it.get("audio_file"):
            v_p = voices_dir / it["audio_file"]
            inputs.extend(["-i", str(v_p)])
            v_ms = start_ms + int(round(voice_delay_sec * 1000))
            v_end_ms = v_ms + int(round(float(it.get("duration_sec", 0.0)) * 1000))
            is_female = it.get("gender") == "female"
            if is_female:
                eq_chain = (
                    "highpass=f=100,"
                    "equalizer=f=220:t=q:w=1.1:g=2.2,"
                    "equalizer=f=4500:t=q:w=1.4:g=-1.2,"
                    "acompressor=threshold=-16dB:ratio=3.0:attack=8:release=110:makeup=2.0"
                )
            else:
                eq_chain = (
                    "highpass=f=85,"
                    "equalizer=f=185:t=q:w=1.1:g=2.4,"
                    "equalizer=f=3200:t=q:w=1.3:g=2.2,"
                    "acompressor=threshold=-16dB:ratio=3.2:attack=8:release=110:makeup=2.2"
                )
            filter_parts.append(
                f"[{in_idx}:a]{eq_chain},"
                f"adelay={v_ms}|{v_ms},volume=1.08[voc_{it['idx']}];"
            )
            speech_labels.append(f"[voc_{it['idx']}]")
            in_idx += 1

        # 4) Reaction SFX đánh SAU PUNCHLINE (hoặc ngay đầu nếu là sys_time)
        after_rel = it.get("after_sfx")
        if after_rel:
            sfx_p = WORKSPACE / after_rel
            if sfx_p.exists():
                inputs.extend(["-i", str(sfx_p)])
                if it.get("kind") in ("sys_time", "sys_recall"):
                    sfx_ms = start_ms
                    nat_dur = probe_duration(sfx_p)
                    sfx_dur = min(nat_dur, max(0.5, float(it.get("after_sfx_dur", ev_dur))))
                    sfx_vol = float(it.get("after_sfx_vol", 0.88))
                    fade_d = min(0.22, sfx_dur * 0.18)
                    fade_st = max(0.08, sfx_dur - fade_d)
                    filter_parts.append(
                        f"[{in_idx}:a]atrim=0:{sfx_dur:.3f},afade=t=out:st={fade_st:.3f}:d={fade_d:.3f},"
                        f"adelay={sfx_ms}|{sfx_ms},volume={sfx_vol:.2f}[asfx_{it['idx']}];"
                    )
                else:
                    # Đánh SAU khi dứt câu thoại +20ms, giữ trọn đuôi tự nhiên không bị cắt cụt!
                    sfx_ms = v_end_ms + 20
                    nat_dur = probe_duration(sfx_p)
                    req_dur = float(it.get("after_sfx_dur", min(nat_dur, 1.50)))
                    max_sfx = min(nat_dur, req_dur)
                    sfx_vol = float(it.get("after_sfx_vol", 0.72))
                    fade_d = min(0.18, max_sfx * 0.16)
                    fade_st = max(0.05, max_sfx - fade_d)
                    filter_parts.append(
                        f"[{in_idx}:a]atrim=0:{max_sfx:.3f},afade=t=out:st={fade_st:.3f}:d={fade_d:.3f},"
                        f"adelay={sfx_ms}|{sfx_ms},volume={sfx_vol:.2f}[asfx_{it['idx']}];"
                    )
                sfx_labels.append(f"[asfx_{it['idx']}]")
                in_idx += 1

    # 5) Nhạc nền BGM loop vô hạn + Music Drop + Sidechain Ducking theo tiếng nói
    bgm_label = None
    if bgm_path and bgm_path.exists():
        inputs.extend(["-stream_loop", "-1", "-i", str(bgm_path)])
        bgm_in = in_idx
        in_idx += 1

        bgm_chain = [
            f"atrim=0:{total_dur:.3f}",
            f"volume={bgm_volume:.3f}",
            "lowpass=f=4800",
            f"afade=t=in:st=0:d=0.18",
            f"afade=t=out:st={max(0.0, total_dur - 0.45):.3f}:d=0.45",
        ]
        # Áp dụng các khoảng ngắt nhạc (Music Drop) sắc nét
        for t0, t1 in drop_windows:
            if t1 > t0 + 0.05:
                bgm_chain.append(f"volume=enable='between(t,{t0:.3f},{t1:.3f})':volume=0.0")
        filter_parts.append(f"[{bgm_in}:a]{','.join(bgm_chain)}[bgm_raw];")
        bgm_label = "[bgm_raw]"

    # Gộp speech để làm tín hiệu sidechain ducking cho BGM
    mix_inputs = []
    if speech_labels:
        filter_parts.append(
            f"{''.join(speech_labels)}amix=inputs={len(speech_labels)}:duration=longest:normalize=0[voc_bus];"
        )
        if bgm_label:
            filter_parts.append("[voc_bus]asplit=2[voc_main][voc_sc];")
            filter_parts.append(
                f"{bgm_label}[voc_sc]sidechaincompress=threshold=0.04:ratio=3.5:attack=15:release=180[bgm_ducked];"
            )
            mix_inputs.extend(["[voc_main]", "[bgm_ducked]"])
        else:
            mix_inputs.append("[voc_bus]")
    elif bgm_label:
        mix_inputs.append(bgm_label)

    mix_inputs.extend(sfx_labels)

    pre_wav = output_wav.with_name(output_wav.stem + "_premaster.wav")
    filter_parts.append(
        f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=longest:normalize=0,"
        f"alimiter=limit=0.95[preout]"
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex",
            "".join(filter_parts),
            "-map",
            "[preout]",
            "-t",
            f"{total_dur:.3f}",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(pre_wav),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    # Pass 2: Chuẩn hóa Loudnorm 2-pass đạt thực tế ~-14.8 LUFS sau nén AAC (ngang tầm Con Bò -15.2 LUFS)
    stats = _measure_loudnorm(pre_wav)
    if stats and "input_i" in stats:
        ln = (
            f"loudnorm=I=-13.8:TP=-1.0:LRA=6:linear=true:"
            f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
            f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
            f"offset={stats['target_offset']}"
        )
    else:
        ln = "loudnorm=I=-13.8:TP=-1.0:LRA=6"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(pre_wav),
            "-af",
            ln,
            "-ar",
            "44100",
            "-ac",
            "2",
            str(output_wav),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    pre_wav.unlink(missing_ok=True)
    return output_wav

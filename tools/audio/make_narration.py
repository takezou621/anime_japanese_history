#!/usr/bin/env python3
"""make_narration.py — script.json → VOICEVOX TTS → narration WAV + timing.json

使い方:
    uv run python tools/audio/make_narration.py --episode ep01
    uv run python tools/audio/make_narration.py --script tools/audio/test_script.json --out audio/test

契約: docs/02_DESIGN.md §3 (tools/audio/make_narration.py)
- VOICEVOX HTTP API (127.0.0.1:50021): audio_query → synthesis の 2 段
- speaker UUID は /speakers から動的解決 (voice_style "四国めたん/ノーマル" 等で一致)
- query パラメータ: speedScale/pitch は characters 設定, volumeScale は 1.2 (既定)
- beat に reading があれば text の代わりに TTS 入力に使う
- ギャップ: ビート間 0.6s / シーン間 0.9s / セクション間 1.2s
- VOICEVOX 未起動時は vv-engine/run を自動起動して /version 応答を最大 90 秒待つ
"""
from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path

ENGINE_URL = "http://127.0.0.1:50021"
ENGINE_BIN = "/Applications/VOICEVOX.app/Contents/Resources/vv-engine/run"
ENGINE_WAIT_SEC = 90

BEAT_GAP = 0.6
SCENE_GAP = 0.9
SECTION_GAP = 1.2


# ---------------------------------------------------------------- HTTP helpers
def http_json(path: str, method: str = "GET", payload: dict | None = None,
              timeout: float = 60.0) -> dict:
    url = f"{ENGINE_URL}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode())


def engine_alive(timeout: float = 3.0) -> bool:
    try:
        with urllib.request.urlopen(f"{ENGINE_URL}/version", timeout=timeout):
            return True
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError):
        return False


def ensure_engine(wait_sec: int = ENGINE_WAIT_SEC) -> None:
    """VOICEVOX が生きていれば何もしない。死んでいたら自動起動して待つ。"""
    if engine_alive():
        return
    print(f"[narration] VOICEVOX engine 応答なし → 自動起動: {ENGINE_BIN}")
    proc = subprocess.Popen(
        [ENGINE_BIN, "--host", "127.0.0.1", "--port", "50021", "--use_gpu=false"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    deadline = time.monotonic() + wait_sec
    while time.monotonic() < deadline:
        if engine_alive(timeout=2.0):
            print(f"[narration] VOICEVOX engine 起動完了 (pid={proc.pid})")
            return
        time.sleep(1.5)
    raise RuntimeError(f"VOICEVOX engine が {wait_sec} 秒以内に応答しません")


# ------------------------------------------------------------------- VOICEVOX
def resolve_style_ids(voice_styles: list[str]) -> dict[str, int]:
    """voice_style ("四国めたん/ノーマル") → VOICEVOX style UUID を /speakers から動的解決。"""
    speakers = http_json("/speakers")
    by_name: dict[str, dict[str, int]] = {}
    for sp in speakers:
        by_name[sp["name"]] = {st["name"]: int(st["id"]) for st in sp["styles"]}

    out: dict[str, int] = {}
    for vs in voice_styles:
        if "/" in vs:
            sp_name, st_name = vs.split("/", 1)
        else:
            sp_name, st_name = vs, "ノーマル"
        if sp_name not in by_name:
            raise KeyError(f"VOICEVOX speaker '{sp_name}' が見つかりません")
        styles = by_name[sp_name]
        if st_name not in styles:
            raise KeyError(
                f"VOICEVOX style '{st_name}' が '{sp_name}' に見つかりません "
                f"(available: {list(styles)})")
        out[vs] = styles[st_name]
    return out


def synth_beat(text: str, style_id: int, speed_scale: float, pitch: float,
               volume_scale: float, retries: int = 3) -> bytes:
    """audio_query → synthesis の 2 段で 1 ビート分の WAV bytes を得る。"""
    query_enc = urllib.parse.urlencode({"speaker": style_id, "text": text})
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            query = http_json(f"/audio_query?{query_enc}", method="POST")
            query["speedScale"] = speed_scale
            query["pitch"] = pitch
            query["volumeScale"] = volume_scale
            synth_enc = urllib.parse.urlencode({"speaker": style_id})
            url = f"{ENGINE_URL}/synthesis?{synth_enc}"
            data = json.dumps(query).encode()
            req = urllib.request.Request(url, data=data, method="POST",
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as res:
                return res.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            last_err = e
            print(f"[narration] TTS retry {attempt}/{retries}: {e}")
            time.sleep(1.5 * attempt)
    raise RuntimeError(f"synthesis 失敗 (text={text[:24]!r}): {last_err}")


def wav_duration(wav_bytes: bytes) -> float:
    with wave.open(__import__("io").BytesIO(wav_bytes), "rb") as w:
        return w.getnframes() / float(w.getframerate())


# -------------------------------------------------------------------- timeline
def build_timing(script: dict, beat_meta: list[dict], tail_sec: float) -> dict:
    """beat_meta: [{"scene_id","section","speaker","wav","duration","text"}, ...]
    ギャップ: ビート間 0.6 / シーン間 0.9 / セクション間 1.2 を頭に足して配置。"""
    scenes: list[dict] = []
    sections: dict[str, dict] = {}
    cur = 0.0
    prev_section: str | None = None
    prev_scene_id: str | None = None

    for m in beat_meta:
        if m["scene_id"] != prev_scene_id:
            if prev_section is None:
                pass  # 冒頭はギャップなし
            elif m["section"] != prev_section:
                cur += SECTION_GAP
            else:
                cur += SCENE_GAP
            scene_start = cur
        else:
            scene_start = scenes[-1]["start"]
            cur += BEAT_GAP  # 同一シーン内のビート間

        beat_start = cur
        cur = beat_start + m["duration"]

        if not scenes or scenes[-1]["id"] != m["scene_id"]:
            scenes.append({"id": m["scene_id"], "section": m["section"],
                           "start": round(scene_start, 3), "beats": []})
        scenes[-1]["beats"].append({
            "speaker": m["speaker"],
            "wav": m["wav"],
            "start": round(beat_start, 3),
            "duration": round(m["duration"], 3),
            "text": m["text"],
        })
        prev_section, prev_scene_id = m["section"], m["scene_id"]

    total = cur + tail_sec
    for i, sc in enumerate(scenes):
        sec = sc["section"]
        end = scenes[i + 1]["start"] if i + 1 < len(scenes) else total
        if sec in sections:
            sections[sec]["end"] = end  # 分断されている場合は後続で延長
        else:
            sections[sec] = {"start": sc["start"], "end": end}

    return {
        "episode": script.get("episode", ""),
        "title": script.get("title", ""),
        "gaps": {"beat": BEAT_GAP, "scene": SCENE_GAP, "section": SECTION_GAP,
                 "tail": tail_sec},
        "total_duration": round(total, 3),
        "scenes": scenes,
        "sections": sections,
    }


# ------------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser(description="script.json → narration WAV + timing.json")
    ap.add_argument("--episode", default=None, help="ep01 など。script/out の既定パスに使う")
    ap.add_argument("--script", default=None, help="script.json のパス (既定: content/episodes/<ep>/script.json)")
    ap.add_argument("--out", default=None, help="出力ディレクトリ (既定: audio/<ep>)")
    ap.add_argument("--volume-scale", type=float, default=1.2, help="VOICEVOX volumeScale (既定 1.2)")
    ap.add_argument("--tail", type=float, default=1.0, help="最終ビート後の余白秒 (既定 1.0)")
    ap.add_argument("--force", action="store_true", help="既存 WAV があっても再生成")
    ap.add_argument("--keep-going", action="store_true", help="1 ビート失敗でも続行 (失敗ビートは timing から除外)")
    args = ap.parse_args()

    episode = args.episode
    script_path = Path(args.script) if args.script else (
        Path("content/episodes") / (episode or "ep01") / "script.json")
    if not episode:
        episode = script_path.parent.name
    out_dir = Path(args.out) if args.out else Path("audio") / episode
    nar_dir = out_dir / "narration"
    nar_dir.mkdir(parents=True, exist_ok=True)

    script = json.loads(script_path.read_text())
    characters = {c["id"]: c for c in script.get("characters", [])}
    if not characters:
        raise SystemExit("script.json に characters がありません")

    ensure_engine()
    style_ids = resolve_style_ids(sorted({c["voice_style"] for c in characters.values()}))
    print(f"[narration] style ids: {style_ids}")

    total_chars = 0
    beat_meta: list[dict] = []
    for scene in script["scenes"]:
        sid = scene["id"]
        for bi, beat in enumerate(scene["beats"]):
            char = characters[beat["speaker"]]
            tts_text = beat.get("reading") or beat["text"]
            total_chars += len(tts_text)
            wav_rel = f"narration/{sid}_b{bi:02d}.wav"
            wav_path = out_dir / wav_rel
            if wav_path.exists() and not args.force:
                dur = wav_duration(wav_path.read_bytes())
                print(f"[narration] skip (exists): {wav_rel} {dur:.3f}s")
            else:
                wav_bytes = synth_beat(
                    tts_text, style_ids[char["voice_style"]],
                    speed_scale=float(char.get("speed_scale", 1.0)),
                    pitch=float(char.get("pitch", 0.0)),
                    volume_scale=args.volume_scale)
                wav_path.write_bytes(wav_bytes)
                dur = wav_duration(wav_bytes)
                print(f"[narration] {wav_rel}  {dur:.3f}s  {beat['speaker']}: {tts_text[:32]}")
            beat_meta.append({
                "scene_id": sid, "section": scene["section"], "speaker": beat["speaker"],
                "wav": wav_rel, "duration": dur, "text": beat["text"],
            })

    timing = build_timing(script, beat_meta, tail_sec=args.tail)
    timing_path = out_dir / "timing.json"
    timing_path.write_text(json.dumps(timing, ensure_ascii=False, indent=2) + "\n")

    est = total_chars / 7.5
    print(f"\n[narration] ビート数={len(beat_meta)}  総文字数={total_chars}  "
          f"推定秒数≈{est:.1f}s (7.5字/s)  実音声総尺={timing['total_duration']:.3f}s")
    print(f"[narration] timing.json → {timing_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

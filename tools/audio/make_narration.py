#!/usr/bin/env python3
"""make_narration.py — script.json → VOICEVOX TTS → narration WAV + timing.json

使い方:
    uv run python tools/audio/make_narration.py --episode ep01
    uv run python tools/audio/make_narration.py --script tools/audio/test_script.json --out audio/test

契約: docs/02_DESIGN.md §3 (tools/audio/make_narration.py)
- VOICEVOX HTTP API (127.0.0.1:50021): audio_query → synthesis の 2 段
- speaker UUID は /speakers から動的解決 (voice_style "四国めたん/ノーマル" 等で一致)
- query パラメータ: speedScale/pitch/intonationScale は characters 設定, volumeScale は 1.2 (既定)
- beat に reading があれば text の代わりに TTS 入力に使う
- 発音辞書 (pronunciation_dict.json): 最長一致優先 + 単語境界考慮で TTS 前に置換。
  置換内容は audio/<ep>/pronunciation_log.json に記録。script.json は変更しない。
- キャッシュ: narration_manifest.json に TTS テキスト+辞書ハッシュを記録し,
  テキスト/辞書が変わった WAV は自動で再生成する (--force で全再生成)
- ギャップ: ビート間 0.45s / シーン間 0.7s / セクション間 0.9s / テール 0.7s (CLI で変更可)
- VOICEVOX 未起動時は vv-engine/run を自動起動して /version 応答を最大 90 秒待つ
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
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

BEAT_GAP = 0.45     # ビート間 (lead 調整 2026-11-14: 0.6 → 0.45)
SCENE_GAP = 0.7     # シーン間 (0.9 → 0.7)
SECTION_GAP = 0.9   # セクション間 (1.2 → 0.9)
TAIL_SEC = 0.7      # 最終ビート後の余白 (1.0 → 0.7)

DEFAULT_DICT_PATH = Path(__file__).resolve().parent / "pronunciation_dict.json"
# 漢字相当文字 (境界判定用。ヶ/ノ等の括り文字は含めない → 「賤ヶ岳」等の複合キーが跨げる)
_KANJI_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff々〆]")
# 固有名詞の直後に付いて「名前+接尾」を形成する語 (この場合は部分置換を許可する)
NAME_SUFFIXES = ("軍勢", "軍団", "一族", "一門", "家臣", "軍", "勢", "方",
                 "氏", "党", "家", "殿", "公", "衆", "側")


def load_pronunciation_dict(path: str | None) -> tuple[dict, str | None]:
    """発音辞書を読み込む。戻り値 (辞書, sha256先頭12桁)。辞書がなければ ({}, None)。"""
    p = Path(path) if path else DEFAULT_DICT_PATH
    if not p.exists():
        return {}, None
    raw = p.read_bytes()
    d = json.loads(raw.decode("utf-8"))
    kana = re.compile(r"^[ぁ-ゖー]+$")
    for k, v in d.items():
        if not kana.match(v):
            raise SystemExit(f"pronunciation_dict.json の値がひらがなでありません: {k}={v}")
        if not (_KANJI_RE.search(k) or re.fullmatch(r"[0-9%]+", k)):
            raise SystemExit(f"pronunciation_dict.json のキーに漢字がありません: {k}")
    return d, hashlib.sha256(raw).hexdigest()[:12]


def apply_pronunciation(text: str, pdict: dict) -> tuple[str, list[dict]]:
    """辞書による読み置換。最長一致優先 + 単語境界考慮。
    - 前隣が漢字 → 名前の途中なので置換しない (未知のより長い固有名詞を保護)
    - 後隣が漢字で、その漢字連続が NAME_SUFFIXES に一致 → 「名前+接尾」として許可
    - 辞書値はひらがななので、置換結果が後続キーと再マッチすることはない
    戻り値 (置換後テキスト, 置換リスト [{"from","to"}])"""
    repls: list[dict] = []
    keys = sorted(pdict, key=lambda k: (-len(k), k))
    for key in keys:
        val = pdict[key]
        pos = 0
        while True:
            i = text.find(key, pos)
            if i < 0:
                break
            j = i + len(key)
            prev_k = i > 0 and _KANJI_RE.match(text[i - 1])
            next_k = j < len(text) and _KANJI_RE.match(text[j])
            if prev_k:
                pos = i + 1
                continue
            if next_k:
                m = _KANJI_RE.match(text, j)
                following = text[j: m.end()] if m else ""
                if following not in NAME_SUFFIXES:
                    pos = i + 1
                    continue
            text = text[:i] + val + text[j:]
            repls.append({"from": key, "to": val})
            pos = i + len(val)
    return text, repls


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
               volume_scale: float, intonation_scale: float = 1.0,
               retries: int = 3) -> bytes:
    """audio_query → synthesis の 2 段で 1 ビート分の WAV bytes を得る。"""
    query_enc = urllib.parse.urlencode({"speaker": style_id, "text": text})
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            query = http_json(f"/audio_query?{query_enc}", method="POST")
            query["speedScale"] = speed_scale
            query["pitch"] = pitch
            query["intonationScale"] = intonation_scale
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
def build_timing(script: dict, beat_meta: list[dict], tail_sec: float = TAIL_SEC,
                 beat_gap: float = BEAT_GAP, scene_gap: float = SCENE_GAP,
                 section_gap: float = SECTION_GAP) -> dict:
    """beat_meta: [{"scene_id","section","speaker","wav","duration","text"}, ...]
    ギャップ: ビート間 / シーン間 / セクション間 を頭に足して配置。"""
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
                cur += section_gap
            else:
                cur += scene_gap
            scene_start = cur
        else:
            scene_start = scenes[-1]["start"]
            cur += beat_gap  # 同一シーン内のビート間

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

    total = round(cur + tail_sec, 3)
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
        "gaps": {"beat": beat_gap, "scene": scene_gap, "section": section_gap,
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
    ap.add_argument("--tail", type=float, default=TAIL_SEC, help="最終ビート後の余白秒 (既定 0.7)")
    ap.add_argument("--beat-gap", type=float, default=BEAT_GAP, help="ビート間ギャップ秒 (既定 0.45)")
    ap.add_argument("--scene-gap", type=float, default=SCENE_GAP, help="シーン間ギャップ秒 (既定 0.7)")
    ap.add_argument("--section-gap", type=float, default=SECTION_GAP, help="セクション間ギャップ秒 (既定 0.9)")
    ap.add_argument("--dict", default=None, help="発音辞書 JSON (既定: tools/audio/pronunciation_dict.json)")
    ap.add_argument("--no-dict", action="store_true", help="発音辞書を使わない")
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

    pdict, dict_sha = ({}, None) if args.no_dict else load_pronunciation_dict(args.dict)
    if pdict:
        print(f"[narration] 発音辞書: {len(pdict)}語 (sha256={dict_sha})")
    else:
        print("[narration] 発音辞書: 不使用")

    # 声質設定 (speed/pitch/intonation/volume) のハッシュ — 変わったら全WAV再生成
    voice_params = {
        cid: {
            "speed_scale": float(c.get("speed_scale", 1.0)),
            "pitch": float(c.get("pitch", 0.0)),
            "intonation_scale": float(c.get("intonation_scale",
                                            c.get("intonationScale", 1.0))),
            "volume_scale": args.volume_scale,
        } for cid, c in characters.items()
    }
    voice_sha = hashlib.sha256(
        json.dumps(voice_params, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:12]
    for cid, vp in voice_params.items():
        print(f"[narration] 声質設定 {cid}: {vp}")

    manifest_path = out_dir / "narration_manifest.json"
    manifest: dict = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError:
            manifest = {}

    total_chars = 0
    beat_meta: list[dict] = []
    log_beats: list[dict] = []
    total_repls = 0
    term_counts: dict[str, int] = {}
    for scene in script["scenes"]:
        sid = scene["id"]
        for bi, beat in enumerate(scene["beats"]):
            char = characters[beat["speaker"]]
            base_text = beat["text"]
            raw_tts = beat.get("reading") or base_text
            tts_text, repls = apply_pronunciation(raw_tts, pdict) if pdict else (raw_tts, [])
            total_chars += len(tts_text)
            wav_rel = f"narration/{sid}_b{bi:02d}.wav"
            wav_path = out_dir / wav_rel

            cached = (not args.force and wav_path.exists()
                      and manifest.get("dict_sha256") == dict_sha
                      and manifest.get("voice_sha256") == voice_sha
                      and manifest.get("beats", {}).get(wav_rel, {}).get("tts_text") == tts_text)
            if cached:
                dur = wav_duration(wav_path.read_bytes())
                print(f"[narration] skip (cache): {wav_rel} {dur:.3f}s")
            else:
                wav_bytes = synth_beat(
                    tts_text, style_ids[char["voice_style"]],
                    speed_scale=voice_params[beat["speaker"]]["speed_scale"],
                    pitch=voice_params[beat["speaker"]]["pitch"],
                    intonation_scale=voice_params[beat["speaker"]]["intonation_scale"],
                    volume_scale=voice_params[beat["speaker"]]["volume_scale"])
                wav_path.write_bytes(wav_bytes)
                dur = wav_duration(wav_bytes)
                reason = "regen(dict/text/voice)" if wav_path.exists() and not args.force else "new"
                print(f"[narration] {wav_rel}  {dur:.3f}s  {beat['speaker']}: {tts_text[:32]}"
                      f"{'  [' + reason + ']' if not cached else ''}")
            manifest.setdefault("beats", {})[wav_rel] = {
                "tts_text": tts_text, "speaker": beat["speaker"]}

            log_beats.append({
                "wav": wav_rel,
                "text": base_text,
                "reading": beat.get("reading"),
                "tts_text": tts_text,
                "replacements": repls,
            })
            for r in repls:
                term_counts[r["from"]] = term_counts.get(r["from"], 0) + 1
            total_repls += len(repls)
            beat_meta.append({
                "scene_id": sid, "section": scene["section"], "speaker": beat["speaker"],
                "wav": wav_rel, "duration": dur, "text": base_text,
            })

    timing = build_timing(script, beat_meta, tail_sec=args.tail,
                          beat_gap=args.beat_gap, scene_gap=args.scene_gap,
                          section_gap=args.section_gap)
    timing_path = out_dir / "timing.json"
    timing_path.write_text(json.dumps(timing, ensure_ascii=False, indent=2) + "\n")

    # 発音置換ログ
    log_path = out_dir / "pronunciation_log.json"
    log = {
        "episode": episode,
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "dict_path": str(DEFAULT_DICT_PATH if not args.dict else args.dict),
        "dict_entries": len(pdict) if pdict else 0,
        "dict_sha256": dict_sha,
        "voice_sha256": voice_sha,
        "voice_params": voice_params,
        "summary": {
            "beats": len(log_beats),
            "beats_with_replacements": sum(1 for b in log_beats if b["replacements"]),
            "total_replacements": total_repls,
            "terms": dict(sorted(term_counts.items(), key=lambda kv: -kv[1])),
        },
        "beats": log_beats,
    }
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    manifest["dict_sha256"] = dict_sha
    manifest["voice_sha256"] = voice_sha
    manifest["generated_at"] = log["generated_at"]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    est = total_chars / 7.5
    print(f"\n[narration] ビート数={len(beat_meta)}  総文字数={total_chars}  "
          f"推定秒数≈{est:.1f}s (7.5字/s)  実音声総尺={timing['total_duration']:.3f}s")
    print(f"[narration] 辞書置換: {total_repls}件 "
          f"({log['summary']['beats_with_replacements']}ビート) → {log_path}")
    print(f"[narration] timing.json → {timing_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

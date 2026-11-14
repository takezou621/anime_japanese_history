#!/usr/bin/env python3
"""asr_check.py — mix.wav を faster-whisper で転写し、script.json の beats と正規化突合する QA ツール

使い方:
    uv run --with faster-whisper --with pykakasi --with numpy python tools/qa/asr_check.py --episode ep01
    uv run --with faster-whisper --with pykakasi --with numpy python tools/qa/asr_check.py --all
    # オプション: --model small --threshold 0.95 --device cpu --compute-type int8 --force
    # 依存: ffmpeg (mix.wav の 16kHz mono float32 デコードに使用。PyAV は使わない —
    #       av>=15 では faster-whisper の decode_audio が非互換のため)

出力:
    reports/asr_check_epNN.json  (全体一致率 + ビート別の不一致リスト)

仕様 (T4: ASR突合, 2026-11 lead 指示):
- モデル既定: small (多言語, 日本語対応。初回実行時に HuggingFace からダウンロードされる)
- 正規化: NFKC → アラビア数字を漢数字へ変換 (両側に適用し表記差を吸収)
  → pykakasi で漢字/カタカナをひらがなへ → 記号・空白・残留数字を除去
- 一致率: difflib.SequenceMatcher の ratio (0.0-1.0) を正規化文字列で算出
  - 全体一致率: 台本全ビート連結 vs ASR 全セグメント連結 (時間順)
  - ビート別: ASR セグメントを timing.json のビート区間 (中点で割当) に振り分けて算出
- 閾値: 既定 0.95 (目安運用)。ASR は音声の実読みを転写するため、かな漢字変換差
  (例: よきの/よしのぶ は同音として正規化され区別できない) や固有名詞の表記ゆれは
  正規化比較では検出されない。固有名詞の実読み検証は pronunciation_log 突合・
  VOICEVOX audio_query 解析 (reports/qa_audio_epNN.md) でカバーすること
- 終了コード: 全体一致率が閾値以上なら 0、未満なら 1 (引数エラー等は 2)
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------- 正規化
_DIGITS = "零一二三四五六七八九"


def arabic_to_kanji_num(digits: str) -> str:
    """0-9999 のアラビア数字文字列を漢数字へ変換する (年号等を想定)。

    >>> arabic_to_kanji_num("1185")
    '千百八十五'
    >>> arabic_to_kanji_num("239")
    '二百三十九'
    """
    n = int(digits)
    if n > 9999:
        return digits  # 想定外の長大な数はそのまま (正規化の外れ値)
    if n == 0:
        return _DIGITS[0]
    parts: list[str] = []
    for unit, weight in (("千", 1000), ("百", 100), ("十", 10)):
        d, n = divmod(n, weight)
        if d:
            parts.append(((_DIGITS[d] if d != 1 else "") + unit))
    if n:
        parts.append(_DIGITS[n])
    return "".join(parts)


class Normalizer:
    """台本テキストと ASR 転写を同じ正規化パスに通して比較可能にする。

    pykakasi が使えない環境では kanji→kana を行わないフォールバック正規化
    (かな漢字表記差に弱い) となり、results に `normalizer: "fallback"` を記録する。
    """

    def __init__(self) -> None:
        self.mode = "pykakasi"
        self._conv = None
        try:
            import pykakasi

            self._conv = pykakasi.kakasi()
        except ImportError:
            self.mode = "fallback"

    def text(self, raw: str) -> str:
        s = unicodedata.normalize("NFKC", raw)
        # アラビア数字 → 漢数字 (両側に同じ変換を適用して年号等の表記差を吸収)
        s = re.sub(r"\d+", lambda m: arabic_to_kanji_num(m.group()), s)
        if self._conv is not None:
            s = "".join(t["hira"] for t in self._conv.convert(s))
        # ひらがな・長音・ラテン文字以外 (記号, 空白, 残留数字) を除去
        return re.sub(r"[^ぁ-ゖーa-zA-Z]", "", s)


# ---------------------------------------------------------------- 入力読込
def load_beats(root: Path, episode: str) -> list[dict]:
    """script.json (正規テキスト) と timing.json (グローバル時刻) を突合してビート列を作る。"""
    script = json.loads((root / f"content/episodes/{episode}/script.json").read_text())
    timing = json.loads((root / f"audio/{episode}/timing.json").read_text())
    sb = [(sc["id"], bi, b["text"]) for sc in script["scenes"] for bi, b in enumerate(sc["beats"])]
    tb = [(sc["id"], bi, b) for sc in timing["scenes"] for bi, b in enumerate(sc["beats"])]
    if len(sb) != len(tb):
        raise SystemExit(f"{episode}: script beats={len(sb)} と timing beats={len(tb)} が不一致です")
    beats = []
    for (sid_s, bi_s, text), (sid_t, bi_t, t) in zip(sb, tb):
        if (sid_s, bi_s) != (sid_t, bi_t):
            raise SystemExit(f"{episode}: ビートID不整合 script={sid_s}_b{bi_s:02d} timing={sid_t}_b{bi_t:02d}")
        beats.append({"beat_id": f"{sid_s}_b{bi_t:02d}", "start": float(t["start"]),
                      "duration": float(t["duration"]), "text": text})
    return beats


def assign_segments(beats: list[dict], segments: list[dict], total: float) -> list[str]:
    """ASR セグメントをビート区間へ割当てる。区間 = ビート開始〜次ビート開始 (最終は total)。

    セグメントの中点がどの区間に属するかで 1 対 1 割当する (重複計上を避ける)。
    """
    bounds = [b["start"] for b in beats] + [max(total, beats[-1]["start"] + beats[-1]["duration"])]
    assigned: list[str] = [[] for _ in beats]
    for seg in segments:
        mid = (seg["start"] + seg["end"]) / 2.0
        for i in range(len(beats)):
            if bounds[i] <= mid < bounds[i + 1]:
                assigned[i].append(seg["text"])
                break
    return ["".join(texts) for texts in assigned]


def ratio(a: str, b: str) -> float | None:
    """正規化文字列間の類似度 (0.0-1.0)。両側が空の場合は比較不能 (None)。"""
    if not a and not b:
        return None
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


# ---------------------------------------------------------------- 転写
def decode_ffmpeg(mix: Path, sr: int = 16000) -> "np.ndarray":
    """mix.wav を ffmpeg で 16kHz mono float32 (Whisper 入力形式) にデコードする。

    faster-whisper 内蔵の decode_audio は PyAV を経由するが av>=15 で非互換のため
    ffmpeg 直デコードとする (リポジトリ標準の外部ツール)。
    """
    import numpy as np

    cmd = ["ffmpeg", "-v", "error", "-i", str(mix), "-ar", str(sr), "-ac", "1",
           "-f", "f32le", "-"]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"ffmpeg デコード失敗 ({mix}): {p.stderr.decode(errors='replace')[-400:]}")
    audio = np.frombuffer(p.stdout, dtype=np.float32)
    if audio.size == 0:
        raise SystemExit(f"ffmpeg デコード結果が空です: {mix}")
    return audio


def transcribe(mix: Path, model_size: str, device: str, compute_type: str) -> tuple[list[dict], float]:
    """mix.wav を全文転写し [{start, end, text}] と音声尺 (秒) を返す。"""
    import numpy as np
    from faster_whisper import WhisperModel

    audio = decode_ffmpeg(mix)
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    seg_iter, info = model.transcribe(np.asarray(audio), language="ja", vad_filter=True,
                                      vad_parameters={"min_silence_duration_ms": 300},
                                      condition_on_previous_text=False)
    segments = [{"start": float(s.start), "end": float(s.end), "text": s.text.strip()}
                for s in seg_iter]
    return segments, float(info.duration)


# ---------------------------------------------------------------- 本体
def run_episode(root: Path, episode: str, args: argparse.Namespace, norm: Normalizer) -> Path:
    mix = root / f"audio/{episode}/mix.wav"
    if not mix.exists():
        raise SystemExit(f"mix.wav がありません: {mix}")
    out_path = root / args.out_dir / f"asr_check_{episode}.json"
    if out_path.exists() and not args.force:
        print(f"[asr] skip (出力済み): {out_path} (--force で上書き)")
        return out_path

    beats = load_beats(root, episode)
    t0 = time.monotonic()
    segments, audio_dur = transcribe(mix, args.model, args.device, args.compute_type)
    elapsed = time.monotonic() - t0
    print(f"[asr] {episode}: {audio_dur:.1f}s 音声を {elapsed:.1f}s で転写 (segments={len(segments)})")

    assigned = assign_segments(beats, segments, audio_dur)
    script_all = norm.text("".join(b["text"] for b in beats))
    asr_all = norm.text("".join(assigned))
    overall = ratio(script_all, asr_all)

    beat_rows = []
    for b, asr_text in zip(beats, assigned):
        exp_n, asr_n = norm.text(b["text"]), norm.text(asr_text)
        r = ratio(exp_n, asr_n)
        beat_rows.append({
            "beat_id": b["beat_id"], "start": round(b["start"], 3),
            "expected": b["text"], "asr": asr_text,
            "similarity": None if r is None else round(r, 4),
            "ok": None if r is None else r >= args.threshold,
        })
    n_pass = sum(1 for r in beat_rows if r["ok"] is True)
    n_fail = sum(1 for r in beat_rows if r["ok"] is False)
    n_na = sum(1 for r in beat_rows if r["ok"] is None)
    overall_pass = overall is not None and overall >= args.threshold

    result = {
        "episode": episode,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": args.model, "device": args.device, "compute_type": args.compute_type,
        "vad_filter": True, "normalizer": norm.mode,
        "audio_duration_sec": round(audio_dur, 3),
        "asr_segments": len(segments),
        "beats": len(beat_rows),
        "threshold": args.threshold,
        "overall_similarity": None if overall is None else round(overall, 4),
        "overall_pass": overall_pass,
        "beat_pass": n_pass, "beat_fail": n_fail, "beat_na": n_na,
        "beats_detail": beat_rows,
        "note": ("ASR突合は音声と台本の一致率の目安。固有名詞の実読み検証は "
                 "pronunciation_log 突合 (reports/qa_audio_epNN.md) でカバーすること"),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    print(f"[asr] {episode}: 全体一致率={result['overall_similarity']} "
          f"(閾値 {args.threshold}) ビート OK={n_pass} NG={n_fail} N/A={n_na} → {out_path}")
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(description="mix.wav ASR転写 ↔ script.json beats 突合")
    ap.add_argument("--episode", default=None, help="ep01 など。--all と排他")
    ap.add_argument("--all", action="store_true", help="ep01-ep10 を連続実行")
    ap.add_argument("--model", default="small", help="faster-whisper モデル名 (既定 small)")
    ap.add_argument("--device", default="cpu", help="cpu / auto (既定 cpu)")
    ap.add_argument("--compute-type", default="int8", help="int8 / float16 等 (既定 int8)")
    ap.add_argument("--threshold", type=float, default=0.95, help="合格閾値 (既定 0.95)")
    ap.add_argument("--out-dir", default="reports", help="出力ディレクトリ (既定 reports)")
    ap.add_argument("--root", default=".", help="リポジトリルート (既定 カレント)")
    ap.add_argument("--force", action="store_true", help="出力済みでも再実行する")
    args = ap.parse_args()

    episodes = [f"ep{i:02d}" for i in range(1, 11)] if args.all else [args.episode]
    if bool(args.all) == bool(args.episode):
        ap.error("--episode epNN か --all のどちらか一方を指定してください")
    root = Path(args.root).resolve()
    norm = Normalizer()
    if norm.mode == "fallback":
        print("[asr] 警告: pykakasi が無いため kanji→kana 正規化なし (fallback) — 一致率が低く出ます")

    exit_code = 0
    for ep in episodes:
        try:
            run_episode(root, ep, args, norm)
        except SystemExit as e:
            print(f"[asr] {ep}: {e}", file=sys.stderr)
            exit_code = 2
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""asr_check.py — mix.wav を faster-whisper で転写し、script.json の beats と正規化突合する QA ツール

使い方:
    uv run --with faster-whisper --with pykakasi --with numpy python tools/qa/asr_check.py --episode ep01
    uv run --with faster-whisper --with pykakasi --with numpy python tools/qa/asr_check.py --all
    # オプション: --model small --threshold 0.70 --review-threshold 0.6 --device cpu --compute-type int8 --force
    # 依存: ffmpeg (mix.wav の 16kHz mono float32 デコードに使用。PyAV は使わない —
    #       av>=15 では faster-whisper の decode_audio が非互換のため)

出力:
    reports/asr_check_epNN.json  (全体一致率 + ビート別の不一致リスト + 要確認リスト)

仕様 (T4: ASR突合, 2026-11 lead 指示。閾値運用は 2026-11-15 lead 承認版):
- モデル既定: small (多言語, 日本語対応。初回実行時に HuggingFace からダウンロードされる)
- 正規化: NFKC → アラビア数字を漢数字へ変換 (両側に適用し表記差を吸収)
  → pykakasi で漢字/カタカナをひらがなへ → 記号・空白・残留数字を除去
- 一致率: difflib.SequenceMatcher の ratio (0.0-1.0) を正規化文字列で算出
  - 全体一致率: 台本全ビート連結 vs ASR 全セグメント連結 (時間順)
  - ビート別: ASR セグメントを timing.json のビート区間に重なり時間比例で分割割当
- 比較元テキスト: script.json の TTS 入力 (beat.reading があればそれ, 無ければ text)。
  音声は reading 指定の読みで発話されるため、漢字からの pykakasi 既定読みと
  乖離する固有名詞 (中大兄皇子=なかのおおえ 等) でも台本側を正しい読みで比較する
- 閾値運用 (2026-11-15 lead 承認):
  - 全体一致率ゲート: 既定 0.70 (回帰検知用途 — 音声の入れ替わり/欠落/誤レンダリング検出)。
    未達時は終了コード 1
  - ビート別判定 (ok / beat_pass / beat_fail / review_list) は --review-threshold
    (既定 0.6) 基準に統一。0.6 未満のビートを results.review_list に「要確認リスト」
    として出力する
  - ep01 実測ベースライン: small で 0.768 / medium で 0.803。キャラ語尾 (〜のだ) や
    固有名詞の ASR 誤変換 (氷河→評価 等) が常時発生するため 0.95 は達成不可能
  - 固有名詞の正確性は pronunciation_log 突合 (audio) + 検証済み辞書で担保する
    (ASR一致率と役割分担)。かな漢字変換差 (よきの/よしのぶ 等の同音異表記) は
    正規化比較では検出されない
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
def load_pronunciation(root: Path, dict_path: str | None, no_dict: bool) -> tuple[dict, str | None, object]:
    """make_narration.py の発音辞書ローダと置換関数を取得する (ロジック再利用)。

    戻り値 (pdict, dict_sha, apply_fn)。辞書が無い/読めない場合は空辞書で縮退し、
    ASR突合は継続する (audio pipeline が実際に使った辞書と不一致になる可能性は
    results.dict_sha で判別できる)。
    """
    if no_dict:
        return {}, None, None
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "audio"))
        from make_narration import DEFAULT_DICT_PATH, apply_pronunciation, load_pronunciation_dict

        path = dict_path or str(root / DEFAULT_DICT_PATH)
        if not Path(path).exists():
            print(f"[asr] 警告: 発音辞書がありません: {path} (置換なしで継続)")
            return {}, None, None
        pdict, sha = load_pronunciation_dict(path)
        return pdict, sha, apply_pronunciation
    except ImportError as e:
        print(f"[asr] 警告: make_narration を import できず辞書置換をスキップ: {e}")
        return {}, None, None


def load_beats(root: Path, episode: str, pdict: dict, apply_fn) -> list[dict]:
    """script.json と timing.json を突合してビート列を作る。

    比較元テキストは実際の TTS 入力: beat.reading (あれば) + 発音辞書置換
    (make_narration.apply_pronunciation と同一ロジック) を適用したもの。
    音声は reading 指定・辞書指定の読みで発話されるため、漢字表記からの
    pykakasi 既定読みと乖離する固有名詞 (中大兄皇子=なかのおおえ 等) では
    text 直接比較だと正規化文字列が不一致になる。
    """
    script = json.loads((root / f"content/episodes/{episode}/script.json").read_text())
    timing = json.loads((root / f"audio/{episode}/timing.json").read_text())
    sb = [(sc["id"], bi, b.get("reading") or b["text"], b["text"])
          for sc in script["scenes"] for bi, b in enumerate(sc["beats"])]
    tb = [(sc["id"], bi, b) for sc in timing["scenes"] for bi, b in enumerate(sc["beats"])]
    if len(sb) != len(tb):
        raise SystemExit(f"{episode}: script beats={len(sb)} と timing beats={len(tb)} が不一致です")
    beats = []
    for (sid_s, bi_s, raw_tts, display), (sid_t, bi_t, t) in zip(sb, tb):
        if (sid_s, bi_s) != (sid_t, bi_t):
            raise SystemExit(f"{episode}: ビートID不整合 script={sid_s}_b{bi_s:02d} timing={sid_t}_b{bi_t:02d}")
        tts_text = raw_tts
        if pdict:
            tts_text, _repls = apply_fn(raw_tts, pdict)
        beats.append({"beat_id": f"{sid_s}_b{bi_t:02d}", "start": float(t["start"]),
                      "duration": float(t["duration"]), "tts_text": tts_text, "text": display})
    return beats


def assign_segments(beats: list[dict], segments: list[dict], total: float) -> list[str]:
    """ASR セグメントをビート区間へ割当てる。区間 = ビート開始〜次ビート開始 (最終は total)。

    セグメントが複数ビートにまたがる場合は、重なり時間の比率に従ってテキストを
    比例分割する (セグメント中点割当だと境界ビートが空/混入するため)。
    """
    bounds = [b["start"] for b in beats] + [max(total, beats[-1]["start"] + beats[-1]["duration"])]
    assigned: list[str] = [[] for _ in beats]
    for seg in segments:
        s, e, raw = seg["start"], seg["end"], seg["text"]
        text = re.sub(r"\s+", "", raw)
        if not text:
            continue
        overlaps = []
        for i in range(len(beats)):
            ov = min(e, bounds[i + 1]) - max(s, bounds[i])
            if ov > 0.05:  # 50ms 未満の接触はノイズとして無視
                overlaps.append((i, ov))
        if not overlaps:
            continue
        total_ov = sum(ov for _, ov in overlaps)
        consumed = 0
        for k, (i, ov) in enumerate(overlaps):
            if k == len(overlaps) - 1:
                take = len(text) - consumed  # 最後のビートに残りを全て割当
            else:
                take = int(round(len(text) * (ov / total_ov)))
            assigned[i].append(text[consumed:consumed + take])
            consumed += take
    return ["".join(t) for t in assigned]


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
def run_episode(root: Path, episode: str, args: argparse.Namespace, norm: Normalizer,
                pdict: dict, apply_fn, dict_sha: str | None) -> dict:
    """1 エピソード分を処理し results dict を返す (main で overall_pass を参照)。"""
    mix = root / f"audio/{episode}/mix.wav"
    if not mix.exists():
        raise SystemExit(f"mix.wav がありません: {mix}")
    out_path = root / args.out_dir / f"asr_check_{episode}.json"
    if out_path.exists() and not args.force:
        # スキップ時も既存レポートの overall_pass を引き継ぐ (失敗レポートの
        # 再実行でゲートを回避させないため)。読めない場合は未達扱い。
        print(f"[asr] skip (出力済み): {out_path} (--force で上書き)")
        try:
            prev = json.loads(out_path.read_text())
            overall_pass = bool(isinstance(prev, dict) and prev.get("overall_pass", False))
        except (OSError, json.JSONDecodeError):
            overall_pass = False
        return {"overall_pass": overall_pass, "skipped": True, "out_path": str(out_path)}

    beats = load_beats(root, episode, pdict, apply_fn)

    t0 = time.monotonic()
    segments, audio_dur = transcribe(mix, args.model, args.device, args.compute_type)
    elapsed = time.monotonic() - t0
    print(f"[asr] {episode}: {audio_dur:.1f}s 音声を {elapsed:.1f}s で転写 (segments={len(segments)})")

    assigned = assign_segments(beats, segments, audio_dur)
    script_all = norm.text("".join(b["tts_text"] for b in beats))
    asr_all = norm.text("".join(assigned))
    overall = ratio(script_all, asr_all)

    # ビート別 ok / review_list は丸め前の実値 r で判定する (丸め誤差で閾値直下を
    # 取りこぼさない)。表示用 similarity のみ round する。
    beat_rows = []
    review_list = []
    for b, asr_text in zip(beats, assigned):
        exp_n, asr_n = norm.text(b["tts_text"]), norm.text(asr_text)
        r = ratio(exp_n, asr_n)
        if r is not None and r < args.review_threshold:
            review_list.append(b["beat_id"])
        beat_rows.append({
            "beat_id": b["beat_id"], "start": round(b["start"], 3),
            "expected": b["text"], "asr": asr_text,
            "similarity": None if r is None else round(r, 4),
            "ok": None if r is None else r >= args.review_threshold,
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
        "review_threshold": args.review_threshold,
        "dict_sha": dict_sha,
        "overall_similarity": None if overall is None else round(overall, 4),
        "overall_pass": overall_pass,
        "beat_pass": n_pass, "beat_fail": n_fail, "beat_na": n_na,
        "review_list": review_list,
        "beats_detail": beat_rows,
        "note": (f"ASR突合は音声と台本の一致率の目安。全体ゲート (threshold={args.threshold:g}) は回帰検知用途、"
                 f"ビート別 ok / review_list は review_threshold={args.review_threshold:g} を要確認基準とする。"
                 "固有名詞の実読み検証は pronunciation_log 突合 (reports/qa_audio_epNN.md) でカバーすること"),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    print(f"[asr] {episode}: 全体一致率={result['overall_similarity']} "
          f"(ゲート {args.threshold}) ビート OK={n_pass} 要確認={len(review_list)} N/A={n_na} → {out_path}")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="mix.wav ASR転写 ↔ script.json beats 突合")
    ap.add_argument("--episode", default=None, help="ep01 など。--all と排他")
    ap.add_argument("--all", action="store_true", help="ep01-ep10 を連続実行")
    ap.add_argument("--model", default="small", help="faster-whisper モデル名 (既定 small)")
    ap.add_argument("--device", default="cpu", help="cpu / auto (既定 cpu)")
    ap.add_argument("--compute-type", default="int8", help="int8 / float16 等 (既定 int8)")
    ap.add_argument("--threshold", type=float, default=0.70,
                    help="全体一致率のゲート (既定 0.70。回帰検知用途 — 2026-11-15 lead 承認)")
    ap.add_argument("--review-threshold", type=float, default=0.6,
                    help="ビート別要確認リストの閾値 (既定 0.6)")
    ap.add_argument("--dict", default=None,
                    help="発音辞書 JSON (既定: tools/audio/pronunciation_dict.json — make_narration と同一)")
    ap.add_argument("--no-dict", action="store_true", help="発音辞書置換を無効化")
    ap.add_argument("--out-dir", default="reports", help="出力ディレクトリ (既定 reports)")
    ap.add_argument("--root", default=".", help="リポジトリルート (既定 カレント)")
    ap.add_argument("--force", action="store_true", help="出力済みでも再実行する")
    args = ap.parse_args()

    episodes = [f"ep{i:02d}" for i in range(1, 11)] if args.all else [args.episode]
    if bool(args.all) == bool(args.episode):
        ap.error("--episode epNN か --all のどちらか一方を指定してください")
    root = Path(args.root).resolve()
    pdict, dict_sha, apply_fn = load_pronunciation(root, args.dict, args.no_dict)
    if pdict:
        print(f"[asr] 発音辞書: {len(pdict)} 語 (sha256[:12]={dict_sha})")
    norm = Normalizer()
    if norm.mode == "fallback":
        print("[asr] 警告: pykakasi が無いため kanji→kana 正規化なし (fallback) — 一致率が低く出ます")

    # 終了コード: どれか 1 話でも全体ゲート未達なら 1、入力エラーは 2、全て達成で 0
    exit_code = 0
    for ep in episodes:
        try:
            result = run_episode(root, ep, args, norm, pdict, apply_fn, dict_sha)
            if not result.get("overall_pass", False) and not result.get("skipped"):
                exit_code = 1
        except SystemExit as e:
            print(f"[asr] {ep}: {e}", file=sys.stderr)
            exit_code = 2
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""make_mix.py — narration WAV 列 + BGM → フル尺ミックス (loudnorm -14 LUFS)

使い方:
    uv run python tools/audio/make_mix.py --episode ep01

処理:
1. timing.json の通りに narration wav を adelay で 48kHz ナレトラックへ配置
2. BGM は簡易エンベロープ: ナレ区間 -18dB / 無音区間 -8dB (0.35s リニアランプ)
3. amix → loudnorm=I=-14:TP=-1.5:LRA=11 → audio/<ep>/mix.wav (48kHz 16bit)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DUCK_DB = -18.0   # ナレーション区間の BGM ゲイン
QUIET_DB = -8.0   # 無音区間の BGM ゲイン
RAMP = 0.35       # エンベロープのランプ秒
GUARD = 0.18      # ナレ区間の前後マージン秒
SR = 48000


def merge_intervals(intervals: list[tuple[float, float]],
                    min_gap: float) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for s, e in sorted(intervals):
        if out and s - out[-1][1] < min_gap:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def build_envelope_expr(intervals: list[tuple[float, float]],
                        duck_db: float, quiet_db: float,
                        ramp: float, guard: float) -> str:
    """BGM ゲイン式: quiet + (duck-quiet)*active(t)。active は各ナレ区間の
    リニアランプ項の和 (0..1 にクランプ)。eval=frame で t を使える。"""
    depth = duck_db - quiet_db  # 負の値 (-10)
    terms = []
    for s, e in intervals:
        a = max(0.0, s - guard)
        b = e + guard
        terms.append(
            f"min(1\\,max(0\\,(t-{a:.3f})/{ramp:.3f}))"
            f"-min(1\\,max(0\\,(t-{b:.3f})/{ramp:.3f}))"
        )
    active = "min(1\\,max(0\\," + "+".join(terms) + "))" if terms else "0"
    return f"{quiet_db:.1f}+({depth:.1f})*{active}"


def main() -> int:
    ap = argparse.ArgumentParser(description="narration + BGM → loudnorm ミックス")
    ap.add_argument("--episode", default="ep01")
    ap.add_argument("--audio-dir", default=None, help="既定: audio/<ep>")
    ap.add_argument("--timing", default=None, help="既定: audio/<ep>/timing.json")
    ap.add_argument("--bgm", default=None, help="既定: audio/<ep>/bgm.wav")
    ap.add_argument("--out", default=None, help="既定: audio/<ep>/mix.wav")
    ap.add_argument("--duck-db", type=float, default=DUCK_DB, help="ナレ区間の BGM dB")
    ap.add_argument("--quiet-db", type=float, default=QUIET_DB, help="無音区間の BGM dB")
    ap.add_argument("--ramp", type=float, default=RAMP)
    ap.add_argument("--guard", type=float, default=GUARD)
    ap.add_argument("--target-i", type=float, default=-14.0)
    ap.add_argument("--tp", type=float, default=-1.5)
    ap.add_argument("--lra", type=float, default=11.0)
    args = ap.parse_args()

    adir = Path(args.audio_dir) if args.audio_dir else Path("audio") / args.episode
    timing_path = Path(args.timing) if args.timing else adir / "timing.json"
    bgm_path = Path(args.bgm) if args.bgm else adir / "bgm.wav"
    out_path = Path(args.out) if args.out else adir / "mix.wav"

    timing = json.loads(timing_path.read_text())
    if not bgm_path.exists():
        raise SystemExit(f"BGM がありません: {bgm_path} (先に make_bgm.py を実行)")

    beats: list[dict] = []
    wavs: list[Path] = []
    for scene in timing["scenes"]:
        for beat in scene["beats"]:
            wav = adir / beat["wav"]
            if not wav.exists():
                raise SystemExit(f"ナレ WAV がありません: {wav}")
            beats.append(beat)
            wavs.append(wav)
    if not wavs:
        raise SystemExit("timing.json に beats がありません")

    # ナレーション区間 (重なり/近接はマージして式を短く保つ)
    raw = [(b["start"], b["start"] + b["duration"]) for b in beats]
    intervals = merge_intervals(raw, min_gap=2 * args.ramp + args.guard)

    env_expr = build_envelope_expr(intervals, args.duck_db, args.quiet_db,
                                   args.ramp, args.guard)

    # ---- ffmpeg filter_complex を組む
    lines: list[str] = []
    for i, beat in enumerate(beats):
        delay_ms = int(round(beat["start"] * 1000))
        lines.append(
            f"[{i + 1}:a]aresample={SR},aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"adelay={delay_ms}:all=1[n{i}]")
    labels = "".join(f"[n{i}]" for i in range(len(beats)))
    lines.append(f"{labels}amix=inputs={len(beats)}:normalize=0:duration=longest[na]")
    lines.append(f"[0:a]aresample={SR},volume='{env_expr}':eval=frame[bg]")
    lines.append(
        f"[na][bg]amix=inputs=2:normalize=0:duration=longest,"
        f"loudnorm=I={args.target_i}:TP={args.tp}:LRA={args.lra},"
        f"aresample={SR}[out]")
    fc = ";\n".join(lines)

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "info",
           "-i", str(bgm_path)]
    for w in wavs:
        cmd += ["-i", str(w)]
    cmd += ["-filter_complex", fc,
            "-map", "[out]", "-ar", str(SR), "-c:a", "pcm_s16le",
            str(out_path)]

    print(f"[mix] beats={len(beats)}  intervals={len(intervals)}  "
          f"BGM {args.quiet_db}dB(無音)/{args.duck_db}dB(ナレ, ramp={args.ramp}s)")
    print(f"[mix] loudnorm 目標: I={args.target_i} TP={args.tp} LRA={args.lra}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr[-4000:])
        raise SystemExit(f"ffmpeg 失敗 (exit {proc.returncode})")

    # loudnorm の計測値を拾う (動的モードでも input/output が出る)
    m = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", proc.stderr)
    report: dict = {"episode": args.episode, "target_i": args.target_i,
                    "duck_db": args.duck_db, "quiet_db": args.quiet_db,
                    "narration_beats": len(beats)}
    if m:
        stats = json.loads(m[-1])
        report["loudnorm"] = stats
        print(f"[mix] loudnorm: input_i={stats.get('input_i')} → "
              f"output_i={stats.get('output_i')}  "
              f"output_tp={stats.get('output_tp')}  LRA={stats.get('output_lra')}")
    report["mix"] = str(out_path)
    (adir / "mix_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"[mix] 出力: {out_path}")
    print(f"[mix] レポート: {adir / 'mix_report.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

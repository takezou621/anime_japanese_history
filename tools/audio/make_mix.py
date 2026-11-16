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
    リニアランプ項の和 (0..1 にクランプ)。eval=frame で t を使う。
    volume フィルタの既定単位は「線形倍率」なので pow(10, dB/20) で返す。"""
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
    gain_db = f"{quiet_db:.1f}+({depth:.1f})*{active}"
    return f"pow(10\\,({gain_db})/20)"


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
    lines.append("[na][bg]amix=inputs=2:normalize=0:duration=longest[buspre]")
    fc_bus = ";\n".join(lines)

    # ---- SFX キュー (任意): audio/<ep>/sfx_cues.json があれば
    # loudnorm 前のバスへ重ねる (make_sfx_cues.py が生成)
    cues_path = adir / "sfx_cues.json"
    cues = (json.loads(cues_path.read_text())
            if cues_path.exists() else [])
    sfx_files: list[Path] = []
    if cues:
        sfx_lines: list[str] = []
        for k, cue in enumerate(cues):
            f = Path("assets/audio/sfx") / cue["file"]
            if not f.exists():
                raise SystemExit(f"SFX がありません: {f}")
            sfx_files.append(f)
            idx = 1 + len(wavs) + k
            gain = 10 ** (float(cue["gain_db"]) / 20.0)
            delay_ms = int(round(float(cue["t"]) * 1000))
            sfx_lines.append(
                f"[{idx}:a]aresample={SR},"
                f"aformat=sample_fmts=fltp:channel_layouts=stereo,"
                f"volume={gain:.4f},adelay={delay_ms}:all=1[sfx{k}]")
        labels = "[buspre]" + "".join(f"[sfx{k}]" for k in range(len(cues)))
        sfx_lines.append(
            f"{labels}amix=inputs={1 + len(cues)}:normalize=0:"
            f"duration=first[bus]")
        fc_bus += ";\n" + ";\n".join(sfx_lines)
        print(f"[mix] SFX キュー: {len(cues)} 件 ({cues_path})")
    else:
        fc_bus += ";\n[buspre]anull[bus]"

    def input_args() -> list[str]:
        cmd = ["-hide_banner", "-i", str(bgm_path)]
        for w in wavs:
            cmd += ["-i", str(w)]
        for s in sfx_files:
            cmd += ["-i", str(s)]
        return cmd

    print(f"[mix] beats={len(beats)}  intervals={len(intervals)}  "
          f"BGM {args.quiet_db}dB(無音)/{args.duck_db}dB(ナレ, ramp={args.ramp}s)")
    print(f"[mix] loudnorm 目標: I={args.target_i} TP={args.tp} LRA={args.lra} (2パス linear)")

    # ---- pass 1: バスのラウドネス計測
    analyze = ["ffmpeg", *input_args(),
               "-filter_complex", fc_bus + ";[bus]loudnorm=print_format=json[out]",
               "-map", "[out]", "-f", "null", "-"]
    p1 = subprocess.run(analyze, capture_output=True, text=True)
    if p1.returncode != 0:
        print(p1.stderr[-4000:])
        raise SystemExit(f"ffmpeg 計測パス失敗 (exit {p1.returncode})")
    m = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", p1.stderr)
    if not m:
        raise SystemExit("loudnorm の計測 JSON が取得できませんでした")
    meas = json.loads(m[-1])
    print(f"[mix] pass1 計測: I={meas['input_i']} TP={meas['input_tp']} "
          f"LRA={meas['input_lra']} thresh={meas['input_thresh']} "
          f"offset={meas.get('target_offset', 0)}")

    # ---- pass 2: linear モードで固定ゲイン適用 (TP 制約あり, alimiter は保険)
    ln = (f"loudnorm=I={args.target_i}:TP={args.tp}:LRA={args.lra}"
          f":measured_I={meas['input_i']}:measured_TP={meas['input_tp']}"
          f":measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}"
          f":offset={meas.get('target_offset', 0)}:linear=true")
    fc_out = fc_bus + (
        f";[bus]{ln},"
        f"alimiter=limit={10 ** ((args.tp - 0.08) / 20.0):.4f}:attack=5:release=80:level=0,"
        f"aresample={SR}[out]")
    cmd = ["ffmpeg", "-y", *input_args(),
           "-filter_complex", fc_out, "-map", "[out]",
           "-ar", str(SR), "-c:a", "pcm_s16le", str(out_path)]
    p2 = subprocess.run(cmd, capture_output=True, text=True)
    if p2.returncode != 0:
        print(p2.stderr[-4000:])
        raise SystemExit(f"ffmpeg 失敗 (exit {p2.returncode})")
    nan_count = p2.stderr.count("Invalid value NaN")
    if nan_count > 5:
        raise SystemExit(f"volume 式が頻繁に NaN を出しました ({nan_count} 回) — エンベロープ式を確認")
    elif nan_count:
        # af_volume は初期化時に t=NaN で1回評価するための既知の benign 警告
        print(f"[mix] 注意: volume 初期評価の NaN 警告 {nan_count} 件 (benign)")

    # ---- 出力のラウドネスを検証してレポートに反映
    verify = ["ffmpeg", "-hide_banner", "-i", str(out_path),
              "-af", "loudnorm=print_format=json", "-f", "null", "-"]
    p3 = subprocess.run(verify, capture_output=True, text=True)
    m3 = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", p3.stderr)
    if m3:
        out_stats = json.loads(m3[-1])
        print(f"[mix] 出力検証: I={out_stats['input_i']} LUFS  "
              f"TP={out_stats['input_tp']} dBTP  LRA={out_stats['input_lra']}")
    else:
        out_stats = None

    report: dict = {"episode": args.episode, "target_i": args.target_i,
                    "duck_db": args.duck_db, "quiet_db": args.quiet_db,
                    "narration_beats": len(beats),
                    "sfx_cues": len(cues),
                    "loudnorm_mode": "2-pass linear",
                    "measured": meas,
                    "output_loudness": out_stats,
                    "mix": str(out_path)}
    (adir / "mix_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"[mix] 出力: {out_path}")
    print(f"[mix] レポート: {adir / 'mix_report.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

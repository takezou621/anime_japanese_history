#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e2e_test.py — aigen ↔ assemble 統合のオフライン通しテスト (API 不要).

偽の「Veo クリップ」(ffmpeg testsrc2) を用意し、script.json の visual.ai_clip /
manifest / 欠損フォールバックの 3 パターンが最終 MP4 + QC json まで通ることを確認する。

  uv run --with pillow python tools/aigen/e2e_test.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W, H, FPS = 1920, 1080, 30
FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}" +
          (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=600)


def main() -> int:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not (ffmpeg and ffprobe):
        print("ffmpeg/ffprobe が必要です")
        return 2

    print("== aigen ↔ assemble E2E (オフライン) ==")
    tmp = Path(tempfile.mkdtemp(prefix="aigen_e2e_"))
    assets = tmp / "assets" / "scenes"
    assets.mkdir(parents=True)

    # 背景 2枚 (1920x1080 PNG)
    for name, color in (("bg_a", "0x2b4a8b"), ("bg_b", "0xe8543f")):
        r = run([ffmpeg, "-y", "-loglevel", "error", "-f", "lavfi",
                 "-i", f"color=c={color}:s={W}x{H}:d=1",
                 "-frames:v", "1", str(assets / f"{name}.png")])
        check(f"背景生成 {name}", r.returncode == 0)

    # 偽 AI クリップ: 4秒 720p (scale/crop + pingpong 伸長を両方 exercise)
    clip4 = tmp / "fake_veo_4s.mp4"
    r = run([ffmpeg, "-y", "-loglevel", "error", "-f", "lavfi", "-i",
             "testsrc2=size=1280x720:rate=30:duration=4",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip4)])
    check("偽クリップ生成", r.returncode == 0)

    # script.json: s01=欠損クリップ(フォールバック), s02=正常クリップ, xfade境界
    script = {
        "episode": "epAI", "title": "AI統合E2E",
        "characters": [],
        "scenes": [
            {"id": "s01", "section": "opening",
             "visual": {"background": "bg_a",
                        "ai_clip": str(tmp / "missing.mp4"),
                        "camera": {"motion": "kenburns_in"}},
             "beats": [{"speaker": "sensei", "text": "AI統合のテストです。"}]},
            {"id": "s02", "section": "story",
             "visual": {"background": "bg_b",
                        "ai_clip": str(clip4),
                        "camera": {"motion": "kenburns_in"}},
             "beats": [{"speaker": "manabu",
                        "text": "AIクリップの上に字幕が乗るのだ!"}]},
        ],
    }
    script_path = tmp / "script.json"
    script_path.write_text(json.dumps(script, ensure_ascii=False),
                           encoding="utf-8")

    timing = {"episode": "epAI", "total_duration": 14.0,
              "scenes": [
                  {"id": "s01", "start": 0.0, "duration": 6.0,
                   "beats": [{"index": 0, "speaker": "sensei",
                              "start": 0.2, "duration": 1.5}]},
                  {"id": "s02", "start": 6.0, "duration": 8.0,
                   "beats": [{"index": 0, "speaker": "manabu",
                              "start": 6.3, "duration": 2.0}]},
              ]}
    timing_path = tmp / "timing.json"
    timing_path.write_text(json.dumps(timing, ensure_ascii=False),
                           encoding="utf-8")

    mix = tmp / "mix.wav"
    r = run([ffmpeg, "-y", "-loglevel", "error", "-f", "lavfi",
             "-i", "anullsrc=r=48000:cl=stereo:d=14", str(mix)])
    check("mix 生成", r.returncode == 0)

    out = tmp / "epAI_FINAL.mp4"
    qc_out = tmp / "epAI_QC.json"
    cmd = ["uv", "run", "--with", "pillow", "python",
           str(ROOT / "tools" / "editor" / "assemble.py"),
           "--episode", "epAI",
           "--script", str(script_path), "--timing", str(timing_path),
           "--assets", str(tmp / "assets"), "--mix", str(mix),
           "--out", str(out), "--qc", str(qc_out),
           "--profile", "test", "--jobs", "2"]
    print("  assemble.py 実行中...")
    r = run(cmd)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
        check("assemble.py 完了", False)
        return 1
    check("assemble.py 完了", out.is_file())

    qc = json.loads(qc_out.read_text(encoding="utf-8"))
    check("QC PASS (test profile)", qc.get("pass") is True,
          json.dumps(qc.get("checks", {}), ensure_ascii=False)[:200])

    # 長さ: head/tail borrow 設計により最終タイムラインは timing.json と同一
    # (6s + 8s = 14.0s, xfade は borrow 0.5+0.5 の内部で完結)
    dur = float(subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(out)], capture_output=True, text=True
    ).stdout.strip())
    check("長さ 14.0s ±0.3 (= timing.total)", abs(dur - 14.0) < 0.3,
          f"{dur:.3f}s")

    ai = qc.get("ai_segments", [])
    by_sid = {a["sid"]: a for a in ai}
    check("ai_segments レポート", set(by_sid) == {"s01", "s02"})
    check("s02 = ai (pingpong)", by_sid.get("s02", {}).get("mode") == "ai"
          and "pingpong" in by_sid.get("s02", {}).get("detail", ""))
    check("s01 = fallback (欠損)", by_sid.get("s01", {}).get("mode") == "fallback")

    print("=" * 34)
    if FAILS:
        print(f"結果: {len(FAILS)} 失敗 → {FAILS}")
        return 1
    print(f"結果: 全テスト合格 ✅  (作業ディレクトリ: {tmp})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

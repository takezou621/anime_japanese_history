#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai_segments.py — Veo i2v クリップを assemble のセグメント契約に正規化する.

契約 (docs/02_DESIGN.md §2.1):
- script.json の ``visual.ai_clip`` にパス (repo ルート相対) を書く、または
  ``video/epNN_ai/manifest.json`` の ``{"<scene_id>": "<ファイル名>"}`` を使う。
  両方ある場合は script.json が優先。
- クリップは「シーン長 (timing.json 実測) ちょうど」に伸縮される:
  - クリップ >= シーン長 : 冒頭からトリム
  - クリップ <  シーン長 : 往復 (ping-pong) ループで自然につなぐ
    (STYLE_GUIDE「静止3秒禁止」を満たす。静止画ホールドは使わない)
- 出力は 1920x1080 / 30fps CFR / 音声なし (ナレーションは mix.wav 側)。
- クリップが無い/壊れている場合は assemble.py が従来の kenburns に
  フォールバックし、QC json の ``ai_segments`` に記録する。

Selftest (オフライン, API 不要):
  python3 tools/editor/ai_segments.py
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN_W, MAIN_H = 1920, 1080
FPS = 30
MAX_SOURCE_SEC = 30.0     # ping-pong 用メモリガード (reverse は全フレーム保持)
MANIFEST_NAME = "manifest.json"


# ---------------------------------------------------------------------------
# 解決

def manifest_path(ep: str) -> Path:
    return ROOT / "video" / f"{ep}_ai" / MANIFEST_NAME


def load_manifest(ep: str) -> dict:
    p = manifest_path(ep)
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"[ai][warn] manifest を読めません: {p}")
        return {}
    return data.get("clips", data) if isinstance(data, dict) else {}


def resolve_clip(scene: dict, ep: str, manifest: dict) -> str:
    """scene の AI クリップパスを返す (無ければ "")。script.json > manifest。"""
    vis = scene.get("visual", {}) or {}
    ref = str(vis.get("ai_clip") or "").strip()
    if ref:
        p = Path(ref)
        if not p.is_absolute():
            p = ROOT / ref
        return str(p)
    sid = scene.get("id", "")
    name = manifest.get(sid)
    if name:
        return str(manifest_path(ep).parent / str(name))
    return ""


# ---------------------------------------------------------------------------
# プローブ + 正規化

def probe_duration(ffprobe: str, path: str) -> float:
    out = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=60)
    try:
        return float(out.stdout.strip().splitlines()[0])
    except (ValueError, IndexError):
        raise RuntimeError(f"duration を取得できません: {path} ({out.stderr[:200]})")


def build_prepare_graph(src_duration: float, dur: float) -> tuple[str, str]:
    """正規化 filter_complex を返す。(graph, mode)"""
    head = (f"[0:v]scale={MAIN_W}:{MAIN_H}:force_original_aspect_ratio=increase,"
            f"crop={MAIN_W}:{MAIN_H},fps={FPS},settb=AVTB")
    if src_duration > MAX_SOURCE_SEC:
        head += f",trim=duration={MAX_SOURCE_SEC:.3f},setpts=PTS-STARTPTS"
        src_duration = MAX_SOURCE_SEC
    if src_duration >= dur:
        graph = (f"{head}[base];[base]trim=duration={dur:.3f},"
                 f"setpts=PTS-STARTPTS,format=yuv420p,setsar=1[v]")
        return graph, "trim"
    # 往復 (ping-pong) ユニットを作り、シーン長をカバーするまで繰り返す
    unit_frames = max(int(round(src_duration * FPS)), 2)
    loops = max(int(-(-dur // (2 * src_duration))) - 1, 0)  # ceil で必要回数-1
    graph = (
        f"{head}[base];"
        f"[base]split[b1][b2];[b2]reverse[br];"
        f"[b1][br]concat=n=2:v=1:a=0,setpts=PTS-STARTPTS[pp];"
        f"[pp]loop=loop={loops}:size={unit_frames}:start=0[lpl];"
        f"[lpl]trim=duration={dur:.3f},setpts=PTS-STARTPTS,fps={FPS},"
        f"format=yuv420p,setsar=1[v]")
    return graph, "pingpong"


def prepare_ai_clip(ffmpeg: str, clip: str, frames: int, out_path: Path,
                    ffprobe: str | None = None) -> dict:
    """AI クリップを「ちょうど frames フレームの 1920x1080@30 無音」に正規化する。"""
    dur = frames / FPS
    if not Path(clip).is_file():
        raise FileNotFoundError(f"AI clip not found: {clip}")
    src = probe_duration(ffprobe, clip) if ffprobe else 8.0
    if ffprobe is None:
        # ffprobe 無しでも trim は安全側 (クリップが短い場合は pingpong が必要だが
        # assemble からは必ず ffprobe を渡す。8.0 は Veo 既定尺の想定)
        src = 8.0
        if dur <= src:
            pass
    graph, mode = build_prepare_graph(src, dur)
    fpath = out_path.with_suffix(".filter.txt")
    fpath.write_text(graph, encoding="utf-8")
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", str(clip),
           "-/filter_complex", str(fpath),
           "-map", "[v]", "-an",
           "-c:v", "libx264", "-crf", "14", "-preset", "medium",
           "-pix_fmt", "yuv420p", "-r", str(FPS), "-fps_mode", "cfr",
           str(out_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"prepare failed: {proc.stderr[-400:]}")
    return {"path": str(out_path), "mode": mode,
            "in_duration": src, "out_duration": dur}


# ---------------------------------------------------------------------------
# selftest (オフライン)

def _selftest() -> int:
    import shutil
    import tempfile
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not (ffmpeg and ffprobe):
        print("ffmpeg/ffprobe が必要です (brew install ffmpeg-full)")
        return 2
    fails: list[str] = []

    def check(name, cond, detail=""):
        print(f"  [{'OK ' if cond else 'FAIL'}] {name}" +
              (f" — {detail}" if detail and not cond else ""))
        if not cond:
            fails.append(name)

    print("== ai_segments selftest ==")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        src = tmp / "src.mp4"
        subprocess.run([ffmpeg, "-y", "-loglevel", "error",
                        "-f", "lavfi", "-i",
                        "testsrc2=size=1280x720:rate=30:duration=8",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(src)],
                       check=True)
        check("source probe", abs(probe_duration(ffprobe, str(src)) - 8.0) < 0.2)

        # trim パス (3s < 8s)
        out_trim = tmp / "trim.mp4"
        info = prepare_ai_clip(ffmpeg, str(src), 90, out_trim, ffprobe)
        d = probe_duration(ffprobe, str(out_trim))
        check("trim 90frames", info["mode"] == "trim" and abs(d - 3.0) < 0.1,
              f"{info} d={d:.3f}")

        # pingpong パス (20s > 8s)
        out_pp = tmp / "pp.mp4"
        info = prepare_ai_clip(ffmpeg, str(src), 600, out_pp, ffprobe)
        d = probe_duration(ffprobe, str(out_pp))
        check("pingpong 600frames", info["mode"] == "pingpong"
              and abs(d - 20.0) < 0.15, f"{info} d={d:.3f}")

        # 解像度/形式
        probe = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0",
                                "-show_entries",
                                "stream=width,height,r_frame_rate,codec_name",
                                "-of", "json", str(out_pp)],
                               capture_output=True, text=True)
        st = json.loads(probe.stdout)["streams"][0]
        check("1920x1080 h264", st["width"] == 1920 and st["height"] == 1080
              and st["codec_name"] == "h264")
        check("30fps", abs(eval(st["r_frame_rate"]) - 30) < 0.01)

        # manifest / ai_clip 解決
        scene = {"id": "s02", "visual": {"background": "x"}}
        got = resolve_clip(scene, "ep00", {})
        check("manifest 無しは空", got == "")
        got = resolve_clip(scene, "ep00", {"s02": "s02_x.mp4"})
        check("manifest 経由のパス", got.endswith("video/ep00_ai/s02_x.mp4"),
              got)
        scene2 = {"id": "s02", "visual": {"ai_clip": "/abs/clip.mp4"}}
        check("ai_clip 明示は最優先",
              resolve_clip(scene2, "ep00", {"s02": "s02_x.mp4"}) ==
              "/abs/clip.mp4")

    print("=" * 24)
    if fails:
        print(f"結果: {len(fails)} 失敗 → {fails}")
        return 1
    print("結果: 全テスト合格 ✅")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())

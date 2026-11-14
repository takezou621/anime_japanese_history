# -*- coding: utf-8 -*-
"""Render QC for the editor pipeline (video/epNN_QC.json).

Checks (docs/02_DESIGN.md §3 tools/editor + Issue #5):
- duration   : matches timing.json total_duration (±0.35s); for the full
               profile additionally 300-600s (YouTube long-form target)
- resolution : 1920x1080
- fps        : 30
- codec/pix  : h264 + yuv420p
- audio      : aac present, stream info recorded
- loudness   : EBU R128 integrated loudness (loudnorm print) — target
               -14 LUFS ±1.5, true peak <= -1.0 dBTP (warn-only in test profile)
- black      : blackdetect ratio < 1%

Exit code 1 when any critical check fails.
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone

LOUDNESS_TARGET = -14.0
LOUDNESS_TOL = 1.5
TP_MAX = -1.0
DUR_TOL = 0.35
FULL_RANGE = (300.0, 600.0)
BLACK_MAX = 0.01


def probe_media(ffprobe: str, path: str) -> dict:
    out = subprocess.run(
        [ffprobe, "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", path],
        capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def measure_loudness(ffmpeg: str, path: str) -> dict:
    """Run loudnorm analysis pass, return {'input_i':..,'input_tp':..,..}."""
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostats", "-i", path,
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", proc.stderr)
    if not m:
        raise RuntimeError(f"loudnorm analysis failed: {proc.stderr[-800:]}")
    return json.loads(m.group(0))


def detect_black(ffmpeg: str, path: str, duration: float) -> dict:
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostats", "-i", path,
         "-vf", "blackdetect=d=0.1:pic_th=0.98", "-an",
         "-f", "null", "-"],
        capture_output=True, text=True)
    runs = []
    for m in re.finditer(
            r"black_start:([\d.]+)\s+black_end:([\d.]+)\s+black_ratio:([\d.]+)",
            proc.stderr):
        s, e = float(m.group(1)), float(m.group(2))
        s, e = max(s, 0.0), min(e, duration)
        if e > s:
            runs.append({"start": round(s, 3), "end": round(e, 3),
                         "dur": round(e - s, 3)})
    total = sum(r["dur"] for r in runs)
    return {"runs": runs, "ratio": (total / duration) if duration > 0 else 0.0}


def _get_stream(probe: dict, codec_type: str) -> dict | None:
    for st in probe.get("streams", []):
        if st.get("codec_type") == codec_type:
            return st
    return None


def run_checks(video: str, timing: dict, profile: str,
               ffmpeg: str, ffprobe: str,
               expected: float | None = None) -> dict:
    probe = probe_media(ffprobe, video)
    fmt = probe.get("format", {})
    duration = float(fmt.get("duration", 0.0))
    v = _get_stream(probe, "video") or {}
    a = _get_stream(probe, "audio") or {}

    checks: dict = {}

    if expected is None:
        expected = float(timing.get("total_duration",
                                    timing.get("total", 0.0)) or 0.0)
    ok_dur = abs(duration - expected) <= DUR_TOL if expected else True
    in_range = FULL_RANGE[0] <= duration <= FULL_RANGE[1]
    checks["duration"] = {
        "pass": bool(ok_dur and (profile != "full" or in_range)),
        "value": round(duration, 3),
        "expected": expected,
        "range": list(FULL_RANGE) if profile == "full" else None,
        "detail": ("matches timing total" if ok_dur else
                   f"deviates from timing total by {duration - expected:+.3f}s")
        + ("" if profile != "full" or in_range else
           f"; outside {FULL_RANGE[0]:.0f}-{FULL_RANGE[1]:.0f}s"),
    }

    width, height = v.get("width"), v.get("height")
    checks["resolution"] = {"pass": (width, height) == (1920, 1080),
                            "value": f"{width}x{height}"}

    fps = v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1"
    try:
        num, den = fps.split("/")
        fps_val = float(num) / float(den)
    except (ValueError, ZeroDivisionError):
        fps_val = 0.0
    checks["fps"] = {"pass": abs(fps_val - 30.0) < 0.01,
                     "value": round(fps_val, 3)}

    checks["video_codec"] = {"pass": v.get("codec_name") == "h264",
                             "value": v.get("codec_name")}
    checks["pix_fmt"] = {"pass": v.get("pix_fmt") == "yuv420p",
                         "value": v.get("pix_fmt")}
    checks["audio"] = {
        "pass": a.get("codec_name") == "aac",
        "value": {"codec": a.get("codec_name"),
                  "sample_rate": a.get("sample_rate"),
                  "channels": a.get("channels"),
                  "bit_rate": a.get("bit_rate")},
    }

    loud = measure_loudness(ffmpeg, video)
    try:
        i_lufs = float(loud.get("input_i"))
        tp = float(loud.get("input_tp"))
    except (TypeError, ValueError):
        i_lufs, tp = None, None
    loud_ok = (i_lufs is not None and tp is not None
               and LOUDNESS_TARGET - LOUDNESS_TOL <= i_lufs
               <= LOUDNESS_TARGET + LOUDNESS_TOL and tp <= TP_MAX)
    checks["loudness"] = {
        "pass": True if profile == "test" else bool(loud_ok),
        "warn": profile == "test" and not loud_ok,
        "value": {"input_i": i_lufs, "input_tp": tp,
                  "input_lra": loud.get("input_lra"),
                  "target_i": LOUDNESS_TARGET, "tolerance": LOUDNESS_TOL,
                  "tp_max": TP_MAX},
        "detail": ("test profile: loudness is advisory only" if profile == "test"
                   else ("within -14 LUFS ±1.5, TP<=-1.0" if loud_ok
                         else "out of loudness/TP target")),
    }

    black = detect_black(ffmpeg, video, duration)
    checks["black_frames"] = {
        "pass": black["ratio"] < BLACK_MAX,
        "value": {"ratio": round(black["ratio"], 5), "runs": black["runs"]},
        "threshold": BLACK_MAX,
    }

    qc = {
        "episode": timing.get("episode", ""),
        "profile": profile,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "video": video,
        "duration_sec": round(duration, 3),
        "checks": checks,
        "streams": probe.get("streams", []),
        "format": {"duration": fmt.get("duration"),
                   "size": fmt.get("size"),
                   "bit_rate": fmt.get("bit_rate")},
        "pass": bool(all(c["pass"] for c in checks.values())),
    }
    return qc


def print_summary(qc: dict) -> None:
    print("\n=== QC summary ===")
    for name, c in qc["checks"].items():
        mark = "PASS" if c["pass"] else "FAIL"
        warn = " (warn)" if c.get("warn") else ""
        val = c.get("value")
        if isinstance(val, dict):
            val = {k: val[k] for k in list(val)[:4]}
        print(f"  [{mark}{warn}] {name}: {val}")
    print(f"  overall: {'PASS' if qc['pass'] else 'FAIL'}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--timing", required=True)
    ap.add_argument("--profile", default="full", choices=["full", "test"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--ffmpeg", default="ffmpeg")
    ap.add_argument("--ffprobe", default="ffprobe")
    a = ap.parse_args()
    with open(a.timing, encoding="utf-8") as f:
        timing = json.load(f)
    qc = run_checks(a.video, timing, a.profile, a.ffmpeg, a.ffprobe)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(qc, f, ensure_ascii=False, indent=2)
    print_summary(qc)
    print(f"QC json -> {a.out}")
    raise SystemExit(0 if qc["pass"] else 1)

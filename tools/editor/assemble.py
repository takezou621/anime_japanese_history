#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assemble.py — script.json + timing.json + assets -> final MP4 + QC (Issue #5).

Pipeline
--------
1. plan      : timing.json defines each scene's global [start, start+duration).
               Sections are taken from script.json. A boundary between scenes
               of DIFFERENT sections becomes a 0.5s xfade; same-section
               boundaries are hard cuts.
2. segments  : per scene, a 1920x1080@30 CFR segment is rendered:
               - background PNG -> 3x supersample -> zoompan kenburns camera
                 (jitter-free; 静止3秒禁止 rule satisfied on every scene)
               - layer assets (characters/props) and overlay_text PNGs are
                 composited with appear motions (slide_in_l/r, pop_in, fade,
                 fade_up, slide_up, zoom_in) enabled at the beat start time,
                 converted to segment-local time (t_local = t_global -
                 segment_start)
               Timing pads: a segment adjacent to an xfade boundary borrows
               0.5s of head/tail, and the xfade blend is placed at
               [boundary - 0.5, boundary). This keeps the final video timeline
               IDENTICAL to timing.json (no subtitle drift).
3. subtitles : ASS generated from timing.json (tools/editor/make_subtitles.py),
               burned on the final timeline via libass `subtitles`.
4. mux       : audio/epNN/mix.wav + x264 crf18/preset slow + AAC 192k,
               +faststart, yuv420p.
5. QC        : video/epNN_QC.json (tools/editor/qc.py).

Requires an ffmpeg with libass (`subtitles` filter). Autodetected:
/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg, falling back to PATH.
ffmpeg 9 note: legacy -filter_complex_script/-vsync are gone; this tool uses
`-/filter_complex <file>` (read option value from file) and -fps_mode.

Usage (defaults follow the repo convention):
  uv run --with pillow python tools/editor/assemble.py --episode ep01
  ... --profile test --only-scenes s01,s02 --dry-plan
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from motion import FPS, MAIN_W, MAIN_H, kenburns_exprs, layer_motion, DEFAULT_MOTION_DUR
from text_overlays import render_overlay, STYLES
import make_subtitles
import qc as qcmod

XFADE_DUR = 0.5          # section crossfade (STYLE_GUIDE / DESIGN)
SUPER_W, SUPER_H = 5760, 3240   # 3x supersampled zoompan input
CONTIG_TOL = 0.02

FFMPEG_CANDIDATES = [
    "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",
    "/usr/local/opt/ffmpeg-full/bin/ffmpeg",
    "ffmpeg",
]


# ---------------------------------------------------------------------------
# toolchain
# ---------------------------------------------------------------------------

def find_toolchain(preferred: str | None = None) -> tuple[str, str]:
    cands = [preferred] if preferred else list(FFMPEG_CANDIDATES)
    for cand in cands:
        if not cand:
            continue
        exe = shutil.which(cand) or (cand if os.path.isfile(cand) else None)
        if not exe:
            continue
        try:
            out = subprocess.run([exe, "-hide_banner", "-filters"],
                                 capture_output=True, text=True, timeout=30)
            has_libass = "subtitles" in out.stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
        ffprobe = shutil.which(str(Path(exe).with_name("ffprobe"))) or \
            shutil.which("ffprobe")
        if not has_libass:
            print(f"[toolchain] {exe} has no libass `subtitles` filter; "
                  "trying next candidate")
            continue
        if not ffprobe:
            print(f"[toolchain] {exe} usable but ffprobe missing; "
                  "trying next candidate")
            continue
        return exe, ffprobe
    raise SystemExit("no ffmpeg with the libass `subtitles` filter found; "
                     "install ffmpeg-full (brew install ffmpeg-full) or pass "
                     "--ffmpeg /path/to/ffmpeg")


# ---------------------------------------------------------------------------
# data model + plan
# ---------------------------------------------------------------------------

@dataclass
class Layer:
    image: str
    filters: list[str]
    x: str
    y: str
    enable: str
    desc: str = ""


@dataclass
class Span:
    sid: str
    section: str
    start: float          # timing global start
    end: float            # timing global end (= start + duration)
    head: float           # 0.5 borrow before segment start (xfade only)
    tail: float           # 0.5 borrow after segment end (xfade only)
    frames: int
    dur: float            # frames / FPS (exact)
    seg_start: float      # start - head (local t=0 of the segment)
    cam_motion: str
    cam_intensity: float
    bg: str
    layers: list[Layer] = field(default_factory=list)


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_plan(script: dict, timing: dict, assets_dir: Path,
               tmp_dir: Path, only: list[str] | None) -> tuple[list[Span], list[dict]]:
    scenes = script.get("scenes", [])
    if not scenes:
        raise SystemExit("script.json has no scenes")
    windows, total = make_subtitles.scene_windows(timing)

    missing = [sc["id"] for sc in scenes if sc["id"] not in windows]
    if missing:
        raise SystemExit(f"timing.json missing scenes: {missing}")

    if only:
        wanted = set(only)
        scenes = [sc for sc in scenes if sc["id"] in wanted]
        if not scenes:
            raise SystemExit(f"--only-scenes matched none of {only}")

    spans: list[Span] = []
    for i, sc in enumerate(scenes):
        start, end = windows[sc["id"]]
        dur = end - start
        head = tail = 0.0
        prev_sc = scenes[i - 1] if i > 0 else None
        next_sc = scenes[i + 1] if i + 1 < len(scenes) else None
        if prev_sc and prev_sc.get("section") != sc.get("section"):
            head = XFADE_DUR
        if next_sc and next_sc.get("section") != sc.get("section"):
            tail = XFADE_DUR
        frames = max(int(round((dur + head + tail) * FPS)), int(FPS * 0.5))
        seg_start = start - head
        vis = sc.get("visual", {})
        cam = vis.get("camera", {}) or {}
        bg_name = vis.get("background")
        spans.append(Span(
            sid=sc["id"], section=sc.get("section", ""),
            start=start, end=end, head=head, tail=tail,
            frames=frames, dur=frames / FPS, seg_start=seg_start,
            cam_motion=cam.get("motion", "kenburns_in"),
            cam_intensity=cam.get("intensity", 1.0),
            bg=str(assets_dir / "scenes" / f"{bg_name}.png")))
        # contiguity check (timing should be gapless across scenes)
        if prev_sc:
            p_start, p_end = windows[prev_sc["id"]]
            if abs(p_end - start) > CONTIG_TOL:
                print(f"[plan][warn] gap/overlap between {prev_sc['id']} "
                      f"(end {p_end:.3f}) and {sc['id']} (start {start:.3f})")
    # cross-check script vs timing sections when timing provides them
    tsecs = make_subtitles.timing_scenes(timing)
    for sc in scenes:
        tsec = (tsecs.get(sc["id"]) or {}).get("section")
        if tsec and tsec != sc.get("section"):
            print(f"[plan][warn] section mismatch for {sc['id']}: script="
                  f"{sc.get('section')} timing={tsec} (script wins)")
    print(f"[plan] total from timing: {total:.3f}s")
    return spans, scenes


# ---------------------------------------------------------------------------
# layer specs
# ---------------------------------------------------------------------------

def _image_size(path: str) -> tuple[int, int]:
    from PIL import Image  # local import: only needed when rendering
    with Image.open(path) as im:
        return im.size


def _beat_times(scene: dict, ts: dict, scene_end: float,
                seg_start: float) -> list[dict]:
    """Local-time beat info: [{speaker, start(local), end(local)}]."""
    tbeats = ts.get("beats") or []
    sbeats = scene.get("beats", [])
    out = []
    for i, sb in enumerate(sbeats):
        tb = tbeats[i] if i < len(tbeats) else {}
        g = float(tb.get("start", 0.0))
        if tb.get("duration") is not None:
            g_end = g + float(tb["duration"])
        elif i + 1 < len(tbeats):
            g_end = float(tbeats[i + 1]["start"])
        else:
            g_end = scene_end
        out.append({
            "speaker": (tb.get("speaker") or sb.get("speaker") or "").lower(),
            "start": g - seg_start,
            "end": g_end - seg_start,
        })
    return out


def scene_layers(span: Span, scene: dict, ts: dict, assets_dir: Path,
                 tmp_dir: Path) -> None:
    """Populate span.layers (characters/props first, overlay_text on top)."""
    beats = _beat_times(scene, ts, span.end, span.seg_start)
    vis = scene.get("visual", {}) or {}
    assets = vis.get("assets", []) or []

    # decide appear time per asset: match character id in asset name,
    # otherwise the first beat; stagger collisions by 0.25s
    used: dict[float, int] = {}

    def appear_for(name: str) -> float:
        hit = next((b["start"] for b in beats
                    if b["speaker"] and b["speaker"] in name.lower()), None)
        t0 = hit if hit is not None else (beats[0]["start"] if beats else 0.0)
        t0 = max(t0, 0.0)
        k = used.get(round(t0, 3), 0)
        used[round(t0, 3)] = k + 1
        return t0 + 0.25 * k

    for a in assets:
        name = a.get("name", "")
        path = assets_dir / "overlay" / f"{name}.png"
        if not path.is_file():
            raise SystemExit(f"overlay asset missing: {path}")
        iw, ih = _image_size(str(path))
        scale = float(a.get("scale", 1.0) or 1.0)
        tw, th = max(2, int(round(iw * scale)) // 2 * 2), \
            max(2, int(round(ih * scale)) // 2 * 2)
        pos = a.get("pos") or [MAIN_W / 2, MAIN_H / 2]
        px, py = float(pos[0]), float(pos[1])
        t0 = appear_for(name)
        m = layer_motion(a.get("motion"), t0, DEFAULT_MOTION_DUR,
                         px, py, tw, th)
        span.layers.append(Layer(
            image=str(path),
            filters=[f"scale={tw}:{th}:flags=lanczos"] + m["filters"],
            x=m["x"], y=m["y"], enable=m["enable"],
            desc=f"asset:{name}@{t0:.2f}s"))

    # overlay_text entries live on beats and appear at the beat time
    for i, b in enumerate(scene.get("beats", [])):
        t0b = beats[i]["start"] if i < len(beats) else 0.0
        for k, ot in enumerate(b.get("overlay_text") or []):
            style = ot.get("style", "title_main")
            cfg = STYLES.get(style)
            if cfg is None:
                raise SystemExit(f"unknown overlay_text style {style!r} "
                                 f"in {span.sid} beat {i}")
            img, center = render_overlay(ot)
            png = tmp_dir / f"{span.sid}_b{i:02d}_{k}.png"
            img.save(png)
            px, py = center
            t0 = max(t0b + 0.15 * k, 0.0)
            m = layer_motion(ot.get("motion") or cfg["default_motion"],
                             t0, float(ot.get("dur", DEFAULT_MOTION_DUR)),
                             px, py, img.width, img.height)
            span.layers.append(Layer(
                image=str(png),
                filters=m["filters"],
                x=m["x"], y=m["y"], enable=m["enable"],
                desc=f"text:{style}@{t0:.2f}s"))
    # drop None filters
    for L in span.layers:
        L.filters = [f for f in L.filters if f]


# ---------------------------------------------------------------------------
# segment rendering
# ---------------------------------------------------------------------------

def segment_filtergraph(span: Span) -> str:
    z, x, y = kenburns_exprs(span.cam_motion, span.cam_intensity, span.frames)
    parts = [
        f"[0:v]scale={SUPER_W}:{SUPER_H}:flags=lanczos,"
        f"zoompan=z='{z}':x='{x}':y='{y}':d={span.frames}:"
        f"s={MAIN_W}x{MAIN_H}:fps={FPS},settb=AVTB,format=yuv420p,setsar=1[bg0];"
    ]
    cur = "bg0"
    for i, L in enumerate(span.layers, start=1):
        chain = f"[{i}:v]format=rgba"
        for f in L.filters:
            chain += f",{f}"
        chain += f"[L{i}];"
        parts.append(chain)
        parts.append(
            f"[{cur}][L{i}]overlay=x='{L.x}':y='{L.y}'"
            f":enable='{L.enable}':eof_action=pass[O{i}];")
        cur = f"O{i}"
    parts.append(f"[{cur}]format=yuv420p[v]")
    return "\n".join(parts)


def render_segment(span: Span, ffmpeg: str, filter_path: Path,
                   out_path: Path) -> tuple[str, bool, str]:
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", span.bg]
    for L in span.layers:
        cmd += ["-loop", "1", "-framerate", str(FPS),
                "-t", f"{span.dur + 0.5:.3f}", "-i", L.image]
    script = segment_filtergraph(span)
    filter_path.write_text(script, encoding="utf-8")
    cmd += [
        "-/filter_complex", str(filter_path),
        "-map", "[v]",
        "-c:v", "libx264", "-crf", "14", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-r", str(FPS), "-fps_mode", "cfr",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return span.sid, proc.returncode == 0, proc.stderr[-1500:]


# ---------------------------------------------------------------------------
# final assembly
# ---------------------------------------------------------------------------

def _escape_filter_path(p: str) -> str:
    return p.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def final_filtergraph(spans: list[Span], ass_path: str | None,
                      band_input: int | None = None) -> str:
    n = len(spans)
    groups: list[list[int]] = []
    for i, sp in enumerate(spans):
        if i == 0 or spans[i - 1].section != sp.section:
            groups.append([i])
        else:
            groups[-1].append(i)

    lines: list[str] = []
    group_labels: list[str] = []
    for gi, idxs in enumerate(groups):
        if len(idxs) == 1:
            group_labels.append(f"[{idxs[0]}:v]")
            continue
        ins = "".join(f"[{i}:v]" for i in idxs)
        lines.append(f"{ins}concat=n={len(idxs)}:v=1:a=0[G{gi}];")
        group_labels.append(f"[G{gi}]")

    cur = group_labels[0]
    if len(groups) > 1:
        for k in range(1, len(groups)):
            boundary_idx = groups[k][0]          # first scene of next group
            offset = spans[boundary_idx].start - XFADE_DUR
            if offset <= 0:
                raise SystemExit(
                    f"xfade offset <= 0 at boundary before "
                    f"{spans[boundary_idx].sid} ({offset:.3f}s); scene too short")
            lab = f"X{k}"
            lines.append(
                f"{cur}{group_labels[k]}xfade=transition=fade:"
                f"duration={XFADE_DUR}:offset={offset:.3f}[{lab}];")
            cur = f"[{lab}]"

    tail = "null[v]"
    burn_label = cur
    if band_input is not None:
        lines.append(f"[{band_input}:v]format=rgba[BAND];")
        lines.append(f"{cur}[BAND]overlay=0:0:eof_action=pass[XB];")
        burn_label = "[XB]"
    if ass_path:
        tail = (f"subtitles=filename='{_escape_filter_path(ass_path)}':"
                f"fontsdir='/Library/Fonts',format=yuv420p[v]")
    lines.append(f"{burn_label}{tail}")
    return "\n".join(lines)


def assemble_final(spans: list[Span], parts_dir: Path, ffmpeg: str,
                   mix: str, out: str, ass_path: str | None,
                   band_png: str | None = None) -> bool:
    band_input = len(spans) + 1 if band_png else None
    graph = final_filtergraph(spans, ass_path, band_input)
    fscript = parts_dir / "final_filter.txt"
    fscript.write_text(graph, encoding="utf-8")
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-stats"]
    for sp in spans:
        cmd += ["-i", str(parts_dir / f"{sp.sid}.mp4")]
    cmd += ["-i", str(mix)]
    if band_png:
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t",
                f"{spans[-1].end + 1.0:.3f}", "-i", band_png]
    cmd += ["-/filter_complex", str(fscript),
            "-map", "[v]", "-map", f"{len(spans)}:a",
            "-c:v", "libx264", "-crf", "18", "-preset", "slow",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-fps_mode", "cfr",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", "-shortest",
            out]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr[-2500:])
        return False
    return True


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--episode", default="ep01")
    ap.add_argument("--script", default=None)
    ap.add_argument("--timing", default=None)
    ap.add_argument("--assets", default=None)
    ap.add_argument("--mix", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--qc", default=None)
    ap.add_argument("--profile", default="full", choices=["full", "test"])
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--only-scenes", default=None,
                    help="comma separated scene ids to render")
    ap.add_argument("--keep-parts", action="store_true")
    ap.add_argument("--dry-plan", action="store_true")
    ap.add_argument("--ffmpeg", default=None)
    a = ap.parse_args()

    ep = a.episode
    script_path = a.script or f"content/episodes/{ep}/script.json"
    timing_path = a.timing or f"audio/{ep}/timing.json"
    assets_dir = Path(a.assets or f"assets/{ep}")
    mix = a.mix or f"audio/{ep}/mix.wav"
    out = a.out or f"video/{ep}_FINAL.mp4"
    qc_out = a.qc or f"video/{ep}_QC.json"

    ffmpeg, ffprobe = find_toolchain(a.ffmpeg)
    print(f"[toolchain] ffmpeg = {ffmpeg}")

    script = load_json(script_path)
    timing = load_json(timing_path)

    parts_dir = Path(out).parent / f"{ep}_parts"
    text_dir = parts_dir / "text"
    text_dir.mkdir(parents=True, exist_ok=True)

    only = [s for s in (a.only_scenes or "").split(",") if s]
    spans, scenes_used = build_plan(script, timing, assets_dir, text_dir, only or None)

    for sp in spans:
        scene = next(s for s in scenes_used if s["id"] == sp.sid)
        ts = next(s for s in timing["scenes"] if s["id"] == sp.sid)
        if a.dry_plan:
            sp.layers = []
            continue
        scene_layers(sp, scene, ts, assets_dir, text_dir)

    total = spans[-1].end - spans[0].start
    print("\n[plan]")
    for sp in spans:
        pads = f"head={sp.head:.1f} tail={sp.tail:.1f}" if (sp.head or sp.tail) else "cut"
        print(f"  {sp.sid} {sp.section:<8} global {sp.start:7.2f}-{sp.end:7.2f} "
              f"seg_start {sp.seg_start:7.2f} frames {sp.frames:4d} {pads} "
              f"layers {len(sp.layers):2d} cam {sp.cam_motion}")
    print(f"  sections: {spans[0].section}", end="")
    for p, c in zip(spans, spans[1:]):
        if c.section != p.section:
            print(f" | xfade | {c.section}", end="")
    print(f"\n  expected total {total:.3f}s (timing.total="
          f"{timing.get('total_duration')})")

    if a.dry_plan:
        return 0

    # validate inputs exist before spending render time
    for sp in spans:
        if not Path(sp.bg).is_file():
            raise SystemExit(f"background missing: {sp.bg}")

    # segments (parallel)
    t0 = time.time()
    print(f"\n[segments] rendering {len(spans)} scenes with jobs={a.jobs}")
    failures = []
    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as pool:
        futs = {
            pool.submit(render_segment, sp, ffmpeg,
                        parts_dir / f"{sp.sid}_filter.txt",
                        parts_dir / f"{sp.sid}.mp4"): sp
            for sp in spans
        }
        done = 0
        for fut in as_completed(futs):
            sid, ok, err = fut.result()
            done += 1
            print(f"  [{done}/{len(spans)}] {sid}: "
                  f"{'ok' if ok else 'FAILED'}")
            if not ok:
                failures.append((sid, err))
    if failures:
        for sid, err in failures:
            print(f"\n--- {sid} failed ---\n{err}")
        raise SystemExit(1)
    print(f"  segments done in {time.time() - t0:.1f}s")

    # subtitles (global timeline == final timeline by construction)
    ass_path = None
    if any(b.get("text") for sc in scenes_used for b in sc.get("beats", [])):
        events = make_subtitles.build_events(
            {**script, "scenes": scenes_used}, timing)
        ass_path = str(Path(out).parent / f"{Path(out).stem}_subs.ass")
        Path(ass_path).write_text(make_subtitles.render_ass(events),
                                  encoding="utf-8")
        print(f"[subtitles] {len(events)} events -> {ass_path}")

    # subtitle readability band (lead feedback) under the burned text
    band_png = text_dir / "subtitle_band.png"
    from text_overlays import render_subtitle_band
    render_subtitle_band().save(band_png)

    # final assembly
    print(f"\n[final] concat + xfade + band + subs + mux -> {out}")
    if not assemble_final(spans, parts_dir, ffmpeg, mix, out, ass_path,
                          str(band_png)):
        raise SystemExit(1)

    # QC
    qc = qcmod.run_checks(out, timing, a.profile, ffmpeg, ffprobe)
    with open(qc_out, "w", encoding="utf-8") as f:
        json.dump(qc, f, ensure_ascii=False, indent=2)
    qcmod.print_summary(qc)
    print(f"QC json -> {qc_out}")

    if not a.keep_parts:
        shutil.rmtree(parts_dir, ignore_errors=True)
    return 0 if qc["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

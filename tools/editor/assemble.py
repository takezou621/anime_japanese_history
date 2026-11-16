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
               - AI i2v clip, when the scene declares one (visual.ai_clip or
                 video/epNN_ai/manifest.json), is normalized by ai_segments.py
                 to exactly the scene length (trim or ping-pong loop) and used
                 as the background video. Missing/broken clips fall back to
                 the zoompan path and are reported in QC `ai_segments`.
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

from motion import (FPS, MAIN_W, MAIN_H, kenburns_exprs, layer_motion,
                    DEFAULT_MOTION_DUR, speaker_pulse_expr,
                    listener_gate_expr)
from text_overlays import render_overlay, render_quiz_board, render_subtitle_band, STYLES
import make_subtitles
import qc as qcmod
import ai_segments

XFADE_DUR = 0.5          # section crossfade (STYLE_GUIDE / DESIGN)
SUPER_W, SUPER_H = 5760, 3240   # 3x supersampled zoompan input
CONTIG_TOL = 0.02

# character sprite placement (content-aware box-fit, lead spec 2026-11-15):
# scale = min(CHAR_CONTENT_W / content_w, CHAR_CONTENT_H / content_h) so ANY
# sprite layout fits the placement box; the content alpha-bbox bottom lands
# on CHAR_FEET_Y. (full-body Open Peeps: 202x696 content -> scale 1.121,
# character spans y150-930, feet on the ground line)
CHAR_CONTENT_W = 500.0     # visible content width target (px on canvas)
CHAR_CONTENT_H = 780.0     # visible content height target (feet 930, top ~150)
CHAR_SCALE_MAX = 1.5       # absolute safety ceiling (avoid upsampling tiny art)
CHAR_FEET_Y = 930.0


def _bg_path(assets_dir: Path, bg_name: str) -> Path:
    """Prefer Muse's rich backgrounds (scenes_v2) when delivered.

    bg_quiz_board is excluded: the quiz text overlay positions
    (QUIZ_ROW_Y etc.) are calibrated to the original board art.
    """
    if bg_name != "bg_quiz_board":
        v2 = assets_dir / "scenes_v2" / f"{bg_name}.png"
        if v2.is_file():
            return v2
    return assets_dir / "scenes" / f"{bg_name}.png"

_bbox_cache: dict[str, tuple] = {}


def _alpha_bbox(path: str) -> tuple:
    """Alpha-channel bounding box (l, t, r, b) of a PNG, cached."""
    if path not in _bbox_cache:
        from PIL import Image
        with Image.open(path) as im:
            _bbox_cache[path] = im.split()[3].getbbox() or (0, 0, im.width, im.height)
    return _bbox_cache[path]

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
    ai_src: str = ""      # AI i2v clip path (未正規化). 空 = AI無し (kenburns)
    ai_clip: str = ""     # 正規化済みクリップ (prepare 成功後)
    ai_note: str = ""     # prepare 結果 / フォールバック理由 (QC 記録用)
    layers: list[Layer] = field(default_factory=list)


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_plan(script: dict, timing: dict, assets_dir: Path,
               tmp_dir: Path, only: list[str] | None,
               ep: str = "", ai_manifest: dict | None = None
               ) -> tuple[list[Span], list[dict]]:
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
            bg=str(_bg_path(assets_dir, bg_name))))
        clip = ai_segments.resolve_clip(sc, ep, ai_manifest or {})
        if clip:
            spans[-1].ai_src = clip
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
            "sentiment": str(sb.get("sentiment", "") or "").strip(),
            "reaction": str(sb.get("reaction", "") or "").strip(),
            "start": g - seg_start,
            "end": g_end - seg_start,
        })
    return out



# --- T3 (Muse 2026-11-16): lip-sync envelope + talk-mode table ---
# talk variant semantics per (character, expression): "open" = the variant
# shows the open mouth during speech; "closed" = the variant shows the
# closed mouth during intra-speech pauses (base sprite's mouth is open).
_TALK_MODE = {("manabu", ""): "closed", ("manabu", "shocked"): "closed",
              ("manabu", "determined"): "open",
              ("sensei", ""): "open", ("sensei", "determined"): "open"}
_TALK_CACHE: dict = {}


def _speech_windows(wav_path: str) -> list:
    """Speech-active windows [(start, end)] in seconds from a WAV's RMS
    envelope (25 ms window / 10 ms hop, threshold 16% of peak, hangover
    dilation, gaps < 90 ms merged, runs < 60 ms dropped)."""
    if wav_path in _TALK_CACHE:
        return _TALK_CACHE[wav_path]
    import wave as _wave
    from array import array as _array
    out: list = []
    try:
        with _wave.open(wav_path) as w:
            sr = w.getframerate()
            n = w.getnframes()
            ch = w.getnchannels()
            raw = w.readframes(n)
        a = _array("h")
        a.frombytes(raw)
        if ch == 2:
            a = a[::2]
        hop = max(1, sr // 100)
        win = max(1, sr // 40)
        rms = []
        peak = 0.0
        for i in range(0, max(len(a) - win, 0), hop):
            seg = a[i:i + win]
            s = 0.0
            for v in seg:
                s += v * v
            r = (s / len(seg)) ** 0.5
            rms.append(r)
            if r > peak:
                peak = r
        if peak > 0:
            thr = peak * 0.16
            act = [r > thr for r in rms]
            # hangover: dilate by 2 hops (20 ms) on both sides
            dil = list(act)
            for i, v in enumerate(act):
                if v:
                    for k in (i - 2, i - 1, i + 1, i + 2):
                        if 0 <= k < len(dil):
                            dil[k] = True
            runs = []
            i = 0
            while i < len(dil):
                if dil[i]:
                    j = i
                    while j < len(dil) and dil[j]:
                        j += 1
                    runs.append([i * 0.01, j * 0.01])
                    i = j
                else:
                    i += 1
            merged: list = []
            for s, e in runs:
                if merged and s - merged[-1][1] < 0.09:
                    merged[-1][1] = e
                else:
                    merged.append([s, e])
            total = n / sr
            out = [(s, min(e + 0.03, total)) for s, e in merged
                   if e - s >= 0.06]
    except Exception:
        out = []
    _TALK_CACHE[wav_path] = out
    return out


def scene_layers(span: Span, scene: dict, ts: dict, assets_dir: Path,
                 tmp_dir: Path, char_ids: list[str] | None = None,
                 quiz_item: dict | None = None) -> None:
    """Populate span.layers (quiz board -> characters/props -> overlay_text)."""
    beats = _beat_times(scene, ts, span.end, span.seg_start)
    vis = scene.get("visual", {}) or {}
    assets = vis.get("assets", []) or []
    char_ids = [c.lower() for c in (char_ids or [])]

    # quiz board auto-fill (P2-2: ボード空欄問題) — under characters/overlays.
    # Skipped when the writer already provides overlay_text (e.g. quiz_choices)
    has_script_quiz_overlay = any(
        ot.get("style") == "quiz_choices"
        for b in scene.get("beats", [])
        for ot in (b.get("overlay_text") or []))
    if quiz_item and not has_script_quiz_overlay:
        from text_overlays import render_quiz_board
        q = quiz_item.get("q", "")
        chs = [str(c) for c in quiz_item.get("choices", [])][:3]
        ans = quiz_item.get("answer")
        t0b = max(beats[0]["start"] if beats else 0.0, 0.0)
        m0 = layer_motion("fade", t0b, 0.4, MAIN_W / 2, MAIN_H / 2,
                          MAIN_W, MAIN_H)
        f0 = list(m0["filters"])
        ans_i = next((i for i, b in enumerate(scene.get("beats", []))
                      if "正解" in b.get("text", "")), None)
        t_ans = (max(beats[ans_i]["start"], 0.0)
                 if ans_i is not None and ans_i < len(beats) else None)
        if t_ans is not None:
            f0.append(f"fade=t=out:st={max(t_ans - 0.25, 0):.3f}:d=0.25:alpha=1")
        normal_png = tmp_dir / f"{span.sid}_quiz_board.png"
        render_quiz_board(q, chs).save(normal_png)
        span.layers.append(Layer(image=str(normal_png), filters=f0,
                                 x="0", y="0", enable=m0["enable"],
                                 desc=f"quiz_board@{t0b:.2f}s"))
        if t_ans is not None and isinstance(ans, int) and 0 <= ans < len(chs):
            ans_png = tmp_dir / f"{span.sid}_quiz_answer.png"
            render_quiz_board(q, chs, highlight=ans).save(ans_png)
            m1 = layer_motion("fade", t_ans, 0.35, MAIN_W / 2, MAIN_H / 2,
                              MAIN_W, MAIN_H)
            span.layers.append(Layer(image=str(ans_png), filters=m1["filters"],
                                     x="0", y="0",
                                     enable=f"gte(t,{t_ans - 1e-4:.4f})",
                                     desc=f"quiz_answer@{t_ans:.2f}s"))

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

    def _is_char(name: str) -> bool:
        low = name.lower()
        return low.startswith("char_") or any(cid in low for cid in char_ids)

    for a in assets:
        name = a.get("name", "")
        path = assets_dir / "overlay" / f"{name}.png"
        if not path.is_file():
            raise SystemExit(f"overlay asset missing: {path}")
        iw, ih = _image_size(str(path))
        scale = float(a.get("scale", 1.0) or 1.0)
        pos = a.get("pos") or [MAIN_W / 2, MAIN_H / 2]
        px, py = float(pos[0]), float(pos[1])
        if _is_char(name):
            # content-aware box-fit placement: scale fits the content inside
            # the CHAR_CONTENT_W x CHAR_CONTENT_H box (width OR height bound,
            # whichever is smaller), and the content bbox bottom sits on
            # CHAR_FEET_Y regardless of canvas layout.
            # layer_motion treats px/py as the SPRITE center, so convert:
            #   content center x = (sprite left) + content_cx*scale
            #   content bottom y = (sprite top)  + bb*scale
            raw = float(a.get("scale", 1.0) or 1.0)
            bl, bt, br, bb = _alpha_bbox(str(path))
            cw, chh = max(br - bl, 1), max(bb - bt, 1)
            scale = (min(CHAR_CONTENT_W / cw, CHAR_CONTENT_H / chh)
                     if raw == 1.0 else min(raw, CHAR_SCALE_MAX))
            scale = min(scale, CHAR_SCALE_MAX)
            content_cx = (bl + br) / 2.0
        tw, th = max(2, int(round(iw * scale)) // 2 * 2), \
            max(2, int(round(ih * scale)) // 2 * 2)
        if _is_char(name):
            px = px + tw / 2.0 - content_cx * scale   # content center at px
            feet_y = float(a.get("feet_y", CHAR_FEET_Y) or CHAR_FEET_Y)
            py = feet_y + th / 2.0 - bb * scale  # content bottom on line
        t0 = appear_for(name)
        cid = next((c for c in char_ids if c and c in name.lower()), "")
        my_wins = [(b["start"], b["end"]) for b in beats
                   if cid and b.get("speaker") == cid]
        other_wins = [(b["start"], b["end"]) for b in beats
                      if not (cid and b.get("speaker") == cid)]
        dynamics = None
        if cid and (my_wins or other_wins):
            pulse = speaker_pulse_expr(beats, cid)
            gate = listener_gate_expr(other_wins)
            dynamics = (f"(1+{pulse})", f"-4*sin(2*PI*(t)/1.8)*({gate})")
        m = layer_motion(a.get("motion"), t0, DEFAULT_MOTION_DUR,
                         px, py, tw, th, dynamics=dynamics)
        base_layer = Layer(
            image=str(path),
            filters=[f"scale={tw}:{th}:flags=lanczos"] + m["filters"],
            x=m["x"], y=m["y"], enable=m["enable"],
            desc=f"asset:{name}@{t0:.2f}s")
        # T2 sentiment variants + T3 talk/blink (Muse 2026-11-16).
        # Speaker expression from beat.sentiment, listener reaction from
        # beat.reaction. Variant layers need the same scale filter as the
        # base layer (the shipped loop omitted it and never ran).
        clean_filters = list(base_layer.filters)
        clean_x, clean_y = base_layer.x, base_layer.y
        base_enable0 = base_layer.enable  # pre-notch snapshot
        events: list = []  # (beat_index, sentiment) for THIS character
        variant_layers: dict = {}
        if cid:
            for bi2, b in enumerate(beats):
                if b.get("speaker") == cid and b.get("sentiment"):
                    events.append((bi2, b["sentiment"]))
                elif (b.get("speaker") and b.get("speaker") != cid
                      and b.get("reaction")):
                    events.append((bi2, b["reaction"]))

            # Gesture poses have a different silhouette: hide the base
            # mid-window so no double body appears (variant crossfades
            # over the edges).
            _gw = []
            for bi2, sent in events:
                if sent in ("pointing", "raise"):
                    b = beats[bi2]
                    ws, we = max(b["start"], 0.0), min(b["end"], span.dur)
                    if we - ws > 0.3:
                        _gw.append((ws + 0.06, we - 0.06))
            if _gw:
                _not = "+".join(f"between(t,{a2:.3f},{b2:.3f})"
                                for a2, b2 in _gw)
                base_layer.enable = f"({base_layer.enable})*not({_not})"

            def _variant_path(sent):
                # file naming (lead 2026-11-15): char_<name>_expr_<emotion>.png
                p = assets_dir / "overlay" / f"{name}_expr_{sent}.png"
                if not p.is_file():  # back-compat: char_<name>_<sent>.png
                    p = assets_dir / "overlay" / f"{name}_{sent}.png"
                return p if p.is_file() else None

        span.layers.append(base_layer)
        if cid:
            for bi2, sent in events:
                vpath = _variant_path(sent)
                if vpath is None:
                    continue
                b = beats[bi2]
                ws, we = max(b["start"], 0.0), min(b["end"], span.dur)
                if we - ws < 0.15:
                    continue
                # Crossfade on the variant layer itself (in over the
                # identical-geometry base, out at the end). Chained
                # fade out/in pairs on the BASE permanently kill its
                # alpha (fade filters multiply), so the base is never
                # faded.
                # Clone the base transform verbatim (filters/x/y incl.
                # entrance slide, speaker pulse and idle bob). A static
                # rest transform here made the variant diverge from the
                # moving base: a second figure at entrances and a
                # full-body ghost during expression windows (user
                # report 2026-11-16, s01 t=5.5s). Only the image, the
                # enable window and the crossfade fades differ.
                w0 = max(ws - 0.12, 0.0)
                w1 = min(we + 0.12, span.dur)
                venable = (f"({base_enable0})"
                           f"*between(t,{w0:.3f},{w1:.3f})")
                vfilters = (list(clean_filters)
                            + [f"fade=t=in:st={w0:.3f}:d=0.3:alpha=1",
                               f"fade=t=out:st={max(we - 0.18, 0):.3f}"
                               f":d=0.3:alpha=1"])
                span.layers.append(Layer(
                    image=str(vpath), filters=vfilters,
                    x=clean_x, y=clean_y, enable=venable,
                    desc=f"variant:{sent}@{ws:.2f}s"))
                variant_layers[(bi2, sent)] = (
                    clean_filters, clean_x, clean_y, venable)

            def _expr_of_beat(bi2):
                for bj, s2 in events:
                    if bj == bi2:
                        return s2
                return ""

            def _seg_transform(bi2, sent):
                # (filters, x, y, parent_enable): derived layers clone
                # their parent's transform AND gate on its enable, so
                # they can never diverge from or precede the parent.
                if sent and (bi2, sent) in variant_layers:
                    return variant_layers[(bi2, sent)]
                return (clean_filters, clean_x, clean_y, base_enable0)

            audio_dir = assets_dir.parent.parent / "audio" / assets_dir.name
            # --- lip-sync layers (envelope-driven mouth alternation) ---
            for bi2, b in enumerate(beats):
                if b.get("speaker") != cid:
                    continue
                sent = _expr_of_beat(bi2)
                mode = _TALK_MODE.get((cid, sent))
                if not mode:
                    continue
                tname = (f"{name}_expr_{sent}_talk.png" if sent
                         else f"{name}_talk.png")
                tpath = assets_dir / "overlay" / tname
                if not tpath.is_file():
                    continue
                wav = audio_dir / "narration" / f"{span.sid}_b{bi2:02d}.wav"
                speech = _speech_windows(str(wav))
                if not speech:
                    continue
                bs, be = max(b["start"], 0.0), min(b["end"], span.dur)
                wins = []
                if mode == "open":
                    for s2, e2 in speech:
                        wins.append((bs + s2, min(bs + e2, be)))
                else:  # closed: complement of speech within the beat
                    cur = bs
                    for s2, e2 in speech:
                        a2, b2 = bs + s2, min(bs + e2, be)
                        if a2 - cur >= 0.07:
                            wins.append((cur, a2))
                        cur = max(cur, b2)
                    if be - cur >= 0.07:
                        wins.append((cur, be))
                wins = [(s2, e2) for s2, e2 in wins if e2 - s2 >= 0.05]
                if not wins:
                    continue
                tf, tx, ty, pen = _seg_transform(bi2, sent)
                en = "+".join(f"between(t,{s2:.3f},{e2:.3f})"
                              for s2, e2 in wins[:140])
                en = f"({pen})*({en})"
                span.layers.append(Layer(
                    image=str(tpath), filters=list(tf), x=tx, y=ty,
                    enable=en, desc=f"talk:{sent or 'base'}@{bs:.2f}s"))
            # --- blink layers (seeded, follows the active expression) ---
            import random as _random
            rng = _random.Random(f"{span.sid}:{cid}")
            blink_groups: dict = {}
            t = rng.uniform(0.9, 2.0)
            while t < span.dur - 0.25:
                mid = t + 0.065
                bidx = next((bi2 for bi2, b in enumerate(beats)
                             if b["start"] <= mid < b["end"]), -1)
                sent = _expr_of_beat(bidx) if bidx >= 0 else ""
                if sent != "laugh":
                    blink_groups.setdefault((bidx, sent), []).append(
                        (t, t + 0.13))
                t += rng.uniform(2.2, 4.6)
            for (bidx, sent), wins in blink_groups.items():
                bname = (f"{name}_expr_{sent}_blink.png" if sent
                         else f"{name}_blink.png")
                bpath = assets_dir / "overlay" / bname
                if not bpath.is_file():
                    continue
                tf, tx, ty, pen = _seg_transform(bidx, sent)
                en = "+".join(f"between(t,{s2:.3f},{e2:.3f})"
                              for s2, e2 in wins)
                en = f"({pen})*({en})"
                span.layers.append(Layer(
                    image=str(bpath), filters=list(tf), x=tx, y=ty,
                    enable=en, desc=f"blink:{sent or 'base'}x{len(wins)}"))

    # overlay_text entries live on beats and appear at the beat time;
    # they persist for max(beat, 3s) capped at scene end, then fade out 0.4s
    scene_end_local = span.end - span.seg_start
    # T9: exam_points[].importance drives keyword_card colour (high=朱/赤)
    exam_imps = [str(ep.get("importance", "")).strip().lower()
                 for ep in scene.get("exam_points", [])
                 if isinstance(ep, dict)]
    kc_index = 0
    for i, b in enumerate(scene.get("beats", [])):
        t0b = beats[i]["start"] if i < len(beats) else 0.0
        beat_end_local = beats[i]["end"] if i < len(beats) else t0b + 1.0
        for k, ot in enumerate(b.get("overlay_text") or []):
            style = ot.get("style", "title_main")
            if style == "keyword_card":
                imp = str(ot.get("importance", "")).strip().lower() or (
                    exam_imps[kc_index] if kc_index < len(exam_imps) else "")
                if imp == "high":
                    style = "keyword_card_red"
            ot = dict(ot, style=style)  # swap propagates to render_overlay
            if style == "keyword_card" or style == "keyword_card_red":
                kc_index += 1
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
            t_end = min(max(beat_end_local, t0 + 3.0), scene_end_local)
            if ot.get("hold"):
                t_end = min(t0 + float(ot["hold"]), scene_end_local)
            if t_end < scene_end_local - 1e-3:
                m["filters"].append(
                    f"fade=t=out:st={t_end - 0.4:.3f}:d=0.4:alpha=1")
            span.layers.append(Layer(
                image=str(png),
                filters=m["filters"],
                x=m["x"], y=m["y"], enable=m["enable"],
                desc=f"text:{style}@{t0:.2f}s-out@{t_end:.2f}s"))
    # drop None filters
    for L in span.layers:
        L.filters = [f for f in L.filters if f]


# ---------------------------------------------------------------------------
# segment rendering
# ---------------------------------------------------------------------------

def segment_filtergraph(span: Span,
                        layer_inputs: list[int] | None = None) -> str:
    if layer_inputs is None:
        layer_inputs = list(range(1, len(span.layers) + 1))
    from collections import Counter
    use = Counter(layer_inputs)
    split_ready: set[int] = set()
    if span.ai_clip:
        # AI i2v クリップは ai_segments.py が 1920x1080@30 CFR に正規化済み
        parts = ["[0:v]settb=AVTB,format=yuv420p,setsar=1[bg0];"]
    else:
        z, x, y = kenburns_exprs(span.cam_motion, span.cam_intensity, span.frames)
        parts = [
            f"[0:v]scale={SUPER_W}:{SUPER_H}:flags=lanczos,"
            f"zoompan=z='{z}':x='{x}':y='{y}':d={span.frames}:"
            f"s={MAIN_W}x{MAIN_H}:fps={FPS},settb=AVTB,format=yuv420p,setsar=1[bg0];"
        ]
    cur = "bg0"
    seen: Counter = Counter()
    for i, (L, k) in enumerate(zip(span.layers, layer_inputs), start=1):
        if use[k] > 1:
            if k not in split_ready:
                outs = "".join(f"[in{k}_{n}]" for n in range(use[k]))
                parts.append(f"[{k}:v]format=rgba,split={use[k]}{outs};")
                split_ready.add(k)
            src_label = f"in{k}_{seen[k]}"
            seen[k] += 1
        else:
            src_label = f"{k}:v"
        chain = f"[{src_label}]format=rgba"
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


def render_segment(span: Span, ffmpeg: str, ffprobe: str, filter_path: Path,
                   out_path: Path) -> tuple[str, bool, str]:
    if span.ai_src and not span.ai_clip:
        # AI クリップをシーン長ちょうどに正規化 (失敗時は kenburns にフォールバック)
        prepared = filter_path.parent / f"{span.sid}_ai.mp4"
        try:
            info = ai_segments.prepare_ai_clip(ffmpeg, span.ai_src, span.frames,
                                               prepared, ffprobe)
            span.ai_clip = info["path"]
            span.ai_note = (f"{info['mode']} {info['in_duration']:.1f}s->"
                            f"{info['out_duration']:.1f}s")
            print(f"  [ai] {span.sid}: {span.ai_note} ({span.ai_src})")
        except Exception as err:  # noqa: BLE001 — クリップ1本の失敗で番組を落とさない
            span.ai_note = f"fallback: {err}"
            span.ai_src = ""
            print(f"  [ai][warn] {span.sid}: {span.ai_note}")
    src = span.ai_clip or span.bg
    # 同一画像のレイヤーは 1 入力に統合 (ffmpeg の looped-image 入力が
    # 40+ 並ぶと framesync がデッドロックするため + 高速化)
    uniq: dict[str, int] = {}
    layer_inputs: list[int] = []
    for L in span.layers:
        key = str(L.image)
        if key not in uniq:
            uniq[key] = len(uniq) + 1  # [0] は背景
        layer_inputs.append(uniq[key])
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", src]
    for key in uniq:
        cmd += ["-loop", "1", "-framerate", str(FPS),
                "-t", f"{span.dur + 0.5:.3f}", "-i", key]
    script = segment_filtergraph(span, layer_inputs)
    filter_path.write_text(script, encoding="utf-8")
    cmd += [
        "-/filter_complex", str(filter_path),
        "-map", "[v]",
        # セグメントは中間素材 (最終muxでCBR再エンコード) — veryfastで十分
        "-c:v", "libx264", "-crf", "14", "-preset", "veryfast",
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
            # raw file input: normalize timebase to match concat outputs
            # (mp4 demuxer tb 1/15360 vs concat AVTB 1/1000000 breaks xfade)
            lines.append(f"[{idxs[0]}:v]settb=AVTB[G{gi}];")
            group_labels.append(f"[G{gi}]")
            continue
        ins = "".join(f"[{i}:v]" for i in idxs)
        lines.append(f"{ins}concat=n={len(idxs)}:v=1:a=0,settb=AVTB[G{gi}];")
        group_labels.append(f"[G{gi}]")

    cur = group_labels[0]
    if len(groups) > 1:
        # xfade offsets live on the LOCAL timeline of the rendered subset
        # (--only-scenes subsets are not contiguous in global time)
        content_before = 0.0
        for k in range(1, len(groups)):
            content_before += sum(spans[i].end - spans[i].start
                                  for i in groups[k - 1])
            offset = content_before - XFADE_DUR
            if offset <= 0:
                raise SystemExit(
                    f"xfade offset <= 0 at boundary before "
                    f"{spans[groups[k][0]].sid} ({offset:.3f}s); scene too short")
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


def estimate_final_duration(spans: list[Span]) -> float:
    """Expected final duration (matches final_filtergraph's construction).

    Final length = last xfade offset + last group's segment durations, where
    offsets are on the subset-local timeline. For a single group (no xfades)
    this is just the sum of segment durations.
    """
    groups: list[list[int]] = []
    for i, sp in enumerate(spans):
        if i == 0 or spans[i - 1].section != sp.section:
            groups.append([i])
        else:
            groups[-1].append(i)
    if len(groups) == 1:
        return sum(spans[i].dur for i in groups[0])
    content_before = sum(spans[i].end - spans[i].start
                         for gi in groups[:-1] for i in gi)
    offset_last = content_before - XFADE_DUR
    return offset_last + sum(spans[i].dur for i in groups[-1])


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
    # master encode spec (lead 2026-11-15): 35Mbps floor + bt709 + TP limiter
    # (minrate=35M keeps measured bitrate >= target on static animation)
    # (alimiter 0.94 = -0.55dBTP ceiling guards against AAC TP overshoot)
    cmd += ["-/filter_complex", str(fscript),
            "-map", "[v]", "-map", f"{len(spans)}:a",
            "-c:v", "libx264", "-preset", "slow",
            "-b:v", "35M", "-minrate", "35M",
            "-maxrate", "35M", "-bufsize", "4400k",
            "-x264-params", "nal-hrd=cbr:filler=1",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-fps_mode", "cfr",
            "-colorspace", "bt709", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-color_range", "tv",
            "-c:a", "aac", "-b:a", "192k",
            "-af", "alimiter=limit=0.75:level=false:attack=5:release=50",
            "-movflags", "+faststart",
            # explicit -t (NOT -shortest): ffmpeg -shortest can stop ~0.7s
            # before the true shortest-stream end (packet timing quirk),
            # truncating the video. The plan duration is authoritative.
            "-t", f"{estimate_final_duration(spans):.3f}",
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
    ap.add_argument("--no-quiz-overlay", action="store_true",
                    help="disable quiz board auto-fill (P2-2)")
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

    ai_manifest = ai_segments.load_manifest(ep)
    if ai_manifest:
        print(f"[ai] manifest: {len(ai_manifest)} clip(s) "
              f"({ai_segments.manifest_path(ep)})")

    parts_dir = Path(out).parent / f"{ep}_parts"
    text_dir = parts_dir / "text"
    text_dir.mkdir(parents=True, exist_ok=True)

    only = [s for s in (a.only_scenes or "").split(",") if s]
    spans, scenes_used = build_plan(script, timing, assets_dir, text_dir,
                                    only or None, ep=ep, ai_manifest=ai_manifest)

    char_ids = [c.get("id", "") for c in script.get("characters", [])]
    quiz_list = script.get("quiz", []) or []
    quiz_ord = 0
    for sp in spans:
        scene = next(s for s in scenes_used if s["id"] == sp.sid)
        ts = next(s for s in timing["scenes"] if s["id"] == sp.sid)
        if a.dry_plan:
            sp.layers = []
            continue
        quiz_item = None
        if sp.section == "quiz" and not a.no_quiz_overlay:
            if quiz_ord < len(quiz_list):
                quiz_item = quiz_list[quiz_ord]
            quiz_ord += 1
        scene_layers(sp, scene, ts, assets_dir, text_dir, char_ids, quiz_item)

    total = spans[-1].end - spans[0].start
    print("\n[plan]")
    for sp in spans:
        pads = f"head={sp.head:.1f} tail={sp.tail:.1f}" if (sp.head or sp.tail) else "cut"
        ai_tag = f"ai:{Path(sp.ai_src).name}" if sp.ai_src else ""
        print(f"  {sp.sid} {sp.section:<8} global {sp.start:7.2f}-{sp.end:7.2f} "
              f"seg_start {sp.seg_start:7.2f} frames {sp.frames:4d} {pads} "
              f"layers {len(sp.layers):2d} cam {sp.cam_motion} {ai_tag}")
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
        if sp.ai_src and not Path(sp.ai_src).is_file():
            print(f"[ai][warn] clip missing -> kenburns fallback: "
                  f"{sp.sid} {sp.ai_src}")

    # segments (parallel)
    t0 = time.time()
    print(f"\n[segments] rendering {len(spans)} scenes with jobs={a.jobs}")
    failures = []
    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as pool:
        # 再開サポート: 1MB超の完成パーツがあるセグメントはスキップ
        # (作業休止/再開時に完成済みシーンを再利用する)
        todo = []
        for sp in spans:
            part = parts_dir / f"{sp.sid}.mp4"
            if part.is_file() and part.stat().st_size > 1_000_000:
                print(f"  [skip] {sp.sid}: part exists "
                      f"({part.stat().st_size // 1_000_000}MB)")
                continue
            todo.append(sp)
        futs = {
            pool.submit(render_segment, sp, ffmpeg, ffprobe,
                        parts_dir / f"{sp.sid}_filter.txt",
                        parts_dir / f"{sp.sid}.mp4"): sp
            for sp in todo
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
    render_subtitle_band().save(band_png)

    # final assembly
    print(f"\n[final] concat + xfade + band + subs + mux -> {out}")
    if not assemble_final(spans, parts_dir, ffmpeg, mix, out, ass_path,
                          str(band_png)):
        raise SystemExit(1)

    # QC (partials check against the rendered subset's expected duration)
    qc_expected = estimate_final_duration(spans) if only else None
    qc = qcmod.run_checks(out, timing, a.profile, ffmpeg, ffprobe,
                          expected=qc_expected)
    ai_report = [
        {"sid": sp.sid, "mode": "ai" if sp.ai_clip else "fallback",
         "clip": sp.ai_src or "", "detail": sp.ai_note}
        for sp in spans if (sp.ai_src or sp.ai_clip or sp.ai_note)]
    if ai_report:
        qc["ai_segments"] = ai_report
        used = sum(1 for r in ai_report if r["mode"] == "ai")
        print(f"[ai] segments: {used} AI / {len(ai_report) - used} fallback")
    with open(qc_out, "w", encoding="utf-8") as f:
        json.dump(qc, f, ensure_ascii=False, indent=2)
    qcmod.print_summary(qc)
    print(f"QC json -> {qc_out}")

    if not a.keep_parts:
        shutil.rmtree(parts_dir, ignore_errors=True)
    return 0 if qc["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

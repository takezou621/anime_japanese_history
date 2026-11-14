# -*- coding: utf-8 -*-
"""ffmpeg expression builders for the editor pipeline (tools/editor).

Conventions
-----------
- Expressions are evaluated in SEGMENT-LOCAL time ``t`` (seconds). The caller
  converts timing.json global times via ``local = global - segment_start``.
- Main canvas is always 1920x1080 @30fps CFR; layer ``pos`` is the CENTER of
  the layer in canvas coordinates.
- All numeric constants are baked from Python as formatted literals, so the
  generated filtergraph never contains bare Python values.

Style references: docs/03_STYLE_GUIDE.md (モーション原則: 静止3秒禁止 / kenburns
必須 / 登場モーション 0.4-0.6s ease-out / pop_in overshoot 5%).
"""
from __future__ import annotations

import math

MAIN_W, MAIN_H = 1920, 1080
FPS = 30

DEFAULT_MOTION_DUR = 0.5  # STYLE_GUIDE: 0.4-0.6s


def clamp01(p: str) -> str:
    """ffmpeg expression that clamps progress to [0, 1]."""
    return f"min(max({p},0),1)"


def progress(t0: float, dur: float) -> str:
    """clamped progress p of a motion starting at local t0, lasting dur."""
    return clamp01(f"(t-{t0:.3f})/{max(dur, 1e-3):.3f}")


def ease_out_cubic(p: str) -> str:
    return f"(1-pow(1-{p},3))"


# ---------------------------------------------------------------------------
# background camera (zoompan)
# ---------------------------------------------------------------------------

def kenburns_exprs(motion: str | None, intensity, frames: int):
    """Return (zoom, x, y) expressions for a zoompan kenburns camera.

    zoompan is fed a 3x supersampled background (5760x3240) so sub-pixel
    camera moves stay jitter-free at 1920x1080 output. `on` is the output
    frame index inside zoompan.
    """
    try:
        q = float(intensity) if intensity is not None else 1.0
    except (TypeError, ValueError):
        q = 1.0
    q = max(0.2, min(q, 3.0))

    if frames <= 1:  # degenerate, keep camera moving rule anyway
        return f"{1 + 0.06 * q:.4f}", "(iw-iw/zoom)/2", "(ih-ih/zoom)/2"

    n = frames - 1
    p = f"(on/{n})"
    m = (motion or "kenburns_in").lower()

    if m == "kenburns_out":
        zoom = f"min(1+{0.06 * q:.4f}*(1-{p}),1.30)"
        x = f"(iw-iw/zoom)/2-0.02*iw*{p}"
        y = "(ih-ih/zoom)/2"
    elif m == "pan_l":
        zoom = f"{1 + 0.08 * q:.4f}"
        x = f"(iw-iw/zoom)*(1-{p})"
        y = "(ih-ih/zoom)/2"
    elif m == "pan_r":
        zoom = f"{1 + 0.08 * q:.4f}"
        x = f"(iw-iw/zoom)*{p}"
        y = "(ih-ih/zoom)/2"
    else:  # kenburns_in (default)
        zoom = f"min(1+{0.06 * q:.4f}*{p},1.30)"
        x = f"(iw-iw/zoom)/2+0.02*iw*{p}"
        y = "(ih-ih/zoom)/2"
    return zoom, x, y


# ---------------------------------------------------------------------------
# layer motions (character / prop / overlay_text PNGs)
# ---------------------------------------------------------------------------

def layer_motion(motion: str | None, t0: float, dur: float, px: float, py: float,
                 tw: int, th: int,
                 dynamics: tuple[str, str] | None = None) -> dict:
    """Build per-layer filter pieces for an appear motion.

    Returns dict with:
      filters: list of filter strings applied to the (rgba) layer input
      x, y   : overlay position expressions (may reference w/h = layer size)
      enable : overlay enable expression (gte(t, t0))
    """
    m = (motion or "fade").lower()
    dur = min(max(dur, 0.3), 0.8)  # STYLE_GUIDE: 0.4-0.6s, tolerate clamping
    p = progress(t0, dur)
    # T2 dynamics: (P_expr, bob_str) — speaker pulse + listener bob
    P_expr = dynamics[0] if dynamics else "1"
    bob = dynamics[1] if dynamics else ""
    left, top = px - tw / 2.0, py - th / 2.0
    out = {
        "filters": [],
        "x": f"{left:.1f}",
        "y": f"{top:.1f}",
        "enable": f"gte(t,{max(t0, 0.0) - 1e-4:.4f})",
    }

    if m in ("pop_in", "zoom_in"):
        if m == "pop_in":  # ease-out with ~5% overshoot, then settle
            s = (f"if(lt({p},0.7),1.05*(1-pow(1-({p}/0.7),3)),"
                 f"1.05-0.05*(1-pow(1-(({p}-0.7)/0.3),3)))")
        else:  # zoom_in: 0.6 -> 1.0 ease-out
            s = f"0.6+0.4*{ease_out_cubic(p)}"
        # clamp scale away from 0 so the scale filter is valid even while
        # the layer is still hidden (enable hides it until t0)
        s = f"max({s},0.05)"
        F = f"({s})*({P_expr})"
        out["filters"].append(
            f"scale=w='trunc(iw*{F}/2)*2':h='trunc(ih*{F}/2)*2':eval=frame")
        # center-x anchoring; feet line (py + th/2) stays fixed under F
        out["x"] = f"{px:.1f}-w/2"
        out["y"] = f"{py + th / 2:.1f}-h*{F}/2{bob}"
    elif m == "slide_in_left":
        x0 = -tw - 24.0
        out["x"] = (f"({x0:.1f}+({left:.1f}-{x0:.1f})*{ease_out_cubic(p)})"
                    f"-w*(({P_expr})-1)/2")
        out["y"] = f"{top:.1f}-h*(({P_expr})-1)/2{bob}"
        out["filters"].append(f"fade=t=in:st={t0:.3f}:d={dur:.3f}:alpha=1")
    elif m == "slide_in_right":
        x0 = MAIN_W + 24.0
        out["x"] = (f"({x0:.1f}+({left:.1f}-{x0:.1f})*{ease_out_cubic(p)})"
                    f"-w*(({P_expr})-1)/2")
        out["y"] = f"{top:.1f}-h*(({P_expr})-1)/2{bob}"
        out["filters"].append(f"fade=t=in:st={t0:.3f}:d={dur:.3f}:alpha=1")
    elif m in ("slide_up", "slide_in_bottom"):
        y0 = MAIN_H + 24.0
        out["y"] = (f"({y0:.1f}+({top:.1f}-{y0:.1f})*{ease_out_cubic(p)})"
                    f"-h*(({P_expr})-1)/2{bob}")
        out["x"] = f"{left:.1f}-w*(({P_expr})-1)/2"
        out["filters"].append(f"fade=t=in:st={t0:.3f}:d={dur:.3f}:alpha=1")
    elif m == "fade_up":
        out["y"] = (f"({top:.1f}+48*(1-{ease_out_cubic(p)})"
                    f")-h*(({P_expr})-1)/2{bob}")
        out["x"] = f"{left:.1f}-w*(({P_expr})-1)/2"
        out["filters"].append(f"fade=t=in:st={t0:.3f}:d={dur:.3f}:alpha=1")
    else:  # fade (default)
        out["filters"].append(f"fade=t=in:st={t0:.3f}:d={dur:.3f}:alpha=1")
        out["x"] = f"{left:.1f}-w*(({P_expr})-1)/2"
        out["y"] = f"{top:.1f}-h*(({P_expr})-1)/2{bob}"
    return out


# ---------------------------------------------------------------------------
# character dynamics (T2): listener bob / speaker pulse / sentiment windows
# ---------------------------------------------------------------------------

def beat_windows(beats: list[dict], speaker: str) -> list[tuple[float, float]]:
    """Beat windows [start, end] belonging to `speaker` (local seconds)."""
    return [(b["start"], b["end"]) for b in beats
            if speaker and b.get("speaker") == speaker]


def listener_gate_expr(windows: list[tuple[float, float]]) -> str:
    """Expression = 1 while ANY of the windows is active, else 0."""
    if not windows:
        return "0"
    terms = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in windows)
    return f"min(1,{terms})"


def speaker_pulse_expr(beats: list[dict], speaker: str,
                       amount: float = 0.04, decay: float = 0.5) -> str:
    """Expression for a gentle scale pulse right after each of MY beats.
    Returns the delta (0..1 scale units); caller adds 1. Clamped to 1."""
    if not beats:
        return "0"
    terms = "+".join(f"max(0,1-(t-{b['start']:.3f})/{decay:.2f})"
                     for b in beats)
    return f"min(1,{terms})*{amount:.3f}"


def char_dynamics(windows_my: list[tuple[float, float]],
                  windows_other: list[tuple[float, float]],
                  base_left: float, base_top: float,
                  tw: int, th: int) -> dict:
    """Build bob/pulse filters + compensated x/y for a character layer.

    - listening bob: +/-4px vertical sine while the OTHER char speaks
    - speaker pulse: scale up to +4% right after MY beats, anchored so the
      feet (content bottom) stay planted
    Returns dict(filters=[scale_filter], x=..., y=...) — merge into the
    layer's x/y expressions (they must reference P via the returned consts).
    """
    pulse_terms = "+".join(f"max(0,1-(t-{s:.3f})/0.50)"
                           for s, _e in windows_my)
    P = (f"(1+0.04*min(1,{pulse_terms}))" if pulse_terms else "(1)")
    gate = listener_gate_expr(windows_other)
    bob = f"-4*sin(2*PI*(t)/1.8)*({gate})" if gate != "0" else ""
    # scale filter around the sprite centre, feet compensated:
    #   top' = top - (P-1)*th   left' = left - (P-1)*tw/2
    scale_f = (f"scale=w='trunc(iw*{P}/2)*2':h='trunc(ih*{P}/2)*2'"
               ":eval=frame")
    x = f"{base_left:.1f}-({P}-1)*{tw / 2:.1f}"
    y = f"{base_top:.1f}-({P}-1)*{th:.1f}{bob}"
    return {"filters": [scale_f], "x": x, "y": y}

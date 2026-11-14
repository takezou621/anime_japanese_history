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
                 tw: int, th: int) -> dict:
    """Build per-layer filter pieces for an appear motion.

    Returns dict with:
      filters: list of filter strings applied to the (rgba) layer input
      x, y   : overlay position expressions (may reference w/h = layer size)
      enable : overlay enable expression (gte(t, t0))
    """
    m = (motion or "fade").lower()
    dur = min(max(dur, 0.3), 0.8)  # STYLE_GUIDE: 0.4-0.6s, tolerate clamping
    p = progress(t0, dur)
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
        out["filters"].append(
            f"scale=w='trunc(iw*({s})/2)*2':h='trunc(ih*({s})/2)*2':eval=frame")
        out["x"] = f"{px:.1f}-(w-{tw})/2"
        out["y"] = f"{py:.1f}-(h-{th})/2"
    elif m == "slide_in_left":
        x0 = -tw - 24.0
        out["x"] = f"{x0:.1f}+({left:.1f}-{x0:.1f})*{ease_out_cubic(p)}"
    elif m == "slide_in_right":
        x0 = MAIN_W + 24.0
        out["x"] = f"{x0:.1f}+({left:.1f}-{x0:.1f})*{ease_out_cubic(p)}"
    elif m in ("slide_up", "slide_in_bottom"):
        y0 = MAIN_H + 24.0
        out["y"] = f"{y0:.1f}+({top:.1f}-{y0:.1f})*{ease_out_cubic(p)}"
    elif m == "fade_up":
        out["y"] = f"{top:.1f}+48*(1-{ease_out_cubic(p)})"
        out["filters"].append(f"fade=t=in:st={t0:.3f}:d={dur:.3f}:alpha=1")
    else:  # fade (default)
        out["filters"].append(f"fade=t=in:st={t0:.3f}:d={dur:.3f}:alpha=1")
    return out

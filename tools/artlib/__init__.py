"""artlib — アニメ日本史ラボ 用イラストライブラリ (Pillow + numpy).

使い方:
    sys.path.insert(0, <repo>/tools)
    from artlib import Canvas, nature, props, character, ui
"""
from .canvas import (Canvas, Layer, G, almond_pts, as_rgb, blob_pts, cbez,
                     dots_pattern, gradient, load_font, paste_masked, qbez,
                     radial, render_ov, save, shade, speckle, sublayer, tint,
                     with_alpha)
from . import palette, nature, props, character, ui

__all__ = [
    "Canvas", "Layer", "G", "almond_pts", "as_rgb", "blob_pts", "cbez",
    "dots_pattern", "gradient", "load_font", "paste_masked", "qbez", "radial",
    "render_ov", "save", "shade", "speckle", "sublayer", "tint", "with_alpha",
    "palette", "nature", "props", "character", "ui",
]

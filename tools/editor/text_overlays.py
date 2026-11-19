# -*- coding: utf-8 -*-
"""overlay_text PNG renderer (STYLE_GUIDE §overlay_text 定義).

Renders ``beats[].overlay_text`` entries from script.json into transparent
RGBA PNGs; assemble.py overlays them onto scene segments with the appear
motion defined per style.

Style table (docs/03_STYLE_GUIDE.md):

===================  ======================================================
title_main           72px NotoBlack, 白文字 + 朱フチ, 中央上1/3, fade_up
era_badge            角丸カプセル (藍地に白 44px), 左上, slide_in_left
keyword_card         白角丸カード + 藍枠, 64px, pop_in
exam_banner          朱バナー 白 56px, slide_up
year_number          96px 山吹 + 濃フチ, zoom_in
subtitle             (字幕は make_subtitles.py の ASS 焼き込みが本体)
===================  ======================================================

Geometry contract: rendered PNG is 2x supersampled then downscaled; ``pos``
(when given in the script entry) is the CENTER of the card in 1920x1080
canvas coordinates, matching visual.assets ``pos`` semantics.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path("/Library/Fonts")
FONT_FILES = {
    "Black": "NotoSansJP-Black.otf",
    "Bold": "NotoSansJP-Bold.otf",
    "Regular": "NotoSansJP-Regular.otf",
}
SS = 2  # supersampling factor
CANVAS_W, CANVAS_H = 1920, 1080

# palette (docs/03_STYLE_GUIDE.md)
AI = "#2b4a8b"        # メイン 藍
SHU = "#e8543f"       # アクセント 朱
YAMABUKI = "#f5b942"  # ハイライト 山吹
WHITE_UI = "#fffdf7"  # 温かい白
TEXT_DARK = "#26282e"

STYLES: dict[str, dict] = {
    "title_main": dict(font="Black", size=72, fill="#ffffff", stroke=SHU,
                       stroke_w=6, shadow=True, default_motion="fade_up",
                       pad=(44, 22), wrap=20, radius=0, bg=None,
                       default_pos=lambda w, h: (CANVAS_W / 2, 330)),
    "era_badge": dict(font="Bold", size=44, fill="#ffffff", bg=AI, border=None,
                      radius=None, default_motion="slide_in_left",
                      pad=(38, 16), wrap=16, shadow=False,
                      default_pos=lambda w, h: (80 + w / 2, 104)),
    "keyword_card": dict(font="Bold", size=64, fill=AI, bg=WHITE_UI,
                         border=(AI, 6), radius=28, min_size=(520, 140),
                         default_motion="pop_in", pad=(48, 26), wrap=12,
                         shadow=False,
                         default_pos=lambda w, h: (CANVAS_W / 2, 560)),
    "keyword_card_red": dict(font="Bold", size=64, fill=SHU, bg=WHITE_UI,
                             border=(SHU, 6), radius=28, min_size=(520, 140),
                             default_motion="pop_in", pad=(48, 26), wrap=12,
                             shadow=False,
                             default_pos=lambda w, h: (CANVAS_W / 2, 560)),
    # ending 画面 (T9/lead 2026-11-15): 次回予告カード + 登録導線テロップ
    "next_episode_card": dict(font="Black", size=44, fill=AI, bg=WHITE_UI,
                              border=(AI, 5), radius=20, min_size=(760, 150),
                              default_motion="pop_in", pad=(50, 30), wrap=22,
                              shadow=False,
                              default_pos=lambda w, h: (CANVAS_W / 2, 400)),
    "subscribe_banner": dict(font="Black", size=44, fill="#ffffff", bg=SHU,
                             border=None, radius=None, default_motion="fade",
                             pad=(56, 22), wrap=24, shadow=False,
                             default_pos=lambda w, h: (CANVAS_W / 2, 170)),
    "quiz_choices": dict(font="Bold", size=44, fill=TEXT_DARK, bg=WHITE_UI,
                         border=(AI, 5), radius=20, min_size=(1000, 300),
                         split_slash=True, default_motion="pop_in",
                         pad=(56, 34), wrap=20, shadow=False,
                         # board area of bg_quiz_board (rows y 300/485/670)
                         default_pos=lambda w, h: (950, 490)),
    "exam_banner": dict(font="Black", size=56, fill="#ffffff", bg=SHU,
                        border=None, radius=16, default_motion="slide_up",
                        pad=(56, 20), wrap=26, shadow=False,
                        # lead v2: bottom-anchored banners must stay above the
                        # subtitle band (band top ≈ 0.86h) -> center at 0.70h
                        default_pos=lambda w, h: (CANVAS_W / 2,
                                                  int(CANVAS_H * 0.70))),
    "year_number": dict(font="Black", size=96, fill=YAMABUKI, stroke=TEXT_DARK,
                        stroke_w=5, shadow=True, default_motion="zoom_in",
                        pad=(28, 14), wrap=10, radius=0, bg=None,
                        default_pos=lambda w, h: (CANVAS_W / 2, 420)),
    "subtitle": dict(font="Bold", size=42, fill="#ffffff", stroke="#000000",
                     stroke_w=3, shadow=False, default_motion="fade",
                     pad=(18, 8), wrap=22, radius=8, bg=None,
                     default_pos=lambda w, h: (CANVAS_W / 2, 994)),
}

_BREAK_AFTER = "、。！？…!?）」』:;"


def wrap_lines(text: str, max_chars: int) -> list[str]:
    """Manual CJK-aware wrap: <=max_chars per line, prefer punctuation breaks."""
    out: list[str] = []
    buf = ""
    for ch in text:
        buf += ch
        if len(buf) >= max_chars or ch in _BREAK_AFTER and len(buf) >= max_chars - 4:
            out.append(buf)
            buf = ""
    if buf:
        out.append(buf)
    return out or [""]


def _font(cfg: dict) -> ImageFont.FreeTypeFont:
    path = FONT_DIR / FONT_FILES[cfg["font"]]
    return ImageFont.truetype(str(path), cfg["size"] * SS)


def render_subtitle_band(width: int = CANVAS_W, height: int = CANVAS_H,
                         band_h: int = 140, inset: int = 16, radius: int = 18,
                         alpha: int = 90) -> Image.Image:
    """Rounded translucent black band behind burned-in subtitles.

    lead feedback (10s test review): a dark band under the subtitle zone keeps
    text readable at small playback sizes. Returns a full-canvas RGBA PNG to
    overlay at (0,0) BEFORE the libass subtitles filter.
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(
        [inset, height - band_h - inset, width - inset, height - inset],
        radius=radius, fill=(10, 10, 14, max(0, min(alpha, 255))))
    return img


# quiz board geometry (measured from bg_quiz_board.png renders, 2026-11-15)
QUIZ_Q_CENTER = (950, 200)      # question text center (board top zone)
QUIZ_ROW_Y = (300, 485, 670)    # choice text centers (just above the lines)
QUIZ_TEXT_X = 560               # choice text left edge (clears manabu @x330)
QUIZ_MARKS = ("ア", "イ", "ウ")


def render_quiz_board(question: str, choices: list[str],
                      highlight: int | None = None,
                      width: int = CANVAS_W, height: int = CANVAS_H
                      ) -> Image.Image:
    """Full-canvas RGBA PNG with the quiz question + choice rows laid onto
    bg_quiz_board's answer slots (P2-2: ボードが空欄のまま問題).

    highlight = index of the correct choice (drawn with a 山吹 badge + ✓)
    for the answer phase. The bg art's クイズ第N問 badge overlaps row 3's
    line, so choice texts sit just ABOVE their lines.
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ai = AI  # 藍

    q_font = ImageFont.truetype(str(FONT_DIR / FONT_FILES["Bold"]), 42)
    c_font = ImageFont.truetype(str(FONT_DIR / FONT_FILES["Bold"]), 40)
    m_font = ImageFont.truetype(str(FONT_DIR / FONT_FILES["Black"]), 44)

    qx, qy = QUIZ_Q_CENTER
    lines = wrap_lines(_quiz_sanitize(question), 24)[:2]
    yy = qy - 12 if len(lines) == 2 else qy
    for ln in lines:
        d.text((qx, yy), ln, font=q_font, anchor="mm",
               fill=(255, 255, 255, 255), stroke_width=2,
               stroke_fill=hex_rgba(TEXT_DARK))
        yy += 58

    for i, row_y in enumerate(QUIZ_ROW_Y):
        hl = (highlight == i)
        if hl:
            d.rounded_rectangle([470, row_y - 30, 1520, row_y + 30], radius=14,
                                fill=hex_rgba(YAMABUKI, 215))
        mark = QUIZ_MARKS[i] if i < len(QUIZ_MARKS) else "?"
        if hl:
            d.text((QUIZ_TEXT_X, row_y), mark, font=m_font, anchor="lm",
                   fill=hex_rgba(TEXT_DARK))
        else:
            d.text((QUIZ_TEXT_X, row_y), mark, font=m_font, anchor="lm",
                   fill=(255, 255, 255, 255), stroke_width=2,
                   stroke_fill=hex_rgba(TEXT_DARK))
        txt = _quiz_sanitize(choices[i]) if i < len(choices) else ""
        if hl:
            d.text((QUIZ_TEXT_X + 70, row_y), txt, font=c_font, anchor="lm",
                   fill=hex_rgba(TEXT_DARK))
        else:
            d.text((QUIZ_TEXT_X + 70, row_y), txt, font=c_font, anchor="lm",
                   fill=(255, 255, 255, 255), stroke_width=2,
                   stroke_fill=hex_rgba(TEXT_DARK))
        if hl:
            # drawn check: the Black font has no U+2714 glyph and falls
            # back to a boxed X, which reads as "wrong" on the answer row
            cx = QUIZ_TEXT_X - 46
            d.line([(cx + 2, row_y), (cx + 13, row_y + 11),
                    (cx + 34, row_y - 13)],
                   fill=hex_rgba(SHU), width=7, joint="curve")
    return img


def hex_rgba(hexcolor: str, alpha: int = 255) -> tuple:
    h = hexcolor.lstrip("#")
    if len(h) != 6:
        return (0, 0, 0, alpha)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def _quiz_sanitize(text: str) -> str:
    return str(text).replace("\n", " ").strip()


def render_overlay(entry: dict) -> tuple[Image.Image, tuple[int, int]]:
    """Render one overlay_text entry -> (RGBA image, default center pos).

    Supported entry keys: text, style, motion (override), pos ([cx, cy]).
    """
    style = entry.get("style", "title_main")
    if style not in STYLES:
        raise KeyError(f"unknown overlay_text style: {style!r} "
                       f"(known: {sorted(STYLES)})")
    cfg = STYLES[style]
    raw_text = str(entry.get("text", ""))
    if cfg.get("split_slash") and "/" in raw_text:
        lines = [ln.strip() for ln in raw_text.split("/") if ln.strip()]
    else:
        lines = wrap_lines(raw_text, cfg["wrap"])
    font = _font(cfg)

    stroke_w = int(cfg.get("stroke_w", 0) or 0) * SS
    pad_w, pad_h = cfg["pad"][0] * SS, cfg["pad"][1] * SS
    line_h = int(cfg["size"] * SS * 1.26)
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    widths = [probe.textlength(ln, font=font) for ln in lines]
    text_w = int(max(widths))
    w = text_w + pad_w * 2 + stroke_w * 2
    h = line_h * len(lines) + pad_h * 2 + stroke_w * 2
    # lead v2: guarantee a minimum card size (final-pixel units)
    min_w, min_h = cfg.get("min_size", (0, 0))
    w = max(w, min_w * SS)
    h = max(h, min_h * SS)
    w += w % 2
    h += h % 2

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if cfg.get("bg"):
        radius = cfg.get("radius")
        if radius is None:  # pill capsule
            radius = h // 2
        else:
            radius = radius * SS
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius,
                            fill=cfg["bg"])
        border = cfg.get("border")
        if border:
            bc, bw = border[0], border[1] * SS
            d.rounded_rectangle([bw // 2, bw // 2, w - 1 - bw // 2,
                                 h - 1 - bw // 2], radius=max(radius - bw // 2, 0),
                                outline=bc, width=bw)

    y = pad_h + stroke_w
    for ln in lines:
        cy = y + line_h / 2
        if cfg.get("shadow"):
            d.text((w / 2, cy + 4 * SS), ln, font=font, anchor="mm",
                   fill=(0, 0, 0, 110), stroke_width=stroke_w,
                   stroke_fill=(0, 0, 0, 110))
        d.text((w / 2, cy), ln, font=font, anchor="mm", fill=cfg["fill"],
               stroke_width=stroke_w, stroke_fill=cfg.get("stroke"))
        y += line_h

    if SS > 1:
        img = img.resize((w // SS, h // SS), Image.LANCZOS)

    pos = entry.get("pos")
    if pos:
        center = (float(pos[0]), float(pos[1]))
    else:
        center = cfg["default_pos"](img.width, img.height)
    return img, center

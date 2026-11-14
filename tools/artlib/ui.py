"""UI バッジ — era_badge / keyword_card / exam_banner / year_number / title_main.

すべて透過 PNG。STYLE_GUIDE の overlay_text スタイル定義に準拠。
"""
from __future__ import annotations

from .canvas import Canvas, load_font, shade, tint, with_alpha
from . import palette as P


def _render(w, h, draw_fn, ss=2, pad=0):
    cv = Canvas(w, h, ss=ss)
    draw_fn(cv.g(), ss)
    return cv.render()


def _fit_text(text, size, weight, max_w):
    """幅 max_w に収まるようフォントサイズを縮小."""
    f = load_font(int(size * 4), weight)
    from PIL import ImageFont
    probe = ImageFont.truetype(f.path, 100)
    w100 = probe.getbbox(text)[2] - probe.getbbox(text)[0]
    est = size * 100 / max(1, w100) * max_w
    return max(10, int(min(size, est)))


def era_badge(main, sub=None, style="indigo", target_w=None, size=44, pad=36):
    """角丸カプセル (藍地に白 44px). sub がある場合は2段."""
    colors = {"indigo": (P.INDIGO, P.UI_WHITE), "shu": (P.SHU, P.UI_WHITE),
              "night": ((24, 34, 66), P.UI_WHITE)}
    bg, fg = colors.get(style, colors["indigo"])
    probe = Canvas(2000, 200, ss=2)
    gw = probe.g()
    tw, _ = gw.text_size(main, size, "bold")
    w = int(tw + pad * 2)
    h = size + 28 if sub is None else int(size * 1.62) + 28
    if target_w:
        w = target_w

    def draw(g, ss):
        g.rrect((1, 1, w - 1, h - 1), (h - 2) / 2, fill=bg,
                outline=with_alpha((255, 255, 255), 150), owidth=2)
        if sub is None:
            g.text((w / 2, h / 2 + 2), main, size, fg, "bold", "mm")
        else:
            sw, _ = gw.text_size(sub, int(size * 0.42), "medium")
            mw, _ = gw.text_size(main, size, "bold")
            g.text((w / 2, h * 0.34), main, size, fg, "bold", "mm")
            g.text((w / 2, h * 0.72), sub, int(size * 0.42),
                   with_alpha(fg, 210), "medium", "mm")
    return _render(w + 2, h + 2, draw)


def keyword_card(keyword, sub=None, size=64, target_w=560):
    """白角丸カード + 藍枠 + 大きめキーワード."""
    probe = Canvas(2400, 300, ss=2)
    gw = probe.g()
    ksz = _fit_text(keyword, size, "black", target_w - 96)
    kw, kh = gw.text_size(keyword, ksz, "black")
    w = max(target_w, int(kw + 96))
    if sub:
        ssz = 30
        sub_w, _ = gw.text_size(sub, ssz, "bold")
        w = max(w, int(sub_w + 96))
    h = 148 if sub else 128
    return _render(w, h, _card_draw(keyword, sub, ksz))


def _card_draw(keyword, sub, ksz):
    def draw(g, ss):
        w = g.size[0]
        h = g.size[1]
        g.rrect((3, 3, w - 3, h - 3), 26, fill=with_alpha(P.UI_WHITE, 242),
                outline=P.INDIGO, owidth=6)
        g.rrect((3, 3, w - 3, h - 3), 26, outline=with_alpha(P.SHU, 0), owidth=0)
        cy = h * (0.42 if sub else 0.5)
        g.text((w / 2, cy), keyword, ksz, P.INDIGO_D, "black", "mm")
        if sub:
            g.text((w / 2, h * 0.76), sub, 30, P.SHU, "bold", "mm")
    return draw


def exam_banner(text="ここが受験ポイント!", size=56):
    """朱バナー (両端を斜めに切ったリボン形)."""
    probe = Canvas(2400, 200, ss=2)
    gw = probe.g()
    tw, _ = gw.text_size(text, size, "black")
    w = int(tw + 150)
    h = int(size * 1.7)
    notch = 44

    def draw(g, ss):
        pts = [(notch, 2), (w - notch, 2), (w - 1, h / 2), (w - notch, h - 2),
               (notch, h - 2), (1, h / 2)]
        g.poly(pts, fill=P.SHU, outline=P.SHU_D, owidth=3)
        g.poly([(notch, 8), (w - notch, 8), (w - notch, 20), (notch, 20)],
               fill=with_alpha((255, 255, 255), 70))
        g.text((w / 2, h / 2 + 2), text, size, P.UI_WHITE, "black", "mm")
    return _render(w, h, draw)


def year_number(text, size=96):
    """年号強調 (山吹 + 藍フチ). 透明背景テキスト."""
    probe = Canvas(2400, 300, ss=2)
    gw = probe.g()
    tw, th = gw.text_size(text, size, "black")
    w, h = int(tw + 60), int(th + 60)
    return _render(w, h, lambda g, ss: g.text(
        (w / 2, h / 2), text, size, P.YAMABUKI, "black", "mm",
        stroke_width=10, stroke_fill=P.INDIGO_DD))


def title_main(text, size=72):
    """白文字 + 朱フチのメインタイトル."""
    probe = Canvas(2600, 300, ss=2)
    gw = probe.g()
    tw, th = gw.text_size(text, size, "black")
    w, h = int(tw + 80), int(th + 50)
    return _render(w, h, lambda g, ss: g.text(
        (w / 2, h / 2), text, size, P.UI_WHITE, "black", "mm",
        stroke_width=8, stroke_fill=P.SHU))


def quiz_frame(w=760, h=340, q_no=None):
    """クイズ用カード枠 (白半透明 + 藍枠). 上に問題番号バッジ."""
    def draw(g, ss):
        g.rrect((4, 4, w - 4, h - 4), 30, fill=with_alpha(P.UI_WHITE, 235),
                outline=P.INDIGO, owidth=7)
        if q_no:
            bw = 150
            g.rrect((26, -34, 26 + bw, 56), 28, fill=P.YAMABUKI,
                    outline=P.INDIGO_DD, owidth=4)
            g.text((26 + bw / 2, 12), q_no, 40, P.INDIGO_DD, "black", "mm")
    return _render(w, h + 40, draw)

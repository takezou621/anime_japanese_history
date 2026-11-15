"""自然物 — 空・雲・山並み・地面・木・水・鳥・星月."""
from __future__ import annotations

import math
import random

from .canvas import (Canvas, G, blob_pts, gradient, mix, shade, speckle, tint,
                     with_alpha)
from . import palette as P


# ---------------------------------------------------------------- 空・天体


def sky(cv, stops):
    """全面に空グラデを敷く."""
    g = gradient(cv.img.size, stops, "v")
    cv.img.alpha_composite(g)


def sky_rect(cv, box, stops):
    """矩形内に空グラデ."""
    x0, y0, x1, y1 = [int(v * cv.ss) for v in box]
    g = gradient((x1 - x0, y1 - y0), stops, "v")
    cv.img.alpha_composite(g, (x0, y0))


def sun(g, cx, cy, r, color=P.YAMABUKI, core=(255, 244, 200), halo=0.0):
    if halo > 0:
        g.circle(cx, cy, r * (1 + halo), fill=with_alpha(core, 70))
        g.circle(cx, cy, r * (1 + halo * 0.6), fill=with_alpha(core, 90))
    g.circle(cx, cy, r, fill=color)
    g.circle(cx, cy, r * 0.78, fill=core)


def moon(cv, cx, cy, r, cut_color, color=(247, 242, 219), crescent=True):
    g = cv.g()
    g.circle(cx, cy, r * 1.18, fill=with_alpha(color, 40))
    g.circle(cx, cy, r, fill=color)
    g.ellipse((cx - r * 0.5, cy - r * 0.4, cx + r * 0.5, cy + r * 0.45),
              fill=with_alpha((216, 208, 180), 120))
    if crescent:
        g.circle(cx + r * 0.55, cy - r * 0.25, r * 0.92, fill=cut_color)


def stars(g, box, n, seed=7, color=(255, 255, 255), sparkle=6):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        a = rnd.randint(90, 230)
        r = rnd.uniform(0.8, 2.2)
        g.circle(x, y, r, fill=with_alpha(color, a))
    for _ in range(sparkle):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        r = rnd.uniform(4, 8)
        a = rnd.randint(140, 230)
        c = with_alpha(color, a)
        g.line([(x - r, y), (x + r, y)], c, 1.6)
        g.line([(x, y - r), (x, y + r)], c, 1.6)


def cloud(g, cx, cy, s, base=(255, 255, 255), under=(210, 226, 238),
          alpha=None, seed=1):
    """アニメ風フラット雲 (T10: 形状/透明度を seed でランダム化)."""
    rnd = random.Random(seed)
    if alpha is None:
        alpha = rnd.randint(244, 255)
    s = s * rnd.uniform(0.92, 1.12)

    def shape(dx, dy, color):
        c = with_alpha(color, alpha)
        g.ellipse((cx - 2.1 * s + dx, cy - 0.30 * s + dy,
                   cx + 2.1 * s + dx, cy + 0.52 * s + dy), fill=c)
        offs = [(-1.5, 0.72, 0.62), (-0.55, 0.95, 0.74), (0.5, 0.9, 0.7),
                (1.45, 0.66, 0.58)]
        for i, (ox, oy, pr) in enumerate(offs):
            px = cx + ox * s + rnd.uniform(-0.08, 0.08) * s + dx
            py = cy - oy * s + dy + rnd.uniform(-0.04, 0.04) * s
            g.circle(px, py, pr * s, fill=c)

    shape(0, 0.10 * s, under)
    shape(0, 0, base)
    # T10: 光の当たる上部に不透明な明色ポフ (半透明はバッファ置換で穴になるため不使用)
    hx = cx + rnd.uniform(-0.4, 0.4) * s
    g.ellipse((hx - 0.7 * s, cy - 0.62 * s, hx + 0.7 * s, cy - 0.30 * s),
              fill=tint(base, 0.0))


def clouds_row(cv, y, n, s, seed=3, **kw):
    rnd = random.Random(seed)
    g = cv.g()
    for i in range(n):
        cx = cv.w * (i + 0.5 + rnd.uniform(-0.18, 0.18)) / n
        cy = y + rnd.uniform(-0.3, 0.3) * s
        cloud(g, cx, cy, s * rnd.uniform(0.8, 1.25), seed=seed + i, **kw)


def birds(g, pts, s, color=(64, 60, 72), width=3.0):
    for (x, y) in pts:
        g.arc((x - s, y - s * 0.55, x, y + s * 0.55), 200, 320, color, width)
        g.arc((x, y - s * 0.55, x + s, y + s * 0.55), 220, 340, color, width)


# ---------------------------------------------------------------- 山並み


def _ridge_line(w, y_base, amp, seed, freq=2.3):
    rnd = random.Random(seed)
    p1 = rnd.uniform(0, math.tau)
    p2 = rnd.uniform(0, math.tau)
    p3 = rnd.uniform(0, math.tau)
    pts = []
    n = 30
    for i in range(n + 1):
        x = w * i / n
        t = math.tau * i / n
        m = (0.55 * math.sin(t * freq + p1) + 0.30 * math.sin(t * freq * 2.3 + p2)
             + 0.15 * math.sin(t * freq * 4.1 + p3))
        m = 0.55 + 0.45 * m  # 0.1〜1.0 くらいに
        pts.append((x, y_base - amp * max(0.08, m)))
    return pts


def ridge(cv, y_base, amp, color, seed=1, freq=2.3, highlight=None, hl_w=2.5):
    g = cv.g()
    pts = _ridge_line(cv.w, y_base, amp, seed, freq)
    g.poly(pts + [(cv.w, cv.h), (0, cv.h)], fill=color)
    if highlight:
        g.line(pts, highlight, hl_w)


def mountain_ridge(cv, y_base, amp, stops, seed=1, freq=2.0, snowline=None):
    """縦グラデの山シルエット + 山頂ハイライト."""
    g = cv.g()
    pts = _ridge_line(cv.w, y_base, amp, seed, freq)
    top = min(p[1] for p in pts)
    lay = cv.layer()
    lg = lay.g()
    lg.poly(pts + [(cv.w, cv.h), (0, cv.h)], fill=(255, 255, 255))
    grad = gradient(lay.img.size, [(0, stops[0]), (1, stops[1])], "v")
    from .canvas import paste_masked
    paste_masked(lay.img, grad, lay.img.split()[3])
    # マスクを再構築 (paste_masked は alpha を合成するので先に保存)
    cv.img.alpha_composite(lay.img)
    if snowline:
        rnd = random.Random(seed + 99)
        for p in pts:
            if p[1] < top + amp * snowline and rnd.random() < 0.7:
                g.circle(p[0], p[1] + 2, rnd.uniform(3, 6),
                         fill=with_alpha((250, 252, 255), 190))


# ---------------------------------------------------------------- 地面


def ground(cv, y, color, dark=None, curve=16, seed=3, speckles=0,
           speckle_colors=None, speckle_r=(1.5, 3.5)):
    """緩い弧の地平線から下を塗る."""
    g = cv.g()
    pts = []
    n = 22
    rnd = random.Random(seed)
    wob = [rnd.uniform(-1, 1) for _ in range(n + 1)]
    for i in range(n + 1):
        x = cv.w * i / n
        u = 2 * i / n - 1
        yy = y - curve * (1 - u * u) + curve * 0.12 * wob[i]
        pts.append((x, yy))
    g.poly(pts + [(cv.w, cv.h), (0, cv.h)], fill=color)
    if dark:
        g.line(pts, dark, 3.5)
    if speckles and speckle_colors:
        yl = pts[len(pts) // 2][1]
        speckle(g, (0, yl + 8, cv.w, cv.h), speckles, speckle_colors,
                r=speckle_r, seed=seed + 5)
    return pts


def path_band(g, pts_top, pts_bot, color, dark=None, w_dark=3):
    """道・帯ポリゴン (上端線と下端線の2点列)."""
    poly = list(pts_top) + list(reversed(pts_bot))
    g.poly(poly, fill=color)
    if dark:
        g.line(poly, dark, w_dark)


def water_band(cv, box, base, light, streaks=16, seed=7, alpha=None):
    """水面バンド + 光の横縞."""
    g = cv.g()
    x0, y0, x1, y1 = box
    c = with_alpha(base, alpha) if alpha else base
    g.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill=c)
    rnd = random.Random(seed)
    for _ in range(streaks):
        yy = rnd.uniform(y0 + 4, y1 - 4)
        ln = rnd.uniform(20, 130)
        xx = rnd.uniform(x0, x1 - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2, 4)),
                2, fill=with_alpha(light, rnd.randint(70, 150)))


def grass_tufts(g, box, n, color, seed=5, h=14, width=2.2, alpha=None):
    c = with_alpha(color, alpha) if alpha else color
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(n):
        x = rnd.uniform(x0, x1)
        y = rnd.uniform(y0, y1)
        hh = h * rnd.uniform(0.7, 1.4)
        lean = rnd.uniform(-4, 4)
        g.line([(x, y), (x + lean * 0.4, y - hh * 0.6), (x + lean, y - hh)],
               c, width)
        g.line([(x, y), (x - lean * 0.5, y - hh * 0.5)], c, width * 0.7)


def reeds_fg(cv, y, seed=4, color=(60, 52, 60), n=40, s=1.0):
    """前景の芒 (シルエット用)."""
    g = cv.g()
    rnd = random.Random(seed)
    for _ in range(n):
        x = rnd.uniform(0, cv.w)
        h = rnd.uniform(60, 150) * s
        lean = rnd.uniform(-18, 18)
        g.line([(x, y + rnd.uniform(-8, 8)), (x + lean * 0.5, y - h * 0.55),
                (x + lean, y - h)], color, rnd.uniform(2.5, 4))
        g.ellipse((x + lean - 7, y - h - 16, x + lean + 7, y - h + 2),
                  fill=color)


# ---------------------------------------------------------------- 木


def tree(cv, x, y, s, kind="oak", leaf=None, leaf_d=None, leaf_l=None,
         trunk=P.WOOD, seed=0):
    """y は地面の接点. s=1 で高さ約 210px."""
    g = cv.g()
    leaf = leaf or P.WAKAKUSA
    # T10: 同一スタンプの反復を避けるため seed で色調とサイズを揺らす
    rnd = random.Random(seed)
    leaf = mix(leaf, rnd.choice([P.WAKAKUSA_L, (96, 150, 100), (120, 168, 108)]),
               rnd.uniform(0.0, 0.35))
    leaf_d = shade(leaf, 0.76)
    leaf_l = tint(leaf, 0.28)
    s = s * rnd.uniform(0.9, 1.14)
    if kind == "oak":
        # T10: 幹の傾きと非対称な樹冠 (seed 決定論)
        lean = rnd.uniform(-0.16, 0.16)
        tw = 11 * s
        th = 95 * s
        top_x = x + lean * th
        g.poly([(x - tw, y), (x - tw * 0.45, y - th * 0.75),
                (x - tw * 0.3 + lean * th * 0.4, y - th),
                (x + tw * 0.3 + lean * th * 0.4, y - th),
                (x + tw * 0.45, y - th * 0.75), (x + tw, y),
                (x + tw * 0.6, y + 2), (x - tw * 0.6, y + 2)],
               fill=trunk, outline=shade(trunk, 0.8), owidth=2.2 * s)
        g.line([(x - tw * 0.3, y - th * 0.2), (x - tw * 1.4, y - th * 0.55)],
               trunk, 5 * s)
        cy = y - th - 30 * s
        base_offs = [(-52, 12, 52), (0, -14, 62), (52, 10, 50),
                     (-26, -34, 44), (28, -36, 44)]
        jitter = rnd.uniform(0.85, 1.15)
        canopy = []
        cy = y - th - 30 * s
        for (dx, dy, r) in [(-52, 12, 52), (0, -14, 62), (52, 10, 50),
                            (-26, -34, 44), (28, -36, 44)]:
            canopy += blob_pts(x + dx * s + rnd.uniform(-4, 4),
                               cy + dy * s, r * s, r * 0.82 * s,
                               seed=seed + int(dx) + 1, wobble=0.08, n=16)
        g.poly(canopy, fill=leaf_d)
        g.poly([(p[0], p[1] - 7 * s) for p in canopy], fill=leaf)
        g.poly([(p[0] - 4 * s, p[1] - 13 * s) for p in canopy[::2]], fill=leaf_l)
        # T10: 陽の当たる上部のハイライト blob (不透明・樹冠内)
        for b in range(2):
            hb = blob_pts(x - 16 * s + b * 34 * s, cy - 30 * s, 17 * s, 11 * s,
                          seed=seed * 31 + b, wobble=0.16)
            g.poly(hb, fill=leaf_l)
        # 落ち影
                # 落ち影
        g.ellipse((x - tw * 2.2, y - 6 * s, x + tw * 2.2, y + 10 * s),
                  fill=with_alpha((60, 50, 44), 52))
    elif kind == "pine":
        tw = 9 * s
        g.poly([(x - tw, y), (x - 4 * s, y - 60 * s), (x + 4 * s, y - 60 * s),
                (x + tw, y), (x + 5 * s, y + 2), (x - 5 * s, y + 2)], fill=trunk)
        for i, (yy, wdt, hh) in enumerate([(0, 78, 62), (-38, 62, 54),
                                           (-72, 46, 48), (-102, 30, 40)]):
            base = y + yy * s
            g.poly([(x - wdt * s, base), (x + wdt * s, base),
                    (x, base - hh * s)], fill=leaf_d)
            g.poly([(x + wdt * s * 0.15, base), (x + wdt * s, base),
                    (x, base - hh * s)], fill=leaf)
    else:  # bush
        r = 34 * s
        g.poly(blob_pts(x, y - r * 0.5, r, r * 0.72, seed=seed, wobble=0.14),
               fill=leaf_d)
        g.poly(blob_pts(x - 2 * s, y - r * 0.62, r * 0.9, r * 0.62, seed=seed + 1,
                        wobble=0.14), fill=leaf)
        g.poly(blob_pts(x - 4 * s, y - r * 0.72, r * 0.6, r * 0.44, seed=seed + 2,
                        wobble=0.12), fill=leaf_l)


def forest_band(cv, y, n, s_range=(0.5, 1.1), leaf=P.WAKAKUSA, seed=2,
                kinds=None, alpha=None):
    """木々の帯 (奥行き用). y=地面線."""
    rnd = random.Random(seed)
    g = cv.g()
    kinds = kinds or ["oak", "oak", "pine"]
    for i in range(n):
        x = cv.w * (i + rnd.uniform(0.05, 0.6)) / n
        s = rnd.uniform(*s_range)
        kind = rnd.choice(kinds)
        c = leaf
        if alpha is not None:
            c = with_alpha(leaf, alpha)
        tree(cv, x, y + rnd.uniform(-6, 6), s, kind=kind, leaf=c,
             leaf_d=with_alpha(shade(leaf, 0.78), alpha) if alpha is not None else shade(leaf, 0.78),
             leaf_l=c, seed=seed * 7 + i)


def light_shafts(cv, pts_list, color=(255, 250, 220), alpha=26):
    """木漏れ日の光柱 (半透明ポリゴン群)."""
    g = cv.g()
    for pts in pts_list:
        g.poly(pts, fill=with_alpha(color, alpha))


def foreground_parallax(cv, y=1000, seed=7, tone=(52, 58, 44), n_tufts=26,
                        n_stones=6, fence_x=None):
    """前景のパララックス層 (濃い草・石・柵を画面下端に重ねる)."""
    g = cv.g()
    rnd = random.Random(seed)
    col = tone
    # 手前の草 (大きめ・濃い)
    for _ in range(n_tufts):
        px = rnd.uniform(0, cv.w)
        py = rnd.uniform(y, cv.h)
        h = rnd.uniform(26, 54)
        lean = rnd.uniform(-14, 14)
        g.line([(px, py), (px + lean * 0.4, py - h * 0.6), (px + lean, py - h)],
               col, rnd.uniform(3.4, 5.6))
        g.line([(px, py), (px - lean * 0.5, py - h * 0.55)], col, 3.4)
    # 石
    for _ in range(n_stones):
        px = rnd.uniform(0, cv.w)
        py = rnd.uniform(y + 20, cv.h - 10)
        r_ = rnd.uniform(10, 26)
        g.ellipse((px - r_, py - r_ * 0.6, px + r_, py + r_ * 0.6),
                  fill=shade(col, 1.35), outline=shade(col, 0.7), owidth=2.2)
    # 柵 (指定があればシルエットで)
    if fence_x:
        for px in range(int(fence_x[0]), int(fence_x[1]), 46):
            g.poly([(px, cv.h), (px + 12, cv.h), (px + 10, y - 30),
                    (px + 2, y - 30)], fill=col)
        g.line([(fence_x[0], y - 26), (fence_x[1], y - 26)], col, 6)

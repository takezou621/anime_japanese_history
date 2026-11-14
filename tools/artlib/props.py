"""時代小物 — 竪穴住居・高床倉庫・土器・銅鐸・埴輪・古墳・舟・火など.

各 prop は g に描画し、(x, y) は地面の基準点、s はスケール倍率。
マスクが必要な小物 (土器など) は独立レイヤーで描いてから合成する。
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw

from .canvas import (Canvas, G, Layer, blob_pts, cbez, mix, qbez, radial, shade,
                     speckle, sublayer, tint, with_alpha)
from . import palette as P


def rect(g, x0, y0, x1, y1, fill=None, outline=None, owidth=0):
    g.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill=fill,
           outline=outline, owidth=owidth)


def smoke_wisp(g, x, y, s, seed=0, color=(224, 220, 214), alpha=150):
    rnd = random.Random(seed)
    for i in range(4):
        r = (7 + 5 * i) * s
        yy = y - (14 + 20 * i) * s * rnd.uniform(0.85, 1.1)
        xx = x + rnd.uniform(-14, 14) * s + (i % 2 - 0.5) * 16 * s
        g.circle(xx, yy, r, fill=with_alpha(color, max(30, alpha - 30 * i)))


# ---------------------------------------------------------------- 住居系


def pit_house(g, x, y, s, roof=None, roof_d=None, door=(46, 32, 26),
              smoke=False, seed=0):
    """竪穴住居 (側面). s=1 で幅約 320px."""
    roof = roof or P.STRAW
    roof_d = roof_d or P.STRAW_D
    w = 320 * s
    h = 150 * s
    # 地面影
    g.ellipse((x - w * 0.52, y - 10 * s, x + w * 0.52, y + 14 * s),
              fill=with_alpha((80, 62, 48), 70))
    # ドーム屋根
    pts = []
    n = 26
    for i in range(n + 1):
        u = -1 + 2 * i / n
        yy = -h * (1 - u * u) ** 0.55
        pts.append((x + u * w / 2, y + yy))
    g.poly(pts, fill=roof, outline=shade(roof_d, 0.85), owidth=3 * s)
    # 茅の筋
    for i in range(1, 9):
        u = -1 + 2 * i / 9
        g.line([(x + u * w * 0.48, y - 4 * s),
                (x + u * w * 0.16, y - h * 0.88)], roof_d, 2.4 * s)
    # 横バンド
    for (t, drop) in [(0.38, 24), (0.64, 13)]:
        by = y - h * t
        bw = w * 0.5 * (1 - t * 0.52)
        g.arc((x - bw, by - drop * s, x + bw, by + drop * s), 200, 340,
              roof_d, 2.4 * s)
    # 軒
    g.line([(x - w * 0.5, y + 2 * s), (x + w * 0.5, y + 2 * s)],
           shade(roof_d, 0.8), 6 * s)
    # 土盛り部
    g.rrect((x - w * 0.42, y, x + w * 0.42, y + 15 * s), 6 * s, fill=P.SOIL)
    # 入口 (角丸の上を持つ開口)
    dw, dh = 56 * s, 62 * s
    g.pieslice((x - dw / 2, y - dh * 2, x + dw / 2, y + dh * 2), 200, 340, fill=door)
    rect(g, x - dw / 2, y - dh * 0.75, x + dw / 2, y + 3 * s, fill=door)
    if smoke:
        smoke_wisp(g, x + w * 0.04, y - h - 6 * s, s, seed=seed + 3)


def warehouse(g, x, y, s, wall=None, roof=None, roof_d=None, ladder=True,
              lit=False, seed=0):
    """高床倉庫. s=1 で幅約 430px・高さ約 360px."""
    wall = wall or (208, 172, 118)
    roof = roof or P.STRAW
    roof_d = roof_d or P.STRAW_D
    g.ellipse((x - 210 * s, y - 8 * s, x + 210 * s, y + 12 * s),
              fill=with_alpha((80, 62, 48), 60))
    # 高床の柱
    pw = 13 * s
    ph = 92 * s
    for px in [-150, -95, 95, 150]:
        g.poly([(x + px * s - pw / 2, y), (x + px * s + pw / 2, y),
                (x + px * s + pw / 2 - 3 * s, y - ph),
                (x + px * s - pw / 2 + 3 * s, y - ph)], fill=P.WOOD_D)
    # 床下の貫
    rect(g, x - 165 * s, y - ph * 0.62, x + 165 * s, y - ph * 0.62 + 10 * s,
         fill=P.WOOD)
    # 倉本体
    by = y - ph
    bw = 175 * s
    bh = 118 * s
    rect(g, x - bw, by - bh, x + bw, by, fill=wall)
    rect(g, x - bw, by - bh, x - bw + 14 * s, by, fill=shade(wall, 0.82))
    rect(g, x + bw - 14 * s, by - bh, x + bw, by, fill=shade(wall, 0.82))
    for i in range(1, 4):
        g.line([(x - bw + 6 * s, by - bh * i / 4), (x + bw - 6 * s, by - bh * i / 4)],
               shade(wall, 0.78), 2.2 * s)
    # 扉
    rect(g, x - 30 * s, by - 78 * s, x + 30 * s, by - 6 * s, fill=P.WOOD_D)
    g.line([(x, by - 78 * s), (x, by - 6 * s)], shade(P.WOOD_D, 0.7), 2.5 * s)
    # 屋根 (茅葺切妻, 反った軒)
    rw = 215 * s
    rh = 105 * s
    peak = by - bh - rh
    eave_l = (x - rw, by - bh + 12 * s)
    eave_r = (x + rw, by - bh + 12 * s)
    rpts = (qbez(eave_l, (x - rw * 0.45, by - bh - rh * 0.72), (x, peak), 16)
            + qbez((x, peak), (x + rw * 0.45, by - bh - rh * 0.72), eave_r, 16)[1:])
    g.poly(rpts + [(x + rw * 0.97, by - bh - rh * 0.18),
                   (x - rw * 0.97, by - bh - rh * 0.18)],
           fill=roof, outline=shade(roof_d, 0.85), owidth=3 * s)
    for i in range(1, 8):
        t = i / 8
        gx = -rw + 2 * rw * t
        g.line([(x + gx, by - bh + 10 * s),
                (x + gx * 0.34, by - bh - rh * 0.82)], roof_d, 2.2 * s)
    g.line([eave_l, eave_r], shade(roof_d, 0.8), 5 * s)
    if lit:
        g.rrect((x - 22 * s, by - 66 * s, x + 22 * s, by - 14 * s), 6 * s,
                fill=with_alpha((255, 214, 120), 235))
    if ladder:
        lx = x + bw + 30 * s
        g.line([(lx, y), (lx - 26 * s, by - 8 * s)], P.WOOD_D, 6 * s)
        for i in range(1, 6):
            t = i / 6
            px = lx - 26 * s * t
            py = y - (by - 8 * s - y) * t
            g.line([(px - 10 * s, py), (px + 10 * s, py)], P.WOOD_D, 3.4 * s)


def big_hall(g, x, y, s, lit=True, roof=None, roof_d=None, wall=None, seed=0):
    """大型高床殿屋 (卑弥呼・大和政権の館風). s=1 で幅約 600px."""
    roof = roof or P.STRAW
    roof_d = roof_d or P.STRAW_D
    wall = wall or (196, 158, 108)
    g.ellipse((x - 320 * s, y - 10 * s, x + 320 * s, y + 16 * s),
              fill=with_alpha((40, 32, 40), 70))
    # 高床柱
    ph = 120 * s
    for px in [-240, -170, -60, 60, 170, 240]:
        g.poly([(x + px * s - 7 * s, y), (x + px * s + 7 * s, y),
                (x + px * s + 5 * s, y - ph), (x + px * s - 5 * s, y - ph)],
               fill=P.WOOD_D)
    rect(g, x - 265 * s, y - ph * 0.55, x + 265 * s, y - ph * 0.55 + 12 * s,
         fill=P.WOOD)
    # 1階
    by = y - ph
    bw = 260 * s
    bh = 128 * s
    rect(g, x - bw, by - bh, x + bw, by, fill=wall)
    rect(g, x - bw, by - bh, x - bw + 18 * s, by, fill=shade(wall, 0.8))
    rect(g, x + bw - 18 * s, by - bh, x + bw, by, fill=shade(wall, 0.8))
    win = with_alpha((255, 214, 120), 235) if lit else shade(wall, 0.55)
    for wx in (-180, 60):
        g.rrect((x + wx * s - 28 * s, by - 86 * s, x + wx * s + 28 * s, by - 26 * s),
                6 * s, fill=win)
        g.line([(x + wx * s, by - 86 * s), (x + wx * s, by - 26 * s)],
               shade(wall, 0.6), 2.4 * s)

    def gable(cx0, cy0, rw, rh):
        peak = cy0 - rh
        pts = (qbez((cx0 - rw, cy0 + 10 * s), (cx0 - rw * 0.45, cy0 - rh * 0.7),
                    (cx0, peak), 14)
               + qbez((cx0, peak), (cx0 + rw * 0.45, cy0 - rh * 0.7),
                      (cx0 + rw, cy0 + 10 * s), 14)[1:])
        pts += [(cx0 + rw * 0.96, cy0 - rh * 0.2), (cx0 - rw * 0.96, cy0 - rh * 0.2)]
        g.poly(pts, fill=roof, outline=shade(roof_d, 0.85), owidth=3 * s)
        for i in range(1, 9):
            gx = cx0 - rw + 2 * rw * i / 9
            g.line([(cx0 + gx * 0.96, cy0 - rh * 0.2), (cx0 + gx, cy0 + 8 * s)],
                   roof_d, 2.2 * s)
        # 堅魚木 (棟の突起)
        g.line([(cx0 - 44 * s, peak + 4 * s), (cx0 + 44 * s, peak + 4 * s)],
               P.WOOD_D, 8 * s)
        for px in (-28, 28):
            g.line([(cx0 + px * s, peak - 16 * s), (cx0 + px * s, peak + 20 * s)],
                   P.WOOD_D, 7 * s)
        return peak

    y1 = gable(x, by - bh, 300 * s, 92 * s)
    # 2階
    b2y = y1 + 24 * s
    b2w = 150 * s
    b2h = 88 * s
    rect(g, x - b2w, b2y - b2h, x + b2w, b2y, fill=shade(wall, 0.92))
    for wx in (-90, 0, 90):
        g.rrect((x + wx * s - 24 * s, b2y - 60 * s, x + wx * s + 24 * s, b2y - 14 * s),
                5 * s, fill=win)
    gable(x, b2y, 190 * s, 82 * s)


# ---------------------------------------------------------------- 土器


def _pot_profile(x, y, h, lw, mw, tw):
    """深鉢の左プロファイル (下から上へ)."""
    left = (cbez((x - lw, y), (x - mw * 1.05, y - h * 0.22), (x - mw, y - h * 0.42),
                 (x - mw * 0.62, y - h * 0.62), 14)
            + cbez((x - mw * 0.62, y - h * 0.62), (x - mw * 0.48, y - h * 0.82),
                   (x - tw, y - h * 0.9), (x - tw * 1.06, y - h), 12))
    right = [(2 * x - px, py) for (px, py) in reversed(left)]
    return left + right


def jomon_pot(g, x, y, s, body=None, pat_d=None, flame=True, seed=0):
    """深鉢形土器 (縄文もよう+火焔型の突起). s=1 で高さ約 230px. y=底."""
    body = body or P.CLAY
    pat_d = pat_d or P.CLAY_D
    h = 220 * s
    lw, mw, tw = 34 * s, 84 * s, 62 * s
    prof = _pot_profile(x, y, h, lw, mw, tw)
    # 地面影
    g.ellipse((x - mw * 0.9, y - 6 * s, x + mw * 0.9, y + 10 * s),
              fill=with_alpha((70, 54, 42), 60))
    g.poly(prof, fill=body, outline=shade(pat_d, 0.8), owidth=2.6 * s)
    # もようを器の中だけに (独立レイヤー+マスク)
    lay = Layer(g.size[0], g.size[1], g.ss)
    sg = lay.g()
    rnd = random.Random(seed)
    rows = int(h * 0.66 / (9 * s))
    for r_i in range(rows):
        yy = y - h * 0.16 - r_i * 9 * s
        off = rnd.uniform(-2, 2)
        xx = x - mw * 0.82 + off
        while xx < x + mw * 0.82:
            sg.line([(xx, yy + 8 * s), (xx + 6 * s, yy - 2 * s)], pat_d, 3.0 * s)
            xx += 12 * s
    band_y = y - h * 0.58
    sg.arc((x - mw * 0.92, band_y - 18 * s, x + mw * 0.92, band_y + 18 * s),
           200, 340, tint(pat_d, 0.3), 7 * s)
    mask = Image.new("L", lay.img.size, 0)
    md = ImageDraw.Draw(mask)
    md.polygon([((px * g.ss), (py * g.ss)) for (px, py) in prof], fill=255)
    cut = Image.new("RGBA", lay.img.size, (0, 0, 0, 0))
    cut.paste(lay.img, (0, 0), mask)
    g.img.alpha_composite(cut)
    # 口縁
    g.ellipse((x - tw * 1.06, y - h - 7 * s, x + tw * 1.06, y - h + 9 * s),
              fill=shade(pat_d, 0.62), outline=shade(pat_d, 0.8), owidth=2.2 * s)
    g.ellipse((x - tw * 0.8, y - h - 4 * s, x + tw * 0.8, y - h + 6 * s),
              fill=shade(pat_d, 0.45))
    # 火焔型の突起
    if flame:
        for fx, fh in [(-0.68, 26), (-0.23, 36), (0.23, 36), (0.68, 26)]:
            bx = x + fx * tw * 1.28
            tipy = y - h - fh * s
            g.poly(qbez((bx - 9 * s, y - h + 2 * s), (bx - 4 * s, y - h - fh * s * 0.7),
                        (bx, tipy), 8)
                   + qbez((bx, tipy), (bx + 4 * s, y - h - fh * s * 0.7),
                          (bx + 9 * s, y - h + 2 * s), 8),
                   fill=body, outline=shade(pat_d, 0.8), owidth=1.8 * s)
    # ハイライト
    g.line([(x - mw * 0.6, y - h * 0.18), (x - mw * 0.48, y - h * 0.56)],
           with_alpha((255, 244, 220), 90), 6 * s)


def yayoi_pot(g, x, y, s, body=(214, 176, 130), seed=0):
    """弥生土器 (薄手・すっきりした壺). s=1 で高さ約 170px."""
    h = 170 * s
    lw, mw, tw = 26 * s, 62 * s, 44 * s
    prof = _pot_profile(x, y, h, lw, mw, tw)
    prof = [(px, py - 4 * s) for (px, py) in prof]
    g.ellipse((x - mw * 0.9, y - 4 * s, x + mw * 0.9, y + 9 * s),
              fill=with_alpha((70, 54, 42), 50))
    g.poly(prof, fill=body, outline=shade(body, 0.72), owidth=2.4 * s)
    g.ellipse((x - tw * 1.04, y - h - 5 * s, x + tw * 1.04, y - h + 7 * s),
              fill=shade(body, 0.6), outline=shade(body, 0.72), owidth=2 * s)
    # 赤彩の帯
    g.arc((x - mw * 0.85, y - h * 0.52 - 12 * s, x + mw * 0.85, y - h * 0.52 + 12 * s),
          200, 340, P.SHU_D, 5 * s)
    g.line([(x - mw * 0.6, y - h * 0.2), (x - mw * 0.5, y - h * 0.5)],
           with_alpha((255, 244, 220), 80), 5 * s)


# ---------------------------------------------------------------- 青銅器・埴輪


def dotaku(g, x, y, s, bronze=(122, 150, 118), pat=None, seed=0):
    """銅鐸. s=1 で高さ約 250px. y=下端."""
    pat = pat or shade(bronze, 0.68)
    h = 230 * s
    tw, mw, bw = 30 * s, 56 * s, 44 * s
    left = (cbez((x - tw, y - h), (x - mw * 0.9, y - h * 0.82), (x - mw, y - h * 0.55),
                 (x - mw * 0.8, y - h * 0.28), 12)
            + qbez((x - mw * 0.8, y - h * 0.28), (x - mw * 0.55, y - h * 0.08),
                   (x - bw, y - h * 0.03), 8))
    right = [(2 * x - px, py) for (px, py) in reversed(left)]
    g.poly(left + right, fill=bronze, outline=shade(bronze, 0.6), owidth=2.6 * s)
    for bx in (-0.5, 0.0, 0.5):
        xx = x + bx * mw * s
        g.line([(xx, y - h * 0.86), (xx, y - h * 0.12)], pat, 5 * s)
    for ty in (0.72, 0.48):
        for bx in (-0.5, 0.0, 0.5):
            xx = x + bx * mw * s
            yy = y - h * ty
            g.circle(xx, yy, 7 * s, outline=pat, owidth=2.4 * s)
            g.circle(xx, yy, 2.6 * s, fill=pat)
    # 釣手 (横棒) と鈕
    g.rrect((x - tw - 16 * s, y - h - 9 * s, x + tw + 16 * s, y - h + 5 * s),
            7 * s, fill=shade(bronze, 0.72))
    for px in (-1, 1):
        g.rrect((x + px * (tw + 20) * s - 10 * s, y - h - 4 * s,
                 x + px * (tw + 20) * s + 10 * s, y - h + 8 * s), 6 * s,
                fill=shade(bronze, 0.66))
    g.line([(x - mw * 0.55, y - h * 0.7), (x - mw * 0.45, y - h * 0.25)],
           with_alpha((240, 250, 235), 90), 5 * s)


def haniwa(g, x, y, s, clay=None, face=True, hat=True, seed=0):
    """人物埴輪. s=1 で高さ約 250px."""
    clay = clay or P.CLAY
    cd = P.CLAY_D
    bw = 46 * s
    g.poly([(x - bw, y), (x - bw * 0.82, y - 150 * s), (x + bw * 0.82, y - 150 * s),
            (x + bw, y)], fill=clay, outline=shade(cd, 0.8), owidth=2.4 * s)
    g.ellipse((x - bw, y - 10 * s, x + bw, y + 10 * s), fill=shade(cd, 0.7))
    g.line([(x - bw * 0.85, y - 60 * s), (x + bw * 0.85, y - 60 * s)], cd, 5 * s)
    g.rrect((x - bw * 1.25, y - 118 * s, x + bw * 1.25, y - 102 * s), 8 * s,
            fill=clay, outline=shade(cd, 0.8), owidth=2 * s)
    hr = 30 * s
    hy = y - 150 * s - hr
    g.circle(x, hy, hr, fill=clay, outline=shade(cd, 0.8), owidth=2.4 * s)
    if hat:
        g.pieslice((x - hr * 2.1, hy - hr * 1.9, x + hr * 2.1, hy + hr * 1.1),
                   180, 360, fill=shade(cd, 0.78))
        g.ellipse((x - hr * 0.7, hy - hr * 1.5, x + hr * 0.7, hy - hr * 0.5),
                  fill=clay)
    if face:
        ey = hy + 2 * s
        for px in (-1, 1):
            g.circle(x + px * 11 * s, ey, 3.4 * s, fill=cd)
        g.arc((x - 10 * s, ey + 4 * s, x + 10 * s, ey + 16 * s), 15, 165, cd, 3 * s)


# ---------------------------------------------------------------- 古墳


def keyhole_tomb(g, cx, cy, s, mound=None, mound_d=None, moat=None,
                 haniwa_dots=True, seed=0):
    """前方後円墳 (俯瞰). s=1 で全長約 460px. 後円部中心 (cx,cy), 前方部は上."""
    mound = mound or (108, 168, 96)
    mound_d = mound_d or (82, 132, 74)
    moat = moat or (116, 170, 200)
    rr = 105 * s
    fw = 58 * s        # 前方部付け根半幅
    ftw = 96 * s       # 前方部端半幅
    fl = 280 * s       # 前方部長
    top_y = cy - rr - fl

    def trap(w_end, w_root, length):
        return [(cx + w_end, cy - rr - length), (cx + w_root, cy - rr * 0.9),
                (cx - w_root, cy - rr * 0.9), (cx - w_end, cy - rr - length)]

    # 堀
    g.circle(cx, cy, rr * 1.58, fill=moat)
    g.poly(trap(ftw * 1.5, fw * 1.85, fl * 1.2), fill=moat)
    # 堀の波紋
    rnd = random.Random(seed)
    for _ in range(8):
        a = rnd.uniform(0, math.tau)
        d = rr * rnd.uniform(1.62, 1.78)
        px, py = cx + math.cos(a) * d, cy + math.sin(a) * d
        g.arc((px - 10 * s, py - 5 * s, px + 10 * s, py + 5 * s), 200, 340,
              with_alpha((235, 246, 252), 130), 2.2 * s)
    # 墳丘 (影 → 本体)
    g.circle(cx, cy + 3 * s, rr * 1.03, fill=mound_d)
    g.poly([(px + 3 * s, py + 4 * s) for (px, py) in trap(ftw, fw, fl)], fill=mound_d)
    g.circle(cx, cy - 2 * s, rr, fill=mound)
    g.poly(trap(ftw, fw, fl), fill=mound)
    # 造出・テラス
    g.circle(cx, cy + rr * 0.3, rr * 0.52, fill=tint(mound, 0.1))
    g.poly([(cx - ftw * 0.62, cy - fl * 0.84), (cx + ftw * 0.62, cy - fl * 0.84),
            (cx + fw * 0.36, cy - fl * 0.1), (cx - fw * 0.36, cy - fl * 0.1)],
           fill=tint(mound, 0.14))
    # 後円部頂の石室痕
    g.ellipse((cx - 12 * s, cy + rr * 0.55 - 12 * s, cx + 12 * s, cy + rr * 0.55 + 12 * s),
              fill=shade(mound_d, 0.85))
    if haniwa_dots:
        for (hx, hy) in [(cx - rr * 0.95, cy - rr * 0.2), (cx + rr * 0.95, cy - rr * 0.2),
                         (cx - rr * 0.8, cy + rr * 0.8), (cx + rr * 0.8, cy + rr * 0.8),
                         (cx - ftw * 0.88, cy - fl * 0.72),
                         (cx + ftw * 0.88, cy - fl * 0.72)]:
            g.circle(hx, hy, 6.5 * s, fill=P.CLAY, outline=P.CLAY_D, owidth=1.8 * s)


# ---------------------------------------------------------------- 舟・道具


def boat(g, x, y, s, hull=None, hull_d=None, oars=2, figure=False, seed=0):
    """丸木舟 (側面). s=1 で長さ約 240px. y=喫水線."""
    hull = hull or P.WOOD
    hull_d = hull_d or P.WOOD_D
    L = 120 * s
    g.ellipse((x - L * 1.05, y + 4 * s, x + L * 1.05, y + 16 * s),
              fill=with_alpha((30, 48, 70), 80))
    top = ([(x - L, y - 34 * s)]
           + qbez((x - L, y - 34 * s), (x - L * 0.25, y - 16 * s), (x, y - 14 * s), 10)
           + qbez((x, y - 14 * s), (x + L * 0.25, y - 16 * s), (x + L, y - 38 * s), 10))
    bot = ([(x + L * 0.98, y + 2 * s)]
           + qbez((x + L * 0.98, y + 2 * s), (x + L * 0.2, y + 14 * s), (x, y + 15 * s), 10)
           + qbez((x, y + 15 * s), (x - L * 0.2, y + 14 * s), (x - L * 0.98, y + 2 * s), 10))
    g.poly(top + bot, fill=hull, outline=shade(hull_d, 0.8), owidth=2.4 * s)
    g.line(top, shade(hull_d, 0.75), 4 * s)
    for i in range(3):
        g.line([(x - L * 0.5, y - 12 * s + i * 3 * s),
                (x + L * 0.5, y - 12 * s + i * 3 * s)], shade(hull, 0.85), 2 * s)
    rnd = random.Random(seed)
    for i in range(oars):
        px = x + (-0.45 + 0.5 * i) * L
        ang = 0.5 + rnd.uniform(-0.15, 0.15)
        ex = px + math.sin(ang) * 40 * s
        g.line([(px, y - 20 * s), (ex, y + 26 * s)], shade(hull_d, 0.9), 4 * s)
        g.ellipse((ex - 8 * s, y + 24 * s, ex + 8 * s, y + 40 * s),
                  fill=shade(hull_d, 0.85))
    if figure:
        fx = x - L * 0.35
        g.circle(fx, y - 74 * s, 10 * s, fill=P.INK)
        g.poly([(fx - 12 * s, y - 64 * s), (fx + 12 * s, y - 64 * s),
                (fx + 8 * s, y - 18 * s), (fx - 8 * s, y - 18 * s)], fill=P.INK)
        g.line([(fx, y - 58 * s), (fx + 34 * s, y - 30 * s)], P.INK, 4 * s)
        g.line([(fx + 34 * s, y - 30 * s), (fx + 30 * s, y + 16 * s)], P.INK, 3 * s)


def campfire(g, x, y, s, glow=True, stones=True, seed=0):
    """焚き火. s=1 で高さ約 170px."""
    rnd = random.Random(seed)
    if glow:
        gl = radial((int(360 * s * g.ss), int(300 * s * g.ss)), (255, 190, 110),
                    alpha_in=110, power=2.2)
        g.img.alpha_composite(gl, (int((x - 180 * s) * g.ss), int((y - 210 * s) * g.ss)))
    if stones:
        for i in range(7):
            a = math.pi * (0.15 + 0.7 * i / 6)
            px = x + math.cos(a) * 52 * s
            py = y + math.sin(a) * 16 * s
            g.ellipse((px - 9 * s, py - 6 * s, px + 9 * s, py + 6 * s), fill=P.STONE_D)
    for dx in (-16, 16, 0):
        lx = x + dx * s
        g.rrect((lx - 30 * s, y - 12 * s, lx + 30 * s, y + 2 * s), 5 * s, fill=P.WOOD_D)

    def flame(wid, hh, col):
        pts = (qbez((x - wid, y - 6 * s), (x - wid * 0.9, y - hh * 0.45),
                    (x - wid * 0.12, y - hh * 0.62), 10)
               + qbez((x - wid * 0.12, y - hh * 0.62), (x - wid * 0.05, y - hh),
                      (x, y - hh), 6)
               + qbez((x, y - hh), (x + wid * 0.06, y - hh * 0.98),
                      (x + wid * 0.12, y - hh * 0.6), 6)
               + qbez((x + wid * 0.12, y - hh * 0.6), (x + wid * 0.9, y - hh * 0.45),
                      (x + wid, y - 6 * s), 10))
        g.poly(pts, fill=col)

    flame(30 * s, 120 * s * rnd.uniform(0.9, 1.05), P.SHU)
    flame(22 * s, 95 * s, P.SHU_D)
    flame(15 * s, 70 * s, P.YAMABUKI)
    flame(8 * s, 44 * s, (255, 238, 180))
    smoke_wisp(g, x + 6 * s, y - 130 * s, s, seed=seed + 1)


def stone_tools(g, x, y, s, seed=0):
    """打製石器 (石斧・ナイフ) を台石の上に."""
    g.ellipse((x - 60 * s, y - 16 * s, x + 60 * s, y + 12 * s), fill=P.STONE_D)
    g.ellipse((x - 60 * s, y - 22 * s, x + 60 * s, y - 4 * s), fill=P.STONE)
    ax = x - 26 * s
    pts = (qbez((ax - 16 * s, y - 24 * s), (ax - 22 * s, y - 60 * s), (ax, y - 86 * s), 12)
           + qbez((ax, y - 86 * s), (ax + 22 * s, y - 60 * s), (ax + 16 * s, y - 24 * s), 12))
    g.poly(pts, fill=(150, 148, 142), outline=(110, 108, 102), owidth=2 * s)
    g.poly(qbez((ax - 8 * s, y - 30 * s), (ax - 11 * s, y - 56 * s), (ax - 3 * s, y - 76 * s), 8)
           + [(ax + 3 * s, y - 70 * s), (ax - 4 * s, y - 34 * s)],
           fill=(178, 176, 170))
    nx = x + 28 * s
    pts = ([(nx - 10 * s, y - 20 * s)]
           + qbez((nx - 10 * s, y - 20 * s), (nx - 18 * s, y - 52 * s), (nx, y - 72 * s), 10)
           + qbez((nx, y - 72 * s), (nx + 18 * s, y - 52 * s), (nx + 10 * s, y - 20 * s), 10)
           + [(nx + 10 * s, y - 20 * s)])
    g.poly(pts, fill=(140, 138, 132), outline=(104, 102, 96), owidth=2 * s)
    for k in range(3):
        g.poly([(nx - 6 * s + k * 5 * s, y - 28 * s - k * 12 * s),
                (nx - 10 * s + k * 5 * s, y - 40 * s - k * 10 * s),
                (nx - 2 * s + k * 5 * s, y - 36 * s - k * 12 * s)],
               fill=(170, 168, 162))


def bones(g, x, y, s, seed=0):
    rnd = random.Random(seed)
    for i in range(3):
        bx = x + (i - 1) * 34 * s + rnd.uniform(-6, 6)
        ang = rnd.uniform(-0.3, 0.3)
        dx, dy = math.cos(ang) * 26 * s, math.sin(ang) * 8 * s
        g.line([(bx - dx, y - dy), (bx + dx, y + dy)], (222, 214, 196), 5 * s)
        for ex in (-1, 1):
            g.circle(bx + ex * dx, y + ex * dy, 4.5 * s, fill=(232, 226, 210))


def draw_acorn(g, x, y, s, cap=(122, 84, 50), body=(214, 168, 108)):
    g.ellipse((x - 7 * s, y - 8 * s, x + 7 * s, y + 9 * s), fill=body)
    g.pieslice((x - 9 * s, y - 14 * s, x + 9 * s, y - 1 * s), 180, 360, fill=cap)
    g.line([(x, y - 13 * s), (x + 3 * s, y - 19 * s)], cap, 2.4 * s)


def deer(g, x, y, s, col=(122, 90, 66), dark=(92, 66, 48), antlers=True, flip=1):
    """鹿 (側面). s=1 で肩高約 120px. y=地面."""
    bd, bh = 62 * s, 46 * s
    by = y - bh * 2.4
    for (dx, ph) in [(-44, 0), (-26, 4), (26, 4), (44, 0)]:
        px = x + dx * s
        g.line([(px, by + bh - 6 * s), (px, y - ph * s)], dark, 7 * s)
    g.ellipse((x - bd, by, x + bd, by + bh), fill=col)
    nx = x + flip * (bd - 6 * s)
    g.poly([(nx - 12 * s, by + 8 * s), (nx + 12 * s, by + 8 * s),
            (nx + flip * 26 * s, by - 52 * s), (nx + flip * 6 * s, by - 56 * s)],
           fill=col)
    hx, hy = nx + flip * 30 * s, by - 58 * s
    g.ellipse((hx - 20 * s, hy - 13 * s, hx + 20 * s, hy + 13 * s), fill=col)
    _a, _b = sorted((hx + flip * 12 * s, hx + flip * 26 * s))
    g.ellipse((_a, hy - 8 * s, _b, hy + 4 * s), fill=col)
    g.circle(hx + flip * 8 * s, hy - 4 * s, 2.6 * s, fill=(40, 30, 28))
    if antlers:
        for (dx, ln) in [(4, 26), (12, 20)]:
            bx = hx - 2 * s + dx * s * flip
            g.line([(bx, hy - 8 * s), (bx + flip * 6 * s, hy - 8 * s - ln * s)], dark, 3.4 * s)
            g.line([(bx + flip * 4 * s, hy - 8 * s - ln * s * 0.55),
                    (bx + flip * 16 * s, hy - 12 * s - ln * s * 0.5)], dark, 3 * s)
    g.ellipse((x - flip * (bd + 2) * s - 8 * s, by + 2 * s,
               x - flip * (bd + 2) * s + 10 * s, by + 16 * s), fill=(232, 222, 205))
    rnd = random.Random(7)
    for _ in range(5):
        px = x + rnd.uniform(-bd * 0.7, bd * 0.7)
        py = by + bh * rnd.uniform(0.25, 0.7)
        g.circle(px, py, 4 * s, fill=(210, 190, 165))


def boar(g, x, y, s, col=(86, 70, 60), dark=(60, 48, 42), flip=1):
    """イノシシ (側面). s=1 で体長約 160px."""
    bd, bh = 80 * s, 48 * s
    by = y - bh * 2.0
    for (dx, ph) in [(-56, 0), (-34, 3), (34, 3), (56, 0)]:
        px = x + dx * s
        g.line([(px, by + bh - 4 * s), (px, y - ph * s)], dark, 8 * s)
    g.ellipse((x - bd, by, x + bd, by + bh), fill=col)
    hx = x - flip * (bd + 10 * s)
    g.poly([(x - flip * bd * 0.6, by + 6 * s), (hx, by + 10 * s),
            (hx, by + bh * 0.8), (x - flip * bd * 0.7, by + bh)], fill=col)
    g.circle(hx + flip * 4 * s, by + bh * 0.45, 3 * s, fill=(30, 24, 22))
    # 牙
    _a, _b = sorted((hx - flip * 16 * s, hx + flip * 6 * s))
    g.arc((_a, by + bh * 0.3, _b, by + bh * 0.7),
          200 if flip > 0 else 340, 340 if flip > 0 else 140, (240, 232, 210), 4 * s)
    # 背のたてがみ
    for i in range(5):
        px = x - flip * (bd * 0.5) + flip * i * 30 * s * (1 if flip > 0 else 1)
        g.poly([(px, by - 2 * s), (px + 10 * s, by - 14 * s), (px + 20 * s, by - 2 * s)],
               fill=dark)


# ---------------------------------------------------------------- 弥生の村部品


def palisade(g, x0, x1, y, s, col=(96, 66, 48), dark=(70, 48, 36), gate_x=None,
             gate_w=120, seed=0):
    """柵列 (尖った柱 + 横板). gate_x/gate_w で出入口を開ける."""
    rnd = random.Random(seed)
    step = 44 * s
    x = x0
    while x <= x1:
        skip = gate_x is not None and gate_x <= x <= gate_x + gate_w
        if not skip:
            ph = (70 + rnd.uniform(0, 22)) * s
            g.poly([(x - 9 * s, y), (x - 9 * s, y - ph), (x, y - ph - 16 * s),
                    (x + 9 * s, y - ph), (x + 9 * s, y)], fill=col,
                   outline=dark, owidth=1.8 * s)
        x += step
    g.line([(x0, y - 40 * s), (x1, y - 40 * s)], dark, 5 * s)


def seedling(g, x, y, s):
    for dx in (-5, 0, 5):
        g.line([(x + dx * s * 0.4, y), (x + dx * s, y - 14 * s)], P.WAKAKUSA_D, 2.4 * s)


def rice_paddy(cv, y0, y1, sky_ref, seed=0, levee=(122, 98, 66), rows_seed=0):
    """水田帯 (空の反射 + 畦 + 稲の列)."""
    g = cv.g()
    rnd = random.Random(seed)
    y = y0
    while y < y1 - 40:
        bh = rnd.uniform(46, 78)
        b0, b1 = y, min(y + bh, y1)
        t = (b0 + b1) / 2 / cv.h
        col = mix(sky_ref[0], sky_ref[1], min(1.0, max(0.0, t)))
        g.poly([(0, b0), (cv.w, b0), (cv.w, b1), (0, b1)], fill=col)
        for _ in range(6):
            yy = rnd.uniform(b0 + 6, max(b0 + 8, b1 - 6))
            ln = rnd.uniform(40, 150)
            xx = rnd.uniform(0, cv.w - ln)
            g.rrect((xx, yy, xx + ln, yy + 3), 2, fill=with_alpha((255, 255, 255), 60))
        g.line([(0, b1), (cv.w, b1)], levee, 5)
        for r_i in range(3):
            ry = b0 + (b1 - b0) * (r_i + 0.5) / 3
            n = int(cv.w / (26 - 7 * r_i))
            rr2 = random.Random(rows_seed + int(ry))
            for i in range(n):
                xx = (i + rr2.uniform(-0.2, 0.2)) * cv.w / n
                seedling(g, xx, ry + rr2.uniform(-4, 4), 0.8 + 0.12 * r_i)
        y = b1 + 7


def torch(g, x, y, s, flame=True, seed=0):
    """松明. y=地面."""
    g.line([(x, y), (x, y - 90 * s)], P.WOOD_D, 8 * s)
    g.ellipse((x - 12 * s, y - 100 * s, x + 12 * s, y - 76 * s), fill=(60, 44, 36))
    if flame:
        for (wid, hh, col) in [(13, 34, P.SHU), (9, 26, P.YAMABUKI), (5, 16, (255, 238, 180))]:
            g.poly(qbez((x - wid, y - 84 * s), (x - wid, y - 84 * s - hh * 0.6),
                        (x, y - 84 * s - hh), 8)
                   + qbez((x, y - 84 * s - hh), (x + wid, y - 84 * s - hh * 0.6),
                          (x + wid, y - 84 * s), 8),
                   fill=col)
        gl = radial((int(90 * s * g.ss), int(90 * s * g.ss)), (255, 190, 110),
                    alpha_in=90, power=2.0)
        g.img.alpha_composite(gl, (int((x - 45 * s) * g.ss), int((y - 130 * s) * g.ss)))


def banner_pole(g, x, y, s, flag=P.SHU, seed=0):
    """旗ポール (大和政権の目印風)."""
    g.line([(x, y), (x, y - 260 * s)], P.WOOD_D, 9 * s)
    g.circle(x, y - 266 * s, 8 * s, fill=P.YAMABUKI, outline=shade(P.YAMABUKI, 0.7), owidth=2)
    top = y - 240 * s
    pts = (qbez((x + 8 * s, top), (x + 90 * s, top + 6 * s), (x + 150 * s, top + 18 * s), 12)
           + qbez((x + 150 * s, top + 18 * s), (x + 100 * s, top + 60 * s),
                  (x + 8 * s, top + 108 * s), 12))
    pts += [(x + 8 * s, top), ]
    g.poly(pts, fill=flag, outline=shade(flag, 0.75), owidth=2.4 * s)
    g.circle(x + 74 * s, top + 46 * s, 16 * s, outline=P.UI_WHITE, owidth=3.5 * s)


# ================================================================ ep02 (飛鳥・奈良)


def curved_roof(g, cx, ye, rw, tw, rh, roof=None, roof_d=None, lift=12.0,
                sag=10.0, outline_d=True, s=1.0):
    """反りを持つ東屋根 (軒が両端で持ち上がる). ye=軒の基準Y."""
    roof = roof or P.TILE
    roof_d = roof_d or P.TILE_D
    pts = ([(cx - tw, ye - rh), (cx + tw, ye - rh)]
           + qbez((cx + tw, ye - rh), (cx + rw * 0.82, ye - rh * 0.25),
                  (cx + rw, ye - lift), 10)
           + qbez((cx + rw, ye - lift), (cx, ye + sag), (cx - rw, ye - lift), 12)
           + qbez((cx - rw, ye - lift), (cx - rw * 0.82, ye - rh * 0.25),
                  (cx - tw, ye - rh), 10))
    g.poly(pts, fill=roof, outline=roof_d if outline_d else None, owidth=2.6 * s)
    # 棟と軒の陰
    g.line([(cx - tw, ye - rh + 2 * s), (cx + tw, ye - rh + 2 * s)], shade(roof_d, 0.8), 4 * s)
    g.arc((cx - rw * 0.96, ye - 8 * s, cx + rw * 0.96, ye + 12 * s),
          200, 340, shade(roof_d, 0.75), 3 * s)
    return pts


def pagoda(g, x, y, s, roof=None, roof_d=None, wall=None, frame=None,
           base=(176, 168, 152), seed=0):
    """法隆寺風五重塔. s=1 で高さ約 660px・y=地面."""
    roof = roof or P.TILE
    roof_d = roof_d or P.TILE_D
    wall = wall or P.PLASTER
    frame = frame or P.VERMILION_WOOD
    # 地面影 + 基壇
    g.ellipse((x - 190 * s, y - 10 * s, x + 190 * s, y + 14 * s),
              fill=with_alpha((70, 60, 50), 70))
    g.rrect((x - 155 * s, y - 26 * s, x + 155 * s, y), 8 * s, fill=base,
            outline=shade(base, 0.78), owidth=3 * s)
    g.line([(x - 155 * s, y - 22 * s), (x + 155 * s, y - 22 * s)], shade(base, 0.9), 3 * s)
    ye = y - 26 * s  # 基壇上端
    bw = 118 * s     # 初層の身舎半幅
    body_h = 62 * s
    roof_h = 34 * s
    for i in range(5):
        # 身舎 (白壁 + 朱の柱)
        rect(g, x - bw, ye - body_h, x + bw, ye, fill=wall,
               outline=shade(wall, 0.8), owidth=2.2 * s)
        for px in (-bw + 8 * s, bw - 18 * s):
            rect(g, x + px, ye - body_h, x + px + 10 * s, ye, fill=frame)
        if i == 0:
            g.rrect((x - 24 * s, ye - body_h + 10 * s, x + 24 * s, ye - 4 * s), 8 * s,
                    fill=shade(frame, 0.82))
            g.line([(x, ye - body_h + 10 * s), (x, ye - 4 * s)], shade(frame, 0.7), 3 * s)
        elif i == 2:
            rect(g, x - 30 * s, ye - body_h + 16 * s, x + 30 * s, ye - 12 * s,
                   fill=shade(frame, 0.85))
        ye -= body_h
        # 屋根 (次層の身舎より広く)
        rw = bw + 62 * s - i * 8 * s
        tw = (bw - 14 * s) if i < 4 else 16 * s
        curved_roof(g, x, ye, rw, tw, roof_h, roof, roof_d, s=s)
        ye -= roof_h + 8 * s
        bw -= 13 * s
    # 相輪
    px = x
    g.line([(px, ye + 6 * s), (px, ye - 78 * s)], P.GOLD, 5 * s)
    for k in range(9):
        g.circle(px, ye - 8 * s - k * 7.6 * s, 6.5 * s, outline=P.GOLD, owidth=2.6 * s)
    g.poly(qbez((px - 8 * s, ye - 76 * s), (px, ye - 96 * s), (px + 8 * s, ye - 76 * s), 8),
           fill=P.GOLD)


def kondo(g, x, y, s, roof=None, roof_d=None, wall=None, frame=None,
          base=(176, 168, 152), seed=0):
    """金堂風の仏堂 (2階屋根+裳階). s=1 で幅約 560px・y=地面."""
    roof = roof or P.TILE
    roof_d = roof_d or P.TILE_D
    wall = wall or P.PLASTER
    frame = frame or P.VERMILION_WOOD
    g.ellipse((x - 280 * s, y - 10 * s, x + 280 * s, y + 14 * s),
              fill=with_alpha((70, 60, 50), 70))
    # 基壇
    g.rrect((x - 255 * s, y - 30 * s, x + 255 * s, y), 8 * s, fill=base,
            outline=shade(base, 0.78), owidth=3 * s)
    # 裳階 (下屋)
    sk_h = 46 * s
    rect(g, x - 230 * s, y - 30 * s - sk_h, x + 230 * s, y - 30 * s, fill=shade(wall, 0.92))
    for px in range(-218, 219, 48):
        rect(g, x + px * s, y - 30 * s - sk_h, x + px * s + 11 * s, y - 30 * s, fill=frame)
    curved_roof(g, x, y - 30 * s - sk_h, 258 * s, 208 * s, 30 * s, roof, roof_d, s=s)
    y2 = y - 30 * s - sk_h - 34 * s
    # 身舎 (1階)
    bh = 118 * s
    rect(g, x - 205 * s, y2 - bh, x + 205 * s, y2, fill=wall,
           outline=shade(wall, 0.8), owidth=2.4 * s)
    for px in (-193, -145, 145, 193):
        rect(g, x + px * s, y2 - bh, x + px * s + 12 * s, y2, fill=frame)
    for px in (-96, 0, 96):
        g.rrect((x + px * s - 22 * s, y2 - bh + 14 * s, x + px * s + 22 * s, y2 - 10 * s),
                8 * s, fill=shade(frame, 0.8))
    y2 -= bh
    # 上部の小屋根
    curved_roof(g, x, y2, 238 * s, 60 * s, 36 * s, roof, roof_d, s=s)


def daibutsu(g, x, y, s, bronze=None, bronze_d=None, seed=0):
    """東大寺大仏 (坐像・光背・蓮華座). s=1 で高さ約 430px. y=地面."""
    bronze = bronze or P.BRONZE
    bronze_d = bronze_d or P.BRONZE_D
    hr = 52 * s
    hy = y - 322 * s
    # 光背
    g.circle(x, hy, 168 * s, fill=with_alpha(P.GOLD, 60))
    g.circle(x, hy, 168 * s, outline=P.GOLD, owidth=7 * s)
    g.circle(x, hy, 138 * s, outline=with_alpha(P.GOLD, 200), owidth=3.4 * s)
    rnd = random.Random(seed)
    for k in range(14):
        a = math.pi * (0.12 + 0.76 * k / 13)
        px = x + math.cos(a) * 152 * s
        py = hy + math.sin(a) * 152 * s
        g.circle(px, py, 5 * s, fill=with_alpha(P.GOLD, 220))
    # 蓮華座
    g.ellipse((x - 130 * s, y - 58 * s, x + 130 * s, y), fill=shade(bronze_d, 0.8))
    g.ellipse((x - 122 * s, y - 74 * s, x + 122 * s, y - 16 * s), fill=bronze_d,
              outline=shade(bronze_d, 0.7), owidth=2.6 * s)
    for k in range(9):
        px = x - 108 * s + k * 27 * s
        g.ellipse((px - 12 * s, y - 70 * s, px + 12 * s, y - 26 * s),
                  fill=bronze, outline=shade(bronze_d, 0.75), owidth=2 * s)
    # 像身 (袈裟をまとった坐像)
    body = (qbez((x - 96 * s, y - 250 * s), (x - 118 * s, y - 170 * s), (x - 104 * s, y - 96 * s), 12)
            + [(x + 104 * s, y - 96 * s)]
            + qbez((x + 104 * s, y - 96 * s), (x + 118 * s, y - 170 * s), (x + 96 * s, y - 250 * s), 12))
    g.poly(body + [(x + 70 * s, y - 282 * s), (x - 70 * s, y - 282 * s)],
           fill=bronze, outline=shade(bronze_d, 0.72), owidth=2.6 * s)
    # 膝と衣の襞
    g.ellipse((x - 96 * s, y - 130 * s, x - 34 * s, y - 74 * s), fill=bronze,
              outline=shade(bronze_d, 0.7), owidth=2.2 * s)
    g.ellipse((x + 34 * s, y - 130 * s, x + 96 * s, y - 74 * s), fill=bronze,
              outline=shade(bronze_d, 0.7), owidth=2.2 * s)
    for dx in (-52, -22, 12, 44):
        g.line(qbez((x + dx * s, y - 244 * s), (x + dx * s * 1.3, y - 170 * s),
                    (x + dx * s * 1.15, y - 100 * s), 10),
               shade(bronze_d, 0.78), 3.2 * s)
    # 結跏趺坐の手
    g.ellipse((x - 34 * s, y - 116 * s, x + 34 * s, y - 88 * s), fill=tint(bronze, 0.12),
              outline=shade(bronze_d, 0.72), owidth=2.2 * s)
    g.ellipse((x - 16 * s, y - 108 * s, x + 16 * s, y - 94 * s), fill=bronze)
    # 頭部 (螺髪 + 白髻)
    g.circle(x, hy, hr, fill=bronze, outline=shade(bronze_d, 0.72), owidth=2.6 * s)
    g.circle(x, hy - hr + 6 * s, 12 * s, fill=bronze, outline=shade(bronze_d, 0.72), owidth=2 * s)
    for k in range(7):
        px = x - hr * 0.62 + k * hr * 0.2
        g.circle(px, hy - hr * 0.52, 6.5 * s, fill=shade(bronze_d, 0.86))
    # 静寂の顔 (閉じた目・長い耳たぶ)
    for sx in (-1, 1):
        g.arc((x + sx * 8 * s - 12 * s, hy - 8 * s, x + sx * 8 * s + 12 * s, hy + 8 * s),
              20, 160, shade(bronze_d, 0.6), 3.2 * s)
        g.ellipse((x + sx * hr * 0.92 - 7 * s, hy - 6 * s, x + sx * hr * 0.92 + 7 * s,
                   hy + 30 * s), fill=bronze, outline=shade(bronze_d, 0.72), owidth=2 * s)
    g.arc((x - 10 * s, hy + 22 * s, x + 10 * s, hy + 32 * s), 15, 165,
          shade(bronze_d, 0.6), 3 * s)


def envoy_ship(g, x, y, s, sails=2, flag=True, figures=False, seed=0):
    """遣唐使船. s=1 で全長約 440px. y=喫水線."""
    hull = P.WOOD
    hull_d = P.WOOD_D
    L = 220 * s
    g.ellipse((x - L * 1.06, y + 6 * s, x + L * 1.06, y + 20 * s),
              fill=with_alpha((30, 48, 70), 80))
    top = ([(x - L, y - 52 * s)]
           + qbez((x - L, y - 52 * s), (x - L * 0.3, y - 30 * s), (x, y - 26 * s), 12)
           + qbez((x, y - 26 * s), (x + L * 0.3, y - 30 * s), (x + L, y - 56 * s), 12))
    bot = ([(x + L * 0.98, y + 2 * s)]
           + qbez((x + L * 0.98, y + 2 * s), (x + L * 0.2, y + 16 * s), (x, y + 17 * s), 12)
           + qbez((x, y + 17 * s), (x - L * 0.2, y + 16 * s), (x - L * 0.98, y + 2 * s), 12))
    g.poly(top + bot, fill=hull, outline=shade(hull_d, 0.8), owidth=2.6 * s)
    g.line(top, shade(hull_d, 0.75), 4 * s)
    for i in range(3):
        g.line([(x - L * 0.72, y - 30 * s + i * 10 * s), (x + L * 0.72, y - 30 * s + i * 10 * s)],
               shade(hull, 0.82), 2.2 * s)
    # 帆 (むしろ製の四角帆)
    mast_h = 190 * s
    mast_xs = [x - 90 * s, x + 80 * s] if sails >= 2 else [x]
    for mi, mx in enumerate(mast_xs[:sails]):
        g.line([(mx, y - 30 * s), (mx, y - 30 * s - mast_h)], P.WOOD_D, 7 * s)
        sw = 86 * s
        sh = 128 * s
        sy = y - 40 * s - mast_h + 34 * s
        sail_pts = (qbez((mx - sw / 2, sy), (mx, sy + 10 * s), (mx + sw / 2, sy + 4 * s), 10)
                    + qbez((mx + sw / 2, sy + 4 * s), (mx + sw / 2 + 6 * s, sy + sh / 2),
                           (mx + sw / 2 - 2 * s, sy + sh), 10)
                    + qbez((mx + sw / 2 - 2 * s, sy + sh), (mx, sy + sh + 8 * s),
                           (mx - sw / 2, sy + sh - 4 * s), 10)
                    + qbez((mx - sw / 2, sy + sh - 4 * s), (mx - sw / 2 - 6 * s, sy + sh / 2),
                           (mx - sw / 2, sy), 10))
        g.poly(sail_pts, fill=(222, 206, 162), outline=shade((180, 164, 120), 0.9), owidth=2.4 * s)
        for k in range(1, 5):
            yy = sy + sh * k / 5
            g.line([(mx - sw * 0.44, yy), (mx + sw * 0.44, yy - 2 * s)],
                   shade((180, 164, 120), 0.85), 2 * s)
    # 櫂
    rnd = random.Random(seed)
    for i in range(3):
        px = x - L * 0.5 + i * L * 0.42
        ex = px + math.sin(0.55 + rnd.uniform(-0.1, 0.1)) * 52 * s
        g.line([(px, y - 28 * s), (ex, y + 30 * s)], shade(hull_d, 0.9), 5 * s)
        g.ellipse((ex - 9 * s, y + 28 * s, ex + 9 * s, y + 46 * s), fill=shade(hull_d, 0.85))
    if figures:
        for fx in (-L * 0.55, L * 0.45):
            fx = x + fx
            g.circle(fx, y - 66 * s, 9 * s, fill=P.INK)
            g.poly([(fx - 10 * s, y - 57 * s), (fx + 10 * s, y - 57 * s),
                    (fx + 7 * s, y - 20 * s), (fx - 7 * s, y - 20 * s)], fill=P.INK)
    if flag:
        fx = x + L * 0.86
        g.line([(fx, y - 54 * s), (fx, y - 110 * s)], P.WOOD_D, 5 * s)
        g.poly([(fx, y - 110 * s), (fx + 44 * s, y - 102 * s), (fx, y - 92 * s)],
               fill=P.SHU, outline=shade(P.SHU, 0.75), owidth=2 * s)


def daigokuden(g, x, y, s, roof=None, roof_d=None, wall=None, frame=None,
               base=(190, 180, 162), lit=False, seed=0):
    """大極殿風の正殿. s=1 で幅約 900px・高さ約 400px. y=地面."""
    roof = roof or P.TILE
    roof_d = roof_d or P.TILE_D
    wall = wall or P.PLASTER
    frame = frame or P.VERMILION_WOOD
    g.ellipse((x - 470 * s, y - 12 * s, x + 470 * s, y + 18 * s),
              fill=with_alpha((70, 60, 50), 70))
    # 石基壇 + 石段
    g.rrect((x - 440 * s, y - 44 * s, x + 440 * s, y), 10 * s, fill=base,
            outline=shade(base, 0.78), owidth=3 * s)
    g.line([(x - 440 * s, y - 38 * s), (x + 440 * s, y - 38 * s)], shade(base, 0.9), 3 * s)
    for k in range(5):
        sw = (150 - k * 24) * s
        yy = y - 9 * s - k * 8.5 * s
        g.rrect((x - sw / 2, yy, x + sw / 2, yy + 9 * s), 3 * s,
                fill=tint(base, 0.18), outline=shade(base, 0.8), owidth=1.6 * s)
    # 身舎 (朱柱+白壁)
    by = y - 44 * s
    bh = 128 * s
    rect(g, x - 380 * s, by - bh, x + 380 * s, by, fill=wall,
           outline=shade(wall, 0.8), owidth=2.6 * s)
    for px in range(-360, 361, 72):
        rect(g, x + px * s, by - bh, x + px * s + 14 * s, by, fill=frame)
    for px in (-288, -180, 180, 288):
        win = with_alpha((255, 216, 130), 220) if lit else shade(frame, 0.62)
        g.rrect((x + px * s - 20 * s, by - bh + 18 * s, x + px * s + 20 * s, by - 14 * s),
                4 * s, fill=win)
        g.line([(x + px * s - 8 * s, by - bh + 18 * s), (x + px * s - 8 * s, by - 14 * s)],
               shade(frame, 0.6), 2.4 * s)
        g.line([(x + px * s + 8 * s, by - bh + 18 * s), (x + px * s + 8 * s, by - 14 * s)],
               shade(frame, 0.6), 2.4 * s)
    y2 = by - bh
    # 大屋根 (2段)
    curved_roof(g, x, y2, 460 * s, 96 * s, 74 * s, roof, roof_d, lift=18 * s, sag=16 * s, s=s)
    y3 = y2 - 80 * s
    curved_roof(g, x, y3, 320 * s, 60 * s, 58 * s, roof, roof_d, lift=16 * s, sag=12 * s, s=s)
    # 棟飾り (上屋根の棟に載せる)
    g.rrect((x - 70 * s, y3 - 74 * s, x + 70 * s, y3 - 58 * s), 6 * s, fill=P.GOLD,
            outline=shade(P.GOLD, 0.72), owidth=2.2 * s)
    for px in (-52, 0, 52):
        g.circle(x + px * s, y3 - 80 * s, 7 * s, fill=P.GOLD)


def mansion(g, x, y, s, roof=None, roof_d=None, wall=None, seed=0, flag=P.SHU):
    """飛鳥の豪族邸宅 (高床母屋+脇屋+板塀+門). s=1 で幅約 760px. y=地面."""
    roof = roof or P.STRAW
    roof_d = roof_d or P.STRAW_D
    wall = wall or (208, 172, 118)
    g.ellipse((x - 390 * s, y - 10 * s, x + 390 * s, y + 16 * s),
              fill=with_alpha((70, 60, 50), 60))
    # 板塀
    wall_top = y - 96 * s
    for px in range(int(-370 * s), int(370 * s), 26):
        if -90 * s <= px <= 90 * s:
            continue
        ph = 84 * s + (abs(px) // 26 % 4) * 6 * s
        rect(g, x + px, wall_top + (96 * s - ph), x + px + 24 * s, y,
               fill=shade(P.WOOD, 0.95), outline=shade(P.WOOD_D, 0.9), owidth=1.6 * s)
    g.line([(x - 370 * s, wall_top + 10 * s), (x + 370 * s, wall_top + 10 * s)],
           shade(P.WOOD_D, 0.85), 4 * s)
    # 門 (屋根つき)
    gx = x - 150 * s
    rect(g, gx - 44 * s, y - 96 * s, gx + 44 * s, y, fill=shade(P.WOOD_D, 0.95))
    rect(g, gx - 34 * s, y - 84 * s, gx + 34 * s, y, fill=shade(wall, 0.72))
    curved_roof(g, gx, y - 96 * s, 64 * s, 40 * s, 26 * s, roof, roof_d, s=s)
    # 母屋 (高床)
    warehouse(g, x + 170 * s, y - 10 * s, 0.85, wall=wall, roof=roof, roof_d=roof_d,
              ladder=True, seed=seed)
    # 脇屋 (小)
    warehouse(g, x + 20 * s, y - 6 * s, 0.52, wall=shade(wall, 0.9), ladder=False, seed=seed + 1)
    # 旗
    banner_pole(g, x - 300 * s, y + 2 * s, 0.8, flag=flag)


def tile_roof_house(g, x, y, s, wall=(226, 214, 190), roof=None, roof_d=None, seed=0):
    """奈良の木造瓦屋住宅. s=1 で幅約 240px. y=地面."""
    roof = roof or P.TILE
    roof_d = roof_d or P.TILE_D
    g.ellipse((x - 130 * s, y - 8 * s, x + 130 * s, y + 12 * s),
              fill=with_alpha((70, 60, 50), 60))
    bh = 92 * s
    bw = 92 * s
    rect(g, x - bw, y - bh, x + bw, y, fill=wall, outline=shade(wall, 0.8), owidth=2.4 * s)
    # 柱
    for px in (-bw + 6 * s, bw - 16 * s):
        rect(g, x + px, y - bh, x + px + 9 * s, y, fill=shade(wall, 0.78))
    # 扉・窓
    g.rrect((x - 22 * s, y - 62 * s, x + 22 * s, y - 4 * s), 6 * s, fill=P.WOOD_D)
    g.rrect((x + 36 * s, y - 66 * s, x + 74 * s, y - 30 * s), 4 * s, fill=shade(wall, 0.62))
    g.rrect((x - 74 * s, y - 66 * s, x - 36 * s, y - 30 * s), 4 * s, fill=shade(wall, 0.62))
    # 入母屋風の瓦屋根
    curved_roof(g, x, y - bh, 138 * s, 46 * s, 44 * s, roof, roof_d, s=s)


def suzakumon(g, x, y, s, roof=None, roof_d=None, wall=None, frame=None,
              base=(186, 178, 160), lit=True, seed=0):
    """朱雀門風の都の正門 (朱の2階建て). s=1 で幅約 460px. y=地面."""
    roof = roof or P.TILE
    roof_d = roof_d or P.TILE_D
    wall = wall or (210, 120, 92)
    frame = frame or P.VERMILION_WOOD
    g.ellipse((x - 260 * s, y - 10 * s, x + 260 * s, y + 16 * s),
              fill=with_alpha((70, 60, 50), 70))
    # 城壁部
    g.rrect((x - 225 * s, y - 64 * s, x + 225 * s, y), 8 * s, fill=base,
            outline=shade(base, 0.76), owidth=3 * s)
    g.line([(x - 225 * s, y - 58 * s), (x + 225 * s, y - 58 * s)], shade(base, 0.9), 3 * s)
    # 門洞
    g.pieslice((x - 42 * s, y - 108 * s, x + 42 * s, y + 40 * s), 180, 360,
               fill=(52, 38, 36))
    rect(g, x - 42 * s, y - 62 * s, x + 42 * s, y, fill=(52, 38, 36))
    # 楼閣 1階
    by = y - 64 * s
    bh = 96 * s
    rect(g, x - 195 * s, by - bh, x + 195 * s, by, fill=wall,
           outline=shade(wall, 0.75), owidth=2.6 * s)
    for px in range(-180, 181, 72):
        rect(g, x + px * s, by - bh, x + px * s + 13 * s, by, fill=frame)
    for px in (-110, 0, 110):
        g.rrect((x + px * s - 24 * s, by - bh + 16 * s, x + px * s + 24 * s, by - 12 * s),
                6 * s, fill=(52, 38, 36) if not lit else with_alpha((255, 216, 130), 210))
    y2 = by - bh
    curved_roof(g, x, y2, 250 * s, 90 * s, 52 * s, roof, roof_d, lift=14 * s, s=s)
    # 2階
    b2y = y2 - 46 * s
    b2h = 72 * s
    rect(g, x - 140 * s, b2y - b2h, x + 140 * s, b2y, fill=shade(wall, 0.92),
           outline=shade(wall, 0.75), owidth=2.6 * s)
    for px in (-128, 128):
        rect(g, x + px * s, b2y - b2h, x + px * s + 13 * s, b2y, fill=frame)
    for px in (-52, 52):
        g.rrect((x + px * s - 20 * s, b2y - b2h + 14 * s, x + px * s + 20 * s, b2y - 10 * s),
                6 * s, fill=(52, 38, 36) if not lit else with_alpha((255, 216, 130), 210))
    curved_roof(g, x, b2y - b2h + 4 * s, 186 * s, 52 * s, 46 * s, roof, roof_d,
                lift=12 * s, s=s)
    # 隅飾り
    for px in (-160, 160):
        g.line([(x + px * s, y - 64 * s), (x + px * s, by - bh)], frame, 10 * s)


def kanmuri(g, cx, cy, s, style="kanmuri", color=(40, 38, 44)):
    """貴族の冠. style: kanmuri(黒)|mikkan(冕冠・金板+赤ひも). (cx,cy)=頭頂."""
    if style == "mikkan":
        # 冕板 (上の金板) + 垂り紐
        g.rrect((cx - 40 * s, cy - 46 * s, cx + 40 * s, cy - 18 * s), 8 * s,
                fill=P.GOLD, outline=shade(P.GOLD, 0.7), owidth=2.4 * s)
        for px in (-28, 0, 28):
            g.circle(cx + px * s, cy - 32 * s, 5 * s, fill=shade(P.GOLD, 0.8))
        for px in (-32, 32):
            g.line(qbez((cx + px * s, cy - 18 * s), (cx + px * s * 1.4, cy + 4 * s),
                        (cx + px * s * 1.2, cy + 26 * s), 10), P.SHU_D, 5 * s)
            g.circle(cx + px * s * 1.2, cy + 28 * s, 4 * s, fill=P.SHU)
        g.rrect((cx - 26 * s, cy - 20 * s, cx + 26 * s, cy + 2 * s), 10 * s, fill=color)
    else:
        # 立烏帽子/幞頭風: 前の抑付 + 鼻先
        g.rrect((cx - 30 * s, cy - 44 * s, cx + 30 * s, cy + 2 * s), 12 * s,
                fill=color, outline=shade(color, 0.6), owidth=2.2 * s)
        g.rrect((cx - 7 * s, cy - 60 * s, cx + 7 * s, cy - 40 * s), 5 * s,
                fill=color, outline=shade(color, 0.6), owidth=2 * s)
        g.line([(cx - 30 * s, cy - 40 * s), (cx + 30 * s, cy - 40 * s)], shade(color, 1.35), 3 * s)
        # 後ろのひも
        g.line(qbez((cx - 24 * s, cy - 6 * s), (cx - 52 * s, cy + 8 * s),
                    (cx - 46 * s, cy + 34 * s), 10), color, 4 * s)
        g.line(qbez((cx + 24 * s, cy - 6 * s), (cx + 52 * s, cy + 8 * s),
                    (cx + 46 * s, cy + 34 * s), 10), color, 4 * s)


def shaku(g, x, y, s, col=(216, 184, 132), deg=-32):
    """笏 (細長の木の板). (x,y)=手で持つ下端."""
    pts = []
    for i in range(9):
        t = i / 8
        pts.append((x + math.cos(math.radians(deg)) * 150 * s * t,
                    y - math.sin(math.radians(deg)) * 150 * s * t))
    g.line(pts, shade(col, 0.6), 15 * s)
    g.line(pts, col, 10 * s)


def grid_blocks(cv, y0, y1, cols=8, seed=0, block=(214, 202, 172),
                road=(232, 226, 208), house_roof=None, density=0.6):
    """平城京の碁盤目 (俯瞰): 区画と屋根の点列."""
    g = cv.g()
    rnd = random.Random(seed)
    house_roof = house_roof or P.TILE
    col_w = cv.w / cols
    rows = max(1, int((y1 - y0) / (col_w * 0.9)))
    row_h = (y1 - y0) / rows
    for r_i in range(rows):
        for c_i in range(cols):
            x0, x1 = c_i * col_w, (c_i + 1) * col_w
            yy0, yy1 = y0 + r_i * row_h, y0 + (r_i + 1) * row_h
            g.poly([(x0 + 3, yy0 + 3), (x1 - 3, yy0 + 3), (x1 - 3, yy1 - 3), (x0 + 3, yy1 - 3)],
                   fill=block)
            # 檜皮葺/瓦の屋根を数軒
            n = int(rnd.uniform(1, 4) * density) + 1
            for _ in range(n):
                hw = rnd.uniform(26, 52)
                hh = rnd.uniform(18, 34)
                hx = rnd.uniform(x0 + 14, x1 - hw - 14)
                hy = rnd.uniform(yy0 + 14, yy1 - hh - 14)
                g.poly([(hx, hy + hh / 2), (hx + hw * 0.12, hy), (hx + hw * 0.88, hy),
                        (hx + hw, hy + hh / 2), (hx + hw * 0.88, hy + hh),
                        (hx + hw * 0.12, hy + hh)], fill=house_roof,
                       outline=shade(house_roof, 0.75), owidth=1.6)
    # 道路グリッド
    for c_i in range(1, cols):
        rect(g, c_i * col_w - 3, y0, c_i * col_w + 3, y1, fill=road)
    for r_i in range(1, rows):
        rect(g, 0, y0 + r_i * row_h - 3, cv.w, y0 + r_i * row_h + 3, fill=road)


# ================================================================ ep03 (平安)


def shinden(g, x, y, s, roof=(118, 132, 100), roof_d=(92, 106, 80), wall=P.PLASTER,
            frame=P.VERMILION_WOOD, seed=0):
    """寝殿造 (寝殿+対屋+渡殿+池+橋). s=1 で幅約 920px. y=池の手前."""
    # 池 (手前)
    g.ellipse((x - 470 * s, y - 66 * s, x + 470 * s, y + 66 * s), fill=(120, 168, 196),
              outline=(88, 132, 162), owidth=3 * s)
    rnd = random.Random(seed)
    for _ in range(10):
        lx = x + rnd.uniform(-420, 420) * s
        ly = y + rnd.uniform(-46, 46) * s
        lr = rnd.uniform(10, 20) * s
        g.ellipse((lx - lr, ly - lr * 0.55, lx + lr, ly + lr * 0.55), fill=(104, 152, 112))
        g.poly([(lx - lr * 0.25, ly - lr * 0.1), (lx + lr * 0.25, ly - lr * 0.1),
                (lx, ly + lr * 0.28)], fill=(96, 144, 104))
    for _ in range(6):
        kx = x + rnd.uniform(-380, 380) * s
        ky = y + rnd.uniform(-40, 40) * s
        g.ellipse((kx - 8 * s, ky - 5 * s, kx + 8 * s, ky + 5 * s),
                  fill=P.YAMABUKI, outline=shade(P.YAMABUKI, 0.7), owidth=1.6 * s)
    # 蓮の花
    for (fx, fy) in [(-330, 26), (310, -20), (390, 30)]:
        px, py = x + fx * s, y + fy * s
        for k in range(5):
            a = -math.pi / 2 + (k - 2) * 0.5
            g.ellipse((px + math.cos(a) * 9 * s - 5 * s, py + math.sin(a) * 9 * s - 5 * s,
                       px + math.cos(a) * 9 * s + 5 * s, py + math.sin(a) * 9 * s + 5 * s),
                      fill=(238, 176, 188))
        g.circle(px, py, 4 * s, fill=P.YAMABUKI)
    # 対屋 (左右の奥)
    for sx in (-1, 1):
        px = x + sx * 360 * s
        by = y - 120 * s
        rect(g, px - 70 * s, by - 84 * s, px + 70 * s, by, fill=wall,
             outline=shade(wall, 0.8), owidth=2.2 * s)
        for wx in (-40, 40):
            rect(g, px + wx * s - 9 * s, by - 70 * s, px + wx * s + 9 * s, by - 12 * s,
                 fill=shade(frame, 0.8))
        curved_roof(g, px, by - 84 * s, 104 * s, 40 * s, 30 * s, roof, roof_d, s=s)
        # 渡殿 (廊下)
        cy_ = by - 40 * s
        step = 1 if sx > 0 else -1
        x0, x1 = (px - 70 * s, x + 190 * s) if sx > 0 else (px + 70 * s, x - 190 * s)
        rect(g, min(x0, x1), cy_ - 26 * s, max(x0, x1), cy_ + 6 * s, fill=shade(wall, 0.94))
        for wx in range(int(min(x0, x1)), int(max(x0, x1)), 60):
            rect(g, wx, cy_ - 26 * s, wx + 8 * s, cy_ + 6 * s, fill=frame)
        g.line([(min(x0, x1), cy_ - 28 * s), (max(x0, x1), cy_ - 28 * s)], roof_d, 8 * s)
        g.line([(min(x0, x1), cy_ - 24 * s), (max(x0, x1), cy_ - 24 * s)], roof, 14 * s)
    # 寝殿 (中央奥)
    by = y - 150 * s
    bh = 110 * s
    bw = 210 * s
    rect(g, x - bw, by - bh, x + bw, by, fill=wall, outline=shade(wall, 0.8), owidth=2.6 * s)
    for px in range(-196, 197, 56):
        rect(g, x + px * s, by - bh, x + px * s + 13 * s, by, fill=frame)
    for px in (-130, 0, 130):
        rect(g, x + px * s - 26 * s, by - bh + 16 * s, x + px * s + 26 * s, by - 12 * s,
             fill=(120, 108, 96))
    curved_roof(g, x, by - bh, 300 * s, 96 * s, 52 * s, roof, roof_d, lift=14 * s, s=s)
    # 池に架かる反り橋
    g.line(qbez((x - 30 * s, y + 40 * s), (x, y - 60 * s), (x + 30 * s, y + 40 * s), 14),
           P.WOOD_D, 9 * s)
    g.line(qbez((x - 30 * s, y + 40 * s), (x, y - 60 * s), (x + 30 * s, y + 40 * s), 14),
           shade(P.WOOD, 1.1), 5 * s)


def amida(g, x, y, s, gold=(226, 190, 118), gold_d=(178, 142, 82), seed=0):
    """阿弥陀如来 (立像・来迎印・光背). s=1 で高さ約 480px. y=地面."""
    hr = 46 * s
    hy = y - 408 * s
    # 光背 (放射)
    g.circle(x, hy, 176 * s, fill=with_alpha(P.GOLD, 46))
    g.circle(x, hy, 176 * s, outline=P.GOLD, owidth=6 * s)
    g.circle(x, hy, 146 * s, outline=with_alpha(P.GOLD, 210), owidth=3 * s)
    for k in range(16):
        a = math.tau * k / 16
        r0, r1 = 84 * s, 168 * s
        g.line([(x + math.cos(a) * r0, hy + math.sin(a) * r0),
                (x + math.cos(a) * r1, hy + math.sin(a) * r1)],
               with_alpha(P.GOLD, 130), 3 * s)
    rnd = random.Random(seed)
    for _ in range(10):
        a = rnd.uniform(0, math.tau)
        d = rnd.uniform(120, 172) * s
        g.circle(x + math.cos(a) * d, hy + math.sin(a) * d, 3.4 * s, fill=P.GOLD)
    # 足下の蓮座 (二重)
    g.ellipse((x - 96 * s, y - 30 * s, x + 96 * s, y + 8 * s), fill=shade(gold_d, 0.8))
    g.ellipse((x - 88 * s, y - 48 * s, x + 88 * s, y - 6 * s), fill=gold_d,
              outline=shade(gold_d, 0.7), owidth=2.4 * s)
    for k in range(9):
        px = x - 78 * s + k * 19.5 * s
        g.ellipse((px - 9 * s, y - 44 * s, px + 9 * s, y - 12 * s), fill=gold,
                  outline=shade(gold_d, 0.75), owidth=1.8 * s)
    # 像身 (立ち姿の袈裟)
    body = (qbez((x - 66 * s, y - 352 * s), (x - 88 * s, y - 250 * s), (x - 60 * s, y - 60 * s), 14)
            + [(x + 60 * s, y - 60 * s)]
            + qbez((x + 60 * s, y - 60 * s), (x + 88 * s, y - 250 * s), (x + 66 * s, y - 352 * s), 14))
    g.poly(body + [(x + 46 * s, y - 380 * s), (x - 46 * s, y - 380 * s)],
           fill=gold, outline=shade(gold_d, 0.72), owidth=2.6 * s)
    # 衣のU字襞
    for dx in (-44, -16, 16, 44):
        g.arc((x + dx * s - 20 * s, y - 240 * s, x + dx * s + 20 * s, y - 170 * s),
              30, 150, shade(gold_d, 0.78), 3 * s)
    # 腕と来迎印 (右手を挙げ、左手を下げて指先で輪)
    arm_l = qbez((x - 60 * s, y - 340 * s), (x - 130 * s, y - 290 * s), (x - 118 * s, y - 208 * s), 12)
    arm_r = qbez((x + 60 * s, y - 340 * s), (x + 128 * s, y - 300 * s), (x + 122 * s, y - 248 * s), 12)
    g.line(arm_l, shade(gold_d, 0.72), 20 * s)
    g.line(arm_l, gold, 14 * s)
    g.line(arm_r, shade(gold_d, 0.72), 20 * s)
    g.line(arm_r, gold, 14 * s)
    g.circle(x - 118 * s, y - 202 * s, 11 * s, fill=gold, outline=shade(gold_d, 0.72), owidth=2 * s)
    g.circle(x + 122 * s, y - 242 * s, 11 * s, fill=gold, outline=shade(gold_d, 0.72), owidth=2 * s)
    g.circle(x - 114 * s, y - 202 * s, 4.5 * s, fill=(255, 244, 214))
    g.circle(x + 126 * s, y - 242 * s, 4.5 * s, fill=(255, 244, 214))
    # 頭部
    g.circle(x, hy, hr, fill=gold, outline=shade(gold_d, 0.72), owidth=2.6 * s)
    g.circle(x, hy - hr + 5 * s, 10 * s, fill=gold, outline=shade(gold_d, 0.72), owidth=2 * s)
    for k in range(7):
        px = x - hr * 0.6 + k * hr * 0.2
        g.circle(px, hy - hr * 0.55, 5.5 * s, fill=shade(gold_d, 0.86))
    for sx in (-1, 1):
        g.arc((x + sx * 8 * s - 11 * s, hy - 7 * s, x + sx * 8 * s + 11 * s, hy + 7 * s),
              20, 160, shade(gold_d, 0.6), 3 * s)
        g.ellipse((x + sx * hr * 0.92 - 6 * s, hy - 5 * s, x + sx * hr * 0.92 + 6 * s,
                   hy + 26 * s), fill=gold, outline=shade(gold_d, 0.72), owidth=2 * s)
    g.arc((x - 9 * s, hy + 20 * s, x + 9 * s, hy + 30 * s), 15, 165, shade(gold_d, 0.6), 3 * s)


def emaki(g, x, y, s, paper=(240, 230, 206), seed=0):
    """鳥獣戯画風の絵巻 (開いた巻物+獣の戯れ). (x,y)=中心."""
    w, h = 430 * s, 220 * s
    # 巻紙 (上下にゆるい波)
    top = qbez((x - w / 2, y - h / 2), (x, y - h / 2 - 10 * s), (x + w / 2, y - h / 2), 12)
    bot = qbez((x - w / 2, y + h / 2), (x, y + h / 2 + 10 * s), (x + w / 2, y + h / 2), 12)
    g.poly(top + bot[::-1], fill=paper, outline=shade(paper, 0.85), owidth=2.4 * s)
    # 詞書の罫 (右側)
    for k in range(4):
        yy = y - h * 0.28 + k * h * 0.17
        g.line([(x + w * 0.18, yy), (x + w * 0.44, yy)], with_alpha((150, 140, 120), 160), 2 * s)
    # 軸 (両端)
    for sx in (-1, 1):
        rx = x + sx * (w / 2 + 12 * s)
        g.rrect((rx - 9 * s, y - h / 2 - 14 * s, rx + 9 * s, y + h / 2 + 14 * s), 8 * s,
                fill=(90, 66, 52), outline=(64, 46, 36), owidth=2.2 * s)
        g.circle(rx, y - h / 2 - 14 * s, 13 * s, fill=(120, 92, 70), outline=(70, 52, 40), owidth=2 * s)
        g.circle(rx, y + h / 2 + 14 * s, 13 * s, fill=(120, 92, 70), outline=(70, 52, 40), owidth=2 * s)
    ink = (72, 62, 56)
    # 兎 (後ろ足で立って枝を持つ)
    rx, ry = x - w * 0.28, y + h * 0.16
    g.ellipse((rx - 20 * s, ry - 46 * s, rx + 20 * s, ry + 6 * s), fill=paper,
              outline=ink, owidth=2.6 * s)
    g.circle(rx, ry - 62 * s, 15 * s, fill=paper, outline=ink, owidth=2.6 * s)
    for sx_ in (-1, 1):
        g.ellipse((rx + sx_ * 6 * s - 4 * s, ry - 92 * s, rx + sx_ * 6 * s + 4 * s, ry - 66 * s),
                  fill=paper, outline=ink, owidth=2.2 * s)
    g.ellipse((rx + 16 * s, ry - 84 * s, rx + 58 * s, ry - 68 * s), fill=(214, 178, 120),
              outline=ink, owidth=2.2 * s)
    g.line([(rx - 12 * s, ry + 4 * s), (rx - 16 * s, ry + 24 * s)], ink, 3.4 * s)
    g.line([(rx + 12 * s, ry + 4 * s), (rx + 16 * s, ry + 24 * s)], ink, 3.4 * s)
    g.circle(rx - 5 * s, ry - 64 * s, 2.2 * s, fill=ink)
    g.line([(rx + 8 * s, ry - 58 * s), (rx + 14 * s, ry - 56 * s)], ink, 2 * s)
    g.poly([(rx - 22 * s, ry - 40 * s), (rx - 44 * s, ry - 30 * s), (rx - 40 * s, ry - 52 * s)],
           fill=paper, outline=ink, owidth=2.2 * s)
    # 蝦蟇 (大口を開けて笑う)
    fx, fy = x + w * 0.04, y + h * 0.2
    g.ellipse((fx - 30 * s, fy - 34 * s, fx + 30 * s, fy + 12 * s), fill=paper,
              outline=ink, owidth=2.6 * s)
    g.pieslice((fx - 22 * s, fy - 14 * s, fx + 22 * s, fy + 20 * s), 0, 180,
               fill=(226, 190, 190), outline=ink, owidth=2.2 * s)
    for sx_ in (-1, 1):
        g.circle(fx + sx_ * 14 * s, fy - 20 * s, 3 * s, fill=ink)
    g.ellipse((fx - 8 * s, fy - 30 * s, fx + 8 * s, fy - 24 * s), fill=ink)
    for sx_ in (-1, 1):
        g.line([(fx + sx_ * 18 * s, fy + 10 * s), (fx + sx_ * 24 * s, fy + 22 * s)], ink, 3.2 * s)
    g.poly([(fx - 30 * s, fy - 16 * s), (fx - 52 * s, fy - 4 * s), (fx - 46 * s, fy - 24 * s)],
           fill=paper, outline=ink, owidth=2.2 * s)
    g.poly([(fx + 30 * s, fy - 16 * s), (fx + 52 * s, fy - 4 * s), (fx + 46 * s, fy - 24 * s)],
           fill=paper, outline=ink, owidth=2.2 * s)
    # 猿 (杖を持って走る)
    mx, my = x + w * 0.30, y + h * 0.22
    g.ellipse((mx - 22 * s, my - 34 * s, mx + 22 * s, my + 4 * s), fill=paper,
              outline=ink, owidth=2.6 * s)
    g.circle(mx, my - 44 * s, 13 * s, fill=paper, outline=ink, owidth=2.6 * s)
    g.circle(mx - 6 * s, my - 48 * s, 2.2 * s, fill=ink)
    g.arc((mx - 2 * s, my - 44 * s, mx + 10 * s, my - 38 * s), 200, 340, ink, 2 * s)
    g.line([(mx - 20 * s, my), (mx - 30 * s, my + 18 * s)], ink, 3.4 * s)
    g.line([(mx + 20 * s, my), (mx + 28 * s, my + 18 * s)], ink, 3.4 * s)
    g.line([(mx + 34 * s, my - 60 * s), (mx + 46 * s, my + 14 * s)], (120, 96, 72), 3.6 * s)
    g.line([(mx + 20 * s, my - 26 * s), (mx + 35 * s, my - 48 * s)], ink, 3 * s)
    # 草の筆致
    for (gx0, gy0) in [(-w * 0.38, h * 0.3), (w * 0.16, h * 0.34), (-w * 0.05, -h * 0.32),
                       (w * 0.38, -h * 0.3)]:
        bx, by = x + gx0, y + gy0
        g.line([(bx, by), (bx - 6 * s, by - 14 * s)], (150, 140, 118), 2.4 * s)
        g.line([(bx, by), (bx + 6 * s, by - 12 * s)], (150, 140, 118), 2.4 * s)


def ox_cart(g, x, y, s, roof=(126, 136, 104), body=(198, 158, 110), curtain=(226, 208, 168),
            ox=(122, 92, 62), seed=0):
    """牛車 (ぎっしゃ). s=1 で全長約 460px. y=地面. 進行方向は左."""
    # 車体
    bx, by = x + 60 * s, y - 96 * s
    g.rrect((bx - 96 * s, by - 96 * s, bx + 96 * s, by), 10 * s, fill=body,
            outline=shade(body, 0.74), owidth=2.6 * s)
    # 御簾 (簾の襞)
    for k in range(7):
        px = bx - 88 * s + k * 26 * s
        rect(g, px, by - 88 * s, px + 13 * s, by - 10 * s, fill=curtain,
               outline=shade(curtain, 0.8), owidth=1.4 * s)
    # 屋根 (檜皮葺の低いドーム)
    pts = (qbez((bx - 112 * s, by - 96 * s), (bx - 70 * s, by - 168 * s), (bx, by - 176 * s), 12)
           + qbez((bx, by - 176 * s), (bx + 70 * s, by - 168 * s), (bx + 112 * s, by - 96 * s), 12))
    g.poly(pts, fill=roof, outline=shade(roof, 0.8), owidth=2.4 * s)
    # 車輪 (大きな放射輻)
    for wx in (bx - 52 * s, bx + 52 * s):
        g.circle(wx, y - 42 * s, 42 * s, fill=(150, 118, 82), outline=(96, 72, 50), owidth=4 * s)
        g.circle(wx, y - 42 * s, 12 * s, fill=(110, 84, 58))
        for k in range(10):
            a = math.tau * k / 10
            g.line([(wx + math.cos(a) * 12 * s, y - 42 * s + math.sin(a) * 12 * s),
                    (wx + math.cos(a) * 38 * s, y - 42 * s + math.sin(a) * 38 * s)],
                   (96, 72, 50), 3.2 * s)
    # 牛 2頭 (手前)
    for i, ox_x in enumerate((x - 130 * s, x - 20 * s)):
        o_y = y + (4 if i else 0) * s
        # 脚
        for lx in (-34, -16, 14, 32):
            g.line([(ox_x + lx * s, o_y - 26 * s), (ox_x + lx * s, o_y - 2 * s)],
                   shade(ox, 0.6), 9 * s)
        # 胴 (肩の瘤つき)
        g.rrect((ox_x - 48 * s, o_y - 80 * s, ox_x + 46 * s, o_y - 20 * s), 24 * s,
                fill=ox, outline=shade(ox, 0.68), owidth=2.6 * s)
        g.ellipse((ox_x - 36 * s, o_y - 98 * s, ox_x + 6 * s, o_y - 58 * s),
                  fill=tint(ox, 0.08), outline=shade(ox, 0.68), owidth=2 * s)
        # 頭部 (前を左に)
        hx = ox_x - 62 * s
        g.ellipse((hx - 26 * s, o_y - 92 * s, hx + 22 * s, o_y - 54 * s), fill=ox,
                  outline=shade(ox, 0.68), owidth=2.4 * s)
        g.ellipse((hx - 26 * s, o_y - 72 * s, hx - 2 * s, o_y - 54 * s),
                  fill=tint(ox, 0.22), outline=shade(ox, 0.6), owidth=2 * s)
        g.line([(hx - 18 * s, o_y - 60 * s), (hx - 6 * s, o_y - 60 * s)],
               shade(ox, 0.55), 2.6 * s)
        # 角 (大きく上に反る)
        for hx2, a0, a1 in ((-16, 150, 300), (0, 210, 360)):
            g.arc((hx + hx2 * s - 12 * s, o_y - 128 * s, hx + hx2 * s + 20 * s, o_y - 80 * s),
                  a0, a1, (236, 230, 216), 7 * s)
        # 耳と目
        g.ellipse((hx + 14 * s, o_y - 96 * s, hx + 30 * s, o_y - 86 * s), fill=ox,
                  outline=shade(ox, 0.6), owidth=1.8 * s)
        g.circle(hx - 12 * s, o_y - 78 * s, 3 * s, fill=(40, 30, 26))
        # 首 (胴と頭をつなぐ)
        g.line([(hx + 18 * s, o_y - 64 * s), (ox_x - 40 * s, o_y - 58 * s)],
               shade(ox, 0.7), 16 * s)
    # 樅 (つなぎ棒)
    g.line([(bx - 96 * s, by - 40 * s), (x - 116 * s, y - 66 * s)], P.WOOD_D, 6 * s)


# ================================================================ ep04 (鎌倉)


def kabuto(g, cx, cy, s, bowl=(70, 52, 48), horns=P.LACQUER_GOLD):
    """武将の兜 (鍬形つき). (cx,cy)=鉢の中心."""
    # 鉢 (頭盔)
    g.pieslice((cx - 34 * s, cy - 36 * s, cx + 34 * s, cy + 34 * s), 180, 360,
               fill=bowl, outline=shade(bowl, 0.7), owidth=2.6 * s)
    # 眉庇 (ひさい)
    g.rrect((cx - 40 * s, cy - 8 * s, cx + 40 * s, cy + 2 * s), 4 * s,
            fill=shade(bowl, 0.85))
    # 鍬形 (金色の月牙)
    for sx in (-1, 1):
        g.line(qbez((cx + sx * 8 * s, cy - 30 * s), (cx + sx * 30 * s, cy - 46 * s),
                    (cx + sx * 38 * s, cy - 62 * s), 10), horns, 6 * s)
    # 頭立物
    g.line([(cx, cy - 32 * s), (cx, cy - 46 * s)], horns, 4 * s)
    # 錣 (首回りの板)
    for k in range(3):
        yy = cy + 4 * s + k * 9 * s
        g.arc((cx - 34 * s - k * 3 * s, yy - 10 * s, cx + 34 * s + k * 3 * s, yy + 12 * s),
              30, 150, shade(bowl, 0.78), 4 * s)
    # 立物の前立 (小さな日輪)
    g.circle(cx - 18 * s, cy - 44 * s, 6 * s, fill=P.SHU, outline=shade(P.SHU, 0.7), owidth=1.6 * s)


def warhorse(g, x, y, s, col=(96, 72, 56), dark=(66, 50, 40), saddle=(140, 52, 44),
             flip=1):
    """武者の馬 (鞍と铃つき). s=1 で体長約 240px. y=地面. flip=1 で左向き."""
    bd, bh = 78 * s, 52 * s
    by = y - bh * 2.5
    # 脚 (関節つき・のった足)
    for (lx, knee) in [(-62, -14), (-40, 12), (34, 14), (58, -12)]:
        px = x + flip * lx * s
        g.line([(px, by + bh - 4 * s), (px + flip * knee * 0.6 * s, y - bh * 1.1)],
               dark, 9 * s)
        g.line([(px + flip * knee * 0.6 * s, y - bh * 1.1), (px + flip * knee * s, y - 4 * s)],
               dark, 7 * s)
        g.rrect((px + flip * knee * s - 6 * s, y - 8 * s, px + flip * knee * s + 6 * s, y),
                3 * s, fill=(40, 34, 32))
    # 胴
    _a, _b = sorted((x - flip * (bd + 10) * s, x + flip * (bd - 6) * s))
    g.rrect((_a, by, _b, by + bh), 22 * s,
            fill=col, outline=dark, owidth=2.6 * s)
    # 首と頭
    nx = x + flip * (bd - 18) * s
    g.poly([(nx - flip * 16 * s, by + 10 * s), (nx + flip * 10 * s, by + 14 * s),
            (nx + flip * 30 * s, by - 44 * s), (nx + flip * 8 * s, by - 50 * s)],
           fill=col, outline=dark, owidth=2.4 * s)
    hx, hy = nx + flip * 32 * s, by - 46 * s
    g.ellipse((hx - 26 * s, hy - 16 * s, hx + 26 * s, hy + 14 * s), fill=col,
              outline=dark, owidth=2.4 * s)
    _a, _b = sorted((hx - flip * 20 * s, hx - flip * 2 * s))
    g.ellipse((_a, hy - 2 * s, _b, hy + 12 * s), fill=shade(col, 0.85))
    g.circle(hx - flip * 10 * s, hy - 4 * s, 2.6 * s, fill=(28, 24, 22))
    for ex in (-16, -6):
        _a, _b = sorted((hx + flip * ex * s - 5 * s, hx + flip * ex * s + 5 * s))
        g.ellipse((_a, hy - 20 * s, _b, hy - 12 * s), fill=col, outline=dark, owidth=1.8 * s)
    # たてがみ
    for k in range(4):
        g.poly([(nx + flip * (14 + k * 7) * s, by - 46 * s + k * 10 * s),
                (nx + flip * (24 + k * 7) * s, by - 38 * s + k * 10 * s),
                (nx + flip * (10 + k * 7) * s, by - 32 * s + k * 10 * s)], fill=dark)
    # 尾
    g.line(qbez((x - flip * (bd + 8) * s, by + 6 * s), (x - flip * (bd + 26) * s, by + 30 * s),
                (x - flip * (bd + 20) * s, by + 66 * s), 10), dark, 8 * s)
    # 鞍 + 铃 (赤い房)
    sx_ = x - flip * 18 * s
    g.chord((sx_ - 30 * s, by - 26 * s, sx_ + 30 * s, by + 18 * s), 180, 360,
            fill=saddle, outline=shade(saddle, 0.7), owidth=2.4 * s)
    g.line([(sx_, by - 10 * s), (sx_ + flip * 6 * s, by + 20 * s)], shade(saddle, 0.75), 4 * s)


def samurai_rider(g, x, y, s, armor=P.LACQUER_RED, bow=True, banner=True, flip=1,
                  seed=0):
    """騎馬武士 (大鎧+弓). s=1 で全高約 330px. y=地面."""
    col, dark = (96, 72, 56), (66, 50, 40)
    # 馬 ( riders は中央やや後ろに乗る )
    by = y - 52 * s * 2.5 + 52 * s  # warhorse の by 計算に合わせた基準
    # 先に馬を描く (内部で再計算)
    bd, bh = 78 * s, 52 * s
    horse_by = y - bh * 2.5
    warhorse(g, x, y, s, col=col, dark=dark, flip=flip)
    # 骑手の基準 (鞍の上)
    rx = x - flip * 18 * s
    ry = horse_by - 14 * s
    # 脚 (鐙に沿って曲げる)
    g.poly([(rx - flip * 4 * s, ry), (rx + flip * 8 * s, ry),
            (rx + flip * 16 * s, ry + 42 * s), (rx - flip * 2 * s, ry + 52 * s)],
           fill=shade(armor, 0.8), outline=P.INK, owidth=2.2 * s)
    # 胴 (大鎧の箱)
    g.rrect((rx - 26 * s, ry - 92 * s, rx + 26 * s, ry + 2 * s), 10 * s,
            fill=armor, outline=P.INK, owidth=2.8 * s)
    for k in range(4):
        yy = ry - 74 * s + k * 20 * s
        g.line([(rx - 24 * s, yy), (rx + 24 * s, yy)], shade(armor, 0.7), 3 * s)
    g.line([(rx, ry - 92 * s), (rx, ry + 2 * s)], shade(armor, 0.62), 3 * s)
    # 肩の袖 (大きな板)
    for sx in (-1, 1):
        g.rrect((rx + sx * 26 * s - 20 * s, ry - 92 * s, rx + sx * 26 * s + 20 * s,
                 ry - 52 * s), 8 * s, fill=shade(armor, 0.9), outline=P.INK, owidth=2.2 * s)
        for k in range(3):
            g.line([(rx + sx * 14 * s, ry - 84 * s + k * 11 * s),
                    (rx + sx * 42 * s, ry - 84 * s + k * 11 * s)], shade(armor, 0.65), 2.4 * s)
    # 母衣 (背後の布)
    if banner:
        g.poly(qbez((rx - flip * 26 * s, ry - 84 * s), (rx - flip * 66 * s, ry - 60 * s),
                    (rx - flip * 52 * s, ry + 6 * s), 10)
               + qbez((rx - flip * 52 * s, ry + 6 * s), (rx - flip * 34 * s, ry + 4 * s),
                      (rx - flip * 24 * s, ry - 30 * s), 10),
               fill=with_alpha(P.SHU, 200))
    # 頭 (兜 + 顔)
    hy = ry - 92 * s - 34 * s
    kabuto(g, rx, hy, 0.62 * s)
    g.ellipse((rx - 16 * s, hy + 2 * s, rx + 16 * s, hy + 30 * s), fill=P.SKIN,
              outline=P.INK, owidth=2.2 * s)
    g.line([(rx - 12 * s, hy + 12 * s), (rx - 4 * s, hy + 12 * s)], P.INK, 2.6 * s)
    g.line([(rx + 4 * s, hy + 12 * s), (rx + 12 * s, hy + 12 * s)], P.INK, 2.6 * s)
    g.line([(rx - 4 * s, hy + 24 * s), (rx + 6 * s, hy + 24 * s)], shade(P.INK, 0.7), 2.2 * s)
    # 弓 (長弓を斜めに構える)
    if bow:
        bx = rx + flip * 34 * s
        g.arc((bx - 26 * s, ry - 130 * s, bx + 30 * s, ry + 30 * s), 60 if flip > 0 else 90,
              300 if flip > 0 else 330, P.WOOD_D, 5 * s)
        tip1 = (bx + 34 * s * math.cos(math.radians(90 + 15)), ry - 130 * s + 60 * s)
        g.line([(bx + flip * 20 * s, ry - 122 * s), (bx - flip * 10 * s, ry - 4 * s)],
               (226, 220, 206), 2 * s)
        g.line([(bx + flip * 8 * s, ry - 64 * s), (bx + flip * 22 * s, ry - 40 * s)],
               (226, 220, 206), 2 * s)


def torii(g, x, y, s, col=P.SHU, w=260):
    """鳥居 (神門). y=地面."""
    w = w * s
    # 柱 (内傾)
    for sx in (-1, 1):
        px = x + sx * w / 2
        g.poly([(px - 12 * s, y), (px + 12 * s, y), (px + 9 * s, y - 210 * s),
                (px - 9 * s, y - 210 * s)], fill=col, outline=shade(col, 0.72), owidth=2.4 * s)
        g.circle(px, y - 4 * s, 14 * s, fill=shade(col, 0.85))
    # 貫
    g.rrect((x - w / 2 - 6 * s, y - 150 * s, x + w / 2 + 6 * s, y - 128 * s), 4 * s,
            fill=col, outline=shade(col, 0.72), owidth=2.2 * s)
    # 笠木 (反った上の梁)
    beam = (qbez((x - w / 2 - 26 * s, y - 186 * s), (x, y - 210 * s),
                 (x + w / 2 + 26 * s, y - 186 * s), 14)
            + [(x + w / 2 + 34 * s, y - 172 * s), (x - w / 2 - 34 * s, y - 172 * s)])
    g.poly(beam, fill=shade(col, 0.88), outline=shade(col, 0.66), owidth=3 * s)
    g.rrect((x - w / 2 - 20 * s, y - 204 * s, x + w / 2 + 20 * s, y - 192 * s), 4 * s,
            fill=(40, 34, 38))


def war_boat(g, x, y, s, onfire=False, banner=True, seed=0):
    """和船 (関船: 盾板+櫂). onfire=True で炎上. y=喫水線."""
    hull, hull_d = P.WOOD, P.WOOD_D
    L = 150 * s
    g.ellipse((x - L * 1.05, y + 5 * s, x + L * 1.05, y + 17 * s),
              fill=with_alpha((30, 48, 70), 80))
    top = ([(x - L, y - 40 * s)]
           + qbez((x - L, y - 40 * s), (x - L * 0.3, y - 24 * s), (x, y - 20 * s), 10)
           + qbez((x, y - 20 * s), (x + L * 0.3, y - 24 * s), (x + L, y - 44 * s), 10))
    bot = ([(x + L * 0.97, y + 2 * s)]
           + qbez((x + L * 0.97, y + 2 * s), (x + L * 0.2, y + 14 * s), (x, y + 15 * s), 10)
           + qbez((x, y + 15 * s), (x - L * 0.2, y + 14 * s), (x - L * 0.97, y + 2 * s), 10))
    g.poly(top + bot, fill=hull, outline=shade(hull_d, 0.8), owidth=2.6 * s)
    # 盾板 (舷の楯並べ)
    shield_n = 8
    for k in range(shield_n):
        sx_ = x - L * 0.82 + (2 * L * 0.82) * k / (shield_n - 1)
        sy_ = y - 24 * s + 6 * s * (1 - abs(k - (shield_n - 1) / 2) / ((shield_n - 1) / 2))
        g.rrect((sx_ - 12 * s, sy_ - 26 * s, sx_ + 12 * s, sy_ + 2 * s), 4 * s,
                fill=(206, 198, 178), outline=shade(hull_d, 0.9), owidth=2 * s)
    # 櫂
    rnd = random.Random(seed)
    for i in range(3):
        px = x - L * 0.6 + i * L * 0.55
        ex = px + math.sin(0.5 + rnd.uniform(-0.1, 0.1)) * 36 * s
        g.line([(px, y - 22 * s), (ex, y + 22 * s)], shade(hull_d, 0.9), 4.4 * s)
    if banner:
        fx = x + L * 0.8
        g.line([(fx, y - 40 * s), (fx, y - 100 * s)], P.WOOD_D, 4.4 * s)
        g.poly([(fx, y - 100 * s), (fx + 40 * s, y - 92 * s), (fx, y - 84 * s)],
               fill=P.SHU, outline=shade(P.SHU, 0.75), owidth=2 * s)
    if onfire:
        campfire(g, x + L * 0.2, y - 30 * s, 0.85 * s, glow=True, stones=False, seed=seed)
        smoke_wisp(g, x + L * 0.24, y - 150 * s, 1.4 * s, color=(60, 56, 60), alpha=190,
                   seed=seed + 1)
        # 焦げ
        g.ellipse((x - 10 * s, y - 34 * s, x + L * 0.5, y - 18 * s),
                  fill=with_alpha((52, 44, 44), 150))


def mongol_ship(g, x, y, s, throwing=True, seed=0):
    """蒙古軍船 (投石器で石弾). s=1 で全長約 420px. y=喫水線."""
    hull, hull_d = (128, 104, 76), (94, 74, 54)
    L = 210 * s
    g.ellipse((x - L * 1.05, y + 6 * s, x + L * 1.05, y + 20 * s),
              fill=with_alpha((30, 48, 70), 80))
    top = ([(x - L, y - 46 * s)]
           + qbez((x - L, y - 46 * s), (x - L * 0.3, y - 28 * s), (x, y - 24 * s), 12)
           + qbez((x, y - 24 * s), (x + L * 0.3, y - 28 * s), (x + L, y - 50 * s), 12))
    bot = ([(x + L * 0.97, y + 2 * s)]
           + qbez((x + L * 0.97, y + 2 * s), (x + L * 0.2, y + 16 * s), (x, y + 17 * s), 12)
           + qbez((x, y + 17 * s), (x - L * 0.2, y + 16 * s), (x - L * 0.97, y + 2 * s), 12))
    g.poly(top + bot, fill=hull, outline=shade(hull_d, 0.8), owidth=2.6 * s)
    g.line(top, shade(hull_d, 0.75), 4 * s)
    for i in range(3):
        g.line([(x - L * 0.7, y - 34 * s + i * 9 * s), (x + L * 0.7, y - 34 * s + i * 9 * s)],
               shade(hull, 0.82), 2.2 * s)
    # マスト+角帆 (蒙古風の暗い帆)
    mx = x - 40 * s
    g.line([(mx, y - 30 * s), (mx, y - 200 * s)], P.WOOD_D, 7 * s)
    sail = (qbez((mx - 70 * s, y - 168 * s), (mx, y - 158 * s), (mx + 70 * s, y - 168 * s), 10)
            + qbez((mx + 70 * s, y - 168 * s), (mx + 84 * s, y - 110 * s),
                   (mx + 64 * s, y - 52 * s), 10)
            + qbez((mx + 64 * s, y - 52 * s), (mx, y - 42 * s), (mx - 64 * s, y - 52 * s), 10)
            + qbez((mx - 64 * s, y - 52 * s), (mx - 84 * s, y - 110 * s),
                   (mx - 70 * s, y - 168 * s), 10))
    g.poly(sail, fill=(176, 158, 124), outline=shade((140, 124, 96), 0.9), owidth=2.4 * s)
    for k in range(1, 4):
        yy = y - 168 * s + k * 30 * s
        g.line([(mx - 58 * s, yy), (mx + 58 * s, yy)], shade((140, 124, 96), 0.85), 2 * s)
    # 兵士 (モンゴル風の三角帽)
    rnd = random.Random(seed)
    for k in range(4):
        sx_ = x - L * 0.6 + k * L * 0.4
        sy_ = y - 40 * s
        g.circle(sx_, sy_ - 44 * s, 9 * s, fill=(72, 58, 50))
        g.poly([(sx_ - 9 * s, sy_ - 46 * s), (sx_ + 9 * s, sy_ - 46 * s), (sx_, sy_ - 62 * s)],
               fill=(58, 46, 42))
        g.poly([(sx_ - 10 * s, sy_ - 36 * s), (sx_ + 10 * s, sy_ - 36 * s),
                (sx_ + 7 * s, sy_ - 4 * s), (sx_ - 7 * s, sy_ - 4 * s)], fill=(84, 66, 56))
    # 投石器と石弾
    if throwing:
        cx_ = x + L * 0.55
        g.line([(cx_, y - 30 * s), (cx_ - 20 * s, y - 120 * s)], P.WOOD_D, 6 * s)
        g.line([(cx_ - 20 * s, y - 120 * s), (cx_ + 44 * s, y - 150 * s)], P.WOOD_D, 5 * s)
        pot = (cx_ + 150 * s, y - 190 * s)
        g.line(qbez((cx_ + 24 * s, y - 150 * s), (cx_ + 90 * s, y - 200 * s),
                    (pot[0], pot[1]), 12), with_alpha((210, 205, 195), 140), 2.2 * s)
        g.circle(pot[0], pot[1], 11 * s, fill=(96, 92, 88), outline=(64, 60, 58), owidth=2.2 * s)
        # 着弾の爆発
        ex, ey = x + L * 0.62, y - 8 * s
        for k in range(7):
            a = math.tau * k / 7
            g.ellipse((ex + math.cos(a) * 26 * s - 8 * s, ey + math.sin(a) * 18 * s - 8 * s,
                       ex + math.cos(a) * 26 * s + 8 * s, ey + math.sin(a) * 18 * s + 8 * s),
                      fill=with_alpha((210, 150, 90), 190))
        g.circle(ex, ey, 16 * s, fill=(226, 176, 110), outline=(180, 120, 70), owidth=2.4 * s)


def zen_temple(g, x, y, s, roof=None, roof_d=None, seed=0):
    """禅寺 (唐様の山門と仏殿+石庭). s=1 で幅約 700px. y=地面."""
    roof = roof or (104, 110, 100)
    roof_d = roof_d or (78, 84, 78)
    wall = P.PLASTER
    frame = P.WOOD_D
    g.ellipse((x - 360 * s, y - 10 * s, x + 360 * s, y + 16 * s),
              fill=with_alpha((60, 60, 52), 60))
    # 石庭 (白砂と石)
    rect(g, x - 330 * s, y - 40 * s, x + 330 * s, y, fill=(232, 230, 220))
    for (rx, ry, rr) in [(-180, -18, 22), (-120, -8, 14), (200, -14, 26), (140, -6, 13)]:
        g.poly(blob_pts(x + rx * s, y + ry * s, rr * s, rr * 0.7 * s, seed=int(rx),
                        wobble=0.12), fill=(150, 148, 142), outline=(116, 114, 108),
               owidth=2.2 * s)
    for k in range(7):
        g.line([(x - 320 * s + k * 100 * s, y - 36 * s), (x - 260 * s + k * 100 * s, y - 4 * s)],
               with_alpha((200, 198, 190), 150), 3 * s)
    # 山門 (2階の唐様門)
    gx = x - 170 * s
    rect(g, gx - 60 * s, y - 90 * s, gx + 60 * s, y - 40 * s, fill=shade(wall, 0.9))
    rect(g, gx - 22 * s, y - 84 * s, gx + 22 * s, y - 40 * s, fill=(64, 54, 50))
    curved_roof(g, gx, y - 90 * s, 86 * s, 46 * s, 34 * s, roof, roof_d, lift=16 * s, s=s)
    rect(g, gx - 44 * s, y - 148 * s, gx + 44 * s, y - 128 * s, fill=shade(wall, 0.92))
    curved_roof(g, gx, y - 148 * s, 62 * s, 34 * s, 26 * s, roof, roof_d, lift=14 * s, s=s)
    # 仏殿 (本堂)
    bx = x + 150 * s
    rect(g, bx - 130 * s, y - 116 * s, bx + 130 * s, y - 44 * s, fill=wall,
         outline=shade(wall, 0.8), owidth=2.4 * s)
    for px in range(-116, 117, 46):
        rect(g, bx + px * s, y - 116 * s, bx + px * s + 11 * s, y - 44 * s, fill=frame)
    rect(g, bx - 26 * s, y - 100 * s, bx + 26 * s, y - 44 * s, fill=(64, 54, 50))
    curved_roof(g, bx, y - 116 * s, 168 * s, 84 * s, 42 * s, roof, roof_d, lift=20 * s, s=s)
def kamakura_goten(g, x, y, s, seed=0):
    """鎌倉の御所 (幕府の館: 塀+門+政庁+旗). s=1 で幅約 720px. y=地面."""
    g.ellipse((x - 380 * s, y - 10 * s, x + 380 * s, y + 16 * s),
              fill=with_alpha((60, 60, 52), 60))
    # 板塀
    wall_top = y - 120 * s
    for px in range(int(-340 * s), int(340 * s), 30):
        if -80 * s <= px <= 80 * s:
            continue
        ph = 96 * s + (abs(px) // 30 % 4) * 8 * s
        rect(g, x + px, wall_top + (120 * s - ph), x + px + 28 * s, y,
             fill=shade(P.WOOD, 1.02), outline=shade(P.WOOD_D, 0.9), owidth=1.8 * s)
    g.line([(x - 340 * s, wall_top + 12 * s), (x + 340 * s, wall_top + 12 * s)],
           shade(P.WOOD_D, 0.85), 5 * s)
    # 門 (楼門)
    gx = x
    rect(g, gx - 56 * s, y - 150 * s, gx + 56 * s, y, fill=shade(P.WOOD_D, 0.95))
    rect(g, gx - 40 * s, y - 136 * s, gx + 40 * s, y - 6 * s, fill=shade((170, 150, 116), 0.9))
    curved_roof(g, gx, y - 150 * s, 84 * s, 52 * s, 34 * s, P.STRAW, P.STRAW_D, s=s)
    # 政庁 (内部の政所)
    by = y - 150 * s
    rect(g, x - 200 * s, by - 150 * s, x + 200 * s, by, fill=(206, 176, 126),
         outline=shade((170, 142, 100), 0.8), owidth=2.6 * s)
    for px in range(-186, 187, 52):
        rect(g, x + px * s, by - 150 * s, x + px * s + 12 * s, by, fill=P.WOOD_D)
    curved_roof(g, x, by - 150 * s, 240 * s, 110 * s, 60 * s, P.STRAW, P.STRAW_D, s=s)
    # 旗 (御所の白旗)
    for fx in (-300, 300):
        banner_pole(g, x + fx * s, y + 2 * s, 0.85, flag=(238, 238, 236))


# ================================================================ ep05 (室町)


def kinkaku(g, x, y, s, gold=None, gold_d=None, roof=(84, 88, 76), seed=0):
    """金閣 (舎利殿: 3層の金楼閣). s=1 で高さ約 380px. y=地面."""
    gold = gold or P.GOLD_LEAF
    gold_d = gold_d or P.GOLD_LEAF_D
    rnd = random.Random(seed)
    # 池に面した石積みの島
    g.ellipse((x - 130 * s, y - 8 * s, x + 130 * s, y + 14 * s),
              fill=with_alpha((60, 60, 52), 60))
    g.rrect((x - 110 * s, y - 44 * s, x + 110 * s, y), 8 * s, fill=(128, 122, 112),
            outline=(96, 92, 84), owidth=3 * s)
    speckle(g, (x - 104 * s, y - 40 * s, x + 104 * s, y - 4 * s), 24,
            [(112, 106, 96), (144, 138, 126)], r=(2, 5), seed=seed)
    y_ = y - 44 * s

    def tier(cy0, bw, bh, rw, rh):
        rect(g, x - bw, cy0 - bh, x + bw, cy0, fill=gold,
             outline=shade(gold_d, 0.85), owidth=2.4 * s)
        # 白壁の窓帯
        rect(g, x - bw * 0.72, cy0 - bh * 0.66, x + bw * 0.72, cy0 - bh * 0.2,
               fill=shade(gold, 1.18))
        for wx in range(int(-bw * 0.6), int(bw * 0.61), 34):
            rect(g, x + wx * s, cy0 - bh * 0.6, x + wx * s + 12 * s, cy0 - bh * 0.26,
                 fill=shade(gold_d, 0.8))
        curved_roof(g, x, cy0 - bh, rw, bw * 0.55, rh, roof, shade(roof, 0.85),
                    lift=10 * s, s=s)

    # 1階 / 2階 / 3階
    tier(y_, 96 * s, 62 * s, 128 * s, 34 * s)
    tier(y_ - 92 * s, 66 * s, 54 * s, 98 * s, 30 * s)
    tier(y_ - 170 * s, 50 * s, 52 * s, 76 * s, 30 * s)
    # 頂の鳳凰
    px, py = x, y_ - 210 * s
    g.ellipse((px - 9 * s, py - 8 * s, px + 9 * s, py + 6 * s), fill=P.GOLD,
              outline=shade(P.GOLD, 0.7), owidth=1.8 * s)
    g.circle(px - 2 * s, py - 10 * s, 5 * s, fill=P.GOLD)
    g.line([(px + 6 * s, py - 2 * s), (px + 26 * s, py - 12 * s)], P.GOLD, 3.4 * s)
    g.line([(px + 6 * s, py), (px + 24 * s, py - 4 * s)], P.GOLD, 3 * s)
    # 金箔の照り
    g.line([(x - 40 * s, y_ - 38 * s), (x - 26 * s, y_ - 6 * s)],
           with_alpha((255, 240, 190), 120), 6 * s)


def ginkaku(g, x, y, s, silver=None, silver_d=None, roof=(96, 100, 94), seed=0):
    """銀閣 (東山文化: ひなびた2層の楼閣). s=1 で高さ約 300px. y=地面."""
    silver = silver or P.SILVER_LEAF
    silver_d = silver_d or P.SILVER_LEAF_D
    g.ellipse((x - 120 * s, y - 8 * s, x + 120 * s, y + 14 * s),
              fill=with_alpha((60, 60, 52), 60))
    g.rrect((x - 100 * s, y - 40 * s, x + 100 * s, y), 8 * s, fill=(118, 122, 116),
            outline=(90, 94, 88), owidth=3 * s)
    y_ = y - 40 * s

    def tier(cy0, bw, bh, rw, rh):
        rect(g, x - bw, cy0 - bh, x + bw, cy0, fill=silver,
             outline=shade(silver_d, 0.9), owidth=2.4 * s)
        rect(g, x - bw * 0.7, cy0 - bh * 0.62, x + bw * 0.7, cy0 - bh * 0.22,
               fill=shade(silver, 1.12))
        for wx in range(int(-bw * 0.55), int(bw * 0.56), 30):
            rect(g, x + wx * s, cy0 - bh * 0.56, x + wx * s + 11 * s, cy0 - bh * 0.28,
                 fill=(72, 70, 66))
        curved_roof(g, x, cy0 - bh, rw, bw * 0.55, rh, roof, shade(roof, 0.85),
                    lift=10 * s, s=s)
        # 苔むらい
        speckle(g, (x - rw * 0.6, cy0 - bh - rh, x + rw * 0.6, cy0 - bh), 8,
                [(110, 124, 104)], r=(2, 4), seed=seed + int(bw))

    tier(y_, 80 * s, 60 * s, 108 * s, 32 * s)
    tier(y_ - 88 * s, 56 * s, 52 * s, 84 * s, 30 * s)
    # 頂の擬宝珠 (銀)
    g.circle(x, y_ - 176 * s, 7 * s, fill=P.SILVER_LEAF, outline=shade(P.SILVER_LEAF_D, 0.8),
             owidth=2 * s)


def nobori(g, x, y, s, col=P.SHU, mark=(240, 236, 228), seed=0):
    """旗指物 (縦長の旗). y=地面."""
    g.line([(x, y), (x, y - 210 * s)], P.WOOD_D, 6 * s)
    g.rrect((x - 15 * s, y - 206 * s, x + 15 * s, y - 30 * s), 4 * s, fill=col,
            outline=shade(col, 0.72), owidth=2.2 * s)
    rect(g, x - 15 * s, y - 176 * s, x + 15 * s, y - 160 * s, fill=mark)
    g.circle(x, y - 88 * s, 9 * s, outline=mark, owidth=3 * s)
    g.line([(x - 15 * s, y - 44 * s), (x + 15 * s, y - 44 * s)], mark, 4 * s)


def mountain_fort(g, x, y, s, seed=0, flag=P.SHU):
    """山城 (上赤坂城風: 山頂の柵と櫓). s=1 で幅約 620px. y=麓の地面."""
    rnd = random.Random(seed)
    # 山体
    g.poly(blob_pts(x, y - 120 * s, 320 * s, 130 * s, seed=seed, wobble=0.16),
           fill=(128, 148, 100), outline=(104, 122, 82), owidth=3 * s)
    # 2重の柵 (尾根に沿う)
    palisade(g, x - 240 * s, x + 240 * s, y - 150 * s, 0.72, col=(92, 66, 48),
             dark=(66, 46, 36), seed=seed)
    palisade(g, x - 150 * s, x + 150 * s, y - 220 * s, 0.6, col=(92, 66, 48),
             dark=(66, 46, 36), seed=seed + 1)
    # 物見櫓
    wx = x
    rect(g, wx - 42 * s, y - 320 * s, wx + 42 * s, y - 252 * s, fill=P.WOOD_D)
    for px in (-34, 0, 34):
        rect(g, wx + px * s - 5 * s, y - 320 * s, wx + px * s + 5 * s, y - 252 * s,
             fill=shade(P.WOOD_D, 0.85))
    g.poly([(wx - 60 * s, y - 326 * s), (wx + 60 * s, y - 326 * s), (wx, y - 372 * s)],
           fill=shade(P.WOOD, 1.1), outline=P.WOOD_D, owidth=3 * s)
    nobori(g, wx - 90 * s, y - 258 * s, 0.62, col=flag, seed=seed)
    nobori(g, wx + 90 * s, y - 258 * s, 0.62, col=(238, 238, 236), seed=seed + 1)
    # 麓の門
    rect(g, x - 44 * s, y - 96 * s, x + 44 * s, y - 20 * s, fill=shade(P.WOOD_D, 0.92))
    g.line([(x - 44 * s, y - 96 * s), (x + 44 * s, y - 96 * s)], shade(P.WOOD_D, 0.7), 5 * s)


def two_court_flags(g, x, y, s, col_north=(216, 178, 96), col_south=(150, 108, 178)):
    """南北朝の二つの朝廷旗 (金=北朝 / 紫=南朝). y=地面."""
    for (fx, col, h) in [(-120, col_north, 200), (120, col_south, 200)]:
        fx = x + fx * s
        g.line([(fx, y), (fx, y - h * s)], P.WOOD_D, 7 * s)
        g.poly([(fx, y - h * s), (fx + 64 * s, y - h * s + 12 * s),
                (fx, y - h * s + 64 * s)], fill=col, outline=shade(col, 0.72), owidth=2.4 * s)
        g.circle(fx + 22 * s, y - h * s + 30 * s, 10 * s, fill=with_alpha((240, 240, 234), 220))
    # 間に小さな山
    g.poly(blob_pts(x, y - 20 * s, 90 * s, 42 * s, seed=7, wobble=0.14),
           fill=(130, 148, 104))


def kango_ship(g, x, y, s, seed=0):
    """勘合船 (日明貿易の大型ジャンク船). s=1 で全長約 480px. y=喫水線."""
    hull, hull_d = (140, 106, 72), (104, 78, 54)
    L = 240 * s
    g.ellipse((x - L * 1.05, y + 6 * s, x + L * 1.05, y + 20 * s),
              fill=with_alpha((30, 48, 70), 80))
    top = ([(x - L, y - 48 * s)]
           + qbez((x - L, y - 48 * s), (x - L * 0.3, y - 28 * s), (x, y - 24 * s), 12)
           + qbez((x, y - 24 * s), (x + L * 0.3, y - 28 * s), (x + L, y - 52 * s), 12))
    bot = ([(x + L * 0.97, y + 2 * s)]
           + qbez((x + L * 0.97, y + 2 * s), (x + L * 0.2, y + 16 * s), (x, y + 17 * s), 12)
           + qbez((x, y + 17 * s), (x - L * 0.2, y + 16 * s), (x - L * 0.97, y + 2 * s), 12))
    g.poly(top + bot, fill=hull, outline=shade(hull_d, 0.8), owidth=2.6 * s)
    g.line(top, shade(hull_d, 0.75), 4 * s)
    # 高い船尾楼
    g.rrect((x + L * 0.55, y - 108 * s, x + L * 0.92, y - 40 * s), 8 * s,
            fill=shade(hull, 1.12), outline=shade(hull_d, 0.8), owidth=2.4 * s)
    g.rrect((x + L * 0.58, y - 100 * s, x + L * 0.89, y - 56 * s), 6 * s,
            fill=with_alpha((70, 56, 48), 220))
    # 3本のマスト+硬帆
    for (mx, mh, sw) in [(-L * 0.55, 170 * s, 78 * s), (0, 200 * s, 96 * s),
                         (L * 0.45, 150 * s, 66 * s)]:
        mx = x + mx
        g.line([(mx, y - 26 * s), (mx, y - 26 * s - mh)], P.WOOD_D, 7 * s)
        sail = (qbez((mx - sw, y - 40 * s - mh + 24 * s), (mx, y - 34 * s - mh + 24 * s),
                     (mx + sw, y - 40 * s - mh + 24 * s), 10)
                + qbez((mx + sw, y - 40 * s - mh + 24 * s),
                       (mx + sw * 1.05, y - 40 * s - mh / 2),
                       (mx + sw * 0.9, y - 30 * s), 10)
                + qbez((mx + sw * 0.9, y - 30 * s), (mx, y - 22 * s),
                       (mx - sw * 0.9, y - 30 * s), 10)
                + qbez((mx - sw * 0.9, y - 30 * s), (mx - sw * 1.05, y - 40 * s - mh / 2),
                       (mx - sw, y - 40 * s - mh + 24 * s), 10))
        g.poly(sail, fill=(198, 182, 148), outline=shade((150, 136, 106), 0.9), owidth=2.4 * s)
        for k in range(1, 5):
            yy = y - 40 * s - mh + 24 * s + (mh - 36 * s) * k / 5
            g.line([(mx - sw * 0.82, yy), (mx + sw * 0.82, yy - 2 * s)],
                   shade((150, 136, 106), 0.85), 2.2 * s)
    # 勘合旗
    fx = x + L * 0.86
    g.line([(fx, y - 108 * s), (fx, y - 190 * s)], P.WOOD_D, 4.4 * s)
    g.rrect((fx, y - 190 * s, fx + 54 * s, y - 128 * s), 4 * s,
            fill=P.YAMABUKI, outline=shade(P.YAMABUKI, 0.72), owidth=2.2 * s)
    g.circle(fx + 27 * s, y - 158 * s, 12 * s, outline=(150, 110, 60), owidth=3.4 * s)


# ================================================================ ep06 (織豊)


def tenshu(g, x, y, s, tiers=5, wall=P.SHIRO_WALL, roof=P.TENSHU_ROOF,
           stone=P.ISHIGAKI, gold_top=True, seed=0):
    """天守 (石垣+白壁の重層天守). s=1 で高さ約 620px. y=地面."""
    rnd = random.Random(seed)
    # 石垣 (扇の勾配)
    g.ellipse((x - 320 * s, y - 10 * s, x + 320 * s, y + 16 * s),
              fill=with_alpha((60, 60, 52), 60))
    sw = 250 * s
    sh = 110 * s
    for k in range(6):
        yy0 = y - sh * (k + 1) / 6
        yy1 = y - sh * k / 6
        w_ = sw * (1 - k * 0.09)
        rect(g, x - w_, yy0, x + w_, yy1, fill=shade(stone, 1 - k * 0.05),
             outline=shade(stone, 0.72), owidth=2 * s)
        for _ in range(8):
            bxp = x + rnd.uniform(-w_ * 0.9, w_ * 0.9)
            byp = rnd.uniform(yy0 + 4, yy1 - 4)
            g.rrect((bxp, byp, bxp + rnd.uniform(10, 22) * s, byp + rnd.uniform(5, 9) * s),
                    2 * s, fill=shade(stone, rnd.uniform(0.8, 1.15)))
    # 天守本体
    ye = y - sh
    bw = 130 * s
    body_h = 54 * s
    roof_h = 26 * s
    for i in range(tiers):
        rect(g, x - bw, ye - body_h, x + bw, ye, fill=wall,
             outline=shade(wall, 0.78), owidth=2.2 * s)
        for px in (-bw + 8 * s, bw - 20 * s):
            rect(g, x + px, ye - body_h, x + px + 9 * s, ye, fill=shade(roof, 0.95))
        # 出窓/扉
        if i == 0:
            g.rrect((x - 20 * s, ye - body_h + 12 * s, x + 20 * s, ye - 4 * s), 6 * s,
                    fill=(64, 58, 54))
        else:
            for wx in (-bw * 0.5, 0, bw * 0.5):
                g.rrect((x + wx * s - 7 * s, ye - body_h * 0.72, x + wx * s + 7 * s,
                         ye - body_h * 0.28), 3 * s, fill=(58, 62, 70))
        ye -= body_h
        curved_roof(g, x, ye, bw + 46 * s - i * 10 * s, bw * 0.6,
                    roof_h, roof, shade(roof, 0.82), lift=8 * s, s=s)
        ye -= roof_h + 6 * s
        bw -= 16 * s
    # 最上階の金の装飾
    if gold_top:
        g.rrect((x - 40 * s, ye - 12 * s, x + 40 * s, ye), 4 * s, fill=P.GOLD_LEAF,
                outline=shade(P.GOLD_LEAF, 0.7), owidth=2 * s)


def azuchi_castle(g, x, y, s, seed=0):
    """安土城 (琵琶湖畔の丘の上の天主). s=1 で全高約 780px. y=地面 (湖畔)."""
    # 山の丘
    g.poly(blob_pts(x, y - 90 * s, 360 * s, 120 * s, seed=seed, wobble=0.14),
           fill=(118, 146, 100), outline=(96, 122, 82), owidth=3 * s)
    tenshu(g, x, y - 120 * s, s, tiers=5, seed=seed)
    # のぼり旗
    nobori(g, x - 210 * s, y - 60 * s, 0.6, col=(238, 238, 236), seed=seed + 1)
    nobori(g, x + 210 * s, y - 58 * s, 0.6, col=P.SHU, seed=seed + 2)


def osaka_castle(g, x, y, s, seed=0):
    """大坂城 (巨大な石垣と白亜の天守). s=1 で全高約 800px. y=地面."""
    g.ellipse((x - 380 * s, y - 10 * s, x + 380 * s, y + 16 * s),
              fill=with_alpha((60, 60, 52), 60))
    # 巨大な石垣 (2段)
    rect(g, x - 340 * s, y - 96 * s, x + 340 * s, y, fill=shade(P.ISHIGAKI, 0.9),
         outline=shade(P.ISHIGAKI, 0.7), owidth=3 * s)
    for k in range(7):
        yy = y - 96 * s + k * 14 * s
        g.line([(x - 340 * s, yy), (x + 340 * s, yy)], shade(P.ISHIGAKI, 0.78), 3 * s)
    rect(g, x - 250 * s, y - 176 * s, x + 250 * s, y - 96 * s,
         fill=shade(P.ISHIGAKI, 1.05), outline=shade(P.ISHIGAKI, 0.72), owidth=3 * s)
    for k in range(5):
        yy = y - 176 * s + k * 16 * s
        g.line([(x - 250 * s, yy), (x + 250 * s, yy)], shade(P.ISHIGAKI, 0.76), 3 * s)
    tenshu(g, x, y - 176 * s, s * 1.02, tiers=5, gold_top=False, seed=seed)
    # 鯱 (金色のシャチホコ)
    for sx in (-1, 1):
        px = x + sx * 46 * s
        g.poly(qbez((px, y - 176 * s - 250 * s * 1.02), (px + sx * 16 * s, y - 176 * s - 262 * s * 1.02),
                    (px + sx * 26 * s, y - 176 * s - 248 * s * 1.02), 8),
               fill=P.GOLD_LEAF, outline=shade(P.GOLD_LEAF, 0.7), owidth=2.2 * s)


def bakeblock_fence(g, x0, x1, y, s, col=(140, 106, 74)):
    """馬防柵 (長篠の三重柵). y=地面."""
    h = 92 * s
    step = 26 * s
    px = x0
    while px <= x1:
        g.poly([(px, y), (px + 10 * s, y), (px + 10 * s, y - h - 8 * s),
                (px, y - h - 8 * s)], fill=col, outline=shade(col, 0.72), owidth=1.8 * s)
        px += step
    g.line([(x0, y - h), (x1, y - h)], shade(col, 0.66), 8 * s)
    g.line([(x0, y - h + 18 * s), (x1, y - h + 18 * s)], shade(col, 0.75), 5 * s)


def arquebusier(g, x, y, s, firing=False, seed=0):
    """鉄砲隊 (膝立ちの火縄銃兵). y=地面."""
    # 陣笠
    g.pieslice((x - 22 * s, y - 96 * s, x + 22 * s, y - 58 * s), 180, 360,
               fill=(90, 84, 66), outline=(64, 60, 48), owidth=2.2 * s)
    # 顔
    g.ellipse((x - 13 * s, y - 62 * s, x + 13 * s, y - 40 * s), fill=P.SKIN,
              outline=P.OUTLINE, owidth=2 * s)
    g.line([(x - 8 * s, y - 54 * s), (x - 3 * s, y - 54 * s)], P.OUTLINE, 2.2 * s)
    g.line([(x + 3 * s, y - 54 * s), (x + 8 * s, y - 54 * s)], P.OUTLINE, 2.2 * s)
    # 胴 (足軽の袴)
    g.rrect((x - 20 * s, y - 44 * s, x + 20 * s, y - 8 * s), 8 * s,
            fill=(108, 92, 70), outline=shade((108, 92, 70), 0.7), owidth=2.2 * s)
    # 膝立ちの脚
    g.rrect((x - 18 * s, y - 12 * s, x + 4 * s, y), 4 * s, fill=(84, 70, 56))
    g.rrect((x + 2 * s, y - 20 * s, x + 22 * s, y - 2 * s), 4 * s, fill=(84, 70, 56))
    # 火縄銃 (長い筒を三脚で構える)
    gx, gy = x + 26 * s, y - 52 * s
    g.line([(gx, gy), (gx + 42 * s, y - 8 * s)], (64, 60, 58), 6 * s)
    g.line([(gx + 6 * s, gy + 6 * s), (gx + 30 * s, y - 4 * s)], P.WOOD_D, 4 * s)
    g.line([(x + 2 * s, y - 30 * s), (gx, gy)], (108, 92, 70), 4 * s)
    if firing:
        for k in range(5):
            a = math.tau * k / 5
            g.ellipse((gx - 6 * s + math.cos(a) * 14 * s, gy - 10 * s + math.sin(a) * 10 * s,
                       gx + 10 * s + math.cos(a) * 14 * s, gy + 2 * s + math.sin(a) * 10 * s),
                      fill=with_alpha((226, 190, 130), 200))
        g.circle(gx - 2 * s, gy - 4 * s, 12 * s, fill=(240, 208, 150),
                 outline=(190, 140, 90), owidth=2.4 * s)


def atakebune(g, x, y, s, flag=P.SHU, seed=0):
    """安宅船 (鉄板を張った巨船). s=1 で全長約 380px. y=喫水線."""
    hull, hull_d = (110, 84, 60), (80, 60, 44)
    L = 190 * s
    g.ellipse((x - L * 1.06, y + 6 * s, x + L * 1.06, y + 18 * s),
              fill=with_alpha((30, 48, 70), 80))
    top = ([(x - L, y - 56 * s)]
           + qbez((x - L, y - 56 * s), (x - L * 0.3, y - 34 * s), (x, y - 30 * s), 10)
           + qbez((x, y - 30 * s), (x + L * 0.3, y - 34 * s), (x + L, y - 60 * s), 10))
    bot = ([(x + L * 0.97, y + 2 * s)]
           + qbez((x + L * 0.97, y + 2 * s), (x + L * 0.2, y + 16 * s), (x, y + 17 * s), 10)
           + qbez((x, y + 17 * s), (x - L * 0.2, y + 16 * s), (x - L * 0.97, y + 2 * s), 10))
    g.poly(top + bot, fill=hull, outline=shade(hull_d, 0.8), owidth=2.6 * s)
    # 鉄板の装甲帯
    for k in range(4):
        yy = y - 50 * s + k * 9 * s
        g.line([(x - L * 0.8, yy), (x + L * 0.8, yy)], shade(hull_d, 0.7), 4 * s)
    # 盾板+射出口
    for k in range(6):
        sx_ = x - L * 0.75 + (2 * L * 0.75) * k / 5
        g.rrect((sx_ - 14 * s, y - 62 * s, sx_ + 14 * s, y - 30 * s), 4 * s,
                fill=(196, 188, 168), outline=shade(hull_d, 0.9), owidth=2.2 * s)
    # 櫓と帆
    mx = x
    g.line([(mx, y - 30 * s), (mx, y - 150 * s)], P.WOOD_D, 7 * s)
    sail = (qbez((mx - 60 * s, y - 140 * s), (mx, y - 132 * s), (mx + 60 * s, y - 140 * s), 10)
            + qbez((mx + 60 * s, y - 140 * s), (mx + 66 * s, y - 100 * s),
                   (mx + 54 * s, y - 60 * s), 10)
            + qbez((mx + 54 * s, y - 60 * s), (mx, y - 52 * s), (mx - 54 * s, y - 60 * s), 10)
            + qbez((mx - 54 * s, y - 60 * s), (mx - 66 * s, y - 100 * s),
                   (mx - 60 * s, y - 140 * s), 10))
    g.poly(sail, fill=(200, 184, 150), outline=shade((152, 138, 108), 0.9), owidth=2.4 * s)
    # 幟と兜飾り
    for fx in (-L * 0.7, L * 0.7):
        fx = x + fx
        g.line([(fx, y - 56 * s), (fx, y - 120 * s)], P.WOOD_D, 4.4 * s)
        g.rrect((fx - 10 * s, y - 118 * s, fx + 10 * s, y - 66 * s), 3 * s,
                fill=flag, outline=shade(flag, 0.72), owidth=2 * s)


def gold_screen(g, x, y, s, seed=0):
    """金屏風 (桃山絵画の4曲一双). (x,y)=屏風の中心."""
    panel_w, panel_h = 110 * s, 190 * s
    n = 4
    total_w = panel_w * n
    x0 = x - total_w / 2
    # 脚
    for lx in (x0 + 20 * s, x + total_w / 2 - 20 * s):
        g.poly([(lx - 8 * s, y + panel_h / 2), (lx + 8 * s, y + panel_h / 2),
                (lx + 14 * s, y + panel_h / 2 + 26 * s), (lx + 2 * s, y + panel_h / 2 + 26 * s)],
               fill=(64, 52, 44))
    # パネル (金箔 + 金雲 + 松)
    for k in range(n):
        px0 = x0 + k * panel_w
        g.rrect((px0 + 2 * s, y - panel_h / 2, px0 + panel_w - 2 * s, y + panel_h / 2),
                3 * s, fill=P.GOLD_LEAF, outline=shade(P.GOLD_LEAF, 0.72), owidth=2.4 * s)
        # 金雲 (たなびく雲の帯)
        cy_ = y - panel_h / 2 + 40 * s + (k % 2) * 30 * s
        g.poly(blob_pts(px0 + panel_w / 2, cy_, panel_w * 0.6, 26 * s,
                        seed=seed + k, wobble=0.2),
               fill=with_alpha((244, 214, 150), 200))
        g.line([(px0 + 6 * s, cy_ + 16 * s), (px0 + panel_w - 6 * s, cy_ + 16 * s)],
               with_alpha((196, 152, 84), 180), 2.4 * s)
        # 松の枝 (k=0,2) / 桐の花 (k=1,3)
        if k % 2 == 0:
            bx = px0 + panel_w * 0.3
            g.line(qbez((bx, y + panel_h / 2 - 20 * s), (bx + 20 * s, y + 10 * s),
                        (bx + 56 * s, y - 30 * s), 10), (90, 68, 52), 4.4 * s)
            for nk in range(5):
                nx = bx + 14 * s + nk * 12 * s
                ny = y + 4 * s - nk * 12 * s
                g.circle(nx, ny, 7 * s, fill=(88, 116, 96))
                g.circle(nx, ny, 3 * s, fill=(72, 98, 80))
        else:
            bx = px0 + panel_w * 0.5
            for nk in range(3):
                g.line([(bx, y + panel_h / 2 - 16 * s),
                        (bx + (nk - 1) * 16 * s, y + panel_h / 2 - 52 * s)],
                       (84, 66, 54), 3.6 * s)
                g.circle(bx + (nk - 1) * 16 * s, y + panel_h / 2 - 56 * s, 5 * s,
                         fill=(196, 130, 176))
    # 枠
    g.rrect((x0, y - panel_h / 2, x0 + total_w, y + panel_h / 2), 4 * s,
            outline=(64, 52, 44), owidth=3.4 * s)


def kenchi_stakes(g, box, n=6, seed=0, s=1.0):
    """検地の打ち杭 (水帳の札つき). box=(x0,y0,x1,y1)."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(n):
        px = rnd.uniform(x0, x1)
        py = rnd.uniform(y0, y1)
        g.line([(px, py), (px, py - 26 * s)], (110, 84, 60), 4 * s)
        g.rrect((px + 2 * s, py - 30 * s, px + 20 * s, py - 12 * s), 2 * s,
                fill=(238, 232, 214), outline=(180, 172, 152), owidth=1.8 * s)
        g.line([(px + 5 * s, py - 24 * s), (px + 16 * s, py - 24 * s)],
               with_alpha((140, 130, 110), 190), 1.8 * s)


# ================================================================ ep07 (江戸前半)


def fuji(g, x, y, s, col=(110, 128, 150), snow=(240, 244, 248)):
    """富士山 (雪の冠). s=1 で高さ約 300px. y=麓."""
    peak = y - 300 * s
    g.poly([(x - 210 * s, y), (x - 86 * s, peak + 4 * s), (x + 86 * s, peak + 4 * s),
            (x + 210 * s, y)], fill=col)
    # 雪冠 (坂の角度に合わせたギザギザ)
    cap = [(x - 86 * s, peak + 4 * s)]
    for k in range(9):
        px = x - 86 * s + 172 * s * (k + 1) / 9
        py = peak + 4 * s + 62 * s * (k + 1) / 9
        cap.append((px, py + (8 * s if k % 2 == 0 else 0)))
    cap.append((x + 86 * s, peak + 4 * s))
    g.poly(cap, fill=snow)


def edo_castle(g, x, y, s, seed=0):
    """江戸城 (大奥を擁する幕府の城). s=1 で全高約 760px. y=地面."""
    g.ellipse((x - 400 * s, y - 10 * s, x + 400 * s, y + 16 * s),
              fill=with_alpha((60, 60, 52), 60))
    # 内堀と石垣
    g.rrect((x - 380 * s, y - 110 * s, x + 380 * s, y), 10 * s, fill=shade(P.ISHIGAKI, 0.92),
            outline=shade(P.ISHIGAKI, 0.7), owidth=3 * s)
    for k in range(6):
        yy = y - 110 * s + k * 18 * s
        g.line([(x - 380 * s, yy), (x + 380 * s, yy)], shade(P.ISHIGAKI, 0.76), 3.4 * s)
    # 桜田門っぽい門
    rect(g, x - 60 * s, y - 96 * s, x + 60 * s, y, fill=shade(P.WOOD_D, 0.95))
    g.rrect((x - 42 * s, y - 82 * s, x + 42 * s, y - 8 * s), 6 * s, fill=(70, 58, 52))
    curved_roof(g, x, y - 96 * s, 92 * s, 56 * s, 34 * s, P.TILE, shade(P.TILE, 0.85), s=s)
    tenshu(g, x, y - 110 * s, s * 0.95, tiers=5, gold_top=False, seed=seed)
    # 鯱
    for sx in (-1, 1):
        px = x + sx * 44 * s * 0.95
        py = y - 110 * s - 268 * s * 0.95
        g.poly(qbez((px, py), (px + sx * 14 * s, py - 14 * s), (px + sx * 24 * s, py - 2 * s), 8),
               fill=P.GOLD_LEAF, outline=shade(P.GOLD_LEAF, 0.7), owidth=2.2 * s)


def daimyo_procession(g, x, y, s, seed=0, banner=P.SHU):
    """参勤交代の大名行列 (輿+槍持ち+荷物+武者). s=1 で全長約 900px. y=地面."""
    rnd = random.Random(seed)
    # 先導 (槍持ち×2)
    for i, sx_ in enumerate((-420, -350)):
        px = x + sx_ * s
        g.line([(px, y - 4 * s), (px, y - 150 * s)], P.WOOD_D, 5 * s)
        g.poly([(px - 6 * s, y - 150 * s), (px + 6 * s, y - 150 * s), (px, y - 176 * s)],
               fill=(200, 198, 192))
        g.circle(px, y - 60 * s, 10 * s, fill=(84, 68, 60))
        g.poly([(px - 12 * s, y - 52 * s), (px + 12 * s, y - 52 * s),
                (px + 8 * s, y - 10 * s), (px - 8 * s, y - 10 * s)], fill=(96, 82, 72))
    # 荷物持ち ×2
    for sx_ in (-270, -200):
        px = x + sx_ * s
        g.circle(px, y - 66 * s, 10 * s, fill=(90, 74, 66))
        g.poly([(px - 13 * s, y - 58 * s), (px + 13 * s, y - 58 * s),
                (px + 9 * s, y - 12 * s), (px - 9 * s, y - 12 * s)], fill=(102, 88, 78))
        g.rrect((px - 22 * s, y - 84 * s, px + 22 * s, y - 58 * s), 5 * s,
                fill=(186, 158, 116), outline=shade((150, 126, 92), 0.8), owidth=2.2 * s)
        g.line([(px - 20 * s, y - 60 * s), (px + 20 * s, y - 60 * s)],
               shade((150, 126, 92), 0.8), 3 * s)
    # 大名の輿 (中央)
    kx = x - 20 * s
    g.rrect((kx - 60 * s, y - 150 * s, kx + 60 * s, y - 66 * s), 10 * s,
            fill=(150, 60, 52), outline=shade((150, 60, 52), 0.72), owidth=2.6 * s)
    rect(g, kx - 40 * s, y - 138 * s, kx + 40 * s, y - 96 * s, fill=(96, 78, 66))
    # 輿の屋根
    g.poly([(kx - 70 * s, y - 150 * s), (kx + 70 * s, y - 150 * s),
            (kx + 52 * s, y - 196 * s), (kx - 52 * s, y - 196 * s)],
           fill=P.WOOD_D, outline=shade(P.WOOD_D, 0.72), owidth=2.6 * s)
    # 担ぎ棒と担ぎ手 ×4
    for px in (-86, -46, 46, 86):
        px = kx + px * s
        g.circle(px, y - 58 * s, 10 * s, fill=(84, 68, 60))
        g.poly([(px - 12 * s, y - 50 * s), (px + 12 * s, y - 50 * s),
                (px + 8 * s, y - 8 * s), (px - 8 * s, y - 8 * s)], fill=(96, 82, 72))
        g.line([(px - 14 * s, y - 68 * s), (px + 14 * s, y - 68 * s)], P.WOOD_D, 5 * s)
    g.line([(kx - 96 * s, y - 68 * s), (kx + 96 * s, y - 68 * s)], P.WOOD_D, 7 * s)
    # 後ろの武者と槍荷
    for i in range(4):
        px = x + (90 + i * 76) * s
        g.circle(px, y - 70 * s, 11 * s, fill=(84, 68, 60))
        g.poly([(px - 14 * s, y - 60 * s), (px + 14 * s, y - 60 * s),
                (px + 10 * s, y - 12 * s), (px - 10 * s, y - 12 * s)], fill=(88, 76, 68))
        g.line([(px, y - 6 * s), (px, y - 168 * s)], P.WOOD_D, 4.6 * s)
        g.poly([(px - 6 * s, y - 168 * s), (px + 6 * s, y - 168 * s), (px, y - 192 * s)],
               fill=(200, 198, 192))
    # 家紋入りの幟
    nobori(g, x + 380 * s, y - 4 * s, 0.72, col=banner, seed=seed)


def cross_flag(g, x, y, s, col=(238, 236, 228)):
    """キリシタンの白旗 (十字の幟). y=地面."""
    g.line([(x, y), (x, y - 200 * s)], P.WOOD_D, 5 * s)
    g.rrect((x - 16 * s, y - 196 * s, x + 16 * s, y - 34 * s), 3 * s, fill=col,
            outline=shade(col, 0.85), owidth=2.2 * s)
    g.line([(x - 8 * s, y - 150 * s), (x + 8 * s, y - 150 * s)], (150, 70, 60), 6 * s)
    g.line([(x, y - 166 * s), (x, y - 134 * s)], (150, 70, 60), 6 * s)


def hara_castle(g, x, y, s, seed=0):
    """原城跡 (南島原の柵の砦・一揆の旗). s=1 で幅約 680px. y=地面."""
    rnd = random.Random(seed)
    # 半島の台地
    g.poly([(x - 340 * s, y), (x - 300 * s, y - 130 * s), (x + 300 * s, y - 130 * s),
            (x + 340 * s, y)], fill=(136, 128, 112), outline=(108, 100, 88), owidth=3 * s)
    # 穴を掘った柵の砦 (壊れかけ)
    palisade(g, x - 260 * s, x + 260 * s, y - 130 * s, 0.72, col=(104, 88, 76),
             dark=(78, 66, 58), seed=seed)
    for px in range(int(-240 * s), int(240 * s), 90):
        if rnd.random() < 0.4:
            g.poly([(x + px, y - 130 * s + 8 * s), (x + px + 26 * s, y - 130 * s + 8 * s),
                    (x + px + 18 * s, y - 96 * s), (x + px + 6 * s, y - 96 * s)],
                   fill=(120, 104, 90), outline=(94, 80, 70), owidth=2 * s)
    # 一揆の旗 (十字の白旗×2)
    cross_flag(g, x - 150 * s, y - 126 * s, 0.72)
    cross_flag(g, x + 150 * s, y - 126 * s, 0.72)


def sakoku_door(g, cx, cy, s, door=(104, 74, 54), frame=(64, 52, 44)):
    """鎖国の扉モチーフ (閉じていく二枚の扉). (cx,cy)=扉の中心."""
    w, h = 150 * s, 210 * s
    g.rrect((cx - w - 10 * s, cy - h / 2 - 10 * s, cx + w + 10 * s, cy + h / 2 + 10 * s),
            8 * s, fill=frame, outline=shade(frame, 0.7), owidth=3 * s)
    # 背後の光 (海と世界)
    rect(g, cx - w + 6 * s, cy - h / 2 + 6 * s, cx + w - 6 * s, cy + h / 2 - 6 * s,
           fill=(140, 176, 196))
    for k in range(3):
        g.arc((cx - 120 * s, cy - 40 * s + k * 30 * s, cx + 120 * s, cy + 0 * s + k * 30 * s),
              200, 340, with_alpha((230, 240, 246), 130), 3 * s)
    # 二枚の扉 (中央で閉じる・蝶番)
    for sx in (-1, 1):
        px0 = cx + (0 if sx < 0 else 4 * s)
        px1 = cx + sx * w * (0.86 if sx < 0 else 0.14 + 0.72)
        pts = [(cx, cy - h / 2 + 8 * s), (cx + sx * w * 0.86, cy - h / 2 + 8 * s),
               (cx + sx * w * 0.86, cy + h / 2 - 8 * s), (cx, cy + h / 2 - 8 * s)]
        if sx > 0:
            pts = [(cx + 4 * s, cy - h / 2 + 8 * s), (cx + w * 0.86, cy - h / 2 + 8 * s),
                   (cx + w * 0.86, cy + h / 2 - 8 * s), (cx + 4 * s, cy + h / 2 - 8 * s)]
        else:
            pts = [(cx - 4 * s, cy - h / 2 + 8 * s), (cx - w * 0.86, cy - h / 2 + 8 * s),
                   (cx - w * 0.86, cy + h / 2 - 8 * s), (cx - 4 * s, cy + h / 2 - 8 * s)]
        g.poly(pts, fill=door, outline=shade(door, 0.7), owidth=2.6 * s)
        # 飾り金具
        g.line([(cx + sx * w * 0.43, cy - h / 2 + 12 * s),
                (cx + sx * w * 0.43, cy + h / 2 - 12 * s)], shade(door, 0.6), 5 * s)
        g.circle(cx + sx * w * 0.2, cy, 8 * s, fill=(150, 118, 78))


def fan_dejima(g, x, y, s, seed=0):
    """扇形の出島 (湾内の扇型人工島+オランダ商館). s=1 で幅約 520px. y=水面."""
    # 扇形の島 (扇の要は内陸側)
    hx, hy = x - 190 * s, y
    r0, r1 = 90 * s, 470 * s
    a0, a1 = -0.62, 0.62
    pts = []
    for k in range(13):
        a = a0 + (a1 - a0) * k / 12
        pts.append((hx + r1 * math.cos(a), hy + r1 * math.sin(a)))
    for k in range(12, -1, -1):
        a = a0 + (a1 - a0) * k / 12
        pts.append((hx + r0 * math.cos(a), hy + r0 * math.sin(a)))
    g.poly(pts, fill=(204, 196, 178), outline=(168, 160, 142), owidth=3 * s)
    speckle(g, (hx + r0 * 0.4, hy - 90 * s, hx + r1 * 0.7, hy + 90 * s), 26,
            [(188, 180, 162), (216, 210, 194)], r=(2, 5), seed=seed)
    # オランダ商館 (階段状の切妻屋根の洋館)
    bx = hx + r1 * 0.55
    g.rrect((bx - 90 * s, hy - 110 * s, bx + 90 * s, hy - 20 * s), 4 * s,
            fill=(218, 210, 192), outline=(172, 164, 146), owidth=2.6 * s)
    for k in range(3):
        yy = hy - 100 * s + k * 34 * s
        for wx in range(-64, 65, 30):
            g.rrect((bx + wx * s, yy, bx + wx * s + 18 * s, yy + 22 * s), 2 * s,
                    fill=(88, 96, 108), outline=(64, 72, 84), owidth=1.8 * s)
    # 階段状の切妻屋根 (オランダ風)
    for k in range(3):
        yy = hy - 110 * s - k * 24 * s
        w_ = 96 * s - k * 26 * s
        g.rrect((bx - w_, yy, bx + w_, yy + 16 * s), 3 * s, fill=(92, 62, 48),
                outline=(68, 46, 36), owidth=2.2 * s)
    # オランダ旗 (三色)
    fy = hy - 200 * s
    g.line([(bx, hy - 110 * s), (bx, fy)], P.WOOD_D, 5 * s)
    for k, c in enumerate([(166, 62, 54), (240, 240, 238), (46, 74, 138)]):
        g.rrect((bx, fy + k * 16 * s, bx + 44 * s, fy + (k + 1) * 16 * s), 2 * s, fill=c)
    # 桟橋
    g.line([(hx + r0 * 0.55, hy + 30 * s), (hx + r1 * 0.92, hy + 66 * s)],
           P.WOOD_D, 8 * s)


def japan_map_trade(g, x, y, s, seed=0):
    """日本地図と交易ルート (羊皮紙の海図). (x,y)=中心."""
    w, h = 560 * s, 360 * s
    g.rrect((x - w / 2, y - h / 2, x + w / 2, y + h / 2), 10 * s,
            fill=(238, 230, 208), outline=(150, 120, 88), owidth=4 * s)
    speckle(g, (x - w / 2 + 10, y - h / 2 + 10, x + w / 2 - 10, y + h / 2 - 10), 60,
            [(222, 212, 188), (250, 244, 226)], r=(2, 5), seed=seed)
    # 本州 (大きい弧状の島)
    hon = (qbez((x - 240 * s, y - 40 * s), (x - 180 * s, y - 130 * s), (x - 60 * s, y - 110 * s), 14)
           + qbez((x - 60 * s, y - 110 * s), (x + 40 * s, y - 90 * s), (x + 120 * s, y - 20 * s), 14)
           + qbez((x + 120 * s, y - 20 * s), (x + 90 * s, y + 30 * s), (x + 20 * s, y + 10 * s), 12)
           + qbez((x + 20 * s, y + 10 * s), (x - 120 * s, y + 10 * s), (x - 240 * s, y - 40 * s), 14))
    g.poly(hon, fill=(178, 192, 152), outline=(140, 156, 120), owidth=3 * s)
    # 四国
    g.poly(blob_pts(x - 120 * s, y + 60 * s, 56 * s, 30 * s, seed=2, wobble=0.14),
           fill=(178, 192, 152), outline=(140, 156, 120), owidth=2.6 * s)
    # 九州 (南西)
    g.poly(blob_pts(x - 220 * s, y + 80 * s, 52 * s, 62 * s, seed=3, wobble=0.16),
           fill=(178, 192, 152), outline=(140, 156, 120), owidth=2.6 * s)
    # 北海道 (北東・小さく)
    g.poly(blob_pts(x + 200 * s, y - 120 * s, 48 * s, 34 * s, seed=4, wobble=0.18),
           fill=(168, 182, 146), outline=(140, 156, 120), owidth=2.6 * s)
    # 江戸・長崎・出島の港ドット
    for (px, py, c) in [(x + 90 * s, y - 30 * s, P.SHU), (x - 210 * s, y + 60 * s, (70, 90, 150))]:
        g.circle(px, py, 7 * s, fill=c, outline=shade(c, 0.7), owidth=2 * s)
    # 交易ルート (点線の弧)
    for (x2, y2, c) in [(x + 260 * s, y + 60 * s, P.SHU), (x - 290 * s, y + 130 * s, (70, 90, 150))]:
        g.line(qbez((x - 210 * s, y + 60 * s), ((x - 210 * s + x2) / 2, y - 60 * s), (x2, y2), 14),
               c, 3.4 * s)
        # 波線風に点を打つ
        for k in range(7):
            t = (k + 1) / 8
            bx_, by_ = qbez((x - 210 * s, y + 60 * s), ((x - 210 * s + x2) / 2, y - 60 * s),
                            (x2, y2), 14)[int(t * 13)]
            g.circle(bx_, by_, 4 * s, fill=(238, 230, 208))
    # 磁針 (羅針盤)
    g.circle(x + w / 2 - 70 * s, y - h / 2 + 60 * s, 34 * s, fill=(232, 226, 206),
             outline=(150, 120, 88), owidth=3 * s)
    g.line([(x + w / 2 - 70 * s, y - h / 2 + 84 * s), (x + w / 2 - 70 * s,
            y - h / 2 + 34 * s)], (176, 90, 70), 5 * s)
    g.line([(x + w / 2 - 82 * s, y - h / 2 + 60 * s), (x + w / 2 - 58 * s,
            y - h / 2 + 60 * s)], (110, 110, 120), 4 * s)


# ================================================================ ep08 (幕末)


def black_ship(g, x, y, s, seed=0, smoke=True):
    """黒船 (ペリーの蒸気軍艦). s=1 で全長約 520px. y=喫水線."""
    hull = P.BLACKSHIP
    L = 260 * s
    g.ellipse((x - L * 1.05, y + 8 * s, x + L * 1.05, y + 22 * s),
              fill=with_alpha((26, 34, 48), 90))
    top = ([(x - L, y - 64 * s)]
           + qbez((x - L, y - 64 * s), (x - L * 0.3, y - 38 * s), (x, y - 32 * s), 12)
           + qbez((x, y - 32 * s), (x + L * 0.3, y - 38 * s), (x + L, y - 68 * s), 12))
    bot = ([(x + L * 0.97, y + 2 * s)]
           + qbez((x + L * 0.97, y + 2 * s), (x + L * 0.2, y + 18 * s), (x, y + 19 * s), 12)
           + qbez((x, y + 19 * s), (x - L * 0.2, y + 18 * s), (x - L * 0.97, y + 2 * s), 12))
    g.poly(top + bot, fill=hull, outline=shade(hull, 0.7), owidth=3 * s)
    # 砲門の並び
    for k in range(7):
        g.rrect((x - L * 0.75 + k * L * 0.22, y - 44 * s, x - L * 0.75 + k * L * 0.22 + 14 * s,
                 y - 34 * s), 2 * s, fill=(28, 30, 36))
    # 外輪 (パドルホイールの箱)
    for sx in (-1, 1):
        wx = x + sx * L * 0.42
        g.rrect((wx - 22 * s, y - 96 * s, wx + 22 * s, y - 24 * s), 6 * s,
                fill=shade(hull, 0.85), outline=shade(hull, 0.6), owidth=2.6 * s)
        for k in range(6):
            a = math.tau * k / 6
            g.rrect((wx + math.cos(a) * 12 * s - 4 * s, y - 62 * s + math.sin(a) * 22 * s - 4 * s,
                     wx + math.cos(a) * 12 * s + 4 * s, y - 62 * s + math.sin(a) * 22 * s + 4 * s),
                    2 * s, fill=shade(hull, 1.2))
    # マスト (帆を収めた状態) と索
    for mx in (-150 * s, -60 * s, 150 * s):
        mx = x + mx
        g.line([(mx, y - 62 * s), (mx, y - 190 * s)], shade(hull, 0.8), 6 * s)
        g.poly([(mx, y - 186 * s), (mx + 56 * s, y - 178 * s), (mx, y - 168 * s)],
               fill=(210, 208, 202), outline=shade(hull, 0.7), owidth=2.2 * s)
        g.line([(mx + 40 * s, y - 62 * s), (mx + 40 * s, y - 180 * s)],
               with_alpha((210, 208, 202), 150), 1.8 * s)
    # 煙突と煙
    for (sx_, h_) in [(-90 * s, 90 * s), (-40 * s, 104 * s)]:
        px = x + sx_
        g.rrect((px - 10 * s, y - 62 * s - h_, px + 10 * s, y - 58 * s), 4 * s,
                fill=(64, 66, 72), outline=shade(hull, 0.6), owidth=2.4 * s)
        g.rrect((px - 12 * s, y - 62 * s - h_, px + 12 * s, y - 58 * s - h_ + 6 * s), 3 * s,
                fill=shade(hull, 1.2))
    if smoke:
        smoke_wisp(g, x - 40 * s, y - 178 * s, 1.6 * s, color=(84, 84, 88), alpha=190,
                   seed=seed)
        smoke_wisp(g, x - 92 * s, y - 164 * s, 1.3 * s, color=(84, 84, 88), alpha=170,
                   seed=seed + 1)
    # 星条旗
    fx = x + L * 0.78
    g.line([(fx, y - 60 * s), (fx, y - 132 * s)], shade(hull, 0.9), 4.4 * s)
    for k, c in enumerate([(180, 62, 56), (240, 240, 240), (46, 74, 138)]):
        g.rrect((fx, y - 132 * s + k * 20 * s, fx + 48 * s, y - 132 * s + (k + 1) * 20 * s),
                2 * s, fill=c)
    rect(g, fx, y - 132 * s, fx + 20 * s, y - 112 * s, fill=(58, 74, 140))


def snow_gate(g, x, y, s, seed=0):
    """桜田門 (雪の積もる御門). y=地面."""
    # 石垣の門
    g.rrect((x - 240 * s, y - 120 * s, x + 240 * s, y), 10 * s,
            fill=shade(P.ISHIGAKI, 0.95), outline=shade(P.ISHIGAKI, 0.7), owidth=3 * s)
    # 櫓 (門の上の建物)
    rect(g, x - 130 * s, y - 210 * s, x + 130 * s, y - 120 * s, fill=(104, 92, 84),
           outline=shade((104, 92, 84), 0.8), owidth=2.6 * s)
    curved_roof(g, x, y - 210 * s, 168 * s, 104 * s, 40 * s, P.TILE, shade(P.TILE, 0.85),
                s=s)
    rect(g, x - 36 * s, y - 92 * s, x + 36 * s, y - 6 * s, fill=(60, 52, 50))
    # 雪の積もり (屋根と石垣の上端)
    g.line(qbez((x - 168 * s, y - 216 * s), (x, y - 252 * s), (x + 168 * s, y - 216 * s), 14),
           (240, 244, 248), 14 * s)
    g.line([(x - 240 * s, y - 118 * s), (x + 240 * s, y - 118 * s)], (240, 244, 248), 9 * s)
    rnd = random.Random(seed)
    for _ in range(10):
        px = x + rnd.uniform(-230, 230) * s
        py = y - rnd.uniform(20, 110) * s
        g.ellipse((px - 16 * s, py - 5 * s, px + 16 * s, py + 5 * s),
                  fill=with_alpha((240, 244, 248), 200))


def shishi(g, x, y, s, col=(64, 54, 62), sword=True, seed=0):
    """志士 (着流し+日本刀の立姿). y=地面."""
    # 脚 (袴)
    g.poly([(x - 20 * s, y - 66 * s), (x - 8 * s, y - 66 * s), (x - 12 * s, y),
            (x - 22 * s, y)], fill=col, outline=shade(col, 0.7), owidth=2 * s)
    g.poly([(x + 8 * s, y - 66 * s), (x + 20 * s, y - 66 * s), (x + 22 * s, y),
            (x + 12 * s, y)], fill=col, outline=shade(col, 0.7), owidth=2 * s)
    # 胴
    g.rrect((x - 22 * s, y - 132 * s, x + 22 * s, y - 60 * s), 8 * s, fill=col,
            outline=shade(col, 0.7), owidth=2.2 * s)
    # 肩に羽織の陰
    g.rrect((x - 26 * s, y - 134 * s, x + 26 * s, y - 96 * s), 8 * s,
            fill=shade(col, 0.85), outline=shade(col, 0.7), owidth=2 * s)
    # 頭 (髷)
    g.circle(x, y - 152 * s, 20 * s, fill=P.SKIN, outline=P.OUTLINE, owidth=2.4 * s)
    g.rrect((x - 20 * s, y - 174 * s, x + 20 * s, y - 156 * s), 6 * s,
            fill=(44, 38, 42), outline=shade((44, 38, 42), 0.7), owidth=2 * s)
    g.circle(x, y - 178 * s, 8 * s, fill=(44, 38, 42))
    g.line([(x - 8 * s, y - 152 * s), (x - 3 * s, y - 152 * s)], P.OUTLINE, 2.4 * s)
    g.line([(x + 3 * s, y - 152 * s), (x + 8 * s, y - 152 * s)], P.OUTLINE, 2.4 * s)
    # 刀 (腰に差す or 抜く)
    if sword:
        g.line([(x + 10 * s, y - 96 * s), (x + 74 * s, y - 160 * s)], (150, 148, 156), 5 * s)
        g.line([(x + 74 * s, y - 160 * s), (x + 84 * s, y - 170 * s)], (96, 66, 52), 6 * s)
        g.rrect((x + 4 * s, y - 102 * s, x + 16 * s, y - 92 * s), 3 * s, fill=(70, 52, 44))


# ================================================================ ep09/ep10 (明治〜現代)


def brick_building(g, x, y, s, w=200, floors=2, col=P.BRICK_RED, seed=0):
    """赤煉瓦の洋館. s=1 で幅約 w*2px. y=地面."""
    bw = w * s
    bh = (floors * 90 + 20) * s
    rect(g, x - bw, y - bh, x + bw, y, fill=col, outline=shade(col, 0.72), owidth=2.6 * s)
    for k in range(int(bh / (14 * s))):
        yy = y - bh + 8 * s + k * 14 * s
        g.line([(x - bw + 6 * s, yy), (x + bw - 6 * s, yy)], shade(col, 0.82), 2.4 * s)
    # 白い帯と窓
    for f in range(floors):
        fy = y - bh + f * 90 * s + 26 * s
        for wx in range(int(-bw * 0.62), int(bw * 0.63), 60):
            g.rrect((x + wx * s, fy, x + wx * s + 34 * s, fy + 44 * s), 3 * s,
                    fill=(200, 216, 214), outline=shade(col, 0.6), owidth=2 * s)
            g.line([(x + wx * s + 17 * s, fy + 2 * s), (x + wx * s + 17 * s, fy + 42 * s)],
                   shade(col, 0.6), 2.4 * s)
    curved_roof(g, x, y - bh, bw + 24 * s, bw * 0.42, 34 * s, (86, 88, 84),
                shade((86, 88, 84), 0.8), lift=8 * s, s=s)


def steam_train(g, x, y, s, smoke=True, seed=0):
    """蒸気機関車+客車. s=1 で機関車幅約 260px. y=線路の地面."""
    # 線路
    rect(g, x - 700 * s, y, x + 900 * s, y + 14 * s, fill=(120, 104, 88))
    rect(g, x - 700 * s, y - 4 * s, x + 900 * s, y + 2 * s, fill=(84, 74, 64))
    for k in range(int(1600 * s / 60)):
        px = x - 700 * s + k * 60 * s
        rect(g, px, y, px + 16 * s, y + 14 * s, fill=(96, 84, 70))
    # 機関車
    bx = x
    g.rrect((bx - 130 * s, y - 130 * s, bx + 110 * s, y - 20 * s), 10 * s,
            fill=(52, 54, 62), outline=(36, 38, 44), owidth=2.8 * s)
    g.rrect((bx - 118 * s, y - 96 * s, bx - 30 * s, y - 34 * s), 8 * s,
            fill=(78, 80, 88), outline=(52, 54, 60), owidth=2.2 * s)
    for wx in (-90 * s, -46 * s):
        g.circle(bx + wx, y - 24 * s, 24 * s, fill=(38, 40, 46), outline=(24, 26, 30),
                 owidth=3 * s)
    g.circle(bx + 80 * s, y - 24 * s, 15 * s, fill=(38, 40, 46), outline=(24, 26, 30),
             owidth=2.6 * s)
    g.rrect((bx - 96 * s, y - 168 * s, bx - 60 * s, y - 128 * s), 4 * s,
            fill=(160, 74, 58), outline=shade((160, 74, 58), 0.7), owidth=2.2 * s)
    g.rrect((bx - 44 * s, y - 158 * s, bx + 96 * s, y - 120 * s), 6 * s,
            fill=(64, 66, 74), outline=(44, 46, 52), owidth=2.4 * s)
    if smoke:
        smoke_wisp(g, bx - 78 * s, y - 180 * s, 1.3 * s, color=(150, 150, 154),
                   alpha=170, seed=seed)
        smoke_wisp(g, bx - 60 * s, y - 216 * s, 1.1 * s, color=(150, 150, 154),
                   alpha=150, seed=seed + 1)
    # 客車
    for k in range(2):
        cx = bx + 150 * s + k * 190 * s
        g.rrect((cx - 84 * s, y - 120 * s, cx + 84 * s, y - 24 * s), 8 * s,
                fill=(150, 84, 66), outline=shade((150, 84, 66), 0.7), owidth=2.4 * s)
        for wx in range(-64, 65, 32):
            g.rrect((cx + wx * s, y - 104 * s, cx + wx * s + 22 * s, y - 56 * s), 3 * s,
                    fill=(206, 216, 214), outline=(140, 120, 100), owidth=2 * s)
        for wx in (-48 * s, 48 * s):
            g.circle(cx + wx, y - 22 * s, 16 * s, fill=(38, 40, 46), outline=(24, 26, 30),
                     owidth=2.6 * s)


def shinkansen(g, x, y, s, seed=0):
    """新幹線 (白い弾丸列車). s=1 で全長約 700px. y=軌道."""
    g.rrect((x - 360 * s, y - 66 * s, x + 340 * s, y - 12 * s), 26 * s,
            fill=(240, 242, 244), outline=(190, 194, 200), owidth=2.6 * s)
    g.poly(qbez((x + 340 * s, y - 60 * s), (x + 396 * s, y - 40 * s), (x + 396 * s, y - 16 * s), 10)
           + [(x + 340 * s, y - 12 * s)], fill=(240, 242, 244),
           outline=(190, 194, 200), owidth=2.6 * s)
    g.line([(x - 330 * s, y - 30 * s), (x + 390 * s, y - 30 * s)], (70, 78, 88), 8 * s)
    for k in range(7):
        wx = x - 300 * s + k * 96 * s
        g.rrect((wx, y - 46 * s, wx + 40 * s, y - 20 * s), 4 * s,
                fill=(96, 120, 140), outline=(70, 92, 112), owidth=2 * s)
    g.rrect((x - 350 * s, y - 8 * s, x + 350 * s, y + 6 * s), 3 * s, fill=(120, 124, 130))


def factory(g, x, y, s, seed=0, col=(196, 128, 108)):
    """洋風の工場 (ノコギリ屋根+煙突). s=1 で幅約 480px. y=地面."""
    rect(g, x - 240 * s, y - 120 * s, x + 240 * s, y, fill=col,
         outline=shade(col, 0.72), owidth=2.6 * s)
    for k in range(4):
        px = x - 220 * s + k * 120 * s
        g.poly([(px, y - 120 * s), (px + 60 * s, y - 164 * s), (px + 120 * s, y - 120 * s)],
               fill=shade(col, 0.8), outline=shade(col, 0.6), owidth=2.2 * s)
    g.rrect((x + 120 * s, y - 210 * s, x + 148 * s, y - 118 * s), 4 * s,
            fill=(108, 110, 114), outline=(84, 86, 90), owidth=2.4 * s)
    smoke_wisp(g, x + 134 * s, y - 218 * s, 1.1 * s, color=(150, 150, 154), alpha=170,
               seed=seed)
    for wx in range(-200, 201, 66):
        g.rrect((x + wx * s, y - 84 * s, x + wx * s + 40 * s, y - 30 * s), 3 * s,
                fill=(198, 214, 210), outline=shade(col, 0.62), owidth=2 * s)


def rickshaw(g, x, y, s, puller=(96, 82, 70)):
    """人力車. y=地面."""
    g.rrect((x - 6 * s, y - 92 * s, x + 10 * s, y - 62 * s), 5 * s, fill=shade(puller, 0.85),
            outline=P.OUTLINE, owidth=2.2 * s)
    g.circle(x + 2 * s, y - 100 * s, 12 * s, fill=P.SKIN, outline=P.OUTLINE, owidth=2.2 * s)
    g.rrect((x - 2 * s, y - 114 * s, x + 6 * s, y - 96 * s), 4 * s, fill=(52, 46, 50))
    g.line([(x + 8 * s, y - 70 * s), (x + 60 * s, y - 88 * s)], P.WOOD_D, 5 * s)
    g.rrect((x + 44 * s, y - 128 * s, x + 128 * s, y - 64 * s), 8 * s,
            fill=(164, 96, 76), outline=shade((164, 96, 76), 0.7), owidth=2.4 * s)
    g.poly([(x + 40 * s, y - 128 * s), (x + 132 * s, y - 128 * s), (x + 118 * s, y - 158 * s),
            (x + 54 * s, y - 158 * s)], fill=(212, 196, 158), outline=shade((180, 160, 124),
            0.8), owidth=2.4 * s)
    g.circle(x + 66 * s, y - 30 * s, 26 * s, fill=(38, 40, 46), outline=(24, 26, 30),
             owidth=3 * s)
    for k in range(6):
        a = math.tau * k / 6
        g.line([(x + 66 * s, y - 30 * s), (x + 66 * s + math.cos(a) * 24 * s,
                y - 30 * s + math.sin(a) * 24 * s)], (70, 72, 78), 2.6 * s)
    g.line([(x + 92 * s, y - 64 * s), (x + 66 * s, y - 4 * s)], P.WOOD_D, 6 * s)


def gaslamp(g, x, y, s):
    """ガス灯. y=地面."""
    g.line([(x, y), (x, y - 190 * s)], (58, 60, 66), 7 * s)
    g.rrect((x - 14 * s, y - 236 * s, x + 14 * s, y - 190 * s), 8 * s,
            fill=(226, 208, 160), outline=(172, 156, 118), owidth=2.6 * s)
    g.poly([(x - 18 * s, y - 236 * s), (x + 18 * s, y - 236 * s), (x + 10 * s, y - 252 * s),
            (x - 10 * s, y - 252 * s)], fill=(58, 60, 66))
    gl = radial((int(160 * s * g.ss), int(160 * s * g.ss)), (255, 216, 150),
                alpha_in=120, power=2.2)
    g.img.alpha_composite(gl, (int((x - 80 * s) * g.ss), int((y - 316 * s) * g.ss)))


def schoolhouse(g, x, y, s, seed=0):
    """洋風小学校. s=1 で幅約 420px. y=地面."""
    rect(g, x - 210 * s, y - 150 * s, x + 210 * s, y, fill=(214, 210, 200),
         outline=shade((214, 210, 200), 0.76), owidth=2.6 * s)
    curved_roof(g, x, y - 150 * s, 240 * s, 120 * s, 36 * s, (88, 90, 84),
                shade((88, 90, 84), 0.8), lift=8 * s, s=s)
    rect(g, x - 14 * s, y - 90 * s, x + 14 * s, y, fill=(88, 74, 64))
    for wx in (-150, -80, 80, 150):
        g.rrect((x + wx * s - 26 * s, y - 110 * s, x + wx * s + 26 * s, y - 60 * s), 3 * s,
                fill=(196, 212, 210), outline=shade((214, 210, 200), 0.68), owidth=2.2 * s)
    g.line([(x - 210 * s, y - 108 * s), (x + 210 * s, y - 108 * s)], shade((214, 210, 200),
           0.72), 4 * s)
    # 国旗
    g.line([(x + 250 * s, y), (x + 250 * s, y - 240 * s)], P.WOOD_D, 6 * s)
    rect(g, x + 250 * s, y - 240 * s, x + 322 * s, y - 196 * s, fill=(238, 238, 236))
    g.circle(x + 286 * s, y - 218 * s, 15 * s, fill=P.SHU, outline=shade(P.SHU, 0.7),
             owidth=2)


def castle_ruins(g, x, y, s, seed=0):
    """廃藩で取り壊された城跡 (石垣と崩れた柵)."""
    g.ellipse((x - 300 * s, y - 8 * s, x + 300 * s, y + 14 * s),
              fill=with_alpha((60, 60, 52), 50))
    rect(g, x - 260 * s, y - 90 * s, x + 260 * s, y, fill=shade(P.ISHIGAKI, 0.88),
         outline=shade(P.ISHIGAKI, 0.68), owidth=3 * s)
    for k in range(4):
        yy = y - 90 * s + k * 22 * s
        g.line([(x - 260 * s, yy), (x + 260 * s, yy)], shade(P.ISHIGAKI, 0.7), 3.4 * s)
    # 崩れた石 (散在)
    rnd = random.Random(seed)
    for _ in range(10):
        px = x + rnd.uniform(-240, 240) * s
        py = y - rnd.uniform(90, 130) * s
        g.rrect((px, py, px + rnd.uniform(14, 26) * s, py + rnd.uniform(8, 14) * s),
                2 * s, fill=shade(P.ISHIGAKI, rnd.uniform(0.75, 1.1)),
                outline=shade(P.ISHIGAKI, 0.66), owidth=1.8 * s)


def war_ruins(g, x, y, s, seed=0):
    """焼け野原の廃墟 (鉄骨と瓦礫). s=1 で幅約 900px. y=地面."""
    rnd = random.Random(seed)
    ground_y = y
    for k in range(6):
        px = x - 380 * s + k * 150 * s
        ph = rnd.uniform(70, 150) * s
        rect(g, px, ground_y - ph, px + 110 * s, ground_y, fill=(96, 94, 92),
             outline=(72, 70, 68), owidth=2.6 * s)
        # 焼けた鉄骨
        for b in range(3):
            bx = px + 20 * s + b * 34 * s
            g.line([(bx, ground_y - ph), (bx, ground_y - ph - 30 * s)], (58, 56, 54),
                   4.4 * s)
        for w_ in range(3):
            wx = px + rnd.uniform(10, 80) * s
            wy = ground_y - rnd.uniform(20, ph - 16)
            g.rrect((wx, wy, wx + 26 * s, wy + 18 * s), 2 * s, fill=(52, 50, 48))
    # 瓦礫
    speckle(g, (x - 430 * s, ground_y - 20 * s, x + 430 * s, ground_y + 10 * s), 130,
            [(110, 106, 100), (130, 126, 120), (88, 86, 84)], r=(3, 8), seed=seed)

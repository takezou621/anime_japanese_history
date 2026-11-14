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

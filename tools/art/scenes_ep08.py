"""ep08 シーン背景 (幕末) — script.json の background 名と 1:1 対応.

黒船・桜田門の雪・蛤御門の戦火・薩長志士・大政奉還・夜明けの空。
テキストは焼き込まない。
"""
from __future__ import annotations

import math
import random

from artlib import palette as P
from artlib.canvas import (Canvas, blob_pts, dots_pattern, gradient, qbez,
                           radial, shade, speckle, tint, with_alpha)
from artlib.nature import (birds, cloud, clouds_row, forest_band, grass_tufts,
                           ground, moon, mountain_ridge, reeds_fg, ridge, sky,
                           stars, sun, tree)
from artlib.props import (black_ship, boat, campfire, daigokuden, kabuto, nobori,
                          rice_paddy, samurai_rider, shishi, smoke_wisp,
                          snow_gate, suzakumon, tenshu, tile_roof_house, torch,
                          torii)
from artlib.props import rect
from scenes_ep07 import daimyo_procession, fuji

W, H = 1920, 1080


def new_canvas():
    return Canvas(W, H, ss=2)


def _crowd(g, box, n, seed=0, col=(70, 62, 68)):
    """人群のシルエット."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(n):
        px = rnd.uniform(x0, x1)
        py = rnd.uniform(y0, y1)
        s_ = rnd.uniform(0.8, 1.2)
        g.circle(px, py - 26 * s_, 9 * s_, fill=col)
        g.poly([(px - 10 * s_, py - 18 * s_), (px + 10 * s_, py - 18 * s_),
                (px + 7 * s_, py + 2 * s_), (px - 7 * s_, py + 2 * s_)], fill=col)


def _dust(g, box, n, seed=0, color=(188, 174, 148), alpha=110):
    rnd = random.Random(seed)
    for _ in range(n):
        px = rnd.uniform(box[0], box[2])
        py = rnd.uniform(box[1], box[3])
        r_ = rnd.uniform(20, 70)
        g.ellipse((px - r_, py - r_ * 0.4, px + r_, py + r_ * 0.4),
                  fill=with_alpha(color, rnd.randint(40, alpha)))


# ---------------------------------------------------------------- 黒船と開国


def bg_bakumatsu_blackship(cv):
    """黒船来航 (1853・浦賀沖)."""
    sky(cv, [(0.00, (110, 140, 176)), (0.55, (176, 200, 220)), (1.00, (240, 234, 220))])
    g = cv.g()
    clouds_row(cv, 150, 3, 40, seed=2, base=(214, 218, 222), under=(160, 166, 174), alpha=235)
    horizon = 460
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (136, 180, 208)), (0.4, (96, 154, 198)), (1, (64, 122, 170))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(3)
    for _ in range(26):
        yy = rnd.uniform(horizon + 10, H - 20)
        ln = rnd.uniform(30, 150)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((240, 250, 255), rnd.randint(50, 130)))
    # 黒船 (主役)
    black_ship(g, 1150, 660, 1.35, seed=1)
    # 見物する日本の小舟
    boat(g, 260, 940, 0.9, oars=2, figure=True, seed=2)
    boat(g, 500, 830, 0.6, oars=1, seed=3)
    # 遠くの浦賀の岬
    g.poly([(W, horizon), (W, 330)] + [(x, 330 + 40 * math.sin(x * 0.005))
                                       for x in range(1920, 1550, -50)] + [(1550, 458)],
           fill=(140, 160, 146))
    birds(g, [(700, 270), (800, 310), (760, 240)], 12, width=3.4)


def bg_bakumatsu_court(cv):
    """京都朝廷 (動揺する公家の宮中)."""
    sky(cv, P.SKY_HEIAN_DAY)
    g = cv.g()
    sun(g, 300, 190, 52, halo=0.45)
    clouds_row(cv, 150, 3, 32, seed=4)
    mountain_ridge(cv, 440, 110, ((110, 140, 130), (170, 190, 168)), seed=5, freq=1.9)
    sand = gradient((int(W * cv.ss), int((H - 600) * cv.ss)),
                    [(0, (238, 236, 226)), (1, (214, 212, 202))], "v")
    cv.img.alpha_composite(sand, (0, int(600 * cv.ss)))
    g.line([(0, 602), (W, 602)], (186, 184, 172), 4)
    speckle(g, (0, 620, W, 1080), 180, [(226, 224, 212), (204, 202, 190)], r=(1.6, 3.6), seed=6)
    # 紫宸殿
    daigokuden(g, 960, 880, 0.78, roof=(118, 132, 100), roof_d=(92, 106, 80), lit=False, seed=2)
    _wband(g, 40, 540, 740, 830, seed=3)
    _wband(g, 1380, 1880, 740, 830, seed=4)
    # 公家の列 (シルエット)
    for k in range(6):
        px = 300 + k * 100
        g.circle(px, 1000 - 52, 12, fill=(72, 60, 76))
        g.poly([(px - 16, 956), (px + 16, 956), (px + 11, 1008), (px - 11, 1008)],
               fill=(72, 60, 76))
    grass_tufts(g, (0, 660, W, 1070), 70, (150, 148, 104), seed=7)
    birds(g, [(1200, 240), (1300, 280), (1260, 210)], 12, width=3.2)


def _wband(g, x0, x1, y0, y1, wall=P.PLASTER, frame=P.VERMILION_WOOD,
           step=90, seed=0):
    rect(g, x0, y0, x1, y1, fill=wall, outline=shade(wall, 0.8), owidth=2.2)
    rnd = random.Random(seed)
    px = x0 + 10
    while px < x1 - 14:
        rect(g, px, y0, px + 11, y1, fill=frame)
        px += step + rnd.uniform(-6, 6)
    g.line([(x0, y0), (x1, y0)], shade(frame, 0.7), 4)


def bg_bakumatsu_treaty(cv):
    """日米和親条約・開国の調印."""
    sky(cv, P.SKY_EDO_DAY)
    g = cv.g()
    sun(g, 340, 180, 52, halo=0.45)
    clouds_row(cv, 140, 3, 30, seed=8)
    mountain_ridge(cv, 430, 100, ((108, 136, 130), (166, 186, 164)), seed=9, freq=1.9)
    ground(cv, 630, (190, 184, 136), dark=(158, 152, 108), curve=12, seed=10,
           speckles=150, speckle_colors=[(170, 164, 118), (204, 198, 150)],
           speckle_r=(2, 5))
    # 幕舎 (条約調印の儀式)
    for bx in (760, 1160):
        rect(g, bx - 90, 580, bx + 90, 680, fill=(214, 202, 172),
             outline=(168, 154, 122), owidth=2.4)
        g.poly([(bx - 98, 580), (bx + 98, 580), (bx + 76, 548), (bx - 76, 548)],
               fill=(96, 84, 72), outline=(72, 62, 54), owidth=2.6)
        # 卓と文書
        rect(g, bx - 60, 700, bx + 60, 740, fill=(116, 84, 58), outline=(86, 62, 42), owidth=3.4)
        g.rrect((bx - 44, 664, bx + 44, 712), 6, fill=(238, 232, 214),
                outline=(190, 182, 160), owidth=2.4)
    # 両国の旗
    g.line([(420, 700), (420, 420)], P.WOOD_D, 8)
    for k, c in enumerate([(180, 62, 56), (240, 240, 240), (46, 74, 138)]):
        rect(g, 420, 420 + k * 22, 420 + 52, 420 + (k + 1) * 22, fill=c)
    g.line([(1500, 700), (1500, 420)], P.WOOD_D, 8)
    rect(g, 1500, 420, 1552, 442, fill=(238, 238, 236))
    g.circle(1526, 431, 11, fill=P.SHU, outline=shade(P.SHU, 0.7), owidth=2)
    # 席につく者たちのシルエット
    for bx in (760, 1160):
        for k in range(3):
            px = bx - 50 + k * 50
            g.circle(px, 590, 12, fill=(84, 68, 60))
            g.poly([(px - 15, 600), (px + 15, 600), (px + 10, 660), (px - 10, 660)],
                   fill=(84, 68, 60))
    grass_tufts(g, (0, 690, W, 1070), 80, (150, 148, 104), seed=11)
    birds(g, [(700, 240), (800, 280), (760, 210)], 12, width=3.2)


def bg_bakumatsu_ansei(cv):
    """安政の大獄 (暗い牢獄と雪の灯)."""
    cv.img.alpha_composite(gradient(cv.img.size,
                                    [(0, (44, 46, 62)), (0.6, (62, 64, 78)),
                                     (1, (88, 90, 100))], "v"))
    g = cv.g()
    # 牢の格子 (縦鉄棒)
    rect(g, 200, 80, 1720, 860, fill=(60, 62, 72), outline=(44, 46, 54), owidth=5)
    for k in range(15):
        px = 240 + k * 100
        g.rrect((px - 7, 100, px + 7, 840), 4, fill=(88, 90, 100), outline=(60, 62, 70),
                owidth=2.4)
    # 格子の奥に鎖で繋がれた者のシルエット
    g.circle(960, 480, 34, fill=(36, 34, 44))
    g.poly([(928, 508), (992, 508), (978, 700), (942, 700)], fill=(36, 34, 44))
    for k in range(5):
        g.circle(940 + k * 12, 560 + k * 26, 7, fill=(72, 74, 86),
                 outline=(52, 54, 62), owidth=2)
    # 雪の灯り (窓から差す白)
    rect(g, 120, 200, 260, 420, fill=with_alpha((226, 232, 240), 120))
    gl = radial((int(700 * cv.ss), int(700 * cv.ss)), (200, 210, 226),
                alpha_in=70, power=2.4)
    cv.img.alpha_composite(gl, (int(60 * cv.ss), int(100 * cv.ss)))
    # 蝋燭
    g.rrect((1740, 700, 1790, 800), 6, fill=(150, 120, 90), outline=(120, 96, 72), owidth=2.4)
    g.rrect((1754, 640, 1776, 700), 4, fill=(236, 216, 180))
    gl2 = radial((int(400 * cv.ss), int(400 * cv.ss)), (255, 210, 150),
                 alpha_in=90, power=2.2)
    cv.img.alpha_composite(gl2, (int(1580 * cv.ss), int(500 * cv.ss)))
    # 雪片
    rnd = random.Random(12)
    for _ in range(40):
        px, py = rnd.uniform(200, 1720), rnd.uniform(90, 840)
        g.circle(px, py, rnd.uniform(1.4, 3), fill=with_alpha((230, 234, 240), rnd.randint(60, 150)))


def bg_bakumatsu_sonno(cv):
    """尊王攘夷運動 (夜の都と志士たち)."""
    sky(cv, [(0.00, (40, 36, 66)), (0.55, (84, 64, 92)), (1.00, (150, 100, 110))])
    g = cv.g()
    stars(g, (40, 40, 1880, 400), 60, seed=13)
    mountain_ridge(cv, 470, 100, ((40, 34, 60), (80, 60, 86)), seed=14, freq=1.8)
    ground(cv, 630, (86, 74, 84), dark=(70, 60, 72), curve=12, seed=15,
           speckles=140, speckle_colors=[(76, 64, 76), (98, 84, 94)],
           speckle_r=(2, 5))
    # 街道と町家
    for (hx, hy, hs) in [(250, 660, 0.8), (500, 645, 0.7), (1420, 650, 0.72),
                         (1660, 668, 0.8)]:
        tile_roof_house(g, hx, hy, hs, seed=int(hx))
    # 志士たち (夜の集会)
    for k in range(5):
        shishi(g, 860 + k * 90 + (k % 2) * 30, 900 + (k % 2) * 20, 0.72 + (k % 3) * 0.06,
               seed=16 + k)
    # 攘夷の幟 (白に日の丸)
    nobori(g, 400, 860, 0.85, col=(238, 238, 236), seed=17)
    nobori(g, 1520, 860, 0.85, col=(238, 238, 236), seed=18)
    # 行灯の灯り
    for lx in (700, 1100, 1460):
        g.rrect((lx - 12, 690, lx + 12, 740), 6, fill=(230, 168, 108),
                outline=(180, 128, 86), owidth=2.2)
        gl = radial((int(300 * cv.ss), int(300 * cv.ss)), (255, 200, 130),
                    alpha_in=95, power=2.2)
        cv.img.alpha_composite(gl, (int((lx - 150) * cv.ss), int((590) * cv.ss)))
    birds(g, [(700, 220), (800, 260), (760, 190)], 10, color=(36, 30, 44), width=3.6)


def bg_bakumatsu_sakurada(cv):
    """桜田門外の変 (1860・雪の御門)."""
    sky(cv, [(0.00, (124, 134, 150)), (0.55, (176, 182, 194)), (1.00, (222, 226, 230))])
    g = cv.g()
    clouds_row(cv, 150, 3, 40, seed=19, base=(210, 216, 222), under=(168, 174, 182), alpha=235)
    ground(cv, 620, (216, 220, 226), dark=(186, 190, 198), curve=12, seed=20,
           speckles=120, speckle_colors=[(200, 204, 210), (172, 176, 184)],
           speckle_r=(2, 5))
    # 桜田門
    snow_gate(g, 1180, 660, 1.0, seed=2)
    # 襲撃する志士たち (雪の中)
    for k in range(4):
        shishi(g, 240 + k * 110, 950 + (k % 2) * 24, 0.78 + (k % 3) * 0.08,
               sword=True, seed=21 + k)
    # 逃げる警戒の武士
    shishi(g, 1500, 820, 0.5, col=(96, 78, 70), sword=True, seed=25)
    # 雪片
    rnd = random.Random(26)
    for _ in range(60):
        px, py = rnd.uniform(0, W), rnd.uniform(60, 1060)
        g.circle(px, py, rnd.uniform(1.6, 3.4), fill=with_alpha((240, 244, 248),
                 rnd.randint(90, 190)))
    # 長い影
    for k in range(4):
        sx_ = 250 + k * 110
        g.ellipse((sx_ - 60, 1020, sx_ + 90, 1060), fill=with_alpha((150, 156, 168), 140))
    grass_tufts(g, (0, 700, 900, 1070), 60, (150, 154, 162), seed=27)


def bg_bakumatsu_warship(cv):
    """諸藩の軍艦 (海軍練成)."""
    sky(cv, P.SKY_EDO_DAY)
    g = cv.g()
    sun(g, 420, 180, 54, halo=0.45)
    clouds_row(cv, 150, 3, 32, seed=28)
    horizon = 420
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (138, 188, 212)), (0.4, (98, 158, 202)), (1, (66, 126, 176))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(29)
    for _ in range(26):
        yy = rnd.uniform(horizon + 10, H - 20)
        ln = rnd.uniform(30, 150)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((240, 250, 255), rnd.randint(50, 130)))
    # 練成の軍艦 (帆船×2)
    black_ship(g, 640, 700, 0.85, smoke=False, seed=1)
    black_ship(g, 1420, 840, 0.7, smoke=False, seed=2)
    birds(g, [(760, 280), (860, 320), (820, 250)], 12, width=3.4)


def bg_bakumatsu_alliance(cv):
    """薩長同盟 (1866・二つの藩が手を結ぶ)."""
    sky(cv, [(0.00, (110, 120, 160)), (0.55, (180, 150, 160)), (1.00, (238, 200, 170))])
    g = cv.g()
    clouds_row(cv, 160, 3, 40, seed=30, base=(210, 170, 170), under=(150, 110, 130), alpha=225)
    mountain_ridge(cv, 440, 110, ((100, 88, 110), (150, 116, 130)), seed=31, freq=1.8)
    ground(cv, 620, (172, 156, 116), dark=(142, 128, 94), curve=12, seed=32,
           speckles=150, speckle_colors=[(152, 138, 102), (186, 170, 130)],
           speckle_r=(2, 5))
    # 薩摩の陣 (左: 赤系) / 長州の陣 (右: 白系)
    rect(g, 160, 560, 460, 680, fill=(214, 202, 172), outline=(168, 154, 122), owidth=2.4)
    g.poly([(150, 560), (470, 560), (450, 524), (170, 524)], fill=(146, 66, 56),
           outline=(112, 50, 44), owidth=2.6)
    nobori(g, 130, 700, 0.8, col=(146, 66, 56), seed=3)
    rect(g, 1460, 560, 1760, 680, fill=(214, 202, 172), outline=(168, 154, 122), owidth=2.4)
    g.poly([(1450, 560), (1770, 560), (1750, 524), (1470, 524)], fill=(96, 88, 130),
           outline=(72, 66, 100), owidth=2.6)
    nobori(g, 1790, 700, 0.8, col=(96, 88, 130), seed=4)
    # 会合の使者 (中央で向かい合う)
    shishi(g, 880, 900, 0.9, col=(146, 66, 56), sword=False, seed=5)
    shishi(g, 1040, 900, 0.9, col=(96, 88, 130), sword=False, seed=6)
    g.rrect((700, 860, 1220, 930), 8, fill=(214, 202, 172), outline=(168, 154, 122),
            owidth=3)
    # 間の道
    g.poly([(700, 1080), (1220, 1080), (1100, 930), (820, 930)], fill=(206, 190, 152))
    grass_tufts(g, (0, 700, W, 1070), 80, (150, 140, 104), seed=7)
    birds(g, [(700, 240), (800, 280), (760, 210)], 11, width=3.2)


def bg_bakumatsu_return(cv):
    """大政奉還の儀 (1867・二条城の大広間)."""
    cv.img.alpha_composite(gradient(cv.img.size,
                                    [(0, (52, 46, 66)), (0.6, (72, 62, 82)),
                                     (1, (104, 90, 104))], "v"))
    g = cv.g()
    # 大広間の床
    rect(g, 0, 760, W, H, fill=(120, 96, 80))
    rect(g, 30, 780, W - 30, H - 14, fill=(136, 110, 88))
    # 格天井
    for k in range(3):
        rect(g, 120 + k * 560, 80, 660 + k * 560, 200, fill=(104, 88, 76),
             outline=(80, 66, 56), owidth=3.4)
    # 正面の飾り (金の屏風を構える)
    from artlib.props import gold_screen
    gold_screen(g, 960, 400, 1.0, seed=2)
    # 座る将軍 (慶喜) と公卿・役人のシルエット
    g.circle(960, 700, 30, fill=(44, 36, 50))
    g.poly([(926, 726), (994, 726), (982, 820), (938, 820)], fill=(44, 36, 50))
    for k in range(6):
        px = 380 + k * 240
        g.circle(px, 880, 22, fill=(52, 44, 58))
        g.poly([(px - 24, 900), (px + 24, 900), (px + 18, 980), (px - 18, 980)],
               fill=(52, 44, 58))
    # 上表文の卓 (中央)
    rect(g, 800, 860, 1120, 920, fill=(116, 84, 58), outline=(86, 62, 42), owidth=4)
    g.rrect((880, 820, 1040, 890), 6, fill=(238, 232, 214), outline=(190, 182, 160),
            owidth=2.6)
    g.rrect((918, 830, 1002, 866), 4, fill=(196, 118, 100), outline=(150, 88, 76),
            owidth=2.4)
    # 灯籠の行灯
    for lx in (300, 1620):
        g.rrect((lx - 20, 700, lx + 20, 780), 10, fill=(232, 170, 110),
                outline=(180, 128, 86), owidth=2.6)
        gl = radial((int(400 * cv.ss), int(400 * cv.ss)), (255, 200, 130),
                    alpha_in=95, power=2.2)
        cv.img.alpha_composite(gl, (int((lx - 200) * cv.ss), int((560) * cv.ss)))
    rect(g, 0, 760, W, 780, fill=(88, 68, 58))


def bg_bakumatsu_kaikoku(cv):
    """開港横浜 (洋館と異国船の賑わい)."""
    sky(cv, P.SKY_EDO_DAY)
    g = cv.g()
    sun(g, 340, 180, 52, halo=0.45)
    clouds_row(cv, 140, 3, 30, seed=33)
    horizon = 430
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (140, 188, 212)), (0.4, (100, 160, 204)), (1, (68, 128, 178))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(34)
    for _ in range(24):
        yy = rnd.uniform(horizon + 10, 720)
        ln = rnd.uniform(30, 140)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((240, 250, 255), rnd.randint(50, 130)))
    # 洋船
    black_ship(g, 1300, 640, 0.6, smoke=False, seed=1)
    boat(g, 700, 800, 0.7, oars=2, seed=2)
    # 岸壁と洋館・倉庫
    rect(g, 0, 760, W, H, fill=(176, 168, 148))
    rect(g, 0, 760, W, 800, fill=(152, 144, 124))
    for wx in (140, 640, 1180):
        rect(g, wx, 620, wx + 240, 764, fill=(216, 208, 190), outline=(170, 162, 146),
             owidth=3)
        g.poly([(wx - 12, 620), (wx + 252, 620), (wx + 232, 574), (wx + 12, 574)],
               fill=(120, 96, 84), outline=(94, 76, 66), owidth=2.6)
        for k in range(3):
            g.rrect((wx + 30 + k * 80, 650, wx + 90 + k * 80, 710), 3,
                    fill=(96, 104, 116), outline=(70, 78, 90), owidth=2.2)
        # 各国の旗
        for k, c in enumerate([(180, 62, 56), (240, 240, 240), (46, 74, 138)]):
            rect(g, wx + 20 + k * 24, 590, wx + 44 + k * 24, 612, fill=c)
    _crowd(g, (60, 820, 1860, 1060), 24, seed=35)
    birds(g, [(600, 240), (700, 280), (660, 210)], 12, width=3.2)


def bg_bakumatsu_kyoto(cv):
    """蛤御門の変 (1864・京で燃える戦火)."""
    sky(cv, [(0.00, (30, 26, 52)), (0.55, (92, 48, 76)), (1.00, (196, 96, 80))])
    g = cv.g()
    stars(g, (40, 40, 1500, 300), 50, seed=36)
    ground(cv, 640, (88, 70, 80), dark=(70, 56, 68), curve=12, seed=37,
           speckles=140, speckle_colors=[(76, 60, 72), (100, 80, 90)],
           speckle_r=(2, 5))
    # 御門 (蛤御門) と土塀
    snow_gate(g, 1360, 660, 0.95, seed=2)
    _wband2(g, 0, 1150, 560, 660)
    # 門の背後と左に戦火
    campfire(g, 300, 700, 1.8, stones=False, seed=38)
    campfire(g, 900, 690, 1.4, stones=False, seed=39)
    smoke_wisp(g, 330, 470, 2.0, color=(62, 52, 66), alpha=200, seed=40)
    smoke_wisp(g, 920, 470, 1.6, color=(62, 52, 66), alpha=190, seed=41)
    # 戦う武士のシルエット
    for k in range(5):
        shishi(g, 520 + k * 150, 940 + (k % 2) * 26, 0.62 + (k % 2) * 0.1,
               sword=True, seed=42 + k)
    # 松明
    torch(g, 160, 990, 1.0)
    torch(g, 1780, 1000, 1.0)
    reeds_fg(cv, 1080, seed=43, color=(40, 30, 44), n=32, s=1.0)


def _wband2(g, x0, x1, y0, y1):
    """土塀 (漆喰の塀)."""
    rect(g, x0, y0, x1, y1, fill=(196, 188, 172), outline=(158, 150, 134), owidth=3)
    for px in range(int(x0), int(x1), 200):
        g.poly([(px, y0), (px + 30, y0), (px + 34, y1), (px - 4, y1)],
               fill=with_alpha((150, 140, 124), 140))


def bg_bakumatsu_dawn(cv):
    """夜明けの空 (維新の朝)."""
    sky(cv, P.SKY_BAKUMATSU_DAWN)
    g = cv.g()
    stars(g, (40, 40, 1500, 300), 40, seed=44)
    sun(g, 1240, 660, 110, color=(246, 160, 120), core=(252, 210, 168), halo=0.4)
    mountain_ridge(cv, 520, 110, ((48, 40, 70), (100, 74, 96)), seed=45, freq=1.8)
    fuji(g, 1700, 560, 0.6, col=(64, 58, 92), snow=(214, 210, 220))
    # 都の屋根のシルエット
    rnd = random.Random(46)
    x = 0
    while x < W:
        hw = rnd.uniform(110, 180)
        hh = rnd.uniform(38, 72)
        rect(g, x, 700 - hh, x + hw, 740, fill=(58, 46, 66))
        g.poly([(x - 8, 700 - hh), (x + hw + 8, 700 - hh), (x + hw * 0.72, 700 - hh - 28),
                (x + hw * 0.28, 700 - hh - 28)], fill=(48, 38, 58))
        x += hw + rnd.uniform(16, 58)
    rect(g, 0, 736, W, H, fill=(50, 40, 60))
    speckle(g, (0, 746, W, 1080), 130, [(44, 36, 54), (60, 48, 68)], r=(2, 6), seed=47)
    # 光の帯 (地平の暁)
    g.ellipse((-200, 660, W + 200, 800), fill=with_alpha((250, 190, 150), 110))
    birds(g, [(600, 260), (720, 230), (680, 300)], 12, width=4)


# ---------------------------------------------------------------- ポイント用タイムライン


def bg_timeline(cv):
    """ep08 用ポイント背景 — 黒船〜大政奉還のタイムライン."""
    sky(cv, P.SKY_STUDIO)
    g = cv.g()
    g.circle(1700, 200, 260, outline=with_alpha(P.UI_WHITE, 40), owidth=40)
    g.circle(1700, 200, 170, outline=with_alpha(P.YAMABUKI, 70), owidth=10)
    g.circle(170, 900, 210, outline=with_alpha(P.UI_WHITE, 34), owidth=30)
    g.circle(170, 900, 130, fill=with_alpha(P.INDIGO_L, 90))
    for i in range(7):
        g.line([(i * 300 - 200, 0), (i * 300 + 160, 1080)],
               with_alpha(P.UI_WHITE, 14), 60)
    dots_pattern(g, (0, 0, 500, 400), 44, 5, P.UI_WHITE, alpha=46, seed=1)
    dots_pattern(g, (1420, 680, W, H), 44, 5, P.UI_WHITE, alpha=46, seed=2)
    band_y = 830
    g.rrect((120, band_y, 1800, band_y + 140), 70, fill=with_alpha((20, 34, 68), 210),
            outline=with_alpha(P.UI_WHITE, 110), owidth=4)
    nodes = [320, 750, 1180, 1610]
    labels = ["黒船来航 1853", "桜田門外の変 1860", "蛤御門の変 1864", "大政奉還 1867"]
    icon_y = band_y - 26
    for i, nx in enumerate(nodes):
        g.ellipse((nx - 120, icon_y - 220, nx + 120, icon_y + 6),
                  fill=with_alpha((255, 255, 255), 22))
        if i < 3:
            g.line([(nx + 64, band_y + 70), (nodes[i + 1] - 64, band_y + 70)],
                   with_alpha(P.UI_WHITE, 150), 6)
            g.poly([(nodes[i + 1] - 60, band_y + 70), (nodes[i + 1] - 84, band_y + 58),
                    (nodes[i + 1] - 84, band_y + 82)], fill=with_alpha(P.UI_WHITE, 150))
        g.circle(nx, band_y + 70, 46, fill=P.INDIGO, outline=P.YAMABUKI, owidth=6)
        g.circle(nx, band_y + 70, 9, fill=P.YAMABUKI)
        g.text((nx, band_y + 118), labels[i], 24, (214, 224, 248), "bold", "mm")
    black_ship(g, nodes[0], icon_y - 46, 0.34, smoke=False, seed=1)
    snow_gate(g, nodes[1], icon_y - 8, 0.4, seed=2)
    campfire(g, nodes[2], icon_y - 26, 0.55, stones=False, seed=3)
    smoke_wisp(g, nodes[2] + 12, icon_y - 170, 0.9, color=(140, 136, 140), alpha=180, seed=4)
    daigokuden(g, nodes[3], icon_y - 6, 0.26, roof=(118, 132, 100),
               roof_d=(92, 106, 80), lit=False, seed=5)
    gl = radial((int(1400 * cv.ss), int(900 * cv.ss)), (90, 120, 200),
                alpha_in=50, power=2.4)
    cv.img.alpha_composite(gl, (int(260 * cv.ss), int(160 * cv.ss)))

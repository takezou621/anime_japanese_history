"""ep03 シーン背景 (平安) — script.json の background 名と 1:1 対応.

雅な平安京・寝殿造・国風文化 (絵巻/仮名文字/浄土美術) の空気感。
テキストは焼き込まない (editor の overlay_text が担当)。
"""
from __future__ import annotations

import math
import random

from artlib import palette as P
from PIL import Image
from artlib.canvas import (Canvas, blob_pts, dots_pattern, gradient, qbez,
                           radial, shade, speckle, tint, with_alpha)
from artlib.nature import (birds, cloud, clouds_row, forest_band, grass_tufts,
                           ground, light_shafts, moon, mountain_ridge, reeds_fg,
                           ridge, sky, stars, sun, tree)
from artlib.props import (amida, banner_pole, campfire, daigokuden, emaki,
                          envoy_ship, grid_blocks, ox_cart, palisade, rect,
                          rice_paddy, shinden, smoke_wisp, suzakumon,
                          tile_roof_house, torch, warehouse)
from scenes_ep01 import bow_and_arrows

W, H = 1920, 1080


def new_canvas():
    return Canvas(W, H, ss=2)


def _wall_band(g, x0, x1, y0, y1, wall=P.PLASTER, frame=P.VERMILION_WOOD,
               step=90, seed=0):
    rect(g, x0, y0, x1, y1, fill=wall, outline=shade(wall, 0.8), owidth=2.2)
    rnd = random.Random(seed)
    px = x0 + 10
    while px < x1 - 14:
        rect(g, px, y0, px + 11, y1, fill=frame)
        px += step + rnd.uniform(-6, 6)
    g.line([(x0, y0), (x1, y0)], shade(frame, 0.7), 4)


# ---------------------------------------------------------------- 都・宮中


def bg_heian_capital(cv):
    """平安京 (朱雀大路と牛車)."""
    sky(cv, P.SKY_HEIAN_DAY)
    g = cv.g()
    sun(g, 1440, 170, 56, halo=0.45)
    clouds_row(cv, 140, 3, 34, seed=3)
    ridge(cv, 510, 46, (172, 182, 160), seed=4, freq=2.2)
    horizon = 540
    road_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                         [(0, (236, 226, 202)), (1, (208, 198, 172))], "v")
    cv.img.alpha_composite(road_grad, (0, int(horizon * cv.ss)))
    g.line([(0, horizon), (W, horizon)], (194, 184, 158), 4)
    # 朱雀大路
    g.poly([(720, 1080), (1220, 1080), (1012, 546), (908, 546)], fill=(230, 220, 192))
    g.line([(909, 548), (726, 1078)], (200, 190, 164), 5)
    g.line([(1011, 548), (1194, 1078)], (200, 190, 164), 5)
    g.line([(960, 556), (960, 1076)], with_alpha((210, 200, 172), 150), 8)
    # 宅地 (奥から手前)
    houses = sorted([(90, 980, 1.5), (320, 890, 1.25), (500, 812, 1.05),
                     (640, 756, 0.9), (760, 716, 0.74),
                     (1830, 970, 1.45), (1610, 885, 1.2), (1440, 806, 1.0),
                     (1300, 752, 0.85), (1180, 712, 0.7)], key=lambda t: t[1])
    for i, (hx, hy, hs) in enumerate(houses):
        tile_roof_house(g, hx, hy, hs, seed=i)
    # 遠くの羅城門代わりの正門
    suzakumon(g, 960, 592, 0.5, lit=True, seed=5)
    g.ellipse((-100, 548, W + 100, 598), fill=with_alpha((242, 234, 214), 110))
    # 牛車が大路を走る
    ox_cart(g, 890, 980, 0.85, seed=2)
    speckle(g, (720, 1000, 1220, 1080), 70, [(200, 190, 162), (218, 208, 184)],
            r=(1.6, 3.6), seed=6)
    birds(g, [(420, 220), (520, 260), (480, 190)], 12, width=3.2)


def bg_heian_palace(cv):
    """大内裏 (紫宸殿風の正殿と白砂の中庭)."""
    sky(cv, P.SKY_HEIAN_DAY)
    g = cv.g()
    sun(g, 320, 190, 56, halo=0.45)
    clouds_row(cv, 150, 3, 34, seed=7)
    mountain_ridge(cv, 460, 120, ((110, 140, 130), (170, 190, 166)), seed=8, freq=1.9)
    # 白砂の中庭
    sand = gradient((int(W * cv.ss), int((H - 600) * cv.ss)),
                    [(0, (238, 236, 226)), (1, (216, 214, 202))], "v")
    cv.img.alpha_composite(sand, (0, int(600 * cv.ss)))
    g.line([(0, 602), (W, 602)], (188, 186, 172), 4)
    speckle(g, (0, 620, W, 1080), 200, [(226, 224, 212), (204, 202, 190), (232, 230, 220)],
            r=(1.6, 3.6), seed=9)
    # 玉垣 (朱の低い柵)
    for px0 in (40, 1420):
        rect(g, px0, 700, px0 + 460, 740, fill=(226, 148, 118),
             outline=shade((226, 148, 118), 0.8), owidth=2.4)
        for px in range(px0 + 8, px0 + 460, 52):
            rect(g, px, 688, px + 10, 740, fill=P.VERMILION_WOOD)
    # 紫宸殿 (檜皮葺の正殿)
    daigokuden(g, 960, 900, 0.85, roof=(118, 132, 100), roof_d=(92, 106, 80),
               lit=False, seed=2)
    # 回廊
    _wall_band(g, 20, 560, 760, 850, seed=3)
    _wall_band(g, 1360, 1900, 760, 850, seed=4)
    # 苔庭の松
    tree(cv, 100, 1030, 1.25, kind="pine", leaf=(60, 112, 88), seed=5)
    tree(cv, 1830, 1020, 1.15, kind="pine", leaf=(60, 112, 88), seed=6)
    birds(g, [(1240, 230), (1340, 270), (1300, 200)], 12, width=3.2)


def bg_heian_court(cv):
    """朝廷 (牛車と幄舎の並ぶ宮中)."""
    sky(cv, P.SKY_HEIAN_DAY)
    g = cv.g()
    clouds_row(cv, 150, 3, 34, seed=10)
    mountain_ridge(cv, 440, 110, ((112, 140, 132), (172, 190, 168)), seed=11, freq=1.8)
    courtyard = gradient((int(W * cv.ss), int((H - 580) * cv.ss)),
                         [(0, (222, 216, 198)), (1, (200, 194, 176))], "v")
    cv.img.alpha_composite(courtyard, (0, int(580 * cv.ss)))
    g.line([(0, 582), (W, 582)], (178, 172, 154), 4)
    speckle(g, (0, 600, W, 1080), 170, [(210, 204, 186), (192, 186, 168)], r=(1.6, 4), seed=12)
    # 奥に宮殿 (2棟)
    daigokuden(g, 480, 690, 0.42, roof=(118, 132, 100), roof_d=(92, 106, 80), lit=False, seed=3)
    daigokuden(g, 1470, 690, 0.42, roof=(118, 132, 100), roof_d=(92, 106, 80), lit=False, seed=4)
    # 幄 (式の幕舎)
    for bx in (860, 1160):
        rect(g, bx - 70, 640, bx + 70, 700, fill=(226, 210, 178),
             outline=(176, 156, 122), owidth=2.4)
        for k in range(5):
            g.line([(bx - 60 + k * 30, 646), (bx - 60 + k * 30, 694)],
                   with_alpha((176, 156, 122), 160), 2.4)
        g.poly([(bx - 78, 640), (bx + 78, 640), (bx + 64, 618), (bx - 64, 618)],
               fill=(196, 100, 84), outline=(150, 74, 62), owidth=2)
    # 牛車
    ox_cart(g, 960, 950, 1.0, seed=5)
    ox_cart(g, 480, 1010, 0.62, seed=6)
    banner_pole(g, 140, 1000, 0.9)
    banner_pole(g, 1790, 1000, 0.9)
    tree(cv, 60, 1020, 1.1, kind="pine", leaf=(60, 112, 88), seed=7)
    tree(cv, 1860, 1010, 1.0, kind="pine", leaf=(60, 112, 88), seed=8)
    birds(g, [(700, 220), (800, 260), (760, 190)], 12, width=3.2)


def bg_heian_ceremony(cv):
    """大儀式 (夜の松明と幄と旗)."""
    sky(cv, P.SKY_NIGHT)
    g = cv.g()
    stars(g, (60, 40, 1860, 420), 110, seed=5, sparkle=6)
    moon(cv, 1680, 170, 52, cut_color=(14, 20, 48))
    mountain_ridge(cv, 480, 100, ((22, 32, 60), (40, 56, 92)), seed=13, freq=1.7)
    ground(cv, 600, (52, 64, 78), dark=(42, 54, 66), curve=12, seed=14,
           speckles=110, speckle_colors=[(44, 58, 70), (34, 46, 58)], speckle_r=(2, 5))
    # 幄舎の列 (式場)
    for bx in range(560, 1401, 210):
        rect(g, bx - 80, 640, bx + 80, 720, fill=(226, 210, 178),
             outline=(176, 156, 122), owidth=2.4)
        g.poly([(bx - 88, 640), (bx + 88, 640), (bx + 70, 614), (bx - 70, 614)],
               fill=(196, 100, 84), outline=(150, 74, 62), owidth=2)
        torch(g, bx - 110, 800, 1.0)
    # 旗の並び
    for i in range(6):
        banner_pole(g, 180 + i * 100, 760 + (i % 2) * 18, 0.7)
        banner_pole(g, 1210 + i * 100, 760 + (i % 2) * 18, 0.7)
    # 中央の炉
    campfire(g, 960, 980, 1.0, seed=15)
    # 地平の霞
    g.ellipse((-100, 700, W + 100, 770), fill=with_alpha((120, 140, 180), 40))
    birds(g, [(500, 200), (600, 240), (560, 170)], 11, color=(30, 30, 44), width=3.4)


# ---------------------------------------------------------------- 地方・海洋


def bg_heian_frontier(cv):
    """蝦夷地の城柵 (北の前線)."""
    sky(cv, P.SKY_FRONTIER)
    g = cv.g()
    clouds_row(cv, 170, 3, 40, seed=16, base=(226, 230, 230), under=(170, 178, 184), alpha=230)
    mountain_ridge(cv, 470, 190, ((96, 112, 128), (150, 164, 172)), seed=17, freq=1.7)
    ridge(cv, 560, 90, (110, 128, 128), seed=18, freq=2.4)
    # 冷たい霧
    g.ellipse((-100, 540, W + 100, 620), fill=with_alpha((226, 232, 232), 120))
    ground(cv, 620, (124, 140, 116), dark=(102, 118, 96), curve=14, seed=19,
           speckles=160, speckle_colors=[(110, 126, 104), (140, 154, 128)],
           speckle_r=(2, 5))
    # 城柵 (丘の上の柵 + 物見櫓)
    g.poly([(240, 880), (1680, 880), (1560, 730), (360, 730)], fill=(136, 148, 118))
    palisade(g, 300, 1650, 770, 1.0, col=(86, 62, 46), dark=(62, 44, 34), seed=5)
    # 物見櫓
    wx = 960
    rect(g, wx - 60, 610, wx + 60, 700, fill=P.WOOD_D)
    for px in (-52, -20, 20, 52):
        rect(g, wx + px - 5, 610, wx + px + 5, 700, fill=shade(P.WOOD_D, 0.85))
    g.poly([(wx - 84, 616), (wx + 84, 616), (wx + 66, 578), (wx - 66, 578)],
           fill=shade(P.WOOD, 1.08), outline=P.WOOD_D, owidth=3)
    banner_pole(g, wx - 130, 700, 0.8)
    banner_pole(g, wx + 130, 700, 0.8)
    torch(g, wx - 230, 840, 0.95)
    torch(g, wx + 230, 840, 0.95)
    # 松の森
    forest_band(cv, 700, 8, (0.7, 1.15), leaf=(52, 96, 78), seed=20)
    tree(cv, 130, 1040, 1.5, kind="pine", leaf=(48, 92, 74), seed=21)
    tree(cv, 1790, 1020, 1.4, kind="pine", leaf=(48, 92, 74), seed=22)
    grass_tufts(g, (0, 700, W, 1080), 100, (128, 142, 108), seed=23)
    birds(g, [(640, 220), (740, 260), (700, 190)], 12, color=(70, 76, 84), width=3.2)


def bg_heian_ship(cv):
    """海 (民間商船の往還)."""
    sky(cv, P.SKY_HEIAN_DAY)
    g = cv.g()
    sun(g, 420, 190, 58, halo=0.45)
    clouds_row(cv, 160, 3, 34, seed=24)
    horizon = 420
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (136, 186, 212)), (0.4, (96, 156, 200)), (1, (64, 124, 174))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(25)
    for _ in range(30):
        yy = rnd.uniform(horizon + 10, H - 20)
        ln = rnd.uniform(30, 160)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((240, 250, 255), rnd.randint(50, 130)))
    # 島影
    g.poly(blob_pts(1600, horizon - 10, 190, 52, seed=26, wobble=0.16), fill=(150, 172, 146))
    # 商船 (旗色は藍)
    envoy_ship(g, 560, 820, 1.15, figures=True, seed=1)
    envoy_ship(g, 1350, 700, 0.8, sails=1, flag=False, seed=2)
    birds(g, [(900, 280), (1010, 320), (970, 250), (1400, 260)], 13, width=3.4)


# ---------------------------------------------------------------- 貴族のくらし


def bg_heian_mansion(cv):
    """寝殿造 (池と対屋と渡殿の貴族邸)."""
    sky(cv, P.SKY_HEIAN_DAY)
    g = cv.g()
    sun(g, 1460, 190, 54, halo=0.45)
    clouds_row(cv, 150, 3, 32, seed=27)
    mountain_ridge(cv, 430, 120, ((112, 142, 132), (170, 188, 164)), seed=28, freq=1.8)
    ridge(cv, 520, 56, (126, 148, 116), seed=29, freq=2.4)
    forest_band(cv, 585, 9, (0.5, 0.9), leaf=(98, 140, 98), seed=30)
    ground(cv, 640, (190, 186, 132), dark=(158, 154, 106), curve=14, seed=31,
           speckles=150, speckle_colors=[(170, 166, 114), (204, 200, 146)],
           speckle_r=(2, 5))
    # 白砂の庭 + 寝殿造
    g.ellipse((360, 700, 1560, 830), fill=with_alpha((228, 224, 206), 190))
    shinden(g, 960, 900, 1.05, seed=2)
    # 花枝 (左の梅)
    tree(cv, 180, 1000, 1.35, kind="pine", leaf=(60, 112, 88), seed=3)
    tree(cv, 1750, 990, 1.25, kind="oak", leaf=(108, 148, 96), seed=4)
    # 菖蒲
    for ix in (620, 1310):
        for k in range(4):
            g.line([(ix + k * 12 - 18, 1020), (ix + k * 12 - 10, 980)],
                   (86, 128, 96), 3)
            g.ellipse((ix + k * 12 - 14, 972, ix + k * 12 - 2, 984), fill=(150, 128, 196))
    grass_tufts(g, (0, 690, W, 1080), 90, (152, 150, 102), seed=32)
    birds(g, [(500, 240), (600, 280), (560, 210)], 12, width=3.2)


def bg_heian_field(cv):
    """地方の田園 (庄園の里)."""
    sky(cv, [(0.00, (134, 176, 208)), (0.55, (186, 208, 224)), (1.00, (244, 234, 214))])
    g = cv.g()
    clouds_row(cv, 160, 3, 34, seed=33)
    mountain_ridge(cv, 460, 150, ((104, 138, 132), (164, 186, 164)), seed=34, freq=1.8)
    forest_band(cv, 640, 10, (0.6, 1.0), leaf=(96, 140, 96), seed=35)
    ground(cv, 650, (178, 176, 116), dark=(146, 144, 94), curve=14, seed=36,
           speckles=160, speckle_colors=[(158, 156, 102), (192, 190, 130)],
           speckle_r=(2, 5))
    rice_paddy(cv, 880, 1080, [(206, 222, 228), (168, 202, 216)], seed=37, rows_seed=7)
    tile_roof_house(g, 340, 800, 1.0, seed=4)
    tile_roof_house(g, 560, 762, 0.8, seed=5)
    warehouse(g, 1580, 750, 0.62, ladder=False, seed=6)
    g.poly([(660, 1080), (790, 1080), (724, 700), (694, 700)], fill=(200, 186, 152))
    grass_tufts(g, (0, 690, 900, 1050), 80, (140, 150, 96), seed=38)
    birds(g, [(1000, 230), (1100, 260), (1060, 200)], 12, width=3.2)


# ---------------------------------------------------------------- 国風文化


def bg_heian_writing(cv):
    """文室 (硯と筆、草仮名の詠書)."""
    # 室内: 壁と床
    cv.img.alpha_composite(gradient(cv.img.size,
                                    [(0, (222, 208, 184)), (0.6, (208, 192, 166)),
                                     (1, (168, 152, 128))], "v"))
    g = cv.g()
    # 床 (畳の縁)
    rect(g, 0, 700, W, H, fill=(164, 172, 130))
    for i in range(3):
        rect(g, 60 + i * 620, 700, 60 + i * 620 + 560, 1080, fill=(178, 186, 142),
             outline=(120, 128, 96), owidth=4)
        for k in (1, 2):
            g.line([(60 + i * 620 + 20, 700 + k * 126), (60 + i * 620 + 540, 700 + k * 126)],
                   with_alpha((120, 128, 96), 130), 2.4)
    # 障子 (開けた窓から庭)
    for wx in (1080, 1500):
        rect(g, wx, 130, wx + 300, 620, fill=(206, 196, 176), outline=(150, 138, 116), owidth=6)
        rect(g, wx + 16, 146, wx + 284, 604, fill=(214, 224, 222))
        # 庭の見え
        rect(g, wx + 16, 146, wx + 284, 380, fill=(206, 226, 216))
        g.poly(blob_pts(wx + 80, 210, 60, 34, seed=int(wx), wobble=0.16), fill=(160, 196, 160))
        g.poly(blob_pts(wx + 210, 240, 52, 30, seed=int(wx) + 1, wobble=0.16), fill=(170, 202, 166))
        rect(g, wx + 16, 380, wx + 284, 420, fill=(150, 176, 148))
        rect(g, wx + 140, 146, wx + 160, 604, fill=(206, 196, 176))
        # 格子
        for k in range(1, 6):
            g.line([(wx + 16, 146 + k * 76), (wx + 284, 146 + k * 76)],
                   with_alpha((150, 138, 116), 180), 3)
    # 掛軸 (水墨の山水)
    rect(g, 560, 90, 760, 560, fill=(236, 228, 208), outline=(150, 138, 116), owidth=5)
    g.rrect((548, 76, 772, 104), 8, fill=(88, 66, 52))
    g.rrect((548, 546, 772, 574), 8, fill=(88, 66, 52))
    g.poly(qbez((596, 470), (636, 300), (700, 250), 12)
           + qbez((700, 250), (724, 330), (724, 470), 12), fill=None,
           outline=shade((110, 110, 120), 1.1), owidth=6)
    g.arc((600, 430, 700, 500), 180, 300, with_alpha((110, 110, 120), 200), 3.4)
    # 卓 (低い机) と文房具
    rect(g, 240, 760, 940, 800, fill=(120, 88, 62), outline=(88, 62, 42), owidth=4)
    rect(g, 264, 800, 916, 840, fill=(104, 76, 52))
    # 料紙 (詠草の広がった紙)
    for (px, py, pw, ph, ang) in [(360, 700, 150, 90, -6), (560, 716, 160, 96, 4),
                                  (740, 690, 130, 80, -2)]:
        pts = [(px, py), (px + pw, py + ang * 0.6), (px + pw + 8, py + ph + ang),
               (px + 8, py + ph)]
        g.poly(pts, fill=(240, 234, 216), outline=(190, 182, 160), owidth=2.4)
        for k in range(1, 5):
            g.line([(px + 14, py + k * ph / 5), (px + pw - 6, py + ang * 0.4 + k * ph / 5)],
                   with_alpha((150, 140, 120), 170), 2.2)
    # 筆・硯・墨
    g.line([(880, 760), (924, 712)], (96, 72, 54), 7)
    g.poly([(918, 724), (942, 700), (934, 734)], fill=(232, 226, 214))
    g.ellipse((300, 812, 400, 856), fill=(110, 112, 120), outline=(80, 82, 92), owidth=3)
    g.ellipse((330, 820, 370, 844), fill=(60, 62, 74))
    # 香炉の煙
    g.ellipse((1520, 780, 1620, 840), fill=(150, 118, 92), outline=(116, 90, 70), owidth=3)
    smoke_wisp(g, 1570, 764, 1.2, color=(190, 182, 170), alpha=140, seed=3)
    # 光
    gl = radial((int(900 * cv.ss), int(600 * cv.ss)), (255, 236, 190), alpha_in=46, power=2.6)
    cv.img.alpha_composite(gl, (int(180 * cv.ss), int(560 * cv.ss)))


def bg_heian_emaki(cv):
    """絵巻 (鳥獣戯画の世界)."""
    # 美術館風の闇 + スポット
    sky(cv, [(0.0, (22, 30, 58)), (0.6, (34, 44, 80)), (1.0, (52, 62, 100))])
    g = cv.g()
    dots_pattern(g, (0, 760, 420, 1080), 46, 5, P.UI_WHITE, alpha=36, seed=2)
    dots_pattern(g, (1500, 0, W, 320), 46, 5, P.UI_WHITE, alpha=36, seed=3)
    g.circle(1770, 180, 190, outline=with_alpha(P.UI_WHITE, 40), owidth=30)
    gl = radial((int(1500 * cv.ss), int(900 * cv.ss)), (240, 230, 200),
                alpha_in=70, power=2.2)
    cv.img.alpha_composite(gl, (int(210 * cv.ss), int(140 * cv.ss)))
    # 台 (畳の敷台)
    rect(g, 260, 850, 1660, 950, fill=(96, 78, 62), outline=(70, 56, 44), owidth=4)
    rect(g, 300, 950, 1620, 1010, fill=(80, 64, 50))
    # 主の絵巻 (中央に大きく)
    emaki(g, 960, 620, 2.15, seed=1)
    # 脇の巻子
    emaki2 = Canvas(700, 460, ss=2)
    emaki(emaki2.g(), 350, 230, 1.1, seed=2)
    small = emaki2.render()
    small = small.resize((480, int(480 * small.height / small.width)), Image.LANCZOS)
    cv.img.alpha_composite(small, (60, 250))
    # 解説の札
    rect(g, 1560, 560, 1740, 700, fill=(206, 192, 164), outline=(150, 138, 116), owidth=3)
    g.line([(1590, 600), (1710, 600)], with_alpha((140, 128, 108), 200), 3)
    g.line([(1590, 630), (1710, 630)], with_alpha((140, 128, 108), 200), 3)
    g.line([(1590, 660), (1690, 660)], with_alpha((140, 128, 108), 200), 3)


def bg_heian_amida(cv):
    """阿弥陀来迎 (金色の浄土)."""
    sky(cv, [(0.00, (16, 22, 52)), (0.55, (34, 40, 84)), (1.00, (72, 66, 120))])
    g = cv.g()
    stars(g, (40, 40, 1880, 700), 130, seed=7, sparkle=10)
    rnd = random.Random(9)
    # 金の粒 (来迎の光屑)
    for _ in range(120):
        px = rnd.uniform(0, W)
        py = rnd.uniform(80, 1000)
        r_ = rnd.uniform(1.2, 3.2)
        a_ = rnd.randint(90, 220)
        g.circle(px, py, r_, fill=with_alpha(P.GOLD, a_))
    # 金色の雲
    for (cx0, cy0, rx, ry) in [(300, 800, 300, 60), (960, 880, 420, 70),
                               (1620, 780, 280, 56), (600, 300, 220, 44),
                               (1400, 340, 240, 48)]:
        g.poly(blob_pts(cx0, cy0, rx, ry, seed=int(cx0), wobble=0.2),
               fill=with_alpha((222, 186, 110), 150))
    # 阿弥陀如来
    amida(g, 960, 900, 1.5, seed=10)
    # 手前の蓮池の光
    g.ellipse((-200, 1000, W + 200, 1200), fill=with_alpha((90, 80, 130), 160))
    for _ in range(18):
        px, py = rnd.uniform(0, W), rnd.uniform(1020, 1070)
        g.rrect((px, py, px + rnd.uniform(30, 90), py + 4), 2,
                fill=with_alpha((244, 212, 140), rnd.randint(70, 150)))


def bg_heian_dusk(cv):
    """平安の黄昏 (都に広がる不穏)."""
    sky(cv, P.SKY_HEIAN_DUSK)
    g = cv.g()
    sun(g, 1380, 330, 96, color=(238, 140, 90), core=(248, 190, 130), halo=0.6)
    clouds_row(cv, 210, 3, 44, seed=39, base=(170, 92, 100), under=(84, 50, 76), alpha=230)
    mountain_ridge(cv, 520, 120, ((56, 44, 74), (104, 66, 86)), seed=40, freq=1.7)
    # 都の屋根のシルエット
    rnd = random.Random(41)
    x = 0
    while x < W:
        hw = rnd.uniform(110, 190)
        hh = rnd.uniform(40, 84)
        rect(g, x, 660 - hh, x + hw, 700, fill=(70, 54, 72))
        g.poly([(x - 8, 660 - hh), (x + hw + 8, 660 - hh), (x + hw * 0.72, 660 - hh - 30),
                (x + hw * 0.28, 660 - hh - 30)], fill=(58, 44, 62))
        x += hw + rnd.uniform(16, 60)
    rect(g, 0, 696, W, H, fill=(58, 46, 64))
    speckle(g, (0, 710, W, 1080), 150, [(50, 40, 58), (66, 52, 70), (78, 60, 74)],
            r=(2, 6), seed=42)
    # 遠くの火と煙
    for (fx, s_) in [(520, 1.0), (1060, 0.8)]:
        g.poly(qbez((fx - 14, 690), (fx - 12, 654), (fx, 630), 8)
               + qbez((fx, 630), (fx + 12, 654), (fx + 14, 690), 8), fill=(240, 148, 74))
        smoke_wisp(g, fx, 612, s_, color=(80, 56, 78), alpha=170, seed=int(fx))
    # 柵と松のシルエット
    palisade(g, 0, 700, 760, 0.9, col=(46, 36, 52), dark=(36, 28, 42), seed=43)
    palisade(g, 1240, 1920, 760, 0.9, col=(46, 36, 52), dark=(36, 28, 42), seed=44)
    tree(cv, 180, 1050, 1.3, kind="pine", leaf=(38, 32, 48), seed=45)
    tree(cv, 1740, 1040, 1.2, kind="pine", leaf=(38, 32, 48), seed=46)
    birds(g, [(600, 250), (720, 220), (680, 290), (1120, 240), (1220, 280)], 12,
          color=(40, 30, 44), width=4)
    reeds_fg(cv, 1080, seed=47, color=(36, 28, 42), n=36, s=1.05)


# ---------------------------------------------------------------- ポイント用タイムライン


def bg_timeline(cv):
    """ep03 用ポイント背景 — 平安のタイムライン."""
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
    labels = ["平安京", "蝦夷征討", "摂関政治", "国風文化"]
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
        g.text((nx, band_y + 118), labels[i], 27, (214, 224, 248), "bold", "mm")
    suzakumon(g, nodes[0], icon_y, 0.30, lit=False, seed=1)
    # 蝦夷征討: 城柵のミニ
    px = nodes[1]
    palisade(g, px - 78, px + 78, icon_y, 0.5, col=(96, 66, 48), dark=(70, 48, 36), seed=2)
    banner_pole(g, px - 66, icon_y - 4, 0.42, flag=P.SHU)
    torch(g, px + 62, icon_y - 2, 0.4)
    ox_cart(g, nodes[2], icon_y, 0.42, seed=3)
    emaki(g, nodes[3], icon_y - 66, 0.42, seed=4)
    gl = radial((int(1400 * cv.ss), int(900 * cv.ss)), (90, 120, 200),
                alpha_in=50, power=2.4)
    cv.img.alpha_composite(gl, (int(260 * cv.ss), int(160 * cv.ss)))

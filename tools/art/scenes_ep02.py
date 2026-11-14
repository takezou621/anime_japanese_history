"""ep02 シーン背景 (飛鳥・奈良) — script.json の background 名と 1:1 対応.

飛鳥=夕暮れの緑豊かな山裾 / 奈良=朱色基調の都 の空気感 (lead 指示)。
テキストは焼き込まない (editor の overlay_text が担当)。
"""
from __future__ import annotations

import math
import random

from artlib import palette as P
from artlib.canvas import (Canvas, blob_pts, dots_pattern, gradient, qbez,
                           radial, shade, speckle, tint, with_alpha)
from artlib.nature import (birds, cloud, clouds_row, forest_band, grass_tufts,
                           ground, light_shafts, moon, mountain_ridge, reeds_fg,
                           ridge, sky, stars, sun, tree)
from artlib.props import (banner_pole, boat, campfire, daibutsu, daigokuden,
                          deer, envoy_ship, grid_blocks, kondo, mansion, pagoda,
                          pit_house, rect, rice_paddy, smoke_wisp, suzakumon,
                          tile_roof_house, torch, warehouse)
from artlib.props import seedling

W, H = 1920, 1080

SKY_ASUKA_FIELD = [  # 飛鳥の田園 (夕方の低い陽)
    (0.00, (120, 150, 182)),
    (0.50, (206, 168, 148)),
    (1.00, (250, 222, 172)),
]
SKY_NARA_MILD = [  # 奈良後期 (やや曇り・ゆがみの予感)
    (0.00, (150, 168, 188)),
    (0.50, (198, 202, 198)),
    (1.00, (234, 224, 202)),
]
SKY_BATTLE = [  # 壬申の乱 (緊張の夕焼け)
    (0.00, (40, 30, 62)),
    (0.40, (122, 50, 72)),
    (0.70, (212, 92, 62)),
    (1.00, (244, 152, 92)),
]


def new_canvas():
    return Canvas(W, H, ss=2)


def _wall_band(g, x0, x1, y0, y1, wall=P.PLASTER, frame=P.VERMILION_WOOD,
               step=90, seed=0):
    """回廊の壁 (白壁+朱柱)."""
    rect(g, x0, y0, x1, y1, fill=wall, outline=shade(wall, 0.8), owidth=2.2)
    rnd = random.Random(seed)
    px = x0 + 10
    while px < x1 - 14:
        rect(g, px, y0, px + 11, y1, fill=frame)
        px += step + rnd.uniform(-6, 6)
    g.line([(x0, y0), (x1, y0)], shade(frame, 0.7), 4)


# ================================================================ 飛鳥


def bg_asuka_palace(cv):
    """飛鳥の宮殿 (蘇我氏風邸宅) — 夕暮れの山裾."""
    sky(cv, P.SKY_ASUKA_DUSK)
    g = cv.g()
    sun(g, 1520, 300, 78, color=(248, 190, 110), core=(254, 226, 168), halo=0.55)
    clouds_row(cv, 190, 3, 40, seed=4, base=(230, 156, 124), under=(128, 74, 88), alpha=225)
    mountain_ridge(cv, 480, 160, ((92, 86, 118), (158, 122, 122)), seed=6, freq=1.8)
    ridge(cv, 570, 80, (110, 132, 88), seed=8, freq=2.4)
    forest_band(cv, 655, 10, (0.6, 1.05), leaf=(104, 148, 96), seed=3)
    ground(cv, 665, (168, 172, 106), dark=(138, 142, 86), curve=16, seed=5,
           speckles=170, speckle_colors=[(148, 152, 94), (184, 188, 124)],
           speckle_r=(2, 5))
    # 丘の上の邸宅
    g.poly([(320, 860), (1560, 860), (1460, 740), (420, 740)], fill=(152, 162, 100))
    g.line([(420, 742), (1460, 742)], (128, 138, 82), 5)
    mansion(g, 850, 800, 1.15, seed=2)
    # 参道
    g.poly([(760, 1080), (1000, 1080), (930, 856), (860, 856)], fill=(204, 182, 140))
    g.line([(862, 858), (764, 1078)], (172, 152, 114), 4)
    g.line([(928, 858), (996, 1078)], (172, 152, 114), 4)
    tree(cv, 120, 1040, 1.6, kind="pine", leaf=(58, 108, 84), seed=9)
    tree(cv, 1810, 1000, 1.3, kind="oak", leaf=(112, 150, 92), seed=10)
    grass_tufts(g, (0, 700, W, 1080), 110, (136, 152, 88), seed=11)
    birds(g, [(420, 250), (530, 290), (490, 220)], 12, width=3.4)


def bg_asuka_court(cv):
    """朝廷 (大極殿風の正殿と回廊)."""
    sky(cv, P.SKY_ASUKA_DUSK)
    g = cv.g()
    sun(g, 300, 250, 64, color=(248, 198, 118), core=(254, 230, 176), halo=0.5)
    clouds_row(cv, 170, 3, 36, seed=7, base=(232, 164, 130), under=(130, 76, 90), alpha=220)
    mountain_ridge(cv, 430, 130, ((96, 90, 118), (164, 128, 126)), seed=5, freq=1.7)
    # 中庭 (白砂)
    sky_rect_grad = gradient((int(W * cv.ss), int((H - 620) * cv.ss)),
                             [(0, (216, 196, 168)), (1, (196, 178, 150))], "v")
    cv.img.alpha_composite(sky_rect_grad, (0, int(620 * cv.ss)))
    g.line([(0, 622), (W, 622)], (168, 150, 124), 4)
    speckle(g, (0, 640, W, 1080), 180, [(206, 188, 158), (182, 164, 136), (222, 206, 178)],
            r=(1.6, 4), seed=8)
    # 回廊 (左右)
    _wall_band(g, 60, 640, 700, 780, seed=3)
    _wall_band(g, 1280, 1860, 700, 780, seed=4)
    # 正殿
    daigokuden(g, 960, 880, 0.82, lit=True, seed=2)
    # 庭の旗
    banner_pole(g, 240, 990, 0.85)
    banner_pole(g, 1680, 990, 0.85)
    # 植え込みの松
    tree(cv, 90, 1020, 1.15, kind="pine", leaf=(58, 108, 84), seed=6)
    tree(cv, 1830, 1010, 1.05, kind="pine", leaf=(58, 108, 84), seed=7)
    # 光
    gl = radial((int(1300 * cv.ss), int(700 * cv.ss)), (255, 200, 130), alpha_in=60, power=2.4)
    cv.img.alpha_composite(gl, (int(300 * cv.ss), int(300 * cv.ss)))
    birds(g, [(1300, 220), (1400, 260), (1360, 190)], 12, width=3.2)


def bg_asuka_ship(cv):
    """遣隋使の出航と法隆寺 (岬の塔)."""
    sky(cv, P.SKY_ASUKA_DUSK)
    g = cv.g()
    sun(g, 1180, 240, 70, color=(248, 194, 112), core=(254, 230, 172), halo=0.55)
    clouds_row(cv, 170, 3, 38, seed=9, base=(228, 158, 126), under=(126, 74, 88), alpha=220)
    horizon = 560
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (108, 128, 168)), (0.35, (88, 108, 152)),
                         (0.75, (120, 104, 128)), (1, (160, 110, 100))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(3)
    for _ in range(26):
        yy = rnd.uniform(horizon + 10, H - 30)
        ln = rnd.uniform(30, 150)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((250, 220, 190), rnd.randint(50, 120)))
    # 太陽の反射帯
    for i in range(8):
        yy = horizon + 30 + i * 76
        ln = 240 - i * 18
        g.rrect((1180 - ln / 2 + math.sin(i * 2.1) * 56, yy,
                 1180 + ln / 2 + math.sin(i * 2.1) * 56, yy + 10), 5,
                fill=with_alpha((255, 220, 160), 100 - i * 9))
    # 岬の法隆寺 (五重塔)
    cape = ([(0, 1080), (0, 640)] + [(x, 640 - 90 * math.exp(-((x - 300) / 380.0) ** 2))
                                     for x in range(0, 900, 40)] + [(900, 700), (700, 1080)])
    g.poly(cape, fill=(120, 142, 92))
    g.line(cape[1:16], (98, 118, 74), 5)
    forest_band(cv, 700, 5, (0.5, 0.85), leaf=(90, 132, 84), seed=5)
    tree(cv, 560, 690, 0.9, kind="pine", leaf=(56, 104, 82), seed=8)
    pagoda(g, 250, 620, 0.86, seed=1)
    # 遣隋使船
    envoy_ship(g, 1380, 800, 1.15, figures=True, seed=2)
    envoy_ship(g, 1790, 690, 0.7, sails=1, flag=False, seed=3)
    birds(g, [(900, 300), (1000, 340), (960, 270), (620, 200)], 13, width=3.4)


def bg_asuka_gate(cv):
    """乙巳の変 (宮門・緊張の夕べ)."""
    sky(cv, P.SKY_SUNSET)
    g = cv.g()
    sun(g, 300, 330, 88, color=(240, 140, 80), core=(250, 190, 130), halo=0.6)
    clouds_row(cv, 200, 3, 42, seed=6, base=(190, 110, 96), under=(90, 50, 70), alpha=230)
    mountain_ridge(cv, 470, 120, ((70, 48, 78), (120, 70, 84)), seed=7, freq=1.7)
    # 宮城の塀 (朱)
    wall_y0, wall_y1 = 600, 726
    rect(g, 0, wall_y0, 1120, wall_y1, fill=P.VERMILION_WOOD,
         outline=shade(P.VERMILION_WOOD, 0.75), owidth=3)
    rect(g, 0, wall_y0 + 22, 1120, wall_y0 + 34, fill=shade(P.VERMILION_WOOD, 0.85))
    rnd = random.Random(2)
    px = 30
    while px < 1100:
        rect(g, px, wall_y0 + 40, px + 12, wall_y1, fill=shade(P.VERMILION_WOOD, 0.82))
        px += 88 + rnd.uniform(-8, 8)
    g.line([(0, wall_y0 + 6), (1120, wall_y0 + 6)], shade(P.VERMILION_WOOD, 1.25), 5)
    # 朱雀門
    suzakumon(g, 1400, 726, 0.95, lit=True, seed=3)
    # 塀の背後に宮殿の屋根
    rect(g, 180, wall_y0 - 84, 900, wall_y0 + 4, fill=shade(P.TILE, 0.9))
    rect(g, 160, wall_y0 - 70, 920, wall_y0 - 84, fill=shade(P.TILE, 1.06))
    # 松明
    for tx in (380, 700, 1020):
        torch(g, tx, 800, 1.05)
    # 地面 (手前)
    rect(g, 0, 726, W, H, fill=(88, 66, 72))
    speckle(g, (0, 740, W, 1080), 150, [(76, 56, 64), (104, 78, 82), (118, 88, 86)],
            r=(2, 6), seed=4)
    # 遠くの火と煙
    g.poly(qbez((640, 690), (636, 660), (648, 640), 8)
           + qbez((648, 640), (656, 660), (660, 690), 8), fill=(244, 150, 70))
    smoke_wisp(g, 650, 620, 0.9, color=(92, 66, 84), alpha=170, seed=5)
    # 舞い落ちる葉
    rnd2 = random.Random(8)
    for _ in range(20):
        fx, fy = rnd2.uniform(0, W), rnd2.uniform(180, 1000)
        s2 = rnd2.uniform(4, 8)
        g.poly([(fx, fy - s2), (fx + s2, fy), (fx, fy + s2), (fx - s2, fy)],
               fill=rnd2.choice([(214, 120, 60), (238, 160, 80)]))
    birds(g, [(500, 260), (620, 230), (580, 300), (900, 240), (1000, 280)], 12,
          color=(48, 36, 50), width=4)
    reeds_fg(cv, 1080, seed=9, color=(44, 34, 46), n=34, s=1.05)


def bg_asuka_field(cv):
    """大化の改新後の田園 (公地公民・班田)."""
    sky(cv, SKY_ASUKA_FIELD)
    g = cv.g()
    sun(g, 1540, 260, 60, color=(248, 200, 120), core=(254, 232, 180), halo=0.45)
    clouds_row(cv, 170, 3, 36, seed=8, base=(238, 186, 150), under=(150, 110, 110), alpha=220)
    mountain_ridge(cv, 470, 150, ((104, 100, 118), (170, 140, 128)), seed=6, freq=1.8)
    ridge(cv, 570, 70, (118, 138, 90), seed=9, freq=2.5)
    forest_band(cv, 648, 10, (0.6, 1.0), leaf=(106, 148, 94), seed=4)
    ground(cv, 655, (172, 172, 106), dark=(140, 140, 86), curve=14, seed=6,
           speckles=160, speckle_colors=[(152, 152, 94), (186, 186, 122)],
           speckle_r=(2, 5))
    # 条里風の区画田
    for r in range(3):
        for c in range(6):
            x0, y0 = 660 + c * 210, 690 + r * 90
            rect(g, x0, y0, x0 + 190, y0 + 76, fill=(190, 196, 128) if (r + c) % 2 else (178, 186, 118))
            g.line([(x0, y0 + 76), (x0 + 190, y0 + 76)], (146, 150, 96), 3)
    # 水田帯 (手前)
    rice_paddy(cv, 950, 1080, [(210, 226, 234), (170, 208, 228)], seed=11, rows_seed=4)
    # 村 (左)
    tile_roof_house(g, 300, 780, 0.95, seed=1)
    warehouse(g, 480, 760, 0.55, ladder=False, seed=2)
    tile_roof_house(g, 130, 850, 0.7, seed=3)
    grass_tufts(g, (0, 700, 660, 1000), 80, (140, 152, 92), seed=12)
    # 畦道
    g.poly([(540, 1080), (660, 1080), (600, 700), (560, 700)], fill=(204, 184, 142))
    birds(g, [(900, 230), (1000, 270), (960, 200)], 12, width=3.2)


def bg_asuka_battle(cv):
    """壬申の乱 (両軍対峙の緊張)."""
    sky(cv, SKY_BATTLE)
    g = cv.g()
    clouds_row(cv, 180, 3, 44, seed=3, base=(150, 80, 90), under=(60, 36, 58), alpha=235)
    # 左右の山 (陣営)
    g.poly([(0, 1080), (0, 560)] + [(x, 560 + 70 * math.sin(x * 0.004))
                                    for x in range(0, 961, 60)] + [(960, 640), (960, 1080)],
           fill=(66, 58, 74))
    g.poly([(960, 1080), (960, 640)] + [(x, 620 + 60 * math.sin(x * 0.005 + 2))
                                        for x in range(960, 1921, 60)] + [(1920, 560), (1920, 1080)],
           fill=(78, 56, 68))
    # 谷間
    rect(g, 0, 640, W, H, fill=(56, 46, 60))
    speckle(g, (0, 660, W, 1080), 160, [(48, 40, 54), (66, 54, 66), (80, 62, 68)],
            r=(2, 6), seed=5)
    # 左陣営 (青旗) / 右陣営 (朱旗)
    for i in range(4):
        banner_pole(g, 150 + i * 130, 610 + (i % 2) * 20, 0.62, flag=(70, 96, 160))
        banner_pole(g, 1300 + i * 130, 600 + (i % 2) * 20, 0.62, flag=P.SHU)
    for tx in (240, 460, 1360, 1600):
        torch(g, tx, 660, 0.9)
    campfire(g, 350, 700, 0.7, glow=False, seed=6)
    campfire(g, 1500, 690, 0.7, glow=False, seed=7)
    # 煙柱
    smoke_wisp(g, 350, 600, 1.1, color=(60, 48, 66), alpha=180, seed=8)
    smoke_wisp(g, 1500, 590, 1.1, color=(70, 48, 62), alpha=180, seed=9)
    # 中央の谷に並ぶ槍のシルエット
    rnd = random.Random(10)
    for _ in range(26):
        sx = rnd.uniform(760, 1160)
        sy = rnd.uniform(950, 1040)
        h = rnd.uniform(60, 110)
        g.line([(sx, sy), (sx + rnd.uniform(-14, 14), sy - h)], (34, 28, 40),
               rnd.uniform(2.2, 3.6))
    birds(g, [(700, 240), (820, 200), (780, 280), (1080, 230), (1180, 270)], 12,
          color=(36, 28, 40), width=4)
    reeds_fg(cv, 1080, seed=11, color=(32, 26, 36), n=40, s=1.1)


# ================================================================ 奈良


def bg_nara_map(cv):
    """平城京の俯瞰図 (碁盤目+宮域+朱雀大路)."""
    # 羊皮紙風の地肌
    cv.img.alpha_composite(gradient(cv.img.size, [(0, (240, 232, 210)), (1, (226, 216, 190))], "v"))
    g = cv.g()
    speckle(g, (0, 0, W, H), 260, [(218, 208, 184), (234, 226, 202), (208, 198, 174)],
            r=(2, 7), seed=1)
    # 周縁の山々
    for (cx0, cy0, rx, ry, c) in [(140, 110, 220, 70, (110, 138, 96)),
                                  (520, 80, 260, 60, (100, 130, 90)),
                                  (1500, 90, 300, 66, (110, 138, 96)),
                                  (1830, 140, 220, 80, (100, 130, 90)),
                                  (90, 990, 200, 60, (110, 138, 96)),
                                  (1840, 1010, 200, 60, (110, 138, 96))]:
        g.poly(blob_pts(cx0, cy0, rx, ry, seed=int(cx0), wobble=0.18), fill=c,
               outline=shade(c, 0.82), owidth=3)
    # 碁盤目区画
    grid_blocks(cv, 180, 1020, cols=10, seed=4)
    # 朱雀大路 (中央の広い道)
    rect(g, 900, 300, 1020, 1020, fill=(236, 230, 212))
    g.line([(906, 310), (906, 1016)], (208, 198, 172), 3)
    g.line([(1014, 310), (1014, 1016)], (208, 198, 172), 3)
    # 宮域 (上中央)
    rect(g, 660, 120, 1260, 300, fill=(196, 120, 96), outline=(150, 84, 66), owidth=4)
    for gx in range(700, 1261, 80):
        rect(g, gx, 126, gx + 10, 294, fill=(168, 96, 76))
    rect(g, 666, 126, 1254, 134, fill=(172, 100, 80))
    # 宮内の殿舎
    daigokuden(g, 960, 280, 0.3, lit=False, seed=2)
    rect(g, 720, 240, 820, 288, fill=(188, 160, 120), outline=(150, 124, 92), owidth=2.4)
    rect(g, 1100, 240, 1200, 288, fill=(188, 160, 120), outline=(150, 124, 92), owidth=2.4)
    g.poly([(726, 240), (814, 240), (770, 214)], fill=P.TILE)
    g.poly([(1106, 240), (1194, 240), (1150, 214)], fill=P.TILE)
    # 朱雀門 (宮域南門)
    suzakumon(g, 960, 306, 0.24, lit=False, seed=3)
    # 羅城門 (大路の南端)
    suzakumon(g, 960, 1030, 0.3, lit=False, seed=4)
    # 東西市の目印
    g.circle(430, 660, 26, fill=(214, 176, 108), outline=(168, 132, 84), owidth=3)
    g.circle(1490, 660, 26, fill=(214, 176, 108), outline=(168, 132, 84), owidth=3)
    g.line([(430 - 14, 660), (430 + 14, 660)], (150, 116, 74), 3)
    g.line([(1490 - 14, 660), (1490 + 14, 660)], (150, 116, 74), 3)
    # 縁飾り (地図フレーム)
    g.rrect((14, 14, W - 14, H - 14), 18, outline=(150, 120, 88), owidth=8)


def bg_nara_ship(cv):
    """遣唐使の船団."""
    sky(cv, P.SKY_NARA_DAY)
    g = cv.g()
    sun(g, 1220, 190, 64, color=(250, 216, 150), core=(254, 238, 192), halo=0.55)
    clouds_row(cv, 160, 3, 36, seed=10)
    horizon = 430
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (136, 186, 212)), (0.4, (94, 154, 198)), (1, (62, 122, 172))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(6)
    for _ in range(30):
        yy = rnd.uniform(horizon + 10, H - 20)
        ln = rnd.uniform(30, 160)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((240, 250, 255), rnd.randint(50, 130)))
    for i in range(7):
        yy = horizon + 24 + i * 82
        ln = 220 - i * 18
        g.rrect((1220 - ln / 2 + math.sin(i * 2.3) * 60, yy,
                 1220 + ln / 2 + math.sin(i * 2.3) * 60, yy + 10), 5,
                fill=with_alpha((255, 234, 170), 105 - i * 10))
    # 遠くの大陸海岸線
    g.poly([(W, 430), (W, 340)] + [(x, 340 + 40 * math.sin(x * 0.006))
                                   for x in range(1920, 1300, -60)] + [(1300, 428)], fill=(150, 168, 148))
    # 船団
    envoy_ship(g, 520, 800, 1.1, figures=True, seed=1)
    envoy_ship(g, 1260, 890, 1.3, figures=True, seed=2)
    envoy_ship(g, 1700, 660, 0.75, sails=1, seed=3)
    birds(g, [(380, 300), (500, 340), (460, 270), (1500, 250), (1600, 290)], 13, width=3.4)


def bg_nara_capital(cv):
    """平城京・朱雀大路 (遷都)."""
    sky(cv, P.SKY_NARA_DAY)
    g = cv.g()
    sun(g, 1480, 170, 56, halo=0.45)
    clouds_row(cv, 140, 3, 34, seed=12)
    # 遠景の山と地平
    ridge(cv, 520, 46, (168, 178, 156), seed=8, freq=2.2)
    horizon = 545
    road_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                         [(0, (234, 224, 198)), (1, (206, 196, 168))], "v")
    cv.img.alpha_composite(road_grad, (0, int(horizon * cv.ss)))
    g.line([(0, horizon), (W, horizon)], (192, 182, 156), 4)
    # 朱雀大路 (遠近)
    g.poly([(760, 1080), (1160, 1080), (1008, 548), (912, 548)], fill=(228, 218, 190))
    g.line([(913, 550), (766, 1078)], (198, 188, 160), 5)
    g.line([(1007, 550), (1154, 1078)], (198, 188, 160), 5)
    g.line([(960, 560), (960, 1076)], with_alpha((208, 198, 170), 150), 8)
    g.line([(878, 700), (826, 1070)], with_alpha((198, 186, 158), 140), 4)
    g.line([(1042, 700), (1094, 1070)], with_alpha((198, 186, 158), 140), 4)
    # 宅地 (奥から手前へ)
    far_first = sorted(
        [(150, 940, 1.35), (350, 855, 1.12), (520, 790, 0.95), (660, 745, 0.8),
         (780, 706, 0.66), (1770, 930, 1.3), (1580, 848, 1.1), (1420, 786, 0.92),
         (1280, 742, 0.78), (1160, 704, 0.64)], key=lambda t: t[1])
    for i, (hx, hy, hs) in enumerate(far_first):
        tile_roof_house(g, hx, hy, hs, seed=i)
        wy = hy + 8 * hs
        if hx < 960:
            rect(g, hx + 96 * hs, wy - 32 * hs, hx + 158 * hs, wy, fill=(206, 190, 160),
                 outline=(178, 162, 132), owidth=2)
        else:
            rect(g, hx - 158 * hs, wy - 32 * hs, hx - 96 * hs, wy, fill=(206, 190, 160),
                 outline=(178, 162, 132), owidth=2)
    # 大路の先に朱雀門
    suzakumon(g, 960, 588, 0.56, lit=True, seed=5)
    # 地平の霞
    g.ellipse((-100, 548, W + 100, 600), fill=with_alpha((240, 232, 210), 110))
    # 手前の石敷き
    speckle(g, (760, 1000, 1160, 1080), 60, [(198, 188, 160), (216, 206, 180)],
            r=(1.6, 3.6), seed=13)
    birds(g, [(400, 220), (500, 260), (460, 190)], 12, width=3.2)


def bg_nara_temple(cv):
    """奈良の大寺 (塔+金堂)."""
    sky(cv, P.SKY_NARA_DAY)
    g = cv.g()
    sun(g, 300, 190, 56, halo=0.45)
    clouds_row(cv, 160, 3, 34, seed=14)
    mountain_ridge(cv, 500, 130, ((104, 140, 128), (164, 186, 158)), seed=9, freq=1.9)
    ridge(cv, 580, 60, (124, 154, 112), seed=10, freq=2.5)
    ground(cv, 660, (186, 184, 128), dark=(154, 152, 104), curve=14, seed=11,
           speckles=150, speckle_colors=[(166, 164, 112), (200, 198, 142)],
           speckle_r=(2, 5))
    # 寺の基壇
    g.rrect((260, 830, 1660, 920), 12, fill=(198, 190, 172), outline=(160, 152, 134), owidth=4)
    g.poly([(880, 920), (1040, 920), (1010, 830), (910, 830)], fill=(222, 214, 196))
    for k in range(1, 5):
        g.line([(920 + k * 6, 920 - k * 18), (1000 - k * 6, 920 - k * 18)],
               (196, 188, 170), 3)
    # 金堂と五重塔
    kondo(g, 1080, 838, 0.78, seed=1)
    pagoda(g, 560, 838, 0.72, seed=2)
    # 中門と回廊の一部
    rect(g, 760, 880, 880, 920, fill=P.VERMILION_WOOD, outline=shade(P.VERMILION_WOOD, 0.75), owidth=2.4)
    rect(g, 1060, 880, 1180, 920, fill=P.VERMILION_WOOD, outline=shade(P.VERMILION_WOOD, 0.75), owidth=2.4)
    # 樹木
    tree(cv, 180, 1000, 1.3, kind="pine", leaf=(60, 112, 88), seed=3)
    tree(cv, 1740, 990, 1.2, kind="pine", leaf=(60, 112, 88), seed=4)
    tree(cv, 1330, 940, 0.8, kind="oak", leaf=(112, 152, 96), seed=5)
    grass_tufts(g, (0, 690, W, 1070), 90, (150, 152, 100), seed=15)
    birds(g, [(1400, 230), (1500, 270), (1460, 200)], 12, width=3.2)


def bg_nara_field(cv):
    """奈良後期の田園 (ゆがみの予感)."""
    sky(cv, SKY_NARA_MILD)
    g = cv.g()
    clouds_row(cv, 180, 3, 40, seed=16, base=(216, 214, 208), under=(160, 158, 154), alpha=230)
    mountain_ridge(cv, 480, 130, ((110, 130, 130), (168, 180, 160)), seed=12, freq=1.9)
    forest_band(cv, 650, 10, (0.6, 1.0), leaf=(100, 138, 96), seed=6)
    ground(cv, 655, (168, 170, 110), dark=(138, 140, 90), curve=14, seed=13,
           speckles=160, speckle_colors=[(150, 152, 98), (184, 186, 124)],
           speckle_r=(2, 5))
    # 税を運ぶ倉 (正倉風の高床)
    warehouse(g, 1460, 720, 0.8, seed=2)
    tile_roof_house(g, 1700, 760, 0.75, seed=3)
    # 水田
    rice_paddy(cv, 860, 1080, [(202, 216, 222), (164, 196, 210)], seed=14, rows_seed=6)
    # 村
    tile_roof_house(g, 330, 830, 1.0, seed=4)
    tile_roof_house(g, 560, 790, 0.8, seed=5)
    # 道と行き交う荷車の轍
    g.poly([(700, 1080), (830, 1080), (760, 700), (726, 700)], fill=(198, 184, 150))
    g.line([(728, 702), (702, 1078)], (170, 156, 124), 3)
    g.line([(758, 702), (828, 1078)], (170, 156, 124), 3)
    tree(cv, 100, 1030, 1.2, kind="pine", leaf=(56, 100, 82), seed=7)
    grass_tufts(g, (0, 700, 900, 1060), 80, (136, 148, 92), seed=17)
    birds(g, [(1100, 230), (1200, 260), (1160, 200)], 12, color=(80, 76, 80), width=3.2)
    # どんよりとした光
    vig = radial((int(W * cv.ss), int(H * cv.ss)), (70, 74, 90), alpha_in=60, power=2.6)
    cv.img.alpha_composite(vig)

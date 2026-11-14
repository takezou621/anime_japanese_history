"""ep05 シーン背景 (室町) — script.json の background 名と 1:1 対応.

配色の物語 (writer メモ): 金閣=山吹金色の華麗さ → 応仁の乱=灰の焼け野原 →
銀閣=銀色のひなびた東山文化。テキストは焼き込まない。
"""
from __future__ import annotations

import math
import random

from artlib import palette as P
from artlib.canvas import (Canvas, blob_pts, dots_pattern, gradient, qbez,
                           radial, shade, speckle, tint, with_alpha)
from artlib.nature import (birds, cloud, clouds_row, forest_band, grass_tufts,
                           ground, mountain_ridge, reeds_fg, ridge, sky, stars,
                           sun, tree)
from artlib.props import (amida, banner_pole, campfire, daigokuden, ginkaku,
                          kango_ship, kabuto, kamakura_goten, kinkaku, mongol_ship,
                          mountain_fort, nobori, ox_cart, samurai_rider,
                          smoke_wisp, suzakumon, tile_roof_house, torch,
                          two_court_flags, war_boat)
from artlib.props import palisade, rice_paddy, seedling, rect
from scenes_ep01 import bow_and_arrows

W, H = 1920, 1080


def new_canvas():
    return Canvas(W, H, ss=2)


def _ash_sky(cv):
    """応仁の乱の灰の空."""
    sky(cv, [(0.00, (98, 100, 104)), (0.45, (150, 150, 150)), (1.00, (196, 194, 188))])


def _wall_band(g, x0, x1, y0, y1, wall=P.PLASTER, frame=P.VERMILION_WOOD,
               step=90, seed=0):
    rect(g, x0, y0, x1, y1, fill=wall, outline=shade(wall, 0.8), owidth=2.2)
    rnd = random.Random(seed)
    px = x0 + 10
    while px < x1 - 14:
        rect(g, px, y0, px + 11, y1, fill=frame)
        px += step + rnd.uniform(-6, 6)


# ---------------------------------------------------------------- 幕府の興亡


def bg_muromachi_kamakura_fall(cv):
    """鎌倉陥落 (1333・燃える切通しの谷)."""
    sky(cv, P.SKY_SUNSET)
    g = cv.g()
    clouds_row(cv, 190, 3, 44, seed=2, base=(178, 100, 96), under=(84, 50, 74), alpha=230)
    # 切通しの山 (両側)
    g.poly([(0, 1080), (0, 250)] + [(x, 250 + 60 * math.sin(x * 0.004))
                                    for x in range(0, 601, 50)] + [(600, 370), (600, 1080)],
           fill=(96, 66, 72))
    g.poly([(W, 1080), (W, 230)] + [(x, 230 + 60 * math.sin(x * 0.004 + 1.5))
                                    for x in range(1920, 1320, -50)] + [(1320, 360), (1320, 1080)],
           fill=(92, 62, 68))
    ground(cv, 540, (118, 92, 88), dark=(94, 74, 70), curve=12, seed=3,
           speckles=140, speckle_colors=[(102, 80, 78), (134, 106, 100)],
           speckle_r=(2, 5))
    # 燃える町並み
    for (hx, hy, hs) in [(300, 660, 0.8), (700, 640, 0.7), (1120, 655, 0.75),
                         (1520, 670, 0.8)]:
        tile_roof_house(g, hx, hy, hs, seed=int(hx))
        campfire(g, hx + 60 * hs, hy + 8, 0.8 * hs, stones=False, seed=int(hx))
        smoke_wisp(g, hx + 60 * hs, hy - 90 * hs, 1.2 * hs, color=(70, 56, 70),
                   alpha=190, seed=int(hx))
    # 突入する騎馬武士
    samurai_rider(g, 880, 950, 0.85, flip=-1)
    samurai_rider(g, 1160, 990, 0.7, banner=False, flip=-1, seed=5)
    reeds_fg(cv, 1080, seed=6, color=(44, 34, 48), n=34, s=1.05)
    birds(g, [(600, 220), (720, 190), (680, 270)], 11, color=(44, 34, 48), width=4)


def bg_muromachi_newgov(cv):
    """建武の新政 (期待に満ちた朝の宮中)."""
    sky(cv, [(0.00, (140, 190, 220)), (0.55, (190, 216, 232)), (1.00, (250, 242, 222))])
    g = cv.g()
    sun(g, 300, 190, 56, halo=0.45)
    clouds_row(cv, 150, 3, 32, seed=7)
    mountain_ridge(cv, 440, 110, ((112, 140, 132), (172, 190, 168)), seed=8, freq=1.9)
    sand = gradient((int(W * cv.ss), int((H - 600) * cv.ss)),
                    [(0, (238, 236, 226)), (1, (216, 214, 202))], "v")
    cv.img.alpha_composite(sand, (0, int(600 * cv.ss)))
    g.line([(0, 602), (W, 602)], (188, 186, 172), 4)
    speckle(g, (0, 620, W, 1080), 190, [(226, 224, 212), (204, 202, 190)], r=(1.6, 3.6), seed=9)
    daigokuden(g, 960, 900, 0.8, roof=(118, 132, 100), roof_d=(92, 106, 80),
               lit=False, seed=2)
    _wall_band(g, 60, 600, 740, 830, seed=3)
    _wall_band(g, 1320, 1860, 740, 830, seed=4)
    banner_pole(g, 240, 1000, 0.85, flag=(238, 238, 236))
    banner_pole(g, 1680, 1000, 0.85, flag=(238, 238, 236))
    tree(cv, 100, 1030, 1.2, kind="pine", leaf=(60, 112, 88), seed=5)
    tree(cv, 1830, 1020, 1.15, kind="pine", leaf=(60, 112, 88), seed=6)
    birds(g, [(1240, 230), (1340, 270), (1300, 200)], 12, width=3.2)


def bg_muromachi_takauji(cv):
    """尊氏の挙兵 (西上する軍勢と旗指物)."""
    sky(cv, [(0.00, (96, 100, 140)), (0.5, (170, 130, 140)), (1.00, (238, 178, 130))])
    g = cv.g()
    clouds_row(cv, 170, 3, 42, seed=10, base=(206, 150, 136), under=(110, 74, 92), alpha=225)
    mountain_ridge(cv, 440, 120, ((88, 78, 106), (148, 114, 124)), seed=11, freq=1.7)
    ground(cv, 620, (166, 150, 112), dark=(136, 124, 92), curve=12, seed=12,
           speckles=150, speckle_colors=[(146, 134, 98), (180, 166, 126)],
           speckle_r=(2, 5))
    # 旗指物の列 (藍・白)
    for i in range(6):
        nobori(g, 240 + i * 150, 730 + (i % 2) * 16, 0.78,
               col=(90, 110, 170) if i % 2 else (238, 238, 236), seed=13 + i)
    # 進軍する騎馬
    for i in range(4):
        samurai_rider(g, 900 + i * 220, 930 - i * 30, 0.66 - i * 0.055,
                      banner=False, flip=-1, seed=14 + i)
    _dust(g, (700, 0, 1500, 1050), 20, seed=15)
    reeds_fg(cv, 1080, seed=16, color=(60, 50, 60), n=30, s=1.0)
    birds(g, [(820, 220), (920, 260), (880, 190)], 11, width=3.4)


def _dust(g, box, n, seed=0, color=(188, 174, 148), alpha=110):
    rnd = random.Random(seed)
    for _ in range(n):
        px = rnd.uniform(box[0], box[2])
        py = rnd.uniform(box[1], box[3])
        r_ = rnd.uniform(20, 70)
        g.ellipse((px - r_, py - r_ * 0.4, px + r_, py + r_ * 0.4),
                  fill=with_alpha(color, rnd.randint(40, alpha)))


def bg_muromachi_namboku(cv):
    """南北朝の動乱 (二つの朝廷)."""
    sky(cv, [(0.00, (96, 96, 140)), (0.5, (172, 130, 138)), (1.00, (234, 176, 134))])
    g = cv.g()
    clouds_row(cv, 180, 3, 44, seed=17, base=(198, 140, 134), under=(104, 66, 88), alpha=225)
    # 左の山 (北朝の金) / 右の山 (南朝の紫)
    g.poly([(0, 1080), (0, 560)] + [(x, 560 + 64 * math.sin(x * 0.004))
                                    for x in range(0, 961, 60)] + [(960, 630), (960, 1080)],
           fill=(120, 132, 96))
    g.poly([(960, 1080), (960, 630)] + [(x, 610 + 58 * math.sin(x * 0.005 + 2))
                                        for x in range(960, 1921, 60)] + [(1920, 570), (1920, 1080)],
           fill=(126, 112, 142))
    rect(g, 0, 630, W, H, fill=(104, 96, 96))
    speckle(g, (0, 650, W, 1080), 150, [(92, 84, 88), (118, 108, 108)], r=(2, 6), seed=18)
    two_court_flags(g, 420, 660, 0.85)
    two_court_flags(g, 1500, 640, 0.85)
    # 荒れた谷
    campfire(g, 960, 1000, 0.85, seed=19)
    smoke_wisp(g, 980, 880, 1.3, color=(70, 62, 72), alpha=180, seed=20)
    _dust(g, (700, 0, 1300, 1060), 14, seed=21)
    birds(g, [(840, 240), (960, 210), (920, 280)], 11, color=(42, 36, 48), width=4)


# ---------------------------------------------------------------- 義満の栄華


def bg_muromachi_yoshimitsu(cv):
    """花の御所 (義満の栄華・金の官殿)."""
    sky(cv, [(0.00, (128, 184, 218)), (0.55, (184, 210, 230)), (1.00, (248, 234, 204))])
    g = cv.g()
    sun(g, 1440, 180, 56, halo=0.45)
    clouds_row(cv, 140, 3, 32, seed=22)
    mountain_ridge(cv, 430, 110, ((110, 140, 130), (170, 188, 164)), seed=23, freq=1.8)
    sand = gradient((int(W * cv.ss), int((H - 580) * cv.ss)),
                    [(0, (236, 228, 206)), (1, (212, 202, 176))], "v")
    cv.img.alpha_composite(sand, (0, int(580 * cv.ss)))
    g.line([(0, 582), (W, 582)], (184, 176, 152), 4)
    speckle(g, (0, 600, W, 1080), 180, [(226, 218, 196), (200, 192, 170)], r=(1.6, 4), seed=24)
    # 金の棟飾りを添えた官殿
    daigokuden(g, 960, 900, 0.85, roof=(96, 104, 92), roof_d=(74, 82, 72), lit=True, seed=2)
    g.rrect((890, 900 - 0.85 * 288, 1030, 900 - 0.85 * 268), 6, fill=P.GOLD_LEAF,
            outline=shade(P.GOLD_LEAF, 0.72), owidth=2.4)
    _wall_band(g, 40, 560, 740, 840, seed=3)
    _wall_band(g, 1360, 1880, 740, 840, seed=4)
    nobori(g, 250, 1010, 0.85, col=P.GOLD_LEAF)
    nobori(g, 1670, 1010, 0.85, col=P.GOLD_LEAF)
    tree(cv, 100, 1030, 1.2, kind="pine", leaf=(60, 112, 88), seed=5)
    tree(cv, 1830, 1020, 1.1, kind="pine", leaf=(60, 112, 88), seed=6)
    birds(g, [(1240, 230), (1340, 270), (1300, 200)], 12, width=3.2)


def bg_muromachi_ship(cv):
    """勘合船 (日明貿易の大船団)."""
    sky(cv, [(0.00, (128, 186, 218)), (0.55, (184, 212, 232)), (1.00, (248, 236, 210))])
    g = cv.g()
    sun(g, 1240, 190, 60, halo=0.5)
    clouds_row(cv, 160, 3, 34, seed=25)
    horizon = 420
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (140, 190, 214)), (0.4, (98, 158, 202)), (1, (66, 126, 176))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(26)
    for _ in range(28):
        yy = rnd.uniform(horizon + 10, H - 20)
        ln = rnd.uniform(30, 150)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((240, 250, 255), rnd.randint(50, 130)))
    kango_ship(g, 620, 780, 0.85, seed=1)
    kango_ship(g, 1440, 890, 1.1, seed=2)
    birds(g, [(900, 280), (1000, 320), (960, 250)], 12, width=3.4)


def bg_muromachi_kinkaku(cv):
    """金閣寺 (山吹金色の楼閣と池の映影)."""
    sky(cv, [(0.00, (250, 214, 150)), (0.45, (246, 190, 130)), (1.00, (250, 226, 186))])
    g = cv.g()
    sun(g, 1450, 230, 62, color=(250, 186, 110), core=(254, 226, 170), halo=0.5)
    clouds_row(cv, 150, 2, 30, seed=27, base=(250, 210, 160), under=(196, 140, 110), alpha=210)
    mountain_ridge(cv, 430, 120, ((104, 138, 122), (170, 190, 158)), seed=28, freq=1.8)
    forest_band(cv, 560, 9, (0.5, 0.95), leaf=(96, 140, 98), seed=29)
    ground(cv, 640, (184, 180, 130), dark=(152, 148, 104), curve=12, seed=30,
           speckles=140, speckle_colors=[(164, 160, 112), (198, 194, 144)],
           speckle_r=(2, 5))
    # 鏡湖池
    pond_y = 940
    g.ellipse((240, pond_y - 110, 1680, pond_y + 130), fill=(120, 168, 196),
              outline=(88, 132, 162), owidth=4)
    for _ in range(10):
        rx = random.Random(int(_ * 13)).uniform(380, 1500)
        ry = pond_y - 60 + random.Random(int(rx)).uniform(-40, 90)
        g.rrect((rx, ry, rx + random.Random(int(ry)).uniform(50, 120), ry + 4), 2,
                fill=with_alpha((244, 226, 170), 90))
    # 中島に金閣
    g.ellipse((640, pond_y - 14, 1280, pond_y + 70), fill=(206, 202, 186),
              outline=(172, 168, 152), owidth=3)
    kinkaku(g, 960, pond_y + 22, 1.45, seed=2)
    # 松
    tree(cv, 240, 1010, 1.35, kind="pine", leaf=(60, 112, 88), seed=3)
    tree(cv, 1680, 1000, 1.3, kind="pine", leaf=(60, 112, 88), seed=4)
    grass_tufts(g, (0, 680, W, 1070), 80, (156, 152, 104), seed=31)
    birds(g, [(500, 240), (600, 280), (560, 210)], 12, width=3.2)


# ---------------------------------------------------------------- 乱と下剋上


def bg_muromachi_onin(cv):
    """応仁の乱 (灰の焼け野原・11年の戦火)."""
    _ash_sky(cv)
    g = cv.g()
    clouds_row(cv, 190, 3, 46, seed=32, base=(126, 126, 126), under=(88, 88, 88), alpha=235)
    mountain_ridge(cv, 470, 110, ((86, 88, 90), (128, 128, 126)), seed=33, freq=1.7)
    ground(cv, 630, (146, 144, 140), dark=(120, 118, 116), curve=12, seed=34,
           speckles=170, speckle_colors=[(126, 124, 122), (162, 160, 156)],
           speckle_r=(2, 5))
    # 焼け残った屋根のシルエット
    rnd = random.Random(35)
    x = 0
    while x < W:
        hw = rnd.uniform(110, 190)
        hh = rnd.uniform(36, 74)
        rect(g, x, 660 - hh, x + hw, 700, fill=(108, 104, 100))
        g.poly([(x - 8, 660 - hh), (x + hw + 8, 660 - hh), (x + hw * 0.7, 660 - hh - 26),
                (x + hw * 0.3, 660 - hh - 26)], fill=(94, 90, 86))
        x += hw + rnd.uniform(14, 54)
    rect(g, 0, 696, W, H, fill=(120, 118, 116))
    speckle(g, (0, 706, W, 1080), 150, [(106, 104, 102), (134, 132, 130)], r=(2, 6), seed=36)
    # 名残の火と灰の煙
    for (fx, s_) in [(560, 0.9), (1180, 1.0)]:
        campfire(g, fx, 700, s_, stones=False, seed=int(fx))
        smoke_wisp(g, fx + 10, 560, 1.5, color=(110, 108, 108), alpha=180, seed=int(fx))
    palisade(g, 0, 660, 750, 0.85, col=(96, 94, 92), dark=(72, 70, 68), seed=37)
    palisade(g, 1260, 1920, 750, 0.85, col=(96, 94, 92), dark=(72, 70, 68), seed=38)
    tree(cv, 200, 1050, 1.2, kind="pine", leaf=(74, 76, 72), seed=39)
    tree(cv, 1720, 1040, 1.15, kind="pine", leaf=(74, 76, 72), seed=40)
    reeds_fg(cv, 1080, seed=41, color=(74, 72, 70), n=34, s=1.0)
    birds(g, [(620, 240), (740, 210), (700, 280)], 11, color=(56, 54, 56), width=4)


def bg_muromachi_domain(cv):
    """守護の領国 (在地の館と旗)."""
    sky(cv, P.SKY_KAMAKURA_DAY)
    g = cv.g()
    sun(g, 360, 190, 54, halo=0.45)
    clouds_row(cv, 150, 3, 32, seed=42)
    mountain_ridge(cv, 440, 130, ((104, 134, 128), (168, 188, 164)), seed=43, freq=1.8)
    ground(cv, 620, (176, 172, 118), dark=(144, 140, 96), curve=14, seed=44,
           speckles=150, speckle_colors=[(156, 152, 104), (190, 186, 132)],
           speckle_r=(2, 5))
    # 領国の館 (小さな御所風)
    kamakura_goten(g, 1280, 720, 0.78, seed=2)
    nobori(g, 1120, 740, 0.8, col=(90, 110, 170))
    # 村と田
    tile_roof_house(g, 320, 800, 0.95, seed=3)
    tile_roof_house(g, 540, 762, 0.75, seed=4)
    rice = [(0, 900), (1920, 900)]
    for k in range(4):
        rect(g, 80 + k * 440, 890, 80 + k * 440 + 400, 1010,
             fill=(186, 192, 128) if k % 2 else (174, 180, 118))
        g.line([(80 + k * 440, 1010), (80 + k * 440 + 400, 1010)], (146, 150, 96), 4)
    grass_tufts(g, (0, 680, 900, 880), 70, (146, 148, 98), seed=45)
    g.poly([(1000, 1080), (1120, 1080), (1050, 720), (1010, 720)], fill=(204, 190, 152))
    birds(g, [(800, 230), (900, 270), (860, 200)], 12, width=3.2)


def bg_muromachi_gekokujo(cv):
    """下剋上 (主を討つ山城の夜)."""
    sky(cv, [(0.00, (44, 36, 66)), (0.5, (96, 66, 96)), (1.00, (170, 96, 100))])
    g = cv.g()
    stars(g, (40, 40, 1880, 360), 50, seed=46)
    mountain_ridge(cv, 430, 110, ((44, 36, 62), (84, 58, 82)), seed=47, freq=1.7)
    ground(cv, 620, (92, 74, 88), dark=(74, 60, 72), curve=12, seed=48,
           speckles=140, speckle_colors=[(80, 64, 78), (104, 84, 96)],
           speckle_r=(2, 5))
    # 主の山城 (旗が翻る)
    mountain_fort(g, 1100, 830, 0.95, seed=2, flag=(238, 238, 236))
    # 攻める側の旗指物と騎馬 (麓)
    for i in range(4):
        nobori(g, 180 + i * 120, 990 + (i % 2) * 14, 0.7, col=P.SHU, seed=3 + i)
    samurai_rider(g, 620, 1040, 0.7, flip=-1)
    torch(g, 1400, 1030, 1.0)
    torch(g, 320, 1010, 0.9)
    campfire(g, 820, 1050, 0.8, seed=49)
    reeds_fg(cv, 1080, seed=50, color=(40, 32, 44), n=32, s=1.0)
    birds(g, [(700, 230), (820, 200), (780, 270)], 11, color=(36, 28, 40), width=4)


# ---------------------------------------------------------------- 東山文化・戦国


def bg_muromachi_ginkaku(cv):
    """銀閣と東山文化 (銀砂子の枯山水・ひなびた銀色)."""
    sky(cv, [(0.00, (168, 184, 200)), (0.55, (206, 214, 216)), (1.00, (238, 236, 228))])
    g = cv.g()
    clouds_row(cv, 150, 2, 28, seed=51, base=(228, 232, 234), under=(178, 186, 192), alpha=220)
    mountain_ridge(cv, 420, 110, ((106, 122, 128), (160, 176, 174)), seed=52, freq=1.9)
    forest_band(cv, 560, 8, (0.5, 0.9), leaf=(88, 128, 104), seed=53)
    # 枯山水の白砂
    sand = gradient((int(W * cv.ss), int((H - 600) * cv.ss)),
                    [(0, (240, 238, 230)), (1, (214, 212, 204))], "v")
    cv.img.alpha_composite(sand, (0, int(600 * cv.ss)))
    g.line([(0, 602), (W, 602)], (184, 182, 172), 4)
    # 砂紋
    rnd = random.Random(54)
    for k in range(16):
        yy = 660 + k * 26
        pts = [(x * 12, yy + math.sin(x * 0.7 + k) * 7) for x in range(0, 161)]
        g.line(pts, with_alpha((190, 188, 178), 150), 3)
    ginkaku(g, 960, 660, 1.15, seed=2)
    # 石组と苔
    for (rx, ry, rr) in [(430, 900, 34), (520, 950, 24), (1420, 920, 30), (1520, 970, 20)]:
        g.poly(blob_pts(rx, ry, rr, rr * 0.66, seed=int(rx), wobble=0.12),
               fill=(150, 148, 142), outline=(116, 114, 108), owidth=2.4)
    tree(cv, 180, 1020, 1.3, kind="pine", leaf=(64, 108, 90), seed=55)
    tree(cv, 1740, 1010, 1.2, kind="pine", leaf=(64, 108, 90), seed=56)
    # 向月見台の光
    gl = radial((int(1000 * cv.ss), int(600 * cv.ss)), (220, 224, 226), alpha_in=60, power=2.4)
    cv.img.alpha_composite(gl, (int(460 * cv.ss), int(480 * cv.ss)))


def bg_muromachi_sengoku(cv):
    """戦国の夜明け (群雄割拠の山城々)."""
    sky(cv, [(0.00, (60, 54, 96)), (0.5, (150, 100, 120)), (1.00, (238, 160, 110))])
    g = cv.g()
    stars(g, (40, 40, 1500, 260), 40, seed=57)
    clouds_row(cv, 210, 2, 46, seed=58, base=(170, 110, 120), under=(80, 52, 74), alpha=230)
    # 群雄の山城 (3つの尾根)
    for (fx, col) in [(420, (90, 110, 170)), (960, P.SHU), (1500, (226, 178, 96))]:
        g.poly(blob_pts(fx, 700, 330, 90, seed=int(fx), wobble=0.15),
               fill=(104, 92, 106))
        mountain_fort(g, fx, 730, 0.62, seed=int(fx) % 100, flag=col)
        nobori(g, fx - 210, 742, 0.6, col=col, seed=int(fx))
    # 谷の霧
    g.ellipse((-100, 700, W + 100, 820), fill=with_alpha((190, 170, 170), 110))
    ground(cv, 840, (96, 84, 96), dark=(80, 70, 82), curve=12, seed=59,
           speckles=130, speckle_colors=[(84, 74, 88), (110, 96, 106)],
           speckle_r=(2, 5))
    # 進む武士団
    for i in range(3):
        samurai_rider(g, 620 + i * 260, 1000 - i * 20, 0.6 - i * 0.05,
                      banner=False, flip=-1, seed=60 + i)
    reeds_fg(cv, 1080, seed=61, color=(42, 34, 46), n=30, s=1.0)
    birds(g, [(760, 230), (880, 200), (840, 270)], 11, color=(38, 30, 42), width=4)


# ---------------------------------------------------------------- ポイント用タイムライン


def bg_timeline(cv):
    """ep05 用ポイント背景 — 室町のタイムライン."""
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
    labels = ["室町幕府", "南北朝の動乱", "応仁の乱", "戦国の始まり"]
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
    samurai_rider(g, nodes[0], icon_y, 0.4, banner=False, flip=-1)
    two_court_flags(g, nodes[1], icon_y + 4, 0.42)
    campfire(g, nodes[2], icon_y - 20, 0.55, stones=False, seed=2)
    smoke_wisp(g, nodes[2] + 10, icon_y - 160, 0.9, color=(140, 140, 140), alpha=170, seed=3)
    mountain_fort(g, nodes[3], icon_y + 4, 0.42, seed=4)
    gl = radial((int(1400 * cv.ss), int(900 * cv.ss)), (90, 120, 200),
                alpha_in=50, power=2.4)
    cv.img.alpha_composite(gl, (int(260 * cv.ss), int(160 * cv.ss)))

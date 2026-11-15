"""ep09 シーン背景 (明治) — script.json の background 名と 1:1 対応.

戊辰戦争から文明開化、自由民権と富岡製糸場まで。テキストは焼き込まない。
"""
from __future__ import annotations

import math
import random

from artlib import palette as P
from artlib.canvas import (Canvas, blob_pts, dots_pattern, gradient, radial,
                           shade, speckle, tint, with_alpha)
from artlib.nature import (birds, clouds_row, forest_band, grass_tufts, ground,
                           mountain_ridge, reeds_fg, ridge, sky, stars, sun, tree)
from artlib.props import (arquebusier, banner_pole, brick_building, campfire, rect,
                          castle_ruins, factory, gaslamp, kenchi_stakes,
                          mountain_fort, nobori, rickshaw, rice_paddy,
                          samurai_rider, schoolhouse, shishi, smoke_wisp,
                          steam_train, tile_roof_house, two_court_flags)

W, H = 1920, 1080


def new_canvas():
    return Canvas(W, H, ss=2)


def _dust(g, box, n, seed=0, color=(188, 174, 148), alpha=110):
    rnd = random.Random(seed)
    for _ in range(n):
        px = rnd.uniform(box[0], box[2])
        py = rnd.uniform(box[1], box[3])
        r_ = rnd.uniform(20, 70)
        g.ellipse((px - r_, py - r_ * 0.4, px + r_, py + r_ * 0.4),
                  fill=with_alpha(color, rnd.randint(40, alpha)))


def _wband(g, x0, x1, y0, y1, wall=P.PLASTER, frame=P.VERMILION_WOOD,
           step=90, seed=0):
    rect(g, x0, y0, x1, y1, fill=wall, outline=shade(wall, 0.8), owidth=2.2)
    rnd = random.Random(seed)
    px = x0 + 10
    while px < x1 - 14:
        rect(g, px, y0, px + 11, y1, fill=frame)
        px += step + rnd.uniform(-6, 6)
    g.line([(x0, y0), (x1, y0)], shade(frame, 0.7), 4)


# ---------------------------------------------------------------- 戦乱と維新


def bg_meiji_boshin(cv):
    """戊辰戦争 (1868・箱館まで続いた戦い)."""
    sky(cv, P.SKY_SUNSET)
    g = cv.g()
    clouds_row(cv, 190, 3, 44, seed=2, base=(178, 100, 96), under=(84, 50, 74), alpha=230)
    mountain_ridge(cv, 460, 130, ((66, 46, 74), (118, 72, 84)), seed=3, freq=1.7)
    ground(cv, 630, (120, 96, 90), dark=(96, 76, 72), curve=12, seed=4,
           speckles=150, speckle_colors=[(104, 84, 80), (136, 110, 104)],
           speckle_r=(2, 5))
    # 進軍する新政府軍と抵抗する旧幕府軍
    for i in range(3):
        samurai_rider(g, 400 + i * 180, 880 - i * 24, 0.6 - i * 0.05,
                      banner=(i == 0), flip=-1, seed=5 + i)
    for i in range(2):
        samurai_rider(g, 1500 + i * 200, 860 - i * 20, 0.52, banner=False, seed=8 + i)
    # 砲撃の炎
    campfire(g, 1200, 700, 1.0, stones=False, seed=10)
    smoke_wisp(g, 1220, 570, 1.4, color=(70, 56, 72), alpha=190, seed=11)
    _dust(g, (200, 0, 1500, 1060), 18, seed=12)
    reeds_fg(cv, 1080, seed=13, color=(46, 36, 50), n=32, s=1.0)
    birds(g, [(700, 230), (820, 200), (780, 270)], 10, color=(44, 34, 48), width=4)


def bg_meiji_civilization(cv):
    """文明開化 (煉瓦街・汽車・ガス灯)."""
    sky(cv, P.SKY_MEIJI_DAY)
    g = cv.g()
    sun(g, 420, 170, 54, halo=0.45)
    clouds_row(cv, 140, 3, 30, seed=14)
    # 銀座煉瓦街 (両側の煉瓦建築 + 接地影)
    for (bx, by, bs, sd) in [(180, 760, 0.62, 1), (640, 736, 0.5, 2),
                             (1300, 736, 0.5, 3), (1740, 760, 0.62, 4)]:
        g.ellipse((bx - 150 * bs, by - 10 * bs, bx + 170 * bs, by + 26 * bs),
                  fill=with_alpha((70, 60, 50), 90))
        brick_building(g, bx, by, bs, w=160, floors=2, seed=sd)
    # 歩道 (建物と大路をつなぐ縁石で接地感を出す)
    rect(g, 0, 742, W, 790, fill=(178, 170, 146))
    g.line([(0, 744), (W, 744)], (152, 146, 124), 4)
    # 中央の中景: 電柱と往来する人・荷車
    for px in (820, 1000):
        g.line([(px, 700), (px, 880)], (70, 66, 72), 7)
        g.line([(px - 44, 724), (px + 44, 724)], (70, 66, 72), 4)
        g.line([(px - 44, 758), (px + 44, 758)], (70, 66, 72), 4)
    rickshaw(g, 900, 900, 0.9)
    # 歩行者 (小さく散らして自然に)
    rnd_p = random.Random(16)
    for k in range(6):
        px = 760 + k * 80 + rnd_p.uniform(-20, 20)
        py = 950 + (k % 3) * 30
        sc = rnd_p.uniform(0.55, 0.75)
        g.circle(px, py - 26 * sc, 9 * sc, fill=(64, 56, 62))
        g.poly([(px - 9 * sc, py - 18 * sc), (px + 9 * sc, py - 18 * sc),
                (px + 6 * sc, py + 2 * sc), (px - 6 * sc, py + 2 * sc)],
               fill=(64, 56, 62))
    # 大通り
    ground(cv, 700, (196, 190, 164), dark=(164, 158, 132), curve=10, seed=15,
           speckles=130, speckle_colors=[(176, 170, 144), (212, 206, 180)],
           speckle_r=(2, 5))
    # ガス灯
    for gx in (200, 620, 960, 1300, 1720):
        gaslamp(g, gx, 800, 0.62)
    # 蒸気汽車 (遠景を走る)
    steam_train(g, 1480, 940, 0.52, seed=3)
    # 人力車 (手前)
    rickshaw(g, 300, 1000, 1.0)
    # 散切り頭の紳士のシルエット
    for px in (760, 860, 1140):
        g.circle(px, 850, 14, fill=(64, 56, 62))
        g.poly([(px - 16, 862), (px + 16, 862), (px + 11, 920), (px - 11, 920)],
               fill=(64, 56, 62))
        g.rrect((px - 15, 830, px + 15, 852), 5, fill=(52, 46, 52))
    birds(g, [(1200, 200), (1300, 240), (1260, 170)], 12, width=3.2)


def bg_meiji_government(cv):
    """太政官政府 (洋風の官庁と太政大臣)."""
    sky(cv, P.SKY_MEIJI_DAY)
    g = cv.g()
    sun(g, 1440, 180, 54, halo=0.45)
    clouds_row(cv, 140, 3, 30, seed=16)
    ground(cv, 560, (196, 190, 160), dark=(164, 158, 130), curve=10, seed=17,
           speckles=140, speckle_colors=[(176, 170, 140), (210, 204, 174)],
           speckle_r=(2, 5))
    # 太政官の洋館 (左右対称)
    brick_building(g, 960, 760, 0.85, w=240, floors=2, seed=2)
    # 軍の幟と衛兵
    nobori(g, 560, 780, 0.85, col=(238, 238, 236))
    nobori(g, 1360, 780, 0.85, col=P.SHU)
    for i in range(3):
        arquebusier(g, 620 + i * 90, 960, 0.72, firing=False, seed=18 + i)
    # 陸橋と坂
    g.poly([(820, 1080), (1100, 1080), (1020, 760), (900, 760)], fill=(210, 202, 174))
    tree(cv, 200, 1020, 1.2, kind="pine", leaf=(60, 112, 88), seed=19)
    tree(cv, 1720, 1010, 1.1, kind="pine", leaf=(60, 112, 88), seed=20)
    birds(g, [(700, 230), (800, 270), (760, 200)], 12, width=3.2)


def bg_meiji_haipan(cv):
    """廃藩置県 (取り壊される城跡と新しい県)."""
    sky(cv, [(0.00, (120, 150, 180)), (0.55, (170, 196, 210)), (1.00, (236, 230, 212))])
    g = cv.g()
    clouds_row(cv, 150, 3, 32, seed=21)
    mountain_ridge(cv, 440, 120, ((108, 136, 130), (166, 188, 164)), seed=22, freq=1.9)
    ground(cv, 630, (176, 172, 120), dark=(144, 140, 98), curve=12, seed=23,
           speckles=150, speckle_colors=[(156, 152, 104), (190, 186, 134)],
           speckle_r=(2, 5))
    # 取り壊された城跡
    castle_ruins(g, 560, 700, 0.85, seed=2)
    # 解体の作業場 (木材の山)
    for k in range(3):
        rect(g, 820 + k * 200, 690, 900 + k * 200, 730, fill=(158, 126, 94),
             outline=(126, 100, 74), owidth=2.4)
    # 新しい県庁の小さな洋館
    brick_building(g, 1450, 700, 0.55, w=120, floors=2, seed=3)
    nobori(g, 1240, 720, 0.8, col=(238, 238, 236))
    grass_tufts(g, (0, 700, W, 1070), 80, (150, 148, 104), seed=24)
    birds(g, [(700, 230), (800, 270), (760, 200)], 12, width=3.2)


def bg_meiji_heishi(cv):
    """徴兵制 (訓練する兵士の列)."""
    sky(cv, P.SKY_EDO_DAY)
    g = cv.g()
    clouds_row(cv, 150, 3, 30, seed=25)
    mountain_ridge(cv, 430, 100, ((108, 136, 130), (166, 188, 164)), seed=26, freq=1.9)
    ground(cv, 600, (178, 172, 124), dark=(146, 140, 100), curve=10, seed=27,
           speckles=140, speckle_colors=[(158, 152, 108), (192, 186, 138)],
           speckle_r=(2, 5))
    # 訓練する兵士の列 (銃を構えて整列)
    for r in range(2):
        for k in range(6):
            arquebusier(g, 420 + k * 180 + r * 90, 760 + r * 130, 0.85 - r * 0.08,
                        firing=False, seed=28 + r * 6 + k)
    # 教官と軍旗
    shishi(g, 300, 800, 0.85, col=(86, 66, 56), sword=True, seed=29)
    nobori(g, 1660, 800, 0.9, col=(238, 238, 236))
    nobori(g, 1800, 820, 0.75, col=P.SHU)
    _dust(g, (300, 0, 1700, 1000), 12, seed=30)
    grass_tufts(g, (0, 880, W, 1070), 70, (152, 148, 104), seed=31)


def bg_meiji_itagaki(cv):
    """自由民権運動 (板垣死すとも自由は死せず)."""
    sky(cv, [(0.00, (140, 150, 186)), (0.55, (190, 176, 186)), (1.00, (240, 216, 196))])
    g = cv.g()
    clouds_row(cv, 150, 3, 32, seed=32)
    mountain_ridge(cv, 450, 110, ((104, 96, 120), (160, 132, 136)), seed=33, freq=1.8)
    ground(cv, 630, (176, 168, 122), dark=(146, 138, 100), curve=12, seed=34,
           speckles=150, speckle_colors=[(156, 148, 106), (190, 182, 136)],
           speckle_r=(2, 5))
    # 演説の壇と幟
    rect(g, 880, 760, 1240, 840, fill=(120, 88, 62), outline=(88, 62, 42), owidth=4)
    shishi(g, 1060, 756, 1.0, col=(64, 54, 62), sword=False, seed=35)
    for k in range(5):
        nobori(g, 300 + k * 130, 850 + (k % 2) * 14, 0.72,
               col=(90, 110, 170) if k % 2 else (238, 238, 236), seed=36 + k)
    # 民衆 (聴衆のシルエット)
    rnd = random.Random(37)
    for _ in range(16):
        px = rnd.uniform(500, 1500)
        py = rnd.uniform(900, 1030)
        g.circle(px, py - 30, 13, fill=(66, 58, 70))
        g.poly([(px - 14, py - 18), (px + 14, py - 18), (px + 9, py + 8), (px - 9, py + 8)],
               fill=(66, 58, 70))
    birds(g, [(900, 230), (1000, 270), (960, 200)], 12, width=3.2)


def bg_meiji_nochi(cv):
    """地租改正 (検地の杭と新しい租税)."""
    sky(cv, P.SKY_EDO_DAY)
    g = cv.g()
    sun(g, 1440, 180, 52, halo=0.45)
    clouds_row(cv, 150, 3, 30, seed=38)
    mountain_ridge(cv, 450, 110, ((108, 136, 130), (166, 188, 164)), seed=39, freq=1.9)
    ground(cv, 620, (178, 172, 120), dark=(146, 140, 98), curve=12, seed=40,
           speckles=150, speckle_colors=[(158, 152, 106), (192, 186, 136)],
           speckle_r=(2, 5))
    # 測量された田
    for r in range(2):
        for c in range(6):
            x0, y0 = 140 + c * 290, 700 + r * 130
            rect(g, x0, y0, x0 + 270, y0 + 112,
                 fill=(190, 196, 130) if (r + c) % 2 else (178, 184, 118))
            g.line([(x0, y0 + 116), (x0 + 270, y0 + 116)], (146, 150, 96), 4)
    kenchi_stakes(g, (200, 660, 900, 960), n=5, seed=2, s=1.25)
    kenchi_stakes(g, (1150, 660, 1780, 960), n=4, seed=3, s=1.25)
    # 地券の卓
    rect(g, 880, 920, 1220, 980, fill=(120, 88, 62), outline=(88, 62, 42), owidth=4)
    g.rrect((920, 884, 1180, 946), 6, fill=(238, 232, 214), outline=(190, 182, 160),
            owidth=2.4)
    for k in range(2):
        g.line([(944, 912 + k * 18), (1176, 912 + k * 18)], with_alpha((150, 140, 120), 170),
               2.6)
    grass_tufts(g, (0, 690, W, 1070), 70, (150, 148, 104), seed=41)
    birds(g, [(700, 230), (800, 270), (760, 200)], 12, width=3.2)


def bg_meiji_people(cv):
    """庶民の文明開化 (牛鍋屋と人力車・ガス灯)."""
    sky(cv, P.SKY_MEIJI_DAY)
    g = cv.g()
    sun(g, 1440, 170, 52, halo=0.45)
    clouds_row(cv, 140, 3, 30, seed=42)
    ground(cv, 660, (196, 190, 164), dark=(164, 158, 132), curve=10, seed=43,
           speckles=140, speckle_colors=[(176, 170, 144), (212, 206, 180)],
           speckle_r=(2, 5))
    # 牛鍋屋 (軒の並ぶ町家)
    for (hx, hy, hs) in [(200, 700, 0.75), (520, 672, 0.62), (1450, 680, 0.7),
                         (1700, 705, 0.8)]:
        tile_roof_house(g, hx, hy, hs, seed=int(hx))
        # のれん
        rect(g, hx - 40 * hs, 700 - 20 * hs, hx + 40 * hs, 700 + 8 * hs,
             fill=with_alpha((150, 90, 80), 220))
    # 人力車×2 とガス灯
    rickshaw(g, 480, 950, 0.9)
    rickshaw(g, 1120, 990, 1.05)
    for gx in (700, 1300, 1650):
        gaslamp(g, gx, 860, 0.62)
    _crowd(g, (200, 880, 1750, 1060), 18, seed=44)
    birds(g, [(700, 230), (800, 270), (760, 200)], 12, width=3.2)


def _crowd(g, box, n, seed=0, col=(70, 62, 68)):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(n):
        px = rnd.uniform(x0, x1)
        py = rnd.uniform(y0, y1)
        s_ = rnd.uniform(0.8, 1.2)
        g.circle(px, py - 26 * s_, 9 * s_, fill=col)
        g.poly([(px - 10 * s_, py - 18 * s_), (px + 10 * s_, py - 18 * s_),
                (px + 7 * s_, py + 2 * s_), (px - 7 * s_, py + 2 * s_)], fill=col)


def bg_meiji_school(cv):
    """学制 (洋風小学校に通う児童)."""
    sky(cv, P.SKY_MEIJI_DAY)
    g = cv.g()
    sun(g, 380, 180, 52, halo=0.45)
    clouds_row(cv, 140, 3, 30, seed=45)
    mountain_ridge(cv, 440, 110, ((108, 136, 130), (166, 188, 164)), seed=46, freq=1.9)
    ground(cv, 640, (182, 176, 124), dark=(150, 144, 100), curve=12, seed=47,
           speckles=150, speckle_colors=[(162, 156, 108), (196, 190, 138)],
           speckle_r=(2, 5))
    # 洋風小学校
    schoolhouse(g, 960, 700, 0.95, seed=2)
    # 通学する児童 (ランドセル風の影)
    rnd = random.Random(48)
    for k in range(6):
        px = 300 + k * 220 + rnd.uniform(-30, 30)
        py = 900 + (k % 2) * 50 + rnd.uniform(-10, 10)
        g.circle(px, py - 34, 12, fill=(228, 214, 200))
        g.poly([(px - 13, py - 24), (px + 13, py - 24), (px + 9, py + 12), (px - 9, py + 12)],
               fill=rnd.choice([(86, 110, 150), (150, 96, 90), (96, 140, 100)]))
        g.rrect((px - 10, py - 22, px + 10, py - 4), 4, fill=(150, 120, 80))
    # 通学路
    g.poly([(0, 980), (W, 980), (W, 1080), (0, 1080)], fill=(212, 198, 158))
    grass_tufts(g, (0, 700, W, 980), 70, (150, 148, 104), seed=49)
    birds(g, [(700, 230), (800, 270), (760, 200)], 12, width=3.2)


def bg_meiji_seikanron(cv):
    """征韓論争 (政府が二つに裂ける)."""
    sky(cv, [(0.00, (110, 110, 150)), (0.55, (170, 150, 166)), (1.00, (234, 200, 176))])
    g = cv.g()
    clouds_row(cv, 160, 3, 36, seed=50, base=(200, 160, 164), under=(140, 100, 118),
               alpha=225)
    mountain_ridge(cv, 440, 100, ((96, 88, 112), (150, 120, 132)), seed=51, freq=1.8)
    ground(cv, 620, (170, 160, 118), dark=(140, 132, 96), curve=12, seed=52,
           speckles=150, speckle_colors=[(150, 140, 102), (184, 174, 132)],
           speckle_r=(2, 5))
    # 裂ける二つの陣営 (左=征韓派・右=反対派)
    two_court_flags(g, 420, 700, 0.95)
    two_court_flags(g, 1500, 700, 0.95)
    # 対峙する参議のシルエット
    shishi(g, 820, 900, 0.85, col=(76, 60, 68), sword=False, seed=53)
    shishi(g, 1100, 900, 0.85, col=(60, 56, 66), sword=False, seed=54)
    # 荒れる空
    _dust(g, (600, 0, 1400, 1060), 14, seed=55)
    birds(g, [(860, 240), (960, 210), (920, 280)], 10, color=(44, 40, 56), width=4)


def bg_meiji_tomioka(cv):
    """富岡製糸場 (洋風の製糸工場と繰糸器)."""
    sky(cv, P.SKY_MEIJI_DAY)
    g = cv.g()
    sun(g, 400, 180, 52, halo=0.45)
    clouds_row(cv, 150, 3, 30, seed=56)
    mountain_ridge(cv, 440, 110, ((106, 136, 128), (166, 188, 164)), seed=57, freq=1.9)
    ground(cv, 620, (182, 178, 128), dark=(150, 146, 102), curve=12, seed=58,
           speckles=150, speckle_colors=[(162, 158, 110), (196, 192, 142)],
           speckle_r=(2, 5))
    # 製糸場 (ノコギリ屋根の煉瓦工場)
    factory(g, 960, 740, 1.0, seed=2)
    # 働く女工のシルエット
    for k in range(5):
        px = 700 + k * 130
        g.circle(px, 830, 11, fill=(90, 74, 68))
        g.poly([(px - 12, 818), (px + 12, 818), (px + 8, 862), (px - 8, 862)],
               fill=(110, 88, 96))
        g.rrect((px - 9, 812, px + 9, 822), 3, fill=(196, 190, 176))
    # 桑畑
    for k in range(6):
        tree(cv, 140 + k * 330, 990, 0.6, kind="oak", leaf=(116, 156, 104), seed=59 + k)
    grass_tufts(g, (0, 700, W, 1070), 70, (150, 148, 104), seed=60)
    birds(g, [(700, 230), (800, 270), (760, 200)], 12, width=3.2)


def bg_meiji_dusk(cv):
    """明治の夕暮れ (煉瓦街に灯るガス灯と汽車)."""
    sky(cv, [(0.00, (96, 100, 150)), (0.5, (190, 140, 150)), (1.00, (244, 196, 150))])
    g = cv.g()
    clouds_row(cv, 170, 3, 40, seed=61, base=(214, 150, 140), under=(130, 90, 110),
               alpha=225)
    mountain_ridge(cv, 470, 100, ((86, 74, 104), (140, 104, 122)), seed=62, freq=1.8)
    ground(cv, 620, (170, 150, 120), dark=(140, 122, 96), curve=10, seed=63,
           speckles=140, speckle_colors=[(150, 134, 106), (184, 166, 136)],
           speckle_r=(2, 5))
    # 煉瓦街のシルエット
    brick_building(g, 420, 700, 0.7, w=170, floors=2, seed=2)
    brick_building(g, 1500, 700, 0.7, w=170, floors=2, seed=3)
    # ガス灯の並び (灯る)
    for gx in (200, 620, 960, 1300, 1720):
        gaslamp(g, gx, 860, 0.66)
    # 蒸気汽車が通り過ぎる
    steam_train(g, 960, 990, 0.6, seed=4)
    _crowd(g, (150, 880, 1750, 1050), 16, seed=64)
    birds(g, [(700, 230), (800, 270), (760, 200)], 12, width=3.2)




def bg_meiji_seinan(cv):
    """西南戦争 (1877・城山の決戦と燃える鹿児島)."""
    sky(cv, [(0.00, (46, 36, 66)), (0.5, (120, 70, 92)), (0.75, (206, 100, 80)),
             (1.00, (240, 150, 104))])
    g = cv.g()
    stars(g, (40, 40, 1300, 280), 40, seed=62)
    mountain_ridge(cv, 450, 110, ((52, 40, 68), (100, 66, 88)), seed=63, freq=1.7)
    # 燃える鹿児島市街 (中景の屋根と火柱)
    rnd = random.Random(64)
    x = 0
    while x < W:
        hw = rnd.uniform(110, 180)
        hh = rnd.uniform(38, 70)
        rect(g, x, 660 - hh, x + hw, 700, fill=(78, 58, 70))
        g.poly([(x - 8, 660 - hh), (x + hw + 8, 660 - hh), (x + hw * 0.72, 660 - hh - 26),
                (x + hw * 0.28, 660 - hh - 26)], fill=(66, 48, 62))
        x += hw + rnd.uniform(16, 58)
    rect(g, 0, 700, W, H, fill=(92, 72, 82))
    speckle(g, (0, 710, W, 1080), 130, [(80, 62, 74), (104, 82, 90)], r=(2, 6), seed=65)
    for fx in (620, 1000, 1420):
        campfire(g, fx, 700, 1.2, stones=False, seed=int(fx))
        smoke_wisp(g, fx + 20, 540, 1.8, color=(64, 50, 68), alpha=200, seed=int(fx))
    # 城山の丘と指揮官 (西郷風の大きな姿)
    g.poly(blob_pts(1500, 660, 340, 100, seed=66, wobble=0.14),
           fill=(88, 96, 74), outline=(72, 80, 60), owidth=3 * 1)
    shishi(g, 1480, 560, 0.95, col=(52, 44, 56), sword=True, seed=67)
    for k in range(3):
        shishi(g, 1360 + k * 70, 600 + (k % 2) * 14, 0.5, col=(58, 48, 58),
               sword=(k == 0), seed=68 + k)
    nobori(g, 1620, 600, 0.6, col=(238, 238, 236), seed=69)
    # 政府軍の陣列 (手前左: 銃を構えた整列)
    for r in range(2):
        for k in range(5):
            arquebusier(g, 200 + k * 170 + r * 80, 890 + r * 110, 0.8 - r * 0.08,
                        firing=False, seed=70 + r * 5 + k)
    nobori(g, 120, 880, 0.85, col=(238, 238, 236))
    nobori(g, 760, 920, 0.7, col=P.SHU)
    _dust(g, (100, 0, 1700, 1060), 16, seed=71)
    reeds_fg(cv, 1080, seed=72, color=(42, 34, 48), n=32, s=1.0)
    birds(g, [(760, 240), (880, 210), (840, 280)], 10, color=(40, 30, 44), width=4)


# ---------------------------------------------------------------- ポイント用タイムライン


def bg_timeline(cv):
    """ep09 用ポイント背景 — 明治のタイムライン."""
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
    labels = ["戊辰戦争 1868", "廃藩置県 1871", "文明開化", "自由民権運動"]
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
        g.text((nx, band_y + 118), labels[i], 26, (214, 224, 248), "bold", "mm")
    campfire(g, nodes[0], icon_y - 24, 0.55, stones=False, seed=1)
    smoke_wisp(g, nodes[0] + 12, icon_y - 166, 0.9, color=(150, 146, 146), alpha=180, seed=2)
    castle_ruins(g, nodes[1], icon_y - 6, 0.44, seed=3)
    brick_building(g, nodes[2], icon_y - 4, 0.4, w=90, floors=2, seed=4)
    shishi(g, nodes[3], icon_y - 6, 0.6, col=(64, 54, 62), sword=False, seed=5)
    gl = radial((int(1400 * cv.ss), int(900 * cv.ss)), (90, 120, 200),
                alpha_in=50, power=2.4)
    cv.img.alpha_composite(gl, (int(260 * cv.ss), int(160 * cv.ss)))

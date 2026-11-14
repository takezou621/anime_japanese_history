"""ep06 シーン背景 (織豊) — script.json の background 名と 1:1 対応.

桶狭間から天下統一、桃山の華やぎと茶の湯まで。テキストは焼き込まない。
"""
from __future__ import annotations

import math
import random

from artlib import palette as P
from artlib.canvas import (Canvas, blob_pts, dots_pattern, gradient, qbez,
                           radial, shade, speckle, tint, with_alpha)
from artlib.nature import (birds, cloud, clouds_row, forest_band, grass_tufts,
                           ground, mountain_ridge, ridge, sky, stars, sun, tree)
from artlib.props import (arquebusier, atakebune, azuchi_castle, bakeblock_fence,
                          banner_pole, boat, campfire, gold_screen, kabuto,
                          kango_ship, mongol_ship, nobori, osaka_castle,
                          ox_cart, samurai_rider, smoke_wisp, tenshu, torii)
from artlib.props import kenchi_stakes, rect, seedling
from scenes_ep01 import bow_and_arrows

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


# ---------------------------------------------------------------- 戦い


def bg_azuchi_okahazama(cv):
    """桶狭間 (1560・暴風の暁に奇襲)."""
    sky(cv, [(0.00, (66, 74, 96)), (0.5, (120, 126, 148)), (1.00, (188, 184, 178))])
    g = cv.g()
    clouds_row(cv, 170, 4, 50, seed=2, base=(92, 96, 110), under=(60, 64, 78), alpha=240)
    mountain_ridge(cv, 440, 120, ((84, 88, 104), (128, 132, 142)), seed=3, freq=1.8)
    ground(cv, 620, (140, 132, 110), dark=(116, 108, 90), curve=12, seed=4,
           speckles=150, speckle_colors=[(126, 118, 98), (156, 148, 124)],
           speckle_r=(2, 5))
    # 今川の本陣 (右奥: 幕+旗)
    for bx in (1420, 1580, 1740):
        rect(g, bx - 70, 560, bx + 70, 640, fill=(214, 202, 172),
             outline=(168, 154, 122), owidth=2.4)
        g.poly([(bx - 78, 560), (bx + 78, 560), (bx + 60, 534), (bx - 60, 534)],
               fill=(170, 90, 76), outline=(132, 96, 78), owidth=2)
        nobori(g, bx, 540, 0.55, col=(170, 90, 76), seed=bx)
    campfire(g, 1580, 700, 0.8, seed=5)
    # 奇襲する織田勢 (左から)
    for i in range(4):
        samurai_rider(g, 260 + i * 190, 900 - i * 28, 0.62 - i * 0.05,
                      banner=(i == 0), flip=-1, seed=6 + i)
    nobori(g, 150, 900, 0.8, col=(240, 240, 238))
    _dust(g, (120, 0, 900, 1060), 22, seed=7)
    # 暴風の雨筋
    rnd = random.Random(8)
    for _ in range(50):
        rx, ry = rnd.uniform(0, W), rnd.uniform(60, 1060)
        g.line([(rx, ry), (rx - 12, ry + 28)], with_alpha((190, 196, 204), 85), 1.8)
    birds(g, [(760, 230), (860, 200), (820, 270)], 10, color=(50, 48, 58), width=3.6)


def bg_azuchi_gifu(cv):
    """岐阜 (稲葉山の城と天下布武の町)."""
    sky(cv, P.SKY_AZUCHI_DAY)
    g = cv.g()
    sun(g, 1460, 180, 54, halo=0.45)
    clouds_row(cv, 140, 3, 32, seed=9)
    # 金華山 (急な山に天守)
    g.poly([(660, 1080), (660, 560)] + [(x, 560 - 90 * math.exp(-((x - 1050) / 300.0) ** 2))
                                        for x in range(660, 1441, 60)] + [(1440, 700), (1440, 1080)],
           fill=(116, 140, 102))
    forest_band(cv, 700, 6, (0.5, 0.9), leaf=(88, 130, 96), seed=10)
    tenshu(g, 1050, 590, 0.42, tiers=4, gold_top=False, seed=2)
    # 山麓の城下町
    ground(cv, 760, (188, 184, 134), dark=(156, 152, 108), curve=12, seed=11,
           speckles=150, speckle_colors=[(168, 164, 116), (202, 198, 148)],
           speckle_r=(2, 5))
    for (hx, hy, hs) in [(320, 850, 0.9), (520, 800, 0.75), (720, 762, 0.65),
                         (900, 735, 0.58)]:
        tile_roof_house(g, hx, hy, hs, seed=int(hx))
    nobori(g, 120, 880, 0.8, col=(238, 238, 236))
    ox_cart(g, 1500, 950, 0.6, seed=3)
    grass_tufts(g, (0, 780, W, 1070), 80, (152, 150, 104), seed=12)
    birds(g, [(500, 230), (600, 270), (560, 200)], 12, width=3.2)


def bg_azuchi_castle(cv):
    """安土城 (琵琶湖畔に聳える天主)."""
    sky(cv, P.SKY_AZUCHI_DAY)
    g = cv.g()
    sun(g, 1440, 180, 56, halo=0.45)
    clouds_row(cv, 140, 3, 32, seed=13)
    mountain_ridge(cv, 400, 90, ((104, 138, 126), (164, 186, 162)), seed=14, freq=1.8)
    horizon = 520
    lake = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                    [(0, (140, 190, 214)), (0.4, (100, 160, 202)), (1, (70, 128, 176))], "v")
    cv.img.alpha_composite(lake, (0, int(horizon * cv.ss)))
    rnd = random.Random(15)
    for _ in range(24):
        yy = rnd.uniform(horizon + 10, H - 30)
        ln = rnd.uniform(30, 140)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((240, 250, 255), rnd.randint(50, 130)))
    # 湖畔の丘の上に天主
    azuchi_castle(g, 960, 700, 0.9, seed=2)
    # 湖の舟
    boat(g, 420, 900, 0.85, oars=2, figure=True, seed=3)
    boat(g, 1520, 830, 0.6, oars=1, seed=4)
    birds(g, [(500, 240), (600, 280), (560, 210)], 12, width=3.2)


def bg_azuchi_nagashino(cv):
    """長篠の戦い (1575・馬防柵と三千挺鉄砲)."""
    sky(cv, [(0.00, (96, 130, 168)), (0.5, (160, 170, 178)), (1.00, (216, 210, 196))])
    g = cv.g()
    clouds_row(cv, 150, 3, 38, seed=16, base=(210, 214, 216), under=(160, 164, 170), alpha=230)
    mountain_ridge(cv, 430, 100, ((100, 124, 124), (152, 170, 162)), seed=17, freq=1.9)
    ground(cv, 620, (168, 164, 120), dark=(138, 134, 98), curve=12, seed=18,
           speckles=160, speckle_colors=[(148, 144, 104), (182, 178, 132)],
           speckle_r=(2, 5))
    # 鉄砲隊 (柵の背後に膝立ちで発射)
    for i in range(7):
        firing = i % 3 == 0
        arquebusier(g, 240 + i * 250, 736 + (i % 2) * 10, 1.0 - i * 0.04,
                    firing=firing, seed=19 + i)
    # 馬防柵 (手前の三重柵が縦横を遮る)
    bakeblock_fence(g, 0, W, 790, 1.0)
    # 武田の騎馬突撃 (遠景の平地・塵を上げて)
    for i in range(3):
        samurai_rider(g, 160 + i * 140, 650 + i * 26, 0.30 - i * 0.035,
                      banner=False, flip=1, seed=20 + i)
    _dust(g, (60, 620, 700, 730), 16, seed=21)
    # 織田の幟
    nobori(g, 1560, 900, 0.9, col=(238, 238, 236))
    nobori(g, 1720, 930, 0.8, col=(90, 110, 170))
    grass_tufts(g, (0, 840, W, 1070), 70, (148, 144, 100), seed=22)
    birds(g, [(1200, 230), (1300, 270), (1260, 200)], 11, width=3.2)


def bg_azuchi_honnoji(cv):
    """本能寺の変 (1582・夜半の炎上)."""
    sky(cv, [(0.00, (18, 22, 48)), (0.55, (36, 34, 62)), (1.00, (60, 40, 56))])
    g = cv.g()
    stars(g, (40, 40, 1200, 320), 60, seed=23)
    moon(cv, 1700, 170, 46, cut_color=(16, 18, 44))
    ground(cv, 640, (56, 44, 54), dark=(46, 36, 46), curve=12, seed=24,
           speckles=130, speckle_colors=[(48, 38, 48), (64, 50, 60)],
           speckle_r=(2, 5))
    # 寺の建物 (シルエット)
    g.rect(g, 300, 560, 900, 700, fill=(64, 50, 56))
    g.poly([(288, 560), (912, 560), (860, 496), (340, 496)], fill=(52, 42, 50))
    for px in range(330, 901, 90):
        rect(g, px, 580, px + 22, 700, fill=(46, 36, 44))
    # 炎上
    campfire(g, 560, 690, 2.0, stones=False, seed=25)
    campfire(g, 820, 660, 1.4, stones=False, seed=26)
    smoke_wisp(g, 590, 430, 2.2, color=(60, 52, 62), alpha=200, seed=27)
    smoke_wisp(g, 860, 470, 1.6, color=(60, 52, 62), alpha=180, seed=28)
    # 包囲する兵士のシルエット (槍の列)
    rnd = random.Random(29)
    for _ in range(22):
        px = rnd.uniform(1100, 1850)
        py = rnd.uniform(880, 1020)
        g.line([(px, py), (px + rnd.uniform(-10, 10), py - rnd.uniform(50, 96))],
               (40, 30, 44), rnd.uniform(2.4, 3.6))
        g.circle(px, py - 8, 8, fill=(40, 30, 44))
    # 手前の松明
    torch(g, 200, 1000, 1.05)
    torch(g, 1740, 1010, 1.0)
    reeds_fg(cv, 1080, seed=30, color=(36, 28, 42), n=30, s=1.0)


def bg_azuchi_yamazaki(cv):
    """山崎の戦い (天王山をめぐる夕戦)."""
    sky(cv, P.SKY_SUNSET)
    g = cv.g()
    clouds_row(cv, 180, 3, 44, seed=31, base=(182, 100, 96), under=(86, 50, 74), alpha=230)
    # 天王山の斜面 (右から左へ下る)
    g.poly([(0, 1080), (0, 520)] + [(x, 520 + 90 * math.sin(x * 0.0035 + 0.6))
                                    for x in range(0, 1921, 60)] + [(W, 1080)],
           fill=(120, 100, 96))
    g.line([(0, 522), (W, 522)], (98, 82, 80), 5)
    # 山頂を巡る両軍の旗 (上=秀吉の金 / 下=光秀の朱)
    for i in range(3):
        nobori(g, 1500 + i * 90, 560 + i * 24, 0.55, col=P.GOLD_LEAF, seed=32 + i)
        nobori(g, 340 + i * 90, 640 + i * 26, 0.55, col=P.SHU, seed=33 + i)
    # 斜面の軍勢
    for i in range(3):
        samurai_rider(g, 1360 - i * 130, 640 + i * 30, 0.5 - i * 0.04, banner=False, seed=34 + i)
        samurai_rider(g, 500 + i * 130, 760 + i * 30, 0.46 - i * 0.04, banner=False,
                      flip=-1, seed=35 + i)
    _dust(g, (200, 0, 1700, 1060), 20, seed=36)
    rect(g, 0, 780, W, H, fill=(96, 80, 84))
    speckle(g, (0, 800, W, 1080), 120, [(84, 70, 76), (110, 92, 94)], r=(2, 6), seed=37)
    birds(g, [(860, 240), (960, 210), (920, 280)], 10, color=(44, 34, 48), width=4)


# ---------------------------------------------------------------- 天下統一


def bg_azuchi_osaka(cv):
    """大坂城 (巨石の石垣と白亜の大天守)."""
    sky(cv, P.SKY_AZUCHI_DAY)
    g = cv.g()
    sun(g, 1420, 170, 56, halo=0.45)
    clouds_row(cv, 140, 3, 32, seed=38)
    mountain_ridge(cv, 400, 90, ((104, 138, 126), (166, 188, 164)), seed=39, freq=1.8)
    ground(cv, 560, (182, 178, 128), dark=(150, 146, 102), curve=12, seed=40,
           speckles=150, speckle_colors=[(162, 158, 110), (196, 192, 142)],
           speckle_r=(2, 5))
    osaka_castle(g, 960, 660, 0.85, seed=2)
    # 楼門と松
    nobori(g, 300, 900, 0.85, col=(238, 238, 236))
    nobori(g, 1620, 900, 0.85, col=(238, 238, 236))
    tree(cv, 150, 1030, 1.25, kind="pine", leaf=(60, 112, 88), seed=3)
    tree(cv, 1780, 1020, 1.15, kind="pine", leaf=(60, 112, 88), seed=4)
    grass_tufts(g, (0, 700, W, 1070), 80, (152, 150, 104), seed=41)
    birds(g, [(520, 230), (620, 270), (580, 200)], 12, width=3.2)


def bg_azuchi_kenchi(cv):
    """太閤検地 (打出の杭と新たな水帳)."""
    sky(cv, P.SKY_KAMAKURA_DAY)
    g = cv.g()
    sun(g, 380, 190, 54, halo=0.45)
    clouds_row(cv, 150, 3, 32, seed=42)
    mountain_ridge(cv, 450, 120, ((106, 136, 130), (168, 188, 164)), seed=43, freq=1.9)
    ground(cv, 620, (180, 176, 122), dark=(148, 144, 100), curve=12, seed=44,
           speckles=150, speckle_colors=[(160, 156, 108), (194, 190, 138)],
           speckle_r=(2, 5))
    # 検地後の整った田 (区画)
    for r in range(2):
        for c in range(6):
            x0, y0 = 120 + c * 300, 700 + r * 130
            rect(g, x0, y0, x0 + 280, y0 + 116,
                 fill=(190, 196, 130) if (r + c) % 2 else (178, 184, 118))
            g.line([(x0, y0 + 116), (x0 + 280, y0 + 116)], (146, 150, 96), 4)
    # 打ち杭 (水帳の札)
    kenchi_stakes(g, (200, 660, 700, 960), n=5, seed=2, s=1.3)
    kenchi_stakes(g, (1100, 660, 1700, 960), n=5, seed=3, s=1.3)
    # 検地帳を広げた卓
    rect(g, 880, 900, 1240, 960, fill=(120, 88, 62), outline=(88, 62, 42), owidth=4)
    g.rrect((920, 866, 1200, 930), 8, fill=(238, 232, 214), outline=(190, 182, 160), owidth=2.4)
    for k in range(3):
        g.line([(944, 886 + k * 16), (1176, 886 + k * 16)], with_alpha((150, 140, 120), 170), 2.6)
    # 村
    tile_roof_house(g, 1680, 780, 0.8, seed=4)
    tree(cv, 130, 1020, 1.2, kind="pine", leaf=(60, 112, 88), seed=5)
    grass_tufts(g, (0, 680, W, 1070), 80, (152, 150, 104), seed=45)
    birds(g, [(1240, 230), (1340, 270), (1300, 200)], 12, width=3.2)


def bg_azuchi_korea(cv):
    """朝鮮出兵 (文禄の役・渡海する船団)."""
    sky(cv, [(0.00, (130, 170, 200)), (0.55, (176, 198, 212)), (1.00, (232, 222, 204))])
    g = cv.g()
    clouds_row(cv, 160, 3, 40, seed=46, base=(210, 214, 216), under=(160, 164, 172), alpha=230)
    horizon = 430
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (134, 178, 202)), (0.4, (96, 150, 194)), (1, (64, 120, 168))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(47)
    for _ in range(26):
        yy = rnd.uniform(horizon + 10, H - 20)
        ln = rnd.uniform(30, 150)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((240, 250, 255), rnd.randint(50, 130)))
    # 出征の船団 (安宅船×3)
    atakebune(g, 420, 640, 0.62, seed=1)
    atakebune(g, 1080, 780, 0.9, seed=2)
    atakebune(g, 1700, 590, 0.5, flag=(238, 238, 236), seed=3)
    # 遠くの半島海岸
    g.poly([(0, horizon), (0, 350)] + [(x, 350 + 34 * math.sin(x * 0.006))
                                       for x in range(0, 501, 50)] + [(500, 428)], fill=(150, 168, 148))
    birds(g, [(800, 280), (900, 320), (860, 250)], 12, width=3.4)


def bg_azuchi_momoyama(cv):
    """桃山文化 (金屏風と聚楽第の華やぎ)."""
    cv.img.alpha_composite(gradient(cv.img.size,
                                    [(0, (74, 56, 52)), (0.6, (94, 72, 62)),
                                     (1, (120, 96, 78))], "v"))
    g = cv.g()
    # 床 (板の間)
    rect(g, 0, 780, W, H, fill=(140, 108, 80))
    rect(g, 30, 800, W - 30, H - 16, fill=(160, 126, 94))
    # 金屏風 (主役)
    gold_screen(g, 820, 500, 1.85, seed=2)
    # 脇飾り: 鎧と槍
    kabuto(g, 330, 660, 1.5)
    rect(g, 260, 760, 400, 800, fill=(96, 68, 48), outline=(70, 50, 36), owidth=3)
    rect(g, 1540, 700, 1680, 780, fill=(150, 118, 88), outline=(116, 90, 66), owidth=3)
    bow_and_arrows(g, 1610, 700, 0.9)
    # 胡粉の花瓶
    g.rrect((1180, 700, 1300, 800), 12, fill=(214, 208, 198), outline=(170, 164, 154),
            owidth=3)
    g.line([(1240, 700), (1240, 660)], (84, 66, 54), 4.4)
    for k in range(4):
        g.circle(1216 + k * 16, 646 - (k % 2) * 8, 7, fill=(226, 130, 150))
    # 桃山の金の光
    gl = radial((int(1600 * cv.ss), int(1000 * cv.ss)), (255, 214, 150),
                alpha_in=64, power=2.4)
    cv.img.alpha_composite(gl, (int(160 * cv.ss), int(80 * cv.ss)))


def bg_azuchi_chado(cv):
    """利休の茶室 (侘びの二畳間)."""
    cv.img.alpha_composite(gradient(cv.img.size,
                                    [(0, (94, 78, 66)), (0.6, (78, 64, 56)),
                                     (1, (58, 48, 44))], "v"))
    g = cv.g()
    # 躙口 (小さな入口から差す光)
    rect(g, 1180, 560, 1560, 1080, fill=(66, 56, 50))
    g.rrect((1210, 660, 1530, 1000), 10, fill=(214, 226, 222))
    rect(g, 1370, 660, 1388, 1000, fill=(66, 56, 50))
    gl = radial((int(900 * cv.ss), int(700 * cv.ss)), (240, 232, 210),
                alpha_in=80, power=2.2)
    cv.img.alpha_composite(gl, (int(600 * cv.ss), int(520 * cv.ss)))
    # 畳
    rect(g, 0, 840, W, H, fill=(110, 118, 90))
    rect(g, 40, 860, W - 40, H - 14, fill=(122, 130, 100))
    g.line([(0, 860), (W, 860)], (92, 98, 76), 5)
    # 床の間 (掛け軸と一輪挿し)
    rect(g, 320, 180, 560, 600, fill=(84, 68, 58), outline=(62, 50, 44), owidth=4)
    g.rrect((360, 220, 520, 520), 6, fill=(228, 222, 206), outline=(180, 172, 156), owidth=2.4)
    g.poly(qbez((392, 460), (416, 330), (456, 300), 10)
           + qbez((456, 300), (474, 380), (470, 460), 10), fill=None,
           outline=shade((96, 96, 108), 1.05), owidth=5)
    g.rrect((348, 600, 532, 628), 6, fill=(70, 56, 48))
    # 一輪の朝顔
    g.line([(398, 596), (394, 556)], (96, 108, 88), 3.4)
    g.ellipse((382, 540, 406, 562), fill=(150, 128, 190))
    # 炉と釜
    g.rrect((880, 780, 1060, 870), 14, fill=(64, 52, 46), outline=(48, 40, 36), owidth=3)
    g.ellipse((906, 786, 1034, 836), fill=(58, 50, 44))
    g.ellipse((924, 792, 1016, 828), fill=(74, 64, 56), outline=(52, 46, 42), owidth=3)
    smoke_wisp(g, 970, 760, 0.8, color=(170, 164, 156), alpha=110, seed=3)
    # 茶碗と棗
    g.ellipse((760, 800, 830, 836), fill=(150, 96, 76), outline=(116, 74, 60), owidth=2.4)
    g.ellipse((774, 800, 816, 818), fill=(178, 118, 92))
    g.rrect((660, 786, 712, 838), 8, fill=(180, 150, 110), outline=(146, 118, 84), owidth=2.2)
    # 窓の小さな光
    rect(g, 120, 260, 260, 380, fill=(64, 56, 52))
    rect(g, 132, 272, 248, 368, fill=with_alpha((222, 226, 220), 150))


def bg_azuchi_sunset(cv):
    """天下統一の夕暮れ (平和な城下町)."""
    sky(cv, P.SKY_EVENING)
    g = cv.g()
    sun(g, 1360, 400, 84, color=(244, 176, 110), core=(250, 214, 160), halo=0.55)
    clouds_row(cv, 210, 3, 42, seed=48, base=(226, 140, 118), under=(120, 70, 84), alpha=225)
    mountain_ridge(cv, 500, 100, ((84, 62, 82), (140, 96, 96)), seed=49, freq=1.7)
    # 城下町の屋根
    rnd = random.Random(50)
    x = 0
    while x < W:
        hw = rnd.uniform(110, 180)
        hh = rnd.uniform(38, 70)
        rect(g, x, 660 - hh, x + hw, 700, fill=(126, 92, 88))
        g.poly([(x - 8, 660 - hh), (x + hw + 8, 660 - hh), (x + hw * 0.72, 660 - hh - 26),
                (x + hw * 0.28, 660 - hh - 26)], fill=(112, 80, 78))
        x += hw + rnd.uniform(16, 58)
    # 大坂城のシルエット (遠景)
    tenshu(g, 620, 660, 0.34, tiers=5, gold_top=True, seed=2)
    rect(g, 0, 700, W, H, fill=(106, 84, 86))
    speckle(g, (0, 710, W, 1080), 130, [(94, 74, 78), (118, 94, 96)], r=(2, 6), seed=51)
    # 帰る牛車と人影
    ox_cart(g, 420, 1000, 0.7, seed=3)
    reeds_fg(cv, 1080, seed=52, color=(64, 48, 56), n=32, s=1.0)
    birds(g, [(700, 250), (820, 220), (780, 290), (1000, 240)], 12, width=4)


# ---------------------------------------------------------------- ポイント用タイムライン


def bg_timeline(cv):
    """ep06 用ポイント背景 — 桶狭間〜天下統一のタイムライン."""
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
    labels = ["桶狭間の戦い", "天下布武", "本能寺の変", "太閤検地・天下統一"]
    icon_y = band_y - 26
    for i, nx in enumerate(nodes):
        g.ellipse((nx - 130, icon_y - 220, nx + 130, icon_y + 6),
                  fill=with_alpha((255, 255, 255), 22))
        if i < 3:
            g.line([(nx + 64, band_y + 70), (nodes[i + 1] - 64, band_y + 70)],
                   with_alpha(P.UI_WHITE, 150), 6)
            g.poly([(nodes[i + 1] - 60, band_y + 70), (nodes[i + 1] - 84, band_y + 58),
                    (nodes[i + 1] - 84, band_y + 82)], fill=with_alpha(P.UI_WHITE, 150))
        g.circle(nx, band_y + 70, 46, fill=P.INDIGO, outline=P.YAMABUKI, owidth=6)
        g.circle(nx, band_y + 70, 9, fill=P.YAMABUKI)
        g.text((nx, band_y + 118), labels[i], 24, (214, 224, 248), "bold", "mm")
    samurai_rider(g, nodes[0], icon_y, 0.42, banner=False, flip=-1)
    tenshu(g, nodes[1], icon_y + 2, 0.3, tiers=4, gold_top=True, seed=1)
    campfire(g, nodes[2], icon_y - 24, 0.55, stones=False, seed=2)
    smoke_wisp(g, nodes[2] + 12, icon_y - 166, 0.9, color=(150, 146, 146), alpha=180, seed=3)
    kenchi_stakes(g, (nodes[3] - 70, icon_y - 40, nodes[3] + 70, icon_y - 4),
                  n=4, seed=4, s=1.0)
    gl = radial((int(1400 * cv.ss), int(900 * cv.ss)), (90, 120, 200),
                alpha_in=50, power=2.4)
    cv.img.alpha_composite(gl, (int(260 * cv.ss), int(160 * cv.ss)))

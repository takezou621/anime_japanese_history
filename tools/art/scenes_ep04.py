"""ep04 シーン背景 (鎌倉) — script.json の background 名と 1:1 対応.

源平合戦の海戦・鎌倉幕府・元寇・新仏教と禅 の空気感。テキストは焼き込まない。
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
from artlib.props import (amida, banner_pole, boat, campfire, dotaku, kabuto,
                          kamakura_goten, mongol_ship, ox_cart, pagoda,
                          samurai_rider, smoke_wisp, suzakumon, tile_roof_house,
                          torii, torch, war_boat, warehouse)
from artlib.props import rect
from scenes_ep01 import bow_and_arrows

W, H = 1920, 1080


def new_canvas():
    return Canvas(W, H, ss=2)


def _dust(g, box, n, seed=0, color=(188, 174, 148), alpha=110):
    rnd = random.Random(seed)
    for _ in range(n):
        px = rnd.uniform(*box[0::2])
        py = rnd.uniform(box[1], box[3])
        r_ = rnd.uniform(20, 70)
        g.ellipse((px - r_, py - r_ * 0.4, px + r_, py + r_ * 0.4),
                  fill=with_alpha(color, rnd.randint(40, alpha)))


# ---------------------------------------------------------------- 源平


def bg_kamakura_rebellion(cv):
    """保元・平治の乱 (炎上と武士の台頭)."""
    sky(cv, P.SKY_SUNSET)
    g = cv.g()
    clouds_row(cv, 200, 3, 44, seed=2, base=(180, 100, 96), under=(86, 50, 74), alpha=230)
    mountain_ridge(cv, 470, 130, ((66, 46, 74), (118, 72, 84)), seed=3, freq=1.7)
    ground(cv, 630, (118, 94, 88), dark=(94, 74, 70), curve=14, seed=4,
           speckles=150, speckle_colors=[(102, 82, 78), (134, 108, 100)],
           speckle_r=(2, 5))
    # 炎上する邸宅
    tile_roof_house(g, 520, 640, 0.9, seed=1)
    campfire(g, 560, 660, 1.3, seed=2)
    smoke_wisp(g, 590, 470, 1.8, color=(84, 60, 76), alpha=190, seed=3)
    campfire(g, 760, 650, 1.0, seed=4)
    # 逃げる人影と騎馬武士
    samurai_rider(g, 1380, 700, 0.72, banner=False, flip=-1)
    samurai_rider(g, 1620, 730, 0.6, banner=False, flip=-1, seed=5)
    # 手前の芒
    reeds_fg(cv, 1080, seed=6, color=(46, 36, 50), n=38, s=1.1)
    birds(g, [(500, 230), (620, 200), (580, 280)], 12, color=(44, 34, 48), width=4)


def bg_kamakura_harbor(cv):
    """由比ヶ浜の港 (海に開けた鎌倉)."""
    sky(cv, P.SKY_KAMAKURA_DAY)
    g = cv.g()
    sun(g, 400, 180, 56, halo=0.45)
    clouds_row(cv, 150, 3, 34, seed=7)
    # 左右に切通しの山 (鎌倉の谷あい)
    g.poly([(0, 1080), (0, 420)] + [(x, 420 + 70 * math.sin(x * 0.005))
                                    for x in range(0, 521, 50)] + [(520, 500), (330, 1080)],
           fill=(140, 148, 112))
    g.poly([(W, 1080), (W, 400)] + [(x, 400 + 66 * math.sin(x * 0.005 + 2))
                                    for x in range(1920, 1300, -50)] + [(1320, 490), (1580, 1080)],
           fill=(136, 144, 108))
    horizon = 470
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (138, 188, 214)), (0.4, (98, 158, 202)), (1, (66, 126, 176))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(8)
    for _ in range(26):
        yy = rnd.uniform(horizon + 10, 720)
        ln = rnd.uniform(30, 150)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((240, 250, 255), rnd.randint(50, 130)))
    # 港の船
    war_boat(g, 900, 660, 0.55, banner=True, seed=1)
    boat(g, 1350, 780, 0.85, oars=2, figure=True, seed=2)
    war_boat(g, 1600, 560, 0.34, banner=False, seed=3)
    # 浜
    beach = [(0, 760)] + [(x, 760 + math.sin(x * 0.004 + 1) * 18 + x * 0.02)
                          for x in range(0, W + 1, 120)] + [(W, 1080), (0, 1080)]
    g.poly(beach, fill=(224, 204, 166))
    g.line(beach[:14], (200, 180, 144), 5)
    speckle(g, (0, 810, W, 1080), 200, [(208, 188, 152), (240, 226, 196), (186, 166, 132)],
            r=(1.6, 4.2), seed=9)
    for i in range(3):
        yy = 775 + i * 16
        g.arc((-100, yy - 14, W + 100, yy + 40), 190, 350,
              with_alpha((255, 255, 255), 150 - i * 40), 7 - i * 1.6)
    grass_tufts(g, (0, 860, W, 1070), 60, (152, 172, 112), seed=10)
    birds(g, [(800, 240), (900, 280), (860, 210), (1200, 260)], 13, width=3.4)


def bg_kamakura_uprising(cv):
    """源頼朝の挙兵 (暁の誓い)."""
    sky(cv, [(0.00, (56, 60, 96)), (0.45, (140, 116, 140)), (0.70, (226, 156, 120)),
             (1.00, (246, 208, 160))])
    g = cv.g()
    stars(g, (40, 40, 1200, 240), 40, seed=11)
    mountain_ridge(cv, 470, 130, ((70, 62, 92), (130, 100, 116)), seed=12, freq=1.8)
    ground(cv, 630, (128, 108, 100), dark=(102, 86, 82), curve=14, seed=13,
           speckles=150, speckle_colors=[(112, 94, 88), (144, 122, 112)],
           speckle_r=(2, 5))
    # 白旗 (源氏) の集団と松明
    for i in range(5):
        banner_pole(g, 380 + i * 150, 700 + (i % 2) * 16, 0.8, flag=(240, 240, 238))
        torch(g, 300 + i * 170, 760, 0.85)
    samurai_rider(g, 1080, 760, 0.8, flip=-1)
    samurai_rider(g, 1320, 790, 0.66, banner=False, flip=-1)
    campfire(g, 1600, 780, 0.9, seed=14)
    # 朝霧
    g.ellipse((-100, 640, W + 100, 740), fill=with_alpha((226, 210, 190), 90))
    reeds_fg(cv, 1080, seed=15, color=(50, 42, 54), n=34, s=1.05)
    birds(g, [(700, 230), (800, 200), (760, 270)], 11, color=(48, 40, 56), width=3.6)


def bg_kamakura_seabattle(cv):
    """壇ノ浦の海戦 (燃える船・1185)."""
    sky(cv, P.SKY_SUNSET)
    g = cv.g()
    clouds_row(cv, 180, 3, 46, seed=16, base=(190, 100, 96), under=(88, 52, 74), alpha=235)
    horizon = 430
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (150, 110, 140)), (0.35, (120, 84, 124)),
                         (0.7, (96, 76, 118)), (1, (130, 84, 104))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(17)
    for _ in range(24):
        yy = rnd.uniform(horizon + 10, H - 24)
        ln = rnd.uniform(30, 150)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((250, 214, 190), rnd.randint(50, 130)))
    # 太陽の反射帯
    for i in range(7):
        yy = horizon + 26 + i * 84
        ln = 240 - i * 20
        g.rrect((1380 - ln / 2 + math.sin(i * 2.2) * 54, yy,
                 1380 + ln / 2 + math.sin(i * 2.2) * 54, yy + 10), 5,
                fill=with_alpha((255, 206, 150), 110 - i * 10))
    # 戦船団 (炎上)
    war_boat(g, 420, 700, 1.0, onfire=False, seed=1)
    war_boat(g, 960, 860, 1.25, onfire=True, seed=2)
    war_boat(g, 1520, 640, 0.8, onfire=True, banner=False, seed=3)
    # 矢の雨 (アーチを描く流矢)
    for (ax, ay, adx) in [(700, 420, 60), (1100, 400, 80), (500, 460, 50)]:
        g.line(qbez((ax, ay), (ax + adx, ay + 90), (ax + adx * 2, ay + 240), 12),
               with_alpha((90, 70, 80), 200), 2.6)
    smoke_wisp(g, 1240, 520, 1.6, color=(70, 58, 70), alpha=190, seed=18)
    smoke_wisp(g, 1760, 560, 1.2, color=(70, 58, 70), alpha=170, seed=19)
    birds(g, [(700, 240), (820, 210), (780, 290)], 11, color=(46, 34, 48), width=4)


def bg_kamakura_shogunate(cv):
    """鎖られた谷の幕府 (鎌倉の御所と町)."""
    sky(cv, P.SKY_KAMAKURA_DAY)
    g = cv.g()
    sun(g, 1500, 180, 54, halo=0.45)
    clouds_row(cv, 140, 3, 32, seed=20)
    # 切通しの山 (両側)
    g.poly([(0, 1080), (0, 260)] + [(x, 260 + 60 * math.sin(x * 0.004))
                                    for x in range(0, 601, 50)] + [(600, 380), (450, 1080)],
           fill=(128, 138, 104))
    g.poly([(W, 1080), (W, 240)] + [(x, 240 + 60 * math.sin(x * 0.004 + 1.5))
                                    for x in range(1920, 1320, -50)] + [(1320, 370), (1500, 1080)],
           fill=(124, 134, 100))
    forest_band(cv, 420, 6, (0.6, 1.0), leaf=(88, 132, 96), seed=21)
    ground(cv, 520, (188, 184, 132), dark=(156, 152, 106), curve=12, seed=22,
           speckles=150, speckle_colors=[(168, 164, 114), (202, 198, 146)],
           speckle_r=(2, 5))
    # 御所
    kamakura_goten(g, 960, 700, 0.9, seed=2)
    # 町並み
    tile_roof_house(g, 260, 820, 0.9, seed=3)
    tile_roof_house(g, 1620, 830, 0.95, seed=4)
    tile_roof_house(g, 120, 950, 0.7, seed=5)
    tile_roof_house(g, 1810, 960, 0.72, seed=6)
    # 通る騎馬武士
    samurai_rider(g, 620, 1000, 0.72, flip=-1)
    # 並木と道
    g.poly([(830, 1080), (1090, 1080), (1000, 700), (920, 700)], fill=(206, 192, 156))
    grass_tufts(g, (0, 720, W, 1080), 90, (150, 152, 100), seed=23)
    birds(g, [(640, 210), (740, 250), (700, 180)], 12, width=3.2)


def bg_kamakura_oath(cv):
    """御家人の起請文 (八幡宮の誓い)."""
    sky(cv, P.SKY_KAMAKURA_DAY)
    g = cv.g()
    sun(g, 360, 190, 54, halo=0.45)
    clouds_row(cv, 150, 3, 32, seed=24)
    mountain_ridge(cv, 440, 120, ((108, 134, 128), (168, 186, 162)), seed=25, freq=1.9)
    ground(cv, 640, (182, 180, 128), dark=(150, 148, 104), curve=14, seed=26,
           speckles=150, speckle_colors=[(162, 160, 110), (196, 194, 142)],
           speckle_r=(2, 5))
    # 参道
    g.poly([(820, 1080), (1120, 1080), (1010, 640), (930, 640)], fill=(210, 196, 158))
    # 八幡宮 (鳥居+拝殿)
    torii(g, 960, 700, 0.95)
    rect(g, 820, 470, 1100, 640, fill=(188, 150, 108), outline=shade((152, 122, 88), 0.8),
         owidth=3)
    g.poly([(800, 470), (1120, 470), (1080, 400), (840, 400)], fill=(150, 116, 84),
           outline=(118, 92, 66), owidth=3)
    g.rect(g, 930, 540, 990, 640, fill=(72, 58, 50))
    # 灯籠
    for lx in (760, 1160):
        g.rrect((lx - 14, 600, lx + 14, 660), 6, fill=(126, 120, 112),
                outline=(96, 90, 84), owidth=2.4)
        g.rrect((lx - 20, 584, lx + 20, 604), 8, fill=shade((126, 120, 112), 0.85))
    # 誓紙を広げた卓
    rect(g, 560, 900, 900, 950, fill=(120, 88, 62), outline=(88, 62, 42), owidth=4)
    rect(g, 584, 950, 876, 1000, fill=(104, 76, 52))
    for (px, py) in [(600, 862), (680, 874), (770, 858)]:
        g.poly([(px, py), (px + 110, py + 4), (px + 104, py + 64), (px - 4, py + 58)],
               fill=(240, 234, 216), outline=(190, 182, 160), owidth=2.4)
        g.line([(px + 16, py + 18), (px + 88, py + 22)], with_alpha((140, 128, 108), 190), 2.6)
        g.line([(px + 16, py + 34), (px + 76, py + 38)], with_alpha((140, 128, 108), 190), 2.6)
    # 桜の名所風の木
    tree(cv, 250, 1020, 1.3, kind="oak", leaf=(150, 168, 120), seed=27)
    tree(cv, 1690, 1010, 1.25, kind="pine", leaf=(60, 112, 88), seed=28)
    grass_tufts(g, (0, 700, W, 1070), 90, (150, 152, 100), seed=29)
    birds(g, [(1240, 240), (1340, 280), (1300, 210)], 12, width=3.2)


def bg_kamakura_shokyu(cv):
    """承久の乱 (進軍の大行列)."""
    sky(cv, [(0.00, (110, 130, 168)), (0.5, (178, 150, 150)), (1.00, (236, 190, 148))])
    g = cv.g()
    clouds_row(cv, 170, 3, 42, seed=30, base=(214, 160, 140), under=(130, 90, 104), alpha=225)
    mountain_ridge(cv, 430, 120, ((92, 86, 108), (150, 120, 122)), seed=31, freq=1.7)
    ground(cv, 600, (172, 158, 116), dark=(140, 128, 94), curve=12, seed=32,
           speckles=150, speckle_colors=[(152, 140, 100), (186, 172, 130)],
           speckle_r=(2, 5))
    # 進軍の列 (手前→奥)
    for i in range(6):
        samurai_rider(g, 300 + i * 240, 900 - i * 26, 0.62 - i * 0.05,
                      banner=(i % 2 == 0), flip=-1, seed=33 + i)
    # 砂塵
    _dust(g, (200, 0, 1500, 1040), 26, seed=34)
    # 旗の列
    for i in range(4):
        banner_pole(g, 1620 + i * 70, 640 + (i % 2) * 14, 0.5, flag=P.SHU)
    reeds_fg(cv, 1080, seed=35, color=(64, 54, 60), n=30, s=1.0)
    birds(g, [(900, 220), (1000, 260), (960, 190)], 11, width=3.4)


def bg_kamakura_lawbook(cv):
    """御成敗式目 (政所の執務室)."""
    cv.img.alpha_composite(gradient(cv.img.size,
                                    [(0, (216, 198, 172)), (0.6, (198, 180, 154)),
                                     (1, (150, 134, 112))], "v"))
    g = cv.g()
    # 床
    rect(g, 0, 720, W, H, fill=(150, 122, 96))
    rect(g, 40, 740, W - 40, H - 20, fill=(170, 140, 110))
    # 障子
    for wx in (1280, 1640):
        rect(g, wx, 120, wx + 220, 600, fill=(206, 196, 176), outline=(150, 138, 116), owidth=6)
        rect(g, wx + 14, 134, wx + 206, 586, fill=(214, 220, 214))
        g.rect(g, wx + 14, 134, wx + 206, 340, fill=(198, 210, 202))
        g.poly(blob_pts(wx + 70, 210, 52, 30, seed=int(wx), wobble=0.16), fill=(156, 190, 156))
        for k in range(1, 6):
            g.line([(wx + 14, 134 + k * 75), (wx + 206, 134 + k * 75)],
                   with_alpha((150, 138, 116), 170), 3)
        g.rect(g, wx + 100, 134, wx + 118, 586, fill=(206, 196, 176))
    # 掛軸の代わりに板札 (法令の板)
    for k, px in enumerate((620, 760)):
        rect(g, px, 150, px + 90, 560, fill=(202, 178, 138), outline=(160, 138, 104),
             owidth=3.4)
        for kk in range(6):
            g.line([(px + 12, 190 + kk * 58), (px + 78, 190 + kk * 58)],
                   with_alpha((120, 100, 78), 200), 3)
    # 卓と式目の巻子
    rect(g, 240, 770, 1000, 820, fill=(116, 84, 58), outline=(86, 62, 42), owidth=4)
    rect(g, 264, 820, 976, 872, fill=(100, 72, 50))
    for (sx_, sw_) in [(300, 220), (560, 260)]:
        g.rrect((sx_, 726, sx_ + sw_, 786), 8, fill=(238, 232, 214),
                outline=(190, 182, 160), owidth=2.4)
        g.rrect((sx_ - 10, 718, sx_ + 8, 794), 6, fill=(88, 64, 50))
        g.rrect((sx_ + sw_ - 8, 718, sx_ + sw_ + 10, 794), 6, fill=(88, 64, 50))
        for kk in range(4):
            g.line([(sx_ + 24, 742 + kk * 12), (sx_ + sw_ - 24, 742 + kk * 12)],
                   with_alpha((150, 140, 120), 170), 2.4)
    # 兜飾り (甲冑の置物)
    stand_x = 1200
    rect(g, stand_x - 60, 700, stand_x + 60, 740, fill=(96, 68, 48),
         outline=(70, 50, 36), owidth=3)
    kabuto(g, stand_x, 660, 1.05)
    # 灯明
    g.rrect((440, 690, 480, 750), 6, fill=(110, 104, 96), outline=(84, 80, 74), owidth=2.4)
    gl = radial((int(300 * cv.ss), int(300 * cv.ss)), (255, 210, 140), alpha_in=110, power=2.2)
    cv.img.alpha_composite(gl, (int(310 * cv.ss), int(560 * cv.ss)))
    smoke_wisp(g, 460, 680, 0.7, color=(180, 174, 164), alpha=120, seed=36)


def bg_kamakura_mongol(cv):
    """元寇 (防人の浜と蒙古の軍船・嵐)."""
    sky(cv, P.SKY_MONGOL_STORM)
    g = cv.g()
    clouds_row(cv, 160, 4, 50, seed=37, base=(96, 100, 108), under=(56, 60, 70), alpha=240)
    mountain_ridge(cv, 420, 100, ((58, 66, 78), (96, 104, 114)), seed=38, freq=1.8)
    horizon = 470
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (110, 128, 140)), (0.4, (84, 100, 116)), (1, (62, 78, 96))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(39)
    for _ in range(24):
        yy = rnd.uniform(horizon + 10, H - 20)
        ln = rnd.uniform(30, 140)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((214, 222, 228), rnd.randint(50, 120)))
    # 蒙古軍船 (3隻) と石弾
    mongol_ship(g, 500, 560, 0.5, throwing=False, seed=1)
    mongol_ship(g, 1360, 590, 0.62, throwing=True, seed=2)
    mongol_ship(g, 1780, 520, 0.4, throwing=False, seed=3)
    # 防塁 (石築地)
    rect(g, 0, 820, W, 900, fill=(148, 144, 134))
    for k in range(40):
        px = k * 48
        rect(g, px, 820 + (k % 2) * 6, px + 46, 896, fill=shade((148, 144, 134), 0.9),
             outline=(120, 116, 108), owidth=2)
    g.line([(0, 820), (W, 820)], (124, 120, 112), 5)
    # 浜と防戦の騎馬武士
    rect(g, 0, 900, W, H, fill=(150, 146, 130))
    speckle(g, (0, 910, W, 1080), 130, [(136, 132, 118), (162, 158, 144)], r=(1.6, 4), seed=40)
    samurai_rider(g, 420, 1010, 0.8, flip=-1)
    samurai_rider(g, 680, 1030, 0.66, banner=False, flip=-1, seed=41)
    samurai_rider(g, 960, 1000, 0.6, banner=False, flip=-1, seed=42)
    # 嵐の雨筋
    for _ in range(60):
        rx = rnd.uniform(0, W)
        ry = rnd.uniform(60, 1060)
        g.line([(rx, ry), (rx - 10, ry + 26)], with_alpha((190, 198, 206), 90), 1.8)
    # 遠くの稲光
    g.poly([(1500, 150), (1560, 260), (1520, 260), (1580, 380)], fill=with_alpha((250, 250, 230), 200))


def bg_kamakura_tokuso(cv):
    """得宗専制 (北条氏の御所・夕餉の緊張)."""
    sky(cv, P.SKY_HEIAN_DUSK)
    g = cv.g()
    clouds_row(cv, 190, 3, 44, seed=43, base=(180, 100, 100), under=(86, 50, 74), alpha=230)
    mountain_ridge(cv, 460, 110, ((56, 44, 74), (106, 66, 86)), seed=44, freq=1.7)
    ground(cv, 620, (110, 90, 90), dark=(88, 72, 74), curve=12, seed=45,
           speckles=140, speckle_colors=[(96, 78, 80), (124, 102, 102)],
           speckle_r=(2, 5))
    # 御所 (夕照)
    kamakura_goten(g, 960, 720, 1.0, seed=2)
    # 旗を赤に替えたいので上書きで小さい北条旗
    for fx in (660, 1260):
        g.line([(fx, 720), (fx, 560)], P.WOOD_D, 8 * 0.85)
        g.poly([(fx, 560), (fx + 52, 570), (fx, 582)], fill=P.SHU,
               outline=shade(P.SHU, 0.72), owidth=2)
    # 松明
    torch(g, 420, 900, 1.0)
    torch(g, 1500, 900, 1.0)
    reeds_fg(cv, 1080, seed=46, color=(40, 30, 44), n=32, s=1.0)
    birds(g, [(560, 240), (680, 210), (640, 280)], 11, color=(40, 30, 44), width=4)


def bg_kamakura_jodo(cv):
    """新仏教の広がり (念仏の集いと阿弥陀)."""
    sky(cv, [(0.00, (36, 40, 76)), (0.5, (72, 66, 110)), (1.00, (120, 96, 130))])
    g = cv.g()
    stars(g, (40, 40, 1880, 500), 110, seed=47, sparkle=8)
    rnd = random.Random(48)
    for _ in range(90):
        px, py = rnd.uniform(0, W), rnd.uniform(60, 900)
        g.circle(px, py, rnd.uniform(1.2, 3), fill=with_alpha(P.GOLD, rnd.randint(80, 200)))
    mountain_ridge(cv, 520, 90, ((30, 34, 64), (52, 52, 88)), seed=49, freq=1.8)
    # 山上の阿弥陀
    amida(g, 960, 640, 1.05, seed=2)
    # 金の雲
    for (cx0, cy0, rx, ry) in [(420, 520, 260, 50), (1460, 500, 260, 50)]:
        g.poly(blob_pts(cx0, cy0, rx, ry, seed=int(cx0), wobble=0.2),
               fill=with_alpha((222, 186, 110), 140))
    # 説法を聴く集団のシルエット (畦に座る)
    for k in range(9):
        px = 240 + k * 180 + rnd.uniform(-24, 24)
        py = 950 + rnd.uniform(-20, 40)
        g.circle(px, py - 46, 16, fill=(40, 36, 56))
        g.poly([(px - 22, py - 32), (px + 22, py - 32), (px + 16, py + 14),
                (px - 16, py + 14)], fill=(40, 36, 56))
    g.ellipse((-200, 1000, W + 200, 1180), fill=with_alpha((64, 56, 96), 170))
    for _ in range(14):
        px, py = rnd.uniform(0, W), rnd.uniform(1020, 1066)
        g.rrect((px, py, px + rnd.uniform(30, 80), py + 4), 2,
                fill=with_alpha((244, 212, 140), rnd.randint(60, 140)))


def bg_kamakura_zen(cv):
    """禅寺 (唐様の山門と石庭の朝)."""
    sky(cv, [(0.00, (150, 176, 196)), (0.55, (200, 212, 216)), (1.00, (238, 238, 226))])
    g = cv.g()
    clouds_row(cv, 150, 2, 30, seed=50, base=(232, 236, 238), under=(178, 186, 192), alpha=220)
    mountain_ridge(cv, 400, 110, ((96, 118, 124), (150, 168, 160)), seed=51, freq=1.8)
    forest_band(cv, 560, 8, (0.5, 0.9), leaf=(74, 120, 100), seed=52)
    ground(cv, 600, (176, 176, 140), dark=(146, 146, 112), curve=12, seed=53,
           speckles=140, speckle_colors=[(156, 156, 120), (190, 190, 154)],
           speckle_r=(2, 5))
    # 霧
    g.ellipse((-100, 540, W + 100, 660), fill=with_alpha((226, 232, 232), 110))
    # 禅寺
    from artlib.props import zen_temple
    zen_temple(g, 960, 900, 1.0, seed=2)
    # 樹
    tree(cv, 160, 1020, 1.35, kind="pine", leaf=(52, 100, 82), seed=3)
    tree(cv, 1770, 1010, 1.25, kind="pine", leaf=(52, 100, 82), seed=4)
    grass_tufts(g, (0, 680, W, 1070), 80, (150, 150, 108), seed=54)


# ---------------------------------------------------------------- ポイント用タイムライン


def bg_timeline(cv):
    """ep04 用ポイント背景 — 平氏〜元寇のタイムライン."""
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
    labels = ["平氏政権", "鎌倉幕府", "承久の乱", "元寇"]
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
    war_boat(g, nodes[0], icon_y - 40, 0.42, banner=False, seed=1)
    kabuto(g, nodes[1], icon_y - 60, 0.9)
    banner_pole(g, nodes[2] - 46, icon_y - 4, 0.5, flag=P.SHU)
    torch(g, nodes[2] + 52, icon_y - 2, 0.42)
    mongol_ship(g, nodes[3], icon_y - 46, 0.32, throwing=False, seed=2)
    gl = radial((int(1400 * cv.ss), int(900 * cv.ss)), (90, 120, 200),
                alpha_in=50, power=2.4)
    cv.img.alpha_composite(gl, (int(260 * cv.ss), int(160 * cv.ss)))

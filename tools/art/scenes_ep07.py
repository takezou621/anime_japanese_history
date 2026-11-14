"""ep07 シーン背景 (江戸前半) — script.json の background 名と 1:1 対応.

家康と江戸幕府・参勤交代・キリシタン弾圧と島原の乱・鎖国と出島・元禄文化。
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
                           stars, sun, tree, light_shafts)
from artlib.props import (boat, campfire, cross_flag, daimyo_procession,
                          edo_castle, fan_dejima, hara_castle, japan_map_trade,
                          kabuto, nobori, osaka_castle, palisade, rect,
                          rice_paddy, sakoku_door, samurai_rider, smoke_wisp,
                          suzakumon, tenshu, tile_roof_house, torii, torch, war_boat)
from scenes_ep01 import bow_and_arrows

W, H = 1920, 1080


def new_canvas():
    return Canvas(W, H, ss=2)


def fuji(g, x, y, s, col=(110, 128, 150), snow=(240, 244, 248)):
    peak = y - 300 * s
    g.poly([(x - 210 * s, y), (x - 86 * s, peak + 4 * s), (x + 86 * s, peak + 4 * s),
            (x + 210 * s, y)], fill=col)
    cap = [(x - 86 * s, peak + 4 * s)]
    for k in range(9):
        px = x - 86 * s + 172 * s * (k + 1) / 9
        py = peak + 4 * s + 62 * s * (k + 1) / 9
        cap.append((px, py + (8 * s if k % 2 == 0 else 0)))
    cap.append((x + 86 * s, peak + 4 * s))
    g.poly(cap, fill=snow)


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


# ---------------------------------------------------------------- 幕府


def bg_edo_shogunate(cv):
    """家康と江戸城 (幕府のはじまり)."""
    sky(cv, P.SKY_EDO_DAY)
    g = cv.g()
    sun(g, 1440, 180, 56, halo=0.45)
    clouds_row(cv, 140, 3, 32, seed=2)
    mountain_ridge(cv, 400, 90, ((106, 138, 128), (166, 188, 164)), seed=3, freq=1.8)
    ground(cv, 560, (184, 180, 130), dark=(152, 148, 104), curve=12, seed=4,
           speckles=150, speckle_colors=[(164, 160, 112), (198, 194, 144)],
           speckle_r=(2, 5))
    edo_castle(g, 1200, 640, 0.78, seed=2)
    # 家康と家臣の騎馬 (手前)
    samurai_rider(g, 480, 950, 0.85, flip=-1)
    samurai_rider(g, 740, 1000, 0.66, banner=False, flip=-1, seed=5)
    samurai_rider(g, 300, 1010, 0.6, banner=False, flip=-1, seed=6)
    nobori(g, 150, 960, 0.85, col=(238, 238, 236))
    grass_tufts(g, (0, 700, W, 1070), 80, (152, 150, 104), seed=7)
    birds(g, [(520, 230), (620, 270), (580, 200)], 12, width=3.2)


def bg_edo_government(cv):
    """幕府の組織 (評定所の執務)."""
    cv.img.alpha_composite(gradient(cv.img.size,
                                    [(0, (216, 198, 172)), (0.6, (198, 180, 154)),
                                     (1, (150, 134, 112))], "v"))
    g = cv.g()
    rect(g, 0, 700, W, H, fill=(150, 122, 96))
    rect(g, 40, 720, W - 40, H - 20, fill=(170, 140, 110))
    # 障子
    for wx in (1300, 1620):
        rect(g, wx, 120, wx + 220, 620, fill=(206, 196, 176), outline=(150, 138, 116), owidth=6)
        rect(g, wx + 14, 134, wx + 206, 606, fill=(216, 222, 216))
        for k in range(1, 7):
            g.line([(wx + 14, 134 + k * 78), (wx + 206, 134 + k * 78)],
                   with_alpha((150, 138, 116), 170), 3)
        rect(g, wx + 100, 134, wx + 118, 606, fill=(206, 196, 176))
    # 評定所の長机と文書
    for row, yy in ((0, 760), (1, 900)):
        for k in range(3):
            tx = 260 + k * 560
            rect(g, tx, yy, tx + 380, yy + 56, fill=(116, 84, 58),
                 outline=(86, 62, 42), owidth=4)
            rect(g, tx + 20, yy + 56, tx + 360, yy + 96, fill=(100, 72, 50))
            for kk in range(3):
                g.rrect((tx + 44 + kk * 110, yy - 34, tx + 130 + kk * 110, yy + 6), 4 * 1,
                        fill=(238, 232, 214), outline=(190, 182, 160), owidth=2)
                g.line([(tx + 54 + kk * 110, yy - 22), (tx + 122 + kk * 110, yy - 22)],
                       with_alpha((150, 140, 120), 170), 2.4)
    # 目付の上座 (少し高い所)
    rect(g, 760, 700, 1160, 740, fill=(96, 68, 48), outline=(70, 50, 36), owidth=4)
    kabuto(g, 960, 640, 1.0)
    # 灯明
    for lx in (200, 960, 1720):
        g.rrect((lx - 16, 560, lx + 16, 640), 8, fill=(110, 104, 96),
                outline=(84, 80, 74), owidth=2.4)
        gl = radial((int(240 * cv.ss), int(240 * cv.ss)), (255, 210, 140),
                    alpha_in=100, power=2.2)
        cv.img.alpha_composite(gl, (int((lx - 120) * cv.ss), int((480) * cv.ss)))


def bg_edo_daimyo(cv):
    """大名の領国 (高い石垣の馆と城下町)."""
    sky(cv, P.SKY_EDO_DAY)
    g = cv.g()
    sun(g, 380, 190, 54, halo=0.45)
    clouds_row(cv, 150, 3, 32, seed=8)
    mountain_ridge(cv, 440, 120, ((106, 136, 130), (168, 188, 164)), seed=9, freq=1.9)
    ground(cv, 620, (180, 176, 122), dark=(148, 144, 100), curve=12, seed=10,
           speckles=150, speckle_colors=[(160, 156, 108), (194, 190, 138)],
           speckle_r=(2, 5))
    # 大名の馆 (石垣+門+天守)
    rect(g, 900, 640, 1560, 720, fill=shade(P.ISHIGAKI, 0.94),
         outline=shade(P.ISHIGAKI, 0.72), owidth=3)
    tenshu(g, 1280, 640, 0.5, tiers=4, gold_top=False, seed=2)
    nobori(g, 940, 760, 0.8, col=(90, 110, 170))
    nobori(g, 1520, 760, 0.8, col=P.SHU)
    # 城下町
    for (hx, hy, hs) in [(300, 800, 0.95), (500, 756, 0.78), (680, 726, 0.64),
                         (1620, 770, 0.9), (1440, 748, 0.7)]:
        tile_roof_house(g, hx, hy, hs, seed=int(hx))
    rice_paddy(cv, 900, 1080, [(206, 222, 228), (168, 202, 216)], seed=11, rows_seed=8)
    grass_tufts(g, (0, 680, 900, 900), 70, (146, 148, 98), seed=12)
    birds(g, [(820, 230), (920, 270), (880, 200)], 12, width=3.2)


def bg_edo_sankinkotai(cv):
    """参勤交代の大名行列 (東海道と富士)."""
    sky(cv, P.SKY_EDO_DAY)
    g = cv.g()
    sun(g, 1500, 160, 52, halo=0.45)
    clouds_row(cv, 140, 3, 30, seed=13)
    # 富士山 (左奥・山並みの手前に描き麓を隠す)
    fuji(g, 560, 560, 0.85)
    mountain_ridge(cv, 560, 70, ((124, 146, 128), (176, 194, 172)), seed=14, freq=2.2)
    ground(cv, 560, (188, 180, 132), dark=(156, 148, 106), curve=12, seed=15,
           speckles=140, speckle_colors=[(168, 160, 114), (202, 194, 146)],
           speckle_r=(2, 5))
    # 東海道の松並木
    for k in range(5):
        tree(cv, 120 + k * 420, 1000, 1.15, kind="pine", leaf=(60, 112, 88), seed=16 + k)
    # 街道と大名行列
    road = [(0, 900), (W, 900), (W, 1000), (0, 1000)]
    g.poly([(0, 880), (W, 880), (W, 1000), (0, 1000)], fill=(212, 198, 158))
    g.line([(0, 884), (W, 884)], (182, 168, 130), 4)
    daimyo_procession(g, 960, 948, 1.12, seed=2)
    # 一里塚っぽい盛り土
    for kx in (260, 1700):
        g.ellipse((kx - 60, 830, kx + 60, 884), fill=(158, 148, 108))
        tree(cv, kx, 842, 0.7, kind="pine", leaf=(58, 108, 86), seed=17 + kx)
    birds(g, [(1200, 200), (1300, 240), (1260, 170)], 12, width=3.2)


def bg_edo_kirishitan(cv):
    """キリシタンの伝来 (西洋の宣教師と信徒)."""
    sky(cv, [(0.00, (150, 170, 196)), (0.55, (198, 206, 210)), (1.00, (236, 226, 206))])
    g = cv.g()
    clouds_row(cv, 150, 3, 32, seed=18)
    mountain_ridge(cv, 460, 110, ((110, 128, 134), (164, 182, 176)), seed=19, freq=1.9)
    ground(cv, 620, (170, 168, 120), dark=(140, 138, 98), curve=12, seed=20,
           speckles=150, speckle_colors=[(150, 148, 104), (184, 182, 134)],
           speckle_r=(2, 5))
    # 南蛮寺風の教会
    rect(g, 1200, 380, 1560, 700, fill=(206, 198, 182), outline=(164, 156, 140), owidth=3.4)
    g.poly([(1180, 380), (1580, 380), (1500, 288), (1260, 288)], fill=(96, 86, 78),
           outline=(72, 64, 58), owidth=3)
    g.rrect((1340, 470, 1420, 700), 8 * 0.5, fill=(90, 80, 72))
    g.rrect((1240, 470, 1300, 560), 6 * 0.5, fill=(150, 160, 172))
    g.rrect((1460, 470, 1520, 560), 6 * 0.5, fill=(150, 160, 172))
    # 十字架 (屋根の上)
    g.line([(1370, 288), (1370, 218)], (86, 74, 66), 8)
    g.line([(1344, 246), (1396, 246)], (86, 74, 66), 8)
    # 宣教師 (黒い法衣) と信徒
    px = 480
    g.rrect((px - 30, 700, px + 30, 940), 14, fill=(52, 48, 56), outline=(40, 36, 44), owidth=2.4)
    g.circle(px, 668, 24, fill=P.SKIN, outline=P.OUTLINE, owidth=2.4)
    g.rrect((px - 18, 640, px + 18, 676), 8, fill=(64, 58, 66))
    g.line([(px + 30, 720), (px + 52, 780)], (74, 66, 58), 5)
    for k in range(4):
        jx = px - 160 + k * 90
        jy = 980
        g.circle(jx, jy - 52, 13, fill=(96, 78, 66))
        g.poly([(jx - 16, jy - 40), (jx + 16, jy - 40), (jx + 11, jy + 4),
                (jx - 11, jy + 4)], fill=(120, 100, 84))
    # 十字の小さな礼拝堂 (左奥)
    rect(g, 200, 560, 340, 700, fill=(196, 188, 172), outline=(158, 150, 134), owidth=3)
    g.poly([(190, 560), (350, 560), (310, 492), (230, 492)], fill=(92, 82, 74),
           outline=(70, 62, 56), owidth=2.6)
    g.line([(270, 492), (270, 430)], (86, 74, 66), 6)
    g.line([(248, 456), (292, 456)], (86, 74, 66), 6)
    grass_tufts(g, (0, 680, W, 1070), 80, (150, 148, 104), seed=21)
    birds(g, [(700, 230), (800, 270), (760, 200)], 12, width=3.2)


def bg_edo_shimabara(cv):
    """島原の乱 (1637・原城の籠城と幕府軍)."""
    sky(cv, P.SKY_SHIMABARA_FIRE)
    g = cv.g()
    stars(g, (40, 40, 1500, 300), 40, seed=22)
    ground(cv, 640, (92, 76, 84), dark=(74, 60, 70), curve=12, seed=23,
           speckles=140, speckle_colors=[(80, 64, 76), (104, 84, 94)],
           speckle_r=(2, 5))
    # 原城 (籠城する一揆勢)
    hara_castle(g, 640, 620, 0.9, seed=2)
    campfire(g, 640, 560, 0.9, stones=False, seed=24)
    smoke_wisp(g, 700, 430, 1.5, color=(70, 58, 72), alpha=190, seed=25)
    # 幕府軍の陣 (右: 幕+旗+提灯)
    for bx in (1300, 1500, 1700):
        rect(g, bx - 70, 600, bx + 70, 680, fill=(214, 202, 172),
             outline=(168, 154, 122), owidth=2.4)
        g.poly([(bx - 78, 600), (bx + 78, 600), (bx + 60, 574), (bx - 60, 574)],
               fill=(170, 90, 76), outline=(132, 96, 78), owidth=2)
    for i in range(4):
        nobori(g, 1240 + i * 160, 760, 0.8, col=(238, 238, 236), seed=26 + i)
    torch(g, 1200, 900, 1.0)
    torch(g, 1760, 900, 1.0)
    # 手前の松明と芒
    reeds_fg(cv, 1080, seed=27, color=(42, 32, 44), n=32, s=1.0)
    birds(g, [(760, 240), (880, 210), (840, 280)], 10, color=(40, 30, 44), width=4)


def bg_edo_sakoku(cv):
    """鎖国 (1639・閉ざされる国)."""
    sky(cv, [(0.00, (88, 100, 118)), (0.55, (130, 140, 154)), (1.00, (176, 180, 182))])
    g = cv.g()
    clouds_row(cv, 160, 3, 40, seed=28, base=(160, 164, 170), under=(120, 124, 132), alpha=235)
    sea_grad = gradient((int(W * cv.ss), int((H - 560) * cv.ss)),
                        [(0, (128, 148, 162)), (1, (96, 112, 128))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(560 * cv.ss)))
    g.line([(0, 562), (W, 562)], (112, 126, 140), 4)
    # 遠ざかる船 (去っていく唐船)
    boat(g, 1500, 700, 0.5, oars=1, seed=1)
    # 中央に鎖国の扉モチーフ
    sakoku_door(g, 960, 560, 1.35)
    # 鎖の連なり
    for k in range(8):
        cx_ = 300 + k * 44
        cy_ = 980 + (k % 2) * 14
        g.circle(cx_, cy_, 14, fill=(96, 96, 102), outline=(70, 70, 76), owidth=3)
        g.circle(cx_, cy_, 5, fill=(120, 120, 126))
    g.line([(300, 980), (612, 1008)], (96, 96, 102), 4)
    grass_tufts(g, (0, 960, W, 1070), 60, (110, 114, 108), seed=29)


def bg_edo_dejima(cv):
    """出島 (扇形の人工島とオランダ商館)."""
    sky(cv, P.SKY_EDO_DAY)
    g = cv.g()
    sun(g, 380, 180, 54, halo=0.45)
    clouds_row(cv, 150, 3, 32, seed=30)
    mountain_ridge(cv, 430, 100, ((112, 132, 136), (166, 186, 178)), seed=31, freq=1.9)
    horizon = 500
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (136, 186, 212)), (0.4, (98, 158, 202)), (1, (66, 126, 176))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(32)
    for _ in range(24):
        yy = rnd.uniform(horizon + 10, H - 20)
        ln = rnd.uniform(30, 150)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((240, 250, 255), rnd.randint(50, 130)))
    # 扇形の出島
    fan_dejima(g, 1200, 780, 0.85, seed=2)
    # オランダ商船
    war_boat(g, 480, 700, 0.6, banner=False, seed=3)
    birds(g, [(700, 240), (800, 280), (760, 210)], 12, width=3.2)


def bg_edo_trade(cv):
    """交易ルート (海図と出船)."""
    cv.img.alpha_composite(gradient(cv.img.size,
                                    [(0, (36, 44, 74)), (0.6, (52, 60, 92)),
                                     (1, (74, 80, 112))], "v"))
    g = cv.g()
    stars(g, (40, 40, 1880, 360), 70, seed=33)
    # 海図 (中央に大きく)
    japan_map_trade(g, 960, 520, 1.6, seed=2)
    # 周辺の小舟 (海図の外枠の外に)
    boat(g, 170, 1000, 0.6, oars=2, seed=3)
    boat(g, 1740, 1000, 0.6, oars=1, seed=4)
    # 光
    gl = radial((int(1500 * cv.ss), int(900 * cv.ss)), (220, 214, 190),
                alpha_in=60, power=2.4)
    cv.img.alpha_composite(gl, (int(210 * cv.ss), int(100 * cv.ss)))


def bg_edo_town(cv):
    """江戸の繁華街 (橋と芝居小屋と人出)."""
    sky(cv, P.SKY_EDO_DAY)
    g = cv.g()
    sun(g, 1460, 170, 52, halo=0.45)
    clouds_row(cv, 140, 3, 30, seed=34)
    mountain_ridge(cv, 380, 90, ((110, 138, 130), (166, 186, 164)), seed=35, freq=2.0)
    # 遠くに江戸城の天守
    tenshu(g, 300, 690, 0.4, tiers=4, gold_top=False, seed=2)
    # 街 (両側の店)
    ground(cv, 700, (196, 188, 158), dark=(164, 156, 128), curve=12, seed=36,
           speckles=150, speckle_colors=[(176, 168, 140), (210, 202, 172)],
           speckle_r=(2, 5))
    for sx in (120, 1620):
        rect(g, sx, 640, sx + 300, 850, fill=(206, 192, 168), outline=(164, 152, 132),
             owidth=3)
        g.poly([(sx - 10, 640), (sx + 310, 640), (sx + 290, 590), (sx + 20, 590)],
               fill=(96, 84, 72), outline=(74, 64, 56), owidth=2.6)
        # 暖簾
        rect(g, sx + 40, 700, sx + 260, 760, fill=with_alpha((140, 90, 80), 220))
        for k in range(6):
            g.line([(sx + 52 + k * 38, 700), (sx + 52 + k * 38, 760)],
                   with_alpha((96, 64, 58), 180), 3)
        # 提灯
        for lx in (sx + 50, sx + 250):
            g.rrect((lx - 10, 780, lx + 10, 830), 6, fill=(222, 130, 96),
                    outline=(170, 96, 70), owidth=2.2)
            g.line([(lx, 780), (lx, 756)], (96, 84, 72), 2.6)
    # 両国橋風の橋 (中央)
    rect(g, 700, 700, 1220, 780, fill=(150, 118, 88), outline=(118, 92, 68), owidth=4)
    for k in range(9):
        g.rrect((720 + k * 54, 780, 756 + k * 54, 810), 3, fill=(128, 100, 74))
    g.line([(700, 706), (1220, 706)], (118, 92, 68), 6)
    g.line([(700, 740), (1220, 740)], (118, 92, 68), 4)
    # 橋の欄干の擬宝珠
    for k in range(8):
        g.circle(740 + k * 60, 706, 9, fill=(190, 178, 140), outline=(146, 136, 108),
                 owidth=2.4)
    # 人出
    _crowd(g, (740, 830, 1180, 1000), 16, seed=37)
    _crowd(g, (120, 880, 540, 1060), 12, seed=38, col=(78, 68, 72))
    _crowd(g, (1380, 880, 1800, 1060), 12, seed=39, col=(78, 68, 72))
    # 夕方の提灯の灯り
    gl = radial((int(700 * cv.ss), int(500 * cv.ss)), (255, 214, 150),
                alpha_in=55, power=2.4)
    cv.img.alpha_composite(gl, (int(600 * cv.ss), int(560 * cv.ss)))
    birds(g, [(900, 200), (1000, 240), (960, 170)], 12, width=3.2)


def bg_edo_culture(cv):
    """元禄文化 (芝居小屋と浮世絵)."""
    cv.img.alpha_composite(gradient(cv.img.size,
                                    [(0, (66, 56, 66)), (0.6, (86, 72, 82)),
                                     (1, (112, 96, 104))], "v"))
    g = cv.g()
    # 舞台 (歌舞伎の回り舞台)
    stage_y = 760
    rect(g, 560, stage_y, 1360, stage_y + 120, fill=(120, 88, 66), outline=(88, 64, 48),
         owidth=4)
    # 引幕 (紅白の縞)
    for k in range(14):
        c = P.SHU if k % 2 == 0 else (240, 236, 228)
        rect(g, 580 + k * 56, 560, 580 + (k + 1) * 56, stage_y, fill=c)
    # 舞台の俳優シルエット (見得を切る)
    px, py = 960, 660
    g.circle(px, py - 120, 26, fill=(40, 32, 44))
    g.poly([(px - 34, py - 96), (px + 34, py - 96), (px + 26, py + 20), (px - 26, py + 20)],
           fill=(40, 32, 44))
    g.line([(px - 34, py - 60), (px - 90, py - 130)], (40, 32, 44), 8)
    g.line([(px + 34, py - 60), (px + 60, py + 20)], (40, 32, 44), 8)
    g.line([(px - 26, py + 20), (px - 26, py + 60)], (40, 32, 44), 8)
    g.line([(px + 26, py + 20), (px + 26, py + 60)], (40, 32, 44), 8)
    # 客席 (上げ下げの靴脱ぎ風に並ぶ人)
    rect(g, 480, 900, 1440, 980, fill=(104, 92, 98))
    _crowd(g, (520, 920, 1400, 1060), 22, seed=40, col=(52, 44, 56))
    # 行灯
    for lx in (560, 1360):
        g.rrect((lx - 18, 500, lx + 18, 560), 8, fill=(232, 170, 110),
                outline=(180, 128, 86), owidth=2.4)
        gl = radial((int(300 * cv.ss), int(300 * cv.ss)), (255, 200, 130),
                    alpha_in=110, power=2.2)
        cv.img.alpha_composite(gl, (int((lx - 150) * cv.ss), int((420) * cv.ss)))
    # 浮世絵の額 (壁)
    rect(g, 200, 300, 420, 520, fill=(230, 226, 214), outline=(150, 140, 126), owidth=4)
    rect(g, 1500, 300, 1720, 520, fill=(230, 226, 214), outline=(150, 140, 126), owidth=4)
    for (fx, fy) in ((240, 360), (1540, 360)):
        g.ellipse((fx, fy, fx + 120, fy + 110), fill=(214, 160, 120))
        g.poly([(fx + 20, fy + 90), (fx + 60, fy + 30), (fx + 100, fy + 90)],
               fill=(120, 140, 110))


def bg_edo_dusk(cv):
    """江戸の夕暮れ (平和な日暮れと鐘の音)."""
    sky(cv, P.SKY_EVENING)
    g = cv.g()
    sun(g, 1400, 390, 80, color=(244, 176, 110), core=(250, 214, 160), halo=0.55)
    clouds_row(cv, 210, 3, 42, seed=41, base=(226, 140, 118), under=(120, 70, 84), alpha=225)
    mountain_ridge(cv, 500, 100, ((84, 62, 82), (140, 96, 96)), seed=42, freq=1.7)
    fuji(g, 1520, 520, 0.55, col=(120, 110, 140), snow=(232, 224, 216))
    # 街と寺
    rnd = random.Random(43)
    x = 0
    while x < W:
        hw = rnd.uniform(110, 180)
        hh = rnd.uniform(38, 70)
        rect(g, x, 660 - hh, x + hw, 700, fill=(122, 92, 88))
        g.poly([(x - 8, 660 - hh), (x + hw + 8, 660 - hh), (x + hw * 0.72, 660 - hh - 26),
                (x + hw * 0.28, 660 - hh - 26)], fill=(108, 80, 78))
        x += hw + rnd.uniform(16, 58)
    # 時の鐘 (鐘楼)
    rect(g, 1160, 560, 1300, 660, fill=(104, 78, 72), outline=(82, 60, 56), owidth=3)
    g.poly([(1150, 560), (1310, 560), (1280, 512), (1180, 512)], fill=(92, 68, 64),
           outline=(70, 52, 48), owidth=2.6)
    g.ellipse((1200, 596, 1260, 652), fill=(88, 84, 92), outline=(64, 60, 68), owidth=3)
    rect(g, 0, 700, W, H, fill=(106, 84, 86))
    speckle(g, (0, 710, W, 1080), 130, [(94, 74, 78), (118, 94, 96)], r=(2, 6), seed=44)
    reeds_fg(cv, 1080, seed=45, color=(64, 48, 56), n=32, s=1.0)
    birds(g, [(700, 250), (820, 220), (780, 290)], 12, width=4)


# ---------------------------------------------------------------- ポイント用タイムライン


def bg_timeline(cv):
    """ep07 用ポイント背景 — 関ヶ原〜鎖国のタイムライン."""
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
    labels = ["関ヶ原の戦い", "江戸幕府 1603", "島原の乱", "鎖国 1639"]
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
    # 関ヶ原: 対峙する二つの幟
    nobori(g, nodes[0] - 56, icon_y + 4, 0.5, col=(90, 110, 170), seed=1)
    nobori(g, nodes[0] + 56, icon_y + 4, 0.5, col=P.SHU, seed=2)
    # 江戸幕府: 江戸城の天守
    tenshu(g, nodes[1], icon_y + 2, 0.32, tiers=4, gold_top=False, seed=3)
    # 島原の乱: 十字の旗
    cross_flag(g, nodes[2], icon_y - 10, 0.62)
    # 鎖国: 閉じる扉
    sakoku_door(g, nodes[3], icon_y - 78, 0.36)
    gl = radial((int(1400 * cv.ss), int(900 * cv.ss)), (90, 120, 200),
                alpha_in=50, power=2.4)
    cv.img.alpha_composite(gl, (int(260 * cv.ss), int(160 * cv.ss)))

"""ep10 シーン背景 (近現代) — script.json の background 名と 1:1 対応.

日清・日露から大正デモクラシー、二つの大戦と高度経済成長、現代まで。
歴史上の戦乱は、犠牲の実態を損なわないようシンボリックな平麺構成で表現する。
テキストは焼き込まない。
"""
from __future__ import annotations

import math
import random

from artlib import palette as P
from artlib.canvas import (Canvas, blob_pts, dots_pattern, gradient, qbez,
                           radial, shade, speckle, tint, with_alpha)
from artlib.nature import (birds, clouds_row, grass_tufts, ground, moon,
                           mountain_ridge, reeds_fg, ridge, sky, stars, sun, tree)
from artlib.props import (black_ship, brick_building, campfire, factory,
                          kango_ship, mountain_fort, nobori, osaka_castle,
                          rickshaw, rice_paddy, samurai_rider, shinkansen,
                          smoke_wisp, steam_train, tile_roof_house, war_ruins)
from artlib.props import arquebusier, rect, seedling

W, H = 1920, 1080


def new_canvas():
    return Canvas(W, H, ss=2)


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


def _city_silhouette(g, y, seed=0, col=(64, 56, 70), window=None):
    """都市の屋根のシルエット."""
    rnd = random.Random(seed)
    x = 0
    while x < W:
        hw = rnd.uniform(110, 200)
        hh = rnd.uniform(40, 90)
        rect(g, x, y - hh, x + hw, y, fill=col)
        g.poly([(x - 8, y - hh), (x + hw + 8, y - hh), (x + hw * 0.72, y - hh - 26),
                (x + hw * 0.28, y - hh - 26)], fill=shade(col, 0.86))
        if window:
            for _ in range(4):
                wx = rnd.uniform(x + 14, x + hw - 24)
                wy = rnd.uniform(y - hh + 10, y - 14)
                rect(g, wx, wy, wx + 12, wy + 10, fill=window)
        x += hw + rnd.uniform(16, 60)


# ---------------------------------------------------------------- 明治の戦争


def bg_modern_nisshin(cv):
    """日清戦争 (1894・黄海の海戦)."""
    sky(cv, [(0.00, (120, 156, 190)), (0.55, (176, 190, 204)), (1.00, (232, 224, 208))])
    g = cv.g()
    clouds_row(cv, 150, 3, 38, seed=2, base=(214, 216, 218), under=(162, 166, 172), alpha=230)
    horizon = 420
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (132, 176, 202)), (0.4, (96, 152, 196)), (1, (64, 122, 170))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(3)
    for _ in range(24):
        yy = rnd.uniform(horizon + 10, H - 20)
        ln = rnd.uniform(30, 150)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((240, 250, 255), rnd.randint(50, 130)))
    # 戦闘の痕 (遠い煙)
    smoke_wisp(g, 500, 400, 1.4, color=(120, 124, 132), alpha=170, seed=4)
    smoke_wisp(g, 1560, 430, 1.2, color=(120, 124, 132), alpha=160, seed=5)
    # 日清両軍の軍艦 (シンボリックに遠景で)
    black_ship(g, 620, 640, 0.6, smoke=False, seed=6)
    black_ship(g, 1400, 560, 0.5, smoke=False, seed=7)
    birds(g, [(700, 280), (800, 320), (760, 250)], 12, width=3.4)


def bg_modern_nichiro(cv):
    """日露戦争 (1904・旅順の包囲と雪原)."""
    sky(cv, [(0.00, (110, 128, 156)), (0.55, (176, 186, 200)), (1.00, (226, 228, 224))])
    g = cv.g()
    clouds_row(cv, 150, 3, 40, seed=8, base=(210, 216, 222), under=(160, 166, 174), alpha=235)
    mountain_ridge(cv, 430, 130, ((100, 114, 130), (156, 168, 184)), seed=9, freq=1.9)
    ground(cv, 620, (202, 208, 212), dark=(176, 182, 190), curve=12, seed=10,
           speckles=140, speckle_colors=[(186, 192, 198), (214, 220, 226)],
           speckle_r=(2, 5))
    # 雪原の塹壕と兵士のシルエット
    rect(g, 0, 700, W, 780, fill=(168, 174, 184))
    for k in range(6):
        arquebusier(g, 260 + k * 260, 770 + (k % 2) * 8, 0.85 - (k % 2) * 0.06,
                    firing=False, seed=11 + k)
    # 遠くの要塞と煙
    mountain_fort(g, 1520, 660, 0.55, seed=2, flag=(168, 174, 184))
    smoke_wisp(g, 1520, 470, 1.4, color=(110, 114, 124), alpha=180, seed=12)
    nobori(g, 240, 900, 0.85, col=(238, 238, 236))
    grass_tufts(g, (0, 900, W, 1070), 60, (190, 196, 204), seed=13)
    birds(g, [(700, 240), (800, 280), (760, 210)], 12, width=3.2)


def bg_modern_manshu(cv):
    """満州事変 (1931・夜の鉄道と軍列)."""
    sky(cv, [(0.00, (28, 32, 56)), (0.55, (52, 56, 84)), (1.00, (86, 84, 110))])
    g = cv.g()
    stars(g, (40, 40, 1880, 400), 70, seed=14)
    mountain_ridge(cv, 480, 110, ((32, 36, 60), (56, 60, 88)), seed=15, freq=1.8)
    ground(cv, 600, (56, 62, 76), dark=(46, 52, 64), curve=10, seed=16,
           speckles=130, speckle_colors=[(48, 54, 66), (64, 70, 84)],
           speckle_r=(2, 5))
    # 夜の南満洲鉄道
    steam_train(g, 900, 800, 0.85, seed=2)
    # 哨戒する兵士のシルエット
    for k in range(4):
        arquebusier(g, 300 + k * 220, 950 + (k % 2) * 20, 0.7, firing=False, seed=17 + k)
    # 探照灯
    g.poly([(1500, 240), (1240, 800), (1400, 800)], fill=with_alpha((220, 226, 235), 70))
    moon(cv, 1640, 160, 44, cut_color=(26, 30, 54))
    reeds_fg(cv, 1080, seed=18, color=(38, 34, 46), n=30, s=1.0)


def bg_modern_panic(cv):
    """世界恐慌 (1929・閉ざされる市場)."""
    sky(cv, [(0.00, (98, 100, 112)), (0.55, (144, 146, 154)), (1.00, (186, 186, 182))])
    g = cv.g()
    clouds_row(cv, 170, 3, 42, seed=19, base=(140, 142, 148), under=(100, 102, 108),
               alpha=235)
    ground(cv, 640, (150, 150, 148), dark=(126, 126, 124), curve=10, seed=20,
           speckles=140, speckle_colors=[(134, 134, 132), (164, 164, 160)],
           speckle_r=(2, 5))
    # 閉まる店と下がる相場の看板
    for bx in (300, 700, 1100, 1500):
        rect(g, bx - 90, 560, bx + 90, 700, fill=(128, 128, 130), outline=(104, 104, 106),
             owidth=3)
        g.poly([(bx - 98, 560), (bx + 98, 560), (bx + 84, 526), (bx - 84, 526)],
               fill=(108, 108, 112), outline=(88, 88, 92), owidth=2.6)
        rect(g, bx - 60, 600, bx + 60, 700, fill=with_alpha((84, 84, 88), 220))
    # 下向きの矢印看板
    g.poly([(860, 300), (1060, 300), (960, 480)], fill=(150, 90, 84),
           outline=(120, 72, 64), owidth=3)
    _crowd(g, (200, 800, 1700, 1050), 26, seed=21, col=(66, 66, 70))
    birds(g, [(700, 240), (800, 280), (760, 210)], 10, color=(52, 52, 58), width=3.6)


def bg_modern_taisho(cv):
    """大正デモクラシー (モダンな銀座とデモ)."""
    sky(cv, [(0.00, (130, 184, 216)), (0.55, (186, 210, 230)), (1.00, (248, 238, 224))])
    g = cv.g()
    sun(g, 1420, 170, 52, halo=0.45)
    clouds_row(cv, 140, 3, 30, seed=22)
    # モダンな煉瓦街 (電線つき)
    brick_building(g, 240, 720, 0.6, w=170, floors=2, seed=3)
    brick_building(g, 1700, 720, 0.6, w=170, floors=2, seed=4)
    ground(cv, 700, (196, 190, 164), dark=(164, 158, 132), curve=10, seed=23,
           speckles=140, speckle_colors=[(176, 170, 144), (212, 206, 180)],
           speckle_r=(2, 5))
    # 電線
    for k in range(3):
        py = 380 + k * 60
        g.line(qbez((0, py), (W / 2, py + 24), (W, py), 16), with_alpha((60, 62, 70), 160), 2.6)
    # デモの行列 (幟と人)
    for k in range(5):
        nobori(g, 300 + k * 150, 880, 0.7,
               col=(90, 110, 170) if k % 2 else (238, 238, 236), seed=24 + k)
    _crowd(g, (200, 880, 1700, 1060), 28, seed=25)
    # 人力車と自動車もどき
    rickshaw(g, 1200, 1000, 0.85)
    birds(g, [(700, 230), (800, 270), (760, 200)], 12, width=3.2)


def bg_modern_futsusen(cv):
    """普通選挙法 (1925・投票所に並ぶ国民)."""
    sky(cv, P.SKY_EDO_DAY)
    g = cv.g()
    sun(g, 380, 180, 52, halo=0.45)
    clouds_row(cv, 150, 3, 30, seed=26)
    mountain_ridge(cv, 450, 110, ((108, 136, 130), (166, 188, 164)), seed=27, freq=1.9)
    ground(cv, 640, (188, 184, 136), dark=(156, 152, 108), curve=12, seed=28,
           speckles=150, speckle_colors=[(168, 164, 116), (202, 198, 150)],
           speckle_r=(2, 5))
    # 投票所
    rect(g, 760, 560, 1160, 700, fill=(214, 210, 200), outline=shade((214, 210, 200), 0.74),
         owidth=3)
    g.poly([(746, 560), (1174, 560), (1140, 506), (780, 506)], fill=(96, 84, 72),
           outline=(72, 62, 54), owidth=2.6)
    rect(g, 900, 600, 1020, 700, fill=(88, 76, 66))
    g.line([(960, 506), (960, 600)], (72, 62, 54), 4)
    # 立会い箱 (投票箱)
    for bx in (520, 1400):
        rect(g, bx - 60, 700, bx + 60, 780, fill=(120, 88, 62), outline=(88, 62, 42),
             owidth=4)
        g.rrect((bx - 40, 736, bx + 40, 770), 4, fill=(64, 52, 44))
        g.line([(bx - 24, 730), (bx + 24, 730)], (160, 152, 134), 6)
    # 並ぶ国民
    _crowd(g, (300, 800, 700, 1060), 14, seed=29)
    _crowd(g, (1220, 800, 1620, 1060), 14, seed=30)
    grass_tufts(g, (0, 700, W, 1070), 70, (150, 148, 104), seed=31)
    birds(g, [(700, 230), (800, 270), (760, 200)], 12, width=3.2)


# ---------------------------------------------------------------- 戦争と復興


def bg_modern_taiheiyo(cv):
    """太平洋戦争 (symbolic: 遠い空の戦闘機と煙)."""
    sky(cv, [(0.00, (84, 78, 96)), (0.55, (130, 120, 132)), (1.00, (170, 148, 142))])
    g = cv.g()
    clouds_row(cv, 160, 3, 44, seed=32, base=(150, 140, 146), under=(106, 96, 108),
               alpha=235)
    # 遠い編隊のシルエット (小さく・象徴的に)
    for k in range(6):
        px = 300 + k * 220 + (k % 2) * 40
        py = 240 + (k % 3) * 34
        g.poly([(px, py), (px + 34, py - 8), (px + 68, py), (px + 30, py + 10)],
               fill=(52, 50, 58))
        g.line([(px + 30, py + 10), (px + 30, py + 22)], (52, 50, 58), 4)
    # 燃える都の遠景
    _city_silhouette(g, 700, seed=33, col=(70, 62, 70))
    campfire(g, 700, 720, 1.4, stones=False, seed=34)
    campfire(g, 1300, 700, 1.1, stones=False, seed=35)
    smoke_wisp(g, 740, 520, 2.0, color=(70, 66, 72), alpha=200, seed=36)
    smoke_wisp(g, 1330, 540, 1.6, color=(70, 66, 72), alpha=190, seed=37)
    ground(cv, 740, (96, 90, 94), dark=(80, 74, 80), curve=10, seed=38,
           speckles=130, speckle_colors=[(84, 78, 84), (108, 100, 106)],
           speckle_r=(2, 6))
    reeds_fg(cv, 1080, seed=39, color=(44, 38, 48), n=32, s=1.0)
    birds(g, [(600, 240), (700, 280), (660, 210)], 10, color=(40, 36, 46), width=4)


def _ash_sky(cv):
    sky(cv, [(0.00, (110, 112, 118)), (0.5, (150, 150, 152)), (1.00, (190, 190, 186))])


def bg_modern_1945(cv):
    """1945 (焼け野原からの一本の芽)."""
    g = cv.g()
    clouds_row(cv, 170, 3, 44, seed=40, base=(136, 138, 142), under=(96, 98, 102),
               alpha=235)
    ground(cv, 640, (140, 138, 134), dark=(116, 114, 110), curve=10, seed=41,
           speckles=160, speckle_colors=[(126, 124, 120), (154, 152, 148)],
           speckle_r=(2, 6))
    # 廃墟
    from artlib.props import war_ruins
    war_ruins(g, 960, 760, 1.0, seed=2)
    # 烏
    birds(g, [(500, 240), (620, 280), (580, 210)], 11, color=(48, 46, 50), width=4)


def bg_modern_kenpo(cv):
    """日本国憲法公布 (1946・新しい国のかたち)."""
    sky(cv, [(0.00, (124, 184, 216)), (0.55, (182, 212, 232)), (1.00, (248, 240, 224))])
    g = cv.g()
    sun(g, 400, 180, 54, halo=0.45)
    clouds_row(cv, 150, 3, 30, seed=48)
    mountain_ridge(cv, 450, 110, ((108, 136, 130), (166, 188, 164)), seed=49, freq=1.9)
    ground(cv, 640, (190, 186, 140), dark=(158, 154, 108), curve=12, seed=50,
           speckles=150, speckle_colors=[(170, 166, 118), (204, 200, 152)],
           speckle_r=(2, 5))
    # 国会議事堂風の建物
    brick_building(g, 960, 700, 0.9, w=210, floors=3, seed=2)
    rect(g, 900, 700, 1020, 640, fill=(150, 148, 142), outline=shade((150, 148, 142), 0.72),
         owidth=3)
    g.poly([(880, 640), (1040, 640), (1020, 600), (900, 600)], fill=(96, 98, 104),
           outline=(72, 74, 80), owidth=2.6)
    # 日章旗の並び
    for k in range(4):
        px = 480 + k * 180
        g.line([(px, 700), (px, 480)], P.WOOD_D, 6)
        rect(g, px, 480, px + 72, 528, fill=(238, 238, 236))
        g.circle(px + 36, 504, 16, fill=P.SHU, outline=shade(P.SHU, 0.7), owidth=2)
    grass_tufts(g, (0, 700, W, 1070), 80, (150, 148, 104), seed=51)
    birds(g, [(700, 230), (800, 270), (760, 200)], 12, width=3.2)


def bg_modern_korea(cv):
    """特需 (朝鮮戦争の物資輸出で賑わう港)."""
    sky(cv, P.SKY_EDO_DAY)
    g = cv.g()
    sun(g, 360, 180, 52, halo=0.45)
    clouds_row(cv, 150, 3, 30, seed=52)
    horizon = 470
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (140, 188, 212)), (0.4, (98, 158, 202)), (1, (66, 126, 176))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(53)
    for _ in range(24):
        yy = rnd.uniform(horizon + 10, 700)
        ln = rnd.uniform(30, 150)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((240, 250, 255), rnd.randint(50, 130)))
    # 貨物船
    black_ship(g, 560, 700, 0.7, smoke=True, seed=1)
    black_ship(g, 1400, 560, 0.45, smoke=False, seed=2)
    # 岸壁のクレーンとコンテナ
    rect(g, 0, 760, W, H, fill=(170, 164, 146))
    rect(g, 0, 760, W, 796, fill=(148, 142, 124))
    for k in range(5):
        px = 120 + k * 380
        g.rrect((px, 620, px + 240, 764), 4, fill=(178, 148, 118),
                outline=(146, 118, 92), owidth=3)
        for wx in range(4):
            for wy in range(2):
                g.rrect((px + 16 + wx * 56, 632 + wy * 60, px + 64 + wx * 56,
                         684 + wy * 60), 3, fill=with_alpha((120, 96, 76), 200))
    factory(g, 1700, 770, 0.42, seed=2)
    birds(g, [(600, 240), (700, 280), (660, 210)], 12, width=3.2)


# ---------------------------------------------------------------- 戦後と現代


def bg_modern_growth(cv):
    """高度経済成長 (工場と新幹線とビル群)."""
    sky(cv, P.SKY_GROWTH)
    g = cv.g()
    sun(g, 1400, 180, 54, halo=0.45)
    clouds_row(cv, 140, 3, 30, seed=54)
    ground(cv, 560, (188, 184, 136), dark=(156, 152, 108), curve=10, seed=55,
           speckles=140, speckle_colors=[(168, 164, 116), (202, 198, 150)],
           speckle_r=(2, 5))
    # 工場群
    factory(g, 320, 620, 0.8, seed=2)
    factory(g, 1620, 640, 0.7, seed=3)
    # ビル群 (遠景)
    for (bx, bh) in [(760, 120), (860, 170), (960, 140), (1060, 190)]:
        rect(g, bx - 50, 560 - bh, bx + 50, 560, fill=(150, 156, 162),
             outline=shade((150, 156, 162), 0.75), owidth=2.6)
        for wy in range(int(560 - bh) + 14, 548, 30):
            for wx in range(int(bx - 34), int(bx + 34), 26):
                rect(g, wx, wy, wx + 14, wy + 14, fill=with_alpha((210, 220, 226), 190))
    # 高架を走る新幹線
    rect(g, 0, 700, W, 780, fill=(150, 148, 142), outline=(122, 120, 116), owidth=3)
    shinkansen(g, 960, 700, 0.9, seed=4)
    # 前景の田んぼ (残る農地)
    rice_paddy(cv, 980, 1080, [(208, 224, 230), (170, 204, 220)], seed=5, rows_seed=9)
    birds(g, [(700, 220), (800, 260), (760, 190)], 12, width=3.2)


def bg_modern_dusk(cv):
    """現代の夕暮れ (電気の灯る街)."""
    sky(cv, [(0.00, (56, 56, 96)), (0.55, (110, 90, 130)), (1.00, (210, 140, 130))])
    g = cv.g()
    stars(g, (40, 40, 1880, 340), 50, seed=56)
    # ビル群の灯る窓
    for (bx, bh, w_) in [(200, 420, 180), (500, 340, 200), (820, 480, 220),
                         (1160, 380, 200), (1460, 460, 220)]:
        rect(g, bx, 1080 - bh, bx + w_, 1080, fill=(72, 66, 78),
             outline=shade((72, 66, 78), 0.8), owidth=3)
        rnd = random.Random(int(bx))
        for wy in range(int(1080 - bh) + 20, 1050, 44):
            for wx in range(int(bx) + 16, int(bx + w_) - 20, 40):
                lit = rnd.random() < 0.6
                rect(g, wx, wy, wx + 20, wy + 26,
                     fill=with_alpha((250, 214, 150), 220) if lit else (52, 48, 60))
    moon(cv, 400, 200, 42, cut_color=(52, 50, 90))
    _crowd(g, (100, 900, 1820, 1060), 30, seed=57, col=(56, 48, 62))
    gl = radial((int(1200 * cv.ss), int(700 * cv.ss)), (255, 190, 130),
                alpha_in=60, power=2.4)
    cv.img.alpha_composite(gl, (int(360 * cv.ss), int(460 * cv.ss)))


# ---------------------------------------------------------------- ポイント用タイムライン


def bg_timeline(cv):
    """ep10 用ポイント背景 — 近現代のタイムライン."""
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
    labels = ["日清・日露戦争", "世界恐慌", "1945 焼け野原", "高度経済成長"]
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
        g.text((nx, band_y + 118), labels[i], 25, (214, 224, 248), "bold", "mm")
    black_ship(g, nodes[0], icon_y - 46, 0.3, smoke=False, seed=1)
    rect(g, nodes[1] - 90, icon_y - 66, nodes[1] + 90, icon_y - 10,
         fill=(128, 128, 130), outline=(104, 104, 106), owidth=3)
    g.poly([(nodes[1] - 100, icon_y - 66), (nodes[1] + 100, icon_y - 66),
            (nodes[1] + 86, icon_y - 100), (nodes[1] - 86, icon_y - 100)],
           fill=(108, 108, 112), outline=(88, 88, 92), owidth=2.6)
    war_ruins(g, nodes[2], icon_y + 2, 0.44, seed=3)
    shinkansen(g, nodes[3], icon_y - 26, 0.34, seed=4)
    gl = radial((int(1400 * cv.ss), int(900 * cv.ss)), (90, 120, 200),
                alpha_in=50, power=2.4)
    cv.img.alpha_composite(gl, (int(260 * cv.ss), int(160 * cv.ss)))

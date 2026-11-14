"""ep01 シーン背景 (1920x1080) — script.json の background 名と 1:1 対応.

各関数は Canvas(1920, 1080) を受け取り全面を描く。テキストは焼き込まない
(文字は editor の overlay_text が担当)。
"""
from __future__ import annotations

import math
import random

from artlib import palette as P
from artlib.canvas import Canvas, blob_pts, dots_pattern, gradient, radial, \
    shade, speckle, sublayer, tint, with_alpha
from artlib.nature import (birds, cloud, clouds_row, forest_band, grass_tufts,
                           ground, light_shafts, moon, mountain_ridge, reeds_fg,
                           ridge, sky, stars, sun, tree, water_band)
from artlib.props import (banner_pole, big_hall, boat, boar, bones, campfire,
                          deer, dotaku, draw_acorn, haniwa, jomon_pot,
                          keyhole_tomb, palisade, pit_house, rect, rice_paddy,
                          smoke_wisp, stone_tools, torch, warehouse,
                          yayoi_pot)

W, H = 1920, 1080


def new_canvas():
    return Canvas(W, H, ss=2)


# ---------------------------------------------------------------- 共通パーツ


def dogu(g, x, y, s, clay=(150, 108, 78)):
    """土偶 (シンプルな遮光器土偶風). y=底."""
    g.ellipse((x - 40 * s, y - 6 * s, x + 40 * s, y + 8 * s),
              fill=with_alpha((70, 54, 42), 60))
    # 台座
    g.rrect((x - 26 * s, y - 16 * s, x + 26 * s, y), 6 * s, fill=shade(clay, 0.8))
    # 胴 (寛いだシルエット)
    g.poly(blob_pts(x, y - 60 * s, 42 * s, 48 * s, seed=3, wobble=0.1),
           fill=clay, outline=shade(clay, 0.7), owidth=2.4 * s)
    # 頭
    g.circle(x, y - 122 * s, 26 * s, fill=clay, outline=shade(clay, 0.7), owidth=2.4 * s)
    # 遮光器の角 (左右の耳飾り)
    for sx in (-1, 1):
        g.poly([(x + sx * 20 * s, y - 136 * s), (x + sx * 44 * s, y - 158 * s),
                (x + sx * 30 * s, y - 122 * s)], fill=shade(clay, 0.85),
               outline=shade(clay, 0.7), owidth=2 * s)
    # 目 (細長の切れ目)
    for sx in (-1, 1):
        g.line([(x + sx * 7 * s - 9 * s, y - 124 * s), (x + sx * 7 * s + 9 * s, y - 128 * s)],
               (40, 28, 24), 3.4 * s)
    # 胸の装飾痕
    g.arc((x - 22 * s, y - 66 * s, x + 22 * s, y - 34 * s), 200, 340,
          shade(clay, 0.75), 3 * s)


def dotaku_stand(g, x, y, s):
    """銅鐸を吊るした木架. y=地面."""
    top = y - 300 * s
    for px in (-70, 70):
        g.poly([(x + px * s - 8 * s, y), (x + px * s + 8 * s, y),
                (x + px * s + 6 * s, top), (x + px * s - 6 * s, top)], fill=P.WOOD_D)
    g.rrect((x - 84 * s, top - 10 * s, x + 84 * s, top + 10 * s), 8 * s, fill=P.WOOD)
    g.line([(x, top + 6 * s), (x, top + 26 * s)], shade(P.WOOD_D, 0.8), 4 * s)
    dotaku(g, x, top + 26 * s + 250 * s, s * 0.95)


def fish_hanging(g, x, y, s, n=3, seed=0):
    """魚干し場 (2本柱+横棒+魚). y=地面."""
    top = y - 170 * s
    for px in (-90, 90):
        g.line([(x + px * s, y), (x + px * s, top)], P.WOOD_D, 9 * s)
    g.line([(x - 100 * s, top), (x + 100 * s, top)], P.WOOD_D, 8 * s)
    rnd = random.Random(seed)
    for i in range(n):
        fx = x + (-70 + 70 * i) * s
        fy = top + 6 * s
        g.line([(fx, fy), (fx, fy + 14 * s)], (80, 60, 46), 3 * s)
        flip = 1 if rnd.random() < 0.5 else -1
        g.ellipse((fx - 26 * s, fy + 14 * s, fx + 26 * s, fy + 48 * s),
                  fill=(118, 152, 168), outline=(70, 100, 116), owidth=2 * s)
        g.poly([(fx + flip * 26 * s, fy + 31 * s), (fx + flip * 48 * s, fy + 20 * s),
                (fx + flip * 48 * s, fy + 42 * s)], fill=(96, 128, 144))
        g.circle(fx + flip * 18 * s, fy + 26 * s, 2.5 * s, fill=(30, 40, 46))


def shell_mound(g, x, y, s, seed=0):
    """貝塚 (貝の積もった塚). y=底."""
    rnd = random.Random(seed)
    g.poly(blob_pts(x, y - 30 * s, 130 * s, 52 * s, seed=1, wobble=0.12),
           fill=(168, 142, 112), outline=(128, 104, 78), owidth=3 * s)
    g.poly(blob_pts(x - 6 * s, y - 38 * s, 104 * s, 40 * s, seed=2, wobble=0.1),
           fill=(186, 162, 130))
    for _ in range(14):
        sx = x + rnd.uniform(-105, 105) * s
        sy = y - rnd.uniform(4, 62) * s
        a = rnd.uniform(0, math.tau)
        g.ellipse((sx - 9 * s, sy - 6 * s, sx + 9 * s, sy + 6 * s),
                  fill=(232, 222, 200), outline=(150, 134, 108), owidth=1.6 * s)
        g.arc((sx - 7 * s, sy - 5 * s, sx + 7 * s, sy + 5 * s),
              200 + a * 30, 330 + a * 30, (150, 134, 108), 1.6 * s)


def bow_and_arrows(g, x, y, s):
    """弓と矢 (地面に立てかけ). y=地面."""
    g.arc((x - 34 * s, y - 150 * s, x + 34 * s, y + 30 * s), 200, 340,
          P.WOOD_D, 7 * s)
    g.line([(x - 26 * s, y - 122 * s), (x + 26 * s, y - 122 * s)],
           (196, 186, 164), 2.6 * s)
    for dx in (-16, -4, 8):
        px = x + dx * s
        g.line([(px, y), (px + 14 * s, y - 168 * s)], P.WOOD, 5 * s)
        g.poly([(px + 12 * s, y - 158 * s), (px + 22 * s, y - 178 * s),
                (px + 16 * s, y - 156 * s)], fill=(150, 148, 142))
        g.line([(px, y - 6 * s), (px + 10 * s, y - 14 * s)], (220, 210, 190), 3 * s)


def chalk_doodle_timeline(g, box, color=(235, 240, 246)):
    """黒板のチョーク落書き (時代矢印+ミニ絵). テキストなし."""
    x0, y0, x1, y1 = box
    mid = (y0 + y1) / 2
    g.line([(x0, mid), (x1, mid)], color, 4)
    g.poly([(x1, mid), (x1 - 26, mid - 12), (x1 - 26, mid + 12)], fill=color)
    xs = [x0 + 60, x0 + 250, x0 + 440, x0 + 630]
    for i, cx in enumerate(xs):
        g.circle(cx, mid, 10, outline=color, owidth=3.4)
        g.line([(cx + 12, mid), ((xs[i + 1] - 14) if i < 3 else x1 - 30, mid)],
               color, 3)
    # ミニアイコン: 石器 / 土器 / 住居 / 古墳
    g.poly([(xs[0] - 16, mid - 26), (xs[0] + 16, mid - 26), (xs[0], mid - 54)],
           fill=None, outline=color, owidth=3)
    jomon_pot(g, xs[1], mid - 26, 0.22, body=color, pat_d=shade(color, 0.82),
              flame=False, seed=1)
    g.arc((xs[2] - 26, mid - 58, xs[2] + 26, mid + 6), 180, 360, color, 3.4)
    g.line([(xs[2] - 26, mid - 26), (xs[2] + 26, mid - 26)], color, 3.4)
    g.circle(xs[3], mid - 44, 14, outline=color, owidth=3)
    g.poly([(xs[3] + 32, mid - 90), (xs[3] + 10, mid - 50), (xs[3] - 10, mid - 50),
            (xs[3] - 32, mid - 90)], outline=color, owidth=3)


def bookshelf(g, x, y, w, h, seed=0):
    """本棚 (本の背表紙). y=棚下端."""
    rnd = random.Random(seed)
    rect(g, x, y - h, x + w, y, fill=(96, 78, 62), outline=(70, 56, 44), owidth=4)
    shelves = 4
    for s_i in range(shelves):
        sy = y - h * (s_i + 1) / shelves + 6
        rect(g, x + 8, sy, x + w - 8, sy + h / shelves - 10, fill=(120, 100, 80))
        bx = x + 16
        while bx < x + w - 30:
            bw = rnd.uniform(14, 26)
            bh = rnd.uniform(0.55, 0.9) * (h / shelves - 18)
            c = rnd.choice([P.INDIGO, P.SHU, P.YAMABUKI, P.WAKAKUSA,
                            (150, 130, 170), (170, 120, 90)])
            rect(g, bx, sy + h / shelves - 12 - bh, bx + bw, sy + h / shelves - 12, fill=c)
            g.line([(bx + bw / 2, sy + h / shelves - 12 - bh + 6),
                    (bx + bw / 2, sy + h / shelves - 16)], with_alpha((255, 255, 255), 90), 2)
            bx += bw + 4
    g.line([(x, y - h), (x + w, y - h)], (70, 56, 44), 6)


def window_frame(g, x, y, w, h, sky_stops, evening=False):
    """窓 (外に空と雲)."""
    g.rrect((x - 10, y - 10, x + w + 10, y + h + 10), 16, fill=(96, 110, 140))
    from artlib.canvas import gradient as _gr
    win = _gr((int(w * g.ss), int(h * g.ss)), sky_stops, "v")
    g.img.alpha_composite(win, (int(x * g.ss), int(y * g.ss)))
    wg = g
    rnd = random.Random(5)
    for i in range(3):
        cloud(wg, x + w * (0.28 + 0.3 * i), y + h * (0.3 + 0.18 * ((i * 7) % 3)),
              34 + 8 * i, seed=10 + i, alpha=235)
    if evening:
        sun(wg, x + w * 0.3, y + h * 0.62, 46, color=(248, 190, 120),
            core=(255, 228, 180), halo=0.3)
    # 框
    g.line([(x + w / 2, y - 6), (x + w / 2, y + h + 6)], (96, 110, 140), 12)
    g.line([(x - 6, y + h * 0.42), (x + w + 6, y + h * 0.42)], (96, 110, 140), 12)
    g.rrect((x - 24, y + h + 10, x + w + 24, y + h + 30), 8, fill=(84, 74, 66))


def blackboard(g, x, y, w, h):
    """藍色黒板 + チョーク落書き."""
    g.rrect((x - 14, y - 14, x + w + 14, y + h + 14), 12, fill=(96, 78, 62))
    g.rrect((x, y, x + w, y + h), 8, fill=(36, 58, 88))
    g.rrect((x + 8, y + 8, x + w - 8, y + h - 8), 6,
            fill=with_alpha((255, 255, 255), 26))
    chalk_doodle_timeline(g, (x + 50, y + 40, x + w - 60, y + h * 0.62))
    # 黑板消しとチョーク
    g.rrect((x + w * 0.62, y + h + 16, x + w * 0.72, y + h + 34), 6, fill=(140, 130, 120))
    for i in range(3):
        g.rrect((x + w * 0.3 + i * 26, y + h + 18, x + w * 0.3 + i * 26 + 20, y + h + 32),
                4, fill=(240, 240, 236))


def school_lab(cv, evening=False):
    """歴史資料室スタジオ (opening/ending 共通)."""
    wall_top = (206, 200, 190) if evening else (219, 226, 238)
    wall_bot = (232, 226, 214) if evening else (238, 242, 248)
    if evening:
        wall_top = (196, 168, 148)
        wall_bot = (228, 202, 172)
    sky(cv, [(0.0, wall_top), (0.68, wall_bot),
             (1.0, (170, 146, 118) if evening else (182, 156, 128))])
    g = cv.g()
    # 壁のパネル線
    g.line([(0, 640), (W, 640)], with_alpha((120, 100, 82), 90), 5)
    # 床 (板)
    fl_top = 640
    floor_grad = gradient((int(W * cv.ss), int((H - fl_top) * cv.ss)),
                          [(0, (196, 166, 134)), (1, (156, 126, 98))], "v")
    cv.img.alpha_composite(floor_grad, (0, int(fl_top * cv.ss)))
    rnd = random.Random(8)
    for i in range(1, 8):
        yy = fl_top + (H - fl_top) * (i / 7) ** 1.15
        g.line([(0, yy), (W, yy)], with_alpha((110, 86, 66), 120), 3)
    for _ in range(10):
        px = rnd.uniform(0, W)
        g.line([(px, fl_top), (px + rnd.uniform(-60, 60), H)], with_alpha((110, 86, 66), 45), 2.5)
    # 窓 (右)
    win_stops = P.SKY_EVENING if evening else P.SKY_DAY
    window_frame(g, 1400, 110, 400, 430, win_stops, evening=evening)
    if evening:
        # 窓からの夕光
        g.poly([(1400, 540), (1800, 540), (1960, 1080), (1240, 1080)],
               fill=with_alpha((255, 190, 120), 34))
    else:
        g.poly([(1400, 540), (1800, 540), (1960, 1080), (1240, 1080)],
               fill=with_alpha((255, 252, 235), 26))
    # 黒板 (中央左)
    blackboard(g, 330, 120, 900, 440)
    # 本棚 (左端)
    bookshelf(g, 40, 620, 210, 500, seed=2)
    # 本棚 (右端・窓の下は避ける)
    bookshelf(g, 1680, 940, 200, 380, seed=7)
    # 地球儀 (床に置く)
    gx, gy = 320, 1000
    g.ellipse((gx - 40, gy - 8, gx + 40, gy + 10), fill=with_alpha((90, 70, 56), 90))
    g.line([(gx, gy), (gx, gy - 40)], (90, 76, 62), 8)
    g.arc((gx - 48, gy - 132, gx + 48, gy - 40), 200, 250, (70, 100, 140), 4)
    g.circle(gx, gy - 86, 44, fill=(96, 150, 200), outline=(60, 90, 130), owidth=4)
    g.poly(blob_pts(gx - 8, gy - 90, 22, 16, seed=3, wobble=0.2),
           fill=(110, 178, 110))
    # 床のラグ (中央)
    g.ellipse((560, 900, 1420, 1050), fill=with_alpha((150, 60, 50), 90))
    g.ellipse((610, 912, 1370, 1036), fill=with_alpha((190, 90, 70), 90))
    # 暗い vignette
    vig = radial((int(W * cv.ss), int(H * cv.ss)), (10, 14, 30),
                 alpha_in=70, power=2.6)
    cv.img.alpha_composite(vig)
    if evening:
        # デスクランプの光
        gl = radial((700 * cv.ss, 500 * cv.ss), (255, 200, 120), alpha_in=60, power=2.4)
        cv.img.alpha_composite(gl, (int(500 * cv.ss), int(620 * cv.ss)))


def bg_school_lab(cv):
    school_lab(cv, evening=False)


def bg_school_lab_evening(cv):
    school_lab(cv, evening=True)


# ---------------------------------------------------------------- 旧石器


def bg_paleolithic(cv):
    sky(cv, P.SKY_DAWN)
    g = cv.g()
    sun(g, 330, 300, 52, color=(240, 226, 200), core=(250, 244, 228), halo=0.5)
    clouds_row(cv, 210, 3, 30, seed=11, base=(236, 240, 244), under=(200, 208, 218), alpha=180)
    mountain_ridge(cv, 560, 150, ((150, 164, 182), (196, 204, 214)), seed=4, freq=1.8)
    ridge(cv, 600, 90, (168, 172, 178), seed=9, freq=2.4)
    # 石灰岩の崖 (右 2/3)
    cliff = [(1150, 1080), (1150, 260)]
    cliff += ([(1150 + dx, 240 + dy) for (dx, dy) in
               [(-8, 30), (14, 40), (-6, 44), (18, 36), (4, 42), (-10, 46)]])
    cliff += [(1420, 0), (W, 0), (W, 1080)]
    g.poly(cliff, fill=(182, 176, 160))
    # 層理の帯
    for i, yy in enumerate(range(120, 900, 110)):
        pts = [(1160 + (i % 2) * 20, yy)]
        xx = 1180
        while xx < W:
            pts.append((xx, yy + math.sin(xx * 0.01 + i) * 12))
            xx += 90
        g.line(pts, with_alpha((140, 134, 118), 160), 10)
    # 岩のハイライト/陰
    speckle(g, (1180, 100, W, 1000), 140, [(206, 200, 184), (150, 144, 128), (168, 162, 146)],
            r=(3, 9), seed=3)
    # 転石 (崖下含む)
    for (bx, by, bs) in [(1080, 1000, 60), (900, 1020, 40), (1640, 1010, 70),
                         (1230, 700, 46), (1300, 760, 34), (1180, 820, 52),
                         (1750, 900, 58), (700, 690, 30)]:
        g.poly(blob_pts(bx, by - bs * 0.4, bs, bs * 0.72, seed=int(bx), wobble=0.16),
               fill=(190, 184, 168), outline=(150, 144, 128), owidth=3)
    # 地面
    ground(cv, 660, (172, 158, 136), dark=(140, 128, 108), curve=18, seed=6,
           speckles=260, speckle_colors=[(150, 138, 118), (190, 178, 156), (128, 116, 98)],
           speckle_r=(2, 6))
    # 焚き火 + 道具 + 骨
    campfire(g, 620, 900, 1.15, glow=True, seed=2)
    stone_tools(g, 960, 985, 1.55)
    bones(g, 420, 980, 1.0, seed=4)
    # 草むら (まばら)
    grass_tufts(g, (0, 700, 1150, 1060), 60, (150, 146, 96), seed=5, h=16, width=2.4)
    birds(g, [(1500, 190), (1600, 230), (1560, 260)], 13, color=(110, 112, 120), width=3.2)


# ---------------------------------------------------------------- 縄文


def bg_jomon_coast(cv):
    sky(cv, P.SKY_MORNING)
    g = cv.g()
    sun(g, 430, 240, 60, halo=0.5)
    clouds_row(cv, 190, 3, 34, seed=4)
    # 岬 (遠景)
    mountain_ridge(cv, 520, 120, ((96, 150, 150), (150, 190, 170)), seed=3, freq=2.4)
    # 海
    horizon = 520
    sea_grad = gradient((int(W * cv.ss), int((760 - horizon) * cv.ss)),
                        [(0, (110, 170, 200)), (0.6, (86, 148, 190)), (1, (70, 130, 175))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    rnd = random.Random(6)
    for _ in range(26):
        yy = rnd.uniform(horizon + 10, 750)
        ln = rnd.uniform(30, 150)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)),
                3, fill=with_alpha((240, 250, 255), rnd.randint(60, 150)))
    # 浜 (砂)
    beach = [(0, 730)] + [(x, 730 + math.sin(x * 0.004 + 1.2) * 22 + x * 0.02)
                          for x in range(0, W + 1, 120)] + [(W, 1080), (0, 1080)]
    g.poly(beach, fill=(222, 202, 164))
    g.line(beach[:14], (198, 178, 142), 5)
    speckle(g, (0, 780, W, 1080), 220, [(206, 186, 150), (240, 224, 192), (182, 162, 128)],
            r=(1.6, 4.5), seed=8)
    # 打ち寄せの泡
    for i in range(3):
        yy = 745 + i * 16
        g.arc((-100, yy - 14, W + 100, yy + 40), 190, 350,
              with_alpha((255, 255, 255), 150 - i * 40), 7 - i * 1.6)
    # 貝塚と舟
    shell_mound(g, 330, 960, 1.05, seed=2)
    boat(g, 1350, 950, 1.05, oars=1, seed=1)
    # 浜の木 (背後)
    forest_band(cv, 742, 8, (0.7, 1.0), leaf=(96, 156, 108), seed=5)
    grass_tufts(g, (0, 820, W, 1060), 50, (150, 172, 110), seed=6)
    # 貝殻散らし
    for _ in range(16):
        sx, sy = rnd.uniform(60, 1860), rnd.uniform(840, 1050)
        g.ellipse((sx - 8, sy - 5, sx + 8, sy + 5), fill=(240, 232, 214),
                  outline=(180, 164, 136), owidth=1.6)
    birds(g, [(1500, 220), (1600, 260), (1560, 180)], 14, width=3.4)


def bg_jomon_pottery(cv):
    # 森の内部
    sky(cv, [(0.0, (150, 186, 140)), (0.5, (196, 216, 168)), (1.0, (232, 226, 178))])
    g = cv.g()
    ground(cv, 700, (150, 172, 110), dark=(120, 142, 88), curve=14, seed=3,
           speckles=200, speckle_colors=[(128, 150, 92), (170, 190, 128), (108, 128, 78)],
           speckle_r=(2, 5))
    # 奥の森
    forest_band(cv, 690, 10, (0.5, 0.9), leaf=(96, 148, 100), seed=8)
    # 光の柱
    light_shafts(cv, [[(300, 0), (430, 0), (660, 1080), (440, 1080)],
                      [(900, 0), (1010, 0), (1290, 1080), (1090, 1080)],
                      [(1500, 0), (1600, 0), (1840, 1080), (1650, 1080)]],
                 color=(255, 250, 210), alpha=30)
    # 大木 (左右フレーム)
    tree(cv, 130, 1010, 2.6, kind="oak", leaf=(104, 158, 104), seed=1)
    tree(cv, 1810, 980, 2.4, kind="oak", leaf=(104, 158, 104), seed=2)
    tree(cv, 620, 700, 1.1, kind="oak", leaf=(92, 146, 98), seed=3)
    tree(cv, 1500, 680, 0.9, kind="pine", leaf=(70, 128, 92), seed=4)
    # 土器を載せた切り株
    sx, sy = 950, 940
    g.ellipse((sx - 150, sy - 20, sx + 150, sy + 26), fill=with_alpha((70, 60, 40), 70))
    g.rrect((sx - 110, sy - 150, sx + 110, sy), 16, fill=(148, 110, 72),
            outline=(112, 82, 52), owidth=4)
    g.ellipse((sx - 110, sy - 160, sx + 110, sy - 128), fill=(190, 158, 112),
              outline=(150, 122, 84), owidth=3)
    g.ellipse((sx - 74, sy - 152, sx + 74, sy - 138), fill=(120, 150, 92))
    jomon_pot(g, sx, sy - 148, 1.35, seed=5)
    # どんぐりと鹿
    for (ax, ay, as_) in [(330, 1040, 1.5), (430, 1000, 1.1), (1580, 1050, 1.6),
                          (1660, 1010, 1.2), (250, 990, 0.9)]:
        draw_acorn(g, ax, ay, as_)
    deer(g, 1560, 860, 0.85, flip=-1)
    deer(g, 1680, 900, 0.55, antlers=False, flip=1)
    grass_tufts(g, (0, 760, W, 1060), 90, (120, 152, 88), seed=7)
    # 木漏れ日の斑点
    rnd = random.Random(9)
    for _ in range(16):
        px, py = rnd.uniform(200, 1750), rnd.uniform(780, 1050)
        g.ellipse((px - 26, py - 10, px + 26, py + 10), fill=with_alpha((255, 248, 200), 46))


def bg_jomon_village(cv):
    sky(cv, P.SKY_MORNING)
    g = cv.g()
    sun(g, 1520, 200, 58, halo=0.4)
    clouds_row(cv, 170, 3, 36, seed=6)
    mountain_ridge(cv, 520, 170, ((108, 148, 168), (168, 196, 190)), seed=2, freq=1.9)
    ridge(cv, 580, 90, (128, 168, 148), seed=7, freq=2.6)
    forest_band(cv, 668, 9, (0.6, 1.0), leaf=(96, 150, 100), seed=3)
    ground(cv, 660, (168, 178, 112), dark=(140, 150, 90), curve=16, seed=4,
           speckles=180, speckle_colors=[(150, 160, 96), (184, 192, 128), (128, 138, 82)],
           speckle_r=(2, 5))
    # 広場の土
    g.ellipse((360, 800, 1620, 1060), fill=with_alpha((190, 164, 118), 150))
    g.ellipse((500, 850, 1480, 1020), fill=with_alpha((206, 180, 132), 130))
    # 竪穴住居 ×4 (環状配置風)
    pit_house(g, 470, 810, 1.0, smoke=True, seed=1)
    pit_house(g, 1430, 790, 1.05, seed=2)
    pit_house(g, 240, 880, 0.85, seed=3)
    pit_house(g, 1690, 900, 0.8, seed=4)
    # 中央の焚き火
    campfire(g, 965, 950, 0.85, seed=5)
    # 土器
    jomon_pot(g, 1210, 1000, 0.62, seed=6, flame=False)
    jomon_pot(g, 700, 1010, 0.5, seed=7, flame=True)
    # 前景の大木
    tree(cv, 120, 1060, 1.7, kind="oak", leaf=(100, 154, 102), seed=9)
    grass_tufts(g, (0, 700, W, 1080), 110, (134, 156, 90), seed=10)
    birds(g, [(500, 200), (610, 240), (570, 170)], 13, width=3.4)
    # どんぐりの木の実
    rnd_ac = random.Random(11)
    for _ in range(5):
        draw_acorn(g, rnd_ac.uniform(60, 240), rnd_ac.uniform(980, 1070), 1.0)


def bg_jomon_daily_life(cv):
    sky(cv, P.SKY_DAY)
    g = cv.g()
    clouds_row(cv, 150, 3, 32, seed=8)
    mountain_ridge(cv, 500, 140, ((110, 150, 170), (170, 198, 186)), seed=5, freq=2.1)
    forest_band(cv, 650, 10, (0.6, 1.0), leaf=(94, 148, 100), seed=4)
    ground(cv, 650, (168, 178, 112), dark=(138, 148, 90), curve=14, seed=6,
           speckles=170, speckle_colors=[(150, 160, 96), (184, 192, 128)],
           speckle_r=(2, 5))
    # 川 (右奥から手前へ)
    river = [(1250, 650), (1450, 720), (1700, 790), (W, 860), (W, 960),
             (1600, 880), (1350, 800), (1150, 730), (1050, 680)]
    g.poly(river + [(1250, 650)], fill=(120, 172, 202))
    g.line([(1150, 730), (1350, 800), (1600, 880)], with_alpha((240, 250, 255), 120), 4)
    g.line([(1250, 650), (1450, 720), (1700, 790)], with_alpha((240, 250, 255), 90), 3)
    # 貝塚 / 土偶 / 弓矢 / 魚干し / 焚き火と土器
    shell_mound(g, 300, 970, 1.0, seed=3)
    dogu(g, 640, 950, 1.0)
    bow_and_arrows(g, 880, 970, 1.0)
    fish_hanging(g, 1290, 890, 0.95, seed=2)
    campfire(g, 1580, 1010, 0.9, seed=6)
    jomon_pot(g, 1720, 1000, 0.55, seed=8, flame=True)
    # 前景の草と花
    grass_tufts(g, (0, 700, 1150, 1070), 100, (134, 156, 90), seed=9)
    rnd = random.Random(10)
    for _ in range(12):
        fx, fy = rnd.uniform(40, 1100), rnd.uniform(760, 1060)
        g.line([(fx, fy), (fx, fy - 16)], (150, 166, 108), 2.6)
        g.circle(fx, fy - 20, 5, fill=(238, 214, 130))
        g.circle(fx, fy - 20, 2.4, fill=(214, 150, 60))
    birds(g, [(700, 190), (800, 230), (760, 170)], 12, width=3.2)


# ---------------------------------------------------------------- 弥生


def bg_yayoi_rice_field(cv):
    sky(cv, P.SKY_DAY)
    g = cv.g()
    sun(g, 350, 190, 56, halo=0.45)
    clouds_row(cv, 160, 3, 34, seed=3)
    mountain_ridge(cv, 430, 190, ((96, 140, 150), (150, 186, 160)), seed=6, freq=1.7,
                   snowline=0.0)
    ridge(cv, 500, 80, (120, 162, 130), seed=8, freq=2.4)
    # 山裾の林
    forest_band(cv, 560, 12, (0.45, 0.8), leaf=(88, 146, 96), seed=5)
    # 中景の丘 + 高床倉庫
    hill = [(0, 700)] + [(x, 700 - 120 * math.exp(-((x - 480) / 420.0) ** 2))
                         for x in range(0, W + 1, 60)] + [(W, 700), (W, 780), (0, 780)]
    g.poly(hill, fill=(150, 172, 108))
    warehouse(g, 430, 590, 0.78, seed=1)
    warehouse(g, 700, 640, 0.5, seed=2, ladder=False)
    # 水田帯 (空を映す)
    rice_paddy(cv, 770, 1080, [(186, 216, 236), (142, 201, 232)], seed=7, rows_seed=3)
    # 畦道 (手前から奥への小道)
    g.poly([(880, 1080), (1000, 1080), (1010, 770), (960, 770)], fill=(188, 158, 112))
    g.line([(958, 772), (1008, 1078)], (160, 132, 92), 4)
    # 銅鐸の木架 (手前右)
    dotaku_stand(g, 1640, 1030, 0.9)
    # 霞
    for yy in (700, 735):
        g.ellipse((-100, yy - 16, W + 100, yy + 16), fill=with_alpha((255, 255, 255), 40))
    birds(g, [(1200, 200), (1300, 240), (1260, 170)], 13, width=3.4)


def bg_yayoi_village(cv):
    sky(cv, [(0.0, (110, 176, 218)), (0.55, (150, 202, 232)), (1.0, (228, 240, 244))])
    g = cv.g()
    clouds_row(cv, 150, 3, 32, seed=9)
    mountain_ridge(cv, 420, 160, ((100, 142, 158), (160, 190, 172)), seed=4, freq=1.8)
    forest_band(cv, 540, 10, (0.5, 0.85), leaf=(90, 146, 98), seed=6)
    ground(cv, 590, (166, 176, 110), dark=(138, 148, 90), curve=14, seed=7,
           speckles=150, speckle_colors=[(148, 158, 94), (182, 190, 126)],
           speckle_r=(2, 5))
    # 棚田風の段
    for i, (y0, y1) in enumerate([(660, 720), (730, 790), (800, 860)]):
        rect(g, 0, y0, W, y1, fill=(174, 184, 118))
        g.line([(0, y1), (W, y1)], (140, 148, 92), 4)
    # 集落台地
    g.ellipse((300, 800, 1650, 1000), fill=with_alpha((196, 176, 128), 200))
    # 高床倉庫 (主) + 小 + 平地住居
    warehouse(g, 660, 820, 0.95, seed=3)
    warehouse(g, 1080, 760, 0.6, seed=4, ladder=False)
    pit_house(g, 1460, 860, 0.75, seed=5, smoke=False)
    # 弥生土器と作業場
    yayoi_pot(g, 880, 1000, 0.85, seed=1)
    yayoi_pot(g, 1240, 1010, 0.55, seed=2)
    jomon_pot(g, 380, 990, 0.5, flame=False, seed=3)
    # 柵
    palisade(g, 240, 900, 700, 0.8, seed=2)
    palisade(g, 1180, 1720, 700, 0.8, seed=3)
    # 水田の縁 (最前景)
    rice_paddy(cv, 1010, 1080, [(200, 224, 240), (160, 208, 234)], seed=10, rows_seed=5)
    tree(cv, 120, 660, 1.2, kind="oak", leaf=(98, 152, 100), seed=8)
    tree(cv, 1840, 640, 1.0, kind="pine", leaf=(74, 130, 94), seed=9)
    birds(g, [(400, 190), (500, 230), (460, 160)], 12, width=3.2)


def bg_yayoi_moat(cv):
    sky(cv, P.SKY_SUNSET)
    g = cv.g()
    sun(g, 1480, 330, 92, color=(248, 196, 110), core=(252, 226, 160), halo=0.6)
    clouds_row(cv, 200, 3, 40, seed=5, base=(214, 130, 100), under=(120, 70, 84), alpha=220)
    # 遠景の稜線 (シルエット)
    mountain_ridge(cv, 500, 130, ((84, 56, 84), (140, 80, 82)), seed=8, freq=1.6)
    # 集落の台地
    plateau = [(140, 1080), (140, 700)] + [(x, 690 - 40 * math.sin(x * 0.004))
                                           for x in range(140, 1781, 60)] + \
              [(1780, 700), (1780, 1080)]
    g.poly(plateau, fill=(118, 96, 84))
    g.line(plateau[1:14], (96, 76, 68), 5)
    # 環濠 (水面が夕日を映す)
    moat_y0, moat_y1 = 760, 850
    rect(g, 0, moat_y0, W, moat_y1, fill=(74, 66, 104))
    rnd = random.Random(9)
    for _ in range(24):
        yy = rnd.uniform(moat_y0 + 6, moat_y1 - 6)
        ln = rnd.uniform(40, 200)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(3, 6)), 3,
                fill=with_alpha((248, 170, 100), rnd.randint(70, 170)))
    g.line([(0, moat_y0), (W, moat_y0)], (90, 74, 96), 6)
    g.line([(0, moat_y1), (W, moat_y1)], (60, 50, 74), 5)
    # 手前の地面
    rect(g, 0, moat_y1, W, H, fill=(96, 80, 88))
    speckle(g, (0, 860, W, 1080), 140, [(84, 68, 78), (112, 92, 98), (128, 100, 96)],
            r=(2, 6), seed=4)
    # 集落: 柵と住居 (シルエット気味)
    palisade(g, 200, 960, 700, 0.85, col=(84, 56, 48), dark=(60, 40, 36), seed=6)
    palisade(g, 1000, 1720, 700, 0.85, col=(84, 56, 48), dark=(60, 40, 36), seed=7)
    pit_house(g, 520, 668, 0.72, roof=(158, 122, 74), roof_d=(120, 92, 58), seed=8)
    pit_house(g, 860, 660, 0.6, roof=(150, 116, 70), roof_d=(114, 88, 54), seed=9)
    pit_house(g, 1240, 672, 0.66, roof=(162, 126, 76), roof_d=(124, 94, 58), seed=10)
    warehouse(g, 1500, 660, 0.42, wall=(150, 122, 88), ladder=False, seed=11)
    # 緊張感: 遠くの火と煙、カラス
    g.poly(qbez_fire(1180, 640, 1.2), fill=(240, 150, 70))
    smoke_wisp(g, 1190, 600, 0.8, color=(90, 74, 90), alpha=170, seed=3)
    birds(g, [(400, 240), (520, 210), (640, 260), (1560, 200), (1650, 240)], 12,
          color=(52, 40, 52), width=4)
    # 前景の芒 (シルエット)
    reeds_fg(cv, 1080, seed=5, color=(48, 38, 48), n=36, s=1.1)


def qbez_fire(x, y, s):
    from artlib.canvas import qbez
    return (qbez((x - 16 * s, y), (x - 14 * s, y - 30 * s), (x, y - 52 * s), 8)
            + qbez((x, y - 52 * s), (x + 14 * s, y - 30 * s), (x + 16 * s, y), 8))


# ---------------------------------------------------------------- 古墳


def bg_kofun(cv):
    sky(cv, P.SKY_DAY)
    g = cv.g()
    clouds_row(cv, 120, 3, 40, seed=2)
    # 遠景の地平 (上空からの俯瞰の視線を示唆)
    ridge(cv, 250, 80, (150, 186, 168), seed=3, freq=2.2)
    # 地面 (草原の平面・上空 260px は残す)
    plain = gradient((int(W * cv.ss), int((H - 260) * cv.ss)),
                     [(0, (168, 196, 128)), (0.5, (140, 176, 108)), (1, (112, 148, 92))], "v")
    cv.img.alpha_composite(plain, (0, int(260 * cv.ss)))
    # 周囲の畑 (パッチ)
    rnd = random.Random(5)
    for _ in range(16):
        px, py = rnd.uniform(-60, 1800), rnd.uniform(60, 1020)
        pw, ph = rnd.uniform(90, 220), rnd.uniform(60, 140)
        if abs(px - 960) < 420 and abs(py - 600) < 380:
            continue
        rect(g, px, py, px + pw, py + ph,
             fill=rnd.choice([(196, 210, 140), (180, 200, 132), (208, 218, 150)]))
        for lx in range(int(px) + 10, int(px + pw) - 8, 18):
            g.line([(lx, py + 4), (lx, py + ph - 4)], with_alpha((140, 160, 100), 120), 2)
    # 木々の cluster
    for (tx, ty, ts) in [(210, 300, 0.9), (420, 240, 0.7), (1650, 300, 0.85),
                         (1780, 820, 0.9), (260, 900, 0.8), (1620, 960, 0.75)]:
        tree(cv, tx, ty, ts, kind="oak", leaf=(96, 152, 100), seed=int(tx))
    # 参道 (古墳の下に敷く)
    g.poly([(830, 884), (1090, 884), (1044, 208), (876, 208)], fill=(206, 190, 150))
    g.line([(877, 210), (831, 882)], (176, 160, 124), 4)
    g.line([(1043, 210), (1089, 882)], (176, 160, 124), 4)
    # 前方後円墳 (主役・中央)
    keyhole_tomb(g, 960, 660, 1.3, seed=1)
    # 雲の影
    g.poly(blob_pts(1300, 300, 260, 90, seed=9, wobble=0.2),
           fill=with_alpha((40, 70, 40), 36))
    g.poly(blob_pts(500, 900, 220, 80, seed=10, wobble=0.2),
           fill=with_alpha((40, 70, 40), 30))
    birds(g, [(300, 150), (380, 120)], 11, width=3)


def bg_kofun_haniwa(cv):
    sky(cv, P.SKY_DAY)
    g = cv.g()
    sun(g, 1560, 170, 52, halo=0.4)
    clouds_row(cv, 180, 2, 36, seed=6)
    # 古墳の裾 (画面下半分が墳丘の斜面)
    mound = [(0, 560)] + [(x, 560 + 60 * math.sin(x * 0.003 + 0.8)) for x in range(0, W + 1, 120)] + \
        [(W, 1080), (0, 1080)]
    g.poly(mound, fill=(124, 172, 104))
    g.line(mound[:14], (100, 146, 86), 6)
    # 段築のテラス
    g.arc((-200, 780, W + 200, 1140), 20, 160, (100, 148, 86), 26)
    speckle(g, (0, 600, W, 1080), 220, [(140, 184, 118), (108, 152, 92), (160, 196, 128)],
            r=(2, 5), seed=3)
    # 埴輪の列 (斜面に沿って・透視風に大きく)
    haniwa(g, 240, 880, 1.15, seed=1)
    haniwa(g, 620, 940, 1.3, seed=2, hat=False)
    haniwa(g, 1030, 900, 1.2, seed=3)
    haniwa(g, 1440, 970, 1.35, seed=4, hat=False)
    # 円筒埴輪
    for (cx0, cy0, cs) in [(440, 1020, 0.8), (830, 1050, 0.85), (1240, 1030, 0.8)]:
        g.poly([(cx0 - 30 * cs, cy0), (cx0 - 24 * cs, cy0 - 110 * cs),
                (cx0 + 24 * cs, cy0 - 110 * cs), (cx0 + 30 * cs, cy0)],
               fill=P.CLAY, outline=P.CLAY_D, owidth=2.6 * cs)
        g.ellipse((cx0 - 30 * cs, cy0 - 8 * cs, cx0 + 30 * cs, cy0 + 8 * cs),
                  fill=shade(P.CLAY_D, 0.75))
        g.line([(cx0 - 26 * cs, cy0 - 70 * cs), (cx0 + 26 * cs, cy0 - 70 * cs)], P.CLAY_D, 4 * cs)
    # 草花
    grass_tufts(g, (0, 600, W, 1080), 90, (110, 154, 84), seed=5)
    rnd = random.Random(7)
    for _ in range(14):
        fx, fy = rnd.uniform(40, 1880), rnd.uniform(620, 1060)
        g.circle(fx, fy, 4.5, fill=(238, 214, 130))
        g.circle(fx, fy, 2, fill=(214, 150, 60))
    birds(g, [(600, 220), (700, 260)], 11, width=3.2)


def bg_yamato_court(cv):
    sky(cv, P.SKY_NIGHT)
    g = cv.g()
    stars(g, (60, 60, 1860, 520), 130, seed=3, sparkle=8)
    moon(cv, 1620, 190, 62, cut_color=(16, 24, 58))
    # 遠景の山 (夜)
    mountain_ridge(cv, 520, 120, ((26, 36, 66), (44, 60, 96)), seed=5, freq=1.7)
    # 地面
    ground(cv, 620, (44, 62, 74), dark=(34, 48, 60), curve=14, seed=6,
           speckles=110, speckle_colors=[(52, 72, 84), (38, 54, 64)], speckle_r=(2, 5))
    # 参道
    g.poly([(760, 1080), (1160, 1080), (1060, 660), (860, 660)], fill=(60, 78, 88))
    g.line([(862, 662), (764, 1078)], (48, 64, 74), 4)
    g.line([(1058, 662), (1156, 1078)], (48, 64, 74), 4)
    # 大型殿屋
    big_hall(g, 960, 900, 1.35, lit=True, seed=2)
    # 松明と旗
    torch(g, 380, 1000, 1.15)
    torch(g, 1540, 1000, 1.15)
    banner_pole(g, 200, 960, 0.95)
    banner_pole(g, 1720, 960, 0.95)
    # 棟のシルエット樹
    tree(cv, 80, 700, 1.2, kind="pine", leaf=(30, 52, 56), seed=3)
    tree(cv, 1850, 690, 1.1, kind="pine", leaf=(30, 52, 56), seed=4)
    # 霞
    g.ellipse((-100, 880, W + 100, 960), fill=with_alpha((120, 140, 180), 40))
    # 殿屋の窓明かりのグロー
    gl = radial((900 * cv.ss, 500 * cv.ss), (255, 200, 120), alpha_in=70, power=2.4)
    cv.img.alpha_composite(gl, (int(510 * cv.ss), int(520 * cv.ss)))


def bg_kofun_ships(cv):
    sky(cv, [(0.0, (120, 180, 218)), (0.5, (170, 212, 236)), (0.8, (240, 232, 200)), (1.0, (250, 238, 210))])
    g = cv.g()
    sun(g, 1180, 210, 64, color=(250, 216, 150), core=(254, 238, 190), halo=0.55)
    clouds_row(cv, 170, 3, 34, seed=8)
    horizon = 400
    sea_grad = gradient((int(W * cv.ss), int((H - horizon) * cv.ss)),
                        [(0, (140, 190, 214)), (0.4, (92, 152, 196)),
                         (1, (60, 118, 172))], "v")
    cv.img.alpha_composite(sea_grad, (0, int(horizon * cv.ss)))
    # 太陽の反射帯
    for i in range(9):
        yy = horizon + 20 + i * 70
        ln = 220 - i * 16
        g.rrect((1180 - ln / 2 + math.sin(i * 2.2) * 60, yy, 1180 + ln / 2 + math.sin(i * 2.2) * 60,
                 yy + 10), 5, fill=with_alpha((255, 232, 170), 110 - i * 8))
    rnd = random.Random(7)
    for _ in range(30):
        yy = rnd.uniform(horizon + 10, H - 20)
        ln = rnd.uniform(30, 160)
        xx = rnd.uniform(0, W - ln)
        g.rrect((xx, yy, xx + ln, yy + rnd.uniform(2.5, 5)), 3,
                fill=with_alpha((240, 250, 255), rnd.randint(50, 130)))
    # 波うねり
    for i in range(5):
        yy = horizon + 90 + i * 130
        g.arc((rnd.uniform(-200, 400), yy - 30, rnd.uniform(1400, 2100), yy + 60),
              190, 350, with_alpha((235, 246, 252), 80), 4)
    # 遠くの岬と緑の島
    mountain_ridge(cv, horizon + 10, 60, ((120, 150, 150), (150, 180, 160)), seed=11, freq=3.0)
    g.poly(blob_pts(300, horizon - 8, 130, 46, seed=12, wobble=0.18),
           fill=(140, 178, 132))
    # 船団 (倭の五王の遣使イメージ)
    boat(g, 480, 830, 1.0, figure=True, seed=1)
    boat(g, 980, 920, 1.3, figure=True, seed=2)
    boat(g, 1500, 760, 0.85, figure=True, oars=1, seed=3)
    birds(g, [(400, 300), (520, 340), (470, 270), (1450, 260), (1560, 300)], 13, width=3.4)


# ---------------------------------------------------------------- ポイント/クイズ


def bg_timeline(cv):
    """ep01 用ポイント背景 — 旧石器〜古墳のタイムライン (ep02/03 と同デザイン).

    ノード直上に時代アイコン、直下に時代ラベル。kenburns クロップ安全域つき。
    """
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
    labels = ["旧石器", "縄文", "弥生", "古墳時代"]
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
    # ノード直上に時代アイコン (打製石器 / 土器+竪穴住居 / 銅鐸 / 前方後円墳)
    stone_tools(g, nodes[0], icon_y, 1.15)
    jomon_pot(g, nodes[1] - 52, icon_y, 0.52, seed=1)
    pit_house(g, nodes[1] + 66, icon_y, 0.44, seed=2)
    dotaku(g, nodes[2], icon_y + 2, 0.8, seed=3)
    keyhole_tomb(g, nodes[3], icon_y - 62, 0.42, seed=4)
    gl = radial((int(1400 * cv.ss), int(900 * cv.ss)), (90, 120, 200),
                alpha_in=50, power=2.4)
    cv.img.alpha_composite(gl, (int(260 * cv.ss), int(160 * cv.ss)))


def bg_quiz_board(cv):
    # 放射のポップ背景 (山吹 × 朱)
    cv.img.alpha_composite(gradient(cv.img.size, [(0, (255, 214, 120)), (1, (250, 190, 96))], "v"))
    g = cv.g()
    cx, cy = W / 2, H / 2 - 40
    n = 22
    for i in range(n):
        a0 = 360.0 * i / n
        c = P.YAMABUKI if i % 2 == 0 else (242, 170, 74)
        g.pieslice((cx - 2400, cy - 2400, cx + 2400, cy + 2400),
                   a0, a0 + 360.0 / n + 0.5, fill=c)
    # 中央のボード
    bx0, by0, bx1, by1 = 380, 170, 1540, 900
    g.rrect((bx0 - 26, by0 - 26, bx1 + 26, by1 + 26), 40,
            fill=with_alpha((60, 30, 30), 120))
    g.rrect((bx0, by0, bx1, by1), 30, fill=with_alpha(P.UI_WHITE, 240),
            outline=P.INDIGO, owidth=10)
    # ピン (板留め)
    for px in (bx0 + 60, bx1 - 60):
        g.circle(px, by0 + 30, 14, fill=P.SHU, outline=shade(P.SHU, 0.75), owidth=3)
    # コーナーのハーフトーン
    dots_pattern(g, (0, 0, 420, 300), 40, 7, P.SHU, alpha=110, seed=5)
    dots_pattern(g, (1500, 780, W, H), 40, 7, P.SHU, alpha=110, seed=6)
    # 紙吹雪
    rnd = random.Random(9)
    for _ in range(26):
        px, py = rnd.uniform(0, W), rnd.uniform(0, H)
        if bx0 - 40 < px < bx1 + 40 and by0 - 40 < py < by1 + 40:
            continue
        c = rnd.choice([P.SHU, P.INDIGO, P.UI_WHITE, P.WAKAKUSA])
        s = rnd.uniform(6, 14)
        ang = rnd.uniform(0, math.tau)
        pts = [(px + s * math.cos(ang + k * math.pi / 2),
                py + s * 0.6 * math.sin(ang + k * math.pi / 2)) for k in range(4)]
        g.poly(pts, fill=c)
    # ボード上の罫 (クイズの選択欄イメージ)
    for i in range(3):
        yy = by0 + 160 + i * 180
        g.line([(bx0 + 70, yy), (bx1 - 70, yy)], with_alpha((90, 110, 150), 90), 3.4)
        g.rrect((bx0 + 50, yy - 40, bx0 + 110, yy + 16), 10,
                fill=with_alpha((90, 110, 150), 60))

"""アニメ調人物 — 目・髪・顔パーツと立ち絵 (char_sensei / char_manabu).

約 900x1400 の透過 PNG を想定。大きな目・シンプル房分割の髪・フラット影。
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw

from .canvas import (Canvas, Layer, almond_pts, cbez, qbez, shade, sublayer,
                     tint, with_alpha)
from . import palette as P

SKIN = P.SKIN
SKIN_SH = P.SKIN_SH
INK = P.OUTLINE


# ---------------------------------------------------------------- パーツ


def anime_eye(cv, cx, cy, w, h, iris=(62, 108, 158), flip=1, lash_w=7.0,
              look=(0.0, 0.0), lash=None, calm=False):
    """大きなアニメ目. flip=1 で左目 (ハイライト左上). lash はまつ毛色."""
    lay = sublayer(cv)
    lg = lay.g()
    pts = almond_pts(cx, cy, w, h)
    # 白目
    sclera = sublayer(cv)
    sclera.g().poly(pts, fill=(255, 255, 255, 255))
    # 虹彩 (白目でクリップ)
    iris_lay = sublayer(cv)
    ig = iris_lay.g()
    icx = cx + look[0] * w * 0.18
    icy = cy + h * 0.10 + look[1] * h * 0.15
    r = min(w, h) * 0.62
    ig.circle(icx, icy, r * 1.14, fill=shade(iris, 0.62))
    ig.circle(icx, icy, r, fill=iris)
    ig.circle(icx, icy, r * 0.46, fill=(44, 36, 52))
    ig.circle(icx, icy, r * 0.20, fill=(20, 16, 26))
    ig.circle(icx - r * 0.38, icy - r * 0.42, r * 0.30, fill=(255, 255, 255))
    ig.circle(icx + r * 0.30, icy + r * 0.34, r * 0.14,
              fill=with_alpha((255, 255, 255), 210))
    ig.ellipse((icx - r * 0.9, icy - r * 0.35, icx + r * 0.9, icy + r * 0.55),
               fill=with_alpha((255, 255, 255), 26))
    ig.flush()
    mask = sclera.img.split()[3]
    from .canvas import paste_masked
    paste_masked(lay.img, iris_lay.img, mask)
    # 上まぶたの影
    top_pts = almond_pts(cx, cy, w, h)[:26]
    lg.line([(p[0], p[1] + h * 0.22) for p in top_pts],
            with_alpha((120, 70, 70), 60), h * 0.26)
    # まつ毛 (上線)
    lc = lash or (70, 52, 60)
    lg.line(top_pts, lc, lash_w)
    # 目頭・外角のツン
    fx = flip * (w * 0.52)
    lg.line([(cx + fx, cy - h * 0.16), (cx + fx * 1.18, cy - h * 0.34)], lc, lash_w * 0.8)
    # 下まぶた
    bot_pts = almond_pts(cx, cy, w, h)[26:]
    lg.line([(p[0], p[1] - 1.5) for p in bot_pts[2:-2]],
            with_alpha((120, 70, 70), 130), 2.0)
    lg.flush()
    cv.img.alpha_composite(lay.img)


def brow(g, cx, cy, w, angle=0.0, color=(70, 52, 60), width=6.5, flip=1):
    """眉 (angle>0 で内側下がり)."""
    dx = w / 2
    dy = math.tan(math.radians(angle)) * dx
    pts = qbez((cx - dx, cy - dy * flip), (cx, cy + dy * flip * 0.4),
               (cx + dx, cy + dy), 12)
    g.line(pts, color, width)


def mouth(g, cx, cy, w, style="smile", col=(186, 84, 74)):
    if style == "line":
        g.arc((cx - w / 2, cy - w * 0.22, cx + w / 2, cy + w * 0.22),
              15, 165, col, 4.5)
    elif style == "smile":
        g.arc((cx - w / 2, cy - w * 0.30, cx + w / 2, cy + w * 0.30),
              10, 170, col, 5.5)
    elif style in ("open", "grin"):
        hh = w * (0.42 if style == "grin" else 0.5)
        g.pieslice((cx - w / 2, cy - hh * 0.5, cx + w / 2, cy + hh),
                   0, 180, fill=(126, 56, 62), outline=(96, 42, 48), owidth=2.5)
        # 歯
        g.chord((cx - w / 2 + 3, cy - hh * 0.52, cx + w / 2 - 3, cy + hh * 0.16),
                180, 360, fill=(255, 253, 247))
        # 舌
        g.ellipse((cx - w * 0.28, cy + hh * 0.34, cx + w * 0.28, cy + hh * 0.98),
                  fill=(226, 110, 100))


def blush(g, cx, cy, w, color=(238, 128, 110), alpha=80):
    g.ellipse((cx - w, cy - w * 0.42, cx + w, cy + w * 0.42),
              fill=with_alpha(color, alpha))
    g.ellipse((cx - w * 0.6, cy - w * 0.26, cx + w * 0.6, cy + w * 0.26),
              fill=with_alpha(color, min(255, alpha + 30)))


def nose(g, cx, cy, col=(214, 150, 126)):
    g.arc((cx - 5, cy - 4, cx + 5, cy + 5), 10, 150, col, 3)


def face_and_neck(cv, cx, cy, r, skin=SKIN, outline=INK, ow=3.0):
    """顔 (角丸+尖った顎) と首. 顔中心 (cx,cy), 半径 r."""
    g = cv.g()
    # 首 (先に: 顔の下)
    nw = r * 0.36
    g.poly([(cx - nw * 0.8, cy + r * 0.72), (cx + nw * 0.8, cy + r * 0.72),
            (cx + nw * 1.15, cy + r * 1.5), (cx - nw * 1.15, cy + r * 1.5)],
           fill=skin, outline=outline, owidth=ow * 0.8)
    g.poly([(cx - nw * 0.85, cy + r * 0.74), (cx + nw * 0.85, cy + r * 0.74),
            (cx + nw * 0.95, cy + r * 0.98), (cx - nw * 0.95, cy + r * 0.98)],
           fill=with_alpha(SKIN_SH, 170))
    # 顔輪郭: 上は円弧・下は顎へテーパー
    pts = []
    n = 26
    for i in range(n + 1):
        a = math.radians(150 + 240 * i / n)  # 150°→390° (上を通る)
        pts.append((cx + r * 1.02 * math.cos(a), cy + r * 0.96 * math.sin(a)))
    chin = (cx, cy + r * 1.18)
    right = (cx + r * 0.99, cy + r * 0.5)
    left = (cx - r * 0.99, cy + r * 0.5)
    jaw_r = cbez(right, (cx + r * 0.8, cy + r * 1.02), (cx + r * 0.34, cy + r * 1.2),
                 chin, 12)
    jaw_l = cbez(chin, (cx - r * 0.34, cy + r * 1.2), (cx - r * 0.8, cy + r * 1.02),
                 left, 12)
    full = pts + jaw_r + jaw_l
    g.poly(full, fill=skin, outline=outline, owidth=ow)
    # 耳
    for sx in (-1, 1):
        ex = cx + sx * r * 0.98
        g.ellipse((ex - r * 0.14, cy - r * 0.06, ex + r * 0.14, cy + r * 0.3),
                  fill=skin, outline=outline, owidth=ow * 0.8)
        g.arc((ex - r * 0.07, cy + r * 0.02, ex + r * 0.07, cy + r * 0.22),
              40, 200, with_alpha(SKIN_SH, 220), 2.5)
    # 前髪の影 (額上部)
    g.chord((cx - r * 0.88, cy - r * 0.62, cx + r * 0.88, cy + r * 0.24),
            180, 360, fill=with_alpha((190, 130, 105), 60))
    g.flush()
    return {"chin": chin, "left": left, "right": right}


def lock(g, a, c1, tip, c2, b, fill, outline=None, ow=0):
    """房1本: a→(c1)→tip→(c2)→b の閉曲線."""
    pts = qbez(a, c1, tip, 12) + qbez(tip, c2, b, 12)[1:]
    g.poly(pts, fill=fill, outline=outline, owidth=ow)


def zigzag(pts, dip=18.0, n=8):
    """点列を下向きの丸いジグザグ曲線でつなぐ (前髪の房並べ)."""
    out = [pts[0]]
    for p, q in zip(pts, pts[1:]):
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + dip
        out += qbez(p, (mx, my), q, n)[1:]
    return out


def hair_shine(hair_layer, color, box, width_band, start=200, end=340):
    """髪レイヤーにクリップされた光帯 (アニメハイライト)."""
    shine = sublayer(hair_layer)
    sg = shine.g()
    sg.arc(box, start, end, color, width_band)
    sg.flush()
    from .canvas import paste_masked
    paste_masked(hair_layer.img, shine.img, hair_layer.img.split()[3])


def rotate_pts(pts, deg, around=(0, 0)):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for (x, y) in pts:
        dx, dy = x - around[0], y - around[1]
        out.append((around[0] + dx * ca - dy * sa, around[1] + dx * sa + dy * ca))
    return out


def rrect_pts(x0, y0, x1, y1, r, n=6):
    """角丸矩形のポリゴン点列 (回転用)."""
    pts = []
    corners = [  # (中心x, 中心y, 開始角)
        (x0 + r, y0 + r, 180.0),   # 左上
        (x1 - r, y0 + r, 270.0),   # 右上
        (x1 - r, y1 - r, 0.0),     # 右下
        (x0 + r, y1 - r, 90.0),    # 左下
    ]
    for (ccx, ccy, a0) in corners:
        for i in range(n + 1):
            a = math.radians(a0 + 90.0 * i / n)
            pts.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    return pts


def arm_limb(g, pts, width, skin=SKIN, outline=INK, ow=2.6, round_end=True):
    """腕/脚の太い limb (ライン+輪郭)."""
    g.line(pts, outline, width + ow * 2)
    g.line(pts, skin, width)
    if round_end:
        g.circle(pts[-1][0], pts[-1][1], (width + ow * 2) / 2, fill=outline)
        g.circle(pts[-1][0], pts[-1][1], width / 2, fill=skin)


# ---------------------------------------------------------------- 立ち絵本体

CW, CH = 900, 1400


def _back_hair_sensei(cv):
    """先生の後髪 (腰までのロング)."""
    lay = sublayer(cv)
    g = lay.g()
    HAIR = P.HAIR_NAVY
    HD = shade(HAIR, 0.78)
    pts = (qbez((258, 420), (232, 240), (300, 158), 14)
           + qbez((300, 158), (380, 118), (450, 118), 10)
           + qbez((450, 118), (520, 118), (600, 158), 10)
           + qbez((600, 158), (668, 240), (642, 420), 14)
           + qbez((642, 420), (664, 620), (620, 830), 14)
           + qbez((620, 830), (600, 900), (568, 906), 8))
    # 下端の房スクALLOP
    bottom = []
    for k in range(4):
        x0 = 568 - k * 88
        bottom += qbez((x0, 906), (x0 - 30, 948), (x0 - 52, 918), 6)
        bottom += qbez((x0 - 52, 918), (x0 - 66, 896), (x0 - 88, 918), 6)
    pts += bottom
    pts += qbez((252, 918), (236, 640), (258, 420), 14)
    g.poly(pts, fill=HAIR, outline=INK, owidth=3)
    # 内側の濃い房
    g.poly(qbez((300, 200), (270, 480), (296, 760), 12)
           + qbez((296, 760), (302, 830), (330, 846), 6)
           + qbez((330, 846), (360, 700), (336, 210), 12), fill=HD)
    g.poly(qbez((600, 200), (630, 480), (604, 760), 12)
           + qbez((604, 760), (598, 830), (570, 846), 6)
           + qbez((570, 846), (540, 700), (564, 210), 12), fill=HD)
    hair_shine(lay, with_alpha((108, 124, 168), 150), (300, 100, 640, 330), 26)
    lay.flush()
    cv.img.alpha_composite(lay.img)


def build_sensei(ss=2):
    """ヒスト先生 — 藍スーツ+山吹ネクタイ+眼鏡+教科書の知的女性講師."""
    cv = Canvas(CW, CH, ss=ss)
    g = cv.g()
    HAIR = P.HAIR_NAVY
    HD = shade(HAIR, 0.78)
    OW = 3.0

    # ---------- 背後のロングヘア ----------
    _back_hair_sensei(cv)

    # ---------- 脚・靴 ----------
    for lx in (412, 488):
        arm_limb(g, [(lx - 2, 1000), (lx, 1140), (lx - 2, 1288)], 40,
                skin=P.SKIN, ow=2.6)
        # ニーハイ風の暗いタイツ? → 素足スキン+シェード
        g.line([(lx - 14, 1060), (lx - 10, 1130)], with_alpha(SKIN_SH, 130), 6)
    for lx, flip in ((412, 1), (488, -1)):
        shoe = rrect_pts(lx - 34, 1286, lx + 36, 1336, 14)
        if flip == 1:
            shoe = rotate_pts(shoe, 0, (lx, 1310))
        g.poly(shoe, fill=(38, 44, 66), outline=INK, owidth=2.4)
        g.line([(lx - 30, 1300), (lx + 30, 1300)], (78, 88, 118), 3)

    # ---------- スカート ----------
    skirt = (qbez((352, 872), (330, 960), (356, 1022), 10)
             + qbez((356, 1022), (450, 1040), (544, 1022), 8)
             + qbez((544, 1022), (570, 960), (548, 872), 10))
    g.poly(skirt, fill=P.INDIGO_D, outline=INK, owidth=3)
    g.line([(404, 886), (398, 1018)], shade(P.INDIGO_D, 0.8), 4)
    g.line([(496, 886), (502, 1018)], shade(P.INDIGO_D, 0.8), 4)
    g.line([(352, 884), (548, 884)], shade(P.INDIGO_D, 0.9), 8)

    # ---------- 胴体 (ジャケット) ----------
    torso = (qbez((318, 560), (306, 680), (332, 880), 14)
             + qbez((332, 880), (450, 908), (568, 880), 8)
             + qbez((568, 880), (594, 680), (582, 560), 14)
             + qbez((582, 560), (520, 512), (450, 512), 10)
             + qbez((450, 512), (380, 512), (318, 560), 10))
    g.poly(torso, fill=P.INDIGO, outline=INK, owidth=3)
    # 袖の影・脇の影
    g.poly(qbez((556, 560), (576, 700), (556, 876), 12)
           + qbez((556, 876), (540, 872), (540, 560), 8), fill=with_alpha((24, 40, 78), 110))
    # シャチョー (襟) とシャツ
    g.poly([(418, 516), (450, 596), (482, 516), (450, 508)], fill=P.UI_WHITE,
           outline=(120, 126, 140), owidth=2)
    # ラペル
    g.poly([(418, 516), (396, 640), (428, 664), (446, 600)], fill=P.INDIGO_L,
           outline=INK, owidth=2.2)
    g.poly([(482, 516), (504, 640), (472, 664), (454, 600)], fill=P.INDIGO_L,
           outline=INK, owidth=2.2)
    # ネクタイ (山吹)
    g.poly([(438, 522), (462, 522), (456, 548), (444, 548)], fill=P.YAMABUKI_D,
           outline=INK, owidth=1.8)
    g.poly(qbez((442, 548), (434, 640), (438, 760), 10)
           + [(452, 776), (462, 760)]
           + qbez((462, 760), (466, 640), (458, 548), 10),
           fill=P.YAMABUKI, outline=INK, owidth=2)
    g.poly([(438, 760), (452, 776), (466, 760), (458, 820), (446, 820)],
           fill=P.YAMABUKI, outline=INK, owidth=2)
    g.line([(444, 600), (456, 640)], with_alpha((255, 240, 200), 120), 5)
    g.line([(444, 680), (456, 716)], with_alpha((255, 240, 200), 120), 5)
    # ボタン
    g.circle(404, 700, 5, fill=P.UI_WHITE)

    # ---------- 教科書を持つ左腕 (画面左・手前) ----------
    arm_limb(g, [(338, 580), (300, 700), (318, 780)], 42, ow=2.6)
    # 教科書
    bx, by = 392, 780
    book = rrect_pts(bx - 86, by - 116, bx + 86, by + 116, 10)
    book = rotate_pts(book, -8, (bx, by))
    g.poly(book, fill=(36, 54, 100), outline=INK, owidth=2.6)
    lab = rotate_pts(rrect_pts(bx - 62, by - 40, bx + 62, by + 46, 6), -8, (bx, by))
    g.poly(lab, fill=P.UI_WHITE)
    l1 = rotate_pts([(bx - 40, by - 14), (bx + 40, by - 14)], -8, (bx, by))
    l2 = rotate_pts([(bx - 40, by + 6), (bx + 40, by + 6)], -8, (bx, by))
    l3 = rotate_pts([(bx - 40, by + 26), (bx + 12, by + 26)], -8, (bx, by))
    g.line(l1, P.INDIGO, 7)
    g.line(l2, shade(P.INDIGO, 0.75), 5)
    g.line(l3, P.SHU, 5)
    g.poly(rotate_pts([(bx - 86, by - 116), (bx - 74, by - 116), (bx - 74, by + 116),
                       (bx - 86, by + 116)], -8, (bx, by)), fill=(226, 224, 216))
    # 本を支える手
    g.circle(330, 792, 24, fill=SKIN, outline=INK, owidth=2.4)

    # ---------- 右腕 (垂らす) ----------
    arm_limb(g, [(566, 584), (600, 720), (592, 850)], 42, ow=2.6)
    g.circle(590, 884, 24, fill=SKIN, outline=INK, owidth=2.4)

    # ---------- 顔 ----------
    cv.flush()
    face_and_neck(cv, 450, 330, 148)
    anime_eye(cv, 384, 348, 90, 60, iris=(62, 108, 158), flip=1, lash_w=6.5,
              calm=True)
    anime_eye(cv, 516, 348, 90, 60, iris=(62, 108, 158), flip=-1, lash_w=6.5,
              calm=True)
    bg_ = cv.g()
    brow(bg_, 384, 296, 72, angle=-4, color=(56, 44, 58), flip=1)
    brow(bg_, 516, 296, 72, angle=-4, color=(56, 44, 58), flip=-1)
    nose(bg_, 452, 398)
    mouth(bg_, 452, 438, 46, "smile")
    blush(bg_, 352, 402, 26, alpha=64)
    blush(bg_, 548, 402, 26, alpha=64)

    # ---------- 前髪 ----------
    lay = sublayer(cv)
    fg = lay.g()
    # ベースの前髪: 頭頂アーク → 下端はジグザグの房並べ (非交差)
    A, B = (262, 344), (638, 332)
    top = (qbez(A, (240, 190), (320, 148), 12)
           + qbez((320, 148), (390, 116), (450, 116), 8)
           + qbez((450, 116), (510, 116), (580, 148), 8)
           + qbez((580, 148), (660, 190), B, 12))
    seq = [B, (596, 336), (556, 296), (498, 342), (462, 292),
           (402, 344), (366, 296), (314, 340), (290, 300), A]
    bottom = zigzag(seq, dip=13)[1:]
    fg.poly(top + bottom, fill=HAIR, outline=INK, owidth=3)
    # 房のaccent (額の中央寄り)
    lock(fg, (356, 210), (362, 264), (396, 316), (404, 268), (430, 226),
         HD, INK, 2)
    lock(fg, (544, 210), (538, 264), (504, 316), (496, 268), (470, 226),
         HD, INK, 2)
    hair_shine(lay, with_alpha((108, 124, 168), 160), (296, 96, 620, 300), 22)
    lay.flush()
    cv.flush()
    cv.img.alpha_composite(lay.img)
    # 側面の長い房 (耳の前)
    sg = cv.g()
    lock(sg, (266, 320), (250, 480), (266, 660), (286, 560), (300, 330),
         HAIR, INK, 2.6)
    lock(sg, (634, 320), (650, 480), (634, 660), (614, 560), (600, 330),
         HAIR, INK, 2.6)

    # ---------- 眼鏡 ----------
    gg = cv.g()
    FR = (30, 44, 86)
    for ex in (388, 512):
        frame = rrect_pts(ex - 58, 316, ex + 58, 380, 20)
        gg.poly(frame, fill=with_alpha((240, 248, 255), 14), outline=FR, owidth=5)
        # レンズの光 (細く控えめ)
        gg.line([(ex - 42, 354), (ex - 22, 332)], with_alpha((255, 255, 255), 85), 4)
        gg.line([(ex - 30, 362), (ex - 16, 346)], with_alpha((255, 255, 255), 55), 2.5)
    gg.line([(446, 334), (454, 334)], FR, 5)
    gg.line([(330, 336), (300, 344)], FR, 5)
    gg.line([(570, 336), (600, 344)], FR, 5)

    return cv


def build_manabu(ss=2):
    """マナブ — 白T+朱ベスト+リュックの元気少年."""
    cv = Canvas(CW, CH, ss=ss)
    g = cv.g()
    HAIR = P.HAIR_BROWN
    HD = shade(HAIR, 0.76)
    OW = 3.0

    # ---------- リュック (背中側) ----------
    g.rrect((272, 560, 352, 852), 30, fill=P.INDIGO, outline=INK, owidth=3)
    g.rrect((548, 560, 628, 852), 30, fill=P.INDIGO, outline=INK, owidth=3)
    g.rrect((292, 600, 332, 700), 12, fill=P.INDIGO_L)
    g.rrect((568, 600, 608, 700), 12, fill=P.INDIGO_L)

    # ---------- 脚・靴 ----------
    for lx in (414, 486):
        arm_limb(g, [(lx - 2, 960), (lx, 1120), (lx - 2, 1288)], 46, ow=2.6)
        g.line([(lx - 16, 1120), (lx - 9, 1200)], with_alpha(SKIN_SH, 110), 6)
    for lx in (414, 486):
        shoe = rrect_pts(lx - 36, 1284, lx + 40, 1336, 16)
        g.poly(shoe, fill=P.UI_WHITE, outline=INK, owidth=2.6)
        g.line([(lx - 30, 1306), (lx + 34, 1306)], P.SHU, 6)
        g.line([(lx - 32, 1322), (lx + 36, 1322)], (150, 154, 162), 4)

    # ---------- ショーツ ----------
    shorts = (qbez((346, 838), (330, 900), (346, 972), 10)
              + qbez((346, 972), (450, 992), (554, 972), 8)
              + qbez((554, 972), (570, 900), (554, 838), 10))
    g.poly(shorts, fill=P.INDIGO_D, outline=INK, owidth=3)
    g.poly([(346, 906), (450, 926), (554, 906), (554, 972), (450, 988),
            (346, 972)], fill=with_alpha((26, 44, 86), 90))
    g.line([(342, 848), (558, 848)], shade(P.INDIGO_D, 0.85), 9)

    # ---------- Tシャツ胴体 ----------
    torso = (qbez((330, 566), (318, 700), (340, 848), 14)
             + qbez((340, 848), (450, 872), (560, 848), 8)
             + qbez((560, 848), (582, 700), (570, 566), 14)
             + qbez((570, 566), (514, 520), (450, 520), 10)
             + qbez((450, 520), (386, 520), (330, 566), 10))
    g.poly(torso, fill=P.UI_WHITE, outline=INK, owidth=3)
    g.poly(qbez((524, 570), (548, 710), (528, 844), 12)
           + qbez((528, 844), (512, 840), (512, 574), 8),
           fill=with_alpha((196, 190, 176), 110))

    # ---------- 朱ベスト (前開き) ----------
    for (x0, dir) in ((330, 1), (570, -1)):
        vest = (qbez((x0, 560), (x0 + dir * 26, 548), (x0 + dir * 66, 560), 8)
                + qbez((x0 + dir * 66, 560), (x0 + dir * 96, 700),
                       (x0 + dir * 78, 852), 12)
                + qbez((x0 + dir * 78, 852), (x0 + dir * 40, 862),
                       (x0 + dir * 14, 850), 8)
                + qbez((x0 + dir * 14, 850), (x0 + dir * 6, 700), (x0, 560), 10))
        g.poly(vest, fill=P.SHU, outline=INK, owidth=2.6)
        g.line([(x0 + dir * 14, 852), (x0 + dir * 14, 566)], P.SHU_D, 6)
        g.line([(x0 + dir * 66, 560), (x0 + dir * 78, 850)], P.YAMABUKI, 7)
    g.rrect((396, 540, 504, 572), 12, fill=P.SHU, outline=INK, owidth=2.2)

    # ---------- リュック肩紐 ----------
    g.line([(348, 570), (392, 700), (398, 830)], P.INDIGO, 16)
    g.line([(552, 570), (508, 700), (502, 830)], P.INDIGO, 16)
    g.line([(348, 570), (392, 700), (398, 830)], P.INDIGO_D, 4)
    g.circle(398, 838, 9, fill=P.YAMABUKI, outline=INK, owidth=2)
    g.circle(502, 838, 9, fill=P.YAMABUKI, outline=INK, owidth=2)

    # ---------- 腕 (左は上げて拳グー) ----------
    arm_limb(g, [(352, 596), (318, 700), (330, 780)], 40, ow=2.6)   # 右側の腕
    g.circle(334, 800, 24, fill=SKIN, outline=INK, owidth=2.4)
    # 上げた左腕
    arm_limb(g, [(340, 590), (282, 620), (268, 540)], 40, ow=2.6)
    fist = rrect_pts(244, 462, 300, 520, 16)
    g.poly(fist, fill=SKIN, outline=INK, owidth=2.6)
    g.arc((246, 468, 296, 512), 90, 270, with_alpha(SKIN_SH, 200), 4)

    arm_limb(g, [(548, 596), (592, 700), (586, 790)], 40, ow=2.6)
    g.circle(584, 820, 24, fill=SKIN, outline=INK, owidth=2.4)

    # ---------- 顔 ----------
    cv.flush()
    face_and_neck(cv, 450, 326, 146)
    anime_eye(cv, 384, 348, 96, 68, iris=(196, 126, 52), flip=1, lash_w=7)
    anime_eye(cv, 516, 348, 96, 68, iris=(196, 126, 52), flip=-1, lash_w=7)
    bg_ = cv.g()
    brow(bg_, 382, 296, 70, angle=-8, color=(64, 44, 36), flip=1)
    brow(bg_, 518, 296, 70, angle=-8, color=(64, 44, 36), flip=-1)
    nose(bg_, 452, 396)
    mouth(bg_, 454, 440, 88, "grin")
    blush(bg_, 348, 404, 30, alpha=88)
    blush(bg_, 552, 404, 30, alpha=88)

    # ---------- 髪 (もじゃもじゃスパイク) ----------
    lay = sublayer(cv)
    fg = lay.g()
    # 頭頂キャップ (生え際まで。顔は覆わない。外周だけ線を引く)
    cap_top = (qbez((292, 356), (268, 200), (330, 150), 12)
               + qbez((330, 150), (390, 116), (450, 116), 8)
               + qbez((450, 116), (510, 116), (570, 150), 8)
               + qbez((570, 150), (632, 200), (608, 356), 12))
    cap = cap_top + (qbez((608, 356), (520, 302), (450, 298), 10)
                     + qbez((450, 298), (380, 302), (292, 356), 10))
    fg.poly(cap, fill=HAIR)
    fg.line(cap_top, INK, 3)
    # スパイク房 (上)
    spikes = [((302, 244), (272, 180), (318, 190)),
              ((338, 190), (338, 110), (384, 150)),
              ((398, 158), (418, 92), (452, 140)),
              ((462, 140), (496, 96), (520, 152)),
              ((530, 152), (572, 112), (568, 190)),
              ((584, 190), (622, 182), (598, 242))]
    for (a, tip, b) in spikes:
        lock(fg, a, ((a[0] + tip[0]) / 2 - 6, (a[1] + tip[1]) / 2),
             tip, ((tip[0] + b[0]) / 2 + 6, (tip[1] + b[1]) / 2), b,
             HAIR, INK, 2.6)
    # 前髪の房 (まつ毛のすぐ上まで)
    fringes = [((306, 330), (318, 330), (338, 306)),
               ((346, 302), (370, 324), (394, 300)),
               ((402, 296), (430, 322), (458, 298)),
               ((466, 298), (494, 324), (518, 300)),
               ((526, 302), (548, 328), (566, 312))]
    for (a, tip, b) in fringes:
        lock(fg, a, ((a[0] + tip[0]) / 2 - 10, (a[1] + tip[1]) / 2),
             tip, ((tip[0] + b[0]) / 2 + 10, (tip[1] + b[1]) / 2), b,
             HAIR, INK, 2.4)
    hair_shine(lay, with_alpha((186, 146, 106), 150), (300, 100, 600, 260), 20)
    lay.flush()
    cv.flush()
    cv.img.alpha_composite(lay.img)
    # 側面の房 (耳の前)
    sg = cv.g()
    lock(sg, (286, 344), (270, 416), (282, 466), (298, 416), (308, 350), HAIR, INK, 2.4)
    lock(sg, (614, 344), (630, 416), (618, 466), (602, 416), (592, 350), HAIR, INK, 2.4)

    return cv


def build_nyobo(ss=2):
    """十二単の女房 — 多重襲の袿と裳、桧扇を持つ平安貴族の侍女."""
    cv = Canvas(CW, CH, ss=ss)
    g = cv.g()
    HAIR = (32, 30, 38)
    HD = shade(HAIR, 0.78)
    OW = 3.0
    LAYERS = [(176, 132, 196), (216, 118, 132), (240, 170, 180), (196, 220, 180),
              (244, 240, 232)]  # 表→内

    # ---------- 背後の黒髪 (腰まで) ----------
    lay = sublayer(cv)
    lg = lay.g()
    pts = (qbez((262, 430), (238, 250), (300, 160), 14)
           + qbez((300, 160), (370, 120), (450, 120), 10)
           + qbez((450, 120), (530, 120), (600, 160), 10)
           + qbez((600, 160), (662, 250), (638, 430), 14)
           + qbez((638, 430), (660, 640), (614, 860), 14)
           + qbez((614, 860), (596, 916), (566, 920), 8))
    bottom = []
    for k in range(4):
        x0 = 566 - k * 84
        bottom += qbez((x0, 920), (x0 - 28, 958), (x0 - 48, 930), 6)
        bottom += qbez((x0 - 48, 930), (x0 - 62, 908), (x0 - 84, 930), 6)
    pts += bottom + qbez((248, 930), (232, 640), (262, 430), 14)
    lg.poly(pts, fill=HAIR, outline=INK, owidth=3)
    hair_shine(lay, with_alpha((94, 88, 108), 120), (300, 110, 620, 330), 20)
    lay.flush()
    cv.img.alpha_composite(lay.img)

    # ---------- 裳 (裾が広がる袴) ----------
    skirt = (qbez((356, 866), (322, 1000), (300, 1160), 12)
             + qbez((300, 1160), (292, 1230), (306, 1272), 8)
             + qbez((306, 1272), (450, 1296), (594, 1272), 8)
             + qbez((594, 1272), (608, 1230), (600, 1160), 8)
             + qbez((600, 1160), (578, 1000), (544, 866), 12))
    g.poly(skirt, fill=(88, 72, 122), outline=INK, owidth=3)
    # 裳の褶 (縦の fold)
    for dx in (-110, -56, 0, 56, 110):
        g.line(qbez((450 + dx * 0.42, 880), (450 + dx * 0.9, 1060),
                    (450 + dx, 1258), 12), shade((88, 72, 122), 0.78), 8)
    # 裾の段と雲文
    g.line(qbez((306, 1210), (450, 1240), (594, 1210), 12), (214, 196, 150), 16)
    rnd = random.Random(5)
    for _ in range(9):
        px = rnd.uniform(320, 580)
        py = rnd.uniform(1200, 1252)
        g.arc((px - 16, py - 8, px + 16, py + 8), 180, 360, (164, 148, 118), 4)

    # ---------- 表着 (胴体+広袖) ----------
    robe = (qbez((352, 568), (338, 700), (352, 868), 14)
            + qbez((352, 868), (450, 896), (548, 868), 8)
            + qbez((548, 868), (562, 700), (548, 568), 14)
            + qbez((548, 568), (500, 524), (450, 524), 10)
            + qbez((450, 524), (400, 524), (352, 568), 10))
    g.poly(robe, fill=(186, 74, 94), outline=INK, owidth=3)
    # 左右の広袖 (袂)
    for sx in (-1, 1):
        mx = 450 + sx * 160
        sleeve = (qbez((mx - 52 * sx, 616), (mx - 96 * sx, 640), (mx - 100 * sx, 760), 10)
                  + qbez((mx - 100 * sx, 760), (mx - 96 * sx, 850), (mx - 40 * sx, 862), 10)
                  + qbez((mx - 40 * sx, 862), (mx - 8 * sx, 850), (mx - 10 * sx, 760), 8)
                  + qbez((mx - 10 * sx, 760), (mx - 8 * sx, 650), (mx - 52 * sx, 616), 8))
        g.poly(sleeve, fill=shade((186, 74, 94), 0.94), outline=INK, owidth=2.6)
        # 袂口の重ね襲
        for li, c in enumerate(LAYERS):
            g.line([(mx - 84 * sx + 8 * sx, 800 + li * 13),
                    (mx - 24 * sx, 806 + li * 13)], c, 9)
    # 胴の陰
    g.poly(qbez((516, 570), (534, 700), (514, 862), 12)
           + qbez((514, 862), (500, 858), (500, 574), 8),
           fill=with_alpha((140, 52, 70), 110))

    # ---------- 重ね襲の襟 (胸の多重V) ----------
    for li, c in enumerate(LAYERS):
        yv = 592 + li * 13
        g.line([(414 - li * 3, 540), (450, yv), (486 + li * 3, 540)], c, 15)
    g.line([(414 - 12, 540), (450, 632), (486 + 12, 540)], INK, 2.6)

    # ---------- 顔 ----------
    cv.flush()
    face_and_neck(cv, 450, 330, 146)
    anime_eye(cv, 388, 350, 78, 50, iris=(96, 66, 50), flip=1, lash_w=5.5, calm=True)
    anime_eye(cv, 512, 350, 78, 50, iris=(96, 66, 50), flip=-1, lash_w=5.5, calm=True)
    bg_ = cv.g()
    brow(bg_, 388, 300, 62, angle=-2, color=(60, 48, 54), flip=1, width=5)
    brow(bg_, 512, 300, 62, angle=-2, color=(60, 48, 54), flip=-1, width=5)
    nose(bg_, 452, 396)
    mouth(bg_, 452, 434, 34, "smile")
    blush(bg_, 356, 402, 24, alpha=60)
    blush(bg_, 544, 402, 24, alpha=60)

    # ---------- 前髪 (丸眉・姫カット) ----------
    lay = sublayer(cv)
    fg = lay.g()
    A, B = (272, 320), (628, 318)
    top = (qbez(A, (248, 190), (320, 150), 12)
           + qbez((320, 150), (390, 118), (450, 118), 8)
           + qbez((450, 118), (510, 118), (580, 150), 8)
           + qbez((580, 150), (652, 190), B, 12))
    seq = [B, (576, 336), (536, 292), (480, 340), (432, 290), (380, 340),
           (330, 296), (296, 324), A]
    fg.poly(top + zigzag(seq, dip=12)[1:], fill=HAIR, outline=INK, owidth=3)
    hair_shine(lay, with_alpha((94, 88, 108), 130), (300, 100, 600, 280), 18)
    lay.flush()
    cv.flush()
    cv.img.alpha_composite(lay.img)
    sg = cv.g()
    lock(sg, (276, 330), (258, 500), (272, 700), (292, 560), (306, 336), HAIR, INK, 2.6)
    lock(sg, (624, 330), (642, 500), (628, 700), (608, 560), (594, 336), HAIR, INK, 2.6)
    # 髪飾り (小さな金の簪)
    sg.line([(560, 214), (596, 196)], (216, 178, 110), 6)
    sg.circle(598, 194, 7, fill=(230, 196, 130), outline=(160, 128, 82), owidth=2)

    # ---------- 桧扇 (右手) ----------
    fan_cx, fan_cy = 620, 812
    for k in range(7):
        t = (k - 3) / 3.0
        ang = math.radians(-90 + t * 52)
        ex = fan_cx + math.cos(ang) * 128
        ey = fan_cy + math.sin(ang) * 128
        sg.line([(fan_cx, fan_cy), (ex, ey)], shade((216, 186, 140), 0.8), 10)
        sg.line([(fan_cx, fan_cy), (ex, ey)], (222, 192, 146), 6.5)
        if k in (2, 4):
            sg.circle((fan_cx + ex) / 2 + t * 14, (fan_cy + ey) / 2 - 6, 4,
                      fill=(86, 108, 150))
            sg.circle((fan_cx + ex) / 2 - t * 12, (fan_cy + ey) / 2 + 4, 3,
                      fill=(196, 96, 96))
    sg.arc((fan_cx - 92, fan_cy - 148, fan_cx + 92, fan_cy + 40), 235, 305,
           shade((216, 186, 140), 0.7), 5)
    sg.circle(fan_cx, fan_cy, 9, fill=P.SHU, outline=shade(P.SHU, 0.72), owidth=2)

    return cv

#!/usr/bin/env python3
"""サムネイル自動生成 (1280x720) — アニメ日本史ラボ

Usage:
  uv run --with pillow --with numpy python tools/thumbnail.py \
    --episode ep01 \
    --background assets/ep01/scenes/bg_jomon_village.png \
    --character assets/ep01/overlay/char_manabu.png \
    --headline "縄文×弥生×古墳" \
    --sub "日本史のはじまり!" \
    --badge "受験必須" \
    --out youtube/thumbnails/ep01_thumb.png

背景やキャラが無い場合は自動でフォールバック背景を描画する。
"""
from __future__ import annotations

import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1280, 720
SS = 2  # supersampling

# パレット (docs/03_STYLE_GUIDE.md)
BLUE = (43, 74, 139)
RED = (232, 84, 63)
YELLOW = (245, 185, 66)
GREEN = (90, 164, 105)
DARK = (38, 40, 46)
CREAM = (255, 253, 247)

FONT_DIR = "/Library/Fonts"


def font(size: int, weight: str = "Black") -> ImageFont.FreeTypeFont:
    path = f"{FONT_DIR}/NotoSansJP-{weight}.otf"
    if not os.path.exists(path):
        path = f"{FONT_DIR}/NotoSansJP-Bold.otf"
    return ImageFont.truetype(path, size)


def fallback_background() -> Image.Image:
    """アセットが無い場合のPop系グラデ背景。"""
    img = Image.new("RGB", (W * SS, H * SS))
    top, bottom = (142, 201, 232), (43, 74, 139)
    px = img.load()
    for y in range(H * SS):
        t = y / (H * SS - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        for x in range(W * SS):
            px[x, y] = (r, g, b)
    d = ImageDraw.Draw(img)
    # 斜めの朱ワイプ帯 (動きのある構図)
    d.polygon([(0, H * SS), (W * SS * 0.45, H * SS), (W * SS * 0.75, 0), (W * SS * 0.35, 0)],
              fill=(232, 84, 63))
    d.polygon([(W * SS * 0.45, H * SS), (W * SS * 0.5, H * SS), (W * SS * 0.8, 0), (W * SS * 0.75, 0)],
              fill=(245, 185, 66))
    return img


def load_cover(path: str | None) -> Image.Image:
    if path and os.path.exists(path):
        bg = Image.open(path).convert("RGB")
        # カバー裁ち抜き (アスペクト維持で中央クロップ)
        scale = max(W * SS / bg.width, H * SS / bg.height)
        bg = bg.resize((int(bg.width * scale) + 1, int(bg.height * scale) + 1), Image.LANCZOS)
        x = (bg.width - W * SS) // 2
        y = (bg.height - H * SS) // 2
        return bg.crop((x, y, x + W * SS, y + H * SS))
    return fallback_background()


def text_with_stroke(d: ImageDraw.ImageDraw, xy, text, f, fill, stroke, swidth, anchor=None):
    d.text(xy, text, font=f, fill=fill, stroke_width=swidth, stroke_fill=stroke, anchor=anchor)


def rounded(d: ImageDraw.ImageDraw, box, radius, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def build(out: str, background: str | None, character: str | None, headline: str,
          sub: str | None, badge: str | None, channel_label: str = "アニメ日本史ラボ"):
    img = load_cover(background)

    # 下部に暗いグラデを敷いて文字可読性を上げる
    shade = Image.new("L", (1, H * SS), 0)
    for y in range(H * SS):
        t = max(0.0, (y / (H * SS - 1) - 0.45) / 0.55)
        shade.putpixel((0, y), int(160 * t))
    shade = shade.resize((W * SS, H * SS))
    black = Image.new("RGB", (W * SS, H * SS), (0, 0, 0))
    img = Image.composite(black, img, shade)

    img = img.convert("RGBA")
    # キャラ立ち絵 (右側)
    if character and os.path.exists(character):
        ch = Image.open(character).convert("RGBA")
        target_h = int(H * SS * 0.92)
        scale = target_h / ch.height
        ch = ch.resize((int(ch.width * scale), target_h), Image.LANCZOS)
        img.alpha_composite(ch, (W * SS - ch.width - int(30 * SS), H * SS - ch.height + int(10 * SS)))

    d = ImageDraw.Draw(img)

    # チャンネルラベル (左上)
    f_ch = font(int(30 * SS), "Bold")
    tw = d.textlength(channel_label, font=f_ch)
    rounded(d, [int(36 * SS), int(30 * SS), int(36 * SS) + tw + int(28 * SS), int(30 * SS) + int(48 * SS)],
            radius=int(24 * SS), fill=CREAM + (235,))
    d.text((int(36 * SS) + int(14 * SS), int(30 * SS) + int(24 * SS)), channel_label,
           font=f_ch, fill=BLUE, anchor="lm")

    # 大見出し (左下寄り、朱フチ白文字)
    lines = headline.split("\\n") if "\\n" in headline else [headline]
    f_head = font(int(96 * SS), "Black")
    y = int(H * SS * 0.52)
    for i, line in enumerate(lines):
        text_with_stroke(d, (int(40 * SS), y + i * int(110 * SS)), line, f_head,
                         CREAM, (193, 48, 34), max(3, int(7 * SS)), anchor="lm")

    # サブコピー
    if sub:
        f_sub = font(int(46 * SS), "Bold")
        text_with_stroke(d, (int(44 * SS), int(H * SS * 0.52) + len(lines) * int(110 * SS) + int(10 * SS)),
                         sub, f_sub, YELLOW, DARK, max(2, int(5 * SS)), anchor="lm")

    # 受験バッジ (右上)
    if badge:
        f_b = font(int(52 * SS), "Black")
        bw = d.textlength(badge, font=f_b)
        box = [W * SS - bw - int(96 * SS), int(34 * SS), W * SS - int(36 * SS), int(110 * SS)]
        rounded(d, box, radius=int(18 * SS), fill=RED + (255,))
        d.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), badge, font=f_b, fill=CREAM, anchor="mm")
        # ハイライトの鋲
        d.ellipse([box[0] - int(10 * SS), box[3] - int(6 * SS), box[0] + int(6 * SS), box[3] + int(10 * SS)],
                  fill=YELLOW + (255,))

    out_img = img.convert("RGB").resize((W, H), Image.LANCZOS)
    out_img = out_img.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=3))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    out_img.save(out, "PNG")
    print(f"saved: {out} ({W}x{H})")


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--episode", default="epXX")
    p.add_argument("--background", default=None)
    p.add_argument("--character", default=None)
    p.add_argument("--headline", required=True)
    p.add_argument("--sub", default=None)
    p.add_argument("--badge", default="受験必須")
    p.add_argument("--out", default=None)
    a = p.parse_args(argv)
    out = a.out or f"youtube/thumbnails/{a.episode}_thumb.png"
    build(out, a.background, a.character, a.headline, a.sub, a.badge)


if __name__ == "__main__":
    main(sys.argv[1:])

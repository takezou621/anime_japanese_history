#!/usr/bin/env python3
"""Muse 納品アート (characters_v2) から制作スプライトを生成 — アニメ日本史ラボ

納品ソース (assets/characters_v2/source/*.webp) を:
  1. 白背景の削除 (端からの flood-fill — 白T/白シャツなど内部の白は保持)
  2. コンテンツ bbox 切り抜き
  3. 900x1400 キャンバスに縦フィット (下端=足元)
して char_sensei.png / char_manabu.png を生成する。

Usage:
  uv run --with pillow python tools/sprites_v2/make_sprites.py --out assets/ep01/overlay
"""
from __future__ import annotations

import argparse
import sys
from collections import deque
from pathlib import Path

from PIL import Image
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCES = REPO_ROOT / "assets" / "characters_v2" / "source"
W, H = 900, 1400

SPRITES = {
    "char_sensei": SOURCES / "media-generation-sensei-fullbody-0-21a41610-b4df-441e-8df5-1bd81fbb8fd4.webp",
    "char_manabu": SOURCES / "media-generation-manabu-fullbody-0-8a4e1fa1-0fb0-46cc-84f6-0c41a09ff7ee.webp",
}


def remove_white_bg(img: Image.Image, thresh: int = 42) -> Image.Image:
    """端から flood-fill で外接白背景を透過化 (内部の白は保持)。"""
    img = img.convert("RGBA")
    arr = np.array(img)
    h, w = arr.shape[:2]
    # 明度が閾値以上かつ彩度が低い = 白背景候補
    rgb = arr[:, :, :3].astype(np.int16)
    brightness = rgb.max(axis=2)
    colorfulness = rgb.max(axis=2) - rgb.min(axis=2)
    is_whiteish = (brightness >= 255 - thresh) & (colorfulness <= 24)

    # BFS flood-fill: 端の白候補ピクセルから内部へ伝播
    visited = np.zeros((h, w), dtype=bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if is_whiteish[y, x] and not visited[y, x]:
                q.append((y, x))
                visited[y, x] = True
    for y in range(h):
        for x in (0, w - 1):
            if is_whiteish[y, x] and not visited[y, x]:
                q.append((y, x))
                visited[y, x] = True
    while q:
        y, x = q.popleft()
        for ny, nx in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)):
            if 0 <= ny < h and 0 <= nx < w and is_whiteish[ny, nx] and not visited[ny, nx]:
                visited[ny, nx] = True
                q.append((ny, nx))

    arr[visited, 3] = 0
    return Image.fromarray(arr)


def fit_canvas(img: Image.Image, top_margin_ratio: float = 0.02) -> Image.Image:
    bbox = img.getbbox()
    cropped = img.crop(bbox)
    scale = 1380 / cropped.height
    scaled = cropped.resize((int(cropped.width * scale), 1380), Image.LANCZOS)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.alpha_composite(scaled, ((W - scaled.width) // 2, 10))
    return canvas


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="assets/ep01/overlay")
    p.add_argument("--only", choices=list(SPRITES), default=None)
    a = p.parse_args(argv)
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = [a.only] if a.only else list(SPRITES)
    for cid in targets:
        src = Image.open(SPRITES[cid])
        sprite = fit_canvas(remove_white_bg(src))
        out = out_dir / f"{cid}.png"
        sprite.save(out, "PNG")
        print(f"saved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

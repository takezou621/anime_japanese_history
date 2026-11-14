#!/usr/bin/env python3
"""Open Peeps (CC0) ベースのキャラクター立ち絵コンポーザ — アニメ日本史ラボ

キャラクター素材: Open Peeps by Pablo Stanley (https://www.openpeeps.com) — CC0 1.0
パーツ出典: https://github.com/CeamKrier/react-peeps (コードMIT, 絵柄はCC0)
CC0 のため営利利用・改変・クレジットなし利用が可能だが、本プロジェクトでは
動画概要欄にクレジットを明記する (docs/01_PLAN.md §5)。

Usage:
  uv run --with pillow python tools/peeps/compose_peeps.py --out assets/ep01/overlay
  uv run --with pillow python tools/peeps/compose_peeps.py --out /tmp/preview --preview-composite

Output: char_sensei.png / char_manabu.png (900x1400, 腰上バスト立ち絵, 下端が画面下端に一致)
"""
from __future__ import annotations

import argparse
import subprocess
import sys

from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
PARTS = REPO_ROOT / "tools" / "peeps" / "parts"
INK = "#26282e"          # 線画 (STYLE_GUIDE テキスト色)
HEAD_FILL = "#fffdf7"    # 頭部/肌ベース (STYLE_GUIDE 温かい白)
W, H = 900, 1400
SS = 2                   # スーパーサンプリング

# キャラ定義 (docs/03_STYLE_GUIDE.md §1 キャラ立ち絵)
CHARACTERS = {
    "char_sensei": {
        "pose": "pose_ButtonShirt", "clothes": "#2b4a8b",   # 藍ブラウス
        "hair": "hair_Bun", "head": HEAD_FILL,
        "face": "face_Calm",
        "acc": "acc_GlassRoundThick",
    },
    "char_manabu": {
        "pose": "pose_Shirt", "clothes": "#e8543f",          # 朱シャツ
        "hair": "hair_ShortMessy", "head": HEAD_FILL,
        "face": "face_CheersNM",
        "acc": None,
    },
}


def load_part(name: str, clothes: str, head: str) -> str:
    frag = (PARTS / f"{name}.svg").read_text()
    return frag.replace("{{CLOTHES}}", clothes).replace("{{HEAD}}", head)


def build_svg(char: dict) -> str:
    pose = load_part(char["pose"], char["clothes"], char["head"])
    hair = load_part(char["hair"], char["clothes"], char["head"])
    face = load_part(char["face"], char["clothes"], char["head"])
    acc = load_part(char["acc"], char["clothes"], char["head"]) if char["acc"] else ""
    # react-peeps の合成幾何: pose→原点, head→(225,0), face→(+159,+186), accessories→(+47,+241)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 850 1200">'
        f"<g>{pose}</g>"
        '<g transform="translate(225 0)">'
        f"{hair}"
        '<g transform="translate(159 186)">' + face + "</g>"
        '<g transform="translate(47 241)">' + acc + "</g>"
        "</g></svg>"
    )


def render(out: Path, char: dict) -> None:
    svg = build_svg(char)
    work = Path("/tmp/peeps_work")
    work.mkdir(parents=True, exist_ok=True)
    svg_path = work / "peep.svg"
    raw_path = work / "peep.png"
    svg_path.write_text(svg)
    ss_w = W * SS
    ss_h = H * SS
    # ピープ原図 (850x1200) をキャンバス縦幅いっぱいにレンダリング (2x)
    result = subprocess.run(
        ["resvg", str(svg_path), str(raw_path),
         "--width", str(int(ss_w)), "--background", "transparent"],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not raw_path.exists():
        sys.exit(f"resvg failed (rc={result.returncode}): {result.stderr}")
    raw = Image.open(raw_path).convert("RGBA")
    # ポートレートcrop: 頭+肩まで (タイトな話者枠). 胴体・腕は切る
    bbox = raw.getbbox()
    if bbox:
        bx0, by0, bx1, by1 = bbox
        ch = by1 - by0
        cw = bx1 - bx0
        # 上端から内容高の 64% まで (頭+肩), 幅は内容幅の 80% を中央クロップ
        keep_h = int(ch * 0.64)
        keep_w = int(cw * 0.80)
        cx0 = bx0 + (cw - keep_w) // 2
        raw = raw.crop((cx0, by0, cx0 + keep_w, by0 + keep_h))
    # 縦合わせ: ピープ原図 850:1200 → キャンバス 900:1400 は縦長比率差が僅小のため
    # 幅基準で拡大し、下端をキャンバス下端に合わせて中央配置
    scale = ss_w / raw.width
    scaled = raw.resize((ss_w, min(int(raw.height * scale), ss_h)), Image.LANCZOS)
    canvas = Image.new("RGBA", (ss_w, ss_h), (0, 0, 0, 0))
    y = ss_h - scaled.height  # 下端一致 (バスト下端=キャンバス下端)
    canvas.alpha_composite(scaled, ((ss_w - scaled.width) // 2, y))
    canvas = canvas.resize((W, H), Image.LANCZOS)
    canvas.save(out, "PNG")
    print(f"saved: {out}")


def preview_composite(out_dir: Path) -> None:
    """背景+キャラ+字幕帯のプレビュー合成 (検収用)。"""
    bg_path = REPO_ROOT / "assets" / "ep01" / "scenes" / "bg_school_lab.png"
    if not bg_path.exists():
        print("preview: bg_school_lab.png が無いためスキップ")
        return
    bg = Image.open(bg_path).convert("RGBA").resize((1920, 1080), Image.LANCZOS)
    ch_s = Image.open(out_dir / "char_sensei.png").convert("RGBA")
    ch_m = Image.open(out_dir / "char_manabu.png").convert("RGBA")
    # editor と同一の配置ロジック: scale 0.58 / 足元(下端) y=930
    scale = 0.58
    for ch, x_center in ((ch_s, 1450), (ch_m, 470)):
        w = int(ch.width * scale)
        h = int(ch.height * scale)
        ch = ch.resize((w, h), Image.LANCZOS)
        bg.alpha_composite(ch, (x_center - w // 2, 930 - h))
    # 字幕帯 (editor 相当: 下部 140px, 角丸半透明)
    from PIL import ImageDraw
    band = Image.new("RGBA", (1920, 140), (20, 22, 26, 210))
    bg.alpha_composite(band, (0, 940))
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((410, 970, 1510, 1050), radius=16, fill=(255, 253, 247, 255))
    out = out_dir / "preview_composite.png"
    bg.convert("RGB").save(out, "PNG")
    print(f"saved: {out}")


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="assets/ep01/overlay")
    p.add_argument("--preview-composite", action="store_true")
    p.add_argument("--only", choices=list(CHARACTERS), default=None)
    a = p.parse_args(argv)
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = [a.only] if a.only else list(CHARACTERS)
    for cid in targets:
        render(out_dir / f"{cid}.png", CHARACTERS[cid])
    if a.preview_composite:
        preview_composite(out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

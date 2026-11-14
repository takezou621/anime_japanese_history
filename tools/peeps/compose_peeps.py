#!/usr/bin/env python3
"""Open Peeps (CC0) ベースのキャラクター全身立ち絵コンポーザ — アニメ日本史ラボ

キャラクター素材: Open Peeps by Pablo Stanley (https://www.openpeeps.com) — CC0 1.0
パーツ出典: https://github.com/CeamKrier/react-peeps (コードMIT, 絵柄はCC0)

合成方式 (v3 全身モード):
  1. 胴体 (スタンディングポーズ) と頭部 (髪+顔+アクセサリ) を別々にレンダリング
  2. αbbox を計測し、頭の顎下端を胴体の襟上端に OVERLAP px 重ねて配置
     (頭の水平中心 = 胴体の肩中心)
  3. 2パスレンダリングで確定配置 (計測 → 補正 → 最終)

Usage:
  uv run --with pillow python tools/peeps/compose_peeps.py --out assets/ep01/overlay
  uv run --with pillow python tools/peeps/compose_peeps.py --mode bust --out /tmp/bust_test
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
PARTS = REPO_ROOT / "tools" / "peeps" / "parts"
INK = "#26282e"          # 線画 (STYLE_GUIDE テキスト色)
HEAD_FILL = "#fffdf7"    # 頭部/肌ベース (STYLE_GUIDE 温かい白)
W, H = 900, 1400
SS = 2                   # スーパーサンプリング
OVERLAP = 40             # 頭の顎を胴体の襟に重ねるpx
HEAD_SCALE = 1.1         # 頭部拡大 (ポーズの胴体が大きめのため)

CHARACTERS = {
    "char_sensei": {
        "head_scale": HEAD_SCALE,
        "standing_pose": "ShirtPantsWB",   # 藍シャツ+パンツ 全身
        "bust_pose": "pose_ButtonShirt",
        "clothes": "#2b4a8b",
        "hair": "hair_Bun", "head": HEAD_FILL,
        "face": "face_Calm",
        "acc": "acc_GlassRoundThick",
    },
    "char_manabu": {
        "head_scale": HEAD_SCALE,
        "standing_pose": "ShirtPantsWB",
        "bust_pose": "pose_Shirt",
        "clothes": "#e8543f",                # 朱シャツ
        "hair": "hair_ShortMessy", "head": HEAD_FILL,
        "face": "face_CheersNM",
        "acc": None,
    },
}


def load_part(name: str, clothes: str, head: str) -> str:
    frag = (PARTS / f"{name}.svg").read_text()
    return frag.replace("{{CLOTHES}}", clothes).replace("{{HEAD}}", head)


def load_standing(name: str, ink: str, clothes: str) -> str:
    frag = (PARTS / f"stand_{name}.svg").read_text()
    return frag.replace("{{CLOTHES}}", clothes).replace("{{INK}}", ink)


def build_head_svg(char: dict, ink: str, head_fill: str, dx: float = 0, dy: float = 0) -> str:
    hair = CP_load(char["hair"], ink, head_fill)
    face = CP_load(char["face"], ink, head_fill)
    acc = CP_load(char["acc"], ink, head_fill) if char["acc"] else ""
    k = char["head_scale"]
    head_tf = f'translate({225 + dx:.0f} {dy:.0f}) translate(359 366) scale({k}) translate(-359 -366)'
    return (
        f'<g transform="{head_tf}">{hair}'
        '<g transform="translate(159 186)">' + face + "</g>"
        '<g transform="translate(47 241)">' + acc + "</g>"
    )


def CP_load(name: str, ink: str, fill: str) -> str:
    frag = (PARTS / f"{name}.svg").read_text()
    frag = frag.replace("{{INK}}", ink)
    frag = frag.replace("{{CLOTHES}}", fill)
    frag = frag.replace("{{HEAD}}", fill)
    return frag


def render_png(svg_str: str, out_png: Path, width: int) -> Image.Image:
    work = Path("/tmp/peeps_work")
    work.mkdir(parents=True, exist_ok=True)
    svg_path = work / "render.svg"
    svg_path.write_text(svg_str)
    png_path = work / "render.png"
    result = subprocess.run(
        ["resvg", str(svg_path), str(png_path), "--width", str(width),
         "--background", "transparent"],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not png_path.exists():
        sys.exit(f"resvg failed (rc={result.returncode}): {result.stderr}")
    return Image.open(png_path).convert("RGBA")


def compose_fullbody(char: dict) -> Image.Image:
    """全身立ち絵を 900x1400 キャンバスに生成 (2パス計測アラインメント)。"""
    ink = INK
    # パス1: 胴体と頭を別々にレンダリングして bbox 計測
    # (ポーズパスは原点より上に描かれるため、ビューボックスは上方向へ拡張)
    body = render_png(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -900 1400 4800">'
        f'<g transform="translate(150 750)">'
        f'<g>{load_standing(char["standing_pose"], ink, char["clothes"])}</g></g></svg>',
        work_png(f"{char.get('_tag', 'c')}_body.png"), 1400)
    bm = bbox_of(body)
    head_alone = render_png(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -900 1400 4800">'
        f'<g transform="translate(225 0) translate(359 366) scale({char["head_scale"]}) '
        f'translate(-359 -366)">{CP_load(char["hair"], ink, char["head"])}'
        '<g transform="translate(159 186)">' + CP_load(char["face"], ink, char["head"]) + "</g>"
        '<g transform="translate(47 241)">' + (CP_load(char["acc"], ink, char["head"]) if char["acc"] else "") + "</g>"
        "</g></svg>",
        work_png(f"{char.get('_tag', 'c')}_head.png"), 1400)
    hm = bbox_of(head_alone)

    # パス2: 補正を適用した完全合成
    ddx = bm["cx"] - hm["cx"]
    ddy = (bm["y0"] + OVERLAP) - hm["y1"]
    full_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -900 1400 4800">'
        f'<g transform="translate(150 750)">'
        f'<g>{load_standing(char["standing_pose"], ink, char["clothes"])}</g></g>'
        f'<g transform="translate({225 + ddx:.0f} {ddy:.0f}) translate(359 366) '
        f'scale({char["head_scale"]}) translate(-359 -366)">'
        + CP_load(char["hair"], ink, char["head"])
        + '<g transform="translate(159 186)">' + CP_load(char["face"], ink, char["head"]) + "</g>"
        + '<g transform="translate(47 241)">' + (CP_load(char["acc"], ink, char["head"]) if char["acc"] else "") + "</g>"
        + "</g></svg>")
    full = render_png(full_svg, work_png(f"{char.get('_tag', 'c')}_full.png"), 1400)
    b = full.getbbox()
    full = full.crop(b)
    return full


def work_png(name: str) -> Path:
    work = Path("/tmp/peeps_work")
    work.mkdir(parents=True, exist_ok=True)
    return work / name


def bbox_of(img: Image.Image):
    b = img.getbbox()
    return {"x0": b[0], "y0": b[1], "x1": b[2], "y1": b[3], "cx": (b[0] + b[2]) / 2}


def place_on_canvas(img: Image.Image) -> Image.Image:
    """全身キャラを 900x1400 キャンバスに縦フィット (下端=足) で配置。"""
    scale = 1380 / img.height
    scaled = img.resize((int(img.width * scale), 1380), Image.LANCZOS)
    canvas = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    canvas.alpha_composite(scaled, ((W * SS - scaled.width) // 2, (H * SS - 1380) // 2))
    return canvas.resize((W, H), Image.LANCZOS)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="assets/ep01/overlay")
    p.add_argument("--only", choices=list(CHARACTERS), default=None)
    p.add_argument("--mode", choices=["fullbody", "bust"], default="fullbody")
    a = p.parse_args(argv)
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = [a.only] if a.only else list(CHARACTERS)
    for cid in targets:
        char = dict(CHARACTERS[cid])
        char["_tag"] = cid
        if a.mode == "fullbody":
            full = compose_fullbody(char)
            canvas = place_on_canvas(full)
            out = out_dir / f"{cid}.png"
            canvas.save(out, "PNG")
            print(f"saved: {out}")
        else:
            svg = build_head_svg_bust(char)
            img = render_png(
                svg.replace('viewBox="0 0 850 1200"', 'viewBox="0 0 850 1200"'), 
                work_png(f"bust_{cid}.png"), 1800)
            img.save(out_dir / f"{cid}_bust.png", "PNG")
            print(f"saved: {out_dir / f'{cid}_bust.png'}")
    return 0


def build_head_svg_bust(char: dict) -> str:
    ink = INK
    head_fill = char["head"]
    pose = CP_load(char["bust_pose"], ink, char["clothes"])
    hair = CP_load(char["hair"], ink, head_fill)
    face = CP_load(char["face"], ink, head_fill)
    acc = CP_load(char["acc"], ink, head_fill) if char["acc"] else ""
    k = char["head_scale"]
    head_tf = f'translate(225 0) translate(359 366) scale({k}) translate(-359 -366)'
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 850 1200">'
        f"<g>{pose}</g>"
        f'<g transform="{head_tf}">{hair}'
        '<g transform="translate(159 186)">' + face + "</g>"
        '<g transform="translate(47 241)">' + acc + "</g>"
        "</g></svg>")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

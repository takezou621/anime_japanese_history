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

from PIL import Image, ImageOps

REPO_ROOT = Path(__file__).resolve().parents[2]
PARTS = REPO_ROOT / "tools" / "peeps" / "parts"
INK = "#26282e"          # 線画 (STYLE_GUIDE テキスト色)
HEAD_FILL = "#fffdf7"    # 頭部/肌ベース (STYLE_GUIDE 温かい白)
W, H = 900, 1400
SS = 2                   # スーパーサンプリング
OVERLAP = 110            # 頭の顎を胴体の襟に重ねるpx (40では首元の柱が露出して顔が浮いた)
HEAD_SCALE = 1.1         # 頭部拡大 (ポーズの胴体が大きめのため)

CHARACTERS = {
    "char_sensei": {
        # 配置は全話で右側固定 (script.json 実測: 右190回/左0回)。
        # 素材の顔は右向きのため、左の相方と向き合うよう左右反転する
        "flip": True,
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


# 表情オーバーレイ (faceパーツの座標系に直接描くパッチ).
# face_Calm の目 (x60-122/186-226, y108-147) と 口 (x122-190, y160-240) を基準にする。
EXPRESSIONS = {
    "surprised": [
        {"op": "patch", "cx": 156, "cy": 205, "rx": 56, "ry": 42},
        {"op": "omouth", "cx": 156, "cy": 200, "rx": 24, "ry": 32},
        {"op": "patch", "cx": 91, "cy": 128, "rx": 36, "ry": 26},
        {"op": "patch", "cx": 206, "cy": 128, "rx": 36, "ry": 26},
        {"op": "eye", "cx": 91, "cy": 124},
        {"op": "eye", "cx": 206, "cy": 124},
    ],
    "smile": [
        {"op": "patch", "cx": 156, "cy": 205, "rx": 58, "ry": 44},
        {"op": "grin", "cx": 156, "cy": 198, "rx": 58, "ry": 44},
    ],
    "serious": [
        {"op": "patch", "cx": 156, "cy": 205, "rx": 56, "ry": 42},
        {"op": "flatmouth", "cx": 156, "cy": 212, "w": 62},
    ],
}


def expression_svg(name: str | None, skin_fill) -> str:
    """表情パッチの SVG 断片を返す (faceグループ内に挿入)."""
    if not name or name not in EXPRESSIONS:
        return ""
    skin = f"#{skin_fill[0]:02x}{skin_fill[1]:02x}{skin_fill[2]:02x}" \
        if isinstance(skin_fill, (tuple, list)) else str(skin_fill)
    out = []
    for op in EXPRESSIONS[name]:
        kind = op["op"]
        if kind == "patch":
            out.append(f'<ellipse cx="{op["cx"]}" cy="{op["cy"]}" '
                       f'rx="{op["rx"]}" ry="{op["ry"]}" fill="{skin}"/>')
        elif kind == "omouth":
            out.append(f'<ellipse cx="{op["cx"]}" cy="{op["cy"]}" '
                       f'rx="{op["rx"]}" ry="{op["ry"]}" fill="{INK}"/>')
        elif kind == "eye":
            out.append(f'<circle cx="{op["cx"]}" cy="{op["cy"]}" r="21" fill="{INK}"/>')
            out.append(f'<circle cx="{op["cx"] - 7}" cy="{op["cy"] - 8}" r="7" '
                       f'fill="#fffdf7"/>')
        elif kind == "grin":
            cx, cy, rx, ry = op["cx"], op["cy"], op["rx"], op["ry"]
            out.append(f'<path d="M{cx - rx} {cy} A {rx} {ry} 0 0 0 {cx + rx} {cy} Z" '
                       f'fill="{INK}"/>')
            out.append(f'<rect x="{cx - rx + 6}" y="{cy}" width="{2 * rx - 12}" '
                       f'height="{ry * 0.34:.0f}" fill="#fffdf7"/>')
        elif kind == "flatmouth":
            out.append(f'<line x1="{op["cx"] - op["w"] / 2}" y1="{op["cy"]}" '
                       f'x2="{op["cx"] + op["w"] / 2}" y2="{op["cy"]}" '
                       f'stroke="{INK}" stroke-width="9" stroke-linecap="round"/>')
    return "".join(out)


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
        '<g transform="translate(159 186)">' + CP_load(char["face"], ink, char["head"])
        + expression_svg(char.get("face_expr"), char["head"]) + "</g>"
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
        + '<g transform="translate(159 186)">' + CP_load(char["face"], ink, char["head"])
        + expression_svg(char.get("face_expr"), char["head"]) + "</g>"
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
    """全身キャラを 900x1400 キャンバスに縦フィット (下端=足) で配置。

    旧実装は SS 適用後のキャンバス (2800px) に対して最終解像度の
    1380px で拡縮していたため、キャラが縦半分・中央浮きになっていた。
    """
    target_h = (H - 20) * SS
    scale = target_h / img.height
    scaled = img.resize((int(img.width * scale), target_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    canvas.alpha_composite(scaled, ((W * SS - scaled.width) // 2,
                                    H * SS - target_h - 10 * SS))
    return canvas.resize((W, H), Image.LANCZOS)


def topmost_center(img: Image.Image):
    """最上部の不透明行の中心xとそのyを返す (バストポーズの首アンカー)。"""
    a = img.getchannel("A")
    w, h = img.size
    px = a.load()
    for y in range(h):
        xs = [x for x in range(w) if px[x, y] > 10]
        if len(xs) >= 3:
            return (xs[0] + xs[-1]) / 2, y
    return w / 2, 0


def compose_bust(char: dict) -> Image.Image:
    """バストアップを 900x1400 キャンバスに生成 (計測アラインメント)。

    旧実装 (build_head_svg_bust) は全身用の固定オフセット
    translate(225 0) と HEAD_SCALE=1.1 を流用していたため、肩幅の広い
    バストポーズでは巨大な顔が胸の上に乗り、位置も左へずれていた。
    ここではポーズと頭部を別々にレンダリングして実測し、
      - 頭の幅 = ポーズ肩幅の 44%
      - 顎の位置 = ポーズ上端 + ポーズ高の 16% (襟に食い込ませる)
      - 頭の水平中心 = ポーズ首アンカー (最上部行) の中心
    で合成し、900x1400 キャンバスへ正規化する。
    """
    ink = INK
    hf = char["head"]
    RW = 1700  # viewBox 850x1200 を 2 倍解像度でレンダリング
    pose = render_png(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 850 1200"><g>'
        + CP_load(char["bust_pose"], ink, char["clothes"]) + "</g></svg>",
        work_png(f"bust_{char['_tag']}_pose.png"), RW)
    head = render_png(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 850 1200">'
        '<g transform="translate(225 0)">'
        + CP_load(char["hair"], ink, hf)
        + '<g transform="translate(159 186)">' + CP_load(char["face"], ink, hf)
        + expression_svg(char.get("face_expr"), hf) + "</g>"
        + '<g transform="translate(47 241)">'
        + (CP_load(char["acc"], ink, hf) if char["acc"] else "") + "</g>"
        + "</g></svg>",
        work_png(f"bust_{char['_tag']}_head.png"), RW)
    pb = pose.getbbox()
    hb = head.getbbox()
    neck_cx, _neck_top = topmost_center(pose)
    pose_w = pb[2] - pb[0]
    pose_h = pb[3] - pb[1]
    head_crop = head.crop(hb)
    k = (0.44 * pose_w) / head_crop.width
    head_s = head_crop.resize(
        (max(1, int(head_crop.width * k)), max(1, int(head_crop.height * k))),
        Image.LANCZOS)
    chin_y = pb[1] + 0.16 * pose_h
    # 頭はポーズの上端より上にはみ出すので、頭の高さ分の余白を持つ
    # キャンバスにポーズを置いてから合成する (余白なしだと頭頂が切れる)
    margin_top = head_s.height + 20
    canvas = Image.new("RGBA", (pose.width, pose.height + margin_top), (0, 0, 0, 0))
    canvas.alpha_composite(pose, (0, margin_top))
    canvas.alpha_composite(
        head_s, (int(neck_cx - head_s.width / 2),
                 int(margin_top + chin_y - head_s.height)))
    fig = canvas.crop(canvas.getbbox())
    s2 = min((W * SS * 0.94) / fig.width, (H * SS * 0.75) / fig.height)
    fig = fig.resize((int(fig.width * s2), int(fig.height * s2)), Image.LANCZOS)
    out = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    out.alpha_composite(fig, ((W * SS - fig.width) // 2, 40 * SS))
    return out.resize((W, H), Image.LANCZOS)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="assets/ep01/overlay")
    p.add_argument("--only", choices=list(CHARACTERS), default=None)
    p.add_argument("--mode", choices=["fullbody", "bust"], default="fullbody")
    p.add_argument("--face", choices=list(EXPRESSIONS), default=None,
                   help="表情オーバーレイ (surprised/smile/serious)")
    p.add_argument("--suffix", default="",
                   help="出力ファイル名の末尾に付ける差分サフィックス")
    a = p.parse_args(argv)
    if a.face and not a.suffix:
        p.error("--face には --suffix が必要です (基本キャラ PNG の上書き防止)")
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = [a.only] if a.only else list(CHARACTERS)
    for cid in targets:
        char = dict(CHARACTERS[cid])
        char["_tag"] = cid
        if a.face:
            char["face_expr"] = a.face
        if a.mode == "fullbody":
            full = compose_fullbody(char)
            canvas = place_on_canvas(full)
            if char.get("flip"):
                canvas = ImageOps.mirror(canvas)
            out = out_dir / f"{cid}{a.suffix}.png"
            canvas.save(out, "PNG")
            print(f"saved: {out}")
        else:
            bust = compose_bust(char)
            if char.get("flip"):
                bust = ImageOps.mirror(bust)
            out = out_dir / f"{cid}{a.suffix}_bust.png"
            bust.save(out, "PNG")
            print(f"saved: {out}")
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

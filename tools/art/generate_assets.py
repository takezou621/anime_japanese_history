#!/usr/bin/env python3
"""ep01 アセット一括生成 ( Issue #3 ).

使い方:
  uv run --with pillow --with numpy python tools/art/generate_assets.py            # 全生成
  uv run --with pillow --with numpy python tools/art/generate_assets.py --only bg_jomon_village bg_school_lab
  uv run --with pillow --with numpy python tools/art/generate_assets.py --chars     # 立ち絵のみ
  uv run --with pillow --with numpy python tools/art/generate_assets.py --preview   # 合成プレビューのみ
  uv run --with pillow --with numpy python tools/art/generate_assets.py --sheet     # コンタクトシート (/tmp)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "art"))

from artlib import palette as P  # noqa: E402
from artlib.canvas import Canvas, save  # noqa: E402
from artlib import character, ui  # noqa: E402
import scenes_ep01 as S  # noqa: E402
import scenes_ep02 as S2  # noqa: E402
from artlib.props import jomon_pot, keyhole_tomb, dotaku as dotaku_prop  # noqa: E402
from artlib.props import haniwa as haniwa_prop  # noqa: E402

ASSETS_ROOT = ROOT / "assets"
ASSETS = ASSETS_ROOT / "ep01"
SCENE_DIR = ASSETS / "scenes"
OVERLAY_DIR = ASSETS / "overlay"
UI_DIR = ASSETS / "ui"

EP_SCENES = {
    "ep02": {
        "dir": ASSETS_ROOT / "ep02",
        "scenes": {
            "bg_asuka_palace": S2.bg_asuka_palace,
            "bg_asuka_court": S2.bg_asuka_court,
            "bg_asuka_ship": S2.bg_asuka_ship,
            "bg_asuka_gate": S2.bg_asuka_gate,
            "bg_asuka_field": S2.bg_asuka_field,
            "bg_asuka_battle": S2.bg_asuka_battle,
            "bg_nara_map": S2.bg_nara_map,
            "bg_nara_ship": S2.bg_nara_ship,
            "bg_nara_capital": S2.bg_nara_capital,
            "bg_nara_temple": S2.bg_nara_temple,
            "bg_nara_field": S2.bg_nara_field,
            "bg_timeline": S2.bg_timeline,
        },
        "priority": ["bg_asuka_palace", "bg_nara_capital"],
        "reused": ["bg_school_lab", "bg_school_lab_evening", "bg_quiz_board"],
    },
}

W, H = 1920, 1080

SCENES = {
    "bg_school_lab": S.bg_school_lab,
    "bg_paleolithic": S.bg_paleolithic,
    "bg_jomon_coast": S.bg_jomon_coast,
    "bg_jomon_pottery": S.bg_jomon_pottery,
    "bg_jomon_village": S.bg_jomon_village,
    "bg_jomon_daily_life": S.bg_jomon_daily_life,
    "bg_yayoi_rice_field": S.bg_yayoi_rice_field,
    "bg_yayoi_village": S.bg_yayoi_village,
    "bg_yayoi_moat": S.bg_yayoi_moat,
    "bg_kofun": S.bg_kofun,
    "bg_kofun_haniwa": S.bg_kofun_haniwa,
    "bg_yamato_court": S.bg_yamato_court,
    "bg_kofun_ships": S.bg_kofun_ships,
    "bg_timeline": S.bg_timeline,
    "bg_quiz_board": S.bg_quiz_board,
    "bg_school_lab_evening": S.bg_school_lab_evening,
}

PRIORITY = ["bg_school_lab", "bg_jomon_village", "bg_yayoi_rice_field"]


# ---------------------------------------------------------------- overlays


def gen_characters():
    outs = []
    for name, fn in (("char_sensei", character.build_sensei),
                     ("char_manabu", character.build_manabu)):
        img = fn().render()
        p = save(img, OVERLAY_DIR / f"{name}.png")
        outs.append(p)
        print(f"  overlay {p.name} {img.size}")
    return outs


def gen_props():
    """小物レイヤー (サムネイル等の再利用用)."""
    specs = [
        ("prop_jomon_pottery", 340, 420, lambda cv: jomon_pot(cv.g(), 170, 380, 1.4, seed=1)),
        ("prop_dotaku", 300, 420, lambda cv: dotaku_prop(cv.g(), 150, 380, 1.5, seed=1)),
        ("prop_haniwa", 280, 400, lambda cv: haniwa_prop(cv.g(), 140, 360, 1.3, seed=1)),
        ("prop_keyhole_tomb", 640, 560, lambda cv: keyhole_tomb(cv.g(), 320, 330, 1.0, seed=1)),
    ]
    outs = []
    for name, w, h, draw in specs:
        cv = Canvas(w, h, ss=2)
        draw(cv)
        img = cv.render()
        p = save(img, OVERLAY_DIR / f"{name}.png")
        outs.append(p)
        print(f"  overlay {p.name} {img.size}")
    return outs


def gen_ui_badges():
    """era_badge / keyword_card 等のサンプルセット (script.json の文言準拠)."""
    eras = [
        ("era_paleolithic", "旧石器時代", "土器のない時代"),
        ("era_jomon", "縄文時代", "約1万年前〜 磨製石器"),
        ("era_yayoi", "弥生時代", "紀元前3世紀ごろ〜 稲作の開始"),
        ("era_kofun", "古墳時代", "3世紀中ごろ〜 前方後円墳"),
    ]
    outs = []
    for name, main, sub in eras:
        img = ui.era_badge(main, sub=sub)
        outs.append(save(img, UI_DIR / f"{name}.png"))
    img = ui.exam_banner("ここが受験ポイント!")
    outs.append(save(img, UI_DIR / "exam_banner.png"))
    for i in (1, 2, 3):
        img = ui.exam_banner(f"クイズ 第{i}問")
        outs.append(save(img, UI_DIR / f"quiz_banner_{i}.png"))
    keywords = [
        ("keyword_seisei", "打製石器"),
        ("keyword_masei", "磨製石器"),
        ("keyword_jomon_pottery", "縄文土器", "世界最古級の土器"),
        ("keyword_pit_dwelling", "竪穴住居"),
        ("keyword_kaizuka", "貝塚"),
        ("keyword_rice", "水稲農業", "平原・低地で開始"),
        ("keyword_warehouse", "高床倉庫"),
        ("keyword_kango", "環濠集落", "戦争のはじまり"),
        ("keyword_dotaku", "銅鐸=祭り・銅剣=武器"),
        ("keyword_himiko", "卑弥呼と邪馬台国", "239年 魏に遣使"),
        ("keyword_zenkofuen", "前方後円墳"),
        ("keyword_haniwa", "埴輪"),
        ("keyword_yamato", "大和政権"),
    ]
    for kw in keywords:
        name, text = kw[0], kw[1]
        sub = kw[2] if len(kw) > 2 else None
        img = ui.keyword_card(text, sub=sub)
        outs.append(save(img, UI_DIR / f"{name}.png"))
    img = ui.year_number("239年")
    outs.append(save(img, UI_DIR / "year_239.png"))
    img = ui.title_main("アニメ日本史ラボ")
    outs.append(save(img, UI_DIR / "title_main.png"))
    manifest = {"ep01_ui_assets": [p.name for p in outs]}
    (UI_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    for p in outs:
        print(f"  ui {p.name} ")
    return outs


# ---------------------------------------------------------------- preview


def gen_preview():
    """bg_jomon_village + char_manabu 合成サンプル."""
    from PIL import Image
    bg = Image.open(SCENE_DIR / "bg_jomon_village.png").convert("RGBA")
    ch = Image.open(OVERLAY_DIR / "char_manabu.png").convert("RGBA")
    scale = 0.62
    ch = ch.resize((int(ch.width * scale), int(ch.height * scale)), Image.LANCZOS)
    base = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    base.alpha_composite(bg)
    # 足元の影
    sh = Canvas(560, 120, ss=2)
    sh.g().ellipse((40, 30, 520, 96), fill=(52, 40, 34, 96))
    shadow = sh.render().resize((280, 60), Image.LANCZOS)
    foot_x, foot_y = 1360, 1012
    base.alpha_composite(shadow, (foot_x - shadow.width // 2, foot_y - 34))
    base.alpha_composite(ch, (foot_x - ch.width // 2, foot_y - ch.height + 4))
    p = save(base, ASSETS / "preview_composite.png")
    print(f"  preview {p}")
    return p


def gen_contact_sheet(out_file="/tmp/ajh_art/sheet_ep01.png", ep="ep01"):
    """QA 用コンタクトシート (/tmp に保存, リポジ外)."""
    from PIL import Image, ImageDraw
    if ep == "ep02":
        names = sorted(EP_SCENES["ep02"]["scenes"].keys())
        scene_dir = EP_SCENES["ep02"]["dir"] / "scenes"
    else:
        names = sorted(SCENES.keys())
        scene_dir = SCENE_DIR
    cols, cw, chh = 3, 480, 270
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw, rows * chh), (24, 26, 32))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        img = Image.open(scene_dir / f"{n}.png").resize((cw, chh), Image.LANCZOS)
        x, y = (i % cols) * cw, (i // cols) * chh
        sheet.paste(img, (x, y))
        d.rectangle([x + 4, y + 4, x + 300, y + 26], fill=(24, 26, 32))
        d.text((x + 10, y + 8), n, fill=(240, 240, 240))
    out = Path(out_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"  sheet {out}")
    return out


# ---------------------------------------------------------------- main


def gen_ui_badges_ep02():
    """ep02 のバッジセット (script.json の文言準拠)."""
    import shutil
    outs = []
    eras = [
        ("era_asuka", "飛鳥時代", "592年〜 大化の改新まで"),
        ("era_taika", "大化の改新", "645年 乙巳の変ののち"),
        ("era_ritsuryo", "律令国家", "大宝律令 701年〜"),
        ("era_nara", "奈良時代", "710年 平城京遷都"),
    ]
    for name, main, sub in eras:
        img = ui.era_badge(main, sub=sub)
        outs.append(save(img, ASSETS_ROOT / "ep02" / "ui" / f"{name}.png"))
    outs.append(save(ui.exam_banner("ここが受験ポイント!"),
                     ASSETS_ROOT / "ep02" / "ui" / "exam_banner.png"))
    for i in (1, 2, 3):
        outs.append(save(ui.exam_banner(f"クイズ 第{i}問"),
                         ASSETS_ROOT / "ep02" / "ui" / f"quiz_banner_{i}.png"))
    keywords = [
        ("keyword_kanii", "冠位十二階"),
        ("keyword_kenpo", "十七条憲法"),
        ("keyword_kenzuishi", "遣隋使", "607年 小野妹子"),
        ("keyword_horyuji", "法隆寺", "世界最古の木造建築"),
        ("keyword_issshi", "乙巳の変", "645年 中大兄皇子"),
        ("keyword_taika", "公地公民・班田収授・租庸調"),
        ("keyword_chuoken", "中央集権", "壬申の乱ののち確立"),
        ("keyword_taihoritsu", "大宝律令", "701年 律令国家へ"),
        ("keyword_nikan", "二官八省一台"),
        ("keyword_kenntoshi", "遣唐使", "630年〜"),
        ("keyword_heijokyo", "平城京", "710年 遷都"),
        ("keyword_kiyo", "古事記・日本書紀・万葉集"),
    ]
    udir = ASSETS_ROOT / "ep02" / "ui"
    for kw in keywords:
        img = ui.keyword_card(kw[1], sub=kw[2] if len(kw) > 2 else None)
        outs.append(save(img, udir / f"{kw[0]}.png"))
    for yr, name in (("645年", "year_645"), ("701年", "year_701"), ("710年", "year_710")):
        outs.append(save(ui.year_number(yr), udir / f"{name}.png"))
    outs.append(save(ui.title_main("アニメ日本史ラボ 第2話"), udir / "title_main.png"))
    for f in ("era_asuka", "era_nara"):
        pass
    manifest = {"ep02_ui_assets": [p.name for p in outs]}
    (udir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ui ep02 x{len(outs)}")
    return outs


def copy_reused_assets(ep="ep02"):
    """ep01 生成物の再利用分をコピー."""
    import shutil
    spec = EP_SCENES[ep]
    src_dir = ASSETS_ROOT / "ep01" / "scenes"
    dst_dir = spec["dir"] / "scenes"
    for name in spec["reused"]:
        shutil.copyfile(src_dir / f"{name}.png", dst_dir / f"{name}.png")
        print(f"  reused {name}.png")
    for f in ("char_sensei.png", "char_manabu.png"):
        shutil.copyfile(ASSETS_ROOT / "ep01" / "overlay" / f,
                        spec["dir"] / "overlay" / f)
    print("  reused char_sensei / char_manabu")


def gen_preview_ep02(bg="bg_asuka_palace", ch_name="char_manabu",
                     foot=(1360, 1012), scale=0.62):
    from PIL import Image
    bg_img = Image.open(ASSETS_ROOT / "ep02" / "scenes" / f"{bg}.png").convert("RGBA")
    ch = Image.open(ASSETS_ROOT / "ep02" / "overlay" / f"{ch_name}.png").convert("RGBA")
    ch = ch.resize((int(ch.width * scale), int(ch.height * scale)), Image.LANCZOS)
    base = Image.new("RGBA", bg_img.size, (0, 0, 0, 0))
    base.alpha_composite(bg_img)
    sh = Canvas(560, 120, ss=2)
    sh.g().ellipse((40, 30, 520, 96), fill=(52, 40, 34, 96))
    shadow = sh.render().resize((280, 60), Image.LANCZOS)
    base.alpha_composite(shadow, (foot[0] - shadow.width // 2, foot[1] - 34))
    base.alpha_composite(ch, (foot[0] - ch.width // 2, foot[1] - ch.height + 4))
    p = save(base, ASSETS_ROOT / "ep02" / "preview_composite.png")
    print(f"  preview {p}")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", default="ep01", choices=["ep01", "ep02"])
    ap.add_argument("--only", nargs="*", help="生成するシーン名")
    ap.add_argument("--chars", action="store_true", help="立ち絵のみ")
    ap.add_argument("--props", action="store_true", help="小物オーバーレイのみ")
    ap.add_argument("--ui", action="store_true", help="バッジのみ")
    ap.add_argument("--preview", action="store_true", help="合成プレビューのみ")
    ap.add_argument("--sheet", action="store_true", help="コンタクトシートのみ")
    ap.add_argument("--priority", action="store_true", help="優先シーンのみ")
    args = ap.parse_args()

    if args.ep == "ep02":
        spec = EP_SCENES["ep02"]
        out_dir = spec["dir"] / "scenes"
        if args.sheet:
            gen_contact_sheet("/tmp/ajh_art/sheet_ep02.png", ep="ep02")
            return
        if args.preview:
            gen_preview_ep02()
            return
        if args.ui:
            gen_ui_badges_ep02()
            return
        copy_reused_assets("ep02")
        todo = args.only or (spec["priority"] if args.priority else list(spec["scenes"].keys()))
        for name in todo:
            fn = spec["scenes"].get(name)
            if fn is None:
                print(f"  !! unknown scene: {name}")
                continue
            cv = S2.new_canvas()
            fn(cv)
            img = cv.render()
            p = save(img, out_dir / f"{name}.png")
            print(f"  scene {p.name} {img.size}")
        if not args.only and not args.priority:
            gen_ui_badges_ep02()
            gen_preview_ep02(bg="bg_nara_capital")
        return

    if args.sheet:
        gen_contact_sheet()
        return
    if args.preview:
        gen_preview()
        return
    if args.chars:
        gen_characters()
        return
    if args.props:
        gen_props()
        return
    if args.ui:
        gen_ui_badges()
        return

    todo = []
    if args.only:
        todo = args.only
    elif args.priority:
        todo = PRIORITY
    else:
        todo = list(SCENES.keys())
    for name in todo:
        fn = SCENES.get(name)
        if fn is None:
            print(f"  !! unknown scene: {name}")
            continue
        cv = S.new_canvas()
        fn(cv)
        img = cv.render()
        p = save(img, SCENE_DIR / f"{name}.png")
        print(f"  scene {p.name} {img.size}")
    if not args.only and not args.priority:
        gen_characters()
        gen_props()
        gen_ui_badges()
        gen_preview()


if __name__ == "__main__":
    main()

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
import scenes_ep03 as S3  # noqa: E402
import scenes_ep04 as S4  # noqa: E402
import scenes_ep05 as S5  # noqa: E402
import scenes_ep06 as S6  # noqa: E402
import scenes_ep07 as S7  # noqa: E402
import scenes_ep08 as S8  # noqa: E402
import scenes_ep09 as S9  # noqa: E402
import scenes_ep10 as S10  # noqa: E402
from artlib.props import jomon_pot, keyhole_tomb, dotaku as dotaku_prop  # noqa: E402
from artlib.props import haniwa as haniwa_prop  # noqa: E402

ASSETS_ROOT = ROOT / "assets"
ASSETS = ASSETS_ROOT / "ep01"
SCENE_DIR = ASSETS / "scenes"
OVERLAY_DIR = ASSETS / "overlay"
UI_DIR = ASSETS / "ui"

EP_SCENES = {
    "ep10": {
        "dir": ASSETS_ROOT / "ep10",
        "scenes": {
            "bg_modern_nisshin": S10.bg_modern_nisshin,
            "bg_modern_nichiro": S10.bg_modern_nichiro,
            "bg_modern_manshu": S10.bg_modern_manshu,
            "bg_modern_panic": S10.bg_modern_panic,
            "bg_modern_taisho": S10.bg_modern_taisho,
            "bg_modern_futsusen": S10.bg_modern_futsusen,
            "bg_modern_taiheiyo": S10.bg_modern_taiheiyo,
            "bg_modern_1945": S10.bg_modern_1945,
            "bg_modern_kenpo": S10.bg_modern_kenpo,
            "bg_modern_korea": S10.bg_modern_korea,
            "bg_modern_growth": S10.bg_modern_growth,
            "bg_modern_dusk": S10.bg_modern_dusk,
            "bg_timeline": S10.bg_timeline,
        },
        "priority": ["bg_modern_1945", "bg_modern_growth"],
        "reused": ["bg_school_lab", "bg_school_lab_evening", "bg_quiz_board"],
    },
    "ep09": {
        "dir": ASSETS_ROOT / "ep09",
        "scenes": {
            "bg_meiji_boshin": S9.bg_meiji_boshin,
            "bg_meiji_civilization": S9.bg_meiji_civilization,
            "bg_meiji_government": S9.bg_meiji_government,
            "bg_meiji_haipan": S9.bg_meiji_haipan,
            "bg_meiji_heishi": S9.bg_meiji_heishi,
            "bg_meiji_itagaki": S9.bg_meiji_itagaki,
            "bg_meiji_nochi": S9.bg_meiji_nochi,
            "bg_meiji_seinan": S9.bg_meiji_seinan,
            "bg_meiji_people": S9.bg_meiji_people,
            "bg_meiji_school": S9.bg_meiji_school,
            "bg_meiji_seikanron": S9.bg_meiji_seikanron,
            "bg_meiji_tomioka": S9.bg_meiji_tomioka,
            "bg_meiji_dusk": S9.bg_meiji_dusk,
            "bg_timeline": S9.bg_timeline,
        },
        "priority": ["bg_meiji_civilization", "bg_meiji_boshin"],
        "reused": ["bg_school_lab", "bg_school_lab_evening", "bg_quiz_board"],
    },
    "ep08": {
        "dir": ASSETS_ROOT / "ep08",
        "scenes": {
            "bg_bakumatsu_blackship": S8.bg_bakumatsu_blackship,
            "bg_bakumatsu_court": S8.bg_bakumatsu_court,
            "bg_bakumatsu_treaty": S8.bg_bakumatsu_treaty,
            "bg_bakumatsu_ansei": S8.bg_bakumatsu_ansei,
            "bg_bakumatsu_sonno": S8.bg_bakumatsu_sonno,
            "bg_bakumatsu_sakurada": S8.bg_bakumatsu_sakurada,
            "bg_bakumatsu_warship": S8.bg_bakumatsu_warship,
            "bg_bakumatsu_alliance": S8.bg_bakumatsu_alliance,
            "bg_bakumatsu_return": S8.bg_bakumatsu_return,
            "bg_bakumatsu_kaikoku": S8.bg_bakumatsu_kaikoku,
            "bg_bakumatsu_kyoto": S8.bg_bakumatsu_kyoto,
            "bg_bakumatsu_dawn": S8.bg_bakumatsu_dawn,
            "bg_timeline": S8.bg_timeline,
        },
        "priority": ["bg_bakumatsu_blackship", "bg_bakumatsu_sakurada"],
        "reused": ["bg_school_lab", "bg_school_lab_evening", "bg_quiz_board"],
    },
    "ep07": {
        "dir": ASSETS_ROOT / "ep07",
        "scenes": {
            "bg_edo_shogunate": S7.bg_edo_shogunate,
            "bg_edo_government": S7.bg_edo_government,
            "bg_edo_daimyo": S7.bg_edo_daimyo,
            "bg_edo_sankinkotai": S7.bg_edo_sankinkotai,
            "bg_edo_kirishitan": S7.bg_edo_kirishitan,
            "bg_edo_shimabara": S7.bg_edo_shimabara,
            "bg_edo_sakoku": S7.bg_edo_sakoku,
            "bg_edo_dejima": S7.bg_edo_dejima,
            "bg_edo_trade": S7.bg_edo_trade,
            "bg_edo_town": S7.bg_edo_town,
            "bg_edo_culture": S7.bg_edo_culture,
            "bg_edo_dusk": S7.bg_edo_dusk,
            "bg_timeline": S7.bg_timeline,
        },
        "priority": ["bg_edo_shogunate", "bg_edo_sankinkotai"],
        "reused": ["bg_school_lab", "bg_school_lab_evening", "bg_quiz_board"],
    },
    "ep06": {
        "dir": ASSETS_ROOT / "ep06",
        "scenes": {
            "bg_azuchi_okahazama": S6.bg_azuchi_okahazama,
            "bg_azuchi_gifu": S6.bg_azuchi_gifu,
            "bg_azuchi_castle": S6.bg_azuchi_castle,
            "bg_azuchi_nagashino": S6.bg_azuchi_nagashino,
            "bg_azuchi_honnoji": S6.bg_azuchi_honnoji,
            "bg_azuchi_yamazaki": S6.bg_azuchi_yamazaki,
            "bg_azuchi_osaka": S6.bg_azuchi_osaka,
            "bg_azuchi_kenchi": S6.bg_azuchi_kenchi,
            "bg_azuchi_korea": S6.bg_azuchi_korea,
            "bg_azuchi_momoyama": S6.bg_azuchi_momoyama,
            "bg_azuchi_chado": S6.bg_azuchi_chado,
            "bg_azuchi_sunset": S6.bg_azuchi_sunset,
            "bg_timeline": S6.bg_timeline,
        },
        "priority": ["bg_azuchi_castle", "bg_azuchi_nagashino"],
        "reused": ["bg_school_lab", "bg_school_lab_evening", "bg_quiz_board"],
    },
    "ep05": {
        "dir": ASSETS_ROOT / "ep05",
        "scenes": {
            "bg_muromachi_kamakura_fall": S5.bg_muromachi_kamakura_fall,
            "bg_muromachi_newgov": S5.bg_muromachi_newgov,
            "bg_muromachi_takauji": S5.bg_muromachi_takauji,
            "bg_muromachi_namboku": S5.bg_muromachi_namboku,
            "bg_muromachi_yoshimitsu": S5.bg_muromachi_yoshimitsu,
            "bg_muromachi_ship": S5.bg_muromachi_ship,
            "bg_muromachi_kinkaku": S5.bg_muromachi_kinkaku,
            "bg_muromachi_onin": S5.bg_muromachi_onin,
            "bg_muromachi_domain": S5.bg_muromachi_domain,
            "bg_muromachi_gekokujo": S5.bg_muromachi_gekokujo,
            "bg_muromachi_ginkaku": S5.bg_muromachi_ginkaku,
            "bg_muromachi_sengoku": S5.bg_muromachi_sengoku,
            "bg_timeline": S5.bg_timeline,
        },
        "priority": ["bg_muromachi_kinkaku", "bg_muromachi_onin"],
        "reused": ["bg_school_lab", "bg_school_lab_evening", "bg_quiz_board"],
    },
    "ep04": {
        "dir": ASSETS_ROOT / "ep04",
        "scenes": {
            "bg_kamakura_rebellion": S4.bg_kamakura_rebellion,
            "bg_kamakura_harbor": S4.bg_kamakura_harbor,
            "bg_kamakura_uprising": S4.bg_kamakura_uprising,
            "bg_kamakura_seabattle": S4.bg_kamakura_seabattle,
            "bg_kamakura_shogunate": S4.bg_kamakura_shogunate,
            "bg_kamakura_oath": S4.bg_kamakura_oath,
            "bg_kamakura_shokyu": S4.bg_kamakura_shokyu,
            "bg_kamakura_lawbook": S4.bg_kamakura_lawbook,
            "bg_kamakura_mongol": S4.bg_kamakura_mongol,
            "bg_kamakura_tokuso": S4.bg_kamakura_tokuso,
            "bg_kamakura_jodo": S4.bg_kamakura_jodo,
            "bg_kamakura_zen": S4.bg_kamakura_zen,
            "bg_timeline": S4.bg_timeline,
        },
        "priority": ["bg_kamakura_seabattle", "bg_kamakura_shogunate"],
        "reused": ["bg_school_lab", "bg_school_lab_evening", "bg_quiz_board"],
    },
    "ep03": {
        "dir": ASSETS_ROOT / "ep03",
        "scenes": {
            "bg_heian_capital": S3.bg_heian_capital,
            "bg_heian_frontier": S3.bg_heian_frontier,
            "bg_heian_palace": S3.bg_heian_palace,
            "bg_heian_court": S3.bg_heian_court,
            "bg_heian_ceremony": S3.bg_heian_ceremony,
            "bg_heian_ship": S3.bg_heian_ship,
            "bg_heian_mansion": S3.bg_heian_mansion,
            "bg_heian_field": S3.bg_heian_field,
            "bg_heian_writing": S3.bg_heian_writing,
            "bg_heian_emaki": S3.bg_heian_emaki,
            "bg_heian_amida": S3.bg_heian_amida,
            "bg_heian_dusk": S3.bg_heian_dusk,
            "bg_timeline": S3.bg_timeline,
        },
        "priority": ["bg_heian_mansion", "bg_heian_capital"],
        "reused": ["bg_school_lab", "bg_school_lab_evening", "bg_quiz_board"],
    },
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


def gen_next_episode_card():
    """汎用の次回予告カード背景 (assets/common/ui/) を生成."""
    out_dir = ASSETS_ROOT / "common" / "ui"
    img = ui.next_episode_card()
    p = save(img, out_dir / "bg_next_episode.png")
    print(f"  ui shared {p.name}")
    return p


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
        outs.append(save(ui.keyword_card_red(text, sub=sub), UI_DIR / f"{name}_red.png"))
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
    if ep in EP_SCENES:
        names = sorted(EP_SCENES[ep]["scenes"].keys())
        scene_dir = EP_SCENES[ep]["dir"] / "scenes"
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
        outs.append(save(ui.keyword_card_red(kw[1], sub=kw[2] if len(kw) > 2 else None),
                         udir / f"{kw[0]}_red.png"))
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


def gen_ui_badges_ep10():
    """ep10 のバッジセット."""
    outs = []
    udir = ASSETS_ROOT / "ep10" / "ui"
    eras = [
        ("era_nisshin", "日清・日露戦争", "1894年・1904年"),
        ("era_taisho2", "大正デモクラシー", "普通選挙法 1925年"),
        ("era_1945", "1945 焼け野原", "太平洋戦争の終結"),
        ("era_growth", "高度経済成長", "復興と発展"),
    ]
    for name, main, sub in eras:
        outs.append(save(ui.era_badge(main, sub=sub), udir / f"{name}.png"))
    outs.append(save(ui.exam_banner("ここが受験ポイント!"), udir / "exam_banner.png"))
    for i in (1, 2, 3):
        outs.append(save(ui.exam_banner(f"クイズ 第{i}問"), udir / f"quiz_banner_{i}.png"))
    keywords = [
        ("keyword_nisshin2", "日清戦争", "1894年〜95年"),
        ("keyword_nichiro2", "日露戦争", "1904年〜05年"),
        ("keyword_manshu2", "満州事変", "1931年"),
        ("keyword_panic2", "世界恐慌", "1929年〜"),
        ("keyword_futsusen2", "普通選挙法", "1925年"),
        ("keyword_taiheiyo2", "太平洋戦争", "1941年〜45年"),
        ("keyword_kenpo2", "日本国憲法", "1946年11月3日公布"),
        ("keyword_kodo", "高度経済成長", "1955年〜"),
    ]
    for kw in keywords:
        img = ui.keyword_card(kw[1], sub=kw[2] if len(kw) > 2 else None)
        outs.append(save(img, udir / f"{kw[0]}.png"))
        outs.append(save(ui.keyword_card_red(kw[1], sub=kw[2] if len(kw) > 2 else None),
                         udir / f"{kw[0]}_red.png"))
    for yr, name in (("1894年", "year_1894"), ("1904年", "year_1904"),
                     ("1925年", "year_1925"), ("1945年", "year_1945")):
        outs.append(save(ui.year_number(yr), udir / f"{name}.png"))
    outs.append(save(ui.title_main("アニメ日本史ラボ 最終話"), udir / "title_main.png"))
    manifest = {"ep10_ui_assets": [p.name for p in outs]}
    (udir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ui ep10 x{len(outs)}")
    return outs


def gen_ui_badges_ep09():
    """ep09 のバッジセット."""
    outs = []
    udir = ASSETS_ROOT / "ep09" / "ui"
    eras = [
        ("era_boshin", "戊辰戦争", "1868年 王政復古ののち"),
        ("era_haipan", "廃藩置県", "1871年 藩を廃止"),
        ("result", "文明開化", "学制・地租改正・徴兵令"),
        ("era_minken", "自由民権運動", "1874年〜"),
    ]
    for name, main, sub in eras:
        outs.append(save(ui.era_badge(main, sub=sub), udir / f"{name}.png"))
    outs.append(save(ui.exam_banner("ここが受験ポイント!"), udir / "exam_banner.png"))
    for i in (1, 2, 3):
        outs.append(save(ui.exam_banner(f"クイズ 第{i}問"), udir / f"quiz_banner_{i}.png"))
    keywords = [
        ("keyword_boshin", "戊辰戦争", "1868年 旧幕府軍との戦い"),
        ("keyword_haikan", "廃藩置県", "1871年 中央集権へ"),
        ("keyword_zeichi", "地租改正", "1873年"),
        ("keyword_chohei", "徴兵令", "1873年"),
        ("keyword_gakusei", "学制", "1872年"),
        ("keyword_tomioka", "富岡製糸場", "1872年 群馬"),
        ("keyword_seikan", "征韓論", "1873年 西郷隆盛"),
        ("keyword_itagaki", "自由民権運動", "板垣退助"),
    ]
    for kw in keywords:
        img = ui.keyword_card(kw[1], sub=kw[2] if len(kw) > 2 else None)
        outs.append(save(img, udir / f"{kw[0]}.png"))
        outs.append(save(ui.keyword_card_red(kw[1], sub=kw[2] if len(kw) > 2 else None),
                         udir / f"{kw[0]}_red.png"))
    for yr, name in (("1868年", "year_1868"), ("1871年", "year_1871"),
                     ("1872年", "year_1872"), ("1877年", "year_1877")):
        outs.append(save(ui.year_number(yr), udir / f"{name}.png"))
    outs.append(save(ui.title_main("アニメ日本史ラボ 第9話"), udir / "title_main.png"))
    manifest = {"ep09_ui_assets": [p.name for p in outs]}
    (udir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ui ep09 x{len(outs)}")
    return outs


def gen_ui_badges_ep08():
    """ep08 のバッジセット."""
    outs = []
    udir = ASSETS_ROOT / "ep08" / "ui"
    eras = [
        ("era_blackship", "黒船来航", "1853年 ペリー"),
        ("era_sakurada", "桜田門外の変", "1860年 井伊直弼"),
        ("era_chochu", "薩長同盟", "1866年 西郷と桂"),
        ("era_taisei", "大政奉還", "1867年 徳川慶喜"),
    ]
    for name, main, sub in eras:
        outs.append(save(ui.era_badge(main, sub=sub), udir / f"{name}.png"))
    outs.append(save(ui.exam_banner("ここが受験ポイント!"), udir / "exam_banner.png"))
    for i in (1, 2, 3):
        outs.append(save(ui.exam_banner(f"クイズ 第{i}問"), udir / f"quiz_banner_{i}.png"))
    keywords = [
        ("keyword_perry", "ペリー来航", "1853年 浦賀"),
        ("keyword_washin", "日米和親条約", "1854年"),
        ("keyword_ansei", "安政の大獄", "1858年 井伊直弼"),
        ("keyword_sonno", "尊王攘夷", "倒幕運動へ"),
        ("keyword_sakurada2", "桜田門外の変", "1860年"),
        ("keyword_chochu2", "薩長同盟", "1866年 西郷・桂"),
        ("keyword_taisei2", "大政奉還", "1867年 二条城"),
        ("keyword_meiji", "王政復古", "1868年 明治維新へ"),
    ]
    for kw in keywords:
        img = ui.keyword_card(kw[1], sub=kw[2] if len(kw) > 2 else None)
        outs.append(save(img, udir / f"{kw[0]}.png"))
        outs.append(save(ui.keyword_card_red(kw[1], sub=kw[2] if len(kw) > 2 else None),
                         udir / f"{kw[0]}_red.png"))
    for yr, name in (("1853年", "year_1853"), ("1860年", "year_1860"),
                     ("1867年", "year_1867")):
        outs.append(save(ui.year_number(yr), udir / f"{name}.png"))
    outs.append(save(ui.title_main("アニメ日本史ラボ 第8話"), udir / "title_main.png"))
    manifest = {"ep08_ui_assets": [p.name for p in outs]}
    (udir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ui ep08 x{len(outs)}")
    return outs


def gen_ui_badges_ep07():
    """ep07 のバッジセット."""
    outs = []
    udir = ASSETS_ROOT / "ep07" / "ui"
    eras = [
        ("era_sekigahara", "関ヶ原の戦い", "1600年 天下分け目"),
        ("era_edo_bakufu", "江戸幕府", "1603年 家康の開幕"),
        ("era_shimabara", "島原の乱", "1637年 天草・原城"),
        ("era_sakoku", "鎖国", "1639年 国を閉ざす"),
    ]
    for name, main, sub in eras:
        outs.append(save(ui.era_badge(main, sub=sub), udir / f"{name}.png"))
    outs.append(save(ui.exam_banner("ここが受験ポイント!"), udir / "exam_banner.png"))
    for i in (1, 2, 3):
        outs.append(save(ui.exam_banner(f"クイズ 第{i}問"), udir / f"quiz_banner_{i}.png"))
    keywords = [
        ("keyword_ieyasu", "徳川家康", "江戸幕府初代将軍"),
        ("keyword_shokuhou", "参勤交代", "大名の江戸滞在"),
        ("keyword_buke", "武家諸法度"),
        ("keyword_kirishitan", "キリシタン禁教"),
        ("keyword_shimabara", "島原の乱", "1637年 天草四郎"),
        ("keyword_sakoku", "鎖国", "1639年 完成"),
        ("keyword_dejima", "出島", "オランダとの窓"),
        ("keyword_genroku", "元禄文化", "上方の町人文化"),
    ]
    for kw in keywords:
        img = ui.keyword_card(kw[1], sub=kw[2] if len(kw) > 2 else None)
        outs.append(save(img, udir / f"{kw[0]}.png"))
        outs.append(save(ui.keyword_card_red(kw[1], sub=kw[2] if len(kw) > 2 else None),
                         udir / f"{kw[0]}_red.png"))
    for yr, name in (("1600年", "year_1600"), ("1603年", "year_1603"),
                     ("1637年", "year_1637"), ("1639年", "year_1639")):
        outs.append(save(ui.year_number(yr), udir / f"{name}.png"))
    outs.append(save(ui.title_main("アニメ日本史ラボ 第7話"), udir / "title_main.png"))
    manifest = {"ep07_ui_assets": [p.name for p in outs]}
    (udir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ui ep07 x{len(outs)}")
    return outs


def gen_ui_badges_ep06():
    """ep06 のバッジセット."""
    outs = []
    udir = ASSETS_ROOT / "ep06" / "ui"
    eras = [
        ("era_okahazama", "桶狭間の戦い", "1560年 織田信長"),
        ("era_tenka", "天下布武", "岐阜城・安土城"),
        ("era_honnoji", "本能寺の変", "1582年 光秀の謀反"),
        ("era_toyotomi", "豊臣政権", "太閤検地・刀狩り"),
    ]
    for name, main, sub in eras:
        outs.append(save(ui.era_badge(main, sub=sub), udir / f"{name}.png"))
    outs.append(save(ui.exam_banner("ここが受験ポイント!"), udir / "exam_banner.png"))
    for i in (1, 2, 3):
        outs.append(save(ui.exam_banner(f"クイズ 第{i}問"), udir / f"quiz_banner_{i}.png"))
    keywords = [
        ("keyword_okahazama", "桶狭間の戦い", "1560年 今川義元を討つ"),
        ("keyword_gifu", "岐阜城", "稲葉山城を改称"),
        ("keyword_azuchi", "安土城", "琵琶湖畔の5重天守"),
        ("keyword_nagashino", "長篠の戦い", "1575年 三千挺鉄砲"),
        ("keyword_honnoji", "本能寺の変", "1582年 明智光秀"),
        ("keyword_yamazaki", "山崎の戦い", "天王山 秀吉の勝利"),
        ("keyword_shikko", "四民公平の地教"),
        ("keyword_kenchi", "太閤検地", "土地の丈量"),
        ("keyword_katana", "刀狩り"),
        ("keyword_chado", "茶の湯", "千利休の侘び茶"),
    ]
    for kw in keywords:
        img = ui.keyword_card(kw[1], sub=kw[2] if len(kw) > 2 else None)
        outs.append(save(img, udir / f"{kw[0]}.png"))
        outs.append(save(ui.keyword_card_red(kw[1], sub=kw[2] if len(kw) > 2 else None),
                         udir / f"{kw[0]}_red.png"))
    for yr, name in (("1560年", "year_1560"), ("1582年", "year_1582"),
                     ("1590年", "year_1590")):
        outs.append(save(ui.year_number(yr), udir / f"{name}.png"))
    outs.append(save(ui.title_main("アニメ日本史ラボ 第6話"), udir / "title_main.png"))
    manifest = {"ep06_ui_assets": [p.name for p in outs]}
    (udir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ui ep06 x{len(outs)}")
    return outs


def gen_ui_badges_ep05():
    """ep05 のバッジセット."""
    outs = []
    udir = ASSETS_ROOT / "ep05" / "ui"
    eras = [
        ("era_muromachi", "室町幕府", "1336年 足利尊氏"),
        ("era_namboku", "南北朝の動乱", "吉野朝と京都朝"),
        ("era_yoshimitsu", "義満の栄華", "金閣と日明貿易"),
        ("era_onin", "応仁の乱", "1467年〜 戦国の序章"),
    ]
    for name, main, sub in eras:
        outs.append(save(ui.era_badge(main, sub=sub), udir / f"{name}.png"))
    outs.append(save(ui.exam_banner("ここが受験ポイント!"), udir / "exam_banner.png"))
    for i in (1, 2, 3):
        outs.append(save(ui.exam_banner(f"クイズ 第{i}問"), udir / f"quiz_banner_{i}.png"))
    keywords = [
        ("keyword_takauji", "足利尊氏", "室町幕府を開く"),
        ("keyword_kenmu", "建武の新政", "後醍醐天皇"),
        ("keyword_namboku", "南北朝", "北朝と南朝"),
        ("keyword_shugo2", "守護大名", "領国を固める"),
        ("keyword_yoshimitsu", "足利義満", "花の御所・金閣"),
        ("keyword_kinkaku", "金閣", "山吹金色の楼閣"),
        ("keyword_kango", "勘合貿易", "日明貿易"),
        ("keyword_onin", "応仁の乱", "1467年〜11年の戦乱"),
        ("keyword_gekokujo", "下剋上", "守護討伐・国人排斥"),
        ("keyword_ginkaku", "銀閣と東山文化", "足利義政"),
    ]
    for kw in keywords:
        img = ui.keyword_card(kw[1], sub=kw[2] if len(kw) > 2 else None)
        outs.append(save(img, udir / f"{kw[0]}.png"))
        outs.append(save(ui.keyword_card_red(kw[1], sub=kw[2] if len(kw) > 2 else None),
                         udir / f"{kw[0]}_red.png"))
    for yr, name in (("1336年", "year_1336"), ("1392年", "year_1392"),
                     ("1467年", "year_1467")):
        outs.append(save(ui.year_number(yr), udir / f"{name}.png"))
    outs.append(save(ui.title_main("アニメ日本史ラボ 第5話"), udir / "title_main.png"))
    manifest = {"ep05_ui_assets": [p.name for p in outs]}
    (udir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ui ep05 x{len(outs)}")
    return outs


def gen_ui_badges_ep04():
    """ep04 のバッジセット."""
    outs = []
    udir = ASSETS_ROOT / "ep04" / "ui"
    eras = [
        ("era_heishi", "平氏政権", "平清盛の栄華"),
        ("era_kamakura", "鎌倉幕府", "1192年 頼朝の開幕"),
        ("era_shokyu", "承久の乱", "1221年 幕府の勝利"),
        ("era_mongol", "元寇", "1274・1281年"),
    ]
    for name, main, sub in eras:
        outs.append(save(ui.era_badge(main, sub=sub), udir / f"{name}.png"))
    outs.append(save(ui.exam_banner("ここが受験ポイント!"), udir / "exam_banner.png"))
    for i in (1, 2, 3):
        outs.append(save(ui.exam_banner(f"クイズ 第{i}問"), udir / f"quiz_banner_{i}.png"))
    keywords = [
        ("keyword_heishi", "平氏政権", "平清盛 太政大臣"),
        ("keyword_genpei", "源平合戦", "壇ノ浦 1185年"),
        ("keyword_kamakura", "鎌倉幕府", "1192年 源頼朝"),
        ("keyword_shugo", "守護・地頭"),
        ("keyword_shokyu", "承久の乱", "1221年 後鳥羽上皇"),
        ("keyword_seisei", "御成敗式目", "1232年 北条泰時"),
        ("keyword_mongol", "元寇", "文永・弘安の役"),
        ("keyword_tokuso", "得宗専制", "北条氏の独裁"),
        ("keyword_jodo", "浄土教", "法然・親鸞"),
        ("keyword_zen", "禅宗", "栄西・道元"),
    ]
    for kw in keywords:
        img = ui.keyword_card(kw[1], sub=kw[2] if len(kw) > 2 else None)
        outs.append(save(img, udir / f"{kw[0]}.png"))
        outs.append(save(ui.keyword_card_red(kw[1], sub=kw[2] if len(kw) > 2 else None),
                         udir / f"{kw[0]}_red.png"))
    for yr, name in (("1185年", "year_1185"), ("1192年", "year_1192"),
                     ("1221年", "year_1221"), ("1232年", "year_1232")):
        outs.append(save(ui.year_number(yr), udir / f"{name}.png"))
    outs.append(save(ui.title_main("アニメ日本史ラボ 第4話"), udir / "title_main.png"))
    manifest = {"ep04_ui_assets": [p.name for p in outs]}
    (udir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ui ep04 x{len(outs)}")
    return outs


def gen_preview_generic(ep="ep04", bg=None, ch_name="char_manabu",
                        foot=(1360, 1012), scale=0.62):
    from PIL import Image
    bg = bg or {"ep02": "bg_asuka_palace", "ep03": "bg_heian_mansion",
                "ep04": "bg_kamakura_shogunate"}[ep]
    bg_img = Image.open(ASSETS_ROOT / ep / "scenes" / f"{bg}.png").convert("RGBA")
    ch = Image.open(ASSETS_ROOT / ep / "overlay" / f"{ch_name}.png").convert("RGBA")
    ch = ch.resize((int(ch.width * scale), int(ch.height * scale)), Image.LANCZOS)
    base = Image.new("RGBA", bg_img.size, (0, 0, 0, 0))
    base.alpha_composite(bg_img)
    sh = Canvas(560, 120, ss=2)
    sh.g().ellipse((40, 30, 520, 96), fill=(52, 40, 34, 96))
    shadow = sh.render().resize((280, 60), Image.LANCZOS)
    base.alpha_composite(shadow, (foot[0] - shadow.width // 2, foot[1] - 34))
    base.alpha_composite(ch, (foot[0] - ch.width // 2, foot[1] - ch.height + 4))
    p = save(base, ASSETS_ROOT / ep / "preview_composite.png")
    print(f"  preview {p}")
    return p


def gen_ui_badges_ep03():
    """ep03 のバッジセット."""
    outs = []
    udir = ASSETS_ROOT / "ep03" / "ui"
    eras = [
        ("era_heian", "平安時代", "794年 平安遷都〜"),
        ("era_kengyou", "摂関政治", "藤原氏の全盛"),
        ("era_kokufu", "国風文化", "仮名・絵巻・浄土教"),
    ]
    for name, main, sub in eras:
        outs.append(save(ui.era_badge(main, sub=sub), udir / f"{name}.png"))
    outs.append(save(ui.exam_banner("ここが受験ポイント!"), udir / "exam_banner.png"))
    for i in (1, 2, 3):
        outs.append(save(ui.exam_banner(f"クイズ 第{i}問"), udir / f"quiz_banner_{i}.png"))
    keywords = [
        ("keyword_heiankyo", "平安京", "794年 桓武天皇"),
        ("keyword_kozui", "皇位継承と政争"),
        ("keyword_kanpyo", "寛平・延喜の治"),
        ("keyword_sessho", "摂関政治", "藤原氏 北家"),
        ("keyword_shinden", "寝殿造"),
        ("keyword_kana", "仮名文字", "真・草・仮名"),
        ("keyword_kokufu", "国風文化", "古風・洒脱の文化"),
        ("keyword_emaki", "物語絵巻"),
        ("keyword_jodo", "浄土教", "阿弥陀如来信仰"),
    ]
    for kw in keywords:
        img = ui.keyword_card(kw[1], sub=kw[2] if len(kw) > 2 else None)
        outs.append(save(img, udir / f"{kw[0]}.png"))
        outs.append(save(ui.keyword_card_red(kw[1], sub=kw[2] if len(kw) > 2 else None),
                         udir / f"{kw[0]}_red.png"))
    outs.append(save(ui.year_number("794年"), udir / "year_794.png"))
    outs.append(save(ui.title_main("アニメ日本史ラボ 第3話"), udir / "title_main.png"))
    manifest = {"ep03_ui_assets": [p.name for p in outs]}
    (udir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ui ep03 x{len(outs)}")
    return outs


def gen_preview_ep03(bg="bg_heian_mansion", ch_name="char_manabu",
                     foot=(1360, 1012), scale=0.62):
    from PIL import Image
    bg_img = Image.open(ASSETS_ROOT / "ep03" / "scenes" / f"{bg}.png").convert("RGBA")
    ch = Image.open(ASSETS_ROOT / "ep03" / "overlay" / f"{ch_name}.png").convert("RGBA")
    ch = ch.resize((int(ch.width * scale), int(ch.height * scale)), Image.LANCZOS)
    base = Image.new("RGBA", bg_img.size, (0, 0, 0, 0))
    base.alpha_composite(bg_img)
    sh = Canvas(560, 120, ss=2)
    sh.g().ellipse((40, 30, 520, 96), fill=(52, 40, 34, 96))
    shadow = sh.render().resize((280, 60), Image.LANCZOS)
    base.alpha_composite(shadow, (foot[0] - shadow.width // 2, foot[1] - 34))
    base.alpha_composite(ch, (foot[0] - ch.width // 2, foot[1] - ch.height + 4))
    p = save(base, ASSETS_ROOT / "ep03" / "preview_composite.png")
    print(f"  preview {p}")
    return p


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
    ap.add_argument("--ep", default="ep01",
                    choices=["ep01", "ep02", "ep03", "ep04", "ep05", "ep06", "ep07",
                             "ep08", "ep09", "ep10"])
    ap.add_argument("--only", nargs="*", help="生成するシーン名")
    ap.add_argument("--chars", action="store_true", help="立ち絵のみ")
    ap.add_argument("--props", action="store_true", help="小物オーバーレイのみ")
    ap.add_argument("--ui", action="store_true", help="バッジのみ")
    ap.add_argument("--preview", action="store_true", help="合成プレビューのみ")
    ap.add_argument("--sheet", action="store_true", help="コンタクトシートのみ")
    ap.add_argument("--priority", action="store_true", help="優先シーンのみ")
    args = ap.parse_args()

    if args.ep == "ep10":
        spec = EP_SCENES["ep10"]
        out_dir = spec["dir"] / "scenes"
        if args.sheet:
            gen_contact_sheet("/tmp/ajh_art/sheet_ep10.png", ep="ep10")
            return
        if args.preview:
            gen_preview_generic("ep10")
            return
        if args.ui:
            gen_ui_badges_ep10()
            return
        copy_reused_assets("ep10")
        todo = args.only or (spec["priority"] if args.priority else list(spec["scenes"].keys()))
        for name in todo:
            fn = spec["scenes"].get(name)
            if fn is None:
                print(f"  !! unknown scene: {name}")
                continue
            cv = S10.new_canvas()
            fn(cv)
            img = cv.render()
            p = save(img, out_dir / f"{name}.png")
            print(f"  scene {p.name} {img.size}")
        if not args.only and not args.priority:
            gen_ui_badges_ep10()
            gen_next_episode_card()
            gen_preview_generic("ep10", bg="bg_modern_growth")
        return

    if args.ep == "ep09":
        spec = EP_SCENES["ep09"]
        out_dir = spec["dir"] / "scenes"
        if args.sheet:
            gen_contact_sheet("/tmp/ajh_art/sheet_ep09.png", ep="ep09")
            return
        if args.preview:
            gen_preview_generic("ep09")
            return
        if args.ui:
            gen_ui_badges_ep09()
            return
        copy_reused_assets("ep09")
        todo = args.only or (spec["priority"] if args.priority else list(spec["scenes"].keys()))
        for name in todo:
            fn = spec["scenes"].get(name)
            if fn is None:
                print(f"  !! unknown scene: {name}")
                continue
            cv = S9.new_canvas()
            fn(cv)
            img = cv.render()
            img = ui.harmonize(img)
            p = save(img, out_dir / f"{name}.png")
            print(f"  scene {p.name} {img.size}")
        if not args.only and not args.priority:
            gen_ui_badges_ep09()
            gen_next_episode_card()
            gen_preview_generic("ep09", bg="bg_meiji_civilization")
        return

    if args.ep == "ep08":
        spec = EP_SCENES["ep08"]
        out_dir = spec["dir"] / "scenes"
        if args.sheet:
            gen_contact_sheet("/tmp/ajh_art/sheet_ep08.png", ep="ep08")
            return
        if args.preview:
            gen_preview_generic("ep08")
            return
        if args.ui:
            gen_ui_badges_ep08()
            return
        copy_reused_assets("ep08")
        todo = args.only or (spec["priority"] if args.priority else list(spec["scenes"].keys()))
        for name in todo:
            fn = spec["scenes"].get(name)
            if fn is None:
                print(f"  !! unknown scene: {name}")
                continue
            cv = S8.new_canvas()
            fn(cv)
            img = cv.render()
            img = ui.harmonize(img)
            p = save(img, out_dir / f"{name}.png")
            print(f"  scene {p.name} {img.size}")
        if not args.only and not args.priority:
            gen_ui_badges_ep08()
            gen_next_episode_card()
            gen_preview_generic("ep08", bg="bg_bakumatsu_blackship")
        return

    if args.ep == "ep07":
        spec = EP_SCENES["ep07"]
        out_dir = spec["dir"] / "scenes"
        if args.sheet:
            gen_contact_sheet("/tmp/ajh_art/sheet_ep07.png", ep="ep07")
            return
        if args.preview:
            gen_preview_generic("ep07")
            return
        if args.ui:
            gen_ui_badges_ep07()
            return
        copy_reused_assets("ep07")
        todo = args.only or (spec["priority"] if args.priority else list(spec["scenes"].keys()))
        for name in todo:
            fn = spec["scenes"].get(name)
            if fn is None:
                print(f"  !! unknown scene: {name}")
                continue
            cv = S7.new_canvas()
            fn(cv)
            img = cv.render()
            img = ui.harmonize(img)
            p = save(img, out_dir / f"{name}.png")
            print(f"  scene {p.name} {img.size}")
        if not args.only and not args.priority:
            gen_ui_badges_ep07()
            gen_next_episode_card()
            gen_preview_generic("ep07", bg="bg_edo_shogunate")
        return

    if args.ep == "ep06":
        spec = EP_SCENES["ep06"]
        out_dir = spec["dir"] / "scenes"
        if args.sheet:
            gen_contact_sheet("/tmp/ajh_art/sheet_ep06.png", ep="ep06")
            return
        if args.preview:
            gen_preview_generic("ep06")
            return
        if args.ui:
            gen_ui_badges_ep06()
            return
        copy_reused_assets("ep06")
        todo = args.only or (spec["priority"] if args.priority else list(spec["scenes"].keys()))
        for name in todo:
            fn = spec["scenes"].get(name)
            if fn is None:
                print(f"  !! unknown scene: {name}")
                continue
            cv = S6.new_canvas()
            fn(cv)
            img = cv.render()
            img = ui.harmonize(img)
            p = save(img, out_dir / f"{name}.png")
            print(f"  scene {p.name} {img.size}")
        if not args.only and not args.priority:
            gen_ui_badges_ep06()
            gen_next_episode_card()
            gen_preview_generic("ep06", bg="bg_azuchi_castle")
        return

    if args.ep == "ep05":
        spec = EP_SCENES["ep05"]
        out_dir = spec["dir"] / "scenes"
        if args.sheet:
            gen_contact_sheet("/tmp/ajh_art/sheet_ep05.png", ep="ep05")
            return
        if args.preview:
            gen_preview_generic("ep05")
            return
        if args.ui:
            gen_ui_badges_ep05()
            return
        copy_reused_assets("ep05")
        todo = args.only or (spec["priority"] if args.priority else list(spec["scenes"].keys()))
        for name in todo:
            fn = spec["scenes"].get(name)
            if fn is None:
                print(f"  !! unknown scene: {name}")
                continue
            cv = S5.new_canvas()
            fn(cv)
            img = cv.render()
            img = ui.harmonize(img)
            p = save(img, out_dir / f"{name}.png")
            print(f"  scene {p.name} {img.size}")
        if not args.only and not args.priority:
            gen_ui_badges_ep05()
            gen_next_episode_card()
            gen_preview_generic("ep05", bg="bg_muromachi_kinkaku")
        return

    if args.ep == "ep04":
        spec = EP_SCENES["ep04"]
        out_dir = spec["dir"] / "scenes"
        if args.sheet:
            gen_contact_sheet("/tmp/ajh_art/sheet_ep04.png", ep="ep04")
            return
        if args.preview:
            gen_preview_generic("ep04")
            return
        if args.ui:
            gen_ui_badges_ep04()
            return
        copy_reused_assets("ep04")
        todo = args.only or (spec["priority"] if args.priority else list(spec["scenes"].keys()))
        for name in todo:
            fn = spec["scenes"].get(name)
            if fn is None:
                print(f"  !! unknown scene: {name}")
                continue
            cv = S4.new_canvas()
            fn(cv)
            img = cv.render()
            img = ui.harmonize(img)
            p = save(img, out_dir / f"{name}.png")
            print(f"  scene {p.name} {img.size}")
        if not args.only and not args.priority:
            gen_ui_badges_ep04()
            gen_next_episode_card()
            gen_preview_generic("ep04", bg="bg_kamakura_shogunate")
        return

    if args.ep == "ep03":
        spec = EP_SCENES["ep03"]
        out_dir = spec["dir"] / "scenes"
        if args.sheet:
            gen_contact_sheet("/tmp/ajh_art/sheet_ep03.png", ep="ep03")
            return
        if args.preview:
            gen_preview_ep03()
            return
        if args.ui:
            gen_ui_badges_ep03()
            return
        copy_reused_assets("ep03")
        todo = args.only or (spec["priority"] if args.priority else list(spec["scenes"].keys()))
        for name in todo:
            fn = spec["scenes"].get(name)
            if fn is None:
                print(f"  !! unknown scene: {name}")
                continue
            cv = S3.new_canvas()
            fn(cv)
            img = cv.render()
            img = ui.harmonize(img)
            p = save(img, out_dir / f"{name}.png")
            print(f"  scene {p.name} {img.size}")
        if not args.only and not args.priority:
            gen_ui_badges_ep03()
            gen_next_episode_card()
            gen_preview_ep03(bg="bg_heian_mansion")
        return

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
            img = ui.harmonize(img)
            p = save(img, out_dir / f"{name}.png")
            print(f"  scene {p.name} {img.size}")
        if not args.only and not args.priority:
            gen_ui_badges_ep02()
            gen_next_episode_card()
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
        img = ui.harmonize(img)  # T10: 新キャラの彩度に合わせた色調統一
        p = save(img, SCENE_DIR / f"{name}.png")
        print(f"  scene {p.name} {img.size}")
    if not args.only and not args.priority:
        gen_characters()
        gen_props()
        gen_ui_badges()
        gen_next_episode_card()
        gen_preview()


if __name__ == "__main__":
    main()

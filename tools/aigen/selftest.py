#!/usr/bin/env python3
"""tools/aigen のオフライン動作確認 (API クレジット不要).

  uv run python tools/aigen/cli.py selftest
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR))

import config as C  # noqa: E402
import ledger as L  # noqa: E402
import pipeline as P  # noqa: E402
import storyboard as SB  # noqa: E402
import cli  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    mark = "OK " if cond else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def t_config():
    print("config:")
    cfg = C.load_config()
    check("既定値の読み込み", cfg["monthly_budget_usd"] == 10.0)
    check("モデルID設定", all(k in cfg["models"] for k in
                             ("text", "image", "video", "video_test")))
    tmp = Path(tempfile.mkdtemp()) / "override.json"
    tmp.write_text(json.dumps({"monthly_budget_usd": 3.0,
                               "models": {"image": "test-model"}}))
    cfg2 = C.load_config(tmp)
    check("config.json による上書き", cfg2["monthly_budget_usd"] == 3.0
          and cfg2["models"]["image"] == "test-model"
          and cfg2["models"]["text"] == cfg["models"]["text"])


def t_costs():
    print("見積もり:")
    cfg = C.load_config()
    check("画像 1K×2枚", abs(L.est_image(cfg, "1K", 2) - 0.04) < 1e-9)
    check("画像 4K×1枚", abs(L.est_image(cfg, "4K") - 0.12) < 1e-9)
    check("動画 8秒 1080p", abs(L.est_video(cfg, 8) - 3.20) < 1e-9)
    check("動画 8秒 4k は倍額", abs(L.est_video(cfg, 8, "4k") - 6.40) < 1e-9)
    check("動画 8秒 音声なしは同じ(倍率1.0)", abs(L.est_video(cfg, 8, audio=False) - 3.20) < 1e-9)
    try:
        L.est_image(cfg, "8K")
        check("不正サイズはエラー", False)
    except ValueError:
        check("不正サイズはエラー", True)


def t_ledger():
    print("台帳/予算ガード:")
    cfg = C.load_config()
    with tempfile.TemporaryDirectory() as td:
        led = L.Ledger(cfg, path=Path(td) / "usage.json")
        check("初期残高=予算", abs(led.remaining() - 10.0) < 1e-9)
        led.record(op="image", model="m", est_usd=0.02, note="t1")
        led.record(op="video", model="m", est_usd=3.2, note="t2")
        check("消費合計", abs(led.month_spend() - 3.22) < 1e-9)
        check("残高", abs(led.remaining() - 6.78) < 1e-9)
        check("内訳", abs(led.by_operation()["video"] - 3.2) < 1e-9)
        # 予算超過 → BudgetError
        try:
            led.check(6.8, "動画 13.5秒", force=False)
            check("超過で拒否", False)
        except L.BudgetError:
            check("超過で拒否", True)
        check("force なら通る", abs(led.check(6.8, force=True) - 6.78) < 1e-9)
        check("残り以内なら通る", abs(led.check(6.78, "ぎり") - 6.78) < 1e-9)
        # 過去月のエントリは当月に数えない
        led.data["entries"].append(
            {"ts": "2000-01-01T00:00:00+09:00", "op": "video", "model": "m",
             "est_usd": 100.0, "note": "past", "files": []})
        check("過去月は当月に含めない", abs(led.month_spend() - 3.22) < 1e-9)
        check("月指定集計", led.month_spend("2000-01") == 100.0)
        s = led.render_summary()
        check("サマリ生成", "残り" in s and "画像 4K" in s)
        # 再読込で永続化確認
        led2 = L.Ledger(cfg, path=Path(td) / "usage.json")
        check("永続化", abs(led2.month_spend() - 3.22) < 1e-9)


def t_storyboard():
    print("storyboard (script.json 連携):")
    # 実リポジトリは常に進行中のため、fixture ep を一時ディレクトリで検証する
    import storyboard as SB
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        scenes = root / "assets" / "epT" / "scenes"
        scenes.mkdir(parents=True)
        (scenes / "bg_old.png").write_bytes(b"png")
        epdir = root / "content" / "episodes" / "epT"
        epdir.mkdir(parents=True)
        script = {"scenes": [
            {"id": "s01", "section": "opening",
             "visual": {"background": "bg_old"}, "beats": []},
            {"id": "s02", "section": "story",
             "visual": {"background": "bg_new1"}, "beats": []},
            {"id": "s03", "section": "story",
             "visual": {"background": "bg_new1"}, "beats": []},
            {"id": "s04", "section": "story",
             "visual": {"background": "bg_new2"}, "beats": []},
        ]}
        (epdir / "script.json").write_text(json.dumps(script), encoding="utf-8")
        orig = SB.repo_root
        SB.repo_root = lambda: root
        try:
            rows = SB.scene_rows("epT")
            check("scene_rows が script を読む", len(rows) == 4)
            uniq = SB.unique_new_backgrounds("epT")
            check("未実装のみ・初出順・ユニーク",
                  [r["bg"] for r in uniq] == ["bg_new1", "bg_new2"],
                  f"got {[r['bg'] for r in uniq]}")
            check("reused マークは旧背景のみ対象外",
                  all(not r["reused"] for r in uniq))
            uniq_all = SB.unique_new_backgrounds("epT", include_reused=True)
            check("--include-reused は既存も含む",
                  [r["bg"] for r in uniq_all] == ["bg_old", "bg_new1", "bg_new2"])
        finally:
            SB.repo_root = orig
    fb = SB.fallback_prompt_en("bg_heian_capital")
    check("フォールバック プロンプト", "heian capital" in fb and "no text" in fb)
    # 文脈構築は合成行で検証 (実データの状態に依存しない)
    row0 = {"scene_id": "s02", "section": "story", "bg": "bg_heian_capital",
            "beats_text": "平安京が始まったのだ!", "characters": []}
    ctx = SB.build_scene_prompt_context(row0, "平安テスト")
    check("文脈にセリフを含む", row0["beats_text"][:8] in ctx)


def t_prompts():
    print("システム指示:")
    cfg = C.load_config()
    img_si = P.image_system_instruction(cfg)
    vid_si = P.video_system_instruction(cfg)
    check("画像SI: 文字禁止", "no text" in img_si and "watermarks" in img_si)
    check("画像SI: キャラ禁止", "NO people" in img_si)
    check("画像SI: パレット反映", "#2b4a8b" in img_si)
    check("画像SI: 16:9", "16:9" in img_si)
    check("動画SI: 開始フレーム前提", "STARTS from the provided still frame" in vid_si)
    check("動画SI: 文字禁止", "No on-screen text" in vid_si)


def t_episode():
    print("episode (動画パイプライン統合):")
    import episode as EP
    script = {
        "title": "テスト話",
        "scenes": [
            {"id": "s01", "visual": {"background": "bg_a",
                                     "camera": {"motion": "kenburns_in"}}},
            {"id": "s02", "visual": {"background": "bg_b",
                                     "ai": {"image": {"hint": "夕暮れ", "variants": 3}}}},
            {"id": "s03", "visual": {"background": "bg_c",
                                     "ai": {"video": {"prompt": "前進", "seconds": 6,
                                                      "resolution": "1080p",
                                                      "audio": False}}}},
            {"id": "s04", "visual": {"background": "bg_d",
                                     "ai": {"image": {"hint": "夜", "variants": 1},
                                            "video": {"prompt": "pan", "seconds": 8}}}},
        ],
    }
    rows = EP.ai_scenes(script)
    check("ai 指定シーン抽出", [r["scene"]["id"] for r in rows] == ["s02", "s03", "s04"])
    check("image/video 両持ちらら抽出", rows[-1]["image"] and rows[-1]["video"])

    cfg = C.load_config()
    with tempfile.TemporaryDirectory() as td:
        led = L.Ledger(cfg, path=Path(td) / "usage.json")
        plan = EP.plan_episode(cfg, led, "epT", script, variants=2)
        check("plan: 画像2行", len(plan["images"]) == 2)
        check("plan: クリップ2行", len(plan["clips"]) == 2)
        exp_img = L.est_image(cfg, "1K", 3) + L.est_image(cfg, "1K", 1)
        exp_vid = L.est_video(cfg, 6) + L.est_video(cfg, 8)
        check("plan: 費用合計", abs(plan["est_total"] - round(
            exp_img + exp_vid + plan["est_text"], 4)) < 1e-9)
        check("plan: 残高は未消費", plan["remaining"] == 10.0
              and led.month_spend() == 0.0)
        p2 = EP.plan_episode(cfg, led, "epT", script, stages=("clips",))
        check("stages=clips は画像0行", p2["images"] == [] and len(p2["clips"]) == 2)
        p3 = EP.plan_episode(cfg, led, "epT", script, only=["s03"])
        check("only=s03 限定", len(p3["images"]) == 0 and len(p3["clips"]) == 1)
        EP.print_plan(plan, cfg)  # smoke

        # manifest 往復
        mp = EP.write_manifest(cfg, "epT", {"s03": "s03_bg_c.mp4"},
                               path=Path(td) / "manifest.json")
        data = json.loads(mp.read_text(encoding="utf-8"))
        check("manifest clips キー", data["clips"] == {"s03": "s03_bg_c.mp4"})
        back = EP.load_manifest(cfg, "epT")  # repo側は別パスなので内容のみ確認用
        check("manifest_path 規約", EP.manifest_path(cfg, "epT").name ==
              "manifest.json" and "epT_ai" in str(EP.manifest_path(cfg, "epT")))
    # クリップファイル名の規約
    fn = EP.clip_filename({"id": "s02", "visual": {"background": "bg_b"}}, {})
    check("clip ファイル名 <sid>_<bg>.mp4", fn == "s02_bg_b.mp4")


def t_cli():
    print("CLI (dry-run は API 不要):")
    p = cli.build_parser()
    for argv in (
        ["models"],
        ["prompt", "夕暮れの平安京", "--mode", "image", "--dry-run"],
        ["image", "夕暮れの平安京の大路", "--ep", "ep03", "--name", "bg_heian_capital",
         "--dry-run"],
        ["image", "x", "--tier", "final", "--prompt-file", "/tmp/p.txt", "--dry-run"],
        ["video", "/tmp/f.png", "ゆっくり前進", "--ep", "ep03", "--dry-run"],
        ["storyboard", "--ep", "ep03", "--plan", "-v"],
        ["episode", "--ep", "ep03", "--plan"],
        ["episode", "--ep", "ep03", "--images", "--only", "s02"],
        ["budget"],
        ["adopt", "x.png", "--ep", "ep03", "--bg", "bg_heian_capital"],
    ):
        try:
            a = p.parse_args(argv)
            check(f"parse {' '.join(argv[:2])}", True)
        except SystemExit:
            check(f"parse {' '.join(argv[:2])}", False)
    # dry-run 実行 (実ファイル/実 script.json に対して)
    tmp = Path(tempfile.mkdtemp())
    fake_img = tmp / "bg_heian_capital_1K_v1.png"
    fake_img.write_bytes(b"\x89PNG fake")
    check("image --dry-run", cli.main(["image", "夕暮れの平安京", "--ep", "ep03",
                                       "--dry-run"]) == 0)
    check("video --dry-run", cli.main(["video", str(fake_img), "前進",
                                       "--ep", "ep03", "--dry-run"]) == 0)
    check("storyboard --plan", cli.main(["storyboard", "--ep", "ep03",
                                         "--plan"]) == 0)
    check("budget", cli.main(["budget"]) == 0)
    check("models (offline)", cli.main(["models"]) == 0)
    # 存在しない画像の video は契約違反として弾く
    check("video は画像必須", cli.main(["video", str(tmp / "none.png"), "x",
                                       "--dry-run"]) == cli.EXIT_USAGE)


def run(verbose: bool = False) -> int:
    print("== tools/aigen selftest (オフライン) ==")
    t_config()
    t_costs()
    t_ledger()
    t_storyboard()
    t_prompts()
    t_episode()
    t_cli()
    print("=" * 34)
    if FAILS:
        print(f"結果: {len(FAILS)} 失敗 → {FAILS}")
        return 1
    print("結果: 全テスト合格 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(run(verbose="-v" in sys.argv))

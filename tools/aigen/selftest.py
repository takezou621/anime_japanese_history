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
    rows = SB.scene_rows("ep03")
    check("ep03 シーン数=19", len(rows) == 19, f"got {len(rows)}")
    uniq = SB.unique_new_backgrounds("ep03")
    bgs = [r["bg"] for r in uniq]
    check("新規平安背景 12種", len(uniq) == 12 and
          all(b.startswith("bg_heian_") for b in bgs),
          f"got {len(uniq)}: {bgs}")
    check("既存背景 (bg_school_lab 等) をスキップ",
          "bg_school_lab" not in bgs and "bg_timeline" not in bgs)
    uniq_all = SB.unique_new_backgrounds("ep03", include_reused=True)
    check("--include-reused で既存も含む", "bg_timeline" in
          [r["bg"] for r in uniq_all])
    fb = SB.fallback_prompt_en("bg_heian_capital")
    check("フォールバック プロンプト", "heian capital" in fb and "no text" in fb)
    row0 = [r for r in uniq if r["bg"] == "bg_heian_capital"][0]
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
    t_cli()
    print("=" * 34)
    if FAILS:
        print(f"結果: {len(FAILS)} 失敗 → {FAILS}")
        return 1
    print("結果: 全テスト合格 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(run(verbose="-v" in sys.argv))

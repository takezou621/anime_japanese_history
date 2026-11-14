#!/usr/bin/env python3
"""AI 生成 CLI — 月 $10 予算ガード付き 2段階パイプライン.

戦略 (Google AI Pro 月$10 クレジット最適化):
  1. プロンプト設計  : 日本語ラフ → 英語プロンプト (テキストモデル, 極小コスト)
  2. イラスト draft  : 1K で構図を当てる (複数バリアント, 安い)
  3. イラスト final  : 当たり1枚だけ 4K で再生成
  4. 動画化          : 採用画像を開始フレームとして Veo に渡す (テキストから直接作らない)

使い方:
  uv run --with google-genai python tools/aigen/cli.py models
  uv run --with google-genai python tools/aigen/cli.py budget
  uv run --with google-genai python tools/aigen/cli.py storyboard --ep ep03 --plan
  uv run --with google-genai python tools/aigen/cli.py image "夕暮れの平安京大路" --ep ep03 --name bg_heian_capital
  uv run --with google-genai python tools/aigen/cli.py image "..." --tier final --same-prompt assets/ep03/ai_drafts/prompts/bg_heian_capital.txt
  uv run --with google-genai python tools/aigen/cli.py video assets/ep03/ai_drafts/bg_heian_capital_1K_v1.png "ゆっくり前進、屋台の提灯が揺れる" --ep ep03 --yes
  uv run --with pillow python tools/aigen/cli.py adopt assets/ep03/ai_drafts/xxx.png --ep ep03 --bg bg_heian_capital
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
ROOT = DIR.parent.parent
sys.path.insert(0, str(DIR))

import config as C  # noqa: E402
import ledger as L  # noqa: E402
import pipeline as P  # noqa: E402
import storyboard as SB  # noqa: E402

EXIT_USAGE = 2
EXIT_BUDGET = 3
EXIT_CREDS = 4
EXIT_DEPS = 5


# ---------------------------------------------------------------- 共通

def _money(usd: float) -> str:
    return f"${usd:.2f}"


def _ask_confirm(est_usd: float, what: str, yes: bool) -> bool:
    if yes:
        return True
    import sys
    if sys.stdin.isatty():
        ans = input(f"{what} の見積もりは {_money(est_usd)} です。実行しますか? [y/N] ")
        return ans.strip().lower() in {"y", "yes"}
    print(f"[中止] {_money(est_usd)} かかる操作には --yes が必要です: {what}")
    return False


def _expand_with_budget(client, cfg, led, raw, mode, *, dry: bool,
                        prompt_file: Path | None = None):
    """プロンプト拡張 (--same-prompt 指定時はスキップ)。見積もりはテキスト1回分。"""
    if prompt_file:
        text = Path(prompt_file).read_text(encoding="utf-8").strip()
        print(f"[Prompt] (file指定, 拡張スキップ)\n{text}\n")
        return text, 0.0
    if dry:
        print(f"[dry-run] プロンプト拡張をスキップ (raw を使用): {raw!r}")
        return raw, 0.0
    est = L.est_text(cfg, 1)
    led.check(est, "プロンプト拡張")
    text = P.expand_prompt(client, cfg, raw, mode)
    led.record(op="text", model=cfg["models"]["text"], est_usd=est,
               note=f"expand {mode}: {raw[:40]}...")
    print(f"[Prompt]\n{text}\n")
    return text, est


def _resolve_backend(cfg, wanted: str | None):
    try:
        client = P.make_client(cfg, backend=wanted)
        return client, None
    except P.NoCredentials as err:
        return None, err


# ---------------------------------------------------------------- サブコマンド

def cmd_models(args, cfg, led):
    rows = [
        ("text (プロンプト設計)", cfg["models"]["text"], _money(L.est_text(cfg)) + "/回"),
        ("image (イラスト)", cfg["models"]["image"],
         " / ".join(f"{k} {_money(v)}" for k, v in cfg["pricing_usd"]["image"].items()) + "/枚"),
        ("video (本番 i2v)", cfg["models"]["video"],
         _money(cfg["pricing_usd"]["video_per_second_1080p"]) + "/秒 (1080p)"),
        ("video_test (任意)", cfg["models"]["video_test"],
         _money(L.est_video_test(cfg)) + "/回"),
    ]
    print("設定中のモデル (config.json で変更可。実行前に実在IDを確認すること):\n")
    for role, mid, price in rows:
        print(f"  {role:<22} {mid:<28} {price}")
    print(f"\n月間予算: {_money(cfg['monthly_budget_usd'])}  /  image_api: {cfg['models']['image_api']}")
    if not args.remote:
        print("実在モデル一覧を見るには: ... cli.py models --remote (要 credentials)")
        return 0
    client, err = _resolve_backend(cfg, args.backend)
    if err:
        print(f"[credentials 必要] {err}")
        return EXIT_CREDS
    try:
        names = P.list_remote_models(client)
    except RuntimeError as err:
        print(f"[error] {err}")
        return 1
    print(f"\n実在モデル ({len(names)}件) — config.json の ID と突き合わせてください:")
    for n in names:
        print(f"  {n}")
    return 0


def cmd_prompt(args, cfg, led):
    client, err = _resolve_backend(cfg, None)
    if err and not args.dry_run:
        print(f"[credentials 必要] {err}")
        return EXIT_CREDS
    if args.dry_run:
        print(P.image_system_instruction(cfg) if args.mode == "image"
              else P.video_system_instruction(cfg))
        print(f"\n[dry-run] 変換対象: {args.raw}")
        return 0
    text, _ = _expand_with_budget(client, cfg, led, args.raw, args.mode,
                                  dry=False, prompt_file=args.prompt_file)
    if args.save:
        Path(args.save).write_text(text + "\n", encoding="utf-8")
        print(f"保存: {args.save}")
    return 0


def cmd_image(args, cfg, led):
    size = cfg["image_tier"].get(args.tier, args.tier)
    variants = max(1, args.variants)
    est_img = L.est_image(cfg, size, variants)
    est = round(est_img + (0.0 if args.prompt_file else L.est_text(cfg)), 4)

    out_dir = Path(args.out).parent if args.out else C.drafts_dir(cfg, args.ep)
    name = args.name or ("img_" + hashlib.sha1(args.raw.encode()).hexdigest()[:8])
    if args.out:
        stem, ext = Path(args.out).stem, (Path(args.out).suffix or ".png")
    else:
        stem, ext = f"{name}_{size}", ".png"

    if args.dry_run:
        print(f"[dry-run] model={cfg['models']['image']} size={size} aspect="
              f"{cfg['style']['aspect_ratio']} variants={variants}")
        print(f"  prompt: {args.raw}")
        print(f"  出力先: {out_dir}/{stem}_v1..v{variants}{ext}")
        print(f"  見積もり: 画像 {variants}枚 × {_money(L.est_image(cfg, size))} "
              f"+ テキスト = {_money(est)} (残り {_money(led.remaining())})")
        return 0

    client, err = _resolve_backend(cfg, None)
    if err:
        print(f"[credentials 必要] {err}")
        return EXIT_CREDS

    try:
        led.check(est, f"画像生成 {variants}枚 ({size})", force=args.force)
    except L.BudgetError as err:
        print(f"[予算ガード] {err}")
        return EXIT_BUDGET
    if est_img >= 0.5 and not _ask_confirm(est, f"画像生成 {variants}枚 ({size})", args.yes):
        return EXIT_USAGE

    prompt, _ = _expand_with_budget(client, cfg, led, args.raw, "image", dry=False,
                                    prompt_file=args.prompt_file)
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for i in range(1, variants + 1):
        out_path = (out_dir / f"{stem}{ext}" if variants == 1
                    else out_dir / f"{stem}_v{i}{ext}")
        print(f"生成中 ({size}) {i}/{variants} → {out_path}")
        P.generate_image(client, cfg, prompt=prompt, size=size,
                         aspect=args.aspect, out_path=out_path)
        saved.append(str(out_path))
    led.record(op="image", model=cfg["models"]["image"], est_usd=est_img,
               note=f"tier={args.tier}({size}) {name}", files=saved,
               variants=variants)
    print(f"完了: {len(saved)}枚 / 見積 {_money(est_img)} / 残り {_money(led.remaining())}")
    return 0


def cmd_video(args, cfg, led):
    img = Path(args.image)
    if not img.exists():
        print(f"[error] 開始フレーム画像がありません: {img}")
        print("  先に image コマンドで採用画像を作ってください (2段階パイプライン)")
        return EXIT_USAGE
    v = cfg["video"]
    seconds = args.seconds if args.seconds is not None else v["duration_seconds"]
    resolution = args.resolution or v["resolution"]
    audio = not args.no_audio
    est = L.est_video(cfg, seconds, resolution, audio)
    what = f"動画 {seconds}秒 {resolution}{' 音声あり' if audio else ''}"

    out = Path(args.out) if args.out else \
        C.video_dir(cfg, args.ep) / f"{img.stem}_veo.mp4"

    if args.dry_run:
        print(f"[dry-run] model={cfg['models']['video']} i2v start={img}")
        print(f"  motion: {args.raw}")
        print(f"  出力先: {out}  見積もり: {_money(est)} (残り {_money(led.remaining())})")
        return 0

    client, err = _resolve_backend(cfg, args.backend)
    if err:
        print(f"[credentials 必要] {err}")
        return EXIT_CREDS

    try:
        led.check(est, what, force=args.force)
    except L.BudgetError as err:
        print(f"[予算ガード] {err}")
        return EXIT_BUDGET
    if est >= cfg["video"]["confirm_over_usd"] and not _ask_confirm(est, what, args.yes):
        return EXIT_USAGE

    prompt, _ = _expand_with_budget(client, cfg, led, args.raw, "video", dry=False,
                                    prompt_file=args.prompt_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"Veo に送信: start={img} → {out}")
    try:
        meta = P.generate_video(client, cfg, prompt=prompt, image_path=img,
                                out_path=out, seconds=seconds,
                                resolution=resolution, audio=audio)
    except TimeoutError as err:
        print(f"[error] {err} (課金は発生している可能性があります --budget で確認)")
        led.record(op="video_timeout", model=cfg["models"]["video"], est_usd=est,
                   note=str(err))
        return 1
    led.record(op="video", model=cfg["models"]["video"], est_usd=est,
               note=f"{seconds}s {resolution} audio={audio}", files=[meta["path"]])
    print(f"完了: {meta['path']} / 見積 {_money(est)} / 残り {_money(led.remaining())}")
    return 0


def cmd_storyboard(args, cfg, led):
    ep = args.ep
    title = SB.load_script(ep).get("title", ep)
    rows = SB.unique_new_backgrounds(ep, include_reused=args.include_reused)
    if args.only:
        want = set(args.only)
        rows = [r for r in rows if r["bg"] in want]
    variants = max(1, args.variants)
    size = cfg["image_tier"].get(args.tier, args.tier)
    n_img = len(rows) * variants
    est_img = L.est_image(cfg, size, n_img)
    est_text = 0.0 if args.dry_run else L.est_text(cfg, len(rows))

    print(f"ep: {ep} — {title}")
    print(f"対象背景: {len(rows)}種 × {variants}バリアント ({size})")
    for r in rows:
        tag = "[再利用]" if r["reused"] else "[新規]  "
        print(f"  {tag} {r['bg']:<20} scenes={','.join(r['scenes'])}")
    print(f"見積もり: 画像 {n_img}枚 = {_money(est_img)}, プロンプト設計 = "
          f"{_money(est_text)}, 合計 {_money(round(est_img + est_text, 4))} "
          f"(残り {_money(led.remaining())})\n")

    if args.plan or args.dry_run:
        for r in rows:
            cached = SB.prompt_cache_path(cfg, ep, r["bg"])
            src = "cache" if cached.exists() else \
                ("text-model (実行時に生成)" if not args.dry_run else "fallback(dry-run)")
            print(f"— {r['bg']} ({src})")
            if args.verbose:
                text, _ = SB.get_scene_prompt(None, cfg, ep, r, title)
                print(f"  {text}")
        return 0

    client, err = _resolve_backend(cfg, None)
    if err:
        print(f"[credentials 必要] {err}")
        return EXIT_CREDS
    try:
        led.check(round(est_img + est_text, 4), f"storyboard {ep} ({n_img}枚)",
                  force=args.force)
    except L.BudgetError as err:
        print(f"[予算ガード] {err}")
        return EXIT_BUDGET
    if not _ask_confirm(round(est_img + est_text, 4),
                        f"storyboard {ep} 画像{n_img}枚", args.yes):
        return EXIT_USAGE

    out_dir = C.drafts_dir(cfg, ep)
    out_dir.mkdir(parents=True, exist_ok=True)
    for r in rows:
        prompt, _ = SB.get_scene_prompt(client, cfg, ep, r, title)
        print(f"— {r['bg']} ×{variants}")
        for i in range(1, variants + 1):
            out_path = out_dir / f"{r['bg']}_{size}_v{i}.png"
            P.generate_image(client, cfg, prompt=prompt, size=size,
                             aspect=cfg["style"]["aspect_ratio"], out_path=out_path)
            led.record(op="image", model=cfg["models"]["image"],
                       est_usd=L.est_image(cfg, size),
                       note=f"storyboard {ep} {r['bg']} v{i}", files=[str(out_path)])
    html = out_dir / "storyboard.html"
    imgs = sorted(p.name for p in out_dir.glob(f"*_{size}_v*.png"))
    html.write_text(
        "<html><head><meta charset='utf-8'><title>storyboard %s</title>"
        "<style>body{background:#1c1f26;color:#fff;font-family:sans-serif}"
        "img{width:420px;margin:6px;border-radius:8px}"
        "figure{display:inline-block;margin:4px;text-align:center}</style></head>"
        "<body><h1>%s — AI drafts (%s)</h1>" % (ep, title, size)
        + "".join(f"<figure><img src='{n}'><br><small>{n}</small></figure>"
                  for n in imgs)
        + "</body></html>", encoding="utf-8")
    print(f"\n完了: {len(imgs)}枚 → {out_dir}\n確認用ページ: {html}")
    print("当たりを決めたら final 化:  ... image ... --tier final --same-prompt "
          f"{out_dir}/prompts/{rows[0]['bg']}.txt")
    return 0


def cmd_episode(args, cfg, led):
    """script.json の visual.ai → 画像 draft + Veo クリップ (+manifest) を一括生成。

    生成されたクリップは video/epNN_ai/manifest.json 経由で assemble.py が
    自動使用し、無い/失敗したシーンは従来 kenburns にフォールバックする。
    """
    import episode as EP
    stages = tuple(s for s, flag in (("images", args.images),
                                     ("clips", args.clips)) if flag) or \
        ("images", "clips")
    script = SB.load_script(args.ep)
    plan = EP.plan_episode(cfg, led, args.ep, script, variants=args.variants,
                           only=args.only, stages=stages)
    EP.print_plan(plan, cfg)
    if args.plan or args.dry_run:
        return 0
    if not (plan["images"] or plan["clips"]):
        return 0
    client, err = _resolve_backend(cfg, None)
    if err:
        print(f"[credentials 必要] {err}")
        return EXIT_CREDS
    try:
        led.check(plan["est_total"], f"episode {args.ep} AI生成",
                  force=args.force)
    except L.BudgetError as err:
        print(f"[予算ガード] {err}")
        return EXIT_BUDGET
    if plan["est_total"] >= 0.5 and not _ask_confirm(
            plan["est_total"], f"episode {args.ep} AI生成", args.yes):
        return EXIT_USAGE
    n_img = n_clip = 0
    if "images" in stages and plan["images"]:
        n_img = len(EP.run_images(client, cfg, led, plan))
    if "clips" in stages and plan["clips"]:
        n_clip = len(EP.run_clips(client, cfg, led, plan))
    print(f"\n完了: 画像 {n_img} / クリップ {n_clip}")
    print(f"次: 動画生成 → uv run --with pillow python tools/editor/assemble.py "
          f"--episode {args.ep}")
    return 0


def cmd_budget(args, cfg, led):
    print(led.render_summary(args.month))
    return 0


def cmd_adopt(args, cfg, led):
    """当たり draft を 1920×1080 に整えて editor 契約の scenes/ へ採用する。"""
    try:
        from PIL import Image  # noqa
    except ImportError:
        print("Pillow が必要です: uv run --with pillow python tools/aigen/cli.py adopt ...")
        return EXIT_DEPS
    from PIL import Image as PILImage
    src = Path(args.file)
    if not src.exists():
        print(f"[error] ファイルがありません: {src}")
        return EXIT_USAGE
    dst_dir = ROOT / "assets" / args.ep / "scenes"
    dst = dst_dir / f"{args.bg}.png"
    if dst.exists() and not args.overwrite:
        print(f"[中止] 既存: {dst} (--overwrite で上書き)")
        return EXIT_USAGE
    dst_dir.mkdir(parents=True, exist_ok=True)
    im = PILImage.open(src).convert("RGB")
    tw, th = 1920, 1080
    scale = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)),
                   PILImage.LANCZOS)
    x = (im.width - tw) // 2
    y = (im.height - th) // 2
    im.crop((x, y, x + tw, y + th)).save(dst, "PNG")
    print(f"採用: {src} → {dst} (1920×1080, editor 契約どおり)")
    print("以降の assemble.py は自動でこの背景を使います (code-drawn と差し替え可)")
    return 0


def cmd_selftest(args, cfg, led):
    import selftest
    return selftest.run(verbose=args.verbose)


# ---------------------------------------------------------------- パーサ

def build_parser() -> argparse.ArgumentParser:
    # サブコマンドの後ろにも置けるよう、同一フラグを parent でも受ける
    # (SUPPRESS: 未指定時にサブパーサが既定値で上書きしない)
    common = argparse.ArgumentParser(add_help=False)
    for flag, kw in (
        ("--config", dict(help="config.json パス (既定: tools/aigen/config.json)")),
        ("--force", dict(action="store_true", help="予算ガードを無視して強行")),
        ("--yes", dict(action="store_true", help="確認を省略")),
        ("--dry-run", dict(action="store_true",
                           help="API を叩かず計画と見積もりだけ表示")),
    ):
        common.add_argument(flag, default=argparse.SUPPRESS, **kw)

    ap = argparse.ArgumentParser(
        prog="cli.py",
        description="AI 生成 CLI (画像2段階 + i2v動画, 月$10 予算ガード付き)")
    ap.add_argument("--config", help="config.json パス (既定: tools/aigen/config.json)")
    ap.add_argument("--force", action="store_true", help="予算ガードを無視して強行")
    ap.add_argument("--yes", "-y", action="store_true", help="確認を省略")
    ap.add_argument("--dry-run", action="store_true",
                    help="API を叩かず計画と見積もりだけ表示")
    sub = ap.add_subparsers(dest="command", required=True)

    def add(name, help_, func):
        p = sub.add_parser(name, help=help_, parents=[common])
        p.set_defaults(func=func)
        return p

    p = add("models", "設定モデル/単価の表示 (--remote で実在一覧)", cmd_models)
    p.add_argument("--remote", action="store_true")
    p.add_argument("--backend", choices=["gemini_api", "vertexai"])

    p = add("prompt", "日本語ラフ → 英語プロンプト変換のみ", cmd_prompt)
    p.add_argument("raw", help="日本語の指示")
    p.add_argument("--mode", choices=["image", "video"], default="image")
    p.add_argument("--prompt-file", help="既存英プロンプトファイル表示用 (省略可)")
    p.add_argument("--save", help="結果の保存先")

    p = add("image", "イラスト生成 (draft=1K → 採用後 final=4K)", cmd_image)
    p.add_argument("raw", help="イラストの指示 (日本語OK)")
    p.add_argument("--ep", default="ep01", help="エピソード (出力先の決定に使用)")
    p.add_argument("--name", help="出力ファイル名の基底 (既定: ハッシュ)")
    p.add_argument("-o", "--out", help="出力パス (指定時は --ep を無視)")
    p.add_argument("--tier", choices=["draft", "final"], default="draft",
                   help="draft=1K / final=4K (既定: draft)")
    p.add_argument("--variants", type=int, default=1, help="生成枚数 (当たり選び用)")
    p.add_argument("--aspect", help="アスペクト比 (既定: config の 16:9)")
    p.add_argument("--prompt-file",
                   help="拡張済み英プロンプトファイル (final 再生成時に使う)")

    p = add("video", "採用画像を開始フレームにして Veo で動画化", cmd_video)
    p.add_argument("image", help="開始フレーム画像パス")
    p.add_argument("raw", help="動き・カメラワークの指示 (日本語OK)")
    p.add_argument("--ep", default="ep01")
    p.add_argument("-o", "--out", help="出力 mp4 パス")
    p.add_argument("--seconds", type=float, help="尺 (既定: config)")
    p.add_argument("--resolution", choices=["1080p", "4k"], help="既定: 1080p")
    p.add_argument("--no-audio", action="store_true", help="音声なし (安い)")
    p.add_argument("--backend", choices=["gemini_api", "vertexai"],
                   help="Veo の接続先 (既定: 自動)")
    p.add_argument("--prompt-file", help="拡張済み motion プロンプトファイル")

    p = add("storyboard", "script.json の新規背景を draft 一括生成", cmd_storyboard)
    p.add_argument("--ep", required=True, help="エピソード (ep03 など)")
    p.add_argument("--variants", type=int, default=2, help="背景ごとのバリアント数")
    p.add_argument("--tier", choices=["draft", "final"], default="draft")
    p.add_argument("--only", nargs="*", help="この背景名だけ (例: bg_heian_capital)")
    p.add_argument("--include-reused", action="store_true",
                   help="既存 (code-drawn) 背景も対象にする")
    p.add_argument("--plan", action="store_true", help="生成せず計画と費用のみ")
    p.add_argument("-v", "--verbose", action="store_true", help="プロンプト本文も表示")

    p = add("episode", "script.json の visual.ai を一括生成 (画像+Veoクリップ)",
            cmd_episode)
    p.add_argument("--ep", required=True, help="エピソード (ep03 など)")
    p.add_argument("--images", action="store_true", help="画像 draft を生成")
    p.add_argument("--clips", action="store_true",
                   help="Veo i2v クリップを生成 (manifest 経由で assemble が使用)")
    p.add_argument("--variants", type=int, default=2,
                   help="画像バリアント数 (visual.ai.image.variants を既定)")
    p.add_argument("--only", nargs="*", help="このシーンIDだけ (s02 s06 ...)")
    p.add_argument("--plan", action="store_true", help="生成せず計画と費用のみ")

    p = add("budget", "月次予算の残高確認", cmd_budget)
    p.add_argument("--month", help="YYYY-MM (既定: 当月)")

    p = add("adopt", "当たり draft を 1920×1080 で scenes/ に採用", cmd_adopt)
    p.add_argument("file", help="draft PNG")
    p.add_argument("--ep", required=True)
    p.add_argument("--bg", required=True, help="採用先の背景名 (bg_heian_capital など)")
    p.add_argument("--overwrite", action="store_true")

    p = add("selftest", "オフライン動作確認 (API 不要)", cmd_selftest)
    p.add_argument("-v", "--verbose", action="store_true")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    cfg = C.load_config(Path(args.config) if args.config else None)
    led = L.Ledger(cfg)
    try:
        return args.func(args, cfg, led)
    except L.BudgetError as err:
        print(f"[予算ガード] {err}")
        return EXIT_BUDGET
    except P.NoCredentials as err:
        print(f"[credentials] {err}")
        return EXIT_CREDS


if __name__ == "__main__":
    sys.exit(main())

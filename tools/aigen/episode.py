#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""episode.py — script.json の visual.ai を動画パイプラインへ一括供給する.

契約 (docs/02_DESIGN.md §2.1, 追記のみ・後方互換):
  script.json のシーンに任意で
    "visual": {
      ...,
      "ai": {
        "image": {"hint": "夕暮れ、朱雀大路...", "variants": 2, "tier": "draft"},
        "video": {"prompt": "ゆっくり前進、群衆、夕光", "seconds": 8,
                  "resolution": "1080p", "audio": false}
      }
    }
  を足すと、このドライバが:
  - 画像: ai_drafts に draft (選定後 adopt で scenes/ 採用)
  - 動画: video/epNN_ai/<sid>_<bg>.mp4 を Veo i2v で生成し
          video/epNN_ai/manifest.json ({"clips": {"<sid>": "<file>"}}) を更新
          → assemble.py が manifest を読んで自動でセグメントに使用
            (クリップ無し/失敗シーンは従来 kenburns にフォールバック)
"""
from __future__ import annotations

import json
from pathlib import Path

import ledger as L
import storyboard as SB

MANIFEST_NAME = "manifest.json"


# ---------------------------------------------------------------------------
# script.json 解析

def ai_scenes(script: dict) -> list[dict]:
    """visual.ai を持つシーンだけ抽出 → [{scene, image, video}]"""
    out = []
    for sc in script.get("scenes", []):
        ai = (sc.get("visual", {}) or {}).get("ai") or {}
        img = ai.get("image") or {}
        vid = ai.get("video") or {}
        if img or vid:
            out.append({"scene": sc, "image": img or None,
                        "video": vid or None})
    return out


def clip_filename(scene: dict, video_cfg: dict) -> str:
    sid = scene.get("id", "s00")
    bg = (scene.get("visual", {}) or {}).get("background", "bg")
    ext = ".mp4"
    return f"{sid}_{bg}{ext}"


def clip_out_dir(cfg: dict, ep: str) -> Path:
    from config import video_dir
    return video_dir(cfg, ep)


# ---------------------------------------------------------------------------
# manifest (editor ai_segments.load_manifest と対になる書き込み)

def manifest_path(cfg: dict, ep: str) -> Path:
    return clip_out_dir(cfg, ep) / MANIFEST_NAME


def load_manifest(cfg: dict, ep: str) -> dict:
    p = manifest_path(cfg, ep)
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data.get("clips", data) if isinstance(data, dict) else {}


def write_manifest(cfg: dict, ep: str, clips: dict,
                   path: Path | None = None) -> Path:
    p = path or manifest_path(cfg, ep)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"_comment": "scene_id -> clip filename (assemble.py が使用)",
               "clips": clips}
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                 encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# 計画 (オフライン)

def plan_episode(cfg: dict, led: L.Ledger, ep: str, script: dict,
                 variants: int = 2, only: list[str] | None = None,
                 stages: tuple[str, ...] = ("images", "clips")) -> dict:
    """AI 対象シーンの一覧と費用見積もりを返す (API 呼び出し無し)。"""
    want = set(only or [])
    rows_img, rows_vid = [], []
    for r in ai_scenes(script):
        sc = r["scene"]
        sid = sc.get("id", "?")
        if want and sid not in want:
            continue
        vis = sc.get("visual", {}) or {}
        if "images" in stages and r["image"]:
            n = int(r["image"].get("variants", variants) or variants)
            tier = r["image"].get("tier", "draft")
            size = cfg["image_tier"].get(tier, tier)
            rows_img.append({"sid": sid, "bg": vis.get("background", ""),
                             "hint": r["image"].get("hint", ""),
                             "variants": n, "size": size,
                             "est": L.est_image(cfg, size, n)})
        if "clips" in stages and r["video"]:
            v = r["video"]
            sec = float(v.get("seconds", cfg["video"]["duration_seconds"]))
            res = v.get("resolution", cfg["video"]["resolution"])
            audio = bool(v.get("audio", cfg["video"]["generate_audio"]))
            # 開始フレーム: 明示 "frame" > 採用済み scenes/<bg>.png
            frame = v.get("frame") or ""
            rows_vid.append({"sid": sid, "bg": vis.get("background", ""),
                             "prompt": v.get("prompt", ""),
                             "seconds": sec, "resolution": res,
                             "audio": audio, "bg_image": frame,
                             "est": L.est_video(cfg, sec, res, audio)})
    est_text = L.est_text(cfg, len(rows_img) + len(rows_vid))
    est = round(sum(r["est"] for r in rows_img) +
                sum(r["est"] for r in rows_vid) + est_text, 4)
    return {"ep": ep, "title": script.get("title", ep),
            "images": rows_img, "clips": rows_vid,
            "est_text": est_text, "est_total": est,
            "remaining": led.remaining()}


def print_plan(plan: dict, cfg: dict) -> None:
    print(f"ep: {plan['ep']} — {plan['title']}")
    if not plan["images"] and not plan["clips"]:
        print("  visual.ai 指定シーンなし (既存パイプラインのまま)")
        return
    if plan["images"]:
        print(f"画像 ({len(plan['images'])}シーン):")
        for r in plan["images"]:
            print(f"  {r['sid']} {r['bg']:<20} {r['size']} ×{r['variants']} "
                  f"≈ ${r['est']:.2f}  hint: {r['hint'][:36]}")
    if plan["clips"]:
        print(f"AI クリップ ({len(plan['clips'])}シーン):")
        for r in plan["clips"]:
            print(f"  {r['sid']} {r['bg']:<20} {r['seconds']}s {r['resolution']}"
                  f"{' 音声' if r['audio'] else ''} ≈ ${r['est']:.2f}  "
                  f"prompt: {r['prompt'][:36]}")
    print(f"合計見積もり ${plan['est_total']:.2f} / 残り ${plan['remaining']:.2f} "
          f"(予算 ${cfg['monthly_budget_usd']:.2f})")


# ---------------------------------------------------------------------------
# 実行

def run_images(client, cfg: dict, led: L.Ledger, plan: dict) -> list[str]:
    """画像 stage: draft を ai_drafts へ出力し、adopt コマンドを案内する。"""
    from pipeline import generate_image
    from config import drafts_dir
    title = plan["title"]
    out_dir = drafts_dir(cfg, plan["ep"])
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for r in plan["images"]:
        row = {"scene_id": r["sid"], "section": "story", "bg": r["bg"],
               "beats_text": r["hint"], "characters": []}
        prompt, _ = SB.get_scene_prompt(client, cfg, plan["ep"], row, title)
        size = r["size"]
        for i in range(1, r["variants"] + 1):
            out_path = out_dir / f"{r['bg']}_{size}_v{i}.png"
            print(f"[ai:image] {r['sid']} {r['bg']} ({size}) v{i} → {out_path}")
            generate_image(client, cfg, prompt=prompt, size=size,
                           aspect=cfg["style"]["aspect_ratio"], out_path=out_path)
            led.record(op="image", model=cfg["models"]["image"],
                       est_usd=L.est_image(cfg, size),
                       note=f"episode {plan['ep']} {r['sid']} {r['bg']} v{i}",
                       files=[str(out_path)])
            saved.append(str(out_path))
        print(f"  採用時: uv run --with pillow python tools/aigen/cli.py adopt "
              f"{out_dir}/{r['bg']}_{size}_v1.png --ep {plan['ep']} --bg {r['bg']}")
    return saved


def run_clips(client, cfg: dict, led: L.Ledger, plan: dict) -> list[str]:
    """動画 stage: Veo i2v クリップ生成 + manifest.json 更新 (assemble が読む)。"""
    from pipeline import expand_prompt, generate_video
    from config import repo_root
    out_dir = clip_out_dir(cfg, plan["ep"])
    out_dir.mkdir(parents=True, exist_ok=True)
    clips = load_manifest(cfg, plan["ep"])
    made = []
    for r in plan["clips"]:
        fname = clip_filename({"id": r["sid"],
                               "visual": {"background": r["bg"]}}, {})
        out_path = out_dir / fname
        frame = r.get("bg_image") or ""
        frame_path = (repo_root() / frame) if frame and not Path(frame).is_absolute() \
            else Path(frame)
        if not frame_path.is_file():
            frame_path = repo_root() / "assets" / plan["ep"] / "scenes" / \
                f"{r['bg']}.png"
        if not frame_path.is_file():
            raise FileNotFoundError(
                f"開始フレームがありません: {frame_path}\n"
                "  背景を採用するか, visual.ai.video の \"frame\" でパスを指定")
        # 開始フレームは採用済み背景。motion 指示に文脈を渡す
        raw = (f"開始フレームは日本史アニメの背景「{r['bg']}」です。"
               f"このフレームから: {r['prompt']}")
        prompt = expand_prompt(client, cfg, raw, "video")
        print(f"[ai:clip] {r['sid']} {r['seconds']}s {r['resolution']} "
              f"frame={frame_path.name} → {out_path}")
        print(f"  motion: {prompt[:100]}...")
        generate_video(client, cfg, prompt=prompt, image_path=frame_path,
                       out_path=out_path, seconds=r["seconds"],
                       resolution=r["resolution"], audio=r["audio"])
        led.record(op="video", model=cfg["models"]["video"], est_usd=r["est"],
                   note=f"episode {plan['ep']} {r['sid']} {r['seconds']}s",
                   files=[str(out_path)])
        clips[r["sid"]] = fname
        made.append(str(out_path))
    mp = write_manifest(cfg, plan["ep"], clips)
    print(f"[ai] manifest 更新: {mp} ({len(clips)}シーン) "
          f"→ assemble.py が自動で使用します")
    return made

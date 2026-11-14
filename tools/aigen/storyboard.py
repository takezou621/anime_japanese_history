#!/usr/bin/env python3
"""script.json (唯一の契約) と AI 生成パイプラインの橋渡し.

- ep 指定で script.json を読み、新規に必要な背景のみ抽出
- シーンの beats (セリフ) とセクションを文脈としてテキストモデルに渡し、
  シーンごとの英語アートプロンプトを自動作成 (キャッシュ: ai_drafts/prompts/)
- クレジット無し/dry-run でも計画と費用見積もりが出る (フォールバックプロンプト)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from config import repo_root


def script_path(ep: str) -> Path:
    return repo_root() / "content" / "episodes" / ep / "script.json"


def load_script(ep: str) -> dict:
    p = script_path(ep)
    if not p.exists():
        raise FileNotFoundError(f"script.json がありません: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def scene_rows(ep: str) -> list[dict]:
    """script.json → [{scene_id, section, bg, beats_text, characters}]"""
    d = load_script(ep)
    rows = []
    for s in d.get("scenes", []):
        vis = s.get("visual", {})
        beats = " ".join(b.get("text", "") for b in s.get("beats", []))
        rows.append({
            "scene_id": s.get("id", "?"),
            "section": s.get("section", "?"),
            "bg": vis.get("background", ""),
            "beats_text": beats,
            "characters": [a.get("name") for a in vis.get("assets", [])
                           if str(a.get("name", "")).startswith("char_")],
        })
    return rows


def existing_backgrounds() -> set[str]:
    """すでに code-drawn で存在する背景名 (assets/ep*/scenes/ + ep01 引き当て)。"""
    found: set[str] = set()
    assets = repo_root() / "assets"
    if assets.exists():
        for ep_dir in sorted(assets.glob("ep*")):
            for f in (ep_dir / "scenes").glob("bg_*.png"):
                found.add(f.stem)
    return found


def unique_new_backgrounds(ep: str, include_reused: bool = False) -> list[dict]:
    """ep で必要な背景を初出順にユニーク化。既存背景は原則スキップ。"""
    have = existing_backgrounds()
    out: dict[str, dict] = {}
    for r in scene_rows(ep):
        bg = r["bg"]
        if not bg:
            continue
        reused = bg in have
        if reused and not include_reused:
            continue
        if bg not in out:
            out[bg] = {**r, "reused": reused, "scenes": [r["scene_id"]]}
        else:
            out[bg]["scenes"].append(r["scene_id"])
    return list(out.values())


def fallback_prompt_en(bg: str, section: str = "story") -> str:
    """テキストモデル無しで使う簡易フォールバック (dry-run/計画用)."""
    pretty = bg.removeprefix("bg_").replace("_", " ").strip()
    return (f"Flat anime background illustration of {pretty} in Japanese history "
            f"({section} section), bright pop colors, clean shapes, "
            "no people, no text, 16:9.")


def build_scene_prompt_context(row: dict, title: str) -> str:
    """テキストモデルに渡す文脈 (シーン説明) を組む。"""
    era = re.sub(r"^bg_(heian|asuka|nara|yayoi|jomon|kofun|muromachi|sengoku|edo)_?",
                 r"[\1] ", row["bg"]).removeprefix("bg_").replace("_", " ")
    return (
        f"番組タイトル: {title}\n"
        f"シーン: {row['scene_id']} ({row['section']}) / 背景名: {row['bg']} (時代ヒント: {era})\n"
        f"このシーンのセリフ: {row['beats_text']}\n"
        "上記内容を表現する、指定時代の日本史アニメ背景 1 枚の英プロンプトを作成してください。"
    )


def prompt_cache_path(cfg: dict, ep: str, bg: str) -> Path:
    from config import drafts_dir
    return drafts_dir(cfg, ep) / "prompts" / f"{bg}.txt"


def get_scene_prompt(client, cfg: dict, ep: str, row: dict, title: str,
                     use_cache: bool = True, cache_dir: Path | None = None) -> tuple[str, bool]:
    """シーンの英プロンプトを返す (キャッシュ or テキストモデル or フォールバック)。

    戻り値: (prompt_text, is_cached_or_fallback)
    client=None の場合はフォールバック (キャッシュがあればそれ)。
    """
    from pipeline import expand_prompt  # 遅延 import (SDK 無し環境対応)
    cpath = (cache_dir or prompt_cache_path(cfg, ep, row["bg"]))
    if use_cache and cpath.exists():
        return cpath.read_text(encoding="utf-8").strip(), True
    if client is None:
        return fallback_prompt_en(row["bg"], row["section"]), True
    text = expand_prompt(client, cfg, build_scene_prompt_context(row, title), "image")
    cpath.parent.mkdir(parents=True, exist_ok=True)
    cpath.write_text(text + "\n", encoding="utf-8")
    return text, False

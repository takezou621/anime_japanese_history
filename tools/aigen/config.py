#!/usr/bin/env python3
"""tools/aigen 設定モジュール.

Google AI Pro の月 $10 クレジット内で AI イラスト/動画生成を行うための
モデルID・単価・予算・スタイル設定。既定値は EMBEDDED_DEFAULTS、
tools/aigen/config.json があれば上書きマージする。

注意: モデルIDと単価は参考資料由来の「目安」。実行前に
  uv run --with google-genai python tools/aigen/cli.py models --remote
等で実在ID/実際の単価を確認し、config.json を修正すること。
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

DIR = Path(__file__).resolve().parent
CONFIG_PATH = DIR / "config.json"

EMBEDDED_DEFAULTS: dict = {
    # 月間予算 (USD)。この枠を超える課金見積もりはデフォルトで拒否する。
    "monthly_budget_usd": 10.0,
    "models": {
        # プロンプト設計 (日本語ラフ → 構図/ライティング/カメラ指定入り英語プロンプト)
        "text": "gemini-4-argon",
        # イラスト生成。image_api: "gemini" = generate_content系 (Nano Banana 系),
        # "imagen" = generate_images系 (Imagen 系)。実際のIDに合わせて変更。
        "image": "gemini-nano-banana-2.1",
        "image_api": "gemini",
        # 動画化 (本番)。開始フレーム画像を渡す image-to-video で一発成功させる。
        "video": "veo-3.1-generate-001",
        # 動画テスト用 (低コスト, 任意)
        "video_test": "gemini-omni-1.2-flash",
    },
    "env": {
        "api_key": "GEMINI_API_KEY",
        "project": "GCP_PROJECT_ID",
        "location": "GCP_LOCATION",
        "location_default": "us-central1",
    },
    # 単価 (USD)。あくまで見積もり用の目安値。
    "pricing_usd": {
        "text_per_call": 0.0005,
        "image": {"1K": 0.02, "2K": 0.04, "4K": 0.12},
        "video_per_second_1080p": 0.40,
        "video_4k_multiplier": 2.0,
        "video_audio_multiplier": 1.0,
        "video_test_per_call": 0.01,
    },
    # 2段階パイプライン: draft で構図/キャラ確定 → 採用枚だけ final で upscale。
    "image_tier": {"draft": "1K", "final": "4K"},
    "video": {
        "aspect_ratio": "16:9",
        "duration_seconds": 8,
        "resolution": "1080p",
        "generate_audio": True,
        # この見積金額(USD)を超える動画1本は --yes 必須 (ガチャ防止の最終確認)
        "confirm_over_usd": 2.0,
        "poll_interval_sec": 15,
        "timeout_sec": 900,
    },
    # STYLE_GUIDE (docs/03_STYLE_GUIDE.md) 由来のスタイル制約。
    # 背景/立ち絵は editor がテキストやキャラを上から合成するため
    # 「画像内に文字を描かない」「背景に主要キャラを描かない」が鉄則。
    "style": {
        "palette_hex": ["#2b4a8b", "#e8543f", "#f5b942", "#5aa469",
                        "#8ec9e8", "#dff1f7", "#c9a36b", "#8a6f4d"],
        "aspect_ratio": "16:9",
        "base_ja": (
            "アニメ調フラットアート。難しい受験内容を明るくポップに見せる。"
            "影は同系色の濃いフラット1色でグラデ乱用禁止。"
            "時代考証(建築・服飾・小物)は教科書準拠。"
            "画像内に文字・数字・ロゴ・水印を一切描かない。"
            "背景に主要キャラは描かない (キャラは別レイヤーで合成する)。"
            "画面中央左はテキスト合成のために比較的シンプルに。"
        ),
    },
    # 出力先 (ep は ep01/ep02/... に置換)
    "paths": {
        "drafts_dir": "assets/{ep}/ai_drafts",
        "video_dir": "video/{ep}_ai",
        "state_dir": "tools/aigen/state",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_config(path: Path | None = None) -> dict:
    """EMBEDDED_DEFAULTS に config.json (存在すれば) をマージして返す。"""
    p = path or CONFIG_PATH
    cfg = copy.deepcopy(EMBEDDED_DEFAULTS)
    if p.exists():
        cfg = _deep_merge(cfg, json.loads(p.read_text(encoding="utf-8")))
    return cfg


def state_dir(cfg: dict) -> Path:
    return DIR.parent.parent / cfg["paths"]["state_dir"]


def drafts_dir(cfg: dict, ep: str) -> Path:
    return DIR.parent.parent / cfg["paths"]["drafts_dir"].format(ep=ep)


def video_dir(cfg: dict, ep: str) -> Path:
    return DIR.parent.parent / cfg["paths"]["video_dir"].format(ep=ep)


def repo_root() -> Path:
    return DIR.parent.parent

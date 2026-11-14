#!/usr/bin/env python3
"""google-genai SDK ラッパー (テキスト/画像/動画).

- テキスト: 日本語ラフ指示 → スタイルガイド準拠の英語プロンプトへ変換
- 画像: Nano Banana 系 (generate_content) / Imagen 系 (generate_images) を自動ルート
- 動画: Veo 系 image-to-video (開始フレーム画像を必ず渡す「2段階パイプライン」)

SDK が無い環境でも import でき (genai=None)、CLI が導入コマンドを案内する。
"""
from __future__ import annotations

import mimetypes
import time
from pathlib import Path

try:  # google-genai は実行時にのみ必要 (selftest は無しで動く)
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore
except ImportError:  # pragma: no cover
    genai = None
    types = None

INSTALL_HINT = (
    "google-genai が未インストールです。次のように実行してください:\n"
    "  uv run --with google-genai python tools/aigen/cli.py <command> ...\n"
    "  (または pip install google-genai)")


class NoCredentials(RuntimeError):
    """API キーも GCP プロジェクトも未設定。"""


# ------------------------------------------------ クライアント

def backend_available(cfg: dict) -> str | None:
    """環境変数から使えるバックエンドを返す ('gemini_api' | 'vertexai' | None)。"""
    import os
    e = cfg["env"]
    if os.environ.get(e["api_key"]):
        return "gemini_api"
    if os.environ.get(e["project"]):
        return "vertexai"
    return None


def make_client(cfg: dict, backend: str | None = None):
    """genai.Client を生成する。backend: None=自動 / 'gemini_api' / 'vertexai'。"""
    if genai is None:
        raise NoCredentials(INSTALL_HINT)
    import os
    e = cfg["env"]
    api_key = os.environ.get(e["api_key"])
    project = os.environ.get(e["project"])
    location = os.environ.get(e["location"], e.get("location_default", "us-central1"))
    backend = backend or ("gemini_api" if api_key else ("vertexai" if project else None))
    if backend == "gemini_api":
        if not api_key:
            raise NoCredentials(f"{e['api_key']} が未設定です (export GEMINI_API_KEY=...)")
        return genai.Client(api_key=api_key)
    if backend == "vertexai":
        if not project:
            raise NoCredentials(f"{e['project']} が未設定です (export GCP_PROJECT_ID=...)")
        return genai.Client(vertexai=True, project=project, location=location)
    raise NoCredentials(
        f"{e['api_key']} または {e['project']} を設定してください\n"
        "  Gemini API 用: export GEMINI_API_KEY=...\n"
        "  Vertex AI 用 : export GCP_PROJECT_ID=... GCP_LOCATION=us-central1")


# ------------------------------------------------ システム指示 (プロンプト設計)

def _palette_text(cfg: dict) -> str:
    return ", ".join(cfg["style"]["palette_hex"])


def image_system_instruction(cfg: dict) -> str:
    return (
        "You are the art director of an educational Japanese-history anime YouTube "
        "channel (flat anime art style, bright and pop, for junior-high exam students).\n"
        "Convert the user's Japanese scene description into ONE highly detailed English "
        f"prompt for a single {cfg['style']['aspect_ratio']} anime BACKGROUND illustration.\n"
        "Hard rules:\n"
        f"- Flat anime art style, clean shapes, limited palette: {_palette_text(cfg)}.\n"
        "- One flat darker shade of the same hue for shadows; no heavy gradients.\n"
        "- Historically accurate Japanese era details (architecture, props, scenery).\n"
        "- Composition leaves the center-left relatively simple because titles and "
        "subtitle bands are overlaid later by an editor.\n"
        "- NO people or characters in the scene (characters are composited separately).\n"
        "- ABSOLUTELY no text, letters, numbers, logos, watermarks, signatures, borders, "
        "or UI elements.\n"
        "- Specify lighting (time of day), atmosphere, and depth layers "
        "(foreground / midground / background).\n"
        "Output ONLY the final English prompt: one paragraph, no quotes, no explanations."
    )


def video_system_instruction(cfg: dict) -> str:
    return (
        "You are a film director for an educational Japanese-history anime channel.\n"
        "Convert the user's Japanese motion request into ONE concise English video "
        "prompt for a single shot that STARTS from the provided still frame.\n"
        "Describe: camera movement (slow push-in, gentle pan, etc.), subject motion, "
        "lighting shifts, and ambient audio (footsteps, wind, rain, room tone, subtle "
        "traditional Japanese instruments).\n"
        "Keep the first-frame composition recognizable; motion must stay subtle to "
        "avoid flicker or warping. No on-screen text.\n"
        "Output ONLY the final English prompt: one paragraph, no quotes, no explanations."
    )


def expand_prompt(client, cfg: dict, raw: str, mode: str) -> str:
    """テキストモデルで日本語ラフ → 英語プロンプトへ変換する。"""
    sys_inst = (image_system_instruction(cfg) if mode == "image"
                else video_system_instruction(cfg))
    res = client.models.generate_content(
        model=cfg["models"]["text"],
        contents=raw,
        config=types.GenerateContentConfig(system_instruction=sys_inst),
    )
    text = (res.text or "").strip()
    if not text:
        raise RuntimeError("プロンプト拡張が空で返りました (モデルIDを確認してください)")
    return text


# ------------------------------------------------ 画像生成

def generate_image(client, cfg: dict, *, prompt: str, size: str,
                   aspect: str | None, out_path: Path) -> dict:
    """1枚生成して out_path (PNG) に保存する。"""
    aspect = aspect or cfg["style"]["aspect_ratio"]
    m = cfg["models"]
    if m.get("image_api", "gemini") == "imagen":
        # Imagen 系: GenerateImagesConfig の image_size は "1K"/"2K"/"4K"
        res = client.models.generate_images(
            model=m["image"],
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect,
                image_size=size,
                output_mime_type="image/png",
                person_generation="dont_allow",
            ),
        )
        img = res.generated_images[0].image
        img.save(str(out_path))
        return {"via": "generate_images", "path": str(out_path)}
    # Nano Banana 系: generate_content + response_modalities=["IMAGE"]
    kwargs: dict = {"response_modalities": ["IMAGE"]}
    try:
        kwargs["image_config"] = types.ImageConfig(image_size=size, aspect_ratio=aspect)
    except (TypeError, AttributeError):
        pass  # 古いSDKでは image_size 非対応 → 既定解像度で出る
    res = client.models.generate_content(
        model=m["image"], contents=prompt,
        config=types.GenerateContentConfig(**kwargs))
    for part in (res.candidates[0].content.parts or []):
        blob = getattr(part, "inline_data", None)
        if blob and blob.data:
            out_path.write_bytes(blob.data)
            return {"via": "generate_content", "path": str(out_path),
                    "mime": getattr(blob, "mime_type", "image/png")}
    raise RuntimeError("画像データがレスポンスに含まれていません (モデルID/image_api を確認)")


# ------------------------------------------------ 動画生成 (image-to-video)

def _build_video_config(cfg: dict, *, seconds: float, resolution: str,
                        audio: bool, aspect: str) -> object:
    """SDK バージョン差異を吸収しつつ GenerateVideosConfig を組む。"""
    v = cfg["video"]
    attempts = [
        dict(aspect_ratio=aspect, duration_seconds=seconds,
             resolution=resolution, generate_audio=audio,
             person_generation="dont_allow"),
        dict(aspect_ratio=aspect, duration_seconds=seconds,
             resolution=resolution, generate_audio=audio),
        dict(aspect_ratio=aspect, duration_seconds=seconds, generate_audio=audio),
        dict(aspect_ratio=aspect, duration_seconds=seconds),
    ]
    last_err: Exception | None = None
    for kw in attempts:
        try:
            return types.GenerateVideosConfig(**kw)
        except TypeError as err:  # 未対応フィールドが含まれる
            last_err = err
    raise RuntimeError(f"GenerateVideosConfig を構成できません: {last_err}")


def generate_video(client, cfg: dict, *, prompt: str, image_path: Path,
                   out_path: Path, seconds: float | None = None,
                   resolution: str | None = None, audio: bool | None = None,
                   model: str | None = None) -> dict:
    """Veo に開始フレーム画像を渡して 1本生成する (ガチャ防止の本体)。"""
    v = cfg["video"]
    seconds = seconds if seconds is not None else v["duration_seconds"]
    resolution = resolution or v["resolution"]
    audio = v["generate_audio"] if audio is None else audio
    mime = mimetypes.guess_type(str(image_path))[0] or "image/png"
    config = _build_video_config(cfg, seconds=seconds, resolution=resolution,
                                 audio=audio, aspect=v["aspect_ratio"])
    op = client.models.generate_videos(
        model=model or cfg["models"]["video"],
        prompt=prompt,
        image=types.Image(image_bytes=image_path.read_bytes(), mime_type=mime),
        config=config,
    )
    deadline = time.monotonic() + v["timeout_sec"]
    while not getattr(op, "done", False):
        if time.monotonic() > deadline:
            raise TimeoutError(f"動画生成が {v['timeout_sec']} 秒で完了しませんでした")
        print(f"  レンダリング中... ({v['poll_interval_sec']}秒待機)")
        time.sleep(v["poll_interval_sec"])
        op = client.operations.get(op)
    response = getattr(op, "result", None) or getattr(op, "response", None)
    videos = getattr(response, "generated_videos", None) or []
    if not videos:
        raise RuntimeError("生成動画がレスポンスに含まれていません (モデルIDを確認)")
    videos[0].video.save(str(out_path))
    return {"path": str(out_path), "seconds": seconds,
            "resolution": resolution, "audio": audio}


def list_remote_models(client) -> list[str]:
    """実在モデルID一覧 (credentials 必須)。config.json 修正用。"""
    try:
        return sorted({m.name.lstrip("models/") for m in client.models.list()})
    except Exception as err:  # SDK 差異/権限不足
        raise RuntimeError(f"モデル一覧の取得に失敗: {err}") from err

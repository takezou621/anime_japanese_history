#!/usr/bin/env python3
"""Season 1 総集編コンパイラ (タスク7).

全10話の FINAL.mp4 を連結し、冒頭にシリーズタイトルカード (3秒) を挿入した
一本の総集編を生成する。

技術方式 (docs/08_COMPILATION_SHORTS_PLAN.md):
1. タイトルカード: Pillow で 1920x1080 PNG を生成 -> 全話と同一エンコード
   パラメータ (1920x1080/30fps/yuv420p/bt709 + H.264 35Mbps CBR + 無音AAC) の
   3秒 MP4 にエンコード
2. concat demuxer (-c copy) で連結 — 品質劣化なし
3. QC: duration = 3s + 全10話合計 / ビットレート / 色空間 bt709

Usage:
  uv run --with pillow python tools/editor/compile_compilation.py \
      [--title-card-sec 3] [--out video/compilation_FINAL.mp4]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"
EPISODES = [f"ep{n:02d}" for n in range(1, 11)]
TITLE_CARD_SEC = 3.0


def probed_duration(path: Path) -> float:
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def make_title_card(out_png: Path, out_mp4: Path, sec: float) -> None:
    """シリーズタイトルカードを生成 (Pillow -> 3s MP4, 全話同一パラメータ)."""
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), (24, 32, 54))  # 深紺ベース
    d = ImageDraw.Draw(img)
    # グラデーション風の装飾帯
    for y in range(H):
        shade = int(18 + (y / H) * 14)
        d.line([(0, y), (W, y)], fill=(shade, shade + 10, shade + 30))
    # 中央の金色ライン
    d.rectangle([(W // 2 - 420, H // 2 - 130), (W // 2 + 420, H // 2 - 124)],
                fill=(212, 175, 55))
    d.rectangle([(W // 2 - 420, H // 2 + 124), (W // 2 + 420, H // 2 + 130)],
                fill=(212, 175, 55))

    # 日本語フォント探索 (tofu 防止: 見つかったフォントで日本語が
    # 実際に描けることを画素分散で検証してから採用)
    import glob
    from PIL import Image as _Img
    font_paths = (
        glob.glob("/System/Library/Fonts/Hiragino*.ttc")
        + glob.glob("/System/Library/Fonts/Supplemental/Songti*.ttc")
        + glob.glob("/System/Library/Fonts/NotoSansCJK*.ttc")
        + glob.glob("/System/Library/Fonts/Supplemental/NotoSansCJK*.ttc")
        + glob.glob(str(Path.home() / "Library/Fonts/*JP*.ttf"))
    )
    small_font = None
    for fp in font_paths:
        try:
            cand_title = ImageFont.truetype(fp, 92)
            cand_sub = ImageFont.truetype(fp, 44)
            cand_small = ImageFont.truetype(fp, 34)
            # tofu 検証: 日本語を描いて画素が多数立つことを確認
            probe = _Img.new("L", (300, 100), 0)
            pd = ImageDraw.Draw(probe)
            pd.text((10, 10), "日本史はじめて", font=cand_small, fill=255)
            ink = sum(1 for px in probe.getdata() if px > 40)
            if ink < 300:
                continue  # tofu (フォントが日本語非対応)
            title_font, subtitle_font, small_font = cand_title, cand_sub, cand_small
            print(f"title card font: {fp} (ink={ink})")
            break
        except OSError:
            continue
    if title_font is None:
        title_font = subtitle_font = small_font = ImageFont.load_default()

    def center(draw_obj, text, y, font, fill=(240, 234, 214)):
        box = draw_obj.textbbox((0, 0), text, font=font)
        draw_obj.text(((W - box[2] + box[0]) / 2, y), text, font=font,
                      fill=fill)

    center(d, "日本史はじめて物語", H // 2 - 80, title_font, (240, 234, 214))
    center(d, "Season 1 総集編", H // 2 + 40, subtitle_font, (212, 175, 55))
    center(d, "全10話を一気見で振り返る 日本史のキホン", H // 2 + 140,
           small_font, (200, 200, 210))
    img.save(out_png)

    # 無音AAC 付きの 3秒 MP4 (全話と同一のエンコードパラメータ)
    subprocess.run([
        FFMPEG, "-y", "-loglevel", "error",
        "-loop", "1", "-framerate", "30", "-t", f"{sec:.3f}", "-i", str(out_png),
        "-i", str(REPO / "audio/ep01/bgm.wav"),
        "-c:v", "libx264", "-preset", "veryfast", "-b:v", "35M", "-minrate", "35M",
        "-maxrate", "35M", "-bufsize", "4400k",
        "-x264-params", "nal-hrd=cbr:filler=1",
        "-pix_fmt", "yuv420p", "-r", "30", "-fps_mode", "cfr",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-color_range", "tv",
        "-t", f"{sec:.3f}",
        "-af", "afade=t=out:st=2.3:d=0.7,volume=0.7",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", str(out_mp4),
    ], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title-card-sec", type=float, default=TITLE_CARD_SEC)
    ap.add_argument("--out", default="video/compilation_FINAL.mp4")
    args = ap.parse_args()

    video_dir = REPO / "video"
    final_paths = [video_dir / f"{ep}_FINAL.mp4" for ep in EPISODES]
    missing = [str(p) for p in final_paths if not p.is_file()]
    if missing:
        raise SystemExit(f"missing episode renders: {missing}")

    ep_durations = {ep: probed_duration(video_dir / f"{ep}_FINAL.mp4")
                    for ep in EPISODES}
    total_episodes = sum(ep_durations.values())
    print("episode durations:")
    for ep in EPISODES:
        print(f"  {ep}: {ep_durations[ep]:.3f}s")
    print(f"  total episodes: {total_episodes:.3f}s")

    # 1) タイトルカード
    card_png = video_dir / "compilation_title_card.png"
    card_mp4 = video_dir / "compilation_title_card.mp4"
    print(f"title card: {args.title_card_sec}s -> {card_mp4.name}")
    make_title_card(card_png, card_mp4, args.title_card_sec)

    # 2) concat list
    concat_list = video_dir / "compilation_concat.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        f.write(f"file '{card_mp4.resolve()}'\n")
        for p in final_paths:
            f.write(f"file '{p.resolve()}'\n")

    # 3) 連結 (-c copy: 品質劣化なし)
    print(f"concat -> {args.out}")
    subprocess.run([
        FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", str(concat_list), "-c", "copy", "-movflags", "+faststart",
        args.out], check=True)

    # 4) QC
    got = probed_duration(Path(args.out))
    expected = args.title_card_sec + total_episodes
    probe = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=color_space,bit_rate", "-of", "json",
         args.out], capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)["streams"][0]
    qc = {
        "duration_got": round(got, 3),
        "duration_expected": round(expected, 3),
        "duration_ok": abs(got - expected) <= 1.0,
        "episodes_total": round(total_episodes, 3),
        "color_space": info.get("color_space"),
        "overall": "PASS" if abs(got - expected) <= 1.0 else "FAIL",
    }
    qc_path = video_dir / "compilation_QC.json"
    qc_path.write_text(json.dumps(qc, ensure_ascii=False, indent=2),
                       encoding="utf-8")
    print(json.dumps(qc, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""script.json から YouTube メタデータ (YAML) を生成する — アニメ日本史ラボ

Usage:
  uv run --with pillow python youtube/make_metadata.py --episode ep01
出力: youtube/ep01.yaml
"""
from __future__ import annotations

import argparse
import json
import sys


def yaml_quote(s: str) -> str:
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--episode", required=True)
    p.add_argument("--script", default=None)
    a = p.parse_args(argv)
    script_path = a.script or f"content/episodes/{a.episode}/script.json"
    sc = json.load(open(script_path, encoding="utf-8"))
    yt = sc.get("youtube", {})

    # チャプター: timing.json があれば実測、無ければシーン順で概算
    chapters = []
    try:
        timing = json.load(open(f"audio/{a.episode}/timing.json", encoding="utf-8"))
        sections = timing.get("sections", {})
        label = {"opening": "オープニング", "story": "ストーリー本編", "points": "受験ポイントまとめ",
                 "quiz": "クイズ3問", "ending": "エンディング・次回予告"}
        total = float(timing.get("total_duration", 0))
        for sec in ["opening", "story", "points", "quiz", "ending"]:
            if sec in sections and float(sections[sec]["start"]) > 0.5:
                t = int(float(sections[sec]["start"]))
                chapters.append(f"{t // 60:02d}:{t % 60:02d} {label.get(sec, sec)}")
        if total > 0 and chapters:
            t = max(0, int(total) - 1)
            chapters.append(f"{t // 60:02d}:{t % 60:02d} エンディング・次回予告")
    except FileNotFoundError:
        pass

    points = [s for scene in sc.get("scenes", []) for s in scene.get("exam_points", [])]
    quiz = sc.get("quiz", [])

    desc = yt.get("description", "")
    extra = []
    if points:
        extra.append("■ この動画の受験ポイント")
        extra += [f"・{pt}" for pt in points]
    if quiz:
        extra.append("\n■ クイズ (動画内で解答解説)")
        extra += [f"Q{i + 1}. {q.get('q', '')}" for i, q in enumerate(quiz)]
    extra.append("\n■ 制作について")
    extra.append("本動画はAI(スクリプト・イラスト・音声・編集)により制作しています。")
    extra.append("音声: VOICEVOX (四国めたん / ずんだもん) キャラクター設定はオリジナルです。")
    full_desc = desc + ("\n\n" + "\n".join(extra) if extra else "")
    if chapters:
        full_desc += "\n\n■ タイムスタンプ\n0:00 オープニング\n" + "\n".join(chapters)

    lines = []
    lines.append(f"title: {yaml_quote(yt.get('title', sc.get('title', '')))}")
    lines.append("youtube:")
    lines.append(f"  title: {yaml_quote(yt.get('title', sc.get('title', '')))}")
    lines.append(f"  privacy: public")
    lines.append(f"  description: {yaml_quote(full_desc)}")
    tags = yt.get("tags", [])
    lines.append("  tags: [" + ", ".join(yaml_quote(t) for t in tags) + "]")
    lines.append(f"thumbnail: youtube/thumbnails/{a.episode}_thumb.png")
    out_path = f"youtube/{a.episode}.yaml"
    open(out_path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"saved: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

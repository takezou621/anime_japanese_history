# Manim PoC（監督による検証済みサンプル、2026-11-15）

図解インサート生成に Manim を採用するための実証サンプル。監督（Muse）が Mac mini 上で構築・検証した。

## 環境
- venv: このディレクトリの `.venv`（Python 3.12、uv で作成）
- **manim 0.22.1（バージョン固定）**
- システム依存: Homebrew の pango 1.58.2 / cairo 1.18.6（導入済み）

## サンプル
- `timeline_poc.py`: 第1話向け年表（日本のあゆみ: 旧石器→縄文→弥生→古墳）。線が伸び、時代マーカーとラベルが順に出現する
- 出力: `out/videos/timeline_poc/1080p30/TimelinePoc.mov`

## レンダーコマンド
```
source .venv/bin/activate
manim render -r 1920,1080 --fps 30 -t --format=mov --media_dir ./out timeline_poc.py TimelinePoc
```

## 検証結果（監督実測）
- 1920×1080 / 30fps / 4.97秒、日本語テキスト（Hiragino Sans、Text()+Pango）は文字化けなし
- **透過は `--format=mov`（qtrle / argb、アルファあり）を使うこと**。`--format=webm` はアルファが落ちて不透明（yuv420p）になることを確認済み
- 紺背景への ffmpeg overlay 合成で表示確認済み

## 本番適用時の注意
- 日本語は必ず `Text()`（Pango）で描画し、`Tex()` 系は使わない
- 台本JSONからシーンを生成し、透過MOVを editor の overlay に渡す形にする
